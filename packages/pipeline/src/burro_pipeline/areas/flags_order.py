"""The order a person is shown the areas in: most at stake first.

A person cannot look at every area. So the areas are put in order of how many
homes a wrong border would put in the wrong area, and how unsure the method
was of each.

**How sure the method was.** The method gives every output area a margin: by
how much its second choice is further than its first. An output area with a
margin under 10% is in doubt, by how near the margin is to nothing: wholly at
no margin, half at 5%, not at all at 10%. How sure the method was of an area is
the share of it that is not in doubt. An output area the draft gives no margin
had no second choice, and is not in doubt. Where the draft gives no margin for
any output area of an area, how sure the method was is not known, and is not
made up.

**What is at stake.** The sum of two things.

- Over the output areas a flag about the border points at: the homes of each,
  times how unsure the method is of it. An output area that several flags
  point at is counted once, at the most unsure. An output area with a margin
  under 10% counts whether or not so many do that the area is flagged for it.
- For each flag that is of the area as a whole: a tenth of the area's homes.

A flag about the name adds nothing: it is settled where names are read.

**The order.** An area that breaks a rule the design holds a release to comes
before every other: one in two pieces, or on both banks. Then the most at stake
first. Of two with as much at stake, the one with more flags about its border,
then the one that holds more.

Where the licence gate does not give the count of homes for this use, an
output area counts as one. An output area is drawn to hold much the same number
of households as another, so the order changes little. Every row says which
was used.

A borough's place is the sum over the areas whose main borough it is.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from burro_pipeline.areas.flags import (
    ABOUT_THE_NAME,
    BORDERS,
    BREAKS_A_RULE,
    Draft,
    Flag,
    Rules,
    close_cells,
    main_borough,
)

# The share of an area that a flag of the whole area puts at stake.
OF_THE_WHOLE = 0.1
WHOLE = "whole"


@dataclass(frozen=True)
class Placed:
    """One area, or one borough, in its place in the order."""

    queue: str
    item: str
    # Its place, from 1.
    rank: int
    flags: tuple[str, ...]
    # The homes, or output areas, that a wrong border would put in the wrong area.
    at_stake: float
    # What it holds in all, in the same unit.
    held: float
    # The share of it the method was sure of. None where that is not known.
    sure: float | None
    weighed_by: str
    why: tuple[str, ...]

    @property
    def about_the_border(self) -> tuple[str, ...]:
        """Its flags that are about where the border runs, and not about the name."""
        return tuple(code for code in self.flags if code not in ABOUT_THE_NAME)


def doubts(draft: Draft, flags: Sequence[Flag], rules: Rules) -> dict[str, dict[str, float]]:
    """For each area, the cells in doubt, each with the most doubt anything gives it.

    A cell is in doubt where a flag points at it, and where its margin is under the
    number the rule turns on, whether or not so many are that the area is flagged for it.
    A cell a flag points at only to show it, with no doubt, is left out.
    """
    found = {area_id: close_cells(draft, rules, area_id) for area_id in sorted(draft.areas)}
    for flag in flags:
        if flag.queue != BORDERS:
            continue
        cells = found.setdefault(flag.area, {})
        for oa, doubt in zip(flag.cells, flag.doubt, strict=True):
            cells[oa] = max(cells.get(oa, 0.0), min(1.0, max(0.0, doubt)))
    return {
        area_id: {oa: doubt for oa, doubt in sorted(cells.items()) if doubt > 0}
        for area_id, cells in found.items()
    }


def sure_of(draft: Draft, rules: Rules, area_id: str) -> float | None:
    """The share of an area the method was sure of, from its margins and nothing else."""
    oas = draft.cells_of[area_id]
    held = draft.held[area_id]
    if not oas or held <= 0 or all(draft.cells[oa].margin is None for oa in oas):
        return None
    close = close_cells(draft, rules, area_id)
    unsure = math.fsum(draft.weight(oa) * close[oa] for oa in sorted(close))
    return max(0.0, 1 - unsure / held)


def areas_in_order(draft: Draft, flags: Sequence[Flag], rules: Rules | None = None) -> list[Placed]:
    """Every area that has a cell, the most at stake first."""
    rules = rules or Rules()
    pointed = doubts(draft, flags, rules)
    raised: dict[str, list[Flag]] = {}
    for flag in flags:
        if flag.queue == BORDERS:
            raised.setdefault(flag.area, []).append(flag)
    found: list[tuple[tuple[object, ...], Placed]] = []
    for area_id in sorted(draft.areas):
        if not draft.cells_of[area_id]:
            continue
        cells = pointed.get(area_id, {})
        mine = raised.get(area_id, [])
        held = draft.held[area_id]
        of_the_whole = sum(flag.whole and flag.code not in ABOUT_THE_NAME for flag in mine)
        at_stake = math.fsum(draft.weight(oa) * cells[oa] for oa in sorted(cells))
        at_stake = min(held, at_stake + OF_THE_WHOLE * held * of_the_whole)
        placed = Placed(
            queue=BORDERS,
            item=area_id,
            rank=0,
            flags=tuple(flag.code for flag in mine),
            at_stake=at_stake,
            held=held,
            sure=sure_of(draft, rules, area_id),
            weighed_by=draft.weighed_by,
            why=tuple(flag.why for flag in mine),
        )
        breaks = any(flag.code in BREAKS_A_RULE for flag in mine)
        key = (not breaks, -at_stake, -len(placed.about_the_border), -held, area_id)
        found.append((key, placed))
    return _ranked([placed for _, placed in sorted(found, key=lambda pair: pair[0])])


def boroughs_in_order(
    draft: Draft, areas: Sequence[Placed], groups: Mapping[str, str]
) -> list[Placed]:
    """Every borough, the one with most at stake first. `groups` names each borough's item."""
    inside: dict[str, list[Placed]] = {}
    for placed in areas:
        inside.setdefault(main_borough(draft, placed.item), []).append(placed)
    found: list[tuple[tuple[object, ...], Placed]] = []
    for code, mine in sorted(inside.items()):
        if code not in groups:
            continue
        flagged = [placed for placed in mine if placed.about_the_border]
        at_stake = math.fsum(placed.at_stake for placed in mine)
        held = math.fsum(placed.held for placed in mine)
        known = [placed for placed in mine if placed.sure is not None]
        sure = (
            math.fsum(each.sure * each.held for each in known if each.sure is not None)
            / math.fsum(each.held for each in known)
            if known and len(known) == len(mine)
            else None
        )
        has = "area has" if len(flagged) == 1 else "areas have"
        placed = Placed(
            queue=WHOLE,
            item=groups[code],
            rank=0,
            flags=tuple(sorted({code for placed in mine for code in placed.flags})),
            at_stake=at_stake,
            held=held,
            sure=sure,
            weighed_by=draft.weighed_by,
            why=(f"{len(flagged)} of its {len(mine)} {has} a flag about the border.",),
        )
        found.append(((-at_stake, -len(flagged), groups[code]), placed))
    return _ranked([placed for _, placed in sorted(found, key=lambda pair: pair[0])])


def _ranked(placed: Sequence[Placed]) -> list[Placed]:
    return [replace(each, rank=rank) for rank, each in enumerate(placed, start=1)]
