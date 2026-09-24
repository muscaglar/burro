"""Which part of a file is taken: the row groups that may hold a row in a box, and no more.

Every file here is made up, and is written by a Parquet library as the
publisher of places lays out its own. The made-up places stand in a row from
west to east in open sea, a row group to each quarter of a degree, so that
which row groups a box takes can be said by hand. No socket is opened: the
file is asked for a piece at a time from disk.
"""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportMissingTypeStubs=false

import hashlib
import io
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from burro_pipeline.fetch.parquet import MAGIC, TAIL, footer_bytes, read_footer
from burro_pipeline.fetch.take import (
    Box,
    NotLaidOut,
    NotTaken,
    Plan,
    TakenFile,
    TooLarge,
    is_wanted,
    joined,
    plan_in,
    plan_of,
    take,
)

from .parquet_support import BOX_IN, CANARY, COLUMNS, LATITUDE, TAKEN, Place, a_town, made_up_places

# A box round the second and third row groups, which hold 2.25 to 2.75 degrees east.
BOX = (2.3, 53.0, 2.7, 54.0)


@dataclass(frozen=True)
class Stated:
    """What a made-up list states of the part to take."""

    box: tuple[float, float, float, float] = BOX
    box_in: str = BOX_IN
    columns: tuple[str, ...] = TAKEN


@dataclass
class OnDisk:
    """A file that is asked for a piece at a time, from disk. It keeps what was asked of it."""

    path: Path
    asked: list[tuple[int, int]] = field(default_factory=list[tuple[int, int]])

    @property
    def of_bytes(self) -> int:
        return self.path.stat().st_size

    def end(self, count: int) -> bytes:
        self.asked.append((self.of_bytes - count, count))
        return self.path.read_bytes()[-count:]

    def piece(self, first: int, count: int, keep: Callable[[bytes], object]) -> None:
        self.asked.append((first, count))
        keep(self.path.read_bytes()[first : first + count])


@pytest.fixture
def file(tmp_path: Path) -> Path:
    return made_up_places(tmp_path / "places.parquet", a_town())


def planned(path: Path, stated: Stated | None = None) -> Plan:
    content = path.read_bytes()
    length = footer_bytes(content[-TAIL:])
    footer = read_footer(content[-TAIL - length : -TAIL])
    return plan_of(footer, len(content), length, stated or Stated())


def taken(path: Path, stated: Stated | None = None, most: int = 10_000_000) -> tuple[Plan, bytes]:
    part = io.BytesIO()
    plan = take(OnDisk(path), stated or Stated(), part, most)
    return plan, part.getvalue()


# Which row groups


def test_the_row_groups_that_may_hold_a_row_in_the_box_are_taken_and_no_other(file: Path):
    plan = planned(file)
    assert (plan.of_row_groups, plan.row_groups) == (6, (1, 2))
    assert (plan.of_rows, plan.rows) == (24, 8)


def test_a_row_group_is_taken_whole_though_one_row_of_it_lies_in_the_box(file: Path):
    """The box holds the last place of the first row group alone. The row group has four."""
    plan = planned(file, Stated(box=(2.2, 53.0, 2.24, 54.0)))
    assert (plan.row_groups, plan.rows) == ((0,), 4)


def test_a_row_on_the_edge_of_the_box_is_in_it(tmp_path: Path):
    town = [Place(2.0, LATITUDE), Place(3.0, LATITUDE), Place(4.0, LATITUDE)]
    path = made_up_places(tmp_path / "places.parquet", town, rows_in_a_group=1)
    assert planned(path, Stated(box=(3.0, 53.0, 3.5, 54.0))).row_groups == (1,)
    assert planned(path, Stated(box=(2.5, 53.0, 3.0, 54.0))).row_groups == (1,)
    assert planned(path, Stated(box=(2.5, 53.4, 3.5, 54.0))).row_groups == (1,)
    assert planned(path, Stated(box=(2.5, 53.0, 3.5, 53.4))).row_groups == (1,)


def test_a_box_north_or_south_of_every_row_takes_no_row_group(file: Path):
    for box in ((2.0, 54.0, 4.0, 55.0), (2.0, 50.0, 4.0, 53.0)):
        plan = planned(file, Stated(box=box))
        assert (plan.row_groups, plan.rows) == ((), 0)


def test_a_part_with_no_row_group_still_holds_the_start_and_the_footer_of_the_file(file: Path):
    plan, part = taken(file, Stated(box=(10.0, 53.0, 11.0, 54.0)))
    whole = file.read_bytes()
    length = footer_bytes(whole[-TAIL:])
    assert plan.runs == ((0, 4), (len(whole) - TAIL - length, length + TAIL))
    assert part == MAGIC + whole[-TAIL - length :]


