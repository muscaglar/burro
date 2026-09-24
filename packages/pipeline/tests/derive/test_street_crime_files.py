"""The reader of the police's zip opens a crime file, and no other file of the zip.

Nothing here is real. The zip is made up, in the layout of the one the form at
data.police.uk makes: a folder for each month, and in it a file for each force
and each kind of data. The names of the columns of a crime file are the
publisher's. Every value is made up, and a canary stands in every column and
every file that is never read.

The zip that was saved on 2026-09-24 holds outcomes and stop and search
beside the crime files. The registry entry forbids reading both, and these
hold the reader to it: every file it opens is counted, and none is but a file
whose name ends `-street.csv`.
"""

import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import burro_pipeline
import pytest
from burro_pipeline.derive import street_crime_files
from burro_pipeline.derive.street_crime_files import (
    ENDS,
    FORCES,
    HELD,
    MAY_BE_READ,
    SOURCE,
    CrimeFile,
    columns_of,
    crime_files,
    rows,
)
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Opened
from burro_pipeline.registry.model import Use

from ..cells.support import receipt_of, registry, zip_of

# A string found nowhere else. It stands where the reader never reads.
CANARY = "Zzyzx Parva"
MONTHS = ("2026-01", "2026-02")
KINDS = ("street", "outcomes", "stop-and-search")
# What a stop and search file holds that must never be read. The names are made up to be
# like the publisher's: no file of the publisher was opened to write them.
ABOUT_A_PERSON = ("Gender", "Age range", "Self-defined ethnicity", "Officer-defined ethnicity")


def crime_csv(month: str, crimes: int = 2) -> str:
    """A made-up crime file: the publisher's columns, and rows that are made up."""
    lines = [",".join(HELD)]
    for n in range(crimes):
        row = {
            "Crime ID": CANARY,
            "Month": month,
            "Reported by": "A made-up force",
            "Falls within": "A made-up force",
            "Longitude": f"1.{n:04d}",
            "Latitude": f"55.{n:04d}",
            "Location": CANARY,
            "LSOA code": f"E0199900{n + 1}",
            "LSOA name": CANARY,
            "Crime type": "Criminal damage and arson",
            "Last outcome category": CANARY,
            "Context": CANARY,
        }
        lines.append(",".join(row[name] for name in HELD))
    return "\n".join(lines) + "\n"


def other_csv(columns: tuple[str, ...]) -> str:
    """A made-up file of a kind that is never read. Every cell of it is the canary."""
    return ",".join(columns) + "\n" + ",".join(CANARY for _ in columns) + "\n"


def members(kinds: tuple[str, ...] = KINDS) -> dict[str, str | bytes]:
    """The members of a made-up zip: each month, each force, each kind."""
    found: dict[str, str | bytes] = {}
    for month in MONTHS:
        for force in FORCES:
            for kind in kinds:
                name = f"{month}/{month}-{force}-{kind}.csv"
                if kind == "street":
                    found[name] = crime_csv(month)
                elif kind == "outcomes":
                    found[name] = other_csv(("Crime ID", "Month", "Outcome type"))
                else:
                    found[name] = other_csv(("Type", "Date", *ABOUT_A_PERSON))
    return found


def handed(folder: Path, held: dict[str, str | bytes] | bytes) -> Opened:
    """A made-up zip as a step is handed one: a copy of it, and its receipt."""
    content = held if isinstance(held, bytes) else zip_of(held)
    path = folder / "handed" / "made-up.zip"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    made = receipt_of(SOURCE, Use.SCORING, "made-up.zip", content, street_crime_files.EDITION)
    return Opened(made, path)


