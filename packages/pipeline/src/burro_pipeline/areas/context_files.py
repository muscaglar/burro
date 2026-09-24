"""Make the layers a reviewer sees behind a border, from the files of a build.

The gate is asked about every source of every layer before any file is looked
for. A layer is made only where the gate gave every source of it, and what it
refused is written down with what the desk can show in its place. Every file
is then read for the use `gazetteer`, through its receipt.

A file may have no receipt, as the town centres had none until their list
stated the period of their data. A build may not rest on it. For a draft, and
for a draft alone, it is read where it lies and every layer made from it says so.

What is written, to a folder that is no part of the repository:

| Path | Holds |
|---|---|
| `layers/all/boroughs.geojson` | Every borough's outline |
| `layers/<borough>/<layer>.geojson` | A layer the desk draws, for one borough and 500 m round it |
| `layers/<borough>/cells.geojson`, `areas`, `seeds` | The draft itself, where there is one |
| `not_yet_drawn/<borough>/<layer>.geojson` | A layer the desk has no name for yet |
| `boroughs.csv` | Every borough, for the desk to ask how well a reviewer knows it |
| `layers.json` | What the gate said, what was made and how large, and what was not made |

**The ground of a borough's group.** The desk shows an area under the borough
its draft names for it. So where there is a draft, a borough's group holds the
borough, every area the draft names it for, every area most of whose output
areas lie in it, and 500 m round them all. An area that runs into the next
borough is then drawn whole, with the roads and the wards behind it.

Nothing is written to the store, and nothing here is committed.
"""

import csv
import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

from burro_pipeline.areas import (
    assign_shapes,
    context,
    context_names,
    context_read,
    context_shapes,
    flags_files,
    flags_ground,
)
from burro_pipeline.areas.assign_shapes import Box
from burro_pipeline.areas.context import ALL, Answer, Borough, Drawn, Layer
from burro_pipeline.areas.context_read import Link, Taken, take
from burro_pipeline.cells import shapes, spine
from burro_pipeline.cells.shapes import Shape
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Inputs

OUTLINES_EDITION = "BGC V2"
# The roads that are drawn, by what the file says each is for. A local road is left out:
# London holds over a hundred thousand, and the edge of a cell already runs down most.
ROADS_DRAWN = frozenset({"Motorway", "A Road", "B Road", "Minor Road"})
# How far beyond London a layer is read, in metres: the margin of a borough's group.
BEYOND = context.MARGIN


@dataclass(frozen=True)
class Written:
    """One file that was written."""

    path: str
    layer: str
    group: str
    features: int
    bytes: int
    sha256: str


@dataclass
class Made:
    """What a run made, and what it could not."""

    answers: dict[str, Answer]
    written: list[Written] = field(default_factory=list[Written])
    # The sources of each layer that was read with no receipt.
    unreceipted: dict[str, list[str]] = field(default_factory=dict[str, list[str]])
    # Why a layer the gate gave was still not made, by its name.
    not_made: dict[str, str] = field(default_factory=dict[str, str])
    inputs: dict[str, Taken] = field(default_factory=dict[str, Taken])
    boroughs: list[Borough] = field(default_factory=list[Borough])


@dataclass(frozen=True)
class London:
    """The ground every layer is cut to."""

    outlines: Mapping[str, Shape]
    borough_of: Mapping[str, str]
    names: Mapping[str, str]
    boroughs: Mapping[str, Shape]
    # What each borough's group is cut to, before its margin. It is the borough, and
    # with a draft the areas that are shown under it too.
    grounds: Mapping[str, Shape] = field(default_factory=dict[str, Shape])

    def ground_of(self, code: str) -> Shape:
        return self.grounds.get(code, self.boroughs[code])


