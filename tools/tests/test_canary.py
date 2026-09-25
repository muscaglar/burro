"""The canary: a marked row and a marked key, planted and then searched for.

Every row, key and address here is made up. No socket is opened: the website's
answers are played back from a table.
"""

import io
import json
from collections.abc import Mapping
from pathlib import Path

import canary
import pytest
from canary import Answer, markers_of, plant, planted_release, search
from public_log import SECRET_NAMES, is_public

FIXTURE = Path(__file__).resolve().parents[2] / "data" / "fixtures" / "synthetic"
RUN = {"GITHUB_RUN_ID": "1234567890"}
MARKERS = markers_of(RUN)


def planted(environ: Mapping[str, str] | None = None) -> tuple[int, str]:
    out = io.StringIO()
    return plant(FIXTURE, {"PATH": "/usr/bin:/bin", **RUN, **(environ or {})}, out), out.getvalue()


# The markers


def test_every_job_of_a_run_knows_the_same_markers_and_no_other_run_does():
    assert markers_of(RUN) == markers_of({**RUN, "GITHUB_RUN_ATTEMPT": "2"})
    assert markers_of(RUN) != markers_of({"GITHUB_RUN_ID": "1234567891"})
    assert MARKERS.row != MARKERS.key


def test_away_from_a_run_the_markers_are_new_each_time():
    assert markers_of({}) != markers_of({})


def test_a_marker_is_not_written_in_this_repository():
    # A marker that stood in a file would be found in a log that quotes the file.
    source = Path(canary.__file__).read_text()
    assert MARKERS.row not in source and MARKERS.key not in source


def test_every_secret_is_given_a_marked_value_long_enough_to_search_for():
    secrets = MARKERS.secrets()
    assert set(secrets) == set(SECRET_NAMES)
    assert all(MARKERS.key in value for value in secrets.values())
    assert secrets["BURRO_STORE_ENDPOINT"].startswith("https://")
    assert secrets["BURRO_RELEASES_ENDPOINT"].startswith("https://")
    assert len(set(secrets.values())) == len(secrets)


# The planted releases


def test_the_marked_row_is_planted_in_a_copy_and_the_fixture_is_not_touched(tmp_path: Path):
    before = {path.name: path.read_bytes() for path in sorted(FIXTURE.rglob("*")) if path.is_file()}
    whole, broken = planted_release(FIXTURE, tmp_path, MARKERS)
    after = {path.name: path.read_bytes() for path in sorted(FIXTURE.rglob("*")) if path.is_file()}
    assert before == after
    assert MARKERS.row.encode() in (whole / "places.json").read_bytes()
    assert MARKERS.row.encode() in (broken / "places.json").read_bytes()


def test_one_planted_release_still_matches_its_manifest_and_one_cannot_be_parsed(tmp_path: Path):
    import hashlib

    whole, broken = planted_release(FIXTURE, tmp_path, MARKERS)
    manifest = json.loads((whole / "manifest.json").read_text())
    places = next(entry for entry in manifest["files"] if entry["name"] == "places.json")
    content = (whole / "places.json").read_bytes()
    assert places == {
        "name": "places.json",
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
    }
    assert manifest["counts"]["places"] == len(json.loads(content)["places"])
    with pytest.raises(json.JSONDecodeError):
        json.loads((broken / "places.json").read_bytes())


# Planting, and searching what was shown


@pytest.fixture(scope="module")
def clean() -> tuple[int, str]:
    """The canary run once as it stands. Three tests read what it showed."""
    return planted()


def test_on_the_synthetic_release_nothing_that_is_shown_holds_the_row_or_the_key(
    clean: tuple[int, str],
):
    status, out = clean
    assert status == 0, out
    assert MARKERS.row not in out and MARKERS.key not in out
    assert out.splitlines()[-1].startswith("step=canary status=ok steps=3 found=0")


def test_the_canary_shows_only_what_the_public_log_would_show(clean: tuple[int, str]):
    _, out = clean
    assert all(is_public(line) for line in out.splitlines()), out


def test_the_canary_reads_a_release_with_the_projects_own_reader(clean: tuple[int, str]):
    _, out = clean
    # The reader accepts a release or refuses it with 2. Anything else did not run it.
    assert "step=check status=ok exit=0" in out
    assert "step=check status=failed exit=2" in out


