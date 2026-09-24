"""Fetch the files of a list: ask the gate, download, store, write the receipt.

The order is fixed. The licence registry is asked about every file of the list
before anything is asked of a publisher, and each file is held to the entry of
its source. One refusal stops every download. The gate is asked again as the
first thing done for each file. A file is looked at before it is kept, so that
a sign-in page is never stored as a dataset, and so that nothing is kept that
names a table its entry may not hold, or that cannot be looked into. The
receipt is written last. It holds the address the list gave and the address
the file came from in the end, and is written only
from an edition and a period that somebody is sure of.

What a run says is a line of `key=value` for each file: the step, the source,
a status, a hash, counts. A reason is a number, from the table in `WORDS`.
No line holds an address, a row, a key or anything a publisher or the store said.
Two things a person needs to mend a fetch are said in a form that gives nothing
away: what arrived in place of a file, as one word from the list of kinds, and
the host a request was sent on to, as the start of a hash of its name.
"""

import hashlib
import tempfile
import time
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import ValidationError

from burro_pipeline.evidence import How, Receipt, clean_url, file_id_of
from burro_pipeline.evidence.receipt import RECEIPTS_FOLDER
from burro_pipeline.fetch import gate
from burro_pipeline.fetch.download import Downloaded, DownloadRefused, Limits, Reason, download
from burro_pipeline.fetch.kinds import Kind, sniff
from burro_pipeline.fetch.sources import Listed
from burro_pipeline.fetch.store import Held, Part, Store, StoreError
from burro_pipeline.registry import Registry

STEP = "fetch"


class Status(StrEnum):
    OK = "ok"
    SKIPPED = "skipped"
    REFUSED = "refused"
    FAILED = "failed"
    MISSING = "missing"
    UNREADABLE = "unreadable"
    DIFFERS = "differs"


class Why(IntEnum):
    """Why a file was not fetched, or not given a receipt. The number is what is printed."""

    GATE = 1
    ANOTHER_WAS_REFUSED = 2
    NO_ADDRESS = 3
    NOT_SAVED_BY_HAND = 4
    NOT_THE_FORMAT = 5
    NOT_SURE = 6
    RECEIPT_DIFFERS = 7
    STORE = 8
    NOT_A_FILE = 9
    ADDRESS_GIVEN = 10
    DAY_GIVEN = 11
    NOT_THE_PAGE = 12
    NOT_THE_HOST = 13
    RESIDENT_TABLE = 14
    NOT_THE_STORE = 15
    KEPT_RECEIPT_DIFFERS = 16
    FAULT = 17
    NOT_THE_ADDRESS = 18
    CANNOT_SEE_INSIDE = 19
    NOT_HTTPS = 20
    BAD_ADDRESS = 21
    NOT_PUBLIC = 22
    NO_CONNECTION = 23
    NOT_SECURE = 24
    TIMED_OUT = 25
    BAD_ANSWER = 26
    STATUS = 27
    REDIRECT_ELSEWHERE = 28
    TOO_MANY_REDIRECTS = 29
    TOO_LARGE = 30
    CUT_SHORT = 31
    NOT_WRITTEN = 32
    NOT_ASCII = 33


