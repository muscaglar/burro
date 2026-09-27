"""Tokens: what a link holds, what a session is, and what binds a link to a browser.

Each is 32 bytes from the system's own source of randomness. What is stored of one is
its SHA-256 and never the token, so that whoever reads the file of accounts can use none
of them. A plain hash is enough for a token, where it is not for a password: a token is
256 random bits, which nobody finds by trying.

No key is used here, and nothing here is ever given a spec.
"""

import hashlib
import hmac
import re
import secrets

BYTES = 32
# 128 bits: an id that names a row and opens nothing.
ID_BYTES = 16

# 32 bytes as URL-safe text. What is not in this shape is no token, and is never hashed.
_SHAPE = re.compile(r"[A-Za-z0-9_-]{43}")


def fresh() -> str:
    return secrets.token_urlsafe(BYTES)


def fresh_id() -> str:
    return secrets.token_urlsafe(ID_BYTES)


def in_shape(sent: str) -> bool:
    """Whether what was sent could be a token at all."""
    return _SHAPE.fullmatch(sent) is not None


def hashed(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def same(one: str, other: str) -> bool:
    """Whether two hashes are the same, in a time that does not tell how alike they are."""
    return hmac.compare_digest(one.encode(), other.encode())


def same_secret(sent: str, held: str) -> bool:
    """Whether what was sent is the secret that is held.

    Each is hashed first, so that the comparison is of two things of one length and
    tells nothing of how long the secret is.
    """
    # A secret is in plain letters. What is not is compared as nothing, in the same time.
    written = sent.encode() if sent.isascii() else b""
    return hmac.compare_digest(
        hashlib.sha256(written).digest(), hashlib.sha256(held.encode()).digest()
    )
