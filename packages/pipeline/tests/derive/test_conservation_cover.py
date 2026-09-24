"""Conservation cover, from the platform's records to a share of the land of each area.

Every file here is made up: `heritage_support.py` writes the records, and the
tests of cells draw the town they stand on. Each square of the town is one
hectare, so each figure can be worked out by hand.

    Quillhaven 001   4 hectares. Old Quarter lies over 2 of them
    Quillhaven 002   4 hectares. Wharf lies over half of one
    Tallowgate 001   5 hectares, in an authority that sent nothing

A made-up outline is written to the sixth decimal place of a degree, as a
real one is. That is about a tenth of a metre, so land is held here to the
hundredth of a hectare, and a figure to the first decimal place it is given to.
"""

from dataclasses import replace
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, TAGS
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import land, spine
from burro_pipeline.derive import conservation_cover
from burro_pipeline.derive.conservation_cover import (
    COVERED,
    INSIDE_AREAS,
    ONE_OF_EACH,
    Authority,
    Cover,
    Outlined,
    one_of_each,
)
from burro_pipeline.derive.heritage_shapes import outline_from
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import LSOA_RATIO_BY_HOMES, Worked
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import held, registry
from .heritage_support import (
    AREAS,
    AUTHORITATIVE,
    CANARY,
    CONSERVATION,
    INNER_COURT,
    OF_QUILLHAVEN,
    OF_TALLOWGATE,
    OLD_QUARTER,
    QUAYSIDE,
    QUILLHAVEN,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    SOME,
    TALLOWGATE,
    TALLOWGATE_1,
    THE_COPY,
    THE_MINISTRY,
    WHARF,
    MadeUp,
    areas_file,
    inputs_of,
    outline,
    outlines,
)

LSOAS = tuple(f"E01999{number:03d}" for number in range(1, 7))
NO_FIGURE = Worked(None, 0, 2, 0.0, State.SOURCE_GAP)
# The platform's number for an authority outside London. It is not one it has given out.
A_NEIGHBOUR = "90003"


def built(inputs: Inputs) -> Cover:
    found = spine.build(inputs)
    return conservation_cover.build(inputs, found, land.build(inputs, found))


def of_areas(folder: Path, records: list[MadeUp]) -> Cover:
    return built(inputs_of(folder, areas=areas_file(records)))


def figures_of(found: Cover) -> dict[str, float | None]:
    return {area: one.value for area, one in found.worked.items()}


def drawn(entity: str, box: tuple[float, float, float, float], **said: str) -> Outlined:
    """A made-up conservation area as the measure holds one, from a box of the town."""
    written = outline(*box)
    made = outline_from(written["type"], written["coordinates"])
    assert made is not None
    given = {"provider": OF_QUILLHAVEN, "quality": AUTHORITATIVE, "entered": "2024-05-01"} | said
    return Outlined(entity=entity, shape=made[0], **given)


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Cover:
    return built(inputs_of(tmp_path_factory.mktemp("town")))


@pytest.fixture(scope="module")
def both(tmp_path_factory: pytest.TempPathFactory) -> Cover:
    """The town with a conservation area in each of its two authorities."""
    return of_areas(tmp_path_factory.mktemp("both"), [*AREAS, QUAYSIDE])


# The figure


def test_the_conservation_land_of_each_lsoa_is_what_lies_inside_an_area(both: Cover):
    assert list(both.inside) == list(LSOAS)
    expected = (2.0, 0.0, 0.0, 0.5, 1.0, 0.0)
    for lsoa, hectares in zip(LSOAS, expected, strict=True):
        assert both.inside[lsoa] == pytest.approx(hectares, abs=0.01), lsoa
    assert conservation_cover.hectares_in(both.inside) == pytest.approx(3.5, abs=0.02)