def read_london(inputs: Inputs, made: Made) -> London:
    """London's output areas and boroughs, from the lookup and the generalised outlines."""
    lookup = take(inputs, context.LOOKUP, edition=spine.LOOKUP_EDITION)
    boundaries = take(inputs, context.OUTLINES, edition=OUTLINES_EDITION)
    if lookup.opened is None or boundaries.opened is None:
        raise LockError("input_has_one_receipt", context.LOOKUP)
    rows = spine.read_lookup(lookup.opened)
    borough_of = {row[spine.OA]: row[spine.BOROUGH] for row in rows}
    names = {row[spine.BOROUGH]: row[spine.BOROUGH_NAME] for row in rows}
    outlines = shapes.read_outlines(boundaries.opened, spine.OA, set(borough_of))
    if not rows or len(borough_of) != len(rows) or set(outlines) != set(borough_of):
        raise LockError("input_is_as_described", boundaries.file_id, "an outline is missing")
    made.inputs |= {lookup.file_id: lookup, boundaries.file_id: boundaries}
    return London(outlines, borough_of, names, context.borough_outlines(outlines, borough_of))


def roads_drawn(links: Sequence[Link]) -> list[Drawn]:
    """The roads to draw: the links of one name and one kind joined into one line.

    A road is called by its name where the file gives one, and by its number
    where not. It is known by the id of the first of its links, in the order
    of their ids.
    """
    together: dict[tuple[str, str], list[Link]] = {}
    for link in links:
        if link.kind in ROADS_DRAWN:
            together.setdefault((link.kind, link.name or link.number), []).append(link)
    found: list[Drawn] = []
    for (kind, name), held in sorted(together.items()):
        first = min(link.record_id for link in held)
        line = context_shapes.joined_lines([link.shape for link in held])
        found.append(Drawn(first, {"class": kind, "name": name}, line))
    return found


def _write(out: Path, folder: str, layer: Layer, group: str, things: Sequence[Drawn]) -> Written:
    path = out / folder / group / f"{layer.name}.geojson"
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (context.canonical(context.collection(layer, group, things)) + "\n").encode()
    path.write_bytes(content)
    return Written(
        path=path.relative_to(out).as_posix(),
        layer=layer.name,
        group=group,
        features=len(things),
        bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
    )


def _folder(layer: Layer) -> str:
    return "layers" if layer.desk_draws_it else "not_yet_drawn"


def _each_borough(
    out: Path, london: London, layer: Layer, things: Sequence[Drawn], made: Made
) -> None:
    fewer = context.thinned(layer, things)
    grounds = {code: london.ground_of(code) for code in london.boroughs}
    for group, near in context.by_borough(layer, fewer, grounds, london.names).items():
        if near:
            made.written.append(_write(out, _folder(layer), layer, group, near))


def _read(made: Made, layer: str, file: Taken) -> Taken:
    made.inputs[file.file_id] = file
    if not file.has_receipt:
        made.unreceipted.setdefault(layer, []).append(file.source_id)
    return file


# The layers that are the draft itself.
OF_THE_DRAFT = ("cells", "areas", "seeds")
NO_DRAFT = "No draft was handed over."


def build(inputs: Inputs, out: Path, *, draft: bool, drafted: Path | None = None) -> Made:
    """Make every layer the gate gives, and write them with what was and was not made.

    `draft` says whether a file with no receipt may be read. `drafted` is the
    folder of a draft, where there is one: its cells, areas and seeds are then
    drawn too. A layer whose file cannot be read is left out and the reason is
    kept: one layer that fails does not stop the rest.
    """
    asked = [source for layer in context.LAYERS for source in layer.sources]
    asked += [wanted.source for wanted in context.WANTED]
    made = Made(answers=context.ask(inputs.registry, asked))
    given = {layer.name for layer in context.LAYERS if context.may_be_made(layer, made.answers)}
    if "boroughs" not in given:
        return made
    london = read_london(inputs, made)
    made.boroughs = context.boroughs_to_ask(london.outlines, london.borough_of, london.names)
    box = assign_shapes.box_of(list(london.boroughs.values()), BEYOND)
    of_the_draft: dict[str, list[Drawn]] = {}
    if drafted is not None:
        of_the_draft = _of_the_draft(inputs, made, london, drafted)
        london = replace(london, grounds=grounds_of(london, drafted, of_the_draft["areas"]))

    boroughs = context.layer_named("boroughs")
    outlines = [
        Drawn(code, {"name": london.names[code]}, shape)
        for code, shape in sorted(london.boroughs.items())
    ]
    made.written.append(_write(out, _folder(boroughs), boroughs, ALL, outlines))

    makers: dict[str, Callable[[], list[Drawn]]] = {
        "wards": lambda: _wards(inputs, made),
        "centres": lambda: _centres(inputs, made, draft),
        "roads": lambda: roads_drawn(_links(inputs, made, box)),
        "names": lambda: _names(inputs, made, box),
        "water": lambda: _water(inputs, made, london),
    }
    for name, maker in makers.items():
        if name not in given:
            continue
        try:
            _each_borough(out, london, context.layer_named(name), maker(), made)
        except LockError as error:
            made.not_made[name] = str(error)
    if drafted is None:
        made.not_made |= dict.fromkeys((name for name in OF_THE_DRAFT if name in given), NO_DRAFT)
    for name, things in of_the_draft.items():
        if name in given:
            _each_borough(out, london, context.layer_named(name), things, made)
    write_list(out, made)
    return made


