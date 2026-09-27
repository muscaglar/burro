"""The service passes on no word that says a vibe is a rough guide.

The founder walked the website and wrote: "remove the concept of rough guide,
we don't want to pass this on to a user". The website stopped drawing the label
and the sentence. The service went on serving both, in words that a client
shows as they come: in `rough_guides` of route 11, at the end of the note of
every offer of Village feel, and in the note of a word for character, "a
village feel (a rough guide)".

What is measured stands. Village feel is served on its recipe, is applied from
no word, is taken by a press of its own and is on a result only where it was
asked for. Which vibe it is is still told, by `sureness` of the vibe, which is
an id and no words. The shape of every answer is as it was: `rough_guides` is
a list still, and holds nothing (contract, sections 3.2 and 9.2).

The caution on recorded rents said that Burro uses them "as a rough guide to
what a home lets for". It was said of rents and of no vibe, and was set aside
here. They were the last words the service served that said it, and a client
shows them as they come: it says "a general idea" now, and nothing is set aside.
Every area here is made up.
"""

import json
import re
from typing import Any

import pytest
from burro_core.catalogue import ROUGH_GUIDE, ROUGH_GUIDES, WHY_A_ROUGH_GUIDE
from burro_core.facts import RENT_CAUTION
from burro_core.ids import TagId
from fastapi.testclient import TestClient

from .support import client_for, make_deps, model_output, model_tag, through_the_route
from .test_a_rent_of_a_wider_place import let

# The label, and what opens and what closes the sentence of the one vibe that is less sure.
SAYS_SO = re.compile(r"rough guide|less sure|seemed like villages", re.IGNORECASE)
VILLAGE = "tag:village_feel"
NAMES_IT = ("villagey", "a village feel", "village feel, honestly", "I like villages")
FOR_CHARACTER = ("a real identity", "somewhere with character, honestly", "its own feel")


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def data(response: Any) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    return response.json()["data"]


def words_of(served: Any) -> str:
    """Every string of an answer."""
    return json.dumps(served, ensure_ascii=False)


def test_core_holds_the_words_still_and_they_are_the_ones_that_are_looked_for():
    """The review desk shows them to whoever decides a recipe. No client is handed them."""
    assert {TagId.VILLAGE_FEEL} == ROUGH_GUIDES
    assert SAYS_SO.search(ROUGH_GUIDE)
    assert all(SAYS_SO.search(sentence) for sentence in WHY_A_ROUGH_GUIDE.values())


def test_route_11_holds_nothing_to_stand_beside_a_vibe_and_says_which_vibe_by_an_id(
    client: TestClient,
):
    found = data(client.get("/v1/meta"))

    # The shape is as it was: a list, which holds nothing.
    assert found["rough_guides"] == []
    sure = {tag["tag_id"]: tag["sureness"] for tag in found["tags"]}
    assert [tag_id for tag_id, said in sure.items() if said == "rough_guide"] == ["village_feel"]
    assert not SAYS_SO.search(words_of(found))


@pytest.mark.parametrize("text", NAMES_IT)
def test_the_offer_of_the_vibe_says_nothing_of_how_sure_it_is(client: TestClient, text: str):
    found = data(client.post("/v1/interpret", json={"text": text}))

    (offer,) = [one for one in found["suggestions"] if one["target"] == VILLAGE]
    assert (offer["label"], offer["does"], offer["note"]) == (
        "Village feel",
        "Add Village feel.",
        "",
    )
    assert not SAYS_SO.search(words_of(found))
    # It is taken by a press of its own still, and by no press that takes it with others.
    assert [(way["id"], way["guess"]) for way in offer["choices"]] == [
        ("more", False),
        ("ignore", False),
    ]
    assert offer["add_all"] == "" and found["applied"] == []


@pytest.mark.parametrize("text", FOR_CHARACTER)
def test_the_note_of_a_word_for_character_names_a_village_feel_and_nothing_more(
    client: TestClient, text: str
):
    found = data(client.post("/v1/interpret", json={"text": text}))

    notes = {offer["target"]: offer["note"] for offer in found["suggestions"]}
    assert VILLAGE in notes
    assert "a village feel, the age of the buildings and a town centre nearby" in notes[VILLAGE]
    assert not SAYS_SO.search(words_of(found))


def test_what_a_model_reads_of_it_is_offered_with_no_word_of_how_sure_it_is():
    text = "honestly, somewhere that feels like a village"
    reads = model_output(tag_ops=[model_tag("village_feel", toward="high", words=text)])

    found = through_the_route(reads, text)

    (offer,) = [one for one in found["suggestions"] if one["target"] == VILLAGE]
    assert offer["note"] == "" and offer["add_all"] == ""
    assert not [way for way in offer["choices"] if way["guess"]]
    assert not SAYS_SO.search(words_of(found))


def test_no_answer_of_a_search_that_asked_for_it_says_how_sure_it_is(client: TestClient):
    found = data(client.post("/v1/interpret", json={"text": "villagey"}))
    (offer,) = found["suggestions"]
    pressed = {"spec": found["spec"], "operations": offer["choices"][0]["operations"]}
    ranked = data(client.post("/v1/rank", json=pressed | {"limit": 24}))
    assert [tag["tag_id"] for tag in ranked["spec"]["tags"]] == ["village_feel"]
    explained = data(client.post("/v1/explanations", json={"spec": ranked["spec"], "limit": 5}))
    first, second = (area["area_id"] for area in ranked["ranked"][:2])
    compared = data(
        client.post("/v1/compare", json={"area_ids": [first, second], "spec": ranked["spec"]})
    )
    page = data(client.get(f"/v1/areas/{first}"))

    for served in (ranked, explained, compared, page):
        assert not SAYS_SO.search(words_of(served))
    assert "village_feel" in json.dumps(explained)


def test_what_is_said_of_recorded_rents_says_nothing_of_a_rough_guide():
    """On a release whose rents are of a wider place: route 11, an area, and a budget to rent."""
    client = client_for(make_deps(release=let()))
    told = data(client.get("/v1/meta"))
    first = data(client.get("/v1/areas"))["areas"][0]["area_id"]
    area = data(client.get(f"/v1/areas/{first}"))
    offered = data(
        client.post("/v1/interpret", json={"text": "Honestly, renting, max £1,900 a month"})
    )

    assert told["rents"]["caution"] == RENT_CAUTION
    assert RENT_CAUTION in words_of(area) and RENT_CAUTION in words_of(offered)
    for served in (told, area, offered):
        assert not SAYS_SO.search(words_of(served))
    assert not re.search(r"\brough\b", RENT_CAUTION)
