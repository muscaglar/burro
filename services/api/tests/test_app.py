"""Settings, loading and the parts the routes rest on."""

import ast
import hashlib
import io
import json
import logging
import re
import shutil
import subprocess
import sys
import tomllib
from dataclasses import MISSING, fields, replace
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
from burro_api.cli import main, serve
from burro_api.deps import Deps
from burro_api.errors import KNOWN_NAMES, MESSAGES, path_of
from burro_api.loading import IGNORED, load_release
from burro_api.logs import LOGGER, configure_logging
from burro_api.providers.base import Request, Response
from burro_api.providers.choose import BY_RULES, Refusal, choose, told_of
from burro_api.providers.interface import ModelError
from burro_api.providers.terms import SETTINGS, TERMS, WORDS_ALONE, Provider
from burro_api.reader import ModelInterpreter
from burro_api.settings import DEFAULT_ORIGINS, SYNTHETIC_FIXTURE, Settings
from burro_api.stores import InMemoryShareStore, StoredShare
from burro_api.wire import ErrorCode
from burro_core import RuleInterpreter
from burro_core.interpret import InterpretRequest
from burro_core.release import BUILD_FOLDER, EVIDENCE, HASHES, LOCK, MANIFEST, ReleaseError
from pydantic import ValidationError

from .support import (
    CANARY,
    NOW,
    FakeModelClient,
    logging_put_back,
    release,
    renter,
    searching,
)

SOURCE = Path(burro_api.__file__).parent
KEY_VARIABLES = sorted(terms.key_variable for terms in TERMS.values())
# The providers that may read what real people type. One of the four never may.
FOR_PEOPLE = [provider for provider in Provider if provider is not Provider.DEEPSEEK]
# Everything the chooser reads. A test that starts the service as the command
# line does clears them, so that it says the same whatever shell it runs in.
CHOSEN_BY = ("BURRO_MODEL_PROVIDER", "BURRO_MODEL_TERMS_ACCEPTED", "BURRO_MODEL_ID", *KEY_VARIABLES)


def never_sends(request: Request, timeout_s: float) -> Response:
    raise AssertionError("choosing a provider makes no call")


def unheard(provider: Provider | None, refusal: Refusal) -> None:
    """Takes the warning and writes no line."""


def runs_nothing(app: object, **how: object) -> None:
    """Stands in for the server, and returns as one that was stopped does."""


def call(number: int, at: str = "2026-09-23T12:00:00Z") -> CallRecord:
    return CallRecord(
        call_id=f"11111111-1111-4111-8111-{number:012d}",
        at=at,
        endpoint=Endpoint.INTERPRET,
        interpreter=Caller.RULE,
        provider="",
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
    assert (settings.model_timeout_s, settings.model_max_tokens) == (6, 2048)
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
            "BURRO_MODEL_TIMEOUT_S": "2.5",
            "BURRO_MODEL_MAX_TOKENS": "1024",
            "BURRO_PORT": "9000",
        }
    )

    assert settings.release_dir == Path("/srv/releases/lon-2027-01-05-01")
    assert (settings.model_timeout_s, settings.model_max_tokens) == (2.5, 1024)
    assert settings.port == 9000


def test_the_settings_hold_nothing_of_a_provider():
    # Which provider, its key, its terms and its model are the chooser's. The
    # settings hold none of them, so none can be shown with the settings.
    env = {
        "BURRO_MODEL_PROVIDER": "gemini",
        "BURRO_MODEL_TERMS_ACCEPTED": "gemini",
        "BURRO_MODEL_ID": "gemini-3.5-flash-lite",
        **{variable: f"a-test-key-{CANARY}" for variable in KEY_VARIABLES},
    }

    settings = Settings.from_env(env)

    assert settings == Settings.from_env({})
    assert not [name for name in Settings.model_fields if "key" in name or name == "model_id"]
    assert CANARY not in settings.model_dump_json() and CANARY not in repr(settings)


