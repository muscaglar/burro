"""A name for each drafted area: which is offered first, which are the others, and which has none.

Every name here is made up, and is one the synthetic release already holds.
The ground is six output areas in a row, given to three areas:

    output areas   a1  a2 | b1  b2 | c1  c2
    areas          lon-n0001 lon-n0002 lon-n0003
"""

from collections.abc import Mapping

import pytest
from burro_pipeline.areas import draft_names
from burro_pipeline.areas.draft_names import (
    AREA,
    BY_AN_OUTLINE_ALONE,
    HEAVIER_NAME_INSIDE,
    INSIDE,
    LABEL_ONLY,
    NOT_ITS_SEED,
    ON_THE_LINE,
    OUTLINE,
    POINT,
    POINT_INSIDE,
    POLYGON_OVERLAP,
    SAME_GROUND,
    SEED_LIES_ELSEWHERE,
    UNNAMED,
    WAS_PUT_UNDER_ANOTHER,
    WIDE,
    Name,
    Naming,
    Record,
    Rules,
    name_areas,
)

A, B, C = "lon-n0001", "lon-n0002", "lon-n0003"
AREA_OF = {"a1": A, "a2": A, "b1": B, "b2": B, "c1": C, "c2": C}
STANDS = {A: A, B: B, C: C}
SURVEY, AUTHORITY = "Ordnance Survey", "Greater London Authority"


def point(oa: str, record_id: str = "osgb-made-up-1") -> Record:
    return Record(
        source_id="os-open-names",
        record_id=record_id,
        publisher=SURVEY,
        field="NAME1",
        as_written="Alderwick",
        gives=POINT,
        match="same",
        writes=True,
        lies_on={oa: 1.0},
    )


def outline(
    lies_on: Mapping[str, float],
    record_id: str = "TCB-made-up-1",
    *,
    source_id: str = "gla-town-centre-boundaries",
    publisher: str = AUTHORITY,
    as_written: str = "Alderwick",
    match: str = "same",
    writes: bool = True,
) -> Record:
    return Record(
        source_id=source_id,
        record_id=record_id,
        publisher=publisher,
        field="sitename",
        as_written=as_written,
        gives=OUTLINE,
        match=match,
        writes=writes,
        lies_on=dict(lies_on),
    )


def place(
    place_id: str,
    name: str,
    *records: Record,
    proposed: str = AREA,
    points: int = 6,
    of: tuple[str, ...] = (),
    second_name: str = "",
    second_field: str = "",
) -> Name:
    return Name(place_id, name, proposed, points, records, of, second_name, second_field)


def three() -> list[Name]:
    """A seed in each area, each where its own point lies."""
    return [
        place(A, "Alderwick", point("a1", "osgb-1")),
        place(B, "Cindermoor", point("b1", "osgb-2")),
        place(C, "Eskerfold", point("c1", "osgb-3")),
    ]


def named(
    names: list[Name], *, stands: Mapping[str, str] | None = None, rules: Rules | None = None
) -> Naming:
    return name_areas(names, AREA_OF, STANDS | dict(stands or {}), rules)


def marks(naming: Naming) -> set[tuple[str, str]]:
    return {(mark.area_id, mark.mark) for mark in naming.marks}


# The name offered first


def test_an_area_is_offered_the_name_it_was_grown_from_where_that_lies_in_it():
    naming = named(three())
    assert {area: first.as_offered for area, first in naming.first.items() if first} == {
        A: "Alderwick",
        B: "Cindermoor",
        C: "Eskerfold",
    }
    assert all(first.why == draft_names.SEED for first in naming.first.values() if first)
    assert naming.marks == ()


def test_a_name_whose_point_lies_outside_is_offered_where_its_outline_lies_over_the_area():
    """The seed stands on its town centre. The point Ordnance Survey gives is next door."""
    names = three()
    names[0] = place(A, "Alderwick", point("b1", "osgb-1"), outline({"a1": 0.9, "b1": 0.1}))
    naming = named(names)
    first = naming.first[A]
    assert first is not None and first.as_offered == "Alderwick"
    assert [each.locates for each in first.records] == [LABEL_ONLY, POLYGON_OVERLAP]
    assert (A, BY_AN_OUTLINE_ALONE) in marks(naming)
    # It is the name of one area, and is not offered again where its point lies.
    assert all(each.name.place_id != A for each in naming.others[B])


