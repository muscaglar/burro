"""How much of an outline lies on each output area, and how far a point is from an area.

The geometry the naming of the areas needs, and no more. It is here while the
parts of the areas are built side by side, and belongs in `cells/shapes.py`
once they are joined, as `names_shapes.py` says of itself. Like that module,
this one tells the type checker not to ask what the geometry library returns.

Every coordinate is on the National Grid, in metres, so a share is a share of
ground and nothing is projected.
"""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportUnknownParameterType=false
# pyright: reportMissingTypeStubs=false, reportAttributeAccessIssue=false

from collections.abc import Mapping

import shapely

from burro_pipeline.areas.names_shapes import Ground
from burro_pipeline.cells.shapes import Point, Shape

# A share is written to so many decimal places, so that the same outline gives the same
# share on every machine.
DECIMALS = 6


def shares_on(shape: Shape, ground: Ground) -> dict[str, float]:
    """The share of an outline that lies on each output area it lies on.

    An output area the outline only touches holds none of it, and is left out.
    The shares add up to less than one where part of the outline lies on no
    output area: over the water, or beyond London.
    """
    whole = float(shape.area)
    if whole <= 0:
        return {}
    found: dict[str, float] = {}
    for _, code in ground.near(shape, 0.0):
        held = float(shapely.intersection(ground.shape(code), shape).area)
        share = round(held / whole, DECIMALS)
        if share > 0:
            found[code] = share
    return dict(sorted(found.items()))


def near_each_other(outlines: Mapping[str, Shape], metres: float) -> dict[str, tuple[str, ...]]:
    """For each outline, the others that lie within so many metres of it, in the order of ids.

    Two areas on the two banks of a river share no side, and still stand side by side in
    a picture. This is what tells a picture to give them two colours.
    """
    codes = sorted(outlines)
    held = [outlines[code] for code in codes]
    tree = shapely.STRtree(held)
    found: dict[str, set[str]] = {code: set() for code in codes}
    near, of = tree.query(held, predicate="dwithin", distance=metres).tolist()
    for one, other in zip(near, of, strict=True):
        if one != other:
            found[codes[int(one)]].add(codes[int(other)])
    return {code: tuple(sorted(found[code])) for code in codes}


def nearest_to(
    outline: Shape, points: Mapping[str, Point], count: int
) -> tuple[tuple[float, str], ...]:
    """The points nearest an outline, each with how far off it is in metres, the nearest first."""
    found = sorted(
        (round(float(shapely.distance(outline, shapely.Point(at))), 1), name)
        for name, at in points.items()
    )
    return tuple(found[:count])
