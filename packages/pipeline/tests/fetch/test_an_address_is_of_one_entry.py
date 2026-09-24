"""A file is fetched only from an address that the entry of its source names.

A publisher serves many datasets from one host. If the gate held a file to a
host and no more, a file that the registry bans, holds or keeps for the audit
would pass under any approved id on that host, with a receipt that says
`scoring`. So an entry names the addresses of its files, and an address passes
only under the entry that names it. Every file here is made up. Nothing is
asked of any publisher: the addresses of the repository's own registry are
read and never opened.
"""

from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

import pytest
from burro_pipeline.evidence.fence import source_is_kept_apart
from burro_pipeline.fetch.by_hand import keep_by_hand
from burro_pipeline.fetch.cli import main
from burro_pipeline.fetch.download import Downloaded, user_agent
from burro_pipeline.fetch.gate import Reason, Refused, ask, hold_where_it_ended, hosts_of
from burro_pipeline.fetch.run import WORDS, Status, Why, fetch
from burro_pipeline.fetch.sources import Listed, load_list
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.registry import Registry, Source, load
from burro_pipeline.registry import Status as Standing
from burro_pipeline.registry.model import INTERNAL_USES

from .support import MADE_UP_REGISTRY

REPOSITORY = Path(__file__).parents[4]
NOW = datetime(2026, 9, 24, 9, 12, 31, tzinfo=UTC)
AGENT = user_agent("data@made-up.example")
BODY = b"code,homes\nmade-up-1,10\nmade-up-2,20\n"
FILES = "https://files.made-up.example"
# The file of the entry that is read for the audit alone, on the host of every entry.
OF_THE_AUDIT = f"{FILES}/audit/made-up-classification.csv"


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


def listed(**changed: object) -> Listed:
    fields: dict[str, object] = {
        "item": "homes",
        "source_id": "made-up-homes",
        "use": "scoring",
        "what": "Made-up homes by made-up area",
        "format": "csv",
        "page": "https://made-up.example/homes",
        "url": f"{FILES}/files/homes.csv",
        "max_bytes": 1_000_000,
        "edition": "2025",
        "data_period": {"as_at": "2025-03-31"},
        **changed,
    }
    return Listed.model_validate(fields)


def never(*_: object, **__: object) -> Downloaded:
    raise AssertionError("nothing may be asked of a publisher here")


def refused(file: Listed, registry: Registry) -> Refused:
    with pytest.raises(Refused) as caught:
        ask(file, registry)
    return caught.value


# The gate


def test_an_address_the_entry_names_passes(registry: Registry):
    assert ask(listed(), registry).id == "made-up-homes"
    assert ask(listed(url=f"{FILES}/files/2025/homes.csv"), registry).id == "made-up-homes"


@pytest.mark.parametrize(
    "address",
    [
        # On the host the entry names, and under no address it names for its files.
        f"{FILES}/about-these-files",
        f"{FILES}/other/homes.csv",
        f"{FILES}/files",
        f"{FILES}/filesystem/homes.csv",
        f"{FILES}/FILES/homes.csv",
        # The file of another entry, however it is written.
        OF_THE_AUDIT,
        f"{FILES}/files/../audit/made-up-classification.csv",
        f"{FILES}/files/%2e%2e/audit/made-up-classification.csv",
        f"{FILES}/files/%252e%252e/audit/made-up-classification.csv",
        f"{FILES}/files/..%2Faudit/made-up-classification.csv",
        f"{FILES}/files//audit/made-up-classification.csv",
        # Another port of the host, and the host of the entry's pages.
        f"{FILES}:8443/files/homes.csv",
        "https://made-up.example/files/homes.csv",
        "https://made-up.example/homes",
    ],
)
def test_an_address_the_entry_does_not_name_for_its_files_is_refused(
    registry: Registry, address: str
):
    found = refused(listed(url=address), registry)
    assert found.reason is Reason.NOT_THE_ADDRESS
    assert "example" not in str(found) and "audit" not in str(found)


def test_an_entry_that_names_no_address_has_no_file_to_fetch(registry: Registry):
    """An entry from before the field, or one whose files nobody has found."""
    file = listed(
        source_id="made-up-rail", use="validation_only", page="https://made-up.example/rail"
    )
    bare = Registry(
        tuple(
            entry.model_copy(update={"file_urls": ()}) if entry.id == "made-up-rail" else entry
            for entry in registry
        )
    )
    assert refused(file.model_copy(update={"url": f"{FILES}/rail/made-up.csv"}), bare).reason is (
        Reason.NOT_THE_ADDRESS
    )


