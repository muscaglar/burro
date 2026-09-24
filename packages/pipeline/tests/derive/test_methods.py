"""The methods that turn a publisher's figure into a figure for an area.

Every number here is made up. The town is four output areas in two areas, and
small enough that each figure can be worked out by hand beside the test.

    area north:  n1 (100 homes)  n2 (300 homes)
    area south:  s1 (200 homes)  s2 (200 homes)

Each output area is an LSOA of its own, or n2 and s1 are one LSOA that lies
across both areas.
"""

import hashlib
import math
from pathlib import Path

import burro_pipeline
import pytest
from burro_pipeline.cells.spine import Homes
from burro_pipeline.derive import methods
from burro_pipeline.derive.methods import (
    AREA_ROW_RATIO,
    GRID_AT_HOMES,
    LSOA_RATIO_BY_HOMES,
    METHODS,
    Worked,
    area_row_ratio,
    cell_of,
    grid_at_homes,
    lsoa_ratio_by_homes,
    lsoa_to_area_by_homes,
    lsoa_value_by_homes,
    oa_sum,
    row_of,
    to_places,
)
from burro_pipeline.evidence.receipt import How, Period, Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.evidence.row import EvidenceRow, Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry.model import Use

NORTH, SOUTH = "lon-nnorth", "lon-nsouth"
HOMES = Homes(
    area_of={"n1": NORTH, "n2": NORTH, "s1": SOUTH, "s2": SOUTH},
    homes={"n1": 100, "n2": 300, "s1": 200, "s2": 200},
)
# Each LSOA lies in one area: one and two in the north, three and four in the south.
NESTED = {"n1": "one", "n2": "two", "s1": "three", "s2": "four"}
# The LSOA `wide` lies across both areas: 300 of its 500 homes are in the north.
SPLIT = {"n1": "one", "n2": "wide", "s1": "wide", "s2": "four"}


def value_of(worked: Worked) -> float:
    assert worked.value is not None
    return worked.value


# A sum of counts over output areas


def test_a_sum_over_output_areas_adds_the_areas_own():
    found = oa_sum({"n1": 1, "n2": 2, "s1": 4, "s2": 8}, HOMES)
    assert (found[NORTH].value, found[SOUTH].value) == (3, 12)
    assert found[NORTH] == Worked(3, 2, 2, 1.0, State.PRESENT)


def test_an_output_area_with_no_count_adds_nothing_and_is_not_covered():
    found = oa_sum({"n2": 2, "s1": 4, "s2": 8}, HOMES)[NORTH]
    # 300 of the north's 400 homes are in an output area with a count.
    assert found == Worked(2, 1, 2, 0.75, State.PARTIAL)


def test_below_half_the_homes_the_figure_is_not_given():
    found = oa_sum({"n1": 1, "s1": 4, "s2": 8}, HOMES)[NORTH]
    assert found == Worked(None, 1, 2, 0.25, State.BELOW_THRESHOLD)


def test_at_half_the_homes_the_figure_is_given():
    found = oa_sum({"s1": 4}, HOMES)[SOUTH]
    assert found == Worked(4, 1, 2, 0.5, State.PARTIAL)


def test_an_area_the_source_holds_nothing_for_is_a_gap_and_never_a_nought():
    found = oa_sum({"s1": 4, "s2": 8}, HOMES)[NORTH]
    assert found == Worked(None, 0, 2, 0.0, State.SOURCE_GAP)


def test_a_count_of_nought_is_a_count():
    found = oa_sum({"n1": 0, "n2": 0}, HOMES)[NORTH]
    assert found == Worked(0, 2, 2, 1.0, State.PRESENT)


def test_an_area_the_publisher_withheld_is_said_to_be_withheld():
    found = oa_sum({"s1": 4, "s2": 8}, HOMES, withheld={"n1", "n2"})[NORTH]
    assert found == Worked(None, 0, 2, 0.0, State.SUPPRESSED, (Flag.SUPPRESSED_IN_SOURCE,))


def test_a_figure_with_a_part_withheld_carries_its_flag():
    found = oa_sum({"n2": 2}, HOMES, withheld={"n1"}, flags=[Flag.ROUNDED_IN_SOURCE])[NORTH]
    assert found.state is State.PARTIAL
    assert found.flags == (Flag.ROUNDED_IN_SOURCE, Flag.SUPPRESSED_IN_SOURCE)


