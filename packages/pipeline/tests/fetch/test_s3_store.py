"""The object store, against a stand-in on the loopback address.

The stand-in keeps files in memory and answers as an S3 store does. It works
out every signature again from what arrived on the wire, so a request that was
signed one way and sent another is refused. Every file is made up, and a
connection to any address but the loopback is blocked.
"""

import hashlib
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit
from xml.sax.saxutils import escape

import pytest
from burro_pipeline.fetch.s3 import S3Store, Settings, authorization, settings_from_environment
from burro_pipeline.fetch.store import Held, StoreError, store_from_environment

from .support import (
    CANARY_BUCKET,
    CANARY_KEY,
    CANARY_ROW,
    CANARY_SECRET,
    ONLY_LOOPBACK,
    Answer,
    Seen,
    Served,
    serving,
)

pytestmark = ONLY_LOOPBACK

CONTENT = f"code,homes\nmade-up-1,10\n{CANARY_ROW},20\n".encode()
SHA256 = hashlib.sha256(CONTENT).hexdigest()
NOW = datetime(2026, 9, 24, 9, 0, 0, tzinfo=UTC)
# The start of every token for the next page of a listing. It holds the signs that a
# query must encode, so a token that is signed one way and sent another is refused.
NEXT_PAGE = "t+/= &<"


class StandIn:
    """An S3 store in memory. `page` is how many keys a listing holds."""

    def __init__(self, page: int = 1000) -> None:
        self.held: dict[str, bytes] = {}
        self.page = page
        self.fail_with: Answer | None = None

    def error(self, status: int, code: str) -> Answer:
        said = f"{code}: {CANARY_BUCKET} {CANARY_KEY} at a made-up host"
        body = f"<Error><Code>{code}</Code><Message>{said}</Message></Error>"
        return Answer(status, {"Content-Type": "application/xml"}, body.encode())

    def __call__(self, request: Seen) -> Answer:
        address = urlsplit(request.path)
        path, query = unquote(address.path), parse_qsl(address.query, keep_blank_values=True)
        signed = request.headers.get("authorization", "").split("SignedHeaders=")[-1].split(",")[0]
        expected = authorization(
            method=request.method,
            path=path,
            query=query,
            headers={name: request.headers[name] for name in signed.split(";")},
            payload_sha256=request.headers.get("x-amz-content-sha256", ""),
            key_id=CANARY_KEY,
            secret=CANARY_SECRET,
            region="auto",
        )
        if request.headers.get("authorization") != expected:
            return self.error(403, "SignatureDoesNotMatch")
        if self.fail_with is not None:
            return self.fail_with
        bucket, _, key = path.removeprefix("/").partition("/")
        if bucket != CANARY_BUCKET:
            return self.error(404, "NoSuchBucket")
        if not key:
            return self.listing(dict(query))
        if request.method == "PUT":
            if request.headers.get("if-none-match") == "*" and key in self.held:
                return self.error(412, "PreconditionFailed")
            if hashlib.sha256(request.body).hexdigest() != request.headers["x-amz-content-sha256"]:
                return self.error(400, "XAmzContentSHA256Mismatch")
            self.held[key] = request.body
            return Answer(200)
        if key not in self.held:
            return self.error(404, "NoSuchKey")
        return Answer(200, body=self.held[key])

    def listing(self, query: dict[str, str]) -> Answer:
        keys = sorted(key for key in self.held if key.startswith(query.get("prefix", "")))
        start = int(query.get("continuation-token", NEXT_PAGE + "0").removeprefix(NEXT_PAGE))
        shown, rest = keys[start : start + self.page], keys[start + self.page :]
        contents = "".join(
            f"<Contents><Key>{escape(key)}</Key><Size>{len(self.held[key])}</Size></Contents>"
            for key in shown
        )
        more = (
            f"<IsTruncated>true</IsTruncated>"
            f"<NextContinuationToken>{escape(NEXT_PAGE)}{start + self.page}</NextContinuationToken>"
            if rest
            else "<IsTruncated>false</IsTruncated>"
        )
        body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
            f"<Name>{CANARY_BUCKET}</Name>{contents}{more}</ListBucketResult>"
        )
        return Answer(200, {"Content-Type": "application/xml"}, body.encode())


@pytest.fixture
def stand_in() -> StandIn:
    return StandIn()


@pytest.fixture
def served(stand_in: StandIn) -> Iterator[Served]:
    with serving(stand_in) as server:
        yield server


def settings(served: Served, **changed: str) -> Settings:
    values = {
        "endpoint": served.address,
        "bucket": CANARY_BUCKET,
        "key_id": CANARY_KEY,
        "secret": CANARY_SECRET,
        **changed,
    }
    return Settings(**values, plain_http_to_loopback=True)


@pytest.fixture
def store(served: Served) -> S3Store:
    return S3Store(settings(served), now=lambda: NOW)


