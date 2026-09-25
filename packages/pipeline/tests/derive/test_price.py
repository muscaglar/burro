"""What a home sells for, from the publisher's workbook to a figure for each area.

Every file here is made up. The workbook is laid out as the publisher lays out
its own, with its own names for sheets and columns. What it holds is made up:
the three MSOAs of the made-up town of the tests of cells, and one outside
London, each with a price chosen so that a test can say which cell it came from.

    MSOA        area             any kind   detached   semi      terraced   flat
    E02999001   Quillhaven 001    410000    [x]        525000    450000     300000
    E02999002   Quillhaven 002    655000    1200000    [x]       700500     [x]
    E02999003   Tallowgate 001    287500    no row     no row    [x]        250000
    E02999901   outside London    150000    320000     [x]       140000      95000
"""

from collections.abc import Mapping
from pathlib import Path

import pytest
from burro_core.catalogue import CHAINS, FEATURES, TAGS
from burro_core.ids import FeatureId, NativeResolution
from burro_pipeline.cells import spine
from burro_pipeline.derive import price, price_median
from burro_pipeline.derive.measures import MEASURES, says_what_core_says
from burro_pipeline.derive.price import Prices
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry import Registry, RegistryError
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, held, registry
from .noise_support import Cell, Raw
from .price_support import (
    CANARY_PRICE,
    COLUMNS,
    DISTRICTS,
    LAST,
    OUTSIDE,
    PRICES,
    Q1,
    Q2,
    SAID_ON_THE_COVER,
    SOURCE,
    T1,
    THE_YEAR_BEFORE,
    book,
    described,
    inputs_of,
    listed,
    receipt,
    sheet_of,
)

A1, A2, A3 = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
ANY, DETACHED, SEMI, TERRACED, FLAT = (home.key for home in price.HOMES)


def built(folder: Path, content: bytes | None = None, period: Period | None = None) -> Prices:
    """The measure, from a made-up build whose workbook is the one given."""
    inputs = inputs_of(folder, book() if content is None else content, period=period)
    return price.build(inputs, spine.build(inputs))


def refused(folder: Path, content: bytes, period: Period | None = None) -> LockError:
    """The refusal of a workbook that is not what the step was written to read."""
    inputs = inputs_of(folder, content, period=period)
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        price.build(inputs, found)
    assert stopped.value.rule == "input_is_as_described"
    assert stopped.value.subject == receipt(content).file_id
    # A refusal repeats nothing from the file.
    assert CANARY not in str(stopped.value) and str(CANARY_PRICE) not in str(stopped.value)
    return stopped.value


def priced(**changed: Mapping[str, Cell]) -> dict[str, Mapping[str, Cell]]:
    """The prices of the made-up workbook, with those of some sheets changed."""
    return {**PRICES, **{f"1{sheet}": cells for sheet, cells in changed.items()}}


def values(found: Prices, key: str) -> dict[str, float | None]:
    return {area: one.value for area, one in found.of[key].worked.items()}


# The parser


def test_the_median_of_every_msoa_is_read_as_the_publisher_wrote_it(tmp_path: Path):
    sheets = built(tmp_path).workbook.sheets
    assert sheets[ANY].price == {Q1: 410_000, Q2: 655_000, T1: 287_500, OUTSIDE: 150_000}
    assert (sheets[ANY].withheld, sheets[ANY].rows) == (frozenset(), 4)
    assert sheets[DETACHED].price == {Q2: 1_200_000, OUTSIDE: 320_000}
    assert (sheets[DETACHED].withheld, sheets[DETACHED].rows) == (frozenset({Q1}), 3)
    assert sheets[FLAT].price == {Q1: 300_000, T1: 250_000, OUTSIDE: 95_000}
    assert sheets[ANY].district == DISTRICTS


def test_each_kind_of_home_is_read_from_the_sheet_the_contents_give_it():
    assert [(home.sheet, home.a_home) for home in price.HOMES] == [
        ("1a", "a home"),
        ("1b", "a detached house"),
        ("1c", "a semi-detached house"),
        ("1d", "a terraced house"),
        ("1e", "a flat or a maisonette"),
    ]


