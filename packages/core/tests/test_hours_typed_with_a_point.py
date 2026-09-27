"""Hours typed with a point are read only where they can be read one way.

"1.15 hours to Pellam Cross" was applied as a journey of 69 minutes, and "1.30
hours" as one of 78. Whoever types "1.30" has most likely typed an hour and a
half as a clock shows it, and the arithmetic makes 78 minutes of it. Nobody
can say which was meant, so neither is a number the person gave.

A half and a quarter of an hour are read, "1.5 hours", "1.25 hours", "0.75
hours": no clock shows 5 or 75 minutes after a point, and a quarter is how
part of an hour is typed. Any other part is not read, and the time is said to
be unread. Every name and every sentence here is made up.
"""

import pytest
from burro_core.grammar import Grammar
from burro_core.ids import InterpretStatus, Tenure
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter
from burro_core.ops import NO_OPERATIONS
from burro_core.places import Names
from burro_core.reading import Item, hours_at, lines_of
from burro_core.spec import default_spec

from .support import place_id, small_release

RENTER = default_spec(Tenure.RENT)
READER = RuleInterpreter()
GRAMMAR = Grammar(Names(small_release()), small_release())


def read(text: str) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=small_release()))


def items(text: str) -> list[Item]:
    (line,) = lines_of(text)
    return GRAMMAR.items(line)


def minutes_held(result: InterpretResult) -> set[int]:
    """Every number of minutes that an edit or a way of an offer holds."""
    edits = list(result.operations.commute_ops)
    for found in result.suggestions:
        for choice in found.choices:
            edits += choice.operations.commute_ops
    return {edit.max_minutes for edit in edits if edit.max_minutes}


HALVES_AND_QUARTERS = [
    ("1.5 hours", 90),
    ("0.5 hours", 30),
    ("1.25 hours", 75),
    ("0.25 hours", 15),
    ("0.75 hours", 45),
    ("1.0 hours", 60),
    ("1.00 hours", 60),
    ("1.5h", 90),
    ("1.5hrs", 90),
    ("1.5 hrs", 90),
    ("1.25h", 75),
]

READ_TWO_WAYS = [
    "1.15 hours",
    "1.30 hours",
    "1.45 hours",
    "1.05 hours",
    "1.10 hours",
    "1.20 hours",
    "1.50 hours",
    "1.2 hours",
    "1.3 hours",
    "1.4 hours",
    "1.1 hours",
    "0.1 hours",
    "1.15h",
    "1.30h",
    "1.15hrs",
    "1.30 hrs",
]


@pytest.mark.parametrize(("typed", "minutes"), HALVES_AND_QUARTERS)
def test_a_half_and_a_quarter_of_an_hour_typed_with_a_point_are_read(typed: str, minutes: int):
    (line,) = lines_of(f"{typed} to Pellam Cross")
    assert hours_at(line.tokens, 0) == (minutes, len(typed.split()))
    result = read(f"{typed} to Pellam Cross")
    assert result.status is InterpretStatus.OK
    (edit,) = result.operations.commute_ops
    assert (edit.place_id, edit.max_minutes) == (place_id(1), minutes)


@pytest.mark.parametrize("typed", READ_TWO_WAYS)
def test_any_other_part_of_an_hour_typed_with_a_point_is_no_time_the_reader_reads(typed: str):
    text = f"{typed} to Pellam Cross"
    (line,) = lines_of(text)
    assert hours_at(line.tokens, 0) is None
    assert not [found for found in items(text) if found.hours]
    result = read(text)
    # Nothing is applied, and no journey is offered at a number of minutes nobody gave.
    assert result.operations == NO_OPERATIONS
    assert minutes_held(result) == set()
    unread = [text[span.start : span.end] for span in result.unread]
    assert [left for left in unread if typed in left]


@pytest.mark.parametrize("typed", READ_TWO_WAYS)
def test_it_is_no_time_after_words_that_cap_it_or_beside_a_home_either(typed: str):
    for text in (
        f"within {typed} of Pellam Cross",
        f"at most {typed} to Pellam Cross",
        f"renting a 2 bed, {typed} to Pellam Cross",
        f"I work at Pellam Cross, {typed} max",
    ):
        result = read(text)
        assert result.operations == NO_OPERATIONS, text
        assert minutes_held(result) == set(), text
