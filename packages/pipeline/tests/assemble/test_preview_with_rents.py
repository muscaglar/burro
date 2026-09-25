"""The step `preview` on a build whose list names the workbook of the rents of London.

The town is Quillhaven and Tallowgate, which do not exist, and every rent is
made up. The workbook and the directory of postcodes are those of the tests
of rents, laid out as their publishers lay out their own. No postcode begins
with a Q, so no district here is a district.

    area             its homes stand in                 so it takes the figure of
    Quillhaven 001   QH1, all of them                   the district QH1
    Quillhaven 002   three districts, none with half    the borough Quillhaven
    Tallowgate 001   QT2, 430 of its 820 homes          the district QT2

    a home of one bedroom   the count, the lower quartile, the median and the upper quartile
    QH1                     170   1,300   1,400   1,450
    Quillhaven              520   1,250   1,500   1,800
    QT2                      60   1,150   1,275   1,400
"""

import io
import json
import re
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from burro_core.explain import render
from burro_core.facts import RENT_CAUTION, facts_for
from burro_core.ids import (
    Confidence,
    CostOfKind,
    FilterReason,
    Provenance,
    Segment,
    Strictness,
    TemplateId,
    Tenure,
)
from burro_core.rank import rank
from burro_core.release import EVIDENCE, LOCK, CostOf
from burro_core.spec import Budget, PreferenceSpec, check_spec, default_spec
from burro_pipeline.cells import postcodes
from burro_pipeline.derive import price_paid, rent
from burro_pipeline.evidence.lock import read_lock
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry import load
from burro_pipeline.registry.model import Use
from burro_pipeline.release import cli as release_cli
from burro_pipeline.release.read import read_release
from public_log import is_public

from ..cells import postcodes_support
from ..cells.support import held
from ..derive import rent_support
from ..derive.rent_support import CANARY_RENT, QH1, QT2, QUILLHAVEN, TALLOWGATE
from .support import ONE, PAGE, REGISTRY, THREE, TWO, File, Made, made
from .test_preview_with_sales import listed as the_sales_listed
from .test_preview_with_sales import sales

Printed = pytest.CaptureFixture[str]
ITEM, DIRECTORY = "rents-of-the-town", "postcode-directory"
# Every rent of the made-up workbook that an area takes, as a run of digits. None may be
# printed.
RENTS = ("1300", "1400", "1450", "1250", "1500", "1800", "1150", "1275")
# A hash that a step prints. It is sixty-four letters and digits, of which any four may be
# the digits of a rent by chance, and it says nothing of what was hashed. So it is taken
# out of what was printed before a rent is looked for there.
A_HASH = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")
DISTRICTS = (QH1, "QH2", "QH3", "QT1", QT2)


@dataclass(frozen=True)
class Workbook(File):
    """The made-up workbook as a file of a build. Its receipt gives twelve months."""

    def receipt(self) -> Receipt:
        return rent_support.receipt(self.content, use=self.use)


@dataclass(frozen=True)
class Directory(File):
    """The made-up postcode directory, as a file a person saved."""

    def receipt(self) -> Receipt:
        return postcodes_support.directory_receipt(self.content)


def workbook(use: Use = Use.SCORING, content: bytes | None = None) -> Workbook:
    return Workbook(
        ITEM,
        rent_support.SOURCE,
        use,
        rent_support.WORKBOOK_NAME,
        rent_support.EDITION,
        "2026-03",
        rent_support.book() if content is None else content,
    )


def directory() -> Directory:
    return Directory(
        DIRECTORY,
        postcodes.SOURCE,
        Use.CELLS,
        postcodes_support.NAME,
        postcodes_support.EDITION,
        postcodes_support.PERIOD,
        postcodes_support.directory_zip(rent_support.DIRECTORY),
    )


