"""The made-up count, the folder a census is written to, and the gate in front of a real one."""

import ast
import json
import re
from functools import cache
from pathlib import Path
from typing import Any

import burro_pipeline
import pytest
from burro_core.census import (
    CENSUS,
    FEWER,
    MADE_UP,
    MANIFEST,
    RULES,
    SHOWN_AND_NEVER_RANKED_ON,
    Census,
    CensusError,
    CensusKind,
    CensusLeftOut,
    panel,
    parse_census,
)
from burro_core.release import DATA_FILES, InMemoryRelease
from burro_pipeline.registry import (
    Dimension,
    Registry,
    RegistryError,
    Source,
    Status,
    Use,
    load,
)
from burro_pipeline.release import build_synthetic, residents
from burro_pipeline.release.cli import main
from burro_pipeline.release.read import IGNORED
from burro_pipeline.release.residents import (
    MEANING,
    UnreadableCensus,
    folder_of,
    packed,
    read_census,
    write_census,
)
from burro_pipeline.release.synthetic import RELEASE_ID, SEED, count
from burro_pipeline.release.synthetic.count import NOT_COUNTED, PLANS, made_up_census
from burro_pipeline.release.write import USE_OF
from burro_pipeline.release.write import packed as packed_release

from .test_release_files import REAL_ID, real_release, registered

REPOSITORY = Path(__file__).parents[3]
COMMITTED = REPOSITORY / "data" / "fixtures" / "residents" / folder_of(RELEASE_ID)
RELEASES = REPOSITORY / "data" / "fixtures" / "synthetic"
RESIDENTS_ID = "made-up-census"
ALL_FIVE = ("TS003", "TS004", "TS007A", "TS021", "TS030")


@cache
def release() -> InMemoryRelease:
    return build_synthetic()


@cache
def made_up() -> Census:
    return made_up_census(release(), SEED)


def area_ids(of: InMemoryRelease) -> list[str]:
    return [area.area_id for area in of.neighbourhoods]


# --- The made-up count -----------------------------------------------------------


def test_the_made_up_count_rebuilds_byte_for_byte(tmp_path: Path):
    write_census(made_up(), release(), tmp_path)
    rebuilt = {f.name: f.read_bytes() for f in (tmp_path / folder_of(RELEASE_ID)).iterdir()}
    committed = {f.name: f.read_bytes() for f in COMMITTED.iterdir() if f.name != IGNORED}
    assert sorted(committed) == sorted(rebuilt) == [CENSUS, MANIFEST]
    stale = sorted(name for name in rebuilt if rebuilt[name] != committed[name])
    assert not stale, "the committed count is not what the generator makes: run `make fixture`"


def test_the_seed_decides_every_figure_and_no_heading():
    once, again, other = (made_up_census(release(), seed) for seed in (7, 7, 8))
    assert once == again
    assert once.areas != other.areas
    assert once.tables == other.tables


def test_the_made_up_count_moves_no_figure_of_the_release():
    """It is drawn from a stream of its own, after the release is made."""
    before = packed_release(build_synthetic())
    made_up_census(build_synthetic(), SEED)
    assert packed_release(build_synthetic()) == before


def test_the_made_up_count_holds_a_table_of_each_kind_for_every_area():
    found = made_up()
    assert {table.kind for table in found.tables} == set(CensusKind)
    assert [area.area_id for area in found.areas] == area_ids(release())
    assert found.synthetic and found.whole.name == "Quillhaven"


def test_gaps_are_left_on_purpose_and_nothing_fills_them():
    found = made_up()
    names = {area.area_id: area.name for area in release().neighbourhoods}
    left_out = {
        names[area.area_id]: {table.reason for table in area.tables}
        for area in found.areas
        if any(table.reason for table in area.tables)
    }
    assert left_out == {
        "Grapnel Dock": {CensusLeftOut.TOO_FEW},
        NOT_COUNTED: {CensusLeftOut.NOT_HELD},
        "Sedgewater Marsh": {CensusLeftOut.TOO_FEW},
    }
    for area in found.areas:
        for table in area.tables:
            if table.reason is not None:
                assert table.base is None and table.counts == ()
    # Every table of every area that is counted holds a row that is too small to give.
    small = [
        table.table_code
        for area in found.areas
        for table in area.tables
        if table.reason is None and None in table.counts
    ]
    assert {table.table_code for table in found.tables} - set(small) <= {"SYN-AGE"}


