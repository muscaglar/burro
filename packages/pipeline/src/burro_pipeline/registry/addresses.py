"""The addresses of an entry's files, and whether an address is one of them.

A publisher serves many datasets from one host. So the host of an address says
nothing of what a file is, and an entry names the addresses of its files under
`file_urls`:

- a whole address, which names itself and no other
- a prefix, which ends in `/` and names every address under it. It ends at the
  dataset: everything under it is a file of this entry and of no other

An address passes only under the entry that names it. It is compared as it is
written, letter for letter. Only the scheme and the host are read in any case,
the host with or without a dot after it, and the port of https may be left
out. An address that is written so that a server could read it as another is
named by nothing: one with `..` in it, a doubled `/`, a `\\`, a space, or a
sign that is encoded to hide one of these.

Nothing here reads a file or reaches a network.
"""

import unicodedata
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from urllib.parse import unquote, urlsplit

from burro_pipeline.registry.model import Source

# How many times a path is decoded to find what a server would read in it.
DECODED = 3
HTTPS_PORT = 443


@dataclass(frozen=True)
class Address:
    """An address as it is compared."""

    # The scheme, the host and the port: `https://files.example` or `https://files.example:8443`.
    origin: str
    # As it is written, and never empty: an address with no path is the top of its host.
    path: str
    query: str

    @property
    def is_a_prefix(self) -> bool:
        return self.path.endswith("/")

    def folded(self) -> tuple[str, str]:
        """The path and the query as a server that reads no case and decodes once may read them."""
        return unquote(self.path).casefold(), self.query.casefold()


def _is_written_plainly(path: str) -> bool:
    """Whether a path can be read one way only, however many times a server decodes it."""
    for _ in range(DECODED + 1):
        # A sign of another width, or one that is encoded wrongly, may be read as a plain one.
        read_as = unicodedata.normalize("NFKC", path)
        if any(ord(sign) < 0x20 or sign in "\\\x7f�" for sign in read_as):
            return False
        *folders, last = read_as.split("/")[1:] or [""]
        if "" in folders or not {".", ".."}.isdisjoint((*folders, last)):
            return False
        decoded = unquote(path)
        if decoded == path:
            return True
        path = decoded
    # Still not what a server would read. It is written to hide something.
    return False


def read(address: str) -> Address | None:
    """An address as it is compared, or nothing if it cannot be read one way only.

    What stands after `#` is a part of a page. It is never sent to a server,
    so it is left out. A letter outside ASCII is let through: the download
    refuses such an address with a reason of its own, and asks nothing of it.
    """
    address = address.partition("#")[0]
    if any(ord(sign) <= 0x20 or sign in "\\\x7f" for sign in address):
        return None
    try:
        parts = urlsplit(address)
        port = parts.port
    except ValueError:
        return None
    host = (parts.hostname or "").lower().rstrip(".")
    if parts.scheme.lower() != "https" or not host or port == 0:
        return None
    if parts.username is not None or parts.password is not None:
        return None
    path = parts.path or "/"
    if not _is_written_plainly(path):
        return None
    if ":" in host:
        host = f"[{host}]"
    origin = f"https://{host}" if port in (None, HTTPS_PORT) else f"https://{host}:{port}"
    return Address(origin, path, parts.query)


def names(held: str, address: str) -> bool:
    """Whether an address written under `file_urls` names an address that is asked about."""
    named, asked = read(held), read(address)
    if named is None or asked is None or named.origin != asked.origin:
        return False
    if named.is_a_prefix:
        return not named.query and asked.path.startswith(named.path)
    return (asked.path, asked.query) == (named.path, named.query)


def is_a_file_of(source: Source, address: str) -> bool:
    """Whether an address is one that an entry names for its files."""
    return any(names(held, address) for held in source.file_urls)


def _same_but_for_a_parameter(one: tuple[str, str], other: tuple[str, str]) -> bool:
    """Whether two whole addresses may be one. An address with no parameter may be another
    with its parameter left out."""
    (left, left_query), (right, right_query) = one, other
    return left == right and (left_query == right_query or not left_query or not right_query)


