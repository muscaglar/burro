"""Taking part of a file: which row groups of a Parquet file, and which bytes of them.

Some publishers give the whole world as a few large files, and a build wants
the rows of one city. A Parquet file is laid out so that a reader can take
part of it: its footer says where each column of each row group lies, and the
least and the most of what each holds. So fetch reads the footer, works out
here which bytes to ask for, and asks for those and no other.

What is taken is decided by three things a list states of the file, and by
nothing else:

1. **A box**, in degrees: west, south, east and north. A row group is taken
   unless the file's own footer shows that no row of it lies in the box. It
   shows that by the least and the most of the four numbers of the box each
   row fits in. A row group whose footer records no least or no most cannot be
   shown to hold nothing, so it is taken.
2. **The column that holds the box of each row**, by its name in the file. Its
   four parts are named as the GeoParquet standard names them.
3. **The columns to take**, each by its name in the file. A name takes the
   column and every column inside it, and a column inside another is named
   from the top: `sources.list.element.dataset` takes that one and nothing
   beside it. No byte of any other column is asked for, so what a step may
   never read never reaches the store.

So what is taken is every row that lies in the box, and the other rows of the
row groups those rows are in. It is never the rows of the box alone: a row
group is taken whole or not at all. The step that reads the part keeps the
rows it wants.

**The bytes are the publisher's own.** Nothing is unpacked and nothing is
written again. What is kept is the runs of bytes that were taken, one after
another in the order of the file: the four letters the file starts with, the
columns taken of each row group taken, and the footer with the eight bytes
the file ends with. The receipt says where in the file each run lies. So the
same runs asked of the same file are the same bytes, and the same hash, and
anyone can take the part again and see.

A part is not a Parquet file, because a footer says where a column lies in
the whole file. `TakenFile` hands a reader the part as the whole file, with
each run where it lay. A read of a byte that was not taken is refused. It is
never answered with nothing.

Nothing here opens a connection. `download.py` asks the publisher.
"""

import hashlib
import io
import math
import secrets
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol

from burro_pipeline.evidence.receipt import Taken
from burro_pipeline.fetch.download import Downloaded, DownloadRefused, InPieces, Limits, Reason
from burro_pipeline.fetch.parquet import (
    MAGIC,
    TAIL,
    Chunk,
    Footer,
    NotAFooter,
    RowGroup,
    footer_bytes,
    read_footer,
)

# The four numbers of the box a row fits in, as the GeoParquet standard names them.
XMIN, XMAX, YMIN, YMAX = "xmin", "xmax", "ymin", "ymax"
PIECE = 1024 * 1024

Run = tuple[int, int]


class NotLaidOut(Exception):
    """The file is not laid out so that the part can be taken. Safe to print."""


@dataclass(frozen=True)
class Box:
    """A box on the map, in degrees of longitude and latitude."""

    west: float
    south: float
    east: float
    north: float

    def __post_init__(self) -> None:
        held = (self.west, self.south, self.east, self.north)
        if not all(math.isfinite(part) for part in held):
            raise ValueError("a box is four numbers")
        if not (-180 <= self.west < self.east <= 180 and -90 <= self.south < self.north <= 90):
            raise ValueError("a box runs from west to east and from south to north, in degrees")

    def as_written(self) -> tuple[float, float, float, float]:
        return self.west, self.south, self.east, self.north


class Wanted(Protocol):
    """What a list states of the part of a file to take."""

    @property
    def box(self) -> tuple[float, float, float, float]: ...
    @property
    def box_in(self) -> str: ...
    @property
    def columns(self) -> tuple[str, ...]: ...


@dataclass(frozen=True)
class Plan:
    """The part of one file to take: which row groups, and which bytes."""

    # The size of the whole file, in bytes.
    of_bytes: int
    # How many row groups the file holds, and which are taken, counted from 0.
    of_row_groups: int
    row_groups: tuple[int, ...]
    # How many rows the file holds, and how many the row groups taken hold.
    of_rows: int
    rows: int
    # The runs of bytes to take, each as its first byte and how many, in the order of the
    # file. No two overlap, and no two lie side by side.
    runs: tuple[Run, ...]

    @property
    def bytes(self) -> int:
        """How many bytes the part holds."""
        return sum(count for _, count in self.runs)


