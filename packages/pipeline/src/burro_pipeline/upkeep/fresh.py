"""What is held, and how old it is: every file that has a receipt, held to its publisher's rhythm.

It reads the registry, the lists and the receipts, and nothing else. It asks nothing of a
publisher, so it cannot know whether a newer edition is out. What it says is how long ago
a file was retrieved, against how often its publisher says the dataset changes:

    due        retrieved longer ago than its cadence. It is time to look at the page
    fresh      retrieved within its cadence, or the publisher changes it rarely
    not known  the registry does not say how often it changes, in words that are read.
               Such a file is never called fresh
    older      a file of the same item of a list was retrieved since. No build takes it
               unless it is told to
    unlisted   no list names the file. No build takes it

The day is counted from the day the file was retrieved, as its receipt states it, to the
day that is given. No clock is read.

A receipt is paired with a file of a list as `held` pairs them, and by no other rule.
A list says whether a newer edition would be let in as it stands:

    none                the list says where the file states its own edition and its
                        period. A fetch takes whatever the publisher gives now
    period              the file states its own edition, and the list states the period.
                        A person brings `data_period` forward first
    edition and period  the list states both. A fetch writes them on whatever arrives,
                        so a person brings `edition` and `data_period` forward first,
                        and the address where it names the edition
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from burro_pipeline.evidence import How, Receipt
from burro_pipeline.fetch.cli import paired
from burro_pipeline.fetch.sources import FetchList, Listed
from burro_pipeline.registry.cadence import DAYS, Cadence


class State(StrEnum):
    DUE = "due"
    FRESH = "fresh"
    NOT_KNOWN = "not_known"
    OLDER = "older"
    UNLISTED = "unlisted"


class Pins(StrEnum):
    NONE = "none"
    PERIOD = "period"
    EDITION_AND_PERIOD = "edition_and_period"
    # No list names the file, so no list says.
    NOT_LISTED = "not_listed"


# The fields of an item of a list that a person brings forward, by what the list pins.
FIELDS = {
    Pins.NONE: (),
    Pins.PERIOD: ("data_period",),
    Pins.EDITION_AND_PERIOD: ("edition", "data_period"),
    Pins.NOT_LISTED: (),
}


class Before(Exception):
    """The day that was given is before the day a file was retrieved."""


@dataclass(frozen=True)
class Held:
    """One file that has a receipt, and how it stands on the day that was given."""

    receipt: Receipt
    # The list that names the file and the name it gives it. None where no list names it.
    build: str | None
    item: str | None
    cadence: Cadence
    days: int
    state: State
    pins: Pins

    @property
    def by_hand(self) -> bool:
        return self.receipt.how is How.BY_HAND

    def line(self) -> str:
        """One line that may be read by anyone: ids, a day, counts and words of fixed lists."""
        receipt = self.receipt
        named = "" if self.build is None else f" list={self.build} item={self.item}"
        saved = " by_hand=1" if self.by_hand else ""
        return (
            f"step=fresh source={receipt.source_id}{named} file_id={receipt.file_id} "
            f"retrieved={receipt.retrieved_on} days={self.days} cadence={self.cadence} "
            f"state={self.state} pins={self.pins}{saved}"
        )


def pinned_by(file: Listed) -> Pins:
    """What an item of a list pins: what a person brings forward before a newer edition."""
    if file.edition_from is None:
        return Pins.EDITION_AND_PERIOD
    return Pins.NONE if file.edition_from.period_too else Pins.PERIOD


def _stands(cadence: Cadence, days: int) -> State:
    if cadence is Cadence.NOT_SAID:
        return State.NOT_KNOWN
    longest = DAYS.get(cadence)
    return State.DUE if longest is not None and days > longest else State.FRESH


def held(
    receipts: Sequence[Receipt],
    lists: Sequence[FetchList],
    cadences: Mapping[str, Cadence],
    on: date,
) -> list[Held]:
    """Every file that has a receipt, as it stands on a day, in the order of the receipts.

    `cadences` gives the rhythm of each source by its id. A source it does not
    hold says none. Raises `Before` where a file was retrieved after the day.
    """
    items = {(one.build, file.item): file for one in lists for file in one.files}
    found: list[tuple[Receipt, str | None, str | None]] = []
    for receipt, of in zip(receipts, paired(receipts, lists), strict=True):
        # A file that two lists name is a file of the first of them, in name order.
        build = min(of) if of else None
        found.append((receipt, build, of[build] if build is not None else None))
    # Of the files of one item, the one retrieved last is the file that is held.
    last: dict[tuple[str, str], tuple[str, str]] = {}
    for receipt, build, item in found:
        if build is not None and item is not None:
            mine = (receipt.retrieved_at, receipt.file_id)
            last[build, item] = max(last.get((build, item), mine), mine)
    out: list[Held] = []
    for receipt, build, item in found:
        days = (on - date.fromisoformat(receipt.retrieved_on)).days
        if days < 0:
            raise Before
        cadence = cadences.get(receipt.source_id, Cadence.NOT_SAID)
        if build is None or item is None:
            state, pins = State.UNLISTED, Pins.NOT_LISTED
        else:
            pins = pinned_by(items[build, item])
            newest = last[build, item] == (receipt.retrieved_at, receipt.file_id)
            state = _stands(cadence, days) if newest else State.OLDER
        out.append(Held(receipt, build, item, cadence, days, state, pins))
    return out


def counted(files: Sequence[Held]) -> dict[str, int]:
    """How many files stand each way, and how many sources say no cadence that is read."""
    counts = {state.value: 0 for state in State}
    for file in files:
        counts[file.state] += 1
    unsaid = {file.receipt.source_id for file in files if file.cadence is Cadence.NOT_SAID}
    return {"receipts": len(files), **counts, "not_said": len(unsaid)}


def _period(receipt: Receipt) -> str:
    period = receipt.data_period
    return period.as_at or f"{period.start} to {period.end}"


# What stands first in a table: what a person acts on.
ORDER = (State.DUE, State.NOT_KNOWN, State.FRESH, State.OLDER, State.UNLISTED)
SAID = {
    State.DUE: "due",
    State.NOT_KNOWN: "not known",
    State.FRESH: "fresh",
    State.OLDER: "older",
    State.UNLISTED: "unlisted",
}
HEAD = (
    "State",
    "Source",
    "List",
    "Item",
    "Edition",
    "Period",
    "Retrieved",
    "Days",
    "Cadence",
    "Bring forward",
    "Saved by hand",
)


def table(files: Sequence[Held]) -> str:
    """The same, for a person: one row for each file, with its edition and its period."""
    rows = [
        (
            SAID[file.state],
            file.receipt.source_id,
            file.build or "",
            file.item or "",
            file.receipt.edition,
            _period(file.receipt),
            file.receipt.retrieved_on,
            str(file.days),
            file.cadence.replace("_", " "),
            " and ".join(FIELDS[file.pins]) or ("" if file.build is None else "nothing"),
            "yes" if file.by_hand else "",
        )
        for file in sorted(
            files,
            key=lambda one: (
                ORDER.index(one.state),
                one.receipt.source_id,
                one.item or "",
                one.receipt.file_id,
            ),
        )
    ]
    widths = [max(len(row[at]) for row in (HEAD, *rows)) for at in range(len(HEAD))]
    lines = [
        "  ".join(cell.ljust(width) for cell, width in zip(row, widths, strict=True)).rstrip()
        for row in (HEAD, *rows)
    ]
    return "\n".join(lines)
