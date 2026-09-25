"""A journey timed from a timetable: the walk, the wait, each train, each change, the walk.

This is the measure an estimate of a journey is held against (decision record
0027). It is no routing engine and builds no release: it knows no street, and
walks in a straight line made longer by one number. It times a journey on the
trains it is handed and on nothing else, so a journey that a person would make
by a train it was not handed is not timed by it.

**The question it answers.** A person must be at a place by a time. When is
the last moment they can leave home? The journey is what lies between the two.
It is asked for every minute of a window, and the journey of the window is the
one that half of those minutes do at least as well as, by the rule of a
percentile that `engine.py` holds.

**So no wait is assumed.** A person who must be there by a time leaves so as to
meet a train, and is early by whatever the timetable makes them. Over the
minutes of a window that comes to half the time between trains where trains
are evenly spaced, and to what the timetable gives where they are not.

How one time is worked out, for one place and one minute to be there by:

1. From every platform within a walk of the place, a person must step off a
   train early enough to walk out and to the place.
2. The trains are taken from the last to leave to the first. A train helps
   from a platform where it leaves, if a person who stays on it can step off
   in time at a platform further on: in time to walk to the place, or to
   change to a train that helps.
3. The last train that helps from a platform is the one to board there.
4. A person leaves home in time to walk to a platform and board. Of the
   platforms within a walk of home, the one that lets them leave last is
   theirs. They walk all the way where that lets them leave later still.

What it cannot see is what no timetable holds: a delay, a closure, a full
train, a lift that is out, a hill, and which door of a station is open. What
stands for the way between a street and a platform is one number, the same at
every station.

Standard library only.
"""

import math
from bisect import bisect_left, bisect_right
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_pipeline.travel.engine import percentile_of
from burro_pipeline.travel.feed import Trip

Point = tuple[float, float]
NEVER = -(10**9)


@dataclass(frozen=True)
class Assumed:
    """What a journey is timed with that no timetable holds. A time is seconds, a length metres.

    `docs/research/data/journey-estimate-held-against-timetables.md` says where
    each number is from, and which are nobody's but the measure's own.
    """

    # Metres walked in an hour.
    walk_speed: int = 4800
    # How much further a walk is than the straight line between its ends.
    detour: float = 1.3
    # Between a street and a platform, at each end of a journey.
    in_and_out: int = 120
    # Between stepping off one train and standing where the next is boarded, before any
    # walk between two platforms that stand apart.
    change: int = 240
    # Between stepping off a train and boarding the next at the same platform.
    same_platform: int = 60
    # The longest walk to a platform or from one, and the longest all the way, as a
    # straight line. And the longest between two platforms.
    longest_walk: int = 2400
    longest_change: int = 800
    # The first and the last minute a person must be there by, in seconds of the day.
    first: int = 8 * 3600
    last: int = 9 * 3600 + 30 * 60
    # The journey of a window is the one this many in 100 of its minutes do as well as.
    typical: int = 50
    # The longest journey that is timed. A longer one is no journey.
    cutoff: int = 120 * 60

    def __post_init__(self) -> None:
        if self.walk_speed < 1 or self.detour < 1 or not 1 <= self.typical <= 100:
            raise ValueError("a speed is 1 or more, a detour 1 or more, a percentile 1 to 100")
        if min(self.in_and_out, self.change, self.same_platform) < 0:
            raise ValueError("a time is 0 or more")
        if min(self.longest_walk, self.longest_change) < 0 or self.first % 60 or self.last % 60:
            raise ValueError("a length is 0 or more, and a window begins and ends on a minute")
        if not 0 <= self.first <= self.last or self.cutoff < 60:
            raise ValueError("a window begins before it ends, and a journey may take a minute")

    @property
    def minutes(self) -> tuple[int, ...]:
        """Every minute of the window a person must be there by, in seconds of the day."""
        return tuple(range(self.first, self.last + 1, 60))

    def walk(self, metres: float) -> int:
        """How long a walk between two points takes, in whole seconds, rounded up.

        A walk that comes to a whole second is that second: what a machine adds
        in working it out, a millionth of a second or less, rounds nothing up.
        """
        return math.ceil(round(metres * self.detour * 3600 / self.walk_speed, 6))


@dataclass(frozen=True)
class Timed:
    """One journey as it was timed over a window."""

    # Whole minutes, rounded up: a limit is a promise that the journey fits within it.
    # Nothing where too few of the minutes of the window have a journey within the cutoff.
    minutes: int | None
    # How many trains the journey takes: what most of the minutes that take the typical
    # time take. None of them is a journey on foot all the way.
    rides: int = 0


