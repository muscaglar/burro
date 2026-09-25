"""The made-up estimate of household income, the folder it is written to, and the gate.

Household income is shown on an area's page and is no part of a release. So
what is held here is that it is written apart, that a real one passes the
licence gate for `display` and for nothing that ranks, and that nothing which
builds what is ranked on reads it.
"""

import ast
import json
from functools import cache
from pathlib import Path
from typing import Any

import burro_pipeline
import pytest
from burro_core.income import INCOME, MADE_UP, MANIFEST, RULES, Income, IncomeError, parse_income
from burro_core.release import DATA_FILES, InMemoryRelease
from burro_pipeline.registry import Registry, RegistryError, Status, Use
from burro_pipeline.release import build_synthetic, income
from burro_pipeline.release.cli import main
from burro_pipeline.release.income import (
    MEANING,
    UnreadableIncome,
    folder_of,
    packed,
    read_income,
    write_income,
)
from burro_pipeline.release.read import IGNORED
from burro_pipeline.release.synthetic import RELEASE_ID, SEED, estimate
from burro_pipeline.release.synthetic.estimate import NOT_ESTIMATED, made_up_income
from burro_pipeline.release.write import packed as packed_release

from .test_release_files import REAL_ID, real_release, registered

REPOSITORY = Path(__file__).parents[3]
COMMITTED = REPOSITORY / "data" / "fixtures" / "income" / folder_of(RELEASE_ID)
RELEASES = REPOSITORY / "data" / "fixtures" / "synthetic"
PACKAGE = Path(burro_pipeline.__file__).parent
SHOWN_ID = "made-up-income"


@cache
def release() -> InMemoryRelease:
    return build_synthetic()


@cache
def made_up() -> Income:
    return made_up_income(release(), SEED)


# --- The made-up estimates --------------------------------------------------------


def test_the_made_up_estimates_rebuild_byte_for_byte(tmp_path: Path):
    write_income(made_up(), release(), tmp_path)
    rebuilt = {f.name: f.read_bytes() for f in (tmp_path / folder_of(RELEASE_ID)).iterdir()}
    committed = {f.name: f.read_bytes() for f in COMMITTED.iterdir() if f.name != IGNORED}
    assert sorted(committed) == sorted(rebuilt) == [INCOME, MANIFEST]
    stale = sorted(name for name in rebuilt if rebuilt[name] != committed[name])
    assert not stale, "the committed figures are not what the generator makes: run `make fixture`"


def test_the_seed_decides_every_figure():
    once, again, other = (made_up_income(release(), seed) for seed in (7, 7, 8))
    assert once == again and once.areas != other.areas


def test_the_made_up_estimates_move_no_figure_of_the_release():
    """They are drawn from a stream of their own, after the release is made."""
    before = packed_release(build_synthetic())
    made_up_income(build_synthetic(), SEED)
    assert packed_release(build_synthetic()) == before


def test_every_area_has_an_estimate_between_its_limits_but_the_one_left_out_on_purpose():
    names = {area.area_id: area.name for area in release().neighbourhoods}
    without = [names[area.area_id] for area in made_up().areas if area.estimate is None]
    assert without == [NOT_ESTIMATED]
    for area in made_up().areas:
        if area.estimate is not None:
            assert area.lower is not None and area.upper is not None
            assert area.lower < area.estimate < area.upper


def test_a_made_up_estimate_follows_no_trait_of_an_area():
    """It is drawn from noise alone, so no picture of the made-up city says who is well off.

    The figures are decided by the seed and by how many areas there are, and
    by nothing of any area: the generator reads no plan of an area and no
    figure of the release, and a release with other figures gets the same.
    """
    ours = _imports(Path(estimate.__file__))
    assert not [name for name in ours if name.endswith((".names", ".build", ".count"))]
    source = Path(estimate.__file__).read_text(encoding="utf-8")
    for never in (".features", ".tags", ".costs", ".feature(", "AreaPlan", "plan."):
        assert never not in source, never
    other = build_synthetic(seed=SEED + 1)
    assert other.features != release().features
    assert made_up_income(other, SEED).areas == made_up().areas


def test_the_words_of_a_made_up_estimate_are_the_made_up_words():
    assert made_up().synthetic is True and made_up().source.source_id == "synthetic"
    assert made_up().source.url == "" and "made-up" in MADE_UP.heading.casefold()


