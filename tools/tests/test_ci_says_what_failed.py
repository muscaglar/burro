"""What a failed step of hosted CI says again, where a person who is not signed in can read it.

Anyone can read the annotations of a run. Its log is for those who are signed in. So a
step of `ci.yml` runs its command through `.github/run.sh`, which says the end of what a
failed command printed as an annotation. The runner reads a line that starts `::error` as
one, and reads `%0A` in it as the end of a line.
"""

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github" / "run.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
SH = shutil.which("sh")
THROUGH = 'sh "$GITHUB_WORKSPACE/.github/run.sh" '

pytestmark = pytest.mark.skipif(SH is None, reason="there is no sh on the PATH")


@dataclass(frozen=True)
class Ran:
    code: int
    # What the command printed, as the log of the run holds it.
    printed: list[str]
    # What was said again, one annotation a line.
    said: list[str]


def run(*command: str, folder: Path) -> Ran:
    """Run a command as a step of the workflow runs it."""
    assert SH is not None
    # The system's shell, on a script of this repository.
    done = subprocess.run(
        [SH, str(SCRIPT), *command],
        capture_output=True,
        text=True,
        errors="replace",
        timeout=30,
        check=False,
        env={"PATH": "/usr/bin:/bin", "RUNNER_TEMP": str(folder)},
    )
    assert done.stderr == ""
    lines = done.stdout.splitlines()
    said = [line for line in lines if line.startswith("::error ")]
    return Ran(done.returncode, [line for line in lines if line not in said], said)


def printing(text: str | bytes, code: int, *, folder: Path) -> Ran:
    """Run a command that prints this, some of it as an error, and ends with this code."""
    held = folder / "to-print"
    held.write_bytes(text if isinstance(text, bytes) else text.encode())
    script = (
        "import sys; from pathlib import Path; held = Path(sys.argv[1]).read_bytes(); "
        "half = len(held) // 2; sys.stdout.buffer.write(held[:half]); sys.stdout.flush(); "
        "sys.stderr.buffer.write(held[half:]); sys.exit(int(sys.argv[2]))"
    )
    return run(sys.executable, "-c", script, str(held), str(code), folder=folder)


def title_of(annotation: str) -> str:
    return annotation.split("::", 2)[1].removeprefix("error title=")


def lines_of(annotation: str) -> list[str]:
    """The lines a person reads in an annotation, as the runner takes them apart."""
    message = annotation.split("::", 2)[2]
    return [line.replace("%0D", "\r").replace("%25", "%") for line in message.split("%0A")]


def test_a_command_that_passes_prints_what_it_prints_and_nothing_is_said_again(tmp_path: Path):
    ran = printing("error: this was only a word\nall is well\n", 0, folder=tmp_path)

    assert (ran.code, ran.said) == (0, [])
    assert ran.printed == ["error: this was only a word", "all is well"]


@pytest.mark.parametrize("code", [1, 2, 143])
def test_a_command_that_fails_fails_the_step_with_its_own_code(code: int, tmp_path: Path):
    ran = printing("it went wrong\n", code, folder=tmp_path)

    assert ran.code == code
    assert ran.printed == ["it went wrong"]


def test_the_end_of_what_a_failed_command_printed_is_said_as_one_annotation(tmp_path: Path):
    ran = printing("".join(f"line {n}\n" for n in range(1, 201)), 1, folder=tmp_path)

    [last] = ran.said
    assert title_of(last).endswith("%3A the last lines it printed")
    assert lines_of(last) == [f"line {n}" for n in range(141, 201)]
    # What is said again was printed first, where a person who is signed in reads it whole.
    assert ran.printed == [f"line {n}" for n in range(1, 201)]


def test_the_title_is_the_command_that_failed(tmp_path: Path):
    ran = run("sh", "-c", "exit 3", "a, b: c", folder=tmp_path)

    # A comma and a colon end a title, so each is written as the runner asks.
    assert [title_of(each) for each in ran.said] == ["sh -c exit 3 a%2C b%3A c"]
    assert ran.code == 3


def test_the_lines_that_name_a_failure_are_said_first_and_in_their_order(tmp_path: Path):
    quiet = "".join(f"line {n}\n" for n in range(100))
    named = [
        "a/b.swift:3:9: error: cannot find type 'Portrait' in scope",
        "src/a.ts(3,9): error TS2304: Cannot find name 'x'.",
        "  /home/a.py:3:9 - error: Import cannot be resolved",
        "E       IndexError: list index out of range",
        "FAILED tests/test_one.py::test_it - assert 1 == 2",
        "ERROR tests/test_two.py - ModuleNotFoundError",
        "Found 3 errors.",
        "  12:3  error  'x' is never used  no-unused-vars",
        "FAIL test/access/search.test.tsx (41.2 s)",
        "  ● the keyboard > test_a_search_can_be_made_by_keyboard_alone",
        '    thrown: "Exceeded timeout of 30000 ms for a test.',
        "not ok 3 - the page opens",
        "✖ the page opens (3.1ms)",
        "App/Generated.swift is out of date. Run `make generate`.",
        "** BUILD FAILED **",
        "make: *** [test] Error 1",
        "npm error Lifecycle script `test` failed with error:",
        "Tests:       2 failed, 2664 passed, 2666 total",
        "2 failed, 11168 passed, 206 skipped in 34.26s",
    ]
    printed = "".join(f"{line}\n{quiet}" for line in named)

    about, last = printing(printed, 2, folder=tmp_path).said

    assert title_of(about).endswith("%3A the lines that name a failure")
    assert lines_of(about) == named
    assert lines_of(last) == [f"line {n}" for n in range(40, 100)]


