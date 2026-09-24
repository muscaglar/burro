"""What the tests of the census measures share: two made-up tables, laid out as Nomis lays its own.

Every figure here is made up. The town is the made-up town of the tests of
cells: three areas, each an MSOA. Beside them is one MSOA outside London and
one in Wales, which are part of no area.

The categories are the publisher's own, in the order its pages give them: a
total and 18 bands of age, and a total and 21 kinds of household. A column is
named as the zip of accommodation type names one, which a build reads: the
name of the variable, a colon, and the name of the category. The table of age
as it was fetched names its columns so. The table of households does not: it
adds `; measures: Value`, writes "One person" with no hyphen and the total as
"Total", and puts every name, and the first three cells of every row, between
quotes. `as_the_files_write_it` and `as_the_files_are_written` make a table so,
and a test on the real files holds both to the header of each. A test writes
the header the other ways it may be written too. What the columns hold is
made up.

    Age, usual residents           all   20-24  25-29  30-34   65 and over
    Quillhaven 001   E02999001    1000     100    150     50       100        30.0 and 10.0
    Quillhaven 002   E02999002    2000     200    300    400        25        45.0 and 1.3
    Tallowgate 001   E02999003     800       8      8      8       400         3.0 and 50.0

    Households                     all   of one   with dependent children
    Quillhaven 001   E02999001     400     100    40 + 20 + 30 + 10            25.0 and 25.0
    Quillhaven 002   E02999002    1000     555    10 +  5 +  5 +  5            55.5 and 2.5
    Tallowgate 001   E02999003     300      30   100 + 40 + 30 + 10            10.0 and 60.0
"""

import csv
import io
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import census_msoa
from burro_pipeline.derive.census_msoa import AGE, HOUSEHOLDS, Of, Share, Table
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, contents, inputs_of, receipt_of, zip_of

ONE, TWO, THREE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
MSOA_ONE, MSOA_TWO, MSOA_THREE = "E02999001", "E02999002", "E02999003"
OUTSIDE, IN_WALES = "E02999901", "W02999001"
# No count of any column that is read. A figure made from a cell that is not read would show it.
NEVER = 9990

FIRST = ("date", "geography", "geography code")
BANDS = (
    "Aged 4 years and under",
    *(f"Aged {first} to {first + 4} years" for first in range(5, 85, 5)),
    "Aged 85 years and over",
)
KINDS = (
    "One-person household",
    "One-person household: Aged 66 years and over",
    "One-person household: Other",
    "Single family household",
    "Single family household: All aged 66 years and over",
    "Single family household: Married or civil partnership couple",
    "Single family household: Married or civil partnership couple: No children",
    "Single family household: Married or civil partnership couple: Dependent children",
    "Single family household: Married or civil partnership couple: All children non-dependent",
    "Single family household: Cohabiting couple family",
    "Single family household: Cohabiting couple family: No children",
    "Single family household: Cohabiting couple family: With dependent children",
    "Single family household: Cohabiting couple family: All children non-dependent",
    "Single family household: Lone parent family",
    "Single family household: Lone parent family: With dependent children",
    "Single family household: Lone parent family: All children non-dependent",
    "Single family household: Other single family household",
    "Single family household: Other single family household: Other family composition",
    "Other household types",
    "Other household types: With dependent children",
    "Other household types: Other, including all full-time students and all aged 66 years and over",
)
# The categories of each table, the total first, as its own page gives them.
CATEGORIES: Mapping[str, tuple[str, ...]] = {
    "TS007A": ("Total", *BANDS),
    "TS003": ("Total: All households", *KINDS),
}
YOUNG = ("Aged 20 to 24 years", "Aged 25 to 29 years", "Aged 30 to 34 years")
OLD = BANDS[13:]
WITH_CHILDREN = (KINDS[7], KINDS[11], KINDS[14], KINDS[19])
ONE_PERSON, ONE_FAMILY, OTHER_KINDS = KINDS[0], KINDS[3], KINDS[18]

