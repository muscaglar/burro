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
3. **What a person types stays in the box it was typed in, and in one `POST` body.** Never in a URL, browser storage, the console, an error report or a log. A place id, a spec, a fact id and a share id are treated the same way.

Do not weaken a rule to make a change pass. Raise it instead.

## Where things live

| Path | What it is |
|---|---|
| `src/lib/api/schema.d.ts` | Every API type. Generated, committed, never edited by hand |
| `src/lib/api/required.ts` | What the `data` of each answer must hold, by name. Generated beside the types. The client refuses an answer that lacks one |
| `src/lib/api/client.ts` | The API as the browser calls it: one function a route. It never throws and never logs |
| `src/lib/api/server.ts` | The API as a build reads it: routes 4, 5, 6 and 11 only |
| `src/lib/api/recorded.ts` | Reads the recorded answers, for tests and for a build with no API |
| `src/lib/search/` | The search: `state.ts` is the one object and the pure function that moves it on, `store.ts` holds it in memory, `flow.ts` makes the calls, `edits.ts` builds every edit a control sends, `counts.ts` says whether a weight counts, `unread.ts` finds the parts of a sentence that no edit rests on |
| `src/lib/session/session.ts` | What is kept while the tab is open: the search, the areas chosen to compare, and the link that was last made. In memory, held by the shell of every page. `useCompare`, `useMadeLink`, and `useOpenSearch` in `store.ts`, read it |
| `src/lib/compare/list.ts` | Two to four areas, and which areas a comparison's address names |
| `src/lib/area/` | `profile.ts` says which fact goes under which heading of an area's page. `describe.ts` makes its title, description, canonical address and structured data from its `area` fact |
| `src/lib/indexing.ts` | The one rule that says whether a search engine may index anything, and the website's own address. The layout, an area's page, `robots.ts`, `sitemap.ts` and the headers in `next.config.ts` all ask it |
| `src/lib/facts.ts` | The source and the date of a fact, read off it |
| `src/lib/map/style.ts` | The only file that holds a colour, a layer or a source of the map. `library.ts` is the map library, loaded on demand |
| `src/lib/paths.ts`, `city.ts` | The only place an address is built. It takes a slug or an id, never text |
| `src/lib/headers.ts` | The content security policy: the website's origin and the API's, and no other |
| `src/content/` | Site copy. No number and no proper noun about a place |
| `src/styles/tokens.css` | Every colour, size and space. `test/tokens.test.ts` works out the contrast |
| `src/components/Name/` | `Name.tsx`, `Name.module.css`, `Name.test.tsx` |
| `test/recorded/` | Answers captured from the real API. Written by `test/record.py`, never edited. `area/` holds every area's profile, `visit/` one person's whole visit |
| `test/visit.test.tsx` | One whole visit, answered only with what the service answered to that very request. `test/support/visit.ts` is its stand-in |
| `test/search/unexpected.test.tsx` | What becomes of the page when the API sends what the website did not expect |
| `test/search/races.test.tsx` | What becomes of the page when answers come in an order nobody planned, or do not come: a release that moved, an answer while a number is typed, Stop once the words are read, reasons that fail |
| `scripts/` | `gen-api.mjs` generates from the contract. `check-pages.mjs` reads the built pages |
| `test/support/` | The jsdom environment, the axe check, the contrast formula, and the stand-ins: `api.ts` for the API, `maplibre.ts` for the map library, `watch.ts` for everywhere a leak could go, `search.tsx` to open the search page |
| `test/search/`, `test/privacy/`, `test/access/` | Every state of the search page, what must never leave the box, and what must work by keyboard |
| `test/area/`, `test/compare/`, `test/share/`, `test/indexing.test.tsx` | The page of an area, the comparison, opening a shared link, and what a search engine is told |
| `test/support/figures.ts` | Finds every figure a page shows and says which the API did not send. A test of a page that shows figures expects none |
| `test/support/css.ts` | Reads a style sheet: its rules, what each sets, and how much a selector weighs. jsdom lays nothing out, so a test of layout reads the styles |
| `test/search/shown.test.tsx` | What the search page shows and the words it uses. It holds the tests marked `test.failing`, each of which waits on a gap of section 13 of the design |
| `test/search/walked.test.tsx` | What the search page did when a person used it in a browser, and no test had caught: where things stand, where the focus is left, what is said when a part was not read |
| `test/styles.test.ts` | What a browser showed of the layout, held in the style sheets: a box that scrolls, a line for a keyboard, the space between two small links |

