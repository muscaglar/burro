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
from burro_api.deps import Deps
from burro_api.loading import load_census, load_income, load_release
from burro_api.providers.choose import BY_RULES, told_of
from burro_api.providers.terms import TERMS
from burro_api.reader import ModelInterpreter, ModelRefused, ModelReply, ModelTimeout
from burro_api.settings import SYNTHETIC_CENSUS, SYNTHETIC_FIXTURE, SYNTHETIC_INCOME
from burro_api.stores import InMemoryShareStore
from burro_core import RuleInterpreter, TemplateExplainer
from burro_core.catalogue import band_of, percentile_of, tag_raw, tags_of
from burro_core.estimate import ESTIMATED
from burro_core.ids import FeatureId, GrittyVariant, InterpreterName
from burro_core.release import InMemoryRelease, parse_release
from burro_pipeline.release.synthetic.build import RELEASE_IDS, build_synthetic
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
    "get_census": ("GET", "/v1/areas/{id_or_slug}/census"),
    "get_income": ("GET", "/v1/areas/{id_or_slug}/income"),
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

    name = InterpreterName.MODEL

    def interpret(self, request: object) -> Any:
        raise ModelTimeout


class ModelThatRefuses:
    """Stands in for a provider that will not read what was typed, so that the rules read it."""

    name = InterpreterName.MODEL

    def interpret(self, request: object) -> Any:
        raise ModelRefused


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


# What people are told in a recording where a model reads: the first provider of
# the table, as the table has it. No recording calls a provider.
A_PROVIDER = next(iter(TERMS.values()))
A_MODEL_READS = told_of(A_PROVIDER, with_settings=False)


def make_deps(**changes: Any) -> Deps:
    """What the service depends on. People are told what fits whoever reads."""
    by_rules = isinstance(changes.get("interpreter", RuleInterpreter()), RuleInterpreter)
    release = load_release(SYNTHETIC_FIXTURE)
    # The made-up count is of the committed release. Another release is served with none.
    changes.setdefault(
        "census", None if "release" in changes else load_census(SYNTHETIC_CENSUS, release)
    )
    # So is the made-up estimate of household income.
    changes.setdefault(
        "income", None if "release" in changes else load_income(SYNTHETIC_INCOME, release)
    )
    deps = Deps(
        release=release,
        interpreter=RuleInterpreter(),
        explainer=TemplateExplainer(),
        shares=InMemoryShareStore(),
        calls=InMemoryCallLog(),
        clock=FixedClock(),
        ids=SeededIds(SEED),
        told=BY_RULES,
        allowed_origins=(ORIGIN,),
    )
    return replace(deps, **({"told": BY_RULES if by_rules else A_MODEL_READS} | changes))


def _data(body: Any) -> dict[str, Any]:
    return body.get("data") or {}


def _reads(body: Any) -> tuple[bool, bool]:
    """Whether the answer says a model reads what is typed, and that the settings go with it."""
    reader = _data(body)["reader"]
    return reader["model_reads"], reader["settings_sent"]


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


def _offered(body: Any) -> list[list[str]]:
    """The directions each suggestion of an answer offers, in the order they stand."""
    return [[one["direction"] for one in s["choices"]] for s in _data(body).get("suggestions", [])]


def _guessed(body: Any) -> list[str]:
    """The way of each suggestion that is marked as Burro's guess, in the order they stand."""
    return [
        way["id"]
        for s in _data(body).get("suggestions", [])
        for way in s["choices"]
        if way["guess"]
    ]


def _nothing_applied(body: Any) -> bool:
    """True when the reader applied nothing: a prompt that is not plain is read not at all."""
    return _changed(body) == 0 and not any(_data(body)["operations"].values())


def _vibe(body: Any, tag_id: str) -> dict[str, Any] | None:
    """The vibe of that id in the spec of an answer, where the spec holds it."""
    return next((t for t in _data(body)["spec"]["tags"] if t["tag_id"] == tag_id), None)


def _towards(body: Any, tag_id: str, end: str) -> bool:
    found = _vibe(body, tag_id)
    return found is not None and found["toward"] == end and found["weight"] > 0


def _journeys_of_an_area_with_no_time(body: Any) -> list[bool]:
    """Whether the journeys count, for each listed area that has a journey with no time."""
    return [
        part["present"]
        for area in _data(body)["ranked"]
        if any(leg["status"] == "missing" for leg in area["legs"])
        for part in area["contributions"]
        if part["component"] == "commute"
    ]


def _stands_below(body: Any) -> bool:
    """Whether an area with no figure for what was asked is listed, below every area that has one.

    What was asked is clean air, so the area is one with no figure for it.
    """
    lacks = [
        any(
            part["component"] == "feature:air_no2" and not part["present"]
            for part in area["contributions"]
        )
        for area in _data(body)["ranked"]
    ]
    return any(lacks) and lacks == sorted(lacks)


def _templates(body: Any) -> set[str]:
    """The template of every fact an answer holds."""
    return {fact["template"] for fact in _data(body)["facts"]}


def _fits(body: Any) -> list[dict[str, Any]]:
    """How the budget fits each ranked area that has a cost to hold it against."""
    return [area["budget"] for area in _data(body)["ranked"] if area["budget"] is not None]


def _left_out(body: Any) -> set[str | None]:
    """Why each table of a census is left out for the area, where it is."""
    return {table["reason"] for table in _data(body).get("tables", [])}


def _shares(body: Any) -> set[str]:
    return {row["share"] for table in _data(body).get("tables", []) for row in table["rows"]}


def _bands(body: Any) -> set[str | None]:
    """Where each journey of each listed area stands against its limit, as it was estimated."""
    return {leg["estimate"] for area in _data(body)["ranked"] for leg in area["legs"]}


def _no_minutes(body: Any) -> bool:
    """True when no journey of an answer is given in minutes: an estimate is a band alone."""
    times = ("minutes", "minutes_typical", "minutes_just_missed")
    legs = [leg for area in _data(body)["ranked"] for leg in area["legs"]]
    return all(leg[time] is None for leg in legs for time in times)


def _mixed(body: Any) -> bool:
    """True when a result's strip holds a mark drawn as a range: three bands or more."""
    marks = [mark for area in _data(body)["ranked"] for mark in area["strip"]]
    return any(mark["spread_high"] - mark["spread_low"] >= 2 for mark in marks)


