"""The files that names and seeds are read from: the gate, the receipt, and the store left alone.

Every file here is made up: `names_support.py` says how. No test reads a
publisher's file or reaches a network.
"""

import ast
from pathlib import Path

import burro_pipeline.areas
import pytest
from burro_pipeline.areas import (
    names_centres,
    names_draft,
    names_files,
    names_ground,
    names_places,
    names_wards,
    seeds_roads,
)
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.registry.model import SHARE_ALIKE_LICENCES, Status, Use

from ..cells.support import held as every_file
from ..cells.support import registry
from .names_support import CENTRES, FILES, NAMES, contents, given

AREAS = Path(burro_pipeline.areas.__file__).parent
MODULES = sorted([*AREAS.glob("names*.py"), *AREAS.glob("seeds*.py")])
# Every source a module of names or seeds reads, by the module's own constant.
READ = {
    names_places.SOURCE,
    names_centres.SOURCE,
    names_wards.SOURCE,
    seeds_roads.SOURCE,
    names_ground.BOUNDARIES,
    names_ground.spine.LOOKUP,
}
# Sources that would be useful and that the gate does not give for a gazetteer.
REFUSED = (
    "hoc-library-msoa-names",
    "gla-high-street-boundaries",
    "ons-census-2021-housing-tables",
    "os-open-rivers",
    "os-open-greenspace",
    "osm-geofabrik-greater-london",
)


def test_every_source_that_is_read_is_approved_for_a_gazetteer_and_is_not_share_alike():
    for source_id in sorted(READ):
        source = registry().get(source_id)
        registry().require(source_id, Use.GAZETTEER)
        assert source.status is Status.APPROVED, source_id
        assert not source.share_alike and not source.licences & SHARE_ALIKE_LICENCES, source_id


@pytest.mark.parametrize("source_id", REFUSED)
def test_a_source_the_gate_refuses_is_not_opened_though_a_file_of_it_is_there(
    tmp_path: Path, source_id: str
):
    """The gate is asked before a receipt or a file is looked for."""
    made = given(tmp_path, {})
    with pytest.raises(LockError) as refused:
        names_files.with_receipt(made.inputs, source_id)
    assert refused.value.rule == "gate_refuses"
    with pytest.raises(LockError) as refused:
        names_files.without_receipt(made.inputs, source_id)
    assert refused.value.rule == "gate_refuses"
    assert made.inputs.opened == ()


@pytest.mark.parametrize("path", MODULES, ids=lambda path: path.name)
def test_no_module_of_names_or_seeds_names_a_source_the_gate_refuses(path: Path):
    """OpenStreetMap least of all: ADR 0004."""
    text = path.read_text(encoding="utf-8").casefold()
    held = {
        node.value
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert not held & set(REFUSED)
    assert "osm-" not in text and "geofabrik" not in text and "overture" not in text


def test_a_file_is_read_through_its_receipt_and_says_what_the_receipt_says(tmp_path: Path):
    made = given(tmp_path)
    file = names_files.with_receipt(made.inputs, NAMES)
    receipt = next(each for each in made.receipts if each.source_id == NAMES)
    assert file.has_receipt and file.receipt == receipt
    assert (file.file_id, file.sha256, file.name) == (
        receipt.file_id,
        receipt.sha256,
        FILES["names"][1],
    )
    assert (file.edition, file.retrieved_on) == ("2026-07", "2026-09-23")
    assert file.publisher == "Ordnance Survey"
    assert file.path.read_bytes() == contents()["names"]


def test_a_file_with_no_receipt_is_read_for_a_draft_alone_and_says_that_it_has_none(
    tmp_path: Path,
):
    made = given(tmp_path)
    with pytest.raises(LockError) as refused:
        names_files.either(made.inputs, CENTRES, draft=False)
    assert refused.value.rule == "input_has_one_receipt"
    file = names_files.either(made.inputs, CENTRES, draft=True)
    assert not file.has_receipt
    # Nothing is put in the place of what nobody has stated.
    assert (file.edition, file.data_date, file.retrieved_on) == ("", "", "")
    assert file.path.read_bytes() == contents()["centres"]
    assert file.publisher == "Greater London Authority"
    with pytest.raises(LockError):
        _ = file.opened


def test_a_file_that_has_a_receipt_is_never_read_without_it(tmp_path: Path):
    made = given(tmp_path)
    with pytest.raises(LockError) as refused:
        names_files.without_receipt(made.inputs, NAMES)
    assert refused.value.rule == "input_has_one_receipt"


def test_a_build_stops_at_the_file_with_no_receipt_and_a_draft_does_not(tmp_path: Path):
    made = given(tmp_path)
    with pytest.raises(LockError) as refused:
        names_draft.read(made.inputs, draft=False)
    assert (refused.value.rule, refused.value.subject) == ("input_has_one_receipt", CENTRES)
    assert not names_draft.read(made.inputs, draft=True).files[CENTRES].has_receipt


def test_nothing_is_written_to_the_store(tmp_path: Path):
    made = given(tmp_path)
    before = every_file(made.store)
    names_draft.read(made.inputs, draft=True)
    assert every_file(made.store) == before


def test_a_geopackage_is_taken_out_of_its_zip_once_and_beside_the_copy(tmp_path: Path):
    made = given(tmp_path)
    file = names_files.with_receipt(made.inputs, names_wards.SOURCE)
    first = names_files.taken_out(file, names_wards.MEMBER)
    assert first.parent == file.path.parent and first.read_bytes().startswith(b"SQLite format 3")
    written = first.stat().st_mtime_ns
    assert names_files.taken_out(file, names_wards.MEMBER) == first
    assert first.stat().st_mtime_ns == written
    with pytest.raises(LockError) as refused:
        names_files.taken_out(file, "not-there.gpkg")
    assert refused.value.rule == "input_is_as_described"
