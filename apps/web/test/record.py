"""Records answers from the real app, for the website to be built and tested against.

Run it from the repository root:

    make web-record

which is `uv run python apps/web/test/record.py`.

It builds the app as the service does, on the committed synthetic release, and
drives it through the framework's test client, so no port is bound and nothing
leaves the machine. The clock and the ids are fixed, so a second run writes the
same bytes. Every file in `recorded/` is written by this script and never
edited by hand: to change one, change a scenario below and run it again.

Each scenario is there to show one thing, and `PROVES` holds what that is as a
test of its answer. The reader of sentences changes, and a sentence that was a
question yesterday may be read in full today. When a scenario stops showing
what it is there to show, nothing is written and the run says which: reword
its sentence until it shows it again.

Every prompt here is made up for the recording. None is anything a person typed.
"""

import base64
import io
import json
import random
import re
import sys
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from burro_api import logs
from burro_api.app import create_app
from burro_api.calls import InMemoryCallLog
from burro_api.claude import ClaudeInterpreter, ModelReply, ModelTimeout
from burro_api.deps import Deps
from burro_api.loading import load_release
from burro_api.settings import SYNTHETIC_FIXTURE
from burro_api.stores import InMemoryShareStore
from burro_core import RuleInterpreter, TemplateExplainer
from burro_core.ids import InterpreterName
from fastapi.testclient import TestClient

OUT = Path(__file__).resolve().parent / "recorded"
NOW = datetime(2026, 9, 23, 12, 0, 0, tzinfo=UTC)
SEED = 20260923
# The web app as it runs on a developer's machine, which is the one origin the
# service allows when nothing is set. A browser sends it with every call.
ORIGIN = "http://localhost:3000"

# The route each operation of the contract is served at.
ROUTES = {
    "healthz": ("GET", "/healthz"),
    "get_meta": ("GET", "/v1/meta"),
    "list_areas": ("GET", "/v1/areas"),
    "get_geometry": ("GET", "/v1/areas/geometry"),
    "get_area": ("GET", "/v1/areas/{id_or_slug}"),
    "interpret": ("POST", "/v1/interpret"),
    "rank": ("POST", "/v1/rank"),
    "explain_top": ("POST", "/v1/explanations"),
    "compare": ("POST", "/v1/compare"),
    "search_places": ("POST", "/v1/places/search"),
    "create_share": ("POST", "/v1/shares"),
    "get_share": ("GET", "/v1/shares/{share_id}"),
}
# A path that is no route. The contract names no operation for it.
NO_ROUTE = "/v1/nothing-here"

WORKS = "syn-p0021"  # Cindermoor Works
SCHOOL = "syn-p0031"  # Alderwick Primary School, which a share coarsens to a station
GONE_PLACE = "syn-p9999"  # A place no release has, as a spec kept from an older one names


class FixedClock:
    """Says the same time, and moves on a millisecond each time it is asked how long."""

    def __init__(self) -> None:
        self._elapsed = 0.0

    def now(self) -> datetime:
        return NOW

    def elapsed(self) -> float:
        self._elapsed += 0.001
        return self._elapsed


class SeededIds:
    """Ids shaped as the service makes them, drawn from a fixed seed."""

    def __init__(self, seed: int) -> None:
        # Not for secrecy: a recording must come out the same every time.
        self._random = random.Random(seed)  # noqa: S311

    def _uuid(self) -> str:
        return str(uuid.UUID(int=self._random.getrandbits(128), version=4))

    def request_id(self) -> str:
        return self._uuid()

    def call_id(self) -> str:
        return self._uuid()

    def share_id(self) -> str:
        raw = self._random.getrandbits(128).to_bytes(16, "big")
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


class ModelThatTimesOut:
    """Stands in for a model that does not answer, so that the rules answer in its place."""

    name = InterpreterName.CLAUDE

    def interpret(self, request: object) -> Any:
        raise ModelTimeout


class ModelThatAnswers:
    """Stands in for a model that answers, so that what a model read can be recorded."""

    def __init__(self, answer: dict[str, Any]) -> None:
        self._answer = json.dumps(answer)

    def complete(self, **sent: Any) -> ModelReply:
        return ModelReply(
            output=self._answer, input_tokens=812, output_tokens=96, cache_read_tokens=640
        )


class ExplainerThatBreaks:
    """Stands in for a fault in the service, which is answered with a 500."""

    def draft(self, area: object) -> Any:
        raise RuntimeError


