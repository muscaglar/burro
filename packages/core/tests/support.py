"""The releases and specs the tests share.

Every name here is made up and every figure is invented. Nothing describes a
real place. Two releases are built: the four areas of the contract's worked
example, given by hand exactly as section 6.8 prints them, and a small release
that is complete enough to pass `parse_release`. A third is read: the
committed synthetic release, for the tests that must hold of what is served.
"""

import copy
import dataclasses
import random
from collections.abc import Mapping, Sequence
from functools import cache
from pathlib import Path
from typing import Any

from burro_core.catalogue import (
    FEATURES,
    RANKED_AS,
    TAGS,
    band_of,
    default_direction,
    percentile_of,
    tag_raw,
    tags_of,
)
from burro_core.ids import (
    Combine,
    Confidence,
    Direction,
    FeatureId,
    GrittyVariant,
    Mode,
    PlaceKind,
    Provenance,
    PtBasis,
    Segment,
    Strictness,
    TagId,
    Tenure,
    Toward,
    segments_for,
)
from burro_core.release import (
    SYNTHETIC_ATTRIBUTION,
    CostEstimate,
    Counts,
    Cutoffs,
    Destination,
    FeatureValue,
    InMemoryRelease,
    Manifest,
    Metric,
    Neighbourhood,
    Origin,
    Place,
    Release,
    Source,
    TagValue,
    TravelTable,
    open_release,
    parse_release,
)
from burro_core.spec import (
    Budget,
    Commute,
    FeatureWeight,
    PreferenceSpec,
    TagWeight,
    default_spec,
)

SYNTHETIC = ("synthetic",)
AS_OF = "2026-08"
BUILT_AT = "2026-09-23T00:00:00Z"
RELEASE_ID = "syn-2026-09-23-01"

AREA_NAMES = (
    "Alderwick",
    "Brackenhythe",
    "Cindermoor",
    "Dulcimer Green",
    "Eskerfold",
    "Farrowmere",
    "Gorsebeck",
    "Hollinsworth Quay",
)
BOROUGHS = ("Quillhaven", "Ostrel Vale")
PLACES = (
    ("Pellam Cross", PlaceKind.STATION, ("Pellam Cross Station",)),
    ("Foxholt Works", PlaceKind.LANDMARK, ("Foxholt",)),
    ("Wexmoor University", PlaceKind.UNIVERSITY, ("Wexmoor",)),
    ("Pellam Infirmary", PlaceKind.HOSPITAL, ()),
)
STATIONS = (
    ("Pellam Cross", ("Amber line", "Birch line")),
    ("Tinderside Halt", ("Birch line",)),
    ("Orlop Road", ("Cobalt line",)),
)


def area_id(number: int) -> str:
    return f"syn-n{number:04d}"


def place_id(number: int) -> str:
    return f"syn-p{number:04d}"


def destination_id(number: int) -> str:
    return f"syn-d{number:04d}"


# The vibes the releases of the tests carry: the twelve, and Gritty.
VARIANT = GrittyVariant.B
VIBES = tags_of(VARIANT)
# The features no release carries yet, so that three recipes run short.
NOT_CARRIED = frozenset(
    {
        FeatureId.PRIVATE_OUTDOOR_SPACE,
        FeatureId.CUISINE_VARIETY,
        FeatureId.GP_WALK,
        FeatureId.PHARMACY_WALK,
    }
)
CARRIED = tuple(feature_id for feature_id in FeatureId if feature_id not in NOT_CARRIED)


def manifest(
    areas: int, rankable: int, destinations: int, places: int, variant: GrittyVariant = VARIANT
) -> Manifest:
    return Manifest(
        release_id=RELEASE_ID,
        schema_version=2,
        built_at=BUILT_AT,
        catalogue_version=14,
        gritty_variant=variant,
        synthetic=True,
        preview=False,
        city="syn",  # pyright: ignore[reportArgumentType]
        seed=20260923,
        sources=(
            Source(
                source_id="synthetic",
                name="Synthetic test data",
                publisher="Burro",
                licence="None. Made up for testing",
                attribution=SYNTHETIC_ATTRIBUTION,
                url="",
                retrieved_on="2026-09-23",
            ),
        ),
        files=(),
        counts=Counts(
            neighbourhoods=areas,
            rankable=rankable,
            destinations=destinations,
            places=places,
            stations=len(STATIONS),
        ),
    )


