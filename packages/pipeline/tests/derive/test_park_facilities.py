"""What a park offers, from the publisher's sites to a count of kinds for each area.

Every file here is made up: `green_support.py` writes the sites as the
publisher lays them out, and the tests of cells draw the town they stand on.
The centre of each output area is put in the very middle of its square, so
each figure can be worked out by hand.

    Long Meadow   a park in the town, with a gate for walkers at (50, 150)
                  inside it: two play spaces and a tennis court
    East Park     a park east of the town, outside London, with a gate at (1500, 150)
                  inside it: a bowling green, a playing field and a golf course
                  beside it: a tennis court. Four parts in ten of a sports facility
    Shut Garden   a park with a gate for cars alone. Inside it: a sports facility
    Yard          a cemetery, with a play space inside it

    Within 1,200 metres of the gate of East Park: the six output areas east of (300, *)

    Quillhaven 001   homes 110, 120, 130, 140   all have 2 kinds within reach
    Quillhaven 002   homes 150, 160, 170, 180   320 have 2 kinds, and 340 have 4
    Tallowgate 001   homes 190, 200, 210, 220   all have 4
"""

import math
import re
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import centres, spine
from burro_pipeline.cells.shapes import hectares, outline_of
from burro_pipeline.derive import green_sites, measures, park_facilities
from burro_pipeline.derive.green_sites import Greenspace, Site, WayIn
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked, homes_within_at
from burro_pipeline.derive.park_facilities import Counted, Facilities, Offers
from burro_pipeline.derive.park_proximity import Parks
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
    CANARY,
    GOLF,
    LONG_MEADOW,
    OAS,
    ON_FOOT,
    PARK,
    PLAY,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    TALLOWGATE,
    MadeUpSite,
    MadeUpWay,
    at,
    box,
    centres_in_the_middle,
    document,
    file_ids,
    inputs_of,
    tile,
    tiles,
)

AREAS = (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE)
GREEN, SPORT, FIELD, COURT = (
    "Bowling Green",
    "Other Sports Facility",
    "Playing Field",
    "Tennis Court",
)
PLOT, YARD, GROUNDS = "Allotments Or Community Growing Spaces", "Cemetery", "Religious Grounds"


def site(site_id: str, kind: str, west: float, south: float, wide: float, high: float):
    return MadeUpSite(site_id, kind, ((box(west, south, wide, high),),))


EAST_PARK = site("idEASTPARK", PARK, 1500, 100, 100, 50)
SHUT_GARDEN = site("idSHUTGARDEN", PARK, 300, 0, 50, 50)
SITES = (
    LONG_MEADOW,
    site("idSWINGS", PLAY, 60, 110, 20, 20),
    site("idSLIDE", PLAY, 200, 110, 20, 20),
    site("idCOURT", COURT, 100, 110, 30, 30),
    EAST_PARK,
    site("idGREEN", GREEN, 1510, 105, 20, 20),
    site("idFIELD", FIELD, 1540, 100, 50, 50),
    site("idLINKS", GOLF, 1510, 130, 20, 10),
    # It lies against the east side of East Park.
    site("idCLUB", COURT, 1600, 100, 20, 20),
    # Four parts in ten of it lie inside East Park.
    site("idTRACK", SPORT, 1494, 100, 10, 10),
    SHUT_GARDEN,
    site("idGYM", SPORT, 310, 10, 20, 20),
    site("idYARD", YARD, 400, 0, 100, 100),
    site("idSANDPIT", PLAY, 410, 10, 20, 20),
)
TO_LONG_MEADOW = MadeUpWay("idLONGMEADOW", ON_FOOT, at(50, 150))
TO_EAST_PARK = MadeUpWay("idEASTPARK", ON_FOOT, at(1500, 150))
WAYS_IN = (
    TO_LONG_MEADOW,
    TO_EAST_PARK,
    MadeUpWay("idSHUTGARDEN", BY_CAR, at(300, 25)),
    MadeUpWay("idYARD", ON_FOOT, at(450, 50)),
    MadeUpWay("idSANDPIT", ON_FOOT, at(420, 20)),
    MadeUpWay("idFIELD", ON_FOOT, at(1540, 125)),
)
NEAR, BOTH = (PLAY, COURT), (GREEN, PLAY, FIELD, COURT)


