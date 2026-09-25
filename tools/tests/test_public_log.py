"""What a step of a data build may show. Every row, key and address here is made up."""

import base64
import io
import sys
from pathlib import Path

import pytest
from public_log import (
    COUNTS,
    FEATURES,
    HASHES,
    RELEASES,
    RULES,
    SECRET_NAMES,
    SECRETS_OF,
    STATUSES,
    STORE,
    TRAVEL_RULES,
    forms_of,
    is_public,
    main,
    mask,
    run_step,
)

ROW = "made-up-row,SW0 0XX,250000"
KEY = "made-up-key-0123456789"
ADDRESS = "https://made-up-account.store.example.test"
HOST = "made-up-account.store.example.test"
HASH = "0123456789abcdef" * 4
SECRETS = {
    "BURRO_STORE_ENDPOINT": ADDRESS,
    "BURRO_STORE_BUCKET": "made-up-bucket",
    "BURRO_STORE_KEY_ID": "made-up-key-id",
    "BURRO_STORE_SECRET": KEY,
}
# What an environment holds while no step of its workflow reads the store. The guide
# gives these, and a test holds the guide to what is accepted here.
REHEARSAL = {
    "BURRO_STORE_ENDPOINT": "https://rehearsal-0000.invalid",
    "BURRO_STORE_BUCKET": "rehearsal-bucket-0000",
    "BURRO_STORE_KEY_ID": "rehearsal-key-id-0000",
    "BURRO_STORE_SECRET": "rehearsal-secret-0000",
}


def python(code: str) -> list[str]:
    # With -S it starts sooner: no step here needs a package, and there are some forty.
    return [sys.executable, "-S", "-c", code]


def shown(code: str, environ: dict[str, str] | None = None) -> tuple[int, str]:
    out = io.StringIO()
    status = run_step("assemble", python(code), {**SECRETS, **(environ or {})}, out)
    return status, out.getvalue()


# Which lines are public


@pytest.mark.parametrize(
    "line",
    [
        "step=fetch files=3 bytes=1048576",
        f"step=assemble sha256={HASH}",
        f"step=manifest status=ok copy=a release=syn-2026-09-23-01 files=11 manifest_sha256={HASH}",
        "step=manifest status=failed copy=b wrong=2",
        "step=manifest status=failed copy=b unlisted=1",
        "step=compare status=differs files=11 differing=1",
        "step=fetch source=synthetic file_id=f-0123456789ab status=ok",
        "release=syn-2026-09-23-01 file=manifest.json",
        "withheld=0",
        # What each step prints today, with made-up counts.
        "step=assemble status=ok exit=0 withheld=1 seconds=0.7",
        "step=assemble status=failed exit=1 secrets=1 withheld=0",
        "step=assemble status=refused debug=1",
        "step=assemble status=refused short=1",
        "step=secrets set=5 missing=0",
        "step=secrets status=missing missing=2",
        "step=plan n=1 source=synthetic status=missing why=3 seconds=0.0",
        "step=plan status=missing files=11 ready=0",
        f"step=fetch n=2 source=synthetic status=ok file_id=f-0123456789ab sha256={HASH} "
        "bytes=732000 new=1 by_hand=1 seconds=12.5",
        "step=fetch n=3 source=synthetic status=failed why=27 http=403 seconds=0.4",
        "step=fetch status=failed files=11 ok=9 skipped=0 refused=0 failed=1 missing=1 "
        "unreadable=0 differs=0",
        "step=store status=ok files=10 bytes=168002",
        "step=store status=ok receipts=10 new=1 same=9 differs=0 unreadable=0",
        f"step=seal status=ok release=lon-2026-10-02-01 inputs=11 development=1 lock_sha256={HASH}",
        "step=seal status=refused gate_refuses=1 file_id=f-0123456789ab",
        f"step=check status=failed release=lon-2026-10-02-01 facts=1119 rows=1119 files=3 "
        f"findings=2 evidence_sha256={HASH} fact_has_a_row=1 row_has_a_value=1",
        f"step=report status=ok release=lon-2026-10-02-01 areas=450 measures=5 values=2200 "
        f"gaps=50 no_record=0 coverage_sha256={HASH}",
        "step=canary status=ok steps=3 found=0 unread=0 uncaught=0",
        "step=search status=ok jobs=4 logs=4 artifacts=0 found=0",
        # The lock of a release, and a release that is kept and taken.
        f"step=lock status=ok copy=a release=lon-2026-10-02-01 files=25 bytes=88000000 "
        f"areas=1002 measures=98 vibes=14 sha256={HASH}",
        "step=compare status=differs folder=build file=evidence.json",
        "step=compare status=differs files=25 differing=1 wrong=1",
        "step=keep kind=object_store",
        "step=keep status=ok release=lon-2026-10-02-01 files=25 bytes=88000000 new=25 same=0",
        "step=keep status=refused release=lon-2026-10-02-01 differs=1",
        f"step=take status=ok release=lon-2026-10-02-01 files=25 bytes=88000000 sha256={HASH}",
        "step=take status=missing release=lon-2026-10-02-01",
        "step=take status=differs release=lon-2026-10-02-01 folder=income file=income.json",
        "step=take status=refused release=lon-2026-10-02-01 unlisted=3",
    ],
)
def test_a_line_of_step_names_counts_and_hashes_is_public(line: str):
    assert is_public(line)


