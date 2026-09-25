"""A release that carries a name a person gave is served by that name.

A person may give a vibe another name, and a measure another label, at the panel of the
review desk, and a build carries them (ADR 0029). The release here is the made-up city
with one vibe and one measure named otherwise. No name here is of a real place.
"""

import dataclasses
import json
from typing import Any

import pytest
from burro_core.ids import FeatureId, TagId
from burro_core.release import InMemoryRelease
from fastapi.testclient import TestClient

from .support import client_for, make_deps, release, renter, wire

GIVEN = "Green and leafy"
LABEL = "Nitrogen dioxide in the air, as a mean over the year"


def renamed() -> InMemoryRelease:
    held = release()
    return dataclasses.replace(
        held,
        vibes=tuple(
            vibe.replace(label=GIVEN, short_label=GIVEN) if vibe.tag_id is TagId.LEAFY else vibe
            for vibe in held.vibes
        ),
        metrics=tuple(
            metric.replace(label=LABEL, short_label="Nitrogen dioxide")
            if metric.feature_id is FeatureId.AIR_NO2
            else metric
            for metric in held.metrics
        ),
    )


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps(release=renamed()))


def spec_of(client: TestClient) -> dict[str, Any]:
    found = client.post("/v1/interpret", json={"text": "leafy, clean air", "spec": wire(renter())})
    return found.json()["data"]["spec"]


def names(body: Any) -> list[str]:
    """Every name and label an answer holds, wherever it holds it."""
    found: list[str] = []

    def walk(held: Any) -> None:
        if isinstance(held, dict):
            for key, value in held.items():  # pyright: ignore[reportUnknownVariableType]
                if key in ("label", "short_label", "name", "text") and isinstance(value, str):
                    found.append(value)
                walk(value)
        elif isinstance(held, list):
            for one in held:  # pyright: ignore[reportUnknownVariableType]
                walk(one)

    walk(body)
    return found


def test_the_catalogue_that_is_served_says_the_names_the_release_carries(client: TestClient):
    meta = client.get("/v1/meta").json()["data"]
    leafy = next(tag for tag in meta["tags"] if tag["tag_id"] == "leafy")
    no2 = next(feature for feature in meta["features"] if feature["feature_id"] == "air_no2")
    assert (leafy["label"], no2["label"]) == (GIVEN, LABEL)


@pytest.mark.parametrize("route", ["areas", "explanations", "compare"])
def test_an_answer_says_the_name_a_person_gave_and_never_cores_own(client: TestClient, route: str):
    spec = spec_of(client)
    ranked = client.post("/v1/rank", json={"spec": spec, "limit": 2}).json()["data"]["ranked"]
    first, second = (one["area_id"] for one in ranked)
    answers = {
        "areas": lambda: client.get(f"/v1/areas/{first}"),
        "explanations": lambda: client.post("/v1/explanations", json={"spec": spec, "limit": 2}),
        "compare": lambda: client.post(
            "/v1/compare", json={"area_ids": [first, second], "spec": spec}
        ),
    }
    body = answers[route]().json()
    said = names(body)
    assert any(GIVEN in one for one in said), route
    assert not [one for one in said if one == "Leafy" or one.startswith("Leafy:")], route
    assert "Modelled annual mean nitrogen dioxide" not in json.dumps(body), route
