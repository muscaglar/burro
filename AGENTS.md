# Burro

Burro helps people find an area of London: to rent in, to buy in, or to visit. They say what is important to them and name the places they must reach; Burro ranks named neighbourhoods on a map and shows its working. The full plan is in [docs/PLAN.md](docs/PLAN.md).

This file is for anyone changing the code, human or agent. Keep it under 150 lines.

## Commands

```
make setup            install dependencies
make ci               everything hosted CI checks: run this before you say you are done
make test ARGS="-k gate"
make test ARGS="-m full"   the generated tests in full, which make ci samples
make format           fix lint and formatting
make registry-check   validate the licence registry
make fixture          rebuild the synthetic release in data/fixtures/synthetic
make api              run the API on 127.0.0.1:8000, on the synthetic release
make openapi          rewrite contracts/openapi.json after a route or a record changes
make eval-reader      score the sentence reader against its cases, as a test of make ci does. It fails if one is read backwards
make web-check        everything the website is held to: run this before you say a change to apps/web is done
make web              run the website on localhost:3000, with `make api` running in another terminal
make web-types        rewrite the website's API types after contracts/openapi.json changes
make web-record       record the API's answers again for the website's tests
make -C apps/ios check   everything the iOS app is held to: run this before you say a change to apps/ios is done
make plan ARGS="--list m1 --words"   ask the licence registry about every file of a list. No network
make fetch            a step of a data build. So are by-hand, describe, seal, cells, preview and
                      coverage. With no ARGS a step prints its help and does nothing more
make preview ARGS="--release-id ID --built-at TIME --out data/releases"
                      build the preview release of a first build, from the store. No network
make desk             start the review desk and its panel on 127.0.0.1:8765, and print the address to open
make desk-check       everything the review desk is held to: run this before you say a change to tools/desk is done
make desk-fill ARGS="--from FOLDER --data data/raw/desk"   fill the desk's queues from a draft folder
uv run python -m burro_pipeline draft --out FOLDER
                      make the whole draft of London's areas, from the store. No network
make help             list every target
uv run burro-release check FOLDER    say whether a folder is a valid release, and why not
uv run python -m burro_pipeline --help    every step of a data build, in the order a build takes them
```

You need `uv`, `ruff`, `pyright` and `make` on your PATH. Tests run offline. A whole run of `make ci` on a hosted runner stays under five minutes, and the tests alone stay under two minutes on a machine of your own: a default, taken on 2026-09-25, and the founder's to overturn. A generated test draws a fixed sample in `make ci` and runs in full under the marker `full`. `make ci` runs the tests side by side, split by file over one process for each core. So a test counts on nothing another test left behind, binds no fixed port and writes no fixed path: one that does either is refused, by `conftest.py` at the root. It also sets how git is started, by a test or by the code it tests: git does no upkeep of its own, and reads no settings of the machine or of the person. And it takes out of the environment what a hosted runner sets, so that a test behaves on a runner as it does anywhere: a test of what a tool does on a runner names a file under its own folder. `make test` runs them plainly, in one process, and `make test-split` as `make ci` does. See ADR 0020. A few modules of tests read real files, and are skipped where `BURRO_STORE_FOLDER` names no store. The website needs Node 20.9 or later and npm, and `make web-setup` once. Its check is not part of `make ci`: hosted CI runs it as a job of its own. The iOS app needs a Mac with Xcode that can run `swift test`. Its check is not part of `make ci` either: hosted CI runs it in the job `ios`. What its generator makes of the contract is held in `make ci`, which needs no Mac. The review desk needs no package. Its page is tested with Node 20 or later, in the job `desk`, and `make ci` runs the page against the desk where Node is on the PATH.

## Where things live