def _limits(group: RowGroup, box_in: str) -> tuple[float | None, ...]:
    """The least west, the most east, the least south and the most north of a row group."""
    by_part: dict[str, Chunk] = {
        chunk.path[1]: chunk
        for chunk in group.chunks
        if len(chunk.path) == 2 and chunk.path[0] == box_in
    }
    if not {XMIN, XMAX, YMIN, YMAX} <= set(by_part):
        raise NotLaidOut("it does not hold the box of each row in the column the list names")
    west, east = by_part[XMIN], by_part[XMAX]
    south, north = by_part[YMIN], by_part[YMAX]
    return (
        west.number(west.least),
        east.number(east.most),
        south.number(south.least),
        north.number(north.most),
    )


def may_hold_a_row_in(group: RowGroup, box: Box, box_in: str) -> bool:
    """Whether a row group could hold a row that lies in the box, by the file's own footer.

    It could unless the footer shows that it does not. A least or a most that
    is missing, or that is no number, shows nothing.
    """
    west, east, south, north = _limits(group, box_in)
    known = [part for part in (west, east, south, north) if part is not None]
    if len(known) < 4 or not all(math.isfinite(part) for part in known):
        return True
    assert west is not None and east is not None and south is not None and north is not None
    return west <= box.east and east >= box.west and south <= box.north and north >= box.south


def joined(runs: Sequence[Run]) -> tuple[Run, ...]:
    """Runs of bytes in the order of the file, with those that touch or overlap made one."""
    found: list[Run] = []
    for first, count in sorted(runs):
        if found and first <= found[-1][0] + found[-1][1]:
            start, so_far = found[-1]
            found[-1] = (start, max(so_far, first + count - start))
        else:
            found.append((first, count))
    return tuple(found)


def is_wanted(path: Sequence[str], columns: Sequence[str]) -> bool:
    """Whether a column of the file is one a list names, or is inside one it names."""
    named = [tuple(column.split(".")) for column in columns]
    return any(tuple(path[: len(parts)]) == parts for parts in named)


def plan_of(footer: Footer, of_bytes: int, footer_length: int, wanted: Wanted) -> Plan:
    """The part of a file to take, from its footer and what the list states.

    `of_bytes` is the size of the whole file, and `footer_length` the length
    its last eight bytes give for the footer.
    """
    box = Box(*wanted.box)
    footer_at = of_bytes - TAIL - footer_length
    if footer_at < len(MAGIC):
        raise NotLaidOut("its footer is longer than the file")
    paths = [chunk.path for group in footer.groups[:1] for chunk in group.chunks]
    missing = [
        column
        for column in wanted.columns
        if footer.groups and not any(is_wanted(path, (column,)) for path in paths)
    ]
    if missing:
        raise NotLaidOut(f"it lacks {len(missing)} of the columns the list names")
    taken = tuple(
        n for n, group in enumerate(footer.groups) if may_hold_a_row_in(group, box, wanted.box_in)
    )
    runs: list[Run] = [(0, len(MAGIC)), (footer_at, footer_length + TAIL)]
    for n in taken:
        for chunk in footer.groups[n].chunks:
            if chunk.first + chunk.count > footer_at:
                raise NotLaidOut("its footer places a column outside the file")
            if is_wanted(chunk.path, wanted.columns):
                runs.append((chunk.first, chunk.count))
    return Plan(
        of_bytes=of_bytes,
        of_row_groups=len(footer.groups),
        row_groups=taken,
        of_rows=footer.rows,
        rows=sum(footer.groups[n].rows for n in taken),
        runs=joined(runs),
    )


