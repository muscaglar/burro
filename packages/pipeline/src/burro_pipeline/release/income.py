"""Write the household income of a release to a folder of its own, and read one back.

The figure is no file of a release. It stands in a folder beside one, named for
the release with `-income` after it, and holds two files: the figures, and a
manifest with their hash. `open_income` in core is the only judge of the
folder, so the pipeline that writes one and the API that loads one cannot come
to disagree about what it is.

This is where the licence gate stands for it. The source a real one cites must
be registered for `display`, and the check runs before anything is written. The
registry gives household income no use that ranks, so no build can take it for
a measure. A made-up figure cites only the reserved source `synthetic`, which
is no dataset at all, so the registry is not asked.
"""

import hashlib
from pathlib import Path

from burro_core.income import (
    INCOME,
    INCOME_FOLDER,
    MANIFEST,
    Income,
    IncomeError,
    IncomeManifest,
    open_income,
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
    "with -income after it",
    "files_match_manifest": "is not the file the manifest lists: it is missing, it has "
    "changed, or it does not belong in the folder",
    "json_is_valid": "is not valid JSON",
    "shape_is_valid": "is not shaped as the contract says: a field is missing, unknown or of "
    "the wrong type",
    "source_is_stated": "does not name the source the figures name",
    "income_is_of_the_release": "was made for another release, or says it is made up where "
    "the release does not",
    "made_up_is_said": "mixes made-up and real: the source, an area or the address disagrees "
    "with the rest",
    "areas_are_the_releases": "does not hold every area of the release once, in the order "
    "of its id, and no other",
    "limits_hold_the_estimate": "holds an estimate without both its limits, or outside them",
    "year_is_a_year": "is of a period that is not twelve months",
    "real_income_needs_a_registry": "says the figures are real, and real ones are written "
    "only with the licence registry to check their source against",
    "income_is_never_overwritten": "is already written, and a real one never changes",
    "folder_holds_something_else": "is not part of it, so the folder was left as it was",
}


def in_words(error: IncomeError, folder: Path) -> str:
    """A refusal in one line a person can act on: where, what is wrong, and the rule's name."""
    meaning = MEANING.get(error.rule, "breaks a rule")
    where = f"{error.file}, at {error.row}," if error.row else error.file
    subject = f"{folder}: {where}" if where else str(folder)
    return f"{subject} {meaning} [{error.rule}]"


class UnreadableIncome(IncomeError):
    """The folder that was refused, said in one line a person can act on."""

    def __init__(self, folder: Path, error: IncomeError) -> None:
        super().__init__(error.file, error.rule, error.row)
        self.line = in_words(error, folder)

    def __str__(self) -> str:
        return self.line


def folder_of(release_id: str) -> str:
    return f"{release_id}{INCOME_FOLDER}"


def _check_source(income: Income, registry: Registry | None) -> None:
    """The licence gate. Raises `RegistryError` for a source that may not be shown."""
    if income.synthetic:
        return
    if registry is None:
        raise IncomeError(MANIFEST, "real_income_needs_a_registry")
    try:
        registry.require(income.source.source_id, Use.DISPLAY)
    except RegistryError as error:
        raise RegistryError(f"{INCOME}: {error}") from None


def packed(income: Income) -> dict[str, bytes]:
    """The bytes of both files. The manifest is worked out from the figures as they are written."""
    content = canonical_json(income.model_dump(mode="json"))
    manifest = IncomeManifest(
        release_id=income.release_id,
        synthetic=income.synthetic,
        income_sha256=hashlib.sha256(content).hexdigest(),
        income_bytes=len(content),
        source=income.source,
    )
    return {INCOME: content, MANIFEST: canonical_json(manifest.model_dump(mode="json"))}


def _refuse_to_overwrite(target: Path, names: set[str], synthetic: bool) -> None:
    if not target.exists():
        return
    if not synthetic:
        raise IncomeError(MANIFEST, "income_is_never_overwritten")
    for entry in sorted(target.iterdir()):
        if entry.name == IGNORED and entry.is_file():
            continue
        if entry.name not in names or not entry.is_file():
            raise IncomeError(entry.name, "folder_holds_something_else")


def _area_ids(release: InMemoryRelease) -> list[str]:
    return [area.area_id for area in release.neighbourhoods]


def write_income(
    income: Income, release: InMemoryRelease, folder: Path, registry: Registry | None = None
) -> Income:
    """Write the figures into `folder`, in a folder of their own named for the release.

    Nothing is written unless the source passes the gate and the bytes open as
    the figures of this release. The manifest goes last, so a folder that was
    only half written has none and cannot be opened.
    """
    _check_source(income, registry)
    manifest = release.manifest
    name = folder_of(manifest.release_id)
    files = packed(income)
    written = open_income(name, files, manifest.release_id, manifest.synthetic, _area_ids(release))

    target = folder / name
    _refuse_to_overwrite(target, set(files), income.synthetic)
    target.mkdir(parents=True, exist_ok=True)
    (target / MANIFEST).unlink(missing_ok=True)
    (target / INCOME).write_bytes(files[INCOME])
    (target / MANIFEST).write_bytes(files[MANIFEST])
    return written


def read_income(folder: Path, release: InMemoryRelease) -> Income:
    """The figures in `folder`, held to every rule and to the release they were made for.

    Raises `UnreadableIncome` if a file is missing, extra, changed or
    malformed, or if the figures break a rule. A file named `IGNORED` is left
    out, as the reader of a release leaves it out.
    """
    files: dict[str, bytes] = {}
    try:
        entries = sorted(folder.iterdir())
    except OSError:
        raise UnreadableIncome(folder, IncomeError("", FOLDER_IS_READABLE)) from None
    for entry in entries:
        try:
            if entry.name == IGNORED and entry.is_file():
                continue
            files[entry.name] = entry.read_bytes()
        except OSError:
            raise UnreadableIncome(folder, IncomeError(entry.name, FILE_IS_READABLE)) from None
    manifest = release.manifest
    try:
        return open_income(
            folder.resolve().name,
            files,
            manifest.release_id,
            manifest.synthetic,
            _area_ids(release),
        )
    except IncomeError as error:
        raise UnreadableIncome(folder, error) from None
