"""Homes in the higher council tax bands, from a made-up table laid out as the publisher's.

Every figure here is made up. The town is the made-up town of the tests of
cells: three areas, each an MSOA of two LSOAs. The table of homes by band has
the publisher's own columns, its mark at the start, its quotes round every
cell, its row for each larger area, and its ways of writing a cell.

The homes of an area are read from the row of the MSOA, which is the area's
own. The rows of its LSOAs are what that row is held to.

    area               row           E     F     G     H     all     the share
    Quillhaven 001     E02999001     30    20    10    -     200     60 of 200 is 30.0
                         E01999001   20    10    10    -     120
                         E01999002   10    10    0     0      80
    Quillhaven 002     E02999002     0     0     0     0      40     0.0
                         E01999003   0     0     0     0      40
                         E01999004   0     0     0     0       0
    Tallowgate 001     E02999003     -     -     0     0     500     no figure
                         E01999005   -     0     0     0     250
                         E01999006   0     -     0     0     250
"""

import csv
import io
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, TAGS
from burro_core.ids import Describes, FeatureId, FeatureKind, NativeResolution, Polarity
from burro_pipeline.cells import spine
from burro_pipeline.derive import homes_density, homes_higher_bands, measures
from burro_pipeline.derive.homes_higher_bands import Banded
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import Flag, State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, contents, inputs_of, receipt_of, registry, zip_of
from .test_homes_density import COLUMNS, LARGER, NAME, NOTES, TABLE

ONE, TWO, THREE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
LOOKUP = "ons-oa21-lsoa21-msoa21-lad22-lookup"
# The counts of bands E, F, G and H, and of all homes, of each row that is read.
Row = tuple[str, str, str, str, str]
OF_LSOAS: Mapping[str, Row] = {
    "E01999001": ("20", "10", "10", "-", "120"),
    "E01999002": ("10", "10", "0", "0", "80"),
    "E01999003": ("0", "0", "0", "0", "40"),
    "E01999004": ("0", "0", "0", "0", "0"),
    "E01999005": ("-", "0", "0", "0", "250"),
    "E01999006": ("0", "-", "0", "0", "250"),
    # Outside London, and in Wales. Neither is part of any area.
    "E01999901": ("100", "100", "100", "100", "700"),
    "W01999001": ("10", "10", "10", "10", "90"),
}
OF_MSOAS: Mapping[str, Row] = {
    "E02999001": ("30", "20", "10", "-", "200"),
    "E02999002": ("0", "0", "0", "0", "40"),
    "E02999003": ("-", "-", "0", "0", "500"),
    "E02999901": ("100", "100", "100", "100", "700"),
}
# A count found in no row that is read. It stands in every band that is not.
NEVER_READ = "9990"
ROUNDED = (Flag.ROUNDED_IN_SOURCE,)
WITHHELD = (Flag.ROUNDED_IN_SOURCE, Flag.SUPPRESSED_IN_SOURCE)


def table_of(
    of_lsoas: Mapping[str, Row] = OF_LSOAS,
    of_msoas: Mapping[str, Row] = OF_MSOAS,
    columns: Sequence[str] = COLUMNS,
) -> bytes:
    """The table of homes by band, as the publisher writes it."""
    text = io.StringIO(newline="")
    table = csv.DictWriter(
        text, columns, extrasaction="ignore", lineterminator="\n", quoting=csv.QUOTE_ALL
    )
    table.writeheader()
    whole: Row = (NEVER_READ, NEVER_READ, NEVER_READ, NEVER_READ, NEVER_READ)
    rows = [*((kind, code, whole) for kind, code in LARGER)]
    rows += [("MSOA", code, held) for code, held in of_msoas.items()]
    rows += [("LSOA", code, held) for code, held in of_lsoas.items()]
    for kind, code, (e, f, g, h, homes) in rows:
        table.writerow(
            {"geography": kind, "ba_code": "n/a", "ecode": code, "area_name": CANARY}
            # The lower four bands are never read.
            | dict.fromkeys(("band_a", "band_b", "band_c", "band_d"), NEVER_READ)
            | {"band_e": e, "band_f": f, "band_g": g, "band_h": h}
            | {"band_i": "10" if code.startswith("W") else "..", "all_properties": homes}
        )
    return b"\xef\xbb\xbf" + text.getvalue().encode()


def inputs_with(folder: Path, table: bytes | None = None, as_at: str = "2025-03-31") -> Inputs:
    """The made-up build of the tests of cells, and the table of homes beside it."""
    given = inputs_of(folder, contents())
    content = zip_of({TABLE: table_of() if table is None else table, NOTES: CANARY})
    path = folder / "given" / NAME
    path.write_bytes(content)
    given.store.put(homes_higher_bands.SOURCE, NAME, path)
    receipt = receipt_of(homes_higher_bands.SOURCE, Use.SCORING, NAME, content, "2025").model_copy(
        update={"data_period": Period(as_at=as_at)}
    )
    return Inputs(given.registry, [*given.receipts, receipt], given.store, given.work)


