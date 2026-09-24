import dataclasses

import pytest
from burro_core.catalogue import FEATURES
from burro_core.explain import render
from burro_core.facts import Fact, fact_id, facts_for, money, month, plain, said, standing
from burro_core.ids import (
    FactKind,
    FeatureId,
    Mode,
    Provenance,
    PtBasis,
    Strictness,
    TemplateId,
    Tenure,
)
from burro_core.rank import rank
from burro_core.release import InMemoryRelease, Origin, ReleaseError
from burro_core.spec import Commute, PreferenceSpec, SpecError, default_spec
from burro_core.verify import normalise_number, verify

from .support import (
    area_id,
    build_worked_release,
    build_worked_spec,
    draws,
    place_id,
    random_spec,
    small_release,
)


def commute(place: int, mode: Mode = Mode.PT, minutes: int = 40) -> Commute:
    return Commute(
        place_id=place_id(place),
        mode=mode,
        max_minutes=minutes,
        strictness=Strictness.SOFT,
        provenance=Provenance.STATED,
    )


def full_spec() -> PreferenceSpec:
    """A spec that asks for something of every kind, so every kind of fact is built."""
    spec = build_worked_spec()
    return spec.replace(
        commutes=(commute(1), commute(2), commute(3, Mode.CYCLE)),
        budget=spec.budget.replace(amount=1500),
    )


def every_fact(release: InMemoryRelease, spec: PreferenceSpec | None) -> list[Fact]:
    return [f for area in release.neighbourhoods for f in facts_for(release, area.area_id, spec)]


def by_id(facts: tuple[Fact, ...]) -> dict[str, Fact]:
    return {fact.fact_id: fact for fact in facts}


def test_every_fact_names_a_source_and_a_date():
    release = small_release()
    facts = every_fact(release, full_spec())
    known = {s.source_id: s.name for s in release.manifest.sources}
    for fact in facts:
        assert fact.sources
        assert all(known[s.source_id] == s.name for s in fact.sources)
        assert [s.source_id for s in fact.sources] == sorted({s.source_id for s in fact.sources})
        assert fact.as_of
        assert fact.synthetic is True
        assert fact.fact_id == f"{fact.area_id}/{fact.kind}/{fact.key}"
    # Every kind, journeys and stations included.
    assert {fact.kind for fact in facts} == set(FactKind)
    assert {fact.template for fact in facts} == set(TemplateId)


def test_each_kind_of_fact_takes_its_date_from_where_the_contract_says():
    release = small_release()
    facts = by_id(facts_for(release, area_id(1), full_spec()))
    dated = {
        "area/name": "2026-09-23",  # the neighbourhoods file
        "feature/park_proximity": "2025",  # the vintage of the catalogue row
        "tag/leafy": "2026-09-23",  # the day the release was built
        "cost/rent.bed_1": "2026-08",  # the cost row
        "budget_fit/rent.bed_1": "2026-08",
        "travel/syn-p0001.pt": "2026-09",  # the travel file
        "station/syn-s0001": "2026-09",  # the stations file
    }
    assert {key: facts[f"{area_id(1)}/{key}"].as_of for key in dated} == dated


def test_facts_come_in_the_order_of_their_ids_and_each_id_once():
    for spec in (None, full_spec()):
        for area in small_release().neighbourhoods:
            ids = [f.fact_id for f in facts_for(small_release(), area.area_id, spec)]
            assert ids == sorted(set(ids))


def test_without_a_spec_the_facts_are_those_of_a_profile_page():
    kinds = {f.kind for f in facts_for(small_release(), area_id(2), None)}
    assert kinds == {FactKind.AREA, FactKind.FEATURE, FactKind.TAG, FactKind.COST, FactKind.STATION}
    with_spec = {f.kind for f in facts_for(small_release(), area_id(2), full_spec())}
    assert with_spec - kinds == {FactKind.TRAVEL, FactKind.BUDGET_FIT}


def test_an_area_the_release_lacks_has_no_facts():
    assert facts_for(small_release(), "syn-n0099", None) == ()
    assert facts_for(small_release(), "", full_spec()) == ()


def test_a_missing_value_never_produces_a_fact_that_carries_a_number():
    release = small_release()
    for area in release.neighbourhoods:
        facts = by_id(facts_for(release, area.area_id, full_spec()))
        for metric in release.metrics:
            row = release.feature(area.area_id, metric.feature_id)
            assert row is not None
            found = facts.get(fact_id(area.area_id, FactKind.FEATURE, metric.feature_id))
            assert (found is None) == (row.value is None)
        for fact in facts.values():
            if fact.kind is FactKind.MISSING:
                assert fact.numbers == ()
                assert not any(c.isdigit() for c in fact.slots["name"])


