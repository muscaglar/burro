"""The desk's server: one page and its answers, on this machine alone.

It binds to the loopback address and to no other. It answers a request only when
the request names this server as its host, comes from this server's own page, and,
to write, holds the token this run made. It writes nowhere but the two folders of
decisions, and only by adding a line, which is on disk before it answers.

It never builds a path from the words of a request. A page's file, a queue, an
item, a group and a layer are keys of tables made when it starts, and a word
that is no key finds nothing.

What it prints is the method, the route's template and the status. Never an item,
an answer or a note.

Standard library only. See docs/design/desk.md, section 4.
"""

import errno
import hmac
import json
import secrets
import sys
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Final, cast
from urllib.parse import unquote

from desk import records
from desk.records import (
    DISPUTED,
    DONE,
    FOUNDER,
    MOVE,
    NOTE_LIMIT,
    OF_RULES,
    RULE,
    SECONDS_LIMIT,
    SKIP,
    UNDO,
    Broken,
    Item,
    Items,
    Json,
    Line,
    Question,
    Read,
    Standing,
    Unfit,
)

LOOPBACK: Final = "127.0.0.1"
PORT: Final = 8765
BODY_LIMIT: Final = 16 * 1024
# A body that is too large is read and thrown away up to here, so that the refusal is heard.
DRAIN_LIMIT: Final = 1024 * 1024
DRAIN_WAIT: Final = 0.2

BANNER: Final = {
    True: "MADE-UP CITY. Nothing here is a real place.",
    False: (
        "REAL DATA FOR LONDON. A draft that nobody has checked. What you decide here is built."
    ),
}

# Sent with every answer. With them the browser itself refuses any other host.
HEADERS: Final = (
    (
        "Content-Security-Policy",
        "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; "
        "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
    ),
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "no-referrer"),
    ("Cache-Control", "no-store"),
    ("Cross-Origin-Resource-Policy", "same-origin"),
)

# The files of the page that are served, by ending. No other file of the folder is.
KINDS: Final = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
}
JSON_KIND: Final = "application/json; charset=utf-8"
HTML_KIND: Final = KINDS[".html"]

# What a browser is given for an icon, so that it logs no fault for the lack of one:
# a drawing with nothing in it.
ICON: Final = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"/>'

# What a request to decide holds: these fields, all of them, and no other.
DECIDE: Final = frozenset(
    {
        *("queue", "item", "rev", "part", "answer"),
        *("note", "second", "settles", "detail", "seconds", "stands"),
    }
)

FORBIDDEN, NOT_FOUND, BAD_REQUEST = "forbidden", "not_found", "bad_request"
STALE_ITEM, TOO_LARGE, NOT_SAVED = "stale_item", "too_large", "not_saved"
ALREADY: Final = "already_answered"
# Fixed words. A refusal never repeats what was sent.
WORDS: Final = {
    FORBIDDEN: "The desk did not take this. Load the page again from the address it printed.",
    NOT_FOUND: "The desk holds nothing by that name.",
    BAD_REQUEST: "The desk could not read what was sent.",
    STALE_ITEM: "This item has changed since it was shown. It is shown again.",
    TOO_LARGE: "What was sent is too long.",
    ALREADY: "This item has an answer already. It is shown again.",
    NOT_SAVED: "Not saved. Start the desk again with make desk.",
}
# What a fault of the disk is said as, by its number. The words hold no path and no line,
# and say what a person can do: starting the desk again makes no room on a disk.
DISK_FULL: Final = (
    "Not saved. The disk is full. Make room on it. The desk need not be started again."
)
MAY_NOT_WRITE: Final = "Not saved. The desk may not write to its folder. Give it leave to."
COPY_DIFFERS: Final = (
    "Not saved in the kept copy, which holds what the desk's folder does not. "
    "Stop the desk, and look at both."
)
FAULTS: Final = {
    errno.ENOSPC: DISK_FULL,
    errno.EDQUOT: DISK_FULL,
    errno.EACCES: MAY_NOT_WRITE,
    errno.EPERM: MAY_NOT_WRITE,
    errno.EROFS: MAY_NOT_WRITE,
}
NEEDS_NOTE: Final = "This answer needs a note. Say why."
NOT_AN_ANSWER: Final = "That is not one of the answers to this question."
NOTHING_TO_SETTLE: Final = "There is no dispute on this item to settle."
NOT_THE_FOUNDER: Final = "Only the first reviewer settles a dispute."
NOT_A_SPELLING: Final = "That spelling is not one a source wrote."
NOTE_NOT_PLAIN: Final = "A note is one line of plain text."
NOT_AN_AREA: Final = (
    "The desk cannot make an area of another name. If it should be one, write a note and skip it."
)
# An item of a name that was proposed as another name of an area, and the answer that would
# make it an area. Only the areas build gives an area its id, so a build could not apply it.
OTHER_NAME, AREA = "a:", "area"
METHOD_NOT_KNOWN: Final = "The desk takes GET and POST, and nothing else."


class Refused(Exception):
    """A request the desk does not take. It holds the status, the code and fixed words.

    `elsewhere` is true of one refusal alone: the address of the desk, opened by a browser
    from another page. It is told how to open the desk, in a page of its own.
    """

    def __init__(
        self,
        status: HTTPStatus,
        error: str,
        words: str | None = None,
        *,
        elsewhere: bool = False,
    ) -> None:
        super().__init__(error)
        self.status, self.error, self.words = status, error, words or WORDS[error]
        self.elsewhere = elsewhere


