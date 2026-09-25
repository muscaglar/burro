"""The service on a release whose rents are each of a postcode district or of a borough.

The release here is the committed synthetic one, with every rent made the rent
of a wider place: the areas lie two to a district, and the last four take the
figure of their borough. It is made up, and describes no real place. No
postcode begins with a Q, so no district here is a district. It is shaped as a
build of London is, which reads the rents a publisher gives for each postcode
district and each borough, and gives an area the figure of the place it lies in.

Wherever a rent is served, or a budget that was held against one, so is the
place it is of, the months and how many rents were recorded.
"""

import dataclasses
from functools import cache
from typing import Any

import pytest
from burro_api.wording import RENTS_NOTE
from burro_core.facts import RENT_CAUTION, RENT_IS_OF_A_PLACE
from burro_core.ids import CostOfKind, Provenance, Segment, Strictness, Tenure
from burro_core.rank import FIRM_BUDGET_MARGIN_PERCENT
from burro_core.release import CostEstimate, CostOf, InMemoryRelease, confidence_of
from burro_core.spec import Budget, PreferenceSpec, default_spec
from fastapi.testclient import TestClient

from .support import client_for, make_deps, release, wire

BUDGET = 1_400
# The most a middle rent may be and not be left out by a firm budget: a quarter over it.
AT_THE_LINE = BUDGET * (100 + FIRM_BUDGET_MARGIN_PERCENT) // 100
SINCE, UNTIL = "2025-04", "2026-03"
# How many areas take the figure of their borough, and how many rents each kind of place
# rests on.
OF_THE_BOROUGH, IN_A_DISTRICT, IN_A_BOROUGH = 4, 30, 520


@cache
def places() -> dict[str, CostOf]:
    """The place the rents of each area are of. Two areas lie in each district."""
    areas = sorted({row.area_id for row in release().costs if row.tenure is Tenure.RENT})
    borough = {area.area_id: area.borough for area in release().neighbourhoods}
    found: dict[str, CostOf] = {}
    for at, area in enumerate(areas):
        if at >= len(areas) - OF_THE_BOROUGH:
            found[area] = CostOf(kind=CostOfKind.BOROUGH, name=borough[area])
        else:
            found[area] = CostOf(kind=CostOfKind.POSTCODE_DISTRICT, name=f"QA{at // 2 + 1}")
    return found


@cache
def let() -> InMemoryRelease:
    """The committed release, with every rent the rent of the place its area lies in.

    A place has one figure for a kind of home: that of the first of its areas.
    """
    of_the_place: dict[tuple[CostOf, Segment], CostEstimate] = {}
    rows: list[CostEstimate] = []
    for row in release().costs:
        if row.tenure is not Tenure.RENT:
            rows.append(row)
            continue
        place = places()[row.area_id]
        rents = IN_A_BOROUGH if place.kind is CostOfKind.BOROUGH else IN_A_DISTRICT
        first = of_the_place.setdefault(
            (place, row.segment),
            row.replace(
                of=place,
                rents=rents,
                since=SINCE,
                as_of=UNTIL,
                confidence=confidence_of(rents),
            ),
        )
        rows.append(first.replace(area_id=row.area_id))
    return dataclasses.replace(release(), costs=tuple(rows))


@cache
def middles() -> dict[str, int]:
    """The middle rent of a home of one bedroom that each area shows, by its id."""
    return {
        row.area_id: row.median
        for row in let().costs
        if (row.tenure, row.segment) == (Tenure.RENT, Segment.BED_1)
    }


def renter(hard: bool, amount: int = BUDGET) -> PreferenceSpec:
    """A renter with a budget for a home of one bedroom, and whatever else a renter starts with."""
    return default_spec(Tenure.RENT).replace(
        budget=Budget(
            amount=amount,
            segment=Segment.BED_1,
            strictness=Strictness.HARD if hard else Strictness.SOFT,
            weight=0.80,
            provenance=Provenance.STATED,
        )
    )


@pytest.fixture
def client() -> TestClient:
    return client_for(make_deps(release=let()))


def data(response: Any) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    return response.json()["data"]


def ranked(client: TestClient, spec: PreferenceSpec) -> dict[str, Any]:
    return data(client.post("/v1/rank", json={"spec": wire(spec), "limit": 100}))


def test_the_made_up_rents_stand_on_both_sides_of_the_budget_and_of_the_line():
    assert any(rent > AT_THE_LINE for rent in middles().values())
    assert any(BUDGET < rent <= AT_THE_LINE for rent in middles().values())
    assert any(rent < BUDGET for rent in middles().values())
    kinds = {place.kind for place in places().values()}
    assert kinds == set(CostOfKind)


