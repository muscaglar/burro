# Burro: plan for v1

Written 2026-09-23, before anything was built. Corrected the same day to match what has been built since: see Status, below.

| Founder decision, 2026-09-23 | Answer |
|---|---|
| Hours available | As many as needed. External waits and money are the constraints, not founder time |
| Neighbourhood map | Founder curates, with a paid second reviewer for the less familiar half of London |
| Solicitor budget of GBP 5,000 to 10,000 | Rejected. Legal risk is removed by design instead. See section 9 |
| Census figures about residents | Shown on an area's page, and never ranked on. See ADR 0014 |
| How Burro knows things | Evidence first. Every insight rests on a stored, cited record, shown or not. A model may help build a release and never answers from memory. See ADR 0014 |
| Coverage of the first version | All of London. No pilot borough |
| Language model | No one provider. Gemini first, with OpenAI, DeepSeek and Claude supported behind one interface |

Evidence behind every claim here is in [`docs/research/`](research/README.md). Of 72 claims the plan depends on, 47 were confirmed against primary sources, 19 were partly wrong and have been corrected below, 1 was refuted, and 5 were not checked and are now spikes or launch gates.

## Status, 2026-09-23

The code of phase 0a is done. Much of phases 2 and 3 has been built ahead of phases 0b and 1, on a synthetic release: a made-up city of 24 areas. No real dataset has been ingested, so nothing Burro shows today is a fact about London.

| Part | State |
|---|---|
| Licence registry and ingest gate | Built. 110 sources are registered |
| Ranking engine, release format, API | Built, on synthetic data. No database, no sign-in, no quotas |
| Reading a prompt | Done by rules today. The reader that uses Claude is built and has only ever met a stand-in |
| Explanations | Fixed template sentences, each checked by the verifier. Sentences written by Claude wait for a stronger verifier |
| Website | Built, on synthetic data: search, map, area pages, comparison, sharing. No basemap. Not yet tested by hand |
| iOS app | Built, on synthetic data. It has never been run: nothing in it has been seen on a screen, in a simulator or on a phone |
| Not yet done | Real data, travel times, a call to a live model. See section 11 |

Fifteen decision records are in [`docs/adr/`](adr/README.md). How the built parts fit is in [`docs/design/contract.md`](design/contract.md) and [`docs/design/web.md`](design/web.md).

## 1. What Burro is

Burro helps someone decide where in London to live before they start looking at properties. They describe the life they want, name up to three places they need to reach, and see about 450 named neighbourhoods ranked on a map. Each result says where the place is, gives up to three reasons it matched and one trade-off, and shows the source and date behind every number.

The ranking is arithmetic over published data, so the same question always gives the same answer. Claude turns language into structured preferences and writes explanations from a table of facts. It never ranks, never scores, and never describes a place from its own knowledge.

## 2. Why anyone would choose it

The category is not empty: other tools match people to areas by quiz or by chat. "AI area finder" is no longer a position.

What Burro sets out to offer:

| Burro does | In place of |
|---|---|
| Several commute destinations at once, from real timetables, in under a second | One destination, or a paid API, or "check TfL yourself" |
| Shows its working: visible weights, cited facts, dated sources | Opaque match percentages, or an LLM's recollection |
| Named neighbourhoods people say out loud | Postcodes, boroughs, or listings |
| Independent of estate agent revenue | Everything resolves to a listing |
| Built for someone who has never been to London | Assumes local knowledge |

Positioning line: **decide where before you search what.** Lead with two workplaces on one map, not with "AI".

## 3. Decisions already made

| Topic | Decision |
|---|---|
| Name | Burro |
| Audience | Renters and buyers, with people relocating to London as a first-class case |
| Area unit | Named neighbourhoods, computed from a fine grid underneath |
| Interaction | Prompt, then ranked map, then refine by chat or by visible weights |
| Commute | Public transport, cycling, walking. Several destinations. Precomputed |
| Vibe | Derived from data plus openly licensed text |
| v1 extras | Comparison, shareable links, saved shortlists with accounts |
| Not in v1 | Links to property listings, driving, payments |
| Clients | Next.js website first, then native SwiftUI |
| Backend | Python, Claude API |
| Business | Free at launch, premium later |
| Data | Open first, small paid extras, commercial-safe licences only |