def _elsewhere(banner: str) -> bytes:
    """The page a person is given who opened the address from another page.

    A browser says of a click in a chat, in a terminal on the web or in any other page
    that it came from another site, and the desk gives such a request nothing it holds.
    So the person is told what to do, and the link is a request of the desk's own page,
    which the desk takes. The words are fixed: nothing of the request is in them.
    """
    return (
        '<!doctype html>\n<html lang="en-GB">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Burro review desk</title>\n</head>\n<body>\n"
        f"<p><strong>{banner}</strong></p>\n"
        "<h1>The review desk</h1>\n"
        "<p>Your browser opened this address from another page or program, "
        "so the desk did not show itself. Nothing is wrong, and nothing was changed.</p>\n"
        '<p><a href="/">Open the desk</a></p>\n'
        "<p>Or type the address into the address bar of the browser, and press Enter.</p>\n"
        "</body>\n</html>\n"
    ).encode()


# By whether the desk holds the made-up city.
ELSEWHERE: Final = {made_up: _elsewhere(words) for made_up, words in BANNER.items()}


def bad(words: str | None = None) -> Refused:
    return Refused(HTTPStatus.BAD_REQUEST, BAD_REQUEST, words)


def missing() -> Refused:
    return Refused(HTTPStatus.NOT_FOUND, NOT_FOUND)


# The desk


def say(line: str) -> None:
    """Print a line at once, so that it is seen when it happens, in a file as on a screen."""
    sys.stdout.write(f"{line}\n")
    sys.stdout.flush()


@dataclass(frozen=True, slots=True)
class Desk:
    """All that the server knows. It is made once, when the server starts."""

    data: Path
    reviewer: str
    synthetic: bool
    # The queues this reviewer is asked to work, in the order of the questions, which is
    # the order of the work. Each has items.
    questions: Mapping[str, Question]
    items: Mapping[str, Items]
    # The files of the page by name, and the layers by group and layer.
    pages: Mapping[str, Path]
    layers: Mapping[tuple[str, str], Path]
    clock: Callable[[], datetime] = records.now
    # What the server prints. It is handed the method, the template and the status.
    log: Callable[[str], None] = say
    token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    # One line is written at a time.
    lock: threading.Lock = field(default_factory=threading.Lock)
    # Where a second copy of every line is kept, outside the repository. None keeps none.
    keep: Path | None = None
    # Every queue that has items, whoever works it: a queue may wait on one of them.
    every: Mapping[str, Question] = field(default_factory=lambda: dict[str, Question]())
    # What each file of decisions held when it was last read, while it stands as it did.
    files: records.Files = field(default_factory=records.Files)
    # How many lines the kept copy lacked when the desk started, which it then wrote.
    brought_up: int = 0


def _files(folder: Path, endings: frozenset[str]) -> dict[str, Path]:
    """The plain files of a folder by name. A link is left out: it may lead anywhere."""
    if not folder.is_dir():
        return {}
    return {
        path.name: path
        for path in sorted(folder.iterdir())
        if path.suffix in endings and path.is_file() and not path.is_symlink()
    }


# The folder where the second copy is kept unless another is named, by its name alone. It
# is looked for in the home folder of whoever starts the desk. No path is written here:
# a path names a machine, and whoever works on it.
KEPT_IN_HOME: Final = "burro-desk-decisions"
NEEDS_KEEP: Final = (
    "On real data the desk keeps a second copy of every decision, outside the repository, "
    f"because one git command can remove the first. Make the folder {KEPT_IN_HOME} in your "
    "home folder, or name another: make desk KEEP=FOLDER"
)


class NeedsKeep(Unfit):
    """Real data, and no folder named for the second copy of every decision."""


def _within(path: Path, folder: Path) -> bool:
    whole, held = path.resolve(), folder.resolve()
    return whole == held or held in whole.parents or whole in held.parents


def kept_copy(data: Path, page: Path, keep: Path, outside: Path | None) -> int:
    """Hold the kept copy to the folder of decisions, and bring it up where it is behind.
    Returns how many lines it lacked. Raises `Unfit` where it may not be kept there, or
    where it holds what the folder does not: then a person must look, and nothing is written."""
    if any(_within(keep, each) for each in (data, page.parent)):
        raise Unfit("The copy is kept apart from the desk's own folders. Choose another folder.")
    if outside is not None and outside.resolve() in keep.resolve().parents:
        raise Unfit(
            "The copy is kept outside the repository, where no git command reaches it. "
            "Choose a folder elsewhere."
        )
    found = records.compare(data, keep)
    if found.ahead:
        raise Unfit(
            "The kept copy holds decisions that the desk's folder has lost: "
            f"{', '.join(found.ahead)}. Copy them back before you start, from the folder "
            "of the copy into the desk's folder of data. Nothing was changed."
        )
    if found.differ:
        raise Unfit(
            f"The kept copy and the desk's folder differ: {', '.join(found.differ)}. "
            "Look at both before you start. Nothing was changed."
        )
    return sum(records.keep_up(data / name, keep / name) for name in found.behind)


