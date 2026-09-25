"""The reader of a timetable in TransXChange: what it takes, what it refuses and how it says so.

Every timetable here is made up, under names the synthetic release holds.
`timetable_support.py` writes it: one line, one way, three trains of a morning.
"""

import io
import zipfile
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
from burro_pipeline.travel import transxchange
from burro_pipeline.travel.feed import DAY_SECONDS
from burro_pipeline.travel.transxchange import (
    MEANING,
    TimetableError,
    on_the_day,
    read,
    seconds_of,
    timetables_in,
)

from .support import CANARY, KINDLEWHARF, PELLAM, SATURDAY, TALLOWGATE, TUESDAY, WEXMOOR, hours
from .timetable_support import AMBER, MORNING, Journey, Link, Written, where

WEDNESDAY = date(2026, 9, 23)


def refused(written: Written, day: date = TUESDAY) -> TimetableError:
    with pytest.raises(TimetableError) as stopped:
        read(written.file(), day)
    return stopped.value


# What is read


def test_a_timetable_is_read_as_it_stands_on_the_day():
    found = read(Written().file(), TUESDAY)

    assert (found.line, found.mode) == ("Amber line", "underground")
    assert found.runs == (date(2026, 9, 1), date(2026, 12, 18))
    assert (found.journeys, len(found.trips)) == (3, 3)
    assert [trip.trip_id for trip in found.trips] == ["VJ1", "VJ2", "VJ3"]
    assert {trip.route_id for trip in found.trips} == {"Amber line"}
    # A stop is where the file puts it, in metres on the grid, whether or not a train calls.
    assert found.stops == {stop: where(stop) for stop in (PELLAM, TALLOWGATE, WEXMOOR, KINDLEWHARF)}


def test_the_time_of_a_call_is_every_run_and_every_wait_before_it():
    """It leaves at 07:00, is at Tallowgate 5 minutes on, stands a minute, and runs 15 more."""
    first = read(Written().file(), TUESDAY).trips[0]

    assert first.stops == (PELLAM, TALLOWGATE, WEXMOOR)
    assert first.arrives == (hours(7), hours(7, 5), hours(7, 21))
    assert first.departs == (hours(7), hours(7, 6), hours(7, 21))


def test_a_wait_may_be_stated_at_either_end_of_a_stretch():
    """A minute as the first stretch ends, and half a minute as the second begins."""
    links = (AMBER[0], replace(AMBER[1], wait_at_start="PT30S", wait_at_end="PT2M"))

    first = read(Written(patterns={"JP1": links}).file(), TUESDAY).trips[0]

    assert first.arrives == (hours(7), hours(7, 5), hours(7, 21, 30))
    assert first.departs == (hours(7), hours(7, 6, 30), hours(7, 23, 30))


def test_a_stop_a_train_passes_is_no_call_and_the_time_to_pass_it_is_kept():
    passing = (
        replace(AMBER[0], at_end="pass", wait_at_end=""),
        replace(AMBER[1], at_start="pass"),
    )

    first = read(Written(patterns={"JP1": passing}).file(), TUESDAY).trips[0]

    assert first.stops == (PELLAM, WEXMOOR)
    assert first.arrives == (hours(7), hours(7, 20))


@pytest.mark.parametrize(
    ("written", "seconds"),
    [("PT2M", 120), ("PT30S", 30), ("PT1M48S", 108), ("PT0S", 0), ("PT1H2M3S", 3723)],
)
def test_a_length_of_time_is_read_as_the_file_writes_it(written: str, seconds: int):
    assert seconds_of(written) == seconds


# The days a journey runs on


def test_a_journey_runs_on_the_days_it_states_and_on_its_service_s_where_it_states_none():
    journeys = (
        Journey("VJ1", "07:00:00"),
        Journey("VJ2", "07:10:00", days="<Saturday/><Sunday/>"),
        Journey("VJ3", "07:20:00", days="<Tuesday/><Wednesday/>"),
        Journey("VJ4", "07:30:00", days="<MondayToSunday/>"),
    )
    written = Written(journeys=journeys).file()

    def running(day: date) -> list[str]:
        return [trip.trip_id for trip in read(written, day).trips]

    assert running(TUESDAY) == ["VJ1", "VJ3", "VJ4"]
    assert running(SATURDAY) == ["VJ2", "VJ4"]
    assert running(date(2026, 9, 24)) == ["VJ1", "VJ4"]


def test_no_journey_runs_before_the_file_begins_or_after_it_ends():
    written = Written(runs=("2026-09-23", "2026-09-24")).file()

    assert not read(written, TUESDAY).trips
    assert len(read(written, WEDNESDAY).trips) == 3
    assert not read(written, date(2026, 9, 25)).trips
    # A file that runs on another day is no refusal: it holds its journeys all the same.
    assert read(written, TUESDAY).journeys == 3


