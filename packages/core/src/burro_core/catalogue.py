"""The catalogue: 113 features and the fifteen vibes made of them.

A release carries fourteen of the fifteen: the thirteen, and the one that gritty is
read as.

Every feature describes a place, its buildings or what was recorded there, but for four,
which describe who lived there at Census 2021: the age of residents and what households were
made of, and nothing else about them (ADR 0006, as amended on 2026-09-24). Each of the
four says so in its name, is asked for towards more of what it counts and never
towards fewer, stands in no scale, and counts towards no likeness. Two vibes hold one.
An id names the idea, not the method: distances and thresholds live in a release's
`definition` and may change with `CATALOGUE_VERSION`. An id is never renamed, reused or
given a new meaning.

On screen a tag is a vibe: a named, published recipe over measured parts. A
part is a feature in a recipe. An area is placed in one of five bands among
the areas compared, and no surface prints a percentage for a vibe (ADR 0013).
Every recipe is checked as this module is imported, so a recipe that breaks
a rule stops the program before it can place anything.
"""

from bisect import bisect_left, bisect_right
from collections.abc import Iterable, Mapping, Sequence
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
    Sureness,
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
# 13 holds cafes, gyms and pubs, each as a count that is shown and a figure for each 1,000
# homes that a wish is ranked on. Pubs and bars are counted from the file of places, and are
# 35 in 100 of Going out again. The homes near a cluster of pubs and bars are named for what
# is counted: three or more within 150 m. It names the food shop as it is built: a straight
# line in metres, to the nearest place its file gives as a grocer, a supermarket or a
# convenience store. Everyday on foot says that each of its distances is a straight line,
# what is not known of a shop, and that it is mostly a map of how built up a place is: on
# London its order is mostly that of homes to the hectare. It holds the chains of grocers,
# gyms and coffee: the places of each tier within reach and the distance to the nearest, the
# mix of tiers, which is what is ranked on, and the distance to the nearest place of each
# chain a person may name. Independent places are named for what is measured: a share of
# the places to eat and drink within reach, in a straight line. With them Village feel holds
# 60 in 100 of its recipe, and it places an area only where something of its town centre has
# a figure. It holds Well connected, and the four measures it is made of: how far the
# nearest station of the Underground or the DLR is, how far the nearest of the Overground or
# the Elizabeth line, how far the nearest National Rail station or tram stop, and how many
# routes of a bus stop within 400 m of home. Each counts how near stops are, and nothing of
# how often anything runs from them. The stops of buses are a count that is shown, and a
# wish for buses is ranked on the routes. It holds the four measures of who lived in an area
# at Census 2021, and the two vibes that count one: Family area and Young professionals.
# Family amenities says that it counts places alone. It holds three figures of the homes of
# a place: the share of homes in the higher council tax bands, which is a reading of a word
# for a smart area, and how far what homes sold for has risen over five years and over ten.
# None stands in a vibe or in likeness. It names private outdoor space for what its file
# counts: a share of addresses, by MSOA. Its publisher counts addresses and says nothing of
# what it takes for a home. It is one number for what several streams of work each added
# on 2026-09-24.
# 14 is the catalogue of Village feel as the founder chose to serve it, on 2026-09-25. It
# holds the measure of how much of the high street nearest a home lies in a conservation
# area, which a build of London works out and no likeness counts. Village feel is made of
# it, of homes per hectare read from the low end, of homes built before 1919 and of
# conservation cover, and of no part for the size or the shape of a town centre or for
# independent places. A vibe says whether it is as sure as the rest or a rough guide, and
# Village feel is the one rough guide: it is on a result only where it was asked for. No
# vibe is held off.
CATALOGUE_VERSION = 14

# Below this share of a tag's formula, by weight, the tag is unknown for the area.
TAG_MIN_COVERAGE_HUNDREDTHS = 60
# No part may decide a vibe alone: with the coverage rule, a part of this
# many hundredths could place an area with nothing else known.
PART_MAX_HUNDREDTHS = 59
# In a vibe that counts who lives somewhere no part carries more than this, so that it is
# never one census figure under a vibe's name.
PART_MAX_WHERE_RESIDENTS_COUNT = 40
# What the name of a measure that counts residents ends with, and what the meaning of a
# vibe that holds one says: who was counted is who was counted at this census.
CENSUS_SAID = "Census 2021"
BANDS = 5

# The groups of the settings, in the order they are shown.
FAMILIES: Mapping[Family, str] = MappingProxyType(
    {
        Family.STREETS_HOMES: "Streets and homes",
        Family.PACE_FOOD: "Pace and food",
        Family.GREEN: "Green",
        Family.DAILY_LIFE: "Daily life",
        Family.WHO_LIVES_THERE: "Who lives there, at the 2021 census",
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
    # Whether the vibe is as sure as the rest, or a rough guide. A vibe that does not say
    # is as sure as the rest. A rough guide says so wherever it is shown, with why.
    sureness: Sureness = Sureness.AS_THE_REST


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
    Dimension.BRANDS: Family.DAILY_LIFE,
    Dimension.RESIDENTS: Family.WHO_LIVES_THERE,
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
        _F.HOMES_HIGHER_BANDS,
        _F.PRICE_RISE_5Y,
        _F.PRICE_RISE_10Y,
        _F.HIGHSTREET_CONSERVED,
    }
)
# Two nuisances are measured from where homes stand, so each is shown in a
# family of the settings though it is a figure of air and noise.
_SHOWN_IN: Mapping[FeatureId, Family] = {
    _F.ROAD_MAJOR_EXPOSURE: Family.STREETS_HOMES,
    _F.EVENING_CLUSTER_EXPOSURE: Family.PACE_FOOD,
}
# The three kinds of place the table of tiers holds, as a label says one and many of each,
# and the three tiers, as a label says each. A place of coffee is a coffee shop, a bakery
# or a sandwich shop of a chain: what the founder's table puts under coffee.
KINDS_OF_CHAIN: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        "grocer": ("grocer", "grocers"),
        "gym": ("gym", "gyms"),
        "coffee": ("coffee place", "coffee places"),
    }
)
TIERS: Mapping[str, str] = MappingProxyType(
    {"premium": "premium", "mid": "mid-range", "value": "value"}
)
# The two measures of each kind of place of each tier: how many are within reach, and how
# far the nearest is.
NEARBY, DISTANCE = "nearby", "distance"


