"""The crime files of the police's zip, and no other file of it.

The form at data.police.uk makes one zip for the forces and the months that
are chosen. It holds a folder for each month, and in it a file for each force
and each kind of data that was ticked:

    2023-08/2023-08-metropolitan-street.csv            recorded crime
    2023-08/2023-08-metropolitan-outcomes.csv          what became of a crime
    2023-08/2023-08-metropolitan-stop-and-search.csv   each person stopped

The zip that was saved on 2026-09-24 holds all three kinds. The registry
entry allows the first alone. The founder decided that day that the zip is
kept as it was saved, that the crime files alone are read, and that the rest
of it is never opened. A stop and search file holds the ethnicity, the gender
and the age of each person stopped, and is never read whatever else changes:
it says whom the police stopped, and not who lives in a place.

So this is the one reader of the source. A step that reads recorded crime
asks `Inputs.open` for the zip, and reads it here and nowhere else.

- A file is found by its name in the list the zip keeps of itself. Nothing is
  opened to find one.
- A file is opened only where its whole name is that of a crime file: the
  month as a folder, the month again, one of the forces the list names, and
  `-street.csv`. Any other name is refused, whoever asks and however it is
  written, before the zip is asked for it.
- Nothing is unpacked to a disk. A file is read where it is, a line at a time,
  so a name is never the path of anything.
- A row holds the columns that were asked for and no other, and a column may
  be asked for only if it is on the list here. The id of a crime is not on it:
  it is what joins a crime to its outcome. Nor is what became of the crime,
  which the file repeats from the outcomes. Nor is the name of a street or of
  an LSOA: a figure needs neither.

What it cannot see: whether a month of a force is whole. A file that is
there may hold fewer crimes than were recorded, and nothing in its name says.

A refusal is a few fixed words and the id of the zip. It repeats no name from
the zip and nothing from a row.
"""

import csv
import io
import re
import zipfile
from collections.abc import Generator, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass

from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Opened

SOURCE = "police-uk-street-level-crime"
# The edition of the zip that was saved on 2026-09-24, as its receipt gives it.
EDITION = "August 2023 to July 2026"

# How the name of a crime file ends. No file that ends otherwise is ever opened.
ENDS = "-street.csv"
# The forces the list names. A crime file of another force is not what the step expects.
FORCES = ("city-of-london", "metropolitan")
# The whole name of a crime file: the month as a folder, the month again, the force.
CRIME_FILE = re.compile(
    rf"(?P<month>\d{{4}}-(?:0[1-9]|1[0-2]))/(?P=month)-(?P<force>{'|'.join(FORCES)}){re.escape(ENDS)}"
)

# The columns a crime file holds, as its first line names them.
HELD = (
    "Crime ID",
    "Month",
    "Reported by",
    "Falls within",
    "Longitude",
    "Latitude",
    "Location",
    "LSOA code",
    "LSOA name",
    "Crime type",
    "Last outcome category",
    "Context",
)
# The columns a step may ask for. Add one only with the reason a figure needs it.
MAY_BE_READ = frozenset(
    {
        "Month",
        "Reported by",
        "Falls within",
        "Longitude",
        "Latitude",
        "LSOA code",
        "Crime type",
    }
)


# A crime file as a table: each row by the names of its columns.
Table = csv.DictReader[str]


@dataclass(frozen=True, order=True)
class CrimeFile:
    """One crime file of the zip: a month of one force."""

    month: str
    force: str
    # The name the zip gives it.
    name: str


def _not_as_described(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def _named(name: str) -> CrimeFile | None:
    """A crime file by its whole name, or nothing for any other name."""
    found = CRIME_FILE.fullmatch(name)
    if found is None:
        return None
    return CrimeFile(month=found["month"], force=found["force"], name=name)


def crime_files(opened: Opened) -> tuple[CrimeFile, ...]:
    """Every crime file of the zip, by month and then by force. No file is opened.

    The names are read from the list the zip keeps of itself. A name that
    ends as a crime file does, and is not the whole name of one, stops the
    step: a crime file must not be passed over without a word, and a file that
    only looks like one must not be opened.
    """
    try:
        with zipfile.ZipFile(opened.path) as archive:
            names = archive.namelist()
    except (zipfile.BadZipFile, OSError):
        raise _not_as_described(opened, "it is not a zip") from None
    found: list[CrimeFile] = []
    for name in names:
        file = _named(name)
        if file is not None:
            found.append(file)
        elif name.endswith(ENDS):
            raise _not_as_described(opened, "a file ends as a crime file and is not named as one")
    if len({(file.month, file.force) for file in found}) != len(found):
        raise _not_as_described(opened, "a month of a force is there twice")
    if not found:
        raise _not_as_described(opened, "it holds no crime file")
    return tuple(sorted(found))


@contextmanager
def _table(opened: Opened, name: str) -> Generator[Table]:
    """One crime file as a table. It is the one place a file of the zip is opened.

    `name` is held to the whole name of a crime file before the zip is asked
    for anything, so no other file of the zip can be opened through here.
    """
    if _named(name) is None:
        raise _not_as_described(
            opened, "it was asked for a file that is no crime file, and no other is opened"
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
            raise _not_as_described(opened, "a crime file could not be opened") from None
        with raw:
            try:
                yield csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
            except (zipfile.BadZipFile, OSError, EOFError, UnicodeDecodeError, csv.Error):
                raise _not_as_described(
                    opened, "a crime file could not be read as a table"
                ) from None


def columns_of(opened: Opened, name: str) -> tuple[str, ...]:
    """The names of the columns of one crime file, as its first line gives them.

    Names only: no row is read. It is for holding a file to `HELD` before a
    figure is made from it.
    """
    with _table(opened, name) as table:
        return tuple(table.fieldnames or ())


def rows(opened: Opened, name: str, columns: Sequence[str]) -> Iterator[dict[str, str]]:
    """The rows of one crime file, for the columns that are asked for.

    `name` is the name the zip gives the file. A column is asked for by its
    name, and only if it is one that may be read. Each row holds the columns
    asked for and no other.
    """
    if _named(name) is None:
        raise _not_as_described(
            opened, "it was asked for a file that is no crime file, and no other is opened"
        )
    if not columns or not set(columns) <= MAY_BE_READ:
        raise _not_as_described(opened, "it was asked for a column that is not read")
    with _table(opened, name) as table:
        if not set(columns) <= set(table.fieldnames or ()):
            raise _not_as_described(opened, "a column is missing")
        for row in table:
            if any(row[column] is None for column in columns):
                raise _not_as_described(opened, "a row is short")
            yield {column: row[column] for column in columns}