class Asked(Protocol):
    """A file that is asked for a piece at a time. `download.InPieces` is one."""

    def end(self, count: int) -> bytes:
        """The last so many bytes of the file."""
        ...

    @property
    def of_bytes(self) -> int:
        """The size of the whole file, once any piece of it has arrived."""
        ...

    def piece(self, first: int, count: int, keep: Callable[[bytes], object]) -> None:
        """So many bytes of the file from a first byte, handed to `keep` as they arrive."""
        ...


def take(asked: Asked, wanted: Wanted, to: BinaryIO, most: int) -> Plan:
    """Take the part of a file that a list states, and write it to `to`.

    The end of the file is asked for first, then its footer, and then each run
    of the plan in the order of the file. A part that would be over `most`
    bytes is refused before any of its runs is asked for.
    """
    tail = asked.end(TAIL)
    try:
        length = footer_bytes(tail)
        if length + TAIL + len(MAGIC) > asked.of_bytes:
            raise NotLaidOut("its footer is longer than the file")
        if length + TAIL + len(MAGIC) > most:
            raise TooLarge
        held = bytearray()
        asked.piece(asked.of_bytes - TAIL - length, length, held.extend)
        footer = read_footer(bytes(held))
    except NotAFooter as refused:
        raise NotLaidOut(str(refused)) from None
    plan = plan_of(footer, asked.of_bytes, length, wanted)
    if plan.bytes > most:
        raise TooLarge
    footer_at = asked.of_bytes - TAIL - length
    for first, count in plan.runs:
        # The footer and the end of the file have arrived already, and are not asked for
        # again. A column that ends where the footer starts is in one run with it.
        before = min(first + count, footer_at) - first
        if before > 0:
            asked.piece(first, before, to.write)
    to.write(bytes(held) + tail)
    return plan


class TooLarge(Exception):
    """The part is over the size the list states for it."""


class NotTaken(OSError):
    """A reader asked for a byte of the file that is not in the part."""


class TakenFile(io.RawIOBase):
    """A part of a file, read as the whole file is: each run stands where it lay.

    It is for a reader of Parquet, which goes to where the footer says a
    column lies. A read that touches a byte that was not taken raises
    `NotTaken`: what was not taken is not known, and is never read as nothing.
    """

    def __init__(self, path: Path, runs: Sequence[Run], of_bytes: int) -> None:
        super().__init__()
        self._file = path.open("rb")
        self._runs = tuple(runs)
        self._of_bytes, self._at = of_bytes, 0
        # Where each run starts in the part as it is kept.
        self._kept_at: list[int] = []
        kept = 0
        for _, count in self._runs:
            self._kept_at.append(kept)
            kept += count

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self._at

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        start = {io.SEEK_SET: 0, io.SEEK_CUR: self._at, io.SEEK_END: self._of_bytes}[whence]
        self._at = max(0, start + offset)
        return self._at

    def readinto(self, buffer: bytearray | memoryview) -> int:  # pyright: ignore[reportIncompatibleMethodOverride]
        wanted = min(len(buffer), max(0, self._of_bytes - self._at))
        if wanted == 0:
            return 0
        for (first, count), kept_at in zip(self._runs, self._kept_at, strict=True):
            if first <= self._at and self._at + wanted <= first + count:
                self._file.seek(kept_at + self._at - first)
                held = self._file.read(wanted)
                if len(held) != wanted:
                    raise NotTaken("the part is shorter than its receipt says")
                buffer[:wanted] = held
                self._at += wanted
                return wanted
        raise NotTaken("a byte that was not taken was asked for")

    def close(self) -> None:
        self._file.close()
        super().close()

    def footer_alone(self) -> bytes:
        """The footer as a file of its own: the start of the file, its footer and its end.

        A reader of Parquet looks for the footer by reading the end of the
        file in one piece, which may start before the footer does, among bytes
        that were not taken. So it is handed the footer by itself first, and
        then reads each column from where the footer says it lies.
        """
        kept = self._kept_at[-1] + self._runs[-1][1]
        self._file.seek(kept - TAIL)
        tail = self._file.read(TAIL)
        try:
            length = footer_bytes(tail)
        except NotAFooter:
            raise NotTaken("the part does not end as a Parquet file ends") from None
        if length + TAIL > self._runs[-1][1]:
            raise NotTaken("the part does not hold the footer of the file")
        self._file.seek(kept - TAIL - length)
        return MAGIC + self._file.read(length) + tail


