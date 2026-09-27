"""A visit weighs nothing of what homes sold for, and no reader offers it one.

A visit holds no budget: Burro holds no price of a stay. It could still weigh
what homes sold for. An edit of the middle price paid for a home, or of how much
that rose, was applied to a visit, and the explanation of the area then gave the
price of a home as a reason to stay there. "A hotel somewhere affluent" was
offered "What homes sell for", and a client that takes what is offered took it.

So an edit that would make a visit weigh one is turned away and says why, as an
edit that would give it a budget is. A search that becomes a visit drops what it
weighed of them, as it drops its budget. And the reader offers none on a visit
or beside the words for one: where a word has other readings those are offered,
and where it has none it is said why nothing is.

Every name and every figure here is made up.
"""

import pytest
from burro_core.catalogue import FEATURES, SOLD_FOR
from burro_core.explain import TemplateExplainer, explain
from burro_core.ids import Dimension, Direction, FeatureId, Provenance, RejectReason, Tenure
from burro_core.interpret import (
    IGNORE,
    NO_PRICE_ON_A_VISIT,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
)
from burro_core.ops import NO_OPERATIONS
from burro_core.rank import rank
from burro_core.reducer import apply
from burro_core.spec import FeatureWeight, PreferenceSpec, default_spec

from .support import fixture_release
from .test_reducer import budget, ops, reasons, tag, weight, weights

RENTER = default_spec(Tenure.RENT)
BUYER = default_spec(Tenure.BUY)
VISITOR = default_spec(Tenure.VISIT)
READER = RuleInterpreter()
PRICES = ("price_median", "price_rise_5y", "price_rise_10y")


def read(text: str, spec: PreferenceSpec = RENTER) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=spec, release=fixture_release()))


def offered(result: InterpretResult) -> dict[str, tuple[str, int]]:
    """What is offered, by its target: what is said of it, and how many ways it may be taken."""
    return {found.target: (found.note, len(found.choices) - 1) for found in result.suggestions}


def test_the_measures_of_what_homes_sold_for_are_the_ones_that_are_counted_in_pounds():
    assert {feature.value for feature in SOLD_FOR} == set(PRICES)
    in_pounds = {
        feature_id
        for feature_id, feature in FEATURES.items()
        if feature.dimension is Dimension.HOMES and feature.unit == "£"
    }
    assert in_pounds == SOLD_FOR


# The reducer


@pytest.mark.parametrize("feature_id", PRICES)
@pytest.mark.parametrize(
    "given",
    [
        {"action": "nudge", "step": "up_large"},
        {"action": "nudge", "step": "up_small", "direction": "less"},
        {"action": "set", "value": 0.5, "direction": "more", "provenance": "ui_edit"},
    ],
    ids=["a step", "a step towards cheaper", "a number"],
)
def test_an_edit_that_would_make_a_visit_weigh_what_homes_sold_for_is_turned_away(
    feature_id: str, given: dict[str, object]
):
    action = str(given["action"])
    edit = weight(action, feature_id, **{k: v for k, v in given.items() if k != "action"})
    result = apply(VISITOR, ops(edit), fixture_release())
    assert reasons(result) == [RejectReason.NOT_IN_RELEASE]
    assert result.applied == () and result.spec == VISITOR
    # The same edit is in order for a home to rent and for a home to buy.
    for spec in (RENTER, BUYER):
        home = apply(spec, ops(edit), fixture_release())
        assert home.rejected == () and feature_id in weights(home.spec)


def test_an_edit_that_names_a_visit_and_a_price_makes_the_visit_and_turns_the_price_away():
    edits = ops(budget(tenure="visit"), weight("nudge", "price_median", step="up_large"))
    result = apply(RENTER, edits, fixture_release())
    assert result.spec.visiting and reasons(result) == [RejectReason.NOT_IN_RELEASE]
    assert not set(PRICES) & set(weights(result.spec))


def test_a_search_that_becomes_a_visit_drops_what_it_weighed_of_what_homes_sold_for():
    asked = apply(
        BUYER,
        ops(
            weight("set", "price_median", value=0.6, direction="less", provenance="ui_edit"),
            weight("nudge", "price_rise_5y", step="up_large"),
            weight("nudge", "water_access", step="up_large"),
            tag("nudge", "leafy", step="up_large"),
        ),
        fixture_release(),
    ).spec
    assert {"price_median", "price_rise_5y", "water_access"} <= set(weights(asked))
    visit = apply(asked, ops(budget(tenure="visit")), fixture_release())
    assert visit.rejected == () and visit.spec.visiting
    held = weights(visit.spec)
    assert not set(PRICES) & set(held)
    # Everything else that was asked for is kept.
    assert "water_access" in held and [t.tag_id for t in visit.spec.tags] == ["leafy"]
    # It does not come back where the visit becomes a search for a home again.
    home = apply(visit.spec, ops(budget(tenure="buy")), fixture_release()).spec
    assert not set(PRICES) & set(weights(home))