# Each says what happened, and then what a person can do about it.
WORDS: dict[Why, str] = {
    Why.GATE: "The licence registry refuses this source for this use. Nothing was asked for",
    Why.ANOTHER_WAS_REFUSED: "Another file of the list was refused by the registry, or is not "
    "as its registry entry has it, so none was fetched",
    Why.NO_ADDRESS: "The list holds no address for the file. Find it on the page, or save the "
    "file by hand",
    Why.NOT_SAVED_BY_HAND: "The file is saved by hand, and no receipt of it was found. Save it "
    "from its page, and hand it over with the step by-hand",
    Why.NOT_THE_FORMAT: "What arrived is not the format listed. It may be a web page. It was "
    "not stored. The line says what it was after kind=, as one word: html is a web page. "
    "Open the address in a browser: if it asks for a sign-in or for terms to be accepted, "
    "save the file by hand",
    Why.NOT_SURE: "The file is stored. No receipt was written, because the list does not state "
    "its edition and its period, or is not sure of them. State both in the list and fetch again",
    Why.RECEIPT_DIFFERS: "A receipt of this file exists and says something else. It was left "
    "as it is. Compare the list with the receipt: one of them has the edition, the period or "
    "the use wrong",
    Why.STORE: "The store refused, or could not be reached. See that it is named as the "
    "step's help says, and that its key may do what the step does",
    Why.NOT_A_FILE: "The path given is not a file that can be read",
    Why.ADDRESS_GIVEN: "The address given is not an https address, or holds a login, a key "
    "or `;`. Nothing was kept. Give the address of the file as the list or the registry "
    "entry has it",
    Why.DAY_GIVEN: "The day given is not a day, or has not come yet",
    Why.NOT_THE_PAGE: "The page the list gives for this file is not one that the registry "
    "entry of its source holds. Nothing was asked for. Copy the page from the entry: its own "
    "address, or one of its evidence addresses",
    Why.NOT_THE_HOST: "The address of the file is on a host that the registry entry of its "
    "source does not name. Nothing was asked for, or nothing was kept. Look at the address in "
    "the list. If the publisher keeps the files of this source on that host, name the file's "
    "address under `file_urls` in the entry, in a change that a person reads",
    Why.RESIDENT_TABLE: "The file names a census table about residents, in the list, in its "
    "address or in its own name, and its source is not under residents. Nothing was asked "
    "for, or nothing was kept. Such a table is fetched under the entry for residents and "
    "under no other (ADR 0014)",
    Why.NOT_THE_STORE: "The file is read for the audit, or is a census table about residents. "
    "Each is kept in a store of its own, named by variables of its own, which the key of a "
    "product build cannot read (ADR 0015). No such store is built, so the file cannot be "
    "fetched or handed over. Nothing was asked for, and nothing was kept",
    Why.KEPT_RECEIPT_DIFFERS: "A receipt of this file is kept in the store, and it says "
    "something else than the list does now, or it cannot be read as a receipt. It was left as "
    "it is, and no receipt was written. Bring it back with the step receipts and compare it "
    "with the list: one of them has the edition, the period or the use wrong",
    Why.FAULT: "Fetch stopped on a fault of its own while it worked on this file, and went "
    "on to the next. Only the kind of the fault is said. To see where it came from, run the "
    "step for this item on a machine of your own with BURRO_FETCH_DEBUG=1",
    Why.NOT_THE_ADDRESS: "The address of the file is not one that the registry entry of its "
    "source names under `file_urls`, or the publisher sent the request on to an address that "
    "the entry does not hold, or to one that can be read more than one way. Nothing was asked "
    "for, or nothing was kept. A publisher keeps many "
    "datasets on one host, so an entry names the address of each of its files, or a prefix "
    "that ends at its dataset. If this is a file of this source, name its address there, in "
    "a change that a person reads. Never widen a prefix to make a fetch pass",
    Why.CANNOT_SEE_INSIDE: "The file is a zip, or holds one, that could not be looked into: "
    "it is cut short, locked with a password, nested more than four zips deep, or its zips "
    "unpack to more than is looked into. Nothing was kept, because what it holds cannot be "
    "held to the registry entry of its source. Open it on a machine of your own and see "
    "what it holds",
    Why.NOT_HTTPS: "The address is not https. List the file's https address",
    Why.BAD_ADDRESS: "The address could not be read, or holds a login. Look at it in the list",
    Why.NOT_PUBLIC: "The address is not a public one. Look at it in the list",
    Why.NO_CONNECTION: "The publisher could not be reached. Try again later",
    Why.NOT_SECURE: "The secure connection failed. Try again later, and do not turn the check off",
    Why.TIMED_OUT: "The publisher was too slow. Try again later",
    Why.BAD_ANSWER: "The answer could not be read, or the address the file came from in the "
    "end holds `;`, which may stand before a key. Nothing was kept. Try again later, or save "
    "the file by hand",
    Why.STATUS: "The publisher answered with a status that is not 200, given as http=. For 404 "
    "look at the address in the list. For 401, 403 or 429 the publisher refuses a program: "
    "save the file by hand",
    Why.REDIRECT_ELSEWHERE: "The publisher sent the request on to another host. Name that host "
    "in the list under may_redirect_to, or list the file's final address. The line gives the "
    "start of a hash of the host's name after host=, and never the name. To see that a host is "
    "the one, name it in the list and run plan --words, which prints the same beside each host",
    Why.TOO_MANY_REDIRECTS: "The publisher sent the request on too many times. List the file's "
    "final address",
    Why.TOO_LARGE: "The file is over the size the list states for it. If it is the right file, "
    "raise max_bytes in the list",
    Why.CUT_SHORT: "The file stopped before its end. Try again",
    Why.NOT_WRITTEN: "The file could not be written to disk. See that the disk has room",
    Why.NOT_ASCII: "The address, or one the publisher sent the request on to, holds a letter "
    "outside ASCII. Nothing was asked of that address. Write the address in the list as a "
    "browser sends it, with each such letter percent-encoded, or save the file by hand",
}