def make_deps(**changes: Any) -> Deps:
    deps = Deps(
        release=load_release(SYNTHETIC_FIXTURE),
        interpreter=RuleInterpreter(),
        explainer=TemplateExplainer(),
        shares=InMemoryShareStore(),
        calls=InMemoryCallLog(),
        clock=FixedClock(),
        ids=SeededIds(SEED),
        allowed_origins=(ORIGIN,),
    )
    return replace(deps, **changes)


def _data(body: Any) -> dict[str, Any]:
    return body.get("data") or {}


def _changed(body: Any) -> int:
    """How many edits of an answer changed the spec."""
    return sum(1 for one in _data(body).get("applied", []) if one["changed"])


def _asks(body: Any, *, options: bool) -> bool:
    """True when the answer holds one question, with options to pick from or with none."""
    asked = _data(body).get("clarify", [])
    return len(asked) == 1 and bool(asked[0]["options"]) == options


def _off(body: Any, feature_id: str) -> bool:
    """True when the spec of the answer holds the feature at 0: taken off, and the entry kept."""
    weights = _data(body)["spec"]["weights"]
    return any(one["feature_id"] == feature_id and one["weight"] == 0 for one in weights)


def _legs(body: Any, status: str) -> int:
    ranked = _data(body).get("ranked", [])
    return sum(1 for area in ranked for leg in area["legs"] if leg["status"] == status)


# What each scenario must show to be worth recording. A step of the visit is named without
# its number. A scenario that is not here is recorded whatever it shows.
PROVES: dict[str, Callable[[Any], bool]] = {
    "interpret-first": lambda b: _changed(b) == 4 and not _data(b)["rejected"],
    "interpret-two-journeys": lambda b: len(_data(b)["spec"]["commutes"]) == 2,
    "interpret-by-the-river": lambda b: (
        [c["mode"] for c in _data(b)["spec"]["commutes"]] == ["cycle"]
    ),
    "interpret-buyer-family": lambda b: _data(b)["spec"]["tenure"] == "buy",
    "interpret-second-sentence": lambda b: _changed(b) == 2 and _off(b, "highstreet_access"),
    "interpret-clarify": lambda b: _asks(b, options=True) and _changed(b) > 0,
    "interpret-clarify-no-options": lambda b: _asks(b, options=False) and _changed(b) > 0,
    "interpret-notice": lambda b: _data(b)["notice"] == "neutral_places" and _changed(b) > 0,
    "interpret-nothing-read": lambda b: _changed(b) == 0 and _data(b)["unmet"] == ["other"],
    "interpret-rejected": lambda b: bool(_data(b)["rejected"]) and _changed(b) > 0,
    "interpret-unmet": lambda b: len(_data(b)["unmet"]) >= 3 and _changed(b) > 0,
    "interpret-degraded": lambda b: _data(b)["degraded"] is True and _changed(b) > 0,
    "interpret-by-model": lambda b: _data(b)["interpreter"] == "claude" and _changed(b) == 2,
    "interpret-off-topic": lambda b: (
        _data(b)["status"] == "off_topic" and _data(b)["notice_text"] != ""
    ),
    "rank-first": lambda b: len(_data(b)["ranked"]) == 20 and not _data(b)["filtered"],
    "rank-refined": lambda b: bool(_data(b)["ranked"]) and bool(_data(b)["filtered"]),
    "rank-rejected-edit": lambda b: bool(_data(b)["rejected"]),
    "rank-switched-off": lambda b: _off(b, "station_walk"),
    "rank-on-foot": lambda b: _legs(b, "beyond_cutoff") > 0 and _legs(b, "ok") > 0,
    "rank-empty-spec": lambda b: _data(b)["empty_spec"] is True,
    "rank-nothing-matches": lambda b: not _data(b)["ranked"] and bool(_data(b)["filtered"]),
    "rank-two-journeys": lambda b: any(area["untested_filters"] for area in _data(b)["ranked"]),
    "compare-three": lambda b: len({area["status"] for area in _data(b)["areas"]}) > 1,
    "share-made": lambda b: _data(b)["coarsened"] is True,
    "share-made-exact": lambda b: _data(b)["coarsened"] is False,
    "share-opened-stale": lambda b: _data(b)["stale"] is True,
    "visit/first": lambda b: _changed(b) == 4,
    "visit/second": lambda b: _changed(b) == 2 and _off(b, "highstreet_access"),
    "visit/firm-rank": lambda b: bool(_data(b)["filtered"]) and bool(_data(b)["ranked"]),
    "visit/place": lambda b: _asks(b, options=True) and _changed(b) == 0,
    "visit/answered-rank": lambda b: len(_data(b)["spec"]["commutes"]) == 2,
    "visit/people": lambda b: _data(b)["notice"] == "neutral_places" and _changed(b) > 0,
    "visit/unread": lambda b: _changed(b) == 0 and not _data(b)["clarify"],
    "visit/slow": lambda b: _data(b)["degraded"] is True and _changed(b) > 0,
}


