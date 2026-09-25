"""What "add all" may add at one press, and the ways code makes for each thing.

"Add all" presses for the person, so it takes less than a person may. It
adds a wish or a vibe at a mention or a small step, a journey as a guide to
a place named in full, and what a person plainly said of the home they look
for: that they are renting or buying, the kind of home, and the budget as
they worded it, firm where they used a firm word. A journey that was plainly
said, to one place and with one time, is offered both ways whoever read it,
and one press takes the guide. It never adds a journey as a firm limit, a
rule for an area, what runs two ways with no guess, a journey to a place that
is yet to be chosen, or recorded crime.
"""

import copy
import dataclasses
from functools import cache
from typing import Any

import pytest
from burro_api.guard import plainly_said
from burro_api.offers import (
    FIRM,
    GUIDE,
    LESS,
    MORE,
    OFF,
    Degree,
    changes,
    of_the_rules,
    ways_of,
)
from burro_api.typed import Typed
from burro_core import RuleInterpreter
from burro_core.catalogue import FEATURES, HOLDS_CRIME, TAGS
from burro_core.grammar import Grammar
from burro_core.ids import Dimension, FeatureId, Polarity, Segment, TagId, TagShape, Tenure
from burro_core.interpret import InterpretRequest
from burro_core.places import Names
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
    scorer,
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


@cache
def _served_once() -> list[tuple[str, dict[str, Any]]]:
    """Every answer on disk, as route 1 serves it. Served once, for the first test that asks.

    Every process that runs tests imports this file, and one of them runs its tests.
    Served as the file was imported, every answer was served again in every process.
    """
    found: list[tuple[str, dict[str, Any]]] = []
    for (case, look), row in answers_on_disk().items():
        if "output" in row:
            found.append((f"{case} look {look}", served_again(case, look)[0]))
    return found


def every_answer() -> list[tuple[str, dict[str, Any]]]:
    """Every answer on disk, as route 1 serves it: a copy that is the test's own.

    What is served once is handed to no test. A test that changes what it was handed
    changes its copy, and nothing that the next test reads.
    """
    return copy.deepcopy(_served_once())


def test_a_test_that_changes_what_it_was_handed_changes_nothing_the_next_reads():
    handed = every_answer()
    before = repr(handed)
    handed[0][1]["suggestions"] = "changed by a test"
    del handed[1:]

    assert repr(every_answer()) == before and len(every_answer()) > 100


# --- What it never adds --------------------------------------------------------------------


def test_add_all_never_adds_a_journey_as_a_firm_limit_or_a_rule_for_an_area():
    # A journey is estimated from distance, so one press leaves no area out on one.
    for case, found in every_answer():
        for way in taken(found):
            edits = way["operations"]
            assert not [e for e in edits["commute_ops"] if e["strictness"] == "hard"], case
            assert edits["area_ops"] == [], case


def test_add_all_adds_a_firm_budget_only_where_it_is_the_guess():
    firm = 0
    for case, found in every_answer():
        for way in taken(found):
            if any(edit["strictness"] == "hard" for edit in way["operations"]["budget_ops"]):
                assert way["guess"], case
                firm += 1
    assert firm


def test_add_all_never_adds_recorded_crime():
    for case, found in every_answer():
        for way in taken(found):
            for wish in way["operations"]["weight_ops"]:
                assert FEATURES[FeatureId(wish["feature_id"])].dimension is not Dimension.CRIME
            for tag in way["operations"]["tag_ops"]:
                assert TagId(tag["tag_id"]) not in HOLDS_CRIME, case


def test_add_all_never_adds_a_thing_that_runs_two_ways_with_no_guess():
    for case, found in every_answer():
        for offer in found["suggestions"]:
            ways = [way for way in offer["choices"] if way["id"] != "ignore"]
            if offer["add_all"] and len(ways) > 1:
                assert any(way["guess"] for way in ways), case


def test_add_all_never_adds_a_journey_to_a_place_that_is_yet_to_be_chosen():
    for case, found in every_answer():
        for offer in found["suggestions"]:
            assert not (offer["asks_place"] and offer["add_all"]), case
        for way in taken(found):
            assert all(edit["place_id"] for edit in way["operations"]["commute_ops"]), case


def test_add_all_never_sets_a_number_for_a_weight():
    for case, found in every_answer():
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


def test_where_the_guess_is_a_firm_journey_add_all_adds_the_guide():
    found, _ = served_again("own-003", before=UNREAD_FIRST)

    [journey] = found["suggestions"]
    assert [way["id"] for way in journey["choices"] if way["guess"]] == [FIRM]
    assert journey["add_all"] == GUIDE
    assert journey["needs"] == "the journey can be made a firm limit"


