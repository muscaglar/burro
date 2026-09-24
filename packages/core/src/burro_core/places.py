"""Resolving a name a person typed to a place or an area of the release.

Destinations are resolved by Burro's own index, never by a model (ADR 0002).
The text is used to look up an id and then dropped: nothing here keeps it,
returns it or puts it in an error.

Searching and resolving part ways. A search box is helped by the start of a
word, so `search_places` offers every match. Resolving turns words into a
commute or a filter with nobody looking, so it takes a name only when whole
words of it were given: "far" begins Farrowmere and names nothing.
"""

import re
import unicodedata
from collections.abc import Callable, Iterable
from typing import NamedTuple

from burro_core._record import Record
from burro_core.ids import OptionKind, PlaceKind
from burro_core.release import Release

EXACT = 1.0
# The text is whole words from the start of the name: "Pellam" for Pellam Cross.
LEADING_WORDS = 0.9
# The text is the start of the name and stops part-way through a word: "Pel".
PREFIX = 0.8
ALL_TOKENS = 0.6
# The weakest score that is taken without asking.
RESOLVED_AT = LEADING_WORDS
MAX_OPTIONS = 5

_KIND_ORDER = {kind: position for position, kind in enumerate(PlaceKind)}
_APOSTROPHES = re.compile("['`\N{RIGHT SINGLE QUOTATION MARK}]")
_NOT_WORD = re.compile(r"[^0-9a-z]+")


class Match(Record):
    id: str
    name: str
    kind: OptionKind
    score: float


class Resolution(Record):
    # The id, when one match is good enough to take without asking.
    resolved: str | None
    # Otherwise what to offer: up to five matches, best first. Empty if nothing matched.
    options: tuple[Match, ...]


