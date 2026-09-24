"""A census table by MSOA, from the publisher's zip to a share for each area.

Every file here is made up. The tables have the publisher's own categories, in
the order its pages give them, and are laid out as the zip of accommodation
type is, which a build reads: a file for each geography, the columns `date`,
`geography` and `geography code`, and a column for each category. What they
hold is made up. `census_support.py` draws the town and its counts.

The step was written before either table was fetched. So these tests hold the
step to every way a column may be named, the way each fetched file names its
own among them, and to a refusal in fixed words where the file is not as it
was taken to be.
"""

import re
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

import pytest
from burro_core.ids import FeatureId, Polarity
from burro_pipeline.derive import (
    census_msoa,
    households_dependent_children,
    households_one_person,
    measures,
    residents_aged_20_34,
    residents_aged_65_over,
)
from burro_pipeline.derive.census_msoa import AGE, HOUSEHOLDS, Category, Of, Table
from burro_pipeline.derive.methods import AREA_ROW_RATIO, Worked
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.registry import Registry, Source, Status
from burro_pipeline.registry.model import SCORED_TABLES, Use

from ..cells.support import CANARY, REPOSITORY, held, registry
from . import census_support as made_up
from .census_support import (
    AGES,
    HOMES,
    IN_WALES,
    MSOA_ONE,
    MSOA_THREE,
    MSOA_TWO,
    NEVER,
    ONE,
    OUTSIDE,
    THREE,
    TWO,
    built,
    inputs_with,
    refused,
    spine_of,
    table_csv,
    zipped,
)


class Measure(Protocol):
    """What the module of each measure holds."""

    @property
    def KEY(self) -> str: ...
    @property
    def SOURCE(self) -> str: ...
    @property
    def METHODS(self) -> tuple[Method, ...]: ...
    @property
    def MEASURE(self) -> Of: ...
    def core_holds_it(self) -> bool: ...


MODULES: tuple[Measure, ...] = (
    residents_aged_20_34,
    residents_aged_65_over,
    households_dependent_children,
    households_one_person,
)
MEASURES: tuple[Of, ...] = tuple(module.MEASURE for module in MODULES)
YOUNG, OLD = residents_aged_20_34.MEASURE, residents_aged_65_over.MEASURE
CHILDREN, ALONE = households_dependent_children.MEASURE, households_one_person.MEASURE
# A band that no measure counts. A made-up row holds in it everyone who is in no other band.
MIDDLE = "Aged 35 to 39 years"
# Words for anything about residents that was not decided on. None may stand in a name.
NOT_DECIDED = re.compile(
    r"ethnic|religio|faith|born|birth|language|disab|health|income|depriv|sexual|gender|"
    r"\bsex\b|married|marriage|civil partner|cohabit|lone parent|single parent|student|tenure|"
    r"renter|owner|migra|nationalit|passport|class\b|poor|rich|wealth|qualification|employ",
    re.IGNORECASE,
)


def value_of(worked: Worked) -> float:
    assert worked.value is not None
    return worked.value


# What may be read


def test_two_tables_may_be_read_and_they_are_the_two_that_may_feed_a_score():
    assert set(census_msoa.TABLES) == SCORED_TABLES == {"TS003", "TS007A"}
    assert (AGE.counted, HOUSEHOLDS.counted) == ("usual residents", "households")


@pytest.mark.parametrize("code", ["TS004", "TS021", "TS030", "TS007", "TS038", "TS077", "TS044"])
def test_the_step_cannot_be_pointed_at_any_other_table(code: str):
    with pytest.raises(ValueError, match="no table that may feed a score"):
        Table(code, "Made up", "usual residents", Category("total", ("Total",)), (), ())


def test_each_table_is_told_from_every_other_by_the_name_of_its_zip():
    assert AGE.is_the_table("census2021-ts007a.zip")
    assert HOUSEHOLDS.is_the_table("census2021-ts003.zip")
    for other in ("census2021-ts007.zip", "census2021-ts003-extra.zip", "census2021-ts021.zip"):
        assert not AGE.is_the_table(other) and not HOUSEHOLDS.is_the_table(other)
    assert (AGE.member, HOUSEHOLDS.member) == ("-ts007a-msoa.csv", "-ts003-msoa.csv")