| Path | What it is |
|---|---|
| `registry/sources/` | Every dataset Burro may touch, with its licence, one file per topic. The ingest gate reads it |
| `packages/pipeline/` | Builds data releases. Owns the registry code, the step that fetches a publisher's file, the records of evidence and the lock of a build, the geography and the measures of a first build, the step that works journeys out from a timetable, and writes and reads a release folder. Its command line has one step for each |
| `packages/pipeline/src/burro_pipeline/fetch/lists/` | The files each build takes, as data: the registry entry, the page, and the address once a person has found it |
| `data/fixtures/synthetic/` | The synthetic release: a made-up city, generated by `make fixture`. It describes no real place |
| `data/fixtures/residents/`, `data/fixtures/income/` | The made-up count of who lived in the made-up city, and the made-up estimate of household income, generated by `make fixture`. Neither is part of a release. Each is shown on an area's page and never ranked on |
| `packages/pipeline/src/burro_pipeline/areas/` | The draft of London's named areas: names and seeds, every output area given to an area, the flags, the layers behind a border, and what the review desk is handed. A draft is made by method and checked by nobody, and is written outside what git tracks |
| `data/receipts/` | One receipt for each publisher's file that was fetched: its address, its hash and its dates, and no row of it. Written by fetch, never edited |
| `data/releases/` | Where a build writes a release. Git ignores it: what is there is made from publishers' files |
| `data/approved/` | The lock of each release of London the founder approved: ids, hashes and counts, and no figure. An image carries a release only if its lock is here. Only the founder commits one, and a release itself is never committed. See ADR 0030 |
| `packages/core/` | The ranking engine: spec, reducer, `rank()`, facts, verifier, the reader of sentences, and the vibes with their bands, likeness and the portrait. Pure Python, no IO |
| `services/api/` | The HTTP API: FastAPI over one release held in memory. No database, unless accounts are turned on: then one file of SQLite, for accounts and what they keep, and nothing of a release or of a call (ADR 0045). With accounts off no route of them exists and no file is opened. Holds the only model key, and the secrets of accounts where they are on. [docs/design/accounts.md](docs/design/accounts.md) is the design of accounts, and [docs/design/accounts-threats.md](docs/design/accounts-threats.md) says what could go wrong and what holds it |
| `contracts/openapi.json` | The API contract the clients are generated from, at version 3. Generated by `make openapi`, never edited by hand |
| `apps/web/` | The website: Next.js, TypeScript, plain CSS. Its types are generated from the contract, and its tests run against answers recorded from the API. Its look is the map of a gentle game (ADR 0033): its drawings are text under `apps/web/art/`, its pictures are made from them, and its two faces are files of its own under `apps/web/public/fonts/`. A result shows each thing that was asked for as a name and a gauge, and its working holds every source (ADR 0046). Its own words are written for a person who has never seen Burro (ADR 0038, rule 14). Its own `AGENTS.md` has its rules |
| `apps/ios/` | The iPhone app: SwiftUI, Swift 6, no package. `BurroKit` holds everything but the entry point and is tested on a Mac. Its models are generated from the contract, and its tests run against the website's recorded answers. Its generated files are in step with the contract, and its tests that name a figure with the answers as they are now recorded. Its colours and words are held to `apps/ios/website/`, a copy of the website's files as they stood on 2026-09-26, and not to the website, until the app is given the look (ADR 0037). Its own `AGENTS.md` has its rules |
| `evals/` | The cases the sentence reader is scored against. Its own `AGENTS.md` has its rules |
| `tools/` | Repository checks, and what keeps a row, a key and the store's address out of a public log. Standard library only |
| `tools/desk/` | The review desk: where a person looks at data and decides a name, a border, a quotation or a rating. Its panel is where a person looks through a release, flags what looks wrong, and renames or adjusts what is worked out: a change is a line of a file, and a build that is given the file applies it. One server on the person's own machine, plain files of decisions under `data/raw/`. [docs/desk-guide.md](docs/desk-guide.md) is its guide, [docs/design/desk.md](docs/design/desk.md) and [docs/design/panel.md](docs/design/panel.md) are its designs, and its own `AGENTS.md` has its rules |
| `.github/workflows/data-*.yml` | The hosted workflows that fetch and build data, and check what the store holds. Started by hand, on `main`, and approved by the founder. `tools/check_data_workflows.py` holds them to their rules |
| `docs/data-builds.md` | For the founder: where data builds stand, what to set up, and how to run one |
| `docs/design/london-data.md` | The plan for real, cited data for all of London. Six designs stand behind it |
| `docs/README.md` | Where to look: the way in to every guide. From it, `docs/architecture.md` draws the whole, `docs/history.md` says how Burro got here, and `docs/PLAN.md` has the scope and the roadmap |
| `docs/design/contract.md` | How core, the release and the API fit: every record, rule and route. Code and contract change together |
| `docs/design/web.md`, `docs/design/look.md`, `docs/design/words.md` | The website: every page, state and control, and what the contract does not yet give it. Its look: what is drawn where, where each part is changed, how each is turned down in one line, and what is still open for the founder. And its words: who reads them, how a sentence is written for them, and what no sentence may loosen |
| `docs/design/vibes.md`, `docs/design/slice-1.md` | The design of the vibes, and the account of the first slice of them: what was built, what was found, and what is the founder's to decide |
| `docs/adr/` | Decisions and their reasons. Read the relevant one before changing course |
| `docs/research/` | Evidence behind the plan. A dated snapshot, not a source of truth |

