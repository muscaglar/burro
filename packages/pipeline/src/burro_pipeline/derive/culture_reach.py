"""What is within reach of where homes are: the distance, the weights and the edge of London.

A measure of venues says what is within reach of an area's homes, and not what
lies inside its outline: a high street on a border serves both sides. This
module holds how that is worked out, for any places that are points. Nothing
in it is of culture alone. It reads no file of places and holds no kind of
venue: it is handed points, each with a slot it adds to.

**There is one of this.** A count of venues is only comparable with another if
both are made the same way. A place may stand at the very end of the reach,
and a distance measured another way by a few centimetres puts it on the other
side. So every measure of venues asks here, and no second module of `derive/`
measures a distance on the ground or says where the edge of London is. A test
reads every module and holds the pipeline to that.

How a figure is made:

1. For each output area, what stands within so many metres of its centre, in a
   straight line. The centre is the point the statistics office gives as the
   centre of population of the output area: where its homes are taken to stand.
2. An area's figure is the mean of those counts over its homes: what is
   within reach of its typical home. A home is a household at the census.
3. A second figure asks a sharper question: what is within reach for each
   1,000 homes within the same reach. It is one sum over another, each taken
   over the area's homes, and never a mean of rates.
4. A share is made the same way: what is within reach of one kind over what
   is within reach of every kind, each added up over the area's homes.
5. How far the nearest place stands is measured the same way as what is
   within reach, as far as a distance that is given and no further.

**It is a straight line, and not a walk.** No network of streets is built. So
the name of a measure says a straight line.

Why 800 metres. A person who walks 80 metres in a minute walks 800 in ten. As
a straight line it reaches further than that walk does, by as much as the
streets wind. The distance is a choice and not a finding.

How a distance is measured. A place is given as a longitude and a latitude,
and a centre is on the National Grid. A centre is turned to longitude and
latitude by the pipeline's one fixed operation, which is good to 2 metres.
The distance is then measured on the ground at the latitude of the centre: so
many metres to a degree north, and so many to a degree east, on the earth as
WGS84 has it. Over 800 metres that is right to a few centimetres.

The edge of London. A build counts the homes of London and no other, and a
source may hold the places of London and no other. A home near the edge may be
within reach of a home or of a place outside London. So an output area has a
count only where no centre of an output area outside London lies within reach
of its own. Where one does, such an output area adds nothing, and the coverage
of its area falls by its homes. Below half the homes covered no figure is
given.

**The rule asks where homes are, and not where land is.** Where no home
outside London is within reach, land outside London still may be. Such an
output area is counted, and a place that stands on that land is missed by a
source that holds London alone. So no sentence here says that a source covers
the whole reach of an output area that is counted. A measure says of its own
source whether it holds what lies beyond the edge.
"""

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace

from burro_pipeline.cells import centres
from burro_pipeline.cells.shapes import longitude_and_latitude
from burro_pipeline.cells.spine import OA, Spine
from burro_pipeline.derive.methods import (
    Worked,
    lsoa_ratio_by_homes,
    lsoa_value_by_homes,
    to_places,
)
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

# How far a place may be from where homes are, in a straight line, in whole metres.
METRES = 800
# The second figure is for each so many homes within the same reach.
PER = 1_000
# A figure is given to this many decimal places.
DECIMALS = 1
CODE = "burro_pipeline.derive.culture_reach"

# The earth as WGS84 has it: its radius at the equator in metres, and how flat it is.
RADIUS, FLATTENING = 6_378_137.0, 1 / 298.257223563
ECCENTRICITY_SQUARED = FLATTENING * (2 - FLATTENING)
# Points are kept by squares this wide in degrees while what is near is looked for. Each is
# a little under 300 metres wide at London.
ACROSS, UP = 0.004, 0.0025

Point = tuple[float, float]
Square = tuple[int, int]
# A point with what it adds: its longitude, its latitude, a slot, and what it adds to it.
Weighed = tuple[float, float, int, int]


def at_the_edge(metres: int) -> str:
    """How a method ends: which output areas are left out, and what the rule does not see.

    It says what the rule is and no more. The rule asks where homes outside
    London are taken to stand, so it does not say that the source covers the
    whole reach of an output area that is counted.
    """
    return (
        "leaving out every output area where the homes of an output area outside London are "
        f"taken to stand within {metres} metres of its own, because what is within reach of it "
        "then lies partly outside London, and not given where under 50 in 100 of the area's homes "
        "are in an output area that is counted: land outside London with no home near may still "
        "be within reach of an output area that is counted."
    )