def open_desk(
    data: Path,
    page: Path,
    questions: Path,
    reviewer: str,
    *,
    clock: Callable[[], datetime] = records.now,
    log: Callable[[str], None] = say,
    keep: Path | None = None,
    outside: Path | None = None,
) -> Desk:
    """Read what the desk serves. Raises `Unfit`, in words a person can act on.

    `keep` is where a second copy of every line is kept, and `outside` the repository it
    must lie outside of. Real data is not served without a copy.
    """
    if not records.REVIEWER.fullmatch(reviewer):
        raise Unfit("A reviewer is r1, r2 and so on up to r99. It is a label, never a name.")
    asked = records.read_questions(questions)
    found = {
        name: records.read_items(path)
        for name, path in _files(data / "items", frozenset({".jsonl"})).items()
    }
    items = {each.queue: each for each in found.values()}
    if not items:
        raise Unfit("There is no item to show. Fill the queues with make desk-fill.")
    for queue, held in items.items():
        if queue not in asked:
            raise Unfit(f"items/{queue}.jsonl is of a queue that has no question.")
        if held.question != asked[queue].version:
            raise Unfit(
                f"items/{queue}.jsonl was made for another version of its question. "
                "Fill the queues again with make desk-fill."
            )
    if len({held.synthetic for held in items.values()}) != 1:
        raise Unfit("Some items are of the made-up city and some are real. Fill the queues again.")
    astray = records.misplaced(data, asked)
    if astray:
        raise Unfit(
            f"Decisions are in the wrong folder: {', '.join(astray)}. Lines that may be "
            f"published are kept in {records.PUBLIC_TREE}, and the rest in "
            f"{records.PRIVATE_TREE}. Move each folder, then start again."
        )
    pages = _files(page, frozenset(KINDS))
    if "index.html" not in pages:
        raise Unfit("The page is missing: there is no index.html to serve.")
    layers = {
        (group.name, path.stem): path
        for group in sorted((data / "layers").glob("*"))
        if group.is_dir() and not group.is_symlink()
        for path in _files(group, frozenset({".geojson"})).values()
    }
    synthetic = next(iter(items.values())).synthetic
    if keep is None and not synthetic:
        raise NeedsKeep(NEEDS_KEEP)
    brought_up = 0 if keep is None else kept_copy(data, page, keep, outside)
    listed = {
        name: asked[name]
        for name in asked
        if name in items and (reviewer == FOUNDER or asked[name].open_to_all)
    }
    if not listed:
        raise Unfit("No queue here is one that a second reviewer is asked to work.")
    return Desk(
        data=data,
        reviewer=reviewer,
        synthetic=synthetic,
        questions=listed,
        every={name: asked[name] for name in asked if name in items},
        items=items,
        pages=pages,
        layers=layers,
        clock=clock,
        log=log,
        keep=keep,
        brought_up=brought_up,
    )


# What is answered. Each asks what the files of decisions hold. A file is read from the
# disk whenever it has changed, and nothing is kept from one run to the next.


@dataclass(frozen=True, slots=True)
class Queue:
    """One queue as it stands now: its question, its items and every reviewer's lines."""

    question: Question
    items: Items
    reads: Mapping[str, Read]
    stands: Mapping[str, Standing]
    # How well the reviewer says they know each borough. What they know comes first.
    known: Mapping[str, str] = field(default_factory=lambda: dict[str, str]())

    def state_of(self, reviewer: str, item: Item) -> str:
        return records.state_of(reviewer, item, self.question, self.stands)


def _read(desk: Desk, question: Question) -> tuple[dict[str, Read], dict[str, Standing]]:
    reads = records.read_queue(
        desk.data, question.queue, private=question.private, files=desk.files
    )
    return reads, {name: records.standing(held.lines) for name, held in reads.items()}


def _known(desk: Desk) -> dict[str, str]:
    """How well this reviewer says they know each borough, where the desk asks it."""
    asked = desk.every.get(records.KNOW)
    if asked is None:
        return {}
    items, (_, stands) = desk.items[records.KNOW], _read(desk, asked)
    mine = stands.get(desk.reviewer, records.NOTHING)
    fresh = {
        name: line
        for name, line in mine.answers.items()
        if name in items.by_id and records.fresh(line, items.by_id[name], asked)
    }
    return records.known_by(Standing(fresh, {}, None))


def look(desk: Desk, queue: str) -> Queue:
    if queue not in desk.questions:
        raise missing()
    reads, stands = _read(desk, desk.questions[queue])
    known = _known(desk) if queue in records.BY_KNOWN else {}
    return Queue(desk.questions[queue], desk.items[queue], reads, stands, known)


def waits(desk: Desk, question: Question) -> list[Json]:
    """What a queue waits on: each queue it is made from that the founder has not
    finished, with how many of its items are left. Names are decided before borders are
    drafted, and a name changed afterwards reopens the borders made from it.

    A queue waits too on every answer of the founder's that a build will set aside until
    the draft is made again: `set_aside` says how many, where there are any. A border
    looked at before then is drawn round a name that is to go."""
    found: list[Json] = []
    for name in question.after:
        asked = desk.every.get(name)
        if asked is None:
            continue
        reads, stands = _read(desk, asked)
        left = records.progress(FOUNDER, desk.items[name], asked, reads).left
        aside = records.set_aside(FOUNDER, desk.items[name], asked, stands)
        if left or aside:
            row: dict[str, Json] = {"queue": name, "title": asked.title, "left": left}
            found.append({**row, records.SET_ASIDE: aside} if aside else row)
    return found


def counts(desk: Desk, now: Queue) -> dict[str, Json]:
    found = records.progress(desk.reviewer, now.items, now.question, now.reads)
    about: dict[str, Json] = {"queue": now.question.queue, "title": now.question.title}
    # What a rule settled is counted as the rule's, so that no answer is counted twice.
    aside = records.set_aside(desk.reviewer, now.items, now.question, now.stands, own=True)
    more: dict[str, Json] = {records.SET_ASIDE: aside, "waits": waits(desk, now.question)}
    return {**about, **found.as_dict(), **more}


