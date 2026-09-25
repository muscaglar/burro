"""Explanations: a few sentences about a ranked area, each one checked before it is shown.

An explainer drafts; `explain` verifies every sentence and replaces any that
fails with the template for its fact. The explainer sees facts and
contributions, and never anything a person typed.

`explain` takes the template explainer and no other. The verifier checks
numbers and capitalised names, which is enough for fixed text and not for a
sentence a model wrote, so a second explainer is refused here until the
verifier is extended (contract, sections 7.4 and 11).
"""

from collections.abc import Mapping
from typing import Protocol

from burro_core._record import Record
from burro_core.catalogue import CRIME_CAVEAT, NEVER_A_TRADE_OFF
from burro_core.facts import Fact, facts_for
from burro_core.ids import (
    COMMUTE,
    FactKind,
    JourneyBand,
    SentenceOrigin,
    SentenceRole,
    TemplateId,
    TravelStatus,
    component_for_feature,
)
from burro_core.rank import Contribution, RankedArea, RankResult
from burro_core.release import Release
from burro_core.spec import PreferenceSpec, spec_hash
from burro_core.verify import Sentence, verify

MAX_REASONS = 3
# A reason is something the area does well. Below this a component adds to the
# score and is still no reason to live there: it can only be the trade-off.
# And a trade-off is something the area does badly: at or above this a
# component is never one, unless it is a shortfall a reason may not state, a
# home over budget or a journey over its cap.
REASON_MIN_UTILITY = 0.5
# And "badly" is not "a hair under a half". A walk of 5 minutes to a station,
# worth 0.48, was given as what an area gives up. A trade-off is worth less
# than this, or it falls short of a limit the person set. What lies between
# the two thresholds is neither: it is in the working of a result and nowhere
# else. It is a first figure, to be held against recorded searches. And what
# is worth less than this is still no trade-off where it is a short walk:
# `NEVER_A_TRADE_OFF` in the catalogue holds what is short.
TRADE_OFF_MAX_UTILITY = 0.35
# Where the decision is written down that `explain` takes one explainer only.
ONLY_THE_TEMPLATE = (
    "explain() takes TemplateExplainer and no other explainer until verify() is extended. "
    "Attaching another is a decision, not a parameter: see docs/design/contract.md, "
    "section 11, 'A model-written explanation', and section 7.4 for what verify() does not check."
)

# `{standing}` is one of the clauses of `STANDINGS` in `facts.py`, already
# filled: "closer than 80% of the 22 areas compared in this release".
_FEATURE = "{label}: {value}, {standing}."
_STATION = "{name}, about {walk} minutes on foot. Lines: {lines}."
_COUNTED = "counted from {low_end} to {high_end}"
_DATED = "Parts dated {span}. {judgement}"
# Where a band rests on part of its recipe, `{partly}` says so. It is empty
# where it rests on the whole, and the sentence is then as it always was.
_IN_PART = "{partly}"
# A vibe is a band among the areas compared, and never a percentage.
_VIBE = (
    f"{{label}}: band {{band}} of 5, {_COUNTED}, among the {{compared}} areas "
    f"compared in this release. {_IN_PART}"
)
# A mixed area is a range, never a point in the middle.
_VIBE_RANGE = (
    "{label}: varies within this area, from band {spread_low} to band {spread_high} "
    f"of 5, {_COUNTED}. {_IN_PART}"
)
_BY_PT = (
    "By public transport to {place}: about {typical} minutes on a typical weekday "
    "morning, {missed} if you just miss a service"
)
_BY_OTHER = "{mode} to {place}: about {minutes} minutes"
_OVER = ", {margin} {margin_unit} over the {limit} you set."

