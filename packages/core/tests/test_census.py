"""The census of an area's page: what is served of it, and what can never reach it.

Two things are held here. How a figure is shown, so that it reads as a
description and not a verdict. And that nothing which ranks, explains, compares
or reads a sentence can be handed a census at all.
"""

import ast
import copy
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast, get_type_hints

import burro_core
import pytest
from burro_core.census import (
    BEARS_ON,
    CENSUS,
    CENSUS_2021,
    FEWER,
    FLOOR,
    MADE_UP,
    MANIFEST,
    NEARLY_ALL,
    NEVER_SAID,
    NO_CENSUS,
    RULES,
    SHOWN_AND_NEVER_RANKED_ON,
    Census,
    CensusError,
    CensusKind,
    CensusLeftOut,
    CensusPanel,
    CensusPanelRow,
    CensusPanelTable,
    Words,
    base_in_words,
    day_in_words,
    offer,
    open_census,
    panel,
    parse_census,
    percent_of,
    share_in_words,
)
from burro_core.ids import (
    Describes,
    Dimension,
    FactKind,
    FeatureId,
    Setting,
    TagId,
    TemplateId,
    UnmetCategory,
)
from burro_core.ops import Operations
from burro_core.release import DATA_FILES, InMemoryRelease, Release, ReleaseError, open_release
from burro_core.spec import PreferenceSpec

from .counted import (
    AREAS,
    CANARY_LABEL,
    CITY,
    FOLDER,
    NAME,
    as_bytes,
    committed_bytes,
    document,
    files,
    opened,
)
from .support import RELEASE_ID, fixture_release

SOURCE = Path(burro_core.__file__).parent
Document = dict[str, Any]
Break = Callable[[Document], object]


def shown(area: int = 0) -> CensusPanel:
    found = panel(opened(), AREAS[area], NAME)
    assert found is not None
    return found


def table_of(found: CensusPanel, kind: CensusKind) -> CensusPanelTable:
    return next(table for table in found.tables if table.kind is kind)


def row_of(found: CensusPanel, kind: CensusKind, code: str) -> CensusPanelRow:
    return next(row for row in table_of(found, kind).rows if row.code == code)


# --- What is shown ----------------------------------------------------------------


def test_a_figure_is_a_share_with_its_count():
    row = row_of(shown(), CensusKind.AGE, "age-0")
    assert (row.share, row.percent, row.count) == ("36%", 36, "1,437")


def test_a_figure_stands_beside_the_citys_figure_for_the_same_thing():
    found = shown()
    row = row_of(found, CensusKind.AGE, "age-0")
    assert (row.city_share, row.city_percent) == ("40%", 40)
    assert found.city == CITY
    assert table_of(found, CensusKind.AGE).columns.city == CITY


def test_nothing_else_stands_beside_a_figure():
    """The record has no room for another area, a rank, a band or a word about the figure."""
    assert set(CensusPanelRow.model_fields) == {
        "code",
        "heading",
        "label",
        "depth",
        "share",
        "percent",
        "count",
        "city_share",
        "city_percent",
    }
    # What is said of the city is its share, and never how many were counted in it.
    assert not [name for name in CensusPanelRow.model_fields if "city" in name and "count" in name]
    for record in (CensusPanel, CensusPanelTable, CensusPanelRow):
        names = " ".join(record.model_fields)
        for word in ("rank", "band", "score", "percentile", "other", "neighbour", "similar"):
            assert word not in names, (record.__name__, word)


def test_every_table_says_which_census_it_is_from_and_its_day():
    found = shown()
    assert "21 March 2021" in found.date_line
    for table in found.tables:
        assert "21 March 2021" in table.caption
        assert NAME in table.caption and CITY in table.caption


def test_every_table_says_the_area_it_is_for_and_how_many_were_counted():
    caption = table_of(shown(), CensusKind.AGE).caption
    assert f"in {NAME}" in caption
    assert "About 4,000 people counted" in caption


def test_a_base_is_said_to_the_nearest_hundred():
    assert [base_in_words(base) for base in (1_000, 4_040, 4_051, 19_449)] == [
        "1,000",
        "4,000",
        "4,100",
        "19,400",
    ]


