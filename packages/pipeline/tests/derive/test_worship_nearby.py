"""Places of worship nearby, from the file of places to a count of buildings for each area.

Every file here is made up, and says so: `community_support.py` puts the
buildings in the town that `culture_support.py` draws. The centres stand 1,000
metres apart, so that every count can be made by hand.

Three tests hold the measure to what it must never do. It is never turned
into an estimate of who lives somewhere, never added up into a score, and
never offered with a direction of fewer.
"""

import ast
import dataclasses
import re
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, TAGS
from burro_core.ids import Describes, FeatureId, FeatureKind, NativeResolution, Polarity
from burro_pipeline.cells import spine
from burro_pipeline.derive import (
    brands_nearby,
    culture_reach,
    measures,
    places_counted,
    venues_nearby,
    worship_kinds,
    worship_nearby,
)
from burro_pipeline.derive.culture_venues import OF_THE_RELEASE
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.places_counted import Building
from burro_pipeline.derive.worship_kinds import KINDS, NAMED, Kind
from burro_pipeline.derive.worship_nearby import (
    BUILDINGS,
    CANNOT_SEE,
    CANNOT_SEE_OF,
    FILED_TWICE,
    KEY,
    KEY_OF,
    KEYS,
    LABEL,
    LABEL_OF,
    NOUGHT,
    OFFER,
    OFFER_OF,
    ONE_BUILDING,
    WAITS_ON,
    Worship,
    as_places,
)
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence

from ..fetch.parquet_support import Place
from .community_support import (
    ANGLICAN,
    BUDDHIST_TEMPLE,
    CHURCH,
    COMMUNITY_CENTRE,
    GURDWARA,
    HINDU_TEMPLE,
    IN_THE_TOWN,
    MOSQUE,
    OF_A_SCORE,
    OF_FEWER,
    OF_RESIDENTS,
    OF_THOSE_WHO_GO,
    SHRINE,
    SYNAGOGUE,
    WORSHIP,
)
from .culture_support import (
    BY_EVERY_CENTRE,
    CAFE,
    CANARY,
    DAY,
    OAS,
    ONE,
    Q1,
    Q2,
    R2,
    SOURCE,
    T4,
    THREE,
    TWO,
    beside,
    centres_at,
    inputs_of,
    place,
)

OA_Q1, OA_Q2, OA_Q3, OA_Q4 = OAS[:4]
OA_R1, OA_R2, OA_T1, OA_T4 = OAS[4], OAS[5], OAS[8], OAS[11]
SLOT = {kind: KINDS.index(kind) for kind in KINDS}
ALL = range(len(KINDS))


def built(folder: Path, *places: Place, centres: bytes | None = None, **how: object) -> Worship:
    given = places if places else IN_THE_TOWN
    inputs = inputs_of(folder, given, centres, **how)  # pyright: ignore[reportArgumentType]
    return worship_nearby.build(inputs, spine.build(inputs))


@pytest.fixture
def town(tmp_path: Path) -> Worship:
    return built(tmp_path)


def value_of(worked: Worked) -> float:
    assert worked.value is not None
    return worked.value


def shown(found: Worship) -> list[str]:
    """Every word a row that is put forward would show: its name, its wish and its sentence."""
    return [
        text
        for row in found.proposed
        for text in (row.key, row.label, row.short_label, row.unit, row.definition)
    ]


# What is within reach


def test_each_home_is_given_the_buildings_within_reach_of_its_own_centre(town: Worship):
    reach = town.nearby.reach
    assert reach.metres == 800
    assert reach.of(ALL)[OA_Q1] == 4.0
    assert reach.of(ALL)[OA_Q2] == reach.of(ALL)[OA_Q3] == 1.0
    assert reach.of(ALL)[OA_R1] == 1.0 and reach.of(ALL)[OA_T1] == 3.0
    assert reach.of(ALL)[OA_R2] == 0.0


