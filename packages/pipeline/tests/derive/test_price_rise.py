"""How far what homes sold for has risen, from a made-up workbook laid out as the publisher's.

Every figure here is made up: the workbook of `price_support.py`, whose sheet
of homes of any kind holds the last year and two earlier ones.

    MSOA        area             year ending March 2026   March 2021   March 2016
    E02999001   Quillhaven 001    410000                  400000       205000
    E02999002   Quillhaven 002    655000                  [x]          524000
    E02999003   Tallowgate 001    287500                  250000       300000

    over five years   102.5, no figure, 115.0
    over ten years    200.0, 125.0, 95.8
"""

from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, TAGS
from burro_core.ids import Describes, FeatureId, FeatureKind, NativeResolution, Polarity, Tenure
from burro_core.spec import default_spec
from burro_pipeline.cells import spine
from burro_pipeline.derive import measures, price, price_rise
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.price_rise import Risen
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence

from .price_support import (
    CANARY_PRICE,
    COLUMNS,
    EARLIER,
    FIVE_BEFORE,
    PRICES,
    Q1,
    SAID_ON_THE_COVER,
    SOURCE,
    TEN_BEFORE,
    book,
    inputs_of,
)

A1, A2, A3 = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
LOOKUP = "ons-oa21-lsoa21-msoa21-lad22-lookup"
RISES = (FeatureId.PRICE_RISE_5Y, FeatureId.PRICE_RISE_10Y)


def built(folder: Path, years: int, content: bytes | None = None) -> Risen:
    inputs = inputs_of(folder, book() if content is None else content)
    return price_rise.build(inputs, spine.build(inputs), years)


def refusal(folder: Path, content: bytes) -> str:
    inputs = inputs_of(folder, content)
    with pytest.raises(LockError) as refused:
        price_rise.build(inputs, spine.build(inputs), 5)
    assert refused.value.rule == "input_is_as_described"
    assert str(CANARY_PRICE) not in str(refused.value)
    return str(refused.value)


# What the measure is


@pytest.mark.parametrize("feature_id", RISES)
def test_a_rise_is_a_figure_of_what_was_paid_for_homes_that_a_person_may_weigh(
    feature_id: FeatureId,
):
    feature = FEATURES[feature_id]
    assert feature.label.startswith("Median price paid for a home, for each £100 of the median ")
    assert feature.short_label.startswith("Price rise over ")
    assert (feature.unit, feature.polarity) == ("£", Polarity.EITHER)
    assert (feature.higher, feature.lower) == ("a steeper rise", "a smaller rise")
    assert (feature.kind, feature.describes) == (FeatureKind.TASTE, Describes.BUILDINGS)
    assert feature.native_resolution is NativeResolution.MSOA
    # No vibe rests on it, no likeness is counted on it, and nothing weighs it by default.
    assert feature.in_likeness is False
    assert feature_id not in {term.feature_id for tag in TAGS.values() for term in tag.terms}
    for tenure in Tenure:
        assert feature_id not in {w.feature_id for w in default_spec(tenure).weights}


def test_what_stands_beside_a_rise_says_that_it_promises_nothing():
    assert price_rise.CANNOT_SEE[0].startswith(
        "A rise is of prices that were paid, and promises nothing"
    )
    assert "promises nothing of what a home will sell for" in price_rise.DEFINITION
    for line in price_rise.CANNOT_SEE:
        said = line.lower()
        # No word of where a place is heading, and none of who is moving to it but to say so.
        assert "up and coming" not in said and "gentrif" not in said and "invest" not in said


def test_both_are_on_the_list_of_a_build_and_read_the_workbook_of_prices():
    listed = {measure.feature: measure for measure in measures.MEASURES}
    for years, feature_id in price_rise.OVER.items():
        measure = listed[feature_id]
        assert measure.source == price.SOURCE == SOURCE
        assert measure.reads is price_rise.is_a_file
        assert measure.methods == (price_rise.risen_over(years),)
        assert not measure.waits_on and not measure.held_back
        assert not measure.in_parts and not measure.in_squares


def test_the_span_of_years_is_part_of_the_name_of_the_method():
    five, ten = price_rise.risen_over(5), price_rise.risen_over(10)
    assert (five.derivation_id, ten.derivation_id) == ("area_row_rise_5y@1", "area_row_rise_10y@1")
    assert five.parameters == {"years": 5, "for_each": 100}
    assert "5 years before" in five.sentence and "10 years before" in ten.sentence
    with pytest.raises(ValueError, match="over five years, or over ten"):
        price_rise.risen_over(3)


# The figure


def test_a_rise_is_the_last_median_for_each_hundred_pounds_of_the_earlier_one(tmp_path: Path):
    assert built(tmp_path, 5).worked == {
        A1: Worked(102.5, 1, 1, 1.0, State.PRESENT),
        # The publisher withheld the figure of the earlier year.
        A2: Worked(None, 0, 1, 0.0, State.SUPPRESSED, (Flag.SUPPRESSED_IN_SOURCE,)),
        A3: Worked(115.0, 1, 1, 1.0, State.PRESENT),
    }
    assert built(tmp_path / "ten", 10).worked == {
        A1: Worked(200.0, 1, 1, 1.0, State.PRESENT),
        A2: Worked(125.0, 1, 1, 1.0, State.PRESENT),
        # What homes sold for fell: the figure is under 100, and is never below nought.
        A3: Worked(95.8, 1, 1, 1.0, State.PRESENT),
    }


