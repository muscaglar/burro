"""Route 13, the census of one area, and the tests that try to reach it from a search.

The census is shown on an area's page and used for nothing else. So most of
what is held here is what cannot be done: no search, comparison, share,
explanation, log line or model is ever handed a figure of it, and moving the
figures from one area to another changes no other answer.
"""

import json
import re
from collections.abc import Iterator, Sequence
from functools import cache
from pathlib import Path
from typing import Any, cast

import pytest
from burro_api import loading
from burro_api.app import deps_from
from burro_api.cli import main
from burro_api.deps import Deps
from burro_api.loading import load_census
from burro_api.logs import LOGGABLE
from burro_api.settings import SYNTHETIC_CENSUS, SYNTHETIC_FIXTURE, Settings
from burro_api.wire import BODIES
from burro_core.catalogue import COUNTS_RESIDENTS
from burro_core.census import (
    CENSUS,
    FEWER,
    MADE_UP,
    MANIFEST,
    SHOWN_AND_NEVER_RANKED_ON,
    Census,
    CensusError,
    CensusKind,
)
from burro_core.ids import Direction, FeatureId, Provenance, TagId, Toward
from burro_core.spec import FeatureWeight, PreferenceSpec, TagWeight, check_spec
from fastapi import FastAPI
from fastapi.testclient import TestClient

from .support import (
    MODEL,
    WORKS,
    FakeModelClient,
    Seen,
    census,
    client_for,
    make_deps,
    model_output,
    reader_asking,
    release,
    renter,
    searching,
    watching,
    wire,
)

ROUTE = "/v1/areas/{id_or_slug}/census"
SEARCHES = 60
# `make ci` runs every fifth of them. `make test ARGS="-m full"` runs them all.
EVERY = 5
AREA = "foxholt"
AREA_ID = "syn-n0007"
COMMITTED = Path(__file__).resolve().parents[3] / "contracts" / "openapi.json"


def at(area: str) -> str:
    return f"/v1/areas/{area}/census"


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with client_for(make_deps()) as kept:
        yield kept


def data(response: Any) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    return response.json()["data"]


def code(response: Any) -> tuple[int, str]:
    return response.status_code, response.json()["error"]["code"]


def canaries(found: Census | None = None) -> list[str]:
    """What is in the census and nowhere else: every heading, label and code of a row.

    The made-up count names groups that are in no release, no catalogue and no
    sentence. If one is seen outside route 13, the census leaked.
    """
    found = found or census()
    rows = [row for table in found.tables for row in table.rows]
    marks = {table.table_code for table in found.tables}
    marks |= {row.code for row in rows}
    marks |= {row.heading for row in rows if "made-up" in row.heading.casefold()}
    marks |= {table.title for table in found.tables}
    return sorted(mark.casefold() for mark in marks)


def holds_a_canary(text: str) -> list[str]:
    folded = text.casefold()
    return [mark for mark in canaries() if mark in folded]


# --- What the route serves ------------------------------------------------------------


def test_the_census_of_an_area_is_served_by_its_id_and_by_its_slug(client: TestClient):
    by_slug, by_id = client.get(at(AREA)), client.get(at(AREA_ID))
    assert by_slug.json() == by_id.json()
    found = data(by_slug)
    assert found["area_id"] == AREA_ID and found["heading"] == MADE_UP.heading
    assert [table["kind"] for table in found["tables"]] == [
        "households",
        "country_of_birth",
        "age",
        "ethnic_group",
        "religion",
    ]


def test_a_figure_is_a_share_with_its_count_beside_the_citys_share(client: TestClient):
    found = data(client.get(at(AREA)))
    assert found["city"] == "Quillhaven"
    for table in found["tables"]:
        assert table["columns"]["share"] == "Foxholt"
        assert table["columns"]["city"] == "Quillhaven"
        for row in table["rows"]:
            assert set(row) == {
                "code",
                "heading",
                "label",
                "depth",
                "share",
                "percent",
                "count",
                "city_share",
                "city_percent",
            }
            assert re.fullmatch(r"([1-9][0-9]?|100)%|over 99%|fewer than 1 in 100", row["share"])
            assert row["city_share"]
            if row["share"] == FEWER:
                assert row["count"] is None and row["percent"] is None
            else:
                assert re.fullmatch(r"[1-9][0-9]?(,[0-9]{3})*|[1-9][0-9]{0,2}", row["count"])
                assert int(row["count"].replace(",", "")) >= 10


