"""The lock: every input a build is made from, by hash, and the step that seals it.

`seal` writes the lock before a build starts. It takes the list of the build,
and holds the folder of receipts to it: every file the list names has its
receipt, and no receipt is there that the list does not name. It asks the
licence gate about every file again, because a source can lose its approval
after it was fetched.
It refuses a file that is kept for the audit or for the census table, which
the gate lets through. A build then reads nothing the lock does not name:
`Lock.admit` hashes what it is handed and refuses it if the hash is not there.

A file that states its own edition. A publisher that replaces a file under one
address leaves the list no edition to state, so the list says where the file
states its own, and fetch writes the receipt from what it reads there. The
store may then hold several editions of one file of the list, each with its
receipt. Which one a build takes is this rule, and `take` is the one place
that applies it:

1. A receipt is of the item when fetch could have written it from the item: it
   gives the item's source and use, the list's own address for the file, the
   place the list says the edition is read in, and an edition that is the
   list's words and then a day or a time. Where the file gives the edition
   alone, the period is the list's, and the receipt gives that too.
2. A build takes the edition it is told to take, named as the receipt writes
   it. Told nothing, it takes the newest: the one whose edition states the
   latest day. The day is the one the file states. It is never the day the
   file was retrieved, and never the order of a folder.
3. The lock says what was taken: beside the hash of such a file, the name the
   list gives the file and the edition of the receipt. So the lock alone says
   what was read, and a build that is told to take the editions a lock names
   seals that lock again, whatever has arrived since.
4. Two receipts of one item that state one edition stop the build: one edition
   is one file, and nothing says which of the two is meant. So does an edition
   that is named and that no receipt states.

Every lock is the lock of a product release. The step that builds the census
table, and the audit, are not built, and neither will read this lock.

The lock names the code by its commit. In a repository `seal` reads the commit
that is checked out, and refuses a working copy with changes. It is in a
repository when the folder it is given, or any folder above it, is the top of
a working copy.

A refusal is one line. It names a file by its id and a rule by its name, and
never holds a row, a key or the address of the vault.
"""

import hashlib
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any, Literal, Protocol, Self

from burro_core.ids import SYNTHETIC_PREFIX, ReleaseId, SourceId
from pydantic import (
    Field,
    SerializerFunctionWrapHandler,
    ValidationError,
    model_serializer,
    model_validator,
)

from burro_pipeline.evidence.fence import is_kept_apart
from burro_pipeline.evidence.receipt import EditionFrom, Period, Receipt, clean_url
from burro_pipeline.evidence.record import (
    MADE_UP_SOURCE,
    EvidenceRecord,
    Sha256,
    Text,
    Timestamp,
    file_id_of,
    in_words,
    strictly_increasing,
)
from burro_pipeline.evidence.repository import NotRead, checked_out, top_of
from burro_pipeline.registry import Registry, RegistryError
from burro_pipeline.registry.model import Use

SCHEMA_VERSION = 1
LOCKS_FOLDER = PurePosixPath("data/locks")
COMMIT_PATTERN = r"^([0-9a-f]{40}|[0-9a-f]{64})$"
NAME_PATTERN = r"^[a-z0-9][a-z0-9_.-]*(/[a-z0-9][a-z0-9_.-]*)*$"
# The name a list gives a file, as fetch's lists write it.
ITEM_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"
# A day or a time, as fetch writes it in the edition of a file that states its own.
STATED = re.compile(r"\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}Z)?")
CHUNK = 1 << 20

