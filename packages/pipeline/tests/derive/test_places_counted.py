"""What two measures of buildings share: the file read by a table, and the count within reach.

Every file here is made up, and says so: `community_support.py` puts the
buildings in the town that `culture_support.py` draws. The table of these
tests is a small one of its own, so that what is held is the code that is
shared and no table of a measure.
"""

import ast
from enum import StrEnum
from pathlib import Path

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.derive import culture_file, culture_reach, places_counted
from burro_pipeline.derive.culture_file import Record
from burro_pipeline.derive.culture_kinds import NotOnTheTable
from burro_pipeline.derive.culture_reach import ground_of
from burro_pipeline.derive.culture_venues import ONE_VENUE
from burro_pipeline.derive.places_counted import (
    CLOSE,
    METHOD,
    UNIT,
    Building,
    Held,
    as_buildings,
    close_together,
    held_against_the_centre,
    nearby,
)
from burro_pipeline.evidence.lock import LockError

from ..fetch.parquet_support import Place
from .community_support import CHURCH, IN_THE_TOWN, MOSQUE
from .culture_support import (
    CAFE,
    DAY,
    EDITION,
    OAS,
    ONE,
    Q1,
    Q2,
    SHOP,
    THREE,
    TWO,
    beside,
    inputs_of,
    place,
)


class Kind(StrEnum):
    CHURCH = "church"
    MOSQUE = "mosque"


class LeftOut(StrEnum):
    NOTHING_OF_THE_TABLE = "nothing_of_the_table"
    NAMED_AND_LEFT_OUT = "named_and_left_out"


KINDS = tuple(Kind)


def decide(record: Record) -> Kind | LeftOut:
    if record.primary == "christian_place_of_worship":
        return Kind.CHURCH
    if record.primary == "muslim_place_of_worship":
        return Kind.MOSQUE
    if record.primary == "cafe":
        return LeftOut.NAMED_AND_LEFT_OUT
    if record.primary == "zzyzx_parva":
        raise NotOnTheTable
    return LeftOut.NOTHING_OF_THE_TABLE


def read(folder: Path, *places: Place, **how: object) -> Held:
    inputs = inputs_of(folder, places or IN_THE_TOWN, **how)  # pyright: ignore[reportArgumentType]
    opened = culture_file.opened_of(inputs)
    return places_counted.read(opened, decide, KINDS, (LeftOut.NOTHING_OF_THE_TABLE,))


# The file, read by a table


def test_a_record_is_counted_under_the_kind_its_table_gives_it(tmp_path: Path):
    held = read(tmp_path, place(Q1, CHURCH), place(Q2, MOSQUE), place(Q2, SHOP))
    assert [one.kind for one in held.records] == ["church", "mosque"]
    assert held.by_kind == {"church": 1, "mosque": 1}
    assert (held.rows, len(held.every)) == (3, 3)
    assert (held.file.edition, held.as_at) == (EDITION, DAY)


def test_what_is_left_out_is_counted_by_the_reason_and_by_the_category(tmp_path: Path):
    held = read(
        tmp_path,
        place(Q1, CHURCH),
        place(Q1, CHURCH, status="permanently_closed"),
        place(Q1, MOSQUE, status="temporarily_closed"),
        place(Q1, CAFE),
        place(Q1, SHOP),
    )
    assert dict(held.left_out) == {
        "closed": 1,
        "named_and_left_out": 1,
        "nothing_of_the_table": 1,
    }
    assert dict(held.left_out_as) == {"cafe": 1, "christian_place_of_worship": 1}
    assert dict(held.counted_as) == {
        "christian_place_of_worship": 1,
        "muslim_place_of_worship": 1,
    }


def test_a_category_that_a_table_should_hold_and_does_not_stops_the_build(tmp_path: Path):
    with pytest.raises(LockError) as stopped:
        read(tmp_path, place(Q1, ("cultural_and_historic", "zzyzx_parva")))
    assert stopped.value.rule == "input_is_as_described"
    assert "zzyzx" not in str(stopped.value)


def test_which_source_gave_each_record_is_kept(tmp_path: Path):
    held = read(
        tmp_path, place(Q1, CHURCH, dataset="Foursquare"), place(Q2, MOSQUE, dataset="meta")
    )
    assert held.by_dataset == {"Foursquare": 1, "meta": 1}


# One building with many records


def test_records_of_one_kind_within_25_metres_of_the_first_are_one_building():
    assert ONE_VENUE == 25
    here = (2.5, 53.5)
    records = [
        Building(*here, "church", ("meta",), 0.9),
        Building(*here, "church", ("Foursquare",), None),
        Building(*here, "mosque", ("meta",), 0.9),
    ]
    buildings, again = as_buildings(records, ["church", "mosque"])
    assert [(one.kind, one.datasets) for one in buildings] == [
        ("church", ("Foursquare", "meta")),
        ("mosque", ("meta",)),
    ]
    assert again == {"church": 1}
    assert as_buildings(list(reversed(records)), ["church", "mosque"]) == (buildings, again)


def test_a_kind_that_is_not_asked_for_is_not_made_into_a_building():
    records = [Building(2.5, 53.5, "church", ("meta",), 0.9)]
    assert as_buildings(records, ["mosque"]) == ((), {})


def test_buildings_that_stand_close_to_another_of_their_kind_are_counted_for_a_person_to_look():
    """Records are one building within 25 metres of the most westerly of them. A record of
    the same building that stands further from it is a building again, and is counted here."""
    assert CLOSE == 2 * ONE_VENUE == 50
    a_degree_north = culture_reach.metres_to_a_degree(53.5)[1]
    here = (2.5, 53.5)
    near = (2.5, 53.5 + 40 / a_degree_north)
    far = (2.5, 53.5 + 400 / a_degree_north)
    buildings = [Building(*at, "church", ("meta",), None) for at in (here, near, far)]
    buildings.append(Building(*here, "mosque", ("meta",), None))
    assert close_together(buildings, ["church", "mosque"]) == {"church": 2}
    assert close_together(buildings, ["mosque"]) == {}
    assert close_together((), ["church"]) == {}


