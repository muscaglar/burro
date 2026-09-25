"""What would move: a change that is proposed, worked out on the release before it is kept.

Before a person keeps a change of a recipe, the panel shows what a build would make of
it: how many areas change band, the areas that rise and fall most, and the first ten
areas of three searches, before and after. Every band and every rank is core's own:
`tag_raw`, `percentile_of`, `band_of` and `rank`. No second copy of that arithmetic is
written here: a search is ranked by `burro_pipeline.upkeep.searches`, as the step `moved`
ranks it before and after a build.

"Before" is the release as a build would make it today, with every change the founder
has kept laid over core's own. "After" is that with the change that is proposed. So
what is shown is what this one change would move.

The three searches are typed edits, in `searches.json`. The panel holds nobody's search:
the first is the founder's own test sentence, which is a case of the reader's evaluation
set, and the other two are made up.

It reads files and writes none. See docs/design/panel.md, section 4.
"""

import dataclasses
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final

from burro_core.catalogue import TAGS, Tag, band_of, percentile_of, tag_raw, tags_of
from burro_core.ids import TagId
from burro_core.release import InMemoryRelease, TagValue
from burro_pipeline import changes
from burro_pipeline.changes import Change
from burro_pipeline.upkeep import searches as ranked
from burro_pipeline.upkeep.searches import (
    FIRST,
    NO_PLACE,
    NOT_IN_IT,
    Search,
    Unfit,
    first_of,
    read_searches,
)

from desk.panel.look import Held

__all__ = [
    "FIRST",
    "NOT_IN_IT",
    "NO_PLACE",
    "SEARCHES",
    "Search",
    "Unfit",
    "built_with",
    "first_of",
    "moved",
    "of_a_recipe",
    "places_what_core_holds_off",
    "read_searches",
    "rows_of",
    "searched",
    "seen",
    "with_vibes",
]

SEARCHES: Final = Path(__file__).with_name("searches.json")
# The rule of core that a vibe it holds off is placed by no change to its shares.
HELD_OFF: Final = "held_off_stays_held_off"


def rows_of(release: InMemoryRelease, vibe: Tag) -> tuple[TagValue, ...]:
    """Where every area of a release stands on a vibe, by the recipe the vibe is handed
    with: worked out by core, from the release's own percentiles."""
    areas = [area.area_id for area in release.neighbourhoods]
    rankable = [area.rankable for area in release.neighbourhoods]
    raws = [
        tag_raw(
            vibe.tag_id,
            {
                term.feature_id: row.percentile
                for term in vibe.terms
                if (row := release.feature(area, term.feature_id)) is not None
            },
            vibe.terms,
        )
        for area in areas
    ]
    scores = percentile_of([raw.raw for raw in raws], rankable)
    bands = band_of([raw.raw for raw in raws], rankable)
    return tuple(
        TagValue(
            area_id=area,
            tag_id=vibe.tag_id,
            raw=raw.raw,
            score=score,
            coverage=raw.coverage,
            band=band,
            spread_low=band,
            spread_high=band,
        )
        for area, raw, score, band in zip(areas, raws, scores, bands, strict=True)
    )


def places_what_core_holds_off(release: InMemoryRelease, vibe: Tag) -> bool:
    """Whether a recipe places an area on a vibe that core's own recipe places none on.

    It is the rule `held_off_stays_held_off` of core, asked before a change is
    kept: a build would stop at the change, and nothing is kept that a build
    would stop at.
    """
    if vibe.terms == TAGS[vibe.tag_id].terms:
        return False
    by_core = any(row.raw is not None for row in rows_of(release, TAGS[vibe.tag_id]))
    return not by_core and any(row.raw is not None for row in rows_of(release, vibe))


def with_vibes(release: InMemoryRelease, vibes: Sequence[Tag]) -> InMemoryRelease:
    """The release as a build would make it with these vibes: every band of a vibe that
    differs is worked out again, by core, from the release's own percentiles."""
    held = {vibe.tag_id: vibe for vibe in release.vibes}
    moved = {vibe.tag_id: vibe for vibe in vibes if held.get(vibe.tag_id) != vibe}
    if not moved:
        return release
    rows = {
        (row.area_id, row.tag_id): row for vibe in moved.values() for row in rows_of(release, vibe)
    }
    return dataclasses.replace(
        release,
        vibes=tuple(moved.get(vibe.tag_id, vibe) for vibe in release.vibes),
        tags=tuple(rows.get((row.area_id, row.tag_id), row) for row in release.tags),
    )


