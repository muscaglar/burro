"""A visit: a search for somewhere to stay, which is a kind of search of its own.

A person who is choosing where to book a hotel names no budget, no number of
bedrooms and no kind of home, and Burro holds no price of a stay. So a visit
holds none of them. An edit that would give it one is turned away and says
why. What homes cost is no part of how its areas are ranked, no explanation
speaks of it, and a release is asked for no cost to serve one. Everything else
that a person asks for is kept when a search becomes a visit, and a search
that stops being one takes the usual budget of its new kind.

Every name and figure here is made up.
"""

import dataclasses
from typing import Any

import pytest
from burro_core.catalogue import (
    COUNTS_RESIDENTS,
    FEATURES,
    NUISANCES,
    RANKED_AS,
    default_direction,
)
from burro_core.explain import Explanation, TemplateExplainer, explain
from burro_core.facts import facts_for
from burro_core.ids import (
    Dimension,
    FactKind,
    FeatureId,
    FilterReason,
    Provenance,
    RejectReason,
    Segment,
    SegmentChoice,
    Strictness,
    TagId,
    Tenure,
    TenureChoice,
    segments_for,
)
from burro_core.rank import asked_for, rank
from burro_core.reducer import ReducerResult, apply
from burro_core.release import CostEstimate, InMemoryRelease, ReleaseError, parse_release
from burro_core.spec import (
    DEFAULT_BUDGET_WEIGHT,
    DEFAULT_COMMUTE_WEIGHT,
    DEFAULT_SEGMENT,
    DEFAULT_WEIGHTS,
    LIMITS,
    MENTION_WEIGHT,
    NO_BUDGET,
    PreferenceSpec,
    canonical,
    check_spec,
    default_budget,
    default_spec,
    given_way,
    spec_hash,
)
from pydantic import ValidationError

from .support import (
    cost,
    documents,
    draws,
    fixture_release,
    preview_release,
    random_spec,
    small_release,
)
from .test_reducer import (
    Edit,
    area,
    budget,
    commute,
    ops,
    reasons,
    run,
    setting,
    tag,
    weight,
    weights,
)

VISITOR = default_spec(Tenure.VISIT)
RENTER = default_spec(Tenure.RENT)
# What a visitor is taken to mind until they say, as the contract lists it in section 4.1.
USUAL = {
    "station_walk": 0.50,
    "station_lines": 0.30,
    "venue_food_drink_per_homes": 0.30,
    "venue_evening_per_homes": 0.30,
    "culture_venues_per_homes": 0.30,
    "park_proximity": 0.30,
}
# No sentence of a visit holds one of these. Each stands in a sentence of what a home costs
# or of a budget, and in no sentence of a measure, a vibe or a journey.
OF_COST = (
    "your budget",
    "this kind of home",
    "rents for",
    "sells for",
    "middle rent",
    "of all sizes",
)


def searching(spec: PreferenceSpec = RENTER) -> PreferenceSpec:
    """A search in which a person has asked for a good deal, of every kind there is."""
    found = run(
        spec,
        budget(amount=1500, segment="bed_2", strictness="hard"),
        setting("set", "budget_weight", value=0.6, provenance="ui_edit"),
        commute("add", 1, max_minutes=35, strictness="hard"),
        commute("add", 2, mode="cycle"),
        weight("set", "water_access", value=0.7, provenance="ui_edit"),
        weight("remove", "station_lines", provenance="ui_edit"),
        tag("nudge", "leafy", step="up_large"),
        tag("set", "pace", value=0.4, toward="low", provenance="ui_edit"),
        area("exclude", 3),
        setting("set", "pt_basis", choice="just_missed", provenance="ui_edit"),
        setting("set", "commute_weight", value=0.8, provenance="ui_edit"),
    )
    assert found.rejected == ()
    return found.spec


# A kind of search of its own


def test_a_visit_is_the_third_kind_of_search():
    assert [tenure.value for tenure in Tenure] == ["rent", "buy", "visit"]
    assert [choice.value for choice in TenureChoice] == ["rent", "buy", "visit", "unchanged"]
    # Nothing is named for a home or for money that is a visit's.
    assert segments_for(Tenure.VISIT) == ()
    assert LIMITS.money(Tenure.VISIT) is None
    assert Tenure.VISIT not in DEFAULT_SEGMENT
    assert {"rent", "buy"} == {name for name in type(LIMITS).model_fields if name in Tenure}


