"""The founder's guide to data builds: how long a stored file is locked, and who deletes one.

Two kinds of file must be able to go. A register may hold the names of people who trade
under their own name, and a person may ask to be erased. A file may be used by its
owner's permission, and the owner may take it back. So the lock on the store has an end,
and the guide says who deletes a file, how, and what record is left. Each test reads
docs/data-builds.md beside what it speaks of.
"""

import json
import re
import tomllib
from pathlib import Path

from burro_pipeline.evidence import lock
from public_log import RULES

ROOT = Path(__file__).resolve().parents[2]
GUIDE = (ROOT / "docs" / "data-builds.md").read_text(encoding="utf-8")
LOCK = "### The lock: what is stored is kept as it is for 90 days"
DELETING = "### Who can delete a file, and how"
# The rule by which a build refuses a file that is not in the store as its receipt has it.
GONE = "file_is_in_the_vault"


def section(heading: str) -> str:
    """What the guide says under a heading, up to the next heading of its rank or above."""
    assert GUIDE.count(f"\n{heading}\n") == 1, f"the guide has one heading {heading!r}"
    marks = heading.split(" ", 1)[0]
    after = GUIDE.split(f"\n{heading}\n", 1)[1]
    return re.split(rf"\n#{{1,{len(marks)}}} ", after, maxsplit=1)[0]


def test_the_lock_is_for_ninety_days_and_not_for_good():
    said = section(LOCK)
    steps = [line for line in said.splitlines() if re.match(r"\d+\. ", line)]
    assert any("for 90 days" in step for step in steps)
    assert not [step for step in steps if "indefinitely" in step]
    # Nowhere does the guide still say that what is stored is never deleted.
    assert "never deleted or written over" not in GUIDE
    assert not re.search(r"locked indefinitely", GUIDE)


def test_the_guide_says_which_two_kinds_of_file_must_be_able_to_go():
    said = section(LOCK)
    assert "trade under their own name" in said
    assert "permission" in said and "take it back" in said


def test_the_guide_says_why_ninety_days_loses_nothing():
    """Every file's hash is in a receipt, so a file that is deleted or replaced is found by
    the next build. The lock was never what told a build that a file is the one read."""
    said = section(LOCK)
    assert "Why 90 days loses nothing" in said
    (why,) = [line for line in said.splitlines() if line.startswith("| Why 90 days loses nothing")]
    assert "hash" in why and "receipt" in why and "the next build" in why
    assert f"`{GONE}`" in why


def test_the_rule_the_guide_names_is_the_one_a_build_refuses_by():
    assert GONE in lock.MEANING, "the lock names the rule"
    assert GONE in RULES, "a public log may show it"
    assert f"`status=refused {GONE}=1`" in section(DELETING)


def test_the_guide_says_who_can_delete_a_file_and_that_no_run_does():
    said = section(DELETING)
    assert "You, and nobody else" in said
    assert "No workflow deletes a file" in said and "no step of the pipeline" in said


def test_the_record_is_written_before_anything_is_deleted_and_names_no_person():
    said = section(DELETING)
    steps = [line for line in said.splitlines() if re.match(r"\d+\. ", line)]
    assert len(steps) >= 5
    note = next(at for at, step in enumerate(steps) if "`registry/evidence/`" in step)
    gone = next(at for at, step in enumerate(steps) if "In Cloudflare" in step)
    assert note < gone, "the note is written first"
    assert "What record is left" in said
    assert "no person's name" in said and "no name of a business" in said
    assert "`<source-id>-<yyyy-mm-dd>.md`" in said
    # The receipt is taken out of the folder, and the history keeps it.
    assert "`git rm`" in said and "history" in said


def test_the_guide_says_what_a_build_does_when_a_file_its_lock_names_is_gone():
    said = section(DELETING)
    assert "What a build does when a file is gone" in said
    assert "writes nothing" in said
    # A release is built again without the file, and never mended.
    assert "built again" in said and "under a new id" in said


