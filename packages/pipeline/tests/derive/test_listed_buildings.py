"""Listed buildings, from the entries of the list to a figure for each square kilometre.

Every file here is made up: `heritage_support.py` writes the entries, and the
tests of cells draw the town they stand on. Each square of the town is one
hectare, so each figure can be worked out by hand.

    Quillhaven 001   4 hectares, 0.04 of a square kilometre, and 500 homes. 3 entries
    Quillhaven 002   4 hectares and 660 homes. 1 entry
    Tallowgate 001   5 hectares, in an authority where the file holds no entry
"""

from dataclasses import replace
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import land, spine
from burro_pipeline.derive import listed_buildings
from burro_pipeline.derive.listed_buildings import COVERED, PLACED, Listed
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import LSOA_RATIO_BY_HOMES, Worked
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import held, registry
from .heritage_support import (
    CANARY,
    ENTRIES,
    LISTED,
    ON_THE_ISLAND,
    QUILLHAVEN,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    TALLOWGATE,
    TALLOWGATE_1,
    THE_LIST,
    MadeUp,
    entries_file,
    inputs_of,
    outline,
    point,
)

LSOAS = tuple(f"E01999{number:03d}" for number in range(1, 7))
NO_FIGURE = Worked(None, 0, 2, 0.0, State.SOURCE_GAP)


def built(inputs: Inputs) -> Listed:
    found = spine.build(inputs)
    return listed_buildings.build(inputs, found, land.build(inputs, found))


def of_entries(folder: Path, records: list[MadeUp]) -> Listed:
    return built(inputs_of(folder, entries=entries_file(records)))


def entry(number: int, east: float, north: float, grade: str = "II") -> MadeUp:
    return MadeUp(f"3100{number:04d}", point(east, north), provider=THE_LIST, grade=grade)


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Listed:
    return built(inputs_of(tmp_path_factory.mktemp("town")))


@pytest.fixture(scope="module")
def both(tmp_path_factory: pytest.TempPathFactory) -> Listed:
    """The town with an entry in each of its two authorities."""
    return of_entries(tmp_path_factory.mktemp("both"), [*ENTRIES, ON_THE_ISLAND])


# The figure


def test_the_entries_of_each_lsoa_are_those_whose_point_stands_in_it(both: Listed):
    assert both.entries == dict(zip(LSOAS, (3, 0, 0, 1, 0, 1), strict=True))
    assert listed_buildings.entries_in(both.entries) == 5


def test_an_area_is_given_its_entries_for_each_square_kilometre(both: Listed):
    assert (3 / 0.04, 1 / 0.04, 1 / 0.05) == (75.0, 25.0, 20.0)
    assert both.worked == {
        QUILLHAVEN_1: Worked(75.0, 2, 2, 1.0, State.PRESENT),
        QUILLHAVEN_2: Worked(25.0, 2, 2, 1.0, State.PRESENT),
        TALLOWGATE_1: Worked(20.0, 2, 2, 1.0, State.PRESENT),
    }


def test_an_entry_counts_as_one_whatever_its_grade(tmp_path: Path):
    grades = [entry(1, 50, 150, "I"), entry(2, 60, 150, "I"), entry(3, 250, 50, "II")]
    found = of_entries(tmp_path, grades)
    assert (found.worked[QUILLHAVEN_1].value, found.worked[QUILLHAVEN_2].value) == (50.0, 25.0)


def test_the_entries_that_are_counted_are_counted_by_grade(both: Listed):
    assert both.counted.by_grade == {"I": 1, "II": 3, "II*": 1}
    assert sum(both.counted.by_grade.values()) == both.counted.placed == 5


def test_an_entry_with_no_grade_is_counted_under_none(tmp_path: Path):
    found = of_entries(tmp_path, [replace(entry(1, 50, 150), grade=None)])
    assert found.counted.by_grade == {"": 1}
    assert found.worked[QUILLHAVEN_1].value == 25.0


