"""Community centres and cultural centres nearby, from the file of places to a count for each area.

Every file here is made up, and says so: `community_support.py` puts the
buildings in the town that `culture_support.py` draws. Two community centres
and a cultural centre stand beside Q1, and a community centre beside T1. A
civic centre, a social club and a youth organisation stand beside Q1 and are
not counted.
"""

import dataclasses
import inspect
import re
from pathlib import Path

import pytest
from burro_core.catalogue import TAGS
from burro_core.ids import Describes, FeatureId, FeatureKind, Polarity
from burro_pipeline.cells import spine
from burro_pipeline.derive import brands_nearby, centres_nearby, measures, venues_nearby
from burro_pipeline.derive.centres_nearby import (
    BESIDE_A_CENTRE,
    CANNOT_SEE,
    CANNOT_SEE_OF,
    ELSEWHERE,
    IS,
    IS_NOT,
    KEY_OF,
    KEYS,
    KINDS,
    LABEL_OF,
    OFFER_OF,
    PARENTS,
    TOP,
    WAITS_ON,
    WHOSE,
    Centres,
    Kind,
    LeftOut,
    kind_of,
)
from burro_pipeline.derive.culture_kinds import NotOnTheTable
from burro_pipeline.derive.culture_venues import OF_THE_RELEASE
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.row import State

from ..fetch.parquet_support import Place
from .community_support import (
    CIVIC_CENTRE,
    COMMUNITY_CENTRE,
    CULTURAL_CENTRE,
    IN_THE_TOWN,
    MOSQUE,
    OF_A_SCORE,
    OF_FEWER,
    OF_RESIDENTS,
    OF_THOSE_WHO_GO,
    SOCIAL_CLUB,
    YOUTH,
)
from .culture_support import (
    BY_EVERY_CENTRE,
    CANARY,
    DAY,
    OAS,
    ONE,
    Q1,
    SOURCE,
    THREE,
    TWO,
    beside,
    inputs_of,
    place,
)

OA_Q1, OA_T1 = OAS[0], OAS[8]
COMMUNITY, CULTURAL = (KINDS.index(kind) for kind in KINDS)


def built(folder: Path, *places: Place, **how: object) -> Centres:
    given = places if places else IN_THE_TOWN
    inputs = inputs_of(folder, given, **how)  # pyright: ignore[reportArgumentType]
    return centres_nearby.build(inputs, spine.build(inputs))


@pytest.fixture
def town(tmp_path: Path) -> Centres:
    return built(tmp_path)


def value_of(worked: Worked) -> float:
    assert worked.value is not None
    return worked.value


# The table


def test_two_kinds_of_centre_are_counted_each_by_a_category_of_its_own():
    assert [kind.value for kind in KINDS] == ["community_centre", "cultural_centre"]
    assert IS == {
        "community_center": Kind.COMMUNITY_CENTRE,
        "cultural_center": Kind.CULTURAL_CENTRE,
    }
    assert not set(IS) & set(IS_NOT)


@pytest.mark.parametrize(
    ("hierarchy", "found"),
    [
        (COMMUNITY_CENTRE, Kind.COMMUNITY_CENTRE),
        (CULTURAL_CENTRE, Kind.CULTURAL_CENTRE),
        (CIVIC_CENTRE, LeftOut.BESIDE),
        (SOCIAL_CLUB, LeftOut.BESIDE),
        (YOUTH, LeftOut.BESIDE),
        (MOSQUE, LeftOut.NOT_A_CENTRE),
        (("food_and_drink", "cafe"), LeftOut.NOT_A_CENTRE),
        (COMMUNITY_CENTRE[:2], LeftOut.PARENT_ALONE),
        (COMMUNITY_CENTRE[:1], LeftOut.PARENT_ALONE),
        ((*COMMUNITY_CENTRE[:2], "scout_hall"), LeftOut.BESIDE),
        ((TOP, "government_office", "town_hall"), LeftOut.BESIDE),
        ((TOP, "civic_organization", "charity_organization"), LeftOut.BESIDE),
    ],
)
def test_the_most_particular_category_of_a_record_decides(
    hierarchy: tuple[str, ...], found: Kind | LeftOut
):
    assert kind_of(hierarchy[-1], hierarchy) is found


def test_every_category_that_is_left_out_by_its_name_says_why_in_plain_words():
    assert IS_NOT == {**BESIDE_A_CENTRE, **ELSEWHERE}
    assert not set(BESIDE_A_CENTRE) & set(ELSEWHERE) and not set(IS_NOT) & (set(IS) | PARENTS)
    for category, why in IS_NOT.items():
        assert re.fullmatch(r"[a-z][a-z0-9_]*", category), category
        assert why and why[0].islower() and not why.endswith(".") and "!" not in why