def town_of(
    sites: tuple[MadeUpSite, ...] = SITES, ways_in: tuple[MadeUpWay, ...] = WAYS_IN
) -> dict[str, bytes]:
    return tiles(document(sites, ways_in))


def built(inputs: Inputs) -> Facilities:
    return park_facilities.build(inputs, spine.build(inputs))


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Facilities:
    return built(inputs_of(tmp_path_factory.mktemp("town"), town_of()))


@pytest.fixture(scope="module")
def alone(tmp_path_factory: pytest.TempPathFactory) -> Facilities:
    """The town with the file of its own square alone. It stands hard against two others."""
    only = {"tc": tile("tc", document(SITES, WAYS_IN))}
    return built(inputs_of(tmp_path_factory.mktemp("alone"), only))


def values_of(made: Facilities) -> list[float | None]:
    return [made.worked[area].value for area in AREAS]


# What is a park, and what it offers


def test_a_park_is_of_any_size_and_has_a_way_in_on_foot(town: Facilities):
    """East Park is half a hectare. Shut Garden has a gate for cars alone."""
    assert (park_facilities.PARK, park_facilities.LEAST) == ("Public Park Or Garden", 0)
    assert (town.offers.parks.parks, town.offers.parks.without_a_way_in) == (3, 1)
    assert town.offers.ways_in == ((at(50, 150), "idLONGMEADOW"), (at(1500, 150), "idEASTPARK"))


def test_a_park_offers_the_kinds_of_site_that_lie_inside_it(town: Facilities):
    assert town.offers.of_park == {
        "idEASTPARK": (GREEN, FIELD),
        "idLONGMEADOW": (PLAY, COURT),
    }


def test_five_kinds_may_be_counted_and_four_never_are():
    assert park_facilities.KINDS == (GREEN, SPORT, PLAY, FIELD, COURT)
    assert park_facilities.NEVER == (PLOT, YARD, GOLF, GROUNDS)
    every = {*park_facilities.KINDS, *park_facilities.NEVER, park_facilities.PARK}
    assert every == set(green_sites.KINDS)


def test_a_kind_is_counted_once_however_many_sites_of_it_a_park_holds(town: Facilities):
    """Long Meadow holds two play spaces. Four more stand in no park, three of them far off."""
    assert town.offers.counted[PLAY] == Counted(sites=6, inside_a_park=2)
    assert town.offers.of_park["idLONGMEADOW"].count(PLAY) == 1


def test_a_golf_course_inside_a_park_is_counted_as_left_out_and_is_no_kind(town: Facilities):
    assert town.offers.never[GOLF] == Counted(sites=1, inside_a_park=1)
    assert GOLF not in town.offers.of_park["idEASTPARK"]


def test_a_cemetery_is_no_park_so_what_stands_in_it_is_not_counted(town: Facilities):
    """The sandpit has a gate of its own, and the cemetery a gate for walkers."""
    assert town.offers.never[YARD] == Counted(sites=1, inside_a_park=0)
    assert "idYARD" not in town.offers.of_park
    assert all(park != "idYARD" for _, park in town.offers.ways_in)


@pytest.mark.parametrize("kind", [PLOT, YARD, GOLF, GROUNDS])
def test_a_site_of_a_kind_that_never_counts_is_no_park_and_no_kind(kind: str, tmp_path: Path):
    """It stands where Long Meadow did, with the gate and the sites that Long Meadow had."""
    sites = (MadeUpSite("idLONGMEADOW", kind, LONG_MEADOW.pieces), *SITES[1:4])
    ways_in = (TO_LONG_MEADOW,)
    inside = (*SITES[:4], site("idOTHER", kind, 60, 150, 20, 20))
    as_a_park = built(inputs_of(tmp_path / "park", town_of(sites, ways_in)))
    as_a_kind = built(inputs_of(tmp_path / "kind", town_of(inside, ways_in)))
    assert as_a_park.offers.of_park == {}
    assert values_of(as_a_park) == [0.0, 0.0, 0.0]
    assert as_a_kind.offers.of_park == {"idLONGMEADOW": (PLAY, COURT)}
    assert as_a_kind.offers.never[kind] == Counted(sites=1, inside_a_park=1)