def listed(file: File) -> str:
    """What the list says of the workbook, or of the directory, which a person saved."""
    if isinstance(file, Workbook):
        found = [
            'format = "xlsx"',
            f'url = "{file.url}"',
            'data_period = { start = "2025-04", end = "2026-03" }',
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


def with_rents(
    folder: Path,
    *,
    with_the_directory: bool = True,
    with_the_workbook: bool = True,
    with_sales: bool = False,
    content: bytes | None = None,
) -> Made:
    """The made-up build, with the workbook of rents named in its list and kept in its store."""
    build = made(folder)
    with (folder / "made-up.toml").open("a", encoding="utf-8") as the_list:
        build.keep(workbook(content=content), receipt=with_the_workbook)
        the_list.write(listed(workbook(content=content)))
        build.keep(directory(), receipt=with_the_directory)
        the_list.write(listed(directory()))
        for year in price_paid_years() if with_sales else ():
            build.keep(sales(year))
            the_list.write(the_sales_listed(sales(year)))
    return build


def price_paid_years() -> tuple[int, ...]:
    return (2023, 2024, 2025)


def quietly(build: Made, *more: str, out: Path | None = None) -> int:
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return build.run(*more, out=out)


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def renter(amount: int, strictness: Strictness, segment: Segment = Segment.BED_1) -> PreferenceSpec:
    """A renter with a budget, who asks for nothing else."""
    return default_spec(Tenure.RENT).replace(
        weights=(),
        tags=(),
        budget=Budget(
            amount=amount,
            segment=segment,
            strictness=strictness,
            weight=0.80,
            provenance=Provenance.STATED,
        ),
    )


@pytest.fixture(scope="module")
def build(tmp_path_factory: pytest.TempPathFactory) -> Made:
    """The build with its rents, built once for every test that only reads it."""
    found = with_rents(tmp_path_factory.mktemp("let"))
    assert quietly(found) == 0
    return found


# What the step does


def test_a_build_whose_list_names_the_workbook_says_one_line_of_its_rents(
    tmp_path: Path, capsys: Printed
):
    assert with_rents(tmp_path).run() == 0
    said = capsys.readouterr().out.splitlines()
    assert all(is_public(line) for line in said)
    [cost] = [line for line in said if line.startswith("step=cost ")]
    assert cost == f"step=cost status=ok source={rent.SOURCE} areas=3 rows=14 files=4"
    assert " findings=0 " in next(line for line in said if line.startswith("step=check"))


def test_what_it_prints_holds_no_rent_no_postcode_and_no_name_of_a_district(
    tmp_path: Path, capsys: Printed
):
    assert with_rents(tmp_path).run() == 0
    printed = "".join(capsys.readouterr())
    assert A_HASH.search(printed) is not None
    said = A_HASH.sub("", printed)
    for figure in (*RENTS, str(CANARY_RENT)):
        assert figure not in said and f"{int(figure):,}" not in said
    for row in rent_support.DIRECTORY:
        assert row.postcode not in said
    for district in DISTRICTS:
        assert district not in said


def test_a_build_with_sales_and_rents_says_a_line_of_each(tmp_path: Path, capsys: Printed):
    found = with_rents(tmp_path, with_sales=True)
    assert found.run() == 0
    said = capsys.readouterr().out.splitlines()
    costs = [line for line in said if line.startswith("step=cost ")]
    assert [line.split()[2] for line in costs] == [
        f"source={price_paid.SOURCE}",
        f"source={rent.SOURCE}",
    ]
    held = read_release(found.release).costs
    assert {row.tenure for row in held} == {Tenure.BUY, Tenure.RENT}
    assert list(held) == sorted(held, key=lambda row: (row.area_id, row.tenure, row.segment))
    assert all(row.of is None for row in held if row.tenure is Tenure.BUY)


@pytest.mark.parametrize("missing", ["the workbook", "the directory"])
def test_no_rent_is_carried_where_a_file_it_needs_has_no_receipt(
    tmp_path: Path, capsys: Printed, missing: str
):
    """An area cannot be placed without the directory, and nothing is guessed in its place."""
    found = with_rents(
        tmp_path,
        with_the_workbook=missing != "the workbook",
        with_the_directory=missing != "the directory",
    )
    assert found.run() == 0
    said = capsys.readouterr()
    skipped = f"step=cost status=skipped source={rent.SOURCE} input_has_one_receipt=1"
    assert skipped in said.out.splitlines()
    assert (
        "The workbook of rents, or the postcode directory an area is placed by, has no receipt"
        in said.err
    )
    assert read_release(found.release).costs == ()
    record = read(found.beside / "build.json")
    assert (record["rent"]["source_id"], record["rent"]["carried"]) == (rent.SOURCE, [])
    assert record["rent"]["left_out"]["rule"] == "input_has_one_receipt"
    report = (found.beside / "coverage.md").read_text(encoding="utf-8")
    assert "| cost/rent.bed_1 | input_has_one_receipt |" in report


def test_a_workbook_that_no_longer_says_what_is_said_of_it_stops_the_build(
    tmp_path: Path, capsys: Printed
):
    notes = dict(rent_support.SAID_IN_THE_NOTES) | {"note 3": "Made up for a test."}
    found = with_rents(tmp_path, content=rent_support.book(notes=notes))
    assert found.run() == 2
    said = capsys.readouterr()
    assert "input_is_as_described=1" in said.out
    assert not found.release.exists() and not found.beside.exists()


def test_a_build_whose_list_names_no_workbook_of_rents_says_nothing_of_rents(
    tmp_path: Path, capsys: Printed
):
    found = made(tmp_path)
    assert found.run() == 0
    assert "step=cost" not in capsys.readouterr().out
    assert "rent" not in read(found.beside / "build.json")


# The release


def rents_of(build: Made) -> dict[tuple[str, Segment], Any]:
    return {
        (row.area_id, row.segment): row
        for row in read_release(build.release).costs
        if row.tenure is Tenure.RENT
    }


def test_the_release_holds_the_rent_of_the_place_each_area_lies_in(build: Made):
    held = rents_of(build)
    of = {area: held[area, Segment.BED_1] for area in (ONE, TWO, THREE)}
    assert {area: (row.of, row.rents) for area, row in of.items()} == {
        ONE: (CostOf(kind=CostOfKind.POSTCODE_DISTRICT, name=QH1), 170),
        TWO: (CostOf(kind=CostOfKind.BOROUGH, name=QUILLHAVEN), 520),
        THREE: (CostOf(kind=CostOfKind.POSTCODE_DISTRICT, name=QT2), 60),
    }
    assert {
        area: (row.lower_quartile, row.median, row.upper_quartile) for area, row in of.items()
    } == {
        ONE: (1_300, 1_400, 1_450),
        TWO: (1_250, 1_500, 1_800),
        THREE: (1_150, 1_275, 1_400),
    }
    assert {(row.since, row.as_of, row.confidence) for row in of.values()} == {
        ("2025-04", "2026-03", Confidence.HIGH)
    }


def test_an_area_with_no_figure_of_either_place_has_no_rent(build: Made):
    held = rents_of(build)
    assert len(held) == 14
    assert (ONE, Segment.ROOM) not in held and (TWO, Segment.ROOM) not in held
    assert (THREE, Segment.BED_4PLUS) not in held
    # Where the district gives no range the borough's is taken, and says so.
    assert held[THREE, Segment.BED_2].of == CostOf(kind=CostOfKind.BOROUGH, name=TALLOWGATE)


def test_nothing_of_a_place_no_area_lies_in_is_in_anything_that_was_written(build: Made):
    for path in sorted(p for folder in (build.release, build.beside) for p in folder.iterdir()):
        said = path.read_text(encoding="utf-8")
        assert str(CANARY_RENT) not in said, path.name
        for row in rent_support.DIRECTORY:
            assert row.postcode not in said, path.name
        for district in ("QH2", "QH3", "QT1", rent_support.NO_AREA_LIES_IN):
            assert f'"{district}"' not in said, path.name


def test_the_manifest_credits_each_publisher_in_the_registrys_words(build: Made):
    credited = {s.source_id: s for s in read_release(build.release).manifest.sources}
    for source_id in (rent.SOURCE, postcodes.SOURCE):
        assert credited[source_id].attribution == load(REGISTRY).get(source_id).attribution
    assert "Office for National Statistics" in credited[rent.SOURCE].attribution


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


def test_every_rent_has_a_row_of_evidence_that_holds_its_median_and_names_its_files(
    build: Made,
):
    evidence = evidence_of(build)
    sealed = {held.name for held in read_lock(build.beside / LOCK).inputs}
    for (area, segment), row in rents_of(build).items():
        behind_it = evidence.row(f"{area}/cost/rent.{segment}")
        assert behind_it is not None
        assert behind_it.value == float(row.median)
        assert behind_it.units_used == row.rents
        assert Flag.ROUNDED_IN_SOURCE in behind_it.flags
        assert row.of is not None
        assert behind_it.derivation_id == rent.BY_KIND[row.of.kind].derivation_id
        assert evidence.sources_of(behind_it) == frozenset(row.source_ids)
        assert set(behind_it.inputs) <= sealed and len(behind_it.inputs) == 4


def test_a_row_of_evidence_says_how_much_of_the_area_stands_in_the_district(build: Made):
    evidence = evidence_of(build)
    whole = evidence.row(f"{ONE}/cost/rent.bed_1")
    part = evidence.row(f"{THREE}/cost/rent.bed_1")
    assert whole is not None and part is not None
    assert (whole.state, whole.weight_covered) == (State.PRESENT, 1.0)
    assert (part.state, part.weight_covered) == (State.PARTIAL, round(430 / 820, 6))


def test_an_area_with_no_rent_has_a_row_that_says_why(build: Made):
    evidence = evidence_of(build)
    none = evidence.row(f"{ONE}/cost/rent.room")
    assert none is not None and (none.state, none.value) == (State.SOURCE_GAP, None)
    withheld = evidence.row(f"{THREE}/cost/rent.bed_4plus")
    assert withheld is not None and withheld.state is State.SUPPRESSED
    # The build read no prices, and the evidence says so of every price.
    price = evidence.row(f"{ONE}/cost/buy.flat")
    assert price is not None and price.state is State.NOT_CARRIED


def test_the_record_of_the_build_counts_the_rents_and_holds_none(build: Made):
    record = read(build.beside / "build.json")
    assert record["cost"]["rent"].startswith("Burro holds the rent of the postcode district")
    let = record["rent"]
    assert (let["source_id"], let["listed"], let["left_out"]) == (rent.SOURCE, True, None)
    assert let["as_of"] == "2026-03"
    assert let["methods"] == ["rent_of_the_district@1", "rent_of_the_borough@1"]
    assert let["cannot_see"] == list(rent.CANNOT_SEE)
    assert let["counted"] == {
        "since": "2025-04",
        "until": "2026-03",
        "fewest_rents": 10,
        "least_share_of_homes_percent": 50,
        "boroughs": 2,
        "districts": 6,
        "areas_of_a_district": 2,
        "areas_of_no_district": 1,
        "areas_by_home": {
            "room": {"postcode_district": 0, "borough": 1, "none": 2},
            "studio": {"postcode_district": 1, "borough": 1, "none": 1},
            "bed_1": {"postcode_district": 2, "borough": 1, "none": 0},
            "bed_2": {"postcode_district": 1, "borough": 2, "none": 0},
            "bed_3": {"postcode_district": 1, "borough": 2, "none": 0},
            "bed_4plus": {"postcode_district": 1, "borough": 1, "none": 1},
        },
    }
    one_bed = next(one for one in let["carried"] if one["segment"] == "bed_1")
    assert one_bed == {"tenure": "rent", "segment": "bed_1", "areas": 3, "present": 2, "partial": 1}
    said = json.dumps(record)
    for figure in RENTS:
        assert figure not in said
    for district in DISTRICTS:
        assert f'"{district}"' not in said


# What a renter is answered


def test_a_budget_to_rent_is_no_longer_turned_away(build: Made):
    release = read_release(build.release)
    assert release.costed(Tenure.RENT, Segment.BED_1)
    assert check_spec(renter(1_400, Strictness.HARD), release) == ()


def test_a_firm_budget_leaves_out_an_area_only_where_the_middle_rent_is_far_over_it(
    build: Made,
):
    """A quarter over 1,100 is 1,375: the rents of 1,400 and 1,500 are over it, and 1,275 is not."""
    release = read_release(build.release)
    result = rank(renter(1_100, Strictness.HARD), release)
    assert [(f.area_id, f.reason) for f in result.filtered] == [
        (ONE, FilterReason.OVER_BUDGET),
        (TWO, FilterReason.OVER_BUDGET),
    ]
    [kept] = result.ranked
    assert kept.area_id == THREE and kept.budget is not None
    assert (kept.budget.margin, kept.budget.upper_quartile) == (-175, None)
    assert 0 < kept.budget.utility < 1


def test_a_renter_of_two_bedrooms_is_held_against_homes_of_two_bedrooms(build: Made):
    release = read_release(build.release)
    result = rank(renter(1_700, Strictness.SOFT, Segment.BED_2), release)
    fits = {area.area_id: area.budget for area in result.ranked}
    assert {area: fit.margin for area, fit in fits.items() if fit is not None} == {
        ONE: 50,
        TWO: -200,
        THREE: 50,
    }


def test_what_is_said_of_a_rent_names_the_place_the_months_and_the_count(build: Made):
    release = read_release(build.release)
    facts = {f.fact_id: f for f in facts_for(release, THREE, renter(1_100, Strictness.HARD))}
    rented = facts[f"{THREE}/cost/rent.bed_1"]
    assert rented.template is TemplateId.COST_RENT_RECORDED
    assert render(rented).text == (
        "Rent for a 1-bedroom home: £1,150 to £1,400 a month, middle £1,275. This is of "
        "postcode district QT2, and not of Tallowgate 001 alone. It rests on about 60 rents "
        "recorded there from April 2025 to March 2026."
    )
    assert rented.slots["caution"] == RENT_CAUTION
    over = facts[f"{THREE}/budget_fit/rent.bed_1"]
    assert render(over).text == (
        "The middle rent for a 1-bedroom home in postcode district QT2 is £175 over your "
        "budget of £1,100 a month. About half of the rents recorded there were under £1,275."
    )
    sources = {source.source_id for source in rented.sources}
    assert {rent.SOURCE, postcodes.SOURCE} <= sources
