"""How much a point for a postcode can move a distance, counted on the real directory.

Every other test of the measures that place by postcode runs on made-up files.
These read the real directory and the real centres of output areas, and are
skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

No file of GP practices or of pharmacies has been fetched, so no figure of
either measure is held here. What is held is what the module says of the
ground it measures on: how far apart London's postcodes stand, how far a
postcode stands from the centre of its output area, and what a trial with
made-up places found. Every number is a count or a distance over all of
London, counted on 2026-09-24. None is of a place, and no postcode is held.

Nothing is written to the store. A file is copied out of it to be read.
"""

import math
import os
import random
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from burro_pipeline.cells import centres, postcodes, spine
from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.postcodes import Lookup
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import nearest_by_postcode
from burro_pipeline.derive.methods import to_places
from burro_pipeline.derive.park_proximity import median_by_homes
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
# The trial puts a made-up place at every so-manyth point, and draws from this seed.
EVERY, SEED = 100, 20_260_924
SQUARE = 100


def has_a_receipt() -> bool:
    return RECEIPTS.is_dir() and any(
        receipt.source_id == postcodes.SOURCE for receipt in read_receipts(RECEIPTS)
    )


pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and has_a_receipt()),
    reason=f"the directory is not here: {FOLDER_VARIABLE} names no folder, or it has no receipt",
)


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    work = tmp_path_factory.mktemp("by-postcode")
    return Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), work)


@pytest.fixture(scope="module")
def lookup(real: Inputs) -> Lookup:
    return postcodes.build(real)