def test_what_a_visit_weighs_of_a_price_can_always_be_taken_off():
    """A search that was sent whole may hold one. To take it off is in order."""
    price = FeatureWeight(
        feature_id=FeatureId.PRICE_MEDIAN,
        weight=0.5,
        direction=Direction.MORE,
        provenance=Provenance.UI_EDIT,
    )
    held = VISITOR.replace(weights=(*VISITOR.weights, price))
    taken_off = ops(weight("remove", "price_median", provenance="ui_edit"))
    off = apply(held, taken_off, fixture_release())
    assert off.rejected == () and [found.changed for found in off.applied] == [True]
    assert not weights(off.spec).get("price_median")


def test_no_explanation_of_a_visit_that_asked_for_a_price_gives_one_as_a_reason():
    result = apply(
        VISITOR, ops(weight("set", "price_median", value=0.5, direction="more")), fixture_release()
    )
    ranked = rank(result.spec, fixture_release())
    areas = tuple(found.area_id for found in ranked.ranked[:5])
    for explanation in explain(ranked, fixture_release(), result.spec, areas, TemplateExplainer()):
        trade_off = [explanation.trade_off] if explanation.trade_off else []
        for sentence in (*explanation.reasons, *trade_off):
            assert "price paid for a home" not in sentence.text


# The reader

SMART = ("feature:brand_mix", "feature:homes_higher_bands", "tag:street_character")


@pytest.mark.parametrize(
    ("text", "spec"),
    [
        ("a hotel somewhere affluent", RENTER),
        ("visiting, somewhere affluent", RENTER),
        ("honestly, a city break somewhere posh", BUYER),
        ("somewhere affluent", VISITOR),
        ("honestly, somewhere upmarket", VISITOR),
    ],
)
def test_a_word_for_a_smart_area_is_offered_beside_a_visit_without_what_homes_sold_for(
    text: str, spec: PreferenceSpec
):
    result = read(text, spec)
    found = offered(result)
    assert not [target for target in found if target.removeprefix("feature:") in PRICES]
    assert set(SMART) <= set(found)
    # What is said of the word names what is offered, and no price.
    for target in SMART:
        assert "homes sell for" not in found[target][0]
    assert result.not_in_release == ()


@pytest.mark.parametrize("text", ["somewhere affluent", "honestly, somewhere upmarket"])
@pytest.mark.parametrize("spec", [RENTER, BUYER], ids=["renting", "buying"])
def test_it_is_offered_to_whoever_looks_for_a_home_as_it_was(text: str, spec: PreferenceSpec):
    assert "feature:price_median" in offered(read(text, spec))


@pytest.mark.parametrize(
    ("text", "spec"),
    [
        ("rising prices", VISITOR),
        ("honestly, somewhere on the up", VISITOR),
        ("a hotel, rising prices", RENTER),
        ("what homes sell for", VISITOR),
    ],
)
def test_a_word_that_is_read_as_nothing_else_is_said_to_be_what_a_visit_does_not_weigh(
    text: str, spec: PreferenceSpec
):
    result = read(text, spec)
    assert not [edit for edit in result.operations.weight_ops if edit.feature_id in SOLD_FOR]
    prices = {
        target: said
        for target, said in offered(result).items()
        if target.removeprefix("feature:") in PRICES
    }
    assert prices and set(prices.values()) == {(NO_PRICE_ON_A_VISIT, 0)}
    for found in result.suggestions:
        if found.target in prices:
            assert found.choices == (IGNORE,)
    assert result.not_in_release == ()
    assert "prices" not in " ".join(text[s.start : s.end] for s in result.unread)


def test_nothing_is_applied_to_a_visit_of_what_homes_sold_for():
    for text in ("what homes sell for", "price rise over five years"):
        result = read(text, VISITOR)
        assert result.operations == NO_OPERATIONS
        assert apply(VISITOR, result.operations, fixture_release()).spec == VISITOR
    assert FeatureId.PRICE_MEDIAN in SOLD_FOR
