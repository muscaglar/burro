"""The town centres, from the publisher's file to the nearest centre of each output area.

Every file here is made up: `centres_support.py` draws the centres, and the
tests of cells draw the town they stand beside.
"""

import math
from pathlib import Path

import pytest
from burro_pipeline.cells import centres, spine
from burro_pipeline.derive import centre_shapes, town_centres
from burro_pipeline.derive.town_centres import Found, Nearest
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import TOWN, held, registry
from .centres_support import (
    AS_AT,
    CANARY,
    COLUMNS,
    GREEN,
    GREEN_FILLS,
    OAS,
    ROAD,
    ROAD_FILLS,
    MadeUpCentre,
    box,
    centres_gpkg,
    homes_in_the_middle,
    inputs_of,
    opened_of,
    outline,
)


def built(folder: Path, packed: bytes | None = None, homes: bytes | None = None) -> Found:
    inputs = inputs_of(folder, packed, homes=homes)
    return town_centres.build(inputs, spine.build(inputs))


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Found:
    return built(tmp_path_factory.mktemp("town"))


# What is read of the file


def test_every_centre_is_read_with_its_outline_its_size_and_how_much_of_its_circle_it_fills(
    town: Found,
):
    assert list(town.centres) == [GREEN.record_id, ROAD.record_id]
    green, road = town.centres[GREEN.record_id], town.centres[ROAD.record_id]
    assert (green.hectares, road.hectares) == (4.0, 20.0)
    assert green.fills == pytest.approx(GREEN_FILLS / 100)
    assert road.fills == pytest.approx(ROAD_FILLS / 100)


def test_a_name_and_a_class_are_never_read(town: Found, tmp_path: Path):
    """A file with no column for either reads as the whole file does."""
    kept = [name for name in COLUMNS if name not in ("sitename", "classification")]
    without = built(tmp_path, centres_gpkg(columns=kept))
    assert without.nearest == town.nearest
    assert CANARY not in repr(town)


def test_the_file_is_the_one_the_publisher_names(town: Found):
    assert town_centres.is_the_file("Town_Centres_Boundaries.gpkg")
    assert not town_centres.is_the_file("GLA_High_Street_boundaries_2.gpkg")
    assert town.geography is Geography.POLYGON
    assert town.as_at == AS_AT


NOT_AS_DESCRIBED = {
    "the layer is under another name": (
        lambda: centres_gpkg(layer="high_streets"),
        "a layer is missing",
    ),
    "the layer is not on the National Grid": (
        lambda: centres_gpkg(grid=4326),
        "a layer is missing",
    ),
    "the column of sizes is not there": (
        lambda: centres_gpkg(columns=[name for name in COLUMNS if name != "hectares"]),
        "a column is missing",
    ),
    "an id is written twice": (lambda: centres_gpkg([GREEN, GREEN]), "an id is missing or twice"),
    "an id is not written": (
        lambda: centres_gpkg([MadeUpCentre("", GREEN.pieces)]),
        "an id is missing or twice",
    ),
    "the size is not the outline's": (
        lambda: centres_gpkg([MadeUpCentre("TCB00000009", GREEN.pieces, said=5.0)]),
        "an outline is not of the size given",
    ),
    "the size is nothing": (
        lambda: centres_gpkg([MadeUpCentre("TCB00000009", GREEN.pieces, said=0.0)]),
        "an outline is not of the size given",
    ),
    "the size is written as text": (
        lambda: centres_gpkg([MadeUpCentre("TCB00000009", GREEN.pieces, said="four")]),
        "a centre has no size",
    ),
    "the layer holds no row": (lambda: centres_gpkg([]), "it holds no centre"),
}


@pytest.mark.parametrize("which", sorted(NOT_AS_DESCRIBED))
def test_a_file_that_is_not_as_described_stops_the_step(tmp_path: Path, which: str):
    made, said = NOT_AS_DESCRIBED[which]
    with pytest.raises(LockError) as refused:
        town_centres.read(opened_of(tmp_path, made()))
    assert refused.value.rule == "input_is_as_described"
    assert said in str(refused.value) and CANARY not in str(refused.value)


