"""The receipt: one for each publisher's file, written when the file is fetched.

A receipt says what was fetched, from where, when, and under which registry
entry. It holds an address, a hash and dates, and no row of the file. Every
other record names a file by the `file_id` of its receipt.
"""

import hashlib
import re
from enum import StrEnum
from functools import lru_cache
from itertools import pairwise
from pathlib import PurePosixPath
from typing import Annotated, Any, Self
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from burro_core.ids import SourceId
from pydantic import Field, SerializerFunctionWrapHandler, model_serializer, model_validator

from burro_pipeline.evidence.record import (
    MADE_UP_SOURCE,
    EvidenceRecord,
    FileId,
    Sha256,
    Text,
    Timestamp,
    When,
    file_id_of,
    first_and_last_day,
    strictly_increasing,
)
from burro_pipeline.registry.model import Use

EVIDENCE_FOLDER = PurePosixPath("registry/evidence")
RECEIPTS_FOLDER = PurePosixPath("data/receipts")
# Where publishers' files are kept in the vault. Fetch writes there and `seal` looks there.
VAULT_PREFIX = "raw/"
# Where a copy of each receipt is kept in the vault, so that it outlives the machine that fetched.
KEPT_PREFIX = "receipts/"
# A query parameter whose name holds one of these is taken for a key, and is never stored.
SECRET_NAME = re.compile(r"key|token|secret|sig|auth|pass|credential|session|login|user", re.I)
# A file's name is one part of a path in the vault, so it may not hold a way out of it,
# and it does not start with a dot.
FILE_NAME = r"[^./\\\x00-\x1f\x7f][^/\\\x00-\x1f\x7f]{0,254}"
FILE_NAME_PATTERN = rf"^{FILE_NAME}$"


class How(StrEnum):
    FETCHED = "fetched"  # by code
    BY_HAND = "by_hand"  # saved by a person, from a page that refuses code
    MADE_UP = "made_up"  # no file at all: made up for testing, under the source `synthetic`


class Where(StrEnum):
    """Where the edition of a file was read, when no page of its publisher states one."""

    # An element of the header of an XML file. The header is the first element under the root.
    XML_HEADER = "xml_header"
    # The last change a GeoPackage records of its contents. It is about the file.
    GEOPACKAGE = "geopackage"
    # The time the header block of a street extract says its data runs to.
    STREET_EXTRACT = "street_extract"
    # Nowhere. The file holds no date, and its edition is the day it was retrieved.
    RETRIEVED = "retrieved"


# The name of an element, as a list may give it: no prefix, and nothing that could be markup.
ELEMENT = r"[A-Za-z_][A-Za-z0-9_.-]{0,63}"
# The place in a file that holds the edition, where the kind of file fixes it.
PLACE = {
    Where.GEOPACKAGE: "gpkg_contents.last_change",
    Where.STREET_EXTRACT: "OSMHeader.osmosis_replication_timestamp",
    Where.RETRIEVED: "",
}


class Geography(StrEnum):
    """What a file's rows are keyed by. It is read from the file and never assumed."""

    OA21 = "oa21"
    LSOA21 = "lsoa21"
    LSOA11 = "lsoa11"
    MSOA21 = "msoa21"
    MSOA11 = "msoa11"
    LAD = "lad"
    POSTCODE = "postcode"
    POINT = "point"
    GRID_1KM = "grid_1km"
    POLYGON = "polygon"
    LINE = "line"
    # A file that places nothing: a page of text, a timetable's calendar.
    NONE = "none"


@lru_cache(maxsize=4096)
def _days(start: str, end: str) -> tuple[str, str]:
    """The first day of one date and the last day of another.

    A check asks this of every file of every row, and a build has few periods.
    So each pair is worked out once.
    """
    return first_and_last_day(start)[0].isoformat(), first_and_last_day(end)[1].isoformat()


