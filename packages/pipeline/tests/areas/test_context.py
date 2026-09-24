"""What is drawn behind a border for a reviewer, on a made-up town.

Every name, code and shape here is made up. The town is drawn in squares of
100 metres, in the North Sea.
"""

import json
from typing import Any, cast

import pytest
from burro_pipeline.areas import assign_shapes, context, context_shapes
from burro_pipeline.areas.context import Drawn, Layer
from burro_pipeline.registry.model import SHARE_ALIKE_LICENCES, Status

from ..cells.support import registry
from .context_support import block, boroughs_of, outlines_of, road
from .flags_support import BOROUGHS, QUILLHAVEN, TALLOWGATE

ROWS = ("AABB", "AABB")
WARDS = context.layer_named("wards")
ROADS = context.layer_named("roads")


def ring_of(found: object) -> list[list[float]]:
    geometry = cast(dict[str, Any], found)
    assert geometry["type"] == "Polygon"
    return geometry["coordinates"][0]


# The gate


def test_every_source_of_every_layer_is_given_for_the_gazetteer_by_the_registry():
    """A layer names a source only if the gate gives it. Rule 1."""
    sources = [source for layer in context.LAYERS for source in layer.sources]

    answers = context.ask(registry(), sources)

    assert all(answer.given for answer in answers.values()), answers
    assert all(context.may_be_made(layer, answers) for layer in context.LAYERS)


def test_what_the_design_wants_and_the_gate_refuses_is_refused_in_the_gates_own_words():
    """When the registry gives one of these the use, this fails: make its layer then."""
    answers = context.ask(registry(), [wanted.source for wanted in context.WANTED])

    assert {source for source, answer in answers.items() if not answer.given} == {
        "os-open-greenspace",
        "os-open-rivers",
        "dft-naptan",
    }
    assert all("not registered for gazetteer" in answer.words for answer in answers.values())


def test_a_layer_with_one_source_refused_is_not_made():
    layer = Layer("wards", ("os-boundary-line", "os-open-rivers"), ("name",))

    answers = context.ask(registry(), layer.sources)

    assert not context.may_be_made(layer, answers)
    assert not context.may_be_made(layer, {})


def test_no_layer_is_from_openstreetmap_or_from_any_share_alike_source():
    """Rule 3, and ADR 0004: what a border may be moved to match is never share-alike."""
    held = registry()
    for source_id in {source for layer in context.LAYERS for source in layer.sources}:
        source = held.get(source_id)
        assert not source.share_alike
        assert not (source.licences & SHARE_ALIKE_LICENCES)
        assert source.status is Status.APPROVED
        assert "osm" not in source_id and "openstreetmap" not in source.publisher.casefold()


def test_every_refusal_says_what_the_desk_shows_in_its_place_and_what_is_to_decide():
    for wanted in context.WANTED:
        assert wanted.in_its_place.endswith(".")
        assert wanted.to_decide.startswith("Whether ")
        assert "gazetteer" in wanted.to_decide


# A layer, as the desk reads it


def test_a_layer_is_written_as_the_desk_reads_one():
    things = [
        Drawn("E05999002", {"name": "Quillhaven East Ward"}, block(0, 2, 2, 2)),
        Drawn("E05999001", {"name": "Quillhaven West Ward"}, block(0, 0, 2, 2)),
    ]

    found = context.collection(WARDS, "quillhaven", things)

    assert found["type"] == "FeatureCollection"
    assert found["desk"] == {
        "layer": "wards",
        "group": "quillhaven",
        "source_ids": ["os-boundary-line"],
        "synthetic": False,
    }
    features = cast(list[dict[str, Any]], found["features"])
    assert [each["id"] for each in features] == ["E05999001", "E05999002"]
    assert set(features[0]) == {"type", "id", "properties", "geometry"}
    assert features[0]["properties"] == {"name": "Quillhaven West Ward"}
    # Longitude first, in the North Sea, to six decimal places.
    for longitude, latitude in ring_of(features[0]["geometry"]):
        assert 2 < longitude < 4 and 53 < latitude < 54
        assert round(longitude, 6) == longitude and round(latitude, 6) == latitude