TEMPLATES: Mapping[TemplateId, str] = {
    TemplateId.AREA: "{name} is in {borough}.",
    TemplateId.FEATURE: _FEATURE,
    TemplateId.FEATURE_CRIME: f"{_FEATURE} {CRIME_CAVEAT}",
    TemplateId.VIBE: f"{_VIBE} {_DATED}",
    TemplateId.VIBE_RANGE: f"{_VIBE_RANGE} {_DATED}",
    TemplateId.VIBE_UNKNOWN: (
        "Burro cannot place {name} on {label}. "
        "Parts with a figure in this release: {known} of {parts}."
    ),
    TemplateId.COST_RENT: (
        "Rent for a {segment}: £{lower} to £{upper} a month, middle £{median}, "
        "as of {as_of}. Confidence: {confidence}."
    ),
    TemplateId.COST_BUY: (
        "Price for a {segment}: £{lower} to £{upper}, middle £{median}, "
        "as of {as_of}. Confidence: {confidence}."
    ),
    # A publisher's median, with no range. It says what the figure is of, and what is not
    # known of it. No word stands for a confidence that no source states.
    TemplateId.COST_BUY_MEDIAN: (
        "Price for a {segment}: £{median}. This is the middle price of {homes} of all sizes "
        "sold in {period}. The publisher gives no range, and does not say "
        "how many sales it rests on."
    ),
    # A median that Burro worked out from the sales themselves. It says how many it rests
    # on, and from which month to which.
    TemplateId.COST_BUY_SOLD: (
        "Price for a {segment}: £{median}. This is the middle price of the {sales} {homes} "
        "of all sizes sold from {period}."
    ),
    TemplateId.BUDGET_UNDER: "The upper end is £{margin} under your budget of £{amount}.",
    TemplateId.BUDGET_OVER: "The upper end is £{margin} over your budget of £{amount}.",
    TemplateId.BUDGET_UNDER_MEDIAN: (
        "The middle price of {homes} of all sizes is £{margin} under your budget of £{amount}."
    ),
    # A median that is over a budget says what a median is: about half sold for less.
    TemplateId.BUDGET_OVER_MEDIAN: (
        "The middle price of {homes} of all sizes is £{margin} over your budget of £{amount}. "
        "{half_sold}"
    ),
    TemplateId.TRAVEL_PT: f"{_BY_PT}.",
    TemplateId.TRAVEL_PT_OVER: f"{_BY_PT}{_OVER}",
    TemplateId.TRAVEL_OTHER: f"{_BY_OTHER}.",
    TemplateId.TRAVEL_OTHER_OVER: f"{_BY_OTHER}{_OVER}",
    TemplateId.TRAVEL_BEYOND: "{mode} to {place}: more than {cutoff} minutes.",
    # A journey that was estimated from distance. It says a band against the limit the
    # person set, never a number of minutes of its own, and says that it is an estimate.
    TemplateId.TRAVEL_ESTIMATED: "{mode} to {place}: {said} the {limit} minutes you set. "
    "{estimated}",
    TemplateId.STATION: f"Nearest station: {_STATION}",
    # The contract gives one station sentence. A station that is not the
    # nearest needs its own, or the template would say something untrue.
    TemplateId.STATION_NEARBY: f"Station within a short walk: {_STATION}",
    TemplateId.MISSING: (
        "There is no {label} figure for {name} in this release, so it was left out of the score."
    ),
    TemplateId.MISSING_JOURNEY: (
        "There is no journey time from {name} to {place} in this release, "
        "so that journey was left out of the score."
    ),
    TemplateId.LIKENESS: (
        "{name} is in the same band as {other} on {same} of the {measures} measures "
        "compared, and least alike in {family}."
    ),
    TemplateId.LIKENESS_SAME: (
        "{name} is in the same band as {other} on all {measures} measures compared."
    ),
}
# How a vibe is said in an explanation: where the area sits, and what that
# rests on where it is part of a recipe. A result is to say in a few lines why
# this place, and the full statement of a vibe ran to thirty words, half of
# them the same on every result that led with it. What is left out is not
# lost: the dates are the fact's `as_of`, and the line that the recipe is a
# judgement is its slot `judgement`, which a client shows with the source.
# Each is the start of the full statement, word for word, so a short sentence
# says nothing the full one does not.
IN_SHORT: Mapping[TemplateId, str] = {
    TemplateId.VIBE: _VIBE,
    TemplateId.VIBE_RANGE: _VIBE_RANGE,
}
# What is said of a figure from the side that counts as worse. A trade-off is
# filled from these, where a reason is filled from the slots they stand for.
_WORSE = {"standing": "standing_worse"}