# What each scenario must show to be worth recording. A step of the visit is named without
# its number. A scenario that is not here is recorded whatever it shows.
PROVES: dict[str, Callable[[Any], bool]] = {
    "census": lambda b: (
        _left_out(b) == {None}
        and "fewer than 1 in 100" in _shares(b)
        and {row["depth"] for t in _data(b)["tables"] for row in t["rows"]} == {0, 1, 2}
    ),
    "census-too-few": lambda b: _left_out(b) == {"too_few"} and not _shares(b),
    "census-not-held": lambda b: _left_out(b) == {"not_held"} and not _shares(b),
    "census-not-found": lambda b: b["error"]["code"] == "area_not_found",
    "census-off": lambda b: b["error"]["code"] == "census_not_available",
    "meta-no-census": lambda b: _data(b)["census"]["available"] is False,
    "income": lambda b: (
        _data(b)["estimate"] is not None
        and _data(b)["limits"] is not None
        and _data(b)["none_given"] is None
    ),
    "income-none-given": lambda b: (
        (_data(b)["estimate"], _data(b)["limits"]) == (None, None) and bool(_data(b)["none_given"])
    ),
    "income-not-found": lambda b: b["error"]["code"] == "area_not_found",
    "income-off": lambda b: b["error"]["code"] == "income_not_available",
    "meta-no-income": lambda b: _data(b)["income"]["available"] is False,
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
    "interpret-nothing-read": lambda b: (
        _nothing_applied(b)
        and _data(b)["unmet"] == ["other"]
        and not _data(b)["suggestions"]
        and len(_data(b)["unread"]) == 1
    ),
    "interpret-money-and-work": lambda b: (
        _changed(b) == 2
        and not _data(b)["unread"]
        and [place["name"] for place in _data(b)["places"]] == ["Cindermoor Works"]
    ),
    "interpret-suggest": lambda b: (
        _data(b)["status"] == "suggest"
        and _nothing_applied(b)
        and _offered(b) == [["more", "less", "ignore"], ["less", "ignore"]]
        and len(_data(b)["unread"]) == 1
    ),
    "interpret-suggest-many": lambda b: _nothing_applied(b) and len(_offered(b)) > 4,
    "interpret-suggest-notice": lambda b: (
        _data(b)["notice"] == "neutral_places" and _nothing_applied(b) and bool(_offered(b))
    ),
    "interpret-suggest-place": lambda b: (
        _nothing_applied(b) and [s["target"] for s in _data(b)["suggestions"]] == ["commute"]
    ),
    "interpret-suggest-who-is-counted": lambda b: (
        _data(b)["notice"] == "none"
        and _nothing_applied(b)
        and [s["target"] for s in _data(b)["suggestions"]]
        == ["tag:young_professionals", "tag:pace", "feature:station_walk"]
        and _offered(b)[0] == ["more", "ignore"]
        and "census of 2021" in _data(b)["suggestions"][0]["note"]
        and not _data(b)["suggestions"][0]["add_all"]
    ),
    "interpret-suggest-newcomer": lambda b: (
        _nothing_applied(b)
        and [len(ways) for ways in _offered(b)] == [2, 2, 2, 3, 2, 2]
        and [found["target"] for found in _data(b)["suggestions"][-2:]] == ["budget", "budget"]
    ),
    "interpret-plain-list": lambda b: (
        _data(b)["status"] == "ok" and _changed(b) == 3 and not _data(b)["unread"]
    ),
    "interpret-scale": lambda b: _towards(b, "pace", "low"),
    "interpret-gritty": lambda b: _towards(b, "street_character", "high"),
    "variant-a/interpret-gritty": lambda b: (
        _vibe(b, "works_warehouses") is not None
        and any(a["code"] == "word" and a["word"] == "gritty" for a in _data(b)["assumptions"])
        and "street_cleanliness" in _data(b)["unmet"]
    ),
    "variant-a/meta": lambda b: _data(b)["gritty_variant"] == "a",
    "interpret-rejected": lambda b: bool(_data(b)["rejected"]) and _changed(b) > 0,
    "interpret-unmet": lambda b: len(_data(b)["unmet"]) >= 3 and _changed(b) > 0,
    "meta": lambda b: (
        _reads(b) == (False, False)
        and _data(b)["reader"]["terms_url"] is None
        and _data(b)["census"]["available"] is True
        and _data(b)["income"]["available"] is True
    ),
    "meta-model-reads": lambda b: _reads(b) == (True, False) and _data(b)["reader"]["terms_url"],
    "meta-model-reads-with-settings": lambda b: _reads(b) == (True, True),
    "interpret-degraded": lambda b: (
        _data(b)["degraded"] is True and not _data(b)["model_refused"] and _changed(b) > 0
    ),
    "interpret-refused": lambda b: (
        _data(b)["degraded"] is True and _data(b)["model_refused"] is True and _changed(b) > 0
    ),
    "interpret-by-model": lambda b: (
        _data(b)["interpreter"] == "model"
        and _nothing_applied(b)
        and _guessed(b) == ["more", "firm"]
        and not _data(b)["model_pending"]
    ),
    # Seven of the twelve have no guess. They are the rules' to offer, and a model adds nothing
    # to one: the four readings of a word for how well off a place is, and the three of a word
    # for its identity.
    "interpret-by-model-long": lambda b: (
        _data(b)["interpreter"] == "model"
        and _nothing_applied(b)
        and len(_data(b)["suggestions"]) == 12
        and len(_guessed(b)) == 5
        and _data(b)["notice"] == "none"
        and sum(1 for s in _data(b)["suggestions"] if len(s["choices"]) > 3) == 1
        and sum(1 for s in _data(b)["suggestions"] if s["add_all"] and s["needs"]) == 2
        and bool(_data(b)["unread"])
    ),
    "interpret-by-model-place": lambda b: (
        _nothing_applied(b)
        and [s["asks_place"] for s in _data(b)["suggestions"]] == [True]
        and _data(b)["suggestions"][0]["named_at"] is not None
        and _data(b)["suggestions"][0]["add_all"] == ""
    ),
    "interpret-by-model-least": lambda b: (
        _nothing_applied(b) and _offered(b) == [["ignore"]] and _guessed(b) == []
    ),
    "interpret-rules-at-once": lambda b: (
        _data(b)["interpreter"] == "rule"
        and _data(b)["model_pending"] is True
        and _nothing_applied(b)
        and _guessed(b) == []
        and len(_data(b)["suggestions"]) >= 4
    ),
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
    "rank-suggestion-chosen": lambda b: _changed(b) == 1 and len(_data(b)["ranked"]) == 20,
    "rank-shelf": lambda b: _changed(b) == 1 and _towards(b, "leafy", "high"),
    "rank-scale": lambda b: _towards(b, "pace", "low") and _mixed(b),
    "rank-scale-turned": lambda b: _changed(b) == 1 and _towards(b, "pace", "high"),
    "rank-two-places": lambda b: _journeys_of_an_area_with_no_time(b) == [True],
    "explanations-only-one": lambda b: {"missing_journey", "travel_pt_over"} <= _templates(b),
    "explanations-by-bike-over": lambda b: "travel_other_over" in _templates(b),
    # An area with no time for the one journey stands below every area that has one, so it
    # is ranked and is not among the twenty that are listed.
    "rank-no-time": lambda b: (
        _journeys_of_an_area_with_no_time(b) == []
        and _data(b)["areas_ranked"] > len(_data(b)["ranked"])
        and _data(b)["ranked"][0]["rank"] == 1
    ),
    "compare-three": lambda b: len({area["status"] for area in _data(b)["areas"]}) > 1,
    "compare-two-journeys": lambda b: (
        len([row for row in _data(b)["rows"] if row["place"] is not None]) == 2
        and "missing_journey" in _templates(b)
        and "character_unknown" in {area["status"] for area in _data(b)["areas"]}
        and any(0 < area["present"] < area["counted"] for area in _data(b)["areas"])
    ),
    "share-made": lambda b: _data(b)["coarsened"] is True,
    "share-made-exact": lambda b: _data(b)["coarsened"] is False,
    "share-opened-stale": lambda b: _data(b)["stale"] is True,
    "preview/meta": lambda b: (
        _data(b)["preview"] is True
        and _data(b)["holds"] == {"journeys": False, "costs": False}
        and [held["tag_id"] for held in _data(b)["recipes"] if held["placed"]]
        == ["quiet_residential", "parks_close_by", "homes"]
    ),
    "preview/interpret-plain": lambda b: (
        _changed(b) == 1
        and [thing["target"] for thing in _data(b)["not_in_release"]] == ["tag:leafy"]
    ),
    "preview/rank-plain": lambda b: len(_data(b)["ranked"]) == 20,
    "preview/interpret-home": lambda b: (
        _data(b)["spec"]["tenure"] == "buy"
        and _data(b)["spec"]["budget"]["amount"] is None
        and [thing["target"] for thing in _data(b)["not_in_release"]] == ["budget"]
    ),
    "preview/interpret-long": lambda b: (
        _nothing_applied(b)
        and bool(_offered(b))
        and [thing["target"] for thing in _data(b)["not_in_release"]]
        == ["feature:culture_venues_per_homes", "commute", "budget"]
        and bool(_data(b)["unread"])
    ),
    "preview/interpret-journey": lambda b: (
        not _data(b)["clarify"]
        and [thing["target"] for thing in _data(b)["not_in_release"]] == ["commute"]
    ),
    "preview/rank-refused-edits": lambda b: (
        [edit["reason"] for edit in _data(b)["rejected"]] == ["not_in_release"] * 3
        and bool(_data(b)["ranked"])
    ),
    "preview/rank-lacking": lambda b: _stands_below(b),
    "preview/places-search": lambda b: (
        _data(b)["places"] == [] and [area["name"] for area in _data(b)["areas"]] == ["Alderwick"]
    ),
    "places-search": lambda b: (
        len(_data(b)["places"]) == 3
        and [area["name"] for area in _data(b)["areas"]] == ["Pellam Cross"]
    ),
    "places-search-area": lambda b: (
        _data(b)["places"] == []
        and [(a["name"], a["named"]["label"]) for a in _data(b)["areas"]]
        == [("Ostrel Vale", "Quillhaven 016")]
    ),
    **{
        f"example-{at}": lambda b: (
            _data(b)["status"] == "ok"
            and not _data(b)["rejected"]
            and not _data(b)["unread"]
            and _changed(b) == len(_data(b)["applied"]) > 0
        )
        for at in range(1, 7)
    },
    **{
        f"preview/example-{at}": lambda b: (
            len(_data(b)["ranked"]) == 20 and not _data(b)["rejected"]
        )
        for at in range(1, 7)
    },
    "one-number/area": lambda b: (
        "cost_buy_median" in _templates(b)
        and not {"cost_buy", "cost_rent"} & _templates(b)
        and all(
            (row["tenure"], row["lower_quartile"], row["upper_quartile"], row["confidence"])
            == ("buy", None, None, "unstated")
            for row in _data(b)["cost"]
        )
    ),
    "one-number/rank-buyer": lambda b: (
        all(fit["upper_quartile"] is None for fit in _fits(b))
        and {fit["margin"] < 0 for fit in _fits(b)} == {True, False}
    ),
    "one-number/explanations-buyer": lambda b: (
        {"budget_under_median", "budget_over_median"} <= _templates(b)
    ),
    "estimate/meta": lambda b: (
        _data(b)["journey_estimate"] is not None
        and _data(b)["journey_estimate"]["said"] == ESTIMATED
        and _data(b)["holds"]["journeys"] is True
    ),
    "estimate/rank": lambda b: (
        _bands(b) == {"likely_within", "borderline", "likely_beyond"}
        and _legs(b, "estimated") == len(_data(b)["ranked"])
        and not _data(b)["filtered"]
        and _no_minutes(b)
    ),
    "estimate/explanations": lambda b: "travel_estimated" in _templates(b),
    "estimate/rank-firm": lambda b: (
        _bands(b) == {"likely_within", "borderline"}
        and {one["reason"] for one in _data(b)["filtered"]} == {"commute_likely_beyond"}
    ),
    "estimate/compare": lambda b: (
        {c["estimate"] for row in _data(b)["rows"] for c in row["cells"]}
        == {None, "likely_within", "borderline", "likely_beyond"}
        and {area["status"] for area in _data(b)["areas"]} == {"ranked", "commute_likely_beyond"}
    ),
    "counted/area": lambda b: (
        "cost_buy_sold" in _templates(b)
        and not {"cost_buy", "cost_rent", "cost_buy_median"} & _templates(b)
        and all(
            row["sales"] >= 10 and row["since"] and row["confidence"] in ("high", "medium")
            for row in _data(b)["cost"]
        )
        and {row["confidence"] for row in _data(b)["cost"]} == {"high", "medium"}
    ),
    "counted/rank-firm": lambda b: (
        bool(_data(b)["filtered"])
        and {fit["margin"] < 0 for fit in _fits(b)} == {True, False}
        and all(fit["upper_quartile"] is None for fit in _fits(b))
    ),
    "counted/explanations-firm": lambda b: (
        {"budget_under_median", "budget_over_median"} <= _templates(b)
        and any("half_sold" in fact["slots"] for fact in _data(b)["facts"])
    ),
    "visit/first": lambda b: _changed(b) == 4,
    "visit/second": lambda b: _changed(b) == 2 and _off(b, "highstreet_access"),
    "visit/firm-rank": lambda b: bool(_data(b)["filtered"]) and bool(_data(b)["ranked"]),
    "visit/place": lambda b: _asks(b, options=True) and _changed(b) == 0,
    "visit/answered-rank": lambda b: len(_data(b)["spec"]["commutes"]) == 2,
    "visit/people": lambda b: _data(b)["notice"] == "neutral_places" and _changed(b) > 0,
    "visit/unread": lambda b: _changed(b) == 0 and not _data(b)["clarify"],
    "visit/slow-at-once": lambda b: (
        _data(b)["model_pending"] is True and not _data(b)["degraded"] and len(_offered(b)) == 1
    ),
    "visit/slow": lambda b: (
        _data(b)["degraded"] is True and _nothing_applied(b) and len(_offered(b)) == 1
    ),
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


def tag_edit(tag_id: str, **changes: Any) -> dict[str, Any]:
    edit: dict[str, Any] = {
        "action": "nudge",
        "tag_id": tag_id,
        "value": 0.0,
        "step": "none",
        "toward": "default",
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


def journey_read(name: str, minutes: int, words: str) -> dict[str, Any]:
    """A journey as a model answers it, with the words of the person's that it rests on."""
    return {
        "action": "add",
        "destination_text": name,
        "position": 0,
        "mode": "unchanged",
        "max_minutes": minutes,
        "strictness": "unchanged",
        "step": "none",
        "provenance": "stated",
        "words": words,
    }


def vibe_read(tag_id: str, words: str) -> dict[str, Any]:
    return {
        "action": "nudge",
        "tag_id": tag_id,
        "value": 0.0,
        "step": "up_large",
        "toward": "high",
        "provenance": "stated",
        "words": words,
    }


def wish_read(feature_id: str, words: str) -> dict[str, Any]:
    return {
        "action": "nudge",
        "feature_id": feature_id,
        "value": 0.0,
        "step": "up_large",
        "direction": "default",
        "provenance": "stated",
        "words": words,
    }


def read_by(answer: dict[str, Any], with_settings: bool = False) -> TestClient:
    """The service with a model behind it that gives this answer."""
    interpreter = ModelInterpreter(
        ModelThatAnswers(answer),
        model="a-model",
        max_tokens=2048,
        timeout_s=6.0,
        with_settings=with_settings,
    )
    told = told_of(A_PROVIDER, with_settings)
    return TestClient(create_app(make_deps(interpreter=interpreter, told=told, model_id="a-model")))


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
        "Renting a 1 bed for about £1,700 a month, leafy and quiet, 35 minutes to Cindermoor Works",
        "A first sentence, read in full: a budget, two tags and a journey",
    ),
    "nights-out": (
        "Somewhere buzzy with bars and restaurants, I work at Pellam Exchange",
        "A sentence about venues, with a workplace and no budget",
    ),
    "buyer-family": (
        "Buying a terraced house for about £450k, good primary schools and a park for the kids, "
        "40 minutes to Dulcimer Green Hospital",
        "A buyer, so the tenure changes and the buyer's defaults come in",
    ),
    "two-journeys": (
        "Renting a studio, no more than £1,100 a month, 30 minutes to Wexmoor University "
        "and at most 25 minutes to Foxholt Market",
        "A firm budget and two journeys, one of them firm",
    ),
    "by-the-river": (
        "Historic, near the river, 20 minutes to Tallowgate Guild Quarter by bike",
        "A vibe towards one end, a feature, and a journey by bike",
    ),
}


