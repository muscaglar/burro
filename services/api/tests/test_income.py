"""Route 14, the household income of one area, and the tests that try to reach it from a search.

The estimate is shown on an area's page and used for nothing else. So most of
what is held here is what cannot be done: no route ranks on it, none compares
on it, and none explains by it. No search, share, log line or model is handed
a figure of it, and moving the figures from one area to another changes no
other answer.
"""

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from burro_api import loading
from burro_api.app import deps_from
from burro_api.cli import main
from burro_api.deps import Deps
from burro_api.loading import load_income
from burro_api.logs import LOGGABLE
from burro_api.settings import SYNTHETIC_FIXTURE, SYNTHETIC_INCOME, Settings
from burro_api.wire import BODIES
from burro_core.ids import FeatureId, TagId
from burro_core.income import INCOME, MADE_UP, MANIFEST, Income, IncomeError
from burro_core.spec import PreferenceSpec
from fastapi.testclient import TestClient

from .support import client_for, income, make_deps, release, searching, watching, wire
from .test_census import a_sample_of_searches, answers, references, searches

ROUTE = "/v1/areas/{id_or_slug}/income"
AREA = "foxholt"
AREA_ID = "syn-n0007"
# The new town, which the made-up estimates hold no figure for.
NOT_ESTIMATED = "otterby-fields"
COMMITTED = Path(__file__).resolve().parents[3] / "contracts" / "openapi.json"
# The routes that rank, compare and explain, and every other route that answers a search.
RANKS, COMPARES, EXPLAINS = "/v1/rank", "/v1/compare", "/v1/explanations"


def at(area: str) -> str:
    return f"/v1/areas/{area}/income"


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with client_for(make_deps()) as kept:
        yield kept


def data(response: Any) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    return response.json()["data"]


def code(response: Any) -> tuple[int, str]:
    return response.status_code, response.json()["error"]["code"]


def amounts(found: Income | None = None) -> list[int]:
    """Every figure of the estimates: the estimate of each area, and both its limits."""
    found = found or income()
    held = {
        amount
        for area in found.areas
        for amount in (area.estimate, area.lower, area.upper)
        if amount is not None
    }
    return sorted(held)


def holds_a_figure(text: str, found: Income | None = None) -> list[str]:
    """The figures of the estimates that an answer holds, as they are printed or as they are held.

    It is for the body of an answer, which is the same from run to run. A
    made-up estimate is given to the pound, so no price of the made-up
    release, which is given to the 500, is ever one.
    """
    forms = [form for amount in amounts(found) for form in (f"{amount:,}", str(amount))]
    return [
        form
        for form in sorted(set(forms))
        if re.search(rf"(?<![0-9A-Za-z,.\-]){form}(?![0-9A-Za-z,\-])", text)
    ]


def holds_a_printed_figure(text: str, found: Income | None = None) -> list[str]:
    """The figures that a text holds as they are printed: with the comma that groups them.

    It is for a log, a header and a line of a refusal, which hold numbers of
    their own that change from run to run: the id of a process, of a request,
    of a folder. A figure is only ever served as it is printed.
    """
    return [form for amount in amounts(found) if (form := f"{amount:,}") in text]


def names_income(text: str) -> bool:
    return bool(re.search(r"income|earn|salar|wage", text.casefold()))


# --- What the route serves ------------------------------------------------------------


def test_the_income_of_an_area_is_served_by_its_id_and_by_its_slug(client: TestClient):
    by_slug, by_id = client.get(at(AREA)), client.get(at(AREA_ID))
    assert by_slug.json() == by_id.json()
    found = data(by_slug)
    held = income().of(AREA_ID)
    assert held is not None and held.estimate is not None
    assert found["area_id"] == AREA_ID
    assert found["estimate"] == f"£{held.estimate:,}"
    assert (found["lower"], found["upper"]) == (f"£{held.lower:,}", f"£{held.upper:,}")
    assert found["limits"] == f"£{held.lower:,} to £{held.upper:,}"
    assert found["none_given"] is None


def test_it_says_its_source_its_year_and_that_it_is_an_estimate_from_a_model(client: TestClient):
    found = data(client.get(at(AREA)))
    assert found["heading"] == MADE_UP.heading and found["kind"] == MADE_UP.kind
    assert found["year_line"] == "A made-up year ending March 2023: April 2022 to March 2023."
    assert "estimate from a model" in found["modelled"]
    assert found["source_line"].startswith("Source: made up by Burro for testing.")
    assert found["licence_line"] == MADE_UP.licence_line
    assert found["notes"] == list(MADE_UP.notes)
    assert "a mean, and not a median" in found["notes"][0]


