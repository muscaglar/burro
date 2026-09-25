"""A price that is one number: a publisher's median of what was paid, with no range.

A publisher may give the median of the sales of a year and nothing else: no
quartile, and no count of the sales. A cost row then holds the median and no
range, and says that what it rests on is not stated. Nothing stands in for the
range. The budget is held against the median, as it is written, and the
sentence says what the median is of: homes of that kind, of all sizes.

Every name and figure here is made up.
"""

import dataclasses
from typing import Any, cast

import pytest
from burro_core.explain import TEMPLATES, TemplateExplainer, explain, render
from burro_core.facts import Fact, facts_for
from burro_core.ids import (
    Confidence,
    FactKind,
    FilterReason,
    Segment,
    SentenceRole,
    Strictness,
    TemplateId,
    Tenure,
    UnrankedReason,
)
from burro_core.rank import RankedArea, RankResult, budget_held_against, rank
from burro_core.release import ReleaseError, parse_release
from burro_core.spec import PreferenceSpec, default_spec
from burro_core.verify import verify

from .no_range import FLATS, FOUR, ONE, THREE, TWO, buyer, median, priced
from .support import AS_OF, SYNTHETIC, documents, small_release


def by_area(result: RankResult) -> dict[str, RankedArea]:
    return {area.area_id: area for area in result.ranked}


def facts_of(area: str, spec: PreferenceSpec | None = None) -> dict[str, Fact]:
    return {fact.fact_id: fact for fact in facts_for(priced(), area, spec)}


def first_price(found: dict[str, Any]) -> dict[str, Any]:
    """The first price of a flat to buy in the files of the small release.

    It is found by what it is of and never by where it stands, so that it is
    the same row however many costs the small release holds.
    """
    rows = cast(list[dict[str, Any]], found["cost.json"]["rows"])
    return next(row for row in rows if (row["tenure"], row["segment"]) == ("buy", "flat"))


def with_cost(**changes: Any) -> dict[str, Any]:
    """The files of the small release, with its first price changed. It is a flat to buy."""
    found = documents()
    row = first_price(found)
    assert row["area_id"] == ONE
    row.update(lower_quartile=None, upper_quartile=None, confidence="unstated")
    row.update(changes)
    return found


def rule_broken(broken: dict[str, Any]) -> tuple[str, str]:
    with pytest.raises(ReleaseError) as caught:
        parse_release(broken)
    return caught.value.file, caught.value.rule


# The row


def test_a_price_may_hold_a_median_and_no_range():
    release = parse_release(with_cost())
    held = release.cost(ONE, Tenure.BUY, Segment.FLAT)
    assert held is not None
    assert (held.lower_quartile, held.median, held.upper_quartile) == (None, 350_000, None)
    assert held.confidence is Confidence.UNSTATED


def test_a_release_writes_a_row_with_no_range_as_it_reads_it():
    """What is not known is null in the file, and is read back as not known."""
    release = parse_release(with_cost())
    written = cast(dict[str, Any], release.documents()["cost.json"])
    [row] = [
        r
        for r in written["rows"]
        if (r["area_id"], r["tenure"], r["segment"]) == (ONE, "buy", "flat")
    ]
    assert (row["lower_quartile"], row["upper_quartile"]) == (None, None)
    assert parse_release(release.documents()).costs == release.costs


@pytest.mark.parametrize(
    "changes",
    [
        # One end of a range is no range.
        {"lower_quartile": 300_000},
        {"upper_quartile": 450_000},
        # A row with no range says nothing of how many sales it rests on.
        {"confidence": "high"},
        {"confidence": "low"},
    ],
)
def test_a_row_that_holds_half_of_what_it_says_is_refused(changes: dict[str, Any]):
    assert rule_broken(with_cost(**changes)) == ("cost.json", "values_are_in_range")


def test_a_rent_with_no_range_is_refused():
    """No source gives a rent as one number, and no sentence says one."""
    found = documents()
    rows = cast(list[dict[str, Any]], found["cost.json"]["rows"])
    rent = next(row for row in rows if row["tenure"] == "rent")
    rent.update(lower_quartile=None, upper_quartile=None, confidence="unstated")
    assert rule_broken(found) == ("cost.json", "values_are_in_range")


def test_a_row_with_a_range_says_what_it_rests_on():
    """`unstated` is for a row with no range, and for no other."""
    found = documents()
    first_price(found).update(confidence="unstated")
    assert rule_broken(found) == ("cost.json", "values_are_in_range")


def test_a_median_is_carried_as_the_publisher_wrote_it():
    """An estimate of Burro's own is rounded. A publisher's figure is the one in its file."""
    release = parse_release(with_cost(median=437_501))
    held = release.cost(ONE, Tenure.BUY, Segment.FLAT)
    assert held is not None and held.median == 437_501


# The budget