def test_a_sliver_of_an_outline_does_not_put_a_name_in_an_area():
    names = three()
    names[0] = place(A, "Alderwick", point("b1", "osgb-1"), outline({"a1": 0.04, "b1": 0.96}))
    naming = named(names)
    assert naming.first[A] is None
    assert draft_names.located(names[0].records[1], A, AREA_OF, Rules()).locates == LABEL_ONLY
    assert named(names, rules=Rules(overlap=0.04)).first[A] is not None


def test_a_record_whose_label_only_holds_the_name_never_puts_it_in_an_area():
    """`Alderwick Road` is not `Alderwick`. It adds points, and places nothing."""
    beside = outline({"a1": 1.0}, as_written="Alderwick Road", match="held", writes=False)
    names = three()
    names[0] = place(A, "Alderwick", point("b1", "osgb-1"), beside)
    assert named(names).first[A] is None


def test_an_area_no_name_lies_in_has_no_name_and_is_never_given_one():
    names = three()
    names[0] = place(A, "Alderwick", point("b1", "osgb-1"))
    naming = named(names)
    assert naming.first[A] is None
    assert naming.unnamed == (A,)
    assert (A, UNNAMED) in marks(naming)
    assert naming.offered(A) == ()
    # The name it was grown from is offered where its record lies, and says what it is.
    [moved] = [each for each in naming.others[B] if each.name.place_id == A]
    assert (moved.kind, moved.why) == (INSIDE, draft_names.SEED_OUTSIDE)
    assert (B, SEED_LIES_ELSEWHERE) in marks(naming)
    assert naming.placed[A] == B


def test_an_area_whose_own_name_lies_outside_is_offered_the_heaviest_name_that_lies_in_it():
    names = three()
    names[0] = place(A, "Alderwick", point("b1", "osgb-1"))
    names += [
        place("lon-n0011", "Foxholt", point("a1", "osgb-11"), proposed=INSIDE, points=3),
        place("lon-n0012", "Pellam Cross", point("a2", "osgb-12"), proposed=INSIDE, points=4),
    ]
    naming = named(names)
    first = naming.first[A]
    assert first is not None
    assert (first.as_offered, first.why, first.role) == ("Pellam Cross", "placed", "primary")
    assert [each.as_offered for each in naming.others[A]] == ["Foxholt"]
    assert (A, NOT_ITS_SEED) in marks(naming)


# The others


def test_every_other_name_is_offered_in_the_area_its_record_lies_in_the_heaviest_first():
    names = [
        *three(),
        place("lon-n0011", "Foxholt", point("a2", "osgb-11"), proposed=INSIDE, points=3),
        place("lon-n0012", "Wexmoor", point("a2", "osgb-12"), proposed=INSIDE, points=5),
        place("lon-n0013", "Kindlewharf", point("a1", "osgb-13"), proposed=INSIDE, points=3),
    ]
    naming = named(names)
    assert [each.as_offered for each in naming.others[A]] == ["Wexmoor", "Foxholt", "Kindlewharf"]
    assert {each.kind for each in naming.others[A]} == {INSIDE}
    assert {each.role for each in naming.others[A]} == {"alias"}
    assert naming.others[B] == naming.others[C] == ()


def test_of_two_names_with_as_many_points_the_one_more_publishers_write_comes_first():
    both = (point("a2", "osgb-12"), outline({"a2": 1.0}))
    names = [
        *three(),
        place("lon-n0011", "Foxholt", point("a2", "osgb-11"), proposed=INSIDE, points=3),
        place("lon-n0012", "Wexmoor", *both, proposed=INSIDE, points=3),
    ]
    assert [each.as_offered for each in named(names).others[A]] == ["Wexmoor", "Foxholt"]


def test_a_seed_that_stands_for_no_area_is_another_name_of_the_area_its_record_lies_in():
    """Its area was too small, and became part of the next. Its name is not lost."""
    names = [*three(), place("lon-n0004", "Farrowmere", point("c2", "osgb-4"), points=7)]
    naming = named(names, stands={"lon-n0004": B})
    [taken_in] = naming.others[C]
    assert (taken_in.as_offered, taken_in.kind) == ("Farrowmere", INSIDE)
    assert taken_in.why == draft_names.SEED_OF_NO_AREA
    assert (C, HEAVIER_NAME_INSIDE) in marks(naming)
    assert naming.others[B] == ()