@dataclass
class Recorder:
    """Sends a request to an app and keeps what came back, one file for each scenario.

    Nothing is written until every scenario has been recorded and each shows what it is
    there to show. A run that fails leaves the recordings as they were.
    """

    written: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    held: dict[Path, str] = field(default_factory=dict[Path, str])
    failed: list[str] = field(default_factory=list[str])

    def call(
        self,
        client: TestClient,
        scenario: str,
        shows: str,
        operation_id: str | None,
        body: Any = None,
        **path: str,
    ) -> Any:
        method, route = ROUTES[operation_id] if operation_id else ("GET", NO_ROUTE)
        sent_to = route.format(**path)
        headers = {"Origin": ORIGIN}
        if method == "POST":
            response = client.post(sent_to, json=body, headers=headers)
        else:
            response = client.get(sent_to, headers=headers)
        request: dict[str, Any] = {
            "operation_id": operation_id,
            "method": method,
            "route": route,
            "path": sent_to,
        }
        if method == "POST":
            request["body"] = body
        record = {
            "scenario": scenario,
            "shows": shows,
            "captured": True,
            "request": request,
            "status": response.status_code,
            "headers": {name.lower(): value for name, value in sorted(response.headers.items())},
            "body": response.json(),
        }
        proves = PROVES.get(re.sub(r"^visit/\d+-", "visit/", scenario))
        if response.status_code >= 500 and scenario != "error-internal":
            self.failed.append(f"{scenario}: the service failed")
        elif proves is not None and not proves(record["body"]):
            self.failed.append(f"{scenario}: it no longer shows what it is for. {shows}")
        self.held[OUT / f"{scenario}.json"] = (
            json.dumps(record, indent=2, ensure_ascii=False) + "\n"
        )
        self.written.append(
            {
                "scenario": scenario,
                "operation_id": operation_id,
                "status": response.status_code,
                "shows": shows,
            }
        )
        return record["body"]

    def finish(self) -> bool:
        """Write every recording and the index, and take away what no scenario made this time.

        Nothing is written, and False is returned, if any scenario failed to show what it is for.
        """
        if self.failed:
            return False
        index = sorted(self.written, key=lambda entry: entry["scenario"])
        self.held[OUT / "index.json"] = (
            json.dumps({"scenarios": index}, indent=2, ensure_ascii=False) + "\n"
        )
        for target, text in self.held.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        for found in sorted(OUT.rglob("*.json")):
            if found not in self.held:
                found.unlink()
        return True


def operations(**groups: list[dict[str, Any]]) -> dict[str, Any]:
    """The six arrays of an edit, empty unless one is given."""
    empty: dict[str, Any] = {
        "budget_ops": [],
        "commute_ops": [],
        "weight_ops": [],
        "tag_ops": [],
        "area_ops": [],
        "setting_ops": [],
    }
    return empty | groups


def budget_edit(**changes: Any) -> dict[str, Any]:
    edit: dict[str, Any] = {
        "action": "set",
        "tenure": "unchanged",
        "amount": 0,
        "segment": "unchanged",
        "strictness": "unchanged",
        "step": "none",
        "provenance": "ui_edit",
    }
    return edit | changes


def commute_edit(place_id: str, **changes: Any) -> dict[str, Any]:
    edit: dict[str, Any] = {
        "action": "update",
        "place_id": place_id,
        "mode": "unchanged",
        "max_minutes": 0,
        "strictness": "unchanged",
        "step": "none",
        "provenance": "ui_edit",
    }
    return edit | changes


def weight_edit(feature_id: str, **changes: Any) -> dict[str, Any]:
    edit: dict[str, Any] = {
        "action": "set",
        "feature_id": feature_id,
        "value": 0.0,
        "step": "none",
        "direction": "default",
        "provenance": "ui_edit",
    }
    return edit | changes


