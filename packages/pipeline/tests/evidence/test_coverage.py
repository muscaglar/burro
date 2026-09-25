"""Coverage: every area and every measure has a state, and a gap is counted and never filled.

The release is the synthetic one, which has gaps on purpose, and its evidence
is made up. The committed report is what the code prints for it.
"""

import dataclasses
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from burro_core.ids import FeatureId
from burro_pipeline.evidence.claim import Claim, claim_id_of
from burro_pipeline.evidence.coverage import (
    Coverage,
    LeftOut,
    cover,
    essentials,
    measures_of,
    report,
    summary,
)
from burro_pipeline.evidence.row import IS_A_GAP, EvidenceRow, State
from burro_pipeline.evidence.store import Evidence
from public_log import is_public

from .examples import CLAIM, PAGE
from .support import CANARY, RELEASE_ID, changed, evidence, release, with_rows, without

COMMITTED = Path(__file__).parent / "fixtures" / f"coverage-{RELEASE_ID}.md"
PARK = "feature/park_proximity"
# Set by hand in the synthetic release: no cost, one vibe alone, a journey that was not routed.
NO_COST, NOT_MEASURED, NOT_ROUTED = "syn-n0016", "syn-n0017", "syn-n0008"


def covered() -> Coverage:
    return cover(release(), evidence())


def not_carried(fact_id: str) -> EvidenceRow:
    """The row that says a release holds no figure, because it carries no such measure."""
    return EvidenceRow(
        fact_id=fact_id,
        derivation_id=None,
        inputs=(),
        data_period=None,
        retrieved_on=None,
        units_used=0,
        units_expected=0,
        weight_covered=0,
        state=State.NOT_CARRIED,
    )


def states(coverage: Coverage, area_id: str, kind: str) -> Counter[State]:
    return Counter(
        coverage.cell(area_id, measure).state
        for measure in coverage.measures
        if measure.startswith(f"{kind}/")
    )


# The cells.


def test_every_area_and_every_measure_has_a_state():
    coverage = covered()
    assert len(coverage.areas) == 24 and len(coverage.measures) == 142
    assert len(coverage.cells) == 24 * 142
    assert {(c.area_id, c.measure) for c in coverage.cells} == {
        (area.area_id, measure)
        for area in release().neighbourhoods
        for measure in measures_of(release())
    }
    assert all(isinstance(cell.state, State) for cell in coverage.cells)


def test_a_release_is_held_to_every_measure_a_result_needs():
    kinds = Counter(measure.split("/")[0] for measure in measures_of(release()))
    # Every feature core knows, and the vibes the release carries: the thirteen, and Gritty.
    assert kinds == {"area": 2, "travel": 3, "cost": 10, "station": 1, "feature": 112, "tag": 14}


def test_the_gaps_the_synthetic_release_has_on_purpose_are_counted():
    coverage = covered()
    assert len(coverage.gaps) == 329
    assert Counter(cell.state for cell in coverage.gaps) == {
        # 170 features and 17 vibes with too little covered. Twelve of the features are the
        # four shares of who lives there, in the three areas where too few were counted.
        State.BELOW_THRESHOLD: 187,
        # 33 costs with no estimate, 12 vibes with none of their parts, and one measure of
        # which nothing at all was covered.
        State.SOURCE_GAP: 46,
        # Four features that core knows and no release carries yet, in each of 24 areas.
        State.NOT_CARRIED: 96,
    }
    # One rankable area has no cost, one can be placed on one vibe alone and on part of its
    # recipe, and one has journeys that were not routed.
    assert states(coverage, NO_COST, "cost") == {State.SOURCE_GAP: 10}
    # Of Gritty it holds no part now that homes per hectare is none.
    assert states(coverage, NOT_MEASURED, "tag") == {
        State.PARTIAL: 1,
        State.BELOW_THRESHOLD: 5,
        State.SOURCE_GAP: 8,
    }
    assert states(coverage, NOT_ROUTED, "travel") == {State.PARTIAL: 3}
    assert coverage.cell(NOT_ROUTED, "travel/pt").weight_covered == pytest.approx(38 / 40)


