"""The stations Transport for London serves, and which of its modes call at each.

The file is a zip of tables that Transport for London publishes as its
station data. Four of the tables are read, and of each the columns named here
and no other:

| Table | Columns | What it says |
|---|---|---|
| `ModesAndLines.csv` | `Mode`, `Name` | Which mode each line is of |
| `Platforms.csv` | `UniqueId`, `StationUniqueId` | Which station each platform is of |
| `PlatformServices.csv` | `PlatformUniqueId`, `Line` | Which lines call at each platform |
| `StationPoints.csv` | `StationUniqueId`, `Lon`, `Lat` | Where the points of each station are |

So a mode calls at a station where a line of that mode calls at one of its
platforms. The modes are the publisher's seven: the Underground, the DLR, the
Overground, the Elizabeth line, National Rail, the trams and the cable car.

**No name is read, of a station or of anything in one.** `Stations.csv` is not
opened. Nor is any table of lifts, toilets or ways through a station: the
registry entry asks that nothing is said of a station from what such a table
leaves out, and nothing here reads one.

**What this is for.** The national file of stops gives one kind of railway
station, whoever runs its trains. This file tells the Overground and the
Elizabeth line from other rail. A step joins the two by where a station
stands, because the two files share no code that a step may trust unchecked.

**What it cannot say.** A station this file does not hold is one Transport for
London does not serve, and no more is known of it from here. National Rail is
given for the stations the publisher serves and for some it does not, so that a
station is missing from the file says nothing of which trains call at it.

What the parser holds the file to: each table is there with the columns that
are read, a line of a service is one the table of lines names, a mode is one of
the seven, a platform of a service is one the table of platforms names, a
point is two numbers that stand in or near Britain, and a station with a
service has a point. A file that breaks one stops the build.
"""

import math
from collections.abc import Collection
from dataclasses import dataclass

from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.shapes import national_grid
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

SOURCE = "tfl-step-free-station-topology"
PUBLISHER = "Transport for London"
PRODUCT = "its station data"
# The publisher's name for the file.
FILE = "tfl-stationdata-detailed.zip"
# The tables that are read, and the columns of each.
LINES, LINES_COLUMNS = "ModesAndLines.csv", ("Mode", "Name")
PLATFORMS, PLATFORMS_COLUMNS = "Platforms.csv", ("UniqueId", "StationUniqueId")
SERVICES, SERVICES_COLUMNS = "PlatformServices.csv", ("PlatformUniqueId", "Line")
POINTS, POINTS_COLUMNS = "StationPoints.csv", ("StationUniqueId", "Lon", "Lat")
# The modes, as the publisher writes them.
UNDERGROUND, DLR, OVERGROUND, ELIZABETH = "tube", "dlr", "overground", "elizabeth-line"
NATIONAL_RAIL, TRAM, CABLE_CAR = "nationalRail", "tram", "cableCar"
MODES = frozenset({UNDERGROUND, DLR, OVERGROUND, ELIZABETH, NATIONAL_RAIL, TRAM, CABLE_CAR})
# The three modes of a railway station.
OF_A_RAILWAY = frozenset({OVERGROUND, ELIZABETH, NATIONAL_RAIL})
# Where a point may stand: in or near Britain. One outside is no point of a station.
WEST, EAST, SOUTH, NORTH = -9.0, 3.0, 49.0, 61.0


@dataclass(frozen=True, order=True)
class Station:
    """One station of the file: the publisher's id of it, its modes and its points."""

    station_id: str
    modes: frozenset[str]
    # Every point the file gives for the station, on the National Grid, in order.
    points: tuple[Point, ...]

    def is_served_by(self, modes: Collection[str]) -> bool:
        return not self.modes.isdisjoint(modes)


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file of stations."""
    return name == FILE


def open_the_file(inputs: Inputs, use: Use, *, edition: str | None = None) -> Opened:
    """The file of stations, through the gate, for the use a step puts it to."""
    return inputs.open(SOURCE, use, edition=edition, named=is_the_file)


def _table(opened: Opened, name: str, columns: tuple[str, ...]) -> list[dict[str, str]]:
    with opened.text(inside=name) as text:
        return list(opened.rows(text, columns))


def _stop(opened: Opened, why: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, why)


def _placed(opened: Opened) -> dict[str, list[Point]]:
    """The points of each station, on the National Grid."""
    rows = _table(opened, POINTS, POINTS_COLUMNS)
    try:
        where = [(float(row["Lon"]), float(row["Lat"])) for row in rows]
    except ValueError:
        raise _stop(opened, "a point is no point") from None
    if not all(
        math.isfinite(lon) and math.isfinite(lat) and WEST <= lon <= EAST and SOUTH <= lat <= NORTH
        for lon, lat in where
    ):
        raise _stop(opened, "a point is no point")
    on_the_grid = national_grid([lon for lon, _ in where], [lat for _, lat in where])
    found: dict[str, list[Point]] = {}
    for row, point in zip(rows, on_the_grid, strict=True):
        found.setdefault(row["StationUniqueId"], []).append(point)
    return found


def read(opened: Opened) -> tuple[Station, ...]:
    """Every station of the file at which a line calls, in the order of their ids."""
    mode_of = {row["Name"]: row["Mode"] for row in _table(opened, LINES, LINES_COLUMNS)}
    if not mode_of or not set(mode_of.values()) <= MODES:
        raise _stop(opened, "a mode is none the step knows")
    station_of = {
        row["UniqueId"]: row["StationUniqueId"]
        for row in _table(opened, PLATFORMS, PLATFORMS_COLUMNS)
    }
    modes: dict[str, set[str]] = {}
    for row in _table(opened, SERVICES, SERVICES_COLUMNS):
        if row["Line"] not in mode_of:
            raise _stop(opened, "a service is of a line the file does not name")
        if row["PlatformUniqueId"] not in station_of:
            raise _stop(opened, "a service is at a platform the file does not name")
        modes.setdefault(station_of[row["PlatformUniqueId"]], set()).add(mode_of[row["Line"]])
    points = _placed(opened)
    if not modes or not set(modes) <= set(points):
        raise _stop(opened, "a station has no point")
    return tuple(
        Station(station, frozenset(modes[station]), tuple(sorted(points[station])))
        for station in sorted(modes)
    )
