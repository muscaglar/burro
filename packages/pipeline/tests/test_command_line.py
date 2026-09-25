"""The pipeline's command line: one command for each step, and help a newcomer can follow.

The Makefile and the hosted workflows run these same commands, so each is held
here to the arguments the command takes. Nothing here reaches a network or a
store, and every file is made up.
"""

import argparse
import re
import shlex
import subprocess
import sys
from pathlib import Path

import check_data_workflows
import pytest
from burro_pipeline import cli
from burro_pipeline.areas import cli as areas_cli
from burro_pipeline.assemble import cli as assemble_cli
from burro_pipeline.cells import cli as cells_cli
from burro_pipeline.command import IGNORED_BY_GIT, PROG, may_be_written
from burro_pipeline.fetch.sources import LISTS, load_list
from burro_pipeline.kept import cli as kept_cli
from burro_pipeline.release.cli import parser as release_parser

REPOSITORY = Path(__file__).parents[3]
FIXTURE = REPOSITORY / "data" / "fixtures" / "synthetic" / "syn-2026-09-23-01"
WORKFLOWS = REPOSITORY / ".github" / "workflows"
# In the order a build takes them. `why` is no step: it explains what fetch prints.
STEPS = [
    "fresh",
    "plan",
    "fetch",
    "by-hand",
    "receipts",
    "held",
    "describe",
    "seal",
    "cells",
    "travel",
    "draft",
    "preview",
    "check",
    "coverage",
    "keep",
    "take",
    "moved",
    "why",
]
# The steps a person runs from the Makefile.
MADE = ["plan", "fetch", "by-hand", "describe", "seal", "cells", "preview", "coverage"]
Printed = pytest.CaptureFixture[str]


def help_of(step: str, capsys: Printed) -> str:
    with pytest.raises(SystemExit) as stopped:
        cli.main([step, "--help"])
    out = capsys.readouterr()
    assert (stopped.value.code, out.err) == (0, "")
    return out.out


def options_of(step: str) -> list[argparse.Action]:
    """Every argument a step takes, but for `--help` itself."""
    actions = cli.parser_of(step)._actions  # pyright: ignore[reportPrivateUsage]
    return [action for action in actions if action.dest != "help"]


def test_there_is_one_command_for_each_step_in_the_order_a_build_takes_them(capsys: Printed):
    assert list(cli.STEPS) == STEPS
    assert cli.main(["--help"]) == 0
    out = capsys.readouterr()
    assert out.err == ""
    listed = [line.split()[0] for line in out.out.splitlines() if line.startswith("  ")]
    assert [name for name in listed if name in STEPS] == STEPS
    assert f"{PROG} STEP --help" in out.out


@pytest.mark.parametrize("step", STEPS)
def test_a_step_says_what_it_does_with_an_example_and_its_exit_codes(step: str, capsys: Printed):
    said = help_of(step, capsys)
    assert said.startswith(f"usage: {PROG} {step} ")
    summary = cli.STEPS[step].summary
    assert f"\n{summary}.\n" in said
    assert "\nexamples:\n" in said and "\nexit codes:\n  0  " in said
    assert f"\n  {PROG} {step}" in said


@pytest.mark.parametrize("step", STEPS)
def test_a_step_says_whether_it_reaches_a_network(step: str, capsys: Printed):
    """The one thing a newcomer must know before running a step for the first time."""
    said = " ".join(help_of(step, capsys).split())
    reaches = "the only step that reaches a publisher" in said
    assert reaches == (step == "fetch")
    assert reaches or "Reaches no network" in said or "Reaches no publisher" in said


@pytest.mark.parametrize("step", STEPS)
def test_every_argument_of_a_step_says_what_it_is_for(step: str):
    unsaid = [action.dest for action in options_of(step) if not (action.help or "").strip()]
    assert unsaid == []


@pytest.mark.parametrize("step", STEPS)
def test_every_example_in_a_steps_help_is_a_command_the_step_takes(step: str):
    examples = cli.STEPS[step].examples
    assert examples
    for example in examples:
        assert cli.parse([step, *shlex.split(example)]).command == step