# What a newcomer types of the home they look for, after what they want of the place.
A_BUYER = (
    "Somewhere quiet, with access to parks, slightly affluent, with a real identity. "
    "At most 35-40min commute from Pellam Exchange. "
    "If I'm buying, max \N{POUND SIGN}400k for a 1 bed flat."
)
# A model that reads what is wanted of the place and the journey, and nothing of the home.
READS_THE_PLACE = model_output(
    commute_ops=[
        model_commute(
            destination_text="Pellam Exchange",
            max_minutes=40,
            strictness="hard",
            words="At most 35-40min commute from Pellam Exchange",
        )
    ],
    weight_ops=[model_weight("park_proximity", words="access to parks")],
    tag_ops=[model_tag("quiet_residential", words="somewhere quiet")],
)
OF_A_HOME = ("Buying", "A budget of \N{POUND SIGN}400,000", "A flat")


def by_the_rules(text: str) -> dict[str, Any]:
    response = client_for(make_deps()).post("/v1/interpret", json={"text": text})
    assert response.status_code == 200
    return response.json()["data"]


def guesses(found: dict[str, Any]) -> dict[str, str]:
    """The way of each offer that is Burro's guess, by the offer's label."""
    return {
        offer["label"]: way["id"]
        for offer in found["suggestions"]
        for way in offer["choices"]
        if way["guess"]
    }


def pressed(found: dict[str, Any]) -> dict[str, str]:
    """The way of each offer that one press takes, by the offer's label."""
    return {o["label"]: o["add_all"] for o in found["suggestions"] if o["add_all"]}


@pytest.mark.parametrize("reads", [None, READS_THE_PLACE], ids=["the rules alone", "a model"])
def test_what_is_plainly_said_of_a_home_carries_the_guess_and_one_press_takes_it(
    reads: dict[str, Any] | None,
):
    found = by_the_rules(A_BUYER) if reads is None else through_the_route(reads, A_BUYER)

    for each in (guesses(found), pressed(found)):
        assert {label: each.get(label) for label in OF_A_HOME} == dict.fromkeys(OF_A_HOME, MORE)
    # The home is said with what Burro cannot hold of it, and is taken all the same.
    flat = next(offer for offer in found["suggestions"] if offer["label"] == "A flat")
    assert "not by the number of bedrooms" in flat["note"]
    assert found["applied"] == []


def test_with_a_model_one_press_takes_what_it_read_and_what_was_plainly_said_of_the_home():
    found = through_the_route(READS_THE_PLACE, A_BUYER)

    assert pressed(found) == {
        "Quiet streets": MORE,
        "Nearer a park": MORE,
        "Pellam Exchange": GUIDE,
        **dict.fromkeys(OF_A_HOME, MORE),
    }
    journey = next(offer for offer in found["suggestions"] if offer["target"] == "commute")
    assert [way["id"] for way in journey["choices"] if way["guess"]] == [FIRM]


@pytest.mark.parametrize("reads", [None, READS_THE_PLACE], ids=["the rules alone", "a model"])
def test_one_press_never_takes_a_reading_the_rules_keep_for_themselves(
    reads: dict[str, Any] | None,
):
    found = by_the_rules(A_BUYER) if reads is None else through_the_route(reads, A_BUYER)

    of_a_wish = [o for o in found["suggestions"] if o["target"] not in ("budget", "commute")]
    kept = [offer for offer in of_a_wish if offer["note"]]
    # Four readings of "affluent" and three of "a real identity".
    assert len(kept) == 7
    assert [offer["add_all"] for offer in kept] == [""] * len(kept)
    assert not any(way["guess"] for offer in kept for way in offer["choices"])


def _firmness(found: dict[str, Any]) -> list[str]:
    """How firm each budget is that one press takes."""
    return [
        edit["strictness"]
        for offer in found["suggestions"]
        for way in offer["choices"]
        if offer["add_all"] and way["id"] == offer["add_all"]
        for edit in way["operations"]["budget_ops"]
        if edit["amount"]
    ]


@pytest.mark.parametrize(
    ("text", "firm"),
    [
        ("Honestly, max \N{POUND SIGN}400k", True),
        ("Honestly, up to \N{POUND SIGN}1,700 a month", True),
        ("Honestly, no more than \N{POUND SIGN}1,700 a month", True),
        ("Honestly, about \N{POUND SIGN}600k", False),
        ("Honestly, \N{POUND SIGN}1,700 a month", False),
        ("Honestly, under \N{POUND SIGN}1,700 a month", False),
    ],
)
def test_one_press_takes_a_budget_as_the_person_worded_it(text: str, firm: bool):
    amount = next(word for word in text.split() if word.startswith("\N{POUND SIGN}"))
    number = 1000 * int(amount[1:-1]) if amount.endswith("k") else int(amount[1:].replace(",", ""))
    read = model_output(budget_ops=[model_budget(amount=number, strictness="hard", words=text)])

    by_rules, by_model = by_the_rules(text), through_the_route(read, text)

    # The rules offer it one way, as it was worded. A model's reading is offered both
    # ways, and the way the words make it is the guess, whatever the model called it.
    assert _firmness(by_rules) == (["hard"] if firm else ["unchanged"])
    assert _firmness(by_model) == (["hard"] if firm else ["soft"])
    assert list(pressed(by_model).values()) == [FIRM if firm else GUIDE]
    assert guesses(by_model) == pressed(by_model) and guesses(by_rules) == pressed(by_rules)


