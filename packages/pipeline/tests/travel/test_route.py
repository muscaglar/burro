"""The driver: origins in shards, each routed once, and one shard routed twice."""

from collections.abc import Sequence

import pytest
from burro_pipeline.travel.engine import Fine, Point, Reached, RoutingError, Settings
from burro_pipeline.travel.route import digest, join, packed, route, same_twice, shard_of

SETTINGS = Settings(departures=10)
ORIGINS = [Point(f"syn-o{n:02d}", (n / 1000, 0.0)) for n in range(11)]
ENDS = [Point("syn-d02", (0.05, 0.0)), Point("syn-d01", (0.02, 0.0))]


class Counting:
    """An engine that answers with how often it has been asked: no two answers are the same."""

    name, version = "counting", "1"

    def __init__(self) -> None:
        self.asked = 0

    def reach(self, origin: Point, destinations: Sequence[Point], settings: Settings) -> Reached:
        self.asked += 1
        row = tuple(self.asked for _ in destinations)
        return Reached(origin.point_id, dict.fromkeys(settings.percentiles, row), row, row)


class Steady(Counting):
    """An engine that answers the same whenever it is asked: by where the origin is."""

    def reach(self, origin: Point, destinations: Sequence[Point], settings: Settings) -> Reached:
        row = tuple(round(1000 * (origin.at[0] + end.at[0])) for end in destinations)
        return Reached(origin.point_id, dict.fromkeys(settings.percentiles, row), row, row)


class Mistaken(Counting):
    def reach(self, origin: Point, destinations: Sequence[Point], settings: Settings) -> Reached:
        found = super().reach(origin, destinations, settings)
        return Reached("syn-o99", found.pt, found.cycle, found.walk)


@pytest.mark.parametrize("shards", [1, 2, 3, 4, 11, 12])
def test_every_origin_is_in_exactly_one_shard(shards: int):
    parts = [shard_of(ORIGINS[::-1], shard, shards) for shard in range(1, shards + 1)]

    assert sorted(origin.point_id for part in parts for origin in part) == [
        origin.point_id for origin in ORIGINS
    ]
    assert max(map(len, parts)) - min(map(len, parts)) <= 1


def test_a_shard_holds_the_same_origins_in_whatever_order_they_are_given():
    assert shard_of(ORIGINS, 2, 3) == shard_of(ORIGINS[::-1], 2, 3)
    assert [origin.point_id for origin in shard_of(ORIGINS, 2, 3)] == [
        "syn-o01",
        "syn-o04",
        "syn-o07",
        "syn-o10",
    ]


@pytest.mark.parametrize(("shard", "shards"), [(0, 4), (5, 4), (1, 0)])
def test_a_shard_that_is_not_one_of_the_shards_is_refused(shard: int, shards: int):
    with pytest.raises(ValueError, match="counted from 1"):
        shard_of(ORIGINS, shard, shards)


def test_an_origin_given_twice_is_refused():
    with pytest.raises(RoutingError) as stopped:
        route(Counting(), [*ORIGINS, ORIGINS[0]], ENDS, SETTINGS)

    assert stopped.value.rule == "origins_are_given_once"


def test_origins_and_destinations_are_routed_in_the_order_of_their_ids():
    found = route(Counting(), ORIGINS[::-1], ENDS, SETTINGS)

    assert found.destination_ids == ("syn-d01", "syn-d02")
    assert [one.origin_id for one in found.reached] == [origin.point_id for origin in ORIGINS]
    assert [one.walk[0] for one in found.reached] == list(range(1, 12))


def test_an_engine_that_answers_for_another_origin_is_refused():
    with pytest.raises(RoutingError) as stopped:
        route(Mistaken(), ORIGINS, ENDS, SETTINGS)

    assert stopped.value.rule == "answers_are_whole"


def test_the_shards_of_a_build_join_to_what_one_run_finds():
    engine = Steady()
    whole = route(engine, ORIGINS, ENDS, SETTINGS)

    parts = [route(engine, shard_of(ORIGINS, shard, 3), ENDS, SETTINGS) for shard in (3, 1, 2)]

    assert join(parts) == whole
    assert digest(join(parts), SETTINGS) == digest(whole, SETTINGS)


def test_an_origin_in_two_shards_is_refused():
    engine = Counting()
    first, second = (
        route(engine, ORIGINS[:6], ENDS, SETTINGS),
        route(engine, ORIGINS[5:], ENDS, SETTINGS),
    )

    with pytest.raises(RoutingError) as stopped:
        join([first, second])

    assert stopped.value.rule == "origins_are_given_once"


def test_shards_routed_to_other_destinations_are_refused():
    engine = Counting()
    first, second = (
        route(engine, ORIGINS[:6], ENDS, SETTINGS),
        route(engine, ORIGINS[6:], ENDS[:1], SETTINGS),
    )

    with pytest.raises(RoutingError) as stopped:
        join([first, second])

    assert stopped.value.rule == "answers_are_whole"


def test_an_engine_that_finds_the_same_twice_passes():
    engine = Steady()
    shard = shard_of(ORIGINS, 1, 4)

    same_twice(engine, shard, ENDS, SETTINGS, route(engine, ORIGINS, ENDS, SETTINGS))


def test_an_engine_that_finds_something_else_the_second_time_is_refused():
    engine = Counting()
    shard = shard_of(ORIGINS, 1, 4)
    first = route(engine, shard, ENDS, SETTINGS)

    with pytest.raises(RoutingError) as stopped:
        same_twice(engine, shard, ENDS, SETTINGS, first)

    assert stopped.value.rule == "same_twice"


def test_the_fine_matrices_are_one_byte_a_journey():
    row = (0, 253, None)
    fine = Fine(("a", "b", "c"), (Reached("o1", {50: row, 90: row}, row, (1, 2, 3)),))
    settings = Settings(percentiles=(50, 90))

    held = packed(fine, settings)

    assert held == bytes([0, 253, 254] * 3 + [1, 2, 3])
    assert len(digest(fine, settings)) == 64


def test_the_hash_of_the_fine_matrices_names_what_they_are_keyed_by():
    row = (1, 2)
    one = Fine(("a", "b"), (Reached("o1", {50: row, 90: row}, row, row),))
    other = Fine(("a", "c"), (Reached("o1", {50: row, 90: row}, row, row),))
    settings = Settings(percentiles=(50, 90))

    assert packed(one, settings) == packed(other, settings)
    assert digest(one, settings) != digest(other, settings)


def test_a_time_that_does_not_fit_in_a_byte_is_refused():
    row = (254,)
    fine = Fine(("a",), (Reached("o1", {50: row, 90: row}, row, row),))

    with pytest.raises(RoutingError) as stopped:
        packed(fine, Settings(percentiles=(50, 90)))

    assert stopped.value.rule == "answers_are_whole"
