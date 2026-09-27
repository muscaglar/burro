"""No area is left out because a person said where somebody else is, or where they stay.

Route 1 offered "visiting my mother in Pellam Cross" as a rule for the area,
with two ways and no guess. A client that takes what is offered took the first,
which is to look only there: one area was ranked, and 21 were left out on a
guess. Core now offers what the words mean (contract, section 8.2): a journey
to the place where the name is a place's too, and nothing where Burro holds no
place of that name.

Every sentence of the first list is one the service was driven with. What a
client takes is taken here as the website's rule names it: the way that one
press adds, else the guide of a limit, else Burro's guess, else the first way.
"""

from typing import Any

import pytest
from burro_core.interpret import MAY_BE_ANOTHERS
from fastapi.testclient import TestClient

from .support import client_for, make_deps

PELLAM, FOXHOLT = "syn-p0012", "syn-p0007"
DRIVEN = [
    ("visiting my mother in Pellam Cross", PELLAM, MAY_BE_ANOTHERS),
    ("my mother lives in Pellam Cross", PELLAM, MAY_BE_ANOTHERS),
    ("staying with friends in Foxholt", FOXHOLT, ""),
    ("I want to stay in Foxholt", FOXHOLT, ""),
    ("a hotel in Pellam Cross", PELLAM, ""),
    ("Pellam Cross in under 25", PELLAM, ""),
]


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def read(client: TestClient, text: str) -> dict[str, Any]:
    response = client.post("/v1/interpret", json={"text": text})
    assert response.status_code == 200, response.text
    return response.json()["data"]


def taken(found: dict[str, Any]) -> dict[str, list[Any]]:
    """The edits of what a client takes that takes what is offered, and asks nothing."""
    edits: dict[str, list[Any]] = {}
    for offer in found["suggestions"]:
        ways = {way["id"]: way for way in offer["choices"] if way["id"] != "ignore"}
        guess = next((way for way in ways.values() if way["guess"]), None)
        way = ways.get(offer["add_all"]) or ways.get("guide") or guess or ways.get("more")
        operations: dict[str, list[Any]] = way["operations"] if way else {}
        for group, held in operations.items():
            edits.setdefault(group, []).extend(held)
    return edits


def ranked(client: TestClient, found: dict[str, Any]) -> dict[str, Any]:
    body = {"spec": found["spec"], "limit": 100} | (
        {"operations": taken(found)} if taken(found) else {}
    )
    response = client.post("/v1/rank", json=body)
    assert response.status_code == 200, response.text
    return response.json()["data"]


@pytest.mark.parametrize(("text", "place", "note"), DRIVEN)
def test_route_1_offers_a_journey_to_the_place_and_no_rule_for_the_area(
    client: TestClient, text: str, place: str, note: str
):
    found = read(client, text)

    assert (found["status"], found["applied"]) == ("suggest", [])
    assert not [offer for offer in found["suggestions"] if offer["target"] == "area"]
    [journey] = [offer for offer in found["suggestions"] if offer["target"] == "commute"]
    assert journey["note"] == note
    assert {
        edit["place_id"] for way in journey["choices"] for edit in way["operations"]["commute_ops"]
    } == {place}
    # Where it may be somebody else's, no press takes it with others.
    assert journey["add_all"] == ("" if note else "more")


@pytest.mark.parametrize(("text", "place", "note"), DRIVEN)
def test_no_area_is_left_out_of_what_a_client_ranks_that_takes_what_is_offered(
    client: TestClient, text: str, place: str, note: str
):
    found = read(client, text)
    after = ranked(client, found)

    assert after["rejected"] == [] and after["filtered"] == []
    assert after["spec"]["areas"] == []
    assert len(after["ranked"]) == len(ranked(client, read(client, "leafy"))["ranked"])
    assert [(held["place_id"], held["strictness"]) for held in after["spec"]["commutes"]] == [
        (place, "soft")
    ]


@pytest.mark.parametrize(
    "text",
    [
        "my mother lives in Alderwick",
        "visiting my mother in Alderwick",
        "I want to stay in Alderwick",
        "I want to be near Alderwick",
    ],
)
def test_a_name_that_is_an_areas_alone_is_said_to_be_unread(client: TestClient, text: str):
    found = read(client, text)

    assert not [o for o in found["suggestions"] if o["target"] in ("area", "commute")]
    unread = " ".join(text[left["start"] : left["end"]] for left in found["unread"])
    assert "Alderwick" in unread and "other" in found["unmet"]
    after = ranked(client, found)
    assert after["filtered"] == [] and after["spec"]["areas"] == []


def test_a_place_that_a_person_would_rather_not_be_in_is_offered_to_be_left_out(
    client: TestClient,
):
    """What turns the place away stands after it. To look only there was offered first."""
    found = read(client, "my boss lives in Tallowgate so I'd rather not")

    [area] = found["suggestions"]
    assert area["target"] == "area"
    assert [way["id"] for way in area["choices"]] == ["less", "ignore"]
    assert area["does"] == "Leave Tallowgate out of the results."
    # Nothing of it is taken unasked: the search is ranked as it stood.
    assert taken(found) == {}
    assert ranked(client, found)["filtered"] == []
