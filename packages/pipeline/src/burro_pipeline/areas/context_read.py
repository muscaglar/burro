"""The publishers' files a layer and a flag are read from, each through the licence gate.

Every file is asked for under the use `gazetteer`, and the gate is asked before
the file is looked for. A source the gate refuses is never opened, however
useful it would be.

A file is read through its receipt, as every step of a build reads one. A
file may have none: the town centres had none until their list stated the
period of their data. A build may not rest on such a file. A
draft for a person's eyes may, and says so: with `draft` a file that has no
receipt is handed over marked as having none, and everything made from it
carries the mark. A file that has a receipt is never read that way.

| Read | From | Kept |
|---|---|---|
| Wards, and boroughs as drawn to the water | Boundary-Line | Code, name as written, outline |
| Town centres | The town centre boundaries | Id, name and class as written, outline |
| Road links | OS Open Roads | Id, class, what it is for, name, number, line |

London's wards and boroughs are told by the file's own code for the kind of
area, and never by where an outline lies. A name is kept exactly as written.

Nothing is written to the store. A file is copied out of it, and the copy is
held to its hash.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from burro_pipeline.areas import assign_shapes
from burro_pipeline.areas.assign_files import taken_out
from burro_pipeline.areas.assign_shapes import Box
from burro_pipeline.cells.shapes import Shape
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.store import StoreError, hash_file
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry import RegistryError
from burro_pipeline.registry.model import Use

USE = Use.GAZETTEER
# Where the copy of a file with no receipt is put, in the step's own folder.
NO_RECEIPT = "no-receipt"

BOUNDARY_LINE_MEMBER = "bdline_gb.gpkg"
WARDS, BOROUGHS = "district_borough_unitary_ward", "district_borough_unitary"
AREA_NAME, AREA_CODE, AREA_KIND = "Name", "Census_Code", "Area_Code"
# The file's codes for a ward and for a borough of London.
WARD_OF_LONDON, BOROUGH_OF_LONDON = "LBW", "LBO"

CENTRES = "town_centres"
CENTRE_ID, CENTRE_NAME, CENTRE_CLASS = "layerreference", "sitename", "classification"
# The classes that are of district rank or above, as the file writes them. The last holds
# the word for the rank and another beside it: the file does not say it is the same class,
# and it is read as one.
DISTRICT_OR_ABOVE = frozenset(
    {"International", "Metropolitan", "Major", "District", "District Centre"}
)

ROADS_MEMBER, LINKS = "oproad_gb.gpkg", "road_link"
LINK_ID, LINK_CLASS, LINK_KIND = "id", "road_classification", "road_function"
LINK_NAME, LINK_NUMBER = "name_1", "road_classification_number"


@dataclass(frozen=True)
class Taken:
    """One publisher's file, as a step is handed it."""

    source_id: str
    file_id: str
    sha256: str
    # The publisher's label for the edition. Empty where the file has no receipt.
    edition: str
    # Where the checked copy is.
    path: Path
    # The file as the shared readers take one. Nothing where the file has no receipt.
    opened: Opened | None

    @property
    def has_receipt(self) -> bool:
        return self.opened is not None


@dataclass(frozen=True)
class Outlined:
    """One ward, or one town centre: the publisher's id, the name as written, the outline."""

    record_id: str
    name: str
    shape: Shape
    # The class of a town centre, as written. Empty for a ward.
    rank: str = ""

    @property
    def counts(self) -> bool:
        """Whether a town centre is of district class or above, as the design asks."""
        return self.rank in DISTRICT_OR_ABOVE


@dataclass(frozen=True)
class Link:
    """One link of the roads."""

    record_id: str
    # The class of the road, and what the road is for, each as the file writes it.
    of_class: str
    kind: str
    name: str
    number: str
    shape: Shape


def _text(value: object) -> str:
    """A field as text, exactly as the file holds it. Empty where the file holds nothing."""
    return "" if value is None else str(value)


