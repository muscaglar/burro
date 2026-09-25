"""What the terms of a publisher ask to be said wherever its credit is shown.

The terms of the London Datastore ask whoever re-uses its data to state that the
Greater London Authority cannot warrant the quality or accuracy of the data. The
licence registry holds the statement with each source of the authority's, a
build carries it to the release with the credit, and the service serves it
wherever it serves the credit: with every source of route 11, which the page of
sources draws, and with the source of a fact wherever the credit stands beside
a figure. The credit itself stays as its publisher worded it.

The release here is the committed synthetic one, whose one source is given such
a statement, as a build gives one to a source the registry holds it for. It is
made up, and describes no real place.
"""

import dataclasses
from typing import Any

import pytest
from burro_core.release import InMemoryRelease
from fastapi.testclient import TestClient

from .support import client_for, make_deps, release

ASKED = "The publisher cannot warrant the quality or accuracy of the data."


def resting_on_it(*, beside_figures: bool) -> InMemoryRelease:
    """The committed release, with a source whose terms ask for the statement."""
    held = release()
    sources = tuple(
        source.replace(said_with_attribution=ASKED, credit_beside_figures=beside_figures)
        for source in held.manifest.sources
    )
    return dataclasses.replace(held, manifest=held.manifest.replace(sources=sources))


def data(response: Any) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    return response.json()["data"]


def served_by(client: TestClient) -> list[dict[str, Any]]:
    """Every source the service serves with a fact: of an area's page, and of what is ranked."""
    area = data(client.get("/v1/areas"))["areas"][0]["area_id"]
    found = data(client.post("/v1/interpret", json={"text": "leafy and quiet"}))
    explained = data(client.post("/v1/explanations", json={"spec": found["spec"], "limit": 3}))
    facts = [*data(client.get(f"/v1/areas/{area}"))["facts"], *explained["facts"]]
    assert facts
    return [source for fact in facts for source in fact["sources"]]


def test_a_release_that_rests_on_a_source_whose_terms_ask_for_it_serves_the_statement():
    client = client_for(make_deps(release=resting_on_it(beside_figures=False)))

    credits = data(client.get("/v1/meta"))["attributions"]

    assert credits
    for credit, held in zip(credits, release().manifest.sources, strict=True):
        assert credit["said_with_attribution"] == ASKED
        # The credit is as the publisher worded it, and holds none of the statement.
        assert credit["attribution"] == held.attribution
        assert ASKED not in credit["attribution"]


def test_a_release_that_rests_on_no_such_source_serves_none():
    client = client_for(make_deps())

    credits = data(client.get("/v1/meta"))["attributions"]

    assert credits and [credit["said_with_attribution"] for credit in credits] == [None] * len(
        credits
    )
    assert {source["said_with_attribution"] for source in served_by(client)} == {None}


@pytest.mark.parametrize("beside_figures", [True, False])
def test_a_fact_brings_the_statement_wherever_it_brings_the_credit(beside_figures: bool):
    client = client_for(make_deps(release=resting_on_it(beside_figures=beside_figures)))

    sources = served_by(client)

    for source in sources:
        if beside_figures:
            assert source["attribution"] and source["said_with_attribution"] == ASKED
        else:
            # The source is credited by its name and its publisher, and the statement
            # stands with its credit on the page of sources.
            assert (source["attribution"], source["said_with_attribution"]) == (None, None)
