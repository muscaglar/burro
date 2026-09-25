"""Answers written to get a wrong reading past the guard (contract, section 8.2).

The answers on disk are what one model gave. These are what a model could
give that is careless, or means harm: words quoted from one part of a
sentence for an edit about another, a quote so wide that it holds what was
said of another thing, and a quote so narrow that it leaves out what turns
the wish round. No call is made: a stand-in hands the answer to the reader.

A model chooses the words it quotes. So nothing that makes an offer stronger
is read from the quote alone: it is read where the number or the thing
stands, as core finds it.
"""

import json
from typing import Any

import pytest
from burro_api.answer import parsed
from burro_api.guard import Check, Guarded, guarded
from burro_api.offers import FIRM, GUIDE, in_add_all
from burro_api.reader import ModelInterpreter
from burro_api.typed import Typed
from burro_core.grammar import Grammar
from burro_core.ids import InterpreterName, Notice, UnmetCategory, WeightAction
from burro_core.interpret import InterpretRequest, RuleInterpreter
from burro_core.ops import NO_OPERATIONS
from burro_core.places import Names

from .support import (
    MODEL,
    FakeModelClient,
    asked,
    model_budget,
    model_commute,
    model_output,
    model_tag,
    model_weight,
    offers,
    read_again,
    release,
    renter,
    served_again,
    through_the_route,
)


def fired(answer: Any, text: str) -> set[Check]:
    """The checks that fire on one answer to one sentence."""
    reader = ModelInterpreter(FakeModelClient(answer), MODEL, 512, 2.5)
    reader.interpret(InterpretRequest(text=text, spec=renter(), release=release()))
    return set(reader.fired)


def _guesses(result: Any, target: str) -> list[str]:
    """The ways that are marked as the guess, of every offer of one kind.

    Of a budget it is the guess at the amount. What the rules read plainly of the home
    beside it, "2 bedrooms", carries a guess of its own, which says nothing of how firm.
    """
    return [
        way.id
        for name, offer in offers(result).items()
        if name.rstrip("+") == target
        for way in offer.choices
        if way.guess
        and (target != "budget" or any(edit.amount for edit in way.operations.budget_ops))
    ]


# --- A firm limit nobody gave -------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "amount"),
    [
        # "At most" is said of the bedrooms, and "no more than" of the journey.
        ("Honestly, at most 2 bedrooms, around \N{POUND SIGN}1,500 a month", 1500),
        ("No more than 2 bedrooms. Honestly, roughly \N{POUND SIGN}1,500 a month", 1500),
        (
            "No more than 40 minutes to Pellam Exchange, honestly, and about "
            "\N{POUND SIGN}1,900 a month",
            1900,
        ),
        ("Honestly, at most 40 minutes to Pellam Exchange and about 1900 a month", 1900),
    ],
)
def test_a_budget_is_not_made_firm_by_words_that_are_said_of_another_number(text: str, amount: int):
    # The model quotes the whole of what was typed, and calls the budget firm.
    budget = model_budget(amount=amount, strictness="hard", words=text)

    result, _ = asked(model_output(budget_ops=[budget]), text=text)

    assert _guesses(result, "budget") == [GUIDE]


@pytest.mark.parametrize(
    ("text", "budget", "journey"),
    [
        # The words stand between two numbers, and are said of the one they stand against.
        ("honestly under 1500 a month and no more than 40 minutes to Pellam Exchange", GUIDE, FIRM),
        ("honestly 1500 a month at most and about 40 minutes to Pellam Exchange", FIRM, GUIDE),
        ("honestly 40 minutes to Pellam Exchange and no more than 1500 a month", FIRM, GUIDE),
    ],
)
def test_words_between_two_numbers_make_firm_the_one_they_stand_against(
    text: str, budget: str, journey: str
):
    answer = model_output(
        budget_ops=[model_budget(amount=1500, strictness="hard", words=text)],
        commute_ops=[
            model_commute(
                destination_text="Pellam Exchange", max_minutes=40, strictness="hard", words=text
            )
        ],
    )

    result, _ = asked(answer, text=text)

    assert _guesses(result, "budget") == [budget]
    assert _guesses(result, "commute") == [journey]


def test_a_journey_is_not_made_firm_by_words_that_are_said_of_another_journey():
    text = "Honestly, at most 20 minutes to Pellam Exchange and about 50 to Foxholt Market"
    journey = model_commute(
        destination_text="Foxholt Market", max_minutes=50, strictness="hard", words=text
    )

    result, _ = asked(model_output(commute_ops=[journey]), text=text)

    [market] = [
        offer
        for offer in offers(result).values()
        if any(
            edit.max_minutes == 50 for way in offer.choices for edit in way.operations.commute_ops
        )
    ]
    assert [way.id for way in market.choices if way.guess] == [GUIDE]


