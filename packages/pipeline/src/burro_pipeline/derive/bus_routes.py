"""How many routes of a bus stop near home, from the bus routes of Transport for London.

The file is the publisher's list of the stops of every route of London Buses, in
the order a bus calls at them: a row for each stop of each run of each route. It
is `Data_3rdParties_bus-sequences-` and the day it is of. Where homes are comes
from the centres of output areas, which `cells/centres.py` reads.

Five columns are read, and no other: `Route`, `Stop_Code_LBSL`,
`Location_Easting`, `Location_Northing` and `Virtual_Bus_Stop`. **No name is
read, of a stop or of anything else.**

**What the figure is.** The number of different routes with a stop within 400
metres, in a straight line, of where homes stand. A route counts once, however
many of its stops are near and whichever way it runs. It is the mean over an
area's homes, to one decimal place.

**It counts routes, and not buses.** The file says where each route stops, and
nothing of how often a bus runs or at what hours. A route of one bus an hour
counts as one of twelve. The registry entry asks that no figure made from the
file says how good a service is, and this one does not.

**What is no stop.** A row the file marks as a virtual stop. The publisher's
guide says that there is no bus stop at one, and asks that none is shown. Every
stop of a river service and of a tram is marked so, so no route of either is
counted.

**What is no route of its own.** The publisher's guide names no kind of route.
Each of these is what it was seen to be in the file of 3 October 2025:

| The name of a route | What it was seen to be | Counted |
|---|---|---|
| A number, or a letter or two and a number | A route | Yes |
| `N` and a number | A night route | Yes |
| A number and `X` | A route that misses stops out | Yes |
| `UL`, `TR` or `DL` and a number | A bus that stands in for a line that is shut | No |
| `Y` and the name of another route | That route, sent another way | No |

A bus that stands in for a line of rail, of the trams or of the DLR runs from
station to station: three in four of its stops are at one. A route named `Y`
and a number is the route of that number as it runs on the days it is sent
another way, and most of its stops are that route's. Half of the stops of a
night route, in the middle case, are those of the day route of its number.

A night route is counted because it is a route a person can take, and the file
does not say which routes run by day. So a home by a main road, where night
routes run, counts more routes than run at any one hour.

**The file is old, and the network changes often.** It is of 3 October 2025,
and is the newest the publisher has put out. The publisher's page gives two
weeks as the longest a figure from this feed may be shown before it is
updated. Whether a figure this old may be shown is to be settled with the
publisher before launch: the registry entry holds it. The day the file is of
is the period of the figure, and is shown beside it.

**Only the routes of London Buses are counted.** A route that another
authority runs is not in the file. So a home near London's edge may have more
buses than the figure says.

Nothing is filled in. An output area with no centre adds nothing, and the
coverage of its area falls by its homes. Nought is a figure: no route of the
file stops within 400 metres.
"""

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId, NativeResolution
from burro_core.release import Metric

from burro_pipeline.cells import centres
from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import school_primary_nearby
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import Worked, row_of
from burro_pipeline.derive.station_shapes import which_within
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.BUS_ROUTES_NEARBY
SOURCE = "tfl-bus-stops-and-routes"
PUBLISHER = "Transport for London"
PRODUCT = "the London Buses standard network data"
# The publisher's name for the file begins so, and ends with the day it is of.
FILE = re.compile(r"^Data_3rdParties_bus-sequences-[0-9]{8}\.csv$")
ROUTE, STOP, EASTING, NORTHING, VIRTUAL = (
    "Route",
    "Stop_Code_LBSL",
    "Location_Easting",
    "Location_Northing",
    "Virtual_Bus_Stop",
)
COLUMNS = (ROUTE, STOP, EASTING, NORTHING, VIRTUAL)
# How the file marks a stop that is one, and one at which there is no bus stop.
A_STOP, NO_STOP = "0", "1"
# A route that stands in for a line while it is shut, and a route as it runs on the days it
# is sent another way, by how each is named in the file of 3 October 2025. The guide
# defines neither. Neither is a route of its own.
STANDS_IN = re.compile(r"^(UL|TR|DL)[0-9]+[A-Z]?$")
SENT_ANOTHER_WAY = re.compile(r"^Y(?P<route>[0-9]+[A-Z]?)$")
# A route is within reach of a home where one of its stops is within this many metres.
REACH = 400
KEYED_BY = Geography.POINT
CENSUS = 2021
LABEL = "Bus routes that stop within 400 m of home, in a straight line"

