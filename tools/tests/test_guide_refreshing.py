"""The guide to refreshing London, held to the steps it speaks of.

A guide goes stale without a sound. Each test here reads docs/refreshing-london.md beside
the command line and the receipts, and fails when the two part: a command the pipeline no
longer takes, a line no step prints, a count that is no longer what the step counts.
"""

import re
import shlex
from pathlib import Path

import pytest
from burro_pipeline import cli
from burro_pipeline.command import PROG
from public_log import is_public

ROOT = Path(__file__).resolve().parents[2]
REFRESHING = (ROOT / "docs" / "refreshing-london.md").read_text(encoding="utf-8")


def section(guide: str, heading: str) -> str:
    """What stands under a heading of a guide, up to the next heading of its kind."""
    marks = "#" * (len(heading) - len(heading.lstrip("#")))
    after = guide.split(f"\n{heading}", 1)[1]
    return re.split(rf"\n{marks} ", after, maxsplit=1)[0]


def commands_of(guide: str) -> list[list[str]]:
    """Every command of the pipeline a guide shows, as the words a shell would hand it."""
    joined = guide.replace("\\\n", " ")
    found = re.findall(rf"uv run {re.escape(PROG)} ([^\n`]+)", joined)
    return [shlex.split(command) for command in found]


def test_every_command_the_guide_shows_is_one_the_pipeline_takes():
    commands = commands_of(REFRESHING)
    assert {words[0] for words in commands} >= {"fresh", "plan", "receipts", "take", "moved"}
    for words in commands:
        if words[1:] == ["--help"]:
            assert words[0] in cli.STEPS
            continue
        if words[1:2] == ["--list"] and words[2] == "NAME":
            words[2] = "m1"
        assert cli.parse(words).command == words[0], words


def test_every_line_the_guide_shows_is_one_a_step_prints():
    lines = [
        line.strip("` ")
        for line in REFRESHING.splitlines()
        if line.strip("` ").startswith(("step=fresh", "step=moved"))
    ]
    assert len(lines) >= 6
    for line in lines:
        assert is_public(line), line


def test_the_guide_gives_the_order_a_refresh_is_done_in():
    """A step of the table at the head is the section of its number."""
    steps = dict(re.findall(r"^\| (\d) \| ([^|]+) \|", section(REFRESHING, "## 0. In short"), re.M))
    assert [said.strip() for said in steps.values()] == [
        "See what is due",
        "Bring forward each list that pins an edition",
        "Fetch",
        "Bring the receipts back, and commit them",
        "Build",
        "See what moved",
        "Approve",
        "Deploy",
    ]
    headings = re.findall(r"^## (.+)$", REFRESHING, re.MULTILINE)
    assert [heading.split(".")[0] for heading in headings] == [
        *("0", "1", "2", "3", "4", "5", "6", "7"),
        *("9", "10", "11"),
    ]
    assert headings[7] == "7. Approve, and 8. Deploy"
    for said in ("What is done by hand each time", "What rhythm is sensible", "can break"):
        assert any(said in heading for heading in headings), said


def test_the_guide_counts_the_files_as_the_step_counts_them(capsys: pytest.CaptureFixture[str]):
    """The line the guide shows of 2026-09-25 is the line the step prints of that day, for
    as long as the receipts are those of that day."""
    from burro_pipeline.evidence import read_receipts
    from burro_pipeline.upkeep.cli import main

    receipts = read_receipts(ROOT / "data" / "receipts")
    if max(receipt.retrieved_on for receipt in receipts) > "2026-09-25":
        pytest.skip("a file was fetched since the guide was written")
    assert main(["fresh", "--on", "2026-09-25", "--receipts", str(ROOT / "data/receipts")]) == 0
    whole = capsys.readouterr().out.splitlines()[-1]
    assert f"\n{whole}\n" in REFRESHING