def test_a_journey_that_first_leaves_a_day_late_is_timed_past_the_end_of_the_day():
    late = Journey("VJ9", "00:10:00", more="<DepartureDayShift>1</DepartureDayShift>")

    found = read(Written(journeys=(*MORNING, late)).file(), TUESDAY)

    assert found.trips[-1].trip_id == "VJ9"
    assert found.trips[-1].departs[0] == DAY_SECONDS + 600


# What is not read


def test_no_name_is_read_of_a_stop_or_of_where_a_journey_is_bound():
    """The made-up file writes one word wherever a name stands, and the word is found nowhere."""
    written = Written().file()
    found = read(written, TUESDAY)

    assert CANARY.encode() in written
    assert CANARY not in repr(found)


def test_what_a_journey_states_of_bank_holidays_is_passed_over():
    """It runs on a Tuesday, whatever it says of the bank holidays it does not run on."""
    stated = (
        "<RegularDayType><DaysOfWeek><Tuesday/></DaysOfWeek></RegularDayType>"
        "<BankHolidayOperation><DaysOfNonOperation><AllBankHolidays/>"
        "</DaysOfNonOperation></BankHolidayOperation>"
    )
    written = Written(journeys=(Journey("VJ1", "07:00:00", profile=stated),)).file()

    assert len(read(written, TUESDAY).trips) == 1
    assert not read(written, WEDNESDAY).trips


def test_a_journey_that_runs_on_holidays_alone_runs_on_no_day_of_a_week():
    stated = "<RegularDayType><HolidaysOnly/></RegularDayType>"
    written = Written(journeys=(Journey("VJ1", "07:00:00", profile=stated),)).file()

    assert not read(written, TUESDAY).trips and not read(written, SATURDAY).trips


# The refusals


BROKEN = {
    "is_a_timetable": Written(root="TransNothing"),
    "holds_one_service": Written(after_the_service="<Service/>"),
    "service_is_stated": Written(line=""),
    "stop_has_a_point": Written(stops=("", TALLOWGATE, WEXMOOR)),
    "days_are_read": Written(days="<Someday/>"),
    "times_are_read": Written(journeys=(Journey("VJ1", "7 o'clock"),)),
    "references_resolve": Written(journeys=(Journey("VJ1", "07:00:00", pattern="JP9"),)),
    "journey_has_a_pattern": Written(patterns={"JP1": (replace(AMBER[0], at_end="pass"),)}),
    "no_journey_is_a_headway": Written(
        journeys=(Journey("VJ1", "07:00:00", more="<Frequency><Interval/></Frequency>"),)
    ),
    "no_journey_has_times_of_its_own": Written(
        journeys=(
            Journey(
                "VJ1",
                "07:00:00",
                more="<VehicleJourneyTimingLink><RunTime>PT9M</RunTime></VehicleJourneyTimingLink>",
            ),
        )
    ),
    "no_day_is_special": Written(
        journeys=(
            Journey(
                "VJ1",
                "07:00:00",
                profile="<RegularDayType><DaysOfWeek><Tuesday/></DaysOfWeek></RegularDayType>"
                "<SpecialDaysOperation><DaysOfNonOperation/></SpecialDaysOperation>",
            ),
        )
    ),
}


@pytest.mark.parametrize("rule", sorted(BROKEN))
def test_a_timetable_that_breaks_a_rule_is_refused_under_the_name_of_the_rule(rule: str):
    stopped = refused(BROKEN[rule])

    assert stopped.rule == rule
    assert str(stopped) == f"the timetable {MEANING[rule]} [{rule}]"


def test_every_rule_has_a_timetable_that_breaks_it():
    assert set(BROKEN) | {"one_timetable_a_line", "zip_is_read"} == set(MEANING)


@pytest.mark.parametrize(
    "written",
    [
        Written(line=CANARY, days="<Someday/>"),
        Written(stops=(CANARY + " x", TALLOWGATE, WEXMOOR)),
        Written(journeys=(Journey(CANARY, CANARY),)),
        Written(journeys=(Journey("VJ1", "07:00:00", pattern=CANARY),)),
        Written(patterns={"JP1": (replace(AMBER[0], run=CANARY),)}),
    ],
)
def test_a_refusal_repeats_nothing_from_the_file(written: Written):
    assert CANARY not in str(refused(written))


@pytest.mark.parametrize(
    "before",
    ['<!DOCTYPE TransXChange [<!ENTITY more "more">]>', "<!DOCTYPE TransXChange>"],
)
def test_a_file_that_declares_a_document_type_is_not_read(before: str):
    assert refused(Written(before=before)).rule == "is_a_timetable"


def test_what_is_no_xml_is_refused():
    for content in (b"", b"stop_id,stop_lat", b"<TransXChange><Services>"):
        with pytest.raises(TimetableError) as stopped:
            read(content, TUESDAY)
        assert stopped.value.rule == "is_a_timetable"


