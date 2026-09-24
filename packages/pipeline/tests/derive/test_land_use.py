"""Five shares of land, from a made-up table of land use to a figure for each area.

Every file here is made up. The workbook is laid out as the publisher's is:
its sheets, its rows of names and its columns are what the step `describe`
gave of the real one, and every code, place and figure is made up.
`land_use_support.py` says which is which.

The town is the made-up town of the tests of cells. An output area is a square
of one hectare, so an LSOA is two hectares, and the last has an island.

    area             LSOA        hectares   industry  storage  transport  gardens  woodland
    Quillhaven 001   E01999001   2          0.5       0.2      0.1        0.4      0
                     E01999002   2          0.1       0        0.3        0.8      0.2
    Quillhaven 002   E01999003   2          0         0        0          1.2      0.4
                     E01999004   2          0.25      0.05     0          0.3      0
    Tallowgate 001   E01999005   2          1.0       0.5      0.25       0        0
                     E01999006   3          0.5       0.25     0.75       0.15     0.3

    industry    Quillhaven 001   0.6 over 4    = 15.0
                Quillhaven 002   0.25 over 4   = 6.3, from 6.25, a half taken upward
                Tallowgate 001   1.5 over 5    = 30.0
    gardens     Quillhaven 001   1.2 over 4    = 30.0
                Quillhaven 002   1.5 over 4    = 37.5
                Tallowgate 001   0.15 over 5   = 3.0
"""

import re
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, TAGS, tags_of
from burro_core.ids import FeatureId, GrittyVariant, NativeResolution, TagId
from burro_pipeline.cells import land, spine
from burro_pipeline.derive import land_use
from burro_pipeline.derive.land_use import LandUse
from burro_pipeline.derive.land_use_sheet import read_table
from burro_pipeline.derive.measures import Ground, Measure, says_what_core_says
from burro_pipeline.derive.methods import LSOA_RATIO_BY_HOMES
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import held, registry
from .land_use_support import (
    A_REGION,
    AS_AT,
    AS_PUBLISHED,
    CANARY,
    CANARY_NUMBER,
    CATEGORIES,
    CODE,
    COLUMNS,
    DASH,
    GAP,
    GARDENS,
    HECTARES,
    INDUSTRY,
    LAND,
    OF_A_GROUP,
    OUTSIDE,
    PER_CENT,
    RESIDENTIAL,
    ROADS,
    SOURCE,
    STORAGE,
    TOTAL,
    TRANSPORT,
    UNITS,
    USED,
    WOODLAND,
    Cell,
    Row,
    all_of,
    figures,
    inputs_of,
    published,
    receipt,
    sheet_as_published,
    workbook,
)

Q1, Q2, T1 = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
F = FeatureId
FIVE = (
    F.LAND_GARDENS,
    F.LAND_INDUSTRY,
    F.LAND_STORAGE,
    F.LAND_TRANSPORT_OTHER,
    F.LAND_WOODLAND,
)
# The measures whose name is core's, so that a build carries them: all five.
AS_CORE = FIVE
WORKED_BY_HAND: Mapping[FeatureId, Mapping[str, float]] = {
    F.LAND_INDUSTRY: {Q1: 15.0, Q2: 6.3, T1: 30.0},
    F.LAND_STORAGE: {Q1: 5.0, Q2: 1.3, T1: 15.0},
    F.LAND_TRANSPORT_OTHER: {Q1: 10.0, Q2: 0.0, T1: 20.0},
    F.LAND_GARDENS: {Q1: 30.0, Q2: 37.5, T1: 3.0},
    F.LAND_WOODLAND: {Q1: 5.0, Q2: 10.0, T1: 6.0},
}


def built(
    folder: Path,
    content: bytes | None = None,
    feature: FeatureId = F.LAND_INDUSTRY,
    period: Period | None = None,
) -> LandUse:
    """One measure, from a made-up build whose table is the one given."""
    inputs = inputs_of(folder, published() if content is None else content, period=period)
    found = spine.build(inputs)
    return land_use.build(feature, inputs, found, land.build(inputs, found))


def refused(folder: Path, content: bytes, feature: FeatureId = F.LAND_INDUSTRY) -> LockError:
    """The refusal of a table that is not what the step was written to read."""
    inputs = inputs_of(folder, content)
    found = spine.build(inputs)
    measured = land.build(inputs, found)
    with pytest.raises(LockError) as stopped:
        land_use.build(feature, inputs, found, measured)
    assert stopped.value.rule == "input_is_as_described"
    assert stopped.value.subject == receipt(content).file_id
    # A refusal repeats nothing from the file.
    assert CANARY not in str(stopped.value) and str(CANARY_NUMBER) not in str(stopped.value)
    return stopped.value


def values(found: LandUse) -> dict[str, float | None]:
    return {area: one.value for area, one in found.worked.items()}


# What the publisher's documents give, and the step holds


def test_the_28_categories_are_named_as_the_technical_notes_name_them():
    assert len(land_use.CATEGORIES) == 28
    assert [category.name for category in land_use.CATEGORIES] == list(CATEGORIES)
    assert len({category.code for category in land_use.CATEGORIES}) == 28
    assert len({category.group for category in land_use.CATEGORIES}) == 13
    for category in land_use.CATEGORIES:
        assert category.name in category.spelt


