"""The footer of a Parquet file is read from its bytes, and says where each column lies.

Every file here is made up, and is written by a Parquet library as the
publisher of places lays out its own. What Burro's own reader finds in a footer
is held to what that library finds in the same file. No socket is opened.
"""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportMissingTypeStubs=false

import struct
from contextlib import suppress
from itertools import pairwise
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from burro_pipeline.fetch.parquet import (
    MAGIC,
    TAIL,
    UNPACKED,
    Footer,
    NotAFooter,
    footer_bytes,
    read_footer,
)

from .parquet_support import CANARY, COLUMNS, Place, a_town, made_up_places


def footer_of(path: Path) -> bytes:
    content = path.read_bytes()
    length = footer_bytes(content[-TAIL:])
    return content[-TAIL - length : -TAIL]


@pytest.fixture
def file(tmp_path: Path) -> Path:
    return made_up_places(tmp_path / "places.parquet", a_town())


@pytest.fixture
def footer(file: Path) -> Footer:
    return read_footer(footer_of(file))


def test_the_end_of_a_file_says_how_long_its_footer_is(file: Path):
    content = file.read_bytes()
    assert content[:4] == MAGIC and content[-4:] == MAGIC
    assert footer_bytes(content[-TAIL:]) == pq.ParquetFile(file).metadata.serialized_size


@pytest.mark.parametrize(
    "tail", [b"", b"PAR1", b"\x10\x00\x00\x00PARE", b"\x00\x00\x00\x00PAR1", b"x" * 9]
)
def test_an_end_that_is_not_the_end_of_a_parquet_file_is_refused(tail: bytes):
    with pytest.raises(NotAFooter):
        footer_bytes(tail)


def test_the_footer_says_how_many_rows_each_row_group_holds(file: Path, footer: Footer):
    written = pq.ParquetFile(file).metadata
    assert footer.rows == written.num_rows == 24
    assert [group.rows for group in footer.groups] == [4] * 6
    assert len(footer.groups) == written.num_row_groups


def test_the_footer_names_the_columns_in_the_order_the_file_holds_them(footer: Footer):
    assert footer.columns == COLUMNS


def test_every_column_lies_where_the_library_that_wrote_the_file_says(file: Path, footer: Footer):
    written = pq.ParquetFile(file).metadata
    for n, group in enumerate(footer.groups):
        assert len(group.chunks) == written.row_group(n).num_columns
        for m, chunk in enumerate(group.chunks):
            column = written.row_group(n).column(m)
            assert ".".join(chunk.path) == column.path_in_schema
            first = column.data_page_offset
            if column.has_dictionary_page:
                first = min(first, column.dictionary_page_offset)
            assert (chunk.first, chunk.count) == (first, column.total_compressed_size)


def test_the_columns_of_a_file_fill_it_from_its_start_to_its_footer(file: Path, footer: Footer):
    """So the bytes of a column are the whole of what the file holds of it."""
    chunks = sorted((chunk.first, chunk.count) for group in footer.groups for chunk in group.chunks)
    assert chunks[0][0] == len(MAGIC)
    for (first, count), (then, _) in pairwise(chunks):
        assert first + count == then
    last = chunks[-1][0] + chunks[-1][1]
    assert last <= file.stat().st_size - TAIL - len(footer_of(file))


def test_the_least_and_the_most_of_the_box_are_what_the_library_recorded(
    file: Path, footer: Footer
):
    written = pq.ParquetFile(file).metadata
    for n, group in enumerate(footer.groups):
        for m, chunk in enumerate(group.chunks):
            if chunk.path[0] != "bbox":
                continue
            recorded = written.row_group(n).column(m).statistics
            assert chunk.number(chunk.least) == pytest.approx(recorded.min)
            assert chunk.number(chunk.most) == pytest.approx(recorded.max)


