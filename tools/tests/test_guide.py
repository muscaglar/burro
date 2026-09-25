"""The founder's guide to data builds, held to the workflows and the tools it describes.

A guide goes stale without a sound. Each test here reads docs/data-builds.md
beside what it speaks of, and fails when the two part.
"""

import re
from dataclasses import replace
from pathlib import Path

import pytest
from burro_pipeline.fetch.kinds import Kind
from burro_pipeline.fetch.run import Outcome, Status, Why
from burro_pipeline.fetch.store import Held
from check_data_workflows import INSTALL, MASK_MADE_UP, PACKAGES_BEFORE, WORKFLOWS
from public_log import (
    COUNTS,
    HASHES,
    RULES,
    SECRETS_OF,
    STATUSES,
    STORE,
    TRAVEL_RULES,
    is_public,
)

ROOT = Path(__file__).resolve().parents[2]
GUIDE = (ROOT / "docs" / "data-builds.md").read_text(encoding="utf-8")
# Every name a line of a public log may hold.
NAMES = (
    COUNTS
    | RULES
    | TRAVEL_RULES
    | HASHES
    | STATUSES
    | {
        *("step", "status", "copy", "source", "file", "release", "file_id", "feature"),
        *("seconds", "why", "http", "host", "kind", "list", "item"),
    }
)


def cells(row: str) -> list[str]:
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def table_under(heading: str) -> list[list[str]]:
    """The rows of the first table after a heading, the row of names first."""
    after = GUIDE.split(heading, 1)[1]
    rows = re.search(r"(?:^\|.*\n)+", after, re.MULTILINE)
    assert rows is not None, f"no table under {heading}"
    return [cells(row) for row in rows[0].splitlines() if not re.fullmatch(r"[|\s:-]+", row)]


# What a run shows


def test_every_name_the_guide_shows_on_a_line_is_one_a_log_may_show():
    lines = [span for span in re.findall(r"`([^`\n]+)`", GUIDE) if re.match(r"[a-z_0-9]+=", span)]
    assert lines, "the guide shows what a run prints"
    shown = {name for line in lines for name in re.findall(r"(?:^| )([a-z][a-z0-9_]*)=", line)}
    assert shown - NAMES == set()


def names_on(line: str) -> list[str]:
    return re.findall(r"(?:^| )([a-z][a-z0-9_]*)=", line)


def lines_of_a_fetch() -> list[str]:
    """What the guide shows of a line of fetch: in the table of failures, under the step Fetch."""
    rows = [row for row in table_under("## 9. When a run fails")[1:] if row[0] == "Fetch"]
    assert rows, "the guide says what to do when a fetch fails"
    return [span for row in rows for span in re.findall(r"`([a-z_]+=[^`]*)`", row[1])]


def test_a_line_of_fetch_is_shown_in_the_order_fetch_prints_it():
    """A person searches a log for what the guide shows, so the guide shows it as it is printed."""
    held = Held("made-up-homes", "0" * 64, "homes.csv", 1)
    whole = Outcome(1, "made-up-homes", Status.FAILED, Why.STORE, held, http="403", by_hand=True)
    whole = replace(whole, kind=Kind.HTML, host="0" * 12)
    order = names_on(whole.line())
    assert {"status", "why", "http", "kind", "host"} <= set(order)
    for line in lines_of_a_fetch():
        shown = [name for name in names_on(line) if name in order]
        assert shown == sorted(shown, key=order.index), line


def test_the_guide_says_what_to_do_about_every_way_a_file_of_a_fetch_can_end():
    shown = " ".join(lines_of_a_fetch())
    ends = {status.value for status in Status} - {Status.OK.value}
    assert {end for end in ends if f"status={end}" not in shown} == set()