def test_a_visit_holds_no_budget_and_no_kind_of_home():
    assert VISITOR.visiting and not RENTER.visiting
    assert VISITOR.budget == NO_BUDGET == default_budget(Tenure.VISIT)
    assert (NO_BUDGET.amount, NO_BUDGET.weight) == (None, 0.0)
    assert (NO_BUDGET.strictness, NO_BUDGET.provenance) == (Strictness.SOFT, Provenance.DEFAULT)
    assert not VISITOR.budget_requested
    # The usual budget of a home is as it was.
    for tenure in (Tenure.RENT, Tenure.BUY):
        usual = default_budget(tenure)
        assert usual == default_spec(tenure).budget
        assert (usual.amount, usual.segment) == (None, DEFAULT_SEGMENT[tenure])
        assert (usual.weight, usual.strictness) == (DEFAULT_BUDGET_WEIGHT, Strictness.SOFT)


@pytest.mark.parametrize(
    "given",
    [
        {"amount": 150},
        {"amount": 1500},
        {"amount": 450_000},
        {"weight": 0.3},
        {"weight": 0.05},
        {"strictness": Strictness.HARD},
        {"provenance": Provenance.STATED},
        *({"segment": segment} for segment in Segment if segment is not NO_BUDGET.segment),
    ],
    ids=lambda given: "-".join(f"{name}-{value}" for name, value in given.items()),
)
def test_no_visit_can_be_made_that_holds_a_budget_or_a_home(given: dict[str, Any]):
    held = NO_BUDGET.replace(**given)
    with pytest.raises(ValidationError) as refused:
        VISITOR.replace(budget=held)
    # What was sent may be what a person typed, so the refusal shows none of it.
    assert not any(str(value) in str(refused.value) for value in given.values())
    with pytest.raises(ValidationError):
        searching().replace(tenure=Tenure.VISIT)
    with pytest.raises(ValidationError):
        PreferenceSpec.model_validate(
            VISITOR.model_dump(mode="json") | {"budget": held.model_dump(mode="json")}
        )
    # The same budget is one a search for a home may hold.
    assert RENTER.replace(budget=held).budget == held


def test_the_hash_of_a_visit_says_that_it_is_one_and_holds_no_budget():
    written = canonical(VISITOR)
    assert '"tenure":"visit"' in written and '"budget":null' in written
    assert NO_BUDGET.segment.value not in written
    same_wishes = RENTER.replace(weights=VISITOR.weights)
    assert canonical(same_wishes).replace('"rent"', '"visit"') == written
    assert spec_hash(same_wishes) != spec_hash(VISITOR)
    # A search for a home is written, and hashed, as it was before there was a visit.
    nothing_set = RENTER.replace(weights=())
    assert canonical(nothing_set) == (
        '{"areas":[],"budget":null,"commutes":[],"schema_version":1,"tags":[],'
        '"tenure":"rent","weights":[]}'
    )
    assert spec_hash(nothing_set) == (
        "879be1ff788f9463f2dc60271c9190fdd35ea3df7522cce631dbde9ce8089a6b"
    )


# What a visitor is taken to mind


def test_a_visit_starts_from_what_a_visitor_is_likely_to_mind():
    assert weights(VISITOR) == USUAL
    assert {w.provenance for w in VISITOR.weights} == {Provenance.DEFAULT}
    assert DEFAULT_WEIGHTS[Tenure.VISIT] == {FeatureId(name): at for name, at in USUAL.items()}
    assert (VISITOR.commutes, VISITOR.tags, VISITOR.areas) == ((), (), ())
    assert VISITOR.commute_weight == DEFAULT_COMMUTE_WEIGHT
    assert VISITOR.tenure_from is Provenance.DEFAULT
    # Nobody asked for any of it, so none of it puts an area below another for want of a figure.
    assert asked_for(VISITOR) == frozenset()


def test_the_usual_settings_of_a_visit_keep_every_rule_a_usual_setting_keeps():
    for held in VISITOR.weights:
        feature = FEATURES[held.feature_id]
        assert held.direction is default_direction(held.feature_id)
        # A count is shown and never ranked on, so none is weighed: what is, is for each
        # 1,000 homes.
        assert held.feature_id not in RANKED_AS
        # Nothing of who lives somewhere, no recorded crime, no price and no nuisance.
        assert held.feature_id not in COUNTS_RESIDENTS
        assert held.feature_id not in NUISANCES
        assert feature.dimension not in (Dimension.CRIME, Dimension.BRANDS)
    assert {FeatureId.PRICE_MEDIAN, FeatureId.NOISE_EXPOSURE, FeatureId.AIR_NO2}.isdisjoint(
        DEFAULT_WEIGHTS[Tenure.VISIT]
    )
    # Every one is a measure the committed release ranks on, so none is left out as served.
    ranked = {metric.feature_id for metric in fixture_release().metrics if metric.rankable}
    assert set(DEFAULT_WEIGHTS[Tenure.VISIT]) <= ranked


