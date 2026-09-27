"""A word that is read several ways is offered beside an aside as it is by itself.

"Posh" names no measure. It is read as the mix of brands, towards Polished, as
what homes sell for and as the homes in the higher council tax bands, and each
is offered the one way the word gives: "somewhere posh" asks for no cheaper
homes. It was offered so only where the grammar makes the whole of its
sentence. "Somewhere posh, honestly" is one the grammar does not make, so each
reading was offered both ways, as "anything but posh" is. A client that takes
what is offered and asks nothing takes neither of two ways that the words do
not choose between, so nothing was ranked, and the person was shown no areas.

What is said of the words alone says nothing of the wish: "honestly", "I
think". Where the sentence is one the grammar makes once that is left out of
it, wherever it stands, the word is offered as it is when it stands by itself.
What may turn it, put it in doubt or give it to somebody else leaves it as it
was, and so do words the rules do not know, beside it or beyond a mark. What
waits for a person still waits: recorded crime that the words do not name, and
the higher council tax bands (ADR 0012, as amended on 2026-09-27).

Every sentence here is made up, and the website was driven with the first six.
"""

from typing import Any

import pytest
from burro_core.interpret import NOT_SAID_TO_BE_WANTED
from fastapi.testclient import TestClient

from .support import client_for, make_deps

MIX, GRITTY = "feature:brand_mix", "tag:street_character"
SELLS_FOR, BANDS = "feature:price_median", "feature:homes_higher_bands"
RISE_5, RISE_10 = "feature:price_rise_5y", "feature:price_rise_10y"
LEAFY, QUIET, PUBS = "tag:leafy", "tag:quiet_residential", "feature:venue_evening_per_homes"
MORE, LESS = "more", "less"
# A word for a smart area, by what it is read as and the one way it gives of each.
SMART = {MIX: [MORE], GRITTY: [LESS], SELLS_FOR: [MORE], BANDS: [MORE]}
# The same readings, where the words do not say which way is meant.
EITHER_WAY = {MIX: [MORE, LESS], GRITTY: [MORE, LESS], SELLS_FOR: [MORE, LESS], BANDS: [MORE, LESS]}
# What waits for a person, whatever stands beside the word: recorded crime that the words
# do not name, and a measure that a decision holds to be offered and never applied.
WAITS = {GRITTY, BANDS}
# Every thing that such a word is read into, and that it does not name.
READ_IN = {MIX, GRITTY, SELLS_FOR, BANDS, RISE_5, RISE_10}
LEAFY_TOO = SMART | {LEAFY: [MORE], QUIET: [MORE]}


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps())


def read(client: TestClient, text: str) -> dict[str, Any]:
    response = client.post("/v1/interpret", json={"text": text})
    assert response.status_code == 200, response.text
    found = response.json()["data"]
    assert not any(found["operations"].values()), text
    return found


