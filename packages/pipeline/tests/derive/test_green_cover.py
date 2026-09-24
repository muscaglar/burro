"""Green cover, from the publisher's sites to a share of the land of each area.

Every file here is made up: `green_support.py` draws the sites, and the tests
of cells draw the town they stand on. Each square of the town is one hectare,
so each figure can be worked out by hand.

    Quillhaven 001   4 hectares. Long Meadow lies over 1.5 of them
    Quillhaven 002   4 hectares. Long Meadow lies over 0.5, and the golf course over 2
    Tallowgate 001   5 hectares, one of them an island. The pocket garden is 0.04
"""

import re
from dataclasses import replace
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import land, spine
from burro_pipeline.derive import green_cover, green_sites
from burro_pipeline.derive.green_cover import Cover
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import LSOA_RATIO_BY_HOMES, Worked
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
    GREAT,
    LINKS,
    LONG_MEADOW,
    PARK,
    POCKET,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    TALLOWGATE,
    MadeUpSite,
    box,
    document,
    file_ids,
    inputs_of,
    tile,
    tiles,
)

LSOAS = tuple(f"E01999{number:03d}" for number in range(1, 7))


def built(inputs: Inputs) -> Cover:
    found = spine.build(inputs)
    return green_cover.build(inputs, found, land.build(inputs, found))


def of_sites(folder: Path, sites: list[MadeUpSite]) -> Cover:
    return built(inputs_of(folder, tiles(document(sites, []))))


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Cover:
    return built(inputs_of(tmp_path_factory.mktemp("town")))


@pytest.fixture(scope="module")
def alone(tmp_path_factory: pytest.TempPathFactory) -> Cover:
    """The town with the file of its own square alone. Its island lies on another."""
    return built(inputs_of(tmp_path_factory.mktemp("alone"), {"tc": tile("tc")}))


# The figure


def test_the_park_land_of_each_lsoa_is_what_lies_inside_a_park(town: Cover):
    assert town.inside == dict(zip(LSOAS, (1.5, 0.0, 0.5, 0.0, 0.0, 0.04), strict=True))
    assert green_cover.hectares_in(town.inside) == 2.04
    assert (town.parks, town.sites) == (4, 8)


def test_an_area_is_given_its_park_land_as_a_share_of_its_land(town: Cover):
    assert (100 * 1.5 / 4, 100 * 0.5 / 4, 100 * 0.04 / 5) == (37.5, 12.5, 0.8)
    assert town.worked == {
        QUILLHAVEN_1: Worked(37.5, 2, 2, 1.0, State.PRESENT),
        QUILLHAVEN_2: Worked(12.5, 2, 2, 1.0, State.PRESENT),
        TALLOWGATE: Worked(0.8, 2, 2, 1.0, State.PRESENT),
    }


def test_a_garden_inside_a_park_is_counted_once(tmp_path: Path, town: Cover):
    """The made-up town has a walled garden inside its park. Without it nothing moves."""
    without = of_sites(tmp_path, [LONG_MEADOW, POCKET, LINKS, GREAT])
    assert without.parks == town.parks - 1
    assert without.worked == town.worked


def test_a_site_of_another_kind_is_not_counted(tmp_path: Path):
    """The golf course lies over half of Quillhaven 002, and is no part of its figure."""
    every = [replace(LONG_MEADOW, kind=kind, site_id=f"id{at}") for at, kind in kinds_but_park()]
    found = of_sites(tmp_path, [*every, POCKET])
    assert [one.value for one in found.worked.values()] == [0.0, 0.0, 0.8]
    assert (found.parks, found.sites) == (1, 13)


def kinds_but_park() -> list[tuple[int, str]]:
    return [(at, kind) for at, kind in enumerate(green_sites.KINDS) if kind != PARK]


def test_an_area_that_no_park_touches_holds_nought_and_nought_is_a_figure(tmp_path: Path):
    found = of_sites(tmp_path, [GREAT])
    assert set(found.worked.values()) == {Worked(0.0, 2, 2, 1.0, State.PRESENT)}
    assert set(found.inside.values()) == {0.0}


