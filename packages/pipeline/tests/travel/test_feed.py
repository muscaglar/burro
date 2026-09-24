"""The reader of a timetable: what it takes, and what it refuses and how it says so.

Every feed here is made up, in open sea, under names the synthetic release holds.
"""

import io
import zipfile
from collections.abc import Callable
from datetime import date
from pathlib import Path

import pytest
from burro_pipeline.travel import feed as reader
from burro_pipeline.travel.feed import MEANING, Counted, FeedError, read_feed, seconds_of

from .support import (
    CANARY,
    PELLAM,
    SATURDAY,
    SUNDAY,
    TUESDAY,
    WEXMOOR,
    Table,
    put,
    tables,
    zip_of,
)

Held = dict[str, Table]


def refused(held: Held, day: date = TUESDAY) -> FeedError:
    with pytest.raises(FeedError) as stopped:
        read_feed(zip_of(held), day)
    return stopped.value


def test_a_feed_that_keeps_every_rule_is_read_as_it_stands_on_the_day():
    found = read_feed(zip_of(tables()), TUESDAY)

    # On a weekday, 43 trips of one line and 42 of the other. On a Saturday, 15.
    assert found.counted == Counted(
        stops=4, routes=2, trips=100, running=85, calls=43 * 3 + 42 * 2, past_midnight=0
    )
    assert found.covers == (date(2026, 9, 1), date(2026, 12, 18))
    assert [trip.trip_id for trip in found.trips[:3]] == [
        "syn-r1-w001",
        "syn-r2-w001",
        "syn-r1-w002",
    ]
    first = found.trips[0]
    assert (first.stops, first.departs) == ((PELLAM, "syn-s0011", WEXMOOR), (18000, 18300, 19200))
    assert found.stops[WEXMOOR].at == (pytest.approx(5000 / 111_320, abs=1e-6), 0.0)


def test_only_the_trips_that_run_on_the_day_are_kept():
    weekday, saturday = read_feed(zip_of(tables()), TUESDAY), read_feed(zip_of(tables()), SATURDAY)

    assert {trip.route_id for trip in weekday.trips} == {"syn-r1", "syn-r2"}
    assert {trip.route_id for trip in saturday.trips} == {"syn-r1"}
    assert (weekday.counted.running, saturday.counted.running) == (85, 15)
    # What the feed holds is counted the same whatever the day.
    assert weekday.counted.trips == saturday.counted.trips == 100


def test_a_day_on_which_nothing_runs_is_refused():
    assert (refused(tables(), SUNDAY).rule, refused(tables(), SUNDAY).table) == (
        "calendar_covers_the_day",
        "trips.txt",
    )


@pytest.mark.parametrize("day", [date(2026, 8, 31), date(2026, 12, 19)])
def test_a_day_the_feed_does_not_cover_is_refused(day: date):
    assert refused(tables(), day).rule == "calendar_covers_the_day"


def test_the_feeds_own_word_on_what_it_covers_is_kept_to():
    held = tables()
    held["feed_info.txt"] = [
        ["feed_publisher_name", "feed_start_date", "feed_end_date"],
        ["Burro (made up)", "20260923", "20261218"],
    ]

    assert refused(held, TUESDAY).rule == "calendar_covers_the_day"
    assert read_feed(zip_of(held), date(2026, 9, 23)).covers[0] == date(2026, 9, 23)


def test_a_day_that_is_taken_out_or_put_in_is_read_from_the_second_calendar():
    held = tables()
    held["calendar_dates.txt"] = [
        ["service_id", "date", "exception_type"],
        ["syn-weekdays", "20260922", "2"],
        ["syn-saturdays", "20260922", "1"],
    ]

    assert read_feed(zip_of(held), TUESDAY).counted.running == 15
    assert read_feed(zip_of(held), date(2026, 9, 23)).counted.running == 85


def test_a_feed_with_the_second_calendar_alone_is_read():
    held = tables()
    del held["calendar.txt"]
    held["calendar_dates.txt"] = [
        ["service_id", "date", "exception_type"],
        ["syn-weekdays", "20260922", "1"],
        ["syn-saturdays", "20260926", "1"],
    ]

    found = read_feed(zip_of(held), TUESDAY)

    assert (found.counted.running, found.covers) == (85, (TUESDAY, SATURDAY))