def test_the_same_layer_is_always_the_same_bytes():
    things = [Drawn("E05999001", {"name": "Quillhaven West Ward"}, block(0, 0, 2, 2))]

    once = context.canonical(context.collection(WARDS, "quillhaven", things))
    again = context.canonical(context.collection(WARDS, "quillhaven", list(reversed(things))))

    assert once == again
    assert json.loads(once)["desk"]["layer"] == "wards"


def test_a_feature_may_hold_no_property_that_its_layer_is_not_given():
    """So no figure about who lives somewhere can ride in on a layer. Rule 8."""
    crowded = Drawn("E05999001", {"name": "Quillhaven West Ward", "residents": "9"}, block(0, 0))

    with pytest.raises(ValueError, match="no other"):
        context.feature(WARDS, crowded)


def test_the_properties_of_every_layer_are_the_ones_the_desk_gives_it():
    assert {layer.name: set(layer.properties) for layer in context.LAYERS} == {
        "boroughs": {"name"},
        "wards": {"name"},
        "centres": {"name", "class"},
        "roads": {"class", "name"},
        "names": {"name", "kind"},
        "cells": {"area", "colour", "borough"},
        "areas": {"name"},
        "seeds": {"area", "name"},
        "water": {"name"},
    }


def test_an_id_held_twice_in_one_layer_is_refused():
    twice = [Drawn("E05999001", {"name": "Quillhaven West Ward"}, block(0, 0))] * 2

    with pytest.raises(ValueError, match="held twice"):
        context.collection(WARDS, "quillhaven", twice)


def test_a_line_and_a_point_are_written_as_a_map_draws_them():
    line = cast(dict[str, Any], context_shapes.drawn(road((0, 0), (0, 2), (1, 2))))
    point = cast(dict[str, Any], context_shapes.drawn(context_shapes.point((700_000, 400_000))))

    assert line["type"] == "LineString" and len(line["coordinates"]) == 3
    assert point["type"] == "Point" and len(point["coordinates"]) == 2


# Boroughs


def test_a_borough_is_its_output_areas_joined_with_no_line_between():
    found = context.borough_outlines(outlines_of(ROWS), boroughs_of(ROWS, 2))

    assert list(found) == [QUILLHAVEN, TALLOWGATE]
    assert assign_shapes.metres_round(found[QUILLHAVEN]) == pytest.approx(800.0)
    assert found[QUILLHAVEN].equals(block(0, 0, 2, 2))


def test_every_borough_is_listed_once_by_name_for_the_desk_to_ask():
    found = context.boroughs_to_ask(outlines_of(ROWS), boroughs_of(ROWS, 3), BOROUGHS)

    assert [
        (each.name, each.code, each.group, each.output_areas, each.hectares) for each in found
    ] == [
        ("Quillhaven", QUILLHAVEN, "quillhaven", 6, 6.0),
        ("Tallowgate", TALLOWGATE, "tallowgate", 2, 2.0),
    ]


def test_a_boroughs_group_is_its_name_in_lower_case_with_hyphens_as_the_desk_makes_it():
    assert context.group_of("Quillhaven and Tallowgate") == "quillhaven-and-tallowgate"
    assert context.group_of("Tallowgate upon Quill") == "tallowgate-upon-quill"


def test_two_boroughs_that_would_share_a_group_stop_the_list():
    names = {QUILLHAVEN: "Quillhaven", TALLOWGATE: "quillhaven"}

    with pytest.raises(ValueError, match="share a group"):
        context.boroughs_to_ask(outlines_of(ROWS), boroughs_of(ROWS, 2), names)


# What is drawn for each borough