def test_an_area_is_given_its_conservation_land_as_a_share_of_its_land(both: Cover):
    assert (100 * 2 / 4, 100 * 0.5 / 4, 100 * 1 / 5) == (50.0, 12.5, 20.0)
    assert both.worked == {
        QUILLHAVEN_1: Worked(50.0, 2, 2, 1.0, State.PRESENT),
        QUILLHAVEN_2: Worked(12.5, 2, 2, 1.0, State.PRESENT),
        TALLOWGATE_1: Worked(20.0, 2, 2, 1.0, State.PRESENT),
    }


def test_land_inside_two_conservation_areas_is_counted_once(tmp_path: Path, town: Cover):
    """Inner Court lies inside Old Quarter. Without it nothing moves."""
    without = of_areas(tmp_path, [area for area in AREAS if area != INNER_COURT])
    assert without.counted.kept == town.counted.kept - 1
    assert without.worked == town.worked


def test_an_area_in_a_covered_authority_that_no_record_touches_holds_nought(tmp_path: Path):
    found = of_areas(tmp_path, [WHARF])
    assert found.worked[QUILLHAVEN_1] == Worked(0.0, 2, 2, 1.0, State.PRESENT)
    assert found.inside[LSOAS[0]] == 0.0


def test_an_area_wholly_inside_a_conservation_area_reads_one_hundred(tmp_path: Path):
    """Each authority has an area of its own, so each is covered. One more lies over all."""
    everything = MadeUp("44000030", outline(-100, -300, 900, 700))
    found = of_areas(tmp_path, [everything, WHARF, replace(QUAYSIDE, entity="44000031")])
    assert figures_of(found) == {QUILLHAVEN_1: 100.0, QUILLHAVEN_2: 100.0, TALLOWGATE_1: 100.0}


def test_a_figure_is_given_to_one_decimal_place(tmp_path: Path):
    # 0.27 hectares of 4 is 6.75 in 100.
    found = of_areas(tmp_path, [MadeUp("44000030", outline(10, 10, 90, 30))])
    assert found.worked[QUILLHAVEN_1].value in (6.7, 6.8)


def test_conservation_land_that_is_more_than_the_land_of_its_lsoa_stops_the_step(
    tmp_path: Path, town: Cover
):
    inputs = inputs_of(tmp_path)
    found = spine.build(inputs)
    measured = replace(land.build(inputs, found), of_lsoa=dict.fromkeys(LSOAS, 1.0))
    with pytest.raises(ValueError, match="no more than its land"):
        conservation_cover.figures(dict(town.inside), measured, found)


def test_conservation_land_that_is_over_by_the_last_place_kept_is_all_of_the_land(
    tmp_path: Path,
):
    """An LSOA wholly inside an area is measured twice, and the two may differ in the last place."""
    inputs = inputs_of(tmp_path)
    found = spine.build(inputs)
    measured = land.build(inputs, found)
    inside = dict.fromkeys(LSOAS, 0.0) | {LSOAS[0]: 2.0001, LSOAS[1]: 2.0}
    assert conservation_cover.figures(inside, measured, found)[QUILLHAVEN_1].value == 100.0
    inside[LSOAS[0]] = 2.0002
    with pytest.raises(ValueError, match="no more than its land"):
        conservation_cover.figures(inside, measured, found)


# Which records


def test_every_record_of_the_file_is_counted_once(town: Cover):
    counted = town.counted
    assert (counted.in_the_file, counted.in_the_box, counted.nowhere) == (8, 7, 0)
    assert (counted.ended, counted.points, counted.no_land) == (1, 1, 0)
    assert (counted.mended, counted.outside, counted.twice, counted.kept) == (0, 1, 1, 3)
    left_out = counted.ended + counted.points + counted.no_land + counted.outside + counted.twice
    assert counted.in_the_box == left_out + counted.kept