def test_a_least_of_text_is_not_kept_and_is_never_read_as_a_number(file: Path, footer: Footer):
    """The least and the most of a column of text are two of its values: a name, of a file
    of places. The footer holds them. What is read of a footer keeps neither."""
    assert CANARY.encode() in footer_of(file)
    of_text = [one for g in footer.groups for one in g.chunks if one.physical not in UNPACKED]
    assert {one.path[0] for one in of_text} >= {"id", "names", "addresses", "operating_status"}
    assert {(one.least, one.most) for one in of_text} == {(None, None)}
    assert CANARY not in repr(footer)
    (chunk,) = [one for one in footer.groups[0].chunks if one.path == ("operating_status",)]
    assert chunk.number(b"open") is None


def test_a_file_whose_writer_recorded_nothing_gives_no_least_and_no_most(tmp_path: Path):
    path = made_up_places(tmp_path / "places.parquet", a_town(), statistics=False)
    footer = read_footer(footer_of(path))
    assert {(chunk.least, chunk.most) for g in footer.groups for chunk in g.chunks} == {
        (None, None)
    }


def test_a_file_that_is_not_packed_is_read_the_same(tmp_path: Path):
    path = made_up_places(tmp_path / "places.parquet", a_town(), packed="none")
    assert read_footer(footer_of(path)).rows == 24


def test_a_file_with_many_columns_and_row_groups_is_read(tmp_path: Path):
    town = [Place(2 + n / 1000, 53.4) for n in range(600)]
    path = made_up_places(tmp_path / "places.parquet", town, rows_in_a_group=3)
    footer = read_footer(footer_of(path))
    assert len(footer.groups) == 200 and footer.rows == 600


@pytest.mark.parametrize(
    "content",
    [b"", b"\x00", b"not a footer at all", b"\xff" * 64, b"\x19" * 64, b"\x1c" * 100_000],
    ids=["empty", "a stop", "text", "ones", "lists", "nested too deep"],
)
def test_bytes_that_are_no_footer_are_refused_in_fixed_words(content: bytes):
    with pytest.raises(NotAFooter) as refused:
        read_footer(content)
    assert "Parquet" in str(refused.value) or "row" in str(refused.value)


def cut_short(whole: bytes, every: int) -> None:
    for cut in range(0, len(whole) - 1, every):
        with pytest.raises(NotAFooter):
            read_footer(whole[:cut])


def changed(whole: bytes, every: int) -> None:
    for at in range(0, len(whole), every):
        with suppress(NotAFooter):
            read_footer(whole[:at] + bytes([whole[at] ^ 0x5A]) + whole[at + 1 :])


def test_a_footer_cut_short_is_refused_and_never_half_read(file: Path):
    """A sample of the places a footer may be cut at. The whole runs under `full`."""
    whole = footer_of(file)
    cut_short(whole, max(1, len(whole) // 60))


def test_a_footer_with_a_byte_changed_is_read_or_refused_and_nothing_else(file: Path):
    """A footer that is wrong is never a fault of another kind: a run says why=, and goes on."""
    whole = footer_of(file)
    changed(whole, max(1, len(whole) // 60))


@pytest.mark.full
def test_a_footer_cut_short_or_changed_at_any_byte_is_read_or_refused(tmp_path: Path):
    path = made_up_places(tmp_path / "places.parquet", a_town(groups=2))
    whole = footer_of(path)
    cut_short(whole, 1)
    changed(whole, 1)


def test_a_refusal_repeats_nothing_the_file_holds(file: Path):
    whole = footer_of(file)
    with pytest.raises(NotAFooter) as refused:
        read_footer(whole[: len(whole) // 2])
    assert CANARY not in str(refused.value)
    assert "bbox" not in str(refused.value)


def test_row_groups_that_do_not_add_up_to_the_file_are_refused(file: Path):
    """The footer's own count of rows is held to the row groups it lists."""
    whole = bytearray(footer_of(file))
    # The count of rows of the file is field 3 of the footer: a number of eight bytes, 24.
    written = struct.pack("<B", 0x16) + bytes([24 << 1])
    at = whole.index(written)
    whole[at + 1] = 25 << 1
    with pytest.raises(NotAFooter, match="as many rows"):
        read_footer(bytes(whole))
