"""Help for the fetch tests: a server on the loopback address, and made-up files.

Nothing here reaches a publisher. The server binds to 127.0.0.1 on a port the
operating system picks, and a test that uses it is marked so that a connection
to any other address is refused.
"""

import sqlite3
import zipfile
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from xml.sax.saxutils import escape

import pytest

LOOPBACK = "127.0.0.1"
ONLY_LOOPBACK = pytest.mark.allow_hosts([LOOPBACK])

# Strings found nowhere else. If a log line or an error repeats a row, a key or
# the address of the store, one of these shows up in it.
CANARY_ROW = "Zzyzx Parva canary row"
CANARY_KEY = "zzyzx-canary-key-id"
CANARY_SECRET = "zzyzx/canary+secret"  # noqa: S105
CANARY_BUCKET = "zzyzx-canary-bucket"


# A licence registry of made-up sources: one approved, one gated, one banned, and three
# that are read for the audit or shown as the census table about residents.
# All are on one host, as the datasets of a real publisher are. So each entry names the
# addresses of its own files, as a real entry must.
MADE_UP_REGISTRY = """
schema_version = 1

[[source]]
id = "made-up-homes"
name = "Made-up homes"
publisher = "Made-up Office"
url = "https://made-up.example/homes"
dimension = "housing"
licence = "OGL-3.0"
licence_url = "https://licence.made-up.example/terms"
commercial_use = "yes"
share_alike = false
attribution = "Contains made-up data."
attribution_verified = true
status = "approved"
uses = ["scoring", "display"]
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://made-up.example/licence",
    "https://made-up.example/notes",
    "https://files.made-up.example/about-these-files",
]
file_urls = [
    "https://files.made-up.example/files/",
    "https://files.made-up.example/output/",
    "https://made-up.example/notes/",
]

[[source]]
id = "made-up-rail"
name = "Made-up timetable"
publisher = "Made-up Rail"
url = "https://made-up.example/rail"
dimension = "transport"
licence = "Bespoke-terms"
commercial_use = "unknown"
share_alike = false
status = "gated"
status_reason = "The made-up terms must be read and saved first."
uses = ["routing", "validation_only"]
verified_how = "secondary_source"
verified_on = 2026-09-23
evidence_urls = ["https://files.made-up.example/about-these-files"]
file_urls = ["https://files.made-up.example/rail/"]

[[source]]
id = "made-up-ratings"
name = "Made-up ratings"
publisher = "Made-up Reviews"
url = "https://made-up.example/ratings"
dimension = "places"
licence = "Bespoke-terms"
commercial_use = "no"
share_alike = false
status = "banned"
status_reason = "The made-up terms forbid storing anything."
verified_how = "primary_source"
verified_on = 2026-09-23

[[source]]
id = "made-up-audit"
name = "Made-up tables for the audit"
publisher = "Made-up Office"
url = "https://made-up.example/audit"
dimension = "audit"
licence = "OGL-3.0"
commercial_use = "yes"
share_alike = false
status = "held"
status_reason = "Made up. It is read for the audit and for nothing else."
uses = ["audit_only"]
verified_how = "secondary_source"
verified_on = 2026-09-23
evidence_urls = ["https://files.made-up.example/about-these-files"]
file_urls = ["https://files.made-up.example/audit/"]

[[source]]
id = "made-up-checked"
name = "Made-up homes that the audit reads too"
publisher = "Made-up Office"
url = "https://made-up.example/checked"
dimension = "housing"
licence = "OGL-3.0"
commercial_use = "yes"
share_alike = false
status = "gated"
status_reason = "Made up. It waits for its made-up terms to be read."
uses = ["audit_only", "validation_only"]
verified_how = "secondary_source"
verified_on = 2026-09-23
evidence_urls = ["https://files.made-up.example/about-these-files"]
file_urls = ["https://files.made-up.example/checked/"]

[[source]]
id = "made-up-residents"
name = "Made-up census table about residents"
publisher = "Made-up Office"
url = "https://made-up.example/residents"
dimension = "residents"
tables = ["TS021"]
licence = "OGL-3.0"
commercial_use = "yes"
share_alike = false
attribution = "Contains made-up data."
attribution_verified = true
status = "approved"
uses = ["census_table"]
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://made-up.example/licence",
    "https://files.made-up.example/about-these-files",
]
file_urls = ["https://files.made-up.example/residents/"]
"""


