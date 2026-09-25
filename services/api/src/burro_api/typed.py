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
from burro_core.interpret import SIGNS_OF_DOUBT, may_ask_for_fewer
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
    ASKS_BURRO,
    CAPS,
    CAPS_FIRMLY,
    COURTESY,
    DREADS,
    ESSENTIAL,
    FIRM_OF_MINUTES,
    FIRM_OF_MONEY,
    FOR_WHOM,
    IN_CASE,
    JOINS,
    LARGE_STEP,
    NEAR_TO,
    NEARBY,
    PHRASES_OF_DOUBT,
    SMALL_STEP,
    SOMEWHERE,
    SOMEWHERE_THAT,
    SPEAKER,
    STANDS_FOR,
    STRENGTHENS,
    TAKES_OFF,
    TAKES_OFF_AFTER,
    TO_DO,
    TROUBLES,
    TURNS_DOWN,
    TURNS_DOWN_AFTER,
    TURNS_FIRMLY,
    TURNS_SOFTLY,
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
    "not_minded",
    "overlap",
    "somebody_elses",
    "stands_against",
    "turned_about",
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
# What leads in to a thing, and what says after it where it is wanted, is no doubt about
# it: "a park within walking distance".
_NO_DOUBT_ABOUT = _phrases(_NO_DOUBT, NEARBY.words)
# Who else may wish, and the third person of a wish, which says whose wish it is only
# where somebody stands straight before it who is not of the speaker's own household.
_WHO_ELSE = _phrases(WHO_ELSE)
_WISHES_OF_ANOTHER = tuple(tuple(wish.split()) for wish in sorted(WISHES_OF_ANOTHER))
_HOUSEHOLD = frozenset(whom.split()[-1] for whom in FOR_WHOM.words)
# The words that begin a wish of the speaker's own: "I want", "we'd like", "I am after".
_SPEAKS = frozenset(SPEAKER.words)
_WISHES = frozenset(wish.split()[0] for wish in WISH.words)
_JOINS = frozenset(JOINS.words)
# The one word that joins which begins a new wish, whoever wished before it.
_BUT = Join.BUT.value
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
    """Whether a wish of the speaker's own begins at a token: "I want", "we'd like"."""
    return (
        tokens[index].word in _SPEAKS
        and index + 1 < len(tokens)
        and tokens[index + 1].word in _WISHES
    )


def _cut(tokens: Sequence[Token], index: int, others: set[int]) -> bool:
    """Whether what is said of a thing reaches no further than a token beside it.

    It stops at another thing, at a wish of the speaker's own, and at a word
    that joins two wishes. A word that joins nothing, which the sentence
    ends with, is part of what is said: "a high street, anything but".
    """
    joins = tokens[index].word in _JOINS and index + 1 < len(tokens)
    return index in others or joins or _own_wish(tokens, index)


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
                if _own_wish(tokens, begins):
                    break
        within, beyond, _ = self.about(span)
        reach = tokens[begins].start, max(within[1], beyond[1])
        return holds(self.said(reach), _WHO_ELSE) or any(
            _wishes_as_another(tokens, index)
            for index, token in enumerate(tokens)
            if reach[0] <= token.start and token.end <= reach[1]
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
        meant is the person's to say.
        """
        said = self.said((0, len(self.text)))
        return frozenset(tenure for tenure, words in _TENURES if holds(said, words))

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


def _turns_alone(said: str) -> bool:
    """Whether some words turn a wish round and say nothing more: "no thanks", "I'd hate that".

    Words that go on to say something are said of that: "not too expensive".
    """
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


def somebody_elses(typed: Typed, where: Span) -> bool:
    """Whether the words about a thing give the wish to someone else: "my mum is after a park".

    Whichever way the wish runs: what a friend cannot stand is no more the
    person's own than what a friend is after.
    """
    return typed.anothers(where)


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
