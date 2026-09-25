"""What homes let for: the middle rent of each kind of home, for the place an area lies in.

Every file here is made up: `rent_support.py` draws the workbook and the
directory of postcodes, on the town of the tests of cells. No postcode begins
with a Q, so no district here is a district.
"""

import dataclasses
import json
from pathlib import Path

import pytest
from burro_core.ids import Confidence, CostOfKind, Segment, Tenure
from burro_core.release import CostOf
from burro_pipeline.cells import postcodes, spine
from burro_pipeline.derive import rent
from burro_pipeline.derive.rent import Given, Rents
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.registry import Registry, RegistryError
from burro_pipeline.registry.model import Use

from ..cells.postcodes_support import MadeUpPostcode
from ..cells.support import registry
from .rent_support import (
    A_CANARY,
    AREAS,
    BOROUGHS,
    CANARY_RENT,
    DIRECTORY,
    DISTRICTS,
    KINDS,
    NOT_AVAILABLE,
    Q1,
    Q2,
    QH1,
    QH2,
    QT1,
    QT2,
    QUILLHAVEN,
    SAID_IN_THE_NOTES,
    SAID_ON_THE_COVER,
    SUPPRESSED,
    T1,
    TALLOWGATE,
    book,
    inputs_of,
    listed,
    table_of,
)

IN_QH1 = CostOf(kind=CostOfKind.POSTCODE_DISTRICT, name=QH1)
IN_QT2 = CostOf(kind=CostOfKind.POSTCODE_DISTRICT, name=QT2)
IN_QUILLHAVEN = CostOf(kind=CostOfKind.BOROUGH, name=QUILLHAVEN)
IN_TALLOWGATE = CostOf(kind=CostOfKind.BOROUGH, name=TALLOWGATE)


@pytest.fixture(scope="module")
def made(tmp_path_factory: pytest.TempPathFactory) -> Rents:
    inputs = inputs_of(tmp_path_factory.mktemp("rents"))
    return rent.build(inputs, spine.build(inputs))


def built(folder: Path, **changes: object) -> Rents:
    inputs = inputs_of(folder, **changes)  # pyright: ignore[reportArgumentType]
    return rent.build(inputs, spine.build(inputs))


def refusal(folder: Path, content: bytes, **changes: object) -> str:
    with pytest.raises(LockError) as refused:
        built(folder, content=content, **changes)
    assert refused.value.rule == "input_is_as_described"
    return str(refused.value)


def taken(made: Rents, home: Segment) -> dict[str, tuple[CostOf, Given] | None]:
    return {area: made.of[home].taken.get(area) for area in AREAS}


# Which place an area takes the figure of.


def test_an_area_that_lies_in_one_district_takes_the_figure_of_the_district(made: Rents):
    assert made.of[Segment.BED_1].taken[Q1] == (IN_QH1, Given(170, 1_300, 1_400, 1_450))
    assert made.stood[Q1].district == QH1
    assert (made.stood[Q1].homes, made.stood[Q1].of) == (500, 500)


def test_an_area_takes_a_district_where_half_or_more_of_its_homes_stand_in_it(made: Rents):
    # Two output areas of 390 homes stand in one district and two of 430 in another.
    assert made.stood[T1].district == QT2
    assert (made.stood[T1].homes, made.stood[T1].of) == (430, 820)
    assert made.of[Segment.BED_1].taken[T1] == (IN_QT2, Given(60, 1_150, 1_275, 1_400))


def test_an_area_no_district_holds_half_of_takes_the_figure_of_its_borough(made: Rents):
    assert made.stood[Q2].district is None
    assert made.stood[Q2].districts == 3
    assert made.of[Segment.BED_1].taken[Q2] == (IN_QUILLHAVEN, Given(520, 1_250, 1_500, 1_800))


def test_exactly_half_of_the_homes_is_enough(tmp_path: Path):
    # 110 and 140 homes in one district, 120 and 130 in another: each holds half of 500.
    split = (
        MadeUpPostcode("QH2 1CK", (50, 150)),
        MadeUpPostcode("QH2 2CK", (150, 50)),
        MadeUpPostcode("QH1 1CK", (150, 150)),
        MadeUpPostcode("QH1 2CK", (50, 50)),
    )
    made = built(tmp_path, directory=split)
    # Where two districts hold half each, the area takes the first of them by its name.
    assert (made.stood[Q1].district, made.stood[Q1].homes) == (QH1, 250)