class Period(EvidenceRecord):
    """The time the data describes, in the publisher's terms: one date, or a span."""

    as_at: When | None = None
    start: When | None = None
    end: When | None = None

    @model_validator(mode="after")
    def _one_date_or_a_span(self) -> Self:
        span = self.start is not None and self.end is not None
        if (self.as_at is None) != span or (self.start is None) != (self.end is None):
            raise ValueError("a period is `as_at` alone, or `start` and `end` together")
        first, last = self.days()
        if first > last:
            raise ValueError("a period may not end before it starts")
        return self

    def days(self) -> tuple[str, str]:
        """The first and the last day of the period."""
        return _days(self.as_at or self.start or "", self.as_at or self.end or "")


class EditionFrom(EvidenceRecord):
    """Where an edition was read, when no page of the publisher states one.

    A publisher that replaces a file under one address, and names no edition on
    its page, leaves the file itself as the one thing that says which file it
    is. Fetch reads that from what arrives. A receipt that holds this says so,
    and a receipt that does not holds an edition that a page stated.
    """

    where: Where
    # The place, as the file names it. For XML, the header and the element in it, as
    # `Header/ExtractDate`. Empty where the edition is the day the file was retrieved.
    at: str
    # Whether the period of the data was read there too. A day that is about the file and
    # not about its data is not the period of its data.
    period_too: bool

    @model_validator(mode="after")
    def _is_a_place_the_kind_of_file_has(self) -> Self:
        if self.where is Where.XML_HEADER:
            if not re.fullmatch(rf"{ELEMENT}/{ELEMENT}", self.at):
                raise ValueError("at names the header and the element in it, as Header/ExtractDate")
        elif self.at != PLACE[self.where]:
            fixed = PLACE[self.where]
            raise ValueError(f"at is {fixed}" if fixed else "at names no place in the file")
        if self.where is Where.GEOPACKAGE and self.period_too:
            raise ValueError(
                "the day a GeoPackage was last changed is about the file, and is never the "
                "period of its data"
            )
        return self


# The name of a column of a file, as a list may give it: letters, digits and `_`. A column
# inside another is named from the top, as the file's own layout names it, with a dot
# between: `sources.list.element.dataset`.
_NAME = r"[A-Za-z_][A-Za-z0-9_]{0,63}"
COLUMN = rf"^{_NAME}(\.{_NAME}){{0,7}}$"
Column = Annotated[str, Field(pattern=COLUMN)]


class Taken(EvidenceRecord):
    """Which part of a publisher's file was taken, where fetch took part of one.

    Some publishers give the whole world as a few large files, laid out so
    that a reader can take the rows of one place. What is kept is then not the
    file at the address, and the receipt says so: the size of the whole file,
    what was wanted of it, which row groups were taken, and where in the file
    each run of bytes that was kept lies. The hash of the receipt is of those
    runs, one after another. So the same part can be taken again from the
    address, and is the same bytes.
    """

    # The size of the whole file at the publisher, in bytes.
    of_bytes: int = Field(ge=1)
    # The box the rows were wanted in, in degrees: west, south, east and north.
    box: tuple[float, float, float, float]
    # The column of the file that holds the box each row fits in.
    box_in: Column
    # The columns that were taken, in name order. A name takes the column and every column
    # inside it.
    columns: tuple[Column, ...] = Field(min_length=1)
    # How many row groups the file holds, and which were taken, counted from 0.
    of_row_groups: int = Field(ge=0)
    row_groups: tuple[int, ...]
    # How many rows the file holds, and how many the row groups taken hold.
    of_rows: int = Field(ge=0)
    rows: int = Field(ge=0)
    # The runs of bytes that were kept: the first byte of each and how many, in the order
    # of the file. The first is the start of the file and the last is its footer.
    runs: tuple[tuple[Annotated[int, Field(ge=0)], Annotated[int, Field(ge=1)]], ...] = Field(
        min_length=1
    )

    @model_validator(mode="after")
    def _holds_together(self) -> Self:
        west, south, east, north = self.box
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            raise ValueError("box runs from west to east and from south to north, in degrees")
        if any(round(part, 6) != part for part in self.box):
            raise ValueError("box is given to six decimal places at most")
        if not strictly_increasing(self.columns):
            raise ValueError("columns are in name order, each once")
        if self.box_in not in self.columns:
            raise ValueError("box_in is one of the columns that were taken")
        groups = (-1, *self.row_groups, self.of_row_groups)
        if not all(a < b for a, b in pairwise(groups)):
            raise ValueError("row_groups are those taken, counted from 0, each once")
        if self.rows > self.of_rows or (not self.row_groups and self.rows):
            raise ValueError("the row groups taken hold no more rows than the file")
        if self.runs[0][0] != 0:
            raise ValueError("the part starts with the start of the file")
        if not all(a + count < b for (a, count), (b, _) in pairwise(self.runs)):
            raise ValueError("runs are in the order of the file, and no two touch")
        if sum(self.runs[-1]) != self.of_bytes:
            raise ValueError("the part ends with the end of the file")
        return self

    @property
    def bytes(self) -> int:
        """How many bytes the runs come to."""
        return sum(count for _, count in self.runs)