def test_a_row_group_with_no_least_and_no_most_cannot_be_ruled_out_and_is_taken(tmp_path: Path):
    path = made_up_places(tmp_path / "places.parquet", a_town(), statistics=False)
    assert planned(path).row_groups == (0, 1, 2, 3, 4, 5)


def test_rows_in_no_order_are_still_all_found(tmp_path: Path):
    """The publisher puts places near each other in one row group. Nothing here needs it to."""
    town = a_town()
    mixed = [town[(7 * n) % len(town)] for n in range(len(town))]
    path = made_up_places(tmp_path / "places.parquet", mixed)
    plan = planned(path)
    inside = sum(BOX[0] <= place.longitude <= BOX[2] for place in mixed)
    rows = pq.ParquetFile(path)
    found = 0
    for n in plan.row_groups:
        for box in rows.read_row_group(n, columns=["bbox"]).column("bbox").to_pylist():
            found += BOX[0] <= box["xmin"] and box["xmax"] <= BOX[2]
    assert found == inside == 6


# Which bytes


def test_the_bytes_taken_are_the_columns_named_of_the_row_groups_taken(file: Path):
    plan = planned(file)
    written = pq.ParquetFile(file).metadata
    wanted: list[tuple[int, int]] = []
    for n in (1, 2):
        for m in range(written.row_group(n).num_columns):
            column = written.row_group(n).column(m)
            if is_wanted(column.path_in_schema.split("."), TAKEN):
                first = column.data_page_offset
                if column.has_dictionary_page:
                    first = min(first, column.dictionary_page_offset)
                wanted.append((first, column.total_compressed_size))
    size = file.stat().st_size
    ends = [(0, 4), (size - TAIL - written.serialized_size, written.serialized_size + TAIL)]
    assert plan.runs == joined([*wanted, *ends])
    assert plan.bytes == sum(count for _, count in wanted) + 4 + written.serialized_size + TAIL
    assert plan.of_bytes == size


def test_no_byte_of_a_column_that_is_not_named_is_taken(tmp_path: Path):
    """The names, the addresses and the ids hold the canary. Written unpacked, it would show."""
    path = made_up_places(tmp_path / "places.parquet", a_town(), packed="none")
    assert CANARY.encode() in path.read_bytes()
    _, part = taken(path, Stated(columns=("geometry", "confidence", "taxonomy", "bbox")))
    footer_at = len(part) - TAIL - footer_bytes(part[-TAIL:])
    assert CANARY.encode() not in part[:footer_at]


def test_the_footer_is_taken_whole_and_holds_the_least_and_most_of_every_column(tmp_path: Path):
    """So the footer is no place for what a step may not read. It holds no row.

    It does hold the least and the most of each column as the writer recorded
    them, and for a column of text those are two of its values. That is said
    here so that nobody takes the footer to be free of them.
    """
    path = made_up_places(tmp_path / "places.parquet", a_town(), packed="none")
    _, part = taken(path, Stated(columns=("geometry", "bbox")))
    assert CANARY.encode() in part[-TAIL - footer_bytes(part[-TAIL:]) :]


def test_a_column_inside_another_is_taken_by_itself_and_nothing_beside_it(tmp_path: Path):
    """Where a record came from is kept beside the id its first publisher gave it."""
    path = made_up_places(tmp_path / "places.parquet", a_town(), packed="none")
    whole, _ = taken(path, Stated(columns=("sources", "bbox")))
    one, part = taken(path, Stated(columns=("sources.list.element.dataset", "bbox")))
    assert one.row_groups == whole.row_groups and one.bytes < whole.bytes
    footer_at = len(part) - TAIL - footer_bytes(part[-TAIL:])
    assert b"meta" in part[:footer_at] and CANARY.encode() not in part[:footer_at]


@pytest.mark.parametrize(
    "column", ["sources.dataset", "sources.list.element.data", "source", "bbox.xmin.more"]
)
def test_a_name_that_is_no_column_of_the_file_is_refused_and_is_never_taken_for_another(
    file: Path, column: str
):
    assert "lacks 1 of the columns" in refused(file, Stated(columns=("bbox", column)))


def test_runs_that_touch_or_overlap_are_one_run():
    assert joined([(10, 5), (0, 4), (4, 6), (20, 1), (15, 2), (16, 3)]) == ((0, 19), (20, 1))
    assert joined([]) == ()


def test_the_columns_may_be_named_in_any_order(file: Path):
    assert planned(file, Stated(columns=tuple(reversed(TAKEN)))) == planned(file)


def test_every_column_named_takes_the_whole_file_of_the_row_groups_taken(file: Path):
    plan = planned(file, Stated(box=(0.0, 50.0, 10.0, 60.0), columns=COLUMNS))
    assert plan.runs == ((0, file.stat().st_size),)


# What is asked of the publisher