def model_output(**changes: Any) -> dict[str, Any]:
    """What a model answers in: the six arrays, and what it could not read."""
    empty: dict[str, Any] = {
        "status": "ok",
        "budget_ops": [],
        "commute_ops": [],
        "weight_ops": [],
        "tag_ops": [],
        "area_ops": [],
        "setting_ops": [],
        "policy_flags": [],
        "unmet": [],
    }
    return empty | changes


def read_by(answer: dict[str, Any]) -> TestClient:
    """The service with a model behind it that gives this answer."""
    interpreter = ClaudeInterpreter(
        ModelThatAnswers(answer), model="a-model", max_tokens=2048, timeout_s=6.0
    )
    return TestClient(create_app(make_deps(interpreter=interpreter, model_id="a-model")))


def commute(place_id: str, minutes: int = 40, strictness: str = "soft") -> dict[str, Any]:
    return {
        "place_id": place_id,
        "mode": "pt",
        "max_minutes": minutes,
        "strictness": strictness,
        "provenance": "stated",
    }


# What a person says next. It takes a usual setting off, which leaves an entry of 0 in the spec.
SECOND_SENTENCE = "a bit more green space, and ignore the high street"

# Prompts that should disagree, each with a place from the release. The first
# is the search every other recording of a ranking follows on from.
PROMPTS = {
    "first": (
        "Renting a 1 bed up to £1,700 a month, leafy and quiet, 35 minutes to Cindermoor Works",
        "A first sentence, read in full: a budget, two tags and a journey",
    ),
    "nights-out": (
        "Somewhere buzzy with bars and restaurants, I work at Pellam Exchange",
        "A sentence about venues, with a workplace and no budget",
    ),
    "buyer-family": (
        "Buying a terraced house up to £450k, good primary schools and a park for the kids, "
        "40 minutes to Dulcimer Green Hospital",
        "A buyer, so the tenure changes and the buyer's defaults come in",
    ),
    "two-journeys": (
        "Renting a studio, no more than £1,100 a month, 30 minutes to Wexmoor University "
        "and at most 25 minutes to Foxholt Market",
        "A firm budget and two journeys, one of them firm",
    ),
    "by-the-river": (
        "Historic and by the river, cycle 20 minutes to Tallowgate Guild Quarter",
        "Two tags and a journey by bike",
    ),
}


def record_the_release(rec: Recorder, client: TestClient) -> dict[str, Any]:
    """Routes 4, 5, 6, 11 and 12: what a page is built from."""
    rec.call(client, "healthz", "The service is up. The one answer with no meta", "healthz")
    meta = rec.call(
        client, "meta", "Everything a form needs, and every source and method", "get_meta"
    )
    areas = rec.call(client, "areas", "Every area of the release, by id", "list_areas")
    rec.call(client, "geometry", "The boundary of every area, as GeoJSON", "get_geometry")
    for area in areas["data"]["areas"]:
        rec.call(
            client,
            f"area/{area['slug']}",
            f"The profile of {area['name']}, asked for by its slug",
            "get_area",
            id_or_slug=area["slug"],
        )
    rec.call(
        client,
        "area",
        "One area's profile: features, tags, cost, stations, neighbours and facts",
        "get_area",
        id_or_slug="alderwick",
    )
    rec.call(
        client,
        "area-by-id",
        "The same profile, asked for by its id",
        "get_area",
        id_or_slug="syn-n0001",
    )
    rec.call(
        client,
        "area-not-rankable",
        "An area the release does not rank",
        "get_area",
        id_or_slug="grapnel-dock",
    )
    rec.call(
        client,
        "area-not-found",
        "A slug the release lacks: 404",
        "get_area",
        id_or_slug="nowhere-at-all",
    )
    return meta["data"]