def test_what_a_visitor_says_outweighs_the_usual_settings():
    given = {name: given_way(at) for name, at in USUAL.items()}
    assert sum(given.values()) == pytest.approx(0.35)
    # One thing said of the place outweighs all that was left unsaid, as for a home.
    assert sum(given.values()) < MENTION_WEIGHT
    # A visit has no budget to stand beside a journey. One place to reach outweighs them.
    assert sum(given.values()) < DEFAULT_COMMUTE_WEIGHT
    said = run(VISITOR, commute("add", 1, max_minutes=30)).spec
    assert weights(said) == given
    assert said.commute_weight > sum(weights(said).values())


# Becoming a visit, and ceasing to be one


@pytest.mark.parametrize("provenance", ["stated", "inferred", "ui_edit"])
def test_a_search_that_becomes_a_visit_drops_the_budget_and_the_home_and_keeps_the_rest(
    provenance: str,
):
    before = searching()
    assert (before.budget.amount, before.budget.segment) == (1500, Segment.BED_2)
    moved = run(before, budget(tenure="visit", provenance=provenance))
    assert moved.rejected == () and [a.changed for a in moved.applied] == [True]
    after = moved.spec
    assert (after.tenure, after.tenure_from) == (Tenure.VISIT, Provenance(provenance))
    assert after.budget == NO_BUDGET
    # Where they need to get to, what they want around them, and the areas they ruled out.
    assert after.commutes == before.commutes
    assert after.tags == before.tags
    assert after.areas == before.areas
    assert (after.commute_combine, after.pt_basis) == (before.commute_combine, before.pt_basis)
    assert (after.commute_weight, after.commute_weight_from) == (0.8, Provenance.UI_EDIT)
    chosen = {w.feature_id: w for w in before.weights if w.provenance is not Provenance.DEFAULT}
    assert {w.feature_id: w for w in after.weights if w.feature_id in chosen} == chosen
    # What nobody chose is now a visitor's, given way, and what was taken off stays off.
    usual = {name: given_way(at) for name, at in USUAL.items() if name != "station_lines"}
    assert {
        w.feature_id.value: w.weight for w in after.weights if w.provenance is Provenance.DEFAULT
    } == usual
    assert weights(after)["station_lines"] == 0.0
    assert check_spec(after, small_release()) == ()


@pytest.mark.parametrize("tenure", [Tenure.RENT, Tenure.BUY])
def test_a_visit_that_becomes_a_search_for_a_home_takes_the_usual_budget_of_that_kind(
    tenure: Tenure,
):
    visiting = run(searching(), budget(tenure="visit")).spec
    back = run(visiting, budget(tenure=tenure.value, provenance="ui_edit"))
    assert back.rejected == ()
    found = back.spec.budget
    # Not the budget that was dropped: a rent is not a price, and nobody said it again.
    assert (found.amount, found.segment) == (None, DEFAULT_SEGMENT[tenure])
    assert (found.strictness, found.weight) == (Strictness.SOFT, DEFAULT_BUDGET_WEIGHT)
    assert (back.spec.tenure, back.spec.tenure_from) == (tenure, Provenance.UI_EDIT)
    assert back.spec.commutes == visiting.commutes and back.spec.tags == visiting.tags
    # A budget that is given with the change is taken, as it is between renting and buying.
    amount = 1700 if tenure is Tenure.RENT else 400_000
    given = run(visiting, budget(tenure=tenure.value, amount=amount, strictness="hard")).spec
    assert (given.budget.amount, given.budget.strictness) == (amount, Strictness.HARD)
    assert given.budget.segment is DEFAULT_SEGMENT[tenure]


def test_to_say_visiting_on_a_visit_is_to_choose_it():
    said = run(VISITOR, budget(tenure="visit"))
    assert [a.changed for a in said.applied] == [True] and said.rejected == ()
    assert said.spec == VISITOR.replace(tenure_from=Provenance.STATED)
    # Who chose it is no wish: the usual settings stay whole, and the hash where it was.
    assert weights(said.spec) == USUAL
    assert spec_hash(said.spec) == spec_hash(VISITOR)


