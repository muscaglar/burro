import subprocess
from pathlib import Path

import pytest
from check_public_only import (
    hosts_private_to_this_machine,
    lines_naming,
    lines_with_credentials,
    main,
    private_hosts,
    problems_in,
)

PRIVATE = "mirror.example.test"
PUBLIC_LOCK = """
[[package]]
name = "pydantic"
source = { registry = "https://pypi.org/simple" }
wheels = [{ url = "https://files.pythonhosted.org/packages/ab/cd/pydantic-2.0-py3-none-any.whl" }]
"""
PRIVATE_LOCK = PUBLIC_LOCK.replace("https://pypi.org/simple", f"https://{PRIVATE}/simple")
LEAK = f"index = https://user:secret@{PRIVATE}/simple\n"  # public-only: allow
UV_LOCK = Path("uv.lock")


def test_public_lockfile_is_clean():
    assert private_hosts(UV_LOCK, PUBLIC_LOCK) == set()


def test_private_registry_is_caught():
    assert private_hosts(UV_LOCK, PRIVATE_LOCK) == {PRIVATE}


def test_private_wheel_host_is_caught():
    lock = PUBLIC_LOCK.replace("files.pythonhosted.org", PRIVATE)
    assert private_hosts(UV_LOCK, lock) == {PRIVATE}


def test_lookalike_host_is_caught():
    lock = PUBLIC_LOCK.replace("https://pypi.org/simple", "https://pypi.org.example.test/simple")
    assert private_hosts(UV_LOCK, lock) == {"pypi.org.example.test"}


def test_credentials_in_a_registry_url_do_not_hide_the_host():
    private = f"https://user:secret@{PRIVATE}"  # public-only: allow
    lock = PUBLIC_LOCK.replace("https://pypi.org", private)
    assert private_hosts(UV_LOCK, lock) == {PRIVATE}


def test_the_private_host_is_never_printed():
    (problem,) = problems_in(UV_LOCK, PRIVATE_LOCK.encode())
    assert PRIVATE not in problem


