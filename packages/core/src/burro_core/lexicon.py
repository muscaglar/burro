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

Burro ranks places, never residents. `POLICY_LEXICON` holds words for people,
never for buildings. A word of it is heard, makes no edit, and gets one
neutral sentence (ADR 0006).
"""

import re
import unicodedata
from collections.abc import Mapping
from types import MappingProxyType
from typing import NamedTuple

from burro_core.catalogue import (
    CRIME_CAVEAT,
    FEATURES,
    GRITTY,
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
NO_GYMS = (
    "Burro has no data on gyms, pools or leisure centres yet. "
    "The nearest it can count is what there is to do in parks within a walk."
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
PLACES_NOT_PEOPLE = "Burro measures places, not the people in them."
NO_IDENTITY = (
    "Burro cannot measure the character of a place. The nearest it can count are a village "
    "feel, the age of the buildings and a town centre nearby. Choose any that fit what you mean."
)
NO_CHANGE = (
    "Burro cannot see how a place is changing. "
    "The nearest it can say is where a place stands on this scale today."
)


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
        found[prepare(feature.label)] = named
        # The short label of a nuisance says the wish: "Less transport noise".
        found[prepare(feature.short_label)] = (
            _low(ranked) if ranked in NUISANCES else _feature(ranked)
        )
    for tag_id, tag in TAGS.items():
        named = _tag(tag_id)._replace(no_end=tag.shape is TagShape.SCALE)
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
        _nearest(NO_GYMS, features=(_F.PARK_FACILITIES,)),
        *("gym", "gyms", "leisure centre", "leisure centres", "sports centre"),
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
    **_said(
        _feature(_F.VENUE_FOOD_DRINK_PER_HOMES),
        "restaurants",
        "cafes",
        "coffee shops",
        "places to eat",
        "eating out",
    ),
    **_said(_tag(_T.FOODIE), "foodie"),
    **_said(_tag(_T.FOODIE, _INFERRED), "food scene", "good food"),
    **_said(_feature(_F.VENUE_EVENING), "pubs", "bars", "pub", "bar"),
    **_said(_tag(_T.PACE), "buzzy"),
    **_said(_tag(_T.PACE, _INFERRED), "lively", "bustling", "nightlife", "night life"),
    **_said(_tag(_T.PACE, _INFERRED, Toward.LOW), "calm", "sleepy"),
    **_said(
        _feature(_F.VENUE_INDEPENDENT),
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
    **_said(
        _feature(_F.STATION_WALK),
        "near a station",
        "close to a station",
        "near the station",
        "near the tube",
        "tube station",
        "train station",
        "station nearby",
        "station",
        "stations",
        "the tube",
    ),
    **_said(
        _feature(_F.STATION_LINES, _INFERRED),
        "transport links",
        "well connected",
        "good transport",
        "connections",
    ),
    **_said(_tag(_T.EVERYDAY_ON_FOOT), "walkable", "walkability"),
    **_said(_tag(_T.VILLAGE_FEEL), "villagey", "village", "villages"),
    **_said(
        _tag(_T.FAMILY_AMENITIES, _INFERRED),
        "family friendly",
        "good for kids",
        "good for families",
    ),
}

_MIXED = tuple(MIXED_WORDS)
_UPKEEP = ("polished", "smart", "well kept")
_WORKS = ("industrial", "warehouses")


# What a word for a smart area is offered as, wherever what homes sell for is held: homes
# that sell for more than the middle. Decided on 2026-09-24. It is never applied.
_SELLS_FOR_MORE = Target((_F.PRICE_MEDIAN,), (), _INFERRED, note=PLACES_NOT_PEOPLE, one_way=True)


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
        # A smart area, read as of the place. The scale is not held here, so it has the
        # one reading: what homes sell for. "Smart" is a word for upkeep here.
        **_said(_SELLS_FOR_MORE, *(word for word in _SMART if word not in _UPKEEP)),
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
        # A smart area, read as of the place, in two ways for the person to choose
        # from: towards the polished end, and homes that sell for more. Each is offered
        # that one way. Nothing of what people earn or who they are is read into it.
        **_said(_SELLS_FOR_MORE._replace(tags=(_T.STREET_CHARACTER,), toward=Toward.LOW), *_SMART),
        **_said(_tag(_T.STREET_CHARACTER, _INFERRED), "rough"),
        **_said(
            _tag(_T.STREET_CHARACTER, _INFERRED)._replace(
                note=NO_CHANGE, unmet=UnmetCategory.CHANGE_OVER_TIME
            ),
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
        *(f"{group} {people}" for group in _GROUPS.split() for people in _PEOPLE),
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
        "young professionals",
        "professionals",
        "young families",
        "lots of families",
        "full of families",
        "other families",
        "young people",
        "young couples",
        "old people",
        "older people",
        "elderly",
        "pensioners",
        "retirees",
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
        # A word for a smart area is of the place, and so is a word for a rough
        # one. Beside a word for people it is of them.
        *(f"{smart} {people}" for smart in (*_SMART, "rough") for people in _WHO.split()),
        *(f"{rich} families" for rich in ("rich", "wealthy", "poor")),
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
    UnmetCategory.HEALTH_SERVICES: ("gp", "doctor", "doctors", "dentist", "pharmacy", "surgery"),
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
    UnmetCategory.UPKEEP: ("upkeep", "well maintained", "manicured", "run down"),
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
    UnmetCategory.CHANGE_OVER_TIME: (
        "up and coming",
        "gentrifying",
        "gentrification",
        "on the up",
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