MEANING: Mapping[str, str] = {
    "input_is_locked": "is not an input of this build: its hash is not in the lock",
    "input_has_one_receipt": "has no receipt among those the step was given, or has more "
    "than one that fits what the step asked for",
    "input_is_as_described": "is not what the step was written to read",
    "measure_is_as_core_says": "is not named or measured as the catalogue in core says the "
    "measure is, so no release may carry it",
    "measure_has_a_figure": "has a figure for no area, so there is nothing of it to carry",
    "measure_is_not_held_back": "is held back: a check of its figures found that they do not "
    "yet say what the measure is named for, so no release carries it, whatever the catalogue "
    "in core says",
    "gate_refuses": "may not be used as its receipt says",
    "file_is_for_the_product": "is kept for the audit or for the census table, and no such "
    "file is an input of a product release",
    "real_build_needs_a_registry": "is a real file, and a real build is sealed only with the "
    "licence registry to check it against",
    "listed_file_has_a_receipt": "is a file of the list, and no receipt of it is in the folder. "
    "If the list names more files of its source, edition and period, it may be another of "
    "them that has none",
    "receipt_is_listed": "is the receipt of a file that the list of the build does not name, "
    "or names fewer times than there are receipts",
    "listed_file_has_one_receipt": "is one of two receipts of a file of one name, source, "
    "edition and period, and the list names each file once",
    "named_edition_has_a_receipt": "is the edition of no receipt of a file of the list that "
    "states its own edition",
    "real_release_needs_a_lock": "is not made up, and such a release is checked only against "
    "the lock of its build",
    "real_release_needs_a_registry": "is not made up, and such a release is checked only with "
    "the licence registry to hold its evidence to",
    "real_release_needs_its_hashes": "is not made up, and such a release is checked only "
    "against the hashes of its build",
    "build_is_as_it_was_written": "is not as it was when the release was built: it has "
    "changed since, or it is of another build",
    "file_is_in_the_vault": "is not in the vault, or is not the size its receipt gives",
    "licence_evidence_is_saved": "names licence evidence that is not saved in registry/evidence/",
    "one_receipt_for_a_file": "has more than one receipt",
    "lock_has_an_input": "names no input, and a release that is not made up is built from at "
    "least one",
    "made_up_is_consistent": "mixes made-up files with real ones",
    "commit_is_named": "is not sealed in a repository, so the commit of its code cannot be "
    "read and must be given",
    "commit_is_checked_out": "is not the commit that is checked out",
    "tree_has_no_changes": "holds changes that are not committed, so no commit names the code "
    "it holds",
    "repository_is_read": "could not be read, so nothing shows which commit is checked out or "
    "that the files are that commit",
    "receipt_is_valid": "is not a valid receipt",
    "lock_is_valid": "is not a valid lock",
}


class LockError(Exception):
    """A build may not go on. Names what was refused and the rule, and never a value."""

    def __init__(self, rule: str, subject: str, detail: str = "") -> None:
        self.rule = rule
        self.subject = subject
        line = f"{subject} {MEANING.get(rule, 'breaks a rule')}"
        super().__init__(f"{line}: {detail} [{rule}]" if detail else f"{line} [{rule}]")


class InputKind(StrEnum):
    PUBLISHER_FILE = "publisher_file"  # a file in the vault, with a receipt
    GAZETTEER = "gazetteer"  # a curated file in the repository, such as the output area list
    CLAIM_BUNDLE = "claim_bundle"  # the reviewed claims of one research run
    TOOL_OUTPUT = "tool_output"  # what an outside tool wrote, such as the routing engine