@pytest.fixture
def saved(tmp_path: Path) -> Path:
    path = tmp_path / "saved.csv"
    path.write_bytes(CONTENT)
    return path


def test_a_file_put_in_the_store_comes_back_byte_for_byte(
    store: S3Store, stand_in: StandIn, saved: Path, tmp_path: Path
):
    held, new = store.put("made-up-source", "homes.csv", saved)
    assert new
    assert held == Held("made-up-source", SHA256, "homes.csv", len(CONTENT))
    assert stand_in.held == {f"raw/made-up-source/{SHA256}/homes.csv": CONTENT}
    assert store.get(SHA256, tmp_path / "copy.csv") == held
    assert (tmp_path / "copy.csv").read_bytes() == CONTENT


def test_every_request_is_signed_as_it_is_sent(store: S3Store, served: Served, saved: Path):
    held, _ = store.put("made-up-source", "a name with spaces & signs.csv", saved)
    assert store.list() == [held]
    assert [request.method for request in served.seen] == ["HEAD", "PUT", "GET"]
    assert all("Signature=" in request.headers["authorization"] for request in served.seen)
    assert all(request.headers["x-amz-date"] == "20260924T090000Z" for request in served.seen)


def test_a_file_put_twice_is_sent_once_and_never_written_over(
    store: S3Store, served: Served, saved: Path
):
    first, _ = store.put("made-up-source", "homes.csv", saved)
    second, new = store.put("made-up-source", "homes.csv", saved)
    assert not new
    assert second == first
    assert [request.method for request in served.seen] == ["HEAD", "PUT", "HEAD"]


def test_a_file_stored_by_another_run_a_moment_ago_is_left_as_it_is(stand_in: StandIn, saved: Path):
    key = f"raw/made-up-source/{SHA256}/homes.csv"

    def stored_in_between(request: Seen) -> Answer:
        answer = StandIn.__call__(stand_in, request)
        if request.method == "HEAD":
            stand_in.held[key] = CONTENT
        return answer

    with serving(stored_in_between) as other:
        racing = S3Store(settings(other), now=lambda: NOW)
        held, new = racing.put("made-up-source", "homes.csv", saved)
    assert not new
    assert held.key == key
    assert [request.headers.get("if-none-match") for request in other.seen] == [None, "*"]


def test_a_listing_is_read_page_by_page(served: Served, stand_in: StandIn, tmp_path: Path):
    stand_in.page = 2
    store = S3Store(settings(served), now=lambda: NOW)
    expected: list[Held] = []
    for number in range(5):
        path = tmp_path / f"{number}.csv"
        path.write_bytes(f"made up {number}\n".encode())
        expected.append(store.put(f"made-up-{number}", "file.csv", path)[0])
    served.seen.clear()
    assert store.list() == expected
    assert len(served.seen) == 3


def test_a_key_the_store_did_not_write_is_left_out_of_the_list(
    store: S3Store, stand_in: StandIn, saved: Path
):
    held, _ = store.put("made-up-source", "homes.csv", saved)
    stand_in.held["raw/made-up-source/not-a-hash/homes.csv"] = b"made up"
    stand_in.held[f"raw/made-up-source/{SHA256}/.part-0123"] = b"made up"
    assert store.list() == [held]


def test_a_file_changed_in_the_store_is_refused(
    store: S3Store, stand_in: StandIn, saved: Path, tmp_path: Path
):
    held, _ = store.put("made-up-source", "homes.csv", saved)
    stand_in.held[held.key] = CONTENT[:-1] + b"!"
    with pytest.raises(StoreError, match="does not match its hash"):
        store.get(SHA256, tmp_path / "copy.csv")
    assert list(tmp_path.glob("copy*")) == []


def test_a_hash_held_with_another_size_stops_the_run(
    store: S3Store, stand_in: StandIn, saved: Path
):
    held, _ = store.put("made-up-source", "homes.csv", saved)
    stand_in.held[held.key] = CONTENT + b"more"
    with pytest.raises(StoreError, match="another size"):
        store.put("made-up-source", "homes.csv", saved)


def test_a_hash_the_store_does_not_hold_is_refused(store: S3Store, tmp_path: Path):
    with pytest.raises(StoreError, match="holds no file"):
        store.get("0" * 64, tmp_path / "copy.csv")


def shows_nothing_behind_it(error: BaseException) -> bool:
    """True if a traceback of this error would print no other error with it."""
    return error.__cause__ is None and (error.__context__ is None or error.__suppress_context__)


def secrets_in(text: str, served: Served) -> list[str]:
    secret = [CANARY_BUCKET, CANARY_KEY, CANARY_SECRET, CANARY_ROW, served.address]
    return [value for value in [*secret, str(served.port), "127.0.0.1"] if value in text]