Planned, not yet created: `map/`. Create a folder when it has real content, not before.

## How the backend fits together

```
words ──► interpreter ──► typed edits ─┐
sliders and chips ──────► typed edits ─┴─► reducer ──► spec ──► rank(spec, release) ──► facts ──► checked sentences
```

- `burro_pipeline → burro_core ← burro_api`. The pipeline and the API never import each other. They meet at the release folder, and `open_release` in core is the only judge of one.
- The server keeps nothing for a search, unless a person who has signed in keeps it. The client holds the spec and sends it again. A spec is stored in a share, and in a search that a person keeps under their account: the spec, and never the words. A search knows nobody, signed in or not. Accounts are off until one setting turns them on, a person signs in by a link sent by email, and nothing that worked without an account asks for one. See ADR 0011, 0043 and 0044.
- With no model the rules read the prompt, and every route works. A key alone turns no model on: a provider reads only when it is named, its key is present, its terms are accepted and its model is one the adapter was fitted to (ADR 0019, ADR 0023). DeepSeek never reads what people type. A model that is slow, capped or broken is answered for by the rules, never by a 5xx.
- The model proposes, code checks, and the website applies what is offered and asks nothing. The rules read first, and a model is asked only of what they left unread. The service applies nothing a model reads: it offers it, with Burro's guess marked, and the guard says what may be offered at all. The website takes the way the service names or guesses, and the gentler where it does neither: a limit as a guide, never as a firm one. It shows each thing as a chip that can be taken off, and what nobody said says "assumed". It takes nothing the service says waits for a person: what counts who lives somewhere, recorded crime that the words do not name, and what a decision holds to be offered and never applied. Nor, where the words give no way of it, a rule that leaves areas out or a thing that runs two ways. What it left it names in a line. A model never ranks, scores or describes a place. See ADR 0012, as amended on 2026-09-26, for what that gives up.
- The rules apply a prompt only when the whole of it is a plain list of wishes. Of any other they apply nothing: the API returns what was noticed as suggestions, each with its ways, and a client says which it takes. It marks the way the words give as its guess, offers no way for more of a thing the words turn round, and says of each offer whether the words name what it counts and whether it waits for a person. It also says where the words stand that nothing was made of, as offsets and never as words. A time in hours is read as minutes. An amount by the week is offered as what it comes to by the month, and never applied. What a home cannot hold is said, with nothing to choose. See ADR 0012.
- A vibe is a recipe over measured parts. What is served of one is a band, one of five, with its parts and what it cannot see. The vibes are the release's. Gritty is one vibe, a scale from Polished to Gritty that counts recorded crime, and a release of London carries it. Works and warehouses is a part of it, and no vibe of its own there. Recorded crime counts only when a person asks for it by name, and to type "gritty" is to ask. See ADR 0013.
- A band rests on the parts of a recipe that the release holds, and says what share of the recipe that is. Under 60 in 100 there is no band.
- An area with no figure for a thing that was asked for stands below every area that has one, and says which figure it lacks. It is never left out for it, and never scored as nought. A usual setting that nobody chose moves no area. See ADR 0024.
- A limit is firm only where the words make it one. "Max", "up to", "at most" and "no more than" make a budget firm. "At most", "max", "no more than" and "within" make minutes firm, and a range of minutes is firm at its longer end. Core holds both lists, and the guard on a model reads them.
- A search is to rent, to buy or to visit. A visit holds no budget, no number of bedrooms and no kind of home: an edit that would give it one is turned away, what homes cost is no part of how it is ranked or of what is said of an area, and a release is asked for no cost to serve it. See ADR 0041. A cost is a range, or one number: a median of what sold. A build of London works the median out from the sales, for each kind of home, and says how many sales it rests on: under 10 give no figure. A budget is held against the upper end of a range, and against a median. A firm budget leaves an area out on a median only where the median is over it by more than a quarter, which core's `FIRM_BUDGET_MARGIN_PERCENT` holds: about half of what sold went for less than the median. See ADR 0021.
- The tests and the service run on the synthetic release unless a release is named. See ADR 0010. Each nested `AGENTS.md` has the rules of its own package.
- Fetch is the only step that may reach a network, and it asks the registry first. Every other step reads what is in the store, by its hash. See ADR 0015.
- A release says two things of itself, and every response carries both: `synthetic`, that its figures are made up, and `preview`, that it is not finished. The first real build is a preview and is not made up. What it has not measured is not in it. See ADR 0017.
- A release that is not made up is served only with what it was built with beside it: its evidence, its lock and the hashes of the three. `open_served` in core holds them, for the service and for `burro-release check` alike. A release with no journey, cost or station is a preview, whatever it says. See ADR 0018.
- An area of a build is a census area under its publisher's label. Given the draft of names, it bears the name of the drafted neighbourhood that holds most of its output areas, with the label beside it, and says that the name is a draft until a person has decided it at the review desk. See ADR 0025.
- A wish for what the release holds for no area is turned away as `not_in_release`: a vibe no area has a band for, a budget where no home of that kind has a cost, a journey where no place is named. Route 1 names what was asked for and is not there, and route 11 says what the release holds (`holds`, `recipes`).

