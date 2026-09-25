# apps/web

The Burro website: Next.js, TypeScript, plain CSS. It is built to [docs/design/web.md](../../docs/design/web.md). If the two disagree, change one of them in the same commit. The API it calls is described in [docs/design/contract.md](../../docs/design/contract.md), sections 4, 5, 8 and 9.

```
npm install          from the package index this machine is configured for. Never set one
npm run check        everything: run this before you say you are done
npm run gen:api      rewrite what is generated from contracts/openapi.json, after it changes
npm run check:api    fail if what is generated is out of date
npm run typecheck    next typegen, then tsc --noEmit
npm run lint         eslint, with no warnings allowed
npm test             jest, offline. Pass a path or -t "name" after --
npm run build        next build
npm run check:pages  read every page the build wrote, and fail on what is wrong with one
npm run dev          the website on localhost:3000. From the repository root, `make web` sets the API's address
```

`check` runs `check:api`, `typecheck`, `lint`, `test`, `build` and `check:pages`, in that order, and stops at the first failure. It takes about a minute. From the repository root it is `make web-check`.

To see a change in a browser, build and serve it: `NEXT_PUBLIC_BURRO_API_URL=... npm run build`, then the same with `npm run start -- -p PORT`. The API answers a page only from an origin in its `BURRO_ALLOWED_ORIGINS`. Then make the checks of [section 9](../../docs/design/web.md) that a test cannot.

## The three rules

1. **Words about a place are the API's.** The website lays them out. It never writes, joins or rewords a sentence about a place, and it formats no number that a fact's `slots` hold already formatted. Site copy lives in `src/content/` and names controls, states and codes only.
2. **The spec on screen is the last spec the API returned.** The website builds edits, never specs.
3. **What a person types stays in the box it was typed in, and in the body of the `POST` that reads it.** That is one call to the rules, and one more to a model where one reads. Never in a URL, browser storage, the console, an error report, a log or the store. Beside an offer the page draws the words the offer rests on, cut from the box by where they stand, while the box holds them. A place id, a spec, a fact id and a share id are treated the same way.

Do not weaken a rule to make a change pass. Raise it instead.

## Where things live