def _imports(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            found.add(node.module or "")
            found |= {f"{node.module}.{alias.name}" for alias in node.names}
    return found


def test_the_made_up_estimates_read_no_file_and_no_dataset():
    ours = _imports(Path(estimate.__file__))
    assert not [name for name in ours if name.split(".")[0] in {"pathlib", "os", "csv", "io"}]
    assert not [name for name in ours if "registry" in name or "inputs" in name]


# --- The folder -------------------------------------------------------------------


def test_written_figures_read_back_the_same(tmp_path: Path):
    as_written = write_income(made_up(), release(), tmp_path)
    folder = tmp_path / folder_of(RELEASE_ID)
    assert read_income(folder, release()) == as_written == made_up()
    assert sorted(entry.name for entry in folder.iterdir()) == [INCOME, MANIFEST]


def test_household_income_is_no_file_of_a_release():
    assert INCOME not in DATA_FILES and INCOME not in packed_release(release())
    assert not [name for name in packed_release(release()) if "income" in name]
    held = b"".join(packed_release(release()).values()).decode().casefold()
    assert "income" not in held


def test_the_committed_figures_are_kept_outside_the_folder_of_releases():
    assert COMMITTED.parent != RELEASES
    assert [entry.name for entry in RELEASES.iterdir() if entry.is_dir()] == [RELEASE_ID]
    assert not list(RELEASES.rglob(INCOME))


def refusal(folder: Path) -> UnreadableIncome:
    with pytest.raises(UnreadableIncome) as caught:
        read_income(folder, release())
    return caught.value


def written(tmp_path: Path) -> Path:
    write_income(made_up(), release(), tmp_path)
    return tmp_path / folder_of(RELEASE_ID)


def test_a_missing_a_changed_and_a_stray_file_are_each_refused_in_one_line(tmp_path: Path):
    folder = written(tmp_path)
    (folder / IGNORED).write_bytes(b"\x00")
    assert read_income(folder, release()) == made_up()
    (folder / "notes.txt").write_bytes(b"mine")
    assert (refusal(folder).file, refusal(folder).rule) == ("notes.txt", "files_match_manifest")
    (folder / "notes.txt").unlink()
    (folder / INCOME).write_bytes((folder / INCOME).read_bytes() + b" ")
    said = refusal(folder)
    assert str(said) == (
        f"{folder}: {INCOME} is not the file the manifest lists: it is missing, it has "
        "changed, or it does not belong in the folder [files_match_manifest]"
    )
    (folder / INCOME).unlink()
    assert refusal(folder).file == INCOME
    assert refusal(tmp_path / "nowhere").rule == income.FOLDER_IS_READABLE


def test_figures_in_a_folder_of_another_name_or_beside_another_release_are_refused(
    tmp_path: Path,
):
    folder = written(tmp_path)
    renamed = folder.rename(tmp_path / f"{RELEASE_ID}-residents")
    assert refusal(renamed).rule == "folder_is_named_for_the_release"
    other = written(tmp_path / "again")
    with pytest.raises(UnreadableIncome) as caught:
        read_income(other, real_release())
    assert caught.value.rule in {"folder_is_named_for_the_release", "income_is_of_the_release"}


def test_figures_that_break_a_rule_are_never_written(tmp_path: Path):
    first = made_up().areas[0]
    broken = made_up().replace(areas=(first.replace(lower=first.upper), *made_up().areas[1:]))
    with pytest.raises(IncomeError) as caught:
        write_income(broken, release(), tmp_path)
    assert caught.value.rule == "limits_hold_the_estimate"
    assert list(tmp_path.iterdir()) == []


def test_a_folder_that_holds_something_else_is_left_as_it_was(tmp_path: Path):
    mine = tmp_path / folder_of(RELEASE_ID) / "thesis.txt"
    mine.parent.mkdir()
    mine.write_text("three years of work")
    with pytest.raises(IncomeError) as caught:
        write_income(made_up(), release(), tmp_path)
    assert (caught.value.file, caught.value.rule) == ("thesis.txt", "folder_holds_something_else")
    assert mine.read_text() == "three years of work"


def test_every_refusal_has_a_meaning_in_plain_words():
    rules = {rule.__name__ for rule in RULES}
    rules |= {"folder_is_named_for_the_release", "files_match_manifest", "json_is_valid"}
    rules |= {"shape_is_valid", "source_is_stated"}
    assert rules <= set(MEANING)
    assert all(words and not words.endswith(".") for words in MEANING.values())


# --- The gate in front of real figures ----------------------------------------------


@cache
def real() -> Income:
    """The made-up figures under real ids, citing a source as real ones would."""
    found: dict[str, Any] = json.loads(json.dumps(made_up().model_dump(mode="json")))
    found = json.loads(json.dumps(found).replace("syn-", "lon-"))
    found.update(release_id=REAL_ID, synthetic=False)
    found["source"].update(source_id=SHOWN_ID, url="https://example.org/income")
    ids = [area.area_id for area in real_release().neighbourhoods]
    return parse_income(found, REAL_ID, False, ids)


def holding(*uses: Use, status: Status = Status.APPROVED) -> Registry:
    return Registry((registered(SHOWN_ID, *uses, status=status),))


def test_real_figures_are_written_when_their_source_is_registered_to_be_shown(tmp_path: Path):
    as_written = write_income(real(), real_release(), tmp_path, holding(Use.DISPLAY))
    assert as_written.synthetic is False
    assert read_income(tmp_path / folder_of(REAL_ID), real_release()) == as_written


def test_real_figures_are_refused_without_a_registry(tmp_path: Path):
    with pytest.raises(IncomeError) as caught:
        write_income(real(), real_release(), tmp_path)
    assert caught.value.rule == "real_income_needs_a_registry"
    assert list(tmp_path.iterdir()) == []


def test_a_source_that_is_not_approved_or_not_registered_to_be_shown_is_refused(
    tmp_path: Path,
):
    gated = holding(Use.DISPLAY, status=Status.GATED)
    with pytest.raises(RegistryError, match=f"'{SHOWN_ID}' is gated, not approved"):
        write_income(real(), real_release(), tmp_path, gated)
    with pytest.raises(RegistryError, match="is not in the licence registry"):
        write_income(real(), real_release(), tmp_path, Registry(()))
    with pytest.raises(RegistryError):
        write_income(real(), real_release(), tmp_path, holding(Use.VALIDATION_ONLY))
    assert list(tmp_path.iterdir()) == []


def test_real_figures_are_never_written_over(tmp_path: Path):
    registry = holding(Use.DISPLAY)
    write_income(real(), real_release(), tmp_path, registry)
    with pytest.raises(IncomeError) as caught:
        write_income(real(), real_release(), tmp_path, registry)
    assert caught.value.rule == "income_is_never_overwritten"


def test_calling_figures_made_up_does_not_get_a_real_source_past_the_gate(tmp_path: Path):
    disguised = real().replace(synthetic=True)
    with pytest.raises(IncomeError) as caught:
        write_income(disguised, real_release(), tmp_path)
    assert caught.value.rule == "income_is_of_the_release"
    assert list(tmp_path.iterdir()) == []


# --- Apart from what builds the product ------------------------------------------------

# The modules that may name household income. The step that builds a preview writes the
# folder once the release is written and checked: it hands the figures to nothing.
MAY_NAME_IT = {
    PACKAGE / "release" / "income.py",
    PACKAGE / "release" / "cli.py",
    PACKAGE / "release" / "synthetic" / "estimate.py",
    PACKAGE / "derive" / "household_income.py",
    PACKAGE / "assemble" / "cli.py",
}


def test_nothing_that_builds_what_is_ranked_on_imports_household_income():
    for path in sorted(PACKAGE.rglob("*.py")):
        reads = [
            name
            for name in _imports(path)
            if name.startswith(("burro_core.income", "burro_pipeline.release.income"))
            or name.endswith((".household_income", ".estimate"))
        ]
        if path not in MAY_NAME_IT:
            assert not reads, (path.relative_to(PACKAGE), reads)
    # What puts a release together, and what stands behind its figures, is handed none of it.
    for name in ("release.py", "tags.py"):
        path = PACKAGE / "assemble" / name
        if path.exists():
            assert not [one for one in _imports(path) if "income" in one], name
    for path in (PACKAGE / "derive" / "measures.py", PACKAGE / "evidence" / "served.py"):
        assert "income" not in path.read_text(encoding="utf-8").casefold(), path.name
    ours = _imports(PACKAGE / "derive" / "household_income.py")
    assert not [
        name
        for name in ours
        if name.startswith(("burro_core.rank", "burro_core.catalogue", "burro_core.facts"))
    ]


# --- The command ----------------------------------------------------------------------


def test_the_command_builds_the_figures_beside_the_release_and_checks_them(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    releases, shown = tmp_path / "releases", tmp_path / "shown"
    assert main(["build-synthetic", "--out", str(releases), "--income-out", str(shown)]) == 0
    folder = shown / folder_of(RELEASE_ID)
    assert main(["check", str(releases / RELEASE_ID), "--income", str(folder)]) == 0
    built, written_down, checked, held = capsys.readouterr().out.splitlines()
    assert (built, written_down) == (checked, held)
    assert written_down == f"{RELEASE_ID}-income: 24 areas, 23 with an estimate, made up"
    assert packed(made_up())[INCOME] == (folder / INCOME).read_bytes()
    # The line gives counts, and no figure of any area.
    assert not [area for area in made_up().areas if str(area.estimate) in written_down]


def test_the_command_writes_no_figures_unless_it_is_told_where(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    assert main(["build-synthetic", "--out", str(tmp_path)]) == 0
    assert [entry.name for entry in tmp_path.iterdir()] == [RELEASE_ID]
    assert len(capsys.readouterr().out.splitlines()) == 1


def test_the_command_refuses_broken_figures_in_one_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    releases = tmp_path / "releases"
    assert main(["build-synthetic", "--out", str(releases)]) == 0
    folder = written(tmp_path)
    (folder / MANIFEST).write_bytes(b"{")
    capsys.readouterr()
    assert main(["check", str(releases / RELEASE_ID), "--income", str(folder)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"error: {folder}: {MANIFEST} is not valid JSON [json_is_valid]\n"
