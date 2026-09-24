"""Addresses with private outdoor space, from a made-up workbook.

Every figure here is made up. The town is the made-up town of the tests of
cells: three areas, each an MSOA.

The workbook is laid out as the publisher lays out its own, which was read as
it is stored on 2026-09-24. It has the publisher's five sheets under their own
names, and the sheet that is read has its 26 columns. Their names stand in two
rows: the first names the columns that say which area a row is of, and holds a
heading for houses, for flats and for both; the second holds, under each
heading, the names of its counts, which are the same under each. The sheet
merges each heading across its columns. Under the rows of areas stand an empty
row and two lines of the publisher's, in the first column.

The four sheets that are never opened are not well formed, and hold a canary.
The counts of houses and of flats are a number found nowhere else.

    area             row         addresses   with private outdoor space
    Quillhaven 001   E02999001      500           400          80 in 100
    Quillhaven 002   E02999002      300           100          33.3 in 100
    Tallowgate 001   no row: it was drawn again for the census of 2021
"""

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, TAGS
from burro_core.ids import FeatureId, TagId
from burro_pipeline.cells import spine
from burro_pipeline.derive import private_outdoor_space as outdoor
from burro_pipeline.derive.measures import MEASURES, says_what_core_says
from burro_pipeline.derive.methods import AREA_ROW_RATIO, Worked
from burro_pipeline.derive.private_outdoor_space import Counted, OutdoorSpace
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.fetch.sources import load_list
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Status, Use

from ..cells.support import CANARY, contents, held, inputs_of, receipt_of, registry
from .noise_support import NOT_WELL_FORMED, Cell, Table, letters, workbook

ONE, TWO, THREE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
# The files of the list: the workbook, and the lookup between the areas of two censuses.
LISTED = load_list("m11-outdoor-space").files
NEVER_OPENED = ("Readme", "Country gardens", "Region gardens", "LAD gardens")
# The columns that say which area a row is of. One is read.
KEYS = (
    "Country code",
    "Country name",
    "Region code",
    "Region name",
    "LAD code",
    "LAD name",
    outdoor.CODE,
    "MSOA name",
)
SHARE = "Percentage of adresses with private outdoor space"
AREA, MEAN = "Private outdoor space total area (m2)", "Average size of private outdoor space (m2)"
# The three headings, and the names under each, as the publisher spells them.
HOUSES = "Property type: Houses"
FLATS = "Property type: Flats"
UNDER_HOUSES = (
    outdoor.ADDRESSES,
    outdoor.WITH_SPACE,
    AREA,
    SHARE,
    MEAN,
    "Median size of private outdoor space (m2)",
)
UNDER_FLATS = (
    outdoor.ADDRESSES,
    outdoor.WITH_SPACE,
    AREA,
    "Private outdoor space count",
    SHARE,
    MEAN,
    "Average number of flats sharing a garden",
)
UNDER_TOTAL = (outdoor.ADDRESSES, outdoor.WITH_SPACE, AREA, SHARE, MEAN)
Groups = Sequence[tuple[str, Sequence[str]]]
GROUPS: Groups = ((HOUSES, UNDER_HOUSES), (FLATS, UNDER_FLATS), (outdoor.TOTAL, UNDER_TOTAL))
# The two lines the publisher writes under the rows of areas, in the first column.
UNDER_THE_TABLE = ("Source: a mapping agency, as made up for a test", CANARY)
# A number found nowhere else. It stands in every column of figures that is not read.
CANARY_NUMBER = 987654.0
# For each row: the count of addresses, and of those with private outdoor space.
Counts = tuple[Cell, Cell]
AREAS: Mapping[str, Counts] = {
    "E02999001": (500, 400),
    "E02999002": (300, 100),
    # Outside London, in Wales and in Scotland. None is part of any area.
    "E02999901": (700, 700),
    "W02999001": (90, 45),
    "S02999001": (80, 40),
}


def row_of_area(
    code: Cell, counts: Counts, keys: Sequence[str] = KEYS, groups: Groups = GROUPS
) -> list[Cell]:
    """A row of the sheet: the area it is of, and its counts under each heading."""
    row: list[Cell] = [code if name == outdoor.CODE else CANARY for name in keys]
    for heading, names in groups:
        under: dict[str, Cell] = dict.fromkeys(names, CANARY_NUMBER)
        if heading == outdoor.TOTAL:
            under |= {outdoor.ADDRESSES: counts[0], outdoor.WITH_SPACE: counts[1]}
        row.extend(under[name] for name in names)
    return row