def test_a_time_past_midnight_is_read_and_counted():
    held = tables()
    last = len(held["stop_times.txt"]) - 1
    put(held, "stop_times.txt", last, "arrival_time", "24:20:00")
    put(held, "stop_times.txt", last, "departure_time", "24:20:00")

    found = read_feed(zip_of(held), SATURDAY)

    assert found.counted.past_midnight == 2
    assert max(trip.arrives[-1] for trip in found.trips) == 24 * 3600 + 20 * 60


def test_a_feed_zipped_inside_a_folder_is_read():
    inside = io.BytesIO()
    with zipfile.ZipFile(zip_of(tables())) as plain, zipfile.ZipFile(inside, "w") as nested:
        for name in plain.namelist():
            nested.writestr(f"feed/{name}", plain.read(name))
    inside.seek(0)

    assert read_feed(inside, TUESDAY).counted.running == 85


def test_a_column_that_is_not_read_is_never_kept():
    """A stop's name is what a person would know a place by. The reader never takes it."""
    held = tables()
    put(held, "stops.txt", 1, "stop_name", CANARY)
    held["routes.txt"][1][1] = CANARY

    assert CANARY not in repr(read_feed(zip_of(held), TUESDAY))


def test_a_place_that_is_no_stop_needs_no_point():
    held = tables()
    held["stops.txt"][0].append("location_type")
    for row in held["stops.txt"][1:]:
        row.append("")
    held["stops.txt"].append(["syn-s9001", "Pellam Cross concourse", "", "", "3"])

    assert read_feed(zip_of(held), TUESDAY).counted.stops == 4


Broken = tuple[str, str, int | None, Callable[[Held], object]]


def _drop(table: str) -> Callable[[Held], object]:
    return lambda held: held.pop(table)


def _set(table: str, row: int, column: str, value: str) -> Callable[[Held], object]:
    return lambda held: put(held, table, row, column, value)


def _without(table: str, column: str) -> Callable[[Held], object]:
    def change(held: Held) -> None:
        at = held[table][0].index(column)
        held[table] = [[cell for n, cell in enumerate(row) if n != at] for row in held[table]]

    return change


CALLS, DAYS = "stop_times.txt", "calendar.txt"
BROKEN: list[Broken] = [
    ("feed_holds_its_tables", "stops.txt", None, _drop("stops.txt")),
    ("feed_holds_its_tables", "stop_times.txt", None, _drop(CALLS)),
    ("feed_holds_its_tables", "calendar.txt", None, _drop("calendar.txt")),
    ("table_holds_its_columns", "stops.txt", None, _without("stops.txt", "stop_lat")),
    ("table_holds_its_columns", CALLS, None, _without(CALLS, "departure_time")),
    ("table_holds_its_columns", "routes.txt", 3, _set("routes.txt", 2, "route_type", CANARY)),
    ("table_holds_its_columns", CALLS, 2, _set(CALLS, 1, "stop_sequence", CANARY)),
    ("ids_are_unique", "stops.txt", 3, _set("stops.txt", 2, "stop_id", "syn-s0007")),
    ("ids_are_unique", "routes.txt", 3, _set("routes.txt", 2, "route_id", "syn-r1")),
    ("ids_are_unique", "trips.txt", 3, _set("trips.txt", 2, "trip_id", "syn-r1-w001")),
    ("ids_are_unique", CALLS, 3, _set(CALLS, 2, "stop_sequence", "1")),
    ("stop_has_a_point", "stops.txt", 2, _set("stops.txt", 1, "stop_lat", "")),
    ("stop_has_a_point", "stops.txt", 2, _set("stops.txt", 1, "stop_lon", CANARY)),
    ("stop_has_a_point", "stops.txt", 3, _set("stops.txt", 2, "stop_lat", "91")),
    ("stop_has_a_point", "stops.txt", 3, _set("stops.txt", 2, "stop_lon", "-180.5")),
    ("stop_has_a_point", "stops.txt", 3, _set("stops.txt", 2, "stop_lat", "nan")),
    ("references_resolve", "trips.txt", 2, _set("trips.txt", 1, "route_id", CANARY)),
    ("references_resolve", "trips.txt", 2, _set("trips.txt", 1, "service_id", CANARY)),
    ("references_resolve", CALLS, 2, _set(CALLS, 1, "stop_id", CANARY)),
    ("references_resolve", CALLS, 2, _set(CALLS, 1, "trip_id", CANARY)),
    ("times_are_in_order", CALLS, 2, _set(CALLS, 1, "departure_time", "")),
    ("times_are_in_order", CALLS, 2, _set(CALLS, 1, "arrival_time", "5:00")),
    ("times_are_in_order", CALLS, 2, _set(CALLS, 1, "arrival_time", "05:60:00")),
    ("times_are_in_order", CALLS, 2, _set(CALLS, 1, "arrival_time", CANARY)),
    # It leaves before it arrives.
    ("times_are_in_order", CALLS, 3, _set(CALLS, 2, "arrival_time", "05:05:01")),
    # It arrives before it left the stop before.
    ("times_are_in_order", CALLS, 4, _set(CALLS, 3, "arrival_time", "05:04:59")),
    ("calendar_is_readable", DAYS, 2, _set(DAYS, 1, "start_date", "2026-09-01")),
    ("calendar_is_readable", DAYS, 2, _set(DAYS, 1, "end_date", "20260231")),
    ("calendar_is_readable", DAYS, 2, _set(DAYS, 1, "tuesday", "yes")),
    ("calendar_is_readable", DAYS, 3, _set(DAYS, 2, "start_date", "20270101")),
    ("no_trip_is_a_headway", "frequencies.txt", 2, lambda held: held.update({
        "frequencies.txt": [
            ["trip_id", "start_time", "end_time", "headway_secs"],
            ["syn-r1-w001", "07:00:00", "09:00:00", "600"],
        ]
    })),
]  # fmt: skip


