"""The day a file says of itself, read in the one place the list names and nowhere else.

Every file is made up, and shaped like a publisher's: a register in XML with a day in
its header, a GeoPackage that records when its contents were last changed, and a street
extract whose header block says what time its data runs to. Nothing is fetched, no
socket is opened, and no file of a publisher is read.
"""

import struct
import zlib
from pathlib import Path

import pytest
from burro_pipeline.evidence import Period, Where
from burro_pipeline.fetch.dated import START, Found, found_in
from burro_pipeline.fetch.sources import InTheFile

from .dated_support import (
    A_ROW,
    DAY,
    RETRIEVED_AT,
    TIME,
    block,
    geopackage,
    geopackage_drawn_from_a_layer,
    header_block,
    header_of,
    held,
    register,
    seconds_of,
    street_extract,
    whole,
    written,
)
from .support import CANARY_ROW

IN_THE_HEADER = InTheFile(
    where=Where.XML_HEADER, at="Header/ExtractDate", words="extract of", period_too=True
)
LAST_CHANGE = InTheFile(
    where=Where.GEOPACKAGE, at="gpkg_contents.last_change", words="last changed", period_too=False
)
RUNS_TO = InTheFile(
    where=Where.STREET_EXTRACT, at="OSMHeader.osmosis_replication_timestamp", period_too=True
)
THE_DAY_RETRIEVED = InTheFile(where=Where.RETRIEVED, at="", words="retrieved", period_too=True)


def in_a_register(tmp_path: Path, content: bytes, there: InTheFile = IN_THE_HEADER) -> Found | None:
    return found_in(there, written(tmp_path / "register.xml", content), RETRIEVED_AT)


def in_a_geopackage(tmp_path: Path, *changes: object) -> Found | None:
    return found_in(LAST_CHANGE, geopackage(tmp_path / "made-up.gpkg", changes), RETRIEVED_AT)


def in_an_extract(tmp_path: Path, content: bytes) -> Found | None:
    return found_in(RUNS_TO, written(tmp_path / "made-up.osm.pbf", content), RETRIEVED_AT)


# A register in XML.


def test_the_day_in_the_header_of_a_register_is_its_edition_and_its_period(tmp_path: Path):
    found = in_a_register(tmp_path, register(header_of(DAY)))
    assert found == Found(f"extract of {DAY}", Period(as_at=DAY))


@pytest.mark.parametrize(
    "content",
    [
        register(header_of(DAY), mark=b"\xef\xbb\xbf"),
        register(header_of(f"\n    {DAY}\n  ")),
        register(header_of(DAY), before="<!-- made up -->\n"),
        register(header_of(DAY).replace("Header>", "fhrs:Header>")).replace(
            b"xmlns:xsi", b'xmlns:fhrs="https://made-up.example/fhrs" xmlns:xsi'
        ),
    ],
    ids=["a byte order mark", "space about the day", "a comment above the root", "a prefix"],
)
def test_a_header_is_read_however_the_publisher_lays_it_out(tmp_path: Path, content: bytes):
    found = in_a_register(tmp_path, content)
    assert found is not None and found.edition == f"extract of {DAY}"


def test_a_header_with_no_day_gives_nothing(tmp_path: Path):
    assert in_a_register(tmp_path, register(header_of())) is None


@pytest.mark.parametrize(
    "said",
    [
        "16/09/2026",
        "2026-9-16",
        "2026-02-30",
        "2026-13-01",
        "2026-09-16T00:00:00",
        "16 September 2026",
        "20260916",
        "",
        "soon",
        CANARY_ROW,
        "2026-09-16 " + "x" * 80,
        "<Day>2026-09-16</Day>",
        "2026-<!-- made up -->09-16<Day/>",
    ],
)
def test_a_header_whose_day_is_not_a_day_gives_nothing(tmp_path: Path, said: str):
    assert in_a_register(tmp_path, register(header_of(said))) is None


