"""What is held, and how old it is: the step `fresh`, on made-up receipts.

Every source, list, file and receipt here is made up. The step reads a folder of
receipts, a folder of lists and a registry, and nothing else: no store, no publisher and
no clock. The last tests run it on the receipts this repository holds.
"""

import hashlib
import re
from datetime import date, timedelta
from pathlib import Path

import public_log
import pytest
from burro_pipeline import cli
from burro_pipeline.evidence import How, Period, Receipt, file_id_of, read_receipts
from burro_pipeline.fetch.sources import LISTS, Listed, load_list
from burro_pipeline.registry.cadence import Cadence
from burro_pipeline.upkeep import fresh
from burro_pipeline.upkeep.cli import main

REPOSITORY = Path(__file__).resolve().parents[4]
TODAY = date(2026, 9, 25)

SOURCE = """
[[source]]
id = "{id}"
name = "Made-up {id}"
publisher = "Made-up Office"
url = "https://made-up.example/{id}"
dimension = "housing"
licence = "OGL-3.0"
commercial_use = "yes"
share_alike = false
attribution = "Contains made-up data."
status = "approved"
uses = ["scoring"]
cadence = "{cadence}"
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://made-up.example/licence"]
file_urls = ["https://files.made-up.example/{id}/"]
"""
# Each made-up source, and how often its made-up publisher says it changes.
CADENCES = {
    "made-up-register": "Daily",
    "made-up-prices": "Monthly, on the 20th working day. A yearly file is replaced each month.",
    "made-up-roads": "Every six months, April and October.",
    "made-up-homes": "Annual. Latest year is 2025.",
    "made-up-census": "One-off. The next is not before 2031.",
    "made-up-outlines": "Irregular. The page showed an update nine months ago.",
    "made-up-stations": "The publisher states no update frequency for the files.",
}
REGISTRY = "schema_version = 1\n" + "".join(
    SOURCE.format(id=source, cadence=cadence) for source, cadence in CADENCES.items()
)

ITEM = """
[[file]]
item = "{item}"
source_id = "made-up-{item}"
use = "scoring"
what = "Made-up {item}"
format = "{format}"
page = "https://made-up.example/made-up-{item}"
url = "https://files.made-up.example/made-up-{item}/{item}.{format}"
max_bytes = 1000000
{more}
"""
STATED = 'edition = "2025"\ndata_period = {{ as_at = "{as_at}" }}'
# What each made-up item says of its edition: the list states it, or the file does.
ITEMS = {
    "register": (
        "xml",
        'edition_from = { where = "xml_header", at = "Header/ExtractDate", '
        'period_too = true, words = "extract of" }',
    ),
    "prices": ("csv", STATED.format(as_at="2025-08")),
    "roads": ("zip", STATED.format(as_at="2025-04")),
    "homes": ("csv", STATED.format(as_at="2025-03-31")),
    "census": ("csv", STATED.format(as_at="2021-03-21")),
    "outlines": (
        "gpkg",
        'edition_from = { where = "geopackage", at = "gpkg_contents.last_change", '
        'period_too = false, words = "last changed" }\ndata_period = { as_at = "2025-12-01" }',
    ),
    "stations": (
        "json",
        'edition_from = { where = "retrieved", at = "", period_too = true, words = "retrieved" }',
    ),
}
LIST = 'schema_version = 1\nbuild = "made-up"\n' + "".join(
    ITEM.format(item=item, format=kind, more=more) for item, (kind, more) in ITEMS.items()
)
# What a line says of the made-up list, as a line says it of a list of this repository.
AS_IN_A_RUN = {
    r"source=made-up-[a-z]+": "source=defra-pcm-background-air",
    r"list=made-up": "list=m1",
    r"item=[a-z]+": "item=oa-lookup",
}


