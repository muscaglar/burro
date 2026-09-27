"""The person's words as they were typed, and what core makes of where they stand.

Nothing here reads a word. It finds where words stand in the text, and asks
core where a sentence ends, what a token is, which of its phrases a stretch
holds and which numbers stand in it. Every list of words is core's. Do not
write one here.

What is kept of the words is where they stand, as offsets. Nothing here is
logged or stored.
"""

import re
import unicodedata
from collections.abc import Iterable, Iterator, Sequence
from functools import cache
from typing import NamedTuple

from burro_core.catalogue import FEATURES, NUISANCES
from burro_core.grammar import (
    BEDROOMS,
    BUYS,
    CYCLED,
    IN_MONEY,
    MONTHLY,
    RENTS,
    THOUSANDS,
    WALKED,
    Grammar,
    Join,
    about_a_campus,
    part_of_a_longer_time,
)
from burro_core.ids import (
    FeatureId,
    FeatureKind,
    GrittyVariant,
    PlaceKind,
    TagId,
    Tenure,
    Toward,
    UnmetCategory,
)
from burro_core.interpret import (
    BY_THE_MONTH,
    SIGNS_OF_DOUBT,
    known_in,
    may_ask_for_fewer,
    names_a_visit,
    paid_by,
    taken_back_in,
)
from burro_core.lexicon import (
    ENDS_NAMED_AS_HOMES,
    Target,
    counts_residents,
    lexicon_of,
    prepare,
)
from burro_core.reading import COUNTED, MINUTES, Is, Item, Line, Token, lines_of, whole
from burro_core.release import Release
from burro_core.vocabulary import (
    ARTICLE,
    ASIDES,
    ASKS_BURRO,
    CANNOT_BEAR,
    CAPS,
    CAPS_FIRMLY,
    CARRIES_A_TURN,
    COURTESY,
    DREADS,
    ESSENTIAL,
    FIRM_OF_MINUTES,
    FIRM_OF_MONEY,
    FOR_WHOM,
    GIVES_A_REASON,
    GOOD,
    HEADS_WHAT_IS_WANTED,
    IMPORTANT,
    IN_CASE,
    JOINS,
    LARGE_STEP,
    LEADS_IN_A_WISH,
    LEADS_IN_WHAT_IS_SAID_NEXT,
    NEAR_TO,
    NEARBY,
    OPENS_A_HEADING,
    PHRASES_OF_DOUBT,
    SAYS_HOW_LONG,
    SMALL_STEP,
    SOFTLY,
    SOMEWHERE,
    SOMEWHERE_THAT,
    SPEAKER,
    STANDS_FOR,
    STRENGTHENS,
    TAKES_OFF,
    TAKES_OFF_AFTER,
    THE_MOST_AFTER,
    TO_DO,
    TROUBLES,
    TURNS_DOWN,
    TURNS_DOWN_AFTER,
    TURNS_FIRMLY,
    TURNS_NOTHING,
    TURNS_SOFTLY,
    TURNS_WHERE_IT_STANDS_ALONE,
    WHO_ELSE,
    WHOSE,
    WISH,
    WISHES_OF_ANOTHER,
    WORDS_OF_DOUBT,
    WORDS_THAT_TURN_AWAY,
)

__all__ = [
    "CYCLES",
    "DOUBT",
    "ESSENTIALLY",
    "FIRMLY_OF_MINUTES",
    "FIRMLY_OF_MONEY",
    "NEAR_ON_FOOT",
    "SMALL",
    "TURNS",
    "WALKS",
    "Span",
    "Typed",
    "holds",
    "in_doubt",
    "is_nuisance",
    "may_be_said_of_it",
    "not_minded",
    "overlap",
    "said_not_to_matter",
    "somebody_elses",
    "stands_against",
    "turned_about",
    "turned_once",
    "without",
]

Span = tuple[int, int]
_WORDS_ONLY = re.compile(r"[^a-z0-9]+")
_CHUNK = re.compile(r"\S+")
# A number as it is typed, with what scales it where no letter follows: "400k", "1.2m".
_FIGURE = re.compile(r"([0-9][0-9,]*(?:\.[0-9]+)?)(?:(k|m)(?![a-z]))?")
_APOSTROPHES = str.maketrans(
    dict.fromkeys(
        "`\N{RIGHT SINGLE QUOTATION MARK}\N{LEFT SINGLE QUOTATION MARK}"
        "\N{MODIFIER LETTER APOSTROPHE}\N{PRIME}",
        "'",
    )
)


def _said(text: str) -> str:
    """Words as core's lists hold them: lower case, no marks, one space between two."""
    return _WORDS_ONLY.sub(" ", prepare(text)).strip()


def _phrases(*lists: Iterable[str]) -> tuple[str, ...]:
    """Some phrases of core's, written as `_said` writes a text, the longest first."""
    found = {_said(phrase) for phrases in lists for phrase in phrases}
    return tuple(sorted(found - {""}, key=lambda phrase: (-len(phrase), phrase)))


