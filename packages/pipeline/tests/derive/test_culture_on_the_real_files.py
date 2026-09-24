"""Culture nearby, held to the files their publishers gave.

Every other test of the measure runs on made-up places. These read real files,
and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

The first tests hold the box of the list to where London's homes are, from the
centres of the first build. They run wherever the store is.

The rest read the part of the file of places, and are skipped where it has
no receipt. They hold what must be so of any file of places, and the counts
that the part of release 2026-09-23.0 gave when it was first read. A count is
of the part, or of London as a whole. None is said of a named area.

Nothing is written to the store. A file is copied out of it to be read.
"""

import os
from pathlib import Path

import pytest
from burro_pipeline.cells import centres, land, spine
from burro_pipeline.cells.shapes import longitude_and_latitude
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import culture_check, culture_file, culture_venues, homes_density
from burro_pipeline.derive.culture_kinds import ELSEWHERE, IS, IS_NOT, PARENTS, LeftOut
from burro_pipeline.derive.culture_reach import METRES, ground_of, metres_to_a_degree
from burro_pipeline.derive.culture_venues import Culture
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.evidence.row import State
from burro_pipeline.fetch.sources import load_list
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.fetch.take import plan_in
from burro_pipeline.inputs import Inputs

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and RECEIPTS.is_dir()),
    reason=f"the store of fetched files is not here: {FOLDER_VARIABLE} names no folder",
)
FETCHED = (RECEIPTS / culture_file.SOURCE).is_dir()
NOT_FETCHED = pytest.mark.skipif(
    not FETCHED, reason="the part of the file of places has not been fetched: it has no receipt"
)


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    work = tmp_path_factory.mktemp("real")
    return Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), work)


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine) -> Culture:
    return culture_venues.build(real, found)


# The box of the list


def test_the_box_holds_every_home_of_london_with_more_than_twice_the_reach_to_spare(
    real: Inputs, found: Spine
):
    """So a venue within reach of any home of London is in the part that is taken."""
    (file,) = load_list("m2-culture").files
    assert file.take is not None
    west, south, east, north = file.take.box
    at = [longitude_and_latitude(*point) for point in centres.build(real, found).values()]
    assert len(at) == len(found.area_of) == 26_369
    across, up = metres_to_a_degree(north)
    spare = 2 * METRES
    assert min(point[0] for point in at) - west > spare / across
    assert east - max(point[0] for point in at) > spare / across
    assert min(point[1] for point in at) - south > spare / up
    assert north - max(point[1] for point in at) > spare / up


def test_the_box_is_no_wider_than_it_needs_to_be(real: Inputs, found: Spine):
    """It holds land outside London, and no more than 5,000 metres of it on any side."""
    (file,) = load_list("m2-culture").files
    assert file.take is not None
    west, south, east, north = file.take.box
    at = [longitude_and_latitude(*point) for point in centres.build(real, found).values()]
    across, up = metres_to_a_degree(south)
    assert (min(point[0] for point in at) - west) * across < 5_000
    assert (east - max(point[0] for point in at)) * across < 5_000
    assert (min(point[1] for point in at) - south) * up < 5_000
    assert (north - max(point[1] for point in at)) * up < 5_000


# The part, once it is fetched


@NOT_FETCHED
def test_the_part_in_the_store_is_the_part_the_list_asks_for(real: Inputs):
    (file,) = load_list("m2-culture").files
    assert file.take is not None
    opened = real.open(culture_file.SOURCE, file.use, named=culture_file.is_the_file)
    taken = opened.receipt.taken
    assert taken is not None and opened.receipt.edition == file.edition
    assert (taken.box, taken.box_in) == (file.take.box, file.take.box_in)
    assert taken.columns == tuple(sorted(file.take.columns))
    plan = plan_in(opened.path, taken.runs, taken.of_bytes, file.take)
    assert (plan.row_groups, plan.runs) == (taken.row_groups, taken.runs)


@NOT_FETCHED
def test_every_row_of_the_part_is_read_and_every_row_is_counted_once(made: Culture):
    places = made.places
    assert places.file.taken is not None and places.rows == places.file.taken.rows
    assert places.rows == len(places.venues) + sum(places.left_out.values())
    assert sum(places.counted_as.values()) == len(places.venues)
    assert len(made.venues) + sum(made.records_of_one_venue.values()) == len(places.venues)


@NOT_FETCHED
def test_the_part_holds_the_records_it_held_when_it_was_first_read(made: Culture):
    """Of 683,409 rows, 7,641 are of a kind, and they are 6,908 venues. The part is the row
    groups that may hold a place in the box, so it holds rows that stand outside the box."""
    places = made.places
    assert places.rows == 683_409
    assert {kind.value: count for kind, count in places.by_kind.items()} == {
        "museum": 1_023,
        "gallery": 2_330,
        "theatre": 712,
        "cinema": 618,
        "music_venue": 1_617,
        "library": 1_341,
    }
    assert dict(places.left_out) == {
        LeftOut.NO_CATEGORY: 51_966,
        LeftOut.NOT_A_KIND: 6_433,
        LeftOut.NOT_CULTURE: 612_930,
        LeftOut.PARENT_ALONE: 4_439,
    }
    assert len(made.venues) == 6_908
    assert sum(made.records_of_one_venue.values()) == 733