class LockedInput(EvidenceRecord):
    # The `file_id` of a publisher's file. For anything else, the name a step knows it by.
    name: str = Field(pattern=NAME_PATTERN)
    kind: InputKind
    sha256: Sha256
    bytes: int = Field(ge=1)
    # The registry entry the file was fetched under. Null for what is not a publisher's file.
    source_id: SourceId | None = None
    # For a file that states its own edition: the name the list gives the file, and the
    # edition the build took of it, as its receipt writes it. The list states no edition
    # for such a file, so the lock does. A lock leaves both out for every other input,
    # and is written as it was before the fields.
    item: str | None = Field(default=None, pattern=ITEM_PATTERN)
    edition: Text | None = None

    @model_validator(mode="after")
    def _holds_together(self) -> Self:
        from_a_publisher = self.kind is InputKind.PUBLISHER_FILE
        if from_a_publisher != (self.source_id is not None):
            raise ValueError("a source is named exactly for a publisher's file")
        if from_a_publisher and self.name != file_id_of(self.sha256):
            raise ValueError("a publisher's file is named by its file_id")
        if (self.item is None) != (self.edition is None):
            raise ValueError("a file of the list and the edition taken of it are named together")
        if self.edition is not None and not from_a_publisher:
            raise ValueError("an edition is named for a publisher's file, and for nothing else")
        return self

    @model_serializer(mode="wrap")
    def _written_as_before_where_no_edition_was_taken(
        self, written_by: SerializerFunctionWrapHandler
    ) -> dict[str, Any]:
        """An input whose edition the list states is the same bytes as it was before the fields."""
        written: dict[str, Any] = written_by(self)
        for later in ("item", "edition"):
            if written.get(later) is None:
                written.pop(later, None)
        return written


def _sha256_of(path: Path) -> tuple[str, int]:
    """The hash and the size of a file, read a piece at a time: one may be over a gigabyte."""
    found, size = hashlib.sha256(), 0
    with path.open("rb") as file:
        while piece := file.read(CHUNK):
            found.update(piece)
            size += len(piece)
    return found.hexdigest(), size


class Lock(EvidenceRecord):
    schema_version: Literal[1] = SCHEMA_VERSION
    release_id: ReleaseId
    # An input, never read from the clock, so that a build repeats.
    built_at: Timestamp
    # The code the build runs, by commit.
    commit: str = Field(pattern=COMMIT_PATTERN)
    # The hash of the package lockfile. Null in a development build, which is never served.
    packages: Sha256 | None = None
    inputs: tuple[LockedInput, ...]

    @model_validator(mode="after")
    def _holds_together(self) -> Self:
        if not strictly_increasing([locked.name for locked in self.inputs]):
            raise ValueError("inputs are sorted by name, each once")
        made_up = self.release_id.startswith(SYNTHETIC_PREFIX)
        if not made_up and not self.inputs:
            raise ValueError("a release that is not made up is built from at least one input")
        sources = {locked.source_id for locked in self.inputs if locked.source_id is not None}
        if any((source == MADE_UP_SOURCE) != made_up for source in sources):
            raise ValueError("a made-up file is an input of a made-up release, and of no other")
        return self

    @property
    def development(self) -> bool:
        """Whether this is a development build: its packages are not held by hash."""
        return self.packages is None

    def holds(self, name: str) -> bool:
        return any(locked.name == name for locked in self.inputs)

    def _admit(self, sha256: str, size: int, subject: str) -> LockedInput:
        for locked in self.inputs:
            if locked.sha256 == sha256 and locked.bytes == size:
                return locked
        raise LockError("input_is_locked", subject)

    def admit(self, content: bytes, subject: str = "an input") -> LockedInput:
        """The input these bytes are, or a refusal if the lock does not name them."""
        return self._admit(hashlib.sha256(content).hexdigest(), len(content), subject)

    def admit_file(self, path: Path) -> LockedInput:
        """The input this file is, or a refusal if the lock does not name it."""
        return self._admit(*_sha256_of(path), subject=path.name)

    def path(self) -> PurePosixPath:
        """Where the lock is kept in the repository."""
        return LOCKS_FOLDER / f"{self.release_id}.json"


class Dated(Protocol):
    """Where a file states its own edition, as an item of fetch's list says it."""

    @property
    def words(self) -> str: ...
    def in_a_receipt(self) -> EditionFrom: ...