| Path | What it is |
|---|---|
| `src/lib/api/schema.d.ts` | Every API type. Generated, committed, never edited by hand |
| `src/lib/api/required.ts` | What the `data` of each answer must hold, by name. Generated beside the types. The client refuses an answer that lacks one |
| `src/lib/api/client.ts` | The API as the browser calls it: one function a route. It never throws and never logs |
| `src/lib/api/server.ts` | The API as a build reads it: routes 4, 5, 6 and 11 only. Never route 13 or 14 |
| `src/lib/api/recorded.ts` | Reads the recorded answers, for tests and for a build with no API |
| `src/lib/search/` | The search: `state.ts` is the one object and the pure function that moves it on, `store.ts` holds it in memory, `flow.ts` makes the calls, `edits.ts` builds every edit a control sends, `counts.ts` says whether a weight counts, `card.ts` says what a fit rests on, `spans.ts` turns the API's offsets into places in the box |
| `src/lib/vibes.ts` | Where an area sits on a vibe, in words: a band of five, the same in words a person would use, a range for a mixed area, the names of the two ends, and how a part of a recipe is read |
| `src/content/bands.ts`, `templates.ts` | The words for a band, which are site copy for a code and are held to the contract's formula. The contract's own templates for a likeness and a station, filled from the slots of a fact until a fact comes with a sentence |
| `src/components/Portrait/`, `Track/`, `VibesList/`, `VibeMap/` | The portrait an area's page opens with, the line of five cells a vibe is marked on, the page of every vibe, and the city coloured by one vibe |
| `src/content/crime.ts`, `names.ts` | The one account of when recorded crime counts, which every page that speaks of it says word for word. The room for the other names weighed for a vibe, which is empty until the cases are chosen |
| `src/content/rough.ts`, `src/components/RoughGuide/` | What a vibe that is a rough guide says of itself: which vibe is one, its label and its sentence, all read from route 11. The label beside a name, and the note that says why |
| `src/lib/session/session.ts` | What is kept while the tab is open: the search, the areas chosen to compare, and the link that was last made. In memory, held by the shell of every page. `useCompare`, `useMadeLink`, and `useOpenSearch` in `store.ts`, read it |
| `src/lib/compare/list.ts`, `rows.ts` | Two to four areas, and which areas a comparison's address names. The rows of what counts as they are drawn: one for each journey, with the same destination across it |
| `src/lib/area/` | `profile.ts` says which fact goes under which heading of an area's page, and which vibes two areas share a band on. `portrait.ts` finds the fact behind each vibe of the portrait, chooses the five lines that say what an area is like, says what a band rests on, and says what the vibes shown cannot see. `describe.ts` makes its title, description, canonical address and structured data from its `area` fact |
| `src/lib/indexing.ts` | The one rule that says whether a search engine may index anything, and the website's own address. The layout, an area's page, `robots.ts`, `sitemap.ts` and the headers in `next.config.ts` all ask it |
| `src/lib/facts.ts` | The source and the date of a fact, read off it |
| `src/lib/map/style.ts` | The only file that holds a colour, a layer or a source of the map. `library.ts` is the map library, loaded on demand |
| `src/lib/paths.ts`, `city.ts` | The only place an address is built. It takes a slug or an id, never text |
| `src/lib/headers.ts` | The content security policy: the website's origin and the API's, and no other |
| `src/content/` | Site copy. No number and no proper noun about a place, and no name or terms of a provider of a model |
| `src/styles/tokens.css` | Every colour, size and space. `test/tokens.test.ts` works out the contrast |
| `src/components/CensusPanel/`, `src/content/census.ts` | The census figures of an area's page: asked for when the part is opened, drawn as the API sent them. `part.ts` holds the id of the part, in a file the server may read |
| `test/census/` | `shown.test.tsx` holds the rules of how the census is shown. `apart.test.ts` holds that only the page of an area asks for it, and that no other answer holds a row of it |
| `src/components/BesideName/`, `src/lib/area/named.ts` | What stands beside the name of an area, smaller: the label its publisher gives the area, and that the name is a draft. `named.ts` says what stands there and what the page of an area says of its name |
| `src/components/IncomePanel/`, `src/content/income.ts`, `test/income/` | The household income of an area's page, which is shown and never ranked on: asked for when the part is opened, from route 14, and drawn as the API sent it. The tests hold it apart as the census is held: no file of a search, a comparison or the map names it |
| `test/recorded/` | Answers captured from the real API. Written by `test/record.py`, never edited. `area/` holds every area's profile, `visit/` one person's whole visit, `one-number/` a release whose prices have no range, `counted/` one whose prices were counted from sales, and `let/` one whose rents are each of a postcode district or of a borough |
| `test/visit.test.tsx` | One whole visit, answered only with what the service answered to that very request. `test/support/visit.ts` is its stand-in |
| `test/search/unexpected.test.tsx` | What becomes of the page when the API sends what the website did not expect |
| `test/search/races.test.tsx` | What becomes of the page when answers come in an order nobody planned, or do not come: a release that moved, an answer while a number is typed, Stop once the words are read, reasons that fail |
| `scripts/` | `gen-api.mjs` generates from the contract. `check-pages.mjs` reads the built pages |
| `test/support/` | The jsdom environment, the axe check, the contrast formula, and the stand-ins: `api.ts` for the API, `maplibre.ts` for the map library, `watch.ts` for everywhere a leak could go, `search.tsx` to open the search page |
| `test/search/`, `test/privacy/`, `test/access/` | Every state of the search page, what must never leave the box, and what must work by keyboard |
| `test/area/`, `test/compare/`, `test/share/`, `test/indexing.test.tsx` | The page of an area, the comparison, opening a shared link, and what a search engine is told |
| `test/support/figures.ts` | Finds every figure a page shows and says which the API did not send. A test of a page that shows figures expects none |
| `test/support/css.ts` | Reads a style sheet: its rules, what each sets, and how much a selector weighs. jsdom lays nothing out, so a test of layout reads the styles |
| `test/search/shown.test.tsx` | What the search page shows and the words it uses: a place by its name, a reason from its good side, and gritty as each release builds it. A test that waits on the API is marked `test.failing`. None is today |
| `test/search/budget.test.tsx`, `test/area/budget.test.tsx` | What a results page, and the page of an area, hold before anything is opened. No test measures a height: these hold what the measured heights depend on (design, sections 4.1 and 4.2) |
| `test/search/walked.test.tsx` | What the search page did when a person used it in a browser, and no test had caught: where things stand, where the focus is left, what is said when a part was not read |
| `test/styles.test.ts` | What a browser showed of the layout, held in the style sheets: a box that scrolls, a line for a keyboard, the space between two small links |