def test_each_building_is_counted_under_its_own_kind(town: Worship):
    within = town.nearby.reach.within
    assert [within[OA_Q1][SLOT[kind]] for kind in KINDS] == [1, 1, 1, 0, 0, 0, 1]
    assert within[OA_Q2][SLOT[Kind.GURDWARA]] == within[OA_Q3][SLOT[Kind.GURDWARA]] == 1
    assert within[OA_T1][SLOT[Kind.MOSQUE]] == 2 and within[OA_T1][SLOT[Kind.CHURCH]] == 1


def test_a_building_790_metres_off_on_the_grid_is_within_reach_and_one_810_off_is_not(
    town: Worship,
):
    within = town.nearby.reach.within[OA_Q4]
    assert within[SLOT[Kind.HINDU_TEMPLE]] == 1 and within[SLOT[Kind.BUDDHIST_TEMPLE]] == 0


def test_the_figure_of_an_area_is_the_mean_over_its_homes(town: Worship):
    assert value_of(town.worked[ONE]) == round((110 * 4 + 120 + 130 + 140) / 500, 1) == 1.7
    assert value_of(town.worked[TWO]) == round(150 / 660, 1) == 0.2
    assert value_of(town.worked[THREE]) == round(190 * 3 / 820, 1) == 0.7
    assert {one.state for one in town.worked.values()} == {State.PRESENT}


def test_each_kind_has_a_figure_of_its_own_for_every_area(town: Worship):
    of = {kind: {area: value_of(one) for area, one in town.of_kind[kind].items()} for kind in NAMED}
    assert of[Kind.CHURCH] == {ONE: 0.2, TWO: 0.2, THREE: 0.2}
    assert of[Kind.MOSQUE] == {ONE: 0.2, TWO: 0.0, THREE: 0.5}
    assert of[Kind.SYNAGOGUE] == {ONE: 0.2, TWO: 0.0, THREE: 0.0}
    assert of[Kind.GURDWARA] == {ONE: 0.5, TWO: 0.0, THREE: 0.0}
    assert of[Kind.HINDU_TEMPLE] == {ONE: 0.3, TWO: 0.0, THREE: 0.0}
    assert of[Kind.BUDDHIST_TEMPLE] == {ONE: 0.0, TWO: 0.0, THREE: 0.0}
    assert set(town.of_kind) == set(NAMED)


# What is counted and what is not


def test_what_is_no_place_of_worship_is_not_counted_and_is_counted_as_left_out(town: Worship):
    held = town.held
    assert held.rows == len(IN_THE_TOWN) == 36
    assert held.rows == len(held.records) + sum(held.left_out.values())
    # The cultural centre stands under the same top as a place of worship, and is left out
    # by its name as the shrine, the monastery and the retreat are.
    assert dict(held.left_out) == {"beside": 4, "closed": 1, "not_worship": 19}
    assert dict(held.left_out_as) == {
        "christian_place_of_worship": 1,
        "cultural_center": 1,
        "monastery": 1,
        "shrine": 1,
        "zen_center": 1,
    }
    assert sum(held.counted_as.values()) == len(held.records) == 12


def test_a_record_of_no_kind_named_counts_toward_the_total_and_toward_no_kind(tmp_path: Path):
    found = built(tmp_path, *BY_EVERY_CENTRE, place(Q1, WORSHIP))
    assert found.nearby.reach.of(ALL)[OA_Q1] == 1.0
    assert value_of(found.worked[ONE]) == round(110 / 500, 1)
    for kind in NAMED:
        assert {one.value for one in found.of_kind[kind].values()} == {0.0}


def test_a_record_of_no_kind_named_beside_a_building_of_a_kind_is_that_building_again(
    tmp_path: Path,
):
    """A mosque, and 10 metres off a record that says no more than a place of worship."""
    found = built(tmp_path, place(Q1, MOSQUE), place(beside(Q1, 10), WORSHIP))
    assert [one.kind for one in found.buildings] == ["mosque"]
    assert found.nearby.reach.of(ALL)[OA_Q1] == 1.0
    assert found.records_of_one_building == {Kind.NO_KIND_NAMED: 1}