# Plain prompts, each read in full. Each is ranked and explained as the prompts above are.
PLAIN = (
    (
        "money-and-work",
        "I rent and can pay about £1,500 a month for a one bed flat. I work at Cindermoor Works.",
        "Two plain sentences about money and work, read in full, and the place by its name",
    ),
    ("scale", "not buzzy", "A scale, asked for towards its low end"),
    ("gritty", "somewhere a bit gritty", "A word with two meanings, where gritty is a scale"),
    ("near-a-station", "near a station", "One wish, for something an area can do well or badly"),
    (
        "two-places",
        "new build, 35 minutes to Cindermoor Works and 40 minutes to Wexmoor University",
        "Two flexible journeys, where a listed area has a time for one and none for the other",
    ),
    (
        "no-time",
        "new build, walkable, 40 minutes to Wexmoor University",
        "One journey, for which an area has no time, so it stands below the twenty listed",
    ),
    (
        "only-one",
        "only Gorsebeck, 35 minutes to Cindermoor Works and 40 minutes to Wexmoor University",
        "One area chosen: a journey over its limit is its trade-off, and another has no time",
    ),
    (
        "by-bike-over",
        "only Wexmoor, 10 minutes to Cindermoor Works by bike",
        "One area chosen, whose journey by bike is over the limit set for it",
    ),
)

