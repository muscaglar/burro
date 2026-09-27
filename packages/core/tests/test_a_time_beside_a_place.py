"""A time that is typed beside a place is the time of the journey to it.

In a prompt that is not plain a place is offered as a journey to it, and a
journey that holds no time is added with the usual 45 minutes. A time was read
only where it stood straight before its place: "40 minutes to Cindermoor
Works". With a word or two between them, "40 minutes or so to", "35 minutes on
the tube to", and wherever the time stood after the place, "Cindermoor Works
within 40 minutes", the minutes were dropped, and the journey was offered at
45 with a sentence that said the person gave none. Since 2026-09-26 the website
takes what is offered without asking, so a person who typed 40 was given 45.

Each of these now holds the minutes that were typed, and a limit is firm where
the words make it one and nowhere else. Where a time stands beside a place and
the reader cannot take it, the place is offered with nothing to choose, as it
was. Where a time stands apart from the place and the reader cannot tell which
journey it is for, the journey is offered with no time, and its note says that
a time was given: whoever words the offer never says that the person gave
none. Every name and every sentence here is made up, and the first twelve are
the ones the service was driven with.

Since 2026-09-27 the grammar reads a journey with its place first, so three of
the twelve are plain and are applied, each with the journey it was offered
with: `test_a_time_after_its_place.py` holds the rule.
"""

import pytest
from burro_core.ids import InterpretStatus, ModeChoice, StrictnessChoice, Tenure
from burro_core.interpret import (
    IGNORE,
    TIME_NOT_PLACED,
    TIME_NOT_TAKEN,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
)
from burro_core.ops import NO_OPERATIONS, CommuteEdit
from burro_core.spec import default_spec

from .support import fixture_release

RENTER = default_spec(Tenure.RENT)
READER = RuleInterpreter()
HARD, AS_IT_IS = StrictnessChoice.HARD, StrictnessChoice.UNCHANGED
NO_WAY, BY_TRANSPORT = ModeChoice.UNCHANGED, ModeChoice.PT
ON_FOOT, BY_BIKE = ModeChoice.WALK, ModeChoice.CYCLE


def place(name: str) -> str:
    (found,) = (one.place_id for one in fixture_release().places if one.name == name)
    return found


WORKS = place("Cindermoor Works")
QUARTER = place("Tallowgate Guild Quarter")
INFIRMARY = place("Pellam Infirmary")
CROSS = place("Pellam Cross")


def read(text: str) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=fixture_release()))


def journeys(result: InterpretResult) -> list[CommuteEdit]:
    """Each journey that an edit or a way of an offer holds."""
    edits = list(result.operations.commute_ops)
    for found in result.suggestions:
        for choice in found.choices:
            edits += choice.operations.commute_ops
    return edits


def said_of(result: InterpretResult) -> list[tuple[str, int, StrictnessChoice, ModeChoice]]:
    return [
        (edit.place_id, edit.max_minutes, edit.strictness, edit.mode) for edit in journeys(result)
    ]


def unread(text: str, result: InterpretResult) -> list[str]:
    return [text[span.start : span.end] for span in result.unread]


# The twelve plain ways of saying a time beside a place that the service was driven with.
DRIVEN = [
    ("Cindermoor Works within 40 minutes", (WORKS, 40, HARD, NO_WAY)),
    ("Cindermoor Works, 40 minutes", (WORKS, 40, AS_IT_IS, NO_WAY)),
    ("to Cindermoor Works in 40 minutes", (WORKS, 40, AS_IT_IS, NO_WAY)),
    ("get to Cindermoor Works in 40 minutes or less", (WORKS, 40, AS_IT_IS, NO_WAY)),
    ("my commute to Cindermoor Works should be under 40 minutes", (WORKS, 40, AS_IT_IS, NO_WAY)),
    ("40 minutes or so to Cindermoor Works", (WORKS, 40, AS_IT_IS, NO_WAY)),
    ("40 minutes each way to Cindermoor Works", (WORKS, 40, AS_IT_IS, NO_WAY)),
    ("40 mins door to door to Cindermoor Works", (WORKS, 40, AS_IT_IS, NO_WAY)),
    ("35 minutes on the tube to Tallowgate Guild Quarter", (QUARTER, 35, AS_IT_IS, BY_TRANSPORT)),
    ("35 minutes on the bus to Tallowgate Guild Quarter", (QUARTER, 35, AS_IT_IS, BY_TRANSPORT)),
    (
        "no more than 35 minutes on the tube to Tallowgate Guild Quarter",
        (QUARTER, 35, HARD, BY_TRANSPORT),
    ),
    ("35 minute commute, Tallowgate Guild Quarter", (QUARTER, 35, AS_IT_IS, NO_WAY)),
]


