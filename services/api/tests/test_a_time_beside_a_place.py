"""A journey is never offered at the usual minutes with a sentence that says none were given.

Route 1 offered "Cindermoor Works within 40 minutes" as a journey with no time.
It said "You gave no number of minutes, so Burro has used 45.", which was
untrue, and a client that takes what is offered added a journey of 45 minutes
for a person who typed 40. Core now reads a time wherever the words give it to
a place (contract, section 8.2). Where it cannot tell which journey a time is
for, the journey is offered with no time, and the offer says that a time was
given and could not be placed: it never says that the person gave none.

A journey that the words make a limit is offered as a guide too, so that a
client which takes what is offered has a way to take that leaves no area out
on an estimate (ADR 0027). Every sentence of the first list is one the service
was driven with. No call is made: where a model reads, a stand-in hands the
answer to the reader.

Since 2026-09-27 the grammar reads a journey with its place first, so three of
the twelve are plain lists of wishes. Each is applied, at the minutes that were
typed and as firm as its words make it: `test_a_limit_that_stands_after_its_place.py`
holds the rule.
"""

from typing import Any

import pytest
from burro_api.offers import FIRM, GUIDE, MORE
from burro_core.interpret import TIME_NOT_PLACED
from fastapi.testclient import TestClient

from .support import WORKS, client_for, make_deps, model_commute, model_output, through_the_route

QUARTER = "syn-p0018"  # Tallowgate Guild Quarter
GAVE_NONE = "You gave no number of minutes"
NOT_PLACED = (
    "Burro could not tell whether the minutes you gave are for this journey, so it has used 45."
)
NO_WAY_SAID = "You did not say how you would travel, so Burro has assumed public transport."

# What was typed, where the journey leads, its minutes, whether the words make them a limit,
# and how the words say it is made.
DRIVEN = [
    ("Cindermoor Works within 40 minutes", WORKS, 40, True, "unchanged"),
    ("Cindermoor Works, 40 minutes", WORKS, 40, False, "unchanged"),
    ("to Cindermoor Works in 40 minutes", WORKS, 40, False, "unchanged"),
    ("get to Cindermoor Works in 40 minutes or less", WORKS, 40, False, "unchanged"),
    ("my commute to Cindermoor Works should be under 40 minutes", WORKS, 40, False, "unchanged"),
    ("40 minutes or so to Cindermoor Works", WORKS, 40, False, "unchanged"),
    ("40 minutes each way to Cindermoor Works", WORKS, 40, False, "unchanged"),
    ("40 mins door to door to Cindermoor Works", WORKS, 40, False, "unchanged"),
    ("35 minutes on the tube to Tallowgate Guild Quarter", QUARTER, 35, False, "pt"),
    ("35 minutes on the bus to Tallowgate Guild Quarter", QUARTER, 35, False, "pt"),
    ("no more than 35 minutes on the tube to Tallowgate Guild Quarter", QUARTER, 35, True, "pt"),
    ("35 minute commute, Tallowgate Guild Quarter", QUARTER, 35, False, "unchanged"),
]
# Of the twelve, those that the rules apply: the place and then its time, and the name of a
# place with a time beside it that is said apart from any place.
NOW_PLAIN = frozenset(
    {
        "Cindermoor Works within 40 minutes",
        "Cindermoor Works, 40 minutes",
        "35 minute commute, Tallowgate Guild Quarter",
    }
)
OFFERED = [row for row in DRIVEN if row[0] not in NOW_PLAIN]
APPLIED = [row for row in DRIVEN if row[0] in NOW_PLAIN]


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def read(client: TestClient, text: str) -> dict[str, Any]:
    response = client.post("/v1/interpret", json={"text": text})
    assert response.status_code == 200
    return response.json()["data"]


def ways_of(offer: dict[str, Any]) -> list[tuple[str, str, int, str, str]]:
    """Each way of a journey: which it is, where it leads, and what it would send."""
    return [
        (way["id"], edit["place_id"], edit["max_minutes"], edit["strictness"], edit["mode"])
        for way in offer["choices"]
        for edit in way["operations"]["commute_ops"]
    ]


def test_three_of_the_twelve_are_plain_and_the_rest_are_offered():
    assert (len(DRIVEN), len(APPLIED), len(OFFERED)) == (12, 3, 9)


@pytest.mark.parametrize(("text", "place", "minutes", "firm", "mode"), APPLIED)
def test_route_1_applies_a_plain_journey_at_the_minutes_that_were_typed(
    client: TestClient, text: str, place: str, minutes: int, firm: bool, mode: str
):
    found = read(client, text)

    assert (found["status"], found["suggestions"], found["unread"]) == ("ok", [], [])
    [journey] = found["operations"]["commute_ops"]
    limit = "hard" if firm else "unchanged"
    assert (journey["place_id"], journey["max_minutes"]) == (place, minutes)
    assert (journey["strictness"], journey["mode"]) == (limit, mode)
    # It is never said that the person gave no number of minutes: they gave one.
    assert "max_minutes" not in [assumed["code"] for assumed in found["assumptions"]]
    [held] = found["spec"]["commutes"]
    firmness = "hard" if firm else "soft"
    assert (held["place_id"], held["max_minutes"], held["strictness"]) == (place, minutes, firmness)


