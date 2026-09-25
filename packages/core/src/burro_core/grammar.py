"""The grammar of a plain prompt: a list of things wanted or not wanted, and no more.

The rule-based reader applies a prompt only when the whole of it is made by
this grammar. One token the grammar does not place makes the whole prompt not
plain, whichever sentence it stands in, and nothing is then applied, not even
a budget. It is all or nothing, because no single word is ever the fault:
"pubs are so noisy" is made of words that are each harmless.

    prompt    = sentence { stop sentence } [ stop ]
    sentence  = courtesy | [ opening ] item { joiner [ opening ] item } [ close ]
    opening   = [ speaker [ wish ] [ to-do ] ] [ somewhere [ that ] ]
    joiner    = "," | ";" | "and" | "or" | "but" | "plus" | "also" | "with"
    item      = want | unwant | home | journey | rule | people | no-measure
    want      = [ near ] { degree | good | article } thing [ place ] [ nearby ] [ counts ]
    unwant    = turn { article | good } thing [ place ] [ nearby ] | thing after-turn
    home      = { tenure | size | budget | cheaper }
    journey   = cue place [ mode ] | time to place [ mode ] | reach place [ time ] [ mode ]
              | near place | "to get there" time [ mode ]
    rule      = ( not-in | only-in ) the whole name of an area

The words of each part are in `vocabulary.py`, and a thing is a phrase of the
lexicon. `home` and `journey` are wide, because they are made of numbers,
names of the release and closed lists of words. `thing` is narrow.

Nothing here makes an edit. It says what each part of a plain prompt is, and
where in the text it stands.
"""

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple

from burro_core.catalogue import FEATURES, HOLDS_CRIME
from burro_core.ids import (
    AreaAction,
    DirectionChoice,
    EditProvenance,
    FeatureId,
    GrittyVariant,
    ModeChoice,
    SegmentChoice,
    Step,
    UnmetCategory,
)
from burro_core.lexicon import (
    GENERIC_PLACES,
    Target,
    counts_residents,
    lexicon_of,
    no_measure_of,
)
from burro_core.places import MAX_OPTIONS, Match, Names
from burro_core.reading import (
    COUNTED,
    JOINING_MARKS,
    MINUTES,
    Is,
    Item,
    Line,
    Tables,
    by_first_word,
    items_of,
    tables,
)
from burro_core.release import Release
from burro_core.vocabulary import (
    ARTICLE,
    ASKS_BURRO,
    AT_THE_END,
    CAPS,
    CAPS_FIRMLY,
    COURTESY,
    ESSENTIAL,
    FIRM_OF_MINUTES,
    FIRM_OF_MONEY,
    FOR_WHOM,
    GOOD,
    IMPORTANT,
    JOINS,
    LARGE_STEP,
    NEAR_TO,
    NEARBY,
    NOT_IN,
    ONLY_IN,
    PLACE_NOUN,
    PLAIN_WORDS,
    SMALL_STEP,
    SOFTLY,
    SOMEWHERE,
    SOMEWHERE_THAT,
    SPEAKER,
    STRENGTHENS,
    TAKES_OFF,
    TAKES_OFF_AFTER,
    TO_DO,
    TROUBLES,
    TURNS_DOWN,
    TURNS_DOWN_AFTER,
    TURNS_FIRMLY,
    TURNS_SOFTLY,
    WHOSE,
    WISH,
    WISH_ALONE,
)

MAX_NAME_WORDS = 6
# No rent and no price is this low, so a smaller number that has no sign of money on
# it is a number of things, "at most 2 pubs", which is no limit the reader sets.
LEAST_MONEY = 100

# Words that expect the name of a place to follow. The speaker does the working:
# "works at" and "worked at" are not here, so another's workplace and a former
# one are never read.
_WORKS = ("work", "working", "based", "study", "studying")
# Where the speaker works, said before the name of the place: "30 minutes from work
# at", "not far from my office in". The place is still the whole of a name.
AT_WORK = frozenset(
    f"{whose}{noun} {where}"
    for whose in ("", "my ", "our ", "the ")
    for noun in ("work", "office", "job")
    for where in ("at", "in")
)
# A person commutes from where they live, to where they work. One who is choosing
# where to live may say it of where they work all the same, so the place is heard
# as one that may be meant to be reached: it is offered, and never applied. With a
# time before it, "a 40 minute commute from", the place is one to reach, and that
# is read by the minutes and not by these.
COMMUTES_FROM = frozenset(f"{verb} from" for verb in ("commute", "commuting"))
EXPECTS_A_NAME = frozenset(
    {
        *(f"{verb} {where}" for verb in _WORKS for where in ("at", "in", "near")),
        # A job the speaker has, in the present tense, is where the speaker works.
        *(f"have a job {where}" for where in ("at", "in", "near")),
        *(f"{verb} to" for verb in ("commute", "commuting", "travel", "travelling")),
        *COMMUTES_FROM,
        *(f"from {at_work}" for at_work in AT_WORK),
        *(f"{how} commute to" for how in ("easy", "short", "quick")),
        *(
            f"{near} {whose}work {where}"
            for near in ("near", "close to")
            for whose in ("my ", "")
            for where in ("at", "in")
        ),
        *(
            f"{whose}{noun} {verb}{where}"
            for whose in ("", "my ", "our ")
            for noun in ("office", "job")
            for verb in ("", "is ")
            for where in ("at", "in", "near")
        ),
    }
)
CYCLED = frozenset({"cycle", "cycling", "bike", "biking", "bicycle", "by bike", "by bicycle"})
WALKED = frozenset({"walk", "walking", "on foot"})
BY_TRANSPORT = frozenset(
    {
        *(f"by {what}" for what in ("tube", "train", "bus", "tram", "public transport")),
        *("tube", "train", "bus", "tram", "underground", "overground", "public transport"),
    }
)
MODES = CYCLED | WALKED | BY_TRANSPORT
# A journey that is said with how it is made: "I cycle to", "a 20 minute walk to".
GOES: Mapping[str, ModeChoice] = {
    **dict.fromkeys(("cycle", "cycling", "bike", "bike ride", "ride"), ModeChoice.CYCLE),
    **dict.fromkeys(("walk", "walking"), ModeChoice.WALK),
    **dict.fromkeys(("commute", "commuting", "journey", "trip", "travel"), ModeChoice.UNCHANGED),
}
GOES_TO = frozenset(
    f"{verb} to{work}"
    for verb in ("cycle", "cycling", "walk", "walking")
    for work in ("", " work at", " work in")
)
REACHES = frozenset({"get to", "reach", "to get to", "to reach", "be in", "to be in"})
GETS_THERE = frozenset({"to get there", "get there", "to be there", "be there"})
TO_A_PLACE = frozenset({"to", "from", "of"})
A_JOURNEY = frozenset({"commute", "journey"})
# A length of time in words, in minutes.
HOURS: Mapping[str, int] = {
    "half an hour": 30,
    "an hour": 60,
    "one hour": 60,
    "1 hour": 60,
    "an hour and a half": 90,
}
# What says a number is the most, after it: "30 minutes max", "20 minutes tops".
_AT_MOST = frozenset({"max", "maximum", "tops"})
# What may stand between a word that caps and its number: "within about 30
# minutes", "up to around £1,500". The number is still the most it may be.
_OR_SO = frozenset({"about", "around"})
RENTS = frozenset({"rent", "renting", "rental", "tenancy", "to rent", "to let", "renter"})
BUYS = frozenset(
    {
        *("buy", "buying", "purchase", "purchasing", "mortgage", "to buy", "for sale"),
        *("buyer", "first time buyer"),
    }
)
_NOT_TO_RENT = frozenset(f"not {word}" for word in RENTS)
_NOT_TO_BUY = frozenset(f"not {word}" for word in BUYS)
BEDROOMS = frozenset({"bed", "beds", "bedroom", "bedrooms", "bedroomed"})
MONTHLY = frozenset({"pcm", "pm", "per month", "a month", "monthly", "per calendar month"})
IN_MONEY = frozenset({"pounds", "quid"})
# A thousand pounds, after a number: "2 grand".
THOUSANDS = frozenset({"grand"})
PAYS = frozenset(
    {
        *(f"{can}{verb}" for can in ("", "can ") for verb in ("pay", "spend", "stretch to")),
        *(
            f"{whose}budget{verb}"
            for whose in ("", "my ", "our ", "a ", "the ")
            for verb in ("", " is", " of")
        ),
    }
)
RENT_SEGMENTS: Mapping[str, SegmentChoice] = {
    "studio": SegmentChoice.STUDIO,
    # "Room" by itself is also space, "room for a desk", so it is known with its article.
    "a room": SegmentChoice.ROOM,
    "room to rent": SegmentChoice.ROOM,
    "flatshare": SegmentChoice.ROOM,
    "flat share": SegmentChoice.ROOM,
    "house share": SegmentChoice.ROOM,
    "houseshare": SegmentChoice.ROOM,
}
BUY_SEGMENTS: Mapping[str, SegmentChoice] = {
    "flat": SegmentChoice.FLAT,
    "apartment": SegmentChoice.FLAT,
    "maisonette": SegmentChoice.FLAT,
    "terraced": SegmentChoice.TERRACED,
    "terrace": SegmentChoice.TERRACED,
    "semi detached": SegmentChoice.SEMI_DETACHED,
    "semi": SegmentChoice.SEMI_DETACHED,
    "detached": SegmentChoice.DETACHED,
}
# What a home is called after its size or its kind: "a one bed flat", "a terraced house".
A_HOME = frozenset(
    {
        *("flat", "house", "home", "place", "apartment", "property"),
        *("flats", "houses", "homes", "apartments", "properties"),
    }
)
# What is said before a thing to give it more weight, and says nothing else.
WEIGHT_ON = frozenset({"weight on", "emphasis on"})
_AT_THE_HEAD = frozenset({"need", "want"})
_SOMEWHERE_NOUNS = frozenset({"area", "place", "neighbourhood", "neighborhood", "location"})
# What opens a sentence that says how much the wish before it counts: "it's the
# most important thing".
_IT_IS = frozenset({"it's", "it is", "that's", "that is"})
# What follows a word for essential before a thing: "the most important thing is parks".
_THING_IS = frozenset({"thing is", "is", "thing for us is", "thing for me is"})
# What stands between the parts of a budget and says nothing: "a flat for £1,500".
_GLUE = frozenset(
    {
        *("for", "at", "of", "is", "on", "with", "a", "an", "the", "my", "our"),
        *("looking for", "i can get", "we can get"),
    }
)
CHEAPER = frozenset({"cheaper", "less expensive", "lower budget", "lower my budget"})
DEARER = frozenset(
    {"raise my budget", "increase my budget", "stretch my budget", "raise the budget"}
)
# What may stand before a name: "the Clinkers", "my office".
_BEFORE_A_NAME = frozenset({"the", "a", "an", "my", "our"})
# The words a phrase of the lexicon may open with that are said of the thing, so
# that the phrase is more than a bare name.
_OWN_WORDS = GOOD.words | frozenset(
    {"near", "close", "nearer", "cleaner", "higher", "lower", "fewer", "more", "less", "away"}
)
# The words that turn a thing and say near of it.
_NOT_NEAR = frozenset({"not near", "not close to"})
# What says that a thing counts, after the thing: "is important", "would be good".
_IS = frozenset({"is", "are"})
_WOULD_BE = frozenset({"would be"})

