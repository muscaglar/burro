"""Homes built since 2000, from a made-up table laid out as the publisher lays out its own.

Every figure here is made up. The town is the made-up town of the tests of
cells: three areas, each an MSOA of two LSOAs. The table is the one the tests
of homes built before 1919 make, with the publisher's own 35 columns. Here a
row says what it holds for the period 2000 to 2008 and for any year, and holds
nought for every other period.

A figure is read from the row of the MSOA, which is the area's own. The rows
of its LSOAs are what that row is held to.

    area             row         2000 to 2008   2009   2010   no period  all homes
    Quillhaven 001   E02999001       100          20     30       0         500
                       E01999001      60          10     20       0         300
                       E01999002      40          10     10       0         200
                                     150 of 500 homes is 30 in 100
    Quillhaven 002   E02999002        10           -      0       -         500
                       E01999003      10           -      0       0         400
                       E01999004       -           0      0       -         100
                                     10 of 500 homes is 2 in 100, and marked
    Tallowgate 001   E02999003       200           0    100     100        1000
                       E01999005     200           0    100     100         500
                       E01999006       0           0      0       0         500
                                     300 of the 900 homes with a period is 33.3 in 100,
                                     and 900 of 1,000 homes are covered
"""

import csv
import io
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId
from burro_pipeline.cells import spine
from burro_pipeline.derive import homes_post2000, homes_pre1919
from burro_pipeline.derive.homes_post2000 import Post2000
from burro_pipeline.derive.measures import MEASURES, says_what_core_says
from burro_pipeline.derive.methods import AREA_ROW_RATIO, Worked
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, contents, held, inputs_of, receipt_of, registry
from .test_homes_pre1919 import BANDS, COLUMNS, LARGER, NAME, TABLE, zipped

ONE, TWO, THREE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
PERIOD, UNKNOWN, HOMES = "bp_2000_2008", "bp_unkw", "all_properties"
# The columns that are added up in the table of 31 March 2025: the period, and 17 years.
ADDED = (PERIOD, *(f"bp_{year}" for year in range(2009, 2026)))
# What a row holds where it does not hold nought.
Cells = Mapping[str, str]
LSOAS: Mapping[str, Cells] = {
    "E01999001": {PERIOD: "60", "bp_2009": "10", "bp_2010": "20", HOMES: "300"},
    "E01999002": {PERIOD: "40", "bp_2009": "10", "bp_2010": "10", HOMES: "200"},
    "E01999003": {PERIOD: "10", "bp_2009": "-", HOMES: "400"},
    "E01999004": {PERIOD: "-", UNKNOWN: "-", HOMES: "100"},
    "E01999005": {PERIOD: "200", "bp_2010": "100", UNKNOWN: "100", HOMES: "500"},
    "E01999006": {HOMES: "500"},
    # Outside London, and in Wales. Neither is part of any area.
    "E01999901": {PERIOD: "700", HOMES: "700"},
    "W01999001": {PERIOD: "90", HOMES: "90"},
}
# The publisher's own row for each MSOA, each count rounded once. A figure is read from it.
MSOAS: Mapping[str, Cells] = {
    "E02999001": {PERIOD: "100", "bp_2009": "20", "bp_2010": "30", HOMES: "500"},
    "E02999002": {PERIOD: "10", "bp_2009": "-", UNKNOWN: "-", HOMES: "500"},
    "E02999003": {PERIOD: "200", "bp_2010": "100", UNKNOWN: "100", HOMES: "1000"},
    "E02999901": {PERIOD: "700", HOMES: "700"},
}
ROUNDED = (Flag.ROUNDED_IN_SOURCE,)
MARKED = (Flag.ROUNDED_IN_SOURCE, Flag.SUPPRESSED_IN_SOURCE)