OF_A_DOWNLOAD = {reason: Why[reason.name] for reason in Reason}
_OF_THE_GATE = {reason: Why[reason.name] for reason in gate.Reason}
# How much of the hash of a host's name is printed. Enough to tell the hosts of a list apart.
HOST_DIGITS = 12


def host_mark(host: str) -> str:
    """What stands for a host in a line that anyone may read: the start of a hash of its name.

    A line never holds a host's name. A person who thinks they know the host
    names it in the list, and `plan --words` prints the same digits beside it.
    """
    name = host.lower().rstrip(".")
    return hashlib.sha256(name.encode()).hexdigest()[:HOST_DIGITS]


class Downloader(Protocol):
    def __call__(
        self,
        address: str,
        to: Path,
        limits: Limits,
        *,
        agent: str,
        may_redirect_to: tuple[str, ...] = (),
    ) -> Downloaded: ...


@dataclass(frozen=True)
class Outcome:
    """What became of one file of the list."""

    n: int
    source_id: str
    status: Status
    why: Why | None = None
    held: Held | None = None
    new: bool = False
    http: str = ""
    # For a person at a terminal. Never part of `line`.
    detail: str = ""
    seconds: float = 0.0
    by_hand: bool = False
    # What arrived in place of the file, where it was not kept for what it is.
    kind: Kind | None = None
    # The host a request was sent on to, as `host_mark` gives it. Never its name.
    host: str = ""

    @property
    def done(self) -> bool:
        return self.status is Status.OK

    def line(self) -> str:
        """The one line a run prints for this file: keys, numbers and hashes."""
        parts = [f"step={STEP}", f"n={self.n}", f"source={self.source_id}", f"status={self.status}"]
        if self.held is not None:
            held = self.held
            parts += [f"file_id={held.file_id}", f"sha256={held.sha256}", f"bytes={held.bytes}"]
            parts.append(f"new={int(self.new)}")
        if self.by_hand:
            parts.append("by_hand=1")
        if self.why is not None:
            parts.append(f"why={int(self.why)}")
        if self.http:
            parts.append(f"http={self.http}")
        if self.kind is not None:
            parts.append(f"kind={self.kind}")
        if self.host:
            parts.append(f"host={self.host}")
        parts.append(f"seconds={self.seconds:.1f}")
        return " ".join(parts)

    def words(self) -> str:
        """The reason in words, for a person at a terminal."""
        if self.why is None:
            return ""
        return f"{WORDS[self.why]}{f' ({self.detail})' if self.detail else ''}."


def summary(outcomes: Sequence[Outcome]) -> str:
    counts = {
        status: sum(1 for outcome in outcomes if outcome.status is status) for status in Status
    }
    status = Status.OK if all(outcome.done for outcome in outcomes) else Status.FAILED
    each = " ".join(f"{name.value}={count}" for name, count in counts.items())
    return f"step={STEP} status={status} files={len(outcomes)} {each}"


def timestamp(now: datetime) -> str:
    return now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def refusal(n: int, file: Listed, refused: gate.Refused, by_hand: bool = False) -> Outcome:
    """What became of a file that the gate did not let through."""
    why = _OF_THE_GATE[refused.reason]
    return Outcome(n, file.source_id, Status.REFUSED, why, detail=refused.detail, by_hand=by_hand)


def fault(n: int, file: Listed, found: Exception) -> Outcome:
    """What became of a file that fetch stopped on, by a fault of its own.

    What a fault says may hold a row or an address. So only its kind is kept,
    and that is said to a person at a terminal and never in a line.
    """
    return Outcome(n, file.source_id, Status.FAILED, Why.FAULT, detail=type(found).__name__)