def test_what_is_missing_for_a_spec_is_stated_as_missing_and_not_as_a_figure():
    release = small_release()
    spec = full_spec()
    # Area 3 has no time to place 2, and area 7 no cost estimate.
    three = by_id(facts_for(release, area_id(3), spec))
    assert f"{area_id(3)}/missing/commute" in three
    assert f"{area_id(3)}/travel/syn-p0002.pt" not in three
    assert f"{area_id(3)}/travel/syn-p0001.pt" in three
    seven = by_id(facts_for(release, area_id(7), spec))
    assert f"{area_id(7)}/missing/budget" in seven
    assert not [f for f in seven.values() if f.kind in (FactKind.COST, FactKind.BUDGET_FIT)]
    # What the spec does not ask for is not reported as missing.
    unasked = spec.replace(commute_weight=0.0, budget=spec.budget.replace(weight=0.0))
    kinds = {f.kind for f in facts_for(release, area_id(3), unasked)}
    assert FactKind.MISSING not in kinds


def test_an_id_that_rank_names_is_always_an_id_that_facts_for_returns():
    release = small_release()
    draw = draws(51)
    cited = 0
    for _ in range(60):
        spec = random_spec(draw, release)
        for area in rank(spec, release).ranked:
            known = {f.fact_id for f in facts_for(release, area.area_id, spec)}
            for contribution in area.contributions:
                assert contribution.fact_ids
                assert set(contribution.fact_ids) <= known
                cited += len(contribution.fact_ids)
    assert cited > 500


def test_a_feature_fact_holds_the_value_and_the_share_of_areas_strictly_beyond_it():
    release = small_release()
    row = release.feature(area_id(1), FeatureId.NOISE_EXPOSURE)
    assert row is not None
    # It is scored on the mid-rank percentile, which counts half of itself as beaten.
    assert (row.value, row.percentile) == (15.0, 21.4)
    noise = [
        found.value
        for area in release.neighbourhoods
        if area.rankable
        and (found := release.feature(area.area_id, FeatureId.NOISE_EXPOSURE)) is not None
        and found.value is not None
    ]
    assert (len(noise), sum(v > 15.0 for v in noise), sum(v == 15.0 for v in noise)) == (7, 5, 1)
    fact = by_id(facts_for(release, area_id(1), None))[f"{area_id(1)}/feature/noise_exposure"]
    # Five of seven is 71.4%. The sentence says 71, which is true, and never 79.
    assert fact.numbers == ("15%", "71%", "7")
    assert fact.slots == {
        "label": "Share of homes at 55 dB or more of transport noise",
        "value": "15%",
        "comparative": "quieter than",
        "pct": "71",
        "compared": "7",
        "standing": "quieter than 71% of the 7 areas compared in this release",
    }
    assert fact.names == ()
    assert fact.template is TemplateId.FEATURE


def with_values(feature_id: FeatureId, *values: float | None) -> InMemoryRelease:
    """The small release with one feature given these values, area by area."""
    release = small_release()
    given = dict(zip((a.area_id for a in release.neighbourhoods), values, strict=False))
    return dataclasses.replace(
        release,
        features=tuple(
            row.replace(value=given[row.area_id], percentile=0.0, coverage=1.0)
            if row.feature_id is feature_id and given.get(row.area_id) is not None
            else row.replace(value=None, percentile=None, coverage=0.0)
            if row.feature_id is feature_id
            else row
            for row in release.features
        ),
    )


def water(release: InMemoryRelease, number: int) -> Fact:
    return by_id(facts_for(release, area_id(number), None))[
        f"{area_id(number)}/feature/water_access"
    ]


STANDING = [
    # The figure of each of the eight areas, the eighth of which is not rankable.
    # Then the area, and what is said of it.
    (
        (0, 0, 0, 0, 5, 9, 12),
        1,
        "less than 42% of the 7 areas compared in this release, and the same as 3 others",
    ),
    ((0, 0, 0, 0, 5, 9, 12), 5, "more than 57% of the 7 areas compared in this release"),
    ((0, 0, 0, 0, 5, 9, 12), 7, "more than 85% of the 7 areas compared in this release"),
    (
        (1, 1, 2, 2, 3, 3, 4),
        3,
        "less than 42% of the 7 areas compared in this release, and the same as 1 other",
    ),
    ((3, 3, 3, 3, 3, 3, 3), 4, "the same as all 6 other areas compared in this release"),
    (
        (3, 3, None, None, None, None, None),
        1,
        "the same as the only other area compared in this release",
    ),
    (
        (3, None, None, None, None, None, None),
        1,
        "with no other area in this release to compare it with",
    ),
    # An area that is not rankable is placed against the seven and is not one of them.
    (
        (0, 0, 0, 0, 5, 9, 12, 0),
        8,
        "less than 42% of the 7 areas compared in this release, and the same as 4 others",
    ),
    ((0, 0, 0, 0, 5, 9, 12, 20), 8, "more than 100% of the 7 areas compared in this release"),
    ((3, 3, 3, 3, 3, 3, 3, 3), 8, "the same as all 7 other areas compared in this release"),
]