def test_one_home_under_half_is_not_enough(tmp_path: Path):
    # 110 and 130 homes in one district: 240 of 500, and nothing stands in any other.
    split = (MadeUpPostcode("QH1 1CK", (50, 150)), MadeUpPostcode("QH1 2CK", (50, 50)))
    made = built(tmp_path, directory=split)
    assert made.stood[Q1].district is None
    assert made.of[Segment.BED_1].taken[Q1] == (IN_QUILLHAVEN, Given(520, 1_250, 1_500, 1_800))


def test_an_output_area_stands_in_the_district_of_most_of_its_postcodes(made: Rents):
    """The last output area of Tallowgate holds one postcode of a district and two of another."""
    assert made.stood[T1].districts == 2
    assert made.stood[T1].homes == 210 + 220


def test_an_output_area_with_no_postcode_in_use_stands_in_no_district(made: Rents):
    # Its homes are homes of the area all the same: 150, 160 and 170 of 660 are placed.
    assert made.stood[Q2].of == 660
    assert made.stood[Q2].homes == 170


# What is carried, and what is not.


def test_a_figure_is_carried_as_the_workbook_writes_it(made: Rents):
    [row] = [row for row in rent.costs(made) if (row.area_id, row.segment) == (Q1, Segment.BED_3)]
    assert (row.lower_quartile, row.median, row.upper_quartile) == (1_800, 2_000, 2_213)
    assert (row.rents, row.since, row.as_of) == (100, "2025-04", "2026-03")
    assert (row.tenure, row.of, row.confidence) == (Tenure.RENT, IN_QH1, Confidence.HIGH)
    assert row.sales is None


def test_what_a_figure_rests_on_is_what_its_count_makes_it(made: Rents):
    rests_on = {(row.area_id, row.segment): row.confidence for row in rent.costs(made)}
    assert rests_on[Q1, Segment.STUDIO] is Confidence.MEDIUM
    assert rests_on[Q1, Segment.BED_4PLUS] is Confidence.MEDIUM
    assert rests_on[T1, Segment.STUDIO] is Confidence.HIGH


def test_a_row_with_a_median_and_no_quartiles_is_not_carried(made: Rents):
    """The district gives a median for two bedrooms and no range, so the borough's is taken."""
    assert made.of[Segment.BED_2].taken[T1] == (IN_TALLOWGATE, Given(470, 1_400, 1_650, 1_800))
    assert made.of[Segment.ROOM].taken[T1] == (IN_TALLOWGATE, Given(30, 700, 800, 900))
    # And where the borough gives no range either, the area has no figure.
    assert taken(made, Segment.STUDIO)[Q2] is None


def test_where_the_district_has_no_figure_the_boroughs_is_taken(made: Rents):
    assert made.of[Segment.STUDIO].taken[T1] == (IN_TALLOWGATE, Given(50, 1_000, 1_200, 1_400))
    assert made.of[Segment.BED_3].taken[T1] == (IN_TALLOWGATE, Given(250, 1_700, 1_950, 2_100))


def test_where_neither_has_a_figure_the_area_has_none_and_nothing_is_filled_in(made: Rents):
    assert taken(made, Segment.ROOM) == {
        Q1: None,
        Q2: None,
        T1: (IN_TALLOWGATE, Given(30, 700, 800, 900)),
    }
    assert taken(made, Segment.BED_4PLUS)[T1] is None
    held = {(row.area_id, row.segment) for row in rent.costs(made)}
    assert (Q1, Segment.ROOM) not in held and (T1, Segment.BED_4PLUS) not in held


def test_no_figure_is_taken_from_a_place_an_area_does_not_lie_in(made: Rents):
    """Every district that no area takes holds a canary in every cell."""
    assert A_CANARY[1] == CANARY_RENT
    for row in rent.costs(made):
        assert CANARY_RENT not in (row.lower_quartile, row.median, row.upper_quartile)
        assert row.of is not None and row.of.name not in (QH2, QT1)
    said = json.dumps([row.model_dump(mode="json") for row in rent.evidence(made)])
    assert str(CANARY_RENT) not in said


