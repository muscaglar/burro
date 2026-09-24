"""A timetable in the open format that transit feeds use (GTFS), checked as it is read.

The step that works journeys out is handed a feed for one day. It is a zip of
tables, each a file of comma-separated rows under a row of column names. The
reader takes the tables a journey needs and the columns it names, and no
other: a stop's name is never read, so none can be printed.

It asks more of a feed than the format does. Every call of every trip has its
own times, and no trip is given as "every N minutes". A feed that Burro's own
converters wrote is so, and an engine that is handed one has nothing to draw
at random.

What is checked, each under the name of its rule:

- `feed_is_a_zip`: the file is a zip, and each table in it is text.
- `feed_holds_its_tables`: stops, routes, trips and stop times are there, and
  one of the two calendars.
- `table_holds_its_columns`: a table holds every column that is read, and no
  row is short.
- `ids_are_unique`: no stop, route or trip is given twice, and no trip calls
  twice at one place in its order.
- `stop_has_a_point`: every stop has a latitude and a longitude, each a number
  on the globe.
- `references_resolve`: a trip names a route and a service that are there, and
  a call names a trip and a stop that are.
- `times_are_in_order`: every call has its times, as hours, minutes and
  seconds. No call leaves before it arrives, no trip goes back in time, and
  every trip calls at two stops or more.
- `calendar_is_readable`: a day is a date, a weekday is 0 or 1, and an
  exception is 1 or 2.
- `calendar_covers_the_day`: the day asked for is within the days the feed
  says it covers, and a trip runs on it.
- `no_trip_is_a_headway`: the table of headways holds no row.

A refusal names the table, the line and the rule. It never repeats a value
from the feed. Lines are counted as an editor counts them: the column names
are line 1.

Standard library only.
"""

import csv
import io
import zipfile
import zlib
from collections.abc import Iterator, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from datetime import date
from itertools import pairwise
from pathlib import Path, PurePosixPath
from typing import IO, BinaryIO

STOPS, ROUTES, TRIPS, STOP_TIMES = "stops.txt", "routes.txt", "trips.txt", "stop_times.txt"
CALENDAR, CALENDAR_DATES = "calendar.txt", "calendar_dates.txt"
FREQUENCIES, FEED_INFO = "frequencies.txt", "feed_info.txt"
NEEDED = (STOPS, ROUTES, TRIPS, STOP_TIMES)

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
COLUMNS: Mapping[str, tuple[str, ...]] = {
    STOPS: ("stop_id", "stop_lat", "stop_lon"),
    ROUTES: ("route_id", "route_type"),
    TRIPS: ("route_id", "service_id", "trip_id"),
    STOP_TIMES: ("trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"),
    CALENDAR: ("service_id", *WEEKDAYS, "start_date", "end_date"),
    CALENDAR_DATES: ("service_id", "date", "exception_type"),
}
# A place that is no stop: a node inside a station, or where to stand on a platform. The
# format asks no point of either, and no trip calls at one.
NOT_A_STOP = frozenset({"3", "4"})
ADDED, REMOVED = "1", "2"
DAY_SECONDS = 24 * 60 * 60

MEANING: Mapping[str, str] = {
    "feed_is_a_zip": "is not a zip of tables that can be read as text",
    "feed_holds_its_tables": "is a table the feed must hold, and does not",
    "table_holds_its_columns": "lacks a column that is read, or holds a row that is short",
    "ids_are_unique": "gives an id twice",
    "stop_has_a_point": "holds a stop with no point on the globe",
    "references_resolve": "names something the feed does not hold",
    "times_are_in_order": "holds a trip whose times are missing, unreadable or out of order",
    "calendar_is_readable": "holds a day, a weekday or an exception that cannot be read",
    "calendar_covers_the_day": "does not cover the day asked for",
    "no_trip_is_a_headway": "gives a trip as a headway, and not by its own times",
}

Lonlat = tuple[float, float]


class FeedError(Exception):
    """The feed may not be routed on. Names a table, a line and a rule, and never a value."""

    def __init__(self, rule: str, table: str, line: int | None = None) -> None:
        self.rule, self.table, self.line = rule, table, line
        where = table if line is None else f"{table}, line {line}"
        super().__init__(f"{where} {MEANING[rule]} [{rule}]")