PRIVATE_CASES = [
    ("uv.lock", PRIVATE_LOCK),
    ("pyproject.toml", f'[[tool.uv.index]]\nurl = "https://{PRIVATE}/simple"\n'),
    ("pyproject.toml", f'[tool.uv]\nindex-url = "https://{PRIVATE}/simple"\n'),
    ("pyproject.toml", f'[tool.uv]\nextra-index-url = ["https://{PRIVATE}/simple"]\n'),
    ("pyproject.toml", f'[tool.uv]\nfind-links = ["https://{PRIVATE}/wheels"]\n'),
    ("pyproject.toml", f'[tool.uv.pip]\nindex-url = "https://{PRIVATE}/simple"\n'),
    ("pyproject.toml", f'[tool.uv.sources]\nx = {{ url = "https://{PRIVATE}/x.whl" }}\n'),
    ("pyproject.toml", f'[tool.uv.sources]\nx = {{ git = "ssh://git@{PRIVATE}/x.git" }}\n'),
    ("pyproject.toml", f'[project]\ndependencies = ["x @ https://{PRIVATE}/x.whl"]\n'),
    ("pyproject.toml", f'[project]\ndependencies = ["x @ git+https://{PRIVATE}/x.git"]\n'),
    ("pyproject.toml", f'[dependency-groups]\ndev = ["x @ https://{PRIVATE}/x.whl"]\n'),
    ("pyproject.toml", f'[tool.anything.at.all]\nwhatever = "https://{PRIVATE}/"\n'),
    ("pyproject.toml", f"not valid toml [ https://{PRIVATE}/simple"),
    ("pyproject.toml", '[tool.uv]\nindex-url = "HTTPS://MIRROR.EXAMPLE.TEST/simple"\n'),
    ("pyproject.toml", f'[tool.uv]\nindex-url = "https://{PRIVATE}/s"  # public-only: allow\n'),
    ("PyProject.TOML", f'[tool.uv]\nindex-url = "https://{PRIVATE}/simple"\n'),
    ("uv.toml", f'[[index]]\nurl = "https://{PRIVATE}/simple"\n'),
    ("uv.toml", f'index-url = "https://{PRIVATE}/simple"\n'),
    ("requirements.txt", f"--index-url http://{PRIVATE}/simple\n"),
    ("requirements-dev.txt", f"x @ https://{PRIVATE}/x.whl\n"),
    ("REQUIREMENTS.TXT", f"--index-url https://{PRIVATE}/simple\n"),
    ("pip.conf", f"[global]\nindex-url = https://{PRIVATE}/simple\n"),
    ("setup.cfg", f"[easy_install]\nindex_url = https://{PRIVATE}/simple\n"),
    ("poetry.lock", f'[package.source]\nurl = "https://{PRIVATE}/simple"\n'),
    ("Dockerfile", f"RUN pip install --index-url https://{PRIVATE}/simple x\n"),
    ("Dockerfile.api", f"ENV UV_INDEX_URL=https://{PRIVATE}/simple\n"),
    ("api.dockerfile", f"ENV UV_INDEX_URL=https://{PRIVATE}/simple\n"),
    (".npmrc", f"registry=https://{PRIVATE}/npm/\n"),
    (".npmrc", f"@scope:registry=https://{PRIVATE}/npm/\n"),
    (".npmrc", f"//{PRIVATE}/npm/:always-auth=true\n"),
    ("package-lock.json", f'"resolved": "https://{PRIVATE}/npm/x/-/x-1.0.0.tgz",\n'),
    ("yarn.lock", f'  resolved "https://{PRIVATE}/npm/x/-/x-1.0.0.tgz#abc"\n'),
    (
        "pnpm-lock.yaml",
        f"    resolution: {{integrity: sha512-x, tarball: https://{PRIVATE}/x.tgz}}\n",
    ),
    ("Package.resolved", f'"location" : "https://{PRIVATE}/swift/x.git",\n'),
    ("Package.swift", f'.package(url: "https://{PRIVATE}/swift/x.git", from: "1.0.0"),\n'),
    ("package.json", f'{{"dependencies": {{"x": "https://{PRIVATE}/x.tgz"}}}}\n'),
    ("package.json", f'{{"publishConfig": {{"registry": "https://{PRIVATE}/npm/"}}}}\n'),
    ("yarn.lock", f'  resolution: "x@https://{PRIVATE}/x.tgz"\n'),
    ("pnpm-lock.yaml", f"    resolution: {{repo: https://{PRIVATE}/x.git, type: git}}\n"),
    (".yarnrc.yml", f'npmRegistryServer: "https://{PRIVATE}/npm/"\n'),
]


@pytest.mark.parametrize(("name", "text"), PRIVATE_CASES)
def test_a_private_host_in_a_package_file_is_caught(name: str, text: str):
    path = Path("apps/x") / name
    assert private_hosts(path, text) == {PRIVATE}
    assert problems_in(path, text.encode()) == [
        f"apps/x/{name}: 1 host(s) outside the public allowlist"
    ]


PUBLIC_CASES = [
    ("pyproject.toml", '[[tool.uv.index]]\nurl = "https://pypi.org/simple"\ndefault = true\n'),
    ("pyproject.toml", '[tool.uv]\nfind-links = ["./wheels"]\n'),
    ("pyproject.toml", '[project]\ndependencies = ["x @ git+https://github.com/o/x.git"]\n'),
    ("pyproject.toml", '[tool.uv.sources]\nx = { git = "ssh://git@github.com/o/x.git" }\n'),
    (".npmrc", "registry=https://registry.npmjs.org/\n//registry.npmjs.org/:always-auth=true\n"),
    ("package-lock.json", '"resolved": "https://registry.npmjs.org/x/-/x-1.0.0.tgz",\n'),
    ("package-lock.json", '"funding": { "url": "https://opencollective.example.test/x" },\n'),
    ("yarn.lock", '  resolved "https://registry.yarnpkg.com/x/-/x-1.0.0.tgz#abc"\n'),
    ("Package.resolved", '"location" : "https://github.com/maplibre/maplibre-gl-native",\n'),
    ("README.md", f"Our mirror was https://{PRIVATE}/ and prose may say so.\n"),
    ("housing.toml", 'url = "https://www.gov.uk/government/collections/price-paid-data"\n'),
]