@pytest.mark.parametrize(
    "why",
    [
        *(Why.NOT_THE_PAGE, Why.NOT_THE_HOST, Why.RESIDENT_TABLE, Why.NOT_THE_STORE),
        *(Why.KEPT_RECEIPT_DIFFERS, Why.FAULT, Why.NOT_ASCII),
        *(Why.NOT_THE_ADDRESS, Why.CANNOT_SEE_INSIDE, Why.RECEIPT_DIFFERS),
    ],
)
def test_the_guide_names_each_reason_that_fetch_gained_with_the_stricter_gate(why: Why):
    rows = [row for row in table_under("## 9. When a run fails")[1:] if row[0] == "Fetch"]
    numbers = {int(n) for row in rows for n in re.findall(r"why=(\d+)", row[1])}
    assert int(why) in numbers


def test_the_guide_says_to_name_each_parameter_an_address_holds():
    assert "`url_parameters`" in GUIDE


def test_the_guide_says_where_an_entry_names_the_addresses_of_its_files():
    assert "`file_urls`" in GUIDE
    rows = [row for row in table_under("## 9. When a run fails")[1:] if row[0] == "Fetch"]
    (held,) = [row for row in rows if "why=13" in row[1]]
    # A file on a host the entry does not name is mended in the entry's addresses, not its pages.
    assert "`file_urls`" in held[3] and "evidence of the entry" not in held[3]


# The receipt of a file, which is written once somebody has read the file

# The items of the first list whose file has been read as a fetch stored it. An item is
# named here in the commit that takes `edition` and `data_period` out of its `unsure`.
#
# All eleven were fetched on 2026-09-23, and each has its receipt in `data/receipts`. A
# program read each one, and no person has: `docs/research/data/m1-files.md` says what each
# holds. The guide asks that a person read a file before its receipt is written. Whether
# what a program read is enough is for the founder to say.
READ_IN_THE_FILE: frozenset[str] = frozenset(
    {
        *("oa-lookup", "oa-boundaries-bgc", "oa-boundaries-bfc", "oa-centres"),
        *("lsoa-boundaries-bgc", "census-ts044"),
        *("voa-ctsop-1-1", "voa-ctsop-3-1", "voa-ctsop-4-1"),
        *("iod-file-8", "defra-no2-2024"),
    }
)


def section(heading: str) -> str:
    """What the guide says under a heading, up to the next heading of its rank or above."""
    assert GUIDE.count(f"\n{heading}\n") == 1, f"the guide has one heading {heading!r}"
    marks = heading.split(" ", 1)[0]
    after = GUIDE.split(f"\n{heading}\n", 1)[1]
    return re.split(rf"\n#{{1,{len(marks)}}} ", after, maxsplit=1)[0]


def test_no_receipt_is_written_for_a_file_of_the_first_list_that_nobody_has_read():
    """The first run stores such a file with no receipt. A receipt is what a figure is cited to."""
    from burro_pipeline.fetch.sources import load_list

    files = load_list("m1").files
    assert {file.item for file in files} >= READ_IN_THE_FILE
    for file in files:
        assert file.ready_for_a_receipt == (file.item in READ_IN_THE_FILE), file.item
        if file.item not in READ_IN_THE_FILE:
            assert {"edition", "data_period"} <= set(file.unsure), file.item


def test_a_file_that_is_named_as_read_has_the_receipt_that_the_list_would_write():
    """A name in `READ_IN_THE_FILE` is no more than a word. The receipt is the record."""
    import json
    from collections import Counter

    from burro_pipeline.fetch.sources import load_list

    def stated(edition: str, period: dict[str, str | None]) -> tuple[str, ...]:
        return (edition, *(period.get(key) or "" for key in ("as_at", "start", "end")))

    kept = Counter(
        (held["source_id"], *stated(held["edition"], held["data_period"]))
        for held in (
            json.loads(path.read_text(encoding="utf-8"))
            for path in (ROOT / "data" / "receipts").glob("*/f-*.json")
        )
    )
    named = Counter(
        (file.source_id, *stated(file.edition, file.data_period.model_dump(mode="json")))
        for file in load_list("m1").files
        if file.item in READ_IN_THE_FILE and file.data_period is not None
    )
    assert sum(named.values()) == len(READ_IN_THE_FILE)
    assert {key: count for key, count in named.items() if kept[key] < count} == {}


