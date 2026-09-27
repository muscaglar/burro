"""The minutes of a longer time are no number of minutes that a person typed.

A model chooses the numbers it gives, and the guard keeps a number of minutes
only where the person typed it. Core reads "1 hour 15" as one number, 75. Where
it does not read a time whole, "1 hour, 15 minutes", the 15 is part of a time
that was not read, and core never offers it by itself. The guard counted it as
a number that was typed all the same: a model that read "I work at Pellam
Exchange. 1 hour, 15 minutes at most." as a journey of 15 minutes had its
reading marked as the guess, and one press took it.

No call is made: a stand-in hands the answer to the reader.
"""

from typing import Any

import pytest
from burro_api.guard import Check
from burro_api.reader import ModelInterpreter
from burro_core.interpret import InterpretRequest

from .support import (
    MODEL,
    FakeModelClient,
    asked,
    model_commute,
    model_output,
    offers,
    release,
    renter,
    resting_on,
)


def fired(answer: Any, text: str) -> set[Check]:
    """The checks that fire on one answer to one sentence."""
    reader = ModelInterpreter(FakeModelClient(resting_on(answer, text)), MODEL, 512, 2.5)
    reader.interpret(InterpretRequest(text=text, spec=renter(), release=release()))
    return set(reader.fired)


def minutes_offered(result: Any) -> set[int]:
    return {
        edit.max_minutes
        for offer in offers(result).values()
        for way in offer.choices
        for edit in way.operations.commute_ops
    }


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        # The time stands apart from the place, so the rules offer the journey with no time.
        ("I work at Pellam Exchange. 1 hour, 15 minutes at most.", 15),
        ("I work at Pellam Exchange, 1 hour, 15 minutes at most", 15),
        ("Pellam Exchange: 1 hour, 15 minutes", 15),
        ("Pellam Exchange in 1 15", 15),
        ("Pellam Exchange, 1 hour 75", 75),
        ("Pellam Exchange, a third of an hour", 60),
    ],
)
def test_the_minutes_of_a_longer_time_are_no_number_of_minutes_a_person_typed(
    text: str, minutes: int
):
    """A model that gave them had its reading marked as the guess, and one press took it."""
    journey = model_commute(destination_text="Pellam Exchange", max_minutes=minutes, words=text)
    answer = model_output(commute_ops=[journey])

    result, _ = asked(answer, text=text)

    assert minutes_offered(result) <= {0}
    assert Check.NOT_TYPED in fired(answer, text)
    assert result.operations.commute_ops == ()


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        ("honestly 1 hour 15 to Pellam Exchange", 75),
        ("honestly three quarters of an hour to Pellam Exchange", 45),
        ("honestly 2 bed 30 minutes to Pellam Exchange", 30),
        ("I work at Pellam Exchange. Honestly 40 minutes at most.", 40),
    ],
)
def test_a_time_that_core_reads_whole_is_still_a_number_the_person_typed(text: str, minutes: int):
    journey = model_commute(destination_text="Pellam Exchange", max_minutes=minutes, words=text)
    answer = model_output(commute_ops=[journey])

    result, _ = asked(answer, text=text)

    assert minutes_offered(result) == {minutes}
    assert Check.NOT_TYPED not in fired(answer, text)
