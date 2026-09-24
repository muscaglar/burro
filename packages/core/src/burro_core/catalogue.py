"""The catalogue: 47 features and the twelve vibes made of them, each describing a place.

A release carries eleven of the twelve: the ten, and the one that gritty is read as.

None describes who lives there (ADR 0006). An id names the idea, not the method:
distances and thresholds live in a release's `definition` and may change with
`CATALOGUE_VERSION`. An id is never renamed, reused or given a new meaning.

On screen a tag is a vibe: a named, published recipe over measured parts. A
part is a feature in a recipe. An area is placed in one of five bands among
the areas compared, and no surface prints a percentage for a vibe (ADR 0013).
Every recipe is checked as this module is imported, so a recipe that breaks
a rule stops the program before it can place anything.
"""

from bisect import bisect_left, bisect_right
from collections.abc import Mapping, Sequence
from types import MappingProxyType

from pydantic import Field

from burro_core._record import Record
from burro_core.ids import (
    Describes,
    Dimension,
    Direction,
    Family,
    FeatureId,
    FeatureKind,
    GrittyVariant,
    Method,
    NativeResolution,
    Polarity,
    TagId,
    TagShape,
    TermReading,
    Toward,
)

# 4 is the catalogue of the vibes once it was joined with the first real builds, and
# said of nitrogen dioxide that it is modelled. 5 names each measure that a real build
# works out for what its file holds.
# 6 names transport noise as a share of residents, which is whose share its file gives: no id and
# no recipe moved.
# 7 names three vibes for what a person would call them: Going out, Houses or flats and Age of
# buildings. No id, end or recipe moved.
# 8 is the catalogue of Gritty as one vibe: the scale that counts recorded crime is named Gritty
# and has the recipe that was decided, and a release that carries it carries Works and warehouses
# beside it.
# 9 is the catalogue of the places to eat and drink as they were decided: the count is named for
# what it counts and is shown, and the places for each 1,000 homes are a feature of their own,
# which a wish is ranked on.
# 10 is the catalogue of Going out without the pubs, which are held back: places to eat and drink
# for each 1,000 homes, high streets and culture.
# 11 holds what homes sell for, the second reading of a word for a smart area.
# 12 names each measure for what its figure is. A distance says it is a straight line, in
# metres, to a play space, a station, a town centre, a GP practice and a pharmacy, and the
# schools are counted within one. Recorded incidents are counted for each 1,000 homes. The
# cultural venues are a count that is shown, and the venues for each 1,000 homes are a
# feature of their own, which a wish is ranked on, as it is for food. Food and drink is
# made of the places for each 1,000 homes. A release that carries Gritty does not carry
# Works and warehouses, which is a part of it.
CATALOGUE_VERSION = 12

# Below this share of a tag's formula, by weight, the tag is unknown for the area.
TAG_MIN_COVERAGE_HUNDREDTHS = 60
# No part may decide a vibe alone: with the coverage rule, a part of this
# many hundredths could place an area with nothing else known.
PART_MAX_HUNDREDTHS = 59
BANDS = 5

# The groups of the settings, in the order they are shown.
FAMILIES: Mapping[Family, str] = MappingProxyType(
    {
        Family.STREETS_HOMES: "Streets and homes",
        Family.PACE_FOOD: "Pace and food",
        Family.GREEN: "Green",
        Family.DAILY_LIFE: "Daily life",
    }
)
# Words a person types that are part place and part judgement. Each is read as
# its place part alone, and the chip quotes the word. It is the lexicon's
# spelling that is quoted, never the text. The list is short, written in one
# place and reviewed as a whole.
MIXED_WORDS: tuple[str, ...] = ("gritty", "edgy", "raw")


class Feature(Record):
    feature_id: FeatureId
    dimension: Dimension
    label: str
    # A plain name of a few words for a form: the wish where the polarity is
    # fixed, the measure where a person may choose the direction.
    short_label: str = Field(min_length=1, max_length=40)
    unit: str
    polarity: Polarity
    native_resolution: NativeResolution
    # The comparatives that fill "X than 80% of areas".
    higher: str
    lower: str
    kind: FeatureKind
    describes: Describes
    # The group of the settings it is shown in. Crime, air and noise are in none.
    family: Family | None
    method: Method
    # Whether likeness between two areas may be counted on it.
    in_likeness: bool


class TagTerm(Record):
    feature_id: FeatureId
    # A whole number of hundredths, so that coverage is compared exactly. A float
    # sum of 0.30, 0.15 and 0.15 must not decide which side of 0.6 it falls.
    hundredths: int = Field(ge=1, le=100)
    reading: TermReading


class Tag(Record):
    tag_id: TagId
    label: str
    short_label: str = Field(min_length=1, max_length=40)
    family: Family
    shape: TagShape
    # The names of the two ends of a scale, low first. A one-way vibe has none.
    low_end: str | None
    high_end: str | None
    meaning: str
    # What the recipe cannot tell. The line every vibe shares comes first.
    cannot_see: tuple[str, ...]
    # Where the vibe may appear: colouring the map, on a result, in a comparison.
    lens: bool
    strip: bool
    table: bool
    # The everyday word shown before a search, and the end it asks for.
    shelf_word: str | None
    shelf_toward: Toward | None
    shelf_order: int | None
    terms: tuple[TagTerm, ...]


class TagRaw(Record):
    raw: float | None
    coverage: float