# What is served of a rent


def test_an_area_serves_each_rent_with_the_place_the_months_and_the_count(client: TestClient):
    area, place = next(iter(places().items()))
    found = data(client.get(f"/v1/areas/{area}"))
    rents = [row for row in found["cost"] if row["tenure"] == "rent"]
    assert rents
    for row in rents:
        assert row["of"] == {"kind": "postcode_district", "name": place.name}
        assert (row["rents"], row["since"], row["as_of"]) == (IN_A_DISTRICT, SINCE, UNTIL)
        assert row["lower_quartile"] <= row["median"] <= row["upper_quartile"]
    # A price is of the area alone, and says no place.
    prices = [row for row in found["cost"] if row["tenure"] == "buy"]
    assert prices and all(row["of"] is None and row["rents"] is None for row in prices)


def test_the_fact_of_a_rent_holds_all_that_a_page_shows_beside_it(client: TestClient):
    area, place = next(iter(places().items()))
    found = data(client.get(f"/v1/areas/{area}"))
    fact = next(f for f in found["facts"] if f["fact_id"] == f"{area}/cost/rent.bed_1")
    assert fact["template"] == "cost_rent_recorded"
    slots = fact["slots"]
    assert (slots["of_kind"], slots["of_name"]) == ("postcode district", place.name)
    assert slots["of"] == f"postcode district {place.name}"
    assert slots["period"] == "April 2025 to March 2026"
    assert slots["rents"] == str(IN_A_DISTRICT)
    assert slots["caution"] == RENT_CAUTION
    assert place.name in fact["names"]


def test_an_area_that_takes_its_boroughs_rent_says_so(client: TestClient):
    area = max(places())
    found = data(client.get(f"/v1/areas/{area}"))
    [row] = [r for r in found["cost"] if (r["tenure"], r["segment"]) == ("rent", "bed_1")]
    assert row["of"] == {"kind": "borough", "name": found["area"]["borough"]}
    fact = next(f for f in found["facts"] if f["fact_id"] == f"{area}/cost/rent.bed_1")
    assert fact["slots"]["of"] == f"the whole borough of {found['area']['borough']}"


def test_the_service_says_what_is_said_of_rents_that_are_of_a_place(client: TestClient):
    found = data(client.get("/v1/meta"))
    assert found["rents"] == {"of_a_place": RENT_IS_OF_A_PLACE, "caution": RENT_CAUTION}
    assert found["holds"]["costs"] is True


def test_a_release_whose_rents_are_of_the_area_alone_says_nothing_of_it():
    found = data(client_for(make_deps()).get("/v1/meta"))
    assert found["rents"] is None


# What a budget to rent is held against


def test_a_firm_budget_leaves_out_an_area_only_where_the_middle_rent_is_far_over_it(
    client: TestClient,
):
    found = ranked(client, renter(hard=True))
    over = {f["area_id"] for f in found["filtered"] if f["reason"] == "over_budget"}
    assert over == {area for area, rent in middles().items() if rent > AT_THE_LINE}
    kept = {area["area_id"] for area in found["ranked"]}
    assert not over & kept


def test_an_area_kept_by_the_margin_is_ranked_lower_and_says_how_far_over_it_is(
    client: TestClient,
):
    found = ranked(client, renter(hard=True))
    near = {area for area, rent in middles().items() if BUDGET < rent <= AT_THE_LINE}
    fits = {area["area_id"]: area["budget"] for area in found["ranked"]}
    assert near and near <= set(fits)
    for area in near:
        assert fits[area]["margin"] == BUDGET - middles()[area] < 0
        # The margin is to the middle, and the fit names no upper end.
        assert fits[area]["upper_quartile"] is None
        assert 0 <= fits[area]["utility"] < 1


def test_two_areas_of_one_district_are_kept_or_left_out_together(client: TestClient):
    found = ranked(client, renter(hard=True))
    out = {f["area_id"] for f in found["filtered"]}
    by_place: dict[CostOf, set[bool]] = {}
    for area, place in places().items():
        if area in middles():
            by_place.setdefault(place, set()).add(area in out)
    assert all(len(sides) == 1 for sides in by_place.values())


