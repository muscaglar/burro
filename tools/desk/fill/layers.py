"""The layers a map is drawn from: read, held to the design, asked about, and copied.

docs/design/desk.md, sections 6 and 8. A layer is a GeoJSON FeatureCollection in WGS84,
longitude first, with a member `desk` that says which layer it is and which sources it
was made from. Only a layer from sources registered for `gazetteer` is copied. No layer
holds a property the design does not name, so no figure can ride in on one.

The desk converts no coordinates. A layer in another grid is refused.
"""

import json
from collections.abc import Iterable, Iterator, Mapping
from itertools import pairwise
from pathlib import Path
from typing import Any, Final, cast

from desk.fill import gate

type Point = tuple[float, float]
type Collection = dict[str, Any]

# The group that holds what is drawn for every borough at once.
ALL: Final = "all"
DECIMALS: Final = 6
POLYGONS: Final = frozenset({"Polygon", "MultiPolygon"})
LINES: Final = frozenset({"LineString", "MultiLineString"})
POINTS: Final = frozenset({"Point"})

# Each layer, in the order it is drawn: the properties a feature may hold, and its shapes.
LAYERS: Final[Mapping[str, tuple[frozenset[str], frozenset[str]]]] = {
    "cells": (frozenset({"area", "colour", "borough"}), POLYGONS),
    "areas": (frozenset({"name"}), POLYGONS),
    "boroughs": (frozenset({"name"}), POLYGONS),
    "wards": (frozenset({"name"}), POLYGONS),
    "centres": (frozenset({"name", "class"}), POLYGONS),
    "roads": (frozenset({"class", "name"}), LINES),
    "names": (frozenset({"name", "kind"}), POINTS),
    "seeds": (frozenset({"area", "name"}), POINTS),
    "records": (frozenset({"source_id", "as_written"}), POINTS),
}
COLOURS: Final = 12
# The layer whose features each name a source of their own.
RECORDS: Final = "records"
MADE_UP_ID: Final = "syn-"


class Unfit(Exception):
    """A layer that is not as the design gives it. The words name the file, never a value."""


def canonical(document: object) -> str:
    """The one way the desk writes JSON, so that the same data gives the same bytes."""
    return json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


# Shapes


def rings_of(geometry: Mapping[str, Any]) -> Iterator[list[Point]]:
    """Every ring of a polygon, and every line of a road, as a list of points."""
    shape, held = geometry["type"], geometry["coordinates"]
    if shape == "Point":
        yield [(held[0], held[1])]
    elif shape == "LineString":
        yield [(x, y) for x, y, *_ in held]
    elif shape in ("Polygon", "MultiLineString"):
        for ring in held:
            yield [(x, y) for x, y, *_ in ring]
    elif shape == "MultiPolygon":
        for polygon in held:
            for ring in polygon:
                yield [(x, y) for x, y, *_ in ring]


def bounds(features: Iterable[Mapping[str, Any]], margin: float = 0.0) -> list[float] | None:
    """West, south, east and north of some features, with a margin as a share of their size."""
    points = [
        point for feature in features for ring in rings_of(feature["geometry"]) for point in ring
    ]
    if not points:
        return None
    west, east = min(x for x, _ in points), max(x for x, _ in points)
    south, north = min(y for _, y in points), max(y for _, y in points)
    pad = margin * max(east - west, north - south)
    return [round(value, DECIMALS) for value in (west - pad, south - pad, east + pad, north + pad)]


def touching(cells: Iterable[Mapping[str, Any]]) -> dict[str, set[str]]:
    """For each cell, the cells it shares a side with.

    Two cells share a side when both hold the same two points next to each other.
    Output areas are published so: a border is one line, held by the cell on each side.
    """
    sides: dict[tuple[Point, Point], list[str]] = {}
    for cell in cells:
        for ring in rings_of(cell["geometry"]):
            for start, end in pairwise(ring):
                if start != end:
                    sides.setdefault((min(start, end), max(start, end)), []).append(cell["id"])
    beside: dict[str, set[str]] = {}
    for holders in sides.values():
        for one in holders:
            beside.setdefault(one, set()).update(other for other in holders if other != one)
    return beside


# One layer


def _rounded(held: Any) -> Any:
    if isinstance(held, float | int) and not isinstance(held, bool):
        return round(float(held), DECIMALS)
    if isinstance(held, list):
        return [_rounded(each) for each in cast(list[Any], held)]
    raise ValueError


def _feature(held: Any, layer: str, synthetic: bool, what: str) -> dict[str, Any]:
    allowed, shapes = LAYERS[layer]
    if not isinstance(held, dict) or cast(dict[str, Any], held).get("type") != "Feature":
        raise Unfit(f"{what} holds something that is not a feature")
    feature = cast(dict[str, Any], held)
    name, properties, geometry = (
        feature.get("id"),
        feature.get("properties"),
        feature.get("geometry"),
    )
    if not isinstance(name, str) or not name:
        raise Unfit(f"{what} holds a feature with no id")
    if synthetic and not name.startswith(MADE_UP_ID):
        raise Unfit(f"{what} is of the made-up city, and holds an id that does not begin syn-")
    if not isinstance(properties, dict) or not set(cast(dict[str, Any], properties)) <= allowed:
        raise Unfit(f"{what} holds a property that the design does not give to {layer}")
    for key, value in cast(dict[str, Any], properties).items():
        if key == "colour":
            if type(value) is not int or not 0 <= value < COLOURS:
                raise Unfit(f"{what} holds a colour that is not a number from 0 to {COLOURS - 1}")
        elif not isinstance(value, str):
            raise Unfit(f"{what} holds a property that is not text")
    drawn = cast(dict[str, Any], geometry) if isinstance(geometry, dict) else {}
    if drawn.get("type") not in shapes:
        raise Unfit(f"{what} holds a shape that {layer} is not drawn from")
    try:
        shape: dict[str, Any] = {
            "type": drawn["type"],
            "coordinates": _rounded(drawn.get("coordinates")),
        }
        points = [point for ring in rings_of(shape) for point in ring]
    except (ValueError, TypeError, IndexError) as error:
        raise Unfit(f"{what} holds a shape that cannot be read") from error
    if not points or not all(-180 <= x <= 180 and -90 <= y <= 90 for x, y in points):
        raise Unfit(
            f"{what} is not in WGS84, longitude first. The desk converts no coordinates: "
            "the areas build writes its layers in WGS84"
        )
    return {"type": "Feature", "id": name, "properties": properties, "geometry": shape}