_F = FeatureId
_D = Dimension
_N = NativeResolution
_K = FeatureKind
_LESS, _MORE, _EITHER = Polarity.LESS, Polarity.MORE, Polarity.EITHER
_PER_1000 = "per 1,000 residents a year"
_PER_1000_HOMES = "per 1,000 homes"
# What was recorded is counted from points, over the homes of the area: a release holds
# no count of residents.
_PER_1000_HOMES_A_YEAR = "per 1,000 homes a year"
_PER_KM2 = "per km²"

_FAMILY_OF: Mapping[Dimension, Family | None] = {
    Dimension.CRIME: None,
    Dimension.AIR_NOISE: None,
    Dimension.HOMES: Family.STREETS_HOMES,
    Dimension.VENUES_CULTURE: Family.PACE_FOOD,
    Dimension.GREEN_WATER: Family.GREEN,
    Dimension.SCHOOLS: Family.DAILY_LIFE,
    Dimension.STATION_ACCESS: Family.DAILY_LIFE,
    Dimension.SERVICES: Family.DAILY_LIFE,
}
_BUILDINGS = frozenset(
    {
        _F.HOMES_FLATS,
        _F.HOMES_PRE1919,
        _F.HOMES_POST2000,
        _F.HOMES_DENSITY,
        _F.CONSERVATION_COVER,
        _F.LISTED_BUILDINGS,
        _F.PRIVATE_OUTDOOR_SPACE,
        _F.PRICE_MEDIAN,
    }
)
# Two nuisances are measured from where homes stand, so each is shown in a
# family of the settings though it is a figure of air and noise.
_SHOWN_IN: Mapping[FeatureId, Family] = {
    _F.ROAD_MAJOR_EXPOSURE: Family.STREETS_HOMES,
    _F.EVENING_CLUSTER_EXPOSURE: Family.PACE_FOOD,
}
# What likeness may never be counted on, whatever kind of thing it is, until
# an audit has passed it (contract, section 7.6).
_HELD_OUT_OF_LIKENESS = frozenset(
    {
        _F.HOMES_FLATS,
        _F.HOMES_DENSITY,
        _F.PRIVATE_OUTDOOR_SPACE,
        _F.SCHOOL_PRIMARY_NEARBY,
        _F.WATER_ACCESS,
        _F.VENUE_INDEPENDENT,
        _F.STATION_LINES,
        _F.CUISINE_VARIETY,
        _F.VENUE_FOOD_DRINK_PER_HOMES,
        _F.CULTURE_VENUES_PER_HOMES,
        _F.PRICE_MEDIAN,
    }
)


def _feature(
    feature_id: FeatureId,
    dimension: Dimension,
    label: str,
    short_label: str,
    unit: str,
    polarity: Polarity,
    native: NativeResolution,
    higher: str,
    lower: str,
    kind: FeatureKind,
    method: Method = Method.MEASURED,
) -> Feature:
    likeable = kind in (FeatureKind.TASTE, FeatureKind.AMENITY)
    return Feature(
        feature_id=feature_id,
        dimension=dimension,
        label=label,
        short_label=short_label,
        unit=unit,
        polarity=polarity,
        native_resolution=native,
        higher=higher,
        lower=lower,
        kind=kind,
        describes=Describes.EVENTS
        if dimension is Dimension.CRIME
        else Describes.BUILDINGS
        if feature_id in _BUILDINGS
        else Describes.PLACE,
        family=_SHOWN_IN.get(feature_id, _FAMILY_OF[dimension]),
        # A figure is said to be measured until a real build finds that it is not.
        method=method,
        in_likeness=likeable and feature_id not in _HELD_OUT_OF_LIKENESS,
    )


