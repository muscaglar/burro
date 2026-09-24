"""Interpreters: from what a person typed to typed edits.

`RuleInterpreter` needs no model and no network, so the product still works as
a form when a model is slow, capped or absent. It reads the text, produces
edits, and keeps none of the words: assumptions and unmet requests are codes,
notices are fixed text, and clarification options come from the release.

It reads a sentence only when it knows every token in it. It is a fallback,
and the controls on screen are always there, so a wish it does not read costs
little and a wish it reverses costs trust. English has too many words that
turn a wish round, and people mistype them, so the reader keeps no list of
them. It keeps the list of what it does know, `burro_core.vocabulary`, and a
sentence that holds anything else makes no edit and is reported as unread.

A sentence ends at a full stop, a question mark, an exclamation mark or a
line break, and nowhere else. A question makes no edit. A sentence that holds
doubt and names nothing takes back what the sentences beside it raised.

Every edit says which words of the text it rests on, by where they start and
end. Nothing here keeps the words.

Burro ranks places, never residents. A request about who lives somewhere gets
one neutral sentence and no edit, because no id exists that could express it.
"""

import re
import unicodedata
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from itertools import pairwise
from typing import NamedTuple, Protocol

from burro_core._record import Record
from burro_core.catalogue import FEATURES, TAGS
from burro_core.ids import (
    AreaAction,
    AssumptionCode,
    BudgetAction,
    CommuteAction,
    DirectionChoice,
    EditProvenance,
    FeatureId,
    InterpreterName,
    InterpretStatus,
    ModeChoice,
    Notice,
    OpsGroup,
    OptionKind,
    PlaceKind,
    Polarity,
    Provenance,
    SegmentChoice,
    Step,
    StrictnessChoice,
    TagId,
    Tenure,
    TenureChoice,
    UnmetCategory,
    WeightAction,
)
from burro_core.ops import AreaEdit, BudgetEdit, CommuteEdit, Operations, TagEdit, WeightEdit
from burro_core.places import MAX_OPTIONS, Match, Names
from burro_core.release import Release
from burro_core.spec import LIMITS, PreferenceSpec
from burro_core.vocabulary import (
    ALSO_AT_THE_END,
    CAPS,
    CAPS_FIRMLY,
    ESSENTIAL,
    LARGE_STEP,
    NEAR_TO,
    NEVER_READ,
    NOT_IN,
    ONLY_IN,
    PHRASES_OF_DOUBT,
    PLAIN_PHRASES,
    PLAIN_WORDS,
    SMALL_STEP,
    TAKES_OFF,
    TAKES_OFF_AFTER,
    TROUBLES,
    TURNS_DOWN,
    TURNS_DOWN_AFTER,
    TURNS_FIRMLY,
    TURNS_SOFTLY,
    WORDS_OF_DOUBT,
)

MAX_TEXT = 600
MAX_NAME_WORDS = 6
_MAX_DIGITS = 12
_TOO_MANY = 10**12

NOTICES: Mapping[Notice, str] = {
    Notice.NONE: "",
    # The same for every group and every user.
    Notice.NEUTRAL_PLACES: (
        "Burro ranks places by what is there, such as schools, parks, venues and transport, "
        "and never by who lives there. The rest of your search has been applied."
    ),
    Notice.OFF_TOPIC: (
        "Burro helps you choose where to live. Say what you want from a place, or use the form."
    ),
}


@dataclass(frozen=True, repr=False)
class InterpretRequest:
    text: str
    spec: PreferenceSpec  # the spec to edit; a default for a first prompt
    release: Release

    def __post_init__(self) -> None:
        if not 1 <= len(self.text) <= MAX_TEXT:
            raise ValueError(f"text must be 1 to {MAX_TEXT} characters")

    def __repr__(self) -> str:
        # The text is what a person typed. It must never reach a log by way of a repr.
        return "InterpretRequest(text=<hidden>)"


class Assumption(Record):
    """What was chosen for an edit because the text did not say."""

    code: AssumptionCode
    group: OpsGroup
    index: int


class ClarifyOption(Record):
    id: str
    name: str
    kind: OptionKind


class Clarify(Record):
    """An edit whose place or area could not be settled, and what to offer instead."""

    group: OpsGroup
    index: int
    options: tuple[ClarifyOption, ...]


class RestsOn(Record):
    """Which words of the text an edit rests on: where they start and end, never the words.

    `start` and `end` count the characters of the text as it was typed, as
    Python counts them, so `text[start:end]` is the words. An edit made of
    several parts, as a budget is of "renting", "2 bed" and "£1,500", has one
    of these for each part. They are for showing a person which of their
    words made each edit. Nothing stores or logs them.
    """

    group: OpsGroup
    index: int
    start: int
    end: int


class Usage(Record):
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int


NO_USAGE = Usage(input_tokens=0, output_tokens=0, cache_read_tokens=0)


class InterpretResult(Record):
    status: InterpretStatus
    operations: Operations
    assumptions: tuple[Assumption, ...]
    unmet: tuple[UnmetCategory, ...]
    clarify: tuple[Clarify, ...]
    notice: Notice
    interpreter: InterpreterName
    degraded: bool
    usage: Usage
    # In the order of the six groups, then by edit, then by where the words stand.
    rests_on: tuple[RestsOn, ...] = ()


class Interpreter(Protocol):
    name: InterpreterName

    def interpret(self, request: InterpretRequest) -> InterpretResult: ...


# Every mark a person's keyboard may put where an apostrophe goes.
_APOSTROPHE = (
    "'`\N{RIGHT SINGLE QUOTATION MARK}\N{LEFT SINGLE QUOTATION MARK}"
    "\N{MODIFIER LETTER APOSTROPHE}\N{PRIME}\N{FULLWIDTH APOSTROPHE}"
)
_APOSTROPHES = re.compile(f"[{_APOSTROPHE}]")


