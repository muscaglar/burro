"""The service on a preview: a release with areas, outlines and a few measures, and no more.

The release here is the committed synthetic one with its journeys, its places
to reach, its stations and its costs taken out, and all but five of its
measures. It is made up, and describes no real place. It is shaped as the first
real build is: what that build has not measured is not in it, and nothing
stands in for what is missing.
"""

from functools import cache
from typing import Any, cast

import pytest
from burro_api.routes.common import default_for
from burro_core import ENGINE_VERSION
from burro_core.catalogue import band_of, percentile_of, tag_raw, tags_of
from burro_core.ids import Direction, FeatureId, GrittyVariant, Provenance, TagId, Tenure
from burro_core.interpret import InterpretRequest
from burro_core.ops import NO_OPERATIONS
from burro_core.reducer import apply
from burro_core.release import InMemoryRelease, parse_release
from burro_core.spec import FeatureWeight, PreferenceSpec, TagWeight
from fastapi.testclient import TestClient

from .support import (
    WORKS,
    FakeModelClient,
    budget,
    client_for,
    commute,
    make_deps,
    model_output,
    model_tag,
    model_weight,
    offers,
    reader_asking,
    release,
    resting_on,
    wire,
)

# The five measures of the first real build.
MEASURED = (
    FeatureId.AIR_NO2,
    FeatureId.HOMES_DENSITY,
    FeatureId.HOMES_FLATS,
    FeatureId.HOMES_PRE1919,
    FeatureId.NOISE_EXPOSURE,
)
MATRICES = ("pt_typical", "pt_just_missed", "cycle", "walk")
AREA = "syn-n0001"


def _tags(
    features: list[dict[str, Any]], areas: list[dict[str, Any]], variant: GrittyVariant
) -> list[dict[str, Any]]:
    """The vibes of a release that holds these features, worked out as core works them out."""
    held = {(row["area_id"], row["feature_id"]): row["percentile"] for row in features}
    rankable = [area["rankable"] for area in areas]
    rows: list[dict[str, Any]] = []
    for vibe in tags_of(variant):
        found = [
            tag_raw(
                vibe.tag_id,
                {feature: held.get((area["area_id"], feature)) for feature in FeatureId},
            )
            for area in areas
        ]
        scores = percentile_of([one.raw for one in found], rankable)
        bands = band_of([one.raw for one in found], rankable)
        rows += [
            {
                "area_id": area["area_id"],
                "tag_id": vibe.tag_id,
                "raw": one.raw,
                "score": score,
                "coverage": one.coverage,
                "band": band,
                "spread_low": band,
                "spread_high": band,
            }
            for area, one, score, band in zip(areas, found, scores, bands, strict=True)
        ]
    return rows


@cache
def preview() -> InMemoryRelease:
    found = cast(dict[str, Any], release().documents())
    found["manifest.json"].update(preview=True)
    # The counts are written from the rows when a release is written, and are not read back.
    found["manifest.json"]["counts"].update(destinations=0, places=0, stations=0)
    catalogue, features = found["catalogue.json"], found["features.json"]
    catalogue["metrics"] = [m for m in catalogue["metrics"] if m["feature_id"] in MEASURED]
    features["rows"] = [row for row in features["rows"] if row["feature_id"] in MEASURED]
    found["tags.json"]["rows"] = _tags(
        features["rows"],
        found["neighbourhoods.json"]["neighbourhoods"],
        GrittyVariant(found["manifest.json"]["gritty_variant"]),
    )
    found["destinations.json"]["destinations"] = []
    found["places.json"]["places"] = []
    found["cost.json"]["rows"] = []
    travel = found["travel.json"]
    travel.update(source_ids=[], as_of=None, destination_ids=[])
    for matrix in MATRICES:
        travel[matrix] = [[] for _ in travel["area_ids"]]
    found["stations.json"].update(source_ids=[], as_of=None, rows=[])
    return parse_release(found)


def renter(**changes: Any) -> PreferenceSpec:
    """The default the service serves for this release: it weighs only what is measured."""
    return default_for(preview(), Tenure.RENT).replace(**changes)


def vibe(tag_id: TagId) -> TagWeight:
    return TagWeight(tag_id=tag_id, weight=0.5, provenance=Provenance.STATED)


@pytest.fixture
def client() -> TestClient:
    return client_for(make_deps(release=preview()))


def data(response: Any) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_a_preview_places_an_area_on_a_vibe_only_where_enough_of_its_recipe_is_measured():
    """Nothing was taken out by hand: five measures are 60 in 100 of one recipe, and of no other.

    Flats and homes per hectare are 75 in 100 of Homes. No other vibe has a band.
    """
    placed = [row for row in preview().tags if row.score is not None]
    assert {row.tag_id for row in placed} == {TagId.HOMES}
    assert {row.coverage for row in placed} == {0.75}
    assert all(row.band is not None for row in placed)
    for row in preview().tags:
        if row.score is None:
            assert (row.raw, row.band, row.spread_low, row.spread_high) == (None,) * 4
            assert row.coverage < 0.6


