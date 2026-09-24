"""What the walk of M0 shares: a made-up publisher, its files, and one simple method.

Nothing here is real, and nothing reaches a publisher. The city is the
synthetic one, under ids shaped like London's, because a file that was fetched
may only stand behind a release that is not called synthetic. It carries
gritty as land use, which is one of the two ways a release may. The publisher is
a server on the loopback address. Its files are made from the city's own
figures, so that a figure worked out from a file can be held to the figure the
release serves.

The step that works figures out is not built: it belongs to the first real
build. `flats_share` stands in for it, and is the one method the walk uses.
Every other row of evidence is carried over from the made-up evidence.
"""

import contextlib
import csv
import hashlib
import io
import json
import tempfile
from collections.abc import Callable, Generator, Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
from functools import cache
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

from burro_core.ids import FactKind, FeatureId, GrittyVariant
from burro_core.release import MANIFEST, InMemoryRelease, parse_release
from burro_pipeline import cli
from burro_pipeline.evidence import (
    Evidence,
    EvidenceRow,
    Kind,
    Lock,
    Method,
    Receipt,
    read_lock,
    read_receipts,
    state_of,
)
from burro_pipeline.evidence.made_up import made_up_evidence, span
from burro_pipeline.fetch import cli as fetch_cli
from burro_pipeline.fetch.download import Downloaded, Limits, download
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.registry import Registry, load
from burro_pipeline.release import build_synthetic
from burro_pipeline.release.write import write_release

from ..fetch.support import Answer, Served, serving

REPOSITORY = Path(__file__).parents[4]
RELEASE_ID = "lon-2026-09-23-01"
BUILT_AT = "2026-09-23T00:00:00Z"
COMMIT = "0123456789abcdef0123456789abcdef01234567"
# The one made-up source, and where its made-up publisher would be.
SURVEY = "made-up-survey"
PUBLISHER = "https://files.made-up.example"
CONTACT = "data@made-up.example"
# A string found nowhere else. It stands in every row of the publisher's files.
CANARY = "Zzyzx Parva"
HOMES, MEASURES = "made-up-homes.csv", "made-up-measures.csv"
FLATS = FeatureId.HOMES_FLATS
# Each area is made of this many units, each of this many homes. With these, a share
# to one decimal place and a coverage to two are each a whole number of homes.
UNITS, HOMES_A_UNIT = 100, 1000
# Under this share of an area's homes, a figure is not given.
ENOUGH = 0.5

REGISTRY = """
schema_version = 1

[[source]]
id = "made-up-survey"
name = "Made-up survey"
publisher = "Made-up Office"
url = "https://made-up.example/survey"
dimension = "housing"
licence = "OGL-3.0"
commercial_use = "yes"
share_alike = false
attribution = "Contains made-up data."
attribution_verified = true
status = "{status}"
status_reason = "{reason}"
uses = [{uses}]
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://made-up.example/licence", "https://files.made-up.example/about"]
file_urls = ["https://files.made-up.example/files/"]
"""
EVERY_USE = '"gazetteer", "scoring", "routing", "display", "destination_search"'

METHOD = Method(
    derivation_id="flats_share_of_units@1",
    sentence="Made up for a test: the flats of an area's units over their homes, to 1 decimal "
    "place, and not given where under 50 in 100 of its homes are in a unit with a count.",
    kind=Kind.MEASURED,
    parameters={"decimals": 1, "enough_in_100": 50},
    # The stand-in is part of this test, and `check` looks for a module of the pipeline.
    # So the method names the module that made the figures the stand-in is held to.
    code="burro_pipeline.release.synthetic",
)


@cache
def made_up_city() -> InMemoryRelease:
    """The synthetic city with gritty built from land use, which holds no recorded crime."""
    return build_synthetic(gritty_variant=GrittyVariant.A)


@cache
def city() -> InMemoryRelease:
    """The synthetic city under ids shaped like London's, every file citing the made-up source."""
    text = json.dumps(made_up_city().documents()).replace("syn-", "lon-")
    documents: dict[str, Any] = json.loads(text.replace('"synthetic"', f'"{SURVEY}"'))
    documents[MANIFEST].pop(SURVEY)
    documents[MANIFEST].update(synthetic=False, city="lon", seed=None)
    # The city credits its one source as the registry of the walk does.
    documents[MANIFEST]["sources"][0].update(
        name="Made-up survey",
        publisher="Made-up Office",
        licence="OGL-3.0",
        attribution="Contains made-up data.",
        url="https://made-up.example/survey",
    )
    return parse_release(documents)