def grounds_of(london: London, drafted: Path, areas: Sequence[Drawn]) -> dict[str, Shape]:
    """What each borough's group is cut to: the borough, and the areas shown under it."""
    code_of = {name: code for code, name in london.names.items()}
    shown: dict[str, set[str]] = {code: set() for code in london.boroughs}
    for area_id, borough in flags_files.read_boroughs(drafted).items():
        if borough in code_of:
            shown[code_of[borough]].add(area_id)
    cells: dict[str, dict[str, int]] = {}
    for oa, row in flags_files.read_given(drafted).items():
        held = cells.setdefault(row.area, {})
        held[london.borough_of[oa]] = held.get(london.borough_of[oa], 0) + 1
    for area_id, held in cells.items():
        shown[sorted(held, key=lambda code: (-held[code], code))[0]].add(area_id)
    outline = {area.record_id: area.shape for area in areas}
    return {
        code: shapes.joined(
            [
                london.boroughs[code],
                *(outline[each] for each in sorted(areas_of) if each in outline),
            ]
        )
        for code, areas_of in sorted(shown.items())
    }


def _of_the_draft(
    inputs: Inputs, made: Made, london: London, drafted: Path
) -> dict[str, list[Drawn]]:
    """The cells, the areas and the seeds of a draft, as things to draw.

    It stops where the draft leaves an output area of London in no area: a map
    with a hole in it would show a border that is not there. A seed is drawn
    under the name its own record writes, and under none where the draft does
    not say: a name is shown only where a publisher's record puts it.
    """
    area_of = {oa: row.area for oa, row in flags_files.read_given(drafted).items()}
    if set(area_of) != set(london.outlines):
        raise flags_files.Unfit(f"{flags_files.GIVEN} does not hold every output area once")
    receipted = {receipt.source_id for receipt in inputs.receipts}
    named = flags_files.read_named(drafted, inputs.registry, receipted)
    beside: dict[str, set[str]] = {area_id: set() for area_id in set(area_of.values())}
    for a, b in flags_ground.shared_sides(london.outlines):
        if area_of[a] != area_of[b]:
            beside[area_of[a]].add(area_of[b])
            beside[area_of[b]].add(area_of[a])
    colours = context.colours_of({area: sorted(others) for area, others in beside.items()})
    names = {area_id: named[area_id].name if area_id in named else "" for area_id in beside}
    boroughs = {oa: london.names[london.borough_of[oa]] for oa in area_of}
    seeds = [
        Drawn(
            f"seed-{area_id}",
            {"area": area_id, "name": row.seed_name},
            context_shapes.point(row.seed),
        )
        for area_id, row in sorted(named.items())
        if row.seed is not None and area_id in beside
    ]
    if any(row.unreceipted for row in named.values()):
        made.unreceipted.setdefault("seeds", []).extend(
            sorted({source for row in named.values() for source in row.unreceipted})
        )
    return {
        "cells": context.cells_drawn(london.outlines, area_of, boroughs, colours),
        "areas": context.areas_drawn(london.outlines, area_of, names),
        "seeds": seeds,
    }


def _links(inputs: Inputs, made: Made, box: Box) -> list[Link]:
    return context_read.links(_read(made, "roads", take(inputs, context.OPEN_ROADS)), box)


