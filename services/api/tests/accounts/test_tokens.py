"""Tokens: what a link holds, what a session is, and what binds a link to a browser."""

import re

import pytest
from burro_api.accounts import tokens
from burro_api.accounts.wire import ID_PATTERN


def test_a_token_is_32_bytes_from_the_systems_own_source(monkeypatch: pytest.MonkeyPatch):
    asked: list[int] = []

    def token_urlsafe(size: int) -> str:
        asked.append(size)
        return "t" * 43

    monkeypatch.setattr(tokens.secrets, "token_urlsafe", token_urlsafe)

    assert tokens.fresh() == "t" * 43
    assert asked == [32]


def test_no_two_tokens_are_the_same_and_each_is_in_the_shape_of_one():
    made = [tokens.fresh() for _ in range(2_000)]

    assert len(set(made)) == len(made)
    assert all(tokens.in_shape(token) for token in made)
    assert all(re.fullmatch(r"[A-Za-z0-9_-]{43}", token) for token in made)


def test_an_id_is_128_bits_and_is_in_the_form_the_contract_gives():
    made = [tokens.fresh_id() for _ in range(2_000)]

    assert len(set(made)) == len(made)
    assert all(re.fullmatch(ID_PATTERN, each) for each in made)


def test_what_is_kept_of_a_token_is_its_sha_256_and_never_the_token():
    # The digest of the three letters, as every table of test vectors gives it.
    known = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"

    assert tokens.hashed("abc") == known
    token = tokens.fresh()
    assert token not in tokens.hashed(token) and len(tokens.hashed(token)) == 64


@pytest.mark.parametrize(
    "sent",
    [
        "",
        "short",
        "t" * 42,
        "t" * 44,
        "t" * 42 + " ",
        "t" * 42 + "=",
        "t" * 42 + "\n",
        "t" * 42 + "\N{LATIN SMALL LETTER E WITH ACUTE}",
        # Half of a pair, which cannot be written down to be hashed.
        "t" * 42 + "\ud800",
        "t" * 128,
    ],
)
def test_what_is_not_in_the_shape_of_a_token_is_never_hashed(sent: str):
    assert not tokens.in_shape(sent)


def test_two_hashes_are_compared_in_a_time_that_does_not_tell_how_alike_they_are(
    monkeypatch: pytest.MonkeyPatch,
):
    compared: list[tuple[bytes, bytes]] = []

    def compare_digest(one: bytes, other: bytes) -> bool:
        compared.append((one, other))
        return one == other

    monkeypatch.setattr(tokens.hmac, "compare_digest", compare_digest)
    one, other = tokens.hashed("one"), tokens.hashed("other")

    assert tokens.same(one, one) and not tokens.same(one, other)
    # The standard library's own comparison, and no `==` before it that would tell first.
    assert compared == [(one.encode(), one.encode()), (one.encode(), other.encode())]


def test_a_secret_is_compared_by_its_hash_so_that_not_even_its_length_is_told():
    assert tokens.same_secret("s" * 40, "s" * 40)
    assert not tokens.same_secret("s" * 40, "s" * 39)
    assert not tokens.same_secret("", "s" * 40)
    assert not tokens.same_secret("s" * 39 + "\ud800", "s" * 40)