## Rules

These are the product's promises. Most are enforced by tests. Do not weaken a rule to make a change pass; raise it instead.

**Data and licences**
1. No dataset is downloaded, read or shipped unless the licence registry allows that use. Ingest code calls `Registry.require(id, use)` first. Only `approved` sources may reach a data release; a gated or held source may be read for the internal uses it lists.
2. Never mark a source `approved` without a primary-source link in `evidence_urls`. If you are unsure, use `gated` and say what would settle it.
3. OpenStreetMap is for the basemap and the routing network only. It never enters the gazetteer or scoring, and OSM comparison never changes an individual record. See ADR 0004.
4. Banned sources are in the registry with the reason. They include Google Places and Street View, the property portals and the VOA rating list. Do not look for a way round a ban.

**Ranking and the LLM**
5. Ranking is a pure function of the preference spec and a data release. The model never ranks, scores or describes a place from memory. See ADR 0002.
6. Every number and proper noun the product shows about a place must trace to a stored fact with a source and a date. Where the source is shown may change, and that it can be reached may not: on a result of the website the key of every source stands under the working of the result, one press away, since the founder asked for less on a result (ADR 0046).
7. Missing data is never filled in. Drop the feature for that area and say so. A number that is not known is `null`, never zero. One thing is estimated, and says so wherever it is shown: a journey, where no timetable is held. See ADR 0027.

**Fairness**
8. Rank places. Of residents, only their age and the make-up of their households may feed ranking, a tag or a vibe, from the census, and only towards more of what a figure counts. Nothing else that describes who lives somewhere may, and nothing reads a wish for fewer of any group of people. Ethnic group, religion, country of birth and household income are shown on an area's page and never ranked on (ADR 0014, 0028). Stop and search data is never read. Protected-characteristic data sits under `audit`, which the gate keeps out of scoring and no audit reads, or `residents`, which it lets into the census table on an area's page, and into scoring for the tables of age and household composition alone. See ADR 0006.