# A name carries what a value carries. A row can be printed as names with a count after each.


@pytest.mark.parametrize(
    "line",
    [
        "uprn=100023336956 price=450000 easting=531234 northing=181234",
        "zz9_9zz=1 made_up_person=1 flat_3_12_made_up_street=1",
        "sale=450000.00 year=2024 month=3 day=14",
        "step=fetch files=3 price=450000",
        "step=fetch zz9_9zz=1",
        f"made_up_street_sha256={HASH}",
        f"zz9_9zz_sha256={HASH}",
        "count=12",
        # Steps that are not built print nothing yet. Their names are added with them.
        "step=normalise rows_in=120000 rows_out=4994 columns_dropped=3",
        # A folder of a build is one of three, and a file of one is a file a build writes.
        "step=compare status=differs folder=brackenhythe file=evidence.json",
        "step=compare status=differs folder=build file=brackenhythe.json",
        "step=take status=differs folder=../build file=names.csv",
        "folder=3",
    ],
)
def test_a_number_under_a_name_that_is_not_on_the_list_is_withheld(line: str):
    assert not is_public(line)


@pytest.mark.parametrize(
    "line",
    [
        "files=-3",
        "files=3.5",
        "bytes=1e9",
        "bytes=0x10",
        "files=1234567890123456",
        "seconds=1.2345",
        "seconds=-1.0",
        "seconds=.5",
        "why=450",
        "why=3.0",
        "http=45",
        "http=4030",
        "http=999",
        "exit=-9",
    ],
)
def test_a_count_is_a_whole_number_and_only_a_time_has_a_fraction(line: str):
    assert not is_public(line)


def test_every_name_is_held_to_one_shape():
    assert not COUNTS & HASHES and not COUNTS & RULES and not HASHES & RULES
    # A status is a name too: fetch counts its files by how each ended.
    assert all(is_public(f"{status}=3") for status in STATUSES)
    assert all(is_public(f"{name}=3") for name in COUNTS | RULES)
    assert all(is_public(f"{name}={HASH}") for name in HASHES)
    assert not any(is_public(f"{name}=3") for name in HASHES)
    assert not any(is_public(f"{name}={HASH}") for name in COUNTS | RULES)


def test_every_rule_the_evidence_names_may_be_counted_and_no_other():
    # A refusal names its rule, and a check counts its findings by rule.
    from burro_pipeline.evidence.lock import MEANING as of_the_lock
    from burro_pipeline.evidence.served import MEANING as of_the_check

    assert set(of_the_lock) | set(of_the_check) == RULES


def test_every_rule_the_travel_step_names_may_be_counted_and_no_other():
    from burro_pipeline.travel.engine import MEANING as of_what_is_routed
    from burro_pipeline.travel.feed import MEANING as of_the_timetable

    assert set(of_the_timetable) | set(of_what_is_routed) == TRAVEL_RULES
    assert not TRAVEL_RULES & (COUNTS | RULES | HASHES)
    assert all(is_public(f"step=travel status=refused {rule}=1") for rule in TRAVEL_RULES)
    assert not any(is_public(f"{rule}={HASH}") for rule in TRAVEL_RULES)


def test_a_vibe_is_named_by_its_id_in_cores_catalogue_and_by_nothing_else():
    from burro_core.ids import TagId
    from public_log import VIBES

    assert {vibe.value for vibe in TagId} == VIBES
    assert is_public("step=moved vibe=leafy areas=24 changed=3 up=2 down=1 gained=0 lost=0")
    assert not is_public("step=moved vibe=Leafy changed=3")
    assert not is_public(f"step=moved vibe={ROW}")