@pytest.mark.parametrize(
    "text",
    [
        "Honestly, no more than \N{POUND SIGN}1,700 a month",
        "Honestly, \N{POUND SIGN}1,700 a month at most",
        "Honestly, 2 bedrooms, and I can't go over \N{POUND SIGN}1,700",
        "Honestly, 2 bedrooms for \N{POUND SIGN}1,700 at the most",
    ],
)
def test_a_budget_is_firm_where_the_words_are_said_of_its_own_amount(text: str):
    # However much of the text the model quotes, and whatever it calls the limit.
    for words in (text, "\N{POUND SIGN}1,700"):
        budget = model_budget(amount=1700, strictness="soft", words=words)

        result, _ = asked(model_output(budget_ops=[budget]), text=text)

        assert _guesses(result, "budget") == [FIRM], words


# --- Who lives somewhere --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "words"),
    [
        # The words about people stand after the quote, in the same clause.
        ("honestly somewhere lively for professionals", "somewhere lively"),
        ("honestly a buzzy spot where students live", "a buzzy spot"),
        # They stand in another clause, and the quote is no wish of its own.
        ("honestly young couples, like me", "like me"),
        ("honestly lots of students, that sort of place", "that sort of place"),
        ("honestly a good mix - not too many students - and so on", "and so on"),
        # A wish for fewer of those Burro counts is a wish about people as any other is.
        ("honestly somewhere lively with fewer young professionals", "somewhere lively"),
        ("honestly not too many families, that sort of place", "that sort of place"),
    ],
)
def test_no_offer_of_a_models_rests_on_a_wish_about_who_lives_somewhere(text: str, words: str):
    answer = model_output(tag_ops=[model_tag("pace", toward="high", words=words)])

    result, _ = asked(answer, text=text)

    assert result.notice is Notice.NEUTRAL_PLACES
    assert Check.PEOPLE in fired(answer, text)
    for offer in offers(result).values():
        assert offer.read_by is InterpreterName.RULE
        assert not any(way.guess or way.meant for way in offer.choices)


@pytest.mark.parametrize(
    ("text", "words", "thing"),
    [
        # A wish of its own, in a clause of its own, is the rest of the request.
        (
            "honestly lots of students about, and a park nearby",
            "a park nearby",
            "feature:park_proximity",
        ),
        (
            "Not too many students, honestly. And a park nearby would be grand",
            "a park nearby",
            "feature:park_proximity",
        ),
    ],
)
def test_the_rest_of_a_request_about_people_is_still_offered(text: str, words: str, thing: str):
    answer = model_output(weight_ops=[model_weight("park_proximity", words=words)])

    result, _ = asked(answer, text=text)

    assert result.notice is Notice.NEUTRAL_PLACES
    assert _guesses(result, thing) == ["more"]


WHO_IS_COUNTED = ("tag:young_professionals", "tag:family_area", "feature:residents_aged_20_34")


@pytest.mark.parametrize(
    ("text", "answer"),
    [
        # A model names the measure or the vibe itself, from whatever words.
        (
            "honestly somewhere with plenty of twentysomethings",
            model_output(
                weight_ops=[model_weight("residents_aged_20_34", words="twentysomethings")],
                tag_ops=[model_tag("young_professionals", words="plenty of twentysomethings")],
            ),
        ),
        (
            "honestly somewhere the kids have friends on the street",
            model_output(
                weight_ops=[
                    model_weight("households_dependent_children", words="kids have friends")
                ],
                tag_ops=[model_tag("family_area", words="friends on the street")],
            ),
        ),
        # It asks for fewer, in the one field of an answer that could say so.
        (
            "honestly somewhere grown up",
            model_output(
                weight_ops=[
                    model_weight("residents_aged_20_34", direction="less", words="grown up"),
                    model_weight("residents_aged_65_over", step="down_large", words="grown up"),
                ]
            ),
        ),
    ],
)
def test_what_counts_who_lives_somewhere_is_never_a_models_to_offer(text: str, answer: Any):
    result, _ = asked(answer, text=text)

    assert Check.PEOPLE in fired(answer, text)
    assert not [offer for offer in offers(result) if offer.rstrip("+") in WHO_IS_COUNTED]
    assert result.suggestions == () and result.operations == NO_OPERATIONS


def test_the_words_the_rules_offer_who_is_counted_for_are_the_rules_to_read():
    # The rules offer the vibe for "young professionals", towards more and no other way.
    # What a model reads into the same words is dropped, and what it reads of the place
    # beside them is offered as any other reading of a model's is.
    text = "honestly somewhere lively for young professionals"
    answer = model_output(
        tag_ops=[
            model_tag("pace", toward="high", words="somewhere lively"),
            model_tag("foodie", words="young professionals"),
        ],
        weight_ops=[model_weight("venue_evening", words="for young professionals")],
    )

    result, _ = asked(answer, text=text)

    assert result.notice is Notice.NONE and Check.NEAREST in fired(answer, text)
    found = offers(result)
    assert set(found) == {"tag:young_professionals", "tag:pace"}
    counted = found["tag:young_professionals"]
    assert counted.read_by is InterpreterName.RULE
    assert [way.id for way in counted.choices] == ["more", "ignore"]
    assert not any(way.guess for way in counted.choices) and in_add_all(counted) is None
    assert _guesses(result, "tag:pace") == ["more"]


