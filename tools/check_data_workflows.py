"""Fail if a workflow that builds data could show a row, a key or the store's address.

On a public repository anyone reads a workflow, its log and what it uploads.
A data workflow is a file named `data-*.yml` in .github/workflows, and it is
held to these rules:

1. It is started by hand and by nothing else. One run at a time.
2. A job that is given a secret names the environment, which is named for the
   workflow and which a person must approve. One job checks that the run is on
   the default branch, and every other job waits for it.
3. The workflow asks for no permission. A job asks to read the code. The job
   that searches the log asks to read the log as well.
4. It uses the two actions that set a job up, each at the commit ci.yml pins,
   and keeps no credentials and no cache. The installer is set up at the one
   version stated.
5. A secret is given to one step, by name, and that step runs behind
   tools/public_log.py. The first step given a secret is the one that checks
   them, and no later step is given one it did not check. A step is given
   every secret it reads and no other. Where no step of a job reads one, the
   job holds made-up ones, and the check is of that.
   A step is given nothing else but an input, a matrix value or an output,
   each under a name from a short list, and the token and the default branch,
   each under its own name and each to one step. No value is written in a
   workflow: a setting of the installer can be given as plainly as that.
6. A step runs one command, on one line, from a short list: a tool of this
   folder, or a step of the project's own commands behind tools/public_log.py.
   The steps are on a list too. Nothing on either list prints the environment
   or sends a file anywhere, and `describe` is on neither: what it prints
   holds names from a file, so it is for a person's own machine. A word of a
   command may come from an input, and never from a secret.
7. One line installs, and it is the same in every job: the pipeline package
   and what it needs, with no development group, and nothing published after
   the day stated. The step that installs is given nothing. Every other
   command runs in what was installed, as it stands, and can install nothing.
8. It holds no address.

No other workflow may name a secret or an environment of a data workflow.

The installer reads more than the line that installs. So the repository holds
no settings file of the installer, a manifest holds no setting of it but what
makes the workspace, and what a package needs is named, and is taken from this
workspace or from the index.

The files are read by a reader of this file's own, which knows the few shapes
a workflow here needs and refuses the rest. What it cannot read, it fails.

    python tools/check_data_workflows.py
    python tools/check_data_workflows.py --on-default-branch    the first step of a run

Standard library only: this runs before the virtual environment exists.
See docs/data-builds.md.
"""

import argparse
import os
import re
import sys
import tomllib
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from public_log import SECRET_NAMES, SECRETS_OF, STEPS, STORE

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = Path(".github/workflows")

type Node = str | list[Node] | dict[str, Node]