# What a row holds, by the name of the category. A category that is not named holds NEVER.
Row = Mapping[str, int]


def _ages(total: int, young: Sequence[int], old: Sequence[int]) -> dict[str, int]:
    """The residents of one MSOA by band. The bands add up to the total."""
    held = dict.fromkeys(BANDS, 0) | dict(zip(YOUNG, young, strict=True))
    held |= dict(zip(OLD, old, strict=True))
    # Everyone else is aged 35 to 39, so that the bands come to the total.
    held["Aged 35 to 39 years"] = total - sum(held.values())
    return {"Total": total} | held


def _households(total: int, alone: int, children: Sequence[int], others: int) -> dict[str, int]:
    """The households of one MSOA by kind. The three kinds at the top add up to the total."""
    held = dict.fromkeys(KINDS, NEVER) | dict(zip(WITH_CHILDREN, children, strict=True))
    held |= {ONE_PERSON: alone, OTHER_KINDS: others, ONE_FAMILY: total - alone - others}
    return {"Total: All households": total} | held


AGES: Mapping[str, Row] = {
    MSOA_ONE: _ages(1000, (100, 150, 50), (40, 30, 20, 7, 3)),
    MSOA_TWO: _ages(2000, (200, 300, 400), (5, 5, 5, 5, 5)),
    MSOA_THREE: _ages(800, (8, 8, 8), (100, 100, 100, 50, 50)),
    OUTSIDE: _ages(5000, (1000, 1000, 1000), (100, 100, 100, 100, 100)),
    IN_WALES: _ages(700, (10, 10, 10), (100, 100, 100, 100, 100)),
}
HOMES: Mapping[str, Row] = {
    MSOA_ONE: _households(400, 100, (40, 20, 30, 10), 50),
    MSOA_TWO: _households(1000, 555, (10, 5, 5, 5), 45),
    MSOA_THREE: _households(300, 30, (100, 40, 30, 10), 20),
    OUTSIDE: _households(2000, 500, (300, 100, 100, 50), 100),
    IN_WALES: _households(300, 100, (30, 10, 10, 5), 20),
}
MADE_UP: Mapping[str, Mapping[str, Row]] = {"TS007A": AGES, "TS003": HOMES}


def as_the_zip_of_homes(table: Table, category: str) -> str:
    """The name of a column as the zip of accommodation type writes one."""
    return f"{table.variable}: {category}"


def with_measures(table: Table, category: str) -> str:
    """The name of a column as some tables of the census are said to write one."""
    return f"{table.variable}: {category}; measures: Value"


def with_no_hyphen(table: Table, category: str) -> str:
    return f"{table.variable}: {category.replace('-', ' ')}"


def in_capitals(table: Table, category: str) -> str:
    return f"{table.variable}: {category}".upper()


def bare(table: Table, category: str) -> str:
    return category


def as_the_files_write_it(table: Table, category: str) -> str:
    """The name of a column as the table that was fetched writes it.

    The table of age writes the variable, a colon and the category. The table
    of households adds `; measures: Value`, writes the total as "Total", and
    writes "One person" with no hyphen.
    """
    if table is not HOUSEHOLDS:
        return as_the_zip_of_homes(table, category)
    written = "Total" if category == CATEGORIES[table.code][0] else category
    return with_measures(table, written.replace("One-person", "One person"))


def as_the_files_are_written(table: Table, plain: bytes) -> bytes:
    """A table as the file that was fetched is written, from one written plainly.

    The table of households puts every name of its header between quotes, and
    the date, the name and the code of every row. Its counts stand bare. The
    table of age puts a cell between quotes only where it holds a comma, as a
    plain table does.
    """
    if table is not HOUSEHOLDS:
        return plain
    header, *rows = list(csv.reader(io.StringIO(plain.decode(), newline="")))
    lines = [",".join(f'"{name}"' for name in header)]
    for row in rows:
        quoted = (f'"{cell}"' for cell in row[: len(FIRST)])
        lines.append(",".join((*quoted, *row[len(FIRST) :])))
    return "".join(f"{line}\n" for line in lines).encode()


