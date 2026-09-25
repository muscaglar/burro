"""The step `preview` on a build whose list names the files of prices paid.

The town is Quillhaven and Tallowgate, which do not exist, and every sale is
made up. The files are those of the tests of prices paid, laid out as the
publisher lays out its own, and the postcode directory is the made-up one of
the tests of cells.

    area             flats                          terraced houses          detached houses
    Quillhaven 001   11, at 200,000 to 300,000      none                     none
    Quillhaven 002   9, too few for a figure        10, the two middle ones  none
                                                    at 400,000 and 400,001
    Tallowgate 001   50, at 101,000 to 150,000      none                     10, all at 900,000
"""

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from burro_core.explain import render
from burro_core.facts import facts_for
from burro_core.ids import Confidence, FilterReason, Strictness, TemplateId, Tenure
from burro_core.rank import rank
from burro_core.release import EVIDENCE, LOCK
from burro_pipeline.cells import postcodes
from burro_pipeline.derive import price, price_paid
from burro_pipeline.evidence.lock import read_lock
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry import load
from burro_pipeline.registry.model import Use
from burro_pipeline.release import cli as release_cli
from burro_pipeline.release.read import read_release
from public_log import is_public

from ..cells import postcodes_support
from ..cells.support import held
from ..derive import price_paid_support
from ..derive.price_paid_support import CANARY, CANARY_PRICE, SALES, YEARS
from .support import ONE, PAGE, REGISTRY, THREE, TWO, File, Made, made
from .test_preview_with_a_cost import buyer, with_prices, workbook
from .test_preview_with_a_cost import listed as the_workbook_listed

Printed = pytest.CaptureFixture[str]
LOOKUP = "ons-oa21-lsoa21-msoa21-lad22-lookup"
DIRECTORY = "postcode-directory"


@dataclass(frozen=True)
class Sales(File):
    """The made-up file of one year of sales, as a file of a build."""

    year: int = 0

    def receipt(self) -> Receipt:
        made_up = price_paid_support.receipt_of(self.year, self.content)
        return made_up.model_copy(update={"url": self.url})


@dataclass(frozen=True)
class Directory(File):
    """The made-up postcode directory, as a file a person saved."""

    def receipt(self) -> Receipt:
        return postcodes_support.directory_receipt(self.content)


def sales(year: int) -> Sales:
    return Sales(
        f"price-paid-{year}",
        price_paid.SOURCE,
        Use.SCORING,
        f"pp-{year}.csv",
        price_paid_support.EDITION.format(year=year),
        f"{year}",
        price_paid_support.file_of(year),
        year=year,
    )


def directory() -> Directory:
    return Directory(
        DIRECTORY,
        postcodes.SOURCE,
        Use.CELLS,
        postcodes_support.NAME,
        postcodes_support.EDITION,
        postcodes_support.PERIOD,
        postcodes_support.directory_zip(),
    )


def listed(file: File) -> str:
    """What the list says of a file of sales, or of the directory, which a person saved."""
    if isinstance(file, Sales):
        found = [
            'format = "csv"',
            f'url = "{file.url}"',
            f'data_period = {{ start = "{file.year}-01-01", end = "{file.year}-12-31" }}',
        ]
    else:
        found = ['format = "zip"', "by_hand = true", f'data_period = {{ as_at = "{file.period}" }}']
    return "\n".join(
        [
            "",
            "[[file]]",
            f'item = "{file.item}"',
            f'source_id = "{file.source_id}"',
            f'use = "{file.use}"',
            'what = "Made up for a test"',
            f'page = "{PAGE}"',
            "max_bytes = 10_000_000",
            f'edition = "{file.edition}"',
            *found,
            "",
        ]
    )


def with_sales(
    folder: Path,
    *,
    years: tuple[int, ...] = YEARS,
    with_the_directory: bool = True,
    with_the_workbook: bool = False,
) -> Made:
    """The made-up build, with the files of sales named in its list and kept in its store."""
    build = with_prices(folder) if with_the_workbook else made(folder)
    files: list[File] = [sales(year) for year in YEARS]
    files.append(directory())
    with (folder / "made-up.toml").open("a", encoding="utf-8") as the_list:
        for file in files:
            has_a_receipt = with_the_directory if isinstance(file, Directory) else True
            if isinstance(file, Sales) and file.year not in years:
                has_a_receipt = False
            build.keep(file, receipt=has_a_receipt)
            the_list.write(listed(file))
    return build


