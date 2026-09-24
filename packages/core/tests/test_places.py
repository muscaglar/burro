import dataclasses

import pytest
from burro_core.ids import OptionKind, PlaceKind
from burro_core.places import (
    Names,
    Resolution,
    normalise,
    resolve_area,
    resolve_place,
    search_places,
)
from burro_core.release import InMemoryRelease, Place

from .support import area_id, place, place_id, small_release


def with_places(*extra: Place) -> InMemoryRelease:
    release = small_release()
    return dataclasses.replace(release, places=(*release.places, *extra))


def named(number: int, name: str, kind: PlaceKind, *aliases: str) -> Place:
    return place(1).replace(place_id=place_id(number), name=name, kind=kind, aliases=aliases)


@pytest.mark.parametrize(
    ("text", "normal"),
    [
        ("Pellam Cross", "pellam cross"),
        ("  PELLAM   cross!! ", "pellam cross"),
        ("St. Orlop's Road", "st orlops road"),
        ("Café Wexmoor", "cafe wexmoor"),
        ("Foxholt-on-the-Marsh", "foxholt on the marsh"),
        ("Quill\N{RIGHT SINGLE QUOTATION MARK}s Reach", "quills reach"),
        ("", ""),
        ("?!", ""),
    ],
)
def test_a_name_is_normalised_before_it_is_compared(text: str, normal: str):
    assert normalise(text) == normal


def test_an_exact_name_or_alias_resolves():
    release = small_release()
    assert resolve_place("Foxholt Works", release).resolved == place_id(2)
    assert resolve_place("foxholt works.", release).resolved == place_id(2)
    assert resolve_place("Wexmoor", release).resolved == place_id(3)  # an alias
    assert resolve_place("Pellam Cross Station", release).resolved == place_id(1)
    assert resolve_place("Foxholt Works", release).options == ()


def test_whole_words_from_the_start_of_a_name_resolve_when_nothing_else_matches_as_well():
    release = with_places(named(9, "Knurl Hospital", PlaceKind.HOSPITAL))
    assert resolve_place("Knurl", release).resolved == place_id(9)
    assert resolve_place("Pellam Cross", release).resolved == place_id(1)
    # Two places start with "Pellam", so neither is taken without asking.
    found = resolve_place("Pellam", release)
    assert found.resolved is None
    assert [(o.name, o.kind, o.score) for o in found.options] == [
        ("Pellam Cross", OptionKind.STATION, 0.9),
        ("Pellam Infirmary", OptionKind.HOSPITAL, 0.9),
    ]


@pytest.mark.parametrize("text", ["Foxh", "Foxholt W", "f", "Pellam Infirm", "wex"])
def test_part_of_a_word_is_never_taken_without_asking(text: str):
    # "Far" begins Farrowmere, and "b" begins Brackenhythe. A person who types
    # either has not named a place, so the most they can be is asked.
    found = resolve_place(text, small_release())
    assert found.resolved is None
    assert [o.score for o in found.options] == [0.8]
    # A search box is still helped by it.
    assert [m.id for m in search_places(text, small_release(), 5)] == [found.options[0].id]


def test_no_single_letter_and_no_ordinary_word_resolves_to_anything():
    release = small_release()
    words = "far too not near only avoid a an the in at to from work park station quiet"
    for text in (*"abcdefghijklmnopqrstuvwxyz", *words.split()):
        assert resolve_place(text, release).resolved is None, text
        assert resolve_area(text, release).resolved is None, text


def test_a_cue_that_does_not_expect_a_name_takes_only_the_whole_of_one():
    names = Names(small_release())
    assert names.exact_area("Cindermoor").resolved == area_id(3)
    assert names.exact_area("dulcimer green").resolved == area_id(4)
    assert names.exact_place("Wexmoor").resolved == place_id(3)  # an alias
    # Whole words from the start of a name are not the whole of it.
    for text in ("Dulcimer", "far", "Pellam", "Foxholt W", ""):
        assert names.exact_area(text) == Resolution(resolved=None, options=())
        assert names.exact_place(text) == Resolution(resolved=None, options=())


def test_an_exact_match_beats_a_prefix_of_another_name():
    release = with_places(named(9, "Pellam", PlaceKind.DISTRICT))
    assert resolve_place("Pellam", release).resolved == place_id(9)


def test_a_match_on_words_alone_is_too_weak_to_take_without_asking():
    found = resolve_place("University", small_release())
    assert found.resolved is None
    assert [(o.id, o.score) for o in found.options] == [(place_id(3), 0.6)]
    assert resolve_place("Works Foxholt", small_release()).resolved is None


def test_a_name_that_matches_nothing_gives_no_options():
    for text in ("Nowhereville", "", "   ", "cross pellam station road"):
        found = resolve_place(text, small_release())
        assert (found.resolved, found.options) == (None, ())


def test_matches_are_ordered_by_score_then_kind_then_name_then_id():
    release = with_places(
        named(11, "Knurl Hospital", PlaceKind.HOSPITAL),
        named(12, "Knurl Academy", PlaceKind.SCHOOL),
        named(13, "Knurl", PlaceKind.LANDMARK),
        named(14, "Knurl Street", PlaceKind.STATION),
        named(15, "Knurl Green", PlaceKind.STATION),
        named(16, "Knurl Green", PlaceKind.STATION),
        named(17, "Old Knurl", PlaceKind.DISTRICT),
        named(18, "Knurlow Fields", PlaceKind.STATION),
    )
    found = search_places("knurl", release, 10)
    assert [(m.id, m.score) for m in found] == [
        (place_id(13), 1.0),  # exact
        (place_id(15), 0.9),  # then its leading words: stations first, by name, then by id
        (place_id(16), 0.9),
        (place_id(14), 0.9),
        (place_id(11), 0.9),
        (place_id(12), 0.9),
        (place_id(18), 0.8),  # then a name it is only the start of a word of
        (place_id(17), 0.6),  # then a match on words alone
    ]
    assert search_places("knurl", release, 3) == found[:3]
    assert search_places("knurl", release, 0) == ()
    # No more than five options are ever offered.
    crowded = with_places(*(named(20 + n, f"Knurl {n}", PlaceKind.SCHOOL) for n in range(8)))
    assert len(resolve_place("knurl", crowded).options) == 5


def test_an_area_is_resolved_by_its_name_or_an_alias():
    release = small_release()
    assert resolve_area("Cindermoor", release).resolved == area_id(3)
    assert resolve_area("dulcimer green", release).resolved == area_id(4)
    assert resolve_area("Dulcimer", release).resolved == area_id(4)
    assert resolve_area("Green", release).resolved is None
    assert [o.kind for o in resolve_area("Green", release).options] == [OptionKind.AREA]
    assert resolve_area("Pellam Cross", release).options == ()

    aliased = dataclasses.replace(
        release,
        neighbourhoods=tuple(
            n.replace(aliases=("The Clinkers",)) if n.area_id == area_id(3) else n
            for n in release.neighbourhoods
        ),
    )
    assert resolve_area("the clinkers", aliased).resolved == area_id(3)


def test_what_was_typed_is_in_nothing_that_comes_back():
    # What is offered is the name as the release writes it, never the words as typed.
    typed = "foxholt  WOR"
    found = resolve_place(typed, small_release())
    assert [option.name for option in found.options] == ["Foxholt Works"]
    assert typed not in found.model_dump_json()
    assert "WOR" not in found.model_dump_json()
    nothing = resolve_place("my secret clinic", small_release())
    assert "secret" not in nothing.model_dump_json()