def test_a_figure_is_given_to_one_decimal_place_with_a_half_taken_upward(tmp_path: Path):
    # 0.25 hectares of 4 is 6.25 in 100, and 0.35 of 4 is 8.75.
    sites = [
        MadeUpSite("idA", PARK, ((box(0, 0, 50, 50),),)),
        MadeUpSite("idB", PARK, ((box(200, 0, 70, 50),),)),
    ]
    found = of_sites(tmp_path, sites).worked
    assert (found[QUILLHAVEN_1].value, found[QUILLHAVEN_2].value) == (6.3, 8.8)


def test_an_area_wholly_inside_a_park_reads_one_hundred(tmp_path: Path):
    found = of_sites(tmp_path, [MadeUpSite("idALL", PARK, ((box(-100, -100, 500, 400),),))])
    assert found.worked[QUILLHAVEN_1].value == 100.0
    assert found.worked[QUILLHAVEN_2].value == 100.0


# What the files cover


def test_an_lsoa_on_a_square_no_file_was_read_for_has_no_park_land_that_is_known(alone: Cover):
    assert sorted(alone.inside) == list(LSOAS[:5])


def test_below_half_the_homes_covered_no_figure_is_given(alone: Cover):
    """Tallowgate's island is on another square. 390 of its 820 homes are in the LSOA read."""
    assert alone.worked[TALLOWGATE] == Worked(
        None, 1, 2, round(390 / 820, 6), State.BELOW_THRESHOLD
    )
    assert alone.worked[QUILLHAVEN_1] == Worked(37.5, 2, 2, 1.0, State.PRESENT)


def test_an_area_that_no_file_covers_is_a_gap_and_rests_on_every_file_read(tmp_path: Path):
    """With the file of the square to the south alone, only the island is on a square read."""
    squares = {"th": tiles()["th"]}
    found = built(inputs_of(tmp_path, squares))
    assert set(found.worked.values()) == {Worked(None, 0, 2, 0.0, State.SOURCE_GAP)}
    assert {file_ids(squares)["th"]} <= {file_id for row in found.rows for file_id in row.inputs}
    assert [row.value for row in found.rows] == [None, None, None]


# The evidence


def test_every_area_has_a_row_that_holds_its_figure(town: Cover, alone: Cover):
    assert [row.fact_id for row in town.rows] == [
        f"{area}/feature/green_cover" for area in (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE)
    ]
    assert [row.value for row in town.rows] == [37.5, 12.5, 0.8]
    assert [row.state for row in alone.rows] == [
        State.PRESENT,
        State.PRESENT,
        State.BELOW_THRESHOLD,
    ]
    assert {row.derivation_id for row in town.rows} == {LSOA_RATIO_BY_HOMES.derivation_id}
    assert {row.retrieved_on for row in town.rows} == {"2026-09-23"}


def test_a_row_names_the_files_of_the_squares_its_area_lies_on(town: Cover):
    ids = file_ids(tiles())
    by_source = {receipt.source_id: receipt.file_id for receipt in town.files}
    ground = {by_source[source] for source in (land.BOUNDARIES, spine.LOOKUP, spine.HOMES)}
    of_sites = [set(row.inputs) - ground for row in town.rows]
    # The island of Tallowgate is on the square to the south.
    assert of_sites == [{ids["tc"]}, {ids["tc"]}, {ids["tc"], ids["th"]}]
    assert all(ground <= set(row.inputs) for row in town.rows)
    assert {receipt.file_id for receipt in town.files} == ground | set(ids.values())


def test_a_row_spans_from_the_census_to_the_month_the_sites_are_of(town: Cover):
    for row in town.rows:
        assert row.data_period is not None
        assert row.data_period.days() == ("2021-03-21", "2026-04-30")


