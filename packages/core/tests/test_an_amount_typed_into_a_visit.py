"""An amount typed into a visit is said to be what a visit cannot hold, however it is typed.

A visit holds no budget: Burro holds no price of somewhere to stay. Typed
plainly into a visit, "up to £2,000" is offered with nothing to choose and the
sentence that says why. Typed with one word more, "honestly, up to £2,000", it
was dropped. An amount alone was taken to name a rent or a price by its size,
so the budget was tried on the visit, was turned away, and was said to be what
the data does not hold: which is untrue of a release that holds both, and which
a client says in words about data.

On a visit, and beside the words for one, an amount alone names no kind of
search. By the month it is a rent still, and the words for renting and buying
say which they mean. Every name and every figure here is made up, and the first
four sentences are the ones the service was driven with.
"""

import pytest
from burro_core.ids import InterpretStatus, Tenure
from burro_core.interpret import (
    IGNORE,
    NO_BUDGET_ON_A_VISIT,
    NO_STEP_ON_A_VISIT,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
)
from burro_core.ops import NO_OPERATIONS
from burro_core.reducer import apply
from burro_core.spec import PreferenceSpec, default_spec

from .support import fixture_release

RENTER = default_spec(Tenure.RENT)
VISITOR = default_spec(Tenure.VISIT)
READER = RuleInterpreter()


def read(text: str, spec: PreferenceSpec = VISITOR) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=spec, release=fixture_release()))


def budgets(result: InterpretResult) -> list[tuple[str, str, int]]:
    """Each offer of a budget: what it is called, what is said of it, and how many ways it has."""
    return [
        (found.label, found.note, len(found.choices) - 1)
        for found in result.suggestions
        if found.target == "budget"
    ]


DRIVEN = [
    ("honestly, up to £2,000", "A budget of £2,000", "up to £2,000"),
    ("my budget is £2,000 honestly", "A budget of £2,000", "£2,000"),
    ("honestly £2,000 max", "A budget of £2,000", "£2,000 max"),
    ("somewhere lively honestly, up to £2,000", "A budget of £2,000", "up to £2,000"),
]
MORE = [
    # An amount that can only be a price, by its size.
    ("honestly, £400k", "A budget of £400,000", "£400k"),
    ("zebra, max £450,000", "A budget of £450,000", "max £450,000"),
    # And one that can be neither a rent nor a price.
    ("honestly, around £90", "A budget of £90", "£90"),
]


@pytest.mark.parametrize(("text", "label", "words"), [*DRIVEN, *MORE])
def test_an_amount_typed_into_a_visit_is_said_to_be_what_a_visit_cannot_hold(
    text: str, label: str, words: str
):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert budgets(result) == [(label, NO_BUDGET_ON_A_VISIT, 0)]
    (amount,) = (found for found in result.suggestions if found.target == "budget")
    assert amount.choices == (IGNORE,)
    assert [text[span.start : span.end] for span in amount.spans] == [words]
    # It is not said to be what the data does not hold, which a release may hold.
    assert result.not_in_release == ()
    assert result.status is InterpretStatus.SUGGEST
    assert apply(VISITOR, result.operations, fixture_release()).spec == VISITOR


@pytest.mark.parametrize(
    ("text", "words"),
    [
        ("visiting, honestly, up to £2,000", "up to £2,000"),
        ("honestly, a hotel, up to £2,000", "up to £2,000"),
        ("zebra, a city break, £400k", "£400k"),
    ],
)
@pytest.mark.parametrize("spec", [RENTER, VISITOR], ids=["renting", "visiting"])
def test_an_amount_beside_the_words_for_a_visit_is_said_so_too(
    text: str, words: str, spec: PreferenceSpec
):
    """It was offered as a renter's budget, beside the visit, and both were taken."""
    result = read(text, spec)
    assert result.operations == NO_OPERATIONS
    ((label, note, ways),) = budgets(result)
    assert (note, ways) == (NO_BUDGET_ON_A_VISIT, 0) and label.startswith("A budget of £")
    (amount,) = (found for found in result.suggestions if found.target == "budget")
    assert [text[span.start : span.end] for span in amount.spans] == [words]
    assert result.not_in_release == ()