def _plain(text: str) -> str:
    """Lower case and no accents, with every mark still where it was typed."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def prepare(text: str) -> str:
    """The text as the rules read it: lower case, no accents, no apostrophes, single spaces."""
    bare = _APOSTROPHES.sub("", _plain(text)).replace("&", " and ")
    return re.sub(r"\s+", " ", re.sub(r"[-_/\"()\[\]]", " ", bare)).strip()


class Target(NamedTuple):
    """What a phrase of the lexicon means: features and tags, and how they were named."""

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


_F = FeatureId
_T = TagId
_STATED = EditProvenance.STATED
_INFERRED = EditProvenance.INFERRED
_CRIME = (_F.CRIME_VIOLENCE_ROBBERY, _F.CRIME_BURGLARY_THEFT)

# The features it is a nuisance to have more of. Wanting less of one is caring
# about it. Wanting less of anything else is a wish no weight may be raised for.
NUISANCES = frozenset({*_CRIME, _F.AIR_NO2, _F.NOISE_EXPOSURE})


def _said(target: Target, *phrases: str) -> dict[str, Target]:
    return dict.fromkeys(phrases, target)


def _feature(feature_id: FeatureId, provenance: EditProvenance = _STATED) -> Target:
    return Target((feature_id,), (), provenance)


def _nuisance(*feature_ids: FeatureId, provenance: EditProvenance = _STATED) -> Target:
    return Target(feature_ids, (), provenance, nuisance=True)


def _low(*feature_ids: FeatureId) -> Target:
    return Target(feature_ids, (), _STATED, nuisance=True, wanted_low=True)


def _tag(tag_id: TagId, provenance: EditProvenance = _STATED) -> Target:
    return Target((), (tag_id,), provenance)


# Every feature and tag answers to its label. The phrases below are the other
# ways people ask for one. A phrase is `stated` when it names the thing, and
# `inferred` when the thing is read into looser words.
LEXICON: Mapping[str, Target] = {
    **{
        prepare(feature.label): _nuisance(feature_id)
        if feature_id in NUISANCES
        else _feature(feature_id)
        for feature_id, feature in FEATURES.items()
    },
    **{prepare(tag.label): _tag(tag_id) for tag_id, tag in TAGS.items()},
    # Crime is weighted only on an explicit request. "Safe" is not one: it is
    # inferred, so the reducer turns it away and the user is pointed to the control.
    **_said(_nuisance(*_CRIME), "crime", "crime rate", "crime rates"),
    **_said(_low(*_CRIME), "low crime", "low crime rate", "low crime rates"),
    **_said(Target(_CRIME, (), _INFERRED), "safe", "safer", "safety"),
    **_said(_nuisance(*_CRIME, provenance=_INFERRED), "unsafe", "dangerous"),
    **_said(_nuisance(_F.CRIME_BURGLARY_THEFT), "burglary", "burglaries", "theft", "thefts"),
    **_said(_nuisance(_F.CRIME_VIOLENCE_ROBBERY), "violent crime", "violence", "robbery"),
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
    **_said(_tag(_T.NEAR_UNIVERSITIES), "universities", "university", "near a university"),
    **_said(_tag(_T.NEAR_UNIVERSITIES, _INFERRED), "campus", "uni"),
    **_said(_feature(_F.GREEN_COVER), "green space", "green spaces", "greenspace"),
    **_said(_tag(_T.LEAFY, _INFERRED), "green", "greenery", "trees", "tree lined"),
    **_said(_feature(_F.PARK_PROXIMITY), "park", "parks", "near a park", "close to a park"),
    **_said(
        _feature(_F.PLAY_SPACE_PROXIMITY),
        "playground",
        "playgrounds",
        "play area",
        "play areas",
        "play space",
        "play spaces",
    ),
    **_said(_tag(_T.WATERSIDE, _INFERRED), "river", "canal", "riverside", "by the water", "water"),
    **_said(_feature(_F.AIR_NO2), "air quality"),
    **_said(_nuisance(_F.AIR_NO2), "pollution", "polluted", "nitrogen dioxide"),
    **_said(_low(_F.AIR_NO2), "low pollution"),
    **_said(_feature(_F.AIR_NO2, _INFERRED), "clean air", "fresh air"),
    **_said(_nuisance(_F.AIR_NO2, provenance=_INFERRED), "fumes"),
    **_said(_nuisance(_F.NOISE_EXPOSURE), "noise", "noisy", "traffic noise"),
    **_said(_low(_F.NOISE_EXPOSURE), "low noise"),
    **_said(_tag(_T.QUIET_RESIDENTIAL), "quiet", "quieter"),
    **_said(
        _tag(_T.QUIET_RESIDENTIAL, _INFERRED),
        "peaceful",
        "calm",
        "tranquil",
        "residential",
        "peace and quiet",
    ),
    **_said(
        _feature(_F.VENUE_FOOD_DRINK),
        "restaurants",
        "cafes",
        "coffee shops",
        "places to eat",
        "eating out",
    ),
    **_said(_tag(_T.FOODIE, _INFERRED), "food scene", "good food", "great food"),
    **_said(_feature(_F.VENUE_EVENING), "pubs", "bars", "pub", "bar"),
    **_said(_tag(_T.EVENING_VENUES, _INFERRED), "nightlife", "night life", "going out"),
    **_said(
        _feature(_F.VENUE_INDEPENDENT),
        "independent shops",
        "independent cafes",
        "independents",
        "independent",
    ),
    **_said(
        _feature(_F.CULTURE_VENUES),
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
    **_said(_feature(_F.CULTURE_VENUES, _INFERRED), "culture", "cultural", "arts"),
    **_said(_feature(_F.HIGHSTREET_ACCESS), "high street", "town centre", "highstreet"),
    **_said(_feature(_F.HIGHSTREET_ACCESS, _INFERRED), "shops", "shopping"),
    **_said(_tag(_T.STRONG_HIGH_STREET), "good high street", "great high street"),
    **_said(_feature(_F.HOMES_PRE1919), "pre 1919", "built before 1919"),
    **_said(
        _feature(_F.HOMES_PRE1919, _INFERRED),
        "period homes",
        "period houses",
        "period properties",
        "victorian",
        "georgian",
        "edwardian",
    ),
    **_said(_tag(_T.HISTORIC_CHARACTER, _INFERRED), "historic", "heritage", "character"),
    **_said(_feature(_F.CONSERVATION_COVER), "conservation area", "conservation areas"),
    **_said(_feature(_F.HOMES_DENSITY), "density", "dense", "built up"),
    **_said(
        Target((_F.HOMES_DENSITY,), (), _INFERRED, DirectionChoice.LESS),
        "low density",
        "spacious",
        "not built up",
    ),
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
    **_said(_tag(_T.VILLAGE_FEEL), "villagey", "village", "village vibe", "village like"),
    **_said(_tag(_T.BUZZY, _INFERRED), "lively", "vibrant", "bustling", "buzz"),
    **_said(_tag(_T.CREATIVE, _INFERRED), "arty", "artsy", "artistic"),
    **_said(
        _tag(_T.FAMILY_AMENITIES, _INFERRED),
        "family friendly",
        "child friendly",
        "kid friendly",
        "good for kids",
        "good for children",
    ),
}

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
_UNMET: Mapping[UnmetCategory, tuple[str, ...]] = {
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
}


_POLICY = re.compile(
    r"\b(?:"
    + "|".join(re.escape(p) for p in sorted(POLICY_LEXICON, key=lambda p: (-len(p), p)))
    + r")\b"
)
_DESCRIBES = re.compile(r"[a-z]+ $")
_WORD = r"[a-z0-9]+"
_ONLY_A_GROUP = frozenset(_GROUP_ONLY.split())
_EATS = frozenset(_EATING.split())
_NOT_A_NOUN = frozenset(_NOT_NOUNS.split())
# A word for a group, the word after it, and an amenity if one follows within three words.
_GROUP = re.compile(
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


# --- What the reader knows besides the plain words --------------------------------
#
# Each of these is a word the reader has a rule for, and is known only where
# that rule reads it. They are here, beside the rules, and not in
# `vocabulary.py`, because each is tied to the edit it makes.

# Words that expect the name of a place to follow. The speaker does the working:
# "works at" and "worked at" are not here, so another's workplace and a former
# one are never read.
_EXPECTS_A_NAME = frozenset(
    f"{verb} {where}"
    for verb in ("work", "working", "based", "study", "studying")
    for where in ("at", "in", "near")
) | frozenset(
    {
        *(f"{verb} to" for verb in ("commute", "commuting", "travel", "travelling")),
        *(
            f"{noun} {verb} {where}"
            for noun in ("office", "job")
            for verb in ("is",)
            for where in ("at", "in", "near")
        ),
        *(f"{noun} {where}" for noun in ("office", "job") for where in ("at", "in")),
    }
)
# After a number of minutes: "30 minutes to X", "within 25 minutes of X".
_TO_A_PLACE = frozenset({"to", "from", "of"})
_TRAVELLED = frozenset(
    {"walk", "cycle", "bike ride", "ride", "commute", "journey", "trip", "travel"}
)
_MINUTES = frozenset({"min", "mins", "minute", "minutes"})
_BEDROOMS = frozenset({"bed", "beds", "bedroom", "bedrooms", "bedroomed"})
_MONTHLY = frozenset({"pcm", "pm", "per month", "a month", "monthly", "per calendar month"})
_CYCLED = frozenset({"cycle", "cycling", "bike", "biking", "bicycle", "by bike"})
_WALKED = frozenset({"walk", "walking", "on foot"})
_BY_TRANSPORT = frozenset(
    {"tube", "train", "bus", "tram", "underground", "overground", "public transport"}
)
_RENTS = frozenset({"rent", "renting", "rental", "tenancy", "to rent", "to let"})
_BUYS = frozenset({"buy", "buying", "purchase", "purchasing", "mortgage", "to buy", "for sale"})
_MONEY_WORDS = frozenset({"budget", "budget of", "budget is", "spend", "pay", "pounds", "quid"})
_RENT_SEGMENTS: Mapping[str, SegmentChoice] = {
    "studio": SegmentChoice.STUDIO,
    # "Room" by itself is also space, "room for a desk", so it is known with its article.
    "a room": SegmentChoice.ROOM,
    "room to rent": SegmentChoice.ROOM,
    "flatshare": SegmentChoice.ROOM,
    "flat share": SegmentChoice.ROOM,
    "house share": SegmentChoice.ROOM,
    "houseshare": SegmentChoice.ROOM,
}
_BUY_SEGMENTS: Mapping[str, SegmentChoice] = {
    "flat": SegmentChoice.FLAT,
    "apartment": SegmentChoice.FLAT,
    "maisonette": SegmentChoice.FLAT,
    "terraced": SegmentChoice.TERRACED,
    "terrace": SegmentChoice.TERRACED,
    "semi detached": SegmentChoice.SEMI_DETACHED,
    "semi": SegmentChoice.SEMI_DETACHED,
    "detached": SegmentChoice.DETACHED,
}
_BEDS = (
    SegmentChoice.BED_1,
    SegmentChoice.BED_2,
    SegmentChoice.BED_3,
    SegmentChoice.BED_4PLUS,
)
_CHEAPER = frozenset({"cheaper", "less expensive", "lower budget", "lower my budget"})
_DEARER = frozenset(
    {"raise my budget", "increase my budget", "stretch my budget", "raise the budget"}
)
_COUNTED: Mapping[str, int] = {
    **{
        word: n
        for n, word in enumerate(
            ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"], 1
        )
    },
    "fifteen": 15,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "forty five": 45,
    "fifty": 50,
    "sixty": 60,
}
# "A 40 minute commute", said apart from any place.
_A_JOURNEY = frozenset({"commute", "journey"})
# What joins two wishes, and how.
_JOINS = frozenset({"and", "or", "but", "plus"})
# What may stand in an item of a list beside the thing itself: "a park", "any pubs nearby".
_BARE = frozenset(
    [
        "a",
        "an",
        "the",
        "any",
        "some",
        "more",
        "many",
        "much",
        "lots",
        "lot",
        "of",
        "loads",
        "plenty",
        "nearby",
        "close",
        "by",
        "around",
    ]
)
_SPEAKS = frozenset({"i", "we", "i'm", "im", "i'd", "we're", "we'd"})
_WISHES = frozenset({"want", "need", "like", "love", "looking", "would", "must"})
# What may stand before the words of an area rule or of a journey, and after them.
# Anything else is a subject the reader does not know: "some avoid Tallowgate".
_LEADS_IN = (
    _SPEAKS
    | _WISHES
    | frozenset(
        [
            "am",
            "to",
            "be",
            "live",
            "living",
            "somewhere",
            "please",
            "really",
            "definitely",
            "it",
            "is",
            "that",
        ]
    )
    | frozenset(["my", "our", "so", "also", "the", "and"])
)
_FOLLOWS = frozenset({"please", "thanks", "thank you", "only", "as well", "ideally"})
# With one of these first, the words that follow ask and do not tell: "is there a park".
_ASKS = frozenset({"is", "are", "am"})
# And with one of these straight before the speaker: "would I want a pub next door".
_ASKS_OF = frozenset({"is", "are", "am", "would", "must", "have", "has"})
# What may limit a number from after it, where "under" and "up to" never stand.
_SAID_AFTER_A_NUMBER = CAPS_FIRMLY | frozenset({"max", "maximum"})
# No rent and no price is this low, so a smaller number that has no sign of money on
# it is a number of things, "at most 2 pubs", which is no limit the reader sets.
_LEAST_MONEY = 100

_TURNS = TURNS_FIRMLY | TURNS_SOFTLY
# The words the reader has a rule for that no sentence may hold unread. One
# that no rule accounts for leaves the whole sentence unread.
_MUST_BE_READ = (
    _TURNS
    | TAKES_OFF
    | TAKES_OFF_AFTER
    | TURNS_DOWN
    | TURNS_DOWN_AFTER
    | TROUBLES
    | CAPS_FIRMLY
    | (CAPS - PLAIN_WORDS)
    | ONLY_IN
    | NOT_IN
    | (NEAR_TO - PLAIN_WORDS - PLAIN_PHRASES)
    | _CHEAPER
    | _DEARER
    | NEVER_READ
)
# Every phrase of the vocabulary, plain or with a rule of its own.
VOCABULARY: frozenset[str] = frozenset(
    {
        *PLAIN_WORDS,
        *PLAIN_PHRASES,
        *_MUST_BE_READ,
        *SMALL_STEP,
        *LARGE_STEP,
        *ESSENTIAL,
        *NEAR_TO,
        *_EXPECTS_A_NAME,
        *_MINUTES,
        *_BEDROOMS,
        *_MONTHLY,
        *_CYCLED,
        *_WALKED,
        *_BY_TRANSPORT,
        *_RENTS,
        *_BUYS,
        *_MONEY_WORDS,
        *_RENT_SEGMENTS,
        *_BUY_SEGMENTS,
        *_COUNTED,
        *_TRAVELLED,
        *_A_JOURNEY,
        *_JOINS,
        "to work",
        "by",
    }
)


# --- The text, token by token --------------------------------------------------

_LINE_BREAK = re.compile(r"[\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029]")
_CHUNK = re.compile(r"\S+")
_BRACKETS_OPEN = "([{"
_BRACKETS_CLOSE = ")]}"
_QUOTES = (
    '"\N{LEFT DOUBLE QUOTATION MARK}\N{RIGHT DOUBLE QUOTATION MARK}'
    "\N{DOUBLE LOW-9 QUOTATION MARK}\N{LEFT-POINTING DOUBLE ANGLE QUOTATION MARK}"
    "\N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK}"
)
_LISTS = ",;:"
_ENDS = ".!?\N{HORIZONTAL ELLIPSIS}"
_DASHES = "-\N{EN DASH}\N{EM DASH}\N{HORIZONTAL BAR}"
_BEFORE = _BRACKETS_OPEN + _QUOTES + _APOSTROPHE
_AFTER = _BRACKETS_CLOSE + _QUOTES + _APOSTROPHE + _LISTS + _ENDS
# A word, with nothing in it but letters, digits, and an apostrophe or a hyphen
# between two of them.
_A_WORD = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)*")
_AMOUNT = re.compile(r"(£)?([0-9][0-9,]*(?:\.[0-9]+)?)(k|m)?(pcm|pm)?")
_GLUED = re.compile(
    r"([0-9]+|[a-z]+)-?(min|mins|minute|minutes|bed|beds|bedroom|bedrooms|bedroomed)"
)


class _Token(NamedTuple):
    """One run of characters with no space in it, as it was typed and as it is read.

    A token is never split at a mark inside it: "don;t" is one token, and one
    the reader does not know.
    """

    # As the vocabulary holds a word: lower case, no accents, its apostrophe as "'".
    word: str
    # As the lexicon and the names hold one: with no apostrophe, and a hyphen as a space.
    bare: str
    start: int
    end: int
    # A mark or a line break stands between it and the token before it, so the two
    # are never read as one phrase or one name.
    apart: bool
    # It is written with a hyphen, so it is read whole or not at all.
    joined: bool
    # It holds a mark the reader does not read, or stands in quotes.
    odd: bool


class _Line(NamedTuple):
    """The tokens of one sentence, and how it ended."""

    tokens: tuple[_Token, ...]
    start: int
    end: int
    asked: bool  # it ends in a question mark
    heads: bool  # it ends in a colon or a dash, as a heading does


def _lines(text: str) -> list[_Line]:
    """The sentences of a text. One ends at a full stop, "?", "!" or a line break, only there."""
    lines: list[_Line] = []
    tokens: list[_Token] = []
    asked = False
    apart = False
    trailing = ""
    began = position = 0

    def close(at: int) -> None:
        nonlocal tokens, asked, apart, trailing, began
        if tokens:
            heads = trailing[-1:] in (":", *_DASHES) if trailing else False
            lines.append(_Line(tuple(tokens), began, tokens[-1].end, asked, heads))
        tokens, asked, apart, trailing, began = [], False, False, "", at

    for chunk in _CHUNK.finditer(text):
        if _LINE_BREAK.search(text, position, chunk.start()):
            close(chunk.start())
        position = chunk.end()
        typed = chunk.group()
        lead = 0
        while lead < len(typed) and typed[lead] in _BEFORE:
            lead += 1
        tail = len(typed)
        while tail > lead and typed[tail - 1] in _AFTER:
            tail -= 1
        before, core, after = typed[:lead], typed[lead:tail], typed[tail:]
        if not tokens:
            began = chunk.start()
        if core and all(c in _DASHES for c in core):
            # A dash with a space each side parts two wishes, as a comma does.
            apart, trailing, core = True, trailing + core, ""
        if core:
            plain = _APOSTROPHES.sub("'", _plain(core))
            word = "and" if plain in ("&", "+") else plain
            shaped = _A_WORD.fullmatch(word) or _AMOUNT.fullmatch(word)
            quoted = any(c in _QUOTES or c in _APOSTROPHE for c in before) or any(
                c in _QUOTES for c in after
            )
            bare = word.replace("'", "").replace("-", " ")
            tokens.append(
                _Token(
                    word=word,
                    bare=bare,
                    start=chunk.start() + lead,
                    end=chunk.start() + tail,
                    apart=apart or bool(before),
                    joined="-" in word,
                    odd=not shaped or quoted,
                )
            )
            apart, trailing = False, ""
        marks = after if core else typed
        if marks:
            apart, trailing = True, trailing + marks
        if any(c in _ENDS for c in marks):
            asked = asked or "?" in marks
            if tokens:
                close(chunk.end())
            asked = False
    close(len(text))
    return lines


# --- What each token is ----------------------------------------------------------


class _Is(Enum):
    UNKNOWN = "unknown"
    WORD = "word"  # a word or a phrase of the vocabulary
    THING = "thing"  # a phrase of the lexicon
    NAME = "name"  # the whole of a name of the release
    NUMBER = "number"
    PEOPLE = "people"  # a word for who lives somewhere
    AMENITY = "amenity"  # a community's amenity, which no feature covers
    UNMET = "unmet"  # something Burro cannot answer
    ASKED = "asked"  # words given as the name of a place, that are the name of none
    GENERIC = "generic"  # "work", "the office": a place that was not named


@dataclass
class _Item:
    """One or more tokens read as one thing, and where in the text they stand."""

    what: _Is
    text: str
    first: int
    last: int
    start: int
    end: int
    # A mark stands between it and the item before it.
    apart: bool
    place: str = ""
    area: str = ""
    value: int = 0
    money: bool = False
    unit: str = ""
    unmet: UnmetCategory | None = None
    # A rule has accounted for it.
    read: bool = False


def _by_first_word(phrases: Iterable[str]) -> dict[str, list[tuple[str, ...]]]:
    """Phrases by the word each begins with, the longest first."""
    found: dict[str, list[tuple[str, ...]]] = {}
    for phrase in phrases:
        words = tuple(phrase.split())
        found.setdefault(words[0], []).append(words)
    for listed in found.values():
        listed.sort(key=lambda words: (-len(words), words))
    return found


_UNMET_OF: Mapping[str, UnmetCategory] = {
    phrase: category for category, phrases in _UNMET.items() for phrase in phrases
}
_VOCABULARY_BY = _by_first_word(VOCABULARY)
_LEXICON_BY = _by_first_word(phrase for phrase in LEXICON if "," not in phrase)
# The labels that hold a comma or a number typed with a hyphen, by their first word.
_LABELS: dict[str, list[tuple[str, tuple[str, ...]]]] = {}
for _label in (*FEATURES.values(), *TAGS.values()):
    _printed = prepare(_label.label)
    _LABELS.setdefault(_printed.split()[0].rstrip(","), []).append(
        (_printed, tuple(_printed.split()))
    )
_UNMET_BY = _by_first_word(_UNMET_OF)

# What it costs to read a token one way and not another. The reading that leaves the
# fewest tokens unknown is taken, and of two that leave none, the one made of the longest
# phrases: so "good transport links" is "good" and "transport links", though "good
# transport" is a phrase too, and "Wexmoor University" is the campus and not Wexmoor.
_COST_UNKNOWN = 1000.0
_COST_WORD = 3.0
_COST_PHRASE = 1.0
_COST_CUE = 0.9
_COST_NAME = 0.8


def _number(token: _Token) -> _Item | None:
    """A number, an amount of money, or a number typed with its unit: "30mins", "2-bed"."""
    found = _AMOUNT.fullmatch(token.word)
    if found is not None:
        pound, digits, scale, monthly = found.groups()
        if scale == "m" and not pound:
            return None  # "5m" is as likely five minutes or five metres as five million
        return _Item(
            _Is.NUMBER,
            "",
            0,
            0,
            token.start,
            token.end,
            token.apart,
            value=_whole(digits, scale or ""),
            money=bool(pound or scale or monthly),
            unit="month" if monthly else "",
        )
    glued = _GLUED.fullmatch(token.word)
    if glued is None:
        return None
    count, unit = glued.groups()
    value = int(count) if count.isdigit() else _COUNTED.get(count)
    if value is None or len(count) > _MAX_DIGITS:
        return None
    kind = "min" if unit in _MINUTES else "bed"
    return _Item(_Is.NUMBER, "", 0, 0, token.start, token.end, token.apart, value=value, unit=kind)


def _whole(number: str, suffix: str = "") -> int:
    """A number as it was written, as a whole number. Absurdly long ones are capped.

    The cap is far outside every limit, so the reducer still turns the edit
    away as out of range, and nothing here can overflow on the way to it.
    """
    scale = {"k": 1_000, "m": 1_000_000}.get(suffix, 1)
    digits = number.replace(",", "")
    if len(digits.split(".")[0]) > _MAX_DIGITS:
        return _TOO_MANY
    return min(round(float(digits) * scale), _TOO_MANY)


def _together(tokens: Sequence[_Token], first: int, size: int) -> bool:
    """Whether some tokens stand side by side with nothing but a space between them."""
    run = tokens[first : first + size]
    if len(run) < size or any(token.odd for token in run):
        return False
    if size == 1:
        return True
    return not any(token.joined for token in run) and not any(t.apart for t in run[1:])


def _labels_at(tokens: Sequence[_Token], at: int) -> Iterator[tuple[str, int]]:
    """Each label of the catalogue that the tokens spell from `at`, marks and all.

    A label is fixed text, "Pubs, bars and evening venues", and is read as it
    is printed: with its own commas and its own hyphen, and with no others.
    """
    for label, words in _LABELS.get(tokens[at].bare.split()[0], ()):
        spelt: list[str] = []
        size = 0
        while len(spelt) < len(words) and at + size < len(tokens):
            token = tokens[at + size]
            parts = token.bare.split()
            comma = len(spelt) > 0 and words[len(spelt) - 1].endswith(",")
            if token.odd or (size > 0 and token.apart and not comma):
                break
            spelt += parts
            size += 1
        if spelt == [word.rstrip(",") for word in words]:
            yield label, size


def _phrases_at(
    tokens: Sequence[_Token], at: int, table: Mapping[str, list[tuple[str, ...]]], bare: bool
) -> Iterator[tuple[str, int]]:
    """Each phrase of a table that the tokens spell from `at`, and how many tokens it takes."""
    token = tokens[at]
    if token.joined:
        # Written with a hyphen, it is a phrase only as a whole: "well-connected".
        words = tuple(token.bare.split())
        if words in table.get(words[0], ()):
            yield " ".join(words), 1
        return
    for words in table.get(token.bare if bare else token.word, ()):
        size = len(words)
        if not _together(tokens, at, size):
            continue
        spelt = tuple((t.bare if bare else t.word) for t in tokens[at : at + size])
        if spelt == words:
            yield " ".join(words), size


def _names_at(tokens: Sequence[_Token], at: int, names: Names | None) -> Iterator[_Item]:
    """The places and areas whose whole name the tokens spell from `at`, as typed.

    A name is never put together across a mark, a hyphen or a line break.
    """
    if names is None or tokens[at].joined or tokens[at].bare not in names.first_words:
        return
    for size in range(min(names.longest, len(tokens) - at), 0, -1):
        if not _together(tokens, at, size):
            continue
        spelling = " ".join(token.bare for token in tokens[at : at + size])
        place, area = names.whole_place(spelling), names.whole_area(spelling)
        if place is not None or area is not None:
            yield _item(tokens, _Is.NAME, spelling, at, size, place=place or "", area=area or "")


def _item(
    tokens: Sequence[_Token],
    what: _Is,
    text: str,
    first: int,
    size: int,
    place: str = "",
    area: str = "",
    unmet: UnmetCategory | None = None,
) -> _Item:
    return _Item(
        what,
        text,
        first,
        first + size,
        tokens[first].start,
        tokens[first + size - 1].end,
        tokens[first].apart,
        place=place,
        area=area,
        unmet=unmet,
    )


def _people_in(tokens: Sequence[_Token]) -> tuple[dict[int, _Is], bool]:
    """Which tokens are about who lives somewhere, or name a community's amenity.

    A word for a kind of resident is closed to every other rule, so it can
    never be quietly turned into a feature or a tag. It is heard in every
    sentence, read or not. Said of a venue or a shop, a word for a group asks
    for a community's amenity. Said of anything else it asks who lives
    somewhere, and the noun is closed with it, so that "gay village" is never
    read as a wish for a village.
    """
    spelt = [re.sub(r"[^a-z0-9]+", " ", token.bare).strip() or "?" for token in tokens]
    line = " ".join(spelt)
    owner: list[int] = []
    for index, word in enumerate(spelt):
        owner += [index] * (len(word) + 1)
    found: dict[int, _Is] = {}

    def mark(start: int, end: int, what: _Is) -> None:
        for index in sorted(set(owner[start:end])):
            found.setdefault(index, what)

    about_people = False
    for match in _POLICY.finditer(line):
        # The word before describes the people too: "quiet neighbours" asks
        # for a kind of neighbour, not for a quiet place.
        described = _DESCRIBES.search(line, 0, match.start())
        mark(described.start() if described else match.start(), match.end(), _Is.PEOPLE)
        about_people = True
    for match in _GROUP.finditer(line):
        if any(index in found for index in set(owner[match.start() : match.end()])):
            continue
        group, noun = match.group("group"), match.group("noun")
        if amenity := match.group("amenity"):
            *between, venue = amenity.split()
            if _NOT_A_NOUN.intersection(between):
                continue  # "a student who likes pubs" asks for pubs
            if group not in _ONLY_A_GROUP and venue in _EATS:
                # "Turkish cafes" asks for cafes. The cuisine says nothing of who lives there.
                mark(match.start("group"), match.end("group"), _Is.GENERIC)
                continue
            mark(match.start(), match.end(), _Is.AMENITY)
        elif group in _ONLY_A_GROUP and noun and noun not in _NOT_A_NOUN:
            mark(match.start(), match.end(), _Is.PEOPLE)
            about_people = True
        elif group not in _ONLY_A_GROUP:
            # "White stucco houses", "an English garden": a colour or a country.
            mark(match.start("group"), match.end("group"), _Is.GENERIC)
    return found, about_people


def _read_as(
    tokens: Sequence[_Token], names: Names | None, fixed: Mapping[int, _Is]
) -> list[_Item]:
    """The tokens of a sentence, each read as the vocabulary, the lexicon or the release has it."""
    count = len(tokens)
    best: list[tuple[float, _Item | None]] = [(0.0, None)] * (count + 1)
    for at in range(count - 1, -1, -1):
        token = tokens[at]
        choices: list[tuple[float, _Item]] = []
        if at in fixed:
            choices.append((0.0, _item(tokens, fixed[at], "", at, 1)))
        elif not token.odd:
            choices += [(_COST_NAME, name) for name in _names_at(tokens, at, names)]
            for text, size in (
                *_phrases_at(tokens, at, _LEXICON_BY, bare=True),
                *_labels_at(tokens, at),
            ):
                choices.append((_COST_PHRASE, _item(tokens, _Is.THING, text, at, size)))
            for text, size in _phrases_at(tokens, at, _UNMET_BY, bare=True):
                unmet = _UNMET_OF[text]
                choices.append(
                    (_COST_PHRASE, _item(tokens, _Is.UNMET, text, at, size, unmet=unmet))
                )
            for text, size in _phrases_at(tokens, at, _VOCABULARY_BY, bare=token.joined):
                cost = _COST_CUE if text in _EXPECTS_A_NAME else _COST_PHRASE
                cost = _COST_WORD if size == 1 and not token.joined else cost
                choices.append((cost, _item(tokens, _Is.WORD, text, at, size)))
            number = _number(token)
            if number is not None:
                number.first, number.last = at, at + 1
                choices.append((_COST_PHRASE, number))
        choices = [
            (cost, item)
            for cost, item in choices
            if not any(i in fixed for i in range(at + 1, item.last))
        ] or []
        if at not in fixed:
            choices.append((_COST_UNKNOWN, _item(tokens, _Is.UNKNOWN, "", at, 1)))
        best[at] = min(
            ((cost + best[item.last][0], item) for cost, item in choices),
            key=lambda found: (found[0], -(found[1].last - found[1].first)),
        )
    items: list[_Item] = []
    at = 0
    while at < count:
        item = best[at][1]
        assert item is not None
        items.append(item)
        at = item.last
    for item in items:
        if item.what is _Is.WORD and item.text in _COUNTED:
            item.what, item.value = _Is.NUMBER, _COUNTED[item.text]
    return items


# --- What a sentence asks for ------------------------------------------------------


class _Join(Enum):
    """How a part of a sentence is joined to the part before it."""

    FIRST = "first"
    MARK = "mark"  # a comma, a semicolon, a colon, a dash or a bracket
    AND = "and"
    OR = "or"
    BUT = "but"


class _Way(Enum):
    """What is said of a thing, where something is: by a word the reader has a rule for."""

    NONE = "none"
    NOT_AT_ALL = "not at all"
    LESS = "less"
    OFF = "off"  # said of the weight: "I don't care about"
    DOWN = "down"  # said of the weight: "I care less about"
    TROUBLED = "troubled"  # "I worry about", read of a nuisance alone
    # Listed after a thing that was turned, where the reader cannot say whether it was too.
    IN_DOUBT = "in doubt"


_WAY_OF: Mapping[_Way, frozenset[str]] = {
    _Way.NOT_AT_ALL: TURNS_FIRMLY,
    _Way.LESS: TURNS_SOFTLY,
    _Way.OFF: TAKES_OFF,
    _Way.DOWN: TURNS_DOWN,
    _Way.TROUBLED: TROUBLES,
}
_WAY_AFTER: Mapping[_Way, frozenset[str]] = {_Way.OFF: TAKES_OFF_AFTER, _Way.DOWN: TURNS_DOWN_AFTER}
_TURNING = frozenset(word for words in (*_WAY_OF.values(), *_WAY_AFTER.values()) for word in words)
# What says that a thing counts, and not that it is wanted. Of a nuisance only these
# are a wish to have less of it: "pollution is a must" is not.
_MATTERS = frozenset(
    {
        "important",
        "most important",
        "top priority",
        "matters",
        "matter",
        "priority",
        "care about",
        "weight",
        "emphasis",
    }
)
_MODES = _CYCLED | _WALKED | _BY_TRANSPORT
_HOMES = _RENTS | _BUYS | frozenset(_RENT_SEGMENTS) | frozenset(_BUY_SEGMENTS) | _BEDROOMS
_Edit = BudgetEdit | CommuteEdit | WeightEdit | TagEdit | AreaEdit
_Span = tuple[int, int]


@dataclass
class _Made:
    """An edit a sentence made, and the words it rests on."""

    group: OpsGroup
    edit: _Edit
    spans: list[_Span]
    # It raises a weight or a tag, adds a journey or an area rule, or asks about one.
    raises: bool
    options: tuple[ClarifyOption, ...] | None = None


@dataclass
class _Home:
    """What a sentence says of the home and what it costs. One budget edit is made of them all."""

    rents: list[_Span] = field(default_factory=list[_Span])
    buys: list[_Span] = field(default_factory=list[_Span])
    monthly: list[_Span] = field(default_factory=list[_Span])
    amounts: list[tuple[int, bool, _Span]] = field(default_factory=list[tuple[int, bool, _Span]])
    bedrooms: list[tuple[int, _Span]] = field(default_factory=list[tuple[int, _Span]])
    segments: list[tuple[str, _Span]] = field(default_factory=list[tuple[str, _Span]])
    steps: list[tuple[bool, bool, _Span]] = field(default_factory=list[tuple[bool, bool, _Span]])

    @property
    def said(self) -> bool:
        return bool(self.rents or self.buys or self.monthly or self.amounts or self.steps) or bool(
            self.bedrooms or self.segments
        )


@dataclass
class _Unit:
    items: list[_Item]
    join: _Join


@dataclass
class _Sentence:
    """One sentence, and everything the reader made of it."""

    line: _Line
    items: list[_Item]
    # Every token of it is known, and every word the reader has a rule for was read.
    known: bool = True
    asked: bool = False
    made: list[_Made] = field(default_factory=list[_Made])
    home: _Home = field(default_factory=_Home)
    # Minutes said apart from any place: "a 40 minute commute".
    loose: int = 0
    unmet: set[UnmetCategory] = field(default_factory=set[UnmetCategory])
    about_people: bool = False
    # A campus is named in it, by word or by name.
    campus: bool = False
    # It names something: a thing, a place, a number, a home, or what Burro cannot answer.
    names: bool = False
    # The speaker says what they want in it: "I want", "we need".
    own: bool = False
    # A neighbour that holds doubt and names nothing has taken back what it raised.
    taken_back: bool = False
    # The places, and the words for renting and buying, that stand under a word that turns.
    turned_away: set[str] = field(default_factory=set[str])

    @property
    def doubt(self) -> bool:
        return not self.known or self.asked

    @property
    def names_a_wish(self) -> bool:
        """Whether it holds something an edit could have been made of."""
        return any(
            item.what in (_Is.THING, _Is.NAME, _Is.NUMBER, _Is.ASKED)
            or _is_word(item, _HOMES | _EXPECTS_A_NAME)
            for item in self.items
        )

    def unread(self) -> None:
        """The reader is in doubt, so it does nothing, and says so."""
        self.unmet.add(UnmetCategory.OTHER)


def _is_a_campus(release: Release | None, place_id: str) -> bool:
    place = release.place(place_id) if place_id and release is not None else None
    return place is not None and place.kind is PlaceKind.UNIVERSITY


def _about_a_campus(target: Target) -> bool:
    return _T.NEAR_UNIVERSITIES in target.tags or _F.UNIVERSITY_PROXIMITY in target.features


def _option(match: Match) -> ClarifyOption:
    return ClarifyOption(id=match.id, name=match.name, kind=match.kind)


def _is_word(item: _Item, among: frozenset[str] | Mapping[str, object]) -> bool:
    return item.what is _Is.WORD and item.text in among


def _is_minutes(items: Sequence[_Item], at: int) -> int:
    """How many items a number of minutes takes at `at`: "30mins" is one, "30 minutes" two."""
    if at >= len(items) or items[at].what is not _Is.NUMBER or items[at].money:
        return 0
    if items[at].unit == "min":
        return 1
    return 2 if at + 1 < len(items) and _is_word(items[at + 1], _MINUTES) else 0


class _Reader:
    """Reads one sentence of known words, part by part."""

    def __init__(self, sentence: _Sentence, names: Names | None, release: Release | None) -> None:
        self.sentence = sentence
        self.names = names
        self.release = release
        self.units = self._units(sentence.items)

    @staticmethod
    def _units(items: list[_Item]) -> list[_Unit]:
        units: list[_Unit] = []
        current: list[_Item] = []
        join = _Join.FIRST
        for item in items:
            joins = _is_word(item, _JOINS)
            if (item.apart or joins) and current:
                units.append(_Unit(current, join))
                current, join = [], _Join.MARK
            if joins:
                said = {"and": _Join.AND, "plus": _Join.AND, "or": _Join.OR, "but": _Join.BUT}
                join = said[item.text]
                item.read = True
            else:
                current.append(item)
        if current:
            units.append(_Unit(current, join))
        return units

    # What stands in a part.

    @staticmethod
    def _target(item: _Item) -> bool:
        """Whether an item is something an edit can be made of."""
        if item.what in (_Is.THING, _Is.NAME, _Is.NUMBER, _Is.ASKED):
            return True
        if item.what in (_Is.PEOPLE, _Is.AMENITY, _Is.UNMET):
            return True  # heard, and no edit is made of it
        return item.what is _Is.WORD and (
            item.text in _HOMES
            or item.text in _EXPECTS_A_NAME
            or item.text in _CHEAPER
            or item.text in _DEARER
        )

    def _way(self, unit: _Unit, at: int) -> tuple[_Way, _Item | None]:
        """What is said of the item at `at` by a word that stands before it in its part.

        A word that turns governs the first thing after it and no more. Two
        of them with nothing between are a double negative, which is read by
        nobody: the sentence is left unread.
        """
        governed = False
        for back in range(at - 1, -1, -1):
            item = unit.items[back]
            if item.what is _Is.WORD and item.text in _TURNING:
                way = next((w for w, words in _WAY_OF.items() if item.text in words), None)
                if way is None:
                    return _Way.NONE, None  # said after a thing before it, not of this one
                return (_Way.IN_DOUBT if governed else way), item
            if self._target(item):
                governed = True
        return _Way.NONE, None

    def _way_after(self, unit: _Unit, at: int) -> tuple[_Way, _Item | None]:
        """What is said of the last thing of a part by words that stand after it."""
        for item in unit.items[at + 1 :]:
            if self._target(item):
                break
            for way, words in _WAY_AFTER.items():
                if _is_word(item, words):
                    return way, item
        return _Way.NONE, None

    def _about(self, unit: _Unit, at: int) -> tuple[list[_Item], list[_Item]]:
        """The words said of the item at `at`: back to the thing before it, on to the next."""
        before: list[_Item] = []
        for item in reversed(unit.items[:at]):
            if item.what in (_Is.THING, _Is.NAME):
                break
            before.insert(0, item)
        after: list[_Item] = []
        for item in unit.items[at + 1 :]:
            if item.what in (_Is.THING, _Is.NAME):
                break
            after.append(item)
        return before, after

    def _bare(self, unit: _Unit) -> bool:
        """Whether a part holds nothing but things and the words that stand in a list beside one."""
        things = [item for item in unit.items if item.what is _Is.THING]
        return bool(things) and all(
            (item.what is _Is.THING and not item.text.startswith(("near ", "close to ")))
            or _is_word(item, _BARE)
            for item in unit.items
        )

    def _owns(self, unit: _Unit) -> bool:
        """Whether a part opens with the speaker's own wish: "I want", "we need", "looking for"."""
        words = [item.text for item in unit.items[:3] if item.what is _Is.WORD]
        return bool(words) and (
            (words[0] in _SPEAKS and any(word in _WISHES for word in words[1:]))
            or words[0] in _WISHES - {"would", "must", "like"}
        )

    # Reading.

    def read(self) -> None:
        sentence = self.sentence
        carried = _Way.NONE
        # Where the edits of the list being read begin, if a list of bare things is being read.
        listed: int | None = None
        for n, unit in enumerate(self.units):
            sentence.own = sentence.own or self._owns(unit)
            turns = any(_is_word(item, _TURNING) for item in unit.items)
            goes_on = unit.join in (_Join.MARK, _Join.AND, _Join.OR) and not self._owns(unit)
            shared = _Way.NONE
            if carried is not _Way.NONE and goes_on and not turns:
                if unit.join is _Join.OR or (self._bare(unit) and self._closes_in_or(n)):
                    shared = carried
                elif self._bare(unit):
                    shared = _Way.IN_DOUBT
            if not goes_on:
                listed = None
            began = len(sentence.made)
            said = self._read_unit(unit, shared)
            if said.after is not _Way.NONE and listed is not None:
                # What is said after the last item of a list is said of every item,
                # and the reader cannot say of each what was said of the last.
                if any(made.raises for made in sentence.made[listed:began]):
                    sentence.unread()
                kept = [made for made in sentence.made[listed:began] if not made.raises]
                sentence.made[listed:began] = kept
            if not self._bare(unit):
                listed = None
            elif listed is None:
                listed = began
            if said.before is not _Way.NONE:
                carried = said.before
            elif shared is _Way.NONE:
                carried = _Way.NONE
        unread = [
            item
            for item in sentence.items
            if not item.read
            and (item.what is _Is.NUMBER or (item.what is _Is.WORD and item.text in _MUST_BE_READ))
        ]
        if unread:
            # A word the reader has a rule for stands where no rule reads it.
            sentence.known = False
            sentence.made, sentence.home, sentence.loose = [], _Home(), 0
            sentence.unread()

    def _closes_in_or(self, n: int) -> bool:
        """Whether the list a part is an item of is closed by "or"."""
        for later in self.units[n + 1 :]:
            if later.join is _Join.OR:
                return not self._owns(later)
            if later.join is not _Join.MARK or not self._bare(later):
                return False
        return False

    def _read_unit(self, unit: _Unit, shared: _Way) -> "_Said":
        said = _Said()
        items = unit.items
        at = 0
        while at < len(items):
            item = items[at]
            if item.read or not self._target(item):
                at += 1
                continue
            way, by = self._way(unit, at)
            if way is _Way.NONE:
                way = shared
            if by is not None:
                by.read = True
            if item.what is _Is.NUMBER:
                at = self._number(unit, at, way)
            elif item.what is _Is.WORD and item.text in _EXPECTS_A_NAME:
                at = self._journey(unit, at, at + 1, way, minutes=0, firm=False, spans=[])
            elif item.what in (_Is.NAME, _Is.ASKED):
                at = self._name(unit, at, way)
            elif item.what in (_Is.PEOPLE, _Is.AMENITY, _Is.UNMET):
                item.read = True
                self._placed(unit, at)
                at += 1
            elif item.what is _Is.WORD:
                self._home_word(item, way)
                at += 1
            else:
                where = self._placed(unit, at)
                after, after_by = self._way_after(unit, at)
                if after is not _Way.NONE and after_by is not None:
                    after_by.read = True
                    said.after = after
                    way = after if way is _Way.NONE else _Way.IN_DOUBT
                    by = after_by
                elif way not in (_Way.NONE, _Way.IN_DOUBT) and said.before is _Way.NONE:
                    said.before = way
                self._wish(unit, at, way, by, where)
                at += 1
        return said

    @staticmethod
    def _placed(unit: _Unit, at: int) -> _Item | None:
        """ "Not far from a park" is "near a park": the words before the thing say where."""
        back = at - 1
        while back >= 0 and _is_word(unit.items[back], _ARTICLES):
            back -= 1
        if back >= 0 and _is_word(unit.items[back], NEAR_TO):
            unit.items[back].read = True
            return unit.items[back]
        return None

    def _blocked(self, item: _Item, way: _Way) -> bool:
        """Whether a word that turns stands over an item that only a plain wish can be read of."""
        if way is _Way.NONE:
            return False
        item.read = True
        self.sentence.unread()
        campus = item.what is _Is.NAME and _is_a_campus(self.release, item.place)
        self.sentence.about_people |= campus
        return True

    # Numbers: minutes to a place, money, bedrooms.

    def _number(self, unit: _Unit, at: int, way: _Way) -> int:
        items = unit.items
        number = items[at]
        caps = [item for item in items[max(at - 2, 0) : at] if _is_word(item, CAPS | CAPS_FIRMLY)]
        # And said after it: "£1,400 a month at most", "30 minutes max".
        then = at + 1
        while then < len(items) and _is_word(items[then], _MINUTES | _MONTHLY | _BEDROOMS):
            then += 1
        if then < len(items) and _is_word(items[then], _SAID_AFTER_A_NUMBER):
            caps.append(items[then])
        firm = any(item.text in CAPS_FIRMLY for item in caps) or any(
            _is_word(item, CAPS_FIRMLY) for item in items
        )
        spans = [(min([c.start for c in caps] + [number.start]), number.end)]
        spans += [(c.start, c.end) for c in caps if c.start > number.end]
        size = _is_minutes(items, at)
        beds = number.unit == "bed" or (at + 1 < len(items) and _is_word(items[at + 1], _BEDROOMS))
        for item in caps:
            item.read = True
        number.read = True
        if size:
            spans = [(spans[0][0], items[at + size - 1].end), *spans[1:]]
            for item in items[at : at + size]:
                item.read = True
            return self._minutes(unit, at + size, way, number.value, firm, spans)
        if beds:
            last = items[at + 1] if number.unit != "bed" else number
            last.read = True
            if way is _Way.NONE:
                self.sentence.home.bedrooms.append((number.value, (number.start, last.end)))
            else:
                self.sentence.unread()
            return at + (1 if number.unit == "bed" else 2)
        monthly = number.unit == "month" or (
            at + 1 < len(items) and _is_word(items[at + 1], _MONTHLY)
        )
        money = [i for i in items[max(at - 2, 0) : at] if _is_word(i, _MONEY_WORDS)]
        # "Rent for 1500": a number beside a word for the home is what it costs.
        homely = any(_is_word(i, _RENTS | _BUYS | _MONEY_WORDS) for i in self.sentence.items)
        counted = at + 1 < len(items) and items[at + 1].what is _Is.THING
        worth = number.value >= _LEAST_MONEY and not counted
        said = number.money or monthly or ((caps or money or homely) and worth)
        if not said:
            number.read = False  # a number of things, which is no limit the reader sets
            for item in caps:
                item.read = False
            return at + 1
        for item in money:
            item.read = True
        if way is _Way.NONE:
            self.sentence.home.amounts.append((number.value, firm, spans[0]))
            if monthly:
                said = number if number.unit == "month" else items[at + 1]
                self.sentence.home.monthly.append((said.start, said.end))
        else:
            self.sentence.unread()
        return at + 1

    def _minutes(
        self, unit: _Unit, at: int, way: _Way, minutes: int, firm: bool, spans: list[_Span]
    ) -> int:
        """What a number of minutes is said of: a journey to a place, or a thing, or nothing."""
        items = unit.items
        then = at
        if then < len(items) and _is_word(items[then], _TRAVELLED | _A_JOURNEY):
            if items[then].text in _A_JOURNEY and way is _Way.NONE:
                self.sentence.loose = minutes
            then += 1
        if then < len(items) and _is_word(items[then], _TO_A_PLACE):
            return self._journey(unit, then, then + 1, way, minutes, firm, spans)
        before = [item for item in items[:at] if _is_word(item, _A_JOURNEY)]
        if before and way is _Way.NONE:
            self.sentence.loose = minutes
        return at

    def _journey(
        self,
        unit: _Unit,
        cue: int,
        at: int,
        way: _Way,
        minutes: int,
        firm: bool,
        spans: list[_Span],
    ) -> int:
        """The journey a cue opens, to the place named after it."""
        items = unit.items
        expects = items[cue].text in _EXPECTS_A_NAME or minutes > 0
        while at < len(items) and _is_word(items[at], frozenset({"the", "a", "an", "my", "our"})):
            at += 1
        named = items[at] if at < len(items) else None
        if named is None or named.what not in (_Is.NAME, _Is.ASKED, _Is.GENERIC):
            # "Near a park" asks for a park, and "30 minutes to a park" for one too.
            items[cue].read = items[cue].read or named is None or named.what is _Is.THING
            return cue + 1
        items[cue].read = named.read = True
        leads = self._speaker_does(unit, cue)
        if named.what is _Is.GENERIC:
            return at + 1  # "I commute to work": no place was named, so there is nothing to ask
        if way is not _Way.NONE or not leads:
            # A place named under a word that turns adds no journey. To be kept
            # from a campus is a request about who lives somewhere.
            self.sentence.unread()
            self.sentence.turned_away.add(named.place)
            self.sentence.about_people |= _is_a_campus(self.release, named.place)
            return at + 1
        words = [item.text for item in items if item.what is _Is.WORD]
        mode = (
            ModeChoice.CYCLE
            if _CYCLED.intersection(words)
            else ModeChoice.WALK
            if _WALKED.intersection(words)
            else ModeChoice.PT
            if _BY_TRANSPORT.intersection(words)
            else ModeChoice.UNCHANGED
        )
        options: tuple[ClarifyOption, ...] | None = None
        if named.what is _Is.ASKED or not named.place:
            if not expects:
                return at + 1  # after "near", what is not a name is not asked about
            options = self._options(named)
        edit = CommuteEdit(
            action=CommuteAction.ADD,
            place_id="" if options is not None else named.place,
            mode=mode,
            max_minutes=minutes,
            strictness=StrictnessChoice.HARD if minutes and firm else StrictnessChoice.UNCHANGED,
            step=Step.NONE,
            provenance=_STATED,
        )
        spans = [(min([s for s, _ in spans] + [items[cue].start]), named.end)]
        spans += [(i.start, i.end) for i in items if _is_word(i, _MODES) and i.start > named.end]
        self.sentence.made.append(_Made(OpsGroup.COMMUTE, edit, spans, True, options))
        return at + 1

    @staticmethod
    def _speaker_does(unit: _Unit, cue: int) -> bool:
        """Whether the one who works, studies or travels is the speaker, or nobody is named.

        "Works at" and "worked at" are no words of the reader's, so what is
        left to rule out is a word of plenty or a thing standing as the
        subject: "some work at", "many commute to".
        """
        if unit.items[cue].text not in _EXPECTS_A_NAME:
            return True
        back = cue - 1
        while back >= 0 and _is_word(unit.items[back], LARGE_STEP | {"also", "definitely"}):
            back -= 1
        return back < 0 or _is_word(unit.items[back], _LEADS_IN | _MODES | {"to work", "near"})

    def _options(self, named: _Item) -> tuple[ClarifyOption, ...]:
        """What to offer for words that were given as a name and are the whole of none."""
        if self.names is None or not named.text:
            return ()
        return tuple(_option(m) for m in self.names.search_places(named.text, MAX_OPTIONS))

    # Names: a journey after "near", an area rule after "only" and "not".

    def _name(self, unit: _Unit, at: int, way: _Way) -> int:
        items = unit.items
        named = items[at]
        named.read = True
        back = at - 1
        while back >= 0 and _is_word(items[back], frozenset({"the", "in"})):
            back -= 1
        cue = items[back] if back >= 0 else None
        if cue is not None and cue.what is _Is.WORD and cue.text in ONLY_IN | NOT_IN:
            cue.read = True
            self._area(unit, back, at)
            return at + 1
        if cue is not None and _is_word(cue, NEAR_TO) and named.what is _Is.NAME:
            cue.read = True
            if named.place:
                return self._journey(unit, back, at, way, minutes=0, firm=False, spans=[])
        # A name no cue stands before makes no edit, and is read as no wish.
        self._blocked(named, way)
        return at + 1

    def _area(self, unit: _Unit, cue: int, at: int) -> None:
        """An area rule the contract defines: "only in X", "not X", "avoid X", "anywhere but X".

        An area rule is a filter, so it is made only where the part says that
        and nothing else, and where nobody but the speaker is its subject:
        "some avoid Tallowgate" makes none. The area must be what was named:
        "avoid Wexmoor University" names a campus.
        """
        items = unit.items
        named = items[at]
        action = AreaAction.ONLY if items[cue].text in ONLY_IN else AreaAction.EXCLUDE
        plainly = all(_is_word(item, _LEADS_IN) for item in items[:cue]) and all(
            _is_word(item, _FOLLOWS) for item in items[at + 1 :]
        )
        between = [item for item in items[cue + 1 : at] if item.text != "the"]
        if action is AreaAction.ONLY and any(item.text == "in" for item in between):
            between = [item for item in between if item.text != "in"]
        if named.what is not _Is.NAME or not named.area or not plainly or between:
            self.sentence.unread()
            self.sentence.about_people |= action is AreaAction.EXCLUDE and _is_a_campus(
                self.release, named.place
            )
            return
        for item in items:
            item.read = True
        edit = AreaEdit(action=action, area_id=named.area, provenance=_STATED)
        self.sentence.made.append(_Made(OpsGroup.AREA, edit, [(items[cue].start, named.end)], True))

    # The home: to rent or to buy, and what kind.

    def _much(self, item: _Item) -> bool:
        """Whether a word of degree stands straight before an item: "much cheaper"."""
        items = self.sentence.items
        at = next(n for n, found in enumerate(items) if found is item)
        return at > 0 and _is_word(items[at - 1], LARGE_STEP) and not item.apart

    def _home_word(self, item: _Item, way: _Way) -> None:
        item.read = True
        if way is not _Way.NONE:
            # "I am not looking to buy" says nothing of what the person is looking for.
            self.sentence.unread()
            self.sentence.turned_away.add(
                "rent" if item.text in _RENTS else "buy" if item.text in _BUYS else ""
            )
            return
        home, span = self.sentence.home, (item.start, item.end)
        if item.text in _CHEAPER or item.text in _DEARER:
            home.steps.append((item.text in _CHEAPER, self._much(item), span))
        elif item.text in _RENTS:
            home.rents.append(span)
        elif item.text in _BUYS:
            home.buys.append(span)
        elif item.text in _RENT_SEGMENTS or item.text in _BUY_SEGMENTS:
            home.segments.append((item.text, span))

    # Wishes: a thing of the lexicon, and what is said of it.

    def _wish(self, unit: _Unit, at: int, way: _Way, by: _Item | None, where: _Item | None) -> None:
        """The edits for a thing that was named, from the words said of it (section 5.2)."""
        sentence = self.sentence
        item = unit.items[at]
        item.read = True
        target = LEXICON[item.text]
        before, after = self._about(unit, at)
        large = [i for i in (*before, *after) if _is_word(i, LARGE_STEP)]
        small = [i for i in before if _is_word(i, SMALL_STEP)]
        essential = [i for i in (*before, *after) if _is_word(i, ESSENTIAL)]
        matters = [i for i in (*before, *after) if _is_word(i, _MATTERS)]
        sentence.campus = sentence.campus or _about_a_campus(target)
        turned = way in (_Way.NOT_AT_ALL, _Way.LESS)
        weighed = way in (_Way.OFF, _Way.DOWN)
        if way is _Way.IN_DOUBT or (way is _Way.TROUBLED and not target.nuisance):
            sentence.about_people |= _about_a_campus(target)
            sentence.unread()
            return
        if turned and _about_a_campus(target):
            # To be far from a campus is a way to ask for fewer students
            # (section 8.4). It gets the notice and no edit.
            sentence.about_people = True
            return
        if turned and (target.direction is not DirectionChoice.DEFAULT or target.wanted_low):
            # A phrase that says which way it is wanted, "not built up", cannot be
            # turned round by a word before it without the reader guessing.
            sentence.unread()
            return
        cared_for = turned or way is _Way.TROUBLED or bool(matters) or target.wanted_low
        if target.nuisance and not weighed and not cared_for:
            # A nuisance that is only named, or that the person says they like, is a
            # wish no edit can express: its one direction is less.
            sentence.unread()
            return
        used = [item, *large, *small, *essential]
        used += [said for said in (by, where) if said is not None]
        span = (min(i.start for i in used), max(i.end for i in used))
        up = Step.UP_SMALL if (small and not large) or way is _Way.LESS else Step.UP_LARGE
        down = Step.DOWN_LARGE if large else Step.DOWN_SMALL
        for feature_id in target.features:
            action, value, step, direction = WeightAction.NUDGE, 0.0, up, target.direction
            raises = True
            if way is _Way.OFF:
                action, step, raises = WeightAction.REMOVE, Step.NONE, False
            elif way is _Way.DOWN:
                step, raises = down, False
            elif turned and not target.nuisance:
                raises = False
                if FEATURES[feature_id].polarity is Polarity.EITHER:
                    step, direction = Step.UP_LARGE, DirectionChoice.LESS
                else:
                    # It never raises a weight. Wanted less, the weight is turned down.
                    # Not wanted at all, it is taken off, so that a default stops
                    # counting for a thing the person has said they do not want.
                    step = Step.DOWN_SMALL if way is _Way.LESS else Step.NONE
                    action = WeightAction.NUDGE if way is _Way.LESS else WeightAction.REMOVE
                    sentence.unread()
            elif essential:
                action, value, step = WeightAction.SET, 1.0, Step.NONE
            edit = WeightEdit(
                action=action,
                feature_id=feature_id,
                value=value,
                step=step,
                direction=direction,
                provenance=target.provenance,
            )
            sentence.made.append(_Made(OpsGroup.WEIGHT, edit, [span], raises))
        for tag_id in target.tags:
            action, value, step, raises = WeightAction.NUDGE, 0.0, up, True
            if way is _Way.OFF:
                action, step, raises = WeightAction.REMOVE, Step.NONE, False
            elif way is _Way.DOWN:
                step, raises = down, False
            elif turned:
                # A tag has no direction, so "not too buzzy" can only turn it down.
                step = Step.DOWN_SMALL if way is _Way.LESS else Step.NONE
                action = WeightAction.NUDGE if way is _Way.LESS else WeightAction.REMOVE
                raises = False
                sentence.unread()
            elif essential:
                action, value, step = WeightAction.SET, 1.0, Step.NONE
            tag = TagEdit(
                action=action, tag_id=tag_id, value=value, step=step, provenance=target.provenance
            )
            sentence.made.append(_Made(OpsGroup.TAG, tag, [span], raises))


