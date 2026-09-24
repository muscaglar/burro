"""A release that is not made up is served only with what it was built with.

The build is the made-up build of the tests of assemble: a town that does not
exist, from files that are made up. Each test damages a copy of what the step
wrote, as a checker did to the first real build, and holds that the release is
then refused by `read_served` and by `burro-release check`.
"""

import hashlib
import io
import json
import shutil
import tempfile
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

import pytest
from burro_core.release import EVIDENCE, HASHES, LOCK, MANIFEST
from burro_pipeline.derive.measures import behind
from burro_pipeline.evidence.lock import read_lock
from burro_pipeline.evidence.served import unevidenced
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry import load
from burro_pipeline.release.cli import main as burro_release
from burro_pipeline.release.read import UnreadableRelease, read_release, read_served
from burro_pipeline.release.write import canonical_json, packed

from ..evidence.support import real_release
from .support import (
    ONE,
    REGISTRY,
    RELEASE,
    THREE,
    Made,
    made,
)

Printed = pytest.CaptureFixture[str]
FIGURE = f"{ONE}/feature/homes_flats"
# A measure that is a part of one vibe the build can place, Built age, and of no other. So
# the row of that vibe rests on it, and no other row of a vibe does.
OLD_HOMES = f"{ONE}/feature/homes_pre1919"
# A vibe the build can place: flats and homes per hectare are 75 in 100 of its recipe.
HOMES = f"{ONE}/tag/homes"
# Tallowgate lies on two squares of the grid, so its green cover rests on the file of each.
ON_TWO_SQUARES = f"{THREE}/feature/green_cover"
SITES, TABLES = "os-open-greenspace", "voa-council-tax-stock-of-properties"
REGISTER = "fsa-food-hygiene-ratings"


def is_the_town(name: str) -> bool:
    """Whether a file is the one square the town itself stands on."""
    return name == "opgrsp_gml3_tc.zip"


@pytest.fixture(scope="module")
def build(tmp_path_factory: pytest.TempPathFactory) -> Made:
    """The made-up build. It carries green cover, whose product is cut to squares."""
    found = made(tmp_path_factory.mktemp("built"))
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert found.run() == 0
    return found