# The headings of the three real tables that are shown and never ranked on, as the research
# note of 2026-09-23 records them from the publisher's pages. A made-up count holds none, so
# that no picture of the made-up city shows a made-up share of real people.
REAL_HEADINGS = (
    # TS021 Ethnic group.
    "Asian, Asian British or Asian Welsh",
    "Bangladeshi",
    "Chinese",
    "Indian",
    "Pakistani",
    "Other Asian",
    "Black, Black British, Black Welsh, Caribbean or African",
    "African",
    "Caribbean",
    "Other Black",
    "Mixed or Multiple ethnic groups",
    "White and Asian",
    "White and Black African",
    "White and Black Caribbean",
    "Other Mixed or Multiple ethnic groups",
    "White",
    "English, Welsh, Scottish, Northern Irish or British",
    "Irish",
    "Gypsy or Irish Traveller",
    "Roma",
    "Other White",
    "Other ethnic group",
    "Arab",
    "Any other ethnic group",
    # TS030 Religion.
    "No religion",
    "Christian",
    "Buddhist",
    "Hindu",
    "Jewish",
    "Muslim",
    "Sikh",
    "Other religion",
    "Not answered",
    # TS004 Country of birth.
    "Europe",
    "United Kingdom",
    "EU countries",
    "European Union",
    "Non-EU countries",
    "Africa",
    "Middle East and Asia",
    "The Americas and the Caribbean",
    "Antarctica and Oceania",
    "Australasia",
    "British Overseas",
)
# Words that name real people wherever they stand, whatever the heading around them.
REAL_WORDS = (
    "asian",
    "black",
    "white",
    "arab",
    "roma",
    "irish",
    "british",
    "english",
    "welsh",
    "scottish",
    "african",
    "caribbean",
    "indian",
    "chinese",
    "pakistani",
    "bangladeshi",
    "christian",
    "muslim",
    "jewish",
    "hindu",
    "sikh",
    "buddhist",
    "europe",
    "european",
    "africa",
    "asia",
    "americas",
)


def test_the_made_up_count_holds_no_heading_of_a_real_census_table():
    said = [
        text
        for table in made_up().tables
        for text in (
            table.title,
            table.variable,
            table.definition,
            *(row.heading for row in table.rows),
            *(row.label for row in table.rows),
        )
    ]
    real = {heading.casefold() for heading in REAL_HEADINGS}
    for text in said:
        assert text.casefold() not in real, text
        for part in text.split(": "):
            assert part.casefold() not in real, text
        assert not set(re.findall(r"[a-z]+", text.casefold())) & set(REAL_WORDS), text


def test_every_table_of_made_up_groups_says_in_its_title_that_it_is_made_up():
    for table in made_up().tables:
        assert "made up" in table.title.casefold() or "made-up" in table.title.casefold()
        assert "counts nobody" in table.definition
        assert table.url == "" and table.source_id == "synthetic"
        if table.kind in SHOWN_AND_NEVER_RANKED_ON:
            # Every group says so itself, so that one row alone cannot be taken for a real one.
            # The row for those who gave no answer names no group.
            named = [row.heading for row in table.rows if row.heading != "Gave no answer"]
            assert all("made-up" in heading.casefold() for heading in named)


def test_the_made_up_groups_follow_no_trait_of_an_area():
    """Nothing about a made-up group goes with how leafy, how lively or how dear an area is."""
    for plan in PLANS:
        if plan.kind in SHOWN_AND_NEVER_RANKED_ON:
            assert all(leaf.family == 0 and leaf.lively == 0 for leaf in plan.leaves), plan.code


def test_a_group_is_the_sum_of_what_stands_under_it():
    found = made_up()
    for table, whole in zip(found.tables, found.whole.tables, strict=True):
        depths = [row.depth for row in table.rows]
        for position, depth in enumerate(depths):
            under: list[int | None] = []
            for after in range(position + 1, len(depths)):
                if depths[after] <= depth:
                    break
                if depths[after] == depth + 1:
                    under.append(whole.counts[after])
            if under and None not in under:
                assert whole.counts[position] == sum(each for each in under if each is not None)


def test_the_labels_are_as_long_and_as_deep_as_a_publishers():
    rows = [row for table in made_up().tables for row in table.rows]
    assert max(len(row.label) for row in rows) >= 70
    assert {row.depth for row in rows} == {0, 1, 2}
    assert [len(table.rows) for table in made_up().tables] == [20, 12, 18, 24, 9]


