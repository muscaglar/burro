"""A timetable in TransXChange, as it stands on one day: what runs, where it calls and when.

Transport for London gives its timetables as files of XML in TransXChange, one
service of one line to a file. This reads one file for one day, and gives the
journeys that run on it, each with its calls and the time of each.

What is read, and where it stands in a file:

| What | Where |
|---|---|
| A stop, and where it stands | `StopPoint`: `AtcoCode`, `Easting` and `Northing` |
| The line and its mode | `Service`: `LineName` and `Mode` |
| The days the file runs from and to | `Service`: `OperatingPeriod` |
| The days of the week a journey runs on | `OperatingProfile`: `DaysOfWeek` |
| When a journey first leaves | `VehicleJourney`: `DepartureTime` |
| Where it calls | The links of its `JourneyPattern`: `From` and `To` |
| How long each stretch takes | Each link: `RunTime`, and a `WaitTime` at an end |

A point is in metres on the National Grid. A journey that states no days of
the week runs on its service's. One that states a `DepartureDayShift` first
leaves so many days after the day it runs on.

**How a run time is read.** The run time between two stops is `RunTime` of the
link between them. A journey leaves its first stop at its `DepartureTime`,
reaches the next a run time later, stands there for the waits the two links
state at that stop, and leaves. So the time of every call is a sum, and no
call has a time of its own in the file.

**How the time between two trains is read.** It is stated nowhere. It is the
time between the calls that two journeys make at one stop, one after the
other. A file that gives a journey as "every so many minutes" is refused, so
that every train that is counted has its own times.

**A stop that a train passes is no call.** A link whose end is `pass` adds its
time to the stretch, and the stop at that end is left out.

What is not read, and what follows:

- **No name.** Not of a stop, and not of where a journey is bound. A stop is
  known by its code.
- **No bank holiday.** What a journey states of bank holidays is not read, so
  the day asked for must be no bank holiday. That is the caller's to see to.
- **Whether a train may be boarded or left at a call.** A call at which a
  train stops is taken to be both.

A publisher may give a line two files that both run on one day: a timetable
for the season, and one for a few days of works. Nothing here chooses between
them. `on_the_day` refuses two that run on the day for one line, so that no
train is counted twice.

Transport for London gives its files in a zip of zips. `timetables_in` reads
the files of one whose names a caller asks for, and unpacks nothing to a disk.

A refusal names a rule, and never repeats a value from the file.

Standard library only.
"""

import io
import re
import zipfile
import zlib
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from burro_pipeline.fetch import markup
from burro_pipeline.travel.feed import DAY_SECONDS, Trip

ROOT = "TransXChange"
# The parts of a file that are read. Every other part is passed over, with all it holds.
PARTS = frozenset({"StopPoints", "JourneyPatternSections", "Services", "VehicleJourneys"})
# The days a profile may name, each as the days of the week it stands for, Monday first.
DAYS: Mapping[str, frozenset[int]] = {
    "Monday": frozenset({0}),
    "Tuesday": frozenset({1}),
    "Wednesday": frozenset({2}),
    "Thursday": frozenset({3}),
    "Friday": frozenset({4}),
    "Saturday": frozenset({5}),
    "Sunday": frozenset({6}),
    "MondayToFriday": frozenset(range(5)),
    "MondayToSaturday": frozenset(range(6)),
    "MondayToSunday": frozenset(range(7)),
    "NotSaturday": frozenset({0, 1, 2, 3, 4, 6}),
    "Weekend": frozenset({5, 6}),
}
# The elements that are kept as the file is walked. One that is not here is passed over.
KEPT = frozenset(
    {ROOT, *PARTS, *DAYS}
    | {"StopPoint", "AtcoCode", "Place", "Location", "Easting", "Northing"}
    | {"JourneyPatternSection", "JourneyPatternTimingLink", "From", "To", "Activity"}
    | {"StopPointRef", "WaitTime", "RunTime"}
    | {"Service", "Lines", "Line", "LineName", "Mode", "OperatingPeriod", "StartDate", "EndDate"}
    | {"OperatingProfile", "RegularDayType", "DaysOfWeek", "HolidaysOnly", "SpecialDaysOperation"}
    | {"StandardService", "JourneyPattern", "JourneyPatternSectionRefs"}
    | {"VehicleJourney", "VehicleJourneyCode", "DepartureTime", "DepartureDayShift"}
    | {"JourneyPatternRef", "VehicleJourneyRef", "VehicleJourneyTimingLink", "Frequency"}
)
PASSES = "pass"
# The most one file of a zip may unpack to, in bytes. The largest that was seen is a tenth.
LARGEST = 500_000_000
A_TIME = re.compile(r"(\d{2}):(\d{2}):(\d{2})")
A_LENGTH = re.compile(r"PT(?:(\d{1,3})H)?(?:(\d{1,4})M)?(?:(\d{1,5})S)?")
A_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
A_SHIFT = re.compile(r"[+]?\d")