@pytest.mark.parametrize(
    ("text", "plain"),
    [
        # It says which of renting and buying the rest is said of, and is no doubt.
        ("If I'm buying, max \N{POUND SIGN}400k", ["Buying", "A budget of \N{POUND SIGN}400,000"]),
        ("If I rent, \N{POUND SIGN}1,700 a month", ["Renting", "A budget of £1,700 a month"]),
        # One case set against another names two tenures and two amounts.
        ("If I rent, up to \N{POUND SIGN}1,700 a month; if I buy, max \N{POUND SIGN}400k", []),
        # Core lists these as doubt.
        ("Renting if I must, honestly", []),
        ("If I could buy, honestly", []),
    ],
)
def test_an_if_is_no_doubt_until_it_sets_one_case_against_another(text: str, plain: list[str]):
    found = by_the_rules(text)

    assert found["suggestions"] and found["applied"] == []
    assert list(guesses(found)) == plain and list(pressed(found)) == plain


# "My partner wants to buy" gives buying to someone else, and the words name both tenures.
PARTNERS = "my partner wants to buy but I'd rather rent, max \N{POUND SIGN}400k"


@pytest.mark.parametrize(
    "reads",
    [
        None,
        model_output(
            budget_ops=[
                model_budget(
                    tenure="buy",
                    amount=400000,
                    strictness="hard",
                    words="max \N{POUND SIGN}400k",
                )
            ]
        ),
        model_output(
            budget_ops=[model_budget(tenure="buy", words="my partner wants to buy")],
        ),
    ],
    ids=["the rules alone", "a model that reads the budget", "a model that reads the tenure"],
)
def test_one_press_takes_nothing_about_buying_that_is_somebody_elses_wish(
    reads: dict[str, Any] | None,
):
    found = by_the_rules(PARTNERS) if reads is None else through_the_route(reads, PARTNERS)

    # All of it is offered, each by its own button, and none is Burro's guess.
    offered = [
        edit
        for offer in found["suggestions"]
        for way in offer["choices"]
        for edit in way["operations"]["budget_ops"]
    ]
    assert {edit["tenure"] for edit in offered} >= {"buy", "rent"}
    assert 400000 in {edit["amount"] for edit in offered}
    assert guesses(found) == {} and pressed(found) == {}


@pytest.mark.parametrize(
    "text",
    [
        "Honestly, my mum is buying a flat for about \N{POUND SIGN}300k",
        "My partner wants to buy, max \N{POUND SIGN}400k",
        "Honestly, renting or buying, a flat",
        "Honestly, she is buying",
        "Would I be better off buying a flat?",
    ],
)
def test_nothing_of_a_home_is_the_guess_where_whose_it_is_or_which_is_in_doubt(text: str):
    found = by_the_rules(text)

    assert found["suggestions"] and guesses(found) == {} and pressed(found) == {}


@pytest.mark.parametrize(
    "text",
    [
        "Honestly between \N{POUND SIGN}1500 and \N{POUND SIGN}1800 a month",
        "Honestly, \N{POUND SIGN}1,700 a month, \N{POUND SIGN}1,800 tops",
    ],
)
def test_two_amounts_are_no_budget_to_take_at_one_press(text: str):
    found = by_the_rules(text)

    assert len(found["suggestions"]) == 2
    assert guesses(found) == {} and pressed(found) == {}


def test_to_press_every_guess_of_the_rules_does_the_opposite_of_no_case_that_is_held():
    # Held to the words alone, six were: "I earn 60k" and "I have a 50k deposit" as a
    # budget, and "I'm done renting" and three like it as the tenure that is left.
    score = scorer()
    held = score.load_release(None)
    names, grammar, rules = score.Names(held), Grammar(Names(held), held), RuleInterpreter()
    outcomes: dict[str, list[str]] = {}
    for folder in (score.CASES, score.CASES.parent / "answers" / "cases"):
        cases, problems = score.load_cases(folder, held)
        assert not problems
        for case in cases:
            asked = InterpretRequest(text=case.text, spec=case.start, release=held)
            read = rules.interpret(asked)
            noticed = [of_the_rules(suggestion) for suggestion in read.suggestions]
            marked = plainly_said(noticed, Typed(case.text, grammar, held), case.start)
            if any(way.guess for offer in marked for way in offer.choices):
                outcome, _ = score.offer_of(case, read.replace(suggestions=marked), held, names)
                outcomes.setdefault(outcome.value, []).append(case.id)

    assert set(outcomes) <= {"right", "partial", "not_read"}, outcomes
    assert "budget-030" in outcomes["partial"] and "whole-035" in outcomes["partial"]
    assert sum(len(cases) for cases in outcomes.values()) >= 40


