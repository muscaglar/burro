"""Where fetched files are kept: one small interface, and a folder that implements it.

A file is addressed by the hash of its bytes and is never written over. A
publisher that reissues a file makes a second file. The object store that
speaks the S3 protocol is in `s3.py`, behind the same calls.

The store has three parts, each with a key of its own: the product, the census
tables about residents, and the audit. A store is of one part, and a file is
written to the store of its part and to no other. Only the product's store can
be named today.

An error from a store is one fixed sentence. It never repeats the address of
the store, a key, or anything the store said, because a build's log is public.
"""

import hashlib
import io
import os
import re
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import BinaryIO, Protocol

from burro_core.ids import SOURCE_ID_PATTERN

from burro_pipeline.evidence.receipt import FILE_NAME, KEPT_PREFIX, VAULT_PREFIX, vault_key
from burro_pipeline.evidence.record import FILE_ID_PATTERN, SHA256_PATTERN, file_id_of

SOURCE_ID = re.compile(SOURCE_ID_PATTERN)
SHA256 = re.compile(SHA256_PATTERN)
FILE_ID = re.compile(FILE_ID_PATTERN)
# A key is what a receipt works out for its file: by source, by hash, then the
# publisher's own name for the file. Each part is held to the receipt's own rule.
KEY = re.compile(
    rf"{re.escape(VAULT_PREFIX)}(?P<source_id>{SOURCE_ID_PATTERN.strip('^$')})"
    rf"/(?P<sha256>{SHA256_PATTERN.strip('^$')})/(?P<name>{FILE_NAME})"
)
# The key of a receipt kept beside its file: by source, then by the id of the file.
RECEIPT_KEY = re.compile(
    rf"{re.escape(KEPT_PREFIX)}{SOURCE_ID_PATTERN.strip('^$')}/{FILE_ID_PATTERN.strip('^$')}\.json"
)
# A receipt is a few hundred bytes. One that names the members of a large zip is more.
LARGEST_RECEIPT = 1024 * 1024

NAME_LENGTH = 200
PIECE = 1024 * 1024

FOLDER_VARIABLE = "BURRO_STORE_FOLDER"
S3_VARIABLES = (
    "BURRO_STORE_ENDPOINT",
    "BURRO_STORE_BUCKET",
    "BURRO_STORE_KEY_ID",
    "BURRO_STORE_SECRET",
)
# What an object store may be given beside the four it needs.
S3_MAY_BE_GIVEN = ("BURRO_STORE_REGION",)


class StoreError(Exception):
    """The store refused, or could not be reached. The message is safe to print."""


class Part(StrEnum):
    """The parts of the store. The key of one part cannot read another (ADR 0015)."""

    PRODUCT = "product"
    RESIDENTS = "residents"
    AUDIT = "audit"


@dataclass(frozen=True, order=True)
class Held:
    """One file in the store."""

    source_id: str
    sha256: str
    name: str
    bytes: int

    @property
    def file_id(self) -> str:
        return file_id_of(self.sha256)

    @property
    def key(self) -> str:
        return vault_key(self.source_id, self.sha256, self.name)


class Store(Protocol):
    @property
    def kind(self) -> str:
        """Which kind of store this is, as a run prints it: one word from a fixed list."""
        ...

    @property
    def part(self) -> Part:
        """The part of the store this is. A file for another part is never written to it."""
        ...

    def put(self, source_id: str, name: str, content: Path) -> tuple[Held, bool]:
        """Keep a file. Returns what is held, and whether this call added it."""
        ...

    def get(self, sha256: str, to: Path) -> Held:
        """Copy a file out by its hash, and check the copy against the hash."""
        ...

    def list(self) -> list[Held]:
        """Every file held, in the order of its key."""
        ...

    def keep_receipt(self, key: str, content: bytes) -> bool:
        """Keep a copy of a receipt. The first kept stands. Returns whether this call added it."""
        ...

    def receipt(self, key: str) -> bytes | None:
        """The receipt kept under a key, as it is kept. Nothing if none is kept there."""
        ...

    def receipts(self) -> dict[str, bytes]:
        """Every receipt kept, by its key, in the order of the keys."""
        ...


