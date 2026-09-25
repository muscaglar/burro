"""The step `preview` on a build whose list names the workbook of median prices.

The town is Quillhaven and Tallowgate, which do not exist, and every price is
made up. The workbook is the one of the tests of price, laid out as the
publisher lays out its own.

    MSOA        area             any kind   detached   semi      terraced   flat
    E02999001   Quillhaven 001    410000    [x]        525000    450000     300000
    E02999002   Quillhaven 002    655000    1200000    [x]       700500     [x]
    E02999003   Tallowgate 001    287500    no row     no row    [x]        250000
"""

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest
from burro_core.facts import facts_for
from burro_core.ids import (
    Confidence,
    Direction,
    FeatureId,
    FilterReason,
    Provenance,
    Segment,
    SpecProblemKind,
    Strictness,
    TemplateId,
    Tenure,
)
from burro_core.rank import rank
from burro_core.release import EVIDENCE, LOCK
from burro_core.spec import (
    Budget,
    FeatureWeight,
    PreferenceSpec,
    SpecError,
    check_spec,
    default_spec,
)
from burro_pipeline.derive import price
from burro_pipeline.derive.measures import MEASURES, TAGGED, behind
from burro_pipeline.evidence.lock import read_lock
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.served import unevidenced
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry import load
from burro_pipeline.registry.model import Use
from burro_pipeline.release import cli as release_cli
from burro_pipeline.release.read import read_release
from public_log import is_public

from ..cells.support import held
from ..derive import price_support
from .support import ONE, PAGE, REGISTRY, THREE, TWO, File, Made, made

Printed = pytest.CaptureFixture[str]
ITEM = "median-prices"
LOOKUP = "ons-oa21-lsoa21-msoa21-lad22-lookup"
# What the made-up flats sold for, in the middle. The second area has no figure.
FLATS = {ONE: 300_000, THREE: 250_000}
# Every price of the made-up workbook, as a run of digits. None may be printed.
PRICES = ("410000", "655000", "287500", "1200000", "525000", "450000", "700500", "300000", "250000")


@dataclass(frozen=True)
class Workbook(File):
    """The made-up workbook as a file of a build. Its receipt gives a year of sales."""

    def receipt(self) -> Receipt:
        return price_support.receipt(self.content, use=self.use)


def workbook(use: Use = Use.SCORING) -> Workbook:
    return Workbook(
        ITEM,
        price_support.SOURCE,
        use,
        price_support.WORKBOOK_NAME,
        price_support.EDITION,
        "2026-03",
        price_support.book(),
    )


def listed(file: File) -> str:
    """What the list says of the workbook: its edition, and the year of its sales."""
    return "\n".join(
        [
            "",
            "[[file]]",
            f'item = "{file.item}"',
            f'source_id = "{file.source_id}"',
            f'use = "{file.use}"',
            'what = "Made up for a test"',
            'format = "xlsx"',
            f'page = "{PAGE}"',
            f'url = "{file.url}"',
            "max_bytes = 10_000_000",
            f'edition = "{file.edition}"',
            'data_period = { start = "2025-04", end = "2026-03" }',
            "",
        ]
    )


def with_prices(
    folder: Path, *, listed_for: Use = Use.SCORING, fetched_for: Use | None = Use.SCORING
) -> Made:
    """The made-up build, with the workbook named in its list and kept in its store.

    `listed_for` is the use the list names, and `fetched_for` the use its
    receipt gives. With none it is in the store and has no receipt.
    """
    build = made(folder)
    build.keep(workbook(fetched_for or Use.SCORING), receipt=fetched_for is not None)
    with (folder / "made-up.toml").open("a", encoding="utf-8") as the_list:
        the_list.write(listed(workbook(listed_for)))
    return build