def of_a_tier(kind: str, tier: str, what: str) -> FeatureId:
    """The measure of one kind of place of one tier: how many, or how far the nearest."""
    return FeatureId(f"{kind}_{tier}_{what}")


# The measures of the tiers, which are shown and which no release ranks an area on: the
# mix is what is ranked on. A release switches each off, as it may any feature.
SHOWN_BESIDE_THE_MIX: frozenset[FeatureId] = frozenset(
    of_a_tier(kind, tier, what)
    for kind in KINDS_OF_CHAIN
    for tier in TIERS
    for what in (NEARBY, DISTANCE)
)
# What likeness is not counted on, whatever kind of thing it is (contract,
# section 7.6). Each was held out until an audit had passed it. No audit is run
# since 2026-09-25, when the proxy audit was dropped (ADR 0006), and each stays
# out: whether one joins is the founder's to decide.
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
        # New, and held out as the others are.
        _F.VENUE_CAFE,
        _F.VENUE_CAFE_PER_HOMES,
        _F.VENUE_GYM,
        _F.VENUE_GYM_PER_HOMES,
        _F.VENUE_EVENING_PER_HOMES,
        # Which chains stand in a place may follow what homes there sell for, so no
        # likeness is counted on a tier or on the mix.
        _F.BRAND_MIX,
        *SHOWN_BESIDE_THE_MIX,
        # How near stops are follows how built up a place is. Held out, as the count
        # of lines is.
        _F.UNDERGROUND_PROXIMITY,
        _F.OVERGROUND_PROXIMITY,
        _F.RAIL_PROXIMITY,
        _F.BUS_STOPS_NEARBY,
        _F.BUS_ROUTES_NEARBY,
        _F.HOMES_HIGHER_BANDS,
        _F.PRICE_RISE_5Y,
        _F.PRICE_RISE_10Y,
        # The heaviest part of Village feel, which is a rough guide. What a rough guide
        # rests on is used to work out nothing else: decided on 2026-09-25.
        _F.HIGHSTREET_CONSERVED,
    }
)


def _describes(feature_id: FeatureId, dimension: Dimension) -> Describes:
    if dimension is Dimension.RESIDENTS:
        return Describes.RESIDENTS
    if dimension is Dimension.CRIME:
        return Describes.EVENTS
    return Describes.BUILDINGS if feature_id in _BUILDINGS else Describes.PLACE


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
    # Two areas are never said to be alike for who lives in them: what counts residents is
    # of neither kind, so no likeness is counted on it.
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
        describes=_describes(feature_id, dimension),
        family=_SHOWN_IN.get(feature_id, _FAMILY_OF[dimension]),
        # A figure is said to be measured until a real build finds that it is not.
        method=method,
        in_likeness=likeable and feature_id not in _HELD_OUT_OF_LIKENESS,
    )


# The chains of grocers, gyms and coffee. Decided by the founder on 2026-09-24 (ADR 0026).
#
# Which chain is of which tier is the founder's judgement, and a person adjusts it: so it
# is data of the pipeline's, in one reviewed file, and core holds none of it. Core names a
# tier, and the release says in the definition of each measure which chains were counted
# in it. Core names a chain, so that a person can ask for one and a page can name it, and
# says nothing of what tier it is of.
#
# How far a place may be to be counted, and how far the nearest is looked for. The first is
# the reach of every measure of places. The second is as far as the part of the file that
# is taken is known to hold every place round every home.
WITHIN_M = 800
NEAREST_WITHIN_M = 2_000


class Chain(Record):
    """A chain a person may name: its name, and how a label says the nearest place of it."""

    feature_id: FeatureId
    # As Burro says it, which is as the founder's table writes it.
    name: str
    # The name with its article, for the wish: "a Waitrose", "an Aldi". A name that
    # holds its own article has no other.
    one: str
    # What the distance is to the nearest of, where the name alone would not read.
    nearest: str


def _chain(feature_id: FeatureId, name: str, one: str | None = None, nearest: str = "") -> Chain:
    return Chain(
        feature_id=feature_id,
        name=name,
        one=f"a {name}" if one is None else one,
        nearest=nearest or name,
    )