def hash_file(path: Path) -> tuple[str, int]:
    """The SHA-256 of a file and its size, read in pieces so a large file fits."""
    digest, size = hashlib.sha256(), 0
    with path.open("rb") as file:
        while piece := file.read(PIECE):
            digest.update(piece)
            size += len(piece)
    return digest.hexdigest(), size


def publisher_name(name: str) -> str:
    """A publisher's name for a file, as a receipt and a key hold it.

    It is the name as given, less what could lead out of a folder or break a
    line: anything before a slash, signs that cannot be printed, and dots at
    the start. A long name is cut in the middle and keeps its ending.
    """
    base = re.split(r"[/\\]", name)[-1]
    base = "".join(sign for sign in base if sign.isprintable()).strip().lstrip(". ")
    if len(base) > NAME_LENGTH:
        stem, dot, suffix = base.rpartition(".")
        keep = f"{dot}{suffix}" if dot and len(suffix) <= 8 else ""
        base = (stem if keep else base)[: NAME_LENGTH - len(keep)] + keep
    return base or "file"


def held_at(key: str, size: int) -> Held | None:
    """The file a key stands for, or nothing if the key is not one a store writes."""
    match = KEY.fullmatch(key)
    return Held(match["source_id"], match["sha256"], match["name"], size) if match else None


def checked(source_id: str, name: str, content: Path) -> Held:
    """What a file would be held as. Refuses an id that could not be a registry id."""
    if not SOURCE_ID.fullmatch(source_id):
        raise StoreError("the source id is not a registry id, so nothing was stored")
    try:
        sha256, size = hash_file(content)
    except OSError as error:
        raise StoreError("the file to store could not be read") from error
    return Held(source_id, sha256, publisher_name(name), size)


def checked_receipt(key: str, content: bytes) -> None:
    """Refuse what could not be a receipt, by where it would be kept and by its size."""
    if not RECEIPT_KEY.fullmatch(key):
        raise StoreError("that is not the key of a receipt, so nothing was kept")
    if len(content) > LARGEST_RECEIPT:
        raise StoreError("that is too large to be a receipt, so nothing was kept")


def checked_receipt_key(key: str) -> None:
    """Refuse to read what is not kept where a receipt is kept."""
    if not RECEIPT_KEY.fullmatch(key):
        raise StoreError("that is not the key of a receipt, so nothing was read")


def checked_as_kept(content: bytes) -> bytes:
    """What was read back as a receipt, unless it is too large to be one."""
    if len(content) > LARGEST_RECEIPT:
        raise StoreError("what is kept as that receipt is too large to be one")
    return content


def copy_checked(source: BinaryIO, to: Path, sha256: str, parts: Path | None = None) -> int:
    """Copy bytes to `to`, and keep the copy only if the hash is right.

    The bytes are written to a file of another name first, in `parts` or beside
    `to`, so that a file with the right name is always a whole file.
    """
    to.parent.mkdir(parents=True, exist_ok=True)
    (parts or to.parent).mkdir(parents=True, exist_ok=True)
    part = (parts or to.parent) / f".part-{secrets.token_hex(8)}"
    digest, size = hashlib.sha256(), 0
    try:
        with part.open("xb") as file:
            while piece := source.read(PIECE):
                digest.update(piece)
                size += len(piece)
                file.write(piece)
        if digest.hexdigest() != sha256:
            raise StoreError(
                "the file held does not match its hash, so it was not used. A file in the "
                "store is never written over: look at it by hand"
            )
        part.replace(to)
    finally:
        part.unlink(missing_ok=True)
    return size


def find(store: Store, reference: str) -> Held:
    """The file a hash or a file id stands for."""
    if not (SHA256.fullmatch(reference) or FILE_ID.fullmatch(reference)):
        raise StoreError("a file is named by a file id or a hash: f-0123456789ab, or 64 hex digits")
    start = reference.removeprefix("f-")
    found = sorted({held.sha256: held for held in store.list() if held.sha256.startswith(start)})
    if not found:
        raise StoreError("the store holds no file with that hash")
    if len(found) > 1:
        raise StoreError("the store holds more than one file with that file id: give the hash")
    return next(held for held in store.list() if held.sha256 == found[0])


