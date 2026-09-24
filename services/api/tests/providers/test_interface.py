"""The interface the adapters are built to is the one the reader knows.

A client, a reply and four failures are defined once, in
`providers/interface.py`, so that an adapter needs nothing of the reader. The
reader imports them. This holds the two to the very same names. It needs the
reader, and is skipped, and says so, while the engine under the reader cannot
be loaded.
"""

import dataclasses
import inspect
from typing import Any

import pytest
from burro_api.providers import interface
from burro_api.providers.interface import ModelClient, ModelFailure, ModelReply

from .cases import ANSWER, CASES, Case, answering

FAILURES = ("ModelFailure", "ModelTimeout", "ModelCapped", "ModelRefused", "ModelError")


def _added(failure: type[BaseException]) -> set[str]:
    own: dict[str, object] = dict(vars(failure))
    return set(own) - {
        "__doc__",
        "__module__",
        "__weakref__",
        "__firstlineno__",
        "__static_attributes__",
    }


@pytest.fixture(scope="module")
def reader() -> Any:
    try:
        import burro_api.reader as found
    except ImportError:
        pytest.skip("the reader cannot be loaded: the engine under it is being rebuilt")
    return found


def test_there_are_four_failures_and_each_is_a_failure_of_the_model():
    for name in FAILURES[1:]:
        failure = getattr(interface, name)

        assert failure.__bases__ == (ModelFailure,)
        assert str(failure()) == "" and failure().args == ()
    assert ModelFailure.__bases__ == (Exception,)


def test_a_reply_shows_its_counts_and_never_its_words():
    reply = ModelReply(output=ANSWER, input_tokens=9, output_tokens=87, cache_read_tokens=0)

    assert repr(reply) == "ModelReply(input_tokens=9, output_tokens=87, cache_read_tokens=0)"
    with pytest.raises(dataclasses.FrozenInstanceError):
        reply.output = ""  # type: ignore[misc]


@pytest.mark.parametrize("case", CASES, ids=str)
def test_each_adapter_is_a_client_as_the_interface_describes_one(case: Case):
    client: ModelClient = case.made(answering(case.whole(ANSWER)))

    wanted = inspect.signature(ModelClient.complete)
    given = inspect.signature(type(client).complete)
    assert list(given.parameters) == list(wanted.parameters)
    assert [p.kind for p in given.parameters.values()] == [
        p.kind for p in wanted.parameters.values()
    ]
    assert [p.default for p in given.parameters.values()] == [
        p.default for p in wanted.parameters.values()
    ]


def test_the_failures_are_the_readers_in_name_and_in_kind(reader: Any):
    for name in FAILURES:
        ours: Any = getattr(interface, name)
        theirs: Any = getattr(reader, name)

        assert [base.__name__ for base in ours.__mro__] == [
            base.__name__ for base in theirs.__mro__
        ]
        # Neither adds anything to a plain exception but what it is called.
        assert _added(ours) == _added(theirs) == set()


def test_the_reply_is_the_readers_field_for_field(reader: Any):
    def shape(reply: Any) -> list[tuple[str, object, bool]]:
        return [(held.name, held.type, held.repr) for held in dataclasses.fields(reply)]

    assert shape(ModelReply) == shape(reader.ModelReply)
    assert dataclasses.is_dataclass(reader.ModelReply)
    assert ModelReply.__dataclass_params__.frozen == reader.ModelReply.__dataclass_params__.frozen  # type: ignore[attr-defined]


def test_the_client_is_the_readers_argument_for_argument(reader: Any):
    ours = inspect.signature(ModelClient.complete)
    theirs = inspect.signature(reader.ModelClient.complete)

    assert [(p.name, p.kind, str(p.annotation)) for p in ours.parameters.values()] == [
        (p.name, p.kind, str(p.annotation)) for p in theirs.parameters.values()
    ]


def test_the_reader_and_the_adapters_know_the_very_same_failures(reader: Any):
    # The reader imports the interface, so the route counts an adapter's
    # timeout as a timeout and its cap as a cap.
    for name in (*FAILURES, "ModelReply", "ModelClient"):
        assert getattr(reader, name) is getattr(interface, name)