@dataclass
class _Said:
    """What a part of a sentence said of its things by a word the reader has a rule for."""

    before: _Way = _Way.NONE
    after: _Way = _Way.NONE


_ARTICLES = frozenset({"the", "a", "an", "my", "our"})


def _after_cues(items: list[_Item], tokens: Sequence[_Token], names: Names | None) -> list[_Item]:
    """What follows words that expect a place, where it is not the name of one.

    "I commute to work" names no place, and the word is read as no wish for a
    school or a campus either. After words that expect a name, "work at",
    "30 minutes to", what the release does not hold is what the person calls
    the place: it is asked about, and adds no journey. It is the one place
    where words the reader does not know are not doubt, because a question
    adds nothing to a search.
    """
    found: list[_Item] = []
    at = 0
    while at < len(items):
        item = items[at]
        found.append(item)
        at += 1
        expects = _is_word(item, _EXPECTS_A_NAME) or (
            _is_word(item, _TO_A_PLACE) and _minutes_before(found)
        )
        if not expects and not _is_word(item, NEAR_TO):
            continue
        while at < len(items) and _is_word(items[at], _ARTICLES) and not items[at].apart:
            found.append(items[at])
            at += 1
        if at >= len(items) or items[at].apart:
            continue
        following = items[at]
        spelt = " ".join(token.bare for token in tokens[following.first : following.last])
        odd = any(token.odd for token in tokens[following.first : following.last])
        generic = following.what in (_Is.UNKNOWN, _Is.WORD) or (
            following.what is _Is.THING and expects
        )
        if spelt in GENERIC_PLACES and generic and not odd:
            following.what, following.text = _Is.GENERIC, spelt
            continue
        if not expects or odd or following.what not in (_Is.UNKNOWN, _Is.NAME):
            continue
        run = [following]
        while (
            at + len(run) < len(items)
            and len(run) < MAX_NAME_WORDS
            and not items[at + len(run)].apart
            and items[at + len(run)].what in (_Is.UNKNOWN, _Is.NAME)
            and not any(
                t.odd for t in tokens[items[at + len(run)].first : items[at + len(run)].last]
            )
        ):
            run.append(items[at + len(run)])
        if len(run) == 1 and following.what is _Is.NAME and following.place:
            continue
        if len(run) > 1 and any(item.what is _Is.NAME for item in run):
            # A name, and beside it a word the reader does not know: that is not
            # what the person calls a place, it is something said of one.
            continue
        beyond = items[at + len(run)] if at + len(run) < len(items) else None
        if beyond is not None and not beyond.apart and not _is_word(beyond, _JOINS):
            # More is said after it, so it is not the name of a place that was
            # given: "20 minutes from the nearest bar".
            continue
        words = " ".join(token.bare for token in tokens[run[0].first : run[-1].last])
        asked = _Item(
            _Is.ASKED, words, run[0].first, run[-1].last, run[0].start, run[-1].end, False
        )
        found.append(asked)
        at += len(run)
    return found