def test_every_table_says_its_area_its_day_and_how_many_were_counted(client: TestClient):
    found = data(client.get(at(AREA)))
    assert "21 March 2021" in found["date_line"]
    for table in found["tables"]:
        assert re.search(r"21 March 2021\. .* in Foxholt, .* About [0-9,]+00 ", table["caption"])


def test_what_is_shown_and_never_ranked_on_says_so(client: TestClient):
    found = data(client.get(at(AREA)))
    said = {table["kind"]: table["shown_only"] for table in found["tables"]}
    never = {kind.value for kind in SHOWN_AND_NEVER_RANKED_ON}
    assert {kind for kind, line in said.items() if line} == never
    assert {line for line in said.values() if line} == {MADE_UP.shown_only}


def test_the_rows_are_served_in_the_order_the_census_holds_them(client: TestClient):
    found = data(client.get(at(AREA)))
    for table, held in zip(found["tables"], census().tables, strict=True):
        assert [row["code"] for row in table["rows"]] == [row.code for row in held.rows]
        shares = [row["percent"] or 0 for row in table["rows"]]
        # It is not the order of the figures, either way.
        assert shares != sorted(shares) and shares != sorted(shares, reverse=True)


def test_an_area_with_too_few_and_one_the_count_does_not_hold_say_so(client: TestClient):
    few, none = data(client.get(at("grapnel-dock"))), data(client.get(at("otterby-fields")))
    assert {table["reason"] for table in few["tables"]} == {"too_few"}
    assert {table["reason"] for table in none["tables"]} == {"not_held"}
    for table in (*few["tables"], *none["tables"]):
        assert table["rows"] == [] and table["left_out"]
        # No figure is given where none is held: nothing is filled in.
        assert not re.search(r"\d", table["left_out"] + table["caption"])


def test_every_area_of_the_release_has_an_answer(client: TestClient):
    for area in release().neighbourhoods:
        assert data(client.get(at(area.slug)))["area_id"] == area.area_id


def test_an_area_the_release_lacks_is_not_found(client: TestClient):
    assert code(client.get(at("nowhere"))) == (404, "area_not_found")
    assert code(client.get(at("syn-n0099"))) == (404, "area_not_found")


def test_every_answer_says_that_the_figures_are_made_up(client: TestClient):
    for path in (at(AREA), at("nowhere"), f"{at(AREA)}?a=1"):
        answered = client.get(path)
        assert answered.headers["x-burro-synthetic"] == "true"
        assert answered.json()["meta"]["synthetic"] is True


# --- The route takes nothing -------------------------------------------------------------

QUERIES = (
    "sort=share",
    "order=desc",
    "compare=syn-n0001",
    "area=syn-n0001&area=syn-n0002",
    "kind=ethnic_group",
    "min=20",
    "x",
    "=",
)


@pytest.mark.parametrize("query", QUERIES)
def test_the_census_route_takes_nothing(client: TestClient, query: str):
    """A query could only ask for more than one area's own table, so none is read."""
    refused = client.get(f"{at(AREA)}?{query}")
    assert code(refused) == (422, "invalid_request")
    assert refused.json()["error"]["fields"] == []
    assert not holds_a_canary(refused.text)


def test_the_census_route_takes_no_body_and_no_other_method(client: TestClient):
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        refused = client.request(method, at(AREA), json={"area_ids": ["syn-n0001", "syn-n0002"]})
        assert code(refused) == (405, "method_not_allowed")
    document = cast(FastAPI, client.app).openapi()
    operation = document["paths"][ROUTE]
    assert set(operation) == {"get"} and "requestBody" not in operation["get"]
    assert [each["in"] for each in operation["get"]["parameters"]] == ["path"]