@dataclass(frozen=True)
class Stop:
    stop_id: str
    at: Lonlat


@dataclass(frozen=True)
class Trip:
    """One run of a vehicle: where it calls, in order, and when. Times are seconds of the day.

    A time may be past the end of the day: a trip that starts before midnight
    and ends after it keeps counting.
    """

    trip_id: str
    route_id: str
    stops: tuple[str, ...]
    arrives: tuple[int, ...]
    departs: tuple[int, ...]


@dataclass(frozen=True)
class Counted:
    """What a feed holds, in numbers that anyone may read."""

    stops: int
    routes: int
    trips: int
    # The trips that run on the day asked for, and the calls they make.
    running: int
    calls: int
    # Calls at a time past the end of the day.
    past_midnight: int


@dataclass(frozen=True)
class Feed:
    """A feed that passed every check, as it stands on one day."""

    day: date
    # The first and the last day the feed says it covers.
    covers: tuple[date, date]
    stops: Mapping[str, Stop]
    # The kind of vehicle of each route, as the format numbers them.
    routes: Mapping[str, int]
    # The trips that run on the day, by the time each first leaves and then by id.
    trips: tuple[Trip, ...]
    counted: Counted


class _Tables:
    """The tables of a feed, read a row at a time."""

    def __init__(self, source: Path | BinaryIO) -> None:
        try:
            self._zip = zipfile.ZipFile(source)
        except (zipfile.BadZipFile, OSError):
            raise FeedError("feed_is_a_zip", "the feed") from None
        # A feed may be zipped inside a folder. A table is known by the end of its name.
        self._names = {PurePosixPath(name).name: name for name in sorted(self._zip.namelist())}

    def close(self) -> None:
        self._zip.close()

    def holds(self, table: str) -> bool:
        return table in self._names

    def _open(self, table: str) -> IO[bytes]:
        try:
            return self._zip.open(self._names[table])
        except RuntimeError:
            # Locked with a password, or packed in a way that is not known. Python says
            # either in words that name the file, so they are not passed on.
            raise FeedError("feed_is_a_zip", table) from None

    def rows(
        self, table: str, columns: Sequence[str], optional: Sequence[str] = ()
    ) -> Iterator[tuple[int, dict[str, str]]]:
        """Each row of a table with its line, holding the columns that are read and no other."""
        try:
            with self._open(table) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
                reader = csv.DictReader(text)
                names = set(reader.fieldnames or ())
                if not set(columns) <= names:
                    raise FeedError("table_holds_its_columns", table)
                read = (*columns, *(name for name in optional if name in names))
                for row in reader:
                    if any(row[name] is None for name in read):
                        raise FeedError("table_holds_its_columns", table, reader.line_num)
                    yield reader.line_num, {name: row[name] for name in read}
        except (zipfile.BadZipFile, zlib.error, EOFError, OSError, UnicodeDecodeError, csv.Error):
            raise FeedError("feed_is_a_zip", table) from None


def seconds_of(text: str) -> int | None:
    """A time of the feed as seconds of the day, or none if it is not hours, minutes and seconds."""
    parts = text.split(":")
    if len(parts) != 3 or not all(part.isascii() and part.isdigit() for part in parts):
        return None
    hours, minutes, seconds = parts
    if not (1 <= len(hours) <= 3 and len(minutes) == 2 and len(seconds) == 2):
        return None
    if int(minutes) > 59 or int(seconds) > 59:
        return None
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def _day(text: str) -> date | None:
    if len(text) != 8 or not (text.isascii() and text.isdigit()):
        return None
    try:
        return date(int(text[:4]), int(text[4:6]), int(text[6:]))
    except ValueError:
        return None


def _number(text: str, most: float) -> float | None:
    try:
        value = float(text)
    except ValueError:
        return None
    # `nan` and `inf` are numbers to Python and points to nobody.
    return value if -most <= value <= most else None


