"""The workflow that builds London, held to the rules that are its own.

It reads the store with one key and keeps a release with another. So it is held to more
than any other data workflow: which step is given which key, that a release is kept only
once two builds of it were compared, and that its lock is shown only once it is kept.
Each test here takes the workflow as it is committed, breaks one thing, and looks for
the rule that says so.
"""

import re
from pathlib import Path

import pytest
from check_data_workflows import (
    BEHIND,
    LOCK_TOOL,
    NAMES_GIVEN,
    NEVER_A_TRACEBACK,
    STEPS_OF_A_RUN,
    commands_of,
    pinned_in,
    problems_in,
    read_workflow,
)
from public_log import RELEASES, SECRETS_OF, STORE

REPOSITORY = Path(__file__).resolve().parents[2]
WORKFLOWS = Path(".github/workflows")
LONDON = WORKFLOWS / "data-london.yml"
PIPELINE = "python -m burro_pipeline"
# The steps of the workflow, by the name each has there.
CHECKS = "Every secret is set, and what is made from one is hidden"
DRAFT, BUILD, CHECK = "Draft the names of the areas", "Build London", "Check the release"
HASH, COMPARE = "Hash what was built", "Compare the two builds"
KEEP, SHOW = "Keep the release", "Show the lock of the release"


def text_of(path: Path = LONDON) -> str:
    return (REPOSITORY / path).read_text(encoding="utf-8")


def problems(text: str, path: Path = LONDON) -> list[str]:
    """What a workflow breaks, held to what this repository pins, defines and holds."""
    pinned = pinned_in(text_of(WORKFLOWS / "ci.yml"))
    tools = frozenset(file.name for file in (REPOSITORY / "tools").glob("*.py"))
    return problems_in(path, text, pinned, commands_of(REPOSITORY), tools)


def breaks(text: str, rule: str, path: Path = LONDON) -> bool:
    return any(rule in problem for problem in problems(text, path))


def changed(old: str, new: str, count: int = 1) -> str:
    text = text_of()
    assert text.count(old) >= count, f"the workflow no longer holds {old!r}"
    return text.replace(old, new, count)


def of_the_second_build(old: str, new: str) -> str:
    """The workflow with one thing changed in the job that builds second, and nowhere else."""
    before, mark, after = text_of().partition("\n  second:\n")
    assert mark and after.count(old) == 1, f"the second build holds {old!r} once"
    return before + mark + after.replace(old, new)


def step(name: str) -> str:
    """One step of the workflow, whole: from its name to the line it runs. The last so named."""
    lines = rf"      - name: {re.escape(name)}\n(?:        [^\n]*\n)+"
    found = re.findall(lines, text_of())
    assert found, f"the workflow holds no step named {name!r}"
    return found[-1]


def given(names: tuple[str, ...]) -> str:
    return "".join(f"          {name}: ${{{{ secrets.{name} }}}}\n" for name in names)


def with_more(name: str, names: tuple[str, ...]) -> tuple[str, str]:
    """A step as it is, and as it would be were it given secrets beside what it is given."""
    one = step(name)
    assert one.count("        env:\n") == 1
    return one, one.replace("        env:\n", f"        env:\n{given(names)}")


def behind(text: str) -> list[tuple[str, str, str]]:
    """Every command the workflow runs behind the public log: its job, its command, its step."""
    found: list[tuple[str, str, str]] = []
    jobs = read_workflow(text)["jobs"]
    assert isinstance(jobs, dict)
    for name, job in jobs.items():
        assert isinstance(job, dict) and isinstance(job["steps"], list)
        for one in job["steps"]:
            assert isinstance(one, dict)
            match = BEHIND.fullmatch(str(one.get("run", "")))
            if match is not None:
                found.append((name, match[2], match[3]))
    return found


def test_the_workflow_keeps_every_rule_as_it_is_committed():
    assert problems(text_of()) == []


# What it runs


def test_it_builds_twice_and_each_build_is_built_the_same_way():
    assert [(job, does) for job, _, does in behind(text_of())] == [
        *(("first", does) for does in ("held", "draft", "preview", "check")),
        *(("second", does) for does in ("draft", "preview", "check", "keep")),
    ]
    for does in (" draft --out ", " preview --release-id=", " burro-release check "):
        runs = [line for line in text_of().splitlines() if " run: " in line and does in line]
        assert len(runs) == 2 and runs[0] == runs[1], does


