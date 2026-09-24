"""The nearest park, from the publisher's ways in to a distance for each area.

Every file here is made up: `green_support.py` draws the sites, and the tests
of cells draw the town they stand on. The centre of each output area is put in
the very middle of its square, so each distance can be worked out by hand.

    Long Meadow, 2 hectares     a gate for walkers at (50, 150), and one for cars at (250, 150)
    Great, 20 hectares          a gate for walkers at (1000, 150)
    Pocket, 0.04 hectares       a gate for walkers. It is too small to count

    Quillhaven 001   homes 110, 120, 130, 140   at 0, 100, 100 and 141 metres from a gate
    Quillhaven 002   homes 150, 160, 170, 180   at 200, 300, 224 and 316
    Tallowgate 001   homes 190, 200, 210, 220   at 400, 450, 412 and 461
"""

import math
import re
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import centres, spine
from burro_pipeline.cells.spine import Homes
from burro_pipeline.derive import measures, park_proximity
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.park_proximity import Distances, Proximity
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
    EITHER,
    GREAT,
    LONG_MEADOW,
    OAS,
    ON_FOOT,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    TALLOWGATE,
    MadeUpWay,
    at,
    centres_in_the_middle,
    document,
    file_ids,
    inputs_of,
    tile,
    tiles,
)

AREAS = (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE)


def built(inputs: Inputs) -> Proximity:
    return park_proximity.build(inputs, spine.build(inputs))


def values_of(made: Distances) -> list[float | None]:
    return [made.worked[area].value for area in AREAS]


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Proximity:
    return built(inputs_of(tmp_path_factory.mktemp("town")))


@pytest.fixture(scope="module")
def large(tmp_path_factory: pytest.TempPathFactory) -> Proximity:
    inputs = inputs_of(tmp_path_factory.mktemp("large"))
    return park_proximity.build_large(inputs, spine.build(inputs))


@pytest.fixture(scope="module")
def alone(tmp_path_factory: pytest.TempPathFactory) -> Proximity:
    """The town with the file of its own square alone. It stands hard against two others."""
    return built(inputs_of(tmp_path_factory.mktemp("alone"), {"tc": tile("tc")}))


# Which parks count


def test_a_park_counts_from_two_hectares_and_a_large_one_from_twenty(town: Proximity):
    assert (town.parks.least, town.parks.parks, town.parks.without_a_way_in) == (2, 2, 0)
    assert town.parks.ways_in == (at(50, 150), at(1000, 150))
    assert (park_proximity.LEAST, park_proximity.LEAST_LARGE) == (2, 20)


def test_a_way_in_for_motor_vehicles_alone_is_not_counted(town: Proximity):
    """Long Meadow has a gate for cars 200 metres nearer to the homes of Quillhaven 002."""
    assert at(250, 150) not in town.parks.ways_in
    assert town.of_oa[OAS[4]] == 200.0


def test_a_way_in_for_both_is_a_way_in_on_foot(tmp_path: Path):
    ways_in = [MadeUpWay("idLONGMEADOW", EITHER, at(250, 150))]
    found = built(inputs_of(tmp_path, tiles(document([LONG_MEADOW], ways_in))))
    assert found.of_oa[OAS[4]] == 0.0


def test_a_park_with_no_way_in_on_foot_is_counted_as_one_and_is_no_nearer(tmp_path: Path):
    ways_in = [MadeUpWay("idGREAT", ON_FOOT, at(1000, 150))]
    found = built(inputs_of(tmp_path, tiles(document([LONG_MEADOW, GREAT], ways_in))))
    assert (found.parks.parks, found.parks.without_a_way_in) == (2, 1)
    assert found.of_oa[OAS[0]] == 950.0


def test_a_site_of_another_kind_or_under_the_size_is_no_park(town: Proximity):
    """The pocket garden and the golf course each have a gate nearer to Tallowgate."""
    assert town.of_oa[OAS[10]] == math.hypot(400, 100)
    assert at(410, 20) not in town.parks.ways_in
    assert at(300, 100) not in town.parks.ways_in