METHOD = Method(
    derivation_id=f"routes_within_{REACH}m_by_homes@1",
    sentence="The number of different routes with a stop that counts within "
    f"{REACH} metres, in a straight line, of the point where the homes of each census output "
    "area are taken to stand, each route counted once however many of its stops are near, "
    "added up over the area's homes at the census and divided by those homes, and not given "
    "where under 50 in 100 of the area's homes are in an output area that has such a point.",
    kind=Kind.MEASURED,
    parameters={"metres": REACH, "enough_in_100": 50},
    code="burro_pipeline.derive.bus_routes",
)
METHODS = (METHOD,)
DEFINITION = (
    "The number of different bus routes that {publisher} gives in {product}, as at {day}, "
    "with a stop within {reach} metres, in a straight line, of where homes stand: each home is "
    "placed at the point the statistics office gives as the centre of its census output area, "
    "homes are counted as they stood at the census of {census}, and the figure is the mean "
    "over the area's homes, given to 1 decimal place with a half taken upward, so a route "
    "counts once however many of its stops are near, a night route counts as a day route "
    "does, a stop the publisher marks as virtual is no stop, a bus that stands in for a line "
    "of rail that is shut is no route, a route that another authority runs is not counted, "
    "and it says nothing of how often a bus runs, at what hours, or where it goes."
)
CANNOT_SEE = (
    "This counts the routes with a stop within a straight line of where the homes of each "
    "small census area are taken to stand, and not within a walk.",
    "It counts routes, and not buses: it cannot see how often a route runs, at what hours, "
    "or where it goes. A night route counts as a day route does.",
    "The file is of 3 October 2025, and the network changes often. Transport for London's "
    "page gives two weeks as the longest a figure from this feed may be shown before it is "
    "updated, and no newer file has been put out. Whether a figure this old may be shown is "
    "to be settled with Transport for London before launch.",
    "Only the routes of London Buses are counted, so a home near London's edge may have more "
    "buses than this says.",
)


@dataclass(frozen=True)
class Routes:
    """The stops of the file that count, each with the routes that call at it."""

    # Where each stop stands, on the National Grid, by the publisher's code of it.
    stops: Mapping[str, Point]
    # The routes that call at each stop, by the same code.
    routes: Mapping[str, frozenset[str]]
    # The day the file is of, as its receipt gives it.
    day: str
    file_id: str

    @property
    def every_route(self) -> frozenset[str]:
        return frozenset(route for routes in self.routes.values() for route in routes)


@dataclass(frozen=True)
class Nearby:
    """The measure for every area of the spine, with what stands behind it."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    # How many stops and how many routes count, and the routes of each output area.
    stops: int
    routes: int
    of_oa: Mapping[str, int]


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file of the stops of routes."""
    return FILE.fullmatch(name) is not None


def is_a_route(name: str, every: frozenset[str]) -> bool:
    """Whether a route of the file is a route of its own.

    One that stands in for a line while it is shut is not. Nor is one named
    for another route of the file, as that route runs when it is sent
    another way.
    """
    if STANDS_IN.fullmatch(name):
        return False
    copy = SENT_ANOTHER_WAY.fullmatch(name)
    return copy is None or copy["route"] not in every


def _stop(opened: Opened, why: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, why)


