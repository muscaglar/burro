"""What homes sold for, from made-up files of sales to a median for each area and kind of home.

Every file here is made up: `price_paid_support.py` lays out the files as the
publisher lays out its own, and says what was sold where. No postcode here is
one that has been given out, and no address is an address.

    area             flats                          terraced houses          detached houses
    Quillhaven 001   11, at 200,000 to 300,000      none                     none
    Quillhaven 002   9, too few for a figure        10, the two middle ones  none
                                                    at 400,000 and 400,001
    Tallowgate 001   50, at 101,000 to 150,000      none                     10, all at 900,000
"""

import dataclasses
import pickle
from pathlib import Path

import pytest
from burro_core.ids import Confidence, Segment, Tenure
from burro_core.release import FEWEST_SALES, MANY_SALES, CostEstimate
from burro_pipeline.cells import postcodes, spine
from burro_pipeline.derive import price_paid
from burro_pipeline.derive.price_paid import Sold
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import INTERNAL_USES, Use

from ..cells.postcodes_support import DIRECTORY, MILL_ROW, NORTH_GATE, QUAY
from ..cells.support import held, registry
from .price_paid_support import (
    AREAS,
    CANARY,
    CANARY_PRICE,
    DETACHED,
    NOT_COUNTED,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    SALES,
    TALLOWGATE,
    TERRACED,
    YEARS,
    MadeUpSale,
    file_of,
    files_of,
    inputs_of,
    line_of,
    receipt_of,
)

LOOKUP = "ons-oa21-lsoa21-msoa21-lad22-lookup"


def built(inputs: Inputs) -> Sold:
    return price_paid.build(inputs, spine.build(inputs))


def of(*sales: MadeUpSale, folder: Path) -> Sold:
    return built(inputs_of(folder, files_of(sales)))


def by_key(rows: tuple[CostEstimate, ...]) -> dict[tuple[str, str], CostEstimate]:
    return {(row.area_id, row.segment): row for row in rows}


def refusal(folder: Path, year: int, content: bytes, **receipt: object) -> str:
    files = [
        (receipt_of(year, content, **receipt), content)  # pyright: ignore[reportArgumentType]
        if held_year == year
        else (made, held_content)
        for held_year, (made, held_content) in zip(YEARS, files_of(), strict=True)
    ]
    with pytest.raises(LockError) as refused:
        built(inputs_of(folder, files))
    assert refused.value.rule == "input_is_as_described"
    return str(refused.value)


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Sold:
    return built(inputs_of(tmp_path_factory.mktemp("town")))


# The gate, and what the licence asks


def test_the_registry_allows_the_sales_to_be_scored_on_and_shown():
    assert price_paid.USE is Use.SCORING
    assert price_paid.USE not in INTERNAL_USES
    for use in (Use.SCORING, Use.DISPLAY):
        assert registry().require(price_paid.SOURCE, use).id == price_paid.SOURCE


def test_every_column_of_an_address_is_on_the_list_of_what_is_never_read():
    """The licence registry names them: the building, the flat, the street and the rest."""
    never = {place for places in price_paid.NEVER_READ.values() for place in places}
    assert set(price_paid.NEVER_READ["address"]) == {8, 9, 10, 11, 12, 13, 14}
    assert not never & set(price_paid.READ.values())
    assert never | set(price_paid.READ.values()) == set(range(1, price_paid.WIDTH + 1))
    conditions = " ".join(registry().get(price_paid.SOURCE).conditions)
    assert "Drop PAON, SAON, Street, Locality, Town/City, District and County" in conditions


def test_no_row_of_a_sale_and_no_postcode_is_in_anything_the_step_hands_on(town: Sold):
    """What leaves the step is a median and a count by area: no sale, no postcode, no address."""
    handed_on = pickle.dumps((town, price_paid.costs(town), price_paid.evidence(town)))
    handed_on += repr((town, price_paid.costs(town), price_paid.evidence(town))).encode()
    assert CANARY.encode() not in handed_on
    assert str(CANARY_PRICE).encode() not in handed_on
    for row in DIRECTORY:
        outward, inward = row.postcode.split(" ")
        assert row.postcode.encode() not in handed_on
        assert f"{outward}{inward}".encode() not in handed_on
    # No price of any one sale is handed on, but where it is the median of its area.
    medians = {row.median for row in price_paid.costs(town)}
    for sale in SALES:
        assert str(sale.price).encode() not in handed_on or sale.price in medians


def test_a_sale_prints_nothing_of_itself():
    sale = price_paid.Sale(250_000, Segment.FLAT, False, NORTH_GATE.postcode)
    assert repr(sale) == str(sale) == "Sale()"