# In the order of the founder's table: grocers, gyms and coffee, each from premium to value.
_CHAINS = (
    _chain(_F.BRAND_WAITROSE, "Waitrose"),
    _chain(_F.BRAND_MANDS, "M&S", "an M&S"),
    _chain(_F.BRAND_WHOLE_FOODS, "Whole Foods"),
    _chain(_F.BRAND_SAINSBURYS, "Sainsbury's"),
    _chain(_F.BRAND_TESCO, "Tesco"),
    _chain(_F.BRAND_COOP, "Co-op"),
    _chain(_F.BRAND_MORRISONS, "Morrisons"),
    _chain(_F.BRAND_ASDA, "Asda", "an Asda"),
    _chain(_F.BRAND_ALDI, "Aldi", "an Aldi"),
    _chain(_F.BRAND_LIDL, "Lidl"),
    _chain(_F.BRAND_ICELAND, "Iceland", "an Iceland"),
    _chain(_F.BRAND_EQUINOX, "Equinox", "an Equinox"),
    _chain(_F.BRAND_THIRD_SPACE, "Third Space"),
    _chain(_F.BRAND_BARRYS, "Barry's"),
    _chain(_F.BRAND_VIRGIN_ACTIVE, "Virgin Active"),
    _chain(_F.BRAND_NUFFIELD, "Nuffield"),
    _chain(_F.BRAND_GYMBOX, "Gymbox"),
    _chain(_F.BRAND_DAVID_LLOYD, "David Lloyd"),
    _chain(_F.BRAND_ANYTIME_FITNESS, "Anytime Fitness", "an Anytime Fitness"),
    _chain(_F.BRAND_PUREGYM, "PureGym"),
    _chain(_F.BRAND_THE_GYM_GROUP, "The Gym Group", "The Gym Group", "gym of The Gym Group"),
    _chain(_F.BRAND_GAILS, "Gail's"),
    _chain(_F.BRAND_OLE_AND_STEEN, "Ole & Steen", "an Ole & Steen"),
    _chain(_F.BRAND_PRET, "Pret"),
    _chain(_F.BRAND_NERO, "Nero"),
    _chain(_F.BRAND_STARBUCKS, "Starbucks"),
    _chain(_F.BRAND_COSTA, "Costa"),
    _chain(_F.BRAND_BLANK_STREET, "Blank Street"),
    _chain(_F.BRAND_GREGGS, "Greggs"),
)
CHAINS: Mapping[FeatureId, Chain] = MappingProxyType({c.feature_id: c for c in _CHAINS})

_BY_THE_TABLE = "by Burro's table of tiers"


def _tiered(kind: str, tier: str) -> tuple[Feature, Feature]:
    """The two measures of one kind of place of one tier: how many, and how far the nearest."""
    one, many = KINDS_OF_CHAIN[kind]
    said = TIERS[tier]
    return (
        _feature(
            of_a_tier(kind, tier, NEARBY),
            _D.BRANDS,
            f"{said.capitalize()} {many} within {WITHIN_M} m of home, in a straight line, "
            f"{_BY_THE_TABLE}",
            f"{said.capitalize()} {many} within reach",
            "count",
            _MORE,
            _N.POINT,
            "more",
            "fewer",
            _K.AMENITY,
        ),
        _feature(
            of_a_tier(kind, tier, DISTANCE),
            _D.BRANDS,
            f"Straight-line distance to the nearest {said} {one} within "
            f"{NEAREST_WITHIN_M:,} m of home, {_BY_THE_TABLE}",
            f"Nearer a {said} {one}",
            "m",
            _LESS,
            _N.POINT,
            "further",
            "closer",
            _K.AMENITY,
        ),
    )


