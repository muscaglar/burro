"""The command line: what it writes, and above all what it prints.

A build's log can be read by anyone. So each test that makes the command fail
plants a string in what it is given, and looks for it in what is printed. And
every line of standard output is held to the rule of `tools/public_log.py`,
which is what stands between a step and a public log.
"""

import hashlib
import json
import re
from pathlib import Path

import pytest
from burro_core.release import MANIFEST, Hashes
from burro_pipeline.evidence.cli import main
from burro_pipeline.evidence.lock import Lock, read_lock
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.fetch.sources import load_list
from burro_pipeline.registry import Dimension, Status, Use
from burro_pipeline.release.write import write_release
from public_log import is_public

from .conftest import write
from .examples import RECEIPT
from .support import (
    CANARY,
    COMMIT,
    FIXTURE,
    GIT,
    NO_REPOSITORY,
    REAL_ID,
    RELEASE_ID,
    as_toml,
    evidence,
    git,
    list_as_toml,
    listed,
    lock_of,
    real_evidence,
    real_release,
    registered,
    registry_of,
    release,
    survey_registry,
    with_receipt,
    without,
)

PARK = "syn-n0001/feature/park_proximity"
# A measure that is a part of no vibe and that likeness is not counted on: no fact rests
# on its row but its own.
ALONE = "syn-n0001/feature/venue_independent"
# A commit as it is given where there is no repository to read it from. The tests may
# themselves be run in a working copy, so each names a folder that is in none.
COMMITTED = ("--commit", COMMIT, "--root", str(NO_REPOSITORY))
Printed = pytest.CaptureFixture[str]


def written(tmp_path: Path, found: Evidence) -> str:
    (tmp_path / "evidence.json").write_bytes(found.canonical())
    return str(tmp_path / "evidence.json")


def said(printed: Printed) -> tuple[list[str], list[str]]:
    """What was printed for anyone to read, and what was said in words beside it.

    Neither may hold what was planted, nor an area. Every line of standard
    output must be one the public log lets through, and no line of words is.
    """
    out = printed.readouterr()
    assert CANARY not in out.out + out.err
    for area in release().neighbourhoods:
        assert area.area_id not in out.out + out.err
        assert area.name not in out.out + out.err
    public, words = out.out.splitlines(), out.err.splitlines()
    assert all(is_public(line) for line in public), public
    assert not any(is_public(line) for line in words), words
    return public, words


# check


def test_check_passes_when_every_fact_has_evidence(tmp_path: Path, capsys: Printed):
    assert main(["check", str(FIXTURE), "--made-up"]) == 0
    assert main(["check", str(FIXTURE), "--evidence", written(tmp_path, evidence())]) == 0
    line = (
        f"step=check status=ok release={RELEASE_ID} facts=3241 rows=3457 files=6 findings=0 "
        f"evidence_sha256={evidence().digest()}"
    )
    assert said(capsys) == ([line, line], [])


def test_check_fails_and_prints_counts_when_a_fact_has_no_evidence(tmp_path: Path, capsys: Printed):
    planted = without(ALONE, "syn-n0002/travel/pt")
    found = tmp_path / "findings.txt"
    args = ["check", str(FIXTURE), "--evidence", written(tmp_path, planted), "--list", str(found)]
    assert main(args) == 1
    assert said(capsys) == (
        [
            f"step=check status=failed release={RELEASE_ID} facts=3241 rows=3455 files=6 "
            f"findings=2 evidence_sha256={planted.digest()} fact_has_a_row=2"
        ],
        [],
    )
    # Which facts they are is written where the caller asked, and is not printed.
    assert found.read_text(encoding="utf-8").splitlines() == [
        f"{ALONE} is served, and no row of evidence stands behind it [fact_has_a_row]",
        "syn-n0002/travel/pt is served, and no row of evidence stands behind it [fact_has_a_row]",
    ]


