"""Routes 2, 3 and 7: rank, explain and compare. Each is a function of the body and the release.

They are `POST` only to keep destinations out of URLs. None of them needs a
model, so with no key, a slow model or a capped one, the product is still the
form these routes serve.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from burro_core.catalogue import FEATURES, TAGS
from burro_core.explain import Explanation, explain
from burro_core.facts import (
    Fact,
    cost_key,
    fact_id,
    facts_for,
    journey_key,
    scored_on_just_missed,
    travel_key,
)
from burro_core.ids import (
    BUDGET,
    COMMUTE,
    Combine,
    FactKind,
    FeatureId,
    PtBasis,
    TagId,
    component_for_feature,
    component_for_tag,
)
from burro_core.rank import Contribution, RankResult, budget_held_against, rank
from burro_core.reducer import apply
from burro_core.release import Release
from burro_core.spec import Commute, PreferenceSpec
from fastapi import APIRouter

from burro_api import logs
from burro_api.calls import Caller, CallRecord, CallStatus, Endpoint
from burro_api.deps import Ctx
from burro_api.errors import ApiError
from burro_api.routes.common import (
    NOT_FOUND,
    PREFIX,
    WITH_BODY,
    RequestId,
    check,
    envelope,
    places_of,
    ranking,
)
from burro_api.wire import (
    CharacterMark,
    CharacterRow,
    CompareBody,
    CompareCell,
    ComparedArea,
    CompareData,
    CompareRow,
    CompareStatus,
    Envelope,
    ErrorCode,
    ExplanationsBody,
    ExplanationsData,
    NamedPlace,
    RankBody,
    RankData,
)

router = APIRouter(prefix=PREFIX)

# What a row of a comparison is called when it is not a feature or a tag.
LABELS: Mapping[str, str] = {COMMUTE: "Journey", BUDGET: "Budget"}


@router.post("/rank", name="rank", response_model=Envelope[RankData], responses=WITH_BODY)
def rank_areas(body: RankBody, context: Ctx) -> Envelope[RankData]:
    """Apply any edits to the spec, then rank every area of the release for it."""
    release = context.release
    # A slider's edit goes through the same reducer as a sentence's.
    reduced = apply(body.spec, body.operations, release) if body.operations else None
    spec = reduced.spec if reduced else body.spec
    # The spec is checked as the edits leave it, so that a spec which names
    # what a newer release has dropped can be put right by taking it out.
    check(spec, release)
    result = rank(spec, release)
    return envelope(
        context,
        RankData(
            spec=spec,
            spec_hash=result.spec_hash,
            applied=reduced.applied if reduced else (),
            rejected=reduced.rejected if reduced else (),
            places=places_of(spec, release),
            **ranking(result, body.limit),
        ),
    )


def _cited(
    explanations: tuple[Explanation, ...],
    result: RankResult,
    release: Release,
    spec: PreferenceSpec,
) -> tuple[Fact, ...]:
    """Every fact a sentence cites, and the fact of every mark on the strip of an area explained.

    So each number and each band that is shown has its source and its date.
    """
    strips = {area.area_id: area.strip for area in result.ranked}
    found: list[Fact] = []
    for explanation in explanations:
        sentences = (
            explanation.orientation,
            *explanation.reasons,
            *((explanation.trade_off,) if explanation.trade_off else ()),
            *explanation.missing,
        )
        cited = {cited_id for sentence in sentences for cited_id in sentence.fact_ids}
        cited |= {mark.fact_id for mark in strips.get(explanation.area_id, ())}
        facts = facts_for(release, explanation.area_id, spec)
        found += [fact for fact in facts if fact.fact_id in cited]
    return tuple(found)


@router.post("/explanations", response_model=Envelope[ExplanationsData], responses=WITH_BODY)
def explain_top(
    body: ExplanationsBody, context: Ctx, request_id: RequestId
) -> Envelope[ExplanationsData]:
    """A few checked sentences about each of the top areas, and the facts they cite."""
    deps, meta, release = context.deps, context.meta, context.release
    check(body.spec, release)
    began = deps.clock.elapsed()
    result = rank(body.spec, release)
    top = tuple(area.area_id for area in result.ranked[: body.limit])
    # Every sentence is verified inside `explain`, whoever drafted it.
    explained = explain(result, release, body.spec, top, deps.explainer)
    latency_ms = round((deps.clock.elapsed() - began) * 1000)

    # The template explainer is the only one in this build, and it calls no
    # model. Nothing of the spec is kept or logged, not even a hash of it.
    deps.calls.add(
        CallRecord(
            call_id=deps.ids.call_id(),
            at=context.timestamp(),
            endpoint=Endpoint.EXPLAIN,
            interpreter=Caller.TEMPLATE,
            # The sentences are written from templates. No provider is asked.
            provider="",
            model="",
            status=CallStatus.OK,
            degraded=False,
            input_tokens=0,
            output_tokens=0,
            cache_read_tokens=0,
            latency_ms=latency_ms,
            release_id=meta.release_id,
            engine_version=meta.engine_version,
        )
    )
    logs.event(
        "explain",
        request_id=request_id,
        endpoint=Endpoint.EXPLAIN.value,
        interpreter=Caller.TEMPLATE.value,
        call_status=CallStatus.OK.value,
        latency_ms=latency_ms,
    )
    return envelope(
        context,
        ExplanationsData(
            # Served to the caller, who holds the spec. It is in no line and no record.
            spec_hash=result.spec_hash,
            explanations=explained,
            facts=_cited(explained, result, release, body.spec),
        ),
    )


@dataclass(frozen=True)
class _Component:
    """One row of the comparison: a thing that counts, or one journey of those that count."""

    name: str
    label: str
    weight: float
    feature_id: FeatureId | None = None
    tag_id: TagId | None = None
    # The journey of the row. The journeys count as one thing and are shown
    # one to a row, so that every cell of a row is to the same place.
    journey: Commute | None = None

    @property
    def scored_as(self) -> str:
        """The component of the score this row is part of."""
        return COMMUTE if self.journey is not None else self.name


def _components(spec: PreferenceSpec) -> tuple[_Component, ...]:
    """Every row, by weight from high to low, then by name. The journeys keep the spec's order."""
    found: list[_Component] = []
    if spec.commute_requested:
        # Named as core keys a journey, which puts them in the order of their places.
        found += [
            _Component(journey_key(c), LABELS[COMMUTE], spec.commute_weight, journey=c)
            for c in spec.commutes
        ]
    if spec.budget_requested:
        found.append(_Component(BUDGET, LABELS[BUDGET], spec.budget.weight))
    found += [
        _Component(
            component_for_feature(w.feature_id),
            FEATURES[w.feature_id].label,
            w.weight,
            feature_id=w.feature_id,
        )
        for w in spec.active_weights
    ]
    found += [
        _Component(component_for_tag(t.tag_id), TAGS[t.tag_id].label, t.weight, tag_id=t.tag_id)
        for t in spec.active_tags
    ]
    return tuple(sorted(found, key=lambda c: (-c.weight, c.name)))