## 4. v1 scope

| Area | In | Out for now |
|---|---|---|
| Search | Prompt, rent or buy toggle, up to 3 destinations, editable assumption chips, sliders, chat refinement, map plus an accessible list | Interview-style flows, non-English evaluation |
| Commute | Weekday morning peak by public transport (typical and "just missed it" times), cycling, walking. Nearest station and lines within a 10-minute walk. Route detail fetched from TfL when a result is opened | Evening, weekend and night times, destinations outside Greater London |
| Cost | Rent by bedrooms and sale price by property type, shown as ranges with a confidence tier and an as-of month | Price per square metre, affordability verdicts |
| Features | About 20 across recorded crime, schools, green space and water, air and noise, venues and culture, homes, station access | Broadband, flood, GP access, anything without licence evidence on file |
| Vibe | 12 tags, each a published formula over data | Tags scored by an LLM, embeddings, imagery |
| Profiles | One page per neighbourhood built from the fact table, with an attributed Wikipedia excerpt | LLM-written prose, named venues |
| Compare | 2 to 4 areas, rows ordered by the user's own weights | Pre-rendered pairs |
| Share | Opaque link ID. Destinations coarsened to station or district unless the sender chooses otherwise | User-written titles or notes |
| Accounts | Sign in with Apple, Google or email code. Shortlists. In-app deletion. Search needs no login | Payments, passkeys |

## 5. How it works

```
 prompt ──► read (Claude, or the rules) ──► typed edits ─┐
 sliders and chips ───────────────────────► typed edits ─┤
                                                         ▼
                                        preference spec, held by the client
                                                         │
 data release ──► held in memory ──────────────────► rank()  pure function, milliseconds
                                                         │
                                     ranked areas + per-feature contributions
                                                         │
         fact table ──► explain (templates today) ──► verifier ──► text
```

**Components**

| Part | What it is | Where it runs |
|---|---|---|
| `packages/pipeline` | Python and DuckDB steps that build an immutable data release | Hosted CI, from a private store. A rented machine if routing does not fit (ADR 0015) |
| `packages/core` | Pure Python, no IO: preference model, reducer, `rank()`, fact builder, verifier | Imported by API and pipeline |
| `services/api` | FastAPI. Loads the release into memory. Holds the only Claude key. Keeps nothing for a search | Fly.io, London |
| `apps/web` | Next.js, MapLibre GL JS | Vercel, London |
| `apps/ios` | SwiftUI, MapLibre Native, generated API client | App Store |
| Postgres and Auth | Users, shortlists, shares, entitlements, call metadata. Never area data. Not built: until it is, shares and call records are held in memory | Supabase, London |
| Tiles and releases | Basemap and area tiles served as z/x/y. Not built: the map draws the areas' outlines, served by the API | Cloudflare R2 and a Worker |

**A search, step by step**

1. **Parse.** One Claude call returns typed edits, stated assumptions and the categories of what it could not map, never the phrases. Destinations come back as text and are resolved by Burro's own place index, never by the model. With no key, and whenever the model is slow, capped or broken, the rules read the prompt instead.
2. **Rank.** Hard filters, then a weighted mean of within-London percentiles plus a commute decay. Returns ordered areas with each feature's contribution. The server keeps nothing for a search: the client holds the spec and sends it with each request.
3. **Draw.** The client joins `area_id → score` onto static map tiles and builds result cards from the contributions.
4. **Explain.** For the top results, three by default and five at most, cited sentences are written from the fact table. A verifier checks each one before it is shown. Today the sentences are fixed templates. Claude writes them only once the verifier can check everything a model's sentence asserts.
5. **Refine.** Sliders and chips re-rank directly with no model call. Chat asks Claude for edits and uses the same reducer, so the two stay in step.

**When things go wrong**

| Situation | What the user gets |
|---|---|
| Explanation is slow or fails verification | Reason chips and template sentences |
| Parse times out, errors, or a spend limit is hit | The rules read the prompt instead, and the same controls are there as a form. Never a 5xx |
| API is down | Static profile pages still work |
| Anonymous quota reached | Form and sliders keep working. Never a login wall |