@pytest.mark.parametrize(("name", "text"), PUBLIC_CASES)
def test_public_hosts_and_other_files_pass(name: str, text: str):
    assert private_hosts(Path("apps/x") / name, text) == set()


def test_a_ci_workflow_is_a_package_file():
    workflow = Path(".github/workflows/ci.yml")
    leak = f"env:\n  UV_INDEX_URL: https://{PRIVATE}/simple\n"
    assert private_hosts(workflow, leak) == {PRIVATE}
    assert private_hosts(workflow, "      - run: uv sync\n") == set()
    assert private_hosts(Path("docs/ci.yml"), leak) == set()


def test_an_ip_address_is_not_a_public_host():
    assert private_hosts(Path("pip.conf"), "index-url = https://10.1.2.3/simple\n") == {"10.1.2.3"}


def test_url_with_password_is_caught():
    assert lines_with_credentials(b"ok\n" + LEAK.encode()) == [2]


def test_url_with_token_only_is_caught():
    content = b"postgres://token@db.example.test:5432/burro"  # public-only: allow
    assert lines_with_credentials(content) == [1]


def test_an_npm_token_is_caught():
    assert lines_with_credentials(b"//registry.npmjs.org/:_authToken=npm_abc123\n") == [1]
    assert lines_with_credentials(b"//registry.npmjs.org/:_password = aGVsbG8=\n") == [1]


def test_an_unscoped_or_yarn_token_is_caught():
    assert lines_with_credentials(b"_auth = aGVsbG86d29ybGQ=\n") == [1]
    assert lines_with_credentials(b"_authToken=npm_abc123\n") == [1]
    assert lines_with_credentials(b'npmAuthToken: "npm_abc123"\n') == [1]
    assert lines_with_credentials(b"  npmAuthIdent: user:pass\n") == [1]


@pytest.mark.parametrize(
    "line",
    [
        b"//registry.npmjs.org/:_authToken=${NPM_TOKEN}",
        b"//registry.npmjs.org/:_authToken=$NPM_TOKEN",
        b"_authToken=${NPM_TOKEN}",
        b'npmAuthToken: "${NPM_TOKEN}"',
        b"npmAuthToken: $NPM_TOKEN",
    ],
)
def test_a_token_read_from_the_environment_passes(line: bytes):
    assert lines_with_credentials(line) == []


@pytest.fixture
def machine(tmp_path: Path) -> Path:
    """A home folder set up the way a machine behind a private mirror is."""
    home = tmp_path / "home"
    (home / ".config/uv").mkdir(parents=True)
    index = f"https://user:token@{PRIVATE}/simple"  # public-only: allow
    (home / ".config/uv/uv.toml").write_text(f'[[index]]\nurl = "{index}"\ndefault = true\n')
    (home / ".npmrc").write_text(
        "registry=https://npm.example.test/\n//npm.example.test/:always-auth=true\n"
    )
    return home


def test_the_machines_private_hosts_are_read_from_its_settings(machine: Path):
    assert hosts_private_to_this_machine(machine, {}) == {PRIVATE, "npm.example.test"}


def test_the_machines_private_hosts_are_read_from_its_environment(tmp_path: Path):
    environ = {"PIP_INDEX_URL": f"https://{PRIVATE}/simple", "PATH": "/usr/bin"}
    assert hosts_private_to_this_machine(tmp_path, environ) == {PRIVATE}


def test_a_machine_on_public_registries_has_no_private_hosts(tmp_path: Path):
    (tmp_path / ".npmrc").write_text("registry=https://registry.npmjs.org/\n")
    environ = {"UV_DEFAULT_INDEX": "https://pypi.org/simple"}
    assert hosts_private_to_this_machine(tmp_path, environ) == frozenset()