def merged_of(keys: Sequence[str] = KEYS, groups: Groups = GROUPS) -> list[str]:
    """The cells the sheet merges: a key down its two rows, a heading across its columns."""
    found = [f"{letters(column)}1:{letters(column)}2" for column in range(len(keys))]
    first = len(keys)
    for _, names in groups:
        found.append(f"{letters(first)}1:{letters(first + len(names) - 1)}1")
        first += len(names)
    return found


def sheet_of(
    areas: Mapping[str, Counts] = AREAS,
    *,
    keys: Sequence[str] = KEYS,
    groups: Groups = GROUPS,
    more: Sequence[Sequence[Cell]] = (),
) -> list[list[Cell]]:
    """The sheet that is read: its two rows of names, a row for each area, and what is under."""
    top: list[Cell] = [*keys]
    below: list[Cell] = [None] * len(keys)
    for heading, names in groups:
        top.extend([heading, *[None] * (len(names) - 1)])
        below.extend(names)
    rows = [row_of_area(code, counts, keys, groups) for code, counts in areas.items()]
    under: list[list[Cell]] = [[], *([line] for line in UNDER_THE_TABLE)]
    return [top, below, *rows, *(list(row) for row in more), *under]


def made_up(
    areas: Mapping[str, Counts] = AREAS,
    *,
    keys: Sequence[str] = KEYS,
    groups: Groups = GROUPS,
    more: Sequence[Sequence[Cell]] = (),
    merged: Sequence[str] | None = None,
    sheets: Mapping[str, Table | bytes] | None = None,
) -> bytes:
    """The made-up workbook: four sheets that are never opened, and the one that is read."""
    every: dict[str, Table | bytes] = dict.fromkeys(NEVER_OPENED, NOT_WELL_FORMED)
    every[outdoor.SHEET] = sheet_of(areas, keys=keys, groups=groups, more=more)
    every |= sheets or {}
    given = merged_of(keys, groups) if merged is None else merged
    return workbook(every, merged={outdoor.SHEET: given})


def inputs_with(
    folder: Path,
    content: bytes | None = None,
    *,
    period: Period | None = None,
    **changes: Registry,
) -> Inputs:
    """The made-up build of the tests of cells, and the workbook beside it."""
    given = inputs_of(folder, contents(), **changes)
    content = made_up() if content is None else content
    path = folder / "given" / outdoor.FILE_NAME
    path.write_bytes(content)
    given.store.put(outdoor.SOURCE, outdoor.FILE_NAME, path)
    receipt = receipt_of(
        outdoor.SOURCE, Use.SCORING, outdoor.FILE_NAME, content, outdoor.EDITION
    ).model_copy(update={"data_period": period or Period(as_at="2020-04")})
    return Inputs(given.registry, [*given.receipts, receipt], given.store, given.work)


def built(folder: Path, areas: Mapping[str, Counts] = AREAS) -> OutdoorSpace:
    inputs = inputs_with(folder, made_up(areas))
    return outdoor.build(inputs, spine.build(inputs))


def refused(folder: Path, content: bytes) -> LockError:
    """The refusal of a workbook, which repeats nothing the workbook holds."""
    inputs = inputs_with(folder, content)
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        outdoor.build(inputs, found)
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return stopped.value


# The figure


def test_the_share_is_the_addresses_with_outdoor_space_over_the_addresses_of_the_area(
    tmp_path: Path,
):
    found = built(tmp_path).worked
    assert found == {
        ONE: Worked(80.0, 1, 1, 1.0, State.PRESENT),
        TWO: Worked(33.3, 1, 1, 1.0, State.PRESENT),
        THREE: Worked(None, 0, 1, 0.0, State.SOURCE_GAP),
    }


def test_a_share_that_stands_on_a_half_is_rounded_upward(tmp_path: Path):
    """1 address of 16 is 6.25 in 100, which a person who rounds by hand gives as 6.3."""
    assert built(tmp_path, {**AREAS, "E02999001": (16, 1)}).worked[ONE].value == 6.3


def test_a_count_of_nought_is_a_count(tmp_path: Path):
    found = built(tmp_path, {**AREAS, "E02999001": (500, 0)}).worked[ONE]
    assert found == Worked(0.0, 1, 1, 1.0, State.PRESENT)


