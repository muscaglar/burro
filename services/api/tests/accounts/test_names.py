"""The name of a search that is kept: what was understood, said in a line.

It is worked out from the spec and from the names the data gives. No word of it was
typed by anybody, because a spec holds no word that was.
"""

import re
from typing import Any

import pytest
from burro_api.accounts.names import LONGEST, USUAL, name_of
from burro_core import default_spec
from burro_core.ids import (
    AreaRuleKind,
    Direction,
    FeatureId,
    Mode,
    Provenance,
    Segment,
    Strictness,
    TagId,
    Tenure,
    Toward,
)
from burro_core.spec import AreaRule, Budget, Commute, FeatureWeight, PreferenceSpec, TagWeight

from ..support import SCHOOL, WORKS, budget, commute, release, renter, searching

POUND = "\N{POUND SIGN}"


def named(spec: PreferenceSpec) -> str:
    return name_of(spec, release())


def vibe(tag_id: TagId, toward: Toward = Toward.HIGH, weight: float = 0.5) -> TagWeight:
    return TagWeight(tag_id=tag_id, weight=weight, toward=toward, provenance=Provenance.STATED)


def measure(
    feature_id: FeatureId, direction: Direction = Direction.MORE, weight: float = 0.5
) -> FeatureWeight:
    return FeatureWeight(
        feature_id=feature_id, weight=weight, direction=direction, provenance=Provenance.STATED
    )


def buying(amount: int | None, segment: Segment, hard: bool = False) -> PreferenceSpec:
    found = default_spec(Tenure.BUY)
    return found.replace(
        budget=Budget(
            amount=amount,
            segment=segment,
            strictness=Strictness.HARD if hard else Strictness.SOFT,
            weight=0.3,
            provenance=Provenance.STATED,
        )
    )


def test_a_search_that_asks_for_nothing_says_so():
    assert named(renter()) == f"Renting, {USUAL}"
    assert named(default_spec(Tenure.BUY)) == f"Buying, {USUAL}"
    # What no page calls "settings": it is said as the website says it.
    assert USUAL == "with what Burro counts in every search"


@pytest.mark.parametrize("tenure", list(Tenure))
def test_every_kind_of_search_has_a_word_of_its_own(tenure: Tenure):
    # A kind of search that is added to core has no word here until it is given one, and a
    # search of that kind could then not be kept.
    said = named(default_spec(tenure))

    assert re.fullmatch(rf"[A-Z][a-z]+ing, {USUAL}", said), said
    assert len({named(default_spec(each)) for each in Tenure}) == len(Tenure)


def test_a_visit_is_named_as_one_and_has_no_home_and_no_budget_to_name():
    visit = default_spec(Tenure.VISIT)
    out = visit.replace(commutes=(commute(WORKS, 20),), tags=(vibe(TagId.PACE, Toward.HIGH),))

    assert named(visit) == f"Visiting, {USUAL}"
    assert named(out) == (
        "Visiting, about 20 minutes to Cindermoor Works by public transport, Buzzy"
    )
    for said in (named(visit), named(out)):
        assert POUND not in said and "home" not in said and "a month" not in said


def test_a_search_is_said_in_the_order_a_person_would_say_it():
    spec = searching(
        budget=budget(1700, hard=True),
        commutes=(commute(WORKS, 35),),
        tags=(vibe(TagId.LEAFY), vibe(TagId.QUIET_RESIDENTIAL)),
    )

    assert named(spec) == (
        f"Renting a 1-bedroom home, up to {POUND}1,700 a month, "
        "about 35 minutes to Cindermoor Works by public transport, Leafy, Quiet streets"
    )


def test_a_budget_says_whether_it_is_firm_and_what_it_is_paid_by():
    assert f"around {POUND}1,800 a month" in named(renter(budget=budget(1800)))
    assert f"up to {POUND}1,800 a month" in named(renter(budget=budget(1800, hard=True)))
    assert named(buying(400_000, Segment.FLAT, hard=True)) == f"Buying a flat, up to {POUND}400,000"
    assert named(buying(1_250_000, Segment.SEMI_DETACHED)) == (
        f"Buying a semi-detached house, around {POUND}1,250,000"
    )
    # A figure is said whole and with its separator, as the data says it.
    assert "a month" not in named(buying(400_000, Segment.FLAT))


def test_a_home_is_named_only_beside_a_budget_which_is_what_it_is_held_against():
    assert named(renter(budget=budget(None))) == f"Renting, {USUAL}"
    assert "home" not in named(renter(tags=(vibe(TagId.LEAFY),)))


def test_a_journey_says_how_long_where_to_and_by_what_way():
    firm = renter(commutes=(commute(WORKS, 40, hard=True),))
    by_bike = renter(
        commutes=(
            Commute(
                place_id=SCHOOL,
                mode=Mode.CYCLE,
                max_minutes=20,
                strictness=Strictness.SOFT,
                provenance=Provenance.STATED,
            ),
        )
    )

    assert named(firm) == "Renting, at most 40 minutes to Cindermoor Works by public transport"
    assert named(by_bike) == "Renting, about 20 minutes to Alderwick Primary School by bike"


