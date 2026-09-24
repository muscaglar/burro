"""The list of files for a build, as data.

A list says which files a build takes: for each, the registry id of its
source, the use the gate is asked for, where a person finds it, and the
address of the file itself once that is known. It is a TOML file in `lists/`,
read by a person and changed in a commit. It is no part of a workflow, and it
holds no key and no address of the store.

A list may hold what nobody is sure of yet, and says so item by item under
`unsure`. Fetch will store a file on an address that is not yet sure. It will
not write a receipt from an edition or a period that is not yet sure, because
a receipt is what a figure on screen is cited to.

A list is committed where anyone reads it, and so is a receipt. So an address
in a list holds no parameter but those the list names as part of the file's
address, and none of those may be one that is taken for a key. It holds no
`;`, which some servers read as the start of a parameter. A receipt keeps a
parameter only with the value the list's own address gives it.
"""

import re
import tomllib
from enum import StrEnum
from pathlib import Path
from typing import Any, Self, cast
from urllib.parse import parse_qsl, urlsplit

from burro_core.ids import SourceId
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from burro_pipeline.evidence import Period, in_words
from burro_pipeline.evidence.receipt import SECRET_NAME
from burro_pipeline.fetch.kinds import Kind
from burro_pipeline.registry.model import Use

LISTS = Path(__file__).parent / "lists"
SCHEMA_VERSION = 1
NAME = r"^[a-z0-9]+(-[a-z0-9]+)*$"
# The name of a parameter in an address, as a list may give it.
PARAMETER = r"[A-Za-z0-9._~-]{1,64}"
# What an item may say it is not sure of.
MAY_BE_UNSURE = frozenset({"url", "format", "max_bytes", "edition", "data_period"})


class ListError(Exception):
    """The list could not be read. The message names an item and repeats no value."""


class Format(StrEnum):
    CSV = "csv"
    ZIP = "zip"
    XLSX = "xlsx"
    GPKG = "gpkg"
    XML = "xml"
    JSON = "json"
    # Any other kind. What arrives is kept unless it is a web page.
    OTHER = "other"

    @property
    def kind(self) -> Kind | None:
        return _KINDS.get(self)


_KINDS = {
    Format.CSV: Kind.CSV,
    Format.ZIP: Kind.ZIP,
    Format.XLSX: Kind.WORKBOOK,
    Format.GPKG: Kind.GEOPACKAGE,
    Format.XML: Kind.XML,
    Format.JSON: Kind.JSON,
}


def _https(address: str) -> bool:
    try:
        parts = urlsplit(address)
        return parts.scheme == "https" and bool(parts.hostname) and parts.port != 0
    except ValueError:
        return False


class Listed(BaseModel):
    """One file of a build."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    # The name of this file in the list. A person gives it to `by-hand` and `--only`.
    item: str = Field(pattern=NAME)
    source_id: SourceId
    # The use the gate is asked for before the file is fetched.
    use: Use
    # What the file is, in the publisher's terms.
    what: str = Field(min_length=1)
    format: Format
    # The dataset's own page, where a person finds the file. From the registry entry.
    page: str
    # The address of the file itself. Empty until somebody has found it.
    url: str = ""
    # A file over this size is refused.
    max_bytes: int = Field(gt=0)
    # The publisher's own label: a version, a release month, a reference number.
    edition: str = ""
    # The time the data describes, in the publisher's terms.
    data_period: Period | None = None
    # The parameters that are part of the file's address, by name. The address holds no
    # other, and no other is written in a receipt: a publisher may add a key on the way.
    # A receipt keeps each only with the value that `url` gives it.
    url_parameters: tuple[str, ...] = ()
    # Hosts the publisher is known to hand a download on to. No other redirect is followed.
    may_redirect_to: tuple[str, ...] = ()
    # What nobody has yet checked, by the name of the field.
    unsure: tuple[str, ...] = ()
    # The publisher will not give the file to a program, so a person saves it.
    by_hand: bool = False
    notes: str = ""

    @model_validator(mode="after")
    def _holds_together(self) -> Self:
        if not _https(self.page):
            raise ValueError("page is an https address")
        for address in (self.page, self.url):
            if address and urlsplit(address).username is not None:
                raise ValueError("an address holds a login")
        if self.url and not _https(self.url):
            raise ValueError("url is an https address, or is left empty")
        if ";" in self.url.partition("#")[0]:
            raise ValueError(
                "url holds `;`. Some servers read what follows it as a parameter, so a key "
                "could stand there unseen. List the address without it"
            )
        for name in self.url_parameters:
            if not re.fullmatch(PARAMETER, name):
                raise ValueError(
                    "url_parameters names each parameter by letters, digits and . _ ~ - alone"
                )
            if SECRET_NAME.search(name):
                raise ValueError(
                    "url_parameters names a parameter that is taken for a key. A key is no "
                    "part of an address that is written down"
                )
        held = parse_qsl(urlsplit(self.url).query, keep_blank_values=True)
        if {name for name, _ in held} - set(self.url_parameters):
            raise ValueError(
                "url holds a parameter that url_parameters does not name. Name it there if "
                "it is part of the file's address, and take it out of url if it is not"
            )
        if unknown := sorted(set(self.unsure) - MAY_BE_UNSURE):
            raise ValueError(f"unsure names `{unknown[0]}`, which is not a field to be unsure of")
        return self

    @property
    def has_an_address(self) -> bool:
        return bool(self.url)

    @property
    def ready_for_a_receipt(self) -> bool:
        """Whether the edition and the period are stated, and somebody is sure of both."""
        stated = bool(self.edition) and self.data_period is not None
        return stated and not {"edition", "data_period"} & set(self.unsure)


class FetchList(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    build: str = Field(pattern=NAME)
    files: tuple[Listed, ...]

    def item(self, name: str) -> Listed:
        for file in self.files:
            if file.item == name:
                return file
        raise ListError(f"the list {self.build} holds no item of that name")


def load_list(which: str | Path) -> FetchList:
    """Read a list, by its name in `lists/` or by the path of a file."""
    if isinstance(which, str):
        path = LISTS / f"{which}.toml"
        if not _is_a_name(which) or not path.is_file():
            raise ListError("there is no list of that name")
    else:
        path = which
    try:
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError:
        raise ListError("the list could not be read from disk") from None
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        raise ListError("the list is not valid TOML") from None

    if document.get("schema_version") != SCHEMA_VERSION:
        raise ListError(f"the list must say schema_version = {SCHEMA_VERSION}")
    if unknown := sorted(set(document) - {"schema_version", "build", "file"}):
        raise ListError(f"the list holds `{unknown[0]}`. Files are written as [[file]]")
    entries = document.get("file", [])
    if not isinstance(entries, list) or not all(
        isinstance(entry, dict) for entry in cast(list[object], entries)
    ):
        raise ListError("files are written as [[file]] tables")

    files: list[Listed] = []
    for position, entry in enumerate(cast(list[dict[str, Any]], entries), start=1):
        try:
            files.append(Listed.model_validate(entry))
        except ValidationError as error:
            name = entry.get("item")
            label = name if isinstance(name, str) and _is_a_name(name) else f"file {position}"
            raise ListError(f"{label}: {in_words(error)}") from None
    names = [file.item for file in files]
    if repeated := sorted({name for name in names if names.count(name) > 1}):
        raise ListError(f"an item is listed more than once: {repeated[0]}")
    try:
        return FetchList(build=document.get("build", ""), files=tuple(files))
    except ValidationError as error:
        raise ListError(f"the list: {in_words(error)}") from None


def _is_a_name(text: str) -> bool:
    return re.fullmatch(NAME, text) is not None
