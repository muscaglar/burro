"""A visit, as the service serves one.

A search may be for somewhere to stay on a visit, and for no home to rent or
to buy. Route 11 serves what a visitor is taken to mind. A visit holds no
budget and no kind of home: an edit that would give it one is turned away and
says why, a body that holds one is refused, no area is left out or moved for
what a home costs, and no sentence, no fact and no row of a comparison speaks
of it. A release that holds no cost serves a visit whole.

A sentence that says a visit is read as one. Where it is plainly said, it
carries Burro's guess, as what is said of renting and of buying does, and one
press takes it. What a model reads of a visit is held to what the rules
noticed, and a visit that a model gives a budget is offered without one.

The release is the committed synthetic one. It is made up, and describes no
real place.
"""

import dataclasses
import json
from typing import Any

import pytest
from burro_api.app import CONTRACT_VERSION, create_app
from burro_api.offers import MORE
from burro_api.reader import SYSTEM, SYSTEM_WITH_SETTINGS
from burro_core.ids import Tenure
from burro_core.interpret import NO_BUDGET_ON_A_VISIT, NO_HOME_ON_A_VISIT
from burro_core.reducer import apply
from burro_core.spec import NO_BUDGET, PreferenceSpec, default_spec
from fastapi.testclient import TestClient

from .support import (
    WORKS,
    client_for,
    commute,
    make_deps,
    model_budget,
    model_output,
    release,
    searching,
    through_the_route,
    wire,
)

VISITOR = default_spec(Tenure.VISIT)
NO_EDITS: dict[str, list[Any]] = {
    "budget_ops": [],
    "commute_ops": [],
    "weight_ops": [],
    "tag_ops": [],
    "area_ops": [],
    "setting_ops": [],
}
# What a sentence of what a home costs or of a budget holds, and no other sentence does.
OF_COST = ("your budget", "this kind of home", "rents for", "sells for", "middle rent")


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def data(response: Any) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    return response.json()["data"]


def budget_edit(**given: Any) -> dict[str, Any]:
    blank = {
        "action": "set",
        "tenure": "unchanged",
        "amount": 0,
        "segment": "unchanged",
        "strictness": "unchanged",
        "step": "none",
        "provenance": "ui_edit",
    }
    return blank | given


def with_edits(**groups: list[dict[str, Any]]) -> dict[str, list[Any]]:
    return NO_EDITS | groups


def visiting(client: TestClient) -> dict[str, Any]:
    """What a search for somewhere to stay starts from, as route 11 serves it."""
    return data(client.get("/v1/meta"))["defaults"]["visit"]


def read(client: TestClient, text: str, spec: PreferenceSpec | None = None) -> dict[str, Any]:
    body = {"text": text} | ({"spec": wire(spec)} if spec is not None else {})
    return data(client.post("/v1/interpret", json=body))


def guesses(found: dict[str, Any]) -> dict[str, str]:
    return {
        offer["label"]: way["id"]
        for offer in found["suggestions"]
        for way in offer["choices"]
        if way["guess"]
    }


def pressed(found: dict[str, Any]) -> dict[str, str]:
    return {offer["label"]: offer["add_all"] for offer in found["suggestions"] if offer["add_all"]}


# What is served of a visit


def test_the_service_serves_what_a_search_for_somewhere_to_stay_starts_from(client: TestClient):
    served = data(client.get("/v1/meta"))
    assert set(served["defaults"]) == {"rent", "buy", "visit"}
    visit = served["defaults"]["visit"]
    assert visit == wire(VISITOR)
    assert (visit["tenure"], visit["tenure_from"]) == ("visit", "default")
    assert visit["budget"] == wire(VISITOR)["budget"] == NO_BUDGET.model_dump(mode="json")
    assert (visit["budget"]["amount"], visit["budget"]["weight"]) == (None, 0.0)
    assert {weight["feature_id"]: weight["weight"] for weight in visit["weights"]} == {
        "station_walk": 0.5,
        "station_lines": 0.3,
        "venue_food_drink_per_homes": 0.3,
        "venue_evening_per_homes": 0.3,
        "culture_venues_per_homes": 0.3,
        "park_proximity": 0.3,
    }
    # The limits of money are of a home to rent and of one to buy. A visit has none.
    assert "visit" not in served["limits"]
    assert {"rent", "buy"} <= set(served["limits"])