_FEATURES = (
    _feature(
        _F.CRIME_VIOLENCE_ROBBERY,
        _D.CRIME,
        "Recorded violence and robbery",
        "Less recorded violence and robbery",
        _PER_1000,
        _LESS,
        _N.LSOA,
        "more",
        "less",
        _K.NUISANCE,
    ),
    _feature(
        _F.CRIME_BURGLARY_THEFT,
        _D.CRIME,
        "Recorded burglary and theft",
        "Less recorded burglary and theft",
        _PER_1000,
        _LESS,
        _N.LSOA,
        "more",
        "less",
        _K.NUISANCE,
    ),
    _feature(
        _F.SCHOOL_PRIMARY_NEARBY,
        _D.SCHOOLS,
        # No network of streets is built, so the schools are counted within a straight
        # line and the name says so, as the distance to a park does.
        "State primary schools within 800 m in a straight line",
        "More primary schools nearby",
        "count",
        _MORE,
        _N.POINT,
        "more",
        "fewer",
        _K.AMENITY,
    ),
    _feature(
        _F.SCHOOL_PRIMARY_ATTAINMENT,
        _D.SCHOOLS,
        "Pupils meeting the expected standard at nearby primaries",
        "Higher primary school results",
        "%",
        _MORE,
        _N.POINT,
        "higher",
        "lower",
        _K.ON_REQUEST,
    ),
    _feature(
        _F.SCHOOL_SECONDARY_ATTAINMENT,
        _D.SCHOOLS,
        "Attainment 8 at nearby secondaries",
        "Higher secondary school results",
        "points",
        _MORE,
        _N.POINT,
        "higher",
        "lower",
        _K.ON_REQUEST,
    ),
    _feature(
        _F.UNIVERSITY_PROXIMITY,
        _D.SCHOOLS,
        "Distance to the nearest university site",
        "Nearer a university",
        "m",
        _LESS,
        _N.POINT,
        "further",
        "closer",
        _K.ON_REQUEST,
    ),
    _feature(
        _F.GREEN_COVER,
        _D.GREEN_WATER,
        # It counts the sites its publisher maps as a public park or garden, and no other
        # green land. So no word of it says green space, or that an area is greener.
        "Public parks and gardens as a share of the area",
        "More public parks and gardens",
        "%",
        _MORE,
        _N.POLYGON,
        "more",
        "less",
        _K.AMENITY,
    ),
    _feature(
        _F.PARK_PROXIMITY,
        _D.GREEN_WATER,
        # No network of streets is built, so the distance is a straight line and the name
        # says so. It is measured to a way in that the publisher marks, from a point.
        "Straight-line distance to the nearest marked way into a park of 2 ha or more",
        "Nearer a park",
        "m",
        _LESS,
        _N.POINT,
        "further",
        "closer",
        _K.AMENITY,
    ),
    _feature(
        _F.PLAY_SPACE_PROXIMITY,
        _D.GREEN_WATER,
        "Straight-line distance to the nearest marked way into a play space",
        "Nearer a play space",
        "m",
        _LESS,
        _N.POINT,
        "further",
        "closer",
        _K.AMENITY,
    ),
    _feature(
        _F.WATER_ACCESS,
        _D.GREEN_WATER,
        # The figure is a share of homes, and it is measured to the line its file draws
        # along the middle of the water, and not to the bank. The file draws a lake too.
        "Share of homes within 300 m, in a straight line, of the centre line of a river, "
        "canal or lake",
        "Nearer a river or canal",
        "%",
        _MORE,
        _N.POLYGON,
        "more",
        "less",
        _K.AMENITY,
    ),
    _feature(
        _F.AIR_NO2,
        _D.AIR_NOISE,
        "Modelled annual mean nitrogen dioxide",
        "Cleaner air",
        "µg/m³",
        _LESS,
        _N.GRID_1KM,
        "higher",
        "lower",
        _K.NUISANCE,
        # Its publisher gives no reading: the figure is a model's, on a grid.
        Method.MODELLED,
    ),
    _feature(
        _F.NOISE_EXPOSURE,
        _D.AIR_NOISE,
        # Its file counts who is exposed, and gives no count of homes, so the name says
        # residents and never homes. It is a measure of the place: how loud it is where
        # people live. It is the one name that says whose share it is (ADR 0006).
        "Share of residents exposed to 55 dB or more of transport noise",
        "Less transport noise",
        "%",
        _LESS,
        _N.LSOA,
        "noisier",
        "quieter",
        _K.NUISANCE,
        # Its publisher gives a share for each small area, with no top and no bottom: an
        # area's figure is the mean of them.
        Method.AVERAGED,
    ),
    _feature(
        _F.VENUE_FOOD_DRINK,
        _D.VENUES_CULTURE,
        # A count within reach of where homes are, and not a walk: no network of streets
        # is built. It is shown and never ranked on: `RANKED_AS`.
        "Places to eat and drink within 800 m of home, in a straight line",
        "Places to eat and drink within reach",
        "count",
        _EITHER,
        _N.POINT,
        "more",
        "fewer",
        _K.TASTE,
    ),
    _feature(
        _F.VENUE_EVENING,
        _D.VENUES_CULTURE,
        "Pubs, bars and evening venues",
        "Pubs and bars",
        _PER_KM2,
        _EITHER,
        _N.POINT,
        "more",
        "fewer",
        _K.TASTE,
    ),
    _feature(
        _F.VENUE_INDEPENDENT,
        _D.VENUES_CULTURE,
        "Places to eat and drink that are not part of a chain",
        "More places that are not chains",
        "%",
        _MORE,
        _N.POINT,
        "more",
        "fewer",
        _K.TASTE,
    ),
    _feature(
        _F.CULTURE_VENUES,
        _D.VENUES_CULTURE,
        # A count within reach of where homes are. It is shown and never ranked on:
        # `RANKED_AS`.
        "Museums, galleries, theatres, cinemas, music venues and libraries within 800 m of "
        "home, in a straight line",
        "Cultural venues within reach",
        "count",
        _MORE,
        _N.POINT,
        "more",
        "fewer",
        _K.AMENITY,
    ),
    _feature(
        _F.HIGHSTREET_ACCESS,
        _D.VENUES_CULTURE,
        # The outlines are of town centres, and a town centre is not a high street: no
        # name of the measure says one. The id is kept, as an id always is.
        "Straight-line distance to the nearest town centre boundary",
        "Nearer a town centre",
        "m",
        _LESS,
        _N.POINT,
        "further",
        "closer",
        _K.AMENITY,
    ),
    _feature(
        _F.HOMES_FLATS,
        _D.HOMES,
        "Flats as a share of homes",
        "Flats",
        "%",
        _EITHER,
        _N.LSOA,
        "more",
        "fewer",
        _K.TASTE,
    ),
    _feature(
        _F.HOMES_PRE1919,
        _D.HOMES,
        "Homes built before 1919",
        "Period homes",
        "%",
        _EITHER,
        _N.LSOA,
        "more",
        "fewer",
        _K.TASTE,
    ),
    _feature(
        _F.HOMES_DENSITY,
        _D.HOMES,
        "Homes per hectare",
        "Homes close together",
        "per ha",
        _EITHER,
        _N.LSOA,
        "denser",
        "less dense",
        _K.TASTE,
    ),
    _feature(
        _F.CONSERVATION_COVER,
        _D.HOMES,
        "Share of the area in a conservation area",
        "More protected streets",
        "%",
        _MORE,
        _N.POLYGON,
        "more",
        "less",
        _K.TASTE,
    ),
    _feature(
        _F.STATION_WALK,
        _D.STATION_ACCESS,
        "Straight-line distance to the nearest way in to a station",
        "Nearer a station",
        "m",
        _LESS,
        _N.POINT,
        "further",
        "closer",
        _K.AMENITY,
    ),
    _feature(
        _F.STATION_LINES,
        _D.STATION_ACCESS,
        "Lines within a 10-minute walk",
        "More lines nearby",
        "count",
        _MORE,
        _N.NETWORK,
        "more",
        "fewer",
        _K.AMENITY,
    ),
    _feature(
        _F.INDEPENDENTS_NEARBY,
        _D.VENUES_CULTURE,
        "Independent places to eat and drink within a 10-minute walk",
        "More independent places nearby",
        "count",
        _MORE,
        _N.NETWORK,
        "more",
        "fewer",
        _K.TASTE,
    ),
    _feature(
        _F.CENTRE_SMALL,
        _D.HOMES,
        "Share of homes whose nearest town centre is a small one",
        "A small town centre",
        "%",
        _MORE,
        _N.POLYGON,
        "more",
        "less",
        _K.TASTE,
    ),
    _feature(
        _F.CENTRE_COMPACT,
        _D.HOMES,
        "Share of the nearest town centre within 200 m of its middle",
        "A compact town centre",
        "%",
        _MORE,
        _N.POLYGON,
        "more",
        "less",
        _K.TASTE,
    ),
    _feature(
        _F.LISTED_BUILDINGS,
        _D.HOMES,
        "Listed buildings",
        "More listed buildings",
        _PER_KM2,
        _MORE,
        _N.POINT,
        "more",
        "fewer",
        _K.TASTE,
    ),
    _feature(
        _F.HOMES_POST2000,
        _D.HOMES,
        "Homes built since 2000",
        "New homes",
        "%",
        _EITHER,
        _N.LSOA,
        "more",
        "fewer",
        _K.TASTE,
    ),
    _feature(
        _F.ROAD_MAJOR_EXPOSURE,
        _D.AIR_NOISE,
        "Share of homes within 100 m of a main road",
        "Away from main roads",
        "%",
        _LESS,
        _N.OA,
        "more",
        "less",
        _K.NUISANCE,
    ),
    _feature(
        _F.EVENING_CLUSTER_EXPOSURE,
        _D.AIR_NOISE,
        "Share of homes within 150 m of a cluster of evening venues",
        "Away from late venues",
        "%",
        _LESS,
        _N.OA,
        "more",
        "less",
        _K.NUISANCE,
    ),
    _feature(
        _F.LAND_INDUSTRY,
        _D.HOMES,
        "Land used for industry",
        "Industrial land",
        "%",
        _EITHER,
        _N.LSOA,
        "more",
        "less",
        _K.TASTE,
    ),
    _feature(
        _F.LAND_STORAGE,
        _D.HOMES,
        "Land used for storage and warehousing",
        "Storage and warehouse land",
        "%",
        _EITHER,
        _N.LSOA,
        "more",
        "less",
        _K.TASTE,
    ),
    _feature(
        _F.LAND_TRANSPORT_OTHER,
        _D.HOMES,
        # Its publisher puts depots and yards under storage, so no name of it says them.
        "Land used for transport other than roads, such as railways, airports and docks",
        "Transport land other than roads",
        "%",
        _EITHER,
        _N.LSOA,
        "more",
        "fewer",
        _K.TASTE,
    ),
    _feature(
        _F.LAND_GARDENS,
        _D.GREEN_WATER,
        "Land that is residential garden",
        "More gardens",
        "%",
        _MORE,
        _N.LSOA,
        "more",
        "less",
        _K.AMENITY,
    ),
    _feature(
        _F.LAND_WOODLAND,
        _D.GREEN_WATER,
        "Land that is woodland",
        "More woodland",
        "%",
        _MORE,
        _N.LSOA,
        "more",
        "less",
        _K.AMENITY,
    ),
    _feature(
        _F.PARK_LARGE_PROXIMITY,
        _D.GREEN_WATER,
        # A straight line, as the distance to any park is.
        "Straight-line distance to the nearest marked way into a park of 20 ha or more",
        "Nearer a large park",
        "m",
        _LESS,
        _N.POINT,
        "further",
        "closer",
        _K.AMENITY,
    ),
    _feature(
        _F.PARK_FACILITIES,
        _D.GREEN_WATER,
        "Kinds of thing to do in parks within a 15-minute walk",
        "More to do in parks",
        "count",
        _MORE,
        _N.NETWORK,
        "more",
        "fewer",
        _K.AMENITY,
    ),
    _feature(
        _F.GROCERY_WALK,
        _D.SERVICES,
        "Walk to the nearest food shop",
        "Nearer a food shop",
        "min",
        _LESS,
        _N.NETWORK,
        "further",
        "closer",
        _K.AMENITY,
    ),
    _feature(
        _F.INCIDENT_CRIMINAL_DAMAGE,
        _D.CRIME,
        # The police's file counts arson with criminal damage.
        "Recorded criminal damage and arson",
        "Less recorded criminal damage",
        _PER_1000_HOMES_A_YEAR,
        _LESS,
        _N.LSOA,
        "more",
        "less",
        _K.NUISANCE,
    ),
    _feature(
        _F.INCIDENT_ANTISOCIAL,
        _D.CRIME,
        "Recorded anti-social behaviour",
        "Less recorded anti-social behaviour",
        _PER_1000_HOMES_A_YEAR,
        _LESS,
        _N.LSOA,
        "more",
        "less",
        _K.NUISANCE,
    ),
    _feature(
        _F.PRIVATE_OUTDOOR_SPACE,
        _D.HOMES,
        "Homes with private outdoor space",
        "More homes with outdoor space",
        "%",
        _MORE,
        _N.LSOA,
        "more",
        "fewer",
        _K.AMENITY,
    ),
    _feature(
        _F.CUISINE_VARIETY,
        _D.VENUES_CULTURE,
        "Kinds of food nearby",
        "More kinds of food",
        "count",
        _MORE,
        _N.POINT,
        "more",
        "fewer",
        _K.TASTE,
    ),
    _feature(
        _F.GP_WALK,
        _D.SERVICES,
        "Straight-line distance to the nearest GP practice, placed by its postcode",
        "Nearer a GP surgery",
        "m",
        _LESS,
        _N.POINT,
        "further",
        "closer",
        _K.AMENITY,
    ),
    _feature(
        _F.PHARMACY_WALK,
        _D.SERVICES,
        "Straight-line distance to the nearest pharmacy, placed by its postcode",
        "Nearer a pharmacy",
        "m",
        _LESS,
        _N.POINT,
        "further",
        "closer",
        _K.AMENITY,
    ),
    _feature(
        _F.VENUE_FOOD_DRINK_PER_HOMES,
        _D.VENUES_CULTURE,
        # What a wish for places to eat and drink is ranked on. Its plain name is the
        # name of the thing, because it is what a person who asks for the thing is given.
        "Places to eat and drink for each 1,000 homes within 800 m, in a straight line",
        "Places to eat and drink",
        _PER_1000_HOMES,
        _EITHER,
        _N.POINT,
        "more",
        "fewer",
        _K.TASTE,
    ),
    # What homes sold for. It was decided on 2026-09-24 that a word for a smart area has
    # two readings, both of the place: the polished end of Gritty, and homes that sell for
    # more than the middle of the city. This is the second. It is a figure of what was
    # paid for homes, and says nothing of who lives somewhere or of what they earn. It is
    # offered and never applied from a word, it stands in no vibe, no likeness is counted
    # on it, and nothing weighs it by default.
    _feature(
        _F.PRICE_MEDIAN,
        _D.HOMES,
        "Median price paid for a home",
        "What homes sell for",
        "£",
        _EITHER,
        _N.MSOA,
        "dearer",
        "cheaper",
        _K.TASTE,
    ),
    _feature(
        _F.CULTURE_VENUES_PER_HOMES,
        _D.VENUES_CULTURE,
        # What a wish for culture is ranked on, as a wish for food is ranked on the places
        # for each 1,000 homes. Its plain name is the name of the wish.
        "Museums, galleries, theatres, cinemas, music venues and libraries for each 1,000 "
        "homes within 800 m, in a straight line",
        "More culture nearby",
        _PER_1000_HOMES,
        _MORE,
        _N.POINT,
        "more",
        "fewer",
        _K.AMENITY,
    ),
)

