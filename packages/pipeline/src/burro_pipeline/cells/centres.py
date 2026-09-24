"""Where the homes of each output area are taken to stand.

The statistics office gives one point for each output area: its centre of
population at the census of 2021, on the National Grid, in metres. A value on a
grid is read at that point, and a walk is started there. The point is never a
measure in its own right.

An output area the file gives no point for is left out, and nothing stands in
for it: not the middle of its outline, and not the point of a neighbour. The
method that reads a value at a point then counts it as not covered.
"""

import math

from burro_pipeline.cells.spine import OA, Spine
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

CENTRES = "ons-oa-pwc-2021"
# The registry asks that the version is pinned.
CENTRES_EDITION = "V4"
EASTING, NORTHING = "X", "Y"

Point = tuple[float, float]


def centres_of(opened: Opened, spine: Spine) -> dict[str, Point]:
    """The centre of each output area of the spine that the file gives one for."""
    wanted = spine.area_of
    found: dict[str, Point] = {}
    with opened.text() as text:
        for row in opened.rows(text, (OA, EASTING, NORTHING)):
            if row[OA] not in wanted:
                continue
            try:
                point = float(row[EASTING]), float(row[NORTHING])
            except ValueError:
                point = math.nan, math.nan
            if row[OA] in found or not all(math.isfinite(part) for part in point):
                raise LockError("input_is_as_described", opened.file_id, "a point is no point")
            found[row[OA]] = point
    return found


def build(inputs: Inputs, spine: Spine) -> dict[str, Point]:
    """The centres, from the files of the build."""
    return centres_of(inputs.open(CENTRES, Use.SCORING, edition=CENTRES_EDITION), spine)
