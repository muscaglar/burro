"""The steps of the command line that fetch owns.

    python -m burro_pipeline plan --list m1         what the gate says and what is missing
    python -m burro_pipeline fetch --list m1        fetch every file of the list that has an address
    python -m burro_pipeline by-hand --list m1 ...  take a file a person saved from a browser
    python -m burro_pipeline held --out FILE        what the store holds, as `seal` reads it
    python -m burro_pipeline receipts               bring the receipts in the store to the folder
    python -m burro_pipeline describe f-0123...     the shape of a stored file, on your own machine
    python -m burro_pipeline why                    what each `why=` number means

The store is named by the environment: BURRO_STORE_FOLDER for a folder, or
BURRO_STORE_ENDPOINT, BURRO_STORE_BUCKET, BURRO_STORE_KEY_ID and
BURRO_STORE_SECRET for an object store, and never both. `fetch` also needs
BURRO_FETCH_CONTACT, an address a publisher can write to. None of these is ever
printed.

`plan`, `fetch`, `by-hand`, `held` and `receipts` print lines of `key=value` that
hold step names, registry ids, counts and hashes, under names that are on the
list in `tools/public_log.py`. `--words` adds a sentence for a person at a
terminal. `describe` prints JSON that holds names from the file's own layout.
`fetch` is the only command that reaches a publisher.
"""

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Mapping, Sequence
from contextlib import nullcontext, suppress
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from burro_pipeline.command import PROG, Step, add_step
from burro_pipeline.evidence import Receipt, Where
from burro_pipeline.evidence.receipt import RECEIPTS_FOLDER
from burro_pipeline.fetch import gate
from burro_pipeline.fetch.by_hand import keep_by_hand
from burro_pipeline.fetch.describe import DescribeError, as_text, describe
from burro_pipeline.fetch.download import DownloadRefused, download, may_be_asked, user_agent
from burro_pipeline.fetch.offline import sockets_refused
from burro_pipeline.fetch.run import (
    OF_A_DOWNLOAD,
    WORDS,
    Downloader,
    Outcome,
    Status,
    Taker,
    Why,
    fetch,
    host_mark,
    refusal,
    summary,
    write_receipt,
)
from burro_pipeline.fetch.sources import (
    FetchList,
    InTheFile,
    Listed,
    ListError,
    Take,
    load_list,
)
from burro_pipeline.fetch.store import (
    FOLDER_VARIABLE,
    S3_VARIABLES,
    FolderStore,
    Store,
    StoreError,
    find,
    store_from_environment,
)
from burro_pipeline.fetch.take import take_part
from burro_pipeline.registry import Registry, RegistryError, load

RECEIPTS = Path(RECEIPTS_FOLDER)
CONTACT = "BURRO_FETCH_CONTACT"
# Set to 1 on a developer's own machine to see where a fault came from.
DEBUG = "BURRO_FETCH_DEBUG"

THE_STORE = f"""\
The store is named by the environment, and is never printed:
  {FOLDER_VARIABLE}    a folder on this machine, or
  {S3_VARIABLES[0]}  the address of an object store, with
  {S3_VARIABLES[1]}, {S3_VARIABLES[2]} and {S3_VARIABLES[3]}
Name one and not the other: with both named, the step does not start."""
SAYS_WHICH = "Its first line says which kind of store it was given: a folder, or an object store."

COULD_NOT_START = "It could not start: the list, the registry, the store or an argument is wrong"
A_FAULT = "A fault of its own, and of no one file. Only the kind of the fault is printed"

