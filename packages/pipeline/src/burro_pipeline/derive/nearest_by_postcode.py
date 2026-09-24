"""The nearest place of a kind, where a file gives each place by its postcode alone.

Some files say where a place is by a postcode and nothing else: a surgery, a
pharmacy. `cells/postcodes.py` gives a postcode a point. This module puts each
place at that point, and measures how far the nearest is from where homes are.
A measure's own module reads its publisher's file and says which places count.

**It is a straight line, and not a walk.** No network of streets is built. The
figure is the distance across whatever lies between, and the name of every
measure made here says so.

**A point for a postcode is not a door.** The directory's guide says the point
is the mean of all the addresses of the postcode, moved to the address nearest
that mean. So a place is put at a door of its postcode, which may not be its
own. In the directory of August 2026 half of London's postcodes in use stand
within 40 metres of the point of another, and 9 in 10 within 74. So a door is
mostly within a few tens of metres of where its place is put.

Where homes are taken to stand moves a distance more. A postcode in use stands
78 metres from the centre of its own output area at the middle, and 196 metres
at 9 in 10. So of one home, a distance of a few hundred metres is good to
about a hundred metres either way.

**A figure is given to the nearest 100 metres.** An area's figure is the
median over its homes, which is steadier than the distance of one home, and
still not known to 10 metres. A trial on the points of the directory of August
2026 put a made-up place at every hundredth postcode in use, and then moved
each to another spot on the ground of its own postcode. An area's figure moved
by 11 metres at the middle, and by under 30 metres for 9 areas in 10. Given to
the nearest 10 metres, three figures in four changed. Given to the nearest
100, one in seven did. `docs/research/data/postcodes.md` has the trial. The
distance to a park is given to the nearest 10 metres, and the same trial says
of it that its last digit is not known either: that is for whoever owns that
measure to weigh.

How a figure is made:

1. Each place that counts is looked up by its postcode. One whose postcode is
   no row of London, or has not the shape of a postcode, is placed nowhere.
   One whose point is the middle of a postcode sector, or was kept from before
   November 2000, is placed nowhere either: such a point may be hundreds of
   metres from every address of its postcode. Each is counted.
2. A place at a postcode that has ended is placed where the postcode last
   stood. The file says the place is open, and the directory says where its
   postcode was. How many were placed so is counted.
3. For each output area, the distance from its centre to the nearest place.
4. An area's figure is the median of those distances over its homes.

Nothing is filled in. The lookup holds London's postcodes alone, as the
licence registry asks, so a place outside London is placed nowhere. Near the
edge of London the nearest place may be one of those. So an output area has a
distance only where no home outside London is taken to stand nearer than the
nearest place that was found. Where one does, the distance is not known, it
adds nothing, and the coverage of its area falls by its homes. Below half the
homes covered no figure is given.

**The rule asks where homes are, and not where land is.** Where no home
outside London is nearer than the place that was found, land outside London
still may be, and a place on it is missed.
"""

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace

from burro_core.facts import fact_id
from burro_core.ids import FactKind

from burro_pipeline.cells import centres, postcodes
from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.postcodes import Lookup
from burro_pipeline.cells.spine import OA, Spine
from burro_pipeline.derive.methods import Worked, cell_of, row_of, to_places
from burro_pipeline.derive.park_proximity import median_by_homes
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

# A figure is given to the nearest so many metres, which is this many decimal places.
NEAREST, DECIMALS = 100, -2
# Points are kept by squares this wide while the nearest is looked for, in metres.
KEPT_BY = 500
# What the places are keyed by, in the file of every measure made here.
KEYED_BY = Geography.POSTCODE
CENSUS = 2021

METHOD = Method(
    derivation_id="straight_line_to_nearest_by_postcode@1",
    sentence="The distance in a straight line from the point where the homes of each census "
    "output area are taken to stand to the nearest of the places that count, each put at the "
    "point the postcode directory gives for its postcode, as the median over the area's homes "
    "at the census, which is the mean of the two middle distances where the homes divide "
    "exactly in half between them, leaving out every output area where the homes of an output "
    "area outside London are taken to stand nearer than the nearest place that was found, "
    "because a place outside London may then be nearer and no place outside London is placed, "
    "and not given where under 50 in 100 of the area's homes are in an output area whose "
    "nearest place is known.",
    kind=Kind.MEASURED,
    parameters={"enough_in_100": 50},
    code="burro_pipeline.derive.nearest_by_postcode",
)
METHODS: tuple[Method, ...] = (METHOD,)

