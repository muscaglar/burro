"""Interpreters: from what a person typed to typed edits.

`RuleInterpreter` needs no model and no network, so the product still works as
a form when a model is slow, capped or absent. It reads the text, produces
edits, and keeps none of the words: assumptions and unmet requests are codes,
notices are fixed text, and every label comes from the catalogue or the
release.

It asks when it is not sure. It applies a prompt by itself only when the whole
of it is plain: a list of things wanted or not wanted, with an optional
opening, a budget and a journey to a place named in full (`grammar.py`). For
any other prompt it applies nothing. It offers what it noticed as
suggestions, each with the directions a person may choose, and says which
stretches of the text it made nothing of. The person chooses. The reader
never guesses a direction, so it never reads a wish backwards (ADR 0012).

Every edit and every suggestion says which words of the text it rests on, by
where they start and end. Nothing here keeps the words.

Burro ranks places first. Of who lives somewhere it counts their age and their
households, at Census 2021, and a phrase for either is offered, towards more
of what is counted, and never applied. Any other request about who lives
somewhere, and any wish for fewer of anyone, gets one neutral sentence and no
edit: no id exists that could express the first, and nothing reads the second.
"""

import dataclasses
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from itertools import pairwise
from typing import NamedTuple, Protocol

from burro_core._record import Record
from burro_core.catalogue import (
    COUNTS_RESIDENTS,
    CRIME_CAVEAT,
    FEATURES,
    HOLDS_CRIME,
    HOLDS_RESIDENTS,
    SOLD_FOR,
    TAGS,
    only_by_choice,
)
from burro_core.facts import SEGMENT_LABELS, money
from burro_core.grammar import (
    A_HOME,
    A_HOUSE,
    A_JOURNEY,
    ASKS_NOTHING,
    AT_WORK,
    BEDROOMS,
    BUY_SEGMENTS,
    BUYS,
    CYCLED,
    EXPECTS_A_NAME,
    GOES,
    GOES_TO,
    IN_MONEY,
    KNOWN_WORDS,
    MODES,
    MONTHLY,
    MUST_BE_READ,
    ON_TRANSPORT,
    PAYS,
    REACHES,
    RENT_SEGMENTS,
    RENTS,
    STAYS,
    THOUSANDS,
    TO_A_PLACE,
    TURNS,
    VISITS,
    VOCABULARY,
    WALKED,
    Grammar,
    Home,
    Kind,
    NotPlain,
    Way,
    Wish,
    about_a_campus,
    part_of_a_longer_time,
    says_a_walk,
    stay_alone,
    visit_at,
)
from burro_core.ids import (
    AreaAction,
    AssumptionCode,
    BudgetAction,
    CommuteAction,
    Dimension,
    DirectionChoice,
    EditProvenance,
    FeatureId,
    FeatureKind,
    InterpreterName,
    InterpretStatus,
    ModeChoice,
    Notice,
    OpsGroup,
    OptionKind,
    PlaceKind,
    Polarity,
    Provenance,
    RejectReason,
    Segment,
    SegmentChoice,
    Step,
    StrictnessChoice,
    SuggestionDirection,
    TagId,
    TagShape,
    Tenure,
    TenureChoice,
    Toward,
    TowardChoice,
    UnmetCategory,
    WeightAction,
)
from burro_core.lexicon import (
    COUNTED_AT_THE_CENSUS,
    GENERIC_PLACES,
    LEXICON,
    NO_IDENTITY,
    POLICY_LEXICON,
    Target,
    counts_residents,
    names_it,
    no_identity,
    prepare,
)
from burro_core.ops import (
    NO_OPERATIONS,
    AreaEdit,
    BudgetEdit,
    CommuteEdit,
    Operations,
    TagEdit,
    WeightEdit,
)
from burro_core.places import Match, Names
from burro_core.reading import (
    DASHES,
    HOUR_OR_ITS_LETTER,
    MINUTES,
    Is,
    Item,
    Line,
    Token,
    by_first_word,
    lines_of,
)
from burro_core.reducer import Rejected, apply, given_way_spec, says_a_visit_again
from burro_core.release import Release
from burro_core.spec import DEFAULT_HOUSE, LIMITS, PreferenceSpec
from burro_core.vocabulary import (
    ARTICLE,
    AT_LEAST,
    AT_THE_END,
    BY_ANOTHER_PERIOD,
    BY_THE_WEEK,
    CAPS,
    CAPS_FIRMLY,
    COURTESY,
    ESSENTIAL,
    FIRM_OF_MINUTES,
    FIRM_OF_MONEY,
    GOOD,
    JOINS,
    LARGE_STEP,
    LEAVES_A_TIME_AS_IT_IS,
    LEFT_BEHIND,
    LIVES_THERE,
    NEAR_TO,
    NEARBY,
    NOT_FAR,
    NOT_IN,
    OF_A_PERIOD,
    OF_THE_HOUSEHOLD,
    ONLY_IN,
    PHRASES_OF_DOUBT,
    SMALL_STEP,
    SOMEBODY_ELSE,
    SPEAKER,
    STAYS_AWAY,
    TAKES_OFF,
    TAKES_OFF_AFTER,
    THE_MOST_AFTER,
    TO_DO,
    TROUBLES,
    TURNS_DOWN,
    TURNS_DOWN_AFTER,
    TURNS_ROUND,
    WISH,
    WISH_ALONE,
    WISHES_OF_ANOTHER,
    WORDS_OF_DOUBT,
    WORDS_THAT_TURN_AWAY,
)

__all__ = [
    "GENERIC_PLACES",
    "LEXICON",
    "MAX_TEXT",
    "NOTICES",
    "POLICY_LEXICON",
    "SIGNS_OF_DOUBT",
    "VOCABULARY",
    "Assumption",
    "Choice",
    "Clarify",
    "ClarifyOption",
    "InterpretRequest",
    "InterpretResult",
    "Interpreter",
    "NotInRelease",
    "RestsOn",
    "RuleInterpreter",
    "SentenceRead",
    "Span",
    "Suggestion",
    "Usage",
    "asks_for_nothing",
    "assumptions_for",
    "known_in",
    "may_ask_for_fewer",
    "names_a_visit",
    "not_in_release_of",
    "notice_text",
    "paid_by",
    "prepare",
    "sentences_of",
]

MAX_TEXT = 600

# What is said of every request about who lives somewhere that nothing is offered for: a
# wish to find a group that Burro does not count, and a wish for fewer of anyone.
# It says the three things it said, and no more: what Burro ranks by, the two things it
# counts of who lives in a place and at which census, and that nobody may ask for fewer of
# anyone. It gives no reason for what follows it, which is said by itself.
_PLACES_NOT_PEOPLE = (
    "Burro ranks places by what is there. The only things it counts about the people who "
    "live in a place are their age and the kind of household they live in, as the census "
    "of 2021 recorded them, and you cannot ask for fewer of any group of people."
)
NOTICES: Mapping[Notice, str] = {
    Notice.NONE: "",
    # The same for every group and every user.
    Notice.NEUTRAL_PLACES: f"{_PLACES_NOT_PEOPLE} The rest of your search has been applied.",
    # A search may be for somewhere to stay on a visit, so it says both. What a search is
    # built from without typing is called what the founder named it, "Space
    # requirements": it said "the settings", which no page says.
    Notice.OFF_TOPIC: (
        "Burro helps you choose where to live, or where to stay on a visit. Tell it what you "
        "want from a place, or choose your space requirements to build your search without "
        "typing."
    ),
}
# What the neutral notice says where nothing that was typed changed the search.
# It is as fixed as the other, and the same for everyone.
NOTHING_CHANGED = f"{_PLACES_NOT_PEOPLE} Nothing you typed has changed your search."


def notice_text(notice: Notice, changed: bool) -> str:
    """The fixed text of a notice. `changed` is whether an edit of the answer changed the spec.

    "The rest of your search has been applied" is untrue where nothing was.
    """
    if notice is Notice.NEUTRAL_PLACES and not changed:
        return NOTHING_CHANGED
    return NOTICES[notice]


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
    # For the code `word`: the word with two meanings that was read as its place
    # part alone, as the lexicon spells it and never as it was typed. Empty for
    # every other code.
    word: str = ""


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


class Span(Record):
    """A stretch of the text: where it starts and ends, counted as `RestsOn` counts."""

    start: int
    end: int


class Choice(Record):
    """One thing a person may choose of what the reader noticed, and the edits it would make."""

    direction: SuggestionDirection
    # What the choice is called. Text of Burro's own, never the person's words.
    label: str
    # What is sent to be ranked if it is chosen. Every edit is `ui_edit`: the
    # person pressed it. All six arrays are empty for `ignore`.
    operations: Operations


class Suggestion(Record):
    """A thing the reader noticed in a prompt that is not plain. The person chooses.

    In a plain prompt, which is applied, it is what was said of a home that the
    search cannot hold: there is nothing of it to choose, and its note says why.
    """

    # `feature:<id>`, `tag:<id>`, `budget`, `tenure`, `commute` or `area`.
    target: str
    # The short label of the thing, or the release's name of the place or the area.
    label: str
    spans: tuple[Span, ...]
    # In the order more, less, ignore. `ignore` is always last.
    choices: tuple[Choice, ...]
    # What a person should know before they choose, in fixed words of Burro's
    # own: that a vibe counts recorded crime, or what Burro has no measure of
    # and what it offers in its place. Empty where there is nothing to add.
    note: str = ""
    # The person's own words name what is offered. Of a measure or a vibe, some phrase
    # it rests on names it, as "gritty" and "low crime" name what counts recorded crime,
    # and is no word that it is only read into, as "safe" and "posh" are. What is read
    # from a name or a number that was typed is named by it: a journey, a budget, a
    # home, an area.
    by_name: bool = False
    # What is offered waits for a person to choose it, and whoever takes what is
    # offered without asking leaves it: what counts who lived somewhere, whatever the
    # words, and what counts recorded crime or is a measure that is offered and never
    # applied, where the words do not name it (`only_by_choice` in `catalogue.py`).
    only_by_choice: bool = False


class NotInRelease(Record):
    """A thing a person asked for that the release holds for no area, so none is ranked on it.

    A vibe that no area has a band for, a measure the release does not carry,
    a budget where it holds no cost of that kind of home, a journey where it
    names no place. It is said, so that a person is told what is not there
    yet. It is never offered, and nothing stands in for it.
    """

    # `feature:<id>`, `tag:<id>`, `budget` or `commute`.
    target: str
    # The short label of the thing. Text of Burro's own, never the person's words.
    label: str
    # Where the words stand. Empty where an edit that was made by no words asked for it.
    spans: tuple[Span, ...]


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
    # What was noticed in a prompt that is not plain, in the order it stands. For a
    # plain prompt it holds nothing to choose: only what was said of a home that the
    # search cannot hold, each with its note and no choice but to leave it out.
    suggestions: tuple[Suggestion, ...] = ()
    # Each stretch of the text that nothing was made of and that may have asked for
    # something, in order. It is what is said to be unread.
    unread: tuple[Span, ...] = ()
    # Each stretch that nothing was made of and that asks for nothing: how a wish is
    # led in to, and what joins two. It is not said to be unread. `unmet` holds
    # `other` exactly when this or `unread` is not empty, which is where the reader
    # made nothing of some word, and a model is asked exactly then.
    asks_nothing: tuple[Span, ...] = ()
    # What was noticed in a prompt that is not plain and is not offered, because
    # the release holds it for no area. What an edit asks for and the release
    # lacks is the reducer's to say: `not_in_release_of` names both.
    not_in_release: tuple[NotInRelease, ...] = ()


class Interpreter(Protocol):
    name: InterpreterName

    def interpret(self, request: InterpretRequest) -> InterpretResult: ...


_STATED = EditProvenance.STATED
_INFERRED = EditProvenance.INFERRED
_UI = EditProvenance.UI_EDIT
_Edit = BudgetEdit | CommuteEdit | WeightEdit | TagEdit | AreaEdit
_Span = tuple[int, int]
_BEDS = (
    SegmentChoice.BED_1,
    SegmentChoice.BED_2,
    SegmentChoice.BED_3,
    SegmentChoice.BED_4PLUS,
)
_KINDS_OF_HOME = frozenset(RENT_SEGMENTS) | frozenset(BUY_SEGMENTS)
_HOMES = RENTS | BUYS | VISITS | STAYS | BEDROOMS | _KINDS_OF_HOME
# The words that expect the name of a place after them.
_CUES = EXPECTS_A_NAME | GOES_TO | REACHES | NEAR_TO
_BEFORE_A_NAME = frozenset({"the", "a", "an", "my", "our"})
# After a number of "m", it says the number is a distance: "1.5m away".
_AWAY = frozenset({"away"})
IGNORE = Choice(
    direction=SuggestionDirection.IGNORE, label="Leave it out", operations=NO_OPERATIONS
)
TAKE_OFF = "Take it off"
# What a budget and a journey are called where the release can answer neither.
A_BUDGET = "A budget"
A_JOURNEY_TO = "A journey"
BUDGET_TARGET = "budget"
COMMUTE_TARGET = "commute"


@dataclass
class _Made:
    """An edit a plain prompt made, and the words it rests on."""

    group: OpsGroup
    edit: _Edit
    spans: list[_Span]
    # It raises a weight or a vibe, as against lowering one or taking it off.
    raises: bool = True
    options: tuple[ClarifyOption, ...] | None = None
    # The word with two meanings that the edit was read from.
    word: str = ""
    # The minutes of a journey were given as a range, of which the longer was taken.
    # This is the shorter, and nothing where they were no range.
    at_least: int = 0
    # The kind of home it holds is one Burro took: a house of no kind was named.
    kind_assumed: bool = False


def _is_word(item: Item | None, among: frozenset[str]) -> bool:
    return item is not None and item.what is Is.WORD and item.text in among


def _after(items: Sequence[Item], at: int, cues: frozenset[str]) -> bool:
    """Whether some words stand straight before an item, with at most an article between."""
    while at > 0 and _is_word(items[at - 1], _BEFORE_A_NAME):
        at -= 1
    before = [item.text for item in items[max(at - 4, 0) : at] if item.what is Is.WORD]
    return any(" ".join(before[-size:]) in cues for size in (1, 2, 3, 4) if len(before) >= size)


def _cued(items: Sequence[Item], at: int) -> bool:
    """Whether the words before an item are ones that expect the name of a place."""
    if _after(items, at, _CUES):
        return True
    return _timed(items, at) and _minutes_before(items, at) > 0


# What may stand between a number of minutes and "to", "from" or "of": how the
# journey is made, "a 20 minute walk to", "35 minutes commute from".
_A_WAY_TO_GO = frozenset(GOES) | A_JOURNEY
# The ways that say how by their first word, "by bike", "on foot", "by public transport".
# Each is a way before the place as it is after it.
_BY_A_WAY = frozenset(way for way in MODES if way.split()[0] in ("by", "on"))
_AT_WORK = frozenset(word for phrase in AT_WORK for word in phrase.split())


def _to_a_place(items: Sequence[Item], at: int) -> int | None:
    """Where "to", "from" or "of" stands before a place, with where the speaker works between.

    "30 minutes to", "20 minutes from my office at". `None` where no such
    word leads in to the place.
    """

    def beside(back: int) -> bool:
        """Whether nothing but a space stands between an item and the one after it."""
        return back + 1 >= len(items) or not items[back + 1].apart

    back = at - 1
    while back >= 0 and _is_word(items[back], _BEFORE_A_NAME) and beside(back):
        back -= 1
    if back >= 0 and _is_word(items[back], TO_A_PLACE) and beside(back):
        return back
    # Where the speaker works: "from work at", "of my office in".
    far = back
    while far >= 0 and _is_word(items[far], _AT_WORK) and beside(far):
        far -= 1
    said = " ".join(item.text for item in items[far + 1 : back + 1])
    led = far >= 0 and _is_word(items[far], TO_A_PLACE) and beside(far)
    return far if led and said in AT_WORK else None


def _timed(items: Sequence[Item], at: int) -> bool:
    return _to_a_place(items, at) is not None


def _way_to(items: Sequence[Item], to: int) -> tuple[int, ModeChoice]:
    """How a journey is made, where that stands straight before "to", "from" or "of".

    "A 20 minute walk to", "a 20 minute bike ride to", "35 minutes commute
    from". It gives the item the words begin at, which is `to` where none
    stand there, and the way they say: none for "commute", which names no way.

    The way may be said there as it is said after the place: "30 minutes on
    foot to", "an hour by bike to", "20 minutes by train to". The time and
    the way were both lost, and one press added a journey of 45 minutes by
    public transport.
    """
    for size in (3, 2, 1):
        first = to - size
        run = items[max(first, 0) : to]
        apart = any(item.apart for item in items[first + 1 : to + 1])
        if first < 0 or apart or not all(item.what is Is.WORD for item in run):
            continue
        said = " ".join(item.text for item in run)
        if said in _BY_A_WAY:
            by = ModeChoice.CYCLE if said in CYCLED else ModeChoice.PT
            return first, ModeChoice.WALK if said in WALKED else by
        if said in _A_WAY_TO_GO:
            return first, GOES.get(said, ModeChoice.UNCHANGED)
    return to, ModeChoice.UNCHANGED


def _number_before(items: Sequence[Item], at: int) -> Item | None:
    """The number said straight before a place: "30 minutes to", "within 25 mins of".

    How the journey is made may stand between them: "35 minutes commute from".
    A time in hours is one number, of minutes: "1 hour 15 to". A number that
    stands where the minutes of a longer time stand, "1 hour, 15 minutes to",
    "1 15 to", is never the time of a journey by itself: the journey would be
    offered as one of 15 minutes, and one press would take it.
    """
    to = _to_a_place(items, at)
    if to is None:
        return None
    back = _way_to(items, to)[0] - 1
    if back >= 0 and _is_word(items[back], MINUTES) and not items[back + 1].apart:
        back -= 1
    number = items[back] if back >= 0 else None
    if number is None or number.what is not Is.NUMBER or number.money or items[back + 1].apart:
        return None
    return None if part_of_a_longer_time(items, back) else number


# What may stand between a time in hours and the place, of how much more the time is or how
# exact: "an hour or so to", "1 hour exactly to", "an hour and a bit to", "an hour each way
# to". After any other word the hours are said of something else: "12 hour shifts close to".
_SAID_OF_A_TIME = frozenset(
    {
        *("or", "so", "and", "n", "a", "half", "bit", "ish", "exactly", "roughly", "about"),
        *("each", "way", "total", "in", "all", "seconds", "second", "secs", "sec", "plus"),
        # There and back is twice the journey, and nobody said how long one way is.
        *("there", "back", "both", "ways", "return"),
        # The most it may be, and how the journey is made: "an hour max by bike to".
        *("max", "maximum", "tops", "at", "most", "the", "on", "by", "my"),
        *(word for way in MODES for word in way.split()),
    }
)
# No further than this before the place is a time in hours looked for.
_FURTHEST_HOURS = 5


def _says_hours(item: Item) -> bool:
    """Whether an item is a time in hours, or a word for hours: "an hour", "hours", "hour's"."""
    if item.what is Is.NUMBER:
        return item.hours
    return item.what is Is.WORD and item.text.removesuffix("'s") in HOUR_OR_ITS_LETTER


def _time_stands_before(items: Sequence[Item], at: int) -> bool:
    """Whether a time stands straight before a place, where the time of a journey stands.

    A number, a word for minutes or for hours, or a word that holds a figure,
    before "to", "from" or "of" the place, with how the journey is made
    between them or not: "1 hour, 15 minutes to", "a few hours to", "1h75
    to", "1:15 to", "24 hours commute from". A number of bedrooms and an
    amount of money are no time. It is asked where no minutes were taken for
    the journey, to tell a time that was not taken from none that was given.

    A time in hours stands there too with a word or two after it, of how
    much more it is or how exact: "an hour or so to", "an hour n a half to",
    "1 hour exactly to". One press added a journey of 45 minutes for each.
    """
    to = _to_a_place(items, at)
    if to is None:
        return False
    back = _way_to(items, to)[0] - 1
    if back < 0 or items[back + 1].apart:
        return False
    stands = items[back]
    if _is_word(stands, MINUTES) or _says_hours(stands) or stands.figures:
        return True
    if stands.what is Is.NUMBER and not stands.money and stands.unit in ("", "min"):
        return True
    for further in range(back, max(back - _FURTHEST_HOURS, -1), -1):
        item = items[further]
        if _says_hours(item):
            return True
        said_of_it = item.what is Is.NUMBER or _is_word(item, _SAID_OF_A_TIME | MINUTES)
        # A journey by car is none that Burro holds, and the time before it is a time.
        by_car = item.unmet is UnmetCategory.DRIVING
        if item.apart or not (said_of_it or by_car):
            break
    return False


def _minutes_before(items: Sequence[Item], at: int) -> int:
    """The minutes said straight before a place, where they are minutes a journey may take."""
    number = _number_before(items, at)
    if number is None:
        return 0
    return number.value if LIMITS.minutes_min <= number.value <= LIMITS.minutes_max else 0


def _where_minutes_start(items: Sequence[Item], at: int) -> int:
    number = _number_before(items, at)
    return items[at].start if number is None else number.start


def _range_before(items: Sequence[Item], at: int) -> int:
    """The shorter of a range of minutes said straight before a place, or nothing."""
    number = _number_before(items, at)
    return number.low if number is not None and _minutes_before(items, at) else 0


@dataclass
class _Sentence:
    """One sentence, what it is made of, and what the grammar made of it."""

    line: Line
    items: list[Item]
    wishes: list[Wish] | None  # `None` where the grammar does not make the sentence
    asked: bool = False
    taken_back: bool = False

    @property
    def plain(self) -> bool:
        return self.wishes is not None

    @property
    def own(self) -> bool:
        """Whether the speaker says a wish of their own in it: "I want", "we need"."""
        return any(
            _is_word(first, SPEAKER.words) and _is_word(second, WISH.words)
            for first, second in pairwise(self.items)
        )

    @property
    def names(self) -> bool:
        """Whether it names something: a thing, a place, a number, a home, or what is unmet."""
        named = (Is.THING, Is.NAME, Is.PEOPLE, Is.AMENITY, Is.UNMET)
        return any(
            item.what in named
            or (item.what is Is.NUMBER and (item.money or bool(item.unit) or len(self.items) > 1))
            or _is_word(item, _HOMES)
            or _cued(self.items, at + 1)
            for at, item in enumerate(self.items)
        )


def _option(match: Match) -> ClarifyOption:
    return ClarifyOption(id=match.id, name=match.name, kind=match.kind)


# --- A plain prompt: every item makes the edit the contract gives it -----------------


def _weight_edits(wish: Wish, target: Target) -> Iterator[tuple[_Edit, bool]]:
    """The edits for a thing that was named, from what is said of it (contract 5.2, 8.2)."""
    way = wish.way
    turned = way in (Way.NOT_AT_ALL, Way.LESS)
    up = Step.UP_SMALL if wish.step is Step.UP_SMALL or way is Way.LESS else Step.UP_LARGE
    down = Step.DOWN_LARGE if wish.large else Step.DOWN_SMALL
    for feature_id in target.features:
        action, value, step, direction = WeightAction.NUDGE, 0.0, up, target.direction
        raises = True
        if way is Way.OFF:
            action, step, raises = WeightAction.REMOVE, Step.NONE, False
        elif way is Way.DOWN:
            step, raises = down, False
        elif turned and not target.nuisance:
            raises = False
            if FEATURES[feature_id].polarity is Polarity.EITHER:
                # Fewer of it is a taste in places, so it is a wish like any other.
                step, direction = Step.UP_LARGE, DirectionChoice.LESS
            else:
                # It never raises a weight. Wanted less, the weight is turned down.
                # Not wanted at all, it is taken off, so that a default stops
                # counting for a thing the person has said they do not want.
                step = Step.DOWN_SMALL if way is Way.LESS else Step.NONE
                action = WeightAction.NUDGE if way is Way.LESS else WeightAction.REMOVE
        elif wish.essential:
            action, value, step = WeightAction.SET, 1.0, Step.NONE
        yield (
            WeightEdit(
                action=action,
                feature_id=feature_id,
                value=value,
                step=step,
                direction=direction,
                provenance=target.provenance,
            ),
            raises,
        )
    for tag_id in target.tags:
        scale = TAGS[tag_id].shape is TagShape.SCALE
        action, value, step, raises = WeightAction.NUDGE, 0.0, up, True
        toward = TowardChoice(target.toward.value)
        if way is Way.OFF:
            action, step, raises = WeightAction.REMOVE, Step.NONE, False
            toward = TowardChoice.DEFAULT
        elif way is Way.DOWN:
            step, raises, toward = down, False, TowardChoice.DEFAULT
        elif turned and scale:
            # A turned end is the other end: "not buzzy" is Pace towards Calm.
            toward = TowardChoice.LOW if target.toward is Toward.HIGH else TowardChoice.HIGH
        elif turned:
            # A vibe with one direction can only be turned down, or taken off.
            step = Step.DOWN_SMALL if way is Way.LESS else Step.NONE
            action = WeightAction.NUDGE if way is Way.LESS else WeightAction.REMOVE
            raises, toward = False, TowardChoice.DEFAULT
        elif wish.essential:
            action, value, step = WeightAction.SET, 1.0, Step.NONE
        yield (
            TagEdit(
                action=action,
                tag_id=tag_id,
                value=value,
                step=step,
                toward=toward,
                provenance=target.provenance,
            ),
            raises,
        )


