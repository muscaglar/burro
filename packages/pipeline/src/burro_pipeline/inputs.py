"""A publisher's file, as a step of a build reads it: through the gate, its receipt and the lock.

A step that works a figure out never opens a file by its path. It asks
`Inputs.open` for a source and a use, and is handed a copy of the file with
its receipt. Before the copy is handed over:

1. The licence gate is asked about the source and the use. The use is what
   the step puts the file to, which may differ from the use it was fetched for.
2. One receipt is found for it. None, or more than one, is a refusal.
3. The file is refused if it is kept for the audit or for the census table.
4. Where the build has a lock, the file is refused unless the lock names it by
   the same hash. A build with no lock is a development build, which is never
   served.
5. The file is copied out of the store and the copy is checked against the hash
   and the size its receipt gives. Nothing is ever written to the store.

`Inputs.opened` is every file a step was handed, which is what a row of
evidence names as its inputs. A figure rests on nothing a step did not open
this way.

Some publishers give a file for each part of the whole: a square of the grid,
an authority. `Inputs.open_each` hands a step every such file of a source, each
checked as `open` checks one. A step never picks one of two editions of a
file. The build says which edition it takes, in its lock, and hands the step
the receipts of those alone: `take` in `evidence/lock.py` has the rule.

A refusal is a `LockError`: one line that names a source or a file id and a
rule, and never a path, a row or the address of the store.
"""

import csv
import io
import zipfile
from collections.abc import Callable, Generator, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

from burro_pipeline.evidence.fence import is_kept_apart
from burro_pipeline.evidence.lock import Lock, LockError
from burro_pipeline.evidence.receipt import Period, Receipt
from burro_pipeline.fetch.store import Store, StoreError, hash_file
from burro_pipeline.registry import Registry, RegistryError
from burro_pipeline.registry.model import Use


@dataclass(frozen=True)
class Opened:
    """One file a step was handed: its receipt, and where the checked copy is."""

    receipt: Receipt
    path: Path

    @property
    def file_id(self) -> str:
        return self.receipt.file_id

    def member(self, ends_with: str) -> str:
        """The name of the one file inside a zip whose name ends so."""
        try:
            with zipfile.ZipFile(self.path) as archive:
                found = [name for name in archive.namelist() if name.endswith(ends_with)]
        except (zipfile.BadZipFile, OSError):
            raise LockError("input_is_as_described", self.file_id, "it is not a zip") from None
        if len(found) != 1:
            raise LockError(
                "input_is_as_described", self.file_id, "it does not hold the one file that is read"
            )
        return found[0]

    @contextmanager
    def text(self, inside: str | None = None) -> Generator[TextIO]:
        """The file as text, or the one file inside a zip whose name ends with `inside`.

        It is read as UTF-8, and a mark at the start of the file is left out.
        The ends of lines are left as they are, for a reader of tables to take.
        """
        try:
            if inside is None:
                with self.path.open(encoding="utf-8-sig", newline="") as text:
                    yield text
            else:
                name = self.member(inside)
                with zipfile.ZipFile(self.path) as archive, archive.open(name) as raw:
                    yield io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        except (zipfile.BadZipFile, OSError, UnicodeDecodeError):
            raise LockError(
                "input_is_as_described", self.file_id, "it could not be read as text"
            ) from None

    def rows(self, text: TextIO, columns: Sequence[str]) -> Iterator[dict[str, str]]:
        """The rows of a table, once it is seen to hold every column that is read.

        Each row holds the columns asked for and no other, so that a step
        cannot use a column it did not name.
        """
        table = csv.DictReader(text)
        if not set(columns) <= set(table.fieldnames or ()):
            raise LockError("input_is_as_described", self.file_id, "a column is missing")
        try:
            for row in table:
                if any(row[name] is None for name in columns):
                    raise LockError("input_is_as_described", self.file_id, "a row is short")
                yield {name: row[name] for name in columns}
        except csv.Error:
            raise LockError("input_is_as_described", self.file_id, "a row is broken") from None


def period_of(receipts: Sequence[Receipt]) -> Period:
    """The span of the data in several files: from the first day of any to the last of any."""
    first = min(receipt.data_period.days()[0] for receipt in receipts)
    last = max(receipt.data_period.days()[1] for receipt in receipts)
    return Period(as_at=first) if first == last else Period(start=first, end=last)