def test_no_route_serves_the_census_of_more_than_one_area(client: TestClient):
    """So no client can put one area before another by a figure, or set two side by side."""
    document = cast(FastAPI, client.app).openapi()
    serving = [
        path
        for path, item in document["paths"].items()
        for operation in item.values()
        if "CensusPanel" in json.dumps(operation)
    ]
    assert serving == [ROUTE]
    for path in ("/v1/census", "/v1/areas/census", "/v1/areas/geometry/census"):
        assert client.get(path).status_code == 404
    panel = document["components"]["schemas"]["CensusPanel"]
    assert panel["properties"]["area_id"]["type"] == "string"
    assert "areas" not in panel["properties"]


def test_the_census_route_may_not_be_kept_or_indexed(client: TestClient):
    answered = client.get(at(AREA), headers={"if-none-match": '"syn-2026-09-23-01"'})
    assert answered.status_code == 200
    assert answered.headers["cache-control"] == "no-store"
    assert answered.headers["x-robots-tag"] == "noindex, nosnippet"
    assert "etag" not in answered.headers


# --- It can be switched off ------------------------------------------------------------


def test_the_census_route_can_be_switched_off():
    off = client_for(make_deps(census=None))
    assert code(off.get(at(AREA))) == (404, "census_not_available")
    # An area the release lacks is still said to be no area, whatever is served of the rest.
    assert code(off.get(at("nowhere"))) == (404, "area_not_found")
    assert data(off.get("/v1/meta"))["census"] == {"available": False, "heading": "", "intro": ""}


def test_the_block_that_offers_the_census_holds_no_figure_and_names_no_area(client: TestClient):
    offered = data(client.get("/v1/meta"))["census"]
    assert offered["available"] is True and offered["heading"] == MADE_UP.heading
    assert "%" not in offered["intro"] and not holds_a_canary(json.dumps(offered))
    assert not [area.name for area in release().neighbourhoods if area.name in offered["intro"]]


def test_one_word_in_the_environment_serves_no_census():
    assert Settings.from_env({}).census_dir == SYNTHETIC_CENSUS
    for word in ("off", "OFF", " off "):
        settings = Settings.from_env({"BURRO_CENSUS": word})
        assert settings.census_dir is None
        assert deps_from(settings).census is None
    assert deps_from(Settings.from_env({})).census == census()


def test_the_census_of_a_release_is_looked_for_beside_it(tmp_path: Path):
    folder = tmp_path / SYNTHETIC_FIXTURE.name
    settings = Settings.from_env({"BURRO_RELEASE_DIR": str(folder)})
    assert settings.census_dir == tmp_path.resolve() / SYNTHETIC_CENSUS.name
    # A folder that is not there is no census, and the service starts without one.
    assert load_census(settings.census_dir, release()) is None


def test_a_census_that_was_named_and_is_not_there_stops_the_service(tmp_path: Path):
    settings = Settings.from_env({"BURRO_CENSUS_DIR": str(tmp_path / "nowhere")})
    with pytest.raises(CensusError) as caught:
        deps_from(settings)
    assert caught.value.rule == loading.FOLDER_IS_READABLE


def copied(tmp_path: Path) -> Path:
    folder = tmp_path / SYNTHETIC_CENSUS.name
    folder.mkdir()
    for file in SYNTHETIC_CENSUS.iterdir():
        (folder / file.name).write_bytes(file.read_bytes())
    return folder


def test_a_census_that_breaks_a_rule_stops_the_service_in_one_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    folder = copied(tmp_path)
    (folder / CENSUS).write_bytes((folder / CENSUS).read_bytes() + b" ")
    monkeypatch.setenv("BURRO_CENSUS_DIR", str(folder))
    assert main(["serve"]) == 2
    err = capsys.readouterr().err.strip().splitlines()[-1]
    assert err == (
        f"error: the census could not be loaded: {folder}: {CENSUS} [files_match_manifest]"
    )


