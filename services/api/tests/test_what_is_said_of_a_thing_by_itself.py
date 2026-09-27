"""What is said of a thing is read by itself, where the rules would not apply its sentence.

The way the words give of a wish was marked only where the rules would apply
the whole sentence the thing stands in. They apply a prompt only where the
grammar makes the whole of it, so one word they do not know left the way of
every thing of its sentence unsaid, and a client that takes what is offered
and asks nothing left out what was plainly wanted: "lively, lots going on in
the evening", "historic, lots of character", "Short version: quiet, leafy,
near a station".

The rules now read what is said of the thing by itself, where nothing beside
it may be said of it too (contract, section 8.2; ADR 0012, as amended on
2026-09-27). What they would apply of those words is the way the words give.
They still apply nothing of a prompt that is not plain, and what they do not
read is still not guessed at: "a good local pub within stumbling distance"
holds a word they do not know in what is said of the pub, as "a pub on the
corner would ruin it for me" does, and no list of words tells the two apart.

The sentences are those of the evaluation set that a client which asks
nothing took on the evening of 2026-09-26 and left on the morning after. Each
is named by its case. Every one is made up.
"""

from functools import cache
from typing import Any

import pytest
from burro_api import guard
from burro_core.interpret import DOES_NOT_MATTER, NOT_SAID_TO_BE_WANTED
from fastapi.testclient import TestClient

from .support import client_for, make_deps, scorer

LEAFY, QUIET, PACE, AGE, HOMES = (
    "tag:leafy",
    "tag:quiet_residential",
    "tag:pace",
    "tag:built_age",
    "tag:homes",
)
PARK, STATION, CULTURE, WATER = (
    "feature:park_proximity",
    "feature:station_walk",
    "feature:culture_venues_per_homes",
    "feature:water_access",
)
PUBS, FOOD, CAFES = (
    "feature:venue_evening_per_homes",
    "feature:venue_food_drink_per_homes",
    "feature:venue_cafe_per_homes",
)
SHOPS, INDEPENDENTS, CONSERVED = (
    "feature:highstreet_access",
    "feature:independents_nearby",
    "feature:conservation_cover",
)
NOISE, PLAY, VILLAGE = "feature:noise_exposure", "feature:play_space_proximity", "tag:village_feel"
MORE, LESS, OFF = "more", "less", "off"
SAYS_NOT_WANTED = "Burro read your words as saying that you do not want this"


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


@cache
def held() -> dict[str, tuple[str, str]]:
    """The words of every case of the evaluation set, and where its toggle stands, by its id."""
    score: Any = scorer()
    cases, problems = score.load_cases(score.CASES, score.load_release(None))
    assert not problems
    return {case.id: (case.text, case.tenure.value) for case in cases}


def read(client: TestClient, text: str, tenure: str = "rent") -> dict[str, dict[str, Any]]:
    """What is offered of a sentence, by what each offer is of. Nothing of it is applied."""
    start = client.get("/v1/meta").json()["data"]["defaults"][tenure]
    response = client.post("/v1/interpret", json={"text": text, "spec": start})
    assert response.status_code == 200, response.text
    found = response.json()["data"]
    wishes = [*found["operations"]["weight_ops"], *found["operations"]["tag_ops"]]
    assert not wishes, text
    return {offer["target"]: offer for offer in found["suggestions"]}


def of_the_case(client: TestClient, case: str) -> dict[str, dict[str, Any]]:
    text, tenure = held()[case]
    return read(client, text, tenure)


def ways(offer: dict[str, Any]) -> list[str]:
    return [way["id"] for way in offer["choices"] if way["id"] != "ignore"]


def guess(offer: dict[str, Any]) -> list[str]:
    return [way["id"] for way in offer["choices"] if way["guess"]]


def taken(offer: dict[str, Any]) -> str | None:
    """The way of an offer that a client takes which asks nothing, as the website chooses it."""

    def stops(way: dict[str, Any]) -> bool:
        wishes = [*way["operations"]["weight_ops"], *way["operations"]["tag_ops"]]
        return bool(wishes) and all(edit["action"] == "remove" for edit in wishes)

    if offer["only_by_choice"]:
        return None
    open_to = [way for way in offer["choices"] if way["id"] != "ignore" and not stops(way)]
    said = [way for way in open_to if offer["add_all"] and way["id"] == offer["add_all"]]
    guessed = [way for way in open_to if way["guess"]]
    if said or guessed:
        return (said or guessed)[0]["id"]
    more = [way for way in open_to if way["direction"] == "more"]
    less = [way for way in open_to if way["direction"] == "less"]
    if more and less:
        return None
    return (more or open_to or [{"id": None}])[0]["id"]


