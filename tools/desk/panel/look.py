"""What the panel shows of a release: an area, a measure, a vibe, and what stands out.

A release is read as it is served: through `read_served`, which holds it to every
rule of core and, where it is not made up, to the evidence it was built with. So
the panel shows what a person would be shown, and nothing it has worked out itself.
A band, a percentile and a share of a recipe are the release's own.

Every figure is shown with its unit, its source, its date and the file it rests
on. The file is read from the evidence of the build. The made-up city has made-up
evidence, which says of every file that it is made up.

The panel shows no census table and no household income: neither is a measure,
and neither module of core is imported here.

It reads files and writes none. See docs/design/panel.md.
"""

import json
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Final, cast

from burro_core.catalogue import (
    FEATURES,
    PLACED_ONLY_WITH,
    TAG_MIN_COVERAGE_HUNDREDTHS,
    Tag,
    rough_guides,
)
from burro_core.estimate import kilometres
from burro_core.facts import cost_key, fact_id
from burro_core.ids import FactKind, FeatureId, TagId
from burro_core.release import (
    BUILD_FOLDER,
    EVIDENCE,
    LOCK,
    CostEstimate,
    InMemoryRelease,
    Metric,
    Neighbourhood,
    ReleaseError,
    Source,
    recipes_held,
)
from burro_pipeline.evidence.made_up import made_up_evidence
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.release.read import read_served
from pydantic import ValidationError

type Json = bool | int | float | str | list[Json] | dict[str, Json] | None

BUILD: Final = "build.json"
# How the lock of a build names the file of changes it was given.
CHANGES: Final = "changes/"
# How many areas are listed as the highest, and as the lowest.
LISTED: Final = 10
BINS: Final = 10
# A band that rests on under this many hundredths of its recipe rests on little.
LITTLE: Final = 75
# A figure stands out where its percentile is this far from the middle one of the areas
# beside it, and at least this many of them have a figure.
FAR: Final = 50.0
BESIDE_FOR_FAR, BESIDE_FOR_NOUGHT = 3, 2
FAR_FROM: Final = "far_from_the_areas_beside_it"
NOUGHT: Final = "nought_where_the_areas_beside_it_are_not"
# What a vibe is held against, to see whether it is only a map of how built up a place is.
DENSITY: Final = FeatureId.HOMES_DENSITY
FROM_THE_CENTRE: Final = "distance_from_the_centre"
# Why an area has no figure, by the state of its row of evidence.
WHY: Final[Mapping[str, str]] = {
    "not_carried": "This build does not work the measure out.",
    "below_threshold": "Too little of the area is covered by the publisher's file.",
    "source_gap": "The publisher's file holds nothing for this area.",
    "suppressed": "The publisher withheld the figure.",
    "not_published": "The publisher does not publish it for areas this small.",
    "unknown": "The release holds no figure, and its evidence does not say why.",
}


class NotServed(Exception):
    """A folder that cannot be served as a release. The words are for a person to act on."""


@dataclass(frozen=True)
class Held:
    """A release as it is served, with the evidence it was built with."""

    folder: Path
    release: InMemoryRelease
    evidence: Evidence
    # Why a build left a measure out, by the measure, in the words of its record.
    left_out: Mapping[str, str]
    # The file of changes the release was built with, as its lock names it: the hash of
    # the file and how many bytes it held. None where it was built with none.
    built_with: tuple[str, int] | None = None

    @property
    def synthetic(self) -> bool:
        return self.release.manifest.synthetic

    @cached_property
    def areas(self) -> Mapping[str, Neighbourhood]:
        return {area.area_id: area for area in self.release.neighbourhoods}

    @cached_property
    def metrics(self) -> Mapping[FeatureId, Metric]:
        return {metric.feature_id: metric for metric in self.release.metrics}

    @cached_property
    def vibes(self) -> Mapping[TagId, Tag]:
        return {vibe.tag_id: vibe for vibe in self.release.vibes}

    @cached_property
    def sources(self) -> Mapping[str, Source]:
        return {source.source_id: source for source in self.release.manifest.sources}

    @cached_property
    def costs(self) -> Mapping[str, tuple[CostEstimate, ...]]:
        found: dict[str, list[CostEstimate]] = {}
        for cost in self.release.costs:
            found.setdefault(cost.area_id, []).append(cost)
        return {area: tuple(rows) for area, rows in found.items()}

    @cached_property
    def centre(self) -> tuple[float, float]:
        """The middle of the release's areas: the mean of the points inside them."""
        points = [area.centroid for area in self.release.neighbourhoods]
        return (
            statistics.fmean(point[0] for point in points),
            statistics.fmean(point[1] for point in points),
        )