MEANING: Mapping[str, str] = {
    "is_a_timetable": "is no timetable in TransXChange that can be read",
    "zip_is_read": "is in a zip that cannot be read, or unpacks to more than is read",
    "holds_one_service": "holds no service, or more than one",
    "service_is_stated": "holds a service that states no line, or no days it runs from and to",
    "stop_has_a_point": "holds a stop with no code, or with no point on the National Grid",
    "days_are_read": "states a day, or the days of a week, in a way that is not read",
    "times_are_read": "holds a time or a length of time that cannot be read",
    "references_resolve": "names a stop, a section or a pattern that it does not hold",
    "journey_has_a_pattern": "holds a journey that calls at fewer than two stops",
    "no_journey_is_a_headway": "gives a journey as a headway, and not by its own times",
    "no_journey_has_times_of_its_own": "holds a journey whose links state times of their own",
    "no_day_is_special": "states days of its own on which it runs or does not",
    "one_timetable_a_line": "is the second timetable of its line that runs on the day",
}

Point = tuple[float, float]


class TimetableError(Exception):
    """The timetable may not be timed on. Names a rule, and never a value of the file."""

    def __init__(self, rule: str) -> None:
        self.rule = rule
        super().__init__(f"the timetable {MEANING[rule]} [{rule}]")


@dataclass(frozen=True)
class Timetable:
    """One file, as it stands on one day: a service of one line."""

    line: str
    # The kind of vehicle, as the file says it: one word.
    mode: str
    # The first and the last day the file says it runs on.
    runs: tuple[date, date]
    # Every stop the file places, by its code: metres east and north on the National Grid.
    stops: Mapping[str, Point]
    # The journeys that run on the day, by the time each first leaves. A time is seconds of
    # the day, and is past the end of the day where a journey runs on after midnight.
    trips: tuple[Trip, ...]
    # Every journey of the file, whatever day it runs on.
    journeys: int


@dataclass
class _Node:
    """One element that is kept: its name, its id, its text and what it holds."""

    name: str
    id: str
    text: str = ""
    holds: list["_Node"] = field(default_factory=list["_Node"])

    def each(self, name: str) -> list["_Node"]:
        return [node for node in self.holds if node.name == name]

    def one(self, *names: str) -> "_Node | None":
        """The one element at the end of a path of names, or nothing where any is missing."""
        found: _Node | None = self
        for name in names:
            among = [] if found is None else found.each(name)
            found = among[0] if len(among) == 1 else None
        return found

    def said(self, *names: str) -> str:
        found = self.one(*names)
        return "" if found is None else found.text.strip()


