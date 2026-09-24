"""A file asked for a piece at a time: each piece is the bytes asked for, of one file.

The publisher is a stand-in on the loopback address, and every file is made
up. A connection to any other address is blocked, so a test that reached a
real host would fail.
"""

from collections.abc import Iterator

import pytest
from burro_pipeline.fetch.download import DownloadRefused, InPieces, Limits, Reason, user_agent

from . import pieces_support
from .support import ONLY_LOOPBACK, Answer, Served, serving

pytestmark = ONLY_LOOPBACK

BODY = bytes(range(256)) * 40
AGENT = user_agent("data@made-up.example")
LIMITS = Limits(max_bytes=1_000_000, connect_seconds=2, read_seconds=2, total_seconds=5)


@pytest.fixture
def publisher() -> pieces_support.InPieces:
    return pieces_support.InPieces(BODY)


@pytest.fixture
def served(publisher: pieces_support.InPieces) -> Iterator[Served]:
    with serving(publisher) as server:
        yield server


def asked(served: Served, limits: Limits = LIMITS, path: str = "/files/places.parquet") -> InPieces:
    return InPieces(f"{served.address}{path}", limits, agent=AGENT, loopback_for_tests=True)


def a_piece(file: InPieces, first: int, count: int) -> bytes:
    held = bytearray()
    file.piece(first, count, held.extend)
    return bytes(held)


def refused(file: InPieces, first: int, count: int) -> DownloadRefused:
    held = bytearray()
    with pytest.raises(DownloadRefused) as caught:
        file.piece(first, count, held.extend)
    return caught.value


def test_the_end_of_a_file_arrives_with_the_size_of_the_whole(served: Served):
    file = asked(served)
    assert file.end(8) == BODY[-8:]
    assert file.of_bytes == len(BODY)
    assert file.final_url == f"{served.address}/files/places.parquet"
    assert file.file_name == "places.parquet"
    assert file.arrived == 8


def test_a_piece_arrives_byte_for_byte(served: Served):
    file = asked(served)
    assert a_piece(file, 0, 4) == BODY[:4]
    assert a_piece(file, 1_000, 5_000) == BODY[1_000:6_000]
    assert a_piece(file, len(BODY) - 1, 1) == BODY[-1:]
    assert file.arrived == 5_005


def test_each_piece_is_one_request_that_names_its_bytes_and_carries_no_login(served: Served):
    file = asked(served)
    file.end(8)
    a_piece(file, 4, 96)
    end, piece = served.seen
    assert (end.method, end.headers["range"]) == ("GET", "bytes=-8")
    assert (piece.method, piece.headers["range"]) == ("GET", "bytes=4-99")
    for request in served.seen:
        assert request.headers["accept-encoding"] == "identity"
        assert request.headers["user-agent"] == "Burro-fetch/1 (data@made-up.example)"
        assert "authorization" not in request.headers and "cookie" not in request.headers


def test_a_publisher_that_answers_with_the_whole_file_is_not_read(
    publisher: pieces_support.InPieces, served: Served
):
    publisher.gives_pieces = False
    file = asked(served)
    with pytest.raises(DownloadRefused) as caught:
        file.end(8)
    assert caught.value.reason is Reason.NOT_IN_PIECES
    assert file.arrived == 0


@pytest.mark.parametrize(
    "said",
    [
        None,
        "bytes 0-3/10240",
        "bytes 100-198/10240",
        "bytes 100-199/*",
        "bytes 100-199",
        "items 100-199/10240",
        "bytes 100-199/150",
        f"bytes 100-199/{'9' * 30}",
    ],
    ids=[
        "nothing",
        "other bytes",
        "fewer",
        "no size",
        "no whole",
        "no bytes",
        "past the end",
        "long",
    ],
)
def test_a_piece_that_is_not_said_to_be_the_bytes_asked_for_is_refused(
    publisher: pieces_support.InPieces, served: Served, said: str | None
):
    headers = {} if said is None else {"Content-Range": said}
    publisher.instead[0] = Answer(206, headers, BODY[100:200])
    assert refused(asked(served), 100, 100).reason is Reason.NOT_IN_PIECES


def test_a_piece_that_holds_more_or_fewer_bytes_than_it_says_is_refused(
    publisher: pieces_support.InPieces, served: Served
):
    said = {"Content-Range": f"bytes 100-199/{len(BODY)}"}
    publisher.instead[0] = Answer(206, {**said, "Content-Length": "100"}, BODY[100:200], 60)
    assert refused(asked(served), 100, 100).reason is Reason.CUT_SHORT
    publisher.instead[1] = Answer(206, {**said, "Content-Length": "101"}, BODY[100:201])
    assert refused(asked(served), 100, 100).reason is Reason.NOT_IN_PIECES
    publisher.instead[2] = Answer(206, {**said, "Transfer-Encoding": "chunked"}, BODY[100:300])
    assert refused(asked(served), 100, 100).reason is Reason.NOT_IN_PIECES


def test_each_later_piece_is_asked_of_the_version_the_first_was_of(served: Served):
    file = asked(served)
    file.end(8)
    a_piece(file, 0, 4)
    first, later = served.seen
    assert "if-match" not in first.headers
    assert later.headers["if-match"] == '"made-up-1"'


def test_a_file_that_changes_while_it_is_taken_is_refused(
    publisher: pieces_support.InPieces, served: Served
):
    publisher.then[1] = (BODY[::-1], '"made-up-2"')
    file = asked(served)
    file.end(8)
    assert refused(file, 0, 4).reason is Reason.CHANGED