# The figure


def test_each_output_area_is_as_far_as_its_centre_is_from_the_nearest_way_in(town: Proximity):
    far = [0, 100, 100, math.hypot(100, 100), 200, 300, math.hypot(200, 100)]
    far += [math.hypot(300, 100), 400, 450, math.hypot(400, 100), math.hypot(450, 100)]
    assert [town.of_oa[oa] for oa in OAS] == far


def test_an_area_is_given_the_median_over_its_homes_to_the_nearest_ten_metres(town: Proximity):
    assert town.worked == {
        # 110 homes at 0 and 250 at 100: half of the 500 are no further than 100.
        QUILLHAVEN_1: Worked(100.0, 4, 4, 1.0, State.PRESENT),
        # 150 at 200, 170 at 224 and 160 at 300: half of the 660 are no further than 300.
        QUILLHAVEN_2: Worked(300.0, 4, 4, 1.0, State.PRESENT),
        # 190 at 400, 210 at 412 and 200 at 450: half of the 820 are no further than 450.
        TALLOWGATE: Worked(450.0, 4, 4, 1.0, State.PRESENT),
    }


def test_the_distance_to_a_large_park_is_to_a_park_of_twenty_hectares(large: Proximity):
    assert (large.parks.least, large.parks.parks) == (20, 1)
    # The nearer half of each area's homes are no further than 856, 658 and 461 metres.
    assert values_of(large) == [860.0, 660.0, 460.0]


@pytest.mark.parametrize(
    ("weighed", "median"),
    [
        ([(100.0, 1.0)], 100.0),
        ([(300.0, 1.0), (100.0, 1.0), (200.0, 1.0)], 200.0),
        # The weight divides in half between two distances: the mean of the two.
        ([(100.0, 10.0), (200.0, 10.0)], 150.0),
        ([(100.0, 10.0), (200.0, 5.0), (300.0, 5.0)], 150.0),
        ([(100.0, 9.0), (200.0, 5.0), (300.0, 5.0)], 200.0),
        # What weighs nothing is no part of it.
        ([(100.0, 0.0), (200.0, 1.0)], 200.0),
    ],
)
def test_the_median_is_the_distance_half_the_weight_is_no_further_than(
    weighed: list[tuple[float, float]], median: float
):
    assert park_proximity._median(weighed) == median  # pyright: ignore[reportPrivateUsage]


