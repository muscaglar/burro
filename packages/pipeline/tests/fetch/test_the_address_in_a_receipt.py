"""The address a receipt holds is one that can be committed where anyone reads it.

A receipt is committed in public, and it holds the address a file came from in
the end. A publisher may send a download on to an address that holds a key: a
signature, an expiry, the id of a session. A key was looked for by the name of
its parameter, and a name nobody had thought of was kept.

So no parameter is kept unless the list names it as part of the file's
address, and then only with the value the list's own address gives it, once.
A name alone is not enough: a publisher may send a key under a name the list
holds. And `;` is refused in a path and in a query, in a list and in the
address a file came from, because some servers read what follows it as a
parameter. Every address here is made up, and no socket is opened.
"""

from pathlib import Path

import pytest
from burro_pipeline.evidence import How, read_receipts
from burro_pipeline.fetch.run import Arrival, Status, Why, keep, written_down
from burro_pipeline.fetch.sources import Listed, ListError, load_list
from burro_pipeline.fetch.store import FolderStore

CONTENT = b"code,homes\nmade-up-1,10\n"
FILE = "https://files.made-up.example/download"
# Keys as publishers and their hosts write them. Few hold a word that says what they are.
SIGNED = (
    "X-Amz-Signature=zzyzx&X-Amz-Credential=zzyzx&X-Amz-Expires=300&X-Goog-Expires=300"
    "&Expires=1790000000&Policy=zzyzx&Key-Pair-Id=zzyzx&se=2026-09-24&sp=r&sv=2024&sr=b"
    "&st=zzyzx&hmac=zzyzx&hash=zzyzx&code=zzyzx&k=zzyzx&t=zzyzx&jwt=zzyzx&otp=zzyzx"
    "&sid=zzyzx&nonce=zzyzx&ticket=zzyzx&access=zzyzx&apikey=zzyzx&id=zzyzx"
)


def listed(**changed: object) -> Listed:
    fields: dict[str, object] = {
        "item": "homes",
        "source_id": "made-up-homes",
        "use": "scoring",
        "what": "Made-up homes",
        "format": "csv",
        "page": "https://made-up.example/homes",
        "url": FILE,
        "max_bytes": 1_000_000,
        "edition": "2025",
        "data_period": {"as_at": "2025-03-31"},
        **changed,
    }
    return Listed.model_validate(fields)


def receipt_address(tmp_path: Path, file: Listed, arrived_from: str, how: How = How.FETCHED) -> str:
    """The address in the receipt of a file that arrived from an address."""
    path = tmp_path / "arrived"
    path.write_bytes(CONTENT)
    arrival = Arrival(path, "homes.csv", arrived_from, "2026-09-24T09:12:31Z", how)
    outcome = keep(1, file, arrival, FolderStore(tmp_path / "store"), tmp_path / "receipts")
    assert outcome.status is Status.OK
    (receipt,) = read_receipts(tmp_path / "receipts")
    written = (tmp_path / "receipts" / "made-up-homes" / f"{receipt.file_id}.json").read_text()
    assert "zzyzx" not in written
    return receipt.url


@pytest.mark.parametrize("how", [How.FETCHED, How.BY_HAND])
def test_no_parameter_is_kept_that_the_list_does_not_name(tmp_path: Path, how: How):
    assert receipt_address(tmp_path, listed(), f"{FILE}?{SIGNED}", how) == FILE


def test_a_parameter_with_no_name_or_no_value_is_not_kept(tmp_path: Path):
    assert receipt_address(tmp_path, listed(), f"{FILE}?zzyzx&=zzyzx&zzyzx=") == FILE


@pytest.mark.parametrize("how", [How.FETCHED, How.BY_HAND])
def test_a_parameter_the_list_names_is_kept_and_no_other(tmp_path: Path, how: How):
    file = listed(url=f"{FILE}?year=2025&layers=0", url_parameters=["year", "layers"])
    arrived_from = f"{FILE}?layers=0&{SIGNED}&year=2025#zzyzx"
    assert receipt_address(tmp_path, file, arrived_from, how) == f"{FILE}?layers=0&year=2025"


def test_a_parameter_is_named_letter_for_letter(tmp_path: Path):
    file = listed(url=f"{FILE}?year=2025", url_parameters=["year"])
    assert receipt_address(tmp_path, file, f"{FILE}?Year=zzyzx&year=2025&years=zzyzx") == (
        f"{FILE}?year=2025"
    )


LAYERS = f"{FILE}?layers=0"


@pytest.mark.parametrize(
    ("arrived_from", "kept"),
    [
        (f"{FILE}?layers=0", LAYERS),
        (f"{FILE}?layers=0&token=zzyzx", LAYERS),
        (f"{FILE}?layers=0#zzyzx", LAYERS),
        # The value is not the one the list's own address gives.
        (f"{FILE}?layers=zzyzx", FILE),
        (f"{FILE}?layers=", FILE),
        (f"{FILE}?layers=00", FILE),
        (f"{FILE}?layers=0%26token%3Dzzyzx", FILE),
        (f"{FILE}?layers=0%3Btoken%3Dzzyzx", FILE),
        (f"{FILE}?Layers=zzyzx", FILE),
        (f"{FILE}?zzyzx", FILE),
        # The list's address gives it once, so it is kept once.
        (f"{FILE}?layers=0&layers=zzyzx", LAYERS),
        (f"{FILE}?layers=zzyzx&layers=0", LAYERS),
        (f"{FILE}?layers=0&layers=0", LAYERS),
    ],
)
@pytest.mark.parametrize("how", [How.FETCHED, How.BY_HAND])
def test_a_parameter_is_kept_only_with_the_value_the_lists_own_address_gives_it_once(
    tmp_path: Path, how: How, arrived_from: str, kept: str
):
    file = listed(url=LAYERS, url_parameters=["layers"])
    assert receipt_address(tmp_path, file, arrived_from, how) == kept


