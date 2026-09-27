"""The way the words give of a thing, in a sentence that is no plain list.

The rules offered both ways of a thing that runs two ways, more or fewer, calm
or buzzy, newer or historic, and marked neither as the guess, even where the
words plainly named one. While a person chose, that cost a press. A client
that takes what is offered and asks nothing takes a way only where the service
names it or marks it, so "honestly, somewhere calm" was left out of the search,
and to take the first of two had read it as buzzy (ADR 0012, as amended).

Where the words name the way, it is the guess, by the reading that applies the
word in a plain list. Where they name none, nothing is. Where they turn the
thing round, the turn is read, and where it cannot be, nothing is the guess and
no way is offered that counts the thing for more.

Every sentence here is made up, but the founder's own, which is theirs by
their consent.
"""

from typing import Any

import pytest
from burro_core.interpret import (
    DOES_NOT_MATTER,
    NOT_SAID_TO_BE_WANTED,
    NOT_WANTED,
    NOT_WANTED_AND_COUNTED,
)
from burro_core.vocabulary import ASIDES
from fastapi.testclient import TestClient

from .support import (
    client_for,
    make_deps,
    model_output,
    model_tag,
    model_weight,
    through_the_route,
)

PACE, AGE, GRITTY, LEAFY = "tag:pace", "tag:built_age", "tag:street_character", "tag:leafy"
PUBS, STATION, CULTURE, PARK = (
    "feature:venue_evening_per_homes",
    "feature:station_walk",
    "feature:culture_venues_per_homes",
    "feature:park_proximity",
)
NOISE, VIOLENCE = "feature:noise_exposure", "feature:crime_violence_robbery"
MORE, LESS, OFF = "more", "less", "off"


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def read(client: TestClient, text: str) -> dict[str, dict[str, Any]]:
    """What is offered of a sentence, by what each offer is of. Nothing of it is applied."""
    response = client.post("/v1/interpret", json={"text": text})
    assert response.status_code == 200, response.text
    found = response.json()["data"]
    assert not any(found["operations"].values()), text
    return {offer["target"]: offer for offer in found["suggestions"]}


def ways(offer: dict[str, Any]) -> list[str]:
    return [way["id"] for way in offer["choices"] if way["id"] != "ignore"]


def guess(offer: dict[str, Any]) -> list[str]:
    return [way["id"] for way in offer["choices"] if way["guess"]]


def taken(offer: dict[str, Any]) -> str | None:
    """The way of an offer that a client takes which asks nothing, as the website chooses it.

    The way one press may add. Of a limit, the guide. The way that is the
    guess. And of a thing that runs one way, that way. To stop counting a
    thing is no way of taking it. What waits for a person is left, and so
    are a rule for an area and a thing that runs two ways, where the words
    give no way.
    """

    def stops(way: dict[str, Any]) -> bool:
        wishes = [*way["operations"]["weight_ops"], *way["operations"]["tag_ops"]]
        return bool(wishes) and all(edit["action"] == "remove" for edit in wishes)

    def limits(way: dict[str, Any]) -> list[dict[str, Any]]:
        return [*way["operations"]["budget_ops"], *way["operations"]["commute_ops"]]

    if offer["only_by_choice"]:
        return None
    every = [way for way in offer["choices"] if way["id"] != "ignore"]
    said = [way for way in every if offer["add_all"] and way["id"] == offer["add_all"]]
    open_to = [way for way in every if not stops(way)]
    guides = [
        way
        for way in open_to
        if any(edit["strictness"] != "unchanged" for edit in limits(way))
        and not any(edit["strictness"] == "hard" for edit in limits(way))
    ]
    guessed = [way for way in open_to if way["guess"]]
    if said or guides or guessed:
        return (said or guides or guessed)[0]["id"]
    ruled = any(e["action"] != "clear" for way in open_to for e in way["operations"]["area_ops"])
    more = [way for way in open_to if way["direction"] == "more"]
    less = [way for way in open_to if way["direction"] == "less"]
    if ruled or (more and less):
        return None
    return (more or open_to or [{"id": None}])[0]["id"]


