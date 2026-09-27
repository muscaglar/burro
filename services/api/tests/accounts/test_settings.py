"""What accounts are set to: one setting turns them on, and the secrets are needed at start.

Every secret here is made up, and opens nothing.
"""

from pathlib import Path
from typing import Any

import pytest
from burro_api.accounts.settings import (
    DEFAULT_LINKS_PER_HOUR,
    AccountsSettings,
    KeepRecent,
    NotSet,
    SenderName,
    accounts_from,
    held_to,
)
from burro_api.settings import Settings

from ..support import CANARY

SECRET = f"website-secret-{CANARY}-0123456789abcdef"
LIMITS = f"limits-key-{CANARY}-0123456789abcdefgh"
SENDER_KEY = f"sender-key-{CANARY}"
SITE = "https://burro.example"
ON = {
    "BURRO_ACCOUNTS": "on",
    "BURRO_ACCOUNTS_DB": "/data/accounts.db",
    "BURRO_ACCOUNTS_SITE": SITE,
    "BURRO_WEBSITE_SECRET": SECRET,
    "BURRO_ACCOUNTS_LIMITS_KEY": LIMITS,
    "BURRO_ALLOWED_ORIGINS": SITE,
    "BURRO_HOST": "0.0.0.0",  # noqa: S104
}
AT_HOME = ON | {
    "BURRO_ACCOUNTS_SITE": "http://127.0.0.1:3381",
    "BURRO_ALLOWED_ORIGINS": "http://127.0.0.1:3381",
    "BURRO_ACCOUNTS_DEVELOPMENT": "yes",
    "BURRO_ACCOUNTS_SENDER": "console",
    "BURRO_HOST": "127.0.0.1",
}
WITH_A_COMPANY = ON | {
    "BURRO_ACCOUNTS_SENDER": "postmark",
    "BURRO_ACCOUNTS_SENDER_KEY": SENDER_KEY,
    "BURRO_ACCOUNTS_SENDER_FROM": "sign-in@burro.example",
}


def refused(env: dict[str, str]) -> tuple[str, ...]:
    with pytest.raises(NotSet) as found:
        Settings.from_env(env)
    # The names of the settings are Burro's own. What they were set to is never said.
    said = str(found.value) + repr(found.value) + repr(found.value.names)
    assert CANARY not in said
    for value in env.values():
        assert len(value) < 6 or value not in said, value
    return found.value.names


def on(env: dict[str, str]) -> AccountsSettings:
    found = Settings.from_env(env).accounts
    assert found is not None
    return found


# Off until it is turned on.


@pytest.mark.parametrize("set_to", [None, "", " ", "off", "OFF", " off "])
def test_accounts_are_off_unless_the_one_setting_says_on(set_to: str | None):
    env = {} if set_to is None else {"BURRO_ACCOUNTS": set_to}

    assert Settings.from_env(env).accounts is None
    assert accounts_from(env) is None


def test_with_accounts_off_nothing_else_of_them_is_read_or_held():
    rest = {name: value for name, value in WITH_A_COMPANY.items() if name != "BURRO_ACCOUNTS"}
    # Not even one that is wrong: what is off cannot stop the service.
    wrong = rest | {"BURRO_WEBSITE_SECRET": "short", "BURRO_ACCOUNTS_SENDER": CANARY}

    for env in (rest, wrong):
        settings = Settings.from_env(env)
        assert settings.accounts is None
        assert CANARY not in settings.model_dump_json() and CANARY not in repr(settings)


@pytest.mark.parametrize("set_to", ["yes", "true", "1", "On please", "enabled", CANARY])
def test_a_word_that_is_neither_on_nor_off_stops_the_service(set_to: str):
    # Left to mean off, a slip of the hand would leave accounts off and tell nobody.
    assert refused(ON | {"BURRO_ACCOUNTS": set_to}) == ("BURRO_ACCOUNTS",)


def test_one_setting_turns_accounts_on_and_the_rest_say_how():
    found = on(ON)

    assert found.database == Path("/data/accounts.db") and found.site == SITE
    assert found.development is False and found.sender is None
    assert found.links_per_hour == DEFAULT_LINKS_PER_HOUR == 200
    # Kept only once a person turns it on, unless the founder chooses otherwise.
    assert found.keep_recent is KeepRecent.ASKED


# The secrets.