## 6. Geography

Three grids, one shared `cell` table, each used for what it is good at.

| Layer | Count | Used for | Why |
|---|---|---|---|
| Census Output Area | about 26,400 | Neighbourhood membership, census sums | Nests exactly, follows real streets and rivers |
| LSOA centroid | about 5,000 | Where journeys start | Sits where people live. The router runs one origin at a time, so fewer origins is five times cheaper |
| H3 hexagon, resolution 9 | about 16,700 | Where journeys end | Workplaces cluster where few people live, so census units are poor destinations |
| Named neighbourhood | about 450 | What the user sees | Plus 250 to 350 smaller names stored as aliases |

**The neighbourhood map does not exist and has to be built.** No open polygon set of London neighbourhoods is usable. The source of truth is a reviewed CSV that assigns each Output Area to a neighbourhood. Polygons are generated from it, never hand-drawn, so every boundary change is a reviewable diff. An agent proposes; someone who knows London approves. Budget 100 to 150 hours.

## 7. Data

All v1 sources are free and licensed for commercial use with attribution.

| Dimension | Source | Licence | Caveat |
|---|---|---|---|
| Cells and lookups | ONS 2021 boundaries and centroids | OGL v3 | |
| Place names | OS Open Names, Wikidata | OGL v3, CC0 | Coverage to be measured |
| Destination search | OS Open Names, Code-Point Open, NaPTAN, schools (GIAS), hospitals (NHS ODS), Wikidata landmarks | OGL v3, CC0 | Must resolve "I work at UCL". Target 90% |
| Tube, DLR, tram, bus | TfL Journey Planner timetables | TfL open data licence | No engineering works |
| Rail, Overground, Elizabeth line | Network Rail schedule | Reported OGL-based | **Gate:** terms must be read and saved first |
| Street network for routing | OpenStreetMap | ODbL | Routing and basemap only. See section 9 |
| Sale prices | HM Land Registry Price Paid, UK HPI | OGL v3 | No bedroom count. Postcode rows never displayed |
| Rents | ONS Price Index of Private Rents | OGL v3 | Measures all tenancies, so understates new lets |
| Rent variation within a borough | ONS London postcode-district workbook | OGL v3 | Appears discontinued. Used as a dated snapshot |
| Housing stock | VOA council tax stock, Census 2021 | OGL v3 | Census was taken in lockdown |
| Recorded crime | data.police.uk | OGL v3 | Locations are snapped to anonymised points |
| Schools | GIAS, DfE performance tables, Ofsted | OGL v3 | Three incompatible Ofsted regimes. No catchments |
| Green space and water | OS Open Greenspace, OS Open Rivers | OGL v3 | |
| Air and noise | Defra modelled NO2, Indices of Deprivation 2025 | OGL v3 | |
| Places | Overture Maps Places | Permissive, varies by record | **Spike:** London quality is unmeasured |
| Food and drink | FSA food hygiene register | OGL v3 | Used for counts. Ratings never shown |
| High streets and culture | GLA boundaries, Cultural Infrastructure Map | OGL v3 | Registered per layer. Third-party layers held back |
| Historic character | Historic England | OGL v3 | |
| Area description | Wikipedia excerpt | CC BY-SA 4.0 | Shown verbatim with attribution. Never fed to a prompt |

**Held out until cleared:** GLA air quality 2022, Planning London Datahub, PropertyData, EPC, the RDG rail feed.
**Banned:** Google Places and Street View, portal scraping, the VOA rating list.

## 8. Ranking and the LLM

**Ranking**
- `rank(spec, release_id, engine_version)` is a pure function. Same inputs, same output, forever.
- Features are scored as within-London percentiles. The percentile is the score only, because where areas tie it counts half of them as beaten. A sentence states the share of areas strictly beyond, rounded down, and says when areas tie: "quieter than 40% of the areas compared, and the same as 12 others".
- With several commute destinations, the slowest one drives the score by default.
- Budget is a **soft** constraint by default and is tested against the upper quartile, because official rent data understates what a new tenant pays.
- Missing data is never filled in. The feature is dropped for that area, weights are rebalanced, and a coverage badge is shown.

