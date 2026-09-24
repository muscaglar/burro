"""The decision records: each has a number of its own, and the list names every one.

Two branches can each add a record under the next free number. Brought together, they
would share it, and every mention of that number would then mean two things.
"""

import re
from collections import Counter
from pathlib import Path

RECORDS = Path(__file__).resolve().parents[2] / "docs" / "adr"
LISTED = re.compile(r"^\| \[(\d{4})\]\((\d{4}-[a-z0-9-]+\.md)\) \| (.+?) \| .+? \|$", re.MULTILINE)


def records() -> dict[str, Path]:
    found = sorted(RECORDS.glob("[0-9][0-9][0-9][0-9]-*.md"))
    assert found, "there are decision records"
    return {path.name: path for path in found}


def test_no_two_decision_records_share_a_number():
    numbers = Counter(name[:4] for name in records())
    assert {number for number, count in numbers.items() if count > 1} == set()


def test_the_list_names_every_decision_record_once_in_order_and_by_its_title():
    rows = LISTED.findall((RECORDS / "README.md").read_text(encoding="utf-8"))
    assert [name for _, name, _ in rows] == list(records())
    for number, name, title in rows:
        assert name.startswith(number)
        first = records()[name].read_text(encoding="utf-8").splitlines()[0]
        assert first == f"# {number}. {title}"
