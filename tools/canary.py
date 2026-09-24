"""Plant a marked row and a marked key, and fail if either can be seen.

A row or a key in a public log cannot be taken back. So before a run touches
anything real, it proves on made-up data that nothing of the kind gets out.

    python tools/canary.py plant     in the first job, in the project's environment
    python tools/canary.py search    in the last job, with the run's own token

`plant` copies the synthetic release twice and adds a marked row to each. One
copy still matches its manifest. The other is cut short inside the marked row,
so that the reader fails there. It sets every secret of the store to a marked
value, and runs three steps as a workflow runs any step, behind
tools/public_log.py: the reader on each copy, and a step that prints the row,
prints its whole environment, fails with the row in its message, and tries to
write the row to the run's summary. Then it searches what was shown, and the
files the website reads, for the row and the key. What was shown is printed as
it was, so the run's real log holds what a step's log would.

`search` asks the website for the log of every job of this run that has ended,
and for what the run uploaded. It fails if a log holds a marker or the shape
of a store's address, or if anything at all was uploaded.

The markers are worked out from the run's number, so every job of a run knows
them and no file holds them. They are not secrets. Standard library only.
See docs/data-builds.md.
"""

import argparse
import hashlib
import io
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from http.client import HTTPMessage
from pathlib import Path
from typing import IO, Any, TextIO, cast
from urllib.parse import urlsplit

import public_log

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "fixtures" / "synthetic"
PLACES, MANIFEST = "places.json", "manifest.json"
# The project's own reader of a release, run with the interpreter that runs this.
READER = [sys.executable, "-m", "burro_pipeline.release.cli", "check"]
# The reader accepts a release with 0 and refuses one with 2. Any other code did not run it.
ACCEPTED, REFUSED = 0, 2

# What a step must never do, all at once. The row and the files to write to are its arguments.
WORST_STEP = """
import os, sys
row = sys.argv[1]
print(row)
print(dict(os.environ))
for name in sys.argv[2:]:
    if name in os.environ:
        with open(os.environ[name], "a") as file:
            file.write(row + "\\n")
raise ValueError(row)
"""

# Where a step could write something the website shows. Kept apart from the list in
# public_log.py, so that a file dropped from that list is still searched here.
PUBLIC_FILES = ("GITHUB_STEP_SUMMARY", "GITHUB_OUTPUT", "GITHUB_ENV", "GITHUB_PATH", "GITHUB_STATE")

# The store is an R2 bucket. If it moves, its new shape is added here.
STORE_SHAPE = re.compile(r"\.r2\.cloudflarestorage\.com|\.r2\.dev", re.IGNORECASE)
TRIES, SECONDS_BETWEEN = 6, 10.0
LARGEST_LOG = 64 * 1024 * 1024


@dataclass(frozen=True)
class Markers:
    row: str
    key: str

    def secrets(self) -> dict[str, str]:
        """A marked value for every secret, no two the same."""
        names = enumerate(public_log.SECRET_NAMES)
        values = {name: f"{self.key}-{number}" for number, name in names}
        address = {public_log.ENDPOINT: f"https://{self.key}.invalid"}
        return values | address | {public_log.CONTACT: f"{self.key}@canary.invalid"}

    def found_in(self, text: str) -> bool:
        lowered = text.lower()
        return self.row in lowered or self.key in lowered


def markers_of(environ: Mapping[str, str]) -> Markers:
    """The markers of this run. Away from a run they are new each time."""
    run = environ.get("GITHUB_RUN_ID") or secrets.token_hex(16)

    def marker(kind: str) -> str:
        digest = hashlib.sha256(f"burro canary {kind} {run}".encode()).hexdigest()
        return f"canary-{kind}-{digest[:24]}"

    return Markers(marker("row"), marker("key"))


def _canonical(document: object) -> bytes:
    """As `canonical_json` writes a release file, so a planted file is shaped like a real one."""
    text = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return (text + "\n").encode()


