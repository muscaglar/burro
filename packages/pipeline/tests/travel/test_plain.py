"""The plain router, which is for tests: what it finds in a town small enough to check by hand.

The town is in `support.py`. Every journey here is worked out in the comment beside it.
"""

import ast
import random
from dataclasses import replace
from pathlib import Path

import burro_pipeline.travel
import pytest
from burro_pipeline.travel import plain
from burro_pipeline.travel.engine import Point, Reached, RoutingError, Settings
from burro_pipeline.travel.plain import PlainRouter, Streets, minutes_of, seconds_at

from .streets_support import point, streets
from .support import CORACLE, PELLAM, feed

# Every departure minute from 07:00 to 08:59, and the whole of the window kept.
WHOLE = Settings(percentiles=(50, 90, 100))
AT_PELLAM = point("syn-o-pellam", 0)
AT_KINDLEWHARF = point("syn-o-kindlewharf", 0, -1000)
AT_WEXMOOR = point("syn-d-wexmoor", 5000)
AT_TALLOWGATE = point("syn-d-tallowgate", 2000)


def reach(
    origin: Point = AT_PELLAM,
    end: Point = AT_WEXMOOR,
    settings: Settings = WHOLE,
    every: int = 600,
    birch_ends_at: str = PELLAM,
) -> Reached:
    town = feed(every, birch_ends_at=birch_ends_at)
    return PlainRouter(town, streets()).reach(origin, [end], settings)


def by_pt(found: Reached) -> tuple[int | None, ...]:
    return tuple(found.pt[percent][0] for percent in sorted(found.pt))


def test_the_first_line_of_the_module_says_it_is_for_tests():
    assert (plain.__doc__ or "").startswith("For tests only: a plain, slow router")
    assert (PlainRouter.__doc__ or "").startswith("For tests only")


def test_nothing_that_builds_a_real_release_imports_it():
    """It routes the made-up town. Only the town and the step that drives the town may name it."""
    source = Path(burro_pipeline.travel.__file__).parents[1]
    naming = set[str]()
    for module in sorted(source.rglob("*.py")):
        for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
            named = node.module if isinstance(node, ast.ImportFrom) else None
            if named == "burro_pipeline.travel.plain":
                naming.add(module.relative_to(source).as_posix())

    assert naming <= {"travel/cli.py", "travel/made_up.py"}


def test_the_design_s_own_example_is_found_as_the_design_says():
    """One service every 10 minutes and a ride of 20.

    A person must be at the stop a minute before a train leaves. Whoever
    leaves the door on the hour waits 10 minutes, and whoever leaves a minute
    before a train waits 1. So the 120 times are 21 to 30, each 12 times over.
    """
    assert by_pt(reach()) == (25, 29, 30)


def test_with_no_slack_a_person_boards_the_train_that_leaves_as_they_arrive():
    assert by_pt(reach(settings=replace(WHOLE, board_slack=0))) == (24, 28, 29)


def test_a_train_every_half_hour_is_what_the_window_holds():
    # The waits are 1 to 30 minutes, each 4 times over, and the ride is 20.
    assert by_pt(reach(every=1800)) == (35, 47, 50)


def test_a_journey_with_a_change_waits_twice():
    """From Kindlewharf to Wexmoor: the Birch line, then the Amber line.

    The Birch line leaves at 3 minutes past and is at Pellam Cross at 7 past.
    The Amber line leaves there on the 10 and is at Wexmoor on the 30. Whoever
    leaves the door at 2 minutes past takes 28 minutes, and whoever leaves at
    3 past has missed it and takes 37. So the times are 28 to 37.
    """
    far = replace(WHOLE, longest_walk=500)

    assert by_pt(reach(AT_KINDLEWHARF, settings=far)) == (32, 36, 37)


def test_a_journey_of_two_rides_is_not_found_with_a_limit_of_one():
    # What is left is to walk all the way: 6,000 metres at 4.8 km/h is 75 minutes.
    one_ride = replace(WHOLE, longest_walk=500, most_rides=1)

    assert by_pt(reach(AT_KINDLEWHARF, settings=one_ride)) == (75, 75, 75)


def test_a_walk_to_a_further_stop_is_taken_where_it_is_faster():
    """With one ride and a walk of 1,000 metres allowed, the way is on foot to Pellam Cross.

    The walk is 12 and a half minutes, so the train a person boards leaves 13
    and a half minutes or more after they do. The times are 34 to 43.
    """
    one_ride = replace(WHOLE, longest_walk=1000, most_rides=1)

    assert by_pt(reach(AT_KINDLEWHARF, settings=one_ride)) == (38, 42, 43)


def test_a_change_on_foot_is_made_within_the_longest_change():
    """The Birch line ends at Coracle Row, 300 metres from where the Amber line leaves.

    It is there at 7 past. The walk is 3 minutes and 45 seconds, so the train
    on the 10 has gone and the next is boarded, on the 20. From Kindlewharf
    that is 38 to 47 minutes.
    """
    far = replace(WHOLE, longest_walk=500)

    found = reach(AT_KINDLEWHARF, settings=far, birch_ends_at=CORACLE)
    too_far = reach(
        AT_KINDLEWHARF, settings=replace(far, longest_change=299), birch_ends_at=CORACLE
    )

    assert by_pt(found) == (42, 46, 47)
    # With no change the Birch line leads nowhere, and what is left is to walk all the way.
    assert by_pt(too_far) == (75, 75, 75)


