"""For tests only: a plain, slow router for the made-up town. It routes no real place.

It stands in for the routing engine, so that the step that works journeys out
can be tested from a timetable to a release with nothing installed. It is
written to be read and checked by hand, and not to be fast: it asks the whole
timetable again for every departure minute of every origin. London has 4,994
origins and a timetable some thousands of times the size of the made-up one,
and the travel design (section 3) prices an engine written in Python at weeks
of work and then as long again to trust. This is not that engine.

What makes it fit for the made-up town alone:

- It measures as if the ground were flat, with one length for a degree each
  way. That holds on the equator, where the made-up town lies, and nowhere a
  person lives. It uses no sine and no cosine, so two machines agree.
- Its streets are a list of points and of links between them, each a whole
  number of metres, walked and cycled both ways. It reads no street extract.
- It knows no hill, no one-way street, no crossing and no stress of traffic.
- A point is put on the street at the nearest point of the list, by a
  straight line. An engine puts it on the nearest stretch of a street.

How a journey by public transport is found, for one departure minute:

1. Walk from the door to every stop within the longest walk.
2. For each ride up to the most rides: board any trip at a stop that was
   reached in time, a slack before it leaves, and ride it to every stop after.
   Then walk from each stop reached to the stops within a change of it.
3. Walk from each stop reached to the door at the other end, within the
   longest walk. Or walk all the way, if that is faster.

A time is counted in seconds and written as whole minutes, rounded up: a limit
of 40 minutes is a promise that the journey fits within it, and a journey of
40 minutes and a second does not.

Standard library only.
"""

import heapq
import math
from bisect import bisect_left, bisect_right
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_pipeline.travel.engine import (
    Lonlat,
    Point,
    Reached,
    RoutingError,
    Settings,
    percentile_of,
)
from burro_pipeline.travel.feed import Feed

# One length for a degree, each way: the made-up town is drawn with it.
METRES_PER_DEGREE = 111_320
# A point further than this from the streets is a defect (the travel design, section 4).
SNAP_LIMIT = 200
NEVER = 10**9


@dataclass(frozen=True)
class Streets:
    """The streets of the made-up town: points, and links of whole metres between them."""

    nodes: Mapping[str, Lonlat]
    links: tuple[tuple[str, str, int], ...]


def metres_between(a: Lonlat, b: Lonlat) -> int:
    """The straight line between two points, in whole metres, as if the ground were flat."""
    east = (a[0] - b[0]) * METRES_PER_DEGREE
    north = (a[1] - b[1]) * METRES_PER_DEGREE
    return int(math.sqrt(east * east + north * north) + 0.5)