def test_two_amounts_leave_what_was_said_of_the_tenure_and_the_home_plain():
    found = by_the_rules("Honestly, buying a flat, \N{POUND SIGN}400k or \N{POUND SIGN}450k")

    assert list(pressed(found)) == ["Buying", "A flat"] == list(guesses(found))


# --- A journey that was plainly said ---------------------------------------------------------

# The founder's own sentence, to a place of the made-up city.
THE_FOUNDERS = (
    "I want to live somewhere quiet, with access to parks, slightly affluent but with some "
    "culture around it, something with a real identity. "
    "At most 35-40min commute from Pellam Exchange. "
    "If I'm buying, max \N{POUND SIGN}400k for a 1 bed flat."
)
LONGER_TAKEN = "You gave 35 to 40 minutes. Burro has taken the longer."


def journeys(found: dict[str, Any]) -> list[dict[str, Any]]:
    return [offer for offer in found["suggestions"] if offer["target"] == "commute"]


def ways_of_a_journey(offer: dict[str, Any]) -> list[tuple[str, bool, int, str, str]]:
    """Each way of a journey: which it is, whether it is the guess, and what it would send."""
    return [
        (way["id"], way["guess"], edit["max_minutes"], edit["strictness"], edit["mode"])
        for way in offer["choices"]
        for edit in way["operations"]["commute_ops"]
    ]


def after_one_press(found: dict[str, Any]) -> dict[str, Any]:
    """The ranking that follows one press of the one button, and no other press."""
    edits: dict[str, list[Any]] = {}
    for way in taken(found):
        for group, held in way["operations"].items():
            edits.setdefault(group, []).extend(held)
    # A press that takes nothing sends no edit: the search is ranked as it stands.
    body = {"spec": found["spec"], "limit": 5} | ({"operations": edits} if edits else {})
    ranked = client_for(make_deps()).post("/v1/rank", json=body)
    assert ranked.status_code == 200
    return ranked.json()["data"]


def test_by_the_rules_alone_one_press_takes_a_journey_that_was_plainly_said_as_a_guide():
    found = by_the_rules(THE_FOUNDERS)

    [journey] = journeys(found)
    # It is offered both ways. "At most" makes the limit firm, so the firm limit is the
    # guess. Of "35-40min" the longer is taken, as the rules take it, and the offer says so.
    assert ways_of_a_journey(journey) == [
        (FIRM, True, 40, "hard", "unchanged"),
        (GUIDE, False, 40, "soft", "unchanged"),
    ]
    assert journey["note"] == LONGER_TAKEN
    # One press takes the guide, and a person makes it firm with a press of its own.
    assert journey["add_all"] == GUIDE
    assert journey["needs"] == "the journey can be made a firm limit"
    assert pressed(found) == {
        "Quiet streets": MORE,
        "More culture nearby": MORE,
        "Pellam Exchange": GUIDE,
        **dict.fromkeys(OF_A_HOME, MORE),
    }
    assert found["applied"] == []
    # The search then holds the journey as a guide, and no area is left out on it.
    ranked = after_one_press(found)
    assert ranked["rejected"] == []
    [held] = ranked["spec"]["commutes"]
    assert (held["max_minutes"], held["strictness"], held["mode"]) == (40, "soft", "pt")
    assert (ranked["spec"]["tenure"], ranked["spec"]["budget"]["strictness"]) == ("buy", "hard")
    assert {one["reason"] for one in ranked["filtered"]} <= {"over_budget"}


def test_a_journey_the_rules_read_is_offered_as_a_model_s_reading_of_it_is():
    by_rules, by_model = by_the_rules(A_BUYER), through_the_route(READS_THE_PLACE, A_BUYER)

    [ours], [theirs] = journeys(by_rules), journeys(by_model)
    assert ways_of_a_journey(ours) == ways_of_a_journey(theirs)
    for part in ("label", "does", "follows", "add_all", "needs", "spans"):
        assert ours[part] == theirs[part], part
    assert [way["label"] for way in ours["choices"]] == [way["label"] for way in theirs["choices"]]


@pytest.mark.parametrize(
    ("text", "ways"),
    [
        # No word makes it a limit: the guide is the guess.
        (
            "Honestly, 40 minutes to Pellam Exchange",
            [(GUIDE, True, 40, "soft", "unchanged"), (FIRM, False, 40, "hard", "unchanged")],
        ),
        # "Within" makes a journey firm, and the way of travelling is the one that was said.
        (
            "Honestly, within 30 minutes of Pellam Exchange by bike",
            [(FIRM, True, 30, "hard", "cycle"), (GUIDE, False, 30, "soft", "cycle")],
        ),
        # A range is a limit at its longer end, with no word against it.
        (
            "Honestly, 35-40 minutes to Pellam Exchange",
            [(FIRM, True, 40, "hard", "unchanged"), (GUIDE, False, 40, "soft", "unchanged")],
        ),
    ],
)
def test_a_journey_carries_the_guess_on_the_way_its_words_give_and_is_taken_as_a_guide(
    text: str, ways: list[tuple[str, bool, int, str, str]]
):
    found = by_the_rules(text)

    [journey] = journeys(found)
    assert ways_of_a_journey(journey) == ways
    assert journey["add_all"] == GUIDE
    [held] = after_one_press(found)["spec"]["commutes"]
    assert (held["max_minutes"], held["strictness"]) == (ways[0][2], "soft")
    assert held["mode"] == ("cycle" if "bike" in text else "pt")


