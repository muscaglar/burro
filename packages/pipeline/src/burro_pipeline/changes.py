"""The file of changes: what a person decided at the panel, one line for each change.

A person looks through what Burro presents at the panel of the review desk, and
renames it or adjusts how it is worked out. Nothing they do there changes what
is served. Each change is a line of a plain file, and a build that is given the
file applies the lines that stand. With no file a build is what it was.

A line says who made the change, the day, what stood before, what stands now,
and why in the person's words. It is written as it may be committed: it says
the day and never the hour, and the reviewer by a label and never by a name. A
line is never changed and never removed. To take a change back is a line too.

| Field | Holds |
|---|---|
| `n` | The number of the line in its file, from 1 |
| `on`, `by` | The day. The reviewer, `r1` to `r99`: `r1` is the founder |
| `what` | The kind of change: a value of `What` |
| `of` | What is changed: the id of a vibe, a measure, a chain or a number, or what is flagged |
| `was`, `now` | What stood before, and what stands now. A flag holds neither |
| `why` | The reason: one line of plain text, of 500 characters at most, and never empty |
| `takes_back` | Of a taking back, the number of the line it takes back. Of any other, null |

**No figure of a place is ever in the file.** A figure is a publisher's. A person
flags one, or leaves one out of a build, and the line names the figure by its area
and its measure.

This module is the one reader of the file. The panel writes a line with `line`,
and reads the file with `read`, as a build does. It reads bytes and opens no file.
A refusal names the line by its number and the rule by its name, and never
repeats what a line holds: a reason is a person's words.

See docs/design/panel.md and docs/adr/0029.
"""

import hashlib
import json
import re
import unicodedata
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import date
from enum import StrEnum
from typing import Any, Final, cast

from burro_core.catalogue import FEATURES, TAGS, Tag
from burro_core.ids import AREA_ID_PATTERN, FeatureId, TagId, Tenure, segments_for
from burro_core.release import (
    Metric,
    name_is_plain,
    what_a_measure_breaks,
    what_a_vibe_breaks,
    what_labels_break,
)
from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr, ValidationError

from burro_pipeline.derive import brand_table
from burro_pipeline.derive.brand_table import Chain, Table, TableError
from burro_pipeline.evidence.lock import InputKind, LockedInput

FIELDS: Final = ("n", "on", "by", "what", "of", "was", "now", "why", "takes_back")
REVIEWER: Final = re.compile(r"r[1-9][0-9]?")
FOUNDER: Final = "r1"
DAY: Final = re.compile(r"\d{4}-\d{2}-\d{2}")
WHY_LIMIT: Final = 500
# What a reason may not hold, by the category Unicode gives a character: a control, a
# mark that is not seen, and the end of a line or of a paragraph.
NOT_PLAIN: Final = frozenset({"Cc", "Cf", "Zl", "Zp"})
KEY: Final = re.compile(r"[a-z][a-z0-9]*(_[a-z0-9]+)*")
AREA: Final = re.compile(AREA_ID_PATTERN)


class What(StrEnum):
    """The kinds of line."""

    RECIPE = "recipe"  # the hundredths of the parts of a vibe
    NAME = "name"  # the name of a vibe, and of each of its ends
    CANNOT_SEE = "cannot_see"  # what a vibe cannot see, after the line every vibe says first
    LABEL = "label"  # the label of a measure, and its short label
    BRAND = "brand"  # a row of the table of tiers: moved, added or taken out
    NUMBER = "number"  # a number a person set by judgement
    FLAG = "flag"  # something for a person to look at again. A build does nothing with it
    LEAVE_OUT = "leave_out"  # a figure that is left out of a build
    TAKE_BACK = "take_back"  # takes an earlier line back


# What may be flagged, and which of them is a figure that a build can leave out.
FIGURE, BAND, NAMED, BORDER = "figure", "band", "name", "border"
FLAGGED: Final = (FIGURE, BAND, NAMED, BORDER)
# The numbers a person set by judgement that a line may change. docs/design/panel.md,
# section 6, says where each is and how a change of it reaches a release.
FEWEST_SALES: Final = "fewest_sales"
NUMBERS: Final = frozenset({FEWEST_SALES})
# The fields of a row of the table of tiers that a line holds.
ROW: Final = frozenset({"name", "kind", "tier", "wikidata", "spellings"})
NAMES: Final = frozenset({"label", "low_end", "high_end"})
LABELS: Final = frozenset({"label", "short_label"})


