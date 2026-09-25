"""The verifier: every number and proper noun in a sentence must trace to a cited fact.

The check is inverted. It does not look for names it knows; it rejects anything
it cannot account for. So an invented venue fails for being a capitalised word
no fact allows, without the verifier having to know it is a venue.

It checks numbers and capitalised names, and nothing else a sentence may
assert. It finds a name by its capital, so one written in lower case passes,
and it knows a verdict only by a short list of words. That is enough for the
templates, which are fixed text. It is not enough for a sentence a model
wrote (contract, sections 7.4 and 11), and `explain` takes no explainer but
the template one until it is.
"""

import re
import unicodedata
from collections.abc import Iterable, Iterator, Mapping
from itertools import pairwise
from typing import NamedTuple

from burro_core._record import Record
from burro_core.facts import Fact
from burro_core.ids import FactKind, SentenceOrigin, VerdictReason


class Sentence(Record):
    text: str
    fact_ids: tuple[str, ...]
    origin: SentenceOrigin


class Verdict(Record):
    ok: bool
    # A code, never the text that failed.
    reason: VerdictReason


# Sentence openers and common words that are capitalised without naming anything.
ORDINARY_WORDS = frozenset(
    {
        "a",
        "about",
        "an",
        "and",
        "as",
        "at",
        # The product's own name, where it says what it cannot do.
        "burro",
        "but",
        "by",
        "confidence",
        "for",
        "from",
        "here",
        "i",
        "in",
        "it",
        "its",
        "lines",
        "nearest",
        "no",
        "of",
        "on",
        "parts",
        "price",
        "recorded",
        "rent",
        "station",
        "that",
        "the",
        "there",
        "this",
        "to",
        "with",
        "you",
        "your",
    }
)

_PLAIN = ("", "r", "st", "ly", "ness")
_HARD = ("", "er", "est", "ly", "ness", "ish")
_SOFT = ("y", "ier", "iest", "ily", "iness")
# No sentence may call a place safe or unsafe (ADR 0006). Each word is held
# in every form it takes, because "safely" and "safety" say what "safe" does.
# A word that only holds one, "safeguarded", says something else.
BANNED_WORDS = frozenset(
    stem + ending
    for stem, endings in (
        ("safe", (*_PLAIN, "ty")),
        ("unsafe", _PLAIN),
        ("danger", ("", "s", "ous", "ously", "ousness")),
        ("rough", _HARD),
        ("dodg", _SOFT),
        ("sketch", _SOFT),
    )
    for ending in endings
)

# Praise and blame with nothing behind it. No dataset rates a place, says its
# people are friendly or says where it is heading, so no sentence may. "Gritty"
# and "polished" pass only as the name of an end of a scale or of the vibe
# itself, from the fact of that vibe which a sentence cites, and nowhere else.
VERDICT_WORDS = frozenset(
    stem + ending
    for stem, endings in (
        ("best", ("",)),
        ("top", ("", "s")),
        ("acclaimed", ("",)),
        ("friendl", _SOFT),
        ("unfriendl", _SOFT),
        ("vibran", ("t", "tly", "cy")),
        ("gritt", _SOFT),
        ("polished", ("",)),
        ("closeknit", ("",)),
    )
    for ending in endings
)
VERDICT_PHRASES: tuple[tuple[str, ...], ...] = (
    ("highly", "rated"),
    ("up", "and", "coming"),
    ("close", "knit"),
)
# The slots that name the ends of a scale.
_ENDS = ("low_end", "high_end")

# A quantity with no number behind it can never be checked against a fact. A
# length of time and a fraction said in words are two: no fact holds "an hour".
VAGUE_WORDS = frozenset(
    {"half", "halves", "double", "twice", "dozen", "dozens", "couple", "several"}
    | {"hour", "hours", "quarter", "quarters", "thirds"}
    | {"day", "days", "week", "weeks", "fortnight", "fortnights", "year", "years"}
    | {"decade", "decades", "century", "centuries", "millennium", "millennia"}
    | {"tens", "hundreds", "thousands", "millions", "billions", "trillions"}
)
# What is measured in ones. Said with an article it is one of them: "a minute"
# is 1 minute, and a fact must hold the 1. A month and a year are what a rate
# is counted over, and are not here.
UNIT_WORDS = frozenset(
    {"second", "minute", "min", "mile", "yard", "stop", "hectare", "acre", "pound"}
    | {"metre", "meter", "kilometre", "kilometer", "km"}
)
_ARTICLES = frozenset({"a", "an"})


def _counted(words: str, step: int = 1) -> dict[str, int]:
    """Each word with its place in the list: the first is one `step`."""
    return {word: n * step for n, word in enumerate(words.split(), start=1)}