def test_a_build_is_named_before_and_after_by_the_id_of_its_release_alone():
    assert is_public("step=moved status=ok before=lon-2026-09-25-01 after=lon-2026-10-02-01")
    assert not is_public("step=moved status=ok before=data/releases/lon-2026-09-25-01")
    assert not is_public(f"step=moved status=ok after={ROW}")


def test_what_changed_of_the_catalogue_is_a_version_and_a_count_and_never_a_name():
    """A name or a label that changed is words that a catalogue held. It is counted."""
    assert is_public(
        "step=moved vibe=village_feel parts_came=2 parts_went=3 shares_changed=2 "
        "names_changed=0 rough_came=1 rough_went=0"
    )
    assert is_public("step=moved feature=air_no2 names_changed=1")
    assert is_public(
        "step=moved status=ok before=lon-2026-09-25-01 after=lon-2026-10-02-01 "
        "catalogue_before=13 catalogue_after=14"
    )
    for line in (
        "step=moved catalogue_before=thirteen",
        f"step=moved vibe=leafy names_changed={ROW}",
        "step=moved vibe=leafy was=Leafy now=Green",
        "step=moved vibe=leafy parts_came=highstreet_conserved",
    ):
        assert not is_public(line), line


def test_a_measure_is_named_by_its_id_in_cores_catalogue_and_by_nothing_else():
    from burro_core.ids import FeatureId

    assert {feature.value for feature in FeatureId} == FEATURES
    assert is_public("step=derive status=ok feature=homes_flats areas=24 values=24 files=3")
    assert is_public("step=derive status=skipped feature=noise_exposure input_has_one_receipt=1")
    assert is_public("step=derive status=skipped feature=water_access measure_is_not_held_back=1")
    for line in ("feature=brackenhythe", "feature=3", "feature=homes_flats,0.5", "measure=x"):
        assert not is_public(line)


def test_a_list_and_an_item_are_named_as_the_lists_of_this_repository_name_them():
    from burro_pipeline.fetch.sources import LISTS, load_list

    lists = [load_list(path.stem) for path in sorted(LISTS.glob("*.toml"))]
    assert lists, "the repository holds a list of files"
    for one in lists:
        assert is_public(f"step=store list={one.build} status=ok files=1 receipts=1 missing=0")
        assert all(is_public(f"list={one.build} item={file.item}") for file in one.files)
    assert is_public(
        "step=store list=m2-living source=dfe-gias item=gias-establishments status=missing "
        "file_id=f-0123456789ab"
    )
    assert is_public("step=store status=ok lists=13 receipts=86 missing=0 differs=0 unlisted=0")
    # A name that no list gives is not a name: it may be a row, a bucket or an address.
    for line in (
        "list=made-up-bucket",
        "list=m1.toml",
        "list=3",
        "item=brackenhythe",
        "item=SW00XX",
        "item=extract.zip",
        f"item={HASH}",
        "lists=m1",
    ):
        assert not is_public(line)


# What fetch says of a store, of what arrived, and of a host


@pytest.mark.parametrize(
    "line",
    [
        "step=store kind=object_store",
        "step=fetch n=4 source=synthetic status=unreadable kind=html why=5 seconds=0.2",
        "step=fetch n=4 source=synthetic status=failed why=28 host=0123456789ab seconds=0.2",
    ],
)
def test_what_fetch_says_of_a_store_a_file_and_a_host_is_public(line: str):
    assert is_public(line)


@pytest.mark.parametrize(
    "line",
    [
        "host=files.example.test",
        "host=example",
        "host=0123456789a",
        "host=0123456789abc",
        "host=0123456789AB",
        f"host={HASH}",
        "host=12",
        "kind=made-up-bucket",
        "kind=brackenhythe",
        "found=yes",
        # No step counts under this name, so nothing is shown under it.
        "store=2",
        "store=ok",
    ],
)
def test_a_host_is_shown_as_twelve_digits_of_a_hash_and_never_by_name(line: str):
    assert not is_public(line)