# --- Where the words name the way ---------------------------------------------------------

NAMED = [
    ("Honestly, somewhere lively", PACE, MORE, [MORE, LESS]),
    ("Honestly, somewhere calm", PACE, LESS, [MORE, LESS]),
    ("Honestly, somewhere historic", AGE, MORE, [MORE, LESS]),
    ("Honestly, more pubs", PUBS, MORE, [MORE, LESS]),
    ("Honestly, fewer pubs", PUBS, LESS, [LESS]),
    ("Somewhere gritty, I think", GRITTY, MORE, [MORE, LESS]),
    ("somewhere polished, I think", GRITTY, LESS, [MORE, LESS]),
    ("honestly, new builds", AGE, LESS, [MORE, LESS]),
    ("honestly, leafy and quiet", LEAFY, MORE, [MORE]),
]


@pytest.mark.parametrize(("text", "target", "given", "offered"), NAMED)
def test_the_way_the_words_name_is_the_guess(
    client: TestClient, text: str, target: str, given: str, offered: list[str]
):
    found = read(client, text)[target]

    assert guess(found) == [given]
    assert ways(found) == offered
    assert taken(found) == given


@pytest.mark.parametrize(("text", "target", "given", "offered"), NAMED)
def test_the_guess_is_the_way_the_rules_apply_of_the_same_words_in_a_plain_list(
    client: TestClient, text: str, target: str, given: str, offered: list[str]
):
    # The sentence, less what is said of the words alone, is a plain list.
    said = text
    for aside in ("Honestly, ", "honestly, ", ", I think"):
        said = said.replace(aside, "")
    plain = client.post("/v1/interpret", json={"text": said}).json()["data"]
    assert plain["status"] == "ok" and not plain["suggestions"]
    kind, _, named = target.partition(":")
    edits = plain["operations"]["tag_ops" if kind == "tag" else "weight_ops"]
    (edit,) = [one for one in edits if named in (one.get("tag_id"), one.get("feature_id"))]
    less = edit.get("toward") == "low" or edit.get("direction") == "less"

    assert given == (LESS if less else MORE)


def test_a_wish_that_carries_the_guess_is_one_that_one_press_may_take(client: TestClient):
    for text, target, given, _ in NAMED:
        found = read(client, text)[target]
        counts_crime = "counting recorded crime" in found["does"]
        # Recorded crime is taken by no press that takes it with others.
        assert found["add_all"] == ("" if counts_crime else given), text


def test_a_wish_that_is_said_softly_is_taken_at_a_small_step(client: TestClient):
    found = read(client, "honestly, fairly leafy")[LEAFY]

    (way,) = [way for way in found["choices"] if way["guess"]]
    (edit,) = way["operations"]["tag_ops"]
    assert (edit["action"], edit["step"]) == ("nudge", "up_small")
    assert found["does"] == "Add Leafy, counted a little."


def test_a_wish_is_never_taken_at_the_most_it_can_count(client: TestClient):
    found = read(client, "honestly, a park is essential")[PARK]

    (way,) = [way for way in found["choices"] if way["guess"]]
    (edit,) = way["operations"]["weight_ops"]
    assert (edit["action"], edit["step"]) == ("nudge", "up_large")


# --- What is said of the words alone --------------------------------------------------------


@pytest.mark.parametrize("aside", sorted(ASIDES))
def test_what_is_said_of_the_words_alone_leaves_the_way_as_it_was_given(
    client: TestClient, aside: str
):
    for text in (f"{aside}, somewhere calm", f"somewhere calm, {aside}"):
        found = read(client, text)[PACE]
        assert guess(found) == [LESS], text


