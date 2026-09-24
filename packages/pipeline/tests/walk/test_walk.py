"""The whole of M0, walked once on made-up files.

A made-up publisher's file is served from the loopback address, fetched
through the licence gate into a folder store, given its receipt, described,
and sealed in a lock. A figure is worked out from it by one simple method, its
evidence is written, the coverage report is run, and the figure is traced from
the sentence that shows it back to the hash of the file.

Nothing here is real, and no publisher is reached: a connection to any address
but the loopback is blocked. `test_broken_links.py` breaks each link in turn.
"""

import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass

import public_log
import pytest
from burro_core.facts import fact_id, facts_for
from burro_core.ids import FactKind
from burro_pipeline.evidence import Evidence, How, State, file_id_of, read_receipts, unevidenced
from burro_pipeline.fetch.store import FolderStore, hash_file
from burro_pipeline.registry import Use, load

from ..fetch.support import ONLY_LOOPBACK
from .support import (
    CANARY,
    CONTACT,
    FLATS,
    HOMES,
    MEASURES,
    METHOD,
    PUBLISHER,
    RELEASE_ID,
    SURVEY,
    Figure,
    Said,
    Walk,
    city,
    files_of,
    publishing,
)

pytestmark = ONLY_LOOPBACK

AREA = "lon-n0001"
FACT = fact_id(AREA, FactKind.FEATURE, FLATS)


@dataclass(frozen=True)
class Walked:
    walk: Walk
    figures: dict[str, Figure]
    evidence: Evidence
    # What each step said, in the order they were run.
    said: dict[str, Said]
    # How many requests the publisher had answered when the walk ended.
    asked: int


@pytest.fixture(scope="module")
def walked(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Walked]:
    """One walk, from the fetch to the report. Every test below reads what it left."""
    with publishing(files_of(city())) as served:
        walk = Walk(tmp_path_factory.mktemp("walk"), served)
        said = {"fetch": walk.fetch(), "held": walk.held(), "seal": walk.seal()}
        figures = walk.derive()
        evidence = walk.write_evidence(figures)
        said |= {"check": walk.check(), "coverage": walk.coverage()}
        assert [step for step, found in said.items() if found.code] == []
        yield Walked(walk, figures, evidence, said, len(served.seen))


def test_every_file_of_the_list_is_fetched_once_and_kept_under_its_hash(walked: Walked):
    walk = walked.walk
    held = FolderStore(walk.store).list()
    assert sorted(file.name for file in held) == sorted(walk.files)
    assert walked.asked == len(walk.files)
    for file in held:
        content = walk.files[file.name]
        assert (file.sha256, file.bytes) == (hashlib.sha256(content).hexdigest(), len(content))
        assert hash_file(walk.store / file.key) == (file.sha256, file.bytes)


def test_each_file_has_a_receipt_that_says_where_it_came_from_and_under_which_entry(
    walked: Walked,
):
    receipt = walked.walk.receipt(MEASURES)
    content = walked.walk.files[MEASURES]
    assert receipt.sha256 == hashlib.sha256(content).hexdigest()
    assert receipt.file_id == file_id_of(receipt.sha256)
    assert (receipt.source_id, receipt.use, receipt.how) == (SURVEY, Use.SCORING, How.FETCHED)
    assert receipt.url == f"{PUBLISHER}/files/{MEASURES}"
    # The publisher sent the request nowhere else, so the list gave the same address.
    assert receipt.listed_url == receipt.url
    assert (receipt.edition, receipt.data_period.as_at) == ("made up", "2025")
    written = walked.walk.root / receipt.path()
    assert written.read_bytes() == receipt.canonical()
    assert len(read_receipts(walked.walk.receipts)) == len(walked.walk.files)


def test_a_copy_of_each_receipt_is_kept_in_the_store_beside_its_file(walked: Walked):
    kept = FolderStore(walked.walk.store).receipts()
    assert kept == {
        receipt.kept_key(): receipt.canonical() for receipt in read_receipts(walked.walk.receipts)
    }


