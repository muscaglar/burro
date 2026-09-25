"""The store as an object store that speaks the S3 protocol.

Written with the standard library: the request signing is Signature Version 4,
and the tests check it against the worked examples in its documentation.

The address of the store, the bucket and the keys are read from the
environment. None is ever printed, logged or put in an error: an error from
here is a fixed sentence, a status and the store's own error code, and nothing
the store or the network stack said. A redirect from the store is never followed.
"""

import hashlib
import hmac
import http.client
import io
import ipaddress
import re
import ssl
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO
from urllib.parse import quote, urlsplit

from burro_pipeline.evidence.receipt import VAULT_PREFIX
from burro_pipeline.fetch.markup import MarkupError, read
from burro_pipeline.fetch.store import (
    LARGEST_RECEIPT,
    PIECE,
    RECEIPT_KEY,
    S3_VARIABLES,
    Held,
    Part,
    StoreError,
    checked,
    checked_as_kept,
    checked_receipt,
    checked_receipt_key,
    copy_checked,
    held_at,
    kept_under,
)

UNRESERVED = "-_.~"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
BUCKET = re.compile(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]")
ERROR_CODE = re.compile(rb"<Code>([A-Za-z0-9]{1,64})</Code>")
SECONDS = 120
LISTING_LIMIT = 8 * 1024 * 1024
PAGE = 1000


def canonical_path(path: str) -> str:
    """A path as it is signed and sent: each part encoded once, slashes kept."""
    return quote(path, safe="/" + UNRESERVED)


def canonical_query(query: list[tuple[str, str]]) -> str:
    """A query as it is signed and sent: sorted by name, every part encoded."""
    return "&".join(
        f"{quote(name, safe=UNRESERVED)}={quote(value, safe=UNRESERVED)}"
        for name, value in sorted(query)
    )


def _hmac(key: bytes, text: str) -> bytes:
    return hmac.new(key, text.encode(), hashlib.sha256).digest()


def authorization(
    *,
    method: str,
    path: str,
    query: list[tuple[str, str]],
    headers: Mapping[str, str],
    payload_sha256: str,
    key_id: str,
    secret: str,
    region: str,
) -> str:
    """The value of the Authorization header, by Signature Version 4.

    Every header given is signed. `x-amz-date` must be among them: the date of
    the signature is read from it, so the two cannot differ.
    """
    signed = {name.lower(): " ".join(value.split()) for name, value in headers.items()}
    stamp = signed.get("x-amz-date", "")
    if not re.fullmatch(r"\d{8}T\d{6}Z", stamp):
        raise ValueError("a request is signed with its x-amz-date header, as 20260101T000000Z")
    names = ";".join(sorted(signed))
    request = "\n".join(
        [
            method,
            canonical_path(path),
            canonical_query(query),
            *(f"{name}:{signed[name]}" for name in sorted(signed)),
            "",
            names,
            payload_sha256,
        ]
    )
    scope = f"{stamp[:8]}/{region}/s3/aws4_request"
    to_sign = "\n".join(
        ["AWS4-HMAC-SHA256", stamp, scope, hashlib.sha256(request.encode()).hexdigest()]
    )
    key = f"AWS4{secret}".encode()
    for part in (stamp[:8], region, "s3", "aws4_request"):
        key = _hmac(key, part)
    signature = hmac.new(key, to_sign.encode(), hashlib.sha256).hexdigest()
    return (
        f"AWS4-HMAC-SHA256 Credential={key_id}/{scope},SignedHeaders={names},Signature={signature}"
    )


@dataclass(frozen=True, repr=False)
class Settings:
    """Where the store is and how to sign for it. Never shown: it has no readable form."""

    endpoint: str
    bucket: str
    key_id: str
    secret: str
    region: str = "auto"
    # Tests alone set this, to reach a stand-in on the loopback address.
    plain_http_to_loopback: bool = False

    def __repr__(self) -> str:
        return "Settings(not shown)"


def settings_from_environment(environment: Mapping[str, str]) -> Settings:
    return Settings(
        endpoint=environment.get("BURRO_STORE_ENDPOINT", ""),
        bucket=environment.get("BURRO_STORE_BUCKET", ""),
        key_id=environment.get("BURRO_STORE_KEY_ID", ""),
        secret=environment.get("BURRO_STORE_SECRET", ""),
        region=environment.get("BURRO_STORE_REGION", "") or "auto",
    )