def test_the_evidence_of_the_measure_has_no_loose_end(town: Cover):
    evidence = Evidence.of("lon-2026-10-02-01", town.files, green_cover.METHODS, town.rows)
    assert len(evidence.rows) == 3
    assert [method.kind for method in green_cover.METHODS] == [Kind.MEASURED] * 3
    assert town.geography is Geography.POLYGON


# The gate and the store


def test_the_gate_is_asked_before_the_sites_are_read(tmp_path: Path):
    sources = [
        source.model_copy(update={"uses": (Use.DISPLAY,)})
        if source.id == green_cover.SOURCE
        else source
        for source in registry()
    ]
    inputs = inputs_of(tmp_path, given=Registry(tuple(sources)))
    found = spine.build(inputs)
    measured = land.build(inputs, found)
    before = inputs.opened
    with pytest.raises(LockError) as stopped:
        green_cover.build(inputs, found, measured)
    assert stopped.value.rule == "gate_refuses"
    assert inputs.opened == before


def test_every_file_behind_a_figure_is_registered_for_scoring(town: Cover):
    for source_id in town.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    built(inputs)
    assert held(tmp_path / "store") == before


# The name, the unit and the sentences


def test_the_label_says_parks_and_gardens_and_core_says_the_same(town: Cover):
    """Core's words are held here, so that this fails on the day core changes them.

    The figure counts public parks and gardens alone, and the licence registry asks that
    the product is never described as all green space. Core names the measure for what
    it counts, and says of an area that it has more of it than others, and never that
    it is greener. So the row of the catalogue is core's, and a build carries the measure.
    """
    core = FEATURES[FeatureId.GREEN_COVER]
    assert core.label == "Public parks and gardens as a share of the area"
    assert (core.higher, core.lower) == ("more", "less")
    assert town.metric.label == core.label
    said = " ".join((core.label, core.short_label, core.higher, core.lower)).lower()
    assert "green" not in said
    assert says_what_core_says(town.metric)


def test_the_registry_asks_that_the_sites_are_never_called_all_green_space():
    """The condition the name of the measure is held to. It is the registry's to change."""
    conditions = registry().get(green_cover.SOURCE).conditions
    assert "Do not describe it as all green space." in " ".join(conditions)


def test_core_decides_the_unit_and_which_way_is_more(town: Cover):
    metric, core = town.metric, FEATURES[FeatureId.GREEN_COVER]
    assert (metric.feature_id, metric.dimension) == (core.feature_id, core.dimension)
    assert (metric.unit, metric.polarity) == (core.unit, core.polarity)
    assert (metric.unit, metric.polarity) == ("%", Polarity.MORE)
    assert metric.native_resolution is NativeResolution.POLYGON
    assert metric.vintage == "2026-04"
    assert metric.source_ids == (
        "ons-census-2021-housing-tables",
        "ons-lsoa-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "os-open-greenspace",
    )


def test_the_definition_is_one_sentence_that_says_what_is_counted_and_what_is_not(town: Cover):
    definition = town.metric.definition
    assert definition.endswith(".") and not re.search(r"[.!?]\s|\n", definition)
    for words in (
        "Ordnance Survey",
        "Public Park Or Garden",
        "OS Open Greenspace as at 2026-04",
        "as at 2021-12",
        "to 1 decimal place",
        "other 9 kinds",
        "counted once",
        "not all the green space",
    ):
        assert words in definition


RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|health|ages?|incomes?)\b", re.I
)


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(town: Cover):
    sentences = (
        town.metric.definition,
        *green_cover.CANNOT_SEE,
        *(method.sentence for method in green_cover.METHODS),
    )
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_what_it_cannot_see_is_said_in_two_sentences_with_no_figure_in_them():
    assert len(green_cover.CANNOT_SEE) == 2
    for sentence in green_cover.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)
    assert "holds more green land than this figure counts" in green_cover.CANNOT_SEE[0]
    assert "greener" not in " ".join(green_cover.CANNOT_SEE)