def test_a_grade_the_list_does_not_give_stops_the_step(tmp_path: Path):
    with pytest.raises(LockError) as stopped:
        of_entries(tmp_path, [entry(1, 50, 150, "III")])
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)


def test_an_lsoa_of_a_covered_authority_with_no_entry_holds_nought(town: Listed):
    assert [town.entries[lsoa] for lsoa in LSOAS[:4]] == [3, 0, 0, 1]


def test_nought_is_a_figure_where_the_authority_is_covered(tmp_path: Path):
    found = of_entries(tmp_path, [entry(1, 50, 150)])
    assert found.worked[QUILLHAVEN_2] == Worked(0.0, 2, 2, 1.0, State.PRESENT)


def test_a_figure_is_given_to_one_decimal_place_with_a_half_taken_upward(tmp_path: Path):
    """1 entry on 5 hectares and 1 on the 4 beside it: 20.0, and 3 on 4 is 75.0."""
    found = of_entries(tmp_path, [entry(1, 450, 150), entry(2, 50, 50), entry(3, 60, 50)])
    assert found.worked[TALLOWGATE_1].value == 20.0
    assert found.worked[QUILLHAVEN_1].value == 50.0


# For each 1,000 homes


def test_the_other_reading_is_entries_for_each_thousand_homes(tmp_path: Path, both: Listed):
    found = spine.build(inputs_of(tmp_path))
    assert (round(1000 * 3 / 500, 1), round(1000 * 1 / 660, 1), round(1000 * 1 / 810, 1)) == (
        6.0,
        1.5,
        1.2,
    )
    other = listed_buildings.for_each_thousand_homes(both.entries, found)
    assert {area: one.value for area, one in other.items()} == {
        QUILLHAVEN_1: 6.0,
        QUILLHAVEN_2: 1.5,
        TALLOWGATE_1: 1.2,
    }


def test_the_other_reading_gives_no_figure_where_the_authority_is_not_covered(
    tmp_path: Path, town: Listed
):
    found = spine.build(inputs_of(tmp_path))
    other = listed_buildings.for_each_thousand_homes(town.entries, found)
    assert other[TALLOWGATE_1] == NO_FIGURE


# Which entries


def test_every_record_of_the_file_is_counted_once(town: Listed):
    counted = town.counted
    assert (counted.in_the_file, counted.in_the_box, counted.nowhere) == (8, 7, 0)
    assert (counted.ended, counted.not_points, counted.in_no_area, counted.placed) == (1, 0, 2, 4)
    assert counted.in_the_box == (
        counted.ended + counted.not_points + counted.in_no_area + counted.placed
    )


def test_an_entry_that_has_ended_is_left_out(tmp_path: Path):
    ended = replace(entry(1, 50, 150), ended="2026-09-24")
    found = of_entries(tmp_path, [ended, entry(2, 60, 150)])
    assert (found.counted.ended, found.counted.placed) == (1, 1)
    later = of_entries(tmp_path / "later", [replace(ended, ended="2026-09-25"), entry(2, 60, 150)])
    assert (later.counted.ended, later.counted.placed) == (0, 2)


def test_a_live_entry_that_is_not_a_point_is_counted_and_given_no_place(tmp_path: Path):
    an_outline = MadeUp("31000001", outline(10, 110, 10, 10), provider=THE_LIST, grade="II")
    found = of_entries(tmp_path, [an_outline, entry(2, 60, 150)])
    assert (found.counted.not_points, found.counted.placed) == (1, 1)
    assert found.worked[QUILLHAVEN_1].value == 25.0


def test_an_entry_that_stands_in_no_lsoa_is_counted_in_no_area(town: Listed):
    """One made-up entry stands in the sea, and one in the district beside London."""
    assert town.counted.in_no_area == 2
    assert listed_buildings.entries_in(town.entries) == 4


def test_an_entry_on_an_island_is_counted_in_the_lsoa_the_island_is_part_of(both: Listed):
    assert both.entries[LSOAS[5]] == 1