def test_the_hosts_of_an_entry_are_those_of_its_pages_and_of_its_files(registry: Registry):
    entry = registry.get("made-up-homes")
    assert {"made-up.example", "files.made-up.example"} <= hosts_of(entry)
    only_files = entry.model_copy(
        update={"url": "https://made-up.example/homes", "evidence_urls": ()}
    )
    assert "files.made-up.example" in hosts_of(only_files)


def test_the_refusal_says_where_to_name_the_address():
    said = WORDS[Why.NOT_THE_ADDRESS]
    assert "`file_urls`" in said and "Nothing was asked for" in said
    assert "Never widen" in said
    assert "`file_urls`" in WORDS[Why.NOT_THE_HOST]


# What the reviewer did: a file for the audit, under an approved id on the same host


def test_a_file_of_the_audit_is_not_fetched_under_an_approved_id_on_its_host(
    registry: Registry, store: FolderStore, receipts: Path
):
    honest = listed(
        item="classification",
        source_id="made-up-audit",
        use="audit_only",
        page="https://made-up.example/audit",
        url=OF_THE_AUDIT,
    )
    (outcome,) = fetch([honest], registry, store, receipts, agent=AGENT, downloader=never)
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.NOT_THE_STORE)

    under_another = listed(item="classification", url=OF_THE_AUDIT)
    first, second = fetch(
        [listed(), under_another], registry, store, receipts, agent=AGENT, downloader=never
    )
    assert (first.status, first.why) == (Status.SKIPPED, Why.ANOTHER_WAS_REFUSED)
    assert (second.status, second.why) == (Status.REFUSED, Why.NOT_THE_ADDRESS)
    assert f" status=refused why={int(Why.NOT_THE_ADDRESS)} " in second.line()
    assert not store.folder.exists() and not receipts.exists()


def test_a_file_of_the_audit_is_not_taken_by_hand_under_an_approved_id(
    registry: Registry, store: FolderStore, receipts: Path, tmp_path: Path
):
    saved = tmp_path / "made-up.csv"
    saved.write_bytes(BODY)
    file = listed(item="notes", page="https://made-up.example/notes", url="", by_hand=True)
    outcome = keep_by_hand(
        1, file, saved, OF_THE_AUDIT, "2026-09-24", registry, store, receipts, NOW
    )
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.NOT_THE_ADDRESS)
    assert store.list() == [] and not receipts.exists()


def arriving_from(final: str):
    """A stand-in for the download: the publisher sends the request on, and a file arrives."""

    def downloader(
        address: str, to: Path, limits: object, *, agent: str, may_redirect_to: tuple[str, ...] = ()
    ) -> Downloaded:
        to.write_bytes(BODY)
        return Downloaded("0" * 64, len(BODY), final, "homes.csv", "text/csv")

    return downloader


@pytest.mark.parametrize(
    "final",
    [
        # On a host the entry names, where other datasets are, and no address of the entry.
        f"{FILES}/other/homes.csv",
        f"{FILES}/homes.csv",
        f"{FILES}:8443/files/homes.csv",
        "https://made-up.example/made-up/homes.csv",
    ],
)
def test_a_file_that_arrived_from_a_host_of_the_entry_and_no_address_of_it_is_not_kept(
    registry: Registry, store: FolderStore, receipts: Path, final: str
):
    (outcome,) = fetch(
        [listed()], registry, store, receipts, agent=AGENT, downloader=arriving_from(final)
    )
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.NOT_THE_ADDRESS)
    assert outcome.held is None
    assert store.list() == [] and not receipts.exists()


@pytest.mark.parametrize(
    "final",
    [
        OF_THE_AUDIT,
        f"{FILES}/AUDIT/made-up-classification.csv",
        f"{FILES}/audit/2025/made-up-classification.csv",
        "https://made-up.example/audit",
        "https://made-up.example/ratings",
    ],
)
def test_a_file_that_arrived_from_an_address_another_entry_holds_is_not_kept(
    registry: Registry, store: FolderStore, receipts: Path, final: str
):
    (outcome,) = fetch(
        [listed()], registry, store, receipts, agent=AGENT, downloader=arriving_from(final)
    )
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.NOT_THE_ADDRESS)
    assert outcome.held is None
    assert store.list() == [] and not receipts.exists()


