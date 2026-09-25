"""Read a release folder from disk, and say in one line why one was refused.

`read_release` does one thing: it reads every file in the folder into bytes
and hands them to `open_release` in core, which does all the checking. The API
loads a release through the same function, so the two cannot come to disagree
about what a valid release is.

`read_served` reads a release as it may be served. A release that is not made
up is served only with what it was built with: the hashes of the build, its
evidence and its lock, in the folder beside it. It hands their bytes to
`open_served` in core, as the API does.

`read_built` reads a release as it was built, by its own catalogue, through
`open_built` in core. It is for holding one build against another, and what it
reads is never served: a release of another catalogue may hold what core no
longer does.

One file is left out and never read: the `.DS_Store` a Mac leaves in any folder
that has been opened in a window. It is no part of a release and says nothing
about one. Every other stray file is handed over, and refused.
"""

from collections.abc import Mapping
from pathlib import Path

from burro_core.release import (
    BUILD_FOLDER,
    EVIDENCE,
    HASHES,
    LOCK,
    InMemoryRelease,
    ReleaseError,
    open_built,
    open_release,
    open_served,
)

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
    "one differently: a label alone may differ, in plain words",
    "vibes_match_core": "holds a vibe that is not the catalogue's but for what a person may "
    "adjust, or a recipe that breaks a rule, or not the vibes its manifest says it carries",
    "names_name_no_place": "holds a name, a label or a line that a person gave and that "
    "names an area, a borough or a place of the release. A vibe and a measure are of every "
    "area alike",
    "held_off_stays_held_off": "places an area on a vibe that the catalogue's own recipe "
    "places none on: its shares were moved to the parts that have a figure",
    "changes_are_named": "carries a recipe, a name or a label that is not the catalogue's, "
    "and does not say which file of changes it was built with",
    "rows_are_complete": "lacks a row that every release must have",
    "values_are_in_range": "holds a number outside the range it may take",
    "null_means_null": "has a value without its percentile, or a percentile without its value",
    "bands_match_raw": "holds a band that is not the one its scores give, or a spread that "
    "does not hold it",
    "sources_are_stated": "does not say where a figure came from, or when. Only a preview "
    "that holds no journey or no station may leave the sources of that file unstated",
    "neighbours_are_symmetric": "lists a neighbour that does not list it back",
    "finished_release_is_whole": "does not say the release is a preview, and the release "
    "holds no journey, no place to reach, no cost or no station",
    "percentiles_match_values": "holds a percentile that is not the one its values give",
    "raw_matches_recipe": "places an area on a vibe by figures that are not the ones the "
    "release holds for it, or by another recipe than it carries, or says more of the recipe "
    "was there than was",
    "scores_match_raw": "holds a score for a vibe that is not the one its raw values give",
    # What `open_served` refuses for. The file is one of the folder beside the release.
    "real_release_has_its_build": "is not in the folder beside the release. A release that "
    "is not made up is served only with the hashes of its build, its evidence and its lock",
    "build_is_of_this_release": "holds the hashes of the build of another release",
    "build_is_as_it_was_written": "is not as it was when the release was built: it has "
    "changed since, or it is of another build",
    "changes_are_locked": "does not name the file of changes the release says it was built "
    "with, and no other: it is not there, or it names none, another or more than one",
    # What `open_built` refuses for, of a release that is read by its own catalogue.
    "versions_are_its_own": "has a schema version that this code does not read, or says "
    "another version of the catalogue than the manifest of its release does",
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


def beside(folder: Path) -> Path:
    """The folder beside a release that holds what it was built with."""
    return folder.resolve().with_name(f"{folder.resolve().name}{BUILD_FOLDER}")


def _built_with(folder: Path) -> dict[str, bytes] | None:
    """The bytes of the hashes, the evidence and the lock beside a release, where they are."""
    found: dict[str, bytes] = {}
    for name in (HASHES, EVIDENCE, LOCK):
        try:
            found[name] = (beside(folder) / name).read_bytes()
        except OSError:
            continue
    return found or None


def read_served(folder: Path) -> InMemoryRelease:
    """The release in `folder`, as it may be served: held to what it was built with.

    It is `read_release`, and then the release is held to the folder beside
    it. A made-up release needs nothing beside it. Any other is refused unless
    the hashes of its build, its evidence and its lock are there and are as
    they were when it was built.
    """
    files = _files_of(folder)
    try:
        return open_served(folder.resolve().name, files, _built_with(folder))
    except ReleaseError as error:
        raise UnreadableRelease(folder, error, missing=_is_missing(error, files)) from None


def read_built(folder: Path) -> InMemoryRelease:
    """The release in `folder`, as it was built: read by its own catalogue, and held to
    what it was built with.

    It is `read_served`, but that the release is held to its own catalogue and
    not to core's of today. It is for holding one build against another. What
    it gives back is never served.
    """
    files = _files_of(folder)
    try:
        return open_built(folder.resolve().name, files, _built_with(folder))
    except ReleaseError as error:
        raise UnreadableRelease(folder, error, missing=_is_missing(error, files)) from None


def _is_missing(error: ReleaseError, files: dict[str, bytes]) -> bool:
    """Whether a refusal is of a file of the release that is not there."""
    return error.file not in files and error.rule in ("files_match_manifest", "files_are_expected")


def read_release(folder: Path) -> InMemoryRelease:
    """The release in `folder`, checked against its manifest and every rule of the contract.

    Raises `UnreadableRelease` if a file is missing, extra, changed or
    malformed, or if the release breaks a rule. A file named `IGNORED` is not
    an extra file: it is left out, and never opened.
    """
    files = _files_of(folder)
    try:
        # The folder's own name, even when it was given as `.` or through a link.
        return open_release(folder.resolve().name, files)
    except ReleaseError as error:
        raise UnreadableRelease(folder, error, missing=error.file not in files) from None


def _files_of(folder: Path) -> dict[str, bytes]:
    """The bytes of every file in the folder of a release, by its name."""
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
    return files
