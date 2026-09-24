"""One download: one request, no redirect to another host, a size limit and a time limit.

The publisher here is a stand-in on the loopback address, and every file is
made up. A connection to any other address is blocked, so a test that reached
a real host would fail.
"""

import hashlib
from collections.abc import Iterator
from pathlib import Path

import pytest
from burro_pipeline.fetch.download import (
    Downloaded,
    DownloadRefused,
    Limits,
    Reason,
    download,
    next_address,
    user_agent,
)

from .support import ONLY_LOOPBACK, Answer, Seen, Served, serving

pytestmark = ONLY_LOOPBACK

BODY = b"code,homes\n" + b"made-up,10\n" * 20_000
AGENT = user_agent("data@made-up.example")
LIMITS = Limits(max_bytes=1_000_000, connect_seconds=2, read_seconds=2, total_seconds=5)
# A made-up login, in an address that must be refused for holding one.
WITH_A_LOGIN = "https://user:word@made-up.example/homes.csv"  # public-only: allow


class Publisher:
    """Answers by path. A test fills `pages`."""

    def __init__(self) -> None:
        self.pages: dict[str, Answer] = {"/files/homes.csv": Answer(body=BODY)}

    def __call__(self, request: Seen) -> Answer:
        return self.pages.get(request.path, Answer(404, body=b"not here"))


@pytest.fixture
def publisher() -> Publisher:
    return Publisher()


@pytest.fixture
def served(publisher: Publisher) -> Iterator[Served]:
    with serving(publisher) as server:
        yield server


def fetch(
    served: Served,
    path: str,
    to: Path,
    limits: Limits = LIMITS,
    may_redirect_to: tuple[str, ...] = (),
) -> Downloaded:
    return download(
        f"{served.address}{path}",
        to,
        limits,
        agent=AGENT,
        may_redirect_to=may_redirect_to,
        loopback_for_tests=True,
    )


def refused(served: Served, path: str, to: Path, limits: Limits = LIMITS) -> DownloadRefused:
    with pytest.raises(DownloadRefused) as caught:
        fetch(served, path, to, limits)
    assert not to.exists()
    assert list(to.parent.iterdir()) == []
    return caught.value


@pytest.fixture
def to(tmp_path: Path) -> Path:
    folder = tmp_path / "down"
    folder.mkdir()
    return folder / "file"


def test_a_file_arrives_byte_for_byte_with_its_hash_and_size(served: Served, to: Path):
    got = fetch(served, "/files/homes.csv", to)
    assert to.read_bytes() == BODY
    assert (got.sha256, got.bytes) == (hashlib.sha256(BODY).hexdigest(), len(BODY))
    assert got.final_url == f"{served.address}/files/homes.csv"
    assert got.file_name == "homes.csv"


def test_a_file_is_asked_for_once_as_it_is_with_a_name_and_a_contact(served: Served, to: Path):
    fetch(served, "/files/homes.csv", to)
    (request,) = served.seen
    assert request.method == "GET"
    assert request.headers["accept-encoding"] == "identity"
    assert request.headers["user-agent"] == "Burro-fetch/1 (data@made-up.example)"
    assert "authorization" not in request.headers
    assert "cookie" not in request.headers


def test_the_publishers_name_for_the_file_is_kept(publisher: Publisher, served: Served, to: Path):
    publisher.pages["/download?id=7"] = Answer(
        headers={"Content-Disposition": 'attachment; filename="Table 1 (final).csv"'}, body=BODY
    )
    assert fetch(served, "/download?id=7", to).file_name == "Table 1 (final).csv"


def test_a_name_written_the_long_way_is_read(publisher: Publisher, served: Served, to: Path):
    publisher.pages["/download"] = Answer(
        headers={"Content-Disposition": "attachment; filename*=UTF-8''caf%C3%A9%20homes.csv"},
        body=BODY,
    )
    assert fetch(served, "/download", to).file_name == "café homes.csv"


def test_a_file_with_no_name_of_its_own_is_called_file(
    publisher: Publisher, served: Served, to: Path
):
    publisher.pages["/"] = Answer(body=BODY)
    assert fetch(served, "/", to).file_name == "file"


def test_a_redirect_on_the_same_host_is_followed(publisher: Publisher, served: Served, to: Path):
    publisher.pages["/latest"] = Answer(302, {"Location": "/files/homes.csv"})
    got = fetch(served, "/latest", to)
    assert got.final_url == f"{served.address}/files/homes.csv"
    assert [request.path for request in served.seen] == ["/latest", "/files/homes.csv"]


