"""The edition a file states of itself, read in what arrived and before it is kept.

Some publishers put another file at the same address and name no edition on
their page. The list then says where the file states its own, and fetch reads
it here: one value, in one place, and nothing else of the file.

    a register in XML   a day, in a named element of its header
    a GeoPackage        the day its contents were last changed
    a street extract    the time its header block says its data runs to
    a file with no date nothing is read: the edition is the day it was retrieved

What is found is a day or a time, held to the calendar. It is never text: what
a file holds in the place of a day is not said, not printed and not kept. A
file that does not hold the value, holds it twice, or holds something else
there gives nothing, and fetch then writes no receipt.

A day that is about the file and not about its data is not the period of its
data. The day a GeoPackage was last changed is such a day, so it is an edition
and never a period.
"""

import re
import sqlite3
import struct
import zlib
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from burro_pipeline.evidence import Period, Where
from burro_pipeline.fetch import markup
from burro_pipeline.fetch.kinds import read_only
from burro_pipeline.fetch.sources import InTheFile

# The most of an XML file that is read for its header. A header is a few hundred bytes.
START = 4096
# The longest text that is looked at in the place of a day.
LONGEST = 64
# The most that the first block of a street extract holds, packed or unpacked, and the
# most that the header before it holds. Its publisher's format allows no more for a header.
MOST = 64 * 1024
# The most rows that a GeoPackage's record of its contents is read for: one for each layer.
LAYERS = 1000
# A street extract holds no data from before its project began.
EARLIEST = datetime(2004, 1, 1, tzinfo=UTC)
# A clock in another zone may be a day ahead. No file is dated later than that.
GRACE = timedelta(days=1)

A_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
# A day, or a time of a day as a GeoPackage writes one.
A_CHANGE = re.compile(r"(\d{4}-\d{2}-\d{2})(T\d{2}:\d{2}:\d{2}(\.\d{1,9})?Z)?")
# The fields of a street extract that are read, by the numbers its format gives them.
KIND, SIZE = 1, 3
RAW, PACKED = 1, 3
RUNS_TO = 32
# How a field is written: a number, eight bytes, a length and that many bytes, four bytes.
NUMBER, EIGHT, HELD, FOUR = 0, 1, 2, 5


@dataclass(frozen=True)
class Found:
    """What a file says of itself, as a receipt holds it."""

    edition: str
    # Nothing where the place gives the edition alone. The period is then the list's.
    period: Period | None


class _NotRead(Exception):
    """A file is not laid out as its kind is. It says nothing of the file."""


