"""A journey timed from a timetable, in a town small enough to check by hand.

The town is in `support.py`, and every name in it is made up. Every journey here
is worked out in the words beside it. A person must be at the place by each
minute from 08:00 to 09:30, which is 91 minutes, and the journey of the window
is the 46th of them, shortest first.
"""

from dataclasses import replace
from datetime import date

import pytest
from burro_pipeline.travel.timed import NEVER, Assumed, Timed, Trains
from burro_pipeline.travel.transxchange import on_the_day, read

from .support import CORACLE, KINDLEWHARF, PELLAM, TALLOWGATE, TUESDAY, WEXMOOR, WHERE, feed, hours
from .timetable_support import Journey, Written, where

Point = tuple[float, float]
# Nothing but the timetable: a straight walk, no way in or out of a station, and a walk of
# no more than 500 metres, so that a person boards where they stand.
BARE = Assumed(detour=1.0, in_and_out=0, change=120, same_platform=60, longest_walk=500)
POINTS = {stop: (float(east), float(north)) for stop, (east, north) in WHERE.items()}
AT_PELLAM, AT_TALLOWGATE, AT_WEXMOOR = POINTS[PELLAM], POINTS[TALLOWGATE], POINTS[WEXMOOR]
AT_KINDLEWHARF = POINTS[KINDLEWHARF]


def trains(assumed: Assumed = BARE, every: int = 600, birch_ends_at: str = PELLAM) -> Trains:
    return Trains(feed(every, birch_ends_at=birch_ends_at).trips, POINTS, assumed)


def timed(
    home: Point = AT_PELLAM,
    place: Point = AT_WEXMOOR,
    assumed: Assumed = BARE,
    every: int = 600,
    birch_ends_at: str = PELLAM,
) -> Timed:
    return trains(assumed, every, birch_ends_at).to(place).timed_from(home)


# The wait


def test_a_train_every_ten_minutes_and_a_ride_of_twenty():
    """A train is at Wexmoor on every tenth minute, 20 minutes after it left Pellam Cross.

    Whoever must be there on a tenth minute rides 20 minutes and is there as
    the minute strikes. Whoever must be there a minute before the next train
    took the last one, and is 9 minutes early: 29. The tenth minute falls 10
    times in the window and every other 9 times, so the 46th is 24.
    """
    assert timed() == Timed(24, rides=1)


def test_a_train_every_half_hour_is_what_the_window_holds():
    """A train is at Wexmoor at 20 and at 50 past. The journeys are 20 to 49 minutes.

    From 08:00 to 08:19 they are 30 to 49, from 08:20 to 09:19 they are 20 to
    49 twice over, and from 09:20 to 09:30 they are 20 to 30. 46 of the 91 are
    34 or less.
    """
    assert timed(every=1800) == Timed(34, rides=1)


def test_no_wait_is_assumed_so_the_wait_is_half_the_time_between_trains():
    """The journey of the window is the ride and about half the time between two trains."""
    ride = 20
    assert [timed(every=every).minutes for every in (300, 600, 1200, 1800)] == [
        ride + 2,
        ride + 4,
        ride + 9,
        ride + 14,
    ]


# The walk


def test_the_way_between_a_street_and_a_platform_is_counted_at_each_end():
    """A minute in and a minute out. A train must be at Wexmoor a minute before the time.

    So whoever must be there a minute past a tenth minute rides the train
    that is there on it: a minute in, 20 on the train and a minute out, 22.
    Whoever must be there on a tenth minute took the train before: 31. The
    46th is 27.
    """
    assert timed(assumed=replace(BARE, in_and_out=60)) == Timed(27, rides=1)


def test_a_walk_to_a_platform_is_a_straight_line_at_the_speed_assumed():
    """The door is 600 metres from Pellam Cross, which is 7 and a half minutes at 4.8 km/h.

    The journeys are 27 and a half minutes to 36 and a half. The 46th is 31
    and a half, and a journey is said in whole minutes, rounded up.
    """
    door = (600.0, 0.0)

    assert timed(door, assumed=replace(BARE, longest_walk=600)) == Timed(32, rides=1)