def test_an_outline_may_be_as_far_from_the_size_given_as_2_in_100_and_no_further(tmp_path: Path):
    near = MadeUpCentre("TCB00000009", GREEN.pieces, said=4.08)
    assert town_centres.read(opened_of(tmp_path / "near", centres_gpkg([near])))
    far = MadeUpCentre("TCB00000009", GREEN.pieces, said=4.09)
    with pytest.raises(LockError):
        town_centres.read(opened_of(tmp_path / "far", centres_gpkg([far])))
    assert town_centres.AS_DRAWN == 0.02


def test_a_centre_in_two_pieces_is_one_centre_and_fills_little_of_its_circle(tmp_path: Path):
    pieces = (box(0, 0, 100, 100), box(900, 0, 100, 100))
    found = town_centres.read(opened_of(tmp_path, centres_gpkg([MadeUpCentre("TCB1", pieces)])))
    (one,) = found.values()
    assert one.hectares == 2.0
    # The circle round both pieces is as wide as from one far corner to the other.
    assert one.fills == pytest.approx(20_000 / (math.pi * (1000**2 + 100**2) / 4))


# The gate and the receipt


def test_the_gate_is_asked_before_the_file_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, given=Registry(sources=()))
    with pytest.raises(LockError) as refused:
        town_centres.build(inputs, spine.build(inputs_of(tmp_path / "spine")))
    assert refused.value.rule == "gate_refuses"


def test_a_file_with_no_receipt_is_not_read(tmp_path: Path):
    """The file is in the store, and nothing says of when it is. So no figure rests on it."""
    inputs = inputs_of(tmp_path, with_a_receipt=False)
    with pytest.raises(LockError) as refused:
        town_centres.build(inputs, spine.build(inputs))
    assert refused.value.rule == "input_has_one_receipt"


def test_the_town_centres_are_registered_for_scoring_and_so_is_every_file_behind_them(
    town: Found,
):
    for receipt in town.files:
        registry().require(receipt.source_id, Use.SCORING)
    assert sorted(receipt.source_id for receipt in town.files) == sorted(
        [town_centres.SOURCE, centres.CENTRES, spine.LOOKUP, spine.HOMES]
    )


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    town_centres.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before


# Which centre is nearest


def test_each_output_area_is_as_far_from_the_nearest_outline_as_was_worked_out_by_hand(
    town: Found,
):
    green, road = GREEN.record_id, ROAD.record_id
    by_column = {0: (green, 150), 1: (green, 250), 2: (green, 350), 3: (green, 450)}
    # The homes of column 4 are as far from one as from the other. The first by id is taken.
    by_column |= {4: (green, 550), 5: (road, 450)}
    columns = [unit.squares[0][0] for unit in TOWN if unit.oa in OAS]
    assert [town.nearest[oa] for oa in OAS] == [
        Nearest(by_column[column][0], float(by_column[column][1])) for column in columns
    ]
    assert (town.placed, town.may_be_nearer_beyond) == (12, 0)


def test_a_home_inside_an_outline_is_no_distance_from_it(tmp_path: Path):
    over = MadeUpCentre("TCB00000003", (box(0, 0, 200, 200),))
    found = built(tmp_path, centres_gpkg([over]))
    assert [found.nearest[oa].metres for oa in OAS[:4]] == [0.0] * 4
    assert found.nearest[OAS[4]].metres == 50.0


def test_a_home_inside_two_outlines_is_given_to_the_first_by_id(tmp_path: Path):
    under = MadeUpCentre("TCB00000004", (box(0, 0, 600, 200),))
    over = MadeUpCentre("TCB00000003", (box(0, 0, 200, 200),))
    found = built(tmp_path, centres_gpkg([under, over]))
    assert found.nearest[OAS[0]] == Nearest("TCB00000003", 0.0)
    assert found.nearest[OAS[11]] == Nearest("TCB00000004", 0.0)


def test_an_output_area_with_no_centre_of_population_has_no_nearest_centre(tmp_path: Path):
    found = built(tmp_path, homes=homes_in_the_middle(left_out=[OAS[0]]))
    assert OAS[0] not in found.nearest and len(found.nearest) == 11
    assert (found.placed, found.may_be_nearer_beyond) == (11, 0)


def test_the_order_of_the_rows_changes_nothing(town: Found, tmp_path: Path):
    turned = built(tmp_path, centres_gpkg([ROAD, GREEN]))
    assert turned.nearest == town.nearest and list(turned.centres) == list(town.centres)


# The edge of London