def test_a_record_of_no_kind_named_further_off_is_a_building_of_its_own(tmp_path: Path):
    found = built(tmp_path, place(Q1, MOSQUE), place(beside(Q1, 26), WORSHIP))
    assert sorted(one.kind for one in found.buildings) == ["mosque", "no_kind_named"]
    assert found.nearby.reach.of(ALL)[OA_Q1] == 2.0


def test_what_a_record_says_beside_its_category_is_counted_and_adds_to_no_figure(town: Worship):
    """A community centre that also says it is a mosque. It is a community centre."""
    assert town.said_beside == {Kind.MOSQUE: 1}
    assert town.nearby.reach.within[OA_Q1][SLOT[Kind.MOSQUE]] == 1


def test_a_shrine_a_monastery_and_a_retreat_are_not_counted(tmp_path: Path):
    found = built(tmp_path, place(Q1, SHRINE), place(Q2, CAFE))
    assert found.buildings == () and found.nearby.reach.of(ALL)[OA_Q1] == 0.0


def test_a_category_under_a_place_of_worship_that_the_table_does_not_hold_stops_the_build(
    tmp_path: Path,
):
    with pytest.raises(LockError) as stopped:
        built(tmp_path, place(Q1, (*WORSHIP, "zzyzx_parva_place_of_worship")))
    assert stopped.value.rule == "input_is_as_described"
    assert "zzyzx" not in str(stopped.value) and CANARY not in str(stopped.value)


# One building with many records


def test_records_of_one_kind_that_stand_together_are_one_building(tmp_path: Path):
    found = built(
        tmp_path,
        place(Q1, CHURCH),
        place(beside(Q1, 10), CHURCH),
        place(beside(Q1, 0, 20), CHURCH),
        place(beside(Q2, 0), CAFE),
    )
    assert len(found.held.records) == 3 and len(found.buildings) == 1
    assert found.nearby.reach.of(ALL)[OA_Q1] == 1.0
    assert found.records_of_one_building == {Kind.CHURCH: 2}


def test_five_records_of_one_building_count_once(tmp_path: Path):
    """On one spot, within 12 metres of each other, and under five of the publisher's
    categories: a church, a church of a denomination, a place of worship of no kind named, a
    hall that also says it is a church, and a shrine."""
    on_one_spot = built(tmp_path / "a", *BY_EVERY_CENTRE, *(place(Q1, CHURCH) for _ in range(5)))
    round_it = ((0, 0), (12, 0), (-12, 0), (0, 12), (0, -12))
    near = built(
        tmp_path / "b",
        *BY_EVERY_CENTRE,
        *(place(beside(Q1, east, north), CHURCH) for east, north in round_it),
    )
    said_five_ways = built(
        tmp_path / "c",
        *BY_EVERY_CENTRE,
        place(Q1, CHURCH),
        place(beside(Q1, 5), ANGLICAN),
        place(beside(Q1, -5), WORSHIP),
        place(beside(Q1, 0, 5), COMMUNITY_CENTRE, alternates=("christian_place_of_worship",)),
        place(beside(Q1, 0, -5), SHRINE),
    )
    for found in (on_one_spot, near, said_five_ways):
        assert [one.kind for one in found.buildings] == ["church"]
        assert found.nearby.reach.of(ALL)[OA_Q1] == 1.0
        assert found.close_together == {}


def test_records_of_one_building_that_stand_apart_count_again_and_are_counted_as_close(
    tmp_path: Path,
):
    """Five records, each within 20 metres of the middle of one building. Those at its ends
    stand 40 metres apart, so they are not one building by the rule, and the count is four.
    The measure says so beside the figure, and counts such buildings so a person can look."""
    round_it = ((0, 0), (20, 0), (-20, 0), (0, 20), (0, -20))
    found = built(
        tmp_path,
        *BY_EVERY_CENTRE,
        *(place(beside(Q1, east, north), CHURCH) for east, north in round_it),
    )
    assert len(found.buildings) == 4 and found.nearby.reach.of(ALL)[OA_Q1] == 4.0
    assert found.close_together == {Kind.CHURCH: 4}
    assert "counts more than once" in ONE_BUILDING and ONE_BUILDING in CANNOT_SEE
    assert any("50 metres" in said and "real file" in said for said in WAITS_ON)


