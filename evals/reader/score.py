"""Score a reader of sentences against the cases in `cases/`.

A reader is anything behind `burro_core.interpret.Interpreter`: it is handed
what a person typed and the search as it stands, and answers with typed edits.
This runs one over every case, puts its edits through the reducer as the
service does, and says of each case whether it was read correctly, read in
part, declined, or REVERSED: the reader did the opposite of what was said.

It judges what happened to the search and never how the reader got there, so
the rule-based reader and a model-backed one are held to the same cases.

It prints counts, case ids, and sentences from the cases. The cases are made
up (ADR 0005), so nothing it prints is anyone's private words. It never prints
what a reader answered, and of an error only the name of its class.

Standard library and `burro_core` only. `--reader claude` loads the file
`model_reader.py` beside this one, which is the only file here that imports
the API package. `--reader nothing` and `--reader keywords` are the two
readers of `controls.py`, whose faults are known.

    uv run python evals/reader/score.py
    uv run python evals/reader/score.py --check
    uv run python evals/reader/score.py --group negatives --show all
    uv run python evals/reader/score.py --against evals/reader/baseline/rule.json
"""

import argparse
import hashlib
import importlib
import importlib.util
import json
import sys
import threading
from collections.abc import Callable, Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

from burro_core.catalogue import CATALOGUE_VERSION, default_direction
from burro_core.ids import (
    AreaAction,
    AreaRuleKind,
    BudgetAction,
    CommuteAction,
    DirectionChoice,
    EditProvenance,
    FeatureId,
    Mode,
    ModeChoice,
    Notice,
    OpsGroup,
    SegmentChoice,
    Step,
    Strictness,
    StrictnessChoice,
    TagId,
    Tenure,
    TenureChoice,
    UnmetCategory,
    WeightAction,
    segments_for,
)
from burro_core.interpret import MAX_TEXT, Interpreter, InterpretRequest
from burro_core.ops import (
    AreaEdit,
    BudgetEdit,
    CommuteEdit,
    Operations,
    TagEdit,
    WeightEdit,
)
from burro_core.rank import ENGINE_VERSION
from burro_core.reducer import apply, given_way_spec, minutes_limit
from burro_core.release import InMemoryRelease, ReleaseError, open_release
from burro_core.spec import (
    DEFAULT_COMMUTE_MINUTES,
    DEFAULT_COMMUTE_MODE,
    DEFAULT_SEGMENT,
    DEFAULT_STRICTNESS,
    PreferenceSpec,
    default_spec,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CASES = HERE / "cases"
FLOOR = HERE / "floor.json"
FIXTURES = ROOT / "data" / "fixtures" / "synthetic"
# The readers that can be asked for by one word, and where each is made.
BUILT_IN = {
    "rule": "burro_core.interpret:RuleInterpreter",
    "claude": f"{HERE / 'model_reader.py'}:build",
    "nothing": f"{HERE / 'controls.py'}:Nothing",
    "keywords": f"{HERE / 'controls.py'}:Keywords",
}
# The files whose bytes are the rule-based reader. Their hash says which reader was measured.
RULE_SOURCES = ("interpret.py", "vocabulary.py", "places.py", "reducer.py")

# The groups, in the order they are reported. A file that is not listed is reported last.
GROUPS = (
    "plain_wishes",
    "budgets",
    "journeys",
    "negatives",
    "double_negatives",
    "typos",
    "lists",
    "questions",
    "other_peoples_wishes",
    "who_lives_there",
    "crime",
    "off_topic",
    "other_languages",
    "very_long",
    "very_short",
)


class Outcome(StrEnum):
    """What became of a case, from worst to best."""

    REVERSED = "reversed"  # it did the opposite of what was said
    UNASKED = "unasked"  # it made an edit nobody asked for
    FAILED = "failed"  # the reader raised, and gave no answer
    DECLINED = "declined"  # it read nothing of what was asked
    PARTIAL = "partial"  # it read some of it
    CORRECT = "correct"


ORDER = tuple(Outcome)
COLUMNS = (Outcome.CORRECT, Outcome.PARTIAL, Outcome.DECLINED, Outcome.UNASKED, Outcome.REVERSED)
HEADINGS = {
    Outcome.CORRECT: "correct",
    Outcome.PARTIAL: "in part",
    Outcome.DECLINED: "declined",
    Outcome.UNASKED: "unasked",
    Outcome.REVERSED: "REVERSED",
    Outcome.FAILED: "failed",
}
MEANS = {
    Outcome.REVERSED: "did the opposite of what was said",
    Outcome.UNASKED: "made an edit nobody asked for",
    Outcome.FAILED: "the reader raised and gave no answer",
    Outcome.DECLINED: "read nothing of what was asked",
    Outcome.PARTIAL: "read some of what was asked",
    Outcome.CORRECT: "read correctly",
}


class Verdict(StrEnum):
    MET = "met"
    MISSED = "missed"
    WRONG = "wrong"
    UNASKED = "unasked"
    REVERSED = "reversed"


class Move(StrEnum):
    RAISED = "raised"
    LOWERED = "lowered"
    UNMOVED = "unmoved"


class CaseError(Exception):
    """A case that cannot be scored as it is written. The message names the case and the key."""


# --- The cases ------------------------------------------------------------------

COMPONENT_KEYS = ("rise", "fall", "not_rise", "not_fall", "still", "free")
ANY_KEYS = ("rise_any", "fall_any")
EXPECT_KEYS = frozenset(
    {
        *COMPONENT_KEYS,
        *ANY_KEYS,
        "journeys",
        "areas",
        "budget",
        "tenure",
        "not_tenure",
        "notice",
        "unmet",
        "ask",
    }
)
CASE_KEYS = frozenset({"id", "text", "tenure", "held", "expect", "why"})
JOURNEY_KEYS = frozenset({"add", "not_add", "remove", "may_add"})
JOURNEY_FIELDS = frozenset({"to", "mode", "max_minutes", "strictness"})
AREA_KEYS = frozenset(
    {"exclude", "only", "not_exclude", "not_only", "clear", "may_exclude", "may_only"}
)
BUDGET_KEYS = frozenset({"amount", "not_amount", "segment", "strictness", "clear", "may_set"})
# In place of a mode, a number of minutes, a segment or a strictness: whatever the reader
# chose is accepted, because the words fix none.
ANY = "any"
HELD_KEYS = frozenset({"journeys", "areas", "weights", "tags", "budget"})
NOTICES = frozenset({*(notice.value for notice in Notice), "any"})
ASKS = frozenset({"no", "ok", "must"})
_FEATURE_NAMES = frozenset(f.value for f in FeatureId)
_TAG_NAMES = frozenset(t.value for t in TagId)


@dataclass(frozen=True)
class Journey:
    place_id: str
    name: str
    mode: Mode | None = None
    max_minutes: int | None = None
    strictness: Strictness | None = None
    # The fields the words leave open, so that whatever they hold is accepted.
    free: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Expect:
    rise: tuple[str, ...] = ()
    fall: tuple[str, ...] = ()
    not_rise: tuple[str, ...] = ()
    not_fall: tuple[str, ...] = ()
    still: tuple[str, ...] = ()
    # May go either way: the words can fairly be read both ways.
    free: tuple[str, ...] = ()
    rise_any: tuple[tuple[str, ...], ...] = ()
    fall_any: tuple[tuple[str, ...], ...] = ()
    add: tuple[Journey, ...] = ()
    not_add: tuple[Journey, ...] = ()
    remove: tuple[Journey, ...] = ()
    may_add: tuple[Journey, ...] = ()
    # Each is a pair of the area's id and its name.
    exclude: tuple[tuple[str, str], ...] = ()
    only: tuple[tuple[str, str], ...] = ()
    not_exclude: tuple[tuple[str, str], ...] = ()
    not_only: tuple[tuple[str, str], ...] = ()
    clear: tuple[tuple[str, str], ...] = ()
    may_exclude: tuple[tuple[str, str], ...] = ()
    may_only: tuple[tuple[str, str], ...] = ()
    # The least and the most the amount may be, where one is expected.
    amount: tuple[int, int] | None = None
    not_amount: tuple[int, ...] = ()
    segment: str | None = None
    strictness: Strictness | None = None
    # The amount is to be taken off.
    no_amount: bool = False
    # The fields of the budget the words leave open.
    budget_free: frozenset[str] = frozenset()
    tenure: Tenure | None = None
    not_tenure: Tenure | None = None
    notice: str = Notice.NONE.value
    unmet: tuple[UnmetCategory, ...] = ()
    ask: str = "no"


@dataclass(frozen=True)
class Case:
    id: str
    group: str
    text: str
    tenure: Tenure
    start: PreferenceSpec
    expect: Expect
    why: str

    @property
    def asks(self) -> bool:
        """Whether the words ask for anything, so that to do nothing is to fall short."""
        e = self.expect
        edits = (e.rise, e.fall, e.rise_any, e.fall_any, e.add, e.remove, e.exclude, e.only)
        said = (e.clear, e.unmet, e.amount, e.segment, e.strictness, e.no_amount)
        return (
            any(edits)
            or any(said)
            or e.ask == "must"
            or e.notice not in (ANY, Notice.NONE.value)
            or e.tenure not in (None, self.start.tenure)
        )


class Names:
    """The places and areas of the release, by name and by alias, as a case writes them."""

    def __init__(self, release: InMemoryRelease) -> None:
        self.places: dict[str, list[tuple[str, str]]] = {}
        self.areas: dict[str, list[tuple[str, str]]] = {}
        for place in release.places:
            for name in (place.name, *place.aliases):
                self.places.setdefault(name.casefold(), []).append((place.place_id, place.name))
        for area in release.neighbourhoods:
            for name in (area.name, *area.aliases):
                self.areas.setdefault(name.casefold(), []).append((area.area_id, area.name))
        self.place_names = {place.place_id: place.name for place in release.places}
        self.area_names = {area.area_id: area.name for area in release.neighbourhoods}

    def place(self, name: str, where: str) -> tuple[str, str]:
        return _one(self.places.get(name.casefold(), []), name, "place", where)

    def area(self, name: str, where: str) -> tuple[str, str]:
        return _one(self.areas.get(name.casefold(), []), name, "area", where)


def _one(found: list[tuple[str, str]], name: str, kind: str, where: str) -> tuple[str, str]:
    ids = sorted(set(found))
    if len(ids) != 1:
        problem = "is not in the release" if not ids else "names more than one"
        raise CaseError(f"{where}: the {kind} {name!r} {problem}")
    return ids[0]


def _component(value: object, where: str) -> str:
    if not isinstance(value, str) or ":" not in value:
        raise CaseError(f"{where}: {value!r} is not 'feature:<id>' or 'tag:<id>'")
    kind, _, name = value.partition(":")
    known = {"feature": _FEATURE_NAMES, "tag": _TAG_NAMES}.get(kind, frozenset[str]())
    if name not in known:
        raise CaseError(f"{where}: {value!r} is not a feature or a tag of the catalogue")
    return value


def _listed(value: object, where: str) -> list[Any]:
    if not isinstance(value, list):
        raise CaseError(f"{where}: must be a list")
    return cast(list[Any], value)


def _mapped(value: object, allowed: frozenset[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CaseError(f"{where}: must be an object")
    found = cast(dict[str, Any], value)
    for key in found:
        if key not in allowed:
            raise CaseError(f"{where}: {key!r} is not a key. Known: {', '.join(sorted(allowed))}")
    return found


def _journey(value: object, names: Names, where: str) -> Journey:
    found = _mapped({"to": value} if isinstance(value, str) else value, JOURNEY_FIELDS, where)
    if not isinstance(found.get("to"), str):
        raise CaseError(f"{where}: a journey needs 'to', the name of a place")
    place_id, name = names.place(found["to"], where)
    free = frozenset(key for key in ("mode", "max_minutes", "strictness") if found.get(key) == ANY)
    given = {key: value for key, value in found.items() if key not in free}
    try:
        return Journey(
            place_id=place_id,
            name=name,
            mode=Mode(given["mode"]) if "mode" in given else None,
            max_minutes=int(given["max_minutes"]) if "max_minutes" in given else None,
            strictness=Strictness(given["strictness"]) if "strictness" in given else None,
            free=free,
        )
    except (TypeError, ValueError):
        raise CaseError(f"{where}: a mode, a number of minutes or a strictness is wrong") from None


def _amount(value: object, where: str) -> tuple[int, int]:
    if isinstance(value, bool):
        raise CaseError(f"{where}: an amount is a whole number, or a least and a most")
    if isinstance(value, int):
        return value, value
    pair = _listed(value, where)
    if len(pair) != 2 or not all(isinstance(n, int) and not isinstance(n, bool) for n in pair):
        raise CaseError(f"{where}: an amount is a whole number, or a least and a most")
    return min(pair), max(pair)


def _expect(raw: object, names: Names, where: str) -> Expect:
    found = _mapped(raw, EXPECT_KEYS, where)
    parts: dict[str, Any] = {}
    seen: dict[str, str] = {}

    def once(component: str, key: str) -> str:
        if component in seen:
            raise CaseError(f"{where}: {component} is under both {seen[component]} and {key}")
        seen[component] = key
        return component

    for key in COMPONENT_KEYS:
        listed = _listed(found.get(key, []), f"{where}.{key}")
        parts[key] = tuple(once(_component(c, f"{where}.{key}"), key) for c in listed)
    for key in ANY_KEYS:
        sets = _listed(found.get(key, []), f"{where}.{key}")
        parts[key] = tuple(
            tuple(once(_component(c, f"{where}.{key}"), key) for c in _listed(one, where))
            for one in sets
        )
        if any(len(one) < 2 for one in parts[key]):
            raise CaseError(f"{where}.{key}: each choice needs two things or more to choose from")

    journeys = _mapped(found.get("journeys", {}), JOURNEY_KEYS, f"{where}.journeys")
    for key in JOURNEY_KEYS:
        at = f"{where}.journeys.{key}"
        parts[key] = tuple(_journey(j, names, at) for j in _listed(journeys.get(key, []), at))
    areas = _mapped(found.get("areas", {}), AREA_KEYS, f"{where}.areas")
    for key in AREA_KEYS:
        at = f"{where}.areas.{key}"
        parts[key] = tuple(names.area(str(a), at) for a in _listed(areas.get(key, []), at))

    budget = _mapped(found.get("budget", {}), BUDGET_KEYS, f"{where}.budget")
    if "amount" in budget:
        parts["amount"] = _amount(budget["amount"], f"{where}.budget.amount")
    parts["not_amount"] = tuple(
        _amount(n, f"{where}.budget.not_amount")[0]
        for n in _listed(budget.get("not_amount", []), where)
    )
    free = {key for key in ("segment", "strictness") if budget.get(key) == ANY}
    if budget.get("may_set") is True:
        free |= {"amount", "segment", "strictness"}
    parts["budget_free"] = frozenset(free)
    parts["no_amount"] = budget.get("clear") is True
    try:
        if "segment" in budget and "segment" not in free:
            parts["segment"] = SegmentChoice(budget["segment"]).value
        if "strictness" in budget and "strictness" not in free:
            parts["strictness"] = Strictness(budget["strictness"])
        if "tenure" in found:
            parts["tenure"] = Tenure(found["tenure"])
        if "not_tenure" in found:
            parts["not_tenure"] = Tenure(found["not_tenure"])
        parts["unmet"] = tuple(UnmetCategory(u) for u in _listed(found.get("unmet", []), where))
    except ValueError:
        raise CaseError(
            f"{where}: a segment, strictness, tenure or unmet category is wrong"
        ) from None
    parts["notice"] = found.get("notice", Notice.NONE.value)
    parts["ask"] = found.get("ask", "no")
    if parts["notice"] not in NOTICES:
        raise CaseError(f"{where}.notice: must be one of {', '.join(sorted(NOTICES))}")
    if parts["ask"] not in ASKS:
        raise CaseError(f"{where}.ask: must be one of {', '.join(sorted(ASKS))}")
    return Expect(**parts)


_UI = EditProvenance.UI_EDIT


def _held(
    raw: object, tenure: Tenure, names: Names, release: InMemoryRelease, where: str
) -> PreferenceSpec:
    """The search a follow-up is typed into: the default, with what the case says is held."""
    spec = default_spec(tenure)
    found = _mapped(raw, HELD_KEYS, where)
    if not found:
        return spec
    journeys = tuple(_journey(j, names, where) for j in _listed(found.get("journeys", []), where))
    areas = _mapped(found.get("areas", {}), frozenset({"exclude", "only"}), f"{where}.areas")
    budget = _mapped(found.get("budget", {}), frozenset({"amount", "segment", "strictness"}), where)
    try:
        operations = Operations(
            budget_ops=(
                BudgetEdit(
                    action=BudgetAction.SET,
                    tenure=TenureChoice.UNCHANGED,
                    amount=int(budget.get("amount", 0)),
                    segment=SegmentChoice(budget.get("segment", "unchanged")),
                    strictness=StrictnessChoice(budget.get("strictness", "unchanged")),
                    step=Step.NONE,
                    provenance=_UI,
                ),
            )
            if budget
            else (),
            commute_ops=tuple(
                CommuteEdit(
                    action=CommuteAction.ADD,
                    place_id=j.place_id,
                    mode=ModeChoice(j.mode.value) if j.mode else ModeChoice.UNCHANGED,
                    max_minutes=j.max_minutes or 0,
                    strictness=StrictnessChoice(j.strictness.value)
                    if j.strictness
                    else StrictnessChoice.UNCHANGED,
                    step=Step.NONE,
                    provenance=_UI,
                )
                for j in journeys
            ),
            weight_ops=tuple(
                WeightEdit(
                    action=WeightAction.SET,
                    feature_id=FeatureId(_component(f"feature:{name}", where).partition(":")[2]),
                    value=float(value),
                    step=Step.NONE,
                    direction=DirectionChoice.DEFAULT,
                    provenance=_UI,
                )
                for name, value in _mapped(found.get("weights", {}), _FEATURE_NAMES, where).items()
            ),
            tag_ops=tuple(
                TagEdit(
                    action=WeightAction.SET,
                    tag_id=TagId(name),
                    value=float(value),
                    step=Step.NONE,
                    provenance=_UI,
                )
                for name, value in _mapped(found.get("tags", {}), _TAG_NAMES, where).items()
            ),
            area_ops=tuple(
                AreaEdit(action=action, area_id=names.area(str(a), where)[0], provenance=_UI)
                for key, action in (("exclude", AreaAction.EXCLUDE), ("only", AreaAction.ONLY))
                for a in _listed(areas.get(key, []), where)
            ),
            setting_ops=(),
        )
    except (TypeError, ValueError):
        raise CaseError(f"{where}: a value that is held is wrong") from None
    reduced = apply(spec, operations, release)
    if reduced.rejected:
        reasons = ", ".join(sorted({r.reason.value for r in reduced.rejected}))
        raise CaseError(f"{where}: the reducer turned away what is held: {reasons}")
    return reduced.spec


def load_cases(folder: Path, release: InMemoryRelease) -> tuple[list[Case], list[str]]:
    """Every case of every file in the folder, and what is wrong with any that cannot be read."""
    names = Names(release)
    cases: list[Case] = []
    problems: list[str] = []
    ids: set[str] = set()
    said: dict[tuple[str, str], str] = {}
    for path in sorted(folder.glob("*.jsonl")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            where = f"{path.name}:{number}"
            try:
                raw = _mapped(json.loads(line), CASE_KEYS, where)
                for key in ("id", "text", "tenure", "expect", "why"):
                    if key not in raw:
                        raise CaseError(f"{where}: '{key}' is missing")
                case_id, text = str(raw["id"]), raw["text"]
                where = f"{where} ({case_id})"
                if case_id in ids:
                    raise CaseError(f"{where}: the id is used twice")
                if not isinstance(text, str) or not 1 <= len(text) <= MAX_TEXT:
                    raise CaseError(f"{where}: the text must be 1 to {MAX_TEXT} characters")
                tenure = Tenure(raw["tenure"])
                if (text, tenure.value) in said and "held" not in raw:
                    raise CaseError(f"{where}: the same words as {said[(text, tenure.value)]}")
                expect = _expect(raw["expect"], names, f"{where}.expect")
                start = _held(raw.get("held", {}), tenure, names, release, f"{where}.held")
                if expect.segment and expect.segment not in {
                    s.value for s in segments_for(expect.tenure or tenure)
                }:
                    raise CaseError(f"{where}: the segment does not suit the tenure")
            except (CaseError, ValueError) as error:
                problems.append(
                    str(error) if isinstance(error, CaseError) else f"{where}: not valid"
                )
                continue
            ids.add(case_id)
            said.setdefault((text, tenure.value), case_id)
            cases.append(Case(case_id, path.stem, text, tenure, start, expect, str(raw["why"])))
    return cases, problems


# --- Judging one case -----------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    verdict: Verdict
    what: str
    # It was asked for, and is not only a thing that must be left alone.
    required: bool = False


@dataclass
class Scored:
    case: Case
    outcome: Outcome
    findings: list[Finding] = field(default_factory=list[Finding])
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    degraded: bool = False
    error: str = ""


def _weights(spec: PreferenceSpec) -> dict[str, float]:
    """Each weight of a spec, signed: above nothing where the thing is wanted, below where not.

    A feature that may be wanted either way, pubs say, counts against the thing
    when its direction is `less`. A feature with one direction counts for its
    own good end: a weight on noise is a wish for quiet.
    """
    ready = given_way_spec(spec)
    found: dict[str, float] = {}
    for weight in ready.weights:
        wanted = weight.direction is default_direction(weight.feature_id)
        found[f"feature:{weight.feature_id.value}"] = weight.weight if wanted else -weight.weight
    for tag in ready.tags:
        found[f"tag:{tag.tag_id.value}"] = tag.weight
    return found


def _lean(edit: WeightEdit | TagEdit) -> Move:
    """Which way an edit leans by itself, for one that was applied and changed nothing."""
    against = isinstance(edit, WeightEdit) and (
        edit.direction is not DirectionChoice.DEFAULT
        and edit.direction.value != default_direction(edit.feature_id).value
    )
    if edit.action is WeightAction.REMOVE:
        return Move.LOWERED
    if edit.action is WeightAction.SET:
        up = edit.value > 0 and not against
        return Move.RAISED if up else Move.LOWERED
    if edit.step in (Step.UP_SMALL, Step.UP_LARGE):
        return Move.LOWERED if against else Move.RAISED
    if edit.step in (Step.DOWN_SMALL, Step.DOWN_LARGE):
        return Move.LOWERED
    return Move.UNMOVED


def _moves(
    start: PreferenceSpec,
    final: PreferenceSpec,
    operations: Operations,
    applied: set[tuple[str, int]],
) -> dict[str, Move]:
    """Every feature and tag an applied edit names, and which way it went."""
    before, after = _weights(start), _weights(final)
    edits: dict[str, WeightEdit | TagEdit] = {}
    for index, weight in enumerate(operations.weight_ops):
        if (OpsGroup.WEIGHT.value, index) in applied:
            edits[f"feature:{weight.feature_id.value}"] = weight
    for index, tag in enumerate(operations.tag_ops):
        if (OpsGroup.TAG.value, index) in applied:
            edits[f"tag:{tag.tag_id.value}"] = tag
    moves: dict[str, Move] = {}
    for component, edit in edits.items():
        was, now = before.get(component, 0.0), after.get(component, 0.0)
        moves[component] = Move.RAISED if now > was else Move.LOWERED if now < was else _lean(edit)
    return moves


def _held_as(
    journey: Journey, case: Case, final: PreferenceSpec, release: InMemoryRelease
) -> list[Finding]:
    """A journey that is held, against what the case says of it and against what was unsaid.

    What the words did not give must be as it was before: what the search held
    for the journey, or what nobody chose, which is public transport, 45
    minutes, and not a limit. A number, a mode or a limit the words do not hold
    is an edit nobody asked for.
    """
    held = next(c for c in final.commutes if c.place_id == journey.place_id)
    was = next((c for c in case.start.commutes if c.place_id == journey.place_id), None)
    unsaid_minutes = min(DEFAULT_COMMUTE_MINUTES, minutes_limit(held.mode, release))
    checks = (
        ("mode", journey.mode, held.mode, was.mode if was else DEFAULT_COMMUTE_MODE),
        (
            "minutes",
            journey.max_minutes,
            held.max_minutes,
            was.max_minutes if was else unsaid_minutes,
        ),
        (
            "strictness",
            journey.strictness,
            held.strictness,
            was.strictness if was else DEFAULT_STRICTNESS,
        ),
    )
    findings: list[Finding] = []
    for name, wanted, got, unsaid in checks:
        about = f"the {name} of the journey to {journey.name}"
        if {name, f"max_{name}"} & journey.free:
            continue
        if wanted is None:
            if got != unsaid:
                findings.append(Finding(Verdict.UNASKED, f"{about}: set, and the words give none"))
        elif got == wanted:
            # What nobody chose is no credit to the reader, where it is what was wanted.
            findings.append(Finding(Verdict.MET, about, required=wanted != unsaid))
        elif got == unsaid:
            findings.append(Finding(Verdict.MISSED, f"{about}: not read", required=True))
        else:
            findings.append(Finding(Verdict.UNASKED, f"{about}: not what the words give"))
    return findings


def judge(case: Case, result: Any, release: InMemoryRelease, names: Names) -> list[Finding]:
    """Everything the case expects, and everything else that moved, each with a verdict."""
    expect, start = case.expect, case.start
    operations: Operations = result.operations
    reduced = apply(start, operations, release)
    final = reduced.spec
    applied = {(a.group.value, a.index) for a in reduced.applied}
    moves = _moves(start, final, operations, applied)
    findings: list[Finding] = []
    named: set[str] = set()

    def moved(component: str) -> Move:
        named.add(component)
        return moves.get(component, Move.UNMOVED)

    for component in expect.rise:
        move = moved(component)
        verdict = {Move.RAISED: Verdict.MET, Move.LOWERED: Verdict.REVERSED}.get(
            move, Verdict.MISSED
        )
        findings.append(Finding(verdict, f"{component} was to rise: {move.value}", required=True))
    for component in expect.fall:
        move = moved(component)
        verdict = {Move.LOWERED: Verdict.MET, Move.RAISED: Verdict.REVERSED}.get(
            move, Verdict.MISSED
        )
        findings.append(Finding(verdict, f"{component} was to fall: {move.value}", required=True))
    for wanted, against, choices, word in (
        (Move.RAISED, Move.LOWERED, expect.rise_any, "rise"),
        (Move.LOWERED, Move.RAISED, expect.fall_any, "fall"),
    ):
        for choice in choices:
            went = {moved(component) for component in choice}
            verdict = (
                Verdict.REVERSED
                if against in went
                else Verdict.MET
                if wanted in went
                else Verdict.MISSED
            )
            what = f"one of {', '.join(choice)} was to {word}: {verdict.value}"
            findings.append(Finding(verdict, what, required=True))
    for component in expect.not_rise:
        if moved(component) is Move.RAISED:
            findings.append(Finding(Verdict.REVERSED, f"{component} was not to rise: raised"))
    for component in expect.not_fall:
        if moved(component) is Move.LOWERED:
            findings.append(Finding(Verdict.REVERSED, f"{component} was not to fall: lowered"))
    named.update(expect.free)
    # What the case does not name was to stay as it was, as what it lists under `still` was.
    for component, move in sorted(moves.items()):
        if component not in named and move is not Move.UNMOVED:
            findings.append(Finding(Verdict.UNASKED, f"{component} was to stay: {move.value}"))

    findings += _journeys(case, result, final, release, names)
    findings += _areas(case, result, final, names)
    findings += _money(case, final)
    findings += _said_back(case, result)
    return findings


def _journeys(
    case: Case, result: Any, final: PreferenceSpec, release: InMemoryRelease, names: Names
) -> list[Finding]:
    expect = case.expect
    before = {c.place_id: c for c in case.start.commutes}
    after = {c.place_id: c for c in final.commutes}
    asked = any(c.group is OpsGroup.COMMUTE for c in result.clarify)
    findings: list[Finding] = []
    expected: set[str] = set()
    for journey in expect.may_add:
        expected.add(journey.place_id)
        if journey.place_id in after and journey.place_id not in before:
            findings += _held_as(journey, case, final, release)
    for journey in expect.add:
        expected.add(journey.place_id)
        about = f"a journey to {journey.name} was to be held"
        if journey.place_id in after:
            findings.append(Finding(Verdict.MET, about, required=journey.place_id not in before))
            findings += _held_as(journey, case, final, release)
        elif asked and expect.ask != "no":
            findings.append(Finding(Verdict.MET, f"{about}: asked about", required=True))
        else:
            findings.append(Finding(Verdict.MISSED, f"{about}: not added", required=True))
    for journey in expect.not_add:
        expected.add(journey.place_id)
        if journey.place_id in after and journey.place_id not in before:
            findings.append(
                Finding(Verdict.REVERSED, f"a journey to {journey.name} was not to be added: added")
            )
    for journey in expect.remove:
        expected.add(journey.place_id)
        gone = journey.place_id not in after
        findings.append(
            Finding(
                Verdict.MET if gone else Verdict.MISSED,
                f"the journey to {journey.name} was to be removed",
                required=True,
            )
        )
    for place_id in sorted(set(before) | set(after)):
        if place_id in expected:
            continue
        name = names.place_names.get(place_id, "a place the release does not know")
        if place_id not in before:
            findings.append(Finding(Verdict.UNASKED, f"a journey to {name} was added"))
        elif place_id not in after:
            findings.append(Finding(Verdict.UNASKED, f"the journey to {name} was removed"))
        elif before[place_id] != after[place_id]:
            findings.append(Finding(Verdict.UNASKED, f"the journey to {name} was changed"))
    return findings


def _areas(case: Case, result: Any, final: PreferenceSpec, names: Names) -> list[Finding]:
    expect = case.expect
    before = {a.area_id: a.rule for a in case.start.areas}
    after = {a.area_id: a.rule for a in final.areas}
    asked = expect.ask != "no" and any(c.group is OpsGroup.AREA for c in result.clarify)
    findings: list[Finding] = []
    expected: set[str] = set()
    for allowed, listed in (
        (AreaRuleKind.EXCLUDE, expect.may_exclude),
        (AreaRuleKind.ONLY, expect.may_only),
    ):
        for area_id, _ in listed:
            if after.get(area_id) in (allowed, before.get(area_id)):
                expected.add(area_id)
    for wanted, other, listed in (
        (AreaRuleKind.EXCLUDE, AreaRuleKind.ONLY, expect.exclude),
        (AreaRuleKind.ONLY, AreaRuleKind.EXCLUDE, expect.only),
    ):
        for area_id, name in listed:
            expected.add(area_id)
            got = after.get(area_id)
            verdict = (
                Verdict.MET
                if got is wanted or (got is None and asked)
                else Verdict.REVERSED
                if got is other and before.get(area_id) is not other
                else Verdict.MISSED
            )
            findings.append(
                Finding(verdict, f"the rule {wanted.value} {name}: {verdict.value}", required=True)
            )
    for unwanted, listed in (
        (AreaRuleKind.EXCLUDE, expect.not_exclude),
        (AreaRuleKind.ONLY, expect.not_only),
    ):
        for area_id, name in listed:
            if after.get(area_id) is unwanted and before.get(area_id) is not unwanted:
                expected.add(area_id)
                findings.append(
                    Finding(Verdict.REVERSED, f"the rule {unwanted.value} {name} was made")
                )
    for area_id, name in expect.clear:
        expected.add(area_id)
        gone = area_id not in after
        findings.append(
            Finding(
                Verdict.MET if gone else Verdict.MISSED,
                f"the rule for {name} was to be cleared",
                required=True,
            )
        )
    for area_id in sorted(set(before) | set(after)):
        if area_id in expected or before.get(area_id) is after.get(area_id):
            continue
        name = names.area_names.get(area_id, "an area the release does not know")
        rule = after.get(area_id)
        what = (
            f"the rule {rule.value} {name} was made" if rule else f"the rule for {name} was cleared"
        )
        findings.append(Finding(Verdict.UNASKED, what))
    return findings


def _money(case: Case, final: PreferenceSpec) -> list[Finding]:
    """The tenure, the budget and the settings: what was expected, and what else moved."""
    expect, start = case.expect, case.start
    findings: list[Finding] = []
    switched = final.tenure is not start.tenure
    if expect.not_tenure is not None and switched and final.tenure is expect.not_tenure:
        findings.append(Finding(Verdict.REVERSED, f"the search was moved to {final.tenure.value}"))
    elif expect.tenure is not None:
        right = final.tenure is expect.tenure
        if right or not switched:
            findings.append(
                Finding(
                    Verdict.MET if right else Verdict.MISSED,
                    f"the tenure was to be {expect.tenure.value}",
                    required=start.tenure is not expect.tenure,
                )
            )
        else:
            findings.append(
                Finding(Verdict.REVERSED, f"the search was moved to {final.tenure.value}")
            )
    elif switched:
        findings.append(Finding(Verdict.UNASKED, f"the search was moved to {final.tenure.value}"))

    # What the budget holds where nobody has said anything, after a change of tenure or none.
    unsaid_amount = None if switched else start.budget.amount
    unsaid_segment = DEFAULT_SEGMENT[final.tenure] if switched else start.budget.segment
    unsaid_strictness = DEFAULT_STRICTNESS if switched else start.budget.strictness
    amount = final.budget.amount
    if expect.no_amount:
        findings.append(
            Finding(
                Verdict.MET if amount is None else Verdict.MISSED,
                "the budget's amount was to be taken off",
                required=True,
            )
        )
    elif expect.amount is not None:
        least, most = expect.amount
        if amount is not None and least <= amount <= most:
            findings.append(Finding(Verdict.MET, "the budget's amount", required=True))
        elif amount is not None and amount in expect.not_amount:
            findings.append(
                Finding(Verdict.REVERSED, "the budget is the amount that was turned down")
            )
        elif amount == unsaid_amount:
            findings.append(Finding(Verdict.MISSED, "the budget's amount: not read", required=True))
        else:
            findings.append(Finding(Verdict.UNASKED, "the budget is not the amount the words give"))
    elif amount is not None and amount in expect.not_amount:
        findings.append(Finding(Verdict.REVERSED, "the budget is the amount that was turned down"))
    elif amount != unsaid_amount and "amount" not in expect.budget_free:
        findings.append(Finding(Verdict.UNASKED, "the budget's amount was changed"))

    for name, wanted, got, unsaid in (
        ("segment", expect.segment, final.budget.segment.value, unsaid_segment.value),
        ("strictness", expect.strictness, final.budget.strictness, unsaid_strictness),
    ):
        about = f"the budget's {name}"
        if name in expect.budget_free:
            continue
        if wanted is None:
            if got != unsaid:
                findings.append(Finding(Verdict.UNASKED, f"{about} was changed"))
        elif got == wanted:
            findings.append(Finding(Verdict.MET, about, required=wanted != unsaid))
        elif got == unsaid:
            findings.append(Finding(Verdict.MISSED, f"{about}: not read", required=True))
        else:
            findings.append(Finding(Verdict.UNASKED, f"{about}: not what the words give"))

    settings = (
        ("how journeys are combined", start.commute_combine, final.commute_combine),
        ("which public transport time is scored", start.pt_basis, final.pt_basis),
        ("how much the journey counts", start.commute_weight, final.commute_weight),
        ("how much the budget counts", start.budget.weight, final.budget.weight),
    )
    for about, was, now in settings:
        if was != now and not switched:
            findings.append(Finding(Verdict.UNASKED, f"{about} was changed"))
    return findings


def _said_back(case: Case, result: Any) -> list[Finding]:
    """The notice, what was reported as unmet, and whether a question was asked."""
    expect = case.expect
    findings: list[Finding] = []
    notice = result.notice.value
    if expect.notice not in ("any", Notice.NONE.value):
        given = notice == expect.notice
        findings.append(
            Finding(
                Verdict.MET if given else Verdict.MISSED,
                f"the notice {expect.notice} was to be given",
                required=True,
            )
        )
    elif expect.notice == Notice.NONE.value and notice != Notice.NONE.value:
        findings.append(
            Finding(Verdict.WRONG, f"the notice {notice} was given, and none was called for")
        )
    unmet = set(result.unmet)
    for category in expect.unmet:
        findings.append(
            Finding(
                Verdict.MET if category in unmet else Verdict.MISSED,
                f"{category.value} was to be reported as unmet",
                required=True,
            )
        )
    asked = bool(result.clarify)
    if expect.ask == "must":
        findings.append(
            Finding(
                Verdict.MET if asked else Verdict.MISSED,
                "a question was to be asked",
                required=True,
            )
        )
    elif expect.ask == "no" and asked:
        findings.append(
            Finding(Verdict.WRONG, "a question was asked, and the words left none open")
        )
    return findings


def outcome_of(findings: Sequence[Finding]) -> Outcome:
    verdicts = {finding.verdict for finding in findings}
    if Verdict.REVERSED in verdicts:
        return Outcome.REVERSED
    if Verdict.UNASKED in verdicts:
        return Outcome.UNASKED
    if not verdicts & {Verdict.MISSED, Verdict.WRONG}:
        return Outcome.CORRECT
    required = [finding for finding in findings if finding.required]
    if required and not any(finding.verdict is Verdict.MET for finding in required):
        return Outcome.DECLINED
    return Outcome.PARTIAL


def score(case: Case, reader: Interpreter, release: InMemoryRelease, names: Names) -> Scored:
    request = InterpretRequest(text=case.text, spec=case.start, release=release)
    try:
        result = reader.interpret(request)
    except Exception as error:
        # The name of the class and no more: a message may hold what was typed.
        return Scored(case, Outcome.FAILED, error=type(error).__name__)
    findings = judge(case, result, release, names)
    return Scored(
        case,
        outcome_of(findings),
        findings,
        input_tokens=result.usage.input_tokens,
        output_tokens=result.usage.output_tokens,
        cache_read_tokens=result.usage.cache_read_tokens,
        degraded=bool(result.degraded),
    )


# --- The reader and the release -------------------------------------------------


def load_release(folder: Path | None) -> InMemoryRelease:
    if folder is None:
        found = sorted(p for p in FIXTURES.iterdir() if p.is_dir()) if FIXTURES.is_dir() else []
        if not found:
            raise SystemExit(f"no release under {FIXTURES.relative_to(ROOT)}. Pass --release")
        folder = found[-1]
    files = {p.name: p.read_bytes() for p in sorted(folder.iterdir()) if p.name != ".DS_Store"}
    try:
        return open_release(folder.resolve().name, files)
    except ReleaseError as error:
        raise SystemExit(f"the release was refused: {error}") from None


def load_reader(named: str) -> Callable[[], Interpreter]:
    """A way to make the reader, so that each worker has one of its own.

    `rule` is the rule-based reader. `claude`, `nothing` and `keywords` are in
    the files beside this one. Anything else is `module:name` or
    `path/to/file.py:name`, where the name is a reader or something that makes
    one when it is called with nothing.
    """
    where, _, name = BUILT_IN.get(named, named).rpartition(":")
    if not where or not name:
        raise SystemExit(f"--reader is one of {', '.join(BUILT_IN)}, or module:name")
    if where.endswith(".py"):
        spec = importlib.util.spec_from_file_location(Path(where).stem, where)
        if spec is None or spec.loader is None:
            raise SystemExit(f"{where} cannot be loaded")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        module = importlib.import_module(where)
    made = getattr(module, name)
    # A class, or anything else that is called to make a reader, is called by each worker.
    if isinstance(made, type) or not hasattr(made, "interpret"):
        return cast(Callable[[], Interpreter], made)
    return lambda: cast(Interpreter, made)


def source_hash() -> str:
    """One hash of the files that are the rule-based reader, to say which one was measured."""
    folder = ROOT / "packages" / "core" / "src" / "burro_core"
    digest = hashlib.sha256()
    for name in RULE_SOURCES:
        digest.update(name.encode())
        digest.update((folder / name).read_bytes())
    return digest.hexdigest()[:12]


def run(
    cases: Sequence[Case], make: Callable[[], Interpreter], release: InMemoryRelease, workers: int
) -> list[Scored]:
    names = Names(release)
    local = threading.local()

    def one(case: Case) -> Scored:
        if not hasattr(local, "reader"):
            local.reader = make()
        return score(case, local.reader, release, names)

    if workers <= 1:
        return [one(case) for case in cases]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(one, cases))


# --- The report -----------------------------------------------------------------


def _share(part: int, whole: int) -> float:
    return part / whole if whole else 0.0


def _in_order(groups: Iterable[str]) -> list[str]:
    found = set(groups)
    return [g for g in GROUPS if g in found] + sorted(found - set(GROUPS))


def _rows(scored: Sequence[Scored]) -> list[tuple[str, dict[Outcome, int], int]]:
    rows: list[tuple[str, dict[Outcome, int], int]] = []
    for group in [*_in_order(s.case.group for s in scored), "all"]:
        among = [s for s in scored if group in (s.case.group, "all")]
        counts = {outcome: sum(s.outcome is outcome for s in among) for outcome in Outcome}
        rows.append((group.replace("_", " "), counts, len(among)))
    return rows


def table(scored: Sequence[Scored], markdown: bool = False) -> str:
    rows = _rows(scored)
    failed = any(counts[Outcome.FAILED] for _, counts, _ in rows)
    columns = (*COLUMNS, *((Outcome.FAILED,) if failed else ()))
    head = ["group", "cases", *(HEADINGS[c] for c in columns), "correct share"]
    body = [
        [
            name,
            str(total),
            *(str(counts[c]) for c in columns),
            f"{_share(counts[Outcome.CORRECT], total):.0%}",
        ]
        for name, counts, total in rows
    ]
    if markdown:
        lines = ["| " + " | ".join(head) + " |", "|---|" + "---:|" * (len(head) - 1)]
        lines += ["| " + " | ".join(row) + " |" for row in body]
        return "\n".join(lines)
    widths = [max(len(row[i]) for row in [head, *body]) for i in range(len(head))]
    lines: list[str] = []
    for row in [head, *body]:
        rest = (c.rjust(w) for c, w in zip(row[1:], widths[1:], strict=True))
        lines.append("  ".join([row[0].ljust(widths[0]), *rest]))
        if row is head or row is body[-2]:
            lines.append("  ".join("-" * w for w in widths))
    return "\n".join(lines)


def asked_and_not(scored: Sequence[Scored]) -> str:
    """The correct share, apart for the cases that ask for something and those that do not.

    A reader that does nothing is right about every case that asks for nothing,
    so one share for the whole set flatters it.
    """
    lines: list[str] = []
    for asks, what in ((True, "ask for something"), (False, "are right to leave alone")):
        among = [s for s in scored if s.case.asks is asks]
        right = sum(s.outcome is Outcome.CORRECT for s in among)
        lines.append(
            f"{len(among)} cases {what}: {right} correct ({_share(right, len(among)):.0%})"
        )
    return "\n".join(lines)


def listing(scored: Sequence[Scored], outcome: Outcome, markdown: bool = False) -> str:
    """Every case with this outcome: its id, its tenure, its sentence, and what went wrong."""
    among = [s for s in scored if s.outcome is outcome]
    if not among:
        return ""
    lines = [f"{HEADINGS[outcome]}: {MEANS[outcome]} ({len(among)})"]
    for s in among:
        text = " ".join(s.case.text.split())
        told = [
            f.what
            for f in s.findings
            if f.verdict in (Verdict.REVERSED, Verdict.UNASKED, Verdict.MISSED, Verdict.WRONG)
        ]
        if s.error:
            told = [f"raised {s.error}"]
        if markdown:
            lines.append(f"- `{s.case.id}` ({s.case.tenure.value}) {text}: {'; '.join(told)}")
        else:
            lines.append(f"  [{s.case.id}] ({s.case.tenure.value}) {text}")
            lines += [f"      {what}" for what in told]
    return "\n".join(lines)


def gate(scored: Sequence[Scored], floor: Mapping[str, Any], key: str) -> list[str]:
    """Why the run fails, one line for each reason. Empty where it passes."""
    total = len(scored)
    count = {outcome: sum(s.outcome is outcome for s in scored) for outcome in Outcome}
    reasons: list[str] = []
    if count[Outcome.REVERSED]:
        reasons.append(f"{count[Outcome.REVERSED]} reversed: none is allowed")
    held = floor.get(key)
    if not isinstance(held, dict):
        reasons.append(f"floor.json holds no floor for the reader {key!r}")
        return reasons
    limits = cast(dict[str, Any], held)
    least = limits.get("correct_share")
    share = _share(count[Outcome.CORRECT], total)
    if isinstance(least, (int, float)) and share < float(least):
        reasons.append(f"correct share {share:.3f} is below the floor of {float(least):.3f}")
    most = limits.get("unasked_ceiling")
    if isinstance(most, int) and count[Outcome.UNASKED] > most:
        reasons.append(f"{count[Outcome.UNASKED]} unasked is above the ceiling of {most}")
    groups = limits.get("groups")
    floors = cast(dict[str, Any], groups) if isinstance(groups, dict) else {}
    for name, counts, size in _rows(scored)[:-1]:
        group_floor = floors.get(name.replace(" ", "_"))
        group_share = _share(counts[Outcome.CORRECT], size)
        if isinstance(group_floor, (int, float)) and group_share < float(group_floor):
            reasons.append(
                f"{name}: correct share {group_share:.3f} is below "
                f"its floor of {float(group_floor):.3f}"
            )
    return reasons


def against(scored: Sequence[Scored], earlier: Mapping[str, Any]) -> str:
    """The cases whose outcome is not what an earlier run gave, worse first."""
    before = cast(dict[str, str], earlier.get("outcomes", {}))
    rank = {outcome.value: place for place, outcome in enumerate(ORDER)}
    worse: list[str] = []
    better: list[str] = []
    new = 0
    for s in scored:
        was = before.get(s.case.id)
        if was is None or was not in rank:
            new += 1
        elif rank[s.outcome.value] < rank[was]:
            worse.append(
                f"  [{s.case.id}] {was} -> {s.outcome.value}: {' '.join(s.case.text.split())}"
            )
        elif rank[s.outcome.value] > rank[was]:
            better.append(
                f"  [{s.case.id}] {was} -> {s.outcome.value}: {' '.join(s.case.text.split())}"
            )
    gone = len(set(before) - {s.case.id for s in scored})
    lines = [
        f"against the earlier run ({earlier.get('reader', '?')}, "
        f"engine {earlier.get('engine_version', '?')}, reader {earlier.get('rule_sources', '?')}): "
        f"{len(worse)} worse, {len(better)} better, {new} new, {gone} no longer run"
    ]
    if worse:
        lines += ["worse:", *worse]
    if better:
        lines += ["better:", *better]
    return "\n".join(lines)


def saved(scored: Sequence[Scored], key: str, release: InMemoryRelease) -> dict[str, Any]:
    return {
        "reader": key,
        "engine_version": ENGINE_VERSION,
        "catalogue_version": CATALOGUE_VERSION,
        "release_id": release.manifest.release_id,
        "rule_sources": source_hash(),
        "cases": len(scored),
        "counts": {o.value: sum(s.outcome is o for s in scored) for o in Outcome},
        "outcomes": {s.case.id: s.outcome.value for s in sorted(scored, key=lambda s: s.case.id)},
    }


def _arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score a reader of sentences against the cases.")
    parser.add_argument("--reader", default="rule", help=f"{', '.join(BUILT_IN)}, or module:name")
    parser.add_argument("--cases", type=Path, default=CASES, help="the folder of .jsonl files")
    parser.add_argument(
        "--release", type=Path, help="a release folder. The synthetic one if left out"
    )
    parser.add_argument("--floor", type=Path, default=FLOOR, help="the file of floors")
    parser.add_argument(
        "--floor-key", help="which floor to hold the run to. The reader's name if left out"
    )
    parser.add_argument(
        "--group", action="append", default=[], help="score this group only. Repeatable"
    )
    parser.add_argument(
        "--case", action="append", default=[], help="score this case only. Repeatable"
    )
    parser.add_argument(
        "--show",
        action="append",
        default=[],
        choices=[*(o.value for o in Outcome), "all"],
        help="list the cases with this outcome too. Reversed and unasked are always listed",
    )
    parser.add_argument("--workers", type=int, default=1, help="how many cases to read at once")
    parser.add_argument("--check", action="store_true", help="check the cases and run no reader")
    parser.add_argument("--markdown", action="store_true", help="write the report as Markdown")
    parser.add_argument("--save", type=Path, help="write the outcome of every case to this file")
    parser.add_argument("--against", type=Path, help="compare with a file that --save wrote")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _arguments(argv)
    out = sys.stdout.write
    release = load_release(args.release)
    cases, problems = load_cases(args.cases, release)
    for problem in problems:
        out(f"bad case: {problem}\n")
    if problems:
        out(f"{len(problems)} cases cannot be scored as they are written\n")
        return 2
    sizes = {
        group: sum(c.group == group for c in cases) for group in _in_order(c.group for c in cases)
    }
    if args.check:
        for group, size in sizes.items():
            out(f"{group.replace('_', ' '):<22}{size:>5}\n")
        out(f"{'all':<22}{len(cases):>5}\n")
        return 0
    chosen = [
        c
        for c in cases
        if (not args.group or c.group in args.group) and (not args.case or c.id in args.case)
    ]
    if not chosen:
        out("no case was chosen\n")
        return 2

    make = load_reader(args.reader)
    # A reader of this folder is known by the name it was asked for by. Any other
    # is known by the name it gives itself.
    own = args.reader in BUILT_IN
    key = args.floor_key or (args.reader if own else str(getattr(make().name, "value", "")))
    scored = run(chosen, make, release, args.workers)

    rule = f"   rule reader {source_hash()}" if key == "rule" else ""
    out(
        f"reader {key}   engine {ENGINE_VERSION}   catalogue {CATALOGUE_VERSION}   "
        f"release {release.manifest.release_id}   cases {len(scored)}{rule}\n\n"
    )
    out(table(scored, args.markdown) + "\n\n" + asked_and_not(scored) + "\n")
    shown = [Outcome.REVERSED, Outcome.UNASKED, Outcome.FAILED]
    shown += [
        o
        for o in (Outcome.DECLINED, Outcome.PARTIAL, Outcome.CORRECT)
        if {o.value, "all"} & set(args.show)
    ]
    for outcome in shown:
        found = listing(scored, outcome, args.markdown)
        if found:
            out("\n" + found + "\n")

    tokens = [
        sum(getattr(s, name) for s in scored)
        for name in ("input_tokens", "output_tokens", "cache_read_tokens")
    ]
    if any(tokens):
        out(f"\ntokens: {tokens[0]} in, {tokens[1]} out, {tokens[2]} read from the cache\n")
    degraded = sum(s.degraded for s in scored)
    if degraded:
        out(f"{degraded} answers were marked degraded: another reader answered in its place\n")
    if args.against:
        out("\n" + against(scored, json.loads(args.against.read_text(encoding="utf-8"))) + "\n")
    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(saved(scored, key, release), indent=1, sort_keys=True)
        args.save.write_text(text + "\n", encoding="utf-8")

    if args.group or args.case:
        out("\nonly part of the set was run, so it is held to no floor\n")
        return 1 if any(s.outcome is Outcome.REVERSED for s in scored) else 0
    floor: dict[str, Any] = {}
    if args.floor.is_file():
        floor = json.loads(args.floor.read_text(encoding="utf-8"))
    reasons = gate(scored, floor, key)
    out("\n" + ("\n".join(f"FAIL: {reason}" for reason in reasons) if reasons else "PASS") + "\n")
    return 1 if reasons else 0


if __name__ == "__main__":
    sys.exit(main())
