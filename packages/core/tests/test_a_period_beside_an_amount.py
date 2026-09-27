"""An amount beside any word for a period but the month is no amount by the month.

An amount by the week is offered as what it comes to by the month, and one by
the year is not read: the reader knows each by the words it lists, "a week",
"pw", "per annum". Typed any other way the amount was still offered at the
figure that was typed, as an amount by the month: "£350 p.w.", "£350 /week",
"£350 this week", "£350 per person per week", "£700 every two weeks", "£18,000
p.a.", "annual rent of £18,000". So was the first of two amounts by the week:
"£350 to £400 a week".

The week and the year are read as they are written with a mark, "p.w.",
"/week", "p.a.". And wherever a word for a period stands beside an amount in
words the reader does not list, nobody can say what the amount comes to by the
month: it is not read, and its words are unread. Every sentence here is made up.
"""

import pytest
from burro_core.ids import Tenure, UnmetCategory
from burro_core.interpret import (
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
    Suggestion,
    worked_out_by_the_month,
)
from burro_core.ops import NO_OPERATIONS
from burro_core.spec import PreferenceSpec, default_spec
from burro_core.vocabulary import OF_A_PERIOD

from .support import small_release

RENTER = default_spec(Tenure.RENT)
BUYER = default_spec(Tenure.BUY)
READER = RuleInterpreter()


def read(text: str, spec: PreferenceSpec = RENTER) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=spec, release=small_release()))


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


@pytest.mark.parametrize(
    ("text", "rests_on"),
    [
        ("£350 p.w.", "£350 p.w"),
        ("£350 p.w", "£350 p.w"),
        ("£350 /week", "£350 /week"),
        ("£350 /wk", "£350 /wk"),
        ("£350 /pw", "£350 /pw"),
        ("up to £350 p.w. for a studio", "up to £350 p.w"),
    ],
)
def test_the_week_is_read_as_it_is_written_with_a_mark(text: str, rests_on: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    (budget,) = amounts(result)
    assert budget.note == worked_out_by_the_month(350)
    assert [text[span.start : span.end] for span in budget.spans] == [rests_on]
    assert every_amount(result) == {1517}


@pytest.mark.parametrize(
    "text",
    [
        # The week, in words the reader does not list.
        "£350 this week",
        "£350 week",
        "£350 wk",
        "£350 wkly",
        "£350 / week",
        "£350 per person per week",
        "£350 pppw",
        "£350 a weekend",
        "a week's rent of £350",
        # More weeks than one.
        "£350 biweekly",
        "£350 bi-weekly",
        "£700 every two weeks",
        "£700 every 2 weeks",
        "£700 per 2 weeks",
        "£1,400 every 4 weeks",
        "£1,400 four weekly",
        "£1,400 per 4 weeks",
        # The year, as it is written with a mark and in words the reader does not list.
        "£18,000 p.a.",
        "£18,000 p/a",
        "£18,000 /year",
        "£18,000 /yr",
        "£18,000 a yr",
        "£18,000 per yr",
        "£18,000 each year",
        "£18,000 every year",
        "£18,000 annual",
        "£18,000 annual rent",
        "annual rent of £18,000",
        "honestly an annual rent of £18,000",
        "a year's rent of £18,000",
        "honestly a week's rent of £350",
        # Any other period.
        "£1,500 termly",
        "£500 every day",
        # More months than one: what it comes to by the month is nowhere said.
        "£9,000 for 6 months",
        "£9,000 for six months",
        "£3,000 every 2 months",
        "£3,000 per 2 months",
        "£3,000 bimonthly",
        "£3,000 bi-monthly",
        "£18,000 over 12 months",
        "£1,500 for 12 months",
        "6 months rent of £9,000",
    ],
)
def test_an_amount_beside_a_word_for_a_period_is_no_amount_by_the_month(text: str):
    for spec in (RENTER, BUYER):
        result = read(text, spec)
        assert result.operations == NO_OPERATIONS, text
        assert amounts(result) == [], text
        # The amount is said to be unread, with what it is paid by.
        assert [words for words in unread(text, result) if "£" in words], text


@pytest.mark.parametrize(
    "text",
    ["£60 each night", "£500 for 3 nights", "£60 this night", "£60 per person per night"],
)
def test_an_amount_beside_a_word_for_a_night_is_no_amount_and_is_said_to_be_what_a_place_charges(
    text: str,
):
    """It is what a stay costs, which Burro holds for no area. It was said to be unread.

    Since 2026-09-26 a person may search for somewhere to stay, so what a
    night costs is heard for what it is. It is still no amount by the month,
    and the person is still told that nothing was made of it: by the name of
    what Burro has no measure of, where it was by where the words stand.
    """
    for spec in (RENTER, BUYER):
        result = read(text, spec)
        assert result.operations == NO_OPERATIONS, text
        assert amounts(result) == [] and every_amount(result) == set(), text
        assert UnmetCategory.PRICES_AND_HOURS in result.unmet, text
        assert not [words for words in unread(text, result) if "£" in words], text


@pytest.mark.parametrize(
    ("text", "offered", "not_read"),
    [
        ("£350 to £400 a week", {1733}, "£350"),
        ("between £350 and £400 a week", {1733}, "£350"),
        ("£350 or £400 a week", {1733}, "£350"),
        ("£350 to £400 per week for a 1 bed", {1733}, "£350"),
        ("£16,000 to £18,000 a year", set[int](), "£16,000"),
        # A dash between the two, typed with a space either side of it.
        ("£350 - £400 a week", {1733}, "£350"),
        ("£350 \N{EN DASH} £400 a week", {1733}, "£350"),
    ],
)
def test_the_first_of_two_amounts_by_the_week_is_no_amount_by_the_month(
    text: str, offered: set[int], not_read: str
):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert every_amount(result) == offered
    assert [words for words in unread(text, result) if not_read in words]


@pytest.mark.parametrize(
    ("text", "amount"),
    [
        # What stands straight after the amount is what it is paid by.
        ("£1,500 a month or £350 a week", 1500),
        ("£1,500 a month, 3 days a week in the office", 1500),
        # The week is said of the days, of the market and of the shop.
        ("£1,500 for a flat 3 days a week from the office", 1500),
        ("£1,500 near a weekly market", 1500),
        ("£1,500 and a weekly shop nearby", 1500),
        ("in the office 3 days a week for £1,500", 1500),
        ("next week £1,500", 1500),
        # A number of something else stands between the amount and the period.
        ("£1,500 x 52 weeks", 1500),
        # The month is said of the amount, and the months of how long the let is.
        ("£1,500 a month for 12 months", 1500),
        ("£1,500 a month for a year", 1500),
        ("£1,500 for a 6 month let", 1500),
        ("£1,500 for 2 people", 1500),
        # A mark that is no dash parts the two amounts.
        ("£1,500, £400 a week", 1500),
    ],
)
def test_a_period_that_is_said_of_something_else_leaves_the_amount_as_it_was(
    text: str, amount: int
):
    assert amount in every_amount(read(text))


def test_every_word_for_a_period_is_one_the_grammar_does_not_know():
    from burro_core.grammar import KNOWN_WORDS

    assert not OF_A_PERIOD & KNOWN_WORDS
    assert "month" not in OF_A_PERIOD and "monthly" not in OF_A_PERIOD