TURNS = TURNS_FIRMLY | TURNS_SOFTLY
# Every word that turns, takes off or caps. It is what a caller that holds a
# model's edits asks of a sentence: whether it holds a word of these.
MUST_BE_READ = (
    TURNS
    | TAKES_OFF
    | TAKES_OFF_AFTER
    | TURNS_DOWN
    | TURNS_DOWN_AFTER
    | TROUBLES
    | CAPS_FIRMLY
    | CAPS
    | ONLY_IN
    | NOT_IN
    | (NEAR_TO - {"near", "near to", "close to", "next to"})
    | CHEAPER
    | DEARER
)
# Every phrase the grammar places, besides the lexicon and the names.
VOCABULARY: frozenset[str] = frozenset(
    {
        *PLAIN_WORDS,
        *AT_THE_END,
        *MUST_BE_READ,
        *SMALL_STEP,
        *LARGE_STEP,
        *ESSENTIAL,
        *NEAR_TO,
        *EXPECTS_A_NAME,
        *AT_WORK,
        *GOES_TO,
        *GOES,
        *REACHES,
        *GETS_THERE,
        *TO_A_PLACE,
        *A_JOURNEY,
        *MINUTES,
        *BEDROOMS,
        *MONTHLY,
        *IN_MONEY,
        *MODES,
        *RENTS,
        *BUYS,
        *_NOT_TO_RENT,
        *_NOT_TO_BUY,
        *PAYS,
        *RENT_SEGMENTS,
        *BUY_SEGMENTS,
        *A_HOME,
        *_GLUE,
        *COUNTED,
        *_IS,
        *_WOULD_BE,
        *WEIGHT_ON,
        *_THING_IS,
        *HOURS,
        *_AT_MOST,
        *THOUSANDS,
        *_IT_IS,
        "thing",
        "like me",
        "like us",
        "full of",
        "it",
    }
)
# Every single word that some phrase of the grammar holds. A word that is none
# of these, after words that expect a name, is what the person calls a place.
KNOWN_WORDS: frozenset[str] = frozenset(word for phrase in VOCABULARY for word in phrase.split())


class Join(Enum):
    """How an item is joined to the item before it."""

    FIRST = "first"
    MARK = "mark"  # a comma or a semicolon
    AND = "and"  # and, plus, also, with
    OR = "or"
    BUT = "but"


class Way(Enum):
    """What is said of a thing by a word that turns."""

    NONE = "none"
    NOT_AT_ALL = "not at all"
    LESS = "less"
    OFF = "off"  # said of the weight: "I don't care about"
    DOWN = "down"  # said of the weight: "I care less about"
    TROUBLED = "troubled"  # "I worry about", read of a nuisance alone


class Kind(Enum):
    WISH = "wish"  # a thing wanted, or turned away
    HOME = "home"  # to rent or to buy, what kind of home, and what it may cost
    JOURNEY = "journey"
    RULE = "rule"
    PEOPLE = "people"  # who lives somewhere: no edit, and the notice
    NO_MEASURE = "no measure"  # what Burro has no measure of: no edit, and its category
    NOTHING = "nothing"  # courtesy, or an opening with nothing after it


_WAY_OF: Mapping[Way, frozenset[str]] = {
    Way.NOT_AT_ALL: TURNS_FIRMLY,
    Way.LESS: TURNS_SOFTLY,
    Way.OFF: TAKES_OFF,
    Way.DOWN: TURNS_DOWN,
    Way.TROUBLED: TROUBLES,
}
_WAY_AFTER: Mapping[Way, frozenset[str]] = {Way.OFF: TAKES_OFF_AFTER, Way.DOWN: TURNS_DOWN_AFTER}
_BEFORE_A_THING = _WAY_OF[Way.NOT_AT_ALL] | TURNS_SOFTLY | TAKES_OFF | TURNS_DOWN | TROUBLES
_JOIN_OF: Mapping[str, Join] = {
    "and": Join.AND,
    "plus": Join.AND,
    "also": Join.AND,
    "with": Join.AND,
    "or": Join.OR,
    "but": Join.BUT,
}
assert set(_JOIN_OF) == set(JOINS.words)