# Prompts that are not plain. Nothing of one is applied. What was noticed is offered.
NOT_PLAIN = (
    (
        "suggest",
        "Pubs are so noisy",
        "A prompt that is not plain: nothing applied, two things noticed, and a stretch not read",
    ),
    (
        "suggest-many",
        "My sister wants pubs, a station, a high street, a playground, a river and clean air",
        "More things noticed than are shown at first",
    ),
    (
        "suggest-notice",
        "leafy with lots of students. My street is noisy.",
        "Not plain, with a phrase about who lives somewhere: the notice, and what was noticed",
    ),
    (
        "suggest-who-is-counted",
        "young professionals, lively, near a station",
        "Who lived there at the census, offered towards more and no other way, with its note",
    ),
    (
        "suggest-place",
        "My partner works at Pellam Infirmary",
        "A place noticed in a prompt that is not plain: offered by name, and not added",
    ),
    (
        "suggest-newcomer",
        "I am moving to the city in three months for a job at Cindermoor Works. I have never "
        "lived there. I want somewhere leafy and fairly quiet, not too far from a decent pub. "
        "I can spend about £1,600 a month on a one bed flat.",
        "A newcomer's own words: six things noticed, of which five have one way to be wanted",
    ),
)

# The sentence the page gives as one that Burro reads, where it could read nothing of another.
READABLE = "leafy and quiet, near a park"
# The sentences the first screen offers to start from, in the order the website tries
# them. A test of the website holds each to the words it shows, and to what it says each
# asks for, so that an example is never offered on a release that cannot answer it.
EXAMPLES = (
    "Renting a one bedroom flat for about £1,700 a month, somewhere leafy and quiet",
    "Buying a terraced house, with good primary schools and a park nearby",
    "Somewhere buzzy with bars and restaurants, close to a station",
    "Somewhere quiet, near a big park",
    "Clean air and a park nearby",
    "Buying a house, somewhere quiet with clean air",
)


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


def record_the_census(rec: Recorder, client: TestClient) -> None:
    """Route 13: the census of one area, which only the page of an area asks for."""
    rec.call(
        client,
        "census",
        "The census of one area: each figure a share with its count, beside the whole city's",
        "get_census",
        id_or_slug="foxholt",
    )
    rec.call(
        client,
        "census-too-few",
        "An area where too few were counted: every table is left out, and says so",
        "get_census",
        id_or_slug="grapnel-dock",
    )
    rec.call(
        client,
        "census-not-held",
        "An area the count holds nothing for: every table says so, and none gives a figure",
        "get_census",
        id_or_slug="otterby-fields",
    )
    rec.call(
        client,
        "census-not-found",
        "A slug the release lacks: 404",
        "get_census",
        id_or_slug="nowhere-at-all",
    )
    off = TestClient(create_app(make_deps(census=None)))
    rec.call(
        off,
        "census-off",
        "A service that serves no census: 404, and no figure",
        "get_census",
        id_or_slug="foxholt",
    )
    rec.call(off, "meta-no-census", "What route 11 says where no census is served", "get_meta")


