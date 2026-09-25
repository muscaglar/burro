"""The rules a workflow that builds data is held to. Every workflow here is made up."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from check_data_workflows import (
    GUARD,
    INSTALL,
    INSTALLER,
    LOCK_TOOL,
    MASK,
    MASK_MADE_UP,
    NEVER_A_TRACEBACK,
    PACKAGES_BEFORE,
    STEPS_OF_A_RUN,
    Unreadable,
    pinned_in,
    problems_in,
    problems_in_other,
    problems_in_settings,
    read_workflow,
)
from public_log import CONTACT, RELEASES, SECRETS_OF, STORE

CHECKOUT = "actions/checkout@" + "a" * 40
SETUP_UV = "astral-sh/setup-uv@" + "b" * 40
CI = f"""
jobs:
  ci:
    steps:
      - uses: {CHECKOUT} # v1
      - uses: {SETUP_UV} # v1
"""
PINNED = pinned_in(CI)
COMMANDS = frozenset({"burro-release", "python -m burro_pipeline"})
TOOLS = frozenset(
    {
        "public_log.py",
        "canary.py",
        "check_data_workflows.py",
        "same_manifest.py",
        "release_lock.py",
    }
)
# The four secrets of the store, as a step is given them.
GIVEN = "".join(f"          {name}: ${{{{ secrets.{name} }}}}\n" for name in STORE)
ONE_GIVEN = "          BURRO_STORE_SECRET: ${{ secrets.BURRO_STORE_SECRET }}\n"

GOOD = f"""
name: data-build

on:
  workflow_dispatch:
    inputs:
      release:
        description: Which release to build
        type: choice
        options: [synthetic]
        default: synthetic
      item:
        description: One item, or nothing for all
        type: string
        default: ""

permissions: {{}}

concurrency:
  group: data-build
  cancel-in-progress: false

jobs:
  check:
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    permissions:
      contents: read
    steps:
      - uses: {CHECKOUT} # v1
        with:
          persist-credentials: false
      - uses: {SETUP_UV} # v1
        with:
          version: "0.12.17"
          enable-cache: false
      - name: Only on the default branch
        env:
          DEFAULT_BRANCH: ${{{{ github.event.repository.default_branch }}}}
        run: uv run --no-project python tools/check_data_workflows.py --on-default-branch
      - run: {INSTALL}
      - run: uv run --no-sync python tools/canary.py plant

  build:
    name: Build ${{{{ matrix.copy }}}}
    needs: check
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    environment: data-build
    permissions:
      contents: read
    strategy:
      fail-fast: false
      matrix:
        copy: [a, b]
    outputs:
      a: ${{{{ steps.manifest.outputs.a }}}}
      b: ${{{{ steps.manifest.outputs.b }}}}
    steps:
      - uses: {CHECKOUT} # v1
        with:
          persist-credentials: false
      - uses: {SETUP_UV} # v1
        with:
          version: "0.12.17"
          enable-cache: false
      - run: {INSTALL}
      - name: Hide what is made from a secret
        env:
{GIVEN}        run: uv run --no-project python tools/public_log.py mask
      - name: What the store holds, if a file was named to write it to
        if: inputs.item != ''
        env:
{GIVEN}          ITEM: ${{{{ inputs.item }}}}
        run: uv run --no-project python tools/public_log.py --step store -- uv run --no-sync python -m burro_pipeline held --out="$ITEM"
      - name: Build
        run: uv run --no-project python tools/public_log.py --step assemble -- uv run --no-sync burro-release build-synthetic --out "$RUNNER_TEMP/releases"
      - id: manifest
        env:
          COPY: ${{{{ matrix.copy }}}}
        run: uv run --no-project python tools/release_lock.py hash "$RUNNER_TEMP/releases"

  search:
    needs: [check, build]
    if: always()
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    permissions:
      contents: read
      actions: read
    steps:
      - uses: {CHECKOUT} # v1
        with:
          persist-credentials: false
      - uses: {SETUP_UV} # v1
        with:
          version: "0.12.17"
          enable-cache: false
      - env:
          GITHUB_TOKEN: ${{{{ github.token }}}}
        run: uv run --no-project python tools/canary.py search
