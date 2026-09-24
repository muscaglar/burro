"""The step `cells`, run as a person runs it, on made-up files.

The town is Quillhaven and Tallowgate, which do not exist. Its files are put in
a store of their own with a receipt for each, as fetch would leave them, and
the step is run on them through the pipeline's one command line.
"""

import csv
import io
import json
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline import cli
from burro_pipeline.cells import cli as cells
from burro_pipeline.cells import outline, spine
from burro_pipeline.evidence.served import module_is_found
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.fetch.store import FOLDER_VARIABLE
from public_log import is_public

from .support import CANARY, LONDON, REPOSITORY, contents, held, inputs_of, lookup_csv

RELEASE = "lon-2026-09-23-01"
REGISTRY = REPOSITORY / "registry" / "sources"
Printed = pytest.CaptureFixture[str]


def made(folder: Path, **files: bytes) -> list[str]:
    """A store and a folder of receipts, and the arguments that run the step on them."""
    inputs = inputs_of(folder, contents() | files)
    for receipt in inputs.receipts:
        kept = folder / "receipts" / receipt.source_id / f"{receipt.file_id}.json"
        kept.parent.mkdir(parents=True, exist_ok=True)
        kept.write_bytes(receipt.canonical())
    return [
        "cells",
        *("--release-id", RELEASE),
        *("--out", str(folder / "out")),
        *("--receipts", str(folder / "receipts")),
        *("--registry", str(REGISTRY)),
    ]


def run(folder: Path, arguments: list[str]) -> int:
    return cells.main(arguments, {FOLDER_VARIABLE: str(folder / "store")})


def test_the_step_writes_its_five_files_and_prints_one_line_of_counts(
    tmp_path: Path, capsys: Printed
):
    assert run(tmp_path, made(tmp_path)) == 0
    out = capsys.readouterr()
    assert out.err == ""
    (line,) = out.out.splitlines()
    assert is_public(line)
    assert line.startswith(
        f"step=cells status=ok release={RELEASE} areas=3 output_areas=12 lsoas=6 msoas=3 "
        "boroughs=2 files=4 rows=6 development=1 evidence_sha256="
    )
    assert sorted(path.name for path in (tmp_path / "out").iterdir()) == [
        "areas.json",
        "cells.csv",
        "evidence.json",
        "geometry.json",
        "land.csv",
    ]


def test_what_it_prints_names_no_area_and_repeats_nothing_from_a_file(
    tmp_path: Path, capsys: Printed
):
    assert run(tmp_path, made(tmp_path)) == 0
    said = "".join(capsys.readouterr())
    for word in (CANARY, "Quillhaven", "Tallowgate", "E00999", "lon-n", str(tmp_path)):
        assert word not in said


def written(folder: Path) -> dict[str, Any]:
    return {
        path.name: json.loads(path.read_bytes()) for path in sorted((folder / "out").glob("*.json"))
    }


def test_an_area_is_written_with_its_label_its_place_its_homes_and_its_land(
    tmp_path: Path, capsys: Printed
):
    assert run(tmp_path, made(tmp_path)) == 0
    areas = written(tmp_path)["areas.json"]["areas"]
    assert [area["name"] for area in areas] == [
        "Quillhaven 001",
        "Quillhaven 002",
        "Tallowgate 001",
    ]
    first = areas[0]
    assert first | {"centroid": None} == {
        "area_id": "lon-ne02999001",
        "msoa21cd": "E02999001",
        "name": "Quillhaven 001",
        "slug": "quillhaven-001",
        "borough": "Quillhaven",
        "lad22cd": "E09000901",
        "centroid": None,
        "neighbours": ["lon-ne02999002"],
        "homes": sum(unit.homes for unit in LONDON[:4]),
        "hectares": 4.0,
    }
    longitude, latitude = first["centroid"]
    assert 2.5 < longitude < 2.6 and 53.4 < latitude < 53.5


def test_every_output_area_and_every_lsoa_is_written_once(tmp_path: Path, capsys: Printed):
    assert run(tmp_path, made(tmp_path)) == 0
    text = (tmp_path / "out" / "cells.csv").read_text(encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(text)))
    assert [row["oa21cd"] for row in rows] == sorted(unit.oa for unit in LONDON)
    assert rows[0] == {
        "oa21cd": "E00999001",
        "lsoa21cd": "E01999001",
        "msoa21cd": "E02999001",
        "lad22cd": "E09000901",
        "area_id": "lon-ne02999001",
        "homes": "110",
    }
    land = (tmp_path / "out" / "land.csv").read_text(encoding="utf-8").splitlines()
    assert land[:2] == ["lsoa21cd,hectares", "E01999001,2.0000"]
    assert len(land) == 1 + 6


