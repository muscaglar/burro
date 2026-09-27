"""A journey that the words make a walk is a walk.

"Walking distance to Pellam Cross" was applied as a journey of 45 minutes by
public transport, with the way of travelling said to be assumed. The words
said how it is travelled: on foot. So the words for near that say a walk make
the journey to a place one on foot, in a plain prompt and in an offer alike.

How a journey is travelled is read where it stands beside the place, in the
words the grammar lists: before the name, between the minutes and the name,
and straight after the name. Where two ways are said of one journey nobody
can say which is meant, and none is taken. Every name and every sentence here
is made up.
"""

from typing import Any

import pytest
from burro_core.ids import AssumptionCode, InterpretStatus, OpsGroup, Tenure
from burro_core.interpret import (
    MAY_BE_ANOTHERS,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
)
from burro_core.ops import NO_OPERATIONS
from burro_core.reducer import apply
from burro_core.spec import default_spec

from .support import place_id, small_release

RENTER = default_spec(Tenure.RENT)
READER = RuleInterpreter()
QUIET = ("unchanged", "none", "default", 0, 0.0)


def read(text: str) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=small_release()))


def said(edit: Any) -> dict[str, Any]:
    """An edit with its sentinels left out."""
    return {k: v for k, v in edit.model_dump(mode="json").items() if v not in QUIET}


def journeys(result: InterpretResult) -> list[tuple[str, dict[str, Any]]]:
    """Each way a journey is offered, as its label says it and as its edit holds it."""
    return [
        (choice.label, said(choice.operations.commute_ops[0]))
        for found in result.suggestions
        if found.target == "commute"
        for choice in found.choices
        if choice.operations.commute_ops
    ]


def rested(text: str, result: InterpretResult) -> list[list[str]]:
    return [[text[s.start : s.end] for s in found.spans] for found in result.suggestions]


def unread(text: str, result: InterpretResult) -> list[str]:
    return [text[span.start : span.end] for span in result.unread]


# --- A plain prompt ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "walking distance to Pellam Cross",
        "walking distance of Pellam Cross",
        "within walking distance of Pellam Cross",
        "a short walk to Pellam Cross",
        "a short walk from Pellam Cross",
        "I can walk to Pellam Cross",
        "we can walk to Pellam Cross",
        "able to walk to Pellam Cross",
        "walking distance to the Pellam Cross",
        "I want to be within walking distance of Pellam Cross",
        "leafy, walking distance to Pellam Cross",
    ],
)
def test_the_words_for_near_that_say_a_walk_make_the_journey_one_on_foot(text: str):
    result = read(text)
    assert (result.status, result.unread, result.suggestions) == (InterpretStatus.OK, (), ())
    (edit,) = result.operations.commute_ops
    assert said(edit) == {
        "action": "add",
        "place_id": place_id(1),
        "mode": "walk",
        "provenance": "stated",
    }
    # The way was said. How long and how firm were not, and are said to be assumed.
    assumed = {found.code for found in result.assumptions if found.group is OpsGroup.COMMUTE}
    assert assumed == {AssumptionCode.MAX_MINUTES, AssumptionCode.STRICTNESS}
    after = apply(RENTER, result.operations, small_release())
    assert after.rejected == ()
    assert [(c.place_id, c.mode, c.max_minutes, c.strictness) for c in after.spec.commutes] == [
        (place_id(1), "walk", 45, "soft")
    ]


@pytest.mark.parametrize(
    "text",
    [
        "near Pellam Cross",
        "close to Pellam Cross",
        "next to Pellam Cross",
        "not far from Pellam Cross",
        "easy access to Pellam Cross",
        "by Pellam Cross",
    ],
)
def test_the_words_for_near_that_name_no_way_leave_the_way_to_be_assumed(text: str):
    result = read(text)
    (edit,) = result.operations.commute_ops
    assert said(edit) == {"action": "add", "place_id": place_id(1), "provenance": "stated"}
    assert AssumptionCode.MODE in {found.code for found in result.assumptions}


@pytest.mark.parametrize(
    ("text", "mode"),
    [
        ("close to Pellam Cross on foot", "walk"),
        ("near Pellam Cross by bike", "cycle"),
        ("near Pellam Cross by tube", "pt"),
        # The same way said twice is one way.
        ("walking distance to Pellam Cross on foot", "walk"),
        ("I walk to Pellam Cross on foot", "walk"),
        ("I cycle to Pellam Cross by bike", "cycle"),
    ],
)
def test_a_way_that_is_said_after_the_place_is_the_way_as_it_was(text: str, mode: str):
    (edit,) = read(text).operations.commute_ops
    assert edit.mode == mode


@pytest.mark.parametrize(
    ("text", "label"),
    [
        ("walking distance to Pellam Cross by bike", "Add a journey to Pellam Cross"),
        ("within walking distance of Pellam Cross by tube", "Add a journey to Pellam Cross"),
        ("I cycle to Pellam Cross on foot", "Add a journey to Pellam Cross"),
        ("I walk to Pellam Cross by bike", "Add a journey to Pellam Cross"),
        (
            "a 20 minute walk to Pellam Cross by tube",
            "Add a journey to Pellam Cross within 20 minutes",
        ),
        (
            "a 20 minute bike ride to Pellam Cross on foot",
            "Add a journey to Pellam Cross within 20 minutes",
        ),
    ],
)
def test_two_ways_said_of_one_journey_are_not_plain_and_neither_is_taken(text: str, label: str):
    """Nobody can say which is meant. The second was taken, whatever the first said."""
    result = read(text)
    assert (result.status, result.operations) == (InterpretStatus.SUGGEST, NO_OPERATIONS)
    ((offered, edit),) = journeys(result)
    assert offered == label
    assert "mode" not in edit