@pytest.mark.parametrize(
    "env",
    [
        {"BURRO_PORT": "http"},
        {"BURRO_PORT": "0"},
        {"BURRO_MODEL_TIMEOUT_S": "-1"},
        {"BURRO_MODEL_MAX_TOKENS": f"as many as {CANARY}"},
    ],
)
def test_a_setting_that_is_not_in_the_form_it_needs_is_refused(env: dict[str, str]):
    with pytest.raises(ValidationError) as refused:
        Settings.from_env(env)

    assert CANARY not in str(refused.value)


def model_reads(deps: Deps) -> bool:
    return isinstance(deps.interpreter, ModelInterpreter)


def test_with_no_choice_given_the_rules_read_and_people_are_told_so():
    deps = deps_from(Settings.from_env({}))

    assert isinstance(deps.interpreter, RuleInterpreter)
    assert (deps.told, deps.model_id) == (BY_RULES, "")


@pytest.mark.parametrize("variable", KEY_VARIABLES)
def test_a_key_alone_turns_nothing_on(variable: str):
    env = {variable: "a-test-key-that-opens-nothing"}

    deps = deps_from(Settings.from_env(env), choose(env))

    assert isinstance(deps.interpreter, RuleInterpreter)
    assert (deps.told, deps.model_id) == (BY_RULES, "")


@pytest.mark.parametrize("provider", FOR_PEOPLE, ids=lambda provider: provider.value)
@pytest.mark.parametrize("missing", ["provider", "key", "terms", "none"])
def test_a_provider_reads_only_when_it_is_named_has_a_key_and_its_terms_are_accepted(
    provider: Provider, missing: str
):
    terms = TERMS[provider]
    env = {
        "provider": {"BURRO_MODEL_PROVIDER": provider.value},
        "key": {terms.key_variable: "a-test-key-that-opens-nothing"},
        "terms": {"BURRO_MODEL_TERMS_ACCEPTED": provider.value},
    }
    set_ = {k: v for name, part in env.items() if name != missing for k, v in part.items()}

    deps = deps_from(Settings.from_env(set_), choose(set_, send=never_sends))

    assert model_reads(deps) is (missing == "none")
    if missing == "none":
        assert (deps.told.model_reads, deps.told.provider) == (True, provider.value)
        assert deps.told.notice == terms.notice(with_settings=False)
        assert deps.model_id == terms.model
    else:
        assert (deps.told, deps.model_id) == (BY_RULES, "")


def test_the_provider_that_may_not_read_what_people_type_never_reads_in_the_service():
    terms = TERMS[Provider.DEEPSEEK]
    env = {
        "BURRO_MODEL_PROVIDER": "deepseek",
        terms.key_variable: "a-test-key-that-opens-nothing",
        "BURRO_MODEL_TERMS_ACCEPTED": "deepseek",
    }

    choice = choose(env, send=never_sends, warn=unheard)

    assert choice.refusal is Refusal.NOT_FOR_PEOPLE
    deps = deps_from(Settings.from_env(env), choice)
    assert not model_reads(deps) and (deps.told, deps.model_id) == (BY_RULES, "")


def test_the_reader_is_given_the_limits_of_the_settings_and_the_model_of_the_choice():
    env = {
        "BURRO_MODEL_PROVIDER": "gemini",
        "GEMINI_API_KEY": "a-test-key-that-opens-nothing",
        "BURRO_MODEL_TERMS_ACCEPTED": "gemini",
        "BURRO_MODEL_ID": "gemini-3.1-flash-lite",
        "BURRO_MODEL_TIMEOUT_S": "2.5",
        "BURRO_MODEL_MAX_TOKENS": "1024",
    }
    sent: list[tuple[Request, float]] = []

    def send(request: Request, timeout_s: float) -> Response:
        sent.append((request, timeout_s))
        return Response(500)

    deps = deps_from(Settings.from_env(env), choose(env, send=send))
    with pytest.raises(ModelError):
        deps.interpreter.interpret(InterpretRequest("leafy, honestly", renter(), release()))

    [(request, timeout_s)] = sent
    assert (deps.model_id, deps.model_timeout_s, timeout_s) == ("gemini-3.1-flash-lite", 2.5, 2.5)
    assert request.path == "/v1beta/models/gemini-3.1-flash-lite:generateContent"
    assert json.loads(request.body)["generationConfig"]["maxOutputTokens"] == 1024