@pytest.fixture
def copy(build: Made, tmp_path: Path) -> Made:
    """A copy of what was built, for a test to damage."""
    shutil.copytree(build.out, tmp_path / "out")
    return Made(tmp_path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rewrite(path: Path, change: Callable[[Any], object]) -> None:
    document = json.loads(path.read_bytes())
    change(document)
    path.write_bytes(canonical_json(document))


def rehash_the_manifest(release: Path) -> None:
    """Make the manifest agree with the files as they now are, as a careless hand would."""

    def agree(manifest: Any) -> None:
        for entry in manifest["files"]:
            content = (release / entry["name"]).read_bytes()
            entry.update(sha256=hashlib.sha256(content).hexdigest(), bytes=len(content))

    rewrite(release / MANIFEST, agree)


def rehash_the_build(copy: Made) -> None:
    """Make the hashes of the build agree with what stands there now."""
    rewrite(
        copy.beside / HASHES,
        lambda hashes: hashes.update(
            manifest_sha256=sha256(copy.release / MANIFEST),
            evidence_sha256=sha256(copy.beside / EVIDENCE),
            lock_sha256=sha256(copy.beside / LOCK),
        ),
    )


def raise_a_figure(release: Path) -> None:
    def raised(features: Any) -> None:
        row = next(row for row in features["rows"] if row["value"] is not None)
        row["value"] = row["value"] + 20

    rewrite(release / "features.json", raised)
    rehash_the_manifest(release)


def refused(folder: Path) -> tuple[str, str]:
    with pytest.raises(UnreadableRelease) as stopped:
        read_served(folder)
    return stopped.value.file, stopped.value.rule


def checked(
    copy: Made, capsys: Printed, registry: Path = REGISTRY, receipts: Path | None = None
) -> tuple[int, str, str]:
    arguments = ["check", str(copy.release), "--registry", str(registry)]
    status = burro_release([*arguments, *(["--receipts", str(receipts)] if receipts else [])])
    said = capsys.readouterr()
    return status, said.out, said.err


def registry_with(folder: Path, source_id: str, old: str, new: str) -> Path:
    """A copy of the licence registry in which one entry says something else of its source."""
    changed = folder / "registry"
    changed.mkdir()
    for path in REGISTRY.glob("*.toml"):
        text = path.read_text(encoding="utf-8")
        before, entry, after = text.partition(f'id = "{source_id}"')
        if entry:
            rest, mark, others = after.partition("\n[[source]]")
            assert rest.count(old) == 1
            text = before + entry + rest.replace(old, new) + mark + others
        (changed / path.name).write_text(text, encoding="utf-8")
    return changed


# What the step writes


def test_the_step_writes_the_hashes_of_the_build_beside_the_release(build: Made):
    hashes = json.loads((build.beside / HASHES).read_bytes())
    assert hashes == {
        "release_id": RELEASE,
        "manifest_sha256": sha256(build.release / MANIFEST),
        "evidence_sha256": sha256(build.beside / EVIDENCE),
        "lock_sha256": sha256(build.beside / LOCK),
    }


def test_the_release_is_served_as_it_was_built(build: Made):
    assert read_served(build.release) == read_release(build.release)


def test_the_command_checks_the_release_and_the_evidence_behind_it(build: Made, capsys: Printed):
    status, out, err = checked(build, capsys)
    assert (status, err) == (0, "")
    assert out.splitlines() == [
        f"{RELEASE}: 3 areas (3 rankable), 23 measures, 0 destinations, 0 places, 0 stations, "
        "real, a preview, with evidence behind every fact"
    ]


# What is refused


def test_a_release_with_nothing_beside_it_is_not_served(copy: Made, capsys: Printed):
    """The app served such a release. A figure with no evidence behind it is not a figure."""
    shutil.rmtree(copy.beside)
    assert refused(copy.release) == (HASHES, "real_release_has_its_build")
    status, out, err = checked(copy, capsys)
    assert (status, out) == (2, "")
    assert "[real_release_has_its_build]" in err and err.count("\n") == 1


@pytest.mark.parametrize("missing", [HASHES, EVIDENCE, LOCK])
def test_a_release_that_lacks_a_file_of_its_build_is_not_served(copy: Made, missing: str):
    (copy.beside / missing).unlink()
    assert refused(copy.release) == (missing, "real_release_has_its_build")


def test_a_figure_raised_after_the_build_is_refused_though_the_manifest_agrees(
    copy: Made, capsys: Printed
):
    raise_a_figure(copy.release)
    assert read_release(copy.release).manifest.synthetic is False
    assert refused(copy.release) == (MANIFEST, "build_is_as_it_was_written")
    assert checked(copy, capsys)[0] == 2


def test_a_figure_raised_after_the_build_is_found_though_every_hash_agrees(
    copy: Made, capsys: Printed
):
    """With the hashes made to agree too, the figure is held to its row of evidence."""
    raise_a_figure(copy.release)
    rehash_the_build(copy)
    assert read_served(copy.release).manifest.synthetic is False
    status, out, err = checked(copy, capsys)
    assert (status, out) == (1, "")
    assert "1 fact may not be served" in err and "[row_holds_the_figure]" in err
    assert "lon-n" not in err


@pytest.mark.parametrize("changed", [EVIDENCE, LOCK])
def test_evidence_or_a_lock_changed_after_the_build_is_refused(copy: Made, changed: str):
    """Evidence that was changed stayed well formed, and nothing minded."""
    (copy.beside / changed).write_bytes((copy.beside / changed).read_bytes() + b" ")
    assert refused(copy.release) == (changed, "build_is_as_it_was_written")


def test_a_row_taken_out_of_the_evidence_is_found_though_every_hash_agrees(
    copy: Made, capsys: Printed
):
    def take_out(evidence: Any) -> None:
        evidence["rows"] = [row for row in evidence["rows"] if row["fact_id"] != FIGURE]

    rewrite(copy.beside / EVIDENCE, take_out)
    rehash_the_build(copy)
    status, _, err = checked(copy, capsys)
    assert status == 1
    assert "[fact_has_a_row]" in err


def test_a_figure_whose_evidence_names_another_method_is_found(copy: Made, capsys: Printed):
    """A checker changed the method of a measure to another the evidence held. Nothing minded."""

    def another_method(evidence: Any) -> None:
        for row in evidence["rows"]:
            if row["fact_id"].endswith("/feature/air_no2") and row["derivation_id"]:
                row["derivation_id"] = "area_row_ratio@1"

    rewrite(copy.beside / EVIDENCE, another_method)
    rehash_the_build(copy)
    status, _, err = checked(copy, capsys)
    assert status == 1
    assert "[row_names_its_method]" in err


def test_a_figure_whose_evidence_rests_on_the_file_of_another_measure_is_found(
    copy: Made, capsys: Printed
):
    """Flats and homes built before 1919 cite one source. A checker swapped their evidence."""

    def swapped(evidence: Any) -> None:
        rows = {row["fact_id"]: row for row in evidence["rows"]}
        for fact_id, row in list(rows.items()):
            if fact_id.endswith("/feature/homes_flats"):
                other = rows[fact_id.replace("homes_flats", "homes_pre1919")]
                row["inputs"], other["inputs"] = other["inputs"], row["inputs"]

    rewrite(copy.beside / EVIDENCE, swapped)
    rehash_the_build(copy)
    status, _, err = checked(copy, capsys)
    assert status == 1
    assert "[row_rests_on_its_file]" in err


# The receipts in the evidence, the lock, and the receipts that were committed


def test_the_release_is_held_to_the_receipts_that_were_committed(build: Made, capsys: Printed):
    status, _, err = checked(build, capsys, receipts=build.receipts)
    assert (status, err) == (0, "")


def test_a_receipt_changed_in_the_evidence_is_found_though_every_hash_agrees(
    build: Made, copy: Made, capsys: Printed
):
    """A checker gave a receipt another edition and another address. Only its id was compared."""

    def another_edition(evidence: Any) -> None:
        receipt = next(r for r in evidence["receipts"] if r["source_id"] == TABLES)
        receipt.update(edition="2019", url="https://files.made-up.example/another")

    rewrite(copy.beside / EVIDENCE, another_edition)
    rehash_the_build(copy)
    # Nothing in the release or beside it says what the receipt said when it was written.
    assert checked(copy, capsys)[0] == 0
    status, out, err = checked(copy, capsys, receipts=build.receipts)
    assert (status, out) == (1, "")
    assert "1 fact may not be served: 1 [receipt_is_as_committed]" in err


def test_a_receipt_of_another_file_under_the_same_id_is_found(copy: Made, capsys: Printed):
    """The id of a file is the first twelve digits of its hash. The rest was never compared."""

    def another_file(evidence: Any) -> None:
        receipt = next(r for r in evidence["receipts"] if r["source_id"] == TABLES)
        receipt.update(sha256=receipt["sha256"][:12] + "0" * 52, bytes=receipt["bytes"] + 1)

    rewrite(copy.beside / EVIDENCE, another_file)
    rehash_the_build(copy)
    status, out, err = checked(copy, capsys)
    assert (status, out) == (1, "")
    assert "1 fact may not be served: 1 [receipt_is_the_locked_file]" in err


def test_a_file_changed_in_the_lock_is_found_though_every_hash_agrees(copy: Made, capsys: Printed):
    def another_file(lock: Any) -> None:
        held = next(one for one in lock["inputs"] if one["source_id"] == TABLES)
        held.update(sha256=held["sha256"][:12] + "0" * 52)

    rewrite(copy.beside / LOCK, another_file)
    rehash_the_build(copy)
    status, out, err = checked(copy, capsys)
    assert (status, out) == (1, "")
    assert "[receipt_is_the_locked_file]" in err


# The row of a tag


def test_a_tag_whose_evidence_names_the_method_of_a_measure_is_found(copy: Made, capsys: Printed):
    """The first tag with a score had a row that named the method of a share, and passed."""

    def another_method(evidence: Any) -> None:
        for row in evidence["rows"]:
            if row["fact_id"].endswith("/tag/homes") and row["value"] is not None:
                row["derivation_id"] = "area_row_ratio@1"

    rewrite(copy.beside / EVIDENCE, another_method)
    rehash_the_build(copy)
    status, _, err = checked(copy, capsys)
    assert status == 1
    assert "3 facts may not be served: 3 [row_names_its_method]" in err


def test_a_tag_whose_evidence_rests_on_the_files_of_another_measure_is_found(
    copy: Made, capsys: Printed
):
    def of_old_homes_too(evidence: Any) -> None:
        """Homes built before 1919 are no part of the recipe of Homes.

        Their table is of the source of flats and of density, which are.
        """
        rows = {row["fact_id"]: row for row in evidence["rows"]}
        tag = rows[HOMES]
        tag["inputs"] = sorted({*tag["inputs"], *rows[OLD_HOMES]["inputs"]})

    before = json.loads((copy.beside / EVIDENCE).read_bytes())
    assert len(files_of(before, HOMES, TABLES)) == 2
    rewrite(copy.beside / EVIDENCE, of_old_homes_too)
    changed = json.loads((copy.beside / EVIDENCE).read_bytes())
    assert len(files_of(changed, HOMES, TABLES)) == 3
    rehash_the_build(copy)
    status, _, err = checked(copy, capsys)
    assert status == 1
    assert "1 fact may not be served: 1 [row_rests_on_its_file]" in err


# The credit of a source


def test_a_credit_changed_in_the_manifest_is_found_though_every_hash_agrees(
    copy: Made, capsys: Printed
):
    """A checker changed the credit of a source to a word of its own, under another licence."""

    def ours(manifest: Any) -> None:
        source = next(one for one in manifest["sources"] if one["source_id"] == SITES)
        source.update(attribution="Made up.", licence="CC0-1.0")

    rewrite(copy.release / MANIFEST, ours)
    rehash_the_build(copy)
    status, out, err = checked(copy, capsys)
    assert (status, out) == (1, "")
    assert "1 fact may not be served: 1 [credit_is_the_registrys]" in err


# What core works out: where an area stands among the areas, and its tags


def test_a_percentile_moved_after_the_build_is_found_though_every_hash_agrees(
    copy: Made, capsys: Printed
):
    """An area is ranked on its percentile. One was moved with every figure left true."""

    def moved(features: Any) -> None:
        row = next(row for row in features["rows"] if row["percentile"] is not None)
        row["percentile"] = 99.9 if row["percentile"] != 99.9 else 0.1

    rewrite(copy.release / "features.json", moved)
    rehash_the_manifest(copy.release)
    rehash_the_build(copy)
    # Core now holds a percentile to its figures when it opens a release, so the release is
    # refused before its evidence is read. `percentile_is_cores` holds a release that was
    # never written to a folder.
    assert refused(copy.release) == ("features.json", "percentiles_match_values")
    status, out, err = checked(copy, capsys)
    assert (status, out) == (2, "")
    assert "[percentiles_match_values]" in err


def test_a_tag_said_to_rest_on_more_of_its_recipe_is_found_though_every_hash_agrees(
    copy: Made, capsys: Printed
):
    def whole(tags: Any) -> None:
        # Homes, by its name: it rests on 75 in 100 of its recipe, whatever else is placed.
        rows = (row for row in tags["rows"] if row["tag_id"] == "homes")
        row = next(row for row in rows if row["score"] is not None)
        assert row["coverage"] == 0.75
        row["coverage"] = 1.0

    rewrite(copy.release / "tags.json", whole)
    rehash_the_manifest(copy.release)
    rehash_the_build(copy)
    # Core now holds a vibe to its recipe when it opens a release, so the release is refused
    # before its evidence is read. `tag_is_cores` and `row_holds_the_coverage` hold a release
    # that was never written to a folder.
    assert refused(copy.release) == ("tags.json", "raw_matches_recipe")
    status, out, err = checked(copy, capsys)
    assert (status, out) == (2, "")
    assert "[raw_matches_recipe]" in err


# The licence registry, as it stands on the day a release is checked


def test_a_release_is_found_once_the_registry_gates_a_source_it_rests_on(
    build: Made, tmp_path: Path, capsys: Printed
):
    """A checker gated the source of the sites after the build, and the release still passed."""
    gated = registry_with(
        tmp_path,
        SITES,
        'status = "approved"',
        'status = "gated"\nstatus_reason = "Made up for a test: its terms are being read again."',
    )
    status, out, err = checked(build, capsys, gated)
    assert (status, out) == (1, "")
    assert "[input_is_allowed]" in err
    assert "lon-n" not in err and SITES not in err


def test_a_release_is_found_once_the_registry_no_longer_allows_a_source_for_scoring(
    build: Made, tmp_path: Path, capsys: Printed
):
    shown_only = registry_with(
        tmp_path, SITES, 'uses = ["scoring", "display"]', 'uses = ["display"]'
    )
    status, out, err = checked(build, capsys, shown_only)
    assert (status, out) == (1, "")
    assert "[input_is_allowed]" in err


# A product that its publisher cuts to squares of the grid, a file for each


def files_of(evidence: Any, fact_id: str, source_id: str) -> list[str]:
    """The publisher's names of the files of one source that a row rests on."""
    named = {
        receipt["file_id"]: receipt["publisher_file"]
        for receipt in evidence["receipts"]
        if receipt["source_id"] == source_id
    }
    row = next(row for row in evidence["rows"] if row["fact_id"] == fact_id)
    return sorted(named[file_id] for file_id in row["inputs"] if file_id in named)


def test_a_figure_at_the_edge_of_a_square_rests_on_the_file_of_each_square(
    build: Made, capsys: Printed
):
    evidence = json.loads((build.beside / EVIDENCE).read_bytes())
    assert files_of(evidence, ON_TWO_SQUARES, SITES) == ["opgrsp_gml3_tc.zip", "opgrsp_gml3_th.zip"]
    assert files_of(evidence, f"{ONE}/feature/green_cover", SITES) == ["opgrsp_gml3_tc.zip"]
    status, _, err = checked(build, capsys)
    assert (status, err) == (0, "")


def test_a_figure_of_sites_that_rests_on_no_file_of_sites_is_found(copy: Made, capsys: Printed):
    """The row is left a row that the evidence takes: its period is that of the files it keeps."""

    def no_square(evidence: Any) -> None:
        of = {receipt["file_id"]: receipt["source_id"] for receipt in evidence["receipts"]}
        for row in evidence["rows"]:
            if row["fact_id"] == ON_TWO_SQUARES:
                row["inputs"] = [file_id for file_id in row["inputs"] if of[file_id] != SITES]
                row["data_period"] = {"as_at": None, "start": "2021-03-21", "end": "2022-12-31"}

    rewrite(copy.beside / EVIDENCE, no_square)
    rehash_the_build(copy)
    status, _, err = checked(copy, capsys)
    assert status == 1
    assert "[row_rests_on_its_file]" in err


def test_a_figure_of_sites_is_held_to_the_squares_its_measure_reads(build: Made):
    release = read_release(build.release)
    evidence = Evidence.model_validate_json((build.beside / EVIDENCE).read_bytes())
    lock, registry, held = read_lock(build.beside / LOCK), load(REGISTRY), behind()
    assert unevidenced(release, evidence, lock, registry, held) == ()
    green = held["green_cover"]
    # A measure that read one square alone may not rest on the file of another.
    one_square = green._replace(reads=is_the_town)
    found = unevidenced(release, evidence, lock, registry, held | {"green_cover": one_square})
    assert [(one.fact_id, one.rule) for one in found] == [(ON_TWO_SQUARES, "row_rests_on_its_file")]


def test_a_measure_that_is_not_cut_to_squares_is_held_to_one_file_as_before(
    build: Made, copy: Made, capsys: Printed
):
    """Only a measure that says its product is cut to squares may rest on more than one file."""
    release = read_release(build.release)
    evidence = Evidence.model_validate_json((build.beside / EVIDENCE).read_bytes())
    lock, registry, held = read_lock(build.beside / LOCK), load(REGISTRY), behind()
    assert [name for name, one in held.items() if one.in_squares] == [
        "green_cover",
        "park_facilities",
        "park_large_proximity",
        "park_proximity",
        "play_space_proximity",
    ]
    as_one_file = held | {"green_cover": held["green_cover"]._replace(in_squares=False)}
    found = unevidenced(release, evidence, lock, registry, as_one_file)
    assert [(one.fact_id, one.rule) for one in found] == [(ON_TWO_SQUARES, "row_rests_on_its_file")]

    def a_second_table(evidence: Any) -> None:
        # Of a measure that one placed vibe rests on, so that two rows are at fault: the row
        # of the measure, and the row of Built age, which is held to the files of its parts.
        rows = {row["fact_id"]: row for row in evidence["rows"]}
        rows[OLD_HOMES]["inputs"] = sorted({*rows[OLD_HOMES]["inputs"], *rows[FIGURE]["inputs"]})

    rewrite(copy.beside / EVIDENCE, a_second_table)
    assert len(files_of(json.loads((copy.beside / EVIDENCE).read_bytes()), OLD_HOMES, TABLES)) == 2
    rehash_the_build(copy)
    status, _, err = checked(copy, capsys)
    assert status == 1
    assert "2 facts may not be served: 2 [row_rests_on_its_file]" in err


# A register that its publisher gives as a file for each authority


@pytest.fixture(scope="module")
def with_the_count(tmp_path_factory: pytest.TempPathFactory) -> Made:
    """The made-up build, which carries the places to eat and drink.

    What is held of a row that rests on a file for each authority is held on it.
    """
    found = made(tmp_path_factory.mktemp("with-the-count"))
    quiet = redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO())
    with quiet[0], quiet[1]:
        assert found.run() == 0
    return found