def test_a_thing_that_is_wanted_within_a_walk_is_a_wish_and_no_journey():
    for text in ("walking distance to a park", "a park I can walk to", "a short walk to a station"):
        result = read(text)
        assert result.status is InterpretStatus.OK, text
        assert result.operations.commute_ops == ()
        assert result.operations.weight_ops != ()


# --- A prompt that is not plain ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "label", "words", "mode"),
    [
        (
            "ideally walking distance to Pellam Cross",
            "Add a journey to Pellam Cross on foot",
            "walking distance to Pellam Cross",
            "walk",
        ),
        (
            "ideally within walking distance of Pellam Cross",
            "Add a journey to Pellam Cross on foot",
            "within walking distance of Pellam Cross",
            "walk",
        ),
        (
            "ideally a short walk to Pellam Cross",
            "Add a journey to Pellam Cross on foot",
            "a short walk to Pellam Cross",
            "walk",
        ),
        (
            "ideally I can walk to Pellam Cross",
            "Add a journey to Pellam Cross on foot",
            "I can walk to Pellam Cross",
            "walk",
        ),
        (
            "I walk to work at Pellam Cross, I think",
            "Add a journey to Pellam Cross on foot",
            "walk to work at Pellam Cross",
            "walk",
        ),
        (
            "I cycle to Pellam Cross, I think",
            "Add a journey to Pellam Cross by bike",
            "cycle to Pellam Cross",
            "cycle",
        ),
        (
            "a 25 minute walk to Pellam Cross would suit",
            "Add a journey to Pellam Cross within 25 minutes on foot",
            "25 minute walk to Pellam Cross",
            "walk",
        ),
        (
            "a 20 minute bike ride to Pellam Cross, I think",
            "Add a journey to Pellam Cross within 20 minutes by bike",
            "20 minute bike ride to Pellam Cross",
            "cycle",
        ),
        (
            "20 minutes to Pellam Cross on foot, I think",
            "Add a journey to Pellam Cross within 20 minutes on foot",
            "20 minutes to Pellam Cross on foot",
            "walk",
        ),
        (
            "at most 20 minutes to Pellam Cross by bike, I think",
            "Add a journey to Pellam Cross of no more than 20 minutes by bike",
            "at most 20 minutes to Pellam Cross by bike",
            "cycle",
        ),
        (
            "20 minutes to Pellam Cross by tube, I think",
            "Add a journey to Pellam Cross within 20 minutes by public transport",
            "20 minutes to Pellam Cross by tube",
            "pt",
        ),
    ],
)
def test_a_journey_that_is_offered_holds_the_way_that_stands_beside_its_place(
    text: str, label: str, words: str, mode: str
):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    ((offered, edit),) = journeys(result)
    assert (offered, edit["mode"]) == (label, mode)
    # It rests on the words that say the way, so they are not said to be unread.
    assert rested(text, result) == [[words]]
    assert not [left for left in unread(text, result) if "walk" in left or "foot" in left]
    (journey,) = result.suggestions
    pressed = apply(RENTER, journey.choices[0].operations, small_release())
    assert pressed.rejected == ()
    assert [c.mode for c in pressed.spec.commutes] == [mode]


@pytest.mark.parametrize(
    "text",
    [
        # The walk is said of the park, and the bike of nothing that is named.
        "30 minutes to Pellam Cross and a park I can walk to, I think",
        "a park within walking distance and 30 minutes to Pellam Cross, I think",
        "30 minutes to Pellam Cross, I think, and I cycle a lot",
        # Two ways stand beside the one place.
        "I cycle to Pellam Cross on foot, I think",
        "a 20 minute walk to Pellam Cross by bike, I think",
        # A way that the words for a journey do not list.
        "I drive to Pellam Cross, I think",
        "my partner walks to Pellam Cross",
    ],
)
def test_a_way_that_stands_apart_from_the_place_or_beside_another_way_is_not_taken(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    ((_, edit),) = journeys(result)
    assert "mode" not in edit


@pytest.mark.parametrize(
    "text",
    [
        "not within walking distance of Pellam Cross",
        "not walking distance to Pellam Cross",
        "I don't want to walk to Pellam Cross",
        "nowhere near walking distance of Pellam Cross",
        "I hate the walk to Pellam Cross",
    ],
)
def test_a_walk_that_is_turned_away_is_offered_as_no_journey(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert journeys(result) == []


def test_a_place_that_may_be_somebody_elses_is_offered_on_foot_and_still_says_so():
    result = read("my ex is within walking distance of Pellam Cross")
    ((label, edit),) = journeys(result)
    assert (label, edit["mode"]) == ("Add a journey to Pellam Cross on foot", "walk")
    (journey,) = result.suggestions
    assert journey.note == MAY_BE_ANOTHERS


@pytest.mark.parametrize(
    ("text", "label"),
    [
        ("ideally not far from Pellam Cross", "Add a journey to Pellam Cross"),
        ("ideally close to Pellam Cross", "Add a journey to Pellam Cross"),
        ("ideally easy access to Pellam Cross", "Add a journey to Pellam Cross"),
    ],
)
def test_what_says_near_and_names_no_way_is_offered_with_no_way(text: str, label: str):
    ((offered, edit),) = journeys(read(text))
    assert offered == label
    assert "mode" not in edit