def table_of(
    lsoas: Mapping[str, Cells] = LSOAS,
    msoas: Mapping[str, Cells] = MSOAS,
    columns: Sequence[str] = COLUMNS,
) -> bytes:
    """The table of homes by build period, as the publisher writes it: a mark, and LF.

    A row holds nought wherever it is not said to hold something. The row of a
    larger area holds 9990 and the row of one band 990, so a figure made from
    either would show.
    """
    text = io.StringIO(newline="")
    table = csv.DictWriter(text, columns, extrasaction="ignore", lineterminator="\n")
    table.writeheader()
    rows: list[tuple[str, str, Cells | None]] = [(kind, code, None) for kind, code in LARGER]
    rows += [("MSOA", code, cells) for code, cells in msoas.items()]
    rows += [("LSOA", code, cells) for code, cells in lsoas.items()]
    for kind, code, cells in rows:
        bands = ("All", *BANDS, "I") if code.startswith("W") else ("All", *BANDS)
        for band in bands:
            if band != "All":
                counts = dict.fromkeys(columns, "990")
            elif cells is None:
                counts = dict.fromkeys(columns, "9990")
            else:
                counts = dict.fromkeys(columns, "0") | dict(cells)
            table.writerow(
                counts
                | {"geography": kind, "ecode": code, "area_name": CANARY, "band": band}
                | {"ba_code": "9901" if kind == "LAUA" else "N/A"}
            )
    return b"\xef\xbb\xbf" + text.getvalue().encode()


def inputs_with(
    folder: Path,
    table: bytes | None = None,
    as_at: str = "2025-03-31",
    member: str = TABLE,
    **changes: Registry,
) -> Inputs:
    """The made-up build of the tests of cells, and the table of homes beside it."""
    given = inputs_of(folder, contents(), **changes)
    content = zipped(table_of() if table is None else table, member)
    path = folder / "given" / NAME
    path.write_bytes(content)
    given.store.put(homes_post2000.SOURCE, NAME, path)
    receipt = receipt_of(homes_post2000.SOURCE, Use.SCORING, NAME, content, as_at[:4]).model_copy(
        update={"data_period": Period(as_at=as_at)}
    )
    return Inputs(given.registry, [*given.receipts, receipt], given.store, given.work)


def built(
    folder: Path, lsoas: Mapping[str, Cells] = LSOAS, msoas: Mapping[str, Cells] = MSOAS
) -> Post2000:
    inputs = inputs_with(folder, table_of(lsoas, msoas))
    return homes_post2000.build(inputs, spine.build(inputs))


def with_one(own: Cells, *parts: Cells) -> tuple[Mapping[str, Cells], Mapping[str, Cells]]:
    """The made-up table with another row for Quillhaven 001, and other rows for its LSOAs."""
    first, second = parts
    return (
        {**LSOAS, "E01999001": first, "E01999002": second},
        {**MSOAS, "E02999001": own},
    )


def refused(
    folder: Path, table: bytes, as_at: str = "2025-03-31", member: str = TABLE
) -> LockError:
    """The refusal of a table, which repeats nothing the table holds."""
    inputs = inputs_with(folder, table, as_at, member)
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        homes_post2000.build(inputs, found)
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return stopped.value


# The figure


def test_the_share_is_the_new_homes_of_an_area_over_its_homes_that_have_a_period(tmp_path: Path):
    found = built(tmp_path).worked
    assert found == {
        ONE: Worked(30.0, 1, 1, 1.0, State.PRESENT, ROUNDED),
        TWO: Worked(2.0, 1, 1, 1.0, State.PRESENT, MARKED),
        THREE: Worked(33.3, 1, 1, 0.9, State.PARTIAL, ROUNDED),
    }


def test_the_figure_is_read_from_the_areas_own_row_and_not_added_up_from_its_lsoas(
    tmp_path: Path,
):
    """The LSOAs of Quillhaven 001 add up to 160 new homes of 500, which is 32 in 100.

    The publisher's own row for the area holds 150 of 500. Rounding lets the
    two differ, and the row is the one a reader finds in the table.
    """
    more = {**LSOAS, "E01999001": {**LSOAS["E01999001"], PERIOD: "70"}}
    assert built(tmp_path, more).worked[ONE].value == 30.0


def test_the_period_and_every_year_are_added_and_no_earlier_period_is(tmp_path: Path):
    """A home of 1993 to 1999 is not new, and a home of the table's last year is."""
    own = {"bp_1993_1999": "300", PERIOD: "50", "bp_2009": "10", "bp_2025": "40", HOMES: "500"}
    first = {"bp_1993_1999": "200", PERIOD: "30", "bp_2009": "10", "bp_2025": "20", HOMES: "300"}
    second = {"bp_1993_1999": "100", PERIOD: "20", "bp_2025": "20", HOMES: "200"}
    found = built(tmp_path, *with_one(own, first, second))
    assert found.stock.added == ADDED and len(ADDED) == 18
    assert found.stock.last_year == 2025
    counted = found.stock.of_msoa["E02999001"]
    assert counted.since_2000 == (50, 10, *(0,) * 15, 40)
    assert (counted.new, counted.dated) == (100, 500)
    assert found.worked[ONE].value == 20.0


