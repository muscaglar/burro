"""An amount by the week is never an amount by the month at the same figure.

"£350 a week" was offered as "Set a budget of £350", which the search holds
by the month: a quarter of what the person can pay. A rent is held by the
month. So an amount that is said by the week is offered as what it comes to by
the month, at 52 weeks to 12 months, and the offer says that it was worked out
and from what. It is never applied, since a plain prompt has nowhere to say so.

An amount by any other period, a year, a fortnight, a night, is not read: no
rule says what it comes to, and it is said to be unread. Every sentence here
is made up.
"""

from typing import Any

import pytest
from burro_core.grammar import KNOWN_WORDS
from burro_core.ids import InterpretStatus, Tenure, UnmetCategory
from burro_core.interpret import (
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
    Suggestion,
    by_the_month,
    worked_out_by_the_month,
)
from burro_core.ops import NO_OPERATIONS
from burro_core.reducer import apply
from burro_core.spec import PreferenceSpec, default_spec
from burro_core.vocabulary import BY_ANOTHER_PERIOD, BY_THE_WEEK

from .support import small_release

RENTER = default_spec(Tenure.RENT)
BUYER = default_spec(Tenure.BUY)
READER = RuleInterpreter()
QUIET = ("unchanged", "none", "default", 0, 0.0)
WORKED_OUT = (
    "You gave £350 a week. Burro knows rents by the month, so it has worked out what that "
    "comes to, at 52 weeks to 12 months: £1,517 a month."
)


def read(text: str, spec: PreferenceSpec = RENTER) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=spec, release=small_release()))


def said(edit: Any) -> dict[str, Any]:
    """An edit with its sentinels left out."""
    return {k: v for k, v in edit.model_dump(mode="json").items() if v not in QUIET}


def amounts(result: InterpretResult) -> list[Suggestion]:
    """Every offer that would set an amount."""
    return [
        found
        for found in result.suggestions
        if any(edit.amount for way in found.choices for edit in way.operations.budget_ops)
    ]


def every_amount(result: InterpretResult) -> set[int]:
    """Every amount that some edit holds, applied or offered."""
    ways = [way for found in result.suggestions for way in found.choices]
    offered = [edit for way in ways for edit in way.operations.budget_ops]
    return {edit.amount for edit in (*result.operations.budget_ops, *offered) if edit.amount}


def unread(text: str, result: InterpretResult) -> list[str]:
    return [text[span.start : span.end] for span in result.unread]


# --- What a week comes to by the month -------------------------------------------------------


@pytest.mark.parametrize(
    ("by_the_week", "monthly"),
    [(350, 1517), (300, 1300), (100, 433), (75, 325), (1000, 4333), (461, 1998), (462, 2002)],
)
def test_a_week_comes_to_a_month_at_52_weeks_to_12_months(by_the_week: int, monthly: int):
    assert by_the_month(by_the_week) == monthly == round(by_the_week * 52 / 12)