def _visit(home: Home) -> tuple[BudgetEdit, list[_Span]]:
    """The edit that makes a search a visit. It holds the kind of search, and nothing else."""
    edit = BudgetEdit(
        action=BudgetAction.SET,
        tenure=TenureChoice.VISIT,
        amount=0,
        segment=SegmentChoice.UNCHANGED,
        strictness=StrictnessChoice.UNCHANGED,
        step=Step.NONE,
        provenance=_STATED,
    )
    return edit, sorted({*home.visits, *home.stays})


def _budget(home: Home, spec: PreferenceSpec) -> tuple[BudgetEdit, list[_Span]] | None:
    """The one budget edit a prompt makes, from everything it says of the home.

    A visit holds no budget and no home. Where the words say a visit, the
    edit says so and holds nothing else, and where the search is a visit and
    the words name no other kind of search, no edit is made: what was said of
    an amount or of a home is said to be what a visit cannot hold
    (`_not_held_of`). An amount by the month is a rent, and says so.
    """
    amount, hard, where = home.amounts[0] if home.amounts else (0, False, (0, 0))
    spans: list[_Span] = [where] if home.amounts else []
    tenure = TenureChoice.UNCHANGED
    if home.visits:
        return _visit(home)
    if home.rents or home.buys:
        tenure = TenureChoice.RENT if home.rents else TenureChoice.BUY
        spans += home.rents or home.buys
    elif home.monthly:
        tenure = TenureChoice.RENT
        spans += home.monthly
    elif spec.visiting:
        # An amount alone may be what the visit may cost. It names no home.
        return None
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
    kinds = RENT_SEGMENTS if chosen is Tenure.RENT else BUY_SEGMENTS
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


def _for_a_house_of_no_kind(home: Home, spec: PreferenceSpec) -> bool:
    """Whether a prompt gives an amount to buy a house, and names no kind of house.

    Decided on 2026-09-25: a house is no flat. A price is held by the kind of
    home, and a search to buy holds a flat until a kind is said, so the
    amount was held against what flats sold for. It is held against what
    terraced houses sold for, `DEFAULT_HOUSE`, and the kind is said to be
    assumed. Where a release holds no price for a terraced house the kind is
    the person's to say: the prompt is not plain, and the budget is offered
    for each kind of house that has a price. A rent is held by the number of
    bedrooms, whatever kind of home it is for, and a house with no amount
    holds a budget against nothing.
    """
    made = _budget(home, spec) if home.houses else None
    if made is None:
        return False
    edit = made[0]
    tenure = spec.tenure if edit.tenure is TenureChoice.UNCHANGED else Tenure(edit.tenure.value)
    unsaid = edit.segment is SegmentChoice.UNCHANGED
    return bool(edit.amount) and unsaid and tenure is Tenure.BUY


def _as_can_be_tested(
    edit: BudgetEdit, spans: list[_Span], amount_at: _Span | None, request: InterpretRequest
) -> list[tuple[BudgetEdit, list[_Span]]]:
    """The budget edit of a prompt, in two where the release cannot test its amount.

    An edit is applied whole or not at all. Where the release holds no cost
    of that kind of home, the one edit was turned away with all it held, and
    "buying a terraced house under £450k" left the search a renter's. What
    is said of the home is kept: to rent or to buy, and the kind of home.
    The amount is an edit of its own, which the reducer turns away, so that
    the person is told what is missing. Where the amount can be tested, or
    nothing else was said, it is one edit, as it always was.
    """
    unsaid = (TenureChoice.UNCHANGED, SegmentChoice.UNCHANGED)
    if edit.action is not BudgetAction.SET or not edit.amount or amount_at is None:
        return [(edit, spans)]
    if (edit.tenure, edit.segment) == unsaid:
        return [(edit, spans)]
    alone = NO_OPERATIONS.replace(budget_ops=(edit,))
    tried = apply(given_way_spec(request.spec), alone, request.release)
    if not any(turned.reason is RejectReason.NOT_IN_RELEASE for turned in tried.rejected):
        return [(edit, spans)]
    home = edit.replace(amount=0, strictness=StrictnessChoice.UNCHANGED)
    amount = edit.replace(tenure=unsaid[0], segment=unsaid[1])
    return [(home, [span for span in spans if span != amount_at]), (amount, [amount_at])]


def assumptions_for(operations: Operations, spec: PreferenceSpec) -> tuple[Assumption, ...]:
    """What each edit left to a default, so the person can see it and change it.

    Worked out from the edits and the spec they were made for, so every
    interpreter states the same assumptions for the same edits.
    """
    found: list[Assumption] = []

    def assume(code: AssumptionCode, group: OpsGroup, index: int) -> None:
        found.append(Assumption(code=code, group=group, index=index))

    nobody_chose = spec.budget.provenance is Provenance.DEFAULT
    # What an edit before it said of the home is not assumed of the amount:
    # a budget is made in two where its amount cannot be tested.
    tenure_said = segment_said = False
    # A visit holds no budget, so nothing is assumed of one.
    visiting = spec.visiting
    for index, edit in enumerate(operations.budget_ops):
        if edit.action is not BudgetAction.SET:
            continue
        if edit.tenure is not TenureChoice.UNCHANGED:
            visiting = edit.tenure is TenureChoice.VISIT
        if edit.amount != 0 and not visiting:
            unsaid = edit.tenure is TenureChoice.UNCHANGED and not tenure_said
            if unsaid and spec.tenure_from is Provenance.DEFAULT:
                assume(AssumptionCode.TENURE, OpsGroup.BUDGET, index)
            moved = edit.tenure is not TenureChoice.UNCHANGED and edit.tenure.value != spec.tenure
            left = edit.segment is SegmentChoice.UNCHANGED and not segment_said
            if left and (nobody_chose or moved):
                assume(AssumptionCode.SEGMENT, OpsGroup.BUDGET, index)
            if edit.strictness is StrictnessChoice.UNCHANGED and nobody_chose:
                assume(AssumptionCode.STRICTNESS, OpsGroup.BUDGET, index)
        tenure_said = tenure_said or edit.tenure is not TenureChoice.UNCHANGED
        segment_said = segment_said or edit.segment is not SegmentChoice.UNCHANGED

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


def _about(made: _Made) -> tuple[OpsGroup, str]:
    """What an edit is about: a place, an area, a feature or a vibe, by its id."""
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


@dataclass
class _Read:
    """Everything a plain prompt said: the edits it makes, and what makes none."""

    made: list[_Made] = field(default_factory=list[_Made])
    home: Home = field(default_factory=Home)
    # Where the words of the home stand, for the day no edit can be made of them.
    home_spans: list[_Span] = field(default_factory=list[_Span])
    # Minutes said apart from any place, "a 40 minute commute on foot", each
    # with how they are travelled and whether they are a limit.
    loose: list[Wish] = field(default_factory=list[Wish])
    # What may not be applied for what it is: "safe", "a gym", "edgy".
    offered: list[Wish] = field(default_factory=list[Wish])
    # A journey to a place that may be where the person lives now, "I commute
    # from", which is offered and never applied.
    maybe: list[_Made] = field(default_factory=list[_Made])
    unmet: set[UnmetCategory] = field(default_factory=set[UnmetCategory])
    about_people: bool = False


def _read(wishes: Sequence[Wish]) -> _Read:
    found = _Read()
    for wish in wishes:
        if wish.kind is Kind.HOME:
            found.home.add(wish.home)
            found.home_spans += wish.spans
        elif wish.kind is Kind.PEOPLE:
            found.about_people = True
        elif wish.kind is Kind.NO_MEASURE:
            found.unmet |= set(wish.unmet)
        elif wish.kind is Kind.RULE:
            edit = AreaEdit(action=wish.action, area_id=wish.area_id, provenance=_STATED)
            found.made.append(_Made(OpsGroup.AREA, edit, wish.spans))
        elif wish.kind is Kind.JOURNEY and wish.loose:
            found.loose.append(wish)
        elif wish.kind is Kind.JOURNEY and wish.offered:
            found.maybe.append(_journey(wish))
        elif wish.kind is Kind.JOURNEY:
            found.made.append(_journey(wish))
        elif wish.kind is Kind.WISH and wish.offered:
            found.offered.append(wish)
        elif wish.kind is Kind.WISH and wish.target is not None:
            _wished(found, wish, wish.target)
    return found


def _left_to_choose(read: _Read) -> bool:
    """Whether a prompt holds a word that may not be applied, and names what it reaches nowhere.

    "Safe" names no crime, so it sets none counting: it is offered. Beside
    a wish that names the same thing outright, "safe, with low crime", the
    person has asked by name, and the word adds nothing to what they said.
    A place that is commuted from is always left to choose.
    """
    if read.maybe:
        return True
    named = {
        (*_about(made), getattr(made.edit, "toward", TowardChoice.HIGH))
        for made in read.made
        if made.raises and getattr(made.edit, "provenance", None) is _STATED
    }
    for wish in read.offered:
        target = wish.target
        assert target is not None
        toward = TowardChoice(target.toward.value)
        reaches = {(OpsGroup.WEIGHT, f.value, TowardChoice.HIGH) for f in target.features}
        reaches |= {(OpsGroup.TAG, t.value, toward) for t in target.tags}
        if not reaches <= named:
            return True
    return False


def _wished(found: _Read, wish: Wish, target: Target) -> None:
    turned = wish.way is not Way.NONE
    one_way = any(TAGS[tag_id].shape is TagShape.ONE_WAY for tag_id in target.tags)
    if target.word and turned and one_way:
        # "Not gritty", where gritty is built from land use alone. It is no wish
        # for fewer works: Burro has no measure of upkeep, and says so.
        found.unmet.add(UnmetCategory.UPKEEP)
        return
    if target.unmet is not None:
        found.unmet.add(target.unmet)
    for edit, raises in _weight_edits(wish, target):
        group = OpsGroup.TAG if isinstance(edit, TagEdit) else OpsGroup.WEIGHT
        quoted = target.word if edit.provenance is _INFERRED else ""
        found.made.append(_Made(group, edit, list(wish.spans), raises, word=quoted))


def _journey(wish: Wish) -> _Made:
    options = None if wish.options is None else tuple(_option(m) for m in wish.options)
    edit = CommuteEdit(
        action=CommuteAction.ADD,
        place_id="" if options is not None else wish.place_id,
        mode=wish.mode,
        max_minutes=wish.minutes,
        strictness=StrictnessChoice.HARD
        if wish.minutes and wish.firm
        else StrictnessChoice.UNCHANGED,
        step=Step.NONE,
        provenance=_STATED,
    )
    at_least = wish.at_least if wish.minutes else 0
    return _Made(OpsGroup.COMMUTE, edit, list(wish.spans), options=options, at_least=at_least)


def _given(loose: Sequence[Wish]) -> tuple[set[int], set[ModeChoice]]:
    """The minutes that were said apart from any place, and the ways of travelling them."""
    modes = {wish.mode for wish in loose} - {ModeChoice.UNCHANGED}
    return {wish.minutes for wish in loose}, modes


def _journeys_disagree(read: _Read) -> bool:
    """Whether minutes said apart from any place can be the limit of no journey.

    "A 40 minute commute on foot" is the limit, and the way, of each journey
    of the prompt. Where the prompt names no journey, there is nothing for it
    to be said of. Where a journey was given other minutes or another way,
    or two such wishes differ, the reader cannot say which is meant.
    """
    if not read.loose:
        return False
    minutes, modes = _given(read.loose)
    journeys = [made.edit for made in read.made if isinstance(made.edit, CommuteEdit)]
    return (
        not journeys
        or len(minutes) > 1
        or len(modes) > 1
        or any(edit.max_minutes and edit.max_minutes not in minutes for edit in journeys)
        or any(modes and edit.mode not in (ModeChoice.UNCHANGED, *modes) for edit in journeys)
    )


def _with_loose(made: _Made, loose: Sequence[Wish]) -> _Made:
    """A journey with the minutes that were said apart from it, how, and whether firmly.

    The way of travelling and the firmness of the limit stand with the
    minutes. "A 40 minute commute on foot" was read as 40 minutes by public
    transport, and "no more than 35 minutes" as a wish and no limit.
    """
    edit = made.edit
    if not loose or not isinstance(edit, CommuteEdit):
        return made
    (minutes,), modes = _given(loose)
    firm = any(wish.firm for wish in loose) or edit.strictness is StrictnessChoice.HARD
    spans = [span for wish in loose for span in wish.spans]
    return dataclasses.replace(
        made,
        edit=edit.replace(
            max_minutes=minutes,
            mode=next(iter(modes), edit.mode),
            strictness=StrictnessChoice.HARD if firm else StrictnessChoice.UNCHANGED,
        ),
        spans=[*made.spans, *spans],
        at_least=max(wish.at_least for wish in loose),
    )


def _said_both_ways(read: _Read) -> bool:
    """Whether a prompt both asks for a thing and turns it away, or says two things of one.

    "Pubs or no pubs", "to rent, or to buy", two budgets, one area to be left
    out and to be the only one, a journey of 30 minutes and of 40. The
    reader cannot say which is meant.
    """
    ways: dict[tuple[OpsGroup, str], set[object]] = {}
    for made in read.made:
        edit = made.edit
        if isinstance(edit, WeightEdit):
            said: object = (made.raises, edit.direction is DirectionChoice.LESS)
        elif isinstance(edit, TagEdit):
            said = (made.raises, edit.toward is TowardChoice.LOW)
        elif isinstance(edit, AreaEdit):
            said = edit.action
        else:
            continue
        ways.setdefault(_about(made), set()).add(said)
    twice = any(len(found) > 1 for found in ways.values())
    amounts = {amount for amount, _, _ in read.home.amounts}
    return twice or not read.home.agrees or len(amounts) > 1 or _journeys_disagree(read)


# --- A prompt that is not plain: what was noticed, for the person to choose ---------


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


class _Noticed(NamedTuple):
    """One thing noticed in a text, where it stands, and what may be chosen of it."""

    target: str
    label: str
    span: _Span
    choices: tuple[Choice, ...]
    note: str = ""
    # It is offered whether or not to choose it would change the search, and
    # where nothing of it can be chosen it is still said to have been heard.
    always: bool = False
    # The words name it. A thing of the lexicon says for itself whether its phrase does.
    by_name: bool = True


# What is said on a choice of a vibe whose recipe holds recorded crime, so that
# nobody sets crime counting without being told.
COUNTING_CRIME = ", counting recorded crime"


def _listed(things: Sequence[str]) -> str:
    """The things, as a list is said. A comma stands before the last where one holds "and"."""
    if len(things) == 1:
        return things[0]
    last = ", and " if any(" and " in thing for thing in things) else " and "
    return f"{', '.join(things[:-1])}{last}{things[-1]}"


def counts_crime(tag_id: TagId) -> str:
    """What a vibe whose recipe holds recorded crime says of itself wherever it is offered."""
    tag = TAGS[tag_id]
    parts = [FEATURES[term.feature_id] for term in tag.terms]
    recorded = [_lower_first(part.label) for part in parts if part.dimension is Dimension.CRIME]
    return f"{tag.label} counts {_listed(recorded)}. {CRIME_CAVEAT}"


def _weigh(feature_id: FeatureId, direction: DirectionChoice) -> Operations:
    edit = WeightEdit(
        action=WeightAction.NUDGE,
        feature_id=feature_id,
        value=0.0,
        step=Step.UP_LARGE,
        direction=direction,
        provenance=_UI,
    )
    return NO_OPERATIONS.replace(weight_ops=(edit,))


def _feature_choices(feature_id: FeatureId) -> tuple[Choice, ...]:
    feature = FEATURES[feature_id]
    more, less = SuggestionDirection.MORE, SuggestionDirection.LESS
    if feature_id in COUNTS_RESIDENTS:
        # More of what it counts, and no other choice but to leave it out. No choice of
        # such a measure is ever sent as less, not even to take its weight off.
        wished = _weigh(feature_id, DirectionChoice.MORE)
        return (Choice(direction=more, label=feature.short_label, operations=wished),)
    if feature.polarity is Polarity.EITHER:
        # "More pubs and bars", "Fewer pubs and bars". A word of the feature's
        # own, "denser", stands by itself.
        thing = f" {_lower_first(feature.short_label)}" if feature.higher == "more" else ""
        return (
            Choice(
                direction=more,
                label=f"{feature.higher.capitalize()}{thing}",
                operations=_weigh(feature_id, DirectionChoice.MORE),
            ),
            Choice(
                direction=less,
                label=f"{feature.lower.capitalize()}{thing}",
                operations=_weigh(feature_id, DirectionChoice.LESS),
            ),
        )
    wished = _weigh(feature_id, DirectionChoice.DEFAULT)
    if feature.kind is FeatureKind.NUISANCE:
        # The one direction a nuisance has is less of it, and its short label says so.
        return (Choice(direction=less, label=feature.short_label, operations=wished),)
    off = WeightEdit(
        action=WeightAction.REMOVE,
        feature_id=feature_id,
        value=0.0,
        step=Step.NONE,
        direction=DirectionChoice.DEFAULT,
        provenance=_UI,
    )
    return (
        Choice(direction=more, label=feature.short_label, operations=wished),
        Choice(direction=less, label=TAKE_OFF, operations=NO_OPERATIONS.replace(weight_ops=(off,))),
    )


def _tag_edit(tag_id: TagId, toward: TowardChoice, action: WeightAction) -> Operations:
    edit = TagEdit(
        action=action,
        tag_id=tag_id,
        value=0.0,
        step=Step.UP_LARGE if action is WeightAction.NUDGE else Step.NONE,
        toward=toward,
        provenance=_UI,
    )
    return NO_OPERATIONS.replace(tag_ops=(edit,))


def _one_way(
    choices: tuple[Choice, ...], direction: DirectionChoice = DirectionChoice.DEFAULT
) -> tuple[Choice, ...]:
    """The choices of a thing that is offered one way: more of it, and no other.

    Where the phrase says that less is wanted, it is less of it, and no other.
    """
    less = direction is DirectionChoice.LESS
    wanted = SuggestionDirection.LESS if less else SuggestionDirection.MORE
    return tuple(choice for choice in choices if choice.direction is wanted)


def _tag_choices(tag_id: TagId, only: Toward | None = None) -> tuple[Choice, ...]:
    """What may be chosen of a vibe. `only` is the one end to offer, where one is named."""
    tag = TAGS[tag_id]
    more, less = SuggestionDirection.MORE, SuggestionDirection.LESS
    nudge, remove = WeightAction.NUDGE, WeightAction.REMOVE
    # A choice says all that it sets counting, on its own face.
    crime = COUNTING_CRIME if tag_id in HOLDS_CRIME else ""
    if tag_id in HOLDS_RESIDENTS:
        # More of it, and no other choice but to leave it out.
        only = Toward.HIGH
    if tag.shape is TagShape.SCALE:
        ends = (
            Choice(
                direction=more,
                label=f"Towards {tag.high_end}{crime}",
                operations=_tag_edit(tag_id, TowardChoice.HIGH, nudge),
            ),
            Choice(
                direction=less,
                label=f"Towards {tag.low_end}{crime}",
                operations=_tag_edit(tag_id, TowardChoice.LOW, nudge),
            ),
        )
        return ends if only is None else ends[:1] if only is Toward.HIGH else ends[1:]
    if only is not None:
        add = _tag_edit(tag_id, TowardChoice.HIGH, nudge)
        return (Choice(direction=more, label=f"Add {tag.label}{crime}", operations=add),)
    return (
        Choice(
            direction=more,
            # The name of the vibe, as it is printed wherever the vibe is shown.
            label=f"Add {tag.label}{crime}",
            operations=_tag_edit(tag_id, TowardChoice.HIGH, nudge),
        ),
        Choice(
            direction=less,
            label=TAKE_OFF,
            operations=_tag_edit(tag_id, TowardChoice.DEFAULT, remove),
        ),
    )


# How a journey is travelled, as the label of a choice says it.
_HOW: Mapping[ModeChoice, str] = {
    ModeChoice.PT: " by public transport",
    ModeChoice.CYCLE: " by bike",
    ModeChoice.WALK: " on foot",
}


def _journey_choice(
    name: str,
    place_id: str,
    minutes: int,
    firm: bool = False,
    mode: ModeChoice = ModeChoice.UNCHANGED,
) -> tuple[Choice, ...]:
    """To add a journey to a place, with what was said of it.

    The label says the minutes, whether they are a limit and how they are
    travelled, wherever the choice holds them, so that a person sees all that
    they choose. Of a journey that is only noticed, in a sentence the grammar
    does not make, it holds the minutes said straight before the place, and
    they are a limit where the words against them make them one.
    """
    hard = bool(minutes and firm)
    edit = CommuteEdit(
        action=CommuteAction.ADD,
        place_id=place_id,
        mode=mode,
        max_minutes=minutes,
        strictness=StrictnessChoice.HARD if hard else StrictnessChoice.UNCHANGED,
        step=Step.NONE,
        provenance=_UI,
    )
    within = f" of no more than {minutes} minutes" if hard else f" within {minutes} minutes"
    return (
        Choice(
            direction=SuggestionDirection.MORE,
            label=f"Add a journey to {name}{within if minutes else ''}{_HOW.get(mode, '')}",
            operations=NO_OPERATIONS.replace(commute_ops=(edit,)),
        ),
    )


# What is said of a place that a person asks to be far from. It is offered with nothing
# to choose but to leave it out, so that they are told it was heard.
NO_STAYING_AWAY = "Burro cannot rank on being far from a place."
# What is said of a place where a time stands before it that is none a journey to it may
# hold: the minutes of a longer time, hours the reader does not read, a time beyond what
# any journey may take. No journey is offered, since it would be added with the usual
# minutes, which nobody said.
TIME_NOT_TAKEN = (
    "Burro could not take the time beside this place as the time of a journey. "
    "Say the whole of it in minutes."
)
# What is said of a place where a time was typed apart from it, and the reader cannot tell
# which journey the time is for, or what it says of it. The journey is offered with no time,
# as a journey that was given none is, and whoever words the offer says that a time was
# given and not taken: it never says that the person gave none.
TIME_NOT_PLACED = (
    "You gave a number of minutes, but Burro could not tell whether it is for this journey. "
    "Say the minutes and the place together, with the minutes first."
)
# What is said of a place that may be somebody else's, or one that was left.
MAY_BE_ANOTHERS = "Burro cannot tell whether you must reach this place. Add it if you must."
# What is said of a thing that the words turn round, where no way is offered that counts it
# for more: "I hate culture". A thing that runs one way can rank an area higher and never
# lower, so there is nothing to take of a wish against it. Where it counts in the search
# already, as a station does until a person says otherwise, to stop counting it is what
# is left to choose. What follows the offer of that says already that Burro cannot rank
# an area for the opposite, and a page prints the two together, so it is not said twice.
NOT_WANTED = (
    "Burro read your words as saying that you do not want this. It can rank an area higher "
    "for having it, but never lower, so it has left it out of your search."
)
NOT_WANTED_AND_COUNTED = (
    "Burro read your words as saying that you do not want this, so the most it can do is "
    "to stop counting it."
)
# The same of a nuisance, which is wanted less or not minded: "crime doesn't bother me".
DOES_NOT_MATTER = (
    "Burro read your words as saying that this does not matter to you, so it has left it "
    "out of your search."
)
# What is said of a thing that is offered and waits for a person, because the words do not
# say that the wish is their own: it may be somebody else's, it stands in a list whose
# words may turn it away, or it is a nuisance that is only named.
NOT_SAID_TO_BE_WANTED = (
    "Burro could not tell from your words whether you want this yourself, so it has left "
    "it for you to add."
)


def longer_was_taken(at_least: int, minutes: int) -> str:
    """What an offer says of a range of minutes, so that the person sees which was taken."""
    return (
        f"You gave {at_least} to {minutes} minutes, so Burro has used {minutes}, the longer "
        "of the two."
    )


def _said_of_what_is_offered(sentences: Sequence["_Sentence"]) -> Iterator[tuple[_Span, _Span]]:
    """Where each thing that is only offered stands, and the words that were said of it.

    In a sentence the grammar makes, a hedge, an article and a word for a
    place belong to the thing they stand with: "slightly affluent", "a
    well-heeled area". The offer rests on all of them, so that none is called
    unread. It is so only of a thing that is offered and never applied.
    """
    for sentence in sentences:
        if not sentence.plain or sentence.taken_back:
            continue
        offered = [wish for wish in sentence.wishes or () if wish.offered]
        for item in sentence.items:
            for wish in offered:
                start, end = wish.spans[0]
                if item.what is Is.THING and start <= item.start and item.end <= end:
                    yield item.span, (start, end)


