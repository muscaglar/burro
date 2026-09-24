"""The files that names and seeds are read from, each through the licence gate.

A name is in a draft because a registered publisher's file holds it. So every
file is asked for here, for the use `gazetteer`, and the gate is asked before
the file is looked for. A source the gate refuses is never opened, however
useful it would be.

A file is read through its receipt, as every step of a build reads one. A
file may have none: the town centres had none until their list stated the
period of their data. A build may not rest on such a file. A draft
for a person's eyes may, and says so: `without_receipt` hands the file over
with `has_receipt` false, and everything made from it carries that mark. It is
asked for by name, and a file that has a receipt is never read that way.

Nothing is written to the store. A file is copied out of it, and the copy is
held to its hash.
"""

import shutil
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Period, Receipt
from burro_pipeline.fetch.store import StoreError, hash_file
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry import RegistryError
from burro_pipeline.registry.model import Use

USE = Use.GAZETTEER
# Where the copy of a file with no receipt is put, in the step's own folder.
NO_RECEIPT = "no-receipt"
PIECE = 16 * 1024 * 1024


@dataclass(frozen=True)
class File:
    """One publisher's file, as a reader of names is handed it."""

    source_id: str
    # The registry's name for who publishes it, less anything in brackets.
    publisher: str
    file_id: str
    sha256: str
    # The publisher's own name for the file.
    name: str
    # Where the checked copy is.
    path: Path
    # The publisher's label for the edition, the time the data describes, and the day it was
    # fetched. Each is empty where the file has no receipt: nothing is put in its place.
    edition: str
    data_date: str
    retrieved_on: str
    # The receipt, or nothing where the file has none.
    receipt: Receipt | None = None

    @property
    def has_receipt(self) -> bool:
        return self.receipt is not None

    @property
    def opened(self) -> Opened:
        """The file as the shared readers take one. Only a file with a receipt is one."""
        if self.receipt is None:
            raise LockError("input_has_one_receipt", self.source_id)
        return Opened(self.receipt, self.path)


def publisher_of(inputs: Inputs, source_id: str) -> str:
    """Who publishes a source, as the registry writes it, less what stands in brackets."""
    return inputs.registry.get(source_id).publisher.split(" (")[0].strip()


def _said(period: Period) -> str:
    """The time the data describes, as its receipt gives it: one date, or a span."""
    return period.as_at or f"{period.start}/{period.end}"


def with_receipt(
    inputs: Inputs,
    source_id: str,
    *,
    edition: str | None = None,
    named: Callable[[str], bool] | None = None,
) -> File:
    """The one file of a source, through the gate, its receipt and its hash."""
    opened = inputs.open(source_id, USE, edition=edition, named=named)
    receipt = opened.receipt
    return File(
        source_id=source_id,
        publisher=publisher_of(inputs, source_id),
        file_id=receipt.file_id,
        sha256=receipt.sha256,
        name=receipt.publisher_file,
        path=opened.path,
        edition=receipt.edition,
        data_date=_said(receipt.data_period),
        retrieved_on=receipt.retrieved_on,
        receipt=receipt,
    )


def without_receipt(inputs: Inputs, source_id: str) -> File:
    """The one file of a source that the store holds and no receipt describes.

    For a draft alone. The gate is asked first. It stops when the source has a
    receipt, because then the file is read as every other is, and when the
    store holds no file of the source or more than one.
    """
    try:
        inputs.registry.require(source_id, USE)
    except RegistryError as error:
        raise LockError("gate_refuses", source_id, str(error)) from None
    if any(receipt.source_id == source_id for receipt in inputs.receipts):
        raise LockError("input_has_one_receipt", source_id)
    try:
        held = [file for file in inputs.store.list() if file.source_id == source_id]
        if len(held) != 1:
            raise LockError("file_is_in_the_vault", source_id)
        to = inputs.work / NO_RECEIPT / held[0].file_id / held[0].name
        if not (to.is_file() and hash_file(to)[0] == held[0].sha256):
            to.unlink(missing_ok=True)
            inputs.store.get(held[0].sha256, to)
    except (StoreError, OSError):
        raise LockError("file_is_in_the_vault", source_id) from None
    return File(
        source_id=source_id,
        publisher=publisher_of(inputs, source_id),
        file_id=held[0].file_id,
        sha256=held[0].sha256,
        name=held[0].name,
        path=to,
        edition="",
        data_date="",
        retrieved_on="",
    )


def either(inputs: Inputs, source_id: str, *, draft: bool) -> File:
    """A file by its receipt, or for a draft alone, the file that has none."""
    has = any(receipt.source_id == source_id for receipt in inputs.receipts)
    if has or not draft:
        return with_receipt(inputs, source_id)
    return without_receipt(inputs, source_id)


def taken_out(file: File, ends_with: str) -> Path:
    """The one file inside a zip whose name ends so, taken out beside the zip.

    A GeoPackage is an SQLite file, and SQLite cannot read inside a zip. The
    copy is kept, and is taken for whole when it is the size the zip gives.
    """
    try:
        with zipfile.ZipFile(file.path) as archive:
            found = [each for each in archive.infolist() if each.filename.endswith(ends_with)]
            if len(found) != 1:
                raise LockError(
                    "input_is_as_described", file.file_id, "it does not hold the one file"
                )
            to = file.path.parent / Path(found[0].filename).name
            if not (to.is_file() and to.stat().st_size == found[0].file_size):
                part = to.with_name(f".part-{to.name}")
                with archive.open(found[0]) as packed, part.open("wb") as unpacked:
                    shutil.copyfileobj(packed, unpacked, PIECE)
                part.replace(to)
            return to
    except (zipfile.BadZipFile, OSError):
        raise LockError("input_is_as_described", file.file_id, "it is not a zip") from None