def quietly(build: Made, *more: str, out: Path | None = None) -> int:
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return build.run(*more, out=out)


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def buyer(amount: int, strictness: Strictness, tenure: Tenure = Tenure.BUY) -> PreferenceSpec:
    """A person with a budget, who weighs what a first build measures and nothing else."""
    spec = default_spec(tenure)
    # A measure that waits on something is worked out and left out of the release.
    measured = {measure.feature for measure in MEASURES if not measure.waits_on}
    return spec.replace(
        weights=tuple(w for w in spec.weights if w.feature_id in measured),
        tags=(),
        budget=Budget(
            amount=amount,
            segment=Segment.FLAT if tenure is Tenure.BUY else Segment.BED_1,
            strictness=strictness,
            weight=0.80,
            provenance=Provenance.STATED,
        ),
    )


@pytest.fixture(scope="module")
def build(tmp_path_factory: pytest.TempPathFactory) -> Made:
    """The build with its prices, built once for every test that only reads it."""
    found = with_prices(tmp_path_factory.mktemp("priced"))
    assert quietly(found) == 0
    return found


# What the step does


def test_a_build_whose_list_names_the_workbook_says_one_line_of_its_cost(
    tmp_path: Path, capsys: Printed
):
    assert with_prices(tmp_path).run() == 0
    said = capsys.readouterr().out.splitlines()
    assert all(is_public(line) for line in said)
    [cost] = [line for line in said if line.startswith("step=cost ")]
    assert cost == f"step=cost status=ok source={price.SOURCE} areas=3 rows=6 files=2"
    assert said.index(cost) < said.index(next(x for x in said if x.startswith("step=assemble")))
    assert " findings=0 " in next(line for line in said if line.startswith("step=check"))


def test_what_it_prints_holds_no_price(tmp_path: Path, capsys: Printed):
    assert with_prices(tmp_path).run() == 0
    said = "".join(capsys.readouterr())
    for paid in PRICES:
        assert paid not in said and f"{int(paid):,}" not in said


def test_a_build_whose_list_does_not_name_the_workbook_says_nothing_of_a_cost(
    tmp_path: Path, capsys: Printed
):
    found = made(tmp_path)
    assert found.run() == 0
    assert "step=cost" not in capsys.readouterr().out
    assert read_release(found.release).costs == ()
    record = read(found.beside / "build.json")["cost"]
    assert (record["listed"], record["carried"], record["left_out"]) == (False, [], None)


# The release


def test_the_release_holds_a_price_for_each_kind_of_home_that_has_a_figure(build: Made):
    release = read_release(build.release)
    assert {(row.area_id, row.tenure, row.segment): row.median for row in release.costs} == {
        (ONE, "buy", "semi_detached"): 525_000,
        (ONE, "buy", "terraced"): 450_000,
        (ONE, "buy", "flat"): 300_000,
        (TWO, "buy", "detached"): 1_200_000,
        (TWO, "buy", "terraced"): 700_500,
        (THREE, "buy", "flat"): 250_000,
    }
    for row in release.costs:
        assert (row.lower_quartile, row.upper_quartile) == (None, None)
        assert row.confidence is Confidence.UNSTATED
        assert (row.as_of, row.source_ids) == ("2026-03", (price.SOURCE, LOOKUP))


def test_the_release_holds_what_a_home_of_any_kind_sold_for_as_a_measure(build: Made):
    """Decided on 2026-09-24: a person may ask for homes that sell for more than the middle."""
    release = read_release(build.release)
    held = {metric.feature_id: metric for metric in release.metrics}
    metric = held[FeatureId.PRICE_MEDIAN]
    assert (metric.label, metric.unit) == ("Median price paid for a home", "£")
    assert (metric.rankable, metric.in_likeness) == (True, False)
    assert metric.source_ids == tuple(sorted((price.SOURCE, LOOKUP)))
    found = {area: release.feature(area, FeatureId.PRICE_MEDIAN) for area in (ONE, TWO, THREE)}
    assert {area: row.value for area, row in found.items() if row is not None} == {
        ONE: 410_000,
        TWO: 655_000,
        THREE: 287_500,
    }
    # Each figure has its row, which rests on the workbook and the lookup and holds the figure.
    evidence = evidence_of(build)
    for area, row in found.items():
        behind = evidence.row(f"{area}/feature/price_median")
        assert behind is not None and row is not None and behind.value == row.value
        files = [evidence.receipt(file_id) for file_id in behind.inputs]
        assert {file.source_id for file in files if file is not None} == {price.SOURCE, LOOKUP}
    # No vibe rests on it, so no vibe gains a part.
    assert not [
        vibe.tag_id
        for vibe in release.vibes
        if FeatureId.PRICE_MEDIAN in {term.feature_id for term in vibe.terms}
    ]