def test_every_address_with_outdoor_space_is_the_whole(tmp_path: Path):
    assert built(tmp_path, {**AREAS, "E02999001": (500, 500)}).worked[ONE].value == 100.0


def test_the_counts_are_kept_as_the_workbook_holds_them(tmp_path: Path):
    found = built(tmp_path).table
    assert found.of_area["E02999001"] == Counted(addresses=500, with_space=400)
    assert set(found.of_area) == set(AREAS)
    assert found.rows == len(AREAS)
    assert CANARY_NUMBER not in {
        count for one in found.of_area.values() for count in (one.addresses, one.with_space)
    }


# An area with no row, and a row with no count


def test_an_area_that_was_drawn_again_has_no_row_and_no_figure(tmp_path: Path):
    """The workbook is older than the areas of 2021. Nothing is shared out to one it lacks."""
    found = built(tmp_path)
    assert found.without_a_row == {THREE}
    assert found.worked[THREE] == Worked(None, 0, 1, 0.0, State.SOURCE_GAP)
    row = next(row for row in found.rows if row.area_id == THREE)
    assert (row.state, row.has_a_value) == (State.SOURCE_GAP, False)


def test_an_area_of_another_country_is_read_and_is_part_of_no_figure(tmp_path: Path):
    found = built(tmp_path)
    assert found.table.of_area["W02999001"] == Counted(90, 45)
    assert found.table.of_area["S02999001"] == Counted(80, 40)
    assert set(found.worked) == {ONE, TWO, THREE}


@pytest.mark.parametrize("counts", [(None, 400), (500, None), (None, None)])
def test_an_empty_cell_is_no_count_and_is_never_nought(tmp_path: Path, counts: Counts):
    found = built(tmp_path, {**AREAS, "E02999001": counts})
    assert found.worked[ONE] == Worked(None, 0, 1, 0.0, State.SOURCE_GAP)
    assert ONE not in found.without_a_row


def test_an_area_with_no_address_has_no_figure(tmp_path: Path):
    found = built(tmp_path, {**AREAS, "E02999001": (0, 0)})
    assert found.worked[ONE].value is None
    assert found.worked[ONE].state is State.SOURCE_GAP


def test_a_workbook_that_holds_no_area_of_the_build_stops_the_build(tmp_path: Path):
    """It is then keyed by something else, and every area would read as a gap."""
    elsewhere = {code: counts for code, counts in AREAS.items() if not code.startswith("E02999")}
    elsewhere |= {"E02999901": (700, 700)}
    assert "no area of the build has a row" in str(refused(tmp_path, made_up(elsewhere)))


# What stops the build


@pytest.mark.parametrize(
    "counts",
    [(CANARY, 400), (500, "c"), (500, "-"), (-500, 400), (500.5, 400), (500, 0.8)],
)
def test_a_cell_that_is_no_count_stops_the_build(tmp_path: Path, counts: Counts):
    """No page says how the publisher marks a count it withholds, so no mark is read as one."""
    error = refused(tmp_path, made_up({**AREAS, "E02999001": counts}))
    assert "a count is not a count" in str(error)


def test_more_addresses_with_outdoor_space_than_addresses_stops_the_build(tmp_path: Path):
    error = refused(tmp_path, made_up({**AREAS, "E02999001": (500, 510)}))
    assert "a share is more than the whole" in str(error)


def test_an_area_that_is_there_twice_stops_the_build(tmp_path: Path):
    twice = [row_of_area("E02999002", (300, 100))]
    assert "twice" in str(refused(tmp_path, made_up(more=twice)))


@pytest.mark.parametrize("code", [None, "Zzyzx-001", "E02", "E0299900", "E01999001"])
def test_a_row_that_holds_a_count_and_no_code_of_an_area_stops_the_build(
    tmp_path: Path, code: Cell
):
    odd = [row_of_area(code, (300, 100))]
    error = refused(tmp_path, made_up(more=odd))
    assert "a row holds a count and no code of an area" in str(error)
    assert "Zzyzx" not in str(error)


def test_the_lines_under_the_table_are_no_row_of_it(tmp_path: Path):
    """The publisher writes its source and its rights under the rows, in the first column."""
    found = built(tmp_path)
    assert set(found.table.of_area) == set(AREAS)
    assert found.table.rows == len(AREAS)