def test_every_journey_is_named_and_a_journey_that_counts_for_nothing_is_not():
    two = renter(commutes=(commute(WORKS, 40), commute(SCHOOL, 30)))

    assert "Cindermoor Works" in named(two) and "Alderwick Primary School" in named(two)
    assert named(two.replace(commute_weight=0.0)) == f"Renting, {USUAL}"


def test_a_vibe_towards_an_end_of_a_scale_is_named_by_that_end():
    calm = renter(tags=(vibe(TagId.PACE, Toward.LOW),))
    buzzy = renter(tags=(vibe(TagId.PACE, Toward.HIGH),))
    historic = renter(tags=(vibe(TagId.BUILT_AGE, Toward.HIGH),))

    assert named(calm) == "Renting, Calm"
    assert named(buzzy) == "Renting, Buzzy"
    assert named(historic) == "Renting, Historic"


def test_a_measure_is_named_as_the_data_names_it_where_it_runs_the_usual_way():
    wish = renter(weights=(measure(FeatureId.BRAND_WAITROSE, Direction.LESS),))

    assert named(wish) == "Renting, Nearer a Waitrose"


def test_a_measure_that_is_turned_round_is_counted_and_never_named_as_its_opposite():
    # "Cleaner air" is what the data calls it. A wish for the other way is no wish for
    # cleaner air, and the name has no words of its own for it.
    turned = renter(weights=(measure(FeatureId.AIR_NO2, Direction.MORE),))

    assert "Cleaner air" not in named(turned)
    assert named(turned) == "Renting, and 1 more thing"


def test_a_usual_setting_that_nobody_chose_is_not_named():
    spec = renter()
    assert spec.active_weights

    assert named(spec) == f"Renting, {USUAL}"
    for weight in spec.active_weights:
        [metric] = [m for m in release().metrics if m.feature_id == weight.feature_id]
        assert metric.short_label not in named(spec)


def test_an_area_that_is_asked_for_or_left_out_is_named_as_the_data_names_it():
    first, second, third = (area for area in list(release().neighbourhoods)[:3])

    def rule(area_id: str, kind: AreaRuleKind) -> AreaRule:
        return AreaRule(area_id=area_id, rule=kind, provenance=Provenance.STATED)

    only = renter(
        areas=(rule(first.area_id, AreaRuleKind.ONLY), rule(second.area_id, AreaRuleKind.ONLY))
    )
    out = renter(areas=(rule(third.area_id, AreaRuleKind.EXCLUDE),))

    assert named(only) == f"Renting, only in {first.name} and {second.name}"
    assert named(out) == f"Renting, not in {third.name}"


def test_no_more_than_a_few_things_are_named_and_the_rest_are_counted():
    every = tuple(vibe(each.tag_id) for each in release().vibes if release().placed(each.tag_id))
    assert len(every) > 8

    said = named(renter(tags=every))

    assert said.endswith(f"and {len(every) - 4} more things")
    assert len(said) <= LONGEST


def test_a_name_is_never_longer_than_it_may_be():
    places = [place.place_id for place in release().places][:3]
    spec = renter(
        budget=budget(19_975, hard=True),
        commutes=tuple(commute(place, 120) for place in places),
        tags=tuple(vibe(each.tag_id) for each in release().vibes),
        areas=tuple(
            AreaRule(area_id=a.area_id, rule=AreaRuleKind.EXCLUDE, provenance=Provenance.STATED)
            for a in release().neighbourhoods
        ),
    )

    assert 0 < len(named(spec)) <= LONGEST == 200


def test_a_place_the_data_no_longer_holds_is_a_journey_with_no_name():
    gone = renter(commutes=(commute("syn-p9999", 30),))

    assert named(gone) == "Renting, about 30 minutes to a place by public transport"


def test_the_same_search_has_the_same_name_and_the_name_holds_no_id():
    spec = searching(tags=(vibe(TagId.LEAFY),), commutes=(commute(SCHOOL, 25),))

    assert named(spec) == named(PreferenceSpec.model_validate(spec.model_dump()))
    assert not re.search(r"syn-|_|\{|\}", named(spec))


@pytest.mark.parametrize("tenure", list(Tenure))
def test_every_kind_of_home_has_words(tenure: Tenure):
    from burro_core.ids import segments_for

    for segment in segments_for(tenure):
        found: Any = default_spec(tenure)
        spec = found.replace(
            budget=found.budget.replace(
                amount=2_000 if tenure is Tenure.RENT else 300_000,
                segment=segment,
                provenance=Provenance.STATED,
            )
        )
        assert re.match(r"(Renting|Buying) an? [a-z0-9]", named(spec)), named(spec)
