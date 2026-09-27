"""Hours typed as "h" after a space are hours, and the minutes after them are theirs.

"1h30 to Pellam Cross" is read as 90 minutes. "1 h 30 to Pellam Cross", with a
space before the letter, was offered as a journey of at most 30 minutes, and
one press took it: the reader knew "hour" and "hr" as a word for hours and did
not know "h". It is the fault that "1 hour 15" had.

After a number in figures "h" is a word for hours, so "1 h 30" is one number,
90. After anything else it is a letter the reader does not know, and a number
that stands after it is still never read by itself. Every name and every
sentence here is made up.
"""

import pytest
from burro_core.ids import InterpretStatus, Tenure
from burro_core.interpret import (
    IGNORE,
    TIME_NOT_TAKEN,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
)
from burro_core.ops import NO_OPERATIONS
from burro_core.reading import hours_at, lines_of
from burro_core.reducer import apply
from burro_core.spec import default_spec

from .support import place_id, small_release

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
    ("typed", "minutes"),
    [
        ("1 h", 60),
        ("1 h 30", 90),
        ("1 h 15 mins", 75),
        ("1 h 5", 65),
        ("1.5 h", 90),
        ("0.5 h", 30),
    ],
)
def test_a_figure_and_the_letter_h_are_a_time_in_hours(typed: str, minutes: int):
    text = f"{typed} to Pellam Cross"
    (line,) = lines_of(text)
    assert hours_at(line.tokens, 0) == (minutes, len(typed.split()))
    result = read(text)
    assert (result.status, result.unread, result.suggestions) == (InterpretStatus.OK, (), ())
    (edit,) = result.operations.commute_ops
    assert (edit.place_id, edit.max_minutes) == (place_id(1), minutes)
    assert [text[found.start : found.end] for found in result.rests_on] == [text]


def test_a_time_beyond_what_a_journey_may_take_is_turned_away_as_any_other():
    result = read("2 h to Pellam Cross")
    (edit,) = result.operations.commute_ops
    assert edit.max_minutes == 120
    assert [found.reason for found in apply(RENTER, result.operations, small_release()).rejected]


@pytest.mark.parametrize(
    "text",
    [
        # A mark parts the hours from the minutes.
        "1 h, 30 to Pellam Infirmary",
        "1 h; 30 minutes to Pellam Infirmary",
        # The letter with no figure before it.
        "h 30 to Pellam Infirmary",
        "a few h 30 minutes to Pellam Infirmary",
        "an h to Pellam Infirmary",
        "one h 30 to Pellam Infirmary",
    ],
)
def test_minutes_after_the_letter_are_never_offered_by_themselves(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert minutes_held(result) == set()
    (heard,) = result.suggestions
    assert (heard.choices, heard.note) == ((IGNORE,), TIME_NOT_TAKEN)


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        # The letter is parted from the minutes by a mark, and names a flat.
        ("flat h, 30 minutes to Pellam Infirmary", 30),
        ("block h. 30 minutes to Pellam Infirmary", 30),
    ],
)
def test_the_letter_beyond_a_mark_is_no_part_of_the_time(text: str, minutes: int):
    assert minutes_held(read(text)) == {minutes}