def test_a_site_that_lies_against_a_park_is_not_inside_it(town: Facilities):
    """The club's court shares a side with East Park. Long Meadow holds the one court counted."""
    assert COURT not in town.offers.of_park["idEASTPARK"]
    assert town.offers.counted[COURT] == Counted(sites=2, inside_a_park=1)


def test_a_site_with_under_half_of_its_land_in_a_park_is_not_inside_it(
    town: Facilities, tmp_path: Path
):
    assert SPORT not in town.offers.of_park["idEASTPARK"]
    half = (*SITES, site("idHALF", SPORT, 1495, 120, 10, 10))
    found = built(inputs_of(tmp_path, town_of(half)))
    assert found.offers.of_park["idEASTPARK"] == (GREEN, SPORT, FIELD)
    assert (park_facilities.INSIDE, park_facilities.INSIDE_IN_100) == (0.5, 50)


def test_a_park_with_no_way_in_on_foot_offers_nothing(town: Facilities):
    """Shut Garden holds a sports facility, 50 metres from homes of Quillhaven 002."""
    assert "idSHUTGARDEN" not in town.offers.of_park
    assert town.offers.counted[SPORT] == Counted(sites=2, inside_a_park=1)
    assert all(SPORT not in kinds for kinds in town.within.kinds.values())


# Within reach


def test_a_park_is_within_reach_where_a_way_in_is_no_further_than_1200_metres(
    town: Facilities,
):
    """The gate of East Park is 1,150 metres from one home of Quillhaven 002 and 1,250 from
    the next."""
    assert park_facilities.REACH == 1_200
    assert math.hypot(1500 - 350, 100) < 1_200 < 1500 - 250
    near, both = ("idLONGMEADOW",), ("idEASTPARK", "idLONGMEADOW")
    assert [town.within.parks[oa] for oa in OAS] == [
        *(near, near, near, near),
        *(near, both, near, both),
        *(both, both, both, both),
    ]


def test_each_output_area_counts_the_kinds_in_the_parks_within_its_reach(town: Facilities):
    assert [town.within.kinds[oa] for oa in OAS] == [
        *(NEAR, NEAR, NEAR, NEAR),
        *(NEAR, BOTH, NEAR, BOTH),
        *(BOTH, BOTH, BOTH, BOTH),
    ]


def ground_of(sites: list[Site], ways_in: list[WayIn]) -> Greenspace:
    """Sites and ways in as if one file had been read, of the square the town stands on."""
    return Greenspace(
        sites={one.site_id: one for one in sites},
        ways_in=tuple(ways_in),
        file_of={(700_000, 400_000): "f-000000000000"},
        files=(),
        in_two_files=0,
        as_at="2026-04",
    )


def park_at(site_id: str, west: float, south: float, wide: float, high: float) -> Site:
    shape = outline_of([[box(west, south, wide, high)]])
    return Site(site_id, PARK, shape, hectares(shape), site_id)


def offers_at(*ways_in: WayIn) -> Offers:
    return Offers(
        parks=Parks(0, (), 0, 0),
        ways_in=tuple((way.point, way.site_id) for way in ways_in),
        of_park={way.site_id: (PLAY,) for way in ways_in},
        counted={},
        never={},
    )


def test_a_way_in_exactly_at_the_reach_is_within_it_and_a_metre_more_is_not():
    park = park_at("idPARK", 50_000, 51_200, 100, 100)
    gate = WayIn("idPARK", ON_FOOT, at(50_000, 51_200))
    green = ground_of([park], [gate])
    points = {"at": at(50_000, 50_000), "past": at(50_000, 49_999)}
    found = park_facilities.within_reach(green, offers_at(gate), points)
    assert found.parks == {"at": ("idPARK",), "past": ()}
    assert found.kinds == {"at": (PLAY,), "past": ()}