def test_a_share_is_given_to_one_decimal_place(tmp_path: Path):
    assert built(tmp_path).worked[THREE].value == 33.3


def test_a_share_that_stands_on_a_half_is_rounded_upward(tmp_path: Path):
    """10 new homes of 800 is 1.25 in 100, which a person who rounds by hand gives as 1.3."""
    half = with_one({PERIOD: "10", HOMES: "800"}, {PERIOD: "10", HOMES: "400"}, {HOMES: "400"})
    assert built(tmp_path, *half).worked[ONE].value == 1.3


def test_a_count_of_nought_is_a_count(tmp_path: Path):
    none = with_one({HOMES: "500"}, {HOMES: "300"}, {HOMES: "200"})
    found = built(tmp_path, *none)
    assert found.worked[ONE] == Worked(0.0, 1, 1, 1.0, State.PRESENT, ROUNDED)
    assert found.stock.of_msoa["E02999001"].since_2000 == (0,) * 18


def test_only_the_rows_for_all_bands_of_an_msoa_and_an_lsoa_are_read(tmp_path: Path):
    """A row of one band holds 990, and a row of a larger area 9990. Neither is counted."""
    found = built(tmp_path)
    assert set(found.stock.of_lsoa) == set(LSOAS)
    assert set(found.stock.of_msoa) == set(MSOAS)
    # 6 larger areas, 4 MSOAs and 7 English LSOAs have 9 rows each, and the Welsh LSOA has 10.
    assert found.stock.rows == 9 * (6 + 4 + 7) + 10
    for one in (*found.stock.of_lsoa.values(), *found.stock.of_msoa.values()):
        assert one.homes not in (990, 9990)
        assert not {990, 9990} & set(one.since_2000)


# A count too small to round


def test_a_dash_beside_a_count_adds_nothing_and_marks_the_figure(tmp_path: Path):
    found = built(tmp_path)
    counted = found.stock.of_msoa["E02999002"]
    assert counted.since_2000[:2] == (10, None)
    assert (counted.new, counted.dashes, counted.new_withheld) == (10, 1, True)
    assert found.worked[TWO] == Worked(2.0, 1, 1, 1.0, State.PRESENT, MARKED)


def test_every_dash_is_counted_and_each_can_hide_four_homes(tmp_path: Path):
    own = {PERIOD: "100", "bp_2009": "-", "bp_2016": "-", "bp_2024": "-", HOMES: "500"}
    first = {PERIOD: "60", "bp_2009": "-", "bp_2016": "-", HOMES: "300"}
    second = {PERIOD: "40", "bp_2024": "-", HOMES: "200"}
    found = built(tmp_path, *with_one(own, first, second))
    counted = found.stock.of_msoa["E02999001"]
    assert (counted.dashes, counted.hidden_at_most) == (3, 12)
    assert found.worked[ONE] == Worked(20.0, 1, 1, 1.0, State.PRESENT, MARKED)


@pytest.mark.parametrize(
    ("own", "parts"),
    [
        # A dash for the period and for a year: the area has 2 to 8 new homes.
        (
            {PERIOD: "-", "bp_2012": "-", HOMES: "500"},
            ({PERIOD: "-", "bp_2012": "-", HOMES: "300"}, {HOMES: "200"}),
        ),
        # A dash for one year and nought for every other count: the area has 1 to 4.
        (
            {"bp_2025": "-", HOMES: "500"},
            ({"bp_2025": "-", HOMES: "300"}, {"bp_2025": "-", HOMES: "200"}),
        ),
        (
            {PERIOD: "-", HOMES: "500"},
            ({HOMES: "300"}, {PERIOD: "-", HOMES: "200"}),
        ),
    ],
)
def test_new_homes_that_are_all_too_small_to_round_are_never_said_to_be_nought(
    tmp_path: Path, own: Cells, parts: tuple[Cells, Cells]
):
    """The share is above nought and the file does not say what it is, so none is given."""
    found = built(tmp_path, *with_one(own, *parts))
    assert found.worked[ONE] == Worked(None, 0, 1, 0.0, State.SUPPRESSED, MARKED)
    row = next(row for row in found.rows if row.area_id == ONE)
    assert (row.state, row.has_a_value, row.flags) == (State.SUPPRESSED, False, MARKED)


