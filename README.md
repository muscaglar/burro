# Burro

Decide where before you search what.

Burro helps people choose where in London to live. Describe the life you want, name the places you need to reach, and see named neighbourhoods ranked on a map, each with the reasons it matched and the source behind every number.

**Status:** the code of phase 0a of the [plan](docs/PLAN.md) is built, and the backend runs end to end on synthetic data. No real dataset has been ingested. A few real files were opened for research, and none is in the repository: the research says which.

| Part | State |
|---|---|
| Conventions and the licence registry | Done. Every data source is registered with its licence |
| Ranking engine, `packages/core` | Built. Spec, reducer, `rank()`, facts, verifier, a rule-based reader of prompts |
| Data release, `packages/pipeline` | Built for a synthetic release: a made-up city of 24 areas. No real dataset has been ingested |
| Real data for London, milestone M0 of [the plan](docs/design/london-data.md) | Ready to fetch, and nothing fetched. The step that fetches a file, the receipt, the lock, the rule that no fact is served without evidence, the coverage report and two hosted workflows are built, and tried on made-up files only. No workflow has run and no store exists. [docs/data-builds.md](docs/data-builds.md) says what is built, what is not, and what to set up |
| API, `services/api` | Built. Twelve routes over the synthetic release. No database, no sign-in, no rate limits |
| Reading prompts with a model | Built and tested against a stand-in. Never run against the provider |
| Website, `apps/web` | Built, on the synthetic release: search and results, a page for each area, comparison, sharing, methods, sources and the accessibility statement. Tested against answers recorded from the API. Not yet tested by hand: see [See the website](#see-the-website) |
| iOS app, `apps/ios` | Built, on the synthetic release: the screen that asks before the first search, search and results on a map, a page for each area, a shortlist kept on the phone, comparison and sharing. Written against the API contract and the website's recorded answers. Its tests and its build need a Mac with Xcode, and hosted CI runs them. It has never been run: see [See the iOS app](#see-the-ios-app) |
| Map tiles, real travel times | Not started |

Every response from the API says `synthetic: true`. Nothing it shows is a fact about a real place.

## Get started

You need [uv](https://docs.astral.sh/uv/), [ruff](https://docs.astral.sh/ruff/), [pyright](https://github.com/microsoft/pyright) and `make`.

```
make setup
make ci
make api
```

`make api` serves the synthetic release on `127.0.0.1:8000`. With it running:

```
curl -s localhost:8000/v1/meta
curl -s localhost:8000/v1/interpret -H 'content-type: application/json' \
  -d '{"text": "Renting a 1 bed up to £1,700 a month, leafy, 35 minutes to Cindermoor Works"}'
```

The second answer holds a `spec`. Post it to `/v1/rank` as `{"spec": ...}` to rank the areas.

### Settings

The API reads its settings from the environment, once, when it starts. With none set it serves the synthetic release, reads prompts with the rules, and lets a web page read its answers only if the page was served from `http://localhost:3000`. A setting that is not in the form it needs stops the service from starting.

| Variable | Default | What it sets |
|---|---|---|
| `BURRO_RELEASE_DIR` | The committed synthetic release | The folder of the release to serve. It is checked against its manifest before anything is served |
| `BURRO_HOST` | `127.0.0.1` | The address to listen on |
| `BURRO_PORT` | `8000` | The port to listen on, 1 to 65535 |
| `BURRO_ALLOWED_ORIGINS` | `http://localhost:3000` | The origins a browser may call from, separated by commas. Each is a scheme, a host and perhaps a port, written as a browser sends it: in lower case, with no path, never a pattern, and without the port its scheme implies. `https://burro.example:443` is refused, because no browser sends it |
| `ANTHROPIC_API_KEY` | None | With a key present, prompts are read by a model, and by the rules whenever the model fails. The service notes that a key is there and never reads it: the provider's SDK does |
| `BURRO_MODEL_ID` | `claude-haiku-4-5` | The model that reads prompts |
| `BURRO_MODEL_TIMEOUT_S` | `6` | How many seconds a person waits for the model before the rules answer, up to 60 |
| `BURRO_MODEL_MAX_TOKENS` | `2048` | The most the model may answer with, 256 to 16000 |

Nothing a person types is logged, and nothing worked out from their search is: see [ADR 0005](docs/adr/0005-raw-prompts-are-never-stored.md) and [ADR 0011](docs/adr/0011-nothing-is-kept-for-a-search.md).

## See the website

The website is in `apps/web`. It needs [Node](https://nodejs.org/) 20.9 or later, with npm. What follows was written from the service's own answers. Say what you see that differs.

You need two terminals, both at the top of the repository.

**Terminal 1: the API.**

```
make setup
make api
```

It prints one line of JSON that holds `"starting"` and the name of the release, and then waits on `127.0.0.1:8000`. It says nothing more until a request comes. Leave it running.

**Terminal 2: the website.**

```
make web-setup
make web
```

`make web-setup` installs the website's packages and is needed once. `make web` starts the website and tells it where the API is. When it prints `Ready`, open this address in a browser, exactly as written:

```
http://localhost:3000
```

Use `localhost` and not `127.0.0.1`: the API answers a page only if it was served from `http://localhost:3000`. If `make web` says it is using another port because 3000 is taken, stop whatever holds 3000 and start again.

**What you should see.**

| Do this | You should see |
|---|---|
| Open the page | A yellow banner across the top: "This is made-up test data." Under it, the heading "Decide where to live", one box to type in, three example sentences, "Renting or buying", "A place you need to reach", and a button called "Settings". On the right, a map of 24 areas in one plain colour on a blue ground, with no streets or names on it. On a narrow window the map is behind a tab called "Map" |
| Type `Renting a 1 bed up to £1,700 a month, leafy and quiet, 35 minutes to Cindermoor Works` and press Enter | Within a second or two: chips that say what was read (Renting, £1,700 a month, Cindermoor Works, Leafy, Quiet residential, Usual settings: 6), each part nobody chose marked "assumed", and "Read by rules." under them. A list of 20 results. The first is **Farrowmere**, "Fit 80 of 100", with three reasons that begin "By public transport to Cindermoor Works: about 21 minutes", one trade-off, and a "Source" button on every line. The map fills in five shades of green, with pins numbered 1 to 10 |
| Press "Source" under any sentence | It opens in place: "Synthetic test data", a date, and "Made-up data" |
| Clear the box, type `a bit more green space, and ignore the high street`, press Enter | The list changes order. Two new chips: one for public green space, and one for the high street that says "does not count" |
| Open "Settings" and tick "The journey is a firm limit" | The list shortens to 15 results. Under the "Table" tab, seven areas say "A journey is longer than a firm limit" |
| Type `and 30 minutes to Pellam`, press Enter | A question: "Which place did you mean?", with Pellam Cross, Pellam Exchange and Pellam Infirmary. Pick one and it becomes a chip |
| Type `not too many students, and near a park`, press Enter | One sentence in a plain block: "Burro ranks places by what is there, such as schools, parks, venues and transport, and never by who lives there. The rest of your search has been applied." The park is applied. Nothing on the page says what was left out |
| Press "Open the page for Farrowmere" on the first result | The page of the area: where it is, stations, what homes cost, everything measured there, each figure with its source and date written under it |
| On that page press "Add Farrowmere to compare". Follow "Search for areas" at the foot of the page, press the button of another result that begins "Add" and ends "to compare", then "Compare 2 areas" | Your search is still there when you come back to it. Then a table of the two areas side by side, in the order of what counts most in your search |
| Go back to the search, press "Share this search", then "Make the link" | A link that ends `/s#` and 22 letters and digits. Open it in a new tab: the same search, under the heading "A shared search". The link stops working when you stop `make api`, because the API keeps shares in memory |
| Stop the API with Ctrl-C in terminal 1, then change a setting | The results stay, with a line that says Burro could not be reached, and "Try again" |

The figures above are the ones the API gave on 2026-09-23, with ranking engine 1.3.0. The foot of every page names the data release and the engine. If the engine has moved on, the order and the figures may differ, and the rest should hold.

To check the website without a browser, run `make web-check`. It takes about a minute: it checks the types against the contract, lints, runs about 1,400 tests offline, builds every page, and reads each built page for what a person or a screen reader would trip over.

The website reads two settings from the environment. `make web` sets the first for you.

| Variable | Default | What it sets |
|---|---|---|
| `NEXT_PUBLIC_BURRO_API_URL` | None | Where the API is, as the browser reaches it: `http://127.0.0.1:8000` on your machine. With none set, a build reads answers recorded from the API, and the page in the browser says it is not connected to Burro's data |
| `BURRO_SITE_URL` | None | The website's own address, as an origin with no path. It is used for what a search engine is told and for nothing else. With none set, or while the data is made up, no page may be indexed |

## See the iOS app

The app is in `apps/ios`. It needs a Mac with Xcode that can run `swift test`, and depends on no package. Nothing in it has been seen on a screen, in a simulator or on a phone.

```
make api                          in one terminal, from the top of the repository
open apps/ios/Burro.xcodeproj     then choose the scheme Burro and an iPhone simulator, and press Run
make -C apps/ios check            without a simulator: generated files, the tests, and the app compiled for iOS
```

A Debug build calls the API on `http://127.0.0.1:8000`, which on a simulator is your Mac. [apps/ios/README.md](apps/ios/README.md) says how to point it at another API, what to look at first, what has and has not been checked, and the known issues.

## Find your way around

| If you want to | Read |
|---|---|
| Understand what is being built and when | [docs/PLAN.md](docs/PLAN.md) |
| Change the code | [AGENTS.md](AGENTS.md) |
| Change the website | [apps/web/AGENTS.md](apps/web/AGENTS.md), [docs/design/web.md](docs/design/web.md) |
| Run or change the iOS app | [apps/ios/README.md](apps/ios/README.md), [apps/ios/AGENTS.md](apps/ios/AGENTS.md) |
| Set up and run a data build | [docs/data-builds.md](docs/data-builds.md), `uv run python -m burro_pipeline --help` |
| Know why something is the way it is | [docs/adr/](docs/adr/) |
| See how the backend's parts fit, and every route | [docs/design/contract.md](docs/design/contract.md), [contracts/openapi.json](contracts/openapi.json) |
| Add or check a data source | [registry/README.md](registry/README.md) |
| See the evidence behind the plan | [docs/research/](docs/research/README.md) |