def test_a_visit_is_ranked_as_it_is_served_and_by_nothing_a_home_costs(client: TestClient):
    visit = visiting(client)
    ranked = data(client.post("/v1/rank", json={"spec": visit, "limit": 100}))
    assert ranked["spec"] == visit and ranked["rejected"] == []
    assert ranked["areas_ranked"] == len(ranked["ranked"]) > 10
    assert not [found for found in ranked["filtered"] if found["reason"] == "over_budget"]
    for area in ranked["ranked"]:
        assert area["budget"] is None
        assert "budget" not in [part["component"] for part in area["contributions"]]
        assert "over_budget" not in area["untested_filters"]
    # On a release that holds no cost at all, the same areas stand in the same order.
    bare = client_for(make_deps(release=dataclasses.replace(release(), costs=())))
    assert not data(bare.get("/v1/meta"))["holds"]["costs"]
    again = data(bare.post("/v1/rank", json={"spec": visit, "limit": 100}))
    assert again["scores"] == ranked["scores"] and again["ranked"] == ranked["ranked"]
    assert again["spec_hash"] == ranked["spec_hash"]


def test_no_sentence_and_no_fact_of_a_visit_speaks_of_what_a_home_costs(client: TestClient):
    visit = visiting(client) | {"commutes": [wire_of(commute())]}
    explained = data(client.post("/v1/explanations", json={"spec": visit, "limit": 5}))
    assert len(explained["explanations"]) == 5
    said = [
        sentence["text"]
        for found in explained["explanations"]
        for sentence in (
            found["orientation"],
            *found["reasons"],
            *([found["trade_off"]] if found["trade_off"] else []),
            *found["missing"],
        )
    ]
    assert len(said) > 10
    assert not [text for text in said if any(words in text for words in OF_COST)]
    assert {fact["kind"] for fact in explained["facts"]} <= {"area", "feature", "tag", "travel"}
    # A search for a home with a budget is told of it, in the same release.
    told = data(client.post("/v1/explanations", json={"spec": wire(searching()), "limit": 5}))
    assert "budget_fit" in {fact["kind"] for fact in told["facts"]}


def wire_of(journey: Any) -> dict[str, Any]:
    return journey.model_dump(mode="json")


def test_a_comparison_of_a_visit_has_no_row_for_a_budget(client: TestClient):
    visit = visiting(client) | {"commutes": [wire_of(commute())]}
    areas = [area["area_id"] for area in data(client.get("/v1/areas"))["areas"][:3]]
    compared = data(client.post("/v1/compare", json={"area_ids": areas, "spec": visit}))
    rows = [row["component"] for row in compared["rows"]]
    assert "budget" not in rows and f"commute.{WORKS}.pt" in rows
    assert not {fact["kind"] for fact in compared["facts"]} & {"cost", "budget_fit"}
    of_a_home = data(
        client.post("/v1/compare", json={"area_ids": areas, "spec": wire(searching())})
    )
    assert "budget" in [row["component"] for row in of_a_home["rows"]]


def test_a_visit_is_shared_and_opened_as_a_visit(client: TestClient):
    visit = visiting(client)
    made = data(client.post("/v1/shares", json={"spec": visit}))
    assert made["spec"]["tenure"] == "visit" and made["spec"]["budget"] == visit["budget"]
    opened = data(client.get(f"/v1/shares/{made['share_id']}"))
    assert opened["spec"] == made["spec"]
    assert opened["ranked"] and all(area["budget"] is None for area in opened["ranked"])


# What a visit holds, and what it turns away


