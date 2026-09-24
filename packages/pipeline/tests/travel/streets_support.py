"""The streets of the small town of `support.py`, and points on them. Every name is made up.

The one street runs east from Pellam Cross to Wexmoor, and a lane runs south
to Kindlewharf. A point of the streets stands every 100 metres.
"""

from itertools import pairwise

from burro_pipeline.travel.engine import Point
from burro_pipeline.travel.plain import METRES_PER_DEGREE, Streets

from . import support
from .support import at

STEP = 100
assert METRES_PER_DEGREE == support.METRES_PER_DEGREE


def point(point_id: str, east: float, north: float = 0) -> Point:
    return Point(point_id, at(east, north))


def streets() -> Streets:
    """The one street and the lane south to Kindlewharf, a point every 100 metres."""
    along = {f"syn-k-e{east:05d}": at(east) for east in range(0, 5001, STEP)}
    down = {f"syn-k-s{south:05d}": at(0, -south) for south in range(STEP, 1001, STEP)}
    east = sorted(along)
    south = ["syn-k-e00000", *sorted(down)]
    links = [(a, b, STEP) for run in (east, south) for a, b in pairwise(run)]
    return Streets(nodes=along | down, links=tuple(links))
