"""Route 1 says what a visit cannot hold of an amount, however the amount is typed.

"Up to £2,000", typed into a visit, was offered with the sentence that says
Burro holds no price of a stay. "Honestly, up to £2,000" was not: the amount
was named among what the data does not hold, where a client says in words of
its own that the data holds no rent and no price yet. That is untrue of a
release that holds both, and nothing said why a visit has no budget.

Every sentence of the first list is one the service was driven with.
"""

from typing import Any

import pytest
from burro_api.wording import NOTHING_TAKEN
from burro_core.ids import Tenure
from burro_core.interpret import NO_BUDGET_ON_A_VISIT, NO_STEP_ON_A_VISIT
from burro_core.spec import default_spec
from fastapi.testclient import TestClient

from .support import client_for, make_deps, wire

VISITOR = wire(default_spec(Tenure.VISIT))
DRIVEN = [
    "up to £2,000",
    "honestly, up to £2,000",
    "my budget is £2,000 honestly",
    "honestly £2,000 max",
    "somewhere lively honestly, up to £2,000",
]


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def read(client: TestClient, text: str, spec: dict[str, Any] | None = None) -> dict[str, Any]:
    body = {"text": text} | ({"spec": spec} if spec is not None else {})
    response = client.post("/v1/interpret", json=body)
    assert response.status_code == 200, response.text
    return response.json()["data"]


@pytest.mark.parametrize("text", DRIVEN)
def test_route_1_says_why_a_visit_holds_no_budget(client: TestClient, text: str):
    found = read(client, text, VISITOR)

    [amount] = [offer for offer in found["suggestions"] if offer["target"] == "budget"]
    assert amount["label"] == "A budget of £2,000"
    # Nothing of it can be pressed, and the sentence that says why is Burro's own.
    assert [way["id"] for way in amount["choices"]] == ["ignore"]
    assert (amount["does"], amount["note"]) == (NOTHING_TAKEN, NO_BUDGET_ON_A_VISIT)
    assert (amount["add_all"], amount["said"], amount["follows"]) == ("", [], "")
    # It is not named among what the data does not hold, and it was read.
    assert found["not_in_release"] == [] and found["rejected"] == []
    unread = " ".join(text[left["start"] : left["end"]] for left in found["unread"])
    assert "2,000" not in unread
    assert found["operations"]["budget_ops"] == []
    assert found["spec"]["tenure"] == "visit" and found["spec"]["budget"]["amount"] is None


@pytest.mark.parametrize("text", ["visiting, honestly, up to £2,000", "zebra, a hotel, £400k"])
def test_route_1_says_so_beside_the_words_for_a_visit_too(client: TestClient, text: str):
    """It offered the amount as a renter's budget beside the visit, and a client took both."""
    found = read(client, text)

    [amount] = [offer for offer in found["suggestions"] if offer["target"] == "budget"]
    assert [way["id"] for way in amount["choices"]] == ["ignore"]
    assert amount["note"] == NO_BUDGET_ON_A_VISIT
    assert [offer["label"] for offer in found["suggestions"] if offer["target"] == "tenure"] == [
        "Visiting"
    ]
    assert found["not_in_release"] == []


@pytest.mark.parametrize("text", ["cheaper homes", "somewhere cheaper"])
def test_route_1_says_that_a_visit_has_no_budget_to_lower(client: TestClient, text: str):
    """Each was answered with no edit, no offer and nothing unread."""
    found = read(client, text, VISITOR)

    [step] = found["suggestions"]
    assert (step["target"], step["label"]) == ("budget", "A lower budget")
    assert [way["id"] for way in step["choices"]] == ["ignore"]
    assert (step["does"], step["note"]) == (NOTHING_TAKEN, NO_STEP_ON_A_VISIT)
    assert (step["add_all"], step["only_by_choice"]) == ("", False)
    assert found["operations"]["budget_ops"] == [] and found["rejected"] == []
    assert found["unread"] == [] and found["not_in_release"] == []
    assert found["spec"]["tenure"] == "visit" and found["spec"]["budget"]["amount"] is None