def seconds_at(metres: int, speed: int) -> int:
    """How long a length takes at a speed of metres in an hour, in whole seconds, rounded up."""
    return -(-metres * 3600 // speed)


def minutes_of(seconds: int) -> int:
    """Whole minutes, rounded up."""
    return -(-seconds // 60)


class PlainRouter:
    """For tests only: routes the made-up town, one origin at a time."""

    name = "plain"
    version = "1"

    def __init__(self, feed: Feed, streets: Streets) -> None:
        self._first = [trip.departs[0] for trip in feed.trips]
        self._longest = max(trip.arrives[-1] - trip.departs[0] for trip in feed.trips)
        self._nodes = sorted(streets.nodes.items())
        self._next: dict[str, list[tuple[str, int]]] = {node: [] for node in streets.nodes}
        for a, b, metres in sorted(streets.links):
            self._next[a].append((b, metres))
            self._next[b].append((a, metres))
        # Where each stop stands on the streets: the point of them it is put on, the walk to
        # that point, and how far every other point of the streets is from it. A stop is
        # known by its place in the order of the ids, so that a time is looked up in a list.
        self._stops: list[tuple[str, int, dict[str, int]]] = []
        called_at = sorted({stop for trip in feed.trips for stop in trip.stops})
        for stop_id in called_at:
            node, walk = self._snap(feed.stops[stop_id].at)
            if node is None:
                raise RoutingError("stop_is_on_a_street")
            self._stops.append((node, walk, self._spread(node)))
        place = {stop_id: number for number, stop_id in enumerate(called_at)}
        self._trips = [
            (tuple(place[stop] for stop in trip.stops), trip.arrives, trip.departs)
            for trip in feed.trips
        ]
        self._snapped: dict[Lonlat, tuple[str | None, int]] = {}

    def _snap(self, at: Lonlat) -> tuple[str | None, int]:
        """The nearest point of the streets and the walk to it, or none within the limit."""
        walk, node = min((metres_between(at, point), node) for node, point in self._nodes)
        return (node, walk) if walk <= SNAP_LIMIT else (None, walk)

    def _spread(self, start: str) -> dict[str, int]:
        """The shortest way along the streets from one point of them to every other, in metres."""
        found: dict[str, int] = {}
        ahead = [(0, start)]
        while ahead:
            metres, node = heapq.heappop(ahead)
            if node in found:
                continue
            found[node] = metres
            for to, more in self._next[node]:
                if to not in found:
                    heapq.heappush(ahead, (metres + more, to))
        return found

    def _on_the_street(self, point: Point, rule: str) -> tuple[str, int]:
        if point.at not in self._snapped:
            self._snapped[point.at] = self._snap(point.at)
        node, walk = self._snapped[point.at]
        if node is None:
            raise RoutingError(rule)
        return node, walk

    def _walks(self, node: str, walk: int, longest: int, settings: Settings) -> dict[int, int]:
        """The stops within a walk of a point on the streets, and the seconds to each."""
        found: dict[int, int] = {}
        for stop, (_, to_the_street, spread) in enumerate(self._stops):
            if node in spread and walk + spread[node] + to_the_street <= longest:
                whole = walk + spread[node] + to_the_street
                found[stop] = seconds_at(whole, settings.walk_speed)
        return found

    def _changes(self, settings: Settings) -> list[list[tuple[int, int]]]:
        """From each stop, the other stops within a change of it, and the seconds to each."""
        return [
            [
                (other, seconds)
                for other, seconds in self._walks(
                    node, walk, settings.longest_change, settings
                ).items()
                if other != stop
            ]
            for stop, (node, walk, _) in enumerate(self._stops)
        ]

    def _arrivals(
        self,
        leaves: int,
        access: Mapping[int, int],
        changes: Sequence[Sequence[tuple[int, int]]],
        settings: Settings,
    ) -> list[int]:
        """The earliest a person who leaves the door at `leaves` can be at each stop."""
        first = bisect_left(self._first, leaves - self._longest)
        last = bisect_right(self._first, leaves + settings.cutoff_pt * 60)
        band = self._trips[first:last]
        slack = settings.board_slack
        best = [NEVER] * len(self._stops)
        for stop, walk in access.items():
            best[stop] = leaves + walk
        for _ in range(settings.most_rides):
            # What was reached with one ride fewer. Only from there may a trip be boarded.
            before = best[:]
            for stops, arrives, departs in band:
                aboard = False
                for stop, arrival, departure in zip(stops, arrives, departs, strict=True):
                    if aboard:
                        if arrival < best[stop]:
                            best[stop] = arrival
                    elif before[stop] + slack <= departure:
                        aboard = True
            sooner = [stop for stop, time in enumerate(best) if time < before[stop]]
            if not sooner:
                break
            for stop in sooner:
                for other, walk in changes[stop]:
                    if best[stop] + walk < best[other]:
                        best[other] = best[stop] + walk
        return best

    def reach(self, origin: Point, destinations: Sequence[Point], settings: Settings) -> Reached:
        window_end = settings.window_start + 60 * settings.departures
        if bisect_left(self._first, settings.window_start) >= bisect_left(self._first, window_end):
            raise RoutingError("window_is_in_the_timetable")
        node, walk = self._on_the_street(origin, "origin_is_on_a_street")
        spread = self._spread(node)
        ends = [self._on_the_street(end, "destination_is_on_a_street") for end in destinations]
        # By the streets, door to door. A place the streets do not lead to is never reached.
        apart = [walk + spread[end] + more if end in spread else None for end, more in ends]
        on_foot = [
            None if metres is None else seconds_at(metres, settings.walk_speed) for metres in apart
        ]
        by_bike = [
            None if metres is None else seconds_at(metres, settings.cycle_speed) for metres in apart
        ]
        access = self._walks(node, walk, settings.longest_walk, settings)
        egress = [self._walks(end, more, settings.longest_walk, settings) for end, more in ends]
        changes = self._changes(settings)

        window: list[list[int | None]] = [[] for _ in destinations]
        for minute in range(settings.departures):
            leaves = settings.window_start + 60 * minute
            arrivals = self._arrivals(leaves, access, changes, settings)
            for place, stops in enumerate(egress):
                whole = on_foot[place]
                for stop, more in stops.items():
                    at_stop = arrivals[stop]
                    if at_stop < NEVER and (whole is None or at_stop - leaves + more < whole):
                        whole = at_stop - leaves + more
                window[place].append(_within(whole, settings.cutoff_pt))
        return Reached(
            origin_id=origin.point_id,
            pt={
                percent: tuple(percentile_of(times, percent) for times in window)
                for percent in settings.percentiles
            },
            cycle=tuple(_within(seconds, settings.cutoff_cycle) for seconds in by_bike),
            walk=tuple(_within(seconds, settings.cutoff_walk) for seconds in on_foot),
        )


def _within(seconds: int | None, cutoff: int) -> int | None:
    """Whole minutes, or none where there is no journey within the cutoff."""
    if seconds is None:
        return None
    minutes = minutes_of(seconds)
    return minutes if minutes <= cutoff else None
