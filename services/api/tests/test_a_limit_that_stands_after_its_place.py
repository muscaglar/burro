"""A limit of minutes is as firm after its place as it is before it.

"At most", "max", "no more than" and "within" make minutes firm, and a range of
minutes is firm at its longer end (ADR 0012, "What makes a limit firm"). It was
kept where the limit stood before its place, "within 40 minutes of Cindermoor
Works", and not where it stood after: "Cindermoor Works within 40 minutes" was
offered as a firm limit and as a guide, with neither marked. A client that takes
what is offered and asks nothing then took the guide, and ranked an area that
is 63 minutes away.

A place may now stand before the time of the journey to it, in a plain list of
wishes, and the sentence is applied as the same words are in the other order.
In any other sentence firm is the guess wherever the rules would apply what is
said of the journey, were it all that was typed. What makes a limit firm is as
it was: "under" and "about" make none.

Every sentence here is made up, and the first four are the ones the website was
driven with on 2026-09-27.
"""

from typing import Any

import pytest
from burro_api.offers import FIRM, GUIDE, MORE
from fastapi.testclient import TestClient

from .support import WORKS, client_for, make_deps

MARKET = "syn-p0019"  # Foxholt Market
INFIRMARY = "syn-p0028"  # Pellam Infirmary
FOXHOLT = "syn-p0007"  # Foxholt station, whose name is an area's too
LEAFY, QUIET = "tag:leafy", "tag:quiet_residential"


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def read(client: TestClient, text: str) -> dict[str, Any]:
    response = client.post("/v1/interpret", json={"text": text})
    assert response.status_code == 200, response.text
    return response.json()["data"]


def applied(found: dict[str, Any]) -> list[tuple[str, int, str, str]]:
    """Each journey that was applied: where it leads, its minutes, how firm, and how it is made."""
    return [
        (edit["place_id"], edit["max_minutes"], edit["strictness"], edit["mode"])
        for edit in found["operations"]["commute_ops"]
    ]


def journeys(found: dict[str, Any]) -> list[dict[str, Any]]:
    return [offer for offer in found["suggestions"] if offer["target"] == "commute"]


def ways_of(offer: dict[str, Any]) -> list[tuple[str, bool, int, str]]:
    """Each way of a journey: which it is, whether it is the guess, its minutes and how firm."""
    return [
        (way["id"], way["guess"], edit["max_minutes"], edit["strictness"])
        for way in offer["choices"]
        for edit in way["operations"]["commute_ops"]
    ]


def taken(offer: dict[str, Any]) -> dict[str, Any] | None:
    """The way of a journey that a client takes which asks nothing, as `takes.ts` chooses it.

    The way the service marks as its guess, of a journey that may be a firm
    limit or a guide. Else the way one press may add, else the guide, else
    the one way there is.
    """
    if offer["only_by_choice"]:
        return None
    ways = [way for way in offer["choices"] if way["id"] != "ignore"]
    guessed = [way for way in ways if way["guess"]]
    said = [way for way in ways if offer["add_all"] and way["id"] == offer["add_all"]]
    guides = [way for way in ways if way["id"] == GUIDE]
    found = guessed or said or guides or ways
    return found[0] if found else None


def held_after(client: TestClient, found: dict[str, Any]) -> tuple[list[Any], list[Any]]:
    """The journeys of the search that follows, and the areas a firm limit left out of it."""
    edits: dict[str, list[Any]] = {}
    for offer in found["suggestions"]:
        way = taken(offer) if offer["target"] == "commute" else None
        for group, held in (way or {"operations": {}})["operations"].items():
            edits.setdefault(group, []).extend(held)
    body = {"spec": found["spec"], "limit": 30} | ({"operations": edits} if edits else {})
    response = client.post("/v1/rank", json=body)
    assert response.status_code == 200, response.text
    ranked = response.json()["data"]
    assert ranked["rejected"] == []
    held = [
        (one["place_id"], one["max_minutes"], one["strictness"])
        for one in ranked["spec"]["commutes"]
    ]
    return held, [one for one in ranked["filtered"] if one["reason"] != "over_budget"]


# --- A plain list of wishes is applied, as the same words are in the other order ----------

