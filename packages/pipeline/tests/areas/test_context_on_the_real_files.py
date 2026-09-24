"""The layers behind a border and the ground of the flags, from the files their publishers gave.

Every other test of these runs on made-up files. These read the real ones, and
are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER.
Each file is read through its receipt: from `data/receipts/` where the working
copy holds that folder, and from the copies the store keeps beside each file
where it does not.

They hold counts and sizes, so that a publisher's file that changes is
noticed. A number here is a count or a sum over all of London. None is said of
a named place, and no name is held here. Each was counted on 2026-09-23.

The town centres had no receipt until 2026-09-24, and were read as a draft
reads a file that has none. They are read through their receipt now, so no
layer says that it rests on a file with no receipt.

Nothing is written to the store. A file is copied out of it to be read.
"""

import json
import os
import shutil
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline.areas import context_files, flags_build
from burro_pipeline.areas.context_files import Made
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
IN_THE_REPOSITORY = REPOSITORY / "data" / "receipts"
RECEIPTS = IN_THE_REPOSITORY if IN_THE_REPOSITORY.is_dir() else Path(STORE) / "receipts"
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and RECEIPTS.is_dir()),
    reason=f"the store of fetched files is not here: {FOLDER_VARIABLE} names no folder",
)


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Inputs]:
    """The files of the build. The copies come to several gigabytes, and are not left behind."""
    work = tmp_path_factory.mktemp("real")
    yield Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), work)
    shutil.rmtree(work, ignore_errors=True)


@pytest.fixture(scope="module")
def built(real: Inputs, tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Made]:
    out = tmp_path_factory.mktemp("layers")
    return out, context_files.build(real, out, draft=True)


def features(out: Path, layer: str) -> dict[str, dict[str, Any]]:
    """Every feature of a layer, once, whichever boroughs it is drawn for."""
    found: dict[str, dict[str, Any]] = {}
    for path in sorted(out.glob(f"*/*/{layer}.geojson")):
        for feature in json.loads(path.read_text(encoding="utf-8"))["features"]:
            found.setdefault(feature["id"], feature)
    return found


def test_the_gate_gives_six_sources_for_the_layers_and_refuses_three(built: tuple[Path, Made]):
    given = {source for source, answer in built[1].answers.items() if answer.given}

    assert len(given) == 6
    assert set(built[1].answers) - given == {"os-open-greenspace", "os-open-rivers", "dft-naptan"}


def test_every_layer_is_made_and_london_has_33_boroughs(built: tuple[Path, Made]):
    out, made = built

    assert set(made.not_made) == set(context_files.OF_THE_DRAFT)
    assert len(made.boroughs) == 33
    assert sum(borough.output_areas for borough in made.boroughs) == 26_369
    assert len(features(out, "boroughs")) == 33
    assert len(list(out.glob("layers/*/wards.geojson"))) == 33


def test_the_layers_hold_as_many_things_as_were_counted(built: tuple[Path, Made]):
    out = built[0]

    assert {layer: len(features(out, layer)) for layer in ("wards", "centres", "water")} == {
        "wards": 704,
        "centres": 234,
        "water": 1,
    }
    kinds = Counter(each["properties"]["kind"] for each in features(out, "names").values())
    assert kinds["Railway Station"] == 586
    assert "Postcode" not in kinds and "Named Road" not in kinds
    roads = Counter(each["properties"]["class"] for each in features(out, "roads").values())
    assert roads == {"Minor Road": 2_328, "A Road": 1_503, "B Road": 732, "Motorway": 6}


def test_every_layer_is_small_enough_for_a_page(built: tuple[Path, Made]):
    written = built[1].written

    assert max(each.bytes for each in written) < 250_000
    by_group = Counter[str]()
    for each in written:
        by_group[each.group] += each.bytes
    assert max(by_group.values()) < 400_000
    assert 6_000_000 < sum(each.bytes for each in written) < 7_000_000


def test_no_layer_rests_on_a_file_with_no_receipt(built: tuple[Path, Made]):
    """The layer of town centres did, until the file had its receipt."""
    assert built[1].unreceipted == {}


def test_the_ground_of_the_flags_is_as_many_cells_sides_and_roads_as_were_counted(real: Inputs):
    read = flags_build.read_ground(real, draft=True)

    assert len(read.ground.hectares) == 26_369
    assert len(read.ground.shared) == 77_085
    assert len(read.ground.ward_of) == 26_369
    assert len(set(read.ground.ward_of.values())) == 692
    assert len(read.main_roads) == 40_564
    assert len(read.centres) == 205
    # The generalised outlines hold 8 hectares less than the full ones.
    assert round(sum(read.ground.hectares.values())) == 157_334
    # The gate does not give the count of homes for the gazetteer, so none is read.
    assert read.homes is None
    assert read.unreceipted == []