def _resume(desk: Desk, queues: Mapping[str, Queue]) -> dict[str, Json] | None:
    """Where the reviewer left off: the first open item of the queue last worked in."""
    # A line that a rule wrote is no work of the reviewer's: it was written in the
    # queue of the rule's items while the reviewer was in the queue of rules.
    own = {
        name: [line for line in held.lines if not records.by_rule(line)]
        for name, now in queues.items()
        if (held := now.reads.get(desk.reviewer))
    }
    last = {name: max(lines, key=lambda line: line.n) for name, lines in own.items() if lines}
    if not last:
        return None
    first = max(last, key=lambda name: last[name].at)
    for name in (first, *(name for name in queues if name != first)):
        now = queues[name]
        item = records.next_item(
            desk.reviewer, now.items, now.question, now.stands, known=now.known
        )
        if item is not None:
            return {"queue": name, "item": item}
    return None


def state(desk: Desk) -> dict[str, Json]:
    queues = {name: look(desk, name) for name in desk.questions}
    return {
        "desk": records.DESK,
        "reviewer": desk.reviewer,
        "token": desk.token,
        "banner": BANNER[desk.synthetic],
        "resume": _resume(desk, queues),
        "broken_lines": sum(held.broken for now in queues.values() for held in now.reads.values()),
        "mended_lines": sum(held.mended for now in queues.values() for held in now.reads.values()),
        "queues": [counts(desk, now) for now in queues.values()],
    }


def queue(desk: Desk, name: str) -> dict[str, Json]:
    now = look(desk, name)
    ordered = records.order_for(desk.reviewer, now.items, now.stands, now.known)
    return {
        "question": dict(now.question.held),
        "items": [
            {
                "id": item.id,
                "group": item.group,
                "state": now.state_of(desk.reviewer, item),
                "flagged": bool(item.flags),
                **_part(now.question, item),
            }
            for item in ordered
        ],
    }


def _part(question: Question, held: Item) -> dict[str, Json]:
    """Which part an item is of, where one answer may be given to a whole part."""
    if question.covers is None:
        return {}
    given = cast(dict[str, Json], held.held.get("preset") or {}).get(question.covers)
    return {"part": given if isinstance(given, str) else None}


def item(desk: Desk, name: str, wanted: str) -> dict[str, Json]:
    now = look(desk, name)
    held = now.items.by_id.get(wanted)
    if held is None:
        raise missing()
    found = now.state_of(desk.reviewer, held)
    mine = now.stands.get(desk.reviewer, records.NOTHING).answers.get(held.id)
    # Another's answer is shown only once your own stands, so that agreement can be measured.
    shown = found in (DONE, DISPUTED)
    others = records.verdict(held, now.question, now.stands).answers if shown else None
    return {
        "item": dict(held.held),
        "state": found,
        **({"leans": leans(desk, held)} if name == OF_RULES else {}),
        "mine": None if mine is None else mine.as_dict(),
        "moves": [
            line.as_dict()
            for line in records.moves_of(desk.reviewer, held, now.question, now.stands)
        ],
        "others": [
            {
                "reviewer": line.reviewer,
                "answer": line.answer,
                "note": line.note,
                "at": line.at,
                # The cells they moved, so that a dispute is settled with them in view.
                "moves": [
                    {"part": move.part, **{key: move.detail.get(key) for key in ("from", "to")}}
                    for move in records.moves_of(reviewer, held, now.question, now.stands)
                ],
            }
            for reviewer, line in (others or {}).items()
            if reviewer != desk.reviewer
        ],
    }


def _is(value: object, kind: type) -> bool:
    # True is not a number here, though Python counts it as one.
    return type(value) is kind


# What a queue that adds `pick` may change in the detail: the spelling, and the areas named.
CHOSEN: Final = frozenset({"pick", "of"})


def _detail(question: Question, held: Item, answer: str, sent: dict[str, Json]) -> None:
    """Refuse a detail that a build could not use, or that the item did not give.

    A line holds what the design names and no more. So the detail is what the item was
    made with, its `preset`, and nothing a caller made up: a detail is no second note.
    """
    if answer == MOVE:
        here, there = sent.get("from"), sent.get("to")
        if set(sent) != {"from", "to"} or not (isinstance(here, str) and isinstance(there, str)):
            raise bad()
        if not (here and there and here != there):
            raise bad()
        return
    may_change = CHOSEN if "pick" in question.adds else frozenset[str]()
    given = cast(dict[str, Json], held.held.get("preset") or {})
    fixed = {key: value for key, value in given.items() if key not in may_change}
    if {key: value for key, value in sent.items() if key not in may_change} != fixed and (
        answer != SKIP or sent
    ):
        raise bad()
    spellings = held.picks if "pick" in question.adds and "pick" in sent else None
    if spellings is not None and sent["pick"] not in spellings:
        raise bad(NOT_A_SPELLING)
    of = sent.get("of", [])
    if "pick" in question.adds and not (
        isinstance(of, list) and len(of) <= 5 and all(isinstance(each, str) for each in of)
    ):
        raise bad()


def _same(line: Line | None, sent: Mapping[str, Json]) -> bool:
    """True when what was sent is the line that stands already."""
    return line is not None and all(
        getattr(line, name) == sent[name]
        for name in ("rev", "answer", "note", "second", "settles", "detail")
    )


def _file(desk: Desk, question: Question) -> Path:
    """Where this reviewer's lines of a queue are kept."""
    return records.path_of(desk.data, question.queue, desk.reviewer, private=question.private)