def test_a_point_that_is_no_longitude_and_latitude_stops_the_step(tmp_path: Path):
    short = MadeUp("31000001", {"type": "Point", "coordinates": [2.51]}, provider=THE_LIST)
    with pytest.raises(LockError) as stopped:
        of_entries(tmp_path, [short])
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)


def test_a_point_written_in_metres_is_nowhere_near_london_and_is_let_go(tmp_path: Path):
    """A file that gave its places on the grid would hold nothing in the box, and no figure."""
    in_metres = {"type": "Point", "coordinates": [700_050.0, 400_150.0]}
    found = of_entries(tmp_path, [MadeUp("31000001", in_metres, provider=THE_LIST, grade="II")])
    assert (found.counted.in_the_file, found.counted.in_the_box) == (1, 0)
    assert set(found.worked.values()) == {NO_FIGURE}


# Which authorities


def test_an_authority_in_which_the_file_holds_no_entry_has_no_figure_and_never_nought(
    town: Listed,
):
    assert town.of_authority == {QUILLHAVEN: 4, TALLOWGATE: 0}
    assert town.worked[TALLOWGATE_1] == NO_FIGURE
    assert town.worked[TALLOWGATE_1].value is None
    assert not set(town.entries) & set(LSOAS[4:])


def test_a_file_that_holds_no_entry_of_london_gives_no_area_a_figure(tmp_path: Path):
    found = of_entries(tmp_path, [])
    assert set(found.worked.values()) == {NO_FIGURE}
    assert (found.entries, found.of_authority) == ({}, {QUILLHAVEN: 0, TALLOWGATE: 0})


def test_one_entry_is_enough_for_an_authority_to_be_covered(both: Listed):
    assert both.of_authority == {QUILLHAVEN: 4, TALLOWGATE: 1}
    assert COVERED.parameters == {"at_least": 1}


# The evidence


def test_every_area_has_a_row_whether_it_has_a_figure_or_not(town: Listed):
    assert [row.fact_id for row in town.rows] == [
        f"{area}/feature/listed_buildings" for area in (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE_1)
    ]
    assert [row.value for row in town.rows] == [75.0, 25.0, None]
    assert [row.state for row in town.rows] == [State.PRESENT, State.PRESENT, State.SOURCE_GAP]


def test_a_row_names_the_method_and_the_four_files_the_figure_rests_on(town: Listed):
    assert {row.derivation_id for row in town.rows} == {LSOA_RATIO_BY_HOMES.derivation_id}
    assert len(town.files) == 4
    assert {row.inputs for row in town.rows} == {
        tuple(sorted(receipt.file_id for receipt in town.files))
    }
    assert {receipt.source_id for receipt in town.files} == {
        listed_buildings.SOURCE,
        "ons-lsoa-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "ons-census-2021-housing-tables",
    }


def test_a_row_is_dated_from_the_census_to_the_day_of_the_file(town: Listed):
    span = Period(start="2021-03-21", end="2026-09-24")
    assert all(row.data_period == span for row in town.rows)
    assert {row.retrieved_on for row in town.rows} == {"2026-09-24"}


def test_the_rows_and_the_methods_make_evidence_that_holds_together(town: Listed):
    assert Evidence.of("lon-2026-10-09-01", town.files, listed_buildings.METHODS, town.rows)


def test_each_method_says_every_number_it_turns_on():
    assert listed_buildings.METHODS[0] == LSOA_RATIO_BY_HOMES
    assert {method.kind for method in listed_buildings.METHODS} == {Kind.MEASURED}
    assert PLACED.parameters == {"each_counts": 1}
    assert {method.code for method in (PLACED, COVERED)} == {
        "burro_pipeline.derive.listed_buildings"
    }


def test_nothing_that_is_given_back_holds_a_record_or_its_name(town: Listed):
    """The registry asks for aggregates only. What is kept is counts and figures."""
    said = repr(town)
    assert CANARY not in said
    for record in ENTRIES:
        assert record.entity not in said


# The row of the catalogue


