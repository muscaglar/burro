"""Likeness: which areas are most like one area, in streets, buildings and places.

It is a pure function of a release. It is counted on measured parts and
never on vibes, so that a walk to a park that six recipes hold counts once.
Each part is compared by its band, one of five. The areas in the same band
on the most parts come first. Where two share as many, the nearer comes
first, by a distance in which the parts are grouped by family so that each
family counts the same.

What it may never be counted on: a nuisance, recorded crime, anything that is
weighed on request only, what a home costs, a journey, a vibe's own score,
and the parts held out until an audit has passed them. It is never counted
on a feature that describes who lives somewhere: two areas are never said to
be alike for who lives in them (ADR 0006). A feature says for itself whether
likeness may use it: `Feature.in_likeness`.
"""

from collections.abc import Mapping

from burro_core._record import Record
from burro_core.catalogue import FAMILIES, FEATURES, Feature, band_of
from burro_core.ids import Describes, Family, FeatureId, FeatureKind
from burro_core.release import Release

SIMILAR = 5
# Below this share of the parts, in whole parts, too little is known of an
# area to say what it is like.
MIN_KNOWN_PERCENT = 60
# The most two bands can differ by: band 1 against band 5.
_FURTHEST = 4
_DECIMALS = 9

Bands = Mapping[FeatureId, Mapping[str, int | None]]


class Likeness(Record):
    """How like one area another is. `same` orders the areas, and is what the sentence says."""

    area_id: str
    # 0 is the same band on every part, 1 is the far end of every part. It
    # orders two areas that share as many measures, and is never printed.
    distance: float
    # The parts both areas have a figure for, and how many of them are in the same band.
    measures: int
    same: int
    # The family the two are least alike in. `None` where they differ in none.
    family: Family | None


def may_be_compared(feature: Feature) -> bool:
    """Whether likeness may be counted on a feature. Its own flag, and what no flag may undo."""
    return (
        feature.in_likeness
        and feature.kind in (FeatureKind.TASTE, FeatureKind.AMENITY)
        and feature.describes is not Describes.EVENTS
        and feature.describes is not Describes.RESIDENTS
        and feature.family is not None
    )


def parts_of(release: Release) -> tuple[Feature, ...]:
    """The measures likeness is counted on in this release, each once, by id."""
    carried = (FEATURES[metric.feature_id] for metric in release.metrics)
    return tuple(feature for feature in carried if may_be_compared(feature))


def part_bands(release: Release) -> Bands:
    """The band of every area on every part, with no polarity applied.

    It is the band of the figure itself, low to high, so that two areas are
    alike where their figures are, whichever way a person would want them.
    """
    areas = release.neighbourhoods
    rankable = [area.rankable for area in areas]
    found: dict[FeatureId, Mapping[str, int | None]] = {}
    for part in parts_of(release):
        rows = (release.feature(area.area_id, part.feature_id) for area in areas)
        bands = band_of([None if row is None else row.value for row in rows], rankable)
        found[part.feature_id] = {
            area.area_id: band for area, band in zip(areas, bands, strict=True)
        }
    return found


def _known(bands: Bands, area_id: str) -> bool:
    """Whether enough is known of an area to say what it is like. Counted in whole parts."""
    have = sum(1 for of in bands.values() if of.get(area_id) is not None)
    return bool(bands) and 100 * have >= MIN_KNOWN_PERCENT * len(bands)


def _between(bands: Bands, area_id: str, other_id: str) -> Likeness | None:
    apart: dict[Family, list[int]] = {}
    for feature_id, of in bands.items():
        mine, theirs = of.get(area_id), of.get(other_id)
        family = FEATURES[feature_id].family
        if mine is not None and theirs is not None and family is not None:
            apart.setdefault(family, []).append(abs(mine - theirs))
    if not apart:
        return None
    by_family = {
        family: sum(apart[family]) / (_FURTHEST * len(apart[family]))
        for family in FAMILIES
        if family in apart
    }
    furthest = max(by_family.values())
    differences = [difference for found in apart.values() for difference in found]
    return Likeness(
        area_id=other_id,
        distance=round(sum(by_family.values()) / len(by_family), _DECIMALS),
        measures=len(differences),
        same=sum(1 for difference in differences if difference == 0),
        # The first in the order of the settings, where two are as far apart.
        family=next(f for f, distance in by_family.items() if distance == furthest)
        if furthest > 0
        else None,
    )


def similar(release: Release, area_id: str, n: int = SIMILAR) -> tuple[Likeness, ...]:
    """The rankable areas most like this one, most alike first. Never the area itself.

    Most alike is in the same band on the most measures, which is the count
    each sentence gives. So the order is the one a person can check on the
    page: it was by a distance that is never shown, and an area with 5
    measures the same stood above ones with 7 and 8. Where two share as
    many, the nearer comes first, and then the id decides.

    Empty where likeness is unknown: the release does not hold the area, or
    too little is known of it. An area of which too little is known is like
    nothing, and nothing is like it.
    """
    if release.neighbourhood(area_id) is None:
        return ()
    bands = part_bands(release)
    if not _known(bands, area_id):
        return ()
    found = [
        between
        for other in release.neighbourhoods
        if other.rankable and other.area_id != area_id and _known(bands, other.area_id)
        for between in [_between(bands, area_id, other.area_id)]
        if between is not None
    ]
    found.sort(key=lambda between: (-between.same, between.distance, between.area_id))
    return tuple(found[: max(n, 0)])