# What was typed with the place first, the same words with the time first, and the journey
# that both are: where it leads, its minutes, how firm the words make it, and how it is made.
IN_EITHER_ORDER = [
    (
        "Cindermoor Works within 40 minutes",
        "within 40 minutes of Cindermoor Works",
        (WORKS, 40, "hard", "unchanged"),
    ),
    (
        "Foxholt Market within 30 minutes",
        "within 30 minutes of Foxholt Market",
        (MARKET, 30, "hard", "unchanged"),
    ),
    (
        "Cindermoor Works, 40 minutes max",
        "40 minutes max to Cindermoor Works",
        (WORKS, 40, "hard", "unchanged"),
    ),
    (
        "Cindermoor Works in no more than 40 minutes",
        "no more than 40 minutes from Cindermoor Works",
        (WORKS, 40, "hard", "unchanged"),
    ),
    (
        "Pellam Infirmary at most 35 minutes by bike",
        "at most 35 minutes to Pellam Infirmary by bike",
        (INFIRMARY, 35, "hard", "cycle"),
    ),
    (
        "Pellam Infirmary, at the very most 35 minutes",
        "at the very most 35 minutes to Pellam Infirmary",
        (INFIRMARY, 35, "hard", "unchanged"),
    ),
    # A range of minutes is firm at its longer end, with no word against it.
    (
        "Cindermoor Works, 35-40 minutes",
        "35-40 minutes to Cindermoor Works",
        (WORKS, 40, "hard", "unchanged"),
    ),
    # A name that is an area's too is a place to reach where a time is said of it.
    (
        "Foxholt within 30 minutes",
        "within 30 minutes of Foxholt",
        (FOXHOLT, 30, "hard", "unchanged"),
    ),
    # What makes no limit firm makes none after the place either.
    (
        "Cindermoor Works in under 40 minutes",
        "under 40 minutes to Cindermoor Works",
        (WORKS, 40, "unchanged", "unchanged"),
    ),
    (
        "Cindermoor Works in about 40 minutes",
        "about 40 minutes to Cindermoor Works",
        (WORKS, 40, "unchanged", "unchanged"),
    ),
    (
        "Cindermoor Works, 40 minutes",
        "40 minutes to Cindermoor Works",
        (WORKS, 40, "unchanged", "unchanged"),
    ),
    (
        "Cindermoor Works up to 40 minutes",
        "up to 40 minutes to Cindermoor Works",
        (WORKS, 40, "unchanged", "unchanged"),
    ),
]


@pytest.mark.parametrize(("after", "before", "journey"), IN_EITHER_ORDER)
def test_a_time_after_its_place_is_applied_as_the_same_words_are_in_the_other_order(
    client: TestClient, after: str, before: str, journey: tuple[str, int, str, str]
):
    first, second = read(client, before), read(client, after)

    assert (first["status"], applied(first), first["suggestions"]) == ("ok", [journey], [])
    assert (second["status"], applied(second), second["suggestions"]) == ("ok", [journey], [])
    assert second["assumptions"] == first["assumptions"]
    assert (second["unmet"], second["unread"]) == ([], [])
    # Every word of it is what the journey rests on.
    stands = [(rests["start"], rests["end"]) for rests in second["rests_on"]]
    assert (min(stands)[0], max(end for _, end in stands)) == (0, len(after))


# A journey that a word leads in, with its time after the place.
LED_IN = [
    ("I commute to Cindermoor Works within 40 minutes", (WORKS, 40, "hard", "unchanged")),
    ("I work at Cindermoor Works, no more than 40 minutes", (WORKS, 40, "hard", "unchanged")),
    ("I cycle to Foxholt Market in under 20 minutes", (MARKET, 20, "unchanged", "cycle")),
    ("near Cindermoor Works, within 40 minutes", (WORKS, 40, "hard", "unchanged")),
]


@pytest.mark.parametrize(("text", "journey"), LED_IN)
def test_a_journey_that_a_word_leads_in_holds_the_limit_that_stands_after_its_place(
    client: TestClient, text: str, journey: tuple[str, int, str, str]
):
    found = read(client, text)

    assert (found["status"], applied(found), found["suggestions"]) == ("ok", [journey], [])


def test_a_firm_limit_after_its_place_is_applied_beside_the_wishes_of_a_plain_list(
    client: TestClient,
):
    found = read(client, "leafy and quiet, Cindermoor Works within 40 minutes")

    assert (found["status"], found["suggestions"]) == ("ok", [])
    assert applied(found) == [(WORKS, 40, "hard", "unchanged")]
    assert [edit["tag_id"] for edit in found["operations"]["tag_ops"]] == [
        "leafy",
        "quiet_residential",
    ]