def test_nothing_stands_beside_the_figure(client: TestClient):
    """No other area, no figure of the whole city, no rank, no share and no colour."""
    found = data(client.get(at(AREA)))
    assert set(found) == {
        "area_id",
        "heading",
        "kind",
        "definition",
        "estimate",
        "limits_label",
        "lower",
        "upper",
        "limits",
        "none_given",
        "year_line",
        "modelled",
        "notes",
        "source_line",
        "licence_line",
        "source_url",
        "open_source",
    }
    own = holds_a_printed_figure(json.dumps(found))
    held = income().of(AREA_ID)
    assert held is not None
    assert set(own) == {f"{amount:,}" for amount in (held.estimate, held.lower, held.upper)}
    others = [area.name for area in release().neighbourhoods if area.area_id != AREA_ID]
    assert not [name for name in others if name in json.dumps(found)]


def test_every_area_of_the_release_has_an_answer_and_one_says_it_has_no_estimate(
    client: TestClient,
):
    for area in release().neighbourhoods:
        assert client.get(at(area.area_id)).status_code == 200
    none = data(client.get(at(NOT_ESTIMATED)))
    assert (none["estimate"], none["lower"], none["upper"]) == (None, None, None)
    assert none["none_given"] == MADE_UP.none_given and "£" not in json.dumps(none)


def test_an_area_the_release_lacks_is_not_found(client: TestClient):
    assert code(client.get(at("nowhere"))) == (404, "area_not_found")


def test_every_answer_says_that_the_figures_are_made_up(client: TestClient):
    for path in (at(AREA), at("nowhere"), f"{at(AREA)}?x=1"):
        answered = client.get(path)
        assert answered.headers["x-burro-synthetic"] == "true", path
        assert answered.json()["meta"]["synthetic"] is True, path


@pytest.mark.parametrize(
    "query",
    ["sort=estimate", "area=syn-n0001", "areas=syn-n0001,syn-n0002", "compare=syn-n0002", "x"],
)
def test_the_route_takes_nothing(client: TestClient, query: str):
    refused = client.get(f"{at(AREA)}?{query}")
    assert code(refused) == (422, "invalid_request")
    assert not holds_a_figure(refused.text)


def test_the_route_takes_no_body_and_no_other_method(client: TestClient):
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        assert client.request(method, at(AREA), json={"area_ids": ["syn-n0001"]}).status_code == 405


def test_no_route_serves_the_income_of_more_than_one_area(client: TestClient):
    for path in ("/v1/income", "/v1/areas/income", "/v1/areas/syn-n0001,syn-n0002/income"):
        assert client.get(path).status_code == 404, path
    document = json.loads(COMMITTED.read_text(encoding="utf-8"))
    assert [path for path in document["paths"] if "income" in path] == [ROUTE]
    assert set(document["paths"][ROUTE]) == {"get"}


def test_the_route_may_not_be_kept_or_indexed(client: TestClient):
    answered = client.get(at(AREA), headers={"if-none-match": '"syn-2026-09-23-01"'})
    assert answered.status_code == 200
    assert answered.headers["cache-control"] == "no-store"
    assert answered.headers["x-robots-tag"] == "noindex, nosnippet"
    assert "etag" not in answered.headers


# --- It can be switched off ------------------------------------------------------------


def test_the_route_can_be_switched_off():
    off = client_for(make_deps(income=None))
    assert code(off.get(at(AREA))) == (404, "income_not_available")
    assert code(off.get(at("nowhere"))) == (404, "area_not_found")
    assert data(off.get("/v1/meta"))["income"] == {"available": False, "heading": "", "intro": ""}


def test_the_block_that_offers_it_holds_no_figure_and_names_no_area(client: TestClient):
    offered = data(client.get("/v1/meta"))["income"]
    assert offered["available"] is True and offered["heading"] == MADE_UP.heading
    assert not re.search(r"[0-9£%]", json.dumps(offered))
    assert not [area.name for area in release().neighbourhoods if area.name in offered["intro"]]


def test_one_word_in_the_environment_serves_none():
    assert Settings.from_env({}).income_dir == SYNTHETIC_INCOME
    for word in ("off", "OFF", " off "):
        settings = Settings.from_env({"BURRO_INCOME": word})
        assert settings.income_dir is None
        assert deps_from(settings).income is None
    assert deps_from(Settings.from_env({})).income == income()