def test_each_measure_is_one_category_and_never_a_group():
    """The group industry and commerce holds offices and shops. No measure is made from it."""
    of = {feature: land_use.MEASURES[feature].category for feature in FIVE}
    assert of == {
        F.LAND_INDUSTRY: "I",
        F.LAND_STORAGE: "S",
        F.LAND_TRANSPORT_OTHER: "T",
        F.LAND_GARDENS: "RG",
        F.LAND_WOODLAND: "F",
    }
    groups = {category.group for category in land_use.CATEGORIES}
    spelt = {spelling.casefold() for one in land_use.CATEGORIES for spelling in one.spelt}
    assert "Industry and commerce" in groups and "industry and commerce" not in spelt
    assert "Transport and utilities" in groups and "transport and utilities" not in spelt


def test_transport_other_than_roads_holds_no_road():
    by_code = {category.code: category for category in land_use.CATEGORIES}
    assert by_code["H"].name == "Highways and roads"
    assert by_code["T"].name == "Transport (other)"
    assert land_use.MEASURES[F.LAND_TRANSPORT_OTHER].category != "H"


# Places, never residents


def test_no_measure_is_made_from_land_that_says_who_lives_on_it():
    """Three of the 28 say who lives on the land. Each is read to add up the land, and no more.

    The technical notes give communal accommodation as hostels, old people's
    homes, children's homes, monasteries and convents. They put religious
    buildings and prisons under community buildings, and barracks under
    defence buildings.
    """
    by_code = {category.code: category.name for category in land_use.CATEGORIES}
    assert {by_code[code] for code in land_use.SAYS_WHO_LIVES_THERE} == {
        "Communal accommodation",
        "Community buildings",
        "Defence buildings",
    }
    made_from = {of.category for of in land_use.MEASURES.values()}
    assert not made_from & land_use.SAYS_WHO_LIVES_THERE
    # All the land of an LSOA is its 28 categories added up, so the three are still read.
    assert set(land_use.COLUMNS) >= land_use.SAYS_WHO_LIVES_THERE


@pytest.mark.parametrize("code", ["Q", "C", "D"])
def test_a_measure_of_land_that_says_who_lives_on_it_is_refused(code: str):
    of = replace(land_use.MEASURES[F.LAND_INDUSTRY], category=code)
    with pytest.raises(ValueError, match="says who lives on the land"):
        land_use.measures_of(of)


@pytest.mark.parametrize("named", ["Industry and commerce", "Residential", "i", ""])
def test_a_measure_of_what_is_no_category_of_the_table_is_refused(named: str):
    """A measure names its category by its code. A group, a name and a guess are none."""
    of = replace(land_use.MEASURES[F.LAND_INDUSTRY], category=named)
    with pytest.raises(ValueError, match="is no category of the table"):
        land_use.measures_of(of)


def test_the_registry_entry_names_the_land_that_is_never_a_measure():
    said = " ".join(registry().get(SOURCE).conditions)
    for name in ("Communal accommodation (Q)", "Community buildings (C)", "Defence buildings (D)"):
        assert name in said, name
    assert "who lives" in said


# The parser


def test_the_hectares_of_every_lsoa_are_read_as_the_publisher_wrote_them(tmp_path: Path):
    sheet = built(tmp_path).sheet
    assert set(sheet.hectares) == set(USED)
    assert sheet.hectares["E01999001"]["I"] == 0.5
    assert sheet.hectares["E01999006"]["RG"] == 0.15
    assert dict(sheet.total) == dict(LAND)
    # England, two regions and the two notes under the table hold no code of an LSOA.
    assert (sheet.rows, sheet.others, sheet.without) == (7, 5, ())
    assert sheet.header_at == 6


def test_the_table_is_found_wherever_it_stands_in_the_workbook(tmp_path: Path):
    """The step is told no name of a sheet, no row and no place of a column."""
    as_made = built(tmp_path / "as").worked
    turned = sheet_as_published(columns=tuple(reversed(AS_PUBLISHED)))
    moved = workbook({CANARY: [[CANARY]], "Another name": turned})
    assert built(tmp_path / "moved", moved).worked == as_made
    fewer = tuple(name for name in AS_PUBLISHED if name in (CODE, TOTAL, *CATEGORIES))
    assert built(tmp_path / "fewer", published(columns=fewer)).worked == as_made


@pytest.mark.parametrize("how", ["{name}", "{name} ({code})", "{code}", " {name}  ({code}) "])
def test_a_column_is_found_by_the_name_of_its_category_by_its_code_or_by_both(
    tmp_path: Path, how: str
):
    """The publisher's documents write a category all three ways. No page says which is used."""
    written = {
        one.name: how.format(name=one.name.upper(), code=one.code) for one in land_use.CATEGORIES
    }
    columns = tuple(written.get(name, name) for name in COLUMNS)
    held = {
        code: {written[name]: land for name, land in row.items()} for code, row in figures().items()
    }
    found = built(tmp_path / "written", published(held, columns=columns))
    assert found.worked == built(tmp_path / "as").worked


def test_a_column_under_the_heading_of_its_definition_is_found(tmp_path: Path):
    """The technical notes head the definition of woodland another way than they list it."""
    written = {WOODLAND: "Forestry/Woodland (F)", "Retail": "Retailing"}
    columns = tuple(written.get(name, name) for name in COLUMNS)
    held = {
        code: {written.get(name, name): land for name, land in row.items()}
        for code, row in figures().items()
    }
    found = built(tmp_path / "written", published(held, columns=columns), F.LAND_WOODLAND)
    assert values(found) == dict(WORKED_BY_HAND[F.LAND_WOODLAND])