def test_two_builds_that_are_not_built_alike_are_refused():
    rule = "second: builds another way than first"
    assert breaks(of_the_second_build(" --list m5-journeys", ""), rule)
    assert breaks(of_the_second_build(' --names "$RUNNER_TEMP/draft"', ""), rule)
    assert breaks(of_the_second_build(step(DRAFT), ""), rule)
    assert breaks(of_the_second_build(" --receipts data/receipts", ""), rule)


@pytest.mark.parametrize("does", ["take", "fetch", "by-hand", "receipts", "seal", "describe"])
def test_it_runs_no_step_that_takes_a_release_or_that_writes_a_publishers_file(does: str):
    text = changed('burro_pipeline keep "$RUNNER_TEMP/releases"', f"burro_pipeline {does} --out x")
    assert breaks(text, f"`{does}` is ") or breaks(text, f"`{does}` reads")
    assert does == "fetch" or does not in STEPS_OF_A_RUN[PIPELINE]


def test_the_release_and_the_time_are_typed_by_whoever_starts_the_run():
    assert {"RELEASE", "BUILT_AT"} <= NAMES_GIVEN
    started = read_workflow(text_of())["on"]
    assert isinstance(started, dict) and isinstance(started["workflow_dispatch"], dict)
    typed = started["workflow_dispatch"]["inputs"]
    assert isinstance(typed, dict) and set(typed) == {"built_at", "release"}
    # Neither stands in a command but inside double quotes, where the shell makes no more of it.
    rule = "is not a command a data workflow may run"
    assert breaks(changed('--release-id="$RELEASE"', "--release-id=$RELEASE", 2), rule)
    assert breaks(changed('--built-at="$BUILT_AT"', "--built-at=$BUILT_AT", 2), rule)
    assert breaks(changed('--release-id="$RELEASE"', "--release-id=${{ inputs.release }}", 2), rule)


def test_what_is_typed_is_given_under_a_name_on_the_list_and_no_other():
    text = changed(
        "          RELEASE: ${{ inputs.release }}", "          UV_INDEX: ${{ inputs.release }}"
    )
    assert breaks(text, "`UV_INDEX` is not a name a step is given an input")


# Which step is given which key


def test_each_step_is_given_the_key_it_reads_and_no_other():
    reads = STEPS_OF_A_RUN[PIPELINE]
    assert reads["draft"] == reads["preview"] == reads["held"] == STORE
    assert reads["keep"] == RELEASES and not set(STORE) & set(RELEASES)
    assert STEPS_OF_A_RUN["burro-release"]["check"] == ()
    assert SECRETS_OF["data-london"] == (*STORE, *RELEASES)


def test_the_step_that_keeps_a_release_is_given_no_key_of_the_store():
    kept, more = with_more(KEEP, STORE[-1:])
    assert breaks(changed(kept, more), f"second: `keep` is given {STORE[-1]}, which it does not")
    less = kept.replace(given(RELEASES[-1:]), "")
    assert breaks(changed(kept, less), f"second: `keep` reads {RELEASES[-1]}, and is not given it")


@pytest.mark.parametrize("name", [DRAFT, BUILD])
def test_a_step_that_reads_the_store_is_given_no_key_that_writes_a_release(name: str):
    reads, more = with_more(name, RELEASES[-1:])
    assert breaks(changed(reads, more), f"is given {RELEASES[-1]}, which it does not read")


def test_the_step_that_checks_a_release_is_given_no_key_at_all():
    checked, more = with_more(CHECK, STORE[-1:])
    assert breaks(changed(checked, more), f"`check` is given {STORE[-1]}, which it does not read")


def test_the_first_build_is_given_no_key_that_writes_a_release():
    """Not even to check it. A job holds no key that no step of it reads."""
    checks = f"      - name: {CHECKS}\n        env:\n"
    found = problems(changed(checks, f"{checks}{given(RELEASES)}", count=1))
    assert [p for p in found if "which no step of the job reads" in p] == [
        f"{LONDON}: first: is given {name}, which no step of the job reads"
        for name in sorted(RELEASES)
    ]


@pytest.mark.parametrize("name", [HASH, COMPARE, SHOW])
def test_a_tool_that_holds_two_builds_to_each_other_is_given_no_key(name: str):
    tool, more = with_more(name, RELEASES[-1:])
    assert breaks(changed(tool, more), "is given a secret and does not run behind")


@pytest.mark.parametrize("workflow", ["data-fetch.yml", "data-build.yml", "data-travel.yml"])
def test_no_other_workflow_is_given_the_key_that_writes_a_release(workflow: str):
    path = WORKFLOWS / workflow
    text = text_of(path)
    assert not any(name in text for name in RELEASES)
    named = text.replace("secrets.BURRO_STORE_SECRET", "secrets.BURRO_RELEASES_SECRET")
    assert breaks(named, f"BURRO_RELEASES_SECRET is not a secret of {path.stem}", path)


