"""The high streets, from the publisher's file to the nearest high street of each output area.

Every file here is made up: `high_streets_support.py` draws the high streets,
and the tests of cells draw the town they stand on.
"""

import math
from pathlib import Path

import pytest
from burro_pipeline.cells import centres, spine
from burro_pipeline.derive import high_streets, town_centres
from burro_pipeline.derive.town_centres import Found, Nearest
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import TOWN, held, registry
from .centres_support import OAS, box, homes_in_the_middle
from .high_streets_support import (
    AS_AT,
    CANARY,
    COLUMNS,
    FAR_SIDE,
    IN_TWO,
    NO_SIZE,
    ONE,
    STREETS,
    THREE,
    TWO,
    WITHIN,
    MadeUpStreet,
    inputs_of,
    opened_of,
    streets_gpkg,
)


def built(folder: Path, packed: bytes | None = None, homes: bytes | None = None) -> Found:
    inputs = inputs_of(folder, packed, homes=homes)
    return high_streets.build(inputs, spine.build(inputs))


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Found:
    return built(tmp_path_factory.mktemp("town"))


# What is read of the file


def test_the_rows_of_one_id_are_one_high_street(town: Found):
    """The file holds five rows, and three high streets."""
    assert sum(len(street.pieces) for street in STREETS) == 5
    assert list(town.centres) == [ONE, TWO, THREE]
    assert [town.centres[name].hectares for name in (ONE, TWO, THREE)] == [0.64, 0.36, 0.48]


def test_a_high_street_in_two_pieces_fills_little_of_the_circle_round_both(town: Found):
    # The circle round both pieces of In Two is as wide as from one far corner to the other.
    across = math.hypot(160, 30)
    assert town.centres[TWO].fills == pytest.approx(3_600 / (math.pi * across * across / 4))
    assert town.centres[ONE].fills > town.centres[TWO].fills


def test_a_piece_that_encloses_a_square_metre_is_part_of_its_high_street(tmp_path: Path):
    sliver = MadeUpStreet(101, (*WITHIN.pieces, box(180, 120, 1, 1)))
    found = high_streets.read(opened_of(tmp_path, streets_gpkg([sliver])))
    assert list(found) == [ONE] and found[ONE].hectares == pytest.approx(0.6401)


def test_a_name_and_the_size_the_file_gives_are_never_read(town: Found, tmp_path: Path):
    """A file with no column for either reads as the whole file does."""
    kept = [name for name in COLUMNS if name not in ("highstreet_name", "area_ha")]
    without = built(tmp_path, streets_gpkg(columns=kept))
    assert without.nearest == town.nearest
    assert {name: one.hectares for name, one in without.centres.items()} == {
        name: one.hectares for name, one in town.centres.items()
    }
    assert CANARY not in repr(town) and str(NO_SIZE) not in repr(town)


def test_the_file_is_the_one_the_publisher_names(town: Found):
    assert high_streets.is_the_file("GLA_High_Street_boundaries_2.gpkg")
    assert not high_streets.is_the_file("Town_Centres_Boundaries.gpkg")
    assert not town_centres.is_the_file(high_streets.FILE)
    assert town.geography is Geography.POLYGON
    assert town.as_at == AS_AT


NOT_AS_DESCRIBED = {
    "the layer is under another name": (
        lambda: streets_gpkg(layer="high_streets"),
        "a layer is missing",
    ),
    "the layer is not on the National Grid": (
        lambda: streets_gpkg(grid=4326),
        "a layer is missing",
    ),
    "the column of ids is not there": (
        lambda: streets_gpkg(columns=[name for name in COLUMNS if name != "highstreet_id"]),
        "a column is missing",
    ),
    "an id is not written": (
        lambda: streets_gpkg([MadeUpStreet(None, WITHIN.pieces)]),
        "an id is missing",
    ),
    "an outline is on another grid than the layer says": (
        lambda: streets_gpkg([MadeUpStreet(101, WITHIN.pieces, grid=4326)]),
        "a layer could not be read",
    ),
    "an outline is a line and encloses nothing": (
        lambda: streets_gpkg([MadeUpStreet(101, (((0.0, 0.0), (9.0, 0.0), (0.0, 0.0)),))]),
        "an outline is not a shape",
    ),
    "the layer holds no row": (lambda: streets_gpkg([]), "it holds no high street"),
}


