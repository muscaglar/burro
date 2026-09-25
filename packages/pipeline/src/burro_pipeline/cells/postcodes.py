"""A postcode, as it is typed, to a point and to the census areas it is in.

Many files give a place by its postcode alone. The statistics office's
postcode directory gives each postcode one point on the National Grid and the
output area, the LSOA and the MSOA that point is in. With it such a place can
be put on the map.

**What the licence registry asks of the directory, and what is done here.**

| The registry says | So here |
|---|---|
| All three credits are required | `CREDITS` holds the three, with the year of the data |
| Drop every row of Northern Ireland at ingest | Its file is never opened, and see below |
| Keep London's authorities alone | A row is kept only where its authority is London's |
| Never pass the national file on | Nothing is written. What is kept is held in memory |
| A row of a postcode is never shown, exported or committed | No postcode leaves here |

**Northern Ireland.** The guide inside the zip says that to use a postcode of
Northern Ireland is to accept terms of its own. So the file of its postcode
area is never opened. A line of any other file that begins as one of its
postcodes does is dropped before it is split into columns, so no column of it
is read. A row whose postcode is one of its own is dropped whatever its line
began with.

**No postcode leaves this module.** The lookup answers one question: where is
the postcode I hold. What it gives back holds a point and the codes of areas,
and no postcode. It cannot be asked for its postcodes, for those of an area,
or for those near a point. What it prints of itself is counts. A refusal
repeats nothing from a row.

**A district is no postcode.** It is what stands before the space, which the
postcodes of some thousands of addresses share, and it is how the statistics
office gives the rents of London. `in_use_by_district` counts the postcodes in
use of each output area by it, and gives back no postcode.

**What is read.** The zip holds the directory three times over. The file of
each postcode area is read, under `Data/multi_csv/`, and the whole file is
never opened. A file is found by its name in the list the zip keeps of itself,
and is opened only where its whole name is that of the file of an area. Nine
columns are read, by name:

| Column | What it is |
|---|---|
| `pcds` | The postcode, with one space |
| `doterm` | The month the postcode ended, or nothing while it is in use |
| `lad26cd` | The local authority the point is in |
| `east1m`, `north1m` | The point, on the National Grid, to the metre |
| `gridind` | How good the point is, from 1 to 9 |
| `oa21cd`, `lsoa21cd`, `msoa21cd` | The census areas of 2021 the point is in |

Five columns say something of who lives in an area, and are never read:
`NEVER_READ`. A row that is handed on holds the nine columns and no other.

**What the point is.** The guide inside the zip says it is the mean of all the
addresses of the postcode, moved to the address nearest that mean. So it is a
door of the postcode, and not the door of any one place in it. `QUALITY` says
what each mark of `gridind` means, in the guide's words.

**A postcode that has ended** is in the directory with the month it ended, and
is kept. The guide says that such a postcode keeps its point, and that its
areas are brought up to date at each edition. A register of businesses is
older than the directory, so a place may give a postcode that has since
ended. It is placed where its postcode last stood, and what is given back
says that it has ended, and when. It is never counted as in use. Whether a
place at an ended postcode is counted is for the measure to say.

**How a postcode is read as typed.** Every space is taken out and every
letter is made a capital. What is left must have the shape of a postcode.
Nothing is corrected: a letter typed for a digit is not found.

What it cannot see:

- Where in its postcode a place stands. The point is one door of several.
- A postcode with no point. The directory gives such a postcode no authority,
  so it is never a row of London, and is not found.
- A postcode outside London. The registry keeps London's rows alone.
- A postcode that was ended and then given out again. The guide says the
  directory then holds the new place alone.
"""

import csv
import io
import re
import zipfile
from collections import Counter
from collections.abc import Generator, Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import lru_cache

from burro_pipeline.cells.spine import Spine
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