def test_a_redirect_to_another_host_is_refused_and_that_host_is_never_asked(
    publisher: Publisher, served: Served, to: Path
):
    with serving(lambda _: Answer(body=BODY)) as other:
        publisher.pages["/latest"] = Answer(302, {"Location": f"{other.address}/homes.csv"})
        error = refused(served, "/latest", to)
        assert other.seen == []
    assert error.reason is Reason.REDIRECT_ELSEWHERE
    assert error.detail == "127.0.0.1"


def test_a_redirect_to_a_named_host_is_refused_before_any_lookup(
    publisher: Publisher, served: Served, to: Path
):
    publisher.pages["/latest"] = Answer(
        301, {"Location": "https://cdn.made-up.example/homes.csv?sig=made-up-token"}
    )
    error = refused(served, "/latest", to)
    assert error.reason is Reason.REDIRECT_ELSEWHERE
    assert error.detail == "cdn.made-up.example"
    assert "made-up-token" not in str(error)


def test_a_redirect_to_a_host_the_list_allows_is_followed(
    publisher: Publisher, served: Served, to: Path
):
    with serving(lambda _: Answer(body=BODY)) as other:
        publisher.pages["/latest"] = Answer(302, {"Location": f"{other.address}/homes.csv"})
        got = fetch(served, "/latest", to, may_redirect_to=("127.0.0.1",))
        assert [request.path for request in other.seen] == ["/homes.csv"]
    assert got.bytes == len(BODY)


def test_a_chain_of_redirects_ends(publisher: Publisher, served: Served, to: Path):
    for step in range(10):
        publisher.pages[f"/step/{step}"] = Answer(302, {"Location": f"/step/{step + 1}"})
    error = refused(served, "/step/0", to)
    assert error.reason is Reason.TOO_MANY_REDIRECTS
    assert len(served.seen) == 6


def test_a_redirect_with_nowhere_to_go_is_refused(publisher: Publisher, served: Served, to: Path):
    publisher.pages["/latest"] = Answer(302)
    assert refused(served, "/latest", to).reason is Reason.BAD_ANSWER


@pytest.mark.parametrize(
    ("location", "allowed", "outcome"),
    [
        ("/other", (), "https://made-up.example/other"),
        ("other?x=1", (), "https://made-up.example/files/other?x=1"),
        ("https://made-up.example/other", (), "https://made-up.example/other"),
        ("https://MADE-UP.example:443/other", (), ":443/other"),
        ("http://made-up.example/other", (), Reason.REDIRECT_ELSEWHERE),
        ("https://made-up.example:8443/other", (), Reason.REDIRECT_ELSEWHERE),
        ("https://elsewhere.example/other", (), Reason.REDIRECT_ELSEWHERE),
        ("//elsewhere.example/other", (), Reason.REDIRECT_ELSEWHERE),
        ("https://elsewhere.example/other", ("elsewhere.example",), "elsewhere.example"),
        ("http://elsewhere.example/other", ("elsewhere.example",), Reason.REDIRECT_ELSEWHERE),
        (WITH_A_LOGIN, (), Reason.REDIRECT_ELSEWHERE),
        ("ftp://made-up.example/other", (), Reason.REDIRECT_ELSEWHERE),
        ("https://made-up.example.elsewhere.example/", (), Reason.REDIRECT_ELSEWHERE),
    ],
)
def test_where_a_redirect_may_lead(location: str, allowed: tuple[str, ...], outcome: str | Reason):
    """Worked out from text alone: no socket is opened."""
    start = "https://made-up.example/files/homes.csv"
    if isinstance(outcome, Reason):
        with pytest.raises(DownloadRefused) as caught:
            next_address(start, location, allowed)
        assert caught.value.reason is outcome
    else:
        assert outcome in next_address(start, location, allowed)


def test_a_file_that_says_it_is_too_large_is_refused_before_it_is_read(served: Served, to: Path):
    error = refused(served, "/files/homes.csv", to, Limits(max_bytes=len(BODY) - 1))
    assert error.reason is Reason.TOO_LARGE


def test_a_file_at_the_limit_is_taken(served: Served, to: Path):
    assert fetch(served, "/files/homes.csv", to, Limits(max_bytes=len(BODY))).bytes == len(BODY)


def test_a_file_that_does_not_say_its_size_is_stopped_at_the_limit(
    publisher: Publisher, served: Served, to: Path
):
    publisher.pages["/stream"] = Answer(headers={"Transfer-Encoding": "chunked"}, body=BODY)
    assert fetch(served, "/stream", to).bytes == len(BODY)
    to.unlink()
    error = refused(served, "/stream", to, Limits(max_bytes=100_000))
    assert error.reason is Reason.TOO_LARGE


