"""The geometry the measures of town centres add, and nothing else.

`cells/shapes.py` measures an outline, and `areas/names_shapes.py` finds the
outline nearest a point. The measures of town centres need two things more:
how much of the circle round it an outline fills, and how far a point is from
the nearest of many points. They are here while the measures are built side by
side, and belong in `cells/shapes.py` once the parts are joined. Like that
module, this one tells the type checker not to ask what the geometry library
returns.

Every coordinate is on the National Grid, in metres, so a distance is a
distance on the ground and nothing is projected.
"""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportUnknownParameterType=false
# pyright: reportMissingTypeStubs=false, reportAttributeAccessIssue=false

import math
from collections.abc import Sequence

import shapely

from burro_pipeline.cells.shapes import Point, Shape


def fills_its_circle(shape: Shape) -> float:
    """What an outline encloses, as a share of the smallest circle that holds all of it.

    A circle fills its own, and reads 1. A square reads 0.64, and a strip ten
    times as long as it is wide reads 0.13. An outline in several pieces is
    held by one circle round them all, so pieces that stand apart read low. A
    hole in an outline is no part of what it encloses.
    """
    radius = float(shapely.minimum_bounding_radius(shape))
    if not radius > 0:
        raise ValueError("an outline that no circle can be drawn round")
    return min(1.0, float(shape.area) / (math.pi * radius * radius))


class Points:
    """Some points, asked how far the nearest of them is from another point."""

    def __init__(self, points: Sequence[Point]) -> None:
        self._points = [shapely.Point(point) for point in sorted(set(points))]
        self._tree = shapely.STRtree(self._points)

    def __len__(self) -> int:
        return len(self._points)

    def nearest(self, point: Point) -> float | None:
        """How far a point is from the nearest of the points, in metres. None if there is none."""
        if not self._points:
            return None
        here = shapely.Point(point)
        return float(shapely.distance(self._points[int(self._tree.nearest(here))], here))
