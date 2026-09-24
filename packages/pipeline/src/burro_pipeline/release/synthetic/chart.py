"""The map of the made-up city: a grid of cells with nudged corners, and a river.

Everything here is in kilometres east and north of the middle of the centre.
Only `lon_lat` turns a point into degrees, and it puts the city around
longitude 0, latitude 0, which is open sea: no synthetic polygon can be laid
over a real street.
"""

import math
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise

from burro_pipeline.release.synthetic.names import (
    AREAS,
    CENTRE,
    COLUMN_WIDTHS_KM,
    ROW_HEIGHTS_KM,
    SOUTH_BANK,
)

KM_PER_DEGREE = 111.32
RIVER_HALF_WIDTH_KM = 0.07
NEAR_WATER_KM = 0.3
# How far a corner, and the middle of an edge, may be nudged from the grid.
# Edges bend a little because the two move apart.
CORNER_NUDGE_KM = 0.28
EDGE_NUDGE_KM = 0.16
# The spacing of the points an area is measured on.
SAMPLE_KM = 0.12

Xy = tuple[float, float]
Cell = tuple[int, int]  # row from the south, column from the west
# A point of the grid is a corner or the middle of an edge, so it is counted in
# half cells: (2, 5) is on the first grid line above the southern edge, half
# way along the third cell.
Half = tuple[int, int]


class Draw:
    """The one random source.

    Only `random()` is ever called. Its sequence for a seed is the same on
    every Python version, which the other methods of `Random` do not promise.
    """

    def __init__(self, seed: int) -> None:
        self._next = random.Random(seed).random  # noqa: S311

    def between(self, low: float, high: float) -> float:
        return low + (high - low) * self._next()

    def around(self, spread: float) -> float:
        """Noise within `spread` either way, more often small than large."""
        return (self._next() + self._next() - 1) * spread


def distance(a: Xy, b: Xy) -> float:
    dx, dy = a[0] - b[0], a[1] - b[1]
    return math.sqrt(dx * dx + dy * dy)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(max(value, low), high)


def lon_lat(point: Xy) -> tuple[float, float]:
    return (round(point[0] / KM_PER_DEGREE, 6), round(point[1] / KM_PER_DEGREE, 6))


def centroid(ring: Sequence[Xy]) -> Xy:
    area = cx = cy = 0.0
    for (x0, y0), (x1, y1) in pairwise([*ring, ring[0]]):
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    return (cx / (3 * area), cy / (3 * area))


