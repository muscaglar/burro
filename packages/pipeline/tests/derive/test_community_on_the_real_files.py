"""Places of worship and centres nearby, held to the file its publisher gave.

Every other test of the two measures runs on made-up places. These read the
real part of the file of places, and are skipped where it has no receipt. The
store is named by BURRO_STORE_FOLDER, and the file is read through its receipt
in `data/receipts/`.

They hold what must be so of any file of places, and the counts that the part
of release 2026-09-23.0 gave when it was first read. A count is of buildings,
and of the part as a whole. None is said of a named area, none is set over a
count of homes, and none says how many kinds are anywhere.

Nothing is written to the store. A file is copied out of it to be read.
"""

import os
from collections import Counter
from pathlib import Path

import pytest
from burro_pipeline.cells import land, spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import (
    centres_nearby,
    culture_check,
    culture_file,
    homes_density,
    worship_kinds,
    worship_nearby,
)
from burro_pipeline.derive.centres_nearby import Centres
from burro_pipeline.derive.culture_reach import ground_of
from burro_pipeline.derive.places_counted import held_against_the_centre
from burro_pipeline.derive.worship_nearby import Worship
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.evidence.row import State
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
pytestmark = pytest.mark.skipif(
    not (
        STORE
        and Path(STORE).is_dir()
        and RECEIPTS.is_dir()
        and (RECEIPTS / culture_file.SOURCE).is_dir()
    ),
    reason="the part of the file of places has not been fetched: it has no receipt",
)


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    work = tmp_path_factory.mktemp("real")
    return Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), work)


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def worship(real: Inputs, found: Spine) -> Worship:
    return worship_nearby.build(real, found)


@pytest.fixture(scope="module")
def centres(real: Inputs, found: Spine) -> Centres:
    return centres_nearby.build(real, found)


def test_every_row_of_the_part_is_read_and_every_row_is_counted_once(
    worship: Worship, centres: Centres
):
    for held in (worship.held, centres.held):
        assert held.file.taken is not None and held.rows == held.file.taken.rows
        assert held.rows == len(held.records) + sum(held.left_out.values())
        assert sum(held.counted_as.values()) == len(held.records)
    again = sum(worship.records_of_one_building.values())
    assert len(worship.buildings) + again == len(worship.held.records)


def test_the_part_holds_the_places_of_worship_it_held_when_it_was_first_read(worship: Worship):
    """Of 683,409 rows, 9,074 are a place of worship, and they are 8,048 buildings. The part is
    the row groups that may hold a place in the box, so it holds rows that stand outside the
    box, and these are counts of the part and not of London."""
    held = worship.held
    assert held.rows == 683_409 and len(held.records) == 9_074
    assert held.by_kind == {
        "buddhist_temple": 67,
        "church": 8_189,
        "gurdwara": 62,
        "hindu_temple": 155,
        "mosque": 445,
        "no_kind_named": 3,
        "synagogue": 153,
    }
    assert dict(held.left_out) == {"beside": 6_427, "no_category": 51_966, "not_worship": 615_942}
    assert dict(Counter(one.kind for one in worship.buildings)) == {
        "buddhist_temple": 65,
        "church": 7_237,
        "gurdwara": 59,
        "hindu_temple": 143,
        "mosque": 397,
        "no_kind_named": 3,
        "synagogue": 144,
    }


def test_the_part_holds_the_centres_it_held_when_it_was_first_read(centres: Centres):
    held = centres.held
    assert held.rows == 683_409
    assert held.by_kind == {"community_centre": 1_532, "cultural_centre": 120}
    assert dict(held.left_out) == {
        "beside": 14_302,
        "no_category": 51_966,
        "not_a_centre": 610_541,
        "parent_alone": 4_948,
    }
    assert dict(Counter(one.kind for one in centres.buildings)) == {
        "community_centre": 1_506,
        "cultural_centre": 120,
    }
    # More records are filed as a scout hall than as a community centre, and none is counted.
    assert held.left_out_as["scout_hall"] == 1_702


def test_every_category_under_the_two_tops_that_the_part_holds_is_on_a_table(
    worship: Worship, centres: Centres
):
    """A record under either top is counted or is left out by the name of its category. One
    that is neither stops the build, so that the part was read says the rest."""
    assert set(worship.held.counted_as) <= set(worship_kinds.IS)
    assert set(worship.held.left_out_as) <= set(worship_kinds.IS_NOT)
    assert (len(worship.held.counted_as), len(worship.held.left_out_as)) == (13, 11)
    assert set(centres.held.counted_as) == set(centres_nearby.IS)
    assert set(centres.held.left_out_as) <= set(centres_nearby.IS_NOT) | centres_nearby.PARENTS
    assert len(centres.held.left_out_as) == 51