class Ask(Record):
    """One sentence the explainer is asked for: what it is for and the fact it must cite."""

    role: SentenceRole
    component: str  # empty for the orientation
    fact_id: str


class ExplainInput(Record):
    """All an explainer is given about one area. It has no field that can hold user text."""

    area_id: str
    facts: tuple[Fact, ...]
    contributions: tuple[Contribution, ...]
    asks: tuple[Ask, ...]


class ExplainedSentence(Record):
    text: str
    fact_ids: tuple[str, ...]
    origin: SentenceOrigin
    # True when the drafted sentence failed the verifier and the template took its place.
    replaced: bool


class Explanation(Record):
    area_id: str
    orientation: ExplainedSentence
    reasons: tuple[ExplainedSentence, ...]
    trade_off: ExplainedSentence | None
    missing: tuple[ExplainedSentence, ...]


class Explainer(Protocol):
    def draft(self, area: ExplainInput) -> tuple[Sentence, ...]:
        """One sentence for each of `area.asks`, in the same order."""
        ...


def render(
    fact: Fact, role: SentenceRole = SentenceRole.REASON, *, short: bool = False
) -> Sentence:
    """The template sentence for a fact, said from the side of its role.

    A figure is said from the side that counts as better, but for a
    trade-off, which is said from the side that counts as worse: "further
    than 47% of areas" is no reason, and "closer than 52%" no trade-off. A
    fact that holds one side only, as a vibe and a journey do, is said the
    same in every role.

    `short` is how an explanation says it: a fact of `IN_SHORT` without its
    dates and the line about judgement, and every other fact in full.
    """
    slots = fact.slots
    if role is SentenceRole.TRADE_OFF:
        turned = {name: slots[worse] for name, worse in _WORSE.items() if worse in slots}
        slots = slots | turned
    in_full = TEMPLATES[fact.template]
    template = IN_SHORT.get(fact.template, in_full) if short else in_full
    return Sentence(
        # A clause that is empty leaves two spaces where it stood.
        text=" ".join(template.format(**slots).split()),
        fact_ids=(fact.fact_id,),
        origin=SentenceOrigin.TEMPLATE,
    )


class TemplateExplainer:
    """States each fact with its template. The only explainer in this build."""

    def draft(self, area: ExplainInput) -> tuple[Sentence, ...]:
        facts = {fact.fact_id: fact for fact in area.facts}
        return tuple(render(facts[ask.fact_id], ask.role, short=True) for ask in area.asks)


def _trade_off(badly: list[Contribution]) -> Contribution | None:
    """What the area does badly that costs it most, if it does anything badly.

    A trade-off is never something the area does well. "A 2 minute walk,
    closer than 77% of areas" loses a little to the areas that are closer
    still, and was once given as what the area gives up, because nothing
    lost more. An area that does nothing badly has no trade-off, and that is
    what is said of it.
    """
    by_loss = sorted(badly, key=lambda c: (-c.loss, c.component))
    return next((c for c in by_loss if c.loss > 0), None)


def _over_a_cap(area: RankedArea, spec: PreferenceSpec) -> bool:
    """Whether a journey that was scored is longer than the person will put up with."""
    caps = {commute.place_id: commute.max_minutes for commute in spec.commutes}
    return any(
        leg.status is TravelStatus.BEYOND_CUTOFF
        or leg.estimate is JourneyBand.LIKELY_BEYOND
        or (leg.minutes is not None and leg.minutes > caps[leg.place_id])
        for leg in area.legs
    )


