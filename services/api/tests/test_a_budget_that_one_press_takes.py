"""A budget that one press takes, on a release shaped as a build of London is.

Such a release holds what homes sold for as one number for each kind of home,
a middle price with no range, and what homes let for as the middle rent of a
postcode district or of a borough. Three budgets are held to it here, each
plainly said in a sentence that is not plain, so that one press takes it: to
buy a flat, to buy a house of no kind, which Burro takes as a terraced house,
and to rent a home of one bedroom.

Each is held against a middle. So each leaves an area out only where the
middle is more than a quarter over the budget, and each says what it was held
against: in the offer, before the press, and in the sentence of an area, after.

The release is the committed synthetic one, with every price made one number
and every rent made the rent of a wider place, as the tests of each make it.
It is made up, and describes no real place.
"""

import dataclasses
from functools import cache
from typing import Any, NamedTuple

import pytest
from burro_api.wording import RENTS_NOTE
from burro_core.ids import Confidence, Segment, Tenure
from burro_core.rank import FIRM_BUDGET_MARGIN_PERCENT
from burro_core.release import InMemoryRelease
from fastapi.testclient import TestClient

from .support import client_for, make_deps
from .test_a_rent_of_a_wider_place import let

LEFT_OUT = f"more than {FIRM_BUDGET_MARGIN_PERCENT}% over it are left out."
OF_A_PRICE = (
    f"Areas where the middle price is {LEFT_OUT} "
    "About half of the homes sold in an area went for under its middle price."
)
OF_A_RENT = (
    f"Areas where the middle rent is {LEFT_OUT} "
    "About half of the rents recorded in a place were under its middle rent."
)
A_TERRACED_HOUSE = (
    "You named no kind of house, so Burro has taken a terraced house, the least dear kind "
    "in most areas. Semi-detached and detached are one press away."
)


class Said(NamedTuple):
    """A budget as a person words it, and what is to be said of it."""

    text: str
    tenure: Tenure
    segment: Segment
    amount: int
    # Whose the kind of home is, in the edits that one press takes: the person's, or Burro's.
    kind_is: list[str]
    # What the offer says the budget leaves out, and what a person should know before a press.
    follows: str
    note: str
    # How the sentence of an area begins, and what its fact is made from.
    begins: str
    template: str


BUDGETS = [
    Said(
        text="If I'm buying, max \N{POUND SIGN}400k for a flat",
        tenure=Tenure.BUY,
        segment=Segment.FLAT,
        amount=400_000,
        kind_is=["ui_edit"],
        follows=OF_A_PRICE,
        note="",
        begins="The middle price of flats of all sizes is ",
        template="median",
    ),
    Said(
        text="If I'm buying, max \N{POUND SIGN}400k for a house",
        tenure=Tenure.BUY,
        segment=Segment.TERRACED,
        amount=400_000,
        kind_is=["inferred"],
        follows=OF_A_PRICE,
        note=A_TERRACED_HOUSE,
        begins="The middle price of terraced houses of all sizes is ",
        template="median",
    ),
    Said(
        text="If I'm renting, max \N{POUND SIGN}1,400 a month",
        tenure=Tenure.RENT,
        segment=Segment.BED_1,
        amount=1_400,
        kind_is=[],
        follows=OF_A_RENT,
        note=RENTS_NOTE,
        begins="The middle rent for a 1-bedroom home in ",
        template="recorded",
    ),
]
EACH = pytest.mark.parametrize("said", BUDGETS, ids=["a flat", "a house of no kind", "a rent"])


@cache
def as_london_is_built() -> InMemoryRelease:
    """The release of rents of a wider place, with every price to buy made one number."""
    rows = tuple(
        row.replace(lower_quartile=None, upper_quartile=None, confidence=Confidence.UNSTATED)
        if row.tenure is Tenure.BUY
        else row
        for row in let().costs
    )
    return dataclasses.replace(let(), costs=rows)


def middles(said: Said) -> dict[str, int]:
    """The middle that each area holds for the home a budget is for, by its id."""
    return {
        row.area_id: row.median
        for row in as_london_is_built().costs
        if (row.tenure, row.segment) == (said.tenure, said.segment)
    }


def far_over(said: Said) -> set[str]:
    """The areas whose middle is more than a quarter over the budget, in whole pounds."""
    line = (100 + FIRM_BUDGET_MARGIN_PERCENT) * said.amount
    return {area for area, middle in middles(said).items() if 100 * middle > line}


@pytest.fixture(scope="module")
def client() -> TestClient:
    return client_for(make_deps(release=as_london_is_built()))


def data(response: Any) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    return response.json()["data"]