def test_the_year_that_is_read_is_the_one_the_receipt_gives(tmp_path: Path):
    before = Period(start="2024-04", end="2025-03")
    content = book(year=THE_YEAR_BEFORE, contents_of=listed("March 2025"))
    found = built(tmp_path, content, period=before)
    assert found.workbook.year.column == THE_YEAR_BEFORE
    assert values(found, ANY) == {A1: 410_000.0, A2: 655_000.0, A3: 287_500.0}
    assert found.of[ANY].named.vintage == "2024-04 to 2025-03"


def test_no_other_year_of_a_row_is_read(tmp_path: Path):
    found = built(tmp_path)
    for one in found.workbook.sheets.values():
        assert CANARY_PRICE not in one.price.values()


@pytest.mark.parametrize(
    "period",
    [
        Period(as_at="2026-03"),
        Period(start="2025-04", end="2026-04"),
        Period(start="2025-05", end="2026-03"),
        Period(start="2025-04-01", end="2026-03-31"),
        Period(start="2025", end="2026"),
    ],
)
def test_a_receipt_that_gives_no_year_of_sales_stops_the_step(tmp_path: Path, period: Period):
    assert "does not give a year of sales" in str(refused(tmp_path, book(), period))


def test_a_receipt_of_another_year_than_the_last_of_the_file_stops_the_step(tmp_path: Path):
    """The file holds the year. It is not the file the receipt says it is."""
    before = Period(start="2024-04", end="2025-03")
    stopped = refused(tmp_path, book(), before)
    assert "its contents give another last year than its receipt" in str(stopped)


@pytest.mark.parametrize("missing", ["Local authority code", "MSOA code", LAST])
def test_a_column_that_is_missing_is_named(tmp_path: Path, missing: str):
    columns = [name for name in COLUMNS if name != missing]
    assert f"the column {missing} is missing" in str(refused(tmp_path, book(columns=columns)))


def test_a_sheet_that_is_missing_stops_the_step(tmp_path: Path):
    stopped = refused(tmp_path, book(without=["1e"]))
    assert "it does not hold the one sheet that is read" in str(stopped)


@pytest.mark.parametrize(
    ("sheet", "said"),
    [
        ("1a", described("3a")),
        ("1b", described("2b")),
        ("1e", described("1d").replace("Table 1d", "Table 1e")),
        ("1c", "Table 1c - Mean price paid for semi-detached houses by MSOA"),
        ("1d", CANARY),
    ],
)
def test_contents_that_say_a_sheet_holds_another_thing_stop_the_step(
    tmp_path: Path, sheet: str, said: str
):
    content = book(contents_of=listed(**{sheet: said}))
    assert f"do not say what the sheet {sheet} holds" in str(refused(tmp_path, content))


def test_contents_that_list_a_sheet_twice_stop_the_step(tmp_path: Path):
    content = book(contents_of=[*listed(), ["1a", described("1a")]])
    assert "its contents do not list each sheet once" in str(refused(tmp_path, content))


@pytest.mark.parametrize(
    ("without", "why"),
    [
        ("pounds sterling", "does not say the figures are in pounds"),
        ("fewer than five", "does not say what stands where no figure is given"),
        ("[x]", "does not say what stands where no figure is given"),
    ],
)
def test_a_cover_that_does_not_say_what_a_cell_holds_stops_the_step(
    tmp_path: Path, without: str, why: str
):
    """The unit and the mark are read from the file. A file that says neither is not read."""
    cover = [said.replace(without, CANARY) for said in SAID_ON_THE_COVER[1:]]
    content = book(cover=[SAID_ON_THE_COVER[0], *cover])
    assert why in str(refused(tmp_path, content))


@pytest.mark.parametrize(
    "cell",
    [0, -410_000, 410_000.5, "410000", "x", "[c]", "-", None, CANARY, Raw("n", "<v></v>")],
)
def test_a_cell_that_is_neither_a_price_nor_the_mark_stops_the_step(tmp_path: Path, cell: Cell):
    """Nothing is guessed. A dash, an empty cell and nought are none of them `[x]`."""
    content = book(priced(a={**PRICES["1a"], Q1: cell}))
    assert "a price is not a price" in str(refused(tmp_path, content))