def _keep(desk: Desk, question: Question) -> None:
    """Write to the kept copy what it lacks of a file, before the desk answers. It is
    asked for an answer given twice too, so that a copy that could not be written when
    the line was is written when the page sends the answer again."""
    if desk.keep is not None:
        file = _file(desk, question)
        records.keep_up(file, desk.keep / file.relative_to(desk.data))


def _written(desk: Desk, now: Queue, after: str, line: Line | None) -> dict[str, Json]:
    # A rule is adopted, or is no longer, before the counts are taken.
    ruled = _settle(desk) if now.question.queue == OF_RULES else None
    again = look(desk, now.question.queue)
    return {
        "line": None if line is None else line.as_dict(),
        "next": records.next_item(
            desk.reviewer, again.items, again.question, again.stands, after, again.known
        ),
        "counts": counts(desk, again),
        **({} if ruled is None else {"ruled": ruled}),
    }


# A rule the founder adopts. A draft may put rules that would settle items with no person
# reading each. None is adopted until the founder says yes to it, in the queue of rules.
# A yes writes a line for every item the rule fits that the founder has not answered, in
# the founder's own file of that item's queue, and names the rule in each. A no writes
# nothing. When a yes no longer stands, every line it wrote is taken back by a line of
# its own. Nothing is changed and nothing is removed.
#
# A rule may lean on others: it lets an item through to the rule the item's records fit,
# and has no test of its own. Such a rule settles an item only where the rule the item
# leans on is adopted too, in whichever order the two are adopted. When that rule is no
# longer adopted, what the leaning rule settled by it is taken back with it.


def _gives(rule: Item, item: Item, question: Question) -> str | None:
    """The answer a rule gives an item: what the draft proposes, an answer of the
    question, or the answer that leaves the item as drafted. None where it has none."""
    about = cast(dict[str, Json], rule.held["preset"])
    gives = about.get(records.GIVES)
    if gives == records.PROPOSED:
        gives = cast(dict[str, Json], item.held["preset"]).get(records.PROPOSED)
    if gives == "":
        return RULE
    return gives if isinstance(gives, str) and gives in question.answers else None


# How a rule stands: the founder's yes stands, or it was given to another list of items
# than the draft now puts and the rule is asked again, or the rule is not adopted.
ADOPTED, ASKED_AGAIN, NOT_ADOPTED = "adopted", "asked_again", "not_adopted"


def _adopted(desk: Desk) -> dict[str, tuple[Item, str]]:
    """Every rule the desk holds, by its code, and how the rule stands."""
    asked = desk.every.get(OF_RULES)
    if asked is None:
        return {}
    _, stands = _read(desk, asked)
    mine = stands.get(FOUNDER, records.NOTHING).answers

    def stands_as(rule: Item) -> str:
        line = mine.get(rule.id)
        if line is None or line.answer != records.ADOPT:
            return NOT_ADOPTED
        return ADOPTED if records.fresh(line, rule, asked) else ASKED_AGAIN

    return {rule.id: (rule, stands_as(rule)) for rule in desk.items[OF_RULES].items}


def _by_rule(desk: Desk, question: Question, item: str, rev: str, answer: str, **more: Any) -> None:
    """Write one line in the founder's file of a queue, as a rule gives it or takes it
    back. It is on disk when this returns."""
    records.append(
        records.path_of(desk.data, question.queue, FOUNDER, private=question.private),
        reviewer=FOUNDER,
        queue=question.queue,
        question=question.version,
        item=item,
        rev=rev,
        answer=answer,
        synthetic=desk.synthetic,
        clock=desk.clock,
        files=desk.files,
        **more,
    )


def _stands(rules: Mapping[str, tuple[Item, str]], rule: Json) -> str:
    """How a rule stands, by its code. A rule the desk does not hold is not adopted."""
    return rules[rule][1] if isinstance(rule, str) and rule in rules else NOT_ADOPTED


def _leant_on(rules: Mapping[str, tuple[Item, str]], about: Mapping[str, Json]) -> str:
    """How the rule stands that an item leans on, as its preset or the detail of a line
    names it. An item that leans on no rule is held back by none."""
    other = about.get(records.LEANS_ON)
    return _stands(rules, other) if isinstance(other, str) else ADOPTED


def _settle_queue(desk: Desk, name: str, rules: Mapping[str, tuple[Item, str]]) -> list[int]:
    """Bring one queue to what the adopted rules say. Returns how many items were
    settled, how many answers of a rule were taken back, and how many items an adopted
    rule fits and does not settle, because the rule they lean on is not adopted.

    A rule that is asked again is left as it is until the founder answers it: nothing
    it settled is taken back, and nothing more is settled by it. An answer to an item
    the queue no longer holds is taken back with its rule, as any other is. So is what
    a rule settled by leaning on a rule that is no longer adopted.
    """
    question, items = desk.every[name], desk.items[name]
    path = records.path_of(desk.data, name, FOUNDER, private=question.private)
    taken_back = 0
    for line in records.live(desk.files.read(path).lines):
        rule = records.by_rule(line)
        if rule and NOT_ADOPTED in (_stands(rules, rule), _leant_on(rules, line.detail)):
            _by_rule(desk, question, line.item, line.rev, UNDO, undoes=line.n)
            taken_back += 1
    mine = records.standing(desk.files.read(path).lines).answers
    settled = held_back = 0
    for item in items.items:
        preset = cast(dict[str, Json], item.held["preset"])
        fits, stands = preset.get(records.FITS), mine.get(item.id)
        if _stands(rules, fits) != ADOPTED:
            continue
        if stands is not None and stands.answer != SKIP and records.fresh(stands, item, question):
            # The founder's own answer, or what the rule gave already.
            continue
        if _leant_on(rules, preset) != ADOPTED:
            # The rule lets the item through to another, which the founder has not adopted.
            held_back += 1
            continue
        rule = rules[cast(str, fits)][0]
        answer = _gives(rule, item, question)
        if answer is not None:
            _by_rule(desk, question, item.id, item.rev, answer, detail={**preset, RULE: rule.id})
            settled += 1
    if desk.keep is not None and (settled or taken_back):
        records.keep_up(path, desk.keep / path.relative_to(desk.data))
    return [settled, taken_back, held_back]