def test_the_guide_gives_the_count_that_plan_gives_of_the_first_list():
    from burro_pipeline.fetch.sources import load_list

    files = load_list("m1").files
    ready = sum(file.ready_for_a_receipt for file in files)
    assert f"It reads `ready={ready}` today, and `ready={len(files)}` when" in GUIDE
    assert len(re.findall(r"`ready=\d+` today", GUIDE)) == 1


def test_the_guide_says_that_the_first_fetch_of_a_file_writes_no_receipt():
    said = section("### The first fetch of a file writes no receipt")
    assert "`status=missing`" in said and "`why=6`" in said
    # A person reads the file, states both in the list, and a second run writes the receipt.
    assert "burro_pipeline describe`" in said and "`unsure`" in said and "`new=0`" in said
    # The run ends red, and the guide says that it is meant.
    assert "red" in said and "meant" in said


def test_the_guide_says_who_puts_a_receipt_right_and_what_record_is_left():
    said = section("### Put a receipt right")
    # By whom, and with what.
    assert "You, and nobody else" in said and "No run puts a receipt right" in said
    # The wrong receipt is committed before it is taken out, so the history holds it.
    assert said.index("commit it as it is") < said.index("git rm")
    # At the store only the copy of the receipt is deleted, and the rule is put back.
    assert "`receipts/`" in said and "Put the rule back" in said
    assert "never" in said and "`raw/`" in said
    # What is left of the correction, and that nothing goes without a record.
    assert "What record is left" in said and "Nothing is deleted without a record" in said


def test_the_guide_sends_a_receipt_that_differs_to_where_it_is_put_right():
    rows = [row for row in table_under("## 9. When a run fails")[1:] if row[0] == "Fetch"]
    (differs,) = [row for row in rows if "why=16" in row[1]]
    (unread,) = [row for row in rows if "why=6" in row[1]]
    assert "section 7" in differs[3] and "put it right" in differs[3]
    assert "section 7" in unread[3]


# The check of what the store holds


def test_the_guide_says_how_to_start_the_check_of_what_the_store_holds_and_how_to_read_it():
    said = section("### See that the store holds every file that has a receipt")
    workflow = (ROOT / WORKFLOWS / "data-held.yml").read_text(encoding="utf-8")
    # The workflow, its job and its step are named as the workflow names them.
    assert "choose **data-held**" in said and "the environment `data-held`" in said
    for name in ("What the store holds", "The store holds every file that has a receipt"):
        assert f"name: {name}\n" in workflow and f'"{name}"' in said
    # What it does to the store, which is nothing, and what each way of ending means.
    assert "fetches nothing" in said and "writes nothing to the store" in said
    assert "A green step means" in said and "A red step ends `exit=1`" in said
    # Every line it shows is one a run may show: a list, a file that is missing, the totals.
    lines = re.findall(r"`(step=store [^`\n]+)`", said)
    assert len(lines) == 4 and all(is_public(line) for line in lines)
    assert [" list=" in line for line in lines] == [False, True, True, False]
    assert " item=" in lines[2] and " status=missing " in lines[2]
    assert " status=ok " in lines[3] and " missing=0 differs=0 " in lines[3]
    # And what a person does about a file that is named, by the step that hands a file over.
    assert "`by-hand`" in said and "`--file`" in said and "`retrieved_at`" in said


def test_the_check_of_what_the_store_holds_is_given_a_key_that_can_write_nothing():
    (check,) = [row for row in table_under("### The keys") if row[0] == "Check"]
    assert "Object Read only" in check[2] and "`data-held`" in check[-1]
    assert "Write or delete anything" in check[5]