def test_one_small_area_is_said_as_one():
    found = document()
    found["areas"][0]["output_areas"] = 1
    one = panel(parse_census(found, RELEASE_ID, True, AREAS), AREAS[0], NAME)
    assert one is not None
    assert one.notes[2].startswith(f"{NAME} is drawn by Burro from 1 made-up small area.")
    assert one.derivation_line.startswith(
        f"Added up by Burro over the 1 made-up small area of {NAME}."
    )
    many = shown()
    assert many.notes[2].startswith(f"{NAME} is drawn by Burro from 12 made-up small areas.")
    assert "over the 12 made-up small areas of" in many.derivation_line


def test_a_day_is_said_in_words():
    assert day_in_words("2021-03-21") == "21 March 2021"
    assert day_in_words("2026-09-03") == "3 September 2026"


def test_a_share_is_a_whole_number_and_a_tie_goes_to_the_even_one():
    assert [percent_of(count, 1_000) for count in (25, 35, 154, 155)] == [2, 4, 15, 16]


def test_a_share_reads_a_hundred_only_where_every_one_counted_is_in_it():
    assert share_in_words(3_000, 3_000) == ("100%", 100)
    assert share_in_words(2_990, 3_000) == (NEARLY_ALL, 99)
    assert share_in_words(2_960, 3_000) == ("99%", 99)
    assert row_of(shown(1), CensusKind.ETHNIC_GROUP, "grp-a").share == NEARLY_ALL


def test_rows_are_in_the_order_the_census_holds_them_and_never_by_size():
    found = document()
    codes = [row["code"] for row in found["tables"][1]["rows"]]
    served = [row.code for row in table_of(shown(), CensusKind.ETHNIC_GROUP).rows]
    assert served == codes
    # The second row is larger than the third, and the fourth smaller than all: the order
    # of the census stands whichever way the figures run.
    turned = copy.deepcopy(found)
    turned["areas"][0]["tables"][1]["counts"] = [4_010, 1_485, 2_525, None]
    again = panel(parse_census(turned, RELEASE_ID, True, AREAS), AREAS[0], NAME)
    assert again is not None
    assert [row.code for row in table_of(again, CensusKind.ETHNIC_GROUP).rows] == codes


def test_a_row_is_read_whole_by_a_screen_reader_and_printed_under_its_group():
    row = row_of(shown(), CensusKind.ETHNIC_GROUP, "grp-a1")
    assert (row.heading, row.label, row.depth) == ("Made-up group A: First part", "First part", 1)


def test_the_tables_come_in_the_order_the_census_holds_them():
    assert [table.kind for table in shown().tables] == [CensusKind.AGE, CensusKind.ETHNIC_GROUP]


# --- Small numbers ----------------------------------------------------------------


def test_a_share_under_one_in_a_hundred_is_said_in_words_with_no_count():
    row = row_of(shown(), CensusKind.ETHNIC_GROUP, "grp-z")
    assert (row.share, row.percent, row.count) == (FEWER, None, None)
    assert FEWER == "fewer than 1 in 100"


def test_nothing_reads_nought_or_none():
    for area in range(2):
        for table in shown(area).tables:
            for row in table.rows:
                assert row.share not in ("0%", "none", "None", "")
                assert row.count not in ("0", "")


def test_no_count_under_ten_can_be_held():
    """A table needs a thousand counted, and a count needs 1 in 100 of them: so ten at least."""
    assert FLOOR == 1_000
    found = document()
    found["areas"][0]["tables"][0].update(base=FLOOR, counts=[9, 900, 91])
    with pytest.raises(CensusError) as caught:
        parse_census(found, RELEASE_ID, True, AREAS)
    assert caught.value.rule == "small_counts_are_withheld"
    found["areas"][0]["tables"][0].update(base=FLOOR, counts=[10, 900, 90])
    parse_census(found, RELEASE_ID, True, AREAS)


def test_a_table_is_left_out_where_too_few_were_counted_and_says_so():
    found = shown(2)
    age = table_of(found, CensusKind.AGE)
    assert (age.reason, age.rows) == (CensusLeftOut.TOO_FEW, ())
    assert age.left_out == (
        f"Age, made up. Too few people lived in {NAME} on the day for Burro to give shares."
    )
    group = table_of(found, CensusKind.ETHNIC_GROUP)
    assert (group.reason, group.rows) == (CensusLeftOut.NOT_HELD, ())
    assert group.left_out is not None and "holds no figures" in group.left_out
    # A table that is left out gives no figure anywhere: not in its caption either.
    for table in found.tables:
        assert not re.search(r"\d", table.caption)


