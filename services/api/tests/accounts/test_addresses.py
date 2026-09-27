"""The address a person signs in with, made regular and checked for its shape.

An account is known by the address as it is made regular, and a link is sent to that and
to nothing else. So two ways of writing an address may come to one account only where
they come to one mailbox.
"""

import pytest
from burro_api.accounts.addresses import LONGEST, LONGEST_LOCAL, regular

from ..support import CANARY


@pytest.mark.parametrize(
    ("typed", "made"),
    [
        ("name@example.org", "name@example.org"),
        ("  Name@Example.ORG \n", "name@example.org"),
        ("first.last@example.org", "first.last@example.org"),
        ("o'brien@example.org", "o'brien@example.org"),
        ("name+burro@example.org", "name+burro@example.org"),
        ("n@a.example", "n@a.example"),
        ("name@mail.sub-domain.example.org", "name@mail.sub-domain.example.org"),
        ("name@xn--brr-hoa.example", "name@xn--brr-hoa.example"),
    ],
)
def test_an_address_is_put_in_lower_case_and_nothing_else_of_it_is_changed(typed: str, made: str):
    assert regular(typed) == made


def test_a_full_stop_and_a_plus_are_part_of_an_address():
    # Some hosts of mail read these as one mailbox and some as two. Burro cannot know
    # which, so it never makes one account of two addresses.
    found = {regular(each) for each in ("ab@example.org", "a.b@example.org", "ab+c@example.org")}

    assert len(found) == 3 and None not in found


@pytest.mark.parametrize(
    "typed",
    [
        "",
        " ",
        "name",
        "@example.org",
        "name@",
        "name@example",
        "name@@example.org",
        "na me@example.org",
        "name@exam ple.org",
        ".name@example.org",
        "name.@example.org",
        "na..me@example.org",
        "name@.example.org",
        "name@example.org.",
        "name@-example.org",
        "name@example-.org",
        "name@example..org",
        "name@127.0.0.1",
        "name@[127.0.0.1]",
        '"na me"@example.org',
        "name@example.org, other@example.org",
        "Name <name@example.org>",
        "name@example.org\r\nBcc: other@example.org",
        "name@example.org\x00",
        "name\t@example.org",
        f"{'a' * (LONGEST_LOCAL + 1)}@example.org",
        f"name@{'a' * 64}.example",
        f"{'a' * 60}@{'b' * 60}.{'c' * 60}.{'d' * 60}.{'e' * 12}",
    ],
)
def test_what_is_not_in_the_shape_of_an_address_is_no_address(typed: str):
    assert regular(typed) is None


@pytest.mark.parametrize(
    "typed",
    [
        # Folded into plain letters, each would be the address of somebody else.
        "stra\N{LATIN SMALL LETTER SHARP S}e@example.org",
        "name@fa\N{LATIN SMALL LETTER SHARP S}.example",
        "n\N{LATIN SMALL LETTER A WITH DIAERESIS}me@example.org",
        "name@b\N{LATIN SMALL LETTER U WITH DIAERESIS}cher.example",
        "\N{FULLWIDTH LATIN SMALL LETTER A}@example.org",
        "name@example\N{FULLWIDTH FULL STOP}org",
        "name\N{ZERO WIDTH SPACE}@example.org",
        # Half of a pair, which no text holds and which cannot be written down.
        "name\ud800@example.org",
    ],
)
def test_an_address_that_is_not_in_plain_letters_is_refused_and_never_folded(typed: str):
    assert regular(typed) is None


def test_the_longest_address_is_taken_and_one_longer_is_not():
    domain = f"{'b' * 63}.{'c' * 63}.{'d' * 61}"
    longest = f"{'a' * LONGEST_LOCAL}@{domain}"
    assert len(longest) == LONGEST

    assert regular(longest) == longest
    assert regular(f"{'a' * LONGEST_LOCAL}@e{domain}") is None


def test_nothing_is_raised_whatever_is_typed():
    for typed in (CANARY, "\x00" * 300, "@" * 300, "a@" + "b." * 200 + "c", "\udfff"):
        assert regular(typed) is None