_UNITS = _counted("one two three four five six seven eight nine")
_UNIT_ORDINALS = _counted("first second third fourth fifth sixth seventh eighth ninth")
_TENS = _counted("ten twenty thirty forty fifty sixty seventy eighty ninety", step=10)
_TEN_ORDINALS = _counted(
    "tenth twentieth thirtieth fortieth fiftieth sixtieth seventieth eightieth ninetieth", step=10
)
_TEENS = {
    word: n + 10 for word, n in _counted("eleven twelve thirteen fourteen fifteen sixteen").items()
} | {"seventeen": 17, "eighteen": 18, "nineteen": 19}
_TEEN_ORDINALS = {
    word: n + 10
    for word, n in _counted(
        "eleventh twelfth thirteenth fourteenth fifteenth sixteenth seventeenth eighteenth "
        "nineteenth"
    ).items()
}
_MAGNITUDES = {
    "hundred": 100,
    "thousand": 1_000,
    "million": 1_000_000,
    "billion": 1_000_000_000,
    "trillion": 1_000_000_000_000,
}
_NOTHING = dict.fromkeys(("zero", "nought", "naught", "nil", "none", "zilch", "nowt"), 0)

# A number written as a word is still a number, and must be allowed as digits.
NUMBER_WORDS: Mapping[str, str] = {
    word: str(number)
    for word, number in (
        _NOTHING
        | _UNITS
        | _UNIT_ORDINALS
        | _TENS
        | _TEN_ORDINALS
        | _TEENS
        | _TEEN_ORDINALS
        | _MAGNITUDES
        | {f"{word}th": number for word, number in _MAGNITUDES.items()}
    ).items()
}

# Digits with thousands separators and one decimal point, and the sign that
# says what kind of number it is. ASCII digits only.
_NUMBER = re.compile(
    r"(?P<pound>£\s?)?(?P<digits>(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?)(?P<percent>\s?%)?"
)
_SIGNS = "£%"
# The superscript of a unit, as in m³ and km². After a letter it is part of
# the unit. After anything else it is a number like any other.
_UNIT_POWER = re.compile(r"(?<=[a-z])[\u00b2\u00b3]", re.IGNORECASE)
# A word: letters and digits, joined by an apostrophe or a hyphen.
_JOINERS = "'\N{RIGHT SINGLE QUOTATION MARK}-"
_TOKEN = re.compile(rf"[^\W_]+(?:[{_JOINERS}][^\W_]+)*")
_JOINER = re.compile(f"[{_JOINERS}]")
_DIGIT = re.compile(r"[0-9]")
_LETTER = re.compile(r"[^\W0-9_]")

# A word that has the shape of a number word and is none: "fourty", "ninty",
# "twelth", "fiveteen", "seventies". It says a number and spells it wrongly,
# so no fact can be held to it. The shape is the start of a number word and
# the end of one, and not a list of mistakes.
_NUMBER_SHAPED = re.compile(
    r"(?:thir|fou?r|fi[fv]e?|six|seven|eigh?t?|nine?|ten|elev|eleven|twel[fv]?e?|twen)"
    r"(?:t+[iy]e?s?|t+(?:ie?|y)th|t+ee+n(?:s|th)?|f?ths?|s)"
)
# Number words run together: "twentyone", "onehundred". "Second" is also a
# length of time, and is left out so that "secondhand" is not three of them.
_RUN_TOGETHER = re.compile(
    "(?:"
    + "|".join(sorted((w for w in NUMBER_WORDS if w != "second"), key=len, reverse=True))
    + "){2,}"
)
# A Roman numeral of two letters or more. One letter is a word or a unit.
_ROMAN = re.compile(r"(?=[ivxlcdm]{2,}$)m{0,3}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})")
_ROMAN_VALUES = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
# Letters of other alphabets that read as letters of this one. It decides only
# which reason a sentence fails for: a word that holds a letter no fact holds
# fails whether or not the letter is here.
_READS_AS = str.maketrans(
    "\u0430\u0435\u0456\u0458\u043e\u0440\u0441\u0443\u0445\u0455\u04bb\u0501\u051b\u051d"
    "\u03b1\u03b5\u03b9\u03ba\u03bd\u03bf\u03c1\u03c4\u03c5\u03c7"
    "\u0585\u057d\u0578\u0570",
    "aeijopcyxshdqwaeikvoptuxounh",
)
# Marks and characters that take up no room: an accent, a zero-width space, a soft hyphen.
_TAKES_NO_ROOM = frozenset({"Mn", "Me", "Cf"})


def normalise_number(text: str) -> str:
    """A number as facts hold it: no separators, and no trailing `.0`."""
    return text.replace(",", "").removesuffix(".0")


def _numbers(text: str) -> Iterator[str]:
    """Each number, with its sign kept: `£1750`, `80%`, `45`.

    A sign says what kind of number it is, so "£57" is not supported by a
    fact that holds 57%.
    """
    for match in _NUMBER.finditer(text):
        pound = "£" if match["pound"] else ""
        percent = "%" if match["percent"] else ""
        yield f"{pound}{normalise_number(match['digits'])}{percent}"