@pytest.mark.parametrize(
    "line",
    [
        ROW,
        f"step=normalise row={ROW}",
        "step=normalise postcode=SW00XX",
        "step=normalise name=Brackenhythe",
        "step=made-up-step files=3",
        "status=whatever",
        "sha256=0123",
        f"sha256={HASH.upper()}",
        "source=Some Publisher",
        "file=../../etc/passwd",
        "file=brackenhythe.csv",
        "release=made-up",
        "files=1e9",
        "files=12 ",
        " files=12",
        "files=12  bytes=3",
        "files = 12",
        "FILES=12",
        "Traceback (most recent call last):",
        '  File "normalise.py", line 12, in read',
        f"KeyError: '{ROW}'",
        "::add-mask::made-up",
        "::error::made-up",
        f"::set-output name=row::{ROW}",
        "",
        "=",
        "files=",
        "=12",
    ],
)
def test_any_other_line_is_withheld(line: str):
    assert not is_public(line)


# Running a step


def test_a_steps_own_words_are_counted_and_never_shown():
    status, out = shown(f"print({ROW!r}); print('step=assemble files=11')")
    assert status == 0
    assert ROW not in out
    assert "step=assemble files=11\n" in out
    assert "step=assemble status=ok exit=0 withheld=1" in out


def test_what_a_step_writes_to_its_error_stream_is_withheld_too():
    status, out = shown(f"import sys; print({ROW!r}, file=sys.stderr)")
    assert status == 0
    assert ROW not in out
    assert "withheld=1" in out


def test_a_step_that_fails_says_so_and_shows_no_more():
    status, out = shown(f"raise KeyError({ROW!r})")
    assert status == 1
    assert ROW not in out and "KeyError" not in out and "Traceback" not in out
    assert "step=assemble status=failed exit=1" in out


def test_the_exit_code_of_the_step_is_kept():
    assert shown("raise SystemExit(7)")[0] == 7


def test_a_step_killed_by_a_signal_fails():
    status, out = shown("import os, signal; os.kill(os.getpid(), signal.SIGKILL)")
    assert status != 0
    assert "status=failed" in out


@pytest.mark.parametrize(
    "printed",
    [
        KEY,
        f"key = {KEY}",
        ADDRESS,
        f"connecting to {HOST}:443",
        f"GET {ADDRESS.upper()}/made-up-bucket",
        "made-up-bucket",
        base64.b64encode(f"made-up-key-id:{KEY}".encode()).decode(),
        base64.b64encode(KEY.encode()).decode(),
        KEY.replace("-", "%2D"),
    ],
)
def test_a_step_that_prints_a_secret_fails_the_build(printed: str):
    status, out = shown(f"print({printed!r}); print('files=1')")
    assert status != 0
    assert printed not in out
    assert "step=assemble status=failed" in out and "secrets=1" in out


def test_a_step_that_prints_a_secret_fails_even_when_the_line_would_be_public():
    environ = {"BURRO_STORE_BUCKET": "12345678"}
    status, out = shown("print('files=12345678')", environ)
    assert status != 0
    assert "12345678" not in out


def test_a_step_that_prints_its_environment_fails_the_build():
    status, out = shown("import os; print(dict(os.environ))")
    assert status != 0
    assert all(value not in out for value in SECRETS.values())
    assert "secrets=1" in out


def test_a_secret_split_over_two_lines_is_still_withheld():
    status, out = shown(f"print({KEY[:9]!r}); print({KEY[9:]!r})")
    assert status == 0, "half a key on a line is not a key, and the line is withheld anyway"
    assert KEY[:9] not in out and KEY[9:] not in out


def test_a_secret_too_short_to_search_for_is_refused_before_the_step_runs(tmp_path: Path):
    ran = tmp_path / "ran"
    code = f"open({str(ran)!r}, 'w').close()"
    status, out = shown(code, {"BURRO_STORE_BUCKET": "abc"})
    assert status != 0
    assert not ran.exists()
    assert "abc" not in out


def test_with_debug_logging_on_no_step_is_run_and_no_secret_is_checked(tmp_path: Path):
    # What the runner adds to a log then is not known, so nothing is run to be logged.
    ran = tmp_path / "ran"
    status, out = shown(f"open({str(ran)!r}, 'w').close()", {"RUNNER_DEBUG": "1"})
    assert status != 0
    assert not ran.exists()
    assert out == "step=assemble status=refused debug=1\n"
    masked = io.StringIO()
    assert mask({**SECRETS, "RUNNER_DEBUG": "1"}, masked) != 0
    assert "::add-mask::" not in masked.getvalue()
    assert "debug logging" in masked.getvalue()