def test_a_walk_is_made_longer_by_the_detour():
    """At 1.3 the 600 metres are 780, which is 9 minutes and 45 seconds: 33 and three quarters."""
    door, assumed = (600.0, 0.0), replace(BARE, longest_walk=600, detour=1.3)

    assert assumed.walk(600) == 585
    assert timed(door, assumed=assumed) == Timed(34, rides=1)


def test_a_walk_is_rounded_up_to_a_whole_second():
    assert [Assumed().walk(metres) for metres in (0, 1, 80, 1000)] == [0, 1, 78, 975]


def test_no_platform_beyond_the_longest_walk_is_walked_to():
    door = (600.0, 0.0)

    # Pellam Cross is 600 metres back, and nothing else is nearer than 1,400.
    assert timed(door, assumed=replace(BARE, longest_walk=599)) == Timed(None)
    assert trains(replace(BARE, longest_walk=600)).within_a_walk(door) == {1: 450}


def test_a_person_walks_all_the_way_where_that_lets_them_leave_later():
    """The door is 300 metres short of Wexmoor: 3 minutes and 45 seconds, said as 4."""
    assert timed((4700.0, 0.0)) == Timed(4, rides=0)


def test_a_train_is_taken_where_it_is_quicker_than_the_walk():
    """To Tallowgate, 2,000 metres on: 25 minutes on foot, and 5 by a train every 10 minutes.

    The journeys by train are 5 to 14 minutes, and the 46th is 10.
    """
    far = replace(BARE, longest_walk=2400)

    assert timed(place=AT_TALLOWGATE, assumed=far) == Timed(10, rides=1)
    # With a train every hour most minutes of the window are quicker on foot.
    assert timed(place=AT_TALLOWGATE, assumed=far, every=3600) == Timed(25, rides=0)


# The change


def test_a_change_at_one_platform_takes_what_is_assumed_of_one():
    """From Kindlewharf: the Birch line is at Pellam Cross at 7 past, and the Amber line
    leaves on the 10.

    With a minute to change the train on the 10 is made: from 3 past to 30
    past is 27 minutes, and the 46th is 31. With 4 minutes it is missed, and
    the next leaves on the 20: 37 minutes, and the 46th is 41.
    """
    assert timed(AT_KINDLEWHARF) == Timed(31, rides=2)
    assert timed(AT_KINDLEWHARF, assumed=replace(BARE, same_platform=240)) == Timed(41, rides=2)


def test_a_change_between_two_platforms_is_the_change_and_the_walk_between_them():
    """The Birch line ends at Coracle Row, 300 metres from where the Amber line leaves.

    The change is 2 minutes and the walk 3 minutes and 45 seconds. The train
    is there at 7 past, so the Amber line on the 10 has gone and the one on
    the 20 is boarded: 37 minutes, and the 46th is 41.
    """
    assert timed(AT_KINDLEWHARF, birch_ends_at=CORACLE) == Timed(41, rides=2)
    # With no time to change, the walk alone is made in time for the train on the 10.
    quick = replace(BARE, change=0, walk_speed=9000)
    assert timed(AT_KINDLEWHARF, assumed=quick, birch_ends_at=CORACLE) == Timed(31, rides=2)


def test_no_change_is_made_beyond_the_longest_change():
    too_far = replace(BARE, longest_change=299)

    # The Birch line then leads nowhere, and Wexmoor is too far to walk to.
    assert timed(AT_KINDLEWHARF, assumed=too_far, birch_ends_at=CORACLE) == Timed(None)


# The last train that helps