@pytest.mark.parametrize(
    ("text", "rests_on"),
    [
        ("£350 a week", ["£350 a week"]),
        ("£350 per week", ["£350 per week"]),
        ("£350 each week", ["£350 each week"]),
        ("£350 weekly", ["£350 weekly"]),
        ("£350 pw", ["£350 pw"]),
        ("£350 p/w", ["£350 p/w"]),
        ("£350pw", ["£350pw"]),
        ("£350p/w", ["£350p/w"]),
        ("£350/week", ["£350/week"]),
        ("350pw", ["350pw"]),
        ("350 a week", ["350 a week"]),
        ("350 quid a week", ["350 quid a week"]),
        ("350 pounds per week", ["350 pounds per week"]),
        ("£350 a week, I think", ["£350 a week"]),
        ("I can pay £350 a week", ["£350 a week"]),
        # What is said of the home may stand between the amount and the week.
        ("£350 for a studio per week", ["£350 for a studio per week"]),
        ("£350 rent a week", ["£350 rent a week"]),
        # And the week may stand before the amount, with what is said of paying between.
        ("weekly rent of £350", ["weekly rent of £350"]),
        ("a weekly budget of £350", ["weekly budget of £350"]),
        ("my budget per week is £350", ["per week is £350"]),
    ],
)
def test_an_amount_by_the_week_is_offered_as_what_it_comes_to_by_the_month(
    text: str, rests_on: list[str]
):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    (budget,) = amounts(result)
    assert (budget.target, budget.label) == ("budget", "A budget of £1,517 a month")
    assert [choice.label for choice in budget.choices] == [
        "Set a budget of £1,517 a month",
        "Leave it out",
    ]
    assert said(budget.choices[0].operations.budget_ops[0]) == {
        "action": "set",
        "amount": 1517,
        "provenance": "ui_edit",
    }
    # It says that it was worked out, and from what.
    assert budget.note == WORKED_OUT == worked_out_by_the_month(350)
    # It rests on the week as on the amount, so neither is said to be unread.
    assert [text[span.start : span.end] for span in budget.spans] == rests_on
    assert not [words for words in unread(text, result) if "350" in words or "week" in words]
    # The figure that was typed is an amount by the month nowhere.
    assert every_amount(result) == {1517}
    pressed = apply(RENTER, budget.choices[0].operations, small_release())
    assert pressed.rejected == () and pressed.spec.budget.amount == 1517


def test_the_words_that_make_a_limit_firm_make_what_it_comes_to_firm():
    text = "max £350 per week for a studio"
    (budget,) = amounts(read(text))
    assert [choice.label for choice in budget.choices] == [
        "Set a budget of no more than £1,517 a month",
        "Leave it out",
    ]
    (edit,) = budget.choices[0].operations.budget_ops
    assert (edit.amount, edit.strictness) == (1517, "hard")
    assert budget.note == WORKED_OUT
    assert [text[span.start : span.end] for span in budget.spans] == ["max £350 per week"]


def test_an_amount_by_the_week_is_a_rent_whatever_the_search_holds():
    (budget,) = amounts(read("£350 a week", BUYER))
    assert [choice.label for choice in budget.choices] == [
        "Set a budget of £1,517 a month, to rent",
        "Leave it out",
    ]
    (edit,) = budget.choices[0].operations.budget_ops
    assert (edit.tenure, edit.amount) == ("rent", 1517)
    # No amount by the week is a price, however high it is.
    (dear,) = amounts(read("a house for £4,000 a week", BUYER))
    assert dear.label == "A budget of £17,333 a month"
    assert [edit.tenure for way in dear.choices for edit in way.operations.budget_ops] == ["rent"]


# --- It is never applied ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "renting a 1 bed, £350 a week",
        "renting a 1 bed for £350 a week",
        "renting, up to £350pw",
        "a studio, 350pw, near a park",
        "I rent and can pay up to £350 per week",
        "£350 weekly for a 2 bed",
        "renting a 1 bed, weekly budget of £350",
    ],
)
def test_a_prompt_that_holds_an_amount_by_the_week_is_not_plain_and_applies_nothing(text: str):
    result = read(text)
    assert (result.status, result.operations) == (InterpretStatus.SUGGEST, NO_OPERATIONS)
    (budget,) = amounts(result)
    assert budget.note == WORKED_OUT
    assert every_amount(result) == {1517}


@pytest.mark.parametrize("period", sorted(BY_THE_WEEK | BY_ANOTHER_PERIOD))
def test_no_words_for_a_period_but_the_month_are_words_of_the_grammar(period: str):
    assert not set(period.split()) <= KNOWN_WORDS
    for spec in (RENTER, BUYER):
        for text in (f"£500 {period}", f"renting a 1 bed up to £500 {period}", f"500 {period}"):
            result = read(text, spec)
            assert result.operations == NO_OPERATIONS, text
            assert 500 not in every_amount(result), text


