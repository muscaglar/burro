"""A firm budget, held against a median of what sold.

Half of the homes behind a median sold for less than it. So a firm budget
leaves an area out on a median only where the median is over the budget by
more than a margin, which is written in one place. An area that is kept with
its median over the budget is ranked lower for it, and says that about half
of the homes sold for less. A median may say how many sales it rests on, and
then it says so.

Every name and figure here is made up.
"""

import dataclasses
from importlib import import_module
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
)
from burro_core.rank import (
    BUDGET_OVER_SHARE,
    FIRM_BUDGET_MARGIN_PERCENT,
    over_a_firm_budget,
    rank,
)
from burro_core.release import (
    FEWEST_SALES,
    MANY_SALES,
    InMemoryRelease,
    ReleaseError,
    confidence_of,
    parse_release,
)
from burro_core.verify import verify

from .no_range import FLATS, ONE, SALES, SINCE, THREE, TWO, buyer, counted, median, priced, sold
from .support import AS_OF, cost, documents, small_release

BUDGET = 400_000
# The most a median may be and not be left out by a firm budget of 400,000.
AT_THE_LINE = 500_000


def one_flat(row: Any) -> InMemoryRelease:
    """The small release, with one price of a flat in its first area and no other price."""
    return dataclasses.replace(small_release(), costs=(row,))


def left_out(release: InMemoryRelease, amount: int = BUDGET) -> list[str]:
    result = rank(buyer(Strictness.HARD, amount), release)
    assert {f.reason for f in result.filtered} <= {FilterReason.OVER_BUDGET}
    return [f.area_id for f in result.filtered]


# The margin


def test_the_margin_is_written_once_and_is_a_quarter():
    assert FIRM_BUDGET_MARGIN_PERCENT == 25
    # A firm budget leaves out what a flexible one counts for nothing, and no more.
    assert FIRM_BUDGET_MARGIN_PERCENT == 100 * BUDGET_OVER_SHARE
    # The package gives the function its module's name, so the module is asked for by name.
    named = [name for name in vars(import_module("burro_core.rank")) if "MARGIN" in name]
    assert named == ["FIRM_BUDGET_MARGIN_PERCENT"]


@pytest.mark.parametrize(
    ("paid", "out"),
    [
        (399_999, False),
        (BUDGET, False),
        (BUDGET + 1, False),
        (AT_THE_LINE, False),
        (AT_THE_LINE + 1, True),
        (1_000_000, True),
    ],
)
def test_a_median_is_over_a_firm_budget_only_beyond_the_margin(paid: int, out: bool):
    for row in (median(ONE, paid), counted(ONE, paid, 120)):
        assert over_a_firm_budget(row, BUDGET) is out
        assert left_out(one_flat(row)) == ([ONE] if out else [])


def test_the_line_is_counted_in_whole_pounds():
    """No float decides which side of the line an area falls."""
    # A quarter over 333,333 is 416,666.25: a median of 416,666 is within it, and one of
    # 416,667 is not.
    assert not over_a_firm_budget(median(ONE, 416_666), 333_333)
    assert over_a_firm_budget(median(ONE, 416_667), 333_333)


def test_a_range_is_held_against_its_upper_quartile_as_it_was():
    """The margin is for a median of what sold. A range has an upper end to hold."""
    ranged = cost(ONE, 400_000, Tenure.BUY)
    assert ranged.upper_quartile == 400_000
    assert not over_a_firm_budget(ranged, 400_000)
    assert over_a_firm_budget(ranged, 399_999)
    assert left_out(one_flat(ranged), 399_999) == [ONE]