_PAIRS = tuple(_tiered(kind, tier) for kind in KINDS_OF_CHAIN for tier in TIERS)
_OF_THE_TIERS = (*(pair[0] for pair in _PAIRS), *(pair[1] for pair in _PAIRS))
# The mix: of the places of a tier within reach, the share that are premium, with a
# mid-range place counted as half. So it runs from 0, where every one is value, to 100,
# where every one is premium. It is the first reading of a word for a smart area. It is a
# figure of which shops stand in a place, and never of who lives there or of what they earn.
# It is offered and never applied from a word, it stands in no vibe, no likeness is
# counted on it, and nothing weighs it by default.
_THE_MIX = _feature(
    _F.BRAND_MIX,
    _D.BRANDS,
    f"Share of the chain grocers, gyms and coffee places within {WITHIN_M} m of home that "
    f"are premium, with a mid-range one counted as half, {_BY_THE_TABLE}",
    "Mix of brands",
    "%",
    _EITHER,
    _N.POINT,
    "more premium",
    "less premium",
    _K.TASTE,
)
# The distance to the nearest place of one chain. It is weighed only where a person asks
# for the chain by its name, so it is in no vibe and no likeness, and it runs one way: a
# person may ask to be near a chain, and never to be far from one.
_OF_THE_CHAINS = tuple(
    _feature(
        chain.feature_id,
        _D.BRANDS,
        f"Straight-line distance to the nearest {chain.nearest} within "
        f"{NEAREST_WITHIN_M:,} m of home",
        f"Nearer {chain.one}",
        "m",
        _LESS,
        _N.POINT,
        "further",
        "closer",
        _K.ON_REQUEST,
    )
    for chain in _CHAINS
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
        # A count within reach of where homes are, from the file of places. It is shown
        # and never ranked on: `RANKED_AS`. A nightclub is not counted.
        "Pubs and bars within 800 m of home, in a straight line",
        "Pubs and bars within reach",
        "count",
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
        # A share of the places within reach, and not a count of them: a count says how
        # much is about, and the share says what kind of place it is. It is measured in a
        # straight line, and a place is independent where its file names no chain for it.
        "Share of the places to eat and drink within 800 m of home, in a straight line, "
        "that belong to no chain",
        "More independent places nearby",
        "%",
        _MORE,
        _N.POINT,
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
        # A cluster is three or more, and the file of places cannot say how late one is
        # open. So the name says pubs and bars, and says how many.
        "Share of homes with three or more pubs or bars within 150 m, in a straight line",
        "Away from clusters of pubs and bars",
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
        # A straight line, as every distance is. A food shop is a place its file gives as
        # a grocer, a supermarket or a convenience store: the definition of a release
        # says which. The id says a walk, because an id is never renamed.
        "Straight-line distance to the nearest food shop",
        "Nearer a food shop",
        "m",
        _LESS,
        _N.POINT,
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
        "Addresses with private outdoor space",
        "More addresses with outdoor space",
        "%",
        _MORE,
        _N.MSOA,
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
    # Cafes, gyms and pubs are counted from the file of places, as the cultural venues
    # are, and held to the same rule: the count is shown, and a wish is ranked on the
    # figure for each 1,000 homes.
    _feature(
        _F.VENUE_CAFE,
        _D.VENUES_CULTURE,
        "Cafes and coffee shops within 800 m of home, in a straight line",
        "Cafes within reach",
        "count",
        _MORE,
        _N.POINT,
        "more",
        "fewer",
        _K.AMENITY,
    ),
    _feature(
        _F.VENUE_CAFE_PER_HOMES,
        _D.VENUES_CULTURE,
        "Cafes and coffee shops for each 1,000 homes within 800 m, in a straight line",
        "More cafes nearby",
        _PER_1000_HOMES,
        _MORE,
        _N.POINT,
        "more",
        "fewer",
        _K.AMENITY,
    ),
    _feature(
        _F.VENUE_GYM,
        _D.VENUES_CULTURE,
        "Gyms and fitness studios within 800 m of home, in a straight line",
        "Gyms within reach",
        "count",
        _MORE,
        _N.POINT,
        "more",
        "fewer",
        _K.AMENITY,
    ),
    _feature(
        _F.VENUE_GYM_PER_HOMES,
        _D.VENUES_CULTURE,
        "Gyms and fitness studios for each 1,000 homes within 800 m, in a straight line",
        "More gyms nearby",
        _PER_1000_HOMES,
        _MORE,
        _N.POINT,
        "more",
        "fewer",
        _K.AMENITY,
    ),
    _feature(
        _F.VENUE_EVENING_PER_HOMES,
        _D.VENUES_CULTURE,
        # What a wish for pubs and bars is ranked on, and what Going out holds. A person
        # may want fewer, so its plain name is the name of the thing.
        "Pubs and bars for each 1,000 homes within 800 m, in a straight line",
        "Pubs and bars",
        _PER_1000_HOMES,
        _EITHER,
        _N.POINT,
        "more",
        "fewer",
        _K.TASTE,
    ),
    *_OF_THE_TIERS,
    _THE_MIX,
    *_OF_THE_CHAINS,
    # The four parts of Well connected. Each is a straight line from where homes are
    # taken to stand, and says so. None says how often anything runs, where it goes or how
    # long a journey takes: no timetable is held.
    _feature(
        _F.UNDERGROUND_PROXIMITY,
        _D.STATION_ACCESS,
        "Straight-line distance to the nearest Underground or DLR station",
        "Nearer the Underground or DLR",
        "m",
        _LESS,
        _N.POINT,
        "further",
        "closer",
        _K.AMENITY,
    ),
    _feature(
        _F.OVERGROUND_PROXIMITY,
        _D.STATION_ACCESS,
        # The national file of stops gives one kind of railway station, whoever runs its
        # trains. Which of them the Overground or the Elizabeth line calls at is read from
        # the file of Transport for London, which names the modes at each of its stations.
        "Straight-line distance to the nearest Overground or Elizabeth line station",
        "Nearer the Overground or Elizabeth line",
        "m",
        _LESS,
        _N.POINT,
        "further",
        "closer",
        _K.AMENITY,
    ),
    _feature(
        _F.RAIL_PROXIMITY,
        _D.STATION_ACCESS,
        # A railway station at which no more than the Overground or the Elizabeth line
        # calls is not one of these. A tram stop is counted with them.
        "Straight-line distance to the nearest National Rail station or tram stop",
        "Nearer National Rail or a tram stop",
        "m",
        _LESS,
        _N.POINT,
        "further",
        "closer",
        _K.AMENITY,
    ),
    _feature(
        _F.BUS_STOPS_NEARBY,
        _D.STATION_ACCESS,
        # A stop on each side of a road is two stops, and a stop says nothing of how many
        # buses call at it. So the count is shown and never ranked on: `RANKED_AS`.
        "Bus stops within 400 m of home, in a straight line",
        "Bus stops nearby",
        "count",
        _MORE,
        _N.POINT,
        "more",
        "fewer",
        _K.AMENITY,
    ),
    _feature(
        _F.BUS_ROUTES_NEARBY,
        _D.STATION_ACCESS,
        # What a wish for buses is ranked on: how many different routes stop near home, and
        # not how many stops there are.
        "Bus routes that stop within 400 m of home, in a straight line",
        "More bus routes nearby",
        "count",
        _MORE,
        _N.POINT,
        "more",
        "fewer",
        _K.AMENITY,
    ),
    # Who lived in an area at Census 2021. It was decided on 2026-09-24 that the age of
    # residents and what households are made of may feed a vibe and a ranking, and that
    # nothing else about residents may (ADR 0006). Each name says who is counted and in
    # which census. Each is a share in 100: a release holds no count of people. A person may
    # ask for more of what one counts and never for fewer, so each has the one direction.
    # None is weighed until a person asks, and no word applies one: it is offered.
    _feature(
        _F.RESIDENTS_AGED_20_34,
        _D.RESIDENTS,
        f"Residents aged 20 to 34 as a share of all residents, {CENSUS_SAID}",
        # A few words for a form hold no figure, so the ages are said in the name above.
        "More young adults",
        "%",
        _MORE,
        _N.OA,
        "more",
        "fewer",
        _K.RESIDENTS,
    ),
    _feature(
        _F.RESIDENTS_AGED_65_OVER,
        _D.RESIDENTS,
        f"Residents aged 65 and over as a share of all residents, {CENSUS_SAID}",
        "More older residents",
        "%",
        _MORE,
        _N.OA,
        "more",
        "fewer",
        _K.RESIDENTS,
    ),
    _feature(
        _F.HOUSEHOLDS_DEPENDENT_CHILDREN,
        _D.RESIDENTS,
        f"Households with dependent children as a share of all households, {CENSUS_SAID}",
        "More households with children",
        "%",
        _MORE,
        _N.OA,
        "more",
        "fewer",
        _K.RESIDENTS,
    ),
    _feature(
        _F.HOUSEHOLDS_ONE_PERSON,
        _D.RESIDENTS,
        f"Households of one person as a share of all households, {CENSUS_SAID}",
        "More households of one person",
        "%",
        _MORE,
        _N.OA,
        "more",
        "fewer",
        _K.RESIDENTS,
    ),
    # The homes of a place by their council tax band. A band is what a home was taken to be
    # worth in 1991, so the share says which homes stand in a place and nothing of what one
    # would sell for today. It counts homes and not people: it is offered for a word for a
    # smart area, and never applied, it stands in no vibe, and no likeness is counted on it.
    _feature(
        _F.HOMES_HIGHER_BANDS,
        _D.HOMES,
        "Homes in council tax bands E to H as a share of homes",
        "Homes in the higher council tax bands",
        "%",
        _EITHER,
        _N.MSOA,
        "more",
        "fewer",
        _K.TASTE,
    ),
    # How far what homes sold for has risen. It is the middle price now for each £100 of the
    # middle price then, so it is never below nought, and a fall reads under £100. It is
    # offered for a word for a place on the rise, and never applied. It says what was paid,
    # and promises nothing of what will be.
    _feature(
        _F.PRICE_RISE_5Y,
        _D.HOMES,
        "Median price paid for a home, for each £100 of the median five years before",
        "Price rise over five years",
        "£",
        _EITHER,
        _N.MSOA,
        "a steeper rise",
        "a smaller rise",
        _K.TASTE,
    ),
    _feature(
        _F.PRICE_RISE_10Y,
        _D.HOMES,
        "Median price paid for a home, for each £100 of the median ten years before",
        "Price rise over ten years",
        "£",
        _EITHER,
        _N.MSOA,
        "a steeper rise",
        "a smaller rise",
        _K.TASTE,
    ),
    # How much of the high street nearest a home lies inside a conservation area, as the
    # mean over an area's homes. It counts land inside a line a planning authority drew,
    # so it cannot tell a village street from a main road through old streets. It was
    # measured for Village feel, and is the heaviest part of it.
    _feature(
        _F.HIGHSTREET_CONSERVED,
        _D.HOMES,
        "Share of the nearest high street that lies in a conservation area",
        "A high street in a conservation area",
        "%",
        _MORE,
        _N.POLYGON,
        "more",
        "less",
        _K.TASTE,
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
# Every distance is a straight line, so the walk is longer than the figure: the
# floors were chosen for a walk, and are to be looked at again. The floor of a station
# was looked at on 2026-09-25, and stands: `NEAR_A_STATION`, below.
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
        _F.GROCERY_WALK: _A_WALK_M,
        _F.GP_WALK: _A_WALK_M,
        _F.PHARMACY_WALK: _A_WALK_M,
        _F.HIGHSTREET_ACCESS: _A_WALK_M,
        _F.PARK_PROXIMITY: _A_WALK_M,
        _F.PLAY_SPACE_PROXIMITY: _A_WALK_M,
        _F.PARK_LARGE_PROXIMITY: _A_LONGER_WALK_M,
        _F.UNIVERSITY_PROXIMITY: _A_LONGER_WALK_M,
        # A shop, a gym or a coffee within what a person walks in ten minutes is near.
        **{f.feature_id: _A_WALK_M for f in _OF_THE_TIERS if f.unit == "m"},
        **dict.fromkeys(CHAINS, _A_WALK_M),
        _F.UNDERGROUND_PROXIMITY: _A_WALK_M,
        _F.OVERGROUND_PROXIMITY: _A_WALK_M,
        _F.RAIL_PROXIMITY: _A_WALK_M,
    }
)