def _minutes_before(items: Sequence[_Item]) -> bool:
    """Whether the words that end at "to", "from" or "of" are a number of minutes before it."""
    back = len(items) - 2
    if back >= 0 and _is_word(items[back], _TRAVELLED):
        back -= 1
    if back >= 0 and _is_word(items[back], _MINUTES):
        back -= 1
        return back >= 0 and items[back].what is _Is.NUMBER
    return back >= 0 and items[back].what is _Is.NUMBER and items[back].unit == "min"


def _also(items: list[_Item], tokens: Sequence[_Token]) -> None:
    """ "A park too" is "a park as well". It is read there and nowhere else."""
    for at, item in enumerate(items):
        ends = at + 1 == len(items) or items[at + 1].apart
        follows = at > 0 and items[at - 1].what in (_Is.THING, _Is.NAME) and not item.apart
        also = item.what is _Is.UNKNOWN and tokens[item.first].word == ALSO_AT_THE_END
        if also and ends and follows and not tokens[item.first].odd:
            item.what, item.text = _Is.WORD, ALSO_AT_THE_END


# "Like" also compares, and "love" is also a thing one has: "I need pubs like I need
# noise", "my love of pubs is low". Each is known where the speaker does it.
_ALSO_COMPARES = frozenset({"like", "love"})
_BEFORE_A_WISH = _SPEAKS | LARGE_STEP | frozenset({"would", "also", "definitely", "absolutely"})