def open_held(folder: Path) -> Held:
    """The release in a folder, as it is served. Raises `NotServed`, in one line of words."""
    try:
        release = read_served(folder)
    except ReleaseError as refused:
        raise NotServed(str(refused)) from None
    if release.manifest.synthetic:
        return Held(folder, release, made_up_evidence(release), {})
    beside = folder.resolve().with_name(f"{folder.resolve().name}{BUILD_FOLDER}")
    try:
        evidence = Evidence.model_validate_json((beside / EVIDENCE).read_bytes())
        build = cast(dict[str, Any], json.loads((beside / BUILD).read_bytes()))
        lock = cast(dict[str, Any], json.loads((beside / LOCK).read_bytes()))
    except (OSError, ValueError, ValidationError):
        raise NotServed(
            f"{beside.name} does not hold the evidence and the record of the build, as a "
            "build writes them"
        ) from None
    left_out = {
        str(one["feature_id"]): str(one["why"]) for one in build.get("measures_left_out", [])
    }
    taken = [one for one in lock.get("inputs", []) if str(one["name"]).startswith(CHANGES)]
    built_with = (str(taken[0]["sha256"]), int(taken[0]["bytes"])) if taken else None
    return Held(folder, release, evidence, left_out, built_with)


# What is served


def rough_of(vibe: Tag) -> Json:
    """What a vibe that is a rough guide says of itself: its label, and the sentence that
    says why. Both are core's, as every client is served them. Nothing for a vibe that is
    as sure as the rest."""
    return next(
        ({"label": told.label, "why": told.why} for told in rough_guides((vibe,))),
        None,
    )


def served(held: Held) -> dict[str, Any]:
    """What the release is, in counts: what is served today."""
    manifest = held.release.manifest
    recipes = {one.tag_id: one for one in recipes_held(held.release)}
    return {
        "release_id": manifest.release_id,
        "built_on": manifest.built_at[:10],
        "synthetic": manifest.synthetic,
        "preview": manifest.preview,
        "catalogue_version": manifest.catalogue_version,
        "areas": len(held.release.neighbourhoods),
        "measures": len(held.release.metrics),
        "left_out": len(held.left_out),
        "vibes": [
            {
                "id": vibe.tag_id,
                "label": vibe.label,
                "held": recipes[vibe.tag_id].held,
                "placed": recipes[vibe.tag_id].placed,
                "rough": rough_of(vibe),
            }
            for vibe in held.release.vibes
        ],
    }


def measures(held: Held) -> dict[str, Any]:
    """Every measure the release carries, by the family its setting is shown in."""
    return {
        "measures": [
            {
                "id": metric.feature_id,
                "label": metric.label,
                "unit": metric.unit,
                "family": metric.family,
                "ranked_on": metric.rankable,
            }
            for metric in held.release.metrics
        ]
    }


# An area


def _named(area: Neighbourhood) -> dict[str, Any]:
    return {
        "id": area.area_id,
        "name": area.name,
        "borough": area.borough,
        "label": area.named.label if area.named else area.name,
        "state": area.named.state if area.named else None,
    }