**Vibe tags at launch (12):** village feel, buzzy, leafy, creative, family amenities, near universities, waterside, strong high street, evening venues, quiet residential, foodie, historic character. Tags are named for the place, not for who lives there. A tag ships only if it passes a sanity set of 40 neighbourhoods agreed by people who know London.

**Claude**

| Job | Model | Notes |
|---|---|---|
| Parse and refine | Smallest current model (Haiku 4.5 today) | Structured output. One schema of flat, single-type arrays |
| Explain | Same, with citations | Never receives raw user text. Not attached yet: see the verifier, below |
| Offline evaluation | A different, larger model as judge | Weekly, through the Batch API |

- Model IDs live in configuration. Haiku 4.5 may retire during the build, so every evaluation also runs on Sonnet 5 from day one, and costs are planned on the Sonnet figure.
- **Rules:** with no key, and whenever the model fails, a rule-based reader answers in its place. It has a closed vocabulary. Where a clause holds a sign of doubt, or a word it does not know, it makes no edit and says so, because a wish left unread costs little and a wish read backwards costs trust. What a model returns is held to the same test: the code keeps only what it can justify without trusting the model.
- **Verifier:** every number and every proper noun in an explanation must appear in the cited fact. Anything else is replaced with a template. A seeded test plants an invented venue to prove this works. As built it is enough for fixed templates and not for a model: it does not yet catch a name in lower case, a claim about residents, or a number said of the wrong thing. No sentence written by a model is shown until it does.
- **Disclosure:** an "AI-generated, may be inaccurate" notice at the start of each session. On iOS, an explicit permission screen before the first prompt is sent (App Store guideline 5.1.2(i)).

**Evaluation**

| When | What runs | LLM calls |
|---|---|---|
| Every pull request | Ranking, reducer, verifier, perturbation and missing-data tests | None |
| Prompt, schema or model change, and weekly | 150 golden queries with field-level checks, on both models | Yes, batch |
| Every data release | 40-neighbourhood tag sanity set, diff report of what moved | None |

## 9. Rules the codebase enforces

These are tested in CI, not left to good intentions.

**Privacy**
- Raw prompt text and destination strings are never written to any log, error report or database table. Nor is a place ID, a fact ID or a share ID: each says, or unlocks, where someone works.
- Nothing worked out from a spec is logged or kept about a call: no hash of a spec, plain or under a key. A spec's hash goes only in a response, to the client that already holds the spec. See ADR 0005 and 0011.
- There are no stored searches. The server keeps nothing between requests, and there is no search ID. A share is the only stored spec, and a person makes one on purpose.
- Typed text travels in a `POST` body, never in a URL. Logging is a list of what may be written, not a scrubber of what may not.
- `llm_calls` holds metadata only: call ID, timestamp, endpoint, interpreter, model, status, whether the rules answered in the model's place, token counts, latency, release ID, engine version. It has no text or JSON payload column and no hash of a prompt or a spec, and CI fails if a migration adds one. Rows expire after 30 days. Until there is a database the records are held in memory.
- Sentry runs with request bodies off, default PII off, and a scrubber. It is hosted in the EU and listed as a processor.
- There is no parse cache yet, because there is no model to pay for. When there is one it is keyed by an HMAC under a key that is made at start-up and never stored, held in memory, and expires after 24 hours.
- A test proves the parse handler's timeout and validation-failure paths do not log the request body.
- The only place raw text leaves Burro is the Claude API call. Anthropic retains inputs for up to 30 days under its terms, longer if flagged: [the research on Claude](research/models/claude.md), section 7, gives the pages. The privacy notice says so.

**Legal approach: remove the question instead of paying for the answer**

There is no solicitor in the budget, so nothing in v1 may depend on a legal opinion. Each open question is closed by the most conservative design that still delivers the product.