def test_a_long_sentence_that_names_a_campus_keeps_what_a_model_read_of_its_other_wishes():
    # "25 to 35 minutes from Wexmoor University", in one sentence with the
    # schools, the park and the budget. The journey is not offered, and the
    # rest is.
    result, _ = read_again("own-030")

    assert result.notice is Notice.NEUTRAL_PLACES
    assert not [
        way for o in offers(result).values() for way in o.choices if way.operations.commute_ops
    ]
    assert _guesses(result, "budget") == [GUIDE]
    assert _guesses(result, "tag:parks_close_by") == ["more"]


# --- A thing the rules noticed, read from other words --------------------------------------


@pytest.mark.parametrize(
    ("text", "feature", "words"),
    [
        # The thing stands under a word that turns, and the model rests it on other words.
        ("honestly I hate parks. But a station is essential", "park_proximity", "is essential"),
        ("honestly no parks, but a station would be nice", "park_proximity", "would be nice"),
        ("honestly nowhere near a station, and I mean it", "station_walk", "I mean it"),
        ("I can't stand parks, honestly. A must for me is a station", "park_proximity", "A must"),
    ],
)
def test_a_thing_under_a_turn_is_no_guess_whatever_words_the_model_rests_it_on(
    text: str, feature: str, words: str
):
    answer = model_output(weight_ops=[model_weight(feature, words=words)])

    result, _ = asked(answer, text=text)

    assert _guesses(result, f"feature:{feature}") == []
    # The rules' own offer of it stands, with every way they give.
    assert f"feature:{feature}" in offers(result)


@pytest.mark.parametrize(
    ("text", "feature"),
    [
        ("honestly I don't mind crime, but I want good lighting", "crime_violence_robbery"),
        ("honestly crime doesn't matter, I grew up in worse", "crime_burglary_theft"),
        ("honestly crime doesn't bother me one bit", "crime_violence_robbery"),
        ("honestly not bothered about noise, really", "noise_exposure"),
        ("honestly I don't care about main roads", "road_major_exposure"),
        ("honestly noise is not important to me", "noise_exposure"),
    ],
)
def test_a_nuisance_that_is_said_not_to_matter_is_no_guess(text: str, feature: str):
    # The model quotes all of it. A word that turns stands in the quote, and it
    # is said of how much the thing counts, or stands after the thing.
    answer = model_output(weight_ops=[model_weight(feature, provenance="stated", words=text)])

    result, _ = asked(answer, text=text)

    assert _guesses(result, f"feature:{feature}") == []


# --- What is said about a thing, which a model leaves out of what it quotes ------------------


@pytest.mark.parametrize(
    ("text", "feature", "words"),
    [
        # The words that turn the wish stand after the thing, beyond a mark, and the model
        # rests the thing on words that stand clear of both.
        ("honestly a station, heaven forbid, and that is final", "station_walk", "is final"),
        ("honestly a park, no thanks, as I said before", "park_proximity", "as I said before"),
        ("honestly a playground would be hell, believe me", "play_space_proximity", "believe me"),
        # The wish is somebody else's, and the model quotes the thing alone or other words.
        ("my mum is after a park, and that is final", "park_proximity", "that is final"),
        ("honestly my partner wants a station nearby", "station_walk", "a station nearby"),
        ("a playground is what my sister is after, truly", "play_space_proximity", "truly"),
    ],
)
def test_what_is_said_about_a_thing_is_read_where_the_thing_stands(
    text: str, feature: str, words: str
):
    answer = model_output(weight_ops=[model_weight(feature, words=words)])

    result, _ = asked(answer, text=text)

    assert _guesses(result, f"feature:{feature}") == []
    # The rules' own offer of it stands, with every way they give.
    assert f"feature:{feature}" in offers(result)


@pytest.mark.parametrize(
    ("text", "words"),
    [
        # What turns a wish, or whose it is, is said of another thing of the sentence.
        ("honestly pubs, heaven forbid, but a park would be grand", "a park would be grand"),
        ("honestly my mum wants a pub, but a park would do me", "a park would do me"),
        ("honestly no pubs, and a park nearby", "a park nearby"),
        ("My mate is after nightlife and I want a park", "I want a park"),
        # A heading of a list is nobody's wish but the speaker's.
        ("Wants: a park, honestly", "a park"),
        ("Needs: a park and a station", "a park"),
        # What goes on to say something is said of that.
        ("honestly a park, not too expensive", "a park"),
        ("honestly a park, nothing fancy", "a park"),
        ("honestly a park, I can't wait", "a park"),
        # The speaker's own household wishes as the speaker does.
        ("honestly my dog needs a park", "a park"),
    ],
)
def test_what_is_said_of_another_thing_takes_no_guess_from_this_one(text: str, words: str):
    answer = model_output(weight_ops=[model_weight("park_proximity", words=words)])

    result, _ = asked(answer, text=text)

    assert _guesses(result, "feature:park_proximity") == ["more"]


