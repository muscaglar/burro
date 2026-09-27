"""An amount beside a word for a period is no budget by the month, whoever reads it.

Core says what an amount is paid by, and the guard holds a model to it. Where
the week or the year was typed in a way core did not list, "£350 p.w.", "£350
per person per week", "£700 every two weeks", "£18,000 p.a.", core said nothing
of the period. A model that read the amount at its figure then had its reading
marked as the guess, and one press set a budget of £350 a month.

No call is made: a stand-in hands the answer to the reader.
"""

import pytest
from burro_api.offers import in_add_all

from .support import asked, model_budget, model_output, offers


@pytest.mark.parametrize(
    ("text", "typed", "offered"),
    [
        # The week as it is written with a mark: what it comes to is the rules' to offer.
        ("honestly \N{POUND SIGN}350 p.w.", 350, {1517}),
        ("honestly \N{POUND SIGN}350 /week", 350, {1517}),
        # A period in words core does not list: nobody can say what it comes to.
        ("honestly \N{POUND SIGN}350 this week", 350, set[int]()),
        ("honestly \N{POUND SIGN}350 week", 350, set[int]()),
        ("honestly \N{POUND SIGN}350 per person per week", 350, set[int]()),
        ("honestly \N{POUND SIGN}700 every two weeks", 700, set[int]()),
        ("honestly \N{POUND SIGN}18,000 p.a.", 18000, set[int]()),
        ("honestly \N{POUND SIGN}18,000 each year", 18000, set[int]()),
        ("honestly an annual rent of \N{POUND SIGN}18,000", 18000, set[int]()),
        # The first of two amounts by the week.
        ("honestly \N{POUND SIGN}350 to \N{POUND SIGN}400 a week", 350, {1733}),
        ("honestly \N{POUND SIGN}350 to \N{POUND SIGN}400 a week", 400, {1733}),
    ],
)
def test_a_models_reading_of_such_an_amount_at_its_figure_is_never_offered(
    text: str, typed: int, offered: set[int]
):
    budget = model_budget(amount=typed, words=text)

    result, _ = asked(model_output(budget_ops=[budget]), text=text)

    amounts = {
        edit.amount
        for offer in offers(result).values()
        for way in offer.choices
        for edit in way.operations.budget_ops
        if edit.amount
    }
    assert amounts == offered
    assert not [way for offer in offers(result).values() for way in offer.choices if way.guess]
    assert all(in_add_all(offer) is None for offer in offers(result).values())
    assert result.operations.budget_ops == ()


@pytest.mark.parametrize(
    ("text", "typed"),
    [
        ("honestly \N{POUND SIGN}1,500 a month, 3 days a week in the office", 1500),
        ("honestly \N{POUND SIGN}1,500 near a weekly market", 1500),
    ],
)
def test_an_amount_beside_a_period_that_is_said_of_something_else_is_still_offered(
    text: str, typed: int
):
    budget = model_budget(amount=typed, words=text)

    result, _ = asked(model_output(budget_ops=[budget]), text=text)

    amounts = {
        edit.amount
        for offer in offers(result).values()
        for way in offer.choices
        for edit in way.operations.budget_ops
        if edit.amount
    }
    assert amounts == {typed}