def test_a_record_that_has_ended_is_left_out(tmp_path: Path):
    """Long Gone lay over Quillhaven 002 until 2020."""
    gone = MadeUp("44000005", outline(200, 100, 200, 100), ended="2020-01-01")
    found = of_areas(tmp_path, [WHARF, gone])
    assert found.counted.ended == 1
    assert found.worked[QUILLHAVEN_2].value == 12.5
    still = of_areas(tmp_path / "still", [WHARF, replace(gone, ended="")])
    assert still.worked[QUILLHAVEN_2].value == 62.5


def test_a_record_that_ends_after_the_day_of_the_file_is_still_counted(tmp_path: Path):
    later = MadeUp("44000005", outline(200, 100, 200, 100), ended="2026-09-25")
    found = of_areas(tmp_path, [WHARF, later])
    assert (found.counted.ended, found.worked[QUILLHAVEN_2].value) == (0, 62.5)
    that_day = of_areas(tmp_path / "day", [WHARF, replace(later, ended="2026-09-24")])
    assert (that_day.counted.ended, that_day.worked[QUILLHAVEN_2].value) == (1, 12.5)


def test_a_record_that_is_a_point_encloses_no_land_and_is_left_out(town: Cover):
    assert town.counted.points == 1
    assert town.inside[LSOAS[3]] == pytest.approx(0.5, abs=0.01)


def test_an_outline_whose_pieces_lie_over_one_another_is_mended_and_counted(tmp_path: Path):
    doubled = MadeUp("44000030", outlines((0, 0, 100, 100), (50, 0, 100, 100)))
    found = of_areas(tmp_path, [doubled])
    assert (found.counted.mended, found.counted.kept) == (1, 1)
    assert found.inside[LSOAS[1]] == pytest.approx(1.5, abs=0.01)


def test_a_record_outside_london_is_no_part_of_any_figure(town: Cover):
    assert town.counted.outside == 1
    assert sum(sum(one.areas.values()) for one in town.authorities.values()) == 3


def test_a_geometry_of_another_kind_stops_the_step(tmp_path: Path):
    line = MadeUp("44000030", {"type": "LineString", "coordinates": [[2.5, 53.41], [2.52, 53.41]]})
    with pytest.raises(LockError) as stopped:
        of_areas(tmp_path, [line])
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)


# One record for each area


def test_a_conservation_area_that_is_recorded_twice_is_counted_once(tmp_path: Path, town: Cover):
    """The Copy is Old Quarter again, ten metres short. Without it nothing moves."""
    assert town.counted.twice == 1
    without = of_areas(tmp_path, [area for area in AREAS if area != THE_COPY])
    assert without.counted.twice == 0
    assert without.worked == town.worked
    assert without.authorities[QUILLHAVEN].areas == town.authorities[QUILLHAVEN].areas


def test_of_two_records_of_one_area_the_authoritative_one_is_kept(town: Cover):
    assert town.authorities[QUILLHAVEN].areas == {(OF_QUILLHAVEN, AUTHORITATIVE): 3}
    assert town.authorities[QUILLHAVEN].twice == 1


def test_the_land_of_the_record_that_is_left_out_is_no_part_of_the_figure(tmp_path: Path):
    """The ministry's record runs 50 metres into the next LSOA. The authority's does not."""
    wider = MadeUp("44000002", outline(0, 50, 200, 150), provider=THE_MINISTRY, quality=SOME)
    found = of_areas(tmp_path, [OLD_QUARTER, wider])
    assert found.counted.twice == 1
    assert found.inside[LSOAS[1]] == pytest.approx(0.0, abs=0.01)
    assert found.worked[QUILLHAVEN_1].value == 50.0


def test_which_record_is_kept_does_not_turn_on_the_order_of_the_file(tmp_path: Path):
    one = of_areas(tmp_path / "one", [OLD_QUARTER, THE_COPY])
    other = of_areas(tmp_path / "other", [THE_COPY, OLD_QUARTER])
    assert one.authorities == other.authorities
    assert one.worked == other.worked