FEATURES: Mapping[FeatureId, Feature] = MappingProxyType({f.feature_id: f for f in _FEATURES})

# A walk, a time or a distance is what an area gives up only where it is long.
# At or under this figure, in the feature's own unit, it is never a
# trade-off, however many areas are closer still: a trade-off is worse than
# most and bad in itself. Ten minutes on foot is the catalogue's own measure
# of "within a walk": three features count what is within a 10-minute walk.
# In metres it is what a person walks in ten minutes, at 80 m a minute. A
# large park and a campus are fewer and are walked further to: twenty
# minutes. Each is a first figure, chosen by judgement (contract, section 7.5).
# Every distance but the one to a food shop is a straight line, so the walk is
# longer than the figure: the floors were chosen for a walk, and are to be
# looked at again.
_A_WALK_MIN = 10
_A_WALK_M = 800
_A_LONGER_WALK_M = 1_600


def checked_floors(floors: Mapping[FeatureId, float]) -> Mapping[FeatureId, float]:
    """The figures, if every walk, time and distance has one and nothing else has.

    `ValueError` if a measure in minutes or metres has none, or a measure of
    anything else has one: a share or a count is not long or short.
    """
    measured = {f for f, feature in FEATURES.items() if feature.unit in ("min", "m")}
    if set(floors) != measured or any(figure <= 0 for figure in floors.values()):
        raise ValueError(
            "every walk, time and distance has a figure at which it is never a trade-off"
        )
    return MappingProxyType(dict(floors))