| Question | How it is closed without a solicitor | What is left over |
|---|---|---|
| Could ranking areas amount to steering under the Equality Act? | Burro ranks places, never residents. No input to ranking or to any tag describes who lives somewhere. Housing facts describe buildings | A neutral feature may still correlate with a protected group. The proxy audit and its written rule cover this |
| Does share-alike reach the travel-time table? | Follow the published OpenStreetMap Foundation guidelines, publish the routing method, credit OSM beside commute times | Worst case is being asked to publish the travel-time table under ODbL, which is acceptable |
| Is aggregating Price Paid by postcode allowed? | Ask HM Land Registry for written confirmation. Never display or export postcode rows | Low. It is standard practice |
| Privacy notice, DPIA, terms | Written in-house from the ICO's own templates. Vendor data processing agreements accepted online | No professional has read them |
| Rail and GLA licence terms | Read, save and register the terms. Ask the owner in writing where they are silent | A source can be dropped if terms do not clear |

No professional will have reviewed these positions. If Burro gains traction or starts charging, a capped fixed-fee review of the privacy documents is the first thing to buy. Free legal clinics for startups are worth an application in the meantime.

**Fairness**
- Nothing that describes residents is an input to ranking or to any tag. "Family amenities" is built from schools, nurseries and play space. "Near universities" is built from distance to campuses.
- Nothing about residents feeds a score, a tag or a vibe. Census figures for age, household type, country of birth, ethnic group, religion and main language are shown on an area's page, as the statistics office's own table and nothing more: no sentence, no comparison, no colour, and no way to search or sort by them. Sexual orientation, gender identity, disability and health are used offline only, to audit ranking features for proxy effects. See ADR 0014.
- The model can only emit feature IDs from an allowlist in code.
- Requests to avoid a group get one neutral sentence, and the rest of the query is served. Requests for community are met through amenities: places of worship, specialist shops, venues.
- Recorded crime is off by default, shown as rates by category with caveats, and never labelled "safe" or "unsafe".
- The proxy audit has a written rule before it runs: for each feature, the aim it serves, a correlation threshold that triggers review, and the actions available.

**Licences**
- `registry/sources/` lists every dataset with licence, evidence, attribution text and date verified. The ingest gate refuses a source unless it is approved for that use, or is gated or held and lists that internal use. It refuses the whole registry if any entry breaks a rule.
- The attributions page is generated from the registry.
- OpenStreetMap is used for the basemap and the routing street network only. Walk-distance features use OS Open Roads. OSM comparison may set a global threshold but never change an individual record.
- A public methods page names the OSM extract date, routing engine version and settings. OSM is credited on the map and beside commute times.

## 10. Repository

```
burro/
  AGENTS.md  CLAUDE.md        CLAUDE.md is one line: @AGENTS.md
  Makefile  pyproject.toml
  registry/                   sources/, one file per topic, and saved licence evidence
  docs/                       PLAN.md, adr/, design/, research/
  contracts/                  openapi.json, the single API contract
  packages/core/              pure Python, no IO
  packages/pipeline/          registry/, release/. Ingest and routing steps come with real data
  services/api/               FastAPI. No database yet, so no migrations
  apps/web/                   Next.js. The generated API types are committed
  apps/ios/                   SwiftUI, from the same contract. Not yet built or run
  tools/                      repository checks, standard library only
  data/fixtures/synthetic/    the synthetic release: a made-up city, under 1 MB
  planned                     map/, evals/, docs/policies/
```

**Conventions**
- One Makefile. `make ci` is the gate, and hosted CI runs exactly that. The website has its own gate, `npm run check` in `apps/web`, which `make ci` does not run yet.
- `make test` finishes in under 30 seconds. `make fixture` rebuilds the synthetic release, which reads no file and no network, and a test fails if the committed copy differs by a byte.
- Claude is called through an interface with a fake in tests, so nothing in CI needs a key.
- One OpenAPI file generates the TypeScript types today, and the Swift client when the iOS app is built. A test fails if the file is stale, and `npm run check` fails if the generated types are.
- Each nested `AGENTS.md` has a one-line `CLAUDE.md` beside it, because nested files do not load otherwise.
- Agent settings deny reading `.env` files. There is no Google Maps key in the project.
- Every dependency has a one-line justification. No package that ships a native binary it needs to run; see ADR 0008.

## 11. Roadmap