def test_buildings_of_two_kinds_on_one_spot_are_two_buildings(tmp_path: Path):
    found = built(tmp_path, place(Q1, CHURCH), place(Q1, MOSQUE))
    assert len(found.buildings) == 2 and found.nearby.reach.of(ALL)[OA_Q1] == 2.0


def test_one_building_filed_under_two_kinds_counts_under_each_and_the_words_say_so(
    tmp_path: Path,
):
    found = built(tmp_path, place(Q1, HINDU_TEMPLE), place(beside(Q1, 3), BUDDHIST_TEMPLE))
    assert found.nearby.reach.of(ALL)[OA_Q1] == 2.0
    assert FILED_TWICE in CANNOT_SEE and "twice" in FILED_TWICE
    assert all(FILED_TWICE in lines for lines in CANNOT_SEE_OF.values())


def test_which_records_are_one_building_does_not_turn_on_the_order_of_the_file(tmp_path: Path):
    row = [place(beside(Q1, 20.0 * n), SYNAGOGUE) for n in range(10)]
    one = built(tmp_path / "a", *row)
    other = built(tmp_path / "b", *reversed(row))
    assert one.buildings == other.buildings and len(one.buildings) == 5


def test_as_places_is_handed_records_and_reads_no_file():
    assert as_places(()) == ((), {})
    here = (2.5, 53.5)
    records = [Building(*here, "mosque", ("meta",), 0.9), Building(*here, "mosque", ("x",), None)]
    (building,), again = as_places(records)
    assert building.datasets == ("meta", "x") and again == {Kind.MOSQUE: 1}


# When nought is a count, and the edge of London


def test_nought_is_a_count_where_the_file_holds_something_within_reach(tmp_path: Path):
    found = built(tmp_path, place(Q1, CHURCH), place(R2, CAFE))
    assert found.nearby.reach.of(ALL)[OA_R2] == 0.0
    assert OA_R2 not in found.nearby.nothing_seen


def test_where_the_file_holds_nothing_at_all_within_reach_nothing_is_known(tmp_path: Path):
    found = built(tmp_path, place(Q1, CHURCH))
    assert found.nearby.counted is not None
    assert OA_R2 in found.nearby.nothing_seen and OA_R2 not in found.nearby.counted
    assert found.worked[TWO].value is None
    assert found.of_kind[Kind.MOSQUE][TWO].value is None


def test_an_output_area_with_homes_outside_london_within_reach_has_no_count(tmp_path: Path):
    found = built(tmp_path, centres=centres_at(outside=beside(Q1, 500)))
    assert OA_Q1 in found.nearby.reach.near_the_edge
    assert found.worked[ONE].state is State.PARTIAL


# Never an estimate of who lives there


def test_a_count_of_buildings_is_never_turned_into_an_estimate_of_who_lives_there(
    town: Worship, tmp_path: Path
):
    """A figure is a count of buildings. It is no share, no rate and no figure for each so
    many homes, no file about who lives anywhere is opened for it, and no word of it says
    who lives or who goes anywhere."""
    assert {row.unit for row in town.proposed} == {"count"} == {places_counted.UNIT}
    assert {row.describes for row in town.proposed} == {Describes.BUILDINGS}
    # The files: the places, the centres, the lookup, and the homes that weigh a mean.
    assert sorted(receipt.source_id for receipt in town.files) == [
        "ons-census-2021-housing-tables",
        "ons-oa-pwc-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        SOURCE,
    ]
    # How many homes stand somewhere changes no count of what is within reach of one of them:
    # three mosques by the centre with the fewest homes and by the one with the most.
    three = [place(beside(at, east), MOSQUE) for at in (Q1, T4) for east in (100, 200, 300)]
    same = built(tmp_path, *three).nearby.reach.within
    assert same[OA_Q1][SLOT[Kind.MOSQUE]] == same[OA_T4][SLOT[Kind.MOSQUE]] == 3
    # What is handed back holds no count of homes, so no count can be set over one.
    assert not hasattr(town.nearby.reach, "homes")
    with pytest.raises(AttributeError):
        culture_reach.rates(town.nearby.reach.of((SLOT[Kind.MOSQUE],)), town.nearby.reach, None)  # pyright: ignore[reportArgumentType]
    # No word that is shown says who lives somewhere or who goes to a building.
    for said in (*shown(town), *CANNOT_SEE, *WAITS_ON, LABEL, OFFER):
        readable = said.replace("_", " ")
        assert not OF_RESIDENTS.search(readable), said
        assert not OF_THOSE_WHO_GO.search(readable), said
    # And the first line beside every figure says what it is.
    assert BUILDINGS == "It counts buildings and says nothing of who lives near them."
    assert CANNOT_SEE[0] == BUILDINGS
    assert all(lines[0] == BUILDINGS for lines in CANNOT_SEE_OF.values())


