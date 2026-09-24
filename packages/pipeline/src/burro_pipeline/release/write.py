"""Write a release to disk: the licence gate, canonical JSON, checksums, the manifest last.

This is where the licence gate stands for a release. Every source a real
release cites must be registered for the use its file needs, and the check
runs before anything is written. A synthetic release cites only the reserved
source `synthetic`, which is no dataset at all, so the registry is not asked.
"""

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path
from typing import cast

from burro_core.release import (
    CATALOGUE,
    COST,
    DATA_FILES,
    MANIFEST,
    NEIGHBOURHOODS,
    PLACES,
    STATIONS,
    TRAVEL,
    Counts,
    FileEntry,
    InMemoryRelease,
    ReleaseError,
    open_release,
)

from burro_pipeline.registry import Registry, RegistryError, Use
from burro_pipeline.release.read import IGNORED

# The registry approves a source for a use, not in general. What a source must
# be registered for depends on the file that names it.
USE_OF = {
    CATALOGUE: Use.SCORING,
    COST: Use.SCORING,
    TRAVEL: Use.ROUTING,
    STATIONS: Use.DISPLAY,
    PLACES: Use.DESTINATION_SEARCH,
    NEIGHBOURHOODS: Use.GAZETTEER,
}
FLOAT_DECIMALS = 6


def _cited(release: InMemoryRelease) -> Iterator[tuple[str, str]]:
    """Every source the release names, with the file that names it."""
    for source_id in release.neighbourhoods_origin.source_ids:
        yield NEIGHBOURHOODS, source_id
    for source_id in release.stations_origin.source_ids:
        yield STATIONS, source_id
    for source_id in release.travel_table.source_ids:
        yield TRAVEL, source_id
    for metric in release.metrics:
        for source_id in metric.source_ids:
            yield CATALOGUE, source_id
    for cost in release.costs:
        for source_id in cost.source_ids:
            yield COST, source_id
    for place in release.places:
        yield PLACES, place.source_id


def _check_sources(release: InMemoryRelease, registry: Registry | None) -> None:
    """The licence gate. Raises `RegistryError` for a source that may not be used as it is.

    A synthetic release is let through, and cannot be a way round the gate:
    `open_release` runs next, and refuses a release that calls itself
    synthetic and cites anything but the reserved source.
    """
    if release.manifest.synthetic:
        return
    if registry is None:
        raise ReleaseError(MANIFEST, "real_release_needs_a_registry")
    for file, source_id in sorted(set(_cited(release))):
        try:
            registry.require(source_id, USE_OF[file])
        except RegistryError as error:
            raise RegistryError(f"{file}: {error}") from None


def _rounded(value: object) -> object:
    if isinstance(value, float):
        return round(value, FLOAT_DECIMALS)
    if isinstance(value, dict):
        return {key: _rounded(item) for key, item in cast(dict[str, object], value).items()}
    if isinstance(value, list):
        return [_rounded(item) for item in cast(list[object], value)]
    return value


def canonical_json(document: object) -> bytes:
    """The one way a release file is written, so that the same release is the same bytes."""
    text = json.dumps(
        _rounded(document),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return (text + "\n").encode("utf-8")


def _entry(name: str, content: bytes) -> FileEntry:
    return FileEntry(name=name, sha256=hashlib.sha256(content).hexdigest(), bytes=len(content))


def packed(release: InMemoryRelease) -> dict[str, bytes]:
    """The bytes of every file of a release, the manifest included.

    The manifest's list of files and its counts are worked out here from what
    is being written, so a manifest cannot say one thing and the folder another.
    """
    documents = release.documents()
    files = {name: canonical_json(documents[name]) for name in DATA_FILES}
    manifest = release.manifest.replace(
        files=tuple(_entry(name, files[name]) for name in sorted(files)),
        counts=Counts(
            neighbourhoods=len(release.neighbourhoods),
            rankable=sum(area.rankable for area in release.neighbourhoods),
            destinations=len(release.destinations),
            places=len(release.places),
            stations=len({row.station_id for row in release.station_rows}),
        ),
    )
    return files | {MANIFEST: canonical_json(manifest.model_dump(mode="json"))}


def _refuse_to_overwrite(target: Path, names: set[str], synthetic: bool) -> None:
    """Let nothing be written over but an earlier build of a synthetic release."""
    if not target.exists():
        return
    # A real release never changes once written: a correction is a new release.
    if not synthetic:
        raise ReleaseError(MANIFEST, "release_is_never_overwritten")
    for entry in sorted(target.iterdir()):
        if entry.name == IGNORED and entry.is_file():
            # What a Mac leaves in a folder it has shown. The reader leaves it out, so a
            # folder that reads as a release can be rebuilt. It is not touched.
            continue
        if entry.name not in names or not entry.is_file():
            raise ReleaseError(entry.name, "folder_holds_something_else")


def write_release(
    release: InMemoryRelease, folder: Path, registry: Registry | None = None
) -> InMemoryRelease:
    """Write a release into `folder`, in a folder of its own named for its id.

    Returns the release as it was written, which is what `read_release` gives
    back. Nothing is written unless the sources pass the gate and the bytes
    open as a valid release. The manifest goes last, so a folder that was only
    half written has none and cannot be opened.
    """
    _check_sources(release, registry)
    release_id = release.manifest.release_id
    files = packed(release)
    written = open_release(release_id, files)

    target = folder / release_id
    _refuse_to_overwrite(target, set(files), release.manifest.synthetic)
    target.mkdir(parents=True, exist_ok=True)
    # An earlier build may have left a manifest. While the files change it would describe
    # a folder that is not there, so it goes first and comes back last.
    (target / MANIFEST).unlink(missing_ok=True)
    for name in DATA_FILES:
        (target / name).write_bytes(files[name])
    (target / MANIFEST).write_bytes(files[MANIFEST])
    return written
