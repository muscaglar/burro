"""The sites and the ways into them, read from files laid out as the publisher's.

Every file here is made up: `green_support.py` says how. The elements and
their namespaces are the publisher's own, so a parser that reads these reads
the real files. What they hold is made up.
"""

import io
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest
from burro_pipeline.cells.shapes import outline_of
from burro_pipeline.derive import green_sites
from burro_pipeline.derive.green_sites import Greenspace, Tile, corner_of
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import held, registry
from .green_support import (
    BY_CAR,
    CANARY,
    GREAT,
    LONG_MEADOW,
    ON_FOOT,
    PARK,
    SITES,
    WRITTEN,
    MadeUpSite,
    MadeUpWay,
    at,
    box,
    document,
    file_ids,
    green_receipt,
    inputs_of,
    opened_of,
    tile,
    tiles,
)

TC, TB, TG, TH = (700_000, 400_000), (600_000, 400_000), (600_000, 300_000), (700_000, 300_000)


def read(folder: Path, held_in: bytes | None = None, letters: str = "tc") -> Tile:
    return green_sites.read(opened_of(folder, letters, tile(letters, held_in)))


def refused(folder: Path, held_in: bytes, letters: str = "tc", edition: str = "2026-04") -> str:
    """The refusal of a file, which names a rule and repeats nothing the file holds."""
    opened = opened_of(folder, letters, tile(letters, held_in), edition=edition)
    with pytest.raises(LockError) as stopped:
        green_sites.read(opened)
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return str(stopped.value)


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Tile:
    return read(tmp_path_factory.mktemp("town"))


@pytest.fixture(scope="module")
def four(tmp_path_factory: pytest.TempPathFactory) -> Greenspace:
    return green_sites.build(inputs_of(tmp_path_factory.mktemp("four")))


# The square a file is named for


@pytest.mark.parametrize(
    ("letters", "corner"),
    [
        ("SV", (0, 0)),
        ("TQ", (500_000, 100_000)),
        ("TL", (500_000, 200_000)),
        ("TC", TC),
        ("TB", TB),
        ("TG", TG),
        ("TH", TH),
        ("NN", (200_000, 700_000)),
        ("HP", (400_000, 1_200_000)),
    ],
)
def test_two_letters_of_the_grid_stand_for_a_square(letters: str, corner: tuple[int, int]):
    assert corner_of(letters) == corner


@pytest.mark.parametrize("letters", ["", "T", "TQQ", "TI", "tq", "T1"])
def test_letters_that_name_no_square_are_refused(letters: str):
    with pytest.raises(ValueError, match="two letters of the grid"):
        corner_of(letters)


def test_a_file_is_known_by_the_publishers_name_for_a_square():
    assert green_sites.is_a_tile("opgrsp_gml3_tq.zip")
    assert not green_sites.is_a_tile("opgrsp_gpkg_gb.zip")
    assert not green_sites.is_a_tile("opgrsp_gml3_tq.zip.part")


# The parser


def test_every_site_and_every_way_in_is_read(town: Tile):
    assert (town.letters, town.corner, town.year) == ("TC", TC, 2026)
    assert sorted(town.sites) == sorted(site.site_id for site in SITES)
    assert {site.kind for site in town.sites.values()} == {PARK, "Golf Course"}
    assert [way.site_id for way in town.ways_in] == [
        "idLONGMEADOW",
        "idLONGMEADOW",
        "idLINKS",
        "idPOCKET",
        "idGREAT",
    ]
    assert [way.on_foot for way in town.ways_in] == [True, False, True, True, True]


def test_a_site_is_as_large_as_its_outline_encloses(town: Tile):
    sizes = {site_id: site.hectares for site_id, site in town.sites.items()}
    assert sizes == {
        "idLONGMEADOW": 2.0,
        "idWALLEDPLOT": 0.25,
        "idPOCKET": 0.04,
        "idLINKS": 2.0,
        "idGREAT": 20.0,
    }


def test_a_hole_in_a_site_is_no_part_of_it_and_two_pieces_are_one_site(tmp_path: Path):
    holed = MadeUpSite("idHOLED", PARK, ((box(0, 0, 100, 100), box(40, 40, 20, 20)),))
    split = MadeUpSite("idSPLIT", PARK, ((box(200, 0, 100, 100),), (box(400, 0, 50, 100),)))
    found = read(tmp_path, document([holed, split], []))
    assert found.sites["idHOLED"].hectares == 0.96
    assert found.sites["idSPLIT"].hectares == 1.5


