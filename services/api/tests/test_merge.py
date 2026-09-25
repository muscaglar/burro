"""One offer for each thing: what a model read, put with what the rules noticed.

A person never sees less than the rules alone give. That is held here on
every answer a model gave that is on disk, and on answers written to disagree
with the rules.
"""

import json
from typing import Any

import pytest
from burro_api.offers import FIRM, GUIDE, LESS, MORE, OFF, Offer
from burro_core import RuleInterpreter
from burro_core.ids import InterpreterName
from burro_core.interpret import InterpretRequest, InterpretResult
from burro_core.ops import BudgetEdit, CommuteEdit, Operations

from .support import (
    GROUPS,
    FakeModelClient,
    answers_on_disk,
    asked,
    guessed,
    model_budget,
    model_commute,
    model_output,
    model_tag,
    model_weight,
    offers,
    on_disk,
    quoted,
    read_again,
    reader_asking,
    release,
    through_the_route,
)


def _holds(offered: Operations, ruled: Operations) -> bool:
    """Whether some edits hold all that the rules' own would set: the thing, and which way."""
    for theirs in ruled.weight_ops:
        if not any(
            (ours.feature_id, ours.action, ours.direction)
            == (theirs.feature_id, theirs.action, theirs.direction)
            for ours in offered.weight_ops
        ):
            return False
    for theirs in ruled.tag_ops:
        if not any(
            (ours.tag_id, ours.action, ours.toward) == (theirs.tag_id, theirs.action, theirs.toward)
            for ours in offered.tag_ops
        ):
            return False
    for theirs in ruled.area_ops:
        if theirs not in offered.area_ops:
            return False
    for journey in ruled.commute_ops:
        if not any(_same_journey(ours, journey) for ours in offered.commute_ops):
            return False
    return all(
        any(_same_budget(ours, budget) for ours in offered.budget_ops)
        for budget in ruled.budget_ops
    )


def _same_journey(ours: CommuteEdit, theirs: CommuteEdit) -> bool:
    # A journey the rules took no number for is held by one that has the number typed.
    return (ours.place_id, ours.action) == (theirs.place_id, theirs.action) and (
        theirs.max_minutes in (0, ours.max_minutes)
    )


def _same_budget(ours: BudgetEdit, theirs: BudgetEdit) -> bool:
    return (
        (not theirs.amount or ours.amount == theirs.amount)
        and (theirs.tenure.value == "unchanged" or ours.tenure is theirs.tenure)
        and (theirs.segment.value == "unchanged" or ours.segment is theirs.segment)
    )


def lost(ruled: InterpretResult, result: InterpretResult) -> list[str]:
    """Every way the rules alone offer that is not offered once a model has read."""
    ways = [way.operations for offer in offers(result).values() for way in offer.choices]
    return [
        f"{suggestion.target}: {choice.label}"
        for suggestion in ruled.suggestions
        for choice in suggestion.choices
        if choice.operations.count and not any(_holds(way, choice.operations) for way in ways)
    ]


def test_a_person_never_sees_less_than_the_rules_alone_give():
    # The guard that went applied only what the model said, and lost 14 right
    # readings of the rules on these sentences. None may be lost.
    rules = RuleInterpreter()
    missing: dict[str, list[str]] = {}
    for (case, look), row in answers_on_disk().items():
        if "output" not in row:
            continue
        text, spec, client = on_disk(case, look)
        request = InterpretRequest(text=text, spec=spec, release=release())
        ruled, result = rules.interpret(request), reader_asking(client).interpret(request)
        assert result.operations == ruled.operations, case
        gone = lost(ruled, result)
        if gone:
            missing[f"{case} look {look}"] = gone
    assert missing == {}


@pytest.mark.parametrize(
    "answer",
    [
        model_output(),
        model_output(weight_ops=[model_weight("venue_evening_per_homes", action="remove")]),
        model_output(weight_ops=[model_weight("noise_exposure", direction="more")]),
        model_output(tag_ops=[model_tag("pace", toward="low")], policy_flags=["avoid_group"]),
        model_output(status="off_topic"),
    ],
    ids=["nothing", "takes off", "backwards", "about people", "off topic"],
)
def test_whatever_a_model_answers_every_way_the_rules_give_is_still_offered(answer: Any):
    text = "Pubs are so noisy, and my partner works at Pellam Infirmary, not Wexmoor"

    ruled, _ = asked(model_output(), text=text)
    result, _ = asked(answer, text=text)

    assert lost(ruled, result) == []
    assert [offer.target for offer in result.suggestions] == [
        offer.target for offer in ruled.suggestions
    ]


# The rules noticed the thing.


