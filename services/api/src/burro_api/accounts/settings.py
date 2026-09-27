"""What accounts are set to, read once from the environment as the service starts.

One setting turns accounts on, and they are off unless it says `on`. With them off
nothing else here is read, so a setting of accounts that is wrong cannot stop a service
that has none.

Three settings are secrets: what the website is known by, the key the addresses of
clients are counted under, and the key of the company that sends. Each comes from the
environment, is needed as the service starts where accounts are on, and is shown in no
`repr`, no dump and no line. A setting that is missing or is not in the form it needs
stops the service, which names the setting and never what it was set to.
"""

import re
from collections.abc import Mapping, Sequence
from enum import StrEnum
from pathlib import Path

from pydantic import Field, SecretStr

from burro_api.accounts.addresses import regular
from burro_api.wire import Wire

ON = "on"
OFF = "off"
YES = "yes"
NO = "no"
# The website in the clear, which is for development and for this machine alone.
IN_THE_CLEAR = "http://"
THIS_MACHINE = frozenset({"127.0.0.1", "::1", "localhost"})
# How many links the whole service may send in an hour, unless it is set otherwise. A
# first guess, and the founder's to confirm: each is a letter that is paid for, to an
# address that anybody typed.
DEFAULT_LINKS_PER_HOUR = 200
MOST_LINKS_PER_HOUR = 10_000

# A secret is 32 characters at the least, of those that may stand in a header.
_SECRET = re.compile(r"[\x21-\x7e]{32,512}")
_KEY = re.compile(r"[\x21-\x7e]{1,512}")
_WHOLE = re.compile(r"[0-9]{1,5}")
# A host, and perhaps a port, as they stand in an origin.
_HOST_OF = re.compile(r"https?://(\[[0-9a-f:]+\]|[^:/]+)(?::[0-9]+)?")


class SenderName(StrEnum):
    """Who sends a link. The first writes it to the console, and is for development."""

    CONSOLE = "console"
    POSTMARK = "postmark"
    RESEND = "resend"


class KeepRecent(StrEnum):
    """Whether a person's last searches are kept from the start, or once they turn it on.

    It is what stands for a person who has chosen neither. Whoever has chosen is kept
    to what they chose.
    """

    ASKED = "asked"
    FROM_THE_START = "from_the_start"


# The one line that chooses. It is the founder's to change, here or by the setting
# `BURRO_ACCOUNTS_KEEP_RECENT`.
KEEP_RECENT = KeepRecent.ASKED


class NotSet(Exception):
    """Settings of accounts are missing, or are not in the form they need.

    It names the settings, which are Burro's own words, and never what one was set to:
    a value in the wrong setting could be a secret.
    """

    def __init__(self, names: Sequence[str]) -> None:
        self.names = tuple(sorted(set(names)))
        super().__init__(", ".join(self.names))


class AccountsSettings(Wire):
    # The file accounts are kept in.
    database: Path
    # Where the website stands: the origin a link leads to, and the one a page asks from.
    site: str
    # That the service is being developed, on a machine that listens to itself alone.
    development: bool
    website_secret: SecretStr
    limits_key: SecretStr
    # `None` where no sender is named. Asking for a link is then answered 503.
    sender: SenderName | None
    sender_key: SecretStr | None
    sender_from: str | None
    links_per_hour: int = Field(ge=0, le=MOST_LINKS_PER_HOUR)
    keep_recent: KeepRecent

    @property
    def in_the_clear(self) -> bool:
        """Whether the website is reached with no TLS, which only development allows."""
        return self.site.startswith(IN_THE_CLEAR)


def _said(env: Mapping[str, str], name: str) -> str:
    return env.get(name, "").strip()


def _one_of[T: StrEnum](
    env: Mapping[str, str], name: str, words: type[T], wrong: list[str]
) -> T | None:
    said = _said(env, name).lower()
    if not said:
        return None
    if said not in {word.value for word in words}:
        wrong.append(name)
        return None
    return words(said)


def _secret(env: Mapping[str, str], name: str, wrong: list[str]) -> SecretStr:
    # Not stripped: a space at the end of a secret is a fault, and not one to mend quietly.
    said = env.get(name, "")
    if _SECRET.fullmatch(said) is None:
        wrong.append(name)
    return SecretStr(said)


def _whether(env: Mapping[str, str], name: str, wrong: list[str]) -> bool:
    said = _said(env, name).lower()
    if said not in ("", YES, NO):
        wrong.append(name)
    return said == YES