Span = tuple[int, int]


@dataclass
class Home:
    """What a prompt says of the home and what it costs. One budget edit is made of it all."""

    rents: list[Span] = field(default_factory=list[Span])
    buys: list[Span] = field(default_factory=list[Span])
    monthly: list[Span] = field(default_factory=list[Span])
    # The amount, whether it is a limit, and where it stands.
    amounts: list[tuple[int, bool, Span]] = field(default_factory=list[tuple[int, bool, Span]])
    bedrooms: list[tuple[int, Span]] = field(default_factory=list[tuple[int, Span]])
    segments: list[tuple[str, Span]] = field(default_factory=list[tuple[str, Span]])
    # Cheaper or dearer, by a little or a lot.
    steps: list[tuple[bool, bool, Span]] = field(default_factory=list[tuple[bool, bool, Span]])
    # The tenure that is said not to be wanted: "to buy, not rent". It is read
    # only beside the other, which it agrees with.
    not_rents: list[Span] = field(default_factory=list[Span])
    not_buys: list[Span] = field(default_factory=list[Span])
    # Where an amount stands that was typed with an "m" and no pound sign, "5m",
    # "1.5m", in a part of the sentence that says nothing else of a home or of
    # money. It is as likely minutes, metres or miles, whatever caps it.
    by_an_m: list[Span] = field(default_factory=list[Span])

    @property
    def said(self) -> bool:
        return bool(self.amounts or self.of_a_home)

    @property
    def of_a_home(self) -> bool:
        """Whether it says something of a home that is no amount: to rent or buy, a size, a kind."""
        tenure = self.rents or self.buys or self.not_rents or self.not_buys
        return bool(tenure or self.steps or self.bedrooms or self.segments)

    @property
    def agrees(self) -> bool:
        """Whether what it says of renting and buying can all be true at once."""
        rent = bool(self.rents or self.not_buys)
        buy = bool(self.buys or self.not_rents)
        # A tenure that is only turned away says nothing of what is wanted.
        alone = (self.not_rents and not self.buys) or (self.not_buys and not self.rents)
        return not (rent and buy) and not alone

    def add(self, other: "Home") -> None:
        for name in ("rents", "buys", "monthly", "amounts", "bedrooms", "segments", "steps"):
            getattr(self, name).extend(getattr(other, name))
        self.by_an_m.extend(other.by_an_m)
        self.not_rents.extend(other.not_rents)
        self.not_buys.extend(other.not_buys)


@dataclass
class Wish:
    """One item of a plain prompt: what it is, and where in the text it stands."""

    kind: Kind
    spans: list[Span]
    join: Join = Join.FIRST
    # The speaker opens it with a wish of their own: "I want", "we need".
    own: bool = False
    # A thing of the lexicon, and what is said of it.
    phrase: str = ""
    target: Target | None = None
    way: Way = Way.NONE
    step: Step = Step.UP_LARGE
    essential: bool = False
    large: bool = False
    # Nothing is said of the thing but its name, so a turn before it may reach it.
    bare: bool = False
    # Something said before the thing makes it a wish of its own: that it is
    # wanted near, how much it is wanted, a good word, or a word of the
    # phrase's own. What is said after a thing never does: "nearby" and "is
    # important" may be said of every thing of a list.
    led: bool = False
    # It is said to count, or not to, after the thing: "is important", "would be good".
    counted_after: bool = False
    # It may not be applied for what it is: a word Burro has no measure of, or
    # one that is only read into a vibe that holds recorded crime. It makes no
    # edit. It is plain only beside a wish that names the same thing outright,
    # "safe, with low crime", and is offered anywhere else.
    offered: bool = False
    # What turns it is said after it: "parks are not important".
    turned_after: bool = False
    # It opens with words that say near: "not far from", "within 10 minutes of".
    led_by_near: bool = False
    # Something says the thing is wanted near, before it, "close to a doctor", "not
    # near a doctor", or after it: "a doctor nearby", "a doctor within a ten minute walk".
    near_before: bool = False
    near_after: bool = False
    # The speaker opens it and says no wish, "I'm", "we are": what follows may say
    # who the speaker is.
    of_the_speaker: bool = False
    # It is said to count, and not to be liked: "I care about", "matters to me".
    # "Is essential" and "is a must" are not that: they may say it is wanted.
    counts: bool = False
    home: Home = field(default_factory=Home)
    # A journey: the place, or the words that were given as its name and are the
    # name of none, with what to offer for them.
    place_id: str = ""
    options: tuple[Match, ...] | None = None
    minutes: int = 0
    # The minutes were given as a range, "35-40 minutes", of which `minutes` is the
    # longer. This is the shorter, and nothing where they were no range.
    at_least: int = 0
    firm: bool = False
    mode: ModeChoice = ModeChoice.UNCHANGED
    # The minutes are said of the place named earlier in the sentence: "to get there".
    there: bool = False
    # Minutes said apart from any place: "a 40 minute commute".
    loose: bool = False
    # They are said with no word for a journey, so they need one beside them.
    beside: bool = False
    action: AreaAction = AreaAction.EXCLUDE
    area_id: str = ""
    unmet: tuple[UnmetCategory, ...] = ()


class NotPlain(Exception):
    """A prompt, or a part of one, that the grammar does not make."""


class Time(NamedTuple):
    """A length of time as it was said: its minutes, and whether they are a limit."""

    minutes: int
    firm: bool
    # The shorter of a range of minutes, of which `minutes` is the longer. Nothing
    # where no range was given.
    at_least: int = 0


_BY_FIRST: dict[frozenset[str], Mapping[str, list[tuple[str, ...]]]] = {}


def _by_first(options: frozenset[str]) -> Mapping[str, list[tuple[str, ...]]]:
    """Some phrases by the word each begins with. It is worked out once for each set."""
    found = _BY_FIRST.get(options)
    if found is None:
        found = _BY_FIRST[options] = by_first_word(options)
    return found


def _span(items: Sequence[Item]) -> Span:
    return (items[0].start, items[-1].end)