@pytest.mark.parametrize("code", ["E01999001", "e02999001", "E0299900", "E029990011", CANARY])
def test_a_code_that_is_no_code_of_an_msoa_stops_the_step(tmp_path: Path, code: str):
    content = book(priced(a={**PRICES["1a"], code: 500_000}))
    assert "a code is not a code" in str(refused(tmp_path, content))


@pytest.mark.parametrize("code", ["E02999001", "E0900090", "K04000001", None, CANARY])
def test_a_code_that_is_no_code_of_a_district_stops_the_step(tmp_path: Path, code: Cell):
    content = book(districts={**DISTRICTS, Q1: code})
    assert "a code is not a code" in str(refused(tmp_path, content))


def test_an_msoa_that_is_there_twice_stops_the_step(tmp_path: Path):
    table = [*sheet_of("1d", PRICES["1d"]), sheet_of("1d", PRICES["1d"])[3]]
    assert "an MSOA is there twice" in str(refused(tmp_path, book(sheets={"1d": table})))


def test_a_sheet_with_no_row_under_its_header_stops_the_step(tmp_path: Path):
    assert "it holds no row of an MSOA" in str(refused(tmp_path, book(priced(e={}))))


def test_the_sheets_of_new_and_of_existing_homes_are_never_opened(tmp_path: Path):
    """Each is not well formed in the made-up workbook, so a reader that opened one failed."""
    found = built(tmp_path)
    assert {one.home.sheet for one in found.workbook.sheets.values()} == {
        "1a",
        "1b",
        "1c",
        "1d",
        "1e",
    }


# The census the codes follow


def test_the_rows_are_keyed_by_the_msoas_of_the_census_of_2021(tmp_path: Path):
    assert built(tmp_path).geography is Geography.MSOA21


def test_an_msoa_of_the_spine_with_no_row_for_a_home_of_any_kind_stops_the_step(tmp_path: Path):
    """A workbook on the codes of another census lacks the MSOAs that were drawn again."""
    fewer = {code: cell for code, cell in PRICES["1a"].items() if code != T1}
    stopped = refused(tmp_path, book(priced(a=fewer)))
    assert "an MSOA of the census of 2021 has no row" in str(stopped)


def test_an_msoa_in_another_borough_than_the_lookup_gives_stops_the_step(tmp_path: Path):
    stopped = refused(tmp_path, book(districts={**DISTRICTS, Q2: "E09000902"}))
    assert "an MSOA is in another borough than the lookup gives" in str(stopped)


# The figure


def test_an_areas_figure_is_the_publishers_own_for_the_msoa_it_is(tmp_path: Path):
    found = built(tmp_path)
    assert values(found, ANY) == {A1: 410_000.0, A2: 655_000.0, A3: 287_500.0}
    assert values(found, TERRACED) == {A1: 450_000.0, A2: 700_500.0, A3: None}
    for one in found.of[ANY].worked.values():
        assert (one.units_used, one.units_expected, one.weight_covered) == (1, 1, 1.0)
        assert (one.state, one.flags) == (State.PRESENT, ())


def test_a_figure_is_given_as_it_is_written_and_is_not_rounded(tmp_path: Path):
    """The contract rounds a price to 5,000. This is the number a reader finds in the file."""
    found = built(tmp_path, book(priced(a={**PRICES["1a"], Q1: 481_546})))
    assert values(found, ANY)[A1] == 481_546.0


def test_a_figure_the_publisher_withheld_is_not_given_and_is_never_nought(tmp_path: Path):
    found = built(tmp_path)
    assert values(found, DETACHED) == {A1: None, A2: 1_200_000.0, A3: None}
    one = found.of[DETACHED].worked[A1]
    assert (one.value, one.state, one.flags) == (
        None,
        State.SUPPRESSED,
        (Flag.SUPPRESSED_IN_SOURCE,),
    )
    assert (one.units_used, one.units_expected, one.weight_covered) == (0, 1, 0.0)