def _journeys_made(sentences: Sequence["_Sentence"], grammar: Grammar) -> list[_Made]:
    """The journeys of the sentences the grammar makes, in a prompt that is not plain.

    A journey is made of a cue, a number, words for travelling and a name,
    each of which the grammar places. Where it makes the whole of the
    sentence a journey stands in, and no sentence beside it takes it back,
    the journey is read with all that was said of it: its minutes, whether
    they are a limit and how they are travelled. It is still only offered,
    since the prompt is not plain. Minutes said apart from any place are the
    limit of each, as in a plain prompt, where they agree with it.

    With them are the journeys that a part of any other sentence asks about:
    `_asked_in_part`.
    """
    known = [sentence for sentence in sentences if sentence.plain and not sentence.taken_back]
    read = _read([wish for sentence in known for wish in sentence.wishes or ()])
    made = [found for found in read.made if isinstance(found.edit, CommuteEdit)]
    loose = read.loose if made and not _journeys_disagree(read) else []
    journeys = [*(_with_loose(journey, loose) for journey in made), *_maybe(read, bool(made))]
    journeys += [_journey(wish) for wish in _asked_in_part(sentences, grammar)]
    return sorted(journeys, key=lambda journey: min(journey.spans))


def _asked_in_part(sentences: Sequence["_Sentence"], grammar: Grammar) -> list[Wish]:
    """The journeys that ask which place is meant, in the sentences the grammar does not make.

    "Leafy and quiet, 30 minutes to Pellam, honestly" is not plain, for its
    last word. The part that says the journey is one the grammar makes by
    itself, as it does in a plain list: a time or a cue, and a name that
    several places bear a part of. The journey was dropped there, and where
    an area answers to the name a rule for the area was offered in its
    place. It is asked about, as it is in a plain list.

    Nothing is asked of a sentence that asks, of one that the next takes
    back, or of one that holds a word for staying away: whoever answers the
    question adds a journey to the place.
    """
    found: list[Wish] = []
    for sentence, kept_away in zip(sentences, _kept_away(sentences), strict=True):
        if not (sentence.plain or sentence.asked or sentence.taken_back or kept_away):
            found += grammar.asks_which_place(sentence.items)
    return found


def _maybe(read: _Read, beside_a_journey: bool) -> list[_Made]:
    """The places that are commuted from, each with what may be offered of it.

    Minutes said apart from any place are the limit of the journey to where
    the person works, where the prompt names one. Where the one journey it
    names is from a place, "I commute from Wickerford, at most 40 minutes",
    they are said of that, and the offer holds them.
    """
    minutes, modes = _given(read.loose)
    alone = not beside_a_journey and len(read.maybe) == 1
    if not alone or len(minutes) != 1 or len(modes) > 1:
        return read.maybe
    (journey,) = read.maybe
    assert isinstance(journey.edit, CommuteEdit)
    if journey.edit.max_minutes and journey.edit.max_minutes not in minutes:
        return read.maybe
    return [_with_loose(journey, read.loose)]


def _area_choice(name: str, area_id: str, turned_away: bool) -> tuple[Choice, ...]:
    """An area that was named: to look only there, or to leave it out.

    After a word that turns it away, "avoid Cindermoor if you can", to look
    only there is the opposite of what was said, and is not offered.
    """

    def rule(action: AreaAction) -> Operations:
        edit = AreaEdit(action=action, area_id=area_id, provenance=_UI)
        return NO_OPERATIONS.replace(area_ops=(edit,))

    out = Choice(
        direction=SuggestionDirection.LESS,
        label=f"Leave out {name}",
        operations=rule(AreaAction.EXCLUDE),
    )
    only = Choice(
        direction=SuggestionDirection.MORE,
        label=f"Look only in {name}",
        operations=rule(AreaAction.ONLY),
    )
    return (out,) if turned_away else (only, out)


_TO = {TenureChoice.RENT: ", to rent", TenureChoice.BUY: ", to buy"}


def _budget_choice(
    label: str,
    tenure: TenureChoice = TenureChoice.UNCHANGED,
    amount: int = 0,
    segment: SegmentChoice = SegmentChoice.UNCHANGED,
    firm: bool = False,
) -> tuple[Choice, ...]:
    """One thing said of the budget, and no more: an amount, a tenure, or a kind of home.

    An amount is a firm limit where the words against it say the most that
    can be paid, and the label says so.
    """
    edit = BudgetEdit(
        action=BudgetAction.SET,
        tenure=tenure,
        amount=amount,
        segment=segment,
        strictness=StrictnessChoice.HARD if amount and firm else StrictnessChoice.UNCHANGED,
        step=Step.NONE,
        provenance=_UI,
    )
    return (
        Choice(
            direction=SuggestionDirection.MORE,
            label=label,
            operations=NO_OPERATIONS.replace(budget_ops=(edit,)),
        ),
    )


def _for_a_house(
    label: str,
    tenure: TenureChoice,
    amount: int,
    kind: SegmentChoice,
    *,
    firm: bool,
    assumed: bool,
) -> Choice:
    """An amount for one kind of house: the kind, and then the amount as it was worded.

    The kind stands in an edit of its own, which says whose it is. The one
    Burro took is inferred, so that whoever shows the search can mark it as
    assumed. One that a person presses is theirs.
    """
    of_the_kind = BudgetEdit(
        action=BudgetAction.SET,
        tenure=tenure,
        amount=0,
        segment=kind,
        strictness=StrictnessChoice.UNCHANGED,
        step=Step.NONE,
        provenance=_INFERRED if assumed else _UI,
    )
    (worded,) = _budget_choice(label, tenure, amount=amount, firm=firm)
    return worded.replace(
        operations=NO_OPERATIONS.replace(budget_ops=(of_the_kind, *worded.operations.budget_ops))
    )


def _a_terraced_house(release: Release) -> str:
    """What is said where a terraced house is taken, of the release that is served.

    A terraced house is said to be the least dear kind of house in most areas
    only where it is: in more than half of the areas that hold a price for
    any kind of house.
    """
    priced = least = 0
    for area in release.neighbourhoods:
        rows = (
            release.cost(area.area_id, Tenure.BUY, Segment(kind.value)) for kind in KINDS_OF_HOUSE
        )
        held = {row.segment: row.median for row in rows if row is not None}
        priced += bool(held)
        least += DEFAULT_HOUSE in held and held[DEFAULT_HOUSE] == min(held.values())
    why = THE_LEAST_DEAR if 2 * least > priced else ""
    return f"{A_TERRACED_HOUSE}{why}{ONE_PRESS_AWAY}"


# What may stand between a word that caps and its number: "up to about £1,500".
_OR_SO = frozenset({"about", "around"})


# A year holds 52 weeks and 12 months, which is how a rent by the week is said by the month.
_WEEKS_A_YEAR = 52
_MONTHS_A_YEAR = 12