# --- An end of a scale nobody named --------------------------------------------------------


@pytest.mark.parametrize("toward", ["high", "low"])
@pytest.mark.parametrize(
    ("text", "tag", "words"),
    [
        ("honestly the pace of the place, whatever that means", "pace", "the pace of the place"),
        ("honestly something about built age, I suppose", "built_age", "built age"),
        # The model leaves the name of the scale out of what it quotes.
        ("honestly the pace of the place, whatever that means", "pace", "of the place"),
        # No phrase of core's names the scale, or an end of it.
        ("honestly the age of the buildings, I suppose", "built_age", "the age of the buildings"),
        ("honestly it depends on the homes there", "homes", "the homes there"),
    ],
)
def test_the_name_of_a_scale_is_no_guess_at_an_end_whichever_end_the_model_names(
    text: str, tag: str, words: str, toward: str
):
    # Check 5 fired where the model named no end. It named one here, and the
    # words name the scale and neither of its ends.
    answer = model_output(tag_ops=[model_tag(tag, toward=toward, words=words)])

    result, _ = asked(answer, text=text)

    assert _guesses(result, f"tag:{tag}") == []
    assert Check.NO_END in fired(answer, text)
    offer = offers(result)[f"tag:{tag}"]
    assert [way.id for way in offer.choices] == ["more", "less", "ignore"]


@pytest.mark.parametrize(
    ("text", "words", "toward", "way"),
    [
        ("honestly somewhere calm, I suppose", "somewhere calm", "low", "less"),
        ("honestly a calm pace of life, I suppose", "a calm pace of life", "low", "less"),
        ("honestly somewhere buzzy, I suppose", "buzzy", "high", "more"),
    ],
)
def test_an_end_that_the_words_name_is_the_guess(text: str, words: str, toward: str, way: str):
    answer = model_output(tag_ops=[model_tag("pace", toward=toward, words=words)])

    result, _ = asked(answer, text=text)

    assert _guesses(result, "tag:pace") == [way]


@pytest.mark.parametrize(
    ("text", "tag", "words", "toward"),
    [
        # The model quotes the end alone, and leaves out the word that turns it away.
        ("honestly not buzzy at all", "pace", "buzzy", "high"),
        ("honestly houses, not flats", "homes", "flats", "high"),
        ("honestly nothing historic for me", "built_age", "historic", "high"),
        # It quotes all of it, and names the end that was turned away.
        ("honestly calm, not buzzy", "pace", "honestly calm, not buzzy", "high"),
        ("honestly flats, not houses", "homes", "honestly flats, not houses", "low"),
        # Two words that turn: nobody can say which way, whichever end it names.
        ("honestly I wouldn't say no to buzzy", "pace", "buzzy", "high"),
        ("honestly I wouldn't say no to buzzy", "pace", "buzzy", "low"),
    ],
)
def test_an_end_that_the_words_turn_away_is_no_guess_however_little_a_model_quotes(
    text: str, tag: str, words: str, toward: str
):
    answer = model_output(tag_ops=[model_tag(tag, toward=toward, words=words)])

    result, _ = asked(answer, text=text)

    assert _guesses(result, f"tag:{tag}") == []
    assert [way.id for way in offers(result)[f"tag:{tag}"].choices][:2] == ["more", "less"]


# --- How much a wish counts ---------------------------------------------------------------


def _above_all(result: Any, target: str) -> bool:
    """Whether some way of an offer would set a thing to count above all."""
    return any(
        edit.action is WeightAction.SET and edit.value > 0
        for way in offers(result)[target].choices
        for edit in (*way.operations.weight_ops, *way.operations.tag_ops)
    )


@pytest.mark.parametrize(
    ("text", "words"),
    [
        # What is essential is said of another thing, in another clause or sentence.
        ("honestly a park is essential, and maybe pubs", "a park is essential, and maybe pubs"),
        ("A garden is a must. Honestly, a pub as well", "A garden is a must. Honestly, a pub"),
        ("honestly a pub, you must be joking", "a pub, you must be joking"),
        ("honestly I hate pubs. But a station is essential", "But a station is essential"),
    ],
)
def test_a_thing_does_not_count_above_all_for_what_is_said_of_another(text: str, words: str):
    answer = model_output(
        weight_ops=[model_weight("venue_evening_per_homes", direction="more", words=words)]
    )

    result, _ = asked(answer, text=text)

    assert not _above_all(result, "feature:venue_evening_per_homes")


