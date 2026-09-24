"""The period of one indicator, in a workbook that holds many.

Every receipt here is made up. The workbook stands in for File 8 of the
Indices of Deprivation, whose columns are of different years.
"""

import pytest
from burro_pipeline.derive.methods import LSOA_VALUE_BY_HOMES, Worked, row_of
from burro_pipeline.derive.one_indicator import behind, cited, takes_in
from burro_pipeline.evidence.receipt import Period, Receipt
from burro_pipeline.evidence.row import State, not_carried
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry.model import Use

from ..cells.support import receipt_of

AREA = "lon-ne02999001"
NOISE, DAMAGE = Period(as_at="2021"), Period(start="2018", end="2024")


def receipt(name: str, period: Period) -> Receipt:
    made = receipt_of("mhclg-iod-2025-underlying-indicators", Use.SCORING, name, name.encode(), "1")
    return made.model_copy(update={"data_period": period})


@pytest.mark.parametrize(
    ("stated", "indicator"),
    [
        (NOISE, NOISE),
        (DAMAGE, NOISE),
        (DAMAGE, DAMAGE),
        (DAMAGE, Period(start="2022", end="2024")),
        (Period(start="2017", end="2025"), DAMAGE),
        (Period(start="2018-01-01", end="2024-12-31"), DAMAGE),
        (Period(start="2021-01", end="2021-12"), NOISE),
    ],
)
def test_a_receipt_takes_in_an_indicator_whose_every_day_is_in_its_period(
    stated: Period, indicator: Period
):
    assert takes_in(stated, indicator)


@pytest.mark.parametrize(
    ("stated", "indicator"),
    [
        (NOISE, DAMAGE),
        (NOISE, Period(as_at="2022")),
        (Period(as_at="2021-03-21"), NOISE),
        (Period(start="2018-04", end="2024-03"), DAMAGE),
        (Period(start="2019", end="2024"), DAMAGE),
        (Period(start="2018", end="2023"), DAMAGE),
    ],
)
def test_a_receipt_of_fewer_days_than_the_indicator_does_not_take_it_in(
    stated: Period, indicator: Period
):
    assert not takes_in(stated, indicator)


def test_what_stands_behind_a_figure_is_the_indicator_and_every_other_file():
    lookup, homes = (
        receipt("lookup", Period(as_at="2022-12")),
        receipt("homes", Period(as_at="2021-03-21")),
    )
    assert behind(NOISE, [lookup, homes]) == Period(start="2021-01-01", end="2022-12-31")
    assert behind(DAMAGE, [lookup, homes]) == Period(start="2018-01-01", end="2024-12-31")
    two_years = Period(start="2022", end="2024")
    assert behind(two_years, [lookup, homes]) == Period(start="2021-03-21", end="2024-12-31")
    assert behind(Period(as_at="2021-03-21"), [homes]) == Period(as_at="2021-03-21")
    assert behind(NOISE, []) == Period(start="2021-01-01", end="2021-12-31")


def test_a_row_states_the_years_of_its_indicator_whatever_the_receipt_of_the_workbook_states():
    """So the row of one measure does not move when the receipt is put right for another."""
    lookup = receipt("lookup", Period(as_at="2022-12"))
    worked = Worked(52.0, 2, 2, 1.0, State.PRESENT)
    found: list[Period | None] = []
    for stated in (NOISE, DAMAGE, Period(start="2000", end="2030")):
        workbook = receipt("workbook", stated)
        files = (workbook, lookup)
        row = row_of(f"{AREA}/feature/noise_exposure", worked, LSOA_VALUE_BY_HOMES, files)
        (made,) = cited([row], workbook, files, NOISE)
        found.append(made.data_period)
        assert made.model_copy(update={"data_period": row.data_period}) == row
        # The row stands as evidence: its period is inside the periods of its files.
        assert Evidence.of("lon-2026-10-02-01", files, [LSOA_VALUE_BY_HOMES], [made])
    assert found == [Period(start="2021-01-01", end="2022-12-31")] * 3


def test_a_row_that_names_no_file_states_no_period_and_is_left_as_it_is():
    bare = not_carried(f"{AREA}/feature/noise_exposure")
    workbook = receipt("workbook", DAMAGE)
    assert cited([bare], workbook, (workbook,), NOISE) == (bare,)
