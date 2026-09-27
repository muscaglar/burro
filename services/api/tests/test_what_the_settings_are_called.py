"""No word the service serves for a person to read calls the settings "the settings".

The founder walked the website and named them "Space requirements". The website
says so. The service went on serving two sentences that a client shows as they
come and that named the settings: what Burro says it is for, where nothing that
was typed is about a place, and what people are told goes to a language model
with their words. And a search that is kept, of which nothing was asked, was
named for "Burro's usual settings".

The name of the setting of the service that decides what is sent, and the field
that says whether it is, are read by whoever runs the service and by a client's
code, and are as they were. Every sentence here is made up.
"""

import json
import re
from typing import Any

import pytest
from burro_api.accounts.names import name_of
from burro_api.providers.terms import SETTINGS, TERMS, WORDS_ALONE
from burro_core.ids import Notice, Tenure
from burro_core.interpret import NOTICES
from burro_core.spec import default_spec
from fastapi.testclient import TestClient

from .support import client_for, make_deps, model_output, release, through_the_route, wire

NAMES_THEM = re.compile(r"\bsettings?\b", re.IGNORECASE)
# What a client's code reads, and no person: the name of a field.
A_FIELD = re.compile(r'"[a-z_]+":')
SENTENCES = [
    "what is the capital of France",
    "Honestly, somewhere lively",
    "I never use the station",
    "my mum is after a park",
    "somewhere posh",
    "Honestly, renting, max £1,900 a month, 40 minutes to Pellam Cross at the very most",
    "young professionals",
]


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def data(response: Any) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    return response.json()["data"]


def read_by_a_person(served: Any) -> str:
    """Every string of an answer, less the names of its fields."""
    return A_FIELD.sub("", json.dumps(served, ensure_ascii=False))


def test_what_burro_says_it_is_for_names_the_space_requirements():
    text = "What is the best way to learn the piano"
    found = through_the_route(model_output(status="off_topic"), text)

    assert found["status"] == "off_topic"
    assert found["notice_text"] == NOTICES[Notice.OFF_TOPIC]
    assert "choose your space requirements" in found["notice_text"]
    assert not NAMES_THEM.search(found["notice_text"])


def test_what_people_are_told_goes_with_their_words_names_the_space_requirements():
    assert SETTINGS == (
        "With it go your space requirements: your budget, whether you rent, buy or visit, how "
        "long you will travel, what matters to you, and the areas you have ruled in or out."
    )
    assert WORDS_ALONE == "Your words go alone: none of your space requirements is sent with them."
    for terms in TERMS.values():
        for sent in (True, False):
            assert not NAMES_THEM.search(terms.notice(with_settings=sent))


@pytest.mark.parametrize("text", SENTENCES)
def test_no_word_of_an_answer_of_route_1_names_the_settings(client: TestClient, text: str):
    for spec in (None, wire(default_spec(Tenure.VISIT))):
        body = {"text": text} | ({"spec": spec} if spec is not None else {})
        found = data(client.post("/v1/interpret", json=body))
        told = {key: value for key, value in found.items() if key not in ("spec", "operations")}
        assert not NAMES_THEM.search(read_by_a_person(told)), text


@pytest.mark.parametrize("tenure", list(Tenure))
def test_the_name_of_a_search_that_is_kept_names_no_settings(tenure: Tenure):
    named = name_of(default_spec(tenure), release())

    assert named.endswith("with what Burro counts in every search")
    assert not NAMES_THEM.search(named)


def test_no_word_route_11_gives_a_person_to_read_names_the_settings(client: TestClient):
    found = data(client.get("/v1/meta"))

    # Whether the search goes with the words is a field, which a client's code reads.
    assert found["reader"]["settings_sent"] is False
    assert not NAMES_THEM.search(read_by_a_person(found))