NEVER_A_TRADE_OFF: Mapping[FeatureId, float] = checked_floors(
    {
        _F.STATION_WALK: _A_WALK_M,
        _F.GROCERY_WALK: _A_WALK_MIN,
        _F.GP_WALK: _A_WALK_M,
        _F.PHARMACY_WALK: _A_WALK_M,
        _F.HIGHSTREET_ACCESS: _A_WALK_M,
        _F.PARK_PROXIMITY: _A_WALK_M,
        _F.PLAY_SPACE_PROXIMITY: _A_WALK_M,
        _F.PARK_LARGE_PROXIMITY: _A_LONGER_WALK_M,
        _F.UNIVERSITY_PROXIMITY: _A_LONGER_WALK_M,
    }
)

# What is shown and never ranked on, and the measure that is ranked on in its place.
# Decided on 2026-09-24 of the places to eat and drink: the count is a true count, and on
# its own it says little more than that an area is dense and central. So both figures are
# shown, and a wish for the thing is ranked on the places for each 1,000 homes. A release
# that says the count can be ranked on is refused, and a word that names the count is
# read as a wish for what is ranked. The cultural venues are held to the same rule.
RANKED_AS: Mapping[FeatureId, FeatureId] = MappingProxyType(
    {
        _F.VENUE_FOOD_DRINK: _F.VENUE_FOOD_DRINK_PER_HOMES,
        _F.CULTURE_VENUES: _F.CULTURE_VENUES_PER_HOMES,
    }
)

