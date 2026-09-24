"""Does a figure of culture say something, or only how central an area is.

A first look at the file of places found that a count of one kind of place
stands in almost the order of a count of everything the file holds. A figure
like that says how much is about, and so how central an area is, and says
little of culture. This module asks it of each figure of culture, so that a
person can see which figure to put forward.

Each figure is held against three things, across the areas that have all of
them, by the rank correlation of Spearman:

| Against | What it is | From |
|---|---|---|
| How built up an area is | Homes per hectare | The measure of homes |
| How central it is | How far its homes are from the middle | The centres |
| How much is about | Every record within the same reach | The file of places |

The middle of London's homes is the mean of the centres of its output areas,
each weighed by its homes. No file names a centre of London, and none is
taken from memory.

**What is put forward.** A figure follows the centre where its order is the
order of how much is about, or of the distance from the middle, at 0.9 or
more, by either sign. Where the count follows the centre and the rate does
not, the rate is what is put forward. In every other case nothing is put
forward, and a person decides. 0.9 is a choice and not a finding, and it is
the founder's to change: no decision of record states it.

**What the real file gave.** On the part of release 2026-09-23.0 the count
stands in the order of how much is about at 0.86, and of the distance from
the middle at -0.82. The rate stands at 0.69 and -0.66. So the count is
mostly a map of the centre and does not reach 0.9, the rule puts nothing
forward, and a person decides. `test_culture_on_the_real_files.py` holds the
numbers.

The check reads no file. It is handed the figures of a build. What it prints
is lines of numbers: no name of an area, and no figure of one.
"""

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive.culture_reach import Ground, Point, figures, metres_between
from burro_pipeline.derive.culture_venues import (
    EVERY,
    KEY,
    KEY_OF_THE_KINDS,
    KEY_OF_THE_RATE,
    Culture,
)
from burro_pipeline.derive.methods import Worked

# A figure follows the centre where a rank correlation is this or more, by either sign.
FOLLOWS = 0.9
# Below this many areas no correlation is given.
FEWEST = 3
A_LINE = re.compile(r"check=culture( [a-z_]+=[a-z0-9_.-]+)+")


def ranks(values: Sequence[float]) -> list[float]:
    """The place of each value in their order, from 1. Values that tie share the middle place."""
    order = sorted(range(len(values)), key=lambda n: values[n])
    found = [0.0] * len(values)
    at = 0
    while at < len(order):
        end = at
        while end + 1 < len(order) and values[order[end + 1]] == values[order[at]]:
            end += 1
        for n in order[at : end + 1]:
            found[n] = (at + end) / 2 + 1
        at = end + 1
    return found


def rank_correlation(one: Sequence[float], other: Sequence[float]) -> float | None:
    """How nearly two lists stand in one order, from -1 to 1. None where it cannot be said.

    It is the correlation of the ranks, which counts a tie as the ranks have
    it. It cannot be said of fewer than three pairs, or where one list holds
    one value throughout.
    """
    if len(one) != len(other):
        raise ValueError("two lists are compared that hold as many values as each other")
    if len(one) < FEWEST:
        return None
    first, second = ranks(one), ranks(other)
    mean = (len(one) + 1) / 2
    above = math.fsum((a - mean) * (b - mean) for a, b in zip(first, second, strict=True))
    spread = math.fsum((a - mean) ** 2 for a in first) * math.fsum((b - mean) ** 2 for b in second)
    if spread <= 0:
        return None
    return max(-1.0, min(1.0, above / math.sqrt(spread)))


def middle_of(found: Spine, at: Mapping[str, Point]) -> Point:
    """The middle of London's homes: the mean of the centres, each weighed by its homes."""
    placed = [oa for oa in sorted(at) if found.homes.get(oa, 0) > 0]
    homes = math.fsum(found.homes[oa] for oa in placed)
    if homes <= 0:
        raise ValueError("no home has a centre")
    return (
        math.fsum(found.homes[oa] * at[oa][0] for oa in placed) / homes,
        math.fsum(found.homes[oa] * at[oa][1] for oa in placed) / homes,
    )