def test_an_area_kept_by_the_margin_is_ranked_lower_and_never_as_if_within_the_budget():
    kept = dataclasses.replace(
        small_release(), costs=(median(ONE, 380_000), median(TWO, 450_000), median(THREE, 500_000))
    )
    result = rank(buyer(Strictness.HARD), kept)
    assert result.filtered == ()
    fits = {area.area_id: area.budget for area in result.ranked}
    assert [fits[a].utility for a in (ONE, TWO, THREE)] == [1.0, 0.5, 0.0]  # pyright: ignore[reportOptionalMemberAccess]
    assert [fits[a].margin for a in (ONE, TWO, THREE)] == [20_000, -50_000, -100_000]  # pyright: ignore[reportOptionalMemberAccess]
    ranks = {area.area_id: area.rank for area in result.ranked}
    assert ranks[ONE] < ranks[TWO] < ranks[THREE]


def test_a_firm_budget_and_a_flexible_one_rank_the_areas_that_are_kept_alike():
    """Firm is a filter and no weight: what it keeps is scored as a flexible budget scores it."""
    firm, soft = (rank(buyer(strictness), priced()) for strictness in Strictness)
    assert [a.area_id for a in firm.ranked] == [a.area_id for a in soft.ranked]
    assert [a.score for a in firm.ranked] == [a.score for a in soft.ranked]


# A median that says how many sales it rests on


def test_a_median_may_say_how_many_sales_it_rests_on():
    held = sold().cost(ONE, Tenure.BUY, Segment.FLAT)
    assert held is not None
    assert (held.sales, held.since, held.as_of) == (1_204, SINCE, AS_OF)
    assert (held.lower_quartile, held.upper_quartile) == (None, None)
    assert held.counted and not held.ranged


def test_what_a_counted_median_rests_on_is_what_its_count_makes_it():
    assert (FEWEST_SALES, MANY_SALES) == (10, 50)
    assert confidence_of(FEWEST_SALES) is Confidence.MEDIUM
    assert confidence_of(MANY_SALES - 1) is Confidence.MEDIUM
    assert confidence_of(MANY_SALES) is Confidence.HIGH
    held = {area: sold().cost(area, Tenure.BUY, Segment.FLAT) for area in FLATS}
    assert {area: row.confidence for area, row in held.items() if row} == {
        ONE: Confidence.HIGH,
        TWO: Confidence.HIGH,
        THREE: Confidence.MEDIUM,
    }


def with_a_counted_cost(**changes: Any) -> dict[str, Any]:
    """The files of the small release, with its first price of a flat a counted median."""
    found = documents()
    rows = cast(list[dict[str, Any]], found["cost.json"]["rows"])
    row = next(row for row in rows if (row["tenure"], row["segment"]) == ("buy", "flat"))
    row.update(lower_quartile=None, upper_quartile=None)
    row.update(confidence="high", sales=120, since=SINCE)
    row.update(changes)
    return found


def test_a_release_holds_a_counted_median_and_writes_it_as_it_reads_it():
    release = parse_release(with_a_counted_cost())
    held = release.cost(ONE, Tenure.BUY, Segment.FLAT)
    assert held is not None and (held.sales, held.since) == (120, SINCE)
    assert parse_release(release.documents()).costs == release.costs


@pytest.mark.parametrize(
    "changes",
    [
        # Fewer sales than a figure may rest on.
        {"sales": FEWEST_SALES - 1, "confidence": "medium"},
        # What it rests on is not what its count makes it.
        {"sales": 120, "confidence": "medium"},
        {"sales": 12, "confidence": "high"},
        {"sales": 120, "confidence": "unstated"},
        {"sales": 120, "confidence": "low"},
        # A count with no first month, and a first month with no count.
        {"since": None},
        {"sales": None, "confidence": "unstated"},
        # The sales end before they begin.
        {"since": "2026-09"},
        # A range holds no count: no step works one out with a count behind it yet.
        {"lower_quartile": 300_000, "upper_quartile": 400_000},
    ],
)
def test_a_counted_median_that_does_not_hold_together_is_refused(changes: dict[str, Any]):
    with pytest.raises(ReleaseError) as caught:
        parse_release(with_a_counted_cost(**changes))
    assert (caught.value.file, caught.value.rule) == ("cost.json", "values_are_in_range")


