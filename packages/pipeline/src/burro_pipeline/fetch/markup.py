"""Reading XML that somebody else wrote, with the standard library.

A workbook is a zip of XML, and the object store answers a listing in XML.
Neither needs a document type or an entity of its own, and both are how an XML
file is made to grow without limit or to reach outside itself. So a document
that declares either is refused before anything is read from it.
"""

from collections.abc import Callable
from typing import Protocol
from xml.parsers import expat

Start = Callable[[str, dict[str, str]], None]
End = Callable[[str], None]
Text = Callable[[str], None]

# Expat joins a namespace and a name with this. A name is compared by its last part,
# so a document that uses another prefix, or the strict namespaces, reads the same.
SEPARATOR = " "


class Readable(Protocol):
    def read(self, size: int = ..., /) -> bytes: ...


class MarkupError(Exception):
    """The XML could not be read. The message repeats nothing from the document."""


class Finished(Exception):
    """Raised by a handler that has read all it needs, to stop early."""


def local(name: str) -> str:
    return name.rsplit(SEPARATOR, 1)[-1]


class Limited:
    """A stream that is read up to a size and no further."""

    def __init__(self, source: Readable, limit: int, over: Exception) -> None:
        self._source, self._left, self._over = source, limit, over

    def read(self, size: int = -1, /) -> bytes:
        piece = self._source.read(size)
        self._left -= len(piece)
        if self._left < 0:
            raise self._over
        return piece


def _refuse(*_: object) -> None:
    raise MarkupError("the XML declares a document type or an entity, so it was not read")


def _refuse_a_reference(*_: object) -> int:
    raise MarkupError("the XML declares a document type or an entity, so it was not read")


def read(
    source: Readable | bytes,
    start: Start | None = None,
    end: End | None = None,
    text: Text | None = None,
) -> None:
    """Walk a document once, calling back with local names. Nothing is kept in memory."""
    parser = expat.ParserCreate(namespace_separator=SEPARATOR)
    parser.buffer_text = True
    parser.StartDoctypeDeclHandler = _refuse
    parser.EntityDeclHandler = _refuse
    parser.UnparsedEntityDeclHandler = _refuse
    parser.ExternalEntityRefHandler = _refuse_a_reference
    if start is not None:
        parser.StartElementHandler = lambda name, given: start(
            local(name), {local(key): value for key, value in given.items()}
        )
    if end is not None:
        parser.EndElementHandler = lambda name: end(local(name))
    if text is not None:
        parser.CharacterDataHandler = text
    try:
        if isinstance(source, bytes):
            parser.Parse(source, True)
        else:
            parser.ParseFile(source)
    except Finished:
        return
    except expat.ExpatError as error:
        raise MarkupError(f"the XML is not well formed at line {error.lineno}") from None
