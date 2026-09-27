"""The guide to deployment, held to what is said of a release of another catalogue.

A guide goes stale without a sound. Each test here reads deploy/README.md beside what it
speaks of, and fails when the two part.

A release is served only by code that holds the catalogue it was built with. Neither the
step that takes a release nor the build of the image can tell, so the first word of it is
in the log of the host, once the deploy is made, and that word is the name of a rule. So
the guide says what the line means where a person reads the log, and says before its steps
how to be told in words while nothing is deployed yet.
"""

import json
import os
import re
import shutil
from pathlib import Path

import pytest
import uvicorn
from burro_api import cli as service
from burro_api.settings import SYNTHETIC_FIXTURE
from burro_pipeline.release import cli as release

ROOT = Path(__file__).resolve().parents[2]
GUIDE = (ROOT / "deploy" / "README.md").read_text(encoding="utf-8")
LONDON = "## Serving a release of London"


def section(heading: str, within: str = GUIDE) -> str:
    """What stands under a heading, up to the next heading of its kind or of one above it."""
    marks = len(heading) - len(heading.lstrip("#"))
    after = within.split(f"\n{heading}\n", 1)[1]
    return re.split(rf"\n#{{1,{marks}}} ", after, maxsplit=1)[0]


def rows(text: str) -> list[list[str]]:
    """The rows of the first table of a text, but the row of names."""
    table = re.search(r"(?:^\|.*\n)+", text, re.MULTILINE)
    assert table is not None
    found = [row for row in table[0].splitlines() if not re.fullmatch(r"[|\s:-]+", row)]
    return [[cell.strip() for cell in row.strip().strip("|").split("|")] for row in found[1:]]


@pytest.fixture
def of_another_catalogue(tmp_path: Path) -> Path:
    """The made-up city, as a build under the catalogue before this one would have left it."""
    folder = tmp_path / SYNTHETIC_FIXTURE.name
    shutil.copytree(SYNTHETIC_FIXTURE, folder)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    manifest["catalogue_version"] -= 1
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return folder


@pytest.fixture
def the_log_says(
    of_another_catalogue: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    logging_as_it_was: None,
) -> str:
    """How the line ends that the service writes of such a release, after the folder.

    The service is started as `burro-api serve` starts it, with no setting of Burro's that
    the shell holds but the folder, and with nowhere to listen: a service that came as far
    as to listen would say that it could not.
    """

    def nowhere(*served: object, **how: object) -> None:
        raise SystemExit(3)

    for name in [name for name in os.environ if name.startswith("BURRO_")]:
        monkeypatch.delenv(name)
    monkeypatch.setenv("BURRO_RELEASE_DIR", str(of_another_catalogue))
    monkeypatch.setattr(uvicorn, "run", nowhere)

    assert service.main(["serve"]) == 2
    out, err = capsys.readouterr()
    before = f"error: the release could not be loaded: {of_another_catalogue}: "
    assert out == "" and err.startswith(before) and err.count("\n") == 1
    return err.removeprefix(before).strip()


def test_the_guide_says_what_the_log_means_where_a_release_is_of_another_catalogue(
    the_log_says: str,
):
    table = rows(section("### 2. The API, on Fly.io").split("fails its health check", 1)[1])
    [row] = [row for row in table if f"`{the_log_says}`" in row[0]]
    assert "`the release could not be loaded`" in row[0]
    assert "another catalogue" in row[1]
    # What to do: go back, and build London again.
    assert '"Going back to the release before"' in row[1]
    assert "(../docs/data-builds.md#before-the-service-is-deployed-again)" in row[1]
    # No row says of that line that the folder is at fault, which it is not.
    others = [each for each in table if each != row and "could not be loaded" in each[0]]
    assert [each[0] for each in others] == [
        "`the release could not be loaded`, with any other file and rule"
    ]


def test_the_guide_says_before_its_steps_how_to_be_told_before_anything_is_deployed(
    of_another_catalogue: Path, capsys: pytest.CaptureFixture[str]
):
    london = section(LONDON)
    [row] = [row for row in rows(section("### Before you start", london)) if "catalogue" in row[0]]
    assert "refuses any other as it starts" in row[1]
    # The command the guide gives says it in words, and ends as a failure does.
    [command] = re.findall(r"`uv run burro-release (check [^`]+)`", row[1])
    assert command == "check data/releases/served/ID"
    assert release.main(["check", str(of_another_catalogue)]) == 2
    said = "has a schema or catalogue version that this code does not read [versions_match]"
    assert capsys.readouterr().err.strip().endswith(f"manifest.json, at catalogue_version, {said}")
    # It is run on what step 2 took, before step 4 deploys it.
    steps = section("### The steps", london)
    assert "--out data/releases/served" in steps.split("4. **Deploy", 1)[0]


def test_neither_row_names_a_version_or_a_release_that_the_next_catalogue_makes_untrue():
    table = rows(section("### 2. The API, on Fly.io").split("fails its health check", 1)[1])
    before = rows(section("### Before you start", section(LONDON)))
    found = [row for row in (*table, *before) if "catalogue" in " ".join(row)]
    assert len(found) == 2
    for row in found:
        # The number of a step is one digit. The version of a catalogue, a day and the id
        # of a release are each more.
        assert not re.search(r"\d\d|lon-|syn-", " ".join(row)), row
