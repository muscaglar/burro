"""What the tests of assemble share: the whole of a made-up build, as fetch would leave it.

Nothing here is real. The town is Quillhaven and Tallowgate, two boroughs that
do not exist, which the tests of cells draw in the North Sea. Its files are the
made-up files of the tests of cells and of each measure, each shaped as its
publisher's is. They are put in a store of their own, with a receipt for each
and a list that names them, and the step is run on them through the pipeline's
one command line.
"""

import hashlib
import io
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass, replace
from functools import cache
from pathlib import Path
from types import ModuleType

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId
from burro_pipeline.assemble import cli as assemble
from burro_pipeline.derive import (
    air_no2,
    conservation_cover,
    green_sites,
    homes_density,
    homes_flats,
    homes_pre1919,
    listed_buildings,
    road_major_exposure,
    road_traffic_nearby,
    schools_file,
    stops_file,
    town_centres,
    water_access,
)
from burro_pipeline.evidence.receipt import EditionFrom, How, Period, Receipt, Where
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.registry.model import Use

from .. import once
from ..cells.support import FILES, REPOSITORY, contents
from ..derive import (
    centres_support,
    food_support,
    green_support,
    heritage_support,
    land_use_support,
    noise_support,
    schools_support,
    stops_support,
    traffic_support,
    water_support,
)
from ..derive import test_air_no2 as grid
from ..derive import test_homes_density as by_band
from ..derive import test_homes_flats as by_kind
from ..derive import test_homes_pre1919 as by_period
from ..derive import test_road_major_exposure as by_road
from ..fetch.dated_support import header_of, register

RELEASE = "lon-2026-09-23-01"
BUILT_AT = "2026-09-23T00:00:00Z"
# No commit of any repository. A test seals in a folder that is no repository, because
# the tests may themselves be run in a working copy with changes.
COMMIT = "0" * 40
REGISTRY = REPOSITORY / "registry" / "sources"
ONE, TWO, THREE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
PAGE = "https://made-up.example/about-these-files"
# Where a made-up register states its own edition, as the list of the real one says it.
IN_THE_HEADER = 'where = "xml_header", at = "Header/ExtractDate", words = "extract of"'
REGISTER = "register-501"
# The roads of the made-up build, laid where its homes are taken to stand: the middles of
# the squares of the made-up grid of the air. One A road runs north beside the square that
# most homes stand on, and a road of a lower class runs by each of the other three, so that
# every centre is near some road and the homes of one square alone are near a main road.
ROADS = (
    by_road.straight("A Road", (700_450, 400_000), (700_450, 401_000)),
    by_road.straight("Unclassified", (701_000, 400_400), (702_000, 400_400)),
    by_road.straight("Unclassified", (701_000, 401_400), (702_000, 401_400)),
    by_road.straight("B Road", (705_000, 400_400), (706_000, 400_400)),
)


@cache
def the_roads() -> bytes:
    """The made-up roads as their publisher packs them: a GeoPackage in a zip."""
    return by_road.zipped(by_road.network(ROADS))


@dataclass(frozen=True)
class File:
    """One made-up file of the build: what the list says of it, and what it holds."""

    item: str
    source_id: str
    use: Use
    name: str
    edition: str
    period: str
    content: bytes
    # Whether the list states no edition of it, and says where the file states its own.
    # Its publisher puts each edition at one address, so its address names no edition.
    states_its_own: bool = False

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()

    @property
    def url(self) -> str:
        if self.states_its_own:
            return f"https://files.made-up.example/{self.item}/{self.name}"
        return f"https://files.made-up.example/{self.item}/{self.sha256[:8]}"

    def receipt(self) -> Receipt:
        read = EditionFrom(where=Where.XML_HEADER, at="Header/ExtractDate", period_too=True)
        return Receipt(
            file_id=file_id_of(self.sha256),
            source_id=self.source_id,
            use=self.use,
            publisher_file=self.name,
            url=self.url,
            listed_url=self.url if self.states_its_own else None,
            sha256=self.sha256,
            bytes=len(self.content),
            retrieved_at="2026-09-23T21:09:21Z",
            how=How.FETCHED,
            edition=self.edition,
            edition_from=read if self.states_its_own else None,
            data_period=Period(as_at=self.period),
        )