@pytest.mark.parametrize(
    "text",
    [
        # Not set apart by a mark, it is a word the reader does not know.
        "I honestly want somewhere calm",
        "somewhere calm honestly",
        # Words that are no such aside may say anything.
        "somewhere calm, QuorvexMib TandleFrosk",
        "somewhere calm, maybe",
        "somewhere calm, maybe not",
    ],
)
def test_words_that_are_no_aside_leave_the_way_unsaid(client: TestClient, text: str):
    found = read(client, text)[PACE]

    assert guess(found) == []
    assert ways(found) == [MORE, LESS]
    assert taken(found) is None


# --- Where the words name no way, or may turn it ------------------------------------------


@pytest.mark.parametrize(
    ("text", "target"),
    [
        ("pubs are so noisy", PUBS),
        ("Some want pubs", PUBS),
        # What stands beyond a mark turns a wish as often as what stands beside it.
        ("Nightlife, I'll pass", PACE),
        ("pubs, forget it", PUBS),
        ("Dealbreakers: pubs", PUBS),
        ("Negatives: nightlife", PACE),
        ("I hate pubs", PUBS),
        ("you can't beat a good pub", PUBS),
        ("Is it lively?", PACE),
    ],
)
def test_where_the_words_give_no_way_nothing_is_the_guess_and_nothing_is_taken(
    client: TestClient, text: str, target: str
):
    found = read(client, text)[target]

    assert guess(found) == []
    assert ways(found) == [MORE, LESS]
    assert taken(found) is None


def test_a_thing_said_both_ways_carries_no_guess(client: TestClient):
    found = read(client, "I want pubs. Actually I do not want pubs.")[PUBS]

    assert guess(found) == [] and taken(found) is None


# --- Where the words turn a thing round -----------------------------------------------------

TURNED: list[tuple[str, str, list[str], str | None]] = [
    # The station counts until a person says otherwise, so to stop counting it is left.
    ("I never use the station", STATION, [OFF], NOT_WANTED_AND_COUNTED),
    ("a station, heaven forbid", STATION, [OFF], NOT_WANTED_AND_COUNTED),
    ("parks, playgrounds and a station: I can do without them", STATION, [OFF], None),
    # Culture counts for nothing until it is asked for, so nothing is left.
    ("I hate culture", CULTURE, [], NOT_WANTED),
    ("theatres would be ghastly", CULTURE, [], NOT_WANTED),
    ("I want a park. Not really.", PARK, [OFF], NOT_WANTED_AND_COUNTED),
    # A nuisance is turned by what says that it is not minded.
    ("crime doesn't bother me", VIOLENCE, [], DOES_NOT_MATTER),
    ("noise doesn't matter, honestly", NOISE, [], DOES_NOT_MATTER),
]


@pytest.mark.parametrize(("text", "target", "left", "note"), TURNED)
def test_where_the_words_turn_a_thing_round_no_way_is_offered_that_counts_it(
    client: TestClient, text: str, target: str, left: list[str], note: str | None
):
    found = read(client, text)[target]

    assert ways(found) == left
    assert guess(found) == []
    assert taken(found) is None
    assert found["add_all"] == ""
    if note is not None:
        assert found["note"].endswith(note)


def test_not_too_busy_names_nothing_that_burro_counts_so_nothing_is_offered(client: TestClient):
    response = client.post("/v1/interpret", json={"text": "not too busy"})
    found = response.json()["data"]

    assert found["suggestions"] == [] and not any(found["operations"].values())
    assert found["unread"] == [{"start": 0, "end": 12}]


READ = [
    ("Honestly, no station", STATION, OFF, [OFF]),
    ("honestly, not near a station", STATION, OFF, [OFF]),
    ("Honestly, no pubs", PUBS, LESS, [LESS]),
    ("Honestly, not buzzy", PACE, LESS, [LESS]),
    ("honestly, not calm", PACE, MORE, [MORE]),
    ("honestly, no noise", NOISE, LESS, [LESS]),
    ("low crime and leafy, honestly", VIOLENCE, LESS, [LESS]),
]


