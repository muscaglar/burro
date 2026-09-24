"""What a build of London does with primary schools close by, from the real files.

Every other test of a build with schools runs on made-up files. This builds
from the files their publishers gave, with the list that holds the register
of schools among its lists, and is skipped where the store of fetched files is
not. The store is named by BURRO_STORE_FOLDER.

It holds what the build says of the measure, and no figure. Nothing is
written to the store.
"""

import json
import os
from pathlib import Path
from typing import Any

import pytest
from burro_core.ids import FeatureId, TagId
from burro_pipeline.assemble import cli as assemble
from burro_pipeline.derive import school_primary_nearby
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.fetch.store import FOLDER_VARIABLE
from burro_pipeline.release import read_release

from ..cells.support import REPOSITORY

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"


def has_a_receipt() -> bool:
    return RECEIPTS.is_dir() and any(
        receipt.source_id == school_primary_nearby.SOURCE for receipt in read_receipts(RECEIPTS)
    )


pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and has_a_receipt()),
    reason=f"the register is not here: {FOLDER_VARIABLE} names no folder, or it has no receipt",
)
RELEASE = "lon-2026-09-24-01"
# The register of schools is a file of the third list.
LISTS = ("m1", "m2-places", "m2-living")
FEATURE = FeatureId.SCHOOL_PRIMARY_NEARBY
REGISTER = "f-e2cf7e0c0508"


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, list[str]]:
    folder = tmp_path_factory.mktemp("schools")
    (folder / "no-repository").mkdir()
    arguments = [
        "preview",
        *("--release-id", RELEASE),
        *("--built-at", "2026-09-24T00:00:00Z"),
        *("--out", str(folder / "out")),
        *(word for name in LISTS for word in ("--list", name)),
        *("--receipts", str(RECEIPTS)),
        *("--root", str(folder / "no-repository")),
        *("--commit", "0" * 40),
        *("--work", str(folder / "copies")),
    ]
    printed = folder / "printed"
    with printed.open("w", encoding="utf-8") as said, pytest.MonkeyPatch.context() as patch:
        patch.setattr("sys.stdout", said)
        assert assemble.main(arguments, {FOLDER_VARIABLE: STORE}) == 0
    return folder / "out", printed.read_text(encoding="utf-8").splitlines()


def beside(built: tuple[Path, list[str]], name: str) -> Any:
    return json.loads((built[0] / f"{RELEASE}-build" / name).read_bytes())


def test_the_register_is_sealed_and_the_schools_are_worked_out_and_carried(
    built: tuple[Path, list[str]],
):
    said = built[1]
    assert [line for line in said if f"feature={FEATURE}" in line] == [
        f"step=derive status=ok feature={FEATURE} source=dfe-gias areas=1002 values=1002 files=4"
    ]
    assert " findings=0 " in said[-2]
    record = beside(built, "build.json")
    assert REGISTER in record["files_sealed"]
    assert FEATURE not in {one["feature_id"] for one in record["measures_left_out"]}
    (carried,) = [one for one in record["measures_carried"] if one["feature_id"] == FEATURE]
    assert carried["cannot_see"] == list(school_primary_nearby.CANNOT_SEE)


def test_the_release_carries_the_schools_and_family_amenities_is_placed_on_its_whole_recipe(
    built: tuple[Path, list[str]],
):
    release = read_release(built[0] / RELEASE)
    assert FEATURE in {metric.feature_id for metric in release.metrics}
    family = [tag for tag in release.tags if tag.tag_id is TagId.FAMILY_AMENITIES]
    assert len(family) == 1_002
    # The schools, the nearest play space and the nearest park are the whole of its recipe.
    assert {tag.coverage for tag in family} == {1.0}
    assert all(tag.score is not None and tag.band is not None for tag in family)


def test_every_row_of_the_schools_holds_a_figure_and_rests_on_four_files(
    built: tuple[Path, list[str]],
):
    evidence = beside(built, "evidence.json")
    rows = [row for row in evidence["rows"] if row["fact_id"].endswith(f"/feature/{FEATURE}")]
    assert len(rows) == 1_002
    assert {(row["state"], len(row["inputs"])) for row in rows} <= {("present", 4), ("partial", 4)}
    assert all(row["value"] is not None for row in rows)