class _Walk:
    """The kept elements of a file, gathered as it is walked once."""

    def __init__(self) -> None:
        self.root: _Node | None = None
        self._open: list[_Node] = []
        # How deep the walk is inside an element that is passed over.
        self._passed = 0

    def begun(self, name: str, given: dict[str, str]) -> None:
        if self.root is None:
            if name != ROOT:
                raise TimetableError("is_a_timetable")
            self.root = _Node(name, "")
            self._open.append(self.root)
        elif self._passed or not self._is_kept(name):
            self._passed += 1
        else:
            node = _Node(name, given.get("id", ""))
            self._open[-1].holds.append(node)
            self._open.append(node)

    def _is_kept(self, name: str) -> bool:
        """Whether an element is read. Whatever stands among the days of a week is, so that
        a day that is not known is refused and never passed over."""
        if len(self._open) == 1:
            return name in PARTS
        return name in KEPT or self._open[-1].name == "DaysOfWeek"

    def text(self, piece: str) -> None:
        if not self._passed and self._open:
            self._open[-1].text += piece

    def done(self, _: str) -> None:
        if self._passed:
            self._passed -= 1
        else:
            self._open.pop()


def seconds_of(text: str) -> int:
    """A length of time as the file writes it, `PT2M30S`, in seconds."""
    found = A_LENGTH.fullmatch(text)
    if found is None or not any(found.groups()):
        raise TimetableError("times_are_read")
    hours, minutes, seconds = (int(part or 0) for part in found.groups())
    return hours * 3600 + minutes * 60 + seconds


def _leaves(journey: _Node) -> int:
    """When a journey first leaves, in seconds of the day it runs on."""
    found = A_TIME.fullmatch(journey.said("DepartureTime"))
    shift = journey.said("DepartureDayShift") or "0"
    if found is None or not A_SHIFT.fullmatch(shift):
        raise TimetableError("times_are_read")
    hours, minutes, seconds = (int(part) for part in found.groups())
    if hours > 23 or minutes > 59 or seconds > 59:
        raise TimetableError("times_are_read")
    return int(shift) * DAY_SECONDS + hours * 3600 + minutes * 60 + seconds


def _a_day(text: str) -> date:
    try:
        return date.fromisoformat(text if A_DAY.fullmatch(text) else "")
    except ValueError:
        raise TimetableError("service_is_stated") from None


def _days(holder: _Node) -> frozenset[int] | None:
    """The days of the week a profile names, or nothing where its holder states no profile."""
    profile = holder.one("OperatingProfile")
    if profile is None:
        if holder.each("OperatingProfile"):
            raise TimetableError("days_are_read")
        return None
    if profile.each("SpecialDaysOperation"):
        raise TimetableError("no_day_is_special")
    regular = profile.one("RegularDayType")
    if regular is None:
        raise TimetableError("days_are_read")
    if regular.each("HolidaysOnly"):
        return frozenset()
    named = regular.one("DaysOfWeek")
    if named is None or not named.holds or any(day.name not in DAYS for day in named.holds):
        raise TimetableError("days_are_read")
    return frozenset(number for day in named.holds for number in DAYS[day.name])


def _stops(root: _Node) -> dict[str, Point]:
    found: dict[str, Point] = {}
    for stop in (root.one("StopPoints") or _Node("", "")).each("StopPoint"):
        code = stop.said("AtcoCode")
        east, north = (stop.said("Place", "Location", axis) for axis in ("Easting", "Northing"))
        if not code or not (east.isascii() and east.isdigit() and len(east) <= 7):
            raise TimetableError("stop_has_a_point")
        if not (north.isascii() and north.isdigit() and len(north) <= 7):
            raise TimetableError("stop_has_a_point")
        found[code] = (float(east), float(north))
    return found


# One stretch of a pattern: the stop at each end, whether a train stops there, the wait it
# makes there, and the run between the two. Times are seconds.
_Link = tuple[str, bool, int, str, bool, int, int]


