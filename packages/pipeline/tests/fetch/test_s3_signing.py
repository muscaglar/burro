"""The request signing of the object store, checked against the publisher's own worked examples.

Amazon prints four worked examples in its documentation of Signature Version 4
for S3: each gives a request, a date, a secret and the signature that must come
out. The secret below is the one printed there. It is an example and opens
nothing. No socket is opened here.
"""

import hashlib

import pytest
from burro_pipeline.fetch.s3 import authorization, canonical_path, canonical_query

EXAMPLE_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # noqa: S105
KEY_ID = "made-up-key-id"
HOST = "examplebucket.s3.amazonaws.com"
DATE = "20130524T000000Z"
EMPTY = hashlib.sha256(b"").hexdigest()

EXAMPLES = [
    pytest.param(
        "GET",
        "/test.txt",
        [],
        {"range": "bytes=0-9"},
        EMPTY,
        "f0e8bdb87c964420e857bd35b5d6ed310bd44f0170aba48dd91039c6036bdb41",
        id="get an object",
    ),
    pytest.param(
        "PUT",
        "/test$file.text",
        [],
        {"date": "Fri, 24 May 2013 00:00:00 GMT", "x-amz-storage-class": "REDUCED_REDUNDANCY"},
        hashlib.sha256(b"Welcome to Amazon S3.").hexdigest(),
        "98ad721746da40c64f1a55b78f14c238d841ea1380cd77a1b5971af0ece108bd",
        id="put an object",
    ),
    pytest.param(
        "GET",
        "/",
        [("lifecycle", "")],
        {},
        EMPTY,
        "fea454ca298b7da1c68078a5d1bdbfbbe0d65c699e0f91ac7a200a0136783543",
        id="a query with no value",
    ),
    pytest.param(
        "GET",
        "/",
        [("prefix", "J"), ("max-keys", "2")],
        {},
        EMPTY,
        "34b48302e7b5fa45bde8084f4b7868a86f0a534bc59db6670ed5711ef69dc6f7",
        id="list objects",
    ),
]


@pytest.mark.parametrize(("method", "path", "query", "more", "payload", "signature"), EXAMPLES)
def test_the_signature_is_the_one_the_documentation_works_out(
    method: str,
    path: str,
    query: list[tuple[str, str]],
    more: dict[str, str],
    payload: str,
    signature: str,
):
    headers = {"host": HOST, "x-amz-content-sha256": payload, "x-amz-date": DATE, **more}
    value = authorization(
        method=method,
        path=path,
        query=query,
        headers=headers,
        payload_sha256=payload,
        key_id=KEY_ID,
        secret=EXAMPLE_SECRET,
        region="us-east-1",
    )
    signed = ";".join(sorted(headers))
    assert value == (
        f"AWS4-HMAC-SHA256 Credential={KEY_ID}/20130524/us-east-1/s3/aws4_request,"
        f"SignedHeaders={signed},Signature={signature}"
    )


def test_a_path_is_encoded_once_and_keeps_its_slashes():
    assert canonical_path("/bucket/raw/made-up/a b$c.csv") == "/bucket/raw/made-up/a%20b%24c.csv"
    assert canonical_path("/bucket/raw/~tilde_and-dash.csv") == "/bucket/raw/~tilde_and-dash.csv"


def test_a_query_is_sorted_by_name_and_encoded():
    query = [("prefix", "raw/a b"), ("list-type", "2"), ("continuation-token", "a+b/c=")]
    assert canonical_query(query) == (
        "continuation-token=a%2Bb%2Fc%3D&list-type=2&prefix=raw%2Fa%20b"
    )


def test_header_names_are_signed_in_lower_case_with_values_trimmed():
    one = authorization(
        method="GET",
        path="/",
        query=[],
        headers={
            "Host": HOST,
            "X-Amz-Date": DATE,
            "x-amz-content-sha256": EMPTY,
            "Range": " a  b ",
        },
        payload_sha256=EMPTY,
        key_id=KEY_ID,
        secret=EXAMPLE_SECRET,
        region="auto",
    )
    other = authorization(
        method="GET",
        path="/",
        query=[],
        headers={"host": HOST, "x-amz-date": DATE, "x-amz-content-sha256": EMPTY, "range": "a b"},
        payload_sha256=EMPTY,
        key_id=KEY_ID,
        secret=EXAMPLE_SECRET,
        region="auto",
    )
    assert one == other


def test_a_request_with_no_date_cannot_be_signed():
    with pytest.raises(ValueError, match="x-amz-date"):
        authorization(
            method="GET",
            path="/",
            query=[],
            headers={"host": HOST},
            payload_sha256=EMPTY,
            key_id=KEY_ID,
            secret=EXAMPLE_SECRET,
            region="auto",
        )