@pytest.mark.parametrize(
    "final",
    [
        f"{FILES}/files/homes.csv",
        f"{FILES}/files/2025/homes-v2.csv",
        # The publisher added a parameter on the way. The receipt does not keep it.
        f"{FILES}/files/homes.csv?made-up=1",
        # A host the list names, where no entry holds an address.
        "https://cdn.made-up.example/made-up/homes.csv",
        # A page that this entry cites too is no address of another alone.
        f"{FILES}/about-these-files",
    ],
)
def test_a_file_that_arrived_from_an_address_no_other_entry_holds_is_kept(
    registry: Registry, store: FolderStore, receipts: Path, final: str
):
    file = listed(may_redirect_to=["cdn.made-up.example"])
    (outcome,) = fetch(
        [file], registry, store, receipts, agent=AGENT, downloader=arriving_from(final)
    )
    assert outcome.status is Status.OK
    hold_where_it_ended(registry.get("made-up-homes"), registry, final)


# A host that only the list names, where another entry keeps its files

CDN = "https://cdn.made-up.example"
# A made-up login, in addresses that must be refused for holding one.
AUDIT_WITH_A_LOGIN = "https://made-up@cdn.made-up.example/audit/c.csv"  # public-only: allow
HOMES_WITH_A_LOGIN = "https://made-up@cdn.made-up.example/made-up/homes.csv"  # public-only: allow
# An entry that is read for the audit alone, and keeps its files on a host that the entry
# for homes names nowhere. A list may name that host as one a request is sent on to.
ELSEWHERE = """
[[source]]
id = "made-up-elsewhere"
name = "Made-up tables for the audit, kept on another host"
publisher = "Made-up Office"
url = "https://made-up.example/elsewhere"
dimension = "audit"
licence = "OGL-3.0"
commercial_use = "yes"
share_alike = false
status = "held"
status_reason = "Made up. It is read for the audit and for nothing else."
uses = ["audit_only"]
verified_how = "secondary_source"
verified_on = 2026-09-23
evidence_urls = ["https://made-up.example/elsewhere-licence"]
file_urls = ["https://cdn.made-up.example/audit/"]
"""


@pytest.fixture
def with_a_host_elsewhere(tmp_path: Path) -> Registry:
    path = tmp_path / "registry-elsewhere.toml"
    path.write_text(MADE_UP_REGISTRY + ELSEWHERE, encoding="utf-8")
    return load(path)


def sent_on_to(registry: Registry, store: FolderStore, receipts: Path, final: str):
    file = listed(may_redirect_to=["cdn.made-up.example"])
    (outcome,) = fetch(
        [file], registry, store, receipts, agent=AGENT, downloader=arriving_from(final)
    )
    return outcome


@pytest.mark.parametrize(
    "final",
    [
        # The file of the other entry, as it is written.
        f"{CDN}/audit/c.csv",
        f"{CDN}/AUDIT/c.csv",
        f"{CDN}/%61udit/c.csv",
        # The same file, written so that a server could read the address another way.
        f"{CDN}/audit//c.csv",
        f"{CDN}//audit/c.csv",
        f"{CDN}/made-up/../audit/c.csv",
        f"{CDN}/./audit/c.csv",
        f"{CDN}/audit/./c.csv",
        f"{CDN}/made-up/%2e%2e/audit/c.csv",
        f"{CDN}/made-up/%252e%252e/audit/c.csv",
        f"{CDN}/made-up/..%2Faudit/c.csv",
        f"{CDN}/made-up%2F..%2Faudit/c.csv",
        f"{CDN}/audit%2F%2Fc.csv",
        f"{CDN}/made-up\\..\\audit\\c.csv",
        f"{CDN}/made-up/%5C../audit/c.csv",
        # A letter of it encoded more than once, which a server that decodes again would read.
        f"{CDN}/%2561udit/c.csv",
        f"{CDN}/%252561udit/c.csv",
        f"{CDN}/audi%2574/c.csv",
        f"{CDN}/%2541UDIT/c.csv",
        # With a login, over plain http, and with a space in it.
        AUDIT_WITH_A_LOGIN,
        "http://cdn.made-up.example/audit/c.csv",
        f"{CDN}/audit/c.csv ",
        f"{CDN}/audit /c.csv",
    ],
)
def test_a_file_sent_on_to_the_file_of_another_entry_is_not_kept_however_it_is_written(
    with_a_host_elsewhere: Registry, store: FolderStore, receipts: Path, final: str
):
    outcome = sent_on_to(with_a_host_elsewhere, store, receipts, final)
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.NOT_THE_ADDRESS)
    assert outcome.held is None
    assert "example" not in outcome.line() and "audit" not in outcome.line()
    assert store.list() == [] and not receipts.exists()