def test_the_end_is_asked_for_first_then_the_footer_then_each_run_in_order(file: Path):
    asked = OnDisk(file)
    part = io.BytesIO()
    plan = take(asked, Stated(), part, 10_000_000)
    size = file.stat().st_size
    length = footer_bytes(file.read_bytes()[-TAIL:])
    assert asked.asked[:2] == [(size - TAIL, TAIL), (size - TAIL - length, length)]
    assert asked.asked[2:] == list(plan.runs[:-1])
    assert plan.runs[-1] == (size - TAIL - length, length + TAIL)


def test_no_byte_is_asked_for_twice_but_the_eight_the_file_ends_with(file: Path):
    asked = OnDisk(file)
    take(asked, Stated(box=(0.0, 50.0, 10.0, 60.0), columns=COLUMNS), io.BytesIO(), 10_000_000)
    seen: set[int] = set()
    for first, count in asked.asked[1:]:
        run = set(range(first, first + count))
        assert not run & seen
        seen |= run
    assert len(seen) == file.stat().st_size - TAIL


def test_the_part_is_the_runs_of_the_plan_one_after_another(file: Path):
    plan, part = taken(file)
    whole = file.read_bytes()
    assert part == b"".join(whole[first : first + count] for first, count in plan.runs)
    assert len(part) == plan.bytes < len(whole)


def test_the_same_part_taken_again_is_the_same_bytes(file: Path):
    first, again = taken(file), taken(file)
    assert first == again
    assert hashlib.sha256(first[1]).hexdigest() == hashlib.sha256(again[1]).hexdigest()


def test_a_part_over_the_size_the_list_states_is_refused_before_a_run_is_asked_for(file: Path):
    asked = OnDisk(file)
    with pytest.raises(TooLarge):
        take(asked, Stated(), io.BytesIO(), planned(file).bytes - 1)
    assert len(asked.asked) == 2


def test_a_footer_over_the_size_the_list_states_is_never_asked_for(file: Path):
    asked = OnDisk(file)
    with pytest.raises(TooLarge):
        take(asked, Stated(), io.BytesIO(), 100)
    assert len(asked.asked) == 1


# A file that is not laid out as the list says


def refused(path: Path, stated: Stated) -> str:
    with pytest.raises(NotLaidOut) as stopped:
        taken(path, stated)
    assert CANARY not in str(stopped.value)
    assert not any(name in str(stopped.value) for name in ("taxonomy", "bbox", "geometry"))
    return str(stopped.value)


def test_a_column_the_list_names_and_the_file_lacks_is_refused(tmp_path: Path):
    path = made_up_places(tmp_path / "places.parquet", a_town(), without=("taxonomy",))
    assert "lacks 1 of the columns" in refused(path, Stated())


def test_a_file_that_does_not_hold_the_box_of_each_row_is_refused(tmp_path: Path):
    path = made_up_places(tmp_path / "places.parquet", a_town(), without=("bbox",))
    assert "box of each row" in refused(path, Stated(columns=("geometry",)))
    whole = made_up_places(tmp_path / "whole.parquet", a_town())
    assert "box of each row" in refused(whole, Stated(box_in="geometry"))


def test_a_file_that_is_no_parquet_file_is_refused(tmp_path: Path):
    path = tmp_path / "page.html"
    path.write_bytes(b"<!doctype html><html><body>Sign in</body></html>" * 10)
    assert "does not end as a Parquet file ends" in refused(path, Stated())


def test_a_file_whose_end_gives_a_footer_longer_than_the_file_is_refused(tmp_path: Path):
    path = tmp_path / "short.parquet"
    path.write_bytes(MAGIC + b"\x00" * 20 + (5_000).to_bytes(4, "little") + MAGIC)
    assert "longer than the file" in refused(path, Stated())


def test_a_footer_that_places_a_column_outside_the_file_is_refused_before_a_run_is_asked_for(
    file: Path, tmp_path: Path
):
    """The footer is the publisher's, and says where each column lies. No byte is asked for
    on its word alone: a column that would lie past the rows of the file is refused."""
    whole = file.read_bytes()
    length = footer_bytes(whole[-TAIL:])
    short = tmp_path / "short.parquet"
    short.write_bytes(MAGIC + whole[-TAIL - length :])
    asked = OnDisk(short)
    with pytest.raises(NotLaidOut, match="outside the file"):
        take(asked, Stated(), io.BytesIO(), 10_000_000)
    assert asked.asked == [(len(MAGIC) + length, TAIL), (len(MAGIC), length)]


