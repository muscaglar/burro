"""A body that says it is longer than any number can be read is refused as too large.

A body is refused by its headers before anything reads it. Its length was read
as a number, and a number of more than 4,300 figures is one that is not read
at all: what read it raised, the request was answered 500, and a failure was
written to the log. The server the service is run on refuses such a length
itself, so this was met behind any other server, and by whoever asks the app
with none before it.

A length of more figures than the longest body has is longer than it, whatever
the figures are, and is refused as any body is that is too large.
"""

import pytest
from burro_api.wire import MAX_BODY_BYTES

from .support import watching

BODY = b'{"text": "leafy", "ask_model": false}'
# As many figures as are read as a number, one more, and many more.
FIGURES = [len(str(MAX_BODY_BYTES)) + 1, 21, 4300, 4301, 5000, 100_000]


def headers(length: str) -> dict[str, str]:
    return {"content-type": "application/json", "content-length": length}


@pytest.mark.parametrize("figures", FIGURES)
@pytest.mark.parametrize("figure", ["9", "1"])
def test_a_length_of_many_figures_is_refused_as_too_large_and_is_no_failure(
    figures: int, figure: str
):
    with watching() as seen:
        response = seen.send(
            "POST", "/v1/interpret", content=BODY, headers=headers(figure * figures)
        )

        assert response.status_code == 413
        assert response.json()["error"]["code"] == "body_too_large"
        assert response.headers["x-burro-synthetic"] == "true"
        [line] = seen.events("request")
        assert (line["status"], line["error_code"]) == (413, "body_too_large")
        assert seen.events("failure") == []


@pytest.mark.parametrize("noughts", [1, 20, 4300, 5000])
def test_a_length_that_is_written_with_noughts_before_it_is_read_as_the_number_it_is(
    noughts: int,
):
    with watching() as seen:
        length = "0" * noughts + str(len(BODY))
        response = seen.send("POST", "/v1/interpret", content=BODY, headers=headers(length))
        too_long = "0" * noughts + str(MAX_BODY_BYTES + 1)
        refused = seen.send("POST", "/v1/interpret", content=BODY, headers=headers(too_long))

        assert response.status_code == 200
        assert (refused.status_code, refused.json()["error"]["code"]) == (413, "body_too_large")
        assert seen.events("failure") == []


def test_a_length_of_the_most_a_body_may_be_is_not_refused_for_its_length():
    with watching() as seen:
        most = seen.send(
            "POST", "/v1/interpret", content=BODY, headers=headers(str(MAX_BODY_BYTES))
        )
        over = seen.send(
            "POST", "/v1/interpret", content=BODY, headers=headers(str(MAX_BODY_BYTES + 1))
        )

        assert most.status_code == 200
        assert over.status_code == 413