def record_the_readings(rec: Recorder, client: TestClient) -> dict[str, dict[str, Any]]:
    """Route 1: what is read from a sentence, in every state the search page has."""
    specs: dict[str, dict[str, Any]] = {}
    for name, (text, shows) in PROMPTS.items():
        read = rec.call(client, f"interpret-{name}", shows, "interpret", {"text": text})
        specs[name] = read["data"]["spec"]

    second = rec.call(
        client,
        "interpret-second-sentence",
        "A second sentence, sent with the spec the first one left: one thing more, one taken off",
        "interpret",
        {"text": SECOND_SENTENCE, "spec": specs["first"]},
    )
    specs["second-sentence"] = second["data"]["spec"]
    rec.call(
        client,
        "interpret-clarify",
        "A name that matches several places: a question with options, and the rest applied",
        "interpret",
        {"text": "Leafy, renting, 30 minutes to Pellam"},
    )
    rec.call(
        client,
        "interpret-clarify-no-options",
        "A name that matches nothing: a question with no options, so a search box",
        "interpret",
        {"text": "Quiet, and I work in Quillfeather"},
    )
    rec.call(
        client,
        "interpret-notice",
        "Part of the request is about who lives somewhere: the neutral notice, and the rest",
        "interpret",
        {"text": "Quiet and leafy, not too many students, 30 minutes to Cindermoor Works"},
    )
    rec.call(
        client,
        "interpret-nothing-read",
        "Nothing in the sentence could be read: no edit, and other in unmet",
        "interpret",
        {"text": "What is the best way to learn the piano"},
    )
    rec.call(
        client,
        "interpret-rejected",
        "A loose wish for safety: the edit to recorded crime is rejected, the park is applied",
        "interpret",
        {"text": "Somewhere safe, near a park"},
    )
    rec.call(
        client,
        "interpret-unmet",
        "Things the data cannot answer: each is named in unmet, and the rest is applied",
        "interpret",
        {"text": "Leafy. Near a mosque, with fast broadband and low flood risk"},
    )
    rec.call(
        client,
        "interpret-invalid-text",
        "A line of spaces: 422 on the text",
        "interpret",
        {"text": "   "},
    )
    return specs


def record_the_rankings(
    rec: Recorder, client: TestClient, specs: dict[str, dict[str, Any]], defaults: dict[str, Any]
) -> dict[str, Any]:
    """Routes 2 and 3: a ranking, a refinement, and every way a ranking can come back empty."""
    shown = {
        "first": "The first twenty areas",
        "second-sentence": "The search after a second sentence, with a usual setting taken off",
    }
    for name, spec in specs.items():
        shows = shown.get(name, "Another search, ranked")
        rec.call(client, f"rank-{name}", shows, "rank", {"spec": spec, "limit": 20})
        rec.call(
            client,
            f"explanations-{name}",
            "Reasons and a trade-off for the first five, with every fact they cite",
            "explain_top",
            {"spec": spec, "limit": 5},
        )

    first = specs["first"]
    refined = rec.call(
        client,
        "rank-refined",
        "One control moved: the journey made firm and five minutes shorter",
        "rank",
        {
            "spec": first,
            "operations": operations(
                commute_ops=[commute_edit(WORKS, max_minutes=30, strictness="hard")]
            ),
            "limit": 20,
        },
    )
    rec.call(
        client,
        "explanations-refined",
        "The reasons after the refinement",
        "explain_top",
        {"spec": refined["data"]["spec"], "limit": 5},
    )
    rec.call(
        client,
        "rank-rejected-edit",
        "An edit the reducer refuses: a budget of one pound. The spec comes back as it was",
        "rank",
        {"spec": first, "operations": operations(budget_ops=[budget_edit(amount=1)])},
    )
    rec.call(
        client,
        "rank-crime-switched-on",
        "Recorded crime weighted by a control, which a loose word may not do",
        "rank",
        {
            "spec": first,
            "operations": operations(
                weight_ops=[weight_edit("crime_burglary_theft", action="nudge", step="up_large")]
            ),
        },
    )
    rec.call(
        client,
        "rank-default-rent",
        "A renter's defaults, ranked as they stand, as a comparison with no search uses them",
        "rank",
        {"spec": defaults["rent"]},
    )
    rec.call(
        client,
        "rank-empty-spec",
        "Nothing asked for: every area scores 0 and the order is by id",
        "rank",
        {"spec": defaults["rent"] | {"weights": []}},
    )
    nothing = first | {
        "budget": first["budget"] | {"amount": 400, "strictness": "hard"},
        "commutes": [commute(WORKS, minutes=10, strictness="hard")],
    }
    rec.call(
        client,
        "rank-nothing-matches",
        "Firm limits that no area passes: nothing ranked, and a reason for each area",
        "rank",
        {"spec": nothing},
    )
    stale = first | {"commutes": [commute(WORKS), commute(GONE_PLACE)]}
    rec.call(
        client,
        "rank-stale-spec",
        "A spec that names a place the release no longer has: 422, with the path",
        "rank",
        {"spec": stale},
    )
    rec.call(
        client,
        "rank-stale-spec-repaired",
        "The same spec, sent with the edit that takes the place out",
        "rank",
        {
            "spec": stale,
            "operations": operations(commute_ops=[commute_edit(GONE_PLACE, action="remove")]),
        },
    )
    rec.call(
        client,
        "rank-switched-off",
        "A usual setting switched off by a control: its entry stays in the spec, at 0",
        "rank",
        {
            "spec": first,
            "operations": operations(weight_ops=[weight_edit("station_walk", action="remove")]),
            "limit": 20,
        },
    )
    on_foot = rec.call(
        client,
        "rank-on-foot",
        "A journey on foot: for most areas it is beyond the longest time the release holds",
        "rank",
        {
            "spec": first,
            "operations": operations(commute_ops=[commute_edit(WORKS, mode="walk")]),
            "limit": 20,
        },
    )
    rec.call(
        client,
        "explanations-on-foot",
        "Reasons and trade-offs where a journey is beyond the longest time the release holds",
        "explain_top",
        {"spec": on_foot["data"]["spec"], "limit": 5},
    )
    rec.call(
        client,
        "rank-invalid-operations",
        "An edit that is not an edit: 422, with paths and codes and nothing that was sent",
        "rank",
        {"spec": first, "operations": operations(tag_ops=[{"action": "set"}])},
    )
    return refined["data"]