def test_the_modules_of_the_measure_divide_no_count_and_read_no_table_of_who_lives_anywhere():
    """No count is divided by anything here: the one mean is `culture_reach.py`'s, over homes."""
    for module in (worship_nearby, worship_kinds, places_counted):
        tree = ast.parse(Path(str(module.__file__)).read_text(encoding="utf-8"))
        divided = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div | ast.FloorDiv)
        ]
        assert divided == [], module.__name__
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        assert not {"rates", "for_each_at", "lsoa_ratio_by_homes"} & names, module.__name__
        text = Path(str(module.__file__)).read_text(encoding="utf-8")
        assert "ons-census-2021-religion" not in text and "TS030" not in text


# Never a score


def test_the_counts_are_never_added_up_into_a_score_of_how_much_of_anything_an_area_has(
    town: Worship,
):
    """One figure for each kind, and the plain number of places of worship. Nothing else:
    no kind is weighed, none is set against another, and no vibe may hold a figure."""
    assert [row.key for row in town.proposed] == list(KEYS) == [KEY, *KEY_OF.values()]
    assert len(KEYS) == len(set(KEYS)) == 1 + len(NAMED)
    # The one sum is of buildings, each counted once, with every kind weighing the same.
    within = town.nearby.reach.within
    assert town.nearby.counted is not None
    for oa, count in town.nearby.counted.items():
        assert count == float(sum(within[oa][slot] for slot in ALL))
    # No figure, no field and no id says a score, a share or a mix.
    fields = {field.name for field in dataclasses.fields(Worship)}
    for name in (*fields, *KEYS):
        assert not any(word in name for word in OF_A_SCORE), name
    assert "kinds" not in " ".join(KEYS)
    # No figure is how many kinds are within reach: that would say how mixed a place is.
    assert not any(
        isinstance(node, ast.Attribute) and node.attr == "how_many_of"
        for module in (worship_nearby, places_counted)
        for node in ast.walk(ast.parse(Path(str(module.__file__)).read_text(encoding="utf-8")))
    )
    # And what is handed back cannot be asked for it.
    assert not hasattr(town.nearby.reach, "how_many_of")
    assert not isinstance(town.nearby.reach, culture_reach.Reach)
    # Every row is weighed on request only, which core lets into no recipe of a vibe.
    assert {row.kind for row in town.proposed} == {FeatureKind.ON_REQUEST}
    assert not any(row.in_a_vibe or row.in_likeness for row in town.proposed)
    assert not any(row.rankable for row in town.proposed)


def test_no_vibe_of_the_catalogue_holds_a_place_of_worship():
    parts = {str(term.feature_id) for tag in TAGS.values() for term in tag.terms}
    assert not parts & set(KEYS)
    assert not any("worship" in part for part in parts)


# Never a direction of fewer


def test_a_count_is_never_offered_with_a_direction_of_fewer(town: Worship):
    """The one wish a figure answers is for a building nearby. More is its one direction."""
    assert {row.polarity for row in town.proposed} == {Polarity.MORE}
    assert Polarity.EITHER not in {row.polarity for row in town.proposed}
    assert [row.short_label for row in town.proposed] == [
        "A place of worship nearby",
        "A church nearby",
        "A mosque nearby",
        "A synagogue nearby",
        "A Hindu temple nearby",
        "A gurdwara nearby",
        "A Buddhist temple nearby",
    ]
    for said in (OFFER, *OFFER_OF.values(), LABEL, *LABEL_OF.values()):
        assert not OF_FEWER.search(said), said
        assert said.endswith(("nearby", "in a straight line"))
    # No offer stands in the module under another name.
    offers = {name for name in vars(worship_nearby) if name.startswith("OFFER")}
    assert offers == {"OFFER", "OFFER_OF"}