# The secrets, and where a real one is kept


def environments_with_made_up_secrets() -> set[str]:
    folder = ROOT / WORKFLOWS
    return {path.stem for path in folder.glob("data-*.yml") if MASK_MADE_UP in path.read_text()}


def test_a_workflow_that_reads_no_secret_is_one_there_is():
    assert environments_with_made_up_secrets() == {"data-build", "data-travel"}


# The tables that say which secret each environment holds. The build of London has a
# table of its own, in the section that is the whole of it.
TABLES_OF_SECRETS = ("## 4. The secrets, by name", "### 3. The environment, and its eight secrets")


def said_of(environment: str) -> dict[str, str]:
    """What the guide says each secret is in one environment, in the table that names it."""
    for heading in TABLES_OF_SECRETS:
        names, *rows = table_under(heading)
        if f"In `{environment}`" in names:
            column = names.index(f"In `{environment}`")
            return {row[0].strip("`"): row[column] for row in rows}
    raise AssertionError(f"no table of the guide says what {environment} holds")


def test_the_guide_keeps_a_real_secret_only_where_a_step_reads_it():
    made_up = environments_with_made_up_secrets()
    for environment, holds in SECRETS_OF.items():
        said = said_of(environment)
        assert set(said) >= set(holds), environment
        for secret, cell in said.items():
            if secret not in holds:
                assert cell == "No", (secret, environment)
            elif environment in made_up:
                assert "made-up" in cell and "real" not in cell, (secret, environment)
            else:
                assert "real" in cell and "made-up" not in cell, (secret, environment)
        assert set(said) >= set(STORE)


def test_the_guide_never_tells_the_founder_to_put_a_real_value_where_none_is_read():
    for environment in environments_with_made_up_secrets():
        told = re.findall(rf"[^.\n]*`{environment}`[^.\n]*\.", GUIDE)
        assert not [sentence for sentence in told if re.search(r"\breal (one|value)s?\b", sentence)]
    assert "replace the four values with the real ones" not in GUIDE


# What a run installs


def test_the_guide_says_where_the_day_is_written_and_does_not_repeat_the_line():
    assert "`PACKAGES_BEFORE`" in GUIDE and "`tools/check_data_workflows.py`" in GUIDE
    assert "--exclude-newer" in GUIDE
    # The line is written in the workflows and in the check. A third copy would go stale.
    assert INSTALL not in GUIDE and PACKAGES_BEFORE not in GUIDE


# What the guide is not


@pytest.mark.parametrize(
    "words",
    [
        r"where this was written",
        r"when this was written",
        r"was not yet on github",
        r"could not be rebuilt",
        r"development (to move|moves|has moved)",
        r"(this|the current|the other|another) machine",
        r"on a machine that is not",
        r"package index can be reached",
    ],
)
def test_the_guide_says_what_is_so_and_not_where_it_was_found_to_be_so(words: str):
    found = [line for line in GUIDE.splitlines() if re.search(words, line, re.IGNORECASE)]
    assert found == []


@pytest.mark.parametrize(
    "words",
    [
        r"\b(a|the|any) (reply|letter)\b",
        r"\b(writes?|wrote|written) to (a|the|each) (publisher|data owner|owner)",
        r"has been asked for",
        r"until [^.|]* (has said|answers|has answered|replies|has replied|agrees)",
        r"waits? (on|for) [^.|]*(publisher|owner|permission)",
    ],
)
def test_no_step_of_the_guide_waits_on_a_reply_from_a_data_owner(words: str):
    found = [line for line in GUIDE.splitlines() if re.search(words, line, re.IGNORECASE)]
    assert found == []


def test_the_guide_says_that_no_workflow_describes_a_file():
    about = [line for line in GUIDE.splitlines() if "describe" in line]
    assert about, "the guide speaks of describe"
    assert any("no workflow runs it" in line for line in about)
    assert not any("never prints a value" in line or "no value from" in line for line in about)