def test_just_under_all_the_homes_is_partial_and_the_share_is_kept_to_six_places():
    homes = Homes(area_of={"a": NORTH, "b": NORTH}, homes={"a": 985, "b": 15})
    assert oa_sum({"a": 1}, homes)[NORTH] == Worked(1, 1, 2, 0.985, State.PARTIAL)
    homes = Homes(area_of={"a": NORTH, "b": NORTH}, homes={"a": 990, "b": 10})
    assert oa_sum({"a": 1}, homes)[NORTH] == Worked(1, 1, 2, 0.99, State.PRESENT)
    homes = Homes(area_of={"a": NORTH, "b": NORTH}, homes={"a": 2, "b": 1})
    assert oa_sum({"a": 1}, homes)[NORTH].weight_covered == 0.666667


# A sum of counts over LSOAs


def test_a_sum_over_lsoas_adds_the_lsoas_the_area_takes_in():
    found = lsoa_to_area_by_homes({"one": 10, "two": 20, "three": 40, "four": 80}, NESTED, HOMES)
    assert found[NORTH] == Worked(30, 2, 2, 1.0, State.PRESENT)
    assert found[SOUTH] == Worked(120, 2, 2, 1.0, State.PRESENT)


def test_an_lsoa_that_lies_in_two_areas_is_shared_out_by_where_its_homes_are():
    found = lsoa_to_area_by_homes({"one": 10, "wide": 50, "four": 80}, SPLIT, HOMES)
    # 300 of the 500 homes of `wide` are in the north, so 30 of its 50.
    assert found[NORTH] == Worked(40, 2, 2, 1.0, State.PRESENT, (Flag.UNIT_SPLIT,))
    assert found[SOUTH] == Worked(100, 2, 2, 1.0, State.PRESENT, (Flag.UNIT_SPLIT,))
    assert value_of(found[NORTH]) + value_of(found[SOUTH]) == 10 + 50 + 80


def test_an_lsoa_with_no_count_takes_its_homes_out_of_the_coverage():
    found = lsoa_to_area_by_homes({"one": 10, "four": 80}, SPLIT, HOMES)
    assert found[NORTH] == Worked(None, 1, 2, 0.25, State.BELOW_THRESHOLD)
    assert found[SOUTH] == Worked(80, 1, 2, 0.5, State.PARTIAL)


# A share from two sums


def test_a_share_is_one_sum_over_another_and_never_a_mean_of_rates():
    flats = {"one": 90, "two": 30}
    homes = {"one": 100, "two": 300}
    found = lsoa_ratio_by_homes(flats, homes, NESTED, HOMES, times=100)[NORTH]
    # 120 flats of 400 homes. The mean of 90% and 10% would be 50%.
    assert found == Worked(30.0, 2, 2, 1.0, State.PRESENT)


def test_a_share_counts_only_an_lsoa_that_has_both_its_top_and_its_bottom():
    found = lsoa_ratio_by_homes({"one": 90, "two": 30}, {"two": 300}, NESTED, HOMES)[NORTH]
    assert found == Worked(0.1, 1, 2, 0.75, State.PARTIAL)


def test_a_share_of_a_split_lsoa_shares_out_both_its_top_and_its_bottom():
    top = {"one": 10, "wide": 100, "four": 0}
    bottom = {"one": 100, "wide": 500, "four": 200}
    found = lsoa_ratio_by_homes(top, bottom, SPLIT, HOMES)
    assert value_of(found[NORTH]) == pytest.approx((10 + 60) / (100 + 300))  # pyright: ignore[reportUnknownMemberType]
    assert value_of(found[SOUTH]) == pytest.approx(40 / (200 + 200))  # pyright: ignore[reportUnknownMemberType]


def test_a_density_is_a_count_over_land():
    homes = {"one": 120, "two": 280}
    hectares = {"one": 2.0, "two": 6.0}
    found = lsoa_ratio_by_homes(homes, hectares, NESTED, HOMES)[NORTH]
    assert found.value == 50.0


def test_a_share_of_nothing_is_not_given_and_is_never_nought():
    found = lsoa_ratio_by_homes({"one": 0, "two": 0}, {"one": 0, "two": 0}, NESTED, HOMES)
    assert found[NORTH] == Worked(None, 0, 2, 0.0, State.SOURCE_GAP)


# A share from the publisher's own row for the area


def test_a_share_from_the_areas_own_row_is_one_count_of_the_row_over_another():
    found = area_row_ratio({NORTH: 120, SOUTH: 0}, {NORTH: 400, SOUTH: 400}, HOMES, times=100)
    assert found[NORTH] == Worked(30.0, 1, 1, 1.0, State.PRESENT)
    # A count of nought is a count.
    assert found[SOUTH] == Worked(0.0, 1, 1, 1.0, State.PRESENT)