def test_a_search_becomes_a_visit_by_an_edit_and_drops_the_budget_and_the_home(
    client: TestClient,
):
    before = wire(searching())
    assert (before["budget"]["amount"], before["tenure"]) == (1800, "rent")
    to_a_visit = with_edits(budget_ops=[budget_edit(tenure="visit")])
    moved = data(client.post("/v1/rank", json={"spec": before, "operations": to_a_visit}))
    assert moved["rejected"] == [] and [found["changed"] for found in moved["applied"]] == [True]
    after = moved["spec"]
    assert (after["tenure"], after["tenure_from"]) == ("visit", "ui_edit")
    assert after["budget"] == NO_BUDGET.model_dump(mode="json")
    assert after["commutes"] == before["commutes"]
    assert moved["places"] and moved["ranked"]
    # And back: the usual budget of renting, and not the one that was dropped.
    to_renting = with_edits(budget_ops=[budget_edit(tenure="rent")])
    back = data(client.post("/v1/rank", json={"spec": after, "operations": to_renting}))["spec"]
    assert (back["tenure"], back["budget"]["amount"]) == ("rent", None)
    assert (back["budget"]["segment"], back["budget"]["weight"]) == ("bed_1", 0.3)


@pytest.mark.parametrize(
    ("edits", "reason"),
    [
        ({"budget_ops": [budget_edit(amount=1500)]}, "not_in_release"),
        ({"budget_ops": [budget_edit(amount=150, strictness="hard")]}, "not_in_release"),
        ({"budget_ops": [budget_edit(strictness="hard")]}, "not_in_release"),
        ({"budget_ops": [budget_edit(segment="bed_2")]}, "segment_not_for_tenure"),
        ({"budget_ops": [budget_edit(segment="flat", amount=400_000)]}, "segment_not_for_tenure"),
        ({"budget_ops": [budget_edit(tenure="visit", amount=1500)]}, "not_in_release"),
        ({"budget_ops": [budget_edit(action="nudge", step="up_small")]}, "nothing_to_change"),
        (
            {
                "setting_ops": [
                    {
                        "action": "set",
                        "setting": "budget_weight",
                        "choice": "none",
                        "value": 0.5,
                        "step": "none",
                        "provenance": "ui_edit",
                    }
                ]
            },
            "not_in_release",
        ),
    ],
)
def test_an_edit_that_would_give_a_visit_a_budget_or_a_home_is_turned_away_and_says_why(
    client: TestClient, edits: dict[str, list[dict[str, Any]]], reason: str
):
    visit = visiting(client)
    sent = {"spec": visit, "operations": with_edits(**edits)}
    answered = data(client.post("/v1/rank", json=sent))
    assert [found["reason"] for found in answered["rejected"]] == [reason]
    assert answered["applied"] == [] and answered["spec"] == visit
    # The search is ranked as it was, and none of what was sent is in the answer.
    assert answered["ranked"] and "1500" not in json.dumps(answered["spec"])


@pytest.mark.parametrize(
    "budget",
    [
        {"amount": 1500},
        {"amount": 150, "strictness": "hard"},
        {"weight": 0.3},
        {"segment": "flat"},
        {"strictness": "hard"},
        {"provenance": "stated"},
    ],
)
@pytest.mark.parametrize("route", ["rank", "explanations", "interpret", "shares", "compare"])
def test_a_visit_that_is_sent_with_a_budget_or_a_home_is_refused(
    client: TestClient, budget: dict[str, Any], route: str
):
    visit = visiting(client)
    sent = visit | {"budget": visit["budget"] | budget}
    body: dict[str, Any] = {"spec": sent}
    if route == "interpret":
        body["text"] = "leafy"
    if route == "compare":
        body["area_ids"] = [a["area_id"] for a in data(client.get("/v1/areas"))["areas"][:2]]
    response = client.post(f"/v1/{route}", json=body)
    assert response.status_code == 422
    answered = response.json()
    assert answered["error"]["code"] == "invalid_spec"
    assert answered["error"]["fields"] == [{"path": "spec", "problem": "invalid"}]
    # It says where and never what: nothing that was sent is said back.
    assert "1500" not in response.text and "flat" not in response.text
    assert answered["meta"]["synthetic"] is True
    assert response.headers["x-burro-synthetic"] == "true"


# What is read of a visit