## The API

- The address comes from one environment variable, `NEXT_PUBLIC_BURRO_API_URL`, read in `src/lib/api/config.ts` and by the content security policy. With it unset the browser's client answers `not_configured` and a build reads `test/recorded/`.
- The website's own address comes from `BURRO_SITE_URL`, read on the server in `src/lib/indexing.ts` and nowhere else. It is an origin with no path. With it unset, or while the release is made up or is a preview, no page may be indexed: every page says `noindex`, every answer carries `X-Robots-Tag`, and the sitemap lists nothing. The robots file never keeps a crawler out, because one that is kept out cannot read that a page asks to be left out.
- Import types from `@/lib/api/schema`. To get the type of a route's body or answer, use `BodyOf` and `DataOf` in `operations.ts`. Never write an API type by hand.
- A field the contract gives a default is typed as always there, so send `limit`, `exact_destinations` and `ask_model` every time.
- Every record from the API is read-only, and an index may hold nothing: copy before you sort, and check what `[0]` gave you.
- Every answer carries `synthetic`. It is true if the body or the header says so. The client tells the banner of every answer.
- Every answer carries `preview` too, and the client refuses one that does not. It is true if the body or the header `X-Burro-Preview` says so. The client tells `src/lib/api/said.ts` what every answer says of itself, and `LivePreviewBanner` shows the banner as soon as any answer says its release is a preview.
- A page is shown only while every answer is of the kind of data the page was built on. `AsItWasBuilt` in the shell puts a notice in place of the page once an answer says its data is made up and the page was built on data that is not, or the other way, or one is a preview and the other is not. Do not show a figure beside that notice. A release that moved on to another of the same kind is for the search to handle, as before.
- A failure is a value: `api` with the API's code, message and paths, or one of `timeout`, `aborted`, `offline`, `network`, `not_configured`, `unreadable`. Show `message` as it came. It is fixed text and never holds what was sent.

## Recorded answers

```
make web-record      from the repository root
```

It runs `test/record.py`, which drives the real app through its test client, with a fixed clock and seeded ids, so a second run writes the same bytes. Each scenario is there to show one state. When the reader of sentences changes and a scenario stops showing its state, the script writes nothing and says which: reword that scenario's sentence in `record.py` until it shows it again, and add what a new scenario must show to `PROVES`. `test/recorded/index.json` lists every scenario and what it shows. To add one, add it to `record.py` and run it: never write or edit a recording by hand. `test/recorded.test.ts` holds every recording to the contract, so after the contract changes, run `npm run gen:api` and record again.

In a test, read one with `recordedAnswer("rank", "rank-first")` or `recordedError("share-gone")`, and answer a stand-in `fetch` with `responseFrom(...)`.

A test that names a figure of a recording, a fit of 80 or a share of 31%, fails when the ranking changes and the answers are recorded again. That is what it is for. Put the new figure in, and keep what the test proves: a fit is rounded down only if the recorded one has a fraction to lose.

`record_the_visit` records one person's whole visit, each request made of the answer before it, as the website sends it. `test/visit.test.tsx` fails if the website sends anything else. When you change what the website sends, change the visit to match, and record.

## Tests

