"""The food hygiene register: of which kind a business is, and where it is. Nothing else.

The Food Standards Agency publishes the register that councils keep of every
business that serves or sells food. It gives one file for each authority, and
replaces the file under one address. A file states the day of its extract in
its header, and that day is its edition and the period of its data.

**What the licence registry allows, and what it forbids.** The entry
`fsa-food-hygiene-ratings` is approved for `scoring` and `validation_only`,
under seven conditions. Each is a rule of this module and of every measure
that reads it.

| The registry says | So here |
|---|---|
| Use for counts, the kind of business and chains only | A business is counted by its kind |
| Never show a hygiene rating or a rating image | No rating, key, date or score is read |
| No logo of the agency or the scheme. Naming it is fine | It is named, in words alone |
| Show the date of the data beside every figure | A figure carries the days of its extracts |
| Never show or export a row. Some are sole traders | No name and no address is read |
| Do not imply that the agency endorses anything | No sentence of a measure says so |
| OpenStreetMap never drops, adds or corrects a record | The register is read as it is |

Nothing allows `display`, so no business is shown. A count is a figure for
ranking. Of a business, nothing leaves this module but its kind, its
authority and its point.

What a file holds. It is XML, on one line: the root `FHRSEstablishment`, a
`Header`, and an `EstablishmentCollection` of one `EstablishmentDetail` for
each business.

| Element | Read | Why |
|---|---|---|
| `Header/ExtractDate` | Yes | The day of the extract, held to the receipt |
| `Header/ItemCount` | Yes | The register's own count, which the file is held to |
| `Header/ReturnCode` | Yes | Whether the extract succeeded |
| `BusinessType`, `BusinessTypeID` | Yes | The kind, in words and as a number |
| `LocalAuthorityCode` | Yes | The authority, held to the name of the file |
| `Geocode/Longitude`, `Geocode/Latitude` | Yes | Where the business is |
| `BusinessName` | Never | A name may be a person's |
| `AddressLine1` to `AddressLine4`, `PostCode` | Never | An address may be a home |
| `RatingValue`, `RatingKey`, `RatingDate`, `Scores` | Never | The registry forbids a rating |
| `NewRatingPending`, `RightToReply` | Never | They are about a rating |
| `FHRSID`, `LocalAuthorityBusinessID` | Never | They name one business |
| `LocalAuthorityName`, its web site and its email | Never | Not needed |
| `SchemeType` | Never | Not needed |

The text of an element that is never read is not kept, not even for a moment:
the walk keeps text only while it stands inside an element that is read.

How a missing value is written. An element that does not apply is left out.
A business with no point has an empty `Geocode`. It is counted with its kind,
and it is put nowhere: not at the centre of its authority, and not at its
postcode, which is not read. The file does not say why a point is missing.

Which kinds are which. The register names fourteen kinds, and its own kind
decides what a business is. No rule is made from a name.

| The register's kind | It is |
|---|---|
| Restaurant/Cafe/Canteen | A place to sit and eat |
| Pub/bar/nightclub | A pub or a bar |
| Takeaway/sandwich shop | A takeaway |
| Retailers - other, Retailers - supermarkets/hypermarkets | A shop that sells food |
| The other nine | None of these |

The other nine are a school or a college, a hospital, a nursery or a carer, a
caterer with no place of its own to eat at, a van, a hotel, a maker, a
carrier, an importer and a farmer.

A kind the register is not known to name stops the step, and so does an
element it is not known to hold. A person then says what it is.

What a file is held to, because a figure rests on it:

- **Its day.** The header's day is the day of its receipt.
- **Its count.** It holds as many businesses as its header says.
- **Its authority.** Every business is of one authority, and it is the one
  the publisher's name for the file gives: `FHRS501en-GB.xml`.

The longitude and the latitude are taken to be on WGS84. The file does not say.

Nothing here decides what is within reach of a home, and nothing here is a
figure.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from functools import lru_cache

from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Period, Receipt
from burro_pipeline.fetch.markup import Limited, MarkupError
from burro_pipeline.fetch.markup import read as walk
from burro_pipeline.inputs import Inputs, Opened, period_of
from burro_pipeline.registry.model import Use

SOURCE = "fsa-food-hygiene-ratings"
PUBLISHER = "Food Standards Agency"
# What a measure puts the file to. The registry allows it, and does not allow `display`.
USE = Use.SCORING
# The publisher names a file for the scheme, the authority and the language.
FILE = re.compile(r"FHRS(?P<authority>[0-9]{3})en-GB\.xml")
# How much of a file is read. The largest read so far is under 6 MB.
LIMIT = 256 * 1024 * 1024
# The longest text that is kept of any element that is read. The longest kind has 37 letters.
LONGEST = 64

ROOT, HEADER, COLLECTION, DETAIL = (
    "FHRSEstablishment",
    "Header",
    "EstablishmentCollection",
    "EstablishmentDetail",
)
DAY, COUNT, OUTCOME = "ExtractDate", "ItemCount", "ReturnCode"
SUCCEEDED = "Success"
KIND, KIND_ID, AUTHORITY = "BusinessType", "BusinessTypeID", "LocalAuthorityCode"
POINT, LONGITUDE, LATITUDE = "Geocode", "Longitude", "Latitude"
# The elements of a business that are read, and those that are left. The text of an element
# that is left is never kept.
READ = (KIND, KIND_ID, AUTHORITY, POINT, LONGITUDE, LATITUDE)
LEFT = (
    "FHRSID",
    "LocalAuthorityBusinessID",
    "BusinessName",
    "AddressLine1",
    "AddressLine2",
    "AddressLine3",
    "AddressLine4",
    "PostCode",
    "RatingValue",
    "RatingKey",
    "RatingDate",
    "LocalAuthorityName",
    "LocalAuthorityWebSite",
    "LocalAuthorityEmailAddress",
    "Scores",
    "Hygiene",
    "Structural",
    "ConfidenceInManagement",
    "SchemeType",
    "NewRatingPending",
    "RightToReply",
)
A_DAY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
A_COUNT = re.compile(r"[0-9]{1,7}")
AN_AUTHORITY = re.compile(r"[0-9]{3}")
# A longitude or a latitude, as the register writes one: up to 18 decimal places were seen,
# and a longitude next to the meridian written as `5.2E-05`.
A_NUMBER = re.compile(r"-?[0-9]{1,3}(\.[0-9]{1,20})?(E-[0-9]{1,2})?")
NOT_LAID_OUT = "it is not laid out as a file of the register is"
# What stands in for text that is longer than any value that is read. It is no value.
TOO_LONG = "\x00"


class Group(StrEnum):
    """What a business is, for a measure. The register's own kind decides."""

    EAT = "eat"  # a place to sit and eat
    PUB = "pub"  # a pub, a bar or a nightclub
    TAKEAWAY = "takeaway"
    SHOP = "shop"  # a shop that sells food
    NONE = "none"  # none of these