@pytest.mark.parametrize(("set_to", "sent"), [(None, False), ("no", False), ("yes", True)])
def test_the_settings_are_sent_only_where_the_service_is_set_to_send_them(
    set_to: str | None, sent: bool
):
    env = {
        "BURRO_MODEL_PROVIDER": "gemini",
        "GEMINI_API_KEY": "a-test-key-that-opens-nothing",
        "BURRO_MODEL_TERMS_ACCEPTED": "gemini",
    } | ({} if set_to is None else {"BURRO_MODEL_SENDS_SETTINGS": set_to})
    requests: list[Request] = []

    def send(request: Request, timeout_s: float) -> Response:
        requests.append(request)
        return Response(500)

    deps = deps_from(Settings.from_env(env), choose(env, send=send))
    with pytest.raises(ModelError):
        deps.interpreter.interpret(InterpretRequest("leafy, honestly", searching(), release()))

    [request] = requests
    turn = json.loads(json.loads(request.body)["contents"][0]["parts"][0]["text"])
    # What is sent is what people are told is sent, because both are the choice's.
    assert ("spec" in turn, deps.told.settings_sent) == (sent, sent)
    assert (SETTINGS in deps.told.notice, WORDS_ALONE in deps.told.notice) == (sent, not sent)


def test_what_the_service_depends_on_cannot_tell_people_other_than_who_reads():
    by_rules = deps_from(Settings.from_env({}))
    told = told_of(TERMS[Provider.GEMINI], with_settings=False)
    a_model = ModelInterpreter(FakeModelClient({}), "a-model", 512, 2.5)

    # A default would be "not sent to a language model", said of a service that sends.
    assert "told" in {held.name for held in fields(Deps) if held.default is MISSING}
    with pytest.raises(ValueError, match="does not fit who reads"):
        replace(by_rules, interpreter=a_model)
    with pytest.raises(ValueError, match="does not fit who reads"):
        replace(by_rules, told=told)
    assert replace(by_rules, interpreter=a_model, told=told).told.model_reads


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


# Every provider's own library, and what each is built on. The adapters make one HTTPS
# call each with the standard library, so the service needs none of them.
PROVIDERS_LIBRARIES = {
    "anthropic",
    "openai",
    "google",
    "genai",
    "vertexai",
    "deepseek",
    "litellm",
    "langchain",
    "httpx",
    "httpx2",
    "httpcore",
    "requests",
    "urllib3",
    "aiohttp",
}


def test_nothing_in_the_service_imports_a_providers_library():
    modules = sorted(SOURCE.rglob("*.py"))
    assert len(modules) > 15

    for module in modules:
        for name, _ in imports_of(module):
            # `burro_api.providers.anthropic` is ours: the adapter, named for its provider.
            ours = name.startswith("burro_api")
            assert ours or name.split(".")[0] not in PROVIDERS_LIBRARIES, (module, name)
            # The pipeline and the API never import each other. They meet at the release.
            assert name.split(".")[0] != "burro_pipeline", module
    assert not (SOURCE / "claude_sdk.py").exists()