def made_up_registry_at(port: int) -> str:
    """The made-up registry, with its publisher's files at a port of the loopback address.

    A port is part of an address, and an entry names the addresses of its
    files. So a test that lists a file at the port of its stand-in publisher
    reads a registry that names that port.
    """
    return MADE_UP_REGISTRY.replace(
        '"https://files.made-up.example/', f'"https://files.made-up.example:{port}/'
    )


@dataclass
class Answer:
    status: int = 200
    headers: dict[str, str] = field(default_factory=dict[str, str])
    body: bytes = b""
    # Send fewer bytes than the headers promise, then close.
    cut_short_at: int | None = None
    # Wait this long before each piece of the body.
    seconds_a_piece: float = 0.0
    piece: int = 64 * 1024


@dataclass
class Seen:
    method: str
    path: str
    headers: dict[str, str]
    body: bytes


Respond = Callable[[Seen], Answer]


@dataclass
class Served:
    address: str
    port: int
    seen: list[Seen]


def _handler(respond: Respond, seen: list[Seen]) -> type[BaseHTTPRequestHandler]:
    import time

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: object) -> None:
            """Say nothing: a test reads what it needs from `seen`."""

        def _serve(self) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            request = Seen(
                self.command,
                self.path,
                {name.lower(): value for name, value in self.headers.items()},
                self.rfile.read(length) if length else b"",
            )
            seen.append(request)
            answer = respond(request)
            self.send_response(answer.status)
            headers = dict(answer.headers)
            if "Transfer-Encoding" not in headers:
                headers.setdefault("Content-Length", str(len(answer.body)))
            headers.setdefault("Connection", "close")
            for name, value in headers.items():
                self.send_header(name, value)
            self.end_headers()
            self.close_connection = True
            if self.command == "HEAD":
                return
            body = (
                answer.body if answer.cut_short_at is None else answer.body[: answer.cut_short_at]
            )
            chunked = headers.get("Transfer-Encoding") == "chunked"
            try:
                for start in range(0, len(body), answer.piece):
                    if answer.seconds_a_piece:
                        time.sleep(answer.seconds_a_piece)
                    piece = body[start : start + answer.piece]
                    if chunked:
                        piece = f"{len(piece):x}\r\n".encode() + piece + b"\r\n"
                    self.wfile.write(piece)
                    self.wfile.flush()
                if chunked:
                    self.wfile.write(b"0\r\n\r\n")
            except OSError:
                # The reader hung up first, as it should when a file is too large or too slow.
                pass

        do_GET = do_HEAD = do_PUT = do_POST = do_DELETE = _serve

    return Handler


@contextmanager
def serving(respond: Respond) -> Generator[Served]:
    """A server on the loopback address that answers as `respond` says."""
    seen: list[Seen] = []
    server = ThreadingHTTPServer((LOOPBACK, 0), _handler(respond, seen))
    server.daemon_threads = True
    # A server is stopped as soon as it looks up, so it looks up often: a test waits for it.
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.001}, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        yield Served(f"http://{LOOPBACK}:{port}", port, seen)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def made_up_csv(path: Path, header: str | None, rows: list[str], before: list[str] | None = None):
    """A small made-up CSV, shaped like a publisher's."""
    lines = [*(before or []), *([header] if header is not None else []), *rows]
    path.write_bytes(("\n".join(lines) + "\n").encode())
    return path