def test_the_evidence_traces_each_label_and_each_outline_to_the_hash_of_a_file(
    tmp_path: Path, capsys: Printed
):
    assert run(tmp_path, made(tmp_path)) == 0
    evidence = Evidence.model_validate_json((tmp_path / "out" / "evidence.json").read_bytes())
    files = contents()
    stored = {receipt.sha256: receipt.source_id for receipt in evidence.receipts}
    assert set(stored.values()) == {spine.LOOKUP, outline.BOUNDARIES}
    assert set(stored) == {
        inputs.sha256
        for inputs in inputs_of(tmp_path / "again", files).receipts
        if inputs.source_id in stored.values()
    }
    for area in ("lon-ne02999001", "lon-ne02999002", "lon-ne02999003"):
        name, boundary = evidence.row(f"{area}/area/name"), evidence.row(f"{area}/area/boundary")
        assert name is not None and boundary is not None
        assert name.derivation_id == "published_label@1" and len(name.inputs) == 1
        assert boundary.derivation_id == "outline_of_output_areas@1"
        assert (boundary.units_used, boundary.units_expected, boundary.state) == (4, 4, "present")
        assert evidence.sources_of(boundary) == {spine.LOOKUP, outline.BOUNDARIES}
    assert all(module_is_found(method.code) for method in evidence.methods)


def test_the_same_files_give_the_same_bytes(tmp_path: Path, capsys: Printed):
    assert run(tmp_path / "a", made(tmp_path / "a")) == 0
    assert run(tmp_path / "b", made(tmp_path / "b")) == 0
    assert held(tmp_path / "a" / "out") == held(tmp_path / "b" / "out")


def test_nothing_is_written_to_the_store_and_no_copy_of_a_file_is_left(
    tmp_path: Path, capsys: Printed
):
    arguments = made(tmp_path)
    before = held(tmp_path / "store")
    assert run(tmp_path, arguments) == 0
    assert held(tmp_path / "store") == before
    assert not list((tmp_path / "out").rglob("*.gpkg"))


# What stops it


def test_a_file_changed_in_the_store_is_refused_by_its_rule_and_nothing_is_written(
    tmp_path: Path, capsys: Printed
):
    arguments = made(tmp_path)
    kept = next((tmp_path / "store" / "raw" / spine.LOOKUP).rglob("*.csv"))
    kept.write_bytes(kept.read_bytes() + f"{CANARY}\n".encode())
    assert run(tmp_path, arguments) == 2
    out = capsys.readouterr()
    (line,) = out.out.splitlines()
    assert is_public(line)
    assert line.startswith("step=cells status=refused file_is_in_the_vault=1 file_id=f-")
    assert "[file_is_in_the_vault]" in out.err and CANARY not in out.err
    assert not (tmp_path / "out").exists()


def test_a_file_that_is_not_what_the_step_reads_is_refused_and_not_repeated(
    tmp_path: Path, capsys: Printed
):
    columns = ["OA21CD", CANARY]
    assert run(tmp_path, made(tmp_path, lookup=lookup_csv(columns=columns))) == 2
    out = capsys.readouterr()
    assert out.out.startswith("step=cells status=refused input_is_as_described=1 file_id=f-")
    assert "a column is missing" in out.err and "describe" in out.err
    assert CANARY not in out.err + out.out


def test_a_folder_that_holds_something_is_never_written_over(tmp_path: Path, capsys: Printed):
    arguments = made(tmp_path)
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "areas.json").write_text("made up\n", encoding="utf-8")
    assert run(tmp_path, arguments) == 2
    assert capsys.readouterr().out == "step=cells status=unreadable\n"
    assert (tmp_path / "out" / "areas.json").read_text(encoding="utf-8") == "made up\n"


def test_with_no_store_named_the_step_does_not_start(tmp_path: Path, capsys: Printed):
    assert cells.main(made(tmp_path), {}) == 2
    out = capsys.readouterr()
    assert out.out == "step=cells status=unreadable\n"
    assert FOLDER_VARIABLE in out.err and str(tmp_path) not in out.err


@pytest.mark.parametrize("release_id", ["syn-2026-09-23-01", "lon-2026-09-23", "Zzyzx Parva"])
def test_an_id_that_is_no_release_of_london_stops_it_before_a_file_is_read(
    tmp_path: Path, capsys: Printed, release_id: str
):
    arguments = made(tmp_path)
    arguments[arguments.index("--release-id") + 1] = release_id
    assert run(tmp_path, arguments) == 2
    out = capsys.readouterr()
    assert out.out == "step=cells status=unreadable\n"
    assert "--release-id" in out.err and release_id not in out.err
    assert not (tmp_path / "out").exists() and not (tmp_path / "work").exists()


def test_it_is_a_step_of_the_pipelines_one_command_line(tmp_path: Path, capsys: Printed):
    assert "cells" in cli.STEPS
    arguments = made(tmp_path)
    assert cli.parse(arguments).command == "cells"
