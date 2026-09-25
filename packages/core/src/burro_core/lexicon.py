"""The lexicon: every phrase the rule-based reader takes for a thing, and what it means.

A thing is a feature or a vibe. It answers to its label and its short label,
a scale to the names of its ends, and both to the phrases below, which are the
other ways people ask for one. No other word calls up a vibe. A new phrase
is a case in `evals/` first. The label of a scale names no end, so it is
noticed and offered and never applied.

A phrase is `stated` when it names the thing and `inferred` when the thing is
read into looser words, which a chip marks as "assumed". A word with two
meanings, such as "gritty", is read as its place part alone, and the chip
quotes the word.

Gritty is one vibe, the scale that counts recorded crime, and a release that
holds no recorded crime does not carry it. So what the words for it mean
depends on the release, and `lexicon_of` and `no_measure_of` give the phrases
for one.

Burro ranks places first. Of who lives somewhere it counts two things, from
Census 2021: the age of residents and what their households are made of. A
phrase for either is a thing of the lexicon, and it is only ever offered,
towards more of what is counted: no word applies it, and no word asks for
fewer of anyone. `POLICY_LEXICON` holds every other word for people, and
never one for buildings. A word of it is heard, makes no edit, and gets one
neutral sentence (ADR 0006).
"""

import re
import unicodedata
from collections.abc import Mapping
from types import MappingProxyType
from typing import NamedTuple

from burro_core.catalogue import (
    CHAINS,
    COUNTS_RESIDENTS,
    CRIME_CAVEAT,
    FEATURES,
    GRITTY,
    HOLDS_RESIDENTS,
    MIXED_WORDS,
    NUISANCES,
    RANKED_AS,
    TAGS,
    tags_of,
)
from burro_core.ids import (
    DirectionChoice,
    EditProvenance,
    FeatureId,
    GrittyVariant,
    TagId,
    TagShape,
    Toward,
    UnmetCategory,
)

# Every mark a person's keyboard may put where an apostrophe goes.
APOSTROPHE = (
    "'`\N{RIGHT SINGLE QUOTATION MARK}\N{LEFT SINGLE QUOTATION MARK}"
    "\N{MODIFIER LETTER APOSTROPHE}\N{PRIME}\N{FULLWIDTH APOSTROPHE}"
)
APOSTROPHES = re.compile(f"[{APOSTROPHE}]")