def test_the_order_of_the_rows_changes_nothing(tmp_path: Path):
    turned = dict(reversed(list(figures().items())))
    assert built(tmp_path / "turned", published(turned)).worked == built(tmp_path / "as").worked


def test_all_the_land_of_an_lsoa_is_its_28_categories_added_up(tmp_path: Path):
    """The total of a group is never read, and the grand total is part of no figure."""
    sheet = built(tmp_path, published(figures(n001={"Water": 1.0, "Vacant land": 0.5}))).sheet
    assert sheet.total["E01999001"] == 3.5
    assert str(CANARY_NUMBER) not in repr(sheet)
    assert all(
        set(held) == {one.code for one in land_use.CATEGORIES} for held in sheet.hectares.values()
    )


@pytest.mark.parametrize("missing", CATEGORIES)
def test_a_table_without_one_of_the_28_categories_stops_the_step(tmp_path: Path, missing: str):
    """Without every category the land of an LSOA cannot be added up."""
    columns = tuple(name for name in COLUMNS if name != missing)
    stopped = refused(tmp_path, published(columns=columns))
    code = next(one.code for one in land_use.CATEGORIES if one.name == missing)
    assert f"the column {code} is missing" in str(stopped)


@pytest.mark.parametrize(
    ("changed", "why"),
    [
        ({INDUSTRY: -0.1}, "an area of land is below nothing"),
        ({WOODLAND: "[x]"}, "an area of land is not a number"),
        ({"Water": CANARY}, "an area of land is not a number"),
    ],
)
def test_a_cell_that_is_no_area_of_land_stops_the_step(
    tmp_path: Path, changed: Mapping[str, Cell], why: str
):
    assert why in str(refused(tmp_path, published(figures(n001=changed))))


def test_an_lsoa_that_is_there_twice_stops_the_step(tmp_path: Path):
    table = sheet_as_published(under=())
    twice: list[Row] = [*table, table[-2]]
    assert "an LSOA is there twice" in str(refused(tmp_path, published(sheets={HECTARES: twice})))


def test_an_lsoa_with_no_land_at_all_stops_the_step(tmp_path: Path):
    none: dict[str, Cell] = dict.fromkeys(CATEGORIES, 0.0)
    assert "an LSOA covers no land" in str(refused(tmp_path, published(figures(n001=none))))


def test_a_table_of_somewhere_else_stops_the_step(tmp_path: Path):
    elsewhere = {OUTSIDE: figures()[OUTSIDE]}
    assert "no row of London" in str(refused(tmp_path, published(elsewhere)))


def test_a_table_on_the_codes_of_another_census_stops_the_step(tmp_path: Path):
    """No page names the census. A table of 2011 lacks the LSOAs that were drawn again."""
    fewer = {code: row for code, row in figures().items() if code != "E01999004"}
    stopped = refused(tmp_path, published(fewer))
    assert "an LSOA of the census of 2021 has no row" in str(stopped)


def test_the_rows_are_keyed_by_the_lsoas_of_2021_once_held_to_the_spine(tmp_path: Path):
    assert built(tmp_path).geography is Geography.LSOA21


# The workbook as it is published


def test_the_table_is_the_sheet_that_says_hectares_and_the_other_is_never_read(tmp_path: Path):
    """The workbook holds the table twice, in per cent and in hectares, under the same names."""
    as_made = built(tmp_path / "as")
    every: dict[str, Cell] = dict.fromkeys(CATEGORIES, CANARY_NUMBER)
    other = sheet_as_published(
        {code: every for code in figures()}, unit=UNITS[PER_CENT], dashed=False
    )
    changed = built(tmp_path / "changed", published(sheets={PER_CENT: other}))
    assert changed.worked == as_made.worked
    assert str(CANARY_NUMBER) not in repr(changed.sheet)
    turned = workbook({HECTARES: sheet_as_published(), PER_CENT: other})
    assert built(tmp_path / "turned", turned).worked == as_made.worked


def test_a_workbook_in_which_no_sheet_says_hectares_stops_the_step(tmp_path: Path):
    acres = sheet_as_published(unit="Acres")
    stopped = refused(tmp_path, published(sheets={HECTARES: acres}))
    assert "no sheet that holds the table says its unit" in str(stopped)


def test_the_unit_is_looked_for_above_the_names_and_nowhere_else(tmp_path: Path):
    """A note under the table that says hectares does not make a sheet the table."""
    under = sheet_as_published(unit="Acres", under=("Hectares",))
    stopped = refused(tmp_path, published(sheets={HECTARES: under}))
    assert "no sheet that holds the table says its unit" in str(stopped)


def test_two_sheets_that_say_hectares_stop_the_step(tmp_path: Path):
    twice = published(sheets={PER_CENT: sheet_as_published()})
    assert "more than one sheet holds the table" in str(refused(tmp_path, twice))