def test_a_figure_is_rounded_to_ten_metres_with_a_half_taken_upward(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    found = spine.build(inputs)
    of_oa = dict(zip(OAS, [455.0] * 4 + [454.99] * 4 + [4.0] * 4, strict=True))
    assert [one.value for one in park_proximity.figures(of_oa, found).values()] == [
        460.0,
        450.0,
        0.0,
    ]


def test_an_area_with_no_homes_is_weighed_by_its_output_areas():
    homes = Homes(area_of=dict.fromkeys(OAS[:3], QUILLHAVEN_1), homes=dict.fromkeys(OAS[:3], 0))
    of_oa = {OAS[0]: 100.0, OAS[1]: 300.0}
    found = park_proximity.median_by_homes(of_oa, homes)[QUILLHAVEN_1]
    assert found == Worked(200.0, 2, 3, round(2 / 3, 6), State.PARTIAL)


def test_the_nearest_is_found_however_far_it_is_and_however_the_points_lie():
    """Held to measuring to every point, for points laid out by arithmetic."""
    points = [(float(7 * n * n % 9_000), float(13 * n * n * n % 7_000)) for n in range(60)]
    near = park_proximity._Near(points)  # pyright: ignore[reportPrivateUsage]
    for home in [(0.0, 0.0), (4_500.5, 3_500.5), (-25_000.0, 40_000.0), (8_999.0, 6_999.0)]:
        every = min(math.hypot(x - home[0], y - home[1]) for x, y in points)
        assert near.nearest(home) == every
    assert park_proximity._Near([]).nearest((0.0, 0.0)) is None  # pyright: ignore[reportPrivateUsage]


# What the files cover


def test_a_home_nearer_to_a_square_that_was_not_read_than_to_a_park_has_no_distance(
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


def test_an_output_area_with_no_centre_has_no_distance_and_none_is_filled_in(tmp_path: Path):
    inputs = inputs_of(tmp_path, centres=centres_in_the_middle(left_out=[OAS[0]]))
    found = built(inputs)
    assert OAS[0] not in found.of_oa
    # The first output area holds 110 of the area's 500 homes.
    assert found.worked[QUILLHAVEN_1] == Worked(100.0, 3, 4, round(390 / 500, 6), State.PARTIAL)


def test_where_no_park_is_found_no_area_has_a_figure(tmp_path: Path):
    found = built(inputs_of(tmp_path, tiles(document([LONG_MEADOW], []))))
    assert found.of_oa == {}
    assert {one.state for one in found.worked.values()} == {State.SOURCE_GAP}


# The evidence


def test_every_area_has_a_row_that_holds_its_figure(town: Proximity, large: Proximity):
    assert [row.fact_id for row in town.rows] == [
        f"{area}/feature/park_proximity" for area in AREAS
    ]
    assert [row.value for row in town.rows] == [100.0, 300.0, 450.0]
    assert [row.fact_id for row in large.rows] == [
        f"{area}/feature/park_large_proximity" for area in AREAS
    ]
    assert [row.value for row in large.rows] == [860.0, 660.0, 460.0]
    for row in (*town.rows, *large.rows):
        assert row.derivation_id == "straight_line_to_nearest@1"
        assert row.retrieved_on == "2026-09-23"
        assert row.data_period is not None
        assert row.data_period.days() == ("2021-03-21", "2026-04-30")


def test_a_row_names_the_files_of_the_squares_no_further_than_the_way_in(town: Proximity):
    """A way in that was found 100 metres off rules out a nearer one 150 metres off."""
    ids = file_ids(tiles())
    by_source = {receipt.source_id: receipt.file_id for receipt in town.files}
    ground = {by_source[source] for source in (centres.CENTRES, spine.LOOKUP, spine.HOMES)}
    of_sites = [set(row.inputs) - ground for row in town.rows]
    # A home in the corner of Quillhaven 001 is 100 metres from a gate and 50 from two lines.
    assert of_sites[0] == set(ids.values())
    assert of_sites[1] == of_sites[2] == {ids["tc"], ids["th"]}
    assert all(ground <= set(row.inputs) for row in town.rows)


def test_the_evidence_of_each_measure_has_no_loose_end(town: Proximity, large: Proximity):
    for made in (town, large):
        evidence = Evidence.of("lon-2026-10-02-01", made.files, park_proximity.METHODS, made.rows)
        assert len(evidence.rows) == 3
        assert made.geography is Geography.POINT
    assert park_proximity.METHOD.kind is Kind.MEASURED
    assert park_proximity.METHOD.code == "burro_pipeline.derive.park_proximity"


# The gate and the store


def test_the_gate_is_asked_before_the_sites_are_read(tmp_path: Path):
    sources = [
        source.model_copy(update={"uses": (Use.DISPLAY,)})
        if source.id == park_proximity.SOURCE
        else source
        for source in registry()
    ]
    inputs = inputs_of(tmp_path, given=Registry(tuple(sources)))
    found = spine.build(inputs)
    before = inputs.opened
    with pytest.raises(LockError) as stopped:
        park_proximity.build(inputs, found)
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
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    built(inputs)
    assert held(tmp_path / "store") == before


# The name, the unit and the sentences


def test_the_share_of_homes_with_a_distance_is_kept_with_a_half_taken_upward():
    homes = Homes(area_of=dict.fromkeys(OAS[:2], QUILLHAVEN_1), homes={OAS[0]: 1, OAS[1]: 127})
    found = park_proximity.median_by_homes({OAS[0]: 250.0}, homes)[QUILLHAVEN_1]
    assert (found.value, found.state, found.weight_covered) == (
        None,
        State.BELOW_THRESHOLD,
        0.007813,
    )


@pytest.mark.parametrize(("which", "least"), [("town", 2), ("large", 20)])
def test_the_name_says_it_is_a_straight_line_and_core_says_the_same(
    which: str, least: int, request: pytest.FixtureRequest
):
    """Core's words are held here, so that this fails on the day core names a walk again.

    Until the distance is a walk on a network of streets, no release carries it under a
    name that says a walk.
    """
    metric = request.getfixturevalue(which).metric
    feature = FEATURES[metric.feature_id]
    assert metric.label == (
        f"Straight-line distance to the nearest marked way into a park of {least} ha or more"
    )
    assert feature.label == metric.label and "walk" not in metric.label.lower()
    assert says_what_core_says(metric)
    assert (
        (metric.unit, metric.polarity) == (feature.unit, feature.polarity) == ("m", Polarity.LESS)
    )
    assert metric.native_resolution is feature.native_resolution is NativeResolution.POINT
    assert metric.vintage == "2026-04"


def test_the_sentence_of_the_method_says_what_is_done_where_the_homes_divide_in_half():
    """Two readings of a median differ by tens of metres in a few areas. The sentence chooses."""
    sentence = park_proximity.METHOD.sentence
    assert "the mean of the two middle distances" in sentence
    assert sentence.endswith(".") and sentence.count(". ") == 0


def test_the_large_park_is_a_measure_of_its_own_that_a_build_carries(large: Proximity):
    """Core gained the feature with the vibes. It is the same distance, to a larger park."""
    assert park_proximity.LARGE is FeatureId.PARK_LARGE_PROXIMITY
    assert large.metric.feature_id is FeatureId.PARK_LARGE_PROXIMITY
    assert large.metric.definition == park_proximity.definition_of("2026-04", 20)
    carried = {measure.feature: measure for measure in measures.MEASURES}
    assert carried[park_proximity.LARGE].waits_on == ()
    assert carried[park_proximity.LARGE].in_squares
    assert carried[park_proximity.LARGE].methods == carried[park_proximity.FEATURE].methods


@pytest.mark.parametrize(
    ("least", "said"), [(2, "2 hectares or more"), (20, "20 hectares or more")]
)
def test_the_definition_is_one_sentence_that_says_it_is_a_straight_line(least: int, said: str):
    definition = park_proximity.definition_of("2026-04", least)
    assert definition.endswith(".") and not re.search(r"[.!?]\s|\n", definition)
    for words in (
        "in a straight line",
        "way in on foot",
        said,
        "Ordnance Survey",
        "Public Park Or Garden",
        "OS Open Greenspace as at 2026-04",
        "median",
        "census of 2021",
        "nearest 10 metres",
        "not along any street or path",
        "the walk is longer",
    ):
        assert words in definition


def test_the_definition_of_the_measure_is_the_one_for_two_hectares(town: Proximity):
    assert town.metric.definition == park_proximity.definition_of("2026-04", 2)
    assert "straight line" in park_proximity.METHOD.sentence


RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|health|ages?|incomes?)\b", re.I
)


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(town: Proximity):
    sentences = (
        town.metric.definition,
        *park_proximity.CANNOT_SEE,
        park_proximity.METHOD.sentence,
    )
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_what_it_cannot_see_is_said_in_two_sentences_with_no_figure_in_them():
    assert len(park_proximity.CANNOT_SEE) == 2
    for sentence in park_proximity.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)
    assert "not a walk" in park_proximity.CANNOT_SEE[0]