def built_with(held: Held, lines: Sequence[Change]) -> InMemoryRelease:
    """The release as a build would make it with these lines of the founder's laid over
    core's own. Raises `ChangesError` for a line no build would take."""
    core = tags_of(held.release.manifest.gritty_variant)
    return with_vibes(held.release, changes.adjusted(core, lines))


def seen(what: str, of: str, was: object, now: object) -> str:
    """The mark of a preview: what was looked at, as twelve digits of its hash. A change
    is kept only with the mark of the preview of that very change."""
    held = json.dumps([what, of, was, now], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(held.encode("utf-8")).hexdigest()[:12]


def _bands(release: InMemoryRelease, tag_id: TagId) -> dict[str, TagValue]:
    return {row.area_id: row for row in release.tags if row.tag_id is tag_id}


def moved(before: InMemoryRelease, after: InMemoryRelease, tag_id: TagId) -> dict[str, Any]:
    """How the areas stand on a vibe before and after: how many change band, and which rise
    and fall most. An area is said by its band, and never by the score it is ranked on."""
    was, now = _bands(before, tag_id), _bands(after, tag_id)
    areas = {area.area_id: area for area in after.neighbourhoods}
    steps: dict[tuple[int | None, int | None], int] = {}
    shifts: list[tuple[float, str]] = []
    for area_id, row in now.items():
        old = was[area_id]
        if old.band != row.band:
            steps[old.band, row.band] = steps.get((old.band, row.band), 0) + 1
        if old.score is not None and row.score is not None and old.score != row.score:
            shifts.append((row.score - old.score, area_id))

    def listed(found: Sequence[tuple[float, str]]) -> list[dict[str, Any]]:
        return [
            {
                "id": area_id,
                "name": areas[area_id].name,
                "borough": areas[area_id].borough,
                "from": was[area_id].band,
                "to": now[area_id].band,
            }
            for _, area_id in found[:FIRST]
        ]

    up = sum(n for (a, b), n in steps.items() if a is not None and b is not None and b > a)
    down = sum(n for (a, b), n in steps.items() if a is not None and b is not None and b < a)
    return {
        "areas": len(now),
        "change_band": sum(steps.values()),
        "up": up,
        "down": down,
        "placed_before": sum(row.band is not None for row in was.values()),
        "placed_after": sum(row.band is not None for row in now.values()),
        "steps": [
            {"from": a, "to": b, "areas": n}
            for (a, b), n in sorted(steps.items(), key=lambda one: (one[0][0] or 0, one[0][1] or 0))
        ],
        "rise": listed(sorted(shifts, key=lambda one: (-one[0], areas[one[1]].name))),
        "fall": listed(sorted(shifts, key=lambda one: (one[0], areas[one[1]].name))),
    }


def searched(
    searches: Sequence[Search], before: InMemoryRelease, after: InMemoryRelease
) -> list[dict[str, Any]]:
    """The first ten areas of each search, before and after, with the sentence each was
    read from: the panel shows it on the machine of the person who decides."""
    found = ranked.searched(searches, before, after)
    return [{**one, "says": search.says} for search, one in zip(searches, found, strict=True)]


def of_a_recipe(
    held: Held, searches: Sequence[Search], lines: Sequence[Change], proposed: Change
) -> dict[str, Any]:
    """What a change of the shares of a recipe would move: the bands of the vibe, and the
    first ten areas of each search. Raises `ChangesError` for a change no build would take."""
    before = built_with(held, lines)
    after = built_with(held, [*lines, proposed])
    made = next(vibe for vibe in after.vibes if vibe.tag_id.value == proposed.of)
    if places_what_core_holds_off(held.release, made):
        raise changes.ChangesError(0, HELD_OFF)
    return {
        "bands": moved(before, after, TagId(proposed.of)),
        "searches": searched(searches, before, after),
    }