def test_the_order_records_are_kept_in_is_authoritative_then_entered_last_then_by_number():
    box = (0.0, 0.0, 100.0, 100.0)
    of_the_authority = drawn("9", box, quality=AUTHORITATIVE, entered="2020-01-01")
    newer = drawn("8", box, quality=SOME, entered="2026-01-01")
    older = drawn("7", box, quality=SOME, entered="2021-01-01")
    twin = drawn("6", box, quality=SOME, entered="2021-01-01")
    kept, left_out = one_of_each([older, newer, twin, of_the_authority])
    assert [outlined.entity for outlined in kept] == ["9"]
    assert left_out == {"8": "9", "7": "9", "6": "9"}
    kept, left_out = one_of_each([older, twin, newer])
    assert ([outlined.entity for outlined in kept], left_out) == (["8"], {"6": "8", "7": "8"})
    kept, left_out = one_of_each([older, twin])
    assert ([outlined.entity for outlined in kept], left_out) == (["6"], {"7": "6"})


def test_two_records_are_one_area_where_they_share_half_the_land_they_cover_together():
    """Two boxes of a hectare that share 0.67 of it share half of the 1.33 they cover."""
    first = drawn("1", (0, 0, 100, 100))
    kept, left_out = one_of_each([first, drawn("2", (33, 0, 100, 100))])
    assert ([outlined.entity for outlined in kept], left_out) == (["1"], {"2": "1"})
    kept, left_out = one_of_each([first, drawn("2", (34, 0, 100, 100))])
    assert ([outlined.entity for outlined in kept], left_out) == (["1", "2"], {})


def test_a_small_area_inside_a_large_one_is_not_a_second_record_of_it(town: Cover):
    assert town.counted.kept == 3
    kept, left_out = one_of_each([drawn("1", (0, 0, 200, 200)), drawn("2", (50, 50, 50, 50))])
    assert ([outlined.entity for outlined in kept], left_out) == (["1", "2"], {})


def test_a_record_is_left_out_only_for_one_that_is_kept():
    """B is A again, and C is B again, but C is not A. B is left out, so C is kept."""
    a = drawn("1", (0, 0, 100, 100), entered="2026-01-03")
    b = drawn("2", (30, 0, 100, 100), entered="2026-01-02")
    c = drawn("3", (60, 0, 100, 100), entered="2026-01-01")
    kept, left_out = one_of_each([c, b, a])
    assert ([outlined.entity for outlined in kept], left_out) == (["1", "3"], {"2": "1"})


# Which authorities


def test_an_authority_that_sent_nothing_has_no_figure_and_never_nought(town: Cover):
    assert town.authorities[TALLOWGATE] == Authority(TALLOWGATE, {}, 0, {})
    assert not town.authorities[TALLOWGATE].covered
    assert town.worked[TALLOWGATE_1] == NO_FIGURE
    assert town.worked[TALLOWGATE_1].value is None
    assert not set(town.inside) & set(LSOAS[4:])


def test_every_authority_of_the_build_is_counted_whether_or_not_it_sent_anything(town: Cover):
    assert list(town.authorities) == [QUILLHAVEN, TALLOWGATE]
    assert town.authorities[QUILLHAVEN].covered


def test_a_file_that_holds_no_record_of_london_gives_no_area_a_figure(tmp_path: Path):
    found = of_areas(tmp_path, [])
    assert set(found.worked.values()) == {NO_FIGURE}
    assert found.inside == {}
    assert not any(one.covered for one in found.authorities.values())


def test_an_area_is_given_to_the_authority_that_holds_most_of_its_land(tmp_path: Path):
    """40 metres of it lie in Quillhaven and 60 in Tallowgate, so it is Tallowgate's."""
    astride = MadeUp("44000030", outline(360, 100, 100, 100))
    found = of_areas(tmp_path, [astride])
    assert found.authorities[TALLOWGATE].areas == {(OF_QUILLHAVEN, AUTHORITATIVE): 1}
    assert found.authorities[QUILLHAVEN].areas == {}
    assert not found.authorities[QUILLHAVEN].covered


