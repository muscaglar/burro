"""Settings, loading and the parts the routes rest on."""

import ast
import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import burro_api
import pytest
import uvicorn
from burro_api.app import deps_from
from burro_api.calls import (
    KEEP_DAYS,
    Caller,
    CallRecord,
    CallStatus,
    Endpoint,
    InMemoryCallLog,
)
from burro_api.claude import ClaudeInterpreter
from burro_api.cli import main
from burro_api.errors import KNOWN_NAMES, MESSAGES, path_of
from burro_api.loading import IGNORED, load_release
from burro_api.settings import DEFAULT_MODEL_ID, DEFAULT_ORIGINS, SYNTHETIC_FIXTURE, Settings
from burro_api.stores import InMemoryShareStore, StoredShare
from burro_api.wire import ErrorCode
from burro_core import RuleInterpreter
from burro_core.release import ReleaseError
from pydantic import ValidationError

from .support import CANARY, NOW, renter

SOURCE = Path(burro_api.__file__).parent


def call(number: int, at: str = "2026-09-23T12:00:00Z") -> CallRecord:
    return CallRecord(
        call_id=f"11111111-1111-4111-8111-{number:012d}",
        at=at,
        endpoint=Endpoint.INTERPRET,
        interpreter=Caller.RULE,
        model="",
        status=CallStatus.OK,
        degraded=False,
        input_tokens=0,
        output_tokens=0,
        cache_read_tokens=0,
        latency_ms=1,
        release_id="syn-2026-09-23-01",
        engine_version="1.0.0",
    )


# Settings.


def test_with_nothing_set_the_service_runs_on_the_synthetic_release_with_the_rules():
    settings = Settings.from_env({})

    assert settings.release_dir == SYNTHETIC_FIXTURE and SYNTHETIC_FIXTURE.is_dir()
    assert settings.model_id == DEFAULT_MODEL_ID and settings.model_timeout_s == 6
    assert settings.model_key_present is False
    # The local machine only, unless whoever deploys it says otherwise.
    assert (settings.host, settings.port) == ("127.0.0.1", 8000)
    # And a browser only from the web app as it runs on this machine.
    assert settings.allowed_origins == DEFAULT_ORIGINS == ("http://localhost:3000",)


def test_the_origins_a_browser_may_call_from_are_a_list_in_a_setting():
    listed = "https://burro.example, http://localhost:3000 ,https://staging.burro.example:8443"
    settings = Settings.from_env({"BURRO_ALLOWED_ORIGINS": listed})

    assert settings.allowed_origins == (
        "https://burro.example",
        "http://localhost:3000",
        "https://staging.burro.example:8443",
    )
    assert deps_from(settings).allowed_origins == settings.allowed_origins
    # Left empty, it is the default and never every origin.
    assert Settings.from_env({"BURRO_ALLOWED_ORIGINS": " "}).allowed_origins == DEFAULT_ORIGINS


@pytest.mark.parametrize(
    "listed",
    [
        "*",
        "https://*.burro.example",
        "null",
        "burro.example",
        "https://burro.example/",
        "https://burro.example/app",
        "https://burro.example,",
        "ftp://burro.example",
        "https://burro.example https://other.example",
        # As no browser would send it, so it would match nothing.
        "https://Burro.example",
        "HTTPS://burro.example",
        f"https://{CANARY} example",
    ],
)
def test_an_origin_is_a_scheme_and_a_host_and_never_a_pattern(listed: str):
    with pytest.raises(ValidationError) as refused:
        Settings.from_env({"BURRO_ALLOWED_ORIGINS": listed})

    assert CANARY not in str(refused.value)