# What turns a wish away, takes it off, turns it down or keeps it at a
# distance: every word core has such a rule for, and every one it lists.
TURNS = _phrases(
    TURNS_FIRMLY,
    TURNS_SOFTLY,
    TAKES_OFF,
    TAKES_OFF_AFTER,
    TURNS_DOWN,
    TURNS_DOWN_AFTER,
    WORDS_THAT_TURN_AWAY,
    PHRASES_OF_DOUBT,
)
# Every sign of doubt core lists: what turns, and what is over, is someone
# else's, is not sure, or asks.
DOUBT = _phrases(TURNS, SIGNS_OF_DOUBT)
# What says a nuisance is not wanted, or troubles the person: "no", "less", "worried about".
_TROUBLED_BY = _phrases(TURNS_FIRMLY, TURNS_SOFTLY, TROUBLES, WORDS_OF_DOUBT)
# What says no to the thing it stands with: "no", "less", "doesn't", "never".
_SAYS_NO = _phrases(TURNS_FIRMLY, TURNS_SOFTLY, WORDS_THAT_TURN_AWAY)
# What is said of how much a thing counts, and not of the thing: "don't mind",
# "doesn't matter", "less weight on". Of a nuisance too it takes the weight off.
_COUNTS_FOR_LESS = _phrases(TAKES_OFF, TAKES_OFF_AFTER, TURNS_DOWN, TURNS_DOWN_AFTER)
# What leads in to a thing and is no doubt about it: "not far from a park". What says a
# number is the most it may be, which never makes it a least. And what holds a word that
# turns and turns nothing: "a few restaurants", "nothing but parks".
_NO_DOUBT = _phrases(NEAR_TO, CAPS, CAPS_FIRMLY, THE_MOST_AFTER, TURNS_NOTHING)
# What makes an amount of money a firm limit, and what makes a number of minutes one. Each
# is core's list, so that a model's reading is held to the words the rules are held to.
FIRMLY_OF_MONEY = _phrases(FIRM_OF_MONEY)
FIRMLY_OF_MINUTES = _phrases(FIRM_OF_MINUTES)
# The words core's grammar places that name nothing: the speaker, a wish, an
# article, a word that joins. A quote made of these alone says nothing of a thing.
_NAMES_NOTHING = _phrases(
    *(
        group.words
        for group in (
            *(SPEAKER, WISH, ASKS_BURRO, TO_DO, SOMEWHERE, SOMEWHERE_THAT),
            *(ARTICLE, STRENGTHENS, WHOSE, JOINS, COURTESY),
        )
    )
)
# What turns a wish for a thing round wherever it stands about the thing: what a person
# dreads, thinks little of or cannot bear, and what is said of how little a thing counts.
# A bare word that turns is not among them: after a thing it is as often said of
# something else, "a park that is not too far".
_DREADED = _phrases(DREADS, TAKES_OFF_AFTER, TURNS_DOWN_AFTER)
# Every word that turns a wish, as it is read where it stands apart from the thing, beyond
# a mark. It turns the wish only where nothing more is said beside it: what names nothing,
# what stands for the thing, and what is itself a sign of doubt. "No thanks" turns a wish,
# and "not too expensive" says something of the price.
_TURNS_APART = _phrases(TURNS, _DREADED)
_SAYS_NO_MORE = _phrases(_NAMES_NOTHING, STANDS_FOR, DOUBT)
# What turns only where it is all that stands between two marks: "pubs, pass".
_TURNS_ALONE = frozenset(_phrases(TURNS_WHERE_IT_STANDS_ALONE))
# What leads in to a thing, and what says after it where it is wanted, is no doubt about
# it: "a park within walking distance".
_NO_DOUBT_ABOUT = _phrases(_NO_DOUBT, NEARBY.words)
# Who else may wish, and the third person of a wish, which says whose wish it is only
# where somebody stands straight before it who is not of the speaker's own household.
_WHO_ELSE = _phrases(WHO_ELSE)
_CARRIES_A_TURN = _phrases(CARRIES_A_TURN)
# What may head a list of things that are wanted: what core lists as such, what names
# nothing, what says that a thing counts or is good, and what is said of the words alone.
_HEADS_A_WISH = _phrases(
    HEADS_WHAT_IS_WANTED,
    _NAMES_NOTHING,
    ESSENTIAL,
    IMPORTANT.words,
    GOOD.words,
    ASIDES,
    SAYS_HOW_LONG,
    OPENS_A_HEADING,
)
_OPENS_A_HEADING = _phrases(OPENS_A_HEADING)
_STANDS_FOR = _phrases(STANDS_FOR)
# The words of doubt that end in the word that begins a new wish, where it begins none:
# "anything but", "nothing but".
_PHRASES_WITH_BUT = frozenset(
    phrase for phrase in _phrases(PHRASES_OF_DOUBT) if phrase.split()[-1] == Join.BUT.value
)
_CANNOT_BEAR = _phrases(CANNOT_BEAR)
# What a person says of their own words, and of no wish: "honestly", "I think". And what a
# heading says of the words under it, which is set apart by its colon.
_ASIDES = frozenset(_phrases(ASIDES, SAYS_HOW_LONG))
_LONGEST_ASIDE = max(len(aside.split()) for aside in _ASIDES)
# The speaker, for what is read as the speaker's own with the speaker left unsaid.
_THE_SPEAKER = min(SPEAKER.words, key=lambda word: (len(word), word))
_WISHES_OF_ANOTHER = tuple(tuple(wish.split()) for wish in sorted(WISHES_OF_ANOTHER))
_HOUSEHOLD = frozenset(whom.split()[-1] for whom in FOR_WHOM.words)
# The words that begin a wish of the speaker's own: "I want", "we'd like", "I am after".
_SPEAKS = frozenset(SPEAKER.words)
_WISHES = frozenset(wish.split()[0] for wish in WISH.words)
# How much the speaker wishes, which may stand between the speaker and the wish: "I really
# want", "we would quite like".
_HOW_MUCH_IS_WISHED = frozenset(STRENGTHENS.words) | SOFTLY
# The speaker with whatever is written on to the word, "I'll", "we've": who speaks is told
# by what stands before the apostrophe.
_WHO_SPEAKS = frozenset(speaker.split("'")[0] for speaker in SPEAKER.words)
_JOINS = frozenset(JOINS.words)
# The one word that joins which begins a new wish, whoever wished before it.
_BUT = Join.BUT.value
# Where what is said next begins, so that what stands before it is said of something else.
_LEADS_IN_A_WISH = frozenset(LEADS_IN_A_WISH)
_LEADS_IN_WHAT_IS_SAID_NEXT = frozenset(LEADS_IN_WHAT_IS_SAID_NEXT)
_GIVES_A_REASON = frozenset(GIVES_A_REASON)
_ARTICLES = _phrases(ARTICLE.words)
# What core reads as something, which what is said of one thing does not reach across.
_READ = frozenset({Is.THING, Is.NAME, Is.NUMBER, Is.PEOPLE, Is.AMENITY, Is.UNMET})
SMALL = _phrases(SMALL_STEP)
# What names nothing, and what says how much of a thing is wanted and never whether.
_HOW_MUCH_AND_NO_MORE = _phrases(_NAMES_NOTHING, SMALL_STEP, LARGE_STEP)
ESSENTIALLY = _phrases(ESSENTIAL)
WALKS = _phrases(WALKED)
CYCLES = _phrases(CYCLED)
# Core's words for renting and for buying, by the tenure each names.
_TENURES = ((Tenure.RENT, _phrases(RENTS)), (Tenure.BUY, _phrases(BUYS)))
# What core reads as how near a thing is, in words for walking: "a park I can
# walk to", "within walking distance". It is said of the thing it stands
# beside, and is no way of travelling to another.
NEAR_ON_FOOT = tuple(
    phrase for phrase in _phrases(NEAR_TO, NEARBY.words) if any(w in WALKS for w in phrase.split())
)


def holds(said: str, phrases: Sequence[str]) -> bool:
    """Whether some words hold one of some phrases, word for word and side by side."""
    padded = f" {said} "
    return any(f" {phrase} " in padded for phrase in phrases)


def without(said: str, phrases: Sequence[str]) -> str:
    """The words with some phrases taken out of them, the longest first."""
    padded = f" {said} "
    for phrase in phrases:
        padded = padded.replace(f" {phrase} ", "  ")
    return " ".join(padded.split())


def stands_against(before: str, after: str, phrases: Sequence[str]) -> bool:
    """Whether one of some phrases stands against a number: straight before it, or after.

    Before it, with nothing between but a word that caps: "no more than
    about 40". After it, with nothing between but what it is a number of:
    "40 minutes at most". Words that stand between two numbers are said of
    the one they stand against: "under 1500 and no more than 40 minutes".
    """
    led, follows = f" {before}", f"{after} "
    while True:
        if any(led.endswith(f" {phrase}") for phrase in phrases):
            return True
        cap = next((cap for cap in _OR_SO if led.endswith(f" {cap}")), None)
        if cap is None:
            break
        led = led[: -len(cap) - 1]
    while True:
        if any(follows.startswith(f"{phrase} ") for phrase in phrases):
            return True
        unit = next((unit for unit in _OF_A_NUMBER if follows.startswith(f"{unit} ")), None)
        if unit is None:
            return False
        follows = follows[len(unit) + 1 :]


def _own_wish(tokens: Sequence[Token], index: int) -> bool:
    """Whether a wish of the speaker's own begins at a token: "I want", "we'd like".

    How much the speaker wishes may stand between the two, as the grammar
    reads it: "I really want".
    """
    if tokens[index].word not in _SPEAKS:
        return False
    after = index + 1
    while after < len(tokens) and tokens[after].word in _HOW_MUCH_IS_WISHED:
        after += 1
    return after < len(tokens) and tokens[after].word in _WISHES


def _speaks(token: Token) -> bool:
    """Whether a token is the speaker, with whatever is written on to the word: "I've"."""
    return token.word.split("'")[0] in _WHO_SPEAKS


def _wish_led_in(tokens: Sequence[Token], index: int) -> bool:
    """Whether a wish begins at a token with its speaker left unsaid: "and want", "so need".

    At the head of a sentence or of a part of one, "fed up with my flat,
    looking for", or after a word that leads one in. After "or" it begins
    nothing, since "or" carries a turn: "I don't want pubs or need a
    station".
    """
    if tokens[index].word not in _WISHES:
        return False
    return index == 0 or tokens[index].apart or tokens[index - 1].word in _LEADS_IN_A_WISH


def _cut(tokens: Sequence[Token], index: int, others: set[int]) -> bool:
    """Whether what is said of a thing reaches no further than a token beside it.

    It stops at another thing, at a wish of the speaker's own, at a word
    that joins two wishes, and at a word that begins a reason. "So" joins
    two only where the speaker or a wish follows it, "so I need": before
    anything else it says how much, "so noisy". A word that joins nothing,
    which the sentence ends with, is part of what is said: "a high street,
    anything but".
    """
    word = tokens[index].word
    follows = index + 1 < len(tokens)
    joins = word in _JOINS and follows
    leads = (
        word in _LEADS_IN_WHAT_IS_SAID_NEXT
        and follows
        and (_speaks(tokens[index + 1]) or tokens[index + 1].word in _WISHES)
    )
    reason = word in _GIVES_A_REASON
    return index in others or joins or leads or reason or _own_wish(tokens, index)


def _wishes_as_another(tokens: Sequence[Token], index: int) -> bool:
    """Whether the third person of a wish begins at a token, with somebody before it.

    "My mum wants", "the landlord is after". Nobody stands before the
    heading of a list, "Wants: a park", and the speaker's own household
    wishes as the speaker does: "my dog needs a park".
    """
    if index == 0 or tokens[index].apart or tokens[index - 1].word in _HOUSEHOLD:
        return False
    return any(
        tuple(token.word for token in tokens[index : index + len(wish)]) == wish
        and not any(token.apart for token in tokens[index + 1 : index + len(wish)])
        for wish in _WISHES_OF_ANOTHER
    )


def _turns_in(said: str) -> int:
    """How many words that turn a wish some words hold, each phrase counted once."""
    left, found = without(said, _NO_DOUBT), 0
    while (sign := next((sign for sign in TURNS if holds(left, (sign,))), None)) is not None:
        left, found = without(left, (sign,)), found + 1
    return found


def _fold(typed: str) -> str:
    """What was typed, with its case and the shape of its apostrophes left out of account."""
    return unicodedata.normalize("NFKC", typed).translate(_APOSTROPHES).casefold()