- Named for the behaviour they protect: `test_typed_text_travels_only_in_a_post_body`.
- Offline. The real `fetch` is taken away before each test. Pass the client a stand-in.
- A test that checks privacy plants a canary, a string found nowhere else, and looks for it everywhere it must not be.
- Check a component with `faultsIn(container)` from `test/support/axe.ts`, and a whole page with `{ wholePage: true }`. axe runs in jsdom and cannot judge contrast, size or layout.
- A server component that is `async` is rendered with `render(await Page())`.
- A test waits for what it looks for. An answer lands a moment after it is asked for, so a test never reads the page on the line after a press that starts a call: it waits with `findBy`, `waitFor`, `settled()` or `arrived()`, which waits for every answer that is on its way and not for a turn of the clock. To see that a test waits, run it with the stand-ins a moment late: `BURRO_TEST_LATE_MS=25 npm test`. A stand-in that a suite makes for itself is a moment late always, as the share panel's is.
- Run a whole search with `openSearch(firstSearch())` from `test/support/search.tsx`, and wait with `settled()`. Set what the API answers with `api.on("rank", "rank-refined")`, and read what was sent from `api.lastCallTo("rank").body`. `api.movedTo(release)` makes every answer name another release, as a service does once it holds one. `api.hold` and `api.late` make an answer wait, to put answers in the order a test is about.
- What is one press away is opened with `everyChip`, `everyResult`, `workingOf`, `theTable` and `settingsAt`, or all of it with `theWholeOfIt`.
- Reasons name the spec they are for, and the page shows them only under the ranking of that spec. Answer `explain_top` with the recording that goes with the ranking, or with `reasonsFor(ranking, reasons)` where none was recorded.
- To go from one page to another in a test, draw both inside one `Shell` and swap them with `rerender`: the shell holds the session, as it does in a browser. To put the browser at a shared link, set `window.location.hash`.
- A page that shows figures is held to `figuresNotFrom(main, saidBy(facts))`: every piece of text with a digit in it must be a slot of a fact, or site copy you add to the set by name.
- jsdom has no WebGL, so the map is a stand-in that records what it was told. `setWebGL(true)` gives a test a map, and `lastMap()` is it.
- A test that fails must not print the page. Assert on a boolean, `text.includes(x)`, where the text is long or holds what was typed.
- To see that a test bites, break the code and watch it fail. A test that passes either way protects nothing.

## Tools

The website depends on no tool that starts a program of its own, so that it builds the same way everywhere: no esbuild, and so no Vite, Vitest or tsx, no Turbo, no Biome, and no browser fetched by Playwright or Puppeteer. Next and Jest through `next/jest` compile with a library that Node loads, and are fine. TypeScript stays at 5.9 for the same reason: later versions ship a native program. See [ADR 0008](../../docs/adr/0008-package-sources.md).

`package-lock.json` is not committed, as `uv.lock` is not. Never write an `.npmrc`. `make public-only` fails on a private host in any file git would track.

## Rules