def test_check_holds_the_evidence_to_the_lock(tmp_path: Path, capsys: Printed):
    sealing = ["seal", "--made-up", str(FIXTURE), *COMMITTED, "--out", str(tmp_path)]
    assert main(sealing) == 0
    lock = str(tmp_path / f"{RELEASE_ID}.json")
    assert main(["check", str(FIXTURE), "--made-up", "--lock", lock]) == 0
    fewer = read_lock(Path(lock)).model_dump(mode="json")
    fewer["inputs"] = fewer["inputs"][1:]
    Path(lock).write_bytes(Lock.model_validate(fewer).canonical())
    assert main(["check", str(FIXTURE), "--made-up", "--lock", lock]) == 1
    public, _ = said(capsys)
    assert re.search(r" findings=(\d+) .* input_is_locked=\1$", public[-1])


# check, of a release that is not made up


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The made-up city under real ids, written as a release, with its registry beside it."""
    root = tmp_path_factory.mktemp("real")
    write_release(real_release(), root / "releases", survey_registry())
    (root / "registry.toml").write_text(as_toml(survey_registry()), encoding="utf-8")
    return root


def checking(real: Path, tmp_path: Path, found: Evidence) -> list[str]:
    """The arguments that check the real release against some evidence, its lock and its hashes."""
    (tmp_path / "lock.json").write_bytes(lock_of(found).canonical())
    hashes = Hashes(
        release_id=REAL_ID,
        manifest_sha256=sha256(real / "releases" / REAL_ID / MANIFEST),
        evidence_sha256=found.digest(),
        lock_sha256=lock_of(found).digest(),
    )
    (tmp_path / "hashes.json").write_text(hashes.model_dump_json(), encoding="utf-8")
    return [
        *("check", str(real / "releases" / REAL_ID), "--evidence", written(tmp_path, found)),
        *("--lock", str(tmp_path / "lock.json"), "--registry", str(real / "registry.toml")),
        *("--hashes", str(tmp_path / "hashes.json")),
    ]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_check_passes_a_real_release_held_to_its_lock_and_the_registry(
    real: Path, tmp_path: Path, capsys: Printed
):
    assert main(checking(real, tmp_path, real_evidence())) == 0
    line = (
        f"step=check status=ok release={REAL_ID} facts=3241 rows=3457 files=6 findings=0 "
        f"evidence_sha256={real_evidence().digest()}"
    )
    assert said(capsys) == ([line], [])


def test_check_fails_when_a_figure_rests_on_a_file_kept_for_the_audit(
    real: Path, tmp_path: Path, capsys: Printed
):
    homes = next(r for r in real_evidence().receipts if r.publisher_file == "made-up-homes.csv")
    planted = with_receipt(real_evidence(), homes.file_id, use="audit_only")
    found = tmp_path / "findings.txt"
    assert main([*checking(real, tmp_path, planted), "--list", str(found)]) == 1
    public, words = said(capsys)
    assert words == []
    assert public == [
        f"step=check status=failed release={REAL_ID} facts=3241 rows=3457 files=6 "
        f"findings=6469 evidence_sha256={planted.digest()} "
        "evidence_is_for_the_product=3181 input_is_for_the_product=3288"
    ]
    listed = found.read_text(encoding="utf-8").splitlines()
    assert len(listed) == 6469
    assert (
        "lon-n0001/feature/park_proximity rests on a file kept for the audit or for the "
        "census table [input_is_for_the_product]"
    ) in listed


def test_check_of_a_real_release_is_not_run_without_the_lock_of_its_build(
    real: Path, tmp_path: Path, capsys: Printed
):
    args = checking(real, tmp_path, real_evidence())
    at = args.index("--lock")
    assert main(args[:at] + args[at + 2 :]) == 2
    public, words = said(capsys)
    assert public == ["step=check status=refused real_release_needs_a_lock=1"]
    assert words == [
        f"error: {REAL_ID} is not made up, and such a release is checked only against the "
        "lock of its build. Give --lock, with the lock that was sealed for the build "
        "[real_release_needs_a_lock]"
    ]


def test_check_of_a_real_release_is_not_run_without_the_hashes_of_its_build(
    real: Path, tmp_path: Path, capsys: Printed
):
    args = checking(real, tmp_path, real_evidence())
    assert main(args[: args.index("--hashes")]) == 2
    public, words = said(capsys)
    assert public == ["step=check status=refused real_release_needs_its_hashes=1"]
    assert words == [
        f"error: {REAL_ID} is not made up, and such a release is checked only against the "
        "hashes of its build. Give --hashes, with the hashes the build wrote beside the release "
        "[real_release_needs_its_hashes]"
    ]


@pytest.mark.parametrize("changed", ["evidence.json", "lock.json", "hashes.json"])
def test_check_refuses_evidence_a_lock_or_hashes_changed_after_the_build(
    real: Path, tmp_path: Path, capsys: Printed, changed: str
):
    """Evidence that was changed stayed well formed, and nothing minded. Now each is hashed."""
    args = checking(real, tmp_path, real_evidence())
    if changed == "hashes.json":
        hashes = json.loads((tmp_path / changed).read_bytes()) | {"manifest_sha256": "0" * 64}
        (tmp_path / changed).write_text(json.dumps(hashes), encoding="utf-8")
    else:
        (tmp_path / changed).write_bytes((tmp_path / changed).read_bytes() + b" ")
    assert main(args) == 2
    public, words = said(capsys)
    assert public == ["step=check status=refused build_is_as_it_was_written=1"]
    assert len(words) == 1 and words[0].endswith("[build_is_as_it_was_written]")
    assert "is not as it was when the release was built" in words[0]


def test_check_refuses_the_hashes_of_another_release(real: Path, tmp_path: Path, capsys: Printed):
    args = checking(real, tmp_path, real_evidence())
    hashes = json.loads((tmp_path / "hashes.json").read_bytes())
    other = json.dumps(hashes | {"release_id": "lon-2026-09-22-01"})
    (tmp_path / "hashes.json").write_text(other, encoding="utf-8")
    assert main(args) == 2
    assert said(capsys)[0] == ["step=check status=refused build_is_as_it_was_written=1"]


def test_check_of_a_made_up_release_needs_no_lock(tmp_path: Path, capsys: Printed):
    assert main(["check", str(FIXTURE), "--evidence", written(tmp_path, evidence())]) == 0
    assert said(capsys)[0][0].startswith("step=check status=ok ")


def test_check_of_a_real_release_is_not_run_without_the_registry(
    real: Path, tmp_path: Path, capsys: Printed
):
    args = checking(real, tmp_path, real_evidence())
    args[args.index("--registry") + 1] = str(tmp_path / "nowhere.toml")
    assert main(args) == 2
    public, words = said(capsys)
    assert public == ["step=check status=unreadable"]
    assert len(words) == 1 and words[0].startswith("error: ")


@pytest.mark.parametrize(
    "content",
    [
        CANARY.encode(),
        json.dumps({"rows": [{"name": CANARY, "postcode": CANARY}]}).encode(),
        json.dumps({CANARY: CANARY}).encode(),
        json.dumps([CANARY]).encode(),
    ],
)
def test_evidence_that_is_not_evidence_is_refused_without_what_it_holds(
    tmp_path: Path, capsys: Printed, content: bytes
):
    (tmp_path / "evidence.json").write_bytes(content)
    assert main(["check", str(FIXTURE), "--evidence", str(tmp_path / "evidence.json")]) == 2
    public, words = said(capsys)
    assert public == ["step=check status=unreadable"]
    assert len(words) == 1 and words[0].startswith("error: ") and "evidence.json" in words[0]


def test_a_release_that_is_not_one_is_refused(tmp_path: Path, capsys: Printed):
    assert main(["check", str(tmp_path), "--made-up"]) == 2
    assert main(["coverage", str(tmp_path), "--out", str(tmp_path / "report.md")]) == 2
    public, words = said(capsys)
    assert public == ["step=check status=unreadable", "step=report status=unreadable"]
    assert len(words) == 2 and all(line.startswith("error: ") for line in words)
    assert not (tmp_path / "report.md").exists()


def test_a_command_says_what_it_needs(tmp_path: Path, capsys: Printed):
    out = ["--out", str(tmp_path)]
    for wrong in (
        ["check", str(FIXTURE)],
        ["check", str(FIXTURE), "--made-up", "--evidence", "evidence.json"],
        ["coverage", str(FIXTURE), "--made-up"],
        ["coverage", str(FIXTURE), "--made-up", "--evidence", "evidence.json", *out],
        ["seal", "--commit", COMMIT, *out],
        ["seal", "--commit", COMMIT, "--release-id", REAL_ID, *out],
        [
            *("seal", "--commit", COMMIT, "--release-id", REAL_ID),
            *("--built-at", "2026-09-23T00:00:00Z", "--vault-listing", "listing.json", *out),
        ],
        ["seal", "--commit", COMMIT, "--made-up", str(FIXTURE), "--list", "m1", *out],
        ["seal", "--commit", COMMIT, "--made-up", str(FIXTURE), "--release-id", REAL_ID, *out],
    ):
        with pytest.raises(SystemExit) as stopped:
            main(wrong)
        assert stopped.value.code == 2
    assert said(capsys)[0] == []
    assert list(tmp_path.iterdir()) == []


# coverage


def test_coverage_writes_the_report_and_prints_one_line_of_counts(tmp_path: Path, capsys: Printed):
    out, table = tmp_path / "coverage.md", tmp_path / "coverage.json"
    code = main(["coverage", str(FIXTURE), "--made-up", "--out", str(out), "--json", str(table)])
    assert code == 0
    public, words = said(capsys)
    assert words == [] and len(public) == 1
    assert public[0].startswith(
        f"step=report status=ok release={RELEASE_ID} areas=24 measures=144 values=3117 gaps=339 "
    )
    assert public[0].endswith(f" coverage_sha256={hashlib.sha256(table.read_bytes()).hexdigest()}")
    committed = Path(__file__).parent / "fixtures" / f"coverage-{RELEASE_ID}.md"
    assert out.read_bytes() == committed.read_bytes()


def test_coverage_takes_what_the_build_left_out_and_says_why(tmp_path: Path, capsys: Printed):
    """The build writes `build.json` beside the release. It says what was left out, by rule."""
    record, out = tmp_path / "build.json", tmp_path / "coverage.md"
    dropped = "park_proximity"
    left_out = {
        "feature_id": dropped,
        "rule": "measure_is_as_core_says",
        "why": "It is not named as core names it. Change one of them",
        "waits_on": ["Core names it a walk."],
    }
    record.write_text(json.dumps({"measures_left_out": [left_out]}))
    args = ["coverage", str(FIXTURE), "--made-up", "--out", str(out), "--build", str(record)]
    # The made-up release carries the measure, so nothing may be said of why it is left out.
    assert main(args) == 2
    public, words = said(capsys)
    assert public == ["step=report status=unreadable"]
    assert "left out" in words[0]
    for wrong in ("[]", json.dumps({"measures_left_out": [{"rule": CANARY}]}), "not json"):
        record.write_text(wrong)
        assert main(args) == 2
        assert said(capsys)[0] == ["step=report status=unreadable"]
    record.write_text(json.dumps({"measures_left_out": []}))
    assert main(args) == 0
    committed = Path(__file__).parent / "fixtures" / f"coverage-{RELEASE_ID}.md"
    assert out.read_bytes() == committed.read_bytes()


def test_coverage_with_no_evidence_says_that_nothing_has_a_record(tmp_path: Path, capsys: Printed):
    assert main(["coverage", str(FIXTURE), "--out", str(tmp_path / "coverage.md")]) == 0
    # Every pair of an area and a measure: 144 measures in 24 areas.
    assert " no_record=3456 " in said(capsys)[0][0]


def test_coverage_counts_by_homes_when_it_is_given_them(tmp_path: Path, capsys: Printed):
    homes, out = tmp_path / "homes.json", tmp_path / "coverage.md"
    args = ["coverage", str(FIXTURE), "--made-up", "--homes", str(homes), "--out", str(out)]
    homes.write_text(json.dumps({a.area_id: 100 for a in release().neighbourhoods}))
    assert main(args) == 0
    assert "| Share of homes covered |" in out.read_text(encoding="utf-8")
    # A count that is no number, and a count for one area alone.
    for wrong in ({"syn-n0001": CANARY}, {"syn-n0001": 100}):
        homes.write_text(json.dumps(wrong))
        assert main(args) == 2
    public, words = said(capsys)
    assert public[1:] == ["step=report status=unreadable"] * 2 and len(words) == 2


# seal


def receipt_of(content: bytes, source_id: str) -> Receipt:
    sha256 = hashlib.sha256(content).hexdigest()
    fields = RECEIPT.model_dump(mode="json") | {
        "file_id": file_id_of(sha256),
        "sha256": sha256,
        "bytes": len(content),
        "source_id": source_id,
        "how": "fetched",
        "url": f"https://data.example.org/{source_id}.csv",
        "publisher_file": f"{source_id}.csv",
    }
    return Receipt.model_validate(fields)


REGISTRY = """
schema_version = 1