def test_an_area_with_no_row_on_the_sheet_of_a_kind_is_a_gap_in_the_source(tmp_path: Path):
    one = built(tmp_path).of[SEMI].worked[A3]
    assert (one.value, one.state, one.flags) == (None, State.SOURCE_GAP, ())
    assert (one.units_used, one.units_expected, one.weight_covered) == (0, 1, 0.0)


def test_every_area_has_a_figure_or_a_state_for_every_kind_of_home(tmp_path: Path):
    found = built(tmp_path)
    assert list(found.of) == [ANY, DETACHED, SEMI, TERRACED, FLAT]
    for one in found.of.values():
        assert set(one.worked) == {A1, A2, A3}


def test_an_msoa_outside_london_is_part_of_no_figure(tmp_path: Path):
    dearer = priced(a={**PRICES["1a"], OUTSIDE: 9_000_000})
    found = built(tmp_path / "dearer", book(dearer))
    assert found.of[ANY].worked == built(tmp_path / "as").of[ANY].worked


def test_the_order_of_the_rows_changes_nothing(tmp_path: Path):
    turned = {sheet: dict(reversed(list(cells.items()))) for sheet, cells in PRICES.items()}
    found = built(tmp_path / "turned", book(turned))
    assert {key: one.worked for key, one in found.of.items()} == {
        key: one.worked for key, one in built(tmp_path / "as").of.items()
    }


# The evidence


def test_every_area_has_a_row_of_evidence_that_names_the_two_files(tmp_path: Path):
    found = built(tmp_path)
    assert [row.fact_id for row in found.of[ANY].rows] == [
        f"{area}/feature/price_median" for area in (A1, A2, A3)
    ]
    assert {one.source_id for one in found.files} == {
        SOURCE,
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
    }
    for row, value in zip(found.of[ANY].rows, (410_000.0, 655_000.0, 287_500.0), strict=True):
        assert row.inputs == tuple(sorted(one.file_id for one in found.files))
        assert row.derivation_id == "area_row_value@1"
        assert (row.units_used, row.units_expected, row.weight_covered) == (1, 1, 1.0)
        assert (row.state, row.flags, row.value) == (State.PRESENT, (), value)
        # The span of the two files: from the month of the lookup to the end of the year.
        assert row.data_period == Period(start="2021-12-01", end="2026-03-31")
        assert row.retrieved_on == "2026-09-23"


def test_a_figure_that_is_missing_has_a_row_too_and_the_row_says_why(tmp_path: Path):
    rows = {row.area_id: row for row in built(tmp_path).of[DETACHED].rows}
    assert (rows[A1].state, rows[A1].value) == (State.SUPPRESSED, None)
    assert rows[A1].flags == (Flag.SUPPRESSED_IN_SOURCE,)
    assert (rows[A3].state, rows[A3].value, rows[A3].flags) == (State.SOURCE_GAP, None, ())
    assert all(row.inputs and row.derivation_id for row in rows.values())


def test_the_rows_stand_as_the_evidence_of_a_release(tmp_path: Path):
    found = built(tmp_path)
    rows = [row for one in found.of.values() for row in one.rows]
    evidence = Evidence.of("lon-2026-10-02-01", found.files, price.METHODS, rows)
    assert len(evidence.rows) == 15
    # The row of a kind of home is under the id of its cost, and of any kind under its own.
    assert evidence.row(f"{A2}/feature/price_median") is not None
    row = evidence.row(f"{A2}/cost/buy.terraced")
    assert row is not None and row.value == 700_500.0
    assert evidence.sources_of(row) == frozenset(found.of[TERRACED].named.source_ids)
    assert evidence.method(row.derivation_id or "") == price.AREA_ROW_VALUE


def test_the_method_is_the_publishers_own_figure_and_is_marked_as_measured():
    method = price.AREA_ROW_VALUE
    assert (method.derivation_id, method.kind) == ("area_row_value@1", Kind.MEASURED)
    assert method.code == "burro_pipeline.derive.price"
    assert "publisher's own figure for the area" in method.sentence
    assert list(price.METHODS) == [method]


# The name, the unit and the period


