"""The nearest place of a kind, where a file gives each place by its postcode alone.

Every file here is made up: `by_postcode_support.py` says where each place
stands, on the made-up town of the tests of cells. No postcode here is one
that has been given out.
"""

import dataclasses
import math
import re
from pathlib import Path

import pytest
from burro_pipeline.cells import centres, postcodes, spine
from burro_pipeline.cells.postcodes import Lookup
from burro_pipeline.derive import nearest_by_postcode, park_proximity
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.nearest_by_postcode import Near, Placing
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.row import State
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.postcodes_support import (
    A_BOX,
    DIRECTORY,
    ENDED,
    IN_ANOTHER_FILE,
    LONG_ENDED,
    MILL_ROW,
    NO_POINT,
    NORTH_GATE,
    OUTSIDE,
    QUAY,
    point_of,
)
from ..cells.support import LONDON
from .by_postcode_support import AREAS, NO_POSTCODE, QUILLHAVEN_1, inputs_of

OAS = tuple(unit.oa for unit in LONDON)


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    return inputs_of(tmp_path_factory.mktemp("town"))


@pytest.fixture(scope="module")
def lookup(town: Inputs) -> Lookup:
    return postcodes.build(town)


# Where a place is put


def test_a_place_is_put_at_the_point_of_its_postcode(lookup: Lookup):
    points, tally = nearest_by_postcode.place([NORTH_GATE.postcode, QUAY.postcode], lookup)
    assert points == (point_of(NORTH_GATE), point_of(QUAY))
    assert tally == Placing(
        listed=2,
        placed=2,
        at_an_ended_postcode=0,
        not_a_postcode=0,
        not_of_london=0,
        too_coarse=0,
    )


def test_a_postcode_is_read_as_its_file_writes_it(lookup: Lookup):
    typed = ["qh1 1ck", "QH11CK", " QH1  1CK "]
    points, tally = nearest_by_postcode.place(typed, lookup)
    # Three places at one postcode are three places, on one point.
    assert points == (point_of(NORTH_GATE),)
    assert (tally.listed, tally.placed) == (3, 3)


def test_a_place_at_an_ended_postcode_is_put_where_the_postcode_last_stood(lookup: Lookup):
    points, tally = nearest_by_postcode.place([ENDED.postcode], lookup)
    assert points == (point_of(ENDED),)
    assert (tally.placed, tally.at_an_ended_postcode, tally.not_placed) == (1, 1, 0)


@pytest.mark.parametrize(
    ("typed", "why"),
    [
        (NO_POSTCODE, "not_a_postcode"),
        ("", "not_a_postcode"),
        (OUTSIDE.postcode, "not_of_london"),
        (NO_POINT.postcode, "not_of_london"),
        (IN_ANOTHER_FILE.postcode, "not_of_london"),
        ("QH7 7CK", "not_of_london"),
        # The middle of a postcode sector, and a point kept from before November 2000.
        (A_BOX.postcode, "too_coarse"),
        (LONG_ENDED.postcode, "too_coarse"),
    ],
)
def test_a_place_that_cannot_be_placed_is_put_nowhere_and_is_counted(
    lookup: Lookup, typed: str, why: str
):
    points, tally = nearest_by_postcode.place([typed], lookup)
    assert points == ()
    assert (tally.listed, tally.placed, tally.not_placed) == (1, 0, 1)
    assert getattr(tally, why) == 1


def test_what_is_said_of_the_places_holds_no_postcode(lookup: Lookup):
    typed = [row.postcode for row in DIRECTORY]
    points, tally = nearest_by_postcode.place(typed, lookup)
    said = repr(points) + repr(tally)
    for one in typed:
        assert one not in said and one.replace(" ", "") not in said
    assert {one.name for one in dataclasses.fields(Placing)} == {
        "listed",
        "placed",
        "at_an_ended_postcode",
        "not_a_postcode",
        "not_of_london",
        "too_coarse",
    }


# The nearest


def test_the_nearest_is_found_however_far_it_is_and_however_the_points_lie():
    """Held to measuring to every point, for points laid out by arithmetic."""
    points = [(float(7 * n * n % 9_000), float(13 * n * n * n % 7_000)) for n in range(60)]
    near = Near(points)
    for home in [(0.0, 0.0), (4_500.5, 3_500.5), (-25_000.0, 40_000.0), (8_999.0, 6_999.0)]:
        every = min(math.hypot(x - home[0], y - home[1]) for x, y in points)
        assert near.nearest(home) == every
    assert Near([]).nearest((0.0, 0.0)) is None


def test_the_nearest_is_found_as_the_distance_to_a_park_finds_it():
    """The two searches are two copies of one, until the measures are joined."""
    points = [(float(11 * n * n % 8_000), float(17 * n * n * n % 6_000)) for n in range(80)]
    other = park_proximity._Near(points)  # pyright: ignore[reportPrivateUsage]
    near = Near(points)
    for n in range(40):
        home = (float(37 * n * n % 9_000) - 500.0, float(41 * n % 7_000) - 500.0)
        assert near.nearest(home) == other.nearest(home)


def test_a_distance_is_known_where_no_home_outside_london_is_nearer_than_the_place():
    to_a_place = {"a": 100.0, "b": 300.0, "c": 300.0, "d": 50.0}
    to_a_home_outside = {"a": 200.0, "b": 299.9, "c": 300.0}
    kept, near_the_edge = nearest_by_postcode.known(to_a_place, to_a_home_outside)
    # At exactly the distance of the place, no place there could be nearer.
    assert kept == {"a": 100.0, "c": 300.0, "d": 50.0}
    assert near_the_edge == ("b",)