@pytest.mark.parametrize(("text", "target", "given", "left"), READ)
def test_a_turn_that_the_rules_read_is_the_guess(
    client: TestClient, text: str, target: str, given: str, left: list[str]
):
    found = read(client, text)[target]

    assert guess(found) == [given]
    assert ways(found) == left
    # To stop counting a thing is no way of taking it, so nothing is taken for more.
    assert taken(found) == (None if given == OFF else given)


def test_the_one_way_left_of_a_wish_that_is_turned_round_is_said_and_not_asked(
    client: TestClient,
):
    found = read(client, "I never use the station")[STATION]

    assert found["does"] == "Stop counting this: nearer a station."
    assert [way["label"] for way in found["choices"]] == ["Stop counting it", "Skip"]
    # A page prints the three one after the other, so none says what another said.
    assert found["follows"] == (
        "It counts a little now, because nobody chose. "
        "Burro cannot rank an area for the opposite of it."
    )
    assert found["note"] == (
        "Burro read your words as saying that you do not want this, so the most it can do is "
        "to stop counting it."
    )


def test_two_words_that_turn_before_a_thing_may_turn_it_round_twice(client: TestClient):
    # Nobody can say which from a list of words, so every way is offered as it was.
    for text in ("I can't live without a park", "I don't want to be far from a park"):
        found = read(client, text)[PARK]
        assert ways(found) == [MORE, OFF], text
        assert guess(found) == [], text
    # What carries a turn on is no second turn.
    found = read(client, "honestly neither parks nor pubs")
    assert ways(found[PARK]) == [OFF]


# --- A sentence beside the one a thing stands in ---------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "Somewhere gritty. QuorvexMib TandleFrosk",
        "QuorvexMib TandleFrosk. Somewhere gritty.",
        "Somewhere gritty. Honestly.",
        "Moving next month. Somewhere gritty.",
    ],
)
def test_a_sentence_of_words_that_are_not_known_takes_nothing_back(client: TestClient, text: str):
    found = read(client, text)[GRITTY]

    assert guess(found) == [MORE]
    assert found["by_name"] and not found["only_by_choice"]
    assert taken(found) == MORE


@pytest.mark.parametrize(
    "text",
    [
        "Somewhere gritty. Not really.",
        "Somewhere gritty. No thanks.",
        "Things I hate. Somewhere gritty.",
        "Dealbreakers:\ngritty\npubs",
    ],
)
def test_a_sentence_of_doubt_and_a_heading_turn_what_stands_beside_them(
    client: TestClient, text: str
):
    found = read(client, text)[GRITTY]

    assert guess(found) == []
    assert taken(found) is None


@pytest.mark.parametrize(
    ("text", "left"),
    [
        ("I want a station. Not really.", [OFF]),
        ("I want a station. No thanks.", [OFF]),
        ("Things I hate. Pubs. A station.", [OFF]),
        ("What I want to avoid\n- pubs\n- a station", [OFF]),
        ("No.\nPubs\nA station", [OFF]),
    ],
)
def test_a_thing_that_a_sentence_beside_it_turns_round_is_offered_no_way_for_more(
    client: TestClient, text: str, left: list[str]
):
    found = read(client, text)[STATION]

    assert ways(found) == left and guess(found) == []
    assert found["note"] == NOT_WANTED_AND_COUNTED


@pytest.mark.parametrize(
    "text",
    [
        # A sentence that turns, and says more than that it turns, is as likely said of
        # something else. It marks no guess, and it turns nothing round.
        "Not sure where to begin. A station.",
        "A station. Not sure about the budget yet.",
        "I don't know the city. A station.",
        "Requirements\na park\na station",
    ],
)
def test_a_sentence_that_says_more_than_that_it_turns_turns_nothing_round(
    client: TestClient, text: str
):
    found = read(client, text)[STATION]

    assert ways(found) == [MORE, OFF]
    assert found["only_by_choice"] is False
    assert taken(found) == MORE


# --- What waits for a person ----------------------------------------------------------------

