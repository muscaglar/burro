"""The pipeline's command line: one command for each step of a data build.

    python -m burro_pipeline --help          the steps, in the order a build takes them
    python -m burro_pipeline STEP --help     what a step does, with examples

Each step is owned by the part of the pipeline that does the work. This is the
one way in to all of them, so that the Makefile, the hosted workflows and a
person at a terminal run the same commands.
"""

import argparse
import sys
from collections.abc import Callable, Sequence
from types import ModuleType

from burro_pipeline.areas import cli as areas
from burro_pipeline.assemble import cli as assemble
from burro_pipeline.cells import cli as cells
from burro_pipeline.command import PROG, Step
from burro_pipeline.evidence import cli as evidence
from burro_pipeline.fetch import cli as fetch
from burro_pipeline.kept import cli as kept
from burro_pipeline.travel import cli as travel
from burro_pipeline.upkeep import cli as upkeep

# The steps, in the order a build takes them. `fresh` comes first: it says what is held
# and how old it is, which is what to fetch again. `keep` and `take` follow a build: one
# keeps what was built, and one takes what was approved. `moved` follows them: it holds
# what was built against what is served, before the newer is approved. `why` comes last:
# it is no step of a build, and says what the numbers in a line of fetch mean.
ORDER = (
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
)
_OWNERS: tuple[ModuleType, ...] = (
    fetch,
    evidence,
    cells,
    travel,
    areas,
    assemble,
    kept,
    upkeep,
)
_OWNER: dict[str, ModuleType] = {step.name: owner for owner in _OWNERS for step in owner.STEPS}
_KNOWN: dict[str, Step] = {step.name: step for owner in _OWNERS for step in owner.STEPS}
STEPS: dict[str, Step] = {name: _KNOWN[name] for name in ORDER}

ABOUT = f"""\
usage: {PROG} STEP [arguments]

The steps of a data build, in the order a build takes them.

{{steps}}

{PROG} STEP --help says what a step reads and writes, what it
reaches, and gives examples that work as they stand.

Only `fetch` reaches a publisher. It, `by-hand`, `receipts`, `held`, `describe`,
`cells`, `draft` and `preview` reach the store, which the environment names. No
other step reaches a network. Run each with `uv run` before it, from the top of
the repository. `fresh` reads the receipts the repository holds, and says which
files it is time to fetch again. `draft` makes the names a build gives its areas. `preview` is
the whole of a first build in one command: it seals,
makes the geography, works out each measure, and writes a release. `travel`
routes the made-up town alone, until the engine that routes London is installed.
`keep` and `take` reach the store of releases, which is another store and is
named by variables of its own: `keep` puts a release that was built there, and
`take` brings the one a committed lock names to the folder an image is built from.
`moved` says what differs between two releases, so that a build is approved by a
person who knows what it changed.
What a step prints for anyone to read is one line of key=value: step names,
registry ids, counts and hashes. Why a step stopped is said in words beside it.
"""


def overview() -> str:
    """The steps, one line each."""
    width = max(len(name) for name in STEPS)
    return ABOUT.format(
        steps="\n".join(f"  {name:<{width}}  {step.summary}" for name, step in STEPS.items())
    )


def parser_of(step: str) -> argparse.ArgumentParser:
    """The arguments one step takes."""
    make: Callable[[str], tuple[object, dict[str, argparse.ArgumentParser]]] = _OWNER[step].build
    return make(PROG)[1][step]


def parse(argv: Sequence[str]) -> argparse.Namespace:
    """The arguments of a step, read and not run. Stops with its usage if they are wrong."""
    read: Callable[[Sequence[str]], argparse.Namespace] = _OWNER[argv[0]].parsed
    return read(argv)


def main(argv: Sequence[str] | None = None) -> int:
    words = list(sys.argv[1:] if argv is None else argv)
    if words and words[0] in _OWNER:
        run: Callable[[Sequence[str]], int] = _OWNER[words[0]].main
        return run(words)
    if words in (["-h"], ["--help"]):
        print(overview(), end="")
        return 0
    if words:
        # What was typed is not repeated: a log may hold this line.
        print(f"error: that is not a step. {PROG} --help lists them", file=sys.stderr)
    else:
        print(overview(), end="", file=sys.stderr)
    return 2