def is_nuisance(thing: FeatureId | TagId | None) -> bool:
    return isinstance(thing, FeatureId) and (
        thing in NUISANCES or FEATURES[thing].kind is FeatureKind.NUISANCE
    )


def overlap(one: Span, other: Span) -> bool:
    return one[0] < other[1] and other[0] < one[1]


# What core reads a number as, where its own words say: money, minutes or
# bedrooms. A number that it reads as one is never offered as another.
_MONEY, _MINUTES, _BEDROOMS, _A_WORD = "money", "minutes", "bedrooms", "a word"
# An amount that core reads as paid by the week, or by any period but the month. A rent is
# held by the month, so it is no amount of a budget at the figure that was typed: what a
# week comes to is core's to work out, and the rules offer it.
_BY_NO_MONTH = "money by no month"
# A number that core reads as part of a longer time that it did not read whole: "15", of "1
# hour, 15 minutes", and the hour of "a third of an hour". By itself it is no number of
# minutes that the person gave, so a model's reading of it as one is a number nobody typed.
_PART_OF_A_TIME = "part of a longer time"
_SAID_AFTER = (
    (_MINUTES, _phrases(MINUTES)),
    (_BEDROOMS, _phrases(BEDROOMS)),
    (_MONEY, _phrases(MONTHLY, IN_MONEY, THOUSANDS)),
)
_NOT_MINUTES = frozenset({_MONEY, _BEDROOMS, _A_WORD, _BY_NO_MONTH, _PART_OF_A_TIME})
# What may stand between a number and the words that are said of it: before
# it a word that caps, "about", and after it what it is a number of, "minutes".
_OR_SO = _phrases(CAPS)
_OF_A_NUMBER = _phrases(MINUTES, MONTHLY, IN_MONEY, THOUSANDS, BEDROOMS)
_NO_AMOUNT = frozenset({_MINUTES, _BEDROOMS, _BY_NO_MONTH, _PART_OF_A_TIME})


class _Number(NamedTuple):
    """A number of the text: where it stands, each way it may be read, and what core reads it as."""

    where: Span
    values: frozenset[int]
    kind: str


class _Word(NamedTuple):
    """One word as it was typed, without the marks around it, and where it stands."""

    word: str
    start: int
    end: int


def _words(text: str) -> tuple[_Word, ...]:
    """Every run of characters that holds a letter or a digit, less the marks around it.

    A run is never split at a mark inside it: "lantern-yard" is one word.
    """
    found: list[_Word] = []
    for match in _CHUNK.finditer(text):
        typed = match.group()
        letters = [at for at, character in enumerate(typed) if character.isalnum()]
        if letters:
            first, last = letters[0], letters[-1] + 1
            found.append(
                _Word(_fold(typed[first:last]), match.start() + first, match.start() + last)
            )
    return tuple(found)


@cache
def _named_by(variant: GrittyVariant) -> dict[FeatureId | TagId, tuple[tuple[str, Target], ...]]:
    """Every phrase of core's lexicon for each feature and vibe, with what the phrase says."""
    found: dict[FeatureId | TagId, list[tuple[str, Target]]] = {}
    for phrase, target in lexicon_of(variant).items():
        for thing in (*target.features, *target.tags):
            found.setdefault(thing, []).append((_said(phrase), target))
    return {thing: tuple(phrases) for thing, phrases in found.items()}


