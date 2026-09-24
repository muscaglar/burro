"""The reader of the register of schools hands over the columns asked for, and no other.

Nothing here is real. `schools_support.py` makes the register, laid out as the
publisher's: the 135 columns of the file of 2026-09-24, in a zip of one CSV,
written as Windows-1252. Every value is made up, and a canary stands in every
column that is never read.

The register holds the names of head teachers, counts of pupils and the
religious character of a school. The licence registry forbids each, and these
hold the reader to it.
"""

import re
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline.derive.schools_file import (
    FORBIDDEN,
    MAY_BE_READ,
    NEVER_READ,
    SOURCE,
    columns_of,
    member_of,
    rows,
)
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Opened
from burro_pipeline.registry.model import Use

from ..cells.support import REPOSITORY, registry
from .schools_support import (
    CANARY,
    HELD,
    MEMBER,
    NAMELESS,
    REGISTER,
    inputs_of,
    register_csv,
    row_of,
    zipped,
)

READ = tuple(sorted(MAY_BE_READ))
PIPELINE = REPOSITORY / "packages" / "pipeline" / "src" / "burro_pipeline"


def opened_of(folder: Path, packed: bytes | None = None, *, day: str = "2026-09-24") -> Opened:
    return inputs_of(folder, packed, day=day).open(SOURCE, Use.SCORING)


@pytest.fixture
def saved(tmp_path: Path) -> Opened:
    return opened_of(tmp_path)


@pytest.fixture
def members_opened(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[str]]:
    """The name of every file of a zip that is opened to be read while a test runs."""
    found: list[str] = []
    open_a_member = zipfile.ZipFile.open

    def counted(archive: zipfile.ZipFile, name: Any, *args: Any, **kwargs: Any) -> Any:
        # A made-up zip is written through the same door, and that is no reading.
        if kwargs.get("mode", args[0] if args else "r") == "r":
            found.append(name if isinstance(name, str) else name.filename)
        return open_a_member(archive, name, *args, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "open", counted)
    yield found


def refused(opened: Opened, columns: tuple[str, ...] = READ) -> LockError:
    with pytest.raises(LockError) as stopped:
        list(rows(opened, columns))
    assert stopped.value.rule == "input_is_as_described"
    assert stopped.value.subject == opened.file_id
    # A refusal repeats nothing of the file: no value, and no name of a column.
    assert CANARY not in str(stopped.value) and NAMELESS not in str(stopped.value)
    return stopped.value


# The two lists


def test_seven_columns_may_be_read_and_each_is_of_the_school_itself():
    assert sorted(MAY_BE_READ) == [
        "Easting",
        "EstablishmentStatus (name)",
        "GOR (name)",
        "Northing",
        "PhaseOfEducation (name)",
        "TypeOfEstablishment (name)",
        "URN",
    ]


def test_no_column_the_registry_forbids_may_be_read():
    assert not MAY_BE_READ & FORBIDDEN
    assert len(FORBIDDEN) == sum(len(names) for names in NEVER_READ.values()) == 20


def test_the_names_of_head_teachers_the_counts_of_pupils_and_religion_are_all_forbidden():
    """What the registry entry names, by the names the file gives each."""
    for name in (
        "HeadFirstName",
        "HeadLastName",
        "NumberOfPupils",
        "NumberOfBoys",
        "NumberOfGirls",
        "PercentageFSM",
        "ReligiousCharacter (name)",
        "TelephoneNum",
        "PropsName",
    ):
        assert name in FORBIDDEN


def test_neither_the_name_of_a_school_nor_its_postcode_may_be_read():
    assert not {"EstablishmentName", "Postcode", "Street", "SchoolWebsite"} & MAY_BE_READ


def test_every_column_on_either_list_is_a_column_of_the_register():
    assert set(HELD) >= MAY_BE_READ | FORBIDDEN
    assert len(HELD) == len(set(HELD)) == 135


def test_no_other_module_of_the_pipeline_names_a_column_that_is_forbidden():
    """A column is read by its name, so a module that names none of them reads none."""
    naming = {
        path.relative_to(PIPELINE).as_posix()
        for path in PIPELINE.rglob("*.py")
        if any(f'"{name}"' in path.read_text(encoding="utf-8") for name in FORBIDDEN)
    }
    assert naming == {"derive/schools_file.py"}


def test_no_other_module_of_the_pipeline_opens_the_register():
    """The register is opened by the source's id, and one module holds it."""
    naming = {
        path.relative_to(PIPELINE).as_posix()
        for path in PIPELINE.rglob("*.py")
        if f'"{SOURCE}"' in path.read_text(encoding="utf-8")
    }
    assert naming == {"derive/schools_file.py"}


# What is handed over


def test_the_one_file_of_the_zip_is_opened_to_be_read_and_no_other(
    saved: Opened, members_opened: list[str]
):
    list(rows(saved, READ))
    assert members_opened == [MEMBER]


def test_a_row_holds_the_columns_asked_for_and_no_other(saved: Opened):
    found = list(rows(saved, ("URN", "Easting", "Northing")))
    assert len(found) == len(REGISTER)
    assert all(tuple(row) == ("URN", "Easting", "Northing") for row in found)
    assert found[0] == {"URN": "900001", "Easting": "700000", "Northing": "400000"}


def test_nothing_of_a_column_that_is_not_asked_for_is_handed_over(saved: Opened):
    """A canary stands in every column but those the measure reads, and none comes out."""
    found = list(rows(saved, READ))
    # Counted, and not looked for: a row that is handed over whole is long to print.
    assert (repr(found).count(CANARY), repr(found).count(NAMELESS)) == (0, 0)
    # The canary is in the file, in every row of it.
    with zipfile.ZipFile(saved.path) as archive:
        assert archive.read(MEMBER).count(CANARY.encode()) == len(REGISTER) * (len(HELD) - 8)