@pytest.mark.parametrize(
    "text",
    [
        # It may be where the person lives now.
        "Honestly, I commute from Pellam Exchange",
        # Two places, and one time between them.
        "Honestly, max 30 mins to Pellam Exchange or Pellam Cross",
        "Honestly, maybe 30 minutes to Pellam Exchange",
        "Is 30 minutes to Pellam Exchange too far?",
        "30 minutes to Pellam Cross by bike is too long",
        # Two times, and which is meant is the person's to say.
        "Honestly, 30-45 minutes to Pellam Exchange, no more than 40",
        "Honestly, at most 30 minutes to Pellam Exchange, ideally 20",
        # A number that may be a least is never taken as a most.
        "Honestly, at least 30 minutes from Pellam Exchange",
        "Honestly, not within 30 minutes of Pellam Exchange",
        "Honestly, further than 30 minutes from Pellam Exchange",
    ],
)
def test_a_journey_that_was_not_plainly_said_carries_no_guess(text: str):
    found = by_the_rules(text)

    assert not [way for offer in journeys(found) for way in offer["choices"] if way["guess"]]
    assert not [
        edit
        for way in taken(found)
        for edit in way["operations"]["commute_ops"]
        if edit["strictness"] == "hard" or edit["max_minutes"]
    ]


def test_a_journey_with_no_time_is_offered_as_it_was():
    found = by_the_rules("Honestly, I work at Pellam Infirmary")

    [journey] = journeys(found)
    # One place and no time: there is no limit to be firm, and one way to take it.
    assert ways_of_a_journey(journey) == [(MORE, False, 0, "unchanged", "unchanged")]
    assert journey["add_all"] == MORE


def test_a_journey_the_rules_read_is_the_guess_whether_or_not_a_model_reads():
    quiet = model_output(tag_ops=[model_tag("quiet_residential", words="somewhere quiet")])

    found = through_the_route(quiet, A_BUYER)

    [journey] = journeys(found)
    assert [way["id"] for way in journey["choices"] if way["guess"]] == [FIRM]
    assert journey["add_all"] == GUIDE and journey["read_by"] == "rule"
    assert pressed(found)["Pellam Exchange"] == GUIDE


# --- A place to stay away from, and a place that is somebody else's --------------------------

NO_STAYING_AWAY = "Burro cannot rank on being far from a place."
# Each asks to live away from a place, in words the rules once read as a journey to it.
AWAY_FROM_IT = (
    # Found on 2026-09-25: one press added a journey to the place.
    "my ex lives at Pellam Exchange, 30 minutes away at least",
    "Pellam Exchange, at least 30 minutes away",
    "Pellam Exchange, but far from it",
    "Honestly, over 30 minutes from Pellam Exchange",
    "as far as possible from Pellam Exchange",
    "I want to live far from my ex, who lives at Pellam Exchange",
    "Honestly, 30 minutes from Pellam Exchange at least",
    "Honestly, Pellam Exchange is where my ex is, so well away from there",
    "Honestly, I need to get away from Pellam Exchange",
    "Honestly, Pellam Exchange, and nowhere near it",
    "Honestly, a minimum of 30 minutes from Pellam Exchange",
    "Honestly, 30 minutes or more from Pellam Exchange",
    # Lines that no mark ends are read together.
    "Honestly,\nfar from\nPellam Exchange",
)
# Each names a place with a word for staying away before it. The rules offered nothing, and
# said nothing of why.
TURNED_AWAY = (
    "Honestly, at least 30 minutes from Pellam Exchange",
    "Honestly, no less than 30 minutes from Pellam Exchange",
    "Honestly, more than 30 minutes from Pellam Exchange",
    "Honestly, far from Pellam Exchange",
    "Honestly, well away from Pellam Exchange",
    "Honestly, not near Pellam Exchange",
    "Honestly, nowhere near Pellam Exchange",
    "Honestly, avoid Pellam Exchange",
)
# Each names a place as where somebody else lives, works or goes, or as one that was left.
SOMEBODY_ELSES = (
    "my ex lives at Pellam Exchange",
    "my ex works at Pellam Infirmary",
    "my mum lives near Pellam Exchange",
    "Honestly, my boss lives by Pellam Exchange",
    "Honestly, his mother is at Pellam Infirmary",
    "Honestly, her brother goes to Pellam Infirmary",
    "my mate works at Pellam Infirmary, not me",
    # "She" is nobody the words name.
    "Honestly, she's at Pellam Infirmary",
    # Of the household, and where they live, which is no place they go to.
    "my partner lives at Pellam Exchange",
    "we moved from Pellam Exchange",
)
# Each is a place the person or their household must reach, and is taken as it was.
TO_BE_REACHED = (
    "my partner works at Pellam Infirmary",
    "my kids' school is Pellam Infirmary",
    "my wife works at Pellam Infirmary, 30 minutes max",
    "my husband commutes to Pellam Exchange",
    "Honestly, I work at Pellam Infirmary",
    "Honestly, my boss and I work at Pellam Infirmary",
    "we both work in Pellam Cross",
    "Honestly, my partner is at Pellam Infirmary",
    "Honestly, close to Pellam Exchange",
    "not far from Pellam Exchange",
    "no more than 30 minutes from Pellam Exchange",
)
# Each holds a word for far or for a least that a word before it turns round: it says near,
# or says the most a journey may take. The journey is offered as it was.
TURNED_ROUND = (
    "My commute to Pellam Exchange can't be more than 45 minutes",
    "I'll be at Pellam Infirmary, so ideally neither of us is more than 40 minutes away",
    "Pellam Infirmary, and I don't want to move far",
    "Pellam Exchange can't be far",
)