class _Segment:
    """One part of a sentence, between two joiners, read from left to right."""

    def __init__(self, items: Sequence[Item], reader: "Grammar") -> None:
        self.items = items
        self.reader = reader
        self.at: int = 0
        # The speaker opens it: "I", "we".
        self.spoke = False
        # The wishes that may open it with no speaker. At the head of a sentence
        # "need" and "want" can only be the speaker's: "Need to be near a park".
        self.unspoken: frozenset[str] = frozenset()
        # The speaker says the thing counts, which is not to say they like it:
        # "I care about", "matters to me".
        self.cares = False

    @property
    def done(self) -> bool:
        return self.at >= len(self.items)

    def peek(self, offset: int = 0) -> Item | None:
        at = self.at + offset
        return self.items[at] if at < len(self.items) else None

    def phrase(self, options: Collection[str], at: int | None = None) -> list[Item] | None:
        """The longest of some phrases that the words spell from here, if any does."""
        start = self.at if at is None else at
        first = self.items[start] if start < len(self.items) else None
        if first is None or first.what not in (Is.WORD, Is.NUMBER) or not first.text:
            return None
        if "-" in first.text:
            # Written with a hyphen, it is a phrase only as a whole: "semi-detached".
            return [first] if first.bare in options else None
        table = _by_first(options if isinstance(options, frozenset) else frozenset(options))
        for words in table.get(first.text, ()):
            run = self.items[start : start + len(words)]
            if len(run) == len(words) and all(
                found.what in (Is.WORD, Is.NUMBER) and found.text == word
                for found, word in zip(run, words, strict=True)
            ):
                return list(run)
        return None

    def take(self, options: Collection[str]) -> list[Item] | None:
        found = self.phrase(options)
        if found is not None:
            self.at += len(found)
        return found

    def take_all(self, *groups: Collection[str]) -> list[Item]:
        """Every phrase of some groups that stands here, one after another."""
        taken: list[Item] = []
        while True:
            found = next((f for g in groups if (f := self.take(g)) is not None), None)
            if found is None:
                return taken
            taken += found

    def take_a(self, what: Is) -> Item | None:
        found = self.peek()
        if found is None or found.what is not what:
            return None
        self.at += 1
        return found

    # The opening.

    def opening(self, spoken: bool = False) -> bool:
        """The words a wish is opened with. Whether the speaker says a wish of their own.

        `spoken` is whether the speaker has opened an earlier part of the
        sentence, so that a wish may follow with no speaker of its own: "I
        rent and want a park".
        """
        wish = None
        if self.take(ASKS_BURRO.words) is None and self.take(SPEAKER.words) is not None:
            self.spoke = True
            at = self.at
            self.take_all(STRENGTHENS.words, SOFTLY)
            wish = self.take(WISH.words)
            if wish is None and (would := self.take({"would"})) is not None:
                # "We would really like", "I would quite like": how much the
                # speaker wishes may stand inside the wish.
                self.take_all(STRENGTHENS.words, SOFTLY)
                wish = self.take({"like", "love", "want"})
                if wish is None:
                    self.at -= len(would)
            if wish is None:
                # With no wish after it, it is said of what follows: "I quite leafy" is nothing.
                self.at = at
                self.take_all(STRENGTHENS.words)
        else:
            wish = self.take(WISH.words if spoken else WISH_ALONE | self.unspoken)
        own = wish is not None
        self.cares = wish is not None and _said(wish) == "care about"
        if own:
            self.take_all(STRENGTHENS.words)
        if self.take(TO_DO.words) is None and self.phrase({"to"}) and self._to_something():
            self.at += 1
        if self.take(SOMEWHERE.words) is not None or self._a_good_place():
            self.take(SOMEWHERE_THAT.words)
        return own

    def _a_good_place(self) -> bool:
        """ "A nice neighbourhood", "a lovely quiet area": a place, with a good word for it."""
        start = self.at
        good = self.take({"a", "an"}) is not None and self.take_all(GOOD.words)
        if good and self.take(PLACE_NOUN.words & _SOMEWHERE_NOUNS) is not None:
            return True
        self.at = start
        return False

    def _to_something(self) -> bool:
        """Whether "to" opens what the speaker wishes to do: "to avoid", "to get to", "to rent"."""
        after = self.at + 1
        return any(
            self.phrase(group, after) is not None
            for group in (NOT_IN, ONLY_IN, REACHES, RENTS, BUYS, EXPECTS_A_NAME, GOES_TO)
        )

    # A thing, wanted or turned away.

    def wish(self) -> Wish | None:
        start = self.at
        # Minutes to a thing come first, so that "less than 10 minutes to a park"
        # is a limit on a number and not less of a park.
        # "Not far from" is near, and is tried before "not" is taken for a turn.
        timed = self._timed() or self.take(NEAR_TO)
        turn = None if timed else self.take(_BEFORE_A_THING)
        way = Way.NONE
        if turn is not None:
            said = " ".join(found.text for found in turn)
            way = next(w for w, words in _WAY_OF.items() if said in words)
        small = large = essential = good = False
        near = timed
        while True:
            if self.take(LARGE_STEP) is not None:
                large = True
            elif self.take(SMALL_STEP) is not None:
                small = True
            elif self.take(ESSENTIAL) is not None:
                essential = True
                if self.take(_THING_IS) is not None:
                    self.take(TO_DO.words)
            elif self.take(GOOD.words) is not None or self.take_a(Is.GENERIC) is not None:
                good = True
            elif turn is None and near is None and (near := self._near()) is not None:
                pass
            elif self.take(ARTICLE.words) is None and self.take(WEIGHT_ON) is None:
                break
        thing = self.take_a(Is.THING)
        if thing is None:
            self.at = start
            return None
        self.take(PLACE_NOUN.words)
        nearby = self.nearby()
        self.take(FOR_WHOM.words)
        counts = self._counts()
        if turn is not None and (small or essential or counts is not None):
            # "No more pubs", "not essential parks": a word of degree under a word
            # that turns is more than one rule can read.
            raise NotPlain
        after = counts is not None and counts[0] is not Way.NONE
        target = self.reader.known.lexicon[thing.text]
        # A phrase that says which way a thing is wanted has a word of its own:
        # "clean air", "low crime", "near a park". So has one that opens with
        # such a word: "good schools".
        own = target.wanted_low or target.direction is not DirectionChoice.DEFAULT
        own = own or thing.text.split()[0] in _OWN_WORDS
        led = bool(near or small or large or essential or good) or own
        # The phrase says near itself: "near a park", "close to a station".
        named_near = thing.text.startswith(("near ", "close to "))
        return Wish(
            kind=Kind.WISH,
            spans=[_span(self.items[start : self.at])],
            phrase=thing.text,
            target=target,
            way=counts[0] if counts is not None and after else way,
            step=Step.UP_SMALL if small and not large else Step.UP_LARGE,
            essential=essential or (counts is not None and counts[1]),
            large=large or (counts is not None and counts[2]),
            bare=not (turn or led or nearby or counts),
            led=led,
            counted_after=counts is not None,
            turned_after=after,
            counts=self.cares,
            led_by_near=bool(timed) or named_near,
            near_before=bool(near) or named_near or (turn is not None and _said(turn) in _NOT_NEAR),
            near_after=nearby is not None or thing.text.endswith(" nearby"),
        )

    def nearby(self) -> list[Item] | None:
        """What says near after a thing: "nearby", "within a ten minute walk"."""
        return self.take(NEARBY.words) or self._within_a_walk()

    def _within_a_walk(self) -> list[Item] | None:
        """ "Within a ten minute walk", "in under ten minutes": near, said after the thing."""
        start = self.at
        self.take({"in"})
        if self._time() is not None:
            self.take({"walk", "away", "on foot"})
            return list(self.items[start : self.at])
        self.at = start
        return None

    def _timed(self) -> list[Item] | None:
        """Minutes to a thing, which say it is wanted near: "10 minutes to", "within 5 mins of"."""
        start = self.at
        if self._time() is not None and self.take(TO_A_PLACE) is not None:
            return list(self.items[start : self.at])
        self.at = start
        return None

    def _near(self) -> list[Item] | None:
        """What says a thing is wanted near: "close to", or minutes to it."""
        return self.take(NEAR_TO) or self._timed()

    def _counts(self) -> tuple[Way, bool, bool] | None:
        """What is said of a thing after it: that it counts, or that it does not.

        The way it turns the thing, whether it is essential, and whether it is
        said strongly. `None` where nothing is said.
        """
        start = self.at
        found: tuple[Way, bool, bool] | None = None
        verb = self.take(_IS) or self.take(_WOULD_BE)
        strong = bool(self.take_all(STRENGTHENS.words, LARGE_STEP))
        would_be = verb is not None and _said(verb) in _WOULD_BE
        for way, words in _WAY_AFTER.items():
            if found is None and not would_be and self.take(words) is not None:
                found = (way, False, strong)
        is_said = found is None and verb is not None and not would_be
        if is_said and self.take(ESSENTIAL) is not None:
            found = (Way.NONE, True, strong)
        elif is_said and (article := self.take({"a", "the"})) is not None:
            # "Schools are the top priority".
            if self.take(ESSENTIAL) is not None:
                found = (Way.NONE, True, strong)
            else:
                self.at -= len(article)
        if found is None and verb is not None:
            counts = IMPORTANT.words if not would_be else IMPORTANT.words | GOOD.words
            if self.take(counts - {"matters", "matter"}) is not None:
                found = (Way.NONE, False, strong)
        if found is None and verb is None and self.take({"matters", "matter"}) is not None:
            # "Parks matter slightly" is a wish for parks, however it is put.
            self.take_all(STRENGTHENS.words, LARGE_STEP, SMALL_STEP)
            found = (Way.NONE, False, strong)
            self.cares = True
        if found is None:
            self.at = start
            return None
        self.take(WHOSE.words)
        return found

    # The home: to rent or to buy, what kind, and what it may cost.

    def home(self) -> Wish | None:
        start = self.at
        found = Home()
        led = False
        while not self.done:
            if (words := self.take(_NOT_TO_RENT)) is not None:
                found.not_rents.append(_span(words))
            elif (words := self.take(_NOT_TO_BUY)) is not None:
                found.not_buys.append(_span(words))
            elif (words := self.take(RENTS)) is not None:
                found.rents.append(_span(words))
            elif (words := self.take(BUYS)) is not None:
                found.buys.append(_span(words))
            elif self._cheaper(found) or self._size(found) or self._money(found, led):
                pass
            elif self.take(PAYS) is not None:
                led = True
            elif self.take(_GLUE) is None and self.take(A_HOME) is None:
                break
        if not self.done or not found.said:
            self.at = start
            return None
        if led or found.of_a_home:
            # A word for paying, or the home it is for, stands with the amount.
            found.by_an_m.clear()
        return Wish(kind=Kind.HOME, spans=[_span(self.items[start : self.at])], home=found)

    def _cheaper(self, found: Home) -> bool:
        start = self.at
        much = self.take(LARGE_STEP) is not None
        self.take(SMALL_STEP)
        words = self.take(CHEAPER) or self.take(DEARER)
        if words is None:
            self.at = start
            return False
        # The same, said after it: "raise my budget a little".
        much = self.take(LARGE_STEP) is not None or much
        self.take(SMALL_STEP)
        said = " ".join(word.text for word in words)
        found.steps.append((said in CHEAPER, much, _span(self.items[start : self.at])))
        return True

    def _size(self, found: Home) -> bool:
        """The size or the kind of a home: "two bedrooms", "a 2-bed flat", "a terraced house"."""
        start = self.at
        self.take(ARTICLE.words & {"a", "an", "the"})
        number = self.take_a(Is.NUMBER)
        if number is not None and not number.money and not number.low:
            last = number if number.unit == "bed" else None
            if last is None and (beds := self.take(BEDROOMS)) is not None:
                last = beds[-1]
            if last is not None:
                found.bedrooms.append((number.value, (number.start, last.end)))
                # A price is published by the kind of home, so "a two bed flat"
                # says the kind too.
                kind = self.take(A_HOME)
                if kind is not None and _said(kind) in BUY_SEGMENTS:
                    found.segments.append((_said(kind), _span(kind)))
                return True
        self.at = start
        for kinds in (RENT_SEGMENTS, BUY_SEGMENTS):
            if (words := self.take(frozenset(kinds))) is not None:
                found.segments.append((_said(words), _span(words)))
                self.take(A_HOME - {"flat", "apartment"})
                return True
        return False

    def _money(self, found: Home, led: bool) -> bool:
        """An amount of money, with what caps it: "up to £1,500 a month", "450k max"."""
        start = self.at
        caps = self.take(CAPS_FIRMLY) or self.take(CAPS)
        if caps is not None:
            self.take(_OR_SO)
        number = self.take_a(Is.NUMBER)
        if number is None or number.unit in ("min", "bed") or number.low:
            self.at = start
            return False
        after = self.peek()
        if after is not None and (
            after.what is Is.THING or self.phrase(MINUTES | BEDROOMS) is not None
        ):
            self.at = start
            return False  # a number of things, of minutes or of bedrooms
        if number.distance and self.phrase(TO_A_PLACE) is not None:
            self.at = start
            return False  # "1.5m from a park" is a distance
        thousands = self.take(THOUSANDS) is not None
        marked = self.take(IN_MONEY) is not None or thousands
        monthly = [number] if number.unit == "month" else self.take(MONTHLY)
        firmly = self.take(CAPS_FIRMLY)
        softly = None if firmly else self.take(_AT_MOST)
        of_money = number.money or marked or bool(monthly)
        told = caps or firmly or softly or led or found.said
        if not of_money and not (told and number.value >= LEAST_MONEY):
            self.at = start
            return False
        # Before the amount or after it: "max £400k", "£400k max".
        firm = firmly is not None or any(
            said is not None and _said(said) in FIRM_OF_MONEY for said in (caps, softly)
        )
        opens = caps[0].start if caps else number.start
        amount = number.value * 1_000 if thousands else number.value
        found.amounts.append((amount, firm, (opens, number.end)))
        if monthly:
            found.monthly.append(_span(monthly))
        if number.distance and not (marked or monthly):
            # A word that caps is no word of money: "within 10m", "5m max".
            found.by_an_m.append((opens, number.end))
        return True

    # A journey to a place that was named.

    def journey(self) -> Wish | None:
        start = self.at
        for read in (self._by_a_cue, self._by_a_time, self._by_reaching, self._there, self._loose):
            found = read()
            if found is not None and self.done:
                found.spans = [_span(self.items[start : self.at])]
                found.led_by_near = True
                return found
            self.at = start
        return None

    def _time(self) -> Time | None:
        """A number of minutes, and whether it is a limit: "within 35 minutes", "30mins max".

        A range, "35-40 minutes", "35 to 40 minutes", is read as the longer of
        the two, which leaves out nothing the person would take. It says which
        the shorter was, so that whoever reads it can say a range was given. A
        range is a limit at its longer end: whoever gives one has said how long
        is too long.
        """
        start = self.at
        caps = self.take(CAPS_FIRMLY) or self.take(CAPS)
        if caps is not None:
            self.take(_OR_SO)
        hours = self.take(frozenset(HOURS))
        at_least = 0
        if hours is not None:
            minutes = HOURS[_said(hours)]
        else:
            self.take(ARTICLE.words & {"a", "an"})
            number = self.take_a(Is.NUMBER)
            if number is None or number.money:
                self.at = start
                return None
            longer = None if number.low or number.unit else self._to_a_longer(number)
            if longer is not None:
                at_least, number = number.value, longer
            else:
                at_least = number.low
            if number.unit != "min" and (number.unit or self.take(MINUTES) is None):
                self.at = start
                return None
            minutes = number.value
        firmly = self.take(CAPS_FIRMLY)
        softly = None if firmly else self.take(_AT_MOST)
        # Before the minutes or after them: "within 40 minutes", "40 minutes max".
        firm = firmly is not None or any(
            said is not None and _said(said) in FIRM_OF_MINUTES for said in (caps, softly)
        )
        return Time(minutes, firm or at_least > 0, at_least)

    def _to_a_longer(self, shorter: Item) -> Item | None:
        """The second number of a range in words, "35 to 40": a longer one, after "to"."""
        start = self.at
        if self.take({"to"}) is not None:
            longer = self.take_a(Is.NUMBER)
            plain = longer is not None and not longer.money and not longer.low
            if longer is not None and plain and longer.value > shorter.value:
                return longer
        self.at = start
        return None

    def _mode(self, found: Wish) -> None:
        words = self.take(MODES)
        if words is None:
            return
        said = _said(words)
        found.mode = (
            ModeChoice.CYCLE
            if said in CYCLED
            else ModeChoice.WALK
            if said in WALKED
            else ModeChoice.PT
        )

    def _place(self, found: Wish, asks: bool) -> bool:
        """The place a journey is to: the whole of a name, or words that are the name of none."""
        self.take(_BEFORE_A_NAME)
        named = self.take_a(Is.NAME)
        if named is not None and named.place:
            found.place_id = named.place
            return True
        if not asks:
            return False
        # What the release does not hold is what the person calls the place. It is
        # asked about, and adds no journey. It is asked only where nothing else is
        # said after it, so that it is a name that was given and not something said.
        # The name of an area that is the name of no place is asked about as it is.
        words = [named.text] if named is not None else []
        while named is None and (word := self.peek()) is not None and len(words) < MAX_NAME_WORDS:
            if word.what is not Is.WORD or word.text in KNOWN_WORDS or word.apart:
                break
            words.append(word.text.replace("'", ""))
            self.at += 1
        if not words or " ".join(words) in GENERIC_PLACES:
            return False
        found.options = self.reader.offered(" ".join(words))
        return True

    def _by_a_cue(self) -> Wish | None:
        found = Wish(kind=Kind.JOURNEY, spans=[])
        goes = self.take(GOES_TO)
        if goes is not None:
            found.mode = GOES[goes[0].text]
        elif (cue := self.take(EXPECTS_A_NAME)) is not None:
            # Whether the place is where the person works or where they live now,
            # nobody can say: it is offered.
            found.offered = _said(cue) in COMMUTES_FROM
        else:
            near = self.take(NEAR_TO)
            # After "near", what follows is as often no name at all, so nothing is
            # asked. After "near my office at" a name is expected.
            at_work = near is not None and self.take(AT_WORK) is not None
            if near is None or not self._place(found, asks=at_work):
                return None
            self._mode(found)
            return found
        if not self._place(found, asks=True):
            return None
        self._mode(found)
        return found

    def _by_a_time(self) -> Wish | None:
        """ "30 minutes to X by bike", "within 40 minutes of X", "a 20 minute walk from X"."""
        found = Wish(kind=Kind.JOURNEY, spans=[])
        time = self._time()
        if time is None:
            return None
        found.minutes, found.firm, found.at_least = time
        goes = self.take(frozenset(GOES))
        if goes is not None:
            found.mode = GOES[_said(goes)]
        if self.take(TO_A_PLACE) is None:
            return None
        self.take(AT_WORK)
        if not self._place(found, asks=True):
            return None
        self._mode(found)
        return found

    def _by_reaching(self) -> Wish | None:
        """ "get to X in under 40 minutes", "reach X within 30 minutes on foot"."""
        found = Wish(kind=Kind.JOURNEY, spans=[])
        if self.take(REACHES) is None:
            return None
        self.take(AT_WORK)
        if not self._place(found, asks=True):
            return None
        self._mode(found)
        self.take({"in"})
        time = self._time()
        if time is not None:
            found.minutes, found.firm, found.at_least = time
        self._mode(found)
        return found

    def _there(self) -> Wish | None:
        """ "to get there within 35 minutes": the minutes of the journey named before it."""
        found = Wish(kind=Kind.JOURNEY, spans=[], there=True)
        # It follows the journey it is said of, so the wish needs no speaker of its own.
        self.take(WISH.words)
        if self.take(GETS_THERE) is None:
            return None
        self.take({"in"})
        time = self._time()
        if time is None:
            return None
        found.minutes, found.firm, found.at_least = time
        self._mode(found)
        return found

    def _loose(self) -> Wish | None:
        """ "a 40 minute commute": minutes said apart from any place."""
        found = Wish(kind=Kind.JOURNEY, spans=[], loose=True)
        time = self._time()
        if time is None:
            return None
        # With no word for a journey, "20 minutes tops", it is read only beside a
        # journey that was named in the same sentence.
        found.beside = self.take(A_JOURNEY) is None
        found.minutes, found.firm, found.at_least = time
        self._mode(found)
        return found

    # A rule about an area.

    def rule(self) -> Wish | None:
        start = self.at
        self.take({"it"})
        only = self.take(ONLY_IN)
        words = only or self.take(NOT_IN)
        if words is not None:
            self.take({"the", "in"} if only else {"the"})
            named = self.take_a(Is.NAME)
            if named is not None and named.area and self.done:
                return Wish(
                    kind=Kind.RULE,
                    spans=[_span(self.items[start : self.at])],
                    action=AreaAction.ONLY if only else AreaAction.EXCLUDE,
                    area_id=named.area,
                )
        self.at = start
        return None

    # What makes no edit: who lives somewhere, and what Burro has no measure of.

    def people(self) -> Wish | None:
        start = self.at
        # Whatever is said of who lives somewhere, more of them or fewer, no edit
        # is made of it. So every word that may stand before a thing may stand here.
        self.take_all(ARTICLE.words, _BEFORE_A_THING, SMALL_STEP, LARGE_STEP, {"full of"})
        if self.take_a(Is.PEOPLE) is None:
            self.at = start
            return None
        while self.take_a(Is.PEOPLE) is not None:
            pass
        self.take(PLACE_NOUN.words)
        self.take({"like me", "like us"})
        return Wish(kind=Kind.PEOPLE, spans=[_span(self.items[start : self.at])])

    def no_measure(self) -> Wish | None:
        start = self.at
        self.take_all(ARTICLE.words, GOOD.words, LARGE_STEP, SMALL_STEP, NEAR_TO)
        found = self.take_a(Is.UNMET)
        unmet = (found.unmet,) if found is not None and found.unmet is not None else ()
        while found is None and self.take_a(Is.AMENITY) is not None:
            unmet = (UnmetCategory.COMMUNITY_AMENITIES,)
        if not unmet:
            self.at = start
            return None
        self.take(NEARBY.words)
        return Wish(kind=Kind.NO_MEASURE, spans=[_span(self.items[start : self.at])], unmet=unmet)

    def item(self) -> list[Wish]:
        """What this part of a sentence is, from here to its end.

        It is one item. A home, or what makes no edit, may stand before a
        journey or a wish with no word between them, "2 bed within 30
        minutes of the works", "broadband near a park". The wish must have
        a word of its own, so that a bare name is never read out of words
        that were said of something else.
        """
        start = self.at
        for read in (self.rule, self.journey, self.home, self.wish, self.people, self.no_measure):
            found = read()
            if found is not None and self.done:
                return [found]
            self.at = start
        for cut in range(start + 1, len(self.items)):
            before = _Segment(self.items[:cut], self.reader)
            after = _Segment(self.items[cut:], self.reader)
            for read in (before.home, before.people, before.no_measure, before.wish):
                before.at = start
                first = read()
                if first is None or not before.done:
                    continue
                for then in (after.journey, after.wish):
                    after.at = 0
                    second = then()
                    if second is None or not after.done or second.bare:
                        continue
                    # After a thing, only what is led by "near": "a quiet street not
                    # far from a station". A thing that was turned stands alone, since
                    # "no pubs near a park" may be said of the pubs by the park.
                    wished = first.kind is Kind.WISH
                    if wished and (first.way is not Way.NONE or not second.led_by_near):
                        continue
                    self.at = len(self.items)
                    return [first, second]
        raise NotPlain


