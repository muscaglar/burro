"""The step of the command line that the areas own: `draft`.

    python -m burro_pipeline draft --out FOLDER

It is the whole draft of London's named areas, made from the store in one
command. `draft_run.py` does the work, and says what it makes. This is the way
in to it from the one command line, so that a hosted run can make the draft it
builds on, and no draft is handed to a build from a machine of a person's own.

What it prints may be read by anyone: counts. What it writes names places, so
it goes to the folder `--out` names, and is never printed.
"""

import argparse
import os
from collections.abc import Mapping, Sequence

from burro_pipeline.areas import draft_run
from burro_pipeline.command import PROG, Step, add_step
from burro_pipeline.fetch.cli import THE_STORE

DRAFT = "draft"

STEPS = (
    Step(
        DRAFT,
        "Draft the names and the borders of London's areas, from the store",
        f"""\
Run it before `preview`, and give `preview` the folder it wrote with --names.
Each area of the build then bears the name of the drafted neighbourhood that
holds most of its output areas.

It makes the names and the seeds, grows every output area into an area, offers
a name for each area, and writes the curated files, the flags, the layers and
the pictures. Every name is one a registered publisher's file holds, at a
point or an outline the file gives. No name and no border is supplied by
whoever runs it, or by a model. Nothing from OpenStreetMap is read, and nothing
about who lives anywhere.

It is a draft: what a method made, and nobody has checked. Every row it writes
says so, and a release that is built on it says of every name that it is a
draft, until a person has decided it at the review desk. Once names are
decided there, a build is given the gazetteer the desk compiled in its place.

Every file is asked for under `gazetteer`, by the part that reads it, through
its receipt. A source the licence registry refuses for that use is not read.

Reaches no publisher. Reaches the store, to copy its files out, and writes
nothing to it. No socket is open while a file is read. The same files give the
same bytes: nothing here reads a clock.

{THE_STORE}
From an object store every file that has a receipt is copied out before any is
read, and a line says how many there were. With --work the copies are left
where a build that follows finds them, so that no file is copied out twice. A
key that can only read the store is enough.

Writes the draft under --out, which must be new or empty, and outside what git
tracks. What it writes names places, and is never committed.

Prints one line of counts. It names no place.""",
        ("--out data/releases/draft", "--out data/releases/draft --work data/releases/copies"),
        {
            0: "The draft was written",
            2: "A file may not be read, or is not what the step was written to read, or an "
            "argument is wrong. The reason is said in words. Nothing is left half written "
            "that a build would take",
        },
    ),
)


def build(prog: str = PROG) -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    """The step the areas own, as the command line takes it: the whole, and the step."""
    whole = argparse.ArgumentParser(
        prog=prog, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = whole.add_subparsers(dest="command", required=True)
    step = {step.name: add_step(commands, step, prog) for step in STEPS}
    draft_run.arguments(step[DRAFT])
    return whole, step


def parsed(argv: Sequence[str] | None = None, prog: str = PROG) -> argparse.Namespace:
    """The arguments of the step. Stops with the step's usage if they are not ones it takes."""
    return build(prog)[0].parse_args(argv)


def main(argv: Sequence[str] | None = None, environment: Mapping[str, str] | None = None) -> int:
    return draft_run.run(parsed(argv), os.environ if environment is None else environment)