# How many items an adopted rule fits and does not settle, because each leans on a rule
# that is not adopted. It is said only where there are any.
HELD_BACK: Final = "held_back"


def _settle(desk: Desk) -> dict[str, Json]:
    """Bring every queue to what the rules say that the founder has adopted. Returns how
    many items were settled, and how many answers of a rule were taken back. Where an
    adopted rule leans on one that is not, it says how many items that holds back.

    It is the same whether it is run once or twice. The founder's own answer to an item
    is never written over: a rule settles what the founder has not answered.
    """
    rules = _adopted(desk)
    queues = {
        str(cast(dict[str, Json], rule.held["preset"]).get("queue")) for rule, _ in rules.values()
    }
    found = [_settle_queue(desk, name, rules) for name in sorted(queues & set(desk.every))]
    held_back = sum(each[2] for each in found)
    return {
        "settled": sum(each[0] for each in found),
        "taken_back": sum(each[1] for each in found),
        **({HELD_BACK: held_back} if held_back else {}),
    }


def leans(desk: Desk, rule: Item) -> list[Json]:
    """For a rule that leans on others: each rule it leans on, how that rule stands, and
    how many of the leaning rule's items lean on it. Empty for any other rule.

    The page says it on the rule's screen, so that the founder sees before a yes what
    the rule would settle as the rules stand, and that it settles nothing alone.
    """
    about = cast(dict[str, Json], rule.held["preset"])
    others, queue = about.get(records.LEANS_ON), about.get("queue")
    if not isinstance(others, list) or not isinstance(queue, str) or queue not in desk.items:
        return []
    rules = _adopted(desk)
    counted: dict[str, int] = {}
    for item in desk.items[queue].items:
        preset = cast(dict[str, Json], item.held["preset"])
        other = preset.get(records.LEANS_ON)
        if preset.get(records.FITS) == rule.id and isinstance(other, str):
            counted[other] = counted.get(other, 0) + 1
    return [
        {"rule": other, "stands": _stands(rules, other), "items": counted.get(other, 0)}
        for other in others
        if isinstance(other, str)
    ]


def decide(desk: Desk, sent: object) -> dict[str, Json]:
    """Write one decision, and say what comes next. The line is on disk when this returns."""
    if not isinstance(sent, dict) or frozenset(cast(dict[str, Json], sent)) != DECIDE:
        raise bad()
    body = cast(dict[str, Json], sent)
    words = [body[name] for name in ("queue", "item", "rev", "part", "answer", "note")]
    detail, seconds = body["detail"], body["seconds"]
    if not (
        all(_is(each, str) for each in words)
        and _is(body["second"], bool)
        and _is(body["settles"], bool)
        and isinstance(detail, dict)
        and isinstance(seconds, int)
        and _is(seconds, int)
        and seconds >= 0
    ):
        raise bad()
    name, wanted, rev, part, answer, note = cast(list[str], words)
    believed = body["stands"]
    if believed is not None and not (_is(believed, int) and cast(int, believed) >= 1):
        raise bad()
    with desk.lock:
        now = look(desk, name) if name in desk.questions else None
        held = None if now is None else now.items.by_id.get(wanted)
        if now is None or held is None:
            raise missing()
        if rev != held.rev:
            raise Refused(HTTPStatus.CONFLICT, STALE_ITEM)
        allowed = (*now.question.answers, SKIP, *((MOVE,) if "move" in now.question.adds else ()))
        if answer not in allowed or (answer == MOVE) != bool(part):
            raise bad(NOT_AN_ANSWER)
        if len(note) > NOTE_LIMIT:
            raise bad()
        if not records.plain(note):
            raise bad(NOTE_NOT_PLAIN)
        if "pick" in now.question.adds and answer == AREA and held.id.startswith(OTHER_NAME):
            raise bad(NOT_AN_AREA)
        _detail(now.question, held, answer, cast(dict[str, Json], detail))
        mine = now.stands.get(desk.reviewer, records.NOTHING)
        stands = mine.moves.get(held.id, {}).get(part) if part else mine.answers.get(held.id)
        if _same(stands, body):
            # A decision made twice is written once.
            _keep(desk, now.question)
            return _written(desk, now, held.id, stands) | ({"next": held.id} if part else {})
        if believed != (None if stands is None else stands.n):
            # The page shows the item as it was. Another window answered it since, or
            # took an answer back. Nothing is replaced that the person has not seen.
            raise Refused(HTTPStatus.CONFLICT, ALREADY)
        moved = records.moves_of(desk.reviewer, held, now.question, now.stands)
        if answer not in (SKIP, MOVE) and not note and (answer == "wrong" or moved):
            raise bad(NEEDS_NOTE)
        if body["settles"]:
            if desk.reviewer != FOUNDER:
                raise bad(NOT_THE_FOUNDER)
            if now.state_of(desk.reviewer, held) != DISPUTED:
                raise bad(NOTHING_TO_SETTLE)
        try:
            line = records.append(
                _file(desk, now.question),
                reviewer=desk.reviewer,
                queue=name,
                question=now.question.version,
                item=held.id,
                rev=rev,
                part=part,
                answer=answer,
                note=note,
                second=cast(bool, body["second"]),
                settles=cast(bool, body["settles"]),
                detail=cast(dict[str, Json], detail),
                seconds=min(seconds, SECONDS_LIMIT),
                synthetic=desk.synthetic,
                clock=desk.clock,
                files=desk.files,
            )
        except Broken as broken:
            raise bad() from broken
        _keep(desk, now.question)
        # After a move the same item stays in view.
        return _written(desk, now, held.id, line) | ({"next": held.id} if part else {})