def test_a_header_with_two_days_gives_nothing(tmp_path: Path):
    assert in_a_register(tmp_path, register(header_of(DAY, DAY))) is None
    assert in_a_register(tmp_path, register(header_of(DAY, "2026-09-15"))) is None


def test_a_day_that_has_not_come_gives_nothing(tmp_path: Path):
    """A day of grace allows for a clock in another zone. No more."""
    assert in_a_register(tmp_path, register(header_of("2026-09-25"))) is not None
    assert in_a_register(tmp_path, register(header_of("2026-09-26"))) is None


def test_a_day_is_read_in_the_header_and_nowhere_else(tmp_path: Path):
    """A row of the register holds days too, and one under the very name the list gives."""
    assert "<ExtractDate>" in A_ROW
    assert in_a_register(tmp_path, register(header_of())) is None
    # A header that is not the first thing under the root is not looked for.
    late = register(header_of(DAY)).replace(b"<Header>", b"<Note/><Header>")
    assert in_a_register(tmp_path, late) is None
    # Nor one under another name, nor a day deeper in the header than the list says.
    other = InTheFile(where=Where.XML_HEADER, at="Head/ExtractDate", period_too=True)
    assert in_a_register(tmp_path, register(header_of(DAY)), other) is None
    deeper = register(header_of(more=f"<Extract><ExtractDate>{DAY}</ExtractDate></Extract>"))
    assert in_a_register(tmp_path, deeper) is None


def test_nothing_under_the_header_is_read(tmp_path: Path):
    """What stands after the header may be anything. It is not so much as parsed."""
    cut = register(header_of(DAY)).split(b"<EstablishmentCollection>")[0]
    for after in (b"", b"<Establish", b"\x00\xff\xfe not XML at all <<<", A_ROW.encode() * 500):
        found = in_a_register(tmp_path, cut + after)
        assert found == Found(f"extract of {DAY}", Period(as_at=DAY))


def test_a_header_that_does_not_end_near_the_start_gives_nothing(tmp_path: Path):
    long = register(header_of(DAY, more=f"<Note>{'x' * START}</Note>"))
    assert in_a_register(tmp_path, long) is None
    assert in_a_register(tmp_path, register(header_of(DAY)).replace(b"</Header>", b"")) is None


@pytest.mark.parametrize(
    "before",
    [
        '<!DOCTYPE FHRSEstablishment [<!ENTITY day "2026-09-16">]>',
        '<!DOCTYPE FHRSEstablishment SYSTEM "https://made-up.example/register.dtd">',
    ],
)
def test_a_register_that_declares_an_entity_is_not_read(tmp_path: Path, before: str):
    assert in_a_register(tmp_path, register(header_of(DAY), before=before)) is None
    entity = register(header_of("&day;"), before=before)
    assert in_a_register(tmp_path, entity) is None


@pytest.mark.parametrize("content", [b"", b"code,homes\nE1,10\n", b"<", b"\x00" * 64, b"<a/>"])
def test_what_is_no_register_gives_nothing(tmp_path: Path, content: bytes):
    assert in_a_register(tmp_path, content) is None


def test_the_words_a_list_gives_stand_before_the_day(tmp_path: Path):
    plain = InTheFile(where=Where.XML_HEADER, at="Header/ExtractDate", period_too=True)
    found = in_a_register(tmp_path, register(header_of(DAY)), plain)
    assert found == Found(DAY, Period(as_at=DAY))


def test_a_day_that_the_list_does_not_call_the_period_is_the_edition_alone(tmp_path: Path):
    alone = InTheFile(
        where=Where.XML_HEADER, at="Header/ExtractDate", words="made on", period_too=False
    )
    found = in_a_register(tmp_path, register(header_of(DAY)), alone)
    assert found == Found(f"made on {DAY}", None)


# A GeoPackage.


def test_the_day_a_geopackage_was_last_changed_is_its_edition_and_never_its_period(
    tmp_path: Path,
):
    """The day is about the file. When its data is as at, the file does not say."""
    found = in_a_geopackage(tmp_path, "2025-12-22T16:37:50.337Z")
    assert found == Found("last changed 2025-12-22", None)


