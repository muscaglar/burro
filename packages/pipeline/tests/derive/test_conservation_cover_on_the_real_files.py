"""Conservation cover, worked out from the files their publishers gave.

Every other test of the measure runs on made-up records. These read the real
file, and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts of the file, the count of areas with a figure, and three
figures: London's lowest, middle and highest. None is said of a named area or
of a named authority. Each was worked out on 2026-09-24, by a program. No
person has held any of them against an authority's own list of its
conservation areas.

© Historic England 2026. Contains Ordnance Survey data © Crown copyright and
database right 2026. The Historic England GIS Data contained in this material
was obtained on 2026-09-24. The most publicly available up to date Historic
England GIS Data can be obtained from HistoricEngland.org.uk. Source: Office
for National Statistics licensed under the Open Government Licence v.3.0.

Nothing is written to the store. A file is copied out of it to be read.
"""

import statistics
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

import pytest
from burro_pipeline.cells import land, spine
from burro_pipeline.cells.land import Land
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import conservation_cover
from burro_pipeline.derive.conservation_cover import Counted, Cover
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.planning_data import AUTHORITATIVE, SOME
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import registry
from .real_files import SKIPPED, STORE, real_inputs

pytestmark = SKIPPED
# The file of conservation areas, by the id of its receipt, and the edition it was kept under.
AREAS, EDITION = "f-450c57d438cb", "retrieved 2026-09-24"
# The boundaries of LSOAs, the lookup and the table of homes.
BOUNDARIES, LOOKUP, HOMES = "f-9f549e33f46b", "f-49321b95f212", "f-af7b512615ea"


def listing() -> dict[str, tuple[int, int]]:
    """Every file of the store, with its size and when it was last written."""
    return {
        path.relative_to(STORE).as_posix(): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in sorted(Path(STORE).rglob("*"))
        if path.is_file()
    }


@pytest.fixture(scope="module")
def before() -> dict[str, tuple[int, int]]:
    return listing()


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory, before: dict[str, tuple[int, int]]) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def measured(real: Inputs, found: Spine) -> Land:
    return land.build(real, found)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine, measured: Land) -> Cover:
    return conservation_cover.build(real, found, measured, edition=EDITION)


# The file


def test_every_record_of_the_file_is_counted_once(made: Cover):
    assert made.counted == Counted(
        in_the_file=9_659,
        in_the_box=1_340,
        nowhere=0,
        ended=0,
        points=0,
        no_land=0,
        mended=1,
        outside=194,
        twice=53,
        kept=1_093,
    )


def test_london_holds_about_a_thousand_conservation_areas_each_counted_once(made: Cover):
    assert sum(sum(one.areas.values()) for one in made.authorities.values()) == 1_093
    assert sum(one.twice for one in made.authorities.values()) == 53


# Coverage, which the licence registry asks to be checked for all 33 authorities


def test_the_file_holds_a_conservation_area_in_every_one_of_the_33_authorities(made: Cover):
    assert len(made.authorities) == 33
    assert all(one.covered for one in made.authorities.values())
    counts = sorted(sum(one.areas.values()) for one in made.authorities.values())
    assert (counts[0], statistics.median(counts), counts[-1]) == (4, 29, 86)


def wholly_of_one_quality(counts: list[Mapping[tuple[str, str], int]]) -> dict[str, int]:
    """How many authorities rest on records of one quality alone, for each quality."""
    wholly: dict[str, int] = {AUTHORITATIVE: 0, SOME: 0}
    for areas in counts:
        qualities = {quality for (_, quality), count in areas.items() if count}
        if len(qualities) == 1:
            wholly[next(iter(qualities))] += 1
    return wholly


def test_thirteen_authorities_are_given_no_record_that_is_marked_authoritative(made: Cover):
    """The dataset page says some of its data is not from an authoritative source.

    The file marks each record `authoritative` or `some`, and does not say
    what either means. A record marked `some` may be older than the
    authority's list, or miss an area. The count of each authority is for a
    person to hold against that list.
    """
    by_quality = Counter[str]()
    for one in made.authorities.values():
        for (_, quality), count in one.areas.items():
            by_quality[quality] += count
    assert dict(by_quality) == {AUTHORITATIVE: 646, SOME: 447}
    given = wholly_of_one_quality([one.areas for one in made.authorities.values()])
    assert given == {AUTHORITATIVE: 13, SOME: 13}