def found_in(there: InTheFile, path: Path, retrieved_at: str) -> Found | None:
    """The edition a file states where the list says, or nothing if it states none there.

    `retrieved_at` is the time of the fetch. A file dated later than the day
    after it is not believed.
    """
    retrieved = datetime.strptime(retrieved_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    latest = retrieved + GRACE
    try:
        if there.where is Where.RETRIEVED:
            found = retrieved_at[:10]
        elif there.where is Where.XML_HEADER:
            header, element = there.at.split("/")
            found = _a_day(_in_the_header(path, header, element), latest)
        elif there.where is Where.GEOPACKAGE:
            found = _a_day(_last_change(path), latest)
        else:
            found = _runs_to(path, latest)
    except (_NotRead, markup.MarkupError, OSError, ValueError, zlib.error, sqlite3.Error):
        return None
    period = Period(as_at=found[:10]) if there.period_too else None
    return Found(there.written(found), period)


def _a_day(text: str, latest: datetime) -> str:
    """A day the calendar has, that has come. Anything else is not read."""
    if not A_DAY.fullmatch(text):
        raise _NotRead
    if date.fromisoformat(text) > latest.date():
        raise _NotRead
    return text


class _Header:
    """What is read of the header of an XML file, as the parser walks the file's start.

    The header is the first element under the root. The element that is read
    stands directly under the header. Nothing else is kept, and the walk stops
    where the header ends.
    """

    def __init__(self, header: str, element: str) -> None:
        self.header, self.wanted = header, [header, element]
        self.within: list[str] = []
        self.found: list[str] = []
        self.times = 0
        self.ended = False
        # Whether the element holds more than a day could be: another element, or long text.
        self.more = False

    def begun(self, name: str, _: dict[str, str]) -> None:
        if len(self.within) == 1 and name != self.header:
            raise markup.Finished
        self.more = self.more or self.within[1:] == self.wanted
        self.within.append(name)
        self.times += self.within[1:] == self.wanted

    def text(self, piece: str) -> None:
        if self.within[1:] == self.wanted:
            self.found.append(piece)
            self.more = self.more or sum(len(part) for part in self.found) > LONGEST

    def done(self, _: str) -> None:
        self.within.pop()
        if len(self.within) == 1:
            self.ended = True
            raise markup.Finished


def _in_the_header(path: Path, header: str, element: str) -> str:
    """The text of one element of the header of an XML file. Nothing under the header is read.

    The header ends within the start of the file. The element stands in it
    once, and holds text alone.
    """
    with path.open("rb") as file:
        start = file.read(START)
    read = _Header(header, element)
    markup.read(start, read.begun, read.done, read.text)
    if not read.ended or read.times != 1 or read.more:
        raise _NotRead
    return "".join(read.found).strip()


def _only_the_last_change(action: int, table: str | None, column: str | None, *_: object) -> int:
    """What the one question may read of a GeoPackage: when its contents were last changed."""
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ and (table, column) == ("gpkg_contents", "last_change"):
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def _last_change(path: Path) -> str:
    """The day a GeoPackage says its contents were last changed. No layer is read.

    Every layer has a last change of its own. They must all be of one day: a
    file that gives two days does not say which it is.
    """
    if not path.is_file():
        raise _NotRead
    database = read_only(path)
    try:
        database.set_authorizer(_only_the_last_change)
        rows = database.execute(
            "SELECT last_change FROM gpkg_contents LIMIT ?", (LAYERS + 1,)
        ).fetchall()
    finally:
        database.close()
    days: set[str] = set()
    for (changed,) in rows:
        match = A_CHANGE.fullmatch(changed) if isinstance(changed, str) else None
        if match is None:
            raise _NotRead
        days.add(match[1])
    if len(days) != 1 or len(rows) > LAYERS:
        raise _NotRead
    return days.pop()


def _runs_to(path: Path, latest: datetime) -> str:
    """The time the first block of a street extract says its data runs to.

    No other block is read.
    """
    with path.open("rb") as file:
        (length,) = struct.unpack(">I", _exactly(file.read(4), 4))
        if not 0 < length <= MOST:
            raise _NotRead
        header = _fields(_exactly(file.read(length), length))
        size = _one(header, SIZE)
        if _one(header, KIND) != b"OSMHeader" or not isinstance(size, int) or not 0 < size <= MOST:
            raise _NotRead
        blob = _fields(_exactly(file.read(size), size))
    seconds = _one(_fields(_unpacked(blob)), RUNS_TO)
    if not isinstance(seconds, int) or seconds >= 1 << 63:
        raise _NotRead
    if not EARLIEST.timestamp() <= seconds <= latest.timestamp():
        raise _NotRead
    return datetime.fromtimestamp(seconds, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _exactly(read: bytes, length: int) -> bytes:
    if len(read) != length:
        raise _NotRead
    return read


def _unpacked(blob: list[tuple[int, int | bytes]]) -> bytes:
    """What a blob holds, unpacked where it is packed, and never more than a header block is."""
    kinds = {field for field, _ in blob} - {2}
    if kinds == {RAW}:
        content = _one(blob, RAW)
        if not isinstance(content, bytes):
            raise _NotRead
        return content
    if kinds != {PACKED}:
        raise _NotRead
    packed = _one(blob, PACKED)
    if not isinstance(packed, bytes):
        raise _NotRead
    unpacker = zlib.decompressobj()
    content = unpacker.decompress(packed, MOST)
    if unpacker.unconsumed_tail or not unpacker.eof:
        raise _NotRead
    return content


def _one(fields: list[tuple[int, int | bytes]], wanted: int) -> int | bytes:
    """The one value of a field. A field that is there twice, or not at all, is not read."""
    found = [value for field, value in fields if field == wanted]
    if len(found) != 1:
        raise _NotRead
    return found[0]


def _fields(message: bytes) -> list[tuple[int, int | bytes]]:
    """Each field of a message of a street extract: its number, and what it holds."""
    found: list[tuple[int, int | bytes]] = []
    at = 0
    while at < len(message):
        key, at = _number_at(message, at)
        field, written = key >> 3, key & 7
        if written == NUMBER:
            value, at = _number_at(message, at)
            found.append((field, value))
        elif written == HELD:
            length, at = _number_at(message, at)
            if length > len(message) - at:
                raise _NotRead
            found.append((field, message[at : at + length]))
            at += length
        elif written in (EIGHT, FOUR):
            at += 8 if written == EIGHT else 4
            if at > len(message):
                raise _NotRead
        else:
            raise _NotRead
    return found


def _number_at(message: bytes, at: int) -> tuple[int, int]:
    """A whole number, seven bits to a byte and the least first, and where the next thing starts."""
    value = 0
    for shift in range(0, 70, 7):
        if at >= len(message):
            raise _NotRead
        byte = message[at]
        at += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, at
    raise _NotRead