SOURCE = "ons-postcode-directory"
PUBLISHER = "Office for National Statistics"
# What a measure puts the directory to: it places what a figure counts. The registry lists
# the use for that reason alone.
USE = Use.SCORING
# The three credits the registry asks for, with the year of the data in each.
CREDITS = (
    "Contains OS data © Crown copyright and database right {year}",
    "Contains Royal Mail data © Royal Mail copyright and database right {year}",
    "Source: Office for National Statistics licensed under the Open Government Licence v.3.0",
)

# The publisher's name for the zip gives the month and the year of the edition.
ZIP = re.compile(r"ONSPD_(?P<edition>[A-Z]{3}_[0-9]{4})\.zip")
# Where the zip keeps the file of each postcode area, and how such a file is named.
FOLDER = "Data/multi_csv/"
AREA_FILE = "Data/multi_csv/ONSPD_{edition}_UK_{area}.csv"
AN_AREA = re.compile(r"[A-Z]{1,2}")
# The postcode area of Northern Ireland. Its file is never opened, and no row of it is kept.
NORTHERN_IRELAND = "BT"
# The code of every London borough, and of the City, starts so.
LONDON = "E09"

POSTCODE, ENDED, AUTHORITY = "pcds", "doterm", "lad26cd"
EASTING, NORTHING, QUALITY_MARK = "east1m", "north1m", "gridind"
OA, LSOA, MSOA = "oa21cd", "lsoa21cd", "msoa21cd"
# The columns that are read, and no other.
READ = (POSTCODE, ENDED, AUTHORITY, EASTING, NORTHING, QUALITY_MARK, OA, LSOA, MSOA)
# The columns that say something of who lives in an area. None is ever read.
NEVER_READ = ("oac01ind", "oac11ind", "oac21ind", "imd20ind", "imd25ind")
# Every column of the file of an area, in its order, as the edition of August 2026 names them.
HELD = (
    "pcd7",
    "pcd8",
    "pcds",
    "dointr",
    "doterm",
    "cty26cd",
    "ced25cd",
    "lad26cd",
    "wd26cd",
    "parncp26cd",
    "usrtypind",
    "east1m",
    "north1m",
    "gridind",
    "hlth19cd",
    "nhser24cd",
    "ctry26cd",
    "rgn26cd",
    "ssr95cd",
    "pcon24cd",
    "eer20cd",
    "educ23cd",
    "ttwa15cd",
    "pco19cd",
    "itl25cd",
    "wdstl05cd",
    "oa01cd",
    "wdcas03cd",
    "npark16cd",
    "lsoa01cd",
    "msoa01cd",
    "ruc01ind",
    "oac01ind",
    "oa11cd",
    "lsoa11cd",
    "msoa11cd",
    "wz11cd",
    "sicbl26cd",
    "bua24cd",
    "ruc11ind",
    "oac11ind",
    "lat",
    "long",
    "lep21cd1",
    "lep21cd2",
    "pfa23cd",
    "imd20ind",
    "cal26cd",
    "icb26cd",
    "oa21cd",
    "lsoa21cd",
    "msoa21cd",
    "ruc21ind",
    "oac21ind",
    "imd25ind",
)

# The shape of a postcode with its space taken out: the area, the district, the sector and
# the unit. It is the shape alone, and says nothing of whether a postcode exists.
SHAPE = re.compile(r"[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}")
A_MONTH = re.compile(r"(?P<year>[0-9]{4})(?P<month>0[1-9]|1[0-2])")
A_LENGTH = re.compile(r"[0-9]{1,7}")
OF_AN_OA = re.compile(r"E00[0-9]{6}")
OF_AN_LSOA = re.compile(r"E01[0-9]{6}")
OF_AN_MSOA = re.compile(r"E02[0-9]{6}")
OF_LONDON = re.compile(r"E09[0-9]{6}")