def test_a_dash_for_homes_of_no_known_period_does_not_mark_the_figure(tmp_path: Path):
    """It moves the bottom by at most 4 homes, which is less than rounding does."""
    own = {**MSOAS["E02999001"], UNKNOWN: "-"}
    first, second = LSOAS["E01999001"], {**LSOAS["E01999002"], UNKNOWN: "-"}
    found = built(tmp_path, *with_one(own, first, second))
    assert found.worked[ONE] == Worked(30.0, 1, 1, 1.0, State.PRESENT, ROUNDED)


def test_a_dash_in_the_row_of_an_lsoa_does_not_mark_a_figure_read_from_its_msoa(
    tmp_path: Path,
):
    lsoas = {**LSOAS, "E01999002": {**LSOAS["E01999002"], "bp_2009": "-"}}
    found = built(tmp_path, lsoas)
    assert found.worked[ONE] == Worked(30.0, 1, 1, 1.0, State.PRESENT, ROUNDED)


# More than the whole


def test_counts_that_come_to_more_than_the_whole_within_rounding_give_the_whole(
    tmp_path: Path,
):
    """Each count is rounded by itself: 510 new homes of 500 is no share, and 100 in 100 is.

    Three numbers are added and two are in the bottom, so rounding allows 25
    homes over. The area is 10 over.
    """
    own = {PERIOD: "300", "bp_2015": "110", "bp_2020": "100", HOMES: "500"}
    first = {PERIOD: "200", "bp_2015": "50", "bp_2020": "50", HOMES: "300"}
    second = {PERIOD: "100", "bp_2015": "50", "bp_2020": "50", HOMES: "200"}
    found = built(tmp_path, *with_one(own, first, second))
    counted = found.stock.of_msoa["E02999001"]
    assert (counted.new, counted.dated, counted.over, counted.rounding_allows) == (
        510,
        500,
        10,
        25,
    )
    assert found.worked[ONE] == Worked(100.0, 1, 1, 1.0, State.PRESENT, ROUNDED)
    assert found.at_the_whole == {ONE}


def test_no_area_is_said_to_be_at_the_whole_whose_counts_come_to_no_more(tmp_path: Path):
    all_new = with_one(
        {PERIOD: "500", HOMES: "500"}, {PERIOD: "300", HOMES: "300"}, {PERIOD: "200", HOMES: "200"}
    )
    found = built(tmp_path, *all_new)
    assert found.worked[ONE].value == 100.0
    assert found.at_the_whole == frozenset()


def test_counts_that_come_to_more_than_rounding_allows_stop_the_build(tmp_path: Path):
    """One number is added, so rounding allows 15 homes over. No figure is cut to fit."""
    over = with_one(
        {PERIOD: "520", HOMES: "500"}, {PERIOD: "310", HOMES: "300"}, {PERIOD: "210", HOMES: "200"}
    )
    assert "more than the whole" in str(refused(tmp_path, table_of(*over)))


# The row of an area is held to the rows of its LSOAs


def test_the_row_of_every_area_is_held_to_the_rows_of_its_lsoas(tmp_path: Path):
    assert built(tmp_path).rows_held == 3


@pytest.mark.parametrize(
    ("own", "words"),
    [
        # The MSOA holds 50 homes of 2009, and its LSOAs hold a dash and nought.
        ({"bp_2009": "50"}, "an area's count is not within rounding of its parts"),
        # The MSOA holds a dash for the period, and one of its LSOAs a number.
        ({PERIOD: "-"}, "a dash hides more than a small count"),
        # The MSOA holds nought for 2009, and one of its LSOAs a dash.
        ({"bp_2009": "0"}, "an area holds nought and a part of it does not"),
        # The MSOA holds homes of 2024, and neither of its LSOAs holds any.
        ({"bp_2024": "10"}, "an area holds a count and no part of it does"),
        ({HOMES: "700"}, "an area's count is not within rounding of its parts"),
    ],
)
def test_a_row_that_is_not_what_the_rows_of_its_lsoas_allow_stops_the_build(
    tmp_path: Path, own: Cells, words: str
):
    table = table_of(msoas={**MSOAS, "E02999002": {**MSOAS["E02999002"], **own}})
    assert words in str(refused(tmp_path, table))