def test_a_step_cannot_write_to_what_the_website_shows(tmp_path: Path):
    files = {
        name: tmp_path / name
        for name in ("GITHUB_STEP_SUMMARY", "GITHUB_OUTPUT", "GITHUB_ENV", "GITHUB_PATH")
    }
    code = (
        "import os\n"
        f"for name in {sorted(files)!r}:\n"
        "    if name in os.environ:\n"
        f"        open(os.environ[name], 'a').write({ROW!r})\n"
    )
    status, _ = shown(code, {name: str(path) for name, path in files.items()})
    assert status == 0
    assert not any(path.exists() for path in files.values())


def test_a_step_still_holds_the_secrets_it_was_given():
    code = f"import os; raise SystemExit(0 if os.environ['BURRO_STORE_SECRET'] == {KEY!r} else 9)"
    assert shown(code)[0] == 0


def test_a_line_that_is_not_text_is_withheld():
    status, out = shown("import sys; sys.stdout.buffer.write(b'\\xff\\xfe row\\n')")
    assert status == 0
    assert "withheld=1" in out


def test_a_long_run_of_output_is_read_as_it_comes():
    status, out = shown("for n in range(20000): print('made-up row', n)\nprint('rows=20000')")
    assert status == 0
    assert "rows=20000\n" in out
    assert "withheld=20000" in out


def test_a_command_that_does_not_exist_fails_and_is_not_named():
    out = io.StringIO()
    status = run_step("assemble", ["made-up-command-that-is-not-there", ROW], SECRETS, out)
    assert status != 0
    assert ROW not in out.getvalue()
    assert "status=failed" in out.getvalue()


# The forms a secret can take


def test_a_secret_is_searched_for_in_every_form_it_is_likely_to_be_printed_in():
    forms = forms_of(SECRETS)
    assert {KEY, ADDRESS.lower(), HOST, "made-up-bucket", "made-up-key-id"} <= forms
    assert base64.b64encode(KEY.encode()).decode().lower() in forms
    assert base64.b64encode(f"made-up-key-id:{KEY}".encode()).decode().lower() in forms


def test_a_variable_that_is_not_a_secret_is_not_searched_for():
    assert forms_of({"HOME": "/made-up/home", "PATH": "/usr/bin"}) == frozenset()


def test_the_token_of_the_run_is_a_secret_too():
    assert "made-up-token-0123" in forms_of({"GITHUB_TOKEN": "made-up-token-0123"})


# Hiding what is made from a secret


def test_every_secret_a_step_is_given_must_be_set():
    # A secret that was never stored reaches a step as an empty value.
    out = io.StringIO()
    assert mask({**SECRETS, "BURRO_STORE_BUCKET": ""}, out) != 0
    assert "BURRO_STORE_BUCKET is not set" in out.getvalue()
    assert all(value not in out.getvalue() for value in SECRETS.values() if value)


def test_a_secret_the_step_was_not_given_is_not_asked_for():
    out = io.StringIO()
    assert mask(SECRETS, out) == 0
    assert "BURRO_FETCH_CONTACT" not in out.getvalue()
    assert mask({**SECRETS, "BURRO_FETCH_CONTACT": ""}, out) != 0
    assert "BURRO_FETCH_CONTACT is not set" in out.getvalue()


def test_a_step_given_no_secret_at_all_has_nothing_to_hide_and_fails():
    out = io.StringIO()
    assert mask({"HOME": "/made-up/home"}, out) != 0
    assert "No secret was given to this step" in out.getvalue()


def test_every_environment_holds_the_stores_four_secrets():
    store = {name for name in SECRET_NAMES if name.startswith("BURRO_STORE_")}
    assert len(store) == 4
    assert all(store <= set(names) for names in SECRETS_OF.values())
    assert set(SECRET_NAMES) == {name for names in SECRETS_OF.values() for name in names}


def test_why_a_draft_of_the_areas_stopped_is_shown():
    """A hosted run drafts the names of the areas, and a draft prints under a name of its own.

    With that name off the list, a draft that stopped for want of a file showed
    that it had failed, and not why.
    """
    assert is_public("step=areas-draft status=refused file_is_in_the_vault=1")
    assert is_public("step=areas-draft status=unreadable")
    assert not is_public(f"step=areas-draft status=refused {ROW}")
    assert not is_public("step=areas-draft status=ok name=Brackenhythe")


