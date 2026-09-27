"""What route 1 says of an offer, for a client that takes what is offered and asks nothing.

Two promises of the product rested on a person choosing. Recorded crime counts
only when a person asks for it by name. And some things are offered and never
applied: what counts who lived somewhere, and the share of homes in the higher
council tax bands (ADR 0006, 0013 and 0028). A client that asks nothing reads
two fields of every offer, and keeps both promises without the name of any
measure or vibe: `by_name`, that the person's own words name what the offer
counts, and `only_by_choice`, that what is offered waits for a person.

It is said whoever read the words, the rules or a model. Every sentence here
is made up.
"""

from typing import Any

import pytest
from burro_api import wire
from burro_core.catalogue import COUNTS_RESIDENTS, FEATURES, HOLDS_CRIME, HOLDS_RESIDENTS, TAGS
from burro_core.ids import Dimension, FeatureId, TagId
from burro_core.interpret import NOT_SAID_TO_BE_WANTED
from fastapi.testclient import TestClient

from .support import (
    client_for,
    make_deps,
    model_budget,
    model_commute,
    model_output,
    model_tag,
    model_weight,
    through_the_route,
)

GRITTY = "tag:street_character"
VIOLENCE, BURGLARY = "feature:crime_violence_robbery", "feature:crime_burglary_theft"
BANDS, SELLS_FOR, MIX = (
    "feature:homes_higher_bands",
    "feature:price_median",
    "feature:brand_mix",
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def read(client: TestClient, text: str) -> dict[str, dict[str, Any]]:
    response = client.post("/v1/interpret", json={"text": text})
    assert response.status_code == 200, response.text
    found = response.json()["data"]
    assert not any(found["operations"].values())
    return {offer["target"]: offer for offer in found["suggestions"]}


def test_both_are_fields_of_an_offer_that_a_client_may_pass_over():
    fields = wire.Suggestion.model_fields

    assert fields["by_name"].annotation is bool
    assert fields["only_by_choice"].annotation is bool
    # A client that asks a person, and takes nothing for them, reads an offer as it did.
    assert not fields["by_name"].is_required()
    assert not fields["only_by_choice"].is_required()


@pytest.mark.parametrize(
    ("text", "targets"),
    [
        ("Somewhere gritty, I think", (GRITTY,)),
        ("low crime and leafy, honestly", (VIOLENCE, BURGLARY)),
    ],
)
def test_to_type_the_name_of_what_counts_recorded_crime_is_to_ask_for_it(
    client: TestClient, text: str, targets: tuple[str, ...]
):
    found = read(client, text)

    for target in targets:
        assert found[target]["by_name"] is True, target
        assert found[target]["only_by_choice"] is False, target


@pytest.mark.parametrize(
    ("text", "targets"),
    [
        ("I want somewhere safe", (VIOLENCE, BURGLARY)),
        ("somewhere posh", (GRITTY,)),
        ("somewhere edgy, honestly", (GRITTY,)),
    ],
)
def test_a_word_that_names_no_recorded_crime_leaves_it_to_a_person(
    client: TestClient, text: str, targets: tuple[str, ...]
):
    found = read(client, text)

    for target in targets:
        assert found[target]["by_name"] is False, target
        assert found[target]["only_by_choice"] is True, target


def test_of_a_word_for_a_smart_area_the_higher_bands_wait_and_the_other_readings_do_not(
    client: TestClient,
):
    found = read(client, "somewhere posh")

    assert found[BANDS]["only_by_choice"] is True
    assert found[MIX]["only_by_choice"] is False
    assert found[SELLS_FOR]["only_by_choice"] is False


@pytest.mark.parametrize(
    "text", ["young professionals", "families, honestly", "honestly, people my age"]
)
def test_what_counts_who_lived_somewhere_waits_for_a_person(client: TestClient, text: str):
    found = read(client, text)

    assert found
    assert all(offer["only_by_choice"] is True for offer in found.values())


def counts_what_waits(offer: dict[str, Any], named: bool) -> bool:
    """Whether some way of an offer sets counting what a person alone may add.

    It is worked out from the edits and the catalogue, as a client works it
    out from route 11: who lived somewhere, whatever the words, and recorded
    crime or a measure that is offered and never applied, where they name none.
    """

    def waits(feature_id: FeatureId) -> bool:
        if feature_id in COUNTS_RESIDENTS:
            return True
        crime = FEATURES[feature_id].dimension is Dimension.CRIME
        return (crime or feature_id is FeatureId.HOMES_HIGHER_BANDS) and not named

    parts: list[FeatureId] = []
    for way in offer["choices"]:
        edits = way["operations"]
        parts += [
            FeatureId(edit["feature_id"])
            for edit in edits["weight_ops"]
            if edit["action"] != "remove"
        ]
        parts += [
            term.feature_id
            for edit in edits["tag_ops"]
            if edit["action"] != "remove"
            for term in TAGS[TagId(edit["tag_id"])].terms
        ]
    return any(waits(part) for part in parts)


SENTENCES = [
    "Somewhere gritty, I think",
    "low crime and leafy, honestly",
    "I want somewhere safe",
    "somewhere posh",
    "somewhere affluent, I think",
    "honestly, somewhere up and coming",
    "families and a park, honestly",
    "young professionals",
    "honestly, leafy and quiet with good schools, 30 minutes to Pellam Cross",
    "pubs are so noisy",
    "honestly, renting, about £1,500 a month",
    "a real identity",
    "near a Waitrose, I think",
]


@pytest.mark.parametrize("text", SENTENCES)
def test_no_offer_that_waits_for_nobody_counts_what_a_person_alone_may_add(
    client: TestClient, text: str
):
    found = read(client, text)

    assert found
    for target, offer in found.items():
        if counts_what_waits(offer, offer["by_name"]):
            assert offer["only_by_choice"] is True, target
        elif offer["only_by_choice"]:
            # It waits for what the words say of it, and says so: a nuisance that is
            # only named, a wish that may be somebody else's.
            assert offer["note"].endswith(NOT_SAID_TO_BE_WANTED), target


def test_the_vibe_that_holds_recorded_crime_is_named_by_no_word_but_the_name_of_an_end(
    client: TestClient,
):
    (gritty,) = HOLDS_CRIME
    named = {"gritty": True, "polished": True, "street character": False, "rough": False}
    for word, by_name in named.items():
        offer = read(client, f"honestly, {word}")[f"tag:{gritty}"]
        assert offer["by_name"] is by_name, word
        assert offer["only_by_choice"] is (not by_name), word


# What a model read


def test_a_thing_that_a_model_read_into_words_is_named_by_none_of_them():
    text = "I'd love somewhere with a proper buzz, honestly"
    answer = model_output(tag_ops=[model_tag("pace", toward="high", words="a proper buzz")])

    found = {one["target"]: one for one in through_the_route(answer, text)["suggestions"]}

    assert found["tag:pace"]["read_by"] == "model"
    assert found["tag:pace"]["by_name"] is False
    assert found["tag:pace"]["only_by_choice"] is False


def test_a_thing_that_a_model_read_where_the_words_name_it_is_named():
    text = "what I'm after, honestly, is leafy"
    answer = model_output(tag_ops=[model_tag("leafy", toward="high", words="leafy")])

    found = {one["target"]: one for one in through_the_route(answer, text)["suggestions"]}

    assert found["tag:leafy"]["by_name"] is True
    assert found["tag:leafy"]["only_by_choice"] is False


def test_recorded_crime_that_a_model_read_is_offered_only_where_the_words_name_it():
    text = "honestly, burglary worries me"
    answer = model_output(
        weight_ops=[model_weight("crime_burglary_theft", words="burglary")],
    )

    found = {one["target"]: one for one in through_the_route(answer, text)["suggestions"]}

    assert found[BURGLARY]["by_name"] is True
    assert found[BURGLARY]["only_by_choice"] is False


def test_a_measure_that_waits_for_a_person_waits_whoever_read_the_words():
    text = "I'd want the grander sort of house about, honestly"
    answer = model_output(
        weight_ops=[
            model_weight("homes_higher_bands", direction="more", words="the grander sort of house")
        ],
    )

    found = {one["target"]: one for one in through_the_route(answer, text)["suggestions"]}

    # Whether or not the guard lets a model's reading of it through, none is left to be taken.
    assert all(offer["only_by_choice"] for target, offer in found.items() if target == BANDS)
    residents = {f"tag:{tag_id}" for tag_id in HOLDS_RESIDENTS}
    assert not residents & set(found)


def test_a_journey_and_a_budget_that_a_model_read_are_named_by_what_was_typed():
    text = "honestly I need to be 30 minutes from Pellam Cross and can pay £1,500 a month"
    answer = model_output(
        commute_ops=[
            model_commute(
                destination_text="Pellam Cross",
                max_minutes=30,
                words="30 minutes from Pellam Cross",
            )
        ],
        budget_ops=[model_budget(amount=1500, tenure="rent", words="£1,500 a month")],
    )

    found = {one["target"]: one for one in through_the_route(answer, text)["suggestions"]}

    for target in ("commute", "budget"):
        assert found[target]["by_name"] is True, target
        assert found[target]["only_by_choice"] is False, target


def test_a_journey_to_a_place_that_is_yet_to_be_chosen_is_to_no_place_the_words_name():
    text = "honestly I need to be 30 minutes from Pellam"
    answer = model_output(
        commute_ops=[
            model_commute(destination_text="Pellam", max_minutes=30, words="30 minutes from Pellam")
        ],
    )

    found = [one for one in through_the_route(answer, text)["suggestions"] if one["asks_place"]]

    assert found
    assert all(offer["by_name"] is False for offer in found)