# What each mark of the quality of a point means, as the guide inside the zip gives it.
QUALITY: Mapping[int, str] = {
    1: "within the building of the matched address closest to the postcode mean",
    2: "as for 1, except by visual inspection of maps, in Scotland only",
    3: "approximate to within 50 metres",
    4: "the mean of the matched addresses of the postcode, not moved to a building",
    5: "imputed by the statistics office, by reference to the postcodes round it",
    6: "the mean of the postcode sector, mainly for PO boxes",
    8: "a postcode ended before November 2000, with the last point known for it",
    9: "no point",
}
# The marks of a point that is of the postcode's own addresses, or is put among its
# neighbours. A point of mark 6 is the middle of a sector, which holds thousands of
# addresses, and one of mark 8 is mainly to the nearest 100 metres: each is a place on the
# map, and neither is good for a distance of a few hundred metres.
GOOD_FOR_A_DISTANCE = frozenset({1, 2, 3, 4, 5})

Point = tuple[float, float]
# One row as it is kept: the point, the output area, the quality, the month it ended and the
# authority. The authority is kept with the row, and not with the output area: the directory
# puts a point in the authority it stands in today, and an output area of 2021 may lie across
# the border of two.
_Kept = tuple[int, int, str, int, str | None, str]


@dataclass(frozen=True)
class Placed:
    """Where a postcode is. It holds no postcode."""

    # On the National Grid, in metres.
    point: Point
    oa: str
    lsoa: str
    msoa: str
    # The code of the London borough, or of the City, that the point stands in today. It is
    # the directory's own, and may not be the borough a build puts the output area in.
    borough: str
    # The publisher's mark of how good the point is: a key of `QUALITY`.
    quality: int
    # The month the postcode ended, as `2019-03`, or nothing while it is in use.
    ended: str | None

    @property
    def in_use(self) -> bool:
        return self.ended is None

    @property
    def good_for_a_distance(self) -> bool:
        """Whether the point is near enough its addresses for a distance to be measured to it."""
        return self.quality in GOOD_FOR_A_DISTANCE


@dataclass(frozen=True)
class Counts:
    """What was read, as counts. Nothing here is held to a number: a test on the real file is."""

    # The files of postcode areas in the zip, and how many of them were opened.
    files: int
    opened: int
    # The rows that were read, of every authority, and the lines dropped for Northern Ireland.
    rows: int
    dropped_for_northern_ireland: int
    # The rows of London, and how they divide.
    london: int
    in_use: int
    ended: int
    # The rows of London by the quality of their point: those in use, and those that ended.
    quality_in_use: Mapping[int, int]
    quality_ended: Mapping[int, int]
    # The postcode areas that hold a row of London, with how many rows of it each holds.
    areas: Mapping[str, int]