[[source]]
id = "made-up-parks"
name = "Made-up parks"
publisher = "A made-up publisher"
url = "https://example.org/parks"
dimension = "environment"
licence = "OGL-3.0"
commercial_use = "yes"
share_alike = false
attribution = "Contains made-up data."
attribution_verified = true
status = "{status}"
status_reason = "{reason}"
uses = ["{use}"]
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://example.org/licence"]
"""


def the_parks() -> Receipt:
    return receipt_of(f"park_id,name\n1,{CANARY}\n".encode(), "made-up-parks")


def a_build(tmp_path: Path, status: str = "approved", stored: bool = True) -> list[str]:
    """The arguments that seal one made-up file: its list, a registry and a vault's listing."""
    found = the_parks()
    path = tmp_path / found.path()
    path.parent.mkdir(parents=True)
    path.write_bytes(found.canonical())
    approved = status == "approved"
    reason = "" if approved else "Its terms have not been read."
    use = "scoring" if approved else "validation_only"
    (tmp_path / "registry.toml").write_text(REGISTRY.format(status=status, reason=reason, use=use))
    listing = {found.vault_key(): found.bytes} if stored else {}
    (tmp_path / "vault.json").write_text(json.dumps(listing))
    (tmp_path / "made-up.toml").write_text(list_as_toml([listed(found, "parks")]))
    return [
        "seal",
        *("--release-id", REAL_ID, "--built-at", "2026-09-23T00:00:00Z"),
        *("--commit", COMMIT, "--receipts", str(tmp_path / "data" / "receipts")),
        *("--list", str(tmp_path / "made-up.toml")),
        *("--vault-listing", str(tmp_path / "vault.json")),
        *("--registry", str(tmp_path / "registry.toml"), "--root", str(tmp_path)),
        *("--out", str(tmp_path / "data" / "locks")),
    ]