# A release is kept only once two builds of it were compared


def test_a_release_is_kept_only_after_two_builds_of_it_were_compared():
    rule = "second: keeps a release before two builds of it were compared"
    compare, keep = step(COMPARE), step(KEEP)
    # The step that keeps has a comment of its own above it, which stays where it is.
    assert breaks(changed(keep, "").replace(compare, keep + compare), rule)
    assert breaks(changed(compare, ""), rule)


def test_a_build_is_compared_with_the_build_of_another_job_that_it_waits_for():
    rule = "second: compares a build with no build of another job"
    other = "          COPY_A: ${{ needs.first.outputs.a }}\n"
    assert breaks(changed(other, "          COPY_A: ${{ inputs.release }}\n"), rule)
    assert breaks(changed(other, ""), rule)
    assert breaks(changed(other, other.replace("first", "check")), rule)
    assert breaks(changed("    needs: first\n", "    needs: check\n"), rule)


def test_the_job_that_keeps_a_release_builds_it_too():
    """What is kept is what that job built and compared, and nothing that was handed to it."""
    text = text_of()
    for name in (DRAFT, BUILD, CHECK):
        before, mark, after = text.partition("\n  second:\n")
        text = before + mark + after.replace(step(name), "")
    assert breaks(text, "second: keeps a release it did not build")


def test_the_first_build_keeps_nothing():
    hashed = step(HASH)
    text = changed(hashed, hashed + step(KEEP))
    assert breaks(text, "first: keeps a release before two builds of it were compared")


def test_the_lock_is_shown_only_once_the_release_is_kept():
    keep, show = step(KEEP), step(SHOW)
    before = changed(show, "").replace(keep, show + keep)
    assert breaks(before, "second: shows the lock of a release before it is kept")
    assert breaks(changed(keep, ""), "second: shows the lock of a release that is not kept")


@pytest.mark.parametrize(("name", "does"), [(COMPARE, "compare"), (KEEP, "keep"), (SHOW, "show")])
def test_a_step_that_compares_keeps_or_shows_is_never_left_out_of_a_run(name: str, does: str):
    one = step(name)
    named = f"      - name: {name}\n"
    left_out = one.replace(named, f"{named}        if: inputs.release == ''\n")
    rule = f"second: the step that {does}s a release is never left out of a run"
    assert breaks(changed(one, left_out), rule)


# What no public log guards

# What is said of a tool that a job with a key runs bare, and that is on no list.
NOT_GUARDED = "is not on the list of the tools that never print a traceback"


def bare(text: str) -> list[tuple[str, str]]:
    """Every tool a job that is given a key runs with no public log before it: its job,
    and the tool with what it does."""
    found: list[tuple[str, str]] = []
    jobs = read_workflow(text)["jobs"]
    assert isinstance(jobs, dict)
    for name, job in jobs.items():
        assert isinstance(job, dict) and isinstance(job["steps"], list)
        runs = [str(one.get("run", "")) for one in job["steps"] if isinstance(one, dict)]
        if not any(" secrets." in str(one) for one in job["steps"]):
            continue
        for run in runs:
            tool = re.search(r" python tools/([a-z_]+\.py) ([a-z-]+)", run)
            if tool is not None and tool[1] != "public_log.py":
                found.append((name, f"{tool[1]} {tool[2]}"))
    return found


def test_the_three_steps_no_public_log_guards_are_the_three_on_the_list():
    """They write to the run's outputs and its summary, which a step behind the public
    log is not told of. So each is a program that never prints a traceback."""
    assert bare(text_of()) == [
        ("first", f"{LOCK_TOOL} hash"),
        ("second", f"{LOCK_TOOL} compare"),
        ("second", f"{LOCK_TOOL} show"),
    ]
    assert dict(NEVER_A_TRACEBACK) == {LOCK_TOOL: frozenset({"hash", "compare", "show"})}
    for name in (HASH, COMPARE, SHOW):
        assert "tools/public_log.py" not in step(name)


def test_a_command_of_the_lock_tool_that_is_on_no_list_is_refused():
    """The tool holds an image to its lock too. No run does that, so no list names it."""
    shown = 'tools/release_lock.py show "$RUNNER_TEMP/releases"'
    text = changed(shown, shown.replace(" show ", " carried "))
    assert breaks(text, f"second: `{LOCK_TOOL} carried` {NOT_GUARDED}")
    read = changed(f'{shown} "$RELEASE"', "tools/release_lock.py read data/approved/x.json")
    assert breaks(read, f"second: `{LOCK_TOOL} read` {NOT_GUARDED}")