def _stops(tables: _Tables) -> dict[str, Stop]:
    found: dict[str, Stop] = {}
    for line, row in tables.rows(STOPS, COLUMNS[STOPS], optional=("location_type",)):
        stop_id = row["stop_id"]
        if not stop_id or stop_id in found:
            raise FeedError("ids_are_unique", STOPS, line)
        lat, lon = _number(row["stop_lat"], 90.0), _number(row["stop_lon"], 180.0)
        if lat is None or lon is None:
            if row.get("location_type", "") in NOT_A_STOP and not (
                row["stop_lat"] or row["stop_lon"]
            ):
                continue
            raise FeedError("stop_has_a_point", STOPS, line)
        found[stop_id] = Stop(stop_id, (lon, lat))
    return found


def _routes(tables: _Tables) -> dict[str, int]:
    found: dict[str, int] = {}
    for line, row in tables.rows(ROUTES, COLUMNS[ROUTES]):
        route_id, kind = row["route_id"], row["route_type"]
        if not route_id or route_id in found:
            raise FeedError("ids_are_unique", ROUTES, line)
        if not (kind.isascii() and kind.isdigit() and len(kind) <= 4):
            raise FeedError("table_holds_its_columns", ROUTES, line)
        found[route_id] = int(kind)
    return found


@dataclass(frozen=True)
class _Calendar:
    """Which services run on the day asked for, and the days the feed covers."""

    known: frozenset[str]
    running: frozenset[str]
    covers: tuple[date, date]


def _calendar(tables: _Tables, day: date) -> _Calendar:
    known: set[str] = set()
    running: set[str] = set()
    days: list[date] = []
    if tables.holds(CALENDAR):
        for line, row in tables.rows(CALENDAR, COLUMNS[CALENDAR]):
            first, last = _day(row["start_date"]), _day(row["end_date"])
            flags = [row[weekday] for weekday in WEEKDAYS]
            if first is None or last is None or first > last:
                raise FeedError("calendar_is_readable", CALENDAR, line)
            if not row["service_id"] or any(flag not in ("0", "1") for flag in flags):
                raise FeedError("calendar_is_readable", CALENDAR, line)
            if row["service_id"] in known:
                raise FeedError("ids_are_unique", CALENDAR, line)
            known.add(row["service_id"])
            days += [first, last]
            if first <= day <= last and flags[day.weekday()] == "1":
                running.add(row["service_id"])
    if tables.holds(CALENDAR_DATES):
        added: set[str] = set()
        removed: set[str] = set()
        for line, row in tables.rows(CALENDAR_DATES, COLUMNS[CALENDAR_DATES]):
            when, kind = _day(row["date"]), row["exception_type"]
            if when is None or not row["service_id"] or kind not in (ADDED, REMOVED):
                raise FeedError("calendar_is_readable", CALENDAR_DATES, line)
            known.add(row["service_id"])
            days.append(when)
            if when == day:
                (added if kind == ADDED else removed).add(row["service_id"])
        running = (running | added) - removed
    if not days:
        raise FeedError("calendar_covers_the_day", _calendar_of(tables))
    return _Calendar(frozenset(known), frozenset(running), (min(days), max(days)))


def _calendar_of(tables: _Tables) -> str:
    """The table that says when services run, to name in a refusal."""
    return CALENDAR if tables.holds(CALENDAR) else CALENDAR_DATES


def _said_to_cover(tables: _Tables, covers: tuple[date, date]) -> tuple[date, date]:
    """The days the feed says it covers: its own word where it gives one, and the calendar's."""
    if not tables.holds(FEED_INFO):
        return covers
    first, last = covers
    for line, row in tables.rows(FEED_INFO, (), optional=("feed_start_date", "feed_end_date")):
        for name, text in sorted(row.items()):
            if not text:
                continue
            when = _day(text)
            if when is None:
                raise FeedError("calendar_is_readable", FEED_INFO, line)
            first = max(first, when) if name == "feed_start_date" else first
            last = min(last, when) if name == "feed_end_date" else last
    return first, last


def _trips(
    tables: _Tables, routes: Mapping[str, int], calendar: _Calendar
) -> tuple[dict[str, int], dict[str, str]]:
    """The line of every trip in its table, and the route of each that runs on the day."""
    every: dict[str, int] = {}
    running: dict[str, str] = {}
    for line, row in tables.rows(TRIPS, COLUMNS[TRIPS]):
        trip_id = row["trip_id"]
        if not trip_id or trip_id in every:
            raise FeedError("ids_are_unique", TRIPS, line)
        every[trip_id] = line
        if row["route_id"] not in routes or row["service_id"] not in calendar.known:
            raise FeedError("references_resolve", TRIPS, line)
        if row["service_id"] in calendar.running:
            running[trip_id] = row["route_id"]
    return every, running


