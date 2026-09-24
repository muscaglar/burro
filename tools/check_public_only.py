"""Fail if a private package address or a URL with credentials is about to be committed.

Three checks, on every file git tracks or would track, and on what is staged:

1. No URL with a username, password or token in it, in any file.
2. No URL to a host outside the public allowlist, in any file that says where
   packages come from: manifests, lockfiles, requirements files, Dockerfiles,
   CI workflows, and the settings files of uv, pip, npm and yarn.
3. No mention, in any file and in any form, of a package host that this machine
   is set up to use and that is not public.

The second check fails closed on URLs. To use another public host, add it to
PUBLIC_HOSTS below, where the change is reviewed. There is no per-line opt-out.
A line marked `public-only: allow` is excused from the first check only, for
placeholders such as a local database address.

The third check is the backstop. It reads this machine's own uv, pip, npm and
yarn settings to learn which hosts are private here, then looks for them
everywhere. It catches what a URL pattern cannot, such as a bare hostname. On a
machine with no private settings it does nothing.

It is not a secret scanner. It will not notice an API key on a line of its own.
A private host written without a URL scheme, on a machine that is not
configured to use it, will also pass.

No private hostname is ever written into this repository or printed: hosts are
counted, and the machine's settings are read but never shown. Standard library
only: this runs before the virtual environment exists.
See docs/adr/0008-package-sources.md.
"""

import os
import re
import subprocess
import sys
from collections.abc import Iterator, Mapping
from fnmatch import fnmatch
from pathlib import Path
from urllib.parse import urlsplit

PUBLIC_HOSTS = frozenset(
    {
        "pypi.org",
        "files.pythonhosted.org",
        "registry.npmjs.org",
        "registry.yarnpkg.com",
        "github.com",
    }
)
ALLOW_MARKER = "public-only: allow"

# Files that say where packages come from. Every URL in them must be public.
# Matched without regard to case; a pattern with a slash is matched on the path.
PACKAGE_FILES = (
    "uv.lock",
    "uv.toml",
    "pyproject.toml",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "requirements*.txt",
    "pip.conf",
    "pip.ini",
    ".pypirc",
    "setup.cfg",
    "package.json",
    ".npmrc",
    ".yarnrc",
    ".yarnrc.yml",
    "Package.swift",
    "Package.resolved",
    "Dockerfile*",
    "*.dockerfile",
    ".github/workflows/*",
    ".github/actions/*",
)
# Lockfiles that also hold unrelated links, such as funding pages.
# Only the addresses packages are fetched from are checked.
JS_LOCKFILES = ("package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml")

# Where this machine keeps its own package settings, relative to the home folder.
MACHINE_SETTINGS = (
    ".config/uv/uv.toml",
    ".config/pip/pip.conf",
    ".pip/pip.conf",
    "Library/Application Support/pip/pip.conf",
    ".pypirc",
    ".npmrc",
    ".yarnrc",
    ".yarnrc.yml",
)
MACHINE_VARIABLES = (
    "UV_INDEX",
    "UV_INDEX_URL",
    "UV_DEFAULT_INDEX",
    "UV_EXTRA_INDEX_URL",
    "PIP_INDEX_URL",
    "PIP_EXTRA_INDEX_URL",
    "NPM_CONFIG_REGISTRY",
    "npm_config_registry",
    "YARN_NPM_REGISTRY_SERVER",
)

_URL = r"""(?:git\+)?(?:https?|ssh|git)://[^\s"'<>,)\]}]+"""
URL = re.compile(_URL, re.IGNORECASE)
PACKAGE_ADDRESS = re.compile(
    rf"""(?:resolved|resolution|tarball|registry|repo)["']?\s*[:=]?\s*["']?(?:[^\s"'@]+@)?({_URL})""",
    re.IGNORECASE,
)
NPMRC_HOST = re.compile(r"^\s*//([^/\s:]+)", re.MULTILINE)

# `git@` alone is the conventional ssh user, not a secret.
URL_WITH_CREDENTIALS = re.compile(
    rb"[a-z][a-z0-9+.-]*://(?!git@)[^\s/@\"'<>]+@[a-z0-9\[]", re.IGNORECASE
)
# A value read from the environment, `${NAME}` or `$NAME`, is not a secret.
NPM_TOKEN = re.compile(
    rb"""^\s*(?:(?://[^/\s]+/:)?_(?:auth|authToken|password)\s*=|npmAuth(?:Token|Ident)\s*:)"""
    rb"""\s*(?!["']?\$\{?\w)\S"""
)