@pytest.mark.parametrize(
    "text", ["Cindermoor Works within 40 minutes", "Cindermoor Works, 40 minutes max"]
)
def test_no_area_that_is_known_to_be_further_away_is_ranked(client: TestClient, text: str):
    """An area that is 63 minutes from the place was ranked, under a limit of 40."""
    found = read(client, text)
    start = client.get("/v1/meta").json()["data"]["defaults"]["rent"]

    [held] = found["spec"]["commutes"]
    assert (held["place_id"], held["max_minutes"], held["strictness"]) == (WORKS, 40, "hard")
    ranked = ranking(client, start, found["operations"])
    left_out = {one["area_id"] for one in ranked["filtered"]}
    assert left_out and not left_out & {one["area_id"] for one in ranked["ranked"]}
    # As a guide the same journey leaves none of them out, which is what was seen.
    gentler = ranking(client, start, as_a_guide(found["operations"]))
    assert gentler["filtered"] == []
    assert left_out <= {one["area_id"] for one in gentler["ranked"]}


def ranking(
    client: TestClient, spec: dict[str, Any], operations: dict[str, list[Any]]
) -> dict[str, Any]:
    body = {"spec": spec, "limit": 30, "operations": operations}
    response = client.post("/v1/rank", json=body)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def as_a_guide(operations: dict[str, list[Any]]) -> dict[str, list[Any]]:
    """The same edits, with every journey a guide."""
    gentler = [edit | {"strictness": "soft"} for edit in operations["commute_ops"]]
    return operations | {"commute_ops": gentler}


# --- In any other sentence, firm is the guess wherever the place stands --------------------

# What was typed, where the journey leads, and its minutes. The words make each a limit.
FIRM_IS_THE_GUESS = [
    ("Honestly, Cindermoor Works within 40 minutes", WORKS, 40),
    ("Cindermoor Works within 40 minutes, honestly", WORKS, 40),
    ("Foxholt Market within 30 minutes, I think", MARKET, 30),
    ("Honestly, Cindermoor Works, 40 minutes max", WORKS, 40),
    ("Cindermoor Works, 40 minutes max, I think", WORKS, 40),
    ("Honestly, I work at Cindermoor Works, 40 minutes max", WORKS, 40),
    ("Honestly, Cindermoor Works in no more than 40 minutes", WORKS, 40),
    # Beside what the rules offer and do not apply, and beside words they do not know.
    ("a garden, Foxholt Market within 30 minutes", MARKET, 30),
    ("Pellam Infirmary within 35 minutes, a big kitchen would be lovely", INFIRMARY, 35),
    # And before the place, as it was.
    ("Honestly, within 40 minutes of Cindermoor Works", WORKS, 40),
    ("Honestly, no more than 40 minutes from Cindermoor Works", WORKS, 40),
]


@pytest.mark.parametrize(("text", "place", "minutes"), FIRM_IS_THE_GUESS)
def test_firm_is_the_guess_wherever_the_place_stands(
    client: TestClient, text: str, place: str, minutes: int
):
    found = read(client, text)

    assert (found["status"], applied(found)) == ("suggest", [])
    [journey] = journeys(found)
    assert ways_of(journey) == [(FIRM, True, minutes, "hard"), (GUIDE, False, minutes, "soft")]
    # One press still takes the guide of it: no press leaves an area out on an estimate.
    assert (journey["add_all"], journey["only_by_choice"]) == (GUIDE, False)
    # A client that asks nothing takes the way the words give, and holds the limit.
    held, left_out = held_after(client, found)
    assert held == [(place, minutes, "hard")]
    assert left_out


# What was typed, where the journey leads, and its minutes. No word makes any a limit.
A_GUIDE_IS_THE_GUESS = [
    ("Honestly, Cindermoor Works in under 40 minutes", WORKS, 40),
    ("Honestly, Cindermoor Works, 40 minutes", WORKS, 40),
    ("Cindermoor Works in about 40 minutes, I think", WORKS, 40),
    ("Honestly, 40 minutes to Cindermoor Works", WORKS, 40),
    ("Honestly, about 40 minutes to Cindermoor Works", WORKS, 40),
]


@pytest.mark.parametrize(("text", "place", "minutes"), A_GUIDE_IS_THE_GUESS)
def test_a_limit_the_words_do_not_make_firm_stays_a_guide(
    client: TestClient, text: str, place: str, minutes: int
):
    found = read(client, text)

    assert (found["status"], applied(found)) == ("suggest", [])
    [journey] = journeys(found)
    assert ways_of(journey) == [(GUIDE, True, minutes, "soft"), (FIRM, False, minutes, "hard")]
    held, left_out = held_after(client, found)
    assert held == [(place, minutes, "soft")]
    assert left_out == []


# --- What puts a journey in doubt leaves it with no guess, as it did ------------------------