# An edit that would give a visit a budget or a home

ON_A_VISIT: list[tuple[Edit, RejectReason]] = [
    (budget(amount=150), RejectReason.NOT_IN_RELEASE),
    (budget(amount=1500), RejectReason.NOT_IN_RELEASE),
    (budget(amount=450_000, provenance="ui_edit"), RejectReason.NOT_IN_RELEASE),
    (budget(amount=1500, strictness="hard"), RejectReason.NOT_IN_RELEASE),
    (budget(strictness="hard"), RejectReason.NOT_IN_RELEASE),
    (budget(strictness="soft", provenance="ui_edit"), RejectReason.NOT_IN_RELEASE),
    (budget(tenure="visit", amount=1500), RejectReason.NOT_IN_RELEASE),
    (budget(tenure="visit", strictness="hard"), RejectReason.NOT_IN_RELEASE),
    (budget(tenure="visit", segment="studio"), RejectReason.SEGMENT_NOT_FOR_TENURE),
    (budget(amount=1500, segment="bed_2"), RejectReason.SEGMENT_NOT_FOR_TENURE),
    (budget("nudge", step="up_small"), RejectReason.NOTHING_TO_CHANGE),
    (budget("nudge", step="down_large"), RejectReason.NOTHING_TO_CHANGE),
    (budget(), RejectReason.NOTHING_TO_CHANGE),
    (setting("set", "budget_weight", value=0.5), RejectReason.NOT_IN_RELEASE),
    (setting("set", "budget_weight", value=0.0), RejectReason.NOT_IN_RELEASE),
    (setting("nudge", "budget_weight", step="up_large"), RejectReason.NOT_IN_RELEASE),
    *(
        (budget(segment=kind.value), RejectReason.SEGMENT_NOT_FOR_TENURE)
        for kind in SegmentChoice
        if kind is not SegmentChoice.UNCHANGED
    ),
]


@pytest.mark.parametrize(
    ("edit", "reason"),
    ON_A_VISIT,
    ids=lambda found: found.value if isinstance(found, RejectReason) else type(found).__name__,
)
def test_an_edit_that_would_give_a_visit_a_budget_or_a_home_is_turned_away_and_says_why(
    edit: Edit, reason: RejectReason
):
    for visit in (VISITOR, run(searching(), budget(tenure="visit")).spec):
        turned = run(visit, edit)
        assert reasons(turned) == [reason] and turned.applied == ()
        # It is never applied in silence, and never in part: the search is as it was.
        assert turned.spec == visit
        assert turned.spec.budget == NO_BUDGET


def test_an_edit_that_is_turned_away_leaves_a_search_for_a_home_as_it_was():
    before = searching()
    turned = run(before, budget(tenure="visit", amount=1500))
    assert reasons(turned) == [RejectReason.NOT_IN_RELEASE]
    # The search did not become a visit with half of what was asked.
    assert turned.spec == before and turned.spec.tenure is Tenure.RENT


def test_what_was_set_of_a_home_before_a_visit_is_dropped_and_after_one_is_turned_away():
    first = run(RENTER, budget(amount=1500, segment="bed_2"), budget(tenure="visit"))
    assert first.rejected == () and first.spec.budget == NO_BUDGET
    assert first.spec.tenure is Tenure.VISIT
    then = run(RENTER, budget(tenure="visit"), budget(amount=1500), budget(segment="bed_2"))
    assert reasons(then) == [RejectReason.NOT_IN_RELEASE, RejectReason.SEGMENT_NOT_FOR_TENURE]
    assert [(r.group, r.index) for r in then.rejected] == [("budget_ops", 1), ("budget_ops", 2)]
    assert then.spec == first.spec.replace(tenure_from=then.spec.tenure_from)


def test_to_clear_the_budget_of_a_visit_is_in_order_and_changes_nothing():
    cleared = run(VISITOR, budget("clear"))
    assert cleared.rejected == ()
    assert ([a.changed for a in cleared.applied], cleared.spec) == ([False], VISITOR)