def _without_receipt(inputs: Inputs, source_id: str) -> Taken:
    """The one file of a source that the store holds and no receipt describes."""
    try:
        held = [file for file in inputs.store.list() if file.source_id == source_id]
        if len(held) != 1:
            raise LockError("file_is_in_the_vault", source_id)
        file_id = file_id_of(held[0].sha256)
        to = inputs.work / NO_RECEIPT / file_id / held[0].name
        if not (to.is_file() and hash_file(to)[0] == held[0].sha256):
            to.unlink(missing_ok=True)
            inputs.store.get(held[0].sha256, to)
    except (StoreError, OSError):
        raise LockError("file_is_in_the_vault", source_id) from None
    return Taken(source_id, file_id, held[0].sha256, "", to, None)


def take(
    inputs: Inputs,
    source_id: str,
    *,
    edition: str | None = None,
    named: Callable[[str], bool] | None = None,
    draft: bool = False,
) -> Taken:
    """The one file of a source, through the gate, its receipt and its hash.

    With `draft`, a source that has no receipt at all is read from the store
    as it lies, and is marked as having none. The gate is asked first either
    way.
    """
    try:
        inputs.registry.require(source_id, USE)
    except RegistryError as error:
        raise LockError("gate_refuses", source_id, str(error)) from None
    if draft and not any(receipt.source_id == source_id for receipt in inputs.receipts):
        return _without_receipt(inputs, source_id)
    opened = inputs.open(source_id, USE, edition=edition, named=named)
    receipt = opened.receipt
    return Taken(source_id, receipt.file_id, receipt.sha256, receipt.edition, opened.path, opened)


def _inside(taken: Taken, member: str) -> Path:
    """The GeoPackage inside a zip, taken out beside it. Only a file with a receipt is a zip."""
    if taken.opened is None:
        raise LockError("input_has_one_receipt", taken.source_id)
    return taken_out(taken.opened, member)


def _outlined(rows: list[assign_shapes.Row], file_id: str) -> list[Outlined]:
    found = [
        Outlined(_text(values[0]), _text(values[1]), shape, _text(values[2]) if values[2:] else "")
        for values, shape in rows
    ]
    shapes = [each.shape for each in found]
    if not all(each.record_id and each.name for each in found) or not assign_shapes.are_shapes(
        shapes
    ):
        raise LockError("input_is_as_described", file_id, "an outline lacks a code or a name")
    if len({each.record_id for each in found}) != len(found):
        raise LockError("input_is_as_described", file_id, "a code is held twice")
    return sorted(found, key=lambda each: each.record_id)


def wards(taken: Taken) -> list[Outlined]:
    """Every ward of London in Boundary-Line, in the order of their codes."""
    rows = assign_shapes.read_layer(
        _inside(taken, BOUNDARY_LINE_MEMBER),
        taken.file_id,
        WARDS,
        (AREA_CODE, AREA_NAME),
        where=(AREA_KIND, WARD_OF_LONDON),
    )
    return _outlined(rows, taken.file_id)


def boroughs_to_the_water(taken: Taken) -> list[Shape]:
    """Every borough of London as Boundary-Line draws it: to the middle of tidal water."""
    rows = assign_shapes.read_layer(
        _inside(taken, BOUNDARY_LINE_MEMBER),
        taken.file_id,
        BOROUGHS,
        (AREA_CODE, AREA_NAME),
        where=(AREA_KIND, BOROUGH_OF_LONDON),
    )
    return [each.shape for each in _outlined(rows, taken.file_id)]


def centres(taken: Taken) -> list[Outlined]:
    """Every town centre of the file, in the order of their ids."""
    rows = assign_shapes.read_layer(
        taken.path, taken.file_id, CENTRES, (CENTRE_ID, CENTRE_NAME, CENTRE_CLASS)
    )
    return _outlined(rows, taken.file_id)


def links(taken: Taken, box: Box) -> list[Link]:
    """Every link of the roads whose own box meets a box, in the order of the file."""
    rows = assign_shapes.read_layer(
        _inside(taken, ROADS_MEMBER),
        taken.file_id,
        LINKS,
        (LINK_ID, LINK_CLASS, LINK_KIND, LINK_NAME, LINK_NUMBER),
        box=box,
    )
    return [
        Link(*(_text(value) for value in values), shape=shape)
        for values, shape in rows
        if not shape.is_empty
    ]