def test_the_mean_is_never_read(made: Rents):
    assert "Mean" not in rent.READ
    assert "Mean" not in (rent.COUNT, rent.LOWER, rent.MEDIAN, rent.UPPER)


def test_every_kind_of_home_the_contract_names_for_a_rent_is_read(made: Rents):
    assert tuple(rent.KINDS) == KINDS
    assert tuple(rent.KINDS.values()) == rent.HOMES
    assert set(made.of) == set(rent.HOMES)
    assert {row.segment for row in rent.costs(made)} <= set(rent.HOMES)


def test_the_rows_are_in_the_order_a_release_keeps_them(made: Rents):
    rows = rent.costs(made)
    assert list(rows) == sorted(rows, key=lambda row: (row.area_id, row.tenure, row.segment))
    assert len(rows) == 14


# The evidence.


def row_of(made: Rents, area: str, home: Segment):
    [row] = [row for row in rent.evidence(made) if row.fact_id == f"{area}/cost/rent.{home.value}"]
    return row


def test_a_row_of_evidence_says_how_much_of_the_area_stands_in_the_place(made: Rents):
    whole, borough, in_part = (row_of(made, area, Segment.BED_1) for area in AREAS)
    assert (whole.state, whole.weight_covered, whole.value) == (State.PRESENT, 1.0, 1_400.0)
    # An area lies wholly in its borough.
    assert (borough.state, borough.weight_covered, borough.value) == (State.PRESENT, 1.0, 1_500.0)
    assert (in_part.state, in_part.value) == (State.PARTIAL, 1_275.0)
    assert in_part.weight_covered == round(430 / 820, 6)


def test_a_row_of_evidence_says_which_kind_of_place_the_figure_is_of(made: Rents):
    assert row_of(made, Q1, Segment.BED_1).derivation_id == rent.OF_THE_DISTRICT.derivation_id
    assert row_of(made, Q2, Segment.BED_1).derivation_id == rent.OF_THE_BOROUGH.derivation_id
    assert {method.derivation_id for method in rent.METHODS} == {
        "rent_of_the_district@1",
        "rent_of_the_borough@1",
    }


def test_a_row_of_evidence_counts_the_rents_behind_its_figure(made: Rents):
    row = row_of(made, Q1, Segment.BED_1)
    assert (row.units_used, row.units_expected) == (170, 170)
    assert Flag.ROUNDED_IN_SOURCE in row.flags


def test_an_area_with_no_figure_has_a_row_that_says_why(made: Rents):
    gap = row_of(made, Q1, Segment.ROOM)
    assert (gap.state, gap.value, gap.weight_covered) == (State.SOURCE_GAP, None, 0.0)
    withheld = row_of(made, T1, Segment.BED_4PLUS)
    assert (withheld.state, withheld.value) == (State.SUPPRESSED, None)
    assert Flag.SUPPRESSED_IN_SOURCE in withheld.flags
    # A median with no range is no figure a release carries.
    assert row_of(made, Q2, Segment.STUDIO).state is State.SOURCE_GAP


def test_every_area_and_kind_of_home_has_a_row_of_evidence(made: Rents):
    rows = rent.evidence(made)
    assert len(rows) == len(AREAS) * len(rent.HOMES)
    assert len({row.fact_id for row in rows}) == len(rows)


def test_a_row_of_evidence_names_the_workbook_the_directory_and_the_files_of_the_spine(
    made: Rents,
):
    sources = sorted(receipt.source_id for receipt in made.files)
    assert sources == sorted({rent.SOURCE, postcodes.SOURCE, spine.LOOKUP, spine.HOMES})
    files = {receipt.file_id for receipt in made.files}
    assert all(set(row.inputs) == files for row in rent.evidence(made))
    assert {row.source_ids for row in rent.costs(made)} == {tuple(sources)}


def test_what_is_made_holds_no_postcode(made: Rents):
    said = repr(made) + json.dumps([row.model_dump(mode="json") for row in rent.costs(made)])
    for row in DIRECTORY:
        assert row.postcode not in said
        assert row.postcode.replace(" ", "") not in said


def test_the_same_files_give_the_same_figures_whatever_order_they_are_in(
    tmp_path: Path, made: Rents
):
    turned = book(dict(reversed(list(BOROUGHS.items()))), dict(reversed(list(DISTRICTS.items()))))
    again = built(tmp_path, content=turned, directory=tuple(reversed(DIRECTORY)))
    assert rent.costs(again) == rent.costs(made)
    assert [row.value for row in rent.evidence(again)] == [row.value for row in rent.evidence(made)]