def within_at(metres: int) -> Method:
    """The record of the count for one distance, in whole metres.

    The distance is part of the id, so that two distances name two records.
    The sentence does not say what is counted: the measure's own does.
    """
    return Method(
        derivation_id=f"places_within_{metres}m_at_homes@1",
        sentence=f"The number of places that count within {metres} metres, in a straight line, "
        "of the point where the homes of each census output area are taken to stand, as the mean "
        f"over the area's homes at the census, {at_the_edge(metres)}",
        kind=Kind.MEASURED,
        parameters={"metres": metres, "enough_in_100": 50},
        code=CODE,
    )


def for_each_at(metres: int, per: int = PER) -> Method:
    """The record of the second figure: places for each so many homes within the same reach."""
    return Method(
        derivation_id=f"places_per_{per}_homes_within_{metres}m@1",
        sentence=f"The places that count within {metres} metres, in a straight line, of the "
        "point where the homes of each census output area are taken to stand, added up over the "
        "area's homes at the census, over the homes within the same distance of the same points "
        f"added up the same way, times {per}, {at_the_edge(metres)}",
        kind=Kind.MEASURED,
        parameters={"metres": metres, "per_homes": per, "enough_in_100": 50},
        code=CODE,
    )


def share_at(metres: int) -> Method:
    """The record of a share: what is within reach of one kind, over what is of every kind."""
    return Method(
        derivation_id=f"share_of_places_within_{metres}m@1",
        sentence=f"Of the places that count within {metres} metres, in a straight line, of the "
        "point where the homes of each census output area are taken to stand, the share that "
        "are of the kind asked for, each added up over the area's homes at the census before "
        f"one is divided by the other, times 100, {at_the_edge(metres)}",
        kind=Kind.MEASURED,
        parameters={"metres": metres, "enough_in_100": 50, "times": 100},
        code=CODE,
    )


def nearest_at(metres: int) -> Method:
    """The record of the distance to the nearest place, looked for as far as so many metres."""
    return Method(
        derivation_id=f"nearest_place_within_{metres}m@1",
        sentence="The distance in a straight line from the point where the homes of each census "
        "output area are taken to stand to the nearest place that counts, where one stands "
        f"within {metres} metres, as the median over the area's homes at the census, which is "
        "the mean of the two middle distances where the homes divide exactly in half between "
        "them, and not given where under 50 in 100 of the area's homes are in an output area "
        "with such a place.",
        kind=Kind.MEASURED,
        parameters={"metres": metres, "enough_in_100": 50},
        code=CODE,
    )


def metres_to_a_degree(latitude: float) -> Point:
    """How many metres a degree east and a degree north are, on the ground at a latitude."""
    sine = math.sin(math.radians(latitude))
    bent = math.sqrt(1 - ECCENTRICITY_SQUARED * sine * sine)
    east = RADIUS / bent * math.cos(math.radians(latitude))
    north = RADIUS * (1 - ECCENTRICITY_SQUARED) / (bent * bent * bent)
    return math.radians(east), math.radians(north)


def metres_between(a: Point, b: Point) -> float:
    """The distance on the ground between two points near each other, in a straight line.

    Each is a longitude and a latitude. The metres to a degree are those at
    the first point, which is where homes are.
    """
    east, north = metres_to_a_degree(a[1])
    return math.hypot((b[0] - a[0]) * east, (b[1] - a[1]) * north)


def kept(points: Iterable[Weighed]) -> dict[Square, list[Weighed]]:
    """Points, kept by the square each stands on, so that what is near is found by looking near."""
    on: dict[Square, list[Weighed]] = {}
    for point in sorted(points):
        on.setdefault((math.floor(point[0] / ACROSS), math.floor(point[1] / UP)), []).append(point)
    return on


def _squares(at: Point, metres: float, east: float, north: float) -> tuple[range, range]:
    """The squares that a circle round a point may touch."""
    across, up = metres / east, metres / north
    return (
        range(math.floor((at[0] - across) / ACROSS), math.floor((at[0] + across) / ACROSS) + 1),
        range(math.floor((at[1] - up) / UP), math.floor((at[1] + up) / UP) + 1),
    )


def within(
    held: Mapping[Square, Sequence[Weighed]], at: Point, metres: int, slots: int
) -> list[int]:
    """What the points within so many metres of a point add up to, in each slot.

    A point at exactly the distance is within it.
    """
    east, north = metres_to_a_degree(at[1])
    columns, rows = _squares(at, metres, east, north)
    most = float(metres) * float(metres)
    found = [0] * slots
    for column in columns:
        for row in rows:
            for longitude, latitude, slot, adds in held.get((column, row), ()):
                across, up = (longitude - at[0]) * east, (latitude - at[1]) * north
                if across * across + up * up <= most:
                    found[slot] += adds
    return found