def _end(link: _Node, which: str, stops: Mapping[str, Point]) -> tuple[str, bool, int]:
    end = link.one(which)
    code = "" if end is None else end.said("StopPointRef")
    if end is None or code not in stops:
        raise TimetableError("references_resolve")
    wait = end.one("WaitTime")
    return code, end.said("Activity") != PASSES, 0 if wait is None else seconds_of(wait.text)


def _sections(root: _Node, stops: Mapping[str, Point]) -> dict[str, list[_Link]]:
    found: dict[str, list[_Link]] = {}
    for section in (root.one("JourneyPatternSections") or _Node("", "")).each(
        "JourneyPatternSection"
    ):
        found[section.id] = [
            (*_end(link, "From", stops), *_end(link, "To", stops), seconds_of(link.said("RunTime")))
            for link in section.each("JourneyPatternTimingLink")
        ]
    return found


# Where a pattern calls, in order: the stop, and the seconds after the journey first leaves
# at which a train reaches it and leaves it.
_Calls = tuple[tuple[str, int, int], ...]


def _calls(links: Sequence[_Link]) -> _Calls:
    """The calls of a pattern, from its links in order. A stop a train passes is left out."""
    calls: list[tuple[str, int, int]] = []
    clock = 0
    for place, (start, stops, wait, end, stops_at_end, wait_at_end, run) in enumerate(links):
        if place and start != links[place - 1][3]:
            raise TimetableError("references_resolve")
        if place == 0 and stops:
            calls.append((start, clock, clock))
        if calls and calls[-1][0] == start:
            # The wait a link states at its start is made at the stop the last link ended at.
            calls[-1] = (start, calls[-1][1], calls[-1][2] + wait)
        clock += wait + run
        if stops_at_end:
            calls.append((end, clock, clock + wait_at_end))
        clock += wait_at_end
    if len(calls) < 2:
        raise TimetableError("journey_has_a_pattern")
    return tuple(calls)


def _patterns(service: _Node, sections: Mapping[str, list[_Link]]) -> dict[str, _Calls]:
    found: dict[str, _Calls] = {}
    for pattern in (service.one("StandardService") or _Node("", "")).each("JourneyPattern"):
        named = [ref.text.strip() for ref in pattern.each("JourneyPatternSectionRefs")]
        if not named or not all(name in sections for name in named):
            raise TimetableError("references_resolve")
        found[pattern.id] = _calls([link for name in named for link in sections[name]])
    return found


def _states_times(journey: _Node) -> bool:
    """Whether a link of a journey states a run or a wait of its own."""
    return any(
        link.each("RunTime") or any(end.each("WaitTime") for end in link.holds)
        for link in journey.each("VehicleJourneyTimingLink")
    )


def read(source: markup.Readable | bytes, day: date) -> Timetable:
    """One timetable as it stands on a day, or a refusal.

    Every journey of the file is read, and the ones that run on the day are
    kept. A file none of whose journeys runs on the day gives no trip, and is
    no refusal.
    """
    walk = _Walk()
    try:
        markup.read(source, walk.begun, walk.done, walk.text)
    except markup.MarkupError:
        raise TimetableError("is_a_timetable") from None
    root = walk.root
    services = [] if root is None else (root.one("Services") or _Node("", "")).each("Service")
    if root is None or len(services) != 1:
        raise TimetableError("is_a_timetable" if root is None else "holds_one_service")
    (service,) = services
    line, mode = service.said("Lines", "Line", "LineName"), service.said("Mode")
    runs = (
        _a_day(service.said("OperatingPeriod", "StartDate")),
        _a_day(service.said("OperatingPeriod", "EndDate")),
    )
    if not line or runs[0] > runs[1]:
        raise TimetableError("service_is_stated")
    of_service = _days(service)
    stops = _stops(root)
    patterns = _patterns(service, _sections(root, stops))

    journeys = (root.one("VehicleJourneys") or _Node("", "")).each("VehicleJourney")
    trips: list[Trip] = []
    for journey in journeys:
        if journey.each("Frequency"):
            raise TimetableError("no_journey_is_a_headway")
        if journey.each("VehicleJourneyRef") or _states_times(journey):
            raise TimetableError("no_journey_has_times_of_its_own")
        calls = patterns.get(journey.said("JourneyPatternRef"))
        code = journey.said("VehicleJourneyCode")
        if calls is None or not code:
            raise TimetableError("references_resolve")
        leaves = _leaves(journey)
        days = _days(journey)
        days = of_service if days is None else days
        if days is None:
            raise TimetableError("days_are_read")
        # A journey that leaves a day late is of the day before the one it leaves on.
        if not runs[0] <= day <= runs[1] or day.weekday() not in days:
            continue
        trips.append(
            Trip(
                trip_id=code,
                route_id=line,
                stops=tuple(stop for stop, _, _ in calls),
                arrives=tuple(leaves + reached for _, reached, _ in calls),
                departs=tuple(leaves + left for _, _, left in calls),
            )
        )
    trips.sort(key=lambda trip: (trip.departs[0], trip.trip_id))
    return Timetable(line, mode, runs, stops, tuple(trips), len(journeys))