@pytest.mark.parametrize(
    ("text", "words"),
    [
        ("honestly a pub is essential", "a pub is essential"),
        ("honestly a pub is essential", "pub"),
        ("A garden would be nice. Honestly, pubs are a must", "pubs are a must"),
    ],
)
def test_a_thing_counts_above_all_where_it_is_said_of_the_thing(text: str, words: str):
    answer = model_output(
        weight_ops=[model_weight("venue_evening_per_homes", direction="more", words=words)]
    )

    result, _ = asked(answer, text=text)

    assert _above_all(result, "feature:venue_evening_per_homes")


# --- What is shown under "You wrote" --------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "words"),
    [
        ("honestly a pub, you must be joking", "a pub, you must be joking"),
        ("honestly pubs. Not on your life, mate", "pubs. Not on your life"),
        ("honestly a pub would be grand", "pub"),
    ],
)
def test_all_that_an_offer_rests_on_is_shown_with_it(text: str, words: str):
    # What a model quoted runs on past the thing, and what is shown ran no
    # further than the thing: the words that mock the wish were left out.
    answer = model_output(
        weight_ops=[model_weight("venue_evening_per_homes", direction="more", words=words)]
    )

    found = through_the_route(answer, text)

    [offer] = found["suggestions"]
    shown = offer["shown"]
    assert words in text[shown["start"] : shown["end"]]
    for span in offer["spans"]:
        assert shown["start"] <= span["start"] < span["end"] <= shown["end"]


# --- A way of travelling nobody named ------------------------------------------------------


def _modes(result: Any) -> set[str]:
    return {
        edit.mode.value
        for offer in offers(result).values()
        for way in offer.choices
        for edit in way.operations.commute_ops
    }


@pytest.mark.parametrize(
    "text",
    [
        # The walk is said of another thing: in another clause, in another
        # sentence, and in the clause of the journey itself.
        "Honestly, a park I can walk to; 20 minutes to Cindermoor Works",
        "Honestly, 20 minutes to Cindermoor Works. I like to cycle at weekends",
        "Honestly, 20 minutes to Cindermoor Works, and a supermarket within walking distance",
        "Honestly, 20 minutes to Cindermoor Works and a park I can walk to",
        "Honestly, 20 minutes to Cindermoor Works and a supermarket within walking distance",
    ],
)
@pytest.mark.parametrize("mode", ["walk", "cycle", "unchanged"])
def test_a_walk_that_is_said_of_another_thing_is_not_the_way_to_work(text: str, mode: str):
    # The model quotes all of what was typed, whatever way it names.
    journey = model_commute(
        destination_text="Cindermoor Works", max_minutes=20, mode=mode, words=text
    )

    result, _ = asked(model_output(commute_ops=[journey]), text=text)

    assert _modes(result) == {"unchanged"}


@pytest.mark.parametrize(
    ("text", "words", "mode"),
    [
        ("Honestly, 20 minutes on foot to Cindermoor Works", "", "walk"),
        ("Honestly, a 20 minute walk to Cindermoor Works", "", "walk"),
        ("Honestly, 20 minutes to Cindermoor Works by bike", "Cindermoor Works", "cycle"),
        ("I work at Cindermoor Works, honestly. A 40 minute commute on foot", "", "walk"),
        (
            "I work at Cindermoor Works, honestly. A 40 minute commute on foot",
            "A 40 minute commute on foot",
            "walk",
        ),
    ],
)
def test_the_way_is_read_beside_the_place_and_beside_the_minutes(text: str, words: str, mode: str):
    minutes = 40 if "40" in text else 20
    journey = model_commute(
        destination_text="Cindermoor Works", max_minutes=minutes, mode="pt", words=words or text
    )

    result, _ = asked(model_output(commute_ops=[journey]), text=text)

    assert _modes(result) == {mode}


def test_a_way_that_was_named_and_not_taken_is_said_once():
    text = "honestly 30 minutes to Pellam Exchange and a park I can walk to"
    journey = model_commute(destination_text="Pellam Exchange", max_minutes=30, words=text)

    found = through_the_route(model_output(commute_ops=[journey]), text)

    [offer] = [offer for offer in found["suggestions"] if offer["target"] == "commute"]
    assert offer["said"] == [
        "Burro took public transport. "
        "If you travel another way, change it once the journey is added."
    ]


# --- A least as a most ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "amount"),
    [
        ("honestly at least \N{POUND SIGN}2,000 a month", 2000),
        ("honestly minimum \N{POUND SIGN}2,000 a month, I want somewhere nice", 2000),
        ("honestly no less than \N{POUND SIGN}400k, to get a decent place", 400000),
        ("honestly my budget isn't 2000, it's 1500", 2000),
        ("honestly not \N{POUND SIGN}2,000 a month, I said \N{POUND SIGN}1,500", 2000),
    ],
)
def test_an_amount_that_may_be_a_least_or_is_turned_away_is_no_guess(text: str, amount: int):
    for words in (text, str(amount) if "2000" in text else text.split(",")[0]):
        budget = model_budget(amount=amount, strictness="hard", words=words)

        result, _ = asked(model_output(budget_ops=[budget]), text=text)

        assert _guesses(result, "budget") == [], words


