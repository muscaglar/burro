"""The v1 feature catalogue: 23 features and 12 tags, each describing a place.

None describes who lives there (ADR 0006). An id names the idea, not the method:
distances and thresholds live in a release's `definition` and may change with
`CATALOGUE_VERSION`. An id is never renamed, reused or given a new meaning.
"""

from bisect import bisect_left, bisect_right
from collections.abc import Mapping, Sequence
from types import MappingProxyType

from pydantic import Field

from burro_core._record import Record
from burro_core.ids import (
    Dimension,
    Direction,
    FeatureId,
    NativeResolution,
    Polarity,
    TagId,
    TermReading,
)

CATALOGUE_VERSION = 1

# Below this share of a tag's formula, by weight, the tag is unknown for the area.
TAG_MIN_COVERAGE_HUNDREDTHS = 60


class Feature(Record):
    feature_id: FeatureId
    dimension: Dimension
    label: str
    unit: str
    polarity: Polarity
    native_resolution: NativeResolution
    # The comparatives that fill "X than 80% of areas".
    higher: str
    lower: str


class TagTerm(Record):
    feature_id: FeatureId
    # A whole number of hundredths, so that coverage is compared exactly. A float
    # sum of 0.30, 0.15 and 0.15 must not decide which side of 0.6 it falls.
    hundredths: int = Field(ge=1, le=100)
    reading: TermReading


class Tag(Record):
    tag_id: TagId
    label: str
    terms: tuple[TagTerm, ...]


class TagRaw(Record):
    raw: float | None
    coverage: float


def _feature(
    feature_id: FeatureId,
    dimension: Dimension,
    label: str,
    unit: str,
    polarity: Polarity,
    native: NativeResolution,
    higher: str,
    lower: str,
) -> Feature:
    return Feature(
        feature_id=feature_id,
        dimension=dimension,
        label=label,
        unit=unit,
        polarity=polarity,
        native_resolution=native,
        higher=higher,
        lower=lower,
    )


_F = FeatureId
_D = Dimension
_N = NativeResolution
_LESS, _MORE, _EITHER = Polarity.LESS, Polarity.MORE, Polarity.EITHER
_PER_1000 = "per 1,000 residents a year"