def test_what_was_read_is_counted(made: Rents):
    counts = made.counts
    assert (counts.boroughs, counts.districts) == (2, 6)
    assert counts.areas_of_a_district == 2
    assert counts.areas_of_no_district == 1
    assert counts.by_home[Segment.BED_1] == {"postcode_district": 2, "borough": 1, "none": 0}
    assert counts.by_home[Segment.ROOM] == {"postcode_district": 0, "borough": 1, "none": 2}


# What the measure says of itself.


def test_the_definition_says_the_months_the_place_and_what_the_figure_is_not(made: Rents):
    said = made.of[Segment.BED_1].definition
    assert "April 2025 to March 2026" in said
    assert "postcode district" in said and "borough" in said
    assert "half or more of the homes" in said
    assert "not an asking rent" in said


def test_what_it_cannot_see_says_the_caution_of_the_publisher_in_plain_words():
    said = " ".join(rent.CANNOT_SEE)
    assert "not drawn at random" in said
    assert "comparing one area with another" in said
    assert "Housing Benefit" in said
    # It quotes no figure to make the point.
    assert not any(letter.isdigit() for letter in said)


# The gate.


def with_uses(*uses: Use) -> Registry:
    """The repository's registry, with the workbook registered for other uses."""
    sources = [
        source.model_copy(update={"uses": uses}) if source.id == rent.SOURCE else source
        for source in registry()
    ]
    return Registry(tuple(sources))


def test_the_registry_holds_the_workbook_for_a_cost_and_for_nothing_wider():
    assert rent.USE is Use.SCORING
    for allowed in (Use.SCORING, Use.DISPLAY):
        registry().require(rent.SOURCE, allowed)
    for wider in (Use.GAZETTEER, Use.ROUTING, Use.DESTINATION_SEARCH, Use.PROFILE_TEXT):
        with pytest.raises(RegistryError):
            registry().require(rent.SOURCE, wider)


def test_the_gate_is_asked_before_the_workbook_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, given=with_uses(Use.DISPLAY))
    found = spine.build(inputs)
    before = inputs.opened
    with pytest.raises(LockError) as refused:
        rent.build(inputs, found)
    assert (refused.value.rule, refused.value.subject) == ("gate_refuses", rent.SOURCE)
    assert inputs.opened == before


def test_with_no_receipt_of_the_workbook_nothing_is_read(tmp_path: Path):
    with pytest.raises(LockError) as refused:
        built(tmp_path, with_a_receipt=False)
    assert refused.value.rule == "input_has_one_receipt"


def test_with_no_receipt_of_the_directory_nothing_is_read(tmp_path: Path):
    with pytest.raises(LockError) as refused:
        built(tmp_path, directory=None)
    assert refused.value.rule == "input_has_one_receipt"


# A workbook that is not what the step was written to read.


def test_a_workbook_whose_months_are_not_those_of_its_receipt_stops_the_step(tmp_path: Path):
    other = book(contents_of=listed("January 2025 to December 2025"))
    assert "another period than its receipt" in refusal(tmp_path, other)
    year = Period(start="2025-01", end="2025-12")
    assert "another period than its receipt" in refusal(tmp_path / "b", book(), period=year)


def test_a_receipt_that_gives_no_twelve_months_stops_the_step(tmp_path: Path):
    assert "twelve months" in refusal(
        tmp_path, book(), period=Period(start="2025-04", end="2026-04")
    )


@pytest.mark.parametrize(
    "note",
    ["note 1", "note 2", "note 3", "note 4", "note 5", "note 7"],
)
def test_a_workbook_whose_notes_no_longer_say_what_is_said_of_it_stops_the_step(
    tmp_path: Path, note: str
):
    """What Burro says of a rent rests on these words. With other words it would not be so."""
    changed = dict(SAID_IN_THE_NOTES) | {note: "Made up for a test."}
    assert "its notes do not say" in refusal(tmp_path, book(notes=changed))


def test_a_workbook_whose_cover_no_longer_says_how_to_read_it_stops_the_step(tmp_path: Path):
    cover = [SAID_ON_THE_COVER[0], "Made up for a test.", *SAID_ON_THE_COVER[2:]]
    assert "its cover does not say" in refusal(tmp_path, book(cover=cover))


