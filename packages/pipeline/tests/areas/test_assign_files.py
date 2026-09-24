"""The ground a draft is made on, read from a made-up town in files shaped like the real.

Nothing here is real, and nothing reaches a network or a store of fetched
files. The town is drawn in `assign_files_support.py`.
"""

import csv
import io
from dataclasses import replace
from pathlib import Path

import pytest
from burro_pipeline.areas import assign_files
from burro_pipeline.areas.assign import NORTH, NOT_DRAWN, ROADS, SOUTH, WARD
from burro_pipeline.areas.assign_files import Ground, SeedPoint, fold, holds
from burro_pipeline.areas.assign_settlements import Settlement
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import held, registry
from .assign_files_support import (
    FILES,
    OUTSIDE,
    QUILLHAVEN,
    READING,
    SEEDS,
    TALLOWGATE,
    TOWN,
    contents,
    inputs_of,
    node,
    oa,
    on_the_grid,
    roads,
    zipped,
)

ALDERWICK, CINDERMOOR, ESKERFOLD, DULCIMER = (each.seed_id for each in SEEDS)


@pytest.fixture(scope="module")
def ground(tmp_path_factory: pytest.TempPathFactory) -> Ground:
    inputs = inputs_of(tmp_path_factory.mktemp("ground"), contents())
    return assign_files.read_ground(inputs, SEEDS, READING)


def read(folder: Path, seeds: tuple[SeedPoint, ...] = SEEDS, **files: bytes) -> Ground:
    return assign_files.read_ground(inputs_of(folder, contents() | files), seeds, READING)


def rows_of(written: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(written.decode())))


# The ground


def test_the_ground_is_every_output_area_of_london_and_no_other(ground: Ground):
    assert [cell.oa for cell in ground.cells] == sorted(made.oa for made in TOWN)
    assert OUTSIDE.oa not in ground.outlines
    assert ground.boroughs[QUILLHAVEN] == "Quillhaven"
    assert {cell.borough for cell in ground.cells} == {QUILLHAVEN, TALLOWGATE}


def test_the_water_is_what_one_publisher_draws_and_the_other_leaves_out(ground: Ground):
    assert ground.counted["water_hectares"] == 1.6


def test_the_banks_are_the_two_pieces_the_water_parts_and_nothing_is_said_west_of_it(
    ground: Ground,
):
    bank = {cell.oa: cell.bank for cell in ground.cells}
    assert {bank[oa(column, row)] for column in (2, 3, 4, 5) for row in (2, 3)} == {NORTH}
    assert {bank[oa(column, row)] for column in (2, 3, 4, 5) for row in (0, 1)} == {SOUTH}
    assert {bank[oa(column, row)] for column in (0, 1) for row in (-1, 0, 1, 2, 3)} == {NOT_DRAWN}
    assert ground.counted["with_no_bank"] == 10
    assert ground.counted["boroughs_on_both_banks"] == 0


def test_a_town_with_no_water_has_no_banks(tmp_path: Path):
    """Where the boroughs are drawn no further than the output areas, nothing is water."""
    found = assign_files.read_ground(
        inputs_of(tmp_path, contents()), SEEDS, replace(READING, least_water=2.0)
    )
    assert found.counted["water_hectares"] == 0.0
    assert {cell.bank for cell in found.cells} == {NOT_DRAWN}
    assert found.counted["links_taken_up"] == 0


def test_a_bridge_is_taken_up_and_a_road_that_runs_over_the_water_and_back_stays(ground: Ground):
    assert ground.counted["links_over_the_water"] == 2
    assert ground.counted["links_taken_up"] == 1
    beside = ground.roads.beside[ground.roads.number_of[node(4, 1)]]
    assert ground.roads.number_of[node(4, 2)] not in [other for other, _ in beside]
    far = dict(ground.roads.beside[ground.roads.number_of[node(5, 1)]])
    assert far[ground.roads.number_of[node(3, 1)]] == 320_000


def test_output_areas_share_the_sides_the_files_draw_and_none_across_the_water(ground: Ground):
    assert ground.beside[oa(2, 1)] == {oa(1, 1): 100.0, oa(2, 0): 100.0, oa(3, 1): 100.0}
    assert ground.beside[oa(1, -1)] == {oa(0, -1): 40.0, oa(1, 1): 100.0, oa(1, 2): 100.0}
    assert all(cell.hectares in (1.0, 0.4) for cell in ground.cells)
    assert ground.around[oa(0, -1)] == 280.0


