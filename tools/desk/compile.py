"""Make a build's files from the lines of decisions.

`build` is a pure function of the draft folder, the items and the lines. It reads
no clock and no network, and the same lines give the same bytes, in whatever order
they were written. When a check fails nothing is written, and every check that
failed is said.

What is decided is laid over the draft. Where nothing is decided the draft stands,
and where reviewers differ nothing is applied until the founder settles it. What
could not be applied is listed in `not_applied.csv`, so that no decision is lost
without a word.

    names              areas.csv, aliases.csv, name_evidence.csv     in the gazetteer
    borders, whole     oa_to_area.csv, areas.csv, not_applied.csv    in the gazetteer
    claims             out/private/claims_review.jsonl
    sentences          out/private/golden.jsonl
    any other queue    out/<queue>.csv, a row for each answer that stands
    every queue        out/private/to_look_at.csv

What is made from the lines of a private queue is written to `out/private/`, which only
its owner may read, as the lines themselves are.

Every answer that stands is written with its note and its mark for a second reviewer,
so that neither is a flag nobody sees again. What a person called wrong, could not
judge, marked or skipped with a note is gathered in one list, `to_look_at.csv`. In the
gazetteer a note is written in one place only: as the `reason` of a cell that was moved.

Standard library only. See docs/design/desk.md, section 3, and
docs/design/london-data-areas.md, section 5.
"""

import csv
import io
import json
import os
import re
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, cast

from desk import records
from desk.records import (
    ALONE,
    DISPUTED,
    DONE,
    FOUNDER,
    SKIP,
    TOGETHER,
    Item,
    Items,
    Json,
    Line,
    Question,
    Read,
    Standing,
    Unfit,
    Verdict,
)

type Row = dict[str, str]

# The four files of the areas design, section 5, and their columns.
AREAS, CELLS, ALIASES, EVIDENCE = "areas.csv", "oa_to_area.csv", "aliases.csv", "name_evidence.csv"
NOT_APPLIED: Final = "not_applied.csv"
COLUMNS: Final[Mapping[str, tuple[str, ...]]] = {
    AREAS: (
        *("area_id", "slug", "name", "primary_borough"),
        *("seed_record", "review_state", "superseded_by"),
    ),
    CELLS: ("oa21cd", "area_id", "basis", "evidence", "decided_by", "decided_on", "reason"),
    ALIASES: ("alias", "area_id", "kind", "source_id", "record_id"),
    EVIDENCE: (
        *("area_id", "name", "role", "source_id", "record_id", "as_written", "field"),
        *("locates", "data_date", "retrieved_on", "snapshot_sha256", "checked"),
        *("chosen_by", "chosen_on"),
    ),
    NOT_APPLIED: ("queue", "item", "part", "from_area", "to_area", "decided_by", "why"),
}
# What each queue is written to, under `out/`, when it is not one of the four above.
OUT: Final[Mapping[str, str]] = {
    "claims": "claims_review.jsonl",
    "sentences": "golden.jsonl",
    "figures": "figures_to_check.csv",
}
KINDS_COUNTS: Final = "kinds_counts.csv"
# The one list of what a person flagged, in every queue. It holds the notes of private
# queues among the rest, so it is kept with what is never published.
TO_LOOK_AT: Final = "to_look_at.csv"
LOOK_COLUMNS: Final = (
    *("queue", "item", "title", "reviewer", "answer", "why"),
    *("note", "second", "decided_on", "synthetic"),
)
# Why an answer is in the list, in the order they are tried.
WRONG, NOT_KNOWN, SKIPPED, MARKED = "wrong", "not_known", "skipped", "marked"
CALLED_WRONG: Final = records.CALLED_WRONG
# A rater is asked to say which areas they cannot rate. So it is no flag there.
EXPECTED_NOT_TO_KNOW: Final = frozenset({"ratings"})

# How far an area has been checked. A state never falls. `named_by_rule` is what a draft
# says of an area whose name stands by a rule the founder has decided already: nobody
# read the name, so it is below a name that a person checked. The desk makes no item of
# such a name, and the state is raised only by what a reviewer says of the border.
STATES: Final = (
    "drafted",
    "named_by_rule",
    "name_checked",
    "boundary_checked",
    "checked_twice",
)
# A reviewer is written as a role, never as a name and never as a label.
ROLES: Final[Mapping[str, str]] = {"r1": "founder", "r2": "reviewer-2"}
CLAIM_ROLES: Final[Mapping[str, str]] = {"r1": "founder", "r2": "second"}
PRIMARY, REVIEWED, RIGHT, AREA, DROP = "primary", "reviewed", "right", "area", "drop"
# The key of an item's preset that says which answer the draft proposes.
PROPOSED: Final = "proposed"
# The answers that make a name an alias, which are the kinds of alias too.
KINDS_OF_ALIAS: Final = ("same_ground", "inside", "wide")
ROLE_OF_KIND: Final[Mapping[str, str]] = {"same_ground": "alias", "inside": "alias", "wide": "wide"}
MOST_AREAS: Final = 5
SYNTHETIC: Final = "syn-"