def offered(client: TestClient, said: Said) -> dict[str, Any]:
    found = data(client.post("/v1/interpret", json={"text": said.text}))
    # Nothing is applied until it is pressed.
    assert (found["status"], found["applied"]) == ("suggest", [])
    return found


def one_press(found: dict[str, Any]) -> dict[str, list[Any]]:
    """The edits of every way that one press takes of an answer."""
    edits: dict[str, list[Any]] = {}
    for offer in found["suggestions"]:
        for way in offer["choices"]:
            if offer["add_all"] and way["id"] == offer["add_all"]:
                for group, held in way["operations"].items():
                    edits.setdefault(group, []).extend(held)
    return edits


def pressed(client: TestClient, said: Said) -> dict[str, Any]:
    """The ranking that follows one press, and no other."""
    found = offered(client, said)
    body = {"spec": found["spec"], "operations": one_press(found), "limit": 100}
    ranked = data(client.post("/v1/rank", json=body))
    assert ranked["rejected"] == []
    return ranked


@EACH
def test_the_made_up_figures_stand_on_both_sides_of_the_budget_and_of_the_line(said: Said):
    over, held = far_over(said), middles(said)
    assert over and any(said.amount < held[area] for area in held.keys() - over)
    assert any(middle < said.amount for middle in held.values())


@EACH
def test_one_press_takes_the_budget_as_the_firm_limit_it_was_worded_as(
    client: TestClient, said: Said
):
    found = offered(client, said)
    kinds = [e for e in one_press(found)["budget_ops"] if e["segment"] != "unchanged"]
    # A kind of house that Burro took is its own, so that whoever shows it marks it assumed.
    assert [edit["provenance"] for edit in kinds] == said.kind_is

    spec = pressed(client, said)["spec"]

    held = spec["budget"]
    assert (spec["tenure"], held["segment"]) == (said.tenure.value, said.segment.value)
    assert (held["amount"], held["strictness"]) == (said.amount, "hard")


@EACH
def test_it_leaves_an_area_out_only_where_the_middle_is_more_than_a_quarter_over(
    client: TestClient, said: Said
):
    ranked = pressed(client, said)

    assert {row["reason"] for row in ranked["filtered"]} == {"over_budget"}
    assert {row["area_id"] for row in ranked["filtered"]} == far_over(said)
    # An area kept by the margin is ranked, and its fit says how far over the middle is.
    fits = {row["area_id"]: row["budget"] for row in ranked["ranked"]}
    near = {a for a, middle in middles(said).items() if middle > said.amount} - far_over(said)
    assert near and near <= set(fits)
    for area in near:
        assert fits[area]["margin"] == said.amount - middles(said)[area] < 0
        assert fits[area]["upper_quartile"] is None


@EACH
def test_the_offer_says_what_the_budget_is_held_against_before_it_is_pressed(
    client: TestClient, said: Said
):
    [budget] = [
        offer
        for offer in offered(client, said)["suggestions"]
        if offer["label"].startswith("A budget of")
    ]

    assert budget["follows"] == said.follows
    # What is said of rents is said of a budget to rent, and of no budget to buy.
    assert budget["note"] == said.note


@EACH
def test_the_sentence_of_an_area_says_what_the_budget_was_held_against(
    client: TestClient, said: Said
):
    spec = pressed(client, said)["spec"]
    held = middles(said)
    near = min(area for area in held.keys() - far_over(said) if held[area] > said.amount)
    under = min(area for area, middle in held.items() if middle < said.amount)

    compared = data(client.post("/v1/compare", json={"area_ids": [near, under], "spec": spec}))

    [row] = [row for row in compared["rows"] if row["component"] == "budget"]
    facts = {fact["fact_id"]: fact for fact in compared["facts"]}
    over, within = (facts[cell["fact_id"]] for cell in row["cells"])
    assert over["template"] == f"budget_over_{said.template}"
    assert within["template"] == f"budget_under_{said.template}"
    for area, fact in ((near, over), (under, within)):
        assert fact["slots"]["median"] == f"{held[area]:,}"
        assert fact["slots"]["amount"] == f"{said.amount:,}"
    # The sentences a person reads of the first areas begin with what it was held against.
    asked = spec | {"weights": [], "tags": []}
    explained = data(client.post("/v1/explanations", json={"spec": asked, "limit": 5}))
    sentences = [
        sentence["text"]
        for area in explained["explanations"]
        for sentence in (*area["reasons"], area["trade_off"])
        if sentence is not None and any("/budget_fit/" in f for f in sentence["fact_ids"])
    ]
    assert len(sentences) == 5
    assert all(text.startswith(said.begins) for text in sentences)
    # A middle that is the budget to the pound is at it: no sentence gives a difference of nothing.
    assert not any("\N{POUND SIGN}0 " in text for text in sentences)
