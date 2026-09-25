"""How much of the nearest high street lies inside a conservation area, for each area.

Every file here is made up: `high_streets_support.py` draws the high streets,
`heritage_support.py` writes the conservation areas, and the tests of cells
draw the town they stand on.

    Within     all of it inside Old Quarter: 100 in 100
    In Two     one of its two pieces inside Wharf: 50 in 100
    Far Side   in Tallowgate, which sent nothing: not known. With Quayside, 50 in 100

    Quillhaven 001   the homes of a1 to a4 are nearest to Within
    Quillhaven 002   those of b1 to Within, of b3 and b4 to In Two, of b2 to Far Side
    Tallowgate 001   those of c1 to c4 to Far Side

A made-up conservation area is written to the sixth decimal place of a degree,
as a real one is. That is about a tenth of a metre. So a share is held exactly
where no conservation area cuts across a high street, and to a tenth where one
does.
"""

from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import Dimension, FeatureId, Method, NativeResolution, Polarity
from burro_pipeline.cells import centres, land, spine
from burro_pipeline.derive import conservation_cover, high_streets, highstreet_conserved, measures
from burro_pipeline.derive.highstreet_conserved import Conserved
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.town_centres import Found, Nearest
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import State
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import held, registry
from .centres_support import OAS, box
from .heritage_support import (
    AREAS,
    INNER_COURT,
    OLD_QUARTER,
    QUAYSIDE,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    TALLOWGATE_1,
    THE_COPY,
    WHARF,
    MadeUp,
    areas_file,
    outline,
)
from .high_streets_support import (
    AS_AT,
    CANARY,
    FAR_SIDE,
    IN_TWO,
    ONE,
    STREETS,
    THREE,
    TWO,
    WITHIN,
    MadeUpStreet,
    inputs_of,
    streets_gpkg,
)

# The day the made-up conservation areas are of.
DAY = "2026-09-24"
NOT_KNOWN = Worked(None, 0, 4, 0.0, State.SOURCE_GAP)


def built(inputs: Inputs) -> Conserved:
    return highstreet_conserved.build(inputs, spine.build(inputs))


def of(
    folder: Path,
    streets: list[MadeUpStreet] | None = None,
    areas: list[MadeUp] | None = None,
) -> Conserved:
    return built(
        inputs_of(
            folder,
            None if streets is None else streets_gpkg(streets),
            areas=None if areas is None else areas_file(areas),
        )
    )


def figures_of(found: Conserved) -> dict[str, float | None]:
    return {area: one.value for area, one in found.worked.items()}


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Conserved:
    return built(inputs_of(tmp_path_factory.mktemp("town")))


@pytest.fixture(scope="module")
def both(tmp_path_factory: pytest.TempPathFactory) -> Conserved:
    """The town with a conservation area in each of its two authorities."""
    return of(tmp_path_factory.mktemp("both"), areas=[*AREAS, QUAYSIDE])


# The share of a high street


def test_a_high_street_is_given_the_share_of_its_land_inside_a_conservation_area(both: Conserved):
    assert both.shares == {ONE: 100.0, TWO: 50.0, THREE: 50.0}
    assert both.conservation_areas == 4


def test_a_conservation_area_that_cuts_across_a_high_street_gives_it_a_share_of_its_length(
    tmp_path: Path,
):
    """Old Quarter ends at 200 metres east. A high street from 20 to 380 is half inside it."""
    long = MadeUpStreet(104, (box(20, 120, 360, 40),))
    assert of(tmp_path, [long]).shares["104"] == pytest.approx(50.0, abs=0.1)


def test_land_inside_two_conservation_areas_is_counted_once(tmp_path: Path):
    """Inner Court lies inside Old Quarter, and over the same high street. Nothing moves."""
    long = MadeUpStreet(104, (box(20, 120, 360, 40),))
    assert INNER_COURT in AREAS
    without = [area for area in AREAS if area != INNER_COURT]
    one, two = of(tmp_path / "one", [long], without), of(tmp_path / "two", [long])
    assert two.conservation_areas == one.conservation_areas + 1
    assert two.shares == one.shares and two.worked == one.worked