def test_the_categories_that_are_read_are_the_publishers_own():
    assert [category.name for category in AGE.categories] == list(made_up.BANDS)
    assert len(AGE.categories) == 18 and len(made_up.KINDS) == 21
    read = {category.name for category in HOUSEHOLDS.categories}
    assert read == {
        made_up.ONE_PERSON,
        made_up.ONE_FAMILY,
        made_up.OTHER_KINDS,
        *made_up.WITH_CHILDREN,
    }


def test_no_column_of_households_is_read_but_the_seven_a_measure_or_the_total_needs():
    """The rest say how a couple is joined, and how old a person who lives alone is."""
    never_read = set(made_up.KINDS) - {category.name for category in HOUSEHOLDS.categories}
    assert len(never_read) == 14
    for name in never_read:
        for category in HOUSEHOLDS.categories:
            spelt = {census_msoa.plain(one, HOUSEHOLDS.variable) for one in category.spelt}
            assert census_msoa.plain(name, HOUSEHOLDS.variable) not in spelt


# The reading


@pytest.mark.parametrize("of", MEASURES, ids=[of.key for of in MEASURES])
def test_a_table_is_read_by_msoa_and_every_other_file_of_the_zip_is_left_alone(
    tmp_path: Path, of: Of
):
    counts = built(tmp_path, of).counts
    assert set(counts.of_msoa) == {MSOA_ONE, MSOA_TWO, MSOA_THREE, OUTSIDE, IN_WALES}
    assert counts.rows == 5 and counts.table is of.table


def test_the_counts_of_an_msoa_are_the_cells_of_its_row(tmp_path: Path):
    ages = built(tmp_path, YOUNG).counts.of_msoa[MSOA_ONE]
    assert (ages["total"], ages["aged_20_24"], ages["aged_25_29"], ages["aged_30_34"]) == (
        1000,
        100,
        150,
        50,
    )
    homes = built(tmp_path / "homes", ALONE).counts.of_msoa[MSOA_TWO]
    assert (homes["total"], homes["one_person"]) == (1000, 555)
    assert NEVER not in homes.values() and NEVER not in ages.values()


@pytest.mark.parametrize(
    "named",
    [
        made_up.as_the_zip_of_homes,
        made_up.with_measures,
        made_up.with_no_hyphen,
        made_up.in_capitals,
        made_up.bare,
        made_up.as_the_files_write_it,
    ],
)
@pytest.mark.parametrize("of", MEASURES, ids=[of.key for of in MEASURES])
def test_a_column_is_found_by_the_name_of_its_category_however_the_file_writes_it(
    tmp_path: Path, of: Of, named: Callable[[Table, str], str]
):
    plain = built(tmp_path / "plain", of).worked
    assert built(tmp_path / "other", of, table_csv(of.table, named=named)).worked == plain


@pytest.mark.parametrize("of", MEASURES, ids=[of.key for of in MEASURES])
def test_a_table_written_as_the_fetched_file_is_written_gives_the_same_figures(
    tmp_path: Path, of: Of
):
    """The table of households as it was fetched puts names, dates and codes between quotes."""
    plain = table_csv(of.table, named=made_up.as_the_files_write_it)
    written = made_up.as_the_files_are_written(of.table, plain)
    assert (written != plain) is (of.table is HOUSEHOLDS)
    assert built(tmp_path / "written", of, written).worked == built(tmp_path, of).worked


def test_the_first_category_with_children_is_read_with_the_word_with_or_without_it(
    tmp_path: Path,
):
    """The page writes three of the four with "With", and the first with none."""

    def every_one_with(table: Table, category: str) -> str:
        return f"{table.variable}: {category}".replace(": Dependent", ": With dependent")

    def none_with(table: Table, category: str) -> str:
        return f"{table.variable}: {category}".replace(": With dependent", ": Dependent")

    plain = built(tmp_path / "plain", CHILDREN).worked
    for number, named in enumerate((every_one_with, none_with)):
        table = table_csv(HOUSEHOLDS, named=named)
        assert built(tmp_path / str(number), CHILDREN, table).worked == plain


def test_the_order_of_the_columns_and_of_the_rows_changes_nothing(tmp_path: Path):
    turned = dict(reversed(list(AGES.items())))
    first = ("geography code", "geography", "date")
    table = table_csv(AGE, turned, first=first)
    assert built(tmp_path / "turned", YOUNG, table).worked == built(tmp_path, YOUNG).worked


