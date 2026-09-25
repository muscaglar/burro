"""A rent that is of a wider place than the area: a postcode district, or a borough.

No publisher gives a rent for an area. One gives the rents that were recorded
in each postcode district and in each borough: how many, their middle and
their quartiles. So an area is given the figure of the place it lies in, and
the figure says which place it is of, that it is not of the area alone, the
months it is of and how many rents it rests on. A budget to rent is held
against its middle, as a budget to buy is held against the middle of what
sold.

Every name and figure here is made up.
"""

import re
from typing import Any, cast

import pytest
from burro_core.explain import TEMPLATES, TemplateExplainer, explain, render
from burro_core.facts import IS_OF, RENT_CAUTION, Fact, facts_for
from burro_core.ids import (
    Confidence,
    CostOfKind,
    FactKind,
    FilterReason,
    Segment,
    SentenceRole,
    Strictness,
    TemplateId,
    Tenure,
)
from burro_core.rank import (
    FIRM_BUDGET_MARGIN_PERCENT,
    budget_held_against,
    held_on_the_median,
    over_a_firm_budget,
    rank,
)
from burro_core.release import (
    FEWEST_SALES,
    CostOf,
    InMemoryRelease,
    ReleaseError,
    parse_release,
)
from burro_core.verify import verify

from .recorded import (
    AT_THE_LINE,
    BUDGET,
    DISTRICT,
    FIVE,
    FOUR,
    IN_QUILLHAVEN,
    IN_THE_DISTRICT,
    IN_THE_NEXT,
    MANY,
    ONE,
    OSTREL_VALE,
    QUILLHAVEN,
    SINCE,
    THREE,
    TWO,
    UNTIL,
    let,
    recorded,
    renter,
)
from .support import cost, documents

# What a release holds


def test_a_rent_says_the_place_it_is_of_the_months_and_how_many_rents_it_rests_on():
    held = recorded().cost(ONE, Tenure.RENT, Segment.BED_1)
    assert held is not None
    assert held.of == CostOf(kind=CostOfKind.POSTCODE_DISTRICT, name=DISTRICT)
    assert (held.rents, held.since, held.as_of) == (MANY, SINCE, UNTIL)
    assert (held.lower_quartile, held.median, held.upper_quartile) == (1_350, 1_600, 1_910)
    assert held.ranged and held.sales is None


def test_what_a_rent_rests_on_is_what_its_count_makes_it():
    held = {row.area_id: row for row in recorded().costs}
    assert {area: row.confidence for area, row in held.items()} == {
        ONE: Confidence.HIGH,
        TWO: Confidence.MEDIUM,
        THREE: Confidence.HIGH,
        FIVE: Confidence.HIGH,
    }


def test_a_cost_that_is_of_the_area_alone_says_no_place():
    own = cost(ONE, 1_400)
    assert (own.of, own.rents) == (None, None)


def with_a_rent_of_a_place(**changes: Any) -> dict[str, Any]:
    """The files of the small release, with the rent of a home of one bedroom in its first
    area as a publisher gives it for a district."""
    found = documents()
    rows = cast(list[dict[str, Any]], found["cost.json"]["rows"])
    row = next(row for row in rows if (row["tenure"], row["segment"]) == ("rent", "bed_1"))
    row.update(lower_quartile=1_350, median=1_600, upper_quartile=1_910)
    row.update(confidence="high", rents=MANY, since=SINCE, as_of=UNTIL)
    row.update(of={"kind": "postcode_district", "name": DISTRICT})
    row.update(changes)
    return found


def test_a_release_holds_a_rent_of_a_place_and_writes_it_as_it_reads_it():
    release = parse_release(with_a_rent_of_a_place())
    held = release.cost(ONE, Tenure.RENT, Segment.BED_1)
    assert held is not None and held.of == IN_THE_DISTRICT and held.rents == MANY
    assert parse_release(release.documents()).costs == release.costs


def test_a_rent_may_be_of_the_borough_the_area_is_in():
    release = parse_release(with_a_rent_of_a_place(of={"kind": "borough", "name": QUILLHAVEN}))
    held = release.cost(ONE, Tenure.RENT, Segment.BED_1)
    assert held is not None and held.of == IN_QUILLHAVEN