def test_a_conservation_area_recorded_twice_is_one_area(tmp_path: Path, town: Conserved):
    assert THE_COPY in AREAS
    without = of(tmp_path, areas=[area for area in AREAS if area != THE_COPY])
    assert without.conservation_areas == town.conservation_areas == 3
    assert without.shares == town.shares


def test_a_high_street_that_no_conservation_area_touches_holds_nought(tmp_path: Path):
    """Quillhaven sent its areas, and none is on In Two. Nought is what is known."""
    found = of(tmp_path, areas=[OLD_QUARTER])
    assert found.shares == {ONE: 100.0, TWO: 0.0}
    assert (150 * 100 + 170 * 0 + 180 * 0) / 500 == 30.0
    assert found.worked[QUILLHAVEN_2].value == 30.0


def test_the_sea_is_no_land_of_a_high_street(tmp_path: Path):
    """The town ends at nought metres east, and Old Quarter runs 20 metres out to sea.

    A high street from 40 metres out to 60 metres in has 60 in 100 of its
    outline on land, and all of that inside Old Quarter. Of its whole outline
    80 in 100 is.
    """
    ashore = MadeUpStreet(105, (box(-40, 120, 100, 40),))
    assert of(tmp_path, [ashore]).shares == {"105": 100.0}


def test_a_high_street_mostly_off_the_ground_that_is_known_has_no_share(tmp_path: Path):
    """From 60 metres out to 40 metres in, 40 in 100 of the outline is on land."""
    mostly_at_sea = MadeUpStreet(105, (box(-60, 120, 100, 40),))
    found = of(tmp_path, [mostly_at_sea, IN_TWO])
    assert found.shares == {TWO: 50.0}
    assert highstreet_conserved.KNOWN_IN_100 == 50


# An authority that sent nothing


def test_a_high_street_in_an_authority_that_sent_nothing_has_no_share_and_never_nought(
    town: Conserved,
):
    assert QUAYSIDE not in AREAS
    assert town.shares == {ONE: 100.0, TWO: 50.0}
    assert all(town.found.nearest[oa].centre == THREE for oa in OAS[8:])
    assert not set(OAS[8:]) & set(town.of_oa)
    assert town.worked[TALLOWGATE_1] == NOT_KNOWN


def test_a_high_street_across_a_border_is_measured_where_its_authority_sent_an_area(
    tmp_path: Path,
):
    """Quillhaven ends at 400 metres east, and Tallowgate sent nothing.

    A high street from 320 to 480 has half of its outline in Quillhaven, and
    all of that half inside a conservation area. What stands on the other
    half is not known, so it is no part of the share.
    """
    across = MadeUpStreet(106, (box(320, 120, 160, 40),))
    corner = MadeUp("44000010", outline(290, 90, 120, 120))
    assert of(tmp_path / "half", [across], [OLD_QUARTER, corner]).shares == {"106": 100.0}
    further = MadeUpStreet(106, (box(330, 120, 160, 40),))
    assert of(tmp_path / "less", [further], [OLD_QUARTER, corner]).shares == {}


# The figure of an area


def test_each_home_is_given_the_share_of_its_nearest_high_street(both: Conserved):
    by_hand = [100, 100, 100, 100, 100, 50, 50, 50, 50, 50, 50, 50]
    assert both.of_oa == {oa: float(share) for oa, share in zip(OAS, by_hand, strict=True)}


def test_an_area_is_given_the_mean_over_its_homes(both: Conserved):
    by_hand = (150 * 100 + 160 * 50 + 170 * 50 + 180 * 50) / 660
    assert by_hand == pytest.approx(61.3636, abs=1e-4)
    assert both.worked == {
        QUILLHAVEN_1: Worked(100.0, 4, 4, 1.0, State.PRESENT),
        QUILLHAVEN_2: Worked(61.4, 4, 4, 1.0, State.PRESENT),
        TALLOWGATE_1: Worked(50.0, 4, 4, 1.0, State.PRESENT),
    }