class Typed:
    """The text of one request, and where in it words, sentences and numbers stand."""

    def __init__(self, text: str, grammar: Grammar, release: Release) -> None:
        self.text = text
        self.release = release
        self._words = _words(text)
        self._lines: tuple[Line, ...] = tuple(lines_of(text))
        self._items: tuple[tuple[Item, ...], ...] = tuple(
            tuple(grammar.items(line)) for line in self._lines
        )
        self._lexicon = grammar.known.lexicon
        self._named_by = _named_by(release.manifest.gritty_variant)
        self._numbers = self._numbers_typed()
        self._grammar = grammar
        # Where the sentences stand that a sentence beside them takes back, and those the
        # rules read. Each is asked of few requests, so it is worked out when first asked.
        self._known: tuple[Span, ...] | None = None
        self._taken_back: tuple[Span, ...] | None = None
        # Whether one word that turns leads up to a thing, by where the thing stands. It
        # is asked of every thing of a list for each thing that stands after it, so a list
        # of a hundred things asked it ten thousand times, and anybody may send one.
        self._led_by_a_turn: dict[Span, bool] = {}
        # Where what is said of a thing begins, by where the thing stands. It is asked
        # more than once of every place a thing is named, and is worked out once.
        self._said_from: dict[Span, tuple[int, bool]] = {}
        # What is said of each thing, as it would be typed alone, by where the words stand.
        # Many things may stand in the same words, which are then made ready once.
        self._alone: dict[Span, tuple[str, ...]] = {}

    def says_something(self, span: Span) -> bool:
        """Whether a stretch holds a word that may name a thing, a place or a number.

        It does not where every word of it is one core's grammar places that
        names nothing: "a", "I want", "and the".
        """
        return bool(without(self.said(span), _NAMES_NOTHING))

    def says_more_than_how_much(self, span: Span) -> bool:
        """Whether a stretch says something beside how much of a thing is wanted.

        It does not where it says nothing, and where all it says is a word of
        degree, which belongs to the thing it stands with: "slightly", "a bit".
        """
        return bool(without(self.said(span), _HOW_MUCH_AND_NO_MORE))

    def find(self, quoted: str, after: int = 0) -> Span | None:
        """Where some words stand in the text, or nothing where they do not.

        The same words, in the same order. The marks between them and around
        them are left out of account, so that "£400k" is found by "$400k", and
        a wish by the words either side of a question mark. Part of a word is
        not the word, and words in another order are not the words.
        """
        wanted = [word.word for word in _words(quoted)]
        size = len(wanted)
        for at in range(len(self._words) - size + 1 if size else 0):
            typed = self._words[at : at + size]
            if typed[0].start >= after and [word.word for word in typed] == wanted:
                return typed[0].start, typed[-1].end
        return None

    def every(self, quoted: str) -> Iterator[Span]:
        """Each place some words stand in the text, in order."""
        found = self.find(quoted)
        while found is not None:
            yield found
            found = self.find(quoted, after=found[0] + 1)

    def _within(self, span: Span) -> tuple[tuple[Token, ...], int, int] | None:
        """The sentence a stretch begins in, and its first and last token there."""
        for line in self._lines:
            inside = [
                at
                for at, token in enumerate(line.tokens)
                if overlap(span, (token.start, token.end))
            ]
            if inside:
                return line.tokens, inside[0], inside[-1]
        return None

    def led_up_to(self, span: Span) -> Span:
        """A stretch, with the words that lead up to it as far back as a mark.

        What turns a wish round stands before the thing as often as beside
        it, and a model may copy the thing alone: "a station", of "not near a
        station". So a stretch is read with the words before it, as far as a
        comma, a bracket, a dash or the start of its sentence.
        """
        found = self._within(span)
        if found is None:
            return span
        tokens, first, _ = found
        while first > 0 and not tokens[first].apart:
            first -= 1
        return min(span[0], tokens[first].start), span[1]

    def _begins_anew(self, tokens: Sequence[Token], at: int, until: int) -> bool:
        """Whether what is said next begins at a token, so that what stands before it is not.

        A reason begins after "because", and a new wish after "but", which
        is part of some words of doubt and begins nothing there: "anything
        but". A wish of the speaker's own begins with its speaker, "so I
        need", or with the wish where a word leads it in and the speaker is
        left unsaid: "and want". And after a word that leads in what is said
        next, the speaker begins it, "and I never", or a turn of its own
        does: "and never". What leads in to a thing is no turn: "and not far
        from". A wish of somebody else's begins as the speaker's own does,
        where a word leads it in: "and wants".
        """
        before = tokens[at - 1].word
        if before in _GIVES_A_REASON:
            return True
        if before == _BUT:
            led = tokens[at - 2].bare if at > 1 and not tokens[at - 1].apart else ""
            return f"{led} {_BUT}" not in _PHRASES_WITH_BUT
        if _own_wish(tokens, at) or _wish_led_in(tokens, at):
            return True
        if before in _LEADS_IN_A_WISH and _wishes_as_another(tokens, at):
            return True
        if before not in _LEADS_IN_WHAT_IS_SAID_NEXT:
            return False
        return _speaks(tokens[at]) or self._turn_begins(tokens, at, until)

    def _turn_begins(self, tokens: Sequence[Token], at: int, until: int) -> bool:
        """Whether words that turn a wish begin at a token. What leads in to a thing is no turn."""
        said = f"{self.said((tokens[at].start, until))} "
        if any(said.startswith(f"{near} ") for near in _NO_DOUBT):
            return False
        return any(said.startswith(f"{turn} ") for turn in TURNS)

    def _where_it_is_said_from(self, span: Span) -> tuple[int, bool]:
        """Where what is said of a stretch begins, and whether a wish of the speaker's begins it."""
        if span not in self._said_from:
            found = self._within(span)
            begins, wished = span[0], False
            if found is not None:
                tokens, first, _ = found
                while first > 0 and not tokens[first].apart:
                    if self._begins_anew(tokens, first, span[0]):
                        break
                    first -= 1
                begins = min(span[0], tokens[first].start)
                wished = _own_wish(tokens, first) or _wish_led_in(tokens, first)
            self._said_from[span] = (begins, wished)
        return self._said_from[span]

    def said_before(self, span: Span) -> Span:
        """A stretch, with the words that lead up to it and are said of it.

        As far back as a mark, as `led_up_to` reads, and no further than
        where what is said of it begins: "and want", "so I need", "but I
        love" and "because" each begin what is said next. So a word that
        turns leads up to the thing it is said of, and no further: what a
        person is leaving is not what they want, in "I'm tired of the city
        and want somewhere leafy".

        It is for what the rules noticed. What a model read is held to
        every word as far back as a mark, since a model chooses its words.
        """
        return self._where_it_is_said_from(span)[0], span[1]

    def wished_by_the_speaker(self, span: Span) -> bool:
        """Whether a wish of the speaker's own leads up to a stretch: "I want", "and would like"."""
        return self._where_it_is_said_from(span)[1]

    def saying(self, span: Span) -> Span:
        """What is said of a stretch: from where it begins to where what is said next does.

        It begins where `said_before` has it begin. It ends at the next
        mark, or before the words that begin what is said next: "quiet
        because I hate the city", "a park and I never use the station". A
        word that joins two things ends nothing: "leafy and quiet" is said
        together. A wish that "or" leads in is said of what follows it,
        though a turn before it carries over: "I don't want pubs or need a
        station" says of the pubs that they are not wanted.
        """
        begins = self.said_before(span)[0]
        found = self._within(span)
        if found is None:
            return begins, span[1]
        tokens, _, last = found
        ends = tokens[-1].end
        at = last + 1
        while at < len(tokens) and not tokens[at].apart:
            led_in = tokens[at - 1].word in _LEADS_IN_WHAT_IS_SAID_NEXT | _GIVES_A_REASON
            wished = led_in and tokens[at].word in _WISHES
            if wished or self._begins_anew(tokens, at, ends):
                return begins, tokens[at - 2 if led_in and at - 1 > last else at - 1].end
            at += 1
        return begins, max(span[1], tokens[at - 1].end)

    def said_alone(self, span: Span) -> tuple[str, ...]:
        """What is said of a stretch, as it would be typed were it all that was said.

        Less what is said of the words alone, wherever it stands in it: "I
        honestly want somewhere calm". Where a wish begins it with its
        speaker left unsaid, "and would like somewhere leafy", it is given
        with the speaker said as well, since the grammar reads few wishes
        without one. It is handed to the rules and kept nowhere.
        """
        said = self.saying(span)
        if said not in self._alone:
            self._alone[said] = self._as_typed_alone(*said)
        return self._alone[said]

    def _as_typed_alone(self, begins: int, ends: int) -> tuple[str, ...]:
        """Some words of the text, less what is said of the words alone, with a speaker if none."""
        words = [word for word in self._words if begins <= word.start and word.end <= ends]
        kept = list(self.text[begins:ends])
        at = 0
        while at < len(words):
            size = next(
                (
                    size
                    for size in range(min(_LONGEST_ASIDE, len(words) - at), 0, -1)
                    if " ".join(_said(word.word) for word in words[at : at + size]) in _ASIDES
                ),
                0,
            )
            if size:
                first, final = words[at].start - begins, words[at + size - 1].end - begins
                kept[first:final] = " " * (final - first)
            at += size or 1
        alone = " ".join("".join(kept).split())
        if not alone or not words:
            return ()
        unsaid = words[0].word in _WISHES
        return (alone, f"{_THE_SPEAKER} {alone}") if unsaid else (alone,)

    def holds_a_mark_that_is_not_read(self, span: Span) -> bool:
        """Whether the sentence of a stretch holds a token the reader cannot read as a word.

        One with a mark inside it, one in quotes, or a sign that is no word at
        all: a face that means no turns a wish as a word does.
        """
        return any(
            token.odd
            for line in self._lines
            if overlap(span, (line.start, line.end))
            for token in line.tokens
        )

    def stands_with_people(self, span: Span) -> bool:
        """Whether the clause of a stretch holds words about who lives somewhere.

        Or words for a community's amenity. What stands with either is
        part of a wish about people: "somewhere lively for young
        professionals".
        """
        clause = self.clause(span)
        return any(overlap(clause, people) for people in (*self.about_people(), *self.amenities()))

    def parts(self, span: Span) -> tuple[tuple[Span, ...], int]:
        """The parts of the sentence a stretch stands in, and which of them holds the stretch.

        A part is what stands between two marks. None where the stretch
        stands in no sentence.
        """
        found = self._within(span)
        if found is None:
            return (), 0
        tokens, first, _ = found
        begins = [at for at, token in enumerate(tokens) if at == 0 or token.apart]
        ends = [*begins[1:], len(tokens)]
        parts = tuple(
            (tokens[start].start, tokens[end - 1].end)
            for start, end in zip(begins, ends, strict=True)
        )
        held = max(at for at, start in enumerate(begins) if start <= first)
        return parts, held

    def begins_what_is_said_next(self, span: Span) -> bool:
        """Whether a part of a sentence begins with words that begin what is said next.

        The speaker, a wish with no speaker said, the word that begins a
        new wish or a reason, or a word that leads one of them in: "I'm not
        one for silence", "because I hate the city", "and I never drive".
        """
        found = self._within(span)
        if found is None:
            return False
        tokens, first, _ = found
        word = tokens[first].word
        if _speaks(tokens[first]) or word in _WISHES or word in _GIVES_A_REASON or word == _BUT:
            return True
        return word in _LEADS_IN_WHAT_IS_SAID_NEXT and first + 1 < len(tokens)

    def holds_doubt(self, span: Span) -> bool:
        """Whether a stretch holds a sign of doubt core lists, beside what says where a thing is."""
        return _in_doubt_about(self, span)

    def things(self, span: Span) -> tuple[Span, ...]:
        """Where every thing stands that core finds in the sentence of a stretch."""
        found = self._sentence_of(span)
        if found is None:
            return ()
        return tuple(item.span for item in found[1] if item.what is Is.THING)

    def speaks_in(self, span: Span) -> bool:
        """Whether the speaker stands in a stretch, with whatever is written on to the word."""
        return any(
            word.word.split("'")[0] in _WHO_SPEAKS
            for word in self._words
            if span[0] <= word.start and word.end <= span[1]
        )

    def clause(self, span: Span) -> Span:
        """The clause a stretch stands in: from one mark to the next, within its sentence."""
        found = self._within(span)
        if found is None:
            return span
        tokens, _, last = found
        while last + 1 < len(tokens) and not tokens[last + 1].apart:
            last += 1
        return self.led_up_to(span)[0], max(span[1], tokens[last].end)

    def alone(self, span: Span) -> str:
        """The clause a stretch stands in, as it would be typed were it all that was said.

        It is the clause less the word that leads it in and says which case it
        is said of, where one does: "I'm buying", of "if I'm buying". It is
        handed to the rules and kept nowhere.
        """
        begins, ends = self.clause(span)
        first = next((word for word in self._words if word.start >= begins), None)
        if first is not None and first.word in IN_CASE and first.end < ends:
            begins = first.end
        return self.text[begins:ends].strip()

    def together(self, spans: Sequence[Span]) -> str:
        """The clauses some stretches stand in, as they would be typed were they all that was said.

        A journey may rest on words either side of a mark, its place and the
        time of it: "Cindermoor Works, 40 minutes max". What is said of it is
        then all that stands from the clause of the one to the clause of the
        other, with whatever stands between them, less each part that is said
        of the words alone: "Cindermoor Works, honestly, 40 minutes max". It
        is handed to the rules and kept nowhere.
        """
        held = [self.clause(span) for span in spans]
        begins, ends = min(start for start, _ in held), max(end for _, end in held)
        first = next((word for word in self._words if word.start >= begins), None)
        if first is not None and first.word in IN_CASE and first.end < ends:
            begins = first.end
        # A mark that stood after an aside stands after a space, and is read as it was.
        return " ".join(self.without_asides()[begins:ends].split())

    def _stands(self, span: Span) -> tuple[Sequence[Token], int, int, set[int]] | None:
        """The sentence a thing stands in, its first and last token there, and what else is there.

        What else is there is every token of another thing that core finds
        in the sentence: a thing of the lexicon, a name, a number.
        """
        for line, items in zip(self._lines, self._items, strict=True):
            inside = [
                index
                for index, token in enumerate(line.tokens)
                if overlap(span, (token.start, token.end))
            ]
            if inside:
                others = {
                    index
                    for item in items
                    if item.what in _READ and not overlap(span, item.span)
                    for index in range(item.first, item.last)
                }
                return line.tokens, inside[0], inside[-1], others
        return None

    def about(self, span: Span) -> tuple[Span, Span, Span]:
        """What is said of a thing where it stands: in its clause, and beyond the marks beside it.

        A model chooses the words it quotes, and the words that turn a wish
        round are the ones it leaves out: "a station", of "a station, heaven
        forbid". So what is said of a thing is read from where it stands in
        the sentence, in three stretches, of which any may be empty.

        The thing with its own clause, before it and after, as far as a mark
        either way. The stretch straight after the mark that ends the clause.
        And the stretch straight before the mark that begins it, where
        nothing but an article stands between that mark and the thing: "no",
        of "no, a park", and nothing of "no, I want a park".

        None reaches further than a word that joins two wishes or a wish of
        the speaker's own: "quiet but not dead", "a park, I want little
        else". And what runs up to another thing that core finds, with no
        mark between, is said of that thing: "not", of "a park, not pubs".
        """
        found = self._stands(span)
        if found is None:
            return span, (span[1], span[1]), (span[0], span[0])
        tokens, first, last, others = found

        def reach(begins: int) -> int:
            """Where what begins at a token ends: at the next mark, or at what cuts it short."""
            ends = begins
            while ends < len(tokens) and not _cut(tokens, ends, others):
                if ends > begins and tokens[ends].apart:
                    break
                ends += 1
            return begins if ends in others else ends

        def stretch(begins: int, ends: int, empty: int) -> Span:
            return (tokens[begins].start, tokens[ends - 1].end) if ends > begins else (empty, empty)

        led = mark = first
        while mark > 0 and not tokens[mark].apart:
            mark -= 1
        while led > mark and not _cut(tokens, led - 1, others):
            led -= 1
        follows = last + 1
        ends = follows if follows == len(tokens) or tokens[follows].apart else reach(follows)
        # No further than the sentence the words begin in, however much a model quoted.
        within = tokens[led].start, tokens[ends - 1].end
        marked = ends < len(tokens) and tokens[ends].apart
        beyond = stretch(ends, reach(ends), span[1]) if marked else (span[1], span[1])
        between = self.said((tokens[mark].start, tokens[first].start))
        begins = mark
        while begins > 0 and (begins == mark or not tokens[begins].apart):
            begins -= 1
            if begins in others:
                begins = mark
                break
        apart = mark > 0 and not without(between, _ARTICLES)
        return within, beyond, stretch(begins, mark if apart else begins, span[0])

    def anothers(self, span: Span) -> bool:
        """Whether the words of a thing's sentence give the wish for it to someone else.

        Who wishes is said once for every thing of a list, "he wants pubs
        and a station", so it is read as far back as the start of the
        sentence, across marks and other things, and no further than a wish
        of the speaker's own or the word that begins a new wish: "my brother
        wants a pub but a park would do me", "and I want a park". After the
        thing it is read as far as what is said of the thing reaches: "a
        park is what my sister wants".
        """
        found = self._stands(span)
        if found is None:
            return False
        tokens, first, last, _ = found
        begins = first
        if not any(_own_wish(tokens, index) for index in range(first, last + 1)):
            while begins > 0 and tokens[begins - 1].word != _BUT:
                begins -= 1
                if _own_wish(tokens, begins) or self._speaker_goes_on(tokens, begins):
                    break
        within, beyond, _ = self.about(span)
        # A wish of the speaker's own leads up to the thing, so what stands beyond the
        # mark after it is said next, and says nothing of whose wish this is.
        own = _own_wish(tokens, begins) or self._speaker_goes_on(tokens, begins)
        reach = tokens[begins].start, within[1] if own else max(within[1], beyond[1])
        return holds(self.said(reach), _WHO_ELSE) or any(
            _wishes_as_another(tokens, index)
            for index, token in enumerate(tokens)
            if reach[0] <= token.start and token.end <= reach[1]
        )

    def _speaker_goes_on(self, tokens: Sequence[Token], at: int) -> bool:
        """Whether a wish with no speaker said begins at a token, and is the speaker's own.

        "I hate my landlord and want somewhere leafy": a word leads the
        wish in, and who wishes is who spoke before it. It is the speaker
        where the words before it begin with the speaker, as far back as a
        mark or the word that begins a new wish, or where nobody else is
        named before it in the whole of its sentence. After "My husband
        hates pubs and would like", the wish is his. A wish that begins
        after a mark is read as it was, with all that stands before it: "my
        mum, bless her, would like a park".
        """
        if at == 0 or tokens[at].apart or not _wish_led_in(tokens, at):
            return False
        # What was said before the word that leads the wish in.
        ends = at - 1
        begins = ends - 1
        while begins > 0 and not tokens[begins].apart and tokens[begins - 1].word != _BUT:
            begins -= 1
        if begins < 0:
            return False
        if _speaks(tokens[begins]):
            return True
        said = self.said((tokens[0].start, tokens[ends - 1].end))
        return not holds(said, _WHO_ELSE) and not any(
            _wishes_as_another(tokens, index) for index in range(ends)
        )

    def sentences(self, span: Span) -> Span:
        """The whole of every sentence a stretch stands in."""
        inside = [line for line in self._lines if overlap(span, (line.start, line.end))]
        if not inside:
            return span
        return min(span[0], inside[0].start), max(span[1], inside[-1].end)

    def asks(self, span: Span) -> bool:
        """Whether a stretch stands in a sentence that asks, as core says where one ends."""
        return any(line.asked and overlap(span, (line.start, line.end)) for line in self._lines)

    def same_sentence(self, one: Span, other: Span) -> bool:
        return any(
            line.start <= one[0] < line.end and line.start <= other[0] < line.end
            for line in self._lines
        )

    def said(self, span: Span) -> str:
        """The words of a stretch, as core's lists hold words."""
        return _said(self.text[span[0] : span[1]])

    def _said_after(self, where: Span) -> str:
        """What core's words say a number is of, by what stands straight after it."""
        after = f"{self.said((where[1], self.clause(where)[1]))} "
        for kind, phrases in _SAID_AFTER:
            if any(after.startswith(f"{phrase} ") for phrase in phrases):
                return kind
        return ""

    def _numbers_typed(self) -> tuple[_Number, ...]:
        """Every number of the text: where it stands, and each way it may be read.

        A number core reads is read as core reads it, "twenty" and "£400k"
        among them, and a range with both its numbers, "35-40min". A figure
        inside a word core does not read is read as it is typed, "35b", and
        with what scales it, "1.2m".

        With each is what core's own words say it is a number of: money,
        minutes or bedrooms, by how it is written or by what stands
        straight after it. Figures in a word that holds letters of its own
        are part of a word, "35b", and are read as no number of minutes. An
        amount that core reads as paid by the week, or by any other period
        but the month, is money by no month: "350 a week", "18,000 a year".
        A number that core reads as part of a longer time, which it did not
        read whole, is no number of minutes by itself: "15", of "1 hour, 15
        minutes".
        """
        found: list[_Number] = []
        for items in self._items:
            for at, item in enumerate(items):
                if item.what is not Is.NUMBER:
                    continue
                by_unit = {"min": _MINUTES, "bed": _BEDROOMS, "month": _MONEY}.get(item.unit, "")
                kind = _MONEY if item.money else by_unit or self._said_after(item.span)
                if kind in ("", _MONEY) and paid_by(items, at).by not in ("", BY_THE_MONTH):
                    kind = _BY_NO_MONTH
                if kind in ("", _MINUTES) and part_of_a_longer_time(items, at):
                    kind = _PART_OF_A_TIME
                values = {item.value, item.low} if item.low else {item.value}
                found.append(_Number(item.span, frozenset(values), kind))
        read = [number.where for number in found]
        for word in self._words:
            if any(begun <= word.start and word.end <= ended for begun, ended in read):
                continue
            counted = COUNTED.get(word.word)
            values = set[int]() if counted is None else {counted}
            for figure in _FIGURE.finditer(word.word):
                digits, scale = figure.groups()
                values.add(whole(digits))
                if scale:
                    values.add(whole(digits, scale))
            if values:
                where = (word.start, word.end)
                found.append(_Number(where, frozenset(values), self._kind_of(word, where)))
        return tuple(sorted(found, key=lambda number: number.where))

    def _kind_of(self, word: _Word, where: Span) -> str:
        """What a word that holds figures is a number of, where core does not read it."""
        if word.word in COUNTED:
            return self._said_after(where)
        rest = _said(_FIGURE.sub(" ", word.word))
        if "\N{POUND SIGN}" in self.text[where[0] : where[1]]:
            return _MONEY
        for kind, phrases in _SAID_AFTER:
            if rest in phrases:
                return kind
        return _A_WORD if rest else self._said_after(where)

    def _of(self, span: Span, never: frozenset[str]) -> list[_Number]:
        return [
            number
            for number in self._numbers
            if overlap(span, number.where) and number.kind not in never
        ]

    def minutes(self, span: Span) -> frozenset[int]:
        """Every number in a stretch that may be a number of minutes."""
        return frozenset(
            value for number in self._of(span, _NOT_MINUTES) for value in number.values
        )

    def amounts(self, span: Span) -> frozenset[int]:
        """Every number in a stretch that may be an amount of money."""
        return frozenset(value for number in self._of(span, _NO_AMOUNT) for value in number.values)

    def range_of(self, span: Span, number: int) -> frozenset[int]:
        """The numbers of minutes that stand with one as a range, the number among them.

        In one word, "35-40min", or side by side with no more than a word
        between them and no mark: "30 to 40 minutes". Two numbers that stand
        further apart are of two things: "20 minutes to one place and about
        50 to another".
        """
        found: set[int] = set()
        held = [one for one in self._of(span, _NOT_MINUTES) if number in one.values]
        for one in held:
            begins, ends = self.clause(one.where)
            found |= one.values
            for other in self._of((begins, ends), _NOT_MINUTES):
                first, last = sorted((one.where, other.where))
                between = [w for w in self._words if first[1] <= w.start and w.end <= last[0]]
                if other.where != one.where and len(between) <= 1:
                    found |= other.values
        return frozenset(found)

    def where(self, span: Span, number: int) -> tuple[Span, ...]:
        """Each place a number stands in a stretch."""
        return tuple(
            found.where
            for found in self._numbers
            if number in found.values and overlap(span, found.where)
        )

    def beside(self, span: Span, number: int) -> tuple[tuple[Span, Span], ...]:
        """What stands before a number and after it, for each place it stands in a stretch.

        As far as the next number either way, and no further than the clause
        the number stands in. What is said of one number is not said of the
        next: "at most 2 bedrooms, around £1,500 a month". A model chooses
        how much it quotes, so what makes a limit firm is looked for here and
        not in the whole of the quote.
        """
        found: list[tuple[Span, Span]] = []
        for where in self.where(span, number):
            begins, ends = self.clause(where)
            others = [other.where for other in self._numbers if other.where != where]
            begins = max([begins, *(end for _, end in others if end <= where[0])])
            ends = min([ends, *(start for start, _ in others if start >= where[1])])
            found.append(((begins, where[0]), (where[1], ends)))
        return tuple(found)

    def named_at(
        self, spans: Sequence[Span], thing: FeatureId | TagId
    ) -> tuple[tuple[Span, Target], ...]:
        """Where core finds a thing named within some stretches, and what each phrase says.

        It is where the thing stands as the rules read the words: the longest
        phrase of the lexicon, and never part of one. A model chooses the
        words it quotes, so what is said of a thing is asked where core finds
        it, however much an offer rests on.
        """
        return tuple(
            (item.span, self._lexicon[item.text])
            for items in self._items
            for item in items
            if item.what is Is.THING
            and any(overlap(item.span, span) for span in spans)
            and thing in (*self._lexicon[item.text].features, *self._lexicon[item.text].tags)
        )

    def without_asides(self) -> str:
        """The text, less each part of a sentence that is said of the words and of no wish.

        A part is what stands between two marks. Where the whole of one is a
        phrase core lists as such, "honestly", "I think", it is blanked out
        with the mark that sets it apart, and the rest of the sentence stands
        as it would without it. The text keeps its length, so that what is
        read of it stands where it stood in what was typed. It is handed to
        the rules and kept nowhere.
        """
        left = list(self.text)
        for line in self._lines:
            tokens = line.tokens
            begins = [at for at, token in enumerate(tokens) if at == 0 or token.apart]
            for first, after in zip(begins, [*begins[1:], len(tokens)], strict=True):
                part = (tokens[first].start, tokens[after - 1].end)
                if self.said(part) not in _ASIDES:
                    continue
                # With the mark that parts it from the rest: the one after it where it
                # begins its sentence, and the one before it anywhere else.
                start = line.start if first == 0 else tokens[first - 1].end
                end = tokens[after].start if first == 0 and after < len(tokens) else part[1]
                left[start:end] = " " * (end - start)
        return "".join(left)

    def without_asides_wherever(self) -> str:
        """The text, less what is said of the words and of no wish, wherever it stands.

        A part of a sentence that is such a phrase is left out with its mark,
        as `without_asides` leaves it out. So is one that stands among other
        words, with no mark to set it apart, since a person types as they
        speak: "honestly somewhere posh", "somewhere posh I think". Its words
        stand side by side, and none of them is in quotes or holds a mark.
        The text keeps its length. It is handed to the rules and kept
        nowhere, and is for whoever asks what they make of all that is left:
        a word they do not know among it leaves the sentence one that they do
        not read, as it was.
        """
        left = list(self.without_asides())
        for line in self._lines:
            tokens = line.tokens
            at = 0
            while at < len(tokens):
                size = next(
                    (
                        size
                        for size in range(min(_LONGEST_ASIDE, len(tokens) - at), 0, -1)
                        if not any(token.apart for token in tokens[at + 1 : at + size])
                        and not any(token.odd for token in tokens[at : at + size])
                        and self.said((tokens[at].start, tokens[at + size - 1].end)) in _ASIDES
                    ),
                    0,
                )
                if size:
                    start, end = tokens[at].start, tokens[at + size - 1].end
                    left[start:end] = " " * (end - start)
                at += size or 1
        return "".join(left)

    def _sentence_of(self, span: Span) -> tuple[Sequence[Token], Sequence[Item], int] | None:
        """The sentence a stretch begins in, what core finds there, and where the stretch begins."""
        for line, items in zip(self._lines, self._items, strict=True):
            for at, token in enumerate(line.tokens):
                if overlap(span, (token.start, token.end)):
                    return line.tokens, items, at
        return None

    def under_a_heading_of_other_words(self, span: Span) -> bool:
        """Whether a stretch stands under a heading that core does not know to head a wish.

        A heading is what stands before a colon, in the sentence of the
        stretch. It is said of all that is listed after it: "Dealbreakers:
        pubs, a station". One made of words that core lists as heading what
        is wanted, or that name nothing, leaves the list a list of wishes:
        "Must haves: a park", "I want: a park".
        """
        found = self._sentence_of(span)
        if found is None:
            return False
        tokens, _, first = found
        colons = [at for at in range(1, first + 1) if ":" in tokens[at].marks]
        if not colons:
            return False
        ends = colons[-1]
        begins = ends - 1
        while begins > 0 and not tokens[begins].apart:
            begins -= 1
        return not self.heads_what_is_wanted((tokens[begins].start, tokens[ends - 1].end))

    def heads_what_is_wanted(self, heading: Span) -> bool:
        """Whether some words may head a list of things that are wanted.

        They are made of words that core lists as heading what is wanted,
        that name nothing, or that are said of the words alone: "Must
        haves", "I want", "Short version". Or the speaker says a wish of
        their own in them, and they hold no sign of doubt but a word that
        opens a heading: "What I care about", "So I care about the bones of
        the place". "What I want to avoid" holds one, and heads what is not
        wanted.
        """
        said = self.said(heading)
        if not without(said, _HEADS_A_WISH):
            return True
        found = self._within(heading)
        if found is None:
            return False
        tokens, first, last = found
        own = any(_own_wish(tokens, at) for at in range(first, last + 1))
        return own and not holds(without(said, _OPENS_A_HEADING), DOUBT)

    def closed_by_a_turn(self, span: Span) -> bool:
        """Whether the list a thing stands in ends in words that turn all of it away.

        "A station, a high street, nightlife: I can do without all of them."
        The last part of the sentence names nothing, holds one word that
        turns, and after it a word that stands for what was named: "them",
        "it", "those". It is said of the list before it, as far back as a
        wish of the speaker's own or the word that begins a new one. A word
        that stands before the turn stands for something else: "somewhere
        that doesn't feel like everywhere else".
        """
        found = self._sentence_of(span)
        if found is None:
            return False
        tokens, items, first = found
        last = len(tokens) - 1
        while last > 0 and not tokens[last].apart:
            last -= 1
        if last <= first:
            return False
        between = range(first + 1, last + 1)
        if any(tokens[at].word == _BUT or _own_wish(tokens, at) for at in between):
            closing_own = _own_wish(tokens, last)
            if not closing_own or any(
                tokens[at].word == _BUT or _own_wish(tokens, at) for at in range(first + 1, last)
            ):
                return False
        if any(item.what in _READ and item.first >= last for item in items):
            return False
        closing = (tokens[last].start, tokens[-1].end)
        if not turned_once(self, closing):
            return False
        turns = [at for at in range(last, len(tokens)) if self._turn_begins(tokens, at, closing[1])]
        return bool(turns) and any(
            tokens[at].bare in _STANDS_FOR for at in range(turns[0] + 1, len(tokens))
        )

    def listed_after_a_turn(self, span: Span) -> bool:
        """Whether a thing stands later in a list in which a thing before it is turned away.

        It is asked within the sentence of the thing, of the things core
        finds before the clause it stands in. A clause that begins a wish of
        the speaker's own, or with the word that begins a new wish, is no
        part of the list before it: "no pubs, but a park", "no, I want a park".
        """
        for line, items in zip(self._lines, self._items, strict=True):
            tokens = line.tokens
            inside = [
                at for at, token in enumerate(tokens) if overlap(span, (token.start, token.end))
            ]
            if not inside:
                continue
            clause = inside[0]
            while clause > 0 and not tokens[clause].apart:
                clause -= 1
            # Nor is one that the speaker opens: "no noise, I'm out most nights so bars".
            opens = _own_wish(tokens, clause) or _speaks(tokens[clause])
            if tokens[clause].word == _BUT or opens:
                return False
            begins = clause
            while begins > 0:
                if tokens[begins - 1].word == _BUT or _own_wish(tokens, begins - 1):
                    begins -= 1
                    break
                begins -= 1
            return any(
                item.what is Is.THING
                and begins <= item.first < clause
                and self._is_led_by_a_turn(item.span)
                for item in items
            )
        return False

    def _is_led_by_a_turn(self, span: Span) -> bool:
        """Whether one word that turns a wish leads up to a thing. It is read once for each."""
        if span not in self._led_by_a_turn:
            self._led_by_a_turn[span] = turned_once(self, self.said_before(span))
        return self._led_by_a_turn[span]

    def read_by_the_rules(self, span: Span) -> bool:
        """Whether a stretch stands in a sentence that the rules read, were it all that was typed.

        The grammar makes the whole of the sentence, less what is said of the
        words alone, and no sentence beside it takes it back.
        """
        if self._known is None:
            words = self.without_asides()
            self._known = tuple(
                (found.start, found.end) for found in known_in(words, self._grammar)
            )
        return any(overlap(span, sentence) for sentence in self._known)

    def taken_back_by_the_rules(self, span: Span) -> bool:
        """Whether a sentence beside the one a stretch stands in takes it back, as core reads it.

        By the rule the reader holds what it reads to, of a sentence it
        reads and of one it does not: a sentence that holds doubt and names
        nothing is said of the one before it, and of what is listed after it.
        A sentence that heads what is wanted takes nothing back, "Must
        haves:", so it is left out of what core is asked about, as what is
        said of the words alone is.
        """
        if self._taken_back is None:
            words = list(self.without_asides())
            for line in self._lines:
                whole = (line.start, line.end)
                if ":" in line.closed_by and self.heads_what_is_wanted(whole):
                    words[line.start : line.end] = " " * (line.end - line.start)
            self._taken_back = tuple(
                (found.start, found.end) for found in taken_back_in("".join(words), self._grammar)
            )
        return any(overlap(span, sentence) for sentence in self._taken_back)

    def _names_something(self, at: int) -> bool:
        """Whether core finds a thing, a name, a number or a word for people in a sentence."""
        return any(item.what in _READ for item in self._items[at])

    def _heads_what_is_not_wanted(self, at: int) -> bool:
        """Whether a sentence may head a list of things that are not wanted.

        It names nothing itself. And it ends in a colon, "Dealbreakers:",
        ends in a word for what a person cannot bear, "Things I hate", or
        turns and says nothing more: "No." One that goes on to say what
        cannot be borne is said of that: "I don't want to be somewhere with
        drunk people on a Friday night".
        """
        line = self._lines[at]
        if self._names_something(at):
            return False
        said = self.said((line.start, line.end))
        if ":" in line.closed_by:
            return not self.heads_what_is_wanted((line.start, line.end))
        padded = f" {said} "
        ends_in_it = any(
            f" {bears} " in padded
            and not without(padded.rpartition(f" {bears} ")[2], _SAYS_NO_MORE)
            for bears in _CANNOT_BEAR
        )
        return ends_in_it or _turns_alone(said)

    def taken_back(self, span: Span) -> bool:
        """Whether a sentence beside the one a stretch stands in turns it round.

        The sentence after it names nothing, turns, and says nothing more:
        "I want a station. Not really." Or the stretch stands in a list that
        a sentence before it heads, as far as the list goes: "Things I hate.
        Pubs. A station." A sentence in which the speaker says a wish of their
        own is no part of a list, and nor is one that names nothing.

        A sentence of words that are not known is as likely said of something
        else, and turns nothing: "Not sure where to begin. Somewhere leafy."
        """
        inside = [
            at for at, line in enumerate(self._lines) if overlap(span, (line.start, line.end))
        ]
        if not inside:
            return False
        at = inside[0]
        if at + 1 < len(self._lines) and not self._names_something(at + 1):
            after = self._lines[at + 1]
            if _turns_alone(self.said((after.start, after.end))):
                return True
        back = at
        while back >= 0:
            tokens = self._lines[back].tokens
            own = any(_own_wish(tokens, index) for index in range(len(tokens)))
            if own or not self._names_something(back):
                break
            back -= 1
        return 0 <= back < at and self._heads_what_is_not_wanted(back)

    def names(self, span: Span, thing: FeatureId | TagId) -> tuple[Target, ...]:
        """What core's own phrases for a thing say of it, for each that stands in a stretch."""
        said = self.said(span)
        return tuple(
            target for phrase, target in self._named_by.get(thing, ()) if holds(said, (phrase,))
        )

    def ends_named(self, span: Span, scale: TagId) -> tuple[frozenset[Toward], bool]:
        """The ends of a scale that the words of a clause name, and whether one was turned away.

        "Calm" names the low end of Going out, and so does "not buzzy": an
        end that is turned away is a wish for the other, as the rules read
        it. "Calm by day and buzzy by night" names both, and nobody can say
        which is meant. Nor can anybody where two words that turn lead up to
        one end, "I wouldn't say no to buzzy": no end is named there.

        A word for a home says what is being looked for, "a flat", and is
        no wish of its own. It names an end of Houses or flats only where one
        end is set against the other: "houses not flats".

        The name of a scale names no end of it, though it holds the word for
        each: "houses or flats". Its words are read as the name, and a word
        that turns beside it turns no end away.
        """
        begins, ends = self.clause(span)
        named_by: list[tuple[str, Toward | None, bool]] = [
            (phrase, None if target.no_end else target.toward, False)
            for phrase, target in self._named_by.get(scale, ())
            if not target.note
        ]
        named_by += [
            (word, toward, True) for word, toward in ENDS_NAMED_AS_HOMES.get(scale, {}).items()
        ]
        stand = sorted(
            (start, -end, toward is None, toward or Toward.HIGH, of_a_home)
            for phrase, toward, of_a_home in named_by
            for start, end in self.every(phrase)
            if begins <= start and end <= ends
        )
        named: set[Toward] = set()
        turned = in_the_lexicon = False
        at = begins
        for start, ended, no_end, toward, of_a_home in stand:
            if start < at:
                continue  # part of a longer phrase, which was read
            if no_end:
                at = -ended
                continue
            turns = _turns_in(self.said((at, start)))
            if turns > 1:
                return frozenset(), False
            other = Toward.LOW if toward is Toward.HIGH else Toward.HIGH
            named.add(other if turns else toward)
            turned = turned or bool(turns)
            in_the_lexicon = in_the_lexicon or not of_a_home
            at = -ended
        return (frozenset(named) if turned or in_the_lexicon else frozenset()), turned

    def tenures(self) -> frozenset[Tenure]:
        """The tenures the words name, by core's words for each, whoever's wish each is.

        "If I rent, up to 1,700, and if I buy, max 400k" names both, and so
        does "my partner wants to buy but I'd rather rent". Which of two is
        meant is the person's to say. A visit is named where core reads its
        words as one: "a holiday home" names none, and nor does "I work at a
        hotel".
        """
        said = self.said((0, len(self.text)))
        named = {tenure for tenure, words in _TENURES if holds(said, words)}
        if any(names_a_visit(items, at) for items in self._items for at in range(len(items))):
            named.add(Tenure.VISIT)
        return frozenset(named)

    def reads(self, span: Span) -> bool:
        """Whether core finds a thing, a name or a number in a stretch."""
        return any(
            item.what in (Is.THING, Is.NAME, Is.NUMBER) and overlap(span, item.span)
            for items in self._items
            for item in items
        )

    def part_of_a_longer_name(self, span: Span) -> bool:
        """Whether a stretch is part of a longer name that the person typed.

        The longest name is the one that is named: "Wexmoor University" is
        the campus, and not the area of Wexmoor.
        """
        return any(
            item.what is Is.NAME
            and item.start <= span[0]
            and span[1] <= item.end
            and item.span != span
            for items in self._items
            for item in items
        )

    def amenities(self) -> tuple[Span, ...]:
        """Where the words stand for a community's amenity, which no feature covers."""
        return tuple(
            item.span
            for items in self._items
            for item in items
            if item.what is Is.AMENITY or item.unmet is UnmetCategory.COMMUNITY_AMENITIES
        )

    def about_people(self) -> tuple[Span, ...]:
        """Where the words stand that a notice about who lives somewhere rests on.

        A word for people, and a campus by word or by name: in a prompt that
        is not plain a campus is heard as a request about who lives somewhere.
        So are the words for those Burro counts, their age or their households,
        where a word that turns stands with them: they may ask for fewer of a
        group of people, which nothing reads.
        """
        found: list[Span] = []
        for items in self._items:
            for at, item in enumerate(items):
                place = self.release.place(item.place) if item.place else None
                campus = (place is not None and place.kind is PlaceKind.UNIVERSITY) or (
                    item.what is Is.THING and about_a_campus(self._lexicon[item.text])
                )
                fewer = (
                    item.what is Is.THING
                    and counts_residents(self._lexicon[item.text])
                    and may_ask_for_fewer(items, at)
                )
                if item.what is Is.PEOPLE or campus or fewer:
                    found.append(item.span)
        return tuple(found)