# What the product shows beside every figure made here.
A_STRAIGHT_LINE = (
    "This is a straight line from where the homes of each small census area are taken to "
    "stand, and not a walk, so a railway, a river or a main road in between makes the real "
    "walk longer."
)
NOT_A_DOOR = (
    "A place is put at the point of its postcode, which is a door of that postcode and may not "
    "be its own, and homes are put at the centre of their small census area, so of any one "
    "home the distance is good to about a hundred metres, and the figure of an area is given "
    "to the nearest 100 metres."
)
AT_THE_EDGE = (
    "A place outside London is not counted, so near the edge of London the homes that have "
    "homes outside London nearer than the nearest place found are left out of the figure, and "
    "where only land outside London is nearer a place on that land is missed."
)
NOT_PLACED = (
    "A place whose postcode is not one of London's in the postcode directory, or whose "
    "postcode has no point good enough to measure to, is counted nowhere, so the homes near it "
    "read further from a place than they are."
)
OF_EVERY_MEASURE = (A_STRAIGHT_LINE, NOT_A_DOOR, AT_THE_EDGE, NOT_PLACED)


@dataclass(frozen=True)
class Placing:
    """What became of the places that count, as counts. No count is of one place alone."""

    # The places the file lists that count, with a postcode or without.
    listed: int
    # Those that were put on the map.
    placed: int
    # Those of the placed whose postcode has ended.
    at_an_ended_postcode: int
    # Those that were put nowhere, and why.
    not_a_postcode: int
    not_of_london: int
    too_coarse: int

    @property
    def not_placed(self) -> int:
        return self.not_a_postcode + self.not_of_london + self.too_coarse


