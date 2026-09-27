"""A way of travelling is read beside a place only where nothing beside it sets it in doubt.

In a prompt that is not plain a journey is offered with the way that stands
beside its place, and one press may take it. "A 20 minute bus ride to Pellam
Cross" was offered as a journey by bike, for "ride". "Unable to walk to Pellam
Cross" was offered as a walk, and so was "Pellam Cross on foot is impossible".
"Walk or cycle to Pellam Cross" was offered by bike, which is one of the two.

So the words that say a way are read only where what stands straight beside
them lets them say it. Where it does not, the journey is offered as it was
before a way was read in an offer: with no way, which the service says it took
public transport for. Every name and every sentence here is made up.

A ride that is named by what it is on, "a 20 minute bus ride to", is a journey
by public transport of the minutes that were typed. It was offered at the
usual 45 minutes, with no way. A ride on what Burro holds no journey by, or on
what the reader does not know, is offered with nothing to choose where a time
was typed with it: the time is no time by public transport.
"""

from typing import Any

import pytest
from burro_core.ids import Tenure
from burro_core.interpret import (
    IGNORE,
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
QUIET = ("unchanged", "none", "default", 0, 0.0)


def read(text: str) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=small_release()))


def journeys(result: InterpretResult) -> list[dict[str, Any]]:
    """Each journey that is offered, as its edit holds it, with its sentinels left out."""
    return [
        {
            key: value
            for key, value in choice.operations.commute_ops[0].model_dump(mode="json").items()
            if value not in QUIET
        }
        for found in result.suggestions
        if found.target == "commute"
        for choice in found.choices
        if choice.operations.commute_ops
    ]


def rested(text: str, result: InterpretResult) -> list[str]:
    return [text[s.start : s.end] for found in result.suggestions for s in found.spans]


def no_way(text: str) -> dict[str, Any]:
    """The one journey a sentence is offered, which must hold no way of travelling."""
    result = read(text)
    assert result.operations == NO_OPERATIONS, text
    (edit,) = journeys(result)
    assert edit["place_id"] == place_id(1), text
    assert "mode" not in edit, text
    return edit


@pytest.mark.parametrize(
    "text",
    [
        "a short tube ride to Pellam Cross",
        "a taxi ride to Pellam Cross",
        "a quick motorbike ride to Pellam Cross",
    ],
)
def test_a_ride_on_something_else_is_no_journey_by_bike(text: str):
    """ "Ride" is a bike ride after a time, an article or "bike", and after nothing else."""
    no_way(text)
    assert not [words for words in rested(text, read(text)) if "ride" in words]


@pytest.mark.parametrize(
    "text",
    ["a 20 minute bus ride to Pellam Cross", "a 20 minute train ride to Pellam Cross"],
)
def test_a_ride_that_is_named_by_what_it_is_on_is_a_journey_by_public_transport(text: str):
    """It is no journey by bike, and it holds the minutes that were typed with it."""
    result = read(text)
    assert result.operations == NO_OPERATIONS
    (edit,) = journeys(result)
    assert (edit["place_id"], edit["mode"], edit["max_minutes"]) == (place_id(1), "pt", 20)


@pytest.mark.parametrize(
    "text",
    ["a 10 minute car ride to Pellam Cross", "a 15 minute scooter ride to Pellam Cross"],
)
def test_a_timed_ride_on_what_burro_holds_no_journey_by_is_no_journey_by_bike(text: str):
    """Nor is it one of 45 minutes by public transport, which one press added."""
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert journeys(result) == []
    (heard,) = [found for found in result.suggestions if found.target == "commute"]
    assert (heard.choices, heard.note) == ((IGNORE,), TIME_NOT_TAKEN)


@pytest.mark.parametrize(
    ("text", "mode"),
    [
        ("a 20 minute ride to Pellam Cross, I think", "cycle"),
        ("a 20 minute bike ride to Pellam Cross, I think", "cycle"),
        ("a short bike ride to Pellam Cross", "cycle"),
        ("a short cycle to Pellam Cross", "cycle"),
        ("an easy walk to Pellam Cross", "walk"),
        ("a quick walk to Pellam Cross", "walk"),
        ("the walk to Pellam Cross, I think", "walk"),
        ("30 minutes by bike to Pellam Cross", "cycle"),
        ("I bike to Pellam Cross, I think", "cycle"),
    ],
)
def test_a_way_that_is_said_as_the_grammar_lists_it_is_still_read(text: str, mode: str):
    result = read(text)
    (edit,) = journeys(result)
    assert edit["mode"] == mode


@pytest.mark.parametrize(
    "text",
    [
        "unable to walk to Pellam Cross",
        "impossible to walk to Pellam Cross",
        "it is hard to walk to Pellam Cross",
        "I struggle to walk to Pellam Cross",
        "reluctant to cycle to Pellam Cross",
        "I hope to cycle to Pellam Cross",
        "I have to cycle to Pellam Cross",
    ],
)
def test_a_way_is_not_read_after_a_word_the_reader_cannot_place_and_to(text: str):
    """What stands before "to walk to" says whether the walk is wished for, or can be made."""
    no_way(text)