def test_no_name_of_a_site_is_kept(town: Tile):
    assert CANARY.encode() in document()
    assert CANARY not in repr(town)


def test_an_element_that_is_not_read_changes_nothing(tmp_path: Path, town: Tile):
    more = (
        f"<os:featureMember><ogsp:GreenspaceSite gml:id='idMORE'><ogsp:function>{PARK}"
        f"</ogsp:function><ogsp:madeUp>{CANARY}</ogsp:madeUp><ogsp:geometry><gml:MultiSurface "
        "srsName='urn:ogc:def:crs:EPSG::27700'><gml:surfaceMember><gml:Surface><gml:patches>"
        "<gml:PolygonPatch><gml:exterior><gml:LinearRing><gml:posList>700000 400000 700010 "
        "400000 700010 400010 700000 400000</gml:posList></gml:LinearRing></gml:exterior>"
        "</gml:PolygonPatch></gml:patches></gml:Surface></gml:surfaceMember></gml:MultiSurface>"
        "</ogsp:geometry></ogsp:GreenspaceSite></os:featureMember>"
    )
    found = read(tmp_path, document(more=more))
    assert found.sites["idMORE"].hectares == 0.005
    assert {key: site.drawn for key, site in found.sites.items() if key != "idMORE"} == {
        key: site.drawn for key, site in town.sites.items()
    }


@pytest.mark.parametrize(
    ("sites", "ways_in", "element"),
    [
        ([replace(LONG_MEADOW, kind=None)], [], "function"),
        ([replace(LONG_MEADOW, kind="")], [], "function"),
        ([replace(LONG_MEADOW, pieces=())], [], "posList"),
        ([LONG_MEADOW], [MadeUpWay("idLONGMEADOW", None, at(50, 150))], "accessType"),
        ([LONG_MEADOW], [MadeUpWay(None, ON_FOOT, at(50, 150))], "refToGreenspaceSite"),
        ([LONG_MEADOW], [MadeUpWay("idLONGMEADOW", ON_FOOT, None)], "pos"),
    ],
)
def test_a_file_without_an_element_that_is_read_is_refused_and_the_element_is_named(
    tmp_path: Path, sites: list[MadeUpSite], ways_in: list[MadeUpWay], element: str
):
    assert f"the element {element} is missing" in refused(tmp_path, document(sites, ways_in))


@pytest.mark.parametrize(
    ("sites", "ways_in", "words"),
    [
        ([replace(LONG_MEADOW, kind=CANARY)], [], "a kind that is not one of the ten"),
        ([replace(LONG_MEADOW, kind="Common")], [], "a kind that is not one of the ten"),
        ([LONG_MEADOW], [MadeUpWay("idLONGMEADOW", CANARY, at(50, 150))], "somebody the step"),
        ([replace(LONG_MEADOW, grid="urn:ogc:def:crs:EPSG::4326")], [], "National Grid"),
        ([LONG_MEADOW], [MadeUpWay("idLONGMEADOW", ON_FOOT, at(1, 1), grid=CANARY)], "National"),
        ([LONG_MEADOW, LONG_MEADOW], [], "a site is there twice"),
        ([replace(LONG_MEADOW, site_id="")], [], "a site has no id"),
        ([LONG_MEADOW], [MadeUpWay("idNOSUCH", ON_FOOT, at(50, 150))], "to no site of the file"),
        ([], [], "it holds no site"),
        # A way in on the square to the west, and a site that does not touch the square.
        ([LONG_MEADOW], [MadeUpWay("idLONGMEADOW", ON_FOOT, at(-1, 150))], "a way in is not on"),
        ([replace(LONG_MEADOW, pieces=((box(-500, 0, 100, 100),),))], [], "a site is not on"),
        # A ring that crosses itself, and a piece that lies over another.
        (
            [replace(LONG_MEADOW, pieces=((((0, 0), (9, 9), (9, 0), (0, 9), (0, 0)),),))],
            [],
            "a site is not a shape",
        ),
        (
            [replace(LONG_MEADOW, pieces=((box(0, 0, 100, 100),), (box(50, 50, 100, 100),)))],
            [],
            "a site is not a shape",
        ),
        # A ring that does not end where it began, and one of too few points.
        ([replace(LONG_MEADOW, pieces=((box(0, 0, 9, 9)[:4],),))], [], "is not closed"),
        ([replace(LONG_MEADOW, pieces=((box(0, 0, 9, 9)[:3],),))], [], "not a list of points"),
    ],
)
def test_a_file_that_is_not_as_described_is_refused(
    tmp_path: Path, sites: list[MadeUpSite], ways_in: list[MadeUpWay], words: str
):
    assert words in refused(tmp_path, document(sites, ways_in))