@cache
def made_up() -> Evidence:
    """The made-up evidence of the synthetic city. The walk takes its rows and its files' names."""
    return made_up_evidence(made_up_city())


@cache
def files_of(release: InMemoryRelease) -> Mapping[str, bytes]:
    """What the made-up publisher serves, by file name.

    Two files are tables. One gives the homes of each unit and the area it is
    in. The other gives the flats of each unit, and leaves a unit out where the
    publisher holds no count. The rest hold one line that says what they are.
    """
    homes, flats = io.StringIO(), io.StringIO()
    in_homes, in_flats = csv.writer(homes), csv.writer(flats)
    in_homes.writerow(["unit_code", "unit_name", "area_code", "homes"])
    in_flats.writerow(["unit_code", "unit_name", "flats"])
    values = [value for value in release.features if value.feature_id == FLATS]
    for value in sorted(values, key=lambda value: value.area_id):
        counted = round(value.coverage * UNITS)
        assert counted / UNITS == value.coverage, "a coverage finer than the units can show"
        # The flats of the area, so that the share of its counted homes is the figure served.
        share = value.value if value.value is not None else 50.0
        left = round(share * counted * HOMES_A_UNIT / 100)
        for number in range(UNITS):
            unit = f"U{value.area_id[-4:]}{number:03d}"
            name = f"{CANARY} {number}"
            in_homes.writerow([unit, name, value.area_id, HOMES_A_UNIT])
            if number < counted:
                here = -(-left // (counted - number))
                left -= here
                in_flats.writerow([unit, name, here])
    served = {
        receipt.publisher_file: f"{CANARY}. Made up for a test. {receipt.publisher_file}\n".encode()
        for receipt in made_up().receipts
    }
    return served | {HOMES: homes.getvalue().encode(), MEASURES: flats.getvalue().encode()}


def the_list(
    files: Mapping[str, bytes],
    changed: Mapping[str, object] | None = None,
    without: Sequence[str] = (),
) -> str:
    """The list of the made-up publisher's files, as a person would write it.

    `changed` is what the list says otherwise of the file of measures. `without`
    names the files a shorter list leaves out.
    """
    written = ['schema_version = 1\nbuild = "made-up"\n']
    for receipt in made_up().receipts:
        name = receipt.publisher_file
        if name in without:
            continue
        entry: dict[str, object] = {
            "item": name.removeprefix("made-up-").split(".")[0],
            "source_id": SURVEY,
            "use": str(receipt.use),
            "what": f"A made-up file: {name}",
            "format": "csv" if name in (HOMES, MEASURES) else "other",
            "page": "https://made-up.example/survey",
            "url": f"{PUBLISHER}/files/{name}",
            "max_bytes": len(files[name]) + 1000,
            "edition": "made up",
            "data_period": receipt.data_period.model_dump(exclude_none=True),
        }
        if name == MEASURES:
            entry |= changed or {}
        lines = [f"{key} = {_toml(value)}" for key, value in entry.items()]
        written.append("[[file]]\n" + "\n".join(lines) + "\n")
    return "\n".join(written)


def _toml(value: object) -> str:
    """A value as a list of files writes it. A table is written on one line."""
    if isinstance(value, dict):
        table = cast(dict[str, object], value)
        return "{ " + ", ".join(f"{key} = {_toml(held)}" for key, held in table.items()) + " }"
    return json.dumps(value)


@dataclass(frozen=True)
class Figure:
    """One figure as the method gives it: the value, and how much of the area stood behind it."""

    value: float | None
    covered: float
    units_used: int
    units_expected: int


def flats_share(homes: Path, measures: Path) -> dict[str, Figure]:
    """Flats as a share of homes, for each area, from the publisher's two files.

    The flats of an area's units are added up, and so are the homes of those
    same units. A unit with no count of flats is left out of both, and counts
    against how much of the area was covered. Where under half the homes are
    covered, no figure is given. A mean of shares is never taken.
    """
    with measures.open(encoding="utf-8", newline="") as file:
        flats = {row["unit_code"]: int(row["flats"]) for row in csv.DictReader(file)}
    areas: dict[str, list[tuple[int, int | None]]] = {}
    with homes.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            found = (int(row["homes"]), flats.get(row["unit_code"]))
            areas.setdefault(row["area_code"], []).append(found)
    figures: dict[str, Figure] = {}
    for area, units in sorted(areas.items()):
        counted = [(homes, flats) for homes, flats in units if flats is not None]
        of_counted = sum(homes for homes, _ in counted)
        covered = of_counted / sum(homes for homes, _ in units)
        given = covered >= ENOUGH and of_counted > 0
        value = round(100 * sum(flats for _, flats in counted) / of_counted, 1) if given else None
        figures[area] = Figure(value, round(covered, 6), len(counted), len(units))
    return figures


def rows_of(receipts: Sequence[Receipt], figures: Mapping[str, Figure]) -> Iterator[EvidenceRow]:
    """A row for every figure of the city, resting on the files that were fetched.

    The row of a figure the walk worked out says so: it names the method, the
    two files and what was covered. Every other row is the made-up one, moved
    onto the fetched file of the same name.
    """
    before = made_up()
    named = {receipt.publisher_file: receipt for receipt in receipts}
    now = {old.file_id: named[old.publisher_file] for old in before.receipts}
    for row in before.rows:
        key = row.fact_id.replace("syn-", "lon-")
        if not row.inputs:
            # A measure the city does not carry rests on no file, and its row says so.
            yield EvidenceRow.model_validate(row.model_dump(mode="json") | {"fact_id": key})
            continue
        inputs = tuple(sorted((now[old] for old in row.inputs), key=lambda found: found.file_id))
        fields = row.model_dump(mode="json") | {
            "fact_id": key,
            "inputs": [receipt.file_id for receipt in inputs],
            "data_period": span(inputs).model_dump(mode="json"),
            "retrieved_on": max(receipt.retrieved_on for receipt in inputs),
        }
        if row.measure == f"{FactKind.FEATURE}/{FLATS}":
            figure = figures[row.area_id.replace("syn-", "lon-")]
            fields |= {
                "derivation_id": METHOD.derivation_id,
                "units_used": figure.units_used,
                "units_expected": figure.units_expected,
                "weight_covered": figure.covered,
                "state": state_of(figure.value is not None, figure.covered),
                "value": figure.value,
            }
        yield EvidenceRow.model_validate(fields)


def evidence_of(receipts: Sequence[Receipt], figures: Mapping[str, Figure]) -> Evidence:
    methods = (*made_up().methods, METHOD)
    return Evidence.of(RELEASE_ID, receipts, methods, rows_of(receipts, figures))


def as_the_publisher(served: Served) -> fetch_cli.Downloader:
    """The real download, which finds the made-up publisher at the stand-in's address.

    The stand-in speaks plain http on the loopback address, which a download
    refuses but in a test. So the address is changed on the way out, and changed
    back on the way in, and everything between is the code a real fetch runs.
    """

    def downloader(
        address: str,
        to: Path,
        limits: Limits,
        *,
        agent: str,
        may_redirect_to: tuple[str, ...] = (),
    ) -> Downloaded:
        assert address.startswith(PUBLISHER)
        got = download(
            address.replace(PUBLISHER, served.address, 1),
            to,
            limits,
            agent=agent,
            may_redirect_to=may_redirect_to,
            loopback_for_tests=True,
        )
        return replace(got, final_url=f"{PUBLISHER}{urlsplit(got.final_url).path}")

    return downloader


@dataclass(frozen=True)
class Said:
    """What a step said: its exit code, what anyone may read, and its words beside that."""

    code: int
    lines: list[str]
    words: str

    @property
    def everything(self) -> str:
        return "\n".join(self.lines) + self.words


@dataclass
class Walk:
    """One build on made-up files, step by step, in a folder of its own."""

    root: Path
    served: Served
    release: InMemoryRelease = field(default_factory=city)
    said: list[Said] = field(default_factory=list[Said])

    def __post_init__(self) -> None:
        self.files = files_of(self.release)
        self.store = self.root / "store"
        self.receipts = self.root / "data" / "receipts"
        self.locks = self.root / "data" / "locks"
        self.registry = self.root / "registry.toml"
        self.list = self.root / "made-up.toml"
        self.listing = self.root / "listing.json"
        self.evidence = self.root / "evidence.json"
        self.hashes = self.root / "hashes.json"
        self.report = self.root / "coverage.md"
        self.findings = self.root / "findings.txt"
        self.environment = {"BURRO_STORE_FOLDER": str(self.store), "BURRO_FETCH_CONTACT": CONTACT}
        self.root.mkdir(parents=True, exist_ok=True)
        self.register()
        self.list.write_text(the_list(self.files), encoding="utf-8")

    def register(self, status: str = "approved", reason: str = "", uses: str = EVERY_USE) -> None:
        """Write the licence registry, as it stands or as it would after a change."""
        text = REGISTRY.format(status=status, reason=reason, uses=uses)
        self.registry.write_text(text, encoding="utf-8")

    def run(self, run: Callable[[], int]) -> Said:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = run()
            except SystemExit as stopped:
                code = stopped.code if isinstance(stopped.code, int) else 2
        self.said.append(Said(code, out.getvalue().splitlines(), err.getvalue()))
        return self.said[-1]

    def step(self, *words: str | Path) -> Said:
        """Run a step as the command line runs it."""
        return self.run(lambda: cli.main([str(word) for word in words]))

    def kept(self) -> list[str | Path]:
        return ["--list", self.list, "--registry", self.registry, "--receipts", self.receipts]

    def fetch(self, *more: str) -> Said:
        words = ["fetch", *(str(word) for word in self.kept()), *more]
        downloader = as_the_publisher(self.served)
        return self.run(lambda: fetch_cli.main(words, self.environment, downloader))

    def with_the_store(self, *words: str | Path) -> Said:
        found = [str(word) for word in words]
        return self.run(lambda: fetch_cli.main(found, self.environment))

    def held(self) -> Said:
        return self.with_the_store("held", "--out", self.listing)

    def seal(self) -> Said:
        return self.step(
            *("seal", "--release-id", RELEASE_ID, "--built-at", BUILT_AT, "--commit", COMMIT),
            *("--list", self.list, "--receipts", self.receipts),
            *("--vault-listing", self.listing),
            *("--registry", self.registry, "--root", self.root, "--out", self.locks),
        )

    def lock(self) -> Lock:
        return read_lock(self.locks / f"{RELEASE_ID}.json")

    def receipt(self, name: str) -> Receipt:
        return next(found for found in read_receipts(self.receipts) if found.publisher_file == name)

    def taken(self, name: str) -> Path:
        """A file as a step of a build takes it: out of the store, and only if the lock names it."""
        copy = self.root / "taken" / name
        FolderStore(self.store).get(self.receipt(name).sha256, copy)
        self.lock().admit_file(copy)
        return copy

    def derive(self) -> dict[str, Figure]:
        return flats_share(self.taken(HOMES), self.taken(MEASURES))

    def write_evidence(self, figures: Mapping[str, Figure]) -> Evidence:
        found = evidence_of(read_receipts(self.receipts), figures)
        self.evidence.write_bytes(found.canonical())
        return found

    def write_hashes(self) -> Path:
        """The hashes of the build, as a build writes them: of what stands there now."""
        held = {
            "manifest_sha256": self.folder_of_the_release() / MANIFEST,
            "evidence_sha256": self.evidence,
            "lock_sha256": self.locks / f"{RELEASE_ID}.json",
        }
        hashes = {
            name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in held.items()
        }
        self.hashes.write_text(json.dumps({"release_id": RELEASE_ID} | hashes), encoding="utf-8")
        return self.hashes

    def check(self) -> Said:
        lock = self.locks / f"{RELEASE_ID}.json"
        return self.step(
            *("check", self.folder_of_the_release(), "--evidence", self.evidence),
            *("--lock", lock, "--registry", self.registry, "--list", self.findings),
            *("--hashes", self.write_hashes()),
        )

    def coverage(self) -> Said:
        folder = self.folder_of_the_release()
        return self.step("coverage", folder, "--evidence", self.evidence, "--out", self.report)

    def folder_of_the_release(self) -> Path:
        """The release, as a folder. It is written the first time a step asks for it."""
        folder = self.root / "releases" / RELEASE_ID
        if not folder.exists():
            approved = load_text(REGISTRY.format(status="approved", reason="", uses=EVERY_USE))
            write_release(self.release, folder.parent, approved)
        return folder

    def to_the_lock(self) -> None:
        """Every step up to the lock, each of which must pass."""
        for said in (self.fetch(), self.held(), self.seal()):
            assert said.code == 0, said.everything

    def to_the_end(self) -> Evidence:
        """Every step of the walk, each of which must pass."""
        self.to_the_lock()
        found = self.write_evidence(self.derive())
        for said in (self.check(), self.coverage()):
            assert said.code == 0, said.everything
        return found


def load_text(registry: str) -> Registry:
    """A licence registry, from its text."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "registry.toml"
        path.write_text(registry, encoding="utf-8")
        return load(path)


@contextlib.contextmanager
def publishing(files: Mapping[str, bytes]) -> Generator[Served]:
    """The made-up publisher, serving its files from the loopback address."""
    pages = {f"/files/{name}": Answer(body=content) for name, content in files.items()}
    with serving(lambda request: pages.get(request.path, Answer(404))) as served:
        yield served