def _stopped_at_the_gate(
    files: Sequence[Listed], registry: Registry, part: Part, debug: bool
) -> dict[int, Outcome]:
    """What became of each file that did not pass the gate. Nothing is asked for if any did not."""
    stopped: dict[int, Outcome] = {}
    for n, file in enumerate(files, start=1):
        try:
            gate.ask(file, registry, part)
        except gate.Refused as refused:
            stopped[n] = refusal(n, file, refused)
        except Exception as found:
            if debug:
                raise
            stopped[n] = fault(n, file, found)
    return stopped


def fetch(
    files: Sequence[Listed],
    registry: Registry,
    store: Store,
    receipts: Path,
    *,
    agent: str,
    only: Collection[str] = (),
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    downloader: Downloader = download,
    clock: Callable[[], float] = time.monotonic,
    said: Callable[[Outcome], None] = lambda _: None,
    debug: bool = False,
) -> list[Outcome]:
    """Fetch the files of a list. `said` is called with each outcome as it is known.

    `files` is the whole list, and `only` names the items wanted where that is
    not every one. The gate is asked about the whole list all the same: a list
    with a file that is refused is no list to fetch from.

    A fault of fetch's own in one file fails that file, and the run goes on to
    the next. With `debug` the fault is raised, for a developer who asks.
    """
    stopped = _stopped_at_the_gate(files, registry, store.part, debug)
    outcomes: list[Outcome] = []
    for n, file in enumerate(files, start=1):
        started = clock()
        wanted = not only or file.item in only
        if n in stopped:
            outcome = stopped[n]
        elif not wanted:
            continue
        elif stopped:
            outcome = Outcome(n, file.source_id, Status.SKIPPED, Why.ANOTHER_WAS_REFUSED)
        else:
            try:
                outcome = _fetch_one(n, file, registry, store, receipts, agent, now, downloader)
            except Exception as found:
                if debug:
                    raise
                outcome = fault(n, file, found)
        outcome = replace(outcome, seconds=max(clock() - started, 0.0))
        outcomes.append(outcome)
        said(outcome)
    return outcomes


def _fetch_one(
    n: int,
    file: Listed,
    registry: Registry,
    store: Store,
    receipts: Path,
    agent: str,
    now: Callable[[], datetime],
    downloader: Downloader,
) -> Outcome:
    try:
        source = gate.ask(file, registry, store.part)
    except gate.Refused as refused:
        return refusal(n, file, refused)
    if file.by_hand:
        return _saved_by_hand(n, file, receipts)
    if not file.has_an_address:
        return Outcome(n, file.source_id, Status.MISSING, Why.NO_ADDRESS)

    with tempfile.TemporaryDirectory(prefix="burro-fetch-") as folder:
        arrived = Path(folder) / "arrived"
        try:
            got = downloader(
                file.url,
                arrived,
                Limits(max_bytes=file.max_bytes),
                agent=agent,
                may_redirect_to=file.may_redirect_to,
            )
        except DownloadRefused as stopped:
            why = OF_A_DOWNLOAD[stopped.reason]
            http = stopped.detail if stopped.reason is Reason.STATUS else ""
            detail = stopped.detail if stopped.reason is Reason.REDIRECT_ELSEWHERE else ""
            host = host_mark(detail) if detail else ""
            return Outcome(
                n, file.source_id, Status.FAILED, why, http=http, detail=detail, host=host
            )
        try:
            gate.hold_where_it_ended(source, registry, got.final_url)
            gate.hold_the_file(source, arrived, got.final_url, got.file_name)
        except gate.Refused as refused:
            return refusal(n, file, refused)
        arrival = Arrival(arrived, got.file_name, got.final_url, timestamp(now()), How.FETCHED)
        return keep(n, file, arrival, store, receipts)


@dataclass(frozen=True)
class Arrival:
    """A file that has arrived, by download or by hand, and is not yet stored."""

    path: Path
    name: str
    address: str
    retrieved_at: str
    how: How