def test_a_column_that_no_measure_names_is_never_read(tmp_path: Path):
    also = ("Age: Aged 100 years and over", "Made-up column", CANARY)
    table = table_csv(AGE, also=also)
    assert built(tmp_path / "also", YOUNG, table).worked == built(tmp_path, YOUNG).worked


# What stops the step


@pytest.mark.parametrize(
    ("of", "left_out", "key"),
    [
        (YOUNG, "Total", "total"),
        (YOUNG, "Aged 25 to 29 years", "aged_25_29"),
        (OLD, "Aged 85 years and over", "aged_85_over"),
        # A band that no measure counts is still read: the bands are held to the total.
        (YOUNG, "Aged 4 years and under", "aged_0_4"),
        (ALONE, made_up.ONE_PERSON, "one_person"),
        (ALONE, made_up.ONE_FAMILY, "one_family"),
        (CHILDREN, made_up.WITH_CHILDREN[0], "couple_married_children"),
        (CHILDREN, made_up.WITH_CHILDREN[2], "lone_parent_children"),
        (CHILDREN, "Total: All households", "total"),
    ],
)
def test_a_category_with_no_column_stops_the_step_and_is_named_by_the_steps_own_word(
    tmp_path: Path, of: Of, left_out: str, key: str
):
    stopped = refused(tmp_path, of, table_csv(of.table, left_out=[left_out]))
    assert f"the column of {key} is missing" in str(stopped)


@pytest.mark.parametrize("missing", ["date", "geography code"])
def test_a_table_with_no_column_of_codes_or_of_the_year_stops_the_step(
    tmp_path: Path, missing: str
):
    first = tuple(name for name in made_up.FIRST if name != missing)
    stopped = refused(tmp_path, YOUNG, table_csv(AGE, first=first))
    assert f"the column {missing} is missing" in str(stopped)


def test_two_columns_that_are_taken_for_one_category_stop_the_step(tmp_path: Path):
    stopped = refused(tmp_path, YOUNG, table_csv(AGE, also=["AGE: TOTAL; measures: Value"]))
    assert "two columns are taken for total" in str(stopped)


@pytest.mark.parametrize("cell", ["", "-", "c", "[x]", "12.5", "1,000", "-3", "١٢", CANARY])
def test_a_cell_that_is_no_whole_number_stops_the_step_and_is_never_nought(
    tmp_path: Path, cell: str
):
    """No page says how a count is withheld. So nothing is read into a cell that is no count."""
    cells = {(MSOA_TWO, "Aged 25 to 29 years"): cell}
    stopped = refused(tmp_path, YOUNG, table_csv(AGE, cells=cells))
    assert "a count is not a count" in str(stopped)


def test_a_cell_outside_london_is_held_as_one_inside_it_is(tmp_path: Path):
    stopped = refused(tmp_path, YOUNG, table_csv(AGE, cells={(IN_WALES, "Total"): "-"}))
    assert "a count is not a count" in str(stopped)


@pytest.mark.parametrize("code", ["E01999001", "E09000901", "E0299900", "e02999001", "K04000001"])
def test_a_row_whose_code_is_not_an_msoas_stops_the_step(tmp_path: Path, code: str):
    stopped = refused(tmp_path, YOUNG, table_csv(AGE, {**AGES, code: AGES[OUTSIDE]}))
    assert "a code is not the code of an MSOA" in str(stopped)


def test_an_msoa_that_is_there_twice_stops_the_step(tmp_path: Path):
    stopped = refused(tmp_path, YOUNG, table_csv(AGE, twice=[MSOA_TWO]))
    assert "an MSOA is there twice" in str(stopped)


def test_an_area_with_no_row_stops_the_step_and_is_never_a_gap(tmp_path: Path):
    without = {code: row for code, row in AGES.items() if code != MSOA_TWO}
    stopped = refused(tmp_path, YOUNG, table_csv(AGE, without))
    assert "an MSOA of the census of 2021 has no row" in str(stopped)


def test_a_table_with_no_row_stops_the_step(tmp_path: Path):
    assert "it holds no row of an MSOA" in str(refused(tmp_path, YOUNG, table_csv(AGE, {})))