@pytest.mark.parametrize(
    "changed", ["2025-12-22", "2025-12-22T16:37:50Z", "2025-12-22T16:37:50.337Z"]
)
def test_a_last_change_is_a_day_or_a_time_of_a_day(tmp_path: Path, changed: str):
    found = in_a_geopackage(tmp_path, changed)
    assert found is not None and found.edition == "last changed 2025-12-22"


def test_a_geopackage_of_several_layers_that_changed_on_one_day_gives_that_day(tmp_path: Path):
    found = in_a_geopackage(tmp_path, "2025-12-22T16:37:50.337Z", "2025-12-22T09:00:00Z")
    assert found is not None and found.edition == "last changed 2025-12-22"


def test_a_geopackage_with_two_days_gives_nothing(tmp_path: Path):
    assert in_a_geopackage(tmp_path, "2025-12-22T16:37:50.337Z", "2025-12-23T09:00:00Z") is None
    assert in_a_geopackage(tmp_path, "2025-12-22T16:37:50.337Z", None) is None


def test_a_geopackage_with_no_layer_gives_nothing(tmp_path: Path):
    assert in_a_geopackage(tmp_path) is None


@pytest.mark.parametrize(
    "changed",
    [
        None,
        "",
        "22/12/2025",
        "2025-02-30T00:00:00Z",
        "2025-12-22 16:37:50",
        "2025-12-22T16:37",
        "2025-12-22Tsoon",
        20251222,
        1766421470.337,
        b"2025-12-22",
        CANARY_ROW,
        "2026-09-26T00:00:00Z",
    ],
)
def test_a_last_change_that_is_not_a_day_gives_nothing(tmp_path: Path, changed: object):
    assert in_a_geopackage(tmp_path, changed) is None


def test_a_geopackage_that_keeps_no_last_change_gives_nothing(tmp_path: Path):
    path = geopackage(tmp_path / "made-up.gpkg", ["2025-12-22T16:37:50.337Z"], column="changed")
    assert found_in(LAST_CHANGE, path, RETRIEVED_AT) is None
    for content in (b"", b"SQLite format 3\x00" + b"\x00" * 100, b"code,homes\nE1,10\n"):
        path = written(tmp_path / "not-one.gpkg", content)
        assert found_in(LAST_CHANGE, path, RETRIEVED_AT) is None


def test_no_layer_of_a_geopackage_is_read(tmp_path: Path):
    """A record of contents that is drawn from the rows of a layer is not read."""
    path = geopackage_drawn_from_a_layer(tmp_path / "made-up.gpkg")
    assert found_in(LAST_CHANGE, path, RETRIEVED_AT) is None


# A street extract.


def test_the_time_a_street_extract_runs_to_is_its_edition_and_its_day_is_its_period(
    tmp_path: Path,
):
    found = in_an_extract(tmp_path, street_extract(block(b"OSMHeader", header_block(TIME))))
    assert found == Found(TIME, Period(as_at="2026-09-22"))


def test_a_header_block_that_is_not_packed_is_read_too(tmp_path: Path):
    first = block(b"OSMHeader", header_block(TIME), packed=False)
    found = in_an_extract(tmp_path, street_extract(first))
    assert found is not None and found.edition == TIME


def test_a_header_block_with_no_time_gives_nothing(tmp_path: Path):
    assert in_an_extract(tmp_path, street_extract(block(b"OSMHeader", header_block()))) is None


def test_a_header_block_with_two_times_gives_nothing(tmp_path: Path):
    two = block(b"OSMHeader", header_block(TIME, "2026-09-21T20:22:59Z"))
    assert in_an_extract(tmp_path, street_extract(two)) is None
    assert (
        in_an_extract(tmp_path, street_extract(block(b"OSMHeader", header_block(TIME) * 2))) is None
    )


