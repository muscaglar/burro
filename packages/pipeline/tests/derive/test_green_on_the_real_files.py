"""Green cover and the nearest park, worked out from the files their publishers gave.

Every other test of the two measures runs on made-up sites. These read the
real files, and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts and, for each measure, London's lowest, middle and highest
figure, so that a publisher's file that changes is noticed. None is said of a
named area. Each was worked out on 2026-09-24, by a program. No person has
held any of them against a map.

Contains OS data © Crown copyright and database right 2026. Source: Office for
National Statistics licensed under the Open Government Licence v.3.0.

Nothing is written to the store. A file is copied out of it to be read.
"""

import math
import statistics
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

import pytest
from burro_pipeline.cells import land, spine
from burro_pipeline.cells.land import Land
from burro_pipeline.cells.shapes import hectares_inside, joined
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import green_cover, green_sites, park_proximity
from burro_pipeline.derive.green_cover import Cover
from burro_pipeline.derive.green_sites import Greenspace
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.park_proximity import Distances, Proximity
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from .real_files import SKIPPED, STORE, real_inputs

pytestmark = SKIPPED
# The two squares London lies on, by the ids of their receipts, and the edition of both.
TQ, TL, EDITION = "f-02f39a296d6f", "f-f9c10aca1661", "2026-04"
# The boundaries of LSOAs, the centres, the lookup and the table of homes.
BOUNDARIES, CENTRES, LOOKUP, HOMES = (
    "f-9f549e33f46b",
    "f-00e1d0532798",
    "f-49321b95f212",
    "f-af7b512615ea",
)


def listing() -> dict[str, tuple[int, int]]:
    """Every file of the store, with its size and when it was last written."""
    return {
        path.relative_to(STORE).as_posix(): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in sorted(Path(STORE).rglob("*"))
        if path.is_file()
    }


@pytest.fixture(scope="module")
def before() -> dict[str, tuple[int, int]]:
    return listing()


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory, before: dict[str, tuple[int, int]]) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def measured(real: Inputs, found: Spine) -> Land:
    return land.build(real, found)


@pytest.fixture(scope="module")
def green(real: Inputs) -> Greenspace:
    return green_sites.build(real, edition=EDITION)


@pytest.fixture(scope="module")
def cover(real: Inputs, found: Spine, measured: Land) -> Cover:
    return green_cover.build(real, found, measured, edition=EDITION)


@pytest.fixture(scope="module")
def near(real: Inputs, found: Spine) -> Proximity:
    return park_proximity.build(real, found, edition=EDITION)


@pytest.fixture(scope="module")
def large(real: Inputs, found: Spine) -> Proximity:
    return park_proximity.build_large(real, found, edition=EDITION)


def three_of(worked: Mapping[str, Worked]) -> tuple[float, float, float]:
    """London's lowest, middle and highest figure."""
    values = sorted(one.value for one in worked.values() if one.value is not None)
    return values[0], statistics.median(values), values[-1]


def on_both_squares(made: Cover | Distances) -> int:
    """How many areas have a figure that rests on the files of both squares."""
    return sum({TQ, TL} <= set(row.inputs) for row in made.rows)


# The files


def test_the_two_files_hold_as_many_sites_and_ways_in_as_were_counted(green: Greenspace):
    assert green.file_of == {(500_000, 100_000): TQ, (500_000, 200_000): TL}
    assert (len(green.sites), len(green.ways_in), green.in_two_files) == (31_961, 67_203, 23)
    assert green.as_at == EDITION


def test_each_kind_of_site_is_there_as_often_as_was_counted(green: Greenspace):
    assert Counter(site.kind for site in green.sites.values()) == {
        "Play Space": 9_459,
        "Public Park Or Garden": 4_647,
        "Playing Field": 3_667,
        "Other Sports Facility": 3_554,
        "Religious Grounds": 3_427,
        "Allotments Or Community Growing Spaces": 2_615,
        "Tennis Court": 2_267,
        "Cemetery": 921,
        "Bowling Green": 889,
        "Golf Course": 515,
    }
    assert Counter(way.access for way in green.ways_in) == {
        "Pedestrian": 54_149,
        "Motor Vehicle And Pedestrian": 12_939,
        "Motor Vehicle": 115,
    }


def test_every_way_in_is_to_a_site_of_the_files(green: Greenspace):
    assert all(way.site_id in green.sites for way in green.ways_in)


# Green cover