def test_the_train_to_board_at_each_platform_is_the_last_that_is_there_in_time():
    """To be at Wexmoor by 08:30: the Amber line on the 10, and the Birch line at 3 past."""
    found = trains()
    board, rides = found.to(AT_WEXMOOR).boarded[30]

    at = dict(zip(found.stops, zip(board, rides, strict=True), strict=True))
    assert at == {
        KINDLEWHARF: (hours(8, 3), 2),
        PELLAM: (hours(8, 10), 1),
        TALLOWGATE: (hours(8, 15), 1),
        # No train leaves Wexmoor: the line ends there.
        WEXMOOR: (NEVER, 0),
    }


def test_a_journey_longer_than_the_cutoff_is_no_journey():
    """The journeys are 20 to 29 minutes. With 25 allowed, 55 minutes of the 91 have one."""
    assert timed(assumed=replace(BARE, cutoff=25 * 60)) == Timed(24, rides=1)
    # With 22 allowed, 28 minutes have one: fewer than the 46 that the journey is read at.
    assert timed(assumed=replace(BARE, cutoff=22 * 60)) == Timed(None)


def test_a_place_no_train_reaches_is_not_timed():
    # The Birch line runs to Pellam Cross and never from it.
    assert timed(AT_PELLAM, AT_KINDLEWHARF) == Timed(None)


# What is assumed


def test_the_numbers_a_journey_is_timed_with_are_named_in_one_place():
    assumed = Assumed()

    assert (assumed.walk_speed, assumed.detour) == (4800, 1.3)
    assert (assumed.in_and_out, assumed.change, assumed.same_platform) == (120, 240, 60)
    assert (assumed.longest_walk, assumed.longest_change) == (2400, 800)
    assert (assumed.first, assumed.last) == (hours(8), hours(9, 30))
    assert (assumed.typical, assumed.cutoff) == (50, 120 * 60)
    assert len(assumed.minutes) == 91
    assert (assumed.minutes[0], assumed.minutes[1], assumed.minutes[-1]) == (
        hours(8),
        hours(8, 1),
        hours(9, 30),
    )


@pytest.mark.parametrize(
    "broken",
    [
        {"walk_speed": 0},
        {"detour": 0.9},
        {"typical": 0},
        {"in_and_out": -1},
        {"change": -1},
        {"longest_walk": -1},
        {"first": hours(8) + 1},
        {"first": hours(10)},
        {"cutoff": 0},
    ],
)
def test_a_number_that_means_nothing_is_refused(broken: dict[str, int | float]):
    with pytest.raises(ValueError, match="a "):
        replace(BARE, **broken)  # type: ignore[arg-type]


def test_a_train_that_calls_where_no_point_is_known_is_refused():
    with pytest.raises(ValueError, match="has a point"):
        Trains(feed().trips, {PELLAM: AT_PELLAM}, BARE)


def test_the_same_trains_give_the_same_time():
    assert all(timed(AT_KINDLEWHARF) == timed(AT_KINDLEWHARF) for _ in range(3))


# From a timetable to a time


def test_a_timetable_in_transxchange_is_timed_as_it_is_read():
    """The Amber line as its publisher would write it: 21 minutes to Wexmoor, every 10.

    It is at Wexmoor a minute past every tenth minute. The journeys are 21 to
    30 minutes, and the 46th is 26.
    """
    day = date(2026, 9, 22)
    assert day == TUESDAY
    every_ten = tuple(
        Journey(f"VJ{count:03d}", f"{minute // 60:02d}:{minute % 60:02d}:00")
        for count, minute in enumerate(range(6 * 60, 10 * 60, 10))
    )
    found = on_the_day([read(Written(journeys=every_ten).file(), day)], day)

    reaching = Trains(found.trips, found.stops, BARE).to(where(WEXMOOR))

    assert reaching.timed_from(where(PELLAM)) == Timed(26, rides=1)
    # From Tallowgate the ride is 15 minutes: the journeys are 15 to 24, and the 46th is 20.
    assert reaching.timed_from(where(TALLOWGATE)) == Timed(20, rides=1)
