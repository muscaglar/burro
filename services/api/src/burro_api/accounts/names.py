"""The name of a search that is kept: what was understood, said in a line.

It is worked out from the spec, and from the names the data gives to a place, an area, a
vibe and a measure. A spec holds ids and numbers and no word that anybody typed, so no
name does either.

What is named is what a person asked for. Which things those are is core's to say, and a
usual setting that nobody chose is not among them. Nothing is said here of any area: a
name says what a search holds, and never what a place is like.
"""

from collections.abc import Iterator, Sequence

from burro_core.catalogue import default_direction
from burro_core.facts import MODE_LABELS, SEGMENT_LABELS, money
from burro_core.ids import (
    AreaRuleKind,
    Strictness,
    TagShape,
    Tenure,
    Toward,
    component_for_feature,
)
from burro_core.rank import asked_for
from burro_core.release import Release
from burro_core.spec import AreaRule, Commute, PreferenceSpec

# The longest a name may be. What does not fit is said to be more, and is not cut short.
LONGEST = 200
# How many vibes and measures are named. The rest are counted.
NAMED = 4
# How many areas are named of those a search asks for, or leaves out.
AREAS_NAMED = 2

# Every kind of search has a word, or a search of that kind cannot be kept. A visit holds
# no budget and no kind of home, so its word is never followed by either.
DOING = {Tenure.RENT: "Renting", Tenure.BUY: "Buying", Tenure.VISIT: "Visiting"}
# What a search holds that nobody chose, as the website says it. No page says "settings".
USUAL = "with what Burro counts in every search"
A_MONTH = " a month"
# A budget and a journey that leave areas out, and ones that only rank them lower.
FIRM_BUDGET = "up to"
GUIDE_BUDGET = "around"
FIRM_JOURNEY = "at most"
GUIDE_JOURNEY = "about"
A_PLACE = "a place"
ONLY_IN = "only in"
NOT_IN = "not in"
AND = " and "
AND_MORE = "and more"


def _a(thing: str) -> str:
    return f"an {thing}" if thing[:1] in "aeiou8" else f"a {thing}"


def _counted(count: int, one: str, many: str) -> str:
    return f"and {count} more {one if count == 1 else many}"


def _journey(commute: Commute, release: Release) -> str:
    place = release.place(commute.place_id)
    firm = commute.strictness is Strictness.HARD
    way = MODE_LABELS[commute.mode]
    return (
        f"{FIRM_JOURNEY if firm else GUIDE_JOURNEY} {commute.max_minutes} minutes to "
        # The way of travelling is core's own word, which begins a sentence there.
        f"{place.name if place else A_PLACE} {way[:1].lower()}{way[1:]}"
    )


def _home_and_budget(spec: PreferenceSpec) -> Iterator[str]:
    doing = DOING[spec.tenure]
    amount = spec.budget.amount
    if amount is None or not spec.budget_requested:
        # A kind of home is what a budget is held against, and is nothing without one.
        yield doing
        return
    yield f"{doing} {_a(SEGMENT_LABELS[spec.budget.segment])}"
    firm = spec.budget.strictness is Strictness.HARD
    by = A_MONTH if spec.tenure is Tenure.RENT else ""
    yield f"{FIRM_BUDGET if firm else GUIDE_BUDGET} \N{POUND SIGN}{money(amount)}{by}"


def _things(spec: PreferenceSpec, release: Release) -> tuple[list[str], int]:
    """The vibes and the measures that were asked for, by name, and how many have no name.

    What counts most comes first. A measure is named as the data names it, which is by
    the way it usually runs: one that was turned round is counted, and never named as
    its opposite.
    """
    vibes = {vibe.tag_id: vibe for vibe in release.vibes}
    metrics = {metric.feature_id: metric for metric in release.metrics}
    asked = asked_for(spec)
    found: list[tuple[float, str, str | None]] = []
    for tag in spec.active_tags:
        vibe = vibes.get(tag.tag_id)
        name = None
        if vibe is not None and vibe.shape is TagShape.SCALE:
            name = vibe.low_end if tag.toward is Toward.LOW else vibe.high_end
        elif vibe is not None:
            name = vibe.short_label
        found.append((-tag.weight, tag.tag_id.value, name))
    for weight in spec.active_weights:
        if component_for_feature(weight.feature_id) not in asked:
            continue
        metric = metrics.get(weight.feature_id)
        usual = weight.direction is default_direction(weight.feature_id)
        name = metric.short_label if metric is not None and usual else None
        found.append((-weight.weight, weight.feature_id.value, name))
    names = [name for _, _, name in sorted(found, key=lambda each: each[:2]) if name]
    return names[:NAMED], len(found) - len(names[:NAMED])


def _areas(rules: Sequence[AreaRule], release: Release, kind: AreaRuleKind, said: str) -> str:
    areas = [release.neighbourhood(rule.area_id) for rule in rules if rule.rule is kind]
    names = [area.name for area in areas if area is not None]
    if not areas:
        return ""
    named, rest = names[:AREAS_NAMED], len(areas) - len(names[:AREAS_NAMED])
    if not named:
        # Areas the data no longer holds. They are counted, and have no name to give.
        return f"{said} {rest} {'area' if rest == 1 else 'areas'}"
    if rest:
        return f"{said} {', '.join(named)} {_counted(rest, 'area', 'areas')}"
    return f"{said} {AND.join(named)}"


def _parts(spec: PreferenceSpec, release: Release) -> Iterator[str]:
    yield from _home_and_budget(spec)
    if spec.commute_requested:
        yield from (_journey(commute, release) for commute in spec.commutes)
    names, rest = _things(spec, release)
    yield from names
    if rest:
        yield _counted(rest, "thing", "things")
    yield _areas(spec.areas, release, AreaRuleKind.ONLY, ONLY_IN)
    yield _areas(spec.areas, release, AreaRuleKind.EXCLUDE, NOT_IN)


def name_of(spec: PreferenceSpec, release: Release) -> str:
    """What the search holds, said in a line that is no longer than `LONGEST`."""
    parts = [part for part in _parts(spec, release) if part]
    if len(parts) == 1:
        return f"{parts[0]}, {USUAL}"
    kept: list[str] = []
    for at, part in enumerate(parts):
        last = at == len(parts) - 1
        room = LONGEST - (0 if last else len(f", {AND_MORE}"))
        if len(", ".join([*kept, part])) > room:
            # What does not fit is said to be there, and nothing is cut in two.
            return ", ".join([*kept, AND_MORE])
        kept.append(part)
    return ", ".join(kept)