@pytest.mark.parametrize(
    ("changed", "said"),
    [
        ({"secret": "made-up-wrong-secret"}, "403 SignatureDoesNotMatch"),
        ({"bucket": "made-up-other-bucket"}, "404 NoSuchBucket"),
    ],
)
def test_a_refusal_gives_the_status_and_the_code_and_nothing_the_store_said(
    served: Served, saved: Path, changed: dict[str, str], said: str
):
    store = S3Store(settings(served, **changed), now=lambda: NOW)
    with pytest.raises(StoreError) as refused:
        store.list()
    assert said in str(refused.value)
    assert secrets_in(str(refused.value), served) == []
    assert shows_nothing_behind_it(refused.value)


def test_an_error_names_no_address_bucket_or_key(
    served: Served, stand_in: StandIn, saved: Path, tmp_path: Path
):
    store = S3Store(settings(served), now=lambda: NOW)
    store.put("made-up-source", "homes.csv", saved)
    stand_in.fail_with = stand_in.error(500, "InternalError")
    for call in (
        lambda: store.put("made-up-other", "homes.csv", saved),
        lambda: store.get(SHA256, tmp_path / "copy.csv"),
        store.list,
    ):
        with pytest.raises(StoreError) as refused:
            call()
        assert "500" in str(refused.value)
        assert secrets_in(str(refused.value), served) == []
        assert secrets_in(repr(refused.value), served) == []
        assert shows_nothing_behind_it(refused.value)


def test_a_store_that_is_not_there_is_an_error_that_names_no_address(saved: Path):
    with serving(lambda _: Answer(200)) as gone:
        store = S3Store(settings(gone), now=lambda: NOW)
    with pytest.raises(StoreError) as refused:
        store.put("made-up-source", "homes.csv", saved)
    assert str(refused.value) == "the store could not be reached"
    assert secrets_in(str(refused.value), gone) == []
    assert shows_nothing_behind_it(refused.value)


def test_a_redirect_from_the_store_is_never_followed(served: Served, stand_in: StandIn):
    stand_in.fail_with = Answer(307, {"Location": f"{served.address}/elsewhere"})
    store = S3Store(settings(served), now=lambda: NOW)
    with pytest.raises(StoreError, match="307"):
        store.list()
    assert len(served.seen) == 1


def test_a_listing_with_a_document_type_is_refused(served: Served, stand_in: StandIn):
    stand_in.fail_with = Answer(
        200,
        body=b'<?xml version="1.0"?><!DOCTYPE a [<!ENTITY b "c">]><ListBucketResult/>',
    )
    store = S3Store(settings(served), now=lambda: NOW)
    with pytest.raises(StoreError, match="could not be read"):
        store.list()


def test_the_settings_and_the_store_have_no_readable_form(served: Served):
    shown = repr(settings(served)) + repr(S3Store(settings(served))) + str(settings(served))
    assert secrets_in(shown, served) == []


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://made-up.example",
        "http://127.0.0.1:9",
        "ftp://made-up.example",
        "https://",
        "https://user:word@made-up.example",  # public-only: allow
        "https://made-up.example/a/path",
        "https://made-up.example?query=1",
        "https://made-up.example:notaport",
        "made-up.example",
    ],
)
def test_an_address_that_is_not_plain_https_is_refused_and_not_repeated(endpoint: str):
    environment = {
        "BURRO_STORE_ENDPOINT": endpoint,
        "BURRO_STORE_BUCKET": CANARY_BUCKET,
        "BURRO_STORE_KEY_ID": CANARY_KEY,
        "BURRO_STORE_SECRET": CANARY_SECRET,
    }
    with pytest.raises(StoreError) as refused:
        store_from_environment(environment)
    message = str(refused.value)
    assert "BURRO_STORE_ENDPOINT" in message
    assert all(value not in message for value in environment.values())


def test_a_bucket_name_that_could_not_be_one_is_refused_and_not_repeated():
    environment = {
        "BURRO_STORE_ENDPOINT": "https://made-up.example",
        "BURRO_STORE_BUCKET": "Made Up/Bucket",
        "BURRO_STORE_KEY_ID": CANARY_KEY,
        "BURRO_STORE_SECRET": CANARY_SECRET,
    }
    with pytest.raises(StoreError) as refused:
        store_from_environment(environment)
    assert "BURRO_STORE_BUCKET" in str(refused.value)
    assert "Made Up" not in str(refused.value)


def test_the_environment_names_the_object_store_and_the_region_defaults():
    environment = {
        "BURRO_STORE_ENDPOINT": "https://made-up.example",
        "BURRO_STORE_BUCKET": CANARY_BUCKET,
        "BURRO_STORE_KEY_ID": CANARY_KEY,
        "BURRO_STORE_SECRET": CANARY_SECRET,
    }
    assert isinstance(store_from_environment(environment), S3Store)
    assert settings_from_environment(environment).region == "auto"
    assert not settings_from_environment(environment).plain_http_to_loopback
    assert settings_from_environment({**environment, "BURRO_STORE_REGION": "weur"}).region == "weur"