def test_a_secret_is_held_and_is_shown_in_nothing():
    settings = Settings.from_env(WITH_A_COMPANY)
    found = settings.accounts
    assert found is not None

    assert found.website_secret.get_secret_value() == SECRET
    assert found.limits_key.get_secret_value() == LIMITS
    assert found.sender_key is not None and found.sender_key.get_secret_value() == SENDER_KEY
    for shown in (repr(settings), str(settings), settings.model_dump_json(), repr(found)):
        assert CANARY not in shown
    assert CANARY not in repr(settings.model_dump())


@pytest.mark.parametrize(
    "missing",
    [
        "BURRO_ACCOUNTS_DB",
        "BURRO_ACCOUNTS_SITE",
        "BURRO_WEBSITE_SECRET",
        "BURRO_ACCOUNTS_LIMITS_KEY",
    ],
)
def test_what_accounts_need_is_needed_at_start_and_is_named_where_it_is_missing(missing: str):
    env = {name: value for name, value in ON.items() if name != missing}

    assert missing in refused(env)
    assert missing in refused(env | {missing: " "})


def test_every_setting_that_is_missing_is_named_at_once():
    assert refused({"BURRO_ACCOUNTS": "on"}) == (
        "BURRO_ACCOUNTS_DB",
        "BURRO_ACCOUNTS_LIMITS_KEY",
        "BURRO_ACCOUNTS_SITE",
        "BURRO_WEBSITE_SECRET",
    )


@pytest.mark.parametrize("name", ["BURRO_WEBSITE_SECRET", "BURRO_ACCOUNTS_LIMITS_KEY"])
@pytest.mark.parametrize(
    "secret",
    [
        "short",
        # One character short of enough.
        f"{CANARY}-eighteen-chars-xx",
        f"a secret with a space in it {CANARY} that is long",
        f"a-secret-with-a-tab\t{CANARY}-that-is-long-enough",
        f"a-secret-that-is-not-in-plain-letters-{CANARY}-\N{LATIN SMALL LETTER E WITH ACUTE}",
        f"{CANARY}" * 60,
    ],
)
def test_a_secret_that_is_too_short_or_cannot_go_in_a_header_is_refused(name: str, secret: str):
    assert name in refused(ON | {name: secret})


def test_one_secret_is_not_used_for_two_things():
    names = refused(ON | {"BURRO_ACCOUNTS_LIMITS_KEY": SECRET})

    assert set(names) == {"BURRO_ACCOUNTS_LIMITS_KEY", "BURRO_WEBSITE_SECRET"}


# Where the website stands.


def test_the_website_is_one_of_the_origins_a_browser_may_call_from():
    elsewhere = ON | {"BURRO_ACCOUNTS_SITE": "https://other.example"}

    assert set(refused(elsewhere)) == {"BURRO_ACCOUNTS_SITE", "BURRO_ALLOWED_ORIGINS"}
    listed = ON | {"BURRO_ALLOWED_ORIGINS": f"https://staging.burro.example,{SITE}"}
    assert on(listed).site == SITE


@pytest.mark.parametrize(
    "site",
    ["http://burro.example", "http://127.0.0.1:3381", "http://localhost:3000"],
)
def test_a_link_is_never_to_a_website_in_the_clear_but_in_development(site: str):
    env = ON | {"BURRO_ACCOUNTS_SITE": site, "BURRO_ALLOWED_ORIGINS": site}

    assert "BURRO_ACCOUNTS_SITE" in refused(env)


def test_in_development_the_website_may_be_in_the_clear_on_this_machine_alone():
    assert on(AT_HOME).site == "http://127.0.0.1:3381"
    away = AT_HOME | {
        "BURRO_ACCOUNTS_SITE": "http://burro.example",
        "BURRO_ALLOWED_ORIGINS": "http://burro.example",
    }
    assert "BURRO_ACCOUNTS_SITE" in refused(away)


# Development.


@pytest.mark.parametrize("host", ["0.0.0.0", "192.0.2.7", "burro.example", "::"])  # noqa: S104
def test_the_service_is_in_development_only_where_it_listens_to_this_machine_alone(host: str):
    names = refused(AT_HOME | {"BURRO_HOST": host})

    assert set(names) == {"BURRO_ACCOUNTS_DEVELOPMENT", "BURRO_HOST"}


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
def test_this_machine_alone_is_the_loopback_address(host: str):
    assert on(AT_HOME | {"BURRO_HOST": host}).development is True