def test_a_boroughs_group_holds_what_lies_within_500_metres_of_it():
    rows = ("A" * 12,)
    boroughs = context.borough_outlines(outlines_of(rows), boroughs_of(rows, 6))
    things = [
        Drawn("E05999001", {"name": "Quillhaven West Ward"}, block(0, 0, 1, 1)),
        Drawn("E05999002", {"name": "Tallowgate Ward"}, block(0, 10, 1, 2)),
        Drawn("E05999003", {"name": "Tallowgate Far Ward"}, block(0, 11.5, 1, 1)),
    ]

    found = context.by_borough(WARDS, things, boroughs, BOROUGHS)

    # Quillhaven ends at 600 m. A ward that begins at 1,000 m is within 500 m of it, and
    # one that begins at 1,150 m is not.
    assert [each.record_id for each in found["quillhaven"]] == ["E05999001", "E05999002"]
    assert len(found["tallowgate"]) == 3
    # A ward at the edge is drawn whole.
    assert found["quillhaven"][1].shape.equals(block(0, 10, 1, 2))


def test_a_road_is_cut_to_the_ground_of_each_borough():
    rows = ("A" * 40,)
    boroughs = context.borough_outlines(outlines_of(rows), boroughs_of(rows, 20))
    long_road = Drawn(
        "syn-link-0001", {"class": "A Road", "name": "Tallowgate Row"}, road((0, 0), (0, 40))
    )

    found = context.by_borough(ROADS, [long_road], boroughs, BOROUGHS)

    # Quillhaven is 2,000 m wide, and its group reaches 500 m further.
    assert assign_shapes.metres_round(found["quillhaven"][0].shape) == pytest.approx(2_500.0)
    assert assign_shapes.metres_round(found["tallowgate"][0].shape) == pytest.approx(2_500.0)


def test_outlines_that_share_a_side_still_share_it_once_they_are_thinned():
    wiggle = [(700_000.0, 400_000.0), (700_050.0, 400_000.4), (700_100.0, 400_000.0)]
    north = context_shapes.outline([*wiggle, (700_100.0, 400_100.0), (700_000.0, 400_100.0)])
    south = context_shapes.outline([*wiggle, (700_100.0, 399_900.0), (700_000.0, 399_900.0)])
    things = [Drawn("E05999001", {"name": "a"}, north), Drawn("E05999002", {"name": "b"}, south)]

    thin = context.thinned(WARDS, things)

    assert shapes_points(thin[0]) == 4 and shapes_points(thin[1]) == 4
    assert thin[0].shape.intersection(thin[1].shape).length == pytest.approx(100.0)


def shapes_points(drawn: Drawn) -> int:
    ring = ring_of(context_shapes.drawn(drawn.shape))
    return len(ring) - 1


def test_a_layer_that_is_not_thinned_keeps_every_point():
    names = context.layer_named("names")
    things = [Drawn("syn0000000001", {"name": "a", "kind": "b"}, context_shapes.point((1.0, 2.0)))]

    assert context.thinned(names, things) == things


# Water


def test_the_tidal_water_is_the_boroughs_as_drawn_to_the_river_less_the_land():
    to_the_river = [block(0, 0, 4, 2), block(0, 2, 4, 2)]
    land = list(outlines_of(("AAAA", "AAAA")).values())

    water = context.tidal_water(to_the_river, land)

    assert water is not None
    assert water.equals(block(2, 0, 2, 4))


def test_a_sliver_where_two_publishers_draw_one_line_apart_is_no_water():
    to_the_river = [block(0, 0, 4, 2), block(-0.1, 2, 4.1, 2)]
    land = list(outlines_of(("AAAA", "AAAA")).values())

    water = context.tidal_water(to_the_river, land)

    # A strip 10 m wide lies north of the land, where the two lines differ. It is left out.
    assert water is not None
    assert water.equals(block(2, 0, 2, 4))


def test_with_no_land_or_no_borough_there_is_no_water():
    assert context.tidal_water([], list(outlines_of(("A",)).values())) is None
    assert context.tidal_water([block(0, 0, 2, 2)], []) is None