def test_a_census_is_read_whatever_the_finder_left_beside_it(tmp_path: Path):
    folder = copied(tmp_path)
    (folder / loading.IGNORED).write_bytes(b"\x00")
    assert load_census(folder, release()) == census()
    (folder / "notes.txt").write_bytes(b"mine")
    with pytest.raises(CensusError) as caught:
        load_census(folder, release())
    assert (caught.value.file, caught.value.rule) == ("notes.txt", "files_match_manifest")
    assert sorted(file.name for file in SYNTHETIC_CENSUS.iterdir()) == [CENSUS, MANIFEST]


def test_a_service_cannot_be_made_with_the_census_of_another_release():
    other = census().replace(release_id="syn-2026-09-23-02")
    with pytest.raises(ValueError, match="made for another release"):
        make_deps(census=other)


# --- It never reaches ranking: the tests that try -----------------------------------------

KINDS = [kind.value for kind in CensusKind]
NEVER = sorted(kind.value for kind in SHOWN_AND_NEVER_RANKED_ON)
# What a caller might call them, beside what Burro calls them.
NAMES = [*KINDS, "ethnicity", "race", "faith", "born_abroad", "census", "residents", "syn-grp-01"]


def spec_with(**changes: Any) -> dict[str, Any]:
    return wire(searching()) | changes


def weight(feature_id: str) -> dict[str, Any]:
    return {"feature_id": feature_id, "weight": 1.0, "direction": "more", "provenance": "stated"}


def tag(tag_id: str) -> dict[str, Any]:
    return {"tag_id": tag_id, "weight": 1.0, "toward": "high", "provenance": "stated"}


def specs_that_ask(name: str) -> list[dict[str, Any]]:
    """Every way a spec could be written to ask for a census figure."""
    spec = wire(searching())
    return [
        spec_with(weights=[*spec["weights"], weight(name)]),
        spec_with(tags=[*spec["tags"], tag(name)]),
        spec_with(**{name: 1.0}),
        spec_with(census={name: {"min": 20}}),
        spec_with(filters=[{"kind": name, "row": "syn-grp-02", "at_least": 20}]),
        spec_with(area_rules=[{"kind": name, "area_id": AREA_ID}]),
    ]


def edits_that_ask(name: str) -> list[dict[str, Any]]:
    nothing: dict[str, Any] = {
        "budget_ops": [],
        "commute_ops": [],
        "weight_ops": [],
        "tag_ops": [],
        "area_ops": [],
        "setting_ops": [],
    }
    nudge = {"action": "set", "value": 1.0, "step": "none", "provenance": "stated"}
    return [
        nothing | {"weight_ops": [nudge | {"feature_id": name, "direction": "more"}]},
        nothing | {"tag_ops": [nudge | {"tag_id": name, "toward": "high"}]},
        nothing | {"setting_ops": [nudge | {"setting": name, "choice": "none"}]},
        nothing | {"census_ops": [nudge | {"kind": name}]},
    ]


def refused(response: Any) -> bool:
    """Refused for what was sent, by a code of the contract, and with nothing of the census."""
    return (
        response.status_code == 422
        and response.json()["error"]["code"]
        in {"invalid_spec", "invalid_operations", "invalid_request", "invalid_compare"}
        and not holds_a_canary(response.text)
    )


@pytest.mark.parametrize("name", NAMES)
def test_no_search_can_ask_for_a_census_figure(client: TestClient, name: str):
    for spec in specs_that_ask(name):
        assert refused(client.post("/v1/rank", json={"spec": spec})), name
        assert refused(client.post("/v1/interpret", json={"text": "leafy", "spec": spec})), name
    for edits in edits_that_ask(name):
        sent = {"spec": wire(searching()), "operations": edits}
        assert refused(client.post("/v1/rank", json=sent)), name
    for extra in ({"census": True}, {"sort": name}, {"kinds": [name]}, {name: True}):
        assert refused(client.post("/v1/rank", json={"spec": wire(searching())} | extra)), name