def test_a_figure_of_the_register_rests_on_the_file_of_every_authority(
    with_the_count: Made, capsys: Printed
):
    """Nought is a count only because the register is whole, so a row names all of it."""
    evidence = json.loads((with_the_count.beside / EVIDENCE).read_bytes())
    for area in (ONE, THREE):
        assert files_of(evidence, f"{area}/feature/venue_food_drink", REGISTER) == [
            "FHRS901en-GB.xml",
            "FHRS902en-GB.xml",
        ]
    status, _, err = checked(with_the_count, capsys)
    assert (status, err) == (0, "")


def test_a_figure_of_the_register_that_rests_on_some_of_its_files_is_found(
    with_the_count: Made, tmp_path: Path, capsys: Printed
):
    """A row that names the file of one authority and not of the other is no count of nought."""
    shutil.copytree(with_the_count.out, tmp_path / "out")
    copy = Made(tmp_path)
    figure = f"{ONE}/feature/venue_food_drink"

    def one_authority(evidence: Any) -> None:
        named = {
            receipt["file_id"]: receipt["publisher_file"]
            for receipt in evidence["receipts"]
            if receipt["source_id"] == REGISTER
        }
        row = next(row for row in evidence["rows"] if row["fact_id"] == figure)
        row["inputs"] = [f for f in row["inputs"] if named.get(f) != "FHRS902en-GB.xml"]

    rewrite(copy.beside / EVIDENCE, one_authority)
    assert files_of(json.loads((copy.beside / EVIDENCE).read_bytes()), figure, REGISTER) == [
        "FHRS901en-GB.xml"
    ]
    rehash_the_build(copy)
    status, _, err = checked(copy, capsys)
    assert status == 1
    assert "1 fact may not be served: 1 [row_rests_on_its_file]" in err