def record_the_examples(rec: Recorder, client: TestClient, preview: TestClient) -> None:
    """Each sentence the first screen offers, read on a release that holds everything.

    And ranked on the preview, for those the preview can answer: an example that
    the page offers must give a list.
    """
    for at, text in enumerate(EXAMPLES, start=1):
        rec.call(
            client,
            f"example-{at}",
            "A sentence the first screen offers: it is plain, and every edit of it is applied",
            "interpret",
            {"text": text},
        )
        read = preview.post("/v1/interpret", json={"text": text}).json()["data"]
        if not read["not_in_release"]:
            rec.call(
                preview,
                f"preview/example-{at}",
                "The same sentence ranked on a preview that can answer all of it",
                "rank",
                {"spec": read["spec"], "limit": 20},
            )


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
        "A cheaper home where no budget is set: the edit is rejected, the park is applied",
        "interpret",
        {"text": "Somewhere a bit cheaper, near a park"},
    )
    rec.call(
        client,
        "interpret-unmet",
        "Things the data cannot answer: each is named in unmet, and the rest is applied",
        "interpret",
        {"text": "leafy, broadband, flood risk, near a mosque"},
    )
    rec.call(
        client,
        "interpret-invalid-text",
        "A line of spaces: 422 on the text",
        "interpret",
        {"text": "   "},
    )
    rec.call(
        client,
        "interpret-plain-list",
        "A plain list of wishes, read whole: the sentence the page gives as one Burro reads",
        "interpret",
        {"text": READABLE},
    )
    for name, text, shows in PLAIN:
        read = rec.call(client, f"interpret-{name}", shows, "interpret", {"text": text})
        specs[name] = read["data"]["spec"]
    for name, text, shows in NOT_PLAIN:
        rec.call(client, f"interpret-{name}", shows, "interpret", {"text": text})
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
    record_the_vibes(rec, client, specs, defaults)
    return refined["data"]