@pytest.mark.parametrize(("text", "journey"), DRIVEN)
def test_a_time_typed_beside_a_place_is_the_time_of_the_journey(
    text: str, journey: tuple[str, int, StrictnessChoice, ModeChoice]
):
    result = read(text)
    assert said_of(result) == [journey]
    # The words of the time are what the journey rests on, so none of them is unread.
    assert not [left for left in unread(text, result) if any(c.isdigit() for c in left)]


# Of the twelve, those that the grammar makes since it reads a journey with its place first:
# the place and then its time, and the name of a place beside a time that stands apart.
NOW_PLAIN = frozenset(
    {
        "Cindermoor Works within 40 minutes",
        "Cindermoor Works, 40 minutes",
        "35 minute commute, Tallowgate Guild Quarter",
    }
)


@pytest.mark.parametrize(("text", "journey"), DRIVEN)
def test_nothing_else_is_made_of_the_words_of_the_time(
    text: str, journey: tuple[str, int, StrictnessChoice, ModeChoice]
):
    """ "On the tube" is how the journey is made, and no wish to be well connected."""
    result = read(text)
    if text in NOW_PLAIN:
        # It is applied, as the same words are with the time first, and nothing is offered.
        assert (result.status, result.suggestions) == (InterpretStatus.OK, ())
        assert result.operations == NO_OPERATIONS.replace(commute_ops=result.operations.commute_ops)
        assert len(result.operations.commute_ops) == 1
        return
    assert [found.target for found in result.suggestions] == ["commute"]
    assert result.operations == NO_OPERATIONS