@pytest.mark.parametrize(
    "text",
    [
        "visiting",
        "I'm visiting for a weekend",
        "a hotel",
        "looking for somewhere to stay",
        "staying for 3 nights",
        "on holiday, near a park",
        "a hotel near Cindermoor Works",
    ],
)
def test_a_sentence_that_says_a_visit_is_applied_as_one(client: TestClient, text: str):
    found = read(client, text)
    assert found["status"] == "ok" and found["rejected"] == []
    assert [edit["tenure"] for edit in found["operations"]["budget_ops"]] == ["visit"]
    assert (found["spec"]["tenure"], found["spec"]["tenure_from"]) == ("visit", "stated")
    assert found["spec"]["budget"] == NO_BUDGET.model_dump(mode="json")
    assert found["assumptions"] == [] or all(
        assumed["group"] != "budget_ops" for assumed in found["assumptions"]
    )
    assert found["not_in_release"] == [] and found["unread"] == []
    # It can be ranked as it was left, and the hash is of the search that was left.
    ranked = data(client.post("/v1/rank", json={"spec": found["spec"]}))
    assert ranked["spec_hash"] == found["spec_hash"]


def test_a_visit_that_is_plainly_said_carries_the_guess_and_one_press_takes_it(
    client: TestClient,
):
    text = "Honestly, I'm visiting for a weekend, somewhere leafy"
    found = read(client, text)
    assert found["status"] == "suggest" and found["applied"] == []
    visit = next(offer for offer in found["suggestions"] if offer["target"] == "tenure")
    assert visit["label"] == "Visiting"
    assert [text[span["start"] : span["end"]] for span in visit["spans"]] == [
        "visiting for a weekend"
    ]
    assert guesses(found)["Visiting"] == MORE == pressed(found)["Visiting"]
    (take, skip) = visit["choices"]
    assert (take["label"], skip["label"]) == ("Set", "Skip")
    assert take["operations"]["budget_ops"] == [budget_edit(tenure="visit")]
    # One press makes the search a visit, and nothing of a budget or a home.
    pressed_spec = data(
        client.post("/v1/rank", json={"spec": found["spec"], "operations": take["operations"]})
    )["spec"]
    assert pressed_spec["tenure"] == "visit"
    assert pressed_spec["budget"] == NO_BUDGET.model_dump(mode="json")


def test_the_offer_of_a_visit_says_what_a_visit_is_in_whole_sentences(client: TestClient):
    found = read(client, "Honestly, I'm visiting for a weekend")
    (visit,) = found["suggestions"]
    assert visit["does"] == "Look for somewhere to stay on a visit."
    assert visit["follows"] == (
        "A search for somewhere to stay has no budget and no kind of home, so Burro ranks "
        "areas by everything else you ask for."
    )
    assert (visit["said"], visit["note"], visit["needs"]) == ([], "", "")


@pytest.mark.parametrize(
    "text",
    [
        # Somebody else's, what may be over, and what is turned away or asked.
        "Honestly, my sister is visiting for a weekend",
        "Honestly, maybe a hotel",
        "Honestly, a hotel if I must",
        "Is a hotel worth it?",
        # Two kinds of search in one prompt.
        "Honestly, renting or visiting",
        "Honestly, a hotel, or a flat to rent",
    ],
)
def test_a_visit_that_is_in_doubt_carries_no_guess_and_no_press_takes_it(
    client: TestClient, text: str
):
    found = read(client, text)
    assert found["applied"] == [] and found["spec"]["tenure"] == "rent"
    assert "Visiting" not in guesses(found) and "Visiting" not in pressed(found)


def test_what_is_typed_of_a_home_and_of_money_on_a_visit_is_said_and_never_set(
    client: TestClient,
):
    text = "visiting, a 2 bed flat, up to £2,000"
    found = read(client, text)
    assert found["status"] == "ok" and found["spec"]["tenure"] == "visit"
    assert found["spec"]["budget"] == NO_BUDGET.model_dump(mode="json")
    assert found["rejected"] == [] and found["not_in_release"] == []
    said = {offer["label"]: offer for offer in found["suggestions"]}
    assert set(said) == {"A flat", "A budget of £2,000"}
    assert said["A flat"]["note"] == NO_HOME_ON_A_VISIT
    assert said["A budget of £2,000"]["note"] == NO_BUDGET_ON_A_VISIT
    for offer in said.values():
        assert offer["target"] == "budget" and offer["add_all"] == ""
        assert [way["id"] for way in offer["choices"]] == ["ignore"]
        assert offer["does"] == "Burro could not use these words in your search."
    assert found["unread"] == []