def plain(text: str) -> str:
    """Lower case and no accents, with every mark still where it was typed."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def prepare(text: str) -> str:
    """The text as the rules read it: lower case, no accents, no apostrophes, single spaces."""
    bare = APOSTROPHES.sub("", plain(text)).replace("&", " and ")
    return re.sub(r"\s+", " ", re.sub(r"[-_/\"()\[\]]", " ", bare)).strip()


class Target(NamedTuple):
    """What a phrase of the lexicon means: features and vibes, and how they were named."""

    features: tuple[FeatureId, ...]
    tags: tuple[TagId, ...]
    provenance: EditProvenance
    direction: DirectionChoice = DirectionChoice.DEFAULT
    # The phrase names something it is a nuisance to have, so "less" of it
    # and "no" are the wish itself and not a wish turned round.
    nuisance: bool = False
    # The phrase already says that less of the nuisance is wanted, "low crime",
    # so naming it is the wish. A nuisance that is only named, "noise", is not
    # one the reader can read: the person may like it.
    wanted_low: bool = False
    # The end of a scale the phrase asks for. "Calm" is the low end of Pace.
    toward: Toward = Toward.HIGH
    # What the phrase also asks for that Burro has no measure of.
    unmet: UnmetCategory | None = None
    # The word with two meanings that was read as its place part alone.
    word: str = ""
    # The phrase is the name of a scale, which names neither of its ends. It
    # is noticed and offered with both, and never applied: "going out" is no
    # wish for Buzzy.
    no_end: bool = False
    # Burro has no measure of what the phrase asks for. This says what it
    # cannot do, and what is nearest that it can. A phrase that holds one is
    # never applied: what is nearest is offered, and the person chooses.
    note: str = ""
    # What is nearest is offered one way: towards the end of a scale the
    # phrase names, or as more of a thing. "Affluent" is offered towards
    # Polished, and never towards Gritty.
    one_way: bool = False
    # It is offered that one way whatever is said of it, a word that turns
    # it away among them. "Soulless" and "not bland" ask for a place with
    # character as "characterful" does, and none is a wish for the opposite
    # of a village feel. It is never applied, and never taken off either.
    whatever: bool = False
    # The phrase is a word for a person too, "doctor", "chemist", or for what is
    # no place: "surgery". It is the place only where the words beside it say
    # that it is wanted near, or is to be reached: "near a doctor", "a chemist
    # nearby". Anywhere else it is no thing, so that "I am a doctor" asks for
    # no surgery.
    near_only: bool = False
    # The measures that are offered before the vibes, where what is nearest is
    # offered one way. Of what is only nearest a vibe comes before the measures
    # it is made of, but for a measure that is the first reading of the word.
    leads: tuple[FeatureId, ...] = ()


_F = FeatureId
_T = TagId
_STATED = EditProvenance.STATED
_INFERRED = EditProvenance.INFERRED
_CRIME = (_F.CRIME_VIOLENCE_ROBBERY, _F.CRIME_BURGLARY_THEFT)
# What a home is called. A label, a short label or the name of an end that is
# one of these is no phrase of the lexicon: "flats" says what is being looked
# for, and the reader cannot say that it is a wish for more of them.
HOME_WORDS = frozenset({"homes", "home", "houses", "house", "flats", "flat"})


def _said(target: Target, *phrases: str) -> dict[str, Target]:
    return dict.fromkeys(phrases, target)


def _feature(feature_id: FeatureId, provenance: EditProvenance = _STATED) -> Target:
    return Target((feature_id,), (), provenance)


def _nuisance(*feature_ids: FeatureId, provenance: EditProvenance = _STATED) -> Target:
    return Target(feature_ids, (), provenance, nuisance=True)


def _low(*feature_ids: FeatureId, provenance: EditProvenance = _STATED) -> Target:
    return Target(feature_ids, (), provenance, nuisance=True, wanted_low=True)


def _tag(
    tag_id: TagId, provenance: EditProvenance = _STATED, toward: Toward = Toward.HIGH
) -> Target:
    return Target((), (tag_id,), provenance, toward=toward)


# The first words a newcomer reaches for, of which Burro has no measure. Each
# is offered what is nearest, and says what Burro cannot do and why.
CANNOT_SAY_SAFE = (
    f"Burro cannot say how safe a place is. It can count recorded crime. {CRIME_CAVEAT}"
)
NO_POOLS = (
    "Burro cannot tell a swimming pool or a leisure centre from any other place to train. "
    "The nearest it can count is gyms and fitness studios."
)
NO_NEIGHBOURS = (
    "Burro cannot measure whether neighbours know each other. The nearest it can count is "
    "a small centre of its own, with old streets and independent places."
)
NOT_ONE_HOME = (
    "Burro cannot see whether one home has a garden. "
    "It can count how much of an area is residential garden."
)
# A word for a smart area is read as of the place, and never of who lives there:
# not of what they earn, and not of who they are (ADR 0006).
PLACES_NOT_PEOPLE = "Burro reads this of the place, and not of the people who live there."
NO_IDENTITY = (
    "Burro cannot measure the character of a place. The nearest it can count are a village "
    "feel, the age of the buildings and a town centre nearby. Choose any that fit what you mean."
)
# A word for a place on the rise is read as of what homes sold for: not of who is moving
# in, and not of what a home will be worth. Where a release carries Gritty, "up and coming"
# is offered as where a place stands on that scale too, as it was before a rise was held.
A_RISE_PROMISES_NOTHING = (
    "Burro cannot see where a place is heading. It can count how far what homes sold for "
    "has risen. A rise is of prices that were paid, and promises nothing."
)
A_RISE_OR_THE_SCALE = (
    "Burro cannot see where a place is heading. It can count how far what homes sold for "
    "has risen, and say where a place stands on Gritty today. A rise is of prices that were "
    "paid, and promises nothing."
)
# What a person should know before they ask to be near a chain.
OF_A_CHAIN = (
    "Burro finds a chain by the brand its file of places gives a shop. "
    "The file misses some shops, and lists some that have closed."
)
# What is said wherever a thing that counts who lives somewhere is offered.
COUNTED_AT_THE_CENSUS = (
    "Burro counts who was living there at the census of 2021. It measures places first."
)
# A person's own age is not known to Burro, and it counts two ages and no other. So the
# words are answered with a question, and the two it counts are offered to choose from.
WHAT_AGE = (
    "What age? Burro counts residents aged 20 to 34, and residents aged 65 and over. "
    f"{COUNTED_AT_THE_CENSUS}"
)


def counts_residents(target: Target) -> bool:
    """Whether a phrase asks for a thing that counts who lives somewhere.

    Such a thing is offered and never applied, towards more of what it counts
    and no other way. Under a word that turns it, the phrase asks for fewer of
    a group of people, which nothing reads (ADR 0006).
    """
    return bool(COUNTS_RESIDENTS & set(target.features) or HOLDS_RESIDENTS & set(target.tags))


def _who(
    *, features: tuple[FeatureId, ...] = (), tags: tuple[TagId, ...] = (), note: str = ""
) -> Target:
    """What is offered for a phrase that asks who lives somewhere: more of what is counted."""
    return Target(features, tags, _INFERRED, note=note or COUNTED_AT_THE_CENSUS, one_way=True)


def _nearest(
    note: str, *, features: tuple[FeatureId, ...] = (), tag: TagId | None = None
) -> Target:
    """What is offered for a phrase Burro has no measure of. It is never applied."""
    return Target(features, () if tag is None else (tag,), _INFERRED, note=note)


def _by_name() -> dict[str, Target]:
    """Every feature and vibe by its label and its short label, and a scale by its ends.

    A measure that is shown and never ranked on is named as a wish for the
    measure that is ranked on in its place: to name the count of places to
    eat and drink is to ask for the places for each 1,000 homes.
    """
    found: dict[str, Target] = {}
    for feature_id, feature in FEATURES.items():
        ranked = RANKED_AS.get(feature_id, feature_id)
        named = _nuisance(ranked) if ranked in NUISANCES else _feature(ranked)
        if ranked in COUNTS_RESIDENTS:
            # Its own name is offered too: no word applies a measure of who lives somewhere.
            found[prepare(feature.label)] = found[prepare(feature.short_label)] = _who(
                features=(ranked,)
            )
            continue
        found[prepare(feature.label)] = named
        # The short label of a nuisance says the wish: "Less transport noise".
        found[prepare(feature.short_label)] = (
            _low(ranked) if ranked in NUISANCES else _feature(ranked)
        )
    for tag_id, tag in TAGS.items():
        named = _tag(tag_id)._replace(no_end=tag.shape is TagShape.SCALE)
        if tag_id in HOLDS_RESIDENTS:
            named = _who(tags=(tag_id,))
        found[prepare(tag.label)] = named
        found[prepare(tag.short_label)] = named
    return {phrase: target for phrase, target in found.items() if phrase not in HOME_WORDS}


def _left_out(variant: GrittyVariant) -> frozenset[TagId]:
    """The vibes a release of this kind does not carry."""
    return frozenset(TAGS) - {tag.tag_id for tag in tags_of(variant)}


def _ends(variant: GrittyVariant) -> dict[str, Target]:
    """The names of the ends of the scales a release carries: "calm", "buzzy", "historic"."""
    left_out = _left_out(variant)
    found: dict[str, Target] = {}
    for tag_id, tag in TAGS.items():
        if tag.shape is not TagShape.SCALE or tag_id in left_out:
            continue
        for end, toward in ((tag.low_end, Toward.LOW), (tag.high_end, Toward.HIGH)):
            if end is not None and prepare(end) not in HOME_WORDS:
                found[prepare(end)] = _tag(tag_id, toward=toward)
    return found


def _named_as_a_home() -> dict[TagId, Mapping[str, Toward]]:
    """The ends of a scale that a word for a home names, for one home and for many."""
    found: dict[TagId, dict[str, Toward]] = {}
    for tag_id, tag in TAGS.items():
        for end, toward in ((tag.low_end, Toward.LOW), (tag.high_end, Toward.HIGH)):
            named = "" if end is None else prepare(end)
            for word in (named, named.removesuffix("s")):
                if tag.shape is TagShape.SCALE and word in HOME_WORDS:
                    found.setdefault(tag_id, {})[word] = toward
    return {tag_id: MappingProxyType(ends) for tag_id, ends in found.items()}


# A word for a home is no phrase of the lexicon: "a flat" says what is being looked
# for, and the reader cannot say that it is a wish for more of them. It names an end of
# Houses or flats all the same, and says which way where one end is set against the
# other: "houses not flats". It is held here for whoever has been told that the scale
# is meant, which is the guard on a model, and the reader never reads it.
ENDS_NAMED_AS_HOMES: Mapping[TagId, Mapping[str, Toward]] = MappingProxyType(_named_as_a_home())

# The words for a smart area, which are read as of the place and never of who lives there.
_SMART = ("affluent", "posh", "well heeled", "upmarket", "smart")
# What people are called after a word for a smart area or a rough one. Said of
# them, the word is of who lives somewhere, and is offered nothing.
_WHO = (
    "people families folk folks types sorts locals crowd kids children couples parents "
    "households homeowners commuters clientele community communities"
)
# The character of a people is theirs: "a Polish character", "working class
# identity". After a word for a group or for people, each of these asks who
# lives somewhere, and is never offered as the character of a place.
OF_A_PEOPLE = frozenset({"identity", "character", "soul"})
# What the word "gritty" is read as, by what a release carries.
GRITTY_TAG: Mapping[GrittyVariant, TagId] = GRITTY

# The words for the other end of the mix, which are offered as the mix towards value and as
# nothing else: not as cheaper homes, and not as Gritty, which counts recorded crime.
_PLAIN = ("cheap and cheerful", "unpretentious", "down to earth")
_TOWARDS_VALUE = Target(
    (_F.BRAND_MIX,),
    (),
    _INFERRED,
    DirectionChoice.LESS,
    note=PLACES_NOT_PEOPLE,
    one_way=True,
)
# What people type for a chain, beside its name as Burro says it. A chain is offered as the
# distance to the nearest place of it, one way, and is never applied.
_TYPED: Mapping[FeatureId, tuple[str, ...]] = {
    _F.BRAND_MANDS: ("marks and spencer", "marks and spencers", "m and s food"),
    _F.BRAND_WHOLE_FOODS: ("whole foods market", "wholefoods"),
    _F.BRAND_SAINSBURYS: ("sainsbury", "sainsburys local"),
    _F.BRAND_TESCO: ("tescos", "tesco express"),
    _F.BRAND_COOP: ("coop", "the co op"),
    _F.BRAND_BARRYS: ("barrys bootcamp",),
    _F.BRAND_NUFFIELD: ("nuffield gym",),
    _F.BRAND_PUREGYM: ("pure gym",),
    _F.BRAND_GAILS: ("gails bakery",),
    _F.BRAND_PRET: ("pret a manger",),
    _F.BRAND_NERO: ("caffe nero", "cafe nero"),
    _F.BRAND_COSTA: ("costa coffee",),
    _F.BRAND_BLANK_STREET: ("blank street coffee",),
}


def _chains() -> dict[str, Target]:
    """Every chain by its name, and by what else people type for it."""
    found: dict[str, Target] = {}
    for feature_id, chain in CHAINS.items():
        named = Target((feature_id,), (), _STATED, note=OF_A_CHAIN, one_way=True)
        for phrase in (prepare(chain.name), *_TYPED.get(feature_id, ())):
            found[phrase] = named
    return found


# A place on the rise, read as of what homes sold for: how far the middle price has risen
# over five years and over ten. It is offered one way, a steeper rise, and is never applied:
# a rise is of prices that were paid, and promises nothing.
_ON_THE_RISE = ("on the up", "rising", "rising prices", "prices rising")
_RISING = Target(
    (_F.PRICE_RISE_5Y, _F.PRICE_RISE_10Y),
    (),
    _INFERRED,
    note=A_RISE_PROMISES_NOTHING,
    one_way=True,
)

# The phrases that mean the same whichever way gritty was built.
LEXICON: Mapping[str, Target] = {
    **_by_name(),
    # Crime is weighted only on an explicit request. "Safe" is not one: it names
    # no crime. So it is never applied. Recorded crime is offered by its name,
    # and to choose it is to ask for it.
    **_said(_nuisance(*_CRIME), "crime", "crime rate", "crime rates"),
    **_said(_low(*_CRIME), "low crime", "low crime rate", "low crime rates"),
    **_said(
        _nearest(CANNOT_SAY_SAFE, features=_CRIME),
        *("safe", "safer", "safety", "feel safe", "unsafe", "dangerous"),
    ),
    **_said(
        _nearest(NO_POOLS, features=(_F.VENUE_GYM_PER_HOMES,)),
        *("leisure centre", "leisure centres", "sports centre"),
        *("swimming pool", "swimming pools"),
    ),
    **_said(
        _nearest(NO_NEIGHBOURS, tag=_T.VILLAGE_FEEL),
        *("community", "sense of community", "community feel", "community spirit"),
        "neighbourly",
    ),
    **_said(
        _nearest(NOT_ONE_HOME, features=(_F.LAND_GARDENS,)),
        *("garden", "big garden", "large garden", "private garden", "own garden"),
        "outdoor space",
    ),
    # A place with character, and a place without. Burro has no measure of
    # either, and offers three things it can count for the person to choose
    # from. A word for a place without is offered the same three.
    **_said(
        Target(
            (_F.HIGHSTREET_ACCESS,),
            (_T.VILLAGE_FEEL, _T.BUILT_AGE),
            _INFERRED,
            note=NO_IDENTITY,
            one_way=True,
            whatever=True,
        ),
        *("identity", "real identity", "own identity", "its own identity", "sense of identity"),
        *("character", "real character", "characterful", "its own character"),
        *("own feel", "its own feel", "feel of its own", "proper neighbourhood"),
        *("soul", "soulless", "bland"),
    ),
    # The name of a scale names no end of it. Each answers to the name it has
    # on screen and to the name it had, whatever the catalogue calls it today.
    **_said(_tag(_T.PACE)._replace(no_end=True), "pace", "going out"),
    **_said(
        _tag(_T.BUILT_AGE)._replace(no_end=True),
        *("built age", "age of buildings", "age of the buildings"),
    ),
    **_said(_tag(_T.HOMES)._replace(no_end=True), "houses or flats"),
    # What the scale was called before it was called Gritty. It named no end.
    **_said(_tag(_T.STREET_CHARACTER)._replace(no_end=True), "street character"),
    **_said(_nuisance(_F.CRIME_BURGLARY_THEFT), "burglary", "burglaries", "theft", "thefts"),
    **_said(_nuisance(_F.CRIME_VIOLENCE_ROBBERY), "violent crime", "violence", "robbery"),
    **_said(_nuisance(_F.INCIDENT_CRIMINAL_DAMAGE), "criminal damage", "vandalism"),
    **_said(_nuisance(_F.INCIDENT_ANTISOCIAL), "anti social behaviour", "antisocial behaviour"),
    **_said(_feature(_F.SCHOOL_PRIMARY_NEARBY), "primary school", "primary schools"),
    **_said(
        _feature(_F.SCHOOL_PRIMARY_ATTAINMENT),
        "good primary school",
        "good primary schools",
        "best primary schools",
        "primary school results",
    ),
    **_said(
        _feature(_F.SCHOOL_SECONDARY_ATTAINMENT),
        "secondary school",
        "secondary schools",
        "good secondary schools",
        "attainment 8",
    ),
    **_said(
        Target((_F.SCHOOL_PRIMARY_ATTAINMENT, _F.SCHOOL_SECONDARY_ATTAINMENT), (), _INFERRED),
        "school",
        "schools",
        "good schools",
    ),
    # A campus is one measure, so it is a feature and no vibe. It keeps its one direction.
    **_said(_feature(_F.UNIVERSITY_PROXIMITY), "universities", "university", "near a university"),
    **_said(_feature(_F.UNIVERSITY_PROXIMITY, _INFERRED), "campus", "uni"),
    **_said(_feature(_F.GREEN_COVER), "green space", "green spaces", "greenspace"),
    **_said(_tag(_T.LEAFY), "leafy"),
    **_said(_tag(_T.LEAFY, _INFERRED), "green", "greenery", "trees", "tree lined"),
    **_said(_feature(_F.LAND_GARDENS), "gardens"),
    **_said(_feature(_F.LAND_WOODLAND), "woodland", "woods"),
    **_said(_feature(_F.PARK_PROXIMITY), "park", "parks", "near a park", "close to a park"),
    **_said(_tag(_T.PARKS_CLOSE_BY), "big park", "near a big park", "large park"),
    **_said(
        _feature(_F.PLAY_SPACE_PROXIMITY),
        "playground",
        "playgrounds",
        "play area",
        "play areas",
        "play space",
        "play spaces",
    ),
    # The words of a vibe that was retired weigh the one feature that took its place.
    **_said(
        _feature(_F.WATER_ACCESS, _INFERRED),
        "river",
        "canal",
        "riverside",
        "waterside",
        "by the water",
        "water",
    ),
    **_said(_feature(_F.AIR_NO2), "air quality"),
    **_said(_nuisance(_F.AIR_NO2), "pollution", "polluted", "nitrogen dioxide"),
    **_said(_low(_F.AIR_NO2), "low pollution"),
    **_said(_low(_F.AIR_NO2, provenance=_INFERRED), "clean air", "fresh air"),
    **_said(_nuisance(_F.AIR_NO2, provenance=_INFERRED), "fumes"),
    **_said(_nuisance(_F.NOISE_EXPOSURE), "noise", "noisy", "traffic noise", "transport noise"),
    **_said(_low(_F.NOISE_EXPOSURE), "low noise"),
    **_said(_nuisance(_F.ROAD_MAJOR_EXPOSURE), "main road", "main roads"),
    **_said(_tag(_T.QUIET_RESIDENTIAL), "quiet", "quieter", "quiet street", "quiet streets"),
    **_said(_tag(_T.QUIET_RESIDENTIAL, _INFERRED), "peaceful", "residential", "peace and quiet"),
    # A wish for places to eat and drink is ranked on the places for each 1,000 homes.
    # The count is shown beside it, and no word asks to be ranked on the count.
    **_said(_feature(_F.VENUE_FOOD_DRINK_PER_HOMES), "restaurants", "places to eat", "eating out"),
    # Cafes, gyms and pubs are each ranked on the figure for each 1,000 homes, and the
    # count is shown beside it. A cafe was a place to eat and drink to the reader until
    # it had a measure of its own.
    **_said(_feature(_F.VENUE_CAFE_PER_HOMES), "cafes", "cafe", "coffee shops", "coffee shop"),
    **_said(_feature(_F.VENUE_CAFE_PER_HOMES, _INFERRED), "coffee"),
    **_said(_feature(_F.VENUE_GYM_PER_HOMES), "gyms", "gym"),
    **_said(_feature(_F.VENUE_GYM_PER_HOMES, _INFERRED), "yoga"),
    **_said(_tag(_T.FOODIE), "foodie"),
    **_said(_tag(_T.FOODIE, _INFERRED), "food scene", "good food"),
    **_said(_feature(_F.VENUE_EVENING_PER_HOMES), "pubs", "bars", "pub", "bar"),
    **_said(_tag(_T.PACE), "buzzy"),
    **_said(_tag(_T.PACE, _INFERRED), "lively", "bustling", "nightlife", "night life"),
    **_said(_tag(_T.PACE, _INFERRED, Toward.LOW), "calm", "sleepy"),
    # A wish for independent places is ranked on the share of the places to eat and drink
    # within reach that belong to no chain, which is the measure a build works out.
    **_said(
        _feature(_F.INDEPENDENTS_NEARBY),
        "independent shops",
        "independent cafes",
        "independent coffee shops",
        "independents",
        "independent",
    ),
    # A wish for culture is ranked on the venues for each 1,000 homes, as a wish for
    # places to eat is. The count is shown beside it.
    **_said(
        _feature(_F.CULTURE_VENUES_PER_HOMES),
        "theatres",
        "theatre",
        "cinemas",
        "cinema",
        "galleries",
        "museums",
        "libraries",
        "music venues",
        "live music",
    ),
    **_said(
        _feature(_F.CULTURE_VENUES_PER_HOMES, _INFERRED),
        "culture",
        "cultural",
        "arts",
        "creative",
        "arty",
        "artsy",
        "artistic",
    ),
    **_said(
        _feature(_F.HIGHSTREET_ACCESS),
        "high street",
        "town centre",
        "highstreet",
        "good high street",
        "great high street",
        "strong high street",
        "high street shops",
    ),
    **_said(_feature(_F.HIGHSTREET_ACCESS, _INFERRED), "shops", "shopping"),
    **_said(_feature(_F.GROCERY_WALK), "food shop", "food shops", "supermarket", "supermarkets"),
    # A surgery and a pharmacy are each a distance, and a part of Everyday on foot. A
    # release that carries no figure for one says so: neither is what Burro has no
    # measure of. Whether a surgery takes new patients is what it cannot see.
    **_said(_feature(_F.GP_WALK), "gp surgery", "gp practice", "doctors surgery"),
    **_said(_feature(_F.PHARMACY_WALK), "pharmacy", "pharmacies"),
    # A doctor, a GP and a chemist are people too, and surgery is an operation.
    **_said(
        _feature(_F.GP_WALK)._replace(near_only=True),
        *("gp", "gps", "doctor", "doctors", "surgery"),
    ),
    **_said(_feature(_F.PHARMACY_WALK)._replace(near_only=True), "chemist", "chemists"),
    **_said(_feature(_F.HOMES_PRE1919), "pre 1919", "built before 1919"),
    **_said(
        _feature(_F.HOMES_PRE1919, _INFERRED),
        "period homes",
        "period properties",
        "georgian",
        "edwardian",
    ),
    **_said(_tag(_T.BUILT_AGE), "period"),
    **_said(_tag(_T.BUILT_AGE, _INFERRED), "period houses", "historic", "heritage", "victorian"),
    **_said(_tag(_T.BUILT_AGE, _STATED, Toward.LOW), "new build", "new builds"),
    **_said(_tag(_T.BUILT_AGE, _INFERRED, Toward.LOW), "modern flats"),
    **_said(_feature(_F.LISTED_BUILDINGS), "listed buildings"),
    **_said(_feature(_F.CONSERVATION_COVER), "conservation area", "conservation areas"),
    **_said(_feature(_F.HOMES_DENSITY), "density", "dense", "built up"),
    **_said(
        Target((_F.HOMES_DENSITY,), (), _INFERRED, DirectionChoice.LESS),
        "low density",
        "spacious",
        "not built up",
    ),
    **_said(_tag(_T.HOMES, _INFERRED, Toward.LOW), "suburban", "house with a garden"),
    **_said(_tag(_T.HOMES, _INFERRED, Toward.HIGH), "urban", "city living"),
    # A station of any kind, as near as it is: what a search weighs before anything is said.
    **_said(
        _feature(_F.STATION_WALK),
        "near a station",
        "close to a station",
        "near the station",
        "train station",
        "station nearby",
        "station",
        "stations",
    ),
    # How well connected a place is: the Underground and the DLR, a railway station or a
    # tram stop, and the stops of buses. Its name asks for it, and so do the words people
    # use for good transport, for the Underground and for buses, which are read into it:
    # each is a part of it, and none is what a person means by the words alone. Until
    # catalogue version 13 the first four were read as the count of lines nearby, which no
    # build of London holds. "Tube" and "underground" alone are no phrase of it: each is a
    # way of travelling, "35 minutes by tube", and the grammar holds them as that.
    **_said(_tag(_T.WELL_CONNECTED), "well connected"),
    **_said(
        _tag(_T.WELL_CONNECTED, _INFERRED),
        "transport links",
        "good transport",
        "connections",
        "near a tube",
        "near the tube",
        "the tube",
        "tube station",
        "close to the underground",
        "the underground",
        "good buses",
        "buses",
    ),
    **_said(_tag(_T.EVERYDAY_ON_FOOT), "walkable", "walkability"),
    **_said(_tag(_T.EVERYDAY_ON_FOOT, _INFERRED), "everything on foot"),
    **_said(_tag(_T.VILLAGE_FEEL), "villagey", "village", "villages"),
    # Who lives somewhere: their age and their households, as Census 2021 counted them.
    # Each phrase is offered, and never applied from a word. It was decided on 2026-09-24
    # that a word which names an age and also work, "young professionals", "retirees", is
    # offered for its age alone: what the vibe cannot see says that it counts no work.
    #
    # A place that is good for a family may be one where families live, or one with
    # schools and play space, and the reader cannot say which is meant. So both vibes are
    # offered, and the person chooses.
    **_said(
        _who(tags=(_T.FAMILY_AREA, _T.FAMILY_AMENITIES)),
        "family friendly",
        "good for kids",
        "good for families",
    ),
    **_chains(),
    **_said(_TOWARDS_VALUE, *_PLAIN),
    **_said(
        _who(tags=(_T.FAMILY_AREA,)),
        *("families", "young families", "lots of families", "full of families"),
        "other families",
    ),
    **_said(_who(features=(_F.RESIDENTS_AGED_20_34,)), "young people", "young adults"),
    **_said(
        _who(features=(_F.RESIDENTS_AGED_65_OVER,)),
        *("retirees", "pensioners", "older people", "old people", "elderly"),
    ),
    # Older residents, and quiet streets, each offered for itself.
    **_said(
        _who(features=(_F.RESIDENTS_AGED_65_OVER,), tags=(_T.QUIET_RESIDENTIAL,)),
        "older and quieter",
    ),
    **_said(
        _who(features=(_F.RESIDENTS_AGED_20_34, _F.RESIDENTS_AGED_65_OVER), note=WHAT_AGE),
        "people my age",
        "people our age",
    ),
    **_said(_RISING, *_ON_THE_RISE),
}
# Every phrase that asks who lives somewhere and is offered for it. Typed whole, the
# words in it for people ask for what is counted, and are closed to no rule.
WHO_IS_COUNTED: frozenset[str] = frozenset(
    phrase for phrase, target in LEXICON.items() if counts_residents(target)
)

_MIXED = tuple(MIXED_WORDS)
_UPKEEP = ("polished", "smart", "well kept")
_WORKS = ("industrial", "warehouses")


# What a word for a smart area is offered as, whatever a release carries: first the mix of
# brands towards premium, then homes that sell for more than the middle, and then homes in
# the higher council tax bands. Decided on 2026-09-24. Each is of the place and never of who
# lives there, and none is ever applied. A reading stands on a line of its own.
_SELLS_FOR_MORE = Target(
    (
        _F.BRAND_MIX,
        _F.PRICE_MEDIAN,
        _F.HOMES_HIGHER_BANDS,
    ),
    (),
    _INFERRED,
    note=PLACES_NOT_PEOPLE,
    one_way=True,
    leads=(_F.BRAND_MIX,),
)


def _mixed(target: Target, *, unmet: UnmetCategory | None = None) -> dict[str, Target]:
    """The words with two meanings, each read as its place part and quoted."""
    return {word: target._replace(unmet=unmet, word=word) for word in _MIXED}


# What the words for gritty mean, by what the release that is read carries.
_GRITTY: Mapping[GrittyVariant, Mapping[str, Target]] = {
    # Where no recorded crime is held, from land use alone. "Gritty" is read as
    # it, and the person is told that Burro has no measure of how clean or run
    # down a street is.
    GrittyVariant.A: {
        **_said(_tag(_T.WORKS_WAREHOUSES), *_WORKS, "railway arches"),
        **_mixed(_tag(_T.WORKS_WAREHOUSES, _INFERRED), unmet=UnmetCategory.STREET_CLEANLINESS),
        # A smart area, read as of the place. The scale is not held here, so it has three
        # readings: the mix of brands, and two of its homes, what they sell for and the
        # bands they are in. "Smart" is a word for upkeep here.
        **_said(_SELLS_FOR_MORE, *(word for word in _SMART if word not in _UPKEEP)),
        **_said(_RISING, "up and coming"),
    },
    # As the one vibe, a scale whose name and whose end are the word. To type
    # "gritty" or "polished" is to ask for the scale by name, and so for the
    # recorded crime it counts. Every other word is only read into it, and is
    # offered. Works and warehouses is a part of it and is not served beside
    # it, so its words are read into the scale as any other is, and offered.
    GrittyVariant.B: {
        **_said(_tag(_T.STREET_CHARACTER, _INFERRED), *_WORKS, "railway arches"),
        **_mixed(_tag(_T.STREET_CHARACTER, _INFERRED)),
        "gritty": _tag(_T.STREET_CHARACTER),
        "polished": _tag(_T.STREET_CHARACTER, toward=Toward.LOW),
        **_said(_tag(_T.STREET_CHARACTER, _INFERRED, Toward.LOW), "well kept"),
        # A smart area, read as of the place, in four ways for the person to choose
        # from: the mix of brands towards premium, towards the polished end, homes that
        # sell for more, and homes in the higher council tax bands. Each is offered that
        # one way. Nothing of what people earn or who they are is read into it.
        **_said(_SELLS_FOR_MORE._replace(tags=(_T.STREET_CHARACTER,), toward=Toward.LOW), *_SMART),
        **_said(_tag(_T.STREET_CHARACTER, _INFERRED), "rough"),
        # A place that is up and coming was offered as the scale, with both its ends,
        # before a rise was held. It still is, beside the rise, and nobody can say
        # which end is meant.
        **_said(
            _RISING._replace(tags=(_T.STREET_CHARACTER,), note=A_RISE_OR_THE_SCALE, one_way=False),
            "up and coming",
        ),
    },
}


def _lexicon_of(variant: GrittyVariant) -> Mapping[str, Target]:
    left_out = _left_out(variant)
    # A phrase of the lexicon says how a word is read, so it comes before the
    # bare name of an end: "calm" is read into Pace, and marked as assumed.
    found = {**_ends(variant), **LEXICON, **_GRITTY[variant]}
    return MappingProxyType(
        {phrase: target for phrase, target in found.items() if not left_out & set(target.tags)}
    )


# A word for a group that is a word for nothing else. Beside a venue or a shop
# it asks for a community's amenity. Beside anything else it asks who lives there.
_GROUP_ONLY = (
    "jewish muslim christian catholic hindu sikh buddhist gay lesbian queer trans foreign "
    "immigrant religious student"
)
# A word for a group that is also a cuisine, a country or a colour. It asks
# about people only beside a word for people: "Turkish cafes" asks for cafes.
_GROUP_ALSO = (
    "black white asian african caribbean english british irish polish indian pakistani "
    "bangladeshi chinese arab somali turkish"
)
_GROUPS = f"{_GROUP_ONLY} {_GROUP_ALSO}"
_PEOPLE = ("people", "families", "community", "communities", "area", "areas", "neighbourhood")
# What those who are counted are called, where a phrase for them is offered. Beside a word
# for a group, or for how well off people are, each asks about what was not decided on, and
# is offered nothing: "Muslim families", "wealthy retirees", "posh young professionals".
_COUNTED = (
    "families",
    "young families",
    "young professionals",
    "young people",
    "older people",
    "old people",
    "retirees",
    "pensioners",
)
# What a community's amenity is called. ADR 0006 meets a request for community
# through these, and the v1 catalogue has no feature for one.
_AMENITIES = (
    "shop shops store stores supermarket supermarkets market markets butcher butchers bakery "
    "bakeries deli delis grocer grocers restaurant restaurants cafe cafes takeaway takeaways "
    "food pub pubs bar bars club clubs venue venues school schools nursery nurseries centre "
    "centres bookshop bookshops"
)
# Beside a cuisine, these are a kind of place to eat or drink, which is an ordinary wish.
_EATING = "restaurant restaurants cafe cafes takeaway takeaways food pub pubs bar bars"
# After a word for a group, these do not name what the group is asked for:
# "I am a student looking for a room" says who is asking, and asks for no one.
_NOT_NOUNS = (
    "a an the and or but at in on to of for from with who that which is are am was looking i we so"
)
# A group named as a noun. The plural is never a cuisine, so it stands alone.
_GROUP_NOUNS = (
    "blacks whites asians africans arabs poles indians pakistanis bangladeshis somalis turks "
    "catholics buddhists gays lesbians gypsies"
)

# Words for people, never for buildings. "Mosque" and "kosher shop" name
# amenities and are not here, or a request for them could never be heard. A
# word that also names a cuisine is here only beside a word for people, so that
# "Turkish cafes" is still a request for cafes.
POLICY_LEXICON = frozenset(
    {
        *(f"{group} {people}" for group in _GROUPS.split() for people in (*_PEOPLE, *_COUNTED)),
        # "Gay-friendly" asks who a place is for, as "a gay area" does.
        *(f"{group} friendly" for group in _GROUPS.split()),
        *_GROUP_NOUNS.split(),
        "benefit claimants",
        "people on benefits",
        "residents",
        "neighbours",
        "population",
        "students",
        "student area",
        "studenty",
        "immigrants",
        "immigrant",
        "migrants",
        "foreigners",
        "refugees",
        "asylum seekers",
        # What people do for work, and whether they have a partner, are counted by
        # nothing. "Young professionals" and "retirees" are not here: each is offered
        # for the age it names, and says that it counts no work.
        "professionals",
        "young couples",
        "singles",
        "hipsters",
        "yuppies",
        "working class",
        "middle class",
        "upper class",
        "posh people",
        "rich people",
        "poor people",
        "wealthy people",
        # How well off the people of a place are, said with no word for people.
        # Empty the houses and none of these is still true of the place. "Affluent"
        # and "posh" are not among them: each is offered, as of the place.
        "wealthy",
        "well off",
        "well to do",
        # A word for a smart area is of the place, and so is a word for a plain one
        # and for a rough one. Beside a word for people it is of them.
        *(
            f"{smart} {people}"
            for smart in (*_SMART, *_PLAIN, "rough")
            for people in (*_WHO.split(), *_COUNTED)
        ),
        *(f"{rich} {people}" for rich in ("rich", "wealthy", "poor") for people in _COUNTED),
        # People who sleep in the street are people, and "rough" says nothing of a place there.
        *("rough sleepers", "rough sleeper", "rough sleeping"),
        "council tenants",
        "people like me",
        "people like us",
        "my own kind",
        "ethnic",
        "ethnicity",
        "ethnic minorities",
        "diverse",
        "diversity",
        "multicultural",
        "muslims",
        "christians",
        "jews",
        "hindus",
        "sikhs",
        "lgbt",
        "lgbtq",
        "disabled people",
        "demographic",
        "demographics",
    }
)

_SOLD = ("shop", "shops", "food", "butcher", "butchers", "restaurant", "restaurants", "bakery")
# What Burro has no measure of. Each phrase is heard, makes no edit, and is
# reported by its category, so that a person is told in fixed words.
NO_MEASURE: Mapping[UnmetCategory, tuple[str, ...]] = {
    UnmetCategory.BROADBAND: ("broadband", "fibre", "internet", "wifi", "wi fi"),
    UnmetCategory.FLOOD_RISK: ("flood", "floods", "flooding", "flood risk"),
    # A GP practice and a pharmacy are measured, and are things of the lexicon.
    UnmetCategory.HEALTH_SERVICES: ("dentist", "dentists"),
    UnmetCategory.DRIVING: ("drive", "driving", "car", "parking", "motorway", "by car"),
    UnmetCategory.LISTINGS: ("listing", "listings", "available now", "on the market"),
    UnmetCategory.AFFORDABILITY_VERDICT: (
        "afford",
        "affordable",
        "can i afford",
        "good value",
        "value for money",
        "overpriced",
        "worth it",
        # What is cheap is a verdict too. Burro ranks on a budget that is set.
        "cheap",
        "inexpensive",
        "cheap rent",
        "cheap rents",
        "low rent",
        "low rents",
    ),
    UnmetCategory.COMMUNITY_AMENITIES: (
        "mosque",
        "church",
        "synagogue",
        "temple",
        "gurdwara",
        "place of worship",
        "places of worship",
        "kosher",
        "halal",
        *(f"{kind} {what}" for kind in ("kosher", "halal") for what in _SOLD),
    ),
    UnmetCategory.OUTSIDE_THE_CITY: (
        "outside london",
        "outside the city",
        "commuter belt",
        "commuter town",
        "home counties",
        "countryside",
    ),
    # No open data measures these at the scale of a neighbourhood.
    UnmetCategory.STREET_CLEANLINESS: (
        "clean streets",
        "street cleanliness",
        "litter",
        "fly tipping",
        "graffiti",
    ),
    # Rising damp is of one home, and of its upkeep: it is no rise in what homes sold for.
    UnmetCategory.UPKEEP: ("upkeep", "well maintained", "manicured", "run down", "rising damp"),
    UnmetCategory.RATINGS: (
        "highly rated",
        "best rated",
        "top rated",
        "ratings",
        "reviews",
        "award winning",
    ),
    UnmetCategory.PRICES_AND_HOURS: ("opening hours", "prices", "cheap gym", "budget gym"),
    UnmetCategory.MOBILE_COVERAGE: ("5g", "4g", "mobile signal", "phone signal", "mobile coverage"),
    # A place on the rise is read as of what homes sold for. These say who is moving in,
    # or that something other than a price is rising, which Burro cannot see.
    UnmetCategory.CHANGE_OVER_TIME: (
        "gentrifying",
        "gentrification",
        "rising crime",
        "rising rents",
        "rising rent",
    ),
}
# Where gritty is built from land use alone, a word for a well-kept street
# has nothing to be read as: Burro has no measure of upkeep.
_NO_MEASURE_IN: Mapping[GrittyVariant, Mapping[str, UnmetCategory]] = {
    GrittyVariant.A: dict.fromkeys(_UPKEEP, UnmetCategory.UPKEEP),
    GrittyVariant.B: {},
}


def _no_measure_of(variant: GrittyVariant) -> Mapping[str, UnmetCategory]:
    found = {phrase: category for category, phrases in NO_MEASURE.items() for phrase in phrases}
    found |= dict(_NO_MEASURE_IN[variant])
    # A phrase that the release has something to offer for is a thing of its lexicon.
    offered = _GRITTY[variant]
    return MappingProxyType(
        {phrase: what for phrase, what in found.items() if phrase not in offered}
    )


_LEXICONS = {variant: _lexicon_of(variant) for variant in GrittyVariant}
_NO_MEASURES = {variant: _no_measure_of(variant) for variant in GrittyVariant}


def lexicon_of(variant: GrittyVariant) -> Mapping[str, Target]:
    """Every phrase of the lexicon for a release that carries gritty in this way."""
    return _LEXICONS[variant]


def no_measure_of(variant: GrittyVariant) -> Mapping[str, UnmetCategory]:
    """Every phrase for what Burro has no measure of, with its category, for such a release."""
    return _NO_MEASURES[variant]


POLICY = re.compile(
    r"\b(?:"
    + "|".join(re.escape(p) for p in sorted(POLICY_LEXICON, key=lambda p: (-len(p), p)))
    + r")\b"
    # The character of the people, where it is said straight after them.
    + rf"(?: (?:{'|'.join(sorted(OF_A_PEOPLE))})\b)?"
)
DESCRIBES = re.compile(r"[a-z]+ $")
# The one name of a measure that says residents: the share of them that transport noise
# reaches. Typed whole, it is the name of the measure, and the word in it asks about
# nobody. Anywhere else the word is heard as it always is (ADR 0006).
NAMED_FOR_WHOSE_SHARE = re.compile(
    rf"\b{re.escape(prepare(FEATURES[FeatureId.NOISE_EXPOSURE].label))}\b"
)
# A phrase that is offered for who it counts, typed whole. A word for people in it asks
# for what is counted, and is heard as the phrase and as nothing else: "professionals" in
# "young professionals", "residents" in the name of a measure. A word for a group or for
# how well off people are, said before it, is a longer phrase of `POLICY_LEXICON`, which
# is heard first.
NAMED_FOR_WHO_IS_COUNTED = re.compile(
    r"\b(?:"
    + "|".join(
        re.escape(re.sub(r"[^a-z0-9]+", " ", phrase).strip())
        for phrase in sorted(WHO_IS_COUNTED, key=lambda phrase: (-len(phrase), phrase))
    )
    + r")\b"
)
_WORD = r"[a-z0-9]+"
ONLY_A_GROUP = frozenset(_GROUP_ONLY.split())
EATS = frozenset(_EATING.split())
NOT_A_NOUN = frozenset(_NOT_NOUNS.split())
# A word for a group, the word after it, and an amenity if one follows within three words.
GROUP = re.compile(
    rf"\b(?P<group>{'|'.join(_GROUPS.split())})\b"
    rf"(?:(?P<amenity>(?:\s+{_WORD}){{0,2}}?\s+(?:{'|'.join(_AMENITIES.split())}))\b"
    rf"|\s+(?P<noun>{_WORD}))?"
)

# After a cue that expects the name of a place, these name none: "I commute to
# work", "I study at uni". Nothing is added and nothing is asked, because there
# is nothing to choose from. A name that begins with one is still a name.
_GENERIC = (
    "work office offices school schools uni university college campus home house job site "
    "sites town city centre center client clients customers meetings night nights day days "
    "weekends shifts places somewhere anywhere everywhere various different there here it"
)
GENERIC_PLACES = frozenset(_GENERIC.split())
