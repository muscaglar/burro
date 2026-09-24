"""The gate: the licence registry is asked, and the file is held to the entry of its source.

The registry answers for an id and a use. A list states both, beside a page
and an address, and the id alone says nothing of what the address gives. So
a file is held to the entry its id names, before anything is asked for:

- its page is the entry's own address, or one of its evidence addresses
- its address is one that the entry names for its files: a whole address, or
  one under a prefix that ends at the dataset. A publisher serves many
  datasets from one host, so the host of an address is not enough
- nothing that says what the file is names a census table about residents,
  unless the entry is under a heading that may hold one

And a file is for one part of the store: the product, the census tables about
residents, or the audit. It is refused unless the store it would be written to
is of that part. Which source is kept apart from the product is the fence's to
say, in `evidence/fence.py`: fetch asks that rule and holds none of its own.

What arrived is held too, before it is kept: the address after redirects, the
publisher's own name for the file, and the names inside a zip and inside every
zip it holds. A zip that cannot be looked into is not kept. Nor is a file that
arrived, in the end, from an address that another entry holds, from an address
on a host of its entry that the entry does not hold, or from an address that
cannot be read one way only.

A table that is named with no code cannot be caught by its name. It is caught
by its address: no entry may name an address that another holds.

What a census table about residents is, is the registry's to say. Its own rule
is asked, of the entry as it would stand if it named what the file names. Fetch
holds no list of tables and no pattern of its own.

A refusal is a reason from a fixed list. It repeats no address and no name.
"""

from collections.abc import Iterable
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Protocol
from urllib.parse import unquote, urlsplit

from burro_pipeline.evidence.fence import USES_KEPT_APART, source_is_kept_apart
from burro_pipeline.fetch.kinds import CannotSeeInside, names_inside
from burro_pipeline.fetch.sources import Listed
from burro_pipeline.fetch.store import Part
from burro_pipeline.registry import Dimension, RegistryError, Source, Use
from burro_pipeline.registry.addresses import holds, holds_however_it_is_read, is_a_file_of, read
from burro_pipeline.registry.rules import (
    may_be_scored,
    resident_tables_sit_under_residents_or_audit,
)

# How many times an address is decoded to find what a server would read in it.
DECODED = 3


class Reason(StrEnum):
    GATE = "the licence registry refuses this source for this use"
    NOT_THE_STORE = "it is for another part of the store"
    NOT_THE_PAGE = "the page is not one the registry entry holds"
    NOT_THE_HOST = "the address is on a host the registry entry does not name"
    NOT_THE_ADDRESS = "the address is not one the registry entry names for its files"
    RESIDENT_TABLE = "it names a census table about residents"
    CANNOT_SEE_INSIDE = "it is a zip, or holds one, that cannot be looked into"


class Refused(Exception):
    """A file that the gate does not let through. Safe to print."""

    def __init__(self, reason: Reason, detail: str = "") -> None:
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason.value}: {detail}" if detail else reason.value)


class Asked(Protocol):
    """What is asked of a registry here: the gate, and nothing else."""

    def require(self, source_id: str, use: Use) -> Source: ...