def _matches(path: Path, patterns: tuple[str, ...]) -> bool:
    name, whole = path.name.lower(), path.as_posix().lower()
    return any(
        fnmatch(whole, f"*{pattern.lower()}") if "/" in pattern else fnmatch(name, pattern.lower())
        for pattern in patterns
    )


def _hosts(text: str) -> set[str]:
    urls: list[str] = URL.findall(text)
    return {host for url in urls if (host := urlsplit(url).hostname)}


def _bare_hosts(text: str) -> set[str]:
    """Hosts on npm-style `//host/path` lines, which carry no scheme."""
    found: list[str] = NPMRC_HOST.findall(text)
    return {host.lower() for host in found}


def private_hosts(path: Path, text: str) -> set[str]:
    """Hosts a package file names in a URL that are not on the public allowlist."""
    if _matches(path, JS_LOCKFILES):
        addresses: list[str] = PACKAGE_ADDRESS.findall(text)
        hosts = _hosts("\n".join(addresses))
    elif _matches(path, PACKAGE_FILES):
        hosts = _hosts(text)
    else:
        return set()
    if path.name.lower() in (".npmrc", ".yarnrc"):
        hosts |= _bare_hosts(text)
    return hosts - PUBLIC_HOSTS


def hosts_private_to_this_machine(
    home: Path | None = None, environ: Mapping[str, str] | None = None
) -> frozenset[str]:
    """Package hosts this machine is set up to use that are not public. Never printed."""
    home = home or Path.home()
    environ = os.environ if environ is None else environ
    texts = [environ.get(variable, "") for variable in MACHINE_VARIABLES]
    for setting in MACHINE_SETTINGS:
        try:
            texts.append((home / setting).read_text(errors="replace"))
        except OSError:
            continue
    hosts: set[str] = set()
    for text in texts:
        hosts |= _hosts(text) | _bare_hosts(text)
    return frozenset(hosts - PUBLIC_HOSTS)


def lines_naming(hosts: frozenset[str], content: bytes) -> list[int]:
    """Line numbers that mention any of these hosts, in any form."""
    wanted = [host.encode() for host in hosts]
    return [
        number
        for number, line in enumerate(content.lower().splitlines(), start=1)
        if any(host in line for host in wanted)
    ]


def lines_with_credentials(content: bytes) -> list[int]:
    """Line numbers holding a URL, or an npm or yarn settings line, with a secret in it."""
    return [
        number
        for number, line in enumerate(content.splitlines(), start=1)
        if (URL_WITH_CREDENTIALS.search(line) or NPM_TOKEN.search(line))
        and ALLOW_MARKER.encode() not in line
    ]


def problems_in(
    path: Path, content: bytes, machine_hosts: frozenset[str] = frozenset()
) -> list[str]:
    if b"\0" in content:
        return []
    found = [f"{path}:{n}: contains credentials" for n in lines_with_credentials(content)]
    found += [
        f"{path}:{n}: names a package host that is private to this machine"
        for n in lines_naming(machine_hosts, content)
    ]
    # Private hosts are counted, not printed, so one never reaches a CI log.
    if hosts := private_hosts(path, content.decode(errors="replace")):
        found.append(f"{path}: {len(hosts)} host(s) outside the public allowlist")
    return found


def _git(*args: str) -> bytes:
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def _paths(listing: bytes) -> list[Path]:
    return [Path(name.decode()) for name in listing.split(b"\0") if name]


def on_disk() -> Iterator[tuple[Path, bytes]]:
    """Every file git tracks or would track, as it is in the working tree."""
    for path in _paths(_git("ls-files", "-z", "--cached", "--others", "--exclude-standard")):
        if path.is_symlink():
            yield path, str(path.readlink()).encode()
        elif path.is_file():
            yield path, path.read_bytes()


def staged() -> Iterator[tuple[Path, bytes]]:
    """Every file about to be committed, as it is in the index."""
    for path in _paths(_git("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR")):
        yield path, _git("cat-file", "blob", f":{path.as_posix()}")


def main() -> int:
    machine_hosts = hosts_private_to_this_machine()
    failures = {
        problem
        for path, content in on_disk()
        for problem in problems_in(path, content, machine_hosts)
    }
    failures |= {
        f"{problem} (staged)"
        for path, content in staged()
        for problem in problems_in(path, content, machine_hosts)
        if problem not in failures
    }
    for failure in sorted(failures):
        print(f"error: {failure}", file=sys.stderr)
    if not failures:
        print("public-only: clean")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
