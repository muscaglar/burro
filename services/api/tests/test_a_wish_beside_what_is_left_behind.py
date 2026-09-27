"""A wish that stands beside what a person is leaving, in one run of words with no mark.

"I'm tired of the city and want somewhere leafy and quiet." A word that turns
was held to lead up to every thing after it until a mark, so the wish was read
as turned away: the service offered no way to count it, and said "Burro read
your words as saying that you do not want this". It reached back too: of "I
want somewhere leafy and quiet because I hate the city" the quiet was lost.

A word that turns leads up to the thing it is said of, and no further. A wish
of the speaker's own, "but", "because" and a turn of its own each begin what
is said next (contract, section 8.2; ADR 0012, as amended on 2026-09-27).

The service was driven with the first twenty-five on 2026-09-27: everything
that was wanted counted in four of them. Every sentence here is made up.
"""

from typing import Any

import pytest
from burro_core.interpret import NOT_SAID_TO_BE_WANTED, NOT_WANTED, NOT_WANTED_AND_COUNTED
from fastapi.testclient import TestClient

from .support import client_for, make_deps

LEAFY, QUIET, PACE, AGE = "tag:leafy", "tag:quiet_residential", "tag:pace", "tag:built_age"
PARK, STATION, CULTURE, WATER = (
    "feature:park_proximity",
    "feature:station_walk",
    "feature:culture_venues_per_homes",
    "feature:water_access",
)
PUBS, FOOD = "feature:venue_evening_per_homes", "feature:venue_food_drink_per_homes"
NOISE, AIR, TRAFFIC = "feature:noise_exposure", "feature:air_no2", "feature:road_traffic_nearby"
MORE, LESS, OFF = "more", "less", "off"
SAYS_NOT_WANTED = "Burro read your words as saying that you do not want this"


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def read(client: TestClient, text: str) -> dict[str, dict[str, Any]]:
    """What is offered of a sentence, by what each offer is of. Nothing of it is applied."""
    response = client.post("/v1/interpret", json={"text": text})
    assert response.status_code == 200, response.text
    found = response.json()["data"]
    assert not any(found["operations"].values()), text
    return {offer["target"]: offer for offer in found["suggestions"]}


def ways(offer: dict[str, Any]) -> list[str]:
    return [way["id"] for way in offer["choices"] if way["id"] != "ignore"]


def guess(offer: dict[str, Any]) -> list[str]:
    return [way["id"] for way in offer["choices"] if way["guess"]]


def taken(offer: dict[str, Any]) -> str | None:
    """The way of an offer that a client takes which asks nothing, as the website chooses it."""

    def stops(way: dict[str, Any]) -> bool:
        wishes = [*way["operations"]["weight_ops"], *way["operations"]["tag_ops"]]
        return bool(wishes) and all(edit["action"] == "remove" for edit in wishes)

    if offer["only_by_choice"]:
        return None
    open_to = [way for way in offer["choices"] if way["id"] != "ignore" and not stops(way)]
    said = [way for way in open_to if offer["add_all"] and way["id"] == offer["add_all"]]
    guessed = [way for way in open_to if way["guess"]]
    if said or guessed:
        return (said or guessed)[0]["id"]
    more = [way for way in open_to if way["direction"] == "more"]
    less = [way for way in open_to if way["direction"] == "less"]
    if more and less:
        return None
    return (more or open_to or [{"id": None}])[0]["id"]


# --- What is wanted, after what is left behind --------------------------------------------

