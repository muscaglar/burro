"""A file of the planning data platform: one reader for every dataset it lays out the same way.

The platform gives each of its datasets as one file for England, in GeoJSON: a
collection of features, each a record with its properties and where it is. Two
measures read one each, the conservation areas and the listed buildings. The
two are laid out alike, so they are read by this one reader.

What a record is, as the files fetched on 2026-09-24 hold it:

| Property | What it holds | Read |
|---|---|---|
| `dataset` | The name of the dataset, the same in every record | To hold the file to |
| `entity` | The platform's own number for the record | Yes |
| `organisation-entity` | The platform's number for who provided the record | Yes |
| `quality` | `authoritative` or `some`. The file does not say what either means | Yes |
| `end-date` | The day a record ended, or nothing | Yes |
| `entry-date` | The day the platform entered the record | Yes |
| `listed-building-grade` | The grade of a listed building. Not in every record | Where asked for |
| `name`, `reference`, `notes` | What the record is called, and what is said of it | Never |
| `documentation-url`, `document-url` | A page about the one record | Never |
| `start-date`, `designation-date`, `legislation` | When and how the record was made | Never |
| `prefix`, `typology` | The same in every record | Never |

A name is never read: the name of a listed building is often an address, and
may be the name of a business. A record is never written anywhere. What leaves
this module is a count, or an outline with its provider.

**The provider is kept with every record.** The publisher says the dataset of
conservation areas holds records that the ministry made, which are being
replaced with data from authoritative sources. So each record carries the
number of its provider and its quality, and a measure can tell the two apart.
One provider may give records of both qualities. The file does
not say who a number is: that is in another dataset of the platform, which is
not read.

How the file is read. It is read a piece at a time and never held whole: the
file of listed buildings is some 200 MB. The reader finds the list of features
and takes them one by one, however the file breaks its lines. A record outside
the box that is asked for is counted and let go before anything is made of it.

The file is held to its shape. The step stops where it is not a collection of
features, or where its name is not the dataset's. A record in the box is held
to its shape too: the step stops where one lacks a property that is read, holds
one that is not text, gives a quality the files are not known to hold, or
gives a day that is not a day.
"""

import json
import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TextIO, cast

from burro_pipeline.derive.heritage_shapes import Box, box_in_degrees, touch
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Opened

# The properties every record holds, by the names the file gives them.
DATASET, ENTITY, PROVIDER = "dataset", "entity", "organisation-entity"
QUALITY, ENDED, ENTERED = "quality", "end-date", "entry-date"
ALWAYS = (DATASET, ENTITY, PROVIDER, QUALITY, ENDED, ENTERED)
# The two values of `quality` the files hold.
AUTHORITATIVE, SOME = "authoritative", "some"
QUALITIES = frozenset({AUTHORITATIVE, SOME})
# The members of the collection that may stand before its features.
COLLECTION, FEATURE, FEATURES = "FeatureCollection", "Feature", '"features"'
A_DAY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
A_NUMBER = re.compile(r"[0-9]{1,12}")
# How much of the file is read at once, in characters.
AT_ONCE = 1 << 20
# The list of features is looked for in this much of the start of the file, and no further.
THE_START = 1 << 22
SPACE = " \t\r\n"


@dataclass(frozen=True)
class Record:
    """One record of a dataset, as far as it is read. It holds no name."""

    entity: str
    # The platform's number for who provided the record, and what it says of the record.
    provider: str
    quality: str
    # The day the record ended, or nothing, and the day the platform entered it.
    ended: str
    entered: str
    # The properties a measure asked for beside these, each as text, empty where there is none.
    asked: Mapping[str, str]
    # Where it is, as the file writes it: the kind of geometry, and longitude and latitude.
    kind: str
    coordinates: object

    def live_on(self, day: str) -> bool:
        """Whether the record had not ended on a day. A record that ends later is live."""
        return not self.ended or self.ended > day


@dataclass(frozen=True)
class Read:
    """What was read of a file: the records in the box, and what was counted on the way."""

    records: tuple[Record, ...]
    # Every record the file holds, wherever it is.
    in_the_file: int
    # Records that say nothing of where they are. They are in no box.
    nowhere: int


def _refuse(opened: Opened, why: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, why)


class _Pieces:
    """The text of a file, read a piece at a time."""

    def __init__(self, text: TextIO) -> None:
        self._text = text
        self.held = ""
        self.at = 0
        self.ended = False

    def more(self) -> bool:
        """Read another piece. It says whether there was one."""
        piece = self._text.read(AT_ONCE)
        if not piece:
            self.ended = True
            return False
        # What was taken is let go, so that the file is never held whole.
        self.held = self.held[self.at :] + piece
        self.at = 0
        return True

    def past_space(self) -> str:
        """Step over space, and give the next character, or nothing at the end of the file."""
        while True:
            while self.at < len(self.held) and self.held[self.at] in SPACE:
                self.at += 1
            if self.at < len(self.held):
                return self.held[self.at]
            if not self.more():
                return ""