def test_a_person_may_ask_for_homes_that_sell_for_more_and_is_ranked_on_it(build: Made):
    release = read_release(build.release)
    nothing = default_spec(Tenure.BUY).replace(weights=(), tags=())
    dearer = FeatureWeight(
        feature_id=FeatureId.PRICE_MEDIAN,
        weight=0.5,
        direction=Direction.MORE,
        provenance=Provenance.UI_EDIT,
    )
    asked = nothing.replace(weights=(dearer,))
    assert check_spec(asked, release) == ()
    assert [area.area_id for area in rank(asked, release).ranked] == [TWO, ONE, THREE]
    cheaper = asked.replace(weights=(dearer.model_copy(update={"direction": Direction.LESS}),))
    assert [area.area_id for area in rank(cheaper, release).ranked] == [THREE, ONE, TWO]


def test_a_workbook_fetched_to_validate_against_stands_behind_no_measure(
    tmp_path: Path, capsys: Printed
):
    """The check of a release would refuse the figure, so the build leaves it out and says so."""
    found = with_prices(tmp_path, listed_for=Use.VALIDATION_ONLY, fetched_for=Use.VALIDATION_ONLY)
    assert found.run() == 0
    said = capsys.readouterr()
    skipped = (
        f"step=derive status=skipped feature=price_median source={price.SOURCE} input_is_allowed=1"
    )
    assert skipped in said.out.splitlines() and " findings=0 " in said.out
    assert "price_median is left out of the release" in said.err
    release = read_release(found.release)
    assert FeatureId.PRICE_MEDIAN not in {metric.feature_id for metric in release.metrics}
    assert release.feature(ONE, FeatureId.PRICE_MEDIAN) is None
    (gone,) = [
        one
        for one in read(found.beside / "build.json")["measures_left_out"]
        if one["feature_id"] == "price_median"
    ]
    assert gone["rule"] == "input_is_allowed"
    assert "stands behind no figure of a release" in gone["why"]
    assert gone["waits_on"] and all(said.endswith(".") for said in gone["waits_on"])
    report = (found.beside / "coverage.md").read_text(encoding="utf-8")
    assert "| feature/price_median | input_is_allowed | " in report


def test_the_release_holds_no_rent(build: Made):
    assert not [row for row in read_release(build.release).costs if row.tenure is Tenure.RENT]


def test_it_is_still_a_preview_and_is_not_made_up(build: Made):
    manifest = read_release(build.release).manifest
    assert (manifest.preview, manifest.synthetic) == (True, False)


def test_the_manifest_credits_the_publisher_in_the_registrys_words(build: Made):
    credited = {s.source_id: s for s in read_release(build.release).manifest.sources}
    entry = load(REGISTRY).get(price.SOURCE)
    assert credited[price.SOURCE].attribution == entry.attribution
    assert "Office for National Statistics" in credited[price.SOURCE].attribution
    assert "HM Land Registry" in credited[price.SOURCE].attribution


def test_the_release_passes_the_check_of_a_release(build: Made, capsys: Printed):
    arguments = ["check", str(build.release), "--registry", str(REGISTRY)]
    assert release_cli.main([*arguments, "--receipts", str(build.receipts)]) == 0
    assert "with evidence behind every fact" in capsys.readouterr().out


def test_built_twice_from_the_same_files_it_writes_the_same_bytes(build: Made, tmp_path: Path):
    assert quietly(build, out=tmp_path / "again") == 0
    assert held(build.out) == held(tmp_path / "again")


# The evidence