def built(
    folder: Path,
    of_lsoas: Mapping[str, Row] = OF_LSOAS,
    of_msoas: Mapping[str, Row] = OF_MSOAS,
) -> Banded:
    inputs = inputs_with(folder, table_of(of_lsoas, of_msoas))
    return homes_higher_bands.build(inputs, spine.build(inputs))


def refused(folder: Path, table: bytes, as_at: str = "2025-03-31") -> LockError:
    """The refusal of a table, which repeats nothing the table holds."""
    inputs = inputs_with(folder, table, as_at)
    with pytest.raises(LockError) as stopped:
        homes_higher_bands.build(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value) and NEVER_READ not in str(stopped.value)
    return stopped.value


# What the measure is


def test_it_is_a_figure_of_the_homes_of_a_place_and_never_of_who_lives_in_them():
    """It is a reading of a word for a smart area that counts homes and not people."""
    feature = FEATURES[FeatureId.HOMES_HIGHER_BANDS]
    assert (feature.label, feature.short_label) == (
        "Homes in council tax bands E to H as a share of homes",
        "Homes in the higher council tax bands",
    )
    assert (feature.unit, feature.polarity) == ("%", Polarity.EITHER)
    assert (feature.kind, feature.describes) == (FeatureKind.TASTE, Describes.BUILDINGS)
    assert feature.native_resolution is NativeResolution.MSOA
    # No vibe rests on it, and no likeness is counted on it.
    assert feature.in_likeness is False
    in_a_recipe = {term.feature_id for tag in TAGS.values() for term in tag.terms}
    assert FeatureId.HOMES_HIGHER_BANDS not in in_a_recipe
    for line in (feature.label, feature.short_label, *homes_higher_bands.CANNOT_SEE):
        said = line.lower()
        assert "income" not in said and "wealth" not in said and "rich" not in said


def test_the_registry_allows_the_table_and_no_word_of_the_measure_says_a_price():
    """The licence registry asks that a band is never used as an estimate of a price."""
    entry = registry().require(homes_higher_bands.SOURCE, Use.SCORING)
    assert "Do not use council tax band as a price estimate" in " ".join(entry.conditions)
    feature = FEATURES[FeatureId.HOMES_HIGHER_BANDS]
    for line in (feature.label, feature.short_label, feature.higher, feature.lower):
        assert "price" not in line.lower() and "£" not in line and "dear" not in line.lower()
    assert "is no estimate of what a home sells for today" in homes_higher_bands.DEFINITION
    assert "1991" in homes_higher_bands.CANNOT_SEE[0]


def test_it_reads_the_table_homes_per_hectare_reads_and_the_higher_four_bands_alone():
    assert homes_higher_bands.SOURCE == homes_density.SOURCE
    assert homes_higher_bands.is_the_table is homes_density.is_the_table
    assert homes_higher_bands.HIGHER == ("band_e", "band_f", "band_g", "band_h")
    assert set(homes_higher_bands.COLUMNS) == {
        "geography",
        "ecode",
        *homes_higher_bands.HIGHER,
        "all_properties",
    }


def test_it_is_on_the_list_of_a_build_and_says_what_core_says(tmp_path: Path):
    listed = {measure.feature: measure for measure in measures.MEASURES}
    measure = listed[FeatureId.HOMES_HIGHER_BANDS]
    assert not measure.waits_on and not measure.held_back
    assert measure.cannot_see == homes_higher_bands.CANNOT_SEE
    found = built(tmp_path)
    assert says_what_core_says(found.metric)
    assert found.metric.rankable is True


# The figure


def test_the_share_is_the_homes_of_the_four_bands_over_all_the_homes_of_the_area(tmp_path: Path):
    found = built(tmp_path).worked
    assert found == {
        # 30 and 20 and 10 of 200. The dash of the highest band adds nothing, and marks it.
        ONE: Worked(30.0, 1, 1, 1.0, State.PRESENT, WITHHELD),
        # No home in a higher band: the figure is nought, and is a figure.
        TWO: Worked(0.0, 1, 1, 1.0, State.PRESENT, ROUNDED),
        # Every band is a dash or a nought, and one is a dash: it is not nought, and the
        # table does not say what it is.
        THREE: Worked(None, 0, 1, 0.0, State.SUPPRESSED, WITHHELD),
    }


def test_the_figure_is_read_from_the_areas_own_row_and_not_added_up_from_its_lsoas(
    tmp_path: Path,
):
    """The LSOAs of the first area add up to 60 homes in the bands of 200, as its row does.

    With one LSOA read as 30 in band E they add up to 70, which is 35 in 100.
    The row still reads 30.
    """
    more = {**OF_LSOAS, "E01999001": ("30", "10", "10", "-", "120")}
    assert built(tmp_path, more).worked[ONE].value == 30.0


