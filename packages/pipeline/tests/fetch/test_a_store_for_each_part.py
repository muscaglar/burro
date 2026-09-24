"""A file for the audit, or a census table about residents, is never kept in the product's store.

The store has three parts, each with a key of its own: the product, the census
tables about residents, and the audit (ADR 0015). The key of a product build
can read the product's part and no other. So a file that is read for the audit
alone, or shown as the census table, may only be written to a store that is
named for its part, by variables of its own.

No such store is built. Until one is, the refusal is the whole of it: fetch
asks nothing of a publisher for such a file, keeps nothing, and says why.

Which source is kept apart is one rule, and it is the fence's: `seal` and
`check` ask it of a receipt, and fetch asks it of a file. If the two did not
agree, fetch would keep a file in the product's store that `seal` then refuses.
Every file here is made up, and no socket is opened.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from burro_pipeline.evidence import fence
from burro_pipeline.fetch import gate
from burro_pipeline.fetch.by_hand import keep_by_hand
from burro_pipeline.fetch.cli import main
from burro_pipeline.fetch.download import Downloaded
from burro_pipeline.fetch.gate import Reason, Refused, ask, part_of
from burro_pipeline.fetch.run import WORDS, Status, Why, fetch
from burro_pipeline.fetch.s3 import S3Store
from burro_pipeline.fetch.sources import Listed
from burro_pipeline.fetch.store import FolderStore, Part, store_from_environment
from burro_pipeline.registry import Dimension, Registry, Source, Use, load
from burro_pipeline.registry import Status as Standing

from .support import MADE_UP_REGISTRY

REPOSITORY = Path(__file__).parents[4]
NOW = datetime(2026, 9, 24, 9, 12, 31, tzinfo=UTC)
FILES = "https://files.made-up.example"

# A file of each kind that is kept apart: its source, the use asked for, and its part.
KEPT_APART = [
    ("made-up-audit", Use.AUDIT_ONLY, Part.AUDIT),
    ("made-up-checked", Use.AUDIT_ONLY, Part.AUDIT),
    # The registry holds it for the audit too. So it is kept apart whatever it is listed for.
    ("made-up-checked", Use.VALIDATION_ONLY, Part.AUDIT),
    ("made-up-residents", Use.CENSUS_TABLE, Part.RESIDENTS),
]


@pytest.fixture
def registry(tmp_path: Path) -> Registry:
    path = tmp_path / "registry.toml"
    path.write_text(MADE_UP_REGISTRY, encoding="utf-8")
    return load(path)


@pytest.fixture
def store(tmp_path: Path) -> FolderStore:
    return FolderStore(tmp_path / "store")


@pytest.fixture
def receipts(tmp_path: Path) -> Path:
    return tmp_path / "receipts"


def address_of(source_id: str) -> str:
    """The address of a made-up file of an entry, under the prefix the entry names."""
    folder = "files" if source_id == "made-up-homes" else source_id.removeprefix("made-up-")
    return f"{FILES}/{folder}/made-up.csv"


def listed(source_id: str = "made-up-homes", use: Use = Use.SCORING, **changed: object) -> Listed:
    fields: dict[str, object] = {
        "item": "made-up",
        "source_id": source_id,
        "use": use,
        "what": "A made-up file",
        "format": "csv",
        "page": f"https://made-up.example/{source_id.removeprefix('made-up-')}",
        "url": address_of(source_id),
        "max_bytes": 1_000_000,
        "edition": "2025",
        "data_period": {"as_at": "2025-03-31"},
        **changed,
    }
    return Listed.model_validate(fields)


def never(*_: object, **__: object) -> Downloaded:
    raise AssertionError("nothing may be asked of a publisher here")


@pytest.mark.parametrize(("source_id", "use", "part"), KEPT_APART)
def test_the_part_of_the_store_a_file_is_for_is_read_from_its_use_and_its_heading(
    registry: Registry, source_id: str, use: Use, part: Part
):
    assert part_of(use, registry.get(source_id)) is part


def test_every_other_file_is_for_the_product(registry: Registry):
    assert part_of(Use.SCORING, registry.get("made-up-homes")) is Part.PRODUCT
    # A use that is for looking at a file is no use of the audit's.
    assert part_of(Use.VALIDATION_ONLY, registry.get("made-up-rail")) is Part.PRODUCT


def test_a_source_that_is_kept_apart_is_kept_apart_whatever_use_is_asked_for(registry: Registry):
    for use in Use:
        assert part_of(use, registry.get("made-up-audit")) is Part.AUDIT
        assert part_of(use, registry.get("made-up-residents")) is Part.RESIDENTS
        # Under another heading, the use says which of the two parts: the registry
        # refuses the census table there, and the part is still not the product's.
        of_the_use = Part.RESIDENTS if use is Use.CENSUS_TABLE else Part.AUDIT
        assert part_of(use, registry.get("made-up-checked")) is of_the_use


def held_for(heading: str, status: str, *uses: str) -> Source:
    """A made-up entry under a heading, with a status and the uses the registry holds it for."""
    return Source.model_validate(
        {
            "id": "made-up-classification",
            "name": "Made-up classification",
            "publisher": "Made-up Office",
            "url": "https://made-up.example/classification",
            "dimension": heading,
            "licence": "OGL-3.0",
            "commercial_use": "yes",
            "share_alike": False,
            "attribution": "Contains made-up data.",
            "attribution_verified": True,
            "status": status,
            "status_reason": "Made up. It is read for the audit, and to check a figure against.",
            "uses": list(uses),
            "verified_how": "primary_source",
            "verified_on": "2026-09-23",
            "evidence_urls": ["https://made-up.example/licence"],
        }
    )


@pytest.mark.parametrize(
    ("heading", "status", "uses"),
    [
        ("audit", "held", ("audit_only", "validation_only")),
        ("safety", "held", ("audit_only", "validation_only")),
        ("housing", "approved", ("audit_only", "validation_only")),
        ("housing", "gated", ("audit_only", "prototyping_only")),
    ],
)
def test_a_source_held_for_the_audit_and_for_looking_at_is_for_the_audits_part(
    heading: str, status: str, uses: tuple[str, ...]
):
    """What the reviewer found: listed for the other use, it was kept in the product's store."""
    source = held_for(heading, status, *uses)
    assert fence.source_is_kept_apart(source)
    for use in uses:
        assert part_of(Use(use), source) is Part.AUDIT