def test_an_output_area_whose_reach_takes_in_land_no_file_was_read_for_has_no_count():
    """One home stands 1,200 metres from the side of the square, and one a metre further in."""
    park = park_at("idPARK", 50_000, 50_000, 100, 100)
    gate = WayIn("idPARK", ON_FOOT, at(50_000, 50_000))
    green = ground_of([park], [gate])
    points = {"at": at(1_200, 50_000), "in": at(1_201, 50_000), "off": at(-10, 50_000)}
    found = park_facilities.within_reach(green, offers_at(gate), points)
    assert list(found.kinds) == ["in"]


def test_an_output_area_within_reach_of_a_park_that_lies_on_land_not_read_has_no_count():
    """The park lies across the north side of the square. What it offers is not all known."""
    across = park_at("idACROSS", 50_000, 99_000, 100, 1_100)
    gate = WayIn("idACROSS", ON_FOOT, at(50_000, 99_000))
    green = ground_of([across], [gate])
    points = {"near": at(50_000, 98_000), "far": at(50_000, 97_000)}
    found = park_facilities.within_reach(green, offers_at(gate), points)
    assert green.files_under(across.shape) is None
    assert found.parks == {"far": ()}


def test_the_town_with_the_file_of_its_own_square_alone_has_no_figure(alone: Facilities):
    """Every home of the town is within 1,200 metres of a square that was not read."""
    assert alone.within.kinds == {}
    assert alone.worked == {area: Worked(None, 0, 4, 0.0, State.SOURCE_GAP) for area in AREAS}
    assert [row.value for row in alone.rows] == [None, None, None]
    assert all(row.inputs for row in alone.rows)


def test_a_park_outside_london_is_counted_where_it_is_within_reach(
    town: Facilities, tmp_path: Path
):
    """East Park stands east of every output area of the town."""
    without = tuple(one for one in SITES if one.site_id != "idEASTPARK")
    ways_in = tuple(way for way in WAYS_IN if way.site_id != "idEASTPARK")
    found = built(inputs_of(tmp_path, town_of(without, ways_in)))
    assert values_of(found) == [2.0, 2.0, 2.0]
    assert values_of(town) == [2.0, 3.0, 4.0]


# The figure


def test_an_area_is_given_the_mean_number_of_kinds_over_its_homes(town: Facilities):
    assert town.worked == {
        QUILLHAVEN_1: Worked(2.0, 4, 4, 1.0, State.PRESENT),
        # 320 homes have 2 kinds and 340 have 4: 2,000 over 660 is 3.03.
        QUILLHAVEN_2: Worked(3.0, 4, 4, 1.0, State.PRESENT),
        TALLOWGATE: Worked(4.0, 4, 4, 1.0, State.PRESENT),
    }


def test_the_figure_is_the_sum_of_the_share_of_homes_with_each_kind(town: Facilities):
    shares = {kind: town.shares[kind][QUILLHAVEN_2].value for kind in park_facilities.KINDS}
    assert shares == {GREEN: 340 / 660, SPORT: 0.0, PLAY: 1.0, FIELD: 340 / 660, COURT: 1.0}
    assert math.fsum(value or 0.0 for value in shares.values()) == 2_000 / 660


def test_an_output_area_with_no_park_within_reach_counts_none_and_nought_is_a_figure(
    tmp_path: Path,
):
    """The files cover the town, and hold a cemetery and no park: so there is none."""
    found = built(inputs_of(tmp_path, town_of((site("idYARD", YARD, 400, 0, 100, 100),), ())))
    assert set(found.within.kinds.values()) == {()}
    assert found.worked == {area: Worked(0.0, 4, 4, 1.0, State.PRESENT) for area in AREAS}


def test_a_figure_is_given_to_one_decimal_place_with_a_half_taken_upward(tmp_path: Path):
    found = spine.build(inputs_of(tmp_path, town_of()))
    quarter = Worked(0.25, 4, 4, 1.0, State.PRESENT)
    half = Worked(0.5, 4, 4, 1.0, State.PRESENT)
    shares: dict[str, dict[str, Worked]] = {
        kind: {area: quarter if kind == GREEN else half for area in AREAS}
        for kind in park_facilities.KINDS
    }
    assert [one.value for one in park_facilities.figures(shares, found).values()] == [2.3] * 3