@pytest.mark.parametrize(
    ("name", "text"),
    [
        ("pip.conf", f"[global]\ntrusted-host = {PRIVATE}\n"),
        ("requirements.txt", f"--trusted-host {PRIVATE}\n"),
        ("Dockerfile", f"FROM {PRIVATE}/base/python:3.13\n"),
        (".github/workflows/ci.yml", f"    container:\n      image: {PRIVATE}/ci:latest\n"),
        ("pyproject.toml", f'[tool.uv.sources]\nx = {{ git = "git@{PRIVATE}:o/x.git" }}\n'),
        ("docs/notes.md", f"Packages come from {PRIVATE.upper()} on this laptop.\n"),
        ("src/settings.py", f'MIRROR = "{PRIVATE}"\n'),
    ],
)
def test_a_bare_mention_of_the_machines_private_host_is_caught_in_any_file(name: str, text: str):
    assert private_hosts(Path(name), text) == set(), "a URL pattern cannot see this"
    problems = problems_in(Path(name), text.encode(), frozenset({PRIVATE}))
    assert len(problems) == 1
    assert "names a package host that is private to this machine" in problems[0]
    assert PRIVATE not in problems[0].lower()


def test_without_private_settings_the_backstop_does_nothing():
    assert lines_naming(frozenset(), f"trusted-host = {PRIVATE}\n".encode()) == []


def test_plain_urls_and_emails_pass():
    content = b"see https://example.test/a?b=c@d\nmail hpi@ons.gov.uk\ngit@github.com:org/repo\n"
    assert lines_with_credentials(content) == []


def test_the_conventional_ssh_user_is_not_a_secret():
    assert lines_with_credentials(b"ssh://git@github.com/org/repo.git") == []
    assert lines_with_credentials(b"git+ssh://git@github.com/org/repo.git") == []
    leak = b"ssh://git:hunter2@github.com/org/repo.git"  # public-only: allow
    assert lines_with_credentials(leak) == [1]


def test_a_marked_placeholder_is_excused_from_the_credentials_check():
    line = b"DATABASE_URL=postgresql://postgres:postgres@localhost/burro  # public-only: allow"
    assert lines_with_credentials(line) == []


def test_binary_files_are_skipped():
    assert problems_in(Path("trace.zip"), b"PK\0" + LEAK.encode()) == []


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def stage(path: Path) -> None:
    subprocess.run(["git", "add", "-f", str(path)], check=True)


def test_the_backstop_runs_from_the_command(
    repo: Path, machine: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setenv("HOME", str(machine))
    (repo / "Dockerfile").write_text(f"FROM {PRIVATE}/base/python:3.13\n")
    assert main() == 1
    printed = capsys.readouterr()
    assert "Dockerfile:1: names a package host that is private to this machine" in printed.err
    assert PRIVATE not in printed.err + printed.out


def test_a_clean_repository_passes(repo: Path, capsys: pytest.CaptureFixture[str]):
    (repo / "notes.md").write_text("nothing to see\n")
    assert main() == 0
    assert capsys.readouterr().out == "public-only: clean\n"


def test_an_untracked_file_with_credentials_fails(repo: Path, capsys: pytest.CaptureFixture[str]):
    (repo / "notes.md").write_text(LEAK)
    assert main() == 1
    assert "notes.md:1: contains credentials" in capsys.readouterr().err


def test_an_ignored_file_is_not_read(repo: Path):
    (repo / ".gitignore").write_text("uv.lock\n")
    (repo / "uv.lock").write_text(PRIVATE_LOCK)
    assert main() == 0


def test_an_ignored_lockfile_that_was_force_added_fails(repo: Path):
    (repo / ".gitignore").write_text("uv.lock\n")
    (repo / "uv.lock").write_text(PRIVATE_LOCK)
    stage(repo / "uv.lock")
    assert main() == 1


def test_what_is_staged_is_checked_even_after_the_file_is_fixed_on_disk(
    repo: Path, capsys: pytest.CaptureFixture[str]
):
    (repo / "notes.md").write_text(LEAK)
    stage(repo / "notes.md")
    (repo / "notes.md").write_text("fixed, but not staged again\n")
    assert main() == 1
    assert "notes.md:1: contains credentials (staged)" in capsys.readouterr().err


def test_a_symlink_is_read_as_the_link_git_would_commit(repo: Path):
    (repo / ".gitignore").write_text("secret.txt\n")
    (repo / "secret.txt").write_text(LEAK)
    (repo / "link.txt").symlink_to("secret.txt")
    assert main() == 0
