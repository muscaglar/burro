"""The ground a flag is worked out on, from the shapes of a made-up town.

Every name, code and shape here is made up. The town is drawn in squares of
100 metres, in the North Sea.
"""

import pytest
from burro_pipeline.areas import flags, flags_ground
from burro_pipeline.areas.flags import Rules
from burro_pipeline.areas.flags_ground import Centre, Given, Named

from .context_support import block, boroughs_of, outlines_of, road
from .flags_support import BOROUGHS, area_id, oa

ROWS = ("AABB", "AABB")


def given_of(rows: tuple[str, ...]) -> dict[str, Given]:
    return {
        oa(row, column): Given(area_id(letter), margin=50.0)
        for row, line in enumerate(rows)
        for column, letter in enumerate(line)
    }


NAMED = {area_id("A"): Named("Alderwick"), area_id("B"): Named("Brackenhythe")}


def ground(rows: tuple[str, ...] = ROWS, **more: object) -> flags_ground.Ground:
    return flags_ground.ground_of(outlines_of(rows), boroughs_of(rows, 2), BOROUGHS, **more)  # type: ignore[arg-type]


def test_two_squares_side_by_side_share_one_side_of_a_hundred_metres():
    shared = flags_ground.shared_sides(outlines_of(("AB",)))

    assert list(shared) == [(oa(0, 0), oa(0, 1))]
    ((a, b),) = shared[oa(0, 0), oa(0, 1)]
    assert a[0] == b[0] and abs(a[1] - b[1]) == 100


def test_two_squares_that_meet_at_a_corner_share_no_side():
    shared = flags_ground.shared_sides(outlines_of(("A.", ".B")))

    assert shared == {}


def test_the_ground_holds_the_size_and_the_outline_of_every_output_area():
    found = ground()

    assert found.hectares[oa(0, 0)] == pytest.approx(1.0)
    assert found.perimeter[oa(0, 0)] == pytest.approx(400.0)
    assert len(found.shared) == 10


def test_an_output_area_is_in_the_ward_that_holds_most_of_it():
    wards = {"E05999001": block(0, 0, 2, 1.7), "E05999002": block(0, 1.7, 2, 2.3)}

    found = ground(wards=wards)

    assert found.ward_of[oa(0, 0)] == "E05999001"
    # 70 in 100 of the second column is in the first ward.
    assert found.ward_of[oa(0, 1)] == "E05999001"
    assert found.ward_of[oa(0, 2)] == "E05999002"


def test_an_output_area_with_no_borough_stops_the_ground():
    outlines = outlines_of(ROWS)
    boroughs = boroughs_of(ROWS, 2)
    del boroughs[oa(0, 0)]

    with pytest.raises(ValueError, match="an outline and a borough"):
        flags_ground.ground_of(outlines, boroughs, BOROUGHS)


def test_a_border_is_held_against_the_roads_and_a_side_inside_an_area_is_not():
    area_of = {code: row.area for code, row in given_of(ROWS).items()}
    along_the_border = road((0, 2), (2, 2))
    through_an_area = road((0, 1), (2, 1))

    sides = flags_ground.sides_of(ground(), area_of, [along_the_border, through_an_area], Rules())

    along = {(side.a, side.b): side.along_a_road for side in sides}
    assert along[oa(0, 1), oa(0, 2)] == pytest.approx(100.0)
    assert along[oa(1, 1), oa(1, 2)] == pytest.approx(100.0)
    assert along[oa(0, 0), oa(0, 1)] == 0.0
    assert {side.metres for side in sides} == {100.0}


def test_a_road_that_crosses_a_border_is_not_a_road_along_it():
    area_of = {code: row.area for code, row in given_of(ROWS).items()}
    across = road((0.5, 0), (0.5, 4))

    sides = flags_ground.sides_of(ground(), area_of, [across], Rules())

    along = {(side.a, side.b): side.along_a_road for side in sides}
    # Of the four steps of 25 m along the side, the two beside the crossing are within 20 m.
    assert along[oa(0, 1), oa(0, 2)] == pytest.approx(50.0)
    assert along[oa(1, 1), oa(1, 2)] == 0.0