def test_the_years_that_are_read_are_five_and_ten_before_the_last(tmp_path: Path):
    found = built(tmp_path, 5).medians
    assert found.columns == {
        0: "Year ending Mar 2026",
        5: FIVE_BEFORE,
        10: TEN_BEFORE,
    }
    assert found.paid[0][Q1] == 410_000
    assert found.paid[5][Q1] == EARLIER[FIVE_BEFORE][Q1]
    assert found.paid[10][Q1] == EARLIER[TEN_BEFORE][Q1]
    # No other year is read: each holds a canary, which is in no figure.
    every = [paid for of_year in found.paid.values() for paid in of_year.values()]
    assert CANARY_PRICE not in every


def test_a_figure_withheld_in_the_last_year_gives_no_rise_either(tmp_path: Path):
    withheld = {**PRICES, "1a": {**PRICES["1a"], Q1: "[x]"}}
    # The sheet of all homes must hold a row for every MSOA, and a row may hold no figure.
    found = built(tmp_path, 10, book(withheld))
    assert (found.worked[A1].value, found.worked[A1].state) == (None, State.SUPPRESSED)
    assert found.worked[A2].value == 125.0


def test_a_rise_is_given_to_one_decimal_place_with_a_half_taken_upward(tmp_path: Path):
    # 410,000 for each 100 of 320,000 is 128.125, which is given as 128.1.
    earlier = {**EARLIER, FIVE_BEFORE: {**EARLIER[FIVE_BEFORE], Q1: 320_000}}
    assert built(tmp_path, 5, book(earlier=earlier)).worked[A1].value == 128.1
    # 250,100 for each 100 of 200,000 is 125.05, which is given as 125.1 and never as 125.0.
    earlier = {**EARLIER, FIVE_BEFORE: {**EARLIER[FIVE_BEFORE], Q1: 200_000}}
    paid = {**PRICES, "1a": {**PRICES["1a"], Q1: 250_100}}
    assert built(tmp_path / "b", 5, book(paid, earlier=earlier)).worked[A1].value == 125.1


# The workbook


def test_a_year_the_sheet_does_not_hold_stops_the_build(tmp_path: Path):
    without = [name for name in COLUMNS if name != FIVE_BEFORE]
    assert "the column Year ending Mar 2021 is missing" in refusal(tmp_path, book(columns=without))


@pytest.mark.parametrize("cell", [0, -1, 250_000.5, "n/a"])
def test_a_cell_of_an_earlier_year_that_is_no_price_stops_the_build(tmp_path: Path, cell: object):
    earlier = {**EARLIER, TEN_BEFORE: {**EARLIER[TEN_BEFORE], Q1: cell}}
    assert "a price is not a price" in refusal(tmp_path, book(earlier=earlier))  # pyright: ignore[reportArgumentType]


def test_the_cover_and_the_contents_are_held_as_the_prices_hold_them(tmp_path: Path):
    said = refusal(tmp_path, book(cover=(SAID_ON_THE_COVER[0], "Made up for a test.")))
    assert "its cover does not say the figures are in pounds" in said


# The evidence and the row of the catalogue


@pytest.mark.parametrize("years", [5, 10])
def test_every_figure_rests_on_the_workbook_and_the_lookup_and_holds_its_value(
    tmp_path: Path, years: int
):
    found = built(tmp_path, years)
    assert sorted(receipt.source_id for receipt in found.files) == sorted([LOOKUP, SOURCE])
    assert found.geography is Geography.MSOA21
    key = price_rise.OVER[years].value
    assert {row.fact_id for row in found.rows} == {f"{area}/feature/{key}" for area in (A1, A2, A3)}
    for row in found.rows:
        assert row.derivation_id == f"area_row_rise_{years}y@1"
        assert row.value == found.worked[row.area_id].value
    evidence = Evidence.of(
        "lon-2026-09-24-01", found.files, (price_rise.risen_over(years),), found.rows
    )
    assert len(evidence.rows) == 3


@pytest.mark.parametrize(
    ("years", "start", "in_words"), [(5, "2020-04", "five"), (10, "2015-04", "ten")]
)
def test_the_row_of_the_catalogue_says_both_years_and_what_core_says(
    tmp_path: Path, years: int, start: str, in_words: str
):
    metric = built(tmp_path, years).metric
    assert says_what_core_says(metric)
    assert metric.feature_id is price_rise.OVER[years]
    assert metric.vintage == f"{start} to 2026-03"
    assert "in the year ending March 2026" in metric.definition
    assert f"in the year ending March {2026 - years}" in metric.definition
    assert f"which was {in_words} years before" in metric.definition
    assert "{" not in metric.definition