def _of_cells(item: str, which: str, period: str) -> File:
    source_id, use, name, edition = FILES[which]
    return File(item, source_id, use, name, edition, period, contents()[which])


def files() -> dict[str, File]:
    """Every file of the made-up build, by its name in the list."""
    voa = "2025-03-31"
    tables = (
        ("homes-by-band", homes_density.SOURCE, by_band),
        ("homes-by-kind", homes_flats.SOURCE, by_kind),
        ("homes-by-period", homes_pre1919.SOURCE, by_period),
    )
    found = [
        _of_cells("lookup", "lookup", "2022-12"),
        _of_cells("homes", "homes", "2021-03-21"),
        _of_cells("outlines", "outlines", "2021-12"),
        _of_cells("lsoa-outlines", "lsoa_outlines", "2021-12"),
        # The centres stand where the tests of the grid put them, so that one area has no
        # figure for the air: most of its homes are off the made-up grid.
        File(
            "centres",
            FILES["centres"][0],
            FILES["centres"][1],
            FILES["centres"][2],
            FILES["centres"][3],
            "2021-12",
            grid.centres_at(grid.PLACED),
        ),
        *(
            File(item, source, Use.SCORING, made.NAME, "2025", voa, made.zipped(made.table_of()))
            for item, source, made in tables
        ),
        File("grid", air_no2.SOURCE, Use.SCORING, grid.GRID_NAME, "2024", "2024", grid.grid_csv()),
        File(
            "noise",
            noise_support.SOURCE,
            Use.SCORING,
            noise_support.WORKBOOK_NAME,
            noise_support.EDITION,
            noise_support.YEAR,
            noise_support.file_8(),
        ),
        # The sites are cut to squares of the grid, a file for each. The town stands at the
        # corner of four, so its build holds four files of the one source.
        *(
            File(
                f"sites-{letters}",
                green_sites.SOURCE,
                Use.SCORING,
                f"opgrsp_gml3_{letters}.zip",
                green_support.EDITION,
                green_support.EDITION,
                content,
            )
            for letters, content in sorted(green_support.tiles().items())
        ),
        File(
            "land-use",
            land_use_support.SOURCE,
            Use.SCORING,
            land_use_support.WORKBOOK_NAME,
            land_use_support.EDITION,
            land_use_support.AS_AT,
            land_use_support.published(),
        ),
        File(
            "roads",
            road_major_exposure.SOURCE,
            Use.SCORING,
            by_road.ZIP_NAME,
            by_road.EDITION,
            by_road.EDITION,
            the_roads(),
        ),
        # A count point on each road, so that every home of the town has a figure of traffic.
        File(
            "traffic",
            road_traffic_nearby.SOURCE,
            Use.SCORING,
            road_traffic_nearby.FILE,
            f"retrieved {traffic_support.RETRIEVED}",
            "2025",
            traffic_support.counts_zip(traffic_support.BY_THE_ROADS),
        ),
        File(
            "schools",
            schools_file.SOURCE,
            Use.SCORING,
            schools_support.ZIP_NAME,
            schools_support.DAY,
            schools_support.DAY,
            schools_support.zipped(),
        ),
        File(
            "stops",
            stops_file.SOURCE,
            Use.SCORING,
            stops_support.NAME,
            stops_support.EDITION,
            stops_support.SAVED,
            stops_support.stops_csv(),
        ),
        File(
            "town-centres",
            town_centres.SOURCE,
            Use.SCORING,
            town_centres.FILE,
            centres_support.EDITION,
            centres_support.AS_AT,
            centres_support.centres_gpkg(),
        ),
        File(
            "water",
            water_access.SOURCE,
            Use.SCORING,
            water_support.ZIP_NAME,
            water_support.EDITION,
            water_support.EDITION,
            water_support.the_water(),
        ),
        # The food register is a file for each authority, and the town has two. Each file
        # holds what stands by the homes of its own borough.
        *(
            File(
                f"register-{authority}",
                food_support.SOURCE,
                Use.SCORING,
                food_support.name_of(authority),
                f"extract of {food_support.DAY}",
                food_support.DAY,
                food_support.register_xml(_beside(middle), authority),
            )
            for authority, middle in (
                (food_support.QUILLHAVEN, grid.B),
                (food_support.TALLOWGATE, grid.OFF_THE_GRID),
            )
        ),
        # The two files of the planning data platform, with a record in each of the two
        # authorities of the town, so that every area has a figure.
        File(
            "conservation-areas",
            conservation_cover.SOURCE,
            Use.SCORING,
            conservation_cover.FILE,
            f"retrieved {heritage_support.DAY}",
            heritage_support.DAY,
            heritage_support.areas_file([*heritage_support.AREAS, heritage_support.QUAYSIDE]),
        ),
        File(
            "listed-buildings",
            listed_buildings.SOURCE,
            Use.SCORING,
            listed_buildings.FILE,
            f"retrieved {heritage_support.DAY}",
            heritage_support.DAY,
            heritage_support.entries_file(
                [*heritage_support.ENTRIES, heritage_support.ON_THE_ISLAND]
            ),
        ),
    ]
    return {file.item: file for file in found}


