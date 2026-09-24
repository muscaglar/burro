"""Addresses with private outdoor space, worked out from the workbook its publisher gave.

Every other test of the measure runs on a made-up workbook. These read the real
one, and are skipped where the store of fetched files is not, and until the
workbook has its receipt in `data/receipts/`. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt.

They hold the counts and three figures, so that a publisher's file that changes
is noticed. The three figures are London's lowest, middle and highest. None is
said of a named area or of a named borough. Each was worked out on 2026-09-24,
from the workbook the page names April 2020, and no person has checked one.

The measure is the share of all addresses. The same three figures are held for
houses alone and for flats alone, which the measure does not read, because they
say what the share of all is made of: nearly every house has outdoor space, so
what differs between two areas is how many of their homes are flats, and how
many of those flats have any.

The workbook names no census. What is held here is what its codes are not:
some areas of the build have no row, so the codes are not those of 2021.

The workbook's own words for its source: "Source: Ordnance Survey" and
"© Crown copyright and database rights 2020 OS 100019153". It is published
under the Open Government Licence v3.0, as its page says.

Nothing is written to the store. A file is copied out of it to be read.
"""

import statistics
from collections import Counter

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import private_outdoor_space as outdoor
from burro_pipeline.derive.noise_sheet import Under, read_sheet
from burro_pipeline.derive.private_outdoor_space import OutdoorSpace
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use
from burro_pipeline.rounding import to_places

from .real_files import RECEIPTS, SKIPPED, real_inputs
from .test_private_outdoor_space import UNDER_FLATS, UNDER_HOUSES, UNDER_TOTAL

pytestmark = [
    SKIPPED,
    pytest.mark.skipif(
        not (RECEIPTS / outdoor.SOURCE).is_dir(),
        reason="the workbook has no receipt yet: it is written when the file is fetched again",
    ),
]
WORKBOOK, LOOKUP = "f-e3d7ac61f751", "f-49321b95f212"
HOUSES, FLATS = "Property type: Houses", "Property type: Flats"


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def built(real: Inputs, found: Spine) -> OutdoorSpace:
    return outdoor.build(real, found)


# The workbook


def test_the_receipt_states_what_the_list_states(real: Inputs):
    opened = real.open(outdoor.SOURCE, Use.SCORING, named=outdoor.is_the_workbook)
    assert opened.file_id == WORKBOOK
    assert opened.receipt.edition == outdoor.EDITION
    assert opened.receipt.data_period == Period(as_at="2020-04")


@pytest.mark.parametrize(
    ("heading", "names"),
    [(HOUSES, UNDER_HOUSES), (FLATS, UNDER_FLATS), (outdoor.TOTAL, UNDER_TOTAL)],
)
def test_the_made_up_sheet_has_the_columns_of_the_real_one(
    real: Inputs, heading: str, names: tuple[str, ...]
):
    """The tests that run everywhere read a sheet laid out as this one is."""
    opened = real.open(outdoor.SOURCE, Use.SCORING, named=outdoor.is_the_workbook)
    under = Under(heading, names)
    rows = read_sheet(opened, outdoor.SHEET, (outdoor.CODE,), under=under)
    assert len(rows) == 8_480
    assert all(set(row) == {outdoor.CODE, *names} for row in rows)


def test_a_count_is_named_under_a_heading_and_nowhere_else(real: Inputs):
    opened = real.open(outdoor.SOURCE, Use.SCORING, named=outdoor.is_the_workbook)
    with pytest.raises(LockError, match=f"the column {outdoor.ADDRESSES} is missing"):
        read_sheet(opened, outdoor.SHEET, (outdoor.CODE, outdoor.ADDRESSES))


def counts_under(real: Inputs, heading: str) -> dict[str, tuple[int, int]]:
    """The two counts of every row of an area, under one heading of the sheet.

    No count is empty under any heading. One that was would stop here, and is never nought.
    """
    opened = real.open(outdoor.SOURCE, Use.SCORING, named=outdoor.is_the_workbook)
    under = Under(heading, (outdoor.ADDRESSES, outdoor.WITH_SPACE))
    found: dict[str, tuple[int, int]] = {}
    for row in read_sheet(opened, outdoor.SHEET, (outdoor.CODE,), under=under):
        code, addresses, with_space = (
            row[outdoor.CODE],
            row[outdoor.ADDRESSES],
            row[outdoor.WITH_SPACE],
        )
        if not isinstance(code, str) or not outdoor.AN_AREA.fullmatch(code):
            continue
        assert isinstance(addresses, int | float) and isinstance(with_space, int | float)
        found[code] = (int(addresses), int(with_space))
    return found