def _supported(number: str, allowed: set[str]) -> bool:
    """A number with a sign needs the same number with the same sign. One without needs any."""
    if number.strip(_SIGNS) != number:
        return number in allowed
    return number in {held.strip(_SIGNS) for held in allowed}


def _odd_digit(text: str) -> bool:
    """Whether the text holds a digit that is not ASCII: full-width, a fraction, another script.

    None can be checked against a fact, which holds ASCII digits, so none may
    pass as a word.
    """
    return any(c.isnumeric() and not c.isascii() for c in _UNIT_POWER.sub("", text))


def _words(text: str) -> Iterator[str]:
    """Each word, casefolded, with a hyphenated word split into its parts."""
    for match in _TOKEN.finditer(text):
        yield from _JOINER.split(match.group().casefold())


def _read_as(text: str) -> str:
    """The text as a person reads it: no accents, nothing that takes no room, one alphabet.

    "Safe" written with a Cyrillic a, with an accent or with a zero-width
    space in the middle of it is read as "safe", so it is checked as "safe".
    """
    decomposed = unicodedata.normalize("NFKD", text)
    seen = "".join(c for c in decomposed if unicodedata.category(c) not in _TAKES_NO_ROOM)
    return seen.casefold().translate(_READS_AS)


def _foreign(token: str) -> bool:
    """Whether a word holds a letter that is not of the Latin alphabet."""
    return any(c.isalpha() and not unicodedata.name(c, "").startswith("LATIN") for c in token)


def _roman(word: str) -> int | None:
    """The number a Roman numeral of two letters or more states, if the word is one."""
    if _ROMAN.fullmatch(word) is None:
        return None
    values = [_ROMAN_VALUES[letter] for letter in word]
    return sum(-v if v < after else v for v, after in zip(values, [*values[1:], 0], strict=True))


# A number nobody can read for certain, and a quantity with no number behind it.
_NO_NUMBER = ""
_VAGUE = "?"


def _quantities(words: list[str], own: frozenset[tuple[str, str]] = frozenset()) -> Iterator[str]:
    """Each quantity a run of words states, in order: as digits, `_NO_NUMBER` or `_VAGUE`.

    "Seventy-one" is 71, and is supported by a fact that holds 71. It is not
    supported by one that holds 70 and 1. `own` holds the pairs of words that
    stand together in the cited facts themselves: "a year" is the fact's own
    where a rate is counted by the year, and is no length of time there.
    """
    skip = False
    for before, word, following in zip(["", *words], words, [*words[1:], ""], strict=False):
        if skip:
            skip = False
        elif (
            word in _TENS and word != "ten" and (following in _UNITS or following in _UNIT_ORDINALS)
        ):
            skip = True
            yield str(_TENS[word] + (_UNITS.get(following) or _UNIT_ORDINALS[following]))
        elif word in NUMBER_WORDS:
            yield NUMBER_WORDS[word]
        elif word in VAGUE_WORDS:
            if (before, word) not in own:
                yield _VAGUE
        elif word in _ARTICLES and following in UNIT_WORDS:
            if (word, following) not in own:
                yield "1"
        elif (numeral := _roman(word)) is not None:
            yield str(numeral)
        elif _NUMBER_SHAPED.fullmatch(word) or _RUN_TOGETHER.fullmatch(word):
            yield _NO_NUMBER


def _is_name(token: str) -> bool:
    """Capitalised, or mixing letters and digits as a postcode does."""
    mixed = _DIGIT.search(token) is not None and _LETTER.search(token) is not None
    return token[0].isupper() or mixed


class _Run(NamedTuple):
    tokens: tuple[str, ...]
    opens_sentence: bool
    start: int
    end: int


def _runs(text: str) -> Iterator[_Run]:
    """Each maximal run of name-like tokens with nothing but spaces between them."""
    run: list[str] = []
    opens = False
    start = end = 0
    for match in _TOKEN.finditer(text):
        token = match.group()
        adjacent = text[end : match.start()].isspace()
        if run and not (adjacent and _is_name(token)):
            yield _Run(tuple(run), opens, start, end)
            run = []
        if _is_name(token):
            if not run:
                before = text[: match.start()].rstrip()
                opens = not before or before[-1] in ".!?"
                start = match.start()
            run.append(token.casefold())
        end = match.end()
    if run:
        yield _Run(tuple(run), opens, start, end)


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(match.group().casefold() for match in _TOKEN.finditer(text))


