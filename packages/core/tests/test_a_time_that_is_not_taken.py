"""A time that stands before a place and is not taken is never made up for by the usual one.

In a prompt that is not plain a place is offered as a journey to it, and one
press may take the offer. Where no time was read the journey holds none, and
the search takes the usual 45 minutes. That is so where a person gave no time.
It was so too where they gave one that the reader did not take: "1 hour, 15
minutes to Pellam Infirmary", whose minutes are part of a longer time, "1.15
hours to", "a few hours to", "24 hours to". One press then added a journey of
45 minutes, which nobody said, and the offer said that no number of minutes
was given.

So where a time stands where the time of a journey stands, and is none the
journey may hold, the place is said to have been heard, with nothing to choose
and the reason. Every name and every sentence here is made up.

A time in hours with a word or two after it that leaves it the time it is, "an
hour or so to", "an hour max by bike to", was among them until the reader read
what is said of a time: it is now the time of the journey, as the minutes of
"40 minutes or so to" are (`test_a_time_beside_a_place.py`).
"""

import pytest
from burro_core.ids import Tenure
from burro_core.interpret import (
    IGNORE,
    NO_STAYING_AWAY,
    TIME_NOT_TAKEN,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
)
from burro_core.ops import NO_OPERATIONS
from burro_core.spec import default_spec

from .support import place_id, small_release

RENTER = default_spec(Tenure.RENT)
READER = RuleInterpreter()


def read(text: str) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=small_release()))


def journeys_to(result: InterpretResult) -> list[tuple[str, int]]:
    """Each journey that an edit or a way of an offer holds: its place and its minutes."""
    edits = list(result.operations.commute_ops)
    for found in result.suggestions:
        for choice in found.choices:
            edits += choice.operations.commute_ops
    return [(edit.place_id, edit.max_minutes) for edit in edits]


NOT_TAKEN = [
    # The minutes of a longer time, which was not read whole.
    ("1 hour, 15 minutes to Pellam Infirmary", "1 hour, 15 minutes to"),
    ("1 15 to Pellam Infirmary", "1 15 to"),
    ("1 hour 4 to Pellam Infirmary", "1 hour 4 to"),
    ("1 hour 75 to Pellam Infirmary", "1 hour 75 to"),
    ("zone 2 30 minutes to Pellam Infirmary", "zone 2 30 minutes to"),
    # A time in hours that the reader does not read.
    ("1.15 hours to Pellam Infirmary", "1.15 hours to"),
    ("a few hours to Pellam Infirmary", "a few hours to"),
    ("a couple of hours to Pellam Infirmary", "a couple of hours to"),
    ("a third of an hour to Pellam Infirmary", "a third of an hour to"),
    ("hours to Pellam Infirmary", "hours to"),
    # A time that is typed as one word, with figures the reader does not read.
    ("1.15h to Pellam Infirmary", "1.15h to"),
    ("1h75 to Pellam Infirmary", "1h75 to"),
    ("1:15 to Pellam Infirmary", "1:15 to"),
    ("45min-1hr to Pellam Infirmary", "45min-1hr to"),
    # A time that no journey may take.
    ("24 hours to Pellam Infirmary, I think", "24 hours to"),
    ("ideally 3 hours to Pellam Infirmary", "ideally 3 hours to"),
    ("ideally 2 minutes to Pellam Infirmary", "ideally 2 minutes to"),
    ("an hour and 2 to Pellam Infirmary", "an hour and 2 to"),
    # With how the journey is made between the time and the place.
    ("1 hour, 15 minutes walk to Pellam Infirmary", "1 hour, 15 minutes walk to"),
    ("a few hours commute from Pellam Infirmary", "a few hours commute from"),
    # A time in hours with a word or two after it, of how much more it is.
    ("an hour n a half to Pellam Infirmary", "an hour n a half to"),
    ("an hour and a bit to Pellam Infirmary", "an hour and a bit to"),
    ("1 hour 15 minutes 30 seconds to Pellam Infirmary", "1 hour 15 minutes 30 seconds to"),
    ("an hour plus to Pellam Infirmary", "an hour plus to"),
    ("an hour and a bit on foot to Pellam Infirmary", "an hour and a bit on foot to"),
    # A time in hours that says whose walk it is.
    ("an hour's walk to Pellam Infirmary", "an hour's walk to"),
    ("a quarter of an hour's walk to Pellam Infirmary", "a quarter of an hour's walk to"),
    ("an hour's cycle to Pellam Infirmary", "an hour's cycle to"),
]