- No state library, no CSS framework, no component library. Every dependency needs a one-line reason in `docs/design/web.md`, section 11.
- No route handler, no server action and no middleware: nothing a person types passes through the website's own server.
- No `console`, no browser storage, no cookie, no service worker, no analytics, no script from another origin. ESLint refuses the first four.
- Every control is a native element and carries the class `target` or `target-min`.
- A control is drawn from the spec the API returned. Between being changed and being answered it shows what it was set to: use `useDraft(value, version)`, with `state.answers` as the version. `answers` does not move while an edit waits.
- What is being typed, or set and not yet sent, is the person's: no answer may overwrite it. A control holds a new value against the one it last sent, while that waits, and not against the spec alone.
- Every answer names the release that made it, and the store keeps that with what the answer brought. Reasons are the ranking's only when `reasonsAreIn(state)` says so: a hash is of the spec alone, so never hold two hashes against each other and stop there. The release to name under a result is `servedTheRanking(state)`, not the page's `meta`.
- A failure is kept whole, never as a boolean: its message and its `X-Request-Id` are what a person reports. `failureOfTheCards(state)` is the one to say when the search itself did not fail.
- The figure beside a vibe is the part of its recipe that sits nearest the band of the vibe, of those a person can picture, so that it never reads against the band.
- A figure about a place is shown as the API formatted it. Where the website must turn a number into a whole one, as with a fit, it rounds down.
- What the API serves with no fact behind it has no source and no date, and is not shown: a percentile, a `utility`, a coverage, whether a station is step-free. If you need it on a page, ask for a fact.
- A weight of 0 in a spec is a thing a person took off, and counts for nothing. Ask `counts()`, never whether the entry is there.
- What counts in a search is not all "what you asked for": the settings nobody chose count too. Site copy says "what counts".
- A code the website has no word for is left out, and never shown as a blank or as the code.
- The page offers nothing the release cannot answer, and says what is not there in plain words. Ask `src/lib/holds.ts`, which reads `holds` and `recipes` of route 11: whether a vibe is placed, whether a thing can be answered, which examples to offer. What was asked for and is in the data for no area is named by `NotInData`, from `not_in_release` of route 1. Nothing is filled in. `test/search/preview.test.tsx` holds the page to it, on the made-up preview that `record.py` records.
- A date is the date of what is said, never of one source. `citedBy` in `src/lib/facts.ts` gives each source once and each date once. Every date goes through `readableDate`.
- A built page may hold answers the framework kept from an earlier build. Build on a new release from a folder with no `.next` in it.
- A sentence stands under "Trade-off" only if `isGivenUp` in `ResultList/tradeoff.ts` says the area does that thing badly. Otherwise the card says none was found.
- Nothing is dimmed or drawn see-through: a dimmed colour is not the colour whose contrast was checked. A state is said in words. `tokens.test` fails on an opacity.
- What explains the page is drawn where it can be seen. `visually-hidden` is for a name a sighted person reads from the layout, never for an explanation.
- Who else reads what is typed, what goes with it and what becomes of it there are the API's to say: `reader` of route 11. The website shows `reader.notice` as it was served, and writes no provider's name, no period of keeping and no terms of its own. `test/privacy/source.test.ts` and `test/site-copy.test.ts` read the source and the copy for both. The search page never shows the `reader` it was built on: it asks the service as it opens (`flow.loadReader`), and `submitText` sends no sentence while `state.reader` is `null`.
- What Burro says of a search stands directly under the box: what happened, what was not read, a notice, a question, a failure, what was understood. It is what a person sees when they press Search. Put no control between the box and it.
- Once a ranking follows a press, the first result is in sight without scrolling, at 1440 by 900 and at 390 by 844. What stands between the box and it is said in short, and what is long is one press away: the offers that are left, and why a thing is not in the data. `test/search/walked.test.tsx` holds what stands between them. Measure in a browser before adding a line there.
- The focus is never left on nothing. What is removed gives it to what is beside it. A button that may be pressed until it does nothing, or that waits on an answer, says `aria-disabled` and ignores the press: switched off while it has the focus, it loses it. jsdom leaves the focus on a button that is switched off, so a test holds the attribute.
- A fit is never given alone where it rests on part of what counts. `basedOn` in `src/lib/search/card.ts` says how much, from the counts the API gives with every score.
- What was typed may be selected in the box, and the words an offer rests on are drawn beside it as "You wrote". They are cut from the box when the page is drawn (`written` in `src/lib/search/spans.ts`), and never retyped, stored or put in an attribute. `unread`, and the `spans` and `shown` of an offer, are offsets, and offsets are all the store holds. They go when the box changes, and the words go with them.
- An offer is drawn in four parts, in the API's words: what it would do, what you wrote, what follows, the choices. The website marks the guess the API names and chooses none. Which way one press may add is the API's to say (`add_all`), and what it then says is left is the API's too (`needs`). The rules are asked first (`ask_model: false`) and what they offer is drawn at once. Then the model is asked, and what it read joins it.
- The answer comes first. A results page draws ten results at most and nothing open: the working of a result, the settings, sharing and the table are each one press away. `test/search/budget.test.tsx` and `check:pages` count what is drawn at first. Measure in a browser before raising a count.
- On a phone the first result is whole on the first screen. Nothing but what Burro says of the search stands between the box and the first result: the settings, sharing and the map come after it, and the rest of the results after the map. The list is drawn in two parts for that, `part="first"` and `part="rest"`, and `results()` in `test/support/search.tsx` reads both.
- The tray of areas to compare takes no room until an area is chosen, on every page, and then stays at the foot of the screen. The button that fills it says beside itself what the tray does.
- Nothing is ranked from what the reader noticed until the person chooses. A choice sends the `operations` the API gave with it, unchanged. Every thing one press may add is in sight, so that one button adds them all: what waits behind "Show all" is only what is a question. What carries Burro's guess is drawn first, in the order its words stand in the sentence, before "Show all" and after it: `inSight` and `everyOffer`. After the press the line says what was done, in full: how many were added, how many areas a firm budget among them left out, counted from `filtered` of the ranking that followed (`leftOutByTheBudget`), and what is left for the person. What is left is then folded to one line, which says how many there are and opens them all, so that the first result is in sight: `leftInSight`. The fold applies nothing and loses no offer. It folds again at once when one of them is chosen, by the press and never by where the focus is or by a clock: the line that opens it takes the focus, and the line over it says what was chosen since the press, "Then 1 more added." or "Then 1 skipped.", and no longer names it as left.
- The line that says what happened says what counts most. What is said of the place leads until a person makes a journey or a budget count for more. Where one then counts for more than anything that was asked of the place, the line says so (`leadsOf`), and never "What you asked for counts most".
- A place is named by the answer that brought the spec (`places`), and never by a number or by what was typed.
- The name of an area comes first, and the label its publisher gives the area stands beside it, smaller: draw it with `BesideName`, from `named` of the area. The label says the borough, so the borough is not said twice. A name is a draft until the API says a person has checked it, and a result and the page of an area say so in the words of `NAMED`. The website chooses no name and no side, and writes no publisher's name: who wrote a name is a slot of the fact of the area. The page of methods says how a name is chosen.
- The one box that finds by name finds a place to reach and an area. A place is an option, and picking it adds a journey. An area is a link to its page under the field, fetched when it is pressed, and adds nothing to the search. Where the data names no place the box finds areas alone, and says why.
- A vibe is shown as a band of five between two named ends, and never as a score or a percentage. The band is said in words wherever it is drawn: in the name of the picture, or beside it. On a result the names of the ends are drawn for the eye and said by the picture, so that a screen reader hears each once. An area a vibe cannot place is said to be so, and is never put in the middle.
- The page of an area opens with the portrait and ends with "Go and look". The portrait opens with what the area is like in five lines at most, in words a person would use, and beside it where it is. Which vibe stands in which list is the API's. What is long is closed until it is pressed, in the browser's own `details`, so that it opens with scripts off: a button that needs a script is not used for it. Measure in a browser before raising a count of `test/area/budget.test.tsx`.
- A band that rests on part of a recipe says so beside the band, from the counts its fact holds. The website adds up no share of a recipe: a sum has no source.
- What Burro cannot place an area on is said once, with why. What is known of each vibe is one press away.
- Recorded crime is shown only where a person asked for it or opened it. No figure of recorded crime stands beside a vibe, and a vibe whose recipe holds one is in no summary and in no list of what two areas share. Which vibe that is, is read from route 11 (`holdsRecordedCrime`), and is never written down.
- When recorded crime counts is said one way. `CRIME_RULE` is the only sentence that says it, and a test fails on another. Where no vibe of the release holds recorded crime, it is followed by the line that says so (`ruleIn`).
- A vibe whose recipe holds recorded crime says so wherever it is in a search: on its chip, in the row, beside its slider, and in the source of every sentence about it (`countsOf`).
- A vibe that is a rough guide says so wherever it is shown, in sight and not behind a press: its label and the sentence that says why (`roughOf`). On its chip and under the row, on a result, beside its band on an area's page, on the page of vibes, on the shelf and its card, beside its slider, in a comparison, and where the map is coloured by it. Its offer says it in the API's own note. Which vibe is one is `Tag.sureness`, and the words are `rough_guides` of route 11: none is written into the website, and a vibe that does not say is as sure as the rest. It is in no line of what an area is like in short, and in no list of what two areas share. Where a test holds that a page says no verdict of a place, "rough" among them, the label is taken out first: it is said of a guide.
- A comparison has one row for each journey, as the API sends them. A row is a journey where it names a place, whatever the row is called. The journeys count as one thing, so what they count for is said once, under the first of their rows.
- An area that is not ranked is in no result. It is listed apart, under the list, with why and what it has no figure for, by the names the API gives. A reason or a thing the page has no name for is left out.
- An area with no figure for a thing that was asked for stands below every area that has one. The order is the API's, and the website sorts nothing. The card says which figure the area has none for, in sight, and says that the person asked for it: `COMPLETENESS.lacksAsked`. A usual setting with no figure is named without those words.
- Where fewer areas are listed than are ranked, the page says so. Both counts are the API's.
- A sentence about a vibe is short on a result. What it leaves out is the fact's, and "Source" shows it: the date, whose recipe it is, and that the weights are a judgement. Where a row says the line about judgement itself, its source does not say it again.
- Every vibe on the page of vibes is laid out as the next is. A part added to one is added to all.
- No vibe is written into the website. The page of vibes, the shelf, the settings and the portrait are drawn from route 11 and route 6, so none can disagree with the engine.
- What another page asks the search to add, as "Search for this character" does, is handed over through the session (`wanted`) and sent by the search page. It holds ids of vibes, and never an area or anything typed.
- What is seen on a short button is the start of its name: "Compare", and "Compare: Alderwick" to a screen reader.
- What goes when it is pressed hands the focus on: a chip, a suggestion, a word of the shelf, the place field before a search.
- A box that scrolls is positioned, so that what is laid out `absolute` inside it is cut off with the rest. `test/styles.test.ts` holds every one.
- Nothing moves or changes size because the focus or the pointer came or went. A rule keyed on `:focus`, `:hover` or `:active` sets only what is drawn: a colour, a ring, an underline. What makes room while it is used, as the box does while it is typed in, keeps the room until a press elsewhere has landed, or the press lands on nothing. `test/styles.test.ts` reads every style sheet for it.
- Nothing that can be pressed is laid over the map but a pin. The name of an area is drawn over it where it has room for the whole of it, takes no press, and is kept from a screen reader. The map library says of whatever it is handed that it is a button named "Map marker": take that off what is no button. A rule of the website's that must beat one of the map library's has to weigh more than it: which loads last is not ours to decide.
- A table inside a card is stacked under 40rem, and every part of it says its role again. It is not put in `.scroll-x`. The table of every area is stacked by the width of its own box (`@container`), because beside the list on a desk its box is narrow.
- A test marked `test.failing` waits on the API. It says what the page is to show, and fails the day it passes: take the mark off then. Put a plain test of today's behaviour beside it.
- A page that is built ahead of time gives the source under each figure with `SourceLine`, not behind the `SourceNote` button, so that it reads with scripts off.
- A link to an area, a source or a comparison is `prefetch={false}`: which page a person reads next is told to no server ahead of time.
- `/accessibility` must stay true. When something in "What has not been tested" is checked by hand, move it and say when. Do not claim what has not been done.
- The census figures of an area are shown as a description and never as a verdict. `docs/design/web.md`, section 2.1, has the ten rules and the test that holds each. In short: a table first and a picture second; one colour; the rows in the order they came; a figure beside the whole city's and nothing else; no word of the website's about what a figure means; nothing to sort or filter by. Do not draw a figure of the census anywhere but in `CensusPanel`, do not hand one to the search, the session, a comparison or the map, and do not read route 13 when a page is built: changing any of these is changing ADR 0014.
- What a page that is drawn on the server takes from a file that runs in the browser is a component and nothing else. A constant taken from one arrives as a function, and no test of a component sees it: `check:pages` does.
- If something here is wrong or out of date, fix this file in the same change.
