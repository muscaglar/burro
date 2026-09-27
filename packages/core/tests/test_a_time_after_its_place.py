"""A place may stand before the time of the journey to it, in a plain prompt.

The grammar read a journey with its time first, "within 40 minutes of
Cindermoor Works", and after words that reach a place, "get to Cindermoor
Works within 40 minutes". With the place first and nothing to lead it in,
"Cindermoor Works within 40 minutes", the prompt was not plain. The journey was
offered, as a firm limit and as a guide, and whoever takes what is offered and
asks nothing took the guide: an area that is 63 minutes away was ranked under a
limit of 40.

A journey is now read with its place first as it is read with its time first:
the whole name of a place, and then the time, in the words the grammar reads of
a time anywhere. What makes the time a limit is `FIRM_OF_MINUTES` against its
own number, as it was. The name of a place that stands in a part of the
sentence of its own is a journey only where a time that is said apart from any
place stands straight before it or straight after it, which is then the time
of it, and only where the name is no area's too: "Foxholt, 30 minutes max" may
as well say where a person wants to live.

Every name and every sentence here is made up.
"""

import pytest
from burro_core.ids import InterpretStatus, ModeChoice, StrictnessChoice, Tenure
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter
from burro_core.ops import NO_OPERATIONS
from burro_core.spec import default_spec
from burro_core.vocabulary import CAPS, CAPS_FIRMLY, FIRM_OF_MINUTES

from .support import fixture_release

RENTER = default_spec(Tenure.RENT)
READER = RuleInterpreter()
HARD, AS_IT_IS = StrictnessChoice.HARD, StrictnessChoice.UNCHANGED
NO_WAY, BY_BIKE, ON_FOOT = ModeChoice.UNCHANGED, ModeChoice.CYCLE, ModeChoice.WALK
Journey = tuple[str, int, StrictnessChoice, ModeChoice]


def place(name: str) -> str:
    (found,) = (one.place_id for one in fixture_release().places if one.name == name)
    return found


WORKS = place("Cindermoor Works")
MARKET = place("Foxholt Market")
INFIRMARY = place("Pellam Infirmary")
QUARTER = place("Tallowgate Guild Quarter")
FOXHOLT = place("Foxholt")


def read(text: str) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=fixture_release()))


def applied(result: InterpretResult) -> list[Journey]:
    return [
        (edit.place_id, edit.max_minutes, edit.strictness, edit.mode)
        for edit in result.operations.commute_ops
    ]


# What was typed with the place first, the same words with the time first, and the journey.
IN_EITHER_ORDER: list[tuple[str, str, Journey]] = [
    (
        "Cindermoor Works within 40 minutes",
        "within 40 minutes of Cindermoor Works",
        (WORKS, 40, HARD, NO_WAY),
    ),
    (
        "Foxholt Market within 30 minutes",
        "within 30 minutes of Foxholt Market",
        (MARKET, 30, HARD, NO_WAY),
    ),
    (
        "Cindermoor Works, 40 minutes max",
        "40 minutes max to Cindermoor Works",
        (WORKS, 40, HARD, NO_WAY),
    ),
    (
        "Cindermoor Works 40 minutes max",
        "40 minutes max to Cindermoor Works",
        (WORKS, 40, HARD, NO_WAY),
    ),
    (
        "Cindermoor Works in no more than 40 minutes",
        "no more than 40 minutes to Cindermoor Works",
        (WORKS, 40, HARD, NO_WAY),
    ),
    (
        "the Cindermoor Works within an hour",
        "within an hour of the Cindermoor Works",
        (WORKS, 60, HARD, NO_WAY),
    ),
    (
        "Pellam Infirmary at most 35 minutes by bike",
        "at most 35 minutes to Pellam Infirmary by bike",
        (INFIRMARY, 35, HARD, BY_BIKE),
    ),
    (
        "Pellam Infirmary by bike within 35 minutes",
        "within 35 minutes of Pellam Infirmary by bike",
        (INFIRMARY, 35, HARD, BY_BIKE),
    ),
    (
        "Cindermoor Works, 35-40 minutes",
        "35-40 minutes to Cindermoor Works",
        (WORKS, 40, HARD, NO_WAY),
    ),
    (
        "Cindermoor Works in under 40 minutes",
        "under 40 minutes to Cindermoor Works",
        (WORKS, 40, AS_IT_IS, NO_WAY),
    ),
    (
        "Cindermoor Works in 40 minutes",
        "40 minutes to Cindermoor Works",
        (WORKS, 40, AS_IT_IS, NO_WAY),
    ),
    (
        "Cindermoor Works, 40 minutes",
        "40 minutes to Cindermoor Works",
        (WORKS, 40, AS_IT_IS, NO_WAY),
    ),
    (
        "Cindermoor Works, a 40 minute commute",
        "a 40 minute commute to Cindermoor Works",
        (WORKS, 40, AS_IT_IS, NO_WAY),
    ),
    (
        "Tallowgate Guild Quarter, a 25 minute walk",
        "a 25 minute walk to Tallowgate Guild Quarter",
        (QUARTER, 25, AS_IT_IS, ON_FOOT),
    ),
    (
        "40 minutes max, Cindermoor Works",
        "40 minutes max to Cindermoor Works",
        (WORKS, 40, HARD, NO_WAY),
    ),
    # A name that is an area's too is a place to reach where a time is said of it.
    ("Foxholt within 30 minutes", "within 30 minutes of Foxholt", (FOXHOLT, 30, HARD, NO_WAY)),
]