class Folders:
    """A registry, a folder of lists and a folder of receipts, all made up."""

    def __init__(self, root: Path) -> None:
        self.receipts = root / "receipts"
        self.lists = root / "lists"
        self.registry = root / "registry.toml"
        self.lists.mkdir()
        self.receipts.mkdir()
        self.registry.write_text(REGISTRY, encoding="utf-8")
        (self.lists / "made-up.toml").write_text(LIST, encoding="utf-8")
        self.files = {file.item: file for file in load_list(self.lists / "made-up.toml").files}

    def receipt(self, item: str, days_ago: int, stated: str = "", **more: object) -> Receipt:
        """The receipt a fetch of an item would have written, so many days before today."""
        file: Listed = self.files[item]
        retrieved = (TODAY - timedelta(days=days_ago)).isoformat()
        sha256 = hashlib.sha256(f"{item} {retrieved} {stated}".encode()).hexdigest()
        there = file.edition_from
        found = stated or retrieved
        given: dict[str, object] = {
            "file_id": file_id_of(sha256),
            "source_id": file.source_id,
            "use": file.use,
            "publisher_file": f"{item}.{file.format.value}",
            "url": file.url,
            "listed_url": file.url,
            "sha256": sha256,
            "bytes": 40,
            "retrieved_at": f"{retrieved}T09:00:00Z",
            "how": How.FETCHED,
            "edition": file.edition if there is None else there.written(found),
            "edition_from": None if there is None else there.in_a_receipt(),
            "data_period": Period(as_at=found)
            if there is not None and there.period_too
            else file.data_period,
        }
        receipt = Receipt.model_validate(given | more)
        path = self.receipts / receipt.source_id / f"{receipt.file_id}.json"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(receipt.canonical())
        return receipt

    def run(self, *more: str, on: date = TODAY) -> int:
        return main(
            [
                "fresh",
                "--on",
                on.isoformat(),
                "--receipts",
                str(self.receipts),
                "--lists",
                str(self.lists),
                "--registry",
                str(self.registry),
                *more,
            ]
        )


@pytest.fixture
def folders(tmp_path: Path) -> Folders:
    return Folders(tmp_path)


Printed = pytest.CaptureFixture[str]


def said(capsys: Printed) -> tuple[dict[str, dict[str, str]], dict[str, str], str]:
    """What the step printed: the line of each file by its item, the line of the whole as
    pairs, and what it said in words."""
    out = capsys.readouterr()
    lines = [dict(pair.split("=", 1) for pair in line.split()) for line in out.out.splitlines()]
    return {line["item"]: line for line in lines if "item" in line}, lines[-1], out.err


def as_in_a_run(line: str) -> str:
    for made_up, real in AS_IN_A_RUN.items():
        line = re.sub(made_up, real, line)
    return line


# Whether a file is due


@pytest.mark.parametrize(
    ("item", "longest"), [("register", 7), ("prices", 31), ("roads", 92), ("homes", 366)]
)
def test_a_file_is_due_once_it_was_retrieved_longer_ago_than_its_cadence(
    folders: Folders, capsys: Printed, item: str, longest: int
):
    folders.receipt(item, longest)
    assert folders.run() == 0
    files, whole, _ = said(capsys)
    assert (files[item]["days"], files[item]["state"]) == (str(longest), "fresh")
    assert (whole["due"], whole["fresh"]) == ("0", "1")

    assert folders.run(on=TODAY + timedelta(days=1)) == 0
    files, whole, _ = said(capsys)
    assert (files[item]["days"], files[item]["state"]) == (str(longest + 1), "due")
    assert (whole["due"], whole["fresh"]) == ("1", "0")


def test_it_says_how_often_each_publisher_says_its_file_changes(folders: Folders, capsys: Printed):
    for item in ITEMS:
        folders.receipt(item, 1)
    folders.run()
    files, _, _ = said(capsys)
    assert {item: line["cadence"] for item, line in files.items()} == {
        "register": "weekly",
        "prices": "monthly",
        "roads": "quarterly",
        "homes": "yearly",
        "census": "rarely",
        "outlines": "rarely",
        "stations": "not_said",
    }