def test_a_name_put_under_one_area_is_offered_where_its_record_lies_and_is_marked():
    """It was put under the nearest seed before a border was drawn. The border says otherwise."""
    names = [
        *three(),
        place("lon-n0011", "Foxholt", point("b1", "osgb-11"), proposed=INSIDE, points=3, of=(A,)),
        place("lon-n0012", "Wexmoor", point("a2", "osgb-12"), proposed=INSIDE, points=3, of=(A,)),
    ]
    naming = named(names)
    assert [each.as_offered for each in naming.others[B]] == ["Foxholt"]
    assert marks(naming) == {(B, WAS_PUT_UNDER_ANOTHER)}


def test_another_name_of_the_same_ground_is_kept_so_only_in_the_area_it_gave_way_to():
    def close_by(oa: str) -> Name:
        record = point(oa, "osgb-11")
        return place("lon-n0011", "Foxholt", record, proposed=SAME_GROUND, points=5, of=(A,))

    here = named([*three(), close_by("a1")])
    assert [each.kind for each in here.others[A]] == [SAME_GROUND]
    there = named([*three(), close_by("b2")])
    assert [each.kind for each in there.others[B]] == [INSIDE]


def test_a_name_put_under_a_seed_that_was_taken_in_is_under_the_area_that_took_it():
    names = [
        *three(),
        place("lon-n0004", "Farrowmere", point("c2", "osgb-4")),
        place(
            "lon-n0011",
            "Foxholt",
            point("c2", "osgb-11"),
            proposed=SAME_GROUND,
            points=3,
            of=("lon-n0004",),
        ),
    ]
    naming = named(names, stands={"lon-n0004": C})
    kinds = {each.as_offered: each.kind for each in naming.others[C]}
    assert kinds == {"Farrowmere": INSIDE, "Foxholt": SAME_GROUND}
    assert (C, WAS_PUT_UNDER_ANOTHER) not in marks(naming)


def test_a_wide_name_is_given_to_the_areas_chosen_for_it_five_at_most_and_each_once():
    wide = place(
        "lon-n0020",
        "Quillhaven",
        point("a1", "osgb-20"),
        proposed=WIDE,
        points=8,
        of=(A, "lon-n0004", B, C),
    )
    naming = named([*three(), wide], stands={"lon-n0004": A})
    given = [area for area in (A, B, C) if any(o.kind == WIDE for o in naming.others[area])]
    assert given == [A, B, C]
    assert sum(each.kind == WIDE for each in naming.others[A]) == 1
    assert {each.role for area in given for each in naming.others[area]} == {"wide"}
    # A wide name is no name inside an area, however many points it has.
    assert (A, HEAVIER_NAME_INSIDE) not in marks(naming)
    narrow = named([*three(), wide], stands={"lon-n0004": A}, rules=Rules(wide_over=2))
    assert sum(any(o.kind == WIDE for o in narrow.others[area]) for area in (A, B, C)) == 2


def test_a_second_name_of_a_record_is_another_name_of_the_same_ground():
    names = three()
    names[1] = place(
        B, "Cindermoor", point("b1", "osgb-2"), second_name="Lantern Yard", second_field="NAME2"
    )
    [second] = named(names).others[B]
    assert (second.as_offered, second.kind, second.why) == (
        "Lantern Yard",
        SAME_GROUND,
        draft_names.SECOND_NAME,
    )
    [record] = second.records
    assert (record.record.as_written, record.record.field) == ("Lantern Yard", "NAME2")
    assert (record.record.record_id, record.locates) == ("osgb-2", POINT_INSIDE)


# What is kept beside a name


def test_who_writes_a_name_is_every_publisher_whose_record_writes_it_wherever_it_lies():
    ward = outline(
        {"c1": 1.0},
        "E05-made-up",
        source_id="os-boundary-line",
        publisher=SURVEY,
        as_written="Alderwick Ward",
    )
    held = outline({"a1": 1.0}, as_written="Alderwick Road", match="held", writes=False)
    assert place(A, "Alderwick", point("a1"), ward).publishers == (SURVEY,)
    assert place(A, "Alderwick", point("a1"), held).publishers == (SURVEY,)
    assert place(A, "Alderwick", point("a1"), outline({"c1": 1.0})).publishers == (
        AUTHORITY,
        SURVEY,
    )