def test_a_vibe_on_part_of_its_recipe_says_how_much_and_any_other_says_it_cannot_be_placed(
    client: TestClient,
):
    profile = data(client.get(f"/v1/areas/{AREA}"))
    vibes = {fact["fact_id"]: fact for fact in profile["facts"] if fact["kind"] == "tag"}
    assert len(vibes) == 14
    homes = vibes.pop(f"{AREA}/tag/homes")
    assert homes["template"] == "vibe"
    assert homes["slots"]["partly"] == "Worked out from 2 of its 3 parts, 75 of 100 by weight."
    # It cites what its two parts cite, and is dated as they are: never the day it was built.
    assert homes["sources"] and homes["as_of"] == homes["slots"]["span"]
    for fact in vibes.values():
        assert fact["template"] == "vibe_unknown"
        assert set(fact["slots"]) == {"label", "name", "known", "parts"}
        assert int(fact["slots"]["known"]) < int(fact["slots"]["parts"])
    # The map is coloured by a vibe only where an area is placed on it.
    bands = {row["tag_id"]: row["marks"] for row in data(client.get("/v1/areas"))["bands"]}
    assert [vibe for vibe, marks in bands.items() if any(m["band"] for m in marks)] == ["homes"]


def test_every_answer_of_a_preview_says_that_it_is_one(client: TestClient):
    wished = wire(renter())
    answered = [
        client.get("/v1/meta"),
        client.get("/v1/areas"),
        client.get("/v1/areas/geometry"),
        client.get(f"/v1/areas/{AREA}"),
        client.post("/v1/rank", json={"spec": wished}),
        client.post("/v1/explanations", json={"spec": wished}),
        client.post("/v1/compare", json={"area_ids": [AREA, "syn-n0002"], "spec": wished}),
        client.post("/v1/places/search", json={"q": "anywhere"}),
        client.post("/v1/interpret", json={"text": "fewer flats"}),
        client.post("/v1/shares", json={"spec": wished}),
    ]
    refused = [
        client.get("/v1/areas/nowhere"),
        client.post("/v1/rank", json={"spec": "no"}),
        client.post("/v1/rank", json={"spec": wire(renter(commutes=(commute(),)))}),
    ]
    assert [r.status_code for r in answered] == [200] * len(answered)
    assert [r.status_code for r in refused] == [404, 422, 422]
    for response in (*answered, *refused):
        assert response.headers["x-burro-preview"] == "true"
        assert response.json()["meta"] == {
            "release_id": "syn-2026-09-23-01",
            "engine_version": ENGINE_VERSION,
            "synthetic": True,
            "preview": True,
        }
    assert client.get("/healthz").headers["x-burro-preview"] == "true"
    # An answer that stands has no body, and says so in its header.
    stands = client.get("/v1/areas", headers={"if-none-match": '"syn-2026-09-23-01"'})
    assert (stands.status_code, stands.headers["x-burro-preview"]) == (304, "true")


def test_what_a_preview_has_not_measured_is_not_there_and_nothing_stands_in_for_it(
    client: TestClient,
):
    meta = data(client.get("/v1/meta"))
    assert meta["preview"] is True
    assert [feature["feature_id"] for feature in meta["features"]] == sorted(MEASURED)
    counts = meta["counts"]
    assert (counts["destinations"], counts["places"], counts["stations"]) == (0, 0, 0)

    profile = data(client.get(f"/v1/areas/{AREA}"))
    assert (profile["cost"], profile["stations"]) == ([], [])
    assert [tag["tag_id"] for tag in profile["tags"] if tag["band"] is not None] == ["homes"]
    # A vibe has a fact whether or not the area is placed on it, and a likeness is counted
    # from measures. No cost, no journey and no station is said.
    kinds = sorted({fact["kind"] for fact in profile["facts"]})
    assert kinds == ["area", "feature", "likeness", "tag"]
    assert all(fact["sources"] and fact["as_of"] for fact in profile["facts"])
    assert data(client.post("/v1/places/search", json={"q": "anywhere"}))["places"] == []


def test_a_preview_serves_a_default_it_can_rank_and_ranks_on_what_it_measures(client: TestClient):
    defaults = data(client.get("/v1/meta"))["defaults"]
    for tenure in ("rent", "buy"):
        weighed = {weight["feature_id"] for weight in defaults[tenure]["weights"]}
        assert weighed and weighed <= set(MEASURED)
        ranked = data(client.post("/v1/rank", json={"spec": defaults[tenure], "limit": 100}))
        # Every area is ranked, or is said not to be: none is lost for want of a journey.
        every = len(preview().neighbourhoods)
        assert len(ranked["scores"]) + len(ranked["unranked"]) == every
        assert len(ranked["scores"]) > every // 2 and ranked["filtered"] == []