# The sentences the service was driven with, and what a careful person would say is wanted.
WANTED_AFTER: list[tuple[str, dict[str, str]]] = [
    ("I'm tired of the city and want somewhere leafy and quiet", {LEAFY: MORE, QUIET: MORE}),
    ("We are tired of noise and would like somewhere leafy", {LEAFY: MORE}),
    ("I hate my commute and want to be near a park", {PARK: MORE}),
    ("I'm sick of the traffic so I want quiet streets and a park", {QUIET: MORE, PARK: MORE}),
    (
        "fed up with the noise here and looking for somewhere leafy near a station",
        {LEAFY: MORE, STATION: MORE},
    ),
    ("I can't stand my flat and want somewhere leafy", {LEAFY: MORE}),
    ("I never want to see another pub but I love parks", {PARK: MORE}),
    ("I hate where I live now and want somewhere with a park", {PARK: MORE}),
    ("I'm done with flatshares and want a quiet street near a park", {QUIET: MORE, PARK: MORE}),
    ("tired of long journeys so I need to be near a station", {STATION: MORE}),
    ("I hate driving so I need to be near a station", {STATION: MORE}),
    ("I don't like my area and want somewhere with more culture", {CULTURE: MORE}),
    ("I can't bear the noise any more and want somewhere leafy", {LEAFY: MORE}),
    (
        "we dislike the suburbs and want somewhere with pubs and restaurants",
        {PUBS: MORE, FOOD: MORE},
    ),
    ("I hate noise and love parks", {PARK: MORE, NOISE: LESS}),
    ("I hate noise but want a park nearby", {PARK: MORE, NOISE: LESS}),
    ("never again a basement flat, I want a park nearby", {PARK: MORE}),
    ("I'm bored of where I live and want somewhere leafy", {LEAFY: MORE}),
    ("I can't stand the pollution and want a park", {PARK: MORE, AIR: LESS}),
    ("sick of the city, we want somewhere leafy with a park", {LEAFY: MORE, PARK: MORE}),
    ("I hate my landlord and want somewhere leafy near a station", {LEAFY: MORE, STATION: MORE}),
    ("We hate moving and want to settle somewhere leafy", {LEAFY: MORE}),
    ("I dislike long commutes and want a park and a station nearby", {PARK: MORE, STATION: MORE}),
    (
        "fed up with my flat, looking for somewhere historic by the river",
        {AGE: MORE, WATER: MORE},
    ),
    ("I can't stand crowds and want somewhere leafy", {LEAFY: MORE}),
    # It reaches back no further either: what is hated stands after "because".
    ("I want somewhere leafy and quiet because I hate the city", {LEAFY: MORE, QUIET: MORE}),
    ("I need a park because I can't stand being indoors", {PARK: MORE}),
    ("We'd like somewhere lively because we are bored of the suburbs", {PACE: MORE}),
]


@pytest.mark.parametrize(("text", "wanted"), WANTED_AFTER)
def test_a_wish_that_stands_beside_what_is_left_behind_is_taken_as_a_wish(
    client: TestClient, text: str, wanted: dict[str, str]
):
    found = read(client, text)

    for target, way in wanted.items():
        assert taken(found[target]) == way, (text, target)
        assert found[target]["only_by_choice"] is False, (text, target)


@pytest.mark.parametrize(("text", "wanted"), WANTED_AFTER)
def test_nothing_that_was_wanted_is_said_to_be_not_wanted(
    client: TestClient, text: str, wanted: dict[str, str]
):
    found = read(client, text)

    for target in wanted:
        assert SAYS_NOT_WANTED not in found[target]["note"], (text, target)
        assert NOT_SAID_TO_BE_WANTED not in found[target]["note"], (text, target)


def test_the_way_the_words_give_of_such_a_wish_is_the_guess(client: TestClient):
    found = read(client, "we dislike the suburbs and want somewhere with pubs and restaurants")

    # Each runs two ways, so a client that asks nothing takes it only where it is marked.
    for target in (PUBS, FOOD):
        assert ways(found[target]) == [MORE, LESS]
        assert guess(found[target]) == [MORE]


# --- What the words turn away stays turned away ---------------------------------------------

