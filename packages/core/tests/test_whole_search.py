"""The whole of a search, typed in a few sentences, and each part of one.

A whole search holds a few hedged wishes, a word for a smart area, a word for
character, a journey given as a range of minutes, to a place the release may
not hold, and a home to rent or to buy. These tests hold what the reader
makes of each part. Every name and every sentence in them is made up.

The reader still never guesses. A part that is not plain is offered, and the
person chooses.
"""

import dataclasses
from typing import Any

import pytest
from burro_core.catalogue import CHAINS, FEATURES, TAGS, direction_allowed
from burro_core.ids import (
    AssumptionCode,
    Direction,
    FeatureId,
    GrittyVariant,
    InterpretStatus,
    OpsGroup,
    Provenance,
    Tenure,
    UnmetCategory,
)
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter
from burro_core.lexicon import lexicon_of
from burro_core.ops import NO_OPERATIONS
from burro_core.reducer import apply
from burro_core.spec import PreferenceSpec, default_spec

from .support import fixture_release, place_id, small_release

HIGH_STREET = ("feature:highstreet_access",)
RENTER = default_spec(Tenure.RENT)
BUYER = default_spec(Tenure.BUY)
READER = RuleInterpreter()
QUIET = ("unchanged", "none", "default", 0, 0.0)


def read(
    text: str, spec: PreferenceSpec = RENTER, variant: GrittyVariant = GrittyVariant.B
) -> InterpretResult:
    request = InterpretRequest(text=text, spec=spec, release=small_release(variant))
    return READER.interpret(request)


def said(edit: Any) -> dict[str, Any]:
    """An edit with its sentinels left out."""
    return {k: v for k, v in edit.model_dump(mode="json").items() if v not in QUIET}


def offers(result: InterpretResult) -> list[tuple[str, list[str]]]:
    """What is offered, as a person reads it: each thing, and the choices under it."""
    return [
        (found.target, [choice.label for choice in found.choices]) for found in result.suggestions
    ]


def rested(text: str, result: InterpretResult) -> list[list[str]]:
    return [[text[s.start : s.end] for s in found.spans] for found in result.suggestions]


# --- A range of minutes ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        ("35-40min to Pellam Cross", 40),
        ("35-40 minutes to Pellam Cross", 40),
        ("35\N{EN DASH}40 mins to Pellam Cross", 40),
        ("35 to 40 minutes to Pellam Cross", 40),
        ("within 30 to 40 minutes of Pellam Cross", 40),
        ("at most 25-30min commute from Pellam Cross", 30),
        ("no more than 20-25 minutes to Pellam Cross by bike", 25),
        ("get to Pellam Cross in 30-35 minutes", 35),
        ("I work at Pellam Infirmary, a 30-40 minute commute", 40),
        ("I work at Pellam Infirmary and want to get there in 35-40 minutes at most", 40),
    ],
)
def test_a_range_of_minutes_is_a_firm_limit_at_its_upper_end_and_is_said_to_be_assumed(
    text: str, minutes: int
):
    """Decided on 2026-09-24: whoever gives a range has said how long is too long."""
    result = read(text)
    (edit,) = result.operations.commute_ops
    assert (edit.max_minutes, edit.strictness) == (minutes, "hard")
    assert (result.status, result.unread, result.suggestions) == (InterpretStatus.OK, (), ())
    # The person gave two numbers and Burro took one, so the chip says it was assumed.
    assumed = [(a.code, a.group, a.index) for a in result.assumptions]
    assert (AssumptionCode.MAX_MINUTES, OpsGroup.COMMUTE, 0) in assumed
    assert apply(RENTER, result.operations, small_release()).rejected == ()
    # And the journey rests on both numbers.
    words = " ".join(text[found.start : found.end] for found in result.rests_on)
    assert str(minutes) in words


def test_minutes_that_are_no_range_are_not_said_to_be_assumed():
    for text in ("40 minutes to Pellam Cross", "at most 40min commute from Pellam Cross"):
        result = read(text)
        assert AssumptionCode.MAX_MINUTES not in {found.code for found in result.assumptions}


@pytest.mark.parametrize(
    "text",
    [
        # The second number is no more than the first, so it is no range.
        "40-35 minutes to Pellam Cross",
        "40 to 40 minutes to Pellam Cross",
        # A range of anything else is two numbers, and the reader sets neither.
        "2-3 bed flat to rent",
        "2 to 3 bedrooms",
        "£1,500-£1,800 a month",
        "1500-1800 a month",
        # A range with no minutes to it.
        "35-40 to Pellam Cross",
        # A range that is a minimum.
        "at least 35-40 minutes from Pellam Cross",
    ],
)
def test_a_range_that_is_not_of_minutes_or_runs_backwards_sets_nothing(text: str):
    result = read(text)
    assert result.operations.commute_ops == ()
    assert not [edit for edit in result.operations.budget_ops if edit.amount or edit.segment != ""]
    for edit in result.operations.budget_ops:
        assert (edit.amount, edit.segment) == (0, "unchanged"), text


# --- Thousands and millions ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "amount"),
    [
        ("max £400k for a flat", 400_000),
        ("max 400k for a flat", 400_000),
        ("max 400K for a flat", 400_000),
        ("1.5m for a detached house", 1_500_000),
        ("£1.5m for a detached house", 1_500_000),
        ("1.25M, detached", 1_250_000),
        ("a budget of 2m", 2_000_000),
        ("up to 2m for a detached house", 2_000_000),
        ("under 2k a month", 2_000),
        ("1.5k pcm", 1_500),
    ],
)
def test_k_and_m_after_a_number_are_thousands_and_millions(text: str, amount: int):
    (edit,) = read(text).operations.budget_ops
    assert edit.amount == amount
    assert apply(RENTER, read(text).operations, small_release()).rejected == ()


@pytest.mark.parametrize(
    "text",
    [
        *("5m to Pellam Cross", "a park within 5m", "10m walk to a station", "2m"),
        "I live 5m away",
        # Before "from", "to" and "of" a thing or a place it is a distance, point or no point.
        *("1.5m from a park", "within 1.5m of a station", "1.5m to Pellam Cross"),
    ],
)
def test_a_number_of_m_with_no_word_of_money_beside_it_is_no_amount(text: str):
    # It is as likely five minutes or five metres as five million.
    result = read(text)
    assert result.operations.budget_ops == ()
    assert [found.target for found in result.suggestions if found.target == "budget"] == []


@pytest.mark.parametrize(
    "text",
    [
        # A word that caps is no word of money: it caps minutes and metres as it caps pounds.
        *("within 5m", "under 5m", "up to 5m", "around 15m", "about 20m", "less than 5m"),
        *("no more than 10m", "max 10m", "10m max", "quiet, up to 5m"),
        # Beside a thing to be near or a place to reach, it is as likely how far off that is.
        *("near the tube, 5m max", "close to a park, max 1m", "near a station, 10m max"),
        *("a park, no more than 0.5m", "near a station, 0.5m max", "parks nearby, around 1.5m"),
        *("I work at Pellam Cross, 30m max", "near Pellam Cross, 20m max"),
        "30 minutes to Pellam Cross, 1.5m",
        # And so it is where renting or buying is said in another part of the sentence.
        *("to buy, near a station, 10m max", "to rent, near a park, 5m max"),
        "buying, near a station, 0.5m max",
    ],
)
def test_a_number_of_m_that_nothing_says_is_money_is_never_applied_as_a_budget(text: str):
    # "Near the tube, 5m max" was applied as a budget of five million pounds to buy,
    # and "I work at Pellam Cross, 30m max" as one of thirty million.
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert apply(RENTER, result.operations, small_release()).spec == RENTER


@pytest.mark.parametrize(
    ("text", "most"),
    [
        ("1.5m", ""),
        # "Max" says the most that can be paid, and the choice says so.
        ("max 1.5m", "no more than "),
        # "Within" and "under" make no budget firm.
        ("within 1.5m", ""),
        ("leafy, under 1.5m", ""),
    ],
)
def test_millions_with_nothing_said_of_a_home_are_offered_and_the_person_chooses(
    text: str, most: str
):
    result = read(text)
    assert (result.status, result.operations) == (InterpretStatus.SUGGEST, NO_OPERATIONS)
    label = f"Set a budget of {most}£1,500,000, to buy"
    assert ("budget", [label, "Leave it out"]) in offers(result)


@pytest.mark.parametrize(
    ("text", "amount"),
    [
        # The home it is for, or a word for paying, stands in the same part of the sentence.
        ("a detached house for 2m", 2_000_000),
        ("a detached house up to 2m", 2_000_000),
        ("my budget is 1.5m", 1_500_000),
        ("30 minutes to Pellam Cross, a detached house up to 2m", 2_000_000),
        # Or the sentence says something of a home, and names nothing to be near or to reach.
        ("buying, 1.5m max", 1_500_000),
        ("quiet, buying, 1.5m max", 1_500_000),
        ("1.2m, detached", 1_200_000),
    ],
)
def test_a_number_of_m_is_an_amount_where_the_sentence_says_what_it_is_for(text: str, amount: int):
    (edit,) = read(text).operations.budget_ops
    assert (edit.amount, edit.tenure) == (amount, "buy")


