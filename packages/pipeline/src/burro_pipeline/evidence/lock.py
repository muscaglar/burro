"""The lock: every input a build is made from, by hash, and the step that seals it.

`seal` writes the lock before a build starts. It takes the list of the build,
and holds the folder of receipts to it: every file the list names has its
receipt, and no receipt is there that the list does not name. It asks the
licence gate about every file again, because a source can lose its approval
after it was fetched.
It refuses a file that is kept for the audit or for the census table, which
the gate lets through. A build then reads nothing the lock does not name:
`Lock.admit` hashes what it is handed and refuses it if the hash is not there.

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
from collections.abc import Iterable, Mapping, Sequence
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Literal, Protocol, Self

from burro_core.ids import SYNTHETIC_PREFIX, ReleaseId, SourceId
from pydantic import Field, ValidationError, model_validator

from burro_pipeline.evidence.fence import is_kept_apart
from burro_pipeline.evidence.receipt import Period, Receipt
from burro_pipeline.evidence.record import (
    MADE_UP_SOURCE,
    EvidenceRecord,
    Sha256,
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
CHUNK = 1 << 20

MEANING: Mapping[str, str] = {
    "input_is_locked": "is not an input of this build: its hash is not in the lock",
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
    "real_release_needs_a_lock": "is not made up, and such a release is checked only against "
    "the lock of its build",
    "real_release_needs_a_registry": "is not made up, and such a release is checked only with "
    "the licence registry to hold its evidence to",
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

    @model_validator(mode="after")
    def _holds_together(self) -> Self:
        from_a_publisher = self.kind is InputKind.PUBLISHER_FILE
        if from_a_publisher != (self.source_id is not None):
            raise ValueError("a source is named exactly for a publisher's file")
        if from_a_publisher and self.name != file_id_of(self.sha256):
            raise ValueError("a publisher's file is named by its file_id")
        return self


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
    def edition(self) -> str: ...
    @property
    def data_period(self) -> Period | None: ...


# What a receipt and an item of the list both say of a file.
Said = tuple[str, Use, str, Period | None]


def _of_the_list(receipts: Sequence[Receipt], listed: Sequence[Wanted]) -> None:
    """Refuse a folder of receipts that is not the receipts of the list, each once.

    Files of one source, use, edition and period cannot be told apart by what
    the list says of them. They are counted: as many receipts as the list names
    files, each of a file with a name of its own.
    """
    wanted: dict[Said, list[Wanted]] = {}
    for file in listed:
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


def locked(receipt: Receipt) -> LockedInput:
    """A publisher's file as a lock names it."""
    return LockedInput(
        name=receipt.file_id,
        kind=InputKind.PUBLISHER_FILE,
        sha256=receipt.sha256,
        bytes=receipt.bytes,
        source_id=receipt.source_id,
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
    if listed is not None:
        _of_the_list(given, listed)
    sealed: dict[str, LockedInput] = {}
    for receipt in given:
        if receipt.file_id in sealed:
            raise LockError("one_receipt_for_a_file", receipt.file_id)
        _kept(receipt, vault, root)
        sealed[receipt.file_id] = locked(receipt)
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