# The fourteen kinds, each by the register's number for it, as the register writes them.
KINDS: Mapping[str, tuple[str, Group]] = {
    "1": ("Restaurant/Cafe/Canteen", Group.EAT),
    "14": ("Importers/Exporters", Group.NONE),
    "4613": ("Retailers - other", Group.SHOP),
    "5": ("Hospitals/Childcare/Caring Premises", Group.NONE),
    "7": ("Distributors/Transporters", Group.NONE),
    "7838": ("Farmers/growers", Group.NONE),
    "7839": ("Manufacturers/packers", Group.NONE),
    "7840": ("Retailers - supermarkets/hypermarkets", Group.SHOP),
    "7841": ("Other catering premises", Group.NONE),
    "7842": ("Hotel/bed & breakfast/guest house", Group.NONE),
    "7843": ("Pub/bar/nightclub", Group.PUB),
    "7844": ("Takeaway/sandwich shop", Group.TAKEAWAY),
    "7845": ("School/college/university", Group.NONE),
    "7846": ("Mobile caterer", Group.NONE),
}


class _Refused(Exception):
    """The file is not as the step expects. It holds the fixed words that say how."""


@dataclass(frozen=True, order=True)
class Place:
    """One business the register gives a point for: its kind, and where it is."""

    longitude: float
    latitude: float
    # The register's number for the kind.
    kind: str
    # The register's number for the authority that listed it.
    authority: str

    @property
    def group(self) -> Group:
        return KINDS[self.kind][1]


