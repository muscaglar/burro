"""A difference of nothing is not given as a difference.

Seen in a browser: "The middle price of flats of all sizes is £0 under your
budget of £366,000." A difference of nothing was read as a fault. Two kinds of
sentence give a difference: what a budget is held against, in each of the three
ways it is held, and a journey that is over its limit. Each is held here where
the difference is nothing, and a pound or a minute either side of it.
"""

from collections.abc import Callable

import pytest
from burro_core.explain import TEMPLATES, render
from burro_core.facts import AT_THE_BUDGET, AT_THE_LIMIT, Fact, facts_for
from burro_core.ids import FactKind, Strictness, TemplateId
from burro_core.release import InMemoryRelease
from burro_core.spec import PreferenceSpec
from burro_core.verify import verify

from . import no_range, recorded
from .support import area_id, build_worked_release, build_worked_spec

ONE, TWO, THREE = (area_id(n) for n in (1, 2, 3))
# The templates that give a difference, by what they give it from.
OF_A_BUDGET = {
    TemplateId.BUDGET_UNDER,
    TemplateId.BUDGET_OVER,
    TemplateId.BUDGET_UNDER_MEDIAN,
    TemplateId.BUDGET_OVER_MEDIAN,
    TemplateId.BUDGET_UNDER_RECORDED,
    TemplateId.BUDGET_OVER_RECORDED,
}
OF_A_JOURNEY = {TemplateId.TRAVEL_PT_OVER, TemplateId.TRAVEL_OTHER_OVER}
AT = {TemplateId.BUDGET_AT, TemplateId.BUDGET_AT_MEDIAN, TemplateId.BUDGET_AT_RECORDED}
# A release, a search whose budget is some amount, and the area the budget is held against.
Found = tuple[InMemoryRelease, PreferenceSpec, str]
Held = Callable[[int], Found]


def with_a_range(amount: int) -> Found:
    """The worked example, whose second area has rents from £1,650 to £1,950."""
    spec = build_worked_spec()
    spec = spec.replace(budget=spec.budget.replace(amount=amount), commutes=())
    return build_worked_release(), spec, TWO


def with_one_number(amount: int) -> Found:
    """A release of prices that are one number. The first of its flats sold for £385,000."""
    return no_range.priced(), no_range.buyer(Strictness.SOFT, amount), ONE


def with_a_wider_place(amount: int) -> Found:
    """A release of rents of wider places. The middle rent of the first area's is £1,600."""
    return recorded.recorded(), recorded.renter(Strictness.SOFT, amount), ONE


def budget_fact(found: Found) -> Fact:
    release, spec, area = found
    (fact,) = (f for f in facts_for(release, area, spec) if f.kind is FactKind.BUDGET_FIT)
    return fact


WAYS = [
    pytest.param(
        *(with_a_range, 1_950, TemplateId.BUDGET_AT, "upper"),
        "The upper end is at your budget of £1,950.",
        "The upper end is £1 under your budget of £1,951.",
        "The upper end is £1 over your budget of £1,949.",
        id="a range",
    ),
    pytest.param(
        *(with_one_number, 385_000, TemplateId.BUDGET_AT_MEDIAN, "median"),
        "The middle price of flats of all sizes is at your budget of £385,000.",
        "The middle price of flats of all sizes is £1 under your budget of £385,001.",
        "The middle price of flats of all sizes is £1 over your budget of £384,999. "
        "About half of the flats sold here went for under £385,000.",
        id="one number",
    ),
    pytest.param(
        *(with_a_wider_place, 1_600, TemplateId.BUDGET_AT_RECORDED, "median"),
        "The middle rent for a 1-bedroom home in postcode district QH1 is at your budget of "
        "£1,600 a month.",
        "The middle rent for a 1-bedroom home in postcode district QH1 is £1 under your budget "
        "of £1,601 a month.",
        "The middle rent for a 1-bedroom home in postcode district QH1 is £1 over your budget "
        "of £1,599 a month. About half of the rents recorded there were under £1,600.",
        id="a rent of a wider place",
    ),
]