_FEATURES = (
    _feature(
        _F.CRIME_VIOLENCE_ROBBERY,
        _D.CRIME,
        "Recorded violence and robbery",
        _PER_1000,
        _LESS,
        _N.LSOA,
        "more",
        "less",
    ),
    _feature(
        _F.CRIME_BURGLARY_THEFT,
        _D.CRIME,
        "Recorded burglary and theft",
        _PER_1000,
        _LESS,
        _N.LSOA,
        "more",
        "less",
    ),
    _feature(
        _F.SCHOOL_PRIMARY_NEARBY,
        _D.SCHOOLS,
        "State primary schools within a short walk",
        "count",
        _MORE,
        _N.NETWORK,
        "more",
        "fewer",
    ),
    _feature(
        _F.SCHOOL_PRIMARY_ATTAINMENT,
        _D.SCHOOLS,
        "Pupils meeting the expected standard at nearby primaries",
        "%",
        _MORE,
        _N.POINT,
        "higher",
        "lower",
    ),
    _feature(
        _F.SCHOOL_SECONDARY_ATTAINMENT,
        _D.SCHOOLS,
        "Attainment 8 at nearby secondaries",
        "points",
        _MORE,
        _N.POINT,
        "higher",
        "lower",
    ),
    _feature(
        _F.UNIVERSITY_PROXIMITY,
        _D.SCHOOLS,
        "Distance to the nearest university site",
        "m",
        _LESS,
        _N.POINT,
        "further",
        "closer",
    ),
    _feature(
        _F.GREEN_COVER,
        _D.GREEN_WATER,
        "Public green space as a share of the area",
        "%",
        _MORE,
        _N.POLYGON,
        "greener",
        "less green",
    ),
    _feature(
        _F.PARK_PROXIMITY,
        _D.GREEN_WATER,
        "Walk to the nearest park of 2 ha or more",
        "m",
        _LESS,
        _N.NETWORK,
        "further",
        "closer",
    ),
    _feature(
        _F.PLAY_SPACE_PROXIMITY,
        _D.GREEN_WATER,
        "Walk to the nearest play space",
        "m",
        _LESS,
        _N.NETWORK,
        "further",
        "closer",
    ),
    _feature(
        _F.WATER_ACCESS,
        _D.GREEN_WATER,
        "Share of the area within 300 m of a river or canal",
        "%",
        _MORE,
        _N.POLYGON,
        "more",
        "less",
    ),
    _feature(
        _F.AIR_NO2,
        _D.AIR_NOISE,
        "Modelled annual mean nitrogen dioxide",
        "µg/m³",
        _LESS,
        _N.GRID_1KM,
        "higher",
        "lower",
    ),
    _feature(
        _F.NOISE_EXPOSURE,
        _D.AIR_NOISE,
        "Share of homes at 55 dB or more of transport noise",
        "%",
        _LESS,
        _N.LSOA,
        "noisier",
        "quieter",
    ),
    _feature(
        _F.VENUE_FOOD_DRINK,
        _D.VENUES_CULTURE,
        "Places to eat and drink",
        "per km²",
        _EITHER,
        _N.POINT,
        "more",
        "fewer",
    ),
    _feature(
        _F.VENUE_EVENING,
        _D.VENUES_CULTURE,
        "Pubs, bars and evening venues",
        "per km²",
        _EITHER,
        _N.POINT,
        "more",
        "fewer",
    ),
    _feature(
        _F.VENUE_INDEPENDENT,
        _D.VENUES_CULTURE,
        "Places to eat and drink that are not part of a chain",
        "%",
        _MORE,
        _N.POINT,
        "more",
        "fewer",
    ),
    _feature(
        _F.CULTURE_VENUES,
        _D.VENUES_CULTURE,
        "Theatres, cinemas, galleries, museums, libraries and music venues",
        "per km²",
        _MORE,
        _N.POINT,
        "more",
        "fewer",
    ),
    _feature(
        _F.HIGHSTREET_ACCESS,
        _D.VENUES_CULTURE,
        "Share of homes within a 10-minute walk of a high street or town centre",
        "%",
        _MORE,
        _N.NETWORK,
        "more",
        "less",
    ),
    _feature(
        _F.HOMES_FLATS,
        _D.HOMES,
        "Flats as a share of homes",
        "%",
        _EITHER,
        _N.LSOA,
        "more",
        "fewer",
    ),
    _feature(
        _F.HOMES_PRE1919,
        _D.HOMES,
        "Homes built before 1919",
        "%",
        _EITHER,
        _N.LSOA,
        "more",
        "fewer",
    ),
    _feature(
        _F.HOMES_DENSITY,
        _D.HOMES,
        "Homes per hectare",
        "per ha",
        _EITHER,
        _N.LSOA,
        "denser",
        "less dense",
    ),
    _feature(
        _F.CONSERVATION_COVER,
        _D.HOMES,
        "Share of the area in a conservation area",
        "%",
        _MORE,
        _N.POLYGON,
        "more",
        "less",
    ),
    _feature(
        _F.STATION_WALK,
        _D.STATION_ACCESS,
        "Walk to the nearest station",
        "min",
        _LESS,
        _N.NETWORK,
        "further",
        "closer",
    ),
    _feature(
        _F.STATION_LINES,
        _D.STATION_ACCESS,
        "Lines within a 10-minute walk",
        "count",
        _MORE,
        _N.NETWORK,
        "more",
        "fewer",
    ),
)

FEATURES: Mapping[FeatureId, Feature] = MappingProxyType({f.feature_id: f for f in _FEATURES})


def _tag(tag_id: TagId, label: str, *terms: tuple[int, FeatureId, TermReading]) -> Tag:
    return Tag(
        tag_id=tag_id,
        label=label,
        terms=tuple(
            TagTerm(feature_id=feature_id, hundredths=hundredths, reading=reading)
            for hundredths, feature_id, reading in terms
        ),
    )


_HIGH, _LOW = TermReading.HIGH, TermReading.LOW

