"""The footer of a Parquet file: its row groups, and where each column of each lies.

A Parquet file is a run of row groups and then a footer. The footer says, for
every row group, where the bytes of each column are, and the least and the
most of what the column holds there. The file ends with the length of the
footer, in four bytes, and four letters that say what the file is. So a reader
that has the end of a file knows where every other part of it is, and what it
could hold, before it has read any row.

This module reads a footer and nothing else. It opens no file and no
connection: it is handed bytes. It reads no row, because a footer holds none.
What it keeps of a footer is what taking part of the file turns on, and no
more: how many rows a row group has, the path of each column in it, where the
column's bytes start, how many there are, and the least and the most the
publisher's writer recorded of a column of numbers. The least and the most of
a column of text are two of its values, which of a file of places may be a
name or an address: they are not kept, and nothing this module hands back
holds one.

A footer is written in the compact form of Thrift, which the format's own
definition gives field by field. The numbers of the fields that are read are
named below, each as that definition numbers it. A field that is not read is
stepped over by its type, so a footer from a later version of the format is
read as long as the fields that are read still mean what they did.

A footer that cannot be read is refused in a few fixed words. They repeat
nothing the file holds.
"""

import struct
from dataclasses import dataclass

MAGIC = b"PAR1"
# What a file ends with: the length of the footer, in four bytes, and the magic.
TAIL = 8
# The most a footer may nest, and the most items a list in it may say it holds. A
# footer that says more is not read: it is cut short, or is not a footer.
DEEPEST = 32
MOST_ITEMS = 50_000_000

# The types of the compact form, as its definition numbers them.
STOP, TRUE, FALSE, BYTE, I16, I32, I64, DOUBLE, BINARY, LIST, SET, MAP, STRUCT, UUID = range(14)
# The fields of the footer that are read, as the format's definition numbers them.
ROWS_OF_THE_FILE, ROW_GROUPS = 3, 4
COLUMNS_OF_A_GROUP, ROWS_OF_A_GROUP = 1, 3
IN_ANOTHER_FILE, ABOUT_THE_COLUMN = 1, 3
PHYSICAL, PATH, PACKED_BYTES, FIRST_PAGE, INDEX_PAGE, DICTIONARY_PAGE, STATISTICS = (
    1,
    3,
    7,
    9,
    10,
    11,
    12,
)
MOST_OLD, LEAST_OLD, MOST, LEAST = 1, 2, 5, 6
# The two physical types a coordinate is written as, and how each is unpacked.
FLOAT, DOUBLE_TYPE = 4, 5
UNPACKED = {FLOAT: "<f", DOUBLE_TYPE: "<d"}

Tree = dict[int, object]


class NotAFooter(Exception):
    """What was handed over is not the footer of a Parquet file. Safe to print."""

    def __init__(self, why: str = "it could not be read as the footer of a Parquet file") -> None:
        super().__init__(why)


@dataclass(frozen=True)
class Chunk:
    """One column of one row group: where its bytes lie, and what they could hold."""

    # The column as the file's own layout names it, from the top: `bbox`, `xmin`.
    path: tuple[str, ...]
    physical: int
    # The first byte of the column in the file, and how many bytes it takes there.
    first: int
    count: int
    # The least and the most the writer recorded of a column of numbers, as the file holds
    # them. None where it recorded none, and of every column of anything else.
    least: bytes | None = None
    most: bytes | None = None

    def number(self, held: bytes | None) -> float | None:
        """A least or a most as a number, where the column is one of numbers with a point."""
        form = UNPACKED.get(self.physical)
        if held is None or form is None or len(held) != struct.calcsize(form):
            return None
        (value,) = struct.unpack(form, held)
        return float(value)


@dataclass(frozen=True)
class RowGroup:
    rows: int
    chunks: tuple[Chunk, ...]


@dataclass(frozen=True)
class Footer:
    rows: int
    groups: tuple[RowGroup, ...]

    @property
    def columns(self) -> tuple[str, ...]:
        """The columns of the file by their first name, in the order the file holds them."""
        seen: dict[str, None] = {}
        for group in self.groups[:1]:
            for chunk in group.chunks:
                seen.setdefault(chunk.path[0])
        return tuple(seen)


def footer_bytes(tail: bytes) -> int:
    """How long the footer is, read from the last eight bytes of a file."""
    if len(tail) != TAIL or tail[4:] != MAGIC:
        raise NotAFooter("it does not end as a Parquet file ends")
    (length,) = struct.unpack("<I", tail[:4])
    if length < 1:
        raise NotAFooter
    return int(length)


