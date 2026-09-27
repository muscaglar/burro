"""No area is left out, and no journey dropped, because a person typed part of a name.

"Leafy and quiet, 30 minutes to Pellam, honestly" was answered with a rule for
the area Pellam Cross, to look only there or to leave it out, and its journey
was said to be unread. Three places bear the name, and one area answers to it.
In a plain list route 1 asks which place is meant, and a client that asks
nothing takes the first. Core now asks in any other sentence too, where the
part that says the journey is one the grammar makes (contract, section 8.2),
and offers no rule for an area where the words before its name expect a place
to reach.

"Leafy and quiet, near Gorsebeck" names an area alone, which is no place to be
near: nothing is offered for it, and its words are said to be unread. Both
sentences are ones the website was driven with.

Where a model reads, its answer holds no edit, and so no question of the
rules. The words a question rested on are then said to be unread, unless an
offer rests on them: nothing that was typed is dropped without a word. No call
is made: a stand-in hands the answer to the reader.
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from .support import client_for, make_deps, model_commute, model_output, through_the_route

PELLAM = ["Pellam Cross", "Pellam Exchange", "Pellam Infirmary"]
TYPED = "Leafy and quiet, 30 minutes to Pellam, honestly"


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def read(client: TestClient, text: str) -> dict[str, Any]:
    response = client.post("/v1/interpret", json={"text": text, "ask_model": False})
    assert response.status_code == 200, response.text
    return response.json()["data"]


def words(text: str, spans: list[dict[str, int]]) -> list[str]:
    return [text[span["start"] : span["end"]] for span in spans]


def test_route_1_asks_which_place_is_meant_as_it_does_of_a_plain_list(client: TestClient):
    found, listed = read(client, TYPED), read(client, TYPED.removesuffix(", honestly"))

    assert found["status"] == listed["status"] == "clarify"
    assert found["clarify"] == listed["clarify"]
    [asked] = found["clarify"]
    assert [option["name"] for option in asked["options"]] == PELLAM
    [journey] = found["operations"]["commute_ops"]
    assert (journey["place_id"], journey["max_minutes"]) == ("", 30)
    # It adds nothing until a place is chosen, and what else was said is offered.
    assert found["applied"] == [] and found["spec"]["commutes"] == []
    assert [offer["target"] for offer in found["suggestions"]] == [
        "tag:leafy",
        "tag:quiet_residential",
    ]
    # What is said of the words alone asks for nothing, and is not said to be unread.
    assert (found["unread"], "other" in found["unmet"]) == ([], True)


def test_a_client_that_takes_the_first_place_leaves_no_area_out(client: TestClient):
    found = read(client, TYPED)
    [asked] = found["clarify"]
    journey = found["operations"]["commute_ops"][asked["index"]]
    first = journey | {"place_id": asked["options"][0]["id"]}
    taken = found["operations"] | {"commute_ops": [first]}

    response = client.post(
        "/v1/rank", json={"spec": found["spec"], "operations": taken, "limit": 100}
    )

    after = response.json()["data"]
    assert response.status_code == 200 and after["rejected"] == []
    assert after["filtered"] == [] and after["spec"]["areas"] == []
    [held] = after["spec"]["commutes"]
    assert (held["place_id"], held["max_minutes"], held["strictness"]) == (
        asked["options"][0]["id"],
        30,
        "soft",
    )


@pytest.mark.parametrize(
    "text",
    [
        "Leafy and quiet, near Gorsebeck",
        "Leafy and quiet, my mum lives 30 minutes to Pellam",
        "Leafy and quiet, we both work at Pellam",
    ],
)
def test_a_name_of_an_area_where_a_place_is_expected_is_no_rule_and_is_said_to_be_unread(
    client: TestClient, text: str
):
    found = read(client, text)

    assert found["clarify"] == [] and found["applied"] == []
    assert [offer["target"] for offer in found["suggestions"]] == [
        "tag:leafy",
        "tag:quiet_residential",
    ]
    assert text.split()[-1] in " ".join(words(text, found["unread"]))
    assert "other" in found["unmet"]


# A sentence of its own that asks, and a part of a sentence that does.
ASKED_BY_THE_RULES = ["Maybe somewhere leafy. 30 minutes to Pellam.", TYPED]


@pytest.mark.parametrize("text", ASKED_BY_THE_RULES)
def test_where_a_model_reads_nothing_of_a_journey_its_words_are_said_to_be_unread(text: str):
    found = through_the_route(model_output(), text)

    assert found["clarify"] == [] and found["operations"]["commute_ops"] == []
    assert not [offer for offer in found["suggestions"] if offer["target"] in ("commute", "area")]
    assert "30 minutes to Pellam" in " / ".join(words(text, found["unread"]))
    assert "other" in found["unmet"]


def test_what_is_unread_beside_a_question_that_is_dropped_is_one_stretch_with_it():
    text = "bleh, I work at Pellam"

    found = through_the_route(model_output(), text)

    assert words(text, found["unread"]) == [text]


def test_what_asks_for_nothing_beside_a_question_that_is_dropped_is_not_said_with_it():
    """What is said of the words alone asks for nothing, as the speaker does after it."""
    text = "honestly, I work at Pellam"

    found = through_the_route(model_output(), text)

    assert words(text, found["unread"]) == ["work at Pellam"]
    assert "other" in found["unmet"]


@pytest.mark.parametrize("text", ASKED_BY_THE_RULES)
def test_where_a_model_reads_the_journey_it_is_offered_and_none_of_its_words_is_unread(
    text: str,
):
    journey = model_commute(destination_text="Pellam", max_minutes=30, words="30 minutes to Pellam")

    found = through_the_route(model_output(commute_ops=[journey]), text)

    [offer] = [offer for offer in found["suggestions"] if offer["target"] == "commute"]
    assert offer["asks_place"] and [option["name"] for option in offer["options"]] == PELLAM
    assert not [offer for offer in found["suggestions"] if offer["target"] == "area"]
    assert not any("Pellam" in left or "30" in left for left in words(text, found["unread"]))