Agents write most of the code; the hours below are yours. You have said your time is not the limit, so the dates are set by external waits: Apple enrolment, the rail subscription, recruiting testers, and the December rail timetable change. More of your time buys slack and a better neighbourhood map, not a much earlier launch.

**Where the build stands, 2026-09-23.** The code was built out of order. With no real data to build on, the engine, the API and the website were built on a synthetic release, ahead of the spikes and of phase 1. Nothing seen on it says how the product will feel on London. The phases below still say what must be true before each is done. None has met its exit yet.

| State | What |
|---|---|
| Built, on synthetic data | Licence registry and gate. The release format, its writer and its reader. Ranking, the reducer, 23 features and 12 tags as formulas, facts, template explanations, the verifier. Reading a prompt by rules, and by Claude against a stand-in. An API of twelve routes. The website: search by prompt and by form, map, result cards, sliders, area pages, comparison, share links, methods and sources pages |
| Not yet done | Real data: no source has been ingested. Travel times: the routing engine has not been run. A live model: there is no key, and the golden queries have not been written or run. The iOS app has not been run. Committed lockfiles (ADR 0008) |
| Not started | The neighbourhood map. The spikes of phase 0b. Accounts, the database, quotas, the error tracker. The basemap and tiles. The proxy audit. Testing the website by hand |

| Phase | Weeks | Goal | What gets built | What you do | Your hours | Done when |
|---|---|---|---|---|---|---|
| **0a. Foundations** | 1–2 | Nothing built on sand | Repo, conventions, licence registry with CI gate, Supabase project, synthetic release | Start legal entity. Trade mark search and domain. Register with TfL and Rail Data Marketplace. Create Claude workspaces. Start Apple enrolment. Put questions to ONS, GLA, TfL and HM Land Registry. Find the second curator | 30 | Terms saved |
| **0b. Spikes** | 2–4 | Remove the big unknowns | Timetable conversion for TfL and rail by two paths. Router benchmark and parallel driver. Schema, tokens, latency and cache on both models. Overture against FSA in 20 areas. Destination resolution rate. Neighbourhood map v0. Clickable prototype | Test the prototype with five people who moved to London | 25 | One decision record per spike |
| **1. Commute finder** | 5–8 | The hero capability, no LLM | Data release, travel-time matrices, validation against TfL, cost model with backtest, tile Worker, form-based search with map, methods and attributions pages, rate limit, Sentry | Curate inner London. Brief the second curator. Request a higher Claude tier | 70 | Validation passes on three measures. Fairness, licence and privacy positions written down as decision records |
| **2. Describe your life** | 9–12 | Language in, ranked map out | Feature store, 12 tags, parse call, ranker, result cards, sliders, share links, anonymous tokens, spend counter | Correct agent-drafted golden sets. Finish boundary review. Approve the feature allowlist. Privacy notice, ICO fee, Claude DPA | 90 | Golden sets pass on both models. 20 to 30 beta users |
| **3. Explain and compare** | 13–15 | Show the working | Cited explanations, verifier, chat refinement, profiles, comparison, proxy audit, steering tests, accessibility pass | DPIA, terms and accessibility statement from templates | 55 | No unsupported number or name in 500 explanations |
| **4. Accounts and launch** | 16–18 | Public on the web | Sign-in, shortlists, deletion, entitlements, quotas, spend-limit drill. Rebuild matrices after the December rail timetable change | Email provider, launch | 40 | **Web launch, late January 2027** |
| **5. iOS** | 19–24 | Native app | Device map spike first. App Attest. SwiftUI client, offline shortlist, permission screen | Device testing, App Store submission | 40 | **App approved, March 2027** |
| **6. On evidence** | later | Only what usage justifies | Evening and weekend times, asking-rent figure, more tags, embeddings, payments, second city | Pricing decision | | Triggered by measured demand |

Total founder time to web launch: about 310 hours. The neighbourhood map is the human critical path.

**No external user touches the parse call until the privacy notice, ICO registration and Claude data processing agreement are in place.** Before then, testing uses the form or synthetic prompts.

## 12. Costs

**Monthly, fixed**