def test_a_line_in_the_column_of_codes_is_no_row_of_it(tmp_path: Path):
    note = [row_of_area(CANARY, (None, None))]
    inputs = inputs_with(tmp_path, made_up(more=note))
    found = outdoor.build(inputs, spine.build(inputs))
    assert found.worked == built(tmp_path / "plain").worked
    assert set(found.table.of_area) == set(AREAS)


def test_the_counts_of_houses_and_of_flats_are_never_read(tmp_path: Path):
    """The sheet names a count of addresses three times. The one under both is read."""
    (names,) = [row for row in sheet_of()[1:2]]
    assert names.count(outdoor.ADDRESSES) == names.count(outdoor.WITH_SPACE) == 3
    found = built(tmp_path)
    assert found.table.of_area["E02999001"] == Counted(addresses=500, with_space=400)


def test_the_headings_may_stand_in_another_order(tmp_path: Path):
    turned = (GROUPS[2], GROUPS[0], GROUPS[1])
    inputs = inputs_with(tmp_path, made_up(groups=turned))
    found = outdoor.build(inputs, spine.build(inputs))
    assert found.worked == built(tmp_path / "plain").worked


def without(name: str) -> bytes:
    """The made-up workbook, without one of the names the step asks for."""
    if name == outdoor.CODE:
        return made_up(keys=[key for key in KEYS if key != name])
    less = [one for one in UNDER_TOTAL if one != name]
    return made_up(groups=(*GROUPS[:2], (outdoor.TOTAL, less)))


@pytest.mark.parametrize("missing", outdoor.COLUMNS)
def test_a_sheet_that_lacks_a_column_stops_the_build_and_says_which(tmp_path: Path, missing: str):
    """A count that is named under houses or under flats is no count of both."""
    assert f"the column {missing} is missing" in str(refused(tmp_path, without(missing)))


def test_a_sheet_that_lacks_the_heading_stops_the_build_and_says_which(tmp_path: Path):
    error = refused(tmp_path, made_up(groups=GROUPS[:2]))
    assert f"the heading {outdoor.TOTAL} is missing" in str(error)


def test_a_heading_the_sheet_merges_over_no_column_stops_the_build(tmp_path: Path):
    """What a heading stands over is what the sheet says, and never where the next begins."""
    merged = [one for one in merged_of() if not one.startswith("V1")]
    error = refused(tmp_path, made_up(merged=merged))
    assert "a heading stands over no columns" in str(error)


def test_a_count_that_is_named_twice_under_the_heading_stops_the_build(tmp_path: Path):
    twice = (*GROUPS[:2], (outdoor.TOTAL, (*UNDER_TOTAL, outdoor.ADDRESSES)))
    error = refused(tmp_path, made_up(groups=twice))
    assert f"the column {outdoor.ADDRESSES} is there twice" in str(error)


def test_a_workbook_with_no_sheet_of_the_name_stops_the_build(tmp_path: Path):
    content = workbook({"Readme": NOT_WELL_FORMED, "MSOA parks": sheet_of()})
    assert "the one sheet that is read" in str(refused(tmp_path, content))


def test_a_sheet_with_no_row_of_an_area_stops_the_build(tmp_path: Path):
    assert "no row of an area" in str(refused(tmp_path, made_up({})))


def test_a_file_that_is_no_workbook_stops_the_build(tmp_path: Path):
    assert "not a workbook" in str(refused(tmp_path, CANARY.encode()))


def test_no_other_sheet_is_opened(tmp_path: Path):
    """The other sheets of the made-up workbook are not well formed, and hold a canary."""
    found = built(tmp_path)
    assert found.worked[ONE].value == 80.0


# The gate, and what is read


def without_scoring() -> Registry:
    """The repository's registry, with the workbook no longer registered for scoring."""
    sources = [
        source.model_copy(update={"uses": (Use.DISPLAY,)})
        if source.id == outdoor.SOURCE
        else source
        for source in registry()
    ]
    return Registry(tuple(sources))


def test_the_gate_is_asked_before_the_workbook_is_read(tmp_path: Path):
    inputs = inputs_with(tmp_path, registry=without_scoring())
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        outdoor.build(inputs, found)
    assert stopped.value.rule == "gate_refuses"
    assert all(one.receipt.source_id != outdoor.SOURCE for one in inputs.opened)