def test_the_budget_is_held_against_the_median_where_a_row_has_no_range():
    assert budget_held_against(median(ONE, 385_000)) == 385_000
    ranged = small_release().cost(ONE, Tenure.BUY, Segment.FLAT)
    assert ranged is not None
    assert budget_held_against(ranged) == ranged.upper_quartile == 400_000


def test_no_price_is_scaled_to_a_size_of_home():
    """The file gives no price by bedrooms. What is held is the figure, to the pound."""
    for area, paid in FLATS.items():
        fit = by_area(rank(buyer(Strictness.SOFT, 1_000_000), priced()))[area].budget
        assert fit is not None
        assert fit.margin == 1_000_000 - paid


def test_a_firm_budget_leaves_out_an_area_only_where_its_median_is_far_over_it():
    """About half of the homes behind a median sold for less than it.

    So an area whose median is over a firm budget by no more than the margin
    is kept, and ranked lower. `test_a_firm_budget.py` holds the margin.
    """
    near = rank(buyer(Strictness.HARD), priced())
    assert near.filtered == ()
    assert {ONE, TWO, THREE} <= set(by_area(near))
    # 437,500 is more than a quarter over 340,000, and 400,000 is not.
    far = rank(buyer(Strictness.HARD, 340_000), priced())
    assert [(f.area_id, f.reason) for f in far.filtered] == [(THREE, FilterReason.OVER_BUDGET)]
    assert {ONE, TWO} <= set(by_area(far))


def test_a_soft_budget_ranks_a_dearer_area_lower_and_leaves_none_out():
    result = rank(buyer(Strictness.SOFT), priced())
    assert result.filtered == ()
    areas = by_area(result)
    fits = {area: areas[area].budget for area in FLATS}
    assert all(fit is not None for fit in fits.values())
    assert [fits[a].utility for a in (ONE, TWO, THREE)] == [1.0, 1.0, 0.625]  # pyright: ignore[reportOptionalMemberAccess]
    assert areas[THREE].rank > max(areas[ONE].rank, areas[TWO].rank)
    # Being further under the budget earns nothing: no verdict is given on a price.
    assert areas[ONE].score == areas[TWO].score


def test_a_fit_says_there_is_no_upper_quartile_and_how_far_the_median_is_from_the_budget():
    fit = by_area(rank(buyer(Strictness.SOFT), priced()))[THREE].budget
    assert fit is not None
    assert (fit.upper_quartile, fit.margin, fit.confidence) == (None, -37_500, "unstated")
    assert fit.as_of == AS_OF


@pytest.mark.parametrize("strictness", list(Strictness))
def test_an_area_with_no_figure_is_not_left_out_and_is_not_ranked_as_if_cheap(
    strictness: Strictness,
):
    """It is ranked with the cost not known, and says so."""
    result = rank(buyer(strictness).replace(weights=default_spec(Tenure.BUY).weights), priced())
    assert FOUR not in {f.area_id for f in result.filtered}
    there = by_area(result)[FOUR]
    assert there.budget is None
    budget = next(c for c in there.contributions if c.component == "budget")
    assert (budget.present, budget.utility, budget.contribution) == (False, None, 0.0)
    assert budget.fact_ids == (f"{FOUR}/missing/budget",)
    firm = strictness is Strictness.HARD
    assert there.untested_filters == ((FilterReason.OVER_BUDGET,) if firm else ())
    said = facts_of(FOUR, buyer(strictness))[f"{FOUR}/missing/budget"]
    assert render(said).text == (
        "There is no cost figure for Dulcimer Green in this release, "
        "so it was left out of the score."
    )


@pytest.mark.parametrize("strictness", list(Strictness))
def test_an_area_with_no_figure_is_not_ranked_where_a_budget_is_all_that_was_asked(
    strictness: Strictness,
):
    """It is not left out as if it were dear, and it is given no place as if it were cheap.

    With nothing else to rank it on it falls under the floor of what must be
    known, and says which figure it lacks.
    """
    result = rank(buyer(strictness), priced())
    assert FOUR not in {f.area_id for f in result.filtered}
    assert FOUR not in by_area(result)
    [lacking] = [u for u in result.unranked if u.area_id == FOUR]
    assert (lacking.reason, lacking.missing) == (UnrankedReason.INSUFFICIENT_DATA, ("budget",))
    # Every area that is ranked has a figure, and none of them is the area that lacks one.
    assert set(by_area(result)) <= set(FLATS)


# What is said


def test_a_price_with_no_range_is_said_as_the_middle_price_of_homes_of_all_sizes():
    fact = facts_of(THREE)[f"{THREE}/cost/buy.flat"]
    assert (fact.kind, fact.template) == (FactKind.COST, TemplateId.COST_BUY_MEDIAN)
    assert fact.slots == {
        "segment": "flat",
        "homes": "flats",
        "median": "437,500",
        "as_of": "August 2026",
        "period": "the year ending August 2026",
        "confidence": "unstated",
        "half_sold": "About half of the flats sold here went for under £437,500.",
    }
    assert set(fact.numbers) == {"£437500", "2026", "08", "8"}
    assert render(fact).text == (
        "Price for a flat: £437,500. This is the middle price of flats of all sizes sold "
        "in the year ending August 2026. The publisher gives no range, and does not say "
        "how many sales it rests on."
    )