def test_a_home_whose_high_street_has_no_share_adds_nothing_and_lowers_the_coverage(
    town: Conserved,
):
    """The homes of b2 are nearest to Far Side. They are 160 of the 660 of Quillhaven 002."""
    assert (150 * 100 + 170 * 50 + 180 * 50) / 500 == 65.0
    assert town.worked[QUILLHAVEN_1] == Worked(100.0, 4, 4, 1.0, State.PRESENT)
    assert town.worked[QUILLHAVEN_2] == Worked(65.0, 3, 4, 0.757576, State.PARTIAL)


def test_below_half_the_homes_with_a_share_no_figure_is_given(tmp_path: Path):
    """With In Two gone, the homes of b1 and b3 are nearest to Within.

    Those of b2 and b4 are nearest to Far Side, which has no share. So 320 of
    the 660 homes of Quillhaven 002 have a share, which is under half.
    """
    found = of(tmp_path, [WITHIN, FAR_SIDE])
    assert [found.found.nearest[oa].centre for oa in OAS[4:8]] == [ONE, THREE, ONE, THREE]
    assert found.worked[QUILLHAVEN_2] == Worked(None, 2, 4, 0.484848, State.BELOW_THRESHOLD)


def test_a_figure_is_given_to_one_decimal_place_with_a_half_taken_upward(tmp_path: Path):
    found = spine.build(inputs_of(tmp_path))
    every = dict.fromkeys(OAS[:4], 0.0) | {OAS[2]: 12.5}
    assert 130 * 12.5 / 500 == 3.25
    assert highstreet_conserved.figures(every, found)[QUILLHAVEN_1].value == 3.3
    assert highstreet_conserved.DECIMALS == 1


def test_a_home_has_a_high_street_of_its_own_at_800_metres_and_not_a_metre_further():
    found = Found(
        centres={},
        nearest={
            "at the reach": Nearest(ONE, 800.0),
            "past it": Nearest(ONE, 800.001),
            "with no share": Nearest(THREE, 10.0),
        },
        placed=3,
        may_be_nearer_beyond=0,
        files=(),
        as_at=AS_AT,
    )
    assert highstreet_conserved.values(found, {ONE: 40.0}) == {"at the reach": 40.0}
    assert highstreet_conserved.REACH == 800


def test_the_order_of_the_rows_and_of_the_records_changes_nothing(tmp_path: Path, both: Conserved):
    turned = of(tmp_path, list(reversed(STREETS)), [QUAYSIDE, *reversed(AREAS)])
    assert turned.worked == both.worked and turned.shares == both.shares
    assert turned.of_oa == both.of_oa


# The gate, the receipts and the evidence


def test_the_gate_is_asked_before_a_file_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, given=Registry(sources=()))
    with pytest.raises(LockError) as refused:
        highstreet_conserved.build(inputs, spine.build(inputs_of(tmp_path / "spine")))
    assert refused.value.rule == "gate_refuses"


def test_a_file_of_high_streets_with_no_receipt_is_not_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, with_a_receipt=False)
    with pytest.raises(LockError) as refused:
        built(inputs)
    assert refused.value.rule == "input_has_one_receipt"


def test_a_row_of_evidence_names_every_file_the_figure_rests_on(town: Conserved):
    assert sorted(receipt.source_id for receipt in town.files) == sorted(
        [
            high_streets.SOURCE,
            conservation_cover.SOURCE,
            land.BOUNDARIES,
            centres.CENTRES,
            spine.LOOKUP,
            spine.HOMES,
        ]
    )
    for receipt in town.files:
        registry().require(receipt.source_id, Use.SCORING)
    behind = tuple(sorted(receipt.file_id for receipt in town.files))
    assert [row.fact_id for row in town.rows] == [
        f"{area}/feature/highstreet_conserved"
        for area in (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE_1)
    ]
    for row in town.rows:
        assert row.inputs == behind
        assert row.derivation_id == highstreet_conserved.METHOD.derivation_id
        assert row.value == town.worked[row.fact_id.split("/")[0]].value


