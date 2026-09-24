"""The file of places, read for culture: the kind and the point of each venue.

Overture Maps Foundation publishes the places of the world as Parquet files,
a release at a time. Fetch takes the part of one file that lies round London,
and its receipt says which part: `fetch/take.py`. This module reads that part,
or a file that was kept whole, and nothing of it but what a count of venues
needs.

What the licence registry asks of the source, and what is done about each:

- **Aggregates only. No name of a place and no row of one is shown.** No name
  is read. What is kept of a record is its kind, its point and the dataset it
  came from, and a figure is a count.
- **Keep which source gave each record, so that records can be left out by
  licence.** The name of the dataset is read from `sources` and kept with
  every venue.
- **Build against `taxonomy` and `basic_category`, not the property that was
  removed.** The kind is read from `taxonomy` alone.
- **OpenStreetMap never drops, adds or corrects a record.** No record is
  dropped, added or moved for anything outside the file.
- **Pin one release.** A file is of the release its receipt states.

What is read of a record, and what is never read:

| Column | Read | For |
|---|---|---|
| `geometry` | Yes | The point. A place is a point, as well-known binary |
| `taxonomy` | Yes | `primary`, `hierarchy` and `alternates`: what it is |
| `operating_status` | Yes | Whether the file says the place has closed |
| `sources` | `dataset` alone | Which of the publisher's sources gave it |
| `confidence` | Yes | It is kept, and nothing is left out by it |
| `bbox`, `version`, `basic_category` | Never | Not needed |

`id`, `names`, `addresses`, `phones`, `websites`, `socials`, `emails` and
`brand` are never read. They say who a business is and how to reach it. The
list takes none of them, so a part holds none.

Of `sources` the one column that names the dataset is asked for, by its name
in the file's own layout, and nothing beside it: not the id that a source
gave a record, and not when it last changed. So a part that holds the name of
the dataset and nothing else of `sources` is read as one that holds it whole.

Nothing is filled in, and nothing is guessed:

- The kind of a record is what `culture_kinds.py` says its most particular
  category is. A category of culture that the table does not hold stops the
  build, so that a person says what it is.
- A record that the file says has closed for good is left out. A record that
  says nothing of whether it is open is counted: the file says nothing of
  nearly every record, so it cannot tell an open place from a closed one.
- A record with no point, or with a point that is nowhere on the earth, is
  counted as left out and is put nowhere.
- **Nothing is left out for how sure the publisher is.** The file gives each
  record a number between 0 and 1 for how sure its publisher is that the
  place exists. A first look found the number usable for the records of one
  source only. What floor to set, if any, is a person's to decide against a
  register. The number is kept with each venue so that one can be set.

This is the one module that names the Parquet library. The library carries no
types, so the type checker is told here, and only here, not to ask what it
returns. It is handed a file that is open, and is never given an address: it
opens no connection.

A refusal names the file by its id and the rule. It repeats nothing the file
holds: no category, no status and no number.
"""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportMissingTypeStubs=false

import io
import math
import struct
from collections import Counter
from collections.abc import Generator, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from burro_pipeline.derive.culture_kinds import Kind, LeftOut, NotOnTheTable, kind_of
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.fetch.take import TakenFile
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

SOURCE = "overture-places"
PUBLISHER = "Overture Maps Foundation"
# What the places are keyed by, as the parser finds them.
KEYED_BY = Geography.POINT
# The columns that are read, by their names in the file.
GEOMETRY, TAXONOMY, STATUS, SOURCES, CONFIDENCE = (
    "geometry",
    "taxonomy",
    "operating_status",
    "sources",
    "confidence",
)
READ = (GEOMETRY, TAXONOMY, STATUS, SOURCES, CONFIDENCE)
# What stands inside two of them.
PRIMARY, HIERARCHY, ALTERNATES, DATASET = "primary", "hierarchy", "alternates", "dataset"
# What the publisher writes of whether a place is open. Nothing at all is the most common.
OPEN, SHUT_FOR_NOW, CLOSED = "open", "temporarily_closed", "permanently_closed"
STATUSES = frozenset({None, OPEN, SHUT_FOR_NOW, CLOSED})
# A point as well-known binary writes one: its byte order, its type, and two numbers.
POINT, POINT_BYTES = 1, 21