STEPS = (
    Step(
        "plan",
        "Ask the licence registry about every file of a list, and say what is missing",
        """\
Run it before a fetch. For each file of the list it says whether the registry
allows the source for the use the list gives, whether the file is as the
registry entry of its source has it, whether the list holds the address of
the file, and whether its edition and its period are stated. A file whose
publisher names no edition is ready where the list says, under `edition_from`,
where the file states its own: fetch reads it in what arrives.

A file is as its entry has it when its page is one the entry holds, its
address is one the entry names for its files under `file_urls`, and nothing
that says what it is names a census table about residents. A file that is
read for the audit, or is a census table about residents, is refused: each
is kept in a store of its own, and no such store is built.

Reads the list and the registry. Writes nothing. Reaches no network and no store.

Prints one line for each file, then one line of totals. With --words, each
line is followed by the page a person finds the file on, by the hosts the
list and the registry entry name for the file, and by the reason in words
where a file is not ready.

Beside each host, --words prints the start of a hash of its name, as host=.
A run never prints the name of a host: where a publisher sends a request on
to a host the list does not name, the line of the run holds that hash alone.
Name the host you think it is under may_redirect_to, run plan --words, and
see whether the two are the same.""",
        ("--list m1", "--list m1 --words"),
        {0: "Every file is ready to fetch", 1: "Some file is not ready", 2: COULD_NOT_START},
    ),
    Step(
        "fetch",
        "Fetch the files of a list from their publishers, and keep each in the store",
        f"""\
For each file, in this order: the licence registry is asked, the file is
downloaded over https with one request, what arrived is looked at to see that
it is the format listed, it is kept in the store under its hash, and its
receipt is written. The registry is asked about every file of the list before
anything is asked of a publisher, and each file is held to the registry entry
of its source. If one file of the list is refused, no file is fetched, whether
or not that file was asked for.

Where the list says under `take` which part of a file to take, the end of the
file and its footer are asked for first, and then the bytes of that part and
no other. What is kept is the part, and its receipt says which file it is
part of, which row groups were taken, and where in the file each run of bytes
lies. `plan --words` says what the list asks for.

This is the only step that reaches a publisher.

{THE_STORE}
It also needs {CONTACT}: an email address, or an https page, where a
publisher can reach a person. It is sent with every request.

{SAYS_WHICH}

Writes each file to the store, and its receipt under --receipts. A receipt is
written only when the list states the file's edition and period and is sure
of both, or says where the file states its own. That is read in what arrives,
before it is kept, and nothing else of the file is. Commit the receipts: every
figure is cited to one. A copy of each is kept in the store too, and the step
`receipts` brings the copies back.

What goes wrong with one file is said of that file, and the run goes on to
the next: an address that cannot be asked, a publisher that refuses, a fault
of this step's own.

Prints one line for each file, then one line of totals. A reason is a number
after `why=`, and `{PROG} why` says what each means.""",
        ("--list m1", "--list m1 --only oa-lookup --words"),
        {
            0: "Every file asked for is in the store, with its receipt",
            1: "Some file is not. Its line says why",
            2: COULD_NOT_START,
            3: A_FAULT,
        },
    ),
    Step(
        "by-hand",
        "Take a file that a person saved from a browser",
        f"""\
Some publishers will not give a file to a program. Open the page in a browser,
save the file, and hand it over here with the address it was saved from and
the day it was saved. The file passes the same registry, the same look at its
format and the same store as a file that was fetched, and it is held to the
registry entry of its source in the same way. Its receipt says `by_hand`. The
file you saved is left where it is.

A browser may be given an address with a key in it. So the address is written
in the receipt with no parameter but those of the list's own address, each
with the value the list gives it. Where the address of the file holds a
parameter, state the address in the list under `url`, and name the parameter
under `url_parameters`. An address with `;` in it is refused.

Reaches no publisher: the address is written down and never asked. Reaches the store.

{THE_STORE}
{SAYS_WHICH}

Writes the file to the store, and its receipt under --receipts. A copy of the
receipt is kept in the store too.""",
        (
            "--list m1 --item iod-file-8 --file saved/File_8.xlsx "
            "--url https://www.example.org/files/File_8.xlsx --saved-on 2026-09-24",
        ),
        {
            0: "The file is in the store, with its receipt",
            1: "It was refused. Its line says why",
            2: COULD_NOT_START,
            3: A_FAULT,
        },
    ),
    Step(
        "held",
        "Say what the store holds, and write the listing that seal reads",
        f"""\
Run it before `seal`, with --out. The listing gives the size of each file in
the store by its key, and `seal` checks every receipt against it.

Reaches no publisher. Reaches the store.

{THE_STORE}
{SAYS_WHICH}

Then it prints one line: how many files the store holds, and how many bytes.""",
        ("", "--out listing.json"),
        {0: "The store answered", 2: COULD_NOT_START, 3: A_FAULT},
    ),
    Step(
        "receipts",
        "Bring the receipts of fetched files from the store to the repository",
        f"""\
A hosted run fetches on a machine that is thrown away, and the receipts it
wrote go with it. So fetch keeps a copy of each receipt in the store, beside
its file. This step writes every copy to the folder of receipts, where `seal`
reads them. Run it after a fetch in a hosted run, and commit what it writes.

A receipt that is already in the folder is never written over. Where the
store and the folder hold receipts of one file that say something else, the
step stops with `differs`, and both are left as they are.

Reaches no publisher. Reaches the store.

{THE_STORE}
{SAYS_WHICH}

Writes each receipt under --receipts. Then it prints one line of counts.""",
        ("", f"--receipts {RECEIPTS}"),
        {
            0: "Every receipt in the store is in the folder",
            1: "A receipt differs from the one in the folder, or is not a receipt",
            2: COULD_NOT_START,
            3: A_FAULT,
        },
    ),
    Step(
        "describe",
        "Say the shape of a file, on a machine of your own: its columns, its sheets or its layers",
        f"""\
Run it on a file before writing the code that reads it. It prints the names in
the file's own layout and how many rows stand under them.

What it prints is for a machine of your own, and never for a public log. It
takes the first full row of a table for the names of its columns. Where a table
has no header, that row is data: a name, a postcode, a price. It prints no
names where it can tell such a row from a row of names, and says why. It cannot
always tell. So treat all it prints as if it held a row, and paste it nowhere
that others can read. No workflow runs it.

  a CSV          its column names and its row count
  a workbook     its sheets, and the same for each sheet. For an OpenDocument
                 workbook, --sheet gives the words of one sheet too: each row
                 that holds words alone, as a cover, notes and the title over
                 a table do. A row that holds a number is never given
  a GeoPackage   its layers, their fields, how many features each holds, and
                 the day each says it was last changed
  a zip          the names and sizes inside. With --inside, the shape of each

Name a stored file by its file id or its hash, or a file on disk with --path.

Reaches no publisher. Reaches the store, unless --path is given. With --path it
reaches no network.

{THE_STORE}

Prints JSON in plain ASCII. For a stored file its last field, `store`, says
which kind of store it was given: a folder, or an object store.""",
        (
            "f-0123456789ab",
            "f-0123456789ab --inside",
            "f-0123456789ab --sheet Notes",
            "--path saved/File_8.xlsx",
        ),
        {0: "The shape was printed", 2: "The file could not be found or read", 3: A_FAULT},
    ),
    Step(
        "why",
        "Say what each `why=` number in a line of fetch means",
        "Reads nothing and writes nothing. Reaches no network.",
        ("",),
        {0: "Always"},
    ),
)