# --- What was wanted, and is taken again -------------------------------------------------

TAKEN_AGAIN: list[tuple[str, dict[str, str]]] = [
    # Words the rules do not know stand beyond a mark, after what is said of the thing.
    ("vibe-013", {PACE: MORE}),  # lively, lots going on in the evening
    ("vibe-002", {HOMES: MORE}),  # proper city living, flats are fine
    ("plain-017", {AGE: MORE}),  # historic, lots of character
    ("visit-075", {PACE: MORE}),  # somewhere lively honestly, up to £2,000
    ("whole-007", {AGE: MORE}),  # Characterful streets, historic if possible, and ...
    # A heading that says the list is of what is wanted, or says how long the words are.
    ("list-002", {PUBS: MORE}),  # Must have: a park. Nice to have: pubs.
    ("list-034", {PUBS: MORE}),  # Need: 2 bed, £1,900, ... Want: park, pub.
    ("long-028", {QUIET: MORE, LEAFY: MORE, STATION: MORE}),  # Short version: quiet, ...
    ("long-007", {LEAFY: MORE}),  # What I care about: a safe-feeling, calm area; trees; ...
    ("long-022", {WATER: MORE, CONSERVED: MORE, LEAFY: MORE}),  # So I care about the bones ...
    # A wish of the speaker's own, in a sentence that says more.
    ("long-018", {PACE: MORE}),  # I like a lively area, I'm not someone who needs silence.
    ("neg-038", {PACE: MORE}),  # I want somewhere noisy and lively
    ("long-006", {CULTURE: MORE}),  # i'm out most nights anyway so lots of bars and live music
    # Words that hold a word that turns, and turn nothing.
    ("double-020", {PARK: MORE}),  # nothing but parks
    ("vibe-008", {SHOPS: MORE}),  # a little centre with its own shops
    # "But" begins a new wish, whatever turned before it.
    ("lang-025", {PARK: MORE}),  # pas de pubs but a park would be nice
    # A sentence that goes on to say what is not wanted heads no list of it.
    ("long-023", {QUIET: MORE}),  # ... so not the middle of town. Somewhere ordinary and quiet.
    # What closes a list turns it only where a word after the turn stands for the list.
    ("long-013", {INDEPENDENTS: MORE}),  # ... somewhere that doesn't feel like everywhere else
    # A word that says no, and runs up to another thing, is said of that thing.
    ("long-025", {NOISE: LESS}),  # Low noise matters more than the station to me.
]


@pytest.mark.parametrize(("case", "wanted"), TAKEN_AGAIN)
def test_what_was_plainly_wanted_is_taken_by_a_client_that_asks_nothing(
    client: TestClient, case: str, wanted: dict[str, str]
):
    found = of_the_case(client, case)

    for target, way in wanted.items():
        assert taken(found[target]) == way, (case, target)
        assert found[target]["only_by_choice"] is False, (case, target)
        assert SAYS_NOT_WANTED not in found[target]["note"], (case, target)
        assert DOES_NOT_MATTER not in found[target]["note"], (case, target)


@pytest.mark.parametrize(
    ("text", "target", "given"),
    [
        ("lively, lots going on in the evening", PACE, MORE),
        ("historic, lots of character", AGE, MORE),
        ("somewhere calm, lots of trees about", PACE, LESS),
        ("new builds, all mod cons", AGE, LESS),
        ("Nice to have: pubs", PUBS, MORE),
        ("Short version: fewer pubs, leafy", PUBS, LESS),
        ("What I care about: pubs, a park", PUBS, MORE),
        ("I like a lively area, I'm not someone who needs silence", PACE, MORE),
        ("lively and posh", PACE, MORE),
    ],
)
def test_the_way_the_rules_give_of_what_is_said_of_a_thing_is_the_guess(
    client: TestClient, text: str, target: str, given: str
):
    found = read(client, text)[target]

    assert guess(found) == [given]
    assert found["add_all"] == given
    assert taken(found) == given


@pytest.mark.parametrize(
    "heading",
    ["Must haves", "What I care about", "Short version", "I want", "Things I would love"],
)
def test_a_heading_that_says_the_list_is_wanted_heads_it_on_a_line_of_its_own_too(
    client: TestClient, heading: str
):
    for text in (f"{heading}: a park, pubs", f"{heading}:\na park\npubs"):
        found = read(client, text)
        assert taken(found[PARK]) == MORE, text
        assert guess(found[PUBS]) == [MORE], text
        assert SAYS_NOT_WANTED not in found[PARK]["note"], text