def test_a_file_that_changes_rarely_is_never_due_by_its_age(folders: Folders, capsys: Printed):
    folders.receipt("census", 4000)
    folders.run()
    files, whole, errors = said(capsys)
    assert (files["census"]["days"], files["census"]["state"]) == ("4000", "fresh")
    assert (whole["due"], whole["not_known"], errors) == ("0", "0", "")


@pytest.mark.parametrize("days_ago", [0, 1, 4000])
def test_a_file_whose_cadence_is_not_said_is_never_called_fresh(
    folders: Folders, capsys: Printed, days_ago: int
):
    folders.receipt("stations", days_ago)
    assert folders.run() == 0
    files, whole, errors = said(capsys)
    assert files["stations"]["state"] == "not_known"
    assert (whole["fresh"], whole["not_known"], whole["not_said"]) == ("0", "1", "1")
    # The source is named, so that a person can put its entry right.
    assert "made-up-stations" in errors and "`cadence`" in errors
    assert errors.count("\n") == 1


def test_a_source_the_registry_does_not_hold_says_no_cadence(folders: Folders, capsys: Printed):
    folders.registry.write_text(
        "schema_version = 1\n" + SOURCE.format(id="made-up-homes", cadence="Annual"),
        encoding="utf-8",
    )
    folders.receipt("prices", 1)
    folders.run()
    files, _, _ = said(capsys)
    assert (files["prices"]["cadence"], files["prices"]["state"]) == ("not_said", "not_known")


# The day


def test_the_days_are_counted_from_the_day_it_is_given_and_from_no_clock(
    folders: Folders, capsys: Printed
):
    folders.receipt("prices", 3)
    folders.run()
    first = capsys.readouterr().out
    folders.run()
    assert capsys.readouterr().out == first
    assert " days=3 " in first and " on=2026-09-25 " in first
    folders.run(on=date(2031, 1, 1))
    assert f" days={(date(2031, 1, 1) - TODAY).days + 3} " in capsys.readouterr().out
    # No module of the step asks what the day or the time is.
    for module in ("fresh.py", "cli.py"):
        text = (Path(fresh.__file__).parent / module).read_text(encoding="utf-8")
        assert not re.search(r"\b(today|now|utcnow|time|monotonic)\(", text), module
        assert "import time" not in text and "import datetime\n" not in text


def test_a_day_before_a_file_was_retrieved_stops_the_step(folders: Folders, capsys: Printed):
    folders.receipt("prices", 3)
    assert folders.run(on=TODAY - timedelta(days=4)) == 2
    out = capsys.readouterr()
    assert out.out == ""
    assert "--on is before the day a file was retrieved" in out.err


@pytest.mark.parametrize("given", ["yesterday", "2026-9-25", "20260925", "2026-02-30", ""])
def test_a_day_that_is_no_day_is_refused_and_not_repeated(capsys: Printed, given: str):
    with pytest.raises(SystemExit) as stopped:
        main(["fresh", "--on", given])
    assert stopped.value.code == 2
    errors = capsys.readouterr().err
    assert "it is a day, as 2026-09-25" in errors
    assert not given or given not in errors.replace("2026-09-25", "")


# What a list pins


def test_it_says_which_field_of_its_list_a_person_brings_forward(folders: Folders, capsys: Printed):
    for item in ITEMS:
        folders.receipt(item, 1)
    folders.run()
    files, _, _ = said(capsys)
    pins = {item: line["pins"] for item, line in files.items()}
    # The list states the edition and the period: a fetch writes both on whatever arrives.
    assert {pins[item] for item in ("prices", "roads", "homes", "census")} == {"edition_and_period"}
    # The file states its own edition, and the list states the period.
    assert pins["outlines"] == "period"
    # The file states both, or is dated by the day it is retrieved.
    assert (pins["register"], pins["stations"]) == ("none", "none")
    assert fresh.FIELDS[fresh.Pins.EDITION_AND_PERIOD] == ("edition", "data_period")
    assert fresh.FIELDS[fresh.Pins.PERIOD] == ("data_period",)
    # Each is the name of a field of an item of a list.
    assert {field for fields in fresh.FIELDS.values() for field in fields} <= set(
        Listed.model_fields
    )