@pytest.mark.parametrize(
    ("segment", "homes"),
    [
        (Segment.FLAT, "flats"),
        (Segment.TERRACED, "terraced houses"),
        (Segment.SEMI_DETACHED, "semi-detached houses"),
        (Segment.DETACHED, "detached houses"),
    ],
)
def test_every_kind_of_home_is_said_of_all_sizes(segment: Segment, homes: str):
    release = dataclasses.replace(small_release(), costs=(median(ONE, 610_000, segment),))
    fact = next(f for f in facts_for(release, ONE, None) if f.kind is FactKind.COST)
    assert f"the middle price of {homes} of all sizes sold in the year" in render(fact).text


def test_the_sentence_of_a_price_states_no_range_and_no_word_for_its_confidence():
    text = TEMPLATES[TemplateId.COST_BUY_MEDIAN]
    assert "{lower}" not in text and "{upper}" not in text and "{confidence}" not in text
    assert " to £" not in text


def test_a_budget_fact_says_the_middle_price_and_never_the_upper_end():
    under = facts_of(ONE, buyer(Strictness.SOFT))[f"{ONE}/budget_fit/buy.flat"]
    over = facts_of(THREE, buyer(Strictness.SOFT))[f"{THREE}/budget_fit/buy.flat"]
    assert (under.template, under.slots, under.numbers) == (
        TemplateId.BUDGET_UNDER_MEDIAN,
        {
            "margin": "15,000",
            "amount": "400,000",
            "median": "385,000",
            "homes": "flats",
            "half_sold": "About half of the flats sold here went for under £385,000.",
        },
        ("£400000", "£385000", "£15000"),
    )
    assert (over.template, over.numbers) == (
        TemplateId.BUDGET_OVER_MEDIAN,
        ("£400000", "£437500", "£37500"),
    )
    assert render(under).text == (
        "The middle price of flats of all sizes is £15,000 under your budget of £400,000."
    )
    assert render(over).text == (
        "The middle price of flats of all sizes is £37,500 over your budget of £400,000. "
        "About half of the flats sold here went for under £437,500."
    )
    assert "upper end" not in render(under).text + render(over).text


def test_every_fact_of_a_price_with_no_range_names_a_source_and_a_date():
    spec = buyer(Strictness.SOFT)
    found = [fact for area in FLATS for fact in facts_of(area, spec).values()]
    ours = [fact for fact in found if fact.kind in (FactKind.COST, FactKind.BUDGET_FIT)]
    assert {fact.template for fact in ours if fact.key == "buy.flat"} == {
        TemplateId.COST_BUY_MEDIAN,
        TemplateId.BUDGET_UNDER_MEDIAN,
        TemplateId.BUDGET_OVER_MEDIAN,
    }
    for fact in ours:
        assert [source.source_id for source in fact.sources] == list(SYNTHETIC)
        assert fact.as_of == AS_OF and fact.synthetic is True


def test_a_price_with_a_range_is_said_as_it_was():
    fact = next(
        f for f in facts_for(small_release(), ONE, None) if f.fact_id == f"{ONE}/cost/buy.flat"
    )
    assert fact.template is TemplateId.COST_BUY
    assert render(fact).text == (
        "Price for a flat: £300,000 to £400,000, middle £350,000, as of August 2026. "
        "Confidence: high."
    )


def test_every_sentence_of_a_price_with_no_range_passes_the_verifier():
    spec = buyer(Strictness.SOFT)
    for area in FLATS:
        facts = facts_of(area, spec)
        for key in (f"{area}/cost/buy.flat", f"{area}/budget_fit/buy.flat"):
            for role in SentenceRole:
                assert verify(render(facts[key], role), facts).ok


def test_an_explanation_gives_a_price_under_the_budget_as_a_reason_and_one_over_it_as_a_cost():
    spec = buyer(Strictness.SOFT)
    release = priced()
    result = rank(spec, release)
    said = {
        found.area_id: found
        for found in explain(result, release, spec, (ONE, THREE), TemplateExplainer())
    }
    assert [s.text for s in said[ONE].reasons] == [
        "The middle price of flats of all sizes is £15,000 under your budget of £400,000."
    ]
    assert said[ONE].trade_off is None
    assert said[THREE].reasons == ()
    given_up = said[THREE].trade_off
    assert given_up is not None
    assert given_up.text == (
        "The middle price of flats of all sizes is £37,500 over your budget of £400,000. "
        "About half of the flats sold here went for under £437,500."
    )
    assert not any(s.replaced for s in (*said[ONE].reasons, given_up))
