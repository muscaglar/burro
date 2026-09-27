"""A time in hours is a number of minutes, and its minutes are never read by themselves.

"1 hour 15 to Pellam Cross" was offered as a journey of at most 15 minutes, and
one press took it. "1 hour to", "2 hours to", "1.5 hours to" and "1h to" lost
their time, and the journey was offered at the 45 minutes nobody said. A person
who gives a time in hours has given a number, and the reader reads it where it
reads any other: as one number, of minutes.

No word of it is a word of the grammar. "Hours" by itself is still a word the
reader does not know, and a time is never put together across a mark. Minutes
that the reader could not read with their hours are part of a time it did not
read, and are never offered by themselves. Every name and every sentence here is
made up.
"""

from typing import Any

import pytest
from burro_core.grammar import KNOWN_WORDS, VOCABULARY, Grammar
from burro_core.ids import AssumptionCode, InterpretStatus, Tenure
from burro_core.interpret import (
    IGNORE,
    NO_STAYING_AWAY,
    TIME_NOT_TAKEN,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
)
from burro_core.ops import NO_OPERATIONS
from burro_core.places import Names
from burro_core.reading import Is, Item, lines_of
from burro_core.reducer import apply
from burro_core.spec import default_spec

from .support import place_id, small_release

RENTER = default_spec(Tenure.RENT)
READER = RuleInterpreter()
GRAMMAR = Grammar(Names(small_release()), small_release())
QUIET = ("unchanged", "none", "default", 0, 0.0)


def read(text: str) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=small_release()))


def items(text: str) -> list[Item]:
    (line,) = lines_of(text)
    return GRAMMAR.items(line)


def said(edit: Any) -> dict[str, Any]:
    """An edit with its sentinels left out."""
    return {k: v for k, v in edit.model_dump(mode="json").items() if v not in QUIET}


def journeys(result: InterpretResult) -> list[tuple[str, dict[str, Any]]]:
    """Each way a journey is offered, as its label says it and as its edit holds it."""
    return [
        (choice.label, said(choice.operations.commute_ops[0]))
        for found in result.suggestions
        if found.target == "commute"
        for choice in found.choices
        if choice.operations.commute_ops
    ]


def unread(text: str, result: InterpretResult) -> list[str]:
    return [text[span.start : span.end] for span in result.unread]


# --- A time in hours is one number, of minutes ------------------------------------------------

IN_HOURS = [
    ("1 hour", 60),
    ("2 hours", 120),
    ("1.5 hours", 90),
    ("0.5 hours", 30),
    ("1.25 hours", 75),
    ("1h", 60),
    ("1hr", 60),
    ("2hrs", 120),
    ("1.5h", 90),
    ("1 hr", 60),
    ("2 hrs", 120),
    ("an hour", 60),
    ("one hour", 60),
    ("two hours", 120),
    ("half an hour", 30),
    ("1 hour 15", 75),
    ("an hour 15", 75),
    ("1 hour 15 minutes", 75),
    ("1 hour 15 mins", 75),
    ("1 hour and 15 minutes", 75),
    ("1 hour 5", 65),
    ("one hour fifteen", 75),
    ("an hour and a quarter", 75),
    ("an hour and a half", 90),
    ("an hour and three quarters", 105),
    ("one and a half hours", 90),
    ("1 and a half hours", 90),
    ("1h15", 75),
    ("1h15m", 75),
    ("1hr 15min", 75),
    ("1h 15m", 75),
    ("1 hour 15mins", 75),
    ("a 1-hour", 60),
    ("a one-hour", 60),
    ("a half-hour", 30),
]


@pytest.mark.parametrize(("typed", "minutes"), IN_HOURS)
def test_a_time_in_hours_is_read_as_one_number_of_minutes(typed: str, minutes: int):
    text = f"{typed} commute"
    *before, time, commute = items(text)
    assert [(found.what, found.text) for found in before] in ([], [(Is.WORD, "a")])
    assert (time.what, time.value, time.unit, time.hours) == (Is.NUMBER, minutes, "min", True)
    # It rests on the whole of what was typed of it, and on no word beside it.
    assert text[time.start : time.end] == typed.removeprefix("a ")
    assert (commute.what, commute.text) == (Is.WORD, "commute")


@pytest.mark.parametrize(
    ("typed", "minutes"), [(typed, minutes) for typed, minutes in IN_HOURS if minutes <= 90]
)
def test_a_journey_of_a_time_in_hours_is_applied_with_its_minutes(typed: str, minutes: int):
    text = f"{typed} to Pellam Cross"
    result = read(text)
    assert (result.status, result.unread, result.suggestions) == (InterpretStatus.OK, (), ())
    (edit,) = result.operations.commute_ops
    assert said(edit) == {
        "action": "add",
        "place_id": place_id(1),
        "max_minutes": minutes,
        "provenance": "stated",
    }
    # The person gave one time, so nothing of it is said to be assumed.
    assert AssumptionCode.MAX_MINUTES not in {found.code for found in result.assumptions}
    assert [text[found.start : found.end] for found in result.rests_on] == [text]
    after = apply(RENTER, result.operations, small_release())
    assert after.rejected == ()
    assert [(c.place_id, c.max_minutes) for c in after.spec.commutes] == [(place_id(1), minutes)]


