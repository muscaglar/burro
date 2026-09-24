"""The draft of the areas, on the files as their publishers gave them.

Every other test of the draft runs on made-up files. These read the real ones,
and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER.
Each file is read through its receipt, from `data/receipts/`, or from the folder
BURRO_RECEIPTS_FOLDER names where a working copy holds none.

The seeds are not the curated ones, which are in no file of the repository.
They are every populated place of OS Open Names in London that is not of kind
`City`, each with the 3 points the design gives a populated place. So what is
held here is the method on the real ground, and not the draft a person reviews.

A number here is a count or a sum over all of London, and never a row or a
name. Each was counted on 2026-09-23. Nothing is written to the store.
"""

import csv
import io
import os
import random
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pytest
from burro_pipeline.areas import assign_files, assign_outline, assign_write
from burro_pipeline.areas.assign import NORTH, SOUTH, Draft, Rules, draft
from burro_pipeline.areas.assign_files import Ground, SeedPoint
from burro_pipeline.areas.assign_outline import Outlines
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import REPOSITORY, registry

RECEIPTS_VARIABLE = "BURRO_RECEIPTS_FOLDER"
STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = Path(os.environ.get(RECEIPTS_VARIABLE, "") or REPOSITORY / "data" / "receipts")
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and RECEIPTS.is_dir()),
    reason=f"the store of fetched files or its receipts are not here: {FOLDER_VARIABLE} names "
    f"the store, and data/receipts or {RECEIPTS_VARIABLE} the receipts",
)
# Beyond this box no point is in London. It spares the test placing every name of the country.
BOX = (500_000.0, 150_000.0, 565_000.0, 205_000.0)


@dataclass(frozen=True)
class Real:
    ground: Ground
    draft: Draft
    outlines: Outlines


def places(inputs: Inputs) -> list[SeedPoint]:
    """Every populated place of the file of names that is not a city, as a seed of 3 points."""
    opened = inputs.open("os-open-names", Use.GAZETTEER)
    found: list[SeedPoint] = []
    with zipfile.ZipFile(opened.path) as archive:
        with archive.open("Doc/OS_Open_Names_Header.csv") as raw:
            header = next(csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig")))
        at = {name: header.index(name) for name in header}
        for table in sorted(name for name in archive.namelist() if name.startswith("Data/")):
            with archive.open(table) as raw:
                for row in csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")):
                    if row[at["TYPE"]] != "populatedPlace" or row[at["LOCAL_TYPE"]] == "City":
                        continue
                    point = float(row[at["GEOMETRY_X"]]), float(row[at["GEOMETRY_Y"]])
                    if BOX[0] <= point[0] <= BOX[2] and BOX[1] <= point[1] <= BOX[3]:
                        found.append(
                            SeedPoint(row[at["ID"]], point, 3.0, row[at["NAME1"]], row[at["ID"]])
                        )
    return found


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Real:
    work = tmp_path_factory.mktemp("real")
    inputs = Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), work)
    ground = assign_files.read_ground(inputs, places(inputs))
    found = draft(ground.cells, ground.seeds, ground.roads, ground.beside)
    return Real(ground, found, assign_outline.outlines_of(found.drawn, ground.outlines))


# The ground


def test_the_ground_is_what_was_counted_in_the_files(real: Real):
    assert dict(real.ground.counted) == {
        "output_areas": 26_369,
        "boroughs": 33,
        "seeds_read": 1_301,
        "seeds_in_london": 687,
        "water_hectares": 2_129.7,
        "on_the_north_bank": 13_832,
        "on_the_south_bank": 9_886,
        "with_no_bank": 2_651,
        "boroughs_on_both_banks": 1,
        "wards": 692,
        "output_areas_with_a_ward": 26_369,
        "output_areas_whose_roads_name_a_settlement": 22_558,
        "output_areas_whose_roads_name_a_seed": 9_529,
        "output_areas_whose_ward_names_a_seed": 18_449,
        "output_areas_at_no_node": 0,
        "links_read": 280_877,
        "links_over_the_water": 48,
        "links_taken_up": 23,
        "links_with_an_end_beyond_the_box": 568,
        "links": 280_286,
        "nodes": 227_219,
        "pieces_of_the_roads": 43,
        "nodes_off_the_largest_piece": 220,
    }
    assert len(real.ground.outside) == 614


def test_every_output_area_shares_a_side_with_another_and_london_is_one_piece(real: Real):
    assert all(real.ground.beside[cell.oa] for cell in real.ground.cells)
    sides = sum(len(others) for others in real.ground.beside.values()) // 2
    assert sides == 77_085


def test_no_bank_is_said_of_an_output_area_west_of_where_the_water_ends(real: Real):
    by_bank: dict[str, set[str]] = {}
    for cell in real.ground.cells:
        by_bank.setdefault(cell.bank, set()).add(cell.borough)
    assert {bank: len(boroughs) for bank, boroughs in by_bank.items()} == {
        NORTH: 21,
        SOUTH: 12,
        "": 6,
    }


# The draft


def test_every_london_output_area_is_in_exactly_one_area(real: Real):
    assert sorted(real.draft.given) == [cell.oa for cell in real.ground.cells]
    assert len(real.draft.given) == 26_369
    held = [oa for each in real.draft.drawn.values() for oa in each.cells]
    assert len(held) == len(set(held)) == 26_369
    assert all(given.area in real.draft.drawn for given in real.draft.given.values())


def test_every_area_is_one_piece_and_none_spans_the_tidal_water(real: Real):
    assert all(len(each.pieces) == 1 for each in real.draft.drawn.values())
    assert not [
        each for each in real.draft.drawn.values() if NORTH in each.banks and SOUTH in each.banks
    ]


def test_the_draft_is_what_was_counted(real: Real):
    assert real.draft.counts() == {
        "output_areas": 26_369,
        "areas": 552,
        "seeds_too_close": 41,
        "seeds_under_smallest": 81,
        "seeds_with_no_output_area": 13,
        "given_to_the_nearest": 25_683,
        "no_seed_reached": 0,
        "cut_off_and_joined": 235,
        "of_an_area_too_small": 451,
        "areas_in_pieces": 0,
        "areas_on_both_banks": 0,
        "areas_with_seed_outside": 8,
        "areas_in_two_boroughs": 168,
    }


def test_an_area_may_lie_in_two_boroughs_and_its_main_borough_holds_most_of_it(real: Real):
    for each in real.draft.drawn.values():
        assert each.boroughs[each.primary_borough] == max(each.boroughs.values())
        assert sum(each.boroughs.values()) == len(each.cells)


def test_the_same_ground_in_another_order_gives_the_same_areas(real: Real):
    drawn = random.Random(23)  # noqa: S311
    cells, seeds = list(real.ground.cells), list(real.ground.seeds)
    drawn.shuffle(cells)
    drawn.shuffle(seeds)
    names = list(real.ground.beside)
    drawn.shuffle(names)
    beside = {oa: dict(sorted(real.ground.beside[oa].items(), reverse=True)) for oa in names}
    again = draft(cells, seeds, real.ground.roads, beside, Rules())
    assert again == real.draft


# The outlines


def test_the_outlines_fit_together_and_are_small_enough_for_a_page(real: Real):
    assert real.outlines.fit_together
    assert set(real.outlines.of) == set(real.draft.drawn)
    written = assign_write.canonical_json(assign_outline.feature_collection(real.outlines))
    assert 1_200_000 < len(written) < 1_500_000
    for outline in real.outlines.of.values():
        longitude, latitude = outline.inside
        assert -0.52 < longitude < 0.34 and 51.28 < latitude < 51.70