@pytest.mark.parametrize(
    "heading",
    ["Dealbreakers", "What I want to avoid", "Things I hate", "I used to want", "Irritants"],
)
def test_a_heading_of_any_other_words_leaves_the_way_of_what_it_heads_unsaid(
    client: TestClient, heading: str
):
    for text in (f"{heading}: a park, pubs", f"{heading}:\na park\npubs"):
        found = read(client, text)
        assert taken(found[PARK]) is None, text
        assert guess(found[PUBS]) == [] and taken(found[PUBS]) is None, text


def test_the_guess_is_what_the_rules_apply_of_the_same_words_alone(client: TestClient):
    offered = read(client, "lively, lots going on in the evening")[PACE]
    alone = client.post("/v1/interpret", json={"text": "lively"}).json()["data"]

    assert alone["status"] == "ok"
    [edit] = alone["operations"]["tag_ops"]
    [way] = [way for way in offered["choices"] if way["guess"]]
    [marked] = way["operations"]["tag_ops"]
    assert (
        (marked["tag_id"], marked["toward"]) == (edit["tag_id"], edit["toward"]) == ("pace", "high")
    )
    # A wish is taken at a mention or a small step, whatever the words.
    assert (marked["action"], marked["step"]) == ("nudge", "up_large")


# --- What may be said of the thing leaves its way unsaid ---------------------------------

NO_GUESS: list[tuple[str, str]] = [
    # A word the rules do not know stands in what is said of the thing.
    ("a pub on the corner would ruin it for me", PUBS),
    ("pubs in the area would put me right off", PUBS),
    ("restaurants on every corner get old fast", FOOD),
    ("Red flags for me are pubs and a station on the doorstep", PUBS),
    ("I dinnae want pubs", PUBS),
    ("Some want pubs", PUBS),
    ("pubs are so noisy", PUBS),
    ("I shun busy high street nightlife", PACE),
    ("what's the best pub quiz team name", PUBS),
    # Words that core does not list stand before it, and may head it.
    ("Irritants - pubs, bars", PUBS),
    ("QuorvexMib TandleFrosk, somewhere lively", PACE),
    # What stands beyond a mark holds the speaker, a word that stands for the thing, or doubt.
    ("Nightlife, I'll pass", PACE),
    ("pubs, forget it", PUBS),
    # Or are a word that turns where it stands alone.
    ("pubs, pass", PUBS),
    ("nightlife, hard pass", PACE),
    ("pubs, restaurants, pass", FOOD),
    ("somewhere lively, maybe", PACE),
    ("pubs, bars, clubs, not relevant", PUBS),
    ("lively, I lived somewhere like that once", PACE),
    # A sentence that asks, and a token that is no word.
    ("somewhere with more pubs?", PUBS),
    ("nightlife \N{FACE WITH OPEN MOUTH VOMITING}", PACE),
    # A sentence beside it takes it back, or heads it.
    ("I'd love to be near lots of pubs and bars. Actually no, scrap that.", PUBS),
    ("I can't be doing with any of this. Pubs. Bars.", PUBS),
    # It stands with words about who lives somewhere, which draw the notice.
    ("somewhere lively for professionals", PACE),
    ("a lively spot where students live", PACE),
]


@pytest.mark.parametrize(("text", "target"), NO_GUESS)
def test_what_may_be_said_of_a_thing_leaves_its_way_unsaid(
    client: TestClient, text: str, target: str
):
    found = read(client, text)[target]

    assert guess(found) == []
    assert found["add_all"] == ""
    assert taken(found) is None


@pytest.mark.parametrize(
    ("text", "target", "left"),
    [
        ("Dealbreakers: pubs, a station", STATION, [MORE, OFF]),
        ("What I want to avoid: pubs, a park", PARK, [MORE, OFF]),
        ("I used to want: pubs, a park", PARK, [MORE, OFF]),
        ("Failing that: close to a station", STATION, [MORE, OFF]),
        ("no parks, playgrounds or schools", PLAY, [MORE]),
        ("my mum is after a park", PARK, [MORE, OFF]),
    ],
)
def test_what_the_words_do_not_say_is_the_persons_own_waits_as_it_did(
    client: TestClient, text: str, target: str, left: list[str]
):
    found = read(client, text)[target]

    assert found["only_by_choice"] is True
    assert found["note"].endswith(NOT_SAID_TO_BE_WANTED)
    assert ways(found) == left
    assert guess(found) == [] and taken(found) is None


