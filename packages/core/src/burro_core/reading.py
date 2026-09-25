"""Reading a text: its sentences, its tokens, and what each run of tokens is.

Nothing here decides what a person wants. It finds where a sentence ends,
and which words are a thing of the lexicon, the whole of a name of the
release, a number, a word for who lives somewhere, or a word for what Burro
has no measure of. Every other token is left as the word it is, for the
grammar to place or to fail on.

A sentence ends at a full stop, a question mark, an exclamation mark or a
line break, and nowhere else. A token is what stands between two spaces, less
the marks around it, and is never split at a mark inside it. A name is matched
on the text as typed: it is never put together across a mark, a hyphen or a
line break.
"""

import re
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple

from burro_core.catalogue import FEATURES, TAGS
from burro_core.ids import UnmetCategory
from burro_core.lexicon import (
    APOSTROPHE,
    APOSTROPHES,
    DESCRIBES,
    EATS,
    GROUP,
    NAMED_FOR_WHO_IS_COUNTED,
    NAMED_FOR_WHOSE_SHARE,
    NOT_A_NOUN,
    OF_A_PEOPLE,
    ONLY_A_GROUP,
    POLICY,
    Target,
    plain,
    prepare,
)
from burro_core.places import Names

_MAX_DIGITS = 12
_TOO_MANY = 10**12

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
_BEFORE = _BRACKETS_OPEN + _QUOTES + APOSTROPHE
_AFTER = _BRACKETS_CLOSE + _QUOTES + APOSTROPHE + _LISTS + _ENDS
# The marks that join two items of a list, and no other mark does.
JOINING_MARKS = frozenset(",;")
# A word, with nothing in it but letters, digits, and an apostrophe, a hyphen or an
# ampersand between two of them. An ampersand is how the name of a chain is written,
# "M&S", and is read as the "and" it stands for.
_A_WORD = re.compile(r"[a-z0-9]+(?:['&-][a-z0-9]+)*")
_AMOUNT = re.compile(r"(£)?([0-9][0-9,]*(?:\.[0-9]+)?)(k|m)?(pcm|pm)?")
_GLUED = re.compile(
    r"([0-9]+|[a-z]+)-?(min|mins|minute|minutes|bed|beds|bedroom|bedrooms|bedroomed)"
)
# Two whole numbers with a hyphen between them, "35-40", with or without minutes typed
# on the end. It is a range, and only a length of time is ever read from one.
_RANGE = re.compile(r"([0-9]{1,3})-([0-9]{1,3})(min|mins|minute|minutes)?")
# A dash that stands between two digits is the hyphen of a range, however it was typed.
_DASH_IN_A_RANGE = re.compile(r"(?<=[0-9])[\N{EN DASH}\N{EM DASH}](?=[0-9])")
MINUTES = frozenset({"min", "mins", "minute", "minutes"})
COUNTED: Mapping[str, int] = {
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


class Token(NamedTuple):
    """One run of characters with no space in it, as it was typed and as it is read.

    A token is never split at a mark inside it: "don;t" is one token, and one
    the reader does not know.
    """

    # As the vocabulary holds a word: lower case, no accents, its apostrophe as "'".
    word: str
    # As the lexicon and the names hold one: with no apostrophe, a hyphen as a space, and an
    # ampersand as the word it stands for.
    bare: str
    start: int
    end: int
    # The marks that stand between it and the token before it in its sentence.
    marks: str
    # It is written with a hyphen or an ampersand, so it is read whole or not at all.
    joined: bool
    # It holds a mark the reader does not read, or stands in quotes.
    odd: bool

    @property
    def apart(self) -> bool:
        """A mark stands before it, so it is never read as one phrase with the token before."""
        return bool(self.marks)


class Line(NamedTuple):
    """The tokens of one sentence, and how it ended."""

    tokens: tuple[Token, ...]
    start: int
    end: int
    asked: bool  # it ends in a question mark
    # The marks it ended with, and any that stand after its last token.
    closed_by: str


def lines_of(text: str) -> list[Line]:
    """The sentences of a text. One ends at a full stop, "?", "!" or a line break, only there."""
    lines: list[Line] = []
    tokens: list[Token] = []
    asked = False
    trailing = ""
    began = position = 0

    def close(at: int) -> None:
        nonlocal tokens, asked, trailing, began
        if tokens:
            lines.append(Line(tuple(tokens), began, tokens[-1].end, asked, trailing))
        tokens, asked, trailing, began = [], False, "", at

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
        if after[:1] in APOSTROPHE and after[:1] and core[-1:].lower() == "s" and not before:
            # "Five minutes' walk": the apostrophe of a plural is part of the word,
            # and parts it from nothing.
            after = after[1:]
        if not tokens:
            began = chunk.start()
        if core and all(c in _DASHES for c in core):
            # A dash with a space each side parts two wishes, and is no mark of a list.
            trailing, core = trailing + core, ""
        if core:
            spelt = _DASH_IN_A_RANGE.sub("-", APOSTROPHES.sub("'", plain(core)))
            word = "and" if spelt in ("&", "+") else spelt
            shaped = _A_WORD.fullmatch(word) or _AMOUNT.fullmatch(word)
            quoted = any(c in _QUOTES or c in APOSTROPHE for c in before) or any(
                c in _QUOTES for c in after
            )
            tokens.append(
                Token(
                    word=word,
                    bare=word.replace("'", "").replace("-", " ").replace("&", " and "),
                    start=chunk.start() + lead,
                    end=chunk.start() + tail,
                    marks=(trailing + before) if tokens else "",
                    joined="-" in word or "&" in word,
                    odd=not shaped or quoted,
                )
            )
            trailing = ""
        marks = after if core else typed
        if marks:
            trailing += marks
        if any(c in _ENDS for c in marks):
            asked = asked or "?" in marks
            if tokens:
                close(chunk.end())
            asked = False
    close(len(text))
    return lines


class Is(Enum):
    WORD = "word"  # a word, for the grammar to place
    THING = "thing"  # a phrase of the lexicon
    NAME = "name"  # the whole of a name of the release
    NUMBER = "number"
    PEOPLE = "people"  # a word for who lives somewhere
    AMENITY = "amenity"  # a community's amenity, which no feature covers
    UNMET = "unmet"  # something Burro has no measure of
    GENERIC = "generic"  # a colour or a country beside a thing: it names nothing
    ODD = "odd"  # a token with a mark inside it, or in quotes


@dataclass
class Item:
    """One or more tokens read as one thing, and where in the text they stand."""

    what: Is
    text: str
    first: int
    last: int
    start: int
    end: int
    # The marks that stand between it and the item before it.
    marks: str
    place: str = ""
    area: str = ""
    value: int = 0
    money: bool = False
    unit: str = ""
    unmet: UnmetCategory | None = None
    # A word as the lexicon would hold it: with no apostrophe, and a hyphen as a space.
    bare: str = ""
    # The lower number of a range, "35-40", of which `value` is the upper. Nothing
    # where the number is no range.
    low: int = 0
    # It was typed with an "m" and no pound sign, so that it is as likely a
    # distance as an amount: "1.5m from a park", "near a station, 0.5m max".
    distance: bool = False

    @property
    def span(self) -> tuple[int, int]:
        return (self.start, self.end)

    @property
    def apart(self) -> bool:
        return bool(self.marks)


Phrases = Mapping[str, list[tuple[str, ...]]]


def by_first_word(phrases: Iterable[str]) -> dict[str, list[tuple[str, ...]]]:
    """Phrases by the word each begins with, the longest first."""
    found: dict[str, list[tuple[str, ...]]] = {}
    for phrase in phrases:
        words = tuple(phrase.split())
        found.setdefault(words[0], []).append(words)
    for listed in found.values():
        listed.sort(key=lambda words: (-len(words), words))
    return found


# The labels that hold a comma or a number typed with a hyphen, by their first word. A
# short label may hold a hyphen too, "Mid-range grocers within reach", and is read the same.
_LABELS: dict[str, list[tuple[str, tuple[str, ...]]]] = {}
for _label in (*FEATURES.values(), *TAGS.values()):
    for _printed in dict.fromkeys((prepare(_label.label), prepare(_label.short_label))):
        _LABELS.setdefault(_printed.split()[0].rstrip(","), []).append(
            (_printed, tuple(_printed.split()))
        )

# What it costs to read a token one way and not another. The reading that leaves
# the fewest tokens as words the grammar does not hold is taken, and of two that
# leave as few, the one made of the longest phrases: so "good transport links" is
# "good" and "transport links", though "good transport" is a phrase too, and
# "Wexmoor University" is the campus and not Wexmoor.
_COST_UNKNOWN = 10.0
_COST_WORD = 3.0
_COST_PHRASE = 1.0
_COST_NAME = 0.8


def whole(number: str, suffix: str = "") -> int:
    """A number as it was written, as a whole number. Absurdly long ones are capped.

    The cap is far outside every limit, so the reducer still turns the edit
    away as out of range, and nothing here can overflow on the way to it.
    """
    scale = {"k": 1_000, "m": 1_000_000}.get(suffix, 1)
    digits = number.replace(",", "")
    if len(digits.split(".")[0]) > _MAX_DIGITS:
        return _TOO_MANY
    return min(round(float(digits) * scale), _TOO_MANY)


def _number(token: Token, at: int) -> Item | None:
    """A number, an amount of money, or a number typed with its unit: "30mins", "2-bed"."""
    found = _AMOUNT.fullmatch(token.word)
    if found is not None:
        pound, digits, scale, monthly = found.groups()
        # "5m" is as likely five minutes or five metres as five million, so a whole
        # number of "m" is money only where a word of money stands with it. With a
        # point in it, "1.5m", it is no length of time, and is offered as an amount.
        # Whether either is applied as one is for the grammar to say of the sentence.
        millions = scale != "m" or "." in digits
        return Item(
            Is.NUMBER,
            "",
            at,
            at + 1,
            token.start,
            token.end,
            token.marks,
            value=whole(digits, scale or ""),
            money=bool(pound or monthly or (scale and millions)),
            unit="month" if monthly else "",
            distance=scale == "m" and not pound,
        )
    spanned = _RANGE.fullmatch(token.word)
    if spanned is not None:
        low, high, unit = spanned.groups()
        if int(low) >= int(high):
            return None  # "40-35" is no range, and nobody can say what it is
        return Item(
            Is.NUMBER,
            "",
            at,
            at + 1,
            token.start,
            token.end,
            token.marks,
            value=int(high),
            unit="min" if unit else "",
            low=int(low),
        )
    glued = _GLUED.fullmatch(token.word)
    if glued is None:
        return None
    count, unit = glued.groups()
    value = int(count) if count.isdigit() else COUNTED.get(count)
    if value is None or len(count) > _MAX_DIGITS:
        return None
    kind = "min" if unit in MINUTES else "bed"
    return Item(
        Is.NUMBER, "", at, at + 1, token.start, token.end, token.marks, value=value, unit=kind
    )


def together(tokens: Sequence[Token], first: int, size: int) -> bool:
    """Whether some tokens stand side by side with nothing but a space between them."""
    run = tokens[first : first + size]
    if len(run) < size or any(token.odd for token in run):
        return False
    if size == 1:
        return True
    return not any(token.joined for token in run) and not any(t.apart for t in run[1:])


def _labels_at(tokens: Sequence[Token], at: int) -> Iterator[tuple[str, int]]:
    """Each label of the catalogue that the tokens spell from `at`, marks and all.

    A label is fixed text, "Pubs, bars and evening venues", and is read as it
    is printed: with its own commas and its own hyphen, and with no others.
    """
    for label, words in _LABELS.get(tokens[at].bare.split()[0], ()):
        spelt: list[str] = []
        size = 0
        while len(spelt) < len(words) and at + size < len(tokens):
            token = tokens[at + size]
            comma = len(spelt) > 0 and words[len(spelt) - 1].endswith(",")
            if token.odd or (size > 0 and token.apart and not (comma and token.marks == ",")):
                break
            spelt += token.bare.split()
            size += 1
        if spelt == [word.rstrip(",") for word in words]:
            yield label, size


def phrases_at(tokens: Sequence[Token], at: int, table: Phrases) -> Iterator[tuple[str, int]]:
    """Each phrase of a table that the tokens spell from `at`, and how many tokens it takes."""
    token = tokens[at]
    if token.joined:
        # Written with a hyphen, it is a phrase only as a whole: "well-connected".
        words = tuple(token.bare.split())
        if words in table.get(words[0], ()):
            yield " ".join(words), 1
        return
    for words in table.get(token.bare, ()):
        size = len(words)
        if together(tokens, at, size) and tuple(t.bare for t in tokens[at : at + size]) == words:
            yield " ".join(words), size


def _names_at(tokens: Sequence[Token], at: int, names: Names | None) -> Iterator[Item]:
    """The places and areas whose whole name the tokens spell from `at`, as typed.

    A name is never put together across a mark, a hyphen or a line break.
    """
    if names is None or tokens[at].joined or tokens[at].bare not in names.first_words:
        return
    for size in range(min(names.longest, len(tokens) - at), 0, -1):
        if not together(tokens, at, size):
            continue
        spelling = " ".join(token.bare for token in tokens[at : at + size])
        place, area = names.whole_place(spelling), names.whole_area(spelling)
        if place is not None or area is not None:
            yield item(tokens, Is.NAME, spelling, at, size, place=place or "", area=area or "")


def item(
    tokens: Sequence[Token],
    what: Is,
    text: str,
    first: int,
    size: int,
    place: str = "",
    area: str = "",
    unmet: UnmetCategory | None = None,
) -> Item:
    return Item(
        what,
        text,
        first,
        first + size,
        tokens[first].start,
        tokens[first + size - 1].end,
        tokens[first].marks,
        place=place,
        area=area,
        unmet=unmet,
    )


def people_in(tokens: Sequence[Token]) -> dict[int, Is]:
    """Which tokens are about who lives somewhere, or name a community's amenity.

    A word for a kind of resident is closed to every other rule, so it can
    never be quietly turned into a feature or a vibe. It is heard in every
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
    found: dict[int, Is] = {}

    def mark(start: int, end: int, what: Is) -> None:
        for index in sorted(set(owner[start:end])):
            found.setdefault(index, what)

    named = [
        found.span()
        for whole in (NAMED_FOR_WHOSE_SHARE, NAMED_FOR_WHO_IS_COUNTED)
        for found in whole.finditer(line)
    ]
    for match in POLICY.finditer(line):
        if any(start <= match.start() and match.end() <= end for start, end in named):
            # The whole name of the one measure that says whose share it is, or the whole
            # of a phrase that is offered for who it counts.
            continue
        # The word before describes the people too: "quiet neighbours" asks
        # for a kind of neighbour, not for a quiet place.
        described = DESCRIBES.search(line, 0, match.start())
        mark(described.start() if described else match.start(), match.end(), Is.PEOPLE)
    for match in GROUP.finditer(line):
        if any(index in found for index in set(owner[match.start() : match.end()])):
            continue
        group, noun = match.group("group"), match.group("noun")
        if amenity := match.group("amenity"):
            *between, venue = amenity.split()
            if NOT_A_NOUN.intersection(between):
                continue  # "a student who likes pubs" asks for pubs
            if group not in ONLY_A_GROUP and venue in EATS:
                # "Turkish cafes" asks for cafes. The cuisine says nothing of who lives there.
                mark(match.start("group"), match.end("group"), Is.GENERIC)
                continue
            mark(match.start(), match.end(), Is.AMENITY)
        elif group in ONLY_A_GROUP and noun and noun not in NOT_A_NOUN:
            mark(match.start(), match.end(), Is.PEOPLE)
        elif noun in OF_A_PEOPLE:
            # "A Polish character", "a Black identity": the character of a people.
            mark(match.start(), match.end(), Is.PEOPLE)
        elif group not in ONLY_A_GROUP:
            # "White stucco houses", "an English garden": a colour or a country.
            mark(match.start("group"), match.end("group"), Is.GENERIC)
    return found


class Tables(NamedTuple):
    """The phrases a text is read against, for one release."""

    lexicon: Mapping[str, Target]
    things: Phrases
    no_measure: Mapping[str, UnmetCategory]
    unmet: Phrases
    # Every word that some phrase of the grammar holds.
    words: frozenset[str]


def tables(
    lexicon: Mapping[str, Target],
    no_measure: Mapping[str, UnmetCategory],
    words: frozenset[str],
) -> Tables:
    return Tables(
        lexicon,
        by_first_word(phrase for phrase in lexicon if "," not in phrase),
        no_measure,
        by_first_word(no_measure),
        words,
    )


def items_of(line: Line, names: Names | None, known: Tables) -> list[Item]:
    """The tokens of a sentence, each read as the lexicon or the release has it, or left a word."""
    tokens = line.tokens
    fixed = people_in(tokens)
    count = len(tokens)
    best: list[tuple[float, Item | None]] = [(0.0, None)] * (count + 1)
    for at in range(count - 1, -1, -1):
        token = tokens[at]
        choices: list[tuple[float, Item]] = []
        if at in fixed:
            choices.append((0.0, item(tokens, fixed[at], token.bare, at, 1)))
        elif token.odd:
            choices.append((_COST_WORD, item(tokens, Is.ODD, "", at, 1)))
        else:
            choices += [(_COST_NAME, name) for name in _names_at(tokens, at, names)]
            for text, size in (*phrases_at(tokens, at, known.things), *_labels_at(tokens, at)):
                if text in known.lexicon:
                    choices.append((_COST_PHRASE, item(tokens, Is.THING, text, at, size)))
            for text, size in phrases_at(tokens, at, known.unmet):
                unmet = known.no_measure[text]
                choices.append((_COST_PHRASE, item(tokens, Is.UNMET, text, at, size, unmet=unmet)))
            number = _number(token, at)
            if number is not None:
                choices.append((_COST_PHRASE, number))
            word = item(tokens, Is.WORD, token.word, at, 1)
            word.bare = token.bare
            held = token.word in known.words or all(w in known.words for w in token.bare.split())
            choices.append((_COST_WORD if held else _COST_UNKNOWN, word))
        choices = [
            (cost, found)
            for cost, found in choices
            if not any(i in fixed for i in range(at + 1, found.last))
        ]
        best[at] = min(
            ((cost + best[found.last][0], found) for cost, found in choices),
            key=lambda found: (found[0], -(found[1].last - found[1].first)),
        )
    items: list[Item] = []
    at = 0
    while at < count:
        found = best[at][1]
        assert found is not None
        items.append(found)
        at = found.last
    for found in items:
        if found.what is Is.WORD and found.text in COUNTED:
            found.what, found.value = Is.NUMBER, COUNTED[found.text]
    return items