def test_a_home_nearer_to_homes_beyond_london_than_to_any_centre_has_no_nearest_centre(
    tmp_path: Path,
):
    """The homes beyond London stand at 750 metres east. A centre may stand among them.

    From the homes of column 2 they are 500 metres off, and Green is 350: it is
    known to be the nearest. From those of column 3 they are 400 metres off,
    and Green is 450.
    """
    found = built(tmp_path, centres_gpkg([GREEN]), homes_in_the_middle(TOWN))
    known = [unit.oa for unit in TOWN if unit.oa in OAS and unit.squares[0][0] <= 2]
    assert sorted(found.nearest) == sorted(known)
    assert (found.placed, found.may_be_nearer_beyond) == (12, 6)


def test_a_home_as_near_to_a_centre_as_to_homes_beyond_london_keeps_its_centre(tmp_path: Path):
    """A centre among those homes could be no nearer than the one that was found.

    The home of c2 stands 200 metres from the homes beyond London.
    """
    as_near = MadeUpCentre("TCB00000005", (box(250, 100, 100, 100),))
    found = built(tmp_path / "as-near", centres_gpkg([as_near]), homes_in_the_middle(TOWN))
    assert found.nearest[OAS[9]] == Nearest("TCB00000005", 200.0)
    a_metre_further = MadeUpCentre("TCB00000005", (box(249, 100, 100, 100),))
    found = built(tmp_path / "further", centres_gpkg([a_metre_further]), homes_in_the_middle(TOWN))
    assert OAS[9] not in found.nearest and OAS[8] in found.nearest


def test_the_homes_beyond_london_are_no_part_of_any_figure(tmp_path: Path):
    found = built(tmp_path, homes=homes_in_the_middle(TOWN))
    assert set(found.nearest) <= set(OAS)


def test_a_home_beyond_london_that_is_no_point_stops_the_step(tmp_path: Path):
    with pytest.raises(LockError) as refused:
        built(tmp_path, homes=homes_in_the_middle(TOWN, broken=TOWN[-1].oa))
    assert refused.value.rule == "input_is_as_described"


# Within reach


def test_a_home_has_a_centre_of_its_own_at_800_metres_and_not_a_metre_further(tmp_path: Path):
    at_the_reach = MadeUpCentre("TCB00000006", (box(850, 100, 100, 100),))
    found = built(tmp_path, centres_gpkg([at_the_reach]))
    within = town_centres.within_reach(found)
    # The homes of column 0 stand at 50 metres east: 800 from the outline in row 1.
    assert found.nearest[OAS[0]].metres == 800.0 and OAS[0] in within
    # Those of row 0 stand 50 metres lower, which is a little further.
    assert found.nearest[OAS[2]].metres == pytest.approx(math.hypot(800, 50))
    assert OAS[2] not in within
    assert town_centres.REACH == 800


# The geometry


@pytest.mark.parametrize(
    ("wide", "high", "fills"),
    [(100, 100, 2 / math.pi), (1000, 100, 40 / (101 * math.pi)), (500, 100, 20 / (26 * math.pi))],
)
def test_a_square_fills_more_of_its_circle_than_a_strip(wide: int, high: int, fills: float):
    found = MadeUpCentre("TCB1", (box(0, 0, wide, high),))
    shape = town_centres.names_shapes.geometry_of(_blob(found))
    assert centre_shapes.fills_its_circle(shape) == pytest.approx(fills)


def test_how_much_of_its_circle_an_outline_fills_does_not_change_with_its_size():
    small = town_centres.names_shapes.geometry_of(_blob(MadeUpCentre("a", (box(0, 0, 20, 10),))))
    large = town_centres.names_shapes.geometry_of(
        _blob(MadeUpCentre("b", (box(0, 0, 2000, 1000),)))
    )
    assert centre_shapes.fills_its_circle(small) == pytest.approx(
        centre_shapes.fills_its_circle(large)
    )


def test_the_nearest_of_no_points_is_nothing():
    assert centre_shapes.Points([]).nearest((0.0, 0.0)) is None
    some = centre_shapes.Points([(3.0, 4.0), (30.0, 40.0), (3.0, 4.0)])
    assert len(some) == 2 and some.nearest((0.0, 0.0)) == 5.0


def _blob(centre: MadeUpCentre) -> bytes:
    return outline(centre)