def read(opened: Opened) -> Routes:
    """The stops that count, each with the routes of its own that call at it.

    The file is held to this: every column that is read is there, a route and
    a stop have a name, a stop is marked as one or as virtual, a point is
    two numbers above nought, and a stop stands in one place.
    """
    rows: list[dict[str, str]] = []
    with opened.text() as text:
        for row in opened.rows(text, COLUMNS):
            if not row[ROUTE].strip() or not row[STOP].strip():
                raise _stop(opened, "a row names no route or no stop")
            if row[VIRTUAL] not in (A_STOP, NO_STOP):
                raise _stop(opened, "a stop is not said to be one or not")
            rows.append(row)
    every = frozenset(row[ROUTE].strip() for row in rows)
    stops: dict[str, Point] = {}
    routes: dict[str, set[str]] = {}
    for row in rows:
        route, stop = row[ROUTE].strip(), row[STOP].strip()
        if row[VIRTUAL] == NO_STOP or not is_a_route(route, every):
            continue
        try:
            point = float(row[EASTING]), float(row[NORTHING])
        except ValueError:
            point = math.nan, math.nan
        if not all(math.isfinite(part) and part > 0 for part in point):
            raise _stop(opened, "a point is no point")
        if stops.setdefault(stop, point) != point:
            raise _stop(opened, "a stop stands in two places")
        routes.setdefault(stop, set()).add(route)
    if not stops:
        raise _stop(opened, "it holds no stop that counts")
    return Routes(
        stops={stop: stops[stop] for stop in sorted(stops)},
        routes={stop: frozenset(routes[stop]) for stop in sorted(routes)},
        day=opened.receipt.data_period.days()[1],
        file_id=opened.file_id,
    )


def routes_within_reach(found: Routes, points: Mapping[str, Point]) -> dict[str, int]:
    """How many different routes stop within reach of each output area that has a centre."""
    ordered, stops = sorted(points), sorted(found.stops)
    near = which_within(
        [points[oa] for oa in ordered], [found.stops[stop] for stop in stops], REACH
    )
    return {
        oa: len({route for at in within for route in found.routes[stops[at]]})
        for oa, within in zip(ordered, near, strict=True)
    }


def definition_of(day: str) -> str:
    """The sentence a methods page prints for the measure."""
    return DEFINITION.format(
        publisher=PUBLISHER, product=PRODUCT, day=day, reach=REACH, census=CENSUS
    )


def build(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Nearby:
    """The measure for every area, and its evidence, from the files of the build.

    The gate is asked about the file of routes and about the centres before
    either is read. `found` is the spine of the same build. A row of evidence
    names the file of routes, the centres, the lookup and the table of homes.
    """
    opened = inputs.open(SOURCE, Use.SCORING, edition=edition, named=is_the_file)
    placed = inputs.open(centres.CENTRES, Use.SCORING, edition=centres.CENTRES_EDITION)
    points = centres.centres_of(placed, found)
    if not points:
        raise LockError("input_is_as_described", placed.file_id, "it holds no centre of the build")
    routes = read(opened)
    of_oa = routes_within_reach(routes, points)
    worked = school_primary_nearby.figures(of_oa, found.weights)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    behind = sorted({opened.file_id, placed.file_id, *found.inputs})
    if not all(file_id in handed for file_id in behind):
        raise ValueError("the spine is made from files of this build")
    files = tuple(handed[file_id] for file_id in behind)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, FEATURE), worked[area], METHOD, files)
        for area in sorted(worked)
    )
    metric = catalogue_row(
        FEATURE,
        method=METHOD,
        label=LABEL,
        native_resolution=NativeResolution.POINT,
        source_ids={receipt.source_id for receipt in files},
        vintage=routes.day,
        definition=definition_of(routes.day),
    )
    return Nearby(
        worked=worked,
        rows=rows,
        metric=metric,
        files=files,
        geography=KEYED_BY,
        stops=len(routes.stops),
        routes=len(routes.every_route),
        of_oa=of_oa,
    )