def _contains(ring: Sequence[Xy], point: Xy) -> bool:
    x, y = point
    inside = False
    for (x0, y0), (x1, y1) in pairwise([*ring, ring[0]]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def _to_segment(point: Xy, a: Xy, b: Xy) -> float:
    ax, ay = b[0] - a[0], b[1] - a[1]
    along = clamp(((point[0] - a[0]) * ax + (point[1] - a[1]) * ay) / (ax * ax + ay * ay))
    return distance(point, (a[0] + along * ax, a[1] + along * ay))


def share_near_water(ring: Sequence[Xy], river: Sequence[Xy]) -> float:
    """The per cent of an area within 300 m of the river's bank, measured on a grid of points."""
    reach = RIVER_HALF_WIDTH_KM + NEAR_WATER_KM
    west, east = min(p[0] for p in ring), max(p[0] for p in ring)
    south, north = min(p[1] for p in ring), max(p[1] for p in ring)
    banks = [
        (a, b)
        for a, b in pairwise(river)
        # A stretch of river further than this from the area's box cannot be near any of it.
        if min(a[0], b[0]) - reach <= east
        and max(a[0], b[0]) + reach >= west
        and min(a[1], b[1]) - reach <= north
        and max(a[1], b[1]) + reach >= south
    ]
    inside = near = 0
    for i in range(int((east - west) / SAMPLE_KM) + 1):
        for j in range(int((north - south) / SAMPLE_KM) + 1):
            point = (west + (i + 0.5) * SAMPLE_KM, south + (j + 0.5) * SAMPLE_KM)
            if _contains(ring, point):
                inside += 1
                near += any(_to_segment(point, a, b) <= reach for a, b in banks)
    return 100 * near / inside


def _cells_at(point: Half) -> list[tuple[Cell, Xy]]:
    """The cells that touch a grid point, each with the direction it lies in."""
    row, col = point
    rows = [(row // 2 - 1, -1.0), (row // 2, 1.0)] if row % 2 == 0 else [(row // 2, 0.0)]
    cols = [(col // 2 - 1, -1.0), (col // 2, 1.0)] if col % 2 == 0 else [(col // 2, 0.0)]
    return [
        ((r, c), (dx, dy))
        for r, dy in rows
        for c, dx in cols
        if 0 <= r < len(ROW_HEIGHTS_KM) and 0 <= c < len(COLUMN_WIDTHS_KM)
    ]


def _towards(ways: Sequence[Xy], axis: int) -> float:
    return sum(way[axis] for way in ways) / len(ways)


def _sign(value: float) -> float:
    return float((value > 0) - (value < 0))


def _away_from_south_bank(point: Half) -> Xy | None:
    """Which way the far bank lies from a grid point, if the river runs through it."""
    touching = _cells_at(point)
    south = [way for cell, way in touching if cell in SOUTH_BANK]
    other = [way for cell, way in touching if cell not in SOUTH_BANK]
    if not south or not other:
        return None
    return (
        _sign(_towards(other, 0) - _towards(south, 0)),
        _sign(_towards(other, 1) - _towards(south, 1)),
    )


@dataclass(frozen=True)
class Chart:
    """Where every grid point is, and so where every area is."""

    points: Mapping[Half, Xy]

    def _seen_from(self, cell: Cell, point: Half) -> Xy:
        """A grid point as one cell sees it. On the river, each bank stands back from the water."""
        x, y = self.points[point]
        away = _away_from_south_bank(point)
        if away is None:
            return (x, y)
        back = -RIVER_HALF_WIDTH_KM if cell in SOUTH_BANK else RIVER_HALF_WIDTH_KM
        return (x + back * away[0], y + back * away[1])

    def ring(self, cell: Cell) -> tuple[Xy, ...]:
        """The boundary of a cell, anticlockwise from its south-west corner. Not closed."""
        r, c = 2 * cell[0], 2 * cell[1]
        south = [(r, c), (r, c + 1), (r, c + 2)]
        north = [(r + 2, c + 2), (r + 2, c + 1), (r + 2, c)]
        around = [*south, (r + 1, c + 2), *north, (r + 1, c)]
        return tuple(self._seen_from(cell, point) for point in around)

    def inside(self, cell: Cell, east: float, north: float) -> Xy:
        """A point inside a cell: `east` of the way across it and `north` of the way up."""
        sw, _, se, _, ne, _, nw, _ = self.ring(cell)
        low = (sw[0] + east * (se[0] - sw[0]), sw[1] + east * (se[1] - sw[1]))
        high = (nw[0] + east * (ne[0] - nw[0]), nw[1] + east * (ne[1] - nw[1]))
        return (low[0] + north * (high[0] - low[0]), low[1] + north * (high[1] - low[1]))

    def river(self) -> tuple[Xy, ...]:
        """The middle of the river, from where it enters in the west to where it leaves."""
        on_river = [p for p in self.points if _away_from_south_bank(p) is not None]
        # West to east along the grid line, then south down the bend.
        return tuple(self.points[p] for p in sorted(on_river, key=lambda p: (p[1], -p[0])))


def _grid_lines(widths: Sequence[float], centre: int) -> list[float]:
    """Where the grid lines fall, measured from the middle of the centre's cell."""
    lines = [0.0]
    for width in widths:
        lines.append(lines[-1] + width)
    middle = (lines[centre] + lines[centre + 1]) / 2
    return [line - middle for line in lines]


def _along(lines: Sequence[float], half: int) -> float:
    on_line = lines[half // 2]
    return on_line if half % 2 == 0 else (on_line + lines[half // 2 + 1]) / 2


def draw_chart(draw: Draw) -> Chart:
    centre = next(area for area in AREAS if area.name == CENTRE)
    xs = _grid_lines(COLUMN_WIDTHS_KM, centre.col)
    ys = _grid_lines(ROW_HEIGHTS_KM, centre.row)
    points: dict[Half, Xy] = {}
    for row in range(2 * len(ROW_HEIGHTS_KM) + 1):
        for col in range(2 * len(COLUMN_WIDTHS_KM) + 1):
            if row % 2 and col % 2:
                continue  # the middle of a cell is not on its boundary
            nudge = EDGE_NUDGE_KM if row % 2 or col % 2 else CORNER_NUDGE_KM
            points[row, col] = (
                _along(xs, col) + draw.around(nudge),
                _along(ys, row) + draw.around(nudge),
            )
    return Chart(points)