def test_describe_gives_the_columns_of_the_file_and_no_value_from_a_row(walked: Walked):
    walk = walked.walk
    said = walk.with_the_store("describe", walk.receipt(MEASURES).file_id)
    assert (said.code, said.words) == (0, "")
    shape = json.loads("\n".join(said.lines))
    assert shape["columns"] == ["unit_code", "unit_name", "flats"]
    assert shape["rows"] == sum(figure.units_used for figure in walked.figures.values())
    assert (shape["file_id"], shape["source"]) == (walk.receipt(MEASURES).file_id, SURVEY)
    assert CANARY not in said.everything


def test_every_step_that_is_given_a_store_says_which_kind_it_was_given(walked: Walked):
    """A file read from a folder by mistake must not look like one read from the object store."""
    walk = walked.walk
    for step in ("fetch", "held"):
        assert walked.said[step].lines[0] == "step=store kind=folder"
    brought = walk.with_the_store("receipts", "--receipts", walk.receipts)
    assert brought.lines == [
        "step=store kind=folder",
        "step=store status=ok receipts=6 new=0 same=6 differs=0 unreadable=0",
    ]
    assert all(public_log.is_public(line) for line in brought.lines)
    # What describe prints is read as JSON, so it says so in a field, and last of all.
    described = walk.with_the_store("describe", walk.receipt(MEASURES).file_id)
    shape = json.loads("\n".join(described.lines))
    assert list(shape)[:3] == ["file_id", "source", "sha256"]
    assert (list(shape)[-1], shape["store"]) == ("store", "folder")
    # A file on disk is read from no store, and nothing is said of one.
    on_disk = walk.with_the_store("describe", "--path", walk.taken(MEASURES))
    assert "store" not in json.loads("\n".join(on_disk.lines))


def test_the_lock_names_every_file_by_its_hash_and_nothing_else(walked: Walked):
    lock = walked.walk.lock()
    receipts = read_receipts(walked.walk.receipts)
    assert lock.release_id == RELEASE_ID
    assert [(found.name, found.sha256) for found in lock.inputs] == [
        (receipt.file_id, receipt.sha256) for receipt in receipts
    ]
    assert lock.development


def test_the_figure_worked_out_from_the_file_is_the_figure_the_release_serves(walked: Walked):
    served = {
        value.area_id: (value.value, value.coverage)
        for value in walked.walk.release.features
        if value.feature_id == FLATS
    }
    found = {area: (figure.value, figure.covered) for area, figure in walked.figures.items()}
    assert found == served
    assert found[AREA] == (32.4, 1.0)
    assert sum(value is None for value, _ in found.values()) == 2


def test_a_figure_that_is_missing_has_a_row_that_says_why(walked: Walked):
    gaps = [area for area, figure in walked.figures.items() if figure.value is None]
    for area in gaps:
        row = walked.evidence.row(fact_id(area, FactKind.FEATURE, FLATS))
        assert row is not None
        assert row.state is State.BELOW_THRESHOLD
        assert 0 < row.weight_covered < 0.5
        assert row.units_used < row.units_expected


def test_every_fact_has_evidence_and_every_file_behind_it_is_in_the_lock(walked: Walked):
    walk = walked.walk
    held = load(walk.registry)
    assert unevidenced(walk.release, walked.evidence, walk.lock(), held) == ()
    check = walked.said["check"]
    assert check.lines[0].startswith(f"step=check status=ok release={RELEASE_ID} facts=1669 ")
    assert f" files={len(walk.files)} findings=0 " in check.lines[0]
    assert walk.findings.read_text(encoding="utf-8") == ""