def offered(found: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {offer["target"]: offer for offer in found["suggestions"]}


def ways(found: dict[str, Any]) -> dict[str, list[str]]:
    """Each thing that is offered, with the ways it may be taken."""
    return {
        target: [way["id"] for way in offer["choices"] if way["id"] != "ignore"]
        for target, offer in offered(found).items()
    }


def guessed(found: dict[str, Any]) -> dict[str, list[str]]:
    marked = {
        target: [way["id"] for way in offer["choices"] if way["guess"]]
        for target, offer in offered(found).items()
    }
    return {target: held for target, held in marked.items() if held}


def waits(found: dict[str, Any]) -> set[str]:
    return {target for target, offer in offered(found).items() if offer["only_by_choice"]}


def taken(found: dict[str, Any]) -> dict[str, str]:
    """What a client takes which asks nothing, as `lib/search/takes.ts` chooses it.

    Nothing of what waits for a person. The way one press may add, else the
    way marked as the guess, else the one way of a thing that runs one way,
    and neither of two. And of the things that are read into the same words,
    which the words do not name, the one that carries the guess, or the first.
    """
    took: dict[str, str] = {}
    rests: dict[str, str] = {}
    for offer in found["suggestions"]:
        if offer["only_by_choice"]:
            continue
        stops = [
            way["id"]
            for way in offer["choices"]
            if (wishes := [*way["operations"]["weight_ops"], *way["operations"]["tag_ops"]])
            and all(edit["action"] == "remove" for edit in wishes)
        ]
        open_to = [
            way for way in offer["choices"] if way["id"] != "ignore" and way["id"] not in stops
        ]
        said = [way for way in open_to if offer["add_all"] and way["id"] == offer["add_all"]]
        marked = [way for way in open_to if way["guess"]]
        more = [way for way in open_to if way["direction"] == MORE]
        less = [way for way in open_to if way["direction"] == LESS]
        way = (said or marked or ([] if more and less else open_to) or [None])[0]
        if way is not None:
            took[offer["target"]] = way["id"]
            rests[offer["target"]] = " ".join(f"{s['start']}-{s['end']}" for s in offer["spans"])
    read_in = [
        offer["target"]
        for offer in found["suggestions"]
        if not offer["by_name"] and offer["target"] in took
    ]
    for target in read_in:
        shares = [other for other in read_in if rests[other] == rests[target]]
        kept = next((one for one in shares if one in guessed(found)), shares[0])
        if len(shares) > 1 and target != kept:
            del took[target]
    return took


# --- By itself, as it was -----------------------------------------------------------------

BY_ITSELF = [
    ("somewhere posh", SMART),
    ("I want somewhere posh", SMART),
    ("a posh area with good pubs", SMART | {PUBS: [MORE, LESS]}),
    ("posh, leafy and quiet", LEAFY_TOO),
    ("Somewhere affluent", SMART),
    ("cheap and cheerful", {MIX: [LESS]}),
    ("somewhere on the up", {RISE_5: [MORE], RISE_10: [MORE]}),
]


@pytest.mark.parametrize(("text", "each"), BY_ITSELF)
def test_a_word_that_is_read_several_ways_gives_one_way_of_each_reading(
    client: TestClient, text: str, each: dict[str, list[str]]
):
    found = read(client, text)

    assert ways(found) == each
    assert waits(found) == WAITS & set(each)
    # The words name none of them, and none is marked as the way Burro guesses.
    assert not set(guessed(found)) & READ_IN


# --- Beside what is said of the words alone -----------------------------------------------

# What was typed, the same words with nothing said of them, and what is offered of both.
BESIDE_AN_ASIDE = [
    ("somewhere posh, honestly", "somewhere posh", SMART),
    ("Somewhere affluent, honestly", "Somewhere affluent", SMART),
    ("honestly, somewhere posh", "somewhere posh", SMART),
    ("Honestly, I want somewhere posh", "I want somewhere posh", SMART),
    ("somewhere upmarket, I guess", "somewhere upmarket", SMART),
    ("somewhere well heeled, I suppose", "somewhere well heeled", SMART),
    ("to be honest, somewhere posh", "somewhere posh", SMART),
    ("somewhere posh, if possible", "somewhere posh", SMART),
    ("I think, somewhere posh, ideally", "somewhere posh", SMART),
    ("Short version: somewhere posh", "somewhere posh", SMART),
    ("slightly affluent, I think", "slightly affluent", SMART),
    (
        "a posh area with good pubs, honestly",
        "a posh area with good pubs",
        SMART | {PUBS: [MORE, LESS]},
    ),
    (
        "posh, leafy and quiet, I think",
        "posh, leafy and quiet",
        LEAFY_TOO,
    ),
    ("somewhere cheap and cheerful, I think", "somewhere cheap and cheerful", {MIX: [LESS]}),
    ("honestly, unpretentious", "unpretentious", {MIX: [LESS]}),
    ("somewhere on the up, hopefully", "somewhere on the up", {RISE_5: [MORE], RISE_10: [MORE]}),
    # No mark sets it apart: a person types as they speak.
    ("somewhere posh I think", "somewhere posh", SMART),
    ("honestly somewhere posh", "somewhere posh", SMART),
    ("I think I want somewhere posh", "I want somewhere posh", SMART),
]


@pytest.mark.parametrize(("text", "alone", "each"), BESIDE_AN_ASIDE)
def test_beside_what_is_said_of_the_words_alone_it_is_offered_as_it_is_by_itself(
    client: TestClient, text: str, alone: str, each: dict[str, list[str]]
):
    found, by_itself = read(client, text), read(client, alone)

    assert ways(found) == each
    assert ways(found) == ways(by_itself)
    assert guessed(found) == guessed(by_itself) and not set(guessed(found)) & READ_IN
    # What an offer says of itself is as it was, and so is what it is called.
    for target, offer in offered(found).items():
        same = offered(by_itself)[target]
        for part in ("label", "does", "follows", "note", "by_name", "only_by_choice", "needs"):
            assert offer[part] == same[part], (target, part)
    assert waits(found) == WAITS & set(each)
    # A client that asks nothing takes what it takes of the word by itself, and ranks.
    assert taken(found) == taken(by_itself)
    assert taken(found)


# What was typed, and the same words with nothing said of them. The rules offer the word
# every way of the second, for what stands beside it, so it is offered every way of both.
AS_IT_IS_WITHOUT = [
    # A sentence beside it that the rules do not know, which may be said of it.
    ("Moving next month. Somewhere posh, honestly.", "Moving next month. Somewhere posh."),
    ("Posh but not stuffy, honestly", "Posh but not stuffy"),
    ("somewhere posh, honestly, near a good bakery", "somewhere posh, near a good bakery"),
]


@pytest.mark.parametrize(("text", "without"), AS_IT_IS_WITHOUT)
def test_it_is_offered_no_otherwise_than_the_rules_offer_it_of_the_same_words(
    client: TestClient, text: str, without: str
):
    found, by_itself = read(client, text), read(client, without)

    assert {target: held for target, held in ways(found).items() if target in SMART} == EITHER_WAY
    assert ways(found) == ways(by_itself)
    assert not taken(found).keys() & set(SMART)


def test_the_word_is_offered_one_way_beside_a_thing_whose_way_the_rules_do_not_mark(
    client: TestClient,
):
    """What is made of the thing beside it is as it was: one way, and no guess."""
    found = read(client, "somewhere posh ideally, leafy and quiet")

    assert ways(found) == LEAFY_TOO
    assert waits(found) == WAITS
    assert not set(guessed(found)) & READ_IN


@pytest.mark.parametrize("text", ["somewhere posh, honestly", "Somewhere affluent, honestly"])
def test_the_areas_are_ranked_that_were_not(client: TestClient, text: str):
    """Nothing was taken of either sentence, so the person was shown no areas."""
    found = read(client, text)

    assert taken(found) == {MIX: MORE}
    [offer] = [one for one in found["suggestions"] if one["target"] == MIX]
    [way] = [one for one in offer["choices"] if one["id"] == MORE]
    body = {"spec": found["spec"], "operations": way["operations"], "limit": 30}
    ranked = client.post("/v1/rank", json=body).json()["data"]
    assert ranked["rejected"] == []
    assert len(ranked["ranked"]) > 1
    [held] = [one for one in ranked["spec"]["weights"] if one["feature_id"] == "brand_mix"]
    assert (held["direction"], held["weight"] > 0) == (MORE, True)


# --- What may turn it, put it in doubt or give it to somebody else ------------------------

IN_DOUBT = [
    # A word that turns leads up to it.
    "not posh",
    "not posh, honestly",
    "honestly, nowhere posh",
    "anything but posh",
    "I hate posh areas",
    # What turns it stands beyond a mark, or in the sentence after it.
    "posh? no thanks",
    "somewhere posh, no thanks",
    "somewhere posh, not really",
    "somewhere posh. Not really.",
    "somewhere posh, I don't think",
    # It asks.
    "is it posh, honestly?",
    # A sign of doubt stands with it.
    "maybe somewhere posh, honestly",
    # Words the rules do not know stand with it, or beyond a mark beside it.
    "somewhere posh would finish me off, honestly",
    "somewhere posh, bleh",
    "somewhere posh, honestly, bleh",
    "honestly bleh, somewhere posh",
    # More is said of it than what is said of the words alone, in words the rules do not
    # know: what is said next may be said of it too.
    "Posh but not stuffy, honestly",
    "Honestly, I'm tired of the city and want somewhere posh",
    "somewhere posh I think not",
]


@pytest.mark.parametrize("text", IN_DOUBT)
def test_what_may_turn_it_or_put_it_in_doubt_leaves_it_as_it_was(client: TestClient, text: str):
    found = read(client, text)

    held = ways(found)
    assert set(held) == set(SMART)
    # No way of it is offered alone that counts the word as it would count by itself.
    for target, one_way in SMART.items():
        assert held[target] != one_way, target
    assert not guessed(found)
    assert not taken(found)


@pytest.mark.parametrize(
    "text",
    [
        "my sister wants somewhere posh",
        "my sister wants somewhere posh, honestly",
        "honestly, my mum is after somewhere affluent",
    ],
)
def test_a_wish_that_may_be_somebody_elses_waits_for_the_person(client: TestClient, text: str):
    found = read(client, text)

    assert ways(found) == EITHER_WAY
    assert waits(found) == set(SMART)
    assert not guessed(found) and not taken(found)
    for target in set(SMART) - WAITS:
        assert NOT_SAID_TO_BE_WANTED in offered(found)[target]["note"]
