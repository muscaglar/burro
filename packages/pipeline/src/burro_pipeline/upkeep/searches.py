"""The first areas of a search on a release: a search as typed edits, ranked by core.

A person who approves a build wants to know what it moves for somebody who searches. So
a few searches are kept as typed edits, and each is ranked on a release by core's own
`rank`, as the website's search is. The panel of the review desk ranks them before and
after a change, and the step `moved` before and after a build. There is one copy of
the arithmetic, and it is here.

A search is read from a file of searches, which holds typed edits and no words. Where a
search is of a sentence of the reader's evaluation set, the file names the case, and a
place is named by where its words stand in the sentence, never by the words.

It reads files and writes none. See docs/design/panel.md, section 7.
"""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

from burro_core.catalogue import FEATURES, TAGS
from burro_core.ids import (
    BudgetAction,
    CommuteAction,
    DirectionChoice,
    EditProvenance,
    FeatureId,
    ModeChoice,
    OpsGroup,
    SegmentChoice,
    Step,
    StrictnessChoice,
    TagId,
    Tenure,
    TenureChoice,
    TowardChoice,
    WeightAction,
)
from burro_core.ops import BudgetEdit, CommuteEdit, Operations, TagEdit, WeightEdit
from burro_core.places import resolve_place
from burro_core.rank import rank
from burro_core.reducer import apply
from burro_core.release import InMemoryRelease
from burro_core.spec import PreferenceSpec, default_spec

# How many areas of a search are shown.
FIRST: Final = 10
# What a thing that is asked for in a search weighs: what one mention is worth.
MENTION: Final = 0.5
NO_PLACE: Final = "The release names no place for the journey of this search. It is left out."
NOTHING_LEFT: Final = "Nothing this search asks for is in the release, so no area is ranked."
NOT_IN_IT: Final = "{label} is not in this release, so the search is ranked without it."


class Unfit(Exception):
    """The file of searches is not as it is read. The words say what kind of fault it was."""


@dataclass(frozen=True)
class Search:
    """One search that is ranked before and after: typed edits, and no words."""

    id: str
    name: str
    # The sentence the search was read from. Of the founder's, the case of the evaluation set.
    says: str
    read_as: str
    tenure: Tenure
    budget: Mapping[str, Any] | None
    journeys: tuple[Mapping[str, Any], ...]
    vibes: tuple[tuple[TagId, TowardChoice], ...]
    measures: tuple[tuple[FeatureId, DirectionChoice], ...]