def read(path: Path, *, synthetic: bool) -> Collection:
    """One layer, held to the design. Raises `Unfit`.

    The layer and the group are what the file's place says they are, so a request for
    `quillhaven/cells` can only ever be given the cells of that borough.
    """
    what = f"{path.parent.name}/{path.name}"
    layer, group = path.stem, path.parent.name
    if layer not in LAYERS:
        raise Unfit(f"{what} is not a layer the desk draws")
    if (layer == "boroughs") != (group == ALL):
        raise Unfit(f"{what}: the boroughs are in the group {ALL}, and nothing else is")
    try:
        held = json.loads(path.read_bytes())
    except (OSError, ValueError) as error:
        raise Unfit(f"{what} cannot be read as JSON") from error
    if not isinstance(held, dict) or cast(dict[str, Any], held).get("type") != "FeatureCollection":
        raise Unfit(f"{what} is not a FeatureCollection")
    collection = cast(dict[str, Any], held)
    said, features = collection.get("desk"), collection.get("features")
    if not isinstance(said, dict) or set(cast(dict[str, Any], said)) != {
        "layer",
        "group",
        "source_ids",
        "synthetic",
    }:
        raise Unfit(f"{what} does not say which layer it is, and from which sources")
    member = cast(dict[str, Any], said)
    sources = member["source_ids"]
    if (member["layer"], member["group"], member["synthetic"]) != (layer, group, synthetic):
        raise Unfit(f"{what} says it is another layer, of another group or another city")
    if (
        not isinstance(sources, list)
        or not sources
        or not all(isinstance(each, str) and each for each in cast(list[Any], sources))
    ):
        raise Unfit(f"{what} names no source")
    if not isinstance(features, list):
        raise Unfit(f"{what} holds no list of features")
    kept = [_feature(each, layer, synthetic, what) for each in cast(list[Any], features)]
    if len({feature["id"] for feature in kept}) != len(kept):
        raise Unfit(f"{what} holds an id twice")
    if layer == RECORDS:
        # Each record says which publisher wrote it, and its name is drawn as written.
        # The licence gate is asked about the sources a layer names, so a record of any
        # other source would be shown without anybody having been asked.
        of = [feature["properties"].get("source_id") for feature in kept]
        if not all(isinstance(each, str) and each for each in of):
            raise Unfit(f"{what} holds a record that does not say which source it is of")
        if not set(of) <= set(cast(list[str], sources)):
            raise Unfit(f"{what} holds a record of a source that the layer does not name")
    return {
        "type": "FeatureCollection",
        "desk": {
            "layer": layer,
            "group": group,
            "source_ids": sorted(set(cast(list[str], sources))),
            "synthetic": synthetic,
        },
        "features": kept,
    }


# A folder of layers


def found(folder: Path) -> dict[str, tuple[str, ...]]:
    """The groups of a folder of layers, each with its layers in the order they are drawn."""
    if not folder.is_dir():
        return {}
    groups: dict[str, tuple[str, ...]] = {}
    for group in sorted(each for each in folder.iterdir() if each.is_dir()):
        held = {file.stem for file in group.glob("*.geojson")}
        if held:
            groups[group.name] = tuple(layer for layer in LAYERS if layer in held)
    return groups


def read_all(folder: Path, *, synthetic: bool) -> dict[tuple[str, str], Collection]:
    """Every layer of a folder, by group and layer. Raises `Unfit` at the first that is not fit."""
    layers: dict[tuple[str, str], Collection] = {}
    if not folder.is_dir():
        return layers
    for group in sorted(each for each in folder.iterdir() if each.is_dir()):
        for file in sorted(group.glob("*.geojson")):
            layers[group.name, file.stem] = read(file, synthetic=synthetic)
    return layers


def copy(
    layers: Mapping[tuple[str, str], Collection],
    data: Path,
    *,
    synthetic: bool,
    registry: Path | None = None,
) -> int:
    """Write every layer under `<data>/layers/`, and say how many were written.

    The gate is asked about every source of every layer before anything is written.
    What an earlier fill left there is taken away, so that no layer outlives its draft.
    """
    sources = {each for layer in layers.values() for each in layer["desk"]["source_ids"]}
    gate.ask(sources, gate.GAZETTEER, synthetic=synthetic, registry=registry)
    target = data / "layers"
    if target.is_dir():
        for group in (each for each in target.iterdir() if each.is_dir()):
            for file in group.glob("*.geojson"):
                file.unlink()
    for (group, layer), collection in sorted(layers.items()):
        (target / group).mkdir(parents=True, exist_ok=True)
        (target / group / f"{layer}.geojson").write_text(
            canonical(collection) + "\n", encoding="utf-8"
        )
    return len(layers)