@dataclass(frozen=True)
class Day:
    """Several timetables as they stand on one day: every train once, and every stop."""

    day: date
    stops: Mapping[str, Point]
    trips: tuple[Trip, ...]
    # How many journeys run on the day for each line, by the name of the line.
    running: Mapping[str, int]


def on_the_day(timetables: Sequence[Timetable], day: date) -> Day:
    """The trains of several files on one day, each counted once, or a refusal.

    Two files of one line that both run on the day are refused: one is a
    timetable for a few days of works, and the trains of both are never run.
    The day before and the day after are of no account.
    """
    stops: dict[str, Point] = {}
    trips: list[Trip] = []
    running: dict[str, int] = {}
    for timetable in sorted(timetables, key=lambda one: (one.line, one.runs)):
        stops.update(timetable.stops)
        if not timetable.trips:
            continue
        if timetable.line in running:
            raise TimetableError("one_timetable_a_line")
        running[timetable.line] = len(timetable.trips)
        trips += timetable.trips
    trips.sort(key=lambda trip: (trip.departs[0], trip.route_id, trip.trip_id))
    return Day(day, stops, tuple(trips), running)


def _files_of(archive: zipfile.ZipFile) -> Iterator[tuple[str, bytes]]:
    """The name and the bytes of each file of a zip, in the order of the names."""
    for info in sorted(archive.infolist(), key=lambda info: info.filename):
        if info.is_dir():
            continue
        if info.file_size > LARGEST:
            raise TimetableError("zip_is_read")
        yield info.filename, archive.read(info)


def timetables_in(
    source: Path, day: date, named: Callable[[str], bool]
) -> tuple[tuple[str, Timetable], ...]:
    """Each timetable of a zip whose name is asked for, as it stands on a day, by its name.

    A zip inside the zip is opened, and no deeper. A file is read where its
    name ends `.xml` and `named` says so of the name: a caller that wants one
    kind of service says which names are of that kind. Nothing is unpacked to
    a disk.
    """
    found: list[tuple[str, Timetable]] = []
    try:
        with zipfile.ZipFile(source) as outer:
            for name, content in _files_of(outer):
                if name.lower().endswith(".zip"):
                    with zipfile.ZipFile(io.BytesIO(content)) as inner:
                        found += [
                            (within, read(held, day))
                            for within, held in _files_of(inner)
                            if within.lower().endswith(".xml") and named(within)
                        ]
                elif name.lower().endswith(".xml") and named(name):
                    found.append((name, read(content, day)))
    except (zipfile.BadZipFile, zlib.error, EOFError, OSError, RuntimeError):
        raise TimetableError("zip_is_read") from None
    return tuple(sorted(found, key=lambda one: one[0]))
