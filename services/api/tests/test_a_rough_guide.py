"""A vibe that is a rough guide, as the service serves it.

The founder decided on 2026-09-25 that Village feel is served though it did
not reach the bar they had set, and that it says it is less sure than the
other vibes (ADR 0013, as amended). Route 11 says which vibe is one, with the
label and the sentence that every surface draws. It is never taken without a
press of its own: the rules apply it from no word, one press that adds what
needs no choice never takes it, and a model's guess of it is no guess.

Every area here is made up.
"""

from typing import Any

import pytest
from burro_api.guard import DOUBTS, Check
from burro_api.offers import MORE, SKIP, Offer, Way, in_add_all, ways_of
from burro_core.catalogue import ROUGH_GUIDES, TAGS, says_rough
from burro_core.ids import InterpreterName, TagId
from burro_core.interpret import Span
from fastapi.testclient import TestClient

from .support import (
    asked,
    client_for,
    guessed,
    make_deps,
    model_output,
    model_tag,
    model_weight,
    offers,
    release,
    renter,
    through_the_route,
    wire,
)

VILLAGE = "tag:village_feel"
SAID = (
    "Rough guide. Of the areas it puts highest, about half read as villages to people, and it "
    "takes some busy main roads and some grand inner streets for villages."
)


@pytest.fixture
def client() -> TestClient:
    return client_for(make_deps())


def data(response: Any) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    return response.json()["data"]


def offer_of(found: dict[str, Any], target: str = VILLAGE) -> dict[str, Any]:
    (offer,) = [one for one in found["suggestions"] if one["target"] == target]
    return offer


def asking_for(client: TestClient, *tag_ids: str) -> dict[str, Any]:
    """A search that asks for some vibes, each by a press of its own."""
    spec = wire(renter())
    for tag_id in tag_ids:
        (add, *_) = ways_of(TagId(tag_id))
        body = {"spec": spec, "operations": add.operations.model_dump(mode="json"), "limit": 24}
        spec = data(client.post("/v1/rank", json=body))["spec"]
    return spec


# What route 11 says


def test_route_11_says_which_vibe_is_a_rough_guide_with_its_label_and_its_sentence(
    client: TestClient,
):
    found = data(client.get("/v1/meta"))
    assert found["rough_guides"] == [
        {
            "tag_id": "village_feel",
            "label": "Rough guide",
            "why": (
                "Of the areas it puts highest, about half read as villages to people, and it "
                "takes some busy main roads and some grand inner streets for villages."
            ),
        }
    ]
    said = {tag["tag_id"]: tag["sureness"] for tag in found["tags"]}
    assert said.pop("village_feel") == "rough_guide"
    assert set(said.values()) == {"as_the_rest"} and len(said) == 13
    assert says_rough(TagId.VILLAGE_FEEL) == SAID


def test_the_recipe_is_the_one_the_founder_chose_and_the_vibe_is_placed(client: TestClient):
    found = data(client.get("/v1/meta"))
    (village,) = [tag for tag in found["tags"] if tag["tag_id"] == "village_feel"]
    assert [
        (term["hundredths"], term["feature_id"], term["reading"]) for term in village["terms"]
    ] == [
        (45, "highstreet_conserved", "high"),
        (30, "homes_density", "low"),
        (15, "homes_pre1919", "high"),
        (10, "conservation_cover", "high"),
    ]
    (recipe,) = [one for one in found["recipes"] if one["tag_id"] == "village_feel"]
    assert (recipe["placed"], recipe["held"], recipe["waits_on"]) == (True, 100, [])


# It is never taken without a press of its own


@pytest.mark.parametrize("text", ["villagey", "a village feel", "I like villages"])
def test_the_rules_apply_it_from_no_word_and_offer_it_with_its_label_and_its_sentence(
    client: TestClient, text: str
):
    found = data(client.post("/v1/interpret", json={"text": text}))
    assert (found["status"], found["interpreter"]) == ("suggest", "rule")
    assert found["applied"] == [] and found["spec"]["tags"] == []
    offer = offer_of(found)
    assert (offer["label"], offer["does"], offer["note"]) == (
        "Village feel",
        "Add Village feel.",
        SAID,
    )
    assert [(way["id"], way["label"], way["guess"]) for way in offer["choices"]] == [
        ("more", "Add", False),
        ("ignore", "Skip", False),
    ]
    # One press of its own adds it, and the search then holds it.
    pressed = {"spec": found["spec"], "operations": offer["choices"][0]["operations"]}
    ranked = data(client.post("/v1/rank", json=pressed))
    assert [tag["tag_id"] for tag in ranked["spec"]["tags"]] == ["village_feel"]