RUNS_ON = "ubuntu-24.04"
# Nothing published after this day is installed. No lockfile is committed yet (ADR 0008),
# so this is what holds a version. A person moves it forward, in a change that is read:
# docs/data-builds.md says when and how.
PACKAGES_BEFORE = "2026-09-23T00:00:00Z"
# The one line that installs: the pipeline package and what it needs, with no development
# group. A job is given the key of the store, so it installs what a step imports and no more.
INSTALL = f"uv sync --package burro-pipeline --no-dev --exclude-newer {PACKAGES_BEFORE}"
CHECKOUT, SETUP_UV = "actions/checkout", "astral-sh/setup-uv"
# The one version of the installer a job sets up. Another version may read the line that
# installs another way, and `latest` is whatever is newest on the day of a run. A person
# moves it, in a change that is read, on every line that sets the installer up.
INSTALLER = "0.12.17"
# What each action must be given, and it may be given nothing else. A checkout given a
# branch or a repository would run other code with this workflow's secrets.
MUST_SET = {
    CHECKOUT: {"persist-credentials": "false"},
    SETUP_UV: {"version": INSTALLER, "enable-cache": "false"},
}
# What the installer reads beside the line that installs. A settings file of its own, or a
# table of its settings in a manifest, can name another index, a folder of files, or a day
# of its own for one package. So the repository holds no such file, and a manifest holds
# only what makes the workspace.
SETTINGS_FILE = "uv.toml"
OF_THE_WORKSPACE = frozenset({"package", "workspace", "sources"})
FROM_THE_WORKSPACE = {"workspace": True}
# What a package needs, as a manifest names it: a name, with any extras, versions and
# markers. A file, a folder or an address stands where no name can, or after `@`.
NEEDED = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\s*(?:\[[^\]@]*\])?\s*(?:[(<>=!~;][^@]*)?")

WORKFLOW_KEYS = {"name", "on", "permissions", "concurrency", "jobs"}
JOB_KEYS = {
    "name",
    "needs",
    "if",
    "runs-on",
    "timeout-minutes",
    "environment",
    "permissions",
    "strategy",
    "outputs",
    "steps",
}
STEP_KEYS = {"name", "id", "if", "uses", "with", "env", "run"}

# One command on one line. No pipe, no redirect, no second command, nothing
# worked out by the shell. A variable only inside double quotes, and only one
# the runner sets to a folder, or one the step is given from an input.
LETTER = r"[A-Za-z0-9_./=:@%+,-]"
VARIABLE = re.compile(r"\$([A-Z][A-Z0-9_]*)")
# One letter at a time: a run of letters inside a run of words is slow to refuse.
WORD = rf"""(?:{LETTER}|"(?:{LETTER}|\$[A-Z][A-Z0-9_]*)+")+"""
FOLDERS = frozenset({"RUNNER_TEMP", "GITHUB_WORKSPACE"})
# A plain `uv run` brings the environment up to date before it runs anything: every
# package of the workspace, the development group included, each at its newest. So a
# command is run in one of two ways, and neither installs. With nothing of the project:
APART = "uv run --no-project"
# Or in what the job installed, as it stands:
AS_INSTALLED = "uv run --no-sync"
TOOL = re.compile(
    rf"(?:{re.escape(APART)}|{re.escape(AS_INSTALLED)}) python tools/([a-z_]+\.py)(?: {WORD})*"
)
PUBLIC_LOG = f"{APART} python tools/public_log.py"
# Behind the public log runs a command of the project's own: a console script, or a module.
# Its first word is the step it runs.
COMMAND = r"python -m [a-z_][a-z0-9_.]*|[a-z][a-z0-9-]*"
BEHIND = re.compile(
    rf"{re.escape(PUBLIC_LOG)} --step ([a-z]+) -- {re.escape(AS_INSTALLED)} ({COMMAND})"
    rf" ([a-z][a-z-]*)(?: {WORD})*"
)
# The steps a data workflow runs behind the public log, by the command each is a step of,
# and the secrets each reads. A step is given those and no other. A step is added here
# when a workflow first runs it, in a change that a person reads.
STEPS_OF_A_RUN: dict[str, dict[str, tuple[str, ...]]] = {
    "python -m burro_pipeline": {"fetch": SECRETS_OF["data-fetch"], "held": STORE},
    "burro-release": {"build-synthetic": (), "check": ()},
}
# What these print holds names from a file's own layout. No run shows it, and none runs them.
FOR_A_PERSONS_OWN_MACHINE = frozenset({"describe"})
MASK = f"{PUBLIC_LOG} mask"
# The same check, of secrets that must each be made up.
MASK_MADE_UP = f"{MASK} --made-up"
GUARD = "uv run --no-project python tools/check_data_workflows.py --on-default-branch"
SEARCH = "uv run --no-project python tools/canary.py search"
DEFAULT_BRANCH = "${{ github.event.repository.default_branch }}"
# The expression that stands for the run's own token. It is not a token.
TOKEN = "${{ github.token }}"  # noqa: S105

NAME = r"[A-Za-z_][A-Za-z0-9_-]*"
EXPRESSION = re.compile(r"\$\{\{(.*?)\}\}")
SECRET = re.compile(rf"\$\{{\{{ secrets\.({NAME}) \}}\}}")
INPUT = re.compile(rf"\$\{{\{{ inputs\.{NAME} \}}\}}")
IN_ENV = re.compile(
    rf"\$\{{\{{ (?:inputs\.{NAME}|matrix\.{NAME}|needs\.{NAME}\.outputs\.{NAME}) \}}\}}"
)
# The names a step may be given an input, a matrix value or an output under. Each is read
# by a tool of this folder, or stands in a command inside double quotes. Whoever starts a
# run types an input, so under a name that the installer, Python or the shell reads it
# would be a setting. A name is added here when a workflow first gives it, in a change
# that a person reads.
NAMES_GIVEN = frozenset({"LIST", "ITEM", "COPY", "COPY_A", "COPY_B"})
# A step may be left out of a run, and only by whether an input is empty.
STEP_IF = re.compile(rf"inputs\.{NAME} [!=]= ''")
IN_NAME = re.compile(rf"\$\{{\{{ matrix\.{NAME} \}}\}}")
IN_OUTPUTS = re.compile(rf"\$\{{\{{ steps\.{NAME}\.outputs\.{NAME} \}}\}}")

PINNED = re.compile(r"^\s*-?\s*uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+@[0-9a-f]{40})\s*(?:#.*)?$")
ADDRESS = re.compile(
    r"[a-z][a-z0-9+.-]*://"
    r"|\.r2\.cloudflarestorage\.com|\.r2\.dev|\.amazonaws\.com|\.backblazeb2\.com"
    r"|\.digitaloceanspaces\.com|\.blob\.core\.windows\.net|storage\.googleapis\.com",
    re.IGNORECASE,
)


class Unreadable(Exception):
    """The file holds a shape this reader does not know. It is never guessed at."""

    def __init__(self, line: int, why: str) -> None:
        super().__init__(f"line {line}: {why}")


@dataclass(frozen=True)
class _Line:
    indent: int
    text: str
    number: int


KEY = re.compile(r"([A-Za-z_][A-Za-z0-9_.-]*):(?: +(.*))?")


def _lines(text: str) -> list[_Line]:
    found: list[_Line] = []
    for number, raw in enumerate(text.split("\n"), start=1):
        if any(ord(letter) < 32 or ord(letter) > 126 for letter in raw):
            raise Unreadable(number, "a tab, or a letter that is not plain ASCII")
        line = raw.rstrip(" ")
        if not line or line.lstrip(" ").startswith("#"):
            continue
        if line.startswith("---") or line.startswith("..."):
            raise Unreadable(number, "a second document")
        found.append(_Line(len(line) - len(line.lstrip(" ")), line.lstrip(" "), number))
    return found


def _without_comment(text: str) -> str:
    """A plain value, up to where a comment starts: at ` #`, whatever quotes stand before it."""
    return re.split(r"\s#", f" {text}", maxsplit=1)[0].strip()


def _quoted(text: str, number: int) -> str:
    quote, end = text[0], text.find(text[0], 1)
    inner, after = text[1:end], text[end + 1 :]
    if end < 0 or "\\" in inner or after.startswith(quote) or _without_comment(after):
        raise Unreadable(number, "a quoted value this reader does not know")
    return inner


def _value(text: str, number: int) -> Node | None:
    """What stands after `key:` or `- `. Nothing at all is None: a block may follow."""
    text = text.strip()
    if not text or text.startswith("#"):
        return None
    if text[0] in "'\"":
        return _quoted(text, number)
    plain = _without_comment(text)
    if plain == "{}":
        return {}
    if plain.startswith("["):
        if not plain.endswith("]") or "#" in plain:
            raise Unreadable(number, "a list this reader does not know")
        items = [_value(item, number) for item in plain[1:-1].split(",")]
        if not all(isinstance(item, str) and item and item[0] not in "[{" for item in items):
            raise Unreadable(number, "a list this reader does not know")
        return cast(list[Node], items)
    if plain[0] in "&*!|>%@`{?-" or ": " in plain or plain.endswith(":"):
        raise Unreadable(number, "a value over several lines, an anchor, or a map on one line")
    return plain


def _is_item(line: _Line) -> bool:
    return line.text == "-" or line.text.startswith("- ")


def _block(lines: list[_Line], at: int) -> tuple[Node, int]:
    indent = lines[at].indent
    node, at = (_sequence if _is_item(lines[at]) else _mapping)(lines, at, indent)
    if at < len(lines) and lines[at].indent > indent:
        raise Unreadable(lines[at].number, "the indentation does not line up")
    return node, at


def _mapping(lines: list[_Line], at: int, indent: int) -> tuple[Node, int]:
    found: dict[str, Node] = {}
    while at < len(lines) and lines[at].indent == indent and not _is_item(lines[at]):
        line = lines[at]
        match = KEY.fullmatch(line.text)
        if match is None:
            raise Unreadable(line.number, "not `key: value`")
        key = match[1]
        if key in found:
            raise Unreadable(line.number, f"`{key}` is set twice")
        value, at = _value(match[2] or "", line.number), at + 1
        deeper = at < len(lines) and lines[at].indent > indent
        if value is None:
            found[key], at = _block(lines, at) if deeper else ("", at)
        elif deeper:
            raise Unreadable(lines[at].number, "the indentation does not line up")
        else:
            found[key] = value
    return found, at


def _sequence(lines: list[_Line], at: int, indent: int) -> tuple[Node, int]:
    found: list[Node] = []
    while at < len(lines) and lines[at].indent == indent and _is_item(lines[at]):
        line = lines[at]
        inner = line.text[1:].lstrip(" ")
        if KEY.fullmatch(inner):
            # A map whose first key shares the line with the dash.
            within = indent + len(line.text) - len(inner)
            lines[at] = _Line(within, inner, line.number)
            item, at = _mapping(lines, at, within)
            if at < len(lines) and lines[at].indent > indent:
                raise Unreadable(lines[at].number, "the indentation does not line up")
        else:
            value, at = _value(inner, line.number), at + 1
            if value is None or (at < len(lines) and lines[at].indent > indent):
                raise Unreadable(line.number, "an item this reader does not know")
            item = value
        found.append(item)
    return found, at


def read_workflow(text: str) -> dict[str, Node]:
    """A workflow as maps, lists and words. Raises `Unreadable` for any shape it does not know."""
    lines = _lines(text)
    if not lines or lines[0].indent or _is_item(lines[0]):
        raise Unreadable(lines[0].number if lines else 1, "not a map of keys")
    node, at = _block(lines, 0)
    if at < len(lines):
        raise Unreadable(lines[at].number, "the indentation does not line up")
    return cast(dict[str, Node], node)


def pinned_in(ci: str) -> frozenset[str]:
    """Every action ci.yml uses at a full commit."""
    matches = (PINNED.match(line) for line in ci.splitlines())
    return frozenset(match[1] for match in matches if match)


def _map(node: Node | None) -> dict[str, Node]:
    return node if isinstance(node, dict) else {}


def _maps(node: Node | None) -> list[dict[str, Node]]:
    return [item for item in node if isinstance(item, dict)] if isinstance(node, list) else []


def _words(node: Node | None) -> list[str]:
    if isinstance(node, str):
        return [node] if node else []
    return [item for item in node if isinstance(item, str)] if isinstance(node, list) else []


def _strings(node: Node) -> Iterator[str]:
    if isinstance(node, str):
        yield node
    else:
        for item in node.values() if isinstance(node, dict) else node:
            yield from _strings(item)


def _short(text: str) -> str:
    return text if len(text) <= 60 else f"{text[:57]}..."


@dataclass(frozen=True)
class _Known:
    """What the rules are checked against."""

    environment: str
    pinned: frozenset[str]
    commands: frozenset[str]
    tools: frozenset[str]


def _of_the_workflow(workflow: dict[str, Node]) -> Iterator[str]:
    for key in sorted(set(workflow) - WORKFLOW_KEYS):
        if key == "env":
            yield "a secret is given to one step, never to a workflow: remove `env`"
        else:
            yield f"a data workflow may not hold `{key}`"
    if set(_map(workflow.get("on"))) != {"workflow_dispatch"}:
        yield "it must be started by hand and by nothing else: `on` holds workflow_dispatch only"
    if workflow.get("permissions") != {}:
        yield "the workflow must ask for no permission, `permissions: {}`. A job asks for its own"
    concurrency = _map(workflow.get("concurrency"))
    if not concurrency.get("group") or concurrency.get("cancel-in-progress") != "false":
        yield "one run at a time: set `concurrency`, with a group and cancel-in-progress: false"
    if not _map(workflow.get("jobs")):
        yield "it holds no job"
    outside = {key: value for key, value in workflow.items() if key != "jobs"}
    if any("${{" in text for text in _strings(outside)):
        yield "an expression stands outside a job, where none is needed"


def _of_a_command(step: dict[str, Node], known: _Known) -> Iterator[str]:
    run = step.get("run")
    if not isinstance(run, str):
        yield "a step's `run` must be one command on one line"
        return
    given = _map(step.get("env"))
    env = list(_strings(given))
    behind, tool = BEHIND.fullmatch(run), TOOL.fullmatch(run)
    allowed = (
        run in (INSTALL, MASK, MASK_MADE_UP)
        or (behind is not None and behind[1] in STEPS and behind[2] in known.commands)
        or (tool is not None and tool[1] in known.tools and tool[1] != "public_log.py")
    )
    from_inputs = {name for name, value in given.items() if INPUT.fullmatch(str(value))}
    if not allowed or not set(VARIABLE.findall(run)) <= FOLDERS | from_inputs:
        installs = f". A job installs with one line, and no other: `{INSTALL}`"
        hint = installs if re.match(r"uv sync\b", run) else ""
        yield f"`{_short(run)}` is not a command a data workflow may run{hint}"
    elif behind is not None and behind[3] in FOR_A_PERSONS_OWN_MACHINE:
        yield (
            f"`{behind[3]}` is for a person's own machine: what it prints holds names from "
            "a file, and no workflow runs it"
        )
    elif behind is not None and behind[3] not in STEPS_OF_A_RUN.get(behind[2], ()):
        yield f"`{behind[3]}` is not a step a data workflow runs"
    elif behind is not None:
        reads = set(STEPS_OF_A_RUN[behind[2]][behind[3]])
        holds = {match[1] for value in env if (match := SECRET.fullmatch(value))}
        for name in sorted(holds - reads):
            yield f"`{behind[3]}` is given {name}, which it does not read"
        for name in sorted(reads - holds):
            yield f"`{behind[3]}` reads {name}, and is not given it"
    checks = run in (MASK, MASK_MADE_UP)
    if any(SECRET.fullmatch(value) for value in env) and not (behind or checks):
        yield f"`{_short(run)}` is given a secret and does not run behind tools/public_log.py"
    if TOKEN in env and run != SEARCH:
        yield "the token is for the step that searches the log, and for no other"
    if DEFAULT_BRANCH in env and run != GUARD:
        yield "the default branch is for the step that checks the branch, and for no other"
    if run == INSTALL and "env" in step:
        yield "the step that installs is given nothing: remove `env`"
    yield from _of_what_is_given(step)
    if run == GUARD and env != [DEFAULT_BRANCH]:
        yield "the step that checks the branch is given DEFAULT_BRANCH and nothing else"


def _of_what_is_given(step: dict[str, Node]) -> Iterator[str]:
    """Every value a step is given is one from the list, under a name it may go under."""
    if "env" in step and not isinstance(step["env"], dict):
        yield "a step's `env` is a map of names to values"
    own = {TOKEN: "GITHUB_TOKEN", DEFAULT_BRANCH: "DEFAULT_BRANCH"}
    for name, given in _map(step.get("env")).items():
        value = given if isinstance(given, str) else ""
        secret = SECRET.fullmatch(value)
        # The public log searches a step's lines for a secret by the name it was given under.
        if secret is not None or value in own:
            if name != (secret[1] if secret else own[value]):
                yield f"what is given as {name} must be given under its own name"
        elif "${{" not in value:
            yield (
                f"`{name}` is given a value that is written in the workflow. A step is given "
                "a secret, an input, a matrix value, an output, the token or the default "
                "branch, and nothing else"
            )
        elif IN_ENV.fullmatch(value) and name not in NAMES_GIVEN:
            names = ", ".join(sorted(NAMES_GIVEN))
            yield (
                f"`{name}` is not a name a step is given an input, a matrix value or an "
                f"output under. The names are: {names}"
            )


def _of_an_action(step: dict[str, Node], known: _Known) -> Iterator[str]:
    uses, given = str(step.get("uses")), _map(step.get("with"))
    action = uses.partition("@")[0]
    if action not in MUST_SET:
        yield "a data workflow uses no action but checkout and setup-uv"
        return
    if uses not in known.pinned:
        yield f"`{_short(uses)}` is not an action that ci.yml pins to a full commit"
    name = action.partition("/")[2]
    for key, value in MUST_SET[action].items():
        if given.get(key) != value:
            yield f"{name} must set {key}: {value}"
    if extra := sorted(set(given) - set(MUST_SET[action])):
        yield f"{name} may not be given `{extra[0]}`"
    if "env" in step:
        yield f"{name} is given no `env`"


def _of_the_expressions(job: dict[str, Node], known: _Known) -> Iterator[str]:
    """Every `${{ }}` of a job stands where it may, and is one on the list."""
    allowed: list[str] = []
    for step in _maps(job.get("steps")):
        for value in _strings(_map(step.get("env"))):
            secret = SECRET.fullmatch(value)
            if secret is not None and secret[1] not in SECRETS_OF.get(known.environment, ()):
                yield f"{secret[1]} is not a secret of {known.environment}"
            if secret or IN_ENV.fullmatch(value) or value in (TOKEN, DEFAULT_BRANCH):
                allowed.append(value)
    allowed += IN_NAME.findall(str(job.get("name", "")))
    outputs = _strings(_map(job.get("outputs")))
    allowed += [value for value in outputs if IN_OUTPUTS.fullmatch(value)]
    found = [match[0] for text in _strings(job) for match in EXPRESSION.finditer(text)]
    found += [text for text in _strings(job) if "${{" in text and not EXPRESSION.search(text)]
    for expression in found:
        if expression in allowed:
            allowed.remove(expression)
        else:
            yield f"`{_short(expression)}` is not an expression a data workflow may use there"


def _of_a_job(job: dict[str, Node], known: _Known) -> Iterator[str]:
    for key in sorted(set(job) - JOB_KEYS):
        if key == "env":
            yield "a secret is given to one step, never to a job: remove `env`"
        else:
            yield f"a job may not hold `{key}`"
    if job.get("runs-on") != RUNS_ON:
        yield f"must run on {RUNS_ON}, the platform of record"
    if not str(job.get("timeout-minutes", "")).isdigit():
        yield "must set timeout-minutes"

    listed = job.get("steps")
    steps = _maps(listed)
    runs = [step.get("run") for step in steps]
    asked = job.get("permissions")
    if not isinstance(asked, dict):
        yield "must say which permissions it asks for"
    may_ask = {"contents": "read"} | ({"actions": "read"} if SEARCH in runs else {})
    for name, level in sorted(_map(asked).items()):
        if may_ask.get(name) != level:
            yield f"may not ask for {name}: {level}"
    if "if" in job and (job["if"] != "always()" or SEARCH not in runs):
        yield "`if` is for the job that searches the log, as `if: always()`"

    given_a_secret = any(SECRET.search(text) for text in _strings(job))
    environment = job.get("environment")
    if given_a_secret and environment is None:
        yield "is given a secret and names no environment"
    if environment is not None and environment != known.environment:
        yield f"the environment must be {known.environment}, named for the workflow"
    if environment is not None and "if" in job:
        yield "a job that waits for approval may not run after a failure"

    if not steps or len(steps) != len(listed or ""):
        yield "`steps` must be a list of steps"
    yield from _of_the_order(steps)
    yield from _of_the_install(steps)
    for step in steps:
        for key in sorted(set(step) - STEP_KEYS):
            yield f"a step may not hold `{key}`"
        if "if" in step and not STEP_IF.fullmatch(str(step["if"])):
            yield "a step's `if` may only ask whether an input is empty"
        if ("uses" in step) == ("run" in step):
            yield "a step holds `uses` or `run`, and not both"
        elif "uses" in step:
            yield from _of_an_action(step, known)
        else:
            yield from _of_a_command(step, known)
    yield from _of_the_expressions(job, known)


def _of_the_install(steps: list[dict[str, Node]]) -> Iterator[str]:
    """A command that runs in what was installed comes after the line that installs."""
    runs = [str(step.get("run", "")) for step in steps]
    first = next((n for n, run in enumerate(runs) if f"{AS_INSTALLED} " in run), None)
    if first is not None and INSTALL not in runs[:first]:
        yield "runs a command of the project before it installs"


def _of_the_order(steps: list[dict[str, Node]]) -> Iterator[str]:
    """A secret is checked, and what is made from it hidden, before any step is given it."""
    given = [
        {
            match[1]
            for value in _strings(_map(step.get("env")))
            if (match := SECRET.fullmatch(value))
        }
        for step in steps
    ]
    first = next((n for n, names in enumerate(given) if names), None)
    if first is None:
        return
    check, read = steps[first].get("run"), any(given[first + 1 :])
    if check not in (MASK, MASK_MADE_UP) or "if" in steps[first]:
        yield "the first step that is given a secret must be the one that checks them"
    elif set().union(*given) - given[first]:
        yield "a step is given a secret that was not checked: give it to the first step too"
    elif check == MASK and not read:
        # A key that a workflow uses for nothing is a key that can only be lost.
        how = f"check them with `{MASK_MADE_UP}`"
        yield f"no step reads a secret, so the job holds made-up ones: {how}"
    elif check == MASK_MADE_UP and read:
        yield f"a step reads a secret, so none of them is made up: check them with `{MASK}`"


def _of_the_guard(jobs: dict[str, dict[str, Node]]) -> Iterator[str]:
    """One job checks the branch first, and every other job waits for it."""
    first_run = {
        name: next((step["run"] for step in _maps(job.get("steps")) if "run" in step), None)
        for name, job in jobs.items()
    }
    guards = {name for name, job in jobs.items() if first_run[name] == GUARD and "needs" not in job}
    if not guards:
        yield "no job checks that it runs on the default branch, as its first work"
        return

    def follows(name: str, seen: frozenset[str] = frozenset()) -> bool:
        if name in guards:
            return True
        needs = [need for need in _words(jobs.get(name, {}).get("needs")) if need not in seen]
        return any(follows(need, seen | {name}) for need in needs)

    for name in sorted(jobs):
        if not follows(name):
            yield f"{name}: does not wait for the job that checks the branch"


def problems_in(
    path: Path, text: str, pinned: frozenset[str], commands: frozenset[str], tools: frozenset[str]
) -> list[str]:
    """Every rule a data workflow breaks, as one line each. An address is counted, never shown."""
    found: list[str] = []
    if addresses := len(ADDRESS.findall(text)):
        found.append(f"holds an address ({addresses} found). The store's address is a secret")
    try:
        workflow = read_workflow(text)
    except Unreadable as error:
        return [f"{path}: {problem}" for problem in [*found, f"cannot be read: {error}"]]

    known = _Known(path.stem, pinned, commands, tools)
    found += _of_the_workflow(workflow)
    jobs = {name: _map(job) for name, job in _map(workflow.get("jobs")).items()}
    for name, job in jobs.items():
        found += [f"{name}: {problem}" for problem in _of_a_job(job, known)]
    found += _of_the_guard(jobs)
    if jobs and not any("environment" in job for job in jobs.values()):
        found.append(
            "no job waits for approval: a job that is given a secret names the environment"
        )
    return [f"{path}: {problem}" for problem in found]


def problems_in_other(path: Path, text: str, environments: frozenset[str]) -> list[str]:
    """What a workflow that is not a data workflow may not name."""
    found: list[str] = []
    if any(name in text for name in SECRET_NAMES):
        found.append(f"{path}: names a secret of a data workflow")
    whole = r"(?<![A-Za-z0-9_-]){}(?![A-Za-z0-9_-])"
    if any(re.search(whole.format(re.escape(name)), text) for name in environments):
        found.append(f"{path}: names the environment of a data workflow")
    return found


def _manifests(root: Path) -> list[Path]:
    """The manifest of the workspace, and of each package in it."""
    return [root / "pyproject.toml", *sorted(root.glob("*/*/pyproject.toml"))]


def _needed(manifest: Mapping[str, object]) -> Iterator[object]:
    """Everything a manifest says a package needs: to run, for an extra, to build, in a group."""
    project, build = _table(manifest.get("project")), _table(manifest.get("build-system"))
    lists = [project.get("dependencies", []), build.get("requires", [])]
    lists += _table(project.get("optional-dependencies")).values()
    lists += _table(manifest.get("dependency-groups")).values()
    for needed in lists:
        if not isinstance(needed, list):
            raise TypeError
        for item in cast(list[object], needed):
            # A group may take in another group, by its name.
            if not (
                isinstance(item, dict) and set(cast(dict[str, object], item)) == {"include-group"}
            ):
                yield item


def _table(node: object) -> dict[str, object]:
    if node is None:
        return {}
    if not isinstance(node, dict):
        raise TypeError
    return cast(dict[str, object], node)


def _of_a_manifest(manifest: Mapping[str, object]) -> Iterator[str]:
    settings = _table(_table(manifest.get("tool")).get("uv"))
    for name in sorted(set(settings) - OF_THE_WORKSPACE):
        yield (
            f"holds the setting `{name}` of the installer. A manifest holds what makes the "
            "workspace, and no other setting"
        )
    for name, source in sorted(_table(settings.get("sources")).items()):
        if source != FROM_THE_WORKSPACE:
            yield f"takes `{name}` from somewhere that is not this workspace or the index"
    if not all(isinstance(item, str) and NEEDED.fullmatch(item) for item in _needed(manifest)):
        yield "needs something that is given as a file or an address, and not by its name"


def problems_in_settings(root: Path) -> list[str]:
    """What the repository holds that could change what the line that installs brings.

    A setting is named, and what it is set to is never shown: it may be an address.
    """
    found: list[str] = []
    folders = sorted({root, *(manifest.parent for manifest in _manifests(root))})
    folders += sorted({folder.parent for folder in folders if folder != root} - {root})
    for folder in folders:
        if (folder / SETTINGS_FILE).exists():
            where = (folder / SETTINGS_FILE).relative_to(root).as_posix()
            found.append(
                f"{where}: is a settings file of the installer. What a run installs is said "
                "on the line that installs, and nowhere else"
            )
    for path in _manifests(root):
        if not path.is_file():
            continue
        where = path.relative_to(root).as_posix()
        try:
            manifest = tomllib.loads(path.read_text(encoding="utf-8"))
            found += [f"{where}: {problem}" for problem in _of_a_manifest(manifest)]
        except (OSError, ValueError, TypeError):
            found.append(f"{where}: cannot be read as a manifest")
    return found


def on_default_branch(environ: Mapping[str, str]) -> bool:
    """Whether this run is on the default branch. Asked as the first step of a run."""
    branch = environ.get("DEFAULT_BRANCH", "")
    return bool(branch) and environ.get("GITHUB_REF") == f"refs/heads/{branch}"


def commands_of(root: Path) -> frozenset[str]:
    """Every command the project's own packages define: console scripts, and modules that run."""
    found: set[str] = set()
    for manifest in sorted(root.glob("*/*/pyproject.toml")):
        project = tomllib.loads(manifest.read_text(encoding="utf-8"))
        found |= set(cast(dict[str, str], project.get("project", {}).get("scripts", {})))
        source = manifest.parent / "src"
        for module in sorted(source.glob("**/__main__.py")):
            found.add("python -m " + ".".join(module.parent.relative_to(source).parts))
    return frozenset(found)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_data_workflows", description=__doc__)
    parser.add_argument("--on-default-branch", action="store_true")
    args = parser.parse_args(argv)

    folder = ROOT / WORKFLOWS
    files = sorted([*folder.glob("*.yml"), *folder.glob("*.yaml")])
    data = [file for file in files if file.name.startswith("data-")]
    pinned = pinned_in((folder / "ci.yml").read_text(encoding="utf-8"))
    commands = commands_of(ROOT)
    tools = frozenset(file.name for file in (ROOT / "tools").glob("*.py"))
    environments = frozenset(file.stem for file in data)

    failures: list[str] = []
    for file in files:
        path, text = WORKFLOWS / file.name, file.read_text(encoding="utf-8", errors="replace")
        if file in data:
            failures += problems_in(path, text, pinned, commands, tools)
        else:
            failures += problems_in_other(path, text, environments)
    failures += problems_in_settings(ROOT)
    if args.on_default_branch and not on_default_branch(os.environ):
        failures.append("a data workflow runs on the default branch only. Start it from there")
    for failure in failures:
        print(f"error: {failure}", file=sys.stderr)
    if not failures:
        print(f"data-workflows: clean ({len(data)} checked)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