def test_the_income_of_a_release_is_looked_for_beside_it(tmp_path: Path):
    folder = tmp_path / SYNTHETIC_FIXTURE.name
    settings = Settings.from_env({"BURRO_RELEASE_DIR": str(folder)})
    assert settings.income_dir == tmp_path.resolve() / SYNTHETIC_INCOME.name
    # A folder that is not there is none, and the service starts without it.
    assert load_income(settings.income_dir, release()) is None


def test_a_folder_that_was_named_and_is_not_there_stops_the_service(tmp_path: Path):
    settings = Settings.from_env({"BURRO_INCOME_DIR": str(tmp_path / "nowhere")})
    with pytest.raises(IncomeError) as caught:
        deps_from(settings)
    assert caught.value.rule == loading.FOLDER_IS_READABLE


def copied(tmp_path: Path) -> Path:
    folder = tmp_path / SYNTHETIC_INCOME.name
    folder.mkdir()
    for file in SYNTHETIC_INCOME.iterdir():
        (folder / file.name).write_bytes(file.read_bytes())
    return folder


def test_figures_that_break_a_rule_stop_the_service_in_one_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    folder = copied(tmp_path)
    (folder / INCOME).write_bytes((folder / INCOME).read_bytes() + b" ")
    monkeypatch.setenv("BURRO_INCOME_DIR", str(folder))
    assert main(["serve"]) == 2
    err = capsys.readouterr().err.strip().splitlines()[-1]
    assert err == (
        f"error: the household income could not be loaded: {folder}: {INCOME} "
        "[files_match_manifest]"
    )
    assert not holds_a_printed_figure(err)


def test_the_folder_is_read_whatever_the_finder_left_beside_it(tmp_path: Path):
    folder = copied(tmp_path)
    (folder / loading.IGNORED).write_bytes(b"\x00")
    assert load_income(folder, release()) == income()
    (folder / "notes.txt").write_bytes(b"mine")
    with pytest.raises(IncomeError) as caught:
        load_income(folder, release())
    assert (caught.value.file, caught.value.rule) == ("notes.txt", "files_match_manifest")
    assert sorted(file.name for file in SYNTHETIC_INCOME.iterdir()) == [INCOME, MANIFEST]


def test_a_service_cannot_be_made_with_the_income_of_another_release():
    other = income().replace(release_id="syn-2026-09-23-02")
    with pytest.raises(ValueError, match="made for another release"):
        make_deps(income=other)


# --- No route ranks on it, compares on it, or explains by it ---------------------------------


def moved(found: Income) -> Income:
    """The same estimates with every area's figures handed to the next area."""
    held = [(area.estimate, area.lower, area.upper) for area in found.areas]
    turned = [*held[1:], held[0]]
    areas = tuple(
        area.replace(estimate=estimate, lower=lower, upper=upper)
        for area, (estimate, lower, upper) in zip(found.areas, turned, strict=True)
    )
    return found.replace(areas=areas)


def what_differs(specs: list[PreferenceSpec], of_the_second: Income | None) -> list[str]:
    """The routes that answer otherwise once the estimates are changed, over the same searches."""
    first = answers(make_deps(), specs)
    second = answers(make_deps(income=of_the_second), specs)
    assert len(first) > 5 * len(specs) and {status for _, status, _ in first} == {200}
    return [path for (path, *one), (_, *two) in zip(first, second, strict=True) if one != two]


def answers_of(route: str, deps: Deps | None = None) -> list[str]:
    """Every answer one route gave over a sample of searches, as it was sent."""
    found = answers(deps or make_deps(), a_sample_of_searches())
    return [text for path, status, text in found if path == route and status == 200]


def test_the_figures_that_are_moved_are_not_the_figures_that_were():
    as_it_is, turned = income(), moved(income())
    assert turned != as_it_is
    here = client_for(make_deps(income=turned)).get(at(AREA))
    assert here.status_code == 200 and here.text != client_for(make_deps()).get(at(AREA)).text


@pytest.mark.parametrize("route", [RANKS, COMPARES, EXPLAINS])
def test_the_route_answers_the_same_whatever_the_income_of_an_area_is(route: str):
    """No route ranks on it, compares on it, or explains by it: each is held by itself.

    The estimates are moved from each area to the next, and then taken away.
    An answer that rested on one would change. None does.
    """
    as_it_is = answers_of(route)
    assert len(as_it_is) == len(a_sample_of_searches())
    assert answers_of(route, make_deps(income=moved(income()))) == as_it_is
    assert answers_of(route, make_deps(income=None)) == as_it_is