class Wanted(Protocol):
    """One file of the list of a build, as `seal` reads it. An item of fetch's list is one.

    These are what fetch copies from the list into the receipt of a file, so
    they are what a receipt can be held to. A list holds no hash: it is
    written before the file is fetched.
    """

    @property
    def item(self) -> str: ...
    @property
    def source_id(self) -> str: ...
    @property
    def use(self) -> Use: ...
    @property
    def url(self) -> str: ...
    @property
    def edition(self) -> str: ...
    @property
    def data_period(self) -> Period | None: ...
    @property
    def edition_from(self) -> Dated | None: ...


# What a receipt and an item of the list both say of a file.
Said = tuple[str, Use, str, Period | None]


def stated_in(receipt: Receipt, file: Wanted) -> str | None:
    """The day or the time a receipt states, where it is a receipt of this file of a list.

    It is one where fetch could have written it from the item: see the rule
    at the top of this module. A receipt of anything else gives nothing, and
    so does every receipt for a file whose edition the list states.
    """
    there = file.edition_from
    if there is None or not file.url or receipt.edition_from != there.in_a_receipt():
        return None
    if (receipt.source_id, receipt.use) != (file.source_id, file.use):
        return None
    if receipt.listed_url != clean_url(file.url):
        return None
    if not there.in_a_receipt().period_too and receipt.data_period != file.data_period:
        return None
    words = f"{there.words} " if there.words else ""
    found = receipt.edition.removeprefix(words)
    if not receipt.edition.startswith(words) or not STATED.fullmatch(found):
        return None
    return found


@dataclass(frozen=True)
class Taken:
    """The one edition of a file of a list that a build takes, of those that have a receipt."""

    # The name the list gives the file.
    item: str
    receipt: Receipt
    # The receipts of its other editions, the oldest first. They are no part of the build.
    passed_over: tuple[Receipt, ...]
    # Whether the build was told to take this edition. If not, it is the newest.
    named: bool


def take(
    receipts: Iterable[Receipt],
    listed: Iterable[Wanted],
    editions: Mapping[str, str] | None = None,
) -> tuple[tuple[Taken, ...], tuple[str, ...]]:
    """For each file of a list that states its own edition, the receipt a build takes.

    `editions` is what the build was told to take: the edition of a file, as
    its receipt writes it, by the name the list gives the file. A file that is
    not named there is taken at its newest edition, by the day the file
    states. Also gives the names of the files that have no receipt at all, in
    the order of the list. Nothing stands in for one.

    Refuses two receipts of one file that state one edition, and an edition
    that was named and that no receipt states. A file whose edition the list
    states is left alone: it has the one edition, and none is named for it.
    """
    given = sorted(receipts, key=lambda receipt: receipt.file_id)
    told = dict(editions or {})
    found: list[Taken] = []
    without: list[str] = []
    for file in listed:
        if file.edition_from is None:
            continue
        by_day: dict[str, Receipt] = {}
        for receipt in given:
            day = stated_in(receipt, file)
            if day is None:
                continue
            if day in by_day:
                raise LockError("listed_file_has_one_receipt", receipt.file_id)
            by_day[day] = receipt
        named = told.pop(file.item, None)
        if named is not None:
            chosen = [day for day, receipt in by_day.items() if receipt.edition == named]
            if not chosen:
                # What was named is not repeated: it may be anything.
                raise LockError("named_edition_has_a_receipt", f"the edition named for {file.item}")
        elif by_day:
            chosen = [max(by_day)]
        else:
            without.append(file.item)
            continue
        others = tuple(by_day[day] for day in sorted(by_day) if day != chosen[0])
        found.append(Taken(file.item, by_day[chosen[0]], others, named is not None))
    if told:
        raise LockError(
            "named_edition_has_a_receipt",
            "an edition that was named",
            "the file it is named for is no such file of the list",
        )
    return tuple(found), tuple(without)