def test_the_name_says_what_was_paid_and_for_which_kind_of_home(tmp_path: Path):
    found = built(tmp_path)
    assert {key: one.named.label for key, one in found.of.items()} == {
        "price_median": "Median price paid for a home",
        "price_median_detached": "Median price paid for a detached house",
        "price_median_semi_detached": "Median price paid for a semi-detached house",
        "price_median_terraced": "Median price paid for a terraced house",
        "price_median_flat": "Median price paid for a flat or a maisonette",
    }


def test_the_unit_is_pounds_and_more_is_dearer(tmp_path: Path):
    named = built(tmp_path).of[ANY].named
    assert (named.unit, named.higher, named.lower) == ("£", "dearer", "cheaper")


def test_the_period_and_the_sources_are_the_ones_the_receipts_give(tmp_path: Path):
    named = built(tmp_path).of[ANY].named
    assert named.vintage == "2025-04 to 2026-03"
    assert "year ending March 2026" in named.definition
    assert named.source_ids == (
        "ons-median-house-prices-msoa",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
    )


def test_a_figure_of_a_kind_is_the_middle_of_a_cost_of_the_contract(tmp_path: Path):
    """The contract holds a price by kind of home. It has no place for a home of any kind."""
    found = built(tmp_path)
    assert {key: one.named.cost_key for key, one in found.of.items()} == {
        "price_median": None,
        "price_median_detached": "buy.detached",
        "price_median_semi_detached": "buy.semi_detached",
        "price_median_terraced": "buy.terraced",
        "price_median_flat": "buy.flat",
    }


def test_the_definition_is_one_sentence_that_states_every_number_it_rests_on(tmp_path: Path):
    """The record of a method refuses a sentence that leaves a parameter out."""
    for key, one in built(tmp_path).of.items():
        stated = Method(
            derivation_id=f"{key}@1",
            sentence=one.named.definition,
            kind=Kind.MEASURED,
            parameters={"fewest_sales": price.FEWEST_SALES, "year": 2026, "month": "March"},
            code="burro_pipeline.derive.price",
        )
        assert stated.sentence == one.named.definition
        for said in ("median", "Office for National Statistics", "HM Land Registry", "pounds"):
            assert said in one.named.definition
        assert "is not the value of a home that was not sold" in one.named.definition
        assert one.home.a_home in one.named.definition


def test_what_it_cannot_see_is_said_in_a_few_plain_sentences():
    assert len(price.CANNOT_SEE) == 2
    for said in price.CANNOT_SEE:
        assert said.endswith(".") and "!" not in said and len(said) < 250
    together = " ".join(price.CANNOT_SEE)
    assert together.count(". ") + 1 == 4
    for word in ("sold", "5 sales", "not sold", "large", "small", "asking price", "rent"):
        assert word in together


# The gate, the receipt and the store


def with_uses(*uses: Use) -> Registry:
    """The repository's registry, with the workbook registered for other uses."""
    sources = [
        source.model_copy(update={"uses": uses}) if source.id == SOURCE else source
        for source in registry()
    ]
    return Registry(tuple(sources))


def test_the_registry_holds_the_workbook_for_a_cost_and_for_nothing_wider():
    """It may be ranked on and shown, since 2026-09-24. It names no place and routes nothing."""
    assert price.USE is Use.SCORING
    for allowed in (Use.SCORING, Use.DISPLAY, Use.VALIDATION_ONLY):
        registry().require(SOURCE, allowed)
    for wider in (Use.GAZETTEER, Use.ROUTING, Use.DESTINATION_SEARCH, Use.PROFILE_TEXT):
        with pytest.raises(RegistryError):
            registry().require(SOURCE, wider)


def test_the_price_of_each_kind_of_home_is_a_cost_and_of_a_home_of_any_kind_a_measure():
    """Decided on 2026-09-24: a person may ask for homes that sell for more than the middle.

    So the median for a home of any kind is a measure of a build. The median of each
    kind of home is a cost, which a budget is held against, and is no measure.
    """
    of_the_workbook = [measure for measure in MEASURES if measure.source == price.SOURCE]
    # How far the median has risen is read from the same sheet, over five years and ten.
    assert [measure.feature for measure in of_the_workbook] == [
        FeatureId.PRICE_MEDIAN,
        FeatureId.PRICE_RISE_10Y,
        FeatureId.PRICE_RISE_5Y,
    ]
    measure = of_the_workbook[0]
    assert measure.methods == price.METHODS and not measure.held_back and not measure.waits_on
    assert not measure.in_parts and not measure.in_squares
    assert price_median.FEATURE.value == price.ALL.key and price.ALL.cost_key is None