class FolderStore:
    """The store as a folder on disk. For tests, and for a first run."""

    kind = "folder"
    # The environment names the product's store and no other: `store_from_environment`.
    part = Part.PRODUCT

    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def put(self, source_id: str, name: str, content: Path) -> tuple[Held, bool]:
        held = checked(source_id, name, content)
        kept = self.folder / held.key
        if kept.exists():
            return held, False
        try:
            with content.open("rb") as file:
                copy_checked(file, kept, held.sha256, parts=self.folder / "parts")
        except OSError as error:
            raise StoreError("the file could not be written to the store") from error
        return held, True

    def get(self, sha256: str, to: Path) -> Held:
        held = next((held for held in self.list() if held.sha256 == sha256), None)
        if held is None:
            raise StoreError("the store holds no file with that hash")
        try:
            with (self.folder / held.key).open("rb") as file:
                copy_checked(file, to, sha256)
        except OSError as error:
            raise StoreError("the file could not be read from the store") from error
        return held

    def list(self) -> list[Held]:
        found: list[Held] = []
        for folder, _, names in os.walk(self.folder / VAULT_PREFIX):
            for name in names:
                path = Path(folder) / name
                held = held_at(path.relative_to(self.folder).as_posix(), path.stat().st_size)
                if held is not None:
                    found.append(held)
        return sorted(found, key=lambda held: held.key)

    def keep_receipt(self, key: str, content: bytes) -> bool:
        checked_receipt(key, content)
        kept = self.folder / key
        if kept.exists():
            return False
        try:
            copy_checked(
                io.BytesIO(content),
                kept,
                hashlib.sha256(content).hexdigest(),
                self.folder / "parts",
            )
        except OSError as error:
            raise StoreError("the receipt could not be written to the store") from error
        return True

    def receipt(self, key: str) -> bytes | None:
        checked_receipt_key(key)
        kept = self.folder / key
        try:
            if not kept.is_file():
                return None
            with kept.open("rb") as file:
                return checked_as_kept(file.read(LARGEST_RECEIPT + 1))
        except OSError as error:
            raise StoreError("the receipt could not be read from the store") from error

    def receipts(self) -> dict[str, bytes]:
        found: dict[str, bytes] = {}
        for folder, _, names in os.walk(self.folder / KEPT_PREFIX):
            for name in names:
                path = Path(folder) / name
                key = path.relative_to(self.folder).as_posix()
                if RECEIPT_KEY.fullmatch(key) and path.stat().st_size <= LARGEST_RECEIPT:
                    found[key] = path.read_bytes()
        return dict(sorted(found.items()))


def store_from_environment(environment: Mapping[str, str]) -> Store:
    """The store the environment names. Its address and keys are read here and printed nowhere.

    It is the product's store. The census tables about residents and the audit are each to
    have a store named by variables of their own. Neither is built, so neither can be named.

    One store is named. A folder named beside an object store, or beside any part of one, is
    refused: a run must never write to a folder on a machine that is thrown away, and say ok.
    """
    folder = environment.get(FOLDER_VARIABLE, "")
    if folder and any(environment.get(name, "") for name in (*S3_VARIABLES, *S3_MAY_BE_GIVEN)):
        raise StoreError(
            f"both a folder and an object store are named. Name one: unset {FOLDER_VARIABLE} "
            f"for the object store, or unset {', '.join((*S3_VARIABLES, *S3_MAY_BE_GIVEN))} "
            "for the folder"
        )
    if folder:
        return FolderStore(Path(folder))
    if all(environment.get(name, "") for name in S3_VARIABLES):
        from burro_pipeline.fetch.s3 import S3Store, settings_from_environment

        return S3Store(settings_from_environment(environment))
    raise StoreError(
        f"no store is named. Set {FOLDER_VARIABLE} for a folder, "
        f"or all of {', '.join(S3_VARIABLES)} for an object store"
    )