def test_seal_writes_the_lock_and_prints_its_hash(tmp_path: Path, capsys: Printed):
    assert main(a_build(tmp_path)) == 0
    lock = read_lock(tmp_path / "data" / "locks" / f"{REAL_ID}.json")
    assert [found.source_id for found in lock.inputs] == ["made-up-parks"]
    line = f"step=seal status=ok release={REAL_ID} inputs=1 development=1 "
    assert said(capsys) == ([line + f"lock_sha256={lock.digest()}"], [])


def test_seal_is_refused_when_the_gate_refuses_and_writes_no_lock(tmp_path: Path, capsys: Printed):
    assert main(a_build(tmp_path, status="gated")) == 2
    public, words = said(capsys)
    assert len(public) == 1 and len(words) == 1
    assert re.fullmatch(
        r"step=seal status=refused gate_refuses=1 file_id=f-[0-9a-f]{12}", public[0]
    )
    assert "[gate_refuses]" in words[0] and "'made-up-parks' is gated, not approved" in words[0]
    assert not (tmp_path / "data" / "locks").exists()


def test_seal_refuses_a_file_kept_for_the_audit_and_writes_no_lock(tmp_path: Path, capsys: Printed):
    args = a_build(tmp_path)
    faiths = registered(
        "made-up-faiths", Use.AUDIT_ONLY, status=Status.HELD, heading=Dimension.AUDIT
    )
    parks = registered("made-up-parks", Use.SCORING, heading=Dimension.ENVIRONMENT)
    (tmp_path / "registry.toml").write_text(as_toml(registry_of(parks, faiths)))
    # The file is fetched as the gate allows, and is in the vault with its receipt.
    fields = receipt_of(f"oa21cd,faith\nE00000001,{CANARY}\n".encode(), "made-up-faiths")
    kept_apart = Receipt.model_validate(fields.model_dump(mode="json") | {"use": "audit_only"})
    path = tmp_path / kept_apart.path()
    path.parent.mkdir(parents=True)
    path.write_bytes(kept_apart.canonical())
    listing = json.loads((tmp_path / "vault.json").read_text())
    listing[kept_apart.vault_key()] = kept_apart.bytes
    (tmp_path / "vault.json").write_text(json.dumps(listing))
    # And the list names it. Nothing else is out of order.
    named = [listed(the_parks(), "parks"), listed(kept_apart, "faiths")]
    (tmp_path / "made-up.toml").write_text(list_as_toml(named))

    assert main(args) == 2
    public, words = said(capsys)
    assert public == [
        f"step=seal status=refused file_is_for_the_product=1 file_id={kept_apart.file_id}"
    ]
    assert len(words) == 1 and words[0].endswith("[file_is_for_the_product]")
    assert "is kept for the audit or for the census table" in words[0]
    assert "made-up-faiths" not in words[0]
    assert not (tmp_path / "data" / "locks").exists()