def retrieved_on(receipts: Sequence[Receipt]) -> str:
    """The latest day any of several files was retrieved."""
    return max(receipt.retrieved_on for receipt in receipts)


@dataclass
class Inputs:
    """The files a step may read, and the ones it has read."""

    registry: Registry
    receipts: Sequence[Receipt]
    store: Store
    # Where copies are put. It is a folder of the step's own, and never the store.
    work: Path
    # The lock of the build. With none the build is a development build.
    lock: Lock | None = None
    _opened: dict[str, Opened] = field(default_factory=dict[str, Opened])

    @property
    def development(self) -> bool:
        """Whether this is a development build: it has no lock, or a lock that holds no packages."""
        return self.lock is None or self.lock.development

    @property
    def opened(self) -> tuple[Opened, ...]:
        """Every file handed over so far, in the order of their ids."""
        return tuple(self._opened[file_id] for file_id in sorted(self._opened))

    def open(
        self,
        source_id: str,
        use: Use,
        *,
        edition: str | None = None,
        named: Callable[[str], bool] | None = None,
        holding: Callable[[Receipt], bool] | None = None,
    ) -> Opened:
        """The one file of a source, checked, or a refusal.

        `edition` and `named` tell apart the files of one source: the edition as
        its receipt gives it, and a test of the publisher's name for the file.
        `holding` tells apart two parts that were taken of one file, by what
        the receipt says each holds.
        """
        try:
            self.registry.require(source_id, use)
        except RegistryError as error:
            raise LockError("gate_refuses", source_id, str(error)) from None
        found = [
            receipt
            for receipt in self.receipts
            if receipt.source_id == source_id
            and (edition is None or receipt.edition == edition)
            and (named is None or named(receipt.publisher_file))
            and (holding is None or holding(receipt))
        ]
        if len(found) != 1:
            raise LockError("input_has_one_receipt", source_id)
        receipt = found[0]
        if is_kept_apart(receipt, self.registry):
            raise LockError("file_is_for_the_product", receipt.file_id)
        if receipt.file_id not in self._opened:
            self._opened[receipt.file_id] = Opened(receipt, self._copy(receipt))
        return self._opened[receipt.file_id]

    def open_each(
        self,
        source_id: str,
        use: Use,
        *,
        edition: str | None = None,
        named: Callable[[str], bool] | None = None,
    ) -> tuple[Opened, ...]:
        """Every file of a source that the step was given, each checked, or a refusal.

        It is for a source whose publisher gives a file for each part of the
        whole. The files are told apart by the publisher's name for each, and
        are handed over in the order of those names. `edition` and `named` say
        which files of the source are meant, as they do for `open`.

        Two receipts of one name are two editions of one file, and nothing
        here picks one: that is a refusal, as no receipt at all is. No file is
        copied before every one is known to be the only one of its name.
        """
        try:
            self.registry.require(source_id, use)
        except RegistryError as error:
            raise LockError("gate_refuses", source_id, str(error)) from None
        names = sorted(
            receipt.publisher_file
            for receipt in self.receipts
            if receipt.source_id == source_id
            and (edition is None or receipt.edition == edition)
            and (named is None or named(receipt.publisher_file))
        )
        if not names or len(set(names)) != len(names):
            raise LockError("input_has_one_receipt", source_id)
        return tuple(
            self.open(source_id, use, edition=edition, named=lambda name, one=one: name == one)
            for one in names
        )

    def _copy(self, receipt: Receipt) -> Path:
        """A checked copy of a file, in the step's own folder."""
        to = self.work / receipt.file_id / receipt.publisher_file
        held = (receipt.sha256, receipt.bytes)
        if self.lock is not None and not any(
            (locked.name, locked.sha256, locked.bytes) == (receipt.file_id, *held)
            for locked in self.lock.inputs
        ):
            raise LockError("input_is_locked", receipt.file_id)
        try:
            if not (to.is_file() and hash_file(to) == held):
                to.unlink(missing_ok=True)
                self.store.get(receipt.sha256, to)
            # A store checks what it hands over. It is checked again here, against the
            # receipt: the size too, which a store is not told.
            if hash_file(to) != held:
                to.unlink(missing_ok=True)
                raise LockError("file_is_in_the_vault", receipt.file_id)
        except (StoreError, OSError):
            raise LockError("file_is_in_the_vault", receipt.file_id) from None
        return to