@pytest.mark.parametrize(("rule", "table", "line", "change"), BROKEN)
def test_a_feed_that_breaks_a_rule_is_refused_by_the_name_of_the_rule(
    rule: str, table: str, line: int | None, change: Callable[[Held], object]
):
    held = tables()
    change(held)

    error = refused(held)

    assert (error.rule, error.table, error.line) == (rule, table, line)
    assert str(error).endswith(f"[{rule}]") and MEANING[rule] in str(error)


@pytest.mark.parametrize(("rule", "table", "line", "change"), BROKEN)
def test_a_refusal_never_repeats_what_the_feed_holds(
    rule: str, table: str, line: int | None, change: Callable[[Held], object]
):
    held = tables()
    change(held)

    said = str(refused(held))

    assert CANARY not in said
    assert not any(name in said for name in ("Pellam", "Tallowgate", "syn-s", "syn-r", "05:"))


def test_a_trip_that_calls_at_one_stop_or_at_none_is_refused():
    one = tables()
    one[CALLS] = [row for n, row in enumerate(one[CALLS]) if n not in (2, 3)]
    none = tables()
    none[CALLS] = [row for n, row in enumerate(none[CALLS]) if n not in (1, 2, 3)]

    assert (refused(one).rule, refused(one).table) == ("times_are_in_order", CALLS)
    assert (refused(none).rule, refused(none).table, refused(none).line) == (
        "times_are_in_order",
        "trips.txt",
        2,
    )


def test_a_table_of_headways_that_holds_no_row_is_no_headway():
    held = tables()
    held["frequencies.txt"] = [["trip_id", "start_time", "end_time", "headway_secs"]]

    assert read_feed(zip_of(held), TUESDAY).counted.running == 85


def test_a_row_that_is_short_is_refused_where_it_stands():
    held = tables()
    held[CALLS][5] = held[CALLS][5][:3]

    error = refused(held)

    assert (error.rule, error.table, error.line) == ("table_holds_its_columns", CALLS, 6)


@pytest.mark.parametrize(
    "content", [b"", b"stop_id,stop_lat\n", b"PK\x03\x04 not a zip at all", b"\xff\xfe\x00"]
)
def test_what_is_no_zip_is_refused(content: bytes):
    with pytest.raises(FeedError) as stopped:
        read_feed(io.BytesIO(content), TUESDAY)

    assert stopped.value.rule == "feed_is_a_zip"


def test_a_table_that_is_not_text_is_refused():
    held = io.BytesIO()
    with zipfile.ZipFile(zip_of(tables())) as plain, zipfile.ZipFile(held, "w") as changed:
        for name in plain.namelist():
            changed.writestr(name, b"\xff\xfe\xfa" if name == "routes.txt" else plain.read(name))
    held.seek(0)

    with pytest.raises(FeedError) as stopped:
        read_feed(held, TUESDAY)

    assert (stopped.value.rule, stopped.value.table) == ("feed_is_a_zip", "routes.txt")