@pytest.mark.parametrize("name", sorted(FORBIDDEN))
def test_a_forbidden_column_is_refused_before_the_file_is_opened(
    saved: Opened, members_opened: list[str], name: str
):
    assert "not read" in str(refused(saved, ("URN", name)))
    assert members_opened == []


@pytest.mark.parametrize("name", ["EstablishmentName", "Postcode", "Gender (name)", "no column"])
def test_a_column_that_is_not_on_the_list_is_refused_before_the_file_is_opened(
    saved: Opened, members_opened: list[str], name: str
):
    assert "not read" in str(refused(saved, (name,)))
    assert members_opened == []


def test_asking_for_no_column_is_refused(saved: Opened):
    refused(saved, ())


def test_the_names_of_the_columns_are_read_without_a_row(saved: Opened):
    assert columns_of(saved) == HELD


# How the file is written


def test_the_register_is_read_as_windows_1252_and_is_no_utf8(saved: Opened):
    with zipfile.ZipFile(saved.path) as archive:
        held = archive.read(MEMBER)
    with pytest.raises(UnicodeDecodeError):
        held.decode("utf-8")
    assert len(list(rows(saved, READ))) == len(REGISTER)
    # The pipeline's own reader of text takes UTF-8 alone, and stops on it.
    with pytest.raises(LockError), saved.text(MEMBER) as text:
        text.read()


def test_a_byte_that_is_no_letter_of_windows_1252_stops_the_step(tmp_path: Path):
    broken = register_csv().replace(NAMELESS.encode("cp1252"), b"Made up \x81", 1)
    assert "could not be read" in str(refused(opened_of(tmp_path, zipped(broken))))


def test_a_value_may_hold_a_comma_a_quote_and_the_end_of_a_line(tmp_path: Path):
    made = [row_of(school, number) for number, school in enumerate(REGISTER[:3], start=1)]
    made[1]["Street"] = 'a, "b"\r\nc'
    found = list(rows(opened_of(tmp_path, zipped(register_csv(rows=made))), ("URN",)))
    assert [row["URN"] for row in found] == ["900001", "900002", "900003"]


# What the zip holds


def test_the_zip_holds_one_file_named_for_the_day_of_its_receipt(saved: Opened):
    assert member_of(saved) == MEMBER == "edubasealldata20260924.csv"


@pytest.mark.parametrize(
    "member",
    [
        "madeupdownload20260924.csv",
        "edubasealldata20260924.csv.zip",
        "edubasealldata2026-09-24.csv",
        "folder/edubasealldata20260924.csv",
        "EDUBASEALLDATA20260924.CSV",
    ],
)
def test_a_file_under_any_other_name_is_never_opened(
    tmp_path: Path, members_opened: list[str], member: str
):
    """The form makes other downloads. None is the register, whatever it holds."""
    opened = opened_of(tmp_path, zipped(member=member))
    assert "not the establishment download" in str(refused(opened))
    assert members_opened == []


def test_a_zip_that_holds_a_second_file_is_refused_and_neither_is_opened(
    tmp_path: Path, members_opened: list[str]
):
    opened = opened_of(tmp_path, zipped(beside={"madeupdownload20260924.csv": register_csv()}))
    assert "the one file" in str(refused(opened))
    assert members_opened == []


def test_a_register_of_another_day_than_its_receipt_is_refused(
    tmp_path: Path, members_opened: list[str]
):
    opened = opened_of(tmp_path, zipped(member="edubasealldata20260923.csv"))
    assert "not the day of its receipt" in str(refused(opened))
    assert members_opened == []


def test_a_file_that_is_no_zip_is_refused(tmp_path: Path):
    assert "not a zip" in str(refused(opened_of(tmp_path, register_csv())))


# What a file that is not as described does


def test_a_column_that_is_read_and_is_missing_stops_the_step(tmp_path: Path):
    without = tuple(name for name in HELD if name != "Easting")
    opened = opened_of(tmp_path, zipped(register_csv(columns=without)))
    assert "a column is missing" in str(refused(opened))


def test_a_column_that_is_named_twice_stops_the_step(tmp_path: Path):
    twice = (*HELD, "Easting")
    opened = opened_of(tmp_path, zipped(register_csv(columns=twice)))
    assert "named twice" in str(refused(opened))


def test_a_row_that_is_shorter_than_the_first_line_stops_the_step(tmp_path: Path):
    made = [row_of(school, number) for number, school in enumerate(REGISTER[:3], start=1)]
    del made[1]["AccreditationExpiryDate"]
    opened = opened_of(tmp_path, zipped(register_csv(rows=made)))
    assert "not as long as the first line" in str(refused(opened))


def test_an_empty_file_holds_no_column(tmp_path: Path):
    assert "a column is missing" in str(refused(opened_of(tmp_path, zipped(b""))))


# The gate


def test_the_registry_allows_the_register_for_scoring_and_names_what_is_never_read():
    entry = registry().get(SOURCE)
    assert Use.SCORING in entry.uses
    said = " ".join(entry.conditions)
    for words in ("head teacher", "pupil", "religious character", "governors", "catchment"):
        assert re.search(words, said, re.IGNORECASE)


def test_nothing_is_unpacked_to_a_disk(saved: Opened):
    list(rows(saved, READ))
    work = saved.path.parent.parent
    assert [path.name for path in work.rglob("*") if path.is_file()] == ["extract.zip"]