def test_a_counted_rent_is_refused():
    found = documents()
    rows = cast(list[dict[str, Any]], found["cost.json"]["rows"])
    rent = next(row for row in rows if row["tenure"] == "rent")
    rent.update(lower_quartile=None, upper_quartile=None)
    rent.update(confidence="high", sales=120, since=SINCE)
    with pytest.raises(ReleaseError) as caught:
        parse_release(found)
    assert (caught.value.file, caught.value.rule) == ("cost.json", "values_are_in_range")


# What is said


def facts_of(area: str, strictness: Strictness | None = None) -> dict[str, Fact]:
    spec = None if strictness is None else buyer(strictness)
    return {fact.fact_id: fact for fact in facts_for(sold(), area, spec)}


def test_a_counted_median_says_how_many_sales_it_rests_on_and_when_they_were_made():
    fact = facts_of(ONE)[f"{ONE}/cost/buy.flat"]
    assert (fact.kind, fact.template) == (FactKind.COST, TemplateId.COST_BUY_SOLD)
    assert fact.slots == {
        "segment": "flat",
        "homes": "flats",
        "median": "385,000",
        "as_of": "August 2026",
        "since": "September 2023",
        "period": "September 2023 to August 2026",
        "sales": "1,204",
        "confidence": "high",
        "half_sold": "About half of the flats sold here went for under £385,000.",
    }
    assert set(fact.numbers) == {"£385000", "1204", "2026", "08", "8", "2023", "09", "9"}
    assert render(fact).text == (
        "Price for a flat: £385,000. This is the middle price of the 1,204 flats of all sizes "
        "sold from September 2023 to August 2026."
    )


def test_the_sentence_of_a_counted_median_states_no_range_and_no_price_by_bedrooms():
    text = TEMPLATES[TemplateId.COST_BUY_SOLD]
    assert "{lower}" not in text and "{upper}" not in text and "{confidence}" not in text
    assert "of all sizes" in text and "bedroom" not in text


def test_a_median_over_the_budget_says_that_about_half_sold_for_less():
    for release in (priced(), sold()):
        facts = {f.fact_id: f for f in facts_for(release, THREE, buyer(Strictness.HARD))}
        over = facts[f"{THREE}/budget_fit/buy.flat"]
        assert over.template is TemplateId.BUDGET_OVER_MEDIAN
        assert render(over).text == (
            "The middle price of flats of all sizes is £37,500 over your budget of £400,000. "
            "About half of the flats sold here went for under £437,500."
        )
        # The price itself holds the sentence too, for a page that shows it beside the price.
        price = facts[f"{THREE}/cost/buy.flat"]
        assert price.slots["half_sold"] == over.slots["half_sold"]


def test_a_median_within_the_budget_does_not_say_it():
    under = facts_of(ONE, Strictness.HARD)[f"{ONE}/budget_fit/buy.flat"]
    assert under.template is TemplateId.BUDGET_UNDER_MEDIAN
    assert "half" not in render(under).text


def test_every_sentence_of_a_counted_median_passes_the_verifier():
    for area in FLATS:
        facts = facts_of(area, Strictness.HARD)
        for key in (f"{area}/cost/buy.flat", f"{area}/budget_fit/buy.flat"):
            for role in SentenceRole:
                assert verify(render(facts[key], role), facts).ok


def test_the_card_of_an_area_kept_by_the_margin_says_what_it_gives_up():
    spec, release = buyer(Strictness.HARD), sold()
    [said] = explain(rank(spec, release), release, spec, (THREE,), TemplateExplainer())
    assert said.reasons == ()
    assert said.trade_off is not None and not said.trade_off.replaced
    assert said.trade_off.text.endswith(
        "About half of the flats sold here went for under £437,500."
    )


def test_how_many_sales_stand_behind_each_median_is_as_the_release_holds_it():
    assert {
        a: (row.sales if row else None)
        for a in FLATS
        for row in [sold().cost(a, Tenure.BUY, Segment.FLAT)]
    } == SALES