def made_up_zip(path: Path, members: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            member = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            member.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(member, content)
    return path


def column_letters(index: int) -> str:
    letters = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def made_up_workbook(
    path: Path, sheets: dict[str, list[list[str | int | float | None]]], prologue: str = ""
) -> Path:
    """A small made-up workbook: a zip of XML, as a spreadsheet program writes one.

    Text goes through the shared strings table and numbers are written inline,
    which is how the publishers' workbooks are expected to be laid out.
    """
    strings: list[str] = []

    def shared(text: str) -> int:
        if text not in strings:
            strings.append(text)
        return strings.index(text)

    main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    relationships = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    package = "http://schemas.openxmlformats.org/package/2006/relationships"
    members: dict[str, bytes] = {}
    listed: list[str] = []
    related: list[str] = []
    for number, (name, rows) in enumerate(sheets.items(), start=1):
        written: list[str] = []
        for row_number, row in enumerate(rows, start=1):
            cells: list[str] = []
            for column, value in enumerate(row):
                at = f"{column_letters(column)}{row_number}"
                if value is None:
                    continue
                if isinstance(value, str):
                    cells.append(f'<c r="{at}" t="s"><v>{shared(value)}</v></c>')
                else:
                    cells.append(f'<c r="{at}"><v>{value}</v></c>')
            written.append(f'<row r="{row_number}">{"".join(cells)}</row>')
        members[f"xl/worksheets/sheet{number}.xml"] = (
            f'<?xml version="1.0" encoding="UTF-8"?>{prologue}'
            f'<worksheet xmlns="{main}"><sheetData>{"".join(written)}</sheetData></worksheet>'
        ).encode()
        listed.append(f'<sheet name="{escape(name)}" sheetId="{number}" r:id="rId{number}"/>')
        related.append(
            f'<Relationship Id="rId{number}" Type="{relationships}/worksheet" '
            f'Target="worksheets/sheet{number}.xml"/>'
        )
    members["xl/workbook.xml"] = (
        f'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="{main}" '
        f'xmlns:r="{relationships}"><sheets>{"".join(listed)}</sheets></workbook>'
    ).encode()
    members["xl/_rels/workbook.xml.rels"] = (
        f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="{package}">'
        f"{''.join(related)}</Relationships>"
    ).encode()
    members["xl/sharedStrings.xml"] = (
        f'<?xml version="1.0" encoding="UTF-8"?><sst xmlns="{main}">'
        + "".join(f"<si><t>{escape(text)}</t></si>" for text in strings)
        + "</sst>"
    ).encode()
    members["[Content_Types].xml"] = b'<?xml version="1.0" encoding="UTF-8"?><Types/>'
    return made_up_zip(path, members)


def made_up_geopackage(path: Path, layers: dict[str, tuple[list[tuple[str, str]], int]]) -> Path:
    """A small made-up GeoPackage: an SQLite file with the tables the standard asks for.

    `layers` gives, for each layer, its fields as (name, type) and how many
    made-up features to write. Every text value written is the canary row.
    """
    database = sqlite3.connect(path)
    try:
        database.execute("PRAGMA application_id = 0x47504B47")
        database.execute(
            "CREATE TABLE gpkg_contents (table_name TEXT PRIMARY KEY, data_type TEXT, "
            "identifier TEXT, description TEXT, srs_id INTEGER)"
        )
        database.execute(
            "CREATE TABLE gpkg_geometry_columns (table_name TEXT, column_name TEXT, "
            "geometry_type_name TEXT, srs_id INTEGER, z TINYINT, m TINYINT)"
        )
        for layer, (fields, features) in layers.items():
            quoted = '"' + layer.replace('"', '""') + '"'
            columns = ", ".join(
                f'"{name.replace(chr(34), chr(34) * 2)}" {kind}' for name, kind in fields
            )
            database.execute(
                f"CREATE TABLE {quoted} (fid INTEGER PRIMARY KEY, geom BLOB, {columns})"
            )
            database.execute(
                "INSERT INTO gpkg_contents VALUES (?, 'features', ?, ?, 27700)",
                (layer, layer, CANARY_ROW),
            )
            database.execute(
                "INSERT INTO gpkg_geometry_columns VALUES (?, 'geom', 'MULTIPOLYGON', 27700, 0, 0)",
                (layer,),
            )
            marks = ", ".join("?" for _ in fields)
            for _ in range(features):
                database.execute(
                    f"INSERT INTO {quoted} VALUES (NULL, ?, {marks})",  # noqa: S608
                    (CANARY_ROW.encode(), *(CANARY_ROW for _ in fields)),
                )
        database.commit()
    finally:
        database.close()
    return path