def test_the_service_depends_on_no_providers_library():
    manifest = tomllib.loads((SOURCE.parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    needed = [
        re.split(r"[<>=~! ;\[]", line, maxsplit=1)[0]
        for line in manifest["project"]["dependencies"]
    ]

    assert needed == ["burro-core", "fastapi", "uvicorn"]
    assert not PROVIDERS_LIBRARIES & set(needed)


def test_starting_the_service_loads_no_providers_library():
    code = (
        "import sys\n"
        "from burro_api.app import create_app, deps_from\n"
        "from burro_api.providers.choose import choose\n"
        "from burro_api.settings import Settings\n"
        "create_app(deps_from(Settings.from_env({}), choose({})))\n"
        "loaded = {name.split('.')[0] for name in sys.modules}\n"
        f"unwanted = {sorted(PROVIDERS_LIBRARIES - {'google'})!r}\n"
        "sys.exit(', '.join(sorted(loaded & set(unwanted))) or 0)\n"
    )

    done = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=60, check=False
    )

    assert (done.returncode, done.stderr) == (0, "")


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


# A release that is not made up is served only with what it was built with.

REAL_ID = "lon-2026-09-23-01"


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def a_release_that_is_not_made_up(tmp_path: Path) -> Path:
    """The synthetic release under the ids and the flag of a real one, written as a folder.

    Nothing in it is real. It is the only way this build has of making a
    release that says it is not made up. It stands alone: nothing is beside it.
    It carries Gritty, as a release of London does.
    """
    text = json.dumps(release().documents()).replace("syn-", "lon-")
    found: dict[str, Any] = json.loads(text.replace('"synthetic"', '"made-up-survey"'))
    manifest = found.pop(MANIFEST)
    manifest.pop("made-up-survey")
    manifest.update(synthetic=False, city="lon", seed=None)
    manifest["sources"][0]["attribution"] = "Contains made-up data."
    folder = tmp_path / REAL_ID
    folder.mkdir()
    files = {name: json.dumps(document).encode() for name, document in found.items()}
    manifest["files"] = [
        {"name": name, "sha256": sha256(content), "bytes": len(content)}
        for name, content in sorted(files.items())
    ]
    for name, content in (files | {MANIFEST: json.dumps(manifest).encode()}).items():
        (folder / name).write_bytes(content)
    return folder


def build_beside(folder: Path) -> Path:
    """What a build writes beside its release: evidence, a lock, and the hashes of the three.

    The service reads neither the evidence nor the lock. It holds their bytes
    to the hashes, so any bytes will do here.
    """
    beside = folder.with_name(f"{folder.name}{BUILD_FOLDER}")
    beside.mkdir()
    (beside / EVIDENCE).write_bytes(b'{"rows":[]}\n')
    (beside / LOCK).write_bytes(b'{"inputs":[]}\n')
    hashes = {
        "release_id": folder.name,
        "manifest_sha256": sha256((folder / MANIFEST).read_bytes()),
        "evidence_sha256": sha256((beside / EVIDENCE).read_bytes()),
        "lock_sha256": sha256((beside / LOCK).read_bytes()),
    }
    (beside / HASHES).write_text(json.dumps(hashes), encoding="utf-8")
    return beside


def not_loaded(folder: Path) -> tuple[str, str]:
    with pytest.raises(ReleaseError) as refused:
        load_release(folder)
    return refused.value.file, refused.value.rule


def test_a_release_that_is_not_made_up_is_served_with_its_build_beside_it(tmp_path: Path):
    folder = a_release_that_is_not_made_up(tmp_path)
    build_beside(folder)
    loaded = load_release(folder)
    assert (loaded.manifest.release_id, loaded.manifest.synthetic) == (REAL_ID, False)
    assert deps_from(Settings.from_env({"BURRO_RELEASE_DIR": str(folder)})).release == loaded


def test_a_release_that_is_not_made_up_is_not_served_with_nothing_beside_it(tmp_path: Path):
    """The service once served such a release. A figure with no evidence is not a figure."""
    folder = a_release_that_is_not_made_up(tmp_path)
    assert not_loaded(folder) == (HASHES, "real_release_has_its_build")


@pytest.mark.parametrize("missing", [HASHES, EVIDENCE, LOCK])
def test_a_release_that_lacks_a_file_of_its_build_is_not_served(tmp_path: Path, missing: str):
    folder = a_release_that_is_not_made_up(tmp_path)
    (build_beside(folder) / missing).unlink()
    assert not_loaded(folder) == (missing, "real_release_has_its_build")


def test_a_release_changed_after_it_was_built_is_not_served(tmp_path: Path):
    """The manifest was made to agree with the file that was changed. The hashes do not."""
    folder = a_release_that_is_not_made_up(tmp_path)
    build_beside(folder)
    features = json.loads((folder / "features.json").read_bytes())
    # The highest figure of a measure, raised: it stands where it stood among the others, so
    # core still reads the release, and only the hashes of the build can tell.
    density = [row for row in features["rows"] if row["feature_id"] == "homes_density"]
    figure = max((row for row in density if row["value"] is not None), key=lambda r: r["value"])
    figure["value"] = figure["value"] + 20
    changed = json.dumps(features).encode()
    (folder / "features.json").write_bytes(changed)
    manifest = json.loads((folder / MANIFEST).read_bytes())
    for entry in manifest["files"]:
        if entry["name"] == "features.json":
            entry.update(sha256=sha256(changed), bytes=len(changed))
    (folder / MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
    assert not_loaded(folder) == (MANIFEST, "build_is_as_it_was_written")


@pytest.mark.parametrize("changed", [EVIDENCE, LOCK])
def test_evidence_or_a_lock_changed_after_the_build_is_not_served(tmp_path: Path, changed: str):
    folder = a_release_that_is_not_made_up(tmp_path)
    beside = build_beside(folder)
    (beside / changed).write_bytes((beside / changed).read_bytes() + b" ")
    assert not_loaded(folder) == (changed, "build_is_as_it_was_written")


def test_the_command_line_says_that_a_release_has_no_build_beside_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    folder = a_release_that_is_not_made_up(tmp_path)
    monkeypatch.setenv("BURRO_RELEASE_DIR", str(folder))
    assert main(["serve"]) == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert err.splitlines() == [
        f"error: the release could not be loaded: {folder}: {HASHES} [real_release_has_its_build]"
    ]


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


def rewritten(folder: Path, name: str, change: Any) -> None:
    """One file of a release with a row changed, and the manifest told of its new bytes.

    So the folder is whole and its checksums agree: what is wrong with it is
    what the figures say, which only the rules of core can find.
    """
    held = json.loads((folder / name).read_text(encoding="utf-8"))
    change(held["rows"])
    written = json.dumps(held, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    (folder / name).write_text(written, encoding="utf-8")
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    [entry] = [file for file in manifest["files"] if file["name"] == name]
    entry["sha256"] = hashlib.sha256(written.encode()).hexdigest()
    entry["bytes"] = len(written.encode())
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def placed(rows: list[dict[str, Any]], held: str) -> dict[str, Any]:
    return next(row for row in rows if row[held] is not None and 5 < row[held] < 95)


def another_score(rows: list[dict[str, Any]]) -> None:
    placed(rows, "score")["score"] += 1


def another_raw(rows: list[dict[str, Any]]) -> None:
    # Too little to move a band or a score, and more than a release is written to.
    placed(rows, "score")["raw"] += 0.00001


def another_percentile(rows: list[dict[str, Any]]) -> None:
    placed(rows, "percentile")["percentile"] += 1


@pytest.mark.parametrize(
    ("name", "change", "rule"),
    [
        ("features.json", another_percentile, "percentiles_match_values"),
        ("tags.json", another_raw, "raw_matches_recipe"),
        ("tags.json", another_score, "scores_match_raw"),
    ],
)
def test_the_service_does_not_start_on_a_release_that_ranks_on_what_it_does_not_show(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    name: str,
    change: Any,
    rule: str,
):
    folder = copy_of_the_fixture(tmp_path)
    rewritten(folder, name, change)

    monkeypatch.setenv("BURRO_RELEASE_DIR", str(folder))
    assert main(["serve"]) == 2

    out, err = capsys.readouterr()
    # Every file is whole and every checksum agrees. It is the figures that do not.
    # The folder, the file, the row and the rule are named, and never a figure.
    assert out == ""
    said = err.removeprefix(f"error: the release could not be loaded: {folder}: ")
    assert re.fullmatch(rf"{re.escape(name)}, at rows\[\d+\] \[{rule}\]\n", said), said


def started(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], env: dict[str, str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    """How the server was run, every line written, and what was said, with `env` set."""
    run: list[dict[str, Any]] = []

    def cannot_listen(app: object, **how: Any) -> None:
        run.append(how)
        raise SystemExit(3)

    monkeypatch.setattr(uvicorn, "run", cannot_listen)
    for name, value in ({"BURRO_PORT": "8123"} | env).items():
        monkeypatch.setenv(name, value)
    assert main(["serve"]) == 2
    out, err = capsys.readouterr()
    return run, [json.loads(row) for row in out.splitlines()], err


def test_the_server_is_run_with_its_own_access_log_switched_off(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    run, lines, err = started(monkeypatch, capsys, {})

    [how] = run
    # The server's own access log would write the path, and a path can hold a
    # share id. And it must not set logging up again, over the JSON.
    assert how["access_log"] is False and how["log_config"] is None
    assert (how["host"], how["port"]) == ("127.0.0.1", 8123)
    assert err == "error: could not listen on 127.0.0.1:8123\n"
    [line] = lines
    assert (line["event"], line["interpreter"], line["synthetic"]) == ("starting", "rule", True)
    # No model reads, so none is named.
    assert line["model"] == "" and "provider" not in line


@pytest.mark.parametrize(
    ("env", "provider", "reason"),
    [
        ({"GEMINI_API_KEY": f"a-key-{CANARY}"}, None, "no_provider"),
        ({"ANTHROPIC_API_KEY": f"a-key-{CANARY}"}, None, "no_provider"),
        ({"BURRO_MODEL_PROVIDER": "gemini"}, "gemini", "no_key"),
        (
            {"BURRO_MODEL_PROVIDER": "gemini", "GEMINI_API_KEY": f"a-key-{CANARY}"},
            "gemini",
            "terms_not_accepted",
        ),
        (
            {
                "BURRO_MODEL_PROVIDER": "gemini",
                "GEMINI_API_KEY": f"a-key-{CANARY}",
                "BURRO_MODEL_TERMS_ACCEPTED": "openai",
            },
            "gemini",
            "terms_not_accepted",
        ),
    ],
    ids=["a key alone", "the old key alone", "no key", "no terms", "another's terms"],
)
def test_the_service_says_as_it_starts_which_provider_is_not_used_and_what_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    env: dict[str, str],
    provider: str | None,
    reason: str,
):
    _, lines, _ = started(monkeypatch, capsys, env)

    [warned, began] = lines
    assert (warned["event"], warned["level"], warned["reason"]) == (
        "model_not_used",
        "warning",
        reason,
    )
    assert warned.get("provider") == provider
    assert (began["event"], began["interpreter"], began["model"]) == ("starting", "rule", "")
    # One line, and no value in it.
    assert set(warned) <= {"at", "event", "level", "provider", "reason"}
    assert CANARY not in json.dumps(lines)


def test_the_line_that_says_the_service_is_starting_names_the_provider_that_reads(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    env = {
        "BURRO_MODEL_PROVIDER": "gemini",
        "GEMINI_API_KEY": f"a-key-{CANARY}",
        "BURRO_MODEL_TERMS_ACCEPTED": "gemini",
    }
    monkeypatch.setattr(uvicorn, "run", runs_nothing)
    configure_logging()

    assert serve(Settings.from_env(env), choose(env, send=never_sends)) == 0

    out, _ = capsys.readouterr()
    [line] = [json.loads(row) for row in out.splitlines()]
    assert (line["event"], line["interpreter"]) == ("starting", "model")
    assert (line["provider"], line["model"]) == ("gemini", "gemini-3.5-flash-lite")
    assert CANARY not in out


def test_a_test_that_sets_logging_up_leaves_every_logger_at_the_level_it_found():
    """Or the next test hears less than it says, and which is next depends on the order."""
    ours, library = logging.getLogger(LOGGER), logging.getLogger("some.library")
    with logging_put_back():
        ours.setLevel(logging.NOTSET)
        library.setLevel(logging.WARNING)
        with logging_put_back():
            configure_logging(io.StringIO())
            library.setLevel(logging.DEBUG)
            logging.getLogger("made.in.the.test").setLevel(logging.ERROR)
            assert ours.level == logging.INFO
        assert (ours.level, library.level) == (logging.NOTSET, logging.WARNING)
        assert logging.getLogger("made.in.the.test").level == logging.NOTSET
        assert ours.getEffectiveLevel() == logging.getLogger().level


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
