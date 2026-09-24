"""The licence gate of the desk: nothing is shown from a source the registry does not allow.

Rule 1 of AGENTS.md. A real draft is asked about at the licence registry, source by
source, before any of it is read into a queue. The made-up city is described by made-up
sources alone, and asks nobody.

This is the only module of the desk that imports outside the standard library, and it
does so only for real files. `make desk` on the made-up city needs Python alone.
"""

from collections.abc import Iterable
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from burro_pipeline.registry import Registry

# What the made-up city cites. A publisher of the made-up city is `synthetic-` and a word.
MADE_UP = "synthetic"
# The uses the desk asks for. Section 6 of docs/design/desk.md gives the first, and its
# section 9 asks the registry's owner to confirm the second for a sample of venues.
GAZETTEER, SCORING, PROFILE_TEXT = "gazetteer", "scoring", "profile_text"
USES = (GAZETTEER, SCORING, PROFILE_TEXT)

REGISTRY = Path(__file__).resolve().parents[3] / "registry" / "sources"


class Refused(Exception):
    """A source may not be read for the use asked. The words are for a person to act on."""


def is_made_up(source_id: str) -> bool:
    return source_id == MADE_UP or source_id.startswith(f"{MADE_UP}-")


def ask(
    source_ids: Iterable[str], use: str, *, synthetic: bool, registry: Path | None = None
) -> None:
    """Raise `Refused` unless every source may be read for this use.

    A made-up draft may name made-up sources alone, and a real draft none: the two are
    never mixed. Every source is asked about before the first refusal is raised, so one
    run says all that is wrong.
    """
    if use not in USES:
        raise Refused(f"The desk asks the registry for {', '.join(USES)}, and not for {use}.")
    wanted = sorted(set(source_ids))
    if "" in wanted:
        raise Refused(f"A row names no source. Every row read for {use} names one.")
    if synthetic:
        real = [source_id for source_id in wanted if not is_made_up(source_id)]
        if real:
            raise Refused(f"A made-up draft names a source that is not made up: {real[0]}.")
        return
    made_up = [source_id for source_id in wanted if is_made_up(source_id)]
    if made_up:
        raise Refused(f"A real draft names a made-up source: {made_up[0]}.")
    refusals = _refusals(wanted, use, registry or REGISTRY)
    if refusals:
        raise Refused(" ".join(refusals))


def in_words(source_id: str, *, synthetic: bool, registry: Path | None = None) -> str:
    """A source as a person reads it: who publishes it, and what it is called.

    Two ids may be two files of one publisher, and an id alone does not say so. A
    source the registry does not hold is said by its id: the gate refuses it where it
    is asked about, and that is said there.
    """
    if synthetic or is_made_up(source_id):
        of = source_id.removeprefix(MADE_UP).strip("-")
        return f"Made-up publisher of {of.replace('-', ' ')}" if of else "Made up"
    try:
        from burro_pipeline.registry import RegistryError
    except ImportError:
        return source_id
    try:
        held = _held(registry or REGISTRY).get(source_id)
    except (RegistryError, Refused):
        return source_id
    # What stands in brackets says which edition or which part, and is left out.
    return ", ".join(each.split(" (")[0].strip() for each in (held.publisher, held.name))


def _answers(source_id: str, use: str, registry: Path) -> str:
    """Why the registry refuses a source for a use, or nothing if it allows it."""
    try:
        from burro_pipeline.registry import RegistryError, Use
    except ImportError as error:
        raise Refused(
            "The licence registry cannot be read without the pipeline. "
            "Run make setup, then fill the queues again."
        ) from error
    try:
        _held(registry).require(source_id, Use(use))
    except RegistryError as error:
        return str(error)
    return ""


@cache
def _held(registry: Path) -> "Registry":
    """The registry, read once in a run: a fill asks it about every file of every queue."""
    from burro_pipeline.registry import RegistryError, load

    try:
        return load(registry)
    except RegistryError as error:
        raise Refused(f"The licence registry cannot be read: {error}") from error


def _refusals(source_ids: list[str], use: str, registry: Path) -> list[str]:
    answers = (_answers(source_id, use, registry) for source_id in source_ids)
    return [answer for answer in answers if answer]