def nearest(held: Mapping[Square, Sequence[Weighed]], at: Point, metres: int) -> int | None:
    """The slot of the nearest point within so many metres of a point, or none."""
    east, north = metres_to_a_degree(at[1])
    columns, rows = _squares(at, metres, east, north)
    best: tuple[float, int] | None = None
    for column in columns:
        for row in rows:
            for longitude, latitude, slot, _ in held.get((column, row), ()):
                across, up = (longitude - at[0]) * east, (latitude - at[1]) * north
                squared = across * across + up * up
                if squared <= float(metres) * float(metres) and (best is None or squared < best[0]):
                    best = (squared, slot)
    return None if best is None else best[1]


def nearest_within(
    held: Mapping[Square, Sequence[Weighed]], at: Point, metres: int, slots: int
) -> list[float | None]:
    """How far the nearest point of each slot stands from a point, in metres.

    None for a slot with no point within so many metres. A point at exactly
    the distance is within it. It is measured as what is within reach is.
    """
    east, north = metres_to_a_degree(at[1])
    columns, rows = _squares(at, metres, east, north)
    most = float(metres) * float(metres)
    best: list[float | None] = [None] * slots
    for column in columns:
        for row in rows:
            for longitude, latitude, slot, _ in held.get((column, row), ()):
                across, up = (longitude - at[0]) * east, (latitude - at[1]) * north
                squared = across * across + up * up
                nearest = best[slot]
                if squared <= most and (nearest is None or squared < nearest):
                    best[slot] = squared
    return [None if squared is None else math.sqrt(squared) for squared in best]


def inside(box: tuple[float, float, float, float], at: Point, metres: int) -> bool:
    """Whether everything within so many metres of a point lies in a box of degrees.

    The box is west, south, east and north. A part of a file holds every place
    of its box, so what is nearest to a point is known where this holds.
    """
    east, north = metres_to_a_degree(at[1])
    across, up = metres / east, metres / north
    west, south, furthest_east, furthest_north = box
    return (
        west <= at[0] - across
        and at[0] + across <= furthest_east
        and south <= at[1] - up
        and at[1] + up <= furthest_north
    )


def nearest_of(
    points: Iterable[Weighed],
    slots: int,
    centred: Sequence[tuple[str, Point, int]],
    metres: int,
    box: tuple[float, float, float, float] | None = None,
) -> dict[str, tuple[float | None, ...]]:
    """How far the nearest point of each slot stands from each output area that has a centre.

    `box` is the box the places were taken in, where part of a file was
    taken. An output area whose reach is not wholly in it has no verdict,
    because a nearer place may stand outside the box.
    """
    of_places = kept(points)
    return {
        oa: tuple(nearest_within(of_places, point, metres, slots))
        for oa, point, _ in centred
        if box is None or inside(box, point, metres)
    }


def first_of_each(points: Sequence[Point], metres: float) -> list[int]:
    """For each point, the place in the list of the first point it stands beside, or its own.

    It is how several records of one thing are told to be one: a point within
    so many metres of a point that came before it, and that stands for
    itself, is that point again. A point is held to the first of its group and
    never to the last, so a row of points each beside the next is not taken to
    be one thing from end to end. The points are taken in the order given, so
    hand them over in an order that does not change.
    """
    firsts: dict[Square, list[int]] = {}
    found: list[int] = []
    for place, point in enumerate(points):
        east, north = metres_to_a_degree(point[1])
        columns, rows = _squares(point, metres, east, north)
        near = [
            first
            for column in columns
            for row in rows
            for first in firsts.get((column, row), ())
            if metres_between(points[first], point) <= metres
        ]
        if near:
            found.append(min(near))
            continue
        found.append(place)
        square = (math.floor(point[0] / ACROSS), math.floor(point[1] / UP))
        firsts.setdefault(square, []).append(place)
    return found


def outside_london(
    placed: Opened, found: Spine, on_the_grid: Mapping[str, Point], metres: int
) -> list[Point]:
    """The centre of every output area outside London that may be within reach of one inside.

    The file of centres holds every output area of England and Wales. One that
    is not in the spine is outside London. Those that stand within the box
    round London's own centres, and so many metres beyond it and a little
    more, are turned to longitude and latitude. No other can be within reach.
    """
    inside = [point for oa, point in on_the_grid.items() if oa in found.area_of]
    if not inside:
        return []
    # A metre on the grid is not quite a metre on the ground, so the box is drawn wide.
    wide = 2 * metres
    west, east = min(p[0] for p in inside) - wide, max(p[0] for p in inside) + wide
    south, north = min(p[1] for p in inside) - wide, max(p[1] for p in inside) + wide
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
                beyond.append(longitude_and_latitude(*point))
    return sorted(beyond)


