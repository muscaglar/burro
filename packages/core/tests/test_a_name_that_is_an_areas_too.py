"""The name of an area is no rule for the area where the words say something else of it.

"Visiting my mother in Pellam Cross" was offered as a rule for the area: to
look only there, or to leave it out. Neither is what was said, and a client
that takes what is offered looked only in Pellam Cross, so that one area was
ranked and 21 were left out on a guess. So were "my mother lives in Pellam
Cross", "staying with friends in Foxholt", "I want to stay in Foxholt" and "a
hotel in Pellam Cross".

Where the words say that somebody else is there, or that a person wants to be
near a place or to stay in it, the name is where that is, and no rule. A name
that is a place's too is offered as a journey to the place, which moves areas
by how near they are and leaves none out. A name that is an area's alone is
offered as nothing: Burro holds no journey to an area, so its words are said to
be unread. The words that make a rule make it still: "only in", "not in".

Every name and every sentence here is made up, and the first list is the
sentences the service was driven with.
"""

import pytest
from burro_core.ids import AreaAction, Tenure
from burro_core.interpret import (
    MAY_BE_ANOTHERS,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
)
from burro_core.ops import NO_OPERATIONS
from burro_core.reducer import apply
from burro_core.spec import default_spec

from .support import fixture_release

RENTER = default_spec(Tenure.RENT)
READER = RuleInterpreter()
PLACES = {place.name: place.place_id for place in fixture_release().places}
AREAS = {area.name: area.area_id for area in fixture_release().neighbourhoods}
# A name that is an area's and a station's, and one that is an area's alone.
assert {"Pellam Cross", "Foxholt"} <= set(PLACES) & set(AREAS)
assert "Alderwick" in AREAS and "Alderwick" not in PLACES


def read(text: str) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=fixture_release()))


def rules(result: InterpretResult) -> list[tuple[str, AreaAction]]:
    """Every rule for an area that is applied or offered: the area, and what is done with it."""
    every = [result.operations, *(c.operations for f in result.suggestions for c in f.choices)]
    return [(edit.area_id, edit.action) for operations in every for edit in operations.area_ops]


def journeys(result: InterpretResult) -> list[tuple[str, int, str]]:
    """Every journey that is offered: where it leads, its minutes, and what is said of it."""
    return [
        (edit.place_id, edit.max_minutes, found.note)
        for found in result.suggestions
        for choice in found.choices
        for edit in choice.operations.commute_ops
    ]


def unread(text: str, result: InterpretResult) -> str:
    return " / ".join(text[span.start : span.end] for span in result.unread)


PELLAM, FOXHOLT = PLACES["Pellam Cross"], PLACES["Foxholt"]
DRIVEN = [
    ("visiting my mother in Pellam Cross", (PELLAM, 0, MAY_BE_ANOTHERS)),
    ("my mother lives in Pellam Cross", (PELLAM, 0, MAY_BE_ANOTHERS)),
    ("staying with friends in Foxholt", (FOXHOLT, 0, "")),
    ("I want to stay in Foxholt", (FOXHOLT, 0, "")),
    ("a hotel in Pellam Cross", (PELLAM, 0, "")),
    ("Pellam Cross in under 25", (PELLAM, 25, "")),
]
MORE = [
    # Somebody else is there.
    ("my mum is in Foxholt", (FOXHOLT, 0, MAY_BE_ANOTHERS)),
    ("honestly, my sister lives by Pellam Cross", (PELLAM, 0, MAY_BE_ANOTHERS)),
    ("my boss lives around Foxholt", (FOXHOLT, 0, MAY_BE_ANOTHERS)),
    # One of the household works there, which is a place the household must reach.
    ("my partner works in Pellam Cross", (PELLAM, 0, "")),
    # A person wants to stay there, or to visit.
    ("staying in Foxholt, honestly", (FOXHOLT, 0, "")),
    ("honestly, visiting Pellam Cross", (PELLAM, 0, "")),
    ("zebra, a weekend away in Foxholt", (FOXHOLT, 0, "")),
    ("we want somewhere to stay in Pellam Cross, honestly", (PELLAM, 0, "")),
]


@pytest.mark.parametrize(("text", "journey"), [*DRIVEN, *MORE])
def test_a_name_that_is_a_places_too_is_a_journey_and_no_rule(
    text: str, journey: tuple[str, int, str]
):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert rules(result) == []
    assert journeys(result) == [journey]
    # To take it leaves no area out.
    (offer,) = (found for found in result.suggestions if found.target == "commute")
    taken = apply(RENTER, offer.choices[0].operations, fixture_release())
    assert taken.rejected == () and taken.spec.areas == ()
    assert [commute.strictness for commute in taken.spec.commutes] == ["soft"]


AN_AREAS_ALONE = [
    "my mother lives in Alderwick",
    "visiting my mother in Alderwick",
    "staying with friends in Alderwick",
    "I want to stay in Alderwick",
    "a hotel in Alderwick",
    "I want to be near Alderwick",
    "my mother lives near Alderwick",
    "honestly, close to Alderwick",
    "staying put in Alderwick",
]


@pytest.mark.parametrize("text", AN_AREAS_ALONE)
def test_a_name_that_is_an_areas_alone_is_offered_as_nothing_and_is_said_to_be_unread(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert rules(result) == [] and journeys(result) == []
    assert "area" not in {found.target for found in result.suggestions}
    assert "Alderwick" in unread(text, result)


EITHER = [(AreaAction.ONLY, False), (AreaAction.EXCLUDE, False)]
STILL_A_RULE = [
    # The name alone, and what says where a person wants to live: which rule is meant is
    # theirs to say, and both are offered.
    ("Foxholt", EITHER),
    ("in Foxholt", EITHER),
    ("I want to live in Foxholt", EITHER),
    ("I like Alderwick", EITHER),
    # Somebody else is named, and is not said to be there.
    ("my mate reckons Pellam Cross is nice", EITHER),
    # The words that make a rule make it, whoever else is named and whatever is stayed in.
    ("only in Foxholt", [(AreaAction.ONLY, True)]),
    ("not in Alderwick", [(AreaAction.EXCLUDE, True)]),
    ("a hotel, only in Pellam Cross", [(AreaAction.ONLY, True)]),
    ("my mother says anywhere but Alderwick", [(AreaAction.EXCLUDE, False)]),
    ("honestly, staying, but not in Foxholt", [(AreaAction.EXCLUDE, False)]),
]


@pytest.mark.parametrize(("text", "made"), STILL_A_RULE)
def test_a_rule_for_an_area_is_made_as_it_was(text: str, made: list[tuple[AreaAction, bool]]):
    result = read(text)
    applied = [(edit.action, True) for edit in result.operations.area_ops]
    offered = [
        (edit.action, False)
        for found in result.suggestions
        for choice in found.choices
        for edit in choice.operations.area_ops
    ]
    assert [*applied, *offered] == made
    assert journeys(result) == []