def _wished(items: list[_Item]) -> None:
    """ "Like" and "love" are read as to wish only straight after the speaker."""
    for at, item in enumerate(items):
        if not _is_word(item, _ALSO_COMPARES):
            continue
        back = at - 1
        while back >= 0 and _is_word(items[back], _BEFORE_A_WISH - _SPEAKS) and not item.apart:
            back -= 1
        spoken = back >= 0 and _is_word(items[back], _SPEAKS)
        opens = at == 0 or items[at].apart or _is_word(items[at - 1], _JOINS)
        if not spoken and not (opens and item.text == "love"):
            item.what, item.text = _Is.UNKNOWN, ""


_NAMES_SOMETHING = (_Is.THING, _Is.NAME, _Is.PEOPLE, _Is.AMENITY, _Is.UNMET, _Is.ASKED)


def _read_line(line: _Line, names: Names | None, release: Release | None) -> _Sentence:
    """One sentence, read if every token of it is known, and heard either way."""
    fixed, about_people = _people_in(line.tokens)
    items = _after_cues(_read_as(line.tokens, names, fixed), line.tokens, names)
    _also(items, line.tokens)
    _wished(items)
    sentence = _Sentence(line, items, about_people=about_people)
    turned_about = any(
        _is_word(verb, _ASKS_OF) and _is_word(who, _SPEAKS) and not who.apart
        for verb, who in pairwise(items)
    )
    sentence.asked = line.asked or turned_about or (bool(items) and _is_word(items[0], _ASKS))
    # What Burro cannot answer is heard in every sentence, read or not.
    sentence.unmet = {item.unmet for item in items if item.unmet is not None}
    if any(item.what is _Is.AMENITY for item in items):
        sentence.unmet.add(UnmetCategory.COMMUNITY_AMENITIES)
    sentence.campus = any(
        (item.what is _Is.NAME and _is_a_campus(release, item.place))
        or (item.what is _Is.THING and _about_a_campus(LEXICON[item.text]))
        for item in items
    )
    sentence.names = any(
        item.what in _NAMES_SOMETHING
        or (item.what is _Is.NUMBER and (item.money or bool(item.unit) or len(items) > 1))
        or _is_word(item, _HOMES | _EXPECTS_A_NAME | _MONEY_WORDS | _CHEAPER | _DEARER)
        for item in items
    )
    if len(items) == 1 and items[0].what is _Is.NUMBER and not sentence.names:
        return sentence  # the number of an item in a list: "1."
    sentence.known = all(item.what is not _Is.UNKNOWN for item in items)
    if sentence.known and not sentence.asked:
        _Reader(sentence, names, release).read()
    elif not (sentence.unmet or sentence.about_people) or sentence.names_a_wish:
        sentence.unread()
    if sentence.doubt and sentence.campus:
        # A campus, by word or by name, in a sentence the reader does not read.
        sentence.about_people = True
    return sentence