@pytest.mark.parametrize(
    "seconds",
    [
        *(0, -1, 1, seconds_of("2003-12-31T23:59:59Z")),
        # A day of grace allows for a clock in another zone. This is a second past it.
        *(seconds_of("2026-09-25T09:12:32Z"), 2**40, 2**63 - 1),
    ],
    ids=["nought", "below nought", "1970", "2003", "not come yet", "far off", "the most"],
)
def test_a_time_that_is_no_time_of_a_street_extract_gives_nothing(tmp_path: Path, seconds: int):
    first = block(b"OSMHeader", header_block() + whole(32, seconds))
    assert in_an_extract(tmp_path, street_extract(first)) is None


def test_a_time_is_read_in_the_first_block_and_nowhere_else(tmp_path: Path):
    data_first = block(b"OSMData", header_block(TIME)) + block(b"OSMHeader", header_block(TIME))
    assert in_an_extract(tmp_path, data_first) is None
    # What stands after the first block may be anything.
    first = block(b"OSMHeader", header_block(TIME))
    for after in (b"", b"\xff" * 64, CANARY_ROW.encode() * 500):
        found = in_an_extract(tmp_path, first + after)
        assert found is not None and found.edition == TIME


def packed(size: int, content: bytes) -> bytes:
    """A first block whose blob says it holds `size` bytes, and holds `content`."""
    blob = whole(2, size) + held(3, content)
    header = held(1, b"OSMHeader") + whole(3, len(blob))
    return struct.pack(">I", len(header)) + header + blob


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"\x00\x00",
        b"\x00\x00\x00\x00",
        struct.pack(">I", 2**31),
        struct.pack(">I", 12) + b"short",
        block(b"OSMHeader", header_block(TIME))[:-3],
        # A blob that unpacks to far more than a header block holds, whatever it says it holds.
        packed(2 * 1024 * 1024, zlib.compress(b"\x00" * (2 * 1024 * 1024))),
        packed(40, zlib.compress(b"\x00" * (2 * 1024 * 1024))),
        # A blob that is not packed as it says.
        packed(40, b"not packed at all"),
        # A blob packed in a way that is not read.
        struct.pack(">I", 13) + held(1, b"OSMHeader") + whole(3, 6) + held(4, b"lzma"),
        # A field that runs past the end of its block.
        struct.pack(">I", 4) + b"\x0a\x7f\x00\x00",
        # A number that never ends.
        struct.pack(">I", 12) + b"\xff" * 12,
        # A header that is a field of a kind no street extract holds.
        struct.pack(">I", 2) + b"\x0b\x0c",
        b"code,homes\nE1,10\n",
        b"<?xml version='1.0'?><osm/>",
    ],
)
def test_what_is_no_street_extract_gives_nothing(tmp_path: Path, content: bytes):
    assert in_an_extract(tmp_path, content) is None


# A file that holds no date.


def test_the_day_a_file_was_retrieved_is_read_in_no_file(tmp_path: Path):
    missing = tmp_path / "there-is-no-such-file.csv"
    found = found_in(THE_DAY_RETRIEVED, missing, RETRIEVED_AT)
    assert found == Found("retrieved 2026-09-24", Period(as_at="2026-09-24"))


def test_a_file_that_cannot_be_opened_gives_nothing(tmp_path: Path):
    for there in (IN_THE_HEADER, LAST_CHANGE, RUNS_TO):
        assert found_in(there, tmp_path / "there-is-no-such-file", RETRIEVED_AT) is None
        assert found_in(there, tmp_path, RETRIEVED_AT) is None


def test_nothing_a_file_holds_is_said_but_a_day(tmp_path: Path):
    """What is found is the list's own words and a day. No other text of a file can be in it."""
    hostile = register(header_of(f"2026-09-16{CANARY_ROW}"))
    assert in_a_register(tmp_path, hostile) is None
    found = in_a_register(tmp_path, register(header_of(DAY)))
    assert found is not None and CANARY_ROW not in repr(found)