@dataclass(frozen=True)
class Extract:
    """One file of the register: one authority, as at one day."""

    authority: str
    file_id: str
    # The day of the extract, as the header states it.
    day: str
    # How many businesses the file holds, which is the count its header gives.
    businesses: int
    # How many businesses of each kind it lists, and how many of those it gives a point for,
    # by the register's number for the kind. Every kind is here, at nought if it lists none.
    listed: Mapping[str, int]
    pointed: Mapping[str, int]

    def of(self, group: Group) -> int:
        """How many businesses of a group the file lists, with a point or without."""
        return sum(count for kind, count in self.listed.items() if KINDS[kind][1] is group)

    def with_a_point(self, group: Group) -> int:
        return sum(count for kind, count in self.pointed.items() if KINDS[kind][1] is group)


@dataclass(frozen=True, repr=False)
class Register:
    """Every file of the register that a build was given, read as one."""

    # In the order of the publisher's names for the files.
    extracts: tuple[Extract, ...]
    files: tuple[Receipt, ...]
    # Every business with a point, in a fixed order. A business with none is in no list.
    places: tuple[Place, ...]

    def __repr__(self) -> str:
        """Counts alone, so that a line that prints the register prints no business."""
        listed = sum(one.businesses for one in self.extracts)
        return f"Register(files={len(self.files)}, businesses={listed}, places={len(self.places)})"

    def listed(self, group: Group) -> int:
        return sum(one.of(group) for one in self.extracts)

    def placed(self, group: Group) -> int:
        return sum(one.with_a_point(group) for one in self.extracts)

    @property
    def period(self) -> Period:
        """From the day of the oldest extract to the day of the newest."""
        return period_of(self.files)

    @property
    def as_at(self) -> str:
        """The days of the extracts in words, as a figure is dated: one day, or a span."""
        first, last = self.period.days()
        return first if first == last else f"{first} to {last}"