# The features it is a nuisance to have more of. Wanting less of one is caring
# about it. Wanting less of anything else is a wish no weight may be raised for.
NUISANCES: frozenset[FeatureId] = frozenset(
    feature_id for feature_id, feature in FEATURES.items() if feature.kind is FeatureKind.NUISANCE
)
# The one vibe that may hold recorded crime, and the one scale that may hold a
# nuisance: Gritty. A release of London carries it as a made-up release does:
# decided on 2026-09-24 (ADR 0013, as amended).
HOLDS_CRIME = frozenset({TagId.STREET_CHARACTER})

# What is said wherever a figure of recorded crime is said, or offered to be counted.
CRIME_CAVEAT = "Recorded crime depends on what is reported, and locations are approximate."
# The line every vibe says first of what it cannot see.
COMMON_CANNOT_SEE = "One street or one home. An area is many streets."
# What every vibe says of itself, and how its sources are introduced, so that
# no publisher appears to have placed an area.
JUDGEMENT = "The recipe is Burro's own. The weights are a judgement."
MADE_FROM = "Burro's recipe. Made from data published by:"

_HIGH, _LOW = TermReading.HIGH, TermReading.LOW
_Term = tuple[int, FeatureId, TermReading]


def checked_recipe(tag: Tag) -> Tag:
    """The vibe, if its recipe keeps every rule. `ValueError` if it breaks one.

    A recipe sums to 100 hundredths, holds two parts or more and no part
    twice, and holds no part that could place an area alone. No part is
    weighed on request only, and none is shown and never ranked on. No
    recipe holds recorded crime and no scale
    holds a nuisance, but for the one vibe of `HOLDS_CRIME`. A one-way vibe
    reads a nuisance from its low end. A scale names both its ends.
    """
    broken: str | None = None
    parts = [term.feature_id for term in tag.terms]
    features = [FEATURES[feature_id] for feature_id in parts if feature_id in FEATURES]
    scale = tag.shape is TagShape.SCALE
    exempt = tag.tag_id in HOLDS_CRIME
    if sum(term.hundredths for term in tag.terms) != 100:
        broken = "sums to 100 hundredths"
    elif len(tag.terms) < 2 or len(set(parts)) != len(parts):
        broken = "holds two parts or more, each once"
    elif any(term.hundredths > PART_MAX_HUNDREDTHS for term in tag.terms):
        broken = "holds no part of 60 hundredths or more"
    elif len(features) != len(parts):
        broken = "holds features of the catalogue only"
    elif any(feature.kind is FeatureKind.ON_REQUEST for feature in features):
        broken = "holds no part that is weighed on request only"
    elif any(feature_id in RANKED_AS for feature_id in parts):
        broken = "holds no part that is shown and never ranked on"
    elif not exempt and any(feature.dimension is Dimension.CRIME for feature in features):
        broken = "holds no recorded crime"
    elif not exempt and scale and any(f.kind is FeatureKind.NUISANCE for f in features):
        broken = "holds no nuisance, being a scale"
    elif not scale and any(
        term.reading is TermReading.HIGH and FEATURES[term.feature_id].kind is FeatureKind.NUISANCE
        for term in tag.terms
    ):
        broken = "reads a nuisance from its low end"
    if broken is not None:
        raise ValueError(f"the recipe of {tag.tag_id} breaks a rule: a recipe {broken}")
    ends = (tag.low_end, tag.high_end)
    named = all(ends) and tag.low_end != tag.high_end
    if (scale and not named) or (not scale and any(end is not None for end in ends)):
        raise ValueError(f"the ends of {tag.tag_id} are wrong: a scale names two, a one-way none")
    if tag.cannot_see[:1] != (COMMON_CANNOT_SEE,):
        raise ValueError(f"{tag.tag_id} does not say first what every vibe cannot see")
    return tag


def _tag(
    tag_id: TagId,
    label: str,
    family: Family,
    meaning: str,
    cannot_see: str,
    order: int,
    *terms: _Term,
    ends: tuple[str, str] | None = None,
    shelf: str | None = None,
) -> Tag:
    return checked_recipe(
        Tag(
            tag_id=tag_id,
            label=label,
            short_label=label,
            family=family,
            shape=TagShape.SCALE if ends else TagShape.ONE_WAY,
            low_end=ends[0] if ends else None,
            high_end=ends[1] if ends else None,
            meaning=meaning,
            cannot_see=(
                COMMON_CANNOT_SEE,
                *(f"{line.strip()}." for line in cannot_see.split(".") if line.strip()),
            ),
            # Every vibe holds every flag on made-up data, so that the controls
            # can be judged. On real data a flag is earned (ADR 0013).
            lens=True,
            strip=True,
            table=True,
            shelf_word=shelf,
            shelf_toward=Toward.HIGH if shelf else None,
            shelf_order=order,
            terms=tuple(
                TagTerm(feature_id=feature_id, hundredths=hundredths, reading=reading)
                for hundredths, feature_id, reading in terms
            ),
        )
    )


