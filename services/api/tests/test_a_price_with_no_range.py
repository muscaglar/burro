"""The service on a release whose prices are a publisher's median, with no range.

The release here is the committed synthetic one, with every price to buy a flat
made one number: its median, with no quartile and no count of sales. One area is
left with no price for a flat at all. It is made up, and describes no real
place. It is shaped as a build of London is, which reads the median price paid
for each kind of home and nothing more.
"""

import dataclasses
from functools import cache
from typing import Any

import pytest
from burro_core.ids import Confidence, Provenance, Segment, Strictness, Tenure
from burro_core.release import CostEstimate, InMemoryRelease
from burro_core.spec import Budget, PreferenceSpec, default_spec
from fastapi.testclient import TestClient

from .support import client_for, make_deps, release, wire

BUDGET = 400_000


def _as_a_median(row: CostEstimate) -> CostEstimate:
    return row.replace(lower_quartile=None, upper_quartile=None, confidence=Confidence.UNSTATED)


@cache
def flats() -> dict[str, int]:
    """The median of every area that keeps a price for a flat, by its id."""
    held = sorted(
        (row.area_id, row.median)
        for row in release().costs
        if (row.tenure, row.segment) == (Tenure.BUY, Segment.FLAT)
    )
    # The first area with a price is left with none.
    return dict(held[1:])


@cache
def no_figure() -> str:
    """The area whose price for a flat was taken out. It has every other figure it had."""
    return min(
        row.area_id
        for row in release().costs
        if (row.tenure, row.segment) == (Tenure.BUY, Segment.FLAT)
    )


@cache
def priced() -> InMemoryRelease:
    kept = tuple(
        _as_a_median(row) if row.tenure is Tenure.BUY else row
        for row in release().costs
        if (row.area_id, row.tenure, row.segment) != (no_figure(), Tenure.BUY, Segment.FLAT)
    )
    return dataclasses.replace(release(), costs=kept)


def buyer(hard: bool, amount: int = BUDGET) -> PreferenceSpec:
    """A buyer with a budget for a flat, and whatever else a buyer is given to start with."""
    return default_spec(Tenure.BUY).replace(
        budget=Budget(
            amount=amount,
            segment=Segment.FLAT,
            strictness=Strictness.HARD if hard else Strictness.SOFT,
            weight=0.80,
            provenance=Provenance.STATED,
        )
    )


@pytest.fixture
def client() -> TestClient:
    return client_for(make_deps(release=priced()))


def data(response: Any) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    return response.json()["data"]


def ranked(client: TestClient, spec: PreferenceSpec) -> dict[str, Any]:
    return data(client.post("/v1/rank", json={"spec": wire(spec), "limit": 100}))


def dear_and_cheap() -> tuple[str, str]:
    """An area whose flats sold for more than the budget, and one whose flats sold for less."""
    dear = min(area for area, paid in flats().items() if paid > BUDGET)
    cheap = min(area for area, paid in flats().items() if paid < BUDGET)
    return dear, cheap


def test_the_made_up_prices_stand_on_both_sides_of_the_budget():
    assert any(paid > BUDGET for paid in flats().values())
    assert any(paid < BUDGET for paid in flats().values())


def test_an_area_serves_its_price_as_one_number_and_says_what_it_is_of(client: TestClient):
    area, paid = next(iter(flats().items()))
    found = data(client.get(f"/v1/areas/{area}"))
    [row] = [c for c in found["cost"] if (c["tenure"], c["segment"]) == ("buy", "flat")]
    # What is not known is null. A range is never made from one number.
    assert (row["lower_quartile"], row["median"], row["upper_quartile"]) == (None, paid, None)
    assert row["confidence"] == "unstated"
    fact = next(f for f in found["facts"] if f["fact_id"] == f"{area}/cost/buy.flat")
    assert fact["template"] == "cost_buy_median"
    assert fact["slots"]["homes"] == "flats"
    assert fact["slots"]["median"] == f"{paid:,}"
    assert "lower" not in fact["slots"] and "upper" not in fact["slots"]
    assert fact["numbers"][0] == f"£{paid}"