@pytest.mark.parametrize("name", NAMES)
def test_no_comparison_can_ask_for_a_census_figure(client: TestClient, name: str):
    areas = {"area_ids": ["syn-n0001", "syn-n0002"]}
    for spec in specs_that_ask(name):
        assert refused(client.post("/v1/compare", json=areas | {"spec": spec})), name
    for extra in ({"census": True}, {"rows": [name]}, {"kinds": [name]}, {name: True}):
        sent = areas | {"spec": wire(searching())} | extra
        assert refused(client.post("/v1/compare", json=sent)), name


@pytest.mark.parametrize("name", NAMES)
def test_no_share_and_no_explanation_can_ask_for_a_census_figure(client: TestClient, name: str):
    for spec in specs_that_ask(name):
        assert refused(client.post("/v1/shares", json={"spec": spec})), name
        assert refused(client.post("/v1/explanations", json={"spec": spec})), name
    for path in ("/v1/shares", "/v1/explanations"):
        sent = {"spec": wire(searching()), "census": [name]}
        assert refused(client.post(path, json=sent)), name


def test_no_body_the_service_takes_has_a_field_for_a_census_figure():
    # A measure of the catalogue that counts who lived somewhere is named by its id, as
    # any measure is: it is a feature of the release, and no figure of the census. A body
    # can weigh it, and can hold nothing of the census itself.
    measures = sorted(feature_id.value for feature_id in COUNTS_RESIDENTS)
    assert measures == [
        "households_dependent_children",
        "households_one_person",
        "residents_aged_20_34",
        "residents_aged_65_over",
    ]
    for body in BODIES:
        schema = json.dumps(body.model_json_schema()).casefold()
        for measure in measures:
            schema = schema.replace(f'"{measure}"', "")
        for word in ("census", "ethnic", "religion", "country_of_birth", "residents"):
            assert word not in schema, (body.__name__, word)


def test_the_rows_of_a_comparison_hold_nothing_of_the_census(client: TestClient):
    areas = [area.area_id for area in release().neighbourhoods][:4]
    every = [weight(feature.value) for feature in FeatureId]
    carried = {metric.feature_id.value for metric in release().metrics}
    asked = spec_with(
        weights=[each | {"direction": "less"} for each in every if each["feature_id"] in carried],
        tags=[tag(vibe.tag_id.value) for vibe in release().vibes],
    )
    compared = client.post("/v1/compare", json={"area_ids": areas, "spec": asked})
    if compared.status_code == 422:
        # A direction a feature does not take is refused. The default spec is compared then.
        compared = client.post("/v1/compare", json={"area_ids": areas, "spec": wire(searching())})
    found = data(compared)
    components = {row["component"] for row in found["rows"]}
    assert components and not [each for each in components if each.split(":")[-1] in KINDS]
    assert not holds_a_canary(compared.text)
    assert not [fact for fact in found["facts"] if fact["kind"] in KINDS]


PROMPTS = (
    "somewhere with more of Made-up group A",
    "fewer people of Made-up belief C",
    "lots of Made-up group D, first part",
    "mostly Made-up country N1",
    "a high share of Made-up group B",
    "rank by ethnic group",
    "sort by religion",
    "where most people were born abroad",
    "show me the census",
    "an area where my religion is the biggest",
    "leafy, and more than 20% Made-up belief E",
)


@pytest.mark.parametrize("prompt", PROMPTS)
def test_no_sentence_makes_an_edit_from_a_census_figure(client: TestClient, prompt: str):
    found = data(client.post("/v1/interpret", json={"text": prompt}))
    edits = [edit for group in found["operations"].values() for edit in group]
    named = json.dumps([edits, found["suggestions"], found["spec"]]).casefold()
    assert not [kind for kind in NEVER if kind in named]
    assert not holds_a_canary(json.dumps(found))
    # Whatever was read of the rest, the ranking that follows is of places.
    ranked = data(client.post("/v1/rank", json={"spec": found["spec"]}))
    assert not holds_a_canary(json.dumps(ranked))


