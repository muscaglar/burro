"""Which sites lie inside which: the geometry that what a park offers needs.

`cells/shapes.py` joins outlines and measures the land of one inside others.
What a park offers needs one thing more: for each site, the sites of another
kind that hold at least a given share of its land. It is here while the
measures are built side by side, and belongs in `cells/shapes.py` once they
are joined. Like that module, this one tells the type checker not to ask what
the geometry library returns.

Every coordinate is on the National Grid, in metres, so land is land on the
ground and nothing is projected.
"""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportUnknownParameterType=false
# pyright: reportMissingTypeStubs=false, reportAttributeAccessIssue=false

from collections.abc import Mapping

import shapely

from burro_pipeline.cells.shapes import Shape


def held_by(
    outlines: Mapping[str, Shape], holders: Mapping[str, Shape], least_share: float
) -> dict[str, tuple[str, ...]]:
    """For each outline, the holders that hold at least so much of its land, by their ids.

    The share is of the outline's own land, and is taken against each holder
    alone: land that lies inside two holders counts for both, and the land of
    two holders is never added up. An outline that encloses no land lies
    inside nothing. An outline that no holder holds enough of is given an
    empty list, so every outline has an answer.
    """
    if not 0 < least_share <= 1:
        raise ValueError("a share is more than none and no more than the whole")
    names = sorted(holders)
    tree = shapely.STRtree([holders[name] for name in names])
    found: dict[str, tuple[str, ...]] = {}
    for one in sorted(outlines):
        shape = outlines[one]
        whole = float(shape.area)
        near = sorted(int(at) for at in tree.query(shape, predicate="intersects"))
        found[one] = tuple(
            names[at]
            for at in near
            if whole > 0
            and float(shapely.intersection(shape, holders[names[at]]).area) >= least_share * whole
        )
    return found