def undo(desk: Desk, sent: object) -> dict[str, Json]:
    """Take back the last line of a queue that stands. Asked again, the one before."""
    if not isinstance(sent, dict) or set(cast(dict[str, Json], sent)) != {"queue"}:
        raise bad()
    name = cast(dict[str, Json], sent)["queue"]
    if not isinstance(name, str):
        raise bad()
    with desk.lock:
        now = look(desk, name)
        last = now.stands.get(desk.reviewer, records.NOTHING).last
        if last is not None:
            records.append(
                _file(desk, now.question),
                reviewer=desk.reviewer,
                queue=name,
                question=last.question,
                item=last.item,
                rev=last.rev,
                part=last.part,
                answer=records.UNDO,
                undoes=last.n,
                synthetic=last.synthetic,
                clock=desk.clock,
                files=desk.files,
            )
        _keep(desk, now.question)
        ruled = _settle(desk) if name == OF_RULES else None
        return {
            "undone": None if last is None else last.as_dict(),
            "counts": counts(desk, look(desk, name)),
            **({} if ruled is None else {"ruled": ruled}),
        }


def layer(desk: Desk, group: str, name: str) -> bytes:
    """A layer's file as it is, once it has said which city it is of."""
    path = desk.layers.get((group, name))
    if path is None:
        raise missing()
    held = path.read_bytes()
    try:
        about = cast(dict[str, Any], json.loads(held))["desk"]
        fits = (about["layer"], about["group"], about["synthetic"]) == (name, group, desk.synthetic)
    except (ValueError, KeyError, TypeError):
        fits = False
    if not fits:
        # A layer of the other city, or of no city it names, is never drawn.
        raise missing()
    return held


# The routes

GET, POST = "GET", "POST"
ROUTES: Final = {
    "/": GET,
    "/favicon.ico": GET,
    "/page/{name}": GET,
    "/api/state": GET,
    "/api/queue/{queue}": GET,
    "/api/item/{queue}/{item}": GET,
    "/api/layer/{group}/{layer}": GET,
    "/api/decide": POST,
    "/api/undo": POST,
}


def route(target: str) -> tuple[str, list[str]] | None:
    """The template a path fits, and the words in its places. None when it fits none.

    The path is cut at each slash before anything is decoded, so that an encoded
    slash is one word with a slash in it, and never a step into a folder.
    """
    if not target.startswith("/") or "?" in target or "#" in target:
        return None
    try:
        words = [unquote(each, errors="strict") for each in target[1:].split("/")]
    except UnicodeDecodeError:
        return None
    match words:
        case [""]:
            return "/", []
        case ["favicon.ico"]:
            return "/favicon.ico", []
        case ["page", name]:
            return "/page/{name}", [name]
        case ["api", "state" | "decide" | "undo" as name]:
            return f"/api/{name}", []
        case ["api", "queue", name]:
            return "/api/queue/{queue}", [name]
        case ["api", "item", name, wanted]:
            return "/api/item/{queue}/{item}", [name, wanted]
        case ["api", "layer", group, name]:
            return "/api/layer/{group}/{layer}", [group, name]
        case _:
            return None


