"""Describe: the shape of a stored file, for a person's own machine.

Parsers are written against what a publisher's file really holds: its column
names, its sheets, its layers. Describe reads a file and gives back that.

It takes the first full row of a table for the names of its columns. Where a
table has no header, that row is data. `headers.py` gives no names where it can
tell such a row from a row of names, and it cannot always tell. So what describe
gives is treated as if it held a row: it is shown in no log that others read,
and no workflow runs it.

| The file is | Describe gives |
|---|---|
| A CSV | The column names, if a row can be told to be names, and the row count |
| A workbook | The sheet names, and for each sheet the same as for a CSV |
| An OpenDocument workbook | The same. With `sheet`, the words of that one sheet too |
| A GeoPackage | The layers, their fields, their feature counts, and the day each last changed |
| A zip | The names and sizes inside. With `inside`, the shape of each member |
| Anything else | What it looks like, and nothing from it |

The words of a sheet are what a workbook says of itself: its cover, its notes,
the title over a table. They are given of one sheet that a person names: each
row of it that holds words alone. A row that holds a number is never given.

A name comes from the file, so it is written as a JSON string in plain ASCII:
it cannot start a line, end one, or colour a terminal. An error is a fixed
sentence with at most a row number. All of it runs with sockets refused.

The day a layer was last changed is the one thing given that is no name and no
count. It is what a list states as the period of a file of boundaries, where
neither the file nor its page states a day the outlines are as at. It is given
as a day and as nothing else: what the file writes there that is no day, or no
time of a day, is not given.
"""

import csv
import json
import shutil
import sqlite3
import tempfile
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path
from typing import cast

from burro_pipeline.fetch.dated import A_CHANGE
from burro_pipeline.fetch.headers import KEPT, Row, find_names, most_common_width
from burro_pipeline.fetch.kinds import Kind, read_only, sniff
from burro_pipeline.fetch.markup import Limited
from burro_pipeline.fetch.offline import sockets_refused
from burro_pipeline.fetch.opendocument import OpenDocumentError
from burro_pipeline.fetch.opendocument import sheets as sheets_of_an_opendocument
from burro_pipeline.fetch.workbook import WorkbookError, sheets

# The largest cell that is read. A quote that never closes makes one cell of the
# rest of the file, and this is where reading it stops.
CELL_LIMIT = 16 * 1024 * 1024
# The most that one member of a zip may unpack to, when describe reads inside.
MEMBER_LIMIT = 8 * 1024 * 1024 * 1024
MEMBERS = 10_000
START = 64 * 1024
SEPARATORS = {",": "comma", "\t": "tab", ";": "semicolon", "|": "bar"}
ENCODINGS = (("utf-8-sig", "utf-8"), ("cp1252", "cp1252"), ("latin-1", "latin-1"))
NAME_LENGTH = 200

Shape = dict[str, object]


class DescribeError(Exception):
    """The file could not be read. The message repeats nothing from the file."""


def as_text(shape: Shape) -> str:
    """A shape as it is printed: JSON in plain ASCII, so a name cannot forge a line."""
    return json.dumps(shape, indent=2, ensure_ascii=True)


def _shown(name: object) -> str:
    """A name from a file's own layout, cut if it is too long to be one."""
    text = str(name)
    return text if len(text) <= NAME_LENGTH else text[:NAME_LENGTH] + "..."


def describe(
    path: Path,
    *,
    inside: bool = False,
    member_limit: int = MEMBER_LIMIT,
    cell_limit: int = CELL_LIMIT,
    sheet: str | None = None,
) -> Shape:
    """The shape of the file at `path`. With `sheet`, the words of that sheet of a workbook."""
    with sockets_refused():
        try:
            return _describe(path, inside, member_limit, cell_limit, sheet)
        except OSError:
            raise DescribeError("the file could not be read from disk") from None


def _describe(
    path: Path, inside: bool, member_limit: int, cell_limit: int, sheet: str | None = None
) -> Shape:
    kind = sniff(path)
    found: Shape = {"kind": kind.value, "bytes": path.stat().st_size}
    if kind is Kind.ODS:
        try:
            return found | {"sheets": sheets_of_an_opendocument(path, words_of=sheet)}
        except OpenDocumentError as error:
            raise DescribeError(f"the workbook could not be read: {error}") from None
    if sheet is not None:
        raise DescribeError("the words of a sheet are given of an OpenDocument workbook alone")
    if kind is Kind.CSV:
        return found | _csv(path, cell_limit)
    if kind is Kind.ZIP:
        return found | _zip(path, inside, member_limit, cell_limit)
    if kind is Kind.WORKBOOK:
        try:
            return found | {"sheets": sheets(path)}
        except WorkbookError as error:
            raise DescribeError(f"the workbook could not be read: {error}") from None
    if kind is Kind.GEOPACKAGE:
        try:
            return found | {"layers": _layers(path)}
        except sqlite3.Error:
            raise DescribeError("the GeoPackage could not be read") from None
    return {"kind": "not_read", "bytes": found["bytes"], "looks_like": kind.value}


def _separator(start: str) -> str:
    """The sign that stands between cells: the one the first lines hold most of."""
    counts = Counter[str]()
    for line in start.splitlines()[:50]:
        quoted = False
        for sign in line:
            if sign == '"':
                quoted = not quoted
            elif sign in SEPARATORS and not quoted:
                counts[sign] += 1
    return max(SEPARATORS, key=lambda sign: counts[sign])


def _csv(path: Path, cell_limit: int) -> Shape:
    for encoding, called in ENCODINGS:
        try:
            return {"encoding": called} | _csv_as(path, encoding, cell_limit)
        except UnicodeDecodeError:
            continue
    raise DescribeError("the file is not text in an encoding describe knows")