@dataclass(frozen=True, repr=False, eq=False)
class Lookup:
    """London's postcodes, each with its point and its areas. It gives none of them out."""

    receipt: Receipt
    counts: Counts
    _rows: Mapping[str, _Kept] = field(repr=False)
    # The LSOA and the MSOA of each output area, as the directory gives them.
    _part_of: Mapping[str, tuple[str, str]] = field(repr=False)

    def __repr__(self) -> str:
        """Counts alone, so that a line that prints the lookup prints no postcode."""
        held = self.counts
        return f"Lookup(london={held.london}, in_use={held.in_use}, ended={held.ended})"

    def __len__(self) -> int:
        return len(self._rows)

    def place(self, typed: str) -> Placed | None:
        """Where a postcode is, as it was typed, or nothing where London holds none such."""
        key = key_of(typed)
        kept = None if key is None else self._rows.get(key)
        if kept is None:
            return None
        east, north, oa, quality, ended, borough = kept
        lsoa, msoa = self._part_of[oa]
        return Placed((float(east), float(north)), oa, lsoa, msoa, borough, quality, ended)

    def in_use_by_output_area(self) -> dict[str, int]:
        """How many postcodes in use stand in each output area. It names no postcode."""
        found: Counter[str] = Counter(kept[2] for kept in self._rows.values() if kept[4] is None)
        return dict(sorted(found.items()))

    def in_use_by_district(self) -> dict[str, dict[str, int]]:
        """How many postcodes in use stand in each output area, by their postcode district.

        A district is what stands before the space of a postcode. An output
        area with no postcode in use is not among them. It names no postcode.
        """
        found: dict[str, Counter[str]] = {}
        for key, kept in self._rows.items():
            if kept[4] is None:
                # A postcode is kept with no space, and what follows the space is three long.
                found.setdefault(kept[2], Counter())[key[:-3]] += 1
        return {oa: dict(sorted(found[oa].items())) for oa in sorted(found)}

    def in_use_by_borough(self) -> dict[str, int]:
        """How many postcodes in use stand in each borough, by its code."""
        found: Counter[str] = Counter(kept[5] for kept in self._rows.values() if kept[4] is None)
        return dict(sorted(found.items()))

    def points_in_use(self) -> list[Point]:
        """The point of every postcode in use, in a fixed order, and no postcode with it."""
        return sorted(
            (float(kept[0]), float(kept[1])) for kept in self._rows.values() if kept[4] is None
        )

    def not_of(self, spine: Spine) -> dict[str, int]:
        """What of the lookup does not fit the areas of a build, as counts.

        A postcode is in an area of the build where its output area is one of
        the spine's. The directory and the spine are then held to each other:
        the LSOA and the MSOA of an output area, and the borough of a postcode.
        A borough may differ and the area still be known: an area is made of
        output areas, whatever borough a point stands in today.
        """
        cells = {cell.oa: (cell.lsoa, cell.msoa, cell.borough) for cell in spine.cells}
        rows = list(self._rows.values())
        no_area = [kept for kept in rows if kept[2] not in cells]
        elsewhere = [kept for kept in rows if kept[2] in cells and cells[kept[2]][2] != kept[5]]
        differs = [oa for oa, parts in self._part_of.items() if cells.get(oa, parts)[:2] != parts]
        in_use = self.in_use_by_output_area()
        return {
            "in_no_area": len(no_area),
            "in_use_in_no_area": sum(1 for kept in no_area if kept[4] is None),
            "in_another_borough": len(elsewhere),
            "in_use_in_another_borough": sum(1 for kept in elsewhere if kept[4] is None),
            "output_areas_in_another_lsoa_or_msoa": len(differs),
            "output_areas_with_none_in_use": sum(1 for oa in spine.area_of if oa not in in_use),
        }


def key_of(typed: str) -> str | None:
    """A postcode as it is looked up: no space and all capitals, or nothing for any other text.

    It asks only whether the text has the shape of a postcode. Nothing is
    corrected, and nothing is guessed. A letter outside ASCII is looked for
    before any letter is made a capital: made a capital, a dotless i is an I
    and a long s an S, and the text would be read as a postcode it is not.
    """
    joined = "".join(typed.split())
    if not joined.isascii():
        return None
    joined = joined.upper()
    return joined if SHAPE.fullmatch(joined) else None


def credits_of(receipt: Receipt) -> tuple[str, ...]:
    """The three credits, with the year of the data the receipt gives."""
    year = receipt.data_period.days()[0][:4]
    return tuple(credit.format(year=year) for credit in CREDITS)