@pytest.mark.parametrize("year", ["2011", "2022", "", "21 March 2021"])
def test_a_row_of_another_year_stops_the_step(tmp_path: Path, year: str):
    stopped = refused(tmp_path, YOUNG, table_csv(AGE, year=year))
    assert "a row is not of the year of the census" in str(stopped)


@pytest.mark.parametrize("as_at", ["2021", "2021-03", "2011-03-27", "2021-03-20"])
def test_a_receipt_that_is_not_of_census_day_stops_the_step(tmp_path: Path, as_at: str):
    stopped = refused(tmp_path, YOUNG, table_csv(AGE), as_at=as_at)
    assert "its receipt is not of the day of the census" in str(stopped)


def test_a_table_that_was_read_before_is_still_held_to_its_receipt(tmp_path: Path):
    """A file is read once, whichever measure asks. Its receipt is asked about every time."""
    content = {"TS007A": zipped(AGE, table_csv(AGE))}
    first = inputs_with(tmp_path / "first", content)
    assert census_msoa.build(YOUNG, first, spine_of(first)).worked[ONE].value == 30.0
    # The same bytes, under a receipt that says they are of the census before.
    second = inputs_with(tmp_path / "second", content, as_at="2011-03-27")
    found = spine_of(second)
    for of in (YOUNG, OLD):
        with pytest.raises(LockError) as stopped:
            census_msoa.build(of, second, found)
        assert "its receipt is not of the day of the census" in str(stopped.value)


def test_a_zip_with_no_table_by_msoa_stops_the_step(tmp_path: Path):
    inputs = inputs_with(
        tmp_path, {"TS007A": zipped(AGE, table_csv(AGE), member="census2021-ts007a-ward.csv")}
    )
    with pytest.raises(LockError) as stopped:
        census_msoa.build(YOUNG, inputs, spine_of(inputs))
    assert stopped.value.rule == "input_is_as_described"
    assert "it does not hold the one file that is read" in str(stopped.value)


# A table is held to itself


@pytest.mark.parametrize("moved", [-20, -1, 0, 1, 20])
def test_the_bands_of_a_row_come_to_its_total_give_or_take_2_in_100(tmp_path: Path, moved: int):
    """The statistics office makes small changes to counts. A sum of 18 moves a little."""
    row = {**AGES[MSOA_ONE], MIDDLE: AGES[MSOA_ONE][MIDDLE] + moved}
    made = built(tmp_path, YOUNG, table_csv(AGE, {**AGES, MSOA_ONE: row}))
    assert made.worked[ONE].value == 30.0
    # How far the furthest row stands from its total is kept, so that a test can hold it.
    assert made.counts.furthest_from_its_total == abs(moved)


@pytest.mark.parametrize("moved", [-21, 21, 500])
def test_bands_that_do_not_come_to_the_total_stop_the_step(tmp_path: Path, moved: int):
    """A column taken for the wrong category moves the sum far."""
    row = {**AGES[MSOA_ONE], MIDDLE: AGES[MSOA_ONE][MIDDLE] + moved}
    stopped = refused(tmp_path, YOUNG, table_csv(AGE, {**AGES, MSOA_ONE: row}))
    assert "the categories of a row do not come to its total" in str(stopped)


def test_the_three_kinds_of_household_come_to_all_households(tmp_path: Path):
    row = {**HOMES[MSOA_THREE], made_up.ONE_FAMILY: 100}
    stopped = refused(tmp_path, ALONE, table_csv(HOUSEHOLDS, {**HOMES, MSOA_THREE: row}))
    assert "the categories of a row do not come to its total" in str(stopped)


def test_a_category_that_holds_more_than_the_total_stops_the_step(tmp_path: Path):
    row = {**HOMES[MSOA_THREE], made_up.WITH_CHILDREN[0]: 301}
    stopped = refused(tmp_path, CHILDREN, table_csv(HOUSEHOLDS, {**HOMES, MSOA_THREE: row}))
    assert "a category holds more than the total" in str(stopped)


