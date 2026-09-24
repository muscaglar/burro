"""The nearest play space and what a park offers, worked out from the publishers' files.

Every other test of the two measures runs on made-up sites. These read the
real files, and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts and, for each measure, London's lowest, middle and highest
figure, so that a publisher's file that changes is noticed. None is said of a
named area. Each was worked out on 2026-09-24, by a program. No person has
held any of them against a map.

The counts of sites are of the two squares of the National Grid that London
lies on, which take in land far outside London.

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
from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import park_facilities, play_space_proximity
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.park_facilities import Counted, Facilities
from burro_pipeline.derive.park_proximity import Proximity
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs

from .real_files import SKIPPED, STORE, real_inputs

pytestmark = SKIPPED
# The two squares London lies on, by the ids of their receipts, and the edition of both.
TQ, TL, EDITION = "f-02f39a296d6f", "f-f9c10aca1661", "2026-04"
# The centres, the lookup and the table of homes.
CENTRES, LOOKUP, HOMES = "f-00e1d0532798", "f-49321b95f212", "f-af7b512615ea"
GREEN, SPORT, PLAY, FIELD, COURT = park_facilities.KINDS
PLOT, YARD, GOLF, GROUNDS = park_facilities.NEVER


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
def play(real: Inputs, found: Spine) -> Proximity:
    return play_space_proximity.build(real, found, edition=EDITION)


@pytest.fixture(scope="module")
def offer(real: Inputs, found: Spine) -> Facilities:
    return park_facilities.build(real, found, edition=EDITION)


def three_of(worked: Mapping[str, Worked]) -> tuple[float, float, float]:
    """London's lowest, middle and highest figure."""
    values = sorted(one.value for one in worked.values() if one.value is not None)
    return values[0], statistics.median(values), values[-1]


# The nearest play space


def test_every_area_has_a_distance_to_a_play_space_and_is_wholly_covered(play: Proximity):
    assert (play.parks.parks, play.parks.without_a_way_in) == (9_459, 653)
    assert (len(play.parks.ways_in), len(play.of_oa)) == (12_634, 26_369)
    assert Counter(one.state for one in play.worked.values()) == {State.PRESENT: 1_002}
    assert {one.weight_covered for one in play.worked.values()} == {1.0}
    assert three_of(play.worked) == (60.0, 300.0, 1_110.0)


def test_no_home_of_london_is_nearer_to_a_square_that_was_not_read_than_to_a_play_space(
    play: Proximity, found: Spine
):
    """The two squares cover London: every output area has a distance that is known."""
    assert set(play.of_oa) == set(found.area_of)
    assert max(play.of_oa.values()) < 2_050


# What a park offers


def test_the_parks_and_what_they_offer_are_as_many_as_were_counted(offer: Facilities):
    assert (offer.offers.parks.parks, offer.offers.parks.without_a_way_in) == (4_647, 51)
    assert len(offer.offers.ways_in) == 22_866
    assert Counter(len(kinds) for kinds in offer.offers.of_park.values()) == {
        1: 1_513,
        2: 376,
        3: 125,
        4: 59,
        5: 10,
    }


def test_most_sites_of_every_kind_lie_inside_no_park_and_are_not_counted(offer: Facilities):
    """What is left out, of the two squares: a site in no park is no part of what a park offers."""
    assert offer.offers.counted == {
        GREEN: Counted(sites=889, inside_a_park=138),
        SPORT: Counted(sites=3_554, inside_a_park=625),
        PLAY: Counted(sites=9_459, inside_a_park=2_414),
        FIELD: Counted(sites=3_667, inside_a_park=130),
        COURT: Counted(sites=2_267, inside_a_park=470),
    }


def test_a_few_sites_that_never_count_lie_inside_a_park_and_are_left_out(offer: Facilities):
    assert offer.offers.never == {
        PLOT: Counted(sites=2_615, inside_a_park=10),
        YARD: Counted(sites=921, inside_a_park=4),
        GOLF: Counted(sites=515, inside_a_park=13),
        GROUNDS: Counted(sites=3_427, inside_a_park=7),
    }


def test_every_area_has_a_count_of_kinds_and_is_wholly_covered(offer: Facilities):
    assert Counter(one.state for one in offer.worked.values()) == {State.PRESENT: 1_002}
    assert {one.weight_covered for one in offer.worked.values()} == {1.0}
    assert three_of(offer.worked) == (0.0, 3.2, 5.0)


def test_the_reach_of_no_home_of_london_takes_in_land_that_was_not_read(
    offer: Facilities, found: Spine
):
    """The two squares cover London and 1,200 metres round it: every output area has a count."""
    assert set(offer.within.kinds) == set(offer.within.parks) == set(found.area_of)
    assert Counter(len(kinds) for kinds in offer.within.kinds.values()) == {
        0: 1_195,
        1: 2_278,
        2: 4_126,
        3: 6_875,
        4: 8_847,
        5: 3_048,
    }
    assert sum(not parks for parks in offer.within.parks.values()) == 133


def test_the_figure_of_an_area_is_the_sum_of_its_five_shares(offer: Facilities):
    for area, one in offer.worked.items():
        shares = [offer.shares[kind][area].value for kind in park_facilities.KINDS]
        assert all(share is not None and 0.0 <= share <= 1.0 for share in shares)
        assert one.value is not None and 0.0 <= one.value <= len(park_facilities.KINDS)
        assert math.isclose(one.value, math.fsum(share or 0.0 for share in shares), abs_tol=0.05)


# The names and the evidence


def test_the_play_space_is_named_as_core_names_it_and_what_a_park_offers_is_not(
    play: Proximity, offer: Facilities
):
    """So a release carries the nearest play space, and none carries what a park offers."""
    assert says_what_core_says(play.metric)
    assert not says_what_core_says(offer.metric)
    for made in (play, offer):
        assert "straight line" in made.metric.label.lower().replace("-", " ")
        assert made.metric.vintage == EDITION


def test_a_few_figures_at_the_northern_edge_rest_on_the_files_of_both_squares(
    play: Proximity, offer: Facilities
):
    on_both = [sum({TQ, TL} <= set(row.inputs) for row in made.rows) for made in (play, offer)]
    assert on_both == [3, 4]
    for made in (play, offer):
        assert all(TQ in row.inputs for row in made.rows)


def test_every_figure_rests_on_the_files_it_was_worked_out_from(play: Proximity, offer: Facilities):
    for made in (play, offer):
        assert all({CENTRES, LOOKUP, HOMES} <= set(row.inputs) for row in made.rows)
    assert Evidence.of("lon-2026-10-02-01", play.files, play_space_proximity.METHODS, play.rows)
    assert Evidence.of("lon-2026-10-02-01", offer.files, park_facilities.METHODS, offer.rows)


def test_the_store_is_as_it_was(real: Inputs, play: Proximity, before: dict[str, tuple[int, int]]):
    assert Path(STORE).resolve() not in real.work.resolve().parents
    # Other steps may add a file to the store while this runs. None that was there has changed.
    after = listing()
    assert {name: after.get(name) for name in before} == before