def test_seal_is_refused_when_a_file_is_not_in_the_vault(tmp_path: Path, capsys: Printed):
    assert main(a_build(tmp_path, stored=False)) == 2
    public, words = said(capsys)
    assert public[0].startswith("step=seal status=refused file_is_in_the_vault=1 file_id=f-")
    assert "[file_is_in_the_vault]" in words[0] and "raw/" not in words[0]
    assert not (tmp_path / "data" / "locks").exists()


def test_seal_is_refused_when_there_is_nothing_to_seal(tmp_path: Path, capsys: Printed):
    args = a_build(tmp_path)
    for path in (tmp_path / "data" / "receipts").rglob("*.json"):
        path.unlink()
    (tmp_path / "made-up.toml").write_text(list_as_toml([]))
    assert main(args) == 2
    public, words = said(capsys)
    assert public == ["step=seal status=refused lock_has_an_input=1"]
    assert len(words) == 1 and words[0].endswith("[lock_has_an_input]")
    assert not (tmp_path / "data" / "locks").exists()


# seal, and the code of the build

in_a_repository = pytest.mark.skipif(GIT is None, reason="git is needed to make a repository")


def a_build_in(repository: Path) -> list[str]:
    """The arguments that seal one made-up file in a repository, with everything committed."""
    args = a_build(repository)
    git(repository, "add", "data", "registry.toml", "made-up.toml")
    git(repository, "commit", "--quiet", "--message", "The receipts, the list and the registry")
    at = args.index("--commit")
    return args[:at] + args[at + 2 :]