@pytest.mark.parametrize(
    "changes",
    [
        # A rent of a place is a range. One number is never a rent.
        {"lower_quartile": None, "upper_quartile": None},
        {"lower_quartile": None},
        # A range that is out of order.
        {"lower_quartile": 1_700},
        {"upper_quartile": 1_500},
        # It says how many rents it rests on, and no fewer than a figure may rest on.
        {"rents": None},
        {"rents": FEWEST_SALES - 1, "confidence": "medium"},
        # What it rests on is what its count makes it.
        {"confidence": "medium"},
        {"confidence": "low"},
        {"confidence": "unstated"},
        {"rents": 12},
        # It says the months it is of.
        {"since": None},
        {"since": "2026-04"},
        # It says the place it is of, and a figure that says how many rents says the place.
        {"of": None},
        # A borough that is not the borough the area is in.
        {"of": {"kind": "borough", "name": OSTREL_VALE}},
        # A district that is not written as one is.
        {"of": {"kind": "postcode_district", "name": "Quillhaven"}},
        {"of": {"kind": "postcode_district", "name": "QH1 1CK"}},
        {"of": {"kind": "postcode_district", "name": "qh1"}},
        # Sales are of a price, and a price is of the area.
        {"sales": 120},
    ],
)
def test_a_rent_of_a_place_that_does_not_hold_together_is_refused(changes: dict[str, Any]):
    with pytest.raises(ReleaseError) as caught:
        parse_release(with_a_rent_of_a_place(**changes))
    assert (caught.value.file, caught.value.rule) == ("cost.json", "values_are_in_range")


def test_a_price_says_no_wider_place():
    """A price is worked out from the sales of the area itself."""
    found = documents()
    rows = cast(list[dict[str, Any]], found["cost.json"]["rows"])
    price = next(row for row in rows if (row["tenure"], row["segment"]) == ("buy", "flat"))
    price.update(confidence="high", rents=MANY, since=SINCE)
    price.update(of={"kind": "postcode_district", "name": DISTRICT})
    with pytest.raises(ReleaseError) as caught:
        parse_release(found)
    assert (caught.value.file, caught.value.rule) == ("cost.json", "values_are_in_range")


def test_a_kind_of_place_a_release_does_not_know_is_refused():
    with pytest.raises(ReleaseError) as caught:
        parse_release(with_a_rent_of_a_place(of={"kind": "ward", "name": "Quillhaven"}))
    assert caught.value.file == "cost.json"


def test_two_areas_of_one_place_hold_one_figure():
    """A figure is of the place. An area cannot hold another figure of the same place."""
    same = recorded(let(ONE, 1_600), let(THREE, 1_600))
    assert parse_release(same.documents()).costs == same.costs
    for other in (
        let(THREE, 1_650),
        let(THREE, 1_600, rents=MANY + 10),
        let(THREE, 1_600, upper=2_000),
    ):
        with pytest.raises(ReleaseError) as caught:
            parse_release(recorded(let(ONE, 1_600), other).documents())
        assert (caught.value.file, caught.value.rule) == ("cost.json", "values_are_in_range")


def test_two_kinds_of_home_in_one_place_each_hold_their_own_figure():
    both = recorded(let(ONE, 1_600), let(ONE, 2_000, segment=Segment.BED_2))
    assert parse_release(both.documents()).costs == both.costs


# What a budget is held against


def left_out(release: InMemoryRelease, amount: int = BUDGET) -> list[str]:
    result = rank(renter(Strictness.HARD, amount), release)
    assert {f.reason for f in result.filtered} <= {FilterReason.OVER_BUDGET}
    return [f.area_id for f in result.filtered]


def test_a_budget_to_rent_is_held_against_the_middle_rent_of_the_place():
    row = let(ONE, 1_600)
    assert held_on_the_median(row)
    assert budget_held_against(row) == 1_600
    [area] = rank(renter(Strictness.SOFT), recorded(row)).ranked[:1]
    assert area.area_id == ONE and area.budget is not None
    # The margin is to the middle, and the fit says so: it names no upper end.
    assert (area.budget.margin, area.budget.upper_quartile) == (100, None)
    assert area.budget.utility == 1.0


def test_a_range_of_the_area_alone_is_held_against_its_upper_end_as_it_was():
    own = cost(ONE, 1_700)
    assert not held_on_the_median(own)
    assert budget_held_against(own) == 1_700
    assert not over_a_firm_budget(own, 1_700) and over_a_firm_budget(own, 1_699)


@pytest.mark.parametrize(
    ("middle", "out"),
    [
        (1_699, False),
        (BUDGET, False),
        (BUDGET + 1, False),
        (AT_THE_LINE, False),
        (AT_THE_LINE + 1, True),
        (4_000, True),
    ],
)
def test_a_firm_budget_leaves_a_place_out_only_where_its_middle_rent_is_far_over(
    middle: int, out: bool
):
    assert FIRM_BUDGET_MARGIN_PERCENT == 25
    row = let(ONE, middle)
    assert over_a_firm_budget(row, BUDGET) is out
    assert left_out(recorded(row)) == ([ONE] if out else [])