def test_a_new_category_anywhere_under_the_top_of_the_branch_stops_the_build():
    """Not under a centre alone: a hall that the publisher files elsewhere in the branch
    would else be counted nowhere, and nothing would say so."""
    for under in ((TOP,), COMMUNITY_CENTRE[:2], (TOP, "zzyzx_parva_service")):
        with pytest.raises(NotOnTheTable):
            kind_of("zzyzx_parva_hall", (*under, "zzyzx_parva_hall"))


def test_a_record_with_no_category_is_no_centre():
    assert kind_of(None, ()) is LeftOut.NO_CATEGORY and kind_of("", ()) is LeftOut.NO_CATEGORY


def test_a_category_under_a_centre_that_the_table_does_not_hold_stops_the_build(tmp_path: Path):
    with pytest.raises(NotOnTheTable):
        kind_of("zzyzx_parva_center", (*CULTURAL_CENTRE, "zzyzx_parva_center"))
    with pytest.raises(LockError) as stopped:
        built(tmp_path, place(Q1, (*COMMUNITY_CENTRE, "zzyzx_parva_center")))
    assert stopped.value.rule == "input_is_as_described" and "zzyzx" not in str(stopped.value)


def test_nothing_of_a_name_is_handed_to_the_rule():
    """So a cultural centre is never counted as the centre of any one community."""
    assert list(inspect.signature(kind_of).parameters) == ["primary", "hierarchy"]
    assert WHOSE in CANNOT_SEE_OF[Kind.CULTURAL_CENTRE]
    assert WHOSE not in CANNOT_SEE_OF[Kind.COMMUNITY_CENTRE]


# The figures


def test_each_home_is_given_the_centres_within_reach_of_its_own_centre(town: Centres):
    within = town.nearby.reach.within
    assert within[OA_Q1][:2] == (2, 1) and within[OA_T1][:2] == (1, 0)


def test_the_figure_of_an_area_is_the_mean_over_its_homes(town: Centres):
    community, cultural = (town.of_kind[kind] for kind in KINDS)
    assert value_of(community[ONE]) == round(110 * 2 / 500, 1) == 0.4
    assert value_of(community[TWO]) == 0.0
    assert value_of(community[THREE]) == round(190 / 820, 1) == 0.2
    assert [value_of(cultural[area]) for area in (ONE, TWO, THREE)] == [0.2, 0.0, 0.0]
    assert {one.state for one in community.values()} == {State.PRESENT}


def test_what_stands_beside_a_centre_is_not_counted_and_is_counted_as_left_out(town: Centres):
    held = town.held
    assert held.rows == len(held.records) + sum(held.left_out.values()) == 36
    assert dict(held.left_out) == {"beside": 3, "not_a_centre": 29}
    assert dict(held.left_out_as) == {
        "civic_center": 1,
        "social_club": 1,
        "youth_organization": 1,
    }
    assert dict(held.counted_as) == {"community_center": 3, "cultural_center": 1}


def test_a_community_centre_and_a_cultural_centre_on_one_spot_are_two_buildings(
    tmp_path: Path,
):
    found = built(
        tmp_path, *BY_EVERY_CENTRE, place(Q1, COMMUNITY_CENTRE), place(Q1, CULTURAL_CENTRE)
    )
    assert len(found.buildings) == 2


def test_records_of_one_centre_that_stand_together_are_one_building(tmp_path: Path):
    records = [place(beside(Q1, east), COMMUNITY_CENTRE) for east in (0.0, 10.0, 20.0)]
    found = built(tmp_path, *BY_EVERY_CENTRE, *records)
    assert len(found.buildings) == 1
    assert found.records_of_one_building == {Kind.COMMUNITY_CENTRE: 2}


# What the measure never does


def test_a_count_of_centres_is_never_an_estimate_of_who_lives_there(town: Centres):
    assert {row.unit for row in town.proposed} == {"count"}
    assert {row.describes for row in town.proposed} == {Describes.BUILDINGS}
    shown = [
        text
        for row in town.proposed
        for text in (row.key, row.label, row.short_label, row.definition)
    ]
    for said in (*shown, *CANNOT_SEE, WHOSE, *WAITS_ON):
        # The name of the building holds the word, and says nothing of who lives anywhere.
        readable = said.replace("_", " ")
        rest = re.sub(r"\bcommunity (?:centres?|hall)\b", "", readable, flags=re.IGNORECASE)
        assert not OF_RESIDENTS.search(rest) and not OF_THOSE_WHO_GO.search(rest), said
    assert CANNOT_SEE[0] == "It counts buildings and says nothing of who lives near them."