def test_an_area_with_no_row_of_its_own_stops_the_build(tmp_path: Path):
    fewer = {code: cells for code, cells in MSOAS.items() if code != "E02999002"}
    error = refused(tmp_path, table_of(msoas=fewer))
    assert "an MSOA of the census of 2021 has no row" in str(error)


# Homes of no known period


def test_a_home_of_no_known_period_is_left_out_and_lowers_the_coverage(tmp_path: Path):
    """Counted as not new, the 100 homes of no period would make the share 30 in 100."""
    found = built(tmp_path).worked[THREE]
    assert found == Worked(33.3, 1, 1, 0.9, State.PARTIAL, ROUNDED)


def test_with_under_half_the_homes_of_known_period_no_figure_is_given(tmp_path: Path):
    unknown = {
        **LSOAS,
        "E01999005": {PERIOD: "200", UNKNOWN: "300", HOMES: "500"},
        "E01999006": {UNKNOWN: "300", HOMES: "500"},
    }
    own = {PERIOD: "200", UNKNOWN: "600", HOMES: "1000"}
    found = built(tmp_path, unknown, {**MSOAS, "E02999003": own})
    assert found.worked[THREE] == Worked(None, 1, 1, 0.4, State.BELOW_THRESHOLD, ROUNDED)
    row = next(row for row in found.rows if row.area_id == THREE)
    assert (row.state, row.weight_covered) == (State.BELOW_THRESHOLD, 0.4)


# An area with no count of its homes


def test_an_area_with_no_count_of_all_its_homes_is_said_to_be_withheld(tmp_path: Path):
    none = with_one({HOMES: "-"}, {HOMES: "-"}, {HOMES: "-"})
    assert built(tmp_path, *none).worked[ONE] == Worked(None, 0, 1, 0.0, State.SUPPRESSED, MARKED)


def test_an_area_with_no_home_has_no_figure_and_is_never_nought(tmp_path: Path):
    none = with_one({}, {}, {})
    assert built(tmp_path, *none).worked[ONE] == Worked(None, 0, 1, 0.0, State.SOURCE_GAP, ROUNDED)


# Which columns are years


def test_a_later_edition_brings_a_year_more_and_it_is_added(tmp_path: Path):
    """The table of 31 March 2026 holds a column for 2026, and the step reads it."""
    columns = [*COLUMNS[:-2], "bp_2026", *COLUMNS[-2:]]
    own = {PERIOD: "100", "bp_2026": "50", HOMES: "500"}
    first, second = {PERIOD: "60", "bp_2026": "50", HOMES: "300"}, {PERIOD: "40", HOMES: "200"}
    lsoas, msoas = with_one(own, first, second)
    member = "CTSOP4.1/CTSOP4_1_2026_03_31.csv"
    inputs = inputs_with(tmp_path, table_of(lsoas, msoas, columns), "2026-03-31", member)
    found = homes_post2000.build(inputs, spine.build(inputs))
    assert found.stock.added == (*ADDED, "bp_2026")
    assert (found.stock.last_year, found.metric.vintage) == (2026, "2026-03-31")
    assert found.worked[ONE].value == 30.0
    assert "from 2009 to 2026" in found.metric.definition


@pytest.mark.parametrize(
    "columns",
    [
        # A year is missing from the middle, from the start and from the end.
        [name for name in COLUMNS if name != "bp_2016"],
        [name for name in COLUMNS if name != "bp_2009"],
        [name for name in COLUMNS if name != "bp_2025"],
        # A year after the year of the day the table is of.
        [*COLUMNS[:-2], "bp_2026", *COLUMNS[-2:]],
        # No year at all.
        [name for name in COLUMNS if not homes_pre1919.ONE_YEAR.fullmatch(name)],
    ],
)
def test_a_table_that_does_not_hold_each_year_to_its_own_stops_the_build(
    tmp_path: Path, columns: Sequence[str]
):
    """A year that is missing would be left out of the share, and nothing would say so."""
    error = refused(tmp_path, table_of(columns=columns))
    assert "the years since 2009 are not each there once" in str(error)