# --- The whole text ---------------------------------------------------------------


def _closes(sentence: _Sentence) -> bool:
    """Whether a sentence holds doubt and names nothing: "No thanks.", "I disagree."."""
    return sentence.doubt and not sentence.names


def _take_back(sentences: Sequence[_Sentence]) -> None:
    """A sentence that holds doubt and names nothing takes back what stands beside it.

    It is said of the sentence before it, whatever that is: "I want a
    station. Not really." And it is said of what is listed beside it, before
    and after, as far as the list goes: "Pubs. Bars. None of it." and
    "Dealbreakers:" on a line of its own, with a pub on each line below. A
    list ends at a sentence in which the speaker says what they want, "I
    want a park", which stands by itself.
    """

    def take(sentence: _Sentence) -> None:
        raised = [made for made in sentence.made if made.raises]
        if raised or sentence.home.said or sentence.loose:
            sentence.unread()
        sentence.made = [made for made in sentence.made if not made.raises]
        sentence.home, sentence.loose, sentence.taken_back = _Home(), 0, True
        sentence.about_people = sentence.about_people or sentence.campus

    for at, sentence in enumerate(sentences):
        if not _closes(sentence):
            continue
        back = at - 1
        if back >= 0 and not _closes(sentences[back]):
            take(sentences[back])
            while (
                back > 0
                and not sentences[back].own
                and not sentences[back - 1].own
                and not _closes(sentences[back - 1])
            ):
                back -= 1
                take(sentences[back])
        on = at + 1
        while on < len(sentences) and not sentences[on].own and not _closes(sentences[on]):
            take(sentences[on])
            on += 1