@dataclass(frozen=True)
class Distances:
    """The distance to the nearest place for every area, with what stands behind each figure."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    placing: Placing
    # The distance of each output area whose nearest place is known, in metres.
    of_oa: Mapping[str, float]
    # The output areas with a centre and no distance: a home outside London is nearer than
    # the nearest place that was found.
    near_the_edge: tuple[str, ...]


def place(typed: Iterable[str], lookup: Lookup) -> tuple[tuple[Point, ...], Placing]:
    """Where each place is, from its postcode as its file writes it, and what became of each.

    Nothing of a postcode is kept: what is given back is points and counts. Two
    places at one postcode are two places on one point, and the point is
    given once.
    """
    points: set[Point] = set()
    listed = placed = ended = no_shape = elsewhere = coarse = 0
    for one in typed:
        listed += 1
        found = lookup.place(one)
        if found is None:
            if postcodes.key_of(one) is None:
                no_shape += 1
            else:
                elsewhere += 1
        elif not found.good_for_a_distance:
            coarse += 1
        else:
            placed += 1
            ended += not found.in_use
            points.add(found.point)
    tally = Placing(
        listed=listed,
        placed=placed,
        at_an_ended_postcode=ended,
        not_a_postcode=no_shape,
        not_of_london=elsewhere,
        too_coarse=coarse,
    )
    return tuple(sorted(points)), tally


class Near:
    """Points, kept by the square each stands on, so that the nearest is found by looking near.

    The distance to a park keeps its ways in the same way, in a class of its
    own that no other module may use. The two are to be made one when the
    measures are joined.
    """

    def __init__(self, points: Iterable[Point]) -> None:
        self._on: dict[tuple[int, int], list[Point]] = {}
        for point in sorted(points):
            self._on.setdefault(cell_of(*point, KEPT_BY), []).append(point)
        across = [corner[0] for corner in self._on]
        up = [corner[1] for corner in self._on]
        self._box = (min(across), min(up), max(across), max(up)) if self._on else None

    def nearest(self, point: Point) -> float | None:
        """How far a point is from the nearest of the points, or none if there is no point."""
        if self._box is None:
            return None
        own = cell_of(*point, KEPT_BY)
        west, south, east, north = self._box
        furthest = max(
            abs(own[0] - west), abs(own[0] - east), abs(own[1] - south), abs(north - own[1])
        )
        best, ring = math.inf, 0
        # A point on a square so many squares away is at least one square fewer away.
        while (ring - 1) * KEPT_BY < best and ring * KEPT_BY <= furthest + KEPT_BY:
            for corner in _round(own, ring):
                for other in self._on.get(corner, ()):
                    best = min(best, math.hypot(other[0] - point[0], other[1] - point[1]))
            ring += 1
        return best


def _round(own: tuple[int, int], ring: int) -> list[tuple[int, int]]:
    """The squares that stand so many squares from a square, in a ring round it."""
    if ring == 0:
        return [own]
    reach = range(-ring, ring + 1)
    return [
        (own[0] + across * KEPT_BY, own[1] + up * KEPT_BY)
        for across in reach
        for up in reach
        if max(abs(across), abs(up)) == ring
    ]


def outside_london(placed: Opened, found: Spine, within: tuple[Point, Point]) -> list[Point]:
    """The centre of every output area outside London that stands in a box.

    The file of centres holds every output area of England and Wales. One that
    is not in the spine is outside London.
    """
    (west, south), (east, north) = within
    beyond: list[Point] = []
    with placed.text() as text:
        for row in placed.rows(text, (OA, centres.EASTING, centres.NORTHING)):
            if row[OA] in found.area_of:
                continue
            try:
                point = float(row[centres.EASTING]), float(row[centres.NORTHING])
            except ValueError:
                point = math.nan, math.nan
            if not all(math.isfinite(part) for part in point):
                raise LockError("input_is_as_described", placed.file_id, "a point is no point")
            if west <= point[0] <= east and south <= point[1] <= north:
                beyond.append(point)
    return sorted(beyond)


def to_the_nearest(points: Sequence[Point], at: Mapping[str, Point]) -> dict[str, float]:
    """The distance from each centre to the nearest of some points. None where there is no point."""
    near = Near(points)
    found: dict[str, float] = {}
    for oa in sorted(at):
        nearest = near.nearest(at[oa])
        if nearest is not None:
            found[oa] = nearest
    return found


def box_round(at: Mapping[str, Point], reach: float) -> tuple[Point, Point]:
    """The box round some centres, and so many metres beyond them on every side."""
    across = [point[0] for point in at.values()]
    up = [point[1] for point in at.values()]
    return (min(across) - reach, min(up) - reach), (max(across) + reach, max(up) + reach)


def known(
    to_a_place: Mapping[str, float], to_a_home_outside: Mapping[str, float]
) -> tuple[dict[str, float], tuple[str, ...]]:
    """The distances that are known, and the output areas whose distance is not.

    A distance is known where no home outside London is taken to stand nearer
    than the place that was found. A home outside London at exactly the
    distance of the place leaves it known: no place there could be nearer.
    """
    kept = {
        oa: distance
        for oa, distance in to_a_place.items()
        if to_a_home_outside.get(oa, math.inf) >= distance
    }
    return kept, tuple(sorted(set(to_a_place) - set(kept)))


def figures(of_oa: Mapping[str, float], found: Spine) -> dict[str, Worked]:
    """The figure of every area of the spine, to the nearest 100 metres, or why it has none."""
    worked = median_by_homes(of_oa, found.weights)
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def build(
    inputs: Inputs,
    found: Spine,
    listed: Opened,
    typed: Iterable[str],
    key: str,
    *,
    directory: str | None = None,
) -> Distances:
    """The distance to the nearest place for every area, and its evidence.

    `listed` is the measure's own file, which the measure has opened and read,
    and `typed` the postcode of each place of it that counts. `key` is what the
    rows of evidence call the measure. `directory` is the edition of the
    postcode directory, where a build holds more than one.

    The gate is asked about the directory and about the centres before either
    is read. A row of evidence names the measure's file, the directory, the
    centres, the lookup and the table of homes.
    """
    lookup = postcodes.build(inputs, use=Use.SCORING, edition=directory)
    placed = inputs.open(centres.CENTRES, Use.SCORING, edition=centres.CENTRES_EDITION)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not {*found.inputs, listed.file_id} <= set(handed):
        raise ValueError("the spine and the places are of files of this build")
    at = centres.centres_of(placed, found)
    points, placing = place(typed, lookup)
    to_a_place = to_the_nearest(points, at)
    furthest = max(to_a_place.values(), default=0.0)
    beyond = outside_london(placed, found, box_round(at, furthest)) if to_a_place else []
    of_oa, near_the_edge = known(to_a_place, to_the_nearest(beyond, at))
    worked = figures(of_oa, found)
    behind = sorted({listed.file_id, lookup.receipt.file_id, placed.file_id, *found.inputs})
    files = tuple(handed[file_id] for file_id in behind)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, key), worked[area], METHOD, files)
        for area in sorted(worked)
    )
    return Distances(worked, rows, files, KEYED_BY, placing, of_oa, near_the_edge)