def _said(words: Sequence[Item]) -> str:
    """Some words as the grammar spells them: a word typed with a hyphen as its parts."""
    return " ".join(word.bare if "-" in word.text else word.text for word in words)


# The phrases of the grammar that hold a word that joins: "anywhere but". Within
# one, the word joins nothing.
_HOLDS_A_JOIN = frozenset(
    phrase for phrase in VOCABULARY if set(phrase.split()[1:]) & set(_JOIN_OF)
)


def _inside_a_phrase(items: Sequence[Item]) -> set[int]:
    """Where a word that joins is part of a phrase of the grammar, and so joins nothing."""
    found: set[int] = set()
    for at, item in enumerate(items):
        for phrase in _HOLDS_A_JOIN:
            words = phrase.split()
            run = items[at : at + len(words)]
            spelt = [i.text for i in run if i.what is Is.WORD and (i is item or not i.apart)]
            if spelt == words:
                found |= set(range(at + 1, at + len(words)))
    return found


# After "and" or "but", "with" and "also" add nothing: "but with some culture", "and
# also a park". After any other word that joins they are not read, and nor is a third.
_ADDS_NOTHING = frozenset({"with", "also"})
_ADDED_TO = frozenset({"and", "but"})


def _segments(items: Sequence[Item]) -> list[tuple[Join, list[Item]]]:
    """The parts of a sentence, and how each is joined to the one before."""
    found: list[tuple[Join, list[Item]]] = []
    current: list[Item] = []
    join = Join.FIRST
    # The words that join, since the last part ended.
    joined_by: list[str] = []
    held = _inside_a_phrase(items)
    for at, item in enumerate(items):
        joins = item.what is Is.WORD and item.text in _JOIN_OF and at not in held
        if item.apart and not set(item.marks) <= JOINING_MARKS:
            raise NotPlain  # a colon, a dash, a bracket or a quote joins nothing
        if (item.apart or joins) and current:
            found.append((join, current))
            current, join, joined_by = [], Join.MARK, []
        if not joins:
            current.append(item)
        elif _adds_nothing(item, joined_by):
            # The first word still says how the wish is joined.
            joined_by.append(item.text)
        elif current or joined_by or (not found and item.text == "or"):
            raise NotPlain  # two words that join, or a sentence that opens on "or"
        else:
            join, joined_by = _JOIN_OF[item.text], [item.text]
    if current:
        found.append((join, current))
    elif joined_by:
        raise NotPlain  # a sentence that ends on a word that joins
    return found


