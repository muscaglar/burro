"""Which provider reads what a person types, if any. Decided once, when the service starts.

A key alone turns nothing on. A model reads what is typed only when all of
these agree:

1. `BURRO_MODEL_PROVIDER` names one of the four providers. There is no default.
2. That provider's key is in the environment, and is fit to go in a header.
3. `BURRO_MODEL_TERMS_ACCEPTED` names the same provider: whoever runs the
   service has read its terms and taken them on.
4. A person has checked every sentence people are told about that provider
   against its source, and has written down who and when (`terms.py`). This
   is asked of all four alike, and as this was written none had been.
5. The model is one whose request was read in the provider's documents.
   `BURRO_MODEL_ID` names it, or the table does.

Otherwise the rules read what is typed, and one line is logged that holds the
provider's name and nothing else. Nothing that was set is ever logged: a
value in the wrong variable could be a key.

`choose` also says what people are to be told, so that what the meta route
serves is decided in the same place as who receives the words. The two
cannot be parted: a `Choice` that holds an adapter and tells people that no
model reads their words cannot be made.

Until `choose` is wired into the service, the service does not ask it. See
the warning at the head of `docs/design/models.md`.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from burro_api import logs
from burro_api.providers.anthropic import AnthropicClient
from burro_api.providers.base import Adapter, Key, Send, over_https
from burro_api.providers.deepseek import DeepSeekClient
from burro_api.providers.gemini import GeminiClient
from burro_api.providers.interface import ModelClient
from burro_api.providers.openai import OpenAIClient
from burro_api.providers.terms import RULES_NOTICE, TERMS, Provider, Question, Terms

PROVIDER_VARIABLE = "BURRO_MODEL_PROVIDER"
ACCEPTED_VARIABLE = "BURRO_MODEL_TERMS_ACCEPTED"
MODEL_VARIABLE = "BURRO_MODEL_ID"

ADAPTERS: Mapping[Provider, type[Adapter]] = {
    Provider.GEMINI: GeminiClient,
    Provider.OPENAI: OpenAIClient,
    Provider.DEEPSEEK: DeepSeekClient,
    Provider.ANTHROPIC: AnthropicClient,
}

# The line that is written when something was set and no model is used. Each
# name is fixed text. The list of what may be logged has no field for a
# provider, so until it has, the name of the event carries it.
NOT_USED = "model_not_used"
_NAMES = frozenset(provider.value for provider in Provider)
NOT_USED_BY = {provider: f"{NOT_USED}_{provider.value}" for provider in Provider}


class Refusal(StrEnum):
    """Why no model is used though something was set.

    A fixed word, and never anything that was set. It is handed to whoever
    warns. The line that is written today does not hold it, because the list
    of what may be logged has no field for it: `docs/design/models.md` says
    how to see it.
    """

    NO_PROVIDER = "no_provider"
    UNKNOWN_PROVIDER = "unknown_provider"
    NO_KEY = "no_key"
    UNFIT_KEY = "unfit_key"
    TERMS_NOT_ACCEPTED = "terms_not_accepted"
    TERMS_NOT_CHECKED = "terms_not_checked"
    UNFIT_MODEL = "unfit_model"


@dataclass(frozen=True)
class Source:
    """One sentence of the notice: which question it answers, and where the answer was read."""

    question: str
    says: str
    # False where the provider's documents, as read, do not answer the question.
    answered: bool
    addresses: tuple[str, ...]
    read_on: str
    checked_on: str | None


@dataclass(frozen=True)
class Told:
    """What the meta route says of who reads what is typed."""

    model_reads: bool
    # `None` when no model reads what is typed. Never an empty name.
    provider: str | None
    company: str | None
    notice: str
    sources: tuple[Source, ...] = ()


BY_RULES = Told(model_reads=False, provider=None, company=None, notice=RULES_NOTICE)


@dataclass(frozen=True)
class Choice:
    """Who reads, and what people are told of it. Neither has a default, and the two must agree."""

    # The adapter, or `None` for the rules. It holds the key, and shows none of it.
    client: ModelClient | None = field(repr=False)
    # The model to ask for. Empty when the rules read.
    model: str
    told: Told
    refusal: Refusal | None = None

    def __post_init__(self) -> None:
        reads = self.client is not None
        # Text of our own, and nothing that was set.
        if self.told.model_reads is not reads or bool(self.model) is not reads:
            raise ValueError("what people are told does not fit who reads")
        if reads and self.refusal is not None:
            raise ValueError("a model that was refused does not read")
        if isinstance(self.client, Adapter) and (
            self.told.provider not in _NAMES
            or ADAPTERS[Provider(self.told.provider)] is not type(self.client)
        ):
            raise ValueError("people are told of one provider while another reads")


def by_rules(refusal: Refusal | None = None) -> Choice:
    """The rules read, and people are told so."""
    return Choice(client=None, model="", told=BY_RULES, refusal=refusal)


Warn = Callable[[Provider | None, Refusal], None]


def _warn(provider: Provider | None, refusal: Refusal) -> None:
    # The provider's name and nothing else. Why is `refusal`, which the list
    # of what may be logged has no field for yet.
    del refusal
    logs.event(NOT_USED if provider is None else NOT_USED_BY[provider])


def _named(env: Mapping[str, str], variable: str) -> str:
    return env.get(variable, "").strip().lower()


def _source(terms: Terms, question: Question) -> Source:
    given = terms.answer(question)
    return Source(
        question=question.value,
        says=terms.says(question),
        answered=given.answered,
        addresses=given.addresses,
        read_on=given.read_on.isoformat(),
        checked_on=None if given.checked_on is None else given.checked_on.isoformat(),
    )


def told_of(terms: Terms) -> Told:
    """What people are told when `terms.provider` reads what they type."""
    return Told(
        model_reads=True,
        provider=terms.provider.value,
        company=terms.company,
        notice=terms.notice,
        sources=tuple(_source(terms, question) for question in Question),
    )


def _key(value: str) -> Key | None:
    try:
        return Key(value)
    except ValueError:
        return None


def _decided(
    env: Mapping[str, str], table: Mapping[Provider, Terms], send: Send
) -> tuple[Choice, Provider | None]:
    named = _named(env, PROVIDER_VARIABLE)
    if named not in _NAMES:
        refusal = Refusal.UNKNOWN_PROVIDER if named else Refusal.NO_PROVIDER
        return by_rules(refusal), None
    provider = Provider(named)
    terms = table[provider]
    held = env.get(terms.key_variable, "").strip()
    key = _key(held) if held else None
    model = env.get(MODEL_VARIABLE, "").strip() or terms.model
    if not held:
        refusal = Refusal.NO_KEY
    elif key is None:
        refusal = Refusal.UNFIT_KEY
    elif _named(env, ACCEPTED_VARIABLE) != named:
        refusal = Refusal.TERMS_NOT_ACCEPTED
    elif not terms.checked:
        refusal = Refusal.TERMS_NOT_CHECKED
    elif not ADAPTERS[provider].takes(model):
        refusal = Refusal.UNFIT_MODEL
    else:
        return Choice(ADAPTERS[provider](key, send), model, told_of(terms)), provider
    return by_rules(refusal), provider


def choose(
    env: Mapping[str, str],
    *,
    send: Send = over_https,
    table: Mapping[Provider, Terms] = TERMS,
    warn: Warn = _warn,
) -> Choice:
    """The adapter to use, or none, and what people are to be told.

    It reads the environment it is given and nothing else, makes no call, and
    never raises. With nothing set it is silent: that is the service as it
    runs on a fresh checkout.
    """
    watched = (PROVIDER_VARIABLE, ACCEPTED_VARIABLE, *(table[p].key_variable for p in table))
    if not any(env.get(variable, "").strip() for variable in watched):
        return by_rules()
    choice, provider = _decided(env, table, send)
    if choice.refusal is not None:
        warn(provider, choice.refusal)
    return choice
