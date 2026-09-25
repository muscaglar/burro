# Burro

Decide where before you search what.

Burro helps people choose where in London to live. Describe the life you want, name the places you need to reach, and see named neighbourhoods ranked on a map, each with the reasons it matched and the source behind every number.

**Status:** the code of phase 0a of the [plan](docs/PLAN.md) is built, and the backend runs end to end on synthetic data. The first real files of London have been fetched, and a preview and a draft of the areas were made from them. Neither is served, and neither is in the repository. A few real files were opened for research before that, and none is in the repository: the research says which.

| Part | State |
|---|---|
| Conventions and the licence registry | Done. Every data source is registered with its licence |
| Ranking engine, `packages/core` | Built, at version 1.12.0. Spec, reducer, `rank()`, facts, verifier, and a rule-based reader that applies a plain prompt and asks about any other. It answers a whole first search part by part: a journey given as a range of minutes, a home, a word for a smart area, which it offers as of the place in two ways, and a word for character, which it offers three ways. "Max £400k" and "within 40 minutes" are firm limits, which leave areas out. Thirteen vibes, each a recipe over measured parts and shown as one of five bands, of which two count who lived in an area at the census, by their age or their households, and are only ever offered, the areas most like an area, and the portrait of an area. An area with no figure for what was asked for stands below every area that has one. A cost is a range, or one number where its publisher gives no range |
| Data release, `packages/pipeline` | Built for a synthetic release: a made-up city of 24 areas. The tests and the service run on it unless a release is named |
| Real data for London, milestone M0 of [the plan](docs/design/london-data.md) | Built. The first hosted fetch ran on 24 September 2026, into the bucket. The step that fetches a file, the receipt, the lock, the rule that no fact is served without evidence, the coverage report and the hosted workflows are built. [docs/data-builds.md](docs/data-builds.md) says what is built, what is not, and what to set up |
| A first build of London, milestones M1 and M2 | A preview. The step `fetch` was run outside a workflow, into a store that is a folder, and 87 receipts are in `data/receipts/`. From those files a build makes every part of Greater London as one of the statistics office's 1,002 areas, with 100 measures. They are nitrogen dioxide, transport noise and main roads; homes per hectare, flats, homes built before 1919 and since 2000, and addresses with private outdoor space; public parks and gardens, the nearest park, large park and play space, gardens, woodland and water close by; primary schools within reach; the nearest station, town centre, food shop, GP practice and pharmacy, each as a straight line; the nearest station of the Underground or the DLR, of the Overground or the Elizabeth line, and of National Rail or the trams, and the routes and the stops of buses within 400 m; places to eat and drink, cultural venues, cafes, gyms, and pubs and bars, each as a count that is shown and as a rate for each 1,000 homes that is ranked on; homes near a cluster of pubs and bars; land used for industry, for storage and for transport other than roads; conservation areas and listed buildings, and how much of the nearest high street lies in a conservation area; recorded criminal damage and recorded anti-social behaviour, for each 1,000 homes a year; what homes sell for, the share of homes in the higher council tax bands, and how far what homes sold for has risen over five years and over ten; residents of two ages and households of two kinds, as shares, at the census of 2021; and the chains of grocers, gyms and coffee, by a table of tiers that is the founder's: the places of each tier within reach and the nearest of each, the mix of tiers, the nearest place of each of 27 chains, and the share of places to eat and drink that belong to no chain. Five measures are worked out and left out, each by the name of its rule. The nearest place of two chains has a figure for no area. The size and the shape of a town centre and what there is to do in parks wait on the founder. No measure is held back: private outdoor space was, for want of an audit that was dropped on 2026-09-25. Pubs and bars are counted from the file of places, which holds fewer of them toward the edge of London, and no person has looked at a sample of it. Core places areas on each of the fourteen vibes: Leafy, Going out, Quiet streets, Age of buildings, Everyday on foot, Parks close by, Houses or flats, Food and drink, Family amenities, Well connected, Gritty, Family area, Young professionals and Village feel. Village feel is served as a rough guide: no try at it reached the founder's bar, so it says wherever it is shown that it is less sure than the other vibes, and why, and it is never taken without a press of its own (ADR 0013, as amended on 2026-09-25). It holds what each kind of home sold for, worked out from the sales of three years, and names the 641 stations of London as places to reach. It holds no journey time and no rent: a journey by public transport is estimated from distance, and is said to be an estimate. Household income is written beside it, to be shown on the page of an area and never ranked on. Given the draft of names, each area bears the name of a neighbourhood, which says that it is a draft, with the statistics office's label beside it. It says it is a preview, and it is not served. Sections 15 to 31 of [docs/data-builds.md](docs/data-builds.md), and [the page on the first vibes](docs/research/data/first-vibes-on-london.md) |
| Named areas of London, milestone M3 | A draft, made by method and checked by nobody. One command makes the names and the borders of the areas from publishers' files, with what a person must look at first. Nothing of it is committed. It waits for the review desk |
| The review desk, `tools/desk` | Built. One server and two pages. At the queues a person decides a name, a border, a quotation or a rating. At the panel a person looks through a release, flags what looks wrong, and adjusts a recipe, a name or the table of brands, which a build then reads from a plain file. Tested on the made-up city. [The guide](docs/desk-guide.md), [the queues](docs/design/desk.md), [the panel](docs/design/panel.md) |
| API, `services/api` | Built, to version 2 of the contract. Twelve routes over one release: a ranking, where each area sits on each vibe, the areas most like one area, and what the reader noticed in a sentence it did not apply. Every answer says whether its data is made up and whether its release is a preview. No database, no sign-in, no rate limits |
| London built in a hosted run, and served | Built, and started once: the first hosted build of London was started on 25 September 2026, and the first of its two builds passed. A workflow builds London from the store in a bucket, on two runners, keeps the release in a bucket of its own where the two builds are the same byte for byte, and shows its lock. A release is served only once the founder has committed its lock under `data/approved/`: the image of the API then carries it, and holds every file to the lock as it is built. With no lock the image carries the made-up city, as before. No lock is committed, so no release of London is approved, and no image has been built with London. "London, from the bucket to the service" in [docs/data-builds.md](docs/data-builds.md), and [deploy/README.md](deploy/README.md) |
| On the internet | The website on Vercel and the API on Fly.io, first deployed on 25 September 2026, with the made-up city. Every answer says that its data is made up, and no page may be indexed. There is no domain yet, and no release of London is served. [deploy/README.md](deploy/README.md) |
| Reading prompts with a model | Built and tested against a stand-in. Never run against the provider |
| Website, `apps/web` | Built, on the synthetic release: search and results, a page for each area, a page of every vibe, comparison, sharing, methods, sources and the accessibility statement. It shows a banner on a preview, and a notice and no figure where an answer is of another kind of data than the page was built on. Tested against answers recorded from the API, and walked in a browser window at two sizes. Not yet seen on a real phone or with a screen reader: see [See the website](#see-the-website) |
| iOS app, `apps/ios` | Built, on the synthetic release: the screen that asks before the first search, search and results on a map, a page for each area, a shortlist kept on the phone, comparison and sharing. Written against the API contract and the website's recorded answers. Its tests and its build need a Mac with Xcode, and hosted CI runs them. Its generated files are in step with version 2 of the contract, and its tests that name a figure with the answers as they are now recorded. It draws an offer in its four parts and takes a choice by its id, as the website does. It asks for no census. It has never been run: see [See the iOS app](#see-the-ios-app) |
| Map tiles, real travel times | Not started |

On the synthetic release every response from the API says `synthetic: true`, and nothing it shows is a fact about a real place. On a preview every response says `preview: true`.

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
  -d '{"text": "Renting a 1 bed for about £1,700 a month, leafy, 35 minutes to Cindermoor Works"}'
```

The second answer holds a `spec`. Post it to `/v1/rank` as `{"spec": ...}` to rank the areas.

A sentence is applied only when the whole of it is a plain list of wishes, with a budget and a journey if it has them. Any other is not applied. Its answer holds `suggestions`, each with the choices a person may press, and `unread`, which says where the words stand that nothing was made of. Try `{"text": "Pubs are so noisy"}`.

The release that is served carries Gritty, the one vibe that counts recorded crime, and `/v1/meta` says so as `gritty_variant: b`. To serve a release that holds no recorded crime, and carries every vibe but Gritty:

```
uv run burro-release build-synthetic --gritty a --out /tmp/burro-releases
BURRO_RELEASE_DIR=/tmp/burro-releases/syn-2026-09-23-02 make api
```

### Settings

The API reads its settings from the environment, once, when it starts. With none set it serves the synthetic release, reads prompts with the rules, and lets a web page read its answers only if the page was served from `http://localhost:3000`. A setting that is not in the form it needs stops the service from starting.

| Variable | Default | What it sets |
|---|---|---|
| `BURRO_RELEASE_DIR` | The committed synthetic release | The folder of the release to serve. It is checked against its manifest before anything is served |
| `BURRO_HOST` | `127.0.0.1` | The address to listen on |
| `BURRO_PORT` | `8000` | The port to listen on, 1 to 65535 |
| `BURRO_ALLOWED_ORIGINS` | `http://localhost:3000` | The origins a browser may call from, separated by commas. Each is a scheme, a host and perhaps a port, written as a browser sends it: in lower case, with no path, never a pattern, and without the port its scheme implies. `https://burro.example:443` is refused, because no browser sends it |
| `BURRO_MODEL_PROVIDER` | None | Which provider's model reads prompts: `gemini`, `openai`, `deepseek` or `anthropic`. There is no default, and a key alone turns nothing on. A model reads only when the provider is named, its key is present, its terms are accepted, and the model is one its adapter was fitted to. DeepSeek never reads what people type. Otherwise the rules read, and the service says why as it starts. [docs/design/models.md](docs/design/models.md) has the whole of it |
| `BURRO_MODEL_TERMS_ACCEPTED` | None | The same provider's name. It says that whoever runs the service has read its terms and taken them on |
| `BURRO_MODEL_ID` | The provider's smallest fitted model | The model that reads prompts. One the provider's adapter was fitted to, or the rules read |
| `BURRO_MODEL_SENDS_SETTINGS` | Not set | `yes` sends the search settings to the provider with the words. Otherwise the words go alone |
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
| Open the page | A yellow banner across the top: "This is made-up test data." Under it, the heading "Decide where to live", one box to type in, "Start from a word" with seven words and "More words", "Renting or buying", "A place you need to reach", three example sentences, and a button called "Settings". On the right, a map of 24 areas in one plain colour on a blue ground, with the names of the areas where there is room and no streets. On a narrow window the map comes after the form |
| Press "leafy" | A card opens under the words: what Leafy means, what it is made of and what it cannot see. The map is coloured in five bands. Nothing is sent. "Add to my search" ranks the areas |
| Type `Renting a 1 bed for about £1,700 a month, leafy and quiet, 35 minutes to Cindermoor Works` and press Enter | Within a second or two: "21 areas ranked. What you asked for counts most.", because each thing you say of the place counts for more than a journey or a budget until you say otherwise. Chips that say what was read: Leafy, Quiet streets, Cindermoor Works within 35 minutes, £1,700 a month for one bedroom, Renting, and "Usual settings: 6", with each part nobody chose marked "assumed". "Read without AI." beside them. Ten results, and "Show 10 more". The first is **Farrowmere**, "Fit 71 of 100", with "Why it fits", which begins "Quiet streets: band 4 of 5", one trade-off, and a "Source" button after each. The map fills in shades of green, with pins numbered 1 to 10 |
| Press "Source" after any sentence | It opens in place: "Synthetic test data", who published it, "Data from" and a date, and "Made-up data" |
| Press "3 areas are not ranked", under the list | Otterby Fields, with "Too little data for what counts in your search" and the six things it has no figure for. It is in no result. Then two areas that the data ranks for no search |
| Clear the box, type `a bit more green space, and ignore the high street`, press Enter | The list changes order. Two new chips: one for public green space, and one for the town centre that says "does not count" |
| Open "Settings", then "Journeys", and tick "The journey is a firm limit" | The list shortens to 14 results. Under "Table of all areas", seven areas say "A journey is longer than a firm limit" |
| Type `and 30 minutes to Pellam`, press Enter | A question: "Which place did you mean?", with Pellam Cross, Pellam Exchange and Pellam Infirmary. Pick one and it becomes a chip |
| Type `not too many students, and near a park`, press Enter | One sentence in a plain block: "Burro ranks places by what is there. Of who lives in a place it counts only their age and their households, at the census of 2021, and you cannot ask for fewer of anyone. The rest of your search has been applied." The park is applied. Nothing on the page says what was left out |
| Type `Pubs are so noisy`, press Enter | Nothing is ranked again. Under "Burro was not sure. Choose what to add." are the things it noticed, each with a button for each way it could be meant. Press one and the list is ranked with it |
| Press the name of the first result | The page of the area. It opens with what the area is like in short, and where it is. Then where it sits on each vibe, the stations, what homes cost and everything measured there, each figure with its source and date |
| Go back. Press "Compare" on two results, then "Compare 2 areas" at the foot of the screen | A table of the two areas side by side: where each sits on each vibe, and then each thing that counts in your search, with one row for each journey. Your search is still there when you come back to it |
| Go back to the search, press "Share this search", then "Make the link" | A link that ends `/s#` and 22 letters and digits. Open it in a new tab: the same search, under the heading "A shared search". The link stops working when you stop `make api`, because the API keeps shares in memory |
| Stop the API with Ctrl-C in terminal 1, then change a setting | The results stay, with a line that says Burro could not be reached, and "Try again" |

The figures above are the ones the API gave on 2026-09-24, with ranking engine 1.12.0. The foot of every page names the data release and the engine. If the engine has moved on, the order and the figures may differ, and the rest should hold.

To check the website without a browser, run `make web-check`. It takes about a minute: it checks the types against the contract, lints, runs about 2,900 tests offline, builds every page, and reads each built page for what a person or a screen reader would trip over.

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
| Find any guide, from one page | [docs/README.md](docs/README.md) |
| See the whole in four pictures, and what holds each promise | [docs/architecture.md](docs/architecture.md) |
| Know how Burro got here, and what went wrong on the way | [docs/history.md](docs/history.md) |
| Understand what is being built and when | [docs/PLAN.md](docs/PLAN.md) |
| Change the code | [AGENTS.md](AGENTS.md) |
| Change the website | [apps/web/AGENTS.md](apps/web/AGENTS.md), [docs/design/web.md](docs/design/web.md) |
| Run or change the iOS app | [apps/ios/README.md](apps/ios/README.md), [apps/ios/AGENTS.md](apps/ios/AGENTS.md) |
| Put it on the internet | [deploy/README.md](deploy/README.md) |
| Refresh London, from what is due to what is served | [docs/refreshing-london.md](docs/refreshing-london.md) |
| Know what a second city would take | [docs/adding-a-city.md](docs/adding-a-city.md) |
| Set up and run a data build | [docs/data-builds.md](docs/data-builds.md), `uv run python -m burro_pipeline --help` |
| Know why something is the way it is | [docs/adr/](docs/adr/) |
| See how the backend's parts fit, and every route | [docs/design/contract.md](docs/design/contract.md), [contracts/openapi.json](contracts/openapi.json) |
| Add or check a data source | [registry/README.md](registry/README.md) |
| See the evidence behind the plan | [docs/research/](docs/research/README.md) |