@NOT_FETCHED
def test_every_category_of_the_arts_that_the_part_holds_is_on_the_table(made: Culture):
    """A record of the arts and of entertainment is counted or is left out by the name of its
    category. One that is neither stops the build, so that the part was read says the rest.
    """
    places = made.places
    assert set(places.counted_as) <= set(IS)
    assert set(places.left_out_as) <= set(IS_NOT) | PARENTS
    assert len(places.counted_as) == 25 and len(places.left_out_as) == 59
    assert len(set(places.left_out_as) & set(ELSEWHERE)) == 46


@NOT_FETCHED
def test_no_record_of_a_kind_says_that_it_teaches_and_none_says_that_it_has_closed(
    made: Culture,
):
    """The rule that leaves out a stage school asks what else a record says it is, and this
    release says what else of 2,010 records in 683,409. So the rule leaves out nothing, and a
    stage school that is filed as a theatre is counted as one."""
    left_out = made.places.left_out
    assert LeftOut.ALSO_TEACHES not in left_out and LeftOut.CLOSED not in left_out


@NOT_FETCHED
def test_every_record_of_a_kind_names_its_publisher_beside_the_source_that_gave_it(
    made: Culture,
):
    """The licence registry names the sources whose licence it has read. Every record of a
    kind came from one of four of them, and names the publisher itself beside it, under
    `Overture`. A source that is met here for the first time fails this test, so that a person
    reads its licence before a record of it is counted."""
    found = made.places.by_dataset
    assert found["Overture"] == len(made.places.venues)
    assert set(found) == {"AllThePlaces", "Foursquare", "Microsoft", "Overture", "meta"}
    assert all(len(set(one.datasets) - {"Overture"}) == 1 for one in made.places.venues)


@NOT_FETCHED
def test_the_file_holds_something_within_reach_of_every_home_of_london(made: Culture):
    """So nought is a count wherever a count is given, and the rule that asks whether the file
    holds anything within reach leaves out no output area of this release."""
    assert made.nothing_seen == ()
    assert len(made.reach.near_the_edge) == 311 and len(made.counted) == 26_058
    given = [one.value is not None for one in made.worked.values()]
    assert (sum(given), len(given)) == (992, 1_002)


@NOT_FETCHED
def test_every_kind_is_found_in_the_part_of_london(made: Culture):
    """A category that the table writes in other words than the file does is counted nowhere,
    and nothing stops: the record is read as no record of culture. So a kind with no record
    in the whole of the part is held to be a fault of the table, and never a count of nought.
    """
    found = made.places.by_kind
    assert [kind.value for kind, count in found.items() if count == 0] == []


@NOT_FETCHED
def test_every_area_has_a_row_and_no_figure_stands_on_under_half_its_homes(
    made: Culture, found: Spine
):
    for worked in (made.worked, made.rate, made.kinds):
        assert set(worked) == set(found.weights.areas)
        for one in worked.values():
            assert (one.value is None) == (one.state not in (State.PRESENT, State.PARTIAL))
            assert one.value is None or (one.weight_covered >= 0.5 and one.value >= 0)
    assert all(0 <= one.value <= 6 for one in made.kinds.values() if one.value is not None)


@NOT_FETCHED
def test_the_check_says_which_figure_to_put_forward_in_lines_of_numbers(
    real: Inputs, made: Culture, found: Spine
):
    density = homes_density.build(real, found, land.build(real, found)).worked
    result = culture_check.check(
        made, found, {area: one.value for area, one in density.items()}, ground_of(real, found)
    )
    assert all(culture_check.is_a_line_of_numbers(line) for line in result.lines())
    assert result.put_forward in (None, culture_venues.KEY_OF_THE_RATE)


@NOT_FETCHED
def test_the_count_is_mostly_a_map_of_the_centre_and_the_rate_less_so(
    real: Inputs, made: Culture, found: Spine
):
    """What the check found of release 2026-09-23.0, across the 992 areas that have a figure.
    Neither figure stands in the order of the centre at 0.9, so the rule puts nothing forward
    and a person decides. How many kinds are within reach is the count again."""
    density = homes_density.build(real, found, land.build(real, found)).worked
    result = culture_check.check(
        made, found, {area: one.value for area, one in density.items()}, ground_of(real, found)
    )
    assert result.put_forward is None
    assert [
        (one.figure, one.areas, *(round(each or 0, 2) for each in against))
        for one in result.held
        for against in [(one.with_density, one.with_distance, one.with_every)]
    ] == [
        ("culture_venues", 992, 0.76, -0.82, 0.86),
        ("culture_venues_per_homes", 992, 0.53, -0.66, 0.69),
        ("culture_kinds_nearby", 992, 0.75, -0.80, 0.85),
    ]