@pytest.mark.parametrize(("after", "before", "journey"), IN_EITHER_ORDER)
def test_a_journey_is_read_with_its_place_first_as_it_is_with_its_time_first(
    after: str, before: str, journey: Journey
):
    first, second = read(before), read(after)

    assert (first.status, applied(first)) == (InterpretStatus.OK, [journey])
    assert (second.status, applied(second)) == (InterpretStatus.OK, [journey])
    assert second.assumptions == first.assumptions
    assert (second.suggestions, second.unread, second.unmet) == ((), (), ())
    # It rests on every word of it, and on nothing else.
    stands = sorted((rests.start, rests.end) for rests in second.rests_on)
    assert (stands[0][0], stands[-1][1]) == (0, len(after))


LED_IN: list[tuple[str, Journey]] = [
    ("I commute to Cindermoor Works within 40 minutes", (WORKS, 40, HARD, NO_WAY)),
    ("I work at Cindermoor Works in under 40 minutes", (WORKS, 40, AS_IT_IS, NO_WAY)),
    ("I cycle to Foxholt Market in under 20 minutes", (MARKET, 20, AS_IT_IS, BY_BIKE)),
    ("near Cindermoor Works within 40 minutes", (WORKS, 40, HARD, NO_WAY)),
    ("I want Cindermoor Works within 40 minutes", (WORKS, 40, HARD, NO_WAY)),
    ("somewhere with Cindermoor Works within 40 minutes", (WORKS, 40, HARD, NO_WAY)),
    ("Cindermoor Works within 40 minutes please", (WORKS, 40, HARD, NO_WAY)),
]


@pytest.mark.parametrize(("text", "journey"), LED_IN)
def test_the_time_may_follow_the_place_whatever_leads_the_place_in(text: str, journey: Journey):
    found = read(text)

    assert (found.status, applied(found), found.suggestions) == (InterpretStatus.OK, [journey], ())


def test_it_is_applied_beside_the_other_wishes_of_a_plain_list():
    found = read("leafy and quiet, Cindermoor Works within 40 minutes, 2 bed up to £1,500 a month")

    assert (found.status, found.suggestions) == (InterpretStatus.OK, ())
    assert applied(found) == [(WORKS, 40, HARD, NO_WAY)]
    assert [edit.tag_id.value for edit in found.operations.tag_ops] == [
        "leafy",
        "quiet_residential",
    ]
    [budget] = found.operations.budget_ops
    assert (budget.amount, budget.strictness) == (1500, HARD)


BESIDE_OTHER_WISHES: list[tuple[str, Journey]] = [
    # The time follows the name, whatever stands after the time.
    ("Cindermoor Works, 10 minutes max, a park", (WORKS, 10, HARD, NO_WAY)),
    ("leafy, Cindermoor Works, 40 minutes max", (WORKS, 40, HARD, NO_WAY)),
    # It stands before the name, after a thing that no time is said of.
    ("leafy, 40 minutes max, Cindermoor Works", (WORKS, 40, HARD, NO_WAY)),
    ("a gym, 40 minutes max, Cindermoor Works", (WORKS, 40, HARD, NO_WAY)),
]