def test_a_seed_and_an_output_area_are_put_on_the_node_nearest_them(ground: Ground):
    seeds = {each.seed_id: each for each in ground.seeds}
    assert (seeds[ESKERFOLD].oa, seeds[ESKERFOLD].node) == (oa(4, 2), node(4, 2))
    assert seeds[ESKERFOLD].to_node == 0
    cells = {cell.oa: cell for cell in ground.cells}
    assert all(cell.node == f"syn-node-{cell.oa[-3:]}" for cell in cells.values())


def test_a_seed_on_the_line_between_two_output_areas_lies_in_the_one_that_sorts_first(
    tmp_path: Path,
):
    on_a_line = SeedPoint("syn-n0009", on_the_grid((300.0, 50.0)), 6.0, "Foxholt")
    found = read(tmp_path, (*SEEDS, on_a_line))
    assert {each.seed_id: each.oa for each in found.seeds}["syn-n0009"] == oa(2, 0)


def test_a_seed_outside_london_is_named_and_is_not_grown_from(tmp_path: Path):
    away = SeedPoint("syn-n0009", on_the_grid(OUTSIDE.centre), 6.0, "Foxholt")
    in_the_water = SeedPoint("syn-n0010", on_the_grid((400.0, 220.0)), 6.0, "Eskerfold")
    found = read(tmp_path, (*SEEDS, away, in_the_water))
    assert found.outside == ("syn-n0009", "syn-n0010")
    assert [each.seed_id for each in found.seeds] == sorted(each.seed_id for each in SEEDS)


def test_nothing_is_put_on_a_yard_that_joins_no_road(tmp_path: Path):
    beside_the_yard = SeedPoint("syn-n0009", on_the_grid((250.0, 42.0)), 6.0, "Foxholt")
    found = read(tmp_path, (*SEEDS, beside_the_yard))
    put = {each.seed_id: each for each in found.seeds}["syn-n0009"]
    assert (put.node, put.to_node) == (node(2, 0), 8_000)
    assert found.counted["pieces_of_the_roads"] == 2
    assert found.counted["nodes_off_the_largest_piece"] == 2


def test_a_point_on_a_bank_is_never_put_on_a_node_of_the_other_bank(tmp_path: Path):
    """The seed is 46 m from the quay across the water, and 49 m from a node of its own bank."""
    low = SeedPoint("syn-n0009", on_the_grid((450.0, 199.0)), 6.0, "Foxholt")
    found = read(tmp_path, (*SEEDS, low))
    put = {each.seed_id: each for each in found.seeds}["syn-n0009"]
    assert (put.oa, put.node, put.to_node) == (oa(4, 1), node(4, 1), 49_000)


def test_the_ward_of_an_output_area_is_the_one_that_holds_most_of_it(ground: Ground):
    assert ground.wards[oa(0, 0)].name == "Alderwick"
    assert (ground.wards[oa(0, -1)].code, ground.wards[oa(0, -1)].share) == ("E05999001", 1.0)
    # The ward in the north east is drawn down to the middle of the water.
    assert ground.wards[oa(5, 2)].name == "Eskerfold & Foxholt"
    assert ground.counted["wards"] == 4


def test_a_ward_favours_the_seeds_whose_name_it_holds_as_whole_words(ground: Ground):
    said = {cell.oa: {each.kind: each for each in cell.said} for cell in ground.cells}
    assert said[oa(5, 3)][WARD].as_written == "Eskerfold & Foxholt"
    assert said[oa(5, 3)][WARD].favours == {ESKERFOLD}
    assert said[oa(0, 3)][WARD].favours == {DULCIMER}
    assert said[oa(5, 0)][WARD].favours == {CINDERMOOR}


# What the roads say


def test_the_roads_of_an_output_area_say_the_settlement_most_of_them_name(ground: Ground):
    assert ground.settlements[oa(5, 0)] == Settlement("9999000000000002", "Cindermoor", 2, 2)
    # Three of its five roads name one place, and two another.
    assert ground.settlements[oa(3, 0)] == Settlement("9999000000000001", "Alderwick", 3, 5)
    assert ground.counted["output_areas_whose_roads_name_a_settlement"] == 9


def test_an_output_area_with_no_road_that_names_a_settlement_says_nothing(ground: Ground):
    assert oa(5, 3) not in ground.settlements and oa(1, 1) not in ground.settlements
    said = {cell.oa: {each.kind for each in cell.said} for cell in ground.cells}
    assert said[oa(5, 3)] == {WARD}


def test_a_postcode_and_a_station_are_not_roads_and_a_road_outside_london_is_no_part_of_it(
    ground: Ground,
):
    assert oa(0, 0) not in ground.settlements
    assert OUTSIDE.oa not in ground.settlements