def _takes_in(held: Address, asked: Address) -> bool:
    """Whether an address under `file_urls` takes in an address, read without case."""
    if held.origin != asked.origin:
        return False
    if held.is_a_prefix:
        return asked.folded()[0].startswith(held.folded()[0])
    return _same_but_for_a_parameter(held.folded(), asked.folded())


def _may_be_the_same(one: Address, other: Address) -> bool:
    """Whether some address could pass under both of two addresses under `file_urls`."""
    return _takes_in(one, other) or _takes_in(other, one)


def _read_all(written: Iterable[str]) -> list[Address]:
    return [address for address in map(read, written) if address is not None]


def _holds(source: Source, asked: Address) -> bool:
    if any(_takes_in(held, asked) for held in _read_all(source.file_urls)):
        return True
    pages = _read_all((source.url, *source.evidence_urls))
    return any((page.origin, page.folded()) == (asked.origin, asked.folded()) for page in pages)


def holds(source: Source, address: str) -> bool:
    """Whether an entry holds an address at all: as its own page, its evidence, or a file.

    It is read without case and decoded once, to be on the safe side: this is
    asked of an address that a file must not have come from.
    """
    asked = read(address)
    return asked is not None and _holds(source, asked)


def _readings(asked: Address) -> Iterator[Address]:
    """An address as it is written, and as a server that decodes it again would read it.

    Only the path is decoded again. So a space that is encoded in the name of a
    file stays a part of that name, and is not taken for the end of the address.
    """
    path = asked.path
    for _ in range(DECODED + 1):
        yield Address(asked.origin, path, asked.query)
        decoded = unquote(path)
        if decoded == path:
            return
        path = decoded


def holds_however_it_is_read(source: Source, address: str) -> bool:
    """Whether an entry holds an address, as it is written or as a server may read it.

    A letter that is encoded more than once is read by a server that decodes
    more than once. This is asked only of an address that a file must not have
    come from, so that reading it more ways can refuse more and allow no more.
    An address that cannot be read one way only is held by nothing here: whoever
    asks refuses it first.
    """
    asked = read(address)
    return asked is not None and any(_holds(source, reading) for reading in _readings(asked))


def written_wrongly(source: Source) -> Iterator[str]:
    """What is wrong with the addresses an entry names for its files, one by one."""
    seen: list[Address] = []
    for position, written in enumerate(source.file_urls, start=1):
        which = f"file_urls, address {position}"
        address = read(written) if written.isascii() and "#" not in written else None
        if address is None:
            yield (
                f"{which} is not an https address that reads one way only: it holds a login, "
                "a part of a page after `#`, a space, a letter outside ASCII, `..`, `//` or "
                "`\\`, or a sign encoded to hide one"
            )
            continue
        if address.is_a_prefix and address.path == "/":
            yield f"{which} is the whole of a host. A prefix ends at the dataset"
        if address.is_a_prefix and (address.query or written.endswith("?")):
            yield f"{which} ends in `/`, so it is a prefix, and a prefix holds no parameter"
        if any(_may_be_the_same(address, before) for before in seen):
            yield f"{which} is named already by another address of this entry"
        seen.append(address)


def held_by_two(sources: Iterable[Source]) -> Iterator[tuple[Source, Source]]:
    """Each entry that names, for its files, an address that another entry holds.

    It is given with the other entry. An address that another entry holds is
    one of its files, its own page, or a page of its evidence.
    """
    sources = tuple(sources)
    files = {source.id: _read_all(source.file_urls) for source in sources}
    pages = {source.id: _read_all((source.url, *source.evidence_urls)) for source in sources}
    for source in sources:
        for other in sources if files[source.id] else ():
            if other.id == source.id:
                continue
            same_file = any(
                _may_be_the_same(held, theirs)
                for held in files[source.id]
                for theirs in files[other.id]
            )
            their_page = any(
                _takes_in(held, page) for held in files[source.id] for page in pages[other.id]
            )
            if same_file or their_page:
                yield source, other