def test_of_the_branches_of_religion_beside_a_place_of_worship_the_part_holds_one(
    worship: Worship,
):
    """No shrine, no monastery, no convent and no retreat has a category of its own in the
    part. What the part holds beside a place of worship is filed as an organisation."""
    beside = set(worship.held.left_out_as) & set(worship_kinds.OF_RELIGION)
    assert beside == {"religious_organization"}


def test_no_record_filed_as_something_else_names_a_place_of_worship_beside_it(worship: Worship):
    """This release says what else a record is of 2,010 records in 683,409, and of none of
    them that it is a place of worship."""
    assert worship.said_beside == {}


def test_every_record_names_its_publisher_beside_the_source_that_gave_it(
    worship: Worship, centres: Centres
):
    """The licence registry names the sources whose licence it has read. The file names the
    publisher itself beside one of them in every record, under `Overture`: a look at the file
    found that it is named as what gave the number for how sure the publisher is."""
    for held in (worship.held, centres.held):
        assert held.by_dataset["Overture"] == len(held.records)
        assert set(held.by_dataset) <= {
            "AllThePlaces",
            "Foursquare",
            "Microsoft",
            "Overture",
            "meta",
        }


def test_the_buildings_that_stand_close_to_another_of_their_kind_are_among_the_buildings(
    worship: Worship, centres: Centres
):
    """How many stand close is held to no number, because none has been looked at. A person
    reads it to say whether 25 metres is right for records to be one building."""
    for made in (worship, centres):
        of_kind = Counter(one.kind for one in made.buildings)
        for kind, close in made.close_together.items():
            assert 2 <= close <= of_kind[kind.value]


def test_every_kind_of_building_is_found_in_the_part_of_london(worship: Worship, centres: Centres):
    """A category that the table writes in other words than the file does is counted nowhere,
    and nothing stops. So a kind with no record in the whole of the part is held to be a
    fault of the table, and never a count of nought.
    """
    of_worship = worship.held.by_kind
    assert [kind.value for kind in worship_kinds.KINDS if not of_worship.get(kind.value)] == []
    of_centres = centres.held.by_kind
    assert [kind.value for kind in centres_nearby.KINDS if not of_centres.get(kind.value)] == []


def test_every_area_has_a_row_and_no_figure_stands_on_under_half_its_homes(
    worship: Worship, centres: Centres, found: Spine
):
    every = [worship.worked, *worship.of_kind.values(), *centres.of_kind.values()]
    for worked in every:
        assert set(worked) == set(found.weights.areas)
        for one in worked.values():
            assert (one.value is None) == (one.state not in (State.PRESENT, State.PARTIAL))
            assert one.value is None or (one.weight_covered >= 0.5 and one.value >= 0)


def test_the_places_of_worship_of_an_area_are_no_fewer_than_those_of_any_one_kind(
    worship: Worship,
):
    """Each is given to one decimal place, so a kind may stand above the whole by a rounding."""
    for worked in worship.of_kind.values():
        for area, one in worked.items():
            whole = worship.worked[area].value
            assert one.value is None or (whole is not None and one.value <= whole + 0.1)


def test_each_figure_is_held_against_the_centre_in_lines_of_numbers(
    real: Inputs, worship: Worship, centres: Centres, found: Spine
):
    density = {
        area: one.value
        for area, one in homes_density.build(real, found, land.build(real, found)).worked.items()
    }
    ground = ground_of(real, found)
    of_worship = {worship_nearby.KEY: worship.worked} | {
        worship_nearby.KEY_OF[kind]: worked for kind, worked in worship.of_kind.items()
    }
    of_centres = {centres_nearby.KEY_OF[kind]: worked for kind, worked in centres.of_kind.items()}
    held = (
        *held_against_the_centre(of_worship, worship.nearby, found, density, ground),
        *held_against_the_centre(of_centres, centres.nearby, found, density, ground),
    )
    assert len(held) == 9
    assert all(culture_check.is_a_line_of_numbers(one.line()) for one in held)
    # What release 2026-09-23.0 gave, across the 992 areas that have a figure: with homes per
    # hectare, with the distance from the middle, and with a count of every record. Places of
    # worship and churches are mostly a map of how built up an area is. The kinds with few
    # buildings are not: each is a map of where the file holds such a building.
    assert {
        one.figure: tuple(
            round(each or 0, 2) for each in (one.with_density, one.with_distance, one.with_every)
        )
        for one in held
    } == {
        "worship_places": (0.77, -0.71, 0.82),
        "worship_churches": (0.76, -0.71, 0.80),
        "worship_mosques": (0.53, -0.42, 0.57),
        "worship_synagogues": (0.14, -0.21, 0.21),
        "worship_hindu_temples": (0.17, -0.09, 0.18),
        "worship_gurdwaras": (0.08, 0.03, 0.11),
        "worship_buddhist_temples": (0.27, -0.28, 0.29),
        "community_centres": (0.61, -0.58, 0.58),
        "cultural_centres": (0.42, -0.42, 0.52),
    }
    assert {one.areas for one in held} == {992}
