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
    CYCLED,
    IN_MONEY,
    MONTHLY,
    THOUSANDS,
    WALKED,
    Grammar,
    about_a_campus,
)
from burro_core.ids import (
    FeatureId,
    FeatureKind,
    GrittyVariant,
    PlaceKind,
    TagId,
    UnmetCategory,
)
from burro_core.interpret import SIGNS_OF_DOUBT
from burro_core.lexicon import Target, lexicon_of, prepare
from burro_core.reading import COUNTED, MINUTES, Is, Item, Line, Token, lines_of, whole
from burro_core.release import Release
from burro_core.vocabulary import (
    ARTICLE,
    ASKS_BURRO,
    CAPS,
    CAPS_FIRMLY,
    COURTESY,
    ESSENTIAL,
    FIRM_OF_MINUTES,
    FIRM_OF_MONEY,
    JOINS,
    NEAR_TO,
    NEARBY,
    PHRASES_OF_DOUBT,
    SMALL_STEP,
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
    "not_minded",
    "overlap",
    "stands_against",
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
# What leads in to a thing and is no doubt about it: "not far from a park". And
# what says a number is the most it may be, which never makes it a least.
_NO_DOUBT = _phrases(NEAR_TO, CAPS, CAPS_FIRMLY)
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
SMALL = _phrases(SMALL_STEP)
ESSENTIALLY = _phrases(ESSENTIAL)
WALKS = _phrases(WALKED)
CYCLES = _phrases(CYCLED)
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
_SAID_AFTER = (
    (_MINUTES, _phrases(MINUTES)),
    (_BEDROOMS, _phrases(BEDROOMS)),
    (_MONEY, _phrases(MONTHLY, IN_MONEY, THOUSANDS)),
)
_NOT_MINUTES = frozenset({_MONEY, _BEDROOMS, _A_WORD})
# What may stand between a number and the words that are said of it: before
# it a word that caps, "about", and after it what it is a number of, "minutes".
_OR_SO = _phrases(CAPS)
_OF_A_NUMBER = _phrases(MINUTES, MONTHLY, IN_MONEY, THOUSANDS, BEDROOMS)
_NO_AMOUNT = frozenset({_MINUTES, _BEDROOMS})


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

    def says_something(self, span: Span) -> bool:
        """Whether a stretch holds a word that may name a thing, a place or a number.

        It does not where every word of it is one core's grammar places that
        names nothing: "a", "I want", "and the".
        """
        return bool(without(self.said(span), _NAMES_NOTHING))

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

    def clause(self, span: Span) -> Span:
        """The clause a stretch stands in: from one mark to the next, within its sentence."""
        found = self._within(span)
        if found is None:
            return span
        tokens, _, last = found
        while last + 1 < len(tokens) and not tokens[last + 1].apart:
            last += 1
        return self.led_up_to(span)[0], max(span[1], tokens[last].end)

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
        are part of a word, "35b", and are read as no number of minutes.
        """
        found: list[_Number] = []
        for item in (item for items in self._items for item in items):
            if item.what is Is.NUMBER:
                by_unit = {"min": _MINUTES, "bed": _BEDROOMS, "month": _MONEY}.get(item.unit, "")
                kind = _MONEY if item.money else by_unit or self._said_after(item.span)
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

    def names(self, span: Span, thing: FeatureId | TagId) -> tuple[Target, ...]:
        """What core's own phrases for a thing say of it, for each that stands in a stretch."""
        said = self.said(span)
        return tuple(
            target for phrase, target in self._named_by.get(thing, ()) if holds(said, (phrase,))
        )

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
        """
        found: list[Span] = []
        for items in self._items:
            for item in items:
                place = self.release.place(item.place) if item.place else None
                campus = (place is not None and place.kind is PlaceKind.UNIVERSITY) or (
                    item.what is Is.THING and about_a_campus(self._lexicon[item.text])
                )
                if item.what is Is.PEOPLE or campus:
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
    begins, ends = typed.clause(where)
    apart = [other for other in others if not overlap(other, where)]
    begins = max([begins, *(end for _, end in apart if end <= where[0])])
    ends = min([ends, *(start for start, _ in apart if start >= where[1])])
    before, after = typed.said((begins, where[0])), typed.said((where[1], ends))
    if holds(f"{before} {after}", _COUNTS_FOR_LESS) or holds(after, _SAYS_NO):
        return True
    low = any(one.wanted_low for one in typed.names(where, thing))
    return not (low or holds(before, _TROUBLED_BY) or holds(after, _TROUBLED_BY))