@pytest.mark.parametrize("text", ["1.5m away from the station", "a park 1.5m away"])
def test_a_number_of_m_that_is_said_to_be_away_is_offered_as_no_budget(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert [found.target for found in result.suggestions if found.target == "budget"] == []


def test_the_places_of_these_tests_are_the_ones_the_small_release_holds():
    assert [place_id(n) for n in (1, 4)] == ["syn-p0001", "syn-p0004"]


# --- The words that name a place to reach ------------------------------------------------


@pytest.mark.parametrize(
    ("text", "place", "minutes", "mode"),
    [
        ("I commute to Pellam Cross", 1, 0, "unchanged"),
        ("I need to get to Pellam Infirmary", 4, 0, "unchanged"),
        ("I travel to Pellam Cross", 1, 0, "unchanged"),
        ("from work at Pellam Infirmary", 4, 0, "unchanged"),
        ("30 minutes from work at Pellam Infirmary", 4, 30, "unchanged"),
        ("20 minutes from my office at Pellam Infirmary by bike", 4, 20, "cycle"),
        ("not far from work at Pellam Infirmary", 4, 0, "unchanged"),
        ("a 40 minute commute from Pellam Cross", 1, 40, "unchanged"),
        ("within 30 minutes of Pellam Cross", 1, 30, "unchanged"),
    ],
)
def test_each_way_of_naming_a_place_to_reach_adds_a_journey_to_it(
    text: str, place: int, minutes: int, mode: str
):
    result = read(text)
    (edit,) = result.operations.commute_ops
    assert (edit.action, edit.place_id) == ("add", place_id(place))
    assert (edit.max_minutes, edit.mode) == (minutes, mode)
    assert (result.status, result.unread) == (InterpretStatus.OK, ())


@pytest.mark.parametrize(
    "text",
    [
        "within 30 minutes of pellam cross",
        "I WORK AT PELLAM INFIRMARY",
        "i commute to Pellam cross",
        "at most 25-30min commute from pellam Cross",
    ],
)
def test_a_place_the_release_holds_is_matched_without_regard_to_capitals(text: str):
    (edit,) = read(text).operations.commute_ops
    assert edit.place_id in (place_id(1), place_id(4))


@pytest.mark.parametrize(
    ("text", "offered"),
    [
        ("I commute from Pellam Cross", ["Pellam Cross"]),
        ("commuting from Pellam Infirmary", ["Pellam Infirmary"]),
        ("leafy, and I commute from Pellam Cross", ["Pellam Cross"]),
        # The place the person works at is named, so the other is where they live.
        (
            "I work at Pellam Infirmary and commute from Pellam Cross",
            ["Pellam Infirmary", "Pellam Cross"],
        ),
        (
            "I commute from Pellam Cross. I work at Pellam Infirmary.",
            ["Pellam Cross", "Pellam Infirmary"],
        ),
    ],
)
def test_a_commute_from_a_place_with_no_time_said_of_it_is_offered_and_never_applied(
    text: str, offered: list[str]
):
    # A person commutes from where they live, to where they work. "I work at
    # Pellam Infirmary and commute from Pellam Cross" was applied as a journey
    # to each, and one of the two is the home the person is leaving.
    result = read(text)
    assert (result.status, result.operations) == (InterpretStatus.SUGGEST, NO_OPERATIONS)
    journeys = [found for found in result.suggestions if found.target == "commute"]
    assert [found.label for found in journeys] == offered
    for found in journeys:
        assert [choice.label for choice in found.choices] == [
            f"Add a journey to {found.label}",
            "Leave it out",
        ]
    # What the reader makes of each sentence alone, for a model to be held to,
    # holds no journey to the place that is commuted from.
    request = InterpretRequest(text=text, spec=RENTER, release=small_release())
    alone = READER.by_sentence(request).operations.commute_ops
    assert place_id(1 if "from Pellam Cross" in text else 4) not in [e.place_id for e in alone]


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        # A time from a place says how far off it may be, and so that it is to be reached.
        ("a 40 minute commute from Pellam Cross", 40),
        ("at most 25-30min commute from Pellam Cross", 30),
        ("30 minutes commute from Pellam Cross by bike", 30),
    ],
)
def test_a_commute_from_a_place_with_a_time_said_of_it_is_a_journey_to_it(text: str, minutes: int):
    (edit,) = read(text).operations.commute_ops
    assert (edit.place_id, edit.max_minutes) == (place_id(1), minutes)


def test_minutes_said_apart_from_the_one_place_that_is_commuted_from_are_offered_with_it():
    text = "I commute from Pellam Cross, at most 40 minutes"
    result = read(text)
    assert result.operations == NO_OPERATIONS
    (journey,) = result.suggestions
    assert journey.choices[0].label == "Add a journey to Pellam Cross of no more than 40 minutes"
    assert rested(text, result) == [["commute from Pellam Cross", "at most 40 minutes"]]
    # Beside the place the person works at, the minutes are those of the journey to that.
    both = read("I work at Pellam Infirmary and commute from Pellam Cross, a 40 minute commute")
    assert both.operations == NO_OPERATIONS
    assert [found.choices[0].label for found in both.suggestions] == [
        "Add a journey to Pellam Infirmary within 40 minutes",
        "Add a journey to Pellam Cross",
    ]


def test_a_place_to_commute_from_that_the_release_does_not_hold_is_asked_about():
    result = read("I commute from Quillhaven Lane")
    assert result.status is InterpretStatus.CLARIFY
    assert apply(RENTER, result.operations, small_release()).spec == RENTER