def test_the_canary_fails_when_the_log_lets_a_row_through(monkeypatch: pytest.MonkeyPatch):
    def shows_everything(line: str) -> bool:
        return True

    monkeypatch.setattr("public_log.is_public", shows_everything)
    status, out = planted()
    assert status == 1
    assert out.splitlines()[-1].startswith("step=canary status=failed steps=3 found=1")
    # What was shown is printed as it was. The marker is made up, so it harms nothing.
    assert MARKERS.row in out


def test_the_canary_fails_when_a_printed_key_is_not_caught(monkeypatch: pytest.MonkeyPatch):
    def catches_nothing(line: str, forms: frozenset[str]) -> bool:
        return False

    monkeypatch.setattr("public_log.holds_a_secret", catches_nothing)
    status, out = planted()
    assert status == 1
    assert "step=canary status=failed" in out.splitlines()[-1]


def test_the_canary_fails_when_a_step_can_write_to_the_runs_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("public_log.RUNNERS_FILES", ())
    summary = tmp_path / "summary.md"
    status, out = planted({"GITHUB_STEP_SUMMARY": str(summary)})
    assert status == 1
    assert MARKERS.row in summary.read_text()
    assert MARKERS.row not in out


def test_the_canary_fails_when_the_reader_cannot_be_run(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("canary.READER", ["made-up-command-that-is-not-there"])
    status, out = planted()
    assert status == 1
    assert "step=canary status=failed" in out.splitlines()[-1]


def test_the_canary_fails_when_there_is_no_synthetic_release(tmp_path: Path):
    out = io.StringIO()
    assert plant(tmp_path, RUN, out) == 1
    assert out.getvalue() == "step=canary status=missing\n"


# Searching what a run made public

API = "https://api.example.test"
REPOSITORY = "made-up/repository"
WHERE = {
    "GITHUB_API_URL": API,
    "GITHUB_REPOSITORY": REPOSITORY,
    "GITHUB_RUN_ID": RUN["GITHUB_RUN_ID"],
    "GITHUB_RUN_ATTEMPT": "1",
    "GITHUB_TOKEN": "made-up-token-0123456789",
}
JOBS = f"{API}/repos/{REPOSITORY}/actions/runs/1234567890/attempts/1/jobs?per_page=100"
ARTIFACTS = f"{API}/repos/{REPOSITORY}/actions/runs/1234567890/artifacts?per_page=100"
LOG = f"{API}/repos/{REPOSITORY}/actions/jobs/{{}}/logs"
ELSEWHERE = "https://logs.example.test/made-up/{}"
CLEAN = "step=assemble status=ok exit=0 withheld=3 seconds=1.0\n"


def job(number: int, status: str = "completed", conclusion: str = "success") -> dict[str, object]:
    return {"id": number, "name": f"job {number}", "status": status, "conclusion": conclusion}


class Website:
    """The website's answers, played back. It records what it was asked, and with which token."""

    def __init__(self, logs: Mapping[int, str], artifacts: int = 0) -> None:
        jobs = [job(number) for number in logs] + [job(99, "in_progress", "")]
        self.answers: dict[str, Answer] = {
            JOBS: Answer(200, json.dumps({"total_count": len(jobs), "jobs": jobs}).encode()),
            ARTIFACTS: Answer(200, json.dumps({"total_count": artifacts}).encode()),
        }
        for number, text in logs.items():
            self.answers[LOG.format(number)] = Answer(302, b"", ELSEWHERE.format(number))
            self.answers[ELSEWHERE.format(number)] = Answer(200, text.encode())
        self.asked: list[tuple[str, str | None]] = []

    def __call__(self, address: str, token: str | None) -> Answer:
        self.asked.append((address, token))
        return self.answers.get(address, Answer(404, b""))


def searched(website: Website, environ: Mapping[str, str] = WHERE) -> tuple[int, str]:
    out = io.StringIO()
    status = search(environ, out, website, wait=lambda seconds: None)
    return status, out.getvalue()


def test_a_run_whose_logs_hold_no_marker_and_that_uploaded_nothing_passes():
    status, out = searched(Website({1: CLEAN, 2: CLEAN}))
    assert (status, out) == (0, "step=search status=ok jobs=2 logs=2 artifacts=0 found=0\n")


@pytest.mark.parametrize("leaked", [MARKERS.row, MARKERS.key, MARKERS.key.upper()])
def test_a_marker_in_any_jobs_log_fails_the_run(leaked: str):
    status, out = searched(Website({1: CLEAN, 2: f"{CLEAN}made-up {leaked} made-up\n"}))
    assert status == 1
    assert out == "step=search status=failed jobs=2 logs=2 artifacts=0 found=1\n"


def test_the_shape_of_a_stores_address_in_a_log_fails_the_run():
    log = f"{CLEAN}connecting to made-up-account.r2.cloudflarestorage.com\n"
    assert searched(Website({1: log}))[0] == 1


def test_anything_uploaded_fails_the_run():
    status, out = searched(Website({1: CLEAN}, artifacts=1))
    assert (status, out) == (1, "step=search status=failed jobs=1 logs=1 artifacts=1 found=0\n")


def test_the_job_that_searches_does_not_wait_for_its_own_log():
    website = Website({1: CLEAN})
    searched(website)
    assert LOG.format(99) not in [address for address, _ in website.asked]


def test_a_job_that_never_ran_has_no_log_to_search():
    website = Website({1: CLEAN})
    skipped = [job(1), job(2, conclusion="skipped")]
    body = json.dumps({"total_count": 2, "jobs": skipped}).encode()
    website.answers[JOBS] = Answer(200, body)
    assert searched(website) == (0, "step=search status=ok jobs=1 logs=1 artifacts=0 found=0\n")


@pytest.mark.parametrize(
    "broken",
    [
        {JOBS: Answer(500, b"")},
        {JOBS: Answer(200, b"not json")},
        {JOBS: Answer(200, b'{"jobs": []}')},
        {JOBS: Answer(200, json.dumps({"total_count": 101, "jobs": [job(1)]}).encode())},
        {ARTIFACTS: Answer(403, b"")},
        {ARTIFACTS: Answer(200, b"{}")},
        {LOG.format(1): Answer(404, b"")},
        {LOG.format(1): Answer(302, b"", "")},
        {LOG.format(1): Answer(302, b"", "http://logs.example.test/made-up/1")},
        {ELSEWHERE.format(1): Answer(403, b"")},
    ],
)
def test_a_run_that_cannot_be_read_fails(broken: dict[str, Answer]):
    website = Website({1: CLEAN})
    website.answers |= broken
    status, out = searched(website)
    assert status == 1
    assert out == "step=search status=unreadable\n"


def test_a_log_that_is_not_ready_is_asked_for_again():
    website = Website({1: CLEAN})
    ready = website.answers[LOG.format(1)]
    answers = iter([Answer(404, b""), Answer(404, b""), ready])
    waited: list[float] = []

    def fetch(address: str, token: str | None) -> Answer:
        return next(answers) if address == LOG.format(1) else website(address, token)

    out = io.StringIO()
    assert search(WHERE, out, fetch, wait=waited.append) == 0
    assert len(waited) == 2


def test_the_token_goes_to_the_website_and_never_to_where_a_log_is_kept():
    website = Website({1: CLEAN})
    searched(website)
    tokens = dict(website.asked)
    assert tokens[JOBS] == tokens[LOG.format(1)] == WHERE["GITHUB_TOKEN"]
    assert tokens[ELSEWHERE.format(1)] is None


@pytest.mark.parametrize("name", sorted(WHERE))
def test_away_from_a_run_there_is_nothing_to_search(name: str):
    website = Website({1: CLEAN})
    status, out = searched(website, {key: value for key, value in WHERE.items() if key != name})
    assert (status, out) == (1, "step=search status=unreadable\n")
    assert website.asked == []


def test_the_website_is_asked_over_https_only():
    website = Website({1: CLEAN})
    status, _ = searched(website, {**WHERE, "GITHUB_API_URL": "http://api.example.test"})
    assert status == 1
    assert website.asked == []


def test_nothing_the_search_prints_holds_the_token_or_a_marker():
    _, out = searched(Website({1: f"{MARKERS.row}\n"}, artifacts=2))
    assert WHERE["GITHUB_TOKEN"] not in out and MARKERS.row not in out
    assert all(is_public(line) for line in out.splitlines())