def test_by_the_month_it_is_still_a_rent_and_a_word_for_a_home_still_says_which():
    rent = read("honestly, up to £1,500 a month")
    ((label, note, ways),) = budgets(rent)
    assert (label, note, ways) == ("A budget of £1,500 a month", "", 1)
    (edit,) = rent.suggestions[0].choices[0].operations.budget_ops
    assert (edit.tenure, edit.amount) == ("rent", 1500)
    # "Renting" names the kind of search, and the amount is then a renter's. It was tried
    # on the visit as it stood, was turned away, and was said to be what the data lacks.
    for text, kind, tenure, amount in (
        ("honestly, renting, up to £2,000", "Renting", "rent", 2000),
        ("honestly, buying, max £400k", "Buying", "buy", 400_000),
    ):
        said = read(text)
        assert {found.label for found in said.suggestions} >= {kind}
        ((_, note, ways),) = budgets(said)
        assert (note, ways) == ("", 1) and said.not_in_release == ()
        (budget,) = (found for found in said.suggestions if found.target == "budget")
        (edit,) = budget.choices[0].operations.budget_ops
        assert (edit.tenure, edit.amount) == (tenure, amount)
        pressed = apply(VISITOR, budget.choices[0].operations, fixture_release())
        assert pressed.rejected == ()
        assert (pressed.spec.tenure, pressed.spec.budget.amount) == (tenure, amount)


@pytest.mark.parametrize(
    ("text", "tenure"),
    [("honestly, up to £2,000", "unchanged"), ("honestly, £400k", "buy")],
)
def test_an_amount_typed_by_a_renter_is_offered_as_it_was(text: str, tenure: str):
    result = read(text, RENTER)
    ((_, note, ways),) = budgets(result)
    assert (note, ways) == ("", 1)
    (edit,) = result.suggestions[0].choices[0].operations.budget_ops
    assert edit.tenure == tenure


# --- A wish for somewhere cheaper, which moves a budget that a visit does not hold -----------

CHEAPER = [
    ("cheaper homes", "A lower budget", "cheaper"),
    ("somewhere cheaper", "A lower budget", "cheaper"),
    ("less expensive", "A lower budget", "less expensive"),
    ("raise my budget", "A higher budget", "raise my budget"),
]


@pytest.mark.parametrize(("text", "label", "words"), CHEAPER)
def test_a_wish_to_move_the_budget_typed_into_a_visit_is_said_to_be_what_a_visit_cannot_hold(
    text: str, label: str, words: str
):
    """It was answered with no edit, no offer and nothing unread: nothing said it was heard."""
    result = read(text)

    assert result.operations == NO_OPERATIONS
    assert budgets(result) == [(label, NO_STEP_ON_A_VISIT, 0)]
    (step,) = result.suggestions
    assert step.choices == (IGNORE,)
    assert [text[span.start : span.end] for span in step.spans] == [words]
    assert result.unread == () and result.not_in_release == ()
    assert apply(VISITOR, result.operations, fixture_release()).spec == VISITOR


@pytest.mark.parametrize(("text", "label", "words"), CHEAPER)
def test_the_same_wish_still_moves_the_budget_of_a_search_for_a_home(
    text: str, label: str, words: str
):
    result = read(text, RENTER)

    (edit,) = result.operations.budget_ops
    assert edit.action == "nudge" and edit.step in ("down_small", "up_small")
    assert result.suggestions == ()


def test_what_is_said_of_it_names_no_amount_and_no_control_of_a_page():
    assert "amount" not in NO_STEP_ON_A_VISIT
    assert NO_STEP_ON_A_VISIT == (
        "Burro does not know what it costs to stay in an area, so a search for somewhere to "
        "stay has no budget to raise or lower. This means Burro has left this out of your "
        "search."
    )