def in_doubt(
    typed: Typed, reach: Span, thing: FeatureId | TagId | None, signs: Sequence[str] = TURNS
) -> bool:
    """Whether a wish for a thing stands with a word that turns a wish away.

    What leads in to a thing, "not far from", and what caps a number, "no
    more than", is no doubt about it.

    A nuisance is wanted less, so a word that turns is the wish itself. What
    puts it in doubt is to be named, in core's own words for it, with no such
    word beside it: "I like noise". And what is said of how much it counts:
    "I don't mind crime" is no wish for less of it.
    """
    said = typed.said(reach)
    if is_nuisance(thing) and thing is not None:
        if holds(said, _COUNTS_FOR_LESS):
            return True
        named = typed.names(reach, thing)
        only_named = any(target.nuisance and not target.wanted_low for target in named)
        return only_named and not holds(said, _TROUBLED_BY)
    return holds(without(said, _NO_DOUBT), signs)


def _in_doubt_about(typed: Typed, reach: Span) -> bool:
    """Whether a stretch holds a sign of doubt core lists, beside what says where a thing is."""
    return holds(without(typed.said(reach), _NO_DOUBT_ABOUT), DOUBT)


def may_be_said_of_it(typed: Typed, reach: Span) -> bool:
    """Whether words that stand apart from a thing, beyond a mark, may be said of it.

    They hold a sign of doubt core lists, a word that stands for what was
    named, or the speaker: "nightlife, I'll pass", "pubs, forget it",
    "schools, playgrounds, not relevant". Or they are a word that turns
    where it stands alone: "pubs, pass". Words that hold none of them say
    more of what is wanted, or say something else: "lively, lots going on
    in the evening".
    """
    if reach[1] <= reach[0]:
        return False
    return (
        typed.said(reach) in _TURNS_ALONE
        or _in_doubt_about(typed, reach)
        or holds(typed.said(reach), _STANDS_FOR)
        or typed.speaks_in(reach)
    )