def test_the_method_says_what_is_done(town: Conserved):
    method = highstreet_conserved.METHOD
    assert method.kind is Kind.MEASURED
    assert method.parameters == {"metres": 800, "known_in_100": 50, "enough_in_100": 50}
    assert highstreet_conserved.METHODS[0] is method
    for kept in (conservation_cover.ONE_OF_EACH, conservation_cover.COVERED, land.MEASURED):
        assert kept in highstreet_conserved.METHODS
    assert town.geography is Geography.POLYGON


def test_nothing_is_written_to_the_store_and_twice_is_the_same(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    first, second = built(inputs), built(inputs)
    assert held(tmp_path / "store") == before
    assert first.worked == second.worked and first.rows == second.rows


def test_no_name_of_a_high_street_or_of_a_conservation_area_is_read(town: Conserved):
    assert CANARY not in repr(town)


def test_it_reads_the_file_of_high_streets_and_no_other_of_its_source():
    assert highstreet_conserved.is_the_file("GLA_High_Street_boundaries_2.gpkg")
    assert not highstreet_conserved.is_the_file("Town_Centres_Boundaries.gpkg")
    assert highstreet_conserved.SOURCE == "gla-high-street-boundaries"


# What core holds


def test_core_holds_the_measure_and_it_is_on_the_list_of_a_build():
    """The founder chose on 2026-09-25 to serve Village feel, which is made of it."""
    assert highstreet_conserved.FEATURE is FeatureId.HIGHSTREET_CONSERVED
    (listed,) = [one for one in measures.MEASURES if one.source == high_streets.SOURCE]
    assert listed.feature is FeatureId.HIGHSTREET_CONSERVED
    assert listed.reads("GLA_High_Street_boundaries_2.gpkg")
    assert not listed.reads("Town_Centres_Boundaries.gpkg")
    assert listed.methods == highstreet_conserved.METHODS
    assert listed.cannot_see == highstreet_conserved.CANNOT_SEE
    # Nothing holds it back, and it waits on nothing: core says what the figure is.
    assert (listed.waits_on, listed.held_back) == ((), ())
    assert (listed.in_squares, listed.in_parts) == (False, False)
    behind = measures.behind()[FeatureId.HIGHSTREET_CONSERVED]
    assert behind.derivation_id == highstreet_conserved.METHOD.derivation_id
    assert behind.source_id == high_streets.SOURCE


def test_the_row_of_the_catalogue_says_what_core_says(town: Conserved):
    metric = town.metric
    core = FEATURES[FeatureId.HIGHSTREET_CONSERVED]
    assert measures.says_what_core_says(metric)
    assert (metric.feature_id, metric.unit) == (FeatureId.HIGHSTREET_CONSERVED, "%")
    assert metric.label == "Share of the nearest high street that lies in a conservation area"
    assert (metric.label, metric.short_label) == (core.label, core.short_label)
    assert (metric.dimension, metric.polarity) == (Dimension.HOMES, Polarity.MORE)
    assert metric.native_resolution is NativeResolution.POLYGON
    assert metric.method is Method.MEASURED
    # No likeness between areas counts it, and a wish for it alone may be ranked on.
    assert (metric.in_likeness, metric.rankable) == (False, True)
    assert metric.source_ids == tuple(sorted(receipt.source_id for receipt in town.files))
    assert metric.vintage == DAY
    for said in (AS_AT, DAY, "800 metres", "counted once", "tidal river", "no border"):
        assert said in metric.definition
    assert "{" not in metric.definition


def test_what_it_cannot_see_says_a_trunk_road_reads_as_a_village_street_does():
    assert len(highstreet_conserved.CANNOT_SEE) == 3
    assert "trunk road" in highstreet_conserved.CANNOT_SEE[0]
    assert "does not draw" in highstreet_conserved.CANNOT_SEE[1]
    assert WHARF in AREAS