# The bucket of releases, which has keys of its own

OF_RELEASES = {
    "BURRO_RELEASES_ENDPOINT": "https://made-up-account.releases.example.test",
    "BURRO_RELEASES_BUCKET": "made-up-releases",
    "BURRO_RELEASES_KEY_ID": "made-up-keep-id",
    "BURRO_RELEASES_SECRET": "made-up-keep-0123456789",
}


def test_the_build_of_london_alone_holds_the_key_that_writes_a_release():
    assert set(RELEASES) == set(OF_RELEASES)
    assert SECRETS_OF["data-london"] == (*STORE, *RELEASES)
    holds = {name for name, held in SECRETS_OF.items() if set(RELEASES) & set(held)}
    assert holds == {"data-london"}
    # A fetch is what writes a publisher's file. It is given no key of the releases.
    assert not set(RELEASES) & set(SECRETS_OF["data-fetch"])


def test_the_key_of_the_releases_is_searched_for_in_every_form_too():
    forms = forms_of(SECRETS | OF_RELEASES)
    assert {"made-up-releases", "made-up-keep-id", "made-up-keep-0123456789"} <= forms
    assert "made-up-account.releases.example.test" in forms and HOST in forms
    pair = "made-up-keep-id:made-up-keep-0123456789"
    assert base64.b64encode(pair.encode()).decode().lower() in forms
    # The key of one store is never sent with the id of the other.
    crossed = f"made-up-key-id:{OF_RELEASES['BURRO_RELEASES_SECRET']}"
    assert base64.b64encode(crossed.encode()).decode().lower() not in forms


def test_a_step_that_prints_the_key_of_the_releases_fails_the_build():
    key = OF_RELEASES["BURRO_RELEASES_SECRET"]
    status, out = shown(f"print('kept with {key}')", OF_RELEASES)
    assert status != 0 and key not in out
    assert out == "step=assemble status=failed exit=0 secrets=1 withheld=0\n"


def test_the_address_of_the_releases_is_held_to_https_and_hidden_as_the_stores_is():
    out = io.StringIO()
    assert mask(SECRETS | OF_RELEASES, out) == 0
    lines = out.getvalue().splitlines()
    assert "::add-mask::made-up-account.releases.example.test" in lines
    assert f"::add-mask::{HOST}" in lines
    assert lines[-1] == "step=secrets set=8 missing=0"
    plain = OF_RELEASES | {"BURRO_RELEASES_ENDPOINT": "http://made-up.example.test"}
    out = io.StringIO()
    assert mask(SECRETS | plain, out) != 0
    assert "BURRO_RELEASES_ENDPOINT must begin https://" in out.getvalue()
    assert "made-up.example.test" not in out.getvalue()


def test_a_made_up_address_of_the_releases_ends_as_a_made_up_address_does():
    made_up = {
        "BURRO_RELEASES_ENDPOINT": "https://rehearsal-0000.invalid",
        "BURRO_RELEASES_BUCKET": "rehearsal-releases-0000",
        "BURRO_RELEASES_KEY_ID": "rehearsal-keep-id-0000",
        "BURRO_RELEASES_SECRET": "rehearsal-keep-0000",
    }
    out = io.StringIO()
    assert mask(REHEARSAL | made_up, out, made_up=True) == 0
    real = made_up | {"BURRO_RELEASES_ENDPOINT": OF_RELEASES["BURRO_RELEASES_ENDPOINT"]}
    out = io.StringIO()
    assert mask(REHEARSAL | real, out, made_up=True) != 0
    assert "BURRO_RELEASES_ENDPOINT is not a made-up value" in out.getvalue()


@pytest.mark.parametrize("pasted", [f"{KEY}\n", f" {KEY}", f"{KEY[:8]} {KEY[8:]}", f"{KEY}\r\n"])
def test_a_secret_pasted_with_a_space_or_a_line_break_is_refused(pasted: str):
    out = io.StringIO()
    assert mask({**SECRETS, "BURRO_STORE_SECRET": pasted}, out) != 0
    assert "BURRO_STORE_SECRET holds a space or a line break" in out.getvalue()
    assert KEY not in out.getvalue() and "::add-mask::" not in out.getvalue()