def areas(held: Held) -> dict[str, Any]:
    """Every area, to be found by its name, by its borough or on the map."""
    return {
        "areas": [
            {**_named(area), "centre": [area.centroid[0], area.centroid[1]]}
            for area in held.release.neighbourhoods
        ]
    }


def outlines(held: Held) -> dict[str, Any]:
    """The outline of every area, as the release draws it."""
    found: dict[str, Json] = {}
    for area in held.release.neighbourhoods:
        drawn = held.release.geometry(area.area_id)
        if drawn is not None:
            found[area.area_id] = cast(Json, drawn.model_dump(mode="json"))
    return {"outlines": found}


def _sources(held: Held, source_ids: Sequence[str]) -> list[Json]:
    return [
        {
            "id": source_id,
            "name": held.sources[source_id].name,
            "publisher": held.sources[source_id].publisher,
        }
        for source_id in source_ids
        if source_id in held.sources
    ]


def _rests_on(held: Held, row: EvidenceRow | None) -> dict[str, Any]:
    """The files a figure rests on, how it was made, and the state it is in."""
    if row is None:
        return {"files": [], "method": "", "state": "unknown", "covered": None}
    files: list[Json] = []
    for file_id in row.inputs:
        receipt = held.evidence.receipt(file_id)
        if receipt is not None:
            files.append(
                {
                    "id": file_id,
                    "name": receipt.publisher_file,
                    "edition": receipt.edition,
                    "source": receipt.source_id,
                    "retrieved_on": receipt.retrieved_at[:10],
                }
            )
    method = held.evidence.method(row.derivation_id) if row.derivation_id else None
    return {
        "files": files,
        "method": method.sentence if method else "",
        "state": row.state.value,
        "covered": row.weight_covered,
    }


def _why_missing(held: Held, row: EvidenceRow | None, feature_id: str) -> str:
    if feature_id in held.left_out:
        return held.left_out[feature_id]
    return WHY.get(row.state.value if row else "unknown", WHY["unknown"])


def _figures(held: Held, area_id: str) -> tuple[list[Json], list[Json]]:
    """The figures of an area, and what it has no figure for, each in the catalogue's order."""
    figures: list[Json] = []
    missing: list[Json] = []
    for feature_id, feature in FEATURES.items():
        metric = held.metrics.get(feature_id)
        held_row = held.release.feature(area_id, feature_id) if metric else None
        row = held.evidence.row(fact_id(area_id, FactKind.FEATURE, feature_id))
        if metric is None or held_row is None or held_row.value is None:
            label = metric.label if metric else feature.label
            why = _why_missing(held, row, feature_id)
            missing.append({"measure": feature_id, "label": label, "why": why})
            continue
        figures.append(
            {
                "measure": feature_id,
                "label": metric.label,
                "value": held_row.value,
                "unit": metric.unit,
                "percentile": held_row.percentile,
                "ranked_on": metric.rankable,
                "sources": _sources(held, metric.source_ids),
                "date": metric.vintage,
                **_rests_on(held, row),
            }
        )
    return figures, missing


def _costs(held: Held, area_id: str) -> list[Json]:
    found: list[Json] = []
    for cost in held.costs.get(area_id, ()):
        key = cost_key(cost.tenure, cost.segment)
        found.append(
            {
                "key": key,
                "tenure": cost.tenure,
                "segment": cost.segment,
                "median": cost.median,
                "lower_quartile": cost.lower_quartile,
                "upper_quartile": cost.upper_quartile,
                "sales": cost.sales,
                "since": cost.since,
                "unit": "£",
                "sources": _sources(held, cost.source_ids),
                "date": cost.as_of,
                **_rests_on(held, held.evidence.row(fact_id(area_id, FactKind.COST, key))),
            }
        )
    return found