def test_the_way_a_model_read_is_the_guess_of_the_offer_the_rules_made():
    result, text = read_again("own-008")

    # "a bit buzzy, close to a station": the rules offer both, with every
    # way. The model says which way, and code says how much.
    assert guessed(result) == {"tag:pace": MORE, "feature:station_walk": MORE}
    pace = offers(result)["tag:pace"]
    assert pace.read_by is InterpreterName.RULE
    assert [way.id for way in pace.choices] == [MORE, LESS, "ignore"]
    assert quoted(result, text)["tag:pace"] == ["a bit buzzy", "buzzy"]


def test_a_journey_the_rules_noticed_takes_its_minutes_from_the_words_the_model_quoted():
    result, _ = read_again("own-021")

    journey = offers(result)["commute"]
    edits = [edit for way in journey.choices for edit in way.operations.commute_ops]
    assert {(edit.max_minutes, edit.place_id != "") for edit in edits} == {(40, True)}
    assert [way.id for way in journey.choices] == [FIRM, GUIDE, "ignore"]


def test_the_minutes_the_rules_read_are_kept_where_a_model_quoted_the_name_alone():
    text = "Is there anywhere leafy within 30 minutes of Cindermoor Works?"
    named = model_commute(destination_text="Cindermoor Works", words="Cindermoor Works")

    ruled, _ = asked(model_output(), text=text)
    result, _ = asked(model_output(commute_ops=[named]), text=text)

    assert lost(ruled, result) == []
    journey = offers(result)["commute"]
    edits = [edit for way in journey.choices for edit in way.operations.commute_ops]
    assert {edit.max_minutes for edit in edits} == {30}
    # Nothing is said to have been left unsaid that the person said.
    assert [unsaid.code.value for unsaid in journey.unsaid] == ["mode"]


def test_a_number_of_minutes_the_rules_read_is_still_a_choice_where_a_model_read_another():
    text = "Honestly, 30 minutes to Cindermoor Works, or 45 if it is lovely"
    other = model_commute(
        destination_text="Cindermoor Works",
        max_minutes=45,
        words="30 minutes to Cindermoor Works, or 45 if it is lovely",
    )

    ruled, _ = asked(model_output(), text=text)
    result, _ = asked(model_output(commute_ops=[other]), text=text)

    assert lost(ruled, result) == []
    journey = offers(result)["commute"]
    minutes = [edit.max_minutes for w in journey.choices for edit in w.operations.commute_ops]
    assert set(minutes) == {30, 45}


# The rules and the model name different things for the same words.


def test_two_things_for_the_same_words_are_one_offer_and_the_guess_is_the_rules_thing():
    # "access to parks": the rules name the walk to a park, the model the vibe.
    result, text = read_again("own-021")

    [parks] = [offer for name, offer in offers(result).items() if "park" in name]
    assert parks.target == "feature:park_proximity"
    assert [way.id for way in parks.choices] == [MORE, OFF, "tag:parks_close_by/more", "ignore"]
    assert [way.id for way in parks.choices if way.guess] == [MORE]
    # What the model named is a choice beside it, and is never the guess.
    [theirs] = [way for way in parks.choices if way.id.startswith("tag:")]
    assert theirs.meant and not theirs.guess and not theirs.ruled
    assert "access to parks" in quoted(result, text)["feature:park_proximity"]


def test_the_end_of_a_scale_that_cores_words_name_is_the_guess_where_a_model_names_another():
    # "some nightlife nearby would be nice": Pace for the rules, pubs for the model.
    result, _ = read_again("own-024")

    assert guessed(result)["tag:pace"] == MORE


def test_against_the_one_thing_is_towards_the_other_end_of_the_scale():
    text = "Honestly, nightlife is the last thing on my mind"
    fewer = model_weight("venue_evening_per_homes", action="remove", words=text)

    result, _ = asked(model_output(weight_ops=[fewer]), text=text)

    # "nightlife" names the Buzzy end of Pace, and the model read the words
    # as against it. An end that is turned away is a wish for the other end.
    assert guessed(result) == {"tag:pace": LESS}


def test_two_things_a_model_names_for_the_same_words_are_one_offer_with_no_guess():
    # "old houses", read as listed buildings and as Age of buildings towards Historic, as
    # the answer on disk to `long-013` reads them. The rules make nothing of the words.
    old_houses = {"action": "set", "value": 1.0, "step": "none", "words": "old houses"}
    answer = model_output(
        weight_ops=[model_weight("listed_buildings", **old_houses)],
        tag_ops=[model_tag("built_age", toward="high", **old_houses)],
    )

    result, _ = asked(answer, text="What we want is old houses, mind")

    [old] = [offer for name, offer in offers(result).items() if "listed_buildings" in name]
    assert old.read_by is InterpreterName.MODEL
    assert [way.id for way in old.choices] == [
        MORE,
        "tag:built_age/more",
        "tag:built_age/less",
        "ignore",
    ]
    assert not any(way.guess for way in old.choices)