WAITS = [
    ("my mum is after a park", PARK),
    ("he wants a park, a station", STATION),
    ("no parks, playgrounds or schools", "feature:play_space_proximity"),
    ("Dealbreakers: pubs, a station", STATION),
    ("Cons: a station", STATION),
    ("pubs are so noisy", NOISE),
    ("I like noise", NOISE),
    ("I study crime at university", VIOLENCE),
]


@pytest.mark.parametrize(("text", "target"), WAITS)
def test_where_the_words_do_not_say_that_the_wish_is_the_persons_own_it_waits_for_them(
    client: TestClient, text: str, target: str
):
    found = read(client, text)[target]

    assert found["only_by_choice"] is True
    assert found["note"].endswith(NOT_SAID_TO_BE_WANTED)
    # It is offered as it was, for a person to choose, and no press takes it with others.
    assert ways(found)
    assert guess(found) == [] and found["add_all"] == ""
    assert taken(found) is None


@pytest.mark.parametrize(
    ("text", "target"),
    [
        ("Must haves: a park, a station", STATION),
        ("Priorities: leafy, a station", STATION),
        ("I want: a park and a station", STATION),
        ("honestly, no pubs, but a station", STATION),
        ("No pubs. A station. QuorvexMib TandleFrosk", STATION),
        ("leafy and quiet, QuorvexMib TandleFrosk", LEAFY),
        ("burglary worries me", "feature:crime_burglary_theft"),
    ],
)
def test_a_wish_that_nothing_puts_in_doubt_waits_for_nobody(
    client: TestClient, text: str, target: str
):
    found = read(client, text)[target]

    assert found["only_by_choice"] is False
    assert taken(found) in (MORE, LESS)


def test_a_place_that_may_be_somebody_elses_waits_for_a_person(client: TestClient):
    for text in (
        "My ex works at Pellam Infirmary so I'd rather be elsewhere",
        "my mother lives in Pellam Cross",
    ):
        found = read(client, text)["commute"]
        assert found["only_by_choice"] is True, text
        assert taken(found) is None, text
    # A place of the person's own is taken as it was.
    found = read(client, "Honestly, I work at Pellam Infirmary")["commute"]
    assert found["only_by_choice"] is False and taken(found) == MORE


# --- What does not change --------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "honestly, young professionals",
        "families, honestly",
        "honestly, fewer families",
        "honestly, no students",
        "people my age, I think",
    ],
)
def test_what_counts_who_lives_somewhere_carries_no_guess_and_is_never_turned(
    client: TestClient, text: str
):
    response = client.post("/v1/interpret", json={"text": text})
    found = response.json()["data"]

    assert not any(found["operations"].values())
    for offer in found["suggestions"]:
        assert guess(offer) == [] and offer["add_all"] == "", offer["label"]
        assert offer["only_by_choice"] is True and taken(offer) is None, offer["label"]
        # No way of it asks for fewer of anybody, whatever the words.
        for way in offer["choices"]:
            edits = [*way["operations"]["weight_ops"], *way["operations"]["tag_ops"]]
            assert all(edit["action"] == "nudge" for edit in edits), offer["label"]
            assert all(
                edit.get("direction", "default") != "less" and edit.get("toward") != "low"
                for edit in edits
            ), offer["label"]
        assert NOT_WANTED not in offer["note"] and DOES_NOT_MATTER not in offer["note"]


@pytest.mark.parametrize(
    "text",
    ["somewhere calm", "fewer pubs", "no station", "gritty", "low crime and leafy", "lively"],
)
def test_a_plain_list_is_applied_as_it_was_and_offers_nothing(client: TestClient, text: str):
    found = client.post("/v1/interpret", json={"text": text}).json()["data"]

    assert found["status"] == "ok" and found["suggestions"] == []
    assert any(found["operations"].values()) and found["applied"]
    # With what is said of the words alone beside it, the same is offered and nothing applied.
    offered = client.post("/v1/interpret", json={"text": f"Honestly, {text}"}).json()["data"]
    assert not any(offered["operations"].values())
    took = [way for way in (taken(offer) for offer in offered["suggestions"]) if way]
    stops = text == "no station"
    assert took or stops


