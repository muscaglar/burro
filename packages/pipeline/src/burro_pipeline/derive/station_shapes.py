"""The geometry the nearest station adds: the nearest of many points, and the nearest land.

It is kept in a module of its own while the measures are built side by side,
to be folded into `cells/shapes.py` when they are joined. Like that module it
names the library of geometry, so that the measure handles plain numbers.

Every distance is a straight line on the National Grid, in metres. A point
that stands inside an outline is at no distance from it.
"""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportMissingTypeStubs=false

import math
from collections.abc import Sequence

import shapely

from burro_pipeline.cells.shapes import Shape

Point = tuple[float, float]


def _nearest(tree: shapely.STRtree, points: Sequence[Point]) -> list[float]:
    """For each point, how far the nearest thing of the tree is, in the order of the points."""
    asked = shapely.points([list(point) for point in points])
    pairs, far = tree.query_nearest(asked, return_distance=True, all_matches=False)
    found = dict(zip(pairs[0].tolist(), far.tolist(), strict=True))
    return [float(found[at]) for at in range(len(points))]


def to_the_nearest_point(points: Sequence[Point], among: Sequence[Point]) -> list[float]:
    """For each point, the distance to the nearest of the others. With none, it is endless."""
    if not among or not points:
        return [math.inf for _ in points]
    return _nearest(shapely.STRtree(shapely.points([list(point) for point in among])), points)


def to_the_nearest_land(points: Sequence[Point], outlines: Sequence[Shape]) -> list[float]:
    """For each point, the distance to the nearest of the outlines. With none, it is endless."""
    if not outlines or not points:
        return [math.inf for _ in points]
    return _nearest(shapely.STRtree(list(outlines)), points)


def nearest_within(
    points: Sequence[Point], among: Sequence[Point], metres: float
) -> list[int | None]:
    """For each point, which of the others is nearest and no further off than so many metres.

    It is given as the place of the other in `among`, or as none where none
    stands that near. Of two that are as near as each other, the first counts.
    """
    if not among or not points:
        return [None for _ in points]
    tree = shapely.STRtree(shapely.points([list(point) for point in among]))
    asked = shapely.points([list(point) for point in points])
    pairs = tree.query_nearest(asked, max_distance=metres, all_matches=True)
    found: list[int | None] = [None] * len(points)
    for at, other in zip(pairs[0].tolist(), pairs[1].tolist(), strict=True):
        held = found[at]
        found[at] = other if held is None else min(held, other)
    return found


def which_within(points: Sequence[Point], among: Sequence[Point], metres: float) -> list[list[int]]:
    """For each point, which of the others stand no further off than so many metres.

    Each is given by its place in `among`, in order. One that stands at
    exactly the distance is within it.
    """
    found: list[list[int]] = [[] for _ in points]
    if not among or not points:
        return found
    tree = shapely.STRtree(shapely.points([list(point) for point in among]))
    asked = shapely.points([list(point) for point in points])
    pairs = tree.query(asked, predicate="dwithin", distance=metres)
    for at, other in zip(pairs[0].tolist(), pairs[1].tolist(), strict=True):
        found[at].append(other)
    return [sorted(one) for one in found]


def how_many_within(points: Sequence[Point], among: Sequence[Point], metres: float) -> list[int]:
    """For each point, how many of the others stand no further off than so many metres.

    One that stands at exactly the distance is within it. Two of the others on
    one spot are two.
    """
    if not among or not points:
        return [0 for _ in points]
    tree = shapely.STRtree(shapely.points([list(point) for point in among]))
    asked = shapely.points([list(point) for point in points])
    pairs = tree.query(asked, predicate="dwithin", distance=metres)
    found = [0] * len(points)
    for at in pairs[0].tolist():
        found[at] += 1
    return found


def within(outlines: Sequence[Shape], points: Sequence[Point], metres: float) -> list[Shape]:
    """The outlines that reach into the box the points stand in, widened by so many metres."""
    if not points:
        return []
    across = [point[0] for point in points]
    up = [point[1] for point in points]
    box = shapely.box(
        min(across) - metres, min(up) - metres, max(across) + metres, max(up) + metres
    )
    return [outline for outline in outlines if bool(shapely.intersects(outline, box))]