def test_a_file_of_another_size_is_another_file_though_nothing_marks_it(
    publisher: pieces_support.InPieces, served: Served
):
    publisher.mark = None
    publisher.then[1] = (BODY + b"more", None)
    file = asked(served)
    file.end(8)
    assert "if-match" not in served.seen[0].headers
    assert refused(file, 0, 4).reason is Reason.CHANGED


@pytest.mark.parametrize("mark", ['W/"weak"', "no-quotes", '"two" "marks"', '"line\r\nX-More: 1"'])
def test_a_mark_that_does_not_tell_two_versions_apart_is_not_sent_back(
    publisher: pieces_support.InPieces, served: Served, mark: str
):
    publisher.instead[0] = Answer(
        206, {"Content-Range": f"bytes 0-3/{len(BODY)}", "ETag": mark.split("\r")[0]}, BODY[:4]
    )
    file = asked(served)
    a_piece(file, 0, 4)
    publisher.mark = None
    a_piece(file, 4, 4)
    assert "if-match" not in served.seen[1].headers


def test_pieces_that_come_to_more_than_the_size_stated_are_refused_before_they_are_asked_for(
    served: Served,
):
    file = asked(served, Limits(max_bytes=100, connect_seconds=2, read_seconds=2))
    a_piece(file, 0, 60)
    assert refused(file, 60, 41).reason is Reason.TOO_LARGE
    assert len(served.seen) == 1
    assert a_piece(file, 60, 40) == BODY[60:100]


@pytest.mark.parametrize("status", [404, 403, 416, 500])
def test_a_status_that_is_no_piece_is_said_as_it_is(
    publisher: pieces_support.InPieces, served: Served, status: int
):
    publisher.instead[0] = Answer(status, body=b"not here")
    error = refused(asked(served), 0, 4)
    assert (error.reason, error.detail) == (Reason.STATUS, str(status))


def test_a_piece_past_the_end_of_the_file_is_refused(served: Served):
    error = refused(asked(served), len(BODY), 4)
    assert (error.reason, error.detail) == (Reason.STATUS, "416")
    assert refused(asked(served), len(BODY) - 2, 4).reason is Reason.NOT_IN_PIECES


def test_a_piece_of_no_bytes_is_never_asked_for(served: Served):
    file = asked(served)
    assert refused(file, 0, 0).reason is Reason.NOT_IN_PIECES
    assert refused(file, -1, 4).reason is Reason.NOT_IN_PIECES
    assert served.seen == []


def test_a_redirect_on_the_same_host_is_followed_for_every_piece(
    publisher: pieces_support.InPieces, served: Served
):
    publisher.instead[0] = Answer(302, {"Location": "/files/moved.parquet"})
    publisher.instead[2] = Answer(302, {"Location": "/files/moved.parquet"})
    file = asked(served)
    file.end(8)
    assert a_piece(file, 0, 4) == BODY[:4]
    assert file.final_url == f"{served.address}/files/moved.parquet"
    assert [request.headers["range"] for request in served.seen] == [
        "bytes=-8",
        "bytes=-8",
        "bytes=0-3",
        "bytes=0-3",
    ]


def test_a_piece_that_comes_from_another_address_than_the_first_is_refused(
    publisher: pieces_support.InPieces, served: Served
):
    publisher.instead[1] = Answer(302, {"Location": "/files/another.parquet"})
    file = asked(served)
    file.end(8)
    assert refused(file, 0, 4).reason is Reason.CHANGED


def test_a_redirect_to_another_host_is_refused_and_that_host_is_never_asked(
    publisher: pieces_support.InPieces, served: Served
):
    with serving(pieces_support.InPieces(BODY)) as other:
        publisher.instead[0] = Answer(302, {"Location": f"{other.address}/places.parquet"})
        error = refused(asked(served), 0, 4)
        assert other.seen == []
    assert error.reason is Reason.REDIRECT_ELSEWHERE


def test_a_publisher_that_is_too_slow_is_given_up_on(
    publisher: pieces_support.InPieces, served: Served
):
    said = {"Content-Range": f"bytes 0-{len(BODY) - 1}/{len(BODY)}"}
    publisher.instead[0] = Answer(206, said, BODY, seconds_a_piece=0.2, piece=1_000)
    limits = Limits(max_bytes=1_000_000, connect_seconds=2, read_seconds=2, total_seconds=0.5)
    assert refused(asked(served, limits), 0, len(BODY)).reason is Reason.TIMED_OUT


def test_an_address_that_is_not_public_is_never_asked(served: Served):
    file = InPieces(f"{served.address}/files/places.parquet", LIMITS, agent=AGENT)
    with pytest.raises(DownloadRefused) as caught:
        file.end(8)
    assert caught.value.reason is Reason.NOT_HTTPS
    assert served.seen == []


def test_the_size_of_a_file_is_not_known_before_a_piece_of_it_has_arrived(served: Served):
    file = asked(served)
    with pytest.raises(DownloadRefused):
        _ = file.of_bytes
    with pytest.raises(DownloadRefused):
        _ = file.final_url


def test_a_refusal_repeats_nothing_the_publisher_said(
    publisher: pieces_support.InPieces, served: Served
):
    publisher.instead[0] = Answer(
        206, {"Content-Range": "bytes zzyzx-parva/canary", "ETag": '"zzyzx"'}, b"zzyzx parva"
    )
    error = refused(asked(served), 0, 4)
    assert "zzyzx" not in str(error).lower() and "127.0.0.1" not in str(error)