def turned_once(typed: Typed, reach: Span) -> bool:
    """Whether one word that turns a wish stands in a stretch, and no second.

    Two words that turn may turn a wish round twice, which is to wish for the
    thing, "I can't live without a park", or may say twice that it is not
    wanted: nobody can say which from a list of words. What leads in to a
    thing and what caps a number is no turn.
    """
    said = typed.said(reach)
    found = _turns_in(said)
    if found < 2:
        return found == 1
    # What carries a turn on is no turn of its own beside another.
    return _turns_in(without(said, _CARRIES_A_TURN)) == 1


def _turns_alone(said: str) -> bool:
    """Whether some words turn a wish round and say nothing more: "no thanks", "I'd hate that".

    Words that go on to say something are said of that: "not too expensive".
    And what turns only where it is all that is said: "pass".
    """
    if said in _TURNS_ALONE:
        return True
    return holds(said, _TURNS_APART) and not without(said, _SAYS_NO_MORE)


def turned_about(typed: Typed, where: Span, thing: FeatureId | TagId | None) -> bool:
    """Whether the words about a thing turn a wish for it round, wherever they stand.

    In its own clause, a word of dread or distaste, before the thing or
    after: "a pub on the corner would be hell". Beyond the mark either side
    of its clause, any word that turns and says nothing more: "a station,
    heaven forbid", "pubs, no thanks", "no, a park". What leads in to a thing
    and what says where it is wanted is no doubt about it: "a park within
    walking distance".

    A nuisance is wanted less, so what is dreaded of it is the wish itself.
    `in_doubt` and `not_minded` say what puts one in doubt.
    """
    if is_nuisance(thing):
        return False
    within, beyond, before = typed.about(where)
    return (
        holds(without(typed.said(within), _NO_DOUBT_ABOUT), _DREADED)
        or _turns_alone(typed.said(beyond))
        or _turns_alone(typed.said(before))
    )