def test_a_gap_is_never_a_nought():
    for cell in covered().gaps:
        assert not cell.has_a_value
        assert cell.state in IS_A_GAP
    document = covered().model_dump(mode="json")
    assert all(set(cell) == set(document["cells"][0]) for cell in document["cells"])
    assert "value" not in document["cells"][0]


def test_a_cell_takes_the_state_its_row_gives():
    coverage = covered()
    for row in evidence().rows:
        if row.measure in coverage.measures:
            cell = coverage.cell(row.area_id, row.measure)
            assert (cell.state, cell.record) == (row.state, True)
            # Of a measure that is not carried there is nothing to cover a share of.
            carried = row.state is not State.NOT_CARRIED
            assert cell.weight_covered == (row.weight_covered if carried else None)
    assert coverage.without_a_record == ()


def test_the_reason_a_publisher_gives_is_kept():
    gap = next(row for row in evidence().rows if row.state is State.BELOW_THRESHOLD)

    def withheld(row: dict[str, Any]) -> None:
        row.update(state=State.SUPPRESSED, flags=["suppressed_in_source"], value=None)

    def too_small(row: dict[str, Any]) -> None:
        row.update(state=State.NOT_PUBLISHED, weight_covered=0, units_used=0)

    suppressed = cover(release(), changed(gap.fact_id, withheld))
    assert suppressed.cell(gap.area_id, gap.measure).state is State.SUPPRESSED
    assert len(suppressed.gaps) == 329
    unpublished = cover(release(), changed(gap.fact_id, too_small))
    assert unpublished.cell(gap.area_id, gap.measure).state is State.NOT_PUBLISHED
    # What no source could close is said once, and is not counted as a gap.
    assert len(unpublished.gaps) == 328
    assert "| Not published for areas this small | 1 |" in report(unpublished)


# Where no record stands behind a cell.


def test_a_cell_with_no_row_behind_it_says_so():
    coverage = cover(release(), without(f"syn-n0001/{PARK}", "syn-n0001/travel/pt"))
    assert [(c.area_id, c.measure) for c in coverage.without_a_record] == [
        ("syn-n0001", PARK),
        ("syn-n0001", "travel/pt"),
    ]
    # Its state is worked out from the release alone, and is what the row had said.
    assert coverage.cell("syn-n0001", PARK).state is covered().cell("syn-n0001", PARK).state
    assert "| Pairs with no record behind them | 2 |" in report(coverage)


def test_with_no_evidence_no_cell_has_a_record_and_every_cell_still_has_a_state():
    bare = cover(release())
    assert len(bare.without_a_record) == len(bare.cells)
    assert [cell.state for cell in bare.cells] == [cell.state for cell in covered().cells]
    assert bare.sources == ()
    assert "No evidence was given, so no source can be counted." in report(bare)


def test_a_row_that_disagrees_with_the_release_is_no_record():
    def suppress(row: dict[str, Any]) -> None:
        row.update(state=State.SUPPRESSED, weight_covered=0, units_used=0, value=None)

    cell = cover(release(), changed(f"syn-n0001/{PARK}", suppress)).cell("syn-n0001", PARK)
    # The release holds a figure, so the cell says so, and says that nothing stands behind it.
    assert (cell.has_a_value, cell.record) == (True, False)


def test_a_feature_the_release_does_not_carry_is_not_carried_in_every_area():
    dropped = FeatureId.PARK_PROXIMITY
    thinner = dataclasses.replace(
        release(),
        metrics=tuple(m for m in release().metrics if m.feature_id != dropped),
        features=tuple(f for f in release().features if f.feature_id != dropped),
    )
    kept = with_rows(row for row in evidence().rows if row.measure != PARK)
    coverage = cover(thinner, kept)
    cells = [coverage.cell(area.area_id, PARK) for area in coverage.areas]
    assert {cell.state for cell in cells} == {State.NOT_CARRIED}
    assert not any(cell.record for cell in cells)
    assert "A source the licence registry approves" in report(coverage)
    # A row that says so is a record of it.
    rows = [not_carried(f"{area.area_id}/{PARK}") for area in coverage.areas]
    said = cover(thinner, with_rows([*kept.rows, *rows]))
    assert all(said.cell(area.area_id, PARK).record for area in said.areas)


