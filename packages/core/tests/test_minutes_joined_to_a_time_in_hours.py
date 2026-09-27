"""Minutes that a word joins to a longer time in hours are never read by themselves.

"1 hour 15 or 20 to Pellam Infirmary" says a journey of 75 or 80 minutes. It
was offered as a journey of at most 20 minutes, and one press took it: the
reader read "1 hour 15" whole, and then the 20 as the minutes of a journey.
A number that stands after a time in hours and a word that joins, and is less
than that time, is the minutes of a second time whose hours were not said
again. It is part of a longer time, as the 15 of "1 hour, 15 minutes" is.

A number that is more than the time before it stands by itself: "half an hour
or 40 minutes" is 40 minutes at its longer end. Every name and every sentence
here is made up.
"""

import pytest
from burro_core.ids import Tenure
from burro_core.interpret import (
    IGNORE,
    TIME_NOT_TAKEN,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
)
from burro_core.ops import NO_OPERATIONS
from burro_core.spec import default_spec

from .support import small_release

RENTER = default_spec(Tenure.RENT)
READER = RuleInterpreter()


def read(text: str) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=small_release()))


def minutes_held(result: InterpretResult) -> set[int]:
    """Every number of minutes that an edit or a way of an offer holds."""
    edits = list(result.operations.commute_ops)
    for found in result.suggestions:
        for choice in found.choices:
            edits += choice.operations.commute_ops
    return {edit.max_minutes for edit in edits if edit.max_minutes}


@pytest.mark.parametrize(
    "text",
    [
        "1 hour 15 or 20 to Pellam Infirmary",
        "1 hour 15 or 20 minutes to Pellam Infirmary",
        "1 hour 15 to 20 to Pellam Infirmary",
        "an hour or 45 minutes to Pellam Infirmary",
        "1h15 or 20 to Pellam Infirmary",
        "an hour and a quarter or 20 to Pellam Infirmary",
        "ideally 1 hour 15 or 20 to Pellam Infirmary",
    ],
)
def test_minutes_after_a_longer_time_and_a_word_that_joins_are_never_offered_by_themselves(
    text: str,
):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert minutes_held(result) == set()
    (heard,) = result.suggestions
    assert (heard.choices, heard.note) == ((IGNORE,), TIME_NOT_TAKEN)


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        ("half an hour or 40 minutes to Pellam Infirmary", 40),
        ("1 hour or 90 minutes to Pellam Infirmary", 90),
        ("a quarter of an hour or 20 minutes to Pellam Infirmary", 20),
        ("an hour to an hour and a half to Pellam Infirmary, no more", 90),
        # The second time says its own hours.
        ("1 hour 15 or 1 hour 20 to Pellam Infirmary", 80),
        # Another wish stands between the two.
        ("1 hour to Pellam Cross or 20 minutes to Pellam Infirmary", 20),
    ],
)
def test_a_time_that_stands_by_itself_after_a_word_that_joins_is_still_read(
    text: str, minutes: int
):
    assert minutes in minutes_held(read(text))
