"""The file of stops: the ways in to London's stations, and how they gather into stations.

The Department for Transport publishes NaPTAN, its list of every point where a
person gets on or off public transport. A person saves the stops of one
authority from a form, as one CSV. This reads the file of Greater London, which
the form lists as authority 490.

**One row is one point, and a station is many rows.** The publisher's schema
guide, version 2.5, names the types of stop in its table 3-6. For a station it
names three: a way in from the street, an area inside, and a platform.

| `StopType` | The guide's name for it | Is it in the file of an authority |
|---|---|---|
| `RSE` | Rail Station Entrance | Yes |
| `RLY`, `RPL` | Railway Interchange Area, Railway Platform | No. Issued centrally, under 910 |
| `TMU` | Tram / Metro / Underground Entrance | Yes |
| `MET`, `PLT` | Underground or Metro Interchange Area, platform | No. Under 940 |
| `BCT` | A bus or coach stop on a street | Yes |
| `BCS` | A bay of a bus or coach station | Yes |
| `FTD` | Ferry Terminal / Dock Entrance | Yes. It is not read |

So the file of an authority holds the ways in to a station, and never the
station. The guide says the same, in its section 3.5.1: "Entrance records are
provided by the Local Administrative Area", and the area inside and the
platforms "will be provided centrally".

**The file tells two kinds of station apart, and no more.** A way in is to a
railway station or to a tram, metro or underground station. No column says
whose trains call: the Overground and the Elizabeth line are railway stations
here, as every other railway is. No column tells the Underground from the DLR
or from a tram. Most codes of a way in of the second kind hold two letters
after `ZZ`, and `letters_of` reads them. The guide defines no such letters, so
they are a hint and are counted as one. No figure turns on them.

**How rows are gathered into one station.** The file holds no group of stops:
the publisher keeps groups in a file of their own, which the form for one
authority does not give. The guide asks that every stop of one station has the
same `CommonName`, told apart by `Indicator`. So a station is here the ways in
of one kind that share a name, each within `APART` metres of another of them.
Two ways in of one name that stand further apart are two stations. A railway
station and an underground station of one name are two stations, because the
file gives them as two kinds.

What is read of a row: the seven columns of `NAMED`, and of those the name only
where a caller asks for stations. The file holds 43 columns. A row that is not
`active` is left out. A row of a type that is not asked for is left out before
its point is read.

What the parser holds the file to: every column that is read is there, a type
is one the guide names, a status is one the guide names, a code stands once,
a point that is read is on the National Grid and is two numbers that are not
below nought, and a way in to a station has a name. A file that breaks one stops the build.
"""

import math
import re
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass

from burro_pipeline.cells.centres import Point
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

SOURCE = "dft-naptan"
PUBLISHER, PRODUCT = "the Department for Transport", "NaPTAN"
# The authority whose stops the file holds, as the publisher's form lists it, and the
# publisher's name for the file of one authority: the code, then these words.
AUTHORITY, FILE_ENDS = "490", "Stops.csv"
# The columns that are read, by their names in the file. It holds 43.
CODE, NAME, TYPE, STATUS = "ATCOCode", "CommonName", "StopType", "Status"
GRID, EASTING, NORTHING = "GridType", "Easting", "Northing"
NAMED = (CODE, NAME, TYPE, STATUS, GRID, EASTING, NORTHING)
# The same, for a step that needs no name.
UNNAMED = tuple(column for column in NAMED if column != NAME)
# The two types of way in to a station, and the two types of stop of a bus.
RAIL, METRO = "RSE", "TMU"
ON_STREET, BAY = "BCT", "BCS"
STATION_TYPES, BUS_TYPES = (RAIL, METRO), (ON_STREET, BAY)
# Every type the publisher's guide names. One it does not name stops the build.
TYPES = frozenset(
    {"AIR", "BCE", "BCP", "BCQ", "BCS", "BCT", "BST", "FBT", "FER", "FTD", "GAT", "LCB"}
    | {"LPL", "LSE", "MET", "PLT", "RLY", "RPL", "RSE", "SDA", "STR", "TMU", "TXR"}
)
# What the guide calls each type that is read.
CALLED = {
    RAIL: "Rail Station Entrance",
    METRO: "Tram / Metro / Underground Entrance",
    ON_STREET: "bus or coach stop on a street",
    BAY: "bay of a bus or coach station",
}
# A row counts where its status is this. The guide names two more.
ACTIVE, STATUSES = "active", frozenset({"active", "inactive", "pending"})
# The grid a point is on, as the file writes it.
NATIONAL_GRID = "UKOS"
# Two ways in of one name that stand further apart than this are two stations, in metres.
APART = 1_000
# The letters a code may hold after `ZZ`, and what each was seen to stand for in the names
# of the file. The guide defines none of them.
LETTERS = re.compile(r"^[0-9]{4}ZZ([A-Z]{2})[A-Z0-9]+$")
SEEN_TO_BE = {"LU": "underground", "DL": "dlr", "CR": "tram", "AL": "cable_car"}