class Member(EvidenceRecord):
    """One file inside a zip that a step reads."""

    name: Text
    sha256: Sha256
    bytes: int = Field(ge=0)


def vault_key(source_id: str, sha256: str, publisher_file: str) -> str:
    """Where a file is kept in the vault: by source and by hash, so never written over."""
    return f"{VAULT_PREFIX}{source_id}/{sha256}/{publisher_file}"


def clean_url(url: str) -> str:
    """An address with any login, key, token and fragment taken out.

    A key is looked for by the name of its parameter. One written into the path
    cannot be told from the path, so a source that takes its key that way needs
    its address cleaned by the step that fetches it.
    """
    parts = urlsplit(url)
    host = parts.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    if parts.port is not None:
        host = f"{host}:{parts.port}"
    kept = [
        (name, value)
        for name, value in parse_qsl(parts.query, keep_blank_values=True)
        if not SECRET_NAME.search(name)
    ]
    return urlunsplit((parts.scheme.lower(), host, parts.path, urlencode(kept), ""))


def is_clean(url: str) -> bool:
    """Whether an address is https and is what `clean_url` would make of it."""
    try:
        return url.startswith("https://") and bool(urlsplit(url).hostname) and url == clean_url(url)
    except ValueError:
        # An address that cannot be read. The reason may quote it, so it is not passed on.
        return False


