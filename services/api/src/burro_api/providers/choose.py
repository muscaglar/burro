"""Which provider reads what a person types, if any. Decided once, when the service starts.

A key alone turns nothing on. A model reads what is typed only when all of
these agree:

1. `BURRO_MODEL_PROVIDER` names one of the four providers. There is no default.
2. That provider's key is in the environment, and is fit to go in a header.
3. `BURRO_MODEL_TERMS_ACCEPTED` names the same provider: whoever runs the
   service has read its terms and taken them on.
4. The model is one whose request was read in the provider's documents.
   `BURRO_MODEL_ID` names it, or the table does.
5. The provider is one that may read what real people type. DeepSeek is
   not: its adapter is for the made-up sentences of the evaluation set.

Nothing waits on a person's check of the table in `terms.py` (ADR 0023).

Otherwise the rules read what is typed, and one line is logged that says
which provider is not used and which of these does not hold. Both are words
of ours. Nothing that was set is ever logged: a value in the wrong variable
could be a key.

What is sent is decided here too. The words go alone unless
`BURRO_MODEL_SENDS_SETTINGS` is the one word `yes`. Then the search settings
go with them, without where a journey leads.

`choose` also says what people are to be told, so that what the meta route
serves is decided in the same place as who receives the words and what goes
with them. They cannot be parted: a `Choice` that holds an adapter and tells
people that no model reads their words cannot be made, and nor can one that
sends the settings and tells people that the words go alone.
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
from burro_api.providers.terms import RULES_NOTICE, TERMS, Provider, Terms

PROVIDER_VARIABLE = "BURRO_MODEL_PROVIDER"
ACCEPTED_VARIABLE = "BURRO_MODEL_TERMS_ACCEPTED"
MODEL_VARIABLE = "BURRO_MODEL_ID"
SETTINGS_VARIABLE = "BURRO_MODEL_SENDS_SETTINGS"
# The one word that sends the search settings with the words. Any other
# value, and none, sends the words alone.
SENDS_SETTINGS = "yes"

ADAPTERS: Mapping[Provider, type[Adapter]] = {
    Provider.GEMINI: GeminiClient,
    Provider.OPENAI: OpenAIClient,
    Provider.DEEPSEEK: DeepSeekClient,
    Provider.ANTHROPIC: AnthropicClient,
}

# The providers the service never sends what people type to, whatever is set.
NOT_FOR_PEOPLE = frozenset({Provider.DEEPSEEK})

# The line that is written when something was set and no model is used.
NOT_USED = "model_not_used"
_NAMES = frozenset(provider.value for provider in Provider)


class Refusal(StrEnum):
    """Why no model is used though something was set.

    A fixed word, and never anything that was set. It is handed to whoever
    warns, and the line that is written holds it.
    """

    NO_PROVIDER = "no_provider"
    UNKNOWN_PROVIDER = "unknown_provider"
    NO_KEY = "no_key"
    UNFIT_KEY = "unfit_key"
    TERMS_NOT_ACCEPTED = "terms_not_accepted"
    UNFIT_MODEL = "unfit_model"
    NOT_FOR_PEOPLE = "not_for_people"


@dataclass(frozen=True)
class Told:
    """What the meta route says of who reads what is typed."""

    model_reads: bool
    # `None` when no model reads what is typed. Never an empty name.
    provider: str | None
    company: str | None
    notice: str
    # The company's own page of terms, for a link. `None` when no model reads.
    terms_url: str | None = None
    # Whether the search settings go to the provider with the words. Never
    # true where no model reads: nothing is sent then.
    settings_sent: bool = False


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
    # Whether the reader sends the search settings with the words.
    with_settings: bool = False

    def __post_init__(self) -> None:
        reads = self.client is not None
        # Text of our own, and nothing that was set.
        if self.told.model_reads is not reads or bool(self.model) is not reads:
            raise ValueError("what people are told does not fit who reads")
        if self.told.settings_sent is not self.with_settings or (self.with_settings and not reads):
            raise ValueError("what people are told does not fit what is sent")
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
    # Two words of two enums, so nothing that was set can stand in the line.
    # No provider is named where what was set names none of the four.
    named = {} if provider is None else {"provider": provider.value}
    logs.warning(NOT_USED, reason=refusal.value, **named)


def _named(env: Mapping[str, str], variable: str) -> str:
    return env.get(variable, "").strip().lower()


def told_of(terms: Terms, with_settings: bool) -> Told:
    """What people are told when `terms.provider` reads what they type."""
    return Told(
        model_reads=True,
        provider=terms.provider.value,
        company=terms.company,
        notice=terms.notice(with_settings),
        terms_url=terms.terms_url,
        settings_sent=with_settings,
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
    elif not ADAPTERS[provider].takes(model):
        refusal = Refusal.UNFIT_MODEL
    elif provider in NOT_FOR_PEOPLE:
        refusal = Refusal.NOT_FOR_PEOPLE
    else:
        with_settings = _named(env, SETTINGS_VARIABLE) == SENDS_SETTINGS
        told = told_of(terms, with_settings)
        chosen = Choice(ADAPTERS[provider](key, send), model, told, with_settings=with_settings)
        return chosen, provider
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