@pytest.mark.parametrize(
    "listed",
    [
        # The checker's six: what no browser sends, so what would match nothing.
        "https://burro.example:443",
        "http://burro.example:80",
        "https://burro.example:0",
        "https://burro.example:99999",
        "https://-.",
        "https://burro..example",
        # A port is written as a browser writes it.
        "https://burro.example:65536",
        "https://burro.example:08443",
        "http://localhost:03000",
        "https://burro.example:",
        # A host is labels with a point between them, and a label is letters,
        # digits and hyphens, with a letter or a digit at each end.
        "https://.burro.example",
        "https://burro.example.",
        "https://.",
        "https://-burro.example",
        "https://burro-.example",
        "https://burro.-example",
        f"https://{'a' * 64}.example",
        f"https://{'.'.join(['a' * 60] * 5)}",
        # One that is right does not excuse one that is wrong.
        "http://localhost:3000,https://burro.example:443",
    ],
)
def test_an_origin_that_no_browser_would_send_is_refused_when_the_service_starts(listed: str):
    with pytest.raises(ValidationError) as refused:
        Settings.from_env({"BURRO_ALLOWED_ORIGINS": listed})

    # What was set may be an address nobody else should learn of.
    assert "burro" not in str(refused.value) and "localhost" not in str(refused.value)


@pytest.mark.parametrize(
    "listed",
    [
        "http://localhost:3000",
        "https://burro.example",
        "https://burro.example:8443",
        "http://burro.example:443",
        "https://burro.example:80",
        "http://127.0.0.1:1",
        "https://a.b-c.d1.example:65535",
        "https://xn--brr-hoa.example",
        f"https://{'a' * 63}.example",
    ],
)
def test_an_origin_as_a_browser_sends_it_is_taken(listed: str):
    assert Settings.from_env({"BURRO_ALLOWED_ORIGINS": listed}).allowed_origins == (listed,)


def test_settings_are_read_from_the_environment():
    settings = Settings.from_env(
        {
            "BURRO_RELEASE_DIR": "/srv/releases/lon-2027-01-05-01",
            "BURRO_MODEL_ID": "claude-sonnet-5",
            "BURRO_MODEL_TIMEOUT_S": "2.5",
            "BURRO_PORT": "9000",
            "ANTHROPIC_API_KEY": "a-test-key-that-opens-nothing",
        }
    )

    assert settings.release_dir == Path("/srv/releases/lon-2027-01-05-01")
    assert (settings.model_id, settings.model_timeout_s) == ("claude-sonnet-5", 2.5)
    assert settings.port == 9000 and settings.model_key_present is True
    # Whether there is a key is known. The key is not kept.
    assert "a-test-key" not in settings.model_dump_json()
    assert "a-test-key" not in repr(settings)


@pytest.mark.parametrize(
    "env",
    [
        {"BURRO_PORT": "http"},
        {"BURRO_PORT": "0"},
        {"BURRO_MODEL_TIMEOUT_S": "-1"},
        {"BURRO_MODEL_ID": f"a model called {CANARY}"},
    ],
)
def test_a_setting_that_is_not_in_the_form_it_needs_is_refused(env: dict[str, str]):
    with pytest.raises(ValidationError) as refused:
        Settings.from_env(env)

    assert CANARY not in str(refused.value)


@pytest.mark.parametrize("key", ["", "   "])
def test_an_empty_key_is_no_key(key: str):
    assert Settings.from_env({"ANTHROPIC_API_KEY": key}).model_key_present is False