def _budget(
    sentences: Sequence[_Sentence], spec: PreferenceSpec
) -> tuple[BudgetEdit, list[_Span]] | None:
    """The one budget edit a text makes, from every sentence that was read."""
    home = _Home()
    for sentence in sentences:
        for name in ("rents", "buys", "monthly", "amounts", "bedrooms", "segments", "steps"):
            getattr(home, name).extend(getattr(sentence.home, name))
    amount, hard, where = home.amounts[0] if home.amounts else (0, False, (0, 0))
    spans: list[_Span] = [where] if home.amounts else []
    tenure = TenureChoice.UNCHANGED
    turned_away = {about for sentence in sentences for about in sentence.turned_away}
    said = "rent" if home.rents else "buy"
    if bool(home.rents) != bool(home.buys) and said in turned_away:
        pass  # "to buy or not to buy": asked for and turned away, so neither is taken
    elif bool(home.rents) != bool(home.buys):
        tenure = TenureChoice.RENT if home.rents else TenureChoice.BUY
        spans += home.rents or home.buys
    elif home.rents:
        pass  # both were said, so neither is taken
    elif home.monthly:
        tenure = TenureChoice.RENT
        spans += home.monthly
    # A number alone says which it is: no rent is this high and no price this low.
    elif amount >= LIMITS.buy.minimum and spec.tenure is Tenure.RENT:
        tenure = TenureChoice.BUY
    elif 0 < amount <= LIMITS.rent.maximum and spec.tenure is Tenure.BUY:
        tenure = TenureChoice.RENT
    chosen = spec.tenure if tenure is TenureChoice.UNCHANGED else Tenure(tenure.value)
    segment = SegmentChoice.UNCHANGED
    # A price is published by the type of home and not by its bedrooms.
    beds = [(count, span) for count, span in home.bedrooms if count >= 1]
    if beds and chosen is Tenure.RENT:
        segment = _BEDS[min(beds[0][0], len(_BEDS)) - 1]
        spans.append(beds[0][1])
    kinds = _RENT_SEGMENTS if chosen is Tenure.RENT else _BUY_SEGMENTS
    for word, span in home.segments:
        if word in kinds and segment is SegmentChoice.UNCHANGED:
            segment = kinds[word]
            spans.append(span)
    if amount or tenure is not TenureChoice.UNCHANGED or segment is not SegmentChoice.UNCHANGED:
        edit = BudgetEdit(
            action=BudgetAction.SET,
            tenure=tenure,
            amount=amount,
            segment=segment,
            strictness=StrictnessChoice.HARD if hard else StrictnessChoice.UNCHANGED,
            step=Step.NONE,
            provenance=_STATED,
        )
        return edit, sorted(set(spans))
    for cheaper, much, span in home.steps[:1]:
        small, large = (
            (Step.DOWN_SMALL, Step.DOWN_LARGE) if cheaper else (Step.UP_SMALL, Step.UP_LARGE)
        )
        edit = BudgetEdit(
            action=BudgetAction.NUDGE,
            tenure=TenureChoice.UNCHANGED,
            amount=0,
            segment=SegmentChoice.UNCHANGED,
            strictness=StrictnessChoice.UNCHANGED,
            step=large if much else small,
            provenance=_STATED,
        )
        return edit, [span]
    return None