def read_searches(path: Path, root: Path) -> tuple[Search, ...]:
    """The searches of a file. `root` is the repository, where the evaluation set is."""
    try:
        held = cast(dict[str, Any], json.loads(path.read_bytes()))
        cases = {
            case["id"]: case["text"]
            for row in (root / held["cases"]).read_text(encoding="utf-8").splitlines()
            if row.strip()
            for case in [json.loads(row)]
        }
        return tuple(
            Search(
                id=one["id"],
                name=one["name"],
                says=cases[one["case"]] if "case" in one else one["says"],
                read_as=one["read_as"],
                tenure=Tenure(one["tenure"]),
                budget=one["budget"],
                journeys=tuple(one["journeys"]),
                vibes=tuple((TagId(v["vibe"]), TowardChoice(v["toward"])) for v in one["vibes"]),
                measures=tuple(
                    (FeatureId(m["measure"]), DirectionChoice(m["way"])) for m in one["measures"]
                ),
            )
            for one in held["searches"]
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise Unfit(f"The searches cannot be read: {type(error).__name__}") from None


_UI = EditProvenance.UI_EDIT


def _firm(held: Mapping[str, Any]) -> StrictnessChoice:
    return StrictnessChoice.HARD if held["firm"] else StrictnessChoice.SOFT


def _edits(search: Search, release: InMemoryRelease) -> tuple[Operations, list[str]]:
    """A search as the edits the website would send, and what of it the release cannot hold."""
    notes: list[str] = []
    budget = search.budget
    journeys: list[CommuteEdit] = []
    for journey in search.journeys:
        start, end = journey["words"]
        place = resolve_place(search.says[start:end], release).resolved
        if place is None:
            notes.append(NO_PLACE)
            continue
        journeys.append(
            CommuteEdit(
                action=CommuteAction.ADD,
                place_id=place,
                mode=ModeChoice.PT,
                max_minutes=journey["minutes"],
                strictness=_firm(journey),
                step=Step.NONE,
                provenance=_UI,
            )
        )
    return (
        Operations(
            budget_ops=()
            if budget is None
            else (
                BudgetEdit(
                    action=BudgetAction.SET,
                    tenure=TenureChoice(search.tenure.value),
                    amount=budget["amount"],
                    segment=SegmentChoice(budget["segment"]),
                    strictness=_firm(budget),
                    step=Step.NONE,
                    provenance=_UI,
                ),
            ),
            commute_ops=tuple(journeys),
            weight_ops=tuple(
                WeightEdit(
                    action=WeightAction.SET,
                    feature_id=feature_id,
                    value=MENTION,
                    step=Step.NONE,
                    direction=way,
                    provenance=_UI,
                )
                for feature_id, way in search.measures
            ),
            tag_ops=tuple(
                TagEdit(
                    action=WeightAction.SET,
                    tag_id=tag_id,
                    value=MENTION,
                    step=Step.NONE,
                    toward=toward,
                    provenance=_UI,
                )
                for tag_id, toward in search.vibes
            ),
            area_ops=(),
            setting_ops=(),
        ),
        notes,
    )


def _asked(search: Search, edits: Operations, group: OpsGroup, index: int) -> str:
    """What an edit of a search asks for, by the name core gives it."""
    if group is OpsGroup.TAG:
        return TAGS[edits.tag_ops[index].tag_id].label
    if group is OpsGroup.WEIGHT:
        return FEATURES[edits.weight_ops[index].feature_id].short_label
    return "The budget" if group is OpsGroup.BUDGET else "The journey"


def starts_from(release: InMemoryRelease, tenure: Tenure) -> PreferenceSpec:
    """What a search starts from on a release, as the website's first search does: the
    usual settings, without any the release cannot rank on."""
    spec = default_spec(tenure)
    ranked = {metric.feature_id for metric in release.metrics if metric.rankable}
    return spec.replace(weights=tuple(w for w in spec.weights if w.feature_id in ranked))


def first_of(search: Search, release: InMemoryRelease) -> dict[str, Any]:
    """The first ten areas of a search on a release, and what of it the release cannot hold."""
    edits, notes = _edits(search, release)
    reduced = apply(starts_from(release, search.tenure), edits, release)
    notes += [
        NOT_IN_IT.format(label=_asked(search, edits, turned.group, turned.index))
        for turned in reduced.rejected
    ]
    found = rank(reduced.spec, release)
    if found.empty_spec:
        return {"first": [], "ranked": 0, "left_out": 0, "notes": [*notes, NOTHING_LEFT]}
    areas = {area.area_id: area for area in release.neighbourhoods}
    return {
        "first": [
            {
                "id": one.area_id,
                "name": areas[one.area_id].name,
                "borough": areas[one.area_id].borough,
            }
            for one in found.ranked[:FIRST]
        ],
        "ranked": len(found.ranked),
        "left_out": len(found.filtered),
        "notes": notes,
    }


def searched(
    searches: Sequence[Search], before: InMemoryRelease, after: InMemoryRelease
) -> list[dict[str, Any]]:
    """The first ten areas of each search, before and after. The sentence a search was
    read from is left out: what is given is what may be written to a file."""
    found: list[dict[str, Any]] = []
    for search in searches:
        was, now = first_of(search, before), first_of(search, after)
        found.append(
            {
                "id": search.id,
                "name": search.name,
                "read_as": search.read_as,
                "before": was,
                "after": now,
                "same": [one["id"] for one in was["first"]] == [one["id"] for one in now["first"]],
            }
        )
    return found
