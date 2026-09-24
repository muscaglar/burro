"""The draft from files, its outlines, the files it is written as, and the run.

Nothing here is real, and nothing reaches a network or a store of fetched
files. The town is drawn in `assign_files_support.py`.
"""

import csv
import io
import json
import random
from dataclasses import replace
from pathlib import Path

import pytest
from burro_pipeline.areas import assign_files, assign_outline, assign_run, assign_write
from burro_pipeline.areas.assign import NORTH, SOUTH, Rules
from burro_pipeline.areas.assign_files import Ground, SeedPoint
from burro_pipeline.cells import shapes
from burro_pipeline.fetch.store import FOLDER_VARIABLE

from ..cells.support import held
from .assign_files_support import (
    READING,
    SEEDS,
    TOWN,
    contents,
    inputs_of,
    names_zip,
    oa,
    roads,
    seed,
    zipped,
)

ALDERWICK, CINDERMOOR, ESKERFOLD, DULCIMER = (each.seed_id for each in SEEDS)
# No area of the small town is too small, and no two of its seeds are too close.
RULES = Rules(smallest=1, too_close=0.0)


def read(folder: Path, seeds: tuple[SeedPoint, ...] = SEEDS, **files: bytes) -> Ground:
    return assign_files.read_ground(inputs_of(folder, contents() | files), seeds, READING)


def rows_of(written: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(written.decode())))


# The draft, from the files


def test_no_output_area_is_given_across_the_water_though_the_bridge_is_the_shorter_way(
    tmp_path: Path,
):
    found, _, _ = assign_run.drafted(inputs_of(tmp_path, contents()), SEEDS, RULES, READING)
    # By the bridge the seed north of it is 140 m away. The seed of its own bank is 200 m.
    beside_the_bridge = found.given[oa(4, 1)]
    assert beside_the_bridge.area == CINDERMOOR
    assert {found.given[oa(column, row)].area for column in (2, 3, 4, 5) for row in (2, 3)} <= {
        ESKERFOLD,
        DULCIMER,
    }
    assert not found.listed
    assert all(NORTH not in each.banks or SOUTH not in each.banks for each in found.drawn.values())


def test_every_output_area_of_the_files_is_in_exactly_one_area(tmp_path: Path):
    found, ground, outlines = assign_run.drafted(
        inputs_of(tmp_path, contents()), SEEDS, RULES, READING
    )
    assert sorted(found.given) == sorted(made.oa for made in TOWN)
    assert sorted(oa for each in found.drawn.values() for oa in each.cells) == sorted(found.given)
    assert set(outlines.of) == set(found.drawn) == {ALDERWICK, CINDERMOOR, ESKERFOLD, DULCIMER}
    assert all(len(each.pieces) == 1 for each in found.drawn.values())
    assert ground.counted["output_areas"] == 26


def test_a_draft_writes_nothing_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents())
    before = held(tmp_path / "store")
    assign_run.drafted(inputs, SEEDS, RULES, READING)
    assert held(tmp_path / "store") == before


# The outlines


def test_every_area_has_an_outline_in_longitude_and_latitude_and_they_fit_together(
    tmp_path: Path,
):
    _, _, outlines = assign_run.drafted(inputs_of(tmp_path, contents()), SEEDS, RULES, READING)
    assert outlines.fit_together
    drawn = json.loads(assign_write.canonical_json(assign_outline.feature_collection(outlines)))
    assert [feature["id"] for feature in drawn["features"]] == sorted(outlines.of)
    for feature in drawn["features"]:
        assert feature["geometry"]["type"] == "Polygon"
        (ring,) = feature["geometry"]["coordinates"]
        assert ring[0] == ring[-1] and len(ring) > 4
        assert all(
            2.51 < longitude < 2.53 and 53.41 < latitude < 53.42 for longitude, latitude in ring
        )
    for area, outline in outlines.of.items():
        middle = shapes.longitude_and_latitude(
            *next(each.point for each in SEEDS if each.seed_id == area)
        )
        assert outline.pieces == 1
        assert shapes.metres_between(outline.inside, middle) < 400


# The files that are written


