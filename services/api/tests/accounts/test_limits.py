"""How many times one client may ask, and how the address of a client is held.

Every address here is one that is set aside for writing about, and is nobody's.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from burro_api.accounts.limits import UNKNOWN, Limiter, NotOne, client_of

KEY = b"k" * 32
QUARTER = timedelta(minutes=15)
NOON = datetime(2026, 9, 26, 12, 0, 0, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.at = NOON

    def now(self) -> datetime:
        return self.at

    def pass_(self, **time: float) -> None:
        self.at += timedelta(**time)


def limiter(clock: Clock, most: int = 10, keep: int = 1_000, key: bytes = KEY) -> Limiter:
    return Limiter(key, most, QUARTER, clock.now, keep=keep)


# The address of a client.


@pytest.mark.parametrize(
    ("given", "client"),
    [
        (["192.0.2.7"], "192.0.2.7"),
        ([" 192.0.2.7 "], "192.0.2.7"),
        (["2001:db8:1:2:3:4:5:6"], "2001:db8:1:2::/64"),
        (["2001:DB8:1:2::1"], "2001:db8:1:2::/64"),
        # An address of the older kind, written as one of the newer.
        (["::ffff:192.0.2.7"], "192.0.2.7"),
    ],
)
def test_the_address_of_a_client_is_made_regular(given: list[str], client: str):
    assert client_of(given) == client


def test_a_client_has_the_whole_of_a_network_of_the_newer_kind():
    # One home or one phone is given a network of them, and may ask from any.
    one = client_of(["2001:db8:1:2::1"])
    same = client_of(["2001:db8:1:2:ffff:ffff:ffff:ffff"])
    other = client_of(["2001:db8:1:3::1"])

    assert one == same != other


@pytest.mark.parametrize(
    "given",
    [
        [],
        [""],
        ["unknown"],
        ["192.0.2"],
        ["192.0.2.7:443"],
        ["999.0.2.7"],
        ["192.0.2.7/24"],
        ["example.org"],
        ["x" * 5_000],
        ["192.0.2.7\r\nX-Other: 1"],
    ],
)
def test_an_address_that_cannot_be_read_is_counted_with_every_other_that_cannot(given: list[str]):
    # So what cannot be read is limited the more, and never the less.
    assert client_of(given) == UNKNOWN


@pytest.mark.parametrize(
    "given",
    [
        ["192.0.2.7", "198.51.100.9"],
        ["192.0.2.7", "192.0.2.7"],
        ["192.0.2.7, 198.51.100.9"],
        ["198.51.100.9,192.0.2.7"],
        ["", "192.0.2.7"],
    ],
)
def test_more_than_one_address_is_no_address_the_website_gave(given: list[str]):
    # The website puts in one, and first takes out what the client sent. Two of them
    # say that it did not, and then neither can be believed.
    with pytest.raises(NotOne):
        client_of(given)


# The count.


def test_so_many_are_let_in_within_the_time_and_no_more():
    clock = Clock()
    counted = limiter(clock)

    assert [counted.lets_in("192.0.2.7") for _ in range(12)] == [True] * 10 + [False] * 2


def test_the_time_runs_from_each_call_and_not_from_the_first():
    clock = Clock()
    counted = limiter(clock, most=2)
    assert counted.lets_in("192.0.2.7")
    clock.pass_(minutes=10)
    assert counted.lets_in("192.0.2.7") and not counted.lets_in("192.0.2.7")

    clock.pass_(minutes=5)
    # The first is a quarter of an hour old and counts no more. The second still does.
    assert counted.lets_in("192.0.2.7") and not counted.lets_in("192.0.2.7")
    clock.pass_(minutes=9, seconds=59)
    assert not counted.lets_in("192.0.2.7")
    clock.pass_(seconds=1)
    assert counted.lets_in("192.0.2.7")


def test_a_call_that_is_turned_away_is_not_counted():
    clock = Clock()
    counted = limiter(clock, most=1)
    assert counted.lets_in("192.0.2.7")
    for _ in range(50):
        clock.pass_(seconds=10)
        assert not counted.lets_in("192.0.2.7")

    clock.pass_(minutes=7)
    assert counted.lets_in("192.0.2.7")


def test_one_client_is_not_counted_with_another():
    clock = Clock()
    counted = limiter(clock, most=1)

    assert counted.lets_in("192.0.2.7") and counted.lets_in("192.0.2.8")
    assert not counted.lets_in("192.0.2.7") and not counted.lets_in("192.0.2.8")


def test_a_clock_that_is_put_back_lets_no_more_in():
    clock = Clock()
    counted = limiter(clock, most=1)
    assert counted.lets_in("192.0.2.7")

    clock.pass_(hours=-3)

    assert not counted.lets_in("192.0.2.7")


def test_the_count_holds_where_many_come_at_once():
    clock = Clock()
    counted = limiter(clock, most=25)

    def asks(_: int) -> bool:
        return counted.lets_in("192.0.2.7")

    with ThreadPoolExecutor(max_workers=16) as pool:
        let_in = list(pool.map(asks, range(400)))

    assert let_in.count(True) == 25


# What is held.


def test_what_is_held_of_a_client_is_a_hash_under_a_key_and_never_the_address():
    clock = Clock()
    counted = limiter(clock)
    for address in ("192.0.2.7", "2001:db8:1:2::/64", UNKNOWN):
        counted.lets_in(address)

    held = repr(vars(counted))

    for address in ("192.0.2.7", "192.0.2", "2001:db8", UNKNOWN):
        assert address not in held
    assert counted.held() == 3
    # Nor the key, which is what keeps a guess at an address from being confirmed.
    assert "kkkk" not in held and repr(KEY) not in held
    assert "192.0.2.7" not in repr(counted) and "kkkk" not in repr(counted)


def test_under_another_key_the_same_address_is_held_as_something_else():
    clock = Clock()
    one, other = limiter(clock, key=b"a" * 32), limiter(clock, key=b"b" * 32)
    one.lets_in("192.0.2.7")
    other.lets_in("192.0.2.7")

    assert one.names() != other.names()
    assert all(len(name) == 32 for name in (*one.names(), *other.names()))


def test_a_key_that_is_too_short_is_no_key():
    with pytest.raises(ValueError, match="too short") as refused:
        Limiter(b"short-key", 10, QUARTER, Clock().now)

    assert "short-key" not in str(refused.value)


def test_what_is_too_old_is_let_go_of_as_others_are_counted():
    clock = Clock()
    counted = limiter(clock, keep=50)
    for number in range(40):
        counted.lets_in(f"192.0.2.{number}")
    assert counted.held() == 40

    clock.pass_(minutes=16)
    for number in range(40, 60):
        counted.lets_in(f"192.0.2.{number}")

    # The forty are a quarter of an hour old, and were let go of when the room ran out.
    assert counted.held() <= 20


def test_no_more_clients_are_held_than_there_is_room_for():
    clock = Clock()
    counted = limiter(clock, most=1, keep=100)

    for number in range(1_000):
        clock.pass_(seconds=0.1)
        counted.lets_in(f"198.51.{number // 250}.{number % 250}")

    assert counted.held() <= 100
    # The newest are the ones that are held, so the newest are still held to the limit.
    assert not counted.lets_in("198.51.3.249")