def test_a_group_of_one_category_is_read_from_the_total_under_its_name(tmp_path: Path):
    """Gardens have no name in the row of names. The row above names the group over a total."""
    over = {one.code: one.over for one in land_use.CATEGORIES if one.over}
    assert over == {
        "D": ("Defence",),
        "O": ("Outdoor recreation",),
        "RG": ("Residential gardens",),
        "X": ("Undeveloped land",),
        "V": ("Vacant",),
    }
    sheet = built(
        tmp_path, published(figures(n001={"Outdoor recreation": 0.125, "Vacant land": 0.25}))
    ).sheet
    held = sheet.hectares["E01999001"]
    assert (held["RG"], held["O"], held["V"], held["D"]) == (0.4, 0.125, 0.25, 0.0)


def test_the_total_of_a_group_of_several_categories_is_never_a_category(tmp_path: Path):
    """The group of homes is called Residential, as the category is. Its total is not read."""
    groups = [name for name in AS_PUBLISHED if name.startswith(OF_A_GROUP)]
    assert f"{OF_A_GROUP}Residential" in groups and len(groups) == 10
    sheet = built(tmp_path).sheet
    assert sheet.hectares["E01999003"]["R"] == 0.2
    assert set(land_use.OVER) == {"D", "O", "RG", "X", "V", land_use.ALL}
    named = {spelling.casefold() for spellings in land_use.OVER.values() for spelling in spellings}
    assert not named & {name[1:].casefold() for name in groups}


def test_a_category_is_found_as_the_workbook_spells_it(tmp_path: Path):
    by_code = {one.code: one.spelt for one in land_use.CATEGORIES}
    assert "Institutional and communal accommo-dations" in by_code["Q"]
    assert "Unknown" in by_code["~U"]
    changed = figures(n001={"Communal accommodation": 0.125, ROADS: 0.275})
    assert built(tmp_path, published(changed)).sheet.hectares["E01999001"]["Q"] == 0.125


def test_a_column_that_holds_nothing_changes_nothing(tmp_path: Path):
    without = tuple(name for name in AS_PUBLISHED if name != GAP)
    assert built(tmp_path / "without", published(columns=without)).worked == (
        built(tmp_path / "as").worked
    )


def test_the_rows_of_england_and_of_a_region_are_part_of_no_figure(tmp_path: Path):
    none = sheet_as_published(larger=())
    fewer = built(tmp_path / "fewer", published(sheets={HECTARES: none}))
    assert fewer.worked == built(tmp_path / "as").worked
    assert fewer.sheet.others == 2


def test_the_row_of_a_region_is_read_by_its_code_to_hold_the_sum_of_its_lsoas_to(
    tmp_path: Path,
):
    """A test on the real table holds what London's LSOAs add up to, to the row of London."""
    inputs = inputs_of(tmp_path, published())
    given = inputs.open(SOURCE, Use.SCORING, named=land_use.is_the_table)
    table = read_table(
        given,
        land_use.COLUMNS,
        re.compile(A_REGION),
        over=land_use.OVER,
        total=land_use.TOTAL,
        unit=land_use.UNIT,
    )
    (row,) = table.rows
    assert row.code == A_REGION and set(row.held) == set(land_use.COLUMNS)
    assert set(row.held.values()) == {CANARY_NUMBER}


# The dash, which the workbook does not explain


def test_a_dash_is_none_of_that_land_where_the_row_adds_up_to_its_total(tmp_path: Path):
    found = built(tmp_path, feature=F.LAND_TRANSPORT_OTHER)
    assert DASH in repr(sheet_as_published())
    assert found.worked[Q2].value == 0.0 and found.worked[Q2].state is State.PRESENT
    # 28 cells of each of 7 rows, less the cells that hold land.
    assert found.sheet.dashes == 7 * 28 - sum(len(used) + 2 for used in USED.values())


def test_nought_written_as_a_number_is_read_as_a_dash_is(tmp_path: Path):
    written = built(tmp_path / "written", published(dashed=False))
    assert written.worked == built(tmp_path / "as").worked
    assert written.sheet.dashes == 0


def test_a_row_with_a_dash_that_does_not_add_up_to_its_total_stops_the_step(tmp_path: Path):
    """Were the dash some land that is withheld, the row would fall short of its total."""
    short = figures(n001={TOTAL: LAND["E01999001"] + 0.3})
    assert "a row does not add up to its total" in str(refused(tmp_path, published(short)))


def test_a_row_that_adds_up_to_more_than_its_total_stops_the_step(tmp_path: Path):
    over = figures(n003={TOTAL: LAND["E01999003"] - 0.3})
    stopped = refused(tmp_path, published(over, dashed=False))
    assert "a row does not add up to its total" in str(stopped)


def test_a_row_is_held_to_its_total_give_or_take_what_rounding_allows(tmp_path: Path):
    """The made-up figures are given to three places. Each may be out by half a thousandth,
    and so may the total: 29 of them by 0.0145 together."""
    rounded = figures(n001={INDUSTRY: 0.51, TOTAL: 2.0}, n002={TOTAL: 2.01})
    found = built(tmp_path / "rounded", published(rounded))
    assert found.sheet.places == 3
    assert found.sheet.total["E01999001"] == 2.01
    too_far = figures(n001={INDUSTRY: 0.52, TOTAL: 2.0})
    stopped = refused(tmp_path / "far", published(too_far))
    assert "a row does not add up to its total" in str(stopped)


