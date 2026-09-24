"""What a home sells for, as the cost of a release: one number for each kind of home.

Every file here is made up: the workbook of `price_support.py`, which is laid
out as the publisher lays out its own and holds three made-up MSOAs.

    MSOA        area             any kind   detached   semi      terraced   flat
    E02999001   Quillhaven 001    410000    [x]        525000    450000     300000
    E02999002   Quillhaven 002    655000    1200000    [x]       700500     [x]
    E02999003   Tallowgate 001    287500    no row     no row    [x]        250000
"""

from pathlib import Path

import pytest
from burro_core.ids import Confidence, Segment, Tenure
from burro_core.release import CostEstimate
from burro_pipeline.cells import spine
from burro_pipeline.derive import price
from burro_pipeline.derive.price import Prices
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry.model import INTERNAL_USES, Use

from ..cells.support import registry
from .price_support import PRICES, Q1, SOURCE, THE_YEAR_BEFORE, book, inputs_of, listed

A1, A2, A3 = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
LOOKUP = "ons-oa21-lsoa21-msoa21-lad22-lookup"


def built(folder: Path, content: bytes | None = None, period: Period | None = None) -> Prices:
    inputs = inputs_of(folder, book() if content is None else content, period=period)
    return price.build(inputs, spine.build(inputs))


def by_key(rows: tuple[CostEstimate, ...]) -> dict[tuple[str, str], CostEstimate]:
    return {(row.area_id, row.segment): row for row in rows}


# The gate


def test_the_registry_allows_the_workbook_to_be_scored_on_and_shown():
    """The founder decided on 2026-09-24 that what a home sells for may be shown."""
    assert price.USE is Use.SCORING
    assert price.USE not in INTERNAL_USES
    for use in (Use.SCORING, Use.DISPLAY):
        assert registry().require(SOURCE, use).id == SOURCE


def test_the_credit_is_the_publishers_own_words_and_names_both_publishers():
    entry = registry().get(SOURCE)
    assert entry.attribution_verified is True
    assert entry.attribution == (
        "Source: Office for National Statistics. These statistics were adapted from data "
        "from the HM Land Registry licensed under the Open Government Licence v.3.0."
    )


# The rows


def test_each_kind_of_home_with_a_figure_is_a_price_with_a_median_and_no_range(tmp_path: Path):
    rows = by_key(price.costs(built(tmp_path)))
    assert {key: row.median for key, row in rows.items()} == {
        (A1, "semi_detached"): 525_000,
        (A1, "terraced"): 450_000,
        (A1, "flat"): 300_000,
        (A2, "detached"): 1_200_000,
        (A2, "terraced"): 700_500,
        (A3, "flat"): 250_000,
    }
    for row in rows.values():
        assert row.tenure is Tenure.BUY
        assert (row.lower_quartile, row.upper_quartile) == (None, None)
        assert row.confidence is Confidence.UNSTATED


def test_a_figure_the_publisher_withheld_is_no_row_and_is_never_nought(tmp_path: Path):
    rows = by_key(price.costs(built(tmp_path)))
    for missing in ((A1, "detached"), (A2, "semi_detached"), (A2, "flat"), (A3, "terraced")):
        assert missing not in rows
    # A kind of home with no row for the area on its sheet is no row either.
    assert (A3, "detached") not in rows and (A3, "semi_detached") not in rows
    assert all(row.median > 0 for row in rows.values())


def test_the_median_of_homes_of_any_kind_is_no_cost_of_the_contract(tmp_path: Path):
    """The contract holds a price by kind of home. A home of any kind is none of its kinds."""
    found = built(tmp_path)
    assert found.of[price.ALL.key].home.segment is None
    assert {row.segment for row in price.costs(found)} <= {
        Segment.FLAT,
        Segment.TERRACED,
        Segment.SEMI_DETACHED,
        Segment.DETACHED,
    }
    assert len(price.costs(found)) == 6
    assert not any("price_median" in row.fact_id for row in price.evidence(found))


