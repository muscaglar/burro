"""What a timetable says of the days it runs on, for describe.

A timetable in TransXChange is a file of XML whose root is `TransXChange`.
Each service it holds states the day it runs from, the day it runs to where it
states one, and the kind of vehicle it is run with:

    TransXChange / Services / Service / OperatingPeriod / StartDate
    TransXChange / Services / Service / OperatingPeriod / EndDate
    TransXChange / Services / Service / Mode

The period of a file of timetables is the days its timetables say they run on,
and never the day the file was fetched. A list states it before the file has a
receipt, so describe gives the days.

Those three are read of each service and nothing else is: no stop, no name of
a line or of an operator, no time of a journey. A day is given as a day and as
nothing else, and a mode as one word of small letters. What a file writes in
the place of either that is neither is not given: the service is counted as
stating none. The file is read as far as the end of its services, which stand
before its journeys, and no further.
"""

import re
from collections import Counter
from datetime import date
from pathlib import Path

from burro_pipeline.fetch import markup

ROOT = "TransXChange"
SERVICES = (ROOT, "Services")
SERVICE = (*SERVICES, "Service")
RUNS_FROM = (*SERVICE, "OperatingPeriod", "StartDate")
RUNS_TO = (*SERVICE, "OperatingPeriod", "EndDate")
MODE = (*SERVICE, "Mode")
READ = frozenset({RUNS_FROM, RUNS_TO, MODE})
# The longest text that is looked at in the place of a day or of a mode.
LONGEST = 64
A_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
A_MODE = re.compile(r"[a-z]{1,20}")

Place = tuple[str, ...]
# What stood in each place of one service, each time the place was met. Nothing stands for
# what was no text: an element, or text too long to be a day or a word.
Met = dict[Place, list[str | None]]
Shape = dict[str, object]


class TimetableError(Exception):
    """The timetable could not be read. The message repeats nothing from the file."""


class _NotATimetable(Exception):
    """The root of the file is not the root of a timetable."""


class _Services:
    """What is read of a timetable, as the parser walks it: three places of each service."""

    def __init__(self) -> None:
        self.within: list[str] = []
        self.is_one = False
        self.found: list[Met] = []
        self._text: list[str] | None = None

    def begun(self, name: str, _: dict[str, str]) -> None:
        if not self.is_one and name != ROOT:
            raise _NotATimetable
        self.is_one = True
        if self._text is not None:
            # An element stands where a day or a word belongs.
            self._met(None)
        self.within.append(name)
        place = tuple(self.within)
        if place == SERVICE:
            self.found.append({})
        elif place in READ:
            self._text = []

    def text(self, piece: str) -> None:
        if self._text is not None:
            self._text.append(piece)
            if sum(len(part) for part in self._text) > LONGEST:
                self._met(None)

    def done(self, _: str) -> None:
        if self._text is not None:
            self._met("".join(self._text).strip())
        place = tuple(self.within)
        self.within.pop()
        if place == SERVICES:
            raise markup.Finished

    def _met(self, text: str | None) -> None:
        """Keep what stood in the place that is being read, and read no more of it."""
        self.found[-1].setdefault(tuple(self.within), []).append(text)
        self._text = None


def _the_one(service: Met, place: Place, shape: re.Pattern[str]) -> str:
    """What a service states in a place, where it states one thing there, of the shape."""
    met = service.get(place, [])
    if len(met) != 1 or met[0] is None or not shape.fullmatch(met[0]):
        return ""
    return met[0]


def _a_day(service: Met, place: Place) -> str:
    """The day a service states in a place, where it is a day the calendar has."""
    found = _the_one(service, place, A_DAY)
    try:
        return date.fromisoformat(found).isoformat() if found else ""
    except ValueError:
        return ""


def runs(path: Path) -> Shape | None:
    """The days the services of a timetable say they run from and to, and their modes.

    Nothing for a file of XML that is no timetable. `runs_from` is the
    earliest day any service runs from, and `runs_to` the latest day any runs
    to. A service that states no day is counted, under `no_day_from` or
    `no_day_to`, and adds nothing to either.
    """
    walk = _Services()
    try:
        with path.open("rb") as file:
            markup.read(file, walk.begun, walk.done, walk.text)
    except _NotATimetable:
        return None
    except markup.MarkupError as error:
        if not walk.is_one:
            return None
        raise TimetableError(f"the timetable could not be read: {error}") from None
    if not walk.is_one:
        return None
    first = [_a_day(service, RUNS_FROM) for service in walk.found]
    last = [_a_day(service, RUNS_TO) for service in walk.found]
    modes = Counter(_the_one(service, MODE, A_MODE) for service in walk.found)
    found: Shape = {"root": ROOT, "services": len(walk.found)}
    if any(first):
        found["runs_from"] = min(day for day in first if day)
    if any(last):
        found["runs_to"] = max(day for day in last if day)
    for name, days in (("no_day_from", first), ("no_day_to", last)):
        if days.count(""):
            found[name] = days.count("")
    if named := {mode: count for mode, count in sorted(modes.items()) if mode}:
        found["modes"] = named
    return found