def test_fourteen_authorities_hold_most_of_no_area_that_is_marked_authoritative(made: Cover):
    """One authority is given one `authoritative` record, of which it holds under 1 in 100.

    That record is a conservation area of a place outside London that crosses
    London's edge. Every area the authority holds most of is marked `some`. So
    14 authorities rest wholly on `some`, and not 13, and the fourteenth is
    among those a person checks first.
    """
    mostly = wholly_of_one_quality([one.mostly for one in made.authorities.values()])
    assert mostly == {AUTHORITATIVE: 14, SOME: 14}


def test_an_area_that_lies_mostly_over_the_edge_or_over_water_covers_no_authority(made: Cover):
    """Of the 1,093 areas, 19 are held under half by the authority each is given to.

    Some lie mostly outside London, and some take in the tidal river, which is
    no part of the land. None is what makes its authority covered: the fewest
    areas an authority holds most of is 4.
    """
    given = sum(sum(one.areas.values()) for one in made.authorities.values())
    mostly = sum(sum(one.mostly.values()) for one in made.authorities.values())
    assert (given, mostly, given - mostly) == (1_093, 1_074, 19)
    assert min(sum(one.mostly.values()) for one in made.authorities.values()) == 4
    for one in made.authorities.values():
        assert all(one.mostly[key] <= one.areas[key] for key in one.mostly)


def test_the_provider_of_every_area_is_kept(made: Cover):
    providers = {provider for one in made.authorities.values() for provider, _ in one.areas}
    assert len(providers) == 37
    # The ministry's own number. The file holds two areas of London under it.
    assert sum(one.areas.get(("1", SOME), 0) for one in made.authorities.values()) == 2


# The figures


def test_every_area_has_a_figure_and_is_wholly_covered(made: Cover):
    assert len(made.worked) == 1_002
    assert Counter(one.state for one in made.worked.values()) == {State.PRESENT: 1_002}
    assert {one.weight_covered for one in made.worked.values()} == {1.0}
    assert {one.flags for one in made.worked.values()} == {()}


def test_the_lowest_the_middle_and_the_highest_figure_are_what_was_worked_out(made: Cover):
    values = sorted(one.value for one in made.worked.values() if one.value is not None)
    assert (values[0], statistics.median(values), values[-1]) == (0.0, 7.75, 100.0)


def test_about_a_quarter_of_the_areas_are_at_nought(made: Cover):
    """Each is in an authority the file covers. No conservation area touches it."""
    assert sum(one.value == 0 for one in made.worked.values()) == 262


def test_the_conservation_land_of_london_is_what_was_measured(made: Cover, measured: Land):
    assert len(made.inside) == 4_994
    assert conservation_cover.hectares_in(made.inside) == 24_216.2146
    assert all(made.inside[lsoa] <= measured.of_lsoa[lsoa] + 0.0001 for lsoa in made.inside)


# The evidence


def test_every_figure_rests_on_the_four_files_and_the_method_of_the_design(made: Cover):
    assert len(made.rows) == 1_002
    assert {row.inputs for row in made.rows} == {tuple(sorted([AREAS, BOUNDARIES, LOOKUP, HOMES]))}
    assert {row.derivation_id for row in made.rows} == {"lsoa_ratio_by_homes@1"}
    # From the day of the census, which the weights are of, to the day of the file.
    span = Period(start="2021-03-21", end="2026-09-24")
    assert all(row.data_period == span for row in made.rows)
    assert {row.retrieved_on for row in made.rows} == {"2026-09-24"}
    assert all(row.value == made.worked[row.area_id].value for row in made.rows)
    assert Evidence.of("lon-2026-10-09-01", made.files, conservation_cover.METHODS, made.rows)


def test_the_row_of_the_catalogue_is_cores_and_names_every_source(made: Cover):
    assert says_what_core_says(made.metric)
    assert made.metric.vintage == "2026-09-24"
    assert made.metric.source_ids == (
        "mhclg-planning-data-conservation-areas",
        "ons-census-2021-housing-tables",
        "ons-lsoa-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
    )
    for source_id in made.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_the_files_are_read_from_copies_and_the_store_is_as_it_was(
    real: Inputs, made: Cover, before: dict[str, tuple[int, int]]
):
    copies = sorted(path for path in real.work.rglob("*") if path.is_file())
    assert sorted(path.relative_to(real.work).parts[0] for path in copies) == sorted(
        [AREAS, BOUNDARIES, LOOKUP, HOMES]
    )
    assert Path(STORE).resolve() not in real.work.resolve().parents
    # Other steps may add a file to the store while this runs. None that was there has changed.
    after = listing()
    assert {name: after.get(name) for name in before} == before