def _a_short_walk(contribution: Contribution, area: RankedArea, release: Release) -> bool:
    """Whether a component is a walk, a time or a distance that is short in itself.

    Where an area stands among the others says nothing of how far a walk
    is. A walk of seven minutes to a station was worth 0.34, since fourteen
    areas are closer still, and was given as what the area gives up. The
    catalogue holds the figure at or under which each is never a trade-off.
    """
    for feature_id, figure in NEVER_A_TRADE_OFF.items():
        if contribution.component == component_for_feature(feature_id):
            row = release.feature(area.area_id, feature_id)
            return row is not None and row.value is not None and row.value <= figure
    return False


def _done_badly(
    contribution: Contribution, area: RankedArea, spec: PreferenceSpec, release: Release
) -> bool:
    """Whether a component is something an area gives up.

    It is worse than most and bad in itself: worth less than
    `TRADE_OFF_MAX_UTILITY`, and no short walk. Or it falls short of a limit
    the person set: a home over budget, a journey over its cap.
    """
    if contribution.utility is None:
        return False
    if contribution.utility < TRADE_OFF_MAX_UTILITY:
        return not _a_short_walk(contribution, area, release)
    if contribution.component == "budget":
        return area.budget is not None and area.budget.margin < 0
    return contribution.component == COMMUTE and _over_a_cap(area, spec)


def _within_every_cap(area: RankedArea, spec: PreferenceSpec) -> bool:
    """Whether every journey has a time, and none is longer than the person will put up with.

    The mean of two journeys can be done well while one of them is over its
    cap, and the sentence states the slower one. And a journey with no time
    may be any length, so the journeys are no reason while one is unknown.
    """
    caps = {commute.place_id: commute.max_minutes for commute in spec.commutes}
    return all(
        # A journey that is estimated is a reason only where it is likely within its
        # limit. One that is borderline is neither a reason nor what the area gives up.
        leg.estimate is JourneyBand.LIKELY_WITHIN
        or (
            leg.status is TravelStatus.OK
            and leg.minutes is not None
            and leg.minutes <= caps[leg.place_id]
        )
        for leg in area.legs
    )


def _done_well(contribution: Contribution, area: RankedArea, spec: PreferenceSpec) -> bool:
    """Whether a component is something to give as a reason to live in the area.

    A home over budget and a journey over its cap never are, whatever they
    are worth to the score: a reason does not state a shortfall.
    """
    if contribution.utility is None or contribution.utility < REASON_MIN_UTILITY:
        return False
    if contribution.component == "budget":
        return area.budget is not None and area.budget.margin >= 0
    if contribution.component == "commute":
        return _within_every_cap(area, spec)
    return True


def _asks(
    area: RankedArea, facts: Mapping[str, Fact], spec: PreferenceSpec, release: Release
) -> tuple[Ask, ...]:
    def ask(role: SentenceRole, contribution: Contribution) -> Ask:
        # The first fact is the one that stands behind the component. For a
        # commute it is the leg that drove the score.
        return Ask(role=role, component=contribution.component, fact_id=contribution.fact_ids[0])

    orientation = next(f.fact_id for f in facts.values() if f.kind is FactKind.AREA)
    # Contributions arrive largest first, then by name.
    present = [c for c in area.contributions if c.present]
    well = [c for c in present if _done_well(c, area, spec)]
    reasons = well[:MAX_REASONS]
    # What is done well is a reason or is left unsaid. It is never the trade-off.
    trade_off = _trade_off([c for c in present if _done_badly(c, area, spec, release)])
    asks = [Ask(role=SentenceRole.ORIENTATION, component="", fact_id=orientation)]
    asks += [ask(SentenceRole.REASON, c) for c in reasons]
    if trade_off is not None:
        asks.append(ask(SentenceRole.TRADE_OFF, trade_off))
    # One sentence for each thing that has no figure: a component that was
    # dropped, and each journey with no time, whether or not the rest were scored.
    asks += [
        Ask(role=SentenceRole.MISSING, component=contribution.component, fact_id=cited)
        for contribution in area.contributions
        for cited in contribution.fact_ids
        if cited in facts and facts[cited].kind is FactKind.MISSING
    ]
    return tuple(asks)