def without_a_cost() -> tuple[Coverage, Coverage]:
    """A release that holds no cost at all, with and without the rows that say so."""
    bare = dataclasses.replace(release(), costs=())
    kept = [row for row in evidence().rows if not row.measure.startswith("cost/")]
    rows = [
        not_carried(f"{area.area_id}/{measure}")
        for area in bare.neighbourhoods
        for measure in measures_of(bare)
        if measure.startswith("cost/")
    ]
    return cover(bare, with_rows(kept)), cover(bare, with_rows([*kept, *rows]))


def test_what_a_release_does_not_carry_at_all_is_no_gap_in_a_source():
    """A first build holds no cost, no journey and no station. No source was read for one."""
    unsaid, said = without_a_cost()
    for area in said.areas:
        # With no row, all that can be said is that no figure is there.
        assert states(unsaid, area.area_id, "cost") == {State.SOURCE_GAP: 10}
        assert states(said, area.area_id, "cost") == {State.NOT_CARRIED: 10}
    costs = [cell for cell in said.cells if cell.measure.startswith("cost/")]
    assert all(cell.record and cell.weight_covered is None for cell in costs)
    assert not any(cell.record for cell in unsaid.cells if cell.measure.startswith("cost/"))


def test_a_row_that_says_not_carried_is_no_record_of_a_figure_the_release_holds():
    rows = [
        not_carried(row.fact_id) if row.fact_id == f"syn-n0001/{PARK}" else row
        for row in evidence().rows
    ]
    cell = cover(release(), with_rows(rows)).cell("syn-n0001", PARK)
    assert (cell.has_a_value, cell.record) == (True, False)


# What an honest result needs.


def test_an_area_lacks_an_essential_when_it_has_no_cost_or_too_few_measures():
    coverage = covered()
    assert essentials(coverage, "syn-n0001") == ()
    assert essentials(coverage, NO_COST) == ("cost",)
    assert essentials(coverage, NOT_MEASURED) == ("enough to rank",)
    assert essentials(coverage, "syn-n0009") == ("cost", "enough to rank")
    lacking = [area.area_id for area in coverage.areas if essentials(coverage, area.area_id)]
    assert lacking == ["syn-n0009", NO_COST, NOT_MEASURED, "syn-n0020"]


# Sources, and what a share is a share of.


def test_a_source_is_counted_by_the_areas_its_files_stand_behind():
    (source,) = covered().sources
    assert (source.source_id, source.files, source.areas_with_a_record) == ("synthetic", 6, 24)
    assert (source.first_day, source.last_day) == ("2025-01-01", "2026-09-30")
    assert source.retrieved_on == "2026-09-23"
    assert source.share_covered == 1 and source.boroughs_with_a_gap == ()


def test_a_source_that_stands_behind_nothing_in_an_area_has_a_gap_there():
    rows = [row for row in evidence().rows if row.area_id != "syn-n0003"]
    (source,) = cover(release(), with_rows(rows)).sources
    assert source.areas_with_a_record == 23
    assert source.share_covered == pytest.approx(23 / 24)
    assert source.boroughs_with_a_gap == ("Quillhaven",)


def test_a_share_is_a_share_of_homes_only_when_homes_are_given():
    assert covered().weighted_by == "areas"
    assert "areas, each counted once, because no count of homes was given" in report(covered())
    rows = [row for row in evidence().rows if row.area_id != "syn-n0003"]
    homes = {area.area_id: 100 for area in release().neighbourhoods} | {"syn-n0003": 700}
    by_homes = cover(release(), with_rows(rows), homes)
    assert by_homes.weighted_by == "homes"
    assert by_homes.sources[0].share_covered == pytest.approx(2300 / 3000)
    assert "| Share of homes covered |" in report(by_homes)


def test_a_count_of_homes_is_never_made_up():
    some = {area.area_id: 100 for area in release().neighbourhoods[:-1]}
    with pytest.raises(ValueError, match="homes are given for every area"):
        cover(release(), evidence(), some)
    with pytest.raises(ValueError, match="homes are given for every area"):
        cover(release(), evidence(), some | {"syn-n0024": 1, "syn-n9999": 1})