def distance_from_the_middle(found: Spine, at: Mapping[str, Point]) -> dict[str, float]:
    """How far the homes of each area stand from the middle, in metres, as the mean over them."""
    middle = middle_of(found, at)
    far = {oa: metres_between(middle, at[oa]) for oa in sorted(at)}
    found_for: dict[str, float] = {}
    for area in found.weights.areas:
        oas = [oa for oa in found.weights.of_area[area] if oa in far and found.homes[oa] > 0]
        homes = math.fsum(found.homes[oa] for oa in oas)
        if homes > 0:
            found_for[area] = math.fsum(found.homes[oa] * far[oa] for oa in oas) / homes
    return found_for


@dataclass(frozen=True)
class Held:
    """One figure held against the three: how nearly it stands in the order of each."""

    figure: str
    # How many areas have the figure and all three.
    areas: int
    with_density: float | None
    with_distance: float | None
    with_every: float | None

    @property
    def follows_the_centre(self) -> bool:
        """Whether it stands in the order of how much is about, or of how far from the middle."""
        of_the_centre = (self.with_every, self.with_distance)
        return any(one is not None and abs(one) >= FOLLOWS for one in of_the_centre)

    def line(self) -> str:
        def said(value: float | None) -> str:
            return "none" if value is None else f"{value:.2f}"

        return (
            f"check=culture figure={self.figure} areas={self.areas} "
            f"with_density={said(self.with_density)} with_distance={said(self.with_distance)} "
            f"with_every={said(self.with_every)} follows_the_centre={int(self.follows_the_centre)}"
        )


def held_against(
    figure: str,
    values: Mapping[str, float | None],
    density: Mapping[str, float | None],
    distance: Mapping[str, float | None],
    every: Mapping[str, float | None],
) -> Held:
    """One figure, across the areas that have it and all three it is held against."""
    against = (density, distance, every)
    areas = [
        area
        for area in sorted(values)
        if values[area] is not None and all(held.get(area) is not None for held in against)
    ]

    def of(held: Mapping[str, float | None]) -> list[float]:
        return [float(held[area] or 0.0) for area in areas]

    mine = of(values)
    return Held(
        figure,
        len(areas),
        rank_correlation(mine, of(density)),
        rank_correlation(mine, of(distance)),
        rank_correlation(mine, of(every)),
    )


def put_forward(count: Held, rate: Held) -> tuple[str | None, str]:
    """Which figure is put forward, and why. None where a person decides."""
    if count.with_every is None and count.with_distance is None:
        return None, "The count could not be held against the centre, so a person decides."
    if count.follows_the_centre and not rate.follows_the_centre:
        return rate.figure, (
            f"The count stands in the order of the centre at {FOLLOWS} or more and the rate does "
            "not, so the rate is put forward."
        )
    if count.follows_the_centre:
        return None, (
            f"The count and the rate both stand in the order of the centre at {FOLLOWS} or more, "
            "so neither is put forward and a person decides."
        )
    return None, (
        f"The count does not stand in the order of the centre at {FOLLOWS} or more, so the rule "
        "puts nothing forward and a person decides."
    )


@dataclass(frozen=True)
class Check:
    """What the check found of the three figures of one build."""

    held: tuple[Held, Held, Held]
    put_forward: str | None
    why: str

    def lines(self) -> tuple[str, ...]:
        """What a run prints: a line of numbers for each figure, and what is put forward."""
        chosen = self.put_forward or "none"
        return (*(one.line() for one in self.held), f"check=culture put_forward={chosen}")


def is_a_line_of_numbers(line: str) -> bool:
    """Whether a line holds names and numbers alone, as every line the check prints does."""
    return A_LINE.fullmatch(line) is not None


def _values(worked: Mapping[str, Worked]) -> dict[str, float | None]:
    return {area: one.value for area, one in worked.items()}


def check(
    culture: Culture, found: Spine, density: Mapping[str, float | None], ground: Ground
) -> Check:
    """Hold the three figures of a build against how built up and how central each area is.

    `density` is the homes per hectare of each area, from the measure of homes
    of the same build.
    """
    seen = {oa: float(culture.reach.within[oa][EVERY]) for oa in culture.counted}
    every = _values(figures(seen, found))
    far: dict[str, float | None] = dict(distance_from_the_middle(found, ground.at))
    count = held_against(KEY, _values(culture.worked), density, far, every)
    rate = held_against(KEY_OF_THE_RATE, _values(culture.rate), density, far, every)
    kinds = held_against(KEY_OF_THE_KINDS, _values(culture.kinds), density, far, every)
    chosen, why = put_forward(count, rate)
    return Check((count, rate, kinds), chosen, why)
