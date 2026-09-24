"""Loading a release: read the bytes, and leave every check to core.

The pipeline reads a release through the same `open_release`, so the two
cannot come to disagree about what a valid release is. Do not add a check
here: add a rule in core.

One file is left out and never read, as the pipeline's reader leaves it out:
the `.DS_Store` a Mac leaves in any folder that has been opened in a window.
Every other stray file is handed over, and refused.
"""

from pathlib import Path

from burro_core.release import InMemoryRelease, ReleaseError, open_release

FOLDER_IS_READABLE = "folder_is_readable"
FILE_IS_READABLE = "file_is_readable"
# The one name that is left out, spelt exactly so. It is the pipeline's
# `IGNORED`, said again here because the two never import each other.
IGNORED = ".DS_Store"


def load_release(folder: Path) -> InMemoryRelease:
    """The release in `folder`, checked against its manifest and every rule of the contract.

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
    return open_release(folder.resolve().name, files)