def test_evidence_of_another_release_covers_nothing():
    other = Evidence.of("syn-2026-09-24-01", (), (), ())
    with pytest.raises(ValueError, match="not of this release"):
        cover(release(), other)


# Claims.


def test_claims_are_counted_by_kind_and_by_the_reason_they_were_rejected():
    rejected = CLAIM.model_dump(mode="json")
    rejected["review"] |= {"status": "rejected", "reason": "about_residents"}
    rejected["quote"] = "Alderwick is a district of Quillhaven."
    rejected |= {"start": 0, "end": len(rejected["quote"])}
    rejected["claim_id"] = claim_id_of("syn-n0001", "synthetic", 4021, rejected["quote"])
    claims = [CLAIM, Claim.model_validate(rejected)]
    held = Evidence.of(
        RELEASE_ID, [*evidence().receipts, PAGE], evidence().methods, evidence().rows, claims
    )
    (count,) = cover(release(), held).claims
    assert (count.kind, count.found, count.accepted, count.pending) == ("history", 2, 1, 0)
    assert count.rejected == {"about_residents": 1}
    assert "| history | 2 | 1 | 0 | about_residents 1 |" in report(cover(release(), held))
    # The report counts claims. It never prints one.
    assert CLAIM.quote not in report(cover(release(), held))
    assert "This release holds no claim." in report(covered())


# The report.


def test_the_committed_report_is_what_the_code_makes():
    assert COMMITTED.read_text(encoding="utf-8") == report(covered()), (
        "the committed coverage report is stale: run `make fixture`"
    )


def test_the_report_of_a_made_up_release_says_that_it_is_made_up():
    assert "This release is made up, and so is its evidence." in report(covered())
    real = covered().model_dump(mode="json") | {"synthetic": False}
    assert "made up" not in report(Coverage.model_validate(real))


def test_the_report_has_the_five_tables_and_a_row_for_every_gap():
    text = report(covered())
    titles = ("By source", "By measure", "By area", "Gaps", "Claims")
    assert [line[3:] for line in text.splitlines() if line.startswith("## ")] == list(titles)
    gaps = text.split("## Gaps")[1].split("## Claims")[0]
    # Of 327 gaps, 96 are of the four measures no area has. Each of those is said once.
    assert len([line for line in gaps.splitlines() if line.startswith("| syn-")]) == 329 - 96
    assert len([line for line in gaps.splitlines() if "| not_carried | yes |" in line]) == 4
    by_area = text.split("## By area")[1].split("## Gaps")[0]
    assert len([line for line in by_area.splitlines() if line.startswith("| syn-")]) == 24
    assert text.endswith("|\n") or text.endswith(".\n")


def test_the_report_says_once_what_no_area_has_and_not_once_for_every_area():
    _, said = without_a_cost()
    gaps = report(said).split("## Gaps")[1].split("## Claims")[0]
    # No cost of ten, and none of the four measures that no release carries yet.
    assert "Of the 142 things Burro measures, 128 have a figure in at least one area." in gaps
    assert gaps.count("| cost/rent.bed_1 | not_carried | yes |") == 1
    assert not [line for line in gaps.splitlines() if "| cost/" in line and "| syn-" in line]
    # What some areas lack is still listed for each of them.
    assert len([line for line in gaps.splitlines() if line.startswith("| syn-")]) == 233 - 33
    whole = report(covered())
    assert "Of the 142 things Burro measures, 138 have a figure in at least one area." in whole