def metric(feature_id: FeatureId, rankable: bool | None = None) -> Metric:
    """The row of a feature. What core shows and never ranks on is not ranked on."""
    feature = FEATURES[feature_id]
    if rankable is None:
        rankable = feature_id not in RANKED_AS
    return Metric(
        feature_id=feature_id,
        label=feature.label,
        short_label=feature.short_label,
        dimension=feature.dimension,
        unit=feature.unit,
        polarity=feature.polarity,
        kind=feature.kind,
        describes=feature.describes,
        family=feature.family,
        method=feature.method,
        in_likeness=feature.in_likeness,
        native_resolution=feature.native_resolution,
        source_ids=SYNTHETIC,
        vintage="2025",
        rankable=rankable,
        definition="Invented for testing. It measures nothing.",
    )


def neighbourhood(number: int, rankable: bool = True) -> Neighbourhood:
    name = AREA_NAMES[number - 1]
    return Neighbourhood(
        area_id=area_id(number),
        slug=name.lower().replace(" ", "-"),
        name=name,
        borough=BOROUGHS[(number - 1) % 2],
        aliases=(),
        centroid=(round(-0.1 + number * 0.01, 6), 0.05),
        rankable=rankable,
        neighbours=(),
    )


def place(number: int) -> Place:
    name, kind, aliases = PLACES[number - 1]
    return Place(
        place_id=place_id(number),
        name=name,
        aliases=aliases,
        kind=kind,
        destination_id=destination_id(number),
        # Place 1 is the station, and it stands in for every other place.
        coarse_place_id=place_id(1),
        centroid=(round(0.01 * number, 6), 0.0),
        source_id="synthetic",
    )


def cost(
    area: str, upper: int, tenure: Tenure = Tenure.RENT, segment: Segment | None = None
) -> CostEstimate:
    rent = tenure is Tenure.RENT
    return CostEstimate(
        area_id=area,
        tenure=tenure,
        segment=segment or (Segment.BED_1 if rent else Segment.FLAT),
        lower_quartile=upper - (300 if rent else 100_000),
        median=upper - (150 if rent else 50_000),
        upper_quartile=upper,
        confidence=Confidence.HIGH,
        as_of=AS_OF,
        source_ids=SYNTHETIC,
    )


Cells = tuple[tuple[int | None, ...], ...]


def travel_table(areas: int, destinations: int, pt_typical: Cells, **others: Cells) -> TravelTable:
    unknown: Cells = tuple((None,) * destinations for _ in range(areas))
    # Missing a service costs five minutes. A cell that is not minutes stays as it is.
    missed: Cells = tuple(
        tuple(cell + 5 if cell is not None and cell >= 0 else cell for cell in row)
        for row in pt_typical
    )
    return TravelTable(
        source_ids=SYNTHETIC,
        as_of="2026-09",
        area_ids=tuple(area_id(n) for n in range(1, areas + 1)),
        destination_ids=tuple(destination_id(n) for n in range(1, destinations + 1)),
        cutoff_minutes=Cutoffs(pt=90, cycle=60, walk=60),
        pt_typical=pt_typical,
        pt_just_missed=others.get("pt_just_missed", missed),
        cycle=others.get("cycle", unknown),
        walk=others.get("walk", unknown),
    )


# Section 6.8, as printed: minutes to place 1 and to place 2, the upper
# quartile, the park and noise percentiles, and the leafy score.
WORKED = (
    (32, 24, 1750, 20.0, 35.0, 72.0),
    (18, 28, 1950, 60.0, None, 45.0),
    (44, 22, 1500, 10.0, 15.0, 88.0),
    (25, 36, 1600, 30.0, 30.0, 60.0),
)


def feature_value(area: str, feature_id: FeatureId, percentile: float | None) -> FeatureValue:
    # The value is invented to go with the percentile the contract gives.
    return FeatureValue(
        area_id=area,
        feature_id=feature_id,
        value=None if percentile is None else round(100 + percentile * 9, 6),
        percentile=percentile,
        coverage=1.0,
    )