"""  # noqa: E501
WORKFLOW = Path(".github/workflows/data-build.yml")
# The one step of the made-up workflow that reads the store.
HELD = 'python -m burro_pipeline held --out="$ITEM"'
THE_STEP_THAT_READS = (
    "      - name: What the store holds, if a file was named to write it to\n"
    "        if: inputs.item != ''\n"
    f"        env:\n{GIVEN}"
    "          ITEM: ${{ inputs.item }}\n"
    "        run: uv run --no-project python tools/public_log.py --step store -- "
    f"uv run --no-sync {HELD}\n"
)
INSTALL_STEP = f"      - run: {INSTALL}\n"


def problems(text: str, path: Path = WORKFLOW) -> list[str]:
    return problems_in(path, text, PINNED, COMMANDS, TOOLS)


def changed(old: str, new: str, count: int = 1) -> str:
    assert GOOD.count(old) >= count, f"the made-up workflow no longer holds {old!r}"
    return GOOD.replace(old, new, count)


def test_a_workflow_that_keeps_every_rule_passes():
    assert problems(GOOD) == []


# How it starts


@pytest.mark.parametrize(
    "trigger",
    [
        "  push:\n    branches: [main]\n",
        "  pull_request:\n",
        "  pull_request_target:\n",
        "  schedule:\n    - cron: '0 3 * * 1'\n",
        "  workflow_run:\n    workflows: [ci]\n",
        "  workflow_call:\n",
        "  repository_dispatch:\n",
    ],
)
def test_a_workflow_that_starts_on_anything_but_a_person_is_refused(trigger: str):
    text = changed("on:\n  workflow_dispatch:\n", f"on:\n{trigger}  workflow_dispatch:\n")
    assert any("started by hand and by nothing else" in p for p in problems(text))


@pytest.mark.parametrize("line", ["on: push", "on: [push, workflow_dispatch]", "on: {}"])
def test_a_trigger_written_on_one_line_is_refused(line: str):
    text = GOOD.replace("on:\n  workflow_dispatch:\n", f"{line}\nunused:\n", 1)
    assert any("started by hand and by nothing else" in p for p in problems(text))


def test_a_job_that_does_not_follow_the_branch_guard_is_refused():
    text = changed("    needs: check\n", "")
    assert any(
        "build: does not wait for the job that checks the branch" in p for p in problems(text)
    )


def test_the_branch_is_checked_before_anything_else_is_run():
    guard = (
        "      - name: Only on the default branch\n"
        "        env:\n"
        "          DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}\n"
        f"        run: {GUARD}\n"
    )
    text = changed(guard + INSTALL_STEP, INSTALL_STEP + guard)
    assert any("no job checks that it runs on the default branch" in p for p in problems(text))


def test_a_workflow_with_no_branch_guard_is_refused():
    text = changed(" --on-default-branch", "")
    assert any("no job checks that it runs on the default branch" in p for p in problems(text))


def test_a_job_may_run_after_a_failure_only_to_search_the_log():
    text = changed("    needs: check\n", "    needs: check\n    if: always()\n")
    assert any("build: `if` is for the job that searches the log" in p for p in problems(text))


# The environment and its secrets


def test_a_job_given_a_secret_must_name_the_environment():
    text = changed("    environment: data-build\n", "")
    assert any("build: is given a secret and names no environment" in p for p in problems(text))


def test_the_environment_is_named_for_the_workflow():
    text = changed("    environment: data-build\n", "    environment: production\n")
    assert any("build: the environment must be data-build" in p for p in problems(text))


def test_a_workflow_with_no_job_in_the_environment_is_refused():
    text = changed("    environment: data-build\n", "").replace("${{ secrets.", "${{ inputs.")
    assert any("no job waits for approval" in p for p in problems(text))


def test_a_secret_the_environment_is_not_known_to_hold_is_refused():
    text = changed("secrets.BURRO_STORE_SECRET", "secrets.SOMETHING_ELSE")
    assert any("SOMETHING_ELSE is not a secret of data-build" in p for p in problems(text))


@pytest.mark.parametrize(
    "expression",
    [
        "${{ toJSON(secrets) }}",
        "${{ secrets }}",
        "${{ secrets['BURRO_STORE_SECRET'] }}",
        "${{ toJSON(env) }}",
        "${{ toJSON(github) }}",
        "${{ github.event.inputs.release }}",
        "${{ vars.ANYTHING }}",
    ],
)
def test_an_expression_that_is_not_on_the_list_is_refused(expression: str):
    text = changed("${{ secrets.BURRO_STORE_SECRET }}", expression)
    assert any("is not an expression a data workflow may use" in p for p in problems(text))


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("  group: data-build\n", "  group: data-build-${{ github.ref }}\n"),
        ("name: data-build\n", "name: data-build ${{ inputs.release }}\n"),
        ("        default: synthetic\n", "        default: ${{ github.actor }}\n"),
    ],
)
def test_an_expression_outside_a_job_is_refused(old: str, new: str):
    assert any("outside a job" in p for p in problems(changed(old, new)))


def test_a_secret_of_another_environment_is_refused():
    text = changed("secrets.BURRO_STORE_SECRET", "secrets.BURRO_FETCH_CONTACT")
    assert any("BURRO_FETCH_CONTACT is not a secret of data-build" in p for p in problems(text))
    fetch = Path(".github/workflows/data-fetch.yml")
    found = problems(text.replace("environment: data-build", "environment: data-fetch"), fetch)
    assert not any("is not a secret of" in p for p in found)


def test_the_secrets_are_checked_before_any_step_is_given_one():
    mask = "        run: uv run --no-project python tools/public_log.py mask\n"
    behind = mask.replace("mask", "--step store -- uv run --no-sync burro-release check x")
    assert any(
        "build: the first step that is given a secret" in p for p in problems(changed(mask, behind))
    )


def test_a_secret_that_was_not_checked_is_given_to_no_step():
    checked = f"{GIVEN}        run: {MASK}\n"
    text = changed(checked, checked.replace(ONE_GIVEN, ""))
    assert any("build: a step is given a secret that was not checked" in p for p in problems(text))


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("          BURRO_STORE_SECRET: ${{ secrets.", "          ANOTHER_NAME: ${{ secrets."),
        (
            "          BURRO_STORE_SECRET: ${{ secrets.",
            "          BURRO_FETCH_CONTACT: ${{ secrets.",
        ),
        (
            "          GITHUB_TOKEN: ${{ github.token }}",
            "          ANOTHER_NAME: ${{ github.token }}",
        ),
    ],
)
def test_a_secret_is_given_under_its_own_name(old: str, new: str):
    # The public log searches for a secret by the name it is given under.
    assert any("must be given under its own name" in p for p in problems(changed(old, new)))


def test_a_secret_set_for_a_whole_job_is_refused():
    text = changed(
        "    environment: data-build\n",
        "    environment: data-build\n"
        "    env:\n      BURRO_STORE_SECRET: ${{ secrets.BURRO_STORE_SECRET }}\n",
    )
    assert any("a secret is given to one step, never to a job" in p for p in problems(text))


def test_a_secret_set_for_the_whole_workflow_is_refused():
    text = changed(
        "permissions: {}\n",
        "permissions: {}\n\nenv:\n  BURRO_STORE_SECRET: ${{ secrets.BURRO_STORE_SECRET }}\n",
    )
    assert any("a secret is given to one step, never to a workflow" in p for p in problems(text))


def test_a_step_given_a_secret_must_run_behind_the_public_log():
    text = changed(
        "tools/public_log.py --step store -- uv run --no-sync python -m burro_pipeline held",
        "tools/same_manifest.py hash",
    )
    assert any("is given a secret and does not run behind" in p for p in problems(text))


# What no public log guards, in a job that holds a key

# What the made-up workflow hashes its build with: a tool that is on the list.
HASHED = 'tools/release_lock.py hash "$RUNNER_TEMP/releases"'
NOT_GUARDED = "is not on the list of the tools that never print a traceback"


@pytest.mark.parametrize(
    ("run", "said"),
    [
        ('tools/same_manifest.py hash "$RUNNER_TEMP/releases"', "same_manifest.py hash"),
        ('tools/release_lock.py carried "$RUNNER_TEMP/releases"', "release_lock.py carried"),
        ('tools/release_lock.py "$RUNNER_TEMP/releases"', "release_lock.py"),
        ("tools/canary.py plant", "canary.py plant"),
        ("tools/check_data_workflows.py", "check_data_workflows.py"),
    ],
)
def test_a_job_that_holds_a_key_runs_with_no_public_log_only_a_tool_that_is_on_the_list(
    run: str, said: str
):
    """A job that holds a key reads what is real, and what a tool of it prints is what
    the log of the run holds. A tool that a test holds to no traceback is on the list."""
    found = problems(changed(HASHED, run))
    assert f"{WORKFLOW}: build: `{said}` {NOT_GUARDED}" in [
        problem.split(", and runs with no public log")[0] for problem in found
    ]


def test_the_list_is_of_a_tool_and_of_what_it_does():
    assert LOCK_TOOL in TOOLS and NEVER_A_TRACEBACK[LOCK_TOOL] == {"hash", "compare", "show"}
    for does in NEVER_A_TRACEBACK[LOCK_TOOL]:
        found = problems(changed(HASHED, HASHED.replace(" hash ", f" {does} ")))
        assert not [problem for problem in found if NOT_GUARDED in problem], does


def test_a_job_that_holds_made_up_secrets_may_run_a_tool_that_is_on_no_list():
    """No step of it reads a store, so what it builds is made up: nothing it could print
    is of a real place. It is how the made-up city is built and compared."""
    made_up = changed(THE_STEP_THAT_READS, "").replace(f"run: {MASK}\n", f"run: {MASK_MADE_UP}\n")
    bare = made_up.replace(HASHED, 'tools/same_manifest.py hash "$RUNNER_TEMP/releases"')
    assert bare != made_up and problems(bare) == []
    # Nor is it asked of a job that is given nothing at all.
    assert "tools/canary.py plant" in GOOD and problems(GOOD) == []


def test_a_tool_behind_the_public_log_is_asked_nothing_more():
    assert not [problem for problem in problems(GOOD) if NOT_GUARDED in problem]
    assert GOOD.count("tools/public_log.py --step") == 2


def test_the_token_is_given_only_to_the_step_that_searches_the_log():
    text = changed("${{ secrets.BURRO_STORE_SECRET }}", "${{ github.token }}")
    assert any("the token is for the step that searches the log" in p for p in problems(text))


# Permissions


@pytest.mark.parametrize(
    "permissions",
    [
        "permissions:\n  contents: read\n",
        "permissions: write-all\n",
        "permissions: read-all\n",
    ],
)
def test_the_workflow_itself_asks_for_no_permission(permissions: str):
    text = changed("permissions: {}\n", permissions)
    assert any("the workflow must ask for no permission" in p for p in problems(text))


def test_a_workflow_that_says_nothing_of_permissions_is_refused():
    text = changed("permissions: {}\n", "")
    assert any("the workflow must ask for no permission" in p for p in problems(text))


@pytest.mark.parametrize(
    "asked",
    ["contents: write", "id-token: write", "actions: write", "packages: read", "issues: write"],
)
def test_a_job_that_asks_for_more_than_it_needs_is_refused(asked: str):
    text = changed("      contents: read\n", f"      {asked}\n")
    assert any(f"check: may not ask for {asked}" in p for p in problems(text))


def test_only_the_job_that_searches_the_log_may_read_it():
    text = changed("      contents: read\n", "      contents: read\n      actions: read\n")
    assert any("check: may not ask for actions: read" in p for p in problems(text))


def test_a_job_that_says_nothing_of_permissions_is_refused():
    text = changed("    permissions:\n      contents: read\n", "")
    assert any("check: must say which permissions it asks for" in p for p in problems(text))


# Actions


def test_an_action_pinned_to_a_tag_is_refused():
    text = changed(CHECKOUT, "actions/checkout@v7")
    assert any("is not an action that ci.yml pins" in p for p in problems(text))


def test_an_action_pinned_to_another_commit_is_refused():
    text = changed(CHECKOUT, "actions/checkout@" + "c" * 40)
    assert any("is not an action that ci.yml pins" in p for p in problems(text))


@pytest.mark.parametrize(
    "action",
    [
        "actions/upload-artifact",
        "actions/cache",
        "actions/cache/save",
        "softprops/action-gh-release",
        "actions/upload-pages-artifact",
        "actions/attest-build-provenance",
    ],
)
def test_an_action_that_uploads_is_refused_even_when_ci_pins_it(action: str):
    pinned = f"{action}@{'d' * 40}"
    text = changed(f"      - uses: {CHECKOUT} # v1\n", f"      - uses: {pinned}\n")
    found = problems_in(WORKFLOW, text, PINNED | {pinned}, COMMANDS, TOOLS)
    assert any("a data workflow uses no action but" in p for p in found)


def test_a_checkout_that_keeps_its_credentials_is_refused():
    text = changed("          persist-credentials: false\n", "          fetch-depth: 1\n")
    assert any("checkout must set persist-credentials: false" in p for p in problems(text))


@pytest.mark.parametrize("cache", ["          enable-cache: true\n", ""])
def test_a_package_cache_is_refused(cache: str):
    text = changed("          enable-cache: false\n", cache)
    assert any("setup-uv must set enable-cache: false" in p for p in problems(text))


# What a step may run


@pytest.mark.parametrize(
    "command",
    [
        "env",
        "printenv",
        "export -p",
        "set",
        "set -x",
        "echo $BURRO_STORE_SECRET",
        'echo "${{ secrets.BURRO_STORE_SECRET }}"',
        f"{INSTALL} && env",
        f"{INSTALL}; printenv",
        f"{INSTALL} | tee log.txt",
        f"{INSTALL} > log.txt",
        "uv run --no-project python tools/canary.py plant $(env)",
        "uv run --no-project python tools/canary.py plant `env`",
        "bash -x tools/pre-commit",
        "python -c 'import os; print(os.environ)'",
        "gh release upload v1 release.zip",
        "curl --data @release.zip example.test",
        "uv run --no-project python tools/nothing_here.py",
        "uv run burro-release build-synthetic --out out",
    ],
)
def test_a_step_that_could_print_the_environment_or_send_a_file_is_refused(command: str):
    text = changed(INSTALL_STEP, f"      - run: {command}\n")
    assert any("is not a command a data workflow may run" in p for p in problems(text))


@pytest.mark.parametrize(
    "command",
    [
        "env",
        "printenv BURRO_STORE_SECRET",
        "python -c 'import os; print(os.environ)'",
        "uv run --no-sync burro-nothing fetch",
        "uv run --no-sync python tools/canary.py plant",
    ],
)
def test_a_command_behind_the_public_log_must_be_one_the_project_defines(command: str):
    text = changed("uv run --no-sync burro-release build-synthetic", command)
    assert any("is not a command a data workflow may run" in p for p in problems(text))


@pytest.mark.parametrize(
    "word",
    [
        '"$BURRO_STORE_ENDPOINT"',
        '"$GITHUB_TOKEN"',
        '"$HOME"',
        "$ITEM",
        '"${ITEM}"',
        '"$ITEM$(env)"',
        "'$ITEM'",
    ],
)
def test_a_word_of_a_command_comes_from_an_input_and_never_from_a_secret(word: str):
    text = changed('--out="$ITEM"', f"--out={word}")
    assert any("is not a command a data workflow may run" in p for p in problems(text))


@pytest.mark.parametrize(
    "module", ["http.server", "burro_pipeline.nothing", "burro_pipeline.fetch", "pip"]
)
def test_a_module_behind_the_public_log_must_be_one_the_project_runs(module: str):
    text = changed("python -m burro_pipeline", f"python -m {module}")
    assert any("is not a command a data workflow may run" in p for p in problems(text))


@pytest.mark.parametrize(
    "condition",
    [
        "always()",
        "failure()",
        "github.ref == 'refs/heads/other'",
        "secrets.BURRO_STORE_SECRET != ''",
        "inputs.item != '' || always()",
        "${{ inputs.item != '' }}",
        "contains(toJSON(secrets), inputs.item)",
    ],
)
def test_a_step_is_left_out_only_by_whether_an_input_is_empty(condition: str):
    text = changed("        if: inputs.item != ''\n", f"        if: {condition}\n")
    assert any("a step's `if` may only ask whether an input is empty" in p for p in problems(text))


def test_a_long_command_that_is_not_allowed_is_refused_at_once():
    # A pattern that tries every way to split a long word would never come back.
    text = changed(
        INSTALL_STEP, f"      - run: uv run --no-sync python tools/canary.py {'a' * 200};\n"
    )
    assert any("is not a command a data workflow may run" in p for p in problems(text))
    behind = changed('--out="$ITEM"', f"--out={'a=' * 200};")
    assert any("is not a command a data workflow may run" in p for p in problems(behind))


def test_a_step_written_over_several_lines_is_not_read(tmp_path: Path):
    text = changed(INSTALL_STEP, "      - run: |\n          uv sync\n          env\n")
    assert any("cannot be read" in p for p in problems(text))


def test_a_shell_of_the_steps_own_choosing_is_refused():
    text = changed(INSTALL_STEP, f"{INSTALL_STEP}        shell: bash -x {{0}}\n")
    assert any("a step may not hold `shell`" in p for p in problems(text))


def test_a_job_that_runs_in_a_container_is_refused():
    text = changed(
        "    environment: data-build\n",
        "    environment: data-build\n    container: example.test/image\n",
    )
    assert any("a job may not hold `container`" in p for p in problems(text))


def test_a_job_must_run_on_the_platform_of_record_and_stop_in_time():
    assert any("must run on ubuntu-24.04" in p for p in problems(changed("ubuntu-24.04", "x")))
    text = changed("    timeout-minutes: 10\n", "")
    assert any("check: must set timeout-minutes" in p for p in problems(text))


def test_a_second_run_waits_for_the_first():
    text = changed("  cancel-in-progress: false\n", "  cancel-in-progress: true\n")
    assert any("one run at a time" in p for p in problems(text))


# A secret is given to the step that reads it, and to no other


def test_a_step_that_reads_no_secret_is_given_none():
    # The synthetic release reads nothing, so the step that builds it holds no key.
    text = changed("      - name: Build\n", f"      - name: Build\n        env:\n{ONE_GIVEN}")
    found = problems(text)
    assert any("build: `build-synthetic` is given BURRO_STORE_SECRET" in p for p in found)
    assert any("does not read" in p for p in found)


def test_a_step_is_given_every_secret_it_reads():
    # Found before a run is started, and not by a step that stops for want of a key.
    env = f"        env:\n{GIVEN}          ITEM"
    less = env.replace("          BURRO_STORE_KEY_ID: ${{ secrets.BURRO_STORE_KEY_ID }}\n", "")
    assert less != env
    text = changed(env, less)
    assert any(
        "build: `held` reads BURRO_STORE_KEY_ID, and is not given it" in p for p in problems(text)
    )


def test_what_each_step_reads_is_what_its_help_says_it_reads():
    from burro_pipeline import cli
    from burro_pipeline.fetch import cli as fetch
    from burro_pipeline.kept import cli as kept

    for name, reads in STEPS_OF_A_RUN["python -m burro_pipeline"].items():
        about = cli.STEPS[name].about
        assert (fetch.THE_STORE in about) == (set(STORE) <= set(reads)), name
        assert (fetch.CONTACT in about) == (CONTACT in reads), name
        # The bucket of releases is another store, with names of its own.
        assert (kept.THE_STORE in about) == (set(RELEASES) <= set(reads)), name
        assert set(reads) <= {*STORE, CONTACT, *RELEASES}
        assert not (set(STORE) & set(reads) and set(RELEASES) & set(reads)), name
    assert STEPS_OF_A_RUN["python -m burro_pipeline"]["fetch"] == SECRETS_OF["data-fetch"]
    assert all(reads == () for reads in STEPS_OF_A_RUN["burro-release"].values())


def test_a_job_in_which_no_step_reads_a_secret_is_given_made_up_ones():
    # A key that a workflow uses for nothing is a key that can only be lost.
    none_reads = changed(THE_STEP_THAT_READS, "")
    assert any(
        "build: no step reads a secret, so the job holds made-up ones" in p
        for p in problems(none_reads)
    )
    assert problems(none_reads.replace(f"run: {MASK}\n", f"run: {MASK_MADE_UP}\n")) == []


def test_a_job_in_which_a_step_reads_a_secret_is_not_given_made_up_ones():
    text = changed(f"run: {MASK}\n", f"run: {MASK_MADE_UP}\n")
    assert any(
        "build: a step reads a secret, so none of them is made up" in p for p in problems(text)
    )


def test_the_check_of_made_up_secrets_is_held_to_the_same_rules_as_the_check_of_real_ones():
    made_up = changed(THE_STEP_THAT_READS, "").replace(f"run: {MASK}\n", f"run: {MASK_MADE_UP}\n")
    assert problems(made_up) == []
    other = made_up.replace("secrets.BURRO_STORE_SECRET", "secrets.SOMETHING_ELSE")
    assert any("SOMETHING_ELSE is not a secret of data-build" in p for p in problems(other))
    more = made_up.replace(f"run: {MASK_MADE_UP}\n", f"run: {MASK_MADE_UP} --real\n")
    assert any("is not a command a data workflow may run" in p for p in problems(more))


# The steps a run may run


def test_no_run_describes_a_file():
    # What `describe` prints holds names from a file's own layout, and where it cannot
    # tell a row of names from a row of data, that may be a row.
    text = changed(HELD, 'python -m burro_pipeline describe "$ITEM"')
    assert any("`describe` is for a person's own machine" in p for p in problems(text))
    inside = changed(HELD, 'python -m burro_pipeline describe --inside "$ITEM"')
    assert any("`describe` is for a person's own machine" in p for p in problems(inside))


@pytest.mark.parametrize(
    "step", ["by-hand", "receipts", "why", "plan", "seal", "check", "coverage", "zzyzx"]
)
def test_a_run_runs_no_step_of_the_pipeline_that_is_not_on_the_list(step: str):
    text = changed(HELD, f'python -m burro_pipeline {step} "$ITEM"')
    assert any(f"`{step}` is not a step a data workflow runs" in p for p in problems(text))


def test_a_step_on_the_list_of_one_command_is_not_on_the_list_of_another():
    text = changed("burro-release build-synthetic", "burro-release fetch")
    assert any("`fetch` is not a step a data workflow runs" in p for p in problems(text))


@pytest.mark.parametrize("words", ['--out="$ITEM"', '--out="$ITEM" held', '"$ITEM" describe', ""])
def test_a_command_behind_the_public_log_names_its_step_first(words: str):
    text = changed(HELD, f"python -m burro_pipeline {words}".rstrip())
    assert any("is not a command a data workflow may run" in p for p in problems(text))


def test_every_step_a_run_may_run_is_a_step_there_is():
    from burro_pipeline import cli
    from burro_pipeline.release.cli import parser

    commands = next(action for action in parser()._actions if action.dest == "command")  # pyright: ignore[reportPrivateUsage]
    assert set(STEPS_OF_A_RUN) == COMMANDS
    assert set(STEPS_OF_A_RUN["python -m burro_pipeline"]) <= set(cli.ORDER)
    assert set(STEPS_OF_A_RUN["burro-release"]) <= set(commands.choices or ())
    assert "describe" in cli.ORDER


# What is installed


def test_the_made_up_workflow_installs_as_this_file_says():
    assert GOOD.count(INSTALL_STEP) == 2


@pytest.mark.parametrize(
    "line",
    [
        "uv sync",
        "uv sync --all-packages",
        "uv sync --locked",
        "uv sync --package burro-pipeline",
        "uv sync --package burro-pipeline --no-dev",
        f"uv sync --package burro-pipeline --exclude-newer {PACKAGES_BEFORE}",
        f"uv sync --package burro-api --no-dev --exclude-newer {PACKAGES_BEFORE}",
        f"uv sync --all-packages --no-dev --exclude-newer {PACKAGES_BEFORE}",
        "uv sync --package burro-pipeline --no-dev --exclude-newer 2099-01-01T00:00:00Z",
        "uv sync --package burro-pipeline --no-dev --exclude-newer false",
        f"{INSTALL} --upgrade",
        f"{INSTALL} --group dev",
        f"{INSTALL} --all-groups",
        f"{INSTALL} --exclude-newer-package pydantic=false",
        f"{INSTALL} --index example.test/simple",
        f"{INSTALL} --default-index example.test/simple",
    ],
)
def test_a_job_installs_the_pipeline_alone_and_nothing_newer_than_the_day_stated(line: str):
    text = changed(INSTALL_STEP, f"      - run: {line}\n")
    assert any("A job installs with one line, and no other" in p for p in problems(text))


@pytest.mark.parametrize(
    "line",
    [
        "uv pip install pydantic",
        "uv pip install -r requirements.txt",
        "uv add pydantic",
        "uv tool install ruff",
        "uvx ruff",
        "uv lock --upgrade",
        "pip install pydantic",
        "python -m pip install pydantic",
    ],
)
def test_nothing_is_installed_by_another_command(line: str):
    text = changed(INSTALL_STEP, f"      - run: {line}\n")
    assert any("is not a command a data workflow may run" in p for p in problems(text))


@pytest.mark.parametrize(
    "command",
    [
        "uv run python tools/canary.py plant",
        "uv run --with requests python tools/canary.py plant",
        "uv run --no-sync --with requests python tools/canary.py plant",
        "uv run --with requests --no-sync python tools/canary.py plant",
        "uv run --all-packages python tools/canary.py plant",
        "uv run --isolated python tools/canary.py plant",
        "uv run --group dev python tools/canary.py plant",
        "uv run --no-sync --no-project python tools/canary.py plant",
    ],
)
def test_a_command_is_run_in_what_was_installed_and_installs_nothing(command: str):
    # A plain `uv run` brings the environment up to date first: every package of the
    # workspace, the development group included, each at its newest.
    text = changed("uv run --no-sync python tools/canary.py plant", command)
    assert any("is not a command a data workflow may run" in p for p in problems(text))


@pytest.mark.parametrize(
    "run",
    [
        "uv run burro-release build-synthetic",
        "uv run --no-project burro-release build-synthetic",
        "uv run --with requests burro-release build-synthetic",
        "uv run --no-sync --with requests burro-release build-synthetic",
        "uv run --all-packages burro-release build-synthetic",
    ],
)
def test_a_command_behind_the_public_log_installs_nothing(run: str):
    text = changed("uv run --no-sync burro-release build-synthetic", run)
    assert any("is not a command a data workflow may run" in p for p in problems(text))


def test_a_job_that_runs_in_what_was_installed_installs_first():
    # Found before a run is started, and not by a step that cannot find the pipeline.
    text = changed(INSTALL_STEP, "")
    assert any(
        "check: runs a command of the project before it installs" in p for p in problems(text)
    )
    after = changed(
        f"{INSTALL_STEP}      - run: uv run --no-sync python tools/canary.py plant\n",
        f"      - run: uv run --no-sync python tools/canary.py plant\n{INSTALL_STEP}",
    )
    assert any(
        "check: runs a command of the project before it installs" in p for p in problems(after)
    )


# What can change what the line installs, and is not on the line


@pytest.mark.parametrize(
    "given",
    [
        "UV_EXCLUDE_NEWER: 2099-01-01T00:00:00Z",
        "UV_EXCLUDE_NEWER: false",
        "UV_EXCLUDE_NEWER_PACKAGE: pydantic=2099-01-01T00:00:00Z",
        "UV_CONFIG_FILE: tools/other.toml",
        "UV_INDEX: wheels",
        "UV_DEFAULT_INDEX: wheels",
        "UV_FIND_LINKS: wheels",
        "UV_OVERRIDE: overrides.txt",
        "UV_CONSTRAINT: constraints.txt",
        "UV_PROJECT: elsewhere",
        "UV_PRERELEASE: allow",
        "UV_NO_SYNC: 0",
        "PIP_INDEX_URL: example.test/simple",
        "PYTHONPATH: elsewhere",
        "PYTHONSTARTUP: tools/canary.py",
        "BASH_ENV: tools/pre-commit",
        "XDG_CONFIG_HOME: elsewhere",
        "HOME: elsewhere",
        "PATH: elsewhere",
        "COPY: a",
        "ITEM: 'oa-lookup'",
        'LIST: ""',
    ],
)
@pytest.mark.parametrize(
    "step",
    [
        INSTALL_STEP,
        "      - run: uv run --no-sync python tools/canary.py plant\n",
        "      - name: Build\n        run: uv run --no-project python tools/public_log.py",
    ],
    ids=["the step that installs", "a tool", "a step behind the public log"],
)
def test_a_step_is_given_no_value_that_is_written_in_the_workflow(given: str, step: str):
    # A setting of the installer, of Python or of the shell can be given as plainly as this.
    first, _, rest = step.partition("run: ")
    text = changed(step, f"{first}env:\n          {given}\n        run: {rest}")
    name = given.partition(":")[0]
    assert any(
        f"`{name}` is given a value that is written in the workflow" in p for p in problems(text)
    )


@pytest.mark.parametrize(
    "name",
    [
        "UV_CONFIG_FILE",
        "UV_EXCLUDE_NEWER",
        "UV_EXCLUDE_NEWER_PACKAGE",
        "UV_INDEX",
        "UV_FIND_LINKS",
        "UV_PROJECT",
        "PYTHONPATH",
        "BASH_ENV",
        "HOME",
        "PATH",
        "DEFAULT_BRANCH",
        "GITHUB_TOKEN",
        "GITHUB_REF",
        "RUNNER_TEMP",
        "BURRO_FETCH_CONTACT",
        "item",
        "ANYTHING_ELSE",
    ],
)
@pytest.mark.parametrize(
    "value",
    ["${{ inputs.item }}", "${{ matrix.copy }}", "${{ needs.build.outputs.a }}"],
    ids=["an input", "a matrix value", "an output"],
)
def test_what_comes_from_an_input_is_given_under_a_name_on_the_list(name: str, value: str):
    # Whoever starts a run types an input. Under the right name it would be a setting.
    text = changed("          ITEM: ${{ inputs.item }}\n", f"          {name}: {value}\n")
    found = problems(text)
    assert any(f"`{name}` is not a name a step is given" in p for p in found), found


def test_a_name_on_the_list_may_stand_in_a_command():
    text = changed("          ITEM: ${{ inputs.item }}\n", "          LIST: ${{ inputs.item }}\n")
    assert problems(text.replace('--out="$ITEM"', '--out="$LIST"')) == []


def test_the_step_that_installs_is_given_nothing():
    for given in ("ITEM: ${{ inputs.item }}", "COPY: ${{ matrix.copy }}"):
        text = changed(INSTALL_STEP, f"      - env:\n          {given}\n        run: {INSTALL}\n")
        assert any("the step that installs is given nothing" in p for p in problems(text))


@pytest.mark.parametrize(
    "given",
    [
        "          DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}\n",
        "          UV_CONFIG_FILE: ${{ github.event.repository.default_branch }}\n",
    ],
)
def test_the_default_branch_is_given_to_the_step_that_checks_it_and_to_no_other(given: str):
    text = changed(
        "      - run: uv run --no-sync python tools/canary.py plant\n",
        f"      - env:\n{given}        run: uv run --no-sync python tools/canary.py plant\n",
    )
    assert any(
        "the default branch is for the step that checks the branch" in p for p in problems(text)
    )


def test_the_default_branch_is_given_under_its_own_name():
    text = changed("          DEFAULT_BRANCH: ${{ github", "          UV_PROJECT: ${{ github")
    assert any("must be given under its own name" in p for p in problems(text))


@pytest.mark.parametrize("env", ["        env: UV_CONFIG_FILE\n", "        env: [a, b]\n"])
def test_what_a_step_is_given_is_written_as_names_and_values(env: str):
    text = changed(INSTALL_STEP, f"      - run: {INSTALL}\n{env}")
    assert any("a step's `env` is a map of names to values" in p for p in problems(text))


@pytest.mark.parametrize(
    "version",
    [
        "          version: latest\n",
        '          version: "0.12.18"\n',
        '          version: "0.4.0"\n',
        '          version: ">=0.12.17"\n',
        '          version: "0.12.x"\n',
        "",
    ],
)
def test_the_installer_is_set_up_at_the_one_version_stated(version: str):
    # Another version may read the line another way, and `latest` is whatever is newest.
    assert INSTALLER == "0.12.17"
    text = changed(f'          version: "{INSTALLER}"\n', version)
    assert any(f"check: setup-uv must set version: {INSTALLER}" in p for p in problems(text))


# The installer reads more than the line: a settings file, and a table in a manifest.

TOP = """\
[project]
name = "made-up"
version = "0.0.0"
requires-python = ">=3.13"
dependencies = []