_STREETS, _PACE, _GREEN, _DAILY = (
    Family.STREETS_HOMES,
    Family.PACE_FOOD,
    Family.GREEN,
    Family.DAILY_LIFE,
)
_NOT_UPKEEP = "Whether streets are clean or run down. Empty shops. Graffiti"

# In the order of the shelf, then of "more". Gritty comes last.
_TAGS = (
    _tag(
        TagId.LEAFY,
        "Leafy",
        _GREEN,
        "Gardens, woodland and trees, and a public park near home",
        "Trees under 3 m. Planting or felling since the map was made. Street trees. A wood "
        "that is a public park is counted twice, by woodland and by public parks",
        1,
        (40, _F.LAND_GARDENS, _HIGH),
        (30, _F.LAND_WOODLAND, _HIGH),
        (30, _F.GREEN_COVER, _HIGH),
        shelf="leafy",
    ),
    _tag(
        TagId.VILLAGE_FEEL,
        "Village feel",
        _STREETS,
        "A small, compact centre of its own, historic streets, independent places",
        "Whether neighbours know each other. Which shops there are. Empty units",
        2,
        (25, _F.INDEPENDENTS_NEARBY, _HIGH),
        (20, _F.CENTRE_SMALL, _HIGH),
        (20, _F.CENTRE_COMPACT, _HIGH),
        (20, _F.HOMES_PRE1919, _HIGH),
        (15, _F.CONSERVATION_COVER, _HIGH),
        shelf="villagey",
    ),
    # Pubs and bars were 35 in 100 of it. A check of the register found that pubs alone
    # follow how a council fills it in as much as they follow pubs, so they are held back,
    # and the other three parts are the whole of the recipe in the shares they stood in,
    # to the nearest five. The pubs join when a second source confirms them. The places
    # to eat and drink are those for each 1,000 homes, which a wish for them is ranked on,
    # and so are the cultural venues. A town centre is a distance, read from its near end.
    _tag(
        TagId.PACE,
        "Going out",
        _PACE,
        "How much there is to eat, drink and go out to within reach of homes",
        # Four things, as before: the page of an area draws one line for each.
        "How a weekday differs from a weekend. Who the venues serve. Opening hours and what "
        "is on. Pubs and bars, which are not counted yet",
        3,
        (45, _F.VENUE_FOOD_DRINK_PER_HOMES, _HIGH),
        (30, _F.HIGHSTREET_ACCESS, _LOW),
        (25, _F.CULTURE_VENUES_PER_HOMES, _HIGH),
        ends=("Calm", "Buzzy"),
        shelf="lively",
    ),
    _tag(
        TagId.QUIET_RESIDENTIAL,
        "Quiet streets",
        _STREETS,
        "Homes away from main roads and from clusters of late venues, with little transport noise",
        "Noise from neighbours, venues or works. Which noise is from roads and which from "
        "aircraft. How busy a road is",
        4,
        (40, _F.ROAD_MAJOR_EXPOSURE, _LOW),
        (30, _F.EVENING_CLUSTER_EXPOSURE, _LOW),
        (30, _F.NOISE_EXPOSURE, _LOW),
        shelf="quiet street",
    ),
    _tag(
        TagId.BUILT_AGE,
        "Age of buildings",
        _STREETS,
        "Homes built since 2000 at one end. Period homes, listed buildings and protected "
        "streets at the other",
        "The state of a building. Its inside. An area the conservation data does not "
        "cover is unknown, not zero",
        5,
        (35, _F.HOMES_PRE1919, _HIGH),
        (25, _F.CONSERVATION_COVER, _HIGH),
        (20, _F.LISTED_BUILDINGS, _HIGH),
        (20, _F.HOMES_POST2000, _LOW),
        ends=("Newer", "Historic"),
        shelf="period",
    ),
    _tag(
        TagId.EVERYDAY_ON_FOOT,
        "Everyday on foot",
        _DAILY,
        "A food shop, a town centre, a station, a GP and a pharmacy close to home",
        "Whether a surgery takes new patients. Opening hours. Step-free access at every "
        "station. Which side of a railway a home is on",
        6,
        (25, _F.GROCERY_WALK, _LOW),
        (25, _F.HIGHSTREET_ACCESS, _LOW),
        (20, _F.STATION_WALK, _LOW),
        (15, _F.GP_WALK, _LOW),
        (15, _F.PHARMACY_WALK, _LOW),
        shelf="walkable",
    ),
    _tag(
        TagId.PARKS_CLOSE_BY,
        "Parks close by",
        _GREEN,
        "A park within a walk, a large one not far, and things to do in it",
        "Upkeep. Whether a park is busy. Opening hours. No open rating of parks exists",
        7,
        (40, _F.PARK_PROXIMITY, _LOW),
        (30, _F.PARK_LARGE_PROXIMITY, _LOW),
        (30, _F.PARK_FACILITIES, _HIGH),
        shelf="near a big park",
    ),
    _tag(
        TagId.HOMES,
        "Houses or flats",
        _STREETS,
        "Houses with outdoor space, or flats close together",
        "The size of a home inside. Balconies and front gardens. Whether one home has a garden",
        8,
        (40, _F.HOMES_FLATS, _HIGH),
        (35, _F.HOMES_DENSITY, _HIGH),
        (25, _F.PRIVATE_OUTDOOR_SPACE, _LOW),
        ends=("Houses", "Flats"),
    ),
    _tag(
        TagId.FOODIE,
        "Food and drink",
        _PACE,
        "Many places to eat and drink, many of them independent",
        "Whether the food is good. Prices. Whether a place is still open. Hygiene "
        "ratings are never shown",
        9,
        (40, _F.VENUE_FOOD_DRINK_PER_HOMES, _HIGH),
        (40, _F.INDEPENDENTS_NEARBY, _HIGH),
        (20, _F.CUISINE_VARIETY, _HIGH),
    ),
    _tag(
        TagId.FAMILY_AMENITIES,
        "Family amenities",
        _DAILY,
        "Primary schools, play space and parks nearby",
        "Catchments. School places. What childcare costs. Who lives there",
        10,
        (40, _F.SCHOOL_PRIMARY_NEARBY, _HIGH),
        (35, _F.PLAY_SPACE_PROXIMITY, _LOW),
        (25, _F.PARK_PROXIMITY, _LOW),
    ),
    _tag(
        TagId.WORKS_WAREHOUSES,
        "Works and warehouses",
        _STREETS,
        "Land used for industry, storage and transport, near homes",
        f"{_NOT_UPKEEP}. What the land is used for today. Recorded crime. Who lives there",
        11,
        (40, _F.LAND_INDUSTRY, _HIGH),
        (35, _F.LAND_STORAGE, _HIGH),
        (25, _F.LAND_TRANSPORT_OTHER, _HIGH),
    ),
    # Gritty is one vibe, and an opinion: works and warehouses and what is recorded are
    # six in ten of it. Homes per hectare and nitrogen dioxide were parts and were taken
    # out: each says central and built up, and between them they put a smart district at
    # the gritty end. The weights are a first judgement, for a person to review. The id is
    # the one the scale had when it was called Street character.
    _tag(
        TagId.STREET_CHARACTER,
        "Gritty",
        _STREETS,
        "Works and warehouses, main roads and transport noise, with recorded criminal "
        "damage and anti-social behaviour",
        f"{_NOT_UPKEEP}. Crime that was not reported. Who lives there",
        12,
        (30, _F.INCIDENT_CRIMINAL_DAMAGE, _HIGH),
        (15, _F.LAND_INDUSTRY, _HIGH),
        (15, _F.LAND_STORAGE, _HIGH),
        (15, _F.INCIDENT_ANTISOCIAL, _HIGH),
        (15, _F.ROAD_MAJOR_EXPOSURE, _HIGH),
        (10, _F.NOISE_EXPOSURE, _HIGH),
        ends=("Polished", "Gritty"),
    ),
)