@pytest.mark.parametrize(
    ("text", "mode"),
    [
        ("ideally I want to walk to Pellam Cross", "walk"),
        ("I think I would like to cycle to Pellam Cross", "cycle"),
        ("ideally I need to walk to Pellam Cross", "walk"),
        ("ideally looking to cycle to Pellam Cross", "cycle"),
        ("ideally I'd love to walk to Pellam Cross", "walk"),
    ],
)
def test_a_way_is_read_after_the_speakers_own_wish_to_go_that_way(text: str, mode: str):
    (edit,) = journeys(read(text))
    assert edit["mode"] == mode


@pytest.mark.parametrize(
    "text",
    [
        "walk or cycle to Pellam Cross",
        "I walk or cycle to Pellam Cross",
        "ideally bus and walk to Pellam Cross",
        "ideally tube or cycle to Pellam Cross",
        "30 minutes to Pellam Cross by bike or on foot",
        "30 minutes to Pellam Cross by bike or tube",
        "ideally 30 minutes to Pellam Cross by train and bike",
        "ideally 30 minutes to Pellam Cross by bike and train",
        "ideally 30 minutes to Pellam Cross by train then bike",
        # What leads in to the second way stands between it and the word that joins.
        "a walk or a cycle to Pellam Cross",
        "a short walk or a short cycle to Pellam Cross",
        "the walk or the bike ride to Pellam Cross",
        "ideally a bus or a quick cycle to Pellam Cross",
        "I walk and then cycle to Pellam Cross",
        "I walk or else I cycle to Pellam Cross",
    ],
)
def test_of_two_ways_that_are_joined_neither_is_taken(text: str):
    """Nobody can say which of the two is meant, so the journey is offered with no way."""
    no_way(text)


@pytest.mark.parametrize(
    ("text", "mode"),
    [
        ("leafy and walking distance to Pellam Cross, I think", "walk"),
        ("a park and a 20 minute cycle to Pellam Cross, I think", "cycle"),
        ("20 minutes to Pellam Cross on foot and a park nearby, I think", "walk"),
        ("20 minutes to Pellam Cross by bike, and leafy, I think", "cycle"),
    ],
)
def test_a_way_beside_a_word_that_joins_another_wish_is_still_read(text: str, mode: str):
    (edit,) = journeys(read(text))
    assert edit["mode"] == mode


@pytest.mark.parametrize(
    "text",
    [
        "Pellam Cross on foot is impossible",
        "Pellam Cross by bike would be madness",
        "ideally 30 minutes to Pellam Cross on foot if I must",
        "ideally 30 minutes to Pellam Cross by bike sometimes",
        "ideally 30 minutes to Pellam Cross by bike would suit my ex",
    ],
)
def test_a_way_after_the_place_is_not_read_where_more_is_said_of_it(text: str):
    no_way(text)


@pytest.mark.parametrize(
    ("text", "mode", "minutes"),
    [
        ("ideally 30 minutes to Pellam Cross by bike", "cycle", 30),
        ("ideally 30 minutes to Pellam Cross on foot please", "walk", 30),
        ("ideally 30 minutes to Pellam Cross by bike max", "cycle", 30),
        # That the journey would suit says nothing against the way.
        ("ideally 30 minutes to Pellam Cross on foot if possible", "walk", 30),
        ("ideally 30 minutes to Pellam Cross by bike would suit", "cycle", 30),
        ("a 25 minute walk to Pellam Cross would suit", "walk", 25),
        ("a 25 minute walk to Pellam Cross would be ideal", "walk", 25),
    ],
)
def test_a_way_after_the_place_is_read_where_nothing_more_is_said_of_it(
    text: str, mode: str, minutes: int
):
    (edit,) = journeys(read(text))
    assert (edit["mode"], edit["max_minutes"]) == (mode, minutes)


@pytest.mark.parametrize(
    "text",
    [
        "a walk to Pellam Cross is impossible",
        "walking to Pellam Cross is impossible",
        "walking to Pellam Cross is not an option",
        "a short walk to Pellam Cross terrifies me",
        "I cycle to Pellam Cross when I must",
        "a 20 minute cycle to Pellam Cross scares me",
    ],
)
def test_a_way_before_the_place_is_not_read_where_more_is_said_after_the_place(text: str):
    """What follows the place may say that the way cannot be gone, in words no list holds."""
    no_way(text)


@pytest.mark.parametrize(
    "text",
    [
        "my ex can walk to Pellam Cross",
        "the kids walk to Pellam Cross",
        "my kids can walk to Pellam Cross",
        "so the kids can walk to Pellam Cross",
        "my husband can cycle to Pellam Cross",
        "everyone is able to walk to Pellam Cross",
        "nobody I know would walk to Pellam Cross",
        "my husband can sometimes cycle to Pellam Cross",
        "his walk to Pellam Cross",
        "my ex's walk to Pellam Cross",
        "her cycle to Pellam Cross",
    ],
)
def test_a_way_that_somebody_else_goes_is_not_the_way_of_the_journey(text: str):
    """Who goes that way stands before the words, and only the speaker is one the reader knows."""
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert not [edit for edit in journeys(result) if "mode" in edit]