MORE = [
    # What says the most a time may be, after it and before the place.
    ("ideally 40 minutes max to Cindermoor Works", (WORKS, 40, HARD, NO_WAY)),
    ("ideally 40 minutes at most to Cindermoor Works", (WORKS, 40, HARD, NO_WAY)),
    ("ideally 40 minutes tops to Cindermoor Works", (WORKS, 40, AS_IT_IS, NO_WAY)),
    ("ideally 40 minutes or less to Cindermoor Works", (WORKS, 40, AS_IT_IS, NO_WAY)),
    # How the journey is made, with what is said of the time before it.
    ("40 minutes max by bike to Cindermoor Works, I think", (WORKS, 40, HARD, BY_BIKE)),
    ("40 minutes or so on foot to Cindermoor Works", (WORKS, 40, AS_IT_IS, ON_FOOT)),
    ("40 minutes tops on the bus to Cindermoor Works", (WORKS, 40, AS_IT_IS, BY_TRANSPORT)),
    ("40 minutes on the train to Cindermoor Works", (WORKS, 40, AS_IT_IS, BY_TRANSPORT)),
    ("40 minutes on the underground to Cindermoor Works", (WORKS, 40, AS_IT_IS, BY_TRANSPORT)),
    # A time in hours is a number of minutes, and what may be said of minutes may be said of it.
    ("an hour or so to Cindermoor Works", (WORKS, 60, AS_IT_IS, NO_WAY)),
    ("1 hour exactly to Cindermoor Works", (WORKS, 60, AS_IT_IS, NO_WAY)),
    ("an hour each way to Cindermoor Works", (WORKS, 60, AS_IT_IS, NO_WAY)),
    ("an hour max by bike to Cindermoor Works", (WORKS, 60, HARD, BY_BIKE)),
    ("Cindermoor Works within an hour", (WORKS, 60, HARD, NO_WAY)),
    ("Cindermoor Works in an hour and a quarter", (WORKS, 75, AS_IT_IS, NO_WAY)),
    # After the place, in its clause.
    ("Cindermoor Works in under 40 minutes please", (WORKS, 40, AS_IT_IS, NO_WAY)),
    ("Cindermoor Works in no more than 40 minutes", (WORKS, 40, HARD, NO_WAY)),
    ("Cindermoor Works, 40 minutes max", (WORKS, 40, HARD, NO_WAY)),
    ("Cindermoor Works by bike in 25 minutes", (WORKS, 25, AS_IT_IS, BY_BIKE)),
    ("Cindermoor Works in 25 minutes by bike", (WORKS, 25, AS_IT_IS, BY_BIKE)),
    ("honestly, Cindermoor Works, 35-40 minutes", (WORKS, 40, HARD, NO_WAY)),
    # Apart from the place, in the one sentence that names one place and one time.
    ("a 35 minute commute, honestly, to Tallowgate Guild Quarter", (QUARTER, 35, AS_IT_IS, NO_WAY)),
    ("Tallowgate Guild Quarter, honestly, a 25 minute walk", (QUARTER, 25, AS_IT_IS, ON_FOOT)),
    # And in a sentence of its own, where the prompt names one place and one time.
    ("I work at Cindermoor Works, I think. 40 minutes max.", (WORKS, 40, HARD, NO_WAY)),
    # What stands for the place, after the time: "of it", "from there".
    ("I work at Cindermoor Works, honestly, within half an hour of it", (WORKS, 30, HARD, NO_WAY)),
    ("Cindermoor Works, I think, and 40 minutes from there", (WORKS, 40, AS_IT_IS, NO_WAY)),
    ("Ideally no more than 40 minutes. I work at Cindermoor Works.", (WORKS, 40, HARD, NO_WAY)),
    (
        "I work at Cindermoor Works. Honestly, it should be under 40 minutes.",
        (WORKS, 40, AS_IT_IS, NO_WAY),
    ),
    # A number with no word for minutes is the time where "in" or "within" leads it in.
    ("Cindermoor Works in under 25", (WORKS, 25, AS_IT_IS, NO_WAY)),
    ("Cindermoor Works in 20", (WORKS, 20, AS_IT_IS, NO_WAY)),
    ("Cindermoor Works within 30", (WORKS, 30, HARD, NO_WAY)),
]


@pytest.mark.parametrize(("text", "journey"), MORE)
def test_the_time_is_read_wherever_the_words_give_it_to_the_one_place(
    text: str, journey: tuple[str, int, StrictnessChoice, ModeChoice]
):
    result = read(text)
    assert said_of(result) == [journey]
    assert not [left for left in unread(text, result) if any(c.isdigit() for c in left)]


@pytest.mark.parametrize(
    "text", ["Pellam Cross in under 25 minutes", "Pellam Cross in under 25 minutes, I think"]
)
def test_a_name_that_is_an_areas_too_is_a_place_where_a_time_stands_after_it(text: str):
    """It was offered as an area to look only in, or to leave out."""
    result = read(text)
    assert said_of(result) == [(CROSS, 25, AS_IT_IS, NO_WAY)]
    assert result.operations.area_ops == ()
    # The first is a plain prompt since 2026-09-27, and is applied. The second is offered.
    offered = [] if result.operations.commute_ops else ["commute"]
    assert [found.target for found in result.suggestions] == offered
    assert bool(result.operations.commute_ops) == ("think" not in text)


def test_a_time_with_a_word_for_a_journey_is_the_limit_of_each_journey_of_the_prompt():
    """As the grammar reads "a 40 minute commute" in a plain prompt."""
    text = "Cindermoor Works and Pellam Infirmary, honestly, a 40 minute commute"
    assert sorted(said_of(read(text))) == sorted(
        [(WORKS, 40, AS_IT_IS, NO_WAY), (INFIRMARY, 40, AS_IT_IS, NO_WAY)]
    )