def test_an_area_with_too_little_covered_has_no_figure_and_none_is_made_of_what_is(
    tmp_path: Path,
):
    found = spine.build(inputs_of(tmp_path, town_of()))
    thin = Worked(None, 1, 4, 0.22, State.BELOW_THRESHOLD)
    shares: dict[str, dict[str, Worked]] = {
        kind: {area: thin for area in AREAS} for kind in park_facilities.KINDS
    }
    assert set(park_facilities.figures(shares, found).values()) == {thin}


def test_an_output_area_with_no_centre_has_no_count_and_none_is_filled_in(tmp_path: Path):
    inputs = inputs_of(tmp_path, town_of(), centres=centres_in_the_middle(left_out=[OAS[5]]))
    found = built(inputs)
    assert OAS[5] not in found.within.kinds
    # 160 of the 660 homes have no count. Of the rest, 320 have 2 kinds and 180 have 4.
    assert found.worked[QUILLHAVEN_2] == Worked(2.7, 3, 4, round(500 / 660, 6), State.PARTIAL)


# The evidence


def test_every_area_has_a_row_that_holds_its_figure(town: Facilities):
    assert [row.fact_id for row in town.rows] == [
        f"{area}/feature/park_facilities" for area in AREAS
    ]
    assert [row.value for row in town.rows] == [2.0, 3.0, 4.0]
    for row in town.rows:
        assert row.derivation_id == "kinds_in_parks_within_1200m@1"
        assert row.retrieved_on == "2026-09-23"
        assert row.data_period is not None
        assert row.data_period.days() == ("2021-03-21", "2026-04-30")


def test_a_row_names_the_file_of_every_square_within_reach(town: Facilities):
    """Every home of the town is within 1,200 metres of all four squares."""
    ids = file_ids(town_of())
    by_source = {receipt.source_id: receipt.file_id for receipt in town.files}
    ground = {by_source[source] for source in (centres.CENTRES, spine.LOOKUP, spine.HOMES)}
    for row in town.rows:
        assert set(row.inputs) == set(ids.values()) | ground


def test_the_evidence_of_the_measure_has_no_loose_end(town: Facilities):
    evidence = Evidence.of("lon-2026-10-02-01", town.files, park_facilities.METHODS, town.rows)
    assert len(evidence.rows) == 3
    assert town.geography is Geography.POINT
    assert park_facilities.METHOD.kind is Kind.MEASURED
    assert park_facilities.METHOD.code == "burro_pipeline.derive.park_facilities"
    assert (park_facilities.METHOD, homes_within_at(1_200)) == park_facilities.METHODS


# The gate and the store


def test_the_gate_is_asked_before_the_sites_are_read(tmp_path: Path):
    sources = [
        source.model_copy(update={"uses": (Use.DISPLAY,)})
        if source.id == park_facilities.SOURCE
        else source
        for source in registry()
    ]
    inputs = inputs_of(tmp_path, town_of(), given=Registry(tuple(sources)))
    found = spine.build(inputs)
    before = inputs.opened
    with pytest.raises(LockError) as stopped:
        park_facilities.build(inputs, found)
    assert stopped.value.rule == "gate_refuses"
    assert inputs.opened == before


def test_every_file_behind_a_figure_is_registered_for_scoring(town: Facilities):
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


def test_no_name_of_a_site_is_read(town: Facilities):
    """Every made-up site carries one name, which is found nowhere else."""
    assert CANARY not in repr(town)


# The name, the unit and the sentences


def test_the_name_says_what_is_counted_while_core_says_a_walk_so_no_build_carries_it(
    town: Facilities,
):
    """Core's words are held here, so that this fails on the day core names it otherwise.

    On the day core says what is counted, take `WAITS_ON` away.
    """
    feature = FEATURES[FeatureId.PARK_FACILITIES]
    assert town.metric.label == (
        "Kinds of play and sports site in parks within 1,200 m in a straight line"
    )
    assert "walk" not in town.metric.label.lower()
    assert feature.label == "Kinds of thing to do in parks within a 15-minute walk"
    assert not says_what_core_says(town.metric)
    assert (
        (town.metric.unit, town.metric.polarity)
        == (feature.unit, feature.polarity)
        == ("count", Polarity.MORE)
    )
    assert town.metric.native_resolution is NativeResolution.POINT
    assert feature.native_resolution is NativeResolution.NETWORK
    assert town.metric.vintage == "2026-04"