def test_only_a_measure_that_says_so_may_rest_on_a_file_for_each_part(with_the_count: Made):
    """The leave is the register's. A measure of one file is held to one file, as before."""
    release = read_release(with_the_count.release)
    evidence = Evidence.model_validate_json((with_the_count.beside / EVIDENCE).read_bytes())
    lock, registry, held = read_lock(with_the_count.beside / LOCK), load(REGISTRY), behind()
    assert [name for name, one in held.items() if one.in_parts] == [
        "venue_evening",
        "venue_food_drink",
        "venue_food_drink_per_homes",
    ]
    assert not [name for name, one in held.items() if one.in_parts and one.in_squares]
    assert unevidenced(release, evidence, lock, registry, held) == ()
    as_one_file = held | {"venue_food_drink": held["venue_food_drink"]._replace(in_parts=False)}
    found = unevidenced(release, evidence, lock, registry, as_one_file)
    assert {one.rule for one in found} == {"row_rests_on_its_file"}
    assert {one.fact_id.split("/", 1)[1] for one in found} == {"feature/venue_food_drink"}


def test_a_register_with_the_file_of_one_authority_gone_from_the_evidence_is_found_by_the_lock(
    with_the_count: Made, tmp_path: Path, capsys: Printed
):
    """Every row names the file of one authority alone, and the evidence holds no other.

    The lock names every file of the build, so the file that is gone is still known to be
    a part of the whole. The leave for squares would not find it: a figure of squares may
    rest on some files of its source and not on all.
    """
    shutil.copytree(with_the_count.out, tmp_path / "out")
    copy = Made(tmp_path)

    def gone(evidence: Any) -> None:
        (lost,) = [
            receipt["file_id"]
            for receipt in evidence["receipts"]
            if receipt["publisher_file"] == "FHRS902en-GB.xml"
        ]
        evidence["receipts"] = [r for r in evidence["receipts"] if r["file_id"] != lost]
        for row in evidence["rows"]:
            row["inputs"] = [file_id for file_id in row["inputs"] if file_id != lost]

    rewrite(copy.beside / EVIDENCE, gone)
    rehash_the_build(copy)
    release = read_release(copy.release)
    evidence = Evidence.model_validate_json((copy.beside / EVIDENCE).read_bytes())
    lock, registry, held = read_lock(copy.beside / LOCK), load(REGISTRY), behind()
    found = unevidenced(release, evidence, lock, registry, held)
    assert {one.rule for one in found} == {"row_rests_on_its_file"}
    of_the_register = ("venue_food_drink", "venue_food_drink_per_homes")
    with_a_figure = {
        f"{row.area_id}/feature/{row.feature_id}"
        for row in release.features
        if row.feature_id in of_the_register and row.value is not None
    }
    assert {one.fact_id for one in found if "/feature/" in one.fact_id} == with_a_figure
    as_squares = {
        feature: held[feature]._replace(in_parts=False, in_squares=True)
        for feature in of_the_register
    }
    lenient = unevidenced(release, evidence, lock, registry, held | as_squares)
    assert not [one for one in lenient if "/feature/" in one.fact_id]
    status, _, err = checked(copy, capsys)
    assert status == 1 and "[row_rests_on_its_file]" in err


def test_the_made_up_release_under_real_ids_is_not_served():
    """A checker renamed every id of the synthetic release and flipped its flag. It was served."""
    with tempfile.TemporaryDirectory() as folder:
        release = real_release()
        target = Path(folder) / release.manifest.release_id
        target.mkdir()
        for name, content in packed(release).items():
            (target / name).write_bytes(content)
        assert read_release(target).manifest.synthetic is False
        assert refused(target) == (HASHES, "real_release_has_its_build")
