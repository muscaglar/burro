"""Addresses with private outdoor space, worked out from the workbook its publisher gave.

Every other test of the measure runs on a made-up workbook. These read the real
one, and the real lookup between the areas of 2011 and of 2021 that every
figure is held to. They are skipped where the store of fetched files is not,
and until both files have their receipts in `data/receipts/`. The store is
named by BURRO_STORE_FOLDER, and each file is read through its receipt.

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
some areas of the build have no row, so the codes are not those of 2021. The
areas that have no row are the very areas that the lookup marks as split or
merged: `test_areas_of_2011_on_the_real_files.py` holds what the lookup holds.

The measure is held back from every release, until its row of the proxy audit
has passed. The last tests here hold what Houses or flats would be if it
joined, for whoever decides: the vibe is worked out with the measure and
without it, by the functions a build works a vibe out with, and nothing of it
is served.

The workbook's own words for its source: "Source: Ordnance Survey" and
"© Crown copyright and database rights 2020 OS 100019153". It is published
under the Open Government Licence v3.0, as its page says.

Nothing is written to the store. A file is copied out of it to be read.
"""

import statistics
from collections import Counter

import pytest
from burro_core.catalogue import TAGS
from burro_core.ids import FeatureId, TagId
from burro_core.release import TagValue
from burro_pipeline.assemble.release import Carried, features_of, tags_of
from burro_pipeline.cells import land, spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import private_outdoor_space as outdoor
from burro_pipeline.derive.areas_of_2011 import Mark
from burro_pipeline.derive.measures import MEASURES, Ground
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
        not ((RECEIPTS / outdoor.SOURCE).is_dir() and (RECEIPTS / outdoor.HELD_TO).is_dir()),
        reason="the workbook or the lookup it is held to has no receipt yet",
    ),
]
WORKBOOK, LOOKUP, HELD_TO = "f-e3d7ac61f751", "f-49321b95f212", "f-674387d9ace6"
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


def test_the_areas_with_no_row_are_the_areas_the_lookup_marks_as_changed(built: OutdoorSpace):
    """38 are parts of an area of 2011 that was split, and one was made by joining two. Every
    area the lookup marks as unchanged has its row, under the code it has."""
    assert Counter(built.drawn_again.values()) == {Mark.SPLIT: 38, Mark.MERGED: 1}
    assert set(built.drawn_again) == built.without_a_row


def test_the_workbook_holds_the_areas_of_2011_that_are_no_area_of_2021(
    built: OutdoorSpace, found: Spine
):
    """The 18 that were split and the two that were joined. So its codes are those of 2011."""
    ours = {area.code for area in found.areas}
    of_2011 = {pair.of_2011 for pair in built.changes.pairs}
    assert len(of_2011) == 983 and len(of_2011 - ours) == 20
    assert of_2011 <= set(built.table.of_area)


def test_were_a_split_carried_every_area_but_one_would_have_a_figure(
    built: OutdoorSpace, found: Spine
):
    """No build carries one. It is held here for whoever decides: the one area left is the
    area that was made by joining two."""
    asked = outdoor.figures(built.table, found, built.changes, {Mark.UNCHANGED, Mark.SPLIT})
    without = [area for area, one in asked.items() if one.value is None]
    assert len(without) == 1 and built.drawn_again[without[0]] is Mark.MERGED


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


def test_a_row_of_evidence_names_the_workbook_and_both_lookups(built: OutdoorSpace):
    assert {receipt.file_id for receipt in built.files} == {WORKBOOK, LOOKUP, HELD_TO}
    for row in built.rows:
        assert set(row.inputs) == {WORKBOOK, LOOKUP, HELD_TO}
    evidence = Evidence.of("lon-2026-09-24-01", built.files, outdoor.METHODS, built.rows)
    assert len(evidence.rows) == 1_002


def test_the_figure_is_as_at_the_month_the_page_names(built: OutdoorSpace):
    assert built.metric.vintage == "2020-04"
    assert "as at 2020-04" in built.metric.definition


# What Houses or flats would be if the measure joined. No release carries it.

HOMES = TAGS[TagId.HOMES]
# The two parts Houses or flats rests on today, which are 75 in 100 of its recipe.
RESTS_ON = (FeatureId.HOMES_DENSITY, FeatureId.HOMES_FLATS)


def ranks(values: list[float]) -> list[float]:
    """The rank of each value, with values that are level given the mean of their ranks."""
    order = sorted(range(len(values)), key=lambda index: values[index])
    found = [0.0] * len(values)
    at = 0
    while at < len(order):
        to = at
        while to + 1 < len(order) and values[order[to + 1]] == values[order[at]]:
            to += 1
        for index in order[at : to + 1]:
            found[index] = (at + to) / 2 + 1
        at = to + 1
    return found