@pytest.mark.parametrize("typed", ["2 hours", "two hours", "2hrs", "1 hour 45", "3 hours"])
def test_a_time_no_journey_may_take_is_turned_away_as_any_number_of_minutes_is(typed: str):
    """The release holds no journey by public transport of over 90 minutes."""
    in_hours = read(f"{typed} to Pellam Cross")
    (edit,) = in_hours.operations.commute_ops
    assert edit.max_minutes > 90
    in_minutes = read(f"{edit.max_minutes} minutes to Pellam Cross")
    assert in_hours.operations == in_minutes.operations
    turned_away = apply(RENTER, in_hours.operations, small_release()).rejected
    assert [found.reason for found in turned_away] == ["out_of_range"]


@pytest.mark.parametrize(
    ("text", "minutes", "firm", "mode"),
    [
        ("within an hour of Pellam Cross", 60, True, ""),
        ("within 1 hour of Pellam Cross", 60, True, ""),
        ("at most 1 hour 15 to Pellam Cross", 75, True, ""),
        ("1 hour 15 max to Pellam Cross", 75, True, ""),
        ("under an hour to Pellam Cross", 60, False, ""),
        ("up to 1.5 hours to Pellam Cross", 90, False, ""),
        ("about an hour to Pellam Cross by bike", 60, False, "cycle"),
        ("half an hour to Pellam Cross on foot", 30, False, "walk"),
        ("a 1 hour commute to Pellam Cross", 60, False, ""),
        ("I work at Pellam Cross, a 1 hour commute", 60, False, ""),
        ("I work at Pellam Cross and want to get there within an hour and a quarter", 75, True, ""),
        ("get to Pellam Cross in under an hour", 60, False, ""),
    ],
)
def test_what_is_said_of_a_time_in_hours_is_what_is_said_of_minutes(
    text: str, minutes: int, firm: bool, mode: str
):
    result = read(text)
    assert (result.status, result.unread) == (InterpretStatus.OK, ())
    (edit,) = result.operations.commute_ops
    assert (edit.max_minutes, edit.strictness == "hard") == (minutes, firm)
    assert said(edit).get("mode", "") == mode


def test_a_time_in_hours_said_of_a_thing_says_that_it_is_wanted_near():
    # As minutes do: "a park within 10 minutes". No journey is made of it.
    for text in ("a park within an hour", "within 1 hour of a park", "a park half an hour away"):
        result = read(text)
        assert result.status is InterpretStatus.OK, text
        assert result.operations.commute_ops == ()
        assert [edit.feature_id for edit in result.operations.weight_ops] == ["park_proximity"]


# --- Its minutes are never offered by themselves ------------------------------------------------


@pytest.mark.parametrize(
    ("text", "label", "words"),
    [
        (
            "1 hour 15 to Pellam Cross, I think",
            "Add a journey to Pellam Cross within 75 minutes",
            "1 hour 15 to Pellam Cross",
        ),
        (
            "an hour 15 to Pellam Cross, I think",
            "Add a journey to Pellam Cross within 75 minutes",
            "an hour 15 to Pellam Cross",
        ),
        (
            "an hour and a quarter to Pellam Cross is fine by me",
            "Add a journey to Pellam Cross within 75 minutes",
            "an hour and a quarter to Pellam Cross",
        ),
        (
            "1 hour to Pellam Cross is fine by me",
            "Add a journey to Pellam Cross within 60 minutes",
            "1 hour to Pellam Cross",
        ),
        (
            "1.5 hours to Pellam Cross is fine by me",
            "Add a journey to Pellam Cross within 90 minutes",
            "1.5 hours to Pellam Cross",
        ),
        (
            "1h to Pellam Cross is fine by me",
            "Add a journey to Pellam Cross within 60 minutes",
            "1h to Pellam Cross",
        ),
        (
            "at most an hour and a half to Pellam Cross, I suppose",
            "Add a journey to Pellam Cross of no more than 90 minutes",
            "at most an hour and a half to Pellam Cross",
        ),
    ],
)
def test_a_journey_that_is_offered_holds_the_whole_of_a_time_in_hours(
    text: str, label: str, words: str
):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    ((offered, edit),) = journeys(result)
    assert offered == label
    assert edit["max_minutes"] == int(label.split(" minutes")[0].split()[-1])
    (journey,) = result.suggestions
    assert [text[span.start : span.end] for span in journey.spans] == [words]
    assert apply(RENTER, journey.choices[0].operations, small_release()).rejected == ()