def is_a_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file of an authority."""
    return FILE.fullmatch(name) is not None


def _number(text: str, most: float) -> float:
    if A_NUMBER.fullmatch(text) is None or abs(float(text)) > most:
        raise _Refused("a point is no point")
    return float(text)


@dataclass
class _Walk:
    """Walks one file, and keeps the kind, the authority and the point of each business."""

    places: list[Place] = field(default_factory=list[Place])
    listed: dict[str, int] = field(default_factory=lambda: dict.fromkeys(sorted(KINDS), 0))
    pointed: dict[str, int] = field(default_factory=lambda: dict.fromkeys(sorted(KINDS), 0))
    header: dict[str, str] = field(default_factory=dict[str, str])
    authorities: set[str] = field(default_factory=set[str])
    businesses: int = 0
    headers: int = 0
    _path: list[str] = field(default_factory=list[str])
    _text: list[str] | None = None
    _kept: int = 0
    _held: dict[str, list[str]] = field(default_factory=dict[str, list[str]])

    def start(self, name: str, _: dict[str, str]) -> None:
        depth = len(self._path)
        self._path.append(name)
        self._text = None
        if depth == 0:
            if name != ROOT:
                raise _Refused("it is not a file of the register")
        elif depth == 1:
            # The header stands first, once, and the businesses after it.
            first = name == HEADER and self.headers == 0 and self.businesses == 0
            if not (first or (name == COLLECTION and self.headers == 1)):
                raise _Refused(NOT_LAID_OUT)
            self.headers += name == HEADER
        elif self._path[1] == HEADER:
            if depth != 2 or name not in (DAY, COUNT, OUTCOME) or name in self.header:
                raise _Refused(NOT_LAID_OUT)
            self._keep()
        elif depth == 2:
            if name != DETAIL:
                raise _Refused(NOT_LAID_OUT)
            self._held = {}
        elif name in LEFT:
            # Its text is never kept: `text` keeps nothing while `_text` is None.
            return
        elif depth == 3 and name in (KIND, KIND_ID, AUTHORITY):
            self._keep()
        elif depth == 3 and name == POINT:
            self._held.setdefault(POINT, []).append("")
        elif depth == 4 and self._path[3] == POINT and name in (LONGITUDE, LATITUDE):
            self._keep()
        else:
            raise _Refused("a business holds an element the register is not known to hold")

    def _keep(self) -> None:
        self._text, self._kept = [], 0

    def text(self, piece: str) -> None:
        if self._text is None:
            return
        self._kept += len(piece)
        # More than any element that is read could hold is not kept, and is no value.
        self._text = [TOO_LONG] if self._kept > LONGEST else [*self._text, piece]

    def end(self, name: str) -> None:
        kept, self._text = self._text, None
        if kept is not None:
            text = "".join(kept).strip()
            if self._path[1] == HEADER:
                self.header[name] = text
            else:
                self._held.setdefault(name, []).append(text)
        if len(self._path) == 3 and name == DETAIL:
            self._business()
        self._path.pop()

    def _once(self, name: str) -> str | None:
        found = self._held.get(name, [])
        return found[0] if len(found) == 1 and found[0] else None

    def _business(self) -> None:
        kind, number = self._once(KIND), self._once(KIND_ID)
        if kind is None or number is None:
            raise _Refused("a business does not give its kind once")
        if number not in KINDS or KINDS[number][0] != kind:
            raise _Refused("a kind of business is not one the register is known to name")
        authority = self._once(AUTHORITY)
        if authority is None or AN_AUTHORITY.fullmatch(authority) is None:
            raise _Refused("a business does not say which authority it is of")
        self.authorities.add(authority)
        self.businesses += 1
        self.listed[number] += 1
        along, up = self._held.get(LONGITUDE, []), self._held.get(LATITUDE, [])
        if len(self._held.get(POINT, [])) > 1 or len(along) != len(up) or len(along) > 1:
            raise _Refused("a point is no point")
        if along:
            place = Place(_number(along[0], 180.0), _number(up[0], 90.0), number, authority)
            self.places.append(place)
            self.pointed[number] += 1


def _refused(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def _header(opened: Opened, walked: _Walk) -> str:
    """The day of the extract, once the header is seen to say what a figure rests on."""
    day = walked.header.get(DAY, "")
    if walked.headers != 1 or A_DAY.fullmatch(day) is None:
        raise _refused(opened, "its header does not give the day of its extract")
    if opened.receipt.data_period.days() != (day, day):
        raise _refused(opened, "the day it states is not the day of its receipt")
    count = walked.header.get(COUNT, "")
    if A_COUNT.fullmatch(count) is None:
        raise _refused(opened, "its header does not say how many businesses it holds")
    if walked.header.get(OUTCOME) != SUCCEEDED:
        raise _refused(opened, "its header does not say that the extract succeeded")
    if int(count) != walked.businesses:
        raise _refused(opened, "it does not hold as many businesses as its header says")
    return day


def read(opened: Opened) -> tuple[Extract, tuple[Place, ...]]:
    """One file of the register: what it lists of each kind, and every business with a point.

    It stops at a file that is not named for an authority, at a file that is
    not laid out as the register is, at a kind or an element the register is
    not known to hold, and at a file that is not what its header and its name
    say it is. What it says of a refusal repeats nothing the file holds.

    A build reads the register once for each measure that counts it. A copy
    was held to the hash in its receipt when it was handed over, so the copy
    of one receipt in one place is walked once.
    """
    return _read(opened)


@lru_cache(maxsize=128)
def _read(opened: Opened) -> tuple[Extract, tuple[Place, ...]]:
    named = FILE.fullmatch(opened.receipt.publisher_file)
    if named is None:
        raise _refused(opened, "it is not named for an authority")
    walked = _Walk()
    over = _Refused("the file is larger than any that was read before")
    try:
        with opened.path.open("rb") as raw:
            walk(Limited(raw, LIMIT, over), walked.start, walked.end, walked.text)
    except _Refused as stopped:
        raise _refused(opened, str(stopped)) from None
    except (MarkupError, OSError, ValueError):
        raise _refused(opened, "it could not be read as XML") from None
    day = _header(opened, walked)
    if len(walked.authorities) > 1:
        raise _refused(opened, "its businesses are not all of one authority")
    if walked.authorities and walked.authorities != {named["authority"]}:
        raise _refused(opened, "it is not of the authority its name says")
    extract = Extract(
        authority=named["authority"],
        file_id=opened.file_id,
        day=day,
        businesses=walked.businesses,
        listed=dict(walked.listed),
        pointed=dict(walked.pointed),
    )
    return extract, tuple(sorted(walked.places))


def build(inputs: Inputs) -> Register:
    """Every file of the register that the build was given, from the files of the build.

    The gate is asked once, before any file is read. A build gives one edition
    of each file, and two editions of one file are refused. Which files a
    build must hold is for the measure to say: nothing here knows how many
    authorities there are.
    """
    opened = inputs.open_each(SOURCE, USE, named=is_a_file)
    read_in = [read(one) for one in opened]
    return Register(
        extracts=tuple(extract for extract, _ in read_in),
        files=tuple(one.receipt for one in opened),
        places=tuple(sorted(place for _, places in read_in for place in places)),
    )