TURNED: list[tuple[str, str, list[str]]] = [
    # The five sentences the work of the night before was for.
    ("I hate pubs", PUBS, [MORE, LESS]),
    ("I never use the station", STATION, [OFF]),
    ("I hate culture", CULTURE, []),
    ("I can't stand parks", PARK, [OFF]),
    # A turn leads up to the thing it is said of, whatever is wished beside it.
    ("I never want to see another pub but I love parks", PUBS, [MORE, LESS]),
    ("I love parks but I never use the station", STATION, [OFF]),
    ("I want somewhere quiet because I hate pubs", PUBS, [MORE, LESS]),
    ("I'm tired of pubs and want somewhere without bars", PUBS, [MORE, LESS]),
    ("we are sick of parks and never use the station", PARK, [OFF]),
    ("we are sick of parks and never use the station", STATION, [OFF]),
    ("I want a park and I never use the station", STATION, [OFF]),
    # It carries over a word that joins two things, where nothing begins between them.
    ("I hate pubs and bars", PUBS, [MORE, LESS]),
    ("I never use the park or the station", STATION, [OFF]),
    ("I can't stand parks and playgrounds", "feature:play_space_proximity", []),
    # A wish with no speaker of its own begins nothing after "or", which carries a turn.
    ("I don't want pubs or need a station", STATION, [OFF]),
]


@pytest.mark.parametrize(("text", "target", "left"), TURNED)
def test_a_turn_still_leads_up_to_the_thing_it_is_said_of(
    client: TestClient, text: str, target: str, left: list[str]
):
    found = read(client, text)[target]

    assert ways(found) == left, text
    assert guess(found) == []
    assert taken(found) is None
    assert found["add_all"] == ""


def test_a_turn_that_the_rules_read_is_the_guess_as_it_was(client: TestClient):
    station = read(client, "Honestly, no station")[STATION]
    assert ways(station) == [OFF] and guess(station) == [OFF]
    assert station["note"] == NOT_WANTED_AND_COUNTED

    pace = read(client, "Honestly, not buzzy")[PACE]
    assert ways(pace) == [LESS] and guess(pace) == [LESS] and taken(pace) == LESS

    plain = client.post("/v1/interpret", json={"text": "not buzzy"}).json()["data"]
    assert plain["status"] == "ok" and not plain["suggestions"]
    assert [(edit["tag_id"], edit["toward"]) for edit in plain["operations"]["tag_ops"]] == [
        ("pace", "low")
    ]


def test_what_is_turned_away_is_still_said_to_be(client: TestClient):
    assert read(client, "I hate culture")[CULTURE]["note"] == NOT_WANTED
    assert read(client, "I never use the station")[STATION]["note"] == NOT_WANTED_AND_COUNTED
    found = read(client, "I never want to see another pub but I love parks")
    assert found[PARK]["note"] == ""


# --- Whose wish it is ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "target"),
    [
        # Who is hated is somebody else. The wish is the speaker's own.
        ("I hate my landlord and want somewhere leafy near a station", LEAFY),
        ("I can't stand my boss so I need a park to walk in", PARK),
        ("we are fed up with my mum and would like a station nearby", STATION),
    ],
)
def test_a_wish_of_the_speakers_own_is_nobody_elses_whoever_is_named_before_it(
    client: TestClient, text: str, target: str
):
    found = read(client, text)[target]

    assert found["only_by_choice"] is False
    assert taken(found) == MORE


@pytest.mark.parametrize(
    ("text", "target"),
    [
        # Somebody else speaks, and the wish that follows with no speaker is theirs.
        ("My husband hates pubs and would like a station nearby", STATION),
        ("my mum is tired of the city and wants a park", PARK),
        ("My partner can't stand noise and needs a park", PARK),
    ],
)
def test_a_wish_that_follows_what_somebody_else_says_waits_for_the_person(
    client: TestClient, text: str, target: str
):
    found = read(client, text)[target]

    assert found["only_by_choice"] is True
    assert found["note"].endswith(NOT_SAID_TO_BE_WANTED)
    assert guess(found) == [] and taken(found) is None