def by_the_month(by_the_week: int) -> int:
    """What an amount by the week comes to by the month, to the nearest pound.

    At 52 weeks to 12 months: £350 a week is £1,517 a month. It is counted
    in whole pounds, and no amount of whole pounds a week comes to half a
    pound a month, so nothing is rounded one way or the other by a rule.
    """
    return (by_the_week * _WEEKS_A_YEAR + _MONTHS_A_YEAR // 2) // _MONTHS_A_YEAR


def worked_out_by_the_month(by_the_week: int) -> str:
    """What an offer says of an amount by the week: that it was worked out, and from what."""
    return (
        f"You gave £{money(by_the_week)} a week. Burro knows rents by the month, so it has "
        f"worked out what that comes to, at {_WEEKS_A_YEAR} weeks to {_MONTHS_A_YEAR} "
        f"months: £{money(by_the_month(by_the_week))} a month."
    )


def _said_firmly(
    items: Sequence[Item], first: int, after: int, firmly: frozenset[str]
) -> _Span | None:
    """Where the words that make a limit firm stand against a number, before it or after.

    Before it, with nothing between but "about" or "around": "up to about
    £1,500". After it and what it is a number of: "£1,500 a month max". No
    further than a mark, so that the words of one number make no other firm.
    Nothing where no such words stand against it.
    """
    while first > 0 and not items[first].apart and _is_word(items[first - 1], _OR_SO):
        first -= 1
    led: list[Item] = []
    at = first
    while at > 0 and not items[at].apart and items[at - 1].what is Is.WORD and len(led) < 4:
        led.insert(0, items[at - 1])
        at -= 1
    for size in range(len(led), 0, -1):
        if " ".join(item.text for item in led[-size:]) in firmly:
            return led[-size].start, items[first].start
    if after < len(items) and not items[after].apart:
        said = _phrase_at(items, after, firmly, longest=4)
        if said:
            return items[after - 1].end, said[-1].end
    return None


# What turns away the thing that stands after it, in a prompt that is not
# plain. A word that only weakens a wish, "maybe", turns nothing away.
_TURNS_AWAY = TURNS | WORDS_THAT_TURN_AWAY | frozenset({"anywhere but", "a long way"})
# What may stand between such a word and the thing: what leads in to a place,
# a home or a number, and says nothing of whether it is wanted.
_LEADS_IN = frozenset(
    word
    for phrase in (
        *(NEAR_TO | TO_A_PLACE | EXPECTS_A_NAME | GOES_TO | REACHES | CAPS | MINUTES),
        *(TO_DO.words | WISH.words | _BEFORE_A_NAME),
    )
    for word in phrase.split()
) - {"not"}
_FURTHEST_BACK = 8
# What may say, in a prompt that is not plain, that a thing is wanted less or not at
# all, or that it troubles a person, wherever it stands in the clause of the thing.
_MAY_ASK_FOR_FEWER = (
    _TURNS_AWAY
    | TAKES_OFF
    | TAKES_OFF_AFTER
    | TURNS_DOWN
    | TURNS_DOWN_AFTER
    | TROUBLES
    | PHRASES_OF_DOUBT
    | frozenset({"too many", "too much"})
)
_BUT = frozenset({"but"})


def _begins_anew(items: Sequence[Item], at: int) -> bool:
    """Whether "but" stands here and begins something new, as it does not in "anything but"."""
    if not _is_word(items[at], _BUT):
        return False
    return at == 0 or not _phrase_at(items, at - 1, _MAY_ASK_FOR_FEWER, longest=2)


def may_ask_for_fewer(items: Sequence[Item], at: int) -> bool:
    """Whether a word that turns stands in the clause of a thing, before it or after it.

    It is asked of a thing that counts who lives somewhere: beside such a word
    the person may be asking for fewer of a group of people. Before the thing,
    a clause runs back as far as a mark or "but", because a turn may carry
    over a word that joins: "no pubs or families". After it, a clause runs as
    far as a mark or a word that joins, which begins something else: "young
    people and no pubs".
    """
    first = at
    while first > 0 and not items[first].apart and not _begins_anew(items, first - 1):
        first -= 1
    last = at + 1
    while last < len(items) and not items[last].apart and not _is_word(items[last], JOINS.words):
        last += 1
    clause = items[first:last]
    return any(
        _phrase_at(clause, on, _MAY_ASK_FOR_FEWER, longest=4)
        for on in range(len(clause))
        if on != at - first
    )


def _turned_away(items: Sequence[Item], at: int) -> bool:
    """Whether a thing stands after a word that turns it away: "I don't rent".

    A choice that has one direction, to set a tenure or to add a journey,
    would there be the opposite of what was said. So it is not offered. The
    words that lead in to the thing are passed over, "I don't want to be
    near", as far as a mark.
    """
    least = max(at - _FURTHEST_BACK, 0)
    # What says near is passed over whole, whatever word it holds: "walking distance
    # to" holds a word for what is far, and "not far from" a word that turns.
    near = _phrase_before(items, _before_the_article(items, at), NEAR_TO)
    if near:
        at = items.index(near[0])
    while at > least and not items[at].apart:
        before = items[at - 1]
        led = _is_word(before, _LEADS_IN) or (before.what is Is.NUMBER and not before.money)
        if _after(items, at, _TURNS_AWAY) or not led:
            break
        at -= 1
    return _after(items, at, _TURNS_AWAY) and not _ends_a_visit(items, at)


def _ends_a_visit(items: Sequence[Item], at: int) -> bool:
    """Whether the words straight before an item are the last of the words for a visit.

    "A weekend away near Pellam Cross": "away" is part of what the visit is
    called, and turns nothing away.
    """
    least = max(at - _FURTHEST_BACK, 0)
    return any(start + len(visit_at(items, start)) == at for start in range(least, at))


# What says near, or says the most a number may be, and is no wish to stay away though it
# holds a word for far or for more: "not far from", "within walking distance", "no more than".
_NO_WISH_TO_STAY_AWAY = NEAR_TO | NEARBY.words | NOT_FAR | CAPS_FIRMLY
# The speaker's own words for a journey, which say whose it is whoever else is named:
# "my boss and I work at".
_OWN_JOURNEY = EXPECTS_A_NAME | GOES_TO | REACHES | AT_WORK


def _turned_round(items: Sequence[Item], at: int) -> bool:
    """Whether a word that turns stands before the words at `at`, anywhere in their clause.

    "Can't be more than 45 minutes" is the most a journey may take, and "I
    don't want to move far" is a wish to stay near. Where it is read too
    widely, "I don't like pubs and want to be far from", nothing is lost: a
    place that stands after a word for far is still turned away by it, and
    no journey to it is offered.
    """
    while at > 0 and not items[at].apart:
        at -= 1
        if _is_word(items[at], TURNS_ROUND):
            return True
    return False


def _is_minutes(items: Sequence[Item], at: int) -> bool:
    """Whether a number is one of minutes: by how it is typed, or by the word after it."""
    item = items[at]
    if item.what is not Is.NUMBER or item.money or item.unit in ("bed", "month"):
        return False
    after = items[at + 1] if at + 1 < len(items) else None
    return item.unit == "min" or _is_word(after, MINUTES)


def _a_least(items: Sequence[Item], at: int, size: int) -> bool:
    """Whether the words of a least, which stand at `at`, stand against a number of minutes.

    Straight before the number, "at least 30 minutes", or straight after
    what it is a number of, "30 minutes or more". And where they end their
    clause, after a number of minutes that it holds: "30 minutes from Pellam
    Exchange at least".
    """
    after = at + size
    if after < len(items) and _is_minutes(items, after):
        return True
    before = at - 1
    if before >= 0 and _is_word(items[before], MINUTES):
        before -= 1
    if before >= 0 and _is_minutes(items, before):
        return True
    ends = after == len(items) or items[after].apart
    first = at
    while first > 0 and not items[first].apart:
        first -= 1
    return ends and any(_is_minutes(items, on) for on in range(first, at))


def _stays_away(items: Sequence[Item]) -> bool:
    """Whether the words of a sentence ask to be kept away from a place that it names.

    By a word for far, wherever it stands: "far from", "30 minutes away",
    "and nowhere near it". And by a least, against a number of minutes: "at
    least 30 minutes from". What says near is passed over, whatever word it
    holds: "not far from", "no more than 30 minutes". So is a word for far
    or for a least that is turned round: "can't be more than 45 minutes" is
    the most a journey may take. Burro cannot rank on being far from a
    place, so a journey to it is never offered from such a sentence: it
    would rank the person by how near they are.
    """
    at = 0
    while at < len(items):
        # "A weekend away" is a visit, and keeps nobody away from anywhere.
        near = visit_at(items, at) or _phrase_at(items, at, _NO_WISH_TO_STAY_AWAY, longest=4)
        if near:
            at += len(near)
            continue
        least = _phrase_at(items, at, AT_LEAST)
        far = _phrase_at(items, at, STAYS_AWAY)
        if not far and not (least and _a_least(items, at, len(least))):
            at += 1
        elif not _turned_round(items, at):
            return True
        else:
            # What is turned round is turned with the words for far that run on from it:
            # "can't be far away from" says near.
            at += len(far or least)
            while at < len(items) and not items[at].apart and _phrase_at(items, at, STAYS_AWAY):
                at += 1
    return False


def _may_be_anothers(items: Sequence[Item], at: int) -> bool:
    """Whether a place is named as somebody else's, or as one that was left.

    "My ex lives at", "his mother is in", "we moved from". It is somebody
    else's where the words before it name somebody who is not the speaker.
    Two things make it a place to reach all the same. The speaker's own words
    for a journey, straight before the name: "my boss and I work at". And one
    of the household, where no word says that they live there: "my partner
    works at", "I work at one place and my partner at another". Where one of
    the household lives, "my partner lives at", is no place that the words say
    must be reached. "She" and "he" are nobody the words name, so "she's at"
    is offered and not taken. A place that nobody is named with is read as it
    was.
    """
    if _after(items, at, _OWN_JOURNEY):
        return False
    first = at
    while first > 0 and not items[first].apart:
        first -= 1
    before = items[first:at]

    def holds(phrases: frozenset[str]) -> bool:
        return any(_phrase_at(before, on, phrases) for on in range(len(before)))

    if holds(LEFT_BEHIND):
        return True
    return holds(SOMEBODY_ELSE) and (not holds(OF_THE_HOUSEHOLD) or holds(LIVES_THERE))


# What leads in to where somebody is, or to where a person stays: "lives in", "a hotel in",
# "staying at", "is by".
_SAYS_WHERE = frozenset({"in", "at", "by", "around", "near", "to"})
# What may stand between somebody who is named and where they are said to be: who they
# are, and that they are there. "My mother lives in", "his sister is at", "my partner works
# in". After any other word they are not said to be there: "people keep telling me to look
# at" is advice about an area.
_IS_THERE = (
    LIVES_THERE
    | frozenset({"is", "are", "works", "work", "working", "based", "goes", "go", "and"})
    | frozenset(word for phrase in SOMEBODY_ELSE for word in phrase.split())
)


def _somebody_is_there(items: Sequence[Item], first: int, at: int) -> bool:
    """Whether the words before a name, from `first`, say that somebody else is where it is."""
    before = items[first:at]
    named = [on for on in range(len(before)) if _phrase_at(before, on, SOMEBODY_ELSE)]
    if not named or not _after(items, at, _SAYS_WHERE):
        return False
    led_in = _before_the_article(items, at) - 1
    between = items[first + named[-1] : led_in]
    return all(_is_word(item, _IS_THERE) for item in between)


def _turned_away_after(items: Sequence[Item], at: int) -> bool:
    """Whether what follows a name, in its sentence, turns away what was said of it.

    "My boss lives in Tallowgate so I'd rather not". The word that turns is
    said of the place where nothing that can be wished stands after it:
    "and I don't want pubs" turns the pubs away, and not the place.
    """
    for on in range(at + 1, len(items)):
        if _phrase_at(items, on, _TURNS_AWAY):
            after = items[on + 1 :]
            return not any(item.what in (Is.THING, Is.NAME, Is.NUMBER) for item in after)
    return False


def _expects_a_place(items: Sequence[Item], at: int) -> bool:
    """Whether the words straight before a name expect a place to reach: "I work at", "1h to".

    A cue, side by side with the name or with its article, or a time where
    the time of a journey stands. An area is no place to reach, so the name
    of one is no rule for the area there: "30 minutes to Pellam" says nothing
    of where to look.
    """
    led_in = _before_the_article(items, at)
    return bool(_phrase_before(items, led_in, _CUES)) or _time_stands_before(items, at)


def _is_no_rule(items: Sequence[Item], at: int) -> bool:
    """Whether the words before the name of an area say what no rule for the area means.

    That somebody else is there, "my mother lives in", "visiting my mother
    in". That a person wants to be near it, or to reach it: "close to",
    "near", "I work at", "30 minutes to". Or that they stay there or visit:
    "I want to stay in", "a hotel in", "staying with friends in", "visiting".
    Each says where something is, and neither that Burro should look only
    there nor that it should leave the area out: a client that takes what is
    offered looked only there, and left every other area out on a guess.

    The words that make a rule make it all the same, "only in", "not in", and
    so does what turns the place away after it: "my boss lives in Tallowgate
    so I'd rather not". So does a name that nothing leads in to where
    somebody is: "my mate reckons Pellam Cross is nice".
    """
    if _after(items, at, ONLY_IN | NOT_IN) or _turned_away(items, at):
        return False
    if _turned_away_after(items, at):
        return False
    if _after(items, at, NEAR_TO) or _expects_a_place(items, at):
        return True
    first = at
    while first > 0 and not items[first].apart:
        first -= 1
    stays = any(
        visit_at(items, on) or _phrase_at(items, on, STAYS, longest=2) for on in range(first, at)
    )
    if stays and (_after(items, at, _SAYS_WHERE) or _ends_a_visit(items, at)):
        return True
    return _somebody_is_there(items, first, at)


# The words that say a journey, whatever place is named after them. They are
# listened for only where the release names no place, so that a person is told
# that it holds no journey: where it names places, a journey is noticed by
# the name of its place.
_SAYS_A_JOURNEY = EXPECTS_A_NAME | GOES_TO | A_JOURNEY | frozenset({"commuting"})


def _phrase_at(
    items: Sequence[Item], at: int, phrases: frozenset[str], longest: int = 3
) -> list[Item]:
    """The longest of some phrases that the words spell from `at`, side by side."""
    for size in range(longest, 0, -1):
        run = list(items[at : at + size])
        together = len(run) == size and not any(item.apart for item in run[1:])
        words = together and all(item.what is Is.WORD for item in run)
        if words and " ".join(item.text for item in run) in phrases:
            return run
    # Typed with a hyphen, it is a phrase only as a whole: "semi-detached".
    one = items[at] if at < len(items) else None
    if one is not None and one.what is Is.WORD and "-" in one.text and one.bare in phrases:
        return [one]
    return []


def _before_the_article(items: Sequence[Item], at: int) -> int:
    """Where a name begins with the article that stands before it: "the Clinkers"."""
    while at > 0 and _is_word(items[at - 1], _BEFORE_A_NAME) and not items[at].apart:
        at -= 1
    return at


def _phrase_before(
    items: Sequence[Item], at: int, phrases: frozenset[str], longest: int = 4
) -> list[Item]:
    """The longest of some phrases that the words spell up to `at`, side by side with it."""
    if at >= len(items) or items[at].apart:
        return []
    for size in range(min(longest, at), 0, -1):
        said = _phrase_at(items, at - size, phrases, longest=size)
        if len(said) == size:
            return said
    return []


# A word that names a way of travelling, whichever way: "walk", "bike", "tube", "ride".
_NAMES_A_WAY = frozenset(
    word
    for phrase in (*MODES, *(way for way, by in GOES.items() if by is not ModeChoice.UNCHANGED))
    for word in phrase.split()
) - {"by", "on", "public"}
# What may stand straight before a way that is named, as against one that is gone: "a 20
# minute ride to", "the walk to", "a short bike ride to", "I bike to", "by bike to". After
# any other word nobody can say what the ride is on, "a bus ride to", or what is said of it.
_BEFORE_A_WAY = (
    _BEFORE_A_NAME
    | SPEAKER.words
    | MINUTES
    | {"by", "short", "shorter", "quick", "easy", "brisk", "brief", "gentle", "little"}
    | {"nice", "nicer", "lovely", "pleasant", "decent", "reasonable", "manageable"}
)
# The speaker's own wish, which may stand before "to walk to": "I want to", "looking to".
_WISHES_TO = frozenset(
    (wish.removesuffix(" to")).split()[-1]
    for wish in WISH.words
    if wish.split()[-1] not in ("for", "about", "after")
)
# What joins two ways, so that neither is the way: "walk or cycle to", "by bike and train".
_SETS_BESIDE = JOINS.words | {"nor", "than"}
# What may follow a way that is said after the name of a place: how long, and courtesy.
_AFTER_A_WAY = CAPS | CAPS_FIRMLY | COURTESY.words | {"in", "max", "maximum", "tops"}
# What says that a journey would suit, and nothing against how it is made. It is read
# after the place only where nothing follows it: "would suit my ex" says whose it is.
_WOULD_SUIT = frozenset(
    {
        *("would suit", "would suit me", "would suit us", "suits me", "suits us", "would do"),
        *("would be ideal", "would be great", "would be good", "would be perfect"),
        *("would be nice", "would be fine", "is fine", "is ideal", "is ok", "is okay"),
        *("works", "works for me", "works for us", "if possible", "ideally", "preferably"),
        *("is a must", "is essential", "is important", "is key", "is vital", "matters"),
    }
)
# How often or how surely a journey is made, which may stand between who makes it and the
# words that say how: "I usually cycle to", "ideally we walk to".
_SAID_OF_GOING = frozenset(
    {
        *("ideally", "preferably", "hopefully", "maybe", "perhaps", "probably", "possibly"),
        *("usually", "normally", "mostly", "often", "always", "currently", "already"),
        *("sometimes", "only", "just", "still", "both", "rather"),
        *("can", "could", "must", "may", "might", "will", "would", "should", "do"),
    }
)
# The words that open what says somebody goes on foot, and do not say who: "can walk to".
_SOMEBODY_GOES = frozenset({"can", "able"})
# What may stand between a word that joins two ways and the second of them: "a walk or a
# short cycle to", "I walk or else I cycle to", "a 20 minute walk or a 10 minute cycle to".
_LEADS_IN_TO_A_WAY = (
    _SETS_BESIDE
    | SPEAKER.words
    | MINUTES
    | {"a", "an", "the", "else", "then", "short", "quick", "easy"}
)


def _beside(items: Sequence[Item], at: int) -> Item | None:
    """The item at `at`, where it stands in the sentence, or nothing where it does not."""
    return items[at] if 0 <= at < len(items) else None


def _names_a_way(items: Sequence[Item], at: int) -> bool:
    """Whether the words at an item name a way of travelling, one Burro holds or not."""
    item = _beside(items, at)
    if item is None:
        return False
    if item.unmet is UnmetCategory.DRIVING or _phrase_at(items, at, MODES):
        return True
    return any(word in _NAMES_A_WAY for word in (item.bare or item.text).split())


def _set_beside_another(items: Sequence[Item], first: int) -> bool:
    """Whether the way at `first` is the second of two that a word joins: "walk or cycle to".

    The word that joins stands before it, with nothing between them but what
    leads in to a way, "a walk or a short cycle to", and a way stands before
    the word that joins. Nobody can say which of the two is meant.
    """
    at, joined = first - 1, False
    while at >= 0 and not items[at + 1].apart:
        item = items[at]
        counted = item.what is Is.NUMBER and not item.money
        if not (counted or _is_word(item, _LEADS_IN_TO_A_WAY)):
            break
        joined = joined or _is_word(item, _SETS_BESIDE)
        at -= 1
    return joined and at >= 0 and not items[at + 1].apart and _names_a_way(items, at)


# No further than this before a way does a word that turns stand, and turn it.
_TURNS_A_WAY_FROM = 3
# What holds a word of doubt and casts none on a way: the most a journey may take, and how
# surely the speaker goes. "No more than a 20 minute walk to", "I could walk to".
_NOT_IN_DOUBT = CAPS | CAPS_FIRMLY | frozenset({"could", "should", "would"})


def _is_turned(items: Sequence[Item], first: int) -> bool:
    """Whether a word that turns stands before a way, and turns it: "not by bike to".

    It turns the way as it would turn the place, with nothing between the
    two but what leads in to a journey, or it stands a word or two before
    the way: "I can no longer walk to". A word that turns something else in
    the clause turns no way: "I don't need a station but I want to be within
    a 25 minute ride of". The words that say the most a journey may take
    hold such a word and turn nothing: "no more than an hour on foot to".
    """
    at = first
    while at > 0 and not items[at].apart:
        if _after(items, at, CAPS_FIRMLY):
            # The most the journey may take: what stands before it turns nothing of the way.
            return False
        before = items[at - 1]
        if _after(items, at, _TURNS_AWAY):
            return True
        led = _is_word(before, _LEADS_IN) or (before.what is Is.NUMBER and not before.money)
        if not led:
            break
        at -= 1
    for back in range(first - 1, max(first - 1 - _TURNS_A_WAY_FROM, -1), -1):
        if items[back + 1].apart:
            break
        if _is_word(items[back], TURNS_ROUND) and not _phrase_at(items, back, CAPS_FIRMLY):
            return True
        # Words of doubt may turn a way as they may turn a wish: "anything but", "sick of".
        if _after(items, back + 1, SIGNS_OF_DOUBT) and not _after(items, back + 1, _NOT_IN_DOUBT):
            return True
    return False


def _may_go(items: Sequence[Item], first: int, *, somebody: bool = False) -> bool:
    """Whether the words that say a journey is made, from `first`, may say how it is made.

    "I cycle to", "walking distance to", "can walk to". After "to" they
    are what somebody wishes, is able or is loth to do, and only the
    speaker's own wish is one the reader knows: "I want to walk to" is a
    walk, and "unable to walk to" is not. After a word that joins, where a
    way stands before it, they are one of two ways: "walk or cycle to".

    Where the words say that `somebody` goes, "walk to", "can cycle to", who
    goes stands before them, and only the speaker is one the reader knows:
    "my ex can walk to" and "the kids walk to" are no walk of the speaker's.
    The words that say where a home stands, "walking distance to", "a short
    walk from", are said of the home whoever is named before them.
    """
    before = _beside(items, first - 1)
    if _set_beside_another(items, first) or _is_turned(items, first):
        return False
    if before is None or items[first].apart:
        return True
    if _is_word(before, frozenset({"to"})):
        return not items[first - 1].apart and _is_word(_beside(items, first - 2), _WISHES_TO)
    if not somebody:
        return True
    if _may_name_a_way(items, first):
        # The words name the journey as well as say that it is made: "a short walk to".
        return True
    # Past how often or how surely the journey is made, to who makes it.
    who = first - 1
    while who > 0 and not items[who].apart and _is_word(items[who], _SAID_OF_GOING):
        who -= 1
    goes = items[who]
    if _is_word(goes, _SAID_OF_GOING):
        # Nothing but how it is made stands before it, as far as a mark.
        return True
    return _is_word(goes, SPEAKER.words | JOINS.words)


def _may_name_a_way(items: Sequence[Item], first: int) -> bool:
    """Whether a way that is named before "to", from `first`, is the way of the journey.

    "A 20 minute walk to", "a short bike ride to". A ride is a bike ride
    after a time, an article or nothing, and "a bus ride to" is none: the
    word before it says what the ride is on. It is so of every way that is
    named, since no list of what a person may ride is ever complete.
    """
    before = _beside(items, first - 1)
    if _set_beside_another(items, first) or _is_turned(items, first):
        return False
    if before is None or items[first].apart:
        return True
    if before.what is Is.NUMBER:
        return not before.money
    return _is_word(before, _BEFORE_A_WAY)


def _nothing_more(items: Sequence[Item], after: int) -> bool:
    """Whether nothing is said of the way of a journey, from the item at `after`.

    "20 minutes to Pellam Cross on foot", and then a mark, how long, or
    another wish. "On foot is impossible" says more of the way, and "by bike
    or on foot" sets another beside it. That the journey would suit says
    nothing against the way, where nothing follows it: "a 25 minute walk to
    Pellam Cross would suit".
    """
    following = _beside(items, after)
    if following is None or following.apart or following.what is Is.NUMBER:
        return True
    if _is_word(following, _SETS_BESIDE):
        return not _names_a_way(items, after + 1)
    suits = _phrase_at(items, after, _WOULD_SUIT)
    if suits:
        ends = _beside(items, after + len(suits))
        return ends is None or ends.apart
    return _is_word(following, _AFTER_A_WAY)


def _way_beside(items: Sequence[Item], at: int) -> tuple[ModeChoice, list[_Span]]:
    """How the journey to the place at `at` is travelled, where the words beside it say.

    A journey that the words make a walk is a walk. In a sentence the grammar
    does not make, the way is read only where the grammar itself would read
    it, in the words it lists: straight before the name, "I cycle to",
    "walking distance to", between the minutes and the name, "a 25 minute
    walk to", and straight after the name, "on foot". A way that is said of
    something else in the sentence is not the way to the place: "and a park I
    can walk to". Where the words beside the place say two ways nobody can
    say which is meant, and none is taken. It gives where the words stand
    with the way, for the offer to rest on.

    The grammar reads a way in a sentence it has made the whole of. Here the
    words beside the way may be any, so the way is read only where what
    stands straight beside it lets it be one: `_may_go`, `_may_name_a_way`
    and `_nothing_more`. "A bus ride to" was a journey by bike, "unable to
    walk to" a walk, and "walk or cycle to" a journey by bike, and one press
    took each.
    """
    found: list[tuple[ModeChoice, _Span]] = []
    name = _before_the_article(items, at)
    goes = _phrase_before(items, name, GOES_TO)
    if goes and _may_go(items, items.index(goes[0]), somebody=True):
        found.append((GOES[goes[0].text], (goes[0].start, goes[-1].end)))
    near = _phrase_before(items, name, NEAR_TO)
    if near and says_a_walk(near):
        # "Can walk to" says that somebody can, and "I can walk to" says who.
        somebody = near[0].text in _SOMEBODY_GOES
        if _may_go(items, items.index(near[0]), somebody=somebody):
            found.append((ModeChoice.WALK, (near[0].start, near[-1].end)))
    to = _to_a_place(items, at)
    if to is not None:
        first, way = _way_to(items, to)
        if way is not ModeChoice.UNCHANGED and _may_name_a_way(items, first):
            found.append((way, (items[first].start, items[to - 1].end)))
    after = at + 1
    said = _phrase_at(items, after, MODES) if after < len(items) and not items[after].apart else []
    if not _nothing_more(items, after + len(said)):
        # More is said of the way, or another is set beside it: neither is the way. What
        # follows the place may say that the way before it cannot be gone: "a walk to
        # Pellam Cross is impossible".
        return ModeChoice.UNCHANGED, []
    if said:
        by = " ".join(item.text for item in said)
        mode = (
            ModeChoice.CYCLE if by in CYCLED else ModeChoice.WALK if by in WALKED else ModeChoice.PT
        )
        found.append((mode, (said[0].start, said[-1].end)))
    ways = {way for way, _ in found}
    if len(ways) != 1:
        return ModeChoice.UNCHANGED, []
    return ways.pop(), [span for _, span in found]


# --- The time of a journey, wherever the words give it ------------------------------------
#
# A time was read only where it stood straight before its place: "40 minutes to". With a
# word or two between them, "40 minutes or so to", "35 minutes on the tube to", and
# wherever it stood after the place, "Cindermoor Works within 40 minutes", the minutes
# were dropped, and the journey was offered at the usual 45 with a sentence that said the
# person gave none. So every time of a prompt that is not plain is read where it stands,
# with what is said of it, and is given to the journey the words give it to. Where the
# reader cannot tell which journey that is, or what the time is, it says so.

# What says after a word that joins that the time before it is more than was read: "an
# hour and a bit", "40 minutes and a half".
_MORE_OF_A_TIME = frozenset(
    {"a bit", "bit", "a half", "half", "a quarter", "a little", "more", "change", "some"}
)
# What may close a clause after a time and says nothing more of it: "in under 40 minutes
# though", "40 minutes too".
_CLOSES_A_TIME = AT_THE_END | frozenset({"though", "ideally", "preferably", "hopefully"})
# What leads a time in, after the place it is the time of: "Cindermoor Works in 40 minutes".
_IN = frozenset({"in"})
_A_OR_AN = frozenset({"a", "an"})
# Where the speaker works, after "to", "from" or "of": "within 40 minutes of work". The time
# is of the journey there, whichever place the prompt names for it. So is what stands for a
# place, or for who is there, that was named before: "within half an hour of them".
_THE_WORKPLACE = frozenset({"work", "office", "job"})
_STANDS_FOR_A_PLACE = frozenset({"there", "it", "them", "him", "her"})
# What puts a time in doubt, before it in its clause: a word that turns it round, and a word
# that says it is over. "Never 40 minutes", "it was 90 minutes".
_PUTS_A_TIME_IN_DOUBT = TURNS_ROUND | frozenset({"was", "were", "did", "had", "used"})
# What a person may put before a time that says nothing of it, and nothing of what it is
# the time of. The reader knows none of them anywhere else.
_FILLS = frozenset(
    {
        *("honestly", "basically", "actually", "frankly", "realistically", "roughly"),
        *("approximately", "tbh", "say", "well"),
    }
)
# What may stand before a time in its clause, and says nothing of what the time is the time
# of: a word the grammar places, a word of doubt, how surely a thing is wished, and what
# says nothing at all. After any other word the time is said of what that word names.
_LEADS_IN_TO_A_TIME = _FILLS | frozenset(
    word
    for phrase in (*KNOWN_WORDS, *WORDS_OF_DOUBT, *PHRASES_OF_DOUBT, *_SAID_OF_GOING)
    for word in phrase.split()
)
# A journey, by what it is called, where it is what a time is said of: "the commute should
# be under 40 minutes", "neither journey to be more than 40 minutes".
_A_JOURNEY_BY_NAME = A_JOURNEY | frozenset({"commutes", "commuting", "journeys"})
# The units of what is measured as a distance or as a time to walk.
_AT_A_DISTANCE = frozenset({"m", "min"})
# No further than this after its number is anything that is said of a time read.
_FURTHEST_SAID = 8


class _Time(NamedTuple):
    """A length of time as it stands in a sentence, with what is said of it."""

    # Where its words begin among the items, and the item after the last of them.
    first: int
    last: int
    # Its minutes, where they are minutes a journey may take, and nothing where not.
    minutes: int
    firm: bool
    # The shorter of a range of minutes, of which `minutes` is the longer.
    at_least: int
    # How the journey is made, where the words of the time say so: "35 minutes on the tube".
    mode: ModeChoice
    # It is said of a journey by that word, which makes it the time of each journey of the
    # prompt: "a 40 minute commute", "within 40 minutes of work".
    of_a_journey: bool
    # Nothing puts it in doubt: no word turns it or says it is over, it is no least, and
    # nothing more is said of it that the reader does not read.
    read: bool
    # The place it is said of, by where the name stands among the items. Nothing where it
    # stands apart from every place.
    of: int | None
    # It stands before the place it is said of, and its words run on to the name: "40
    # minutes or so to". Otherwise it follows the place in its clause: "within 40 minutes".
    leads: bool


class _Said(NamedTuple):
    """What is said of a time after its number, as far as the reader reads it."""

    # The item after the last of its words.
    last: int
    firm: bool
    least: bool
    mode: ModeChoice
    of_a_journey: bool
    # The journey is one by car, which is none that Burro holds.
    by_car: bool


def _spelt_with_a_thing(
    items: Sequence[Item], at: int, phrases: frozenset[str], longest: int = 3
) -> list[Item]:
    """The longest of some phrases that the items spell from `at`, side by side.

    A phrase of the lexicon may be part of it: "the tube" is one, and "on the
    tube" is how a journey is made.
    """
    for size in range(longest, 0, -1):
        run = list(items[at : at + size])
        if len(run) != size or any(item.apart for item in run[1:]):
            continue
        words = all(item.what in (Is.WORD, Is.THING) for item in run)
        if words and " ".join(item.text for item in run) in phrases:
            return run
    return []


def _way_at(items: Sequence[Item], at: int) -> tuple[list[Item], ModeChoice]:
    """How a journey is made, where the words say so from `at`, and which way that is.

    "By bike", "on foot", "on the tube", "bus ride", and the words that name
    the journey itself: "walk", "cycle", "commute". A word for a journey
    names no way.
    """
    said = _spelt_with_a_thing(items, at, _BY_A_WAY | ON_TRANSPORT)
    if said:
        by = " ".join(item.text for item in said)
        if by in CYCLED:
            return said, ModeChoice.CYCLE
        return said, ModeChoice.WALK if by in WALKED else ModeChoice.PT
    said = _phrase_at(items, at, _A_WAY_TO_GO, longest=2)
    named = " ".join(item.text for item in said)
    return said, GOES.get(named, ModeChoice.UNCHANGED)


def _said_after(items: Sequence[Item], after: int) -> _Said:
    """What is said of a time after its number and the word for what it is a number of.

    How exact it is, that it is the most or the least, and how the journey
    is made, side by side and in any order: "40 minutes or so", "40 minutes
    max by bike", "35 minutes on the tube". Of two ways that a word joins
    neither is the way, "20 minutes by bus or on foot", and the time is as it
    was said.
    """
    firm = least = of_a_journey = by_car = False
    mode, ways = ModeChoice.UNCHANGED, 0
    last = after
    while last < len(items) and not items[last].apart and last - after < _FURTHEST_SAID:
        if items[last].unmet is UnmetCategory.DRIVING:
            by_car, last = True, last + 1
            continue
        if _is_word(items[last], _AWAY):
            # "40 minutes away" is how far off the place is. Where nothing turns it round
            # it keeps the place at a distance, and no journey is offered for its sentence.
            last += 1
            continue
        said = _phrase_at(items, last, LEAVES_A_TIME_AS_IT_IS)
        most = [] if said else _phrase_at(items, last, THE_MOST_AFTER, longest=4)
        more = [] if said or most else _phrase_at(items, last, AT_LEAST)
        way, by = ([], ModeChoice.UNCHANGED) if said or most or more else _way_at(items, last)
        found = said or most or more or way
        if not found:
            joins = _is_word(items[last], _SETS_BESIDE) and ways > 0
            other = _way_at(items, last + 1)[0] if joins else []
            if not other or items[last + 1].apart:
                break
            # The second of two ways that a word joins: neither is the way.
            ways, mode, last = ways + 1, ModeChoice.UNCHANGED, last + 1 + len(other)
            continue
        firm = firm or " ".join(item.text for item in most) in FIRM_OF_MINUTES
        least = least or bool(more)
        if way and by is ModeChoice.UNCHANGED:
            of_a_journey = True
        elif way and not by_car:
            ways, mode = ways + 1, by if ways == 0 else ModeChoice.UNCHANGED
        last += len(found)
    return _Said(last, firm, least, mode, of_a_journey, by_car)


def _ends_as_it_was_read(items: Sequence[Item], after: int) -> bool:
    """Whether what stands straight after the words of a time leaves it the time that was read.

    Nothing, a mark, what leads on to a place, a courtesy, that it would
    suit, or a word that joins it to something else. After any other word
    more is said of the time than the reader reads: "40 minutes there and
    back", "an hour n a half", "40 minutes 30 seconds". So it is after a word
    that joins, where what follows is more of the time, or nothing: "an hour
    and a bit", "40 minutes plus to". And a number that stands where the
    minutes of a longer time stand, whatever mark parts the two, says that
    the time before it was not read whole: "1 hour; 15".
    """
    following = items[after] if after < len(items) else None
    if following is None:
        return True
    if following.what is Is.NUMBER and part_of_a_longer_time(items, after):
        return False
    if following.apart:
        return True
    if _is_word(following, TO_A_PLACE | COURTESY.words) or _phrase_at(items, after, REACHES):
        return True
    closes = _phrase_at(items, after, _WOULD_SUIT | _CLOSES_A_TIME)
    if closes:
        ends = _beside(items, after + len(closes))
        return ends is None or ends.apart
    if not _is_word(following, JOINS.words):
        return False
    more = _beside(items, after + 1)
    if more is None or more.apart or _is_word(more, TO_A_PLACE):
        return False
    if more.what is Is.NUMBER and part_of_a_longer_time(items, after + 1):
        return False
    return not _phrase_at(items, after + 1, _MORE_OF_A_TIME, longest=2)


def _where_its_part_begins(items: Sequence[Item], at: int) -> int:
    """Where the part of a sentence that an item stands in begins: after a mark."""
    while at > 0 and not items[at].apart:
        at -= 1
    return at


def _is_some_way_off(item: Item, lexicon: Mapping[str, Target]) -> bool:
    """Whether an item is a thing that is measured as a distance, which a time may be said of."""
    if item.what is not Is.THING:
        return False
    measured = lexicon[item.text].features
    return any(FEATURES[feature_id].unit in _AT_A_DISTANCE for feature_id in measured)


def _stands_after(
    items: Sequence[Item], first: int, lexicon: Mapping[str, Target]
) -> tuple[bool, int | None]:
    """What a time that leads to nothing is said of, by what stands before it.

    Whether it is said of something that is no place to reach, and the place
    it follows where it follows one. In its own part of the sentence, the
    place or the thing that stands nearest before it: "Cindermoor Works
    within 40 minutes", "a gym within 10 minutes". Where it opens its part,
    the thing that the part before it names, where that is measured as a
    distance and the part names no place: "a park, a 10 minute walk".
    """
    begins = _where_its_part_begins(items, first)
    for at in range(first - 1, begins - 1, -1):
        before = items[at]
        if before.what is Is.NAME and before.place:
            return False, at
        if before.what in (Is.THING, Is.NAME):
            return True, None
        if _is_word(before, JOINS.words):
            return False, None
    if begins == 0:
        return False, None
    earlier = items[_where_its_part_begins(items, begins - 1) : begins]
    places = any(item.what is Is.NAME and item.place for item in earlier)
    things = any(_is_some_way_off(item, lexicon) for item in earlier)
    return things and not places, None


def _runs_on_to(items: Sequence[Item], last: int, leads_to: Mapping[int, int]) -> int | None:
    """The place that the words after a time run on to, where the reader does not read them.

    They are said of the time, "40 minutes and a bit to", "40 minutes there
    and back to", or they name the journey, "a 15 minute scooter ride to".
    After any other word the time is said of something else: "12 hour shifts
    close to".
    """
    for at in range(last, min(last + _FURTHEST_HOURS + 1, len(items))):
        if items[at].apart:
            return None
        if at in leads_to:
            between = items[last:at]
            said_of_it = all(
                item.what is Is.NUMBER
                or item.unmet is UnmetCategory.DRIVING
                or _is_word(item, _SAID_OF_A_TIME | MINUTES)
                for item in between
            )
            names_it = bool(between) and _is_word(between[-1], frozenset(GOES))
            return leads_to[at] if said_of_it or names_it else None
    return None


def _caps_before(items: Sequence[Item], at: int) -> tuple[int, list[str]]:
    """Where the words that cap a number begin, and what they say: "within about 30 minutes".

    Past the article of the time, "within a 40 minute walk", and past a word
    for about, which may stand between another that caps and the number.
    """
    before = at
    article = before > 0 and not items[before].apart and _is_word(items[before - 1], _A_OR_AN)
    if article and not items[at].hours:
        before -= 1
    caps: list[str] = []
    while len(caps) < 2:
        capped = _phrase_before(items, before, CAPS | CAPS_FIRMLY | AT_LEAST)
        if not capped:
            break
        caps.insert(0, " ".join(item.text for item in capped))
        before -= len(capped)
        if caps[0] not in _OR_SO:
            break
    return (before if caps else at), caps


class _Before(NamedTuple):
    """What the words before a time say of it, in its clause."""

    # They name something the reader does not know, which the time is then said of.
    of_something: bool
    # A word turns the time round, or says that it is over.
    doubted: bool
    # They say that it is the time of a journey, by that word.
    of_a_journey: bool
    # The one way of travelling they name, where they name one.
    mode: ModeChoice


def _said_before(items: Sequence[Item], first: int, follows: int | None) -> _Before:
    """What is said before a time in its clause, as far back as the place it follows.

    And no further back than a word that joins, or the mark that begins its
    part of the sentence. "The nearest shop is a twenty minute walk" says
    how far the shop is, and the reader knows no shop: after a word it does
    not know, a time is said of what that word names. "It should be under 40
    minutes" and "and would like it under 40 minutes" name nothing.
    """
    begins = _where_its_part_begins(items, first) if follows is None else follows + 1
    joined = [at for at in range(begins, first) if _is_word(items[at], JOINS.words)]
    before = items[joined[-1] + 1 if joined else begins : first]
    known = all(item.what is Is.NUMBER or _is_word(item, _LEADS_IN_TO_A_TIME) for item in before)
    named = [GOES[item.text] for item in before if _is_word(item, frozenset(GOES))]
    ways = set(named) - {ModeChoice.UNCHANGED}
    return _Before(
        of_something=not known,
        doubted=any(_is_word(item, _PUTS_A_TIME_IN_DOUBT) for item in before),
        of_a_journey=any(_is_word(item, _A_JOURNEY_BY_NAME) for item in before),
        mode=ways.pop() if len(ways) == 1 else ModeChoice.UNCHANGED,
    )


def _time_at(
    items: Sequence[Item], at: int, leads_to: Mapping[int, int], lexicon: Mapping[str, Target]
) -> _Time | None:
    """The time whose number stands at `at`, with what is said of it. Nothing where it is none.

    A number of minutes, by how it is typed or by the word after it, and a
    time in hours, which is one. A number with no word for minutes is a time
    only where it follows a place in its clause, "in" or a word that caps
    leads it in, it is a number of minutes that a journey may take, and
    nothing follows it that may say what it is a number of: "Cindermoor
    Works in under 25". Anywhere else it is as often an age or a count: "I'm
    under 40". A number of bedrooms, an amount of money, a number by a
    period, "900 minutes a week", and minutes that lead to a thing, "10
    minutes to a park", are none. Nor is a time that says what kind of thing
    something else is, "45 minute classes", or one that stands apart from
    every place and is beyond what any journey may take: "shops open 24
    hours".

    A time that is said of what the reader does not know is one, and the time
    of no journey: "the nearest shop is a twenty minute walk", "within 30
    minutes of my mum". It may be said of something else, so no journey takes
    it, and a journey that was given no other says that a time was typed.

    `leads_to` holds, for each word that leads in to the name of a place, where
    the name stands, and `lexicon` what each thing of the sentence is.
    """
    number = items[at]
    if number.what is not Is.NUMBER or number.money or number.unit not in ("", "min"):
        return None
    if _bedrooms_at(items, at):
        return None
    after = at + 1
    unit = _beside(items, after)
    named = number.unit == "min"
    if not named and unit is not None and _is_word(unit, MINUTES) and not unit.apart:
        named, after = True, after + 1
    first, caps = _caps_before(items, at)
    if first > 0 and not items[first].apart and _is_word(items[first - 1], _IN):
        first -= 1
    elif not named and not caps:
        return None
    following = _beside(items, after)
    if _phrase_at(items, after, MONTHLY | BY_THE_WEEK | BY_ANOTHER_PERIOD):
        return None
    if following is not None and not following.apart and _names_a_period(following):
        return None
    said = _said_after(items, after)
    last = said.last
    ends = _ends_as_it_was_read(items, last)
    taken = LIMITS.minutes_min <= number.value <= LIMITS.minutes_max
    # A least that a word before it turns round is the most the journey may take: "can't be
    # more than 45 minutes". The word that turns it is then no doubt about the time.
    a_least = any(cap in AT_LEAST for cap in caps)
    turned_round = a_least and _turned_round(items, first)
    least = said.least or (a_least and not turned_round)
    firm = said.firm or any(cap in FIRM_OF_MINUTES for cap in caps) or bool(number.low)
    minutes = number.value if taken and not part_of_a_longer_time(items, at) else 0
    whole = bool(minutes) and ends and not least and not said.by_car

    # What it leads to, where its words run on to the name of a place.
    leads_on = last < len(items) and not items[last].apart and _is_word(items[last], TO_A_PLACE)
    reaches = _phrase_at(items, last, REACHES) if ends else []
    reached = _before_the_name(items, last + len(reaches))
    there = _beside(items, reached)
    side_by_side = not any(item.apart for item in items[last : reached + 1])
    to: int | None = None
    if reaches and side_by_side and there is not None and there.what is Is.NAME and there.place:
        to, last = reached, reached
    elif ends and leads_on and last in leads_to:
        to = leads_to[last]
    elif not ends:
        to = _runs_on_to(items, last, leads_to)
        of_a_kind = unit is not None and unit.text in ("minute", "min") and number.value > 1
        if to is None and of_a_kind and number.unit != "min":
            return None  # it says what kind of thing something is: "45 minute classes"
    worded = said.of_a_journey or bool(reaches)
    # It is said of what the reader does not know: nobody can say which journey it is of.
    unknown = False
    if to is None and ends and leads_on:
        where = _before_the_name(items, last + 1)
        led_to = _beside(items, where)
        if not taken or (led_to is not None and led_to.what is not Is.WORD):
            return None  # it is said of a thing: "10 minutes to a park"
        if _is_word(led_to, _THE_WORKPLACE | _STANDS_FOR_A_PLACE):
            worded, last = True, where + 1
        else:
            unknown = True  # "within 30 minutes of my mum"
    follows: int | None = None
    if to is None:
        of_a_thing, follows = _stands_after(items, first, lexicon)
        if of_a_thing or (follows is None and not taken):
            # Beyond what any journey may take, and said of no place: "24 hours".
            return None
    if not named and (follows is None or not taken or not ends):
        # A number of something else, or of what the words after it name: "in 3 weeks".
        return None
    before = _said_before(items, first, follows)
    if unknown or before.of_something:
        # "The nearest shop is a twenty minute walk", "it takes me 50 minutes to get to". It
        # may be the time of a journey and may be said of something else, so it is the
        # time of none, and stands apart from every place.
        mode = ModeChoice.UNCHANGED
        return _Time(first, last, 0, firm, number.low, mode, False, False, None, False)
    read = whole and (turned_round or not before.doubted)
    ways = {said.mode, before.mode} - {ModeChoice.UNCHANGED}
    return _Time(
        first,
        last,
        minutes if read else 0,
        firm,
        number.low,
        ways.pop() if len(ways) == 1 else ModeChoice.UNCHANGED,
        worded or before.of_a_journey,
        read,
        follows if to is None else to,
        to is not None,
    )


def _times_of(items: Sequence[Item], lexicon: Mapping[str, Target]) -> list[_Time]:
    """Every time of a sentence that may be the time of a journey, in the order they stand."""
    leads_to = {
        to: at
        for at, item in enumerate(items)
        if item.what is Is.NAME and item.place and (to := _to_a_place(items, at)) is not None
    }
    found = (_time_at(items, at, leads_to, lexicon) for at in range(len(items)))
    return [time for time in found if time is not None]


def _where_it_is_led_in(times: Sequence[_Time], at: int) -> int:
    """Where the words that lead the name of a place in begin: the time that runs on to it.

    What caps a time, or says that it is the most, holds words that turn a
    wish away anywhere else: "less than 40 minutes to", "40 minutes or less
    to". They are said of the time, so what turns the place away is asked of
    what stands before them. `times` are the times of the sentence the name
    stands in.
    """
    leads = [time for time in times if time.of == at and time.leads]
    return leads[0].first if len(leads) == 1 and leads[0].read else at


class _Given(NamedTuple):
    """The time of one journey, as the words of the prompt give it."""

    minutes: int = 0
    firm: bool = False
    at_least: int = 0
    mode: ModeChoice = ModeChoice.UNCHANGED
    # Where the words of the time stand.
    spans: tuple[_Span, ...] = ()
    # Its words run on to the name of the place: "40 minutes or so to".
    leads: bool = False
    # What is said where a time was typed and none was taken for the journey. Nothing where
    # one was taken, and where the person gave none.
    could_not: str = ""


_Where = tuple[int, int]
# What the words give a journey that they give no time.
_NO_TIME = _Given()


def _made_the_way(given: _Given, mode: ModeChoice) -> _Given:
    """The time of a journey, held to the way the journey is made.

    A time that is said of one way is no time of a journey that the words
    make another way: of "I cycle to Foxholt Works, 25 minutes on foot" nobody
    can say what the journey by bike takes.
    """
    ways = {given.mode, mode} - {ModeChoice.UNCHANGED}
    return _Given(could_not=TIME_NOT_PLACED) if given.minutes and len(ways) > 1 else given


def _where_named(sentences: Sequence["_Sentence"], made: _Made) -> _Where | None:
    """Where the name of the place of a journey stands, of one that the grammar made."""
    edit = made.edit
    assert isinstance(edit, CommuteEdit)
    for at, sentence in enumerate(sentences):
        for on, item in enumerate(sentence.items):
            named = item.what is Is.NAME and item.place == edit.place_id
            if named and any(start <= item.start and item.end <= end for start, end in made.spans):
                return at, on
    return None


def _times_given(
    sentences: Sequence["_Sentence"],
    journeys: Sequence[_Where],
    used: Sequence[_Span],
    lexicon: Mapping[str, Target],
) -> dict[_Where, _Given]:
    """The time of each journey that was given none, as the words of the prompt give it.

    `journeys` says where the name of each place stands: in which sentence,
    and where among its items. `used` is where the words stand that a journey
    the grammar made rests on, whose times are read already.

    A time that is said of a thing the reader knows is none of these: "a gym
    within 10 minutes". The journey beside it was given no time, and says so.

    A time that leads to a place, or follows it in its clause, is the time of
    the journey to it. A time that stands apart from every place is the time
    of the one journey of the prompt, where the prompt holds one such time.
    With a word for a journey, "a 40 minute commute", it is the time of each,
    as it is in a plain prompt. And it is the time of the one journey of its
    sentence, where the sentence holds one such time. Any other time is one
    the reader cannot give to a journey, and every journey that was given
    none says so.

    A time that was not read, and stands where the time of a journey stands,
    before its place, is never made up for by the usual one: the place is
    offered with nothing to choose. One that follows its place, or stands
    apart from it, may be said of something else: the journey is offered
    with no time, and says that a time was given.
    """

    def span_of(at: int, time: _Time) -> _Span:
        items = sentences[at].items
        return items[time.first].start, items[time.last - 1].end

    def is_read(at: int, time: _Time) -> bool:
        begins, ends = span_of(at, time)
        return any(start <= begins and ends <= end for start, end in used)

    times = [
        (at, time)
        for at, sentence in enumerate(sentences)
        for time in _times_of(sentence.items, lexicon)
        if not is_read(at, time)
    ]
    found: dict[_Where, _Given] = {}

    def give(where: _Where, at: int, time: _Time) -> None:
        if time.read:
            stands = (span_of(at, time),)
            found[where] = _Given(
                time.minutes, time.firm, time.at_least, time.mode, stands, time.leads
            )
        else:
            found[where] = _Given(could_not=TIME_NOT_TAKEN if time.leads else TIME_NOT_PLACED)

    apart: list[tuple[int, _Time]] = []
    for at, time in times:
        where = (at, time.of if time.of is not None else -1)
        if time.of is None:
            apart.append((at, time))
        elif where not in journeys:
            # It is said of a place that no journey is offered to, or whose time was read.
            continue
        elif where in found:
            # Two times beside one place: which is meant is the person's to say.
            before = found[where].leads or found[where].could_not == TIME_NOT_TAKEN
            leads = time.leads or before
            found[where] = _Given(could_not=TIME_NOT_TAKEN if leads else TIME_NOT_PLACED)
        else:
            give(where, at, time)
    free = [where for where in journeys if where not in found]
    given: list[tuple[int, _Time]] = []
    if len(apart) == 1 and (len(free) == 1 or apart[0][1].of_a_journey):
        for where in free:
            give(where, *apart[0])
        given = apart if free else []
    else:
        for at in range(len(sentences)):
            here = [where for where in free if where[0] == at]
            said = [(on, time) for on, time in apart if on == at]
            if len(here) == 1 and len(said) == 1:
                give(here[0], *said[0])
                given += said
    if len(given) < len(apart):
        for where in free:
            found.setdefault(where, _Given(could_not=TIME_NOT_PLACED))
    return found


# What is said of a home that the search cannot hold as it was said. A rent is
# published by the number of bedrooms and a price by the kind of home, so each
# tenure has kinds of home of its own (contract, section 4).
BY_KIND = (
    "Burro knows what homes sell for by kind of home, such as a flat or a terraced house, "
    "and not by the number of bedrooms."
)
BY_BEDROOMS = "Burro knows what homes rent for by the number of bedrooms, and not by kind of home."
TO_RENT_ALONE = (
    "Burro knows what a studio or a room costs to rent, and not what either costs to buy."
)
BY_KIND_OF_HOUSE = (
    "Burro knows what houses sold for by kind of house, so it asks which kind you mean."
)
# What is said of a home, and of an amount, where the search is for somewhere to stay on a
# visit. A visit holds neither, so each is offered with nothing to choose but to leave it
# out, and says why. Decided on 2026-09-26.
NO_HOME_ON_A_VISIT = (
    "A search for somewhere to stay is not a search for a home, so it has no number of "
    "bedrooms and no kind of home. If you are looking for a home to live in, say whether "
    "you are renting or buying."
)
NO_BUDGET_ON_A_VISIT = (
    "Burro does not know what it costs to stay in an area, so a search for somewhere to "
    "stay has no budget. This means Burro has left this amount out of your search."
)
# What is said of a wish to move the budget, "somewhere cheaper", where the search is for
# somewhere to stay. It names no amount, and a visit has no budget for it to move. It was
# answered with nothing at all, which left a person to think it was taken.
NO_STEP_ON_A_VISIT = (
    "Burro does not know what it costs to stay in an area, so a search for somewhere to "
    "stay has no budget to raise or lower. This means Burro has left this out of your "
    "search."
)
# What such a wish is called where it is offered with nothing to choose.
LOWER_BUDGET, HIGHER_BUDGET = "A lower budget", "A higher budget"
# What is said of what homes sold for, where the search is for somewhere to stay. A visit
# weighs none of it, so it is offered with nothing to choose but to leave it out, as an
# amount is. Mended on 2026-09-26.
NO_PRICE_ON_A_VISIT = (
    "What homes sold for says what it costs to buy a home in an area, and not what it costs "
    "to stay there. Because of that, Burro has left it out of your search for somewhere to "
    "stay."
)
# What a search for somewhere to stay is called, wherever it is offered.
VISITING = "Visiting"
# What is said where a house of no kind is taken as a terraced house. That it is the kind
# of house that costs the least in most areas is said only of a release of which it is true.
A_TERRACED_HOUSE = "You did not say what kind of house, so Burro has assumed a terraced house"
THE_LEAST_DEAR = ", which is the kind of house that costs the least in most areas"
ONE_PRESS_AWAY = ". You can choose a semi-detached or a detached house instead."
# The kinds of house a price is held by, in the order they are offered.
KINDS_OF_HOUSE = (SegmentChoice.TERRACED, SegmentChoice.SEMI_DETACHED, SegmentChoice.DETACHED)
# A kind of home that says little of one to rent: most homes that are let are flats.
_A_FLAT = frozenset(word for word, kind in BUY_SEGMENTS.items() if kind is SegmentChoice.FLAT)
_THE = frozenset({"a", "an", "the"})


# What an amount is said to be paid by. A rent is held by the month.
BY_THE_MONTH = "month"
BY_WEEK = "week"
# Any other period: a year, a fortnight, a night. No rule says what it comes to by the month.
BY_NO_MONTH = "other"
_PERIODS = ((BY_THE_MONTH, MONTHLY), (BY_WEEK, BY_THE_WEEK), (BY_NO_MONTH, BY_ANOTHER_PERIOD))
# What says that a number is an amount of money, straight after it: "350 quid a week".
_IN_MONEY = IN_MONEY | THOUSANDS
# What may stand between an amount and the home it is for, and says nothing of how it
# is paid: "£350 for a studio per week", "£350 rent a week".
_SAID_OF_A_HOME = frozenset(
    word
    for phrase in (*A_HOME, *BEDROOMS, *_KINDS_OF_HOME, *RENTS, *_THE, "for", "of", "on")
    for word in phrase.split()
)
# What may stand between the period an amount is paid by and the amount, where the period
# comes first: "weekly rent of £350", "my budget per week is up to £350".
_SAID_OF_PAYING = frozenset(
    word
    for phrase in (*PAYS, *RENTS, *CAPS, *CAPS_FIRMLY, *SPEAKER.words, *_THE, "for", "of", "at")
    for word in phrase.split()
)
# No further than this from an amount is what it is paid by looked for.
_FURTHEST_PERIOD = 6
# What may stand between an amount and a word for a period that the reader does not know
# what to make of: "£350 this week", "£350 per person per week", "£700 every two weeks".
_BEFORE_A_PERIOD = _THE | {"per", "each", "every", "this", "person", "head", "for", "over"}
# After one of these a number is how many of the period: "every 2 weeks", "per 4 weeks",
# "for 6 months".
_HOW_MANY_OF_IT = frozenset({"per", "each", "every", "for", "over"})
# What joins two amounts that are paid by one period: "£350 to £400 a week".
_TO_ANOTHER_AMOUNT = frozenset({"to", "or", "and"})
# What a number stands before to say every so many weeks: "four weekly".
_SO_MANY_WEEKLY = frozenset({"weekly", "wkly"})
# No further than this from where the words of an amount end is such a word looked for.
_FURTHEST_UNKNOWN = 4


class Paid(NamedTuple):
    """What an amount is said to be paid by, and where the words that say so stand."""

    # `BY_THE_MONTH`, `BY_WEEK` or `BY_NO_MONTH`, and nothing where the words say none.
    by: str
    # The first item of the amount with what says how it is paid, and the item after the last.
    first: int
    last: int


def _is_said_of(item: Item, words: frozenset[str]) -> bool:
    """Whether an item is a word, or a word typed with a hyphen, that is made of some words."""
    if item.what is not Is.WORD:
        return False
    return all(word in words for word in (item.bare or item.text).split())


def _bedrooms_at(items: Sequence[Item], at: int) -> bool:
    """Whether a number is one of bedrooms: by how it is typed, or by the word after it."""
    item = items[at]
    if item.what is not Is.NUMBER or item.money:
        return False
    after = items[at + 1] if at + 1 < len(items) else None
    return item.unit == "bed" or (not item.unit and _is_word(after, BEDROOMS))


def _names_a_period(item: Item | None) -> bool:
    """Whether an item is a word for a period but the month, or says whose: "a week's"."""
    if item is None or item.what is not Is.WORD:
        return False
    return item.text.removesuffix("'s") in OF_A_PERIOD or item.bare in OF_A_PERIOD


def _after_a_dash(item: Item) -> bool:
    """Whether a dash, and no other mark, parts an item from the one before it."""
    marks = item.marks.replace(" ", "")
    return bool(marks) and all(mark in DASHES for mark in marks)


def _a_period_follows(items: Sequence[Item], after: int) -> bool:
    """Whether a word for a period stands after an amount in words the reader does not list.

    From `after`, side by side and no further than a few words: past an
    article, "per", "this" and the like, past a number that says how many of
    the period, "every 2 weeks", "four weekly", and past a second amount
    that is joined to the first, "£350 to £400 a week". Any other word ends
    it, so a period that is said of something else is not said of the
    amount: "£1,500 near a weekly market", "£1,500 and a weekly shop", "£1,500
    for a flat 3 days a week". A dash joins two amounts as a word does, "£350
    - £400 a week", and any other mark ends it.
    """
    at = after
    while at < len(items) and at - after < _FURTHEST_UNKNOWN:
        item, before = items[at], items[at - 1]
        dashed = item.what is Is.NUMBER and _after_a_dash(item)
        if item.apart and not dashed:
            break
        following = items[at + 1] if at + 1 < len(items) and not items[at + 1].apart else None
        if _names_a_period(item):
            return True
        numbered = following is not None and following.what is Is.NUMBER
        if item.what is Is.NUMBER:
            # How many of the period, or the second of two amounts.
            led = dashed or _is_word(before, _HOW_MANY_OF_IT | _TO_ANOTHER_AMOUNT)
            passed = led or _is_word(following, _SO_MANY_WEEKLY)
        elif _is_word(item, _TO_ANOTHER_AMOUNT):
            passed = numbered
        else:
            # A word that leads in to a period, or a mark that stands by itself: "£350 / week".
            passed = _is_word(item, _BEFORE_A_PERIOD) or (item.what is Is.ODD and not item.figures)
        if not passed:
            return False
        at += 1
    return False


def _a_period_leads(items: Sequence[Item], back: int) -> bool:
    """Whether a word for a period stands before what is said of paying an amount.

    "Annual rent of £18,000", "a week's rent of £350". It is said of the
    amount only where it opens its clause or follows what is said of paying
    or of a home, as a period the reader lists is: in "3 days a week for
    £1,500" it is said of the days. A period that is named, "a week", is
    read with its article. One that is said of the rent, "annual", "a
    week's", may have an article before it, as "a yearly rent of" has.
    """
    if back <= 0 or items[back].apart or not _names_a_period(items[back - 1]):
        return False
    first = back - 1
    said = items[first].text
    of_the_rent = said.endswith(("ly", "'s")) or said == "annual"
    led = items[first - 1] if first > 0 and not items[first].apart else None
    # How many of the period: "6 months rent of".
    counted = led is not None and led.what is Is.NUMBER and not led.money
    if counted or (_is_word(led, _THE) and not of_the_rent):
        first -= 1
    opens = first == 0 or items[first].apart
    return opens or _is_said_of(items[first - 1], _SAID_OF_PAYING | _SAID_OF_A_HOME)


def paid_by(items: Sequence[Item], at: int) -> Paid:
    """What the amount at `at` is said to be paid by: the month, the week, or another period.

    It is said straight after the amount, "£350 a week", "350 quid per
    week", or after the home it is for, "£350 for a studio per week". Or it
    is said before the amount, with nothing between them but what is said of
    paying: "weekly rent of £350". There it is said of the amount only where
    it opens its clause or follows what is said of paying or of a home: in
    "3 days a week for £1,500" it is said of the days. No further than a
    mark either way. What stands straight after the amount is what it is
    paid by, whatever is said before it: "a weekly shop nearby, £1,500 a
    month".

    Where none of the periods the reader lists is said, and a word for a
    period stands beside the amount all the same, "£350 this week", "£700
    every two weeks", "annual rent of £18,000", the amount is by no month:
    `OF_A_PERIOD` in `vocabulary.py` holds the words.

    An amount by the week was offered as an amount by the month at the same
    figure. It is for whoever offers an amount, and for whoever holds a
    model's reading of one to what the person typed.
    """
    item = items[at]
    if item.unit in (BY_THE_MONTH, BY_WEEK):
        return Paid(item.unit, at, at + 1)

    def said_at(on: int) -> Paid | None:
        """The period that is said from an item that stands side by side with the one before."""
        for by, phrases in _PERIODS:
            said = _phrase_at(items, on, phrases)
            if said:
                return Paid(by, at, on + len(said))
        return None

    def beside(on: int) -> bool:
        return on < len(items) and not items[on].apart and on - at <= _FURTHEST_PERIOD

    after = at + 1
    while beside(after) and _is_word(items[after], _IN_MONEY):
        after += 1
    while beside(after):
        found = said_at(after)
        if found is not None:
            return found
        of_a_home = _is_said_of(items[after], _SAID_OF_A_HOME) or _bedrooms_at(items, after)
        if not of_a_home:
            break
        after += 1
    if _a_period_follows(items, after):
        return Paid(BY_NO_MONTH, at, at + 1)
    back = at
    while back > 0 and not items[back].apart and at - back < _FURTHEST_PERIOD:
        if not _is_said_of(items[back - 1], _SAID_OF_PAYING):
            break
        back -= 1
    if back > 0 and not items[back].apart:
        for by, phrases in _PERIODS:
            for size in (3, 2, 1):
                first = back - size
                if first < 0 or len(_phrase_at(items, first, phrases, longest=size)) != size:
                    continue
                opens = first == 0 or items[first].apart
                if opens or _is_said_of(items[first - 1], _SAID_OF_PAYING | _SAID_OF_A_HOME):
                    return Paid(by, first, at + 1)
    if _a_period_leads(items, back):
        return Paid(BY_NO_MONTH, at, at + 1)
    return Paid("", at, at + 1)


# What may stand straight after the words for a visit, and leaves them a visit: what joins
# two wishes, what leads in to where or when, and courtesy. After any other word the words
# before it are as often said of something else: "visiting my mother", "visiting hours",
# "a hotel job". No list of whom a person may visit is ever complete, so this one is of
# what may follow, and is closed.
_AFTER_A_VISIT = (
    JOINS.words
    | COURTESY.words
    | frozenset({"for", "in", "at", "around", "this", "next", "soon"})
    # What opens a wish of its own: "a hotel somewhere lively".
    | frozenset({"somewhere"})
)
_LEADS_TO = frozenset({"to"})
# The words a phrase for a visit may open with that lead it in themselves: "a trip", "my
# visit", "on holiday", "somewhere to stay". What stands before such a phrase is what is
# done with the visit, "planning a trip", and is no part of what it is called.
_LEADS_ITSELF_IN = _BEFORE_A_NAME | frozenset({"on", "somewhere", "places"})
# The words that say no more of a visit than how much of one it is: "just visiting", "only
# visiting". The reader knows none of them, and none makes the word after it part of
# anything else.
_HOW_MUCH_OF_A_VISIT = frozenset(
    {"just", "only", "simply", "really", "actually", "currently", "mostly", "mainly"}
)
# The speaker, where they are named beside somebody else: "my wife and I need a hotel".
_THE_SPEAKER = frozenset({"i", "we", "me", "us"}) | SPEAKER.words
# The words a night is paid by. Burro holds no price of a stay, so an amount by the night
# is no budget: it is what a place charges, which nothing measures.
_A_NIGHT = frozenset({"night", "nights", "nightly"})


def _leaves_it_a_visit(items: Sequence[Item], after: int) -> bool:
    """Whether what stands straight after the words for a visit leaves them a visit.

    Nothing, a mark, a word that joins or leads in to where or when, the name
    of a place or of an area, "visiting Pellam Cross", a number, or a thing
    the lexicon knows. What says near, before a thing or a place and with
    nothing after it: "a hotel close to the station", "a hotel nearby". After
    "to" a name must follow: "a trip to Pellam Cross" is a visit, and "a trip
    to work" is how the speaker gets there.
    """
    following = _beside(items, after)
    if following is None or following.apart:
        return True
    if following.what in (Is.NAME, Is.NUMBER, Is.THING, Is.UNMET):
        # What is wished of the place, or of the stay: "a hotel parking nearby".
        return True
    if following.what is not Is.WORD:
        return False
    if _is_word(following, _LEADS_TO):
        named = _beside(items, _before_the_name(items, after + 1))
        return named is not None and named.what is Is.NAME and not named.apart
    if following.text in _AFTER_A_VISIT or _phrase_at(items, after, NEAR_TO, longest=4):
        return True
    # What says that it is wanted near closes the words: "need a hotel nearby". With more
    # after it, it is as often said for somebody else: "a hotel nearby for when my parents
    # visit".
    nearby = _phrase_at(items, after, NEARBY.words, longest=4)
    closes = _beside(items, after + len(nearby))
    return bool(nearby) and (closes is None or closes.apart or _is_word(closes, JOINS.words))


def _before_the_name(items: Sequence[Item], at: int) -> int:
    """Where a name stands, past the article that may stand before it: "to the Clinkers"."""
    while at < len(items) and _is_word(items[at], _BEFORE_A_NAME) and not items[at].apart:
        at += 1
    return at


def _somebody_elses_visit(items: Sequence[Item], at: int) -> bool:
    """Whether the words before a visit, in its clause, give it to somebody who is not the speaker.

    "My mum is visiting", "my parents need a hotel", "her hotel". Where the
    speaker is named after them, the visit is the speaker's too: "my wife and
    I need a hotel".
    """
    first = at
    while first > 0 and not items[first].apart:
        first -= 1
    before = items[first:at]
    whose = [on for on in range(len(before)) if _phrase_at(before, on, SOMEBODY_ELSE)]
    if not whose:
        return False
    return not any(_is_word(item, _THE_SPEAKER) for item in before[whose[-1] + 1 :])


def names_a_visit(items: Sequence[Item], at: int) -> list[Item]:
    """The words that say a visit from `at`, where nothing beside them says something else.

    It is for whoever reads a sentence the grammar does not make: the
    grammar places a word for a visit itself, and here any word may stand
    beside one. So the words are a visit only where none of these is so. A
    word that turns stands before them, "no hotels". They stand where a place
    is expected, or is said to be near: "I work at a hotel", "near my hotel".
    The visit is somebody else's: "my mum is visiting". A word the reader
    does not know stands straight before a word for a visit that nothing
    leads in, which may make it part of what that word says, or say that the
    visit is over: "bank holiday", "was visiting". Before "a trip" such a
    word is what is done with the trip: "planning a trip". Or what stands
    straight after them says whom or what is visited, and no kind of search:
    "visiting my mother", "a holiday home", "a trip to work".
    """
    said = visit_at(items, at)
    if not said or _turned_away(items, at) or _after(items, at, _CUES):
        return []
    before = items[at - 1] if at > 0 and not items[at].apart else None
    bare = not _is_word(said[0], _LEADS_ITSELF_IN)
    unknown = before is not None and (
        before.what is Is.ODD
        or (
            before.what is Is.WORD
            and before.text not in KNOWN_WORDS
            and before.text not in _HOW_MUCH_OF_A_VISIT
        )
    )
    if bare and unknown:
        return []
    if _somebody_elses_visit(items, at) or not _leaves_it_a_visit(items, at + len(said)):
        return []
    return said


def _by_the_night(sentences: Sequence["_Sentence"]) -> list[_Span]:
    """Where an amount stands that is said by the night, with the words that say so.

    "£150 a night", "150 quid per night", "£90 for one night". It is what a
    place charges for a stay, which Burro holds for no area, so it is heard
    and is no budget. A number that is no amount of money is a number of
    nights, and says nothing of what one costs.
    """
    found: list[_Span] = []
    for sentence in sentences:
        items = sentence.items
        for at, item in enumerate(items):
            in_money = item.money or _is_word(_beside(items, at + 1), IN_MONEY)
            if item.what is not Is.NUMBER or not in_money:
                continue
            paid = paid_by(items, at)
            if paid.by != BY_NO_MONTH:
                continue
            on = at + 1
            while on < len(items) and not items[on].apart and on - at <= _FURTHEST_PERIOD:
                if _names_a_period(items[on]):
                    night = items[on].text.removesuffix("'s") in _A_NIGHT
                    if night:
                        found.append((items[min(paid.first, at)].start, items[on].end))
                    break
                on += 1
    return found


class _Home(NamedTuple):
    """The size and the kind of a home as they were named, and where the words stand."""

    bedrooms: int  # nothing where no number of bedrooms was said
    kind: str  # a word of `RENT_SEGMENTS` or `BUY_SEGMENTS`, or none
    span: _Span
    # The item after the last of its words.
    end: int
    # Where the words for its size stand, with the article before them: "a two bed", of
    # "a two bed flat". And where the words for its kind stand, with what a home is called
    # after them: "terraced house", of "a 3 bed terraced house". Each is the whole of
    # the home where nothing else was said of it, and nothing where it was not said.
    sized: _Span | None = None
    kinded: _Span | None = None


def _home_at(items: Sequence[Item], at: int) -> _Home | None:
    """The home that is named from here: "a two bed flat", "3 bedrooms", "a terraced house"."""
    first = items[at]
    bedrooms, end = 0, at
    if first.what is Is.NUMBER:
        after = items[at + 1] if at + 1 < len(items) else None
        glued = first.unit == "bed"
        apart = not glued and not first.unit and _is_word(after, BEDROOMS)
        if not (glued or (apart and after is not None and not after.apart)):
            return None
        if first.money or first.low or first.value < 1:
            return None
        bedrooms, end = first.value, at + (1 if glued else 2)
    counted = end
    beside = end == at or (end < len(items) and not items[end].apart)
    said = _phrase_at(items, end, _KINDS_OF_HOME) if beside else []
    kind = " ".join(item.bare or item.text for item in said)
    end += len(said)
    if not bedrooms and not kind:
        return None
    # What a home is called, after either: "a terraced house", "a two bed place".
    if end < len(items) and _is_word(items[end], A_HOME) and not items[end].apart:
        end += 1
    # And the article before it, so that "a two bed house" is read whole.
    led = at > 0 and _is_word(items[at - 1], _THE) and not first.apart
    start = items[at - 1].start if led else first.start
    last = items[end - 1].end
    sized = (start, items[counted - 1].end) if bedrooms else None
    kinded = (items[counted].start if bedrooms else start, last) if kind else None
    return _Home(bedrooms, kind, (start, last), end, sized, kinded)


def _segment_for(tenure: Tenure, home: _Home) -> SegmentChoice | None:
    """The kind of home the search can hold for what was said, for one tenure. None for a visit."""
    if tenure is Tenure.VISIT:
        return None
    if tenure is Tenure.BUY:
        return BUY_SEGMENTS.get(home.kind)
    if home.kind in RENT_SEGMENTS:
        return RENT_SEGMENTS[home.kind]
    return _BEDS[min(home.bedrooms, len(_BEDS)) - 1] if home.bedrooms else None


def _said_of(home: _Home) -> str:
    """What a home is called where the search can hold no part of it: what was said."""
    if home.kind:
        kinds = RENT_SEGMENTS if home.kind in RENT_SEGMENTS else BUY_SEGMENTS
        return SEGMENT_LABELS[Segment(kinds[home.kind].value)]
    return SEGMENT_LABELS[Segment(_BEDS[min(home.bedrooms, len(_BEDS)) - 1].value)]


def _not_held(tenure: Tenure, home: _Home) -> str:
    """What is said where part of a home cannot be held for the tenure it is for."""
    if tenure is Tenure.VISIT:
        return NO_HOME_ON_A_VISIT
    if tenure is Tenure.BUY:
        if home.kind in RENT_SEGMENTS:
            return TO_RENT_ALONE
        return BY_KIND if home.bedrooms else ""
    apart = home.kind in BUY_SEGMENTS and home.kind not in _A_FLAT
    return BY_BEDROOMS if apart else ""


def _homes_named(sentences: Sequence["_Sentence"], taken: Home) -> list[_Home]:
    """Each home that plain sentences name, as it was named, with where its words stand.

    `taken` is what the grammar made of the sentences. A home is one that
    the grammar took: its size or its kind stands among what it read. So a
    wish that is turned round beside a home, "no main roads, a two bed flat",
    turns nothing of the home away, and no sentence is plain in which a home
    itself is turned away.
    """
    read = [span for _, span in (*taken.bedrooms, *taken.segments)]
    found: list[_Home] = []
    for sentence in sentences:
        items = sentence.items
        skip = 0
        for at, item in enumerate(items):
            if at < skip or item.what not in (Is.NUMBER, Is.WORD):
                continue
            # The words for a visit name no home, whatever word they hold: "a guest house".
            tenure = item.what is Is.WORD and (
                _phrase_at(items, at, RENTS | BUYS) or visit_at(items, at)
            )
            home = None if tenure else _home_at(items, at)
            if tenure:
                skip = at + len(tenure)
            elif home is not None:
                skip = home.end
                begins, ends = home.span
                if any(begins <= start and end <= ends for start, end in read):
                    found.append(home)
    return found


def _tenure_of(home: Home, spec: PreferenceSpec) -> Tenure:
    """The tenure that what a plain prompt says of a home is for: the words', or the search's."""
    made = _budget(home, spec)
    if made is None or made[0].tenure is TenureChoice.UNCHANGED:
        return spec.tenure
    return Tenure(made[0].tenure.value)


# More flats than one. The grammar takes each as what a home is called, and as no kind of it.
_FLATS = frozenset({"flats", "apartments", "maisonettes"})


def _of_two_homes(sentences: Sequence["_Sentence"], home: Home, spec: PreferenceSpec) -> bool:
    """Whether a prompt names two sizes or two kinds of home, of which the search holds one.

    "Renting a 2 bed or a 3 bed", "a flat or a terraced house to buy". The
    first was applied, and the second was in no list. Nobody can say which is
    meant, so the prompt is not plain, and each is offered. One that is said
    twice is said once: "a 2 bed flat, 2 bedrooms".

    A house of no kind is a kind of home to buy that is no flat, so "a flat
    or a house" names two: it was applied as a flat, and the house was in no
    list. So do "flats or houses", which was applied as a terraced house.
    Beside a kind of house it is that kind, "a terraced house or a house".

    A rent is held by the number of bedrooms, so to rent a flat or a house
    is no kind the search holds, and "a flat or a house" is applied as it
    was. A room and a studio are kinds that a rent is held by, and a flat or
    a house beside either is another kind: "a room or a flat" was applied as
    a room, and the flat was in no list.
    """
    tenure = _tenure_of(home, spec)
    named = _homes_named(sentences, home)
    held = {_segment_for(tenure, one) for one in named} - {None}
    if len(held) > 1:
        return True
    flats = any(
        _is_word(item, _FLATS) and not _turned_away(sentence.items, at)
        for sentence in sentences
        for at, item in enumerate(sentence.items)
    )
    if tenure is Tenure.BUY:
        return bool(home.houses) and (flats or bool(held - set(KINDS_OF_HOUSE)))
    another = flats or bool(home.houses) or any(one.kind in BUY_SEGMENTS for one in named)
    return another and bool(held & {SegmentChoice.ROOM, SegmentChoice.STUDIO})


def _not_held_of(
    sentences: Sequence["_Sentence"], taken: Home, tenure: Tenure, rested: Sequence[_Span]
) -> tuple[Suggestion, ...]:
    """What a plain prompt says of a home that the search cannot hold, in the words of an offer.

    Burro holds what homes sell for by kind of home and not by the number of
    bedrooms, and what they rent for by bedrooms and not by kind. A plain
    prompt is applied with what the search can hold of a home, and the rest
    was in no list: the bedrooms of a home to buy, the kind of house of a home
    to rent, a studio to buy. In a prompt that is not plain the offer of the
    home says why, in its note. Here the same words are said: what cannot be
    held is offered with nothing to choose but to leave it out.

    It rests on the words that were not held, and on the whole of the home
    where no edit rests on any of it. `taken` is what the grammar made of
    the sentences, and `rested` what the edits of the prompt rest on. It is
    the same whatever was applied beside it, so the status of a plain prompt
    still does not say what the search holds.
    """
    found: dict[tuple[str, str], list[_Span]] = {}
    for home in _homes_named(sentences, taken):
        note = _not_held(tenure, home)
        if not note:
            continue
        if tenure is Tenure.VISIT:
            # A visit holds nothing of a home, so the whole of what was named is not held.
            found.setdefault((f"A {_said_of(home)}", note), []).append(home.span)
            continue
        begins, ends = home.span
        in_part = any(begins <= start and end <= ends for start, end in rested)
        of_its_size = note == BY_KIND
        part = (home.sized if of_its_size else home.kinded) if in_part else None
        what = home._replace(kind="") if of_its_size else home._replace(bedrooms=0)
        spans = found.setdefault((f"A {_said_of(what)}", note), [])
        spans.append(part or home.span)
    if tenure is Tenure.VISIT:
        # Nor does a visit hold an amount. It is said by its figure, as an offer names one.
        for amount, _, where in taken.amounts:
            about = (f"A budget of \N{POUND SIGN}{money(amount)}", NO_BUDGET_ON_A_VISIT)
            found.setdefault(about, []).append(where)
        # Nor a budget to move: "somewhere cheaper".
        for cheaper, _, where in taken.steps:
            about = (LOWER_BUDGET if cheaper else HIGHER_BUDGET, NO_STEP_ON_A_VISIT)
            found.setdefault(about, []).append(where)
    return tuple(
        Suggestion(
            target=BUDGET_TARGET,
            label=label,
            spans=tuple(Span(start=start, end=end) for start, end in sorted(set(spans))),
            choices=(IGNORE,),
            note=note,
            by_name=True,
        )
        for (label, note), spans in sorted(found.items(), key=lambda said: min(said[1]))
    )


def _weighs_what_homes_sold_for(edit: _Edit) -> bool:
    """Whether an edit would have what homes sold for count. To take it off is no such edit."""
    if not isinstance(edit, WeightEdit) or edit.action is WeightAction.REMOVE:
        return False
    return edit.feature_id in SOLD_FOR


def _not_weighed(sold: Sequence[_Made]) -> tuple[Suggestion, ...]:
    """What a plain prompt says of what homes sold for, on a visit, in the words of an offer."""
    found: dict[FeatureId, list[_Span]] = {}
    named: set[FeatureId] = set()
    for made in sold:
        assert isinstance(made.edit, WeightEdit)
        found.setdefault(made.edit.feature_id, []).extend(made.spans)
        if made.edit.provenance is _STATED:
            named.add(made.edit.feature_id)
    return tuple(
        Suggestion(
            target=f"feature:{feature_id}",
            label=FEATURES[feature_id].short_label,
            spans=tuple(Span(start=start, end=end) for start, end in sorted(set(spans))),
            choices=(IGNORE,),
            note=NO_PRICE_ON_A_VISIT,
            by_name=feature_id in named,
            only_by_choice=only_by_choice(feature_id, feature_id in named),
        )
        for feature_id, spans in found.items()
    )


def _houses_of_no_kind(sentences: Sequence["_Sentence"]) -> list[_Span]:
    """Where a prompt names a house, where it names no kind of home that a price is held by.

    "A house", "a two bed house". A house share is a room, and a house that
    is turned away, "not a house", is none. Beside a kind that is named, "a
    terraced house", "a house or a flat", the kind is what was said.
    """
    houses: list[_Span] = []
    for sentence in sentences:
        items = sentence.items
        skip = 0
        for at, item in enumerate(items):
            # A guest house is where a visitor stays, and is no house to buy.
            skip = max(skip, at + len(visit_at(items, at)))
            if at < skip:
                continue
            if item.what is not Is.WORD or _turned_away(items, at):
                continue
            if _phrase_at(items, at, frozenset(BUY_SEGMENTS)):
                return []
            shared = _phrase_at(items, at, frozenset(RENT_SEGMENTS))
            if _is_word(item, A_HOUSE) and not shared:
                # And the article before it, so that "a house" is read whole.
                led = at > 0 and _is_word(items[at - 1], _THE) and not item.apart
                houses.append((items[at - 1].start if led else item.start, item.end))
    return houses


_ENDS_A_SENTENCE = frozenset(".?!")


def _kept_away(sentences: Sequence["_Sentence"]) -> list[bool]:
    """Of each sentence, whether its words ask to be kept away from a place it names.

    A sentence that asks wishes nothing: "how far is the station from".
    Lines that no mark ends are read together, so that "far from", typed on
    a line of its own above the name of a place, is said of that place.
    """
    away = [not sentence.asked and _stays_away(sentence.items) for sentence in sentences]
    run_on = [not set(sentence.line.closed_by) & _ENDS_A_SENTENCE for sentence in sentences]
    for at in range(1, len(sentences)):
        away[at] = away[at] or (away[at - 1] and run_on[at - 1])
    for at in range(len(sentences) - 2, -1, -1):
        away[at] = away[at] or (away[at + 1] and run_on[at])
    return away


class _Notices:
    """What is noticed in the sentences of a prompt, in the order it stands."""

    def __init__(
        self, release: Release, grammar: Grammar, spec: PreferenceSpec, about_people: bool = False
    ) -> None:
        self.release = release
        self.grammar = grammar
        self.spec = spec
        # The words draw the notice: they ask who lives somewhere in a way nothing is
        # offered for, or may ask for fewer of a group of people. Nothing that counts
        # who lives somewhere is then offered, whatever else the words name.
        self.about_people = about_people
        # The tenures the words of the prompt name, which a home that is named is for.
        self.said: frozenset[Tenure] = frozenset()
        # The words say a visit, or the search is one and the words name no other kind.
        self.of_a_visit = False
        # Where the prompt names a house, and no kind of home that a price is held by.
        self.houses: list[_Span] = []
        # Where a thing that is only offered stands, with what was said of it:
        # "slightly affluent", "a bit of character". By where the thing stands.
        self.whole: dict[_Span, _Span] = {}
        # The time of each journey that holds none straight before its place, by where the
        # name of the place stands: in which sentence, and where among its items.
        self.given: dict[_Where, _Given] = {}
        # Where the words stand that were heard and that nothing is offered for: how long a
        # stay is, beside a visit.
        self.heard: list[_Span] = []
        # The times of each sentence that was asked of, with the sentence they are of. To
        # work them out is to read the sentence, and they are asked for at every name.
        self._timed: dict[int, tuple[Sequence[Item], list[_Time]]] = {}

    def _times_in(self, items: Sequence[Item]) -> list[_Time]:
        """Every time of a sentence that may be the time of a journey, worked out once.

        A sentence that said one name sixty times had its times worked out
        for each of them, twice over, and anybody may send such a sentence.
        They are kept by which list the items are, with the list beside
        them, so that no other list is ever taken for it.
        """
        kept = self._timed.get(id(items))
        if kept is None or kept[0] is not items:
            kept = self._timed[id(items)] = (items, _times_of(items, self.grammar.known.lexicon))
        return kept[1]

    def of(self, sentences: Sequence["_Sentence"], journeys: Sequence[_Made]) -> list[_Noticed]:
        """What is noticed in the sentences, with the journeys the grammar made of them.

        A name that stands in such a journey is read there, and is not
        noticed a second time by itself.
        """
        found: list[_Noticed] = []
        read = [span for journey in journeys for span in journey.spans]
        away = _kept_away(sentences)
        made = self._times(sentences, journeys, away)
        for journey in journeys:
            if journey.options is None:
                found += self._journey(journey, made.get(id(journey), _Given()))
        worded = frozenset(
            tenure for sentence in sentences for tenure in self._tenures(sentence.items, False)
        )
        # On a visit, and beside the words for one, an amount alone is what the visit may
        # cost. It names no home to rent or to buy, however large or small it is.
        self.of_a_visit = Tenure.VISIT in worded or (self.spec.visiting and not worded)
        self.said = worded | frozenset(
            tenure
            for sentence in sentences
            for tenure in self._tenures(sentence.items, not self.of_a_visit)
        )
        self.houses = _houses_of_no_kind(sentences)
        self.whole = dict(_said_of_what_is_offered(sentences))
        # The words of a time that was taken say how long a journey is and how it is made,
        # and nothing else is made of them: "on the tube" is no wish to be well connected.
        taken = [span for given in self.given.values() if given.minutes for span in given.spans]
        # How long a stay is, in a part of the sentence of its own: "a hotel, 3 nights".
        stays: list[_Span] = []
        for where, (sentence, kept_away) in enumerate(zip(sentences, away, strict=True)):
            items = sentence.items
            skip = 0
            for at, item in enumerate(items):
                if at < skip:
                    continue
                if stay := stay_alone(items, at):
                    stays.append((stay[0].start, stay[-1].end))
                    skip = at + len(stay)
                elif item.what is Is.THING:
                    if not any(start <= item.start and item.end <= end for start, end in taken):
                        found += self._thing(items, at)
                elif item.what is Is.NAME:
                    if not any(start <= item.start and item.end <= end for start, end in read):
                        given = self.given.get((where, at), _Given())
                        found += self._name(items, at, kept_away, given)
                elif item.what is Is.NUMBER:
                    found += self._money(items, at)
                    if (home := _home_at(items, at)) is not None:
                        found += self._home(items, at, home)
                        skip = home.end
                elif item.what is Is.WORD and (said := visit_at(items, at)):
                    # Whatever they say, the words for a visit name no home and no tenure
                    # but their own: "a guest house", "a holiday let".
                    if names_a_visit(items, at):
                        found += self._visit(said)
                    skip = at + len(said)
                elif item.what is Is.WORD and (said := _phrase_at(items, at, RENTS | BUYS)):
                    found += self._tenure(items, at, said)
                    skip = at + len(said)
                elif item.what is Is.WORD and (home := _home_at(items, at)) is not None:
                    found += self._home(items, at, home)
                    skip = home.end
                elif (
                    item.what is Is.WORD
                    and not self.release.places
                    and (said := _phrase_at(items, at, _SAYS_A_JOURNEY, longest=4))
                ):
                    # A journey the grammar made holds these words already, and is
                    # said to be missing by all of them.
                    if not any(start <= item.start and said[-1].end <= end for start, end in read):
                        found += self._journey_said(items, at, said)
                    skip = at + len(said)
        visits = any((thing.target, thing.label) == ("tenure", VISITING) for thing in found)
        # It is said of the visit that the prompt names, or that the search is. It was heard,
        # and there is nothing of it to choose: no search holds how long a stay is.
        self.heard = stays if visits or self.spec.visiting else []
        return found

    def _times(
        self, sentences: Sequence["_Sentence"], journeys: Sequence[_Made], away: Sequence[bool]
    ) -> dict[int, _Given]:
        """The time of each journey that holds none, as the words of the prompt give it.

        It is kept by where the name of each place stands, and is given back
        for the journeys the grammar made, each by which journey it is.
        """
        named: dict[_Where, int] = {}
        timed: list[_Span] = []
        for journey in journeys:
            edit = journey.edit
            assert isinstance(edit, CommuteEdit)
            where = _where_named(sentences, journey)
            if edit.max_minutes:
                timed += journey.spans
            elif where is not None and journey.options is None:
                named[where] = id(journey)
        read = [span for journey in journeys for span in journey.spans]
        noticed = [
            (at, on)
            for at, (sentence, kept_away) in enumerate(zip(sentences, away, strict=True))
            for on, item in enumerate(sentence.items)
            if not kept_away
            and not any(start <= item.start and item.end <= end for start, end in read)
            and self._may_be_reached(sentence.items, on)
        ]
        lexicon = self.grammar.known.lexicon
        self.given = _times_given(sentences, [*named, *noticed], timed, lexicon)
        return {named[where]: given for where, given in self.given.items() if where in named}

    def _may_be_reached(self, items: Sequence[Item], at: int) -> bool:
        """Whether a journey may be offered to what is named here, and no time was read for it.

        The name of a place that nothing turns away and that no time stands
        straight before. A name that is an area's too is one only where no
        word before it makes a rule of it: "only in", "not in".
        """
        item = items[at]
        place = self.release.place(item.place) if item.what is Is.NAME and item.place else None
        if place is None or place.kind is PlaceKind.UNIVERSITY:
            return False
        if self._is_turned_away(items, at) or _minutes_before(items, at):
            return False
        return not item.area or not _after(items, at, ONLY_IN | NOT_IN)

    def _is_turned_away(self, items: Sequence[Item], at: int) -> bool:
        """Whether the name of a place stands after a word that turns it away.

        It is asked of what stands before the time that runs on to the
        place, where one does.
        """
        led_in = _where_it_is_led_in(self._times_in(items), at)
        return _turned_away(items, at) if led_in == at else _turned_away(items, led_in)

    def _tenures(self, items: Sequence[Item], by_size: bool = True) -> Iterator[Tenure]:
        """The tenures a sentence names: by a word for one, or by an amount of one alone.

        A rent is paid by the month, and no rent is as high as a price. A
        word that is turned away, "I don't rent", names nothing. Where it is
        not asked `by_size`, an amount names a rent only by what it is paid by.
        """
        skip = 0
        for at, item in enumerate(items):
            if at < skip:
                continue
            if item.what is Is.WORD and (stay := visit_at(items, at)):
                skip = at + len(stay)
                if names_a_visit(items, at):
                    yield Tenure.VISIT
            elif item.what is Is.WORD and (said := _phrase_at(items, at, RENTS | BUYS)):
                if not _turned_away(items, at):
                    rents = " ".join(word.text for word in said) in RENTS
                    yield Tenure.RENT if rents else Tenure.BUY
            elif item.what is Is.NUMBER and item.unit not in ("min", "bed"):
                paid = paid_by(items, at).by
                if paid == BY_NO_MONTH:
                    continue  # it is not read, so it names nothing
                # A rent is paid by the month or by the week, and no price is.
                if paid or (by_size and item.money and item.value <= LIMITS.rent.maximum):
                    yield Tenure.RENT
                elif by_size and item.money and item.value >= LIMITS.buy.minimum:
                    yield Tenure.BUY

    def _home(self, items: Sequence[Item], at: int, home: _Home) -> Iterator[_Noticed]:
        """The size and the kind of a home, offered whenever they are named.

        A home is for the tenure the words of the prompt name, and for the
        tenure of the search where they name none or both. The choice holds
        the kind of home the search can hold for that tenure, and the tenure
        where it is not the search's own, and says both. Where part of what
        was said cannot be held, the offer says why. Where none of it can,
        nothing is offered to be set, and it is still said to have been
        heard. Nobody is moved to the other tenure for having named a home,
        but a person who has chosen no tenure and names a kind of home that
        is held for buying alone: the choice says that it is to buy.
        """
        if _turned_away(items, at):
            return
        named = next(iter(self.said)) if len(self.said) == 1 else None
        tenure = named or self.spec.tenure
        segment = _segment_for(tenure, home)
        note = _not_held(tenure, home)
        nobody_chose = not self.said and self.spec.tenure_from is Provenance.DEFAULT
        for_sale_alone = home.kind in BUY_SEGMENTS and home.kind not in _A_FLAT
        if segment is None and nobody_chose and tenure is Tenure.RENT and for_sale_alone:
            tenure, segment = Tenure.BUY, BUY_SEGMENTS[home.kind]
        if segment is None:
            if note:
                yield _Noticed("budget", f"A {_said_of(home)}", home.span, (), note, always=True)
            return
        moved = TenureChoice.UNCHANGED if tenure is self.spec.tenure else TenureChoice(tenure.value)
        label = f"A {SEGMENT_LABELS[Segment(segment.value)]}"
        choice = _budget_choice(f"Set {_lower_first(label)}{_TO.get(moved, '')}", moved, 0, segment)
        yield _Noticed("budget", label, home.span, choice, note, always=True)

    def _journey(self, made: _Made, given: _Given = _NO_TIME) -> Iterator[_Noticed]:
        """A journey the grammar made, to a place the release holds, as an offer.

        `given` is the time the words of the prompt give it, where the
        sentence it was made of gives it none.
        """
        edit = made.edit
        assert isinstance(edit, CommuteEdit)
        place = self.release.place(edit.place_id)
        if place is None or place.kind is PlaceKind.UNIVERSITY:
            return
        given = _made_the_way(given, edit.mode)
        if given.could_not == TIME_NOT_TAKEN:
            # A time was typed beside it, so it is not added at the usual one.
            for span in made.spans:
                yield _Noticed(COMMUTE_TARGET, place.name, span, (), given.could_not, always=True)
            return
        minutes, at_least = edit.max_minutes, made.at_least
        firm, mode = edit.strictness is StrictnessChoice.HARD, edit.mode
        if given.minutes:
            minutes, at_least, firm = given.minutes, given.at_least, given.firm
            ways = {mode, given.mode} - {ModeChoice.UNCHANGED}
            mode = ways.pop() if len(ways) == 1 else ModeChoice.UNCHANGED
        choices = _journey_choice(place.name, place.place_id, minutes, firm, mode)
        note = longer_was_taken(at_least, minutes) if at_least else given.could_not
        for span in (*made.spans, *given.spans):
            yield _Noticed("commute", place.name, span, choices, note)

    def _thing(self, items: Sequence[Item], at: int) -> Iterator[_Noticed]:
        item = items[at]
        target = self.grammar.known.lexicon[item.text]
        if about_a_campus(target) or _names_no_place(items, at):
            # A campus in a prompt that is not plain is heard as a request about
            # people. And "I commute to school" is no wish for schools.
            return
        # What is offered one way is offered so where the grammar makes the
        # sentence it stands in, and nothing turns it. In any other sentence
        # nobody can say which way it is meant, "anything but posh", and both
        # ways are offered. A word for character is offered one way whatever
        # is said of it. So is a thing that counts who lives somewhere, of
        # which nothing but more is ever offered.
        of_people = counts_residents(target)
        one_way = target.one_way and (target.whatever or of_people or item.span in self.whole)
        span = self.whole.get(item.span, item.span)
        no_measure = COUNTS_RESIDENTS if self.about_people else frozenset[FeatureId]()
        no_vibe = HOLDS_RESIDENTS if self.about_people else frozenset[TagId]()
        if self.of_a_visit:
            # A visit weighs nothing of what homes sold for. Where the words are read as
            # something else too, that is offered. Where they are not, it is said why
            # nothing is.
            sold = [feature_id for feature_id in target.features if feature_id in SOLD_FOR]
            no_measure |= SOLD_FOR
            if sold and not target.tags and len(sold) == len(target.features):
                for feature_id in sold:
                    label = FEATURES[feature_id].short_label
                    yield _Noticed(
                        f"feature:{feature_id}",
                        label,
                        span,
                        (),
                        NO_PRICE_ON_A_VISIT,
                        always=True,
                        by_name=names_it(target),
                    )
                return
        features = [
            _Noticed(
                f"feature:{feature_id}",
                FEATURES[feature_id].short_label,
                span,
                _one_way(_feature_choices(feature_id), target.direction)
                if one_way
                else _feature_choices(feature_id),
                _note_of(target, feature_id in COUNTS_RESIDENTS),
                by_name=names_it(target),
            )
            for feature_id in target.features
            if feature_id not in no_measure
        ]
        tags = [
            _Noticed(
                f"tag:{tag_id}",
                TAGS[tag_id].short_label,
                span,
                _tag_choices(tag_id, target.toward if one_way else None),
                " ".join(
                    said
                    for said in (
                        _note_of(target, tag_id in HOLDS_RESIDENTS),
                        counts_crime(tag_id) if tag_id in HOLDS_CRIME else "",
                    )
                    if said
                ),
                by_name=names_it(target),
            )
            for tag_id in target.tags
            if tag_id not in no_vibe
        ]
        # Of what is only nearest, a vibe comes before the measures it is made of, but
        # for a measure that is the first reading of the word.
        if not target.one_way:
            yield from (*features, *tags)
            return
        leads = {f"feature:{feature_id}" for feature_id in target.leads}
        first = [one for one in features if one.target in leads]
        yield from (*first, *tags, *(one for one in features if one.target not in leads))

    def _name(
        self, items: Sequence[Item], at: int, kept_away: bool = False, given: _Given = _NO_TIME
    ) -> Iterator[_Noticed]:
        """The name of a place or of an area. `given` is the time the words give a journey to it."""
        item = items[at]
        place = self.release.place(item.place) if item.place else None
        area = self.release.neighbourhood(item.area) if item.area else None
        if place is not None and place.kind is PlaceKind.UNIVERSITY:
            return
        turned_away = self._is_turned_away(items, at)
        minutes = _minutes_before(items, at)
        given = _made_the_way(given, _way_beside(items, at)[0])
        # A time was given where the time of a journey stands, and none was taken. Or one was
        # given apart from the place, and the reader cannot say that it is this journey's:
        # the journey is then offered with no time, and says that one was given.
        stands = not minutes and not given.minutes and _time_stands_before(items, at)
        apart = "" if minutes or stands else given.could_not
        anothers = _may_be_anothers(items, at)
        not_placed = apart == TIME_NOT_PLACED and not anothers
        not_taken = TIME_NOT_TAKEN if stands else "" if not_placed else apart
        timed = bool(given.minutes or apart)
        # The words say where somebody is, or where a person stays or wants to be near:
        # the name of an area is no rule for the area there.
        no_rule = area is not None and _is_no_rule(items, at)
        # A name that is an area's and a place's is a journey after words that
        # expect a place, beside a time, and where the words make no rule of it. It is an
        # area anywhere else.
        if place is not None and (area is None or _cued(items, at) or timed or no_rule):
            if kept_away:
                # Nothing of it can be chosen, and it is said to have been heard.
                yield _Noticed(
                    COMMUTE_TARGET, place.name, item.span, (), NO_STAYING_AWAY, always=True
                )
            elif not_taken and not turned_away:
                # The journey would be added with the usual minutes, which nobody said,
                # and one press took it. It is said to have been heard, and why.
                yield _Noticed(COMMUTE_TARGET, place.name, item.span, (), not_taken, always=True)
            elif not turned_away:
                # It rests on the minutes too, where it holds them, and on what caps them.
                start = _where_minutes_start(items, at) if minutes else item.start
                if minutes:
                    led_in = _where_it_is_led_in(self._times_in(items), at)
                    start = min(start, items[led_in].start)
                shorter = _range_before(items, at)
                number = _number_before(items, at) if minutes else None
                firmly = (
                    _said_firmly(items, items.index(number), len(items), FIRM_OF_MINUTES)
                    if number is not None
                    else None
                )
                if firmly is not None:
                    start = min(start, firmly[0])
                # A range is a limit at its longer end, and so are minutes that are capped.
                firm = bool(shorter) or firmly is not None
                # It rests on the words that say how it is travelled too, where they do.
                mode, said_by = _way_beside(items, at)
                beside = given.spans
                if not minutes and given.minutes:
                    # The time stands with a word or two between it and the place, after the
                    # place, or apart from it, and is the time of the journey all the same.
                    minutes, shorter, firm = given.minutes, given.at_least, given.firm
                    ways = {mode, given.mode} - {ModeChoice.UNCHANGED}
                    mode = ways.pop() if len(ways) == 1 else ModeChoice.UNCHANGED
                    if given.leads:
                        start, beside = min(start, *(begins for begins, _ in beside)), ()
                start = min([start, *(begins for begins, _ in said_by)])
                end = max([item.end, *(ends for _, ends in said_by)])
                choices = _journey_choice(place.name, place.place_id, minutes, firm, mode)
                note = longer_was_taken(shorter, minutes) if shorter else ""
                if not_placed:
                    note = TIME_NOT_PLACED
                if anothers:
                    # It is offered, and no press takes it with others.
                    note = MAY_BE_ANOTHERS
                for span in ((start, end), *beside):
                    yield _Noticed("commute", place.name, span, choices, note)
        elif area is not None and not no_rule:
            # What turns it away may follow it: "my boss lives in Tallowgate so I'd rather not".
            against = turned_away or _turned_away_after(items, at)
            choices = _area_choice(area.name, area.area_id, against)
            yield _Noticed("area", area.name, item.span, choices)

    @staticmethod
    def _journey_said(items: Sequence[Item], at: int, said: Sequence[Item]) -> Iterator[_Noticed]:
        """A journey that is said where the release names no place to make one to.

        Its one choice names no place, and the reducer turns it away: it is
        there to be said to be missing, and is never offered.
        """
        if _turned_away(items, at):
            return
        span = (said[0].start, said[-1].end)
        yield _Noticed(COMMUTE_TARGET, A_JOURNEY_TO, span, _journey_choice("", "", 0))

    def _of_which_tenure(self, amount: int, by_month: bool) -> TenureChoice:
        """The tenure an amount must be of, where it cannot be of the search's own.

        A rent is paid by the month, and no rent is as high as a price. It is
        `unchanged` wherever the amount can be of the tenure the search holds.
        """
        rent = LIMITS.rent.minimum <= amount <= LIMITS.rent.maximum
        buy = LIMITS.buy.minimum <= amount <= LIMITS.buy.maximum and not by_month
        if self.spec.visiting:
            # A visit holds no amount, so a figure alone says nothing of a home. By the
            # month it is a rent.
            return TenureChoice.RENT if by_month else TenureChoice.UNCHANGED
        suits = rent if self.spec.tenure is Tenure.RENT else buy
        if suits or not (rent or buy or by_month):
            return TenureChoice.UNCHANGED
        return TenureChoice.RENT if rent or by_month else TenureChoice.BUY

    def _money(self, items: Sequence[Item], at: int) -> Iterator[_Noticed]:
        """An amount of money, offered as the budget. The choice holds the amount alone.

        The size of home and the tenure that stand beside it are no part of
        it, since the label names neither: each is offered for itself. The
        tenure is part of it only where the amount cannot be of the tenure
        the search holds, and the label then says which it is of.

        A rent is held by the month. An amount that is said by the week is
        offered as what it comes to by the month, and the offer says that it
        was worked out and from what: it is never offered at the figure that
        was typed. An amount by any other period, a year, a night, is not
        read, since no rule says what it comes to.
        """
        item = items[at]
        paid = paid_by(items, at)
        by_month = paid.by in (BY_THE_MONTH, BY_WEEK)
        if item.unit in ("min", "bed") or paid.by == BY_NO_MONTH or not (item.money or by_month):
            return
        after = items[at + 1] if at + 1 < len(items) else None
        if item.distance and _is_word(after, TO_A_PLACE | _AWAY):
            return  # "1.5m from a park" and "1.5m away" are distances
        by_week = paid.by == BY_WEEK
        if by_week and not item.value:
            return  # nothing a week comes to nothing a month, which is no amount
        amount = by_the_month(item.value) if by_week else item.value
        worked_out = worked_out_by_the_month(item.value) if by_week else ""
        span = (items[paid.first].start, items[paid.last - 1].end)
        tenure = self._of_which_tenure(amount, by_month)
        label = f"A budget of £{money(amount)}{' a month' if by_month else ''}"
        firmly = _said_firmly(items, at, max(paid.last, at + 1), FIRM_OF_MONEY)
        if firmly is not None:
            # It rests on the words that make it a limit too: "max £400k".
            span = (min(span[0], firmly[0]), max(span[1], firmly[1]))
        most = f"A budget of no more than £{money(amount)}{' a month' if by_month else ''}"
        named = next(iter(self.said)) if len(self.said) == 1 else None
        unsaid = tenure is TenureChoice.UNCHANGED
        held = (named or self.spec.tenure) if unsaid else Tenure(tenure.value)
        if self.of_a_visit and not by_month and named in (None, Tenure.VISIT):
            # What the visit may cost, whatever kind of home its size would suit.
            held = Tenure.VISIT
        if held is Tenure.VISIT:
            # A visit holds no budget. Nothing of it can be chosen, and it is said why.
            yield _Noticed("budget", label, span, (), NO_BUDGET_ON_A_VISIT, always=True)
            return
        if self.spec.visiting and unsaid:
            # The words name a home to rent or to buy, and the search is a visit, which
            # holds no amount. So the amount says which kind of search it is of.
            tenure = TenureChoice(held.value)
        if self.houses and held is Tenure.BUY:
            # A house is no flat. It is taken as a terraced house, with every other kind of
            # house one press away, and where that has no price the person is asked which.
            moved = TenureChoice.UNCHANGED if self.spec.tenure is Tenure.BUY else TenureChoice.BUY
            took = self.release.costed(Tenure.BUY, DEFAULT_HOUSE)
            kinds = tuple(
                _for_a_house(
                    f"Set {_lower_first(most if firmly else label)} for a "
                    f"{SEGMENT_LABELS[Segment(kind.value)]}{_TO.get(moved, '')}",
                    moved,
                    amount,
                    kind,
                    firm=firmly is not None,
                    assumed=took and kind.value == DEFAULT_HOUSE.value,
                )
                for kind in KINDS_OF_HOUSE
            )
            note = _a_terraced_house(self.release) if took else BY_KIND_OF_HOUSE
            for where in (span, *self.houses):
                yield _Noticed("budget", label, where, kinds, note)
            return
        said = f"Set {_lower_first(most if firmly else label)}{_TO.get(tenure, '')}"
        choice = _budget_choice(said, tenure, amount=amount, firm=firmly is not None)
        yield _Noticed("budget", label, span, choice, worked_out)

    @staticmethod
    def _visit(said: Sequence[Item]) -> Iterator[_Noticed]:
        """A visit, offered by its name. It rests on the words that say it, and how long."""
        choice = _budget_choice(f"Set {VISITING.lower()}", TenureChoice.VISIT)
        yield _Noticed("tenure", VISITING, (said[0].start, said[-1].end), choice)

    @staticmethod
    def _tenure(items: Sequence[Item], at: int, said: Sequence[Item]) -> Iterator[_Noticed]:
        if _turned_away(items, at):
            return
        rent = " ".join(item.text for item in said) in RENTS
        label = "Renting" if rent else "Buying"
        tenure = TenureChoice.RENT if rent else TenureChoice.BUY
        choice = _budget_choice(f"Set {label.lower()}", tenure)
        yield _Noticed("tenure", label, (said[0].start, said[-1].end), choice)


def _note_of(target: Target, counts_who_lives_there: bool) -> str:
    """What is said beside one thing a phrase is offered as.

    What a phrase says of what it asks for is said of every thing it is
    offered as, but for the line that a thing counts who lived somewhere at the
    census, which is said of the things that do and of no other: "family
    friendly" is offered as a vibe that counts households and as one that
    counts places alone.
    """
    if counts_who_lives_there:
        return target.note
    return "" if target.note == COUNTED_AT_THE_CENSUS else target.note


class _Offered(NamedTuple):
    """What came of what was noticed: what is offered, what is heard, and what is missing."""

    suggestions: tuple[Suggestion, ...]
    # Where the words stand of what the search holds already.
    already: list[_Span]
    # What the release holds for no area, in the order it stands in the text.
    missing: tuple[NotInRelease, ...]


def _offered(noticed: Sequence[_Noticed], spec: PreferenceSpec, release: Release) -> _Offered:
    """The suggestions for what was noticed, and where the words stand that need none.

    There is one suggestion for each thing, however often it is named. A
    choice is never offered if its edit would be turned away, or would change
    nothing. A thing of which nothing can be chosen is not offered.

    A thing that is not offered because the search holds it already was heard
    all the same: "near a park", said where the search holds a park already.
    Its words are given back, so that they are not said to be unread. So was
    a thing that is not offered because the release holds it for no area: it
    is said to be missing, by its name. A thing whose every edit would be
    turned away for any other reason was not heard.

    The size and the kind of a home are offered whatever the search holds:
    a person who names one is told that it was heard. Where nothing of it can
    be set it is offered with what is said of it, and with nothing to choose
    but to leave it out. Where the release holds no cost of it for any area,
    it is said to be missing, as any other thing is.

    What is said beside a word for character names the things it is offered
    as. So it names those that are offered and no other: a release that
    places no area on one of them offers the rest, and says so.
    """
    found: dict[tuple[str, str], tuple[list[_Span], tuple[Choice, ...], str]] = {}
    always: set[tuple[str, str]] = set()
    # A thing that is named once is named, whatever other word it was read into beside.
    named = {(thing.target, thing.label) for thing in noticed if thing.by_name}
    for thing in noticed:
        about = (thing.target, thing.label)
        spans, choices, note = found.setdefault(about, ([], thing.choices, thing.note))
        if thing.span not in spans:
            spans.append(thing.span)
        # Named twice, and once where more of it may be chosen, or where more is
        # to be said of it: "posh, but not too posh" is offered with both ends of
        # the scale, and "not rough, not posh" with what is said of both words.
        more = thing.choices if len(thing.choices) > len(choices) else choices
        found[about] = (spans, more, thing.note if len(thing.note) > len(note) else note)
        if thing.always:
            always.add(about)

    # Every choice is tried on the spec with its defaults given way, which is
    # what the reducer applies an edit to. It is worked out once for them all.
    ready = given_way_spec(spec)

    def tried(choice: Choice) -> bool | RejectReason:
        """Whether a choice would change the search, or why it would be turned away."""
        result = apply(ready, choice.operations, release)
        if result.rejected:
            return result.rejected[0].reason
        if says_a_visit_again(ready, result.spec):
            # It was heard, and there is nothing of it to choose.
            return False
        return any(applied.changed for applied in result.applied)

    suggestions: list[Suggestion] = []
    already: list[_Span] = []
    missing: list[NotInRelease] = []
    for (target, label), (spans, choices, note) in found.items():
        outcomes = [(choice, tried(choice)) for choice in choices]
        # Why a choice would be turned away is no answer to whether it changes anything.
        whatever = (target, label) in always
        open_to = tuple(
            choice
            for choice, changes in outcomes
            if changes is True or (whatever and changes is False)
        )
        stood = tuple(Span(start=start, end=end) for start, end in sorted(spans))
        lacking = any(changes is RejectReason.NOT_IN_RELEASE for _, changes in outcomes)
        if open_to or (whatever and note and not lacking):
            by_name = (target, label) in named
            suggestions.append(
                Suggestion(
                    target=target,
                    label=label,
                    spans=stood,
                    choices=(*open_to, IGNORE),
                    note=note,
                    by_name=by_name,
                    only_by_choice=_waits_for_a_person(target, by_name),
                )
            )
        elif outcomes and all(changes is False for _, changes in outcomes):
            already += spans
        elif any(changes is RejectReason.NOT_IN_RELEASE for _, changes in outcomes):
            missing.append(NotInRelease(target=target, label=label, spans=stood))
    # A word for character is offered as what the release carries of three things. Its
    # note names the three, so it is said again of those that are offered.
    nearest = [found.target for found in suggestions if found.note == NO_IDENTITY]
    suggestions = [
        found.replace(note=no_identity(nearest)) if found.note == NO_IDENTITY else found
        for found in suggestions
    ]
    return _Offered(
        tuple(sorted(suggestions, key=lambda suggestion: suggestion.spans[0].start)),
        already,
        tuple(sorted(missing, key=lambda thing: thing.spans[0].start)),
    )


def _waits_for_a_person(target: str, by_name: bool) -> bool:
    """Whether what is offered of a target waits for a person to choose it.

    It is asked of a measure and of a vibe. A journey, a budget, a home and an
    area count no measure, and none waits by this rule: what keeps a rule for
    an area or a firm limit from being taken is said by its ways.
    """
    kind, _, named = target.partition(":")
    if kind == "feature":
        return only_by_choice(FeatureId(named), by_name)
    return kind == "tag" and only_by_choice(TagId(named), by_name)


def _named(edit: object) -> tuple[str, str] | None:
    """What an edit asks for, as a suggestion names it: its target and its label."""
    if isinstance(edit, WeightEdit):
        return f"feature:{edit.feature_id}", FEATURES[edit.feature_id].short_label
    if isinstance(edit, TagEdit):
        return f"tag:{edit.tag_id}", TAGS[edit.tag_id].short_label
    if isinstance(edit, BudgetEdit):
        return BUDGET_TARGET, A_BUDGET
    if isinstance(edit, CommuteEdit):
        return COMMUTE_TARGET, A_JOURNEY_TO
    return None


def not_in_release_of(
    result: InterpretResult, rejected: Sequence[Rejected]
) -> tuple[NotInRelease, ...]:
    """Everything a reading asked for that the release holds for no area, each named once.

    `rejected` is what the reducer turned away of the edits of the reading.
    What it turned away as not in the release is named here by the label of
    the thing, with the words its edit rests on. What the reader noticed and
    did not offer follows. It is for whoever serves a reading: every
    interpreter's edits are held to the one reducer, so what is missing is
    said the same way whoever read the words.
    """
    found: dict[str, tuple[str, list[Span]]] = {}
    for turned in rejected:
        if turned.reason is not RejectReason.NOT_IN_RELEASE:
            continue
        # A group is named as its array of the edits is.
        edits: Sequence[object] = getattr(result.operations, turned.group.value)
        named = _named(edits[turned.index]) if turned.index < len(edits) else None
        if named is None:
            continue
        spans = found.setdefault(named[0], (named[1], []))[1]
        spans += [
            Span(start=rests.start, end=rests.end)
            for rests in result.rests_on
            if (rests.group, rests.index) == (turned.group, turned.index)
        ]
    for thing in result.not_in_release:
        found.setdefault(thing.target, (thing.label, []))[1].extend(thing.spans)
    return tuple(
        NotInRelease(
            target=target,
            label=label,
            spans=tuple(sorted(set(spans), key=lambda span: (span.start, span.end))),
        )
        for target, (label, spans) in found.items()
    )


def _heard(sentence: "_Sentence") -> set[int]:
    """The tokens that a notice or an unmet category rests on.

    What Burro has no measure of, and who lives somewhere, are heard with the
    words said of them: "can I afford it" is one request. The words go as far
    as a mark, a word that joins, a word the grammar does not hold, or a
    thing, a name or a number, which is noticed for itself.
    """
    items = sentence.items
    heard: set[int] = set()
    for at, item in enumerate(items):
        if item.what not in (Is.PEOPLE, Is.AMENITY, Is.UNMET):
            continue
        heard |= set(range(item.first, item.last))
        for step in (-1, 1):
            on = at + step
            while 0 <= on < len(items) and items[on].what in (Is.WORD, Is.GENERIC):
                parted = items[on].apart if step > 0 else items[on + 1].apart
                unknown = items[on].what is Is.WORD and items[on].text not in KNOWN_WORDS
                if parted or unknown or items[on].text in JOINS.words:
                    break
                heard |= set(range(items[on].first, items[on].last))
                on += step
    return heard


_ASKS_NOTHING = by_first_word(ASKS_NOTHING)
_WISHES = by_first_word(WISH.words)
_WISHES_ALONE = by_first_word(WISH_ALONE)
_SPEAKS = by_first_word(SPEAKER.words)
# What says something though each of its words asks for nothing: how much a thing is
# wanted, "a lot", and whose wish it is, "is looking for". Where the words spell one of
# these, it is what they say.
_SAYS_MORE = by_first_word(
    frozenset(
        {
            *(SMALL_STEP | LARGE_STEP | ESSENTIAL | WISHES_OF_ANOTHER | PHRASES_OF_DOUBT),
            *(TURNS | TAKES_OFF | TAKES_OFF_AFTER | TURNS_DOWN | TURNS_DOWN_AFTER | TROUBLES),
            *CAPS_FIRMLY,
        }
    )
)


def _spelt(tokens: Sequence[Token], at: int, phrases: Mapping[str, list[tuple[str, ...]]]) -> int:
    """How many tokens the longest of some phrases takes that the tokens spell from `at`.

    Nothing where they spell none. A phrase is never put together across a mark.
    """
    for words in phrases.get(tokens[at].word, ()):
        run = tokens[at : at + len(words)]
        if tuple(token.word for token in run) == words and not any(t.apart for t in run[1:]):
            return len(words)
    return 0


def _asks_nothing(tokens: Sequence[Token]) -> bool:
    """Whether some words that stand side by side ask for nothing, every one of them.

    They do where each is a phrase of `ASKS_NOTHING`, or a wish that stands
    where the grammar places one: straight after the speaker, "I want", or
    alone where a search is typed, "looking for". A wish that stands anywhere
    else may compare or be another's, and asks for nothing no longer.
    """
    at = 0
    spoke = False
    while at < len(tokens):
        if tokens[at].odd:
            return False
        wished = _spelt(tokens, at, _WISHES if spoke else _WISHES_ALONE)
        size = wished or _spelt(tokens, at, _ASKS_NOTHING)
        if size == 0 or _spelt(tokens, at, _SAYS_MORE) >= size:
            return False
        spoke = not wished and _spelt(tokens, at, _SPEAKS) == size
        at += size
    return True


def asks_for_nothing(words: str) -> bool:
    """Whether some words of a text ask for nothing, every one of them: "I want to live somewhere".

    It is for a caller that holds stretches of the text the reader left
    unread, less the words another reading rests on. What is then left of a
    stretch may ask for nothing, and is not said to be unread.
    """
    lines = lines_of(words)
    return all(_asks_nothing(line.tokens) for line in lines)


def _unread(
    sentences: Sequence["_Sentence"], rested_on: Sequence[_Span]
) -> tuple[tuple[Span, ...], tuple[Span, ...]]:
    """Each stretch of the text that nothing rests on. Two that touch are one.

    Those that may have asked for something come first, and are what is said
    to be unread. Those that hold nothing but words that ask for nothing come
    second, and are not.
    """
    runs: list[list[list[Token]]] = []
    open_run = False
    for sentence in sentences:
        heard = _heard(sentence)
        for index, token in enumerate(sentence.line.tokens):
            read = index in heard or any(
                start <= token.start and token.end <= end for start, end in rested_on
            )
            if read:
                open_run = False
            elif open_run and index > 0:
                runs[-1][-1].append(token)
            elif open_run:
                # A stretch may go on into the next sentence. No phrase does.
                runs[-1].append([token])
            else:
                runs.append([[token]])
                open_run = True
    found: tuple[list[Span], list[Span]] = ([], [])
    for run in runs:
        nothing = all(_asks_nothing(part) for part in run)
        found[nothing].append(Span(start=run[0][0].start, end=run[-1][-1].end))
    return tuple(found[False]), tuple(found[True])


# --- The reader ---------------------------------------------------------------------


def _asks(line: Line, items: Sequence[Item]) -> bool:
    """Whether a sentence asks and does not tell.

    It ends in a question mark, opens with "is", "are" or "am", or puts a verb
    before the speaker: "would I want a pub next door".
    """
    verbs = frozenset(
        {
            *("is", "are", "am", "would", "must", "have", "has", "can", "could", "should"),
            *("do", "does", "will", "shall", "may", "might"),
        }
    )
    turned_about = any(
        _is_word(verb, verbs) and _is_word(who, SPEAKER.words) and not who.apart
        for verb, who in pairwise(items)
    )
    opens = bool(items) and _is_word(items[0], frozenset({"is", "are", "am"}))
    return line.asked or turned_about or opens


# What says that a thing is wanted near, or is to be reached. "By" is not among
# them here: in a sentence the grammar does not make it may say who did a thing.
_NEAR_OR_REACHED = (NEAR_TO - {"by"}) | frozenset({"get to", "reach", "walk to"})
# What may stand between such words and the thing: "close to a good doctor".
_BEFORE_A_THING = ARTICLE.words | GOOD.words


def _no_place(line: Line, items: Sequence[Item], grammar: Grammar) -> list[Item]:
    """The items of a sentence the grammar does not make, less each person read as a place.

    "Doctor" is a person too. In a sentence the grammar makes, it has held
    the word to what says near. In any other, the word is a thing only where
    the words straight beside it say that it is wanted near or is to be
    reached, "she wants to be near a doctor", and is left a word anywhere
    else: "I am a doctor" is offered no surgery.
    """
    found = list(items)
    for at, item in enumerate(items):
        if item.what is not Is.THING or not grammar.known.lexicon[item.text].near_only:
            continue
        back = at
        while back > 0 and _is_word(items[back - 1], _BEFORE_A_THING) and not items[back].apart:
            back -= 1
        led = _after(items, back, _NEAR_OR_REACHED)
        timed = _timed(items, back) and _minutes_before(items, back) > 0
        if not (led or timed or grammar.nearby(items[at + 1 :])):
            token = line.tokens[item.first]
            found[at] = dataclasses.replace(item, what=Is.WORD, text=token.word, bare=token.bare)
    return found


def _sentences(text: str, grammar: Grammar, *, listed: bool = False) -> list[_Sentence]:
    """The sentences of a text. `listed` is what a sentence that names nothing is held to.

    It is said of what stands beside it whatever it holds, for the reader,
    which applies a prompt. For whoever marks what the words give of what
    is only offered, it is said of it only where it holds a word of doubt
    that core lists, or heads a list: `_take_back`.
    """
    found: list[_Sentence] = []
    for line in lines_of(text):
        items = grammar.items(line)
        asked = _asks(line, items)
        try:
            wishes = None if asked else grammar.sentence(line, items)
        except NotPlain:
            wishes = None
        if wishes is None:
            items = _no_place(line, items, grammar)
        found.append(_Sentence(line, items, wishes, asked=asked))
    _take_back(found, listed=listed)
    return found


def _closes(sentence: _Sentence) -> bool:
    """Whether a sentence holds doubt and names nothing: "No thanks.", "I disagree."."""
    return not sentence.plain and not sentence.names


def _take_back(sentences: Sequence[_Sentence], *, listed: bool = False) -> None:
    """A sentence that holds doubt and names nothing is said of what stands beside it.

    "I want a station. Not really." The reader applies nothing of a prompt
    that holds such a sentence. It marks what the sentence is said of all
    the same, for a caller that holds edits the reader did not make: the
    sentence before it, and what is listed beside it, as far as the list goes.

    `listed` is for a caller that marks which way the words give of a thing
    that is only offered. There a sentence that names nothing is said of
    what stands beside it only where it holds a word that core lists as one
    of doubt or as one that turns, "No thanks.", "Not really.", "Things I
    hate", or ends in a colon, which heads what is listed after it:
    "Dealbreakers:". One that holds none is made of words the reader does
    not know, and is as likely said of something else: "Moving next month.
    Somewhere leafy."
    """
    for at, sentence in enumerate(sentences):
        if not _closes(sentence):
            continue
        back = at - 1
        in_doubt = _holds_doubt(sentence) or _holds(sentence, MUST_BE_READ)
        reaches_back = not listed or in_doubt
        heads = not listed or in_doubt or ":" in sentence.line.closed_by
        if reaches_back and back >= 0 and not _closes(sentences[back]):
            sentences[back].taken_back = True
            while (
                back > 0
                and not sentences[back].own
                and not sentences[back - 1].own
                and not _closes(sentences[back - 1])
            ):
                back -= 1
                sentences[back].taken_back = True
        on = at + 1
        while (
            heads and on < len(sentences) and not sentences[on].own and not _closes(sentences[on])
        ):
            sentences[on].taken_back = True
            on += 1


def _names_no_place(items: Sequence[Item], at: int) -> bool:
    """Whether a thing stands where a place was expected, and names none: "I work at uni"."""
    generic = items[at].text.split()[-1] in GENERIC_PLACES
    return generic and _after(items, at, EXPECTS_A_NAME | GOES_TO)


def _asks_for_fewer(sentences: Sequence[_Sentence], grammar: Grammar) -> bool:
    """Whether the words name who lives somewhere and may ask for fewer of them.

    A thing that counts who lives somewhere is offered towards more of what it
    counts. Beside a word that turns, or in a sentence that the next takes
    back, the words may ask for fewer of a group of people. Nothing reads
    that: it is a request about people, and gets the notice and nothing else.
    """
    return any(
        item.what is Is.THING
        and counts_residents(grammar.known.lexicon[item.text])
        and (sentence.taken_back or may_ask_for_fewer(sentence.items, at))
        for sentence in sentences
        for at, item in enumerate(sentence.items)
    )


def _names_a_campus(sentences: Sequence[_Sentence], grammar: Grammar) -> bool:
    """Whether a campus is named, by word or by name.

    In a prompt the reader cannot read, a campus may be what the person wants
    distance from, which is a way to ask for fewer students (contract 8.4).
    """
    release = grammar.release
    for sentence in sentences:
        for at, item in enumerate(sentence.items):
            place = release.place(item.place) if release is not None and item.place else None
            if place is not None and place.kind is PlaceKind.UNIVERSITY:
                return True
            campus = item.what is Is.THING and about_a_campus(grammar.known.lexicon[item.text])
            if campus and not _names_no_place(sentence.items, at):
                return True
    return False


class RuleInterpreter:
    """Reads a request with rules alone. It cannot fail, and it never answers `off_topic`.

    It applies a prompt only when the whole of it is plain. For any other it
    applies nothing, offers what it noticed, and says what it made nothing of.
    It cannot tell an off-topic sentence from one it failed to read, so for
    either it answers `ok` with no edits and `other` among what was unmet.
    """

    name = InterpreterName.RULE

    def __init__(self) -> None:
        # The names and the words of the release last read, so that they are made
        # ready once and not for every request. A release never changes.
        self._grammar: tuple[Release, Grammar] | None = None

    def _grammar_of(self, release: Release) -> Grammar:
        if self._grammar is None or self._grammar[0] is not release:
            self._grammar = (release, Grammar(Names(release), release))
        return self._grammar[1]

    def interpret(self, request: InterpretRequest) -> InterpretResult:
        grammar = self._grammar_of(request.release)
        sentences = _sentences(request.text, grammar)
        if all(sentence.plain for sentence in sentences):
            read = _read([wish for sentence in sentences for wish in sentence.wishes or ()])
            # A house of no kind is a terraced house. Where that has no price, which
            # kind it is is asked.
            asked = _left_to_choose(read) or (
                _for_a_house_of_no_kind(read.home, request.spec)
                and not request.release.costed(Tenure.BUY, DEFAULT_HOUSE)
            )
            two_homes = _of_two_homes(sentences, read.home, request.spec)
            if not _said_both_ways(read) and not asked and not two_homes:
                return self._applied(read, request, sentences)
        return self._suggested(sentences, grammar, request)

    def by_sentence(self, request: InterpretRequest, *, listed: bool = False) -> InterpretResult:
        """What the reader makes of each sentence alone. It is never served as its answer.

        It is for a caller that holds edits the reader did not make to the
        reader's own reading, sentence by sentence: the model-backed
        interpreter. It holds the edits of every sentence that the grammar
        makes and that no sentence beside it takes back, whatever the other
        sentences are. `interpret` applies a prompt whole or not at all, and
        this does not change that: nothing here is applied for the reader.

        `listed` is for a caller that marks which way the words give of what
        is only offered: a sentence that names nothing takes back the one
        before it only where it holds a word of doubt that core lists
        (`_take_back`).
        """
        grammar = self._grammar_of(request.release)
        sentences = _sentences(request.text, grammar, listed=listed)
        heard = self._suggested(sentences, grammar, request)
        known = [s for s in sentences if s.plain and not s.taken_back]
        read = _read([wish for sentence in known for wish in sentence.wishes or ()])
        if not any(isinstance(made.edit, CommuteEdit) for made in read.made):
            # Minutes whose journey stands in a sentence the reader does not
            # know are the limit of nothing here, and take nothing else back.
            read.loose = []
        if _said_both_ways(read):
            read = _Read(unmet=read.unmet, about_people=read.about_people)
        elif _of_two_homes(known, read.home, request.spec):
            # Nobody can say which of two sizes or kinds is meant, so neither is the
            # reader's reading. What else was said is as plainly said as it was: the
            # amount beside them, the tenure, a wish.
            read.home.bedrooms, read.home.segments, read.home.houses = [], [], []
        found = self._applied(read, request, known)
        if len(known) == len(sentences):
            return found
        # What was heard in the sentences it does not know is said all the same.
        about_people = read.about_people or heard.notice is Notice.NEUTRAL_PLACES
        unmet = {*found.unmet, *heard.unmet}
        return found.replace(
            status=InterpretStatus.POLICY_REDIRECT if about_people else found.status,
            notice=Notice.NEUTRAL_PLACES if about_people else Notice.NONE,
            unmet=tuple(category for category in UnmetCategory if category in unmet),
            unread=heard.unread,
            asks_nothing=heard.asks_nothing,
        )

    def _applied(
        self, read: _Read, request: InterpretRequest, sentences: Sequence[_Sentence] = ()
    ) -> InterpretResult:
        """A plain prompt: every item makes the edit the contract gives it.

        `sentences` are those of the prompt, where it is applied as the
        answer: what they say of a home that the search cannot hold is said
        in the answer, beside the edits.
        """
        made = list(read.made)
        # What was named outright is read before what was only implied, so that
        # "safe, with low crime" is the explicit request its second half makes it.
        made.sort(key=lambda m: getattr(m.edit, "provenance", _STATED) is _INFERRED)
        groups: dict[OpsGroup, list[_Made]] = {group: [] for group in OpsGroup}
        budget = _budget(read.home, request.spec)
        # The kind of house that Burro took, where a house of no kind was named.
        took = _for_a_house_of_no_kind(read.home, request.spec)
        if budget is not None and took:
            edit, spans = budget
            kind = SegmentChoice(DEFAULT_HOUSE.value)
            budget = edit.replace(segment=kind), sorted({*spans, *read.home.houses})
        if budget is not None:
            where = read.home.amounts[0][2] if read.home.amounts else None
            groups[OpsGroup.BUDGET] += [
                _Made(OpsGroup.BUDGET, edit, spans, kind_assumed=took and bool(edit.amount))
                for edit, spans in _as_can_be_tested(*budget, where, request)
            ]
        # What is said of a home that the search cannot hold, "a 3 bed" of a home to
        # buy, was passed over in silence: no edit, no offer, nothing unread. It is
        # said in the words of an offer, with nothing to choose. The status of the
        # prompt is as it was: it would say whether the search is to rent or to buy,
        # and a status is kept about a call (contract, section 10.1).
        rested = [span for found in groups[OpsGroup.BUDGET] for span in found.spans]
        tenure = _tenure_of(read.home, request.spec)
        not_held = _not_held_of(sentences, read.home, tenure, rested)
        if tenure is Tenure.VISIT:
            # Nor does a visit weigh what homes sold for. It is said so, and no edit is made.
            sold = [found for found in made if _weighs_what_homes_sold_for(found.edit)]
            made = [found for found in made if found not in sold]
            not_held = (*not_held, *_not_weighed(sold))
        # A home of which no edit can be made and nothing is said is unread, as it was:
        # "a flat", typed by a renter.
        named = bool(read.home.bedrooms or read.home.segments)
        passed_over = budget is None and named and not not_held
        unread = sorted(set(read.home_spans)) if passed_over else []
        unmet = read.unmet | ({UnmetCategory.OTHER} if unread else set[UnmetCategory]())
        seen: set[tuple[OpsGroup, str]] = set()
        for found in made:
            about = _about(found)
            if about[1] and about in seen:
                continue
            seen.add(about)
            # "A 40 minute commute", said apart from any place, is the limit
            # of each journey of the prompt.
            groups[found.group].append(_with_loose(found, read.loose))
        edits = [found.edit for listed in groups.values() for found in listed]
        operations = Operations(
            budget_ops=tuple(edit for edit in edits if isinstance(edit, BudgetEdit)),
            commute_ops=tuple(edit for edit in edits if isinstance(edit, CommuteEdit)),
            weight_ops=tuple(edit for edit in edits if isinstance(edit, WeightEdit)),
            tag_ops=tuple(edit for edit in edits if isinstance(edit, TagEdit)),
            area_ops=tuple(edit for edit in edits if isinstance(edit, AreaEdit)),
            setting_ops=(),
        )
        indexed = [
            (group, index, found)
            for group, listed in groups.items()
            for index, found in enumerate(listed)
        ]
        # A question offers places to choose from, or a field to look one up
        # in. A release that names no place has neither, so nothing is asked:
        # the reducer turns the journey away, as not in the release.
        clarify = tuple(
            Clarify(group=group, index=index, options=found.options)
            for group, index, found in indexed
            if found.options is not None and request.release.places
        )
        quoted = tuple(
            Assumption(code=AssumptionCode.WORD, group=group, index=index, word=found.word)
            for group, index, found in indexed
            if found.word
        )
        # Of a range of minutes the longer was taken. The person gave two numbers
        # and the search holds one, so it is said to be assumed.
        ranged = tuple(
            Assumption(code=AssumptionCode.MAX_MINUTES, group=group, index=index)
            for group, index, found in indexed
            if found.at_least
        )
        # Of a house of no kind a terraced house was taken. The person named no kind,
        # so it is said to be assumed.
        housed = tuple(
            Assumption(code=AssumptionCode.SEGMENT, group=group, index=index)
            for group, index, found in indexed
            if found.kind_assumed
        )
        if read.about_people:
            status = InterpretStatus.POLICY_REDIRECT
        elif clarify:
            status = InterpretStatus.CLARIFY
        else:
            status = InterpretStatus.OK
        return InterpretResult(
            status=status,
            operations=operations,
            assumptions=(*assumptions_for(operations, request.spec), *ranged, *housed, *quoted),
            # In the order the categories are listed, whatever order they were heard in.
            unmet=tuple(category for category in UnmetCategory if category in unmet),
            clarify=clarify,
            notice=Notice.NEUTRAL_PLACES if read.about_people else Notice.NONE,
            interpreter=self.name,
            degraded=False,
            usage=NO_USAGE,
            rests_on=tuple(
                RestsOn(group=group, index=index, start=start, end=end)
                for group, index, found in indexed
                for start, end in sorted(found.spans)
            ),
            suggestions=not_held,
            unread=tuple(Span(start=start, end=end) for start, end in unread),
        )

    def _suggested(
        self, sentences: Sequence[_Sentence], grammar: Grammar, request: InterpretRequest
    ) -> InterpretResult:
        """A prompt that is not plain: nothing is applied, and what was noticed is offered.

        A place the release does not hold, named where the grammar expects a
        place, is asked about all the same. The question is an edit that
        carries no place, so it adds nothing to the search until the person
        says which place was meant.
        """
        journeys = _journeys_made(sentences, grammar)
        asked = self._applied(_Read(made=[j for j in journeys if j.options is not None]), request)
        items = [item for sentence in sentences for item in sentence.items]
        about_people = (
            any(item.what is Is.PEOPLE for item in items)
            or _names_a_campus(sentences, grammar)
            or _asks_for_fewer(sentences, grammar)
        )
        notices = _Notices(request.release, grammar, request.spec, about_people)
        noticed = notices.of(sentences, journeys)
        suggestions, already, missing = _offered(noticed, request.spec, request.release)
        # What is offered, what is said to be missing and what is asked about were all heard.
        rested_on = [
            (span.start, span.end) for found in (*suggestions, *missing) for span in found.spans
        ]
        rested_on += [(rests.start, rests.end) for rests in asked.rests_on]
        # So was what a night costs, which is what a place charges and is no budget.
        nightly = _by_the_night(sentences)
        heard = [*rested_on, *already, *nightly, *notices.heard]
        unread, asks_nothing = _unread(sentences, heard)
        unmet = {item.unmet for item in items if item.unmet is not None}
        if nightly:
            unmet.add(UnmetCategory.PRICES_AND_HOURS)
        # What Burro cannot say of a thing it offers what is nearest for.
        things = [grammar.known.lexicon[item.text] for item in items if item.what is Is.THING]
        unmet |= {thing.unmet for thing in things if thing.note and thing.unmet is not None}
        if any(item.what is Is.AMENITY for item in items):
            unmet.add(UnmetCategory.COMMUNITY_AMENITIES)
        if unread or asks_nothing:
            unmet.add(UnmetCategory.OTHER)
        if about_people:
            status = InterpretStatus.POLICY_REDIRECT
        elif asked.clarify:
            status = InterpretStatus.CLARIFY
        elif suggestions:
            status = InterpretStatus.SUGGEST
        else:
            status = InterpretStatus.OK
        return InterpretResult(
            status=status,
            operations=asked.operations,
            assumptions=asked.assumptions,
            unmet=tuple(category for category in UnmetCategory if category in unmet),
            clarify=asked.clarify,
            notice=Notice.NEUTRAL_PLACES if about_people else Notice.NONE,
            interpreter=self.name,
            degraded=False,
            usage=NO_USAGE,
            rests_on=asked.rests_on,
            suggestions=suggestions,
            unread=unread,
            asks_nothing=asks_nothing,
            not_in_release=missing,
        )


# --- For a caller that holds edits the reader did not make ----------------------------


class SentenceRead(NamedTuple):
    """A sentence of a request as the reader sees it. It holds no word of it, only where it is."""

    start: int
    end: int
    # The grammar makes the whole of it, it does not ask, and no sentence beside
    # it takes it back. An edit the reader made rests on words of such a sentence.
    known: bool
    # It holds a word that turns, takes off, caps or confines: "no", "less",
    # "don't care about", "within", "only".
    turning: bool
    # It holds a word of the written list of doubt, or a token with a mark inside it.
    doubt: bool
    # It asks and does not tell.
    asked: bool
    # A sentence beside it, which holds doubt and names nothing, is said of it.
    taken_back: bool


def _holds(sentence: _Sentence, phrases: frozenset[str], longest: int = 4) -> bool:
    """Whether a sentence holds one of some phrases, word for word and side by side."""
    tokens = sentence.line.tokens
    for at in range(len(tokens)):
        for size in range(1, longest + 1):
            run = tokens[at : at + size]
            if len(run) == size and not any(token.apart for token in run[1:]):
                spelt = (" ".join(t.word for t in run), " ".join(t.bare for t in run))
                if spelt[0] in phrases or spelt[1] in phrases:
                    return True
    return False


def _holds_doubt(sentence: _Sentence) -> bool:
    odd = any(token.odd for token in sentence.line.tokens)
    return odd or _holds(sentence, WORDS_OF_DOUBT | PHRASES_OF_DOUBT)


def sentences_of(
    text: str, names: Names | None = None, release: Release | None = None
) -> tuple[SentenceRead, ...]:
    """The sentences of a request, and which of them the reader could read.

    It is the reader's own reading, for a caller that must hold edits the
    reader did not make to the same test (the model-backed interpreter). The
    offsets count the characters of the text as it was typed.
    """
    return tuple(
        SentenceRead(
            start=sentence.line.start,
            end=sentence.line.end,
            known=sentence.plain and not sentence.taken_back,
            turning=_holds(sentence, MUST_BE_READ),
            doubt=_holds_doubt(sentence),
            asked=sentence.asked,
            taken_back=sentence.taken_back,
        )
        for sentence in _sentences(text, Grammar(names, release))
    )


def known_in(text: str, grammar: Grammar) -> tuple[Span, ...]:
    """Where the sentences stand that the reader reads, each by itself.

    The grammar makes the whole of each, it does not ask, and no sentence
    beside it takes it back (`_take_back`). It is for a caller that marks
    what the words give of a thing that is only offered:
    `by_sentence` gives one edit for a thing however often it is named, so
    which of the places a thing stands in were read is said here.
    """
    return tuple(
        Span(start=sentence.line.start, end=sentence.line.end)
        for sentence in _sentences(text, grammar, listed=True)
        if sentence.plain and not sentence.taken_back
    )


# Every word that puts a sentence in doubt for a caller that holds a model's edits
# to the rules: the written list, and the words that turn a wish away.
SIGNS_OF_DOUBT: frozenset[str] = (
    WORDS_OF_DOUBT | PHRASES_OF_DOUBT | TURNS | TROUBLES | frozenset({"anywhere but"})
)