@pytest.mark.parametrize(
    ("text", "amount", "way"),
    [
        # "Up to" says the most that can be paid, so the guess is the firm limit.
        ("honestly up to \N{POUND SIGN}1,700 a month", 1700, FIRM),
        ("honestly under \N{POUND SIGN}1,700 a month", 1700, GUIDE),
        ("honestly about \N{POUND SIGN}1,700 a month, not a penny more", 1700, GUIDE),
        ("honestly my budget isn't 2000, it's 1500", 1500, GUIDE),
        ("honestly not more than \N{POUND SIGN}1,700 a month", 1700, FIRM),
    ],
)
def test_an_amount_that_is_a_most_is_still_the_guess(text: str, amount: int, way: str):
    budget = model_budget(amount=amount, words=text)

    result, _ = asked(model_output(budget_ops=[budget]), text=text)

    assert _guesses(result, "budget") == [way]


# --- A number of one kind, offered as another ------------------------------------------------


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        # Money, a number of bedrooms, and figures inside a word that is no number.
        ("honestly the train is 45 quid a week to Pellam Exchange", 45),
        ("honestly parking is \N{POUND SIGN}45 a week at Pellam Exchange", 45),
        ("honestly parking is 90pcm near Pellam Exchange", 90),
        ("honestly a 15 bedroom pile near Pellam Exchange", 15),
        ("honestly a 15-bed pile near Pellam Exchange", 15),
        ("honestly flat 35b, Pellam Exchange", 35),
        ("honestly near SW19 and Pellam Exchange", 19),
    ],
)
def test_a_number_that_is_no_number_of_minutes_is_no_limit_on_a_journey(text: str, minutes: int):
    journey = model_commute(destination_text="Pellam Exchange", max_minutes=minutes, words=text)

    result, _ = asked(model_output(commute_ops=[journey]), text=text)

    limits = {
        edit.max_minutes
        for offer in offers(result).values()
        for way in offer.choices
        for edit in way.operations.commute_ops
    }
    assert limits <= {0}
    assert Check.NOT_TYPED in fired(model_output(commute_ops=[journey]), text)


@pytest.mark.parametrize(
    ("text", "amount"),
    [
        ("honestly I spend 900 minutes a week on trains", 900),
        ("honestly 900mins a week on trains", 900),
        ("honestly a hotel with 500 bedrooms nearby", 500),
    ],
)
def test_a_number_of_minutes_or_of_bedrooms_is_no_budget(text: str, amount: int):
    budget = model_budget(amount=amount, words=text)

    result, _ = asked(model_output(budget_ops=[budget]), text=text)

    amounts = {
        edit.amount
        for offer in offers(result).values()
        for way in offer.choices
        for edit in way.operations.budget_ops
    }
    assert amounts <= {0}
    assert Check.NOT_TYPED in fired(model_output(budget_ops=[budget]), text)


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        ("honestly 35-40min to Pellam Exchange", 40),
        ("honestly 30-40 minutes to Pellam Exchange", 40),
        ("honestly twenty minutes to Pellam Exchange", 20),
        ("honestly Pellam Exchange within 45", 45),
        ("honestly 25 to 35 minutes from Pellam Exchange", 35),
    ],
)
def test_a_number_of_minutes_is_read_however_it_is_written(text: str, minutes: int):
    journey = model_commute(destination_text="Pellam Exchange", max_minutes=minutes, words=text)

    result, _ = asked(model_output(commute_ops=[journey]), text=text)

    limits = {
        edit.max_minutes
        for offer in offers(result).values()
        for way in offer.choices
        for edit in way.operations.commute_ops
    }
    assert limits == {minutes}


# --- What "add all" takes -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "words"),
    [
        ("honestly, is a park worth it?", "a park"),
        ("honestly would a park be any good? I can't tell", "a park"),
        ("Do I even want a park?", "a park"),
    ],
)
def test_add_all_takes_nothing_from_a_sentence_that_asks(text: str, words: str):
    answer = model_output(weight_ops=[model_weight("park_proximity", words=words)])

    found = through_the_route(answer, text)

    assert [offer["add_all"] for offer in found["suggestions"]] == [""]


# --- Words the rules offer a reading of -----------------------------------------------------