@in_a_repository
def test_seal_reads_the_commit_from_the_repository(repository: Path, capsys: Printed):
    args = a_build_in(repository)
    assert main(args) == 0
    lock = read_lock(repository / "data" / "locks" / f"{REAL_ID}.json")
    assert lock.commit == git(repository, "rev-parse", "HEAD") != COMMIT
    public, words = said(capsys)
    assert words == [] and public[0].startswith("step=seal status=ok ")
    # The lock it wrote is not tracked, so the step may be run again.
    assert main(args) == 0


@in_a_repository
def test_seal_is_refused_under_a_commit_that_is_not_checked_out(repository: Path, capsys: Printed):
    assert main([*a_build_in(repository), "--commit", COMMIT]) == 2
    public, words = said(capsys)
    assert public == ["step=seal status=refused commit_is_checked_out=1"]
    assert len(words) == 1 and words[0].endswith("[commit_is_checked_out]")
    assert COMMIT not in words[0] and "Leave --commit out" in words[0]
    assert not (repository / "data" / "locks").exists()


@in_a_repository
def test_seal_is_refused_in_a_working_copy_with_changes(repository: Path, capsys: Printed):
    args = a_build_in(repository)
    write(repository, {"a/first.py": f"FIRST = '{CANARY}'\n"})
    assert main(args) == 2
    public, words = said(capsys)
    assert public == ["step=seal status=refused tree_has_no_changes=1"]
    assert words == [
        "error: the working copy holds changes that are not committed, so no commit names "
        "the code it holds: 1 tracked file is not as git last took it. Commit the changes "
        "or put them aside, and seal again. `git status` shows them [tree_has_no_changes]"
    ]
    assert not (repository / "data" / "locks").exists()