def wrongly(text: str) -> dict[str, Any]:
    """A model's answer that reads the place of a sentence as a journey to it, and firmly."""
    name = next(name for name in ("Pellam Exchange", "Pellam Infirmary") if name in text)
    minutes = 30 if "30" in text else 0
    read = model_commute(
        destination_text=name,
        max_minutes=minutes,
        strictness="hard" if minutes else "unchanged",
        words=text,
    )
    return model_output(commute_ops=[read])


def nothing_of_a_journey_is_taken(found: dict[str, Any]) -> None:
    assert found["applied"] == [] and found["operations"]["commute_ops"] == []
    assert not [way for offer in journeys(found) for way in offer["choices"] if way["guess"]]
    assert [offer["add_all"] for offer in journeys(found)] == [""] * len(journeys(found))
    assert not [way for way in taken(found) if way["operations"]["commute_ops"]]
    assert after_one_press(found)["spec"]["commutes"] == []


@pytest.mark.parametrize("text", [*AWAY_FROM_IT, *TURNED_AWAY])
@pytest.mark.parametrize("reader", ["the rules alone", "a model that reads it wrongly"])
def test_a_place_to_stay_away_from_is_never_a_journey_to_it(text: str, reader: str):
    wrong = reader != "the rules alone"
    found = through_the_route(wrongly(text), text) if wrong else by_the_rules(text)

    nothing_of_a_journey_is_taken(found)
    # No way of it can be pressed at all: Burro cannot rank on being far from a place, and
    # the offer says so in one sentence.
    [journey] = journeys(found)
    assert [way["id"] for way in journey["choices"]] == ["ignore"]
    assert journey["does"] == "Burro took no journey from these words."
    assert (journey["note"], journey["follows"], journey["said"]) == (NO_STAYING_AWAY, "", [])


@pytest.mark.parametrize("text", SOMEBODY_ELSES)
@pytest.mark.parametrize("reader", ["the rules alone", "a model that reads it wrongly"])
def test_a_place_that_is_somebody_elses_is_offered_and_never_taken_by_one_press(
    text: str, reader: str
):
    wrong = reader != "the rules alone"
    found = through_the_route(wrongly(text), text) if wrong else by_the_rules(text)

    nothing_of_a_journey_is_taken(found)
    # It is offered by a button of its own: the person may have to reach it all the same.
    [journey] = journeys(found)
    assert len([way for way in journey["choices"] if way["id"] != "ignore"]) >= 1


@pytest.mark.parametrize("text", TO_BE_REACHED)
def test_a_place_the_household_must_reach_is_taken_as_it_was(text: str):
    found = by_the_rules(text)

    if found["status"] == "ok":
        # A plain prompt, which the rules apply.
        assert [edit["place_id"] != "" for edit in found["operations"]["commute_ops"]] == [True]
        return
    [journey] = journeys(found)
    assert journey["add_all"] in (MORE, GUIDE) and journey["note"] in ("", LONGER_TAKEN)
    [held] = after_one_press(found)["spec"]["commutes"]
    assert held["strictness"] == "soft"


@pytest.mark.parametrize("text", TURNED_ROUND)
def test_a_word_for_far_that_is_turned_round_is_no_wish_to_stay_away(text: str):
    found = by_the_rules(text)

    # The journey is offered as it was, and says nothing of staying away. One press takes
    # it or leaves it as before: it leaves it where its own clause holds a sign of doubt.
    [journey] = journeys(found)
    assert [way["id"] for way in journey["choices"]] == [MORE, "ignore"]
    assert journey["note"] == ""
    assert journey["add_all"] == ("" if "can't" in text else MORE)
    assert found["applied"] == []