**Privacy**
9. Raw prompt text and destination strings are never written to a log, an error report or a database table. Nor is a place id, a fact id or a share id: each says, or unlocks, where someone works. Nor is a hash of a spec, or anything else worked out from one: the plain hash can be matched to a workplace by trying specs, and a hash under a key confirms a guess for whoever can read the log. Log counts, latency and status, and of accounts what happened and how it ended, each a word of a closed list: never an address of email, the token of a link, a session, the id of an account, of a session or of a search that is kept, or the address of a client. A spec's hash goes only in a response. A spec is stored only in a share and in a search that a person who has signed in chose to keep, and a place id is in a table only inside such a spec. The name of a place is in a table in one place: the name of a search that is kept, which code makes, holds the release's name of each place its journeys lead to, beside the spec and under the same account. Typed text travels in a `POST` body, never in a URL, and so does an id of accounts. See ADR 0005, 0011, 0043 and 0044.

**Repository**
10. No private hostnames and no credentials in any tracked file. `make public-only` checks four things: URLs with credentials in them, every URL in a package file (manifest, lockfile, settings, Dockerfile, CI workflow), any mention anywhere of a package host that is private to the machine it runs on, and a key: a setting named for a secret with its value beside it, or a key of a provider Burro is fitted to. It is still no secret scanner, so the rest is on you.
11. No secrets in the repository. Do not read `.env` files.
12. Every new dependency needs a one-line reason in the pull request. Prefer the standard library. No package that ships a native binary it needs to run; see ADR 0008.

**Synthetic data**
13. Synthetic data is unmistakably synthetic: made-up names, and a `synthetic` flag on every response, errors included. No figure from it is ever presented as a fact about a real place. See ADR 0010.

**Words**
14. The words of the website that a visitor reads are written as [docs/design/words.md](docs/design/words.md) says: for a person who has never seen Burro, in whole sentences that are joined, with a word of the product explained where it is first used. No rule above is loosened so that a sentence reads well: no place is given a verdict, no figure is rounded or parted from its unit and its date, and what is not known is said to be not known. What the service writes, the website shows as it came. See ADR 0038.

## How to work here

- Small, reviewable changes. One concern per commit. Write the test that would have caught the bug, then fix it.
- Tests are named for the behaviour they protect: `test_gated_source_is_refused_with_its_reason`. Match the code around you. Comments explain why, not what.
- If a decision changes, add or amend an ADR in the same change. If something here is wrong or out of date, fix this file in the same change.
- Generated files are committed and never edited by hand: `contracts/openapi.json`, `data/fixtures/synthetic/`, `data/fixtures/residents/`, the coverage report `make fixture` writes beside the pipeline's tests, and the website's pictures and the list of their names, `apps/web/public/art/` and `apps/web/src/lib/art/names.ts`, which `npm run gen:art` makes in `apps/web` from the drawings. A test fails when one is stale. The app's copy of the website's files, `apps/ios/website/`, is committed and never edited either, and nothing makes it again.
- The website is generated from the backend in two places, both committed: its types, from the contract, and the answers its tests run on, recorded from the API. A test of `make ci` records again, and fails where what is committed is not what the service answers. After a change to a route, a record or the ranking, run `make openapi`, then `make web-types` and `make web-record`, then `make web-check`.
- Before you say a change to the backend works, drive it. `.claude/skills/verify/SKILL.md` says how.

## Adding a data source

1. Read the publisher's licence page. Save the link.
2. Add a `[[source]]` entry to the file for its topic under `registry/sources/`. See `registry/README.md` for the fields.
3. Run `make registry-check`.
4. Only then write the ingest step, starting with `Registry.require`.

## When you are unsure

Stop and ask when a change would: touch one of the rules above, add a paid service, add a data source whose licence is unclear, or send user text anywhere new. Otherwise make the reasonable call and say what you chose.
