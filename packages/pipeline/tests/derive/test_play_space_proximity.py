"""The nearest play space, from the publisher's ways in to a distance for each area.

Every file here is made up: `green_support.py` writes the sites as the
publisher lays them out, and the tests of cells draw the town they stand on.
The centre of each output area is put in the very middle of its square, so
each distance can be worked out by hand.

    Swings     a play space in the town, with a gate for walkers at (50, 150)
    Slide      a play space east of the town, outside London, with a gate at (750, 150)
    Locked     a play space with a gate for cars alone, at (250, 150)
    Unmarked   a play space with no way in marked
    Long Meadow, Links and Pitch are a park, a golf course and a playing field

    Quillhaven 001   homes 110, 120, 130, 140   at 0, 100, 100 and 141 metres from a gate
    Quillhaven 002   homes 150, 160, 170, 180   at 200, 300, 224 and 316
    Tallowgate 001   homes 190, 200, 210, 220   at 300, 200, 316 and 224, all from Slide
"""

import math
import re
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import centres, spine
from burro_pipeline.derive import measures, park_proximity, play_space_proximity
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.park_proximity import Proximity
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import held, registry
from .green_support import (
    BY_CAR,
    EITHER,
    LINKS,
    LONG_MEADOW,
    OAS,
    ON_FOOT,
    PLAY,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    TALLOWGATE,
    MadeUpSite,
    MadeUpWay,
    at,
    box,
    document,
    file_ids,
    inputs_of,
    tile,
    tiles,
)

AREAS = (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE)
SWINGS = MadeUpSite("idSWINGS", PLAY, ((box(40, 140, 20, 20),),))
SLIDE = MadeUpSite("idSLIDE", PLAY, ((box(740, 140, 20, 20),),))
LOCKED = MadeUpSite("idLOCKED", PLAY, ((box(240, 140, 20, 20),),))
UNMARKED = MadeUpSite("idUNMARKED", PLAY, ((box(340, 40, 20, 20),),))
PITCH = MadeUpSite("idPITCH", "Playing Field", ((box(400, 0, 100, 100),),))
SITES = (SWINGS, SLIDE, LOCKED, UNMARKED, LONG_MEADOW, LINKS, PITCH)
TO_SWINGS = MadeUpWay("idSWINGS", ON_FOOT, at(50, 150))
TO_SLIDE = MadeUpWay("idSLIDE", ON_FOOT, at(750, 150))
WAYS_IN = (
    TO_SWINGS,
    TO_SLIDE,
    MadeUpWay("idLOCKED", BY_CAR, at(250, 150)),
    # A gate of each other kind stands on the very centre of an output area.
    MadeUpWay("idLONGMEADOW", ON_FOOT, at(150, 150)),
    MadeUpWay("idLINKS", EITHER, at(350, 50)),
    MadeUpWay("idPITCH", ON_FOOT, at(450, 50)),
)
# How far the centre of each output area is from the nearest gate of a play space.
FAR = (
    *(0.0, 100.0, 100.0, math.hypot(100, 100)),
    *(200.0, 300.0, math.hypot(200, 100), math.hypot(300, 100)),
    *(300.0, 200.0, math.hypot(300, 100), math.hypot(200, 100)),
)


def town_of(
    sites: tuple[MadeUpSite, ...] = SITES, ways_in: tuple[MadeUpWay, ...] = WAYS_IN
) -> dict[str, bytes]:
    return tiles(document(sites, ways_in))


def built(inputs: Inputs) -> Proximity:
    return play_space_proximity.build(inputs, spine.build(inputs))


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Proximity:
    return built(inputs_of(tmp_path_factory.mktemp("town"), town_of()))


@pytest.fixture(scope="module")
def alone(tmp_path_factory: pytest.TempPathFactory) -> Proximity:
    """The town with the file of its own square alone. It stands hard against two others."""
    only = {"tc": tile("tc", document(SITES, WAYS_IN))}
    return built(inputs_of(tmp_path_factory.mktemp("alone"), only))


# Which sites count


def test_a_play_space_of_any_size_counts_where_it_has_a_way_in_on_foot(town: Proximity):
    """Four play spaces of 0.04 hectares each, of which two have a gate for walkers.

    The files of the three squares round the town hold a play space each, with no way in.
    """
    assert (town.parks.least, town.parks.parks, town.parks.without_a_way_in) == (0, 7, 5)
    assert town.parks.ways_in == (at(50, 150), at(750, 150))
    assert (play_space_proximity.COUNTS, play_space_proximity.LEAST) == ("Play Space", 0)


def test_a_play_space_with_a_way_in_for_motor_vehicles_alone_is_no_nearer(town: Proximity):
    """Locked has a gate for cars on the very centre of an output area of Quillhaven 002."""
    assert at(250, 150) not in town.parks.ways_in
    assert town.of_oa[OAS[4]] == 200.0