# The count within reach


def test_the_buildings_of_each_kind_are_counted_within_reach_of_each_home(tmp_path: Path):
    inputs = inputs_of(tmp_path, [place(beside(Q1, 100), CHURCH), place(Q2, SHOP)])
    found = spine.build(inputs)
    held = places_counted.read(
        culture_file.opened_of(inputs), decide, KINDS, (LeftOut.NOTHING_OF_THE_TABLE,)
    )
    buildings, _ = as_buildings(held.records, ["church", "mosque"])
    counted = nearby(
        buildings, held.every, ["church", "mosque"], ground_of(inputs, found), found, added_up=True
    )
    assert counted.kinds == ("church", "mosque")
    assert counted.reach.within[OAS[0]] == (1, 0, 1)
    assert counted.counted is not None
    assert counted.counted[OAS[0]] == 1.0 and counted.counted[OAS[1]] == 0.0
    assert OAS[0] in counted.seen and OAS[4] not in counted.seen
    assert OAS[4] in counted.nothing_seen
    assert set(counted.of_kind) == {"church", "mosque"}


def test_the_kinds_of_a_table_are_added_up_only_where_its_measure_asks(tmp_path: Path):
    """Two kinds that are two things are handed back as two figures, and as no figure of both."""
    inputs = inputs_of(tmp_path, [place(beside(Q1, 100), CHURCH), place(Q2, MOSQUE)])
    found = spine.build(inputs)
    held = places_counted.read(
        culture_file.opened_of(inputs), decide, KINDS, (LeftOut.NOTHING_OF_THE_TABLE,)
    )
    buildings, _ = as_buildings(held.records, ["church", "mosque"])
    ground = ground_of(inputs, found)
    apart = nearby(buildings, held.every, ["church", "mosque"], ground, found, added_up=False)
    assert apart.of_all is None and apart.counted is None
    assert set(apart.of_kind) == {"church", "mosque"} and OAS[0] in apart.seen
    whole = nearby(buildings, held.every, ["church", "mosque"], ground, found, added_up=True)
    assert whole.of_all is not None and whole.of_kind == apart.of_kind


def test_what_is_handed_back_cannot_be_made_into_a_rate_or_a_count_of_kinds(tmp_path: Path):
    """The reach of cultural venues holds the homes within reach, and says how many kinds are
    within it. Neither is handed on: a count of buildings for each so many homes would stand
    in for who lives somewhere, and how many kinds are near would say how mixed a place is."""
    inputs = inputs_of(tmp_path, IN_THE_TOWN)
    found = spine.build(inputs)
    held = places_counted.read(
        culture_file.opened_of(inputs), decide, KINDS, (LeftOut.NOTHING_OF_THE_TABLE,)
    )
    buildings, _ = as_buildings(held.records, ["church", "mosque"])
    counted = nearby(
        buildings, held.every, ["church", "mosque"], ground_of(inputs, found), found, added_up=True
    )
    assert not isinstance(counted.reach, culture_reach.Reach)
    assert not hasattr(counted.reach, "homes") and not hasattr(counted.reach, "how_many_of")
    with pytest.raises(AttributeError):
        culture_reach.rates(counted.reach.of((0,)), counted.reach, found)  # pyright: ignore[reportArgumentType]
    assert counted.reach.metres == 800 and counted.reach.of((0, 1))[OAS[0]] == 1.0


def test_each_figure_is_held_against_how_built_up_and_how_central_an_area_is(tmp_path: Path):
    """Three areas, so a rank correlation can be given. It is a number and no name."""
    inputs = inputs_of(tmp_path, IN_THE_TOWN)
    found = spine.build(inputs)
    held = places_counted.read(
        culture_file.opened_of(inputs), decide, KINDS, (LeftOut.NOTHING_OF_THE_TABLE,)
    )
    buildings, _ = as_buildings(held.records, ["church", "mosque"])
    ground = ground_of(inputs, found)
    counted = nearby(buildings, held.every, ["church", "mosque"], ground, found, added_up=True)
    assert counted.of_all is not None
    density: dict[str, float | None] = {ONE: 30.0, TWO: 20.0, THREE: 10.0}
    churches, every = held_against_the_centre(
        {"made_up_churches": counted.of_kind["church"], "made_up_every": counted.of_all},
        counted,
        found,
        density,
        ground,
    )
    assert (churches.figure, every.figure) == ("made_up_churches", "made_up_every")
    assert churches.areas == every.areas == 3
    for one in (churches, every):
        for value in (one.with_density, one.with_distance, one.with_every):
            assert value is None or -1.0 <= value <= 1.0
        assert "lon-" not in one.line() and "Quillhaven" not in one.line()


def test_a_figure_is_a_count_made_by_the_method_of_cultural_venues():
    assert UNIT == "count"
    assert METHOD.derivation_id == "places_within_800m_at_homes@1"
    assert METHOD.code == "burro_pipeline.derive.culture_reach"


def test_the_module_holds_no_table_and_measures_no_distance_of_its_own():
    """What is within reach is `culture_reach.py`'s, and which category is which is a table's."""
    text = Path(str(places_counted.__file__)).read_text(encoding="utf-8")
    tree = ast.parse(text)
    assert not any(isinstance(node, ast.Dict) and node.keys for node in ast.walk(tree))
    assert "math" not in {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "pyarrow" not in text