class Trains:
    """The trains of one day, laid out to be asked of many times."""

    def __init__(self, trips: Sequence[Trip], stops: Mapping[str, Point], assumed: Assumed) -> None:
        self.assumed = assumed
        called = sorted({stop for trip in trips for stop in trip.stops})
        if not set(called) <= set(stops):
            raise ValueError("every stop a train calls at has a point")
        self.stops: tuple[str, ...] = tuple(called)
        self.points: tuple[Point, ...] = tuple(stops[stop] for stop in called)
        place = {stop: number for number, stop in enumerate(called)}
        # Every hop of every train from one call to the next: when it leaves, where from,
        # when it arrives, where, and which train. The first to leave comes first, and of
        # one train the earlier hop.
        hops = sorted(
            (trip.departs[at], at, number)
            for number, trip in enumerate(trips)
            for at in range(len(trip.stops) - 1)
        )
        self._leaves = [leaves for leaves, _, _ in hops]
        self._hops = [
            (
                leaves,
                place[trips[number].stops[at]],
                trips[number].arrives[at + 1],
                place[trips[number].stops[at + 1]],
                number,
            )
            for leaves, at, number in hops
        ]
        self._trains = len(trips)
        # To each platform, the platforms a person can change from, and how long it takes.
        self._into: list[list[tuple[int, int]]] = [
            [
                (other, self._change(number, other))
                for other in range(len(called))
                if math.dist(self.points[number], self.points[other]) <= assumed.longest_change
            ]
            for number in range(len(called))
        ]

    def _change(self, to: int, other: int) -> int:
        if to == other:
            return self.assumed.same_platform
        apart = math.dist(self.points[to], self.points[other])
        return self.assumed.change + self.assumed.walk(apart)

    def within_a_walk(self, point: Point) -> dict[int, int]:
        """The platforms within a walk of a point, and the seconds between each and the point.

        The way between the street and the platform is counted in.
        """
        found: dict[int, int] = {}
        for number, at in enumerate(self.points):
            apart = math.dist(point, at)
            if apart <= self.assumed.longest_walk:
                found[number] = self.assumed.in_and_out + self.assumed.walk(apart)
        return found

    def boarded_by(self, place: Point, by: int) -> tuple[list[int], list[int]]:
        """For each platform, when the last train leaves that gets a person to a place by a time.

        And how many trains that journey takes. `NEVER` is a platform that no
        train leaves in time.
        """
        platforms = len(self.stops)
        # The latest a person may step off a train at each platform, and the trains they
        # take from there on.
        step_off = [NEVER] * platforms
        rides_after = [0] * platforms
        for platform, walk in self.within_a_walk(place).items():
            step_off[platform] = by - walk
        board = [NEVER] * platforms
        rides_from = [0] * platforms
        helps = [False] * self._trains
        rides_on = [0] * self._trains
        # No train that leaves after the time, or longer before it than the cutoff, helps.
        first = bisect_left(self._leaves, by - self.assumed.cutoff)
        last = bisect_right(self._leaves, by)
        for leaves, start, arrives, end, train in reversed(self._hops[first:last]):
            if arrives <= step_off[end]:
                rides = 1 + rides_after[end]
                if not helps[train] or rides < rides_on[train]:
                    helps[train], rides_on[train] = True, rides
            if not helps[train] or leaves <= board[start]:
                continue
            board[start], rides_from[start] = leaves, rides_on[train]
            for other, takes in self._into[start]:
                if leaves - takes > step_off[other]:
                    step_off[other], rides_after[other] = leaves - takes, rides_on[train]
        return board, rides_from

    def to(self, place: Point) -> "Reaching":
        """The place, as it is reached at every minute of the window. Worked out once for it."""
        return Reaching(self, place, [self.boarded_by(place, by) for by in self.assumed.minutes])


@dataclass(frozen=True)
class Reaching:
    """One place, and when the last train leaves each platform for it, minute by minute."""

    trains: Trains
    place: Point
    boarded: Sequence[tuple[list[int], list[int]]]

    def timed_from(self, home: Point, within: Mapping[int, int] | None = None) -> Timed:
        """The journey from a home to the place, over the window.

        `within` is `within_a_walk` of the home, for a caller who asks of one
        home for many places and works it out once.
        """
        assumed = self.trains.assumed
        walks = list((self.trains.within_a_walk(home) if within is None else within).items())
        apart = math.dist(home, self.place)
        on_foot = assumed.walk(apart) if apart <= assumed.longest_walk else None
        took: list[int | None] = []
        rode: list[int] = []
        for by, (board, rides_from) in zip(assumed.minutes, self.boarded, strict=True):
            leaves, rides = (NEVER, 0) if on_foot is None else (by - on_foot, 0)
            for platform, walk in walks:
                if board[platform] - walk > leaves:
                    leaves, rides = board[platform] - walk, rides_from[platform]
            took.append(by - leaves if by - leaves <= assumed.cutoff else None)
            rode.append(rides)
        seconds = percentile_of(took, assumed.typical)
        if seconds is None:
            return Timed(None)
        most = Counter(rides for time, rides in zip(took, rode, strict=True) if time == seconds)
        return Timed(-(-seconds // 60), min(most, key=lambda rides: (-most[rides], rides)))
