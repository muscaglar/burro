"""What is drawn behind a border: docs/design/desk.md, section 6.

Only layers from sources registered for `gazetteer`, and never a property the design
does not name. Every layer here is made up.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from desk.fill import gate, layers
from desk.fill.layers import Unfit

REGISTRY = Path(__file__).resolve().parents[4] / "registry" / "sources"


def square(name: str, x: float, y: float, **properties: object) -> dict[str, Any]:
    ring = [[x, y], [x + 1, y], [x + 1, y + 1], [x, y + 1], [x, y]]
    return {
        "type": "Feature",
        "id": name,
        "properties": properties,
        "geometry": {"type": "Polygon", "coordinates": [ring]},
    }


def written(
    folder: Path,
    features: list[dict[str, Any]],
    *,
    layer: str = "cells",
    group: str = "quillhaven",
    sources: tuple[str, ...] = ("synthetic",),
    synthetic: bool = True,
    **more: object,
) -> Path:
    about = {"layer": layer, "group": group, "source_ids": list(sources), "synthetic": synthetic}
    path = folder / "layers" / group / f"{layer}.geojson"
    path.parent.mkdir(parents=True, exist_ok=True)
    held = {"type": "FeatureCollection", "desk": {**about, **more}, "features": features}
    path.write_text(json.dumps(held), encoding="utf-8")
    return path


def cell(name: str = "syn-oa0001", x: float = 0.0, **properties: object) -> dict[str, Any]:
    given = {"area": "syn-n0001", "colour": 0, "borough": "Quillhaven", **properties}
    return square(name, x, 0.0, **given)


def test_a_layer_is_read_as_the_design_gives_it(tmp_path: Path):
    held = layers.read(written(tmp_path, [cell()]), synthetic=True)
    assert held["desk"] == {
        "layer": "cells",
        "group": "quillhaven",
        "source_ids": ["synthetic"],
        "synthetic": True,
    }
    assert [feature["id"] for feature in held["features"]] == ["syn-oa0001"]


def test_no_layer_is_from_a_source_without_the_use(tmp_path: Path):
    # The name the design gives this test: section 6.
    roads = {"type": "LineString", "coordinates": [[-0.1, 51.5], [-0.09, 51.51]]}
    road = {"type": "Feature", "id": "r1", "properties": {"class": "A road"}, "geometry": roads}
    for source, allowed in (("os-open-roads", True), ("os-open-greenspace", False)):
        folder = tmp_path / source
        written(folder, [road], layer="roads", group="camden", sources=(source,), synthetic=False)
        held = layers.read_all(folder / "layers", synthetic=False)
        if allowed:
            assert layers.copy(held, folder / "out", synthetic=False, registry=REGISTRY) == 1
        else:
            with pytest.raises(gate.Refused, match="not registered for gazetteer"):
                layers.copy(held, folder / "out", synthetic=False, registry=REGISTRY)
            assert not (folder / "out").exists()


def record(name: str, source: object, wrote: str = "A made-up name") -> dict[str, Any]:
    about: dict[str, object] = {"as_written": wrote}
    if source is not None:
        about["source_id"] = source
    place = {"type": "Point", "coordinates": [-0.1, 51.5]}
    return {"type": "Feature", "id": name, "properties": about, "geometry": place}


def test_a_record_from_a_source_its_layer_does_not_name_is_refused(tmp_path: Path):
    # Rule 3. The gate is asked about the sources a layer names. So a record of a source
    # the layer does not name would be drawn beside a name, asked about by nobody, and
    # credited to another publisher.
    named = ("os-open-names", "wikidata-places-and-landmarks")
    held = [record("lon-r0001", "os-open-names"), record("lon-r0002", "osm-place-nodes")]
    path = written(tmp_path, held, layer="records", group="camden", sources=named, synthetic=False)
    with pytest.raises(Unfit, match="a record of a source that the layer does not name") as refusal:
        layers.read(path, synthetic=False)
    assert "osm-place-nodes" not in str(refusal.value), "the words name the file, never a value"
    assert "A made-up name" not in str(refusal.value)


@pytest.mark.parametrize("source", [None, "", 7, ["os-open-names"]])
def test_a_record_says_which_source_it_is_of(tmp_path: Path, source: object):
    path = written(
        tmp_path,
        [record("lon-r0001", source)],
        layer="records",
        group="camden",
        sources=("os-open-names",),
        synthetic=False,
    )
    with pytest.raises(Unfit):
        layers.read(path, synthetic=False)


def test_the_gate_is_asked_about_the_source_of_every_record(tmp_path: Path):
    named = ("os-open-names", "osm-geofabrik-greater-london")
    held = [record("lon-r0001", "os-open-names"), record("lon-r0002", named[1])]
    written(tmp_path, held, layer="records", group="camden", sources=named, synthetic=False)
    read = layers.read_all(tmp_path / "layers", synthetic=False)
    with pytest.raises(gate.Refused, match="osm-geofabrik-greater-london"):
        layers.copy(read, tmp_path / "out", synthetic=False, registry=REGISTRY)
    assert not (tmp_path / "out").exists()


def test_the_records_of_the_made_up_city_are_each_of_a_source_their_layer_names(tmp_path: Path):
    named = ("synthetic-items", "synthetic-names")
    held = [record("syn-r0001", "synthetic-names"), record("syn-r0002", "synthetic-items")]
    path = written(tmp_path, held, layer="records", sources=named)
    assert len(layers.read(path, synthetic=True)["features"]) == 2


@pytest.mark.parametrize("source", ["osm-geofabrik-greater-london", "protomaps-basemap-london"])
def test_a_layer_made_from_openstreetmap_is_never_copied(tmp_path: Path, source: str):
    # Rule 3 of AGENTS.md. The registry gives these to the basemap and to routing alone.
    written(tmp_path, [cell("c1")], sources=(source,), synthetic=False)
    held = layers.read_all(tmp_path / "layers", synthetic=False)
    with pytest.raises(gate.Refused, match="not registered for gazetteer"):
        layers.copy(held, tmp_path / "out", synthetic=False, registry=REGISTRY)


@pytest.mark.parametrize(
    "properties",
    [{"population": "4200"}, {"median_price": "650000"}, {"crime_rate": "12"}, {"imd_rank": "3"}],
)
def test_a_layer_with_a_property_the_design_does_not_name_is_refused(
    tmp_path: Path, properties: dict[str, object]
):
    with pytest.raises(Unfit, match="a property that the design does not give to cells"):
        held = cell()
        held["properties"].update(properties)
        layers.read(written(tmp_path, [held]), synthetic=True)


def test_a_layer_in_another_grid_is_refused_and_not_converted(tmp_path: Path):
    national_grid = square("syn-oa0001", 530000.0, 180000.0, area="syn-n0001")
    with pytest.raises(Unfit, match="The desk converts no coordinates"):
        layers.read(written(tmp_path, [national_grid]), synthetic=True)


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        ({"layer": "tiles"}, "is not a layer the desk draws"),
        ({"group": "all"}, "the boroughs are in the group all"),
        ({"sources": ()}, "names no source"),
        ({"synthetic": False}, "another layer, of another group or another city"),
        ({"note": "more"}, "does not say which layer it is"),
    ],
)
def test_a_layer_that_does_not_say_what_it_is_is_refused(
    tmp_path: Path, change: dict[str, Any], refusal: str
):
    with pytest.raises(Unfit, match=refusal):
        layers.read(written(tmp_path, [cell()], **change), synthetic=True)


def test_a_layer_is_what_its_place_says_it_is(tmp_path: Path):
    path = written(tmp_path, [cell()])
    moved = path.with_name("areas.geojson")
    path.rename(moved)
    with pytest.raises(Unfit, match="another layer"):
        layers.read(moved, synthetic=True)


@pytest.mark.parametrize(
    ("feature", "refusal"),
    [
        (cell(""), "a feature with no id"),
        (cell("oa-1"), "an id that does not begin syn-"),
        (cell(colour=12), "a colour that is not a number from 0 to 11"),
        (cell(borough=3), "a property that is not text"),
        ({**cell(), "geometry": {"type": "Point", "coordinates": [0, 0]}}, "is not drawn from"),
        ({**cell(), "geometry": {"type": "Polygon", "coordinates": "x"}}, "cannot be read"),
    ],
)
def test_a_feature_that_is_not_as_the_design_gives_it_is_refused(
    tmp_path: Path, feature: dict[str, Any], refusal: str
):
    with pytest.raises(Unfit, match=refusal):
        layers.read(written(tmp_path, [feature]), synthetic=True)


def test_an_id_that_stands_twice_is_refused(tmp_path: Path):
    with pytest.raises(Unfit, match="holds an id twice"):
        layers.read(written(tmp_path, [cell(), cell()]), synthetic=True)


def test_a_layer_is_written_to_six_decimals_with_longitude_first(tmp_path: Path):
    long = square("syn-oa0001", 0.12345678, 0.00000049, area="syn-n0001")
    held = layers.read_all(written(tmp_path, [long]).parents[1], synthetic=True)
    layers.copy(held, tmp_path / "out", synthetic=True)
    text = (tmp_path / "out" / "layers" / "quillhaven" / "cells.geojson").read_text("utf-8")
    assert json.loads(text)["features"][0]["geometry"]["coordinates"][0][0] == [0.123457, 0.0]


def test_a_layer_of_an_earlier_fill_does_not_outlive_its_draft(tmp_path: Path):
    written(tmp_path / "one", [cell()])
    written(tmp_path / "one", [cell()], group="east")
    layers.copy(
        layers.read_all(tmp_path / "one" / "layers", synthetic=True), tmp_path, synthetic=True
    )
    written(tmp_path / "two", [cell()])
    layers.copy(
        layers.read_all(tmp_path / "two" / "layers", synthetic=True), tmp_path, synthetic=True
    )
    assert list(layers.found(tmp_path / "layers")) == ["quillhaven"]


def test_cells_that_share_a_side_are_beside_each_other():
    row = [cell("a", 0), cell("b", 1), cell("c", 2), square("d", 1, 1), square("e", 2.5, 1)]
    beside = layers.touching(row)
    assert beside == {"a": {"b"}, "b": {"a", "c", "d"}, "c": {"b"}, "d": {"b"}, "e": set()}


def test_the_box_round_some_features_has_a_margin():
    assert layers.bounds([cell("a", 0), cell("b", 3)]) == [0, 0, 4, 1]
    assert layers.bounds([cell("a", 0), cell("b", 3)], margin=0.25) == [-1, -1, 5, 2]
    assert layers.bounds([]) is None