def _links_per_hour(env: Mapping[str, str], wrong: list[str]) -> int:
    name = "BURRO_ACCOUNTS_LINKS_PER_HOUR"
    said = _said(env, name)
    if not said:
        return DEFAULT_LINKS_PER_HOUR
    if _WHOLE.fullmatch(said) is None or int(said) > MOST_LINKS_PER_HOUR:
        wrong.append(name)
        return 0
    return int(said)


def turned_on(env: Mapping[str, str]) -> bool:
    """Whether the one setting says `on`. Any word but `on` and `off` stops the service."""
    said = _said(env, "BURRO_ACCOUNTS").lower()
    if said not in ("", ON, OFF):
        # Left to mean off, a slip of the hand would leave accounts off and tell nobody.
        raise NotSet(["BURRO_ACCOUNTS"])
    return said == ON


def accounts_from(env: Mapping[str, str]) -> AccountsSettings | None:
    """What accounts are set to, or `None` where they are off.

    Every setting that is at fault is named at once, so that nobody mends one to be
    told of the next.
    """
    if not turned_on(env):
        return None
    wrong: list[str] = []
    for name in ("BURRO_ACCOUNTS_DB", "BURRO_ACCOUNTS_SITE"):
        if not _said(env, name):
            wrong.append(name)
    website = _secret(env, "BURRO_WEBSITE_SECRET", wrong)
    limits = _secret(env, "BURRO_ACCOUNTS_LIMITS_KEY", wrong)
    if not wrong and website.get_secret_value() == limits.get_secret_value():
        # One secret for two things is lost twice over when it is lost.
        wrong += ["BURRO_WEBSITE_SECRET", "BURRO_ACCOUNTS_LIMITS_KEY"]
    sender = _one_of(env, "BURRO_ACCOUNTS_SENDER", SenderName, wrong)
    key, sent_from = None, None
    if sender is not None and sender is not SenderName.CONSOLE:
        held = env.get("BURRO_ACCOUNTS_SENDER_KEY", "")
        if _KEY.fullmatch(held) is None:
            wrong.append("BURRO_ACCOUNTS_SENDER_KEY")
        key = SecretStr(held)
        sent_from = regular(_said(env, "BURRO_ACCOUNTS_SENDER_FROM"))
        # As it was set, and as it would be made regular: no name stands before it.
        if sent_from is None or sent_from != _said(env, "BURRO_ACCOUNTS_SENDER_FROM"):
            wrong.append("BURRO_ACCOUNTS_SENDER_FROM")
    keep = _one_of(env, "BURRO_ACCOUNTS_KEEP_RECENT", KeepRecent, wrong)
    development = _whether(env, "BURRO_ACCOUNTS_DEVELOPMENT", wrong)
    links = _links_per_hour(env, wrong)
    if wrong:
        raise NotSet(wrong)
    return AccountsSettings(
        database=Path(_said(env, "BURRO_ACCOUNTS_DB")),
        site=_said(env, "BURRO_ACCOUNTS_SITE"),
        development=development,
        website_secret=website,
        limits_key=limits,
        sender=sender,
        sender_key=key,
        sender_from=sent_from,
        links_per_hour=links,
        keep_recent=keep or KEEP_RECENT,
    )


def _on_this_machine(site: str) -> bool:
    found = _HOST_OF.fullmatch(site)
    return found is not None and found[1].strip("[]") in THIS_MACHINE


def held_to(accounts: AccountsSettings, host: str, origins: Sequence[str]) -> None:
    """Hold accounts to where the service listens and to whom it answers, or refuse them.

    What development allows is allowed only on a machine that listens to itself
    alone: the website in the clear, a cookie a page in the clear can be given, and a
    link that is written to the console.
    """
    wrong: list[str] = []
    if accounts.site not in origins:
        # A page of the website asks from the origin a link leads to, and no other.
        wrong += ["BURRO_ACCOUNTS_SITE", "BURRO_ALLOWED_ORIGINS"]
    if accounts.development and host not in THIS_MACHINE:
        wrong += ["BURRO_ACCOUNTS_DEVELOPMENT", "BURRO_HOST"]
    if accounts.in_the_clear and not (accounts.development and _on_this_machine(accounts.site)):
        wrong.append("BURRO_ACCOUNTS_SITE")
    if accounts.sender is SenderName.CONSOLE and not accounts.development:
        wrong += ["BURRO_ACCOUNTS_SENDER", "BURRO_ACCOUNTS_DEVELOPMENT"]
    if wrong:
        raise NotSet(wrong)