def _not_as_described(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def _edition(opened: Opened) -> str:
    named = ZIP.fullmatch(opened.receipt.publisher_file)
    if named is None:
        raise _not_as_described(opened, "it is not named as the directory is")
    return named["edition"]


def _area_of(opened: Opened, name: str) -> str | None:
    """The postcode area a file is of, by its whole name, or nothing for any other name."""
    start, _, end = AREA_FILE.format(edition=_edition(opened), area="\n").partition("\n")
    if not (name.startswith(start) and name.endswith(end)):
        return None
    area = name[len(start) : len(name) - len(end)]
    return area if AN_AREA.fullmatch(area) else None


def area_files(opened: Opened) -> dict[str, str]:
    """The file of every postcode area in the zip, by its area. No file is opened.

    The names are read from the list the zip keeps of itself. The file of
    Northern Ireland is named here, so that it can be counted, and is opened
    nowhere. A name in the folder that is not the name of a file of an area
    stops the step: a file must not be passed over without a word.
    """
    try:
        with zipfile.ZipFile(opened.path) as archive:
            names = [name for name in archive.namelist() if not name.endswith("/")]
    except (zipfile.BadZipFile, OSError):
        raise _not_as_described(opened, "it is not a zip") from None
    found: dict[str, str] = {}
    for name in sorted(names):
        if not name.startswith(FOLDER):
            continue
        area = _area_of(opened, name)
        if area is None or area in found:
            raise _not_as_described(opened, "a file is not named for a postcode area")
        found[area] = name
    if not set(found) - {NORTHERN_IRELAND}:
        raise _not_as_described(opened, "it holds no file of a postcode area")
    return found


def _not_of_northern_ireland(lines: Iterable[str], dropped: list[int]) -> Iterator[str]:
    """The lines of a file, but for any that begins as a postcode of Northern Ireland does.

    A line is dropped by its first two letters, before it is split into
    columns, so no column of it is ever read.
    """
    for line in lines:
        if line.lstrip('"')[: len(NORTHERN_IRELAND)] == NORTHERN_IRELAND:
            dropped[0] += 1
        else:
            yield line


@contextmanager
def _table(opened: Opened, name: str, dropped: list[int]) -> Generator[Iterator[list[str]]]:
    """The file of one postcode area, as rows. It is the one place a file of the zip is opened.

    `name` is held to the whole name of the file of an area before the zip is
    asked for anything, and the file of Northern Ireland is refused by its
    name. So no other file of the zip can be opened through here.
    """
    area = _area_of(opened, name)
    if area is None or area == NORTHERN_IRELAND:
        raise _not_as_described(
            opened, "it was asked for a file that is not read, and no other is opened"
        )
    try:
        archive = zipfile.ZipFile(opened.path)
    except (zipfile.BadZipFile, OSError):
        raise _not_as_described(opened, "it is not a zip") from None
    with archive:
        try:
            raw = archive.open(name)
        except KeyError:
            raise _not_as_described(opened, "it does not hold the file that is read") from None
        except (zipfile.BadZipFile, OSError, NotImplementedError, RuntimeError):
            raise _not_as_described(opened, "a file of an area could not be opened") from None
        with raw:
            text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            try:
                yield csv.reader(_not_of_northern_ireland(text, dropped))
            except (zipfile.BadZipFile, OSError, EOFError, UnicodeDecodeError, csv.Error):
                raise _not_as_described(
                    opened, "a file of an area could not be read as a table"
                ) from None


def columns_of(opened: Opened, name: str) -> tuple[str, ...]:
    """The names of the columns of the file of one area, as its first line gives them.

    Names only: no row is read.
    """
    nothing: list[str] = []
    with _table(opened, name, [0]) as table:
        return tuple(next(table, nothing))


def _month(text: str) -> str | None:
    found = A_MONTH.fullmatch(text)
    return None if found is None else f"{found['year']}-{found['month']}"


def _kept_of(opened: Opened, row: Mapping[str, str]) -> tuple[str, _Kept, tuple[str, str]]:
    """One row of London as it is kept, once every value of it has the shape it should."""
    key = key_of(row[POSTCODE])
    if key is None or row[POSTCODE] != f"{key[:-3]} {key[-3:]}":
        raise _not_as_described(opened, "a postcode is not written as the directory writes one")
    ended = _month(row[ENDED]) if row[ENDED] else None
    if row[ENDED] and ended is None:
        raise _not_as_described(opened, "the month a postcode ended is no month")
    mark = row[QUALITY_MARK]
    if not (mark.isascii() and mark.isdigit() and int(mark) in QUALITY):
        raise _not_as_described(opened, "the quality of a point is not one the guide names")
    if not (A_LENGTH.fullmatch(row[EASTING]) and A_LENGTH.fullmatch(row[NORTHING])):
        raise _not_as_described(opened, "a row of London has no point")
    codes = ((OF_AN_OA, OA), (OF_AN_LSOA, LSOA), (OF_AN_MSOA, MSOA), (OF_LONDON, AUTHORITY))
    if not all(shape.fullmatch(row[name]) for shape, name in codes):
        raise _not_as_described(opened, "a code is not a code")
    kept = (int(row[EASTING]), int(row[NORTHING]), row[OA], int(mark), ended, row[AUTHORITY])
    return key, kept, (row[LSOA], row[MSOA])


def _rows_of_london(
    opened: Opened, name: str, dropped: list[int], read: list[int]
) -> Iterator[dict[str, str]]:
    """The rows of one file whose authority is London's, each with the nine columns alone."""
    with _table(opened, name, dropped) as table:
        header = next(table, None)
        if header is None or not set(READ) <= set(header):
            raise _not_as_described(opened, "a column is missing")
        if len(set(header)) != len(header):
            raise _not_as_described(opened, "a column is named twice")
        at = [header.index(column) for column in READ]
        of_authority, last = header.index(AUTHORITY), max(at)
        for row in table:
            read[0] += 1
            if len(row) <= last:
                raise _not_as_described(opened, "a row is short")
            if row[of_authority].startswith(LONDON):
                yield {column: row[place] for column, place in zip(READ, at, strict=True)}


def read(opened: Opened) -> Lookup:
    """The lookup, from the directory as it was saved.

    It stops at a zip that is not named or laid out as the directory is, at a
    file that lacks a column that is read, at a row of London that is not
    written as the guide says, at a postcode that is there twice, and at an
    output area that the directory puts in two LSOAs or two MSOAs.

    A build asks for the lookup once for each measure that places something.
    A copy was held to the hash in its receipt when it was handed over, so the
    copy of one receipt in one place is read once.
    """
    return _read(opened)


@lru_cache(maxsize=2)
def _read(opened: Opened) -> Lookup:
    files = area_files(opened)
    rows: dict[str, _Kept] = {}
    part_of: dict[str, tuple[str, str]] = {}
    areas: Counter[str] = Counter()
    quality_in_use: Counter[int] = Counter()
    quality_ended: Counter[int] = Counter()
    dropped, read_in = [0], [0]
    read_from = sorted(area for area in files if area != NORTHERN_IRELAND)
    for area in read_from:
        for row in _rows_of_london(opened, files[area], dropped, read_in):
            key, kept, parts = _kept_of(opened, row)
            # Whatever a line began with, no row of Northern Ireland is kept.
            if key.startswith(NORTHERN_IRELAND):
                dropped[0] += 1
                continue
            if key in rows:
                raise _not_as_described(opened, "a postcode is there twice")
            if part_of.setdefault(kept[2], parts) != parts:
                raise _not_as_described(opened, "a unit is part of two others")
            rows[key] = kept
            areas[area] += 1
            (quality_in_use if kept[4] is None else quality_ended)[kept[3]] += 1
    in_use = sum(quality_in_use.values())
    counts = Counts(
        files=len(files),
        opened=len(read_from),
        rows=read_in[0],
        dropped_for_northern_ireland=dropped[0],
        london=len(rows),
        in_use=in_use,
        ended=len(rows) - in_use,
        quality_in_use=dict(sorted(quality_in_use.items())),
        quality_ended=dict(sorted(quality_ended.items())),
        areas=dict(sorted(areas.items())),
    )
    return Lookup(receipt=opened.receipt, counts=counts, _rows=rows, _part_of=part_of)


def build(inputs: Inputs, *, use: Use = USE, edition: str | None = None) -> Lookup:
    """The lookup, from the files of the build. The gate is asked before anything is read."""
    return read(inputs.open(SOURCE, use, edition=edition))