# The rules read one way in that sentence, and the model the other.


def test_where_the_rules_read_the_sentence_the_other_way_the_whole_of_it_is_shown():
    text = "not near a station. My sister swears by a proper brunch spot, mind."
    backwards = model_weight("station_walk", words="a station")

    found = through_the_route(model_output(weight_ops=[backwards]), text)

    # The rules read "not near a station", and apply nothing, since the prompt is not plain.
    assert found["applied"] == []
    [station] = found["suggestions"]
    assert not any(way["guess"] for way in station["choices"])
    assert station["add_all"] == ""
    shown = text[station["shown"]["start"] : station["shown"]["end"]]
    assert shown == "not near a station"


def test_where_the_rules_and_the_model_agree_the_way_is_the_guess():
    text = "not near a station. My sister swears by a proper brunch spot, mind."
    off = model_weight("station_walk", action="remove", words="not near a station")

    result, _ = asked(model_output(weight_ops=[off]), text=text)

    assert guessed(result) == {"feature:station_walk": OFF}


def test_cores_own_word_for_an_end_outweighs_the_end_a_model_names():
    text = "Honestly, somewhere buzzy"
    calm = model_tag("pace", toward="low", words="somewhere buzzy")

    result, _ = asked(model_output(tag_ops=[calm]), text=text)

    assert list(offers(result)) == ["tag:pace"] and guessed(result) == {}


# A budget.


def test_what_the_rules_noticed_of_the_same_budget_is_part_of_the_one_offer():
    result, text = read_again("own-021")

    budgets = [offer for name, offer in offers(result).items() if name.startswith("budget")]
    tenures = [offer for name, offer in offers(result).items() if name.startswith("tenure")]
    # Renting, a one-bedroom home and £1,900 a month: one thing, offered once.
    assert len(budgets) == 1 and tenures == []
    [budget] = budgets
    edits = [edit for way in budget.choices for edit in way.operations.budget_ops]
    assert {(edit.tenure, edit.amount, edit.segment) for edit in edits} == {("rent", 1900, "bed_1")}
    assert "renting" in [text[span.start : span.end] for span in budget.spans]


def test_an_amount_the_person_took_back_is_still_offered_and_is_no_guess():
    # "My budget is £2,000 a month. Sorry, that's wrong, it's £1,600 a month for a two bed."
    result, _ = read_again("own-019", 3)

    amounts: dict[int, Offer] = {
        edit.amount: offer
        for offer in offers(result).values()
        for way in offer.choices
        for edit in way.operations.budget_ops
        if edit.amount
    }
    assert sorted(amounts) == [1600, 2000]
    assert any(way.guess for way in amounts[1600].choices)
    assert not any(way.guess for way in amounts[2000].choices)
    assert amounts[2000].read_by is InterpreterName.RULE


def test_a_tenure_the_words_do_not_bear_out_is_not_the_models_to_set():
    text = "Honestly, about \N{POUND SIGN}1,500 a month would do"
    buying = model_budget(tenure="buy", amount=1500, words=text)

    result, _ = asked(model_output(budget_ops=[buying]), text=text)

    [budget] = offers(result).values()
    edits = [edit for way in budget.choices for edit in way.operations.budget_ops]
    assert {(edit.tenure, edit.amount) for edit in edits} == {("unchanged", 1500)}


def test_an_amount_that_can_only_be_a_price_is_a_budget_to_buy():
    text = "Honestly, about \N{POUND SIGN}400,000 would do"
    budget = model_budget(amount=400000, words=text)

    result, _ = asked(model_output(budget_ops=[budget]), text=text)

    [offer] = offers(result).values()
    edits = [edit for way in offer.choices for edit in way.operations.budget_ops]
    assert {(edit.tenure, edit.amount) for edit in edits} == {("buy", 400000)}


# The order, and what is left unread.


def test_offers_stand_in_the_order_of_their_words():
    for (case, look), row in answers_on_disk().items():
        if "output" not in row:
            continue
        result, _ = read_again(case, look)
        starts = [offer.spans[0].start for offer in result.suggestions]
        assert starts == sorted(starts), case


# Two places the release does not hold, in one sentence.
TWO_PLACES = "I work at Mirrowick Basin and my partner at Zorvane Halt, 45 minutes to each"


def _the_other_way_round(answer: dict[str, Any]) -> dict[str, Any]:
    """An answer with the edits of each kind written in the other order."""
    return answer | {group: list(reversed(answer[group])) for group in GROUPS}