# What near means of a station. The founder decided on 2026-09-25 that near a station
# is about a 10 to 15 minute walk. The measure is a straight line, and a straight line
# of 800 m is a walk of about that. So the figure at or under which the distance is
# never a trade-off is what near means, and no figure moved: an offer of the measure
# says so, after what is counted. The measure itself is named a straight line, in
# metres, and never a walk. It is said of a station and of no other distance.
NEAR_A_STATION = (
    f"Within {NEVER_A_TRADE_OFF[_F.STATION_WALK]:.0f} m in a straight line is about "
    "a 10 to 15 minute walk."
)

# What is shown and never ranked on, and the measure that is ranked on in its place.
# Decided on 2026-09-24 of the places to eat and drink: the count is a true count, and on
# its own it says little more than that an area is dense and central. So both figures are
# shown, and a wish for the thing is ranked on the places for each 1,000 homes. A release
# that says the count can be ranked on is refused, and a word that names the count is
# read as a wish for what is ranked. The cultural venues are held to the same rule, and so
# are the cafes, the gyms and the pubs and bars.
RANKED_AS: Mapping[FeatureId, FeatureId] = MappingProxyType(
    {
        _F.VENUE_FOOD_DRINK: _F.VENUE_FOOD_DRINK_PER_HOMES,
        _F.CULTURE_VENUES: _F.CULTURE_VENUES_PER_HOMES,
        _F.VENUE_CAFE: _F.VENUE_CAFE_PER_HOMES,
        _F.VENUE_GYM: _F.VENUE_GYM_PER_HOMES,
        _F.VENUE_EVENING: _F.VENUE_EVENING_PER_HOMES,
        # Asked for on 2026-09-24: the routes that stop near a home, and not the stops alone.
        _F.BUS_STOPS_NEARBY: _F.BUS_ROUTES_NEARBY,
    }
)