@pytest.fixture(scope="module")
def ground(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def at(real: Inputs, ground: Spine) -> dict[str, Point]:
    return centres.build(real, ground)


@pytest.fixture(scope="module")
def points(lookup: Lookup) -> list[Point]:
    """Every point a postcode in use stands on, once, in a fixed order."""
    return sorted(set(lookup.points_in_use()))


@pytest.fixture(scope="module")
def to_another(points: list[Point]) -> dict[Point, float]:
    """How far each point is from the nearest other point."""
    on: dict[tuple[int, int], list[Point]] = {}
    for point in points:
        on.setdefault((int(point[0] // SQUARE), int(point[1] // SQUARE)), []).append(point)
    found: dict[Point, float] = {}
    for point in points:
        across, up = int(point[0] // SQUARE), int(point[1] // SQUARE)
        best, ring = math.inf, 0
        while (ring - 1) * SQUARE < best:
            for east in range(across - ring, across + ring + 1):
                for north in range(up - ring, up + ring + 1):
                    if max(abs(east - across), abs(north - up)) != ring:
                        continue
                    for other in on.get((east, north), ()):
                        if other != point:
                            far = math.hypot(other[0] - point[0], other[1] - point[1])
                            best = min(best, far)
            ring += 1
        found[point] = best
    return found


def at_the(share: float, ordered: Sequence[float]) -> float:
    """The value that so large a share of some values, in order, are under."""
    return ordered[min(len(ordered) - 1, int(share * len(ordered)))]


def medians(places: Sequence[Point], at: Mapping[str, Point], ground: Spine) -> dict[str, float]:
    of_oa = nearest_by_postcode.to_the_nearest(places, at)
    worked = median_by_homes(of_oa, ground.weights)
    return {area: one.value for area, one in worked.items() if one.value is not None}


def test_many_postcodes_stand_on_a_point_that_another_shares(lookup: Lookup, points: list[Point]):
    every = lookup.points_in_use()
    assert (len(every), len(points)) == (180_965, 166_402)
    counted: dict[Point, int] = {}
    for point in every:
        counted[point] = counted.get(point, 0) + 1
    shared = sum(count for count in counted.values() if count > 1)
    assert shared == 18_797


def test_half_of_londons_postcodes_stand_within_40_metres_of_the_point_of_another(
    to_another: dict[Point, float],
):
    far = sorted(to_another.values())
    assert [round(at_the(share, far)) for share in (0.25, 0.5, 0.75, 0.9, 0.99)] == [
        29,
        40,
        55,
        74,
        129,
    ]


def test_a_postcode_stands_78_metres_from_the_centre_of_its_output_area_at_the_middle(
    lookup: Lookup, at: dict[str, Point]
):
    rows = lookup._rows.values()  # pyright: ignore[reportPrivateUsage]
    far = sorted(
        math.hypot(kept[0] - at[kept[2]][0], kept[1] - at[kept[2]][1])
        for kept in rows
        if kept[4] is None and kept[2] in at
    )
    assert len(far) == 180_964
    assert [round(at_the(share, far)) for share in (0.25, 0.5, 0.75, 0.9, 0.99)] == [
        45,
        78,
        125,
        196,
        533,
    ]


def test_the_rule_at_the_edge_of_london_leaves_out_few_homes_where_places_are_many(
    real: Inputs, points: list[Point], at: dict[str, Point], ground: Spine
):
    """A trial of the method on made-up places. It says nothing of any real place.

    A made-up place is put at every hundredth point, all of them in London. An
    output area is left out where a home outside London is taken to stand
    nearer than the nearest of them.
    """
    places = points[::EVERY]
    placed = real.open(centres.CENTRES, Use.SCORING, edition=centres.CENTRES_EDITION)
    to_a_place = nearest_by_postcode.to_the_nearest(places, at)
    within = nearest_by_postcode.box_round(at, max(to_a_place.values()))
    beyond = nearest_by_postcode.outside_london(placed, ground, within)
    of_oa, near_the_edge = nearest_by_postcode.known(
        to_a_place, nearest_by_postcode.to_the_nearest(beyond, at)
    )
    assert (len(at), len(near_the_edge)) == (26_369, 230)
    assert sum(ground.homes[oa] for oa in near_the_edge) == 29_588
    worked = nearest_by_postcode.figures(of_oa, ground)
    states: dict[str, int] = {}
    for one in worked.values():
        states[one.state.value] = states.get(one.state.value, 0) + 1
    assert states == {"present": 955, "partial": 42, "below_threshold": 5}
    given = sorted(one.value for one in worked.values() if one.value is not None)
    # Given to the nearest 100 metres, 997 figures stand on 15 steps.
    assert (given[0], given[len(given) // 2], given[-1]) == (100.0, 400.0, 1_600.0)
    assert len(set(given)) == 15


def test_a_place_at_another_door_of_its_postcode_moves_three_figures_in_four_given_to_10_metres(
    points: list[Point], to_another: dict[Point, float], at: dict[str, Point], ground: Spine
):
    """A trial of the method on made-up places. It says nothing of any real place.

    A made-up place is put at every hundredth point. Each is then moved to a
    spot drawn evenly from the disc round its point that reaches to the
    nearest other point: the ground that is its postcode's own.
    """
    places = points[::EVERY]
    assert len(places) == 1_665
    before = medians(places, at, ground)
    assert len(before) == 1_002
    drawn = random.Random(SEED)  # noqa: S311
    moved: list[Point] = []
    for place in places:
        reach = to_another[place] * math.sqrt(drawn.random())
        turn = drawn.random() * 2 * math.pi
        moved.append((place[0] + reach * math.cos(turn), place[1] + reach * math.sin(turn)))
    after = medians(moved, at, ground)
    by = sorted(abs(after[area] - before[area]) for area in before)
    assert 10 <= at_the(0.5, by) <= 12
    assert 29 <= at_the(0.9, by) <= 31
    differ = {
        places_given: sum(
            1
            for area in before
            if to_places(before[area], places_given) != to_places(after[area], places_given)
        )
        for places_given in (0, -1, -2)
    }
    # Given to the metre nearly every figure changes, to 10 metres three in four, and to
    # 100 metres about one in seven.
    assert differ == {0: 978, -1: 767, -2: 151}
    assert nearest_by_postcode.DECIMALS == -2