def evidence_of(build: Made) -> Evidence:
    return Evidence.model_validate_json((build.beside / EVIDENCE).read_bytes())


def test_every_price_has_a_row_of_evidence_that_holds_it_and_names_its_files(build: Made):
    evidence = evidence_of(build)
    sealed = {held.name for held in read_lock(build.beside / LOCK).inputs}
    for row in read_release(build.release).costs:
        behind_it = evidence.row(f"{row.area_id}/cost/buy.{row.segment}")
        assert behind_it is not None
        assert (behind_it.state, behind_it.value) == (State.PRESENT, float(row.median))
        assert behind_it.derivation_id == price.AREA_ROW_VALUE.derivation_id
        assert evidence.sources_of(behind_it) == frozenset(row.source_ids)
        assert set(behind_it.inputs) <= sealed


def test_an_area_with_no_price_has_a_row_that_says_why(build: Made):
    evidence = evidence_of(build)
    states = {
        key: row.state
        for key in (
            f"{TWO}/cost/buy.flat",
            f"{THREE}/cost/buy.detached",
            f"{ONE}/cost/rent.bed_1",
        )
        if (row := evidence.row(key)) is not None
    }
    assert states == {
        # The publisher withheld it: under 5 flats were sold.
        f"{TWO}/cost/buy.flat": State.SUPPRESSED,
        # The sheet of detached houses holds no row for the area.
        f"{THREE}/cost/buy.detached": State.SOURCE_GAP,
        # No build works a rent out.
        f"{ONE}/cost/rent.bed_1": State.NOT_CARRIED,
    }


def test_a_price_that_is_changed_after_the_build_is_found(build: Made):
    release = read_release(build.release)
    cheaper = tuple(
        row.replace(median=row.median - 50_000) if row.area_id == ONE else row
        for row in release.costs
    )
    found = unevidenced(
        replace(release, costs=cheaper),
        evidence_of(build),
        read_lock(build.beside / LOCK),
        load(REGISTRY),
        behind(),
        TAGGED.derivation_id,
    )
    assert {(one.fact_id, one.rule) for one in found} == {
        (f"{ONE}/cost/buy.{segment}", "row_holds_the_figure")
        for segment in ("flat", "semi_detached", "terraced")
    }


def test_a_price_that_is_added_after_the_build_is_found(build: Made):
    """A figure where the publisher withheld one has a row that says there is none."""
    release = read_release(build.release)
    made_up = next(row for row in release.costs if row.area_id == ONE and row.segment == "flat")
    added = (*release.costs, made_up.replace(area_id=TWO))
    found = unevidenced(
        replace(release, costs=added),
        evidence_of(build),
        read_lock(build.beside / LOCK),
        load(REGISTRY),
        behind(),
        TAGGED.derivation_id,
    )
    assert (f"{TWO}/cost/buy.flat", "row_has_a_value") in {(f.fact_id, f.rule) for f in found}


# The record of the build, and the report


def test_the_record_of_the_build_counts_the_areas_of_each_kind_and_holds_no_price(build: Made):
    record = read(build.beside / "build.json")["cost"]
    assert (record["listed"], record["left_out"], record["as_of"]) == (True, None, "2026-03")
    assert record["carried"] == [
        {"tenure": "buy", "segment": "detached", "areas": 3, "present": 1}
        | {"source_gap": 1, "suppressed": 1},
        {"tenure": "buy", "segment": "semi_detached", "areas": 3, "present": 1}
        | {"source_gap": 1, "suppressed": 1},
        {"tenure": "buy", "segment": "terraced", "areas": 3, "present": 2, "suppressed": 1},
        {"tenure": "buy", "segment": "flat", "areas": 3, "present": 2, "suppressed": 1},
    ]
    assert record["methods"] == ["area_row_value@1"]
    assert "rent" in record["rent"] and len(record["cannot_see"]) == 2
    written = (build.beside / "build.json").read_text()
    assert not any(paid in written for paid in PRICES)