def test_what_a_night_costs_is_said_to_be_what_burro_has_no_measure_of(client: TestClient):
    text = "a hotel for £150 a night near Cindermoor Works"
    found = read(client, text)
    assert found["applied"] == [] and "prices_and_hours" in found["unmet"]
    assert [offer["target"] for offer in found["suggestions"]] == ["tenure", "commute"]
    assert not any(
        edit["amount"]
        for offer in found["suggestions"]
        for way in offer["choices"]
        for edit in way["operations"]["budget_ops"]
    )
    assert found["unread"] == []


# What a model reads of a visit


def test_a_model_is_told_what_a_visit_is_and_that_it_holds_no_budget():
    for instructions in (SYSTEM, SYSTEM_WITH_SETTINGS):
        assert "rent, buy or visit" in instructions
        assert "A visit has no amount and no segment" in instructions
        assert "make no edit for what a night or a stay costs" in instructions
        # A sentence about where to stay is about what Burro is for, and is not off the subject.
        said = " ".join(instructions.split())
        assert "where they want to live, or where they want to stay on a visit," in said
        assert (
            "If nothing in the request is about choosing where to live, or where to stay on a "
            "visit, set `status` to" in said
        )


def test_a_visit_a_model_read_is_kept_only_where_the_rules_noticed_the_words_for_one():
    unheard = "Honestly, we are coming down for the match"
    read_so = model_output(budget_ops=[model_budget(tenure="visit", words=unheard)])
    found = through_the_route(read_so, unheard)
    assert found["suggestions"] == [] and found["spec"]["tenure"] == "rent"
    heard = "Honestly, we are planning a trip"
    found = through_the_route(
        model_output(budget_ops=[model_budget(tenure="visit", words=heard)]), heard
    )
    (visit,) = found["suggestions"]
    assert (visit["label"], visit["target"]) == ("Visiting", "budget")
    assert [way["operations"]["budget_ops"] for way in visit["choices"][:1]] == [
        [budget_edit(tenure="visit")]
    ]


def test_a_visit_that_a_model_gives_a_budget_or_a_home_is_offered_without_either():
    text = "Honestly, a hotel for two, about 900 all in"
    read_so = model_output(
        budget_ops=[
            model_budget(tenure="visit", amount=900, segment="bed_1", strictness="hard", words=text)
        ]
    )
    found = through_the_route(read_so, text)
    visits = [offer for offer in found["suggestions"] if offer["label"] == "Visiting"]
    (visit,) = visits
    ways = [way for way in visit["choices"] if way["id"] != "ignore"]
    assert [way["operations"]["budget_ops"] for way in ways] == [[budget_edit(tenure="visit")]]
    assert visit["said"] == [
        "A search for somewhere to stay has no budget and no kind of home, so Burro has "
        "left those out."
    ]
    pressed_spec = apply(default_spec(Tenure.RENT), _operations(ways[0]), release()).spec
    assert pressed_spec.visiting and pressed_spec.budget == NO_BUDGET


def test_what_a_model_reads_of_money_on_a_visit_makes_no_offer_and_no_fault():
    text = "Honestly, about 900 all in"
    read_so = model_output(budget_ops=[model_budget(amount=900, words=text)])
    found = through_the_route(read_so, text, VISITOR)
    assert found["spec"] == wire(VISITOR)
    assert not [offer for offer in found["suggestions"] if offer["choices"][0]["id"] != "ignore"]


def _operations(way: dict[str, Any]) -> Any:
    from burro_core.ops import Operations

    return Operations.model_validate(way["operations"])


# The document


def test_the_contract_is_at_its_third_version_and_holds_a_visit():
    assert CONTRACT_VERSION == "3"
    document: dict[str, Any] = create_app(make_deps()).openapi()
    assert document["info"]["version"] == "3"
    schemas = document["components"]["schemas"]
    assert schemas["Tenure"]["enum"] == ["rent", "buy", "visit"]
    assert schemas["TenureChoice"]["enum"] == ["rent", "buy", "visit", "unchanged"]
    assert schemas["Defaults"]["required"] == ["rent", "buy", "visit"]
    # No other list of codes grew for a visit, so no client meets a code it has no word for.
    assert "visit" not in json.dumps(
        [schemas[name]["enum"] for name in ("RejectReason", "Segment", "SegmentChoice")]
    )