def test_the_workbook_is_registered_for_scoring_on_its_publishers_own_pages():
    source = registry().get(outdoor.SOURCE)
    assert source.status is Status.APPROVED
    assert Use.SCORING in source.uses
    assert source.dimension == "housing"
    assert source.url in source.evidence_urls
    assert len(source.file_urls) == 1 and source.file_urls[0].endswith(outdoor.FILE_NAME)


def test_the_registry_keeps_the_survey_of_people_out_and_asks_for_the_audit():
    """The same page offers a survey of people by age and ethnic group. It is never read."""
    source = registry().get(outdoor.SOURCE)
    said = " ".join(source.conditions)
    for words in ("describes residents", "never fetched", "proxy audit", "ADR 0006"):
        assert words in said, words
    assert "2014" not in " ".join(source.file_urls)
    assert any("proxy audit" in line for line in source.before_launch)


def test_the_lookup_between_the_censuses_is_registered_for_cells_and_nothing_else():
    """It says which areas kept their outline. No figure is worked out from it."""
    source = registry().get(outdoor.HELD_TO)
    assert source.status is Status.APPROVED
    assert source.uses == (Use.CELLS,)
    assert source.dimension == "geography"
    assert source.url in source.evidence_urls
    said = " ".join(source.conditions)
    for words in ("Never use it to share a figure out", "registered for cells alone"):
        assert words in said, words
    workbook = registry().get(outdoor.SOURCE)
    assert outdoor.HELD_TO in " ".join(workbook.conditions)
    assert any(outdoor.HELD_TO in line for line in workbook.before_launch)


def test_the_list_names_the_lookup_and_is_sure_of_nothing_that_nobody_has_read():
    """Its first fetch stores the file and writes no receipt."""
    (listed,) = (one for one in LISTED if one.source_id == outdoor.HELD_TO)
    source = registry().get(outdoor.HELD_TO)
    assert listed.use is Use.CELLS
    assert str(listed.page) == source.url
    assert any(str(listed.url).startswith(prefix) for prefix in source.file_urls)
    assert {"url", "edition", "data_period"} <= set(listed.unsure)
    assert not listed.ready_for_a_receipt
    for words in ("CHGIND", "963", "Nobody has read"):
        assert words in listed.notes, words


def test_the_measure_reads_no_lookup_between_the_censuses(tmp_path: Path):
    """A figure is the row of the area's own code, or there is none."""
    inputs = inputs_with(tmp_path)
    outdoor.build(inputs, spine.build(inputs))
    assert outdoor.HELD_TO not in {one.receipt.source_id for one in inputs.opened}


def test_the_list_names_the_one_workbook_and_states_what_was_read_of_it():
    """The edition and the period are stated, and where each was read, so a fetch writes a
    receipt. The period is the page's: the workbook states no month."""
    (listed,) = (one for one in LISTED if one.source_id == outdoor.SOURCE)
    source = registry().get(outdoor.SOURCE)
    assert (listed.source_id, listed.use, listed.edition) == (
        outdoor.SOURCE,
        Use.SCORING,
        outdoor.EDITION,
    )
    assert str(listed.url) in source.file_urls and str(listed.page) == source.url
    assert str(listed.url).endswith(outdoor.FILE_NAME)
    assert listed.unsure == () and listed.ready_for_a_receipt
    assert listed.data_period == Period(as_at="2020-04")
    for words in ("states no month", "epoch 74", outdoor.TOTAL, outdoor.WITH_SPACE):
        assert words in listed.notes, words