def test_the_coverage_report_counts_the_prices_and_says_why_one_is_missing(build: Made):
    report = (build.beside / "coverage.md").read_text()
    assert "cost/buy.flat" in report
    assert "The publisher withheld the figure" in report
    assert not any(paid in report or f"{int(paid):,}" in report for paid in PRICES)


# A workbook that may not stand behind a figure


def left_out(found: Made) -> dict[str, Any]:
    assert read_release(found.release).costs == ()
    credited = {s.source_id for s in read_release(found.release).manifest.sources}
    assert price.SOURCE not in credited
    evidence = evidence_of(found)
    assert not [r for r in evidence.receipts if r.source_id == price.SOURCE]
    row = evidence.row(f"{ONE}/cost/buy.flat")
    assert row is not None and (row.state, row.inputs) == (State.NOT_CARRIED, ())
    return read(found.beside / "build.json")["cost"]["left_out"]


def test_a_workbook_with_no_receipt_is_left_out_and_the_build_goes_on(
    tmp_path: Path, capsys: Printed
):
    found = with_prices(tmp_path, fetched_for=None)
    assert found.run() == 0
    said = capsys.readouterr()
    assert f"step=cost status=skipped source={price.SOURCE} input_has_one_receipt=1" in said.out
    assert "what a home sells for is left out of the release" in said.err
    gone = left_out(found)
    assert gone["rule"] == "input_has_one_receipt"
    assert gone["why"] == "It has no receipt for the use the list names, or has more than one."


def test_a_workbook_that_was_fetched_to_validate_against_is_not_taken_for_one_fetched_to_show(
    tmp_path: Path, capsys: Printed
):
    """The list names it for scoring, and the one receipt of it says validation only."""
    found = with_prices(tmp_path, fetched_for=Use.VALIDATION_ONLY)
    assert found.run() == 0
    said = capsys.readouterr()
    assert f"step=cost status=skipped source={price.SOURCE} input_has_one_receipt=1" in said.out
    assert "for the use `validation_only`" in said.err
    gone = left_out(found)
    assert gone["rule"] == "input_has_one_receipt"
    assert gone["waits_on"][0] == (
        "A receipt of the file is in the folder, for the use `validation_only`."
    )
    # The file is no part of the build: the lock does not name it.
    sealed = {held.source_id for held in read_lock(found.beside / LOCK).inputs}
    assert price.SOURCE not in sealed


def test_a_list_that_names_the_workbook_to_validate_against_carries_no_cost(
    tmp_path: Path, capsys: Printed
):
    """It is sealed, as a file that the checks of a build read. No figure rests on it."""
    found = with_prices(tmp_path, listed_for=Use.VALIDATION_ONLY, fetched_for=Use.VALIDATION_ONLY)
    assert found.run() == 0
    said = capsys.readouterr()
    assert f"step=cost status=skipped source={price.SOURCE} input_is_allowed=1" in said.out
    assert " findings=0 " in said.out
    gone = left_out(found)
    assert gone["rule"] == "input_is_allowed"
    assert "stands behind no figure of a release" in gone["why"]
    assert not any((tmp_path / "out").rglob("*.xlsx"))


def test_a_workbook_that_is_left_out_is_said_to_be_in_the_coverage_report(tmp_path: Path):
    found = with_prices(tmp_path, fetched_for=None)
    assert quietly(found) == 0
    report = (found.beside / "coverage.md").read_text()
    assert "| cost/buy.flat | input_has_one_receipt |" in report


def test_a_workbook_that_is_not_what_was_described_stops_the_build(tmp_path: Path, capsys: Printed):
    """A cost is left out where its file may not be read. It is never guessed from a bad file."""
    found = made(tmp_path)
    broken = replace(workbook(), content=price_support.book(without=["1e"]))
    found.keep(broken)
    with (tmp_path / "made-up.toml").open("a", encoding="utf-8") as the_list:
        the_list.write(listed(broken))
    assert found.run() == 2
    said = capsys.readouterr()
    assert "input_is_as_described=1" in said.out
    assert not found.release.exists() and not found.beside.exists()