def test_a_measure_that_was_worked_out_and_left_out_is_said_with_its_rule_and_what_it_waits_on():
    """A build that works a measure out and leaves it out is not a build that lacks a source."""
    dropped = FeatureId.PARK_PROXIMITY
    thinner = dataclasses.replace(
        release(),
        metrics=tuple(m for m in release().metrics if m.feature_id != dropped),
        features=tuple(f for f in release().features if f.feature_id != dropped),
    )
    rows = [row for row in evidence().rows if row.measure != PARK]
    rows += [not_carried(f"{area.area_id}/{PARK}") for area in release().neighbourhoods]
    coverage = cover(thinner, with_rows(rows))
    left_out = LeftOut(
        measure=PARK,
        rule="measure_is_as_core_says",
        why="is not named as core names it",
        waits_on=("Core names it a walk.", "The figure is a straight line."),
    )
    text = report(coverage, [left_out])
    titles = [line[3:] for line in text.splitlines() if line.startswith("## ")]
    assert titles == [
        "By source",
        "By measure",
        "By area",
        "Worked out and left out",
        "Gaps",
        "Claims",
    ]
    section = text.split("## Worked out and left out")[1].split("## Gaps")[0]
    assert (
        f"| {PARK} | measure_is_as_core_says | It is not named as core names it | "
        "Core names it a walk. The figure is a straight line. |"
    ) in section
    gaps = text.split("## Gaps")[1].split("## Claims")[0]
    (said,) = [line for line in gaps.splitlines() if line.startswith(f"| {PARK} |")]
    assert "Worked out, and left out of the release" in said
    assert "This build does not work the measure out" not in said
    # With nothing left out the report is as it was, and says nothing of it.
    assert "Worked out and left out" not in report(coverage)
    assert report(coverage, []) == report(coverage)


def test_what_is_said_of_a_measure_left_out_is_of_a_measure_the_release_does_not_carry():
    """A reason that is given for a measure the release holds would be said of a figure."""
    carried = LeftOut(measure=PARK, rule="measure_is_as_core_says", why="is not", waits_on=())
    with pytest.raises(ValueError, match="left out"):
        report(covered(), [carried])


def test_a_tag_that_too_few_measures_stand_behind_in_any_area_is_said_once_too():
    """A first build has too few measures for any tag, so each is below the threshold."""
    rows = [
        EvidenceRow.model_validate(
            row.model_dump(mode="json")
            | {"state": "below_threshold", "weight_covered": 0.5, "units_used": 1, "value": None}
        )
        if row.measure == "tag/leafy"
        else row
        for row in evidence().rows
    ]
    bare = dataclasses.replace(
        release(),
        tags=tuple(
            tag.replace(raw=None, score=None, coverage=0.5) if tag.tag_id == "leafy" else tag
            for tag in release().tags
        ),
    )
    gaps = report(cover(bare, with_rows(rows))).split("## Gaps")[1].split("## Claims")[0]
    assert gaps.count("| tag/leafy | below_threshold | yes |") == 1
    assert not [line for line in gaps.splitlines() if "| tag/leafy |" in line and "| syn-" in line]


def test_the_report_is_written_from_the_coverage_and_nothing_else():
    written = covered().canonical()
    assert report(Coverage.model_validate_json(written)) == report(covered())
    assert Coverage.model_validate_json(written).digest() == covered().digest()


def test_a_share_is_rounded_down_so_that_it_never_says_more_than_is_so():
    rows = [row for row in evidence().rows if row.area_id != "syn-n0003"]
    text = report(cover(release(), with_rows(rows)))
    # 23 of 24 is 95.8%.
    assert "| 95% |" in text and "96%" not in text


def test_what_a_build_prints_holds_counts_and_a_hash_and_names_no_area():
    line = summary(covered())
    assert line == (
        f"release={RELEASE_ID} areas=24 measures=142 values=3079 gaps=329 no_record=0 "
        f"coverage_sha256={covered().digest()}"
    )
    assert is_public(line)
    for area in release().neighbourhoods:
        assert area.area_id not in line and area.name not in line
    assert CANARY not in line


def test_coverage_cannot_be_made_with_a_blank():
    document = covered().model_dump(mode="json")
    with pytest.raises(ValueError, match="one cell for every area and every measure"):
        Coverage.model_validate(document | {"cells": document["cells"][1:]})
    with pytest.raises(ValueError, match="one cell for every area and every measure"):
        Coverage.model_validate(document | {"cells": document["cells"][::-1]})
    document["cells"][0]["state"] = None
    with pytest.raises(ValueError, match="state"):
        Coverage.model_validate(document)