def test_the_counts_of_houses_and_of_flats_come_to_the_count_of_both(real: Inputs):
    """In every row. So the share of all is the two shares, weighed by how many of each."""
    houses, flats = counts_under(real, HOUSES), counts_under(real, FLATS)
    both = counts_under(real, outdoor.TOTAL)
    assert len(both) == 8_480 and set(houses) == set(flats) == set(both)
    for code, (addresses, with_space) in both.items():
        assert houses[code][0] + flats[code][0] == addresses
        assert houses[code][1] + flats[code][1] == with_space


@pytest.mark.parametrize(
    ("heading", "lowest", "middle", "highest"),
    [(HOUSES, 27.0, 98.7, 99.9), (FLATS, 7.0, 70.1, 98.3)],
)
def test_nearly_every_house_has_outdoor_space_and_flats_differ_from_area_to_area(
    real: Inputs, found: Spine, heading: str, lowest: float, middle: float, highest: float
):
    """Over the 963 areas of London that have a row. The measure reads neither share."""
    held = counts_under(real, heading)
    shares = sorted(
        to_places(100 * held[area.code][1] / held[area.code][0], outdoor.DECIMALS)
        for area in found.areas
        if area.code in held and held[area.code][0]
    )
    assert len(shares) == 963
    assert (shares[0], statistics.median(shares), shares[-1]) == (lowest, middle, highest)


def test_the_workbook_holds_as_many_areas_as_were_counted(built: OutdoorSpace):
    """An area is an MSOA of England or of Wales, or an intermediate zone of Scotland."""
    assert built.table.rows == 8_480
    assert Counter(code[0] for code in built.table.of_area) == {"E": 6_791, "W": 410, "S": 1_279}


def test_no_count_of_the_workbook_is_withheld(built: OutdoorSpace):
    assert all(one.whole for one in built.table.of_area.values())


def test_the_codes_of_the_workbook_are_not_those_of_the_census_of_2021(
    built: OutdoorSpace, found: Spine
):
    """Of London's areas of 2021 the workbook lacks 39, in 14 boroughs. It names no census."""
    assert built.geography is Geography.MSOA11
    assert len(built.without_a_row) == 39
    lacking = Counter(
        area.borough_code for area in found.areas if area.area_id in built.without_a_row
    )
    assert sorted(lacking.values(), reverse=True) == [5, 4, 4, 4, 4, 3, 2, 2, 2, 2, 2, 2, 2, 1]


# The figures


def test_every_area_the_workbook_holds_has_a_figure_and_no_other_has(built: OutdoorSpace):
    assert len(built.worked) == 1_002
    assert Counter(one.state for one in built.worked.values()) == {
        State.PRESENT: 963,
        State.SOURCE_GAP: 39,
    }
    assert Counter(one.weight_covered for one in built.worked.values()) == {1.0: 963, 0.0: 39}
    for area in built.without_a_row:
        assert built.worked[area].value is None


def test_the_lowest_the_middle_and_the_highest_figure_are_what_was_worked_out(
    built: OutdoorSpace,
):
    found = sorted(one.value for one in built.worked.values() if one.value is not None)
    assert (found[0], statistics.median(found), found[-1]) == (7.2, 86.1, 99.6)


def test_a_row_of_evidence_names_the_workbook_and_the_lookup(built: OutdoorSpace):
    assert {receipt.file_id for receipt in built.files} == {WORKBOOK, LOOKUP}
    for row in built.rows:
        assert set(row.inputs) == {WORKBOOK, LOOKUP}
    evidence = Evidence.of("lon-2026-09-24-01", built.files, outdoor.METHODS, built.rows)
    assert len(evidence.rows) == 1_002


def test_the_figure_is_as_at_the_month_the_page_names(built: OutdoorSpace):
    assert built.metric.vintage == "2020-04"
    assert "as at 2020-04" in built.metric.definition