def test_a_destination_cannot_be_found_by_a_census_label(client: TestClient):
    for text in ("Made-up group A", "Made-up belief", "SYN-GRP", "ethnic group"):
        found = data(client.post("/v1/places/search", json={"q": text}))
        assert found["places"] == []


# --- Only route 13 serves a census figure ----------------------------------------------


def every_other_answer(seen: Seen) -> None:
    """One whole visit: every route but route 13, as a person's search would make them."""
    read = seen.post("/v1/interpret", {"text": "leafy, 40 minutes to Cindermoor Works"})
    spec = read.json()["data"]["spec"]
    seen.post("/v1/rank", {"spec": spec, "limit": 100})
    seen.post("/v1/explanations", {"spec": spec, "limit": 5})
    seen.post("/v1/places/search", {"q": "Cinder"})
    made = seen.post("/v1/shares", {"spec": spec}).json()["data"]["share_id"]
    seen.send("GET", f"/v1/shares/{made}")
    areas = [area.area_id for area in release().neighbourhoods]
    for first in range(0, len(areas), 4):
        seen.post("/v1/compare", {"area_ids": areas[first : first + 4], "spec": spec})
    for path in ("/v1/areas", "/v1/areas/geometry", "/healthz"):
        seen.send("GET", path)
    for area in areas:
        seen.send("GET", f"/v1/areas/{area}")


def test_only_the_census_route_serves_a_census_figure():
    with watching(make_deps()) as seen:
        every_other_answer(seen)
        assert len(seen.responses) > 30
        assert {response.status_code for response in seen.responses} == {200}
        assert not holds_a_canary(seen.everything())
        # Route 11 offers the census in words, and holds no row, no code and no figure of it.
        meta = seen.send("GET", "/v1/meta")
        assert not holds_a_canary(meta.text)

        # The canaries bite: the census route holds them, in its body and nowhere else.
        before = len(seen.responses)
        asked = seen.send("GET", at(AREA))
        assert len(holds_a_canary(asked.text)) > 50
        assert not holds_a_canary(json.dumps(dict(asked.headers)))
        assert len(seen.responses) == before + 1


def test_the_line_for_a_census_names_the_route_and_never_the_area():
    with watching(make_deps()) as seen:
        for path in (at(AREA), at(AREA_ID), at("nowhere"), f"{at(AREA)}?kind=religion"):
            seen.send("GET", path)
        lines = seen.events("request")
        assert [line["route"] for line in lines] == [ROUTE] * 4
        assert [line["status"] for line in lines] == [200, 200, 404, 422]
        written = json.dumps(seen.lines()).casefold()
        records = "\n".join(repr(record.__dict__) for record in seen.records).casefold()
        for never in (AREA, AREA_ID, "nowhere", "religion", "foxholt"):
            assert never not in written and never not in records
        assert not holds_a_canary(written) and not holds_a_canary(records)
        # A line for one area is the line for another, but for its id and how long it took.
        same = [
            {k: v for k, v in line.items() if k not in ("request_id", "latency_ms", "at")}
            for line in lines[:2]
        ]
        assert same[0] == same[1]
        assert not seen.deps.calls.records(seen.deps.clock.now())


def test_no_log_line_has_a_field_for_a_census_figure():
    for name in LOGGABLE:
        assert not [word for word in ("census", "area", "kind", "share", "count") if word in name]


def test_nothing_sent_to_a_model_holds_a_census_figure():
    sent_with_settings = FakeModelClient(model_output())
    reader = reader_asking(sent_with_settings, with_settings=True)
    client = client_for(make_deps(interpreter=reader, model_id=MODEL))
    for prompt in ("leafy and quiet", *PROMPTS[:3]):
        client.post("/v1/interpret", json={"text": prompt, "spec": wire(searching())})
    assert sent_with_settings.calls
    for call in sent_with_settings.calls:
        said = json.dumps(call, default=str).casefold()
        # The person's own words are sent, as ever. Nothing of the census goes with them.
        for prompt in PROMPTS[:3]:
            said = said.replace(json.dumps(prompt)[1:-1].casefold(), "")
        assert not holds_a_canary(said)
        assert "census" not in said and "21 march 2021" not in said