class Receipt(EvidenceRecord):
    file_id: FileId
    source_id: SourceId
    # The use the gate was asked for, before the file was fetched.
    use: Use
    # The file's name as the publisher gave it.
    publisher_file: str = Field(pattern=FILE_NAME_PATTERN)
    # For a zip: each file inside it that a step reads, in name order.
    members: tuple[Member, ...] = ()
    # The address after redirects, with any key taken out. Empty for a made-up file.
    url: str
    # The address the list gave for the file, before any redirect, as clean as `url`.
    # A receipt that has none leaves the field out, and is written as it was before the
    # field: one written before it, one of a file saved by hand whose list gives no
    # address, and one of a made-up file.
    listed_url: str | None = None
    sha256: Sha256
    bytes: int = Field(ge=1)
    # From the fetch, never from the build.
    retrieved_at: Timestamp
    how: How
    # The publisher's own label: a version, a release month, a reference number.
    edition: Text
    # Where the edition was read, when no page of the publisher states one. A receipt of
    # an edition that a page stated leaves the field out, and is written as it was before
    # the field.
    edition_from: EditionFrom | None = None
    # Which part of the file was taken, where fetch took part of one. `sha256` and `bytes`
    # are then of the part. A receipt of a whole file leaves the field out, and is written
    # as it was before the field.
    taken: Taken | None = None
    data_period: Period
    # Null until it has been read from the file.
    geography: Geography | None = None
    # A saved copy of the terms, where a registry condition asks for one.
    licence_evidence: str | None = None

    @model_validator(mode="after")
    def _holds_together(self) -> Self:
        if self.file_id != file_id_of(self.sha256):
            raise ValueError("file_id is not the first twelve digits of sha256")
        if not strictly_increasing([member.name for member in self.members]):
            raise ValueError("members are in name order, each once")
        if (self.how is How.MADE_UP) != (self.source_id == MADE_UP_SOURCE):
            raise ValueError("a made-up file cites the source `synthetic`, and nothing else does")
        if self.how is How.MADE_UP:
            if self.url or self.listed_url is not None:
                raise ValueError("a made-up file has no address")
            if self.edition_from is not None:
                raise ValueError("a made-up file has no edition that was read anywhere")
        elif not is_clean(self.url):
            raise ValueError("url is an https address with no login, key or fragment in it")
        if self.listed_url is not None and not is_clean(self.listed_url):
            raise ValueError("listed_url is an https address with no login, key or fragment in it")
        if self.taken is not None:
            if self.how is not How.FETCHED:
                raise ValueError("only a file that was fetched is taken in part")
            if self.taken.bytes != self.bytes:
                raise ValueError("a part holds as many bytes as its runs come to")
        if self.licence_evidence is not None:
            path = PurePosixPath(self.licence_evidence)
            inside = path.parent == EVIDENCE_FOLDER and str(path) == self.licence_evidence
            if not inside or not re.fullmatch(FILE_NAME_PATTERN, path.name):
                raise ValueError("licence_evidence names a file in registry/evidence/")
        return self

    @model_serializer(mode="wrap")
    def _written_as_before_where_a_later_field_is_not_given(
        self, written_by: SerializerFunctionWrapHandler
    ) -> dict[str, Any]:
        """A receipt with no `listed_url` is the same bytes as it was before the field.

        So is one with no `edition_from`: every receipt of an edition that a page stated.
        And one with no `taken`: every receipt of a whole file.
        """
        written: dict[str, Any] = written_by(self)
        for later in ("listed_url", "edition_from", "taken"):
            if written.get(later) is None:
                written.pop(later, None)
        return written

    @property
    def retrieved_on(self) -> str:
        """The day the file was retrieved."""
        return self.retrieved_at[:10]

    @property
    def made_up(self) -> bool:
        return self.how is How.MADE_UP

    def vault_key(self) -> str:
        """Where the file is kept in the vault."""
        return vault_key(self.source_id, self.sha256, self.publisher_file)

    def path(self) -> PurePosixPath:
        """Where the receipt is kept in the repository."""
        return RECEIPTS_FOLDER / self.source_id / f"{self.file_id}.json"

    def kept_key(self) -> str:
        """Where a copy of the receipt is kept in the vault, beside the file."""
        return f"{KEPT_PREFIX}{self.source_id}/{self.file_id}.json"


def _bytes_of(name: str) -> bytes:
    """What a made-up file would hold if it were written: one line that says what it is."""
    return f"Made up for testing. It describes no real place. {name}\n".encode()


def made_up_receipt(
    name: str, use: Use, geography: Geography, period: Period, retrieved_at: str
) -> Receipt:
    """The receipt of a file that does not exist. Its hash is of the one line it would hold."""
    content = _bytes_of(name)
    sha256 = hashlib.sha256(content).hexdigest()
    inside = ("made-up-services.xml", "made-up-stops.xml") if name.endswith(".zip") else ()
    members = tuple(
        Member(
            name=member,
            sha256=hashlib.sha256(_bytes_of(member)).hexdigest(),
            bytes=len(_bytes_of(member)),
        )
        for member in inside
    )
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=MADE_UP_SOURCE,
        use=use,
        publisher_file=name,
        members=members,
        url="",
        sha256=sha256,
        bytes=len(content),
        retrieved_at=retrieved_at,
        how=How.MADE_UP,
        edition="made up",
        data_period=period,
        geography=geography,
    )