def record_the_rest(
    rec: Recorder,
    client: TestClient,
    specs: dict[str, dict[str, Any]],
    refined: dict[str, Any],
    defaults: dict[str, Any],
) -> None:
    """Routes 7, 8, 9 and 10, and a request for no route."""
    chosen = [area["area_id"] for area in refined["ranked"][:2]]
    chosen += [area["area_id"] for area in refined["filtered"][:1]]
    rec.call(
        client,
        "compare-three",
        "Three areas side by side, one of them filtered, rows in the order of the weights",
        "compare",
        {"area_ids": chosen, "spec": refined["spec"]},
    )
    rec.call(
        client,
        "compare-two-defaults",
        "Two areas compared with no search open, on a renter's defaults",
        "compare",
        {"area_ids": ["syn-n0001", "syn-n0018"], "spec": defaults["rent"]},
    )
    crime = client.post(
        "/v1/rank",
        json={
            "spec": specs["first"],
            "operations": operations(
                weight_ops=[weight_edit("crime_burglary_theft", action="nudge", step="up_large")]
            ),
        },
    ).json()["data"]["spec"]
    rec.call(
        client,
        "compare-crime",
        "Two areas compared on a search that weighs recorded crime",
        "compare",
        {"area_ids": ["syn-n0006", "syn-n0003"], "spec": crime},
    )
    rec.call(
        client,
        "compare-invalid",
        "One area is not a comparison: 422",
        "compare",
        {"area_ids": ["syn-n0001"], "spec": defaults["rent"]},
    )
    rec.call(
        client,
        "compare-area-not-found",
        "A comparison that names an area the release lacks: 404",
        "compare",
        {"area_ids": ["syn-n0001", "syn-n9999"], "spec": defaults["rent"]},
    )

    rec.call(
        client,
        "places-search",
        "Places offered as a name is typed",
        "search_places",
        {"q": "pel"},
    )
    rec.call(
        client,
        "places-search-one-kind",
        "A search that finds schools, each with the station that stands in for it",
        "search_places",
        {"q": "school", "limit": 5},
    )
    rec.call(
        client,
        "places-search-none",
        "A search that finds nothing",
        "search_places",
        {"q": "zzzz"},
    )
    rec.call(
        client,
        "places-search-invalid",
        "One character is too few: 422",
        "search_places",
        {"q": "p"},
    )

    to_school = specs["first"] | {"commutes": [commute(SCHOOL, minutes=30)]}
    made = rec.call(
        client,
        "share-made",
        "A share of a search that names a school: the station stands in for it",
        "create_share",
        {"spec": to_school},
    )
    rec.call(
        client,
        "share-made-exact",
        "A share that keeps the exact place, because the sender asked",
        "create_share",
        {"spec": to_school, "exact_destinations": True},
    )
    rec.call(
        client,
        "share-made-no-place",
        "A share of a search that names no place: there is nothing to stand in for",
        "create_share",
        {"spec": specs["first"] | {"commutes": []}},
    )
    rec.call(
        client,
        "share-opened",
        "A share opened: the stored spec, ranked now",
        "get_share",
        share_id=made["data"]["share_id"],
    )
    rec.call(
        client,
        "share-not-found",
        "A share id nobody made: 404",
        "get_share",
        share_id="AAAAAAAAAAAAAAAAAAAAAA",
    )
    rec.call(
        client,
        "not-found",
        "A path that is no route: 404, in the same envelope",
        None,
    )