NO_GUESS = [
    # It asks.
    "Is Cindermoor Works within 40 minutes?",
    # A sign of doubt stands in what is said of the journey.
    "maybe Cindermoor Works within 40 minutes",
    "Cindermoor Works within 40 minutes perhaps",
    "Cindermoor Works should be within 40 minutes",
    # What more is said of it is in words the rules do not know, and may turn it.
    "Cindermoor Works within 40 minutes would be a nightmare",
    "Cindermoor Works within 40 minutes is what my boss wants",
    # Two times, and which is meant is the person's to say.
    "Honestly, Cindermoor Works within 40 minutes, ideally 30",
    # One time and two places.
    "Cindermoor Works and Pellam Infirmary, honestly, 40 minutes max",
    # The place may be somebody else's.
    "my sister works at Cindermoor Works, within 40 minutes",
    # The name is an area's too and stands apart from the time: which is meant is not said.
    "Foxholt, 30 minutes max",
    # What stands beyond a mark turns it away and says no more, or the sentence after it
    # takes it back: wherever the place stands.
    "Cindermoor Works within 40 minutes, no thanks",
    "within 40 minutes of Cindermoor Works, no thanks",
    "Cindermoor Works, 40 minutes max, no thanks",
    "No thanks, Cindermoor Works within 40 minutes",
    "Cindermoor Works within 40 minutes. Not really.",
    "within 40 minutes of Cindermoor Works. Not really.",
    "Cindermoor Works within 40 minutes. Scrap that.",
    # It stands further off in the sentence, beyond what else was said.
    "Cindermoor Works within 40 minutes, a big kitchen - scrap that",
    "No thanks, honestly, Cindermoor Works within 40 minutes",
]


@pytest.mark.parametrize("text", NO_GUESS)
def test_a_journey_in_doubt_carries_no_guess_and_leaves_no_area_out(client: TestClient, text: str):
    found = read(client, text)

    assert applied(found) == []
    offered = journeys(found)
    assert offered
    assert not [way for offer in offered for way in offer["choices"] if way["guess"]]
    held, left_out = held_after(client, found)
    assert "hard" not in [firm for _, _, firm in held]
    assert left_out == []


# What stands beside the journey says something else, and turns nothing of it.
NOT_TURNED = [
    ("no pubs, honestly, Cindermoor Works within 40 minutes", WORKS, 40),
    ("Cindermoor Works within 40 minutes, not a minute more, honestly", WORKS, 40),
]


@pytest.mark.parametrize(("text", "place", "minutes"), NOT_TURNED)
def test_what_is_said_of_something_else_beside_it_leaves_the_limit_as_the_words_make_it(
    client: TestClient, text: str, place: str, minutes: int
):
    found = read(client, text)

    [journey] = journeys(found)
    assert ways_of(journey)[0] == (FIRM, True, minutes, "hard")
    held, _ = held_after(client, found)
    assert held == [(place, minutes, "hard")]


AWAY_FROM_IT = [
    "Cindermoor Works, at least 40 minutes",
    "not within 40 minutes of Cindermoor Works",
    "Cindermoor Works, 40 minutes away at least",
    # A word at the head of its sentence turns the place away.
    "No, Cindermoor Works within 40 minutes",
]


@pytest.mark.parametrize("text", AWAY_FROM_IT)
def test_a_place_to_stay_away_from_is_still_no_journey_to_it(client: TestClient, text: str):
    found = read(client, text)

    assert applied(found) == []
    assert not [edit for offer in journeys(found) for edit in ways_of(offer)]
    assert not [way["id"] for offer in journeys(found) if (way := taken(offer)) is not None]


def test_a_turn_that_is_said_of_something_else_leaves_a_plain_list_a_plain_list(
    client: TestClient,
):
    found = read(client, "Cindermoor Works within 40 minutes, no pubs please")

    assert (found["status"], found["suggestions"]) == ("ok", [])
    assert applied(found) == [(WORKS, 40, "hard", "unchanged")]
    [pubs] = found["operations"]["weight_ops"]
    assert (pubs["feature_id"], pubs["direction"]) == ("venue_evening_per_homes", "less")


def test_a_place_alone_is_offered_as_it_was_and_is_never_applied(client: TestClient):
    """A name says a journey only with the time of it: alone, it says nothing of what is wanted."""
    found = read(client, "Cindermoor Works")

    assert (found["status"], applied(found)) == ("suggest", [])
    [journey] = journeys(found)
    assert [way["id"] for way in journey["choices"]] == [MORE, "ignore"]
    assert not [way for way in journey["choices"] if way["guess"]]