def test_one_press_that_adds_what_needs_no_choice_never_takes_it(client: TestClient):
    found = data(client.post("/v1/interpret", json={"text": "leafy, quiet streets, villagey"}))
    assert found["applied"] == []
    taken = {one["target"]: one["add_all"] for one in found["suggestions"]}
    assert taken == {"tag:leafy": "more", "tag:quiet_residential": "more", VILLAGE: ""}
    # What is left for the person is said by its name.
    assert offer_of(found)["needs"] == "Village feel"
    # The press sends the way of each offer that it takes, and no other.
    spec = found["spec"]
    for one in found["suggestions"]:
        for way in one["choices"]:
            if one["add_all"] and way["id"] == one["add_all"]:
                body = {"spec": spec, "operations": way["operations"]}
                spec = data(client.post("/v1/rank", json=body))["spec"]
    assert sorted(tag["tag_id"] for tag in spec["tags"]) == ["leafy", "quiet_residential"]
    assert "village_feel" not in str(spec)


def _offer(ways: tuple[Way, ...], **said: Any) -> Offer:
    return Offer(
        target=VILLAGE,
        label="Village feel",
        spans=(Span(start=0, end=8),),
        choices=(*ways, SKIP),
        **said,
    )


def test_one_press_takes_no_rough_guide_whatever_else_is_said_of_its_offer():
    """It is not the note that keeps it out, and not the want of a guess."""
    (add, _) = ways_of(TagId.VILLAGE_FEEL)
    assert in_add_all(_offer((add,))) is None
    assert in_add_all(_offer((add.replace(guess=True),))) is None
    assert in_add_all(_offer((add.replace(ruled=True),), note=SAID)) is None
    assert in_add_all(_offer((add.replace(guess=True),), read_by=InterpreterName.MODEL)) is None
    # A vibe that is as sure as the rest is taken as it was.
    (leafy, _) = ways_of(TagId.LEAFY)
    taken = in_add_all(Offer(target="tag:leafy", label="Leafy", spans=(), choices=(leafy, SKIP)))
    assert taken is not None and taken.id == MORE


# A model's guess of it is no guess


def test_the_check_takes_the_guess_away_and_leaves_the_thing_offered():
    assert Check.ROUGH in DOUBTS
    assert Check.ROUGH.value == "a_rough_guide_is_taken_by_a_press_of_its_own"


@pytest.mark.parametrize(
    ("text", "words"),
    [
        ("a small-town feel, honestly", "a small-town feel"),
        ("somewhere quaint with a green, honestly", "quaint with a green"),
    ],
)
def test_a_models_guess_of_a_rough_guide_is_no_guess(text: str, words: str):
    answer = model_output(tag_ops=[model_tag("village_feel", words=words)])

    result, client = asked(answer, text=text)

    assert client.calls, "the rules read no such words, so the model was asked"
    offer = offers(result)[VILLAGE]
    assert guessed(result) == {}
    assert [(way.id, way.guess) for way in offer.choices] == [("more", False), ("ignore", False)]
    assert (offer.read_by, offer.note, offer.alone) == (InterpreterName.MODEL, SAID, True)
    assert in_add_all(offer) is None
    assert result.operations.tag_ops == () and result.operations.weight_ops == ()


def test_a_model_that_would_set_it_above_all_makes_no_guess_either():
    answer = model_output(
        tag_ops=[model_tag("village_feel", action="set", value=1.0, step="none", words="quaint")]
    )
    result, _ = asked(answer, text="it must be quaint, honestly")
    assert guessed(result) == {}
    assert offers(result)[VILLAGE].note == SAID


def test_as_the_route_serves_it_the_offer_of_a_model_holds_the_label_and_the_sentence():
    answer = model_output(tag_ops=[model_tag("village_feel", words="a small-town feel")])
    found = through_the_route(answer, "a small-town feel, honestly")
    offer = offer_of(found)
    assert (offer["label"], offer["note"], offer["add_all"], offer["read_by"]) == (
        "Village feel",
        SAID,
        "",
        "model",
    )
    assert not [way for way in offer["choices"] if way["guess"]]
    assert found["applied"] == [] and found["spec"]["tags"] == []