def test_a_road_further_than_the_rule_allows_is_no_road_along_a_border():
    area_of = {code: row.area for code, row in given_of(ROWS).items()}
    beside = road((0, 2.3), (2, 2.3))

    near = flags_ground.sides_of(ground(), area_of, [beside], Rules(road_metres=40.0))
    far = flags_ground.sides_of(ground(), area_of, [beside], Rules())

    assert sum(side.along_a_road for side in near) == pytest.approx(200.0)
    assert sum(side.along_a_road for side in far) == 0.0


def test_a_town_centre_is_in_the_area_that_holds_most_of_its_ground():
    outlines = outlines_of(ROWS)
    area_of = {code: row.area for code, row in given_of(ROWS).items()}
    centres = [
        Centre("SYN00000001", "Tallowgate Cross", block(0.2, 1.5, 0.5, 0.8)),
        Centre("SYN00000002", "Quillhaven Market", block(1.2, 0.2, 0.5, 0.5)),
        Centre("SYN00000003", "Quillhaven Cross", block(0.2, 0.2, 0.5, 0.5)),
        Centre("SYN00000004", "Tallowgate Wharf", block(5, 5)),
    ]

    found = flags_ground.centres_of(centres, outlines, area_of)

    assert found == {
        area_id("A"): ("Tallowgate Cross", "Quillhaven Market", "Quillhaven Cross"),
    }


def test_the_draft_the_rules_read_holds_what_the_ground_and_the_draft_say():
    outlines = outlines_of(ROWS)
    given = given_of(ROWS) | {oa(0, 1): Given(area_id("A"), margin=3.0, second=area_id("B"))}
    centres = [
        Centre("SYN00000002", "Quillhaven Market", block(1.2, 0.2, 0.5, 0.5)),
        Centre("SYN00000003", "Quillhaven Cross", block(0.2, 0.2, 0.5, 0.5)),
    ]

    draft = flags_ground.draft_of(
        ground(), given, NAMED, outlines=outlines, centres=centres, main_roads=[]
    )

    cell = draft.cells[oa(0, 1)]
    assert (cell.margin, cell.second, cell.borough, cell.hectares) == (
        3.0,
        area_id("B"),
        "E09000901",
        pytest.approx(1.0),
    )
    assert draft.weighed_by == "output areas"
    assert draft.areas[area_id("A")].centres == ("Quillhaven Market", "Quillhaven Cross")
    found = {flag.code for flag in flags.flags_of(draft) if flag.area == area_id("A")}
    assert {flags.TWO_CENTRES, flags.MARGIN, flags.ONE_PUBLISHER} <= found


def test_homes_are_carried_only_where_they_are_handed_over():
    homes = {code: 120 for code in given_of(ROWS)}

    with_homes = flags_ground.draft_of(ground(), given_of(ROWS), NAMED, homes=homes)
    without = flags_ground.draft_of(ground(), given_of(ROWS), NAMED)

    assert with_homes.weighed_by == "homes"
    assert without.weighed_by == "output areas"
    assert all(cell.homes is None for cell in without.cells.values())


def test_an_output_area_the_draft_leaves_in_no_area_stops_the_flags():
    given = given_of(ROWS)
    del given[oa(1, 3)]

    with pytest.raises(ValueError, match="in one area of the draft"):
        flags_ground.draft_of(ground(), given, NAMED)


def test_an_output_area_in_an_area_with_no_name_stops_the_flags():
    given = given_of(ROWS) | {oa(1, 3): Given("syn-n0099")}

    with pytest.raises(ValueError, match="does not name"):
        flags_ground.draft_of(ground(), given, NAMED)