def _adds_nothing(item: Item, joined_by: Sequence[str]) -> bool:
    """Whether a word that joins stands straight after "and" or "but", and adds nothing to it."""
    after = len(joined_by) == 1 and joined_by[0] in _ADDED_TO
    return after and not item.apart and item.text in _ADDS_NOTHING


# The units of what is measured as a distance or as a time to walk.
_FAR_OFF = frozenset({"m", "min"})


def _is_at_a_distance(wish: Wish) -> bool:
    """Whether a wish is for a place to reach, or for a thing that is some way off."""
    if wish.kind is Kind.JOURNEY:
        return True
    if wish.kind is not Kind.WISH or wish.target is None:
        return False
    near = any(FEATURES[feature].unit in _FAR_OFF for feature in wish.target.features)
    return near or wish.led_by_near


def _goes_on(wish: Wish) -> bool:
    """Whether a wish goes on the list of the thing before it."""
    return wish.kind is Kind.WISH and wish.join in (Join.MARK, Join.AND, Join.OR) and not wish.own


def _led_near(found: Sequence[Wish], at: int) -> bool:
    """Whether a thing is listed after one that is led by near, with bare things between."""
    while at > 0 and _goes_on(found[at]) and found[at].bare:
        at -= 1
        if found[at].kind is Kind.WISH and found[at].near_before:
            return True
    return False