# The features it is a nuisance to have more of. Wanting less of one is caring
# about it. Wanting less of anything else is a wish no weight may be raised for.
NUISANCES: frozenset[FeatureId] = frozenset(
    feature_id for feature_id, feature in FEATURES.items() if feature.kind is FeatureKind.NUISANCE
)
# The features that count who lived somewhere. Each is read from its high end in a recipe,
# stands in no scale, is offered and never applied from a word, and is offered one way.
COUNTS_RESIDENTS: frozenset[FeatureId] = frozenset(
    feature_id
    for feature_id, feature in FEATURES.items()
    if feature.describes is Describes.RESIDENTS
)
# The measures that rest on the conservation areas. Their publisher asks that its data
# never decides a vibe alone, so the parts of a recipe that rest on it come to under 60
# in 100 together: with nothing else known of an area, no vibe places it.
ON_CONSERVATION_AREAS: frozenset[FeatureId] = frozenset(
    {_F.CONSERVATION_COVER, _F.HIGHSTREET_CONSERVED}
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
# What a vibe that is a rough guide says of itself wherever it is shown: one short label,
# and one sentence that says why. The founder decided on 2026-09-25 that Village feel is
# served though it did not reach the bar they had set, and that it must say it is less
# sure than the other vibes (ADR 0013, as amended). Every surface says both, word for
# word, in sight and not behind a press. The sentence gives no figure that a build could
# make false, and names no place.
ROUGH_GUIDE = "Rough guide"
WHY_A_ROUGH_GUIDE: Mapping[TagId, str] = MappingProxyType(
    {
        TagId.VILLAGE_FEEL: (
            "Of the areas it puts highest, about half read as villages to people, and it "
            "takes some busy main roads and some grand inner streets for villages."
        )
    }
)

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

    A part that counts who lives somewhere is read from its high end, and
    stands in no scale: either would rank towards fewer of a group of
    people. In a recipe that holds one, no part carries more than 40
    hundredths, and the meaning of the vibe names the census. Such a vibe
    is put on no result by itself (`strip`): it is shown on one where a
    person asked for it, and is never the first thing said of an area.

    The parts that rest on conservation areas come to under 60 hundredths
    together, so that their one source places no area alone. A vibe that is
    a rough guide has a sentence that says why, and no other vibe has one.
    It is put on no result by itself either.
    """
    broken: str | None = None
    parts = [term.feature_id for term in tag.terms]
    features = [FEATURES[feature_id] for feature_id in parts if feature_id in FEATURES]
    scale = tag.shape is TagShape.SCALE
    exempt = tag.tag_id in HOLDS_CRIME
    residents = [term for term in tag.terms if term.feature_id in COUNTS_RESIDENTS]
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
    elif any(term.reading is not TermReading.HIGH for term in residents):
        broken = "reads a part that counts residents from its high end"
    elif residents and scale:
        broken = "holds no part that counts residents, being a scale"
    elif residents and any(t.hundredths > PART_MAX_WHERE_RESIDENTS_COUNT for t in tag.terms):
        broken = "holds no part of more than 40 hundredths where it counts residents"
    elif residents and CENSUS_SAID not in tag.meaning:
        broken = "names the census in its meaning where it counts residents"
    elif residents and tag.strip:
        broken = "is on a result only where it was asked for, where it counts residents"
    elif (
        sum(term.hundredths for term in tag.terms if term.feature_id in ON_CONSERVATION_AREAS)
        > PART_MAX_HUNDREDTHS
    ):
        broken = "holds under 60 hundredths of parts that rest on conservation areas"
    elif (tag.sureness is Sureness.ROUGH_GUIDE) is not (tag.tag_id in WHY_A_ROUGH_GUIDE):
        broken = "says why it is a rough guide, and says so of no other"
    elif tag.sureness is Sureness.ROUGH_GUIDE and tag.strip:
        broken = "is on a result only where it was asked for, where it is a rough guide"
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
    rough: bool = False,
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
            # can be judged. On real data a flag is earned (ADR 0013). But a vibe
            # that counts who lives somewhere is put on no result by itself, and is
            # in neither list of what an area has most and least of: Burro measures
            # places first. It is shown on a result where a person asked for it. So is
            # a vibe that is a rough guide: what is less sure is never said unasked.
            lens=True,
            strip=not rough
            and not any(feature_id in COUNTS_RESIDENTS for _, feature_id, _ in terms),
            table=True,
            shelf_word=shelf,
            shelf_toward=Toward.HIGH if shelf else None,
            shelf_order=order,
            terms=tuple(
                TagTerm(feature_id=feature_id, hundredths=hundredths, reading=reading)
                for hundredths, feature_id, reading in terms
            ),
            sureness=Sureness.ROUGH_GUIDE if rough else Sureness.AS_THE_REST,
        )
    )


_STREETS, _PACE, _GREEN, _DAILY, _WHO = (
    Family.STREETS_HOMES,
    Family.PACE_FOOD,
    Family.GREEN,
    Family.DAILY_LIFE,
    Family.WHO_LIVES_THERE,
)
# What every vibe that counts residents cannot see: the census is of one day.
_SINCE_THE_CENSUS = (
    "Who has moved in or out since the census was taken, on 21 March 2021, during a lockdown"
)
_NOT_UPKEEP = "Whether streets are clean or run down. Empty shops. Graffiti"

# In the order of the shelf, then of "more". Gritty comes last of the vibes of the place,
# and the two that count who lives there come after it.
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
    # Village feel is a rough guide. It was tried three times against the bar the founder
    # set, and did not reach it. The founder chose on 2026-09-25 to serve it all the same,
    # and that it says it is less sure than the other vibes (ADR 0013, as amended). This
    # is the second try's recipe, as it was counted: no part for a small or a compact
    # centre, for independent places, for traffic or for homes per hectare of land that
    # is no park, each of which was tried and did not help. Change no share but with the
    # founder. Homes per hectare are read from the low end: in a village homes stand
    # apart. The high street is 45 in 100, so no area is placed without one, and the two
    # parts that rest on conservation areas are 55, so they place no area alone.
    _tag(
        TagId.VILLAGE_FEEL,
        "Village feel",
        _STREETS,
        "A high street in a conservation area, homes that stand apart, period homes and "
        "protected streets",
        "How much traffic runs along a high street. Whether the high street nearest a home "
        "is the centre of a village. Whether a park makes the homes beside it read as "
        "standing apart. Whether neighbours know each other",
        2,
        (45, _F.HIGHSTREET_CONSERVED, _HIGH),
        (30, _F.HOMES_DENSITY, _LOW),
        (15, _F.HOMES_PRE1919, _HIGH),
        (10, _F.CONSERVATION_COVER, _HIGH),
        shelf="villagey",
        rough=True,
    ),
    # Pubs and bars are 35 in 100 of it, as they were before they were held back. They
    # were held back while the food register was the one source of them, and are counted
    # from the file of places since a check of the two found it the sounder. While they
    # were out the recipe was 45, 30 and 25. Each count of venues is the figure for each
    # 1,000 homes, which a wish is ranked on. A town centre is a distance, read from its
    # near end.
    _tag(
        TagId.PACE,
        "Going out",
        _PACE,
        "How much there is to eat, drink and go out to within reach of homes",
        "How a weekday differs from a weekend. Who the venues serve. Opening hours. What is on",
        3,
        (35, _F.VENUE_EVENING_PER_HOMES, _HIGH),
        (30, _F.VENUE_FOOD_DRINK_PER_HOMES, _HIGH),
        (20, _F.HIGHSTREET_ACCESS, _LOW),
        (15, _F.CULTURE_VENUES_PER_HOMES, _HIGH),
        ends=("Calm", "Buzzy"),
        shelf="lively",
    ),
    _tag(
        TagId.QUIET_RESIDENTIAL,
        "Quiet streets",
        _STREETS,
        "Homes away from main roads and from clusters of pubs and bars, with little transport "
        "noise",
        "Noise from neighbours, venues or works. Which noise is from roads and which from "
        "aircraft. How busy a road is. How late a pub or a bar is open",
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
        "It is mostly a map of how built up a place is. How long the walk is: each distance "
        "is a straight line. Which side of a railway a home is on. How large a food shop is, "
        "and what it sells. Whether a surgery takes new patients. Opening hours. Step-free "
        "access at every station",
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
        # It is a different thing from Family area, which counts the households that hold
        # children too. This one counts what is there for them, and says so.
        "Primary schools, play space and parks nearby. It counts places alone",
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
    # How near stops are, and no more. The Underground and the DLR count for most, the
    # Overground and the Elizabeth line for less, National Rail and the trams for less
    # again, as less well connected, and the routes of buses for a fifth: asked for on
    # 2026-09-24, in place of journey times that no build holds. The weights are a first
    # judgement, for a person to review.
    _tag(
        TagId.WELL_CONNECTED,
        "Well connected",
        _DAILY,
        "An Underground or DLR station, an Overground or Elizabeth line station, a National "
        "Rail station or tram stop, and bus routes close to home",
        "How often anything runs, where it goes, or how long a journey takes: it counts how "
        "near stops are, and nothing more. Which lines call at a station. Whether a station "
        "has steps",
        12,
        (45, _F.UNDERGROUND_PROXIMITY, _LOW),
        (20, _F.OVERGROUND_PROXIMITY, _LOW),
        (15, _F.RAIL_PROXIMITY, _LOW),
        (20, _F.BUS_ROUTES_NEARBY, _HIGH),
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
        13,
        (30, _F.INCIDENT_CRIMINAL_DAMAGE, _HIGH),
        (15, _F.LAND_INDUSTRY, _HIGH),
        (15, _F.LAND_STORAGE, _HIGH),
        (15, _F.INCIDENT_ANTISOCIAL, _HIGH),
        (15, _F.ROAD_MAJOR_EXPOSURE, _HIGH),
        (10, _F.NOISE_EXPOSURE, _HIGH),
        ends=("Polished", "Gritty"),
    ),
    # The two vibes that count who lived in an area. Each runs one way, reads its census
    # figure from the high end, and holds no part of more than 40 in 100. What is there
    # is six in ten of each: Burro measures places first. The weights are a first judgement,
    # for a person to review.
    #
    # Family area is households with dependent children, and what Family amenities counts
    # in the shares it counts them, to the nearest five. On London's areas it stands at
    # 0.65 with Family amenities, and at nought with flats and with distance from the
    # centre. Family amenities follows how close together homes stand.
    _tag(
        TagId.FAMILY_AREA,
        "Family area",
        _WHO,
        f"Households with dependent children at {CENSUS_SAID}, with primary schools, play "
        "space and a park nearby. It counts who lived there beside what is there",
        f"{_SINCE_THE_CENSUS}. How many children there are, and how old. Catchments. School "
        "places. What childcare costs",
        14,
        (40, _F.HOUSEHOLDS_DEPENDENT_CHILDREN, _HIGH),
        (25, _F.SCHOOL_PRIMARY_NEARBY, _HIGH),
        (20, _F.PLAY_SPACE_PROXIMITY, _LOW),
        (15, _F.PARK_PROXIMITY, _LOW),
    ),
    # Young professionals is residents aged 20 to 34 with what is near for them: a station,
    # places to eat and drink, and culture. It counts age and nothing of work, and says so.
    # A recipe of residents, flats and homes per hectare was proposed and not built: it
    # found the areas that Houses or flats finds.
    _tag(
        TagId.YOUNG_PROFESSIONALS,
        "Young professionals",
        _WHO,
        f"Residents aged 20 to 34 at {CENSUS_SAID}, with a station, places to eat and drink "
        "and culture nearby. It counts who lived there beside what is there",
        f"What anyone does for work: it counts residents by their age alone. "
        f"{_SINCE_THE_CENSUS}. Who is a student. Opening hours and what is on",
        15,
        (40, _F.RESIDENTS_AGED_20_34, _HIGH),
        (25, _F.STATION_WALK, _LOW),
        (20, _F.VENUE_FOOD_DRINK_PER_HOMES, _HIGH),
        (15, _F.CULTURE_VENUES_PER_HOMES, _HIGH),
    ),
)

TAGS: Mapping[TagId, Tag] = MappingProxyType({t.tag_id: t for t in _TAGS})
# The vibes whose recipe holds a part that counts who lived somewhere.
HOLDS_RESIDENTS: frozenset[TagId] = frozenset(
    tag.tag_id for tag in _TAGS if any(term.feature_id in COUNTS_RESIDENTS for term in tag.terms)
)
# The vibes that are a rough guide. Each is offered with its label and its sentence, is
# never applied from a word and never taken with others at one press, and is on a result
# only where a person asked for it.
ROUGH_GUIDES: frozenset[TagId] = frozenset(
    tag.tag_id for tag in _TAGS if tag.sureness is Sureness.ROUGH_GUIDE
)


class RoughGuide(Record):
    """What stands beside a vibe that is a rough guide, wherever the vibe is shown."""

    tag_id: TagId
    # One short label, the same for every vibe that is one.
    label: str
    # One sentence that says why the vibe is less sure than the rest.
    why: str


def says_rough(tag_id: TagId) -> str:
    """What a rough guide says of itself wherever it is offered: its label, and why."""
    return f"{ROUGH_GUIDE}. {WHY_A_ROUGH_GUIDE[tag_id]}"


def rough_guides(vibes: Iterable[Tag]) -> tuple[RoughGuide, ...]:
    """What each vibe that is a rough guide says of itself, in the order the vibes stand in.

    It is read from the vibes that are handed over, which are a release's own,
    so a release that carries no rough guide is told of none.
    """
    return tuple(
        RoughGuide(tag_id=vibe.tag_id, label=ROUGH_GUIDE, why=WHY_A_ROUGH_GUIDE[vibe.tag_id])
        for vibe in vibes
        if vibe.sureness is Sureness.ROUGH_GUIDE
    )


# A vibe that places an area only where one of these parts of its recipe has a figure,
# whatever else of it has. It is how a vibe is held off: its recipe may come to 60 in 100
# on what a build holds, and still find the wrong places without the part that tells them
# apart. No vibe is named here today. Village feel was, from 2026-09-24, for the size and
# the shape of a town centre, which no build carries: the founder chose on 2026-09-25 to
# serve it on another recipe, as a rough guide. `tag_raw()` holds the rule for any vibe
# that is named here in future, and core refuses a release that places such a vibe by
# moving its shares (`held_off_stays_held_off`). Name a vibe here, and take one out, only
# in a change the founder has seen.
PLACED_ONLY_WITH: Mapping[TagId, frozenset[FeatureId]] = MappingProxyType({})

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

    It carries the twelve, and the one that gritty is read as there. It never
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


def tag_raw(
    tag_id: TagId,
    percentiles: Mapping[FeatureId, float | None],
    recipe: Sequence[TagTerm] | None = None,
) -> TagRaw:
    """One area's raw value for a tag, from that area's feature percentiles.

    A feature that is absent from `percentiles` counts as missing, as one whose
    percentile is `None` does. Nothing is filled in: the terms that are present
    are reweighted, and below 60 hundredths of the formula the tag is unknown.
    So is a tag of `PLACED_ONLY_WITH` where none of the parts named for it has
    a figure. How much of the formula is known is said either way.
    `raw` is rounded to the six decimals a release is written with, so that it
    is the same number before it is written and after it is read.

    `recipe` is the recipe a release carries, where a person has adjusted its
    shares (ADR 0029). With none it is core's own. Which parts a recipe holds,
    and which end each is read from, is core's either way: a release that
    carries any other is refused before a band is worked out.
    """
    present = 0
    total = 0.0
    for term in TAGS[tag_id].terms if recipe is None else recipe:
        percentile = percentiles.get(term.feature_id)
        if percentile is None:
            continue
        share = percentile / 100
        total += term.hundredths * (share if term.reading is TermReading.HIGH else 1 - share)
        present += term.hundredths
    needed = PLACED_ONLY_WITH.get(tag_id)
    held = needed is None or any(percentiles.get(part) is not None for part in needed)
    enough = held and present >= TAG_MIN_COVERAGE_HUNDREDTHS
    return TagRaw(raw=round(total / present, 6) if enough else None, coverage=present / 100)