def quietly(build: Made, *more: str, out: Path | None = None) -> int:
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return build.run(*more, out=out)


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


@pytest.fixture(scope="module")
def build(tmp_path_factory: pytest.TempPathFactory) -> Made:
    """The build with its sales, built once for every test that only reads it."""
    found = with_sales(tmp_path_factory.mktemp("sold"))
    assert quietly(found) == 0
    return found


# What the step does


def test_a_build_whose_list_names_the_sales_says_one_line_of_its_cost(
    tmp_path: Path, capsys: Printed
):
    assert with_sales(tmp_path).run() == 0
    said = capsys.readouterr().out.splitlines()
    assert all(is_public(line) for line in said)
    [cost] = [line for line in said if line.startswith("step=cost ")]
    assert cost == f"step=cost status=ok source={price_paid.SOURCE} areas=3 rows=4 files=5"
    assert " findings=0 " in next(line for line in said if line.startswith("step=check"))


def test_what_it_prints_holds_no_price_no_postcode_and_nothing_of_an_address(
    tmp_path: Path, capsys: Printed
):
    assert with_sales(tmp_path).run() == 0
    said = "".join(capsys.readouterr())
    for sale in SALES:
        assert str(sale.price) not in said and f"{sale.price:,}" not in said
        assert not sale.postcode or sale.postcode not in said
    assert CANARY not in said


def test_the_sales_are_read_before_the_workbook_where_a_list_names_both(
    tmp_path: Path, capsys: Printed
):
    """A median of the sales says how many it rests on. The publisher's own says nothing of it."""
    found = with_sales(tmp_path, with_the_workbook=True)
    assert found.run() == 0
    said = capsys.readouterr().out.splitlines()
    [cost] = [line for line in said if line.startswith("step=cost ")]
    assert f"source={price_paid.SOURCE} " in cost
    release = read_release(found.release)
    assert all(row.counted for row in release.costs)
    assert price.SOURCE not in {source for row in release.costs for source in row.source_ids}
    # What homes of any kind sold for is still the publisher's own figure, as a measure.
    assert "step=derive status=ok feature=price_median" in "\n".join(said)


def test_the_cost_is_the_publishers_own_where_the_sales_have_no_receipt(
    tmp_path: Path, capsys: Printed
):
    found = with_sales(tmp_path, years=(), with_the_workbook=True)
    assert found.run() == 0
    said = capsys.readouterr().out.splitlines()
    [cost] = [line for line in said if line.startswith("step=cost ")]
    assert cost == f"step=cost status=ok source={price.SOURCE} areas=3 rows=6 files=2"
    assert not any(row.counted for row in read_release(found.release).costs)


@pytest.mark.parametrize("missing", ["the sales", "the directory"])
def test_no_cost_is_carried_where_a_file_it_needs_has_no_receipt(
    tmp_path: Path, capsys: Printed, missing: str
):
    """A sale cannot be placed without the directory, and nothing is guessed in its place."""
    years = () if missing == "the sales" else YEARS
    found = with_sales(tmp_path, years=years, with_the_directory=missing != "the directory")
    assert found.run() == 0
    said = capsys.readouterr()
    skipped = f"step=cost status=skipped source={price_paid.SOURCE} input_has_one_receipt=1"
    assert skipped in said.out.splitlines()
    assert (
        "A file of prices paid, or the postcode directory a sale is placed by, has no receipt"
        in said.err
    )
    assert read_release(found.release).costs == ()
    record = read(found.beside / "build.json")["cost"]
    assert (record["source_id"], record["carried"]) == (price_paid.SOURCE, [])
    assert record["left_out"]["rule"] == "input_has_one_receipt"
    report = (found.beside / "coverage.md").read_text(encoding="utf-8")
    assert "| cost/buy.flat | input_has_one_receipt |" in report


