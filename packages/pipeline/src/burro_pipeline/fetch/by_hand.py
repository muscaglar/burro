"""Take a file that a person saved from a browser.

Some publishers will not give a file to a program. A person opens the page,
saves the file, and hands it over with the address they saved it from and the
day they saved it. It goes through the same gate, the same look at what it is
and the same store as a file that was fetched, and its receipt says `by_hand`.
Nothing here reaches a network: the address is written down, never asked.
"""

import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from burro_pipeline.evidence import How
from burro_pipeline.fetch import gate
from burro_pipeline.fetch.run import (
    Arrival,
    Outcome,
    Status,
    Why,
    keep,
    refusal,
    written_down,
)
from burro_pipeline.fetch.sources import Listed
from burro_pipeline.fetch.store import Store
from burro_pipeline.registry import Registry

A_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
A_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def saved_at(given: str, now: datetime) -> str | None:
    """When a file was saved, as a receipt holds it, or nothing if it cannot be so.

    A person knows the day and seldom the second, and a receipt holds a time.
    So a day alone is written as midnight UTC of that day. A time that has not
    come yet is refused: a day of grace allows for a clock in another zone.
    """
    try:
        if A_TIME.fullmatch(given):
            when = datetime.strptime(given, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        elif A_DAY.fullmatch(given):
            when = datetime.combine(date.fromisoformat(given), datetime.min.time(), UTC)
        else:
            return None
    except ValueError:
        return None
    if when > now.astimezone(UTC) + timedelta(days=1):
        return None
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def _may_be_written_down(address: str) -> bool:
    try:
        parts = urlsplit(address)
        return parts.scheme == "https" and bool(parts.hostname) and parts.username is None
    except ValueError:
        return False


def keep_by_hand(
    n: int,
    file: Listed,
    saved: Path,
    address: str,
    day: str,
    registry: Registry,
    store: Store,
    receipts: Path,
    now: datetime,
) -> Outcome:
    """Store a file a person saved, with a receipt marked as saved by hand.

    The file is held to the entry of its source as a fetched file is: the
    address it was saved from, the name it was saved under, and the names
    inside it. A browser may be given an address with a key in it. So the
    address is held to the entry as a receipt would hold it, with no parameter
    but those of the list's own address. What it names is read as it was given.
    """
    try:
        source = gate.ask(file, registry, store.part)
    except gate.Refused as found:
        return refusal(n, file, found, by_hand=True)

    def refused(why: Why) -> Outcome:
        return Outcome(n, file.source_id, Status.FAILED, why, by_hand=True)

    try:
        path = saved.resolve(strict=True)
        if not path.is_file():
            return refused(Why.NOT_A_FILE)
        size = path.stat().st_size
    except OSError:
        return refused(Why.NOT_A_FILE)
    if size > file.max_bytes:
        return refused(Why.TOO_LARGE)
    if not _may_be_written_down(address):
        return refused(Why.ADDRESS_GIVEN)
    retrieved_at = saved_at(day, now)
    if retrieved_at is None:
        return refused(Why.DAY_GIVEN)
    try:
        as_a_receipt_holds_it = written_down(address, file.url)
    except ValueError:
        return refused(Why.ADDRESS_GIVEN)
    try:
        gate.hold_what_arrived(source, address)
        gate.hold_the_address(source, as_a_receipt_holds_it)
        gate.hold_the_file(source, path, saved.name)
    except gate.Refused as found:
        return refusal(n, file, found, by_hand=True)
    arrival = Arrival(path, saved.name, address, retrieved_at, How.BY_HAND)
    return keep(n, file, arrival, store, receipts)