def test_a_rent_with_a_range_is_served_as_it_was(client: TestClient):
    area = next(iter(flats()))
    found = data(client.get(f"/v1/areas/{area}"))
    rents = [c for c in found["cost"] if c["tenure"] == "rent"]
    assert rents
    assert all(c["lower_quartile"] <= c["median"] <= c["upper_quartile"] for c in rents)
    assert all(c["confidence"] != "unstated" for c in rents)


def test_a_firm_budget_leaves_out_every_area_whose_flats_sold_for_more(client: TestClient):
    found = ranked(client, buyer(hard=True))
    over = {f["area_id"] for f in found["filtered"] if f["reason"] == "over_budget"}
    assert over == {area for area, paid in flats().items() if paid > BUDGET}
    kept = {area["area_id"] for area in found["ranked"]}
    assert {area for area, paid in flats().items() if paid <= BUDGET} <= kept | {
        u["area_id"] for u in found["unranked"]
    }
    assert not over & kept


def test_a_soft_budget_leaves_none_out_and_says_how_far_each_median_is_from_it(
    client: TestClient,
):
    found = ranked(client, buyer(hard=False))
    assert not [f for f in found["filtered"] if f["reason"] == "over_budget"]
    assert no_figure() in {area["area_id"] for area in found["ranked"]}
    for area in found["ranked"]:
        fit = area["budget"]
        paid = flats().get(area["area_id"])
        if paid is None:
            # The area whose price was taken out, and any that never had one.
            assert fit is None
            continue
        assert fit["upper_quartile"] is None
        assert fit["margin"] == BUDGET - paid
        assert fit["confidence"] == "unstated"
        assert (fit["utility"] == 1.0) == (paid <= BUDGET)


@pytest.mark.parametrize("hard", [True, False])
def test_an_area_with_no_price_is_ranked_with_its_cost_not_known(client: TestClient, hard: bool):
    found = ranked(client, buyer(hard))
    assert no_figure() not in {f["area_id"] for f in found["filtered"]}
    [there] = [area for area in found["ranked"] if area["area_id"] == no_figure()]
    assert there["budget"] is None
    [budget] = [c for c in there["contributions"] if c["component"] == "budget"]
    assert (budget["present"], budget["utility"], budget["contribution"]) == (False, None, 0.0)
    assert budget["fact_ids"] == [f"{no_figure()}/missing/budget"]
    assert there["untested_filters"] == (["over_budget"] if hard else [])


def test_a_comparison_shows_the_median_that_was_held_against_the_budget(client: TestClient):
    dear, cheap = dear_and_cheap()
    body = {"area_ids": [dear, cheap, no_figure()], "spec": wire(buyer(hard=False))}
    found = data(client.post("/v1/compare", json=body))
    [row] = [r for r in found["rows"] if r["component"] == "budget"]
    over, under, missing = row["cells"]
    assert (over["value"], under["value"], missing["value"]) == (
        flats()[dear],
        flats()[cheap],
        None,
    )
    assert over["fact_id"] == f"{dear}/budget_fit/buy.flat"
    assert missing["fact_id"] == f"{no_figure()}/missing/budget"
    served = {fact["fact_id"]: fact for fact in found["facts"]}
    assert served[over["fact_id"]]["template"] == "budget_over_median"
    assert served[under["fact_id"]]["template"] == "budget_under_median"
    assert served[missing["fact_id"]]["numbers"] == []


def test_an_explanation_says_the_middle_price_and_passes_the_check(client: TestClient):
    # A buyer who asks for nothing but the budget, so that the budget is what is said.
    spec = buyer(hard=False).replace(weights=(), tags=())
    found = data(client.post("/v1/explanations", json={"spec": wire(spec), "limit": 5}))
    said = [
        sentence
        for explained in found["explanations"]
        for sentence in (*explained["reasons"], explained["trade_off"])
        if sentence is not None and any("/budget_fit/" in f for f in sentence["fact_ids"])
    ]
    assert len(said) == 5
    for sentence in said:
        assert sentence["text"].startswith("The middle price of flats of all sizes is £")
        assert sentence["text"].endswith(f" under your budget of £{BUDGET:,}.")
        assert sentence["replaced"] is False