def test_a_file_of_sales_that_is_not_what_was_described_stops_the_build(
    tmp_path: Path, capsys: Printed
):
    found = made(tmp_path)
    with (tmp_path / "made-up.toml").open("a", encoding="utf-8") as the_list:
        for year in YEARS:
            file = sales(year)
            if year == 2024:
                content = price_paid_support.file_of(year, width=15)
                file = Sales(
                    file.item, file.source_id, file.use, file.name, file.edition, "2024", content,
                    year=year,
                )  # fmt: skip
            found.keep(file)
            the_list.write(listed(file))
        found.keep(directory())
        the_list.write(listed(directory()))
    assert found.run() == 2
    said = capsys.readouterr()
    assert "input_is_as_described=1" in said.out
    assert not found.release.exists() and not found.beside.exists()


# The release


def test_the_release_holds_a_counted_median_for_each_kind_of_home_with_enough_sales(build: Made):
    release = read_release(build.release)
    held_by = {(row.area_id, row.segment): (row.median, row.sales) for row in release.costs}
    assert held_by == {
        (ONE, "flat"): (250_000, 11),
        (TWO, "terraced"): (400_001, 10),
        (THREE, "detached"): (900_000, 10),
        (THREE, "flat"): (125_500, 50),
    }
    for row in release.costs:
        assert row.tenure is Tenure.BUY
        assert (row.lower_quartile, row.upper_quartile) == (None, None)
        assert (row.since, row.as_of) == ("2023-01", "2025-12")
        assert row.source_ids == (price_paid.SOURCE, LOOKUP, postcodes.SOURCE)
    assert {row.confidence for row in release.costs} == {Confidence.MEDIUM, Confidence.HIGH}


def test_no_row_of_a_sale_no_postcode_and_no_address_is_in_anything_that_was_written(build: Made):
    """The licence registry asks for the proof: only a figure of an area leaves the pipeline."""
    written = held(build.out)
    assert len(written) > 10
    medians = {str(row.median) for row in read_release(build.release).costs}
    for name, content in written.items():
        assert CANARY.encode() not in content, name
        assert str(CANARY_PRICE).encode() not in content, name
        for made_up in postcodes_support.DIRECTORY:
            outward, inward = made_up.postcode.split(" ")
            assert made_up.postcode.encode() not in content, name
            assert f"{outward}{inward}".encode() not in content, name
        for sale in SALES:
            if str(sale.price) not in medians:
                assert f'"{sale.price}"'.encode() not in content, name
                assert f":{sale.price}".encode() not in content, name
                assert f":{sale.price}.0".encode() not in content, name
    assert not any(build.out.rglob("*.csv")) and not any(build.out.rglob("*.zip"))


def test_the_release_holds_no_rent(build: Made):
    assert not [row for row in read_release(build.release).costs if row.tenure is Tenure.RENT]


def test_the_manifest_credits_each_publisher_in_the_registrys_words(build: Made):
    credited = {s.source_id: s for s in read_release(build.release).manifest.sources}
    for source_id in (price_paid.SOURCE, postcodes.SOURCE):
        assert credited[source_id].attribution == load(REGISTRY).get(source_id).attribution
    assert "HM Land Registry" in credited[price_paid.SOURCE].attribution


def test_the_release_passes_the_check_of_a_release(build: Made, capsys: Printed):
    arguments = ["check", str(build.release), "--registry", str(REGISTRY)]
    assert release_cli.main([*arguments, "--receipts", str(build.receipts)]) == 0
    assert "with evidence behind every fact" in capsys.readouterr().out


def test_built_twice_from_the_same_files_it_writes_the_same_bytes(build: Made, tmp_path: Path):
    assert quietly(build, out=tmp_path / "again") == 0
    assert held(build.out) == held(tmp_path / "again")


# The evidence and the record of the build


def evidence_of(build: Made) -> Evidence:
    return Evidence.model_validate_json((build.beside / EVIDENCE).read_bytes())


def test_every_price_has_a_row_of_evidence_that_holds_it_and_names_its_files(build: Made):
    evidence = evidence_of(build)
    sealed = {held.name for held in read_lock(build.beside / LOCK).inputs}
    for row in read_release(build.release).costs:
        behind_it = evidence.row(f"{row.area_id}/cost/buy.{row.segment}")
        assert behind_it is not None
        assert (behind_it.state, behind_it.value) == (State.PRESENT, float(row.median))
        assert behind_it.units_used == row.sales
        assert behind_it.derivation_id == price_paid.MEDIAN_OF_SALES.derivation_id
        assert evidence.sources_of(behind_it) == frozenset(row.source_ids)
        assert set(behind_it.inputs) <= sealed and len(behind_it.inputs) == 5


