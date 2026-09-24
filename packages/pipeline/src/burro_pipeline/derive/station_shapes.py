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