def test_a_play_space_with_no_way_in_marked_is_counted_as_one_and_is_no_nearer(
    town: Proximity,
):
    """Unmarked stands on the centre of an output area, which is 316 metres from a gate."""
    assert town.parks.parks - town.parks.without_a_way_in == 2
    assert town.of_oa[OAS[7]] == math.hypot(300, 100)


def test_a_park_a_golf_course_and_a_playing_field_are_no_play_space(town: Proximity):
    """Each has a gate for walkers on the very centre of an output area."""
    for gate, oa, far in (
        (at(150, 150), 1, 100.0),
        (at(350, 50), 7, 316.0),
        (at(450, 50), 10, 316.0),
    ):
        assert gate not in town.parks.ways_in
        assert round(town.of_oa[OAS[oa]]) == far


def test_a_way_in_for_both_is_a_way_in_on_foot(tmp_path: Path):
    ways_in = (TO_SWINGS, MadeUpWay("idLOCKED", EITHER, at(250, 150)))
    found = built(inputs_of(tmp_path, town_of(ways_in=ways_in)))
    assert found.of_oa[OAS[4]] == 0.0


# The figure


def test_each_output_area_is_as_far_as_its_centre_is_from_the_nearest_way_in(town: Proximity):
    assert [town.of_oa[oa] for oa in OAS] == list(FAR)


def test_an_area_is_given_the_median_over_its_homes_to_the_nearest_ten_metres(town: Proximity):
    assert town.worked == {
        # 110 homes at 0 and 250 at 100: half of the 500 are no further than 100.
        QUILLHAVEN_1: Worked(100.0, 4, 4, 1.0, State.PRESENT),
        # 150 at 200, 170 at 224 and 160 at 300: half of the 660 are no further than 300.
        QUILLHAVEN_2: Worked(300.0, 4, 4, 1.0, State.PRESENT),
        # 200 at 200 and 220 at 224: half of the 820 are no further than 224.
        TALLOWGATE: Worked(220.0, 4, 4, 1.0, State.PRESENT),
    }


def test_the_arithmetic_is_the_nearest_parks_and_no_copy_of_it():
    """The measure says which sites count. The distance and the median are made in one place."""
    assert play_space_proximity.METHOD is park_proximity.STRAIGHT_LINE
    assert play_space_proximity.METHODS == park_proximity.METHODS
    assert play_space_proximity.METHOD.code == "burro_pipeline.derive.park_proximity"
    source = Path(play_space_proximity.__file__).read_text(encoding="utf-8")
    assert "park_proximity.to_the_nearest(" in source
    assert "park_proximity.sites_of(" in source
    assert not re.search(r"\bmath\b|hypot|fsum|def _median|def distances", source)


# What the files cover


def test_a_play_space_outside_london_is_measured_to_where_it_is_the_nearest(
    town: Proximity, tmp_path: Path
):
    """Slide stands in the district east of the town. Without it Tallowgate is 500 metres off."""
    within = built(inputs_of(tmp_path, town_of(ways_in=(TO_SWINGS,))))
    assert within.worked[TALLOWGATE].value == 500.0
    assert town.worked[TALLOWGATE].value == 220.0
    assert within.worked[QUILLHAVEN_1] == town.worked[QUILLHAVEN_1]


def test_a_home_nearer_to_a_square_that_was_not_read_than_to_a_play_space_has_no_distance(
    alone: Proximity,
):
    """The two homes on the north side of Quillhaven 001 are nearer the gate than the line."""
    assert alone.of_oa == {OAS[0]: 0.0, OAS[1]: 100.0}


def test_below_half_the_homes_covered_no_figure_is_given_and_with_none_it_is_a_gap(
    alone: Proximity,
):
    assert alone.worked == {
        QUILLHAVEN_1: Worked(None, 2, 4, round(230 / 500, 6), State.BELOW_THRESHOLD),
        QUILLHAVEN_2: Worked(None, 0, 4, 0.0, State.SOURCE_GAP),
        TALLOWGATE: Worked(None, 0, 4, 0.0, State.SOURCE_GAP),
    }
    assert [row.value for row in alone.rows] == [None, None, None]
    assert all(row.inputs for row in alone.rows)


def test_where_no_play_space_has_a_way_in_no_area_has_a_figure(tmp_path: Path):
    found = built(inputs_of(tmp_path, town_of(ways_in=())))
    assert found.of_oa == {}
    assert {one.state for one in found.worked.values()} == {State.SOURCE_GAP}


# The evidence


def test_every_area_has_a_row_that_holds_its_figure(town: Proximity):
    assert [row.fact_id for row in town.rows] == [
        f"{area}/feature/play_space_proximity" for area in AREAS
    ]
    assert [row.value for row in town.rows] == [100.0, 300.0, 220.0]
    for row in town.rows:
        assert row.derivation_id == "straight_line_to_nearest@1"
        assert row.retrieved_on == "2026-09-23"
        assert row.data_period is not None
        assert row.data_period.days() == ("2021-03-21", "2026-04-30")