# --- The founder's own sentence --------------------------------------------------------------

THE_FOUNDERS = (
    "I want to live somewhere quiet, with access to parks, slightly affluent but with some "
    "culture around it, something with a real identity. "
    "At most 35-40min commute from Pellam Exchange. "
    "If I'm buying, max \N{POUND SIGN}400k for a 1 bed flat."
)


def test_of_the_founders_sentence_no_less_is_taken_than_a_person_would_have_chosen(
    client: TestClient,
):
    response = client.post("/v1/interpret", json={"text": THE_FOUNDERS})
    offers = response.json()["data"]["suggestions"]

    took = {(offer["target"], offer["label"]): taken(offer) for offer in offers}
    left = {about for about, way in took.items() if way is None}
    # All that a person who pressed every offer would have chosen is taken, but what a
    # promise of the product leaves to the person: recorded crime that the words do not
    # name, and the measure that is offered and never applied.
    assert left == {
        (GRITTY, "Gritty"),
        ("feature:homes_higher_bands", "Homes in the higher council tax bands"),
    }
    assert all(offer["only_by_choice"] for offer in offers if taken(offer) is None)
    assert took == {
        ("tag:quiet_residential", "Quiet streets"): MORE,
        (PARK, "Nearer a park"): MORE,
        ("feature:brand_mix", "Mix of brands"): MORE,
        (GRITTY, "Gritty"): None,
        ("feature:price_median", "What homes sell for"): MORE,
        ("feature:homes_higher_bands", "Homes in the higher council tax bands"): None,
        (CULTURE, "More culture nearby"): MORE,
        ("tag:village_feel", "Village feel"): MORE,
        (AGE, "Age of buildings"): MORE,
        ("feature:highstreet_access", "Nearer a town centre"): MORE,
        ("commute", "Pellam Exchange"): "guide",
        ("tenure", "Buying"): MORE,
        ("budget", "A budget of \N{POUND SIGN}400,000"): MORE,
        ("budget", "A flat"): MORE,
    }
    # What the words plainly name is the guess, and is taken as it was said.
    named = {offer["target"]: guess(offer) for offer in offers}
    assert named["tag:quiet_residential"] == named[PARK] == named[CULTURE] == [MORE]


# --- What a model read ----------------------------------------------------------------------


def test_the_way_the_rules_give_stands_whatever_a_model_read():
    text = "Honestly, somewhere calm"
    backwards = model_output(tag_ops=[model_tag("pace", toward="high", words="somewhere calm")])
    nothing = model_output()

    for answer in (backwards, nothing):
        found = {one["target"]: one for one in through_the_route(answer, text)["suggestions"]}
        assert guess(found[PACE]) == [LESS]
        assert found[PACE]["read_by"] == "rule"


def test_a_thing_only_a_model_read_is_offered_no_way_for_more_where_the_words_turn_it():
    text = "a lido on the doorstep, heaven forbid"
    answer = model_output(weight_ops=[model_weight("park_facilities", words="a lido")])

    found = {one["target"]: one for one in through_the_route(answer, text)["suggestions"]}

    lido = found["feature:park_facilities"]
    assert lido["read_by"] == "model"
    assert ways(lido) == [] and guess(lido) == []
    assert lido["note"] == NOT_WANTED
    assert taken(lido) is None


def test_a_models_reading_is_marked_as_a_models_where_the_rules_read_nothing():
    text = "I'd love somewhere with a proper buzz, honestly"
    answer = model_output(tag_ops=[model_tag("pace", toward="high", words="a proper buzz")])

    found = {one["target"]: one for one in through_the_route(answer, text)["suggestions"]}

    assert found[PACE]["read_by"] == "model"
    assert ways(found[PACE]) == [MORE, LESS]