Point = tuple[float, float]


@dataclass(frozen=True)
class Venue:
    """One record of a kind: what it is, where it is, and which source gave it."""

    longitude: float
    latitude: float
    kind: Kind
    datasets: tuple[str, ...]
    # How sure the publisher is that the place exists, from 0 to 1. None where it says nothing.
    confidence: float | None


def in_order(venue: Venue) -> tuple[float, float, str, tuple[str, ...], bool, float]:
    """Where a record stands among the records of a file: from west to east, then by what it is.

    Records are put in order by this and by nothing else, so that the order of
    a file changes nothing. A record that gives no number for how sure its
    publisher is stands before one on the same spot that gives one: nothing
    and a number cannot be held against each other.
    """
    sure = venue.confidence
    return (
        venue.longitude,
        venue.latitude,
        venue.kind.value,
        venue.datasets,
        sure is not None,
        0.0 if sure is None else sure,
    )


@dataclass(frozen=True)
class Places:
    """What one file of places holds of culture. No name and no row of a place is here."""

    # Every record of a kind, in the order of where it stands.
    venues: tuple[Venue, ...]
    # The point of every record that has one, whatever the record is.
    every: tuple[Point, ...]
    # How many rows were read, and how many of them were left out, by the reason.
    rows: int
    left_out: Mapping[LeftOut, int]
    # The records of a kind by their most particular category, and the records of culture
    # that were left out by theirs. A category is the publisher's word, and names no place.
    counted_as: Mapping[str, int]
    left_out_as: Mapping[str, int]
    file: Receipt

    @property
    def by_kind(self) -> dict[Kind, int]:
        found = Counter(venue.kind for venue in self.venues)
        return {kind: found[kind] for kind in Kind}

    @property
    def by_dataset(self) -> dict[str, int]:
        found = Counter(name for venue in self.venues for name in venue.datasets)
        return dict(sorted(found.items()))

    @property
    def as_at(self) -> str:
        """The day the file is as at, as its receipt gives it."""
        return self.file.data_period.days()[1]


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a file of places."""
    return name.startswith("part-") and name.endswith(".parquet")


def _not_as_described(opened: Opened, what: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, what)


def point_of(written: object) -> Point | None:
    """The point a record stands at, or none where its point is nowhere on the earth.

    Raises `ValueError` for what is no point as well-known binary writes one.
    """
    if not isinstance(written, bytes) or len(written) != POINT_BYTES or written[0] not in (0, 1):
        raise ValueError("a place is a point")
    order = "<" if written[0] == 1 else ">"
    kind, longitude, latitude = struct.unpack(f"{order}Idd", written[1:])
    if kind != POINT:
        raise ValueError("a place is a point")
    on_the_earth = (
        math.isfinite(longitude)
        and math.isfinite(latitude)
        and -180 <= longitude <= 180
        and -90 <= latitude <= 90
    )
    return (float(longitude), float(latitude)) if on_the_earth else None


def _words(held: object) -> tuple[str, ...]:
    """A list of categories as the file holds one, or none where it holds none."""
    if held is None:
        return ()
    if not isinstance(held, list) or not all(isinstance(one, str) for one in held):
        raise ValueError("a list of categories is a list of words")
    return tuple(held)


def _datasets(held: object) -> tuple[str, ...]:
    """The datasets a record came from, each once, in name order."""
    if held is None:
        return ()
    if not isinstance(held, list):
        raise ValueError("the sources of a record are a list")
    found: set[str] = set()
    for one in held:
        name = one.get(DATASET) if isinstance(one, dict) else None
        if not isinstance(name, str) or not name:
            raise ValueError("a source of a record names its dataset")
        found.add(name)
    return tuple(sorted(found))


@contextmanager
def _as_parquet(opened: Opened) -> Generator[tuple[Any, Sequence[int]]]:
    """The file as the Parquet library reads it, and the row groups it holds to read.

    A part is read through `TakenFile`, which refuses a read of a byte that
    was not taken. The library is handed the footer by itself first, and is
    told to read each column by itself and not the columns of a row group in
    one piece, which would take in what lies between them.
    """
    taken = opened.receipt.taken
    if taken is None:
        with opened.path.open("rb") as file:
            whole = pq.ParquetFile(file, pre_buffer=False)
            yield whole, range(whole.metadata.num_row_groups)
        return
    with TakenFile(opened.path, taken.runs, taken.of_bytes) as view:
        footer = pq.read_metadata(io.BytesIO(view.footer_alone()))
        if footer.num_row_groups != taken.of_row_groups:
            raise ValueError("the footer does not hold the row groups the receipt says")
        yield pq.ParquetFile(view, metadata=footer, pre_buffer=False), taken.row_groups


def _laid_out(opened: Opened, file: Any) -> None:
    """Stop unless the file holds the columns that are read, each as it is read."""
    layout = file.schema_arrow
    missing = [name for name in READ if name not in layout.names]
    if missing:
        raise _not_as_described(opened, "a column that is read is missing")
    taxonomy, sources = layout.field(TAXONOMY).type, layout.field(SOURCES).type
    inside = pa.types.is_struct(taxonomy) and {PRIMARY, HIERARCHY, ALTERNATES} <= {
        taxonomy.field(n).name for n in range(taxonomy.num_fields)
    }
    listed = pa.types.is_list(sources) and pa.types.is_struct(sources.value_type)
    named = listed and DATASET in {
        sources.value_type.field(n).name for n in range(sources.value_type.num_fields)
    }
    if not (inside and named and pa.types.is_binary(layout.field(GEOMETRY).type)):
        raise _not_as_described(opened, "a column that is read is not laid out as expected")


def dataset_in(layout: Sequence[str]) -> str:
    """The column inside `sources` that names the dataset, as the file's own layout names it.

    `layout` is every column of the file, each named from the top with a dot
    between. Raises `ValueError` where the file holds no such column, or more
    than one: which of two is meant is not guessed.
    """
    found = [
        path for path in layout if (path.split(".")[0], path.split(".")[-1]) == (SOURCES, DATASET)
    ]
    if len(found) != 1:
        raise ValueError("the sources of a record name one dataset each")
    return found[0]


def _rows(file: Any, groups: Sequence[int]) -> Iterator[tuple[Any, Any, Any, Any, Any]]:
    """Each row of the row groups given: its point, what it is, its status and its sources.

    Of its sources the name of the dataset is asked for and nothing beside it.
    """
    layout = [file.schema.column(n).path for n in range(file.metadata.num_columns)]
    asked = {SOURCES: dataset_in(layout)}
    for group in groups:
        columns = [
            file.read_row_group(group, columns=[asked.get(name, name)]).column(name).to_pylist()
            for name in READ
        ]
        yield from zip(*columns, strict=True)


def _said(taxonomy: Any, status: object) -> tuple[str | None, tuple[str, ...], tuple[str, ...]]:
    """What a row says it is: its most particular category, the path to it, and what else fits.

    Raises `ValueError` for a row that is not as the publisher is known to write one.
    """
    said = taxonomy or {}
    primary, path = said.get(PRIMARY), _words(said.get(HIERARCHY))
    if path and primary != path[-1]:
        raise ValueError("the most particular category ends the path to it")
    if status not in STATUSES:
        raise ValueError("a status the publisher is not known to write")
    return primary, path, _words(said.get(ALTERNATES))


@dataclass(frozen=True)
class Record:
    """One row of a file of places, as the file gives it. Nothing is decided of it here.

    It holds what the file says the place is, where it stands and which of the
    publisher's sources gave it. It holds no name, no address and no id.
    """

    primary: str | None
    hierarchy: tuple[str, ...]
    alternates: tuple[str, ...]
    # Where it stands, or none where its point is nowhere on the earth.
    at: Point | None
    # Whether the file says that it has closed for good.
    closed: bool
    datasets: tuple[str, ...]
    # How sure the publisher is that the place exists, from 0 to 1. None where it says nothing.
    confidence: float | None


def records(opened: Opened) -> Iterator[Record]:
    """Every row of a file of places, for a measure that has a table of kinds of its own.

    The same columns are read as for culture, and no other. Which record is
    what is the measure's to say, by its own table. Stops at a file that is
    not as expected.
    """
    try:
        with _as_parquet(opened) as (file, groups):
            _laid_out(opened, file)
            for geometry, taxonomy, status, sources, confidence in _rows(file, groups):
                primary, path, alternates = _said(taxonomy, status)
                sure = float(confidence) if isinstance(confidence, int | float) else None
                yield Record(
                    primary=primary if primary else None,
                    hierarchy=path,
                    alternates=alternates,
                    at=point_of(geometry),
                    closed=status == CLOSED,
                    datasets=_datasets(sources),
                    confidence=sure,
                )
    except LockError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError, pa.ArrowException):
        raise _not_as_described(opened, "it could not be read as a file of places") from None


def read(opened: Opened) -> Places:
    """What a file of places holds of culture. Stops at a file that is not as expected."""
    venues: list[Venue] = []
    every: list[Point] = []
    left_out: Counter[LeftOut] = Counter()
    counted_as: Counter[str] = Counter()
    left_out_as: Counter[str] = Counter()
    rows = 0
    try:
        with _as_parquet(opened) as (file, groups):
            _laid_out(opened, file)
            for geometry, taxonomy, status, sources, confidence in _rows(file, groups):
                rows += 1
                primary, path, alternates = _said(taxonomy, status)
                found = kind_of(primary, path, alternates)
                at = point_of(geometry)
                if at is not None:
                    every.append(at)
                why = found if isinstance(found, LeftOut) else None
                if why is None and status == CLOSED:
                    why = LeftOut.CLOSED
                if why is None and at is None:
                    why = LeftOut.NO_POINT
                if why is not None:
                    left_out[why] += 1
                    if why not in (LeftOut.NOT_CULTURE, LeftOut.NO_CATEGORY):
                        left_out_as[str(primary)] += 1
                    continue
                assert isinstance(found, Kind) and at is not None
                sure = float(confidence) if isinstance(confidence, int | float) else None
                venues.append(Venue(at[0], at[1], found, _datasets(sources), sure))
                counted_as[str(primary)] += 1
    except NotOnTheTable:
        raise _not_as_described(
            opened, "it holds a category of culture that the table of kinds does not hold"
        ) from None
    except LockError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError, pa.ArrowException):
        raise _not_as_described(opened, "it could not be read as a file of places") from None
    return Places(
        venues=tuple(sorted(venues, key=in_order)),
        every=tuple(sorted(every)),
        rows=rows,
        left_out=dict(sorted(left_out.items())),
        counted_as=dict(sorted(counted_as.items())),
        left_out_as=dict(sorted(left_out_as.items())),
        file=opened.receipt,
    )


def opened_of(inputs: Inputs, *, edition: str | None = None) -> Opened:
    """The file of places of the build, as it is handed over. The gate is asked first.

    `edition` is the release, as the receipt gives it. It tells apart the
    files of two releases, once the store holds both.
    """
    return inputs.open(SOURCE, Use.SCORING, edition=edition, named=is_the_file)


def build(inputs: Inputs, *, edition: str | None = None) -> Places:
    """The places of the build, read for culture. The gate is asked before the file is opened."""
    return read(opened_of(inputs, edition=edition))