def test_a_file_cut_short_is_refused(publisher: Publisher, served: Served, to: Path):
    publisher.pages["/cut"] = Answer(body=BODY, cut_short_at=1000)
    assert refused(served, "/cut", to).reason is Reason.CUT_SHORT


def test_a_publisher_that_stops_sending_is_given_up_on(
    publisher: Publisher, served: Served, to: Path
):
    publisher.pages["/slow"] = Answer(body=BODY, seconds_a_piece=0.5, piece=1000)
    limits = Limits(max_bytes=1_000_000, connect_seconds=1, read_seconds=0.05, total_seconds=5)
    assert refused(served, "/slow", to, limits).reason is Reason.TIMED_OUT


def test_a_publisher_that_sends_a_little_at_a_time_runs_out_of_time(
    publisher: Publisher, served: Served, to: Path
):
    publisher.pages["/drip"] = Answer(body=BODY, seconds_a_piece=0.02, piece=100)
    limits = Limits(max_bytes=1_000_000, connect_seconds=1, read_seconds=1, total_seconds=0.1)
    assert refused(served, "/drip", to, limits).reason is Reason.TIMED_OUT


@pytest.mark.parametrize("status", [204, 206, 304, 401, 403, 404, 429, 500, 503])
def test_anything_but_a_plain_yes_is_refused_with_its_status(
    publisher: Publisher, served: Served, to: Path, status: int
):
    publisher.pages["/answer"] = Answer(status, body=b"made-up page that is not the file")
    error = refused(served, "/answer", to)
    assert error.reason is Reason.STATUS
    assert error.detail == str(status)


def test_a_publisher_that_is_not_there_is_refused(to: Path):
    with serving(lambda _: Answer()) as gone:
        pass
    error = refused(gone, "/files/homes.csv", to)
    assert error.reason is Reason.NO_CONNECTION
    assert str(gone.port) not in str(error)


@pytest.mark.disable_socket
@pytest.mark.parametrize(
    ("address", "reason"),
    [
        ("http://made-up.example/homes.csv", Reason.NOT_HTTPS),
        ("ftp://made-up.example/homes.csv", Reason.NOT_HTTPS),
        ("file:///etc/hosts", Reason.NOT_HTTPS),
        ("made-up.example/homes.csv", Reason.NOT_HTTPS),
        (WITH_A_LOGIN, Reason.BAD_ADDRESS),
        ("https:///homes.csv", Reason.BAD_ADDRESS),
        ("https://made-up.example:notaport/homes.csv", Reason.BAD_ADDRESS),
        ("https://made up.example/homes.csv", Reason.BAD_ADDRESS),
        ("https://made-up.example/homes.csv\r\nX-Injected: 1", Reason.BAD_ADDRESS),
        ("https://127.0.0.1/homes.csv", Reason.NOT_PUBLIC),
        ("https://10.0.0.8/homes.csv", Reason.NOT_PUBLIC),
        ("https://169.254.169.254/latest/meta-data", Reason.NOT_PUBLIC),
        ("https://[::1]/homes.csv", Reason.NOT_PUBLIC),
        ("https://localhost/homes.csv", Reason.NOT_PUBLIC),
    ],
)
def test_an_address_that_may_not_be_asked_is_refused_with_no_socket_opened(
    to: Path, address: str, reason: Reason
):
    with pytest.raises(DownloadRefused) as caught:
        download(address, to, LIMITS, agent=AGENT)
    assert caught.value.reason is reason
    assert not to.exists()


def test_plain_http_to_the_loopback_address_is_for_tests_alone(served: Served, to: Path):
    with pytest.raises(DownloadRefused) as caught:
        download(f"{served.address}/files/homes.csv", to, LIMITS, agent=AGENT)
    assert caught.value.reason is Reason.NOT_HTTPS
    assert served.seen == []


def test_a_refusal_in_words_holds_the_reason_and_no_address(
    publisher: Publisher, served: Served, to: Path
):
    publisher.pages["/secret-path?token=made-up-token"] = Answer(500)
    error = refused(served, "/secret-path?token=made-up-token", to)
    assert str(error) == "status 500"
    assert error.__cause__ is None


@pytest.mark.parametrize("contact", ["", " ", "no-at-sign", "a@b\r\nX-Injected: 1", "a@b c"])
def test_a_contact_that_is_not_an_address_is_refused(contact: str):
    with pytest.raises(ValueError, match="BURRO_FETCH_CONTACT"):
        user_agent(contact)


def test_a_contact_may_be_a_page(to: Path):
    assert user_agent("https://made-up.example/contact") == (
        "Burro-fetch/1 (https://made-up.example/contact)"
    )