def test_a_share_is_given_to_one_decimal_place_with_a_half_taken_upward(tmp_path: Path):
    # 10 of 80 is 12.5, and 10 of 160 is 6.25, which is given as 6.3.
    rows = {**OF_MSOAS, "E02999001": ("10", "0", "0", "0", "160")}
    parts = {
        **OF_LSOAS,
        "E01999001": ("10", "0", "0", "0", "80"),
        "E01999002": ("0", "0", "0", "0", "80"),
    }
    assert built(tmp_path, parts, rows).worked[ONE].value == 6.3


def test_counts_that_come_to_more_than_the_whole_within_rounding_read_as_the_whole(
    tmp_path: Path,
):
    """Each count is rounded by itself, so four bands of an area can come to more than it."""
    rows = {**OF_MSOAS, "E02999002": ("20", "10", "10", "10", "40")}
    parts = {
        **OF_LSOAS,
        "E01999003": ("20", "10", "10", "10", "40"),
    }
    found = built(tmp_path, parts, rows)
    assert found.worked[TWO].value == 100.0
    assert found.at_the_whole == frozenset({TWO})


def test_counts_that_come_to_far_more_than_the_whole_stop_the_build(tmp_path: Path):
    rows = {**OF_MSOAS, "E02999002": ("40", "40", "40", "40", "40")}
    parts = {**OF_LSOAS, "E01999003": ("40", "40", "40", "40", "40")}
    said = refused(tmp_path, table_of(parts, rows))
    assert "a share is more than the whole" in str(said)


def test_an_area_with_no_count_of_its_homes_has_no_figure(tmp_path: Path):
    rows = {**OF_MSOAS, "E02999002": ("0", "0", "0", "0", "-")}
    parts = {**OF_LSOAS, "E01999003": ("0", "0", "0", "0", "-")}
    found = built(tmp_path, parts, rows).worked[TWO]
    assert (found.value, found.state) == (None, State.SUPPRESSED)


# The table


def test_a_row_that_its_lsoas_do_not_allow_stops_the_build(tmp_path: Path):
    """The reading of a dash is held to the table's own rows."""
    rows = {**OF_MSOAS, "E02999002": ("0", "0", "0", "10", "40")}
    said = refused(tmp_path, table_of(of_msoas=rows))
    assert "an area holds a count and no part of it does" in str(said)


def test_a_column_that_is_missing_is_named_by_the_name_the_step_asked_for(tmp_path: Path):
    without = [name for name in COLUMNS if name != "band_g"]
    said = refused(tmp_path, table_of(columns=without))
    assert "the column band_g is missing" in str(said)


@pytest.mark.parametrize("cell", ["15", "ten", "", "1e2", "-10"])
def test_a_count_that_is_no_count_stops_the_build(tmp_path: Path, cell: str):
    rows = {**OF_MSOAS, "E02999001": (cell, "20", "10", "-", "200")}
    refused(tmp_path, table_of(of_msoas=rows))


def test_a_table_of_another_day_than_its_receipt_stops_the_build(tmp_path: Path):
    said = refused(tmp_path, table_of(), as_at="2024-03-31")
    assert "the table is not of the day its receipt gives" in str(said)


def test_an_area_with_no_row_stops_the_build(tmp_path: Path):
    without = {code: row for code, row in OF_MSOAS.items() if code != "E02999003"}
    said = refused(tmp_path, table_of(of_msoas=without))
    assert "an MSOA of the census of 2021 has no row" in str(said)


# The evidence


def test_every_figure_rests_on_the_table_and_the_lookup_and_holds_its_value(tmp_path: Path):
    found = built(tmp_path)
    assert sorted(receipt.source_id for receipt in found.files) == sorted(
        [LOOKUP, homes_higher_bands.SOURCE]
    )
    assert found.geography is Geography.MSOA21 and found.rows_held == 3
    by_id = {row.fact_id: row for row in found.rows}
    assert set(by_id) == {f"{area}/feature/homes_higher_bands" for area in (ONE, TWO, THREE)}
    one = by_id[f"{ONE}/feature/homes_higher_bands"]
    assert (one.value, one.state, one.derivation_id) == (30.0, State.PRESENT, "area_row_ratio@1")
    assert by_id[f"{THREE}/feature/homes_higher_bands"].value is None
    evidence = Evidence.of("lon-2026-09-24-01", found.files, homes_higher_bands.METHODS, found.rows)
    assert len(evidence.rows) == 3


def test_the_row_of_the_catalogue_says_the_day_the_source_and_what_a_band_is(tmp_path: Path):
    metric = built(tmp_path).metric
    assert metric.vintage == "2025-03-31"
    assert metric.source_ids == tuple(sorted((LOOKUP, homes_higher_bands.SOURCE)))
    assert "council tax bands E to H" in metric.definition
    assert "Valuation Office Agency as at 2025-03-31" in metric.definition
    assert "what a home would have sold for in 1991" in metric.definition
    assert "{" not in metric.definition
