"""From home points to areas: the roll-up, and the journeys as a release holds them.

An engine routes from points where homes are, several to an area. A release
holds one time for an area. The time of an area is the weighted lower median
of the times of its home points (the travel design, section 7): put the home
points in order of their times, shortest first, and take the time of the
first at which half of the area's weight or more has been counted. It is
always a time that some home point has, so nothing is rounded or averaged.

| Rule | Detail |
|---|---|
| Beyond the cutoff | Counts as longer than any time. If the median lands there, the cell is `-1` |
| Not computed | Never written here. A home point with no answer stops the build |
| The floor | A time under the floor is written as the floor |
| Just missed | Never shorter than typical: both are medians of the same home points |

A weight is a whole number, a count of homes, so that no sum is a fraction and
the order a file is in changes nothing.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_core.release import BEYOND_CUTOFF_CELL, Cutoffs, TravelTable

from burro_pipeline.travel.engine import Fine, Point, Reached, RoutingError, Settings

Cell = int | None


@dataclass(frozen=True)
class Home:
    """A point that stands for some of the homes of one area, and how many."""

    point: Point
    area_id: str
    weight: int


def weighted_lower_median(times: Sequence[tuple[int | None, int]]) -> int | None:
    """The time of the first home point at which half of the weight or more is counted.

    Each is a time and a weight. A time of `None` is beyond the cutoff, and
    counts as longer than any other.
    """
    whole = sum(weight for _, weight in times)
    if not times or any(weight < 1 for _, weight in times):
        raise RoutingError("homes_have_a_weight")
    counted = 0
    for time, weight in sorted(times, key=lambda pair: (pair[0] is None, pair[0] or 0)):
        counted += weight
        if 2 * counted >= whole:
            return time
    raise AssertionError("half of a weight is reached before its whole")


def _cell(time: int | None, floor: int) -> int:
    return BEYOND_CUTOFF_CELL if time is None else max(time, floor)


def table_of(
    fine: Fine,
    homes: Sequence[Home],
    area_ids: Sequence[str],
    settings: Settings,
    source_ids: Sequence[str],
    as_of: str,
) -> TravelTable:
    """The journeys of a release: a time for every area and every destination.

    Every area must have a home point, and every home point an answer. One
    that has none stops the build: a release never holds a time that was not
    worked out from every home point of its area.
    """
    reached: Mapping[str, Reached] = {one.origin_id: one for one in fine.reached}
    by_area: dict[str, list[Home]] = {area_id: [] for area_id in area_ids}
    for home in sorted(homes, key=lambda home: home.point.point_id):
        if home.area_id not in by_area or home.point.point_id not in reached:
            raise RoutingError("origins_are_given_once")
        by_area[home.area_id].append(home)
    if len(homes) != len(reached) or not all(by_area.values()):
        raise RoutingError("homes_have_a_weight")

    def matrix(of: str, percent: int = 0) -> tuple[tuple[Cell, ...], ...]:
        def times(home: Home) -> tuple[int | None, ...]:
            one = reached[home.point.point_id]
            return one.pt[percent] if of == "pt" else one.cycle if of == "cycle" else one.walk

        return tuple(
            tuple(
                _cell(
                    weighted_lower_median(
                        [(times(home)[place], home.weight) for home in by_area[area_id]]
                    ),
                    settings.floor,
                )
                for place in range(len(fine.destination_ids))
            )
            for area_id in sorted(area_ids)
        )

    return TravelTable(
        source_ids=tuple(sorted(source_ids)),
        as_of=as_of,
        area_ids=tuple(sorted(area_ids)),
        destination_ids=fine.destination_ids,
        cutoff_minutes=Cutoffs(
            pt=settings.cutoff_pt, cycle=settings.cutoff_cycle, walk=settings.cutoff_walk
        ),
        pt_typical=matrix("pt", settings.typical),
        pt_just_missed=matrix("pt", settings.just_missed),
        cycle=matrix("cycle"),
        walk=matrix("walk"),
    )