@pytest.mark.parametrize("route", [RANKS, COMPARES, EXPLAINS])
def test_no_answer_of_the_route_holds_a_figure_of_income_or_a_word_for_it(route: str):
    for text in answers_of(route):
        assert not holds_a_figure(text), route
        assert not names_income(text), route


def test_moving_the_income_between_areas_changes_no_other_answer():
    assert what_differs(a_sample_of_searches(), moved(income())) == []


@pytest.mark.full
def test_moving_the_income_between_areas_changes_no_answer_of_sixty_searches():
    assert what_differs(searches(), moved(income())) == []


def test_taking_the_income_away_changes_no_answer_but_the_offer_of_it():
    assert what_differs(a_sample_of_searches(), None) == ["/v1/meta"]
    with_it = data(client_for(make_deps()).get("/v1/meta"))
    without = data(client_for(make_deps(income=None)).get("/v1/meta"))
    assert with_it.pop("income")["available"] is True
    assert without.pop("income")["available"] is False
    assert with_it == without


def test_only_its_own_route_serves_a_figure_of_income():
    with watching(make_deps()) as seen:
        spec = wire(searching())
        seen.post("/v1/rank", {"spec": spec, "limit": 100})
        seen.post("/v1/explanations", {"spec": spec})
        made = seen.post("/v1/shares", {"spec": spec}).json()["data"]["share_id"]
        seen.send("GET", f"/v1/shares/{made}")
        areas = [area.area_id for area in release().neighbourhoods]
        for first in range(0, len(areas), 4):
            seen.post("/v1/compare", {"area_ids": areas[first : first + 4], "spec": spec})
        for path in ("/v1/areas", "/v1/areas/geometry", "/healthz"):
            seen.send("GET", path)
        for area in areas:
            seen.send("GET", f"/v1/areas/{area}")
            seen.send("GET", f"/v1/areas/{area}/census")
        assert len(seen.responses) > 50
        assert {response.status_code for response in seen.responses} == {200}
        for answer in seen.responses:
            assert not holds_a_figure(answer.text), answer.url.path
        # A log holds numbers of its own, so it is searched for a figure as one is printed.
        assert not holds_a_printed_figure(seen.everything())
        assert not [r.url.path for r in seen.responses if names_income(r.text)]
        # Route 11 offers it in words, and holds no figure of it.
        assert not holds_a_figure(seen.send("GET", "/v1/meta").text)

        # The figures bite: its own route holds them, in its body and nowhere else.
        asked = seen.send("GET", at(AREA))
        assert len(holds_a_printed_figure(asked.text)) == 3
        assert not holds_a_printed_figure(json.dumps(dict(asked.headers)))


NAMES = ["income", "household_income", "earnings", "total_annual_household_income", "salary"]


def spec_with(**changes: Any) -> dict[str, Any]:
    return wire(searching()) | changes


def specs_that_ask(name: str) -> list[dict[str, Any]]:
    """Every way a spec could be written to ask for the income of an area."""
    spec = wire(searching())
    weight = {"feature_id": name, "weight": 1.0, "direction": "more", "provenance": "stated"}
    tag = {"tag_id": name, "weight": 1.0, "toward": "high", "provenance": "stated"}
    return [
        spec_with(weights=[*spec["weights"], weight]),
        spec_with(tags=[*spec["tags"], tag]),
        spec_with(**{name: 1.0}),
        spec_with(income={"at_least": 50_000}),
        spec_with(filters=[{"kind": name, "at_least": 50_000}]),
        spec_with(budget={"amount": 1_500, "segment": name, "strictness": "hard", "weight": 1}),
    ]


def refused(response: Any) -> bool:
    """Refused for what was sent, by a code of the contract, and with no figure of income."""
    return (
        response.status_code == 422
        and response.json()["error"]["code"]
        in {"invalid_spec", "invalid_operations", "invalid_request", "invalid_compare"}
        and not holds_a_figure(response.text)
    )


