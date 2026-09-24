"""The plan for real data, held to the decision that no launch waits on a reply.

docs/adr/0007 says that Burro relies on published licences, and that a letter to a
data owner is a courtesy and a record. So no milestone, no step of the critical path
and no task of the plan may wait on one. The one wait on somebody outside that the
plan keeps is the subscription to the rail schedule being approved.
"""

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLAN = (ROOT / "docs" / "design" / "london-data.md").read_text(encoding="utf-8")
RECORD = (ROOT / "docs" / "adr" / "0015-where-builds-run-and-what-gates-a-launch.md").read_text(
    encoding="utf-8"
)
# The sources the plan once held back for want of an answer, by their registry ids.
BROUGHT_FORWARD = (
    "gla-tree-canopy-cover-2024",
    "gla-green-cover-2024",
    "parkrun-events",
    "arts-council-england-libraries-basic-dataset",
    "arts-council-england-accredited-museums",
    "arts-council-england-national-portfolio",
)


def section(number: int) -> str:
    """One numbered section of the plan, from its heading to the next."""
    found = re.search(rf"^## {number}\. .*?(?=^## \d+\. |\Z)", PLAN, re.MULTILINE | re.DOTALL)
    assert found is not None, f"the plan has a section {number}"
    return found[0]


def registered() -> dict[str, dict[str, object]]:
    sources: dict[str, dict[str, object]] = {}
    for path in sorted((ROOT / "registry" / "sources").glob("*.toml")):
        for source in tomllib.loads(path.read_text(encoding="utf-8"))["source"]:
            sources[source["id"]] = source
    return sources


def sentences(text: str) -> list[str]:
    """Each sentence of a document, and each sentence of each cell of its tables."""
    cells = [cell for line in text.splitlines() for cell in line.split("|")]
    return [part.strip() for cell in cells for part in re.split(r"(?<=[.:;])\s+", cell) if part]


# A sentence may say that nothing waits on a letter. That is what the plan is held to say.
DENIES = re.compile(r"\b(no|none|neither|never|nothing|nobody)\b", re.IGNORECASE)


@pytest.mark.parametrize(
    "words",
    [
        r"\bletters? \d",
        r"\b(send|sends|sent) (a |the )?letters?\b",
        r"waits? (on|for) [^.|]*\b(letter|reply|answer)",
        r"until [^.|]*\b(has said|answers|has answered|replies|has replied|agrees)\b",
        r"\banswers? (by|early|on territory)\b",
        r"does not answer",
        r"\bunanswered\b",
        r"\bis silent\b",
        r"\bchase\b",
        r"acknowledgement",
    ],
)
@pytest.mark.parametrize("text", [PLAN, RECORD], ids=["the plan", "the record on builds"])
def test_nothing_in_the_plan_waits_on_a_reply_from_a_data_owner(text: str, words: str):
    found = [
        said[:120]
        for said in sentences(text)
        if re.search(words, said, re.IGNORECASE) and not DENIES.search(said)
    ]
    assert found == []


def test_the_plan_says_that_a_letter_is_a_courtesy_and_gates_nothing():
    said = " ".join(PLAN.split())
    assert "a courtesy and a record" in said
    assert "0007-no-solicitor.md" in said


def test_the_critical_path_keeps_the_wait_on_the_rail_subscription_being_approved():
    waits = [row for row in section(5).splitlines() if "**Wait.**" in row]
    assert any("subscription" in row and "approved" in row for row in waits)
    # The other wait is on the calendar, and on nobody's answer.
    assert len(waits) == 2 and any("timetable change" in row for row in waits)


def test_every_date_in_the_plan_is_still_said_to_be_an_estimate():
    assert 'Every date, hour and pound below is an estimate unless it says "read"' in PLAN


@pytest.mark.parametrize("source_id", BROUGHT_FORWARD)
def test_a_source_brought_forward_is_said_to_stand_as_the_registry_has_it(source_id: str):
    rows = [row for row in section(4).splitlines() if row.startswith("|") and source_id in row]
    assert rows, f"section 4 names {source_id}"
    status = registered()[source_id]["status"]
    assert isinstance(status, str)
    assert f"`{status}`" in section(4)
    # A source the gate refuses is never said to be in hand.
    assert status == "approved" or "the gate refuses" in " ".join(section(4).split())


def test_the_plan_holds_back_no_source_for_want_of_an_answer_that_has_come():
    said = " ".join(PLAN.split())
    for words in ("Tree canopy later", "parkrun without a written yes", "page is saved"):
        assert words not in said
