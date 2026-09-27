"""An hour that is part of a longer time is never read by itself.

"Three quarters of an hour to Pellam Cross" was offered as a journey of at most
60 minutes, and one press took it: the reader read "an hour", and left "three
quarters of" unread. "A quarter of an hour" was 60 minutes too, which is four
times what was said.

A quarter and three quarters of an hour are each a number, and are read where a
number is read, as half an hour is. Any other time in hours that stands
straight after "of" is part of what stands before it, "a third of an hour",
"the best part of an hour", unless that is what the time is the length of: "a
commute of an hour", "a maximum of an hour". It is never the time of a journey
by itself. Every name and every sentence here is made up.
"""

from typing import Any

import pytest
from burro_core.grammar import Grammar
from burro_core.ids import InterpretStatus, Tenure
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter
from burro_core.ops import NO_OPERATIONS
from burro_core.places import Names
from burro_core.reading import Is, Item, lines_of
from burro_core.spec import default_spec

from .support import place_id, small_release

RENTER = default_spec(Tenure.RENT)
READER = RuleInterpreter()
GRAMMAR = Grammar(Names(small_release()), small_release())
QUIET = ("unchanged", "none", "default", 0, 0.0)


def read(text: str) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=small_release()))


def items(text: str) -> list[Item]:
    (line,) = lines_of(text)
    return GRAMMAR.items(line)


def said(edit: Any) -> dict[str, Any]:
    """An edit with its sentinels left out."""
    return {k: v for k, v in edit.model_dump(mode="json").items() if v not in QUIET}


def minutes_held(result: InterpretResult) -> set[int]:
    """Every number of minutes that an edit or a way of an offer holds."""
    edits = list(result.operations.commute_ops)
    for found in result.suggestions:
        for choice in found.choices:
            edits += choice.operations.commute_ops
    return {edit.max_minutes for edit in edits if edit.max_minutes}


PARTS = [
    ("a quarter of an hour", 15),
    ("quarter of an hour", 15),
    ("three quarters of an hour", 45),
]


@pytest.mark.parametrize(("typed", "minutes"), PARTS)
def test_a_quarter_of_an_hour_is_read_as_one_number_of_minutes(typed: str, minutes: int):
    text = f"{typed} commute"
    time, commute = items(text)
    assert (time.what, time.value, time.unit, time.hours) == (Is.NUMBER, minutes, "min", True)
    assert text[time.start : time.end] == typed
    assert (commute.what, commute.text) == (Is.WORD, "commute")


@pytest.mark.parametrize(("typed", "minutes"), PARTS)
def test_a_journey_of_a_quarter_of_an_hour_is_applied_with_its_minutes(typed: str, minutes: int):
    text = f"{typed} to Pellam Cross"
    result = read(text)
    assert (result.status, result.unread, result.suggestions) == (InterpretStatus.OK, (), ())
    (edit,) = result.operations.commute_ops
    assert said(edit) == {
        "action": "add",
        "place_id": place_id(1),
        "max_minutes": minutes,
        "provenance": "stated",
    }
    assert [text[found.start : found.end] for found in result.rests_on] == [text]


@pytest.mark.parametrize(
    ("text", "minutes", "firm"),
    [
        ("within three quarters of an hour of Pellam Cross", 45, True),
        ("no more than a quarter of an hour to Pellam Cross", 15, True),
        ("max three quarters of an hour to Pellam Cross", 45, True),
        ("about three quarters of an hour to Pellam Cross", 45, False),
        ("I work at Pellam Cross, three quarters of an hour max", 45, True),
        ("get to Pellam Cross in a quarter of an hour", 15, False),
    ],
)
def test_what_may_be_said_of_minutes_may_be_said_of_a_part_of_an_hour(
    text: str, minutes: int, firm: bool
):
    result = read(text)
    assert result.status is InterpretStatus.OK
    (edit,) = result.operations.commute_ops
    assert (edit.place_id, edit.max_minutes) == (place_id(1), minutes)
    assert (edit.strictness == "hard") is firm


@pytest.mark.parametrize(
    "text",
    [
        "half of an hour to Pellam Cross",
        "a third of an hour to Pellam Cross",
        "two thirds of an hour to Pellam Cross",
        "three-quarters of an hour to Pellam Cross",
        "the best part of an hour to Pellam Cross",
        "the better part of an hour to Pellam Cross",
        "most of an hour to Pellam Cross",
        "a fraction of an hour to Pellam Cross",
        "a bit of an hour to Pellam Cross",
        "a tenth of 1 hour to Pellam Cross",
        "within a third of an hour of Pellam Cross",
        "no more than two thirds of an hour to Pellam Cross",
        "ideally half of an hour to Pellam Cross",
    ],
)
def test_an_hour_that_is_part_of_what_stands_before_it_is_never_read_by_itself(text: str):
    """Read by itself it is an hour, which nobody said: it was offered, and one press took it."""
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert minutes_held(result) == set()
    # The words of the time are said to be unread, the hour among them.
    unread = [text[span.start : span.end] for span in result.unread]
    assert [left for left in unread if "hour" in left]


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        ("a commute of an hour to Pellam Cross", 60),
        ("a journey of an hour to Pellam Cross", 60),
        ("a walk of half an hour to Pellam Cross", 30),
        ("a commute of 1 hour 15 to Pellam Cross", 75),
        ("a maximum of an hour to Pellam Cross", 60),
        ("a max of 1 hour to Pellam Cross", 60),
    ],
)
def test_a_time_that_a_journey_is_the_length_of_is_still_read_after_of(text: str, minutes: int):
    result = read(text)
    assert minutes_held(result) == {minutes}


def test_a_least_that_is_said_before_of_is_still_a_wish_to_stay_away():
    result = read("a minimum of an hour from Pellam Cross")
    assert result.operations == NO_OPERATIONS
    assert minutes_held(result) == set()
    (kept_away,) = result.suggestions
    assert [choice.direction.value for choice in kept_away.choices] == ["ignore"]