class ChangesError(ValueError):
    """The file of changes cannot be built on. It names a line and a rule, and no value."""

    def __init__(self, line: int, rule: str) -> None:
        super().__init__(f"line {line} of the file of changes is refused [{rule}]")
        self.line, self.rule = line, rule


class Change(BaseModel):
    """One line of the file. `read` and `line` hold it to the rules: the record alone does not."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    n: StrictInt
    on: StrictStr
    by: StrictStr
    what: What
    of: StrictStr
    was: Any
    now: Any
    why: StrictStr
    takes_back: StrictInt | None

    @property
    def key(self) -> tuple[What, str]:
        """What a line is of. One line stands for each."""
        return self.what, self.of


def plain(text: str) -> bool:
    """Whether a text is one line of plain words, in whatever language."""
    return not any(unicodedata.category(each) in NOT_PLAIN for each in text)


def _a_day(text: str) -> bool:
    if not DAY.fullmatch(text):
        return False
    try:
        date.fromisoformat(text)
    except ValueError:
        return False
    return True


def _whole(value: object) -> bool:
    # True is no number here, though Python counts it as one.
    return type(value) is int


def _words(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and plain(value)


def _list_of_words(value: object) -> bool:
    return isinstance(value, list) and all(_words(each) for each in cast(list[object], value))


def _a_recipe(value: object) -> bool:
    held = cast(dict[object, object], value) if isinstance(value, dict) else None
    return bool(held) and all(
        isinstance(part, str) and part in FeatureId and _whole(share)
        for part, share in (held or {}).items()
    )


def _parts(recipe: object) -> dict[str, int]:
    """The parts of a recipe as a line holds it, each with its hundredths."""
    return cast(dict[str, int], recipe) if isinstance(recipe, dict) else {}


def _names(value: object) -> bool:
    held = cast(dict[str, object], value) if isinstance(value, dict) else {}
    ends = (held.get("low_end"), held.get("high_end"))
    return (
        frozenset(held) == NAMES
        and _words(held["label"])
        and all(end is None or _words(end) for end in ends)
    )


def _labels(value: object) -> bool:
    held = cast(dict[str, object], value) if isinstance(value, dict) else {}
    return frozenset(held) == LABELS and all(_words(each) for each in held.values())


def _a_row(value: object) -> bool:
    if value is None:
        return True
    held = cast(dict[str, object], value) if isinstance(value, dict) else {}
    return (
        frozenset(held) == ROW
        and all(_words(held[name]) for name in ("name", "kind", "tier"))
        and all(_list_of_words(held[name]) for name in ("wikidata", "spellings"))
    )


def _a_number(value: object) -> bool:
    return type(value) in (int, float) and value == value and abs(cast(float, value)) < 1e9


def _nothing(value: object) -> bool:
    return value is None


# What `was` and `now` hold, by the kind of line.
SHAPES: Final[Mapping[What, Callable[[object], bool]]] = {
    What.RECIPE: _a_recipe,
    What.NAME: _names,
    What.CANNOT_SEE: _list_of_words,
    What.LABEL: _labels,
    What.BRAND: _a_row,
    What.NUMBER: _a_number,
    What.FLAG: _nothing,
    What.LEAVE_OUT: _nothing,
    What.TAKE_BACK: _nothing,
}


def flagged(of: str) -> tuple[str, str, str] | None:
    """What a flag is of: the kind of thing, the area, and the measure or the vibe.

    A figure is of a measure, or of what a kind of home sells for. A band is of
    a vibe. A name and a border are of the area alone. None where it is of nothing.
    """
    kind, _, rest = of.partition("/")
    area, _, key = rest.partition("/")
    if kind not in FLAGGED or not AREA.fullmatch(area):
        return None
    costs = {f"{tenure}.{segment}" for tenure in Tenure for segment in segments_for(tenure)}
    fits = {
        FIGURE: key in FeatureId or key in costs,
        BAND: key in TagId,
        NAMED: key == "" and rest == area,
        BORDER: key == "" and rest == area,
    }
    return (kind, area, key) if fits[kind] else None


def _names_what_it_changes(what: What, of: str) -> bool:
    if what in (What.RECIPE, What.NAME, What.CANNOT_SEE):
        return of in TagId and TagId(of) in TAGS
    if what is What.LABEL:
        return of in FeatureId and FeatureId(of) in FEATURES
    if what is What.BRAND:
        return KEY.fullmatch(of) is not None
    if what is What.NUMBER:
        return of in NUMBERS
    return True


def broken(change: Change) -> str | None:
    """The rule a line breaks by itself, whatever stands before it. None where it breaks none."""
    if change.n < 1:
        return "lines_are_numbered_in_order"
    if not _a_day(change.on):
        return "line_says_the_day"
    if not REVIEWER.fullmatch(change.by):
        return "reviewer_is_a_label"
    if not (0 < len(change.why) <= WHY_LIMIT and change.why.strip() and plain(change.why)):
        return "line_gives_its_reason"
    if (change.what is What.TAKE_BACK) != (change.takes_back is not None):
        return "only_a_taking_back_names_a_line"
    if change.what in (What.FLAG, What.LEAVE_OUT):
        found = flagged(change.of)
        if found is None:
            return "flag_names_a_thing"
        if change.was is not None or change.now is not None:
            return "flag_holds_no_figure"
        if change.what is What.LEAVE_OUT and not (found[0] == FIGURE and found[2] in FeatureId):
            return "only_a_figure_is_left_out"
    if not _names_what_it_changes(change.what, change.of):
        return "change_names_what_it_changes"
    fits = SHAPES[change.what]
    if not (fits(change.was) and fits(change.now)):
        return "change_is_of_its_kind"
    if change.what is What.RECIPE and set(_parts(change.was)) != set(_parts(change.now)):
        return "change_is_of_its_kind"
    if change.what is What.BRAND and change.was is None and change.now is None:
        return "change_is_of_its_kind"
    return None


def line(change: Change) -> bytes:
    """A line as it is written: one line of JSON, its fields in a fixed order."""
    rule = broken(change)
    if rule is not None:
        raise ChangesError(change.n, rule)
    held = {name: getattr(change, name) for name in FIELDS}
    held["what"] = change.what.value
    written = json.dumps(held, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return written.encode("utf-8") + b"\n"


def _refuse(_: str) -> Any:
    raise ValueError


def _once(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """What a line holds, where it writes each field once. A field that is written twice
    says one thing to a person who reads the file and another to a build."""
    held = dict(pairs)
    if len(held) != len(pairs):
        raise ValueError
    return held


def _parsed(row: bytes, at: int) -> Change:
    try:
        held = cast(
            object,
            json.loads(row.decode("utf-8"), parse_constant=_refuse, object_pairs_hook=_once),
        )
        return Change.model_validate(held)
    except (UnicodeDecodeError, ValueError, RecursionError, ValidationError):
        raise ChangesError(at, "line_is_a_line") from None


def read(data: bytes) -> tuple[Change, ...]:
    """Every line of a file of changes, in order. `ChangesError` for a file that is not one.

    A build applies a file whole or not at all. So one line that cannot be read
    refuses the file, half a line at its end included.
    """
    rows = data.split(b"\n")
    if rows[-1:] == [b""]:
        rows = rows[:-1]
    found: list[Change] = []
    for at, row in enumerate(rows, start=1):
        change = _parsed(row, at)
        rule = broken(change)
        if rule is None and change.n != at:
            rule = "lines_are_numbered_in_order"
        if rule is None and found and change.by != found[0].by:
            rule = "file_is_of_one_reviewer"
        if rule is None and change.takes_back is not None:
            named = found[change.takes_back - 1] if 0 < change.takes_back < at else None
            if named is None or named.of != change.of:
                rule = "taking_back_names_a_line"
        if rule is not None:
            raise ChangesError(at, rule)
        found.append(change)
    return tuple(found)


def taken_back(changes: Iterable[Change]) -> frozenset[int]:
    """The numbers of the lines that a later line takes back.

    A taking back that is itself taken back takes nothing back: the line it
    named stands again.
    """
    ordered = sorted(changes, key=lambda change: change.n)
    gone: set[int] = set()
    for change in reversed(ordered):
        if change.takes_back is not None and change.n not in gone:
            gone.add(change.takes_back)
    return frozenset(gone)


def standing(changes: Sequence[Change]) -> tuple[Change, ...]:
    """The lines that stand: for each thing, the last line that no later line takes back.

    They are in the order they were written. A taking back is never among them.
    """
    gone = taken_back(changes)
    last: dict[tuple[What, str], Change] = {}
    for change in sorted(changes, key=lambda change: change.n):
        if change.n not in gone and change.what is not What.TAKE_BACK:
            last[change.key] = change
    return tuple(sorted(last.values(), key=lambda change: change.n))


# What a build makes of the lines that stand. Each is laid over core's own, and held to
# the rules core holds a release to, so that a change that cannot be served stops the build
# and is never half applied.

# How the lock of a build names a file of changes: by the name of the file, and no folder.
LOCKED_AS: Final = "changes/{}"
STALE: Final = "change_was_made_of_what_stands"
NOT_CARRIED: Final = "change_is_of_what_is_carried"


def to_lock(name: str, content: bytes) -> LockedInput:
    """A file of changes as the lock of a build names it: by its hash."""
    return LockedInput(
        name=LOCKED_AS.format(name),
        kind=InputKind.GAZETTEER,
        sha256=hashlib.sha256(content).hexdigest(),
        bytes=len(content),
    )


def recipe_of(vibe: Tag) -> dict[str, int]:
    """The recipe of a vibe as a line holds it: each part with its hundredths."""
    return {term.feature_id.value: term.hundredths for term in vibe.terms}


def names_of(vibe: Tag) -> dict[str, str | None]:
    return {"label": vibe.label, "low_end": vibe.low_end, "high_end": vibe.high_end}


def lines_of(vibe: Tag) -> list[str]:
    """What a vibe cannot see, after the line every vibe says first."""
    return list(vibe.cannot_see[1:])


def labels_of(measure: Metric) -> dict[str, str]:
    return {"label": measure.label, "short_label": measure.short_label}


HELD: Final[Mapping[What, Callable[[Tag], object]]] = {
    What.RECIPE: recipe_of,
    What.NAME: names_of,
    What.CANNOT_SEE: lines_of,
}


# The rule a change of a vibe breaks where the vibe it would make is no vibe at all.
BROKEN_BY: Final[Mapping[What, str]] = {
    What.RECIPE: "recipe_keeps_its_rules",
    What.NAME: "name_is_plain",
    What.CANNOT_SEE: "says_what_it_cannot_see",
}


def _same(one: object, other: object) -> bool:
    return json.dumps(one, sort_keys=True) == json.dumps(other, sort_keys=True)


def _made_of_what_stands(change: Change, changes: Sequence[Change], core: object) -> bool:
    """Whether a change was made of what core holds, or of what an earlier line made it.

    A line says what stood before it. Where that is neither, core's own has
    moved since the person decided, and what they decided was decided of
    something else: the build stops, and a person looks again.
    """
    before = [one.now for one in changes if one.key == change.key and one.n < change.n]
    return any(_same(change.was, held) for held in (core, *before))


def _with(vibe: Tag, change: Change) -> Tag:
    """A vibe with one change laid over it. `ValueError` for a change it cannot take."""
    if change.what is What.RECIPE:
        now = cast(dict[str, int], change.now)
        if set(now) != {term.feature_id.value for term in vibe.terms}:
            raise ValueError("recipe_holds_cores_parts")
        return vibe.replace(
            terms=tuple(term.replace(hundredths=now[term.feature_id.value]) for term in vibe.terms)
        )
    if change.what is What.NAME:
        now = cast(dict[str, Any], change.now)
        # A vibe of one way has no ends to name, and a scale has both.
        if any(
            (now[end] is None) != (getattr(vibe, end) is None) for end in ("low_end", "high_end")
        ):
            raise ValueError("vibe_is_cores")
        return vibe.replace(
            label=now["label"],
            short_label=now["label"],
            low_end=now["low_end"],
            high_end=now["high_end"],
        )
    return vibe.replace(cannot_see=(vibe.cannot_see[0], *cast(list[str], change.now)))


def adjusted(vibes: Sequence[Tag], changes: Sequence[Change]) -> tuple[Tag, ...]:
    """The vibes of a release, with what stands of a file of changes laid over core's own.

    With no change that stands of a vibe, each is as it was handed over. Raises
    `ChangesError`, which names the line, for a change of a vibe the release
    does not carry, for one made of something other than what stands, and for
    one that breaks a rule core holds a vibe of a release to.
    """
    held = {vibe.tag_id: vibe for vibe in vibes}
    for change in standing(changes):
        if change.what not in HELD:
            continue
        tag_id = TagId(change.of)
        if tag_id not in held:
            raise ChangesError(change.n, NOT_CARRIED)
        if not _made_of_what_stands(change, changes, HELD[change.what](TAGS[tag_id])):
            raise ChangesError(change.n, STALE)
        try:
            made = _with(held[tag_id], change)
        except ValidationError:
            raise ChangesError(change.n, BROKEN_BY[change.what]) from None
        except ValueError as error:
            raise ChangesError(change.n, str(error)) from None
        rule = what_a_vibe_breaks(made)
        if rule is not None:
            raise ChangesError(change.n, rule)
        held[tag_id] = made
    return tuple(held[vibe.tag_id] for vibe in vibes)


def relabelled(measures: Sequence[Metric], changes: Sequence[Change]) -> tuple[Metric, ...]:
    """The measures of a release, each under the label that stands of a file of changes.

    A change of a measure the release does not carry changes nothing: a build
    carries the measures it has a file for, and the label waits for the file.
    """
    held = {measure.feature_id: measure for measure in measures}
    for change in standing(changes):
        feature_id = FeatureId(change.of) if change.what is What.LABEL else None
        if feature_id is None or feature_id not in held:
            continue
        core = FEATURES[feature_id]
        of_core = {"label": core.label, "short_label": core.short_label}
        if not _made_of_what_stands(change, changes, of_core):
            raise ChangesError(change.n, STALE)
        made = held[feature_id].replace(**cast(dict[str, str], change.now))
        rule = what_a_measure_breaks(made)
        if rule is not None:
            raise ChangesError(change.n, rule)
        held[feature_id] = made
    return tuple(held[measure.feature_id] for measure in measures)


def labels_hold(changes: Sequence[Change]) -> None:
    """Hold every label that stands to the rule of a label, before a file is opened.

    `relabelled` holds a label again where it lays it over a measure. This is
    for the start of a build, which has no measure yet. Raises `ChangesError`.
    """
    for change in standing(changes):
        if change.what is not What.LABEL:
            continue
        feature_id = FeatureId(change.of)
        core = FEATURES[feature_id]
        if not _made_of_what_stands(
            change, changes, {"label": core.label, "short_label": core.short_label}
        ):
            raise ChangesError(change.n, STALE)
        now = cast(dict[str, str], change.now)
        rule = what_labels_break(feature_id, now["label"], now["short_label"])
        if rule is not None:
            raise ChangesError(change.n, rule)


def row_of(chain: Chain) -> dict[str, Any]:
    """A row of the table of tiers as a line holds it."""
    return {
        "name": chain.name,
        "kind": chain.kind.value,
        "tier": chain.tier.value,
        "wikidata": list(chain.wikidata),
        "spellings": list(chain.spellings),
    }


def table_with(table: Table, changes: Sequence[Change]) -> Table:
    """The table of tiers with what stands of a file of changes laid over it.

    A chain is moved to another tier, added or taken out. A row a change made
    is on the founder's table: the founder decided it. A chain that is added
    is the last row, and every other row keeps its place. With no change that
    stands of the table, it is the table as it was handed over.

    **A chain of the table is moved by its tier alone.** Its name, its kind and
    how the file writes it are the table's, and no line changes them. **A chain
    that is added is named as the file of places writes it**: its name is one
    of its spellings. So no line can put a name of its own choosing into what
    Burro says of a measure. Whether the name is of a chain at all, and not of
    a person or of one shop, is the build's to say, from the file of places:
    `seen_to_be_a_chain`.

    Raises `ChangesError`, which names the line, for a change made of
    something other than what stands, for a row that is no row of the table,
    and for two rows that could claim one place.
    """
    held = {chain.key: chain for chain in table.chains}
    order = [chain.key for chain in table.chains]
    moved = False
    for change in standing(changes):
        if change.what is not What.BRAND:
            continue
        of_the_file = row_of(table.by_key[change.of]) if change.of in table.by_key else None
        if not _made_of_what_stands(change, changes, of_the_file):
            raise ChangesError(change.n, STALE)
        moved = True
        if change.now is None:
            held.pop(change.of, None)
            continue
        row = cast(dict[str, Any], change.now)
        if of_the_file is not None and {**row, "tier": of_the_file["tier"]} != of_the_file:
            raise ChangesError(change.n, "chain_moves_by_its_tier_alone")
        if of_the_file is None and row["name"] not in row["spellings"]:
            raise ChangesError(change.n, "chain_is_named_as_it_is_written")
        if not name_is_plain(str(row["name"]), figures=True):
            raise ChangesError(change.n, "name_is_plain")
        try:
            held[change.of] = Chain.model_validate(
                {**row, "key": change.of, "on_the_founders_table": True}
            )
            brand_table.checked(tuple(held.values()), table.read_in)
        except (ValidationError, TableError):
            raise ChangesError(change.n, "row_is_a_row_of_the_table") from None
        if change.of not in order:
            order.append(change.of)
    if not moved:
        return table
    return brand_table.checked(tuple(held[key] for key in order if key in held), table.read_in)


# How many places of the file of places must bear a name as their brand, each standing
# apart from the others, for the name to be that of a chain. One shop is no chain.
FEWEST_PLACES_OF_A_CHAIN: Final = 2
NOT_SEEN: Final = "chain_is_seen_to_be_one"


def added(table: Table, changes: Sequence[Change]) -> tuple[Change, ...]:
    """The lines that stand and add a chain the table of the repository does not hold."""
    return tuple(
        change
        for change in standing(changes)
        if change.what is What.BRAND and change.now is not None and change.of not in table.by_key
    )


def seen_to_be_a_chain(
    change: Change, written: Mapping[str, Mapping[str, int]], counted: Mapping[str, int]
) -> bool:
    """Whether the file of places shows that a name a line adds is the name of a chain.

    **How a chain is told from a person and from one shop.** The publisher of the
    file of places gives a place a brand where it has matched the place to a
    chain, and gives none to any other place. So a name is that of a chain where
    the file writes it as the brand of two places or more that stand apart.
    `written` is the rows the file gives the brand of each chain, by how it is
    written, and `counted` the places of each chain that were counted, those
    within a few metres of each other as one. A name the file gives to no place,
    or to one, is not shown to be a chain, and the line is refused.

    **It cannot be told any other way.** A chain that the file of places does
    not know, as it knows none of two chains of gyms of the founder's table, is
    refused here though it is a chain. It is added to the table in the
    repository, in a change that a person reads.
    """
    name = brand_table.folded(str(cast(dict[str, Any], change.now)["name"]))
    rows = sum(
        count
        for spelling, count in written.get(change.of, {}).items()
        if brand_table.folded(spelling) == name
    )
    fewest = FEWEST_PLACES_OF_A_CHAIN
    return rows >= fewest and counted.get(change.of, 0) >= fewest


# The kinds of line a build applies, and the kinds it does nothing with: a flag is for a
# person to look at.
OF_THE_CATALOGUE: Final = frozenset({What.RECIPE, What.NAME, What.CANNOT_SEE, What.LABEL})
APPLIED: Final = OF_THE_CATALOGUE | {What.BRAND}
FOR_A_PERSON: Final = frozenset({What.FLAG})


def applied(changes: Sequence[Change], kinds: Iterable[What]) -> list[dict[str, object]]:
    """The lines that stand of some kinds, as the record of a build lists them: by their
    number, with who and when, and with no reason and no value."""
    wanted = frozenset(kinds)
    return [
        {"n": one.n, "what": one.what.value, "of": one.of, "by": one.by, "on": one.on}
        for one in standing(changes)
        if one.what in wanted
    ]