def _guarded_with(text: str, answer: Any, note: str | None) -> Guarded:
    """What the guard leaves of an answer, with the note of every offer of the rules set."""
    request = InterpretRequest(text=text, spec=renter(), release=release())
    rules = RuleInterpreter()
    ruled = rules.interpret(request)
    if note is not None:
        noted = tuple(offer.replace(note=note) for offer in ruled.suggestions)
        ruled = ruled.replace(suggestions=noted)
    names = Names(release())
    typed = Typed(text, Grammar(names, release()), release())
    output = parsed(json.dumps(answer))
    return guarded(output, request, typed, names, ruled, rules.by_sentence(request))


@pytest.mark.parametrize("text", ["honestly gritty I suppose", "honestly polished I suppose"])
def test_a_word_the_rules_read_into_the_vibe_that_counts_crime_is_the_rules_to_offer(text: str):
    # A word about how smart or how rough a place is, is offered by the rules
    # towards an end of the scale that counts recorded crime. Whether or not
    # core gives the word a note, a model adds no reading of its own to it.
    word = text.split()[1]
    answer = model_output(
        weight_ops=[
            model_weight("land_industry", direction="more", words=word),
            model_weight("noise_exposure", words=text),
        ],
        tag_ops=[model_tag("village_feel", words=word), model_tag("leafy", words=word)],
    )

    for note in (None, ""):
        found = _guarded_with(text, answer, note)
        assert found.readings == [], note
        assert found.fired[Check.NEAREST] == 4, note


def _only_the_rules_offer(words: str) -> bool:
    """Whether nothing a model reads of some words is offered, alone or beside another thing."""
    text = f"honestly {words}, I suppose"
    found: list[bool] = []
    for answer in (
        model_output(weight_ops=[model_weight("conservation_cover", words=words)]),
        model_output(tag_ops=[model_tag("village_feel", words=text)]),
        model_output(tag_ops=[model_tag("built_age", toward="high", words=words)]),
    ):
        result, _ = asked(answer, text=text)
        found += [
            offer.read_by is InterpreterName.RULE
            and not any(way.guess or way.meant for way in offer.choices)
            for offer in offers(result).values()
        ]
    return all(found)


# What these words offer is the rules' to keep: two readings of a word about
# wealth, both of the place, and three of a word about identity (ADR 0012). A
# model adds none. Core lists each of these words, and offers its readings.
@pytest.mark.parametrize("words", ["slightly affluent", "somewhere posh"])
def test_a_model_offers_nothing_that_rests_on_a_word_about_wealth(words: str):
    assert _only_the_rules_offer(words)


@pytest.mark.parametrize("words", ["a bit rough"])
def test_a_model_offers_nothing_that_rests_on_a_word_for_run_down(words: str):
    assert _only_the_rules_offer(words)


@pytest.mark.parametrize("words", ["a real identity", "its own character"])
def test_a_model_adds_no_reading_of_a_word_about_identity(words: str):
    assert _only_the_rules_offer(words)


# --- A nuisance, and what is said of it -----------------------------------------------------


@pytest.mark.parametrize(
    ("text", "feature"),
    [
        # What troubles the person is said after the thing, or before it.
        ("burglary worries me", "crime_burglary_theft"),
        ("knife crime is my biggest worry", "crime_violence_robbery"),
        ("honestly I worry about burglary round here", "crime_burglary_theft"),
        ("honestly no traffic noise, thanks", "noise_exposure"),
        ("honestly less noise would be good", "noise_exposure"),
    ],
)
def test_a_nuisance_that_troubles_the_person_is_the_guess(text: str, feature: str):
    for words in (text, ""):
        named = words or next(w for w in ("burglary", "knife crime", "noise") if w in text)
        answer = model_output(weight_ops=[model_weight(feature, words=named)])

        result, _ = asked(answer, text=text)

        assert _guesses(result, f"feature:{feature}") == ["less"], named


@pytest.mark.parametrize(
    ("text", "feature"),
    [
        # A word that turns stands after the thing: it is said of the thing,
        # and is no wish for less of it.
        ("honestly crime doesn't bother me one bit", "crime_violence_robbery"),
        ("honestly the noise isn't a problem for me", "noise_exposure"),
        ("honestly burglary is nothing to me", "crime_burglary_theft"),
    ],
)
def test_a_nuisance_with_a_word_that_turns_after_it_is_no_guess(text: str, feature: str):
    for words in (text, next(w for w in ("crime", "noise", "burglary") if w in text)):
        answer = model_output(weight_ops=[model_weight(feature, words=words)])

        result, _ = asked(answer, text=text)

        assert _guesses(result, f"feature:{feature}") == [], words


# --- Words that say nothing of a thing ------------------------------------------------------


@pytest.mark.parametrize("words", ["a", "I", "I want", "and the", "would like a", "to have"])
def test_words_that_name_nothing_are_no_words_to_rest_a_thing_on(words: str):
    # Every word of the quote is one that core's grammar places, and none
    # names a thing: an article, the speaker, a wish, a word that joins.
    text = "honestly I want a quiet place and the rest, I would like a think"
    answer = model_output(tag_ops=[model_tag("leafy", words=words)])

    result, _ = asked(answer, text=text)

    assert "tag:leafy" not in offers(result)
    assert Check.WORDS in fired(answer, text)