def test_a_line_that_only_holds_the_word_is_not_taken_for_a_failure(tmp_path: Path):
    printed = (
        "0 errors, 0 warnings, 0 informations\n"
        "test_a_failure_is_an_alert PASSED\n"
        "    raise RuntimeError(LEAKY)\n"
        "11171 passed, 206 skipped, 15 xfailed in 29.03s\n"
        "Tests:       2666 passed, 2666 total\n"
        "and then it stopped\n"
    )

    [last] = printing(printed, 1, folder=tmp_path).said

    assert title_of(last).endswith("%3A the last lines it printed")


def test_no_more_lines_that_name_a_failure_are_said_than_a_person_would_read(tmp_path: Path):
    printed = "".join(f"x.py:{n}: error: number {n}\n" for n in range(500))

    about, _ = printing(printed, 1, folder=tmp_path).said

    # The first say what went wrong first, and the last are where a tool sums up.
    assert lines_of(about) == [
        *(f"x.py:{n}: error: number {n}" for n in range(20)),
        "and 460 lines more, of which the last are:",
        *(f"x.py:{n}: error: number {n}" for n in range(480, 500)),
    ]


def test_what_the_runner_would_read_as_a_command_is_written_so_that_it_is_not(tmp_path: Path):
    ran = printing("100% of it\r\n::add-mask::a word\n::notice::made up\n", 1, folder=tmp_path)

    # One line for each annotation, so nothing that is said again starts a line of its own.
    [last] = ran.said
    assert lines_of(last) == ["100% of it\r", "::add-mask::a word", "::notice::made up"]
    assert last.endswith("::100%25 of it%0D%0A::add-mask::a word%0A::notice::made up")


def test_colour_and_a_line_of_great_length_are_cut_down(tmp_path: Path):
    printed = f"\x1b[31mred\x1b[0m and \x1b[1;32mgreen\x1b[m\n{'x' * 1000}\n"

    [last] = printing(printed, 1, folder=tmp_path).said

    assert lines_of(last) == ["red and green", "x" * 400]


def test_what_is_not_text_is_said_all_the_same(tmp_path: Path):
    [last] = printing(b"caf\xe9 \xff\xfe\nthe end\n", 1, folder=tmp_path).said

    assert lines_of(last)[-1] == "the end"


def test_what_ends_with_no_end_of_line_is_said_again_on_a_line_of_its_own(tmp_path: Path):
    """The runner reads an annotation only where it starts a line."""
    ran = printing("it went wrong", 1, folder=tmp_path)

    [last] = ran.said
    assert lines_of(last) == ["it went wrong"]
    assert ran.printed == ["it went wrong"]


def test_a_command_that_fails_and_prints_nothing_is_said_to_have_printed_nothing(tmp_path: Path):
    ran = run("false", folder=tmp_path)

    assert (ran.code, ran.printed) == (1, [])
    assert ran.said == ["::error title=false::It failed, and printed nothing."]


def test_a_command_that_is_not_there_fails_the_step_and_says_so(tmp_path: Path):
    ran = run("no-such-program-as-this", folder=tmp_path)

    assert ran.code != 0
    [last] = ran.said
    assert "no-such-program-as-this" in lines_of(last)[-1]


def test_two_steps_at_once_keep_what_they_print_apart(tmp_path: Path):
    first = printing("the first\n", 1, folder=tmp_path)
    second = printing("the second\n", 1, folder=tmp_path)

    assert lines_of(first.said[0]) == ["the first"]
    assert lines_of(second.said[0]) == ["the second"]
    # Nothing is left behind of either.
    assert sorted(path.name for path in tmp_path.iterdir()) == ["to-print"]


# The workflow


def jobs() -> dict[str, str]:
    """Each job of the workflow by its name: what stands between it and the next."""
    text = WORKFLOW.read_text(encoding="utf-8").split("\njobs:\n")[1]
    parts = re.split(r"^  (?=[a-z]+:$)", text, flags=re.MULTILINE)[1:]
    return {part.split(":")[0]: part for part in parts}


def commands(job: str) -> list[str]:
    """The command of every step that is one line."""
    return re.findall(r"^ +(?:- )?run: (?!\|)(.+)$", job, flags=re.MULTILINE)


def test_every_command_of_every_job_is_run_so_that_its_failure_is_said_again():
    assert list(jobs()) == ["ci", "web", "desk", "image", "ios"]
    for name, job in jobs().items():
        assert commands(job), name
        for command in commands(job):
            # `a && b` would say the failure of `a` and never that of `b`.
            assert command.startswith(THROUGH) and "&&" not in command, (name, command)


def test_the_iphone_app_is_checked_part_by_part_and_every_part_is_run():
    """So that one run says all that is wrong with it, and not the first thing alone."""
    job = jobs()["ios"]
    makefile = (ROOT / "apps" / "ios" / "Makefile").read_text(encoding="utf-8")
    [parts] = re.findall(r"^check: ([a-z -]+?) ##", makefile, flags=re.MULTILINE)

    ran = [command.removeprefix(THROUGH) for command in commands(job)]
    assert ran == [f"make -C apps/ios {part}" for part in parts.split()]
    # The first runs if the job got so far. Each other runs though one before it failed.
    steps = re.findall(r"^      - (?:if: (.+)\n        )?run: sh ", job, flags=re.MULTILINE)
    assert steps == ["", "success() || failure()", "success() || failure()"]
