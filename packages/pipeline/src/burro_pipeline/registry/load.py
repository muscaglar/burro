"""Load the registry from disk and answer "may I use this?"."""

import tomllib
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, cast

from pydantic import ValidationError

from burro_pipeline.registry.model import INTERNAL_USES, Dimension, Source, Status, Use
from burro_pipeline.registry.rules import Severity, check

DEFAULT_PATH = Path("registry/sources")
SCHEMA_VERSION = 1


class RegistryError(Exception):
    """The registry file is unreadable, or a source may not be used as asked."""


@dataclass(frozen=True)
class Registry:
    sources: tuple[Source, ...]

    def __iter__(self) -> Iterator[Source]:
        return iter(self.sources)

    def get(self, source_id: str) -> Source:
        for source in self.sources:
            if source.id == source_id:
                return source
        raise RegistryError(
            f"{source_id!r} is not in the licence registry. "
            "Add it under registry/sources/ with its licence evidence before using it."
        )

    def require(self, source_id: str, use: Use) -> Source:
        """The ingest gate. Returns the source, or raises if it may not be used this way.

        Anything that reaches a user needs an approved source. A gated or held source
        may still be read for an internal use it lists, so that a spike can inspect a
        file before anyone decides whether to rely on it.
        """
        source = self.get(source_id)
        if source.status is Status.APPROVED:
            if use in source.uses:
                return source
            allowed = ", ".join(source.uses) or "nothing"
            raise RegistryError(
                f"{source_id!r} is not registered for {use}. It is registered for: {allowed}."
            )

        internal = [u for u in source.uses if u in INTERNAL_USES]
        if source.status is not Status.BANNED and use in internal:
            return source
        message = f"{source_id!r} is {source.status}, not approved: {source.status_reason}"
        if internal and source.status is not Status.BANNED:
            message += f" Meanwhile it may be read for: {', '.join(internal)}."
        raise RegistryError(message)

    def attributions(self) -> list[tuple[Source, str]]:
        """Statements the product must display, for approved sources that reach users."""
        return [
            (source, source.attribution)
            for source in sorted(self.sources, key=lambda s: (s.publisher.lower(), s.id))
            if source.status is Status.APPROVED
            and source.attribution
            and not set(source.uses) <= INTERNAL_USES
        ]


def find(start: Path | None = None) -> Path:
    """The repository's registry, found by walking up from `start`."""
    start = (start or Path.cwd()).resolve()
    for folder in (start, *start.parents):
        candidate = folder / DEFAULT_PATH
        if candidate.is_dir():
            return candidate
    raise RegistryError(f"no {DEFAULT_PATH} in {start} or any folder above it")


def _describe(error: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in problem['loc']) or 'entry'}: {problem['msg']}"
        for problem in error.errors()
    )


def load(path: Path | None = None, *, enforce: bool = True) -> Registry:
    """Read a registry and refuse it if it breaks a rule. With no path, use the repository's.

    A folder is read as one file per dimension: `housing.toml` may only hold
    housing sources. A single file may hold anything.

    `enforce=False` is for tools that report problems instead of stopping at the
    first. Duplicate ids are refused either way, because the gate could not give
    a meaningful answer about them.
    """
    path = path or find()
    sources = _read_folder(path) if path.is_dir() else _read(path)

    repeated = sorted(i for i, n in Counter(s.id for s in sources).items() if n > 1)
    if repeated:
        raise RegistryError(f"{path}: id used more than once: {', '.join(repeated)}")
    if enforce:
        errors = [p for p in check(sources, date.today()) if p.severity is Severity.ERROR]
        if errors:
            listed = "; ".join(f"{p.source_id}: {p.message}" for p in errors)
            raise RegistryError(f"{path} breaks the registry rules: {listed}")
    return Registry(tuple(sources))


def _read_folder(folder: Path) -> list[Source]:
    files = sorted(f for f in folder.iterdir() if f.is_file() and f.suffix.lower() == ".toml")
    if not files:
        raise RegistryError(f"no .toml files in {folder}")
    sources: list[Source] = []
    for file in files:
        if file.suffix != ".toml" or file.stem not in Dimension:
            raise RegistryError(
                f"{file}: files are named <dimension>.toml, and {file.stem!r} is not a dimension"
                if file.suffix == ".toml"
                else f"{file}: files are named <dimension>.toml, in lower case"
            )
        for source in _read(file):
            if source.dimension != file.stem:
                raise RegistryError(
                    f"{file}: {source.id} has dimension {source.dimension}, "
                    f"so it belongs in {source.dimension}.toml"
                )
            sources.append(source)
    return sources


def _read(path: Path) -> list[Source]:
    try:
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RegistryError(f"no registry at {path}") from error
    except OSError as error:
        raise RegistryError(f"cannot read {path}: {error.strerror}") from error
    except UnicodeDecodeError as error:
        raise RegistryError(f"{path} is not UTF-8 text") from error
    except tomllib.TOMLDecodeError as error:
        raise RegistryError(f"{path} is not valid TOML: {error}") from error

    version = document.get("schema_version")
    if version != SCHEMA_VERSION:
        raise RegistryError(f"{path} has schema_version {version!r}, expected {SCHEMA_VERSION}")
    unknown = sorted(set(document) - {"schema_version", "source"})
    if unknown:
        raise RegistryError(
            f"{path}: unknown top-level key {unknown[0]!r}. Entries are written as [[source]]"
        )

    entries = cast(list[dict[str, Any]], document.get("source", []))
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise RegistryError(f"{path}: sources must be written as [[source]] tables")

    sources: list[Source] = []
    for position, entry in enumerate(entries, start=1):
        try:
            sources.append(Source.model_validate(entry))
        except ValidationError as error:
            label = entry.get("id", f"entry {position}")
            raise RegistryError(f"{path}: {label}: {_describe(error)}") from error
    return sources