def edits(**groups: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """The six arrays of edits, empty but for those given."""
    names = ("budget_ops", "commute_ops", "weight_ops", "tag_ops", "area_ops", "setting_ops")
    return {name: groups.get(name, []) for name in names}


PARKS = {
    "action": "set",
    "feature_id": "park_proximity",
    "value": 0.5,
    "step": "none",
    "direction": "default",
    "provenance": "ui_edit",
}
LEAFY = {
    "action": "nudge",
    "tag_id": "leafy",
    "value": 0.0,
    "step": "up_large",
    "toward": "high",
    "provenance": "ui_edit",
}
A_BUDGET = {
    "action": "set",
    "tenure": "unchanged",
    "amount": 1800,
    "segment": "unchanged",
    "strictness": "unchanged",
    "step": "none",
    "provenance": "ui_edit",
}
A_JOURNEY = {
    "action": "add",
    "place_id": WORKS,
    "mode": "unchanged",
    "max_minutes": 30,
    "strictness": "unchanged",
    "step": "none",
    "provenance": "ui_edit",
}


def test_a_wish_a_preview_cannot_meet_is_refused_or_said_to_be_missing(client: TestClient):
    # A measure the preview does not carry, a vibe it places no area on, a budget it
    # holds no cost for and a journey to a place it does not name: none can be asked
    # for. Each edit is turned away, and the ranking stands as it was.
    asked = edits(
        budget_ops=[A_BUDGET], commute_ops=[A_JOURNEY], weight_ops=[PARKS], tag_ops=[LEAFY]
    )
    answered = data(client.post("/v1/rank", json={"spec": wire(renter()), "operations": asked}))
    assert [(edit["group"], edit["reason"]) for edit in answered["rejected"]] == [
        ("budget_ops", "not_in_release"),
        ("commute_ops", "not_in_release"),
        ("weight_ops", "not_in_release"),
        ("tag_ops", "not_in_release"),
    ]
    assert answered["spec"] == wire(renter())
    stands = data(client.post("/v1/rank", json={"spec": wire(renter())}))
    assert answered["scores"] == stands["scores"] and answered["scores"]

    # A search that holds one all the same, as a link made on another release may, is
    # refused with where it stands, and is never answered with a ranking of no area.
    for spec, path, problem in (
        (renter(budget=budget(1800)), "spec.budget.amount", "not_in_release"),
        (renter(tags=(vibe(TagId.LEAFY),)), "spec.tags[0].tag_id", "not_in_release"),
        (renter(commutes=(commute(),)), "spec.commutes[0].place_id", "unknown_place"),
    ):
        refused = client.post("/v1/rank", json={"spec": wire(spec)})
        assert refused.status_code == 422
        assert refused.json()["error"]["fields"] == [{"path": path, "problem": problem}]


def test_what_an_area_of_a_preview_has_no_figure_for_is_said_to_be_missing_and_never_filled_in(
    client: TestClient,
):
    # What the preview measures, and not in every area: it is dropped for the area that
    # lacks it, and what is said of it there is that it is missing. Never a figure.
    homes = tuple(
        FeatureWeight(
            feature_id=feature_id,
            weight=1.0,
            direction=Direction.MORE,
            provenance=Provenance.STATED,
        )
        for feature_id in (FeatureId.HOMES_DENSITY, FeatureId.HOMES_FLATS, FeatureId.HOMES_PRE1919)
    )
    wished = wire(renter(weights=(*renter().weights, *homes)))
    ranked = data(client.post("/v1/rank", json={"spec": wished, "limit": 100}))
    lacking = [
        (area["area_id"], part)
        for area in ranked["ranked"]
        for part in area["contributions"]
        if not part["present"]
    ]
    assert lacking
    for _, part in lacking:
        assert (part["utility"], part["share"], part["contribution"]) == (None, 0.0, 0.0)
    explained = data(client.post("/v1/explanations", json={"spec": wished, "limit": 5}))
    for fact in explained["facts"]:
        if fact["kind"] == "missing":
            assert fact["numbers"] == []


def test_a_preview_says_what_it_holds_of_each_vibe_and_that_it_holds_no_journey_and_no_cost(
    client: TestClient,
):
    meta = data(client.get("/v1/meta"))
    assert meta["holds"] == {"journeys": False, "costs": False}
    recipes = {held["tag_id"]: held for held in meta["recipes"]}
    assert list(recipes) == [vibe["tag_id"] for vibe in meta["tags"]]
    assert [tag_id for tag_id, held in recipes.items() if held["placed"]] == ["homes"]
    assert recipes["homes"] == {
        "tag_id": "homes",
        "held": 75,
        "needed": 60,
        "placed": True,
        "waits_on": [
            {
                "feature_id": "private_outdoor_space",
                "label": "Addresses with private outdoor space",
                "hundredths": 25,
            }
        ],
    }
    # A vibe that places no area says how little of its recipe is held, and names every
    # part it waits on, a part that no release carries yet among them.
    for vibe in meta["tags"]:
        held = recipes[vibe["tag_id"]]
        waited = sum(part["hundredths"] for part in held["waits_on"])
        assert held["held"] + waited == 100
        assert held["placed"] is (held["held"] >= held["needed"])
        assert all(part["label"] for part in held["waits_on"])
    assert recipes["pace"]["held"] == 0 and len(recipes["pace"]["waits_on"]) == 4


def test_a_sentence_on_a_preview_names_what_is_missing_and_ranks_on_the_rest(client: TestClient):
    # "Leafy" was shown as understood, and the list was ranked without it.
    text = "leafy, urban, up to £1,500 a month"
    read = data(client.post("/v1/interpret", json={"text": text}))
    assert read["status"] == "ok"
    assert [
        (thing["target"], thing["label"], [text[s["start"] : s["end"]] for s in thing["spans"]])
        for thing in read["not_in_release"]
    ] == [
        ("budget", "A budget", ["up to £1,500"]),
        ("tag:leafy", "Leafy", ["leafy"]),
    ]
    assert [tag["tag_id"] for tag in read["spec"]["tags"]] == ["homes"]
    assert read["spec"]["budget"]["amount"] is None
    ranked = data(client.post("/v1/rank", json={"spec": read["spec"]}))
    assert ranked["areas_ranked"] > 0

    # In a sentence that is not plain nothing is applied. What can be answered is
    # offered, and what cannot is named and never offered.
    unsure = "My partner wants somewhere urban and leafy, with a short commute."
    noticed = data(client.post("/v1/interpret", json={"text": unsure}))
    assert [found["target"] for found in noticed["suggestions"]] == ["tag:homes"]
    assert [
        (thing["target"], [unsure[s["start"] : s["end"]] for s in thing["spans"]])
        for thing in noticed["not_in_release"]
    ] == [("tag:leafy", ["leafy"]), ("commute", ["commute"])]
    unread = [unsure[span["start"] : span["end"]] for span in noticed["unread"]]
    assert not any("leafy" in words or "commute" in words for words in unread)

    # A place is named in no release of this kind, so nothing is asked about one.
    place = data(client.post("/v1/interpret", json={"text": "I work at Tollgate Yard"}))
    assert (place["status"], place["clarify"]) == ("ok", [])
    assert [thing["target"] for thing in place["not_in_release"]] == ["commute"]


@pytest.mark.parametrize(
    ("words", "read_as"),
    [
        ("verdant", model_output(tag_ops=[model_tag("leafy", words="verdant")])),
        (
            "wet underfoot",
            model_output(weight_ops=[model_weight("water_access", words="wet underfoot")]),
        ),
    ],
)
def test_nothing_a_model_reads_is_offered_where_a_preview_holds_it_for_no_area(
    words: str, read_as: dict[str, Any]
):
    """The rules do not know the words, so a model is asked. What it reads could only be
    turned away, so it is not offered, and the words are said to be unread."""
    text = f"honestly somewhere {words}, I suppose"
    asked = InterpretRequest(text=text, spec=renter(), release=preview())
    result = reader_asking(FakeModelClient(resting_on(read_as, text))).interpret(asked)
    assert (result.operations, offers(result)) == (NO_OPERATIONS, {})
    assert [(span.start, span.end) for span in result.unread] == [(0, len(text))]


def test_what_a_model_reads_is_offered_where_a_preview_holds_it_and_a_press_applies_it():
    text = "honestly somewhere old fashioned, I suppose"
    read_as = model_output(tag_ops=[model_tag("homes", words="old fashioned")])
    asked = InterpretRequest(text=text, spec=renter(), release=preview())
    result = reader_asking(FakeModelClient(resting_on(read_as, text))).interpret(asked)
    assert result.operations == NO_OPERATIONS and list(offers(result)) == ["tag:homes"]
    for way in offers(result)["tag:homes"].choices:
        assert apply(renter(), way.operations, preview()).rejected == ()


def test_a_release_that_holds_everything_says_that_nothing_is_missing():
    whole = client_for(make_deps())
    meta = data(whole.get("/v1/meta"))
    assert meta["holds"] == {"journeys": True, "costs": True}
    assert all(held["placed"] for held in meta["recipes"])
    text = "leafy and quiet, up to £1,500 a month, I work at Cindermoor Works"
    assert data(whole.post("/v1/interpret", json={"text": text}))["not_in_release"] == []