def _why_not_placed(vibe: Tag, carried: int) -> str:
    said = (
        f"It rests on {carried} in 100 of its recipe here, and an area has a band from "
        f"{TAG_MIN_COVERAGE_HUNDREDTHS}."
    )
    needed = PLACED_ONLY_WITH.get(vibe.tag_id)
    if needed and carried >= TAG_MIN_COVERAGE_HUNDREDTHS:
        labels = " or ".join(f'"{FEATURES[part].label}"' for part in sorted(needed))
        return f"{said} It is placed only where {labels} has a figure."
    return said


def _vibes(held: Held, area_id: str) -> list[Json]:
    found: list[Json] = []
    for vibe in held.release.vibes:
        placed = held.release.tag(area_id, vibe.tag_id)
        parts: list[Json] = []
        carried = 0
        for term in vibe.terms:
            figure = held.release.feature(area_id, term.feature_id)
            has = figure is not None and figure.value is not None
            carried += term.hundredths if has else 0
            parts.append(
                {
                    "measure": term.feature_id,
                    "label": (held.metrics.get(term.feature_id) or FEATURES[term.feature_id]).label,
                    "hundredths": term.hundredths,
                    "read": term.reading,
                    "has_a_figure": has,
                    "percentile": figure.percentile if figure and has else None,
                }
            )
        band = placed.band if placed else None
        found.append(
            {
                "vibe": vibe.tag_id,
                "label": vibe.label,
                "rough": rough_of(vibe),
                "low_end": vibe.low_end,
                "high_end": vibe.high_end,
                "band": band,
                "held": carried,
                "rests_on_little": band is not None and carried < LITTLE,
                "why": "" if band is not None else _why_not_placed(vibe, carried),
                "parts": parts,
            }
        )
    return found


def area(held: Held, area_id: str) -> dict[str, Any] | None:
    """Everything the release holds of one area, and what it holds no figure for."""
    found = held.areas.get(area_id)
    if found is None:
        return None
    figures, missing = _figures(held, area_id)
    about = {
        **_named(found),
        "named_by": list(found.named.source_ids) if found.named else [],
        "ranked": found.rankable,
        "beside": [
            cast(Json, _named(held.areas[other]))
            for other in found.neighbours
            if other in held.areas
        ],
    }
    return {
        "area": about,
        "figures": figures,
        "costs": _costs(held, area_id),
        "vibes": _vibes(held, area_id),
        "missing": missing,
    }


# A measure


def stands_out(
    values: Mapping[str, float | None],
    percentiles: Mapping[str, float | None],
    beside: Mapping[str, Sequence[str]],
) -> list[dict[str, Any]]:
    """The areas whose figure stands out from those of the areas beside them.

    A figure is far from the areas beside it where its percentile is 50 or more from
    the middle one of theirs, and three of them or more have a figure. A figure is at
    nought where those beside it are not where it is 0, every one beside it that has a
    figure is over 0, and two or more have one. Each area is listed once.
    """
    found: list[dict[str, Any]] = []
    for area_id in sorted(values):
        value, percentile = values[area_id], percentiles.get(area_id)
        if value is None or percentile is None:
            continue
        others = [other for other in beside.get(area_id, ()) if values.get(other) is not None]
        theirs = [cast(float, values[other]) for other in others]
        if value == 0 and len(theirs) >= BESIDE_FOR_NOUGHT and all(one > 0 for one in theirs):
            found.append({"id": area_id, "why": NOUGHT, "beside": len(theirs)})
            continue
        ranks = [rank for other in others if (rank := percentiles.get(other)) is not None]
        if len(ranks) >= BESIDE_FOR_FAR and abs(percentile - statistics.median(ranks)) >= FAR:
            found.append({"id": area_id, "why": FAR_FROM, "beside": len(ranks)})
    return found


def _listed(of: Held, area_id: str, /, **more: Json) -> dict[str, Any]:
    found = of.areas[area_id]
    return {"id": area_id, "name": found.name, "borough": found.borough, **more}


