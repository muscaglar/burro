"""How an offer is worded, as route 1 serves it (contract, section 8.2).

Every offer has four parts: what it would do, the person's own words, what
follows for areas, and the choices. The words are the API's, so that the
website and the iPhone app show the same. The person's words are in none of
them: a client cuts them from the text it holds, by where they stand.
"""

import json
import re
from typing import Any

import pytest
from burro_api.wording import NO_JOURNEY, NO_LEAST, NOTHING_TAKEN
from burro_core.catalogue import FEATURES, TAGS
from burro_core.facts import SEGMENT_LABELS, money
from burro_core.ids import Segment
from fastapi.testclient import TestClient

from .support import (
    CANARY,
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
    served_again,
    through_the_route,
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def offered(client: TestClient, text: str) -> list[dict[str, Any]]:
    response = client.post("/v1/interpret", json={"text": text})
    assert response.status_code == 200
    return response.json()["data"]["suggestions"]


def by_target(found: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {offer["target"]: offer for offer in found}


def buttons(offer: dict[str, Any]) -> list[str]:
    return [way["label"] for way in offer["choices"]]


def wrote(offer: dict[str, Any], text: str) -> str:
    return text[offer["shown"]["start"] : offer["shown"]["end"]]


# --- The four parts ------------------------------------------------------------------------------


def test_a_journey_says_where_how_long_and_how_and_what_each_way_does_to_areas():
    found, text = served_again("own-003", before=UNREAD_FIRST)

    [journey] = found["suggestions"]
    assert journey["does"] == (
        "Add a journey to Foxholt Market: at most 40 minutes, by public transport."
    )
    assert wrote(journey, text) == "At most 35-40min commute from Foxholt Market"
    assert journey["said"] == [
        "You gave 35 to 40: Burro took 40.",
        "You named no way of travelling: Burro took public transport.",
    ]
    assert buttons(journey) == [
        "Add as a firm limit: areas further off are left out",
        "Add as a guide: areas further off rank lower",
        "Skip",
    ]
    assert [way["guess"] for way in journey["choices"]] == [True, False, False]
    assert journey["follows"] == "Areas further off are left out."


def test_a_budget_says_the_amount_the_tenure_and_the_home_and_is_firm_where_the_words_say_max():
    found, text = served_again("own-021")

    budget = by_target(found["suggestions"])["budget"]
    assert budget["does"] == (
        "Set a budget of \N{POUND SIGN}1,900 a month to rent a 1-bedroom home, as a firm limit."
    )
    assert wrote(budget, text) == "If I'm renting, max \N{POUND SIGN}1,900 a month for a 1 bed flat"
    assert budget["follows"] == "Dearer areas are left out."
    assert buttons(budget) == [
        "Set as a firm limit: dearer areas are left out",
        "Set as a guide: dearer areas rank lower",
        "Skip",
    ]
    assert [way["guess"] for way in budget["choices"]] == [True, False, False]


def test_a_wish_says_what_happens_to_areas_and_what_is_counted():
    found, text = served_again("own-022")

    culture = by_target(found["suggestions"])["feature:culture_venues_per_homes"]
    assert culture["does"] == "Rank areas a little higher for this: more culture nearby."
    assert wrote(culture, text) == "a bit of culture"
    assert culture["follows"] == (
        "What Burro counts: museums, galleries, theatres, cinemas, music venues and libraries "
        "for each 1,000 homes within 800 m, in a straight line."
    )
    assert buttons(culture) == ["Add", "Skip"]


def test_a_vibe_says_what_it_counts_and_what_it_cannot_see():
    found, text = served_again("own-022")

    quiet = by_target(found["suggestions"])["tag:quiet_residential"]
    assert quiet["does"] == "Add Quiet streets."
    assert wrote(quiet, text) == "Quiet but not dead"
    assert quiet["follows"] == (
        "What it counts: homes away from main roads and from clusters of pubs and bars, with "
        "little transport noise. It cannot see: one street or one home. An area is many streets."
    )
    assert buttons(quiet) == ["Add", "Skip"]


def test_an_end_of_a_scale_says_how_the_scale_runs(client: TestClient):
    found, text = served_again("own-008")

    pace = by_target(found["suggestions"])["tag:pace"]
    assert pace["does"] == "Add Going out, towards Buzzy, counted a little."
    assert pace["follows"].startswith("Going out runs from Calm to Buzzy. What it counts: ")
    assert buttons(pace) == ["Towards Buzzy", "Towards Calm", "Skip"]
    assert wrote(pace, text) == "a bit buzzy"
    [named] = offered(client, "pace")
    assert named["does"] == "Going out runs from Calm to Buzzy. Which way?"
    assert not any(way["guess"] for way in named["choices"])


def test_a_wish_turned_round_of_a_thing_that_runs_two_ways_is_fewer_of_it():
    found, _ = served_again("list-040")

    pubs = by_target(found["suggestions"])["feature:venue_evening_per_homes"]
    assert pubs["does"] == "Rank areas higher for this: fewer pubs and bars."
    assert buttons(pubs) == ["More pubs and bars", "Fewer pubs and bars", "Skip"]
    assert [way["guess"] for way in pubs["choices"]] == [False, True, False]


def test_a_wish_turned_round_of_a_thing_that_runs_one_way_stops_counting_it():
    found, text = served_again("neg-032")

    [station] = found["suggestions"]
    assert station["does"] == "Stop counting this: nearer a station."
    assert station["follows"] == (
        "It counts a little now, because nobody chose. "
        "Burro cannot rank an area for the opposite of it."
    )
    assert buttons(station) == ["Add", "Stop counting it", "Skip"]
    assert wrote(station, text) == "a station"


def test_an_area_says_what_is_left_out(client: TestClient):
    [out] = offered(client, "Honestly, not Pellam Cross")
    [either] = offered(client, "I love Cindermoor")

    assert out["does"] == "Leave Pellam Cross out of the results."
    assert out["follows"] == "No area of Pellam Cross is shown."
    assert buttons(out) == ["Leave it out of the results", "Skip"]
    assert either["does"] == "Cindermoor: look only there, or leave it out?"
    assert buttons(either) == ["Look only in Cindermoor", "Leave it out of the results", "Skip"]


def test_a_place_the_release_does_not_hold_is_a_question_that_leads_to_the_place_search():
    found, text = served_again("own-004", before=UNREAD_FIRST)

    [asks] = found["suggestions"]
    assert asks["does"] == (
        "Add a journey of at most 40 minutes, by public transport. "
        "Burro does not know this place: choose one."
    )
    assert asks["asks_place"] is True and asks["options"] == []
    named = text[asks["named_at"]["start"] : asks["named_at"]["end"]]
    assert named == "Mirrowick Basin"
    # No way of it holds a place. The client puts in the one the person chooses.
    places = [edit["place_id"] for w in asks["choices"] for edit in w["operations"]["commute_ops"]]
    assert places == ["", ""]
    assert asks["add_all"] == "" and asks["needs"] == "a place for the journey"


def test_a_home_no_price_is_held_for_has_nothing_to_press_and_is_not_said_to_be_a_journey(
    client: TestClient,
):
    # A buyer's home by its bedrooms, where prices are held by the kind of home.
    text = "If I'm buying, max \N{POUND SIGN}400k, one bedroom would do"

    *_, home = offered(client, text)

    assert (home["target"], home["label"]) == ("budget", "A 1-bedroom home")
    assert (home["does"], home["follows"], home["said"]) == (NOTHING_TAKEN, "", [])
    assert "not by the number of bedrooms" in home["note"]
    assert buttons(home) == ["Skip"] and home["add_all"] == ""


def test_a_least_distance_is_answered_in_a_fixed_line_and_with_nothing_to_press():
    found, text = served_again("journey-030")

    [notice] = found["suggestions"]
    assert (notice["does"], notice["follows"]) == (NO_JOURNEY, NO_LEAST)
    assert buttons(notice) == ["Skip"] and notice["said"] == []
    assert wrote(notice, text) == "Minimum 45 minutes from Pellam Infirmary"


# --- Three rules of the wording --------------------------------------------------------------


def every_offer() -> list[tuple[str, dict[str, Any]]]:
    """Every offer that is served for an answer on disk, with the sentence it is of."""
    found: list[tuple[str, dict[str, Any]]] = []
    for (case, look), row in answers_on_disk().items():
        if "output" in row:
            data, text = served_again(case, look)
            found += [(text, offer) for offer in data["suggestions"]]
    return found


EVERY_OFFER = every_offer()


def test_doing_nothing_is_skip_and_is_always_the_last_choice():
    for _, offer in EVERY_OFFER:
        *ways, nothing = offer["choices"]
        assert (nothing["id"], nothing["direction"], nothing["label"]) == (
            "ignore",
            "ignore",
            "Skip",
        )
        assert not any(edits for edits in nothing["operations"].values())
        # "Leave it out" beside "Leave out Pellam Cross" meant the opposite with one word more.
        assert not {"Skip", "Leave it out"} & {way["label"] for way in ways}


def test_a_wish_against_a_thing_is_never_said_to_be_counted_less():
    for _, offer in EVERY_OFFER:
        said = " ".join([offer["does"], offer["follows"], *offer["said"], *buttons(offer)])
        assert "counted less" not in said and "counted a little less" not in said


def test_what_an_offer_would_do_begins_with_a_verb_or_is_a_question():
    verbs = ("Add", "Set", "Rank", "Stop", "Look", "Leave", "Take")
    for _, offer in EVERY_OFFER:
        does = offer["does"]
        assert does.startswith(verbs) or does.endswith("?") or does == NO_JOURNEY, does


def test_what_nobody_said_is_said():
    text = "Honestly, no more than 40 minutes to Cindermoor Works"
    journey = model_commute(destination_text="Cindermoor Works", max_minutes=40, words=text)
    budget = model_budget(amount=1500, words="about 1500 would do")

    found = through_the_route(model_output(commute_ops=[journey]), text)
    money_only = through_the_route(model_output(budget_ops=[budget]), "about 1500 would do")

    assert found["suggestions"][0]["said"] == [
        "You named no way of travelling: Burro took public transport."
    ]
    assert money_only["suggestions"][0]["said"] == [
        "You did not say renting or buying: Burro took renting, as the search stands."
    ]


def test_a_way_of_travelling_that_was_named_and_not_taken_is_said_to_be_so(client: TestClient):
    [journey] = offered(client, "30 minutes to Pellam Cross by bike is too long")

    assert journey["said"] == [
        "Burro took public transport. "
        "If you travel another way, change it once the journey is added."
    ]


def test_every_way_is_unlike_every_other_of_its_offer():
    for _, offer in EVERY_OFFER:
        ids = [way["id"] for way in offer["choices"]]
        assert len(set(ids)) == len(ids), offer["target"]
        assert len(set(buttons(offer))) == len(offer["choices"]), offer["target"]
        assert sum(way["guess"] for way in offer["choices"]) <= 1


def test_the_guess_is_what_the_offer_says_it_would_do():
    for _, offer in EVERY_OFFER:
        guesses = [way for way in offer["choices"] if way["guess"]]
        for way in guesses:
            for wish in way["operations"]["weight_ops"]:
                assert (
                    FEATURES[wish["feature_id"]].short_label.lower()[:12] in (offer["does"].lower())
                    or wish["direction"] != "default"
                ), offer["does"]
            for tag in way["operations"]["tag_ops"]:
                assert TAGS[tag["tag_id"]].label in offer["does"]


# --- An offer says all that each of its ways holds ------------------------------------------------


def _said_of(offer: dict[str, Any], way: dict[str, Any]) -> str:
    return " ".join([offer["does"], offer["follows"], way["label"], *offer["said"]])


def test_every_part_of_every_edit_is_named_on_the_face_of_its_offer():
    for _, offer in EVERY_OFFER:
        ways = [way for way in offer["choices"] if way["id"] != "ignore"]
        guessed = [way for way in ways if way["guess"]] or ways[:1]
        for way in ways:
            # What is said above the ways is said of the guess, or of the one way there is.
            said = _said_of(offer, way) if way in guessed or len(ways) == 1 else way["label"]
            whole = _said_of(offer, way)
            for budget in way["operations"]["budget_ops"]:
                if budget["amount"]:
                    assert f"\N{POUND SIGN}{money(budget['amount'])}" in whole
                if budget["segment"] != "unchanged":
                    assert SEGMENT_LABELS[Segment(budget["segment"])] in whole
                if budget["tenure"] != "unchanged":
                    assert f"to {budget['tenure']}" in whole
                if budget["strictness"] == "hard":
                    assert "firm limit" in way["label"] and "left out" in way["label"]
            for journey in way["operations"]["commute_ops"]:
                place = release().place(journey["place_id"])
                assert place is None or place.name in whole
                if journey["max_minutes"]:
                    assert f"at most {journey['max_minutes']} minutes" in whole
                if journey["strictness"] == "hard":
                    assert "firm limit" in way["label"] and "left out" in way["label"]
                by = {"walk": "on foot", "cycle": "by bike"}.get(journey["mode"], "public")
                assert by in whole
            for area in way["operations"]["area_ops"]:
                named = release().neighbourhood(area["area_id"])
                assert named is not None and named.name in whole
            for tag in way["operations"]["tag_ops"]:
                assert TAGS[tag["tag_id"]].label in whole
                if tag["action"] != "remove" and TAGS[tag["tag_id"]].low_end:
                    end = (
                        TAGS[tag["tag_id"]].low_end
                        if tag["toward"] == "low"
                        else (TAGS[tag["tag_id"]].high_end)
                    )
                    assert f"owards {end}" in said
            for wish in way["operations"]["weight_ops"]:
                feature = FEATURES[wish["feature_id"]]
                # A wish for a thing that runs both ways is said in a word of the thing's
                # own where it has one, "dearer", and what Burro counts names the thing.
                own_word = feature.polarity == "either" and feature.higher != "more"
                thing = feature.label if own_word else feature.short_label
                assert thing.lower() in whole.lower()
                if wish["direction"] == "less" and feature.polarity == "either":
                    assert feature.lower in said.lower()


def test_recorded_crime_is_chosen_under_its_own_name(client: TestClient):
    crimes = offered(client, "somewhere safe") + offered(client, "gritty but safe")

    assert len(crimes) == 5
    for offer in crimes:
        *ways, _ = offer["choices"]
        for way in ways:
            assert "recorded" in way["label"].lower()
        assert offer["add_all"] == ""
        assert offer["needs"] == "recorded crime, which is added under its own name"
        assert "Recorded crime depends on what is reported" in offer["note"]


# --- The person's words are in no part of it ---------------------------------------------------


def test_no_word_of_the_persons_is_in_any_part_of_an_offer():
    text = f"My {CANARY} swears by a proper {CANARY} spot near {CANARY} Park, mind"
    answer = model_output(
        weight_ops=[model_weight("venue_food_drink", words=f"a proper {CANARY} spot")],
        tag_ops=[model_tag("foodie", words=f"My {CANARY} swears by")],
        commute_ops=[model_commute(destination_text=f"{CANARY} Park", max_minutes=20, words=text)],
        unmet=[{"category": "broadband", "words": f"{CANARY} spot"}],
    )

    found = through_the_route(answer, text)

    assert found["suggestions"] and CANARY not in json.dumps(found).casefold()
    for offer in found["suggestions"]:
        # What is served of the words is where they stand, in whole numbers.
        for span in (*offer["spans"], offer["shown"]):
            assert set(span) == {"start", "end"}
            assert 0 <= span["start"] < span["end"] <= len(text)


def test_the_words_an_offer_rests_on_lie_within_what_is_shown():
    for text, offer in EVERY_OFFER:
        shown = offer["shown"]
        assert 0 <= shown["start"] < shown["end"] <= len(text)
        first = min(span["start"] for span in offer["spans"])
        assert shown["start"] <= first < shown["end"]
        # What is shown begins and ends on a word, and holds no line of its own.
        cut = text[shown["start"] : shown["end"]]
        assert cut == cut.strip() and re.match(r"\w|\N{POUND SIGN}", cut)