def _passes_a_verdict(words: list[str], ends: frozenset[str]) -> bool:
    """Whether a sentence holds praise or blame that no fact can stand behind.

    `ends` holds the names of the ends of the scales the cited facts are
    about. A word that is one of them is a name and not a verdict.
    """
    if any(word in VERDICT_WORDS and word not in ends for word in words):
        return True
    return any(
        tuple(words[at : at + len(phrase)]) == phrase
        for phrase in VERDICT_PHRASES
        for at in range(len(words) - len(phrase) + 1)
    )


def passes_a_verdict(text: str) -> bool:
    """Whether words a person gave as a name hold a word that no sentence may say.

    A name a release gives a vibe or a measure is said in every sentence about
    it, and the name of a vibe is excused as a name where a sentence cites its
    fact. So a name is read here as a sentence is, before it can be one: it may
    hold no word that calls a place safe or unsafe, and no praise or blame.
    """
    read = list(_words(_read_as(text)))
    return any(word in BANNED_WORDS for word in read) or _passes_a_verdict(read, frozenset())


def _within(run: tuple[str, ...], allowed: Iterable[tuple[str, ...]]) -> bool:
    size = len(run)
    return any(
        text[start : start + size] == run
        for text in allowed
        for start in range(len(text) - size + 1)
    )


def verify(sentence: Sentence, facts: Mapping[str, Fact]) -> Verdict:
    """Whether everything the sentence asserts is supported by the facts it cites.

    `facts` holds the facts of the one area being explained, keyed by id, so a
    fact about another area cannot be cited.
    """

    def failed(reason: VerdictReason) -> Verdict:
        return Verdict(ok=False, reason=reason)

    if any(cited not in facts for cited in sentence.fact_ids):
        return failed(VerdictReason.UNKNOWN_FACT)
    cited = [facts[cited] for cited in sentence.fact_ids]
    # A sentence citing nothing is allowed nothing, so it passes only if it
    # holds nothing to check.
    allowed_text = [text for fact in cited for text in (fact.label, *fact.slots.values())]
    allowed_words = [list(_words(_read_as(text))) for text in allowed_text]
    numbers = {n for fact in cited for n in fact.numbers}
    numbers |= {n for text in allowed_text for n in _numbers(text)}
    numbers |= {q for words in allowed_words for q in _quantities(words) if q.isdigit()}
    names = [_tokens(name) for fact in cited for name in fact.names]
    names += [_tokens(text) for text in allowed_text]
    own = frozenset(pair for words in allowed_words for pair in pairwise(words))
    written = {token for name in names for token in name}

    if _odd_digit(sentence.text):
        return failed(VerdictReason.UNSUPPORTED_NUMBER)
    if any(not _supported(number, numbers) for number in _numbers(sentence.text)):
        return failed(VerdictReason.UNSUPPORTED_NUMBER)
    # A word for a number is no number inside a name a fact allows: the
    # "Quarter" of a Guild Quarter. It must be with a word that is not one.
    text = sentence.text
    unsupported_name = False
    for run in reversed(list(_runs(sentence.text))):
        tokens = run.tokens
        # The word that opens a sentence is capitalised whatever it is. If it is
        # an ordinary one, what follows it is judged without it.
        if run.opens_sentence and len(tokens) > 1 and tokens[0] in ORDINARY_WORDS:
            tokens = tokens[1:]
        ordinary = len(tokens) == 1 and tokens[0] in ORDINARY_WORDS
        if not ordinary and not _within(tokens, names):
            unsupported_name = True
        elif not ordinary and any(t not in NUMBER_WORDS and t not in VAGUE_WORDS for t in tokens):
            text = f"{text[: run.start]} {text[run.end :]}"
    for quantity in _quantities(list(_words(_read_as(text))), own):
        if quantity == _VAGUE:
            return failed(VerdictReason.VAGUE_QUANTITY)
        if quantity == _NO_NUMBER or not _supported(quantity, numbers):
            return failed(VerdictReason.UNSUPPORTED_NUMBER)
    if unsupported_name:
        return failed(VerdictReason.UNSUPPORTED_NAME)
    read = list(_words(_read_as(sentence.text)))
    # The name of a vibe is a name as the name of an end is: Gritty is named for its high
    # end, and is said by name of an area it cannot place, whose fact holds no end.
    ends = frozenset(
        fact.slots[end].casefold() for fact in cited for end in _ENDS if end in fact.slots
    ) | {fact.label.casefold() for fact in cited if fact.kind is FactKind.TAG}
    if any(word in BANNED_WORDS for word in read) or _passes_a_verdict(read, ends):
        return failed(VerdictReason.BANNED_WORD)
    # A word in letters of another alphabet is one nothing here can read,
    # unless it is the fact's own: the unit of a figure, or a name.
    if any(_foreign(token) and token not in written for token in _tokens(sentence.text)):
        return failed(VerdictReason.UNSUPPORTED_NAME)
    return Verdict(ok=True, reason=VerdictReason.OK)
