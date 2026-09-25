"""Where releases are kept: a bucket of its own, or a folder that stands in for one.

A release is kept under `releases/`, each file under the name its lock gives
it: the folder a build wrote it in, and its name there. A file is never
written over. One that is kept already is left as it is, and must be the same
bytes: a release never changes, and a correction is a new release.

This is not the store of publishers' files, and it is named by variables of
its own. So a step that keeps a release is given a key that opens no
publisher's file, and a step that reads a publisher's file is given none that
writes a release. One store is named, a folder or a bucket, and never both.

An error from here is a fixed sentence. It never repeats the address of the
store, a key, the name of the bucket, or anything the store said.
"""

import re
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from burro_pipeline.fetch.store import NotTheFile, StoreError, copy_checked, hash_file
from burro_pipeline.kept.lock import NAME_PATTERN

FOLDER_VARIABLE = "BURRO_RELEASES_FOLDER"
S3_VARIABLES = (
    "BURRO_RELEASES_ENDPOINT",
    "BURRO_RELEASES_BUCKET",
    "BURRO_RELEASES_KEY_ID",
    "BURRO_RELEASES_SECRET",
)
# What a bucket may be given beside the four it needs.
S3_MAY_BE_GIVEN = ("BURRO_RELEASES_REGION",)
PREFIX = "releases/"
NAME = re.compile(NAME_PATTERN)
ANOTHER = "another file is kept under that name. It was left as it is"


class Differs(StoreError):
    """Another file is kept under the name already. It was left as it is."""


class Kept(Protocol):
    @property
    def kind(self) -> str:
        """Which kind of store this is, as a run prints it: one word from a fixed list."""
        ...

    def holds(self, name: str, content: Path) -> bool:
        """Whether a file of a release is kept already, as the same bytes.

        Raises `Differs` where another file is kept under the name.
        """
        ...

    def put(self, name: str, content: Path) -> bool:
        """Keep a file of a release. Returns whether this call added it.

        Raises `Differs` where another file is kept under the name.
        """
        ...

    def get(self, name: str, sha256: str, size: int, to: Path) -> None:
        """Copy a file of a release out, and keep the copy only if it is the file asked for."""
        ...


def key_of(name: str) -> str:
    """Where a file of a release is kept. Refuses a name that is none a lock gives."""
    if not NAME.fullmatch(name):
        raise StoreError("that is not the name of a file of a release, so nothing was done")
    return f"{PREFIX}{name}"


def _hashed(content: Path) -> tuple[str, int]:
    try:
        return hash_file(content)
    except OSError:
        raise StoreError("the file to keep could not be read") from None


def _held_to_its_size(to: Path, size: int) -> None:
    if to.stat().st_size != size:
        to.unlink(missing_ok=True)
        raise NotTheFile("the file kept is not the size its lock gives, so it was not used")


class FolderKept:
    """The store of releases as a folder on disk. For tests, and for trying a step."""

    kind = "folder"

    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def holds(self, name: str, content: Path) -> bool:
        kept = self.folder / key_of(name)
        try:
            if not kept.exists():
                return False
            if not kept.is_file() or hash_file(kept) != hash_file(content):
                raise Differs(ANOTHER)
        except OSError:
            raise StoreError("the store of releases could not be read") from None
        return True

    def put(self, name: str, content: Path) -> bool:
        if self.holds(name, content):
            return False
        try:
            with content.open("rb") as file:
                copy_checked(
                    file,
                    self.folder / key_of(name),
                    hash_file(content)[0],
                    parts=self.folder / "parts",
                )
        except OSError:
            raise StoreError("the file could not be written to the store of releases") from None
        return True

    def get(self, name: str, sha256: str, size: int, to: Path) -> None:
        kept = self.folder / key_of(name)
        if not kept.is_file():
            raise StoreError("the store of releases holds no file of that name")
        try:
            with kept.open("rb") as file:
                copy_checked(file, to, sha256)
            _held_to_its_size(to, size)
        except OSError:
            raise StoreError("the file could not be read from the store of releases") from None


class BucketKept:
    """The store of releases as a bucket of an object store."""

    kind = "object_store"

    def __init__(self, environment: Mapping[str, str]) -> None:
        # Only a bucket needs what reaches a network, so it is asked for here.
        from burro_pipeline.fetch.s3 import S3Store, Settings

        endpoint, bucket, key_id, secret = (environment.get(name, "") for name in S3_VARIABLES)
        region = environment.get(S3_MAY_BE_GIVEN[0], "") or "auto"
        self._store = S3Store(
            Settings(endpoint=endpoint, bucket=bucket, key_id=key_id, secret=secret, region=region),
            named=S3_VARIABLES,
        )

    def __repr__(self) -> str:
        return "BucketKept(not shown)"

    def holds(self, name: str, content: Path) -> bool:
        key, (sha256, _) = key_of(name), _hashed(content)
        # What is kept there is read back, and must be the same bytes.
        with tempfile.TemporaryDirectory(prefix="burro-kept-") as folder:
            try:
                return self._store.copy_from(key, sha256, Path(folder) / "kept")
            except NotTheFile:
                raise Differs(ANOTHER) from None

    def put(self, name: str, content: Path) -> bool:
        key, (sha256, size) = key_of(name), _hashed(content)
        if self._store.keep_at(key, content, sha256, size):
            return True
        # Another run kept a file there a moment ago. It was left as it is.
        if not self.holds(name, content):
            raise StoreError("the store of releases answered two ways about one file")
        return False

    def get(self, name: str, sha256: str, size: int, to: Path) -> None:
        if not self._store.copy_from(key_of(name), sha256, to):
            raise StoreError("the store of releases holds no file of that name")
        _held_to_its_size(to, size)


def kept_from_environment(environment: Mapping[str, str]) -> Kept:
    """The store of releases the environment names. Its address and keys are printed nowhere.

    One store is named. A folder named beside a bucket, or beside any part of
    one, is refused: a run must never keep a release in a folder on a machine
    that is thrown away, and say that it is kept.
    """
    folder = environment.get(FOLDER_VARIABLE, "")
    of_a_bucket = (*S3_VARIABLES, *S3_MAY_BE_GIVEN)
    if folder and any(environment.get(name, "") for name in of_a_bucket):
        raise StoreError(
            f"both a folder and a bucket are named for releases. Name one: unset "
            f"{FOLDER_VARIABLE} for the bucket, or unset {', '.join(of_a_bucket)} for the folder"
        )
    if folder:
        return FolderKept(Path(folder))
    if all(environment.get(name, "") for name in S3_VARIABLES):
        return BucketKept(environment)
    raise StoreError(
        f"no store of releases is named. Set {FOLDER_VARIABLE} for a folder, "
        f"or all of {', '.join(S3_VARIABLES)} for a bucket"
    )