@pytest.mark.parametrize(
    ("text", "not_read"),
    [
        # A mark parts the hours from the minutes, and a time is put together across none.
        ("1 hour, 15 minutes to Pellam Cross", "1 hour, 15 minutes to"),
        ("1 hour; 15 to Pellam Cross", "1 hour; 15 to"),
        ("an hour (15 minutes to Pellam Cross)", "an hour (15 minutes to"),
        # More minutes than an hour holds.
        ("1 hour 75 to Pellam Cross", "1 hour 75 to"),
        ("1 hour 60 minutes to Pellam Cross", "1 hour 60 minutes to"),
        # A word for hours with no number of them before it.
        ("hours 15 to Pellam Cross", "hours 15 to"),
        ("a few hours 15 minutes to Pellam Cross", "a few hours 15 minutes to"),
        ("1-2 hours 15 to Pellam Cross", "1-2 hours 15 to"),
        # Another number, which may be the hours.
        ("1 15 to Pellam Cross", "1 15 to"),
        ("1 15 minutes to Pellam Cross", "1 15 minutes to"),
        ("one 15 to Pellam Cross", "one 15 to"),
        ("45mins 15 to Pellam Cross", "45mins 15 to"),
    ],
)
def test_minutes_that_stand_after_hours_or_another_number_are_never_offered_by_themselves(
    text: str, not_read: str
):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    # A time that was not read is no time of 15 minutes. Nor is it the usual 45, which
    # nobody said: the place is said to have been heard, with nothing to choose.
    assert journeys(result) == []
    (journey,) = result.suggestions
    assert (journey.target, journey.choices, journey.note) == ("commute", (IGNORE,), TIME_NOT_TAKEN)
    assert [text[span.start : span.end] for span in journey.spans] == ["Pellam Cross"]
    # And the words of the time are said to be unread.
    assert unread(text, result) == [not_read]


@pytest.mark.parametrize(
    "text",
    [
        "renting for 1500 30 minutes to Pellam Cross, I think",
        "2 bed 30 minutes to Pellam Cross, I think",
        "a 2-bed 30 minutes to Pellam Cross, I think",
        "up to £1,500 30 minutes to Pellam Cross, I think",
        "35 to 40 minutes to Pellam Cross, I think",
    ],
)
def test_minutes_after_a_number_that_is_no_part_of_a_time_are_offered_as_they_were(text: str):
    ((label, edit),) = journeys(read(text))
    assert label.startswith("Add a journey to Pellam Cross")
    assert edit["max_minutes"] in (30, 40)


def test_a_plain_list_of_a_home_and_a_journey_is_still_applied():
    result = read("renting 1500 30 minutes to Pellam Cross")
    assert result.status is InterpretStatus.OK
    assert [edit.amount for edit in result.operations.budget_ops] == [1500]
    assert [edit.max_minutes for edit in result.operations.commute_ops] == [30]


# --- What a time in hours is not ---------------------------------------------------------------


def test_no_word_of_a_time_in_hours_is_a_word_of_the_grammar():
    for word in ("hour", "hours", "hr", "hrs", "h", "half", "quarter", "quarters"):
        assert word not in KNOWN_WORDS, word
    assert not [phrase for phrase in VOCABULARY if "hour" in phrase]


@pytest.mark.parametrize(
    "text",
    [
        "hours",
        "parks hours",
        "leafy hour",
        "the hour to Pellam Cross",
        "rush hour to Pellam Cross",
        "hour to Pellam Cross",
        "half to Pellam Cross",
        "a quarter to Pellam Cross",
    ],
)
def test_a_word_for_hours_with_no_number_of_them_is_a_word_the_reader_does_not_know(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert all("max_minutes" not in edit for _, edit in journeys(result))
    assert unread(text, result)


@pytest.mark.parametrize(
    "text",
    [
        # A range of hours is a range of something that is not minutes.
        "1-2 hours to Pellam Cross",
        "1 to 2 hours to Pellam Cross",
        # A time of nothing.
        "0 hours to Pellam Cross",
        # Hours of something else.
        "opening hours",
        "24 hour gym",
    ],
)
def test_what_is_no_time_a_journey_may_take_adds_no_journey(text: str):
    result = read(text)
    assert result.operations.commute_ops == ()
    # Nothing says that a range was given, of which the shorter would be one minute.
    assert {found.note for found in result.suggestions} <= {"", TIME_NOT_TAKEN}


def test_a_number_of_bedrooms_after_a_time_in_hours_is_not_its_minutes():
    *_, time, bedrooms, bed, _ = items("a commute of 1 hour 2 bed flat")
    assert (time.value, time.unit, time.hours) == (60, "min", True)
    assert (bedrooms.what, bedrooms.value, bed.text) == (Is.NUMBER, 2, "bed")
    result = read("2 bed flat within 1 hour of Pellam Cross")
    assert result.status is InterpretStatus.OK
    assert [edit.segment for edit in result.operations.budget_ops] == ["bed_2"]
    assert [edit.max_minutes for edit in result.operations.commute_ops] == [60]


@pytest.mark.parametrize(
    "text",
    [
        "at least 2 hours from Pellam Cross",
        "at least an hour from Pellam Cross",
        "over an hour and a half from Pellam Cross",
        "an hour or more from Pellam Cross",
    ],
)
def test_a_least_in_hours_is_a_place_to_stay_away_from(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    (journey,) = result.suggestions
    assert (journey.target, journey.note) == ("commute", NO_STAYING_AWAY)
    assert [choice.label for choice in journey.choices] == ["Leave it out"]
