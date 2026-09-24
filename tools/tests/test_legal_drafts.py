"""The legal drafts point at each other by number, and promise nothing that a saved file breaks.

A draft sends its reader to a risk of the list, to a task of the checklist, or to a count
of what is missing. Each is a number, and a number moves when a row is put in above it.
The sentence that cites it then sends the reader to the wrong risk, and reads as well as
it did. So each number is held here to the row it names.

One promise is held too. The police publish recorded crime, outcomes and stop and search
from one form, and a file saved whole holds all three. A notice may say that stop and
search is never read. It may say that it is never held only beside a mark that says what
must be done first.
"""

import re
from collections.abc import Iterator
from pathlib import Path

import pytest

DRAFTS = Path(__file__).resolve().parents[2] / "docs" / "legal"
NOTICE = "privacy-notice.md"
TERMS = "terms-of-use.md"
CHECKLIST = "data-protection-checklist.md"
READING = "residents-crime-and-equality.md"
LIST = "README.md"
# The name the list of risks gives each draft in its column "Where".
NAMED = {NOTICE: "Notice", TERMS: "Terms"}
# A sentence that is not yet true of what is held says so with one of these. The last is
# the mark of the appendix that says how each claim is held.
MARKS = ("[FOUNDER", "[NOT BUILT", "[SETTING", "Not true yet")


def lines_of(name: str) -> list[str]:
    return (DRAFTS / name).read_text(encoding="utf-8").splitlines()


def cells(row: str) -> list[str]:
    """The cells of one row of a table, without the edges."""
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def numbers(text: str) -> set[int]:
    return {int(number) for number in re.findall(r"\d+", text)}


def part(name: str, heading: str) -> list[str]:
    """The lines under one heading of a draft, up to the next heading of any depth."""
    found: list[str] = []
    inside = False
    for line in lines_of(name):
        if line.startswith("#"):
            inside = line.lstrip("#").strip() == heading
            continue
        if inside:
            found.append(line)
    assert found, f"{name} has a part headed {heading}"
    return found


def numbered_rows(rows: list[str]) -> dict[int, list[str]]:
    """The rows of a table whose first cell is a number, by that number."""
    found: dict[int, list[str]] = {}
    for row in rows:
        first = cells(row)[0] if row.startswith("|") else ""
        if first.isdigit():
            found[int(first)] = cells(row)
    return found


def risks() -> dict[int, dict[str, set[int]]]:
    """Each risk of the list, with the sections of each draft that it is a risk of."""
    found: dict[int, dict[str, set[int]]] = {}
    listed = numbered_rows(part(LIST, "Which sentences carry the most risk if wrong"))
    for number, row in listed.items():
        where: dict[str, set[int]] = {}
        for said in row[2].split(". "):
            draft, _, sections = said.partition(",")
            where[draft.strip()] = numbers(sections)
        found[number] = where
    return found


def risks_cited(name: str) -> Iterator[tuple[int, int, set[int]]]:
    """Every risk a draft cites: the line, the risk, and the sections the citing sentence is of.

    Under a numbered heading the section is the heading's. In a table that has a column
    headed "Section", as the appendices have, it is what the row says in that column.
    """
    heading: set[int] = set()
    column: int | None = None
    for at, line in enumerate(lines_of(name), 1):
        if line.startswith("#"):
            numbered = re.match(r"#+ (\d+)\. ", line)
            heading = {int(numbered[1])} if numbered else set()
            column = None
            continue
        if not line.startswith("|"):
            column = None
        elif "Section" in cells(line) and column is None:
            column = cells(line).index("Section")
        row = cells(line)
        of = numbers(row[column]) if column is not None and column < len(row) else heading
        for risk in re.findall(r"\brisk (\d+)", line):
            yield at, int(risk), of


def tasks() -> set[int]:
    """The tasks of the checklist, by the headings that open them."""
    return {
        int(found[1])
        for line in lines_of(CHECKLIST)
        if (found := re.match(r"## (\d+)\. ", line)) is not None
    }


def tasks_cited(name: str) -> Iterator[tuple[int, int]]:
    """Every task a draft cites by number, alone or in a list: "tasks 4, 5 and 15"."""
    for at, line in enumerate(lines_of(name), 1):
        for listed in re.findall(r"\btasks? ((?:\d+(?:, | and | to )?)+)", line, re.IGNORECASE):
            for task in numbers(listed):
                yield at, task


@pytest.mark.parametrize("name", [NOTICE, TERMS])
def test_a_risk_cited_by_number_is_a_risk_of_the_section_that_cites_it(name: str):
    listed = risks()
    wrong = [
        f"{name}:{at}: risk {risk} is not a risk of section {sorted(of)} of this draft"
        for at, risk, of in risks_cited(name)
        if not of & listed.get(risk, {}).get(NAMED[name], set())
    ]
    assert wrong == []


def test_the_drafts_cite_risks_so_the_check_has_something_to_hold():
    assert len(list(risks_cited(NOTICE))) >= 4
    assert len(list(risks_cited(TERMS))) >= 1
    assert sorted(risks()) == list(range(1, len(risks()) + 1))


@pytest.mark.parametrize("name", [NOTICE, TERMS, CHECKLIST, READING, LIST])
def test_a_task_cited_by_number_is_a_task_of_the_checklist(name: str):
    there = tasks()
    wrong = [f"{name}:{at}: task {task}" for at, task in tasks_cited(name) if task not in there]
    assert wrong == []


def test_the_checklist_lists_in_short_every_task_it_holds_and_the_list_counts_them():
    there = tasks()
    assert sorted(there) == list(range(1, len(there) + 1))
    in_short = [
        number
        for line in lines_of(CHECKLIST)
        if line.startswith("|") and (number := cells(line)[0]).isdigit()
    ]
    # The tables under "In short" come first, and hold each task once and in order.
    assert [int(number) for number in in_short[: len(there)]] == sorted(there)
    said = " ".join(lines_of(LIST))
    assert f"{len(there)} tasks in four stages" in said


@pytest.mark.parametrize("name", [NOTICE, TERMS])
def test_the_list_counts_what_stands_between_a_draft_and_publishing(name: str):
    missing = numbered_rows(part(name, "Before this is published"))
    assert sorted(missing) == list(range(1, len(missing) + 1))
    row = next(line for line in lines_of(LIST) if line.startswith(f"| [{name}]"))
    assert f"{len(missing)} things stand between it and publishing" in row


NOT_HELD = re.compile(r"\b(never|not) held\b|\bdoes not hold\b", re.IGNORECASE)


def said_not_to_be_held(name: str) -> Iterator[tuple[int, str]]:
    """Each row of a table that says a thing is not held: the row says so, or its table does."""
    head = ""
    for at, line in enumerate(lines_of(name), 1):
        if not line.startswith("|"):
            head = ""
            continue
        head = head or cells(line)[0]
        if NOT_HELD.search(cells(line)[0]) or NOT_HELD.search(head):
            yield at, line


@pytest.mark.parametrize("name", [NOTICE, READING])
def test_stop_and_search_is_said_to_be_never_held_only_beside_a_mark(name: str):
    rows = [(at, row) for at, row in said_not_to_be_held(name) if "stop and search" in row.lower()]
    assert rows, f"{name} says whether stop and search is held"
    unmarked = [
        f"{name}:{at}: {row[:120]}" for at, row in rows if not any(mark in row for mark in MARKS)
    ]
    assert unmarked == []