@pytest.mark.parametrize("name", NAMES)
def test_no_search_no_comparison_and_no_explanation_can_ask_for_it(client: TestClient, name: str):
    areas = {"area_ids": ["syn-n0001", "syn-n0002"]}
    for spec in specs_that_ask(name):
        assert refused(client.post(RANKS, json={"spec": spec})), name
        assert refused(client.post(COMPARES, json=areas | {"spec": spec})), name
        assert refused(client.post(EXPLAINS, json={"spec": spec})), name
        assert refused(client.post("/v1/shares", json={"spec": spec})), name
    for extra in ({"income": True}, {"sort": name}, {"rows": [name]}, {name: True}):
        sent = {"spec": wire(searching())} | extra
        assert refused(client.post(RANKS, json=sent)), name
        assert refused(client.post(COMPARES, json=areas | sent)), name
        assert refused(client.post(EXPLAINS, json=sent)), name


def test_no_body_the_service_takes_has_a_field_for_it():
    for body in BODIES:
        schema = json.dumps(body.model_json_schema()).casefold()
        for word in ("income", "earn", "salary", "wage"):
            assert word not in schema, (body.__name__, word)


@pytest.mark.parametrize(
    "prompt",
    [
        "high income area",
        "rank by household income",
        "sort by income",
        "where people earn the most",
        "leafy, and household income over 60000",
        "an area with good salaries",
    ],
)
def test_no_sentence_makes_an_edit_or_an_offer_from_it(client: TestClient, prompt: str):
    found = data(client.post("/v1/interpret", json={"text": prompt, "spec": wire(searching())}))
    edits = found["operations"]
    assert not edits["weight_ops"] or all(
        edit["feature_id"] in {each.value for each in FeatureId} for edit in edits["weight_ops"]
    )
    offered = [offer["target"] for offer in found["suggestions"]]
    assert not [target for target in offered if names_income(target)]
    assert not holds_a_figure(json.dumps(found))


# --- The log ---------------------------------------------------------------------------------


def test_the_line_for_it_names_the_route_and_never_the_area_or_a_figure():
    with watching(make_deps()) as seen:
        for path in (at(AREA), at(AREA_ID), at("nowhere"), f"{at(AREA)}?sort=estimate"):
            seen.send("GET", path)
        lines = seen.events("request")
        assert [line["route"] for line in lines] == [ROUTE] * 4
        assert [line["status"] for line in lines] == [200, 200, 404, 422]
        written = json.dumps(seen.lines()).casefold()
        records = "\n".join(repr(record.__dict__) for record in seen.records).casefold()
        for never in (AREA, AREA_ID, "nowhere", "estimate"):
            assert never not in written and never not in records
        assert not holds_a_printed_figure(written) and not holds_a_printed_figure(records)
        assert not seen.deps.calls.records(seen.deps.clock.now())


def test_no_log_line_has_a_field_for_it():
    for name in LOGGABLE:
        assert not [word for word in ("income", "estimate", "pounds") if word in name]


# --- The contract --------------------------------------------------------------------------


def test_no_schema_but_its_own_route_names_a_record_of_income():
    document = json.loads(COMMITTED.read_text(encoding="utf-8"))
    schemas = document["components"]["schemas"]
    of_income = {name for name in schemas if "Income" in name}
    assert of_income == {"IncomeOffer", "IncomeShown", "Envelope_IncomeShown_"}
    named_by: dict[str, set[str]] = {name: set() for name in of_income}
    for name, schema in schemas.items():
        for reference in references(schema):
            if reference in of_income:
                named_by[reference].add(name)
    outside = {name: sorted(by - of_income) for name, by in named_by.items()}
    # Route 11 offers it in words. Nothing else names a record of it.
    assert {name: by for name, by in outside.items() if by} == {"IncomeOffer": ["MetaData"]}
    assert set(schemas["IncomeOffer"]["properties"]) == {"available", "heading", "intro"}
    # What routes 2, 3 and 9 answer with names no record of it, however deep.
    for answer in ("RankData", "CompareData", "ExplanationsData"):
        found = [name for name in schemas if name.startswith(answer.removesuffix("Data"))]
        assert found, answer
    reached: set[str] = set()
    waiting = [name for name in schemas if re.match(r"^(Rank|Compare|Explan|Interpret)", name)]
    while waiting:
        name = waiting.pop()
        if name in reached or name not in schemas:
            continue
        reached.add(name)
        waiting += list(references(schemas[name]))
    assert reached and not reached & of_income
    # No vocabulary of a search holds a name for it.
    for vocabulary in ("FeatureId", "TagId", "FactKind", "Segment"):
        assert not [each for each in schemas[vocabulary]["enum"] if names_income(each)]
    assert not [each for each in (*FeatureId, *TagId) if names_income(each.value)]