# The figure


def test_a_figure_is_rounded_to_a_hundred_metres_with_a_half_taken_upward(town: Inputs):
    found = spine.build(town)
    of_oa = dict(zip(OAS, [450.0] * 4 + [449.99] * 4 + [49.0] * 4, strict=True))
    assert [one.value for one in nearest_by_postcode.figures(of_oa, found).values()] == [
        500.0,
        400.0,
        0.0,
    ]
    assert (nearest_by_postcode.NEAREST, nearest_by_postcode.DECIMALS) == (100, -2)


def test_the_places_of_a_build_are_measured_from_the_centres_of_its_output_areas(town: Inputs):
    found = spine.build(town)
    listed = town.open("nhs-ods-gp-practices", Use.SCORING)
    made = nearest_by_postcode.build(
        town, found, listed, [NORTH_GATE.postcode, QUAY.postcode], "gp_walk"
    )
    far = [0, 100, 100, math.hypot(100, 100), 200, math.hypot(200, 100)]
    far += [math.hypot(200, 100), 200, math.hypot(100, 100), 100, 100, 0]
    assert [made.of_oa[oa] for oa in OAS] == far
    assert made.near_the_edge == ()
    assert [made.worked[area].value for area in AREAS] == [100.0, 200.0, 100.0]


def test_a_home_with_a_home_outside_london_nearer_than_the_place_found_has_no_distance(
    town: Inputs,
):
    """With no place in Tallowgate, the district beyond it is nearer than any place found."""
    found = spine.build(town)
    listed = town.open("nhs-ods-gp-practices", Use.SCORING)
    made = nearest_by_postcode.build(town, found, listed, [NORTH_GATE.postcode], "gp_walk")
    # The homes outside London stand at (750, 150). The four output areas of Tallowgate are
    # 200 to 316 metres from them, and 400 to 510 from the one place.
    assert made.near_the_edge == OAS[8:]
    assert set(made.of_oa) == set(OAS[:8])
    assert made.worked[AREAS[2]] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)
    # 150 homes at 200 metres, 170 at 224, 160 at 300 and 180 at 316.
    assert made.worked[AREAS[1]] == Worked(300.0, 4, 4, 1.0, State.PRESENT)
    assert made.worked[QUILLHAVEN_1].value == 100.0


def test_where_no_place_is_placed_no_area_has_a_figure(town: Inputs):
    found = spine.build(town)
    listed = town.open("nhs-ods-gp-practices", Use.SCORING)
    made = nearest_by_postcode.build(town, found, listed, [OUTSIDE.postcode], "gp_walk")
    assert made.of_oa == {}
    assert {one.state for one in made.worked.values()} == {State.SOURCE_GAP}
    assert [row.value for row in made.rows] == [None, None, None]
    assert (made.placing.listed, made.placing.not_of_london) == (1, 1)


def test_a_place_that_is_added_never_makes_a_home_further_from_one(town: Inputs):
    found = spine.build(town)
    listed = town.open("nhs-ods-gp-practices", Use.SCORING)
    few = nearest_by_postcode.build(
        town, found, listed, [NORTH_GATE.postcode, QUAY.postcode], "gp_walk"
    )
    more = nearest_by_postcode.build(
        town, found, listed, [NORTH_GATE.postcode, QUAY.postcode, MILL_ROW.postcode], "gp_walk"
    )
    assert all(more.of_oa[oa] <= few.of_oa[oa] for oa in OAS)
    assert more.of_oa[OAS[4]] == 0.0


def test_the_files_of_the_spine_and_of_the_places_are_files_of_the_build(tmp_path: Path):
    inputs, other = inputs_of(tmp_path / "one"), inputs_of(tmp_path / "other")
    found = spine.build(other)
    listed = inputs.open("nhs-ods-gp-practices", Use.SCORING)
    assert centres.CENTRES not in {one.receipt.source_id for one in inputs.opened}
    with pytest.raises(ValueError, match="files of this build"):
        nearest_by_postcode.build(
            inputs_of(tmp_path / "third"), found, listed, [NORTH_GATE.postcode], "gp_walk"
        )


# The method and the sentences


def test_the_method_says_it_is_a_straight_line_to_a_place_put_at_its_postcode():
    method = nearest_by_postcode.METHOD
    assert method.derivation_id == "straight_line_to_nearest_by_postcode@1"
    assert method.kind is Kind.MEASURED
    assert method.code == "burro_pipeline.derive.nearest_by_postcode"
    for words in (
        "in a straight line",
        "the point the postcode directory gives for its postcode",
        "the mean of the two middle distances",
        "no place outside London is placed",
        "under 50 in 100",
    ):
        assert words in method.sentence
    assert method.sentence.endswith(".") and method.sentence.count(". ") == 0
    assert "walk" not in method.sentence


RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|health|ages?|incomes?)\b", re.I
)


def test_what_every_measure_cannot_see_is_said_in_whole_sentences_about_places():
    said = nearest_by_postcode.OF_EVERY_MEASURE
    assert len(said) == 4
    for sentence in said:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s", sentence)
        assert RESIDENT_WORDS.search(sentence) is None
    assert "not a walk" in said[0]
    assert "a door of that postcode and may not be its own" in said[1]
    assert "nearest 100 metres" in said[1]
