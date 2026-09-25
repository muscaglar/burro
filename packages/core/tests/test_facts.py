import dataclasses

import pytest
from burro_core.catalogue import FEATURES, JUDGEMENT, MADE_FROM, TAGS, default_direction
from burro_core.explain import render
from burro_core.facts import Fact, fact_id, facts_for, money, month, plain, said, standing
from burro_core.ids import (
    Direction,
    FactKind,
    FeatureId,
    GrittyVariant,
    Mode,
    NameState,
    Polarity,
    Provenance,
    PtBasis,
    SentenceRole,
    Strictness,
    TagId,
    TemplateId,
    Tenure,
)
from burro_core.rank import rank
from burro_core.release import InMemoryRelease, Named, Origin, ReleaseError
from burro_core.spec import Commute, FeatureWeight, PreferenceSpec, SpecError, default_spec
from burro_core.verify import normalise_number, verify

from .support import (
    area_id,
    build_worked_release,
    build_worked_spec,
    draws,
    place_id,
    preview_release,
    random_spec,
    small_release,
    with_figures,
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


def mixed(release: InMemoryRelease, tag_id: TagId = TagId.PACE) -> InMemoryRelease:
    """The release with one area that holds both ends of a scale, as a release may say of one."""
    return dataclasses.replace(
        release,
        tags=tuple(
            row.replace(spread_low=max(row.band - 1, 1), spread_high=min(row.band + 1, 5))
            if row.tag_id is tag_id and row.band in (2, 3, 4)
            else row
            for row in release.tags
        ),
    )


def level() -> InMemoryRelease:
    """A release in which every area has the same figure for everything likeness is counted on."""
    same = {f: (1.0,) * 8 for f, feature in FEATURES.items() if feature.in_likeness}
    carried = {metric.feature_id for metric in small_release().metrics}
    return with_figures(small_release(), {f: v for f, v in same.items() if f in carried})


def test_every_fact_names_a_source_and_a_date():
    facts: list[Fact] = []
    for release in (small_release(), mixed(small_release()), level()):
        known = {s.source_id: s.name for s in release.manifest.sources}
        published = {s.source_id: s.publisher for s in release.manifest.sources}
        for spec in (None, full_spec(), full_spec().replace(commutes=(commute(1, minutes=10),))):
            found = every_fact(release, spec)
            facts += found
            for fact in found:
                assert fact.sources
                assert all(known[s.source_id] == s.name for s in fact.sources)
                # Who published each is said with its name, so that no page has to look it up.
                assert all(published[s.source_id] == s.publisher for s in fact.sources)
                assert all(s.publisher for s in fact.sources)
                assert [s.source_id for s in fact.sources] == sorted(
                    {s.source_id for s in fact.sources}
                )
                assert fact.as_of
                assert fact.synthetic is True
                assert fact.fact_id == f"{fact.area_id}/{fact.kind}/{fact.key}"
    # Every kind, journeys and stations included, and every way of saying each. No price
    # of these releases is without a range: `test_a_price_with_no_range.py` holds those.
    # No rent of them is of a wider place: `test_a_rent_of_a_wider_place.py` holds those.
    # And no journey of them is estimated: `test_estimate.py` holds that fact to the same.
    elsewhere = {
        TemplateId.COST_BUY_MEDIAN,
        TemplateId.COST_BUY_SOLD,
        TemplateId.COST_RENT_RECORDED,
        TemplateId.BUDGET_UNDER_MEDIAN,
        TemplateId.BUDGET_OVER_MEDIAN,
        TemplateId.BUDGET_AT_MEDIAN,
        TemplateId.BUDGET_UNDER_RECORDED,
        TemplateId.BUDGET_OVER_RECORDED,
        TemplateId.BUDGET_AT_RECORDED,
        TemplateId.TRAVEL_ESTIMATED,
    }
    assert {fact.kind for fact in facts} == set(FactKind)
    assert {fact.template for fact in facts} == set(TemplateId) - elsewhere


def test_a_fact_carries_the_statement_of_a_source_whose_publisher_asks_to_see_it_by_a_figure():
    """A publisher may ask that its statement of credit stands wherever a figure made from
    its data is shown. The release says so of the source, and a fact that cites it carries
    the statement. Any other source is credited by its name and its publisher."""
    release = small_release()
    assert not any(source.credit_beside_figures for source in release.manifest.sources)
    for fact in every_fact(release, full_spec()):
        assert [source.attribution for source in fact.sources] == [None] * len(fact.sources)
    asked = dataclasses.replace(
        release,
        manifest=release.manifest.replace(
            sources=tuple(
                source.replace(credit_beside_figures=True) for source in release.manifest.sources
            )
        ),
    )
    stated = {source.source_id: source.attribution for source in asked.manifest.sources}
    found = every_fact(asked, full_spec())
    assert found
    for fact in found:
        assert [source.attribution for source in fact.sources] == [
            stated[source.source_id] for source in fact.sources
        ]
        assert all(source.attribution for source in fact.sources)


def test_what_is_said_with_a_credit_goes_wherever_the_credit_goes_and_nowhere_else():
    """The terms of a publisher may ask that something is said wherever its credit is
    shown. The release holds it with the source, and a fact carries it with the credit.
    A source that is credited by its name and its publisher brings neither."""
    asked = "The publisher cannot warrant the quality or accuracy of the data."
    release = small_release()
    assert not any(source.said_with_attribution for source in release.manifest.sources)

    def saying_so(*, beside_figures: bool) -> InMemoryRelease:
        sources = tuple(
            source.replace(said_with_attribution=asked, credit_beside_figures=beside_figures)
            for source in release.manifest.sources
        )
        return dataclasses.replace(release, manifest=release.manifest.replace(sources=sources))

    for fact in every_fact(saying_so(beside_figures=False), full_spec()):
        for source in fact.sources:
            assert (source.attribution, source.said_with_attribution) == (None, None)
    found = every_fact(saying_so(beside_figures=True), full_spec())
    assert found
    for fact in found:
        for source in fact.sources:
            assert source.attribution and source.said_with_attribution == asked
    # Where the credit stands beside a figure and nothing is asked to be said with it,
    # nothing is.
    credited = dataclasses.replace(
        release,
        manifest=release.manifest.replace(
            sources=tuple(
                source.replace(credit_beside_figures=True) for source in release.manifest.sources
            )
        ),
    )
    for fact in every_fact(credited, full_spec()):
        assert [source.said_with_attribution for source in fact.sources] == [None] * len(
            fact.sources
        )


def test_each_kind_of_fact_takes_its_date_from_where_the_contract_says():
    release = small_release()
    facts = by_id(facts_for(release, area_id(1), full_spec()))
    dated = {
        "area/name": "2026-09-23",  # the neighbourhoods file
        "feature/park_proximity": "2025",  # the vintage of the catalogue row
        "tag/parks_close_by": "2025",  # the span of its parts, never the day it was built
        "cost/rent.bed_1": "2026-08",  # the cost row
        "budget_fit/rent.bed_1": "2026-08",
        "travel/syn-p0001.pt": "2026-09",  # the travel file
        "station/syn-s0001": "2026-09",  # the stations file
    }
    assert {key: facts[f"{area_id(1)}/{key}"].as_of for key in dated} == dated
    # An area with no time to a place: the fact that says so is dated as the journeys are.
    missing = by_id(facts_for(release, area_id(3), full_spec()))
    assert missing[f"{area_id(3)}/missing/commute.syn-p0002.pt"].as_of == "2026-09"
    profile = by_id(facts_for(release, area_id(1), None))
    assert {f.as_of for f in profile.values() if f.kind is FactKind.LIKENESS} == {"2025"}


def test_facts_come_in_the_order_of_their_ids_and_each_id_once():
    for spec in (None, full_spec()):
        for area in small_release().neighbourhoods:
            ids = [f.fact_id for f in facts_for(small_release(), area.area_id, spec)]
            assert ids == sorted(set(ids))


def test_without_a_spec_the_facts_are_those_of_a_profile_page():
    kinds = {f.kind for f in facts_for(small_release(), area_id(2), None)}
    assert kinds == {
        FactKind.AREA,
        FactKind.FEATURE,
        FactKind.TAG,
        FactKind.COST,
        FactKind.STATION,
        FactKind.LIKENESS,
    }
    with_spec = {f.kind for f in facts_for(small_release(), area_id(2), full_spec())}
    assert with_spec - kinds == {FactKind.TRAVEL, FactKind.BUDGET_FIT}
    # Which areas are like this one is for a profile page, and no ranking needs it.
    assert kinds - with_spec == {FactKind.LIKENESS}


def bearing_a_name(state: NameState = NameState.DRAFT) -> InMemoryRelease:
    """The small release, with its first area under a name that is not its publisher's label."""
    release = small_release()
    named = Named(label="Quillhaven 001", source_ids=("synthetic",), state=state)
    first, *rest = release.neighbourhoods
    return dataclasses.replace(release, neighbourhoods=(first.replace(named=named), *rest))


def test_the_fact_of_an_area_says_who_wrote_its_name_and_whether_a_person_has_checked_it():
    drafted = by_id(facts_for(bearing_a_name(), area_id(1), None))
    fact = drafted[fact_id(area_id(1), FactKind.AREA, "name")]
    assert fact.slots == {
        "name": "Alderwick",
        "borough": "Quillhaven",
        "label": "Quillhaven 001",
        "written_by": "Burro",
        "state": "draft",
    }
    # The label is shown beside the name, so it is a name the fact may print.
    assert fact.names == ("Alderwick", "Quillhaven", "Quillhaven 001")
    assert [source.source_id for source in fact.sources] == ["synthetic"]
    # What is said of the area is the sentence it always was, and holds no word of a draft.
    assert render(fact).text == "Alderwick is in Quillhaven."
    checked = by_id(facts_for(bearing_a_name(NameState.CHECKED), area_id(1), None))
    assert checked[fact.fact_id].slots["state"] == "checked"


def test_the_fact_of_an_area_that_bears_no_name_but_its_label_says_nothing_of_a_draft():
    fact = by_id(facts_for(bearing_a_name(), area_id(2), None))[
        fact_id(area_id(2), FactKind.AREA, "name")
    ]
    assert fact.slots == {"name": "Brackenhythe", "borough": "Ostrel Vale"}
    assert fact.names == ("Brackenhythe", "Ostrel Vale")


def test_a_name_written_by_a_source_the_release_does_not_hold_makes_no_fact():
    release = bearing_a_name()
    first, *rest = release.neighbourhoods
    assert first.named is not None
    unknown = first.replace(named=first.named.replace(source_ids=("os-names",)))
    with pytest.raises(ReleaseError):
        facts_for(dataclasses.replace(release, neighbourhoods=(unknown, *rest)), area_id(1), None)


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
    # The journey that has no time is named. The journeys as a whole are not missing.
    assert f"{area_id(3)}/missing/commute" not in three
    gap = three[f"{area_id(3)}/missing/commute.syn-p0002.pt"]
    assert gap.template is TemplateId.MISSING_JOURNEY
    assert gap.slots == {"name": "Cindermoor", "place": "Foxholt Works"}
    assert gap.names == ("Cindermoor", "Foxholt Works")
    assert render(gap).text == (
        "There is no journey time from Cindermoor to Foxholt Works in this release, "
        "so that journey was left out of the score."
    )
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
    # And it is noisier than one of the seven: 14.3%, said as 14.
    assert fact.numbers == ("15%", "71%", "7", "14%")
    assert fact.slots == {
        "label": "Share of residents exposed to 55 dB or more of transport noise",
        "value": "15%",
        # One of five, counted from the low end of the figure: 1 + (5 * 1) // 7.
        "band": "1",
        # From the side that counts as better: less noise.
        "comparative": "quieter than",
        "pct": "71",
        "standing": "quieter than 71% of the 7 areas compared in this release",
        # And from the side that counts as worse.
        "comparative_worse": "noisier than",
        "pct_worse": "14",
        "standing_worse": "noisier than 14% of the 7 areas compared in this release",
        "compared": "7",
    }
    assert fact.names == ()
    assert fact.template is TemplateId.FEATURE
    # A reason is said from the better side and a trade-off from the worse.
    assert render(fact).text == render(fact, SentenceRole.REASON).text
    assert render(fact, SentenceRole.REASON).text.endswith(
        "15%, quieter than 71% of the 7 areas compared in this release."
    )
    assert render(fact, SentenceRole.TRADE_OFF).text.endswith(
        "15%, noisier than 14% of the 7 areas compared in this release."
    )
    for role in SentenceRole:
        assert verify(render(fact, role), {fact.fact_id: fact}).ok


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


SEVEN = "of the 7 areas compared in this release"
STANDING = [
    # The figure of each of the eight areas, the eighth of which is not rankable.
    # Then the area, and what is said of it from the better side and from the
    # worse. More water counts as better.
    (
        (0, 0, 0, 0, 5, 9, 12),
        1,
        # No area has less, so what is said is how many have the same.
        "the same as 3 of the 6 other areas compared in this release",
        f"less than 42% {SEVEN}, and the same as 3 others",
    ),
    ((0, 0, 0, 0, 5, 9, 12), 5, f"more than 57% {SEVEN}", f"less than 28% {SEVEN}"),
    (
        (0, 0, 0, 0, 5, 9, 12),
        7,
        f"more than 85% {SEVEN}",
        # No area has more, and none has the same.
        "less than none of the 6 other areas compared in this release",
    ),
    (
        (1, 1, 2, 2, 3, 3, 4),
        3,
        f"more than 28% {SEVEN}, and the same as 1 other",
        f"less than 42% {SEVEN}, and the same as 1 other",
    ),
    (
        (3, 3, 3, 3, 3, 3, 3),
        4,
        "the same as all 6 other areas compared in this release",
        "the same as all 6 other areas compared in this release",
    ),
    (
        (3, 3, None, None, None, None, None),
        1,
        "the same as the only other area compared in this release",
        "the same as the only other area compared in this release",
    ),
    (
        (3, None, None, None, None, None, None),
        1,
        "with no other area in this release to compare it with",
        "with no other area in this release to compare it with",
    ),
    # An area that is not rankable is placed against the seven and is not one of them.
    (
        (0, 0, 0, 0, 5, 9, 12, 0),
        8,
        "the same as 4 of the 7 other areas compared in this release",
        f"less than 42% {SEVEN}, and the same as 4 others",
    ),
    (
        (0, 0, 0, 0, 5, 9, 12, 20),
        8,
        f"more than 100% {SEVEN}",
        "less than none of the 7 other areas compared in this release",
    ),
    (
        (3, 3, 3, 3, 3, 3, 3, 3),
        8,
        "the same as all 7 other areas compared in this release",
        "the same as all 7 other areas compared in this release",
    ),
]


@pytest.mark.parametrize(("values", "number", "better", "worse"), STANDING)
def test_a_comparison_counts_only_the_areas_strictly_beyond_and_says_how_many_are_level(
    values: tuple[float | None, ...], number: int, better: str, worse: str
):
    fact = water(with_values(FeatureId.WATER_ACCESS, *values), number)
    assert fact.slots["standing"] == better
    assert fact.slots["standing_worse"] == worse
    start = f"{FEATURES[FeatureId.WATER_ACCESS].label}: {fact.slots['value']}, "
    assert render(fact).text == f"{start}{better}."
    assert render(fact, SentenceRole.TRADE_OFF).text == f"{start}{worse}."
    for role in SentenceRole:
        assert verify(render(fact, role), {fact.fact_id: fact}).ok


def test_a_share_is_rounded_down_and_never_to_the_nearest():
    # Two of three areas are beyond: 66.67%. "More than 67%" would be untrue.
    fact = water(with_values(FeatureId.WATER_ACCESS, 1, 2, 3), 3)
    assert fact.slots["pct"] == "66"
    top = standing(3.0, [1.0, 2.0, 3.0], among=True)
    assert (top.share(top.below), top.share(top.above)) == (66, 0)
    # Under one area in a hundred is beyond this one. "More than 0%" says
    # nothing, so what is said is how many are level with it.
    most = standing(5.0, [1.0, *[5.0] * 199], among=True)
    assert (most.share(most.below), most.below, most.level, most.others) == (0, 1, 198, 199)
    slots, numbers = said(most, "more than", "less than", Direction.MORE)
    assert slots["standing"] == "the same as 198 of the 199 other areas compared in this release"
    # One is below it, so "less than none" would be untrue of it from the other side.
    assert slots["standing_worse"] == slots["standing"]
    assert numbers == ("198", "199")


def test_a_figure_is_said_from_the_side_that_counts_as_better_for_the_thing():
    release = small_release()
    seen: set[Polarity] = set()
    for area in release.neighbourhoods:
        for fact in facts_for(release, area.area_id, None):
            if fact.kind is not FactKind.FEATURE:
                continue
            feature = FEATURES[FeatureId(fact.key)]
            seen.add(feature.polarity)
            # With no spec the side is the polarity's, and more where a person may choose.
            more = default_direction(feature.feature_id) is Direction.MORE
            better, worse = (
                (feature.higher, feature.lower) if more else (feature.lower, feature.higher)
            )
            assert fact.slots.get("comparative", f"{better} than") == f"{better} than"
            assert fact.slots.get("comparative_worse", f"{worse} than") == f"{worse} than"
            # Each side counts the areas strictly beyond it, so the two never add to more
            # than all of them.
            shares = int(fact.slots.get("pct", 0)) + int(fact.slots.get("pct_worse", 0))
            assert shares <= 100
    assert seen == set(Polarity)


def test_where_a_person_may_choose_the_direction_the_spec_decides_the_better_side():
    release = small_release()
    spec = default_spec(Tenure.RENT)
    fewer = spec.replace(
        weights=(
            *spec.weights,
            *(
                w.replace(feature_id=FeatureId.VENUE_EVENING_PER_HOMES, direction=Direction.LESS)
                for w in spec.weights[:1]
            ),
        )
    )
    key = f"{area_id(2)}/feature/venue_evening_per_homes"
    asked = by_id(facts_for(release, area_id(2), fewer))[key]
    unasked = by_id(facts_for(release, area_id(2), spec))[key]
    profile = by_id(facts_for(release, area_id(2), None))[key]
    # For a person who wants fewer pubs, fewer is the better side.
    assert asked.slots["standing"] == unasked.slots["standing_worse"]
    assert asked.slots["standing_worse"] == unasked.slots["standing"]
    assert unasked.slots == profile.slots
    # A direction the spec holds for a thing with one direction changes nothing.
    park = f"{area_id(2)}/feature/park_proximity"
    assert by_id(facts_for(release, area_id(2), spec))[park].slots["comparative"] == "closer than"


def test_the_band_of_a_figure_is_counted_from_the_low_end_whichever_way_is_better():
    release = with_values(FeatureId.PARK_PROXIMITY, 100, 200, 300, 400, 500, 600, 700, 50)
    bands = [
        by_id(facts_for(release, area_id(n), None))[f"{area_id(n)}/feature/park_proximity"].slots[
            "band"
        ]
        for n in range(1, 9)
    ]
    assert bands == ["1", "1", "2", "3", "3", "4", "5", "1"]


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
    # The two times, the limit the person set, and how far the journey is inside it.
    assert (by_train.template, by_train.numbers) == (TemplateId.TRAVEL_PT, ("15", "20", "40", "25"))
    assert by_train.names == ("Pellam Cross",)
    by_bike = one[f"{area_id(1)}/travel/syn-p0003.cycle"]
    assert (by_bike.template, by_bike.numbers) == (
        TemplateId.TRAVEL_OTHER_OVER,
        ("51", "40", "11"),
    )
    assert by_bike.slots == {
        "mode": "By bike",
        "place": "Wexmoor University",
        "minutes": "51",
        "limit": "40",
        "margin": "11",
        "margin_unit": "minutes",
    }
    assert render(by_bike).text == (
        "By bike to Wexmoor University: about 51 minutes, 11 minutes over the 40 you set."
    )

    # Area 4 has no journey to place 3 within the cutoff. All that is known is the cutoff.
    beyond = by_id(facts_for(release, area_id(4), spec))[f"{area_id(4)}/travel/syn-p0003.cycle"]
    assert (beyond.template, beyond.numbers) == (TemplateId.TRAVEL_BEYOND, ("40", "60"))
    assert (beyond.slots["cutoff"], beyond.slots["limit"]) == ("60", "40")
    assert "margin" not in beyond.slots


def test_a_journey_over_the_limit_a_person_set_says_by_how_much():
    release = build_worked_release()
    spec = build_worked_spec()
    # Cindermoor is 44 minutes from place 1, against a limit of 40.
    over = by_id(facts_for(release, area_id(3), spec))[f"{area_id(3)}/travel/syn-p0001.pt"]
    assert over.template is TemplateId.TRAVEL_PT_OVER
    assert (over.slots["limit"], over.slots["margin"]) == ("40", "4")
    assert render(over).text == (
        "By public transport to Pellam Cross: about 44 minutes on a typical weekday morning, "
        "49 if you just miss a service, 4 minutes over the 40 you set."
    )
    # At the limit itself it is not over, and one minute over is one minute.
    at = spec.replace(commutes=(commute(1, minutes=44), commute(2, minutes=21)))
    facts = by_id(facts_for(release, area_id(3), at))
    assert facts[f"{area_id(3)}/travel/syn-p0001.pt"].template is TemplateId.TRAVEL_PT
    by_one = facts[f"{area_id(3)}/travel/syn-p0002.pt"]
    assert render(by_one).text.endswith("1 minute over the 21 you set.")
    # Scored on the time of someone who just missed a service, it is that time that is over.
    missed = spec.replace(
        pt_basis=PtBasis.JUST_MISSED, commutes=(commute(1, minutes=45), commute(2))
    )
    late = by_id(facts_for(release, area_id(3), missed))[f"{area_id(3)}/travel/syn-p0001.pt"]
    assert (late.template, late.slots["margin"]) == (TemplateId.TRAVEL_PT_OVER, "4")
    for fact in (over, by_one, late):
        assert verify(render(fact), {fact.fact_id: fact}).ok


def test_a_journey_with_only_one_public_transport_time_states_that_one():
    release = build_worked_release()
    table = release.travel_table
    one_time = dataclasses.replace(
        release,
        travel_table=table.replace(pt_just_missed=tuple((None, None) for _ in range(4))),
    )
    fact = by_id(facts_for(one_time, area_id(1), build_worked_spec()))
    journey = fact[f"{area_id(1)}/travel/syn-p0001.pt"]
    assert (journey.template, journey.numbers) == (TemplateId.TRAVEL_OTHER, ("32", "40", "8"))
    assert journey.slots["mode"] == "By public transport"

    # Scored on the time that is not there, the journey is missing, not guessed from the other.
    missed = build_worked_spec().replace(pt_basis=PtBasis.JUST_MISSED)
    facts = by_id(facts_for(one_time, area_id(1), missed))
    assert f"{area_id(1)}/travel/syn-p0001.pt" not in facts
    assert f"{area_id(1)}/missing/commute.syn-p0001.pt" in facts


def test_a_station_fact_names_the_station_and_its_lines():
    facts = by_id(facts_for(small_release(), area_id(2), None))
    nearest = facts[f"{area_id(2)}/station/syn-s0002"]
    assert nearest.template is TemplateId.STATION
    assert nearest.names == ("Tinderside Halt", "Birch line")
    assert nearest.numbers == ("5",)
    nearby = facts[f"{area_id(2)}/station/syn-s0003"]
    assert nearby.template is TemplateId.STATION_NEARBY


def test_a_vibe_cites_the_sources_of_its_parts_that_had_a_figure_and_is_dated_by_them():
    release = build_worked_release()
    real = release.manifest.sources[0].replace(
        source_id="green-source", name="Green space", attribution="Source: green space."
    )
    noise = real.replace(source_id="noise-source", name="Noise")
    dated = {FeatureId.GREEN_COVER: "2021", FeatureId.NOISE_EXPOSURE: "2019"}
    cited = dataclasses.replace(
        release,
        manifest=release.manifest.replace(sources=(*release.manifest.sources, real, noise)),
        metrics=tuple(
            m.replace(
                source_ids=("green-source",)
                if m.feature_id is FeatureId.GREEN_COVER
                else ("noise-source",),
                vintage=dated.get(m.feature_id, m.vintage),
            )
            for m in release.metrics
        ),
    )
    leafy = by_id(facts_for(cited, area_id(1), None))[f"{area_id(1)}/tag/leafy"]
    # Leafy is made of gardens, woodland and green cover. Only green cover has a
    # figure here, and noise is no part of the recipe.
    assert [s.source_id for s in leafy.sources] == ["green-source"]
    # The date is that of the part, and never the day the release was built.
    assert leafy.as_of == "2021" != cited.manifest.built_at[:10]
    assert (leafy.slots["known"], leafy.slots["parts"]) == ("1", "3")


def test_a_vibe_is_said_as_a_band_among_the_areas_compared_and_never_as_a_percentage():
    release = small_release()
    seen: set[TemplateId] = set()
    for area in release.neighbourhoods:
        facts = by_id(facts_for(release, area.area_id, None))
        for vibe in release.vibes:
            fact = facts[f"{area.area_id}/tag/{vibe.tag_id}"]
            row = release.tag(area.area_id, vibe.tag_id)
            assert row is not None
            seen.add(fact.template)
            text = render(fact).text
            assert "%" not in text and not [n for n in fact.numbers if "%" in n]
            assert verify(render(fact), {fact.fact_id: fact}).ok, text
            # The score an area is ranked on is never among what may be printed.
            assert row.score is None or str(row.score) not in fact.numbers
            if row.band is None:
                assert fact.template is TemplateId.VIBE_UNKNOWN
                continue
            assert fact.template is TemplateId.VIBE
            assert fact.slots["band"] == str(row.band)
            assert fact.slots["judgement"] == JUDGEMENT
            assert fact.slots["made_from"] == MADE_FROM
            assert text.endswith(f"Parts dated 2025. {JUDGEMENT}")
    assert seen == {TemplateId.VIBE, TemplateId.VIBE_UNKNOWN}


def test_a_band_that_rests_on_part_of_a_recipe_says_how_much_of_it():
    # The release of the tests carries no private outdoor space, so Homes rests on two
    # of its three parts, which are 75 of its 100. It was said as any other band.
    release = small_release()
    facts = by_id(facts_for(release, area_id(1), None))
    homes, pace = facts[f"{area_id(1)}/tag/homes"], facts[f"{area_id(1)}/tag/pace"]
    row = release.tag(area_id(1), TagId.HOMES)
    assert row is not None and (row.coverage, row.band is not None) == (0.75, True)
    assert (homes.slots["known"], homes.slots["parts"], homes.slots["share"]) == ("2", "3", "75")
    assert homes.slots["partly"] == "Worked out from 2 of its 3 parts, 75 of 100 by weight."
    assert render(homes).text == (
        f"Houses or flats: band {row.band} of 5, counted from Houses to Flats, among the 7 "
        "areas compared in this release. Worked out from 2 of its 3 parts, 75 of 100 by weight. "
        "Parts dated 2025. The recipe is Burro's own. The weights are a judgement."
    )
    assert verify(render(homes), {homes.fact_id: homes}).ok
    assert {"2", "3", "75", "100"} <= set(homes.numbers)
    # A band that rests on the whole of its recipe says no more than it did.
    assert (pace.slots["share"], pace.slots["partly"]) == ("100", "")
    assert "Worked out" not in render(pace).text and "  " not in render(pace).text
    # And every vibe of every area says it exactly where its recipe ran short.
    for area in release.neighbourhoods:
        for fact in facts_for(release, area.area_id, None):
            found = release.tag(area.area_id, TagId(fact.key)) if fact.kind == "tag" else None
            if found is None or found.band is None:
                continue
            assert ("Worked out from" in render(fact).text) is (found.coverage < 1), fact.fact_id
            assert int(fact.slots["share"]) == round(100 * found.coverage)
            assert verify(render(fact), {fact.fact_id: fact}).ok


def test_a_range_that_rests_on_part_of_a_recipe_says_so_too():
    release = mixed(small_release(), TagId.HOMES)
    row = next(r for r in release.tags if r.tag_id is TagId.HOMES and r.spread_low != r.spread_high)
    fact = by_id(facts_for(release, row.area_id, None))[f"{row.area_id}/tag/homes"]
    assert fact.template is TemplateId.VIBE_RANGE
    assert render(fact).text == (
        f"Houses or flats: varies within this area, from band {row.spread_low} to band "
        f"{row.spread_high} of 5, counted from Houses to Flats. Worked out from 2 of its 3 "
        "parts, 75 of 100 by weight. Parts dated 2025. "
        "The recipe is Burro's own. The weights are a judgement."
    )
    assert verify(render(fact), {fact.fact_id: fact}).ok


def test_a_scale_is_counted_from_one_named_end_to_the_other_and_a_one_way_vibe_from_least():
    facts = by_id(facts_for(small_release(), area_id(1), None))
    pace, leafy = facts[f"{area_id(1)}/tag/pace"], facts[f"{area_id(1)}/tag/leafy"]
    assert (pace.slots["low_end"], pace.slots["high_end"]) == ("Calm", "Buzzy")
    assert render(pace).text == (
        "Going out: band 3 of 5, counted from Calm to Buzzy, among the 7 areas compared in this "
        "release. Parts dated 2025. The recipe is Burro's own. The weights are a judgement."
    )
    assert (leafy.slots["low_end"], leafy.slots["high_end"]) == ("least", "most")
    assert render(leafy).text.startswith("Leafy: band 1 of 5, counted from least to most, among")
    # The sentence is the same in every role: a band has no better side.
    for role in SentenceRole:
        assert render(pace, role).text == render(pace).text


def test_gritty_as_a_scale_names_its_ends_only_from_the_slots_of_its_own_fact():
    facts = by_id(facts_for(small_release(GrittyVariant.B), area_id(1), None))
    fact = facts[f"{area_id(1)}/tag/street_character"]
    assert (fact.slots["low_end"], fact.slots["high_end"]) == ("Polished", "Gritty")
    sentence = render(fact)
    assert "counted from Polished to Gritty" in sentence.text
    assert verify(sentence, {fact.fact_id: fact}).ok
    # Cited of any other fact, the same words are a verdict and are refused.
    other = facts[f"{area_id(1)}/tag/pace"]
    planted = sentence.replace(fact_ids=(other.fact_id,))
    assert not verify(planted, {other.fact_id: other}).ok
    # The release that carries gritty as land use alone has no such fact.
    plain_facts = by_id(facts_for(small_release(GrittyVariant.A), area_id(1), None))
    assert f"{area_id(1)}/tag/street_character" not in plain_facts
    works = plain_facts[f"{area_id(1)}/tag/works_warehouses"]
    assert "Gritty" not in render(works).text


def test_a_mixed_area_is_said_as_a_range_and_never_as_a_point_in_the_middle():
    release = mixed(small_release())
    row = next(r for r in release.tags if r.tag_id is TagId.PACE and r.spread_low != r.spread_high)
    fact = by_id(facts_for(release, row.area_id, None))[f"{row.area_id}/tag/pace"]
    assert fact.template is TemplateId.VIBE_RANGE
    assert render(fact).text == (
        f"Going out: varies within this area, from band {row.spread_low} to band "
        f"{row.spread_high} of 5, counted from Calm to Buzzy. Parts dated 2025. "
        "The recipe is Burro's own. The weights are a judgement."
    )
    assert verify(render(fact), {fact.fact_id: fact}).ok
    # Two bands are not a range: the mark is drawn where the band is.
    narrow = dataclasses.replace(
        release,
        tags=tuple(
            r.replace(spread_low=r.band, spread_high=min(r.band + 1, 5))
            if r is row and r.band is not None
            else r
            for r in release.tags
        ),
    )
    assert by_id(facts_for(narrow, row.area_id, None))[fact.fact_id].template is TemplateId.VIBE


def test_an_area_that_cannot_be_placed_on_a_vibe_is_said_to_be_that_with_no_figure_of_it():
    gap = (None, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 3.0)
    parts = {term.feature_id: gap for term in TAGS[TagId.LEAFY].terms}
    release = with_figures(small_release(), parts)
    fact = by_id(facts_for(release, area_id(1), None))[f"{area_id(1)}/tag/leafy"]
    assert fact.template is TemplateId.VIBE_UNKNOWN
    assert render(fact).text == (
        "Burro cannot place Alderwick on Leafy. Parts with a figure in this release: 0 of 3."
    )
    assert fact.numbers == ("0", "3")
    assert "band" not in fact.slots
    assert verify(render(fact), {fact.fact_id: fact}).ok
    # With one part of three known, the sources are that part's.
    some = with_figures(release, {FeatureId.GREEN_COVER: (9.0, *gap[1:])})
    known = by_id(facts_for(some, area_id(1), None))[f"{area_id(1)}/tag/leafy"]
    assert known.slots["known"] == "1" and known.as_of == "2025"


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


def test_a_preview_makes_a_fact_of_its_areas_and_its_measures_and_of_nothing_else():
    release = preview_release()
    facts = every_fact(release, None)
    # A likeness is counted from its measures. No cost, journey or station is said.
    assert {fact.kind for fact in facts} == {
        FactKind.AREA,
        FactKind.FEATURE,
        FactKind.TAG,
        FactKind.LIKENESS,
    }
    assert all(fact.sources and fact.as_of for fact in facts)
    # What a person asks for and the preview holds for no area is refused, and no fact is
    # made of it: a budget, where it holds no cost.
    wished = default_spec(Tenure.RENT)
    with pytest.raises(SpecError):
        facts_for(release, area_id(1), wished.replace(budget=wished.budget.replace(amount=1500)))
    # What it holds for some areas and not for this one is said to be missing, with no figure.
    lacking = next(
        row for row in release.features if row.value is None and row.area_id == area_id(1)
    )
    asked = wished.replace(
        weights=(
            FeatureWeight(
                feature_id=lacking.feature_id,
                weight=0.5,
                direction=default_direction(lacking.feature_id),
                provenance=Provenance.STATED,
            ),
        )
    )
    missing = [f for f in facts_for(release, area_id(1), asked) if f.kind is FactKind.MISSING]
    assert [(fact.key, fact.numbers) for fact in missing] == [(f"feature:{lacking.feature_id}", ())]


def test_no_fact_is_made_from_a_part_that_states_no_source():
    """A station with no source to cite cannot be said. Only a release built by hand holds one."""
    release = small_release()
    unstated = dataclasses.replace(release, stations_origin=Origin(source_ids=(), as_of=None))
    with pytest.raises(ReleaseError) as caught:
        facts_for(unstated, area_id(1), None)
    assert caught.value.rule == "sources_are_stated"


def test_facts_refuse_a_spec_the_release_cannot_rank():
    spec = default_spec(Tenure.RENT).replace(commutes=(commute(9),))
    with pytest.raises(SpecError):
        facts_for(small_release(), area_id(1), spec)


def test_a_distance_of_a_thousand_metres_or_more_is_printed_with_its_separator():
    # "1080 m" was printed beside "£1,750": every other large number had one.
    release = with_figures(
        small_release(), {FeatureId.PARK_PROXIMITY: (1084.0, 996.0, 12_345.0, 40.0, 281.0)}
    )
    printed = [
        by_id(facts_for(release, area_id(n), None))[f"{area_id(n)}/feature/park_proximity"]
        for n in range(1, 6)
    ]
    assert [fact.slots["value"] for fact in printed] == [
        "1,080 m",
        "1,000 m",
        "12,340 m",
        "40 m",
        "280 m",
    ]
    # The number the verifier holds has no separator, as it holds every number.
    assert [fact.numbers[0] for fact in printed] == ["1080", "1000", "12340", "40", "280"]
    for fact in printed:
        assert verify(render(fact), {fact.fact_id: fact}).ok, render(fact).text
        assert verify(render(fact, SentenceRole.TRADE_OFF), {fact.fact_id: fact}).ok


def test_a_flow_of_traffic_is_printed_whole_and_with_its_separator():
    # A flow runs to tens of thousands of motor vehicles a day, and is given to the whole
    # vehicle: "16915.5 motor vehicles a day" would be read as a figure of two kinds.
    release = with_figures(
        small_release(),
        {FeatureId.ROAD_TRAFFIC_NEARBY: (16_915.0, 478.0, 101_407.0, 0.0, 9_999.5)},
    )
    printed = [
        by_id(facts_for(release, area_id(n), None))[f"{area_id(n)}/feature/road_traffic_nearby"]
        for n in range(1, 6)
    ]
    assert [fact.slots["value"] for fact in printed] == [
        "16,915 motor vehicles a day",
        "478 motor vehicles a day",
        "101,407 motor vehicles a day",
        "0 motor vehicles a day",
        "10,000 motor vehicles a day",
    ]
    # The number the verifier holds has no separator, as it holds every number.
    assert [fact.numbers[0] for fact in printed] == ["16915", "478", "101407", "0", "10000"]
    for fact in printed:
        assert verify(render(fact), {fact.fact_id: fact}).ok, render(fact).text
        assert verify(render(fact, SentenceRole.TRADE_OFF), {fact.fact_id: fact}).ok
    # It is said from the side of less, which is the side that counts as better.
    assert render(printed[1]).text.startswith(
        "Traffic past the busiest count point within 500 m of home, in a straight line: "
        "478 motor vehicles a day, less than "
    )