# What a buyer is answered


def test_a_buyer_with_a_firm_budget_loses_the_area_whose_flats_sold_for_far_more(build: Made):
    """A median is left out only where it is more than a quarter over the budget.

    The flats of the first area sold for 300,000 in the middle, which is more
    than a quarter over 239,000, and those of the third for 250,000, which is
    not.
    """
    release = read_release(build.release)
    result = rank(buyer(239_000, Strictness.HARD), release)
    assert [(f.area_id, f.reason) for f in result.filtered] == [(ONE, FilterReason.OVER_BUDGET)]
    kept = {area.area_id: area for area in result.ranked}
    assert set(kept) == {TWO, THREE}
    # The area with no figure for a flat is kept, and is not ranked as if it were cheap.
    assert kept[TWO].budget is None
    assert kept[TWO].untested_filters == (FilterReason.OVER_BUDGET,)
    assert [c.present for c in kept[TWO].contributions if c.component == "budget"] == [False]
    fit = kept[THREE].budget
    assert fit is not None and (fit.upper_quartile, fit.margin) == (None, -11_000)


def test_a_buyer_with_a_firm_budget_keeps_an_area_whose_flats_sold_for_a_little_more(build: Made):
    release = read_release(build.release)
    result = rank(buyer(275_000, Strictness.HARD), release)
    assert result.filtered == ()
    fits = {area.area_id: area.budget for area in result.ranked}
    over, under = fits[ONE], fits[THREE]
    assert over is not None and under is not None
    assert (over.margin, under.margin) == (-25_000, 25_000)
    assert over.utility < under.utility == 1.0


def test_a_buyer_with_a_soft_budget_loses_no_area_and_the_dearer_one_is_worth_less(build: Made):
    release = read_release(build.release)
    result = rank(buyer(275_000, Strictness.SOFT), release)
    assert result.filtered == ()
    fits = {area.area_id: area.budget for area in result.ranked}
    assert fits[TWO] is None
    dearer, cheaper = fits[ONE], fits[THREE]
    assert dearer is not None and cheaper is not None
    assert dearer.utility < cheaper.utility == 1.0


def test_a_buyer_is_told_what_the_price_is_of(build: Made):
    release = read_release(build.release)
    facts = {f.fact_id: f for f in facts_for(release, THREE, buyer(275_000, Strictness.SOFT))}
    assert facts[f"{THREE}/cost/buy.flat"].template is TemplateId.COST_BUY_MEDIAN
    assert facts[f"{THREE}/cost/buy.flat"].slots["period"] == "the year ending March 2026"
    assert facts[f"{THREE}/budget_fit/buy.flat"].template is TemplateId.BUDGET_UNDER_MEDIAN
    nothing = {f.fact_id: f for f in facts_for(release, TWO, buyer(275_000, Strictness.SOFT))}
    assert f"{TWO}/cost/buy.flat" not in nothing
    assert nothing[f"{TWO}/missing/budget"].template is TemplateId.MISSING


def test_a_renter_with_a_budget_is_turned_away_where_the_release_holds_no_rent(build: Made):
    release = read_release(build.release)
    # The release holds what a flat sold for and no rent. What a release holds for no area
    # cannot be asked for, so a renter's budget is turned away, firm or soft, and no area
    # is ranked with a rent that is not known.
    assert release.costed(Tenure.BUY, Segment.FLAT)
    assert not release.costed(Tenure.RENT, Segment.BED_1)
    for strictness in (Strictness.HARD, Strictness.SOFT):
        with pytest.raises(SpecError) as refused:
            rank(buyer(1_500, strictness, Tenure.RENT), release)
        assert [(p.path, p.problem) for p in refused.value.problems] == [
            ("budget.amount", SpecProblemKind.NOT_IN_RELEASE)
        ]
    # A buyer's budget for a flat is still held against the median.
    fits = {a.area_id: a.budget for a in rank(buyer(275_000, Strictness.SOFT), release).ranked}
    fit = fits[THREE]
    assert fit is not None and fit.upper_quartile is None