@pytest.mark.parametrize(("text", "left"), NOT_TAKEN)
def test_a_place_is_offered_as_no_journey_where_the_time_before_it_is_not_taken(
    text: str, left: str
):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    (heard,) = result.suggestions
    assert (heard.target, heard.label) == ("commute", "Pellam Infirmary")
    # Nothing of it can be chosen, so no press adds a journey of minutes nobody said.
    assert heard.choices == (IGNORE,)
    assert heard.note == TIME_NOT_TAKEN
    assert journeys_to(result) == []
    assert [text[span.start : span.end] for span in heard.spans] == ["Pellam Infirmary"]
    # The words of the time are said to be unread.
    assert left in [text[span.start : span.end] for span in result.unread]


@pytest.mark.parametrize(
    ("text", "minutes", "mode"),
    [
        # How exact the time is, and that it is of the journey one way.
        ("an hour or so to Pellam Infirmary", 60, "unchanged"),
        ("1 hour exactly to Pellam Infirmary", 60, "unchanged"),
        ("an hour each way to Pellam Infirmary", 60, "unchanged"),
        # The most it may be, and the way, between it and the place.
        ("an hour max by bike to Pellam Infirmary", 60, "cycle"),
        ("an hour or so on foot to Pellam Infirmary", 60, "walk"),
        ("an hour tops on the bus to Pellam Infirmary", 60, "pt"),
    ],
)
def test_a_time_in_hours_is_taken_with_what_leaves_it_the_time_it_is(
    text: str, minutes: int, mode: str
):
    """Each was said to be a time that was not taken, until what is said of a time was read."""
    result = read(text)
    assert result.operations == NO_OPERATIONS
    (offered,) = result.suggestions
    assert (offered.target, offered.note) == ("commute", "")
    (edit,) = [edit for choice in offered.choices for edit in choice.operations.commute_ops]
    assert (edit.place_id, edit.max_minutes, edit.mode) == (place_id(4), minutes, mode)
    # The offer rests on the whole of the time, so none of it is said to be unread.
    assert [text[span.start : span.end] for span in result.unread] == []


def test_a_name_that_is_an_areas_too_is_a_place_where_a_time_stands_before_it():
    """It was offered as an area to look only in, or to leave out."""
    result = read("1 hour, 15 minutes to Pellam Cross")
    (heard,) = result.suggestions
    assert (heard.target, heard.choices, heard.note) == ("commute", (IGNORE,), TIME_NOT_TAKEN)


@pytest.mark.parametrize(
    "text",
    [
        "ideally near Pellam Infirmary",
        "I work at Pellam Infirmary, I think",
        "ideally walking distance to Pellam Infirmary",
        "Pellam Infirmary would be handy",
        # A number that stands apart from where the time of a journey stands.
        "I work at 15 Pellam Infirmary",
        "2 of us, near Pellam Infirmary",
        # Hours that are said of something else, with a word of its own between.
        "I work 12 hour shifts close to Pellam Infirmary",
        "shops open 24 hours next to Pellam Infirmary",
        "long hours, so close to Pellam Infirmary",
    ],
)
def test_a_place_that_no_time_stands_before_is_offered_as_a_journey_as_it_was(text: str):
    result = read(text)
    (offered,) = [found for found in result.suggestions if found.target == "commute"]
    assert offered.note == ""
    assert journeys_to(result) == [(place_id(4), 0)]


@pytest.mark.parametrize(
    ("text", "minutes"),
    [
        ("ideally 30 minutes to Pellam Infirmary", 30),
        ("ideally 1 hour 15 to Pellam Infirmary", 75),
        ("ideally an hour to Pellam Infirmary", 60),
        ("2 bed 30 minutes to Pellam Infirmary, I think", 30),
    ],
)
def test_a_time_that_is_taken_is_offered_with_the_journey_as_it_was(text: str, minutes: int):
    result = read(text)
    (offered,) = [found for found in result.suggestions if found.target == "commute"]
    assert offered.note == ""
    assert journeys_to(result) == [(place_id(4), minutes)]


def test_a_place_to_stay_away_from_says_so_whatever_time_stands_before_it():
    result = read("at least 1 hour, 15 minutes from Pellam Infirmary")
    (heard,) = result.suggestions
    assert (heard.choices, heard.note) == ((IGNORE,), NO_STAYING_AWAY)


def test_a_time_in_hours_before_a_drive_is_not_made_up_for_either():
    """Burro holds no journey by car, and says so. The hour is no 45 minutes by train."""
    text = "an hour's drive from Pellam Infirmary"
    result = read(text)
    assert journeys_to(result) == []
    (heard,) = [found for found in result.suggestions if found.target == "commute"]
    assert (heard.choices, heard.note) == ((IGNORE,), TIME_NOT_TAKEN)
    assert "driving" in [unmet.value for unmet in result.unmet]
