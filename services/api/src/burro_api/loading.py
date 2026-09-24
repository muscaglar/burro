"""Loading a release: read the bytes, and leave every check to core.

The pipeline reads a release through the same `open_served`, so the two
cannot come to disagree about what a release that may be served is. Do not add
a check here: add a rule in core.

A release that is not made up is served only with what it was built with: the
hashes of the build, its evidence and its lock. They stand in a folder beside
the release, named for it with `-build` after. Their bytes are read here and
handed to core, which holds each to its hash. Nothing of the evidence is read
by the service.

One file is left out and never read, as the pipeline's reader leaves it out:
the `.DS_Store` a Mac leaves in any folder that has been opened in a window.
Every other stray file is handed over, and refused.

The census of a release is read the same way, from a folder of its own, and
core's `open_census` is its only judge. It is handed the bytes, and of the
release only its id, whether it is made up, and the ids of its areas.
"""

from pathlib import Path

from burro_core.census import Census, CensusError, open_census
from burro_core.release import (
    BUILD_FOLDER,
    EVIDENCE,
    HASHES,
    LOCK,
    InMemoryRelease,
    ReleaseError,
    open_served,
)

FOLDER_IS_READABLE = "folder_is_readable"
FILE_IS_READABLE = "file_is_readable"
# The one name that is left out, spelt exactly so. It is the pipeline's
# `IGNORED`, said again here because the two never import each other.
IGNORED = ".DS_Store"


def _built_with(folder: Path) -> dict[str, bytes] | None:
    """The bytes of the hashes, the evidence and the lock beside a release, where they are."""
    beside = folder.resolve().with_name(f"{folder.resolve().name}{BUILD_FOLDER}")
    found: dict[str, bytes] = {}
    for name in (HASHES, EVIDENCE, LOCK):
        try:
            found[name] = (beside / name).read_bytes()
        except OSError:
            # A file that is not there is for core to refuse, where the release needs it.
            continue
    return found or None


def load_release(folder: Path) -> InMemoryRelease:
    """The release in `folder`, checked against its manifest and every rule of the contract.

    A release that is not made up is held to what it was built with too.
    Raises `ReleaseError`, which names the file and the rule and never a value.
    """
    files: dict[str, bytes] = {}
    try:
        entries = sorted(folder.iterdir())
    except OSError:
        raise ReleaseError("", FOLDER_IS_READABLE) from None
    for entry in entries:
        try:
            if entry.name == IGNORED and entry.is_file():
                continue
            files[entry.name] = entry.read_bytes()
        except OSError:
            raise ReleaseError(entry.name, FILE_IS_READABLE) from None
    # The folder's own name, even when it was given as `.` or through a link.
    return open_served(folder.resolve().name, files, _built_with(folder))


def _files_of(folder: Path) -> dict[str, bytes] | None:
    """The bytes of every file in a folder, by name. `None` where the folder is not there."""
    if not folder.is_dir():
        return None
    files: dict[str, bytes] = {}
    for entry in sorted(folder.iterdir()):
        try:
            if entry.name == IGNORED and entry.is_file():
                continue
            files[entry.name] = entry.read_bytes()
        except OSError:
            raise CensusError(entry.name, FILE_IS_READABLE) from None
    return files


def load_census(
    folder: Path | None, release: InMemoryRelease, named: bool = False
) -> Census | None:
    """The census in `folder`, held to every rule and to the release, or `None` where none is.

    A folder that is not there is no census, unless whoever runs the service
    named it: then it is a fault. A folder that is there is never passed
    over: a census that breaks a rule raises `CensusError`, which names the
    file and the rule and never a value.
    """
    if folder is None:
        return None
    try:
        files = _files_of(folder)
    except OSError:
        raise CensusError("", FOLDER_IS_READABLE) from None
    if files is None:
        if named:
            raise CensusError("", FOLDER_IS_READABLE)
        return None
    manifest = release.manifest
    return open_census(
        folder.resolve().name,
        files,
        manifest.release_id,
        manifest.synthetic,
        [area.area_id for area in release.neighbourhoods],
    )