class Stop(Exception):
    """The command cannot start. The message is safe to print."""


def _list(args: argparse.Namespace) -> FetchList:
    which: str = args.list
    try:
        return load_list(Path(which) if which.endswith(".toml") else which)
    except ListError as error:
        raise Stop(str(error)) from None


def _registry(args: argparse.Namespace) -> Registry:
    try:
        return load(args.registry)
    except RegistryError as error:
        raise Stop(str(error)) from None


def _chosen(listed: FetchList, only: Sequence[str]) -> list[tuple[int, Listed]]:
    """The files asked for, each with its place in the whole list."""
    numbered = list(enumerate(listed.files, start=1))
    if not only:
        return numbered
    known = {file.item for file in listed.files}
    if unknown := sorted(set(only) - known):
        raise Stop(f"the list {listed.build} holds no item named {unknown[0]}")
    return [(n, file) for n, file in numbered if file.item in only]


# What plan says in place of the words of a run, where those say what a run did. Plan
# fetches nothing, so nothing is stored and no receipt is written or left out.
BEFORE_A_RUN = {
    Why.NOT_SURE: (
        "A fetch would store the file and write no receipt, because the list does not state "
        "its edition and its period, or is not sure of them. State both in the list. Where "
        "the file states its own edition and the list says where, state the period"
    ),
}


def _say(outcome: Outcome, words: bool) -> None:
    print(outcome.line(), flush=True)
    if words and outcome.why is not None:
        print(f"  {outcome.words()}", flush=True)


