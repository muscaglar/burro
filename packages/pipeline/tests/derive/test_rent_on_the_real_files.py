"""What homes let for, worked out from the workbook its publisher gave.

Every other test of the measure runs on a made-up workbook. These read the real
one, with the real postcode directory, and are skipped where the store of
fetched files is not. The store is named by BURRO_STORE_FOLDER, and each file
is read through its receipt in `data/receipts/`.

They hold the counts and the states, so that a publisher's file that changes is
noticed. They hold no figure, and no name of a place below a borough: the
rent of a district is one row of the publisher's workbook, and no tracked file
holds a figure of a named place. Each count was made on 2026-09-25, from the
workbook of April 2025 to March 2026 and the directory of August 2026, and no
person has checked one.

The workbook gives a table of London as a whole, which is not read. So no sum
is held. What is held in its place is what must be so of any such figures:
every range stands in order, every area of one place shows one figure, and
every figure is the publisher's own row for the place, which is read again and
compared.

Nothing is written to the store. A file is copied out of it to be read.
"""

from collections import Counter

import pytest
from burro_core.ids import Confidence, CostOfKind, Segment, Tenure
from burro_pipeline.cells import postcodes, spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import rent
from burro_pipeline.derive.rent import Rents
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs

from .real_files import SKIPPED, real_inputs

pytestmark = SKIPPED
WORKBOOK = "f-48d278998714"
AREAS = 1_002
ROOM, STUDIO, ONE, TWO, THREE, FOUR = rent.HOMES


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine) -> Rents:
    return rent.build(real, found)


# The workbook


def test_the_workbook_says_of_itself_what_a_page_of_burro_says_of_it(real: Inputs):
    """The step stops at a workbook that does not. Here it is read, and stops nowhere."""
    opened = real.open(rent.SOURCE, rent.USE, named=rent.is_the_workbook)
    assert opened.file_id == WORKBOOK
    read = rent.read(opened)
    assert (read.since, read.until) == ("2025-04", "2026-03")
    assert read.months == "April 2025 to March 2026"


def test_the_tables_name_as_many_places_as_were_counted(real: Inputs, found: Spine):
    read = rent.read(real.open(rent.SOURCE, rent.USE, named=rent.is_the_workbook))
    assert (len(read.boroughs.places), len(read.districts.places)) == (33, 329)
    # The workbook writes a borough by the name the lookup gives it, the City included.
    assert set(read.boroughs.places) == {area.borough for area in found.areas}
    # No row of this edition is marked as withheld: what is not given is not available.
    assert (read.boroughs.withheld, read.districts.withheld) == (frozenset(), frozenset())


def test_the_rows_that_hold_a_range_are_as_many_as_were_counted(real: Inputs):
    read = rent.read(real.open(rent.SOURCE, rent.USE, named=rent.is_the_workbook))
    of_boroughs = Counter(home for _, home in read.boroughs.given)
    of_districts = Counter(home for _, home in read.districts.given)
    assert of_boroughs == {ROOM: 29, STUDIO: 30, ONE: 33, TWO: 33, THREE: 32, FOUR: 32}
    assert of_districts == {ROOM: 46, STUDIO: 67, ONE: 211, TWO: 214, THREE: 202, FOUR: 126}


# Where the homes of an area stand


def test_the_areas_that_lie_in_a_district_are_as_many_as_were_counted(made: Rents):
    assert len(made.stood) == AREAS
    assert (made.counts.areas_of_a_district, made.counts.areas_of_no_district) == (959, 43)
    assert all(where.of > 0 and 0 < where.homes <= where.of for where in made.stood.values())
    lie_in = [where for where in made.stood.values() if where.district is not None]
    assert all(2 * where.homes >= where.of for where in lie_in)
    assert Counter(where.districts for where in made.stood.values()) == {
        1: 390,
        2: 451,
        3: 138,
        4: 15,
        5: 3,
        6: 1,
        8: 2,
        11: 1,
        12: 1,
    }


def test_every_district_an_area_lies_in_is_a_district_of_the_workbook(real: Inputs, made: Rents):
    read = rent.read(real.open(rent.SOURCE, rent.USE, named=rent.is_the_workbook))
    lie_in = {where.district for where in made.stood.values() if where.district is not None}
    assert len(lie_in) == 213
    assert lie_in <= set(read.districts.places)


# The figures


def test_the_areas_with_a_figure_of_each_kind_of_place_are_as_many_as_were_counted(
    made: Rents,
):
    assert made.counts.by_home == {
        ROOM: {"postcode_district": 284, "borough": 646, "none": 72},
        STUDIO: {"postcode_district": 355, "borough": 575, "none": 72},
        ONE: {"postcode_district": 913, "borough": 89, "none": 0},
        TWO: {"postcode_district": 932, "borough": 70, "none": 0},
        THREE: {"postcode_district": 929, "borough": 72, "none": 1},
        FOUR: {"postcode_district": 663, "borough": 338, "none": 1},
    }