def _beside(middle: tuple[int, int]) -> tuple[food_support.Business, ...]:
    """A place to eat, a pub, a takeaway and a shop by the middle of a square, and one nowhere."""
    east, north = middle[0] - food_support.EAST, middle[1] - food_support.NORTH
    kinds = (food_support.EAT, food_support.PUB, food_support.TAKEAWAY, food_support.SHOP)
    return (
        *(
            food_support.Business(kind, (east + 50.0 * number, north - 50.0 * number))
            for number, kind in enumerate(kinds)
        ),
        food_support.Business(food_support.EAT, None),
    )


def register_of(day: str, rows: int = 2, item: str = REGISTER) -> File:
    """A made-up register of a made-up authority, which states the day of its extract.

    It is shaped as a file of the food hygiene register is: a header that holds
    the day, and a row for each business. Every business has the one made-up
    name, and the file says that it is made up.
    """
    said = "<!-- Made up for a test. It describes no real place and no real business. -->"
    return File(
        item,
        "fsa-food-hygiene-ratings",
        Use.SCORING,
        f"made-up-{item}.xml",
        f"extract of {day}",
        day,
        register(header_of(day), before=said, rows=rows),
        states_its_own=True,
    )


def list_of(listed: Sequence[File]) -> str:
    """The list of a build, as fetch takes it. It names each file and holds no hash.

    Of a file that states its own edition it states none, and says where the
    file does.
    """
    written = ['schema_version = 1\nbuild = "made-up"\n']
    for file in listed:
        stated = [f'edition = "{file.edition}"', f'data_period = {{ as_at = "{file.period}" }}']
        in_the_file = [f"edition_from = {{ {IN_THE_HEADER}, period_too = true }}"]
        written.append(
            "\n".join(
                [
                    "[[file]]",
                    f'item = "{file.item}"',
                    f'source_id = "{file.source_id}"',
                    f'use = "{file.use}"',
                    'what = "Made up for a test"',
                    f'format = "{"xml" if file.states_its_own else "other"}"',
                    f'page = "{PAGE}"',
                    f'url = "{file.url}"',
                    "max_bytes = 10_000_000",
                    *(in_the_file if file.states_its_own else stated),
                    "",
                ]
            )
        )
    return "\n".join(written)


@contextmanager
def named_as_core_names_it(measure: ModuleType) -> Generator[None]:
    """For a while, a measure that a build leaves out says of itself what core says of it.

    A build leaves a measure out where its name is not core's. This stands for the day
    core and the measure say the same, so that a test can hold that nothing but the name
    keeps the measure out. No real build is made so.
    """
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(measure, "LABEL", FEATURES[measure.FEATURE].label)
        yield


