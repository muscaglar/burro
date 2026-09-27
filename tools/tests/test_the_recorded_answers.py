"""The answers the clients are tested on, held to what the service gives today.

`make web-record` asks the service and writes what it answers under
`apps/web/test/recorded`. Every test of the website runs on those files, and the app's run
on a copy of them. A check holds each file to the contract, and the app's copy to the
website's, and neither asks the service again. So a change to the ranking that nobody
recorded would leave every test passing, on answers the service no longer gives.

Here the recorder is run as `make web-record` runs it, but that it writes to a folder of
the test's own, and what is committed is held to what it wrote, byte for byte.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
RECORDED = ROOT / "apps" / "web" / "test" / "recorded"


def the_recorder() -> ModuleType:
    """The recorder, read where the test runs: every process that runs tests reads this
    file to learn which tests it holds, and one of them runs this one."""
    spec = importlib.util.spec_from_file_location(
        "the_recorder", ROOT / "apps" / "web" / "test" / "record.py"
    )
    assert spec is not None and spec.loader is not None
    record = importlib.util.module_from_spec(spec)
    sys.modules["the_recorder"] = record
    spec.loader.exec_module(record)
    return record


def held(folder: Path) -> dict[str, bytes]:
    """Every file under a folder, by its path from there."""
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


# The recorder sets logging up as the service does, for the whole process.
@pytest.mark.usefixtures("logging_as_it_was")
def test_what_is_recorded_is_what_the_service_answers_today(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    again = tmp_path / "recorded"
    record = the_recorder()
    monkeypatch.setattr(record, "OUT", again)

    assert record.main() == 0, capsys.readouterr().err
    now, committed = held(again), held(RECORDED)

    to_do = "Run `make web-record`, then the checks of the website and of the app."
    assert sorted(set(committed) - set(now)) == [], f"recorded, and no longer asked. {to_do}"
    assert sorted(set(now) - set(committed)) == [], f"asked, and not recorded. {to_do}"
    moved = sorted(name for name, written in now.items() if committed[name] != written)
    assert moved == [], f"the service answers otherwise than is recorded. {to_do}"
    assert len(committed) > 200