def turned_beside(typed: Typed, where: Span) -> bool:
    """Whether the words beside a journey turn it away, wherever they stand in its sentence.

    A part of its sentence, between two marks, that turns and says no more:
    "Cindermoor Works within 40 minutes, no thanks", "within 40 minutes of
    Cindermoor Works, leafy - scrap that". Or a sentence beside it that
    takes it back: "Not really." A journey is nobody's wish, so whose it is
    is not asked, and words that go on to say something are said of that:
    "no pubs". Every list is core's.
    """
    if typed.taken_back(where) or turned_about(typed, where, None):
        return True
    parts, held = typed.parts(where)
    return any(at != held and _turns_alone(typed.said(part)) for at, part in enumerate(parts))


def somebody_elses(typed: Typed, where: Span) -> bool:
    """Whether the words about a thing give the wish to someone else: "my mum is after a park".

    Whichever way the wish runs: what a friend cannot stand is no more the
    person's own than what a friend is after.
    """
    return typed.anothers(where)


def _either_side(typed: Typed, where: Span, others: Sequence[Span]) -> tuple[str, str]:
    """What is said before a thing and after it, within its clause.

    No further than the next of some other things, either way.
    """
    before, after, _ = _beside_it(typed, where, others)
    return before, after


def _beside_it(typed: Typed, where: Span, others: Sequence[Span]) -> tuple[str, str, bool]:
    """What is said either side of a thing, and whether what is said after it runs up to another."""
    begins, clause_ends = typed.clause(where)
    apart = [other for other in others if not overlap(other, where)]
    begins = max([begins, *(end for _, end in apart if end <= where[0])])
    ends = min([clause_ends, *(start for start, _ in apart if start >= where[1])])
    return typed.said((begins, where[0])), typed.said((where[1], ends)), ends < clause_ends