@dataclass(frozen=True, order=True)
class Stop:
    """One row of the file that is read: a way in to a station, or a stop of a bus."""

    code: str
    # One of the publisher's types, as `RSE`.
    type: str
    # On the National Grid, in metres.
    point: Point
    # The name, as the file gives it. None where the step did not ask for names.
    name: str | None = None


@dataclass(frozen=True, order=True)
class Station:
    """The ways in of one kind that share a name and stand together."""

    type: str
    name: str
    # In the order of their codes.
    ways_in: tuple[Stop, ...]

    @property
    def middle(self) -> Point:
        """The middle of its ways in, to the metre. The file gives a station no point."""
        across = math.fsum(way.point[0] for way in self.ways_in) / len(self.ways_in)
        up = math.fsum(way.point[1] for way in self.ways_in) / len(self.ways_in)
        return float(math.floor(across + 0.5)), float(math.floor(up + 0.5))

    @property
    def wide(self) -> float:
        """How far apart its two furthest ways in stand, in metres."""
        points = [way.point for way in self.ways_in]
        return max(math.dist(one, other) for one in points for other in points)

    @property
    def letters(self) -> str | None:
        """The two letters its codes hold, where every code that holds any holds the same."""
        held = {found for way in self.ways_in if (found := letters_of(way.code)) is not None}
        return held.pop() if len(held) == 1 else None


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file of London's stops."""
    return name == f"{AUTHORITY}{FILE_ENDS}"


def letters_of(code: str) -> str | None:
    """The two letters a code holds after `ZZ`, or none. A hint, which the guide does not define."""
    found = LETTERS.match(code)
    return found.group(1) if found else None


def _point(opened: Opened, row: dict[str, str]) -> Point:
    try:
        point = float(row[EASTING]), float(row[NORTHING])
    except ValueError:
        point = math.nan, math.nan
    if row[GRID] != NATIONAL_GRID or not all(math.isfinite(part) and part >= 0 for part in point):
        raise LockError("input_is_as_described", opened.file_id, "a point is no point")
    return point


def read(opened: Opened, types: Collection[str], *, names: bool = False) -> tuple[Stop, ...]:
    """The rows of the types asked for that are active, in the order of their codes.

    Every row is held to the types and the statuses the guide names, whether
    or not it is asked for. The point of a row that is not asked for is never
    read, and a name is read only where `names` is given.
    """
    if not set(types) <= TYPES:
        raise ValueError("a type that is asked for is one the guide names")
    found: dict[str, Stop] = {}
    seen: set[str] = set()
    with opened.text() as text:
        for row in opened.rows(text, NAMED if names else UNNAMED):
            if row[TYPE] not in TYPES:
                raise LockError("input_is_as_described", opened.file_id, "a type is not known")
            if row[STATUS] not in STATUSES:
                raise LockError("input_is_as_described", opened.file_id, "a status is not known")
            if not row[CODE] or row[CODE] in seen:
                raise LockError(
                    "input_is_as_described", opened.file_id, "a code stands twice or not at all"
                )
            seen.add(row[CODE])
            if row[TYPE] not in types or row[STATUS] != ACTIVE:
                continue
            name = row[NAME].strip() if names else None
            if name == "":
                raise LockError("input_is_as_described", opened.file_id, "a stop has no name")
            found[row[CODE]] = Stop(row[CODE], row[TYPE], _point(opened, row), name)
    if not found:
        raise LockError("input_is_as_described", opened.file_id, "it holds no stop that is read")
    return tuple(found[code] for code in sorted(found))


def _together(stops: Sequence[Stop]) -> list[list[Stop]]:
    """Stops of one name, in groups: each stands within `APART` of another of its group."""
    groups: list[list[Stop]] = []
    for stop in stops:
        near = [
            group
            for group in groups
            if any(math.dist(stop.point, other.point) <= APART for other in group)
        ]
        joined = [stop, *(other for group in near for other in group)]
        groups = [group for group in groups if not any(group is one for one in near)]
        groups.append(sorted(joined))
    return groups


def stations_of(stops: Iterable[Stop]) -> tuple[Station, ...]:
    """The stations the ways in gather into, in the order of their kind, name and first code."""
    named: dict[tuple[str, str], list[Stop]] = {}
    for stop in sorted(stops):
        if stop.type not in STATION_TYPES or stop.name is None:
            raise ValueError("a station is gathered from ways in that have a name")
        named.setdefault((stop.type, stop.name), []).append(stop)
    found = [
        Station(kind, name, tuple(group))
        for (kind, name), of_the_name in named.items()
        for group in _together(of_the_name)
    ]
    return tuple(sorted(found))


def open_the_file(inputs: Inputs, use: Use, *, edition: str | None = None) -> Opened:
    """The file of London's stops, through the gate, for the use a step puts it to."""
    return inputs.open(SOURCE, use, edition=edition, named=is_the_file)