def test_a_road_favours_the_seed_that_is_its_settlement_by_its_record_and_never_by_its_name(
    ground: Ground,
):
    said = {cell.oa: {each.kind: each for each in cell.said} for cell in ground.cells}
    assert said[oa(4, 1)][ROADS].favours == {CINDERMOOR}
    assert said[oa(3, 0)][ROADS].favours == {ALDERWICK}
    # The roads of one square name a place that has the fourth seed's name and is another.
    assert said[oa(0, 3)][ROADS].as_written == "Dulcimer Green"
    assert said[oa(0, 3)][ROADS].favours == frozenset()
    assert ground.counted["output_areas_whose_roads_name_a_seed"] == 8


def test_a_file_of_names_with_no_list_of_its_columns_stops_the_reading(tmp_path: Path):
    with pytest.raises(LockError, match="input_is_as_described"):
        read(tmp_path / "a", names=zipped("Data/XA00.csv", b"a,b\r\n"))
    with pytest.raises(LockError, match="input_is_as_described"):
        read(tmp_path / "b", names=zipped("Doc/OS_Open_Names_Header.csv", b"ID,NAME1\r\n"))


def test_a_name_is_compared_by_whole_words_and_never_by_part_of_one():
    assert fold("Eskerfold & Foxholt") == "eskerfold and foxholt"
    assert holds("Dulcimer Green", "dulcimer green")
    assert holds("Upper Dulcimer Green", "Dulcimer Green")
    assert not holds("Dulcimers Green", "Dulcimer")
    assert not holds("Dulcimer", "Dulcimer Green")
    assert not holds("Dulcimer Green", "")


# The gate


def test_every_file_is_asked_for_as_a_gazetteer_and_none_is_share_alike(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents())
    assign_files.read_ground(inputs, SEEDS, READING)
    read = {opened.receipt.source_id for opened in inputs.opened}
    assert read == {source_id for source_id, _, _, _ in FILES.values()}
    for source_id in read:
        source = registry().get(source_id)
        assert Use.GAZETTEER in source.uses and not source.share_alike


@pytest.mark.parametrize("refused", sorted({source_id for source_id, _, _, _ in FILES.values()}))
def test_a_file_the_gate_does_not_give_for_a_gazetteer_is_not_read(tmp_path: Path, refused: str):
    sources = tuple(
        source.model_copy(update={"uses": (Use.SCORING,)}) if source.id == refused else source
        for source in registry()
    )
    inputs = inputs_of(tmp_path, contents(), Registry(sources=sources))
    with pytest.raises(LockError) as stopped:
        assign_files.read_ground(inputs, SEEDS, READING)
    assert (stopped.value.rule, stopped.value.subject) == ("gate_refuses", refused)
    assert refused not in {opened.receipt.source_id for opened in inputs.opened}


def test_no_module_of_the_draft_names_a_source_the_gate_refuses_for_a_gazetteer():
    """Homes, rivers, green space and the street map are not read, so they are not named."""
    folder = Path(assign_files.__file__).parent
    named = {
        source.id
        for source in registry()
        for path in (*sorted(folder.glob("assign*.py")), folder / "grow.py")
        if f'"{source.id}"' in path.read_text(encoding="utf-8")
    }
    assert named == {source_id for source_id, _, _, _ in FILES.values()} - {
        "ons-oa21-lsoa21-msoa21-lad22-lookup"
    }
    assert all(Use.GAZETTEER in registry().get(source_id).uses for source_id in named)


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents())
    before = held(tmp_path / "store")
    assign_files.read_ground(inputs, SEEDS, READING)
    assert held(tmp_path / "store") == before
    assert sorted(path.name for path in (tmp_path / "work").rglob("*.gpkg")) == [
        "Output_Areas_2021_EW_BFC_V8_made_up.gpkg",
        "Output_Areas_2021_EW_BGC_V2_made_up.gpkg",
        "bdline_gb.gpkg",
        "oproad_gb.gpkg",
    ]


# What stops a reading


def test_a_file_that_is_not_laid_out_as_it_is_read_stops_the_reading(tmp_path: Path):
    with pytest.raises(LockError, match="input_is_as_described"):
        read(tmp_path / "a", roads=zipped("Data/another.gpkg", roads()))
    with pytest.raises(LockError, match="input_is_as_described"):
        read(tmp_path / "b", boundary_line=zipped("Data/bdline_gb.gpkg", roads()))
    with pytest.raises(LockError, match="input_is_as_described"):
        read(tmp_path / "c", centres=contents()["centres"].replace(b"E00999005", b"E00999905"))
    with pytest.raises(ValueError, match="no seed lies"):
        read(tmp_path / "d", (SeedPoint("syn-n0009", on_the_grid(OUTSIDE.centre), 6.0),))
