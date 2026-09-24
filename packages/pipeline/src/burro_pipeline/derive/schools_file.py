"""The register of schools, read for the columns a figure needs and for no other.

The Department for Education gives the register as one download: a zip that
holds one CSV, named for the day it was made, with a row for every
establishment in England, open or closed. The file that was saved on
2026-09-24 holds 135 columns. Some of them are about people, and the licence
registry forbids each:

- the name of a head teacher, and of a proprietor, which may be a person's;
- a telephone number;
- counts of pupils, by sex, on free school meals and with special needs;
- the religious character of a school, which the founder decided on
  2026-09-24 is never read: a school is counted without regard to faith.

So this is the one reader of the source. A step that reads the register asks
`Inputs.open` for the zip, and reads it here and nowhere else.

- The zip holds one file, and its whole name is that of the establishment
  download. The publisher's form makes other downloads, the governors among
  them, which are records about named people. A zip that holds anything else
  is refused before a file of it is opened.
- The day in the name of the file is the day its receipt gives. The period a
  figure is shown with is then the file's own.
- A column may be asked for only if it is on the list here. Each is about the
  school: what it is, whether it is open, and where it stands.
- A row holds the columns that were asked for and no other. A line of a CSV
  cannot be cut before it is parsed, so a line is parsed whole, and the
  columns asked for are taken from it by their place. Nothing else of the line
  is kept, handed over or named.
- Nothing is unpacked to a disk. The file is read where it is, a line at a
  time.

The file is not UTF-8. It reads whole as Windows-1252, and is read as that.

What it cannot see: whether a row is right. The register is what each school
and its authority last told the department.

A refusal is a few fixed words and the id of the zip. It repeats no name from
the zip and nothing from a row.
"""

import csv
import io
import re
import zipfile
from collections.abc import Generator, Iterator, Sequence
from contextlib import contextmanager

from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Opened

SOURCE = "dfe-gias"
# The whole name of the one file the zip holds: the establishment download, and its day.
MEMBER = re.compile(r"edubasealldata(?P<day>[0-9]{8})\.csv")
# How the file is written. It holds bytes that are no UTF-8.
ENCODING = "cp1252"

# The number the register gives a school. It tells one row from another.
URN = "URN"
# Whether it is open, what type of school it is, and which years it teaches.
STATUS = "EstablishmentStatus (name)"
KIND = "TypeOfEstablishment (name)"
PHASE = "PhaseOfEducation (name)"
# Where it stands: the region the register gives it to, and its point on the National Grid.
REGION = "GOR (name)"
EASTING, NORTHING = "Easting", "Northing"

# The columns a step may ask for. Add one only with the reason a figure needs it, and never
# one that is on the list below.
MAY_BE_READ = frozenset({URN, STATUS, KIND, PHASE, REGION, EASTING, NORTHING})
# The columns the licence registry forbids, by their names in the file of 2026-09-24. None
# is ever read. A column that is on neither list is not read either: this one says why not.
NEVER_READ: dict[str, tuple[str, ...]] = {
    "the name of a person": (
        "HeadTitle (name)",
        "HeadFirstName",
        "HeadLastName",
        "HeadPreferredJobTitle",
        "PropsName",
    ),
    "a telephone number": ("TelephoneNum",),
    "a count of pupils": (
        "NumberOfPupils",
        "NumberOfBoys",
        "NumberOfGirls",
        "PercentageFSM",
        "FSM",
        "SENStat",
        "SENNoStat",
        "ResourcedProvisionOnRoll",
        "SenUnitOnRoll",
    ),
    "the religious character of a school": (
        "ReligiousCharacter (code)",
        "ReligiousCharacter (name)",
        "ReligiousEthos (name)",
        "Diocese (code)",
        "Diocese (name)",
    ),
}
FORBIDDEN = frozenset(name for names in NEVER_READ.values() for name in names)
_NOTHING: list[str] = []


def _not_as_described(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def member_of(opened: Opened) -> str:
    """The name of the one file the zip holds, once it is seen to be the establishment download.

    The names are read from the list the zip keeps of itself. No file is
    opened. The day in the name is held to the day the receipt gives.
    """
    try:
        with zipfile.ZipFile(opened.path) as archive:
            names = [name for name in archive.namelist() if not name.endswith("/")]
    except (zipfile.BadZipFile, OSError):
        raise _not_as_described(opened, "it is not a zip") from None
    if len(names) != 1:
        raise _not_as_described(opened, "it does not hold the one file that is read")
    found = MEMBER.fullmatch(names[0])
    if found is None:
        raise _not_as_described(opened, "the file it holds is not the establishment download")
    first, last = opened.receipt.data_period.days()
    if first != last or found["day"] != first.replace("-", ""):
        raise _not_as_described(opened, "the day in its name is not the day of its receipt")
    return names[0]


@contextmanager
def _lines(opened: Opened) -> Generator[Iterator[list[str]]]:
    """The file as lines, each parsed into its parts. It is the one place the file is opened."""
    name = member_of(opened)
    try:
        archive = zipfile.ZipFile(opened.path)
    except (zipfile.BadZipFile, OSError):
        raise _not_as_described(opened, "it is not a zip") from None
    with archive:
        try:
            raw = archive.open(name)
        except (KeyError, zipfile.BadZipFile, OSError, NotImplementedError, RuntimeError):
            raise _not_as_described(opened, "the register could not be opened") from None
        with raw:
            try:
                yield csv.reader(io.TextIOWrapper(raw, encoding=ENCODING, newline=""))
            except (zipfile.BadZipFile, OSError, EOFError, UnicodeDecodeError, csv.Error):
                raise _not_as_described(
                    opened, "the register could not be read as a table"
                ) from None


def columns_of(opened: Opened) -> tuple[str, ...]:
    """The names of the columns of the register, as its first line gives them.

    Names only: no row is read. It is for holding a file to the two lists
    here before a figure is made from it.
    """
    with _lines(opened) as lines:
        return tuple(next(lines, _NOTHING))


def rows(opened: Opened, columns: Sequence[str]) -> Iterator[dict[str, str]]:
    """The rows of the register, for the columns that are asked for.

    A column is asked for by its name, and only if it is one that may be
    read. Each row holds the columns asked for and no other. A file that names
    a column twice is refused: a name would then not say which is meant.
    """
    if not columns or not set(columns) <= MAY_BE_READ:
        raise _not_as_described(opened, "it was asked for a column that is not read")
    with _lines(opened) as lines:
        named = next(lines, _NOTHING)
        if len(set(named)) != len(named):
            raise _not_as_described(opened, "a column is named twice")
        if not set(columns) <= set(named):
            raise _not_as_described(opened, "a column is missing")
        places = [(name, named.index(name)) for name in columns]
        for line in lines:
            if len(line) != len(named):
                raise _not_as_described(opened, "a row is not as long as the first line")
            yield {name: line[at] for name, at in places}