def test_every_record_beside_a_name_says_whether_it_lies_in_the_area_and_where_most_of_it_lies():
    names = three()
    names[0] = place(
        A, "Alderwick", point("a1", "osgb-1"), outline({"a2": 0.3, "b1": 0.6}), outline({"c1": 1})
    )
    first = named(names).first[A]
    assert first is not None
    assert [(each.locates, each.lies_in) for each in first.records] == [
        (POINT_INSIDE, A),
        (POLYGON_OVERLAP, B),
        (LABEL_ONLY, C),
    ]
    assert [round(each.share, 2) for each in first.records] == [1.0, 0.3, 0.0]


def test_every_place_is_offered_somewhere_and_no_name_is_made_up():
    names = [
        *three(),
        place("lon-n0011", "Foxholt", point("b2", "osgb-11"), proposed=INSIDE, points=3),
        place("lon-n0012", "Osierholm", outline({"c2": 0.7, "b2": 0.3}), proposed=INSIDE),
    ]
    naming = named(names)
    assert set(naming.placed) == {name.place_id for name in names}
    assert naming.placed["lon-n0012"] == C
    offered = {each.as_offered for area in (A, B, C) for each in naming.offered(area)}
    assert offered == {name.name for name in names}


def test_a_record_that_lies_on_no_output_area_of_the_draft_places_nothing():
    names = [*three(), place("lon-n0011", "Foxholt", point("z9", "osgb-11"), proposed=INSIDE)]
    naming = named(names)
    assert "lon-n0011" not in naming.placed
    assert all(not naming.others[area] for area in (A, B, C))


def test_the_same_names_in_another_order_give_the_same_naming():
    names = [
        *three(),
        place("lon-n0011", "Foxholt", point("a2", "osgb-11"), proposed=INSIDE, points=3),
        place("lon-n0012", "Wexmoor", point("a2", "osgb-12"), proposed=INSIDE, points=3),
    ]
    assert named(names) == named(list(reversed(names)))


def test_a_place_that_is_there_twice_stops_the_naming():
    with pytest.raises(ValueError, match="twice"):
        named([*three(), place(A, "Alderwick", point("a1"))])


# A point on the line between two output areas


def on_the_line(record_id: str, *cells: str) -> Record:
    """A point that lies on the edge of several output areas, and in none more than another."""
    whole = point(cells[0], record_id)
    return Record(
        whole.source_id,
        record_id,
        whole.publisher,
        whole.field,
        whole.as_written,
        POINT,
        "same",
        True,
        dict.fromkeys(cells, 1 / len(cells)),
    )


def test_a_seed_whose_point_lies_on_the_edge_of_its_own_area_lies_in_it():
    """The file does not say which side of a line a point is on. Its own area bears its
    name, so it is placed there, and the area is not told that no point of its name lies
    in it."""
    names = [
        place(A, "Alderwick", point("a1", "osgb-1")),
        place(B, "Cindermoor", on_the_line("osgb-2", "a2", "b1")),
        place(C, "Eskerfold", point("c1", "osgb-3")),
    ]
    found = named(names)
    first = found.first[B]
    assert first is not None and first.name.name == "Cindermoor"
    assert [each.locates for each in first.records] == [POINT_INSIDE]
    assert first.records[0].share == 0.5
    assert marks(found) == {(B, ON_THE_LINE)}
    (mark,) = found.marks
    assert mark.place_id == B and A in mark.why and "does not settle" in mark.why
    assert A not in [each.name.place_id for each in found.others[A]]


def test_another_name_on_a_line_is_placed_in_the_area_that_sorts_first_and_says_so():
    names = [
        *three(),
        place("lon-n0009", "Foxholt", on_the_line("osgb-9", "b2", "c1"), proposed=INSIDE, of=(C,)),
    ]
    found = named(names)
    assert [each.name.name for each in found.others[B]] == ["Foxholt"]
    assert found.others[C] == ()
    assert (B, ON_THE_LINE) in marks(found)
    # It was put under the other of the two before the borders were drawn: that is no
    # more than the line says, and is not marked a second time.
    assert (B, WAS_PUT_UNDER_ANOTHER) not in marks(found)


def test_a_point_on_a_line_between_two_output_areas_of_one_area_is_simply_inside():
    names = [place(A, "Alderwick", on_the_line("osgb-1", "a1", "a2"))]
    found = name_areas(names, {"a1": A, "a2": A}, {A: A})
    first = found.first[A]
    assert first is not None and first.records[0].share == 1.0
    assert found.marks == ()