def test_the_coverage_report_counts_what_is_there_and_what_is_missing(walked: Walked):
    report = walked.walk.report.read_text(encoding="utf-8")
    coverage = walked.said["coverage"]
    assert coverage.lines[0].startswith("step=report status=ok ")
    # Of 24 areas: 21 with a figure, 1 with part of the area behind it, 2 with too little.
    assert "| feature/homes_flats | 21 | 1 | 2 | 0 | 0 | 0 | 0 | 0 |" in report
    assert "| lon-n0009 | feature/homes_flats | below_threshold | yes | Too little" in report
    assert f"| {SURVEY} | 6 |" in report
    # 70 figures of a measure, 33 costs and 22 vibes that an area lacks, and the four
    # measures that no release carries yet, in each of 24 areas.
    assert " gaps=221 no_record=0 " in coverage.lines[0]
    assert "made up" not in coverage.everything


def test_a_figure_on_the_screen_is_traced_back_to_the_hash_of_the_file_behind_it(walked: Walked):
    walk, evidence = walked.walk, walked.evidence
    # The screen: a sentence, made from a fact that core gives.
    (fact,) = [fact for fact in facts_for(walk.release, AREA, None) if fact.fact_id == FACT]
    assert fact.slots["value"] == "32%"
    assert [source.source_id for source in fact.sources] == [SURVEY]
    # The fact has a row of evidence, under its own id.
    row = evidence.row(fact.fact_id)
    assert row is not None and row.state is State.PRESENT
    assert (row.units_used, row.units_expected, row.weight_covered) == (100, 100, 1.0)
    # The row names how the figure was worked out, in a sentence.
    method = evidence.method(row.derivation_id or "")
    assert method == METHOD
    # The row names the files the figure rests on, and each has its receipt.
    receipts = [evidence.receipt(file_id) for file_id in row.inputs]
    assert sorted(receipt.publisher_file for receipt in receipts if receipt) == [HOMES, MEASURES]
    assert evidence.sources_of(row) == {SURVEY}
    assert row.retrieved_on == max(receipt.retrieved_on for receipt in receipts if receipt)
    for receipt in receipts:
        assert receipt is not None
        # The receipt gives the publisher's address, and the key of the file in the store.
        assert receipt.url == f"{PUBLISHER}/files/{receipt.publisher_file}"
        kept = walk.store / receipt.vault_key()
        # The file in the store is the file that was fetched, to the byte.
        assert hashlib.sha256(kept.read_bytes()).hexdigest() == receipt.sha256
        assert kept.read_bytes() == walk.files[receipt.publisher_file]
        # And the lock of the build names it, so the build could read it and nothing else.
        assert walk.lock().admit_file(kept).name == receipt.file_id
    # Worked out again from those bytes alone, the figure is the one on the screen.
    again = walk.derive()[AREA]
    assert f"{round(again.value or 0)}%" == fact.slots["value"]


def test_what_was_written_can_be_read_back_as_it_was(walked: Walked):
    written = Evidence.model_validate_json(walked.walk.evidence.read_bytes())
    assert written == walked.evidence
    assert written.digest() == walked.evidence.digest()


def test_nothing_a_step_printed_holds_a_row_an_address_a_folder_or_an_area(walked: Walked):
    walk = walked.walk
    names = [area.name for area in walk.release.neighbourhoods]
    hidden = [CANARY, "made-up.example", "127.0.0.1", str(walk.root), CONTACT, MEASURES, *names]
    for step, said in walked.said.items():
        for secret in hidden:
            assert secret not in said.everything, (step, secret)
        assert said.words == "", step


def test_every_line_a_step_printed_has_the_form_the_public_log_lets_through(walked: Walked):
    """But for the id of the made-up source, which is in no registry the log knows."""
    for said in walked.said.values():
        assert said.lines
        for line in said.lines:
            known = line.replace(f"source={SURVEY}", "source=synthetic")
            assert public_log.is_public(known), line


def test_the_walk_wrote_nothing_outside_its_own_folder(walked: Walked):
    walk = walked.walk
    assert sorted(path.name for path in walk.root.iterdir()) == [
        "coverage.md",
        "data",
        "evidence.json",
        "findings.txt",
        "hashes.json",
        "listing.json",
        "made-up.toml",
        "registry.toml",
        "releases",
        "store",
        "taken",
    ]