def _of_the_list(
    receipts: Sequence[Receipt], listed: Sequence[Wanted], editions: Mapping[str, str] | None
) -> tuple[list[Receipt], dict[str, str]]:
    """The receipts of the list, each once, or a refusal of a folder that is not those.

    A file that states its own edition may have a receipt for each of several
    editions. `take` says which one the build takes, and the others are put
    aside. Also gives the name the list gives each such file, by the id of the
    receipt that was taken.

    Files of one source, use, edition and period cannot be told apart by what
    the list says of them. They are counted: as many receipts as the list names
    files, each of a file with a name of its own.
    """
    taken, without = take(receipts, listed, editions)
    if without:
        raise LockError("listed_file_has_a_receipt", without[0])
    aside = {held.file_id for one in taken for held in (one.receipt, *one.passed_over)}
    item_of = {one.receipt.file_id: one.item for one in taken}
    receipts = [receipt for receipt in receipts if receipt.file_id not in aside]
    wanted: dict[Said, list[Wanted]] = {}
    for file in listed:
        if file.edition_from is not None:
            continue
        said = (file.source_id, file.use, file.edition, file.data_period)
        wanted.setdefault(said, []).append(file)
    found: dict[Said, list[Receipt]] = {}
    for receipt in receipts:
        said = (receipt.source_id, receipt.use, receipt.edition, receipt.data_period)
        found.setdefault(said, []).append(receipt)
    for said, files in wanted.items():
        there = len(found.get(said, ()))
        if there < len(files):
            raise LockError("listed_file_has_a_receipt", files[there].item)
    for said, there in found.items():
        if len(there) > len(wanted.get(said, ())):
            raise LockError("receipt_is_listed", there[-1].file_id)
        names = [receipt.publisher_file for receipt in there]
        for receipt in there:
            if names.count(receipt.publisher_file) > 1:
                raise LockError("listed_file_has_one_receipt", receipt.file_id)
    kept = [*receipts, *(one.receipt for one in taken)]
    return sorted(kept, key=lambda receipt: receipt.file_id), item_of


def locked(receipt: Receipt, item: str | None = None) -> LockedInput:
    """A publisher's file as a lock names it.

    `item` is the name the list gives a file that states its own edition. The
    lock then says which edition of it the build took.
    """
    return LockedInput(
        name=receipt.file_id,
        kind=InputKind.PUBLISHER_FILE,
        sha256=receipt.sha256,
        bytes=receipt.bytes,
        source_id=receipt.source_id,
        item=item,
        edition=None if item is None else receipt.edition,
    )


def _allowed(receipt: Receipt, registry: Registry | None) -> None:
    """Refuse a receipt whose file may not be used as the receipt says."""
    if receipt.made_up:
        return
    if registry is None:
        raise LockError("real_build_needs_a_registry", receipt.file_id)
    try:
        registry.require(receipt.source_id, receipt.use)
    except RegistryError as error:
        raise LockError("gate_refuses", receipt.file_id, str(error)) from None


def _kept(receipt: Receipt, vault: Mapping[str, int], root: Path) -> None:
    """Refuse a receipt whose file is not in the vault, or whose licence evidence is not saved."""
    if not receipt.made_up and vault.get(receipt.vault_key()) != receipt.bytes:
        raise LockError("file_is_in_the_vault", receipt.file_id)
    evidence = receipt.licence_evidence
    if evidence is not None and not (root / evidence).is_file():
        raise LockError("licence_evidence_is_saved", receipt.file_id)


def code_at(root: Path, commit: str | None) -> str:
    """The commit of the code a build runs, read from the repository where there is one.

    The repository is looked for in `root` and in every folder above it. In
    one, the commit is the one that is checked out, and the working copy must
    be that commit and nothing more, in every folder of it. A commit that is
    given too must be the same one. Only where no folder above holds a
    repository can nothing be read, and the commit is taken as it is given.
    """
    try:
        top = top_of(root)
        found = None if top is None else checked_out(top)
    except NotRead as error:
        raise LockError("repository_is_read", "the repository", str(error)) from None
    if found is None:
        if commit is None:
            raise LockError("commit_is_named", "the build")
        return commit
    if commit is not None and commit != found.commit:
        raise LockError("commit_is_checked_out", "the commit given")
    if not found.clean:
        raise LockError("tree_has_no_changes", "the working copy", found.in_words())
    return found.commit