def _start(pieces: _Pieces, dataset: str, opened: Opened) -> None:
    """Read to the first feature, and hold what stands before it to a collection of the dataset."""
    while FEATURES not in pieces.held:
        if len(pieces.held) > THE_START or not pieces.more():
            raise _refuse(opened, "it is not a collection of features")
    before, _, after = pieces.held.partition(FEATURES)
    try:
        said = json.loads(before.rstrip(SPACE).removesuffix(",") + "}")
    except ValueError:
        raise _refuse(opened, "it is not a collection of features") from None
    if not isinstance(said, dict) or cast("dict[str, Any]", said).get("type") != COLLECTION:
        raise _refuse(opened, "it is not a collection of features")
    if cast("dict[str, Any]", said).get("name") != dataset:
        raise _refuse(opened, "it is not the dataset that is read")
    pieces.held, pieces.at = after, 0
    if pieces.past_space() != ":":
        raise _refuse(opened, "it is not a collection of features")
    pieces.at += 1
    if pieces.past_space() != "[":
        raise _refuse(opened, "it is not a collection of features")
    pieces.at += 1


def _features(text: TextIO, dataset: str, opened: Opened) -> Iterator[dict[str, Any]]:
    """Every feature of a collection, one by one, however the file breaks its lines."""
    pieces = _Pieces(text)
    _start(pieces, dataset, opened)
    decoder = json.JSONDecoder()
    while True:
        first = pieces.past_space()
        if first == ",":
            pieces.at += 1
            continue
        if first == "]":
            pieces.at += 1
            break
        if first != "{":
            raise _refuse(opened, "its features are not a list of records")
        while True:
            # A record is read whole or not at all: it ends with its own closing brace.
            try:
                feature, end = decoder.raw_decode(pieces.held, pieces.at)
                break
            except ValueError:
                if not pieces.more():
                    raise _refuse(opened, "a record is cut short") from None
        pieces.at = end
        if not isinstance(feature, dict):
            raise _refuse(opened, "its features are not a list of records")
        yield cast("dict[str, Any]", feature)
    if pieces.past_space() != "}":
        raise _refuse(opened, "it is not a collection of features")
    pieces.at += 1
    if pieces.past_space():
        raise _refuse(opened, "it holds more than one collection")


def _text_of(properties: Mapping[str, Any], name: str, opened: Opened, needed: bool) -> str:
    if name not in properties or properties[name] is None:
        if needed:
            raise _refuse(opened, "a record lacks a property that is read")
        return ""
    value = properties[name]
    if not isinstance(value, str):
        raise _refuse(opened, "a property is not text")
    return value


def _where(feature: Mapping[str, Any], opened: Opened) -> tuple[str, list[Any]] | None:
    """Where a record is, as the file writes it, or nothing where it does not say."""
    if feature.get("type") != FEATURE:
        raise _refuse(opened, "its features are not a list of records")
    geometry = feature.get("geometry")
    if geometry is None:
        return None
    if not isinstance(geometry, dict):
        raise _refuse(opened, "a geometry is not a geometry")
    where = cast("dict[str, Any]", geometry)
    kind, coordinates = where.get("type"), where.get("coordinates")
    if not isinstance(kind, str) or not isinstance(coordinates, list):
        raise _refuse(opened, "a geometry is not a geometry")
    return kind, cast("list[Any]", coordinates)


def _record(
    feature: Mapping[str, Any],
    where: tuple[str, list[Any]],
    dataset: str,
    asked: Sequence[str],
    opened: Opened,
) -> Record:
    """One record, held to its shape."""
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        raise _refuse(opened, "its features are not a list of records")
    held = cast("dict[str, Any]", properties)
    always = {name: _text_of(held, name, opened, needed=True) for name in ALWAYS}
    if always[DATASET] != dataset:
        raise _refuse(opened, "a record is of another dataset")
    if not A_NUMBER.fullmatch(always[ENTITY]) or not A_NUMBER.fullmatch(always[PROVIDER]):
        raise _refuse(opened, "a number of the platform is not a number")
    if always[QUALITY] not in QUALITIES:
        raise _refuse(opened, "a quality is not one the file is known to hold")
    if not A_DAY.fullmatch(always[ENTERED]):
        raise _refuse(opened, "a day is not a day")
    if always[ENDED] and not A_DAY.fullmatch(always[ENDED]):
        raise _refuse(opened, "a day is not a day")
    return Record(
        entity=always[ENTITY],
        provider=always[PROVIDER],
        quality=always[QUALITY],
        ended=always[ENDED],
        entered=always[ENTERED],
        asked={name: _text_of(held, name, opened, needed=False) for name in asked},
        kind=where[0],
        coordinates=where[1],
    )


def read(opened: Opened, dataset: str, within: Box, asked: Sequence[str] = ()) -> Read:
    """The records of a dataset that lie in or over a box of longitude and latitude.

    `asked` names the properties that are read beside those every record
    holds. No other is read. A record is kept where the box round it touches
    the box that is asked for, so one that only comes near is kept too: it is
    for the measure to say what lies where. A record outside the box is
    counted and let go, and nothing of it is read but where it is. The records
    are given in the order of their numbers, and the step stops where two
    share one.
    """
    found: dict[str, Record] = {}
    in_the_file = nowhere = 0
    with opened.text() as text:
        for feature in _features(text, dataset, opened):
            in_the_file += 1
            where = _where(feature, opened)
            try:
                box = None if where is None else box_in_degrees(where[1])
            except ValueError:
                raise _refuse(opened, "a geometry is not a geometry") from None
            if where is None or box is None:
                nowhere += 1
                continue
            if not touch(box, within):
                continue
            record = _record(feature, where, dataset, asked, opened)
            if record.entity in found:
                raise _refuse(opened, "two records share a number")
            found[record.entity] = record
    records = tuple(found[entity] for entity in sorted(found, key=int))
    return Read(records=records, in_the_file=in_the_file, nowhere=nowhere)