def test_every_area_has_a_figure_for_green_cover_and_is_wholly_covered(cover: Cover):
    assert (cover.parks, cover.sites, len(cover.inside)) == (4_647, 31_961, 4_994)
    assert Counter(one.state for one in cover.worked.values()) == {State.PRESENT: 1_002}
    assert {one.weight_covered for one in cover.worked.values()} == {1.0}
    assert three_of(cover.worked) == (0.0, 3.3, 78.1)


def test_the_park_land_of_the_lsoas_adds_up_to_the_park_land_of_london_as_one(
    real: Inputs, found: Spine, green: Greenspace, cover: Cover
):
    """The check of the sum: London as one outline, against 4,994 outlines added up."""
    boundaries = real.open(land.BOUNDARIES, Use.SCORING, edition=land.BOUNDARIES_EDITION)
    london = joined(list(land.read(boundaries, found).values()))
    whole = hectares_inside({"london": london}, green_cover.parks_of(green))["london"]
    # Each of 4,994 sums is rounded to a square metre.
    assert math.isclose(whole, green_cover.hectares_in(cover.inside), abs_tol=0.25)


def test_no_area_holds_more_park_land_than_land(cover: Cover, measured: Land):
    assert all(0.0 <= cover.inside[lsoa] <= measured.of_lsoa[lsoa] for lsoa in cover.inside)
    assert all(0.0 <= one.value <= 100.0 for one in cover.worked.values() if one.value is not None)


def test_green_cover_is_named_as_core_names_it_so_a_release_carries_it(cover: Cover):
    assert says_what_core_says(cover.metric)
    assert cover.metric.label.startswith("Public parks and gardens")
    assert cover.metric.vintage == EDITION


# The nearest park


def test_every_area_has_a_distance_to_a_park_and_is_wholly_covered(near: Proximity):
    assert (near.parks.parks, near.parks.without_a_way_in) == (1_477, 10)
    assert (len(near.parks.ways_in), len(near.of_oa)) == (12_743, 26_369)
    assert Counter(one.state for one in near.worked.values()) == {State.PRESENT: 1_002}
    assert three_of(near.worked) == (110.0, 450.0, 2_020.0)


def test_every_area_has_a_distance_to_a_large_park_and_is_wholly_covered(large: Proximity):
    assert (large.parks.parks, large.parks.without_a_way_in) == (312, 2)
    assert (len(large.parks.ways_in), len(large.of_oa)) == (4_685, 26_369)
    assert Counter(one.state for one in large.worked.values()) == {State.PRESENT: 1_002}
    assert three_of(large.worked) == (120.0, 1_030.0, 4_290.0)


def test_a_large_park_is_never_nearer_than_a_park(near: Proximity, large: Proximity):
    assert all(large.of_oa[oa] >= near.of_oa[oa] for oa in near.of_oa)


def test_no_home_of_london_is_nearer_to_a_square_that_was_not_read_than_to_a_park(
    near: Proximity, large: Proximity, found: Spine
):
    """The two squares cover London: every output area has a distance that is known."""
    assert set(near.of_oa) == set(large.of_oa) == set(found.area_of)


def test_each_distance_is_named_as_core_names_it_so_a_release_carries_it(
    near: Proximity, large: Proximity
):
    for made in (near, large):
        assert says_what_core_says(made.metric)
        assert made.metric.label.startswith("Straight-line distance")


# The evidence


def test_a_few_figures_at_the_northern_edge_rest_on_the_files_of_both_squares(
    cover: Cover, near: Proximity, large: Proximity
):
    assert [on_both_squares(made) for made in (cover, near, large)] == [4, 5, 9]
    for made in (cover, near, large):
        assert all(TQ in row.inputs for row in made.rows)


def test_every_figure_rests_on_the_files_it_was_worked_out_from(
    cover: Cover, near: Proximity, large: Proximity
):
    assert all({BOUNDARIES, LOOKUP, HOMES} <= set(row.inputs) for row in cover.rows)
    for made in (near, large):
        assert all({CENTRES, LOOKUP, HOMES} <= set(row.inputs) for row in made.rows)
    assert Evidence.of("lon-2026-10-02-01", cover.files, green_cover.METHODS, cover.rows)
    assert Evidence.of("lon-2026-10-02-01", near.files, park_proximity.METHODS, near.rows)
    assert Evidence.of("lon-2026-10-02-01", large.files, park_proximity.METHODS, large.rows)


def test_the_store_is_as_it_was(real: Inputs, cover: Cover, before: dict[str, tuple[int, int]]):
    assert Path(STORE).resolve() not in real.work.resolve().parents
    # Other steps may add a file to the store while this runs. None that was there has changed.
    after = listing()
    assert {name: after.get(name) for name in before} == before