@contextmanager
def held_back_for_a_while(feature: FeatureId, found: tuple[str, ...]) -> Generator[None]:
    """For a while, a check of the figures of one measure of a build holds it back.

    No measure is held back today. This stands for the day a check finds that the
    figures of one do not say what it is named for, so that the hold is seen to keep a
    measure out whatever core says of it. No real build is made so.
    """
    held = tuple(
        replace(measure, held_back=found) if measure.feature is feature else measure
        for measure in assemble.MEASURES
    )
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(assemble, "MEASURES", held)
        yield


@dataclass(frozen=True)
class Made:
    """A made-up build on disk: its store, its receipts and its list."""

    folder: Path
    # Where the build writes, where that is not beside its files: the files that are made
    # once are read by many tests, and each builds to a folder of its own.
    writes_to: Path | None = None

    @property
    def store(self) -> Path:
        return self.folder / "store"

    @property
    def receipts(self) -> Path:
        return self.folder / "receipts"

    @property
    def out(self) -> Path:
        return self.writes_to or self.folder / "out"

    @property
    def release(self) -> Path:
        return self.out / RELEASE

    @property
    def beside(self) -> Path:
        return self.out / f"{RELEASE}-build"

    def arguments(self, *more: str, out: Path | None = None) -> list[str]:
        (self.folder / "no-repository").mkdir(exist_ok=True)
        return [
            "preview",
            *("--release-id", RELEASE),
            *("--built-at", BUILT_AT),
            *("--out", str(out or self.out)),
            *("--list", str(self.folder / "made-up.toml")),
            *("--receipts", str(self.receipts)),
            *("--registry", str(REGISTRY)),
            *("--root", str(self.folder / "no-repository")),
            *("--commit", COMMIT),
            *more,
        ]

    def run(self, *more: str, out: Path | None = None) -> int:
        return assemble.main(self.arguments(*more, out=out), {FOLDER_VARIABLE: str(self.store)})

    def keep(self, file: File, receipt: bool = True) -> None:
        """Put a file in the store, with its receipt unless it is to have none."""
        given = self.folder / "given" / file.item / file.name
        given.parent.mkdir(parents=True, exist_ok=True)
        given.write_bytes(file.content)
        FolderStore(self.store).put(file.source_id, file.name, given)
        if receipt:
            kept = file.receipt()
            path = self.receipts / kept.source_id / f"{kept.file_id}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(kept.canonical())


def made(
    folder: Path,
    *,
    without_a_receipt: Sequence[str] = (),
    changed: Mapping[str, File] | None = None,
    unlisted: Sequence[File] = (),
) -> Made:
    """The made-up build in a folder: every file stored, receipted and listed.

    `without_a_receipt` names the files that are stored and listed and have no
    receipt. `changed` takes the place of a file. `unlisted` are files of
    another list: stored and receipted, and no part of this build.
    """
    every = files() | dict(changed or {})
    build = Made(folder)
    for item, file in every.items():
        build.keep(file, receipt=item not in without_a_receipt)
    for file in unlisted:
        build.keep(file)
    (folder / "made-up.toml").write_text(list_of(list(every.values())), encoding="utf-8")
    return build


@cache
def _files_made_once() -> Made:
    found = made(once.folder_for("made-once"))
    (found.folder / "no-repository").mkdir()
    once.made(found.folder)
    return found


def made_once(folder: Path) -> Made:
    """The made-up build as `made` makes it, for a test that gives it no file of its own.

    Its store, its receipts and its list are made once in each process, and no test
    writes to them: a build reads them and writes to none of them. What this build
    writes, it writes under `folder`. A test that changes a file of a build, that looks
    for the folder of its files in what a build prints, or that changes core for a
    while, makes its own with `made`: what is made once is made as core is.
    """
    folder.mkdir(parents=True, exist_ok=True)
    return replace(_files_made_once(), writes_to=folder / "out")


@cache
def built_once() -> Made:
    """The made-up build as `made` makes it, built once in each process and never changed.

    It is for a test that only reads a build, or that takes a copy of one. What the step
    printed is thrown away. A test that gives a build other files, or reads what a build
    prints, makes its own.
    """
    found = made_once(once.folder_for("built-once"))
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert found.run() == 0
    once.made(found.out)
    return found
