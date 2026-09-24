"""The roll-up from home points to areas, and the journeys as a release holds them."""

import random

import pytest
from burro_core.release import TravelTable
from burro_pipeline.travel.engine import Fine, Point, Reached, RoutingError, Settings
from burro_pipeline.travel.roll_up import Home, table_of, weighted_lower_median

ENDS = ("syn-d0001", "syn-d0002", "syn-d0003")
SETTINGS = Settings()
Times = tuple[int | None, ...]


def home(point_id: str, area_id: str, weight: int) -> Home:
    return Home(Point(point_id, (0.0, 0.0)), area_id, weight)


def reached(origin_id: str, typical: Times, missed: Times | None = None) -> Reached:
    kept = {percent: typical for percent in SETTINGS.percentiles}
    kept[SETTINGS.just_missed] = typical if missed is None else missed
    return Reached(origin_id, kept, cycle=typical, walk=typical)


def table(found: list[Reached], homes: list[Home], areas: list[str]) -> TravelTable:
    fine = Fine(ENDS, tuple(sorted(found, key=lambda one: one.origin_id)))
    return table_of(fine, homes, areas, SETTINGS, ["synthetic"], "2026-09-22")


@pytest.mark.parametrize(
    ("times", "median"),
    [
        # One home point is the whole of its area.
        ([(30, 100)], 30),
        # Half of the homes are 20 minutes away or less, so 20 it is: the lower of the two.
        ([(20, 50), (40, 50)], 20),
        ([(40, 50), (20, 50)], 20),
        ([(20, 49), (40, 51)], 40),
        ([(10, 100), (20, 300), (90, 200)], 20),
        ([(10, 100), (20, 100), (90, 300)], 90),
        # It is never a time between two: three points of one weight give the middle one.
        ([(11, 1), (35, 1), (12, 1)], 12),
        # Beyond the cutoff counts as longer than any time.
        ([(None, 60), (25, 40)], None),
        ([(None, 40), (25, 60)], 25),
        ([(None, 50), (25, 50)], 25),
        ([(None, 1), (None, 1)], None),
    ],
)
def test_the_time_of_an_area_is_the_weighted_lower_median_of_its_home_points(
    times: list[tuple[int | None, int]], median: int | None
):
    assert weighted_lower_median(times) == median


@pytest.mark.parametrize("times", [[], [(20, 0)], [(20, 10), (30, -1)]])
def test_a_home_point_with_no_weight_stops_the_build(times: list[tuple[int | None, int]]):
    with pytest.raises(RoutingError) as stopped:
        weighted_lower_median(times)

    assert stopped.value.rule == "homes_have_a_weight"


def test_the_table_is_as_a_release_holds_journeys():
    found = [
        reached("a-1", (10, 50, None), (12, 55, None)),
        reached("a-2", (30, 40, None), (33, None, None)),
        reached("b-1", (0, 1, 120), (1, 3, 120)),
    ]
    homes = [
        home("a-1", "syn-n0001", 100),
        home("a-2", "syn-n0001", 300),
        home("b-1", "syn-n0002", 5),
    ]

    made = table(found, homes, ["syn-n0002", "syn-n0001"])

    assert (made.area_ids, made.destination_ids) == (("syn-n0001", "syn-n0002"), ENDS)
    assert (made.source_ids, made.as_of) == (("synthetic",), "2026-09-22")
    assert made.cutoff_minutes.model_dump() == {"pt": 120, "cycle": 60, "walk": 60}
    # The second home point holds three homes in four of the first area.
    assert made.pt_typical == ((30, 40, -1), (2, 2, 120))
    # Where the typical time is inside the cutoff and the just-missed time is not, it is -1.
    assert made.pt_just_missed == ((33, -1, -1), (2, 3, 120))
    assert made.walk == made.cycle == made.pt_typical


def test_no_time_is_under_the_floor():
    found = [reached("a-1", (0, 1, 2))]

    made = table(found, [home("a-1", "syn-n0001", 1)], ["syn-n0001"])

    assert made.pt_typical == ((2, 2, 2),)


def test_just_missed_is_never_shorter_than_typical_in_any_area():
    draw = random.Random(11)  # noqa: S311
    homes = [home(f"h-{n:03d}", f"syn-n{n % 7:04d}", draw.randint(1, 900)) for n in range(40)]
    found: list[Reached] = []
    for one in homes:
        typical = tuple(draw.choice([None, *range(0, 121, 7)]) for _ in ENDS)
        missed = tuple(
            None if time is None else draw.choice([None, time, time + 5]) for time in typical
        )
        found.append(reached(one.point.point_id, typical, missed))

    made = table(found, homes, sorted({one.area_id for one in homes}))

    pairs = [
        (typical or 0, missed or 0)
        for row, other in zip(made.pt_typical, made.pt_just_missed, strict=True)
        for typical, missed in zip(row, other, strict=True)
    ]
    assert None not in (*sum(made.pt_typical, ()), *sum(made.pt_just_missed, ()))
    assert all(missed == -1 or 0 <= typical <= missed for typical, missed in pairs)
    assert any(missed == -1 and typical != -1 for typical, missed in pairs)


def test_the_order_the_home_points_are_given_in_changes_nothing():
    found = [reached(f"h-{n}", (n, 60 - n, None if n % 2 else n)) for n in range(9)]
    homes = [home(f"h-{n}", f"syn-n000{n % 3}", 10 + n) for n in range(9)]
    areas = ["syn-n0000", "syn-n0001", "syn-n0002"]

    assert table(found, homes, areas) == table(found[::-1], homes[::-1], areas[::-1])


def test_an_area_with_no_home_point_stops_the_build():
    with pytest.raises(RoutingError) as stopped:
        table(
            [reached("a-1", (1, 2, 3))], [home("a-1", "syn-n0001", 1)], ["syn-n0001", "syn-n0002"]
        )

    assert stopped.value.rule == "homes_have_a_weight"


def test_a_home_point_that_was_not_routed_stops_the_build():
    homes = [home("a-1", "syn-n0001", 1), home("a-2", "syn-n0001", 1)]

    with pytest.raises(RoutingError) as stopped:
        table([reached("a-1", (1, 2, 3))], homes, ["syn-n0001"])

    assert stopped.value.rule == "origins_are_given_once"


def test_a_home_point_of_an_area_the_build_does_not_hold_stops_the_build():
    with pytest.raises(RoutingError) as stopped:
        table([reached("a-1", (1, 2, 3))], [home("a-1", "syn-n0009", 1)], ["syn-n0001"])

    assert stopped.value.rule == "origins_are_given_once"


def test_an_origin_that_is_no_home_point_stops_the_build():
    found = [reached("a-1", (1, 2, 3)), reached("a-2", (1, 2, 3))]

    with pytest.raises(RoutingError) as stopped:
        table(found, [home("a-1", "syn-n0001", 1)], ["syn-n0001"])

    assert stopped.value.rule == "homes_have_a_weight"