@pytest.mark.parametrize("which", sorted(NOT_AS_DESCRIBED))
def test_a_file_that_is_not_as_described_stops_the_step(tmp_path: Path, which: str):
    made, said = NOT_AS_DESCRIBED[which]
    with pytest.raises(LockError) as refused:
        high_streets.read(opened_of(tmp_path, made()))
    assert refused.value.rule == "input_is_as_described"
    assert said in str(refused.value) and CANARY not in str(refused.value)


# The gate and the receipt


def test_the_gate_is_asked_before_the_file_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, given=Registry(sources=()))
    with pytest.raises(LockError) as refused:
        high_streets.build(inputs, spine.build(inputs_of(tmp_path / "spine")))
    assert refused.value.rule == "gate_refuses"


def test_the_file_is_given_for_scoring_and_for_nothing_else():
    (source,) = [one for one in registry().sources if one.id == high_streets.SOURCE]
    assert list(source.uses) == [Use.SCORING]


def test_a_file_with_no_receipt_is_not_read(tmp_path: Path):
    """The file is in the store, and nothing says of when it is. So no figure rests on it."""
    inputs = inputs_of(tmp_path, with_a_receipt=False)
    with pytest.raises(LockError) as refused:
        high_streets.build(inputs, spine.build(inputs))
    assert refused.value.rule == "input_has_one_receipt"


def test_every_file_behind_the_high_streets_is_registered_for_scoring(town: Found):
    for receipt in town.files:
        registry().require(receipt.source_id, Use.SCORING)
    assert sorted(receipt.source_id for receipt in town.files) == sorted(
        [high_streets.SOURCE, centres.CENTRES, spine.LOOKUP, spine.HOMES]
    )


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    high_streets.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before


# Which high street is nearest


def test_each_output_area_is_as_far_from_the_nearest_outline_as_was_worked_out_by_hand(
    town: Found,
):
    by_hand = [
        (ONE, 0),
        (ONE, 0),
        (ONE, 70),
        (ONE, 70),
        (ONE, 70),
        (THREE, 70),
        (TWO, 10),
        (TWO, 10),
        (THREE, 0),
        (THREE, 0),
        (THREE, 70),
        (THREE, 70),
    ]
    assert [town.nearest[oa] for oa in OAS] == [
        Nearest(name, float(metres)) for name, metres in by_hand
    ]
    assert (town.placed, town.may_be_nearer_beyond) == (12, 0)


def test_a_home_is_as_far_from_a_high_street_as_from_the_nearest_of_its_pieces(town: Found):
    """The home of b4 stands 10 metres from one piece of In Two, and 70 from the other."""
    assert town.nearest[OAS[7]] == Nearest(TWO, 10.0)


def test_the_order_of_the_rows_changes_nothing(town: Found, tmp_path: Path):
    turned = built(tmp_path, streets_gpkg([FAR_SIDE, IN_TWO, WITHIN]))
    assert turned.nearest == town.nearest and list(turned.centres) == list(town.centres)


def test_a_home_has_a_high_street_of_its_own_at_800_metres_as_it_has_a_town_centre(
    tmp_path: Path,
):
    at_the_reach = MadeUpStreet(104, (box(850, 100, 100, 100),))
    found = built(tmp_path, streets_gpkg([at_the_reach]))
    within = town_centres.within_reach(found)
    # The homes of column 0 stand at 50 metres east: 800 from the outline in row 1.
    assert found.nearest[OAS[0]].metres == 800.0 and OAS[0] in within
    assert OAS[2] not in within
    assert high_streets.REACH == town_centres.REACH == 800


# The edge of London


def test_a_home_nearer_to_homes_beyond_london_than_to_any_high_street_has_none(tmp_path: Path):
    """The homes beyond London stand at 750 metres east. A high street may stand among them.

    Within ends at 180 metres east. From the homes of c1, at 450, it is 270
    metres off and the homes beyond London are 300. From those of c2, at 550,
    it is 370 and they are 200.
    """
    found = built(tmp_path, streets_gpkg([WITHIN]), homes_in_the_middle(TOWN))
    assert found.nearest[OAS[8]] == Nearest(ONE, 270.0)
    assert OAS[9] not in found.nearest
    assert set(found.nearest) <= set(OAS)
    assert found.placed == 12 and found.may_be_nearer_beyond == 12 - len(found.nearest)