def test_a_year_that_is_there_twice_stops_the_build(tmp_path: Path):
    """The publisher's table names each column once. One that names a year twice is not it."""
    text = table_of().decode("utf-8-sig").replace("bp_2010,bp_2011", "bp_2010,bp_2010", 1)
    inputs = inputs_with(tmp_path, text.encode("utf-8-sig"))
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        homes_post2000.build(inputs, found)
    assert stopped.value.rule == "input_is_as_described"


@pytest.mark.parametrize(
    "change",
    [
        {"bp_2000_2008": "bp_2000_2009"},
        {"bp_1993_1999": "bp_1993_2001"},
        {"bp_1919_1929": "bp_1910_1929"},
    ],
)
def test_a_build_period_the_step_does_not_know_stops_the_build(
    tmp_path: Path, change: Mapping[str, str]
):
    """A period that is new may take in a year since 2000, and what is added would miss it."""
    columns = [change.get(name, name) for name in COLUMNS]
    error = refused(tmp_path, table_of(columns=columns))
    assert "is missing" in str(error) or "a build period is not one the step knows" in str(error)


@pytest.mark.parametrize("missing", homes_post2000.COLUMNS)
def test_a_table_that_lacks_a_column_stops_the_build_and_says_which(tmp_path: Path, missing: str):
    columns = [name for name in COLUMNS if name != missing]
    error = refused(tmp_path, table_of(columns=columns))
    assert f"the column {missing} is missing" in str(error)


def test_a_table_needs_no_column_that_is_not_read(tmp_path: Path):
    fewer = [name for name in COLUMNS if name not in ("area_name", "ba_code")]
    whole = built(tmp_path / "whole").worked
    inputs = inputs_with(tmp_path / "fewer", table_of(columns=fewer))
    assert homes_post2000.build(inputs, spine.build(inputs)).worked == whole


# What stops the build


@pytest.mark.parametrize(
    ("cells", "words"),
    [
        ({PERIOD: CANARY}, "a count is not a count"),
        ({"bp_2013": ""}, "a count is not a count"),
        ({"bp_2013": ".."}, "a count is not a count"),
        ({"bp_2025": "-10"}, "a count is not a count"),
        ({HOMES: "3e2"}, "a count is not a count"),
        ({"bp_2013": "14"}, "a count is not rounded to 10"),
        ({UNKNOWN: "5"}, "a count is not rounded to 10"),
    ],
)
def test_a_cell_that_cannot_be_read_stops_the_build(tmp_path: Path, cells: Cells, words: str):
    lsoas = {**LSOAS, "E01999001": {**LSOAS["E01999001"], **cells}}
    assert words in str(refused(tmp_path, table_of(lsoas)))


@pytest.mark.parametrize("cells", [{"bp_2021": CANARY}, {HOMES: "504"}])
def test_a_cell_of_the_row_of_an_msoa_that_cannot_be_read_stops_the_build(
    tmp_path: Path, cells: Cells
):
    msoas = {**MSOAS, "E02999001": {**MSOAS["E02999001"], **cells}}
    assert "a count is not" in str(refused(tmp_path, table_of(msoas=msoas)))


def test_a_code_that_is_not_a_code_stops_the_build(tmp_path: Path):
    error = refused(tmp_path, table_of({**LSOAS, "Zzyzx-001": {HOMES: "10"}}))
    assert "a code is not a code" in str(error)
    assert "Zzyzx" not in str(error)


def test_a_table_that_lacks_an_lsoa_of_the_spine_stops_the_build(tmp_path: Path):
    """A table on the codes of another census lacks every LSOA that was drawn again."""
    fewer = {code: cells for code, cells in LSOAS.items() if code != "E01999004"}
    error = refused(tmp_path, table_of(fewer))
    assert "an LSOA of the census of 2021 has no row" in str(error)


@pytest.mark.parametrize(
    "name", ["CTSOP4.1/CTSOP4_1.csv", "CTSOP4.1/CTSOP4_1_2025_13_31.csv", "CTSOP4.1/homes.csv"]
)
def test_a_table_that_is_not_named_for_a_day_stops_the_build(tmp_path: Path, name: str):
    assert "not named for a day" in str(refused(tmp_path, table_of(), member=name))