def _cites_only(ask: Ask, drafted: Sentence, facts: Mapping[str, Fact]) -> bool:
    """Whether a sentence cites the fact it was asked about, the area's name, and no more.

    What a sentence cites is what it may say. If it could cite every fact of
    the area it could say the minutes of a journey of a park. The area fact
    holds names and no number, so it lets a sentence name the area and
    nothing else.
    """
    named = {fact_id for fact_id, fact in facts.items() if fact.kind is FactKind.AREA}
    cited = drafted.fact_ids
    return bool(cited) and cited[0] == ask.fact_id and set(cited[1:]) <= named


def _checked(ask: Ask, drafted: Sentence | None, facts: Mapping[str, Fact]) -> ExplainedSentence:
    """The drafted sentence if it holds up, and otherwise the template for the fact asked about."""
    kept = drafted is not None and _cites_only(ask, drafted, facts) and verify(drafted, facts).ok
    sentence = (
        drafted
        if drafted is not None and kept
        else render(facts[ask.fact_id], ask.role, short=True)
    )
    return ExplainedSentence(
        text=sentence.text,
        fact_ids=sentence.fact_ids,
        origin=sentence.origin,
        replaced=not kept,
    )


def _explain_area(
    area: RankedArea, release: Release, spec: PreferenceSpec, explainer: Explainer
) -> Explanation:
    found = facts_for(release, area.area_id, spec)
    facts = {fact.fact_id: fact for fact in found}
    asks = _asks(area, facts, spec, release)
    drafted = explainer.draft(
        ExplainInput(area_id=area.area_id, facts=found, contributions=area.contributions, asks=asks)
    )
    # A draft of the wrong length cannot be matched to what was asked, so none of it is used.
    aligned = drafted if len(drafted) == len(asks) else (None,) * len(asks)
    checked = [
        (ask.role, _checked(ask, sentence, facts))
        for ask, sentence in zip(asks, aligned, strict=True)
    ]

    def of(role: SentenceRole) -> tuple[ExplainedSentence, ...]:
        return tuple(sentence for found_role, sentence in checked if found_role is role)

    return Explanation(
        area_id=area.area_id,
        orientation=of(SentenceRole.ORIENTATION)[0],
        reasons=of(SentenceRole.REASON),
        trade_off=next(iter(of(SentenceRole.TRADE_OFF)), None),
        missing=of(SentenceRole.MISSING),
    )


def explain(
    result: RankResult,
    release: Release,
    spec: PreferenceSpec,
    area_ids: tuple[str, ...],
    explainer: Explainer,
) -> tuple[Explanation, ...]:
    """Explain each of `area_ids` that the result ranked, in the order given.

    An area the result did not rank has no contributions to explain, so it is
    left out. Raises `ValueError` if the result is not the ranking of this
    spec on this release, and `TypeError` if the explainer is not the
    template explainer.
    """
    # A check in code, so that a second explainer cannot be attached by
    # passing one in. A test that plants a sentence does it from a subclass.
    if not isinstance(explainer, TemplateExplainer):
        raise TypeError(ONLY_THE_TEMPLATE)
    if result.spec_hash != spec_hash(spec) or result.release_id != release.manifest.release_id:
        raise ValueError("the result is not the ranking of this spec on this release")
    ranked = {area.area_id: area for area in result.ranked}
    return tuple(
        _explain_area(ranked[area_id], release, spec, explainer)
        for area_id in area_ids
        if area_id in ranked
    )
