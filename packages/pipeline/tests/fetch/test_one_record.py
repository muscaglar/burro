"""Fetch and evidence hold one record of a fetched file, and one name for where it is kept.

Fetch writes the receipt that evidence reads, and both work out the same key in
the vault and the same path in the repository. If each wrote its own, a file
could be stored where `seal` does not look for it. Every file here is made up,
and no socket is opened.
"""

import ast
import re
from pathlib import Path

import burro_pipeline
import pytest
from burro_pipeline.evidence import How, Period, Receipt, file_id_of, read_receipts
from burro_pipeline.evidence.receipt import FILE_NAME_PATTERN, RECEIPTS_FOLDER
from burro_pipeline.fetch.run import write_receipt
from burro_pipeline.fetch.store import FolderStore, held_at, publisher_name
from burro_pipeline.registry import Use

SOURCE = Path(burro_pipeline.__file__).parent
RECEIPT = SOURCE / "evidence" / "receipt.py"

# Names as a publisher or a browser might give them, the hostile among them.
NAMES = [
    "homes.csv",
    "Table 1 (final).xlsx",
    "café homes.csv",
    "../../etc/passwd",
    "C:\\saved\\homes.csv",
    ".hidden",
    " . .. homes.csv ",
    "..",
    "",
    "a\nb\x1b[31m.csv",
    "a\x7fb.csv",
    "x" * 300 + ".csv",
    "x" * 300,
]


def receipt_of(source_id: str, sha256: str, name: str, size: int) -> Receipt:
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=source_id,
        use=Use.SCORING,
        publisher_file=name,
        url="https://files.made-up.example/homes.csv",
        sha256=sha256,
        bytes=size,
        retrieved_at="2026-09-24T09:12:31Z",
        how=How.FETCHED,
        edition="2025",
        data_period=Period(as_at="2025-03-31"),
    )


@pytest.mark.parametrize("name", NAMES)
def test_a_file_is_stored_under_the_key_its_receipt_gives(tmp_path: Path, name: str):
    saved = tmp_path / "saved"
    saved.write_bytes(b"code,homes\nmade-up-1,10\n")
    store = FolderStore(tmp_path / "store")
    held, _ = store.put("made-up-homes", name, saved)
    receipt = receipt_of(held.source_id, held.sha256, held.name, held.bytes)
    assert held.key == receipt.vault_key()
    assert held.file_id == receipt.file_id
    assert held_at(receipt.vault_key(), receipt.bytes) == held
    assert store.list() == [held]


@pytest.mark.parametrize("name", NAMES)
def test_every_name_the_store_gives_a_file_is_one_a_receipt_accepts(name: str):
    assert re.fullmatch(FILE_NAME_PATTERN, publisher_name(name))


def test_a_receipt_is_written_at_the_path_the_receipt_gives(tmp_path: Path):
    receipt = receipt_of("made-up-homes", "ab" * 32, "homes.csv", 24)
    write_receipt(receipt, tmp_path / RECEIPTS_FOLDER)
    assert (tmp_path / receipt.path()).read_bytes() == receipt.canonical()
    assert read_receipts(tmp_path / RECEIPTS_FOLDER) == (receipt,)


def _written(path: Path) -> list[str]:
    """Every piece of text a module holds, but for what it says of itself."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    said = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef)
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    }
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in said
    ]


@pytest.mark.parametrize(
    "folder", ["raw/", "data/receipts"], ids=["the vault", "the receipts in the repository"]
)
def test_where_a_file_and_its_receipt_are_kept_is_written_in_one_place(folder: str):
    modules = sorted(SOURCE.rglob("*.py"))
    assert RECEIPT in modules
    elsewhere = [
        path.relative_to(SOURCE).as_posix()
        for path in modules
        if path != RECEIPT and any(folder in text for text in _written(path))
    ]
    assert elsewhere == []
    assert any(folder.rstrip("/") in text for text in _written(RECEIPT))


def test_fetch_makes_no_record_of_its_own():
    """The only receipt is the one evidence defines. Fetch imports it and builds no other."""
    defined = [
        f"{path.relative_to(SOURCE).as_posix()}: {node.name}"
        for path in sorted((SOURCE / "fetch").rglob("*.py"))
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.ClassDef) and "receipt" in node.name.lower()
    ]
    assert defined == []
