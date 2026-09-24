# packages/pipeline

Builds Burro's data releases. It holds the licence registry and the ingest gate, the code that writes and reads a release folder, the generator of the synthetic release, the step that fetches a publisher's file, and the records of evidence. It is built to [docs/design/contract.md](../../docs/design/contract.md) and [docs/design/london-data.md](../../docs/design/london-data.md); if code and design disagree, change one of them in the same commit.

No real file has been fetched. Every test runs offline, on small made-up files shaped like a publisher's, and says so.

## The command line

- A step of a build is run as `uv run python -m burro_pipeline STEP`. `--help` lists the steps in the order a build takes them: plan, fetch, by-hand, receipts, held, describe, seal, check, coverage. It is the one way in: the Makefile and the hosted workflows run the same commands, and `tests/test_command_line.py` holds both to the arguments each step takes.
- A step is owned by the part that does the work: `fetch/cli.py` or `evidence/cli.py`. It is a `Step` in that file's `STEPS`, with what it does, examples and exit codes. An example is parsed by a test, so it cannot go stale.
- A step's help says whether it reaches a network. Only `fetch` reaches a publisher.
- On standard output a step prints lines of `key=value` that `tools/public_log.py` lets through: step names, registry ids, counts and hashes. Words go to standard error, on one line: what is wrong, what a person can do about it, and the rule's name. Neither holds a row, a key, an address or the name of an area, and neither repeats what the step was handed from a file.
- `tests/walk/` walks the whole of a build on made-up files and breaks each link in turn. A new step joins the walk.

## The registry

- Every step that reads external data starts with `Registry.require(source_id, use)`. No exceptions, including one-off scripts and notebooks.
- Rules live in `src/burro_pipeline/registry/rules.py`, one small function each, listed in `ERRORS` or `WARNINGS`. A new rule needs a case in `tests/test_registry_rules.py` that shows it catching a violation.
- `load()` refuses a registry that breaks an error rule, so the gate never answers from a bad one. Only tools that report problems pass `enforce=False`.
- `Source` is frozen and rejects unknown fields, so a typo in a registry file fails loudly.
- Tests never touch the network. Use the fixture registry in `tests/test_registry_gate.py`.

## Releases

- `write_release` is the only way a release reaches disk. It checks every source a real release cites against the registry, for the use its file needs, before it writes anything. It never writes over a real release.
- `read_release` reads the bytes and leaves all the checking to `open_release` in core, so the pipeline and the API cannot disagree about what a valid release is. Do not add a check here: add a rule in core.
- A refusal is one line: the folder, the file, the row, what is wrong in plain words, and the rule's name. It never repeats a value from the file. A new rule in core needs its words in `MEANING` in `release/read.py`.
- A folder holds the release's files and nothing else. A stray file, a hidden one included, is refused. The one exception is a file named exactly `.DS_Store`: `read_release` leaves it out and never opens it, and `write_release` leaves it where it is. Do not add a second exception without a decision.

## The synthetic release

- `release/synthetic/` reads nothing: no file, no dataset, no network. That is why it has no `Registry.require`, and a test checks its imports. Keep it that way.
- It is unmistakably made up. Every name is invented, every id begins `syn-`, the map is in open sea, and the manifest says `synthetic`. `tests/test_synthetic_release.py` holds a list of real names and fails if one appears.
- That list is London's best-known names and the names that were once used here and found to be real. It is not a gazetteer, and none has been consulted: on 2026-09-23 every name was looked up in one encyclopaedia, which does not cover a small street, a farm or a hamlet. Make a new name from a word that is no part of any place name, and say in the change whether it was looked up, and where. A name that replaces another must sort where the old one did: ids are given in name order, and an id never moves. Add the old name to the list in the same change. A second test looks for every name on it in every file of code and of tests.
- An alias is a name. "Moot Hall" alone is what real buildings are called; "Tallowgate Moot Hall" is not. Give an alias the name of the place or of the borough before it.
- No time in the release is under 2 minutes. `whole_minutes()` in `journeys.py` is the only place a time is rounded; use it for any new time.
- The character of each area is set by hand in `names.py`. The seed only moves figures a little. A test that says which area a spec should find must hold for other seeds too, or it is testing luck.
- It draws only from `Random(seed).random()` and uses no arithmetic that differs between machines: `sqrt`, never a fractional power.
- `data/fixtures/synthetic/` is generated. After any change to the generator run `make fixture` and commit the result. A test fails if the committed files are not what the generator makes.

## Fetch