def every_entry(registry: Registry) -> list[Source]:
    return [*registry, *load(REPOSITORY / "registry" / "sources")]


def test_fetch_and_the_fence_agree_on_which_source_is_kept_apart(registry: Registry):
    """Every entry of the made-up registry and of the repository's own, asked for every use."""
    for source in every_entry(registry):
        for use in Use:
            apart = use in fence.USES_KEPT_APART or fence.source_is_kept_apart(source)
            assert (part_of(use, source) is not Part.PRODUCT) == apart, (source.id, use)


def test_the_part_of_a_file_that_is_kept_apart_is_the_audits_unless_it_is_a_census_table(
    registry: Registry,
):
    for source in every_entry(registry):
        if not fence.source_is_kept_apart(source):
            continue
        census = source.dimension is Dimension.RESIDENTS or (
            source.dimension is not Dimension.AUDIT and Use.CENSUS_TABLE in source.uses
        )
        for use in source.uses:
            assert part_of(use, source) is (Part.RESIDENTS if census else Part.AUDIT), source.id


def test_it_is_the_fences_own_rule_that_fetch_asks():
    assert gate.source_is_kept_apart is fence.source_is_kept_apart


def test_no_entry_of_the_product_behind_the_first_build_is_kept_apart():
    from burro_pipeline.fetch.sources import load_list

    registry = load(REPOSITORY / "registry" / "sources")
    for file in load_list("m1").files:
        source = registry.get(file.source_id)
        assert source.status is Standing.APPROVED
        assert part_of(file.use, source) is Part.PRODUCT, file.item


@pytest.mark.parametrize(("source_id", "use", "part"), KEPT_APART)
def test_the_gate_refuses_a_file_that_is_not_for_the_store_it_would_be_written_to(
    registry: Registry, source_id: str, use: Use, part: Part
):
    with pytest.raises(Refused) as refused:
        ask(listed(source_id, use), registry)
    assert refused.value.reason is Reason.NOT_THE_STORE
    # The gate is ready for a store of that part. None can be named yet.
    assert ask(listed(source_id, use), registry, part).id == source_id
    with pytest.raises(Refused) as the_other_way:
        ask(listed(), registry, part)
    assert the_other_way.value.reason is Reason.NOT_THE_STORE