def test_a_row_names_the_files_of_the_squares_no_further_than_the_way_in(town: Proximity):
    ids = file_ids(town_of())
    by_source = {receipt.source_id: receipt.file_id for receipt in town.files}
    ground = {by_source[source] for source in (centres.CENTRES, spine.LOOKUP, spine.HOMES)}
    of_sites = [set(row.inputs) - ground for row in town.rows]
    # A home in the corner of Quillhaven 001 is 100 metres from a gate and 50 from two lines.
    assert of_sites[0] == set(ids.values())
    assert of_sites[1] == of_sites[2] == {ids["tc"], ids["th"]}
    assert all(ground <= set(row.inputs) for row in town.rows)


def test_the_evidence_of_the_measure_has_no_loose_end(town: Proximity):
    evidence = Evidence.of("lon-2026-10-02-01", town.files, play_space_proximity.METHODS, town.rows)
    assert len(evidence.rows) == 3
    assert town.geography is Geography.POINT
    assert play_space_proximity.METHOD.kind is Kind.MEASURED


# The gate and the store


def test_the_gate_is_asked_before_the_sites_are_read(tmp_path: Path):
    sources = [
        source.model_copy(update={"uses": (Use.DISPLAY,)})
        if source.id == play_space_proximity.SOURCE
        else source
        for source in registry()
    ]
    inputs = inputs_of(tmp_path, town_of(), given=Registry(tuple(sources)))
    found = spine.build(inputs)
    before = inputs.opened
    with pytest.raises(LockError) as stopped:
        play_space_proximity.build(inputs, found)
    assert stopped.value.rule == "gate_refuses"
    assert inputs.opened == before


def test_every_file_behind_a_figure_is_registered_for_scoring(town: Proximity):
    assert town.metric.source_ids == (
        "ons-census-2021-housing-tables",
        "ons-oa-pwc-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "os-open-greenspace",
    )
    for source_id in town.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path, town_of())
    before = held(tmp_path / "store")
    built(inputs)
    assert held(tmp_path / "store") == before


# The name, the unit and the sentences


def test_the_name_says_a_straight_line_and_core_says_the_same_so_a_build_carries_it(
    town: Proximity,
):
    """Core's words are held here, so that this fails on the day core names a walk again.

    Until the distance is a walk on a network of streets, no release carries it under a
    name that says a walk.
    """
    feature = FEATURES[FeatureId.PLAY_SPACE_PROXIMITY]
    assert town.metric.label == (
        "Straight-line distance to the nearest marked way into a play space"
    )
    assert feature.label == town.metric.label and "walk" not in town.metric.label.lower()
    assert says_what_core_says(town.metric)
    assert (
        (town.metric.unit, town.metric.polarity)
        == (feature.unit, feature.polarity)
        == ("m", Polarity.LESS)
    )
    assert town.metric.native_resolution is feature.native_resolution is NativeResolution.POINT
    assert town.metric.vintage == "2026-04"


def test_a_row_that_names_the_measure_a_walk_is_not_cores(town: Proximity):
    as_a_walk = town.metric.model_copy(update={"label": "Walk to the nearest play space"})
    assert not says_what_core_says(as_a_walk)


def test_the_measure_is_on_the_list_of_a_build_and_waits_on_nothing():
    listed = {measure.feature: measure for measure in measures.MEASURES}
    measure = listed[FeatureId.PLAY_SPACE_PROXIMITY]
    assert (measure.waits_on, measure.held_back) == ((), ())
    assert measure.in_squares
    assert measure.methods == listed[FeatureId.PARK_PROXIMITY].methods
    assert measure.cannot_see == play_space_proximity.CANNOT_SEE


def test_the_definition_is_one_sentence_that_says_it_is_a_straight_line():
    definition = play_space_proximity.definition_of("2026-04")
    assert definition.endswith(".") and not re.search(r"[.!?]\s|\n", definition)
    for words in (
        "in a straight line",
        "way in on foot",
        "a site of any size",
        "Ordnance Survey",
        "Play Space",
        "OS Open Greenspace as at 2026-04",
        "inside London or outside it",
        "median",
        "census of 2021",
        "nearest 10 metres",
        "not along any street or path",
        "the walk is longer",
        "is not counted",
    ):
        assert words in definition


def test_the_definition_of_the_measure_is_the_one_a_methods_page_prints(town: Proximity):
    assert town.metric.definition == play_space_proximity.definition_of("2026-04")


RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|child(ren)?|health|ages?|incomes?)\b",
    re.I,
)


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(town: Proximity):
    sentences = (
        town.metric.label,
        town.metric.definition,
        *play_space_proximity.CANNOT_SEE,
        play_space_proximity.METHOD.sentence,
    )
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_what_it_cannot_see_is_said_in_two_sentences_with_no_figure_in_them():
    assert len(play_space_proximity.CANNOT_SEE) == 2
    for sentence in play_space_proximity.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)
    assert "not a walk" in play_space_proximity.CANNOT_SEE[0]
    assert "open to all" in play_space_proximity.CANNOT_SEE[1]