def test_the_curated_file_holds_the_seven_columns_of_the_design_and_a_row_for_each_output_area(
    tmp_path: Path,
):
    files = assign_write.files_of(
        *assign_run.drafted(inputs_of(tmp_path, contents()), SEEDS, RULES, READING)
    )
    text = files[assign_write.OA_TO_AREA].decode()
    assert text.splitlines()[0] == "oa21cd,area_id,basis,evidence,decided_by,decided_on,reason"
    rows = rows_of(files[assign_write.OA_TO_AREA])
    assert [row["oa21cd"] for row in rows] == sorted(made.oa for made in TOWN)
    assert {row["basis"] for row in rows} == {"auto"}
    assert {(row["decided_by"], row["decided_on"], row["reason"]) for row in rows} == {("", "", "")}
    assert "\r" not in text and text.endswith("\n")


def test_what_placed_an_output_area_is_said_in_the_keys_the_desk_knows_and_no_other(
    tmp_path: Path,
):
    files = assign_write.files_of(
        *assign_run.drafted(inputs_of(tmp_path, contents()), SEEDS, RULES, READING)
    )
    known = {"margin", "second", "roads", "ward", "msoa", "centre"}
    rows = {row["oa21cd"]: row for row in rows_of(files[assign_write.OA_TO_AREA])}
    for row in rows.values():
        pairs = [pair.split("=") for pair in row["evidence"].split(";")]
        assert all(len(pair) == 2 and pair[0] in known for pair in pairs)
    # Its own seed is 200 m away, less 15% for its roads and 5% for its ward. The next
    # is 500 m away.
    assert rows[oa(4, 1)]["evidence"] == (
        f"margin=209;second={ALDERWICK};roads=Cindermoor;ward=Cindermoor"
    )
    assert rows[oa(0, 0)]["evidence"].endswith("ward=Alderwick")


def test_a_seed_that_stands_for_no_area_is_written_with_what_a_person_needs_to_decide(
    tmp_path: Path,
):
    """With the least size at 7, the two areas of six output areas are each taken in."""
    rules = Rules(smallest=7, too_close=0.0)
    files = assign_write.files_of(
        *assign_run.drafted(inputs_of(tmp_path, contents()), SEEDS, rules, READING)
    )
    taken_in = rows_of(files[assign_write.ABSORBED])
    assert [
        (row["seed_id"], row["into"], row["lies_in"], row["why"], row["output_areas"])
        for row in taken_in
    ] == [
        (CINDERMOOR, ALDERWICK, ALDERWICK, "under_smallest", "6"),
        (ESKERFOLD, DULCIMER, DULCIMER, "under_smallest", "6"),
    ]
    assert {row["weight"] for row in taken_in} == {"6"}
    given = {row["area_id"] for row in rows_of(files[assign_write.OA_TO_AREA])}
    assert given == {ALDERWICK, DULCIMER}
    assert {row["area_id"] for row in rows_of(files[assign_write.AREAS_DRAWN])} == given


def test_a_name_that_holds_a_mark_that_parts_the_evidence_is_left_out_of_it():
    given = assign_write.Given("E00999001", ALDERWICK, "nearest", 12, CINDERMOOR, ())
    assert assign_write.evidence_of(given, "Alderwick") == (
        f"margin=12;second={CINDERMOOR};ward=Alderwick"
    )
    assert assign_write.evidence_of(given, "Alder=wick; East") == f"margin=12;second={CINDERMOOR}"
    assert assign_write.evidence_of(replace(given, margin=None, second=""), "") == ""


def test_the_same_files_in_another_order_give_the_same_bytes(tmp_path: Path):
    first = assign_write.files_of(
        *assign_run.drafted(inputs_of(tmp_path / "a", contents()), SEEDS, RULES, READING)
    )
    drawn = random.Random(5)  # noqa: S311
    mixed = tuple(drawn.sample(SEEDS, len(SEEDS)))
    turned = {
        "roads": zipped("Data/oproad_gb.gpkg", roads(turned=True)),
        "names": names_zip(turned=True),
    }
    again = assign_write.files_of(
        *assign_run.drafted(inputs_of(tmp_path / "b", contents() | turned), mixed, RULES, READING)
    )
    # The files of roads and of names are other files, so their ids in the counts are other.
    counts = assign_write.COUNTS
    assert {name: content for name, content in again.items() if name != counts} == {
        name: content for name, content in first.items() if name != counts
    }
    assert json.loads(again[counts])["draft"] == json.loads(first[counts])["draft"]