@pytest.mark.parametrize(("text", "journey"), BESIDE_OTHER_WISHES)
def test_the_time_beside_a_name_is_the_time_of_it_beside_other_wishes(text: str, journey: Journey):
    found = read(text)

    assert (found.status, applied(found), found.suggestions) == (InterpretStatus.OK, [journey], ())
    assert len(found.operations.weight_ops) + len(found.operations.tag_ops) == 1


def test_two_places_may_each_hold_a_time_of_their_own():
    found = read("Cindermoor Works within 40 minutes, Pellam Infirmary in under 30 minutes")

    assert applied(found) == [(WORKS, 40, HARD, NO_WAY), (INFIRMARY, 30, AS_IT_IS, NO_WAY)]


def test_what_makes_minutes_firm_is_the_one_list_wherever_the_place_stands():
    """Every word that caps a number, after a place: firm by the list, and by nothing else."""
    for cap in sorted(CAPS | CAPS_FIRMLY):
        found = read(f"Cindermoor Works {cap} 40 minutes")
        firm = HARD if cap in FIRM_OF_MINUTES else AS_IT_IS
        assert applied(found) == [(WORKS, 40, firm, NO_WAY)], cap
    assert {"under", "up to", "less than", "about", "around"} & FIRM_OF_MINUTES == set()


NOT_PLAIN = [
    # The name of a place alone says nothing of what is wanted of it.
    "Cindermoor Works",
    "leafy, Cindermoor Works",
    "Cindermoor Works by bike",
    # Its sentence says no time apart from any place, so there is none to be the time of it.
    "Cindermoor Works, 30 minutes to Pellam Infirmary",
    "Cindermoor Works. 40 minutes max.",
    "Cindermoor Works and Pellam Infirmary within 40 minutes",
    # The time stands further off, and may be said of what stands between them.
    "Cindermoor Works, a park, 10 minutes max",
    "10 minutes max, a park, Cindermoor Works",
    "Cindermoor Works, leafy and quiet, a 40 minute commute",
    # The time stands before the name and after a thing that is some way off, or a place.
    "a park, 10 minutes max, Cindermoor Works",
    "near a station, 10 minutes max, Cindermoor Works",
    "I work at Pellam Infirmary, a 40 minute commute, Cindermoor Works",
    # A word joins the name and the time, and says something of its own.
    "40 minutes max or Cindermoor Works",
    "at most 30 minutes but Cindermoor Works",
    "Cindermoor Works and 40 minutes max",
    # One time and two places: which journey it is for is the person's to say.
    "Cindermoor Works, Pellam Infirmary, 40 minutes max",
    "Cindermoor Works, 40 minutes max, Pellam Infirmary",
    "Cindermoor Works, a 40 minute commute, Pellam Infirmary",
    # A name that is an area's too, apart from the time: it may say where to live.
    "Foxholt, 30 minutes max",
    "Foxholt, leafy, a 30 minute commute",
    # More is said after the time, which the grammar does not read.
    "Cindermoor Works within 40 minutes of Pellam Infirmary",
    "Cindermoor Works 40 minutes away",
    "Cindermoor Works within 40 minutes would be a nightmare",
    # A least is no most, and a number of something else is no time.
    "Cindermoor Works, at least 40 minutes",
    "Cindermoor Works in 3 weeks",
    "Cindermoor Works, 2 bed",
    # Two times said of one journey.
    "Cindermoor Works within 40 minutes, 30 minutes max",
]


@pytest.mark.parametrize("text", NOT_PLAIN)
def test_a_name_with_no_time_of_its_own_is_never_applied(text: str):
    found = read(text)

    assert found.operations == NO_OPERATIONS


def test_a_time_after_a_place_that_is_commuted_from_is_offered_and_never_applied():
    """It may be where the person lives now."""
    found = read("I commute from Cindermoor Works in under 40 minutes")

    assert found.operations == NO_OPERATIONS
    [offered] = found.suggestions
    [edit] = offered.choices[0].operations.commute_ops
    assert (edit.place_id, edit.max_minutes) == (WORKS, 40)
