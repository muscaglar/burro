"""What a person says of their own words is not said to be unread.

"Somewhere cheap, I think" was answered as "somewhere cheap" is: nothing
applied, nothing offered, and the line that Burro gives no verdict on what a
person can afford. But the answer said that "I think" was not read, and a
person reads that as something Burro missed. "I think" says nothing of what is
wanted. Set apart by a mark, in a part of its sentence of its own, it asks for
nothing, as the words that lead a wish in ask for nothing, and is left out of
what is said to be unread (contract, section 8.1).

"Cheap" is no word for the mix of brands, as "cheap and cheerful" is. It is
heard as a word for what a person can afford, and nothing is offered of it, by
itself or beside what is said of the words.

Nothing else moves. A prompt that holds such words is no more plain, `unmet`
holds `other` as it did, and a model is asked of it exactly as it was. No call
is made: where a model reads, a stand-in hands the answer to the reader.

Every sentence here is made up.
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from .support import client_for, make_deps, model_output, model_tag, through_the_route

# Every part of an answer that says what was made of the words, but what was not met.
MADE_OF_IT = ("status", "operations", "applied", "suggestions", "unread", "notice", "clarify")


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def read(client: TestClient, text: str) -> dict[str, Any]:
    response = client.post("/v1/interpret", json={"text": text})
    assert response.status_code == 200, response.text
    return response.json()["data"]


def unread(text: str, found: dict[str, Any]) -> list[str]:
    return [text[span["start"] : span["end"]] for span in found["unread"]]


def met(found: dict[str, Any]) -> list[str]:
    """What an answer says was not met, less that nothing was made of some word."""
    return [category for category in found["unmet"] if category != "other"]


@pytest.mark.parametrize(
    "text", ["somewhere cheap, I think", "honestly, somewhere cheap", "I think, somewhere cheap"]
)
def test_somewhere_cheap_is_answered_beside_such_words_as_it_is_by_itself(
    client: TestClient, text: str
):
    found, by_itself = read(client, text), read(client, "somewhere cheap")

    for part in MADE_OF_IT:
        assert found[part] == by_itself[part], part
    assert (found["status"], found["suggestions"], found["unread"]) == ("ok", [], [])
    assert not any(found["operations"].values())
    assert met(found) == met(by_itself) == ["affordability_verdict"]
    # The search it returns is the search it was given, as it is of the word by itself.
    assert found["spec"] == by_itself["spec"]


# What was typed, and the same words with nothing said of them.
READ_ALIKE = [
    ("somewhere posh, honestly", "somewhere posh"),
    ("leafy and quiet, I guess", "leafy and quiet"),
    ("somewhere cheap and cheerful, I think", "somewhere cheap and cheerful"),
    ("a park, to be honest", "a park"),
    ("I think, a park, ideally", "a park"),
    ("low crime and leafy, honestly", "low crime and leafy"),
]


@pytest.mark.parametrize(("text", "alone"), READ_ALIKE)
def test_nothing_is_said_to_be_unread_of_what_is_said_of_the_words_alone(
    client: TestClient, text: str, alone: str
):
    found, by_itself = read(client, text), read(client, alone)

    assert found["unread"] == []
    assert met(found) == met(by_itself)
    # Nothing of it is applied for that: the prompt is no more plain than it was.
    assert not any(found["operations"].values())
    assert found["status"] == "suggest"


@pytest.mark.parametrize(
    ("text", "left"),
    [
        # A word that is on no list is unread, with the stretch it stands in.
        ("somewhere posh, bleh", ["bleh"]),
        ("somewhere posh, honestly, bleh", ["honestly, bleh"]),
        ("honestly bleh, somewhere posh", ["honestly bleh, somewhere"]),
        # No mark sets it apart, so it is a word the reader does not know.
        ("somewhere posh I think", ["I think"]),
        ("a park honestly", ["honestly"]),
        # It may stand for a wish that is not, and is on no list of such words.
        ("a park, maybe", ["maybe"]),
        ("a park, I think not", ["I think not"]),
    ],
)
def test_what_is_no_such_phrase_or_is_not_set_apart_is_said_to_be_unread_as_it_was(
    client: TestClient, text: str, left: list[str]
):
    found = read(client, text)

    assert unread(text, found) == left
    assert "other" in found["unmet"]


@pytest.mark.parametrize("text", ["leafy, honestly", "somewhere cheap, I think"])
def test_a_model_is_asked_of_a_prompt_that_holds_such_words_as_it_was(text: str):
    """`other` says that nothing was made of some word, and is what a model is asked by."""
    found = through_the_route(model_output(tag_ops=[model_tag("leafy", words="leafy")]), text)

    assert found["interpreter"] == "model"
    assert "other" in found["unmet"]
    assert found["unread"] == []


def test_the_rules_say_that_nothing_was_made_of_them_as_they_did(client: TestClient):
    found = read(client, "leafy, honestly")

    assert (found["interpreter"], found["unread"]) == ("rule", [])
    assert "other" in found["unmet"]
    assert found["model_pending"] is False