def host_of(address: str) -> str:
    """The host of an address, as it is compared: in lower case, with no dot after it."""
    try:
        return (urlsplit(address).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""


def pages_of(source: Source) -> tuple[str, ...]:
    """The addresses an entry holds for its data: its own, and its evidence."""
    return (source.url, *source.evidence_urls)


def hosts_of(source: Source) -> frozenset[str]:
    """The hosts an entry names. The host of its licence is not one: no file is kept there."""
    named = (*pages_of(source), *source.file_urls)
    return frozenset(host_of(address) for address in named) - {""}


def _every_way(said: Iterable[str]) -> str:
    """What was said, as it is written and as a publisher's server would read it."""
    forms: list[str] = []
    for text in said:
        forms.append(text)
        for _ in range(DECODED):
            decoded = unquote(text)
            if decoded == text:
                break
            forms.append(decoded)
            text = decoded
    return " ".join(forms)


def _names_a_table_about_residents(source: Source, said: Iterable[str]) -> bool:
    # The entry as it would stand if it named what the file names. The rule reads an
    # entry's name, and refuses nothing of an entry that may hold such a table.
    as_if = source.model_copy(update={"name": f"{source.name} {_every_way(said)}"})
    if any(True for _ in resident_tables_sit_under_residents_or_audit(as_if, date.min)):
        return True
    # A source about residents that may feed a score holds age and household composition
    # and no other table. So what names a file of it names no other table either.
    return may_be_scored(source) and not may_be_scored(as_if)


def hold_the_address(source: Source, address: str) -> None:
    """Refuse an address that the entry does not name, or that names a table it may not.

    The host is asked first, and says the more to a person: an address on a
    host the entry names nowhere is most often a slip in the list.
    """
    if host_of(address) not in hosts_of(source):
        raise Refused(Reason.NOT_THE_HOST)
    if _names_a_table_about_residents(source, (address,)):
        raise Refused(Reason.RESIDENT_TABLE)
    if not is_a_file_of(source, address):
        raise Refused(Reason.NOT_THE_ADDRESS)


def hold_where_it_ended(source: Source, registry: Iterable[Source], address: str) -> None:
    """Refuse a file that arrived, in the end, from an address it must not have come from.

    A publisher may send a request on. Where it ends is not in the list. On a
    host that the entry names, other datasets stand beside this one, so the
    address must be one the entry holds. On any other host, which only the
    list names, it must be no address that another entry holds. A file that
    came from the page or the file of another entry is that entry's file.

    An address that cannot be read one way only is refused first, on any host:
    one with `..` or a doubled `/` in it, a login, or a sign encoded to hide
    one. What a server read in it is not known, so nothing shows whose file
    arrived. And an address is another entry's however a server may have read
    it: as it is written, or decoded again.
    """
    if read(address) is None:
        raise Refused(Reason.NOT_THE_ADDRESS)
    if holds(source, address):
        return
    if host_of(address) in hosts_of(source):
        raise Refused(Reason.NOT_THE_ADDRESS)
    others = (other for other in registry if other.id != source.id)
    if any(holds_however_it_is_read(other, address) for other in others):
        raise Refused(Reason.NOT_THE_ADDRESS)


def hold(file: Listed, source: Source) -> None:
    """Refuse a file of a list that is not as the entry of its source has it."""
    if file.page not in pages_of(source):
        raise Refused(Reason.NOT_THE_PAGE)
    if file.url:
        hold_the_address(source, file.url)
    if _names_a_table_about_residents(source, (file.item, file.what, file.edition)):
        raise Refused(Reason.RESIDENT_TABLE)


def hold_what_arrived(source: Source, *named: str) -> None:
    """Refuse a file that has arrived and names a table its entry may not hold.

    `named` is everything that names it: the address it came from in the end,
    the publisher's own name for it, and the names of the files inside it.
    """
    if _names_a_table_about_residents(source, named):
        raise Refused(Reason.RESIDENT_TABLE)


def hold_the_file(source: Source, path: Path, *named: str) -> None:
    """Refuse a file that has arrived for what names it, or for what it holds.

    `named` is as for `hold_what_arrived`. The names inside the file are read
    here, all the way down, and a file that cannot be looked into is refused.
    """
    try:
        inside = names_inside(path)
    except CannotSeeInside:
        raise Refused(Reason.CANNOT_SEE_INSIDE) from None
    hold_what_arrived(source, *named, *inside)


def part_of(use: Use, source: Source) -> Part:
    """The part of the store a file is for.

    Whether a file is kept apart is the fence's to say, and fetch asks the
    rule that `seal` and `check` ask: by the use, or by what the registry
    holds the source for, under any heading and whatever the list asks for.
    If fetch read it another way, it would keep a file in the product's store
    that `seal` then refuses. A file kept apart is for the audit's part, unless
    it is a census table about residents.
    """
    if use not in USES_KEPT_APART and not source_is_kept_apart(source):
        return Part.PRODUCT
    if source.dimension is Dimension.AUDIT:
        return Part.AUDIT
    if source.dimension is Dimension.RESIDENTS or Use.CENSUS_TABLE in (use, *source.uses):
        return Part.RESIDENTS
    return Part.AUDIT


def ask(file: Listed, registry: Asked, part: Part = Part.PRODUCT) -> Source:
    """Ask the registry about a file of a list, and hold the file to the entry it names.

    `part` is the part of the store the file would be written to. Every store
    that can be named today is the product's, so a file for the audit or for
    the census table is refused here, and that is the whole of what is built
    for them.
    """
    try:
        source = registry.require(file.source_id, file.use)
    except RegistryError as error:
        raise Refused(Reason.GATE, str(error)) from None
    if part_of(file.use, source) is not part:
        raise Refused(Reason.NOT_THE_STORE)
    hold(file, source)
    return source