@pytest.mark.parametrize(
    "points", [CANARY, "1 2 3", "1 2 3 4 5 6 7 nan", "1e3 2 3 4 5 6 1e3 2", ""]
)
def test_an_outline_that_is_no_list_of_points_is_refused(tmp_path: Path, points: str):
    written = document().replace(b"700050.00 400100.00 700250.00 400100.00", points.encode(), 1)
    assert written != document()
    assert "not a list of points" in refused(tmp_path, written)


def test_an_outline_with_a_hole_before_its_ring_is_refused(tmp_path: Path):
    written = document().replace(b"gml:exterior", b"gml:interior")
    assert "not laid out in pieces" in refused(tmp_path, written)


@pytest.mark.parametrize(
    ("said", "edition", "words"),
    [
        (None, "2026-04", "does not say whose it is"),
        (CANARY, "2026-04", "does not say whose it is"),
        ("Ordnance Survey Crown Copyright 2025", "2026-04", "not the year of its receipt"),
        ("Ordnance Survey Crown Copyright 2026", "2027-04", "not the year of its receipt"),
    ],
)
def test_a_file_of_another_year_than_its_receipt_says_is_refused(
    tmp_path: Path, said: str | None, edition: str, words: str
):
    assert words in refused(tmp_path, document(said=said), edition=edition)


@pytest.mark.parametrize(
    "before",
    [
        "<!DOCTYPE made-up>",
        f'<!DOCTYPE made-up [<!ENTITY more "{CANARY}">]>',
        '<!DOCTYPE made-up SYSTEM "file:///made-up">',
    ],
)
def test_a_document_that_declares_a_type_or_an_entity_is_not_read(tmp_path: Path, before: str):
    assert "could not be read as GML" in refused(tmp_path, document(before=before))


def test_a_document_that_is_not_well_formed_or_is_something_else_is_refused(tmp_path: Path):
    assert "could not be read as GML" in refused(tmp_path / "cut", document()[:-40])
    other = f"<?xml version='1.0'?><made-up>{CANARY}</made-up>".encode()
    assert "not a collection of features" in refused(tmp_path / "other", other)
    third = document(more="<os:featureMember><ogsp:MadeUp gml:id='idX'/></os:featureMember>")
    assert "neither a site nor a way in" in refused(tmp_path / "third", third)


def test_a_file_that_is_not_named_for_its_square_is_refused(tmp_path: Path):
    # The zip is named for one square and the document inside it for another.
    wrong = tile("tc", member="OS Open Greenspace (GML) TQ/data/OSOpenGreenspace_TQ.gml")
    with pytest.raises(LockError) as stopped:
        green_sites.read(opened_of(tmp_path, "tc", wrong))
    assert stopped.value.rule == "input_is_as_described"
    # `TI` is no square of the grid.
    with pytest.raises(LockError, match="not named for a square"):
        green_sites.read(opened_of(tmp_path / "no-square", "ti", tile("ti")))


def test_made_up_sites_are_the_same_file_whenever_a_test_makes_them():
    """A zip holds the time its members were written. A file is known by the hash of its bytes."""
    with zipfile.ZipFile(io.BytesIO(tile("tc"))) as archive:
        assert {member.date_time for member in archive.infolist()} == {WRITTEN}
    assert file_ids(tiles()) == file_ids(tiles())


# Several files


def test_the_files_of_every_square_are_read_and_each_names_its_own(four: Greenspace):
    ids = file_ids(tiles())
    assert four.file_of == {TC: ids["tc"], TB: ids["tb"], TG: ids["tg"], TH: ids["th"]}
    assert [receipt.file_id for receipt in four.files] == sorted(ids.values())
    assert len(four.sites) == len(SITES) + 3
    assert (four.as_at, four.in_two_files) == ("2026-04", 0)


def test_a_site_that_is_in_two_files_is_kept_once(tmp_path: Path):
    """A site across the line between two squares is in both files, drawn the same way."""
    across = MadeUpSite("idACROSS", PARK, ((box(50, -50, 100, 100),),))
    north = tile("tc", document([across, GREAT], [MadeUpWay("idACROSS", ON_FOOT, at(100, 50))]))
    south = tile("th", document([across], [MadeUpWay("idACROSS", BY_CAR, at(100, -50))]))
    found = green_sites.build(inputs_of(tmp_path, {"tc": north, "th": south}))
    assert sorted(found.sites) == ["idACROSS", "idGREAT"]
    assert (found.in_two_files, len(found.ways_in)) == (1, 2)


