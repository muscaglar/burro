"""The service on a release that holds no journey time: a journey is estimated, and said to be.

The release here is the committed synthetic one with its journey times taken
out, and each area said to have its homes at the point inside it. It is made
up, and describes no real place. It is shaped as a build of London is before a
timetable has been read: it names its places, and holds a time to none.
"""

import io
import json
from collections import Counter
from functools import cache
from typing import Any

import pytest
from burro_api import logs
from burro_core import ENGINE_VERSION
from burro_core.estimate import ESTIMATED, HOW
from burro_core.ids import Mode
from burro_core.release import InMemoryRelease, parse_release
from fastapi.testclient import TestClient

from .support import WORKS, client_for, commute, make_deps, release, renter, wire

MATRICES = ("pt_typical", "pt_just_missed", "cycle", "walk")
BANDS = {"likely_within", "borderline", "likely_beyond"}
# Against this many minutes the made-up areas stand in all three bands.
LIMIT = 30


@cache
def estimating() -> InMemoryRelease:
    found: dict[str, Any] = release().documents()  # pyright: ignore[reportAssignmentType]
    found["manifest.json"].update(preview=True)
    for area in found["neighbourhoods.json"]["neighbourhoods"]:
        area["homes_at"] = area["centroid"]
    travel = found["travel.json"]
    travel.update(source_ids=[], as_of=None, destination_ids=[])
    for matrix in MATRICES:
        travel[matrix] = [[] for _ in travel["area_ids"]]
    return parse_release(found)


@pytest.fixture
def client() -> TestClient:
    return client_for(make_deps(release=estimating()))


def ranked_on(client: TestClient, hard: bool = False, mode: Mode = Mode.PT) -> dict[str, Any]:
    spec = renter(commutes=(commute(WORKS, LIMIT, hard=hard).replace(mode=mode),))
    answer = client.post("/v1/rank", json={"spec": wire(spec), "limit": 100})
    assert answer.status_code == 200
    return answer.json()


def legs_of(body: dict[str, Any]) -> list[dict[str, Any]]:
    return [leg for area in body["data"]["ranked"] for leg in area["legs"]]


def test_the_service_says_how_a_journey_is_estimated_and_that_the_release_is_a_preview(
    client: TestClient,
):
    answer = client.get("/v1/meta")
    body = answer.json()
    assert body["meta"]["preview"] is True and answer.headers["X-Burro-Preview"] == "true"
    assert body["meta"]["engine_version"] == ENGINE_VERSION == "1.13.0"
    assert body["data"]["holds"]["journeys"] is True
    assert body["data"]["journey_estimate"] == HOW.model_dump(mode="json")
    assert body["data"]["journey_estimate"]["said"] == ESTIMATED


def test_a_release_that_holds_its_journey_times_says_nothing_of_an_estimate():
    whole = client_for(make_deps())
    assert whole.get("/v1/meta").json()["data"]["journey_estimate"] is None
    spec = renter(commutes=(commute(WORKS, LIMIT),))
    body = whole.post("/v1/rank", json={"spec": wire(spec), "limit": 100}).json()
    assert {leg["estimate"] for leg in legs_of(body)} == {None}
    assert "estimated" not in {leg["status"] for leg in legs_of(body)}


def test_a_journey_is_served_as_a_band_and_never_in_minutes(client: TestClient):
    body = ranked_on(client)
    legs = legs_of(body)
    assert legs and {leg["status"] for leg in legs} == {"estimated"}
    assert {leg["estimate"] for leg in legs} == BANDS
    for leg in legs:
        assert (leg["minutes"], leg["minutes_typical"], leg["minutes_just_missed"]) == (
            None,
            None,
            None,
        )
    # No figure of the answer is the estimate: what a journey is worth is one of three.
    assert {leg["utility"] for leg in legs} == {1.0, 0.5, 0.0}
    assert not body["data"]["filtered"]


def test_a_firm_limit_leaves_out_only_what_is_likely_beyond_it(client: TestClient):
    soft, firm = ranked_on(client), ranked_on(client, hard=True)
    beyond = {
        area["area_id"]
        for area in soft["data"]["ranked"]
        if area["legs"][0]["estimate"] == "likely_beyond"
    }
    assert beyond
    assert {one["area_id"]: one["reason"] for one in firm["data"]["filtered"]} == dict.fromkeys(
        beyond, "commute_likely_beyond"
    )
    assert {leg["estimate"] for leg in legs_of(firm)} == {"likely_within", "borderline"}
    assert not any(area["untested_filters"] for area in firm["data"]["ranked"])