def test_figures_given_to_every_place_are_held_to_their_total_closely(tmp_path: Path):
    exact = {
        code: {name: float(str(held)) * 0.777 for name, held in row.items()}
        for code, row in figures().items()
    }
    found = built(tmp_path / "exact", published(exact))
    assert found.sheet.places == 4
    off = {code: dict(row) for code, row in exact.items()}
    off["E01999001"] = off["E01999001"] | {TOTAL: all_of(exact["E01999001"]) + 0.002}
    stopped = refused(tmp_path / "off", published(off))
    assert "a row does not add up to its total" in str(stopped)


def test_a_row_that_gives_no_total_is_an_lsoa_with_no_figure(tmp_path: Path):
    found = built(tmp_path, published(figures(n001={TOTAL: None})))
    assert found.sheet.without == ("E01999001",)
    assert found.worked[Q1].state is State.PARTIAL


@pytest.mark.parametrize("held", ["--", "..", "[c]", "n/a", " - x"])
def test_any_other_text_where_a_figure_would_stand_stops_the_step(tmp_path: Path, held: str):
    stopped = refused(tmp_path, published(figures(n001={WOODLAND: held})))
    assert "an area of land is not a number" in str(stopped)


# The unit, which no page states


def test_the_totals_are_held_to_the_land_of_each_lsoa_as_the_build_measures_it(tmp_path: Path):
    """The made-up town is squares of one hectare, so an LSOA's total is its land."""
    assert built(tmp_path).sheet.to_the_land == 1.0


@pytest.mark.parametrize(
    ("times", "unit"), [(10_000, "square metres"), (0.01, "square kilometres"), (2.471, "acres")]
)
def test_a_table_in_another_unit_than_hectares_stops_the_step(
    tmp_path: Path, times: float, unit: str
):
    scaled = {
        code: {name: times * float(str(held)) for name, held in row.items()}
        for code, row in figures().items()
    }
    stopped = refused(tmp_path, published(scaled))
    assert "its totals are not the hectares of its LSOAs" in str(stopped), unit


def test_a_table_of_shares_stops_the_step(tmp_path: Path):
    """A share of each LSOA cannot be added up over an area. The step needs areas of land."""
    shares = {
        code: {name: 100 * float(str(held)) / LAND[code] for name, held in row.items()}
        for code, row in figures().items()
    }
    stopped = refused(tmp_path, published(shares))
    assert "its figures are shares and not areas of land" in str(stopped)


def test_a_total_that_differs_a_little_from_the_land_is_let_through(tmp_path: Path):
    """The outline the build measures is generalised. The publisher's is not."""
    a_little = {
        code: {name: 1.25 * float(str(held)) for name, held in row.items()}
        for code, row in figures().items()
    }
    found = built(tmp_path, published(a_little))
    assert found.sheet.to_the_land == 1.25
    assert values(found) == dict(WORKED_BY_HAND[F.LAND_INDUSTRY])


# The figures


@pytest.mark.parametrize("feature", FIVE)
def test_an_areas_figure_is_the_land_of_the_category_over_all_its_land(
    tmp_path: Path, feature: FeatureId
):
    found = built(tmp_path, feature=feature)
    assert values(found) == dict(WORKED_BY_HAND[feature])
    for one in found.worked.values():
        assert (one.units_used, one.units_expected, one.weight_covered) == (2, 2, 1.0)
        assert (one.state, one.flags) == (State.PRESENT, ())


def test_a_figure_is_one_sum_over_another_and_never_a_mean_of_shares(tmp_path: Path):
    """The LSOAs of Tallowgate are 2 and 3 hectares. A mean of their shares would be 33.3."""
    assert values(built(tmp_path))[T1] == 30.0
    assert land_use.METHODS == (LSOA_RATIO_BY_HOMES,)
    assert LSOA_RATIO_BY_HOMES.kind is Kind.MEASURED


def test_a_figure_is_given_to_one_decimal_place_with_a_half_taken_upward(tmp_path: Path):
    assert values(built(tmp_path))[Q2] == 6.3
    assert values(built(tmp_path / "s", feature=F.LAND_STORAGE))[Q2] == 1.3


def test_land_of_nought_is_a_figure(tmp_path: Path):
    found = built(tmp_path, feature=F.LAND_TRANSPORT_OTHER).worked[Q2]
    assert (found.value, found.state, found.weight_covered) == (0.0, State.PRESENT, 1.0)


def test_an_lsoa_with_an_empty_cell_adds_nothing_and_is_never_nought(tmp_path: Path):
    """Were the cell read as nought the figure would be 15.0. It is the other LSOA's share."""
    found = built(tmp_path, published(figures(n001={"Water": None})))
    one = found.worked[Q1]
    assert (one.value, one.state) == (5.0, State.PARTIAL)
    assert (one.units_used, one.units_expected, one.weight_covered) == (1, 2, 0.54)
    assert found.sheet.without == ("E01999001",)
    assert values(found)[Q2] == 6.3


def test_below_half_the_homes_no_figure_is_given(tmp_path: Path):
    one = built(tmp_path, published(figures(n002={INDUSTRY: None}))).worked[Q1]
    assert (one.value, one.state) == (None, State.BELOW_THRESHOLD)
    assert (one.units_used, one.units_expected, one.weight_covered) == (1, 2, 0.46)