[dependency-groups]
dev = ["made-up-core", "pytest>=8", { include-group = "lint" }]
lint = []

[tool.uv]
package = false

[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
made-up-core = { workspace = true }

[tool.ruff]
line-length = 100
"""
MEMBER = """\
[project]
name = "made-up-core"
version = "0.0.0"
dependencies = ["pydantic>=2.9", "made-up-other[extra]>=1,<2; python_version >= '3.13'"]

[project.optional-dependencies]
more = ["made-up-more"]

[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"
"""


def a_workspace(root: Path, top: str = TOP, member: str = MEMBER) -> Path:
    (root / "packages" / "core").mkdir(parents=True)
    (root / "pyproject.toml").write_text(top, encoding="utf-8")
    (root / "packages" / "core" / "pyproject.toml").write_text(member, encoding="utf-8")
    return root


def test_a_workspace_that_holds_no_setting_of_the_installer_passes(tmp_path: Path):
    assert problems_in_settings(a_workspace(tmp_path)) == []


@pytest.mark.parametrize("where", ["uv.toml", "packages/core/uv.toml", "packages/uv.toml"])
@pytest.mark.parametrize(
    "held", ['exclude-newer-package = { pydantic = "2099-01-01T00:00:00Z" }\n', ""]
)
def test_a_settings_file_of_the_installer_is_refused(tmp_path: Path, where: str, held: str):
    # Such a file can give one package a day of its own, and the line's day then holds it no more.
    (a_workspace(tmp_path) / where).write_text(held, encoding="utf-8")
    assert problems_in_settings(tmp_path) == [
        f"{where}: is a settings file of the installer. What a run installs is said on the "
        "line that installs, and nowhere else"
    ]


@pytest.mark.parametrize(
    "setting",
    [
        'exclude-newer-package = { pydantic = "2099-01-01T00:00:00Z" }',
        "exclude-newer-package = { pydantic = false }",
        'exclude-newer = "2099-01-01T00:00:00Z"',
        'index-url = "wheels"',
        'extra-index-url = ["wheels"]',
        'find-links = ["wheels"]',
        "no-index = true",
        'index-strategy = "unsafe-best-match"',
        'override-dependencies = ["pydantic==3"]',
        'constraint-dependencies = ["pydantic>2.99"]',
        'build-constraint-dependencies = ["hatchling>2"]',
        'prerelease = "allow"',
        'resolution = "lowest"',
        "no-build-isolation = true",
        'required-version = ">=0.1"',
        'dev-dependencies = ["requests"]',
        'default-groups = "all"',
        "managed = false",
        'cache-dir = "elsewhere"',
        'zzyzx = "a setting nobody has heard of"',
    ],
)
@pytest.mark.parametrize("where", ["pyproject.toml", "packages/core/pyproject.toml"])
def test_a_setting_of_the_installer_in_a_manifest_is_refused(
    tmp_path: Path, setting: str, where: str
):
    root = a_workspace(tmp_path)
    text = (root / where).read_text(encoding="utf-8")
    table = "[tool.uv]\npackage = false\n"
    text = text.replace(table, f"{table}{setting}\n") if table in text else f"{text}\n{table}"
    text = text if setting in text else text.replace(table, f"[tool.uv]\n{setting}\n")
    (root / where).write_text(text, encoding="utf-8")
    name = setting.partition(" ")[0]
    found = problems_in_settings(root)
    assert found == [
        f"{where}: holds the setting `{name}` of the installer. A manifest holds what makes "
        "the workspace, and no other setting"
    ]
    assert "2099" not in str(found) and "wheels" not in str(found)


@pytest.mark.parametrize(
    "table",
    [
        '[[tool.uv.index]]\nname = "other"\nurl = "wheels"\n',
        '[tool.uv.pip]\nindex-url = "wheels"\n',
        '[tool.uv.extra-build-dependencies]\npydantic = ["requests"]\n',
        '[[tool.uv.dependency-metadata]]\nname = "pydantic"\nrequires-dist = ["requests"]\n',
    ],
)
def test_a_table_of_the_installers_settings_in_a_manifest_is_refused(tmp_path: Path, table: str):
    root = a_workspace(tmp_path, top=f"{TOP}\n{table}")
    assert any("holds the setting" in p for p in problems_in_settings(root))


@pytest.mark.parametrize(
    "source",
    [
        '{ git = "example.test/made-up-core" }',
        '{ path = "../elsewhere" }',
        '{ path = "wheels/made_up_core-9.9-py3-none-any.whl" }',
        '{ url = "example.test/made_up_core-9.9-py3-none-any.whl" }',
        '{ index = "other" }',
        "{ workspace = false }",
        "{ workspace = true, marker = \"sys_platform == 'linux'\" }",
        '[{ workspace = true }, { index = "other" }]',
    ],
)
@pytest.mark.parametrize("where", ["pyproject.toml", "packages/core/pyproject.toml"])
def test_a_package_is_taken_from_this_workspace_or_from_the_index(
    tmp_path: Path, source: str, where: str
):
    # Nothing but the index says when a file was uploaded, so the day holds nothing else.
    from_here = "made-up-core = { workspace = true }"
    root = a_workspace(tmp_path, member=f"{MEMBER}\n[tool.uv.sources]\n{from_here}\n")
    assert problems_in_settings(root) == []
    text = (root / where).read_text(encoding="utf-8")
    assert from_here in text
    (root / where).write_text(text.replace(from_here, f"made-up-core = {source}"), encoding="utf-8")
    assert problems_in_settings(root) == [
        f"{where}: takes `made-up-core` from somewhere that is not this workspace or the index"
    ]


@pytest.mark.parametrize(
    "needed",
    [
        "pydantic @ file:wheels/pydantic-9.9-py3-none-any.whl",
        "pydantic @ git+ssh:example.test/pydantic",
        "pydantic@file:wheels/pydantic.whl",
        "wheels/pydantic-9.9-py3-none-any.whl",
        "./pydantic",
        "-e .",
        "--index-url wheels",
        "-r requirements.txt",
    ],
)
@pytest.mark.parametrize(
    "old",
    ['"pydantic>=2.9"', '"made-up-more"', '"hatchling>=1.25"', '"pytest>=8"'],
    ids=["needed by a package", "needed for an extra", "needed to build", "in a group"],
)
def test_what_a_package_needs_is_named_and_not_given_as_a_file_or_an_address(
    tmp_path: Path, needed: str, old: str
):
    top, member = TOP.replace(old, f'"{needed}"'), MEMBER.replace(old, f'"{needed}"')
    assert (top, member) != (TOP, MEMBER)
    where = "pyproject.toml" if top != TOP else "packages/core/pyproject.toml"
    found = problems_in_settings(a_workspace(tmp_path, top, member))
    assert found == [
        f"{where}: needs something that is given as a file or an address, and not by its name"
    ]
    assert "wheels" not in str(found) and "example.test" not in str(found)


@pytest.mark.parametrize("held", ["[tool.uv\n", "\u00e9 = [", '[project]\ndependencies = "x"\n'])
def test_a_manifest_that_cannot_be_read_is_refused(tmp_path: Path, held: str):
    root = a_workspace(tmp_path, top=held)
    assert problems_in_settings(root) == ["pyproject.toml: cannot be read as a manifest"]


def test_this_repository_holds_no_setting_of_the_installer():
    assert problems_in_settings(Path(__file__).resolve().parents[2]) == []


def test_the_check_of_a_run_holds_the_settings_of_the_installer_too(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    import shutil

    import check_data_workflows

    here = Path(__file__).resolve().parents[2]
    for folder in (".github/workflows", "tools"):
        shutil.copytree(
            here / folder, tmp_path / folder, ignore=shutil.ignore_patterns("__pycache__", "tests")
        )
    a_workspace(tmp_path)
    monkeypatch.setattr(check_data_workflows, "ROOT", tmp_path)

    def commands_of(root: Path) -> frozenset[str]:
        return COMMANDS

    monkeypatch.setattr(check_data_workflows, "commands_of", commands_of)
    assert check_data_workflows.main([]) == 0, capsys.readouterr().err
    (tmp_path / "uv.toml").write_text("", encoding="utf-8")
    assert check_data_workflows.main([]) == 1
    assert "error: uv.toml: is a settings file of the installer" in capsys.readouterr().err


def test_the_day_stated_is_a_day_that_has_come():
    # A day that has not come holds nothing back until it does.
    stated = datetime.strptime(PACKAGES_BEFORE, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    assert stated <= datetime.now(UTC)
    assert INSTALL.endswith(f" --exclude-newer {PACKAGES_BEFORE}")


# Addresses


@pytest.mark.parametrize(
    "line",
    [
        "# the store is at https://store.example.test/bucket",
        "# s3://made-up-bucket/raw",
        "# made-up-account.r2.cloudflarestorage.com",
        "# pub-0123.r2.dev",
        "# made-up.s3.eu-west-2.amazonaws.com",
    ],
)
def test_an_address_anywhere_in_a_data_workflow_is_refused(line: str):
    text = changed("name: data-build\n", f"name: data-build\n{line}\n")
    assert any("holds an address" in p for p in problems(text))


def test_an_address_is_counted_and_never_repeated():
    text = changed("name: data-build\n", "name: data-build\n# https://store.example.test/x\n")
    assert not any("store.example.test" in p for p in problems(text))


# The reader fails closed


@pytest.mark.parametrize(
    "text",
    [
        "on:\n\tworkflow_dispatch:\n",
        "on: &anchor\n  workflow_dispatch:\n",
        "jobs:\n  a: *anchor\n",
        "jobs:\n  a:\n    run: |\n      env\n",
        "jobs:\n  a:\n    run: >\n      env\n",
        "jobs:\n  a: {runs-on: x}\n",
        "jobs:\n  a: 1\n  a: 2\n",
        "jobs:\n  a: 1\n   b: 2\n",
        "---\njobs:\n  a: 1\n",
        "jobs:\n  a: 'it''s'\n",
        'jobs:\n  a: "a\\nb"\n',
        "jobs:\n  a: caf\u00e9\n",
        "jobs:\n  ? a\n  : 1\n",
        "jobs:\n  <<: 1\n",
        "jobs:\n  a: [b, [c]]\n",
        "jobs:\n  a: [b, 'c # d']\n",
        "jobs:\n  a: b: c\n",
        "steps:\n- run: x\n",
    ],
)
def test_what_the_reader_does_not_know_it_refuses(text: str):
    with pytest.raises(Unreadable):
        read_workflow(text)


def test_the_reader_reads_the_few_shapes_a_workflow_needs():
    text = (
        "a: one # a comment\n"
        "b:\n"
        "  - uses: x@y # v1\n"
        "    with:\n"
        "      flag: false\n"
        '  - run: say "$HOME/a" # and no more\n'
        "c: [x, 'y z', \"w\"]\n"
        "d: {}\n"
        "e:\n"
        "f: ${{ matrix.copy }}\n"
        "g: 'a # b' # c\n"
    )
    assert read_workflow(text) == {
        "a": "one",
        "b": [{"uses": "x@y", "with": {"flag": "false"}}, {"run": 'say "$HOME/a"'}],
        "c": ["x", "y z", "w"],
        "d": {},
        "e": "",
        "f": "${{ matrix.copy }}",
        "g": "a # b",
    }


def test_a_comment_starts_where_yaml_says_it_does():
    # In a plain value a quote protects nothing: what follows " #" is a comment.
    assert read_workflow("run: uv sync 'a # b'\n") == {"run": "uv sync 'a"}


# Every other workflow, which may run on a pull request from anyone


def test_no_other_workflow_may_name_a_secret_or_an_environment_of_a_data_workflow():
    ci, environments = Path(".github/workflows/ci.yml"), frozenset({"data-build"})
    assert problems_in_other(ci, CI, environments) == []
    secret = CI + "        env:\n          KEY: ${{ secrets.BURRO_STORE_SECRET }}\n"
    assert any("names a secret" in p for p in problems_in_other(ci, secret, environments))
    environment = CI.replace("  ci:\n", "  ci:\n    environment:\n      name: data-build\n")
    found = problems_in_other(ci, environment, environments)
    assert any("names the environment of a data workflow" in p for p in found)


def test_only_a_full_commit_counts_as_pinned():
    assert pinned_in("- uses: actions/checkout@v7\n- uses: a/b@" + "e" * 39) == frozenset()
    assert pinned_in(CI) == {CHECKOUT, SETUP_UV}


# The files of this repository


def test_the_data_workflows_of_this_repository_keep_every_rule(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    from check_data_workflows import main

    monkeypatch.chdir(Path(__file__).resolve().parents[2])
    assert main([]) == 0, capsys.readouterr().err


# The check of what the store holds, which fetches nothing and writes nothing to the store

REPOSITORY = Path(__file__).resolve().parents[2]
THE_CHECK = Path(".github/workflows/data-held.yml")
WHAT_IT_RUNS = "python -m burro_pipeline held --receipts data/receipts"


def of_this_repository(text: str, path: Path = THE_CHECK) -> list[str]:
    """What a workflow breaks, held to what this repository pins, defines and holds."""
    from check_data_workflows import commands_of

    pinned = pinned_in((REPOSITORY / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    tools = frozenset(file.name for file in (REPOSITORY / "tools").glob("*.py"))
    return problems_in(path, text, pinned, commands_of(REPOSITORY), tools)


def the_check() -> str:
    text = (REPOSITORY / THE_CHECK).read_text(encoding="utf-8")
    assert text.count(WHAT_IT_RUNS) == 1, "the check holds the store to the receipts, once"
    return text


def test_the_check_of_the_store_runs_one_step_of_the_pipeline_which_lists_the_store():
    from check_data_workflows import BEHIND

    text = the_check()
    assert of_this_repository(text) == []
    runs = [line.split("run: ", 1)[1] for line in text.splitlines() if " run: " in line]
    assert len(runs) == 8, "every command of the workflow is on a line of its own"
    behind = [found for run in runs if (found := BEHIND.fullmatch(run)) is not None]
    assert [(found[2], found[3]) for found in behind] == [("python -m burro_pipeline", "held")]
    # Whoever starts it types nothing: it takes no list, no item and no address.
    assert "inputs" not in text and set(read_workflow(text)["on"]) == {"workflow_dispatch"}


def test_the_environment_of_the_check_holds_no_contact_so_no_step_of_it_can_fetch():
    assert SECRETS_OF["data-held"] == STORE and CONTACT not in SECRETS_OF["data-held"]
    fetch = the_check().replace(WHAT_IT_RUNS, "python -m burro_pipeline fetch --list=m1")
    assert any(
        "held: `fetch` reads BURRO_FETCH_CONTACT, and is not given it" in p
        for p in of_this_repository(fetch)
    )
    contact = "          BURRO_FETCH_CONTACT: ${{ secrets.BURRO_FETCH_CONTACT }}\n"
    given = fetch.replace(ONE_GIVEN, ONE_GIVEN + contact)
    assert given != fetch
    assert any(
        "held: BURRO_FETCH_CONTACT is not a secret of data-held" in p
        for p in of_this_repository(given)
    )


@pytest.mark.parametrize("step", ["by-hand", "receipts", "seal", "describe"])
def test_the_check_of_the_store_runs_no_step_that_writes_or_that_shows_a_file(step: str):
    text = the_check().replace(WHAT_IT_RUNS, f"python -m burro_pipeline {step} --receipts x")
    assert any(f"`{step}` is " in p for p in of_this_repository(text))


def test_the_founders_document_names_every_secret_and_environment_and_no_other():
    import re

    from public_log import SECRET_NAMES, SECRETS_OF

    document = (Path(__file__).resolve().parents[2] / "docs" / "data-builds.md").read_text()
    assert set(re.findall(r"`(BURRO_[A-Z_]+)`", document)) == set(SECRET_NAMES)
    assert set(re.findall(r"`(data-[a-z]+)`", document)) == set(SECRETS_OF)


def test_off_the_default_branch_the_guard_stops_the_run():
    from check_data_workflows import on_default_branch

    assert on_default_branch({"GITHUB_REF": "refs/heads/main", "DEFAULT_BRANCH": "main"})
    assert not on_default_branch({"GITHUB_REF": "refs/heads/other", "DEFAULT_BRANCH": "main"})
    assert not on_default_branch({"GITHUB_REF": "refs/tags/main", "DEFAULT_BRANCH": "main"})
    assert not on_default_branch({"GITHUB_REF": "refs/heads/main"})
    assert not on_default_branch({})