def test_the_words_of_a_made_up_count_are_the_made_up_words():
    shown = panel(made_up(), area_ids(release())[0], "Alderwick")
    assert shown is not None
    assert shown.heading == MADE_UP.heading
    assert shown.licence_line == release().manifest.sources[0].attribution
    assert FEWER in {row.share for table in shown.tables for row in table.rows}


def _imports(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            found.add(node.module or "")
            found |= {f"{node.module}.{alias.name}" for alias in node.names}
    return found


SYNTHETIC_PACKAGE = Path(count.__file__).parent


def test_the_made_up_count_reads_no_file_and_no_dataset():
    """Why it needs no licence gate: there is nothing it could have read."""
    imported = _imports(SYNTHETIC_PACKAGE / "count.py")
    assert not [name for name in imported if name.startswith("burro_pipeline.registry")]
    assert not [name for name in imported if name.split(".")[0] in ("pathlib", "os", "io", "json")]


# --- The folder -------------------------------------------------------------------


def test_a_written_census_reads_back_the_same(tmp_path: Path):
    as_written = write_census(made_up(), release(), tmp_path)
    folder = tmp_path / folder_of(RELEASE_ID)
    assert read_census(folder, release()) == as_written == made_up()
    assert sorted(entry.name for entry in folder.iterdir()) == [CENSUS, MANIFEST]


def test_a_census_is_no_file_of_a_release():
    assert CENSUS not in DATA_FILES and CENSUS not in packed_release(release())
    assert Use.CENSUS_TABLE not in USE_OF.values()


def test_the_committed_count_is_kept_outside_the_folder_of_releases():
    """Whatever lists the releases of the repository finds releases and nothing else."""
    assert COMMITTED.parent != RELEASES
    assert [entry.name for entry in RELEASES.iterdir() if entry.is_dir()] == [RELEASE_ID]
    assert not list(RELEASES.rglob(CENSUS))


def test_the_made_up_count_needs_no_registry_and_an_empty_one_does_not_stop_it(tmp_path: Path):
    assert write_census(made_up(), release(), tmp_path, Registry(())).synthetic is True


def refusal(folder: Path) -> UnreadableCensus:
    with pytest.raises(UnreadableCensus) as caught:
        read_census(folder, release())
    return caught.value


def written(tmp_path: Path) -> Path:
    write_census(made_up(), release(), tmp_path)
    return tmp_path / folder_of(RELEASE_ID)


def test_a_missing_file_is_refused_in_one_readable_line(tmp_path: Path):
    folder = written(tmp_path)
    (folder / CENSUS).unlink()
    refused = refusal(folder)
    assert refused.rule == "files_match_manifest"
    assert str(refused).startswith(f"{folder}: {CENSUS} is not the file the manifest lists")
    assert "\n" not in str(refused)


def test_a_changed_census_is_refused(tmp_path: Path):
    folder = written(tmp_path)
    found = json.loads((folder / CENSUS).read_bytes())
    found["areas"][0]["tables"][0]["base"] += 1
    (folder / CENSUS).write_bytes(json.dumps(found).encode())
    assert refusal(folder).rule == "files_match_manifest"


def test_a_file_that_does_not_belong_is_refused_and_what_the_finder_leaves_is_not(tmp_path: Path):
    folder = written(tmp_path)
    (folder / IGNORED).write_bytes(b"\x00")
    assert read_census(folder, release()) == made_up()
    (folder / "features.json").write_bytes(b"{}")
    assert (refusal(folder).file, refusal(folder).rule) == ("features.json", "files_match_manifest")


def test_a_census_in_a_folder_of_another_name_is_refused(tmp_path: Path):
    folder = written(tmp_path)
    moved = folder.rename(tmp_path / RELEASE_ID)
    assert refusal(moved).rule == "folder_is_named_for_the_release"


def test_a_census_is_refused_beside_a_release_it_was_not_made_for(tmp_path: Path):
    folder = written(tmp_path)
    other = build_synthetic(gritty_variant="a", release_id="syn-2026-09-23-02")
    with pytest.raises(UnreadableCensus) as caught:
        read_census(folder, other)
    assert caught.value.rule == "folder_is_named_for_the_release"


def test_a_folder_that_is_not_there_is_refused_in_one_readable_line(tmp_path: Path):
    assert refusal(tmp_path / "nowhere").rule == "folder_is_readable"


def test_a_census_that_breaks_a_rule_is_never_written(tmp_path: Path):
    broken = made_up().model_dump(mode="json")
    broken["areas"][0]["tables"][0]["counts"][0] = 3
    census = Census.model_validate(broken)
    with pytest.raises(CensusError) as caught:
        write_census(census, release(), tmp_path)
    assert caught.value.rule == "small_counts_are_withheld"
    assert list(tmp_path.iterdir()) == []


def test_a_folder_that_holds_something_else_is_left_as_it_was(tmp_path: Path):
    mine = tmp_path / folder_of(RELEASE_ID) / "thesis.txt"
    mine.parent.mkdir()
    mine.write_text("three years of work")
    with pytest.raises(CensusError) as caught:
        write_census(made_up(), release(), tmp_path)
    assert (caught.value.file, caught.value.rule) == ("thesis.txt", "folder_holds_something_else")
    assert mine.read_text() == "three years of work"


def test_every_refusal_has_a_meaning_in_plain_words():
    rules = {rule.__name__ for rule in RULES}
    beyond = {"files_match_manifest", "json_is_valid", "shape_is_valid", "sources_are_stated"}
    assert rules | beyond | {"folder_is_named_for_the_release"} <= set(MEANING)
    assert all(meaning and meaning[0].islower() for meaning in MEANING.values())


# --- The gate in front of a real census ----------------------------------------------


@cache
def real() -> Census:
    """The made-up count under real ids, citing a source as a real census would."""
    found: dict[str, Any] = json.loads(json.dumps(made_up().model_dump(mode="json")))
    found = json.loads(json.dumps(found).replace("syn-", "lon-"))
    found.update(release_id=REAL_ID, synthetic=False)
    found["sources"][0].update(source_id=RESIDENTS_ID, url="https://example.org/census")
    for table, code in zip(found["tables"], ALL_FIVE, strict=True):
        old = table["table_code"]
        table.update(table_code=code, source_id=RESIDENTS_ID, url="https://example.org/table")
        for held in (found["whole"], *found["areas"]):
            for counted in held["tables"]:
                if counted["table_code"] == old:
                    counted["table_code"] = code
    ids = area_ids(real_release())
    return parse_census(found, REAL_ID, False, ids)


def with_the_census(
    *uses: Use, status: Status = Status.APPROVED, tables: tuple[str, ...]
) -> Registry:
    source = registered(RESIDENTS_ID, *uses, status=status)
    held = source.model_dump() | {"dimension": Dimension.RESIDENTS, "tables": tables}
    return Registry((Source.model_validate(held),))


def test_a_real_census_is_written_when_its_source_is_registered_for_the_census_table(
    tmp_path: Path,
):
    registry = with_the_census(Use.CENSUS_TABLE, tables=ALL_FIVE)
    as_written = write_census(real(), real_release(), tmp_path, registry)
    assert as_written.synthetic is False
    assert read_census(tmp_path / folder_of(REAL_ID), real_release()) == as_written


def test_a_real_census_is_refused_without_a_registry(tmp_path: Path):
    with pytest.raises(CensusError) as caught:
        write_census(real(), real_release(), tmp_path)
    assert caught.value.rule == "real_census_needs_a_registry"
    assert list(tmp_path.iterdir()) == []


def test_a_source_that_is_not_approved_or_not_registered_never_reaches_a_census(tmp_path: Path):
    gated = with_the_census(Use.CENSUS_TABLE, status=Status.GATED, tables=ALL_FIVE)
    with pytest.raises(RegistryError, match=f"'{RESIDENTS_ID}' is gated, not approved"):
        write_census(real(), real_release(), tmp_path, gated)
    with pytest.raises(RegistryError, match="is not in the licence registry"):
        write_census(real(), real_release(), tmp_path, Registry(()))
    assert list(tmp_path.iterdir()) == []


def test_a_table_its_source_does_not_name_never_reaches_a_census(tmp_path: Path):
    registry = with_the_census(Use.CENSUS_TABLE, tables=("TS003", "TS007A"))
    with pytest.raises(CensusError) as caught:
        write_census(real(), real_release(), tmp_path, registry)
    assert caught.value.rule == "table_is_named_by_its_source"
    assert list(tmp_path.iterdir()) == []


def test_the_real_registry_does_not_yet_let_a_census_be_written(tmp_path: Path):
    """The entry is gated until a person has read its licence. Nothing here changes that."""
    committed = load(REPOSITORY / "registry" / "sources")
    found = json.loads(json.dumps(real().model_dump(mode="json")))
    found["sources"][0]["source_id"] = "ons-census-2021-resident-tables"
    for table in found["tables"]:
        table["source_id"] = "ons-census-2021-resident-tables"
    census = parse_census(found, REAL_ID, False, area_ids(real_release()))
    with pytest.raises(RegistryError, match="is gated, not approved"):
        write_census(census, real_release(), tmp_path, committed)
    assert list(tmp_path.iterdir()) == []


def test_a_real_census_is_never_written_over(tmp_path: Path):
    registry = with_the_census(Use.CENSUS_TABLE, tables=ALL_FIVE)
    write_census(real(), real_release(), tmp_path, registry)
    with pytest.raises(CensusError) as caught:
        write_census(real(), real_release(), tmp_path, registry)
    assert caught.value.rule == "census_is_never_overwritten"


def test_calling_a_census_made_up_does_not_get_a_real_source_past_the_gate(tmp_path: Path):
    disguised = real().replace(synthetic=True)
    with pytest.raises(CensusError) as caught:
        write_census(disguised, real_release(), tmp_path)
    assert caught.value.rule == "census_is_of_the_release"
    assert list(tmp_path.iterdir()) == []


# --- Apart from what builds the product ------------------------------------------------

PACKAGE = Path(burro_pipeline.__file__).parent
# The steps that build what is ranked on and said. None may read a census.
PRODUCT_STEPS = ("derive", "assemble", "areas", "cells", "evidence", "fetch")
MAY_NAME_THE_CENSUS = {
    PACKAGE / "release" / "residents.py",
    PACKAGE / "release" / "cli.py",
    PACKAGE / "release" / "synthetic" / "count.py",
}


def test_nothing_that_builds_the_product_imports_the_census_and_it_imports_none_of_them():
    for path in sorted(PACKAGE.rglob("*.py")):
        reads = [
            name
            for name in _imports(path)
            if name.startswith(("burro_core.census", "burro_pipeline.release.residents"))
            or name.endswith(".count")
        ]
        if path not in MAY_NAME_THE_CENSUS:
            assert not reads, (path.relative_to(PACKAGE), reads)
    for path in (Path(residents.__file__), Path(count.__file__)):
        ours = {name for name in _imports(path) if name.startswith("burro_pipeline.")}
        assert not [name for name in ours if name.split(".")[1] in PRODUCT_STEPS], path.name
    assert not [
        name
        for name in _imports(Path(count.__file__))
        if name.startswith(("burro_core.rank", "burro_core.catalogue", "burro_core.facts"))
    ]


# --- The command ----------------------------------------------------------------------


def test_the_command_builds_the_count_beside_the_release_and_checks_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    releases, counts = tmp_path / "releases", tmp_path / "counts"
    assert main(["build-synthetic", "--out", str(releases), "--census-out", str(counts)]) == 0
    folder = counts / folder_of(RELEASE_ID)
    assert main(["check", str(releases / RELEASE_ID), "--census", str(folder)]) == 0
    built, counted, checked, held = capsys.readouterr().out.splitlines()
    assert (built, counted) == (checked, held)
    assert counted == f"{RELEASE_ID}-residents: 5 tables, 24 areas, made up"
    assert packed(made_up())[CENSUS] == (folder / CENSUS).read_bytes()


def test_the_command_writes_no_count_unless_it_is_told_where(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    assert main(["build-synthetic", "--out", str(tmp_path)]) == 0
    assert [entry.name for entry in tmp_path.iterdir()] == [RELEASE_ID]
    assert len(capsys.readouterr().out.splitlines()) == 1


def test_the_command_refuses_a_broken_count_in_one_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    releases = tmp_path / "releases"
    assert main(["build-synthetic", "--out", str(releases)]) == 0
    folder = written(tmp_path)
    (folder / MANIFEST).write_bytes(b"{")
    capsys.readouterr()
    assert main(["check", str(releases / RELEASE_ID), "--census", str(folder)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"error: {folder}: {MANIFEST} is not valid JSON [json_is_valid]\n"
