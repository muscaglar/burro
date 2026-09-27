""" "At the very most" makes a limit firm, as "at most" does.

"At most £1,500 a month" is a firm limit, and "at the very most £1,500 a
month" was a prompt that is not plain: the amount was offered as a guide, which
is less than the words say. It is the same cap said with more force, so it is
read where "at most" and "at the most" are read, before a number and after
it, of money and of minutes.

Every name and every figure here is made up.
"""

import pytest
from burro_core.ids import InterpretStatus, Tenure
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter
from burro_core.reducer import apply
from burro_core.spec import default_spec
from burro_core.vocabulary import (
    CAPS_FIRMLY,
    FIRM_OF_MINUTES,
    FIRM_OF_MONEY,
    THE_MOST_AFTER,
    WORDS_THAT_TURN_AWAY,
)

from .support import fixture_release

RENTER = default_spec(Tenure.RENT)
READER = RuleInterpreter()


def read(text: str) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=fixture_release()))


def test_it_is_a_word_that_caps_firmly_and_turns_nothing_round():
    assert "at the very most" in CAPS_FIRMLY
    assert "at the very most" in FIRM_OF_MONEY & FIRM_OF_MINUTES & THE_MOST_AFTER
    assert "at the very most" not in WORDS_THAT_TURN_AWAY


@pytest.mark.parametrize(
    "text",
    [
        "at the very most £1,500 a month",
        "£1,500 a month at the very most",
        "renting, at the very most 1500 a month",
    ],
)
def test_it_makes_a_budget_firm_as_at_most_does(text: str):
    found, as_at_most = read(text), read(text.replace("at the very most", "at most"))

    assert found.status is InterpretStatus.OK and found.suggestions == ()
    (edit,) = found.operations.budget_ops
    assert (edit.amount, edit.strictness) == (1500, "hard")
    assert found.operations == as_at_most.operations
    held = apply(RENTER, found.operations, fixture_release()).spec.budget
    assert (held.amount, held.strictness) == (1500, "hard")


@pytest.mark.parametrize(
    "text",
    [
        "at the very most 40 minutes to Pellam Cross",
        "40 minutes at the very most to Pellam Cross",
    ],
)
def test_it_makes_a_journey_firm_as_at_most_does(text: str):
    found, as_at_most = read(text), read(text.replace("at the very most", "at most"))

    assert found.status is InterpretStatus.OK and found.suggestions == ()
    (edit,) = found.operations.commute_ops
    assert (edit.max_minutes, edit.strictness) == (40, "hard")
    assert found.operations == as_at_most.operations


@pytest.mark.parametrize(
    "text",
    [
        "40 minutes to Pellam Cross at the very most",
        "Pellam Cross, 40 minutes at the very most",
        "honestly, at the very most 40 minutes to Pellam Cross",
        "honestly, at the very most 1500 a month",
        "leafy, and at the very most 40 minutes to Pellam Cross, I think",
    ],
)
def test_wherever_it_stands_it_is_read_as_at_most_is_read_there(text: str):
    found, as_at_most = read(text), read(text.replace("at the very most", "at most"))

    assert found.status is as_at_most.status
    assert found.operations == as_at_most.operations
    assert [
        (offer.target, offer.label, offer.choices, offer.note) for offer in found.suggestions
    ] == [
        (offer.target, offer.label, offer.choices, offer.note) for offer in as_at_most.suggestions
    ]
