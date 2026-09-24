"""A stand-in publisher that gives a file a piece at a time, on the loopback address.

It answers as an object store does: a request that names the bytes it wants is
answered with those bytes and with what they are, and a request that names
none is answered with the whole file. It marks the version of the file, and
refuses a request for another version. Every file it gives is made up.
"""

import re
from dataclasses import dataclass, field

from .support import Answer, Seen

NAMED = re.compile(r"bytes=(\d*)-(\d*)")


@dataclass
class InPieces:
    """Answers for one made-up file, at any path. A test changes what it holds as it goes."""

    body: bytes
    # The mark of this version of the file, as a publisher writes one. None gives no mark.
    mark: str | None = '"made-up-1"'
    # Headers given with every piece.
    headers: dict[str, str] = field(default_factory=dict[str, str])
    # What to answer in place of a piece, by how many requests came before it.
    instead: dict[int, Answer] = field(default_factory=dict[int, Answer])
    # What to do to the file after so many requests: the body it holds from then on.
    then: dict[int, tuple[bytes, str | None]] = field(
        default_factory=dict[int, tuple[bytes, str | None]]
    )
    # Whether the publisher gives pieces at all.
    gives_pieces: bool = True
    requests: int = 0

    def __call__(self, request: Seen) -> Answer:
        before = self.requests
        self.requests += 1
        if before in self.then:
            self.body, self.mark = self.then[before]
        if before in self.instead:
            return self.instead[before]
        marked = {} if self.mark is None else {"ETag": self.mark}
        wanted = request.headers.get("if-match")
        if wanted is not None and wanted != self.mark:
            return Answer(412, body=b"")
        named = NAMED.fullmatch(request.headers.get("range", ""))
        if named is None or not self.gives_pieces:
            return Answer(200, {**marked, **self.headers}, self.body)
        first, last = named.groups()
        whole = len(self.body)
        if first == "":
            start, end = max(0, whole - int(last)), whole - 1
        else:
            start, end = int(first), min(int(last) if last else whole - 1, whole - 1)
        if start > end or start >= whole:
            return Answer(416, {"Content-Range": f"bytes */{whole}"}, b"")
        said = {"Content-Range": f"bytes {start}-{end}/{whole}", **marked, **self.headers}
        return Answer(206, said, self.body[start : end + 1])