NOT_PLACED = [
    # One time and two places: which journey it is for is the person's to say.
    "Cindermoor Works and Pellam Infirmary, honestly, 40 minutes max",
    # Two times and one place.
    "Cindermoor Works, 40 minutes, or 50 minutes",
    "I work at Cindermoor Works, I think. 40 minutes. 50 minutes at a push.",
    # A time that a word before it turns, or says is over.
    "Cindermoor Works, never 40 minutes",
    "Cindermoor Works. It was 90 minutes.",
    # A time that more is said of, which the reader does not read.
    "Cindermoor Works, 40 minutes ideally speaking",
    # A time that is said of another way than the journey is made.
    "I cycle to Cindermoor Works, 25 minutes on foot",
    # A time that is said of what the reader does not know, which may be the journey.
    "the nearest shop is a twenty minute walk. I work at Cindermoor Works, I think",
    "Cindermoor Works, I think. My last flat was 40 minutes from anywhere.",
    "I want to be within 30 minutes of my mum, who works at Cindermoor Works",
    "I run for 30 minutes every day near Cindermoor Works",
]


@pytest.mark.parametrize("text", NOT_PLACED)
def test_a_time_the_reader_cannot_give_to_a_journey_is_said_to_be_so(text: str):
    result = read(text)
    heard = [found for found in result.suggestions if found.target == "commute"]
    assert heard
    for found in heard:
        # The journey is offered as one that was given no time is, and says that a time
        # was given, so that whoever words it does not say that the person gave none.
        assert found.note == TIME_NOT_PLACED
        assert [choice.direction for choice in found.choices] == ["more", "ignore"]
    assert {edit.max_minutes for edit in journeys(result)} == {0}
    # The words of the time are said to be unread.
    assert [left for left in unread(text, result) if "minute" in left]


NOT_READ = [
    # More than the time that was read: the hour alone is not what was said.
    ("an hour n a half to Cindermoor Works", "an hour n a half to"),
    ("an hour and a bit to Cindermoor Works", "an hour and a bit to"),
    ("an hour plus to Cindermoor Works", "an hour plus to"),
    ("40 minutes and a bit to Cindermoor Works", "40 minutes and a bit to"),
    ("40 minutes plus to Cindermoor Works", "40 minutes plus to"),
    ("40 minutes 30 seconds to Cindermoor Works", "40 minutes 30 seconds to"),
    # There and back is twice the journey, and nobody said how long one way is.
    ("40 minutes there and back to Cindermoor Works", "40 minutes there and back to"),
]


@pytest.mark.parametrize(("text", "left"), NOT_READ)
def test_a_time_before_a_place_that_is_not_read_whole_is_not_made_up_for(text: str, left: str):
    result = read(text)
    assert journeys(result) == []
    (heard,) = result.suggestions
    assert (heard.target, heard.choices, heard.note) == ("commute", (IGNORE,), TIME_NOT_TAKEN)
    assert left in unread(text, result)


OF_SOMETHING_ELSE = [
    # The minutes are said of a thing, and the journey was given none.
    "Cindermoor Works, I think, and a gym within 10 minutes",
    # Or are no time that a journey may take, and say what kind of thing something is.
    "I work 12 hour shifts, honestly, near Cindermoor Works",
    "I spend 45 minute sessions at the gym, honestly, near Cindermoor Works",
    "5 minutes from a park, honestly, near Cindermoor Works",
    "I work at Cindermoor Works, I think. A park within 10 minutes.",
    "near Cindermoor Works, honestly, and 10 minutes to a station",
    # A number that is no time: of years, of days, of bedrooms, of money.
    "Cindermoor Works in 2027, I think",
    "Cindermoor Works in 3 weeks, I think",
    "Cindermoor Works, honestly, 2 bed",
    "Cindermoor Works, honestly, 900 minutes a week",
]


@pytest.mark.parametrize("text", OF_SOMETHING_ELSE)
def test_minutes_that_are_said_of_something_else_are_no_time_of_the_journey(text: str):
    result = read(text)
    (offered,) = [found for found in result.suggestions if found.target == "commute"]
    assert offered.note == ""
    assert said_of(result) == [(WORKS, 0, AS_IT_IS, NO_WAY)]


def test_a_place_to_stay_away_from_is_kept_away_from_whatever_time_stands_after_it():
    result = read("Cindermoor Works, at least 40 minutes")
    assert journeys(result) == []


def test_a_plain_prompt_is_applied_as_it_was():
    result = read("40 minutes to Cindermoor Works")
    assert result.status is InterpretStatus.OK
    assert [(e.place_id, e.max_minutes) for e in result.operations.commute_ops] == [(WORKS, 40)]
    assert result.suggestions == ()