# Why a decision was not applied.
NO_NOTE = "no_note"
IN_DISPUTE = "disputed"
TWO_AREAS = "moved_to_two_areas"
STALE = "item_changed"
NO_AREA_NAMED = "no_area_named"
NO_AREA_ID = "no_area_id"
NO_SUCH_AREA = "no_such_area"
NOT_A_SPELLING = "not_a_spelling"
AREA_HAS_CELLS = "area_has_cells"
AREA_HAS_NAMES = "area_has_names"

# A cell that a spreadsheet would run as a formula gains a leading apostrophe.
FORMULA: Final = ("=", "+", "-", "@", "\t", "\r")


class Refused(Exception):
    """A check failed, so nothing was written. It holds every check that failed."""

    def __init__(self, problems: Sequence[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = tuple(problems)


def slug(name: str) -> str:
    """A name in lower case with hyphens, as the areas design gives a slug."""
    return re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")


# What is read


@dataclass(frozen=True, slots=True)
class Queue:
    question: Question
    items: Items
    reads: Mapping[str, Read]
    stands: Mapping[str, Standing]

    def verdict(self, item: Item) -> Verdict:
        return records.verdict(item, self.question, self.stands)

    def decided(self) -> Iterator[tuple[Item, Verdict]]:
        """Every item in the order of its file, with what its answers come to."""
        for item in self.items.items:
            yield item, self.verdict(item)


@dataclass(frozen=True, slots=True)
class Desk:
    """All that a build's files are made from."""

    synthetic: bool
    queues: Mapping[str, Queue]
    # The draft folder: the bytes of each table, by the name of its file.
    draft: Mapping[str, bytes]


def load(data: Path, questions: Path) -> Desk:
    """Read the draft, the items and the lines. Raises `Unfit` for a file it cannot read."""
    asked = records.read_questions(questions)
    queues: dict[str, Queue] = {}
    for path in sorted((data / "items").glob("*.jsonl")):
        items = records.read_items(path)
        if items.queue not in asked:
            raise Unfit(f"items/{path.name} is of a queue that has no question")
        reads = records.read_queue(data, items.queue, private=asked[items.queue].private)
        stands = {name: records.standing(held.lines) for name, held in reads.items()}
        queues[items.queue] = Queue(asked[items.queue], items, reads, stands)
    if not queues:
        raise Unfit("There is no item, so there is nothing to make files from")
    for name, queue in queues.items():
        if queue.items.question != asked[name].version:
            raise Unfit(f"items/{name}.jsonl was made for another version of its question")
    if len({queue.items.synthetic for queue in queues.values()}) != 1:
        raise Unfit("Some items are of the made-up city and some are real")
    astray = records.misplaced(data, asked)
    if astray:
        raise Unfit(
            f"Decisions are in the wrong folder: {', '.join(astray)}. Lines that may be "
            f"published are kept in {records.PUBLIC_TREE}, and the rest in {records.PRIVATE_TREE}"
        )
    folder = data / "draft"
    tables = (AREAS, CELLS, ALIASES, EVIDENCE)
    draft = {name: (folder / name).read_bytes() for name in tables if (folder / name).is_file()}
    ordered = {name: queues[name] for name in asked if name in queues}
    return Desk(next(iter(queues.values())).items.synthetic, ordered, draft)


# Tables


def table(name: str, held: bytes) -> list[Row]:
    """The rows of a table of the draft. Raises `Unfit` if its columns are not the design's."""
    try:
        reader = csv.DictReader(io.StringIO(held.decode("utf-8"), newline=""), strict=True)
        rows = [dict(row) for row in reader]
    except (UnicodeDecodeError, csv.Error) as error:
        raise Unfit(f"draft/{name} cannot be read as a table") from error
    if tuple(reader.fieldnames or ()) != COLUMNS[name]:
        raise Unfit(f"draft/{name} does not have the columns of the design, in their order")
    if any(None in row or None in row.values() for row in rows):
        raise Unfit(f"draft/{name} has a row with a cell too many or too few")
    return rows


def _cell(value: str) -> str:
    return f"'{value}" if value.startswith(FORMULA) else value


def written(columns: Sequence[str], rows: Iterable[Mapping[str, str]]) -> bytes:
    """A table as bytes: the same rows give the same bytes."""
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow([_cell(row.get(column, "")) for column in columns])
    return out.getvalue().encode("utf-8")


def lines_of(rows: Iterable[Mapping[str, Json]]) -> bytes:
    return "".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
        for row in rows
    ).encode("utf-8")


# What is built


@dataclass(slots=True)
class Built:
    """The files of a build, by name, and what was counted while they were made."""

    gazetteer: dict[str, bytes] = field(default_factory=lambda: dict[str, bytes]())
    out: dict[str, bytes] = field(default_factory=lambda: dict[str, bytes]())
    # The files of `out` that are made from private lines. They are written to
    # `out/private/`, which is the owner's alone, and are never published.
    private: set[str] = field(default_factory=lambda: set[str]())
    # By queue: how many answers and moves were applied, how many were not, and how many
    # answers decide nothing because the person called the item wrong or could not judge.
    applied: Counter[str] = field(default_factory=lambda: Counter[str]())
    set_aside: Counter[str] = field(default_factory=lambda: Counter[str]())
    flagged: Counter[str] = field(default_factory=lambda: Counter[str]())
    # What is in the list to look at, by why it is there.
    look: Counter[str] = field(default_factory=lambda: Counter[str]())
    broken: int = 0
    # How many names were turned down while their areas have ground. Each is set aside
    # until the draft is made again from the answers.
    waits: int = 0
    # By queue: how many items a rule settled that the founder adopted. No person read
    # them one by one, so they are counted apart.
    by_rule: Counter[str] = field(default_factory=lambda: Counter[str]())


@dataclass(slots=True)
class Gazetteer:
    """The four tables while decisions are laid over them."""

    areas: dict[str, Row]
    aliases: list[Row]
    evidence: list[Row]
    cells: dict[str, Row] | None
    not_applied: list[Row] = field(default_factory=lambda: list[Row]())
    problems: list[str] = field(default_factory=lambda: list[str]())

    def set_aside(self, queue: str, line: Line, why: str) -> None:
        here, there = line.detail.get("from"), line.detail.get("to")
        self.not_applied.append(
            {
                "queue": queue,
                "item": line.item,
                "part": line.part,
                "from_area": here if isinstance(here, str) else "",
                "to_area": there if isinstance(there, str) else "",
                "decided_by": ROLES.get(line.reviewer, ""),
                "why": why,
            }
        )


def _raised(row: Row, state: str) -> None:
    now = row["review_state"] if row["review_state"] in STATES else STATES[0]
    row["review_state"] = max(now, state, key=STATES.index)


# The states a reviewer's answer about a border gives an area: checked by one, by two.
BY_ONE, BY_TWO = "boundary_checked", "checked_twice"


def _pick(line: Line, item: Item, fallback: str, wrote: set[str]) -> str | None:
    """The spelling chosen, or None if it is one no source wrote."""
    pick = line.detail.get("pick", fallback)
    if not isinstance(pick, str) or not pick:
        return None
    return pick if pick == fallback or pick in wrote or pick in (item.picks or ()) else None


def _of(line: Line) -> list[str] | None:
    of = line.detail.get("of", [])
    if not isinstance(of, list) or len(of) > MOST_AREAS:
        return None
    return (
        [each for each in of if isinstance(each, str)]
        if all(isinstance(each, str) for each in of)
        else None
    )


def _reslug(row: Row, name: str) -> str:
    """The slug of a new name. What the draft added to tell two areas apart is kept."""
    old = slug(row["name"])
    if row["slug"] == old or not row["slug"].startswith(f"{old}-"):
        return slug(name) if row["slug"] == old else row["slug"]
    return slug(name) + row["slug"][len(old) :]


def _names_of(held: Gazetteer, area_id: str) -> bool:
    """Whether another name is given to an area."""
    return any(row["area_id"] == area_id for row in held.aliases)


def _name_an_area(held: Gazetteer, line: Line, item: Item, area_id: str) -> str:
    """Apply the founder's answer to a name that was proposed as an area.

    Returns why it was not applied, or nothing if it was. Where an answer would leave a
    cell or a name with no area, it is not applied and the draft stands.
    """
    row = held.areas.get(area_id)
    if row is None:
        held.problems.append(f"names: {item.id} is of an area that draft/{AREAS} does not hold")
        return NO_SUCH_AREA
    mine = [
        each for each in held.evidence if each["area_id"] == area_id and each["role"] == PRIMARY
    ]
    name = _pick(line, item, row["name"], {each["as_written"] for each in mine})
    of = _of(line)
    if name is None or of is None:
        return NOT_A_SPELLING
    if line.answer == AREA:
        row["slug"], row["name"] = _reslug(row, name), name
        _raised(row, "name_checked")
        for each in mine:
            each.update(name=name, chosen_by=ROLES[FOUNDER], chosen_on=line.day)
        return ""
    if line.answer in KINDS_OF_ALIAS and not of:
        return NO_AREA_NAMED
    if any(other == area_id or other not in held.areas for other in of):
        return NO_SUCH_AREA
    if held.cells is not None and any(cell["area_id"] == area_id for cell in held.cells.values()):
        return AREA_HAS_CELLS
    if _names_of(held, area_id):
        return AREA_HAS_NAMES
    del held.areas[area_id]
    held.evidence[:] = [each for each in held.evidence if each not in mine]
    first = min(mine, key=lambda each: (each["source_id"], each["record_id"]), default=None)
    for other in of if line.answer in KINDS_OF_ALIAS else ():
        held.aliases.append(
            {
                "alias": name,
                "area_id": other,
                "kind": line.answer,
                "source_id": first["source_id"] if first else "",
                "record_id": first["record_id"] if first else "",
            }
        )
        chosen = {"chosen_by": ROLES[FOUNDER], "chosen_on": line.day}
        about = {"area_id": other, "name": name, "role": ROLE_OF_KIND[line.answer]}
        held.evidence += [{**each, **about, **chosen} for each in mine]
    return ""


def _name_an_alias(held: Gazetteer, line: Line, item: Item, word: str) -> str:
    """Apply the founder's answer to a name that was proposed as another name of an area.

    Returns why it was not applied, or nothing if it was.
    """
    preset = item.held.get("preset")
    before = cast(dict[str, Json], preset).get("of") if isinstance(preset, dict) else None
    given = before if isinstance(before, list) else []
    drafted = {each for each in given if isinstance(each, str)}
    rows = [row for row in held.aliases if slug(row["alias"]) == word and row["area_id"] in drafted]
    if not rows:
        held.problems.append(f"names: {item.id} is of a name that draft/{ALIASES} does not hold")
        return NO_SUCH_AREA
    if line.answer == AREA:
        # An area needs an id, and only the areas build gives one.
        return NO_AREA_ID
    mine = [
        each
        for each in held.evidence
        if each["role"] != PRIMARY and slug(each["name"]) == word and each["area_id"] in drafted
    ]
    name = _pick(line, item, rows[0]["alias"], {each["as_written"] for each in mine})
    of = _of(line)
    if name is None or of is None:
        return NOT_A_SPELLING
    to = [] if line.answer == DROP else of or sorted(drafted)
    if any(other not in held.areas for other in to):
        return NO_SUCH_AREA
    held.aliases[:] = [row for row in held.aliases if row not in rows]
    held.evidence[:] = [each for each in held.evidence if each not in mine]
    for other in to:
        like = next((row for row in rows if row["area_id"] == other), rows[0])
        held.aliases.append({**like, "alias": name, "area_id": other, "kind": line.answer})
        chosen = {"chosen_by": ROLES[FOUNDER], "chosen_on": line.day}
        about = {"area_id": other, "name": name, "role": ROLE_OF_KIND[line.answer]}
        seen = [each for each in mine if each["area_id"] == other] or mine[:1]
        held.evidence += [{**each, **about, **chosen} for each in seen]
    return ""


def names(held: Gazetteer, queue: Queue, built: Built) -> None:
    """Lay the founder's answers over the names of the draft.

    Other names are decided first, and then the names proposed as areas, each in the
    order of the items. So an area goes only once no other name is still given to it.
    """
    decided = [(item, found.applied) for item, found in queue.decided() if found.applied]
    for kind in ("a", "n"):
        for item, line in decided:
            mark, _, rest = item.id.partition(":")
            if mark not in ("a", "n"):
                held.problems.append(f"names: {item.id} is neither an area nor another name")
            if mark != kind:
                continue
            if kind == "n":
                why = _name_an_area(held, line, item, rest)
            else:
                why = _name_an_alias(held, line, item, rest.partition(":")[2])
            if why:
                held.set_aside("names", line, why)
            built.waits += why == AREA_HAS_CELLS
            (built.set_aside if why else built.applied)["names"] += 1


def _role(queue: str, reviewers: Iterable[str], problems: list[str]) -> None:
    for reviewer in reviewers:
        if reviewer not in ROLES:
            problems.append(
                f"decisions/{queue}/{reviewer}.jsonl: {reviewer} has no role to be written as. "
                "Only r1 and r2 decide this queue"
            )


def _moves(held: Gazetteer, name: str, queue: Queue, built: Built) -> list[tuple[Line, str]]:
    """The moves of one queue that may be applied, each with its reason. The rest are set aside."""
    ready: list[tuple[Line, str]] = []
    for item in queue.items.items:
        found = queue.verdict(item)
        for reviewer in sorted(queue.stands, key=records.number_of):
            moved = queue.stands[reviewer].moves.get(item.id, {})
            answer = found.answers.get(reviewer)
            for part in sorted(moved):
                line = moved[part]
                if not records.fresh(line, item, queue.question):
                    why = STALE
                elif found.state == DISPUTED or (found.state == DONE and reviewer not in found.by):
                    why = IN_DISPUTE
                elif answer is None or not answer.note:
                    why = NO_NOTE
                else:
                    ready.append((line, answer.note))
                    continue
                held.set_aside(name, line, why)
                built.set_aside[name] += 1
    return ready


def borders(held: Gazetteer, queues: Mapping[str, Queue], built: Built) -> None:
    """Lay the moves that stand over the cells, and raise the state of each area checked."""
    cells = held.cells
    if cells is None:
        return
    ready: dict[str, list[tuple[str, Line, str]]] = {}
    for name, queue in queues.items():
        for line, reason in _moves(held, name, queue, built):
            ready.setdefault(line.part, []).append((name, line, reason))
    for cell in sorted(ready):
        to = {_text(line.detail.get("to")) for _, line, _ in ready[cell]}
        # The first is the founder's, in the queue of borders, where there is one.
        name, line, reason = ready[cell][0]
        if len(to) > 1:
            for queue, other, _ in ready[cell]:
                held.set_aside(queue, other, TWO_AREAS)
                built.set_aside[queue] += 1
        elif cell not in cells or not to <= set(held.areas):
            held.problems.append(
                f"{name}: the move of {cell} names a cell or an area that the draft does not hold"
            )
        else:
            (there,) = to
            who = ROLES.get(line.reviewer, "")
            cells[cell].update(area_id=there, basis=REVIEWED, reason=reason)
            cells[cell].update(decided_by=who, decided_on=line.day)
            built.applied[name] += 1
    for area_id, row in held.areas.items():
        by = _right_by(area_id, row, queues)
        if by:
            _raised(row, BY_TWO if len(by) > 1 else BY_ONE)
    for name, queue in queues.items():
        for _, found in queue.decided():
            if found.state == DISPUTED:
                built.set_aside[name] += 1
            elif found.applied is not None:
                # An area called wrong, or not known, is checked by nobody.
                nothing = _decides_nothing(name, found.applied.answer)
                (built.flagged if nothing else built.applied)[name] += 1


def _right_by(area_id: str, row: Row, queues: Mapping[str, Queue]) -> set[str]:
    """The reviewers who say an area's boundary is right: of the area, or of its whole borough."""
    by: set[str] = set()
    answered: set[str] = set()
    own = queues.get("borders")
    item = None if own is None else own.items.by_id.get(area_id)
    if own is not None and item is not None:
        found = own.verdict(item)
        answered = set(found.answers)
        if found.state == DISPUTED or (found.applied and found.applied.answer != RIGHT):
            return set()
        by |= set(found.by)
    whole = queues.get("whole")
    borough = None if whole is None else whole.items.by_id.get(slug(row["primary_borough"]))
    if whole is not None and borough is not None:
        found = whole.verdict(borough)
        if found.applied is not None and found.applied.answer == RIGHT:
            # What a reviewer said of the area itself is not said again by the borough.
            by |= set(found.by) - answered
    return by


def _check(held: Gazetteer, draft_cells: list[Row] | None, synthetic: bool) -> None:
    """The checks before anything is written. Each adds a line to the problems."""
    problems = held.problems
    slugs = Counter(row["slug"] for row in held.areas.values())
    if any(count > 1 for count in slugs.values()):
        problems.append(f"{AREAS}: two areas would have one slug")
    for name, rows in ((ALIASES, held.aliases), (EVIDENCE, held.evidence)):
        for gone in sorted({row["area_id"] for row in rows} - set(held.areas)):
            problems.append(f"{name}: a row is of {gone}, which {AREAS} does not hold")
    if held.cells is not None and draft_cells is not None:
        if len(draft_cells) != len(held.cells) or any(not row["oa21cd"] for row in draft_cells):
            problems.append(f"{CELLS}: a cell has two rows, or a row has no cell")
        for gone in sorted({row["area_id"] for row in held.cells.values()} - set(held.areas)):
            problems.append(f"{CELLS}: a cell is in {gone}, which {AREAS} does not hold")
    if any(area_id.startswith(SYNTHETIC) != synthetic for area_id in held.areas):
        problems.append(f"{AREAS}: the made-up city and London are in one file")


def gazetteer(desk: Desk, built: Built) -> list[str]:
    """Make the curated files. Returns the checks that failed."""
    if AREAS not in desk.draft:
        return []
    drafted = {name: table(name, held) for name, held in desk.draft.items()}
    areas = {row["area_id"]: row for row in drafted[AREAS]}
    cells = None if CELLS not in drafted else {row["oa21cd"]: row for row in drafted[CELLS]}
    held = Gazetteer(areas, drafted.get(ALIASES, []), drafted.get(EVIDENCE, []), cells)
    if len(areas) != len(drafted[AREAS]):
        held.problems.append(f"draft/{AREAS} holds an area twice")
    for name in ("borders", "whole", "claims", "sentences"):
        if name in desk.queues:
            _role(name, desk.queues[name].stands, held.problems)
    if "names" in desk.queues:
        names(held, desk.queues["names"], built)
    borders(
        held,
        {name: desk.queues[name] for name in ("borders", "whole") if name in desk.queues},
        built,
    )
    _check(held, drafted.get(CELLS), desk.synthetic)
    tables = {AREAS: held.areas.values(), ALIASES: held.aliases, EVIDENCE: held.evidence}
    tables[NOT_APPLIED] = held.not_applied
    if held.cells is not None:
        tables[CELLS] = held.cells.values()
    for name, rows in tables.items():
        built.gazetteer[name] = written(COLUMNS[name], _in_order(name, rows))
    return held.problems


def _in_order(name: str, rows: Iterable[Row]) -> list[Row]:
    """The rows of a table in the one order they are written in, each of them once."""
    columns = COLUMNS[name]
    return sorted(_once(rows), key=lambda row: tuple(row.get(column, "") for column in columns))


def _once(rows: Iterable[Row]) -> Iterator[Row]:
    seen: set[tuple[tuple[str, str], ...]] = set()
    for row in rows:
        key = tuple(sorted(row.items()))
        if key not in seen:
            seen.add(key)
            yield row


# The files of `out/`


def _decides_nothing(queue: str, answer: str) -> str:
    """Whether an answer calls the item wrong, or says the person could not judge."""
    if answer in CALLED_WRONG:
        return WRONG
    if answer in records.NOT_KNOWN and queue not in EXPECTED_NOT_TO_KNOW:
        return NOT_KNOWN
    return ""


def why_of(queue: str, line: Line) -> str:
    """Why an answer is one to look at again, or nothing if it is not."""
    if line.answer == SKIP:
        return SKIPPED if line.note or line.second else ""
    return _decides_nothing(queue, line.answer) or (MARKED if line.second else "")


def _said(line: Line, synthetic: bool) -> dict[str, Json]:
    """What goes with every answer written: its note, its mark, and which city it is of."""
    return {"note": line.note, "second": line.second, "synthetic": synthetic}


def _claims(queue: Queue, synthetic: bool) -> Iterator[dict[str, Json]]:
    for item, found in sorted(queue.decided(), key=lambda pair: pair[0].id):
        line = found.applied
        if line is not None:
            accepted = line.answer == "accept"
            yield {
                "claim_id": item.id,
                "review": {
                    "status": "accepted" if accepted else "rejected",
                    "reviewed_on": line.day,
                    "reviewer": CLAIM_ROLES[line.reviewer],
                    "reason": None if accepted else line.answer,
                },
                **_said(line, synthetic),
            }


def _golden(queue: Queue, synthetic: bool) -> Iterator[dict[str, Json]]:
    rows: list[dict[str, Json]] = []
    for item, found in queue.decided():
        line = found.applied
        if line is not None:
            about = cast(dict[str, Json], item.held.get("preset") or {})
            where = {key: about.get(key) for key in ("page_id", "revision_id", "sentence")}
            answer: dict[str, Json] = {"fit": line.answer == "fit", "code": line.answer}
            rows.append({**where, **answer, **_said(line, synthetic)})
    yield from sorted(rows, key=lambda row: json.dumps(row, sort_keys=True))


def _text(value: Json) -> str:
    return value if isinstance(value, str) else json.dumps(value, sort_keys=True)


def _flag(value: bool) -> str:
    return "true" if value else "false"


def _may_be_ruled(queue: Queue) -> bool:
    """Whether a rule fits any item of a queue, so that its table says which rule
    settled each row."""
    return any(
        records.FITS in cast(dict[str, Json], item.held.get("preset") or {})
        for item in queue.items.items
    )


def _about(queue: Queue, item: Item, line: Line) -> Row:
    """What the item was made with, and never what a line says it was: a file sent back
    by another reviewer has not been through the server. A queue that lets a spelling be
    chosen adds the spelling and the areas named, where they are ones the item offers.
    Where a rule settled the item, the rule is named: only the founder's own desk writes
    such a line."""
    given = cast(dict[str, Json], item.held.get("preset") or {})
    about = {key: _text(value) for key, value in given.items() if key != PROPOSED}
    if _may_be_ruled(queue):
        fits = line.reviewer == FOUNDER and records.by_rule(line) == given.get(records.FITS)
        about[records.RULE] = records.by_rule(line) if fits else ""
    if "pick" in queue.question.adds:
        drafted = given.get("pick")
        pick, of = line.detail.get("pick", drafted), _of(line)
        offered = (*(item.picks or ()), drafted)
        about["pick"] = pick if isinstance(pick, str) and pick in offered else ""
        about["of"] = " ".join(of or ())
    return about


# The column that says whether a row is of an item the desk asks about today. A name that
# the founder turned down is no item once the draft is made again without it. Its row is
# kept, so that the next draft leaves it out too.
ASKED_TODAY: Final = "asked_today"


def _turned_down(queue: Queue) -> list[Line]:
    """The founder's answers that turned down a name proposed as an area, to items the
    queue no longer holds. Another name is put forward again by every draft, and the
    answer to it is applied here: only an area is left out of a draft for its answer."""
    held = queue.question.held.get(records.SET_ASIDE)
    answers = held.get("answers") if isinstance(held, dict) else None
    if not isinstance(answers, list):
        return []
    mine = queue.stands.get(FOUNDER, records.NOTHING).answers
    return [
        line
        for name, line in sorted(mine.items())
        if name not in queue.items.by_id and line.answer in answers and name.startswith("n:")
    ]


def _each(queue: Queue, synthetic: bool) -> tuple[tuple[str, ...], list[Row]]:
    """A row for every reviewer's answer that stands. Here the reviewer is written as a label."""
    rows: list[Row] = []
    keeps = records.SET_ASIDE in queue.question.held
    for item in sorted(queue.items.items, key=lambda item: item.id):
        for reviewer in sorted(queue.stands, key=records.number_of):
            line = queue.stands[reviewer].answers.get(item.id)
            if line is None or line.answer == SKIP or not records.fresh(line, item, queue.question):
                continue
            fixed = {"item": item.id, "reviewer": reviewer, "answer": line.answer}
            said = {"note": line.note, "second": _flag(line.second)}
            last = {"decided_on": line.day, "synthetic": _flag(synthetic)}
            today = {ASKED_TODAY: _flag(True)} if keeps else {}
            rows.append({**_about(queue, item, line), **today, **fixed, **said, **last})
    for line in _turned_down(queue):
        # The item is gone, so nothing is said of what it was made with but the rule.
        fixed = {"item": line.item, "reviewer": line.reviewer, "answer": line.answer}
        said = {"note": line.note, "second": _flag(line.second), ASKED_TODAY: _flag(False)}
        last = {"decided_on": line.day, "synthetic": _flag(synthetic)}
        rows.append({records.RULE: records.by_rule(line), **fixed, **said, **last})
    rows.sort(key=lambda row: row["item"])
    ends = ("item", "reviewer", "answer", "note", "second", "decided_on", "synthetic")
    fields = sorted({key for row in rows for key in row} - set(ends))
    return (*ends[:3], *fields, *ends[3:]), rows


def _look_at(desk: Desk, built: Built) -> list[Row]:
    """Every answer a person flagged, in the order of the queues and then of the items."""
    rows: list[Row] = []
    for name, queue in desk.queues.items():
        for item in sorted(queue.items.items, key=lambda item: item.id):
            for reviewer in sorted(queue.stands, key=records.number_of):
                line = queue.stands[reviewer].answers.get(item.id)
                if line is None or not records.fresh(line, item, queue.question):
                    continue
                why = why_of(name, line)
                if not why:
                    continue
                built.look[why] += 1
                rows.append(
                    {
                        "queue": name,
                        "item": item.id,
                        "title": _text(item.held.get("title") or ""),
                        "reviewer": reviewer,
                        "answer": line.answer,
                        "why": why,
                        "note": line.note,
                        "second": _flag(line.second),
                        "decided_on": line.day,
                        "synthetic": _flag(desk.synthetic),
                    }
                )
    return rows


def _counts(question: Question, rows: Iterable[Row], synthetic: bool) -> bytes:
    """For each kind of venue: how many were asked about, and how many got each answer."""
    count: dict[str, Counter[str]] = {}
    for row in rows:
        count.setdefault(row.get("kind", ""), Counter())[row["answer"]] += 1
    columns = ("kind", "asked", *question.answers, "synthetic")
    return written(
        columns,
        (
            {
                "kind": kind,
                "asked": str(count[kind].total()),
                **{a: str(count[kind][a]) for a in question.answers},
                "synthetic": _flag(synthetic),
            }
            for kind in sorted(count)
        ),
    )


def out(desk: Desk, built: Built) -> list[str]:
    problems: list[str] = []
    for name, queue in desk.queues.items():
        rule = records.rule_of(name)
        in_gazetteer = rule == ALONE or name in ("borders", "whole")
        made: dict[str, bytes] = {}
        if rule == TOGETHER and not in_gazetteer:
            _role(name, queue.stands, problems)
            if any(reviewer not in ROLES for reviewer in queue.stands):
                continue
            make = _claims if name == "claims" else _golden
            made[OUT[name]] = lines_of(make(queue, desk.synthetic))
            for _, found in queue.decided():
                if found.state == DISPUTED:
                    built.set_aside[name] += 1
                elif found.applied is not None:
                    built.applied[name] += 1
        else:
            # What is applied of a name or a border is counted where it is applied.
            columns, found = _each(queue, desk.synthetic)
            made[OUT.get(name, f"{name}.csv")] = written(columns, found)
            if name == "kinds":
                made[KINDS_COUNTS] = _counts(queue.question, found, desk.synthetic)
            for row in found if not in_gazetteer else ():
                nothing = _decides_nothing(name, row["answer"])
                (built.flagged if nothing else built.applied)[name] += 1
        built.out.update(made)
        if queue.question.private:
            built.private.update(made)
    built.out[TO_LOOK_AT] = written(LOOK_COLUMNS, _look_at(desk, built))
    built.private.add(TO_LOOK_AT)
    for name, queue in desk.queues.items():
        mine = queue.stands.get(FOUNDER, records.NOTHING).answers
        count = sum(
            1
            for item in queue.items.items
            if (line := mine.get(item.id)) is not None
            and records.by_rule(line)
            and records.fresh(line, item, queue.question)
        )
        if count:
            built.by_rule[name] = count
    return problems


def build(desk: Desk) -> Built:
    """Every file of a build, as bytes. Raises `Refused`, with every check that failed."""
    built = Built()
    problems: list[str] = []
    for name, queue in desk.queues.items():
        for reviewer, held in queue.reads.items():
            built.broken += held.broken
            if any(line.synthetic != desk.synthetic for line in held.lines):
                problems.append(
                    f"decisions/{name}/{reviewer}.jsonl holds a line of the other city. "
                    "The made-up city and London are never mixed"
                )
    if not problems:
        problems += gazetteer(desk, built)
        problems += out(desk, built)
    if problems:
        raise Refused(sorted(set(problems)))
    return built


PRIVATE: Final = "private"


def _replace(path: Path, held: bytes, *, private: bool = False) -> None:
    """Write a file whole, or not at all. A private file is the owner's alone."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if private:
        path.parent.chmod(0o700)
    partial = path.with_name(f".{path.name}.partial")
    # Made with its mode, so that a private file is never open to others, even for a moment.
    partial.unlink(missing_ok=True)
    descriptor = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600 if private else 0o644)
    try:
        left = memoryview(held)
        while left:
            left = left[os.write(descriptor, left) :]
    finally:
        os.close(descriptor)
    partial.replace(path)


def where(data: Path, built: Built, name: str) -> Path:
    """Where a file of `out` is written."""
    return data / "out" / PRIVATE / name if name in built.private else data / "out" / name


def _of_the_other_city(folder: Path, synthetic: bool) -> bool:
    """Whether a gazetteer already holds areas of the city that is not being written."""
    try:
        rows = table(AREAS, (folder / AREAS).read_bytes())
    except (FileNotFoundError, Unfit):
        return False
    return any(row["area_id"].startswith(SYNTHETIC) != synthetic for row in rows)


@dataclass(frozen=True, slots=True)
class Written:
    """What a run made, and where it was written."""

    desk: Desk
    built: Built
    # Where the curated files went, or None if none were written.
    gazetteer: Path | None


def run(data: Path, gazetteer_folder: Path | None, questions: Path) -> Written:
    """Make the files and write them. Raises `Unfit` or `Refused`, and then writes nothing.

    The files of `out/` are always written. The curated files are written to the folder
    given. The made-up city is written to `<data>/gazetteer` and nowhere else, so that
    no made-up area is ever found where a build looks for London.
    """
    desk = load(data, questions)
    built = build(desk)
    into = gazetteer_folder
    if desk.synthetic:
        into = into or data / "gazetteer"
        if data.resolve() not in into.resolve().parents:
            raise Refused(
                ["The made-up city is written under its own folder of data, and nowhere else"]
            )
    if into is not None and _of_the_other_city(into, desk.synthetic):
        raise Refused([f"{into.name}/{AREAS} holds the other city. It is not written over"])
    for name, held in built.out.items():
        _replace(where(data, built, name), held, private=name in built.private)
    # A file of an earlier run does not outlive it: what this run did not make is not
    # of today. The folder of London is committed and holds more than the desk makes,
    # so nothing is ever removed from it.
    _only(data / "out", set(built.out) - built.private)
    _only(data / "out" / PRIVATE, built.private)
    if into is not None:
        for name, held in built.gazetteer.items():
            _replace(into / name, held)
        if desk.synthetic and built.gazetteer:
            _only(into, set(built.gazetteer))
    return Written(desk, built, into if built.gazetteer else None)


def _only(folder: Path, made: set[str]) -> None:
    """Remove the plain files of a folder that this run did not make. Folders are left."""
    if not folder.is_dir():
        return
    for path in sorted(folder.iterdir()):
        if path.name not in made and path.is_file() and not path.is_symlink():
            path.unlink()