def test_an_area_astride_a_line_counts_on_both_sides_where_both_are_covered(tmp_path: Path):
    astride = MadeUp("44000030", outline(360, 100, 100, 100), provider=OF_TALLOWGATE)
    found = of_areas(tmp_path, [astride, WHARF])
    assert found.inside[LSOAS[2]] == pytest.approx(0.4, abs=0.01)
    assert found.inside[LSOAS[4]] == pytest.approx(0.6, abs=0.01)
    assert figures_of(found) == {QUILLHAVEN_1: 0.0, QUILLHAVEN_2: 22.5, TALLOWGATE_1: 12.0}


def test_a_record_a_neighbour_sent_does_not_stand_for_the_authority_it_spills_into(
    tmp_path: Path,
):
    """Ten metres of a record of Quillhaven lie in Tallowgate, which sent nothing."""
    spills = MadeUp("44000030", outline(300, 100, 110, 100))
    found = of_areas(tmp_path, [spills])
    assert not found.authorities[TALLOWGATE].covered
    assert found.worked[TALLOWGATE_1] == NO_FIGURE
    assert found.worked[QUILLHAVEN_2].value == 25.0


def test_a_record_that_lies_mostly_outside_london_does_not_stand_for_the_authority_it_crosses_into(
    tmp_path: Path,
):
    """Twenty metres of a record of a place outside London lie in Tallowgate, which sent nothing.

    It is given to Tallowgate, which holds all of its land that is in London.
    Tallowgate holds a tenth of it, so it says nothing of what Tallowgate has.
    """
    crosses = MadeUp("44000030", outline(580, 0, 200, 100), provider=A_NEIGHBOUR)
    found = of_areas(tmp_path, [crosses])
    assert found.counted.kept == 1
    assert found.authorities[TALLOWGATE].areas == {(A_NEIGHBOUR, AUTHORITATIVE): 1}
    assert found.authorities[TALLOWGATE].mostly == {}
    assert not found.authorities[TALLOWGATE].covered
    assert found.worked[TALLOWGATE_1] == NO_FIGURE
    assert set(found.worked.values()) == {NO_FIGURE}


def test_the_land_of_a_record_that_lies_mostly_outside_london_is_counted_where_others_cover(
    tmp_path: Path,
):
    """Quayside is Tallowgate's own. The land a neighbour's area takes in is conservation land."""
    crosses = MadeUp("44000030", outline(580, 0, 200, 100), provider=A_NEIGHBOUR)
    found = of_areas(tmp_path, [QUAYSIDE, crosses])
    assert found.authorities[TALLOWGATE].areas == {
        (OF_TALLOWGATE, AUTHORITATIVE): 1,
        (A_NEIGHBOUR, AUTHORITATIVE): 1,
    }
    assert found.authorities[TALLOWGATE].mostly == {(OF_TALLOWGATE, AUTHORITATIVE): 1}
    assert found.authorities[TALLOWGATE].covered
    assert found.inside[LSOAS[5]] == pytest.approx(0.2, abs=0.01)
    assert (100 * (1 + 0.2) / 5, found.worked[TALLOWGATE_1].value) == (24.0, 24.0)