def test_a_share_that_is_more_than_the_whole_stops_the_step(tmp_path: Path):
    """Each of the four is under the total, and together they are over it."""
    more = dict(zip(made_up.WITH_CHILDREN, (100, 100, 100, 100), strict=True))
    row = {**HOMES[MSOA_THREE], **more}
    stopped = refused(tmp_path, CHILDREN, table_csv(HOUSEHOLDS, {**HOMES, MSOA_THREE: row}))
    assert "a share is more than the whole" in str(stopped)


# Nothing is filled in


def test_an_area_where_nobody_was_counted_has_no_figure_and_is_never_nought(tmp_path: Path):
    nobody = dict.fromkeys(made_up.CATEGORIES["TS007A"], 0)
    made = built(tmp_path, YOUNG, table_csv(AGE, {**AGES, MSOA_TWO: nobody}))
    assert made.worked[TWO] == Worked(None, 0, 1, 0.0, State.SOURCE_GAP)
    (row,) = [row for row in made.rows if row.area_id == TWO]
    assert (row.state, row.has_a_value, row.value) == (State.SOURCE_GAP, False, None)
    assert made.worked[ONE].value == 30.0


def test_a_count_of_nought_is_a_count(tmp_path: Path):
    row = {**AGES[MSOA_THREE]} | dict.fromkeys(made_up.YOUNG, 0)
    row[MIDDLE] += 24
    made = built(tmp_path, YOUNG, table_csv(AGE, {**AGES, MSOA_THREE: row}))
    assert made.worked[THREE] == Worked(0.0, 1, 1, 1.0, State.PRESENT)


# The gate and the fence


def _with_the_source(**changed: object) -> Registry:
    """The repository's registry, with the entry of the two tables changed."""
    real = registry()
    entry = real.get(census_msoa.SOURCE)
    other = Source.model_validate(entry.model_dump() | changed)
    return Registry(tuple(other if source.id == entry.id else source for source in real))


def test_the_gate_is_asked_for_scoring_before_the_table_is_read(tmp_path: Path):
    gated = _with_the_source(status=Status.GATED, status_reason="Made up: not yet decided.")
    inputs = inputs_with(tmp_path, registry=gated)
    found = spine_of(inputs)
    with pytest.raises(LockError) as stopped:
        census_msoa.build(YOUNG, inputs, found)
    assert (stopped.value.rule, stopped.value.subject) == ("gate_refuses", census_msoa.SOURCE)
    assert not any(one.receipt.source_id == census_msoa.SOURCE for one in inputs.opened)


def test_a_source_held_for_the_census_table_alone_is_refused(tmp_path: Path):
    shown = _with_the_source(uses=["census_table"])
    inputs = inputs_with(tmp_path, registry=shown)
    found = spine_of(inputs)
    with pytest.raises(LockError) as stopped:
        census_msoa.build(YOUNG, inputs, found)
    assert stopped.value.rule == "gate_refuses"


def test_a_file_that_was_fetched_for_the_census_table_is_never_read_for_a_score(tmp_path: Path):
    inputs = inputs_with(tmp_path, use=Use.CENSUS_TABLE)
    found = spine_of(inputs)
    with pytest.raises(LockError) as stopped:
        census_msoa.build(YOUNG, inputs, found)
    assert stopped.value.rule == "file_is_for_the_product"


def test_the_table_of_another_measure_is_not_read_in_its_place(tmp_path: Path):
    inputs = inputs_with(tmp_path, {"TS003": zipped(HOUSEHOLDS, table_csv(HOUSEHOLDS))})
    found = spine_of(inputs)
    with pytest.raises(LockError) as stopped:
        census_msoa.build(YOUNG, inputs, found)
    assert stopped.value.rule == "input_has_one_receipt"


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_with(tmp_path)
    before = held(tmp_path / "store")
    for of in MEASURES:
        census_msoa.build(of, inputs, spine_of(inputs))
    assert held(tmp_path / "store") == before


# The evidence


@pytest.mark.parametrize("of", MEASURES, ids=[of.key for of in MEASURES])
def test_every_area_has_a_row_of_evidence_that_holds_its_figure(tmp_path: Path, of: Of):
    made = built(tmp_path, of)
    assert [row.fact_id for row in made.rows] == [
        f"{area}/feature/{of.key}" for area in (ONE, TWO, THREE)
    ]
    for row in made.rows:
        assert row.derivation_id == AREA_ROW_RATIO.derivation_id == "area_row_ratio@1"
        assert row.value == made.worked[row.area_id].value
        # From the day of the census to the month of the lookup, which says what an area is.
        assert row.data_period == Period(start="2021-03-21", end="2021-12-31")
        assert (row.units_used, row.units_expected, row.weight_covered) == (1, 1, 1.0)
    assert AREA_ROW_RATIO.kind is Kind.MEASURED and made.geography is Geography.MSOA21