def test_a_steps_help_needs_no_store_no_key_and_no_network(capsys: Printed):
    """Help is what a person reads first, on a machine where nothing is set up."""
    for step in STEPS:
        assert help_of(step, capsys)


def test_with_no_step_the_steps_are_listed_and_nothing_is_run(capsys: Printed):
    assert cli.main([]) == 2
    out = capsys.readouterr()
    assert out.out == ""
    assert all(f"  {step} " in out.err for step in STEPS)


def test_a_word_that_is_no_step_is_refused_and_not_repeated(capsys: Printed):
    assert cli.main(["zzyzx-parva", "--list", "m1"]) == 2
    out = capsys.readouterr()
    assert out.out == ""
    assert "zzyzx" not in out.err
    assert "is not a step" in out.err and f"{PROG} --help" in out.err


def test_it_runs_as_a_module():
    done = subprocess.run(  # noqa: S603  the interpreter running this test, and fixed arguments
        [sys.executable, "-m", "burro_pipeline", "check", str(FIXTURE), "--made-up"],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPOSITORY,
    )
    assert (done.returncode, done.stderr) == (0, "")
    assert done.stdout.startswith("step=check status=ok release=syn-2026-09-23-01 facts=3220 ")


def test_there_is_one_way_to_run_a_step():
    """A second command for the same step would be one more thing a workflow may name."""
    source = REPOSITORY / "packages" / "pipeline" / "src"
    allowed = check_data_workflows.commands_of(REPOSITORY)
    assert {command for command in allowed if command.startswith("python -m")} == {PROG}
    assert sorted(path.parent.name for path in source.rglob("__main__.py")) == ["burro_pipeline"]


# The Makefile


def recipes() -> dict[str, tuple[str, str]]:
    """Each target of the Makefile that says what it is for: what it says, and what it runs."""
    text = (REPOSITORY / "Makefile").read_text(encoding="utf-8")
    found = re.findall(r"^([a-z-]+):[^\n#]*## ([^\n]+)\n((?:\t[^\n]*\n)+)", text, re.MULTILINE)
    return {target: (says, runs) for target, says, runs in found}


@pytest.mark.parametrize("step", MADE)
def test_the_makefile_has_a_target_for_the_step_which_runs_the_step(step: str):
    says, runs = recipes()[step]
    assert runs == f"\tuv run {PROG} {step} $(or $(ARGS),--help)\n"
    assert "ARGS" in says


def test_a_target_run_with_nothing_more_prints_help_and_reaches_nothing():
    """`make fetch` alone must never start a fetch."""
    for step in MADE:
        assert recipes()[step][1].rstrip().endswith("$(or $(ARGS),--help)")


def test_every_command_the_makefile_runs_with_arguments_is_one_the_step_takes():
    text = (REPOSITORY / "Makefile").read_text(encoding="utf-8")
    joined = text.replace("\\\n", " ")
    commands = re.findall(rf"^\tuv run {re.escape(PROG)} ([^\n$]+)$", joined, re.MULTILINE)
    assert commands, "the fixture target runs the coverage step"
    for command in commands:
        words = shlex.split(command)
        assert cli.parse(words).command == words[0]


# The hosted workflows


def runs_of(node: check_data_workflows.Node) -> list[str]:
    """Every command a workflow runs, wherever in the file it stands."""
    if isinstance(node, str):
        return []
    if isinstance(node, list):
        return [run for item in node for run in runs_of(item)]
    here = [run] if isinstance(run := node.get("run"), str) else []
    return here + [run for item in node.values() for run in runs_of(item)]


def commands_of_the_workflows() -> list[tuple[str, list[str]]]:
    """Every command a data workflow runs behind the public log: its name, and its words."""
    found: list[tuple[str, list[str]]] = []
    for path in sorted(WORKFLOWS.glob("data-*.yml")):
        workflow = check_data_workflows.read_workflow(path.read_text(encoding="utf-8"))
        for run in runs_of(workflow):
            behind = check_data_workflows.BEHIND.fullmatch(run)
            if behind is not None:
                # A command runs in what the job installed, and installs nothing itself.
                runs = f" -- {check_data_workflows.AS_INSTALLED} "
                found.append((behind[2], shlex.split(run.split(runs, 1)[1])))
    return found