def record_the_vibes(
    rec: Recorder, client: TestClient, specs: dict[str, dict[str, Any]], defaults: dict[str, Any]
) -> None:
    """Route 2, as the shelf, a suggestion and a chip of a scale send to it."""
    shelf = rec.call(
        client,
        "rank-shelf",
        "A word of the shelf added to a search: one edit, sent with the defaults",
        "rank",
        {
            "spec": defaults["rent"],
            "operations": operations(tag_ops=[tag_edit("leafy", step="up_large", toward="high")]),
            "limit": 20,
        },
    )
    rec.call(
        client,
        "explanations-shelf",
        "The reasons of a search for one vibe",
        "explain_top",
        {"spec": shelf["data"]["spec"], "limit": 5},
    )
    noticed = client.post(
        "/v1/interpret", json={"text": NOT_PLAIN[0][1], "spec": defaults["rent"]}
    ).json()["data"]
    fewer = noticed["suggestions"][0]["choices"][1]
    chosen = rec.call(
        client,
        "rank-suggestion-chosen",
        "A suggestion chosen: its edits, sent as a control's are",
        "rank",
        {"spec": noticed["spec"], "operations": fewer["operations"], "limit": 20},
    )
    rec.call(
        client,
        "explanations-suggestion-chosen",
        "The reasons of a search made of one suggestion",
        "explain_top",
        {"spec": chosen["data"]["spec"], "limit": 5},
    )
    calm = next(tag for tag in specs["scale"]["tags"] if tag["tag_id"] == "pace")
    turned = rec.call(
        client,
        "rank-scale-turned",
        "A scale turned to its other end, with the weight it had",
        "rank",
        {
            "spec": specs["scale"],
            "operations": operations(
                tag_ops=[tag_edit("pace", action="set", value=calm["weight"], toward="high")]
            ),
            "limit": 20,
        },
    )
    rec.call(
        client,
        "explanations-scale-turned",
        "The reasons of a search for the other end of a scale",
        "explain_top",
        {"spec": turned["data"]["spec"], "limit": 5},
    )


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
    # What is said of the place leads, so an area with no figure for it lacks most of what
    # was asked. Here the person has put the journeys above all else, so that the area
    # that is listed apart has most of what counts and none of the character.
    journeys_first = client.post(
        "/v1/rank",
        json={
            "spec": specs["two-places"],
            "operations": operations(
                setting_ops=[
                    {
                        "action": "set",
                        "setting": "commute_weight",
                        "choice": "none",
                        "value": 1.0,
                        "step": "none",
                        "provenance": "ui_edit",
                    }
                ]
            ),
        },
    ).json()["data"]["spec"]
    rec.call(
        client,
        "compare-two-journeys",
        "Four areas on a search with two journeys, which the person weighs above all else: "
        "a row for each, one area with no time for one of them, one whose fit rests on part "
        "of what counts, and one listed apart",
        "compare",
        {
            "area_ids": ["syn-n0023", "syn-n0014", "syn-n0008", "syn-n0017"],
            "spec": journeys_first,
        },
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
        "places-search-area",
        "A search by name that finds an area and no place: the area, with its label beside it",
        "search_places",
        {"q": "ostrel"},
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
    opened = rec.call(
        client,
        "share-opened",
        "A share opened: the stored spec, ranked now",
        "get_share",
        share_id=made["data"]["share_id"],
    )
    rec.call(
        client,
        "explanations-share-opened",
        "The reasons of the search a share holds",
        "explain_top",
        {"spec": opened["data"]["spec"], "limit": 5},
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
    refuses = TestClient(create_app(make_deps(interpreter=ModelThatRefuses(), model_id="a-model")))
    rec.call(
        refuses,
        "interpret-refused",
        "The provider would not read the words, so the rules did: refused, and still a reading",
        "interpret",
        {"text": PROMPTS["first"][0]},
    )

    # A model says, for each thing it read, which of the person's words it rests on.
    # Nothing it reads is applied: each thing is offered, with Burro's guess marked.
    rec.call(
        read_by(
            model_output(
                commute_ops=[
                    journey_read(
                        "Cindermoor Works", 30, "no more than 30 minutes to Cindermoor Works"
                    )
                ],
                tag_ops=[vibe_read("leafy", "somewhere leafy")],
            )
        ),
        "interpret-by-model",
        "A sentence read by a model: nothing is applied, and each thing it read is offered, "
        "with Burro's guess marked",
        "interpret",
        {"text": "Ideally somewhere leafy, no more than 30 minutes to Cindermoor Works"},
    )
    long = (
        "I want to live somewhere quiet, with access to parks, slightly affluent but with some "
        "culture around it, something with a real identity. At most 35-40min commute from "
        "Pellam Exchange. If I'm renting, max \N{POUND SIGN}1,900 a month for a 1 bed flat."
    )
    read_long = model_output(
        budget_ops=[
            {
                "action": "set",
                "tenure": "rent",
                "amount": 1900,
                "segment": "bed_1",
                "strictness": "hard",
                "step": "none",
                "provenance": "stated",
                "words": "max \N{POUND SIGN}1,900 a month for a 1 bed flat",
            }
        ],
        commute_ops=[
            journey_read("Pellam Exchange", 40, "At most 35-40min commute from Pellam Exchange")
        ],
        weight_ops=[wish_read("culture_venues", "with some culture around it")],
        tag_ops=[
            vibe_read("quiet_residential", "somewhere quiet"),
            vibe_read("parks_close_by", "with access to parks"),
        ],
    )
    rec.call(
        read_by(read_long),
        "interpret-by-model-long",
        "A long sentence read by a model: twelve offers, each in four parts, one with a choice "
        "of two things, a journey and a budget that may be made firm, words nothing was made of, "
        "and seven readings of two words that the rules offer with no guess",
        "interpret",
        {"text": long},
    )
    rec.call(
        read_by(read_long),
        "interpret-rules-at-once",
        "The same, asked of the rules alone: what they offer is served at once, with no guess, "
        "and the answer says that a model has more to read",
        "interpret",
        {"text": long, "ask_model": False},
    )
    rec.call(
        read_by(
            model_output(
                commute_ops=[
                    journey_read("Mirrowick Basin", 40, "At most 40 minutes from Mirrowick Basin")
                ]
            )
        ),
        "interpret-by-model-place",
        "A journey to a place the release does not hold: a question, with its minutes, that "
        "leads to the place search",
        "interpret",
        {"text": "At most 40 minutes from Mirrowick Basin, ideally"},
    )
    rec.call(
        read_by(
            model_output(
                commute_ops=[
                    journey_read("Mirrowick Basin", 45, "Minimum 45 minutes from Mirrowick Basin")
                ]
            )
        ),
        "interpret-by-model-least",
        "A least distance: Burro cannot keep a search away from a place, and says so, with "
        "nothing to press but Skip",
        "interpret",
        {"text": "Minimum 45 minutes from Mirrowick Basin, ideally"},
    )
    rec.call(
        read_by(model_output()),
        "meta-model-reads",
        "Who reads, where a model does: what people are told of its provider, in the API's words",
        "get_meta",
    )
    rec.call(
        read_by(model_output(), with_settings=True),
        "meta-model-reads-with-settings",
        "The same, where the service is set to send the search settings with the words",
        "get_meta",
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


def record_the_other_gritty(rec: Recorder) -> None:
    """The release that carries gritty the other way: a vibe from land use, with one way.

    It is built in memory, as `burro-release build-synthetic --gritty a` builds it, and is
    never committed. The website is built on one release at a time, so its form and its
    areas are recorded again for this one.
    """
    variant = GrittyVariant.A
    release = build_synthetic(release_id=RELEASE_IDS[variant], gritty_variant=variant)
    client = TestClient(create_app(make_deps(release=release)))
    meta = rec.call(
        client,
        "variant-a/meta",
        "The form of a release where gritty is built from land use alone",
        "get_meta",
    )
    rec.call(client, "variant-a/areas", "Its areas, and their bands", "list_areas")
    read = rec.call(
        client,
        "variant-a/interpret-gritty",
        "A word with two meanings: read as its place part, quoted, and the rest said to be unmet",
        "interpret",
        {"text": PLAIN[2][1], "spec": meta["data"]["defaults"]["rent"]},
    )
    spec = read["data"]["spec"]
    rec.call(client, "variant-a/rank-gritty", "Its ranking", "rank", {"spec": spec, "limit": 20})
    rec.call(
        client,
        "variant-a/explanations-gritty",
        "Its reasons",
        "explain_top",
        {"spec": spec, "limit": 5},
    )


# The measures of a first real build, of which this preview is the made-up likeness.
MEASURED = (
    FeatureId.AIR_NO2,
    FeatureId.GREEN_COVER,
    FeatureId.HOMES_DENSITY,
    FeatureId.HOMES_FLATS,
    FeatureId.HOMES_PRE1919,
    FeatureId.NOISE_EXPOSURE,
    FeatureId.PARK_LARGE_PROXIMITY,
    FeatureId.PARK_PROXIMITY,
    FeatureId.ROAD_MAJOR_EXPOSURE,
)
# Shown, and ranked on alone in no search, as a first real build carries it.
SHOWN_ONLY = FeatureId.ROAD_MAJOR_EXPOSURE


def a_preview() -> InMemoryRelease:
    """The committed release as a first real build would hold it. It is made up all the same.

    Its journeys, its places to reach, its stations and its costs are taken out,
    and all but nine of its measures. Every vibe is worked out again from what is
    left, as a builder works it out, so an area has a band only where 60 in 100
    of a recipe is measured. Nothing is taken out by hand, and nothing stands in
    for what is missing.
    """
    found: dict[str, Any] = load_release(SYNTHETIC_FIXTURE).documents()  # pyright: ignore[reportAssignmentType]
    found["manifest.json"].update(preview=True)
    found["manifest.json"]["counts"].update(destinations=0, places=0, stations=0)
    catalogue, features = found["catalogue.json"], found["features.json"]
    catalogue["metrics"] = [
        metric | {"rankable": metric["feature_id"] != SHOWN_ONLY}
        for metric in catalogue["metrics"]
        if metric["feature_id"] in MEASURED
    ]
    features["rows"] = [row for row in features["rows"] if row["feature_id"] in MEASURED]
    areas = found["neighbourhoods.json"]["neighbourhoods"]
    held = {(row["area_id"], row["feature_id"]): row["percentile"] for row in features["rows"]}
    rankable = [area["rankable"] for area in areas]
    rows: list[dict[str, Any]] = []
    for vibe in tags_of(GrittyVariant(found["manifest.json"]["gritty_variant"])):
        raws = [
            tag_raw(vibe.tag_id, {f: held.get((area["area_id"], f)) for f in FeatureId})
            for area in areas
        ]
        scores = percentile_of([raw.raw for raw in raws], rankable)
        bands = band_of([raw.raw for raw in raws], rankable)
        rows += [
            {
                "area_id": area["area_id"],
                "tag_id": vibe.tag_id,
                "raw": raw.raw,
                "score": score,
                "coverage": raw.coverage,
                "band": band,
                "spread_low": band,
                "spread_high": band,
            }
            for area, raw, score, band in zip(areas, raws, scores, bands, strict=True)
        ]
    found["tags.json"]["rows"] = rows
    found["destinations.json"]["destinations"] = []
    found["places.json"]["places"] = []
    found["cost.json"]["rows"] = []
    travel = found["travel.json"]
    travel.update(source_ids=[], as_of=None, destination_ids=[])
    for matrix in ("pt_typical", "pt_just_missed", "cycle", "walk"):
        travel[matrix] = [[] for _ in travel["area_ids"]]
    found["stations.json"].update(source_ids=[], as_of=None, rows=[])
    return parse_release(found)


def record_a_preview(rec: Recorder) -> None:
    """A release that is not finished: no journey, no cost, and a band for three vibes of eleven.

    It is what the website is built on when it is shown a first real build, so
    each state such a build puts the pages in is recorded from it: a word of the
    shelf that no area can be placed on, a budget that cannot be tested, a
    journey with no place to make it to, and an area with no figure for a thing
    that was asked for, which stands below every area that has one.
    """
    client = TestClient(create_app(make_deps(release=a_preview())))
    meta = rec.call(
        client,
        "preview/meta",
        "The form of a preview: what it holds of each recipe, and that it holds no journey or cost",
        "get_meta",
    )
    areas = rec.call(
        client, "preview/areas", "Its areas, and their bands on the three vibes", "list_areas"
    )
    rec.call(client, "preview/geometry", "The outlines of its areas", "get_geometry")
    for area in areas["data"]["areas"][:3]:
        rec.call(
            client,
            f"preview/area-{area['slug']}",
            f"The profile of {area['name']} in a preview: eight vibes cannot place it",
            "get_area",
            id_or_slug=area["slug"],
        )
    renter = meta["data"]["defaults"]["rent"]
    read = rec.call(
        client,
        "preview/interpret-plain",
        "A plain wish for a vibe no area has a band for: named as missing, and the rest applied",
        "interpret",
        {"text": "leafy and quiet", "spec": renter},
    )
    spec = read["data"]["spec"]
    rec.call(
        client,
        "preview/rank-plain",
        "Its ranking, on what the release does hold",
        "rank",
        {"spec": spec, "limit": 20},
    )
    rec.call(
        client,
        "preview/explanations-plain",
        "Its reasons",
        "explain_top",
        {"spec": spec, "limit": 5},
    )
    rec.call(
        client,
        "preview/interpret-home",
        "A budget that cannot be tested: what is said of the home is kept, the amount is missing",
        "interpret",
        {"text": "Buying a terraced house under £450k", "spec": renter},
    )
    rec.call(
        client,
        "preview/interpret-long",
        "A long sentence: what can be answered is offered, and what cannot is named as missing",
        "interpret",
        {
            "text": (
                "We would love somewhere quiet near parks, with some culture about. "
                "My commute should be short, and we could buy for £350k at the very most."
            ),
            "spec": renter,
        },
    )
    rec.call(
        client,
        "preview/interpret-journey",
        "A workplace, where the release names no place: nothing is asked, and it is missing",
        "interpret",
        {"text": "I work at Tollgate Yard", "spec": renter},
    )
    rec.call(
        client,
        "preview/rank-refused-edits",
        "A vibe, a budget and a measure that controls asked for and the release cannot answer",
        "rank",
        {
            "spec": renter,
            "operations": operations(
                budget_ops=[budget_edit(amount=1500)],
                weight_ops=[weight_edit("station_walk", step="up_large")],
                tag_ops=[tag_edit("leafy", step="up_large", toward="high")],
            ),
            "limit": 20,
        },
    )
    period = rec.call(
        client,
        "preview/interpret-period",
        "Two wishes the release can answer, one of them of a measure an area lacks",
        "interpret",
        {"text": "period homes and clean air", "spec": renter},
    )
    rec.call(
        client,
        "preview/rank-lacking",
        "An area with no figure for a thing that was asked for, below every area that has one",
        "rank",
        {"spec": period["data"]["spec"], "limit": 100},
    )
    rec.call(
        client,
        "preview/explanations-lacking",
        "Its reasons: each of the first five has a figure for all that was asked for",
        "explain_top",
        {"spec": period["data"]["spec"], "limit": 5},
    )
    rec.call(
        client,
        "preview/places-search",
        "A search by name in a preview: it names no place to reach, and finds the area",
        "search_places",
        {"q": "alder"},
    )


# The longest journey the estimated searches set, in minutes. Of the made-up areas, some are
# then likely within it, some borderline and some likely beyond.
ESTIMATE_LIMIT = 30


def a_release_that_estimates() -> InMemoryRelease:
    """The committed release as a build of a city holds it before it has read a timetable.

    It names its places and holds no journey time, and says of each area where its homes
    stand: at the point inside it, which is made up as the rest is. So a journey by public
    transport is estimated from distance, and said as a band. It is made up all the same.
    """
    found: dict[str, Any] = load_release(SYNTHETIC_FIXTURE).documents()  # pyright: ignore[reportAssignmentType]
    found["manifest.json"].update(preview=True)
    for area in found["neighbourhoods.json"]["neighbourhoods"]:
        area["homes_at"] = area["centroid"]
    travel = found["travel.json"]
    travel.update(source_ids=[], as_of=None, destination_ids=[])
    for matrix in ("pt_typical", "pt_just_missed", "cycle", "walk"):
        travel[matrix] = [[] for _ in travel["area_ids"]]
    return parse_release(found)


def record_an_estimate(rec: Recorder) -> None:
    """A release that holds no journey time: a journey is estimated, and said to be.

    The committed release holds a time for every journey, so no other recording shows a
    page what an estimate looks like: on a result, in its reasons, in a comparison, where a
    firm limit leaves an area out, and on the page of methods.
    """
    client = TestClient(create_app(make_deps(release=a_release_that_estimates())))
    meta = rec.call(
        client,
        "estimate/meta",
        "The form of a release that holds no journey time: how a journey is estimated",
        "get_meta",
    )
    renter = meta["data"]["defaults"]["rent"]
    spec = renter | {"commutes": [commute(WORKS, ESTIMATE_LIMIT)]}
    ranked = rec.call(
        client,
        "estimate/rank",
        "A journey with a flexible limit: every area is listed, each with one of three bands",
        "rank",
        {"spec": spec, "limit": 100},
    )
    rec.call(
        client,
        "estimate/explanations",
        "Its reasons: a journey is said as a band, and said to be estimated",
        "explain_top",
        {"spec": spec, "limit": 5},
    )
    firm = renter | {"commutes": [commute(WORKS, ESTIMATE_LIMIT, "hard")]}
    rec.call(
        client,
        "estimate/rank-firm",
        "The same journey with a firm limit: only what is likely beyond it is left out",
        "rank",
        {"spec": firm, "limit": 100},
    )
    # One area of each band, by the order of the ranking, which puts the nearest first.
    of_band: dict[str, str] = {}
    for area in ranked["data"]["ranked"]:
        of_band.setdefault(area["legs"][0]["estimate"], area["area_id"])
    rec.call(
        client,
        "estimate/compare",
        "Three areas compared on the firm limit: one of each band, the last of them left out",
        "compare",
        {
            "spec": firm,
            "area_ids": [
                of_band[band] for band in ("likely_within", "borderline", "likely_beyond")
            ],
        },
    )


# What one person types on one visit, in order. Each sentence is made up for the recording.
VISIT = {
    "first": PROMPTS["first"][0],
    "second": SECOND_SENTENCE,
    "place": "and 30 minutes to Pellam",
    "people": "not too many students, and near a park",
    "unread": "What is the best way to learn the piano",
    "slow": "somewhere by the water, honestly",
    "noticed": NOT_PLAIN[0][1],
}
PICKED = "syn-p0017"  # Pellam Exchange, the answer to "which Pellam?"


# What a buyer of the recording of one number has for a flat. Some areas of the made-up city
# are under it and some over, so that both sentences of a budget are recorded.
BUYER_HAS = 455_000


def a_release_of_one_number() -> InMemoryRelease:
    """The committed release with each price as a publisher gives one: one number, no range.

    Every price to buy keeps its median and loses both quartiles, and says that what it
    rests on is not stated. It holds no rent, as a release that is not made up holds
    none: no source gives a rent for an area. It is made up all the same.
    """
    found: dict[str, Any] = load_release(SYNTHETIC_FIXTURE).documents()  # pyright: ignore[reportAssignmentType]
    prices = [row for row in found["cost.json"]["rows"] if row["tenure"] == "buy"]
    for row in prices:
        row.update(lower_quartile=None, upper_quartile=None, confidence="unstated")
    found["cost.json"]["rows"] = prices
    return parse_release(found)


def record_one_number(rec: Recorder) -> None:
    """A release whose prices have no range, as a first real build with a price holds them.

    The committed release holds every cost as a range, so no other recording shows the
    page what a price of one number looks like: on the page of an area, on a result, and
    in the sentence that holds it against a budget.
    """
    client = TestClient(create_app(make_deps(release=a_release_of_one_number())))
    meta = rec.call(client, "one-number/meta", "The form of the release", "get_meta")
    rec.call(
        client,
        "one-number/area",
        "The profile of an area whose prices are one number each, and which has no rent",
        "get_area",
        id_or_slug="farrowmere",
    )
    buyer = meta["data"]["defaults"]["buy"]
    spec = buyer | {
        "budget": buyer["budget"]
        | {"amount": BUYER_HAS, "strictness": "soft", "provenance": "stated"}
    }
    rec.call(
        client,
        "one-number/rank-buyer",
        "A buyer's budget held against the middle price: some areas under it, some over",
        "rank",
        {"spec": spec, "limit": 20},
    )
    rec.call(
        client,
        "one-number/explanations-buyer",
        "Its reasons: the middle price is said to be under the budget, and over it",
        "explain_top",
        {"spec": spec, "limit": 5},
    )


# The first month of the three years a counted price is of, where the last is June 2026.
SOLD_SINCE = "2023-07"
# How many sales a made-up price rests on: some on many, and some on few.
MANY, FEW = 120, 14


def a_release_of_counted_sales() -> InMemoryRelease:
    """The committed release with each price as a build works one out from the sales.

    Every price to buy keeps its median, loses both quartiles, and says how many
    sales it rests on and since when: many for a flat, and few for a detached house.
    It holds no rent. It is made up all the same.
    """
    found: dict[str, Any] = load_release(SYNTHETIC_FIXTURE).documents()  # pyright: ignore[reportAssignmentType]
    prices = [row for row in found["cost.json"]["rows"] if row["tenure"] == "buy"]
    for row in prices:
        few = row["segment"] == "detached"
        row.update(
            lower_quartile=None,
            upper_quartile=None,
            sales=FEW if few else MANY,
            since=SOLD_SINCE,
            confidence="medium" if few else "high",
        )
    found["cost.json"]["rows"] = prices
    return parse_release(found)


def record_counted_sales(rec: Recorder) -> None:
    """A release whose prices are counted from sales, as a build of London holds them.

    Each is one number that says how many sales it rests on. A firm budget leaves an
    area out only where the middle price is far over it, and an area near the line
    says that about half of the homes sold there went for less.
    """
    client = TestClient(create_app(make_deps(release=a_release_of_counted_sales())))
    meta = rec.call(client, "counted/meta", "The form of the release", "get_meta")
    rec.call(
        client,
        "counted/area",
        "The profile of an area whose prices are each the middle of the sales counted",
        "get_area",
        id_or_slug="farrowmere",
    )
    buyer = meta["data"]["defaults"]["buy"]
    spec = buyer | {
        "budget": buyer["budget"]
        | {"amount": BUYER_HAS, "strictness": "hard", "provenance": "stated"}
    }
    rec.call(
        client,
        "counted/rank-firm",
        "A firm budget held against the middle price: an area is left out only where it is "
        "far over, and some that are kept are over it",
        "rank",
        {"spec": spec, "limit": 20},
    )
    rec.call(
        client,
        "counted/explanations-firm",
        "Its reasons: an area over the budget says that about half of the homes sold there "
        "went for less",
        "explain_top",
        {"spec": spec, "limit": 5},
    )


def record_the_income(rec: Recorder, client: TestClient) -> None:
    """Route 14: the household income of one area, which only the page of an area asks for."""
    rec.call(
        client,
        "income",
        "The household income of one area: the estimate, its limits, its year and its source",
        "get_income",
        id_or_slug="foxholt",
    )
    rec.call(
        client,
        "income-none-given",
        "An area the estimates hold no figure for: it says so, and gives none",
        "get_income",
        id_or_slug="otterby-fields",
    )
    rec.call(
        client,
        "income-not-found",
        "A slug the release lacks: 404",
        "get_income",
        id_or_slug="nowhere-at-all",
    )
    off = TestClient(create_app(make_deps(income=None)))
    rec.call(
        off,
        "income-off",
        "A service that serves no household income: 404, and no figure",
        "get_income",
        id_or_slug="foxholt",
    )
    rec.call(off, "meta-no-income", "What route 11 says where none is served", "get_meta")


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
        # The website asks the rules first, which answer at once. No model reads on this
        # visit but at the step that says so, so nothing more is ever pending.
        body = {"text": VISIT[name], "spec": spec, "ask_model": False}
        return step(name, shows, "interpret", body)["data"]

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

    # A model reads, and does not answer. The rules answer at once, and then in its place.
    slow = TestClient(create_app(make_deps(interpreter=ModelThatTimesOut(), model_id="a-model")))
    asked_of = {"text": VISIT["slow"], "spec": defaults["rent"]}
    rec.call(
        slow,
        f"visit/{next(numbered):02d}-slow-at-once",
        "A sentence that is not plain, asked of the rules first: what they offer, at once",
        "interpret",
        asked_of | {"ask_model": False},
    )
    read = rec.call(
        slow,
        f"visit/{next(numbered):02d}-slow",
        "The same, asked of a model that did not answer: the rules' offers, and degraded",
        "interpret",
        asked_of | {"ask_model": True},
    )["data"]
    moved(
        "slow",
        "What the rules offered, chosen: the edits the API gave with the choice",
        read["spec"],
        **read["suggestions"][0]["choices"][0]["operations"],
    )

    # Another day again, begun at the shelf: a word of it added, with nothing typed.
    lively = moved(
        "shelf",
        "A word of the shelf added to the defaults: one edit, and no text",
        defaults["rent"],
        tag_ops=[tag_edit("pace", step="up_large", toward="high")],
    )
    pace = next(tag for tag in lively["spec"]["tags"] if tag["tag_id"] == "pace")

    # The chip of the scale turned: the other end, with the weight it had.
    calm = moved(
        "turned",
        "A scale turned to its other end from its chip",
        lively["spec"],
        tag_ops=[tag_edit("pace", action="set", value=pace["weight"], toward="low")],
    )["spec"]

    # A sentence that is not plain: nothing applied, and nothing ranked until one is chosen.
    noticed = said("noticed", "A sentence that is not plain: what was noticed, and no edit", calm)
    fewer = noticed["suggestions"][0]["choices"][1]
    moved(
        "chosen",
        "One of the things noticed, chosen: the edits the API gave with the choice",
        noticed["spec"],
        **fewer["operations"],
    )


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
    record_the_other_gritty(rec)
    record_a_preview(rec)
    record_one_number(rec)
    record_an_estimate(rec)
    record_counted_sales(rec)
    record_the_examples(rec, client, TestClient(create_app(make_deps(release=a_preview()))))
    record_the_visit(rec, meta["defaults"])
    # From a service of its own, so that it moves the id of no other recording.
    record_the_census(rec, TestClient(create_app(make_deps())))
    record_the_income(rec, TestClient(create_app(make_deps())))
    if not rec.finish():
        sys.stderr.write("Nothing was written. Reword these in record.py, and record again:\n")
        sys.stderr.write("".join(f"  {failure}\n" for failure in rec.failed))
        return 1
    sys.stdout.write(f"Recorded {len(rec.written)} answers in {OUT}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