def test_the_name_is_all_that_differs_from_what_core_says_of_the_measure(town: Facilities):
    """So a name in core is all that a build waits on to carry it."""
    as_core_names_it = town.metric.model_copy(
        update={"label": FEATURES[FeatureId.PARK_FACILITIES].label}
    )
    assert says_what_core_says(as_core_names_it)


def test_the_measure_is_on_the_list_of_a_build_and_says_what_it_waits_on():
    listed = {measure.feature: measure for measure in measures.MEASURES}
    measure = listed[FeatureId.PARK_FACILITIES]
    assert measure.waits_on == park_facilities.WAITS_ON
    assert measure.in_squares
    assert measure.methods == park_facilities.METHODS
    assert measure.cannot_see == park_facilities.CANNOT_SEE
    assert len(measure.waits_on) == 1
    assert "in a straight line" in measure.waits_on[0] and "15-minute walk" in measure.waits_on[0]


def test_the_sentence_of_the_method_states_every_number_it_turns_on():
    sentence = park_facilities.METHOD.sentence
    assert park_facilities.METHOD.parameters == {
        "metres": 1_200,
        "kinds": 5,
        "inside_in_100": 50,
        "enough_in_100": 50,
    }
    for said in ("of 5 that are counted", "within 1200 metres", "at least 50 in 100 of its land"):
        assert said in sentence
    assert sentence.endswith(".") and sentence.count(". ") == 0


def test_the_definition_is_one_sentence_that_says_what_is_counted():
    definition = park_facilities.definition_of("2026-04")
    assert definition.endswith(".") and not re.search(r"[.!?]\s|\n", definition)
    for words in (
        "the five kinds Bowling Green, Other Sports Facility, Play Space, Playing Field and "
        "Tennis Court",
        "Ordnance Survey",
        "OS Open Greenspace as at 2026-04",
        "at least half of their land inside the outline",
        "a site of any size that it maps as Public Park Or Garden",
        "a way in on foot within 1,200 metres in a straight line",
        "inside London or outside it",
        "the mean over the area's homes at the census of 2021",
        "one decimal place",
        "a kind is counted once",
        "not along any street or path",
        "the walk is longer",
        "a cemetery, a golf course, an allotment and religious grounds are never counted",
    ):
        assert words in definition


def test_the_definition_of_the_measure_is_the_one_a_methods_page_prints(town: Facilities):
    assert town.metric.definition == park_facilities.definition_of("2026-04")


RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|child(ren)?|health|ages?|incomes?)\b",
    re.I,
)


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(town: Facilities):
    sentences = (
        town.metric.label,
        town.metric.definition,
        *park_facilities.CANNOT_SEE,
        *park_facilities.WAITS_ON,
        park_facilities.METHOD.sentence,
    )
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_what_it_cannot_see_is_said_in_two_sentences_with_no_figure_in_them():
    assert len(park_facilities.CANNOT_SEE) == 2
    for sentence in park_facilities.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)
    assert "not how many" in park_facilities.CANNOT_SEE[0]
    assert "not a walk" in park_facilities.CANNOT_SEE[1]


def test_what_it_cannot_see_says_that_a_site_on_a_playing_field_is_not_counted(
    town: Facilities, tmp_path: Path
):
    """A playing field is no park, so a court that stands on one is counted nowhere.

    It is the most that the figure leaves out, so the sentence beside the figure says it.
    """
    on_a_field = (
        *SITES,
        site("idREC", FIELD, 0, 0, 100, 100),
        site("idRECCOURT", COURT, 10, 10, 20, 20),
        site("idRECGREEN", GREEN, 50, 10, 20, 20),
    )
    ways_in = (*WAYS_IN, MadeUpWay("idREC", ON_FOOT, at(0, 50)))
    found = built(inputs_of(tmp_path, town_of(on_a_field, ways_in)))
    assert found.offers.of_park == town.offers.of_park
    assert values_of(found) == values_of(town)
    assert "on a playing field" in park_facilities.CANNOT_SEE[1]
    assert "is not counted" in park_facilities.CANNOT_SEE[1]