def test_what_is_made_from_a_secret_is_hidden_by_the_runner():
    out = io.StringIO()
    assert mask(SECRETS, out) == 0
    lines = out.getvalue().splitlines()
    assert f"::add-mask::{HOST}" in lines
    assert f"::add-mask::{base64.b64encode(KEY.encode()).decode()}" in lines
    assert lines[-1] == "step=secrets set=4 missing=0"


def test_an_address_that_is_not_https_is_refused_and_not_shown():
    out = io.StringIO()
    assert mask({**SECRETS, "BURRO_STORE_ENDPOINT": "http://made-up.example.test"}, out) != 0
    assert "made-up.example.test" not in out.getvalue()
    assert "BURRO_STORE_ENDPOINT must begin https://" in out.getvalue()


# Secrets that must each be made up


def test_made_up_secrets_are_checked_and_hidden_as_real_ones_are():
    out = io.StringIO()
    assert mask(REHEARSAL, out, made_up=True) == 0
    lines = out.getvalue().splitlines()
    assert "::add-mask::rehearsal-0000.invalid" in lines
    assert lines[-1] == "step=secrets set=4 missing=0"
    assert is_public(lines[-1])


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("BURRO_STORE_ENDPOINT", ADDRESS),
        ("BURRO_STORE_ENDPOINT", "https://rehearsal-0000.example.test"),
        ("BURRO_STORE_ENDPOINT", "https://rehearsal.invalid.example.test"),
        ("BURRO_STORE_ENDPOINT", "https://made-up-account.example.test/rehearsal-0000.invalid"),
        ("BURRO_STORE_BUCKET", "made-up-bucket"),
        ("BURRO_STORE_KEY_ID", "0123456789abcdef0123456789abcdef"),
        ("BURRO_STORE_SECRET", KEY),
        ("BURRO_STORE_SECRET", f"{KEY}-rehearsal-0000"),
    ],
)
def test_a_value_that_is_not_made_up_is_refused_where_no_step_reads_the_store(
    name: str, value: str
):
    out = io.StringIO()
    assert mask({**REHEARSAL, name: value}, out, made_up=True) != 0
    said = out.getvalue()
    assert f"{name} is not a made-up value" in said
    assert value not in said and "::add-mask::" not in said
    assert said.splitlines()[-1] == "step=secrets status=refused real=1"
    assert is_public(said.splitlines()[-1])


def test_a_made_up_value_is_still_pasted_whole_and_long_enough():
    out = io.StringIO()
    assert mask({**REHEARSAL, "BURRO_STORE_BUCKET": ""}, out, made_up=True) != 0
    assert "BURRO_STORE_BUCKET is not set" in out.getvalue()
    assert mask({**REHEARSAL, "BURRO_STORE_SECRET": "rehearsal-secret 0000"}, out, True) != 0
    assert "BURRO_STORE_SECRET holds a space or a line break" in out.getvalue()


def test_a_real_secret_is_not_asked_to_be_made_up():
    out = io.StringIO()
    assert mask(SECRETS, out) == 0
    assert "is not a made-up value" not in out.getvalue()


def test_the_command_checks_made_up_secrets(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    for name in SECRET_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("RUNNER_DEBUG", raising=False)
    for name, value in REHEARSAL.items():
        monkeypatch.setenv(name, value)
    assert main(["mask", "--made-up"]) == 0
    assert "step=secrets set=4 missing=0" in capsys.readouterr().out
    monkeypatch.setenv("BURRO_STORE_SECRET", KEY)
    assert main(["mask", "--made-up"]) != 0
    printed = capsys.readouterr()
    assert KEY not in printed.out + printed.err
    assert main(["mask"]) == 0
    with pytest.raises(SystemExit):
        main(["mask", "--real"])


def test_the_guide_gives_made_up_values_that_are_accepted():
    guide = (Path(__file__).resolve().parents[2] / "docs" / "data-builds.md").read_text()
    assert all(f"`{value}`" in guide for value in REHEARSAL.values())


# The command


def test_the_command_runs_a_step(capsys: pytest.CaptureFixture[str]):
    code = f"print({ROW!r}); print('files=11')"
    assert main(["--step", "assemble", "--", *python(code)]) == 0
    printed = capsys.readouterr()
    assert ROW not in printed.out + printed.err
    assert "files=11" in printed.out


def test_a_step_must_have_a_name_from_the_list(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit):
        main(["--step", ROW, "--", *python("print(1)")])
    printed = capsys.readouterr()
    assert ROW not in printed.out + printed.err