def follows(one: dict[str, float | None], other: dict[str, float | None]) -> float:
    """The rank correlation of two figures over the areas that have both, to two places."""
    both = sorted(area for area in one if one[area] is not None and other[area] is not None)
    first = ranks([value for area in both if (value := one[area]) is not None])
    second = ranks([value for area in both if (value := other[area]) is not None])
    return to_places(statistics.correlation(first, second), 2)


@pytest.fixture(scope="module")
def today(real: Inputs, found: Spine) -> tuple[Carried, ...]:
    """The two measures of homes a build carries, worked out from the real files."""
    ground = Ground(found, land.build(real, found))
    wanted = [measure for measure in MEASURES if measure.feature in RESTS_ON]
    return tuple(Carried(measure, measure.build(real, ground)) for measure in wanted)


@pytest.fixture(scope="module")
def without(today: tuple[Carried, ...], found: Spine) -> dict[str, TagValue]:
    areas = sorted(area.area_id for area in found.areas)
    return {row.area_id: row for row in tags_of(features_of(today, areas), areas, [HOMES])}


@pytest.fixture(scope="module")
def with_it(today: tuple[Carried, ...], built: OutdoorSpace, found: Spine) -> dict[str, TagValue]:
    (measure,) = [one for one in MEASURES if one.feature is outdoor.FEATURE]
    areas = sorted(area.area_id for area in found.areas)
    carried = (*today, Carried(measure, built))
    return {row.area_id: row for row in tags_of(features_of(carried, areas), areas, [HOMES])}


def test_the_measure_follows_flats_more_than_it_follows_anything_else_of_homes(
    today: tuple[Carried, ...], built: OutdoorSpace
):
    """Where more homes are flats, fewer addresses have outdoor space of their own."""
    figure = {area: one.value for area, one in built.worked.items()}
    found = {
        one.feature: follows(figure, {a: w.value for a, w in one.measured.worked.items()})
        for one in today
    }
    assert found == {FeatureId.HOMES_DENSITY: -0.46, FeatureId.HOMES_FLATS: -0.77}


def test_with_the_measure_the_vibe_would_rest_on_its_whole_recipe_in_963_areas(
    without: dict[str, TagValue], with_it: dict[str, TagValue]
):
    assert Counter(row.coverage for row in without.values()) == {0.75: 1_002}
    assert Counter(row.coverage for row in with_it.values()) == {1.0: 963, 0.75: 39}
    assert all(row.band is not None for row in (*without.values(), *with_it.values()))


def test_with_the_measure_one_area_in_five_would_move_one_band_and_none_would_move_two(
    without: dict[str, TagValue], with_it: dict[str, TagValue]
):
    """Band 5 is the end of flats. As many areas would move towards it as away from it."""
    moved = Counter((with_it[area].band or 0) - (without[area].band or 0) for area in without)
    assert moved == {0: 800, 1: 101, -1: 101}
    order = follows(
        {area: row.raw for area, row in without.items()},
        {area: row.raw for area, row in with_it.items()},
    )
    assert order == 0.98
    for band, in_both in ((1, 179), (5, 177)):
        before = {area for area, row in without.items() if row.band == band}
        after = {area for area, row in with_it.items() if row.band == band}
        assert len(before & after) == in_both
    # Where an area stands among the areas, in 100: how far it would move.
    by = sorted(abs((with_it[area].score or 0) - (without[area].score or 0)) for area in without)
    found = (statistics.median(by), by[int(0.9 * len(by))], by[-1])
    assert tuple(to_places(one, 1) for one in found) == (3.9, 10.3, 16.9)


def test_the_areas_with_no_figure_stand_towards_the_end_of_flats(
    built: OutdoorSpace, without: dict[str, TagValue], with_it: dict[str, TagValue]
):
    """They would rest on 75 in 100 still. 38 of the 39 would keep the band they have, and
    one would move a band towards flats, because the areas round it moved."""
    none = sorted(area for area, one in built.worked.items() if one.value is None)
    assert Counter(without[area].band for area in none) == {2: 3, 3: 4, 4: 11, 5: 21}
    assert Counter(with_it[area].band for area in none) == {2: 3, 3: 4, 4: 10, 5: 22}
    moved = Counter((with_it[area].band or 0) - (without[area].band or 0) for area in none)
    assert moved == {0: 38, 1: 1}
    assert {with_it[area].coverage for area in none} == {0.75}