@pytest.mark.parametrize("of", MEASURES, ids=[of.key for of in MEASURES])
def test_a_row_rests_on_the_table_and_on_the_files_that_say_which_msoa_an_area_is(
    tmp_path: Path, of: Of
):
    made = built(tmp_path, of)
    sources = sorted(receipt.source_id for receipt in made.files)
    assert sources == sorted(
        [
            census_msoa.SOURCE,
            "ons-census-2021-housing-tables",
            "ons-oa21-lsoa21-msoa21-lad22-lookup",
        ]
    )
    (table,) = [receipt for receipt in made.files if receipt.source_id == census_msoa.SOURCE]
    assert table.publisher_file == of.table.file and table.use is Use.SCORING
    assert all(row.inputs == tuple(sorted(r.file_id for r in made.files)) for row in made.rows)


# What is said of a measure


@pytest.mark.parametrize("module", MODULES, ids=[module.KEY for module in MODULES])
def test_core_holds_no_such_measure_so_no_build_carries_it(module: Measure):
    """The list of features is core's to change. This fails on the day core gains the measure."""
    assert not module.core_holds_it()
    assert module.KEY not in {feature.value for feature in FeatureId}
    assert module.KEY not in {measure.feature for measure in measures.MEASURES}
    assert module.SOURCE not in {measure.source for measure in measures.MEASURES}
    assert module.METHODS == (AREA_ROW_RATIO,)


@pytest.mark.parametrize("of", MEASURES, ids=[of.key for of in MEASURES])
def test_the_name_of_a_measure_says_who_is_counted_and_in_which_census(tmp_path: Path, of: Of):
    proposed = built(tmp_path, of).proposed
    who = "residents" if of.table is AGE else "households"
    assert proposed.key.startswith(f"{who}_") and who in proposed.label.lower()
    assert proposed.label.endswith(", Census 2021") and f"all {who}" in proposed.label
    assert (proposed.counted, proposed.describes) == (of.table.counted, "residents")
    assert (proposed.census, proposed.vintage) == ("Census 2021", "2021-03-21")
    assert (proposed.unit, proposed.geography) == ("%", Geography.MSOA21)
    assert len(proposed.short_label) <= 40 and proposed.short_label.startswith("More ")


@pytest.mark.parametrize("of", MEASURES, ids=[of.key for of in MEASURES])
def test_a_person_may_ask_for_more_of_what_is_counted_and_never_for_fewer(tmp_path: Path, of: Of):
    proposed = built(tmp_path, of).proposed
    assert proposed.polarity is Polarity.MORE
    assert (proposed.higher, proposed.lower) == ("more", "fewer")
    said = f"{proposed.label} {proposed.short_label}".lower()
    assert not re.search(r"\b(fewer|less|no|without|away|avoid)\b", said)


@pytest.mark.parametrize("of", MEASURES, ids=[of.key for of in MEASURES])
def test_no_two_areas_are_said_to_be_alike_for_who_lives_in_them(tmp_path: Path, of: Of):
    assert built(tmp_path, of).proposed.in_likeness is False


@pytest.mark.parametrize("of", MEASURES, ids=[of.key for of in MEASURES])
def test_the_sentence_of_a_measure_says_what_is_counted_when_and_by_whom(tmp_path: Path, of: Of):
    definition = built(tmp_path, of).proposed.definition
    for words in (
        of.said,
        f"all the {of.table.counted} of the area",
        "Census 2021",
        "21 March 2021",
        "Office for National Statistics",
        of.table.code,
        "not added up from smaller areas",
        "to 1 decimal place, with a half taken upward",
        "small changes to counts",
        "during a lockdown",
        "says nothing of who lives there now",
    ):
        assert words in definition, words
    assert definition.endswith(".") and not re.search(r"[.!?]\s", definition)