@in_a_repository
def test_seal_from_a_folder_inside_a_repository_is_held_to_the_repository(
    repository: Path, capsys: Printed
):
    args = a_build_in(repository)
    args[args.index("--root") + 1] = str(repository / "a" / "deeper")
    # A commit that is given is held to the one that is checked out, and is not taken.
    assert main([*args, "--commit", COMMIT]) == 2
    assert said(capsys)[0] == ["step=seal status=refused commit_is_checked_out=1"]
    # A change in a folder beside the one given is seen.
    write(repository, {"README.md": f"{CANARY}\n"})
    assert main(args) == 2
    public, words = said(capsys)
    assert public == ["step=seal status=refused tree_has_no_changes=1"]
    assert len(words) == 1 and words[0].endswith("[tree_has_no_changes]")
    assert not (repository / "data" / "locks").exists()
    # With the change put back, the commit is read from the repository above.
    write(repository, {"README.md": "Made up for a test.\n"})
    assert main(args) == 0
    lock = read_lock(repository / "data" / "locks" / f"{REAL_ID}.json")
    assert lock.commit == git(repository, "rev-parse", "HEAD") != COMMIT


def test_seal_outside_a_repository_needs_the_commit_to_be_given(tmp_path: Path, capsys: Printed):
    args = a_build(tmp_path)
    at = args.index("--commit")
    assert main(args[:at] + args[at + 2 :]) == 2
    public, words = said(capsys)
    assert public == ["step=seal status=refused commit_is_named=1"]
    assert len(words) == 1 and words[0].endswith("[commit_is_named]")
    assert not (tmp_path / "data" / "locks").exists()


# seal, and the list of the build


def another(tmp_path: Path, edition: str) -> Receipt:
    """The receipt of another edition of the parks, in the folder and in the vault."""
    found = receipt_of(f"park_id,name\n1,{CANARY}\n2,{edition}\n".encode(), "made-up-parks")
    found = Receipt.model_validate(found.model_dump(mode="json") | {"edition": edition})
    (tmp_path / found.path()).write_bytes(found.canonical())
    listing = json.loads((tmp_path / "vault.json").read_text())
    (tmp_path / "vault.json").write_text(json.dumps(listing | {found.vault_key(): found.bytes}))
    return found


def test_seal_is_refused_when_a_file_of_the_list_has_no_receipt(tmp_path: Path, capsys: Printed):
    args = a_build(tmp_path)
    rivers = listed(the_parks(), "rivers").model_copy(update={"edition": "2026"})
    (tmp_path / "made-up.toml").write_text(list_as_toml([listed(the_parks(), "parks"), rivers]))
    assert main(args) == 2
    public, words = said(capsys)
    assert public == ["step=seal status=refused listed_file_has_a_receipt=1"]
    assert len(words) == 1 and words[0].endswith("[listed_file_has_a_receipt]")
    assert words[0].startswith("error: rivers is a file of the list, and no receipt of it is")
    assert "Fetch the file, or bring its receipt back" in words[0]
    assert not (tmp_path / "data" / "locks").exists()