def _is_loopback(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class S3Store:
    """Files in one bucket, under the same keys as the folder store writes."""

    kind = "object_store"
    # The environment names the product's store and no other: `store_from_environment`.
    part = Part.PRODUCT

    def __init__(
        self,
        settings: Settings,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        named: Sequence[str] = S3_VARIABLES,
    ) -> None:
        """`named` is what the environment calls the four settings, for a refusal to name."""
        endpoint, bucket, key_id, secret = named
        address = urlsplit(settings.endpoint)
        try:
            port = address.port
        except ValueError:
            port = -1
        plain = (
            address.scheme == "http"
            and settings.plain_http_to_loopback
            and _is_loopback(address.hostname or "")
        )
        if (
            not (address.scheme == "https" or plain)
            or not address.hostname
            or port == -1
            or address.username is not None
            or address.path not in ("", "/")
            or address.query
            or address.fragment
        ):
            raise StoreError(f"{endpoint} must be an https address with no path, query or login")
        if not BUCKET.fullmatch(settings.bucket):
            raise StoreError(f"{bucket} is not a bucket name")
        if not (settings.key_id and settings.secret and settings.region):
            raise StoreError(f"{key_id} and {secret} must both be set")
        self._settings = settings
        self._secure = address.scheme == "https"
        self._host = address.hostname
        self._port = port
        self._netloc = address.netloc
        self._now = now

    def __repr__(self) -> str:
        return "S3Store(not shown)"

    def put(self, source_id: str, name: str, content: Path) -> tuple[Held, bool]:
        held = checked(source_id, name, content)
        status, headers, _ = self._ask("HEAD", held.key)
        if status == 200:
            if headers.get("content-length") != str(held.bytes):
                raise StoreError("the store holds that hash with another size: look at it by hand")
            return held, False
        if status != 404:
            raise StoreError(f"the store answered {status} when asked if it holds a file")
        try:
            with content.open("rb") as file:
                # If another run stored the file a moment ago, the store says so and
                # leaves it as it is.
                status, _, said = self._ask(
                    "PUT", held.key, more={"if-none-match": "*"}, body=file, sha256=held.sha256,
                    length=held.bytes,
                )  # fmt: skip
        except OSError:
            raise StoreError("the file to store could not be read") from None
        if status == 412:
            return held, False
        if status not in (200, 201, 204):
            raise StoreError(f"the store answered {_said(status, said)} to a file sent to it")
        return held, True

    def get(self, sha256: str, to: Path) -> Held:
        held = next((held for held in self.list() if held.sha256 == sha256), None)
        if held is None:
            raise StoreError("the store holds no file with that hash")

        def keep(answer: BinaryIO) -> None:
            try:
                copy_checked(answer, to, sha256)
            except OSError:
                raise StoreError("the copy could not be written, or the store stopped") from None
            except http.client.HTTPException:
                raise StoreError("the store stopped before the file was whole") from None

        status, _, said = self._ask("GET", held.key, keep=keep)
        if status != 200:
            raise StoreError(f"the store answered {_said(status, said)} when asked for a file")
        return held

    def keep_at(self, key: str, content: Path, sha256: str, size: int) -> bool:
        """Keep a file under a key of the caller's own choosing, if nothing is kept there.

        Returns whether this call added it. What is kept under the key already
        is left as it is, whatever it holds: the caller reads it back to say
        whether it is the same. A publisher's file is never kept this way: it
        is kept under its hash, by `put`.
        """
        try:
            with content.open("rb") as file:
                status, _, said = self._ask(
                    "PUT", key, more={"if-none-match": "*"}, body=file, sha256=sha256, length=size
                )
        except OSError:
            raise StoreError("the file to keep could not be read") from None
        if status == 412:
            return False
        if status not in (200, 201, 204):
            raise StoreError(f"the store answered {_said(status, said)} to a file sent to it")
        return True

    def copy_from(self, key: str, sha256: str, to: Path) -> bool:
        """Copy out what is kept under a key, and keep the copy only if its hash is right.

        Returns whether anything is kept under the key.
        """

        def keep(answer: BinaryIO) -> None:
            try:
                copy_checked(answer, to, sha256)
            except OSError:
                raise StoreError("the copy could not be written, or the store stopped") from None
            except http.client.HTTPException:
                raise StoreError("the store stopped before the file was whole") from None

        status, _, said = self._ask("GET", key, keep=keep)
        if status == 404:
            return False
        if status != 200:
            raise StoreError(f"the store answered {_said(status, said)} when asked for a file")
        return True

    def _ask(
        self,
        method: str,
        key: str,
        *,
        query: list[tuple[str, str]] | None = None,
        more: Mapping[str, str] | None = None,
        body: BinaryIO | None = None,
        sha256: str = EMPTY_SHA256,
        length: int = 0,
        keep: Callable[[BinaryIO], None] | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        """One signed request. Returns the status, the headers, and a short body.

        With `keep`, a good answer's body is handed over as a stream and not read here.
        """
        settings = self._settings
        path = f"/{settings.bucket}/{key}" if key else f"/{settings.bucket}"
        headers = {
            "host": self._netloc,
            "x-amz-content-sha256": sha256,
            "x-amz-date": self._now().strftime("%Y%m%dT%H%M%SZ"),
            **(more or {}),
        }
        headers["authorization"] = authorization(
            method=method,
            path=path,
            query=query or [],
            headers=headers,
            payload_sha256=sha256,
            key_id=settings.key_id,
            secret=settings.secret,
            region=settings.region,
        )
        if body is not None:
            headers["content-length"] = str(length)
        target = canonical_path(path) + (f"?{canonical_query(query)}" if query else "")
        connection = (
            http.client.HTTPSConnection(
                self._host,
                self._port,
                timeout=SECONDS,
                context=ssl.create_default_context(),
                blocksize=PIECE,
            )
            if self._secure
            else http.client.HTTPConnection(
                self._host, self._port, timeout=SECONDS, blocksize=PIECE
            )
        )
        try:
            connection.request(method, target, body=body, headers=headers)
            answer = connection.getresponse()
            found = {name.lower(): value for name, value in answer.getheaders()}
            if keep is not None and answer.status == 200:
                keep(answer)
                return answer.status, found, b""
            return answer.status, found, answer.read(LISTING_LIMIT + 1)
        except StoreError:
            raise
        except TimeoutError:
            raise StoreError("the store did not answer in time") from None
        except ssl.SSLError:
            raise StoreError(
                "the store could not be reached: the secure connection failed"
            ) from None
        except (OSError, http.client.HTTPException):
            raise StoreError("the store could not be reached") from None
        finally:
            connection.close()

    def keep_receipt(self, key: str, content: bytes) -> bool:
        checked_receipt(key, content)
        # The store leaves a receipt that is already there as it is, and says so.
        status, _, said = self._ask(
            "PUT", key, more={"if-none-match": "*"}, body=io.BytesIO(content),
            sha256=hashlib.sha256(content).hexdigest(), length=len(content),
        )  # fmt: skip
        if status == 412:
            return False
        if status not in (200, 201, 204):
            raise StoreError(f"the store answered {_said(status, said)} to a receipt sent to it")
        return True

    def receipt(self, key: str) -> bytes | None:
        checked_receipt_key(key)
        status, _, said = self._ask("GET", key)
        if status == 404:
            return None
        if status != 200:
            raise StoreError(f"the store answered {_said(status, said)} when asked for a receipt")
        return checked_as_kept(said)

    def receipts(self, source_id: str = "") -> dict[str, bytes]:
        found: dict[str, bytes] = {}
        for key, size in self._keys(kept_under(source_id)):
            if RECEIPT_KEY.fullmatch(key) and size <= LARGEST_RECEIPT:
                status, _, said = self._ask("GET", key)
                if status != 200:
                    asked = "when asked for a receipt"
                    raise StoreError(f"the store answered {_said(status, said)} {asked}")
                found[key] = said
        return dict(sorted(found.items()))

    def _keys(self, prefix: str) -> list[tuple[str, int]]:
        """Every key under a prefix, with the size of what it holds, read page by page."""
        found: list[tuple[str, int]] = []
        token = ""
        while True:
            query = [("list-type", "2"), ("max-keys", str(PAGE)), ("prefix", prefix)]
            if token:
                query.append(("continuation-token", token))
            status, _, said = self._ask("GET", "", query=query)
            if status != 200:
                raise StoreError(f"the store answered {_said(status, said)} when asked for a list")
            page, token = _listing(said)
            found.extend(page)
            if not token:
                return found

    # Last in the class: below it, `list` would mean this method and not the built-in.
    def list(self) -> list[Held]:
        held = (held_at(key, size) for key, size in self._keys(VAULT_PREFIX))
        return sorted((file for file in held if file is not None), key=lambda file: file.key)


def _said(status: int, body: bytes) -> str:
    """A status and the store's own error code, which is one word and names nothing."""
    code = ERROR_CODE.search(body[:65536])
    return f"{status} {code[1].decode()}" if code else str(status)


def _listing(body: bytes) -> tuple[list[tuple[str, int]], str]:
    """The keys on one page of a listing, each with its size, and the token for the next page."""
    if len(body) > LISTING_LIMIT:
        raise StoreError("the store sent a listing too large to read")
    within: list[str] = []
    words: dict[str, str] = {}
    found: list[tuple[str, int]] = []
    whole: dict[str, str] = {}

    def start(name: str, _: dict[str, str]) -> None:
        within.append(name)
        if name == "Contents":
            words.clear()

    def text(piece: str) -> None:
        if len(within) >= 2 and within[-2] == "Contents":
            words[within[-1]] = words.get(within[-1], "") + piece
        elif len(within) == 2:
            whole[within[-1]] = whole.get(within[-1], "") + piece

    def end(name: str) -> None:
        within.pop()
        if name == "Contents" and words.get("Size", "").isdigit():
            found.append((words.get("Key", ""), int(words["Size"])))

    try:
        read(body, start, end, text)
    except MarkupError:
        raise StoreError("the store sent a listing that could not be read") from None
    more = whole.get("IsTruncated", "").strip() == "true"
    token = whole.get("NextContinuationToken", "").strip()
    if more and not token:
        raise StoreError("the store cut a listing short and gave no way to go on")
    return found, token if more else ""
