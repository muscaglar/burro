"""A time or a cue before part of a name says a journey, and never a rule for an area.

"Leafy and quiet, 30 minutes to Pellam" is a plain list, and the reader asks
which place is meant: three places bear the name. With one word after it that
the reader does not know, "honestly", the list is not plain, and the journey
was dropped. "Pellam" is another name of the area Pellam Cross, so the reader
offered a rule for the area in the journey's place, to look only there or to
leave it out, and said that "30 minutes to" was unread. Nobody said either.

Where the part of the sentence that says the journey is one the grammar makes
by itself, the reader now asks which place is meant, as it does in a plain
list. Where it is not, the name is no rule for the area all the same: the
words before it expect a place to reach, so nothing is offered for the name,
and its words are said to be unread. Every name and every sentence here is
made up, and the first of each list is one the website was driven with.
"""

import pytest
from burro_core.ids import InterpretStatus, ModeChoice, OpsGroup, StrictnessChoice, Tenure
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter
from burro_core.reducer import apply
from burro_core.spec import default_spec

from .support import fixture_release

RENTER = default_spec(Tenure.RENT)
READER = RuleInterpreter()
PLACES = {place.name for place in fixture_release().places}
AREAS = {area.name for area in fixture_release().neighbourhoods}
# Three places bear the name, and none is called by it alone. One area answers to it.
PELLAM = ["Pellam Cross", "Pellam Exchange", "Pellam Infirmary"]
assert set(PELLAM) <= PLACES and "Pellam" not in PLACES
# The name of an area alone, which one place bears a part of.
assert "Alderwick" in AREAS and "Alderwick" not in PLACES
HARD, AS_IT_IS = StrictnessChoice.HARD, StrictnessChoice.UNCHANGED
NO_WAY, ON_FOOT, BY_BIKE = ModeChoice.UNCHANGED, ModeChoice.WALK, ModeChoice.CYCLE


def read(text: str) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=fixture_release()))


def offered(result: InterpretResult) -> set[str]:
    return {found.target for found in result.suggestions}


def unread(text: str, result: InterpretResult) -> str:
    return " / ".join(text[span.start : span.end] for span in result.unread)


# What was typed, the plain list that says the same journey, and the journey: its minutes,
# whether the words make them a limit, and how they say it is made.
ASKED = [
    (
        "Leafy and quiet, 30 minutes to Pellam, honestly",
        "Leafy and quiet, 30 minutes to Pellam",
        (30, AS_IT_IS, NO_WAY),
    ),
    ("honestly, I work at Pellam", "I work at Pellam", (0, AS_IT_IS, NO_WAY)),
    ("zebra, within 40 minutes of Pellam", "within 40 minutes of Pellam", (40, HARD, NO_WAY)),
    ("a 25 minute walk to Pellam, honestly", "a 25 minute walk to Pellam", (25, AS_IT_IS, ON_FOOT)),
    (
        "zebra and 30 minutes to Pellam by bike",
        "30 minutes to Pellam by bike",
        (30, AS_IT_IS, BY_BIKE),
    ),
    ("30 minutes to Alderwick, honestly", "30 minutes to Alderwick", (30, AS_IT_IS, NO_WAY)),
]


@pytest.mark.parametrize(("text", "plain", "journey"), ASKED)
def test_a_journey_to_part_of_a_name_is_asked_about_as_it_is_in_a_plain_list(
    text: str, plain: str, journey: tuple[int, StrictnessChoice, ModeChoice]
):
    result, listed = read(text), read(plain)

    assert result.status is listed.status is InterpretStatus.CLARIFY
    (asked,) = result.clarify
    (as_listed,) = listed.clarify
    assert (asked.group, asked.options) == (OpsGroup.COMMUTE, as_listed.options)
    assert asked.options
    edit = result.operations.commute_ops[asked.index]
    assert edit.place_id == ""
    assert (edit.max_minutes, edit.strictness, edit.mode) == journey
    # It rests on the words the plain list rests it on, so none of them is said to be unread.
    said = [text[rests.start : rests.end] for rests in result.rests_on]
    assert said == [
        plain[rests.start : rests.end]
        for rests in listed.rests_on
        if rests.group is OpsGroup.COMMUTE
    ]
    assert not any(
        span.start < rests.end and rests.start < span.end
        for span in result.unread
        for rests in result.rests_on
    )


@pytest.mark.parametrize(("text", "plain", "journey"), ASKED)
def test_a_journey_to_part_of_a_name_is_no_rule_for_the_area_that_answers_to_it(
    text: str, plain: str, journey: tuple[int, StrictnessChoice, ModeChoice]
):
    result = read(text)

    assert "area" not in offered(result)
    assert not result.operations.area_ops
    # The question adds nothing until the person says which place is meant.
    taken = apply(RENTER, result.operations, fixture_release())
    assert taken.spec.commutes == () and taken.spec.areas == ()


def test_the_first_place_that_is_asked_about_bears_most_of_the_name():
    (asked,) = read("Leafy and quiet, 30 minutes to Pellam, honestly").clarify

    assert [option.name for option in asked.options] == PELLAM


# The part that holds the name is no journey the grammar makes by itself: somebody else is
# named in it, or a word the reader does not know stands in it.
NOT_ASKED = [
    "my mum lives 30 minutes to Pellam",
    "we both work at Pellam, honestly",
    "zebra 30 minutes to Pellam",
    "I used to commute to Pellam",
    "my partner works at Alderwick",
]


@pytest.mark.parametrize("text", NOT_ASKED)
def test_a_name_where_a_place_to_reach_is_expected_is_no_rule_and_is_said_to_be_unread(
    text: str,
):
    result = read(text)

    assert result.clarify == () and not any(result.operations.model_dump().values())
    assert "area" not in offered(result) and "commute" not in offered(result)
    assert text.split()[-1].removesuffix(",") in unread(text, result) or "Pellam" in unread(
        text, result
    )


# A sentence that holds a word for staying away is asked nothing of: the place is one to
# keep from, and a question that is answered adds a journey to it.
@pytest.mark.parametrize(
    "text",
    ["far from my ex, 30 minutes to Pellam", "at least 30 minutes to Pellam, honestly"],
)
def test_a_sentence_that_says_to_stay_away_asks_about_no_place(text: str):
    result = read(text)

    assert result.clarify == () and not result.operations.commute_ops
    assert "commute" not in offered(result)


STILL_A_RULE = ["Pellam", "in Pellam", "I want to live in Pellam", "I like Alderwick"]


@pytest.mark.parametrize("text", STILL_A_RULE)
def test_a_name_that_nothing_leads_in_as_a_place_to_reach_is_offered_as_a_rule_as_it_was(
    text: str,
):
    result = read(text)

    assert result.clarify == ()
    assert "area" in offered(result)


# The whole of a name is a journey to the place, offered as it was.
@pytest.mark.parametrize(
    "text",
    ["Leafy and quiet, 30 minutes to Pellam Cross, honestly", "honestly, I work at Pellam Cross"],
)
def test_a_journey_to_the_whole_of_a_name_is_offered_as_it_was(text: str):
    result = read(text)

    assert result.clarify == () and not result.operations.commute_ops
    (journey,) = (found for found in result.suggestions if found.target == "commute")
    assert journey.label == "Pellam Cross"


def test_a_name_no_place_bears_a_part_of_is_said_to_be_unread_as_it_was():
    text = "Leafy, 30 minutes to Zorbleton, honestly"

    result = read(text)

    assert result.clarify == () and not result.operations.commute_ops
    assert "Zorbleton" in unread(text, result)