def keep(n: int, file: Listed, arrival: Arrival, store: Store, receipts: Path) -> Outcome:
    """Look at a file that has arrived, store it, and write its receipt."""
    by_hand = arrival.how is How.BY_HAND
    found = sniff(arrival.path)
    expected = file.format.kind
    if (expected is not None and found is not expected) or found in (Kind.HTML, Kind.EMPTY):
        return Outcome(
            n, file.source_id, Status.UNREADABLE, Why.NOT_THE_FORMAT, by_hand=by_hand, kind=found
        )
    try:
        address = written_down(arrival.address, file.url)
    except ValueError:
        # An address that cannot be read, or that may hold a key. Nothing is kept from it.
        why = Why.ADDRESS_GIVEN if by_hand else Why.BAD_ANSWER
        return Outcome(n, file.source_id, Status.FAILED, why, by_hand=by_hand)
    try:
        held, new = store.put(file.source_id, arrival.name, arrival.path)
    except StoreError as error:
        return Outcome(
            n, file.source_id, Status.FAILED, Why.STORE, detail=str(error), by_hand=by_hand
        )
    if not file.ready_for_a_receipt or file.data_period is None:
        return Outcome(n, file.source_id, Status.MISSING, Why.NOT_SURE, held, new, by_hand=by_hand)
    try:
        receipt = Receipt(
            file_id=file_id_of(held.sha256),
            source_id=file.source_id,
            use=file.use,
            publisher_file=held.name,
            url=address,
            listed_url=written_down(file.url, file.url) if file.url else None,
            sha256=held.sha256,
            bytes=held.bytes,
            retrieved_at=arrival.retrieved_at,
            how=arrival.how,
            edition=file.edition,
            data_period=file.data_period,
        )
    except ValueError:
        # A receipt that does not hold together.
        why = Why.ADDRESS_GIVEN if by_hand else Why.BAD_ANSWER
        return Outcome(n, file.source_id, Status.FAILED, why, held, new, by_hand=by_hand)
    detail = ""
    try:
        status, why = settle(receipt, receipts, store)
    except StoreError as error:
        status, why, detail = Status.FAILED, Why.STORE, str(error)
    return Outcome(n, file.source_id, status, why, held, new, detail=detail, by_hand=by_hand)


def written_down(address: str, listed: str) -> str:
    """An address as a receipt holds it: with no parameter but those of the list's own address.

    A receipt is committed where anyone reads it. A publisher may send a
    download on to an address that holds a key, under a name nobody has thought
    of, or under a name the list holds. So a parameter is kept only with the
    value that the list's own address gives it, and as many times as the list
    gives it, which is once. What is left is cleaned as every address in a
    receipt is.

    An address with `;` in its path or among its parameters is refused. Some
    servers read what follows `;` as a parameter, and it is read here as part
    of a path or of a value, so a key behind it would be kept.

    A key written into the path itself cannot be told from the path. It is kept.
    """
    parts = urlsplit(address)
    if ";" in parts.path or ";" in parts.query:
        raise ValueError("an address holds `;`, and what follows it may be a key")
    given = parse_qsl(urlsplit(listed).query, keep_blank_values=True)
    kept: list[tuple[str, str]] = []
    for pair in parse_qsl(parts.query, keep_blank_values=True):
        if pair in given:
            given.remove(pair)
            kept.append(pair)
    return clean_url(urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(kept), "")))


def settle(receipt: Receipt, receipts: Path, store: Store) -> tuple[Status, Why | None]:
    """Write a receipt to the folder and keep a copy in the store, unless one stands that differs.

    The first receipt of a file stands, in the folder and in the store. A
    hosted run starts with an empty folder, so the folder alone cannot say
    whether a receipt stands: the copy in the store is read back and compared
    too. If either says something else, nothing is written. A run must never
    say ok of a receipt that it dropped.
    """
    path = receipts / receipt.path().relative_to(RECEIPTS_FOLDER)
    try:
        on_disk = path.read_bytes() if path.exists() else None
    except OSError:
        return Status.FAILED, Why.NOT_WRITTEN
    if on_disk is not None and not _says_the_same(on_disk, receipt):
        return Status.DIFFERS, Why.RECEIPT_DIFFERS
    kept = store.receipt(receipt.kept_key())
    if kept is not None and not _says_the_same(kept, receipt):
        return Status.DIFFERS, Why.KEPT_RECEIPT_DIFFERS
    # The receipt that stands in the store is the one a new disk is given.
    first = receipt if kept is None else Receipt.model_validate_json(kept)
    status, why = write_receipt(first, receipts)
    if status is not Status.OK or kept is not None:
        return status, why
    standing = keep_in_the_store(receipt, receipts, store)
    # Another run may have kept its receipt since this one looked. It is read back too.
    kept = store.receipt(receipt.kept_key())
    if kept is None or not _says_the_same(kept, standing):
        return Status.DIFFERS, Why.KEPT_RECEIPT_DIFFERS
    return Status.OK, None


