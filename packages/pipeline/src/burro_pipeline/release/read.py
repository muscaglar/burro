"""Read a release folder from disk, and say in one line why one was refused.

`read_release` does one thing: it reads every file in the folder into bytes
and hands them to `open_release` in core, which does all the checking. The API
loads a release through the same function, so the two cannot come to disagree
about what a valid release is.

One file is left out and never read: the `.DS_Store` a Mac leaves in any folder
that has been opened in a window. It is no part of a release and says nothing
about one. Every other stray file is handed over, and refused.
"""

from collections.abc import Mapping
from pathlib import Path

from burro_core.release import InMemoryRelease, ReleaseError, open_release

FOLDER_IS_READABLE = "folder_is_readable"
FILE_IS_READABLE = "file_is_readable"
MISSING = "is missing"
# The one name that is left out, spelt exactly so. The writer leaves it where it is too.
IGNORED = ".DS_Store"

# What each refusal means, in words that finish a sentence beginning with the
# file. The rule's own name follows in brackets, for the tests and for a search.
MEANING: Mapping[str, str] = {
    FOLDER_IS_READABLE: "is not a folder that can be read",
    FILE_IS_READABLE: "cannot be read as a file",
    "files_match_manifest": "is not the file the manifest lists: it has changed, or it does "
    "not belong in the folder",
    "json_is_valid": "is not valid JSON",
    "shape_is_valid": "is not shaped as the contract says: a field is missing, unknown or of "
    "the wrong type",
    "files_are_expected": "is missing, or is not a file a release has",
    "release_id_matches_folder": "names a release other than the folder it is in",
    "versions_match": "has a schema or catalogue version that this code does not read",
    "synthetic_is_consistent": "mixes synthetic and real: an id, a source or the flag "
    "disagrees with the rest",
    "ids_are_unique": "repeats an id, or holds out of order a list that must be sorted",
    "references_resolve": "names an area, destination, place, station or source that the "
    "release does not have",
    "catalogue_matches_core": "holds a feature or tag the catalogue does not, or describes "
    "one differently",
    "rows_are_complete": "lacks a row that every release must have",
    "values_are_in_range": "holds a number outside the range it may take",
    "null_means_null": "has a value without its percentile, or a percentile without its value",
    "sources_are_stated": "does not say where a figure came from, or when",
    "neighbours_are_symmetric": "lists a neighbour that does not list it back",
    # What `write_release` refuses for.
    "real_release_needs_a_registry": "says the release is real, and a real release is written "
    "only with the licence registry to check its sources against",
    "release_is_never_overwritten": "is already written, and a real release never changes: a "
    "correction is a new release",
    "folder_holds_something_else": "is not part of a release, so the folder was left as it was",
}


def in_words(error: ReleaseError, folder: Path, missing: bool = False) -> str:
    """A refusal in one line a person can act on: where, what is wrong, and the rule's name."""
    meaning = MISSING if missing else MEANING.get(error.rule, "breaks a rule")
    where = f"{error.file}, at {error.row}," if error.row else error.file
    subject = f"{folder}: {where}" if where else str(folder)
    return f"{subject} {meaning} [{error.rule}]"


class UnreadableRelease(ReleaseError):
    """A release folder that was refused, said in one line a person can act on.

    It is a `ReleaseError` with the same file, row and rule. Like one, it says
    where and why and never repeats a value from the file.
    """

    def __init__(self, folder: Path, error: ReleaseError, missing: bool = False) -> None:
        super().__init__(error.file, error.rule, error.row)
        self.line = in_words(error, folder, missing)

    def __str__(self) -> str:
        return self.line


def read_release(folder: Path) -> InMemoryRelease:
    """The release in `folder`, checked against its manifest and every rule of the contract.

    Raises `UnreadableRelease` if a file is missing, extra, changed or
    malformed, or if the release breaks a rule. A file named `IGNORED` is not
    an extra file: it is left out, and never opened.
    """
    files: dict[str, bytes] = {}
    try:
        entries = sorted(folder.iterdir())
    except OSError:
        raise UnreadableRelease(folder, ReleaseError("", FOLDER_IS_READABLE)) from None
    for entry in entries:
        try:
            if entry.name == IGNORED and entry.is_file():
                continue
            files[entry.name] = entry.read_bytes()
        except OSError:
            # A folder inside the folder, or a file this user may not read.
            raise UnreadableRelease(folder, ReleaseError(entry.name, FILE_IS_READABLE)) from None
    try:
        # The folder's own name, even when it was given as `.` or through a link.
        return open_release(folder.resolve().name, files)
    except ReleaseError as error:
        raise UnreadableRelease(folder, error, missing=error.file not in files) from None