def _closed_near(found: Sequence[Wish], at: int) -> bool:
    """Whether a thing listed after this one is said to be nearby."""
    for wish in found[at + 1 :]:
        if not _goes_on(wish):
            return False
        if wish.near_after:
            return True
    return False


def about_a_campus(target: Target) -> bool:
    return FeatureId.UNIVERSITY_PROXIMITY in target.features


def read_into_crime(target: Target) -> bool:
    """Whether a phrase is only read into a vibe whose recipe holds recorded crime.

    "Smart", "well kept", "edgy" and "raw", where gritty is built as a
    scale. None names crime, so none may set it counting: the vibe is offered,
    and the offer says what it counts.
    """
    return target.provenance is EditProvenance.INFERRED and bool(HOLDS_CRIME & set(target.tags))


# The phrases a text is read against, for each way gritty is built. They are
# the same for every release that carries it that way, so they are made once.
_KNOWN: dict[GrittyVariant, Tables] = {}


def _known(variant: GrittyVariant) -> Tables:
    found = _KNOWN.get(variant)
    if found is None:
        found = tables(lexicon_of(variant), no_measure_of(variant), KNOWN_WORDS)
        _KNOWN[variant] = found
    return found


class Grammar:
    """The grammar of a plain prompt, read against the names and the words of one release."""

    def __init__(self, names: Names | None, release: Release | None) -> None:
        self.names = names
        self.release = release
        variant = release.manifest.gritty_variant if release is not None else GrittyVariant.B
        self.known: Tables = _known(variant)

    def offered(self, words: str) -> tuple[Match, ...]:
        """What to offer for words that were given as a name and are the whole of none."""
        return () if self.names is None else self.names.search_places(words, MAX_OPTIONS)

    def items(self, line: Line) -> list[Item]:
        return items_of(line, self.names, self.known)

    def nearby(self, items: Sequence[Item]) -> bool:
        """Whether some items open with what says near after a thing: "nearby", "in 10 minutes"."""
        return _Segment(items, self).nearby() is not None

    def sentence(self, line: Line, items: Sequence[Item]) -> list[Wish]:
        """The items of one sentence. Raises `NotPlain` if the grammar does not make it."""
        if line.asked or any(item.what is Is.ODD for item in items):
            raise NotPlain
        if set(line.closed_by) - set(".!\N{HORIZONTAL ELLIPSIS}") - JOINING_MARKS:
            raise NotPlain  # it ends on a colon or a dash, as a heading does
        if items and items[0].apart:
            raise NotPlain
        found: list[Wish] = []
        parts = _segments(items)
        spoken = False
        for position, (join, part) in enumerate(parts):
            segment = _Segment(part, self)
            last = position == len(parts) - 1
            if segment.take_all(COURTESY.words) and segment.done:
                found.append(Wish(kind=Kind.NOTHING, spans=[_span(part)], join=join))
                continue
            segment.at = 0
            segment.unspoken = _AT_THE_HEAD if position == 0 else frozenset()
            own = segment.opening(spoken)
            spoken = spoken or segment.spoke
            if not segment.done and position < len(parts) - 1:
                at = segment.at
                if not segment.take_all(GOOD.words) or not segment.done:
                    segment.at = at
            if not segment.done and self._most_of_all(segment, found):
                continue
            if segment.done:
                # An opening with nothing after it says nothing, and is carried
                # to what follows: "somewhere, with a park", "somewhere nice and quiet".
                found.append(Wish(kind=Kind.NOTHING, spans=[_span(part)], join=join, own=own))
                continue
            for wish in self._item(segment, last):
                wish.join, wish.own = join, own
                wish.of_the_speaker = segment.spoke and not own
                found.append(self._checked(wish))
        found = [self._checked(wish) for wish in self._one_turn_one_thing(found)]
        self._there(found)
        self._an_m_is_money(found)
        self._a_person_is_no_place(found)
        return found

    @staticmethod
    def _a_person_is_no_place(found: Sequence[Wish]) -> None:
        """Raises `NotPlain` for a word that is a person's too, where nothing says near.

        "Doctor" is a surgery in "near a doctor" and in "a doctor nearby", and
        who the speaker is in "I'm a doctor". What is said after a thing may be
        said of every thing of its list, "a GP and a chemist nearby", and what
        leads a thing leads the bare things listed after it: "near a park and
        a doctor". Neither reaches a thing the speaker opens with no wish.
        """
        for at, wish in enumerate(found):
            if wish.kind is not Kind.WISH or wish.target is None or not wish.target.near_only:
                continue
            if wish.near_before or wish.near_after:
                continue
            if wish.of_the_speaker or not (_led_near(found, at) or _closed_near(found, at)):
                raise NotPlain

    @staticmethod
    def _an_m_is_money(found: Sequence[Wish]) -> None:
        """Raises `NotPlain` for a number of "m" that nothing says is an amount of money.

        "5m" and "1.5m" are as likely minutes, metres or miles as millions,
        and a word that caps says nothing of which: "within 10m", "5m max".
        One is an amount where a word for paying or the home it is for
        stands in the same part of the sentence, "a detached house up to
        2m". Standing in a part of its own, "buying, 1.5m max", it is one
        where the sentence says something else of a home, and names nothing
        to be near and no place to reach whose distance it could be.
        """
        homes = [wish.home for wish in found if wish.kind is Kind.HOME]
        if not any(home.by_an_m for home in homes):
            return
        if not any(home.of_a_home or home.monthly for home in homes):
            raise NotPlain
        if any(_is_at_a_distance(wish) for wish in found):
            raise NotPlain

    def _checked(self, wish: Wish) -> Wish:
        """A wish that one rule can read, or `NotPlain`.

        A nuisance is a thing only under a turn, in a phrase that says low,
        "less noise", "low crime", or where it is said to count: "I care
        about noise". Named alone, or liked, it is a wish no edit can
        express. A phrase that says which way it is wanted cannot be turned
        round by a word before it without the reader guessing. And what
        troubles a person is read of a nuisance alone.
        """
        target = wish.target
        if wish.kind is not Kind.WISH or target is None:
            return wish
        if counts_residents(target):
            if wish.way is not Way.NONE:
                # Whatever turns a thing that counts who lives somewhere, the words ask
                # for fewer of a group of people, or to be kept from one. Nothing reads
                # that: it is a request about people, and gets the notice.
                return Wish(kind=Kind.PEOPLE, spans=wish.spans, join=wish.join, own=wish.own)
            if wish.essential:
                raise NotPlain
            # No word applies it. It is offered, towards more of what it counts.
            wish.offered = True
            return wish
        if target.no_end and wish.way not in (Way.OFF, Way.DOWN):
            # The name of a scale names no end, so the reader would have to
            # choose one. To take it off, or to turn it down, needs none.
            raise NotPlain
        if target.whatever and (wish.way is not Way.NONE or wish.essential):
            # "No character", "I don't care about character": whatever is said of
            # it, it is offered, and no weight is taken off for it.
            raise NotPlain
        if (read_into_crime(target) or target.note) and wish.way is not Way.OFF:
            # Crime counts only when it is asked for by name. A word that is
            # read into a vibe that holds it asks for nothing by name. And
            # what Burro has no measure of is offered what is nearest. Under
            # a word that turns, nobody can say what is meant.
            if wish.way is not Way.NONE or wish.essential:
                raise NotPlain
            wish.offered = True
            return wish
        turned = wish.way in (Way.NOT_AT_ALL, Way.LESS)
        if turned and about_a_campus(target):
            # To be kept from a campus is a request about who lives somewhere.
            return Wish(kind=Kind.PEOPLE, spans=wish.spans, join=wish.join, own=wish.own)
        if wish.way is Way.NONE and target.nuisance and not (target.wanted_low or wish.counts):
            raise NotPlain
        if turned and (target.direction is not DirectionChoice.DEFAULT or target.wanted_low):
            raise NotPlain
        if wish.way is Way.TROUBLED and not target.nuisance:
            raise NotPlain
        if wish.way is not Way.NONE and wish.essential:
            raise NotPlain
        return wish

    @staticmethod
    def _most_of_all(segment: _Segment, found: list[Wish]) -> bool:
        """ "It's the most important thing", said of the wish before it."""
        at = segment.at
        before = found[-1] if found else None
        said = segment.take(_IT_IS) is not None
        segment.take({"the", "a"})
        if said and segment.take(ESSENTIAL) is not None:
            segment.take({"thing"})
            wished = before is not None and before.kind is Kind.WISH and before.way is Way.NONE
            if segment.done and before is not None and wished:
                before.essential = True
                before.spans.append(_span(segment.items))
                return True
        segment.at = at
        return False

    @staticmethod
    def _item(segment: _Segment, last: bool) -> list[Wish]:
        """The item of a segment, with the words that may close a sentence after it."""
        start = segment.at
        try:
            return segment.item()
        except NotPlain:
            pass
        # Read again without the words that close it: "a park too", "near a station
        # please". Courtesy may close any part, and "too" the last.
        closes = AT_THE_END if last else COURTESY.words
        for size in (2, 1):
            closing = segment.items[len(segment.items) - size :]
            if len(segment.items) - start > size and _said(closing) in closes:
                shorter = _Segment(segment.items[: len(segment.items) - size], segment.reader)
                shorter.at = start
                return shorter.item()
        raise NotPlain

    @staticmethod
    def _one_turn_one_thing(found: list[Wish]) -> list[Wish]:
        """A turn governs the thing straight after it, and the things joined to that by "or".

        A thing joined to a turned thing by a comma or "and", with nothing
        said before it, makes the prompt not plain, because the reader
        cannot say whether the turn reaches it. "But", a wish of the
        speaker's, a turn of its own and a word before the thing that is the
        thing's own begin a new wish. What is said after a thing never does:
        "nearby", "on my doorstep" and "would be good" may be said of every
        thing of the list. "No pubs or restaurants nearby" was read as a
        wish for restaurants. So after "or" the turn carries over what is
        said after the thing, and nothing begins a new wish there but a turn
        of its own. And what is said to count after the last thing of a list
        may be said of every one of them, so that is not plain either.
        """
        carried = Way.NONE
        listed = False
        for wish in found:
            if wish.kind is not Kind.WISH:
                carried, listed = Way.NONE, False
                continue
            goes_on = wish.join in (Join.MARK, Join.AND, Join.OR) and not wish.own
            turns = wish.way is not Way.NONE and not wish.turned_after
            if goes_on and carried is not Way.NONE and not turns:
                if wish.join is not Join.OR and wish.led:
                    # "No pubs, near a park": a word of its own, after a comma or "and".
                    carried, listed = Way.NONE, False
                    continue
                if wish.join is not Join.OR or wish.led or wish.counted_after:
                    raise NotPlain
                wish.way = carried
                continue
            if wish.turned_after and goes_on and listed:
                raise NotPlain
            carried = Way.NONE if wish.turned_after else wish.way
            listed = wish.bare
        return found

    @staticmethod
    def _there(found: list[Wish]) -> None:
        """ "There" stands for the one place named earlier in the same sentence."""
        journeys = [wish for wish in found if wish.kind is Kind.JOURNEY and not wish.loose]
        if any(wish.beside for wish in found) and len(journeys) != 1:
            raise NotPlain
        for wish in [wish for wish in journeys if wish.there]:
            named = [other for other in journeys if not other.there]
            before = named[0] if len(named) == 1 else None
            if before is None or found.index(before) > found.index(wish) or before.minutes:
                raise NotPlain
            before.minutes, before.firm = wish.minutes, wish.firm
            before.at_least = wish.at_least
            if wish.mode is not ModeChoice.UNCHANGED:
                before.mode = wish.mode
            before.spans += wish.spans
            found.remove(wish)