# The run


def written_by(tmp_path: Path, seeds: str, out: Path) -> int:
    inputs = inputs_of(tmp_path, contents())
    receipts = tmp_path / "receipts"
    for receipt in inputs.receipts:
        path = receipts / receipt.source_id / f"{receipt.file_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(receipt.model_dump_json(), encoding="utf-8")
    (tmp_path / "seeds.csv").write_text(seeds, encoding="utf-8")
    return assign_run.main(
        [
            *("--seeds", str(tmp_path / "seeds.csv")),
            *("--receipts", str(receipts)),
            *("--out", str(out)),
        ],
        {FOLDER_VARIABLE: str(tmp_path / "store")},
    )


def seeds_csv(seeds: tuple[SeedPoint, ...] = SEEDS) -> str:
    lines = ["name,area_id,weight,northing,easting,seed_id"]
    lines += [
        f"{each.name},{each.seed_id},{each.weight},{each.point[1]},{each.point[0]},{each.record}"
        for each in seeds
    ]
    return "\r\n".join(lines) + "\r\n"


def test_a_run_writes_every_file_of_the_draft_and_prints_counts_alone(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    # The least size and the reading are the real ones, so the small town is one area.
    assert written_by(tmp_path, seeds_csv(), tmp_path / "out") == 0
    assert sorted(path.name for path in (tmp_path / "out").iterdir()) == sorted(
        [
            *("absorbed.csv", "areas_drawn.csv", "cells.csv", "counts.json", "listed.csv"),
            *("oa_evidence.csv", "oa_to_area.csv", "outlines.geojson", "sides.csv"),
        ]
    )
    printed = capsys.readouterr()
    assert printed.err == ""
    assert printed.out.startswith("step=areas-draft status=ok output_areas=26 ")
    assert all(pair.split("=")[1].isdigit() for pair in printed.out.split()[2:])
    assert "Alderwick" not in printed.out and "E00999" not in printed.out


def test_an_area_takes_the_id_the_seeds_give_it_where_they_give_one(tmp_path: Path):
    lines = ["seed_id,area_id,easting,northing,weight,kind"]
    lines += [
        f"{each.record},{each.seed_id},{each.point[0]},{each.point[1]},6,made up" for each in SEEDS
    ]
    (tmp_path / "seeds.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    found = assign_run.read_seeds(tmp_path / "seeds.csv")
    assert found == [replace(each, name="") for each in SEEDS]


def test_a_run_stops_at_seeds_that_are_no_table_of_points(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    for number, wrong in enumerate(
        (
            "area_id,easting,northing,weight\nsyn-n0001,1,2,3\n",
            "seed_id,easting,northing\nsyn-n0001,1,2\n",
            "seed_id,easting,northing,weight\nsyn-n0001,east,2,3\n",
            "seed_id,easting,northing,weight\nsyn-n0001,1,2,nan\n",
            "seed_id,easting,northing,weight\n",
            seeds_csv((*SEEDS, SEEDS[0])),
        )
    ):
        assert written_by(tmp_path / str(number), wrong, tmp_path / "out") == 2
        assert capsys.readouterr().err.startswith("error: ")
    assert not (tmp_path / "out").exists()


def test_a_run_writes_nothing_into_a_folder_that_git_tracks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    tracked = Path(assign_files.__file__).parent / "drafted"
    assert written_by(tmp_path, seeds_csv(), tracked) == 2
    assert "git tracks" in capsys.readouterr().err
    assert not tracked.exists()


def test_a_seed_may_stand_for_no_name_and_no_record(tmp_path: Path):
    bare = tuple(replace(each, name="", record="") for each in SEEDS)
    found = read(tmp_path, bare)
    assert all(not said.favours for cell in found.cells for said in cell.said)
    assert replace(seed(1, "", 0, 0), record="") in bare