def test_the_registry_is_still_asked_first(registry: Registry):
    with pytest.raises(Refused) as refused:
        ask(listed("made-up-audit", Use.SCORING), registry)
    assert refused.value.reason is Reason.GATE


@pytest.mark.parametrize(("source_id", "use", "part"), KEPT_APART)
def test_a_file_that_is_kept_apart_is_not_fetched_into_the_store_of_the_product(
    registry: Registry, store: FolderStore, receipts: Path, source_id: str, use: Use, part: Part
):
    files = [listed(), listed(source_id, use, item="kept-apart")]
    first, second = fetch(files, registry, store, receipts, agent="made up", downloader=never)
    assert (first.status, first.why) == (Status.SKIPPED, Why.ANOTHER_WAS_REFUSED)
    assert (second.status, second.why) == (Status.REFUSED, Why.NOT_THE_STORE)
    assert f" status=refused why={int(Why.NOT_THE_STORE)} " in second.line()
    assert not store.folder.exists() and not receipts.exists()


@pytest.mark.parametrize(("source_id", "use", "part"), KEPT_APART)
def test_a_file_that_is_kept_apart_is_not_taken_by_hand_into_the_store_of_the_product(
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    tmp_path: Path,
    source_id: str,
    use: Use,
    part: Part,
):
    saved = tmp_path / "made-up.csv"
    saved.write_bytes(b"code,count\nmade-up-1,10\n")
    file = listed(source_id, use, url="", by_hand=True)
    address = address_of(source_id)
    outcome = keep_by_hand(1, file, saved, address, "2026-09-24", registry, store, receipts, NOW)
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.NOT_THE_STORE)
    assert not store.folder.exists() and not receipts.exists()


def test_a_file_that_is_only_looked_at_is_still_fetched_into_the_store_of_the_product(
    registry: Registry,
):
    """A spike may open a file before anyone relies on it. That is no part of the audit."""
    assert ask(listed("made-up-rail", Use.VALIDATION_ONLY), registry).id == "made-up-rail"


def test_a_file_the_audit_reads_too_is_not_looked_at_in_the_store_of_the_product(
    registry: Registry,
):
    with pytest.raises(Refused) as refused:
        ask(listed("made-up-checked", Use.VALIDATION_ONLY), registry)
    assert refused.value.reason is Reason.NOT_THE_STORE


def test_every_store_that_can_be_named_is_the_store_of_the_product(tmp_path: Path):
    assert FolderStore(tmp_path).part is Part.PRODUCT
    assert S3Store.part is Part.PRODUCT
    named = store_from_environment({"BURRO_STORE_FOLDER": str(tmp_path)})
    assert named.part is Part.PRODUCT


def test_the_refusal_says_that_no_such_store_is_built():
    said = WORDS[Why.NOT_THE_STORE]
    assert "store of its own" in said and "No such store is built" in said
    assert "Nothing was asked for" in said


LIST = """
schema_version = 1
build = "made-up"

[[file]]
item = "for-the-audit"
source_id = "made-up-audit"
use = "audit_only"
what = "A made-up table for the audit"
format = "csv"
page = "https://made-up.example/audit"
url = "https://files.made-up.example/audit/made-up.csv"
max_bytes = 1000000
edition = "2025"
data_period = { as_at = "2025-03-31" }
"""


def test_plan_and_fetch_say_so_with_a_number_of_its_own(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    (tmp_path / "registry.toml").write_text(MADE_UP_REGISTRY, encoding="utf-8")
    (tmp_path / "list.toml").write_text(LIST, encoding="utf-8")
    common = ["--list", str(tmp_path / "list.toml"), "--registry", str(tmp_path / "registry.toml")]
    environment = {
        "BURRO_STORE_FOLDER": str(tmp_path / "store"),
        "BURRO_FETCH_CONTACT": "data@made-up.example",
    }
    for step in ("plan", "fetch"):
        more = ["--receipts", str(tmp_path / "receipts")] if step == "fetch" else []
        assert main([step, *common, *more, "--words"], environment, never) == 1
        lines = capsys.readouterr().out.splitlines()
        assert f"step={step} n=1 source=made-up-audit status=refused why=15 seconds=0.0" in lines
        assert any("No such store is built" in line for line in lines)
    assert not (tmp_path / "store").exists() and not (tmp_path / "receipts").exists()