def _headers_changed(held: bytes, local: int, central: int, to: Callable[[int], int]) -> bytes:
    """A zip with one byte of every table's header changed, in both places a zip keeps it."""
    changed = bytearray(held)
    for mark, place in ((b"PK\x03\x04", local), (b"PK\x01\x02", central)):
        at = changed.find(mark)
        while at >= 0:
            changed[at + place] = to(changed[at + place])
            at = changed.find(mark, at + 4)
    return bytes(changed)


def _packed_badly() -> bytes:
    """A zip whose first table was squeezed, and whose squeezed bytes were then spoiled."""
    held = io.BytesIO()
    with (
        zipfile.ZipFile(zip_of(tables())) as plain,
        zipfile.ZipFile(held, "w", zipfile.ZIP_DEFLATED) as squeezed,
    ):
        for name in plain.namelist():
            squeezed.writestr(f"{CANARY}/{name}", plain.read(name))
    spoiled = bytearray(held.getvalue())
    name_length = int.from_bytes(spoiled[26:28], "little")
    for at in range(30 + name_length, 42 + name_length):
        spoiled[at] ^= 0xFF
    return bytes(spoiled)


def _in_a_folder_named_for_a_value() -> bytes:
    held = io.BytesIO()
    with zipfile.ZipFile(zip_of(tables())) as plain, zipfile.ZipFile(held, "w") as nested:
        for name in plain.namelist():
            nested.writestr(f"{CANARY}/{name}", plain.read(name))
    return held.getvalue()


CANNOT_BE_UNPACKED = {
    "its bytes are spoiled": _packed_badly,
    "it is locked with a password": lambda: _headers_changed(
        _in_a_folder_named_for_a_value(), 6, 8, lambda byte: byte | 1
    ),
    "it is packed in a way that is not known": lambda: _headers_changed(
        _in_a_folder_named_for_a_value(), 8, 10, lambda _: 99
    ),
}


@pytest.mark.parametrize("why", sorted(CANNOT_BE_UNPACKED))
def test_a_table_that_cannot_be_unpacked_is_refused_in_one_line(why: str):
    """Python says each of these in words of its own, and one of them names the file."""
    with pytest.raises(FeedError) as stopped:
        read_feed(io.BytesIO(CANNOT_BE_UNPACKED[why]()), TUESDAY)

    said = str(stopped.value)
    assert stopped.value.rule == "feed_is_a_zip"
    assert stopped.value.table in reader.COLUMNS
    assert "\n" not in said and CANARY not in said
    # Nothing of what Python said is carried behind the refusal, where a trace would show it.
    assert stopped.value.__cause__ is None and stopped.value.__suppress_context__


@pytest.mark.parametrize(
    ("text", "seconds"),
    [
        ("00:00:00", 0),
        ("7:05:09", 25509),
        ("07:05:09", 25509),
        ("24:00:00", 86400),
        ("27:59:59", 100799),
        ("7:5:9", None),
        ("07:05", None),
        ("07:05:60", None),
        ("-7:05:00", None),
        ("07:05:00 ", None),
        # Digits of another script, which Python would read as numbers.
        ("\u0660\u0667:\u0660\u0665:\u0660\u0660", None),
        ("", None),
    ],
)
def test_a_time_is_hours_minutes_and_seconds_and_may_pass_midnight(text: str, seconds: int | None):
    assert seconds_of(text) == seconds


def test_every_rule_has_its_words_and_the_module_says_every_rule():
    said = reader.__doc__ or ""

    assert all(f"`{rule}`" in said for rule in MEANING)
    assert {rule for rule, *_ in BROKEN} | {"feed_is_a_zip", "calendar_covers_the_day"} == set(
        MEANING
    )


def test_a_feed_in_a_file_is_read_and_the_file_is_let_go(tmp_path: Path):
    held = tmp_path / "feed.zip"
    held.write_bytes(zip_of(tables()).getvalue())

    found = read_feed(held, TUESDAY)
    held.unlink()

    assert found.counted.running == 85
    assert not held.exists()