def test_an_area_with_no_figure_at_all_is_a_gap_in_the_source(tmp_path: Path):
    found = built(tmp_path, published(figures(n001={ROADS: None}, n002={RESIDENTIAL: None})))
    one = found.worked[Q1]
    assert (one.value, one.state, one.weight_covered) == (None, State.SOURCE_GAP, 0.0)
    assert values(found) == {Q1: None, Q2: 6.3, T1: 30.0}


def test_an_lsoa_outside_london_is_part_of_no_figure(tmp_path: Path):
    more = built(tmp_path / "more", published(figures(n901={INDUSTRY: 1.0, RESIDENTIAL: 0.0})))
    assert more.worked == built(tmp_path / "as").worked
    assert set(more.worked) == {Q1, Q2, T1}


def test_the_five_measures_read_the_table_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    read: list[str] = []
    read_table = land_use.read_table

    def watched(*given: object, **named: object):
        read.append("once")
        return read_table(*given, **named)  # type: ignore[arg-type]

    monkeypatch.setattr(land_use, "read_table", watched)
    inputs = inputs_of(tmp_path, published(figures(n001={"Utilities": 0.0625})))
    found = spine.build(inputs)
    measured = land.build(inputs, found)
    for feature in FIVE:
        land_use.build(feature, inputs, found, measured)
    assert read == ["once"]


def test_the_step_names_every_column_it_reads_and_they_are_the_28_categories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    asked: list[Mapping[str, object]] = []
    read_table = land_use.read_table

    def watched(opened: object, columns: Mapping[str, object], *given: object, **named: object):
        asked.append(columns)
        return read_table(opened, columns, *given, **named)  # type: ignore[arg-type]

    monkeypatch.setattr(land_use, "read_table", watched)
    built(tmp_path, published(figures(n001={"Utilities": 0.125})))
    (columns,) = asked
    # The 28 categories, and the publisher's own total that each row is held to.
    assert sorted(columns) == sorted(
        [*(category.code for category in land_use.CATEGORIES), land_use.ALL]
    )


# The other figure, which no build carries


def test_the_mean_of_shares_by_homes_is_another_figure_than_the_share_of_land(tmp_path: Path):
    """Tallowgate's LSOAs are 2 and 3 hectares, with half and a sixth of each in industry."""
    inputs = inputs_of(tmp_path, published())
    found = spine.build(inputs)
    made = land_use.build(F.LAND_INDUSTRY, inputs, found, land.build(inputs, found))
    by_homes = land_use.figures_by_homes(F.LAND_INDUSTRY, made.sheet, found)
    homes: dict[str, int] = {}
    for cell in found.cells:
        homes[cell.lsoa] = homes.get(cell.lsoa, 0) + cell.homes
    shares = {"E01999005": 50.0, "E01999006": 100 * 0.5 / 3}
    by_hand = sum(homes[lsoa] * share for lsoa, share in shares.items()) / sum(
        homes[lsoa] for lsoa in shares
    )
    assert by_homes[T1].value == round(by_hand, 1) != made.worked[T1].value == 30.0
    assert set(by_homes) == set(made.worked)
    assert all(one.state is State.PRESENT for one in by_homes.values())


def test_the_mean_of_shares_by_homes_fills_nothing_in(tmp_path: Path):
    inputs = inputs_of(tmp_path, published(figures(n005={"Water": None})))
    found = spine.build(inputs)
    made = land_use.build(F.LAND_INDUSTRY, inputs, found, land.build(inputs, found))
    one = land_use.figures_by_homes(F.LAND_INDUSTRY, made.sheet, found)[T1]
    assert one.units_used == 1 and one.state in (State.PARTIAL, State.BELOW_THRESHOLD)
    assert one.value in (None, 16.7)


# The evidence


@pytest.mark.parametrize("feature", FIVE)
def test_every_area_has_a_row_of_evidence_that_names_the_three_files(
    tmp_path: Path, feature: FeatureId
):
    found = built(tmp_path, feature=feature)
    assert [row.fact_id for row in found.rows] == [
        f"{area}/feature/{feature.value}" for area in (Q1, Q2, T1)
    ]
    assert {one.source_id for one in found.files} == {
        SOURCE,
        "ons-census-2021-housing-tables",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
    }
    for row in found.rows:
        assert row.inputs == tuple(sorted(one.file_id for one in found.files))
        assert row.derivation_id == "lsoa_ratio_by_homes@1"
        assert (row.units_used, row.units_expected, row.weight_covered) == (2, 2, 1.0)
        assert (row.state, row.flags) == (State.PRESENT, ())
        assert row.retrieved_on == "2026-09-23"


def test_a_figure_that_is_missing_has_a_row_too_and_the_row_says_why(tmp_path: Path):
    changed = figures(n001={ROADS: None}, n002={ROADS: None}, n004={ROADS: None})
    rows = {row.area_id: row for row in built(tmp_path, published(changed)).rows}
    assert (rows[Q1].state, rows[Q1].units_used, rows[Q1].weight_covered) == (
        State.SOURCE_GAP,
        0,
        0.0,
    )
    assert (rows[Q2].state, rows[Q2].units_used) == (State.BELOW_THRESHOLD, 1)
    assert all(row.inputs for row in rows.values())