def _bins(values: Sequence[float]) -> list[Json]:
    least, most = min(values), max(values)
    width = (most - least) / BINS
    if width == 0:
        return [{"from": least, "to": most, "areas": len(values)}]
    counts = [0] * BINS
    for value in values:
        counts[min(BINS - 1, int((value - least) / width))] += 1
    return [
        {"from": least + at * width, "to": least + (at + 1) * width, "areas": count}
        for at, count in enumerate(counts)
    ]


def measure(held: Held, feature_id: str) -> dict[str, Any] | None:
    """One measure across the release: its spread, its ends, its gaps and what stands out."""
    metric = held.metrics.get(cast(FeatureId, feature_id))
    if metric is None:
        return None
    rows = {area_id: held.release.feature(area_id, metric.feature_id) for area_id in held.areas}
    values = {area_id: row.value if row else None for area_id, row in rows.items()}
    percentiles = {area_id: row.percentile if row else None for area_id, row in rows.items()}
    known = sorted(
        (
            (value, held.areas[area_id].name, area_id)
            for area_id, value in values.items()
            if value is not None
        ),
    )
    figures = [value for value, _, _ in known]
    quartiles = (
        statistics.quantiles(figures, n=4, method="inclusive") if len(figures) > 1 else figures * 3
    )
    beside = {area_id: found.neighbours for area_id, found in held.areas.items()}
    return {
        "measure": {
            "id": metric.feature_id,
            "label": metric.label,
            "short_label": metric.short_label,
            "unit": metric.unit,
            "polarity": metric.polarity,
            "family": metric.family,
            "ranked_on": metric.rankable,
            "how": metric.method,
            "definition": metric.definition,
            "date": metric.vintage,
            "sources": _sources(held, metric.source_ids),
        },
        "spread": {
            "areas": len(values),
            "with_a_figure": len(figures),
            "least": figures[0] if figures else None,
            "lower_quartile": quartiles[0] if figures else None,
            "median": quartiles[1] if figures else None,
            "upper_quartile": quartiles[2] if figures else None,
            "most": figures[-1] if figures else None,
            "bins": _bins(figures) if figures else [],
        },
        "highest": [
            cast(Json, _listed(held, area_id, value=value))
            for value, _, area_id in sorted(known, key=lambda one: (-one[0], one[1]))[:LISTED]
        ],
        "lowest": [
            cast(Json, _listed(held, area_id, value=value)) for value, _, area_id in known[:LISTED]
        ],
        "missing": [
            cast(
                Json,
                _listed(
                    held,
                    area_id,
                    why=_why_missing(
                        held,
                        held.evidence.row(fact_id(area_id, FactKind.FEATURE, metric.feature_id)),
                        "",
                    ),
                ),
            )
            for area_id, value in values.items()
            if value is None
        ],
        "stands_out": [
            cast(Json, _listed(held, str(one["id"]), value=values[str(one["id"])], **one))
            for one in stands_out(values, percentiles, beside)
        ],
    }


# A vibe


def _ranks(values: Sequence[float]) -> list[float]:
    """The rank of each value, from 1. Values that are level share the mean of their ranks."""
    order = sorted(range(len(values)), key=lambda at: values[at])
    ranks = [0.0] * len(values)
    at = 0
    while at < len(order):
        end = at
        while end + 1 < len(order) and values[order[end + 1]] == values[order[at]]:
            end += 1
        for place in order[at : end + 1]:
            ranks[place] = (at + end) / 2 + 1
        at = end + 1
    return ranks


def rank_correlation(one: Sequence[float], other: Sequence[float]) -> float | None:
    """How closely two orders follow each other, from -1 to 1: Spearman's.

    None where there are fewer than two pairs, or where either is level throughout,
    so that there is no order to follow.
    """
    if len(one) != len(other) or len(one) < 2:
        return None
    try:
        return round(statistics.correlation(_ranks(one), _ranks(other)), 2)
    except statistics.StatisticsError:
        return None