def test_a_kind_of_home_the_step_does_not_know_stops_the_step(tmp_path: Path):
    kinds = (*KINDS[:5], "Five or More Bedrooms")
    assert "a kind of home" in refusal(tmp_path, book(kinds=kinds))


def test_a_place_that_lacks_a_kind_of_home_stops_the_step(tmp_path: Path):
    short = {name: rows[:5] for name, rows in DISTRICTS.items()}
    sheet = table_of("3", short, named="Postcode District", kinds=KINDS[:5])
    assert "every kind of home once" in refusal(tmp_path, book(sheets={"3": sheet}))


def test_a_place_that_is_there_twice_stops_the_step(tmp_path: Path):
    sheet = table_of("2", BOROUGHS, named="Borough")
    assert "every kind of home once" in refusal(tmp_path, book(sheets={"2": [*sheet, sheet[3]]}))


@pytest.mark.parametrize("cell", ["n/a", "[x]", 0, -5, 1_400.5, ""])
def test_a_cell_that_is_neither_a_figure_nor_a_mark_stops_the_step(tmp_path: Path, cell: object):
    rows = {**DISTRICTS, QH1: ((170, 1_300, cell, 1_450), *DISTRICTS[QH1][1:])}
    assert "a figure is not a figure" in refusal(tmp_path, book(districts=rows))  # pyright: ignore[reportArgumentType]


def test_a_range_that_is_out_of_order_stops_the_step(tmp_path: Path):
    rows = {**DISTRICTS, QH1: ((170, 1_500, 1_400, 1_450), *DISTRICTS[QH1][1:])}
    assert "a range is out of order" in refusal(tmp_path, book(districts=rows))


def test_a_district_that_is_not_written_as_one_stops_the_step(tmp_path: Path):
    rows = {**DISTRICTS, "Quillhaven North": (A_CANARY,) * 6}
    assert "a district is not written as one" in refusal(tmp_path, book(districts=rows))


def test_a_borough_of_the_build_that_the_workbook_does_not_name_stops_the_step(tmp_path: Path):
    only = {QUILLHAVEN: BOROUGHS[QUILLHAVEN]}
    assert "a borough of the build has no row" in refusal(tmp_path, book(boroughs=only))


def test_a_workbook_that_lacks_a_table_stops_the_step(tmp_path: Path):
    assert "it does not hold the one sheet that is read" in refusal(tmp_path, book(without=("3",)))


def test_a_workbook_that_lacks_a_column_stops_the_step(tmp_path: Path):
    columns = ("Borough", "Bedroom Category", "Count of rents", "Mean", "Median")
    sheet = [row[:5] for row in table_of("2", BOROUGHS, named="Borough", columns=columns)]
    assert "the column Lower quartile is missing" in refusal(tmp_path, book(sheets={"2": sheet}))


def test_a_file_that_is_no_workbook_stops_the_step(tmp_path: Path):
    assert "it is not a workbook" in refusal(tmp_path, b"Borough,Median\r\n")


def test_a_count_of_under_ten_rents_is_no_figure(tmp_path: Path):
    """A count is rounded to 10 by its publisher, so one under 10 is one it never writes."""
    rows = {**DISTRICTS, QH1: ((9, 1_300, 1_400, 1_450), *DISTRICTS[QH1][1:])}
    assert "a count is not a count" in refusal(tmp_path, book(districts=rows))


def test_a_district_that_gives_nothing_for_any_kind_of_home_is_read(tmp_path: Path):
    rows = {**DISTRICTS, QH1: (NOT_AVAILABLE,) * 6, QT2: (SUPPRESSED,) * 6}
    made = built(tmp_path, content=book(districts=rows))
    assert made.of[Segment.BED_1].taken[Q1] == (IN_QUILLHAVEN, Given(520, 1_250, 1_500, 1_800))
    assert made.of[Segment.BED_1].taken[T1] == (IN_TALLOWGATE, Given(240, 1_100, 1_300, 1_450))


def test_what_is_made_is_frozen(made: Rents):
    with pytest.raises(dataclasses.FrozenInstanceError):
        made.since = "2020-01"  # pyright: ignore[reportAttributeAccessIssue]