def test_an_authority_is_covered_by_an_area_of_which_it_holds_over_half_and_not_by_one_of_less(
    tmp_path: Path,
):
    """Of 2 hectares, 1.1 lie in Tallowgate and the rest outside London. And then 0.8 do.

    A made-up outline is drawn to a tenth of a metre, so neither is drawn at the half.
    """
    more = MadeUp("44000030", outline(490, 0, 200, 100), provider=A_NEIGHBOUR)
    found = of_areas(tmp_path / "more", [more])
    assert found.authorities[TALLOWGATE].mostly == {(A_NEIGHBOUR, AUTHORITATIVE): 1}
    assert found.authorities[TALLOWGATE].covered
    assert found.worked[TALLOWGATE_1].value == 22.0
    less = MadeUp("44000030", outline(520, 0, 200, 100), provider=A_NEIGHBOUR)
    found = of_areas(tmp_path / "less", [less])
    assert found.authorities[TALLOWGATE].areas == {(A_NEIGHBOUR, AUTHORITATIVE): 1}
    assert not found.authorities[TALLOWGATE].covered
    assert found.worked[TALLOWGATE_1] == NO_FIGURE


def test_the_provider_and_the_quality_of_each_area_are_kept(tmp_path: Path, both: Cover):
    assert both.authorities[QUILLHAVEN].areas == {(OF_QUILLHAVEN, AUTHORITATIVE): 3}
    assert both.authorities[TALLOWGATE].areas == {(OF_TALLOWGATE, AUTHORITATIVE): 1}
    of_the_ministry = replace(WHARF, provider=THE_MINISTRY, quality=SOME)
    found = of_areas(tmp_path, [OLD_QUARTER, of_the_ministry])
    assert found.authorities[QUILLHAVEN].areas == {
        (THE_MINISTRY, SOME): 1,
        (OF_QUILLHAVEN, AUTHORITATIVE): 1,
    }


# The evidence


def test_every_area_has_a_row_whether_it_has_a_figure_or_not(town: Cover):
    assert [row.fact_id for row in town.rows] == [
        f"{area}/feature/conservation_cover" for area in (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE_1)
    ]
    assert [row.value for row in town.rows] == [50.0, 12.5, None]
    assert [row.state for row in town.rows] == [State.PRESENT, State.PRESENT, State.SOURCE_GAP]


def test_a_row_names_the_method_and_the_four_files_the_figure_rests_on(town: Cover):
    assert {row.derivation_id for row in town.rows} == {LSOA_RATIO_BY_HOMES.derivation_id}
    assert len(town.files) == 4
    assert {row.inputs for row in town.rows} == {
        tuple(sorted(receipt.file_id for receipt in town.files))
    }
    assert {receipt.source_id for receipt in town.files} == {
        conservation_cover.SOURCE,
        "ons-lsoa-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "ons-census-2021-housing-tables",
    }


def test_a_row_is_dated_from_the_census_to_the_day_of_the_file(town: Cover):
    span = Period(start="2021-03-21", end="2026-09-24")
    assert all(row.data_period == span for row in town.rows)
    assert {row.retrieved_on for row in town.rows} == {"2026-09-24"}


def test_the_rows_and_the_methods_make_evidence_that_holds_together(town: Cover):
    assert Evidence.of("lon-2026-10-09-01", town.files, conservation_cover.METHODS, town.rows)


def test_each_method_says_every_number_it_turns_on():
    assert conservation_cover.METHODS[0] == LSOA_RATIO_BY_HOMES
    assert {method.kind for method in conservation_cover.METHODS} == {Kind.MEASURED}
    assert ONE_OF_EACH.parameters == {"same_in_100": 50}
    assert COVERED.parameters == {"at_least": 1, "held_in_100": 50}
    assert "of which it holds 50 in 100 or more" in COVERED.sentence
    assert INSIDE_AREAS.parameters == {"decimal_places": 4}
    assert {method.code for method in (ONE_OF_EACH, COVERED, INSIDE_AREAS)} == {
        "burro_pipeline.derive.conservation_cover"
    }


# The row of the catalogue


def test_the_row_of_the_catalogue_is_what_core_says_the_measure_is(town: Cover):
    core = FEATURES[FeatureId.CONSERVATION_COVER]
    assert says_what_core_says(town.metric)
    assert town.metric.label == core.label == "Share of the area in a conservation area"
    assert (town.metric.unit, town.metric.polarity) == ("%", Polarity.MORE)
    assert town.metric.native_resolution is NativeResolution.POLYGON
    assert town.geography is Geography.POLYGON