def test_core_holds_one_feature_for_a_price_and_no_vibe_rests_on_it():
    known = {feature.value for feature in FeatureId}
    assert known & {home.key for home in price.HOMES} == {"price_median"}
    # The name of one chain of coffee holds the letters of a cost, and is no cost. Beside the
    # price core holds how far it has risen, which is no price and no cost.
    of_a_chain = {feature.value for feature in CHAINS}
    assert sorted(f for f in known - of_a_chain if "price" in f or "cost" in f) == [
        "price_median",
        "price_rise_10y",
        "price_rise_5y",
    ]
    in_a_recipe = {term.feature_id for tag in TAGS.values() for term in tag.terms}
    assert FeatureId.PRICE_MEDIAN not in in_a_recipe
    assert FEATURES[FeatureId.PRICE_MEDIAN].in_likeness is False


def test_the_measure_is_the_publishers_own_figure_for_a_home_of_any_kind(tmp_path: Path):
    inputs = inputs_of(tmp_path, book())
    found = spine.build(inputs)
    sold, prices = price_median.build(inputs, found), price.build(inputs, found)
    of_any_kind = prices.of[price.ALL.key]
    assert sold.worked == of_any_kind.worked and sold.rows == of_any_kind.rows
    assert sold.files == prices.files and sold.geography is prices.geography
    assert {row.fact_id.rsplit("/", 2)[1:] == ["feature", "price_median"] for row in sold.rows} == {
        True
    }
    metric, core = sold.metric, FEATURES[FeatureId.PRICE_MEDIAN]
    assert says_what_core_says(metric)
    assert (
        (metric.label, metric.unit)
        == (core.label, core.unit)
        == (
            "Median price paid for a home",
            "£",
        )
    )
    assert (metric.native_resolution, metric.rankable) == (NativeResolution.MSOA, True)
    assert metric.vintage == of_any_kind.named.vintage
    assert "median price paid for a home sold in the area" in metric.definition
    # What stands beside the figure says what it is of, and that it is of no person.
    said = " ".join(price_median.CANNOT_SEE)
    assert "of every kind and size" in said and "as few as 5 sales" in said
    assert "nothing of who lives in a place, or of what they earn" in said


def test_the_gate_is_asked_before_the_workbook_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, book(), using=with_uses(Use.PROTOTYPING_ONLY))
    found = spine.build(inputs)
    before = inputs.opened
    with pytest.raises(LockError) as stopped:
        price.build(inputs, found)
    assert (stopped.value.rule, stopped.value.subject) == ("gate_refuses", SOURCE)
    assert inputs.opened == before
    assert not any((tmp_path / "work").rglob("*.xlsx"))


def test_a_workbook_with_no_receipt_is_not_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, None)
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        price.build(inputs, found)
    assert (stopped.value.rule, stopped.value.subject) == ("input_has_one_receipt", SOURCE)
    assert not any((tmp_path / "work").rglob("*.xlsx"))


def test_another_file_of_the_publisher_is_not_taken_for_the_workbook(tmp_path: Path):
    inputs = inputs_of(tmp_path, book(), name="lowerquartilepricepaidformsoa.xlsx")
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        price.build(inputs, found)
    assert stopped.value.rule == "input_has_one_receipt"


def test_a_spine_of_another_build_is_refused(tmp_path: Path):
    """A row names the lookup of the spine, so it must be a file this build opened."""
    found = spine.build(inputs_of(tmp_path / "other", book()))
    with pytest.raises(ValueError, match="the spine is made from files of this build"):
        price.build(inputs_of(tmp_path / "this", book()), found)


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path, book())
    before = held(tmp_path / "store")
    price.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before