def test_everything_else_is_asked_of_a_visit_as_of_any_search():
    asked = run(
        VISITOR,
        commute("add", 1, max_minutes=30, strictness="hard"),
        weight("nudge", "water_access", step="up_large"),
        weight("remove", "park_proximity", provenance="ui_edit"),
        tag("nudge", "leafy", step="up_large"),
        area("only", 2),
        setting("set", "commute_weight", value=0.9, provenance="ui_edit"),
        setting("set", "commute_combine", choice="mean", provenance="ui_edit"),
    )
    assert asked.rejected == () and all(found.changed for found in asked.applied)
    assert asked.spec.tenure is Tenure.VISIT and asked.spec.budget == NO_BUDGET
    assert [c.max_minutes for c in asked.spec.commutes] == [30]
    assert [t.tag_id for t in asked.spec.tags] == [TagId.LEAFY]
    assert weights(asked.spec)["water_access"] == MENTION_WEIGHT
    assert weights(asked.spec)["park_proximity"] == 0.0
    assert check_spec(asked.spec, small_release()) == ()


# How a visit is ranked


def visits(count: int = 40) -> list[PreferenceSpec]:
    """Searches for somewhere to stay, drawn at random from what the small release carries."""
    draw = draws(75)
    found: list[PreferenceSpec] = []
    while len(found) < count:
        spec = random_spec(draw, small_release())
        if spec.visiting:
            found.append(spec)
    return found


def costing(release: InMemoryRelease, rent: int, price: int) -> InMemoryRelease:
    """The release with every rent it holds at one figure, and every price at another."""
    rows = tuple(
        cost(row.area_id, rent if row.tenure is Tenure.RENT else price, row.tenure, row.segment)
        for row in release.costs
    )
    return dataclasses.replace(release, costs=rows)


def test_what_homes_cost_is_no_part_of_how_a_visit_is_ranked():
    release = small_release()
    dear, cheap = costing(release, 19_000, 9_000_000), costing(release, 400, 150_000)
    bare = dataclasses.replace(release, costs=())
    assert release.costs and not bare.costs
    ranked = 0
    for spec in visits():
        result = rank(spec, release)
        # Whatever a home costs there, and whether the release holds a cost at all.
        assert rank(spec, dear) == rank(spec, cheap) == rank(spec, bare) == result
        assert FilterReason.OVER_BUDGET not in {found.reason for found in result.filtered}
        for found in result.ranked:
            assert found.budget is None
            assert "budget" not in {c.component for c in found.contributions}
            assert FilterReason.OVER_BUDGET not in found.untested_filters
        assert not any("budget" in found.missing for found in result.unranked)
        assert "budget" not in asked_for(spec)
        ranked += len(result.ranked)
    assert ranked > 100
    # A search for a home in the same releases is moved by what a home costs.
    renter = RENTER.replace(budget=RENTER.budget.replace(amount=1500, weight=1.0))
    assert rank(renter, dear).ranked != rank(renter, cheap).ranked


@dataclasses.dataclass(frozen=True)
class Watched(InMemoryRelease):
    """A release that writes down every cost it is asked for."""

    asked: list[tuple[str, ...]] = dataclasses.field(
        default_factory=list[tuple[str, ...]], compare=False
    )

    def cost(self, area_id: str, tenure: Tenure, segment: Segment) -> CostEstimate | None:
        self.asked.append((area_id, tenure, segment))
        return super().cost(area_id, tenure, segment)

    def costed(self, tenure: Tenure, segment: Segment) -> bool:
        self.asked.append((tenure, segment))
        return super().costed(tenure, segment)


def watched(release: InMemoryRelease) -> Watched:
    fields = dataclasses.fields(InMemoryRelease)
    return Watched(**{f.name: getattr(release, f.name) for f in fields if f.init})


def everything_a_search_is_served(spec: PreferenceSpec, release: InMemoryRelease) -> None:
    """What the routes that rank, explain and compare ask of core for one search."""
    assert check_spec(spec, release) == ()
    result = rank(spec, release)
    areas = tuple(found.area_id for found in result.ranked)
    explain(result, release, spec, areas, TemplateExplainer())
    for found in release.neighbourhoods:
        facts_for(release, found.area_id, spec)


def test_a_release_is_asked_for_no_cost_to_serve_a_visit():
    for spec in (VISITOR, run(searching(), budget(tenure="visit")).spec, *visits(10)):
        release = watched(small_release())
        everything_a_search_is_served(spec, release)
        # Nor is it asked whether it holds one, to take what is asked of a visit or to
        # turn away what cannot be.
        for edit in (
            budget(tenure="visit"),
            budget(amount=1500),
            budget(segment="flat"),
            budget("clear"),
            setting("set", "budget_weight", value=0.5),
            tag("nudge", "leafy", step="up_large"),
        ):
            assert apply(spec, ops(edit), release).spec.visiting
        assert release.asked == []
    # A search for a home that becomes a visit asks for none either.
    release = watched(small_release())
    assert apply(searching(), ops(budget(tenure="visit")), release).spec.visiting
    assert release.asked == []
    # The same release is asked, of a search for a home.
    everything_a_search_is_served(searching(), release)
    assert release.asked