def test_a_stored_share_holds_nothing_of_the_census():
    deps = make_deps()
    client = client_for(deps)
    made = data(client.post("/v1/shares", json={"spec": wire(searching())}))
    stored = deps.shares.get(made["share_id"])
    assert stored is not None
    assert not holds_a_canary(stored.model_dump_json())
    assert "census" not in stored.model_dump_json()
    opened = client.get(f"/v1/shares/{made['share_id']}")
    assert opened.status_code == 200 and not holds_a_canary(opened.text)


# --- Moving the figures between areas changes no other answer ------------------------------


def moved(found: Census) -> Census:
    """The same census with every area's figures handed to the next area."""
    tables = [area.tables for area in found.areas]
    turned = [*tables[1:], tables[0]]
    areas = tuple(
        area.replace(tables=given) for area, given in zip(found.areas, turned, strict=True)
    )
    return found.replace(areas=areas)


def searches() -> list[PreferenceSpec]:
    """Sixty specs that differ: every vibe each way it runs, every feature, and what is usual."""
    found: list[PreferenceSpec] = [renter(), searching()]
    for vibe in release().vibes:
        for toward in Toward:
            asked = TagWeight(
                tag_id=vibe.tag_id, weight=1.0, toward=toward, provenance=Provenance.STATED
            )
            found.append(renter(tags=(asked,)))
    for metric in release().metrics:
        for direction in Direction:
            asked_of = FeatureWeight(
                feature_id=metric.feature_id,
                weight=1.0,
                direction=direction,
                provenance=Provenance.STATED,
            )
            found.append(searching(weights=(asked_of,)))
    # Only what the release can rank: a vibe that runs one way has no other end to ask for.
    sound = [spec for spec in found if not check_spec(spec, release())]
    return sound[:SEARCHES]


def a_sample_of_searches() -> list[PreferenceSpec]:
    """Every fifth search, the same each time: what is usual, vibes and features among them."""
    return searches()[::EVERY]


def answers(deps: Deps, specs: list[PreferenceSpec]) -> list[tuple[str, int, str]]:
    """Every answer of routes 1 to 12 over some searches, as it was sent."""
    client = client_for(deps)
    found: list[tuple[str, int, str]] = []

    def keep(path: str, response: Any) -> Any:
        found.append((path, response.status_code, response.text))
        return response

    areas = [area.area_id for area in release().neighbourhoods]
    for number, spec in enumerate(specs):
        sent = wire(spec)
        keep("/v1/rank", client.post("/v1/rank", json={"spec": sent, "limit": 100}))
        keep("/v1/explanations", client.post("/v1/explanations", json={"spec": sent}))
        compared = [areas[(number + step) % len(areas)] for step in (0, 7, 13)]
        keep("/v1/compare", client.post("/v1/compare", json={"area_ids": compared, "spec": sent}))
        made = keep("/v1/shares", client.post("/v1/shares", json={"spec": sent}))
        keep("/v1/shares/{id}", client.get(f"/v1/shares/{made.json()['data']['share_id']}"))
    for prompt in ("leafy and quiet", "nights out", *PROMPTS):
        keep("/v1/interpret", client.post("/v1/interpret", json={"text": prompt}))
    keep("/v1/places/search", client.post("/v1/places/search", json={"q": "Pell"}))
    for path in ("/v1/areas", "/v1/areas/geometry", "/v1/meta", "/healthz"):
        keep(path, client.get(path))
    for area in areas:
        keep("/v1/areas/{id}", client.get(f"/v1/areas/{area}"))
    return found


Answers = Sequence[tuple[str, int, str]]


@cache
def as_it_is() -> Answers:
    """What the service answers as it is, over the sample of searches.

    It is asked once in each process, for every test that holds another service to what
    it answers. A service that is made the same answers the same, and a test of any two
    that differ fails if it does not.
    """
    return tuple(answers(make_deps(), a_sample_of_searches()))