def test_a_footer_that_places_a_column_in_the_footer_itself_is_refused(file: Path, tmp_path: Path):
    """The last row group is cut short by one byte, so its last column runs into the footer."""
    whole = file.read_bytes()
    length = footer_bytes(whole[-TAIL:])
    footer = read_footer(whole[-TAIL - length : -TAIL])
    rows_end = max(chunk.first + chunk.count for chunk in footer.groups[-1].chunks)
    short = tmp_path / "short.parquet"
    short.write_bytes(whole[: rows_end - 1] + whole[-TAIL - length :])
    everywhere = Stated(box=(2.0, 53.0, 4.0, 54.0))
    asked = OnDisk(short)
    with pytest.raises(NotLaidOut, match="outside the file"):
        take(asked, everywhere, io.BytesIO(), 10_000_000)
    assert len(asked.asked) == 2


@pytest.mark.parametrize(
    "box", [(2.0, 53.0, 2.0, 54.0), (3.0, 53.0, 2.0, 54.0), (2.0, 54.0, 3.0, 53.0), (-181, 0, 0, 1)]
)
def test_a_box_that_is_no_box_is_refused(box: tuple[float, float, float, float]):
    with pytest.raises(ValueError, match="a box"):
        Box(*box)


# The part, read as the whole file is


def as_parquet(view: TakenFile) -> pq.ParquetFile:
    """The part as a Parquet library reads it: the footer first, then each column by itself.

    Left to itself the library asks for the columns of a row group in one
    piece, with what lies between them. It is told not to.
    """
    footer = pq.read_metadata(io.BytesIO(view.footer_alone()))
    return pq.ParquetFile(view, metadata=footer, pre_buffer=False)


def test_a_reader_that_looks_for_the_footer_in_the_part_itself_is_refused(
    file: Path, tmp_path: Path
):
    """It reads the end of the file in one piece, which starts among bytes not taken."""
    plan, part = taken(file)
    kept = tmp_path / "part"
    kept.write_bytes(part)
    with TakenFile(kept, plan.runs, plan.of_bytes) as view, pytest.raises(OSError):
        pq.ParquetFile(view)


def test_a_reader_of_parquet_reads_the_part_as_it_reads_the_whole(file: Path, tmp_path: Path):
    plan, part = taken(file)
    kept = tmp_path / "part"
    kept.write_bytes(part)
    whole = pq.ParquetFile(file)
    with TakenFile(kept, plan.runs, plan.of_bytes) as view:
        read = as_parquet(view)
        assert read.metadata.num_row_groups == 6
        for n in plan.row_groups:
            columns = list(TAKEN)
            assert read.read_row_group(n, columns=columns).equals(
                whole.read_row_group(n, columns=columns)
            )


def test_a_read_of_a_row_group_or_a_column_that_was_not_taken_is_refused(
    file: Path, tmp_path: Path
):
    plan, part = taken(file)
    kept = tmp_path / "part"
    kept.write_bytes(part)
    with TakenFile(kept, plan.runs, plan.of_bytes) as view:
        read = as_parquet(view)
        with pytest.raises(OSError, match="not taken"):
            read.read_row_group(0, columns=["geometry"])
        with pytest.raises(OSError, match="not taken"):
            read.read_row_group(1, columns=["names"])


def test_a_byte_that_was_not_taken_is_never_read_as_nothing(file: Path, tmp_path: Path):
    plan, part = taken(file)
    kept = tmp_path / "part"
    kept.write_bytes(part)
    whole = file.read_bytes()
    with TakenFile(kept, plan.runs, plan.of_bytes) as view:
        for first, count in plan.runs:
            view.seek(first)
            assert view.read(count) == whole[first : first + count]
        gap = plan.runs[0][0] + plan.runs[0][1]
        view.seek(gap)
        with pytest.raises(NotTaken):
            view.read(1)
        view.seek(gap - 1)
        with pytest.raises(NotTaken):
            view.read(2)
        view.seek(0, io.SEEK_END)
        assert (view.tell(), view.read(10)) == (len(whole), b"")


# A part held to what its receipt says, with no connection


def test_the_footer_in_a_part_gives_the_plan_the_part_was_taken_by(file: Path, tmp_path: Path):
    plan, part = taken(file)
    kept = tmp_path / "part"
    kept.write_bytes(part)
    assert plan_in(kept, plan.runs, plan.of_bytes, Stated()) == plan


def test_a_part_that_is_not_what_its_runs_say_is_refused(file: Path, tmp_path: Path):
    plan, part = taken(file)
    kept = tmp_path / "part"
    kept.write_bytes(part[:-1])
    with pytest.raises(NotLaidOut, match="as many bytes"):
        plan_in(kept, plan.runs, plan.of_bytes, Stated())
    kept.write_bytes(part)
    with pytest.raises(NotLaidOut, match="end of the file"):
        plan_in(kept, plan.runs, plan.of_bytes + 1, Stated())
    assert plan_in(kept, plan.runs, plan.of_bytes, Stated(box=(2.0, 53.0, 2.2, 54.0))) != plan