def record_what_needs_another_service(rec: Recorder, specs: dict[str, dict[str, Any]]) -> None:
    """A model that fails, a fault in the service, and a share that outlives its release."""
    slow = TestClient(create_app(make_deps(interpreter=ModelThatTimesOut(), model_id="a-model")))
    rec.call(
        slow,
        "interpret-degraded",
        "The model did not answer, so the rules read the words: degraded, and still a reading",
        "interpret",
        {"text": PROMPTS["first"][0]},
    )

    rec.call(
        read_by(
            model_output(
                # A model says, for each edit, which of the person's words it rests on.
                # An edit whose words are not in the text is not taken, and the rules read it.
                commute_ops=[
                    {
                        "action": "add",
                        "destination_text": "Cindermoor Works",
                        "position": 0,
                        "mode": "unchanged",
                        "max_minutes": 30,
                        "strictness": "unchanged",
                        "step": "none",
                        "provenance": "stated",
                        "words": "30 minutes to Cindermoor Works",
                    }
                ],
                tag_ops=[
                    {
                        "action": "nudge",
                        "tag_id": "leafy",
                        "value": 0.0,
                        "step": "up_large",
                        "provenance": "stated",
                        "words": "leafy",
                    }
                ],
            )
        ),
        "interpret-by-model",
        "A sentence read by a model: the same edits, and the answer says who read it",
        "interpret",
        {"text": "Somewhere leafy, 30 minutes to Cindermoor Works"},
    )
    rec.call(
        read_by(model_output(status="off_topic")),
        "interpret-off-topic",
        "A model finds nothing about where to live: no edit, and the notice in the API's words",
        "interpret",
        {"text": "What is the best way to learn the piano"},
    )

    broken = TestClient(
        create_app(make_deps(explainer=ExplainerThatBreaks())), raise_server_exceptions=False
    )
    rec.call(
        broken,
        "error-internal",
        "A fault in the service: 500, with fixed words and a request id to quote",
        "explain_top",
        {"spec": specs["first"], "limit": 5},
    )

    # One store behind two services, as one service is before and after a release.
    store = InMemoryShareStore()
    before = load_release(SYNTHETIC_FIXTURE)
    then = TestClient(create_app(make_deps(release=before, shares=store)))
    made = then.post("/v1/shares", json={"spec": specs["first"]}).json()["data"]

    newer = replace(before, manifest=before.manifest.replace(release_id="syn-2026-10-01-01"))
    rec.call(
        TestClient(create_app(make_deps(release=newer, shares=store))),
        "share-opened-stale",
        "A share opened on a newer release than it was made on: stale, and ranked again",
        "get_share",
        share_id=made["share_id"],
    )
    without = tuple(place for place in before.places if place.place_id != WORKS)
    rec.call(
        TestClient(create_app(make_deps(release=replace(before, places=without), shares=store))),
        "share-gone",
        "A share whose place the release no longer has: 410",
        "get_share",
        share_id=made["share_id"],
    )


# What one person types on one visit, in order. Each sentence is made up for the recording.
VISIT = {
    "first": PROMPTS["first"][0],
    "second": SECOND_SENTENCE,
    "place": "and 30 minutes to Pellam",
    "people": "not too many students, and near a park",
    "unread": "What is the best way to learn the piano",
    "slow": "somewhere by the water",
}
PICKED = "syn-p0017"  # Pellam Exchange, the answer to "which Pellam?"