@pytest.mark.parametrize("of", MEASURES, ids=[of.key for of in MEASURES])
def test_what_a_figure_cannot_see_is_one_or_two_sentences_that_name_the_day_and_the_lockdown(
    of: Of,
):
    assert 1 <= len(of.cannot_see) <= 2
    said = " ".join(of.cannot_see)
    assert "21 March 2021" in said and "during a lockdown" in said
    # Each is one sentence: it ends in a full stop, and holds no other.
    assert all(line.endswith(".") and line.count(".") == 1 for line in of.cannot_see)
    assert not re.search(r"[!?;:]", said)


@pytest.mark.parametrize("of", MEASURES, ids=[of.key for of in MEASURES])
def test_nothing_said_of_a_measure_names_what_was_not_decided_on(tmp_path: Path, of: Of):
    """Age and household make-up were decided on. Nothing else about residents was."""
    proposed = built(tmp_path, of).proposed
    said = " ".join((proposed.key, proposed.label, proposed.short_label, proposed.definition))
    assert NOT_DECIDED.search(said) is None


@pytest.mark.parametrize(
    ("label", "key"),
    [
        ("Aged 20 to 34 as a share of everyone, Census 2021", "aged_20_34"),
        ("Residents aged 20 to 34 as a share of all residents", "residents_aged_20_34"),
        ("Young adults nearby, Census 2021", "young_adults"),
    ],
)
def test_a_measure_that_does_not_say_who_is_counted_or_in_which_census_is_refused(
    label: str, key: str
):
    with pytest.raises(ValueError, match="says in its name who is counted"):
        Of(key, AGE, ("aged_20_24",), label, "More of them", "Made up", ("Made up.",))


def test_a_measure_counts_categories_of_its_own_table_that_are_read():
    for counted in ((), ("one_person",), ("total",), ("aged_100_over",)):
        with pytest.raises(ValueError, match="counts categories of its table"):
            Of(
                "residents_made_up",
                AGE,
                counted,
                "Residents made up as a share of all residents, Census 2021",
                "More made up",
                "Made up",
                ("Made up.",),
            )


# What no measure may be made from


def _of_households(*counted: str, table: Table = HOUSEHOLDS) -> Of:
    return Of(
        "households_made_up",
        table,
        counted,
        "Households made up as a share of all households, Census 2021",
        "More made up",
        "Made up",
        ("Made up.",),
    )


@pytest.mark.parametrize(
    "counted",
    [
        ("lone_parent_children",),
        ("couple_married_children",),
        ("couple_cohabiting_children",),
        ("other_kinds_children",),
        ("couple_married_children", "couple_cohabiting_children"),
        ("couple_married_children", "couple_cohabiting_children", "other_kinds_children"),
        ("one_person", "lone_parent_children"),
    ],
)
def test_no_measure_can_be_made_from_one_kind_of_family_alone(counted: tuple[str, ...]):
    """How a couple is joined was not decided on, and nor were lone parents.

    The four categories with dependent children are read only to be added up.
    The step refuses a measure that counts some of them and not all.
    """
    with pytest.raises(ValueError, match="read only to be added up"):
        _of_households(*counted)


@pytest.mark.parametrize(
    "counted", [("one_family",), ("other_kinds",), ("one_person", "one_family")]
)
def test_no_measure_can_be_made_from_a_category_that_is_read_to_hold_the_total(
    counted: tuple[str, ...],
):
    """Other household types take in households of students. Nothing was decided on them."""
    with pytest.raises(ValueError, match="read only to hold the table to its total"):
        _of_households(*counted)


def test_the_two_measures_of_households_are_still_made():
    assert _of_households("one_person").counted == ("one_person",)
    assert _of_households(*households_dependent_children.WITH_CHILDREN).counted == (
        households_dependent_children.WITH_CHILDREN
    )


def test_a_measure_reads_a_table_as_this_step_holds_it_and_no_table_of_its_own():
    """A table of the same code with other categories would read what no measure may."""
    married = Category(
        "couple_married", ("Single family household: Married or civil partnership couple",)
    )
    own = Table(
        "TS003",
        "Household composition",
        "households",
        Category("total", ("Total: All households",)),
        (married,),
        (),
    )
    with pytest.raises(ValueError, match="reads a table as this step holds it"):
        _of_households("couple_married", table=own)