def _status(area_id: str, result: RankResult) -> CompareStatus:
    reasons = {f.area_id: f.reason.value for f in result.filtered}
    reasons |= {u.area_id: u.reason.value for u in result.unranked}
    return CompareStatus(reasons.get(area_id, CompareStatus.RANKED.value))


class _Comparison:
    """Works out each cell of a comparison, and collects the facts the cells cite."""

    def __init__(self, spec: PreferenceSpec, release: Release, result: RankResult) -> None:
        self._spec = spec
        self._release = release
        self._ranked = {area.area_id: area for area in result.ranked}
        self._facts: dict[str, dict[str, Fact]] = {}
        self.cited: dict[str, Fact] = {}

    def _facts_of(self, area_id: str) -> dict[str, Fact]:
        if area_id not in self._facts:
            found = facts_for(self._release, area_id, self._spec)
            self._facts[area_id] = {fact.fact_id: fact for fact in found}
        return self._facts[area_id]

    def _expected(self, area_id: str, component: _Component) -> str:
        """For an area that was not scored: the fact its figure comes from, by the rule of 7.1."""
        if component.feature_id is not None:
            return fact_id(area_id, FactKind.FEATURE, component.feature_id)
        if component.tag_id is not None:
            return fact_id(area_id, FactKind.TAG, component.tag_id)
        if component.journey is not None:
            return fact_id(area_id, FactKind.TRAVEL, travel_key(component.journey))
        key = cost_key(self._spec.tenure, self._spec.budget.segment)
        return fact_id(area_id, FactKind.BUDGET_FIT, key)

    def _fact_id(
        self, area_id: str, component: _Component, scored: Contribution | None
    ) -> str | None:
        """The fact behind a cell, if there is one. A cell never cites a fact that is not served."""
        facts = self._facts_of(area_id)
        if scored is not None and component.journey is None:
            wanted = scored.fact_ids[0]
        else:
            # An area that was not scored, or a journey: each journey has a
            # fact of its own, whichever of them the score cites first.
            wanted = self._expected(area_id, component)
        # A journey with no time is said to have none, by the fact core keys as the row is.
        missing = fact_id(area_id, FactKind.MISSING, component.name)
        for candidate in (wanted, missing):
            if candidate in facts:
                self.cited[candidate] = facts[candidate]
                return candidate
        return None

    def _minutes(self, area_id: str, journey: Commute) -> int | None:
        """The time of one journey that is scored, as the release holds it, or `None`."""
        place = self._release.place(journey.place_id)
        if place is None:
            return None
        late = scored_on_just_missed(journey, self._spec)
        basis = PtBasis.JUST_MISSED if late else PtBasis.TYPICAL
        return self._release.travel(area_id, place.destination_id, journey.mode, basis).minutes

    def _figures(self, area_id: str, component: _Component) -> tuple[float | None, float | None]:
        """The value and the percentile, read from the release. `None` where there is none."""
        release, spec = self._release, self._spec
        if component.feature_id is not None:
            row = release.feature(area_id, component.feature_id)
            return (row.value, row.percentile) if row else (None, None)
        if component.tag_id is not None:
            # A vibe is shown as a band, which is in `character`. The score it
            # is ranked on is no figure of its fact, and is never printed.
            return None, None
        if component.journey is not None:
            return self._minutes(area_id, component.journey), None
        estimate = release.cost(area_id, spec.tenure, spec.budget.segment)
        # The figure the budget was held against: the median, where a cost has no range.
        return (budget_held_against(estimate) if estimate else None), None

    def _journey(
        self, area_id: str, journey: Commute, scored: Contribution | None
    ) -> tuple[float | None, float | None]:
        """What one journey is worth, and what the journeys add where this one is all that counts.

        Both are core's: a route works out neither. What the journeys add is
        one figure for them all. It stands in the cell of the journey that
        drove the score, which is the first fact the component cites, where
        that journey alone decides it: the slowest counts, or there is one
        journey. Where every journey counts, what one of them adds is not
        something the ranking says, so no cell holds it.
        """
        area = self._ranked.get(area_id)
        if area is None or scored is None:
            return None, None  # an area that is not ranked was not scored
        worth = next((leg.utility for leg in area.legs if leg.place_id == journey.place_id), None)
        alone = self._spec.commute_combine is Combine.SLOWEST or len(self._spec.commutes) == 1
        timed = fact_id(area_id, FactKind.TRAVEL, travel_key(journey))
        drove = scored.present and scored.fact_ids[0] == timed
        return worth, (scored.contribution if alone and drove else None)

    def mark(self, area_id: str, tag_id: TagId) -> CharacterMark:
        """Where an area sits on a vibe, as the release holds it, and the fact that says so."""
        row = self._release.tag(area_id, tag_id)
        said = fact_id(area_id, FactKind.TAG, tag_id)
        self.cited[said] = self._facts_of(area_id)[said]
        return CharacterMark(
            area_id=area_id,
            band=row.band if row else None,
            spread_low=row.spread_low if row else None,
            spread_high=row.spread_high if row else None,
            fact_id=said,
        )

    def counted(self, area_id: str) -> tuple[int, int]:
        """How many things count, and for how many the area has a figure. 0 if it is not ranked."""
        area = self._ranked.get(area_id)
        return (area.counted, area.present) if area else (0, 0)

    def cell(self, area_id: str, component: _Component) -> CompareCell:
        area = self._ranked.get(area_id)
        contributions = area.contributions if area else ()
        scored = next((c for c in contributions if c.component == component.scored_as), None)
        value, percentile = self._figures(area_id, component)
        if component.journey is not None:
            utility, contribution = self._journey(area_id, component.journey, scored)
        else:
            # An area that is not ranked was not scored, so it has neither.
            utility = scored.utility if scored else None
            contribution = scored.contribution if scored and scored.present else None
        return CompareCell(
            area_id=area_id,
            value=value,
            percentile=percentile,
            utility=utility,
            contribution=contribution,
            fact_id=self._fact_id(area_id, component, scored),
        )

    def place(self, component: _Component) -> NamedPlace | None:
        """Where the journey of a row is to, by the release's name. `None` for any other row."""
        found = self._release.place(component.journey.place_id) if component.journey else None
        if found is None:
            return None
        return NamedPlace(place_id=found.place_id, name=found.name, kind=found.kind)