@pytest.mark.parametrize("words", ["boozers", "a proper brunch spot", "trees", "somewhere green"])
def test_words_core_does_not_know_may_still_name_a_thing(words: str):
    text = f"honestly {words}, I suppose"
    answer = model_output(tag_ops=[model_tag("foodie", words=words)])

    result, _ = asked(answer, text=text)

    assert [way.id for o in offers(result).values() for way in o.choices if way.meant]


# --- What an offer says it would do ---------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "answer", "target", "does"),
    [
        # One way is left to take, no guess is marked, and the clause holds a
        # sign of doubt. What is left is the way the doubt is about.
        (
            "honestly not leafy",
            model_output(tag_ops=[model_tag("leafy", words="leafy")]),
            "tag:leafy",
            "Leafy: add it?",
        ),
        (
            "honestly no theatres for me",
            # A model that names the count is heard as a wish for what is ranked on.
            model_output(weight_ops=[model_weight("culture_venues", words="theatres")]),
            "feature:culture_venues_per_homes",
            "More culture nearby: count it?",
        ),
        (
            "honestly crime doesn't bother me one bit",
            model_output(),
            "feature:crime_violence_robbery",
            "Less recorded violence and robbery: count it?",
        ),
    ],
)
def test_the_one_way_left_of_a_thing_in_doubt_is_asked_and_not_said(
    text: str, answer: Any, target: str, does: str
):
    found = through_the_route(answer, text)

    offer = next(offer for offer in found["suggestions"] if offer["target"] == target)
    assert [way["guess"] for way in offer["choices"]] == [False, False]
    assert offer["does"] == does
    assert offer["add_all"] == ""


def test_the_one_way_of_a_thing_that_nothing_puts_in_doubt_is_said():
    found = through_the_route(model_output(), "honestly somewhere leafy")

    [offer] = found["suggestions"]
    assert offer["does"] == "Add Leafy."


# --- A community's amenity ------------------------------------------------------------------


@pytest.mark.parametrize("words", ["near a synagogue", "a mosque nearby", "close to a gurdwara"])
def test_no_offer_of_a_models_rests_on_a_communitys_amenity(words: str):
    # No feature covers a place of worship, and what stands near one is no
    # reading of the place: the rules say so, and a model adds no vibe to it.
    text = f"honestly {words}, I suppose"
    answer = model_output(
        tag_ops=[model_tag("village_feel", words=words)],
        weight_ops=[model_weight("venue_independent", words=text)],
    )

    result, _ = asked(answer, text=text)

    assert result.suggestions == ()
    assert UnmetCategory.COMMUNITY_AMENITIES in result.unmet


def test_a_journey_that_took_no_number_says_which_number_it_will_have():
    # "Can't be more than 45 minutes" holds a word of doubt, so its number is
    # not taken. The journey is then added with a number nobody gave, and the
    # offer said nothing of it.
    found, _ = served_again("own-022")

    [journey] = [offer for offer in found["suggestions"] if offer["target"] == "commute"]
    [edit] = [e for way in journey["choices"] for e in way["operations"]["commute_ops"]]
    assert edit["max_minutes"] == 0
    assert journey["said"][0].startswith(
        "Burro took no number of minutes from these words, and will take 45. "
    )


# --- What an offer says the person gave -----------------------------------------------------


def _said_of_the_journey(text: str, place: str, minutes: int) -> list[str]:
    journey = model_commute(destination_text=place, max_minutes=minutes, words=text)
    found = through_the_route(model_output(commute_ops=[journey]), text)
    return [
        line
        for offer in found["suggestions"]
        if any(
            edit["max_minutes"] == minutes
            for way in offer["choices"]
            for edit in way["operations"]["commute_ops"]
        )
        for line in offer["said"]
    ]


def test_two_journeys_are_not_said_to_be_a_range_of_minutes():
    # The model quotes all of it. The 20 minutes are of another journey.
    text = "Honestly, at most 20 minutes to Pellam Exchange and about 50 to Foxholt Market"

    said = _said_of_the_journey(text, "Foxholt Market", 50)

    assert not [line for line in said if line.startswith("You gave")]


@pytest.mark.parametrize(
    ("text", "low"),
    [
        ("Honestly, 35-40min to Foxholt Market", 35),
        ("Honestly, 30 to 40 minutes to Foxholt Market", 30),
        ("Honestly, between 25 and 40 minutes from Foxholt Market", 25),
    ],
)
def test_a_range_of_minutes_is_said_with_which_was_taken(text: str, low: int):
    said = _said_of_the_journey(text, "Foxholt Market", 40)

    assert f"You gave {low} to 40: Burro took 40." in said