- `src/burro_pipeline/fetch/` is the only part that may reach a network, and in it only `download.py` and `s3.py`. `tests/fetch/test_only_fetch_reaches_a_network.py` reads every module of the pipeline and of core, and holds the list of packages they may import. A package you add goes on that list, with its reason in the change.
- The gate of fetch is `ask` in `fetch/gate.py`, and `plan`, `fetch` and `by-hand` all go through it. It asks `Registry.require`, and then holds the file to the entry of its source: its page is the entry's own address or one of its evidence addresses, its address is one the entry names for its files under `file_urls`, and nothing that says what the file is names a census table about residents. A publisher serves many datasets from one host, so the host of an address is not enough: `registry/README.md` says what an entry needs for a file of its to be fetched. What such a table is, is asked of the registry's own rule: fetch holds no list of tables and no pattern of its own. Never call `Registry.require` alone in fetch.
- The order is fixed: the gate is asked about every file of the list before anything is asked of a publisher, and again as the first thing done for each file. One refusal stops every download, whether or not the file that was refused was asked for. What arrived is held too, before it is kept: the address a request ended at, the publisher's name for the file, and the names inside a zip and inside every zip it holds. A zip that cannot be looked into is refused with `why=19`.
- A store is of one part: the product, the census tables about residents, or the audit. Only the product's can be named. So a file that is read for the audit, or is a census table about residents, is refused with `why=15`. That refusal is the whole of what is built for them: do not add a way round it.
- A list of files is data, in `fetch/lists/`. It holds the page a person finds a file on, from the registry entry, and the file's own address once a person has found it. Never make an address up. What nobody has checked is named under `unsure`. An edition and a period stay there until a person has read them in the file as a fetch stored it, so the first fetch of a file writes no receipt: `tools/tests/test_guide.py` holds the first list to it, and `docs/data-builds.md`, section 7, says how a receipt is then written and how one that is wrong is put right. An address holds no parameter but those the list names under `url_parameters`, and no other is written in a receipt, and each only with the value the list's own address gives it: a list and a receipt are both committed where anyone reads them.
- A file is kept under its hash and is never written over. A receipt is written last, and only from an edition and a period that the list is sure of. The first receipt of a file stands. A copy of it is kept in the store beside the file, because a hosted run writes to a disk that is thrown away. Before a receipt is written, the copy in the store is read back and compared. If it says something else the file ends `differs`, and the run ends red.
- What goes wrong with one file is said of that file, with a number of its own in `Why`, and the run goes on to the next. `WORDS` says what each number means and what a person can do about it. A fault that is of no one file stops the step with exit code 3.
- The receipt is the one in `evidence/receipt.py`. It holds the address the list gave, as `listed_url`, beside the address the file came from in the end. Fetch defines no record of its own, and works out no key or path of its own: `tests/fetch/test_one_record.py`.
- Where a request ended is held by `hold_where_it_ended`. An address that cannot be read one way only is refused on any host, and an address is another entry's however a server may have read it. Reading an address more ways may refuse more, and never allows more.
- A download never follows a redirect to a host the list does not name, never reads a proxy, a cookie or a login from the machine, and refuses an address that is not public or that holds a letter outside ASCII. A test reaches the loopback address only, behind `loopback_for_tests`.
- One store is named by the environment: a folder or an object store, and never both. Its address and its keys appear in no file, no error and no line that is printed. `fetch`, `by-hand`, `held` and `receipts` say which kind of store they were given, in their first line. `describe` prints JSON, and says it in the last field, `store`.
- A line holds only names that are on the list in `tools/public_log.py`. Add a new name there in the same change. What arrived in place of a file is said as `kind=` and one word of `Kind`, and a test holds the list there to it. A host is never printed by name: `host=` is followed by twelve digits of a hash of it, and `plan --words` prints the same beside each host it knows.
- `describe` prints names from a file's own layout, for a person's own machine. It takes the first full row of a table for the names of its columns, and prints no names where it can tell that row to be data. It cannot always tell, so what it prints is treated as if it held a row: no workflow runs it, and `tools/check_data_workflows.py` refuses one that does.

## Evidence

- `src/burro_pipeline/evidence/` holds the receipt, the method, the evidence row and the claim, the lock, the coverage report, and the rule that no fact is served without evidence. Its `README.md` says what each is for.
- A record is frozen and refuses a field it does not know. Say a record that failed to validate with `in_words(error)`, and never print the error itself: it can name a field that came from a file.
- `seal` reads the commit of the code from the repository it is run in, and refuses a working copy with changes. It looks for the repository in the folder it is given and in every folder above it. `repository.py` reads git's own files to do it and runs no program: no module of the pipeline may run one. It does not look at a file git does not track. A test that seals names a folder that is in no repository, outside the working copy, because the tests may themselves be run in a working copy with changes.
- `seal` then asks `Registry.require` about every file again before it looks at any file. A build reads an input through `Lock.admit` or `Lock.admit_file`, which refuse bytes the lock does not name.
- `check` refuses a method whose module is not a module of the pipeline or of core. It looks for the file and imports nothing.
- The licence registry allows a source for the audit or for the census table, and fetch refuses a file of one until a store of its own is built: `why=15`. `fence.py` keeps such a file out of the product whether or not fetch ever kept it: `seal` refuses its receipt, and `check` names every row that rests on it and every fact served from such a row. Do not add a way round either.
- `check` is not run on a release that is not made up without the lock of its build and the licence registry.
- `check` asks the gate again, of every file a row rests on, for the use the figure is put to: `USE_OF_A_ROW` in `served.py`, and ADR 0016. A row that rests on a file fetched for an internal use, or on one the gate refuses for that use, is named under `input_is_allowed`. A new kind of row needs its use there, or every row of it is named.
- A rule that a refusal or a finding names is a name a public log shows. Add it to `RULES` in `tools/public_log.py` in the same change.
- A figure that is missing has a row too, and a state. Nothing is filled in: a share of the whole is a share of homes only when a count of homes is given.
- `seal` takes the list of the build, named as fetch names it, and holds the folder of receipts to it: every file the list names has its receipt, and no receipt is there that the list does not name. A lock with no input is refused, but for a made-up release.
- `made_up.py` reads nothing and is unmistakably made up: the source `synthetic`, `how: made_up`, no address. A test checks its imports.
- `tests/evidence/fixtures/coverage-syn-2026-09-23-01.md` is generated by `make fixture` and committed. A test fails if it is stale.
