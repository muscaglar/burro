"""Write the census of a release to a folder of its own, and read one back.

The census is no file of a release. It stands in a folder beside one, named for
the release with `-residents` after it, and holds two files: the census, and a
manifest with its hash. `open_census` in core is the only judge of the folder,
so the pipeline that writes one and the API that loads one cannot come to
disagree about what a census is.

This is where the licence gate stands for a census. Every source a real one
cites must be registered for the one use `census_table`, and the check runs
before anything is written. A made-up count cites only the reserved source
`synthetic`, which is no dataset at all, so the registry is not asked.
"""

import hashlib
from pathlib import Path

from burro_core.census import (
    CENSUS,
    MANIFEST,
    RESIDENTS_FOLDER,
    Census,
    CensusError,
    CensusManifest,
    open_census,
)
from burro_core.release import InMemoryRelease

from burro_pipeline.registry import Registry, RegistryError, Use
from burro_pipeline.release.read import IGNORED
from burro_pipeline.release.write import canonical_json

FOLDER_IS_READABLE = "folder_is_readable"
FILE_IS_READABLE = "file_is_readable"

# What each refusal means, in words that finish a sentence beginning with the file.
MEANING = {
    FOLDER_IS_READABLE: "is not a folder that can be read",
    FILE_IS_READABLE: "cannot be read as a file",
    "folder_is_named_for_the_release": "is in a folder that is not named for the release "
    "with -residents after it",
    "files_match_manifest": "is not the file the manifest lists: it is missing, it has "
    "changed, or it does not belong in the folder",
    "json_is_valid": "is not valid JSON",
    "shape_is_valid": "is not shaped as the contract says: a field is missing, unknown or of "
    "the wrong type",
    "sources_are_stated": "does not name the sources the census names",
    "census_is_of_the_release": "was made for another release, or says it is made up where "
    "the release does not",
    "made_up_is_said": "mixes made-up and real: a source, an area or an address disagrees "
    "with the rest",
    "tables_are_in_order": "holds a kind of table twice, a row twice, a row that stands "
    "under no group, or a table whose source it does not name",
    "areas_are_the_releases": "does not hold every area of the release once, in the order "
    "of its id, and no other",
    "rows_are_complete": "lacks a table for an area, or a count for a row of one",
    "too_few_are_left_out": "gives shares where too few were counted for one to be steady",
    "small_counts_are_withheld": "holds a count that is under 1 in 100 of those counted, or "
    "is more than were counted",
    "table_is_named_by_its_source": "holds a table that the registry's entry for its source "
    "does not name",
    "real_census_needs_a_registry": "says the census is real, and a real one is written "
    "only with the licence registry to check its sources against",
    "census_is_never_overwritten": "is already written, and a real census never changes",
    "folder_holds_something_else": "is not part of a census, so the folder was left as it was",
}


def in_words(error: CensusError, folder: Path) -> str:
    """A refusal in one line a person can act on: where, what is wrong, and the rule's name."""
    meaning = MEANING.get(error.rule, "breaks a rule")
    where = f"{error.file}, at {error.row}," if error.row else error.file
    subject = f"{folder}: {where}" if where else str(folder)
    return f"{subject} {meaning} [{error.rule}]"


class UnreadableCensus(CensusError):
    """The folder of a census that was refused, said in one line a person can act on."""

    def __init__(self, folder: Path, error: CensusError) -> None:
        super().__init__(error.file, error.rule, error.row)
        self.line = in_words(error, folder)

    def __str__(self) -> str:
        return self.line


def folder_of(release_id: str) -> str:
    return f"{release_id}{RESIDENTS_FOLDER}"


def _check_sources(census: Census, registry: Registry | None) -> None:
    """The licence gate. Raises `RegistryError` for a source that may not feed the census table."""
    if census.synthetic:
        return
    if registry is None:
        raise CensusError(MANIFEST, "real_census_needs_a_registry")
    named: dict[str, tuple[str, ...]] = {}
    for source in census.sources:
        try:
            named[source.source_id] = registry.require(source.source_id, Use.CENSUS_TABLE).tables
        except RegistryError as error:
            raise RegistryError(f"{CENSUS}: {error}") from None
    for position, table in enumerate(census.tables):
        # An entry names the tables it may feed the page with. One it does not name is
        # refused, whatever the file that came with it holds.
        if table.table_code not in named.get(table.source_id, ()):
            raise CensusError(CENSUS, "table_is_named_by_its_source", f"tables[{position}]")


def packed(census: Census) -> dict[str, bytes]:
    """The bytes of both files. The manifest is worked out from the census as it is written."""
    content = canonical_json(census.model_dump(mode="json"))
    manifest = CensusManifest(
        release_id=census.release_id,
        synthetic=census.synthetic,
        census_sha256=hashlib.sha256(content).hexdigest(),
        census_bytes=len(content),
        sources=census.sources,
    )
    return {CENSUS: content, MANIFEST: canonical_json(manifest.model_dump(mode="json"))}


def _refuse_to_overwrite(target: Path, names: set[str], synthetic: bool) -> None:
    if not target.exists():
        return
    if not synthetic:
        raise CensusError(MANIFEST, "census_is_never_overwritten")
    for entry in sorted(target.iterdir()):
        if entry.name == IGNORED and entry.is_file():
            continue
        if entry.name not in names or not entry.is_file():
            raise CensusError(entry.name, "folder_holds_something_else")


def _area_ids(release: InMemoryRelease) -> list[str]:
    return [area.area_id for area in release.neighbourhoods]


def write_census(
    census: Census, release: InMemoryRelease, folder: Path, registry: Registry | None = None
) -> Census:
    """Write a census into `folder`, in a folder of its own named for the release.

    Nothing is written unless the sources pass the gate and the bytes open as
    a census of this release. The manifest goes last, so a folder that was
    only half written has none and cannot be opened.
    """
    _check_sources(census, registry)
    manifest = release.manifest
    name = folder_of(manifest.release_id)
    files = packed(census)
    written = open_census(name, files, manifest.release_id, manifest.synthetic, _area_ids(release))

    target = folder / name
    _refuse_to_overwrite(target, set(files), census.synthetic)
    target.mkdir(parents=True, exist_ok=True)
    (target / MANIFEST).unlink(missing_ok=True)
    (target / CENSUS).write_bytes(files[CENSUS])
    (target / MANIFEST).write_bytes(files[MANIFEST])
    return written


def read_census(folder: Path, release: InMemoryRelease) -> Census:
    """The census in `folder`, held to every rule and to the release it was made for.

    Raises `UnreadableCensus` if a file is missing, extra, changed or
    malformed, or if the census breaks a rule. A file named `IGNORED` is left
    out, as the reader of a release leaves it out.
    """
    files: dict[str, bytes] = {}
    try:
        entries = sorted(folder.iterdir())
    except OSError:
        raise UnreadableCensus(folder, CensusError("", FOLDER_IS_READABLE)) from None
    for entry in entries:
        try:
            if entry.name == IGNORED and entry.is_file():
                continue
            files[entry.name] = entry.read_bytes()
        except OSError:
            raise UnreadableCensus(folder, CensusError(entry.name, FILE_IS_READABLE)) from None
    manifest = release.manifest
    try:
        return open_census(
            folder.resolve().name,
            files,
            manifest.release_id,
            manifest.synthetic,
            _area_ids(release),
        )
    except CensusError as error:
        raise UnreadableCensus(folder, error) from None
