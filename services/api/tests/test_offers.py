"""What "add all" may add at one press, and the ways code makes for each thing.

"Add all" presses for the person, so it takes less than a person may. It
adds a wish or a vibe at a mention or a small step, the tenure, a budget as
a guide, and a journey as a guide to a place named in full. It never adds
what leaves areas out, what runs two ways with no guess, a journey to a
place that is yet to be chosen, or recorded crime.
"""

from typing import Any

import pytest
from burro_api.offers import FIRM, GUIDE, LESS, MORE, OFF, Degree, changes, ways_of
from burro_core.catalogue import FEATURES, HOLDS_CRIME, TAGS
from burro_core.ids import Dimension, FeatureId, Polarity, TagId, TagShape
from burro_core.reducer import apply
from fastapi.testclient import TestClient

from .support import (
    UNREAD_FIRST,
    answers_on_disk,
    client_for,
    make_deps,
    model_budget,
    model_commute,
    model_output,
    model_tag,
    model_weight,
    release,
    renter,
    served_again,
    through_the_route,
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def taken(found: dict[str, Any]) -> list[dict[str, Any]]:
    """Every way that "add all" would take of an answer."""
    return [
        way
        for offer in found["suggestions"]
        for way in offer["choices"]
        if offer["add_all"] and way["id"] == offer["add_all"]
    ]


def every_answer() -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    for (case, look), row in answers_on_disk().items():
        if "output" in row:
            found.append((f"{case} look {look}", served_again(case, look)[0]))
    return found


EVERY_ANSWER = every_answer()


# --- What it never adds --------------------------------------------------------------------


def test_add_all_never_adds_what_leaves_areas_out():
    for case, found in EVERY_ANSWER:
        for way in taken(found):
            edits = way["operations"]
            firm = [e for e in (*edits["budget_ops"], *edits["commute_ops"])]
            assert not [edit for edit in firm if edit["strictness"] == "hard"], case
            assert edits["area_ops"] == [], case


def test_add_all_never_adds_recorded_crime():
    for case, found in EVERY_ANSWER:
        for way in taken(found):
            for wish in way["operations"]["weight_ops"]:
                assert FEATURES[FeatureId(wish["feature_id"])].dimension is not Dimension.CRIME
            for tag in way["operations"]["tag_ops"]:
                assert TagId(tag["tag_id"]) not in HOLDS_CRIME, case


def test_add_all_never_adds_a_thing_that_runs_two_ways_with_no_guess():
    for case, found in EVERY_ANSWER:
        for offer in found["suggestions"]:
            ways = [way for way in offer["choices"] if way["id"] != "ignore"]
            if offer["add_all"] and len(ways) > 1:
                assert any(way["guess"] for way in ways), case


def test_add_all_never_adds_a_journey_to_a_place_that_is_yet_to_be_chosen():
    for case, found in EVERY_ANSWER:
        for offer in found["suggestions"]:
            assert not (offer["asks_place"] and offer["add_all"]), case
        for way in taken(found):
            assert all(edit["place_id"] for edit in way["operations"]["commute_ops"]), case


def test_add_all_never_sets_a_number_for_a_weight():
    for case, found in EVERY_ANSWER:
        for way in taken(found):
            wishes = (*way["operations"]["weight_ops"], *way["operations"]["tag_ops"])
            assert {wish["action"] for wish in wishes} <= {"nudge"}, case
            assert {wish["step"] for wish in wishes} <= {"up_small", "up_large"}, case


def test_once_a_model_has_read_add_all_takes_what_burro_guesses_and_no_more():
    # "schools are irrelevant": the rules notice schools, and the model read
    # nothing of them. What was only noticed is for the person.
    found, _ = served_again("long-013")

    for offer in found["suggestions"]:
        if offer["add_all"]:
            assert any(way["guess"] for way in offer["choices"]), offer["target"]
    schools = [o for o in found["suggestions"] if o["target"].startswith("feature:school")]
    assert schools and all(offer["add_all"] == "" for offer in schools)


@pytest.mark.parametrize(
    "text",
    [
        "schools are irrelevant to us",
        "I like noise",
        "she wants a park",
        "maybe a park",
        "I used to want somewhere leafy",
        "30 minutes to Pellam Cross by bike is too long",
    ],
)
def test_the_rules_alone_add_nothing_at_one_press_that_stands_in_doubt(
    client: TestClient, text: str
):
    found = client.post("/v1/interpret", json={"text": text}).json()["data"]

    assert found["suggestions"] and taken(found) == []


# --- What it adds ----------------------------------------------------------------------------


def test_where_the_guess_is_a_firm_limit_add_all_adds_the_guide():
    found, _ = served_again("own-003", before=UNREAD_FIRST)

    [journey] = found["suggestions"]
    assert [way["id"] for way in journey["choices"] if way["guess"]] == [FIRM]
    assert journey["add_all"] == GUIDE
    assert journey["needs"] == "the journey can be made a firm limit"


def test_add_all_adds_a_wish_a_vibe_the_tenure_a_budget_and_a_journey():
    text = (
        "Honestly somewhere quiet near a park, up to \N{POUND SIGN}1,700 a month to rent, "
        "and 30 minutes to Foxholt Market"
    )
    answer = model_output(
        budget_ops=[
            model_budget(tenure="rent", amount=1700, words="up to \N{POUND SIGN}1,700 a month")
        ],
        commute_ops=[
            model_commute(
                destination_text="Foxholt Market",
                max_minutes=30,
                words="30 minutes to Foxholt Market",
            )
        ],
        weight_ops=[model_weight("park_proximity", words="near a park")],
        tag_ops=[model_tag("quiet_residential", words="somewhere quiet")],
    )

    found = through_the_route(answer, text)

    added = {offer["target"]: offer["add_all"] for offer in found["suggestions"]}
    assert added == {
        "tag:quiet_residential": MORE,
        "feature:park_proximity": MORE,
        "budget": GUIDE,
        "commute": GUIDE,
    }
    # Every way it takes is one the reducer applies, and none is turned away.
    spec = renter()
    for way in taken(found):
        body = {"spec": found["spec"], "operations": way["operations"], "limit": 1}
        ranked = client_for(make_deps()).post("/v1/rank", json=body).json()["data"]
        assert ranked["rejected"] == [] and ranked["applied"][0]["changed"]
    assert spec == renter()


def test_what_is_left_for_the_person_is_said_of_each_offer_that_is_not_added():
    for case, found in EVERY_ANSWER:
        for offer in found["suggestions"]:
            ways = [way for way in offer["choices"] if way["id"] != "ignore"]
            if ways and not offer["add_all"]:
                assert offer["needs"], (case, offer["target"])


def test_the_rules_alone_add_a_thing_there_is_one_way_to_want(client: TestClient):
    found = client.post("/v1/interpret", json={"text": "somewhere quiet, honestly"})

    [quiet] = found.json()["data"]["suggestions"]
    assert quiet["add_all"] == MORE and quiet["needs"] == ""


# --- The ways code makes for each thing -----------------------------------------------------


def test_a_thing_that_runs_two_ways_has_both_and_a_thing_that_runs_one_has_that_and_off():
    for feature_id, feature in FEATURES.items():
        ids = [way.id for way in ways_of(feature_id)]
        if feature.polarity is Polarity.EITHER:
            assert ids == [MORE, LESS]
        else:
            assert len(ids) == 2 and ids[1] == OFF
    for tag_id, tag in TAGS.items():
        ids = [way.id for way in ways_of(tag_id)]
        assert ids == ([MORE, LESS, OFF] if tag.shape is TagShape.SCALE else [MORE, OFF])


@pytest.mark.parametrize("degree", list(Degree))
def test_every_way_is_an_edit_a_control_could_send_and_never_a_reading(degree: Degree):
    for thing in (*FEATURES, *(vibe.tag_id for vibe in release().vibes)):
        for way in ways_of(thing, degree):
            edits = [*way.operations.weight_ops, *way.operations.tag_ops]
            assert [edit.provenance for edit in edits] == ["ui_edit"]
            result = apply(renter(), way.operations, release())
            # None is turned away for what it holds. One may have nothing to change.
            assert {r.reason.value for r in result.rejected} <= {"not_in_release"}


def test_a_way_that_would_change_nothing_is_no_way_of_an_offer():
    station_off = next(way for way in ways_of(FeatureId.STATION_WALK) if way.id == OFF)
    pubs_off = next(way for way in ways_of(FeatureId.CULTURE_VENUES) if way.id == OFF)

    # A renter's search counts the walk to a station, since nobody chose. It counts no culture.
    assert changes(station_off, renter(), release())
    assert not changes(pubs_off, renter(), release())