@pytest.mark.parametrize(
    "text",
    [
        # The past, someone else, and a commute that is over.
        "I commuted from Pellam Cross",
        "she commutes from Pellam Cross",
        "I no longer commute from Pellam Cross",
        "I used to travel from work at Pellam Infirmary",
        # Distance that is wanted from the place.
        "far from work at Pellam Infirmary",
        "miles away from work at Pellam Infirmary",
        "at least 30 minutes from work at Pellam Infirmary",
        "nowhere near my office at Pellam Infirmary",
    ],
)
def test_a_commute_that_is_over_or_is_kept_at_a_distance_adds_no_journey(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert result.clarify == ()


@pytest.mark.parametrize(
    ("text", "asked"),
    [
        ("quiet, with access to parks", {"quiet_residential", "park_proximity"}),
        ("good access to a station", {"station_walk"}),
        ("some culture around it", {"culture_venues_per_homes"}),
        ("somewhere with pubs around", {"venue_evening_per_homes"}),
    ],
)
def test_access_to_a_thing_and_a_thing_that_is_around_are_wishes_to_be_near_it(
    text: str, asked: set[str]
):
    result = read(text)
    raised = {e.feature_id.value for e in result.operations.weight_ops}
    raised |= {e.tag_id.value for e in result.operations.tag_ops}
    assert raised == asked
    assert (result.status, result.unread) == (InterpretStatus.OK, ())
    for edit in (*result.operations.weight_ops, *result.operations.tag_ops):
        assert (edit.action, edit.step) == ("nudge", "up_large")


@pytest.mark.parametrize(
    "text", ["no access to parks", "without access to a station", "culture is not around"]
)
def test_access_that_is_turned_away_raises_nothing(text: str):
    result = read(text)
    for edit in (*result.operations.weight_ops, *result.operations.tag_ops):
        assert edit.action == "remove" or edit.step in ("down_small", "down_large"), text


# --- A journey in a prompt that is not plain ---------------------------------------------

RANGE_25_30 = "You gave 25 to 30 minutes. Burro has taken the longer."


def test_a_journey_in_a_sentence_the_grammar_makes_is_offered_with_all_that_was_said_of_it():
    text = "Maybe somewhere leafy. At most 25-30min commute from Pellam Cross."
    result = read(text)
    assert (result.status, result.operations) == (InterpretStatus.SUGGEST, NO_OPERATIONS)
    leafy, journey = result.suggestions
    assert (leafy.target, journey.target, journey.label) == ("tag:leafy", "commute", "Pellam Cross")
    assert [choice.label for choice in journey.choices] == [
        "Add a journey to Pellam Cross of no more than 30 minutes",
        "Leave it out",
    ]
    # The offer says that a range was given, and which end of it was taken.
    assert journey.note == RANGE_25_30
    assert said(journey.choices[0].operations.commute_ops[0]) == {
        "action": "add",
        "place_id": place_id(1),
        "max_minutes": 30,
        "strictness": "hard",
        "provenance": "ui_edit",
    }
    assert rested(text, result)[1] == ["At most 25-30min commute from Pellam Cross"]
    assert [text[s.start : s.end] for s in result.unread] == ["Maybe somewhere"]
    pressed = apply(RENTER, journey.choices[0].operations, small_release())
    assert pressed.rejected == ()
    assert [(c.place_id, c.max_minutes, c.strictness) for c in pressed.spec.commutes] == [
        (place_id(1), 30, "hard")
    ]


@pytest.mark.parametrize(
    ("said_of_it", "label"),
    [
        ("I work at Pellam Cross.", "Add a journey to Pellam Cross"),
        ("30 minutes to Pellam Cross.", "Add a journey to Pellam Cross within 30 minutes"),
        (
            "20 minutes to Pellam Cross by bike.",
            "Add a journey to Pellam Cross within 20 minutes by bike",
        ),
        (
            "No more than 25 minutes to Pellam Cross on foot.",
            "Add a journey to Pellam Cross of no more than 25 minutes on foot",
        ),
        (
            "I work at Pellam Cross. A 40 minute commute by tube.",
            "Add a journey to Pellam Cross within 40 minutes by public transport",
        ),
    ],
)
def test_the_choice_of_a_journey_says_its_minutes_its_limit_and_how_it_is_travelled(
    said_of_it: str, label: str
):
    result = read(f"Perhaps a park. {said_of_it}")
    assert result.operations == NO_OPERATIONS
    (journey,) = (found for found in result.suggestions if found.target == "commute")
    assert journey.choices[0].label == label
    # And it holds what its label says, and no more.
    edit = said(journey.choices[0].operations.commute_ops[0])
    assert ("max_minutes" in edit) is ("minutes" in label)
    assert ("strictness" in edit) is ("no more than" in label)
    assert ("mode" in edit) is any(how in label for how in (" by ", " on foot"))
    assert apply(RENTER, journey.choices[0].operations, small_release()).rejected == ()


def test_a_place_the_release_does_not_hold_is_asked_about_where_the_prompt_is_not_plain():
    text = "Maybe somewhere leafy. At most 25-30min commute from Quillhaven Lane."
    result = read(text)
    # Nothing is applied: the one edit is the question, and it carries no place.
    assert result.status is InterpretStatus.CLARIFY
    (edit,) = result.operations.commute_ops
    assert said(edit) == {
        "action": "add",
        "place_id": "",
        "max_minutes": 30,
        "strictness": "hard",
        "provenance": "stated",
    }
    assert result.operations.count == 1
    assert [(c.group, c.index, c.options) for c in result.clarify] == [(OpsGroup.COMMUTE, 0, ())]
    after = apply(RENTER, result.operations, small_release())
    assert after.spec == RENTER
    assert [(r.group, r.reason) for r in after.rejected] == [(OpsGroup.COMMUTE, "unknown_place")]
    # What else was noticed is offered beside it.
    assert [found.target for found in result.suggestions] == ["tag:leafy"]
    # The question rests on the words of the journey, which are not called unread.
    words = [text[r.start : r.end] for r in result.rests_on]
    assert words == ["At most 25-30min commute from Quillhaven Lane"]
    assert [text[s.start : s.end] for s in result.unread] == ["Maybe somewhere"]
    # It holds none of the words, as nothing the reader answers does.
    assert "quillhaven" not in result.model_dump_json().casefold()


def test_a_place_that_several_names_begin_with_is_asked_about_with_each_of_them():
    result = read("Maybe somewhere leafy. I work at Pellam.")
    (asked,) = result.clarify
    assert [option.name for option in asked.options] == ["Pellam Cross", "Pellam Infirmary"]
    assert result.operations.commute_ops[asked.index].place_id == ""


@pytest.mark.parametrize(
    "text",
    [
        # Something is said after the words, so nobody can say where the name ends.
        "Maybe leafy. I work at Quillhaven Lane sadly no more",
        "Maybe leafy. I work at Quillhaven Lane, which I hate",
        # The sentence is turned, is someone else's, or asks.
        "Maybe leafy. I don't work at Quillhaven Lane.",
        "Maybe leafy. My ex works at Quillhaven Lane.",
        "Maybe leafy. Do I work at Quillhaven Lane?",
        "Maybe leafy. At least 30 minutes from Quillhaven Lane.",
        # A sentence that names nothing takes it back.
        "I work at Quillhaven Lane. Not really. Maybe leafy.",
    ],
)
def test_a_place_is_asked_about_only_in_a_sentence_the_grammar_makes(text: str):
    result = read(text)
    assert (result.operations, result.clarify) == (NO_OPERATIONS, ())


@pytest.mark.parametrize(
    ("text", "label", "note", "words"),
    [
        (
            "at most 25-30min commute from Pellam Cross, I think",
            "Add a journey to Pellam Cross of no more than 30 minutes",
            RANGE_25_30,
            "at most 25-30min commute from Pellam Cross",
        ),
        (
            "20 minutes from my office at Pellam Infirmary, I suppose",
            "Add a journey to Pellam Infirmary within 20 minutes",
            "",
            "20 minutes from my office at Pellam Infirmary",
        ),
        (
            "a 25 minute walk to Pellam Cross would suit",
            "Add a journey to Pellam Cross within 25 minutes",
            "",
            "25 minute walk to Pellam Cross",
        ),
        (
            "I guess I commute from Pellam Cross",
            "Add a journey to Pellam Cross",
            "",
            "Pellam Cross",
        ),
    ],
)
def test_a_journey_in_a_sentence_the_grammar_does_not_make_holds_its_place_and_its_minutes(
    text: str, label: str, note: str, words: str
):
    # Nobody can say there how it is travelled, so the choice holds no way of travelling.
    # Its minutes are a limit where the words against them make them one, or they are a
    # range. It is still a journey, and never a rule for an area.
    result = read(text)
    assert result.operations == NO_OPERATIONS
    (journey,) = result.suggestions
    assert (journey.target, journey.choices[0].label, journey.note) == ("commute", label, note)
    edit = said(journey.choices[0].operations.commute_ops[0])
    assert "mode" not in edit
    assert ("strictness" in edit) is ("no more than" in label)
    assert rested(text, result) == [[words]]


def test_a_name_that_is_asked_about_is_not_offered_a_second_time_as_an_area():
    # In the release that is served, "Pellam" is another name for the area of Pellam
    # Cross, and three places begin with it. After "work at" it is a place that is meant.
    request = InterpretRequest(
        text="Maybe somewhere leafy. I work at Pellam.", spec=RENTER, release=fixture_release()
    )
    result = READER.interpret(request)
    assert [found.target for found in result.suggestions] == ["tag:leafy"]
    (asked,) = result.clarify
    assert [option.name for option in asked.options] == [
        "Pellam Cross",
        "Pellam Exchange",
        "Pellam Infirmary",
    ]


# --- Two words that join, of which the second adds nothing ----------------------------------


@pytest.mark.parametrize(
    ("text", "raised", "lowered"),
    [
        (
            "quiet but with some culture",
            {"quiet_residential", "culture_venues_per_homes"},
            set[str](),
        ),
        ("leafy and with a park nearby", {"leafy", "park_proximity"}, set[str]()),
        ("leafy and also quiet", {"leafy", "quiet_residential"}, set[str]()),
        ("no pubs but with a park nearby", {"park_proximity"}, {"venue_evening_per_homes"}),
        ("no pubs, but also near a station", {"station_walk"}, {"venue_evening_per_homes"}),
    ],
)
def test_with_and_also_after_a_word_that_joins_add_nothing_to_it(
    text: str, raised: set[str], lowered: set[str]
):
    result = read(text)
    assert (result.status, result.unread) == (InterpretStatus.OK, ())
    edits = (*result.operations.weight_ops, *result.operations.tag_ops)
    up = {
        getattr(e, "feature_id", None) or getattr(e, "tag_id", None)
        for e in edits
        if e.step == "up_large" and getattr(e, "direction", "default") != "less"
    }
    down = {e.feature_id.value for e in result.operations.weight_ops if e.direction == "less"}
    assert ({str(one) for one in up}, down) == (raised, lowered)


@pytest.mark.parametrize(
    "text",
    [
        # The turn may reach the thing after the two words, or may not.
        "no pubs and with parks",
        "no pubs and also parks",
        # Two words that join, of which the second is neither "with" nor "also".
        "leafy and or quiet",
        "leafy but and quiet",
        "leafy with with a park",
        # "With" and "also" open no sentence after a word that joins nothing.
        "leafy or with a park",
    ],
)
def test_two_words_that_join_are_still_not_plain_where_nobody_can_say_what_they_join(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS


# --- The size and the kind of a home --------------------------------------------------------

BY_KIND = "Burro holds what homes sell for by kind of home, and not by the number of bedrooms."
BY_BEDROOMS = "Burro holds rents by the number of bedrooms, and not by kind of home."
TO_RENT_ALONE = "Burro holds what a studio or a room costs to rent, and not to buy."


def homes(result: InterpretResult) -> list[tuple[str, list[str], str]]:
    """Each home that is offered: what it is called, its choices, and what is said of it."""
    return [
        (found.label, [choice.label for choice in found.choices], found.note)
        for found in result.suggestions
        if found.target == "budget" and "budget of" not in found.label
    ]


def test_a_home_to_buy_is_offered_by_its_kind_and_says_that_its_bedrooms_are_not_held():
    text = "If we buy, up to £425k for a 1 bed flat"
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert offers(result) == [
        ("tenure", ["Set buying", "Leave it out"]),
        ("budget", ["Set a budget of no more than £425,000, to buy", "Leave it out"]),
        ("budget", ["Set a flat, to buy", "Leave it out"]),
    ]
    assert homes(result) == [("A flat", ["Set a flat, to buy", "Leave it out"], BY_KIND)]
    # The budget rests on the words that make it a limit, so they are not left unread.
    assert rested(text, result) == [["buy"], ["up to £425k"], ["a 1 bed flat"]]
    assert [text[s.start : s.end] for s in result.unread] == ["If we", "for"]
    # Whichever is pressed first, the three together are the search that was typed.
    for order in ((0, 1, 2), (2, 1, 0), (1, 2, 0)):
        spec = RENTER
        for at in order:
            pressed = apply(spec, result.suggestions[at].choices[0].operations, small_release())
            assert pressed.rejected == ()
            spec = pressed.spec
        assert (spec.tenure, spec.budget.amount, spec.budget.segment) == ("buy", 425_000, "flat")
        # "Up to" is the most that can be paid, whichever is pressed last.
        assert spec.budget.strictness == "hard"


@pytest.mark.parametrize(
    ("text", "spec", "label", "choice", "note"),
    [
        # A renter's home is held by its bedrooms, whatever kind it is.
        ("maybe a two bed house", RENTER, "A 2-bedroom home", "Set a 2-bedroom home", ""),
        ("perhaps 3 bedrooms", RENTER, "A 3-bedroom home", "Set a 3-bedroom home", ""),
        ("maybe a studio", RENTER, "A studio", "Set a studio", ""),
        ("maybe a room in a flatshare", RENTER, "A room in a shared home", None, ""),
        (
            "a 3 bed semi to rent, maybe",
            RENTER,
            "A 3-bedroom home",
            "Set a 3-bedroom home",
            BY_BEDROOMS,
        ),
        # It is offered whether or not it moves what the search holds.
        ("I guess a one bed flat", RENTER, "A 1-bedroom home", "Set a 1-bedroom home", ""),
        ("I guess a flat", BUYER, "A flat", "Set a flat", ""),
        # A buyer's home is held by its kind.
        ("perhaps a terraced house", BUYER, "A terraced house", "Set a terraced house", ""),
        (
            "maybe a 3 bed semi",
            BUYER,
            "A semi-detached house",
            "Set a semi-detached house",
            BY_KIND,
        ),
        # The words say which tenure the home is for, and the choice says it too.
        (
            "thinking of buying a 2 bed flat",
            RENTER,
            "A flat",
            "Set a flat, to buy",
            BY_KIND,
        ),
        (
            "I might rent a two bed flat",
            BUYER,
            "A 2-bedroom home",
            "Set a 2-bedroom home, to rent",
            "",
        ),
        (
            "maybe a studio for £1,100 a month",
            BUYER,
            "A studio",
            "Set a studio, to rent",
            "",
        ),
        # Nobody has chosen to rent, and the kind is one that Burro holds for buying alone.
        (
            "perhaps a detached house",
            RENTER,
            "A detached house",
            "Set a detached house, to buy",
            BY_BEDROOMS,
        ),
    ],
)
def test_a_size_and_a_kind_of_home_are_offered_whenever_they_are_named(
    text: str, spec: PreferenceSpec, label: str, choice: str | None, note: str
):
    result = read(text, spec)
    assert result.operations == NO_OPERATIONS
    if choice is None:
        # A room is what the words say, and the offer is a room.
        choice = "Set a room in a shared home"
    assert homes(result) == [(label, [choice, "Leave it out"], note)]
    (found,) = (f for f in result.suggestions if f.label == label)
    pressed = apply(spec, found.choices[0].operations, small_release())
    assert pressed.rejected == ()
    # What it rests on is not called unread.
    spans = [(span.start, span.end) for span in found.spans]
    assert not [
        unread
        for unread in result.unread
        if any(start < unread.end and unread.start < end for start, end in spans)
    ]


@pytest.mark.parametrize(
    ("text", "spec", "label", "note"),
    [
        # The person has chosen to buy, in words or with the control, and Burro
        # holds no bedrooms for a home to buy. Nothing can be set, and it says so.
        ("thinking of buying a two bed house", RENTER, "A 2-bedroom home", BY_KIND),
        ("maybe a two bed house", BUYER, "A 2-bedroom home", BY_KIND),
        ("maybe a studio", BUYER, "A studio", TO_RENT_ALONE),
        # And no kind of home for one to rent.
        ("I might rent a terraced house", RENTER, "A terraced house", BY_BEDROOMS),
    ],
)
def test_a_home_the_search_cannot_hold_is_said_to_be_heard_and_offers_nothing_to_set(
    text: str, spec: PreferenceSpec, label: str, note: str
):
    result = read(text, spec)
    assert result.operations == NO_OPERATIONS
    assert homes(result) == [(label, ["Leave it out"], note)]
    # Nobody is moved to the other tenure for having named a home.
    (home,) = (found for found in result.suggestions if found.label == label)
    assert [choice.operations for choice in home.choices] == [NO_OPERATIONS]


@pytest.mark.parametrize(
    ("text", "spec"),
    [
        ("a two bed house", BUYER),
        ("two bedrooms", BUYER),
        ("studio", BUYER),
        ("a terraced house", RENTER),
    ],
)
def test_a_plain_home_of_which_no_edit_can_be_made_is_said_to_be_unread(
    text: str, spec: PreferenceSpec
):
    # Each was answered with no edit, no offer and nothing unread: nothing at all.
    result = read(text, spec)
    assert result.operations == NO_OPERATIONS
    assert [text[span.start : span.end] for span in result.unread] == [text]
    assert result.unmet == (UnmetCategory.OTHER,)
    # The status of a plain prompt does not say whether the search is to rent or to buy.
    other = BUYER if spec is RENTER else RENTER
    assert result.status is read(text, other).status is InterpretStatus.OK


def test_the_rest_of_a_plain_prompt_is_applied_beside_a_home_that_cannot_be_held():
    text = "leafy, a two bed house"
    result = read(text, BUYER)
    assert [edit.tag_id for edit in result.operations.tag_ops] == ["leafy"]
    assert result.operations.count == 1
    assert [text[span.start : span.end] for span in result.unread] == ["a two bed house"]
    assert (result.status, result.unmet) == (InterpretStatus.OK, (UnmetCategory.OTHER,))


@pytest.mark.parametrize(
    ("text", "spec", "segment"),
    [
        ("a two bed house", RENTER, "bed_2"),
        ("studio", RENTER, "studio"),
        ("a terraced house", BUYER, "terraced"),
        ("max £350k for a 1 bed flat", RENTER, "flat"),
        ("a 2 bed flat to rent", BUYER, "bed_2"),
    ],
)
def test_a_plain_home_the_search_can_hold_is_still_applied(
    text: str, spec: PreferenceSpec, segment: str
):
    result = read(text, spec)
    (edit,) = result.operations.budget_ops
    assert edit.segment == segment
    assert (result.status, result.suggestions) == (InterpretStatus.OK, ())
    assert apply(spec, result.operations, small_release()).rejected == ()


@pytest.mark.parametrize(
    "text", ["never a studio", "not a two bed", "I don't want a flat", "no terraced houses"]
)
def test_a_home_that_is_turned_away_is_not_offered(text: str):
    for spec in (RENTER, BUYER):
        assert homes(read(text, spec)) == []


# --- A smart area -------------------------------------------------------------------------

PLACES_NOT_PEOPLE = "Burro reads this of the place, and not of the people who live there."
COUNTS_CRIME = (
    "Gritty counts recorded criminal damage and arson, and recorded anti-social behaviour. "
    "Recorded crime depends on what is reported, and locations are approximate."
)
TOWARDS_POLISHED = "Towards Polished, counting recorded crime"
TOWARDS_GRITTY = "Towards Gritty, counting recorded crime"
LEAVE = "Leave it out"
# The first reading of a word for a smart area: the chains of grocers, gyms and coffee
# within reach, towards premium. The third: homes that sell for more than the middle.
MIX = "feature:brand_mix"
MORE_PREMIUM, LESS_PREMIUM = "More premium", "Less premium"
PRICE = "feature:price_median"
DEARER, CHEAPER = "Dearer", "Cheaper"
# The third: homes in the higher council tax bands. It counts homes, and never people.
BANDS = "feature:homes_higher_bands"
MORE_IN_BANDS = "More homes in the higher council tax bands"
FEWER_IN_BANDS = "Fewer homes in the higher council tax bands"


@pytest.mark.parametrize(
    ("text", "words", "unread"),
    [
        ("affluent", "affluent", []),
        ("slightly affluent", "slightly affluent", []),
        ("somewhere posh", "posh", ["somewhere"]),
        ("a well-heeled area", "a well-heeled area", []),
        ("fairly well heeled", "fairly well heeled", []),
        ("upmarket", "upmarket", []),
        ("a smart neighbourhood", "a smart neighbourhood", []),
        ("I want somewhere affluent", "affluent", ["I want somewhere"]),
        ("Maybe leafy. Somewhere affluent.", "affluent", ["Maybe", "Somewhere"]),
    ],
)
def test_a_word_for_a_smart_area_is_offered_as_of_the_place_and_never_applied(
    text: str, words: str, unread: list[str]
):
    result = read(text)
    assert (result.operations, result.notice) == (NO_OPERATIONS, "none")
    assert result.status is InterpretStatus.SUGGEST
    (found,) = (f for f in result.suggestions if f.target == "tag:street_character")
    assert found.label == "Gritty"
    # It says that it is of the place, and what the scale counts.
    assert found.note == f"{PLACES_NOT_PEOPLE} {COUNTS_CRIME}"
    assert [(c.direction, c.label) for c in found.choices] == [
        ("less", TOWARDS_POLISHED),
        ("ignore", LEAVE),
    ]
    assert [text[s.start : s.end] for s in found.spans] == [words]
    assert [text[s.start : s.end] for s in result.unread] == unread
    # To press it is to ask for the scale by name, so it is applied.
    pressed = apply(RENTER, found.choices[0].operations, small_release())
    assert pressed.rejected == ()
    assert [(t.tag_id, t.toward, t.provenance) for t in pressed.spec.tags] == [
        ("street_character", "low", "ui_edit")
    ]
    # It weighs the one scale, and no measure that was not weighed before.
    assert {w.feature_id for w in pressed.spec.weights} == {w.feature_id for w in RENTER.weights}


@pytest.mark.parametrize(
    "text",
    [
        *("affluent", "slightly affluent", "somewhere posh", "a well-heeled area"),
        *("upmarket", "a smart neighbourhood", "I want somewhere affluent"),
    ],
)
def test_a_word_for_a_smart_area_has_four_readings_and_the_mix_of_brands_is_the_first(
    text: str,
):
    """Decided on 2026-09-24: readings of the place, and the person chooses.

    None is what people earn, and none is who lives somewhere. The first is which
    chains stand within reach, and it is offered one way: more premium.
    """
    result = read(text)
    assert (result.operations, result.notice) == (NO_OPERATIONS, "none")
    offered = [found.target for found in result.suggestions]
    assert offered == [MIX, "tag:street_character", PRICE, BANDS]
    mix, polished, _, _ = result.suggestions
    assert (mix.label, mix.note) == ("Mix of brands", PLACES_NOT_PEOPLE)
    assert [(c.direction, c.label) for c in mix.choices] == [
        ("more", MORE_PREMIUM),
        ("ignore", LEAVE),
    ]
    assert mix.spans == polished.spans
    # To press it weighs the one measure, towards premium, and no vibe.
    pressed = apply(RENTER, mix.choices[0].operations, small_release())
    assert pressed.rejected == ()
    asked = [w for w in pressed.spec.weights if w.provenance is not Provenance.DEFAULT]
    assert [(w.feature_id, w.direction, w.provenance) for w in asked] == [
        ("brand_mix", "more", "ui_edit")
    ]
    assert pressed.spec.tags == ()


@pytest.mark.parametrize(
    "text",
    [
        *("affluent", "slightly affluent", "somewhere posh", "a well-heeled area"),
        *("upmarket", "a smart neighbourhood", "I want somewhere affluent"),
    ],
)
def test_a_word_for_a_smart_area_has_a_reading_which_is_what_homes_sell_for(text: str):
    """Decided on 2026-09-24: a reading of the place, and the person chooses.

    It is the middle price that homes sold for, and it is offered one way: dearer.
    """
    result = read(text)
    assert (result.operations, result.notice) == (NO_OPERATIONS, "none")
    _, polished, price, _ = result.suggestions
    assert price.label == "What homes sell for"
    assert price.note == PLACES_NOT_PEOPLE
    assert [(c.direction, c.label) for c in price.choices] == [("more", DEARER), ("ignore", LEAVE)]
    assert price.spans == polished.spans
    # To press it weighs the one measure, towards dearer, and no vibe.
    pressed = apply(RENTER, price.choices[0].operations, small_release())
    assert pressed.rejected == ()
    asked = [w for w in pressed.spec.weights if w.provenance is not Provenance.DEFAULT]
    assert [(w.feature_id, w.direction, w.provenance) for w in asked] == [
        ("price_median", "more", "ui_edit")
    ]
    assert pressed.spec.tags == ()
    # Both may be pressed, and each is then weighed as any wish is.
    both = apply(pressed.spec, polished.choices[0].operations, small_release())
    assert both.rejected == ()
    assert [t.tag_id for t in both.spec.tags] == ["street_character"]


@pytest.mark.parametrize(
    "text",
    [
        *("affluent", "slightly affluent", "somewhere posh", "a well-heeled area"),
        *("upmarket", "a smart neighbourhood", "I want somewhere affluent"),
    ],
)
def test_a_word_for_a_smart_area_has_a_third_reading_which_counts_homes_and_not_people(text: str):
    """The homes of a place by their council tax band: the share in the higher bands.

    It is a figure of the homes that stand in a place. It is offered one way,
    beside what homes sell for, with the same note, and no word applies it.
    """
    result = read(text)
    _, polished, price, bands = result.suggestions
    assert (bands.target, bands.label) == (BANDS, "Homes in the higher council tax bands")
    assert bands.note == PLACES_NOT_PEOPLE == price.note
    assert [(c.direction, c.label) for c in bands.choices] == [
        ("more", MORE_IN_BANDS),
        ("ignore", LEAVE),
    ]
    assert bands.spans == price.spans == polished.spans
    # To press it weighs the one measure, towards more, and no vibe and no price.
    pressed = apply(RENTER, bands.choices[0].operations, small_release())
    assert pressed.rejected == ()
    asked = [w for w in pressed.spec.weights if w.provenance is not Provenance.DEFAULT]
    assert [(w.feature_id, w.direction, w.provenance) for w in asked] == [
        ("homes_higher_bands", "more", "ui_edit")
    ]
    assert pressed.spec.tags == ()
    assert "homes_higher_bands" not in {e.feature_id for e in result.operations.weight_ops}
    for tenure in Tenure:
        assert "homes_higher_bands" not in {w.feature_id for w in default_spec(tenure).weights}


def test_what_homes_sell_for_is_never_weighed_by_a_word_alone():
    """It is offered, and a person presses it. No sentence applies it, however plain."""
    for text in ("affluent", "posh, leafy and quiet", "upmarket and near a park"):
        result = read(text)
        assert "price_median" not in {e.feature_id for e in result.operations.weight_ops}
        assert PRICE in [found.target for found in result.suggestions]
    assert "price_median" not in {w.feature_id for w in RENTER.weights}
    assert "price_median" not in {w.feature_id for w in default_spec(Tenure.BUY).weights}


def test_the_mix_of_brands_is_never_weighed_by_a_word_alone():
    """It is offered, and a person presses it. Nothing weighs it by default."""
    for text in ("affluent", "posh, leafy and quiet", "down to earth and near a park"):
        result = read(text)
        assert "brand_mix" not in {e.feature_id for e in result.operations.weight_ops}
        assert MIX in [found.target for found in result.suggestions]
    for tenure in Tenure:
        assert "brand_mix" not in {w.feature_id for w in default_spec(tenure).weights}
    assert not any(term.feature_id == "brand_mix" for tag in TAGS.values() for term in tag.terms)
    assert not FEATURES[FeatureId.BRAND_MIX].in_likeness


@pytest.mark.parametrize(
    ("text", "words", "unread"),
    [
        ("cheap and cheerful", "cheap and cheerful", []),
        ("unpretentious", "unpretentious", []),
        ("down to earth", "down to earth", []),
        ("somewhere down to earth", "down to earth", ["somewhere"]),
        ("fairly unpretentious", "fairly unpretentious", []),
        ("Leafy. Cheap and cheerful.", "Cheap and cheerful", []),
    ],
)
def test_a_word_for_a_plain_area_is_offered_as_the_other_end_of_the_mix_and_nothing_else(
    text: str, words: str, unread: list[str]
):
    """It is of the place: which chains stand there. It is no wish for recorded crime.

    So it is not offered Gritty, which counts recorded crime, and it is not offered
    cheaper homes: what is cheap is a verdict Burro does not give.
    """
    result = read(text)
    assert result.notice == "none"
    assert "brand_mix" not in {e.feature_id for e in result.operations.weight_ops}
    (mix,) = (found for found in result.suggestions if found.target == MIX)
    assert {found.target for found in result.suggestions} <= {MIX, "tag:leafy"}
    assert (mix.label, mix.note) == ("Mix of brands", PLACES_NOT_PEOPLE)
    assert [(c.direction, c.label) for c in mix.choices] == [
        ("less", LESS_PREMIUM),
        ("ignore", LEAVE),
    ]
    assert [text[s.start : s.end] for s in mix.spans] == [words]
    assert [text[s.start : s.end] for s in result.unread] == unread
    assert UnmetCategory.AFFORDABILITY_VERDICT not in result.unmet
    pressed = apply(RENTER, mix.choices[0].operations, small_release())
    assert pressed.rejected == ()
    asked = [w for w in pressed.spec.weights if w.provenance is not Provenance.DEFAULT]
    assert [(w.feature_id, w.direction, w.provenance) for w in asked] == [
        ("brand_mix", "less", "ui_edit")
    ]
    assert pressed.spec.tags == ()


@pytest.mark.parametrize(
    "text", ["not unpretentious", "anything but down to earth", "is it cheap and cheerful"]
)
def test_a_plain_area_is_offered_with_both_ends_wherever_the_way_it_is_meant_is_not_plain(
    text: str,
):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    (mix,) = result.suggestions
    assert [choice.label for choice in mix.choices] == [MORE_PREMIUM, LESS_PREMIUM, LEAVE]


@pytest.mark.parametrize(
    "text",
    [
        *("unpretentious people", "down to earth locals", "a down to earth crowd"),
        *("cheap and cheerful families", "unpretentious neighbours"),
    ],
)
def test_a_word_for_a_plain_area_said_of_people_is_a_request_about_them(text: str):
    for variant in GrittyVariant:
        result = read(text, variant=variant)
        assert (result.operations, result.suggestions) == (NO_OPERATIONS, ())
        assert (result.status, result.notice) == (
            InterpretStatus.POLICY_REDIRECT,
            "neutral_places",
        )


@pytest.mark.parametrize(
    "text",
    [
        # Under a word that turns.
        *("not posh", "not too affluent", "nowhere upmarket", "less smart", "I hate posh areas"),
        # And wherever the grammar does not make the sentence, since nobody can
        # say there which way the word is meant.
        *("anything but posh", "posh is not for me", "affluent, which I can do without"),
        *("is it posh", "my sister says it is upmarket"),
    ],
)
def test_a_smart_area_is_offered_with_both_ends_wherever_the_way_it_is_meant_is_not_plain(
    text: str,
):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    mix, found, price, bands = result.suggestions
    assert [choice.label for choice in found.choices] == [TOWARDS_GRITTY, TOWARDS_POLISHED, LEAVE]
    assert found.note == f"{PLACES_NOT_PEOPLE} {COUNTS_CRIME}"
    # So are the mix of brands and what homes sell for: nobody can say there which way
    # the word is meant.
    assert mix.target == MIX and mix.note == PLACES_NOT_PEOPLE
    assert [choice.label for choice in mix.choices] == [MORE_PREMIUM, LESS_PREMIUM, LEAVE]
    assert price.target == PRICE and price.note == PLACES_NOT_PEOPLE
    # And so are the bands the homes are in.
    assert bands.target == BANDS and bands.note == PLACES_NOT_PEOPLE
    assert [choice.label for choice in bands.choices] == [MORE_IN_BANDS, FEWER_IN_BANDS, LEAVE]
    assert [choice.label for choice in price.choices] == [DEARER, CHEAPER, LEAVE]


def test_a_thing_named_twice_is_offered_once_with_every_way_it_may_be_chosen():
    mix, found, price, bands = read("somewhere posh but not too posh").suggestions
    assert [choice.label for choice in found.choices] == [TOWARDS_GRITTY, TOWARDS_POLISHED, LEAVE]
    assert len(found.spans) == 2
    assert [choice.label for choice in mix.choices] == [MORE_PREMIUM, LESS_PREMIUM, LEAVE]
    assert [choice.label for choice in price.choices] == [DEARER, CHEAPER, LEAVE]
    assert len(price.spans) == len(mix.spans) == 2
    assert [choice.label for choice in bands.choices] == [MORE_IN_BANDS, FEWER_IN_BANDS, LEAVE]
    assert len(bands.spans) == 2
    # And with all that is said of either word, whichever stands first.
    for text in ("not rough, not posh, I think", "not posh, not rough, I think"):
        offered = {one.target: one for one in read(text).suggestions}
        assert set(offered) == {MIX, "tag:street_character", PRICE, BANDS}
        found = offered["tag:street_character"]
        assert found.note == f"{PLACES_NOT_PEOPLE} {COUNTS_CRIME}"
        assert len(found.choices) == 3


@pytest.mark.parametrize(
    "text",
    [
        *("posh people", "affluent residents", "rich people", "wealthy neighbours"),
        *("affluent people", "well heeled families", "upmarket people", "affluent families"),
        *("no posh neighbours", "somewhere with affluent people"),
    ],
)
def test_a_word_for_who_lives_somewhere_is_still_heard_as_one(text: str):
    result = read(text)
    assert (result.operations, result.suggestions) == (NO_OPERATIONS, ())
    assert (result.status, result.notice) == (InterpretStatus.POLICY_REDIRECT, "neutral_places")


@pytest.mark.parametrize(
    "text",
    [
        # A word for a smart area or a rough one, said of people by any word for them.
        *("posh folk", "posh locals", "posh types", "an affluent crowd", "upmarket clientele"),
        *("affluent households", "affluent homeowners", "affluent commuters"),
        *("an affluent community", "somewhere with well heeled locals", "no posh kids"),
        *("rough people", "rough types", "a rough crowd", "rough families", "no rough sleepers"),
        # The character of a people is theirs, and no character of a place.
        *("somewhere with a Black identity", "a Polish character", "a strong Irish character"),
        *("an area with a Somali soul", "a Turkish identity", "somewhere with an Asian character"),
        *("LGBT identity", "working class identity", "a studenty character"),
        *("a strong Jewish identity", "a Muslim character", "a student soul"),
    ],
)
def test_a_smart_word_or_a_word_for_character_said_of_people_is_a_request_about_them(text: str):
    # "A Polish character" was offered a village feel, historic and a high street,
    # resting on the word for the people, and with no notice that Burro ranks places.
    for variant in GrittyVariant:
        result = read(text, variant=variant)
        assert (result.operations, result.suggestions) == (NO_OPERATIONS, ())
        assert (result.status, result.notice) == (
            InterpretStatus.POLICY_REDIRECT,
            "neutral_places",
        )


@pytest.mark.parametrize(
    ("text", "offered"),
    [
        # Said of the place, or of what stands in it, each is still of the place.
        ("a posh area", [MIX, "tag:street_character", PRICE, BANDS]),
        ("posh shops", [MIX, "tag:street_character", PRICE, BANDS, "feature:highstreet_access"]),
        ("a rough estate", ["tag:street_character"]),
        ("rough pubs", ["tag:street_character", "feature:venue_evening_per_homes"]),
        ("a strong local identity", ["tag:village_feel", "tag:built_age", *HIGH_STREET]),
        ("a village character", ["tag:village_feel", "tag:built_age", *HIGH_STREET]),
    ],
)
def test_a_smart_word_or_a_word_for_character_said_of_a_place_is_still_offered(
    text: str, offered: list[str]
):
    result = read(text)
    assert (result.notice, result.operations) == ("none", NO_OPERATIONS)
    assert [found.target for found in result.suggestions] == offered


def test_a_cuisine_that_holds_a_word_for_character_asks_nothing_about_people():
    result = read("Caribbean soul food nearby")
    assert (result.notice, result.operations) == ("none", NO_OPERATIONS)


@pytest.mark.parametrize("text", ["affluent", "posh", "upmarket", "well heeled"])
def test_where_no_recorded_crime_is_held_a_word_for_a_smart_area_is_read_as_of_its_shops_and_homes(
    text: str,
):
    # The scale is not in such a release. The mix of brands is, and what homes sell for, and
    # the bands they are in.
    result = read(text, variant=GrittyVariant.A)
    assert result.operations == NO_OPERATIONS
    mix, price, bands = result.suggestions
    assert (mix.target, mix.note) == (MIX, PLACES_NOT_PEOPLE)
    assert [choice.label for choice in mix.choices] == [MORE_PREMIUM, LEAVE]
    assert (price.target, price.note) == (PRICE, PLACES_NOT_PEOPLE)
    assert [choice.label for choice in price.choices] == [DEARER, LEAVE]
    assert (bands.target, bands.note) == (BANDS, PLACES_NOT_PEOPLE)
    assert [choice.label for choice in bands.choices] == [MORE_IN_BANDS, LEAVE]


# --- A chain that a person names -----------------------------------------------------------

OF_A_CHAIN = (
    "Burro finds a chain by the brand its file of places gives a shop. "
    "The file misses some shops, and lists some that have closed."
)


@pytest.mark.parametrize(
    ("text", "target", "label", "words"),
    [
        ("near a Waitrose", "brand_waitrose", "Nearer a Waitrose", "near a Waitrose"),
        ("a Gail's nearby", "brand_gails", "Nearer a Gail's", "a Gail's nearby"),
        ("near an M&S", "brand_mands", "Nearer an M&S", "near an M&S"),
        ("marks and spencer", "brand_mands", "Nearer an M&S", "marks and spencer"),
        ("close to a Sainsbury\N{RIGHT SINGLE QUOTATION MARK}s", "brand_sainsburys", None, None),
        ("tesco", "brand_tesco", "Nearer a Tesco", "tesco"),
        ("a co-op on my doorstep", "brand_coop", "Nearer a Co-op", "a co-op on my doorstep"),
        ("near an Aldi", "brand_aldi", "Nearer an Aldi", "near an Aldi"),
        ("pret a manger", "brand_pret", "Nearer a Pret", "pret a manger"),
        ("caffè nero", "brand_nero", "Nearer a Nero", "caffè nero"),
        ("near a PureGym", "brand_puregym", "Nearer a PureGym", "near a PureGym"),
        ("the gym group", "brand_the_gym_group", "Nearer The Gym Group", None),
        ("I want a Third Space nearby", "brand_third_space", "Nearer a Third Space", None),
        ("ole & steen", "brand_ole_and_steen", "Nearer an Ole & Steen", "ole & steen"),
    ],
)
def test_a_chain_a_person_names_is_offered_as_the_distance_to_the_nearest_place_of_it(
    text: str, target: str, label: str | None, words: str | None
):
    """It is offered, one way, and never applied: a person presses it."""
    result = read(text)
    assert (result.operations, result.notice) == (NO_OPERATIONS, "none")
    assert result.status is InterpretStatus.SUGGEST
    (found,) = result.suggestions
    assert found.target == f"feature:{target}" and found.note == OF_A_CHAIN
    assert label is None or found.label == label
    assert [(c.direction, c.label) for c in found.choices] == [
        ("more", found.label),
        ("ignore", LEAVE),
    ]
    assert words is None or [text[s.start : s.end] for s in found.spans] == [words]
    pressed = apply(RENTER, found.choices[0].operations, small_release())
    assert pressed.rejected == ()
    asked = [w for w in pressed.spec.weights if w.provenance is not Provenance.DEFAULT]
    assert [(w.feature_id, w.direction, w.provenance) for w in asked] == [
        (target, "less", "ui_edit")
    ]


def test_every_chain_core_names_is_heard_by_its_name():
    for feature_id, chain in CHAINS.items():
        for text in (chain.name, f"near {chain.one}", f"{chain.one} nearby"):
            result = read(text)
            assert result.operations == NO_OPERATIONS, text
            assert [found.target for found in result.suggestions] == [f"feature:{feature_id}"]


def test_a_chain_is_offered_beside_what_else_was_said_and_nothing_is_applied():
    result = read("leafy, quiet and near a Waitrose")
    assert result.operations == NO_OPERATIONS
    assert [found.target for found in result.suggestions] == [
        "tag:leafy",
        "tag:quiet_residential",
        "feature:brand_waitrose",
    ]


@pytest.mark.parametrize("text", ["no Greggs", "not near a Tesco", "anything but a Costa"])
def test_a_chain_that_is_turned_away_is_never_weighed_and_cannot_be_asked_to_be_far(text: str):
    """A person may ask to be near a chain. No edit says far from one."""
    result = read(text)
    assert result.operations == NO_OPERATIONS
    (found,) = result.suggestions
    assert [c.direction for c in found.choices] == ["more", "ignore"]
    for choice in found.choices:
        for edit in choice.operations.weight_ops:
            assert edit.direction != "more"
            assert not direction_allowed(edit.feature_id, Direction.MORE)


def test_a_chain_the_release_holds_no_place_of_is_said_to_be_missing_and_is_not_offered():
    """As the first build of London holds no place of two chains of the founder's table."""
    carried = tuple(
        metric
        for metric in small_release().metrics
        if metric.feature_id is not FeatureId.BRAND_THIRD_SPACE
    )
    rows = tuple(
        row for row in small_release().features if row.feature_id is not FeatureId.BRAND_THIRD_SPACE
    )
    without = dataclasses.replace(small_release(), metrics=carried, features=rows)
    request = InterpretRequest(text="near a Third Space", spec=RENTER, release=without)
    result = RuleInterpreter().interpret(request)
    assert (result.operations, result.suggestions) == (NO_OPERATIONS, ())
    assert [(one.target, one.label) for one in result.not_in_release] == [
        ("feature:brand_third_space", "Nearer a Third Space")
    ]


# --- A rough area, and one that is up and coming -------------------------------------------

A_RISE_PROMISES_NOTHING = (
    "Burro cannot see where a place is heading. It can count how far what homes sold for "
    "has risen. A rise is of prices that were paid, and promises nothing."
)
A_RISE_OR_THE_SCALE = (
    "Burro cannot see where a place is heading. It can count how far what homes sold for "
    "has risen, and say where a place stands on Gritty today. A rise is of prices that were "
    "paid, and promises nothing."
)
RISES = ["feature:price_rise_5y", "feature:price_rise_10y"]
STEEPER, SMALLER = "A steeper rise", "A smaller rise"


@pytest.mark.parametrize("text", ["rough", "a bit rough"])
def test_a_rough_area_is_offered_as_the_ends_of_the_scale(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    (found,) = result.suggestions
    assert (found.target, found.note) == ("tag:street_character", COUNTS_CRIME)
    assert [choice.label for choice in found.choices] == [TOWARDS_GRITTY, TOWARDS_POLISHED, LEAVE]
    assert (result.unmet, result.unread) == ((), ())


@pytest.mark.parametrize("text", ["up and coming", "an up-and-coming area"])
def test_a_place_that_is_up_and_coming_is_offered_as_a_rise_in_prices_and_as_the_scale(text: str):
    """It was offered as the scale alone, with both its ends, before a rise was held.

    It still is, and nobody can say which end is meant. Beside it stands how
    far what homes sold for has risen, over five years and over ten.
    """
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert [found.target for found in result.suggestions] == [*RISES, "tag:street_character"]
    five, ten, scale = result.suggestions
    assert (five.label, ten.label) == ("Price rise over five years", "Price rise over ten years")
    assert five.note == ten.note == A_RISE_OR_THE_SCALE
    assert scale.note == f"{A_RISE_OR_THE_SCALE} {COUNTS_CRIME}"
    assert [choice.label for choice in scale.choices] == [TOWARDS_GRITTY, TOWARDS_POLISHED, LEAVE]
    for rise in (five, ten):
        assert [choice.label for choice in rise.choices] == [STEEPER, SMALLER, LEAVE]
    # Burro has a measure of it now, so nothing of it is said to be left out.
    assert (result.unmet, result.unread) == ((), ())


@pytest.mark.parametrize(
    ("text", "words"),
    [
        ("on the up", "on the up"),
        ("somewhere on the up", "on the up"),
        ("rising", "rising"),
        ("rising prices", "rising prices"),
    ],
)
def test_a_place_on_the_rise_is_offered_as_how_far_what_homes_sold_for_has_risen(
    text: str, words: str
):
    """Decided on 2026-09-24. It is offered one way, and no word applies it."""
    for variant in GrittyVariant:
        result = read(text, variant=variant)
        assert (result.operations, result.notice) == (NO_OPERATIONS, "none")
        assert [found.target for found in result.suggestions] == RISES
        for rise in result.suggestions:
            assert rise.note == A_RISE_PROMISES_NOTHING
            assert [(c.direction, c.label) for c in rise.choices] == [
                ("more", STEEPER),
                ("ignore", LEAVE),
            ]
            assert [text[s.start : s.end] for s in rise.spans] == [words]
        assert UnmetCategory.CHANGE_OVER_TIME not in result.unmet


@pytest.mark.parametrize("text", ["where prices are rising", "not on the up", "is it rising"])
def test_a_rise_is_offered_both_ways_wherever_the_way_it_is_meant_is_not_plain(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert [found.target for found in result.suggestions] == RISES
    for rise in result.suggestions:
        assert [choice.label for choice in rise.choices] == [STEEPER, SMALLER, LEAVE]
        assert rise.note == A_RISE_PROMISES_NOTHING


def test_where_no_recorded_crime_is_held_up_and_coming_is_a_rise_in_prices_alone():
    result = read("up and coming", variant=GrittyVariant.A)
    assert [found.target for found in result.suggestions] == RISES
    assert {rise.note for rise in result.suggestions} == {A_RISE_PROMISES_NOTHING}
    assert result.unmet == ()


def test_to_press_a_rise_weighs_the_one_measure_and_nothing_else():
    five, _ = read("on the up").suggestions
    pressed = apply(RENTER, five.choices[0].operations, small_release())
    assert pressed.rejected == ()
    asked = [w for w in pressed.spec.weights if w.provenance is not Provenance.DEFAULT]
    assert [(w.feature_id, w.direction, w.provenance) for w in asked] == [
        ("price_rise_5y", "more", "ui_edit")
    ]
    assert pressed.spec.tags == ()
    for tenure in Tenure:
        held = {w.feature_id for w in default_spec(tenure).weights}
        assert not held & {"price_rise_5y", "price_rise_10y"}


def test_a_word_for_who_is_moving_in_is_still_no_measure():
    """A rise is of prices that were paid. Who moves to a place is of people."""
    for text in ("gentrifying", "gentrification"):
        result = read(text)
        assert (result.operations, result.suggestions) == (NO_OPERATIONS, ())
        assert result.unmet == (UnmetCategory.CHANGE_OVER_TIME,)


@pytest.mark.parametrize(
    ("text", "unmet"),
    [
        ("rising damp", UnmetCategory.UPKEEP),
        ("no rising damp", UnmetCategory.UPKEEP),
        ("rising crime", UnmetCategory.CHANGE_OVER_TIME),
        ("rising rents", UnmetCategory.CHANGE_OVER_TIME),
    ],
)
def test_something_else_that_is_rising_is_not_read_as_a_rise_in_prices(
    text: str, unmet: UnmetCategory
):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert not [found for found in result.suggestions if found.target in RISES]
    assert unmet in result.unmet


def test_gritty_is_a_request_for_the_scale_by_name_and_is_applied_where_the_prompt_is_plain():
    for text, toward in (("gritty", "high"), ("somewhere gritty", "high"), ("polished", "low")):
        result = read(text)
        (edit,) = result.operations.tag_ops
        assert (edit.tag_id, edit.toward, edit.provenance) == ("street_character", toward, "stated")
        assert apply(RENTER, result.operations, small_release()).rejected == ()
    # Where it is not plain it is offered, and the choice says what it counts.
    (found,) = read("gritty, I suppose").suggestions
    assert [choice.label for choice in found.choices] == [TOWARDS_GRITTY, TOWARDS_POLISHED, LEAVE]
    assert found.note == COUNTS_CRIME


# --- A place with character ----------------------------------------------------------------

NO_IDENTITY = (
    "Burro cannot measure the character of a place. The nearest it can count are a village "
    "feel, the age of the buildings and a town centre nearby. Choose any that fit what you mean."
)
THREE = [
    ("tag:village_feel", ["Add Village feel", LEAVE]),
    ("tag:built_age", ["Towards Historic", LEAVE]),
    ("feature:highstreet_access", ["Nearer a town centre", LEAVE]),
]


@pytest.mark.parametrize(
    "text",
    [
        *("somewhere with an identity of its own", "a real identity", "its own identity"),
        *("character", "a bit of character", "lots of character", "characterful"),
        *("a place with its own feel", "a proper neighbourhood", "somewhere with soul"),
        # A place without it is turned away, which is no wish for its opposite.
        *("soulless", "bland", "nowhere soulless", "not bland", "I hate bland suburbs"),
        *("no character", "I don't care about character", "character is essential"),
    ],
)
@pytest.mark.parametrize("spec", [RENTER, BUYER], ids=["renter", "buyer"])
def test_a_word_for_character_is_offered_three_ways_and_never_applied(
    text: str, spec: PreferenceSpec
):
    result = read(text, spec)
    assert (result.operations, result.notice) == (NO_OPERATIONS, "none")
    assert offers(result) == THREE
    assert {found.note for found in result.suggestions} == {NO_IDENTITY}
    for found in result.suggestions:
        pressed = apply(spec, found.choices[0].operations, small_release())
        assert pressed.rejected == () and pressed.spec != spec
    # The three rest on the same words, which are not called unread.
    (words,) = {tuple(r) for r in rested(text, result)}
    assert not [s for s in result.unread if text[s.start : s.end] in words]


def test_one_of_the_three_that_is_named_beside_the_word_is_applied_and_the_rest_offered():
    # "Historic, with lots of character": the first is a wish of its own.
    result = read("historic, with lots of character")
    assert result.operations == NO_OPERATIONS
    assert [found.target for found in result.suggestions] == [
        "tag:built_age",
        "tag:village_feel",
        "feature:highstreet_access",
    ]


# --- The names of the scales -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "tag_id", "ends"),
    [
        ("going out", "pace", ["Towards Buzzy", "Towards Calm"]),
        ("pace", "pace", ["Towards Buzzy", "Towards Calm"]),
        ("age of buildings", "built_age", ["Towards Historic", "Towards Newer"]),
        ("the age of the buildings", "built_age", ["Towards Historic", "Towards Newer"]),
        ("built age", "built_age", ["Towards Historic", "Towards Newer"]),
        ("houses or flats", "homes", ["Towards Flats", "Towards Houses"]),
        ("I care about going out", "pace", ["Towards Buzzy", "Towards Calm"]),
    ],
)
def test_a_scale_answers_to_its_new_name_and_to_its_old_and_neither_names_an_end(
    text: str, tag_id: str, ends: list[str]
):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    (found,) = result.suggestions
    assert found.target == f"tag:{tag_id}"
    assert [choice.label for choice in found.choices] == [*ends, LEAVE]


@pytest.mark.parametrize(
    ("text", "tag_id", "toward"),
    [
        ("buzzy", "pace", "high"),
        ("calm", "pace", "low"),
        ("lively", "pace", "high"),
        ("nightlife", "pace", "high"),
        ("historic", "built_age", "high"),
        ("period", "built_age", "high"),
        ("new build", "built_age", "low"),
        ("suburban", "homes", "low"),
        ("city living", "homes", "high"),
    ],
)
def test_the_words_people_type_for_an_end_of_a_scale_are_still_wishes_for_it(
    text: str, tag_id: str, toward: str
):
    (edit,) = read(text).operations.tag_ops
    assert (edit.tag_id, edit.toward) == (tag_id, toward)


def test_to_take_a_scale_off_by_its_new_name_needs_no_end():
    held = apply(RENTER, read("buzzy").operations, small_release()).spec
    result = read("I don't care about going out", held)
    (edit,) = result.operations.tag_ops
    assert (edit.tag_id, edit.action) == ("pace", "remove")
    assert apply(held, result.operations, small_release()).spec.tags == ()


# --- A hedge says how much, and never which way ------------------------------------------------

HEDGES = ("slightly", "a bit", "fairly", "somewhat", "some", "quite", "pretty", "reasonably")
DOWN = ("down_small", "down_large")
THINGS = lexicon_of(GrittyVariant.B)


def leaning(result: InterpretResult) -> set[tuple[str, str]]:
    """Every thing an edit moves, and which way it leans: for it or against, and to which end."""
    found: set[tuple[str, str]] = set()
    for edit in result.operations.weight_ops:
        against = edit.action == "remove" or edit.step in DOWN or edit.direction == "less"
        found.add((f"feature:{edit.feature_id}", "against" if against else "for"))
    for edit in result.operations.tag_ops:
        against = edit.action == "remove" or edit.step in DOWN
        found.add((f"tag:{edit.tag_id}", "against" if against else f"for {edit.toward}"))
    return found


def steps(result: InterpretResult) -> list[str]:
    edits = (*result.operations.weight_ops, *result.operations.tag_ops)
    return [edit.step for edit in edits]


def test_no_hedge_turns_a_wish_round():
    read_in_full = tried = 0
    for phrase in sorted(THINGS):
        plainly = read(phrase)
        for hedge in HEDGES:
            hedged = read(f"{hedge} {phrase}")
            tried += 1
            # With a hedge a thing leans the way it leans without one, or nothing is
            # applied. Nothing is ever applied the other way, and nothing else moves.
            assert leaning(hedged) in (leaning(plainly), set()), f"{hedge} {phrase}"
            # It is never worth more for having been hedged.
            assert "up_large" not in steps(hedged) or hedge == "some", f"{hedge} {phrase}"
            # What is only offered is offered the same, hedged or not.
            assert offers(hedged) == offers(plainly) or leaning(hedged), f"{hedge} {phrase}"
            read_in_full += leaning(hedged) == leaning(plainly)
    assert tried > 2_000
    # And every hedge is read before every thing.
    assert read_in_full == tried


@pytest.mark.parametrize("thing", ["affluent", "posh", "character", "rough", "up and coming"])
@pytest.mark.parametrize("hedge", [*HEDGES, "a bit of", "somewhat of a"])
def test_a_hedge_before_a_word_that_is_only_offered_changes_nothing_that_is_offered(
    hedge: str, thing: str
):
    hedged, plainly = read(f"{hedge} {thing}"), read(thing)
    assert hedged.operations == NO_OPERATIONS
    if hedged.unread == ():
        assert offers(hedged) == offers(plainly)
    # Read or not, it is never offered the other way alone.
    for found, bare in zip(hedged.suggestions, plainly.suggestions, strict=False):
        assert {c.label for c in bare.choices} <= {c.label for c in found.choices}


def test_not_too_is_a_softer_not_and_never_a_wish_for_the_thing():
    tried = 0
    for phrase in sorted(THINGS):
        firmly, softly, wished = read(f"not {phrase}"), read(f"not too {phrase}"), read(phrase)
        tried += 1
        # It leans as "not" leans, or applies nothing.
        assert leaning(softly) in (leaning(firmly), set()), phrase
        # And it never leans as the wish itself does, but where to want less of a
        # thing is to care about it: "not too noisy" is a wish for less noise.
        same = leaning(softly) & leaning(wished)
        assert all(THINGS[phrase].nuisance for _ in same), phrase
        # It takes nothing off: what is wanted less is still wanted.
        assert "remove" not in [e.action for e in softly.operations.weight_ops], phrase
        assert "remove" not in [e.action for e in softly.operations.tag_ops], phrase
    assert tried > 250


@pytest.mark.parametrize(
    ("text", "asked"),
    [
        ("slightly quiet, somewhat leafy and a bit lively", {"quiet_residential", "leafy", "pace"}),
        (
            "fairly quiet with some pubs and a bit of culture",
            {"quiet_residential", "venue_evening_per_homes"},
        ),
        ("some culture", {"culture_venues_per_homes"}),
        ("a bit of a buzz", set[str]()),
    ],
)
def test_hedged_wishes_are_wishes(text: str, asked: set[str]):
    result = read(text)
    raised = {edit.feature_id.value for edit in result.operations.weight_ops}
    raised |= {edit.tag_id.value for edit in result.operations.tag_ops}
    assert asked <= raised
    assert all(way.startswith("for") for _, way in leaning(result))