def _plan(args: argparse.Namespace) -> int:
    listed, registry = _list(args), _registry(args)
    with sockets_refused():
        good = 0
        for n, file in enumerate(listed.files, start=1):
            why: Why | None = None
            try:
                gate.ask(file, registry)
            except gate.Refused as refused:
                outcome = refusal(n, file, refused, by_hand=file.by_hand)
                why = outcome.why
            else:
                if not file.has_an_address and not file.by_hand:
                    status, why = Status.MISSING, Why.NO_ADDRESS
                elif (cannot := _cannot_be_asked(file)) is not None:
                    status, why = Status.FAILED, cannot
                elif not file.ready_for_a_receipt:
                    status, why = Status.MISSING, Why.NOT_SURE
                else:
                    status = Status.OK
                    good += 1
                outcome = Outcome(n, file.source_id, status, why, by_hand=file.by_hand)
            print(outcome.line().replace("step=fetch", "step=plan", 1))
            if args.words:
                unsure = f" Not sure of: {', '.join(file.unsure)}." if file.unsure else ""
                print(f"  {file.item}: {file.what}. Page: {file.page}{unsure}")
                if file.edition_from is not None:
                    print(f"  {_read_in_the_file(file.edition_from)}")
                if file.take is not None:
                    print(f"  {_taken_in_part(file.take)}")
                print(f"  Hosts, each with what a run prints for it: {_hosts_of(file, registry)}")
                if why is not None:
                    before = BEFORE_A_RUN.get(why)
                    print(f"  {outcome.words() if before is None else before + '.'}")
    ready = good == len(listed.files)
    status = Status.OK if ready else Status.MISSING
    print(f"step=plan status={status} files={len(listed.files)} ready={good}")
    return 0 if ready else 1


def _read_in_the_file(there: InTheFile) -> str:
    """Where fetch reads the edition of a file that states its own, for a person."""
    if there.where is Where.RETRIEVED:
        return "The file holds no date. Its edition is the day it is retrieved."
    period = "and its period too" if there.period_too else "and its period is the list's"
    return f"Fetch reads its edition in the file, {period}: {there.where}, at {there.at}."


def _taken_in_part(take: Take) -> str:
    """Which part of a file fetch takes, for a person."""
    west, south, east, north = take.box
    return (
        f"Fetch takes part of the file: the row groups that may hold a row between {west} and "
        f"{east} degrees east and between {south} and {north} degrees north, by {take.box_in}, "
        f"and of those the columns {', '.join(sorted(take.columns))}."
    )


def _hosts_of(file: Listed, registry: Registry) -> str:
    """Every host the list and the registry entry name for a file, each with its hash."""
    hosts = {gate.host_of(file.url), *(host.lower().rstrip(".") for host in file.may_redirect_to)}
    with suppress(RegistryError):
        hosts |= gate.hosts_of(registry.get(file.source_id))
    return ", ".join(f"{host} host={host_mark(host)}" for host in sorted(hosts - {""}))


def _cannot_be_asked(file: Listed) -> Why | None:
    """Why a download would refuse a file's address before it asked anything, if it would."""
    if file.by_hand or not file.has_an_address:
        return None
    try:
        may_be_asked(file.url)
    except DownloadRefused as refused:
        return OF_A_DOWNLOAD[refused.reason]
    return None


def _fetch(
    args: argparse.Namespace,
    environment: Mapping[str, str],
    downloader: Downloader,
    taker: Taker = take_part,
) -> int:
    listed, registry = _list(args), _registry(args)
    chosen = _chosen(listed, args.only)
    try:
        agent = user_agent(environment.get(CONTACT, ""))
    except ValueError as error:
        raise Stop(str(error)) from None
    store = _store(environment, said=True)
    # The whole list is handed over, so that every file of it is held to the registry.
    outcomes = fetch(
        listed.files,
        registry,
        store,
        args.receipts,
        agent=agent,
        only={file.item for _, file in chosen},
        downloader=downloader,
        taker=taker,
        said=lambda outcome: _say(outcome, args.words),
        debug=environment.get(DEBUG) == "1",
    )
    print(summary(outcomes), flush=True)
    return 0 if all(outcome.done for outcome in outcomes) else 1