def record_the_visit(rec: Recorder, defaults: dict[str, Any]) -> None:
    """One person's whole visit, each request made of the answer before it.

    Every body here is the body the website sends at that step, and
    `test/visit.test.tsx` holds the website to it: a request the website makes
    that is not one of these fails the test. So what is recorded is what the
    service answers to the website as it is, and not to a request made up for
    a test. When the website changes what it sends, change it here and record.
    """
    client = TestClient(create_app(make_deps()))
    numbered = iter(range(1, 100))

    def step(name: str, shows: str, operation: str, body: Any = None, **path: str) -> Any:
        scenario = f"visit/{next(numbered):02d}-{name}"
        return rec.call(client, scenario, shows, operation, body, **path)

    def ranked_and_explained(name: str, spec: dict[str, Any]) -> dict[str, Any]:
        ranking = step(f"{name}-rank", "Its ranking", "rank", {"spec": spec, "limit": 20})
        step(f"{name}-reasons", "Its reasons", "explain_top", {"spec": spec, "limit": 5})
        return ranking["data"]

    def said(name: str, shows: str, spec: dict[str, Any]) -> dict[str, Any]:
        return step(name, shows, "interpret", {"text": VISIT[name], "spec": spec})["data"]

    def moved(name: str, shows: str, spec: dict[str, Any], **groups: Any) -> dict[str, Any]:
        body = {"spec": spec, "limit": 20, "operations": operations(**groups)}
        ranking = step(f"{name}-rank", shows, "rank", body)["data"]
        step(f"{name}-reasons", "Its reasons", "explain_top", {"spec": ranking["spec"], "limit": 5})
        return ranking

    # A first sentence, sent with the defaults the page opened on.
    spec = said("first", "A first sentence, sent with a renter's defaults", defaults["rent"])
    spec = spec["spec"]
    ranked_and_explained("first", spec)

    # A second sentence, sent with the spec the first one left.
    spec = said("second", "A second sentence: one thing more, one taken off", spec)["spec"]
    ranked_and_explained("second", spec)

    # One control moved: the journey made a firm limit.
    spec = moved(
        "firm",
        "A control moved: the journey made a firm limit",
        spec,
        commute_ops=[commute_edit(WORKS, strictness="hard")],
    )["spec"]

    # A place named in part. Nothing is applied, so nothing is ranked until it is answered.
    asked = said("place", "A place named in part: a question, and no edit applied", spec)
    question = asked["clarify"][0]
    answer = asked["operations"][question["group"]][question["index"]] | {"place_id": PICKED}
    spec = moved(
        "answered",
        "The question answered: the edit, with the id picked",
        spec,
        **{question["group"]: [answer]},
    )["spec"]

    # Part of a sentence is about who lives somewhere. The rest is applied.
    spec = said("people", "A sentence in part about people: the notice, and the rest", spec)["spec"]
    final = ranked_and_explained("people", spec)

    # Nothing in the sentence is about where to live.
    said("unread", "A sentence with nothing to read in it: no edit, and no ranking", spec)

    # Two areas compared on the search as it stands.
    chosen = [final["ranked"][1]["area_id"], final["ranked"][0]["area_id"]]
    step(
        "compare",
        "The second and the first result compared, on the search as it stands",
        "compare",
        {"area_ids": chosen, "spec": spec},
    )

    # A link made, and opened.
    made = step(
        "share-made",
        "A link to the search",
        "create_share",
        {"spec": spec, "exact_destinations": False},
    )["data"]
    step("share-opened", "The link opened", "get_share", share_id=made["share_id"])
    step(
        "share-reasons",
        "The reasons of the shared search",
        "explain_top",
        {"spec": made["spec"], "limit": 5},
    )

    # The model does not answer, so the rules read the words in its place.
    slow = TestClient(create_app(make_deps(interpreter=ModelThatTimesOut(), model_id="a-model")))
    read = rec.call(
        slow,
        f"visit/{next(numbered):02d}-slow",
        "A sentence the model did not answer: read by the rules, and degraded",
        "interpret",
        {"text": VISIT["slow"], "spec": defaults["rent"]},
    )["data"]
    ranked_and_explained("slow", read["spec"])


def main() -> int:
    # The service writes its log to a stream. Here it is kept and never read.
    logs.configure_logging(io.StringIO())
    rec = Recorder()
    client = TestClient(create_app(make_deps()))
    meta = record_the_release(rec, client)
    specs = record_the_readings(rec, client)
    refined = record_the_rankings(rec, client, specs, meta["defaults"])
    record_the_rest(rec, client, specs, refined, meta["defaults"])
    record_what_needs_another_service(rec, specs)
    record_the_visit(rec, meta["defaults"])
    if not rec.finish():
        sys.stderr.write("Nothing was written. Reword these in record.py, and record again:\n")
        sys.stderr.write("".join(f"  {failure}\n" for failure in rec.failed))
        return 1
    sys.stdout.write(f"Recorded {len(rec.written)} answers in {OUT}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