def filled(word: str) -> str:
    """A word of a command with what the run would put in place of each variable."""
    given = {
        "$LIST": "m1",
        "$ITEM": load_list("m1").files[0].item,
        "$RUNNER_TEMP": "scratch",
        "$RELEASE": "lon-2026-10-02-01",
        "$BUILT_AT": "2026-10-02T09:00:00Z",
    }
    for name, value in given.items():
        word = word.replace(name, value)
    assert "$" not in word, "a variable this test does not know"
    return word


def test_every_command_a_workflow_runs_is_one_the_pipeline_takes():
    commands = commands_of_the_workflows()
    assert {command for command, _ in commands} == {PROG, "burro-release"}
    for command, words in commands:
        arguments = [filled(word) for word in words[len(command.split()) :]]
        if command == PROG:
            assert cli.parse(arguments).command == arguments[0]
        else:
            assert release_parser().parse_args(arguments).command == arguments[0]


def test_a_workflow_runs_the_steps_it_is_named_for():
    steps = {words[3] for command, words in commands_of_the_workflows() if command == PROG}
    assert steps == {"held", "fetch", "travel", "draft", "preview", "keep"}


def test_a_build_of_london_takes_every_list_there_is():
    """A list that is added is a list the hosted build takes, in the same change.

    A file of a list that has no receipt is no part of a build, so a list that
    holds none adds nothing. A list that is left out would leave its measures
    out of what is served, and nothing would say so.
    """
    builds = [words for _, words in commands_of_the_workflows() if words[3:4] == ["preview"]]
    assert len(builds) == 2 and builds[0] == builds[1]
    (words, _) = builds
    taken = [words[n + 1] for n, word in enumerate(words) if word == "--list"]
    assert taken == sorted(path.stem for path in LISTS.glob("*.toml"))
    assert "--names" in words and "--work" in words


def test_the_lists_a_fetch_may_be_started_with_are_the_lists_there_are():
    text = (WORKFLOWS / "data-fetch.yml").read_text(encoding="utf-8")
    offered: check_data_workflows.Node = check_data_workflows.read_workflow(text)
    for key in ("on", "workflow_dispatch", "inputs", "list"):
        assert isinstance(offered, dict)
        offered = offered[key]
    assert isinstance(offered, dict)
    options = offered["options"]
    assert options == sorted(path.stem for path in LISTS.glob("*.toml"))
    assert isinstance(options, list) and offered["default"] in options


# Where a step may write what it makes from a publisher's file


def a_repository(folder: Path) -> Path:
    """A folder that is the top of a working copy, as far as a step looks: it holds `.git`."""
    (folder / ".git").mkdir(parents=True)
    return folder


def test_what_a_step_writes_goes_outside_the_repository_or_where_git_ignores(tmp_path: Path):
    root = a_repository(tmp_path / "repository")
    for folder in ("data/releases", "data/releases/lon-2026-10-02-01", "scratch/copies"):
        assert may_be_written(root / folder, root), folder
    for folder in ("", "out", "data", "data/locks", "data/receipts/copies", "docs/scratch"):
        assert not may_be_written(root / folder, root), folder
    assert may_be_written(tmp_path / "elsewhere", root)
    # A folder that is no repository holds nothing git would take in.
    assert may_be_written(tmp_path / "plain" / "out", tmp_path / "plain")


def test_every_folder_a_step_may_write_to_is_one_git_ignores():
    ignored = (REPOSITORY / ".gitignore").read_text(encoding="utf-8").splitlines()
    for folder in IGNORED_BY_GIT:
        assert f"{folder}/" in ignored, folder


def test_every_folder_an_example_writes_to_is_one_git_ignores():
    """The help says an example works as it stands. One left copies of files where git saw them."""
    for step in (*areas_cli.STEPS, *assemble_cli.STEPS, *cells_cli.STEPS, *kept_cli.STEPS):
        for example in step.examples:
            words = example.split()
            for flag in ("--out", "--work"):
                if flag in words:
                    folder = words[words.index(flag) + 1]
                    assert may_be_written(REPOSITORY / folder, REPOSITORY), (step.name, folder)