def _follows(held: Held, raws: Mapping[str, float | None]) -> list[Json]:
    """How closely a vibe follows homes per hectare, and the distance from the centre."""
    placed = [area_id for area_id, raw in raws.items() if raw is not None]
    away = {area_id: kilometres(held.centre, held.areas[area_id].centroid) for area_id in placed}
    dense = {
        area_id: row.value
        for area_id in placed
        if (row := held.release.feature(area_id, DENSITY)) is not None and row.value is not None
    }
    found: list[Json] = []
    against: tuple[tuple[str, str, Mapping[str, float]], ...] = (
        (DENSITY.value, FEATURES[DENSITY].label, dense),
        (FROM_THE_CENTRE, "Distance from the middle of the areas, in a straight line", away),
    )
    for what, label, figures in against:
        both = [area_id for area_id in placed if area_id in figures]
        found.append(
            {
                "what": what,
                "label": label,
                "areas": len(both),
                "rank_correlation": rank_correlation(
                    [cast(float, raws[area_id]) for area_id in both],
                    [figures[area_id] for area_id in both],
                ),
            }
        )
    return found


def recipe_of(held: Held, vibe: Tag) -> list[Json]:
    """The parts of a recipe, each with its share and whether the release carries it."""
    return [
        {
            "measure": term.feature_id,
            "label": (held.metrics.get(term.feature_id) or FEATURES[term.feature_id]).label,
            "hundredths": term.hundredths,
            "read": term.reading,
            "carried": term.feature_id in held.metrics,
            "counts_residents": FEATURES[term.feature_id].describes == "residents",
        }
        for term in vibe.terms
    ]


def vibe(held: Held, tag_id: str) -> dict[str, Any] | None:
    """One vibe across the release: its recipe, its five bands, its ends and what it follows."""
    found = held.vibes.get(cast(TagId, tag_id))
    if found is None:
        return None
    rows = {area_id: held.release.tag(area_id, found.tag_id) for area_id in held.areas}
    raws = {area_id: row.raw if row else None for area_id, row in rows.items()}
    bands = {area_id: row.band if row else None for area_id, row in rows.items()}
    ordered = sorted(
        (
            (raw, held.areas[area_id].name, area_id)
            for area_id, raw in raws.items()
            if raw is not None
        ),
    )
    share = next(one for one in recipes_held(held.release) if one.tag_id == found.tag_id)
    counts = {str(band): 0 for band in (1, 2, 3, 4, 5)} | {"none": 0}
    for band in bands.values():
        counts["none" if band is None else str(band)] += 1
    return {
        "vibe": {
            "id": found.tag_id,
            "label": found.label,
            "rough": rough_of(found),
            "shape": found.shape,
            "low_end": found.low_end,
            "high_end": found.high_end,
            "family": found.family,
            "meaning": found.meaning,
            "cannot_see": list(found.cannot_see),
            "recipe": recipe_of(held, found),
            "held": share.held,
            "needed": share.needed,
            "placed": share.placed,
        },
        "bands": cast(Json, bands),
        "counts": cast(Json, counts),
        "highest": [
            cast(Json, _listed(held, area_id, band=bands[area_id]))
            for _, _, area_id in sorted(ordered, key=lambda one: (-one[0], one[1]))[:LISTED]
        ],
        "lowest": [
            cast(Json, _listed(held, area_id, band=bands[area_id]))
            for _, _, area_id in ordered[:LISTED]
        ],
        "follows": _follows(held, raws),
        "rests_on_little": [
            cast(Json, _listed(held, area_id, band=row.band, held=round(row.coverage * 100)))
            for area_id, row in rows.items()
            if row is not None and row.band is not None and round(row.coverage * 100) < LITTLE
        ],
    }
