"""The driver: every origin routed once, in shards, and one shard routed twice.

An engine answers for one origin at a time. A build has thousands, so they are
split into shards that run side by side, each on a machine of its own, and
joined. What a shard holds is decided by the ids of the origins alone, so that
the same build splits the same way wherever it runs.

One shard is routed twice in every build and the two answers are compared, as
the travel design asks (section 12, "the same twice"). An engine that draws
anything at random is found there, before a release is made from it.
"""

import hashlib
from collections.abc import Sequence

from burro_pipeline.travel.engine import (
    MOST_MINUTES,
    Engine,
    Fine,
    Point,
    Reached,
    RoutingError,
    Settings,
)

# What a cell of the fine matrices holds in place of minutes: no journey within the cutoff.
BEYOND = 254


def shard_of(origins: Sequence[Point], shard: int, shards: int) -> tuple[Point, ...]:
    """The origins of one shard, counted from 1. Every origin is in exactly one.

    Origins are dealt out in the order of their ids, one to each shard in
    turn, so that each shard holds origins from every part of the map.
    """
    if not 1 <= shard <= shards:
        raise ValueError("a shard is counted from 1 up to the number of shards")
    ordered = _in_order(origins)
    return ordered[shard - 1 :: shards]


def _in_order(origins: Sequence[Point]) -> tuple[Point, ...]:
    ordered = tuple(sorted(origins, key=lambda origin: origin.point_id))
    if len({origin.point_id for origin in ordered}) != len(ordered):
        raise RoutingError("origins_are_given_once")
    return ordered


def route(
    engine: Engine, origins: Sequence[Point], destinations: Sequence[Point], settings: Settings
) -> Fine:
    """Every origin given, routed to every destination, in the order of their ids."""
    ends = tuple(sorted(destinations, key=lambda end: end.point_id))
    reached: list[Reached] = []
    for origin in _in_order(origins):
        found = engine.reach(origin, ends, settings)
        if found.origin_id != origin.point_id or set(found.pt) != set(settings.percentiles):
            raise RoutingError("answers_are_whole")
        reached.append(found)
    return Fine(tuple(end.point_id for end in ends), tuple(reached))


def join(parts: Sequence[Fine]) -> Fine:
    """The shards of a build as one. An origin in two shards is refused."""
    ends = {part.destination_ids for part in parts}
    if len(ends) != 1:
        raise RoutingError("answers_are_whole")
    reached = sorted((one for part in parts for one in part.reached), key=lambda r: r.origin_id)
    return Fine(ends.pop(), tuple(reached))


def packed(fine: Fine, settings: Settings) -> bytes:
    """The fine matrices as the build store keeps them: one byte a cell.

    For each percentile that is kept, then by bike, then on foot: for each
    origin in the order of their ids, a byte for each destination in the
    order of theirs. 0 to 253 is minutes, and 254 is no journey within the
    cutoff.
    """

    def cells(row: Sequence[int | None]) -> bytes:
        if any(cell is not None and not 0 <= cell <= MOST_MINUTES for cell in row):
            raise RoutingError("answers_are_whole")
        return bytes(BEYOND if cell is None else cell for cell in row)

    matrices = [
        *([one.pt[percent] for one in fine.reached] for percent in settings.percentiles),
        [one.cycle for one in fine.reached],
        [one.walk for one in fine.reached],
    ]
    return b"".join(cells(row) for matrix in matrices for row in matrix)


def digest(fine: Fine, settings: Settings) -> str:
    """The hash of the fine matrices with the ids they are keyed by."""
    keyed = "\n".join(
        [*fine.destination_ids, "", *(one.origin_id for one in fine.reached), ""]
    ).encode()
    return hashlib.sha256(keyed + packed(fine, settings)).hexdigest()


def same_twice(
    engine: Engine,
    origins: Sequence[Point],
    destinations: Sequence[Point],
    settings: Settings,
    first: Fine,
) -> None:
    """Route the first shard again and hold it to what was found the first time."""
    again = route(engine, origins, destinations, settings)
    known = {one.origin_id: one for one in first.reached}
    if again.destination_ids != first.destination_ids or any(
        known.get(one.origin_id) != one for one in again.reached
    ):
        raise RoutingError("same_twice")