def table_csv(
    table: Table,
    rows: Mapping[str, Row] | None = None,
    *,
    named: Callable[[Table, str], str] = as_the_zip_of_homes,
    first: Sequence[str] = FIRST,
    year: str = "2021",
    twice: Sequence[str] = (),
    left_out: Sequence[str] = (),
    also: Sequence[str] = (),
    cells: Mapping[tuple[str, str], str] | None = None,
) -> bytes:
    """A table by MSOA as Nomis writes one: no mark at the start, and lines that end LF.

    `left_out` names categories whose column is not written, `also` columns
    that are written beside the table's own, and `cells` what one cell of one
    row holds, where that is no count.
    """
    rows = MADE_UP[table.code] if rows is None else rows
    categories = [one for one in CATEGORIES[table.code] if one not in left_out]
    header = [*first, *(named(table, one) for one in categories), *also]
    text = io.StringIO(newline="")
    written = csv.writer(text, lineterminator="\n")
    written.writerow(header)
    for code in (*rows, *twice):
        held = [
            (cells or {}).get((code, one), str(rows[code].get(one, NEVER))) for one in categories
        ]
        by_name = {"date": year, "geography": CANARY, "geography code": code}
        written.writerow([*(by_name[name] for name in first), *held, *(str(NEVER) for _ in also)])
    return text.getvalue().encode()


def zipped(table: Table, by_msoa: bytes, member: str | None = None) -> bytes:
    """The zip of a table: a file for each geography, and the notes. One file is ever read."""
    code = table.code.lower()
    header = by_msoa.split(b"\n", 1)[0] + b"\n"
    return zip_of(
        {
            f"census2021-{code}-ctry.csv": header,
            f"census2021-{code}-lsoa.csv": header,
            member or f"census2021-{code}-msoa.csv": by_msoa,
            f"census2021-{code}-oa.csv": header,
            f"metadata/{code}-2021-1.txt": CANARY,
        }
    )


def inputs_with(
    folder: Path,
    files: Mapping[str, bytes] | None = None,
    *,
    use: Use = Use.SCORING,
    as_at: str = census_msoa.CENSUS_DAY,
    **changes: Registry,
) -> Inputs:
    """The made-up build of the tests of cells, and the two census tables beside it.

    `files` holds the zip of each table that is given, by the code of the
    table. With none, both are given as they are made up.
    """
    given = inputs_of(folder, contents(), **changes)
    if files is None:
        files = {table.code: zipped(table, table_csv(table)) for table in (AGE, HOUSEHOLDS)}
    receipts = list(given.receipts)
    for code, content in files.items():
        table = census_msoa.TABLES[code]
        path = folder / "given" / table.file
        path.write_bytes(content)
        given.store.put(census_msoa.SOURCE, table.file, path)
        receipt = receipt_of(census_msoa.SOURCE, use, table.file, content, f"Census 2021 {code}")
        receipts.append(receipt.model_copy(update={"data_period": Period(as_at=as_at)}))
    return Inputs(given.registry, receipts, given.store, given.work)


def spine_of(inputs: Inputs) -> Spine:
    return spine.build(inputs)


def built(folder: Path, of: Of, by_msoa: bytes | None = None) -> Share:
    """One measure, from the made-up tables or from a table that is given."""
    files = None if by_msoa is None else {of.table.code: zipped(of.table, by_msoa)}
    inputs = inputs_with(folder, files)
    return census_msoa.build(of, inputs, spine_of(inputs))


def refused(folder: Path, of: Of, by_msoa: bytes, as_at: str = census_msoa.CENSUS_DAY) -> LockError:
    """The refusal of a table, which names a rule and repeats nothing the table holds."""
    inputs = inputs_with(folder, {of.table.code: zipped(of.table, by_msoa)}, as_at=as_at)
    found = spine_of(inputs)
    with pytest.raises(LockError) as stopped:
        census_msoa.build(of, inputs, found)
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)
    assert str(NEVER) not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return stopped.value