# More than one receipt of a file, and a receipt of none


def test_of_two_files_of_one_item_the_one_retrieved_last_is_the_one_that_is_held(
    folders: Folders, capsys: Printed
):
    old = folders.receipt("register", 40, stated="2026-08-10")
    new = folders.receipt("register", 2, stated="2026-09-20")
    folders.run()
    out = capsys.readouterr().out.splitlines()
    by_file = {line.split("file_id=")[1].split()[0]: line for line in out[:-1]}
    assert " state=older " in by_file[old.file_id] and " days=40 " in by_file[old.file_id]
    assert " state=fresh " in by_file[new.file_id]
    assert out[-1] == (
        "step=fresh status=ok on=2026-09-25 receipts=2 due=0 fresh=1 not_known=0 older=1 "
        "unlisted=0 not_said=0"
    )


def test_a_receipt_of_a_file_that_no_list_names_is_counted_apart(folders: Folders, capsys: Printed):
    # The list has been brought forward since: it states another edition of the file.
    folders.receipt("homes", 400, edition="2024", data_period=Period(as_at="2024-03-31"))
    assert folders.run() == 0
    out = capsys.readouterr().out.splitlines()
    assert " list=" not in out[0] and " item=" not in out[0]
    assert " state=unlisted pins=not_listed" in out[0]
    assert " due=0 " in out[-1] and " unlisted=1 " in out[-1]


def test_a_file_that_a_person_saved_says_so(folders: Folders, capsys: Printed):
    folders.receipt("homes", 1, how=How.BY_HAND)
    folders.receipt("prices", 1)
    folders.run()
    files, _, _ = said(capsys)
    assert files["homes"]["by_hand"] == "1" and "by_hand" not in files["prices"]


# What it prints, and what it refuses


def test_it_ends_with_code_0_whatever_is_due(folders: Folders, capsys: Printed):
    for item in ITEMS:
        folders.receipt(item, 500)
    assert folders.run() == 0
    _, whole, _ = said(capsys)
    assert whole == {
        "step": "fresh",
        "status": "ok",
        "on": "2026-09-25",
        "receipts": "7",
        "due": "4",
        "fresh": "2",
        "not_known": "1",
        "older": "0",
        "unlisted": "0",
        "not_said": "1",
    }


def test_every_line_is_one_a_public_log_lets_through_and_holds_nothing_of_a_receipt(
    folders: Folders, capsys: Printed
):
    for item in ITEMS:
        folders.receipt(item, 10, stated="2026-09-01")
    folders.receipt("homes", 400, edition="2024", data_period=Period(as_at="2024-03-31"))
    folders.run()
    out = capsys.readouterr()
    lines = out.out.splitlines()
    assert len(lines) == 9
    assert all(public_log.is_public(as_in_a_run(line)) for line in lines), lines
    # An edition, a period and an address are what a receipt was handed from a list or a
    # file. A line holds none of them.
    for held in ("extract of", "last changed", "2025-03-31", "2026-09-01", "made-up.example"):
        assert held not in out.out, held
    assert not any(public_log.is_public(line) for line in out.err.splitlines())


