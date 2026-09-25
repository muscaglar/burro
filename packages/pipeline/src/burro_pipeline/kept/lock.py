"""The lock of a release, as a step reads the one that is committed.

A lock names a release by its id, the commit it was built from, and every
file of it by its hash and its size. It holds counts and the names of rules
beside them, and no figure and no name of a place. `tools/release_lock.py`
writes it in a hosted run, and is the judge of what an image may carry. This
reads one to say which files `take` brings, and holds each value to its shape
as that tool does. A test holds the two to each other: what one writes the
other reads, to the same hash.

To approve a release is to commit its lock under `APPROVED`, named for the
release. A lock is never changed: a release that is wrong is built again
under a new id.

A refusal says where a lock failed and why, and never repeats what it holds.
"""

import re
from pathlib import Path, PurePosixPath
from typing import Literal, Self

from burro_core.ids import FeatureId
from burro_core.release import BUILD_FOLDER, EVIDENCE, HASHES, LOCK, MANIFEST
from pydantic import Field, StrictBool, StrictInt, ValidationError, model_validator

from burro_pipeline.evidence.lock import COMMIT_PATTERN
from burro_pipeline.evidence.lock import MEANING as OF_THE_LOCK
from burro_pipeline.evidence.record import (
    EvidenceRecord,
    Sha256,
    Timestamp,
    in_words,
    strictly_increasing,
)
from burro_pipeline.evidence.served import MEANING as OF_THE_CHECK

SCHEMA_VERSION = 1
# Where the lock of an approved release is committed, from the top of the repository.
APPROVED = PurePosixPath("data/approved")
# A lock is of a release that is not made up. The made-up city is committed whole.
RELEASE_PATTERN = r"^lon-\d{4}-\d{2}-\d{2}-\d{2}$"
# The folders a build writes, each named for the release with one of these after its id:
# the release, the folder of its build, and the folder of household income.
BESIDE = ("", BUILD_FOLDER, "-income")
# The name of a file in a lock: the folder it is in, and its own name there.
NAME_PATTERN = r"^lon-\d{4}-\d{2}-\d{2}-\d{2}(-[a-z]+)?/[a-z][a-z0-9_]*\.[a-z]+$"
# What a release that is not made up is served with. The service holds it to each.
SERVED_WITH = (
    (BESIDE[0], MANIFEST),
    (BUILD_FOLDER, HASHES),
    (BUILD_FOLDER, EVIDENCE),
    (BUILD_FOLDER, LOCK),
)
RELEASE = re.compile(RELEASE_PATTERN)


class LockRefused(Exception):
    """A lock could not be read, or is no lock. Says why, and never what the file holds."""


class LockedFile(EvidenceRecord):
    """One file of a release: where it stands, its hash and its size."""

    name: str = Field(pattern=NAME_PATTERN)
    sha256: Sha256
    bytes: StrictInt = Field(ge=0)


class LeftOut(EvidenceRecord):
    """A measure that a build worked out and left out, and the rule that kept it out."""

    feature: FeatureId
    rule: str

    @model_validator(mode="after")
    def _names_a_rule(self) -> Self:
        if self.rule not in {*OF_THE_LOCK, *OF_THE_CHECK}:
            raise ValueError("is not the name of a rule of a build")
        return self


class Holds(EvidenceRecord):
    """How much a release holds. Each is a count, and none is a figure of a place."""

    areas: StrictInt = Field(ge=0)
    rankable: StrictInt = Field(ge=0)
    measures: StrictInt = Field(ge=0)
    vibes: StrictInt = Field(ge=0)
    destinations: StrictInt = Field(ge=0)
    places: StrictInt = Field(ge=0)
    stations: StrictInt = Field(ge=0)


class ReleaseLock(EvidenceRecord):
    """The lock of one release. Its hash is the hash `tools/release_lock.py` gives of it."""

    schema_version: Literal[1] = SCHEMA_VERSION
    release_id: str = Field(pattern=RELEASE_PATTERN)
    built_at: Timestamp
    commit: str = Field(pattern=COMMIT_PATTERN)
    development: StrictBool
    preview: StrictBool
    holds: Holds
    left_out: tuple[LeftOut, ...]
    files: tuple[LockedFile, ...]

    @model_validator(mode="after")
    def _holds_together(self) -> Self:
        names = [file.name for file in self.files]
        if not names or not strictly_increasing(names):
            raise ValueError("files are sorted by name, each once, and there is one at least")
        folders = {f"{self.release_id}{suffix}" for suffix in BESIDE}
        if any(name.partition("/")[0] not in folders for name in names):
            raise ValueError("a file is of another release, or of no folder a build writes")
        served = {f"{self.release_id}{suffix}/{file}" for suffix, file in SERVED_WITH}
        if not served <= set(names):
            raise ValueError("what the release is served with is not among the files")
        gone = [(one.feature.value, one.rule) for one in self.left_out]
        if gone != sorted(gone):
            raise ValueError("what was left out is sorted by the id of the measure")
        return self

    def path(self) -> PurePosixPath:
        """Where the lock is committed, from the top of the repository."""
        return APPROVED / f"{self.release_id}.json"


def read_lock(path: Path) -> ReleaseLock:
    """The lock in a file. Raises `LockRefused`, which repeats nothing the file holds."""
    try:
        content = path.read_bytes()
    except OSError:
        raise LockRefused("the lock could not be read as a file") from None
    try:
        lock = ReleaseLock.model_validate_json(content, strict=True)
    except ValidationError as error:
        raise LockRefused(f"the file is no lock of a release: {in_words(error)}") from None
    if path.stem != lock.release_id:
        raise LockRefused("the lock is named for another release than it names")
    return lock


def approved(folder: Path) -> list[str]:
    """The releases that are approved: the id of each lock in a folder, in their order.

    A lock is read only when its release is taken. Here a file is counted by
    its name alone, and what is no lock by its name is passed over.
    """
    if not folder.is_dir():
        return []
    found = (path for path in folder.iterdir() if path.suffix == ".json")
    return sorted(path.stem for path in found if RELEASE.fullmatch(path.stem))