def test_two_files_that_draw_one_site_differently_are_refused(tmp_path: Path):
    one = MadeUpSite("idACROSS", PARK, ((box(50, -50, 100, 100),),))
    other = replace(one, pieces=((box(50, -50, 100, 101),),))
    squares = {"tc": tile("tc", document([one], [])), "th": tile("th", document([other], []))}
    with pytest.raises(LockError, match="two files draw one site differently") as stopped:
        green_sites.build(inputs_of(tmp_path, squares))
    assert stopped.value.rule == "input_is_as_described"


def test_files_of_two_editions_are_told_apart_by_the_edition_asked_for(tmp_path: Path):
    inputs = inputs_of(tmp_path, {"tc": tile("tc")})
    later = tile("tc", document(said="Ordnance Survey Crown Copyright 2027"))
    receipt = green_receipt("tc", later, edition="2027-04")
    path = tmp_path / "later" / receipt.publisher_file
    path.parent.mkdir()
    path.write_bytes(later)
    inputs.store.put(receipt.source_id, receipt.publisher_file, path)
    both = replace(inputs, receipts=[*inputs.receipts, receipt])
    with pytest.raises(LockError) as stopped:
        green_sites.build(both)
    assert stopped.value.rule == "input_has_one_receipt"
    assert green_sites.build(both, edition="2026-04").as_at == "2026-04"
    assert green_sites.build(both, edition="2027-04").as_at == "2027-04"


def test_a_build_with_no_file_of_the_source_is_refused(tmp_path: Path):
    with pytest.raises(LockError) as stopped:
        green_sites.build(inputs_of(tmp_path, {}))
    assert stopped.value.rule == "input_has_one_receipt"


# What the files cover


def test_a_point_is_as_far_from_land_no_file_was_read_for_as_from_the_nearest_such_square(
    tmp_path: Path, four: Greenspace
):
    alone = green_sites.build(inputs_of(tmp_path, {"tc": tile("tc")}))
    # The town stands hard against the west and the south sides of its square.
    assert alone.beyond(at(50, 150)) == 50.0
    assert alone.beyond(at(250, 150)) == 150.0
    assert alone.beyond(at(30, 40)) == 30.0
    assert alone.beyond(at(-1, 150)) == 0.0
    # With the three squares round the corner read too, the nearest is a square away.
    assert four.beyond(at(50, 150)) == 99_850.0
    assert four.beyond(at(-50, -50)) == 99_950.0


def test_a_distance_rests_on_the_files_of_the_squares_within_it(four: Greenspace):
    ids = file_ids(tiles())
    assert four.files_within(at(50, 150), 0.0) == (ids["tc"],)
    assert four.files_within(at(50, 150), 50.0) == tuple(sorted([ids["tc"], ids["tb"]]))
    assert four.files_within(at(50, 50), 60.0) == tuple(sorted([ids["tc"], ids["tb"], ids["th"]]))
    assert four.files_within(at(50, 50), 80.0) == tuple(sorted(ids.values()))


def test_an_outline_rests_on_the_files_of_the_squares_it_lies_on(tmp_path: Path, four: Greenspace):
    ids = file_ids(tiles())
    inside = outline_of([[box(0, 100, 200, 100)]])
    across = outline_of([[box(400, 0, 200, 100)], [box(500, -200, 100, 100)]])
    assert four.files_under(inside) == (ids["tc"],)
    assert four.files_under(across) == tuple(sorted([ids["tc"], ids["th"]]))
    alone = green_sites.build(inputs_of(tmp_path, {"tc": tile("tc")}))
    assert alone.files_under(inside) == (ids["tc"],)
    assert alone.files_under(across) is None


# The gate and the store


def without_scoring() -> Registry:
    """The repository's registry, with the sites no longer registered for scoring."""
    sources = [
        source.model_copy(update={"uses": (Use.DISPLAY,)})
        if source.id == green_sites.SOURCE
        else source
        for source in registry()
    ]
    return Registry(tuple(sources))


def test_the_gate_is_asked_before_a_file_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, given=without_scoring())
    with pytest.raises(LockError) as stopped:
        green_sites.build(inputs)
    assert stopped.value.rule == "gate_refuses"
    assert inputs.opened == ()
    assert not (tmp_path / "work").exists()


def test_the_source_is_registered_for_scoring():
    assert Use.SCORING in registry().get(green_sites.SOURCE).uses


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    green_sites.build(inputs)
    assert held(tmp_path / "store") == before