def assumptions_for(operations: Operations, spec: PreferenceSpec) -> tuple[Assumption, ...]:
    """What each edit left to a default, so the person can see it and change it.

    Worked out from the edits and the spec they were made for, so every
    interpreter states the same assumptions for the same edits.
    """
    found: list[Assumption] = []

    def assume(code: AssumptionCode, group: OpsGroup, index: int) -> None:
        found.append(Assumption(code=code, group=group, index=index))

    nobody_chose = spec.budget.provenance is Provenance.DEFAULT
    for index, edit in enumerate(operations.budget_ops):
        if edit.action is not BudgetAction.SET or edit.amount == 0:
            continue
        if edit.tenure is TenureChoice.UNCHANGED and spec.tenure_from is Provenance.DEFAULT:
            assume(AssumptionCode.TENURE, OpsGroup.BUDGET, index)
        moved = edit.tenure is not TenureChoice.UNCHANGED and edit.tenure.value != spec.tenure
        if edit.segment is SegmentChoice.UNCHANGED and (nobody_chose or moved):
            assume(AssumptionCode.SEGMENT, OpsGroup.BUDGET, index)
        if edit.strictness is StrictnessChoice.UNCHANGED and nobody_chose:
            assume(AssumptionCode.STRICTNESS, OpsGroup.BUDGET, index)

    known = {commute.place_id for commute in spec.commutes}
    for index, commute in enumerate(operations.commute_ops):
        if commute.action is not CommuteAction.ADD or commute.place_id in known:
            continue
        if commute.mode is ModeChoice.UNCHANGED:
            assume(AssumptionCode.MODE, OpsGroup.COMMUTE, index)
        if commute.max_minutes == 0:
            assume(AssumptionCode.MAX_MINUTES, OpsGroup.COMMUTE, index)
        if commute.strictness is StrictnessChoice.UNCHANGED:
            assume(AssumptionCode.STRICTNESS, OpsGroup.COMMUTE, index)

    # A weight that was taken off is in the spec as an entry of nothing.
    weighted = {weight.feature_id for weight in spec.active_weights}
    for index, weight in enumerate(operations.weight_ops):
        if weight.action is WeightAction.REMOVE:
            continue
        if weight.provenance is EditProvenance.INFERRED:
            assume(AssumptionCode.WEIGHT, OpsGroup.WEIGHT, index)
        either = FEATURES[weight.feature_id].polarity is Polarity.EITHER
        unsaid = weight.direction is DirectionChoice.DEFAULT
        if either and unsaid and weight.feature_id not in weighted:
            assume(AssumptionCode.DIRECTION, OpsGroup.WEIGHT, index)
    for index, tag in enumerate(operations.tag_ops):
        if tag.action is not WeightAction.REMOVE and tag.provenance is EditProvenance.INFERRED:
            assume(AssumptionCode.WEIGHT, OpsGroup.TAG, index)
    return tuple(found)


class RuleInterpreter:
    """Reads a request with rules alone. It cannot fail, and it never answers `off_topic`.

    It cannot tell an off-topic sentence from one it failed to read, so for
    either it answers `ok` with no edits and `other` among what was unmet. It
    reads a sentence only when it knows every token in it, and answers the
    same way for one it does not.
    """

    name = InterpreterName.RULE

    def __init__(self) -> None:
        # The names of the release last read, so that they are normalised once
        # and not for every request. A release never changes.
        self._names: tuple[Release, Names] | None = None

    def _names_of(self, release: Release) -> Names:
        if self._names is None or self._names[0] is not release:
            self._names = (release, Names(release))
        return self._names[1]

    def interpret(self, request: InterpretRequest) -> InterpretResult:
        names = self._names_of(request.release)
        sentences = _read(request.text, names, request.release)
        made = [found for sentence in sentences for found in sentence.made]
        # What was named outright is read before what was only implied, so that
        # "safe, with low crime" is the explicit request its second half makes it.
        made.sort(key=lambda m: getattr(m.edit, "provenance", _STATED) is _INFERRED)
        groups: dict[OpsGroup, list[_Made]] = {group: [] for group in OpsGroup}
        budget = _budget(sentences, request.spec)
        if budget is not None:
            groups[OpsGroup.BUDGET].append(_Made(OpsGroup.BUDGET, budget[0], budget[1], True))
        loose = next((sentence.loose for sentence in sentences if sentence.loose), 0)
        seen: set[tuple[OpsGroup, str]] = set()
        both_ways = _said_both_ways(made)
        turned_away = {about for sentence in sentences for about in sentence.turned_away}
        for found in made:
            if _about(found) in both_ways:
                continue
            if isinstance(found.edit, CommuteEdit) and found.edit.place_id in turned_away - {""}:
                continue  # "I commute to X and I want to not commute to X"
            edit = found.edit
            _, about = _about(found)
            if about and (found.group, about) in seen:
                continue
            seen.add((found.group, about))
            if isinstance(edit, CommuteEdit) and not edit.max_minutes and loose:
                # "A 40 minute commute", said apart from any place, is the cap
                # for each commute that was given none.
                found.edit = edit.replace(max_minutes=loose)
            groups[found.group].append(found)
        edits = [found.edit for listed in groups.values() for found in listed]
        operations = Operations(
            budget_ops=tuple(edit for edit in edits if isinstance(edit, BudgetEdit)),
            commute_ops=tuple(edit for edit in edits if isinstance(edit, CommuteEdit)),
            weight_ops=tuple(edit for edit in edits if isinstance(edit, WeightEdit)),
            tag_ops=tuple(edit for edit in edits if isinstance(edit, TagEdit)),
            area_ops=tuple(edit for edit in edits if isinstance(edit, AreaEdit)),
            setting_ops=(),
        )
        clarify = tuple(
            Clarify(group=group, index=index, options=found.options)
            for group, listed in groups.items()
            for index, found in enumerate(listed)
            if found.options is not None
        )
        rests_on = tuple(
            RestsOn(group=group, index=index, start=start, end=end)
            for group, listed in groups.items()
            for index, found in enumerate(listed)
            for start, end in sorted(found.spans)
        )
        unmet = {category for sentence in sentences for category in sentence.unmet}
        if both_ways:
            unmet.add(UnmetCategory.OTHER)
        about_people = any(sentence.about_people for sentence in sentences)
        if operations.count == 0 and not unmet and not about_people:
            unmet.add(UnmetCategory.OTHER)
        if about_people:
            status = InterpretStatus.POLICY_REDIRECT
        elif clarify:
            status = InterpretStatus.CLARIFY
        else:
            status = InterpretStatus.OK
        return InterpretResult(
            status=status,
            operations=operations,
            assumptions=assumptions_for(operations, request.spec),
            # In the order the categories are listed, whatever order they were heard in.
            unmet=tuple(category for category in UnmetCategory if category in unmet),
            clarify=clarify,
            notice=Notice.NEUTRAL_PLACES if about_people else Notice.NONE,
            interpreter=self.name,
            degraded=False,
            usage=NO_USAGE,
            rests_on=rests_on,
        )


def _about(made: _Made) -> tuple[OpsGroup, str]:
    """What an edit is about: a place, an area, a feature or a tag, by its id."""
    edit = made.edit
    if isinstance(edit, CommuteEdit):
        return made.group, edit.place_id
    if isinstance(edit, AreaEdit):
        return made.group, edit.area_id
    if isinstance(edit, WeightEdit):
        return made.group, edit.feature_id.value
    if isinstance(edit, TagEdit):
        return made.group, edit.tag_id.value
    return made.group, ""


def _said_both_ways(made: Sequence[_Made]) -> set[tuple[OpsGroup, str]]:
    """What a request both asks for and turns away: "pubs or no pubs".

    The reader cannot say which is meant, so it makes no edit for it.
    """
    ways: dict[tuple[OpsGroup, str], set[bool]] = {}
    for found in made:
        if isinstance(found.edit, WeightEdit | TagEdit):
            ways.setdefault(_about(found), set()).add(found.raises)
    return {about for about, found in ways.items() if len(found) > 1}


def _read(text: str, names: Names | None, release: Release | None) -> list[_Sentence]:
    sentences = [_read_line(line, names, release) for line in _lines(text)]
    _take_back(sentences)
    return sentences


# --- For a caller that holds edits the reader did not make ----------------------------


class SentenceRead(NamedTuple):
    """A sentence of a request as the reader sees it. It holds no word of it, only where it is."""

    start: int
    end: int
    # The reader knows every token of it and read every word it has a rule for. An
    # edit the reader made rests on words of such a sentence and of no other.
    known: bool
    # It holds a word the reader has a rule for that turns, takes off, caps or
    # confines: "no", "less", "don't care about", "within", "only".
    turning: bool
    # It holds a word of the written list of doubt, or a token with a mark inside it.
    doubt: bool
    # It asks and does not tell.
    asked: bool
    # A sentence beside it, which holds doubt and names nothing, took back what it raised.
    taken_back: bool


_PHRASE_OF_DOUBT = re.compile(
    r"\b(?:" + "|".join(re.escape(phrase) for phrase in sorted(PHRASES_OF_DOUBT)) + r")\b"
)


def _doubts_in(sentence: _Sentence) -> list[tuple[int, str]]:
    """Where a sentence holds a word of the written list of doubt, or a token with a mark in it."""
    tokens = sentence.line.tokens
    found = [
        (token.start, token.bare)
        for token in tokens
        if token.odd or token.word in WORDS_OF_DOUBT or token.bare in WORDS_OF_DOUBT
    ]
    line = " ".join(re.sub(r"[^a-z0-9]+", " ", token.bare).strip() or "?" for token in tokens)
    found += [(tokens[0].start, match.group()) for match in _PHRASE_OF_DOUBT.finditer(line)]
    return found


def _holds_doubt(sentence: _Sentence) -> bool:
    return bool(_doubts_in(sentence))


def sentences_of(
    text: str, names: Names | None = None, release: Release | None = None
) -> tuple[SentenceRead, ...]:
    """The sentences of a request, and which of them the reader read.

    It is the reader's own reading, for a caller that must hold edits the
    reader did not make to the same test (the model-backed interpreter). The
    offsets count the characters of the text as it was typed.
    """
    return tuple(
        SentenceRead(
            start=sentence.line.start,
            end=sentence.line.end,
            known=sentence.known and not sentence.asked and not sentence.taken_back,
            turning=any(_is_word(item, _MUST_BE_READ) for item in sentence.items),
            doubt=_holds_doubt(sentence),
            asked=sentence.asked,
            taken_back=sentence.taken_back,
        )
        for sentence in _read(text, names, release)
    )


class ClauseRead(NamedTuple):
    """A part of a request as the rules see it. It holds what a person typed: never log it."""

    words: str
    # The sentence it stands in holds a word that turns, a word of the written list of
    # doubt or a token with a mark inside it, or asks, or was taken back.
    doubtful: bool


_TURNS_A_WISH = _TURNS | TROUBLES | frozenset({"anywhere but"})


def clauses_of(text: str, names: Names | None = None) -> tuple[ClauseRead, ...]:
    """The parts of a request between its marks and joining words, and which are in doubt.

    It is kept for the model-backed interpreter as it stands today, which
    asks of each part what it names and whether any holds doubt. It is worked
    out from the reader's one reading, `sentences_of`, and is no second test.
    """
    found: list[ClauseRead] = []
    for sentence in _read(text, names, None):
        doubtful = (
            _holds_doubt(sentence)
            or sentence.asked
            or sentence.taken_back
            or any(_is_word(item, _TURNS_A_WISH) for item in sentence.items)
        )
        tokens = sentence.line.tokens
        for unit in _Reader(sentence, names, None).units:
            words = " ".join(
                token.bare for item in unit.items for token in tokens[item.first : item.last]
            )
            found.append(ClauseRead(re.sub(r"[^a-z0-9 ]+", " ", words).strip(), doubtful))
    return tuple(found)


def signs_of_doubt(text: str) -> tuple[str, ...]:
    """Each word of a request that puts a sentence in doubt, in the order it stands.

    It returns words a person typed: never log them.
    """
    found: list[tuple[int, str]] = []
    for sentence in _read(text, None, None):
        found += _doubts_in(sentence)
        found += [(i.start, i.text) for i in sentence.items if _is_word(i, _TURNS_A_WISH)]
    return tuple(word for _, word in sorted(set(found)))


# Every word that puts a sentence in doubt for a caller that holds a model's edits
# to the rules: the written list, and the words the reader has a turning rule for.
SIGNS_OF_DOUBT: frozenset[str] = WORDS_OF_DOUBT | PHRASES_OF_DOUBT | _TURNS_A_WISH