def test_an_explanation_says_the_place_the_rent_is_of_and_passes_the_check(client: TestClient):
    # A renter who asks for nothing but the budget, so that the budget is what is said.
    spec = renter(hard=False).replace(weights=(), tags=())
    found = data(client.post("/v1/explanations", json={"spec": wire(spec), "limit": 5}))
    said = [
        sentence
        for explained in found["explanations"]
        for sentence in (*explained["reasons"], explained["trade_off"])
        if sentence is not None and any("/budget_fit/" in f for f in sentence["fact_ids"])
    ]
    assert len(said) == 5
    for sentence in said:
        assert sentence["text"].startswith("The middle rent for a 1-bedroom home in ")
        assert " in postcode district QA" in sentence["text"] or (
            " in the whole borough of " in sentence["text"]
        )
        assert sentence["replaced"] is False


def test_a_comparison_shows_the_middle_rent_that_was_held_against_the_budget(
    client: TestClient,
):
    dear = min(area for area, rent in middles().items() if rent > BUDGET)
    cheap = min(area for area, rent in middles().items() if rent < BUDGET)
    body = {"area_ids": [dear, cheap], "spec": wire(renter(hard=False))}
    found = data(client.post("/v1/compare", json=body))
    [row] = [r for r in found["rows"] if r["component"] == "budget"]
    over, under = row["cells"]
    assert (over["value"], under["value"]) == (middles()[dear], middles()[cheap])
    served = {fact["fact_id"]: fact for fact in found["facts"]}
    assert served[over["fact_id"]]["template"] == "budget_over_recorded"
    assert served[under["fact_id"]]["template"] == "budget_under_recorded"
    assert served[over["fact_id"]]["slots"]["caution"] == RENT_CAUTION


# What is read of a budget to rent


def test_a_plain_budget_to_rent_is_applied_as_it_was_worded(client: TestClient):
    found = data(client.post("/v1/interpret", json={"text": "renting, up to £1,700 a month"}))
    assert found["status"] == "ok" and found["not_in_release"] == []
    assert found["spec"]["tenure"] == "rent"
    held = found["spec"]["budget"]
    assert (held["amount"], held["segment"], held["strictness"]) == (1_700, "bed_1", "hard")


def offered_budget(client: TestClient, text: str) -> dict[str, Any]:
    found = data(client.post("/v1/interpret", json={"text": text}))
    # The amount is one offer, and the kind of home another.
    [budget] = [offer for offer in found["suggestions"] if offer["label"].startswith("A budget")]
    return budget


def test_the_offer_of_a_firm_budget_to_rent_says_the_margin_the_place_and_the_caution(
    client: TestClient,
):
    budget = offered_budget(client, "Somewhere lovely. If I'm renting, max £1,900 a month.")
    assert budget["does"] == "Set a budget of £1,900 a month, as a firm limit."
    assert budget["follows"] == (
        f"Areas where the middle rent is more than {FIRM_BUDGET_MARGIN_PERCENT}% over it are "
        "left out. About half of the rents recorded in a place were under its middle rent."
    )
    assert budget["note"] == RENTS_NOTE == f"{RENT_IS_OF_A_PLACE} {RENT_CAUTION}"
    assert [way["label"] for way in budget["choices"]] == [
        "Set as a firm limit: areas where the middle rent is more than 25% over it are left out",
        "Skip",
    ]


def test_one_press_takes_a_budget_to_rent_that_was_plainly_said(client: TestClient):
    budget = offered_budget(client, "Somewhere lovely. If I'm renting, max £1,900 a month.")
    [firm, _] = budget["choices"]
    assert firm["guess"] is True
    assert budget["add_all"] == firm["id"]
    [edit] = firm["operations"]["budget_ops"]
    assert (edit["amount"], edit["strictness"]) == (1_900, "hard")


def test_the_offer_of_a_budget_to_rent_as_a_guide_says_the_place_and_the_caution_too(
    client: TestClient,
):
    budget = offered_budget(client, "Somewhere lovely. I could pay around £1,900 a month in rent.")
    assert budget["does"] == "Set a budget of £1,900 a month."
    assert budget["note"] == RENTS_NOTE
    # No word of it makes the budget firm, so one press takes none of it.
    assert [way["guess"] for way in budget["choices"]] == [False, False]


def test_an_offer_that_sets_no_amount_says_no_caution(client: TestClient):
    found = data(
        client.post("/v1/interpret", json={"text": "Somewhere lovely. If I'm renting, 2 beds."})
    )
    homes = [offer for offer in found["suggestions"] if offer["target"] in ("tenure", "budget")]
    assert homes and all(offer["note"] != RENTS_NOTE for offer in homes)


def test_on_a_release_whose_rents_are_of_the_area_alone_the_offer_says_what_it_said():
    client = client_for(make_deps())
    budget = offered_budget(client, "Somewhere lovely. If I'm renting, max £1,900 a month.")
    assert budget["follows"] == "Dearer areas are left out."
    assert budget["note"] == ""