@pytest.mark.parametrize("text", [*AWAY_FROM_IT, *TURNED_AWAY, *SOMEBODY_ELSES])
def test_no_such_place_is_applied_from_a_prompt_that_is_typed_alone(text: str):
    alone = text.removeprefix("Honestly, ")

    found = by_the_rules(alone)

    assert found["operations"]["commute_ops"] == []
    assert not [one for one in found["applied"] if one["group"] == "commute_ops"]


# --- A house, of no kind that was named ------------------------------------------------------

KINDS_OF_HOUSE = ["terraced", "semi_detached", "detached"]
A_HOUSE = "buying a house, about \N{POUND SIGN}600k, near a station"
A_HOUSE_IN_MORE = "If I'm buying, max \N{POUND SIGN}400k for a house"
A_TERRACED_HOUSE = (
    "You named no kind of house, so Burro has taken a terraced house, the least dear kind "
    "in most areas. Semi-detached and detached are one press away."
)


def budget_of(found: dict[str, Any]) -> dict[str, Any]:
    [budget] = [o for o in found["suggestions"] if o["label"].startswith("A budget of")]
    return budget


def held_to(found: dict[str, Any]) -> list[tuple[str, int, str, str]]:
    """Every way of every offer that holds an amount: its id, and what it is held against."""
    held: list[tuple[str, int, str, str]] = []
    for offer in found["suggestions"]:
        for way in offer["choices"]:
            edits = way["operations"]["budget_ops"]
            amounts = [edit for edit in edits if edit["amount"]]
            kinds = [edit["segment"] for edit in edits if edit["segment"] != "unchanged"]
            if amounts:
                held.append((way["id"], amounts[0]["amount"], kinds[-1], amounts[0]["strictness"]))
    return held


def test_a_house_that_is_plainly_said_is_applied_as_a_terraced_house_and_said_to_be_assumed():
    found = by_the_rules(A_HOUSE)

    # No press is asked for: the sentence is applied whole, as it was before a house was
    # asked about, and the budget is no longer held against what flats sold for.
    assert (found["status"], found["suggestions"]) == ("ok", [])
    held = found["spec"]["budget"]
    assert (found["spec"]["tenure"], held["amount"], held["segment"]) == ("buy", 600000, "terraced")
    assert held["strictness"] == "soft"
    # The kind is Burro's, and the answer says so, as it says of a way of travelling.
    [budget] = [at for at, edit in enumerate(found["operations"]["budget_ops"]) if edit["amount"]]
    assumed = [(one["code"], one["group"], one["index"]) for one in found["assumptions"]]
    assert ("segment", "budget_ops", budget) in assumed


def test_a_budget_for_a_house_is_offered_for_a_terraced_house_and_one_press_takes_it():
    found = by_the_rules(A_HOUSE_IN_MORE)

    assert (found["status"], found["applied"]) == ("suggest", [])
    budget = budget_of(found)
    assert held_to(found) == [(kind, 400000, kind, "hard") for kind in KINDS_OF_HOUSE]
    assert [way["label"] for way in budget["choices"]] == [
        "Set a budget of \N{POUND SIGN}400,000 to buy a terraced house, as a firm limit",
        "Set a budget of \N{POUND SIGN}400,000 to buy a semi-detached house, as a firm limit",
        "Set a budget of \N{POUND SIGN}400,000 to buy a detached house, as a firm limit",
        "Skip",
    ]
    # The offer says which kind was taken and why, in one sentence.
    assert budget["note"] == A_TERRACED_HOUSE
    assert budget["does"].startswith(
        "Set a budget of \N{POUND SIGN}400,000 to buy a terraced house, as a firm limit."
    )
    # A terraced house is Burro's guess, and one press takes it with what else was said.
    assert [way["id"] for way in budget["choices"] if way["guess"]] == ["terraced"]
    assert (budget["add_all"], budget["needs"]) == ("terraced", "")
    assert pressed(found) == {"Buying": MORE, "A budget of \N{POUND SIGN}400,000": "terraced"}
    held = after_one_press(found)["spec"]["budget"]
    assert (held["amount"], held["segment"], held["strictness"]) == (400000, "terraced", "hard")
    # The kind stands in an edit of its own that says it is Burro's, so that whoever shows
    # the search marks it as assumed. A kind that a person presses is theirs.
    whose = {
        way["id"]: [
            edit["provenance"]
            for edit in way["operations"]["budget_ops"]
            if edit["segment"] != "unchanged"
        ]
        for way in budget["choices"]
        if way["id"] != "ignore"
    }
    assert whose == {
        "terraced": ["inferred"],
        "semi_detached": ["ui_edit"],
        "detached": ["ui_edit"],
    }


@pytest.mark.parametrize("kind", KINDS_OF_HOUSE)
def test_the_kind_of_house_a_person_chooses_is_what_the_budget_is_held_against(kind: str):
    found = by_the_rules(A_HOUSE_IN_MORE)

    way = next(way for way in budget_of(found)["choices"] if way["id"] == kind)
    body = {"spec": found["spec"], "operations": way["operations"], "limit": 5}
    ranked = client_for(make_deps()).post("/v1/rank", json=body).json()["data"]

    assert ranked["rejected"] == []
    held = ranked["spec"]["budget"]
    assert (ranked["spec"]["tenure"], held["amount"], held["segment"]) == ("buy", 400000, kind)
    # "Max" makes it a firm limit, as the person worded it, and the amount is the person's.
    assert (held["strictness"], held["provenance"]) == ("hard", "ui_edit")