def test_an_area_whose_row_gives_no_count_is_a_gap_and_never_a_nought():
    found = area_row_ratio({SOUTH: 10}, {NORTH: 400, SOUTH: 400}, HOMES)[NORTH]
    assert found == Worked(None, 0, 1, 0.0, State.SOURCE_GAP)


def test_an_area_whose_row_withholds_the_count_is_said_to_be_withheld():
    found = area_row_ratio({SOUTH: 10}, {NORTH: 400, SOUTH: 400}, HOMES, withheld=[NORTH])
    assert found[NORTH] == Worked(None, 0, 1, 0.0, State.SUPPRESSED, (Flag.SUPPRESSED_IN_SOURCE,))
    assert found[SOUTH] == Worked(0.025, 1, 1, 1.0, State.PRESENT)


def test_a_count_that_is_given_beside_one_that_is_withheld_gives_a_figure_that_is_marked():
    found = area_row_ratio({NORTH: 40}, {NORTH: 400}, HOMES, times=100, withheld=[NORTH])[NORTH]
    assert found == Worked(10.0, 1, 1, 1.0, State.PRESENT, (Flag.SUPPRESSED_IN_SOURCE,))


def test_a_share_from_a_row_is_covered_by_as_much_of_the_area_as_the_row_counts():
    covered = {NORTH: 0.9, SOUTH: 0.4}
    found = area_row_ratio(
        {NORTH: 90, SOUTH: 40}, {NORTH: 360, SOUTH: 160}, HOMES, times=100, covered=covered
    )
    assert found[NORTH] == Worked(25.0, 1, 1, 0.9, State.PARTIAL)
    assert found[SOUTH] == Worked(None, 1, 1, 0.4, State.BELOW_THRESHOLD)


def test_a_share_of_nothing_from_a_row_is_not_given():
    found = area_row_ratio({NORTH: 0}, {NORTH: 0}, HOMES)[NORTH]
    assert found == Worked(None, 0, 1, 0.0, State.SOURCE_GAP)


def test_a_row_for_an_area_that_is_not_one_of_the_build_is_refused():
    with pytest.raises(ValueError, match="an area of the build"):
        area_row_ratio({"lon-nelsewhere": 1}, {NORTH: 400}, HOMES)


# How a figure is rounded


@pytest.mark.parametrize(
    ("value", "places", "given"),
    [
        # 10 of 800 homes is 1.25 in 100. A half goes up, as a person rounds by hand.
        (100 * 10 / 800, 1, 1.3),
        (100 * 450 / 800, 1, 56.3),
        (100 * 370 / 800, 1, 46.3),
        # 5635 of 10000 is 56.35, which no float holds exactly.
        (100 * 5635 / 10000, 1, 56.4),
        (56.24, 1, 56.2),
        (0.04, 1, 0.0),
        (0.05, 1, 0.1),
        (17.994999, 2, 17.99),
        (2.5, 0, 3.0),
    ],
)
def test_a_figure_is_rounded_with_a_half_taken_upward(value: float, places: int, given: float):
    assert to_places(value, places) == given


def test_the_share_of_homes_covered_is_kept_with_a_half_taken_upward_too():
    """One home of 128 is 0.0078125 of them. The language's own rounding gives 0.007812."""
    homes = Homes(area_of={"a1": NORTH, "a2": NORTH}, homes={"a1": 1, "a2": 127})
    found = oa_sum({"a1": 5.0}, homes)[NORTH]
    assert round(1 / 128, 6) == 0.007812
    assert (found.state, found.weight_covered) == (State.BELOW_THRESHOLD, 0.007813)


def test_the_languages_own_rounding_would_take_a_half_to_the_even_digit():
    """Why `to_places` is used: the figure a person works out by hand is the one given."""
    assert round(100 * 10 / 800, 1) == 1.2
    assert to_places(100 * 10 / 800, 1) == 1.3


# A mean weighted by homes


def test_a_mean_is_weighted_by_the_homes_of_each_lsoa():
    found = lsoa_value_by_homes({"one": 0.8, "two": 0.4}, NESTED, HOMES)[NORTH]
    # 100 homes at 0.8 and 300 at 0.4.
    assert value_of(found) == pytest.approx(0.5)  # pyright: ignore[reportUnknownMemberType]
    assert (found.state, found.weight_covered, found.flags) == (State.PRESENT, 1.0, ())