## The API

- The address comes from one environment variable, `NEXT_PUBLIC_BURRO_API_URL`, read in `src/lib/api/config.ts` and by the content security policy. With it unset the browser's client answers `not_configured` and a build reads `test/recorded/`.
- The website's own address comes from `BURRO_SITE_URL`, read on the server in `src/lib/indexing.ts` and nowhere else. It is an origin with no path. With it unset, or while the release is made up, no page may be indexed: every page says `noindex`, every answer carries `X-Robots-Tag`, and the sitemap lists nothing. The robots file never keeps a crawler out, because one that is kept out cannot read that a page asks to be left out.
- Import types from `@/lib/api/schema`. To get the type of a route's body or answer, use `BodyOf` and `DataOf` in `operations.ts`. Never write an API type by hand.
- A field the contract gives a default is typed as always there, so send `limit` and `exact_destinations` every time.
- Every record from the API is read-only, and an index may hold nothing: copy before you sort, and check what `[0]` gave you.
- Every answer carries `synthetic`. It is true if the body or the header says so. The client tells the banner of every answer.
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
- Run a whole search with `openSearch(firstSearch())` from `test/support/search.tsx`, and wait with `settled()`. Set what the API answers with `api.on("rank", "rank-refined")`, and read what was sent from `api.lastCallTo("rank").body`. `api.movedTo(release)` makes every answer name another release, as a service does once it holds one. `api.hold` and `api.late` make an answer wait, to put answers in the order a test is about.
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
- A figure about a place is shown as the API formatted it. Where the website must turn a number into a whole one, as with a fit, it rounds down.
- What the API serves with no fact behind it has no source and no date, and is not shown: a percentile, a `utility`, a coverage, whether a station is step-free. If you need it on a page, ask for a fact.
- A weight of 0 in a spec is a thing a person took off, and counts for nothing. Ask `counts()`, never whether the entry is there.
- What counts in a search is not all "what you asked for": the settings nobody chose count too. Site copy says "what counts".
- A code the website has no word for is left out, and never shown as a blank or as the code.
- A sentence stands under "Trade-off" only if `isGivenUp` in `ResultList/tradeoff.ts` says the area does that thing badly. Otherwise the card says none was found.
- Nothing is dimmed or drawn see-through: a dimmed colour is not the colour whose contrast was checked. A state is said in words. `tokens.test` fails on an opacity.
- What explains the page is drawn where it can be seen. `visually-hidden` is for a name a sighted person reads from the layout, never for an explanation.
- What Burro says of a search stands directly under the box: what happened, what was not read, a notice, a question, a failure, what was understood. It is what a person sees when they press Search. Put no control between the box and it.
- The focus is never left on nothing. What is removed gives it to what is beside it. A button that may be pressed until it does nothing, or that waits on an answer, says `aria-disabled` and ignores the press: switched off while it has the focus, it loses it. jsdom leaves the focus on a button that is switched off, so a test holds the attribute.
- A fit is never given alone where it rests on part of what counts. `basedOn` in `AreaTable.tsx` says how much, wherever a `RankedArea` is in hand.
- What was typed may be selected in the box. It is never copied out of it: not into the page, and not into state. `rests_on` is offsets, and offsets are all the store holds.
- A box that scrolls is positioned, so that what is laid out `absolute` inside it is cut off with the rest. `test/styles.test.ts` holds every one.
- Nothing but a pin is laid over the map. A rule of the website's that must beat one of the map library's has to weigh more than it: which loads last is not ours to decide.
- A table inside a card is stacked under 40rem, and every part of it says its role again. It is not put in `.scroll-x`.
- A test marked `test.failing` waits on the API. It says what the page is to show, and fails the day it passes: take the mark off then. Put a plain test of today's behaviour beside it.
- A page that is built ahead of time gives the source under each figure with `SourceLine`, not behind the `SourceNote` button, so that it reads with scripts off.
- A link to an area, a source or a comparison is `prefetch={false}`: which page a person reads next is told to no server ahead of time.
- `/accessibility` must stay true. When something in "What has not been tested" is checked by hand, move it and say when. Do not claim what has not been done.
- If something here is wrong or out of date, fix this file in the same change.
