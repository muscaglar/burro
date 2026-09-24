"""Routes 2, 3 and 7: rank, explain and compare. Each is a function of the body and the release.

They are `POST` only to keep destinations out of URLs. None of them needs a
model, so with no key, a slow model or a capped one, the product is still the
form these routes serve.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from burro_core.catalogue import FEATURES, TAGS
from burro_core.explain import Explanation, explain
from burro_core.facts import Fact, cost_key, fact_id, facts_for
from burro_core.ids import (
    BUDGET,
    COMMUTE,
    FactKind,
    FeatureId,
    TagId,
    component_for_feature,
    component_for_tag,
)
from burro_core.rank import Contribution, RankedArea, RankResult, rank
from burro_core.reducer import apply
from burro_core.release import Release
from burro_core.spec import PreferenceSpec
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
    ranking,
)
from burro_api.wire import (
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
            **ranking(result, body.limit),
        ),
    )


def _cited(
    explanations: tuple[Explanation, ...], release: Release, spec: PreferenceSpec
) -> tuple[Fact, ...]:
    """Every fact a sentence cites, so that each number shown has its source and its date."""
    found: list[Fact] = []
    for explanation in explanations:
        sentences = (
            explanation.orientation,
            *explanation.reasons,
            *((explanation.trade_off,) if explanation.trade_off else ()),
            *explanation.missing,
        )
        cited = {cited_id for sentence in sentences for cited_id in sentence.fact_ids}
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
        ExplanationsData(explanations=explained, facts=_cited(explained, release, body.spec)),
    )


@dataclass(frozen=True)
class _Component:
    """One requested component of the score: a row of the comparison."""

    name: str
    label: str
    weight: float
    feature_id: FeatureId | None = None
    tag_id: TagId | None = None


def _components(spec: PreferenceSpec) -> tuple[_Component, ...]:
    """Every requested component, by weight from high to low, then by name."""
    found: list[_Component] = []
    if spec.commute_requested:
        found.append(_Component(COMMUTE, LABELS[COMMUTE], spec.commute_weight))
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


def _driver(area: RankedArea, scored: Contribution) -> int | None:
    """The minutes of the journey that drove the score: the first fact the component cites."""
    for leg in area.legs:
        key = f"{leg.place_id}.{leg.mode}"
        if fact_id(area.area_id, FactKind.TRAVEL, key) == scored.fact_ids[0]:
            return leg.minutes
    return None


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
        if component.name == BUDGET:
            key = cost_key(self._spec.tenure, self._spec.budget.segment)
            return fact_id(area_id, FactKind.BUDGET_FIT, key)
        # Which journey drives the score is decided by scoring, so an area that
        # was not scored shows no journey. Working it out here would be a second
        # copy of the arithmetic in `rank()`.
        return ""

    def _fact_id(
        self, area_id: str, component: _Component, scored: Contribution | None
    ) -> str | None:
        """The fact behind a cell, if there is one. A cell never cites a fact that is not served."""
        facts = self._facts_of(area_id)
        wanted = scored.fact_ids[0] if scored else self._expected(area_id, component)
        missing = fact_id(area_id, FactKind.MISSING, component.name)
        for candidate in (wanted, missing):
            if candidate in facts:
                self.cited[candidate] = facts[candidate]
                return candidate
        return None

    def _figures(
        self, area_id: str, component: _Component, scored: Contribution | None
    ) -> tuple[float | None, float | None]:
        """The value and the percentile, read from the release. `None` where there is none."""
        release, spec = self._release, self._spec
        if component.feature_id is not None:
            row = release.feature(area_id, component.feature_id)
            return (row.value, row.percentile) if row else (None, None)
        if component.tag_id is not None:
            tag = release.tag(area_id, component.tag_id)
            return None, tag.score if tag else None
        if component.name == BUDGET:
            estimate = release.cost(area_id, spec.tenure, spec.budget.segment)
            return (estimate.upper_quartile if estimate else None), None
        area = self._ranked.get(area_id)
        return (_driver(area, scored) if area and scored and scored.present else None), None

    def cell(self, area_id: str, component: _Component) -> CompareCell:
        area = self._ranked.get(area_id)
        contributions = area.contributions if area else ()
        scored = next((c for c in contributions if c.component == component.name), None)
        value, percentile = self._figures(area_id, component, scored)
        return CompareCell(
            area_id=area_id,
            value=value,
            percentile=percentile,
            # An area that is not ranked was not scored, so it has neither.
            utility=scored.utility if scored else None,
            contribution=scored.contribution if scored and scored.present else None,
            fact_id=self._fact_id(area_id, component, scored),
        )


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
    rows = tuple(
        CompareRow(
            component=component.name,
            label=component.label,
            weight=component.weight,
            cells=tuple(comparison.cell(area_id, component) for area_id in body.area_ids),
        )
        for component in _components(body.spec)
    )
    return envelope(
        context,
        CompareData(
            areas=tuple(
                ComparedArea(
                    area_id=area.area_id, name=area.name, status=_status(area.area_id, result)
                )
                for area in areas
                if area is not None
            ),
            rows=rows,
            facts=tuple(fact for _, fact in sorted(comparison.cited.items())),
        ),
    )