# --- An amount by any other period ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "not_read"),
    [
        ("£18,000 a year", ["£18,000 a year"]),
        ("£18,000 per annum", ["£18,000 per annum"]),
        ("£18k pa", ["£18k pa"]),
        ("£800 a fortnight", ["£800 a fortnight"]),
        ("£800 fortnightly", ["£800 fortnightly"]),
        ("£4,500 a quarter", ["£4,500 a quarter"]),
        ("£500 a day", ["£500 a day"]),
        # The word for renting is offered for itself, and what is left is not read.
        ("a yearly rent of £18,000", ["a yearly", "of £18,000"]),
    ],
)
def test_an_amount_by_another_period_is_not_read_and_is_said_to_be_unread(
    text: str, not_read: list[str]
):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert amounts(result) == []
    assert unread(text, result) == not_read


def test_an_amount_by_the_night_is_not_read_and_is_said_to_be_what_a_place_charges():
    """What a night costs is what a stay costs, which Burro holds for no area.

    It was said to be unread, as an amount by the year is. Since 2026-09-26
    it is heard for what it is, and is no more an amount than it was.
    """
    for text in ("£600 a night", "£600 per night", "£600 nightly"):
        result = read(text)
        assert result.operations == NO_OPERATIONS
        assert amounts(result) == [] and every_amount(result) == set()
        assert UnmetCategory.PRICES_AND_HOURS in result.unmet
        assert unread(text, result) == []


def test_an_amount_by_the_week_that_comes_to_no_rent_the_search_may_hold_is_unread():
    # Under £300 a month, and over £20,000, no rent is held.
    for text in ("£50 a week", "£5,000 a week"):
        result = read(text)
        assert (result.operations, amounts(result)) == (NO_OPERATIONS, [])
        assert unread(text, result) == [text]


# --- What is said by the month, and what is said of something else ------------------------------


@pytest.mark.parametrize(
    ("text", "label"),
    [
        ("£1,500 a month, I think", "A budget of £1,500 a month"),
        ("£1,500 pcm, I think", "A budget of £1,500 a month"),
        ("£1,500, I think", "A budget of £1,500"),
        # The week is said of the days, and a word that joins stands before the amount.
        ("I work 3 days a week and can pay £1,500", "A budget of £1,500"),
        ("in the office 3 days a week for £1,500", "A budget of £1,500"),
        ("£1,500 for a flat 3 days a week from the office", "A budget of £1,500"),
        ("I am in the office twice a week, budget £1,500 a month", "A budget of £1,500 a month"),
        # The month stands against the amount, whatever is said by the week beside it.
        ("weekly shop nearby, £1,500 a month", "A budget of £1,500 a month"),
    ],
)
def test_an_amount_that_is_not_said_by_the_week_is_offered_as_it_was(text: str, label: str):
    (budget,) = amounts(read(text))
    assert (budget.label, budget.note) == (label, "")
    assert every_amount(read(text)) == {1500}


@pytest.mark.parametrize("text", ["£0 a week", "0 a week", "£0pw", "weekly rent of £0"])
def test_nothing_a_week_is_no_amount(text: str):
    for spec in (RENTER, BUYER):
        result = read(text, spec)
        assert (result.operations, amounts(result)) == (NO_OPERATIONS, [])
        assert not [found for found in result.suggestions if found.note]
        assert [words for words in unread(text, result) if "0" in words]


def test_each_of_two_amounts_is_offered_by_what_is_said_of_it():
    result = read("£350 a week or £1,500 a month")
    assert [(found.label, found.note) for found in amounts(result)] == [
        ("A budget of £1,517 a month", WORKED_OUT),
        ("A budget of £1,500 a month", ""),
    ]


def test_a_number_of_something_else_by_the_week_is_no_amount():
    for text in ("900 minutes a week on trains", "3 days a week", "2 nights a week", "5 a week"):
        result = read(text)
        assert (result.operations, amounts(result)) == (NO_OPERATIONS, []), text