def test_a_mean_over_a_split_lsoa_weighs_only_its_homes_in_the_area():
    found = lsoa_value_by_homes({"one": 1.0, "wide": 0.0, "four": 1.0}, SPLIT, HOMES)
    assert value_of(found[NORTH]) == pytest.approx(100 / 400)  # pyright: ignore[reportUnknownMemberType]
    assert value_of(found[SOUTH]) == pytest.approx(200 / 400)  # pyright: ignore[reportUnknownMemberType]
    assert found[NORTH].flags == (Flag.UNIT_SPLIT,)


def test_a_mean_leaves_out_an_lsoa_with_no_value_and_says_how_much_was_covered():
    found = lsoa_value_by_homes({"two": 0.4}, NESTED, HOMES)[NORTH]
    assert found == Worked(0.4, 1, 2, 0.75, State.PARTIAL)


# A value looked up at a point


def test_a_point_stands_on_one_square_and_never_on_two():
    assert cell_of(530_999.9, 180_000.0) == (530_000, 180_000)
    assert cell_of(531_000.0, 179_999.9) == (531_000, 179_000)
    assert cell_of(-0.1, 0.0) == (-1000, 0)
    # The publisher names a square by its middle, which is on the square.
    assert cell_of(530_500, 180_500) == (530_000, 180_000)


GRID = {(530_000, 180_000): 20.0, (531_000, 180_000): 40.0}
CENTRES = {
    "n1": (530_100.0, 180_900.0),
    "n2": (531_900.0, 180_100.0),
    "s1": (530_500.0, 180_500.0),
    "s2": (532_000.0, 180_500.0),
}


def test_a_value_is_read_where_the_homes_are_and_averaged_by_homes():
    found = grid_at_homes(GRID, CENTRES, HOMES)
    # 100 homes on the square at 20 and 300 on the square at 40.
    assert found[NORTH] == Worked(35.0, 2, 2, 1.0, State.PRESENT)


def test_an_output_area_on_a_square_with_no_value_is_not_covered():
    found = grid_at_homes(GRID, CENTRES, HOMES)
    assert found[SOUTH] == Worked(20.0, 1, 2, 0.5, State.PARTIAL)


def test_an_output_area_with_no_centre_is_not_covered_and_nothing_stands_in():
    centres = {oa: point for oa, point in CENTRES.items() if oa != "n2"}
    found = grid_at_homes(GRID, centres, HOMES)[NORTH]
    assert found == Worked(None, 1, 2, 0.25, State.BELOW_THRESHOLD)


# What holds of every method


def every_method() -> list[dict[str, Worked]]:
    counts = {"one": 1.0, "two": 2.0}
    return [
        oa_sum({"n1": 1}, HOMES),
        lsoa_to_area_by_homes(counts, NESTED, HOMES),
        lsoa_ratio_by_homes(counts, counts, NESTED, HOMES),
        lsoa_value_by_homes(counts, NESTED, HOMES),
        grid_at_homes(GRID, {}, HOMES),
        area_row_ratio({NORTH: 1.0}, {NORTH: 2.0, SOUTH: 2.0}, HOMES),
    ]


def test_every_area_has_a_figure_or_a_reason_and_none_is_left_blank():
    for found in every_method():
        assert set(found) == {NORTH, SOUTH}
        for worked in found.values():
            assert (worked.value is None) == (worked.state not in (State.PRESENT, State.PARTIAL))


def test_no_figure_is_not_a_number():
    for found in every_method():
        for worked in found.values():
            assert worked.value is None or math.isfinite(worked.value)


def test_the_order_the_figures_are_given_in_does_not_change_the_answer():
    counts = {"one": 0.1, "two": 0.2, "three": 0.3, "four": 0.7}
    turned = dict(reversed(list(counts.items())))
    homes = Homes(
        area_of=dict(reversed(list(HOMES.area_of.items()))),
        homes=dict(reversed(list(HOMES.homes.items()))),
    )
    assert lsoa_to_area_by_homes(counts, NESTED, HOMES) == lsoa_to_area_by_homes(
        turned, dict(reversed(list(NESTED.items()))), homes
    )


def test_an_output_area_with_no_homes_weighs_nothing():
    homes = Homes(area_of={"a": NORTH, "b": NORTH}, homes={"a": 0, "b": 50})
    assert oa_sum({"b": 7}, homes)[NORTH] == Worked(7, 1, 2, 1.0, State.PRESENT)
    found = lsoa_value_by_homes({"x": 9.0, "y": 1.0}, {"a": "x", "b": "y"}, homes)[NORTH]
    assert found.value == 1.0


