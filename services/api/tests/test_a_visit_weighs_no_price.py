"""The service turns what homes sold for away from a visit, and offers it none.

Route 2 applied an edit of the middle price paid for a home to a visit, and
route 3 then gave the price of a home as a reason to stay in an area: "The
middle price paid for a home: £577,000, which is dearer than 95% of the 21
areas Burro compared." Route 1 offered "What homes sell for" for a word for a
smart area that was typed beside a visit, and a client that takes what is
offered took it.

The edit is turned away now, with the reason an amount on a visit is turned
away with, and no reader offers one (contract, section 5.3, rule 16, and
section 8.2). No call is made: where a model reads, a stand-in hands the answer
to the reader.
"""

from typing import Any

import pytest
from burro_core.ids import Tenure
from burro_core.interpret import NO_PRICE_ON_A_VISIT
from burro_core.spec import default_spec
from fastapi.testclient import TestClient

from .support import client_for, make_deps, model_output, model_weight, through_the_route, wire

VISITOR = default_spec(Tenure.VISIT)
PRICES = ("price_median", "price_rise_5y", "price_rise_10y")
NO_EDITS: dict[str, list[Any]] = {
    "budget_ops": [],
    "commute_ops": [],
    "weight_ops": [],
    "tag_ops": [],
    "area_ops": [],
    "setting_ops": [],
}


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def data(response: Any) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    return response.json()["data"]


def weighing(feature_id: str, **given: Any) -> dict[str, Any]:
    blank = {
        "action": "set",
        "feature_id": feature_id,
        "value": 0.5,
        "step": "none",
        "direction": "more",
        "provenance": "ui_edit",
    }
    return blank | given


def every_sentence(explained: dict[str, Any]) -> list[str]:
    found: list[str] = []
    for area in explained["explanations"]:
        parts = [area["orientation"], *area["reasons"], area["trade_off"], *area["missing"]]
        found += [part["text"] for part in parts if part]
    return found


@pytest.mark.parametrize("feature_id", PRICES)
def test_route_2_turns_the_edit_away_and_says_why(client: TestClient, feature_id: str):
    visit = data(client.get("/v1/meta"))["defaults"]["visit"]
    edits = NO_EDITS | {"weight_ops": [weighing(feature_id)]}

    ranked = data(client.post("/v1/rank", json={"spec": visit, "operations": edits, "limit": 5}))

    assert ranked["rejected"] == [{"group": "weight_ops", "index": 0, "reason": "not_in_release"}]
    assert ranked["applied"] == [] and ranked["spec"] == visit
    assert feature_id not in {held["feature_id"] for held in ranked["spec"]["weights"]}
    # Nothing that is said of an area of the search gives a price of homes.
    explained = data(client.post("/v1/explanations", json={"spec": ranked["spec"], "limit": 5}))
    assert not [text for text in every_sentence(explained) if "price paid for a home" in text]


def test_the_same_edit_is_in_order_for_a_home(client: TestClient):
    edits = NO_EDITS | {"weight_ops": [weighing("price_median")]}
    ranked = data(
        client.post("/v1/rank", json={"spec": wire(default_spec(Tenure.BUY)), "operations": edits})
    )
    assert ranked["rejected"] == []
    assert "price_median" in {held["feature_id"] for held in ranked["spec"]["weights"]}


def test_a_search_that_becomes_a_visit_drops_what_it_weighed_of_a_price(client: TestClient):
    edits = NO_EDITS | {"weight_ops": [weighing("price_median"), weighing("water_access")]}
    home = data(
        client.post("/v1/rank", json={"spec": wire(default_spec(Tenure.BUY)), "operations": edits})
    )
    visit = {"action": "set", "tenure": "visit", "amount": 0, "segment": "unchanged"}
    visit |= {"strictness": "unchanged", "step": "none", "provenance": "ui_edit"}

    after = data(
        client.post(
            "/v1/rank",
            json={"spec": home["spec"], "operations": NO_EDITS | {"budget_ops": [visit]}},
        )
    )

    held = {found["feature_id"] for found in after["spec"]["weights"]}
    assert after["rejected"] == [] and after["spec"]["tenure"] == "visit"
    assert "price_median" not in held and "water_access" in held


@pytest.mark.parametrize(
    ("text", "spec"),
    [
        ("visiting, somewhere affluent", None),
        ("a hotel somewhere affluent", None),
        ("somewhere affluent", wire(VISITOR)),
    ],
)
def test_route_1_offers_no_measure_of_what_homes_sold_for_beside_a_visit(
    client: TestClient, text: str, spec: dict[str, Any] | None
):
    body = {"text": text} | ({"spec": spec} if spec else {})
    found = data(client.post("/v1/interpret", json=body))

    offered = {offer["target"] for offer in found["suggestions"]}
    assert not [target for target in offered if target.removeprefix("feature:") in PRICES]
    assert {"feature:brand_mix", "feature:homes_higher_bands"} <= offered
    assert not [offer for offer in found["suggestions"] if "homes sell for" in offer["note"]]
    assert found["not_in_release"] == [] and found["rejected"] == []


def test_route_1_says_why_a_visit_weighs_none_where_the_words_are_read_as_nothing_else(
    client: TestClient,
):
    found = data(
        client.post("/v1/interpret", json={"text": "rising prices", "spec": wire(VISITOR)})
    )

    assert [offer["target"] for offer in found["suggestions"]] == [
        "feature:price_rise_5y",
        "feature:price_rise_10y",
    ]
    for offer in found["suggestions"]:
        assert [way["id"] for way in offer["choices"]] == ["ignore"]
        assert (offer["note"], offer["add_all"]) == (NO_PRICE_ON_A_VISIT, "")
    assert found["not_in_release"] == [] and found["unread"] == []


def test_what_a_model_reads_of_a_price_is_not_offered_to_a_visit():
    text = "honestly, somewhere with dear homes"
    reads = model_output(
        weight_ops=[model_weight("price_median", direction="more", words="dear homes")]
    )

    found = through_the_route(reads, text, VISITOR)

    assert not [
        edit
        for offer in found["suggestions"]
        for way in offer["choices"]
        for edit in way["operations"]["weight_ops"]
        if edit["feature_id"] in PRICES
    ]
    assert found["operations"]["weight_ops"] == []