def test_a_model_that_reads_it_in_the_words_of_another_thing_makes_an_offer_of_its_own():
    """Two things a model reads in the same words are one offer with both as choices. A
    rough guide is never a choice of another thing's offer: it has an offer of its own,
    which says what it is."""
    text = "near a park, I suppose"
    answer = model_output(
        weight_ops=[model_weight("park_proximity", words="near a park")],
        tag_ops=[model_tag("village_feel", words="near a park")],
    )
    result, _ = asked(answer, text=text)
    found = offers(result)
    assert set(found) == {"feature:park_proximity", VILLAGE}
    park, village = found["feature:park_proximity"], found[VILLAGE]
    assert not [way for way in park.choices if "village_feel" in way.id]
    assert not [edit for way in park.choices for edit in way.operations.tag_ops]
    assert village.note == SAID and not [way for way in village.choices if way.guess]


def test_where_the_rules_offer_it_a_model_adds_nothing_to_the_offer():
    """The rules offer it with what it says of itself, so the thing is theirs to offer."""
    text = "villagey, I suppose"
    answer = model_output(tag_ops=[model_tag("village_feel", words="villagey")])
    result, _ = asked(answer, text=text)
    offer = offers(result)[VILLAGE]
    assert guessed(result) == {}
    assert (offer.read_by, offer.note) == (InterpreterName.RULE, SAID)
    assert in_add_all(offer) is None


def test_to_turn_it_away_takes_it_off_a_search_that_holds_it(client: TestClient):
    """To turn it away is no wish for it, and is read as it is of any vibe."""
    held = asking_for(client, "village_feel")
    assert [tag["tag_id"] for tag in held["tags"]] == ["village_feel"]
    found = data(client.post("/v1/interpret", json={"text": "not villagey", "spec": held}))
    assert found["status"] == "ok"
    assert [(edit["tag_id"], edit["action"]) for edit in found["operations"]["tag_ops"]] == [
        ("village_feel", "remove")
    ]
    assert [tag for tag in found["spec"]["tags"] if tag["weight"] > 0] == []
    # And it adds it to no search that does not.
    bare = data(client.post("/v1/interpret", json={"text": "not villagey"}))
    assert [tag for tag in bare["spec"]["tags"] if tag["weight"] > 0] == []


# It is used to work out no other thing


def test_no_result_shows_it_and_no_explanation_gives_it_as_a_reason_unless_it_was_asked_for(
    client: TestClient,
):
    for spec in (wire(renter()), asking_for(client, "leafy")):
        ranked = data(client.post("/v1/rank", json={"spec": spec, "limit": 24}))
        shown = {mark["tag_id"] for area in ranked["ranked"] for mark in area["strip"]}
        assert "village_feel" not in shown
        told = data(client.post("/v1/explanations", json={"spec": spec, "limit": 5}))
        assert "village_feel" not in str(told) and "Village feel" not in str(told)


def test_asked_for_it_is_on_a_result_and_may_be_given_as_a_reason(client: TestClient):
    spec = asking_for(client, "village_feel")
    ranked = data(client.post("/v1/rank", json={"spec": spec, "limit": 24}))
    first = ranked["ranked"][0]
    (mark,) = [mark for mark in first["strip"] if mark["tag_id"] == "village_feel"]
    assert mark["asked"] is True
    names = {area["area_id"]: area["name"] for area in data(client.get("/v1/areas"))["areas"]}
    # A made-up village comes first. It describes no real place.
    assert names[first["area_id"]] in ("Thrushcombe", "Wickerford")
    told = data(client.post("/v1/explanations", json={"spec": spec, "limit": 5}))
    assert "village_feel" in str(told)


def test_no_likeness_is_counted_on_the_measure_that_was_made_for_it(client: TestClient):
    found = data(client.get("/v1/meta"))
    (street,) = [one for one in found["features"] if one["feature_id"] == "highstreet_conserved"]
    assert street["in_likeness"] is False
    area = data(client.get("/v1/areas/thrushcombe"))
    for like in area["similar"]:
        assert "highstreet_conserved" not in str(like) and "village_feel" not in str(like)


def test_an_area_page_holds_its_band_and_no_list_of_what_the_area_has_most_of_holds_it(
    client: TestClient,
):
    area = data(client.get("/v1/areas/thrushcombe"))
    (row,) = [tag for tag in area["tags"] if tag["tag_id"] == "village_feel"]
    assert row["band"] == 5
    portrait = area["portrait"]
    listed = {mark["tag_id"] for mark in (*portrait["more"], *portrait["less"])}
    assert "village_feel" not in listed
    assert "village_feel" in {mark["tag_id"] for mark in portrait["others"]}


def test_the_made_up_release_places_it_so_that_every_surface_can_be_judged():
    assert set(ROUGH_GUIDES) == {TagId.VILLAGE_FEEL}
    assert release().placed(TagId.VILLAGE_FEEL)
    village = TAGS[TagId.VILLAGE_FEEL]
    assert (village.strip, village.lens, village.table) == (False, True, True)