def test_the_row_of_the_catalogue_is_what_core_says_the_measure_is(town: Listed):
    core = FEATURES[FeatureId.LISTED_BUILDINGS]
    assert says_what_core_says(town.metric)
    assert town.metric.label == core.label == "Listed buildings"
    assert (town.metric.unit, town.metric.polarity) == ("per km²", Polarity.MORE)
    assert town.metric.native_resolution is NativeResolution.POINT
    assert town.geography is Geography.POINT


def test_the_row_names_the_day_of_the_file_and_every_source(town: Listed):
    assert town.metric.vintage == "2026-09-24"
    assert town.metric.source_ids == (
        listed_buildings.SOURCE,
        "ons-census-2021-housing-tables",
        "ons-lsoa-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
    )
    for source_id in town.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_the_definition_says_what_an_entry_is_and_what_is_not_counted(town: Listed):
    said = town.metric.definition
    for words in (
        "as at 2026-09-24",
        "every entry counts as one whatever its grade",
        "a whole terrace",
        "in square kilometres",
        "1 decimal place",
        "has no figure where the file holds no entry in its planning authority",
    ):
        assert words in said


def test_what_the_figure_cannot_see_is_said_in_two_sentences():
    assert len(listed_buildings.CANNOT_SEE) == 2
    assert all(sentence.endswith(".") for sentence in listed_buildings.CANNOT_SEE)
    assert "whole terrace" in listed_buildings.CANNOT_SEE[0]
    assert "whatever its grade" in listed_buildings.CANNOT_SEE[1]


def test_no_word_of_the_measure_says_who_lives_anywhere(town: Listed):
    said = " ".join(
        [town.metric.label, town.metric.definition, *listed_buildings.CANNOT_SEE]
        + [method.sentence for method in listed_buildings.METHODS[2:]]
    ).lower()
    for word in ("resident", "people", "household", "population", "who lives"):
        assert word not in said


# The gate, and the files


def test_the_gate_is_asked_about_the_file_before_it_is_read(tmp_path: Path):
    with pytest.raises(LockError) as stopped:
        built(inputs_of(tmp_path, given=replace_uses(listed_buildings.SOURCE)))
    assert stopped.value.rule == "gate_refuses"
    assert not list((tmp_path / "work").rglob("*.geojson"))


def replace_uses(source_id: str) -> Registry:
    """The repository's registry, with one source allowed for display alone."""
    return Registry(
        tuple(
            one.model_copy(update={"uses": (Use.DISPLAY,)}) if one.id == source_id else one
            for one in registry().sources
        )
    )


def test_a_build_with_no_file_of_listed_buildings_is_refused(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    without = Inputs(
        inputs.registry,
        [one for one in inputs.receipts if one.source_id != listed_buildings.SOURCE],
        inputs.store,
        inputs.work,
    )
    with pytest.raises(LockError) as stopped:
        built(without)
    assert stopped.value.rule == "input_has_one_receipt"


def test_the_made_up_file_is_the_file_the_measure_reads():
    assert (
        listed_buildings.SOURCE,
        listed_buildings.FILE,
        listed_buildings.DATASET,
    ) == LISTED
    assert listed_buildings.is_the_file(LISTED[1])


def test_the_file_is_known_by_the_publishers_name_for_it():
    assert listed_buildings.is_the_file("listed-building.geojson")
    assert not listed_buildings.is_the_file("listed-building.csv")
    assert not listed_buildings.is_the_file("conservation-area.geojson")
    assert not listed_buildings.is_the_file("listed-building.geojson.part")


def test_built_twice_the_figures_and_the_rows_are_the_same(tmp_path: Path, town: Listed):
    again = built(inputs_of(tmp_path, entries=entries_file(ENTRIES[::-1])))
    assert again.worked == town.worked
    assert [row.value for row in again.rows] == [row.value for row in town.rows]
    assert again.of_authority == town.of_authority
    assert again.counted == town.counted


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    built(inputs)
    assert held(tmp_path / "store") == before
