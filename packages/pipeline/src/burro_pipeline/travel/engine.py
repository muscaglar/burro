"""What a routing engine is asked, and what it gives back.

The step that works journeys out does not route. It hands an engine the places
journeys start and end at, one origin at a time, and takes back whole minutes.
The engine that will route London is R5, which needs Java and runs on a hosted
runner alone (ADR 0008 and the travel design, section 3). No module here
imports it, starts it or fetches it. What stands in for it in a test is the
plain router of `plain.py`, which is for the made-up town and nothing else.

An engine is asked for percentiles of the fastest journey over every
departure minute of a window, because that is what R5 gives: it never hands
over the time of each minute. So the rule of a percentile is the engine's to
keep, and `percentile_of` here is the rule this build asks of it:

    Put the times of the window in order, shortest first. A minute with no
    journey inside the cutoff counts as longer than any other. The figure at
    `p` is the time at place `ceil(p * n / 100)` of the `n`, counted from 1.

It is always a time that some departure minute has: nothing is averaged. At 50
it is the time that half of the departure minutes do at least as well as.
Whether R5 counts the same way is one of the things its first run must show.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

Lonlat = tuple[float, float]
# The most a cell of the build store can hold as minutes: one byte, with two values kept
# for "beyond the cutoff" and "not computed" (the travel design, section 8).
MOST_MINUTES = 253


@dataclass(frozen=True)
class Point:
    """Where a journey starts or ends. The id is the build's own, and never a name."""

    point_id: str
    at: Lonlat


@dataclass(frozen=True)
class Settings:
    """How journeys are worked out: section 4 of the travel design, as numbers.

    Every one is written into the record of a build. Two are first guesses
    that the design gives no figure for, and say so.
    """

    # The first departure minute, in seconds of the day, and how many minutes follow it.
    # 07:00 and 120 is every minute from 07:00 to 08:59.
    window_start: int = 7 * 3600
    departures: int = 120
    # What is kept of the window. Two are served, and the rest are kept so that the
    # choice of 90 can be changed without routing again.
    percentiles: tuple[int, ...] = (10, 25, 50, 75, 90)
    typical: int = 50
    just_missed: int = 90
    # The longest journey that is routed, in minutes. Anything longer is "beyond the cutoff".
    cutoff_pt: int = 120
    cutoff_cycle: int = 60
    cutoff_walk: int = 60
    # Metres in an hour.
    walk_speed: int = 4800
    cycle_speed: int = 15000
    most_rides: int = 4
    # A person must be at a stop this many seconds before what they board leaves.
    board_slack: int = 60
    # The longest walk to a stop or from one, and between two stops, in metres. First
    # guesses: the design names both as settings and gives neither a figure.
    longest_walk: int = 2400
    longest_change: int = 800
    # No time that is written is shorter, in minutes.
    floor: int = 2

    def __post_init__(self) -> None:
        cutoffs = (self.cutoff_pt, self.cutoff_cycle, self.cutoff_walk)
        asked = (self.typical, self.just_missed)
        if not all(1 <= cutoff <= MOST_MINUTES for cutoff in cutoffs):
            raise ValueError("a cutoff is from 1 to 253 minutes")
        if self.departures < 1 or not 0 <= self.window_start < 24 * 3600:
            raise ValueError("the window starts within the day and holds a minute or more")
        if list(self.percentiles) != sorted(set(self.percentiles)) or not all(
            1 <= percent <= 100 for percent in self.percentiles
        ):
            raise ValueError("percentiles are from 1 to 100, each once, in order")
        if not set(asked) <= set(self.percentiles) or self.typical > self.just_missed:
            raise ValueError("typical and just missed are percentiles that are kept, in order")
        if min(self.walk_speed, self.cycle_speed, self.most_rides) < 1 or self.board_slack < 0:
            raise ValueError("a speed and the most rides are 1 or more")
        if min(self.longest_walk, self.longest_change, self.floor) < 0:
            raise ValueError("a length and the floor are 0 or more")


@dataclass(frozen=True)
class Reached:
    """From one origin to every destination asked for, in the order asked, in whole minutes.

    `None` is no journey within the cutoff. It is never "not computed": an
    engine that cannot answer for an origin raises, and the build stops.
    """

    origin_id: str
    # For each percentile that is kept, a time for each destination.
    pt: Mapping[int, tuple[int | None, ...]]
    cycle: tuple[int | None, ...]
    walk: tuple[int | None, ...]


class Engine(Protocol):
    """What routes. It is made with its timetable and its streets, and is asked one origin."""

    @property
    def name(self) -> str: ...
    @property
    def version(self) -> str: ...
    def reach(
        self, origin: Point, destinations: Sequence[Point], settings: Settings
    ) -> Reached: ...


class RoutingError(Exception):
    """Journeys could not be worked out. Names a rule, and never a place."""

    def __init__(self, rule: str) -> None:
        self.rule = rule
        super().__init__(f"{MEANING[rule]} [{rule}]")


MEANING: Mapping[str, str] = {
    "origin_is_on_a_street": "a point that journeys start at is too far from any street",
    "destination_is_on_a_street": "a point that journeys end at is too far from any street",
    "stop_is_on_a_street": "a stop of the timetable is too far from any street",
    "window_is_in_the_timetable": "no trip of the timetable leaves within the window",
    "origins_are_given_once": "a point that journeys start at is given twice, or not at all",
    "answers_are_whole": "an engine answered for another origin, or for too few destinations",
    "same_twice": "the same origins routed twice gave two answers",
    "homes_have_a_weight": "an area has no home point, or a home point with no weight",
    "engine_is_installed": "the engine that routes a real timetable is not installed",
}


def percentile_of(times: Sequence[int | None], percent: int) -> int | None:
    """The time at a percentile of a window, by the rule at the top of this module."""
    if not times or not 1 <= percent <= 100:
        raise ValueError("a percentile is from 1 to 100, of one time or more")
    inside = sorted(time for time in times if time is not None)
    # `ceil(percent * n / 100)`, in whole numbers.
    place = -(-percent * len(times) // 100)
    return inside[place - 1] if place <= len(inside) else None


@dataclass(frozen=True)
class Fine:
    """Every origin that was routed, each to every destination: the fine matrices of a build."""

    destination_ids: tuple[str, ...]
    reached: tuple[Reached, ...] = field(default=())

    def __post_init__(self) -> None:
        ids = [one.origin_id for one in self.reached]
        if ids != sorted(set(ids)):
            raise RoutingError("origins_are_given_once")
        width = len(self.destination_ids)
        for one in self.reached:
            rows = (*one.pt.values(), one.cycle, one.walk)
            if any(len(row) != width for row in rows):
                raise RoutingError("answers_are_whole")
