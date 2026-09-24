"""What kind of file a set of bytes is, read from the bytes and never from the name.

A publisher that is asked for a file sometimes answers with a page: a sign-in
form, an error, a notice that the file has moved. It arrives with a good
status and the file's own name. So fetch looks at what arrived before it keeps
it, and describe looks before it reads.
"""

import sqlite3
import tempfile
import zipfile
import zlib
from enum import StrEnum
from pathlib import Path
from typing import IO

START = 64 * 1024
# How a zip starts. One with nothing in it starts as it ends.
ZIP_STARTS = (b"PK\x03\x04", b"PK\x05\x06")
# How many zips down a file is looked into: a zip, and three zips inside one another.
DEEPEST = 4
# The most that the zips inside one file may unpack to while they are looked into.
MOST_INSIDE = 4 * 1024 * 1024 * 1024
PIECE = 1024 * 1024


class Kind(StrEnum):
    CSV = "csv"
    ZIP = "zip"
    WORKBOOK = "workbook"
    GEOPACKAGE = "geopackage"
    SQLITE = "sqlite"
    HTML = "html"
    XML = "xml"
    JSON = "json"
    PDF = "pdf"
    XLS = "xls"
    ODS = "ods"
    GZIP = "gzip"
    EMPTY = "empty"
    UNKNOWN = "unknown"


MARKS: tuple[tuple[bytes, Kind], ...] = (
    (b"%PDF", Kind.PDF),
    (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", Kind.XLS),
    (b"\x1f\x8b", Kind.GZIP),
)


def read_only(path: Path) -> sqlite3.Connection:
    """Open an SQLite file that somebody else wrote, to read and nothing more.

    The file is opened as one that cannot change, so nothing is written beside
    it. What the file itself could make the library do is turned off: its
    triggers, its views, and any function it names in its own layout.
    """
    database = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro&immutable=1", uri=True)
    try:
        database.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, True)
        database.setconfig(sqlite3.SQLITE_DBCONFIG_TRUSTED_SCHEMA, False)
        database.setconfig(sqlite3.SQLITE_DBCONFIG_ENABLE_TRIGGER, False)
        database.setconfig(sqlite3.SQLITE_DBCONFIG_ENABLE_VIEW, False)
        database.execute("PRAGMA cell_size_check = ON")
    except sqlite3.Error:
        database.close()
        raise
    return database


class CannotSeeInside(Exception):
    """A file is a zip, or holds one, that cannot be looked into. It says nothing of the file."""


# What reading a zip raises when the zip is not as it should be, or is locked.
_NOT_READ = (
    zipfile.BadZipFile,
    zlib.error,
    EOFError,
    NotImplementedError,
    RuntimeError,
    OSError,
    ValueError,
)


def names_inside(path: Path, *, deepest: int = DEEPEST, most: int = MOST_INSIDE) -> tuple[str, ...]:
    """The names of the files inside a zip, and inside every zip it holds, as each gives them.

    Nothing for a file that is no zip. A member is taken for a zip when it
    starts as one, whatever its name, and when it is named as one. A zip that
    cannot be looked into raises `CannotSeeInside`: one that cannot be opened,
    is locked, is nested deeper than `deepest`, or holds zips that unpack to
    more than `most` bytes in all. Nothing is written where a name says.
    """
    try:
        with path.open("rb") as file:
            starts_as_one = file.read(4).startswith(ZIP_STARTS)
        if not starts_as_one and not zipfile.is_zipfile(path):
            return ()
        with path.open("rb") as file:
            names, _ = _names_in(file, deepest, most)
    except _NOT_READ:
        raise CannotSeeInside from None
    return names


def _names_in(file: IO[bytes], deeper: int, room: int) -> tuple[tuple[str, ...], int]:
    """The names inside a zip and inside the zips it holds, and the room left to unpack in."""
    if deeper < 1:
        raise CannotSeeInside
    names: list[str] = []
    with zipfile.ZipFile(file) as archive:
        for member in archive.infolist():
            names.append(member.filename)
            if member.is_dir():
                continue
            with archive.open(member) as inside:
                named_as_one = member.filename.lower().endswith(".zip")
                if not inside.read(4).startswith(ZIP_STARTS) and not named_as_one:
                    continue
            with tempfile.TemporaryFile(prefix="burro-inside-") as copy:
                with archive.open(member) as inside:
                    room = _copied(inside, copy, room)
                copy.seek(0)
                more, room = _names_in(copy, deeper - 1, room)
            names += more
    return tuple(names), room


def _copied(inside: IO[bytes], copy: IO[bytes], room: int) -> int:
    """Unpack a member to a copy, and give the room that is left. The bytes are counted:
    the size a zip states for a member is not the size it unpacks to."""
    while piece := inside.read(PIECE):
        room -= len(piece)
        if room < 0:
            raise CannotSeeInside
        copy.write(piece)
    return room


def _of_a_zip(path: Path) -> Kind:
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
    except (zipfile.BadZipFile, OSError, ValueError):
        return Kind.UNKNOWN
    if "xl/workbook.xml" in names:
        return Kind.WORKBOOK
    if {"content.xml", "mimetype"} <= names:
        return Kind.ODS
    return Kind.ZIP


def _of_a_database(path: Path) -> Kind:
    try:
        database = read_only(path)
        try:
            found = database.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'gpkg_contents'"
            ).fetchone()
        finally:
            database.close()
    except sqlite3.Error:
        return Kind.UNKNOWN
    return Kind.GEOPACKAGE if found else Kind.SQLITE


def sniff(path: Path) -> Kind:
    """The kind of a file, from how it starts and, for a container, what it holds."""
    with path.open("rb") as file:
        start = file.read(START)
    if not start:
        return Kind.EMPTY
    if start.startswith(ZIP_STARTS):
        return _of_a_zip(path)
    if start.startswith(b"SQLite format 3\x00"):
        return _of_a_database(path)
    for mark, kind in MARKS:
        if start.startswith(mark):
            return kind
    if b"\x00" in start:
        return Kind.UNKNOWN
    text = start.removeprefix(b"\xef\xbb\xbf").lstrip().lower()
    if text.startswith(b"<"):
        page = text.startswith((b"<!doctype html", b"<html")) or b"<html" in text[:2048]
        return Kind.HTML if page else Kind.XML
    if text.startswith((b"{", b"[")):
        return Kind.JSON
    return Kind.CSV