| Item | USD, an estimate |
|---|---|
| Hosting the API, two small London machines | 13–15 |
| Hosting the website | 20–40 |
| Database and sign-in | 25 |
| Tiles and object storage | 5 |
| Error reports | 0–26 |
| **Total** | **65–120** |

Each line is what the plan allows for that job, and not a price quoted from a host. Read each host's own price page before a bill is relied on.

**Claude, per 1,000 searches** (estimates until measured in phase 0b)

| Setup | USD |
|---|---|
| Parse only, template explanations | 2 |
| Haiku 4.5 throughout | 18 |
| Sonnet 5 throughout, the planning figure | 40 |

The entry-tier spend cap is USD 500 a month, and hitting it pauses all API use: [the research on Claude](research/models/claude.md), section 5, gives the page. On Sonnet that is about 400 searches a day, so a higher tier is requested in phase 1.

**One-off, quotes needed**

| Item | Estimate |
|---|---|
| Solicitor | None planned. See section 9 |
| Trade mark search and filing | A few hundred pounds |
| Second curator, about 40 hours | Depends on rate |
| Apple Developer Program | Not read |
| ICO fee | GBP 52 a year |
| Routing rebuild | Tens of pounds a quarter |

## 13. Top risks

| Risk | Why it matters | What we do |
|---|---|---|
| The neighbourhood map feels wrong | "That's not Peckham" kills trust on sight | Inner London first, paid second reviewer, soft map edges, report link, versioned boundaries |
| Rail timetables cannot be converted or licensed | South London is unusable without rail | Two conversion paths proven in phase 0b. Terms saved before any rail time is shown |
| Rent figures mislead newcomers | The first thing a relocator sees would be wrong | Soft budget, upper quartile test, stated uplift on the methods page, decide on a paid source by end of phase 1 |
| A steering or discrimination complaint | Legal and reputational | Rank places, never residents. Code allowlist, crime off by default, audit with a written rule |
| No professional legal review | A position we think is safe may not be | Most conservative design on every open question. Published licences only. Buy a capped review once there is revenue |
| An explanation states something untrue | It is the product's central promise | Verifier on numbers and names, template fallback, seeded tests |
| Claude spend runs away, or the small model retires | Free endpoint, public internet | Quotas, bot checks, spend limits, deterministic fallback, both models tested from day one |
| External waits stall a phase | Enrolments and the rail subscription are outside our control | Each is started in week one. Exit criteria depend only on things we control |
| Episodic use | People choose an area once every few years | Time-boxed passes fit better than subscriptions. Profile pages bring search traffic |

## 14. Decisions still open

Work proceeds on the recommendation unless you say otherwise.

| # | Decision | Recommendation | Blocks |
|---|---|---|---|
| 4 | Demographic rule | **Decided, 2026-09-23.** Ranking stays fully place-based. Census figures are shown on an area's page and never ranked on. See ADR 0014 | Phase 2 |
| 5 | Name and domain | The founder's to settle | Phase 0a exit |
| 6 | Wikipedia excerpt on profiles | Yes. It is the "open text" you asked for, and costs nothing | Phase 3 |
| 7 | Where is the app sold? | UK and non-EU countries at launch. EU later, once the privacy documents have had the paid review described in section 9 | Phase 5 |
| 8 | Prompts processed outside the UK | Accept and disclose. Claude has no UK or EU region on the direct API: [the research on Claude](research/models/claude.md), section 7 | Privacy notice |
| 10 | Pass or subscription? | Decide in phase 6. The entitlement table handles both | Nothing yet |
| 11 | Is a paid asking-rent source worth GBP 28 to 48 a month? | Decide at the end of phase 1 | Rent model |

## 15. What we will not do

- Ingest, scrape or link to property listings.
- Let the model rank, score or describe a place from memory. A model may help build a release, and what it finds enters only with a source that has been checked.
- Publish a composite "safety" or "liveability" score.
- Rank, filter, colour a map or build a vibe by who lives somewhere. Census figures are shown on an area's page and used for nothing else.
- Run a routing engine, vector database or job orchestrator in production.
- Give affordability verdicts.
- Build payments before there is usage to price.
- Start iOS before the website has real users.