def test_the_two_counts_are_never_added_up_and_never_a_score(town: Centres):
    assert [row.key for row in town.proposed] == list(KEYS) == list(KEY_OF.values())
    fields = {field.name for field in dataclasses.fields(Centres)}
    assert "worked" not in fields and "of_all" not in fields
    # Nor does what stands behind the figures hold the two as one.
    assert town.nearby.of_all is None and town.nearby.counted is None
    assert not hasattr(town.nearby.reach, "homes")
    assert not hasattr(town.nearby.reach, "how_many_of")
    for name in (*fields, *KEYS):
        assert not any(word in name for word in OF_A_SCORE), name
    assert not any(row.in_likeness or row.rankable for row in town.proposed)


def test_a_cultural_centre_is_weighed_on_request_only_and_is_in_no_vibe(town: Centres):
    community, cultural = town.proposed
    assert (cultural.kind, cultural.in_a_vibe) == (FeatureKind.ON_REQUEST, False)
    assert (community.kind, community.in_a_vibe) == (FeatureKind.AMENITY, True)
    parts = {str(term.feature_id) for tag in TAGS.values() for term in tag.terms}
    assert not parts & set(KEYS)


def test_a_count_of_centres_is_never_offered_with_a_direction_of_fewer(town: Centres):
    assert {row.polarity for row in town.proposed} == {Polarity.MORE}
    assert [row.short_label for row in town.proposed] == [
        "A community centre nearby",
        "A cultural centre nearby",
    ]
    for said in (*OFFER_OF.values(), *LABEL_OF.values()):
        assert not OF_FEWER.search(said), said


# The evidence, and the files


def test_every_area_has_a_row_for_each_figure_that_holds_the_figure(town: Centres):
    for kind in KINDS:
        rows, worked = town.rows_of_kind[kind], town.of_kind[kind]
        assert [row.fact_id for row in rows] == [
            f"{area}/feature/{KEY_OF[kind]}" for area in sorted(worked)
        ]
        assert all(row.value == worked[row.fact_id.split("/")[0]].value for row in rows)


def test_core_holds_no_feature_for_a_centre_and_no_build_carries_one():
    assert not centres_nearby.core_holds_it()
    assert not set(KEYS) & {feature.value for feature in FeatureId}
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


def test_the_sentence_of_a_methods_page_says_what_is_counted(town: Centres):
    community, cultural = (row.definition for row in town.proposed)
    for said in (community, cultural):
        assert said.endswith(".") and "!" not in said and "\n" not in said
        assert "Overture Maps Foundation" in said and DAY in said
        assert "800 metres in a straight line" in said and "within 25 metres" in said
    assert "The number of community centres" in community
    assert "The number of cultural centres" in cultural


def test_what_the_figure_cannot_see_is_said_in_whole_sentences():
    for lines in (*CANNOT_SEE_OF.values(), WAITS_ON):
        assert len(lines) == len(set(lines)) >= 3
        for said in lines:
            assert re.fullmatch(r"[A-Z][^!\n|]+\.", said), said
            assert not re.search(r"\bvenues?\b", said), said


def test_records_of_one_centre_that_stand_apart_are_counted_as_close(tmp_path: Path):
    records = [place(beside(Q1, east), COMMUNITY_CENTRE) for east in (0.0, 40.0)]
    found = built(tmp_path, *BY_EVERY_CENTRE, *records)
    assert len(found.buildings) == 2
    assert found.close_together == {Kind.COMMUNITY_CENTRE: 2}


def test_the_words_beside_every_figure_say_that_the_day_is_of_the_release():
    """The file states no period. The founder stated the day of the publisher's release, with
    a note that many records are years older, and a figure is never shown without the note."""
    for lines in (CANNOT_SEE, *CANNOT_SEE_OF.values()):
        assert OF_THE_RELEASE in lines


def test_nothing_the_measure_gives_back_holds_a_name_of_a_place(tmp_path: Path):
    assert CANARY not in repr(built(tmp_path, packed="none"))


def test_the_order_of_the_rows_of_a_file_changes_no_figure(tmp_path: Path):
    one, other = built(tmp_path / "a"), built(tmp_path / "b", *reversed(IN_THE_TOWN))
    assert one.of_kind == other.of_kind and one.buildings == other.buildings