class _Reader:
    """Reads the compact form from bytes. Every read is held to the bytes there are."""

    def __init__(self, data: bytes) -> None:
        self._data, self._at = data, 0

    def _take(self, count: int) -> bytes:
        if count < 0 or self._at + count > len(self._data):
            raise NotAFooter
        held = self._data[self._at : self._at + count]
        self._at += count
        return held

    def _varint(self) -> int:
        value, shift = 0, 0
        while True:
            (byte,) = self._take(1)
            value |= (byte & 0x7F) << shift
            if not byte & 0x80:
                return value
            shift += 7
            if shift > 63:
                raise NotAFooter

    def _whole(self) -> int:
        value = self._varint()
        return (value >> 1) ^ -(value & 1)

    def _list(self, deeper: int) -> list[object]:
        (head,) = self._take(1)
        count, kind = head >> 4, head & 0x0F
        if count == 15:
            count = self._varint()
        if count > min(MOST_ITEMS, len(self._data) - self._at):
            raise NotAFooter
        return [self.value(kind, deeper, in_a_list=True) for _ in range(count)]

    def _map(self, deeper: int) -> list[object]:
        count = self._varint()
        if count == 0:
            return []
        if count > min(MOST_ITEMS, len(self._data) - self._at):
            raise NotAFooter
        (kinds,) = self._take(1)
        return [
            (self.value(kinds >> 4, deeper, in_a_list=True), self.value(kinds & 0x0F, deeper, True))
            for _ in range(count)
        ]

    def value(self, kind: int, deeper: int, in_a_list: bool = False) -> object:
        """One value of a type. A truth value in a struct is its type, and holds no byte."""
        if deeper < 1:
            raise NotAFooter
        if kind in (TRUE, FALSE):
            return (self._take(1) == b"\x01") if in_a_list else kind == TRUE
        if kind == BYTE:
            return self._take(1)[0]
        if kind in (I16, I32, I64):
            return self._whole()
        if kind == DOUBLE:
            return struct.unpack("<d", self._take(8))[0]
        if kind == BINARY:
            return self._take(self._varint())
        if kind in (LIST, SET):
            return self._list(deeper - 1)
        if kind == MAP:
            return self._map(deeper - 1)
        if kind == STRUCT:
            return self.struct(deeper - 1)
        if kind == UUID:
            return self._take(16)
        raise NotAFooter

    def struct(self, deeper: int = DEEPEST) -> Tree:
        """The fields of a struct, by their numbers."""
        found: Tree = {}
        last = 0
        while True:
            (head,) = self._take(1)
            if head == STOP:
                return found
            step, kind = head >> 4, head & 0x0F
            last = last + step if step else self._whole()
            found[last] = self.value(kind, deeper)


def _whole_number(tree: Tree, field: int) -> int | None:
    held = tree.get(field)
    return held if isinstance(held, int) and not isinstance(held, bool) else None


def _held(tree: Tree, field: int) -> bytes | None:
    held = tree.get(field)
    return held if isinstance(held, bytes) else None


def _structs(tree: Tree, field: int) -> list[Tree]:
    held = tree.get(field)
    if not isinstance(held, list):
        raise NotAFooter
    found: list[Tree] = []
    for one in held:  # pyright: ignore[reportUnknownVariableType]
        if not isinstance(one, dict):
            raise NotAFooter
        found.append(one)  # pyright: ignore[reportUnknownArgumentType]
    return found


def _chunk(written: Tree) -> Chunk:
    """One column of one row group, or a refusal where the footer does not say where it is."""
    about = written.get(ABOUT_THE_COLUMN)
    if written.get(IN_ANOTHER_FILE) is not None or not isinstance(about, dict):
        raise NotAFooter("a column of it is kept in another file, or is locked")
    tree: Tree = about  # pyright: ignore[reportUnknownVariableType]
    names = tree.get(PATH)
    physical = _whole_number(tree, PHYSICAL)
    packed, page = _whole_number(tree, PACKED_BYTES), _whole_number(tree, FIRST_PAGE)
    if not isinstance(names, list) or not names or physical is None:
        raise NotAFooter
    if packed is None or page is None or packed < 1 or page < len(MAGIC):
        raise NotAFooter
    path: list[str] = []
    for name in names:  # pyright: ignore[reportUnknownVariableType]
        if not isinstance(name, bytes):
            raise NotAFooter
        try:
            path.append(name.decode("utf-8"))
        except UnicodeDecodeError:
            raise NotAFooter from None
    # A column starts at its dictionary where it has one, and at its first page where not.
    first = page
    for before in (_whole_number(tree, DICTIONARY_PAGE), _whole_number(tree, INDEX_PAGE)):
        if before is not None and len(MAGIC) <= before < first:
            first = before
    recorded = tree.get(STATISTICS)
    least = most = None
    # The least and the most of a column of text are two of its values: of a file of places,
    # a name or an address. They are kept of a column of numbers and of no other.
    if isinstance(recorded, dict) and physical in UNPACKED:
        said: Tree = recorded  # pyright: ignore[reportUnknownVariableType]
        least = _held(said, LEAST) if LEAST in said else _held(said, LEAST_OLD)
        most = _held(said, MOST) if MOST in said else _held(said, MOST_OLD)
    return Chunk(tuple(path), physical, first, packed, least, most)


def read_footer(footer: bytes) -> Footer:
    """The row groups of a file, from the bytes of its footer."""
    try:
        tree = _Reader(footer).struct()
    except (RecursionError, struct.error):
        raise NotAFooter from None
    rows = _whole_number(tree, ROWS_OF_THE_FILE)
    if rows is None or rows < 0:
        raise NotAFooter
    groups: list[RowGroup] = []
    for written in _structs(tree, ROW_GROUPS):
        in_the_group = _whole_number(written, ROWS_OF_A_GROUP)
        if in_the_group is None or in_the_group < 0:
            raise NotAFooter
        chunks = tuple(_chunk(one) for one in _structs(written, COLUMNS_OF_A_GROUP))
        if not chunks:
            raise NotAFooter
        groups.append(RowGroup(in_the_group, chunks))
    if sum(group.rows for group in groups) != rows:
        raise NotAFooter("its row groups do not hold as many rows as it says it holds")
    paths = {tuple(chunk.path for chunk in group.chunks) for group in groups}
    if len(paths) > 1:
        raise NotAFooter("its row groups do not hold the same columns")
    return Footer(rows, tuple(groups))