def test_a_word_that_turns_where_it_stands_alone_turns_nothing_among_other_words(
    client: TestClient,
):
    turned = read(client, "a station, pass")[STATION]
    assert ways(turned) == [OFF] and taken(turned) is None
    assert SAYS_NOT_WANTED in turned["note"]

    for text in ("a park I can pass through", "I pass a park on my way to work"):
        named = read(client, text)[PARK]
        assert ways(named) == [MORE, OFF], text
        assert SAYS_NOT_WANTED not in named["note"], text


# --- The line that chooses what is made of words the rules do not know, beyond a mark ------

BESIDE_WORDS_THAT_ARE_NOT_KNOWN: list[tuple[str, str]] = [
    ("lively, lots going on in the evening", PACE),
    ("proper city living, flats are fine", HOMES),
    ("somewhere lively, QuorvexMib TandleFrosk", PACE),
    ("I want pubs, QuorvexMib TandleFrosk", PUBS),
]
# What is set apart from such words by a wish of the speaker's own, or stands beside
# words the rules know, is read by itself whichever way the line chooses.
SET_APART: list[tuple[str, str]] = [
    ("I'm tired of the city and want pubs", PUBS),
    ("sick of the city, we want somewhere lively", PACE),
    ("I want somewhere lively because I hate the quiet life", PACE),
    ("historic, lots of character", AGE),
    ("Short version: pubs, leafy", PUBS),
    ("somewhere lively honestly, up to \N{POUND SIGN}2,000", PACE),
]


@pytest.mark.parametrize("chosen", [guard.READ, guard.LEFT])
@pytest.mark.parametrize(("text", "target"), SET_APART)
def test_what_is_set_apart_is_read_by_itself_whichever_way_the_line_chooses(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, chosen: str, text: str, target: str
):
    monkeypatch.setattr(guard, "WHERE_WORDS_BEYOND_A_MARK_ARE_NOT_KNOWN", chosen)

    assert guess(read(client, text)[target]) == [MORE]


@pytest.mark.parametrize(("text", "target"), BESIDE_WORDS_THAT_ARE_NOT_KNOWN)
def test_a_thing_beside_words_that_are_not_known_is_read_or_left_as_the_line_chooses(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, text: str, target: str
):
    assert guard.WHERE_WORDS_BEYOND_A_MARK_ARE_NOT_KNOWN == guard.READ
    assert guess(read(client, text)[target]) == [MORE]

    monkeypatch.setattr(guard, "WHERE_WORDS_BEYOND_A_MARK_ARE_NOT_KNOWN", guard.LEFT)

    left = read(client, text)[target]
    assert guess(left) == [] and left["add_all"] == "" and taken(left) is None
    assert ways(left) == [MORE, LESS]


@pytest.mark.parametrize(
    "text",
    [
        # A turn beyond a mark, in words core does not list.
        "pubs, bleh",
        "pubs, give me strength",
        # And one that the speaker begins, after a wish of their own.
        "I want pubs, I'm joking",
    ],
)
@pytest.mark.xfail(strict=True, reason="contract, section 8.2: no list of such words is whole")
def test_a_turn_beyond_a_mark_in_words_core_does_not_list_leaves_the_way_unsaid(
    client: TestClient, text: str
):
    assert guess(read(client, text)[PUBS]) == []


@pytest.mark.parametrize(
    "text", ["pubs, bleh", "pubs, give me strength", "I want pubs, I'm joking"]
)
def test_such_a_turn_leaves_the_way_unsaid_where_the_line_chooses_to_leave_it(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, text: str
):
    monkeypatch.setattr(guard, "WHERE_WORDS_BEYOND_A_MARK_ARE_NOT_KNOWN", guard.LEFT)

    assert guess(read(client, text)[PUBS]) == []


def test_what_counts_recorded_crime_and_who_lived_somewhere_waits_whatever_the_words(
    client: TestClient,
):
    for text in (
        "I'm tired of the city and want somewhere safe",
        "I hate my flat and want somewhere posh",
        "lively, lots of young professionals",
        "sick of the noise, we want a family area",
    ):
        for offer in read(client, text).values():
            counts = offer["target"].removeprefix("feature:").removeprefix("tag:")
            waits = counts.startswith(("crime_", "residents_", "households_")) or counts in (
                "street_character",
                "homes_higher_bands",
                "young_professionals",
                "family_area",
            )
            if waits:
                assert offer["only_by_choice"] is True, (text, offer["target"])
                assert guess(offer) == [] and taken(offer) is None, (text, offer["target"])


def test_a_thing_turned_at_one_place_and_only_named_at_another_is_offered_no_way_for_more(
    client: TestClient,
):
    text = (
        "And please take off the high street thing, I don't know why that's on, "
        "I do all my shopping online."
    )

    found = read(client, text)[SHOPS]

    assert ways(found) == [OFF]
    assert taken(found) is None