def test_an_area_with_no_price_for_a_terraced_house_is_held_to_no_other_kind():
    # Two areas lose their price for a terraced house: the one where flats sold for least,
    # and the one where they sold for most. Each still holds what every other kind sold for.
    city = release()
    flats = sorted(
        (row for row in city.costs if row.segment is Segment.FLAT and row.tenure is Tenure.BUY),
        key=lambda row: row.median,
    )
    without = {flats[0].area_id, flats[-1].area_id}
    costs = tuple(
        row
        for row in city.costs
        if not (row.area_id in without and row.segment is Segment.TERRACED)
    )
    deps = make_deps(release=dataclasses.replace(city, costs=costs))
    found = client_for(deps).post("/v1/interpret", json={"text": A_HOUSE_IN_MORE}).json()["data"]
    edits: dict[str, list[Any]] = {}
    for way in taken(found):
        for group, made in way["operations"].items():
            edits.setdefault(group, []).extend(made)
    body = {"spec": found["spec"], "operations": edits, "limit": 50}

    ranked = client_for(deps).post("/v1/rank", json=body).json()["data"]

    assert ranked["spec"]["budget"]["segment"] == "terraced"
    # Neither is left out by the budget, dear or not, and neither is given a figure for it:
    # each says that the limit could not be tested.
    assert not [row for row in ranked["filtered"] if row["area_id"] in without]
    rows = [row for row in ranked["ranked"] if row["area_id"] in without]
    assert {row["area_id"] for row in rows} == without
    for row in rows:
        assert row["budget"] is None and "over_budget" in row["untested_filters"]
    # Every other area is held to what terraced houses sold for there.
    assert [row for row in ranked["filtered"] if row["reason"] == "over_budget"]


@pytest.mark.parametrize(
    "reads",
    [
        model_output(
            budget_ops=[model_budget(tenure="buy", amount=400000, words="max \N{POUND SIGN}400k")]
        ),
        model_output(
            budget_ops=[
                model_budget(
                    tenure="buy",
                    amount=400000,
                    segment="flat",
                    strictness="hard",
                    words="max \N{POUND SIGN}400k for a house",
                )
            ]
        ),
    ],
    ids=["a model that reads the amount", "a model that calls the house a flat"],
)
def test_a_house_is_never_held_to_what_flats_sold_for_whatever_a_model_answers(
    reads: dict[str, Any],
):
    found = through_the_route(reads, A_HOUSE_IN_MORE)

    assert found["applied"] == []
    assert held_to(found) == [(kind, 400000, kind, "hard") for kind in KINDS_OF_HOUSE]
    budget = budget_of(found)
    assert [way["id"] for way in budget["choices"] if way["guess"]] == ["terraced"]
    assert budget["add_all"] == "terraced"
    assert after_one_press(found)["spec"]["budget"]["segment"] == "terraced"


def test_a_budget_for_a_house_is_asked_about_where_no_terraced_house_has_a_price():
    # The kind that Burro takes cannot serve, so which kind it is is asked, as it was built
    # first: no way is the guess, and one press takes none of it.
    costs = tuple(row for row in release().costs if row.segment is not Segment.TERRACED)
    deps = make_deps(release=dataclasses.replace(release(), costs=costs))

    found = client_for(deps).post("/v1/interpret", json={"text": A_HOUSE}).json()["data"]

    assert (found["status"], found["applied"]) == ("suggest", [])
    budget = budget_of(found)
    assert [way["id"] for way in budget["choices"]] == ["semi_detached", "detached", "ignore"]
    assert budget["does"] == (
        "A budget of \N{POUND SIGN}600,000 for a house: semi-detached or detached?"
    )
    assert budget["note"].startswith("Burro holds what houses sold for by kind of house")
    assert not [way for way in budget["choices"] if way["guess"]]
    assert (budget["add_all"], budget["needs"]) == ("", "a budget of \N{POUND SIGN}600,000")


@pytest.mark.parametrize(
    ("text", "segment"),
    [
        ("buying a terraced house, about \N{POUND SIGN}600k", "terraced"),
        ("buying a flat, about \N{POUND SIGN}600k", "flat"),
    ],
)
def test_a_kind_of_home_that_is_named_is_applied_as_it_was(text: str, segment: str):
    found = by_the_rules(text)

    assert (found["status"], found["suggestions"]) == ("ok", [])
    held = found["spec"]["budget"]
    assert (found["spec"]["tenure"], held["amount"], held["segment"]) == ("buy", 600000, segment)


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
        # "Up to" makes a budget firm, and it is taken as it was worded.
        "budget": FIRM,
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
    for case, found in every_answer():
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
