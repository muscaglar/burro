"""What is published says what is known, and no more than that.

The repository is public, so every document in it is read by people who were not there
when it was written. Each test here reads every document, and fails on a sentence that
does not belong in one.

Some names and some kinds of sentence may never appear in the repository. They are listed
in a file that is not published, so that no check holds what it looks for. Where the
file is absent, as it is in a copy of the public repository, the tests that need it are
skipped. The others run everywhere.
"""

import re
import subprocess
import tomllib
from functools import cache
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
# A document is prose that a person reads: every markdown file, and the registry's entries.
PROSE = (".md",)
ENTRIES = ROOT / "registry" / "sources"
# The lines of a decision hold what a person typed at the review desk: the note of an
# answer, and the reason of a change or of a flag. So a published decision is a document.
DECISIONS, LINES = "decisions", ".jsonl"
# The list that is not published, and what a test says when it is not there.
LIST = ROOT / "private" / "words.toml"
ABSENT = "the list is not in this copy"


# Two letters are read as an `i` where case is ignored, and are no `i` in small letters.
DOTTED = ("\N{LATIN CAPITAL LETTER I WITH DOT ABOVE}", "\N{LATIN SMALL LETTER DOTLESS I}")


def in_small_letters(text: str) -> str | None:
    """A text in small letters, where that changes nothing but the case of a letter."""
    folded = text.casefold()
    same = len(folded) == len(text) and not any(letter in text for letter in DOTTED)
    return folded if same else None


@cache
def the_list() -> dict[str, Any] | None:
    """What the list holds, or nothing where it is absent."""
    if not LIST.is_file():
        return None
    with LIST.open("rb") as file:
        return tomllib.load(file)


@cache
def tracked() -> tuple[Path, ...]:
    """Every file git tracks or would track. Outside a repository: every file there is."""
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if listed.returncode == 0:
        paths = [ROOT / name for name in listed.stdout.decode().split("\0") if name]
    else:
        paths = [path for path in ROOT.rglob("*") if "node_modules" not in path.parts]
    return tuple(path for path in sorted(paths) if path.is_file())


@cache
def documents() -> tuple[tuple[str, str | None, tuple[str, ...]], ...]:
    """Every document git tracks or would track: its path, its text in small letters, its lines."""
    found: list[tuple[str, str | None, tuple[str, ...]]] = []
    for path in tracked():
        if not is_a_document(path):
            continue
        text = path.read_text(encoding="utf-8")
        lines = tuple(text.splitlines())
        found.append((str(path.relative_to(ROOT)), in_small_letters(text), lines))
    return tuple(found)


def is_a_document(path: Path) -> bool:
    """Whether a file is prose that a person reads, or holds what a person typed."""
    typed = path.suffix == LINES and DECISIONS in path.relative_to(ROOT).parts
    return path.suffix in PROSE or ENTRIES in path.parents or typed