def _by_hand(args: argparse.Namespace, environment: Mapping[str, str]) -> int:
    listed, registry = _list(args), _registry(args)
    ((n, file),) = _chosen(listed, [args.item])
    store = _store(environment, said=True)
    # The address is written down and never asked. Only an object store needs a network.
    with sockets_refused() if isinstance(store, FolderStore) else nullcontext():
        outcome = keep_by_hand(
            n,
            file,
            args.file,
            args.url,
            args.saved_on,
            registry,
            store,
            args.receipts,
            datetime.now(UTC),
        )
    _say(outcome, args.words)
    return 0 if outcome.done else 1


def _describe(args: argparse.Namespace, environment: Mapping[str, str]) -> int:
    if (args.reference is None) == (args.path is None):
        raise Stop("describe takes a file id or a hash, or --path and a file, and not both")
    try:
        if args.path is not None:
            shape = describe(args.path, inside=args.inside, sheet=args.sheet)
        else:
            store = _store(environment)
            held = find(store, args.reference)
            with tempfile.TemporaryDirectory(prefix="burro-describe-") as folder:
                copy = Path(folder) / "file"
                store.get(held.sha256, copy)
                found = describe(copy, inside=args.inside, sheet=args.sheet)
            shape = {"file_id": held.file_id, "source": held.source_id, "sha256": held.sha256}
            # What is printed is read as JSON, so the kind of store is a field of it, and
            # the last: a file read from a folder must not look like one read from the store.
            shape |= found | {"store": store.kind}
    except (StoreError, DescribeError) as error:
        raise Stop(str(error)) from None
    print(as_text(shape))
    return 0