def _list_again(release: Path, places: int | None = None) -> None:
    """Make the manifest true of the places file as it now is."""
    content = (release / PLACES).read_bytes()
    manifest = cast(dict[str, Any], json.loads((release / MANIFEST).read_bytes()))
    for entry in cast(list[dict[str, Any]], manifest["files"]):
        if entry["name"] == PLACES:
            entry |= {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
    if places is not None:
        manifest["counts"]["places"] = places
    (release / MANIFEST).write_bytes(_canonical(manifest))


def planted_release(fixture: Path, work: Path, markers: Markers) -> tuple[Path, Path]:
    """Two copies of the synthetic release with a marked row: one whole, one cut short."""
    (source,) = (path for path in sorted(fixture.iterdir()) if path.is_dir())
    whole, broken = work / "whole" / source.name, work / "broken" / source.name
    for copy in (whole, broken):
        shutil.copytree(source, copy)

    document = cast(dict[str, Any], json.loads((whole / PLACES).read_bytes()))
    places = cast(list[dict[str, Any]], document["places"])
    place_id = f"syn-p{len(places) + 1:04d}"
    places.append(
        places[-1] | {"name": markers.row, "aliases": [markers.row], "place_id": place_id}
    )
    (whole / PLACES).write_bytes(_canonical(document))
    _list_again(whole, len(places))

    row = _canonical(places[-1]).rstrip()
    (broken / PLACES).write_bytes((source / PLACES).read_bytes().rstrip()[:-2] + b"," + row[:-1])
    _list_again(broken)
    return whole, broken


def _public_files(environ: Mapping[str, str]) -> str:
    """What stands in the files the website reads after a step."""
    found: list[str] = []
    for name in PUBLIC_FILES:
        path = Path(environ.get(name) or os.devnull)
        if path.is_file():
            found.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(found)


def plant(fixture: Path, environ: Mapping[str, str], out: TextIO) -> int:
    """Run the three steps on planted data. Returns 0 only if nothing planted can be seen."""
    markers = markers_of(environ)
    given = dict(environ) | markers.secrets()
    shown = io.StringIO()
    with tempfile.TemporaryDirectory(prefix="burro-canary-") as work:
        try:
            whole, broken = planted_release(fixture, Path(work), markers)
        except (OSError, ValueError, KeyError, IndexError):
            print("step=canary status=missing", file=out)
            return 1
        worst = [sys.executable, "-c", WORST_STEP, markers.row, *PUBLIC_FILES]
        accepted = public_log.run_step("check", [*READER, str(whole)], given, shown)
        refused = public_log.run_step("check", [*READER, str(broken)], given, shown)
        public_log.run_step("normalise", worst, given, shown)
        public = shown.getvalue() + _public_files(environ)

    caught = re.search(r"^step=normalise status=failed \S+ secrets=[1-9]", shown.getvalue(), re.M)
    # The copy that matches its manifest is accepted today. A later rule may refuse it, and
    # the canary is no judge of a release: it asks only that the reader ran.
    read = accepted in (ACCEPTED, REFUSED) and refused == REFUSED
    failures = [markers.found_in(public), not read, caught is None]
    out.write(shown.getvalue())
    status = "failed" if any(failures) else "ok"
    found, unread, uncaught = (int(failure) for failure in failures)
    counts = f"steps=3 found={found} unread={unread} uncaught={uncaught}"
    print(f"step=canary status={status} {counts}", file=out)
    return int(any(failures))


@dataclass(frozen=True)
class Answer:
    """What the website said: the status, the body, and where it sent the reader on to."""

    status: int
    body: bytes
    location: str = ""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A log is kept on another host. The token must not follow the reader there."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> None:
        return None


def ask(address: str, token: str | None) -> Answer:
    """Ask the website, over https only. Any failure is an answer with the status 0."""
    if urlsplit(address).scheme != "https":
        return Answer(0, b"")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "burro-canary"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(address, headers=headers)  # noqa: S310  https, checked above
    try:
        with urllib.request.build_opener(_NoRedirect).open(request, timeout=60) as response:
            return Answer(response.status, response.read(LARGEST_LOG + 1))
    except urllib.error.HTTPError as error:
        return Answer(error.code, b"", error.headers.get("Location", ""))
    except (urllib.error.URLError, OSError, ValueError):
        return Answer(0, b"")


class _Unreadable(Exception):
    """The website did not answer in the form expected. A search that cannot read fails."""


type Fetch = Callable[[str, str | None], Answer]
type Wait = Callable[[float], None]


def _counted(answer: Answer) -> tuple[int, dict[str, Any]]:
    """How many items a list the website gave holds in all, and the answer itself."""
    try:
        document = cast(dict[str, Any], json.loads(answer.body))
        total = int(document["total_count"])
    except (ValueError, KeyError, TypeError) as error:
        raise _Unreadable from error
    if answer.status != 200:
        raise _Unreadable
    return total, document


def _jobs(answer: Answer) -> list[dict[str, Any]]:
    """The jobs of a run, which must be every job: a list cut short would hide a log."""
    total, document = _counted(answer)
    jobs = cast(list[dict[str, Any]], document.get("jobs", []))
    if total != len(jobs):
        raise _Unreadable
    return jobs


def _log(address: str, token: str, fetch: Fetch, wait: Wait) -> str:
    """The log of one job. It is asked for again while the website has not got it ready."""
    for attempt in range(TRIES):
        if attempt:
            wait(SECONDS_BETWEEN)
        answer = fetch(address, token)
        if answer.status == 302 and urlsplit(answer.location).scheme == "https":
            kept = fetch(answer.location, None)
            if kept.status == 200 and len(kept.body) <= LARGEST_LOG:
                return kept.body.decode(errors="replace")
            raise _Unreadable
        if answer.status != 404:
            raise _Unreadable
    raise _Unreadable


def _ran(job: Mapping[str, Any]) -> bool:
    """Whether a job has ended and has a log. This job has not ended, and a skipped one has none."""
    return job.get("status") == "completed" and job.get("conclusion") != "skipped"


def search(
    environ: Mapping[str, str], out: TextIO, fetch: Fetch = ask, wait: Wait = time.sleep
) -> int:
    """Search the log of every job of this run that has ended, and what the run uploaded."""
    names = ("GITHUB_API_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT")
    api, repository, run, attempt = (environ.get(name, "") for name in names)
    token = environ.get("GITHUB_TOKEN", "")
    markers = markers_of(environ)
    try:
        if not all((api, repository, run, attempt, token)) or urlsplit(api).scheme != "https":
            raise _Unreadable
        of_repository = f"{api}/repos/{repository}/actions"
        of_run = f"{of_repository}/runs/{run}"
        jobs = _jobs(fetch(f"{of_run}/attempts/{attempt}/jobs?per_page=100", token))
        ended = [int(job["id"]) for job in jobs if _ran(job)]
        logs = [_log(f"{of_repository}/jobs/{job}/logs", token, fetch, wait) for job in ended]
        artifacts, _ = _counted(fetch(f"{of_run}/artifacts?per_page=100", token))
        if not logs:
            raise _Unreadable
    except (_Unreadable, KeyError, TypeError, ValueError):
        print("step=search status=unreadable", file=out)
        return 1
    found = sum(markers.found_in(log) or STORE_SHAPE.search(log) is not None for log in logs)
    status = "failed" if found or artifacts else "ok"
    counts = f"jobs={len(ended)} logs={len(logs)} artifacts={artifacts} found={found}"
    print(f"step=search status={status} {counts}", file=out)
    return int(bool(found or artifacts))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="canary", description=__doc__)
    parser.add_argument("command", choices=["plant", "search"])
    args = parser.parse_args(argv)
    if args.command == "plant":
        return plant(FIXTURE, os.environ, sys.stdout)
    return search(os.environ, sys.stdout)


if __name__ == "__main__":
    sys.exit(main())