def test_the_reasons_say_that_a_journey_is_estimated(client: TestClient):
    spec = renter(commutes=(commute(WORKS, LIMIT),))
    body = client.post("/v1/explanations", json={"spec": wire(spec), "limit": 5}).json()["data"]
    facts = {fact["fact_id"]: fact for fact in body["facts"]}
    journeys = [fact for fact in facts.values() if fact["kind"] == "travel"]
    assert journeys and {fact["template"] for fact in journeys} == {"travel_estimated"}
    for fact in journeys:
        assert fact["numbers"] == [str(LIMIT)] and fact["slots"]["estimated"] == ESTIMATED
        assert fact["sources"] and fact["as_of"]
    said = [
        sentence["text"]
        for one in body["explanations"]
        for sentence in [*one["reasons"], *([one["trade_off"]] if one["trade_off"] else [])]
        if facts[sentence["fact_ids"][0]]["kind"] == "travel"
    ]
    assert said and all(text.endswith(ESTIMATED) for text in said)
    assert not any(
        sentence["replaced"] for one in body["explanations"] for sentence in one["reasons"]
    )


def test_a_comparison_gives_the_band_of_each_area_and_no_minutes(client: TestClient):
    ranked = ranked_on(client)["data"]["ranked"]
    of_band: dict[str, str] = {}
    for area in ranked:
        of_band.setdefault(area["legs"][0]["estimate"], area["area_id"])
    chosen = [of_band[band] for band in sorted(BANDS)]
    spec = renter(commutes=(commute(WORKS, LIMIT, hard=True),))
    body = client.post("/v1/compare", json={"spec": wire(spec), "area_ids": chosen}).json()["data"]
    (journey,) = [row for row in body["rows"] if row["place"] is not None]
    assert [cell["estimate"] for cell in journey["cells"]] == sorted(BANDS)
    assert {cell["value"] for cell in journey["cells"]} == {None}
    cited = {fact["fact_id"]: fact["template"] for fact in body["facts"]}
    assert {cited[cell["fact_id"]] for cell in journey["cells"]} == {"travel_estimated"}
    assert Counter(area["status"] for area in body["areas"]) == {
        "ranked": 2,
        "commute_likely_beyond": 1,
    }
    # No other row holds a band: it is of a journey alone.
    others = [cell for row in body["rows"] if row["place"] is None for cell in row["cells"]]
    assert {cell["estimate"] for cell in others} == {None}


@pytest.mark.parametrize("mode", [Mode.CYCLE, Mode.WALK])
def test_by_bike_and_on_foot_nothing_is_estimated_and_the_journey_is_missing(
    client: TestClient, mode: Mode
):
    body = ranked_on(client, mode=mode)
    assert {leg["status"] for leg in legs_of(body)} == {"missing"}
    assert {leg["estimate"] for leg in legs_of(body)} == {None}
    spec = renter(commutes=(commute(WORKS, LIMIT).replace(mode=mode),))
    said = client.post("/v1/explanations", json={"spec": wire(spec), "limit": 5})
    assert said.status_code == 200
    templates = {fact["template"] for fact in said.json()["data"]["facts"]}
    assert "missing_journey" in templates and "travel_estimated" not in templates


def test_the_same_search_gives_the_same_answer(client: TestClient):
    first = json.dumps(ranked_on(client)["data"], sort_keys=True)
    assert all(json.dumps(ranked_on(client)["data"], sort_keys=True) == first for _ in range(5))


def test_an_area_says_where_its_homes_stand(client: TestClient):
    area = client.get("/v1/areas/syn-n0001").json()["data"]["area"]
    assert area["homes_at"] == area["centroid"]
    whole = client_for(make_deps()).get("/v1/areas/syn-n0001").json()["data"]["area"]
    assert whole["homes_at"] is None


def test_nothing_of_the_journey_is_written_to_the_log():
    lines = io.StringIO()
    logs.configure_logging(lines)
    client = client_for(make_deps(release=estimating()))
    ranked_on(client, hard=True)
    written = lines.getvalue().casefold()
    for marker in ("syn-p", "syn-d", "syn-n", "cindermoor", "/travel/", "likely_"):
        assert marker not in written