@pytest.mark.parametrize(("values", "number", "clause"), STANDING)
def test_a_comparison_counts_only_the_areas_strictly_beyond_and_says_how_many_are_level(
    values: tuple[float | None, ...], number: int, clause: str
):
    fact = water(with_values(FeatureId.WATER_ACCESS, *values), number)
    assert fact.slots["standing"] == clause
    text = render(fact).text
    assert (
        text
        == f"Share of the area within 300 m of a river or canal: {fact.slots['value']}, "
        + (f"{clause}.")
    )
    assert verify(render(fact), {fact.fact_id: fact}).ok


def test_a_share_is_rounded_down_and_never_to_the_nearest():
    # Two of three areas are beyond: 66.67%. "More than 67%" would be untrue.
    fact = water(with_values(FeatureId.WATER_ACCESS, 1, 2, 3), 3)
    assert fact.slots["pct"] == "66"
    assert standing(3.0, [1.0, 2.0, 3.0], among=True).pct == 66
    # Under one area in a hundred is beyond this one. "More than 0%" says
    # nothing, so what is said is how many are level with it.
    most = standing(5.0, [1.0, *[5.0] * 199], among=True)
    assert (most.pct, most.below, most.level, most.others) == (0, 1, 198, 199)
    slots, numbers = said(most, "more than", "less than")
    assert slots["standing"] == "the same as 198 of the 199 other areas compared in this release"
    assert numbers == ("198", "199")


def test_the_side_a_comparison_is_made_from_is_the_side_the_percentile_is_on():
    release = small_release()
    for area in release.neighbourhoods:
        for fact in facts_for(release, area.area_id, None):
            if fact.kind is not FactKind.FEATURE or "comparative" not in fact.slots:
                continue
            row = release.feature(area.area_id, FeatureId(fact.key))
            assert row is not None and row.percentile is not None
            feature = FEATURES[FeatureId(fact.key)]
            higher = fact.slots["comparative"] == f"{feature.higher} than"
            assert higher == (row.percentile >= 50), fact.fact_id


def test_recorded_crime_is_stated_with_its_caveat():
    facts = facts_for(small_release(), area_id(2), None)
    crime = [f for f in facts if f.key.startswith("crime_")]
    assert len(crime) == 2
    assert {f.template for f in crime} == {TemplateId.FEATURE_CRIME}
    assert {f.template for f in facts if f.kind is FactKind.FEATURE} == {
        TemplateId.FEATURE,
        TemplateId.FEATURE_CRIME,
    }


@pytest.mark.parametrize(
    ("value", "text"), [(3.0, "3"), (42.46, "42.5"), (0.04, "0"), (-0.01, "0"), (1234.5, "1234.5")]
)
def test_a_number_is_printed_to_one_decimal_with_a_trailing_zero_dropped(value: float, text: str):
    assert plain(value) == text
    assert normalise_number(text) == text


def test_money_has_thousands_separators_and_a_month_is_written_as_people_write_it():
    assert money(1750) == "1,750"
    assert money(450000) == "450,000"
    assert normalise_number(money(1234567)) == "1234567"
    assert month("2026-08") == "August 2026"
    assert month("2025-12") == "December 2025"


def test_a_cost_fact_holds_the_quartiles_and_the_month():
    fact = by_id(facts_for(small_release(), area_id(2), None))[f"{area_id(2)}/cost/rent.bed_1"]
    assert fact.slots == {
        "segment": "1-bedroom home",
        "lower": "1,200",
        "median": "1,350",
        "upper": "1,500",
        "as_of": "August 2026",
        "confidence": "high",
    }
    # Money is held as money, so that a sentence cannot say it of anything else.
    assert set(fact.numbers) == {"£1200", "£1350", "£1500", "2026", "08", "8"}


def test_a_budget_fact_says_which_side_of_the_budget_the_upper_quartile_falls():
    release = build_worked_release()
    spec = build_worked_spec()
    under = by_id(facts_for(release, area_id(1), spec))[f"{area_id(1)}/budget_fit/rent.bed_1"]
    over = by_id(facts_for(release, area_id(2), spec))[f"{area_id(2)}/budget_fit/rent.bed_1"]
    assert (under.template, under.slots["margin"], under.numbers) == (
        TemplateId.BUDGET_UNDER,
        "50",
        ("£1800", "£1750", "£50"),
    )
    assert (over.template, over.slots["margin"], over.numbers) == (
        TemplateId.BUDGET_OVER,
        "150",
        ("£1800", "£1950", "£150"),
    )


