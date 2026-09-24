"""Make the copy of the decisions that may be published.

The lines of a decision are kept under `data/raw/`, which git ignores, and hold more than
may be published: the second a line was written, and how long its item was on screen,
say when a person was at the desk, night by night. Some queues are never published at
all: they say where a person knows a place well, or how they judged words about a real
area.

`build` is a pure function of the items and the lines. It reads no clock and no network,
and the same lines give the same bytes. It takes only the queues whose question says
`public: true`, only the lines that stand today, and of each line only what the design
says may be published: the day and never the hour, and not the time on screen. The
made-up city is never published.

A note may hold what should not be published. So every note is handed back, once, for
a person to read before they commit.

Standard library only. See docs/design/desk.md, section 3.
"""

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from desk import compile as make
from desk import records
from desk.records import MOVE, Json, Line

# The fields of a published line, in the order they are written. `at` is cut to the day.
# `seconds` and `undoes` are left out: the first says how a person works, and no line
# that was taken back is published.
FIELDS: Final = (
    *("n", "at", "reviewer", "queue", "question", "item", "rev", "part"),
    *("answer", "note", "second", "settles", "detail", "synthetic"),
)
TREE: Final = records.PUBLIC_TREE


class Refused(Exception):
    """Nothing may be published, so nothing was written."""


@dataclass(frozen=True, slots=True)
class Published:
    """What a run would write, or wrote."""

    # The bytes of each file, by queue and then by reviewer.
    files: Mapping[tuple[str, str], bytes]
    # Every note in them, each once, in order.
    notes: tuple[str, ...]
    lines: int

    @property
    def queues(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(queue for queue, _ in self.files))


def as_published(line: Line) -> dict[str, Json]:
    """One line as it is published: the day it was written, and not the hour."""
    held = line.as_dict()
    return {name: line.day if name == "at" else held[name] for name in FIELDS}


def _standing(queue: make.Queue) -> Iterator[tuple[str, list[Line]]]:
    """Each reviewer's lines that stand today and decide or move, in the order written."""
    for reviewer in sorted(queue.stands, key=records.number_of):
        held = queue.stands[reviewer]
        found = [
            *held.answers.values(),
            *(m for moves in held.moves.values() for m in moves.values()),
        ]
        kept = [
            line
            for line in found
            if (line.decides or line.answer == MOVE)
            and line.item in queue.items.by_id
            and records.fresh(line, queue.items.by_id[line.item], queue.question)
        ]
        if kept:
            yield reviewer, sorted(kept, key=lambda line: line.n)


def build(desk: make.Desk) -> Published:
    """Every file of the published copy, as bytes. Raises `Refused` for the made-up city."""
    if desk.synthetic:
        raise Refused("The made-up city is never published")
    files: dict[tuple[str, str], bytes] = {}
    notes: set[str] = set()
    count = 0
    for name, queue in desk.queues.items():
        if not queue.question.public:
            continue
        for reviewer, lines in _standing(queue):
            if any(line.synthetic for line in lines):
                raise Refused("A line of the made-up city is among those of London")
            text = "".join(
                json.dumps(as_published(line), ensure_ascii=False, separators=(",", ":")) + "\n"
                for line in lines
            )
            files[name, reviewer] = text.encode("utf-8")
            notes.update(line.note for line in lines if line.note)
            count += len(lines)
    return Published(files, tuple(sorted(notes)), count)


def run(data: Path, to: Path, questions: Path) -> Published:
    """Make the copy and write it under `<to>/decisions/`. Raises `Unfit` or `Refused`, and
    then writes nothing. A file of an earlier run that this one did not make is removed."""
    found = build(make.load(data, questions))
    tree = to / TREE
    for (queue, reviewer), held in found.files.items():
        path = tree / queue / f"{reviewer}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_name(f".{path.name}.partial")
        partial.write_bytes(held)
        partial.chmod(0o644)
        partial.replace(path)
    made = {tree / queue / f"{reviewer}.jsonl" for queue, reviewer in found.files}
    for path in sorted(tree.glob("*/r*.jsonl")) if tree.is_dir() else ():
        if path not in made and path.is_file() and not path.is_symlink():
            path.unlink()
    return found