def _says_the_same(written: bytes, receipt: Receipt) -> bool:
    """Whether what is written is a receipt, and says of the file what `receipt` says."""
    try:
        found = Receipt.model_validate_json(written)
    except ValidationError:
        return False
    return not found.made_up and _same_file(found, receipt)


def keep_in_the_store(receipt: Receipt, receipts: Path, store: Store) -> Receipt:
    """Keep a copy of the receipt that stands, beside its file in the store. Returns it.

    A hosted run writes a receipt to a machine that is thrown away, so the copy
    in the store is the one that lasts. What is kept is the receipt as it
    stands on disk, which is the first ever written of the file.
    """
    path = receipts / receipt.path().relative_to(RECEIPTS_FOLDER)
    try:
        standing = Receipt.model_validate_json(path.read_bytes())
    except (OSError, ValidationError):
        raise StoreError("the receipt could not be read back from disk") from None
    store.keep_receipt(standing.kept_key(), standing.canonical())
    return standing


def _same_file(one: Receipt, other: Receipt) -> bool:
    """Whether two receipts say the same of one file, whenever and however each was got."""
    left, right = (
        receipt.model_dump(
            exclude={"retrieved_at", "url", "listed_url", "how", "geography", "members"}
        )
        for receipt in (one, other)
    )
    return left == right


def write_receipt(receipt: Receipt, receipts: Path) -> tuple[Status, Why | None]:
    """Write a receipt where the evidence looks for it. The first receipt of a file stands.

    `receipts` is the folder of receipts, which in the repository is `data/receipts`.
    """
    path = receipts / receipt.path().relative_to(RECEIPTS_FOLDER)
    try:
        if path.exists():
            before = Receipt.model_validate_json(path.read_bytes())
            same = _same_file(before, receipt)
            return (Status.OK, None) if same else (Status.DIFFERS, Why.RECEIPT_DIFFERS)
        path.parent.mkdir(parents=True, exist_ok=True)
        part = path.with_name(f".{path.name}.part")
        part.write_bytes(receipt.canonical())
        part.replace(path)
    except ValidationError:
        return Status.DIFFERS, Why.RECEIPT_DIFFERS
    except OSError:
        return Status.FAILED, Why.NOT_WRITTEN
    return Status.OK, None


def _saved_by_hand(n: int, file: Listed, receipts: Path) -> Outcome:
    """A file that a person saves is not fetched. It is looked for among the receipts.

    Its receipt is one that was saved by hand under its source, and that says
    what the list says of the file: its edition, its period and its use. A
    list holds no hash, no size and no name of a file, so a receipt is known
    by these alone. Where a receipt of that edition says another period or
    another use, the list and the receipt differ, and the run must not say ok.
    """
    folder = receipts / file.source_id
    of_the_edition = False
    for path in sorted(folder.glob("f-*.json")) if folder.is_dir() else []:
        try:
            receipt = Receipt.model_validate_json(path.read_bytes())
        except (OSError, ValidationError):
            continue
        if receipt.how is not How.BY_HAND or receipt.source_id != file.source_id:
            continue
        if receipt.edition != file.edition:
            continue
        of_the_edition = True
        if receipt.use is file.use and receipt.data_period == file.data_period:
            held = Held(receipt.source_id, receipt.sha256, receipt.publisher_file, receipt.bytes)
            return Outcome(n, file.source_id, Status.OK, held=held, by_hand=True)
    if of_the_edition:
        return Outcome(n, file.source_id, Status.DIFFERS, Why.RECEIPT_DIFFERS, by_hand=True)
    return Outcome(n, file.source_id, Status.MISSING, Why.NOT_SAVED_BY_HAND, by_hand=True)