def _names(inputs: Inputs, made: Made, box: Box) -> list[Drawn]:
    file = _read(made, "names", take(inputs, context.OPEN_NAMES))
    return [
        Drawn(
            each.record_id,
            {"name": each.name, "kind": each.kind},
            context_shapes.point((each.x, each.y)),
        )
        for each in context_names.read(file.path, file.file_id, box)
    ]


def _wards(inputs: Inputs, made: Made) -> list[Drawn]:
    file = _read(made, "wards", take(inputs, context.BOUNDARY_LINE))
    return [
        Drawn(ward.record_id, {"name": ward.name}, ward.shape) for ward in context_read.wards(file)
    ]


def _centres(inputs: Inputs, made: Made, draft: bool) -> list[Drawn]:
    file = _read(made, "centres", take(inputs, context.TOWN_CENTRES, draft=draft))
    return [
        Drawn(centre.record_id, {"name": centre.name, "class": centre.rank}, centre.shape)
        for centre in context_read.centres(file)
    ]


def _water(inputs: Inputs, made: Made, london: London) -> list[Drawn]:
    file = _read(made, "water", take(inputs, context.BOUNDARY_LINE))
    to_the_river = context_read.boroughs_to_the_water(file)
    water = context.tidal_water(to_the_river, list(london.outlines.values()))
    return [] if water is None else [Drawn("tidal-water", {"name": ""}, water)]


# What was made, written down


def said(made: Made) -> dict[str, object]:
    """What `layers.json` holds: the gate's answers, the layers and their sizes, what is missing."""
    by_layer: dict[str, list[Written]] = {}
    for written in made.written:
        by_layer.setdefault(written.layer, []).append(written)
    layers: list[dict[str, object]] = []
    for layer in context.LAYERS:
        files = by_layer.get(layer.name, [])
        refused = [
            source
            for source in layer.sources
            if source not in made.answers or not made.answers[source].given
        ]
        layers.append(
            {
                "layer": layer.name,
                "sources": list(layer.sources),
                "use": str(context.USE),
                "the_gate_gave_it": not refused,
                "made": bool(files),
                "why_not": made.not_made.get(layer.name, ""),
                "the_desk_draws_it": layer.desk_draws_it,
                "rests_on_a_file_with_no_receipt": sorted(
                    set(made.unreceipted.get(layer.name, []))
                ),
                "thinned_by_metres": layer.thinned_by,
                "files": len(files),
                "features": sum(each.features for each in files),
                "bytes": sum(each.bytes for each in files),
                "largest_file_bytes": max((each.bytes for each in files), default=0),
            }
        )
    return {
        "use": str(context.USE),
        "margin_metres": context.MARGIN,
        "the_gate": [asdict(answer) for _, answer in sorted(made.answers.items())],
        "layers": layers,
        "not_given": [
            {
                "what": wanted.what,
                "source": wanted.source,
                "the_gate_said": made.answers[wanted.source].words,
                "in_its_place": wanted.in_its_place,
                "to_decide": wanted.to_decide,
            }
            for wanted in context.WANTED
            if not made.answers[wanted.source].given
        ],
        "read": [
            {
                "source_id": file.source_id,
                "file_id": file.file_id,
                "sha256": file.sha256,
                "edition": file.edition,
                "has_receipt": file.has_receipt,
            }
            for _, file in sorted(made.inputs.items())
        ],
        "boroughs": len(made.boroughs),
        "files": [asdict(written) for written in sorted(made.written, key=lambda w: w.path)],
    }


def write_list(out: Path, made: Made) -> None:
    """Write the list of boroughs and the record of what was made."""
    out.mkdir(parents=True, exist_ok=True)
    with (out / "boroughs.csv").open("w", encoding="utf-8", newline="") as file:
        table = csv.writer(file, lineterminator="\n")
        table.writerow(("queue", "item", "group", "name", "code", "output_areas", "hectares"))
        for borough in made.boroughs:
            table.writerow(
                (
                    "know",
                    borough.group,
                    ALL,
                    borough.name,
                    borough.code,
                    borough.output_areas,
                    format(borough.hectares, ".1f"),
                )
            )
    (out / "layers.json").write_text(
        json.dumps(said(made), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
