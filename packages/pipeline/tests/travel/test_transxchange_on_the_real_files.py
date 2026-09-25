"""The timetables of the Underground and the DLR, read from the file as it was fetched.

Every other test of the reader runs on a made-up timetable. These read the real
one, and are skipped where the store of fetched files is not. The store is
named by BURRO_STORE_FOLDER, and the file is read through its receipt in
`data/receipts/`.

They hold counts over London, so that a file that changes is noticed. None is
said of a named station or of a named line. Each was counted on 2026-09-25,
from the file that was fetched on 2026-09-24.

Nothing is written to the store. The file is copied out of it to be read, and
nothing of it is unpacked to a disk.
"""

import re
from collections import Counter
from datetime import date
from pathlib import Path

import pytest
from burro_pipeline.evidence.receipt import How, Period
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use
from burro_pipeline.travel.transxchange import (
    Day,
    Timetable,
    TimetableError,
    on_the_day,
    timetables_in,
)

from ..derive.real_files import SKIPPED, real_inputs

pytestmark = SKIPPED
SOURCE, FILE, EDITION = "tfl-journey-planner-timetables", "f-5b3c2882ef3a", "21092026"
# The files of the Underground are named `tfl_1-`, and those of the DLR `tfl_25-`.
UNDERGROUND_AND_DLR = re.compile(r"tfl_(1|25)-")
# A day in the middle of a week that is no bank holiday, within the dates of every line.
WEDNESDAY = date(2026, 9, 23)
# A week on, three lines have a timetable for the season and one for a few days of works.
A_WEEK_ON = date(2026, 9, 30)


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def path(real: Inputs) -> Path:
    return real.open(SOURCE, Use.ROUTING, edition=EDITION).path


def of_a_train(name: str) -> bool:
    return UNDERGROUND_AND_DLR.match(name) is not None


@pytest.fixture(scope="module")
def read(path: Path) -> tuple[tuple[str, Timetable], ...]:
    return timetables_in(path, WEDNESDAY, of_a_train)


@pytest.fixture(scope="module")
def day(read: tuple[tuple[str, Timetable], ...]) -> Day:
    return on_the_day([one for _, one in read], WEDNESDAY)


def test_the_file_is_the_issue_of_21_september_2026_and_its_receipt_says_so(real: Inputs):
    receipt = real.open(SOURCE, Use.ROUTING, edition=EDITION).receipt

    assert (receipt.file_id, receipt.how) == (FILE, How.FETCHED)
    assert receipt.publisher_file == "journey-planner-timetables.zip"
    assert receipt.data_period == Period(start="2026-09-19", end="2026-12-23")


def test_it_holds_40_timetables_of_the_underground_and_the_dlr(
    read: tuple[tuple[str, Timetable], ...],
):
    assert len(read) == 40
    assert Counter(one.mode for _, one in read) == {"underground": 35, "rail": 5}
    assert len({one.line for _, one in read}) == 12
    assert sum(one.journeys for _, one in read) == 84_792


def test_one_timetable_of_each_line_runs_on_the_wednesday(
    read: tuple[tuple[str, Timetable], ...], day: Day
):
    assert sum(1 for _, one in read if one.trips) == 12
    assert len(day.running) == 12
    assert sorted(day.running.values()) == [
        233,
        257,
        531,
        617,
        756,
        831,
        872,
        1_017,
        1_046,
        1_099,
        1_573,
        1_584,
    ]
    assert len(day.trips) == 10_416


def test_the_trains_of_the_wednesday_call_at_723_platforms(day: Day):
    assert len({stop for trip in day.trips for stop in trip.stops}) == 723
    assert sum(len(trip.stops) for trip in day.trips) == 228_543
    # Every platform a train calls at is placed, and one that is placed has no train.
    assert len(day.stops) == 724


def test_every_run_of_the_wednesday_is_a_whole_number_of_minutes(day: Day):
    runs = [
        trip.arrives[place + 1] - trip.departs[place]
        for trip in day.trips
        for place in range(len(trip.stops) - 1)
    ]

    assert len(runs) == 218_127
    assert all(run >= 0 and run % 60 == 0 for run in runs)
    # A train stands where the file states a wait.
    stands = [
        left > reached
        for trip in day.trips
        for reached, left in zip(trip.arrives, trip.departs, strict=True)
    ]
    assert sum(stands) == 4_623


def test_a_day_on_which_a_line_has_two_timetables_is_refused(path: Path):
    a_week_on = [one for _, one in timetables_in(path, A_WEEK_ON, of_a_train)]

    assert sum(1 for one in a_week_on if one.trips) == 15
    with pytest.raises(TimetableError) as stopped:
        on_the_day(a_week_on, A_WEEK_ON)
    assert stopped.value.rule == "one_timetable_a_line"