def plan_in(path: Path, runs: Sequence[Run], of_bytes: int, wanted: Wanted) -> Plan:
    """The plan that the footer in a kept part gives for what a list states.

    It is how a part is held to its receipt with no connection: the footer is
    in the part, so the plan can be worked out again from the part alone, and
    must name the runs the receipt names.
    """
    if not runs or sum(count for _, count in runs) != path.stat().st_size:
        raise NotLaidOut("the part does not hold as many bytes as its runs say")
    first, count = runs[-1]
    if first + count != of_bytes or count <= TAIL:
        raise NotLaidOut("the part does not end with the end of the file")
    try:
        with path.open("rb") as file:
            file.seek(-TAIL, io.SEEK_END)
            length = footer_bytes(file.read(TAIL))
            if length + TAIL > count:
                raise NotLaidOut("the last run of the part does not hold the footer of the file")
            file.seek(-TAIL - length, io.SEEK_END)
            footer = read_footer(file.read(length))
    except NotAFooter as refused:
        raise NotLaidOut(str(refused)) from None
    return plan_of(footer, of_bytes, length, wanted)


def taken_as(plan: Plan, wanted: Wanted) -> Taken:
    """What a receipt says of a part: what was wanted, and what the plan took for it."""
    return Taken(
        of_bytes=plan.of_bytes,
        box=wanted.box,
        box_in=wanted.box_in,
        columns=tuple(sorted(wanted.columns)),
        of_row_groups=plan.of_row_groups,
        row_groups=plan.row_groups,
        of_rows=plan.of_rows,
        rows=plan.rows,
        runs=plan.runs,
    )


class _Hashed:
    """Writes to a file, and keeps the hash and the count of what it wrote."""

    def __init__(self, file: BinaryIO) -> None:
        self._file, self.digest, self.size = file, hashlib.sha256(), 0

    def write(self, piece: bytes) -> int:
        self.digest.update(piece)
        self.size += len(piece)
        return self._file.write(piece)


def take_part(
    address: str,
    to: Path,
    limits: Limits,
    wanted: Wanted,
    *,
    agent: str,
    may_redirect_to: tuple[str, ...] = (),
    loopback_for_tests: bool = False,
) -> tuple[Downloaded, Taken]:
    """Take part of one file from its publisher to `to`. On any refusal nothing is left on disk.

    `limits.max_bytes` is the most the part may hold, the footer included.
    """
    asked = InPieces(
        address,
        limits,
        agent=agent,
        may_redirect_to=may_redirect_to,
        loopback_for_tests=loopback_for_tests,
    )
    part = to.with_name(f".part-{secrets.token_hex(8)}")
    try:
        try:
            file = part.open("xb")
        except OSError:
            raise DownloadRefused(Reason.NOT_WRITTEN) from None
        with file:
            kept = _Hashed(file)
            try:
                plan = take(asked, wanted, kept, limits.max_bytes)  # pyright: ignore[reportArgumentType]
            except TooLarge:
                raise DownloadRefused(Reason.TOO_LARGE) from None
            except NotLaidOut as refused:
                raise DownloadRefused(Reason.NOT_LAID_OUT, str(refused)) from None
            except ValueError:
                raise DownloadRefused(Reason.NOT_LAID_OUT) from None
        part.replace(to)
        got = Downloaded(
            sha256=kept.digest.hexdigest(),
            bytes=kept.size,
            final_url=asked.final_url,
            file_name=asked.file_name,
            content_type="application/vnd.apache.parquet",
        )
        return got, taken_as(plan, wanted)
    finally:
        part.unlink(missing_ok=True)