def test_an_area_with_too_few_sales_has_a_row_that_says_how_many_there_were(build: Made):
    evidence = evidence_of(build)
    too_few = evidence.row(f"{TWO}/cost/buy.flat")
    assert too_few is not None
    assert (too_few.state, too_few.value, too_few.units_used) == (State.BELOW_THRESHOLD, None, 9)
    none = evidence.row(f"{ONE}/cost/buy.detached")
    assert none is not None and (none.state, none.units_used) == (State.SOURCE_GAP, 0)
    # No build holds a rent, and the evidence says so of every area.
    rent = evidence.row(f"{ONE}/cost/rent.bed_1")
    assert rent is not None and rent.state is State.NOT_CARRIED


def test_the_record_of_the_build_counts_the_sales_and_holds_no_price(build: Made):
    record = read(build.beside / "build.json")["cost"]
    assert record["source_id"] == price_paid.SOURCE
    assert (record["listed"], record["left_out"], record["as_of"]) == (True, None, "2025-12")
    assert record["methods"] == ["median_of_sales_by_postcode@1"]
    assert record["cannot_see"] == list(price_paid.CANNOT_SEE)
    assert record["counted"] == {
        "since": "2023-01",
        "until": "2025-12",
        "fewest_sales": 10,
        "rows": 96,
        "rows_by_year": {"2023": 30, "2024": 36, "2025": 30},
        "additional": 3,
        "of_no_kind_of_home": 0,
        "placed": 90,
        "not_placed": 3,
        "placed_by_home": {"flat": 70, "terraced": 10, "semi_detached": 0, "detached": 10},
        "newly_built_by_home": {"flat": 2, "terraced": 0, "semi_detached": 0, "detached": 0},
        "at_an_ended_postcode": 6,
    }
    flats = next(one for one in record["carried"] if one["segment"] == "flat")
    assert flats == {
        "tenure": "buy",
        "segment": "flat",
        "areas": 3,
        "present": 2,
        "below_threshold": 1,
    }


# What a buyer is answered


def test_a_buyer_of_a_flat_is_held_against_flats_and_never_against_houses(build: Made):
    """The dear houses of Tallowgate leave its flats within a budget of 150,000."""
    release = read_release(build.release)
    result = rank(buyer(150_000, Strictness.HARD), release)
    assert [(f.area_id, f.reason) for f in result.filtered] == [(ONE, FilterReason.OVER_BUDGET)]
    kept = {area.area_id: area for area in result.ranked}
    fit = kept[THREE].budget
    assert fit is not None and (fit.margin, fit.utility) == (24_500, 1.0)
    assert fit.confidence is Confidence.HIGH
    # Too few flats were sold in the second area: it is kept, with its cost not known.
    assert kept[TWO].budget is None
    assert kept[TWO].untested_filters == (FilterReason.OVER_BUDGET,)


def test_an_area_near_the_line_is_kept_and_says_that_about_half_sold_for_less(build: Made):
    release = read_release(build.release)
    spec = buyer(210_000, Strictness.HARD)
    result = rank(spec, release)
    assert result.filtered == ()
    facts = {fact.fact_id: fact for fact in facts_for(release, ONE, spec)}
    over = facts[f"{ONE}/budget_fit/buy.flat"]
    assert over.template is TemplateId.BUDGET_OVER_MEDIAN
    assert render(over).text == (
        "The middle price of flats of all sizes is £40,000 over your budget of £210,000. "
        "About half of the flats sold here went for under £250,000."
    )
    price_of = facts[f"{ONE}/cost/buy.flat"]
    assert price_of.template is TemplateId.COST_BUY_SOLD
    assert render(price_of).text == (
        "Price for a flat: £250,000. This is the middle price of the 11 flats of all sizes "
        "sold from January 2023 to December 2025."
    )


def test_the_workbook_of_the_other_test_is_still_listed_as_it_was():
    """The two tests share a list entry, so that a change to one is seen in the other."""
    assert 'item = "median-prices"' in the_workbook_listed(workbook())