@pytest.mark.parametrize(
    "run",
    [
        'uv run --no-project python tools/same_manifest.py hash "$RUNNER_TEMP/releases"',
        "uv run --no-project python tools/same_manifest.py compare",
        "uv run --no-sync python tools/canary.py plant",
        "uv run --no-project python tools/check_public_only.py",
    ],
)
@pytest.mark.parametrize("after", [HASH, SHOW])
def test_another_tool_is_run_with_no_public_log_in_no_job_that_holds_a_key(run: str, after: str):
    """A later step of the kind is added with its test, or behind the public log."""
    one = step(after)
    more = f"{one}      - name: One more\n        run: {run}\n"
    job = "first" if after == HASH else "second"
    tool = run.split("tools/")[1].removesuffix(' "$RUNNER_TEMP/releases"')
    assert breaks(changed(one, more), f"{job}: `{tool}` {NOT_GUARDED}")


def test_a_job_that_holds_no_key_may_run_a_tool_that_is_on_no_list():
    """A build of the made-up city reads nothing real, and its job holds made-up secrets."""
    for workflow in ("data-build.yml", "data-travel.yml"):
        path = WORKFLOWS / workflow
        text = text_of(path)
        assert "tools/same_manifest.py hash" in text and "public_log.py mask --made-up" in text
        assert not [problem for problem in problems(text, path) if NOT_GUARDED in problem]
    # The job that checks the rules of this workflow holds no secret at all.
    assert "first: " in " ".join(
        problems(changed("tools/release_lock.py hash a", "tools/canary.py plant"))
    )
    assert not breaks(text_of(), NOT_GUARDED)


def test_a_tool_on_the_list_may_not_be_moved_behind_the_key_of_another_name():
    """The list is of a tool and what it does: a tool of another name that does the same
    is another program, which no test holds."""
    text = changed("tools/release_lock.py hash a", "tools/same_manifest.py hash a")
    assert breaks(text, f"first: `same_manifest.py hash` {NOT_GUARDED}")


# What a person decided at the panel

# Where the desk publishes the founder's file of changes, from the top of the repository.
PUBLISHED = "gazetteer/london/decisions/changes/r1.jsonl"
GIVEN_THE_PLACE = f" --published-changes {PUBLISHED}"


def builds() -> list[str]:
    """The two lines that build London, as the workflow runs them."""
    return [line for line in text_of().splitlines() if " preview --release-id=" in line]


def test_both_builds_are_given_the_place_the_founders_file_of_changes_is_published_to():
    """What is decided at the panel reaches the release a hosted run builds, once it is
    published and committed. A run that finds no file there builds as it did."""
    found = builds()
    assert len(found) == 2 and found[0] == found[1]
    for line in found:
        assert line.count(GIVEN_THE_PLACE) == 1
        # A file that must be there would stop every run of a repository that holds none.
        assert " --changes " not in line


def test_the_place_is_where_the_desk_publishes_the_founders_file():
    from burro_pipeline.assemble.cli import FOUNDERS_FILE
    from desk import records
    from desk.panel import kept

    makefile = (REPOSITORY / "Makefile").read_text(encoding="utf-8")
    to = re.search(r'^desk-publish:.*ARGS="--to ([a-z/]+)"$', makefile, re.MULTILINE)
    assert to is not None, "the Makefile says where the copy that may be committed goes"
    assert f"{to[1]}/{records.PUBLIC_TREE}/{kept.FOLDER}/{FOUNDERS_FILE}" == PUBLISHED


def test_a_run_is_given_one_place_and_never_a_folder_or_a_pattern_to_choose_from():
    (place,) = {word for line in builds() for word in line.split() if "decisions" in word}
    assert place == PUBLISHED and not set(place) & set('*?[]{}$"')


def test_a_build_that_is_given_the_place_in_one_build_alone_is_refused():
    rule = "second: builds another way than first"
    assert breaks(of_the_second_build(GIVEN_THE_PLACE, ""), rule)


def test_no_step_of_a_build_is_left_out_of_a_run_for_want_of_a_file():
    """Whether a file was published is the build's to find, and never the workflow's to ask:
    a step that a run may leave out is a step that a run may be made to leave out."""
    text = text_of()
    assert "\n        if: " not in text and "hashFiles" not in text
    # The job that searches what the run made public runs whatever became of the builds.
    assert re.findall(r"(?m)^    if: (.*)$", text) == ["always()"]