def said_not_to_matter(typed: Typed, where: Span, others: Sequence[Span] = ()) -> bool:
    """Whether the words say that a nuisance is not minded, where core finds it named.

    What is said of how much it counts, before it or after: "I don't mind
    crime", "noise is not important". And a word that says no, after it:
    "crime doesn't bother me". Before it, such a word is the wish itself.
    """
    before, after, runs_on = _beside_it(typed, where, others)
    if holds(f"{before} {after}", _COUNTS_FOR_LESS):
        return True
    # A word that says no, and runs up to another thing, is said of that thing: "low
    # noise matters more than the station".
    return holds(after, _SAYS_NO) and not runs_on


def not_minded(
    typed: Typed, where: Span, thing: FeatureId | TagId, others: Sequence[Span] = ()
) -> bool:
    """Whether a nuisance is not said to be unwanted, where core finds it named.

    What is said of it is read either side of it, within its clause, and no
    further than the next of some other things. A word that turns before a
    nuisance is the wish itself: "no noise". After it, it is said of the
    nuisance, and is no wish for less of it: "crime doesn't bother me". What
    is said of how much it counts is no wish either, before it or after: "I
    don't mind crime". What troubles the person is the wish wherever it
    stands: "burglary worries me".
    """
    if said_not_to_matter(typed, where, others):
        return True
    before, after = _either_side(typed, where, others)
    low = any(one.wanted_low for one in typed.names(where, thing))
    return not (low or holds(before, _TROUBLED_BY) or holds(after, _TROUBLED_BY))