def test_a_table_of_another_day_than_its_receipt_gives_stops_the_build(tmp_path: Path):
    error = refused(tmp_path, table_of(), as_at="2024-03-31")
    assert "not of the day its receipt gives" in str(error)


# The gate, and what is read


def without_scoring() -> Registry:
    """The repository's registry, with the table of homes no longer registered for scoring."""
    sources = [
        source.model_copy(update={"uses": (Use.DISPLAY,)})
        if source.id == homes_post2000.SOURCE
        else source
        for source in registry()
    ]
    return Registry(tuple(sources))


def test_the_gate_is_asked_before_the_table_is_read(tmp_path: Path):
    inputs = inputs_with(tmp_path, registry=without_scoring())
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        homes_post2000.build(inputs, found)
    assert stopped.value.rule == "gate_refuses"
    assert all(one.receipt.source_id != homes_post2000.SOURCE for one in inputs.opened)


def test_it_reads_the_table_homes_built_before_1919_reads(tmp_path: Path):
    """One file of the publisher holds every build period, and both measures read it."""
    assert homes_post2000.SOURCE == homes_pre1919.SOURCE
    assert homes_post2000.is_the_table is homes_pre1919.is_the_table
    inputs = inputs_with(tmp_path)
    found = spine.build(inputs)
    new, old = homes_post2000.build(inputs, found), homes_pre1919.build(inputs, found)
    assert new.stock.file_id == old.stock.file_id
    assert new.files == old.files