# --- What is still left out, and why -------------------------------------------------------

# Each was taken on the evening of 2026-09-26, by a client that took more of whatever was
# offered, and is a thing its case says must rise. None is taken now. To take one is to
# take its opposite too, since no word that core lists tells the two apart.
LEFT_OUT: list[tuple[str, str, str]] = [
    # A word the rules do not know stands in what is said of the thing, as it does in "a
    # pub on the corner would ruin it for me".
    ("plain-010", PACE, "with stuff going on in the evenings"),
    ("plain-027", AGE, "with a bit of space"),
    ("plain-030", PUBS, "late bars"),
    ("plain-044", PUBS, "known for its pubs"),
    ("plain-046", PUBS, "within stumbling distance"),
    ("long-006", PUBS, "would be amazing"),
    ("long-009", PUBS, "matter more than parks"),
    ("long-009", FOOD, "matter more than parks"),
    ("long-021", PUBS, "a pub that does food"),
    ("visit-024", PACE, "a few nights"),
    ("whole-005", FOOD, "a few decent restaurants"),
    # A word that turns leads up to the thing, in words that mean the opposite of what
    # they say.
    ("double-007", PUBS, "you can't beat a good pub"),
    ("double-008", PUBS, "no shortage of pubs"),
    ("double-028", PUBS, "not having a pub nearby would be a dealbreaker"),
    ("typo-036", PARK, "i cant live with out a park"),
    ("lang-024", PARK, "un park, in another language"),
    ("lang-024", PUBS, "in another language"),
    # It stands in a list after a thing that is turned away, and a turn may reach on.
    ("neg-067", LEAFY, "quiet, not near a station, and leafy"),
    ("neg-068", LEAFY, "no pubs, leafy"),
    ("lang-026", PARK, "kein station, lieber parks"),
    # The wish may be somebody else's.
    ("other-015", PUBS, "my husband wants"),
    ("other-029", PUBS, "he wants"),
    ("other-029", STATION, "he wants"),
    ("other-037", PARK, "my wife says"),
    ("long-005", VILLAGE, "my wife wants"),
    ("long-024", SHOPS, "she wants"),
    ("long-026", PARK, "where people stay for years"),
    ("long-026", QUIET, "where people stay for years"),
    ("long-026", "feature:school_primary_nearby", "where people stay for years"),
    # What stands beyond a mark may be said of it.
    ("other-038", PUBS, "the dog doesn't care"),
    ("long-008", FOOD, "that kind of thing"),
    ("whole-010", AGE, "if I'm honest"),
    # Its sentence asks.
    ("ask-016", PUBS, "what about somewhere with more pubs?"),
    ("ask-021", PUBS, "Pubs? Love them."),
    ("sugg-011", PUBS, "Could you find me somewhere with good pubs?"),
    # A sentence before it holds doubt and names nothing, and may head it.
    ("sugg-029", PUBS, "I have never lived there."),
    # It stands under a heading that holds a sign of doubt, or that core does not know.
    ("long-014", SHOPS, "Failing that:"),
    ("long-014", STATION, "Failing that:"),
    ("long-016", VILLAGE, "I want the opposite:"),
    ("long-016", QUIET, "I want the opposite:"),
    ("long-027", LEAFY, "What we liked about Alderwick:"),
    ("long-027", QUIET, "What we liked about Alderwick:"),
    ("long-027", SHOPS, "the little parade of shops"),
    # It stands with a word that is heard as one about who lives somewhere.
    ("who-020", FOOD, "a diverse range of"),
]


def test_every_thing_that_is_still_left_out_is_named_once():
    left = {(case, target) for case, target, _ in LEFT_OUT}
    again = {(case, target) for case, wanted in TAKEN_AGAIN for target in wanted}

    assert len(LEFT_OUT) == len(left) == 44
    assert not left & again


@pytest.mark.parametrize(("case", "target", "because"), LEFT_OUT)
@pytest.mark.xfail(strict=True, reason="contract, section 8.2: what the words give, and do not")
def test_what_was_wanted_and_is_still_left_out(
    client: TestClient, case: str, target: str, because: str
):
    found = of_the_case(client, case)

    assert taken(found[target]) in (MORE, LESS), because


@pytest.mark.parametrize(("case", "target", "because"), LEFT_OUT)
def test_no_way_of_what_is_left_out_is_the_guess(
    client: TestClient, case: str, target: str, because: str
):
    found = of_the_case(client, case)

    # It is left, and is not read the other way: nothing of it is marked or named.
    assert guess(found[target]) == [], because
    assert found[target]["add_all"] == "", because