def test_a_workbook_of_another_name_is_not_taken_for_this_one(tmp_path: Path):
    given = inputs_with(tmp_path)
    other = [
        receipt.model_copy(update={"publisher_file": "ospublicgreenspacereferencetables.xlsx"})
        if receipt.source_id == outdoor.SOURCE
        else receipt
        for receipt in given.receipts
    ]
    inputs = Inputs(given.registry, other, given.store, given.work)
    with pytest.raises(LockError) as stopped:
        outdoor.build(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_has_one_receipt"


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_with(tmp_path)
    before = held(tmp_path / "store")
    outdoor.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before


def test_the_same_files_give_the_same_figures(tmp_path: Path):
    first, second = built(tmp_path / "a"), built(tmp_path / "b")
    assert (first.worked, first.rows, first.metric) == (second.worked, second.rows, second.metric)


def test_a_spine_of_another_build_is_refused(tmp_path: Path):
    other = spine.build(inputs_of(tmp_path / "other", contents()))
    inputs = inputs_with(tmp_path / "this")
    with pytest.raises(ValueError, match="files of this build"):
        outdoor.build(inputs, other)


# The evidence


def test_every_area_has_a_row_of_evidence_whether_or_not_it_has_a_figure(tmp_path: Path):
    found = built(tmp_path)
    assert [row.fact_id for row in found.rows] == [
        f"{area}/feature/private_outdoor_space" for area in (ONE, TWO, THREE)
    ]
    assert [row.state for row in found.rows] == [State.PRESENT, State.PRESENT, State.SOURCE_GAP]
    assert [row.has_a_value for row in found.rows] == [True, True, False]


def test_a_row_names_the_workbook_and_the_lookup(tmp_path: Path):
    found = built(tmp_path)
    sources = {receipt.source_id: receipt.file_id for receipt in found.files}
    assert set(sources) == {outdoor.SOURCE, spine.LOOKUP}
    for row in found.rows:
        assert set(row.inputs) == set(sources.values())
        assert row.derivation_id == AREA_ROW_RATIO.derivation_id
        assert row.units_expected == 1
    assert found.table.file_id == sources[outdoor.SOURCE]
    # The workbook's codes are not those of 2021, and the build finds a row by a code.
    assert found.geography is Geography.MSOA11


def test_the_evidence_of_the_measure_has_no_loose_end(tmp_path: Path):
    found = built(tmp_path)
    evidence = Evidence.of("lon-2026-09-23-01", found.files, outdoor.METHODS, found.rows)
    assert len(evidence.rows) == 3
    method = evidence.method(found.rows[0].derivation_id or "")
    assert method is not None and method.kind is Kind.MEASURED


# The name, and what the measure waits on


def test_the_name_says_addresses_and_is_not_core_s_so_a_build_leaves_it_out(tmp_path: Path):
    """Core names it for homes. The workbook counts addresses, as at April 2020."""
    metric = built(tmp_path).metric
    core = FEATURES[FeatureId.PRIVATE_OUTDOOR_SPACE]
    assert core.label == "Homes with private outdoor space"
    assert metric.label == "Addresses with private outdoor space"
    assert (metric.unit, metric.polarity, metric.dimension) == (
        core.unit,
        core.polarity,
        core.dimension,
    )
    assert not says_what_core_says(metric)
    assert metric.vintage == "2020-04"
    assert metric.source_ids == (outdoor.SOURCE, spine.LOOKUP)


def test_the_measure_is_not_yet_on_the_list_of_a_build():
    """It joins `derive/measures.py` when what it waits on is settled."""
    assert FeatureId.PRIVATE_OUTDOOR_SPACE not in {measure.feature for measure in MEASURES}
    assert outdoor.SOURCE not in {measure.source for measure in MEASURES}


def test_it_says_what_it_waits_on_and_whose_each_is_to_settle():
    said = " ".join(outdoor.WAITS_ON)
    for words in ("names no census", "lookup", "addresses", "proxy audit", "founder"):
        assert words in said, words
    for line in outdoor.WAITS_ON:
        assert line.endswith(".")


def test_it_is_a_quarter_of_the_recipe_of_homes_which_has_a_band_without_it():
    """Flats and homes per hectare are 75 in 100 of Homes. This is the rest."""
    parts = {term.feature_id: term.hundredths for term in TAGS[TagId.HOMES].terms}
    assert parts[FeatureId.PRIVATE_OUTDOOR_SPACE] == 25
    assert sum(parts.values()) - parts[FeatureId.PRIVATE_OUTDOOR_SPACE] == 75


def test_the_definition_is_one_sentence_that_states_what_it_is_made_with(tmp_path: Path):
    definition = built(tmp_path).metric.definition
    stated = Method(
        derivation_id="private_outdoor_space@1",
        sentence=definition,
        kind=Kind.MEASURED,
        parameters={"decimal_places": 1, "census": 2021},
        code="burro_pipeline.derive.private_outdoor_space",
    )
    assert stated.sentence == definition
    for words in (
        "Office for National Statistics",
        "Ordnance Survey",
        "as at 2020-04",
        "not added up from smaller areas",
        "never nought",
        "addresses and not homes",
        "nothing of who lives at one",
    ):
        assert words in definition, words


def test_what_it_cannot_see_is_two_sentences_that_name_no_place():
    assert len(outdoor.CANNOT_SEE) == 2
    for line in outdoor.CANNOT_SEE:
        assert line.endswith(".") and line.count(". ") == 0
        assert "London" not in line