TAGS: Mapping[TagId, Tag] = MappingProxyType({t.tag_id: t for t in _TAGS})

# What the word "gritty" is read as, by what a release carries. Gritty was built two
# ways so that both could be judged, and it was decided that it is one vibe: the scale
# that counts recorded crime. Works and warehouses is a part of it, and is not served
# beside it: as a vibe of its own it is right at the top and wrong as five bands, because
# most areas hold no such land and tie. A release says `b` where it carries Gritty, as
# the committed release and a build of London do. It says `a` where it holds no recorded
# crime, and there it carries Works and warehouses in the place of Gritty.
GRITTY: Mapping[GrittyVariant, TagId] = MappingProxyType(
    {GrittyVariant.A: TagId.WORKS_WAREHOUSES, GrittyVariant.B: TagId.STREET_CHARACTER}
)


def tags_of(variant: GrittyVariant) -> tuple[Tag, ...]:
    """The vibes a release of this variant carries, in the order of the shelf and of "more".

    It carries the ten, and the one that gritty is read as there. It never
    carries both.
    """
    left_out = frozenset(GRITTY.values()) - {GRITTY[variant]}
    return tuple(tag for tag in TAGS.values() if tag.tag_id not in left_out)


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


def band_of(values: Sequence[float | None], rankable: Sequence[bool]) -> tuple[int | None, ...]:
    """The band of each value, 1 to 5, among the rankable areas that have one.

    `band = 1 + min(4, (5 * below) // compared)`, where `compared` is the
    rankable areas with a value and `below` how many of them are strictly
    lower. So areas that are level share a band, and none counts as below
    another. It is counted in whole areas, so no float decides a band. This
    is the only implementation, for vibes and for parts. No polarity is
    applied: band 1 is the low end of the figure.

    An area that is not rankable is banded against the rankable ones without
    joining them, as its percentile is. If no rankable area has a value
    every band is unknown.
    """
    if len(values) != len(rankable):
        raise ValueError("band_of needs one rankable flag for each value")
    population = sorted(v for v, r in zip(values, rankable, strict=True) if r and v is not None)
    if not population:
        return tuple(None for _ in values)

    def one(value: float | None) -> int | None:
        if value is None:
            return None
        below = bisect_left(population, value)
        return 1 + min(BANDS - 1, (BANDS * below) // len(population))

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