@dataclass(frozen=True)
class Ground:
    """Where the homes of a build are taken to stand, and what lies just outside London."""

    # The file of centres, as the step was handed it.
    placed: Opened
    # The centre of each output area of London that the file gives one for, as a longitude
    # and a latitude.
    at: Mapping[str, Point]
    # The centres of the output areas outside London that may be within reach of one inside.
    beyond: tuple[Point, ...]


def ground_of(inputs: Inputs, found: Spine, metres: int = METRES) -> Ground:
    """Where homes stand, from the files of the build. The gate is asked before the file is read."""
    placed = inputs.open(centres.CENTRES, Use.SCORING, edition=centres.CENTRES_EDITION)
    on_the_grid = centres.centres_of(placed, found)
    at = {oa: longitude_and_latitude(*on_the_grid[oa]) for oa in sorted(on_the_grid)}
    return Ground(placed, at, tuple(outside_london(placed, found, on_the_grid, metres)))


@dataclass(frozen=True)
class Reach:
    """What is within reach of where the homes of each output area are taken to stand."""

    metres: int
    # For each output area with a verdict: what is within reach, in each slot.
    within: Mapping[str, tuple[int, ...]]
    # For each output area with a verdict: the homes within the same reach, its own among them.
    homes: Mapping[str, int]
    # The output areas with a centre, and with no verdict: a centre outside London lies
    # within their reach.
    near_the_edge: tuple[str, ...]

    def of(self, slots: Iterable[int]) -> dict[str, float]:
        """What some slots add up to within reach of each output area that has a verdict."""
        wanted = tuple(slots)
        return {oa: float(sum(held[n] for n in wanted)) for oa, held in self.within.items()}

    def how_many_of(self, slots: Iterable[int]) -> dict[str, float]:
        """How many of some slots hold anything within reach of each output area."""
        wanted = tuple(slots)
        return {oa: float(sum(held[n] > 0 for n in wanted)) for oa, held in self.within.items()}


def reach_of(
    points: Iterable[Weighed],
    slots: int,
    ground: Ground,
    found: Spine,
    metres: int = METRES,
) -> Reach:
    """What is within reach of each output area that has a centre.

    `points` are the places, each with the slot it adds to and what it adds. An
    output area with a centre outside London within its reach has no verdict.
    """
    centred = [(oa, ground.at[oa], found.homes[oa]) for oa in sorted(ground.at)]
    return reach_at(points, slots, centred, ground.beyond, metres)


def reach_at(
    points: Iterable[Weighed],
    slots: int,
    centred: Sequence[tuple[str, Point, int]],
    beyond: Sequence[Point],
    metres: int = METRES,
) -> Reach:
    """The same, from the centres themselves: each output area with its centre and its homes.

    It is for a measure that keeps what it found for the next measure of a build, and so
    hands over what it can be known by. `beyond` holds the centres outside London.
    """
    of_places = kept(points)
    of_homes = kept((point[0], point[1], 0, homes) for _, point, homes in centred)
    of_beyond = kept((point[0], point[1], 0, 1) for point in beyond)
    counts: dict[str, tuple[int, ...]] = {}
    homes_within: dict[str, int] = {}
    near_the_edge: list[str] = []
    for oa, point, _ in centred:
        if within(of_beyond, point, metres, 1)[0]:
            near_the_edge.append(oa)
            continue
        counts[oa] = tuple(within(of_places, point, metres, slots))
        homes_within[oa] = within(of_homes, point, metres, 1)[0]
    return Reach(metres, counts, homes_within, tuple(near_the_edge))


def given(worked: Mapping[str, Worked], decimals: int = DECIMALS) -> dict[str, Worked]:
    """Each figure as it is given: to one decimal place, with a half taken upward."""
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, decimals))
        for area, one in worked.items()
    }


def figures(of_oa: Mapping[str, float], found: Spine) -> dict[str, Worked]:
    """The mean over each area's homes of what is within reach of each, or why it has none.

    `of_oa` holds a figure for each output area with a verdict. An output area
    with none adds nothing, and the area's coverage falls by its homes.
    """
    each = dict.fromkeys(found.area_of)
    return given(lsoa_value_by_homes(of_oa, {oa: oa for oa in each}, found.weights))


def rates(
    of_oa: Mapping[str, float], reach: Reach, found: Spine, per: int = PER
) -> dict[str, Worked]:
    """What is within reach for each 1,000 homes within the same reach, for every area.

    What is within reach of each home is added up over the area's homes, and
    so are the homes within reach of each home. One sum is divided by the
    other. An area with no home has no figure.
    """
    each = dict.fromkeys(found.area_of)
    top = {oa: found.homes[oa] * count for oa, count in of_oa.items()}
    bottom = {oa: float(found.homes[oa] * reach.homes[oa]) for oa in of_oa}
    unit_of = {oa: oa for oa in each}
    return given(lsoa_ratio_by_homes(top, bottom, unit_of, found.weights, times=float(per)))