def test_the_table_gives_the_edition_and_the_period_of_each_file_and_what_is_due_first(
    folders: Folders, capsys: Printed
):
    folders.receipt("homes", 1)
    folders.receipt("prices", 40)
    folders.receipt("stations", 3)
    folders.receipt("register", 2, stated="2026-09-20")
    assert folders.run("--table") == 0
    lines = capsys.readouterr().out.splitlines()
    head, whole = lines[0].split(), lines[-1]
    rows = [re.split(r"\s{2,}", row) for row in lines[1:-1]]
    assert head[:4] == ["State", "Source", "List", "Item"]
    assert [row[0] for row in rows] == ["due", "not known", "fresh", "fresh"]
    by_item = {row[3]: row for row in rows}
    assert by_item["prices"][4:] == [
        "2025",
        "2025-08",
        "2026-08-16",
        "40",
        "monthly",
        "edition and data_period",
    ]
    assert by_item["register"][4:] == [
        "extract of 2026-09-20",
        "2026-09-20",
        "2026-09-23",
        "2",
        "weekly",
        "nothing",
    ]
    assert by_item["stations"][8:] == ["not said", "nothing"]
    assert whole.startswith("step=fresh status=ok on=2026-09-25 receipts=4 due=1 ")


@pytest.mark.parametrize(
    ("emptied", "says"),
    [("receipts", "holds no receipt"), ("lists", "holds no list")],
)
def test_it_stops_where_it_was_given_nothing_to_read(
    folders: Folders, capsys: Printed, emptied: str, says: str
):
    folders.receipt("homes", 1)
    for path in sorted((folders.receipts if emptied == "receipts" else folders.lists).rglob("*")):
        if path.is_file():
            path.unlink()
    assert folders.run() == 2
    out = capsys.readouterr()
    assert out.out == "" and says in out.err and out.err.count("\n") == 1


def test_it_reads_no_store_and_names_none(folders: Folders, monkeypatch: pytest.MonkeyPatch):
    """It is run with sockets blocked, as every test is, and with no store named."""
    for name in ("BURRO_STORE_FOLDER", "BURRO_STORE_ENDPOINT", "BURRO_RELEASES_FOLDER"):
        monkeypatch.delenv(name, raising=False)
    folders.receipt("homes", 1)
    assert folders.run() == 0
    text = (Path(fresh.__file__).parent / "cli.py").read_text(encoding="utf-8")
    assert "BURRO_" not in text and "environ" not in text


def test_the_public_log_knows_every_word_the_step_prints_and_no_other():
    assert {rhythm.value for rhythm in Cadence} == public_log.CADENCES
    assert {state.value for state in fresh.State} == public_log.STATES
    assert {pins.value for pins in fresh.Pins} == public_log.PINS
    for word in public_log.STATES - {"unlisted"}:
        assert public_log.is_public(f"step=fresh status=ok {word}=3")


# The command line, and this repository


def test_fresh_is_the_first_step_of_the_command_line():
    assert next(iter(cli.STEPS)) == "fresh"
    assert cli.parse(["fresh", "--on", "2026-09-25"]).on == TODAY


def test_the_repository_as_it_stands_is_read_whole(capsys: Printed):
    """Every receipt of this repository has its line, under a list and an item, and the
    lines come to the number of receipts."""
    receipts = read_receipts(REPOSITORY / "data" / "receipts")
    on = max(date.fromisoformat(receipt.retrieved_on) for receipt in receipts)
    held = str(REPOSITORY / "data" / "receipts")
    assert main(["fresh", "--on", on.isoformat(), "--receipts", held]) == 0
    out = capsys.readouterr()
    lines = out.out.splitlines()
    assert all(public_log.is_public(line) for line in lines)
    whole = dict(pair.split("=", 1) for pair in lines[-1].split())
    states = ("due", "fresh", "not_known", "older", "unlisted")
    assert sum(int(whole[state]) for state in states) == int(whole["receipts"]) == len(receipts)
    assert {line.split("file_id=")[1].split()[0] for line in lines[:-1]} == {
        receipt.file_id for receipt in receipts
    }
    lists = {path.stem for path in LISTS.glob("*.toml")}
    assert {line.split("list=")[1].split()[0] for line in lines[:-1] if " list=" in line} <= lists