def _held(args: argparse.Namespace, environment: Mapping[str, str]) -> int:
    try:
        held = _store(environment, said=True).list()
    except StoreError as error:
        raise Stop(str(error)) from None
    if args.out is not None:
        listing = {file.key: file.bytes for file in held}
        try:
            args.out.write_text(
                json.dumps(listing, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
                encoding="utf-8",
            )
        except OSError:
            raise Stop("the listing could not be written") from None
    total = sum(file.bytes for file in held)
    print(f"step=store status=ok files={len(held)} bytes={total}")
    return 0


def _receipts(args: argparse.Namespace, environment: Mapping[str, str]) -> int:
    try:
        kept = _store(environment, said=True).receipts()
    except StoreError as error:
        raise Stop(str(error)) from None
    counts: dict[str, int] = {"new": 0, "same": 0, "differs": 0, "unreadable": 0}
    for key, content in kept.items():
        counts[_brought_back(key, content, args.receipts)] += 1
    status = (
        Status.UNREADABLE
        if counts["unreadable"]
        else Status.DIFFERS
        if counts["differs"]
        else Status.OK
    )
    each = " ".join(f"{name}={count}" for name, count in counts.items())
    print(f"step=store status={status} receipts={len(kept)} {each}")
    if counts["unreadable"]:
        print(
            "error: something kept in the store as a receipt is not the receipt of the file it "
            "is kept under. It was left where it is. Fetch the file again, to a new store if "
            "this one cannot be trusted",
            file=sys.stderr,
        )
    if counts["differs"]:
        print(
            "error: a receipt in the store says something else than the receipt of the same "
            "file in the folder. Both were left as they are. Compare the two by hand",
            file=sys.stderr,
        )
    return 0 if status is Status.OK else 1


def _brought_back(key: str, content: bytes, receipts: Path) -> str:
    """Write one receipt from the store to the folder, and say what became of it."""
    try:
        receipt = Receipt.model_validate_json(content)
    except ValidationError:
        return "unreadable"
    if receipt.kept_key() != key or receipt.made_up:
        return "unreadable"
    there = (receipts / receipt.path().relative_to(RECEIPTS_FOLDER)).exists()
    status, _ = write_receipt(receipt, receipts)
    if status is not Status.OK:
        return "differs"
    return "same" if there else "new"


def _why() -> int:
    for why, words in WORDS.items():
        print(f"why={int(why)}  {words}.")
    return 0


def _store(environment: Mapping[str, str], said: bool = False) -> Store:
    """The store the environment names. With `said`, a line says which kind it is.

    A step that writes to the store, reads receipts from it, or shows that it
    answers, says so before it asks anything of it: a run that wrote to a folder
    by mistake must not look like one that wrote to the object store. `describe`
    prints JSON, which a line would break, so it says the kind in a field.
    """
    try:
        store = store_from_environment(environment)
    except StoreError as error:
        raise Stop(str(error)) from None
    if said:
        print(f"step=store kind={store.kind}", flush=True)
    return store


def build(prog: str = PROG) -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    """The steps fetch owns, as the command line takes them: the whole, and each step of it."""
    whole = argparse.ArgumentParser(
        prog=prog, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = whole.add_subparsers(dest="command", required=True)
    step = {step.name: add_step(commands, step, prog) for step in STEPS}

    def listed(command: argparse.ArgumentParser) -> None:
        command.add_argument(
            "--list",
            required=True,
            help="the list of files: a name, as m1, or the path of a .toml file shaped like it",
        )
        command.add_argument(
            "--registry",
            type=Path,
            help="the licence registry, a file or a folder (default: this repository's)",
        )
        command.add_argument(
            "--words", action="store_true", help="add a sentence for a person under each line"
        )

    def kept(command: argparse.ArgumentParser) -> None:
        command.add_argument(
            "--receipts",
            type=Path,
            default=RECEIPTS,
            help=f"the folder receipts are written to (default: {RECEIPTS})",
        )

    listed(step["plan"])
    listed(step["fetch"])
    kept(step["fetch"])
    step["fetch"].add_argument(
        "--only",
        action="append",
        default=[],
        metavar="ITEM",
        help="fetch this item of the list and no other. Give it again for each item wanted",
    )
    listed(step["by-hand"])
    kept(step["by-hand"])
    step["by-hand"].add_argument(
        "--item", required=True, help="which item of the list the file is, by its name there"
    )
    step["by-hand"].add_argument(
        "--file", required=True, type=Path, help="the file, as it was saved"
    )
    step["by-hand"].add_argument(
        "--url", required=True, help="the https address the file was saved from"
    )
    step["by-hand"].add_argument(
        "--saved-on",
        required=True,
        metavar="DAY",
        help="the day it was saved, as 2026-09-24, or the time in UTC, as 2026-09-24T16:45:10Z",
    )
    kept(step["receipts"])
    step["held"].add_argument(
        "--out", type=Path, metavar="FILE", help="write the size of each file by its key, as JSON"
    )
    step["describe"].add_argument(
        "reference",
        nargs="?",
        help="a stored file, by its file id (f- and 12 digits) or its hash (64 digits)",
    )
    step["describe"].add_argument(
        "--path", type=Path, metavar="FILE", help="a file on disk, in place of a stored one"
    )
    step["describe"].add_argument(
        "--inside", action="store_true", help="for a zip, give the shape of each file inside it"
    )
    step["describe"].add_argument(
        "--sheet",
        metavar="NAME",
        help="for an OpenDocument workbook, give the words of this one sheet too",
    )
    return whole, step


def parsed(argv: Sequence[str] | None = None, prog: str = PROG) -> argparse.Namespace:
    """The arguments of a step. Stops with the step's usage if they are not ones it takes."""
    return build(prog)[0].parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
    environment: Mapping[str, str] | None = None,
    downloader: Downloader = download,
    taker: Taker = take_part,
) -> int:
    args = parsed(argv)
    environment = os.environ if environment is None else environment
    try:
        if args.command == "plan":
            return _plan(args)
        if args.command == "fetch":
            return _fetch(args, environment, downloader, taker)
        if args.command == "by-hand":
            return _by_hand(args, environment)
        if args.command == "describe":
            return _describe(args, environment)
        if args.command == "held":
            return _held(args, environment)
        if args.command == "receipts":
            return _receipts(args, environment)
        return _why()
    except Stop as stop:
        print(f"error: {stop}", file=sys.stderr)
        return 2
    except Exception as fault:
        # What a fault says may hold a row or an address, and a log is public.
        # So only its kind is printed, unless a developer asks for the rest.
        if environment.get(DEBUG) == "1":
            raise
        print(
            f"error: fetch stopped on a fault of its own ({type(fault).__name__})", file=sys.stderr
        )
        return 3