# --- The words --------------------------------------------------------------------


def _said(words: Words) -> list[str]:
    """Every string of a set of words, whatever it is held in."""
    found: list[str] = []
    for name in Words.model_fields:
        value: object = getattr(words, name)
        if isinstance(value, str):
            found.append(value)
        elif isinstance(value, tuple):
            found += [str(each) for each in cast(tuple[object, ...], value)]
        else:
            found += [str(each) for each in cast(dict[object, object], value).values()]
    return found


@pytest.mark.parametrize("words", [CENSUS_2021, MADE_UP], ids=["real", "made_up"])
def test_no_word_is_one_burro_would_be_choosing(words: Words):
    for text in _said(words):
        used = set(re.findall(r"[a-z]+", text.casefold()))
        assert not used & NEVER_SAID, (text, sorted(used & NEVER_SAID))
    assert {"diverse", "mixed", "majority", "minority", "main"} <= NEVER_SAID


def test_what_is_served_holds_no_word_burro_would_be_choosing():
    """Every string of a panel but a publisher's own heading."""
    for area in range(3):
        found = shown(area).model_dump(mode="json")
        for table in found["tables"]:
            for row in table["rows"]:
                row.update(heading="", label="")
            table.update(title="", caption="", left_out="", definition="")
            table["columns"].update(label="")
        used = set(re.findall(r"[a-z]+", json.dumps(found).casefold()))
        assert not used & NEVER_SAID, sorted(used & NEVER_SAID)


def test_the_real_census_says_its_day_and_that_it_was_taken_in_a_lockdown():
    assert "taken on {day}" in CENSUS_2021.date_line
    assert "Census 2021" in CENSUS_2021.heading and "Census 2021" in CENSUS_2021.caption
    assert CENSUS_2021.notes[0].startswith("The census was taken during a lockdown.")
    assert "An area can change." in CENSUS_2021.notes[1]


def test_the_publishers_sentence_about_the_day_stands_under_the_tables_it_bears_on():
    assert {CensusKind.AGE, CensusKind.HOUSEHOLDS} == BEARS_ON
    found = shown()
    assert table_of(found, CensusKind.AGE).note == MADE_UP.of_the_day
    assert table_of(found, CensusKind.ETHNIC_GROUP).note is None
    # It is the office's own sentence, in quotation marks, and no word of Burro's.
    assert CENSUS_2021.of_the_day.startswith('The statistics office says: "')
    assert CENSUS_2021.of_the_day.endswith('"')


def test_a_made_up_count_names_no_real_census_and_no_real_publisher():
    for text in _said(MADE_UP):
        folded = text.casefold()
        for real in ("census 2021", "office for national statistics", "lockdown", "coronavirus"):
            assert real not in folded, text
    assert "made-up" in MADE_UP.heading.casefold()
    assert "made-up" in MADE_UP.date_line.casefold()
    assert "made-up" in MADE_UP.caption.casefold()


def test_the_two_sets_of_words_fill_the_same_gaps():
    """A page laid out on the made-up count is laid out for the real one."""
    gaps = re.compile(r"\{[a-z]+\}")
    real, made_up = CENSUS_2021.model_dump(mode="json"), MADE_UP.model_dump(mode="json")
    for name in Words.model_fields:
        if name in ("notes", "counted", "intro", "small_area"):
            continue
        assert set(gaps.findall(real[name])) == set(gaps.findall(made_up[name])), name
    assert len(CENSUS_2021.notes) == len(MADE_UP.notes)


def test_what_is_shown_and_shown_only_on_says_so_on_its_table():
    assert {
        CensusKind.ETHNIC_GROUP,
        CensusKind.RELIGION,
        CensusKind.COUNTRY_OF_BIRTH,
    } == SHOWN_AND_NEVER_RANKED_ON
    found = shown()
    assert table_of(found, CensusKind.ETHNIC_GROUP).shown_only == MADE_UP.shown_only
    assert table_of(found, CensusKind.AGE).shown_only is None
    assert "never ranks" in MADE_UP.shown_only