# What is kept of a table, once it is read

# A count for each of the four kinds of household with dependent children. No two are the
# same, and none is a count that is kept: all households, those of one person, or the sum.
FOUR_KINDS = (101, 53, 37, 11)


def _with_four_kinds() -> dict[str, made_up.Row]:
    """The made-up households, with a count of its own for each kind of family in one MSOA."""
    row = {**HOMES[MSOA_ONE], **dict(zip(made_up.WITH_CHILDREN, FOUR_KINDS, strict=True))}
    return {**HOMES, MSOA_ONE: row}


@pytest.mark.parametrize("of", [CHILDREN, ALONE], ids=[CHILDREN.key, ALONE.key])
def test_no_count_of_one_kind_of_family_is_kept_once_a_table_is_read(tmp_path: Path, of: Of):
    """The four categories with dependent children are kept as one sum, and never four.

    A measure that is allowed hands back what it read. If that held the count of
    lone parents of every MSOA, a figure of lone parents would be one line away.
    """
    made = built(tmp_path, of, table_csv(HOUSEHOLDS, _with_four_kinds()))
    for row in made.counts.of_msoa.values():
        assert set(row) == {"total", "one_person", census_msoa.TOGETHER}
    kept = made.counts.of_msoa[MSOA_ONE]
    assert (kept["total"], kept["one_person"], kept[census_msoa.TOGETHER]) == (400, 100, 202)
    # Nor is a household of one family, or of any other kind, which hold the table to its total.
    one_family, other_kinds = 250, 50
    assert not set(kept.values()) & {*FOUR_KINDS, one_family, other_kinds}
    assert built(tmp_path / "again", CHILDREN, table_csv(HOUSEHOLDS, _with_four_kinds())).worked[
        ONE
    ].value == pytest.approx(50.5)


def test_every_band_of_age_is_kept_for_age_is_what_was_decided_on(tmp_path: Path):
    kept = built(tmp_path, YOUNG).counts.of_msoa[MSOA_ONE]
    assert set(kept) == {"total", *(category.key for category in AGE.categories)}
    assert census_msoa.TOGETHER not in kept


def test_the_reader_is_handed_a_table_this_step_holds_and_no_table_of_the_callers_own(
    tmp_path: Path,
):
    """A table of the caller's making could name lone parents, or who lives alone by their age."""
    lone = "Single family household: Lone parent family"
    rows = {code: {**row, lone: 30} for code, row in HOMES.items()}
    own = Table(
        "TS003",
        "Household composition",
        "households",
        HOUSEHOLDS.total,
        (*HOUSEHOLDS.categories[:3], Category("lone_parents", (lone,))),
        HOUSEHOLDS.make_up_the_total,
    )
    inputs = inputs_with(tmp_path, {"TS003": zipped(HOUSEHOLDS, table_csv(HOUSEHOLDS, rows))})
    opened = inputs.open(census_msoa.SOURCE, Use.SCORING, named=HOUSEHOLDS.is_the_table)
    with pytest.raises(ValueError, match="a table is read as this step holds it"):
        census_msoa.read(opened, own)
    assert set(census_msoa.read(opened, HOUSEHOLDS).of_msoa[MSOA_ONE]) == {
        "total",
        "one_person",
        census_msoa.TOGETHER,
    }


def test_a_category_cannot_take_the_name_the_sum_is_kept_under():
    with pytest.raises(ValueError, match="a category is named once"):
        Table(
            "TS003",
            "Household composition",
            "households",
            HOUSEHOLDS.total,
            (Category(census_msoa.TOGETHER, ("One-person household",)),),
            (),
        )


def test_no_other_module_names_the_source_of_age_and_households():
    """The gate is asked about a file, and not about a column of it.

    So a second module that opened the zip could read lone parents, or a person
    who lives alone by their age. One module opens it, and this holds that.
    """
    named = {
        path.relative_to(REPOSITORY).as_posix()
        for folder in ("packages/pipeline/src", "packages/core/src", "services/api/src")
        for path in (REPOSITORY / folder).rglob("*.py")
        if census_msoa.SOURCE in path.read_text(encoding="utf-8")
    }
    assert named == {"packages/pipeline/src/burro_pipeline/derive/census_msoa.py"}