def on_a_preview(spec: PreferenceSpec, *edits: Edit) -> ReducerResult:
    return apply(spec, ops(*edits), preview_release())


def test_a_release_that_holds_no_cost_serves_a_visit_whole():
    """A first build holds what nothing costs. It turns away a budget, and no visit."""
    release = preview_release()
    assert not release.costs
    ranked = {metric.feature_id for metric in release.metrics if metric.rankable}
    usual = VISITOR.replace(weights=tuple(w for w in VISITOR.weights if w.feature_id in ranked))
    assert usual.weights and check_spec(usual, release) == ()
    result = rank(usual, release)
    assert result.ranked and not result.filtered
    moved = on_a_preview(RENTER, budget(tenure="visit"))
    assert moved.rejected == () and moved.spec.visiting
    # A budget is turned away there, for a home as for a visit.
    assert reasons(on_a_preview(RENTER, budget(amount=1500))) == [RejectReason.NOT_IN_RELEASE]
    assert reasons(on_a_preview(usual, budget(amount=1500))) == [RejectReason.NOT_IN_RELEASE]


# What is said of a visit


def said_of(explanation: Explanation) -> list[str]:
    trade_off = [explanation.trade_off] if explanation.trade_off else []
    every = [explanation.orientation, *explanation.reasons, *trade_off, *explanation.missing]
    return [sentence.text for sentence in every]


def cited_by(explanation: Explanation) -> list[str]:
    trade_off = [explanation.trade_off] if explanation.trade_off else []
    every = [explanation.orientation, *explanation.reasons, *trade_off, *explanation.missing]
    return [fact_id for sentence in every for fact_id in sentence.fact_ids]


@pytest.mark.parametrize("release", [small_release(), fixture_release()], ids=["small", "served"])
def test_no_explanation_of_a_visit_speaks_of_what_a_home_costs(release: InMemoryRelease):
    sentences = 0
    draw = draws(76)
    drawn = (random_spec(draw, release) for _ in range(90))
    for spec in (VISITOR, *(spec for spec in drawn if spec.visiting)):
        result = rank(spec, release)
        areas = tuple(found.area_id for found in result.ranked)
        for explanation in explain(result, release, spec, areas, TemplateExplainer()):
            for text in said_of(explanation):
                assert not any(words in text for words in OF_COST), text
                sentences += 1
            for cited in cited_by(explanation):
                kind = cited.split("/")[1]
                assert kind not in (FactKind.COST, FactKind.BUDGET_FIT), cited
                assert not cited.endswith("/missing/budget"), cited
    assert sentences > 200
    # The words are those of a search for a home, where a budget is asked for.
    renter = RENTER.replace(budget=RENTER.budget.replace(amount=1500, weight=1.0))
    result = rank(renter, release)
    areas = tuple(found.area_id for found in result.ranked)
    of_a_home = explain(result, release, renter, areas, TemplateExplainer())
    assert any(words in text for found in of_a_home for text in said_of(found) for words in OF_COST)


def test_the_facts_of_a_visit_hold_no_cost_and_no_budget():
    release = small_release()
    for found in release.neighbourhoods:
        held = {fact.kind for fact in facts_for(release, found.area_id, VISITOR)}
        assert not held & {FactKind.COST, FactKind.BUDGET_FIT}
        assert FactKind.AREA in held and FactKind.FEATURE in held and FactKind.TAG in held
    # The page of an area holds what a home costs there, as it did: it is of no search.
    first = release.neighbourhoods[0].area_id
    assert FactKind.COST in {fact.kind for fact in facts_for(release, first, None)}
    assert FactKind.COST in {fact.kind for fact in facts_for(release, first, RENTER)}


# What a release may hold


def test_a_release_that_holds_a_cost_of_a_visit_is_refused():
    found = documents()
    row = dict(found["cost.json"]["rows"][0])
    for kind in Segment:
        found["cost.json"]["rows"] = [row | {"tenure": "visit", "segment": kind.value}]
        with pytest.raises(ReleaseError):
            parse_release(found)
    assert not any(small_release().costed(Tenure.VISIT, kind) for kind in Segment)