def test_the_upper_end_of_a_rent_of_a_place_leaves_no_area_out():
    """Half of the rents recorded were under the middle, so the upper end is no limit."""
    row = let(ONE, 1_600, upper=3_000)
    assert not over_a_firm_budget(row, BUDGET)
    assert left_out(recorded(row)) == []


def test_every_area_of_a_place_is_kept_or_left_out_together():
    dear = recorded(let(ONE, 2_200), let(THREE, 2_200), let(TWO, 1_500, of=IN_THE_NEXT))
    assert left_out(dear) == [ONE, THREE]


def test_an_area_kept_by_the_margin_is_ranked_lower_and_never_as_if_within_the_budget():
    kept = recorded(
        let(ONE, 1_600),
        let(TWO, 1_912, of=IN_THE_NEXT),
        let(FIVE, 2_125, IN_QUILLHAVEN),
    )
    result = rank(renter(Strictness.HARD), kept)
    assert result.filtered == ()
    fits = {area.area_id: area.budget for area in result.ranked}
    assert [fits[a].margin for a in (ONE, TWO, FIVE)] == [100, -212, -425]  # pyright: ignore[reportOptionalMemberAccess]
    utilities = [fits[a].utility for a in (ONE, TWO, FIVE)]  # pyright: ignore[reportOptionalMemberAccess]
    assert utilities[0] == 1.0 and 0.5 < utilities[1] < 0.51 and utilities[2] == 0.0
    ranks = {area.area_id: area.rank for area in result.ranked}
    assert ranks[ONE] < ranks[TWO] < ranks[FIVE]


def test_an_area_with_no_rent_is_not_left_out_and_is_said_to_be_untested():
    result = rank(renter(Strictness.HARD), recorded())
    assert FOUR not in {f.area_id for f in result.filtered}
    # The budget is all that was asked, so an area with no rent has nothing to be ranked on.
    assert FOUR in {area.area_id for area in result.unranked}


# What is said


def facts_of(area: str, strictness: Strictness | None = None) -> dict[str, Fact]:
    spec = None if strictness is None else renter(strictness)
    return {fact.fact_id: fact for fact in facts_for(recorded(), area, spec)}


def test_a_rent_of_a_district_says_the_district_the_months_and_the_count():
    fact = facts_of(ONE)[f"{ONE}/cost/rent.bed_1"]
    assert (fact.kind, fact.template) == (FactKind.COST, TemplateId.COST_RENT_RECORDED)
    assert fact.slots == {
        "segment": "1-bedroom home",
        "lower": "1,350",
        "median": "1,600",
        "upper": "1,910",
        "as_of": "March 2026",
        "since": "April 2025",
        "period": "April 2025 to March 2026",
        "rents": "170",
        "of_kind": "postcode district",
        "of_name": "QH1",
        "of": "postcode district QH1",
        "name": "Alderwick",
        "is_of": "This is of postcode district QH1, and not of Alderwick alone.",
        "confidence": "high",
        "half_let": "About half of the rents recorded there were under £1,600.",
        "caution": RENT_CAUTION,
    }
    assert set(fact.numbers) == {
        *("£1350", "£1600", "£1910", "170"),
        *("2025", "04", "4", "2026", "03", "3"),
    }
    assert fact.names == ("QH1", "Alderwick")
    assert render(fact).text == (
        "Rent for a 1-bedroom home: £1,350 to £1,910 a month, middle £1,600. This is of "
        "postcode district QH1, and not of Alderwick alone. It rests on about 170 rents "
        "recorded there from April 2025 to March 2026."
    )


def test_a_rent_of_a_borough_says_that_it_is_of_the_whole_borough():
    fact = facts_of(FIVE)[f"{FIVE}/cost/rent.bed_1"]
    assert fact.template is TemplateId.COST_RENT_RECORDED
    assert (fact.slots["of_kind"], fact.slots["of_name"]) == ("borough", QUILLHAVEN)
    assert render(fact).text == (
        "Rent for a 1-bedroom home: £1,950 to £2,510 a month, middle £2,200. This is of "
        "the whole borough of Quillhaven, and not of Eskerfold alone. It rests on about 520 "
        "rents recorded there from April 2025 to March 2026."
    )