def test_every_figure_is_the_publishers_own_row_for_the_place(real: Inputs, made: Rents):
    """A reader who opens the publisher's table for the place finds these numbers."""
    read = rent.read(real.open(rent.SOURCE, rent.USE, named=rent.is_the_workbook))
    tables = {CostOfKind.POSTCODE_DISTRICT: read.districts, CostOfKind.BOROUGH: read.boroughs}
    checked = 0
    for home, let in made.of.items():
        for area, (of, given) in let.taken.items():
            assert tables[of.kind].given[of.name, home] == given
            if of.kind is CostOfKind.POSTCODE_DISTRICT:
                assert made.stood[area].district == of.name
            checked += 1
    assert checked == len(rent.costs(made)) == 5_866


def test_every_area_of_one_place_shows_one_figure_and_none_is_held_here(made: Rents):
    """What a figure is, and not how much: no tracked file holds the figure of a place."""
    rows = rent.costs(made)
    of_a_place: dict[tuple[CostOfKind, str, Segment], set[tuple[int, int, int, int]]] = {}
    for row in rows:
        assert row.of is not None and row.rents is not None
        assert row.lower_quartile is not None and row.upper_quartile is not None
        assert 0 < row.lower_quartile <= row.median <= row.upper_quartile
        assert (row.tenure, row.since, row.as_of) == (Tenure.RENT, "2025-04", "2026-03")
        assert row.rents >= rent.FEWEST and row.rents % 10 == 0
        figure = (row.rents, row.lower_quartile, row.median, row.upper_quartile)
        of_a_place.setdefault((row.of.kind, row.of.name, row.segment), set()).add(figure)
    assert all(len(figures) == 1 for figures in of_a_place.values())
    districts = {name for kind, name, _ in of_a_place if kind is CostOfKind.POSTCODE_DISTRICT}
    boroughs = {name for kind, name, _ in of_a_place if kind is CostOfKind.BOROUGH}
    assert (len(districts), len(boroughs)) == (209, 33)


def test_what_each_figure_rests_on_is_what_its_count_makes_it(made: Rents):
    rests_on = Counter((row.segment, row.confidence) for row in rent.costs(made))
    assert rests_on == {
        (ROOM, Confidence.HIGH): 205,
        (ROOM, Confidence.MEDIUM): 725,
        (STUDIO, Confidence.HIGH): 330,
        (STUDIO, Confidence.MEDIUM): 600,
        (ONE, Confidence.HIGH): 693,
        (ONE, Confidence.MEDIUM): 309,
        (TWO, Confidence.HIGH): 827,
        (TWO, Confidence.MEDIUM): 175,
        (THREE, Confidence.HIGH): 589,
        (THREE, Confidence.MEDIUM): 412,
        (FOUR, Confidence.HIGH): 380,
        (FOUR, Confidence.MEDIUM): 621,
    }


# The evidence


def test_the_states_of_the_rows_of_evidence_are_as_many_as_were_counted(made: Rents):
    states = {home: Counter(row.state for row in let.rows) for home, let in made.of.items()}
    assert states == {
        ROOM: {State.PRESENT: 761, State.PARTIAL: 169, State.SOURCE_GAP: 72},
        STUDIO: {State.PRESENT: 717, State.PARTIAL: 213, State.SOURCE_GAP: 72},
        ONE: {State.PRESENT: 454, State.PARTIAL: 548},
        TWO: {State.PRESENT: 442, State.PARTIAL: 560},
        THREE: {State.PRESENT: 438, State.PARTIAL: 563, State.SOURCE_GAP: 1},
        FOUR: {State.PRESENT: 619, State.PARTIAL: 382, State.SOURCE_GAP: 1},
    }
    for row in rent.evidence(made):
        assert (row.value is None) == (row.state is State.SOURCE_GAP)
        assert row.flags == (() if row.value is None else (Flag.ROUNDED_IN_SOURCE,))
        # A figure of a district says how much of the area stands in it: half or more.
        assert row.value is None or row.weight_covered >= 0.5


def test_every_figure_rests_on_the_four_files_that_stand_behind_it(made: Rents):
    assert sorted(receipt.source_id for receipt in made.files) == [
        spine.HOMES,
        spine.LOOKUP,
        postcodes.SOURCE,
        rent.SOURCE,
    ]
    files = tuple(sorted(receipt.file_id for receipt in made.files))
    rows = rent.evidence(made)
    assert len(rows) == 6 * AREAS
    assert all(row.inputs == files for row in rows)
    assert {row.derivation_id for row in rows} == {
        "rent_of_the_district@1",
        "rent_of_the_borough@1",
    }
    evidence = Evidence.of("lon-2026-09-25-61", made.files, rent.METHODS, rows)
    assert len(evidence.rows) == 6 * AREAS


def test_what_is_made_names_no_postcode(made: Rents):
    """A district is what stands before the space of a postcode, and is no postcode."""
    names = {row.of.name for row in rent.costs(made) if row.of is not None}
    assert all(" " not in name or name in made_boroughs(made) for name in names)
    districts = names - made_boroughs(made)
    assert all(rent.A_DISTRICT.fullmatch(name) for name in districts)


def made_boroughs(made: Rents) -> set[str]:
    return {
        of.name
        for let in made.of.values()
        for of, _ in let.taken.values()
        if of.kind is CostOfKind.BOROUGH
    }