def test_a_journey_with_links_of_its_own_that_state_no_time_is_read():
    """The publisher gives such links where only what a train shows as its end changes."""
    shown = "<VehicleJourneyTimingLink><From/><To/></VehicleJourneyTimingLink>"

    found = read(Written(journeys=(Journey("VJ1", "07:00:00", more=shown),)).file(), TUESDAY)

    assert found.trips[0].arrives == (hours(7), hours(7, 5), hours(7, 21))


# Several files on one day


def birch() -> Written:
    return Written(
        line="Birch line",
        patterns={"JP1": (Link(KINDLEWHARF, PELLAM, "PT4M"),)},
        journeys=(Journey("VJ7", "07:03:00"),),
    )


def test_the_trains_of_several_files_are_put_in_the_order_they_first_leave():
    found = on_the_day([read(one.file(), TUESDAY) for one in (birch(), Written())], TUESDAY)

    assert [trip.trip_id for trip in found.trips] == ["VJ1", "VJ7", "VJ2", "VJ3"]
    assert found.running == {"Amber line": 3, "Birch line": 1}
    assert set(found.stops) == {PELLAM, TALLOWGATE, WEXMOOR, KINDLEWHARF}


def test_two_files_of_one_line_that_both_run_on_the_day_are_refused():
    """A timetable for the season and one for two days of works: both hold the Wednesday."""
    season, works = Written(), Written(runs=("2026-09-23", "2026-09-24"))

    def joined(day: date) -> int:
        return len(on_the_day([read(one.file(), day) for one in (season, works)], day).trips)

    assert joined(TUESDAY) == 3
    with pytest.raises(TimetableError) as stopped:
        joined(WEDNESDAY)
    assert stopped.value.rule == "one_timetable_a_line"


# A publisher's zip of zips


def zipped(held: dict[str, bytes]) -> bytes:
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w") as archive:
        for name, content in held.items():
            archive.writestr(name, content)
    return packed.getvalue()


def a_zip_of_zips(folder: Path) -> Path:
    """Two lines in one zip and a line of buses in another, as the publisher packs them."""
    path = folder / "timetables.zip"
    trains = {"tfl_1-AMB.xml": Written().file(), "tfl_1-BIR.xml": birch().file()}
    buses = {"tfl_9-BUS.xml": Written(line="Bus 9", mode="bus").file(), "read me.txt": b"x"}
    path.write_bytes(zipped({"TRAINS.zip": zipped(trains), "BUSES.zip": zipped(buses)}))
    return path


def test_the_timetables_of_a_zip_of_zips_are_read_where_their_names_are_asked_for(
    tmp_path: Path,
):
    path = a_zip_of_zips(tmp_path)

    every = timetables_in(path, TUESDAY, lambda name: True)
    trains = timetables_in(path, TUESDAY, lambda name: name.startswith("tfl_1-"))

    assert [(name, one.line) for name, one in every] == [
        ("tfl_1-AMB.xml", "Amber line"),
        ("tfl_1-BIR.xml", "Birch line"),
        ("tfl_9-BUS.xml", "Bus 9"),
    ]
    assert [name for name, _ in trains] == ["tfl_1-AMB.xml", "tfl_1-BIR.xml"]
    assert len(on_the_day([one for _, one in trains], TUESDAY).trips) == 4
    # Nothing was unpacked beside the zip.
    assert sorted(found.name for found in tmp_path.iterdir()) == ["timetables.zip"]


def test_a_zip_that_cannot_be_read_or_unpacks_to_too_much_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    broken = tmp_path / "broken.zip"
    broken.write_bytes(b"no zip at all")
    inside = tmp_path / "inside.zip"
    inside.write_bytes(zipped({"TRAINS.zip": b"no zip at all"}))
    for path in (broken, inside, tmp_path / "nowhere.zip"):
        with pytest.raises(TimetableError) as stopped:
            timetables_in(path, TUESDAY, lambda name: True)
        assert stopped.value.rule == "zip_is_read"

    monkeypatch.setattr(transxchange, "LARGEST", 100)
    with pytest.raises(TimetableError) as stopped:
        timetables_in(a_zip_of_zips(tmp_path), TUESDAY, lambda name: True)
    assert stopped.value.rule == "zip_is_read"


def test_a_timetable_of_a_zip_that_breaks_a_rule_is_refused_under_the_rule(tmp_path: Path):
    path = tmp_path / "timetables.zip"
    path.write_bytes(zipped({"TRAINS.zip": zipped({"tfl_1-AMB.xml": b"<Nothing/>"})}))

    with pytest.raises(TimetableError) as stopped:
        timetables_in(path, TUESDAY, lambda name: True)
    assert stopped.value.rule == "is_a_timetable"