def test_no_sentence_of_a_rent_of_a_place_is_without_the_place_the_months_and_the_count():
    for template in (TemplateId.BUDGET_UNDER_RECORDED, TemplateId.BUDGET_OVER_RECORDED):
        assert "{of}" in TEMPLATES[template]
    told = TEMPLATES[TemplateId.COST_RENT_RECORDED]
    assert "{is_of}" in told and "{rents}" in told and "{period}" in told
    assert IS_OF == "This is of {of}, and not of {name} alone."
    # It prints no word for how sure a figure is: it says how many rents it rests on.
    assert "{confidence}" not in told


def test_a_budget_within_the_middle_rent_says_the_place_the_rent_is_of():
    under = facts_of(ONE, Strictness.HARD)[f"{ONE}/budget_fit/rent.bed_1"]
    assert under.template is TemplateId.BUDGET_UNDER_RECORDED
    assert render(under).text == (
        "The middle rent for a 1-bedroom home in postcode district QH1 is £100 under your "
        "budget of £1,700 a month."
    )
    assert "half" not in render(under).text


def test_a_middle_rent_over_the_budget_says_that_about_half_were_let_for_less():
    facts = facts_of(TWO, Strictness.HARD)
    over = facts[f"{TWO}/budget_fit/rent.bed_1"]
    assert over.template is TemplateId.BUDGET_OVER_RECORDED
    assert render(over).text == (
        "The middle rent for a 1-bedroom home in postcode district QH2 is £200 over your "
        "budget of £1,700 a month. About half of the rents recorded there were under £1,900."
    )
    # The rent itself holds the sentence too, for a page that shows it beside the rent.
    assert facts[f"{TWO}/cost/rent.bed_1"].slots["half_let"] == over.slots["half_let"]


def test_a_budget_held_against_a_boroughs_rent_says_that_it_is_of_the_whole_borough():
    over = facts_of(FIVE, Strictness.SOFT)[f"{FIVE}/budget_fit/rent.bed_1"]
    assert render(over).text.startswith(
        "The middle rent for a 1-bedroom home in the whole borough of Quillhaven is £500 over"
    )


def test_the_fact_of_a_budget_holds_what_the_page_shows_beside_it():
    fit = facts_of(ONE, Strictness.HARD)[f"{ONE}/budget_fit/rent.bed_1"]
    for slot in ("of", "of_kind", "of_name", "is_of", "since", "as_of", "period", "rents"):
        assert fit.slots[slot] == facts_of(ONE)[f"{ONE}/cost/rent.bed_1"].slots[slot]
    assert set(fit.numbers) >= {"£1700", "£1600", "£100", "170"}
    assert "QH1" in fit.names


def test_the_caution_is_in_plain_words_and_quotes_no_figure():
    assert RENT_CAUTION == (
        "These rents are a sample that was not drawn at random. Their publisher advises "
        "against comparing one area with another on them. Burro uses them as a rough guide "
        "to what a home lets for."
    )
    assert re.search(r"[0-9£%]", RENT_CAUTION) is None


def test_a_rent_of_the_area_alone_is_said_as_it_was():
    own = {f.fact_id: f for f in facts_for(recorded(cost(ONE, 1_400)), ONE, None)}
    fact = own[f"{ONE}/cost/rent.bed_1"]
    assert fact.template is TemplateId.COST_RENT
    assert "caution" not in fact.slots and "of" not in fact.slots


def test_every_sentence_of_a_rent_of_a_place_passes_the_verifier():
    for area in (ONE, TWO, THREE, FIVE):
        for strictness in Strictness:
            facts = facts_of(area, strictness)
            for key in (f"{area}/cost/rent.bed_1", f"{area}/budget_fit/rent.bed_1"):
                for role in SentenceRole:
                    assert verify(render(facts[key], role), facts).ok, (area, key, role)


def test_the_card_of_an_area_over_the_budget_says_what_it_gives_up_and_of_which_place():
    spec, release = renter(Strictness.HARD), recorded()
    [said] = explain(rank(spec, release), release, spec, (TWO,), TemplateExplainer())
    assert said.reasons == ()
    assert said.trade_off is not None and not said.trade_off.replaced
    assert "in postcode district QH2" in said.trade_off.text
    assert said.trade_off.text.endswith("About half of the rents recorded there were under £1,900.")


def test_the_card_of_an_area_within_the_budget_gives_the_rent_of_its_place_as_a_reason():
    spec, release = renter(Strictness.SOFT), recorded()
    [said] = explain(rank(spec, release), release, spec, (ONE,), TemplateExplainer())
    assert [reason.text for reason in said.reasons] == [
        "The middle rent for a 1-bedroom home in postcode district QH1 is £100 under your "
        "budget of £1,700 a month."
    ]
    assert not any(reason.replaced for reason in said.reasons)
