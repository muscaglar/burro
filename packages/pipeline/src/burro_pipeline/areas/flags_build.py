"""Flag a draft: read the ground through the gate, read the draft, and write what to look at.

| Step | What happens |
|---|---|
| Ask | The gate is asked about each source, for `gazetteer`, before its file is looked for |
| Ground | The output areas, their boroughs and wards, main roads and town centres are read |
| Homes | The count of homes is read only if the gate gives it. If not, cells are counted |
| Draft | The curated files of the draft are read, as section 5 of the areas design gives them |
| Flag | Every rule of `flags.py` is run, and the areas are put in order |
| Write | The flags, the order and the rules go to a folder that is no part of the repository |

A source the gate refuses is not read, and what is lost with it is written down
in the notes. A file with no receipt is read for a draft alone, and every area
that rests on it is flagged for it.

The ground is places and land. Nothing here reads who lives anywhere.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from burro_pipeline.areas import (
    assign_shapes,
    context,
    context_files,
    context_read,
    flags,
    flags_files,
    flags_ground,
    flags_order,
)
from burro_pipeline.areas.context_read import Link, take
from burro_pipeline.areas.flags import Draft, Flag, Rules
from burro_pipeline.areas.flags_ground import Centre, Ground
from burro_pipeline.areas.flags_order import Placed
from burro_pipeline.cells import spine
from burro_pipeline.cells.shapes import Shape
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import RegistryError

# What is lost where a source cannot be read, in words for the notes.
LOST: Mapping[str, str] = {
    spine.HOMES: "Homes are not counted: an area's size, and what is at stake, is counted in "
    "output areas.",
    context.BOUNDARY_LINE: "No ward was read: a border is held to boroughs and main roads alone.",
    context.OPEN_ROADS: "No road was read: a border is held to boroughs and wards alone.",
    context.TOWN_CENTRES: "No town centre was read: no area is flagged for holding two.",
}


@dataclass
class Read:
    """The ground as it was read, and what could not be."""

    ground: Ground
    outlines: Mapping[str, Shape]
    main_roads: list[Shape] = field(default_factory=list[Shape])
    # Every link of the roads that was read, the local roads among them.
    links: list[Link] = field(default_factory=list[Link])
    centres: list[Centre] = field(default_factory=list[Centre])
    homes: dict[str, int] | None = None
    notes: dict[str, str] = field(default_factory=dict[str, str])
    # Every source that was read with no receipt.
    unreceipted: list[str] = field(default_factory=list[str])


@dataclass(frozen=True)
class Flagged:
    """What a run found."""

    draft: Draft
    flags: list[Flag]
    areas: list[Placed]
    boroughs: list[Placed]
    said: Mapping[str, object]


def _homes(inputs: Inputs, notes: dict[str, str]) -> dict[str, int] | None:
    """The homes of every output area, if the gate gives them for this use."""
    try:
        inputs.registry.require(spine.HOMES, context.USE)
    except RegistryError as error:
        notes[spine.HOMES] = f"{LOST[spine.HOMES]} The gate said: {error}"
        return None
    try:
        opened = inputs.open(
            spine.HOMES, context.USE, named=lambda name: spine.HOMES_TABLE in name.lower()
        )
        return spine.read_homes(opened)
    except LockError as error:
        notes[spine.HOMES] = f"{LOST[spine.HOMES]} {error}"
        return None


def read_ground(inputs: Inputs, *, draft: bool) -> Read:
    """The ground, from the files of the build. One file that fails does not stop the rest."""
    made = context_files.Made(answers={})
    london = context_files.read_london(inputs, made)
    notes: dict[str, str] = {}
    wards: dict[str, Shape] = {}
    try:
        file = take(inputs, context.BOUNDARY_LINE)
        wards = {ward.record_id: ward.shape for ward in context_read.wards(file)}
    except LockError as error:
        notes[context.BOUNDARY_LINE] = f"{LOST[context.BOUNDARY_LINE]} {error}"
    ground = flags_ground.ground_of(london.outlines, london.borough_of, london.names, wards)
    read = Read(ground, london.outlines, notes=notes)
    try:
        box = assign_shapes.box_of(list(london.boroughs.values()), context.MARGIN)
        read.links = context_read.links(take(inputs, context.OPEN_ROADS), box)
        read.main_roads = [
            link.shape for link in read.links if link.of_class in flags_ground.MAIN_ROADS
        ]
    except LockError as error:
        notes[context.OPEN_ROADS] = f"{LOST[context.OPEN_ROADS]} {error}"
    try:
        file = take(inputs, context.TOWN_CENTRES, draft=draft)
        if not file.has_receipt:
            read.unreceipted.append(file.source_id)
        read.centres = [
            Centre(centre.record_id, centre.name, centre.shape)
            for centre in context_read.centres(file)
            if centre.counts
        ]
    except LockError as error:
        notes[context.TOWN_CENTRES] = f"{LOST[context.TOWN_CENTRES]} {error}"
    read.homes = _homes(inputs, notes)
    return read


def flag(
    inputs: Inputs,
    read: Read,
    drafted: Path,
    out: Path,
    *,
    rules: Rules | None = None,
    queues: Sequence[str] = (flags.BORDERS,),
) -> Flagged:
    """Flag the draft in a folder, against ground that was read, and write what was found.

    Only borders are flagged unless more is asked for: the draft of names
    flags the names, where they are read.
    """
    rules = rules or Rules()
    receipted = {receipt.source_id for receipt in inputs.receipts}
    given = flags_files.read_given(drafted)
    every = flags_files.read_named(drafted, inputs.registry, receipted)
    held = {row.area for row in given.values()}
    named = {area_id: row for area_id, row in every.items() if area_id in held}
    draft = flags_ground.draft_of(
        read.ground,
        given,
        named,
        outlines=read.outlines,
        main_roads=read.main_roads,
        centres=read.centres,
        homes=read.homes,
        rules=rules,
    )
    found = flags.flags_of(draft, rules, queues)
    areas = flags_order.areas_in_order(draft, found, rules)
    groups = {code: context.group_of(name) for code, name in read.ground.borough_names.items()}
    boroughs = flags_order.boroughs_in_order(draft, areas, groups)
    notes = dict(read.notes)
    if len(named) < len(every):
        notes["names_with_no_output_area"] = (
            f"{len(every) - len(named)} names of {flags_files.AREAS} hold no output area in "
            "the draft, and are left out: the draft made each part of another area."
        )
    if read.unreceipted:
        notes["no_receipt"] = (
            "Read with no receipt, for a draft alone: " + ", ".join(sorted(read.unreceipted)) + "."
        )
    said = flags_files.write(out, draft, found, areas, boroughs, rules=rules, notes=notes)
    return Flagged(draft, found, areas, boroughs, said)