@pytest.mark.parametrize(
    ("text", "mode"),
    [
        ("I cycle to Pellam Cross, I think", "cycle"),
        ("we walk to Pellam Cross, I think", "walk"),
        ("ideally I can walk to Pellam Cross", "walk"),
        ("ideally we can walk to Pellam Cross", "walk"),
        ("ideally walking distance to Pellam Cross", "walk"),
        ("ideally within walking distance of Pellam Cross", "walk"),
        ("a flat within walking distance of Pellam Cross, I think", "walk"),
        ("somewhere a short walk from Pellam Cross, I think", "walk"),
        # How often or how surely the speaker goes that way.
        ("I can cycle to Pellam Cross, I think", "cycle"),
        ("we both cycle to Pellam Cross", "cycle"),
        ("I sometimes walk to Pellam Cross", "walk"),
        ("I'd rather walk to Pellam Cross", "walk"),
        # What kind of walk it is.
        ("a lovely walk to Pellam Cross", "walk"),
        ("a brisk walk to Pellam Cross", "walk"),
        # A word that turns something else in the clause turns no way.
        ("no pubs but ideally a 25 minute ride to Pellam Cross", "cycle"),
        ("I can't drive so ideally a 25 minute ride to Pellam Cross", "cycle"),
        ("ideally at most a 20 minute walk to Pellam Cross", "walk"),
        # That the way matters says nothing against it.
        ("walking distance to Pellam Cross is a must", "walk"),
        ("walking distance to Pellam Cross is essential", "walk"),
    ],
)
def test_a_way_that_the_speaker_goes_or_that_says_where_a_home_stands_is_still_read(
    text: str, mode: str
):
    (edit,) = journeys(read(text))
    assert edit["mode"] == mode


@pytest.mark.parametrize(
    "text",
    [
        "not by bike to Pellam Cross",
        "never by bike to Pellam Cross",
        "I no longer walk to Pellam Cross",
        "I no longer cycle to Pellam Cross",
        "I can no longer walk to Pellam Cross",
        "no longer walking distance to Pellam Cross",
        "never again cycling to Pellam Cross",
        # Words of doubt, which may turn the way as they may turn a wish.
        "anything but walking distance to Pellam Cross",
        "hardly walking distance to Pellam Cross",
        "sick of the walk to Pellam Cross",
        "fed up with the cycle to Pellam Cross",
    ],
)
def test_a_way_that_a_word_before_it_turns_is_not_offered_as_the_way(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert not [edit for edit in journeys(result) if "mode" in edit]


@pytest.mark.parametrize(
    ("text", "mode", "minutes"),
    [
        ("30 minutes on foot to Pellam Cross", "walk", 30),
        ("30 minutes by bike to Pellam Cross", "cycle", 30),
        ("ideally 25 minutes on foot to Pellam Cross", "walk", 25),
        ("an hour by bike to Pellam Cross", "cycle", 60),
        ("three quarters of an hour on foot to Pellam Cross", "walk", 45),
        ("20 minutes by train to Pellam Cross", "pt", 20),
        ("20 minutes by bus to Pellam Cross", "pt", 20),
        ("1 hour 15 by public transport to Pellam Cross", "pt", 75),
        # The words that say the most a journey may take turn no way.
        ("at most an hour on foot to Pellam Cross", "walk", 60),
        ("no more than an hour on foot to Pellam Cross", "walk", 60),
        ("not more than 30 minutes by bike to Pellam Cross", "cycle", 30),
        ("ideally at most 30 minutes by bike to Pellam Cross", "cycle", 30),
    ],
)
def test_a_way_that_is_said_as_it_is_after_the_place_is_read_before_it_with_its_time(
    text: str, mode: str, minutes: int
):
    """ "30 minutes on foot to" was a journey of 45 minutes by public transport, at one press."""
    result = read(text)
    assert result.operations == NO_OPERATIONS
    (edit,) = journeys(result)
    assert (edit["mode"], edit["max_minutes"]) == (mode, minutes)
    # The offer rests on the time and the way as on the place, so neither is said to be unread.
    assert [text[span.start : span.end] for span in result.unread] in ([], ["ideally"])


@pytest.mark.parametrize(
    "text",
    [
        "20 minutes by bus or on foot to Pellam Cross",
        "20 minutes on foot or by bike to Pellam Cross",
        "20 minutes not on foot to Pellam Cross",
        "20 minutes never by bike to Pellam Cross",
    ],
)
def test_such_a_way_is_not_read_where_another_is_set_beside_it_or_a_word_turns_it(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert not [edit for edit in journeys(result) if "mode" in edit]