def test_the_rows_stand_as_the_evidence_of_a_release(tmp_path: Path):
    found = built(tmp_path)
    evidence = Evidence.of("lon-2026-10-02-01", found.files, land_use.METHODS, found.rows)
    row = evidence.row(f"{T1}/feature/land_industry")
    assert row is not None
    assert evidence.sources_of(row) == frozenset(found.metric.source_ids)
    assert evidence.method(row.derivation_id or "") == LSOA_RATIO_BY_HOMES


# The name and the unit


@pytest.mark.parametrize("feature", AS_CORE)
def test_each_measure_is_named_and_made_as_core_says_so_a_build_carries_it(
    tmp_path: Path, feature: FeatureId
):
    metric, core = built(tmp_path, feature=feature).metric, FEATURES[feature]
    assert (metric.label, metric.method) == (core.label, core.method)
    assert metric.method.value == "measured"
    assert says_what_core_says(metric)
    assert land_use.MEASURES[feature].waits_on == ()


def test_transport_is_named_for_what_its_category_holds_and_never_for_depots_or_yards(
    tmp_path: Path,
):
    """Its publisher puts depots and yards under storage. Core named it for them once."""
    metric = built(tmp_path, feature=F.LAND_TRANSPORT_OTHER).metric
    core = FEATURES[F.LAND_TRANSPORT_OTHER]
    for said in (metric.label, core.label, core.short_label):
        assert "depot" not in said.lower() and "yard" not in said.lower()
    assert "railways, airports and docks" in metric.label
    assert says_what_core_says(metric)
    as_it_was = metric.model_copy(
        update={"label": "Land used for depots, yards and other transport"}
    )
    assert not says_what_core_says(as_it_was)


def test_the_words_of_storage_hold_the_depots_and_yards(tmp_path: Path):
    definition = built(tmp_path, feature=F.LAND_STORAGE).metric.definition
    assert "depots, scrap and timber yards, warehousing" in definition.lower()


@pytest.mark.parametrize("feature", FIVE)
def test_core_decides_the_unit_and_which_way_is_more(tmp_path: Path, feature: FeatureId):
    metric, core = built(tmp_path, feature=feature).metric, FEATURES[feature]
    assert (metric.feature_id, metric.dimension) == (core.feature_id, core.dimension)
    assert (metric.unit, metric.polarity) == ("%", core.polarity)
    assert metric.native_resolution is NativeResolution.LSOA
    assert (metric.describes, metric.kind) == (core.describes, core.kind)


@pytest.mark.parametrize("feature", FIVE)
def test_the_row_of_the_catalogue_names_every_source_and_the_year(
    tmp_path: Path, feature: FeatureId
):
    metric = built(tmp_path, feature=feature).metric
    assert metric.source_ids == (
        "mhclg-land-use-statistics-2022",
        "ons-census-2021-housing-tables",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
    )
    assert (metric.vintage, metric.rankable) == (AS_AT, True)


def test_the_period_is_the_one_the_receipt_gives(tmp_path: Path):
    """The step reads no date in the table. The receipt states what a person read there."""
    later = built(tmp_path, period=Period(as_at="2022-05")).metric
    assert later.vintage == "2022-05" and "as at 2022-05" in later.definition


@pytest.mark.parametrize("feature", FIVE)
def test_the_definition_is_one_sentence_that_says_what_the_measure_is_and_is_not(
    tmp_path: Path, feature: FeatureId
):
    definition = built(tmp_path, feature=feature).metric.definition
    assert definition.endswith(".") and definition.count(". ") == 0 and "!" not in definition
    for said in (
        "Ordnance Survey",
        "Department for Levelling Up, Housing and Communities",
        "as at 2022,",
        "28 classes",
        "with a half taken upward",
        "an estimate",
        "nothing of who lives there",
    ):
        assert said in definition, said


@pytest.mark.parametrize("feature", FIVE)
def test_the_definition_says_a_hectare_is_kept_to_the_square_metre(
    tmp_path: Path, feature: FeatureId
):
    """The step keeps each figure of the table to four decimal places before it adds. Where a
    share stands on the edge of a tenth that moves it, so the definition must say it."""
    written = figures(n001={INDUSTRY: 0.50004, RESIDENTIAL: 0.39996})
    assert built(tmp_path / "kept", published(written)).sheet.hectares["E01999001"]["I"] == 0.5
    definition = built(tmp_path / "as", feature=feature).metric.definition
    assert "each figure kept to the square metre" in definition


@pytest.mark.parametrize("feature", FIVE)
def test_no_word_of_a_measure_says_who_lives_anywhere(tmp_path: Path, feature: FeatureId):
    of = land_use.MEASURES[feature]
    metric = built(tmp_path, feature=feature).metric
    said = " ".join([metric.label, metric.definition, *of.cannot_see, *of.waits_on]).lower()
    for word in ("resident", "people", "income", "poor", "rich", "deprived", "affluent"):
        assert word not in said.replace("residential", ""), word
    for word in ("gritty", "polished", "run down", "rough"):
        assert word not in said, word


@pytest.mark.parametrize("feature", FIVE)
def test_what_it_cannot_see_is_said_in_two_plain_sentences(feature: FeatureId):
    cannot_see = land_use.MEASURES[feature].cannot_see
    assert len(cannot_see) == 2
    for said in cannot_see:
        assert said.endswith(".") and "!" not in said and len(said) < 250
        # Each is one sentence.
        assert said.count(". ") == 0
    assert "share of all the land" in cannot_see[1]


# The vibes the measures are parts of