def test_the_model_is_asked_only_when_a_key_is_present(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a-test-key-that-opens-nothing")
    for other in ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE", "ANTHROPIC_BASE_URL"):
        monkeypatch.delenv(other, raising=False)

    with_key = deps_from(Settings.from_env({"ANTHROPIC_API_KEY": "present"}))
    without = deps_from(Settings.from_env({}))

    assert isinstance(with_key.interpreter, ClaudeInterpreter)
    assert with_key.model_id == DEFAULT_MODEL_ID and with_key.model_timeout_s == 6
    assert isinstance(without.interpreter, RuleInterpreter) and without.model_id == ""


def imports_of(path: Path) -> list[tuple[str, bool]]:
    """Each module a file imports, and whether it does so as the file is loaded."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    at_the_top = {id(node) for node in tree.body}
    found: list[tuple[str, bool]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [(alias.name, id(node) in at_the_top) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            found.append((node.module or "", id(node) in at_the_top))
    return found


def test_only_one_module_imports_the_providers_sdk_and_nothing_loads_it_unasked():
    modules = sorted(SOURCE.rglob("*.py"))
    assert len(modules) > 15

    for module in modules:
        for name, at_the_top in imports_of(module):
            if name.split(".")[0] == "anthropic":
                assert module.name == "claude_sdk.py", module
            if name == "burro_api.claude_sdk":
                # Inside a function, so a service with no key never loads the SDK.
                assert module.name == "app.py" and not at_the_top, module
            # The pipeline and the API never import each other. They meet at the release.
            assert name.split(".")[0] != "burro_pipeline", module


# Loading.


def test_a_release_that_has_been_changed_is_refused(tmp_path: Path):
    folder = tmp_path / SYNTHETIC_FIXTURE.name
    folder.mkdir()
    for file in SYNTHETIC_FIXTURE.iterdir():
        (folder / file.name).write_bytes(file.read_bytes())
    assert load_release(folder).manifest.release_id == SYNTHETIC_FIXTURE.name

    cost = folder / "cost.json"
    cost.write_bytes(cost.read_bytes().replace(b"1", b"2", 1))
    with pytest.raises(ReleaseError) as refused:
        load_release(folder)
    assert (refused.value.file, refused.value.rule) == ("cost.json", "files_match_manifest")


def copy_of_the_fixture(tmp_path: Path) -> Path:
    folder = tmp_path / SYNTHETIC_FIXTURE.name
    shutil.copytree(SYNTHETIC_FIXTURE, folder, ignore=shutil.ignore_patterns(IGNORED))
    return folder


def test_a_file_the_finder_leaves_behind_does_not_stop_the_service(tmp_path: Path):
    folder = copy_of_the_fixture(tmp_path)
    # What a Mac leaves in a folder that has been opened in a window. It is not JSON.
    (folder / ".DS_Store").write_bytes(b"\x00\x00\x00\x01Bud1\x00 not a release file")

    loaded = load_release(folder)

    assert IGNORED == ".DS_Store"
    assert loaded.manifest.release_id == SYNTHETIC_FIXTURE.name
    assert loaded == load_release(SYNTHETIC_FIXTURE)
    # The service reads what `burro-release check` reads, and starts on it.
    assert deps_from(Settings.from_env({"BURRO_RELEASE_DIR": str(folder)})).release == loaded


@pytest.mark.parametrize(
    "name",
    [
        ".ds_store",
        ".DS_Store.json",
        "DS_Store",
        "._.DS_Store",
        "._manifest.json",
        "Thumbs.db",
        "desktop.ini",
        ".gitkeep",
        ".hidden",
        "notes.txt",
        "extra.json",
    ],
)
def test_every_other_stray_file_is_still_refused(tmp_path: Path, name: str):
    folder = copy_of_the_fixture(tmp_path)
    (folder / name).write_bytes(b"{}")

    with pytest.raises(ReleaseError) as refused:
        load_release(folder)

    assert (refused.value.file, refused.value.rule) == (name, "files_match_manifest")


def test_a_folder_by_the_name_of_the_file_the_finder_leaves_is_refused(tmp_path: Path):
    folder = copy_of_the_fixture(tmp_path)
    (folder / ".DS_Store").mkdir()

    with pytest.raises(ReleaseError) as refused:
        load_release(folder)

    assert (refused.value.file, refused.value.rule) == (".DS_Store", "file_is_readable")


def test_a_folder_that_is_not_a_release_is_refused(tmp_path: Path):
    with pytest.raises(ReleaseError) as missing:
        load_release(tmp_path / "nothing-here")
    (tmp_path / "manifest.json").mkdir()
    with pytest.raises(ReleaseError) as unreadable:
        load_release(tmp_path)

    assert missing.value.rule == "folder_is_readable"
    assert (unreadable.value.file, unreadable.value.rule) == ("manifest.json", "file_is_readable")


def test_the_command_line_says_why_it_could_not_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    changed = tmp_path / SYNTHETIC_FIXTURE.name
    shutil.copytree(SYNTHETIC_FIXTURE, changed)
    (changed / "travel.json").unlink()

    monkeypatch.setenv("BURRO_RELEASE_DIR", str(tmp_path / "nothing-here"))
    assert main(["serve"]) == 2
    monkeypatch.setenv("BURRO_RELEASE_DIR", str(changed))
    assert main(["serve"]) == 2
    monkeypatch.setenv("BURRO_PORT", "not a port")
    assert main(["serve"]) == 2

    out, err = capsys.readouterr()
    assert out == ""
    # The folder, the file and the rule, so that whoever starts it knows where to look.
    assert err.splitlines() == [
        f"error: the release could not be loaded: {tmp_path / 'nothing-here'} [folder_is_readable]",
        f"error: the release could not be loaded: {changed}: travel.json [files_match_manifest]",
        "error: a setting in the environment is not in the form it needs",
    ]


def test_the_server_is_run_with_its_own_access_log_switched_off(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    run: list[dict[str, Any]] = []

    def cannot_listen(app: object, **how: Any) -> None:
        run.append(how)
        raise SystemExit(3)

    monkeypatch.setattr(uvicorn, "run", cannot_listen)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("BURRO_PORT", "8123")
    assert main(["serve"]) == 2

    [how] = run
    # The server's own access log would write the path, and a path can hold a
    # share id. And it must not set logging up again, over the JSON.
    assert how["access_log"] is False and how["log_config"] is None
    assert (how["host"], how["port"]) == ("127.0.0.1", 8123)
    out, err = capsys.readouterr()
    assert err == "error: could not listen on 127.0.0.1:8123\n"
    [line] = [json.loads(row) for row in out.splitlines()]
    assert (line["event"], line["interpreter"], line["synthetic"]) == ("starting", "rule", True)


def test_the_command_line_writes_the_document_that_is_committed(tmp_path: Path):
    committed = Path(__file__).resolve().parents[3] / "contracts" / "openapi.json"
    out = tmp_path / "contracts" / "openapi.json"

    assert main(["openapi", "--out", str(out)]) == 0

    assert out.read_bytes() == committed.read_bytes()
    assert json.loads(out.read_text())["info"]["title"] == "Burro API"


# The stores.


def share(number: int) -> StoredShare:
    return StoredShare(
        share_id=f"share{number:017d}",
        spec=renter(),
        coarsened=False,
        original_release_id="syn-2026-09-23-01",
        created_at="2026-09-23T12:00:00Z",
    )


def test_the_share_store_lets_the_oldest_go_when_it_is_full():
    store = InMemoryShareStore(keep_at_most=3)
    for number in range(1, 6):
        store.put(share(number))

    assert [store.get(share(n).share_id) is not None for n in range(1, 6)] == [
        False,
        False,
        True,
        True,
        True,
    ]
    assert store.get("no-such-share") is None


def test_a_call_record_is_kept_for_thirty_days_and_no_longer():
    log = InMemoryCallLog()
    log.add(call(1, "2026-08-23T12:00:00Z"))
    log.add(call(2, "2026-08-24T12:00:01Z"))
    log.add(call(3))

    assert KEEP_DAYS == 30
    assert [r.call_id[-1] for r in log.records(NOW)] == ["2", "3"]
    assert [r.call_id[-1] for r in log.records(NOW + timedelta(days=31))] == []


def test_a_call_record_older_than_thirty_days_is_gone_after_the_next_add():
    log = InMemoryCallLog()
    log.add(call(1, "2026-08-01T12:00:00Z"))
    log.add(call(2, "2026-08-24T12:00:01Z"))
    log.add(call(3, "2026-09-23T12:00:00Z"))

    # Read as of a day when the first was a day old, so that it is the adding
    # that let it go and not the reading. Nothing in the service reads.
    young = datetime(2026, 8, 2, 12, 0, 0, tzinfo=UTC)
    assert [r.call_id[-1] for r in log.records(young)] == ["2", "3"]


def test_a_record_with_an_earlier_time_lets_nothing_go_that_is_still_young():
    log = InMemoryCallLog()
    log.add(call(1, "2026-09-20T12:00:00Z"))
    # A clock that was put back. What is kept is measured from the latest time seen.
    log.add(call(2, "2026-07-01T12:00:00Z"))
    log.add(call(3, "2026-09-23T12:00:00Z"))

    assert [r.call_id[-1] for r in log.records(NOW)] == ["1", "3"]


def test_a_record_out_of_the_order_of_time_is_gone_when_it_is_too_old():
    log = InMemoryCallLog()
    log.add(call(1, "2026-08-10T12:00:00Z"))
    # A clock that was put back, so the older record stands behind the younger.
    log.add(call(2, "2026-08-05T12:00:00Z"))
    log.add(call(3, "2026-09-05T12:00:00Z"))

    # On the fifth of September the second is 31 days old, and the first 26.
    young = datetime(2026, 8, 6, 12, 0, 0, tzinfo=UTC)
    assert [r.call_id[-1] for r in log.records(young)] == ["1", "3"]


def test_every_record_that_is_too_old_is_let_go_wherever_it_stands():
    log = InMemoryCallLog()
    days = [20, 1, 19, 2, 18, 3, 25, 4]
    for number, day in enumerate(days, start=1):
        log.add(call(number, f"2026-08-{day:02d}T12:00:00Z"))
    log.add(call(9, "2026-09-18T12:00:00Z"))

    # Thirty days before the last is the nineteenth of August.
    young = datetime(2026, 8, 5, 12, 0, 0, tzinfo=UTC)
    assert [r.call_id[-1] for r in log.records(young)] == ["1", "3", "7", "9"]
    # And reading lets go of what has grown too old since, wherever it stands.
    later = datetime(2026, 9, 19, 12, 0, 1, tzinfo=UTC)
    assert [r.call_id[-1] for r in log.records(later)] == ["7", "9"]
    assert [r.call_id[-1] for r in log.records(young)] == ["7", "9"]


def test_the_call_log_cannot_grow_without_end():
    log = InMemoryCallLog(keep_at_most=100)
    for number in range(250):
        log.add(call(number))

    kept = log.records(NOW)
    assert len(kept) == 100 and kept[0].call_id.endswith("150")


# Errors.


def test_every_error_has_fixed_words_that_name_nothing_that_was_sent():
    assert set(MESSAGES) == set(ErrorCode)
    for message in MESSAGES.values():
        assert "{" not in message and "%" not in message and message.endswith(".")


@pytest.mark.parametrize(
    ("loc", "path"),
    [
        (("body", "spec", "commutes", 0, "max_minutes"), "spec.commutes[0].max_minutes"),
        (
            ("body", "operations", "weight_ops", 12, "feature_id"),
            "operations.weight_ops[12].feature_id",
        ),
        (("body",), ""),
        (("path", "share_id"), "share_id"),
        # A key the sender chose, and the name of a branch of a union.
        (("body", "spec", CANARY), "spec"),
        (("body", CANARY, "spec", CANARY, 3), "spec[3]"),
        (("body", "spec", "budget", "amount", "int"), "spec.budget.amount"),
        (("body", "spec", "function-after[_in_order(), tuple]", 1), "spec[1]"),
        (("body", "text", True, 2.5, None), "text"),
    ],
)
def test_a_path_is_made_of_our_own_field_names_and_positions(loc: tuple[Any, ...], path: str):
    assert path_of(loc) == path
    assert CANARY not in KNOWN_NAMES and "text" in KNOWN_NAMES and "feature_id" in KNOWN_NAMES