def normalise(text: str) -> str:
    """Casefold, strip accents and punctuation, collapse spaces."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    bare = "".join(c for c in decomposed if not unicodedata.combining(c))
    # An apostrophe joins, so that "King's" and "Kings" are one name.
    return _NOT_WORD.sub(" ", _APOSTROPHES.sub("", bare)).strip()


class _Named(NamedTuple):
    """Something with a name, and every way of writing that name, normalised."""

    id: str
    name: str
    kind: OptionKind
    order: int  # where its kind comes when two matches score the same
    spellings: tuple[tuple[str, frozenset[str]], ...]


# The names of a release, normalised. A release never changes and its names
# are few, so each is normalised once. It holds names of a release only, and
# never what a person typed: that is normalised each time, and kept nowhere.
_NAMES: dict[str, str] = {}


def _name(name: str) -> str:
    found = _NAMES.get(name)
    if found is None:
        found = _NAMES[name] = normalise(name)
    return found


def _named(id: str, name: str, kind: OptionKind, order: int, names: Iterable[str]) -> _Named:
    normal = [_name(n) for n in names]
    return _Named(id, name, kind, order, tuple((n, frozenset(n.split())) for n in normal if n))


def _score(query: str, words: frozenset[str], named: _Named) -> float:
    best = 0.0
    for spelling, tokens in named.spellings:
        if spelling == query:
            return EXACT
        if spelling.startswith(f"{query} "):
            best = max(best, LEADING_WORDS)
        elif spelling.startswith(query):
            best = max(best, PREFIX)
        elif words <= tokens:
            best = max(best, ALL_TOKENS)
    return best


def _matches(text: str, among: tuple[_Named, ...]) -> tuple[Match, ...]:
    query = normalise(text)
    if not query:
        return ()
    words = frozenset(query.split())
    found = [(score, n) for n in among if (score := _score(query, words, n)) > 0]
    found.sort(key=lambda m: (-m[0], m[1].order, m[1].name, m[1].id))
    return tuple(Match(id=n.id, name=n.name, kind=n.kind, score=score) for score, n in found)


def _unrivalled(matches: tuple[Match, ...], at_least: float) -> str | None:
    """The id of the best match, if it scores enough and nothing else scores the same."""
    if not matches or matches[0].score < at_least:
        return None
    alone = len(matches) == 1 or matches[1].score < matches[0].score
    return matches[0].id if alone else None


def _resolve(matches: tuple[Match, ...]) -> Resolution:
    resolved = _unrivalled(matches, RESOLVED_AT)
    if resolved is not None:
        return Resolution(resolved=resolved, options=())
    return Resolution(resolved=None, options=matches[:MAX_OPTIONS])


def _exact(matches: tuple[Match, ...]) -> Resolution:
    # Nothing is offered either: the words may not have been meant as a name at all.
    return Resolution(resolved=_unrivalled(matches, EXACT), options=())


def _whole(among: tuple[_Named, ...]) -> dict[str, str]:
    """Each way of writing a name, with the id it names. One that names two things names neither."""
    found: dict[str, set[str]] = {}
    for named in among:
        for spelling, _ in named.spellings:
            found.setdefault(spelling, set()).add(named.id)
    return {spelling: next(iter(ids)) for spelling, ids in found.items() if len(ids) == 1}


class Names:
    """The names of a release, normalised once, for a caller that has many to look up."""

    def __init__(self, release: Release) -> None:
        self._places = tuple(
            _named(
                place.place_id,
                place.name,
                OptionKind(place.kind.value),
                _KIND_ORDER[place.kind],
                (place.name, *place.aliases),
            )
            for place in release.places
        )
        self._areas = tuple(
            _named(area.area_id, area.name, OptionKind.AREA, 0, (area.name, *area.aliases))
            for area in release.neighbourhoods
        )
        self._whole_places = _whole(self._places)
        self._whole_areas = _whole(self._areas)
        spellings = [spelling.split() for spelling in (*self._whole_places, *self._whole_areas)]
        # The most words any name is written in, and the words a name can begin
        # with, so that a reader knows where to look for one and how far.
        self.longest = max((len(words) for words in spellings), default=0)
        self.first_words = frozenset(words[0] for words in spellings if words)

    def search_places(self, text: str, limit: int) -> tuple[Match, ...]:
        return _matches(text, self._places)[: max(limit, 0)]

    def resolve_place(self, text: str) -> Resolution:
        return _resolve(_matches(text, self._places))

    def resolve_area(self, text: str) -> Resolution:
        return _resolve(_matches(text, self._areas))

    def exact_place(self, text: str) -> Resolution:
        """The place whose whole name or alias this is, and otherwise nothing.

        For words that follow "near", which as often open a phrase that names
        no place: "near far too many pubs".
        """
        return _exact(_matches(text, self._places))

    def exact_area(self, text: str) -> Resolution:
        """As `exact_place`, for the words after "not", "avoid" and "only"."""
        return _exact(_matches(text, self._areas))

    def whole_place(self, words: str) -> str | None:
        """The place these words are the whole name of, or an alias of, and no other place.

        The words are as `normalise` leaves them. It answers as `exact_place`
        does, without scoring every name: a reader asks it of every run of
        words in a request, to know where a name stands before it reads
        anything else.
        """
        return self._whole_places.get(words)

    def whole_area(self, words: str) -> str | None:
        """As `whole_place`, over the names and aliases of areas."""
        return self._whole_areas.get(words)


Resolver = Callable[[str], Resolution]


def search_places(text: str, release: Release, limit: int) -> tuple[Match, ...]:
    """The places that match, best first, cut to `limit`.

    A place scores by the best of its name and aliases: 1.0 for an exact
    match, 0.9 when the text is whole words from the start of the name, 0.8
    when it is the start of the name and stops part-way through a word, 0.6
    when every word of the text appears in it. Ties go by kind, then name,
    then id.
    """
    return Names(release).search_places(text, limit)


def resolve_place(text: str, release: Release) -> Resolution:
    """The place a name means, or what to ask.

    It is resolved when the best match is exact, or is whole words from the
    start of a name, and no other match scores the same. Part of a word, or a
    match on words alone, is too weak to take without asking.
    """
    return Names(release).resolve_place(text)


def resolve_area(text: str, release: Release) -> Resolution:
    """As `resolve_place`, over the names and aliases of areas."""
    return Names(release).resolve_area(text)
