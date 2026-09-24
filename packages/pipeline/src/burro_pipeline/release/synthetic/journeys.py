"""Journey times in the made-up city, worked out from where things are.

A straight line is never the way: streets add a detour, and the river has to
be crossed at a bridge. Public transport is the quickest of walking, a bus and
the railway of `names.LINES`, so an area on a line has the journeys its
station rows would lead a person to expect.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise

from burro_pipeline.release.synthetic.chart import Xy, distance
from burro_pipeline.release.synthetic.names import LINES

DETOUR = 1.3
BRIDGE_KM = 0.6
WALK_MIN_PER_KM = 12.0
CYCLE_MIN_PER_KM = 4.0
# Unlocking the bike and locking it again.
CYCLE_FIXED_MIN = 2.0
BUS_MIN_PER_KM = 3.2
# To the stop at one end and from the stop at the other.
BUS_WALK_MIN = 8.0
BUS_HEADWAY_MIN = 10.0
RAIL_MIN_PER_KM = 1.65
RAIL_DWELL_MIN = 0.7
INTERCHANGE_WALK_MIN = 3.0
# A journey by rail starts at one of this many stations nearest the door.
STATIONS_TRIED = 3
# No time in the release is shorter. Next door is still down the stairs and across the
# road, and a sentence that says "about 0 minutes" or "about 1 minutes" reads as a fault.
SHORTEST_MIN = 2


def whole_minutes(minutes: float) -> int:
    """A time as the release holds it: whole minutes, and never under the shortest."""
    return max(round(minutes), SHORTEST_MIN)


@dataclass(frozen=True)
class Spot:
    """A point journeys start or end at, and which side of the river it is on."""

    at: Xy
    south_bank: bool


@dataclass(frozen=True)
class Station:
    station_id: str
    name: str
    spot: Spot
    lines: tuple[str, ...]


def network_km(a: Spot, b: Spot) -> float:
    crossing = BRIDGE_KM if a.south_bank != b.south_bank else 0.0
    return DETOUR * distance(a.at, b.at) + crossing


def on_foot(a: Spot, b: Spot) -> float:
    return WALK_MIN_PER_KM * network_km(a, b)


def by_bike(a: Spot, b: Spot) -> float:
    return CYCLE_FIXED_MIN + CYCLE_MIN_PER_KM * network_km(a, b)


Platform = tuple[str, str]  # a station and a line that calls there


def _rides(stations: Mapping[str, Station]) -> Mapping[Platform, Mapping[Platform, float]]:
    """Minutes on the railway between any two platforms, changing where that is quicker.

    The time runs from the moment a train leaves the first platform to the
    moment one arrives at the second.
    """
    platforms = [(stop, line.name) for line in LINES for stop in line.stops]
    minutes = {a: {b: 0.0 if a == b else float("inf") for b in platforms} for a in platforms}
    for line in LINES:
        for here, there in pairwise(line.stops):
            apart = distance(stations[here].spot.at, stations[there].spot.at)
            run = RAIL_DWELL_MIN + RAIL_MIN_PER_KM * apart
            minutes[here, line.name][there, line.name] = run
            minutes[there, line.name][here, line.name] = run
    for station, line in platforms:
        for other in LINES:
            if other.name != line and station in other.stops:
                # Across the station, then half a headway for the next train, as on any day.
                minutes[station, line][station, other.name] = (
                    INTERCHANGE_WALK_MIN + other.headway / 2
                )
    for via in platforms:
        for a in platforms:
            for b in platforms:
                minutes[a][b] = min(minutes[a][b], minutes[a][via] + minutes[via][b])
    return minutes


class Network:
    """The railway and the buses: how long public transport takes, door to door."""

    def __init__(self, stations: Sequence[Station]) -> None:
        self._stations = tuple(stations)
        self._rides = _rides({station.name: station for station in stations})
        self._headways = {line.name: float(line.headway) for line in LINES}
        self._near: dict[Spot, list[tuple[Station, float]]] = {}

    def _stations_near(self, spot: Spot) -> list[tuple[Station, float]]:
        if spot not in self._near:
            walks = [(station, on_foot(spot, station.spot)) for station in self._stations]
            walks.sort(key=lambda pair: (pair[1], pair[0].station_id))
            self._near[spot] = walks[:STATIONS_TRIED]
        return self._near[spot]

    def _by_rail(self, origin: Spot, end: Spot, missed: bool) -> float:
        best = float("inf")
        for first, walk_there in self._stations_near(origin):
            for last, walk_from in self._stations_near(end):
                if first == last:
                    continue
                for line in first.lines:
                    # Someone who just missed a train waits the whole headway for the next.
                    wait = self._headways[line] * (1.0 if missed else 0.5)
                    ride = min(self._rides[first.name, line][last.name, to] for to in last.lines)
                    best = min(best, walk_there + wait + ride + walk_from)
        return best

    def minutes(self, origin: Spot, end: Spot, missed: bool) -> float:
        """By the quickest of train, bus and simply walking."""
        wait = BUS_HEADWAY_MIN * (1.0 if missed else 0.5)
        bus = BUS_WALK_MIN + wait + BUS_MIN_PER_KM * network_km(origin, end)
        return min(on_foot(origin, end), bus, self._by_rail(origin, end, missed))