@pytest.mark.parametrize(("held", "amount", "template", "slot", "at", "under", "over"), WAYS)
def test_a_cost_that_is_the_budget_to_the_pound_is_said_to_be_at_it(
    held: Held, amount: int, template: TemplateId, slot: str, at: str, under: str, over: str
):
    fact = budget_fact(held(amount))
    assert fact.template is template
    assert render(fact).text == at
    # The difference is no figure of the fact: nothing a page lays out can give it.
    assert "margin" not in fact.slots
    assert fact.slots["verdict"] == AT_THE_BUDGET == "At your budget"
    assert fact.slots["amount"] == fact.slots[slot] == f"{amount:,}"
    # The budget and what it is held against are one amount, and it is held once.
    assert fact.numbers[0] == f"£{amount}" and fact.numbers.count(f"£{amount}") == 1
    assert "£0" not in fact.numbers and "0" not in fact.numbers
    assert verify(render(fact), {fact.fact_id: fact}).ok
    # A pound either side of it is a pound, said as it was.
    above, below = budget_fact(held(amount + 1)), budget_fact(held(amount - 1))
    assert (render(above).text, render(below).text) == (under, over)
    assert (above.slots["margin"], below.slots["margin"]) == ("1", "1")
    assert "verdict" not in above.slots and "verdict" not in below.slots
    assert {above.template, below.template} <= OF_A_BUDGET


def test_every_way_a_budget_is_held_has_a_sentence_for_a_difference_of_nothing():
    # Each pair that says under and over has a third that says at, of the same words.
    for under in sorted(t for t in OF_A_BUDGET if "_under" in t.value):
        at = TemplateId(under.value.replace("_under", "_at"))
        over = TemplateId(under.value.replace("_under", "_over"))
        assert at in AT and over in OF_A_BUDGET
        assert TEMPLATES[at] == TEMPLATES[under].replace("£{margin} under", "at")
        assert TEMPLATES[over].startswith(TEMPLATES[under].replace(" under ", " over ")[:-1])
        assert "{margin}" not in TEMPLATES[at]
    # And these are all the sentences that give a difference.
    gives = {template for template, text in TEMPLATES.items() if "{margin}" in text}
    assert gives == OF_A_BUDGET | OF_A_JOURNEY


def journey(minutes: int) -> Fact:
    """The journey of the third area of the worked example to its first place: 44 minutes."""
    spec = build_worked_spec()
    spec = spec.replace(commutes=(spec.commutes[0].replace(max_minutes=minutes),))
    found = facts_for(build_worked_release(), THREE, spec)
    (fact,) = (f for f in found if f.kind is FactKind.TRAVEL)
    return fact


def test_a_journey_that_takes_the_minutes_of_its_limit_is_at_it_and_under_it_by_nothing():
    at = journey(44)
    assert at.template is TemplateId.TRAVEL_PT
    assert render(at).text == (
        "By public transport to Pellam Cross: about 44 minutes on a typical weekday morning, "
        "49 if you just miss a service."
    )
    assert "margin" not in at.slots and "margin_unit" not in at.slots
    assert (at.slots["limit"], at.slots["verdict"]) == ("44", AT_THE_LIMIT)
    assert AT_THE_LIMIT == "At your limit"
    assert at.numbers == ("44", "49") and "0" not in at.numbers
    assert verify(render(at), {at.fact_id: at}).ok
    # A minute either side of it is a minute, said as it was.
    over, under = journey(43), journey(45)
    assert over.template is TemplateId.TRAVEL_PT_OVER
    assert render(over).text.endswith(", 1 minute over the 43 you set.")
    assert (over.slots["margin"], under.slots["margin"]) == ("1", "1")
    assert under.template is TemplateId.TRAVEL_PT
    assert "verdict" not in over.slots and "verdict" not in under.slots


def test_no_fact_of_any_budget_or_limit_gives_a_difference_of_nothing():
    found: list[Fact] = []
    for held, amounts in (
        (with_a_range, range(1_600, 2_100, 50)),
        (with_one_number, (385_000, 400_000, 437_500, 400_001)),
        (with_a_wider_place, (1_600, 1_900, 2_200, 1_700)),
    ):
        for amount in amounts:
            release, spec, _ = held(amount)
            for area in release.neighbourhoods:
                found += facts_for(release, area.area_id, spec)
    for minutes in range(20, 60):
        found.append(journey(minutes))
    at = [fact for fact in found if "verdict" in fact.slots and "margin" not in fact.slots]
    assert {fact.template for fact in at} == AT | {TemplateId.TRAVEL_PT}
    for fact in found:
        if fact.kind not in (FactKind.BUDGET_FIT, FactKind.TRAVEL):
            continue
        text = render(fact).text
        assert fact.slots.get("margin") != "0", fact.fact_id
        assert "£0 " not in text and " 0 minutes" not in text, text
        assert ("margin" in fact.slots) != (fact in at) or fact.template in (
            TemplateId.TRAVEL_BEYOND,
            TemplateId.TRAVEL_ESTIMATED,
        ), fact.fact_id