@pytest.fixture
def opened_members(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """The name of every member of any zip that is opened while a test runs."""
    seen: list[str] = []
    really_open = zipfile.ZipFile.open

    def watched(self: zipfile.ZipFile, name: Any, *args: Any, **kwargs: Any) -> Any:
        # A member that is written is opened too. Only what is read is counted.
        if (args[0] if args else kwargs.get("mode", "r")) == "r":
            seen.append(name.filename if isinstance(name, zipfile.ZipInfo) else str(name))
        return really_open(self, name, *args, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "open", watched)
    # Every other way into a member goes through `open`, but for these. None is used.
    for way in ("read", "extract", "extractall"):
        monkeypatch.setattr(zipfile.ZipFile, way, _never)
    return seen


def _never(*args: Any, **kwargs: Any) -> None:
    raise AssertionError("the reader took another way into the zip")


def read_whole(opened: Opened) -> Iterator[dict[str, str]]:
    """Every row of every crime file, for every column that may be read."""
    for file in crime_files(opened):
        yield from rows(opened, file.name, sorted(MAY_BE_READ))


def test_the_registry_allows_the_source_for_the_use_a_measure_asks():
    assert registry().require(SOURCE, Use.SCORING).id == SOURCE


def test_the_crime_files_are_found_by_name_and_nothing_is_opened(
    tmp_path: Path, opened_members: list[str]
):
    found = crime_files(handed(tmp_path, members()))
    assert found == tuple(
        CrimeFile(month, force, f"{month}/{month}-{force}{ENDS}")
        for month in MONTHS
        for force in sorted(FORCES)
    )
    assert opened_members == []


def test_a_reader_of_the_whole_zip_opens_the_crime_files_and_no_other(
    tmp_path: Path, opened_members: list[str]
):
    opened = handed(tmp_path, members())
    read = list(read_whole(opened))
    assert len(read) == len(MONTHS) * len(FORCES) * 2
    assert opened_members
    assert all(name.endswith(ENDS) for name in opened_members)
    with zipfile.ZipFile(opened.path) as archive:
        others = [name for name in archive.namelist() if not name.endswith(ENDS)]
    assert len(others) == len(MONTHS) * len(FORCES) * 2
    assert not set(others) & set(opened_members)


def test_nothing_of_a_file_or_a_column_that_is_not_read_is_handed_over(tmp_path: Path):
    for row in read_whole(handed(tmp_path, members())):
        assert set(row) == MAY_BE_READ
        assert CANARY not in row.values()


@pytest.mark.parametrize(
    "name",
    [
        "2026-01/2026-01-metropolitan-outcomes.csv",
        "2026-01/2026-01-metropolitan-stop-and-search.csv",
        "2026-01/2026-01-city-of-london-stop-and-search.csv",
        # Named to look like a crime file, and none.
        "2026-01/2026-01-metropolitan-stop-and-search-street.csv",
        "2026-01/2026-01-metropolitan-outcomes-street.csv",
        "2026-01/2026-01-metropolitan-street.csv/../2026-01-metropolitan-outcomes.csv",
        "2026-01-street.csv/2026-01-metropolitan-stop-and-search.csv",
        "2026-01/2026-02-metropolitan-street.csv",
        "2026-13/2026-13-metropolitan-street.csv",
        "../2026-01/2026-01-metropolitan-street.csv",
        "/2026-01/2026-01-metropolitan-street.csv",
        "2026-01/2026-01-metropolitan-street.csv ",
        "2026-01/2026-01-metropolitan-street.CSV",
        "2026-01/2026-01-metropolitan-street.csv\n",
        "2026-01/2026-01-a-made-up-force-street.csv",
        "",
    ],
)
def test_any_other_file_is_refused_before_the_zip_is_asked_for_it(
    tmp_path: Path, opened_members: list[str], name: str
):
    # The zip holds a file of that very name, so that only the reader stands in the way.
    opened = handed(tmp_path, members() | ({name: other_csv(HELD)} if name else {}))
    with pytest.raises(LockError) as refused:
        list(rows(opened, name, ["Month"]))
    assert refused.value.rule == "input_is_as_described"
    assert opened_members == []
    assert CANARY not in str(refused.value)
    assert not name or name not in str(refused.value)


@pytest.mark.parametrize(
    "column",
    ["Crime ID", "Last outcome category", "Location", "LSOA name", "Context", *ABOUT_A_PERSON],
)
def test_a_column_that_is_not_on_the_list_is_refused(
    tmp_path: Path, opened_members: list[str], column: str
):
    opened = handed(tmp_path, members())
    (first, *_) = crime_files(opened)
    with pytest.raises(LockError) as refused:
        list(rows(opened, first.name, ["Month", column]))
    assert refused.value.rule == "input_is_as_described"
    assert opened_members == []


def test_the_columns_that_may_be_read_are_columns_of_a_crime_file_and_none_joins_an_outcome():
    assert set(HELD) > MAY_BE_READ
    assert not MAY_BE_READ & {"Crime ID", "Last outcome category"}


def test_a_reader_that_names_no_column_is_refused(tmp_path: Path):
    opened = handed(tmp_path, members())
    (first, *_) = crime_files(opened)
    with pytest.raises(LockError):
        list(rows(opened, first.name, []))


def test_a_file_that_ends_as_a_crime_file_and_is_not_named_as_one_stops_the_step(tmp_path: Path):
    odd = members() | {"2026-01/2026-01-metropolitan-outcomes-street.csv": other_csv(HELD)}
    with pytest.raises(LockError) as refused:
        crime_files(handed(tmp_path, odd))
    assert refused.value.rule == "input_is_as_described"


def test_a_zip_with_no_crime_file_stops_the_step(tmp_path: Path, opened_members: list[str]):
    with pytest.raises(LockError):
        crime_files(handed(tmp_path, members(kinds=("outcomes", "stop-and-search"))))
    assert opened_members == []


def test_a_crime_file_that_lacks_a_column_stops_the_step(tmp_path: Path):
    short = members() | {f"2026-01/2026-01-metropolitan{ENDS}": "Month,Crime type\n2026-01,x\n"}
    opened = handed(tmp_path, short)
    with pytest.raises(LockError) as refused:
        list(rows(opened, f"2026-01/2026-01-metropolitan{ENDS}", ["Month", "LSOA code"]))
    assert "a column is missing" in str(refused.value)


def test_a_file_that_is_no_zip_stops_the_step(tmp_path: Path):
    opened = handed(tmp_path, b"Month,Crime type\n")
    with pytest.raises(LockError):
        crime_files(opened)
    with pytest.raises(LockError):
        list(rows(opened, f"2026-01/2026-01-metropolitan{ENDS}", ["Month"]))


def test_the_columns_of_a_crime_file_are_given_by_name_and_no_row_with_them(
    tmp_path: Path, opened_members: list[str]
):
    opened = handed(tmp_path, members())
    for file in crime_files(opened):
        assert columns_of(opened, file.name) == HELD
    assert all(name.endswith(ENDS) for name in opened_members)
    with pytest.raises(LockError):
        columns_of(opened, "2026-01/2026-01-metropolitan-stop-and-search.csv")


def test_a_crime_file_that_is_not_text_stops_the_step(tmp_path: Path):
    broken = members() | {f"2026-01/2026-01-metropolitan{ENDS}": b"Month\n\xff\xfe\x00\n" * 4000}
    opened = handed(tmp_path, broken)
    with pytest.raises(LockError) as refused:
        list(rows(opened, f"2026-01/2026-01-metropolitan{ENDS}", ["Month"]))
    assert refused.value.rule == "input_is_as_described"


def test_the_module_opens_a_member_in_one_place_only():
    """The rule is held where a member is opened. So the module opens one in one place."""
    source = Path(street_crime_files.__file__).read_text(encoding="utf-8")
    code = source.split('"""', 2)[2]
    assert code.count(".open(") == 1
    assert not any(way in code for way in (".read(", ".extract(", ".extractall(", "ZipExtFile"))


def test_no_other_module_names_the_polices_source_or_opens_a_file_of_its_zip():
    """The founder decided that the crime files alone are read, and the rest is never opened.

    So one module names the source, and a measure is handed its rows by that
    module. A measure may ask the gate for the zip, which opens nothing of it.
    It opens no member by itself.
    """
    top = Path(burro_pipeline.__file__).parent
    own = Path(street_crime_files.__file__)
    names_it = sorted(
        path.relative_to(top).as_posix()
        for path in top.rglob("*.py")
        if path != own and SOURCE in path.read_text(encoding="utf-8")
    )
    assert names_it == []
    through_the_reader = sorted(
        path.relative_to(top).as_posix()
        for path in top.rglob("*.py")
        if path != own and "street_crime_files" in path.read_text(encoding="utf-8")
    )
    assert through_the_reader == ["derive/incident_criminal_damage.py"]
    for name in ("derive/incident_criminal_damage.py", "derive/incident_antisocial.py"):
        code = (top / name).read_text(encoding="utf-8").split('"""', 2)[2]
        opens = (".text(", ".member(", ".rows(text", "zipfile", "ZipFile", ".extract")
        assert not [way for way in opens if way in code], name