def test_the_closed_block_holds_no_figure_and_names_no_area():
    said = offer(opened())
    assert said.available and said.heading == MADE_UP.heading
    assert "21 March 2021" in said.intro
    assert NAME not in said.intro and "%" not in said.intro
    assert offer(None) == NO_CENSUS and not NO_CENSUS.available


def test_an_area_the_census_does_not_name_has_no_panel():
    assert panel(opened(), "syn-n0099", NAME) is None


# --- It never reaches ranking -------------------------------------------------------


def _imports(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            found.add(node.module or "")
            found |= {f"{node.module}.{alias.name}" for alias in node.names}
    return found


def test_nothing_in_core_imports_the_census():
    for path in sorted(SOURCE.glob("*.py")):
        if path.stem == "census":
            continue
        assert not [name for name in _imports(path) if "census" in name], path.name
    assert not [name for name in burro_core.__all__ if "census" in name.casefold()]


def test_the_census_imports_nothing_of_core_that_ranks_or_says():
    ours = {name for name in _imports(SOURCE / "census.py") if name.startswith("burro_core")}
    modules = {name for name in ours if name.count(".") == 1}
    assert modules == {"burro_core._record", "burro_core.ids"}
    # Of the ids it takes the form of an id and nothing of the vocabulary.
    taken = {name.rsplit(".", 1)[1] for name in ours if name.count(".") == 2}
    assert not taken & {"FeatureId", "TagId", "FactKind", "Dimension", "TemplateId"}


def test_a_release_cannot_return_a_census_figure():
    members = [name for name in dir(Release) if not name.startswith("_")]
    assert members and not [name for name in members if "census" in name or "resident" in name]
    hints = get_type_hints(InMemoryRelease.__init__)
    for name, hint in hints.items():
        assert "census" not in name and "census" not in str(hint).casefold(), name
    assert not hasattr(fixture_release(), "census")


def test_a_release_folder_that_holds_a_census_file_is_refused():
    assert CENSUS not in DATA_FILES
    held = dict(_release_bytes())
    held[CENSUS] = files()[CENSUS]
    with pytest.raises(ReleaseError) as caught:
        open_release(RELEASE_ID, held)
    assert (caught.value.file, caught.value.rule) == (CENSUS, "files_match_manifest")


def _release_bytes() -> dict[str, bytes]:
    folder = Path(__file__).parents[3] / "data" / "fixtures" / "synthetic" / RELEASE_ID
    return {f.name: f.read_bytes() for f in sorted(folder.iterdir()) if f.name != ".DS_Store"}


VOCABULARY = (
    FeatureId,
    TagId,
    FactKind,
    TemplateId,
    Dimension,
    Describes,
    Setting,
    UnmetCategory,
)
# What a member of the vocabulary would have to hold to name what is shown and never ranked
# on. The age of residents and the make-up of households are not among these: a measure of
# either is a feature with an id of its own, which the founder has allowed.
NAMES_WHAT_IS_NEVER_RANKED_ON = frozenset(
    {
        "ethnic",
        "ethnicity",
        "race",
        "religion",
        "religious",
        "faith",
        "birth",
        "born",
        "nationality",
        "migrant",
        "migrants",
    }
)


def _parts(value: str) -> set[str]:
    return set(re.split(r"[^a-z0-9]+", value.casefold()))


@pytest.mark.parametrize("vocabulary", VOCABULARY, ids=lambda each: each.__name__)
def test_no_word_of_the_vocabulary_names_what_is_never_ranked_on(vocabulary: Any):
    """A spec, an edit, a fact and a sentence are made of these, so none can name one."""
    never = {kind.value for kind in SHOWN_AND_NEVER_RANKED_ON}
    for member in vocabulary:
        assert not _parts(member.value) & NAMES_WHAT_IS_NEVER_RANKED_ON, member
        assert member.value not in never, member


@pytest.mark.parametrize("record", [PreferenceSpec, Operations], ids=lambda each: each.__name__)
def test_no_spec_and_no_edit_has_a_field_for_what_is_never_ranked_on(record: Any):
    schema = json.dumps(record.model_json_schema())
    assert not _parts(schema) & NAMES_WHAT_IS_NEVER_RANKED_ON
    for kind in SHOWN_AND_NEVER_RANKED_ON:
        assert kind.value not in schema.casefold()
    assert "census" not in schema.casefold()


def test_a_census_kind_is_no_feature_and_no_vibe():
    for kind in CensusKind:
        with pytest.raises(ValueError, match="is not a valid"):
            FeatureId(kind.value)
        with pytest.raises(ValueError, match="is not a valid"):
            TagId(kind.value)


def test_a_census_is_never_handed_a_release():
    """It is told the release's id, whether it is made up, and its areas. It is handed no more."""
    for function in (open_census, parse_census, panel, offer):
        hints = get_type_hints(function)
        assert not [name for name, hint in hints.items() if "Release" in str(hint)], function


# --- The one judge ------------------------------------------------------------------


def set_in(*path: str | int, **changes: Any) -> Break:
    def change(found: Document) -> None:
        target: Any = found
        for part in path:
            target = target[part]
        target.update(changes)

    return change


def drop(*path: str | int) -> Break:
    def change(found: Document) -> None:
        target: Any = found
        for part in path[:-1]:
            target = target[part]
        del target[path[-1]]

    return change


BROKEN: list[tuple[str, Break]] = [
    ("census_is_of_the_release", set_in(release_id="syn-2026-09-23-02")),
    ("census_is_of_the_release", set_in(synthetic=False)),
    ("made_up_is_said", set_in("sources", 0, source_id="ons-census-2021")),
    ("made_up_is_said", set_in("tables", 0, url="https://burro.example/table")),
    ("tables_are_in_order", set_in("tables", 1, kind="age")),
    ("tables_are_in_order", set_in("tables", 1, table_code="SYN-AGE")),
    ("tables_are_in_order", set_in("tables", 0, source_id="another")),
    ("tables_are_in_order", set_in("tables", 1, "rows", 1, code="grp-a")),
    ("tables_are_in_order", set_in("tables", 1, "rows", 0, depth=1)),
    ("tables_are_in_order", set_in("tables", 1, "rows", 1, depth=2)),
    ("areas_are_the_releases", drop("areas", 2)),
    ("areas_are_the_releases", set_in("areas", 0, area_id="syn-n0009")),
    ("areas_are_the_releases", set_in("areas", 1, area_id="syn-n0001")),
    ("rows_are_complete", drop("areas", 0, "tables", 1)),
    ("rows_are_complete", drop("whole", "tables", 0)),
    ("rows_are_complete", set_in("areas", 0, "tables", 0, counts=[1_437, 2_000])),
    ("rows_are_complete", set_in("areas", 0, "tables", 0, reason="too_few")),
    ("rows_are_complete", set_in("areas", 2, "tables", 0, base=2_000)),
    ("rows_are_complete", set_in("areas", 2, "tables", 0, reason=None)),
    ("too_few_are_left_out", set_in("areas", 0, "tables", 0, base=999, counts=[400, 400, 199])),
    (
        "small_counts_are_withheld",
        set_in("areas", 0, "tables", 1, counts=[4_010, 2_525, 1_485, 40]),
    ),
    ("small_counts_are_withheld", set_in("areas", 0, "tables", 1, counts=[4_010, 2_525, 1_485, 0])),
    ("small_counts_are_withheld", set_in("areas", 0, "tables", 0, counts=[4_041, 2_000, 603])),
    ("small_counts_are_withheld", set_in("whole", "tables", 0, counts=[8_000, 9_000, 199])),
    ("shape_is_valid", set_in("areas", 0, "tables", 0, counts=[1_437.5, 2_000, 603])),
    ("shape_is_valid", set_in("areas", 0, "tables", 0, counts=["36%", "50%", "15%"])),
    ("shape_is_valid", set_in("areas", 0, rank=1)),
    ("shape_is_valid", set_in("tables", 0, kind="income")),
    ("shape_is_valid", set_in(taken_on="21 March 2021")),
    ("shape_is_valid", drop("whole")),
]


@pytest.mark.parametrize(
    ("rule", "change"), BROKEN, ids=[f"{rule}-{n}" for n, (rule, _) in enumerate(BROKEN)]
)
def test_a_census_that_breaks_a_rule_is_refused_by_that_rule(rule: str, change: Break):
    found = document()
    change(found)
    with pytest.raises(CensusError) as caught:
        parse_census(found, RELEASE_ID, True, AREAS)
    assert (caught.value.file, caught.value.rule) == (CENSUS, rule)


def test_every_rule_is_shown_refusing_a_census():
    assert {rule.__name__ for rule in RULES} <= {rule for rule, _ in BROKEN}


def test_the_census_the_tests_share_is_in_order():
    assert [area.area_id for area in opened().areas] == list(AREAS)


def test_a_refusal_says_where_and_never_what():
    found = document()
    found["tables"][1]["rows"][3]["depth"] = 9
    found["tables"][1]["rows"][3]["label"] = CANARY_LABEL
    with pytest.raises(CensusError) as caught:
        parse_census(found, RELEASE_ID, True, AREAS)
    assert caught.value.row == "tables[1].rows[3].depth"
    assert CANARY_LABEL not in str(caught.value) and "9" not in str(caught.value).split(":")[-1]
    assert caught.value.__cause__ is None


FOLDERS: list[tuple[str, str, Callable[[dict[str, bytes]], object]]] = [
    (MANIFEST, "files_match_manifest", lambda held: held.pop(MANIFEST)),
    (CENSUS, "files_match_manifest", lambda held: held.pop(CENSUS)),
    ("features.json", "files_match_manifest", lambda held: held.update({"features.json": b"{}"})),
    (CENSUS, "files_match_manifest", lambda held: held.update({CENSUS: held[CENSUS] + b" "})),
    (MANIFEST, "json_is_valid", lambda held: held.update({MANIFEST: b"{"})),
    (MANIFEST, "shape_is_valid", lambda held: held.update({MANIFEST: b"{}"})),
]


@pytest.mark.parametrize(("file", "rule", "change"), FOLDERS, ids=range(len(FOLDERS)))
def test_a_folder_that_is_not_as_it_was_written_is_refused(
    file: str, rule: str, change: Callable[[dict[str, bytes]], object]
):
    held = files()
    change(held)
    with pytest.raises(CensusError) as caught:
        open_census(FOLDER, held, RELEASE_ID, True, AREAS)
    assert (caught.value.file, caught.value.rule) == (file, rule)


def test_a_census_made_for_another_release_is_refused():
    with pytest.raises(CensusError) as caught:
        open_census(FOLDER, files(), "syn-2026-09-23-02", True, AREAS)
    assert caught.value.rule == "folder_is_named_for_the_release"
    with pytest.raises(CensusError) as caught:
        open_census(FOLDER, files(), RELEASE_ID, False, AREAS)
    assert caught.value.rule == "census_is_of_the_release"


def test_a_manifest_that_names_other_sources_than_the_census_is_refused():
    held = files()
    manifest = json.loads(held[MANIFEST])
    manifest["sources"][0]["name"] = "Another"
    held[MANIFEST] = as_bytes(manifest)
    with pytest.raises(CensusError) as caught:
        open_census(FOLDER, held, RELEASE_ID, True, AREAS)
    assert (caught.value.file, caught.value.rule) == (MANIFEST, "sources_are_stated")


# --- The made-up census that is committed -------------------------------------------


def committed() -> Census:
    release = fixture_release()
    area_ids = [area.area_id for area in release.neighbourhoods]
    return open_census(FOLDER, committed_bytes(), RELEASE_ID, True, area_ids)


def test_the_committed_census_is_of_the_committed_release():
    found = committed()
    assert found.synthetic and found.release_id == fixture_release().manifest.release_id
    assert {table.kind for table in found.tables} == set(CensusKind)


def test_the_committed_census_shows_every_state_a_page_must_draw():
    found, release = committed(), fixture_release()
    panels = [
        shown
        for area in release.neighbourhoods
        if (shown := panel(found, area.area_id, area.name)) is not None
    ]
    assert len(panels) == len(release.neighbourhoods)
    reasons = {table.reason for each in panels for table in each.tables}
    assert reasons == {None, CensusLeftOut.TOO_FEW, CensusLeftOut.NOT_HELD}
    shares = {row.share for each in panels for table in each.tables for row in table.rows}
    assert FEWER in shares
    depths = {row.depth for each in panels for table in each.tables for row in table.rows}
    assert depths == {0, 1, 2}
    # Beside every figure is the city's, and the city is the release's one borough.
    assert {each.city for each in panels} == {release.neighbourhoods[0].borough}
    assert all(row.city_share for each in panels for table in each.tables for row in table.rows)