def decisions() -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Every published decision: its path and its lines."""
    return tuple(
        (path, lines)
        for path, _, lines in documents()
        if path.endswith(LINES) and DECISIONS in Path(path).parts
    )


def roughly(words: str) -> re.Pattern[str]:
    """The same words, as they are looked for in a text that is all in small letters.

    A search that begins with letters is many times quicker than one that begins at the
    edge of a word and folds each letter as it goes. This one asks less than the words
    do: it leaves out the edge in front. So a document it finds nothing in holds no
    line the words would find, and only the others are read line by line. A document
    that small letters would change by more than case is always read line by line.
    """
    # In small letters `\B` and `\D` would say the opposite of what they say.
    assert not re.search(r"\\[A-Z]", words)
    return re.compile(words.casefold().removeprefix(r"\b"))


def said(words: str) -> list[str]:
    """Every line of every document that holds the words, with where it stands."""
    looked_for, first = re.compile(words, re.IGNORECASE), roughly(words)
    return [
        f"{path}:{number}: {line.strip()[:160]}"
        for path, folded, lines in documents()
        if folded is None or first.search(folded)
        for number, line in enumerate(lines, 1)
        if looked_for.search(line)
    ]


def test_there_are_documents_to_read():
    paths = [path for path, _, _ in documents()]
    assert "README.md" in paths
    assert "docs/PLAN.md" in paths
    assert any(path.startswith("docs/research/") for path in paths)
    assert any(path.startswith("registry/sources/") for path in paths)


def test_words_are_found_where_they_stand():
    found = said(r"\bBurro helps people\b")
    assert any(line.startswith("README.md:") for line in found)
    assert said(r"\bno document says this of itself, by design\b") == []


def test_the_list_is_not_published():
    assert LIST not in tracked(), "keep the list out of what git tracks"


def test_no_document_holds_words_on_the_list():
    held = the_list()
    if held is None:
        pytest.skip(ABSENT)
    found = {
        f"{kind['of']}: {words}": lines
        for kind in held["words"]
        for words in kind["any"]
        if (lines := said(words))
    }
    assert found == {}


def test_no_file_is_at_a_path_on_the_list():
    held = the_list()
    if held is None:
        pytest.skip(ABSENT)
    for name in held["names"]["paths"]:
        path = ROOT / name
        assert not path.exists()
        assert [file for file in tracked() if path in (file, *file.parents)] == []


def test_no_file_holds_a_name_on_the_list():
    held = the_list()
    if held is None:
        pytest.skip(ABSENT)
    names: list[str] = held["names"]["held"]
    found: list[str] = []
    for path in tracked():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        found += [f"{path.relative_to(ROOT)}: {name}" for name in names if name in text]
    assert found == []


def test_no_document_says_whether_a_name_or_a_domain_is_free():
    seems = r"(looks?|looked|appears?|appeared|seems?|seemed)"
    free = r"(free|available|unregistered|unclaimed|taken)"
    assert said(rf"\b(name|domain|mark)s?\b[^.|]{{0,60}}\b{seems} (to be )?{free}\b") == []


# The names of two columns of the statistics office's files have the shape of a postcode.
NOT_A_POSTCODE = {"OA21CD", "OA11CD"}
# The two halves of a postcode stand together, or with a space between them. In an address
# a sign stands in for the space.
BETWEEN = r"(?: |-|_|\+|%20)?"
POSTCODE = re.compile(
    rf"(?<![A-Za-z0-9])[A-Z]{{1,2}}[0-9][A-Z0-9]?{BETWEEN}[0-9][A-Z]{{2}}(?![A-Za-z0-9])"
)
# An address that takes a postcode is given by its pattern, never with a postcode in it.
IN_AN_ADDRESS = re.compile(
    rf"postcode[/=][a-z]{{1,2}}[0-9][a-z0-9]?{BETWEEN}[0-9][a-z]{{2}}\b", re.IGNORECASE
)


def test_no_document_holds_a_postcode():
    found = [
        f"{path}:{number}: {match[0]}"
        for path, _, lines in documents()
        for number, line in enumerate(lines, 1)
        for match in (*POSTCODE.finditer(line), *IN_AN_ADDRESS.finditer(line))
        if match[0] not in NOT_A_POSTCODE
    ]
    assert found == []


# What a person typed at the review desk


def test_a_published_decision_is_read_as_a_document():
    for name in (
        "gazetteer/london/decisions/names/r1.jsonl",
        "gazetteer/london/decisions/changes/r1.jsonl",
    ):
        assert is_a_document(ROOT / name), name
    for name in ("evals/reader/cases/whole_searches.jsonl", "tools/desk/questions.json"):
        assert not is_a_document(ROOT / name), name


# Where a file is on somebody's machine, and a machine that is reached by its name. A
# reason is typed by a person, who may paste either without a thought.
ON_A_MACHINE = re.compile(
    r"(?<![A-Za-z0-9_.~-])(?:/(?:Users|home|private|var|tmp|Volumes|mnt|opt)/|~/|[A-Za-z]:\\\\)"
)
A_HOST = re.compile(
    r"(?i)\b(?:[a-z][a-z0-9+.-]*://|[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:internal|local|lan|corp|test)\b"
    r"|(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b|localhost\b)"
)
# An address of a person. The desk names a reviewer by a label, r1 or r2, and never so.
A_PERSON = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def typed_wrongly(line: str) -> list[str]:
    """What a line of a decision holds that a person should not have typed into it."""
    found = (*ON_A_MACHINE.finditer(line), *A_HOST.finditer(line), *A_PERSON.finditer(line))
    return [match[0] for match in found]


@pytest.mark.parametrize(
    "line",
    [
        # Put together here, so that no file of the repository holds a path of a machine
        # as it would be written, and a check of what is published finds none.
        '{"why":"See /' + 'Users/somebody/notes.txt"}',
        '{"why":"It is in ~/desk"}',
        '{"note":"As https://example.org/page says"}',
        '{"why":"Ask build-7.corp"}',
        '{"why":"It ran on 10.0.0.12:8765"}',
        '{"why":"Ask somebody@example.org"}',
    ],
)
def test_a_path_of_a_machine_a_host_and_an_address_of_a_person_are_each_found(line: str):
    assert typed_wrongly(line) != []


@pytest.mark.parametrize(
    "line",
    [
        '{"n":2,"on":"2026-09-25","by":"r1","what":"recipe","of":"family_amenities"}',
        '{"why":"A park says more of a week than a count of schools.","takes_back":null}',
        '{"was":{"school_primary_nearby":40},"now":{"school_primary_nearby":20}}',
        '{"of":"figure/syn-n0004/air_no2","why":"It is 3.5 times what stands beside it."}',
    ],
)
def test_a_line_of_a_decision_as_the_desk_writes_it_holds_none_of_them(line: str):
    assert typed_wrongly(line) == []


def test_no_published_decision_holds_a_path_of_a_machine_a_host_or_an_address_of_a_person():
    found = [
        f"{path}:{number}: {held}"
        for path, lines in decisions()
        for number, line in enumerate(lines, 1)
        for held in typed_wrongly(line)
    ]
    assert found == []