def test_no_figure_rests_on_fewer_sales_than_a_figure_may(town: Sold):
    """A row of a sale is of one home. A figure of a few sales would say what one sold for."""
    assert price_paid.FEWEST == FEWEST_SALES == 10
    rows = price_paid.costs(town)
    assert rows and all(row.sales is not None and row.sales >= FEWEST_SALES for row in rows)


def test_nothing_is_written_to_the_store_or_anywhere_but_the_steps_own_folder(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    built(inputs)
    assert held(tmp_path / "store") == before
    # A copy of each file that was read, and nothing that was worked out from one.
    written = {path.name for path in (tmp_path / "work").rglob("*") if path.is_file()}
    assert written == {opened.receipt.publisher_file for opened in inputs.opened}
    assert {"pp-2023.csv", "pp-2024.csv", "pp-2025.csv"} <= written


# Which sales count


def test_every_line_is_counted_and_only_a_standard_sale_of_a_home_is_placed(town: Sold):
    counts = town.counts
    assert counts.rows == len(SALES) == 96
    assert counts.by_year == {2023: 30, 2024: 36, 2025: 30}
    assert counts.additional == 3
    assert counts.of_no_kind_of_home == 0
    assert counts.placed == 90
    assert counts.not_placed == 3
    assert counts.by_home == {
        Segment.FLAT: 70,
        Segment.TERRACED: 10,
        Segment.SEMI_DETACHED: 0,
        Segment.DETACHED: 10,
    }
    assert counts.rows == counts.additional + counts.placed + counts.not_placed


def test_a_standard_sale_of_no_kind_of_home_is_counted_and_placed_nowhere(tmp_path: Path):
    other = MadeUpSale(CANARY_PRICE, NORTH_GATE.postcode, "O")
    found = of(*SALES, other, folder=tmp_path)
    assert found.counts.of_no_kind_of_home == 1
    assert price_paid.costs(found) == price_paid.costs(of(*SALES, folder=tmp_path / "b"))


def test_an_additional_sale_changes_no_figure(tmp_path: Path, town: Sold):
    without = [sale for sale in SALES if sale not in NOT_COUNTED]
    assert price_paid.costs(of(*without, folder=tmp_path)) == price_paid.costs(town)


def test_a_newly_built_home_is_counted_and_changes_no_figure(tmp_path: Path, town: Sold):
    assert town.counts.newly_built == {
        Segment.FLAT: 2,
        Segment.TERRACED: 0,
        Segment.SEMI_DETACHED: 0,
        Segment.DETACHED: 0,
    }
    none_new = [dataclasses.replace(sale, new="N") for sale in SALES]
    assert price_paid.costs(of(*none_new, folder=tmp_path)) == price_paid.costs(town)


def test_a_sale_at_a_postcode_that_has_ended_is_put_where_the_postcode_last_stood(town: Sold):
    assert town.counts.at_an_ended_postcode == 6
    assert town.of[Segment.FLAT].sales[QUILLHAVEN_1] == 11


# The figure


def test_the_figure_is_the_median_of_what_was_paid_for_the_kind_of_home(town: Sold):
    rows = by_key(price_paid.costs(town))
    assert {key: (row.median, row.sales) for key, row in rows.items()} == {
        (QUILLHAVEN_1, "flat"): (250_000, 11),
        (QUILLHAVEN_2, "terraced"): (400_001, 10),
        (TALLOWGATE, "flat"): (125_500, 50),
        (TALLOWGATE, "detached"): (900_000, 10),
    }


def test_a_median_of_an_even_number_of_sales_is_the_mean_of_the_two_in_the_middle():
    assert price_paid.median_of([1, 2, 3]) == 2
    assert price_paid.median_of([400_001, 350_000, 400_000, 450_000]) == 400_001
    assert price_paid.median_of([100, 200]) == 150
    # A half is taken upward, and never to the even pound.
    assert price_paid.median_of([100, 101]) == 101
    assert price_paid.median_of([101, 102]) == 102
    with pytest.raises(ValueError, match="at least one price"):
        price_paid.median_of([])


def test_a_flat_is_priced_apart_from_a_house(town: Sold):
    """The dear houses of an area move no figure of its flats."""
    rows = by_key(price_paid.costs(town))
    assert rows[TALLOWGATE, "flat"].median < rows[TALLOWGATE, "detached"].median
    assert town.of[Segment.FLAT].sales[TALLOWGATE] == 50


def test_too_few_sales_give_no_figure_and_the_evidence_says_how_many_there_were(town: Sold):
    worked = town.of[Segment.FLAT].worked[QUILLHAVEN_2]
    assert (worked.value, worked.state) == (None, State.BELOW_THRESHOLD)
    assert (worked.units_used, worked.units_expected) == (9, FEWEST_SALES)
    assert worked.weight_covered == 0.9
    assert (QUILLHAVEN_2, "flat") not in by_key(price_paid.costs(town))
    [row] = [r for r in town.of[Segment.FLAT].rows if r.area_id == QUILLHAVEN_2]
    assert (row.state, row.value, row.units_used) == (State.BELOW_THRESHOLD, None, 9)


def test_no_sale_at_all_is_a_gap_and_never_nought(town: Sold):
    for area in AREAS:
        worked = town.of[Segment.SEMI_DETACHED].worked[area]
        assert (worked.value, worked.state, worked.units_used) == (None, State.SOURCE_GAP, 0)
    assert not [row for row in price_paid.costs(town) if row.segment is Segment.SEMI_DETACHED]
    assert all(row.median > 0 for row in price_paid.costs(town))


def test_one_more_sale_gives_the_figure(tmp_path: Path):
    tenth = MadeUpSale(305_000, MILL_ROW.postcode)
    rows = by_key(price_paid.costs(of(*SALES, tenth, folder=tmp_path)))
    assert (rows[QUILLHAVEN_2, "flat"].median, rows[QUILLHAVEN_2, "flat"].sales) == (313_500, 10)


def test_every_area_has_a_figure_or_a_state_for_every_kind_of_home(town: Sold):
    assert tuple(town.of) == price_paid.HOMES
    for priced in town.of.values():
        assert set(priced.worked) == set(AREAS)
        assert len(priced.rows) == len(AREAS)
        for worked in priced.worked.values():
            assert (worked.value is None) == (worked.state is not State.PRESENT)


# The row of a release


def test_a_row_is_a_price_to_buy_with_no_range_that_says_how_many_sales_it_rests_on(town: Sold):
    for row in price_paid.costs(town):
        assert row.tenure is Tenure.BUY
        assert (row.lower_quartile, row.upper_quartile) == (None, None)
        assert row.counted and not row.ranged
        assert (row.since, row.as_of) == ("2023-01", "2025-12")
    rests_on = {(row.area_id, row.segment): row.confidence for row in price_paid.costs(town)}
    assert MANY_SALES == 50
    assert rests_on == {
        (QUILLHAVEN_1, "flat"): Confidence.MEDIUM,
        (QUILLHAVEN_2, "terraced"): Confidence.MEDIUM,
        (TALLOWGATE, "flat"): Confidence.HIGH,
        (TALLOWGATE, "detached"): Confidence.MEDIUM,
    }


def test_a_row_cites_the_sales_the_directory_and_the_lookup(town: Sold):
    for row in price_paid.costs(town):
        assert row.source_ids == (price_paid.SOURCE, LOOKUP, postcodes.SOURCE)


def test_the_rows_are_in_the_order_a_release_keeps_them(town: Sold):
    rows = price_paid.costs(town)
    assert list(rows) == sorted(rows, key=lambda row: (row.area_id, row.tenure, row.segment))


# The evidence


def test_every_figure_rests_on_every_file_of_sales_the_directory_and_the_lookup(town: Sold):
    sources = sorted(receipt.source_id for receipt in town.files)
    assert sources == sorted([*[price_paid.SOURCE] * 3, LOOKUP, postcodes.SOURCE])
    rows = price_paid.evidence(town)
    assert len(rows) == len(price_paid.HOMES) * len(AREAS)
    named = tuple(sorted(receipt.file_id for receipt in town.files))
    assert all(row.inputs == named for row in rows)
    assert all(row.derivation_id == "median_of_sales_by_postcode@1" for row in rows)
    assert town.geography is Geography.POSTCODE
    evidence = Evidence.of("lon-2026-09-24-01", town.files, price_paid.METHODS, rows)
    assert len(evidence.rows) == len(rows)


def test_the_row_of_a_figure_holds_the_median_and_the_count_of_its_sales(town: Sold):
    by_id = {row.fact_id: row for row in price_paid.evidence(town)}
    row = by_id[f"{TALLOWGATE}/cost/buy.flat"]
    assert (row.state, row.value) == (State.PRESENT, 125_500.0)
    assert (row.units_used, row.units_expected, row.weight_covered) == (50, 50, 1.0)


def test_the_method_says_how_few_sales_give_no_figure():
    assert price_paid.MEDIAN_OF_SALES.parameters == {"fewest_sales": FEWEST_SALES}
    assert "fewer than 10 such sales" in price_paid.MEDIAN_OF_SALES.sentence
    assert price_paid.MEDIAN_OF_SALES.code == "burro_pipeline.derive.price_paid"


def test_the_definition_says_the_kind_of_home_the_period_and_what_is_not_counted(town: Sold):
    said = town.of[Segment.FLAT].definition
    assert "a flat or a maisonette" in said
    assert "from 2023-01 to 2025-12" in said
    assert "fewer than 10 sales" in said
    assert "buy-to-let" in said and "of any one size" in said
    for priced in town.of.values():
        assert "{" not in priced.definition


# The period


def test_the_sales_are_those_of_the_years_the_build_was_given(tmp_path: Path, town: Sold):
    assert (town.since, town.until) == ("2023-01", "2025-12")
    two = [pair for pair in files_of() if "pp-2023" not in pair[0].publisher_file]
    found = built(inputs_of(tmp_path, two))
    assert (found.since, found.until) == ("2024-01", "2025-12")
    assert found.counts.by_year == {2024: 36, 2025: 30}


def test_years_that_do_not_follow_one_another_stop_the_build(tmp_path: Path):
    apart = [pair for pair in files_of() if "pp-2024" not in pair[0].publisher_file]
    with pytest.raises(LockError) as refused:
        built(inputs_of(tmp_path, apart))
    assert refused.value.rule == "input_is_as_described"


def test_no_file_of_sales_leaves_the_step_with_no_receipt_to_read(tmp_path: Path):
    with pytest.raises(LockError) as refused:
        built(inputs_of(tmp_path, []))
    assert refused.value.rule == "input_has_one_receipt"


def test_no_directory_leaves_the_step_with_nothing_to_place_a_sale_by(tmp_path: Path):
    with pytest.raises(LockError) as refused:
        built(inputs_of(tmp_path, directory=False))
    assert refused.value.rule == "input_has_one_receipt"


# A file that is not what was described


def test_a_file_of_another_year_than_its_receipt_stops_the_build(tmp_path: Path):
    said = refusal(
        tmp_path, 2024, file_of(2024), period=Period(start="2024-01-01", end="2024-06-30")
    )
    assert "it is not of the year its receipt gives" in said


def test_a_sale_of_another_year_than_its_file_stops_the_build(tmp_path: Path):
    stray = "\n".join(",".join(f'"{cell}"' for cell in line) for line in [line_of(SALES[0], 1)])
    assert SALES[0].year == 2023
    said = refusal(tmp_path, 2024, file_of(2024) + stray.encode() + b"\n")
    assert "a sale is of another year than its file" in said


@pytest.mark.parametrize(
    ("changed", "words"),
    [
        ({"price": 0}, "a price is not a price"),
        ({"day": "02-30"}, "a day is not a day"),
        ({"home": "X"}, "a kind of home is none the file is known to hold"),
        ({"new": "?"}, "a mark of a new home is none the file is known to hold"),
        ({"category": "C"}, "a category is none the file is known to hold"),
    ],
)
def test_a_cell_that_is_not_what_the_file_is_known_to_hold_stops_the_build(
    tmp_path: Path, changed: dict[str, object], words: str
):
    odd = dataclasses.replace(MadeUpSale(250_000, QUAY.postcode), **changed)  # pyright: ignore[reportArgumentType]
    content = file_of(2024, [*SALES, odd])
    assert words in refusal(tmp_path, 2024, content)


def test_a_line_of_another_width_stops_the_build(tmp_path: Path):
    assert "a line has not the columns of the file" in refusal(
        tmp_path, 2024, file_of(2024, width=15)
    )


def test_a_refusal_repeats_nothing_the_file_holds(tmp_path: Path):
    odd = MadeUpSale(250_000, QUAY.postcode, home="X")
    said = refusal(tmp_path, 2024, file_of(2024, [*SALES, odd]))
    assert CANARY not in said and QUAY.postcode not in said and "250000" not in said


# It repeats


def test_the_same_files_give_the_same_figures_in_whatever_order_they_are_read(tmp_path: Path):
    turned = [pair for pair in reversed(files_of(list(reversed(SALES))))]
    again = built(inputs_of(tmp_path, turned))
    first = built(inputs_of(tmp_path / "b"))
    assert price_paid.costs(again) == price_paid.costs(first)
    assert [row.value for row in price_paid.evidence(again)] == [
        row.value for row in price_paid.evidence(first)
    ]
    assert TERRACED in {sale.home for sale in SALES} and DETACHED in {sale.home for sale in SALES}