def seal(
    release_id: str,
    built_at: str,
    commit: str | None,
    receipts: Iterable[Receipt],
    vault: Mapping[str, int],
    registry: Registry | None,
    root: Path,
    packages: str | None = None,
    others: Iterable[LockedInput] = (),
    listed: Sequence[Wanted] | None = None,
    editions: Mapping[str, str] | None = None,
) -> Lock:
    """The lock of a build, or a refusal that names the first file that may not be in it.

    `root` is the repository, or a folder of it. Where it is in one, the commit
    is read from that repository and a working copy with changes is refused,
    before any file is looked at: see `code_at`. Saved licence evidence is
    looked for under `root` as it is given.

    `receipts` are every receipt in the folder, and `listed` is the list of the
    build, which they are held to. The step `seal` always gives the list of a
    real build. With none, every receipt given is sealed. `vault` is the vault's
    listing: the size of each file by its key. `others` are the inputs that are
    not a publisher's file. A made-up file is in no vault, under no registry
    entry and in no list, so none is asked about it.

    `editions` is what the build is told to take of a file that states its own
    edition: the edition, by the name the list gives the file. Of a file that
    is not named there the newest edition is taken, and the lock says which.
    """
    made_up = release_id.startswith(SYNTHETIC_PREFIX)
    commit = code_at(root, commit)
    given = sorted(receipts, key=lambda receipt: receipt.file_id)
    # The gate is asked about every file before anything else is looked at: a file that
    # may not be used is refused for that, whether or not it was ever stored.
    for receipt in given:
        if receipt.made_up != made_up:
            raise LockError("made_up_is_consistent", receipt.file_id)
        _allowed(receipt, registry)
        # The licence gate allows a file for the audit. It is the lock that keeps it
        # out of a build.
        if is_kept_apart(receipt, registry):
            raise LockError("file_is_for_the_product", receipt.file_id)
    item_of: dict[str, str] = {}
    if listed is not None:
        given, item_of = _of_the_list(given, listed, editions)
    sealed: dict[str, LockedInput] = {}
    for receipt in given:
        if receipt.file_id in sealed:
            raise LockError("one_receipt_for_a_file", receipt.file_id)
        _kept(receipt, vault, root)
        sealed[receipt.file_id] = locked(receipt, item_of.get(receipt.file_id))
    inputs = sorted([*sealed.values(), *others], key=lambda locked: locked.name)
    if not made_up and not inputs:
        raise LockError("lock_has_an_input", "the lock")
    try:
        return Lock(
            release_id=release_id,
            built_at=built_at,
            commit=commit,
            packages=packages,
            inputs=tuple(inputs),
        )
    except ValidationError as error:
        # What was handed in is not repeated, a release id included: it may be anything.
        raise LockError("lock_is_valid", "what was to be sealed", in_words(error)) from None


def read_receipts(folder: Path) -> tuple[Receipt, ...]:
    """Every receipt under a folder, in the order of their ids."""
    found: list[Receipt] = []
    for path in sorted(folder.rglob("*.json")):
        try:
            found.append(Receipt.model_validate_json(path.read_bytes()))
        except ValidationError as error:
            where = path.relative_to(folder).as_posix()
            raise LockError("receipt_is_valid", where, in_words(error)) from None
    return tuple(sorted(found, key=lambda receipt: receipt.file_id))


def read_lock(path: Path) -> Lock:
    try:
        return Lock.model_validate_json(path.read_bytes())
    except ValidationError as error:
        raise LockError("lock_is_valid", path.name, in_words(error)) from None