@router.post("/compare", response_model=Envelope[CompareData], responses=WITH_BODY | NOT_FOUND)
def compare(body: CompareBody, context: Ctx) -> Envelope[CompareData]:
    """Two to four areas side by side, the rows in the order of the person's own weights."""
    release = context.release
    areas = [release.neighbourhood(area_id) for area_id in body.area_ids]
    if any(area is None for area in areas):
        raise ApiError(ErrorCode.AREA_NOT_FOUND)
    check(body.spec, release)
    result = rank(body.spec, release)
    comparison = _Comparison(body.spec, release, result)
    character = tuple(
        CharacterRow(
            tag_id=vibe.tag_id,
            marks=tuple(comparison.mark(area_id, vibe.tag_id) for area_id in body.area_ids),
        )
        for vibe in release.vibes
        if vibe.table
    )
    rows = tuple(
        CompareRow(
            component=component.name,
            label=component.label,
            weight=component.weight,
            place=comparison.place(component),
            cells=tuple(comparison.cell(area_id, component) for area_id in body.area_ids),
        )
        for component in _components(body.spec)
    )
    return envelope(
        context,
        CompareData(
            areas=tuple(
                ComparedArea(
                    area_id=area.area_id,
                    name=area.name,
                    status=_status(area.area_id, result),
                    counted=counted,
                    present=present,
                )
                for area in areas
                if area is not None
                for counted, present in [comparison.counted(area.area_id)]
            ),
            character=character,
            rows=rows,
            facts=tuple(fact for _, fact in sorted(comparison.cited.items())),
        ),
    )