def test_works_and_warehouses_is_a_part_of_gritty_and_no_vibe_of_a_build():
    """A build carries Gritty, which holds land for industry and for storage at 15 each."""
    parts = {term.feature_id: term.hundredths for term in TAGS[TagId.WORKS_WAREHOUSES].terms}
    assert set(parts) == {F.LAND_INDUSTRY, F.LAND_STORAGE, F.LAND_TRANSPORT_OTHER}
    assert TagId.WORKS_WAREHOUSES not in {tag.tag_id for tag in tags_of(GrittyVariant.B)}
    gritty = {term.feature_id: term.hundredths for term in TAGS[TagId.STREET_CHARACTER].terms}
    assert (gritty[F.LAND_INDUSTRY], gritty[F.LAND_STORAGE]) == (15, 15)
    assert F.LAND_TRANSPORT_OTHER not in gritty


def test_leafy_is_whole_once_gardens_and_woodland_are_carried():
    parts = {term.feature_id: term.hundredths for term in TAGS[TagId.LEAFY].terms}
    assert parts[F.LAND_GARDENS] + parts[F.LAND_WOODLAND] == 70
    assert set(parts) - set(AS_CORE) == {F.GREEN_COVER}


# Joining the measures of a build


@pytest.mark.parametrize("feature", FIVE)
def test_each_measure_is_called_as_every_measure_of_a_build_is(tmp_path: Path, feature: FeatureId):
    """The list of measures is not changed here. Each of the five can join it as it stands."""
    of = land_use.MEASURES[feature]
    measure = Measure(
        feature,
        land_use.SOURCE,
        land_use.is_the_table,
        land_use.METHODS,
        of.cannot_see,
        land_use.builder(feature),
        waits_on=of.waits_on,
    )
    inputs = inputs_of(tmp_path, published())
    found = spine.build(inputs)
    made = measure.build(inputs, Ground(found, land.build(inputs, found)))
    assert {area: one.value for area, one in made.worked.items()} == WORKED_BY_HAND[feature]
    assert made.metric.feature_id is feature and made.geography is Geography.LSOA21
    assert bool(measure.waits_on) is not says_what_core_says(made.metric)


# The gate, the receipt and the store


def without_scoring() -> Registry:
    """The repository's registry, with the table no longer registered for scoring."""
    sources = [
        source.model_copy(update={"uses": (Use.DISPLAY,)}) if source.id == SOURCE else source
        for source in registry()
    ]
    return Registry(tuple(sources))


def test_the_source_is_the_one_the_registry_approves_for_scoring():
    assert land_use.SOURCE == SOURCE
    assert registry().require(SOURCE, Use.SCORING).id == SOURCE


def test_the_gate_is_asked_before_the_table_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, published(), using=without_scoring())
    found = spine.build(inputs)
    measured = land.build(inputs, found)
    before = inputs.opened
    with pytest.raises(LockError) as stopped:
        land_use.build(F.LAND_INDUSTRY, inputs, found, measured)
    assert (stopped.value.rule, stopped.value.subject) == ("gate_refuses", SOURCE)
    assert inputs.opened == before
    assert not any((tmp_path / "work").rglob("*.ods"))


def test_a_table_with_no_receipt_is_not_read(tmp_path: Path):
    """The file is in the store, as one is whose period the list is not sure of."""
    inputs = inputs_of(tmp_path, None)
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        land_use.build(F.LAND_INDUSTRY, inputs, found, land.build(inputs, found))
    assert (stopped.value.rule, stopped.value.subject) == ("input_has_one_receipt", SOURCE)
    assert not any((tmp_path / "work").rglob("*.ods"))


def test_another_file_of_the_publisher_is_not_taken_for_the_table(tmp_path: Path):
    inputs = inputs_of(tmp_path, published(), name="Live_Tables_-_Land_Use_Stock_2022.ods")
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        land_use.build(F.LAND_INDUSTRY, inputs, found, land.build(inputs, found))
    assert stopped.value.rule == "input_has_one_receipt"


def test_a_spine_of_another_build_is_refused(tmp_path: Path):
    """A row names the files of the spine, so they must be files this build opened."""
    other = inputs_of(tmp_path / "other", published())
    found = spine.build(other)
    measured = land.build(other, found)
    with pytest.raises(LockError) as stopped:
        land_use.build(F.LAND_INDUSTRY, inputs_of(tmp_path / "this", published()), found, measured)
    assert stopped.value.rule == "input_has_one_receipt"
    assert stopped.value.subject in found.inputs


def test_a_feature_that_is_no_share_of_land_is_refused():
    with pytest.raises(ValueError, match="no measure of land use"):
        land_use.builder(F.HOMES_DENSITY)


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path, published())
    before = held(tmp_path / "store")
    found = spine.build(inputs)
    land_use.build(F.LAND_INDUSTRY, inputs, found, land.build(inputs, found))
    assert held(tmp_path / "store") == before


def test_the_code_column_of_the_made_up_table_is_no_name_the_step_knows():
    """So that a test that passes shows the step found the codes by their shape."""
    known = {spelling.casefold() for one in land_use.CATEGORIES for spelling in one.spelt}
    assert CODE.casefold() not in known and TRANSPORT.casefold() in known
    assert {STORAGE.casefold(), GARDENS.casefold(), WOODLAND.casefold()} <= known