def test_a_parameter_the_list_names_and_gives_no_value_is_not_kept(tmp_path: Path):
    """A list may name a parameter before anybody has found the address."""
    file = listed(url="", url_parameters=["layers"], by_hand=True)
    assert receipt_address(tmp_path, file, f"{FILE}?layers=zzyzx", How.BY_HAND) == FILE


def test_a_parameter_the_list_gives_twice_is_kept_twice(tmp_path: Path):
    file = listed(url=f"{FILE}?layers=0&layers=1", url_parameters=["layers"])
    arrived_from = f"{FILE}?layers=1&layers=0&layers=1&layers=2"
    assert receipt_address(tmp_path, file, arrived_from) == f"{FILE}?layers=1&layers=0"


@pytest.mark.parametrize(
    "arrived_from",
    [
        f"{FILE}?layers=0;token=zzyzx",
        f"{FILE}?layers=0&a=b;token=zzyzx",
        f"{FILE};jsessionid=zzyzx?layers=0",
        "https://files.made-up.example/files;v=zzyzx/homes.csv",
        f"{FILE};zzyzx",
    ],
)
@pytest.mark.parametrize("how", [How.FETCHED, How.BY_HAND])
def test_an_address_that_holds_a_semicolon_is_not_written_down_and_nothing_is_kept(
    tmp_path: Path, how: How, arrived_from: str
):
    with pytest.raises(ValueError, match="`;`") as refused:
        written_down(arrived_from, LAYERS)
    assert "zzyzx" not in str(refused.value)
    path = tmp_path / "arrived"
    path.write_bytes(CONTENT)
    arrival = Arrival(path, "homes.csv", arrived_from, "2026-09-24T09:12:31Z", how)
    store = FolderStore(tmp_path / "store")
    file = listed(url=LAYERS, url_parameters=["layers"])
    outcome = keep(1, file, arrival, store, tmp_path / "receipts")
    why = Why.ADDRESS_GIVEN if how is How.BY_HAND else Why.BAD_ANSWER
    assert (outcome.status, outcome.why, outcome.held) == (Status.FAILED, why, None)
    assert store.list() == [] and not (tmp_path / "receipts").exists()
    assert "zzyzx" not in outcome.line() + outcome.words()


@pytest.mark.parametrize(
    "address",
    [
        f"{FILE}?layers=0;token=zzyzx",
        f"{FILE};jsessionid=zzyzx?layers=0",
        f"{FILE};jsessionid=zzyzx",
        "https://files.made-up.example/files;v=1/homes.csv",
    ],
)
def test_a_list_holds_no_address_with_a_semicolon_in_it(address: str):
    with pytest.raises(ValueError, match="`;`") as refused:
        listed(url=address, url_parameters=["layers"])
    assert "zzyzx" not in str(refused.value)


@pytest.mark.parametrize(
    "named",
    ["api_key", "token", "X-Amz-Signature", "sig", "session", "password", "user", "auth"],
)
def test_a_list_cannot_name_a_parameter_that_is_taken_for_a_key(named: str):
    with pytest.raises(ValueError, match="taken for a key"):
        listed(url_parameters=[named])


@pytest.mark.parametrize("named", ["", "a b", "a=b", "a&b", "yeär", "a" * 65])
def test_a_list_names_a_parameter_by_a_plain_name(named: str):
    with pytest.raises(ValueError, match="url_parameters"):
        listed(url_parameters=[named])


@pytest.mark.parametrize(
    "address",
    [f"{FILE}?year=2025", f"{FILE}?layers=0&year=2025", f"{FILE}?k=zzyzx", f"{FILE}?zzyzx"],
)
def test_the_address_a_list_gives_holds_no_parameter_the_list_does_not_name(address: str):
    with pytest.raises(ValueError, match="url_parameters") as refused:
        listed(url=address, url_parameters=["layers"])
    assert "zzyzx" not in str(refused.value)


def test_a_list_that_names_the_parameters_of_its_address_is_read(tmp_path: Path):
    path = tmp_path / "made-up.toml"
    path.write_text(
        'schema_version = 1\nbuild = "made-up"\n\n[[file]]\nitem = "homes"\n'
        'source_id = "made-up-homes"\nuse = "scoring"\nwhat = "Made-up homes"\nformat = "csv"\n'
        'page = "https://made-up.example/homes"\nmax_bytes = 1000\n'
        f'url = "{FILE}?layers=0"\nurl_parameters = ["layers"]\n',
        encoding="utf-8",
    )
    assert load_list(path).files[0].url_parameters == ("layers",)
    path.write_text(path.read_text().replace('url_parameters = ["layers"]\n', ""))
    with pytest.raises(ListError, match=r"homes: .*url_parameters"):
        load_list(path)


def test_every_address_of_the_first_build_holds_only_parameters_its_list_names():
    from urllib.parse import parse_qsl, urlsplit

    for file in load_list("m1").files:
        held = {name for name, _ in parse_qsl(urlsplit(file.url).query, keep_blank_values=True)}
        assert held <= set(file.url_parameters), file.item


def test_the_help_of_by_hand_says_which_parameters_of_an_address_are_written_down():
    from burro_pipeline import cli

    said = " ".join(cli.STEPS["by-hand"].about.split())
    assert "no parameter but those of the list's own address" in said
    assert "`url_parameters`" in said