def test_seal_is_refused_when_a_receipt_is_there_that_the_list_does_not_name(
    tmp_path: Path, capsys: Printed
):
    args = a_build(tmp_path)
    second = another(tmp_path, "2026")
    assert main(args) == 2
    public, words = said(capsys)
    assert public == [f"step=seal status=refused receipt_is_listed=1 file_id={second.file_id}"]
    assert len(words) == 1 and words[0].endswith("[receipt_is_listed]")
    assert "move its receipt out of the folder" in words[0]
    assert not (tmp_path / "data" / "locks").exists()
    # With the second edition named, and the first too, both are sealed.
    named = [listed(the_parks(), "parks"), listed(second, "parks-2026")]
    (tmp_path / "made-up.toml").write_text(list_as_toml(named))
    assert main(args) == 0
    lock = read_lock(tmp_path / "data" / "locks" / f"{REAL_ID}.json")
    assert [found.name for found in lock.inputs] == sorted([the_parks().file_id, second.file_id])


def test_seal_takes_a_list_by_its_name_as_fetch_does(tmp_path: Path, capsys: Printed):
    args = a_build(tmp_path)
    args[args.index("--list") + 1] = "m1"
    (tmp_path / the_parks().path()).unlink()
    assert main(args) == 2
    public, words = said(capsys)
    assert public == ["step=seal status=refused listed_file_has_a_receipt=1"]
    assert words[0].startswith(f"error: {load_list('m1').files[0].item} is a file of the list")


@pytest.mark.parametrize("which", ["zzyzx", "zzyzx.toml", CANARY])
def test_seal_is_refused_when_the_list_cannot_be_read(tmp_path: Path, capsys: Printed, which: str):
    args = a_build(tmp_path)
    args[args.index("--list") + 1] = which
    assert main(args) == 2
    public, words = said(capsys)
    assert public == ["step=seal status=unreadable"]
    assert len(words) == 1
    assert words[0].startswith("error: the list of the build cannot be read: ")
    assert "zzyzx" not in words[0]
    assert not (tmp_path / "data" / "locks").exists()


def test_seal_never_repeats_an_argument_it_refuses(tmp_path: Path, capsys: Printed):
    args = a_build(tmp_path)
    args[args.index("--release-id") + 1] = CANARY
    args[args.index("--built-at") + 1] = CANARY
    args[args.index("--commit") + 1] = CANARY
    assert main(args) == 2
    public, words = said(capsys)
    assert public == ["step=seal status=refused lock_is_valid=1"]
    assert "[lock_is_valid]" in words[0]


def test_seal_names_the_packages_of_a_build_of_record(tmp_path: Path, capsys: Printed):
    (tmp_path / "packages.lock").write_bytes(b"a made-up lockfile")
    assert main([*a_build(tmp_path), "--packages", str(tmp_path / "packages.lock")]) == 0
    lock = read_lock(tmp_path / "data" / "locks" / f"{REAL_ID}.json")
    assert lock.packages == hashlib.sha256(b"a made-up lockfile").hexdigest()
    assert " development=0 " in said(capsys)[0][0]


def test_the_same_made_up_build_seals_to_the_same_bytes(tmp_path: Path, capsys: Printed):
    for out in ("one", "two"):
        args = ["seal", "--made-up", str(FIXTURE), *COMMITTED, "--out", str(tmp_path / out)]
        assert main(args) == 0
    one, two = (tmp_path / out / f"{RELEASE_ID}.json" for out in ("one", "two"))
    assert one.read_bytes() == two.read_bytes()
    public, _ = said(capsys)
    assert public[0] == public[1]