def test_what_is_offered_does_not_rest_on_the_order_a_model_wrote_its_edits_in():
    # A model does not write its edits in the same order twice. What reaches the
    # person is the same whichever it wrote first: two budgets, and a thing pulled two ways.
    moved: list[str] = []
    for (case, look), row in answers_on_disk().items():
        if "output" not in row:
            continue
        text, spec, _ = on_disk(case, look)
        request = InterpretRequest(text=text, spec=spec, release=release())
        answer = json.loads(row["output"])
        one, other = (
            reader_asking(FakeModelClient(json.dumps(written))).interpret(request)
            for written in (answer, _the_other_way_round(answer))
        )
        if one.suggestions != other.suggestions:
            moved.append(f"{case} look {look}")
    assert moved == []


@pytest.mark.parametrize(
    ("text", "answer"),
    [
        # Two things for the same words, which the rules make nothing of.
        (
            "Honestly, a proper brunch spot would do",
            model_output(
                weight_ops=[
                    model_weight("venue_independent", words="a proper brunch spot"),
                    model_weight("venue_food_drink", words="a proper brunch spot"),
                ]
            ),
        ),
        # Two amounts, of which the person may mean either.
        (
            "Honestly, \N{POUND SIGN}1,500 a month would do, or \N{POUND SIGN}1,700 for a gem",
            model_output(
                budget_ops=[
                    model_budget(amount=1700, words="\N{POUND SIGN}1,700 for a gem"),
                    model_budget(amount=1500, words="\N{POUND SIGN}1,500 a month would do"),
                ]
            ),
        ),
        # One journey, read with two numbers.
        (
            "Honestly, 20 minutes to Foxholt Market would be grand, 35 to Foxholt Market would do",
            model_output(
                commute_ops=[
                    model_commute(
                        destination_text="Foxholt Market",
                        max_minutes=35,
                        words="35 to Foxholt Market would do",
                    ),
                    model_commute(
                        destination_text="Foxholt Market",
                        max_minutes=20,
                        words="20 minutes to Foxholt Market would be grand",
                    ),
                ]
            ),
        ),
        # One thing, pulled two ways, and said to count for more in one place than the other.
        (
            "Honestly, a boozer is essential, and slightly fewer boozers would suit my partner",
            model_output(
                weight_ops=[
                    model_weight(
                        "venue_evening",
                        direction="less",
                        words="slightly fewer boozers would suit my partner",
                    ),
                    model_weight("venue_evening", words="a boozer is essential"),
                ]
            ),
        ),
        # Two vibes, on words that begin at the same word and end apart.
        (
            "Honestly, bunting and cobbles and that",
            model_output(
                tag_ops=[
                    model_tag("village_feel", words="bunting and cobbles and that"),
                    model_tag("leafy", words="bunting"),
                ]
            ),
        ),
        # Two places the release does not hold, each rested on the whole of what was typed.
        (
            TWO_PLACES,
            model_output(
                commute_ops=[
                    model_commute(destination_text="Zorvane Halt", max_minutes=45),
                    model_commute(destination_text="Mirrowick Basin", max_minutes=45),
                ]
            ),
        ),
    ],
    ids=["two things", "two budgets", "two numbers", "two ways", "two vibes", "two places"],
)
def test_the_same_readings_make_the_same_offers_whichever_a_model_wrote_first(
    text: str, answer: dict[str, Any]
):
    one, _ = asked(answer, text=text)
    other, _ = asked(_the_other_way_round(answer), text=text)

    assert one.suggestions and one.suggestions == other.suggestions


def test_two_offers_that_rest_on_the_same_words_stand_in_the_order_of_what_they_name():
    text = TWO_PLACES
    answer = model_output(
        commute_ops=[
            model_commute(destination_text="Zorvane Halt", max_minutes=45),
            model_commute(destination_text="Mirrowick Basin", max_minutes=45),
        ]
    )

    result, _ = asked(answer, text=text)

    named = [offer.named_at for offer in offers(result).values()]
    assert [text[at.start : at.end] for at in named if at is not None] == [
        "Mirrowick Basin",
        "Zorvane Halt",
    ]


def test_what_an_offer_rests_on_is_not_said_to_be_unread():
    for (case, look), row in answers_on_disk().items():
        if "output" not in row:
            continue
        result, _ = read_again(case, look)
        rested = [(s.start, s.end) for offer in result.suggestions for s in offer.spans]
        for unread in result.unread:
            assert not [
                span for span in rested if span[0] < unread.end and unread.start < span[1]
            ], case
        # `other` says that nothing was made of some word, whether or not it may have asked.
        assert ("other" in result.unmet) is bool(result.unread or result.asks_nothing), case


def test_a_journey_to_a_place_named_twice_is_offered_once():
    text = "Honestly, 20 minutes to Foxholt Market. Foxholt Market is where I work"
    journey = model_commute(
        destination_text="Foxholt Market", max_minutes=20, words="20 minutes to Foxholt Market"
    )

    result, _ = asked(model_output(commute_ops=[journey, journey]), text=text)

    assert list(offers(result)) == ["commute"]