def test_the_guide_says_what_to_do_for_each_reason_a_file_must_go():
    said = section(DELETING)
    assert "An owner withdraws its permission" in said
    assert "A person asks to be erased" in said
    # Whoever asks is never named in the repository.
    assert "stays with you" in said


def test_a_file_younger_than_the_lock_is_deleted_with_the_rule_off_and_the_rule_is_put_back():
    said = section(DELETING)
    assert "younger than 90 days" in said
    assert "Put the rule back the same day" in said


def test_what_was_not_read_of_the_lock_is_said_to_be_not_read():
    said = section(LOCK)
    assert "From which day the 90 days of a file are counted" in said
    table = GUIDE.split("## 14. What was read", 1)[1]
    assert "for a number of days, until a date, or indefinitely" in table


# What the commit holds, so that the checks pass on the day

LISTS = ROOT / "packages" / "pipeline" / "src" / "burro_pipeline" / "fetch" / "lists"
RECEIPTS = ROOT / "data" / "receipts"
REGISTER = "fsa-food-hygiene-ratings"
# The test that holds the count of the files of each list.
COUNTED = ROOT / "packages" / "pipeline" / "tests" / "fetch" / "test_editions_a_file_gives.py"


def items() -> list[dict[str, object]]:
    """Every item of every list of files to fetch."""
    found: list[dict[str, object]] = []
    for path in sorted(LISTS.glob("*.toml")):
        found += tomllib.loads(path.read_text(encoding="utf-8")).get("file", [])
    return found


def test_the_guide_says_where_the_lists_are_and_whose_file_an_item_is():
    """A person names where they trade, and a receipt names a file by a hash. The list is
    what says which authority a file is of, so the guide says where the list is."""
    said = section(DELETING)
    assert items(), "the lists are where the guide says"
    assert f"`{LISTS.relative_to(ROOT).as_posix()}/`" in said
    assert "`what`" in said and "`url`" in said
    assert all(item.get("what") for item in items())


def test_the_receipts_of_a_file_of_a_register_are_told_by_the_address_of_its_item():
    said = section(DELETING)
    assert "whose `url` is the item's" in said
    listed = {item["url"] for item in items() if item["source_id"] == REGISTER}
    held = {
        json.loads(path.read_text(encoding="utf-8"))["url"]
        for path in sorted((RECEIPTS / REGISTER).glob("*.json"))
    }
    # A receipt that is left when its item has gone from the list is one that was forgotten.
    assert held <= listed


def test_the_guide_says_what_the_entry_of_a_source_that_is_held_may_still_hold():
    """An entry that is held with a use it may not have stops the registry from loading,
    and every step with it. The guide says so before the founder meets it."""
    said = section(DELETING)
    assert "`uses`" in said and "internal uses alone" in said
    assert "`make registry-check`" in said
    assert "`file_urls`" in said


def test_the_guide_takes_the_items_of_a_source_that_is_held_out_of_every_list():
    """A fetch asks the registry about its whole list, and fetches no file of a list that
    holds one the registry refuses."""
    said = section(DELETING)
    assert "out of every list" in said
    assert "no file of that list is fetched" in said


def test_the_guide_says_which_checks_fail_and_that_they_are_put_right_in_the_same_commit():
    said = section(DELETING)
    assert "`make ci`" in said
    assert COUNTED.is_file()
    assert f"`{COUNTED.relative_to(ROOT).as_posix()}`" in said
    assert "in the same commit" in said
    (step,) = [line for line in said.splitlines() if line.startswith("4. ")]
    assert "what the checks asked for" in step


def test_the_guide_says_of_a_build_alone_that_it_writes_nothing():
    """A build that is refused writes nothing, and a test of each holds it to that. The
    draft of the areas is no build: it may leave what its first parts wrote."""
    said = section(DELETING)
    (row,) = [line for line in said.splitlines() if f"`status=refused {GONE}=1`" in line]
    assert "A build writes nothing" in row
    assert "The draft of the areas is no build" in row
