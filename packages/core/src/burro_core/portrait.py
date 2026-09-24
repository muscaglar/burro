"""The portrait of an area: where it sits on every vibe, and what cannot be placed.

It is built with no spec, so it is the same for everyone. It holds ids and
no sentence: each mark names the fact that holds its sentence, its sources
and its date, and each part the fact that holds its figure. A part with no
figure names none, and nothing is filled in.

The scales come first, in a fixed order. Then the vibes the area has more of
than most areas, then those it has less of, furthest first. A vibe the area
cannot be placed on is listed as that, and never drawn in the middle.
"""

from collections.abc import Iterator

from burro_core._record import Record
from burro_core.catalogue import GRITTY, Tag
from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId, TagId, TagShape, TermReading
from burro_core.release import Release

# The scales, in the order they are drawn. Street character is last.
SCALES = (TagId.HOMES, TagId.PACE, TagId.BUILT_AGE, TagId.STREET_CHARACTER)
# A vibe is "more than most here" when this share of the areas compared, in
# per cent, sit strictly below the area, and "less than most" when as many
# sit strictly above.
MOST_PERCENT = 60
LISTED = 3


class PortraitPart(Record):
    """One part of a recipe, and the fact that holds this area's figure for it."""

    feature_id: FeatureId
    hundredths: int
    reading: TermReading
    # `None` where the area has no figure for the part.
    fact_id: str | None


class PortraitMark(Record):
    """One vibe on the portrait. The band and the sentence are in the fact it names."""

    tag_id: TagId
    fact_id: str
    # The `feature` fact of the heaviest part that has a figure: the plain
    # figure shown beside the mark. `None` where no part has one.
    figure_fact_id: str | None
    parts: tuple[PortraitPart, ...]


class Portrait(Record):
    scales: tuple[PortraitMark, ...]
    more: tuple[PortraitMark, ...]
    less: tuple[PortraitMark, ...]
    # Placed, and in neither list: near the middle, or beyond the three of a list.
    others: tuple[PortraitMark, ...]
    unplaced: tuple[PortraitMark, ...]


def _mark(release: Release, area_id: str, vibe: Tag) -> PortraitMark:
    carried = {metric.feature_id for metric in release.metrics}

    def figure(feature_id: FeatureId) -> str | None:
        row = release.feature(area_id, feature_id)
        known = feature_id in carried and row is not None and row.value is not None
        return fact_id(area_id, FactKind.FEATURE, feature_id) if known else None

    parts = tuple(
        PortraitPart(
            feature_id=term.feature_id,
            hundredths=term.hundredths,
            reading=term.reading,
            fact_id=figure(term.feature_id),
        )
        for term in vibe.terms
    )
    # The heaviest part that has a figure, and of two as heavy the first in the recipe.
    heaviest = max(
        (part for part in parts if part.fact_id is not None),
        key=lambda part: part.hundredths,
        default=None,
    )
    return PortraitMark(
        tag_id=vibe.tag_id,
        fact_id=fact_id(area_id, FactKind.TAG, vibe.tag_id),
        figure_fact_id=heaviest.fact_id if heaviest else None,
        parts=parts,
    )


def _beyond(release: Release, area_id: str, vibe: Tag) -> tuple[int, int, int]:
    """How many rankable areas sit strictly below an area on a vibe, and above, of how many."""
    mine = release.tag(area_id, vibe.tag_id)
    assert mine is not None and mine.raw is not None
    raws = [
        row.raw
        for area in release.neighbourhoods
        if area.rankable
        and (row := release.tag(area.area_id, vibe.tag_id)) is not None
        and row.raw is not None
    ]
    below = sum(1 for raw in raws if raw < mine.raw)
    above = sum(1 for raw in raws if raw > mine.raw)
    return below, above, len(raws)


def _never_first(marks: list[PortraitMark]) -> Iterator[PortraitMark]:
    """A list as it is shown. The way gritty was built is never the first thing said of an area."""
    gritty = frozenset(GRITTY.values())
    if len(marks) > 1 and marks[0].tag_id in gritty:
        marks = [marks[1], marks[0], *marks[2:]]
    yield from marks


def portrait(release: Release, area_id: str) -> Portrait | None:
    """The portrait of one area. `None` for an area the release lacks."""
    if release.neighbourhood(area_id) is None:
        return None
    scales: list[PortraitMark] = []
    more: list[tuple[int, PortraitMark]] = []
    less: list[tuple[int, PortraitMark]] = []
    middle: list[PortraitMark] = []
    unplaced: list[PortraitMark] = []
    for vibe in release.vibes:
        row = release.tag(area_id, vibe.tag_id)
        if row is None:
            continue
        mark = _mark(release, area_id, vibe)
        if row.band is None or row.raw is None:
            unplaced.append(mark)
        elif vibe.shape is TagShape.SCALE:
            scales.append(mark)
        else:
            below, above, compared = _beyond(release, area_id, vibe)
            # Counted in whole areas, so that no float decides which list a vibe is in.
            if vibe.strip and 100 * below >= MOST_PERCENT * compared:
                more.append((below, mark))
            elif vibe.strip and 100 * above >= MOST_PERCENT * compared:
                less.append((above, mark))
            else:
                middle.append(mark)

    def listed(found: list[tuple[int, PortraitMark]]) -> list[PortraitMark]:
        # Furthest first, and of two as far the first by id.
        ordered = sorted(found, key=lambda pair: (-pair[0], pair[1].tag_id))
        return [mark for _, mark in ordered]

    most, least = listed(more), listed(less)
    alone = [
        marks[0]
        for marks in (most, least)
        if len(marks) == 1 and marks[0].tag_id in GRITTY.values()
    ]
    most, least = ([mark for mark in marks if mark not in alone] for marks in (most, least))
    beyond = [*most[LISTED:], *least[LISTED:], *alone]
    order = {tag_id: position for position, tag_id in enumerate(SCALES)}
    shelf = {vibe.tag_id: vibe.shelf_order or 0 for vibe in release.vibes}
    return Portrait(
        scales=tuple(sorted(scales, key=lambda mark: order[mark.tag_id])),
        more=tuple(_never_first(most[:LISTED])),
        less=tuple(_never_first(least[:LISTED])),
        others=tuple(sorted([*middle, *beyond], key=lambda mark: shelf[mark.tag_id])),
        unplaced=tuple(unplaced),
    )