def differing(first: Answers, second: Answers, searches: int) -> list[str]:
    """The routes that answer otherwise the second time, over the same searches."""
    assert len(first) > 5 * searches and {status for _, status, _ in first} == {200}
    return [path for (path, *one), (_, *two) in zip(first, second, strict=True) if one != two]


def what_differs(specs: list[PreferenceSpec], census_of_the_second: Census | None) -> list[str]:
    """The routes that answer otherwise once the census is changed, over the same searches."""
    first = as_it_is() if specs == a_sample_of_searches() else answers(make_deps(), specs)
    second = answers(make_deps(census=census_of_the_second), specs)
    return differing(first, second, len(specs))


def test_the_figures_that_are_moved_are_not_the_figures_that_were():
    as_it_is, turned = census(), moved(census())
    assert turned != as_it_is
    here = client_for(make_deps(census=turned)).get(at(AREA))
    assert here.status_code == 200 and here.text != client_for(make_deps()).get(at(AREA)).text
    assert len(searches()) == SEARCHES and len(a_sample_of_searches()) == SEARCHES // EVERY


def test_moving_the_census_between_areas_changes_no_other_answer():
    assert what_differs(a_sample_of_searches(), moved(census())) == []


@pytest.mark.full
def test_moving_the_census_between_areas_changes_no_answer_of_sixty_searches():
    assert what_differs(searches(), moved(census())) == []


def test_taking_the_census_away_changes_no_answer_but_the_offer_of_it():
    specs = a_sample_of_searches()
    assert what_differs(specs, None) == ["/v1/meta"]
    with_it = data(client_for(make_deps()).get("/v1/meta"))
    without = data(client_for(make_deps(census=None)).get("/v1/meta"))
    assert with_it.pop("census")["available"] is True
    assert without.pop("census")["available"] is False
    assert with_it == without


# --- The contract --------------------------------------------------------------------------


def references(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        found = cast(dict[str, Any], value)
        if isinstance(found.get("$ref"), str):
            yield found["$ref"].rsplit("/", 1)[-1]
        for inner in found.values():
            yield from references(inner)
    elif isinstance(value, list):
        for inner in cast(list[Any], value):
            yield from references(inner)


def test_no_schema_but_the_census_routes_names_a_census_record():
    document = json.loads(COMMITTED.read_text(encoding="utf-8"))
    schemas = document["components"]["schemas"]
    of_the_census = {name for name in schemas if name.startswith("Census")}
    assert of_the_census == {
        "CensusColumns",
        "CensusKind",
        "CensusLeftOut",
        "CensusOffer",
        "CensusPanel",
        "CensusPanelRow",
        "CensusPanelTable",
    }
    named_by: dict[str, set[str]] = {name: set() for name in of_the_census}
    for name, schema in schemas.items():
        for reference in references(schema):
            if reference in of_the_census:
                named_by[reference].add(name)
    outside = {
        name: sorted(by - of_the_census - {"Envelope_CensusPanel_"})
        for name, by in named_by.items()
    }
    # Route 11 offers the census in words. Nothing else names a record of it.
    assert {name: by for name, by in outside.items() if by} == {"CensusOffer": ["MetaData"]}
    assert set(schemas["CensusOffer"]["properties"]) == {"available", "heading", "intro"}
    # No vocabulary of a search holds a kind of the census.
    for vocabulary in ("FeatureId", "TagId", "FactKind"):
        assert not set(schemas[vocabulary]["enum"]) & set(KINDS), vocabulary
    assert not {each.value for each in FeatureId} & set(KINDS)
    assert not {each.value for each in TagId} & set(KINDS)


def test_a_place_a_search_names_is_never_in_the_address_of_a_census(client: TestClient):
    """The address holds an area of the release, and nothing of a search."""
    assert data(client.get(at(AREA)))["area_id"] == AREA_ID
    assert code(client.get(at(WORKS))) == (404, "area_not_found")