def tag_value(area: str, tag_id: TagId, score: float | None, band: int | None = None) -> TagValue:
    """A row of `tags.json`, with the score given as the contract gives it."""
    placed = score is not None
    found = (band or min(5, 1 + int(score // 20))) if placed else None
    return TagValue(
        area_id=area,
        tag_id=tag_id,
        raw=round(score / 100, 6) if placed else None,
        score=score,
        coverage=1.0 if placed else 0.0,
        band=found,
        spread_low=found,
        spread_high=found,
    )


def build_worked_release() -> InMemoryRelease:
    """The worked example, built by hand. Its percentiles are given, not computed."""
    areas = range(1, len(WORKED) + 1)
    return InMemoryRelease(
        manifest=manifest(areas=4, rankable=4, destinations=2, places=2),
        neighbourhoods=tuple(neighbourhood(n) for n in areas),
        neighbourhoods_origin=Origin(source_ids=SYNTHETIC, as_of="2026-09-23"),
        stations_origin=Origin(source_ids=SYNTHETIC, as_of="2026-09"),
        travel_table=travel_table(4, 2, tuple((row[0], row[1]) for row in WORKED)),
        metrics=(
            metric(FeatureId.PARK_PROXIMITY),
            metric(FeatureId.NOISE_EXPOSURE),
            # A part of Leafy, so that the score the example gives has a source to cite.
            metric(FeatureId.GREEN_COVER),
        ),
        features=(
            *(
                feature_value(area_id(n), feature_id, WORKED[n - 1][column])
                for n in areas
                for feature_id, column in (
                    (FeatureId.PARK_PROXIMITY, 3),
                    (FeatureId.NOISE_EXPOSURE, 4),
                )
            ),
            *(feature_value(area_id(n), FeatureId.GREEN_COVER, WORKED[n - 1][5]) for n in areas),
        ),
        tags=tuple(tag_value(area_id(n), TagId.LEAFY, WORKED[n - 1][5]) for n in areas),
        vibes=(TAGS[TagId.LEAFY],),
        costs=tuple(cost(area_id(n), WORKED[n - 1][2]) for n in areas),
        destinations=tuple(
            Destination(destination_id=destination_id(n), centroid=(0.01 * n, 0.0)) for n in (1, 2)
        ),
        places=(place(1), place(2)),
    )


def build_worked_spec() -> PreferenceSpec:
    stated = Provenance.STATED
    return PreferenceSpec(
        schema_version=1,
        tenure=Tenure.RENT,
        budget=Budget(
            amount=1800,
            segment=Segment.BED_1,
            strictness=Strictness.SOFT,
            weight=0.80,
            provenance=stated,
        ),
        commutes=(
            Commute(
                place_id=place_id(1),
                mode=Mode.PT,
                max_minutes=40,
                strictness=Strictness.SOFT,
                provenance=stated,
            ),
            Commute(
                place_id=place_id(2),
                mode=Mode.PT,
                max_minutes=30,
                strictness=Strictness.HARD,
                provenance=stated,
            ),
        ),
        commute_combine=Combine.SLOWEST,
        pt_basis=PtBasis.TYPICAL,
        commute_weight=1.00,
        weights=(
            FeatureWeight(
                feature_id=FeatureId.PARK_PROXIMITY,
                weight=0.50,
                direction=Direction.LESS,
                provenance=stated,
            ),
            FeatureWeight(
                feature_id=FeatureId.NOISE_EXPOSURE,
                weight=0.30,
                direction=Direction.LESS,
                provenance=stated,
            ),
        ),
        tags=(TagWeight(tag_id=TagId.LEAFY, weight=0.40, toward=Toward.HIGH, provenance=stated),),
        areas=(),
        tenure_from=stated,
        commute_combine_from=Provenance.DEFAULT,
        pt_basis_from=Provenance.DEFAULT,
        commute_weight_from=Provenance.DEFAULT,
    )


def _square(lon: float, lat: float) -> list[list[list[float]]]:
    half = 0.004
    west, east = round(lon - half, 6), round(lon + half, 6)
    south, north = round(lat - half, 6), round(lat + half, 6)
    return [[[west, south], [east, south], [east, north], [west, north], [west, south]]]


def _feature_rows(areas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rankable = [a["rankable"] for a in areas]
    rows: list[dict[str, Any]] = []
    for column, feature_id in enumerate(CARRIED):
        # Spread without a random source, with a gap on purpose in every third feature.
        values = [
            None
            if column % 3 == 0 and n == column % len(areas)
            else float((n * 37 + column * 11) % 53)
            for n in range(len(areas))
        ]
        percentiles = percentile_of(values, rankable)
        rows += [
            {
                "area_id": area["area_id"],
                "feature_id": feature_id.value,
                "value": value,
                "percentile": percentile,
                "coverage": 1.0 if value is not None else 0.2,
            }
            for area, value, percentile in zip(areas, values, percentiles, strict=True)
        ]
    return rows


def _tag_rows(
    areas: list[dict[str, Any]], features: list[dict[str, Any]], variant: GrittyVariant
) -> list[dict[str, Any]]:
    percentiles = {(r["area_id"], FeatureId(r["feature_id"])): r["percentile"] for r in features}
    rows: list[dict[str, Any]] = []
    rankable = [a["rankable"] for a in areas]
    for vibe in tags_of(variant):
        raws = [
            tag_raw(
                vibe.tag_id,
                {t.feature_id: percentiles.get((a["area_id"], t.feature_id)) for t in vibe.terms},
            )
            for a in areas
        ]
        scores = percentile_of([r.raw for r in raws], rankable)
        bands = band_of([r.raw for r in raws], rankable)
        rows += [
            {
                "area_id": area["area_id"],
                "tag_id": vibe.tag_id.value,
                "raw": raw.raw,
                "score": score,
                "coverage": raw.coverage,
                "band": band,
                "spread_low": band,
                "spread_high": band,
            }
            for area, raw, score, band in zip(areas, raws, scores, bands, strict=True)
        ]
    return rows


def build_documents(variant: GrittyVariant = VARIANT) -> dict[str, Any]:
    """A small release that keeps every rule of section 2.8, as the content of its files."""
    count = len(AREA_NAMES)
    ids = [area_id(n) for n in range(1, count + 1)]
    areas = [
        neighbourhood(n, rankable=n != count).model_dump(mode="json") for n in range(1, count + 1)
    ]
    # A ring of neighbours: each area touches the one before and the one after.
    for position, area in enumerate(areas):
        area["neighbours"] = sorted({ids[position - 1], ids[(position + 1) % count]})
    features = _feature_rows(areas)
    destinations = [destination_id(n) for n in range(1, len(PLACES) + 1)]
    typical: list[list[int | None]] = [
        [15 + (row * 7 + column * 13) % 60 for column in range(len(destinations))]
        for row in range(count)
    ]
    typical[2][1] = None  # not computed
    typical[3][2] = -1  # no journey within the cutoff
    table = travel_table(
        count,
        len(destinations),
        tuple(tuple(row) for row in typical),
        cycle=tuple(
            tuple(min(cell + 10, 60) if cell and cell > 0 else cell for cell in row)
            for row in typical
        ),
    )
    return {
        "manifest.json": manifest(
            count, count - 1, len(destinations), len(PLACES), variant
        ).model_dump(mode="json"),
        "neighbourhoods.json": {
            "source_ids": ["synthetic"],
            "as_of": "2026-09-23",
            "neighbourhoods": areas,
        },
        "geometry.json": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": area["area_id"],
                    "properties": {"area_id": area["area_id"]},
                    "geometry": {"type": "Polygon", "coordinates": _square(*area["centroid"])},
                }
                for area in areas
            ],
        },
        "catalogue.json": {
            "catalogue_version": 14,
            "metrics": [metric(feature_id).model_dump(mode="json") for feature_id in CARRIED],
            "vibes": [vibe.model_dump(mode="json") for vibe in tags_of(variant)],
        },
        "features.json": {"rows": features},
        "tags.json": {"rows": _tag_rows(areas, features, variant)},
        "cost.json": {
            "rows": [
                cost(
                    ids[n], (1400 if tenure is Tenure.RENT else 400_000) + n * step, tenure, kind
                ).model_dump(mode="json")
                # The last rankable area has no estimate, on purpose.
                for n in range(count - 2)
                for tenure, step in ((Tenure.RENT, 100), (Tenure.BUY, 25_000))
                # Every kind of home has a cost somewhere, so that a budget for
                # any of them can be tested.
                for kind in segments_for(tenure)
            ]
        },
        "destinations.json": {
            "destinations": [
                {"destination_id": d, "centroid": [0.01 * n, 0.0]}
                for n, d in enumerate(destinations)
            ]
        },
        "travel.json": table.model_dump(mode="json"),
        "stations.json": {
            "source_ids": ["synthetic"],
            "as_of": "2026-09",
            "rows": [
                {
                    "area_id": ids[n],
                    "station_id": f"syn-s{1 + (n + extra) % len(STATIONS):04d}",
                    "name": STATIONS[(n + extra) % len(STATIONS)][0],
                    "walk_minutes": 4 + n % 5 + extra * 3,
                    "lines": list(STATIONS[(n + extra) % len(STATIONS)][1]),
                    "step_free": (n + extra) % len(STATIONS) == 0,
                    "nearest": extra == 0,
                }
                for n in range(count)
                # Every other area has a second station within a short walk.
                for extra in range(1 + n % 2)
            ],
        },
        "places.json": {
            "places": [place(n).model_dump(mode="json") for n in range(1, len(PLACES) + 1)]
        },
    }


_DOCUMENTS = {variant: build_documents(variant) for variant in GrittyVariant}


def documents(variant: GrittyVariant = VARIANT) -> dict[str, Any]:
    """The content of a valid release's files. A copy, so a test may break it."""
    return copy.deepcopy(_DOCUMENTS[variant])


@cache
def small_release(variant: GrittyVariant = VARIANT) -> InMemoryRelease:
    """A small release that has been through `parse_release`. Shared: a release never changes."""
    return parse_release(documents(variant))


def with_figures(
    release: InMemoryRelease, figures: Mapping[FeatureId, Sequence[float | None]]
) -> InMemoryRelease:
    """A release with some features given these figures, area by area in id order.

    An area that is given none has no figure. Every percentile, and every
    score and band that rests on one, is worked out again, as a builder
    would work it out.
    """
    areas = release.neighbourhoods
    rankable = [area.rankable for area in areas]
    rows = {(row.area_id, row.feature_id): row for row in release.features}
    for feature_id, given in figures.items():
        values = [*given, *[None] * (len(areas) - len(given))]
        percentiles = percentile_of(values, rankable)
        for area, value, percentile in zip(areas, values, percentiles, strict=True):
            rows[area.area_id, feature_id] = FeatureValue(
                area_id=area.area_id,
                feature_id=feature_id,
                value=value,
                percentile=percentile,
                coverage=1.0 if value is not None else 0.0,
            )
    tags: list[TagValue] = []
    for vibe in release.vibes:
        raws = [
            tag_raw(
                vibe.tag_id,
                {
                    term.feature_id: row.percentile
                    for term in vibe.terms
                    if (row := rows.get((area.area_id, term.feature_id))) is not None
                },
            )
            for area in areas
        ]
        scores = percentile_of([raw.raw for raw in raws], rankable)
        bands = band_of([raw.raw for raw in raws], rankable)
        tags += [
            TagValue(
                area_id=area.area_id,
                tag_id=vibe.tag_id,
                raw=raw.raw,
                score=score,
                coverage=raw.coverage,
                band=band,
                spread_low=band,
                spread_high=band,
            )
            for area, raw, score, band in zip(areas, raws, scores, bands, strict=True)
        ]
    return dataclasses.replace(release, features=tuple(rows.values()), tags=tuple(tags))


def carrying(release: InMemoryRelease, *feature_ids: FeatureId) -> InMemoryRelease:
    """A release that carries some features more, each with a figure for every area.

    It is what a build of London may hold that the releases of the tests do not: the
    distance to a GP practice and to a pharmacy.
    """
    more = tuple(metric(feature_id) for feature_id in feature_ids)
    held = dataclasses.replace(release, metrics=(*release.metrics, *more))
    every = [float(100 * (n + 1)) for n in range(len(release.neighbourhoods))]
    return with_figures(held, dict.fromkeys(feature_ids, every))


def unplaced(release: InMemoryRelease, *tag_ids: TagId) -> InMemoryRelease:
    """A release that carries some vibes and places no area on them.

    It is what a first real build holds of most vibes: the recipe, and too
    few of its parts for any area to have a band.
    """
    rows = tuple(
        row.replace(
            raw=None, score=None, coverage=0.3, band=None, spread_low=None, spread_high=None
        )
        if row.tag_id in tag_ids
        else row
        for row in release.tags
    )
    return dataclasses.replace(release, tags=rows)


MATRICES = ("pt_typical", "pt_just_missed", "cycle", "walk")


def preview_documents() -> dict[str, Any]:
    """The small release as a preview: areas, outlines and measures, and none of the rest.

    It holds no journey, no place to reach, no station and no cost, and says
    so: the journeys and the stations state no source, because there is none.
    """
    found = documents()
    found["manifest.json"].update(preview=True)
    found["destinations.json"]["destinations"] = []
    found["places.json"]["places"] = []
    found["cost.json"]["rows"] = []
    travel = found["travel.json"]
    travel.update(source_ids=[], as_of=None, destination_ids=[])
    for matrix in MATRICES:
        travel[matrix] = [[] for _ in travel["area_ids"]]
    found["stations.json"].update(source_ids=[], as_of=None, rows=[])
    return found


@cache
def preview_release() -> InMemoryRelease:
    """The small preview, once it has been through `parse_release`."""
    return parse_release(preview_documents())


# How far a degree of longitude is on the ground where the made-up releases are drawn, at
# the equator, in kilometres.
KM_TO_A_DEGREE = 111.19508
# How far the homes of each area of the release below stand from place 1, in kilometres, due
# west of it. Against a limit of 40 minutes, at 12 minutes and 3 for each kilometre: the
# first four are likely within, the last of them at 29.7 minutes, the next three are
# borderline, the last of those at 49.8, and the last is likely beyond.
HOMES_KM = (2.0, 5.0, 5.5, 5.9, 7.0, 12.5, 12.6, 20.0)


def estimated_documents() -> dict[str, Any]:
    """The small release as a build that has routed no journey, and names places to reach.

    It holds no journey time, and says of each area where its homes stand. So a
    journey by public transport is estimated from distance, as a build of
    London estimates one. It is a preview, as any release with no journey is.
    """
    found = documents()
    found["manifest.json"].update(preview=True)
    east, north = place(1).centroid
    for area, km in zip(found["neighbourhoods.json"]["neighbourhoods"], HOMES_KM, strict=True):
        area["homes_at"] = [round(east - km / KM_TO_A_DEGREE, 9), north]
    travel = found["travel.json"]
    travel.update(source_ids=[], as_of=None, destination_ids=[])
    for matrix in MATRICES:
        travel[matrix] = [[] for _ in travel["area_ids"]]
    return found


@cache
def estimated_release() -> InMemoryRelease:
    """The small release whose journeys are estimated, once it has been through the parser.

    No area of it is known to stand near the Underground: its figures of that
    are taken out, and a test that wants one puts it in.
    """
    return with_figures(parse_release(estimated_documents()), {FeatureId.UNDERGROUND_PROXIMITY: ()})


FIXTURES = Path(__file__).parents[3] / "data" / "fixtures" / "synthetic"


@cache
def fixture_release() -> InMemoryRelease:
    """The committed synthetic release, which is what the service runs on.

    Core opens no file, so the bytes are read here and handed to
    `open_release`, as the pipeline and the API do.
    """
    (folder,) = (entry for entry in FIXTURES.iterdir() if entry.is_dir())
    # A file browser leaves this behind. The readers skip it too.
    files = {f.name: f.read_bytes() for f in sorted(folder.iterdir()) if f.name != ".DS_Store"}
    return open_release(folder.name, files)


def draws(seed: int) -> random.Random:
    """A seeded source for property-style tests. The same seed gives the same cases."""
    return random.Random(seed)  # noqa: S311


def random_spec(draw: random.Random, release: Release) -> PreferenceSpec:
    spec = default_spec(draw.choice(list(Tenure)))
    # What the release shows and ranks no area on cannot be weighed.
    carried = [metric.feature_id for metric in release.metrics if metric.rankable]
    features = draw.sample(carried, min(draw.randrange(0, 6), len(carried)))
    vibes = list(release.vibes)
    tags = draw.sample(vibes, min(draw.randrange(0, 4), len(vibes)))
    places = draw.sample([p.place_id for p in release.places], draw.randrange(0, 4))
    return spec.replace(
        budget=spec.budget.replace(
            amount=draw.choice([None, *range(1000, 3000, 250)])
            if spec.tenure is Tenure.RENT
            else draw.choice([None, 300_000, 450_000, 600_000]),
            strictness=draw.choice(list(Strictness)),
            weight=draw.randrange(0, 21) / 20,
        ),
        commutes=tuple(
            Commute(
                place_id=p,
                mode=draw.choice([Mode.PT, Mode.CYCLE]),
                max_minutes=draw.randrange(10, 61),
                strictness=draw.choice(list(Strictness)),
                provenance=Provenance.STATED,
            )
            for p in places[:3]
        ),
        commute_combine=draw.choice(list(Combine)),
        pt_basis=draw.choice(list(PtBasis)),
        commute_weight=draw.randrange(0, 21) / 20,
        weights=tuple(
            FeatureWeight(
                feature_id=f,
                weight=draw.randrange(0, 21) / 20,
                direction=default_direction(f),
                provenance=Provenance.STATED,
            )
            for f in features
        ),
        tags=tuple(
            TagWeight(
                tag_id=vibe.tag_id,
                weight=draw.randrange(0, 21) / 20,
                # Only a scale has a low end to ask for.
                toward=draw.choice(list(Toward)) if vibe.low_end else Toward.HIGH,
                provenance=Provenance.STATED,
            )
            for vibe in tags
        ),
    )