@pytest.mark.parametrize(
    "final",
    [
        f"{CDN}/made-up//homes.csv",
        f"{CDN}/made-up/../homes.csv",
        f"{CDN}/made-up/%2e%2e/homes.csv",
        f"{CDN}/made-up/./homes.csv",
        f"{CDN}/made-up\\homes.csv",
        HOMES_WITH_A_LOGIN,
    ],
)
def test_an_address_that_reads_more_than_one_way_is_not_kept_on_any_host(
    registry: Registry, store: FolderStore, receipts: Path, final: str
):
    """No entry names the host. What a server would read in the address is not known."""
    outcome = sent_on_to(registry, store, receipts, final)
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.NOT_THE_ADDRESS)
    assert store.list() == [] and not receipts.exists()
    with pytest.raises(Refused):
        hold_where_it_ended(registry.get("made-up-homes"), registry, final)


@pytest.mark.parametrize(
    "final",
    [
        f"{CDN}/made-up/homes.csv",
        # A space in the name of a file, encoded as a browser sends it.
        f"{CDN}/made-up/made-up%20homes.csv",
        # A sign encoded twice, which names no address of any entry however it is read.
        f"{CDN}/made-up/homes%2520of%25202025.csv",
        f"{CDN}/auditors/c.csv?made-up=1",
    ],
)
def test_a_file_sent_on_to_an_address_that_no_entry_names_is_kept(
    with_a_host_elsewhere: Registry, store: FolderStore, receipts: Path, final: str
):
    assert sent_on_to(with_a_host_elsewhere, store, receipts, final).status is Status.OK


# The command line


LIST = """
schema_version = 1
build = "made-up"

[[file]]
item = "classification"
source_id = "made-up-homes"
use = "scoring"
what = "Made-up homes by made-up area"
format = "csv"
page = "https://made-up.example/homes"
url = "https://files.made-up.example/audit/made-up-classification.csv"
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
        assert f"step={step} n=1 source=made-up-homes status=refused why=18 seconds=0.0" in lines
        assert any("`file_urls`" in line for line in lines)
    assert not (tmp_path / "store").exists() and not (tmp_path / "receipts").exists()


# The repository's own registry, and the list of the first build


@cache
def of_the_repository() -> Registry:
    return load(REPOSITORY / "registry" / "sources")


def as_a_file_of(entry: Source, address: str) -> Listed:
    """A made-up file of an entry, at an address. It is asked of the gate and never fetched."""
    use = next(use for use in entry.uses if use not in INTERNAL_USES)
    return Listed.model_validate(
        {
            "item": "made-up",
            "source_id": entry.id,
            "use": use,
            "what": "Made up",
            "format": "other",
            "page": entry.url,
            "url": address.split("#")[0],
            # A parameter with no value is a part of the address too, and a list names it.
            "url_parameters": [
                name for name, _ in parse_qsl(urlsplit(address).query, keep_blank_values=True)
            ],
            "max_bytes": 10,
            "edition": "made up",
            "data_period": {"as_at": "2021"},
        }
    )


def in_the_product() -> list[Source]:
    return [
        entry
        for entry in of_the_repository()
        if entry.status is Standing.APPROVED
        and not source_is_kept_apart(entry)
        and any(use not in INTERNAL_USES for use in entry.uses)
    ]


def test_no_address_of_another_entry_passes_under_an_entry_of_the_product():
    """Every address every entry holds, asked of the gate under every entry on its host."""
    registry = of_the_repository()
    asked, not_listed = 0, 0
    for entry in in_the_product():
        for other in registry:
            if other.id == entry.id:
                continue
            for address in (other.url, *other.evidence_urls, *other.file_urls):
                try:
                    file = as_a_file_of(entry, address)
                except ValueError:
                    # An address that no list may hold, so it cannot be asked for at all.
                    not_listed += 1
                    continue
                asked += 1
                with pytest.raises(Refused):
                    ask(file, registry)
    assert asked > 1000
    assert not_listed < asked / 100


def test_no_file_of_the_first_build_passes_under_another_entry():
    registry = of_the_repository()
    files = load_list("m1").files
    for file in files:
        assert ask(file, registry).id == file.source_id
        for entry in in_the_product():
            if entry.id == file.source_id:
                continue
            under_another = file.model_copy(
                update={"source_id": entry.id, "page": entry.url, "use": entry.uses[0]}
            )
            with pytest.raises(Refused):
                ask(under_another, registry)


def test_every_file_of_the_first_build_is_at_an_address_its_entry_names():
    from burro_pipeline.registry.addresses import is_a_file_of

    registry = of_the_repository()
    for file in load_list("m1").files:
        assert is_a_file_of(registry.get(file.source_id), file.url), file.item