def _csv_as(path: Path, encoding: str, cell_limit: int) -> Shape:
    before = csv.field_size_limit(cell_limit)
    first: list[tuple[int, Row]] = []
    widths = Counter[int]()
    number = 0
    try:
        with path.open(encoding=encoding, newline="") as file:
            separator = _separator(file.read(START))
            file.seek(0)
            for number, cells in enumerate(csv.reader(file, delimiter=separator), start=1):
                if not any(cell.strip() for cell in cells):
                    continue
                widths[len(cells)] += 1
                if len(first) < KEPT:
                    first.append((number, dict(enumerate(cells))))
    except csv.Error as error:
        what = "a cell is over the size limit" if "limit" in str(error) else "a row is broken"
        raise DescribeError(f"{what}, at or after row {number + 1}") from None
    finally:
        csv.field_size_limit(before)

    full = most_common_width(widths)
    names = find_names([row for _, row in first], full)
    rows = sum(widths.values())
    found: Shape = {
        "separator": SEPARATORS[separator],
        "columns": None if names.columns is None else list(names.columns),
        "column_count": full,
    }
    if names.columns is not None and names.at is not None:
        found["columns_at_row"] = first[names.at][0]
        found["rows"] = rows - (names.at + 1)
    else:
        found["rows"] = rows
        found["why_no_columns"] = names.why
    return found


def _zip(path: Path, inside: bool, member_limit: int, cell_limit: int) -> Shape:
    try:
        with zipfile.ZipFile(path) as archive:
            listed = archive.infolist()
            if len(listed) > MEMBERS:
                raise DescribeError("the zip holds more members than describe lists")
            members: list[Shape] = []
            for member in listed:
                if member.is_dir():
                    continue
                found: Shape = {
                    "name": _shown(member.filename),
                    "bytes": member.file_size,
                    "packed_bytes": member.compress_size,
                }
                if inside:
                    found["inside"] = _member(archive, member, member_limit, cell_limit)
                members.append(found)
    except (zipfile.BadZipFile, NotImplementedError, RuntimeError, EOFError):
        raise DescribeError("the zip could not be read") from None
    return {"members": members}


def _member(
    archive: zipfile.ZipFile, member: zipfile.ZipInfo, member_limit: int, cell_limit: int
) -> Shape:
    """The shape of one member. It is unpacked under a name of our own and then removed."""
    if member.file_size > member_limit:
        return {"kind": "not_read", "why": "over the size limit"}
    try:
        with tempfile.TemporaryDirectory(prefix="burro-describe-") as folder:
            unpacked = Path(folder) / "member"
            with archive.open(member) as source, unpacked.open("xb") as target:
                # The size a zip states is not the size it unpacks to, so the copy is counted.
                over = DescribeError("over the size limit")
                shutil.copyfileobj(Limited(source, member_limit, over), target)
            found = _describe(unpacked, False, member_limit, cell_limit)
    except DescribeError as error:
        return {"kind": "not_read", "why": str(error)}
    found.pop("bytes", None)
    return found


def _quoted(name: str) -> str:
    """A name from the file, written so that it can only ever be read as a name."""
    return '"' + name.replace('"', '""') + '"'


def _layers(path: Path) -> list[Shape]:
    database = read_only(path)
    try:
        listed = database.execute(
            "SELECT table_name, data_type, srs_id FROM gpkg_contents ORDER BY table_name"
        ).fetchmany(MEMBERS)
        changed = _last_changed(database)
        return [
            _layer(database, *cast(tuple[object, object, object], row))
            | ({"last_changed": changed[row[0]]} if row[0] in changed else {})
            for row in listed
        ]
    finally:
        database.close()


def _last_changed(database: sqlite3.Connection) -> dict[object, str]:
    """The day each layer says its contents were last changed, where the file keeps one.

    It is the day `fetch/dated.py` reads for the edition of a GeoPackage. A
    file that keeps no such column gives none, and so does a layer whose last
    change is no day the calendar has.
    """
    try:
        rows = database.execute("SELECT table_name, last_change FROM gpkg_contents").fetchmany(
            MEMBERS
        )
    except sqlite3.Error:
        return {}
    found: dict[object, str] = {}
    for name, changed in rows:
        match = A_CHANGE.fullmatch(changed) if isinstance(changed, str) else None
        if match is None:
            continue
        try:
            date.fromisoformat(match[1])
        except ValueError:
            continue
        found[name] = match[1]
    return found


def _layer(database: sqlite3.Connection, name: object, data: object, srs: object) -> Shape:
    found: Shape = {"name": _shown(name), "data": _shown(data)}
    table = database.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone()
    # A view or a table made by a plug-in would run what the file says. Neither is read.
    if table is None or str(table[0]).lstrip().upper().startswith("CREATE VIRTUAL"):
        return found | {"why": "not a table, so not read"}
    geometry = database.execute(
        "SELECT geometry_type_name FROM gpkg_geometry_columns WHERE table_name = ?", (name,)
    ).fetchone()
    fields = database.execute("SELECT name, type FROM pragma_table_info(?)", (name,)).fetchall()
    count = database.execute(f"SELECT COUNT(*) FROM {_quoted(str(name))}").fetchone()  # noqa: S608
    return found | {
        "geometry": None if geometry is None else _shown(geometry[0]),
        "srs_id": srs if isinstance(srs, int) else None,
        "fields": [{"name": _shown(field), "type": _shown(kind)} for field, kind in fields],
        "features": int(count[0]),
    }