def test_the_row_names_the_day_of_the_file_and_every_source(town: Cover):
    assert town.metric.vintage == "2026-09-24"
    assert town.metric.source_ids == (
        conservation_cover.SOURCE,
        "ons-census-2021-housing-tables",
        "ons-lsoa-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
    )
    for source_id in town.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_the_definition_says_what_is_counted_and_what_is_not(town: Cover):
    said = town.metric.definition
    for words in (
        "as at 2026-09-24",
        "recorded twice is counted once",
        "land inside two is counted once",
        "1 decimal place",
        "has no figure where its planning authority sent no conservation area",
    ):
        assert words in said


def test_what_the_figure_cannot_see_is_said_in_two_sentences():
    assert len(conservation_cover.CANNOT_SEE) == 2
    assert all(sentence.endswith(".") for sentence in conservation_cover.CANNOT_SEE)
    assert "may be incomplete" in conservation_cover.CANNOT_SEE[1]


def test_no_word_of_the_measure_says_who_lives_anywhere(town: Cover):
    said = " ".join(
        [town.metric.label, town.metric.definition, *conservation_cover.CANNOT_SEE]
        + [method.sentence for method in conservation_cover.METHODS[2:]]
    ).lower()
    for word in ("resident", "people", "household", "population", "who lives"):
        assert word not in said


def test_the_source_never_decides_a_vibe_alone():
    """The registry asks it. Core places no vibe on under 60 in 100 of its recipe."""
    for tag in TAGS.values():
        parts = [
            term.hundredths for term in tag.terms if term.feature_id is conservation_cover.FEATURE
        ]
        assert sum(parts) < 60


# The gate, and the files


def test_the_gate_is_asked_about_the_file_before_it_is_read(tmp_path: Path):
    with pytest.raises(LockError) as stopped:
        built(inputs_of(tmp_path, given=replace_uses(conservation_cover.SOURCE)))
    assert stopped.value.rule == "gate_refuses"
    assert not list((tmp_path / "work").rglob("*.geojson"))


def replace_uses(source_id: str) -> Registry:
    """The repository's registry, with one source allowed for display alone."""
    return Registry(
        tuple(
            one.model_copy(update={"uses": (Use.DISPLAY,)}) if one.id == source_id else one
            for one in registry().sources
        )
    )


def test_a_build_with_no_file_of_conservation_areas_is_refused(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    without = Inputs(
        inputs.registry,
        [one for one in inputs.receipts if one.source_id != conservation_cover.SOURCE],
        inputs.store,
        inputs.work,
    )
    with pytest.raises(LockError) as stopped:
        built(without)
    assert stopped.value.rule == "input_has_one_receipt"


def test_the_made_up_file_is_the_file_the_measure_reads():
    assert (
        conservation_cover.SOURCE,
        conservation_cover.FILE,
        conservation_cover.DATASET,
    ) == CONSERVATION
    assert conservation_cover.is_the_file(CONSERVATION[1])


def test_the_file_is_known_by_the_publishers_name_for_it():
    assert conservation_cover.is_the_file("conservation-area.geojson")
    assert not conservation_cover.is_the_file("conservation-area.csv")
    assert not conservation_cover.is_the_file("listed-building.geojson")
    assert not conservation_cover.is_the_file("conservation-area.geojson.part")


def test_built_twice_the_figures_and_the_rows_are_the_same(tmp_path: Path, town: Cover):
    again = built(inputs_of(tmp_path, areas=areas_file(AREAS[::-1])))
    assert again.worked == town.worked
    assert again.authorities == town.authorities
    assert again.counted == town.counted


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    built(inputs)
    assert held(tmp_path / "store") == before