_Call = tuple[int, int, int, str, int]  # order, arrives, departs, stop, line


def _calls(
    tables: _Tables, stops: Mapping[str, Stop], trips: Mapping[str, int]
) -> dict[str, list[_Call]]:
    found: dict[str, list[_Call]] = {}
    for line, row in tables.rows(STOP_TIMES, COLUMNS[STOP_TIMES]):
        if row["stop_id"] not in stops or row["trip_id"] not in trips:
            raise FeedError("references_resolve", STOP_TIMES, line)
        order = row["stop_sequence"]
        if not (order.isascii() and order.isdigit() and len(order) <= 9):
            raise FeedError("table_holds_its_columns", STOP_TIMES, line)
        arrives, departs = seconds_of(row["arrival_time"]), seconds_of(row["departure_time"])
        if arrives is None or departs is None or departs < arrives:
            raise FeedError("times_are_in_order", STOP_TIMES, line)
        found.setdefault(row["trip_id"], []).append(
            (int(order), arrives, departs, row["stop_id"], line)
        )
    return found


def _in_order(calls: list[_Call]) -> list[_Call]:
    """The calls of one trip in their order, once they are seen to go forward in time."""
    calls.sort()
    if len(calls) < 2:
        raise FeedError("times_are_in_order", STOP_TIMES, calls[0][4])
    for before, after in pairwise(calls):
        if before[0] == after[0]:
            raise FeedError("ids_are_unique", STOP_TIMES, after[4])
        if after[1] < before[2]:
            raise FeedError("times_are_in_order", STOP_TIMES, after[4])
    return calls


def read_feed(source: Path | BinaryIO, day: date) -> Feed:
    """The feed in a zip, as it stands on one day, or a refusal.

    Every trip of the feed is checked, whether or not it runs on the day.
    Only the trips that run on the day are kept.
    """
    with closing(_Tables(source)) as tables:
        return _read(tables, day)


def _read(tables: _Tables, day: date) -> Feed:
    for table in NEEDED:
        if not tables.holds(table):
            raise FeedError("feed_holds_its_tables", table)
    if not (tables.holds(CALENDAR) or tables.holds(CALENDAR_DATES)):
        raise FeedError("feed_holds_its_tables", CALENDAR)
    if tables.holds(FREQUENCIES):
        for line, _ in tables.rows(FREQUENCIES, ()):
            raise FeedError("no_trip_is_a_headway", FREQUENCIES, line)

    stops, routes = _stops(tables), _routes(tables)
    calendar = _calendar(tables, day)
    covers = _said_to_cover(tables, calendar.covers)
    if not covers[0] <= day <= covers[1]:
        raise FeedError("calendar_covers_the_day", _calendar_of(tables))
    every, running = _trips(tables, routes, calendar)
    calls = _calls(tables, stops, every)
    for trip_id, line in sorted(every.items()):
        if trip_id not in calls:
            # A trip that calls nowhere. It is refused as one that calls at one stop is.
            raise FeedError("times_are_in_order", TRIPS, line)

    trips: list[Trip] = []
    for trip_id in sorted(calls):
        ordered = _in_order(calls[trip_id])
        if trip_id in running:
            trips.append(
                Trip(
                    trip_id=trip_id,
                    route_id=running[trip_id],
                    stops=tuple(call[3] for call in ordered),
                    arrives=tuple(call[1] for call in ordered),
                    departs=tuple(call[2] for call in ordered),
                )
            )
    if not trips:
        raise FeedError("calendar_covers_the_day", TRIPS)
    trips.sort(key=lambda trip: (trip.departs[0], trip.trip_id))
    return Feed(
        day=day,
        covers=covers,
        stops=stops,
        routes=routes,
        trips=tuple(trips),
        counted=Counted(
            stops=len(stops),
            routes=len(routes),
            trips=len(every),
            running=len(trips),
            calls=sum(len(trip.stops) for trip in trips),
            past_midnight=sum(
                time >= DAY_SECONDS for trip in trips for time in (*trip.arrives, *trip.departs)
            ),
        ),
    )