@pytest.mark.parametrize(("text", "place", "minutes", "firm", "mode"), OFFERED)
def test_route_1_offers_the_journey_at_the_minutes_that_were_typed(
    client: TestClient, text: str, place: str, minutes: int, firm: bool, mode: str
):
    found = read(client, text)

    assert (found["status"], found["applied"]) == ("suggest", [])
    [journey] = found["suggestions"]
    assert journey["target"] == "commute"
    if firm:
        # The words make it a limit. It is offered as one, and as a guide, with no guess,
        # and no press takes a limit that was not plainly said with others.
        assert ways_of(journey) == [
            (FIRM, place, minutes, "hard", mode),
            (GUIDE, place, minutes, "soft", mode),
        ]
        assert journey["add_all"] == ""
    else:
        assert ways_of(journey) == [(MORE, place, minutes, "unchanged", mode)]
        # "Should" is a word that asks, and one press takes nothing from a clause that
        # holds a sign of doubt. The journey is offered all the same.
        assert journey["add_all"] == ("" if "should" in text else MORE)
    assert not [way for way in journey["choices"] if way["guess"]]
    assert f"at most {minutes} minutes" in journey["does"]
    # It never says that the person gave none, and says that no way was named only where
    # none was.
    assert not [line for line in journey["said"] if GAVE_NONE in line]
    assert (NO_WAY_SAID in journey["said"]) == (mode == "unchanged")
    assert journey["note"] == ""


@pytest.mark.parametrize(("text", "place", "minutes", "firm", "mode"), OFFERED)
def test_the_journey_that_is_taken_holds_the_minutes_and_leaves_no_area_out(
    client: TestClient, text: str, place: str, minutes: int, firm: bool, mode: str
):
    """As a client takes it that takes what is offered: the guide, of a limit."""
    found = read(client, text)
    [journey] = found["suggestions"]
    [taken] = [way for way in journey["choices"] if way["id"] in (GUIDE, MORE)]

    body = {"spec": found["spec"], "operations": taken["operations"], "limit": 5}
    ranked = client.post("/v1/rank", json=body).json()["data"]

    assert ranked["rejected"] == []
    [held] = ranked["spec"]["commutes"]
    assert (held["place_id"], held["max_minutes"], held["strictness"]) == (place, minutes, "soft")
    assert ranked["filtered"] == []


@pytest.mark.parametrize(
    "text",
    [
        "Cindermoor Works and Pellam Infirmary, honestly, 40 minutes max",
        "Cindermoor Works, 40 minutes, or 50 minutes",
        "Cindermoor Works, never 40 minutes",
    ],
)
def test_route_1_says_that_it_could_not_tell_which_journey_a_time_is_for(
    client: TestClient, text: str
):
    found = read(client, text)

    journeys = [offer for offer in found["suggestions"] if offer["target"] == "commute"]
    assert journeys
    for journey in journeys:
        # It is offered as a journey that was given no time is, by a press of its own.
        assert [edit[2:4] for edit in ways_of(journey)] == [(0, "unchanged")]
        assert (journey["note"], journey["add_all"]) == (TIME_NOT_PLACED, "")
        assert NOT_PLACED in journey["said"]
        assert not [line for line in journey["said"] if GAVE_NONE in line]
    assert found["spec"]["commutes"] == []


def test_a_journey_that_was_given_no_time_still_says_so(client: TestClient):
    found = read(client, "I work at Cindermoor Works, I think")

    [journey] = found["suggestions"]
    assert ways_of(journey) == [(MORE, WORKS, 0, "unchanged", "unchanged")]
    assert [line for line in journey["said"] if GAVE_NONE in line]


def test_a_model_may_read_a_time_that_the_rules_could_not_place():
    """Which journey a time is for is a model's to read, and the place is offered once."""
    text = "Cindermoor Works and Pellam Infirmary, honestly, 40 minutes max"
    journey = model_commute(destination_text="Cindermoor Works", max_minutes=40, words=text)

    found = through_the_route(model_output(commute_ops=[journey]), text)

    journeys = [offer for offer in found["suggestions"] if offer["target"] == "commute"]
    assert sorted(offer["label"] for offer in journeys) == ["Cindermoor Works", "Pellam Infirmary"]
    by_place = {offer["label"]: offer for offer in journeys}
    assert {edit[2] for edit in ways_of(by_place["Cindermoor Works"])} == {40}
    assert by_place["Cindermoor Works"]["note"] == ""
    # What the model did not read is as the rules gave it.
    assert [edit[2] for edit in ways_of(by_place["Pellam Infirmary"])] == [0]
    assert by_place["Pellam Infirmary"]["note"] == TIME_NOT_PLACED
    assert found["operations"]["commute_ops"] == []