# The evidence


def test_every_area_has_a_row_for_each_figure_that_holds_the_figure(town: Worship):
    every = [(town.rows, town.worked, KEY)]
    every += [(town.rows_of_kind[kind], town.of_kind[kind], KEY_OF[kind]) for kind in NAMED]
    for rows, worked, key in every:
        assert [row.fact_id for row in rows] == [f"{area}/feature/{key}" for area in sorted(worked)]
        for row in rows:
            area = row.fact_id.split("/")[0]
            assert row.value == worked[area].value and row.state is worked[area].state
            assert row.derivation_id == "places_within_800m_at_homes@1"


def test_the_rows_are_ones_the_evidence_of_a_release_would_hold(town: Worship):
    rows = (*town.rows, *(row for kind in NAMED for row in town.rows_of_kind[kind]))
    evidence = Evidence.of("lon-2026-10-02-01", town.files, (worship_nearby.METHOD,), rows)
    assert len(evidence.rows) == 3 * 7


def test_the_period_of_a_figure_runs_from_the_census_to_the_release(town: Worship):
    (row, *_) = town.rows
    assert row.data_period is not None
    assert row.data_period.days() == ("2021-03-21", DAY)


def test_the_places_are_keyed_by_a_point(town: Worship):
    assert town.geography is Geography.POINT


# The name, the unit and the sentences


def test_core_holds_no_feature_for_a_place_of_worship_and_no_build_carries_one():
    assert not worship_nearby.core_holds_it()
    assert not any("worship" in feature.value for feature in FeatureId)
    assert not any("worship" in one.label.lower() for one in FEATURES.values())
    # A build reads the file of places for the cultural venues, for the cafes, the gyms and
    # the pubs and bars, for the nearest food shop and for the chains of grocers, gyms and
    # coffee, and for nothing else.
    of_the_file = {one.feature for one in measures.MEASURES if one.source == SOURCE}
    assert of_the_file == {
        FeatureId.CULTURE_VENUES,
        FeatureId.CULTURE_VENUES_PER_HOMES,
        FeatureId.EVENING_CLUSTER_EXPOSURE,
        FeatureId.GROCERY_WALK,
        *venues_nearby.MEASURES,
        *brands_nearby.FEATURES,
    }


def test_the_rows_the_catalogue_needs_say_what_is_measured(town: Worship):
    total, church, *_ = town.proposed
    assert total.label == "Places of worship within 800 m of home, in a straight line"
    assert church.label == "Churches within 800 m of home, in a straight line"
    assert [row.label for row in town.proposed[1:]] == [LABEL_OF[kind] for kind in NAMED]
    for row in town.proposed:
        assert row.native_resolution is NativeResolution.POINT
        assert row.source_ids == tuple(sorted({receipt.source_id for receipt in town.files}))
        assert row.vintage == DAY


def test_the_sentence_of_a_methods_page_says_what_is_counted_and_what_is_not(town: Worship):
    total, church, mosque, *_ = (row.definition for row in town.proposed)
    for said in (row.definition for row in town.proposed):
        assert said.endswith(".") and "!" not in said and "\n" not in said
        assert "Overture Maps Foundation" in said and DAY in said
        assert "800 metres in a straight line" in said and "within 25 metres" in said
        assert "a count of buildings and of nothing else" in said
        assert "walk" not in said
    assert "The number of places of worship" in total and "a place of worship" in total
    assert "The number of churches" in church and "a Christian place of worship" in church
    assert "The number of mosques" in mosque and "a Muslim place of worship" in mosque