def test_an_area_with_no_homes_at_all_is_covered_by_its_output_areas():
    homes = Homes(area_of={"a": NORTH, "b": NORTH}, homes={"a": 0, "b": 0})
    assert oa_sum({"a": 3}, homes)[NORTH] == Worked(3, 1, 2, 0.5, State.PARTIAL)


def test_the_weights_hold_every_output_area_once_with_its_homes():
    with pytest.raises(ValueError, match="every output area"):
        Homes(area_of={"a": NORTH}, homes={})
    with pytest.raises(ValueError, match="below nothing"):
        Homes(area_of={"a": NORTH}, homes={"a": -1})
    with pytest.raises(ValueError, match="part of a unit"):
        lsoa_to_area_by_homes({}, {"n1": "one"}, HOMES)


# The record of each method, and the row behind a figure


def test_each_method_is_in_a_module_that_is_there_for_a_person_to_read():
    root = Path(burro_pipeline.__file__).parent.parent
    for method in METHODS:
        assert (root / Path(*method.code.split("."))).with_suffix(".py").is_file()
        assert method.code == methods.__name__
    assert len({method.derivation_id for method in METHODS}) == len(METHODS) == 6


def test_each_method_is_named_as_the_design_names_it():
    assert [method.name for method in METHODS] == [
        "oa_sum",
        "lsoa_to_area_by_homes",
        "lsoa_ratio_by_homes",
        "lsoa_value_by_homes",
        "grid_at_homes",
        "area_row_ratio",
    ]
    assert {method.derivation_id: method.kind.value for method in METHODS} == {
        "oa_sum@1": "measured",
        "lsoa_to_area_by_homes@1": "measured",
        "lsoa_ratio_by_homes@1": "measured",
        "lsoa_value_by_homes@1": "averaged",
        "grid_at_homes@1": "modelled",
        "area_row_ratio@1": "measured",
    }


def test_the_sentence_of_a_method_states_the_line_under_which_no_figure_is_given():
    assert methods.ENOUGH == 0.5
    for method in METHODS:
        assert "under 50 in 100" in method.sentence
    assert "1000 metres" in GRID_AT_HOMES.sentence and methods.SQUARE == 1000


def test_the_sentence_of_the_row_method_says_the_count_is_the_publishers_own_for_the_area():
    """So that a reader who opens the publisher's table for the area finds the same count."""
    assert "the publisher's own row for the area" in AREA_ROW_RATIO.sentence
    assert "never added up from the rows of smaller areas" in AREA_ROW_RATIO.sentence


def receipt(name: str, period: Period, retrieved_at: str) -> Receipt:
    sha256 = hashlib.sha256(name.encode()).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id="made-up-survey",
        use=Use.SCORING,
        publisher_file=name,
        url="https://files.made-up.example/about",
        sha256=sha256,
        bytes=1,
        retrieved_at=retrieved_at,
        how=How.FETCHED,
        edition="made up",
        data_period=period,
    )


FILES = (
    receipt("made-up-homes.csv", Period(as_at="2021-03-21"), "2026-09-23T21:09:21Z"),
    receipt("made-up-flats.csv", Period(as_at="2025-03-31"), "2026-09-24T08:00:00Z"),
)


@pytest.mark.parametrize(
    "counts",
    [
        {"one": 1.0, "two": 2.0},
        {"two": 2.0},
        {"one": 1.0},
        {},
    ],
    ids=["present", "partial", "below_threshold", "source_gap"],
)
def test_the_row_behind_a_figure_is_one_the_evidence_takes(counts: dict[str, float]):
    worked = lsoa_ratio_by_homes(counts, {"one": 4.0, "two": 4.0}, NESTED, HOMES)[NORTH]
    row = row_of(f"{NORTH}/feature/homes_flats", worked, LSOA_RATIO_BY_HOMES, FILES)
    assert isinstance(row, EvidenceRow)
    assert row.has_a_value == (worked.value is not None)
    assert row.inputs == tuple(sorted(file.file_id for file in FILES))
    assert row.data_period == Period(start="2021-03-21", end="2025-03-31")
    assert row.retrieved_on == "2026-09-24"
    # The evidence of a release takes the row with its method and its files.
    Evidence.of("lon-2026-09-23-01", FILES, [LSOA_RATIO_BY_HOMES], [row])


def test_a_row_of_a_figure_that_was_withheld_is_one_the_evidence_takes():
    worked = oa_sum({}, HOMES, withheld={"n1"})[NORTH]
    row = row_of(f"{NORTH}/feature/homes_flats", worked, methods.OA_SUM, FILES)
    assert (row.state, row.flags) == (State.SUPPRESSED, (Flag.SUPPRESSED_IN_SOURCE,))