_TAGS = (
    _tag(
        TagId.VILLAGE_FEEL,
        "Village feel",
        (30, _F.VENUE_INDEPENDENT, _HIGH),
        (20, _F.HOMES_PRE1919, _HIGH),
        (20, _F.CONSERVATION_COVER, _HIGH),
        (15, _F.HIGHSTREET_ACCESS, _HIGH),
        (15, _F.PARK_PROXIMITY, _LOW),
    ),
    _tag(
        TagId.BUZZY,
        "Buzzy",
        (30, _F.VENUE_FOOD_DRINK, _HIGH),
        (30, _F.VENUE_EVENING, _HIGH),
        (20, _F.CULTURE_VENUES, _HIGH),
        (20, _F.HIGHSTREET_ACCESS, _HIGH),
    ),
    _tag(
        TagId.LEAFY,
        "Leafy",
        (45, _F.GREEN_COVER, _HIGH),
        (30, _F.PARK_PROXIMITY, _LOW),
        (25, _F.HOMES_DENSITY, _LOW),
    ),
    _tag(
        TagId.CREATIVE,
        "Creative",
        (60, _F.CULTURE_VENUES, _HIGH),
        (40, _F.VENUE_INDEPENDENT, _HIGH),
    ),
    _tag(
        TagId.FAMILY_AMENITIES,
        "Family amenities",
        (30, _F.SCHOOL_PRIMARY_NEARBY, _HIGH),
        (25, _F.SCHOOL_PRIMARY_ATTAINMENT, _HIGH),
        (25, _F.PLAY_SPACE_PROXIMITY, _LOW),
        (20, _F.PARK_PROXIMITY, _LOW),
    ),
    _tag(TagId.NEAR_UNIVERSITIES, "Near universities", (100, _F.UNIVERSITY_PROXIMITY, _LOW)),
    _tag(TagId.WATERSIDE, "Waterside", (100, _F.WATER_ACCESS, _HIGH)),
    _tag(
        TagId.STRONG_HIGH_STREET,
        "Strong high street",
        (50, _F.HIGHSTREET_ACCESS, _HIGH),
        (25, _F.VENUE_FOOD_DRINK, _HIGH),
        (25, _F.VENUE_INDEPENDENT, _HIGH),
    ),
    _tag(TagId.EVENING_VENUES, "Evening venues", (100, _F.VENUE_EVENING, _HIGH)),
    _tag(
        TagId.QUIET_RESIDENTIAL,
        "Quiet residential",
        (35, _F.VENUE_EVENING, _LOW),
        (35, _F.NOISE_EXPOSURE, _LOW),
        (15, _F.VENUE_FOOD_DRINK, _LOW),
        (15, _F.HOMES_DENSITY, _LOW),
    ),
    _tag(
        TagId.FOODIE,
        "Foodie",
        (60, _F.VENUE_FOOD_DRINK, _HIGH),
        (40, _F.VENUE_INDEPENDENT, _HIGH),
    ),
    _tag(
        TagId.HISTORIC_CHARACTER,
        "Historic character",
        (50, _F.CONSERVATION_COVER, _HIGH),
        (50, _F.HOMES_PRE1919, _HIGH),
    ),
)

TAGS: Mapping[TagId, Tag] = MappingProxyType({t.tag_id: t for t in _TAGS})


def default_direction(feature_id: FeatureId) -> Direction:
    """The direction a weight takes when nobody chose one: what the polarity gives.

    Where the polarity is `either` it is `more`, because a person who names a
    thing without saying which way usually wants it.
    """
    return Direction.LESS if FEATURES[feature_id].polarity is Polarity.LESS else Direction.MORE


def direction_allowed(feature_id: FeatureId, direction: Direction) -> bool:
    polarity = FEATURES[feature_id].polarity
    return polarity is Polarity.EITHER or polarity.value == direction.value


def percentile_of(
    values: Sequence[float | None], rankable: Sequence[bool]
) -> tuple[float | None, ...]:
    """The mid-rank percentile of each value among the rankable areas that have one.

    Takes one value and one rankable flag for each area, in the same order. This
    is the only implementation, for features and for tags alike. It is a
    percentile of the raw value: polarity is applied at ranking time.

    An area that is not rankable is placed against the rankable ones without
    joining them. If no rankable area has a value there is nothing to be placed
    against, so every percentile is unknown.
    """
    if len(values) != len(rankable):
        raise ValueError("percentile_of needs one rankable flag for each value")
    population = sorted(v for v, r in zip(values, rankable, strict=True) if r and v is not None)
    if not population:
        return tuple(None for _ in values)

    def one(value: float | None) -> float | None:
        if value is None:
            return None
        below = bisect_left(population, value)
        equal = bisect_right(population, value) - below
        return round(100 * (below + 0.5 * equal) / len(population), 1)

    return tuple(one(v) for v in values)


def tag_raw(tag_id: TagId, percentiles: Mapping[FeatureId, float | None]) -> TagRaw:
    """One area's raw value for a tag, from that area's feature percentiles.

    A feature that is absent from `percentiles` counts as missing, as one whose
    percentile is `None` does. Nothing is filled in: the terms that are present
    are reweighted, and below 60 hundredths of the formula the tag is unknown.
    `raw` is rounded to the six decimals a release is written with, so that it
    is the same number before it is written and after it is read.
    """
    present = 0
    total = 0.0
    for term in TAGS[tag_id].terms:
        percentile = percentiles.get(term.feature_id)
        if percentile is None:
            continue
        share = percentile / 100
        total += term.hundredths * (share if term.reading is TermReading.HIGH else 1 - share)
        present += term.hundredths
    raw = round(total / present, 6) if present >= TAG_MIN_COVERAGE_HUNDREDTHS else None
    return TagRaw(raw=raw, coverage=present / 100)