def test_no_stop_beyond_the_longest_walk_is_walked_to():
    door = point("syn-o-door", 600)
    # Pellam Cross is 600 metres back, and Tallowgate 1,400 on.
    near, far = replace(WHOLE, longest_walk=599), replace(WHOLE, longest_walk=600)

    # On foot all the way: 4,400 metres is 55 minutes.
    assert by_pt(reach(door, settings=near)) == (55, 55, 55)
    # Back to Pellam Cross in 7 and a half minutes, and on from there.
    assert by_pt(reach(door, settings=far)) == (33, 37, 38)


def test_the_walk_is_taken_where_it_is_faster_than_any_train():
    # 300 metres is 3 minutes and 45 seconds on foot, which is written as 4.
    assert by_pt(reach(end=point("syn-d-near", 300))) == (4, 4, 4)


def test_a_journey_longer_than_the_cutoff_is_not_a_time():
    # The times from Kindlewharf are 28 to 37.
    found = reach(AT_KINDLEWHARF, settings=replace(WHOLE, longest_walk=500, cutoff_pt=33))

    assert by_pt(found) == (32, None, None)


def test_by_bike_and_on_foot_the_time_is_the_length_of_the_streets():
    found = PlainRouter(feed(), streets()).reach(
        AT_KINDLEWHARF, [AT_PELLAM, AT_TALLOWGATE, AT_WEXMOOR], WHOLE
    )

    # 1,000, 3,000 and 6,000 metres: round the corner, never as the crow flies.
    assert found.walk == (13, 38, None)
    assert found.cycle == (4, 12, 24)


def test_a_time_is_rounded_up_to_the_whole_minute():
    assert [seconds_at(metres, 4800) for metres in (0, 1, 80, 81, 4800)] == [0, 1, 60, 61, 3600]
    assert [minutes_of(seconds) for seconds in (0, 1, 60, 61, 2400, 2401)] == [0, 1, 1, 2, 40, 41]


def test_a_point_is_put_on_the_street_by_a_straight_line_and_the_walk_is_counted():
    # 150 metres north of the street, at Pellam Cross: 150 to the street and 300 along it.
    found = reach(point("syn-o-north", 0, 150), point("syn-d-near", 300))

    assert found.walk == (6,)


@pytest.mark.parametrize(
    ("origin", "end", "rule"),
    [
        (point("syn-o-far", 0, 201), AT_WEXMOOR, "origin_is_on_a_street"),
        (AT_PELLAM, point("syn-d-far", 5201), "destination_is_on_a_street"),
    ],
)
def test_a_point_too_far_from_any_street_stops_the_build(origin: Point, end: Point, rule: str):
    with pytest.raises(RoutingError) as stopped:
        reach(origin, end)

    assert stopped.value.rule == rule


def test_a_stop_too_far_from_any_street_stops_the_build():
    lane = streets()
    street_alone = Streets(
        {node: at for node, at in lane.nodes.items() if "-e" in node},
        tuple(link for link in lane.links if "-s" not in link[0] + link[1]),
    )

    with pytest.raises(RoutingError) as stopped:
        PlainRouter(feed(), street_alone)

    assert stopped.value.rule == "stop_is_on_a_street"


def test_a_place_the_streets_do_not_lead_to_is_reached_by_train_alone():
    lane = streets()
    # The street is cut between Tallowgate and Wexmoor.
    cut = Streets(lane.nodes, tuple(link for link in lane.links if link[0] != "syn-k-e03000"))

    found = PlainRouter(feed(), cut).reach(AT_PELLAM, [AT_WEXMOOR], WHOLE)

    assert (found.walk, found.cycle, by_pt(found)) == ((None,), (None,), (25, 29, 30))


@pytest.mark.parametrize("start", [4 * 3600, 13 * 3600])
def test_a_window_in_which_no_trip_leaves_is_refused(start: int):
    with pytest.raises(RoutingError) as stopped:
        reach(settings=replace(WHOLE, window_start=start, departures=30))

    assert stopped.value.rule == "window_is_in_the_timetable"


def test_the_same_town_gives_the_same_answer_in_whatever_order_it_is_given():
    lane, timetable = streets(), feed()
    shuffled = list(lane.links)
    random.Random(7).shuffle(shuffled)  # noqa: S311
    turned = [(b, a, metres) for a, b, metres in shuffled]
    ends = [AT_WEXMOOR, AT_TALLOWGATE, AT_PELLAM]

    first = PlainRouter(timetable, lane).reach(AT_KINDLEWHARF, ends, WHOLE)
    second = PlainRouter(timetable, Streets(lane.nodes, tuple(turned))).reach(
        AT_KINDLEWHARF, ends, WHOLE
    )

    assert first == second
