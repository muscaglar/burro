"""Filling the queues of the review desk: part (c) of docs/design/desk.md, section 8.

A queue is a file of items that a step makes from data. `run` fills every queue from a
draft folder, or from the synthetic release, and says for each how many items it holds
and how long they would take at the pace the design gives.

The licence gate is asked about every source before anything is written, and one refusal
leaves the folder as it was. Nothing here touches `<data>/decisions/`.

Standard library only, but for the licence gate on real files: see `gate.py`.
"""

import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from desk.fill import draft, layers
from desk.fill import synthetic as made_up
from desk.fill.draft import Draft
from desk.fill.gate import Refused
from desk.fill.layers import Unfit

__all__ = ["PACE", "Refused", "Report", "Unfit", "fill", "run", "say"]

# The pace of the design, section 1. The step that makes the items holds it: a rule says
# how long the items it would settle would take.
ITEM, GROUP, PACE = draft.ITEM, draft.GROUP, draft.PACE
OK, REFUSED = 0, 2


@dataclass(frozen=True)
class Filled:
    """One queue, as it was filled."""

    queue: str
    items: int
    flagged: int
    groups: int
    # Why the queue was not filled: the files the draft does not hold. Empty if it was.
    lacks: tuple[str, ...] = ()

    @property
    def seconds(self) -> int:
        each, of = PACE[self.queue]
        return each * (self.groups if of == GROUP else self.items)


@dataclass(frozen=True)
class Report:
    synthetic: bool
    queues: tuple[Filled, ...]
    layers: int
    # How many names of areas stand by a rule the founder has decided already. The draft
    # says so of each, and no item is made of it.
    stands: int = 0

    @property
    def items(self) -> int:
        return sum(queue.items for queue in self.queues)


def _of_the_other_city(data: Path, synthetic: bool) -> bool:
    """Whether a folder already holds items of the city that is not being filled."""
    for path in sorted(data.glob("items/*.jsonl")):
        with path.open(encoding="utf-8") as file:
            first = file.readline()
        try:
            if json.loads(first)["synthetic"] is not synthetic:
                return True
        except (ValueError, KeyError, TypeError):
            continue
    return False


def _replace(path: Path, text: str) -> None:
    """Write a file whole, or not at all."""
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f".{path.name}.partial")
    partial.write_text(text, encoding="utf-8")
    partial.replace(path)


def fill(
    source: Path,
    data: Path,
    *,
    synthetic: bool,
    made_on: str | None = None,
    registry: Path | None = None,
) -> Report:
    """Fill every queue the draft can fill. Raises `Unfit` or `Refused`, and then writes no
    item and no layer.

    With `synthetic`, `source` is the synthetic release, and its draft is made first, in
    `<data>/draft`. Without, `source` is the draft folder of real files, `<data>/draft`.
    """
    if _of_the_other_city(data, synthetic):
        raise Unfit(
            "That folder holds the other city: the made-up city and London are never "
            "filled into one folder"
        )
    if synthetic:
        made_on = made_on or made_up.made_on(source)
        made_up.make(source, data / "draft")
        source = data / "draft"
    elif not source.is_dir():
        raise Unfit("There is no draft folder there to fill the queues from")
    elif source.resolve() != (data / "draft").resolve():
        # The step that makes a build's files reads the draft from there, and from nowhere else.
        raise Unfit("A draft of real files is kept in the folder draft, inside the data folder")
    held = Draft.open(source, synthetic=synthetic, registry=registry)
    draft.hold_to_rule_8(held)
    made_on = made_on or datetime.now(UTC).date().isoformat()
    asks = draft.questions()
    written: dict[str, str] = {}
    filled: list[Filled] = []
    for queue in draft.QUEUES:
        lacks = draft.missing(held, queue)
        if lacks:
            filled.append(Filled(queue, 0, 0, 0, tuple(lacks)))
            continue
        draft.ask(held, queue, registry)
        text = draft.fill(held, queue, made_on, asks[queue])
        items = [json.loads(line) for line in text.splitlines()[1:]]
        written[queue] = text
        filled.append(
            Filled(
                queue,
                len(items),
                sum(bool(item["flags"]) for item in items),
                len({item["group"] for item in items}),
            )
        )
    drawn = layers.copy(held.drawn, data, synthetic=synthetic, registry=registry)
    for queue, text in written.items():
        _replace(data / "items" / f"{queue}.jsonl", text)
    stands = len(draft.stands(held)) if "names" in written else 0
    return Report(synthetic, tuple(filled), drawn, stands)


def _long(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} s"
    if seconds < 90 * 60:
        return f"{round(seconds / 60)} min"
    return f"{seconds / 3600:.1f} h"


def _pace(queue: str) -> str:
    each, of = PACE[queue]
    return f"{_long(each)} an {of}" if of == ITEM else f"{_long(each)} an article"


def say(report: Report, out: TextIO) -> None:
    """Say of each queue how many items it holds, and how long they would take.

    Only counts are said. No name, no id and no word of a file is printed.
    """
    city = "the made-up city" if report.synthetic else "real data for London"
    out.write(f"Filled from {city}. {report.layers} layers.\n")
    out.write(f"{'queue':<10} {'items':>6} {'flagged':>8}   {'pace':<17} {'time':>8}\n")
    for queue in report.queues:
        if queue.lacks:
            out.write(f"{queue.queue:<10} not filled: the draft has no {', '.join(queue.lacks)}\n")
            continue
        out.write(
            f"{queue.queue:<10} {queue.items:>6} {queue.flagged:>8}   "
            f"{_pace(queue.queue):<17} {_long(queue.seconds):>8}\n"
        )
    total = sum(queue.seconds for queue in report.queues)
    out.write(f"{'all':<10} {report.items:>6} {'':>8}   {'':<17} {_long(total):>8}\n")
    if report.stands:
        one = report.stands == 1
        spared = _long(report.stands * PACE["names"][0])
        out.write(
            f"{report.stands} {'name of an area stands' if one else 'names of areas stand'} "
            f"by a rule the founder has decided, and {'is' if one else 'are'} not asked "
            f"about: {spared} at the pace of names.\n"
        )
    out.write("The pace is the design's guess. Nobody has timed it.\n")


def run(source: Path, data: Path, *, synthetic: bool) -> int:
    """Fill the queues and say what was filled. Returns 0, or 2 where nothing was written.

    A refusal is said in one line on standard error: what is wrong, in words.
    """
    try:
        report = fill(source, data, synthetic=synthetic)
    except (Unfit, Refused) as error:
        sys.stderr.write(f"Not filled. {str(error).rstrip('.')}.\n")
        return REFUSED
    say(report, sys.stdout)
    return OK