def test_a_table_of_another_name_is_not_taken_for_this_one(tmp_path: Path):
    """The source has three tables. The one read is the one by build period."""
    given = inputs_with(tmp_path)
    other = [
        receipt.model_copy(update={"publisher_file": "CTSOP3.1.zip"})
        if receipt.source_id == homes_post2000.SOURCE
        else receipt
        for receipt in given.receipts
    ]
    inputs = Inputs(given.registry, other, given.store, given.work)
    with pytest.raises(LockError) as stopped:
        homes_post2000.build(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_has_one_receipt"


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_with(tmp_path)
    before = held(tmp_path / "store")
    homes_post2000.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before


def test_the_same_files_give_the_same_figures(tmp_path: Path):
    first, second = built(tmp_path / "a"), built(tmp_path / "b")
    assert (first.worked, first.rows, first.metric) == (second.worked, second.rows, second.metric)


def test_a_spine_of_another_build_is_refused(tmp_path: Path):
    other = spine.build(inputs_of(tmp_path / "other", contents()))
    inputs = inputs_with(tmp_path / "this")
    with pytest.raises(ValueError, match="files of this build"):
        homes_post2000.build(inputs, other)


# The evidence


def test_every_area_has_a_row_of_evidence_whether_or_not_it_has_a_figure(tmp_path: Path):
    none = with_one({HOMES: "-"}, {HOMES: "-"}, {HOMES: "-"})
    found = built(tmp_path, *none)
    assert [row.fact_id for row in found.rows] == [
        f"{area}/feature/homes_post2000" for area in (ONE, TWO, THREE)
    ]
    assert [row.state for row in found.rows] == [State.SUPPRESSED, State.PRESENT, State.PARTIAL]
    assert [row.has_a_value for row in found.rows] == [False, True, True]


def test_a_row_names_the_table_and_the_lookup_and_not_the_census(tmp_path: Path):
    """Nothing is shared out by homes while the figure is the area's own row."""
    found = built(tmp_path)
    sources = {receipt.source_id: receipt.file_id for receipt in found.files}
    assert set(sources) == {homes_post2000.SOURCE, spine.LOOKUP}
    lookup = next(receipt for receipt in found.files if receipt.source_id == spine.LOOKUP)
    for row in found.rows:
        assert set(row.inputs) == set(sources.values())
        assert row.derivation_id == AREA_ROW_RATIO.derivation_id
        assert (row.units_used, row.units_expected) == (1, 1)
        # From the lookup, which says which MSOA an area is, to the day the table is of.
        assert row.data_period == Period(start=lookup.data_period.days()[0], end="2025-03-31")
    assert found.stock.file_id == sources[homes_post2000.SOURCE]


def test_the_evidence_of_the_measure_has_no_loose_end(tmp_path: Path):
    found = built(tmp_path)
    evidence = Evidence.of("lon-2026-09-23-01", found.files, homes_post2000.METHODS, found.rows)
    assert len(evidence.rows) == 3
    assert evidence.sources_of(evidence.rows[0]) == {receipt.source_id for receipt in found.files}
    method = evidence.method(found.rows[0].derivation_id or "")
    assert method is not None and method.kind is Kind.MEASURED


# The name, the unit and the period


def test_the_name_the_unit_and_which_way_is_more_are_core_s(tmp_path: Path):
    metric = built(tmp_path).metric
    feature = FEATURES[FeatureId.HOMES_POST2000]
    assert (metric.label, metric.unit) == ("Homes built since 2000", "%")
    assert (metric.label, metric.unit, metric.polarity, metric.dimension) == (
        feature.label,
        feature.unit,
        feature.polarity,
        feature.dimension,
    )
    assert metric.native_resolution == "lsoa"
    assert says_what_core_says(metric)


def test_the_measure_is_on_the_list_of_a_build(tmp_path: Path):
    """Its row is core's and its file has a receipt, so a build carries it."""
    (listed,) = [measure for measure in MEASURES if measure.feature is homes_post2000.FEATURE]
    assert (listed.source, listed.reads) == (homes_post2000.SOURCE, homes_post2000.is_the_table)
    assert (listed.methods, listed.cannot_see) == (
        homes_post2000.METHODS,
        homes_post2000.CANNOT_SEE,
    )
    assert not listed.in_squares and listed.waits_on == ()
    assert [measure.feature for measure in MEASURES] == sorted(
        measure.feature for measure in MEASURES
    )


def test_the_period_is_the_day_the_table_is_of(tmp_path: Path):
    found = built(tmp_path)
    assert found.stock.as_at == found.metric.vintage == "2025-03-31"
    assert found.geography is Geography.MSOA21


def test_the_measure_names_every_source_a_figure_rests_on(tmp_path: Path):
    assert built(tmp_path).metric.source_ids == (spine.LOOKUP, homes_post2000.SOURCE)


def test_the_definition_is_one_sentence_that_states_what_it_is_made_with(tmp_path: Path):
    """It is held to the rule of a method's sentence: one sentence, every number in it."""
    definition = built(tmp_path).metric.definition
    stated = Method(
        derivation_id="homes_post2000@1",
        sentence=definition,
        kind=Kind.MEASURED,
        parameters={
            "built_since": 2000,
            "first_year": 2009,
            "last_year": 2025,
            "rounded_to": 10,
            "most_hidden": 4,
            "whole": 100,
            "decimal_places": 1,
        },
        code="burro_pipeline.derive.homes_post2000",
    )
    assert stated.sentence == definition
    for words in ("Valuation Office Agency", "2025-03-31", "no recorded build period"):
        assert words in definition
    assert "its count of all homes less its count of homes of no recorded build period" in (
        definition
    )


def test_the_definition_says_what_a_dash_and_a_rounded_year_do_to_the_share(tmp_path: Path):
    """So that nobody reads the share as a floor, or as exact."""
    definition = built(tmp_path).metric.definition
    for words in (
        "the publisher's own for the area",
        "not added up from smaller areas",
        "its count for 2000 to 2008 and its count for each year from 2009 to 2025",
        "a count of 1 to 4 and too small to round, the year adds nothing",
        "as a year of 5 to 9 homes adds 10",
        "no figure is given",
        "the share is given as 100",
        "with a half taken upward",
    ):
        assert words in definition


def test_what_it_cannot_see_is_two_sentences_that_name_no_place():
    assert len(homes_post2000.CANNOT_SEE) == 2
    for line in homes_post2000.CANNOT_SEE:
        assert line.endswith(".") and line.count(". ") == 0
        assert "London" not in line


# The made-up table


def test_the_made_up_table_has_the_columns_the_publishers_has():
    header = table_of().splitlines()[0]
    assert header == b"\xef\xbb\xbf" + ",".join(COLUMNS).encode()
    assert len(COLUMNS) == 35
    assert set(homes_post2000.COLUMNS) | set(ADDED) <= set(COLUMNS)
    assert COLUMNS[15:33] == ADDED