@pytest.mark.parametrize("set_to", ["on", "true", "1", CANARY])
def test_development_is_said_in_one_word(set_to: str):
    assert refused(AT_HOME | {"BURRO_ACCOUNTS_DEVELOPMENT": set_to}) == (
        "BURRO_ACCOUNTS_DEVELOPMENT",
    )


# The sender.


def test_with_no_sender_named_accounts_are_on_and_nothing_is_sent():
    assert on(ON).sender is None


def test_the_sender_for_development_is_refused_where_the_service_is_not_in_development():
    names = refused(ON | {"BURRO_ACCOUNTS_SENDER": "console"})

    assert set(names) == {"BURRO_ACCOUNTS_SENDER", "BURRO_ACCOUNTS_DEVELOPMENT"}
    assert on(AT_HOME).sender is SenderName.CONSOLE


@pytest.mark.parametrize("named", ["sendgrid", "smtp", "Postmark ", "https://api.example", CANARY])
def test_a_sender_is_one_of_a_closed_list(named: str):
    env = WITH_A_COMPANY | {"BURRO_ACCOUNTS_SENDER": named}

    if named.strip().lower() == "postmark":
        assert on(env).sender is SenderName.POSTMARK
    else:
        assert refused(env) == ("BURRO_ACCOUNTS_SENDER",)


@pytest.mark.parametrize("missing", ["BURRO_ACCOUNTS_SENDER_KEY", "BURRO_ACCOUNTS_SENDER_FROM"])
def test_a_company_that_sends_needs_its_key_and_the_address_it_sends_from(missing: str):
    env = {name: value for name, value in WITH_A_COMPANY.items() if name != missing}

    assert refused(env) == (missing,)


@pytest.mark.parametrize("sent_from", ["burro", "Burro <sign-in@burro.example>", f"{CANARY}@x"])
def test_the_address_a_link_is_sent_from_is_an_address(sent_from: str):
    env = WITH_A_COMPANY | {"BURRO_ACCOUNTS_SENDER_FROM": sent_from}

    assert refused(env) == ("BURRO_ACCOUNTS_SENDER_FROM",)


def test_a_key_alone_names_no_sender():
    env = ON | {"BURRO_ACCOUNTS_SENDER_KEY": SENDER_KEY}

    found = on(env)

    # The key is let go of, where nothing is named that it could be the key of.
    assert found.sender is None and found.sender_key is None


# The rest.


@pytest.mark.parametrize(("set_to", "held"), [("0", 0), ("1", 1), ("10000", 10_000)])
def test_the_cap_on_the_whole_service_is_a_whole_number(set_to: str, held: int):
    assert on(ON | {"BURRO_ACCOUNTS_LINKS_PER_HOUR": set_to}).links_per_hour == held


@pytest.mark.parametrize("set_to", ["-1", "10001", "1_000", "20.0", "many", f"9{CANARY}"])
def test_a_cap_that_is_not_a_whole_number_or_is_too_many_is_refused(set_to: str):
    env = ON | {"BURRO_ACCOUNTS_LINKS_PER_HOUR": set_to}

    assert refused(env) == ("BURRO_ACCOUNTS_LINKS_PER_HOUR",)


def test_whether_the_last_searches_are_kept_from_the_start_is_one_setting():
    assert on(ON | {"BURRO_ACCOUNTS_KEEP_RECENT": "asked"}).keep_recent is KeepRecent.ASKED
    chosen = on(ON | {"BURRO_ACCOUNTS_KEEP_RECENT": "from_the_start"})
    assert chosen.keep_recent is KeepRecent.FROM_THE_START
    assert refused(ON | {"BURRO_ACCOUNTS_KEEP_RECENT": "always"}) == ("BURRO_ACCOUNTS_KEEP_RECENT",)


def test_settings_that_were_made_by_hand_are_held_to_the_same():
    found = on(AT_HOME)
    made: dict[str, Any] = found.model_dump()

    away = AccountsSettings.model_validate(made | {"site": "https://burro.example"})

    held_to(found, "127.0.0.1", ("http://127.0.0.1:3381",))
    with pytest.raises(NotSet):
        held_to(found, "0.0.0.0", ("http://127.0.0.1:3381",))  # noqa: S104
    with pytest.raises(NotSet):
        held_to(away, "127.0.0.1", ("http://127.0.0.1:3381",))