def test_a_journey_fact_holds_each_time_that_is_known_and_the_name_of_the_place():
    release = small_release()
    spec = full_spec()
    one = by_id(facts_for(release, area_id(1), spec))
    by_train = one[f"{area_id(1)}/travel/syn-p0001.pt"]
    assert (by_train.template, by_train.numbers) == (TemplateId.TRAVEL_PT, ("15", "20"))
    assert by_train.names == ("Pellam Cross",)
    by_bike = one[f"{area_id(1)}/travel/syn-p0003.cycle"]
    assert (by_bike.template, by_bike.numbers) == (TemplateId.TRAVEL_OTHER, ("51",))
    assert by_bike.slots == {"mode": "By bike", "place": "Wexmoor University", "minutes": "51"}

    # Area 4 has no journey to place 3 within the cutoff. All that is known is the cutoff.
    beyond = by_id(facts_for(release, area_id(4), spec))[f"{area_id(4)}/travel/syn-p0003.cycle"]
    assert (beyond.template, beyond.numbers) == (TemplateId.TRAVEL_BEYOND, ("60",))
    assert beyond.slots["cutoff"] == "60"


def test_a_journey_with_only_one_public_transport_time_states_that_one():
    release = build_worked_release()
    table = release.travel_table
    one_time = dataclasses.replace(
        release,
        travel_table=table.replace(pt_just_missed=tuple((None, None) for _ in range(4))),
    )
    fact = by_id(facts_for(one_time, area_id(1), build_worked_spec()))
    journey = fact[f"{area_id(1)}/travel/syn-p0001.pt"]
    assert (journey.template, journey.numbers) == (TemplateId.TRAVEL_OTHER, ("32",))
    assert journey.slots["mode"] == "By public transport"

    # Scored on the time that is not there, the journey is missing, not guessed from the other.
    missed = build_worked_spec().replace(pt_basis=PtBasis.JUST_MISSED)
    facts = by_id(facts_for(one_time, area_id(1), missed))
    assert f"{area_id(1)}/travel/syn-p0001.pt" not in facts
    assert f"{area_id(1)}/missing/commute" in facts


def test_a_station_fact_names_the_station_and_its_lines():
    facts = by_id(facts_for(small_release(), area_id(2), None))
    nearest = facts[f"{area_id(2)}/station/syn-s0002"]
    assert nearest.template is TemplateId.STATION
    assert nearest.names == ("Tinderside Halt", "Birch line")
    assert nearest.numbers == ("5",)
    nearby = facts[f"{area_id(2)}/station/syn-s0003"]
    assert nearby.template is TemplateId.STATION_NEARBY


def test_a_tag_fact_cites_the_sources_of_the_features_that_had_a_value():
    release = build_worked_release()
    real = release.manifest.sources[0].replace(
        source_id="parks-source", name="Parks", attribution="Source: parks."
    )
    noise = real.replace(source_id="noise-source", name="Noise")
    cited = dataclasses.replace(
        release,
        manifest=release.manifest.replace(sources=(*release.manifest.sources, real, noise)),
        metrics=tuple(
            m.replace(
                source_ids=("parks-source",)
                if m.feature_id is FeatureId.PARK_PROXIMITY
                else ("noise-source",)
            )
            for m in release.metrics
        ),
    )
    leafy = by_id(facts_for(cited, area_id(1), None))[f"{area_id(1)}/tag/leafy"]
    # Leafy is built from green cover, parks and density. Only parks has a value
    # here, and noise is no part of the formula.
    assert [s.source_id for s in leafy.sources] == ["parks-source"]
    assert leafy.as_of == "2026-09-23"
    # Its score is 72, which is what it is ranked on. Two of the four areas score lower.
    assert leafy.numbers == ("50%", "4")
    assert leafy.slots["standing"] == "above 50% of the 4 areas compared in this release"


def test_a_fact_is_never_given_a_source_the_release_does_not_state():
    release = build_worked_release()
    unstated = dataclasses.replace(
        release, stations_origin=Origin(source_ids=("somewhere",), as_of="2026-09")
    )
    # No station rows, so no fact needs that source, and none is invented.
    assert facts_for(unstated, area_id(1), None)
    orphan = dataclasses.replace(
        release, neighbourhoods_origin=Origin(source_ids=("somewhere",), as_of="2026-09")
    )
    with pytest.raises(ReleaseError):
        facts_for(orphan, area_id(1), None)
    # A tag score with no feature behind it would be a fact with no source.
    no_features = dataclasses.replace(release, features=())
    with pytest.raises(ReleaseError):
        facts_for(no_features, area_id(1), None)


def test_facts_refuse_a_spec_the_release_cannot_rank():
    spec = default_spec(Tenure.RENT).replace(commutes=(commute(9),))
    with pytest.raises(SpecError):
        facts_for(small_release(), area_id(1), spec)