class Handler(BaseHTTPRequestHandler):
    """Answers one request. `desk` is set on a class of its own for each server."""

    desk: Desk
    # A request that stalls is dropped.
    timeout = 10
    # The answer ends when the connection closes, so no request waits on another.
    protocol_version = "HTTP/1.0"

    def version_string(self) -> str:
        return "desk"

    def log_message(self, format: str, *args: object) -> None:
        """The library would print the path, which holds an item. So it prints nothing."""

    def do_GET(self) -> None:
        self._handle(GET)

    def do_POST(self) -> None:
        self._handle(POST)

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        """What the library refuses by itself: a method it does not know, a line too long."""
        if code == HTTPStatus.NOT_IMPLEMENTED:
            refusal = Refused(HTTPStatus.METHOD_NOT_ALLOWED, BAD_REQUEST, METHOD_NOT_KNOWN)
        elif code in (HTTPStatus.REQUEST_URI_TOO_LONG, HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE):
            refusal = Refused(HTTPStatus(code), TOO_LARGE)
        else:
            refusal = bad()
        self._refuse(refusal, "-")

    # One request

    def _handle(self, method: str) -> None:
        template = "-"
        try:
            self._check_caller()
            found = route(self.path)
            if found is None:
                raise missing()
            template, words = found
            if ROUTES[template] != method:
                raise Refused(HTTPStatus.METHOD_NOT_ALLOWED, BAD_REQUEST, METHOD_NOT_KNOWN)
            kind, body = self._answer(template, words)
        except Refused as refusal:
            self._drain()
            self._refuse(refusal, template)
        except Exception as fault:
            # Only the kind of fault is said, and its number: its words may hold a path
            # or a line.
            number = fault.errno if isinstance(fault, OSError) else None
            self.desk.log(f"fault {type(fault).__name__}{'' if number is None else f' {number}'}")
            words = COPY_DIFFERS if isinstance(fault, records.Differ) else FAULTS.get(number or 0)
            self._drain()
            self._refuse(Refused(HTTPStatus.INTERNAL_SERVER_ERROR, NOT_SAVED, words), template)
        else:
            self._send(HTTPStatus.OK, kind, body, template)

    def _check_caller(self) -> None:
        """Refuse a request that does not name this server, or comes from another's page."""
        port = cast(tuple[str, int], self.server.server_address)[1]
        hosts = self.headers.get_all("Host") or []
        if len(hosts) != 1 or hosts[0] not in (f"{LOOPBACK}:{port}", f"localhost:{port}"):
            raise Refused(HTTPStatus.FORBIDDEN, FORBIDDEN)
        own = (f"http://{LOOPBACK}:{port}", f"http://localhost:{port}")
        if any(origin not in own for origin in self.headers.get_all("Origin") or []):
            raise Refused(HTTPStatus.FORBIDDEN, FORBIDDEN)
        if any(
            site not in ("same-origin", "none")
            for site in self.headers.get_all("Sec-Fetch-Site") or []
        ):
            raise Refused(HTTPStatus.FORBIDDEN, FORBIDDEN, elsewhere=self._is_opened())

    def _is_opened(self) -> bool:
        """True of a browser that opens the address of the desk as a page of its own.

        It is asked only of a request that named this server and no other origin. A page
        in a frame, a script and a fetch are none of them a page opened.
        """
        how = (self.headers.get_all("Sec-Fetch-Mode"), self.headers.get_all("Sec-Fetch-Dest"))
        return self.command == GET and self.path == "/" and how == (["navigate"], ["document"])

    def _answer(self, template: str, words: list[str]) -> tuple[str, bytes]:
        desk = self.desk
        if template == "/favicon.ico":
            return KINDS[".svg"], ICON
        if template in ("/", "/page/{name}"):
            path = desk.pages.get(words[0] if words else "index.html")
            if path is None:
                raise missing()
            return KINDS[path.suffix], path.read_bytes()
        if template == "/api/layer/{group}/{layer}":
            return JSON_KIND, layer(desk, words[0], words[1])
        if template == "/api/state":
            held = state(desk)
        elif template == "/api/queue/{queue}":
            held = queue(desk, words[0])
        elif template == "/api/item/{queue}/{item}":
            held = item(desk, words[0], words[1])
        else:
            sent = self._body()
            held = decide(desk, sent) if template == "/api/decide" else undo(desk, sent)
        return JSON_KIND, _json({**held, "synthetic": desk.synthetic})

    def _body(self) -> object:
        """What a request to write holds, once it has shown its token."""
        kind = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        token = self.headers.get("X-Desk-Token") or ""
        if kind != "application/json" or not hmac.compare_digest(
            token.encode(), self.desk.token.encode()
        ):
            raise Refused(HTTPStatus.FORBIDDEN, FORBIDDEN)
        length = self._length()
        if length > BODY_LIMIT:
            raise Refused(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, TOO_LARGE)
        raw = self.rfile.read(length)
        self._read = length
        try:
            return cast(object, json.loads(raw.decode("utf-8")))
        except (UnicodeDecodeError, ValueError, RecursionError) as error:
            raise bad() from error

    def _length(self) -> int:
        given = self.headers.get_all("Content-Length") or []
        if len(given) != 1 or not given[0].isascii() or not given[0].isdigit():
            raise bad()
        if self.headers.get("Transfer-Encoding"):
            raise bad()
        return int(given[0])

    _read = 0

    def _drain(self) -> None:
        """Read what is left of a body that was refused, so the caller hears the refusal."""
        try:
            left = min(self._length(), DRAIN_LIMIT) - self._read
            # What was sent is here already. What was only promised is not waited for.
            self.connection.settimeout(DRAIN_WAIT)
            while left > 0:
                taken = self.rfile.read(min(left, 64 * 1024))
                if not taken:
                    return
                left -= len(taken)
        except (Refused, OSError):
            return

    # One answer

    def _refuse(self, refusal: Refused, template: str) -> None:
        synthetic = getattr(getattr(self, "desk", None), "synthetic", True)
        if refusal.elsewhere:
            self._send(refusal.status, HTML_KIND, ELSEWHERE[synthetic], "/")
            return
        body = _json({"error": refusal.error, "message": refusal.words, "synthetic": synthetic})
        self._send(refusal.status, JSON_KIND, body, template)

    def _send(self, status: HTTPStatus, kind: str, body: bytes, template: str) -> None:
        method = self.command if self.command in (GET, POST) else "-"
        try:
            self.send_response_only(status)
            self.send_header("Server", self.version_string())
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            if status == HTTPStatus.METHOD_NOT_ALLOWED:
                self.send_header("Allow", "GET, POST")
            for name, value in HEADERS:
                self.send_header(name, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
        except OSError:
            # The caller went away. What was written to disk stays written.
            status = HTTPStatus.REQUEST_TIMEOUT
        self.close_connection = True
        self.desk.log(f"{method} {template} {int(status)}")


def _json(held: Mapping[str, Json]) -> bytes:
    return json.dumps(held, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request: object, client_address: object) -> None:
        """A fault is never printed with its words: they may hold a line."""


def serve(desk: Desk, port: int = PORT) -> Server:
    """A server for this desk, bound to the loopback address. `serve_forever` starts it."""
    handler = type("DeskHandler", (Handler,), {"desk": desk})
    return Server((LOOPBACK, port), handler)
