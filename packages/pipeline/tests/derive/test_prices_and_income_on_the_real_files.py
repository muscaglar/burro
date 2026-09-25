"""What homes sold for, the council tax bands, the rise in prices and household income,
worked out from the files their publishers gave.

Every other test of each runs on a made-up file. These read the real ones, and
are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold counts and states, so that a publisher's file that changes is
noticed. They hold no figure of any area: no price, no share, no rise and no
income. Each count was made on 2026-09-25, and no person has checked one.

Nothing is written to the store. A file is copied out of it to be read.
"""

from collections import Counter

import pytest
from burro_core.ids import Confidence, Segment
from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import homes_higher_bands, household_income, price_paid, price_rise
from burro_pipeline.derive.price_paid import Sold
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.inputs import Inputs

from ..cells.support import registry
from .real_files import SKIPPED, real_inputs

pytestmark = SKIPPED
AREAS = 1_002


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def sold(real: Inputs, found: Spine) -> Sold:
    return price_paid.build(real, found)


# What homes sold for


def test_the_sales_of_three_years_are_counted_as_the_files_hold_them(sold: Sold):
    counts = sold.counts
    assert (sold.since, sold.until) == ("2023-01", "2025-12")
    assert counts.rows == 2_745_967
    assert dict(counts.by_year) == {2023: 861_263, 2024: 930_559, 2025: 954_145}
    assert (counts.additional, counts.of_no_kind_of_home) == (479_554, 0)
    assert (counts.placed, counts.not_placed) == (244_811, 2_021_602)
    assert counts.rows == counts.additional + counts.placed + counts.not_placed
    assert dict(counts.by_home) == {
        Segment.DETACHED: 11_642,
        Segment.SEMI_DETACHED: 36_317,
        Segment.TERRACED: 66_009,
        Segment.FLAT: 130_843,
    }
    assert counts.newly_built[Segment.FLAT] == 15_456
    assert counts.at_an_ended_postcode == 17


@pytest.mark.parametrize(
    ("home", "present", "too_few", "none"),
    [
        (Segment.FLAT, 984, 18, 0),
        (Segment.TERRACED, 940, 58, 4),
        (Segment.SEMI_DETACHED, 653, 268, 81),
        (Segment.DETACHED, 282, 463, 257),
    ],
)
def test_a_kind_of_home_has_a_figure_where_ten_or_more_of_it_sold(
    sold: Sold, home: Segment, present: int, too_few: int, none: int
):
    states = Counter(worked.state for worked in sold.of[home].worked.values())
    assert states == Counter(
        {
            state: count
            for state, count in (
                (State.PRESENT, present),
                (State.BELOW_THRESHOLD, too_few),
                (State.SOURCE_GAP, none),
            )
            if count
        }
    )
    assert len(sold.of[home].sales) == present
    assert min(sold.of[home].sales.values()) >= price_paid.FEWEST == 10


def test_what_a_figure_rests_on_is_what_its_count_makes_it(sold: Sold):
    rows = price_paid.costs(sold)
    assert len(rows) == 2_859
    assert Counter(row.confidence for row in rows) == {
        Confidence.HIGH: 1_603,
        Confidence.MEDIUM: 1_256,
    }
    assert {(row.since, row.as_of) for row in rows} == {("2023-01", "2025-12")}
    assert all(row.lower_quartile is None and row.upper_quartile is None for row in rows)
    assert {receipt.source_id for receipt in sold.files} == {
        price_paid.SOURCE,
        "ons-postcode-directory",
        spine.LOOKUP,
    } or {receipt.source_id for receipt in sold.files} >= {price_paid.SOURCE}


# The council tax bands


def test_the_bands_give_a_figure_where_the_table_gives_a_count(real: Inputs, found: Spine):
    made = homes_higher_bands.build(real, found)
    states = Counter(worked.state for worked in made.worked.values())
    assert states == {State.PRESENT: 982, State.SUPPRESSED: 20}
    # A band that is a dash adds nothing and marks the figure: 460 figures, and the 20 areas
    # whose higher bands are all behind one.
    marked = [one for one in made.worked.values() if Flag.SUPPRESSED_IN_SOURCE in one.flags]
    assert len(marked) == 480
    assert len([one for one in marked if one.value is not None]) == 460
    assert made.rows_held == AREAS
    shares = [one.value for one in made.worked.values() if one.value is not None]
    assert all(0.0 <= share <= 100.0 for share in shares)


# The rise in prices


@pytest.mark.parametrize(("years", "fell"), [(5, 354), (10, 113)])
def test_a_rise_is_given_for_every_area_and_is_under_a_hundred_where_prices_fell(
    real: Inputs, found: Spine, years: int, fell: int
):
    made = price_rise.build(real, found, years)
    assert Counter(worked.state for worked in made.worked.values()) == {State.PRESENT: AREAS}
    values = [one.value for one in made.worked.values() if one.value is not None]
    assert sum(value < 100 for value in values) == fell
    assert all(value > 0 for value in values)
    assert made.medians.columns == {
        0: "Year ending Mar 2026",
        5: "Year ending Mar 2021",
        10: "Year ending Mar 2016",
    }


# Household income


def test_the_workbook_of_income_says_what_the_page_says_and_holds_every_area(
    real: Inputs, found: Spine
):
    made = household_income.build(real, found)
    assert (made.rows, len(made.areas), made.given) == (7_264, AREAS, AREAS)
    period = made.receipt.data_period
    assert (period.start, period.end) == ("2022-04", "2023-03")
    income = household_income.income_of("lon-2026-09-25-01", made, registry())
    assert income.synthetic is False and len(income.areas) == AREAS
    # Nothing prints a figure by accident.
    assert {repr(held) for held in made.of.values()} == {"Estimate()"}
