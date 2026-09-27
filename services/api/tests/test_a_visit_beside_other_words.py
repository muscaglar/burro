"""A visit is read beside what else is wished, and is not offered to a search that is one.

Route 1 left the search of somebody who typed "a hotel somewhere lively" one
for a home to rent, and offered the rest as to a renter. A client that takes
what is offered then ranked a visitor's words with a renter's usual settings.
Core reads each of the sentences now (contract, section 8.2).

And route 1 offered "Visiting" to a search that was a visit already, whoever
read. A visit that is said of such a search was heard, and there is nothing
of it to choose. Every sentence of the first list is one the service was
driven with. No call is made: where a model reads, a stand-in hands the answer
to the reader.
"""

from typing import Any

import pytest
from burro_core.ids import Tenure
from burro_core.spec import NO_BUDGET, default_spec
from fastapi.testclient import TestClient

from .support import (
    WORKS,
    client_for,
    make_deps,
    model_budget,
    model_output,
    through_the_route,
    wire,
)

VISITOR = default_spec(Tenure.VISIT)
CULTURE = "culture_venues_per_homes"
# What was typed, with the measures, the vibes and the places it asks for.
DRIVEN = [
    ("a hotel somewhere lively", {"pace"}),
    ("a hotel somewhere", set[str]()),
    ("city break, lively, near a station", {"pace", "station_walk"}),
    ("weekend trip, near museums and good food", {CULTURE, "foodie"}),
    ("a weekend away, near museums", {CULTURE}),
    ("a weekend away", set[str]()),
    ("tourist, 3 nights, near museums", {CULTURE}),
    ("short stay near Pellam Cross", {"syn-p0012"}),
    ("where to stay in London", set[str]()),
]


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def read(client: TestClient, text: str, spec: dict[str, Any] | None = None) -> dict[str, Any]:
    body = {"text": text} | ({"spec": spec} if spec is not None else {})
    response = client.post("/v1/interpret", json=body)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def asked(operations: dict[str, list[dict[str, Any]]]) -> set[str]:
    return {
        *(edit["feature_id"] for edit in operations["weight_ops"]),
        *(edit["tag_id"] for edit in operations["tag_ops"]),
        *(edit["place_id"] for edit in operations["commute_ops"]),
    }


@pytest.mark.parametrize(("text", "wished"), DRIVEN)
def test_route_1_makes_the_search_a_visit_and_applies_what_is_wished_beside_it(
    client: TestClient, text: str, wished: set[str]
):
    found = read(client, text)

    assert (found["status"], found["rejected"]) == ("ok", [])
    assert [edit["tenure"] for edit in found["operations"]["budget_ops"]] == ["visit"]
    assert asked(found["operations"]) == wished
    assert (found["spec"]["tenure"], found["spec"]["tenure_from"]) == ("visit", "stated")
    assert found["spec"]["budget"] == NO_BUDGET.model_dump(mode="json")
    assert (found["suggestions"], found["unread"], found["not_in_release"]) == ([], [], [])
    # It can be ranked as it was left, with what a visitor is taken to mind.
    ranked = client.post("/v1/rank", json={"spec": found["spec"], "limit": 3})
    assert ranked.status_code == 200
    assert ranked.json()["data"]["spec_hash"] == found["spec_hash"]


@pytest.mark.parametrize(
    ("text", "place"),
    [
        ("a hotel somewhere affluent", None),
        ("I'm coming for a conference at Cindermoor Works and need a hotel nearby", WORKS),
    ],
)
def test_route_1_offers_the_visit_of_a_sentence_that_is_not_plain(
    client: TestClient, text: str, place: str | None
):
    found = read(client, text)

    assert (found["status"], found["applied"], found["spec"]["tenure"]) == ("suggest", [], "rent")
    [visit] = [offer for offer in found["suggestions"] if offer["target"] == "tenure"]
    assert visit["label"] == "Visiting"
    assert [text[span["start"] : span["end"]] for span in visit["spans"]] == ["hotel"]
    journeys = [
        edit["place_id"]
        for offer in found["suggestions"]
        for way in offer["choices"]
        for edit in way["operations"]["commute_ops"]
    ]
    assert journeys == ([place] if place else [])
    assert not [left for left in found["unread"] if "hotel" in text[left["start"] : left["end"]]]


ON_A_VISIT = [
    "a hotel for £150 a night, honestly",
    "a hotel, honestly",
    "honestly, a hotel near a park",
    "We are planning a trip and want somewhere leafy",
]


@pytest.mark.parametrize("text", ON_A_VISIT)
@pytest.mark.parametrize("chosen_by", ["default", "ui_edit", "stated"])
@pytest.mark.parametrize("reader", ["the rules alone", "a model that reads a visit"])
def test_a_search_that_is_a_visit_already_is_not_offered_a_visit_again(
    client: TestClient, text: str, chosen_by: str, reader: str
):
    visitor = wire(VISITOR) | {"tenure_from": chosen_by}
    if reader == "the rules alone":
        found = read(client, text, visitor)
    else:
        reads = model_output(budget_ops=[model_budget(tenure="visit", words=text)])
        found = through_the_route(reads, text, VISITOR.model_validate(visitor))

    assert [offer["label"] for offer in found["suggestions"] if offer["target"] == "tenure"] == []
    assert found["operations"]["budget_ops"] == []
    assert found["spec"]["tenure"] == "visit"
    # The words were heard: none of them is said to be unread.
    left = " ".join(text[span["start"] : span["end"]] for span in found["unread"])
    assert not [word for word in ("hotel", "trip") if word in left]


def test_a_renter_is_still_offered_a_visit(client: TestClient):
    found = read(client, "honestly, a hotel near a park")

    [visit] = [offer for offer in found["suggestions"] if offer["target"] == "tenure"]
    assert (visit["label"], visit["does"]) == (
        "Visiting",
        "Look for somewhere to stay on a visit.",
    )