def test_what_the_figure_cannot_see_is_said_in_whole_sentences():
    for lines in (CANNOT_SEE, *CANNOT_SEE_OF.values(), WAITS_ON):
        assert len(lines) == len(set(lines)) >= 3
        for said in lines:
            assert re.fullmatch(r"[A-Z][^!\n|]+\.", said), said
    joined = " ".join(CANNOT_SEE)
    for must in ("closed", "straight line", "category", "25 metres", "census", "a hall"):
        assert must in joined
    assert any("chapel" in said for said in CANNOT_SEE_OF[Kind.CHURCH])
    assert not any("chapel" in said for said in CANNOT_SEE_OF[Kind.MOSQUE])


def test_the_words_say_that_a_group_that_meets_in_a_hall_or_a_house_is_not_counted():
    assert any("a hall" in said and "a house" in said for said in CANNOT_SEE)
    assert any("as fully" in said for said in CANNOT_SEE)


def test_nought_is_said_of_a_building_and_is_never_read_as_there_being_none():
    """The words are the measure's own: a place of worship is no venue."""
    assert NOUGHT in CANNOT_SEE and all(NOUGHT in lines for lines in CANNOT_SEE_OF.values())
    assert "not the same as there being none" in NOUGHT
    for lines in (CANNOT_SEE, *CANNOT_SEE_OF.values(), WAITS_ON):
        assert not any(re.search(r"\bvenues?\b", said) for said in lines)


# The files


def test_the_gate_is_asked_of_the_places_and_of_the_centres(tmp_path: Path):
    inputs = inputs_of(tmp_path, IN_THE_TOWN)
    found = spine.build(inputs)
    before = {opened.receipt.source_id for opened in inputs.opened}
    worship_nearby.build(inputs, found)
    after = {opened.receipt.source_id for opened in inputs.opened}
    assert after - before == {SOURCE, "ons-oa-pwc-2021"}


def test_with_no_file_of_places_there_is_no_figure_and_nothing_is_filled_in(tmp_path: Path):
    inputs = inputs_of(tmp_path, None)
    with pytest.raises(LockError) as stopped:
        worship_nearby.build(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_has_one_receipt"


def test_the_spine_must_be_made_from_files_of_this_build(tmp_path: Path):
    other = spine.build(inputs_of(tmp_path / "other", IN_THE_TOWN))
    changed = inputs_of(tmp_path / "this", IN_THE_TOWN)
    changed.receipts = [
        receipt for receipt in changed.receipts if "lookup" not in receipt.source_id
    ]
    with pytest.raises(ValueError, match="files of this build"):
        worship_nearby.build(changed, other)


def test_the_words_beside_every_figure_say_that_the_day_is_of_the_release():
    """The file states no period. The founder stated the day of the publisher's release, with
    a note that many records are years older, and a figure is never shown without the note."""
    for lines in (CANNOT_SEE, *CANNOT_SEE_OF.values()):
        assert OF_THE_RELEASE in lines


def test_nothing_the_measure_gives_back_holds_a_name_of_a_place(tmp_path: Path):
    found = built(tmp_path, packed="none")
    assert CANARY not in repr(found)


def test_built_twice_from_the_same_file_the_figures_and_the_rows_are_the_same(tmp_path: Path):
    one, other = built(tmp_path / "a"), built(tmp_path / "b")
    assert (one.worked, one.of_kind) == (other.worked, other.of_kind)
    assert (one.rows, one.rows_of_kind) == (other.rows, other.rows_of_kind)


def test_the_order_of_the_rows_of_a_file_changes_no_figure(tmp_path: Path):
    one, other = built(tmp_path / "a"), built(tmp_path / "b", *reversed(IN_THE_TOWN))
    assert (one.worked, one.of_kind) == (other.worked, other.of_kind)
    assert one.buildings == other.buildings
    assert one.held.file.file_id != other.held.file.file_id


def test_a_community_centre_beside_a_gurdwara_is_no_place_of_worship(tmp_path: Path):
    found = built(tmp_path, place(Q1, GURDWARA), place(Q1, COMMUNITY_CENTRE))
    assert [one.kind for one in found.buildings] == ["gurdwara"]
