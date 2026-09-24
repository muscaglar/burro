"""What the steps of the command line share: the command's name, and how a step's help is laid out.

Every step answers `--help` in the same order: what it does, what it reads and
writes and whether it reaches a network, examples that are held to the step's
own arguments by a test, and what each exit code means.
"""

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

# How the command is run. It is written in every usage line and every example.
PROG = "python -m burro_pipeline"
# The folders of the repository that git takes nothing in from. What a step makes from a
# publisher's file is written under one of them, or outside the repository. A test holds
# each to the repository's own list of what git ignores.
IGNORED_BY_GIT = ("data/releases", "data/raw", "scratch")
NOT_IGNORED = (
    "is inside the repository, where git would take in what the step writes. What is made "
    "from a publisher's file is never committed. Name a folder under data/releases/ or "
    "scratch/, or one outside the repository"
)


def may_be_written(folder: Path, root: Path) -> bool:
    """Whether a step may write what it makes from a publisher's file to a folder.

    It may where git would not take it in: outside the repository at `root`,
    or under a folder of it that git ignores. A `root` that is no repository
    holds nothing git would take in.
    """
    top, target = root.resolve(), folder.resolve()
    if not (top / ".git").exists() or top not in (target, *target.parents):
        return True
    return any((top / ignored) in (target, *target.parents) for ignored in IGNORED_BY_GIT)


@dataclass(frozen=True)
class Step:
    """One step of the command line, as its help gives it."""

    name: str
    # One line, for the list of steps.
    summary: str
    # What it does, what it reads and writes, and what it reaches.
    about: str
    # Arguments that work as they stand, each written after the step's name.
    examples: Sequence[str]
    # What each exit code means.
    exits: Mapping[int, str]

    def ending(self, prog: str) -> str:
        shown = "\n".join(f"  {prog} {self.name} {example}".rstrip() for example in self.examples)
        codes = "\n".join(f"  {code}  {meaning}" for code, meaning in sorted(self.exits.items()))
        return f"examples:\n{shown}\n\nexit codes:\n{codes}"


class Commands(Protocol):
    def add_parser(
        self,
        name: str,
        *,
        help: str,
        description: str,
        epilog: str,
        formatter_class: type[argparse.HelpFormatter],
    ) -> argparse.ArgumentParser: ...


def add_step(commands: Commands, step: Step, prog: str) -> argparse.ArgumentParser:
    """Add a step to a command, with its help laid out as every step's is."""
    return commands.add_parser(
        step.name,
        help=step.summary,
        description=f"{step.summary}.\n\n{step.about}",
        epilog=step.ending(prog),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
