"""The stations of London, as places a person can name.

A person says where they must reach, and names a station for it. Core looks
the words up among the places of a release, and a release that is not made up
holds no place yet. This makes the table of stations a release
would hold, from the Department for Transport's file of London's stops. The
registry allows the file for destination search, and the gate is asked for
that use before the file is read.

**It gives no journey.** A place is a name and a point. How long it takes to
reach one is worked out by a routing engine on timetables, and none is built.

**A station's name may be shown.** Nothing tracked here holds the name of a
person, of a school or of a business: those are the names the rule is about. A
station's name is the name of a place. Its publisher gives it under the Open
Government Licence, and it is what a person types. The registry asks two things
of how it is shown: the Department for Transport is named as the source, and
no roundel, map or typeface of the operator is used.

What a row is, and where each part comes from:

| Part | It is | From |
|---|---|---|
| `name` | The name, exactly as the file writes it | `CommonName` |
| `aliases` | What a person may type in its place. Matched, and never shown | A rule, below |
| `served` | A railway station, or a tram, metro or underground station | `StopType` |
| `network` | The Underground, the DLR, a tram or the cable car, where it is known | A hint |
| `point` | The middle of its ways in, to the metre, on the National Grid | The ways in |
| `centroid` | The same point as longitude and latitude, to six decimal places | The same |
| `codes` | The code of each way in, which leads back to its row | `ATCOCode` |
| `place_id` | An id made from the first of its codes | A rule, below |

**The name is never changed.** The file writes "Station" after some names and
not after others, and writes "Rail Station", "Underground Station", "DLR
Station" and "Tram Stop" after a few. A person types none of them, or types
"station". A name may hold "&", and a person types "and". So each row is given
aliases, made by rule from the name: the name with its closing words of kind
taken off, that with "station" after it, and each again with "and" for "&". An
alias is for matching alone. What is shown is the name.

**Two stations may answer to one name.** A railway station and an underground
station of one name are two rows, because the file gives them as two kinds.
Core takes a name without asking only where it names one place, so for such a
name it offers both. `shares_a_name` marks each. Whether the two are one place
is the founder's to say.

**The network is a hint.** The file has no column for it. It is read from two
letters that most codes hold, which the publisher's guide does not define, and
it is none where a code holds no such letters. A railway station has none: the
file does not say whose trains call, so the Overground and the Elizabeth line
are railway stations here.

**The id is a draft.** It is made from the code of a way in, because the file
of an authority gives a station no code of its own. The national file does,
and an id should be made from that once it is read.

What core and a release need before a place can be carried is in
`docs/research/data/stations.md`.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from burro_core.ids import PLACE_ID_PATTERN, PlaceKind
from burro_core.places import normalise

from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.shapes import longitude_and_latitude
from burro_pipeline.derive import stops_file
from burro_pipeline.derive.stops_file import Station
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

SOURCE = stops_file.SOURCE
USE = Use.DESTINATION_SEARCH
# Core's kind for every row: a station.
KIND = PlaceKind.STATION
# What the file's type says a station is, in words.
SERVED = {stops_file.RAIL: "rail", stops_file.METRO: "tram_metro_underground"}
# The closing words of a name that say only what kind of stop it is, the longest first. The
# second part of each is what may stand before it: `Station DLR` is written both ways round.
CLOSING = re.compile(
    r"\s+(?:(?:Rail|Underground|Overground|DLR)\s+Station|Station\s+DLR|Tram\s+Stop|Station|DLR)$"
)
# What a person may type after a name, and the word a person may type for a sign in one.
TYPED_AFTER = "station"
AMPERSAND, AND = "&", "and"
CITY = "lon"


@dataclass(frozen=True, order=True)
class StationPlace:
    """One station, as a place a person can name."""

    place_id: str
    # The name, as the file gives it. It is what is shown.
    name: str
    # What may be typed in its place. Made by rule, matched, and never shown.
    aliases: tuple[str, ...]
    kind: PlaceKind
    served: str
    # A hint, from the letters of its codes, or none.
    network: str | None
    # The middle of its ways in: on the National Grid, and as longitude and latitude.
    point: Point
    centroid: Point
    # The code of each way in, in order.
    codes: tuple[str, ...]
    # Whether another row answers to its name or to one of its aliases.
    shares_a_name: bool
    source_id: str = SOURCE


@dataclass(frozen=True)
class Places:
    """The stations of London as places, and the file they were read from."""

    places: tuple[StationPlace, ...]
    file: Receipt
    # The day the file was saved, as its receipt gives it.
    saved: str


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file the places are read from."""
    return stops_file.is_the_file(name)


def bare(name: str) -> str:
    """A name with its closing words of kind taken off, once. A name of only such words is kept.

    They are taken off once, so that a name that ends "Power Station Underground
    Station" keeps the station that is part of it.
    """
    shorter = CLOSING.sub("", name, count=1).strip()
    return shorter or name


def aliases_of(name: str) -> tuple[str, ...]:
    """What a person may type for a name, in the order it is offered.

    The bare name, the bare name with "station" after it, and each again with
    "and" written for "&". One that is spelt as the name is, or as an alias
    before it, is left out.
    """
    short = bare(name)
    offered = [short, f"{short} {TYPED_AFTER}"]
    offered += [alias.replace(AMPERSAND, f" {AND} ") for alias in offered if AMPERSAND in alias]
    kept: list[str] = []
    for alias in (" ".join(one.split()) for one in offered):
        if normalise(alias) not in (normalise(one) for one in (name, *kept)):
            kept.append(alias)
    return tuple(kept)


def place_id_of(station: Station) -> str:
    """The id of a station: the city, and the first of its codes in small letters."""
    code = "".join(re.findall(r"[0-9a-z]+", station.ways_in[0].code.lower()))
    found = f"{CITY}-p{code}"
    if not code or not re.fullmatch(PLACE_ID_PATTERN, found):
        raise ValueError("a code makes an id")
    return found


def _spellings(name: str, aliases: Sequence[str]) -> frozenset[str]:
    return frozenset(normalise(one) for one in (name, *aliases))


def places_of(stations: Sequence[Station]) -> tuple[StationPlace, ...]:
    """The row of every station, in the order of their ids."""
    named = [(station, aliases_of(station.name)) for station in stations]
    answers: dict[str, int] = {}
    for station, aliases in named:
        for spelling in _spellings(station.name, aliases):
            answers[spelling] = answers.get(spelling, 0) + 1
    found = [
        StationPlace(
            place_id=place_id_of(station),
            name=station.name,
            aliases=aliases,
            kind=KIND,
            served=SERVED[station.type],
            network=stops_file.SEEN_TO_BE.get(station.letters or ""),
            point=station.middle,
            centroid=longitude_and_latitude(*station.middle),
            codes=tuple(way.code for way in station.ways_in),
            shares_a_name=any(
                answers[spelling] > 1 for spelling in _spellings(station.name, aliases)
            ),
        )
        for station, aliases in named
    ]
    if len({place.place_id for place in found}) != len(found):
        raise ValueError("an id names one station")
    return tuple(sorted(found))


def build(inputs: Inputs, *, edition: str | None = None) -> Places:
    """The stations of London as places, from the file of the build.

    The gate is asked whether the file may be put to destination search
    before it is read.
    """
    opened = stops_file.open_the_file(inputs, USE, edition=edition)
    ways_in = stops_file.read(opened, stops_file.STATION_TYPES, names=True)
    places = places_of(stops_file.stations_of(ways_in))
    return Places(places, opened.receipt, opened.receipt.data_period.days()[1])