def test_a_figure_is_carried_to_the_pound_and_is_never_rounded_or_scaled(tmp_path: Path):
    """The contract rounds an estimate to 5,000. This is the number a reader finds in the file."""
    found = built(tmp_path, book({**PRICES, "1e": {**PRICES["1e"], Q1: 481_546}}))
    assert by_key(price.costs(found))[A1, "flat"].median == 481_546


def test_a_row_is_dated_by_the_last_month_of_the_year_of_sales(tmp_path: Path):
    assert {row.as_of for row in price.costs(built(tmp_path))} == {"2026-03"}
    before = Period(start="2024-04", end="2025-03")
    content = book(year=THE_YEAR_BEFORE, contents_of=listed("March 2025"))
    assert {row.as_of for row in price.costs(built(tmp_path / "b", content, before))} == {"2025-03"}


def test_a_row_cites_the_workbook_and_the_lookup_that_says_which_msoa_an_area_is(
    tmp_path: Path,
):
    for row in price.costs(built(tmp_path)):
        assert row.source_ids == (SOURCE, LOOKUP)


def test_the_rows_are_in_the_order_a_release_keeps_them(tmp_path: Path):
    rows = price.costs(built(tmp_path))
    assert list(rows) == sorted(rows, key=lambda row: (row.area_id, row.tenure, row.segment))


# The evidence


def test_every_area_and_kind_of_home_has_a_row_of_evidence_under_the_id_of_its_cost(
    tmp_path: Path,
):
    rows = {row.fact_id: row for row in price.evidence(built(tmp_path))}
    assert sorted(rows) == sorted(
        f"{area}/cost/buy.{segment}"
        for area in (A1, A2, A3)
        for segment in ("detached", "flat", "semi_detached", "terraced")
    )


def test_the_row_of_a_price_holds_the_median_so_that_a_changed_figure_is_found(tmp_path: Path):
    rows = {row.fact_id: row for row in price.evidence(built(tmp_path))}
    flat = rows[f"{A1}/cost/buy.flat"]
    assert (flat.state, flat.value, flat.flags) == (State.PRESENT, 300_000.0, ())
    assert (flat.units_used, flat.units_expected, flat.weight_covered) == (1, 1, 1.0)
    assert flat.derivation_id == price.AREA_ROW_VALUE.derivation_id


def test_a_price_that_is_missing_has_a_row_that_says_why(tmp_path: Path):
    rows = {row.fact_id: row for row in price.evidence(built(tmp_path))}
    withheld = rows[f"{A2}/cost/buy.flat"]
    assert (withheld.state, withheld.value) == (State.SUPPRESSED, None)
    assert withheld.flags == (Flag.SUPPRESSED_IN_SOURCE,)
    gap = rows[f"{A3}/cost/buy.detached"]
    assert (gap.state, gap.value, gap.flags) == (State.SOURCE_GAP, None, ())
    assert all(row.inputs and row.derivation_id for row in rows.values())


def test_the_rows_stand_as_the_evidence_of_a_release(tmp_path: Path):
    found = built(tmp_path)
    evidence = Evidence.of("lon-2026-10-02-01", found.files, price.METHODS, price.evidence(found))
    assert len(evidence.rows) == 12
    row = evidence.row(f"{A2}/cost/buy.terraced")
    assert row is not None and row.value == 700_500.0
    assert evidence.sources_of(row) == frozenset({SOURCE, LOOKUP})


# What is said beside a figure


def test_what_the_figure_cannot_see_is_said_in_words_a_person_will_read():
    together = " ".join(price.CANNOT_SEE)
    for said in ("all sizes", "5 sales", "not sold", "asking price", "rent"):
        assert said in together
    for words in price.CANNOT_SEE:
        assert words.endswith(".") and "!" not in words and len(words) < 250


def test_a_renter_is_told_that_no_rent_is_held():
    assert price.NO_RENT.endswith(".") and "!" not in price.NO_RENT
    for said in ("rent", "borough", "postcode district"):
        assert said in price.NO_RENT


@pytest.mark.parametrize("key", [home.key for home in price.HOMES if home.segment is not None])
def test_the_definition_of_each_kind_says_it_is_the_price_of_no_one_size(tmp_path: Path, key: str):
    definition = built(tmp_path).of[key].named.definition
    assert "is not" in definition and "the price of a home of any one size" in definition
