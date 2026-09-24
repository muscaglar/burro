# Burro v1: unified plan

## Scorecard

| Criterion | Lean | Trust | Experience |
|---|---|---|---|
| Fit to the founder's decisions | 4 | 4 | 4 |
| Leanness | 5 | 2 | 3 |
| Legal and trust risk | 4 | 5 | 3 |
| Technical feasibility | 4 | 3 | 3 |
| Time to something a person can try | 5 | 2 | 4 |
| User experience | 3 | 3 | 5 |
| **Total (of 30)** | **25** | **19** | **22** |

- **Lean:** its geometry (LSOA origins, hexagon destinations) is what routing verification later recommended, and it alone has a usable commute finder inside a month. Its product surface is plain.
- **Trust:** best licence registry, demographic tiering and audit, but Output Area origins on a single-threaded router and 20 weeks to web spend scarce human time before anyone tries the product.
- **Experience:** best product thinking, but it leans on unproven items: six matrices from Output Area origins, PropertyData inside the budget filter, share-alike photos, and iOS built alongside web.

**Spine: lean.** Grafted in:

- **From trust:** licence register with saved evidence and a CI gate, built before the first ingest; a `fact` table as the only input to explanations; offline proxy audit recorded in the DPIA; golden sets and a diff report on every data release; published housing backtest; OS Open Roads for the gazetteer partition.
- **From experience:** the result card (orientation line, three reasons, one trade-off); the degraded-mode ladder with a rule-based parser; a latency budget; precomputed example prompts; slowest-commute default; the plain-text portals card; iOS native value (offline shortlist, on-device "Where am I?", share sheet); a prototype tested with five relocators.

## Decisions on the nine disagreements

| # | Decision | Reason |
|---|---|---|
| 1. Base grid | Output Areas for membership and census sums. LSOA population-weighted centroids (4,994) as routing origins. H3 resolution 9 cells (about 16,700) as destinations, each with a point moved onto a walkable street. One shared `cell` table. | r5py routes one origin at a time, so Output Area origins cost five times more for no gain once times roll up to 450 neighbourhoods. |
| 2. Demographics | Rankable: tenure, dwelling type and size, build period, density, churn. Positive-only tag inputs capped at 30% of a tag: households with dependent children, student share. Age bands are not ranked, tagged or displayed. Every other protected characteristic is never loaded into the product store. | Keeps the founder's demographic input while ranking places, not the protected characteristics of residents. |
| 3. Tag count | 12 formula tags at launch, growing towards 20 one at a time, each gated by the golden set. No LLM scoring. | Overture quality in London is unmeasured, and every tag needs a formula, a local sanity check and an explanation. |
| 4. Embeddings | Deferred until more than 10% of real queries contain vibe phrases that match no tag. | 450 areas and a vocabulary that fits in the cached prompt do not need a second vendor or an unexplainable score. |
| 5. OpenStreetMap | Basemap and routing network only. Not in the gazetteer or scoring. Public methods page, OSM credit on the map and beside commute times, and OSM comparison never drives per-record edits. | The matrix is OSM-derived whatever we do. The OSMF Trivial Transformations guideline plus a methods page covers it, and nothing else needs OSM. |
| 6. Portal links | None, and no disabled link abstraction. A plain-text card gives the area name and postcode districts with a copy button. | Founder decision, and all three portals prohibit deep links without written consent. |
| 7. Pricing | No payment code. Entitlement rows carry `source` and `period_end`, so a pass and a subscription are the same row. The shape is chosen before payment work starts. | Premium-later stands. The schema is the only part v1 must get right. |
| 8. iOS map | MapLibre Native 6.31.0, `match` expression, z/x/y tiles from the Worker, overlay bundled in the app, no `pmtiles://` on device. MapKit is the fallback. | One style across clients. PMTiles on native is experimental with open crash reports. |
| 9. Safety | Rankable on request only, default weight zero, named "recorded crime", shown as category rates. No composite score. | Relocators ask for it, and consistent objective rates are the defensible line. |

## 1. v1 in one paragraph

Burro v1 is a London-only website, followed by a SwiftUI app, where a renter or buyer types what they want, names up to three places they must reach, and sees about 450 named neighbourhoods ranked on a map. Each result says where the place is, gives three reasons it matched and one trade-off, and shows the source and date behind every number. Ranking is a pure function over a versioned data release: travel times precomputed from open timetables, rent and price ranges, about 20 percentile-ranked features and 12 formula-defined vibe tags. Claude turns language into typed edits to a preference spec and writes explanations from a fact table, which a verifier checks before display. If Claude is slow, capped or down, the same controls become a form. No dataset is ingested without saved licence evidence.

## 2. What is in v1 and what is cut

| Area | In v1 | Cut or deferred |
|---|---|---|
| Search | Prompt, renter/buyer toggle, up to 3 destinations, editable assumption chips, sliders, chat refinement, fallback parser, map with an accessible list view | Interview flows, non-English evals |
| Commute | Weekday morning peak public transport (p50 and p85 from one run), cycling, walking, labelled "typical timetabled time" | Direct/one-change labels, evening, Saturday and night matrices, itineraries, destinations outside Greater London |
| Cost | Rent by bedroom and sale price by property type, as ranges with confidence tier and as-of month | Asking-rent figure, price per square metre, any affordability or eligibility verdict |
| Features | About 20: recorded crime (3), schools (4), green and water (3), NO2 and noise (2), venues and culture (4), homes (5), station access (2) | Broadband, flood, GP access, cycle infrastructure, any source without licence evidence |
| Vibe | 12 formula tags plus a phrase lexicon in the prompt | LLM-scored tags, embeddings, imagery |
| Profiles | One static page per neighbourhood, templated from the fact table | LLM-written prose, photos, Wikipedia excerpts, named venues |
| Compare | 2 to 4 areas, rows ordered by the user's weights | Prerendered pairs, LLM narratives |
| Share | URL carries the canonical spec and release id. Shows chips, never the raw prompt | User titles or notes |
| Accounts | Supabase Auth (Apple, Google, email code), shortlists, in-app deletion, entitlements with everyone on free. Search needs no login | Payments, passkeys |
| Trust and ops | Methodology, fairness, licences and routing methods pages. Report-a-problem link. Sentry errors, aggregate events, spend circuit breaker | PostHog, session replay, client flag SDKs, orchestrator |

## 3. Architecture

**Components**

- `packages/pipeline`: Python and DuckDB steps run by `just`, writing an immutable release folder to Cloudflare R2. Routing runs on a rented VM.
- `packages/core`: pure Python, no IO. Preference model, reducer, `rank(spec, release_id, engine_version)`, fact builder, verifier, rule-based parser.
- `services/api`: FastAPI on Fly.io London. Loads release roll-ups into memory (tens of MB). Holds the only Anthropic key.
- `apps/web`: Next.js on Vercel Pro, MapLibre GL JS, Protomaps London basemap.
- `apps/ios`: SwiftUI over the generated client, built after web launch.
- Supabase (London) from the accounts phase, for Auth and user tables. It never holds area data.
- Cloudflare Worker serving z/x/y tiles, added when iOS starts.

**Search flow**

1. `POST /v1/search/parse`. The normalised prompt is looked up in a 24-hour cache. On a miss, one Claude call returns status, typed operations, assumptions and unmet requests. Destinations come back as strings and are resolved by Burro's gazetteer, never by the model. An ambiguous destination produces the only clarifying question.
2. `POST /v1/search/rank`. Hard filters, then a weighted mean of percentile utilities plus commute decay. Returns ordered areas with per-feature contributions in milliseconds.
3. The client joins `area_id -> score` onto static vector tiles and builds cards from the contributions.
4. `GET /v1/search/{hash}/explain` streams cited sentences for the top five, each verified before it is re-emitted.
5. Sliders and chips call rank directly. Chat asks Claude for operations and uses the same reducer.

**Degraded modes**

- Explanation slow or fails verification: reason chips and template sentences.
- Parse exceeds 4 seconds, errors, or a spend limit is hit (HTTP 400 on a workspace limit, 429 with no retry-after on the tier cap): the rule-based parser pre-fills the chips as a form.
- API down: static profiles still work.

**Latency targets, to be measured:** chips p50 1.2 s, ranked map p50 2.5 s and p95 4 s, slider re-rank p50 150 ms.

**Analytics:** aggregate-only and server-side, with no persistent identifiers, a notice and an opt-out, so no consent banner. Feature gating is evaluated server-side from the entitlements table.

## 4. Geography and data model

- **Output Area (26,369):** membership and census sums. A neighbourhood is a set of Output Areas in a reviewed CSV. Polygons are dissolved in the build, never hand-drawn.
- **LSOA centroid (4,994):** routing origin and the native level of most features. `native_resolution` is recorded and shown.
- **H3 resolution 9 (about 16,700 cells of about 0.094 km2):** routing destination. Each routing point is moved to the nearest walkable street node inside its cell, because R5 silently snaps points up to 1,600 m.

That is about 83 million pairs per matrix (83 MB at one byte per pair). The API serves only the neighbourhood-by-destination roll-up (450 by 16,700, about 7.5 MB per array) as a population-weighted median with a within-area range. Fine matrices stay in R2, so boundaries can change without re-routing. The engine sees a generic `cell`, so another city can use hexagons throughout.

**Gazetteer.** About 450 ranked neighbourhoods plus 250 to 350 aliases. Seeds come from OS Open Names, Wikidata and MSOA Names. Output Areas are assigned by network distance over OS Open Roads with the Thames as a hard barrier, then reviewed by a person. IDs are immutable, and slugs redirect. Areas under about 3,000 residents are viewable but not ranked.

**Release bundle (`releases/<date>/`)**

- `gazetteer/oa_to_neighbourhood.csv` (source of truth), `neighbourhoods.parquet`, `aliases.parquet`, `cells.parquet`
- `metric_catalogue.yaml`: feature id, sources, native resolution, aggregation, polarity, vintage, rankable flag
- `features_*.parquet`, `tags_neighbourhood.parquet`, `cost_neighbourhood.parquet`, `similar.parquet`
- `facts.parquet`: one row per displayable fact with source and date
- `tt_transit_am_p50.npy`, `tt_transit_am_p85.npy`, `tt_cycle.npy`, `tt_walk.npy`: kept apart from every other table and joined only by key
- `places.sqlite`: full-text search over OS Open Names, Code-Point Open and NaPTAN
- `manifest.json`: input checksums, code commit, OSM extract date, r5py version, jar checksum, routing settings

Postgres tables: `users`, `shortlists`, `shortlist_items`, `plans`, `entitlements`, `events`, `llm_calls`.

## 5. Ranking and LLM design

**Ranking.** `rank()` canonicalises the spec, applies hard filters (budget fit, per-destination time caps, exclusions), then scores each area as a weighted mean of within-London percentiles plus a piecewise commute decay. With several destinations the slowest commute drives the score by default. Small-count rates are shrunk toward the borough mean. Missing features are dropped and weights renormalised, with a coverage badge. Nothing is imputed. The contribution table is the single source for chips, explanations and tests.

**Allowlist.** A code-level allowlist of feature ids is the only vocabulary the model can emit. The IMD rank is never a feature. Requests to avoid a group get one neutral sentence and the rest of the query is served. Affinity requests are met through amenities.

**Tags.** Village feel, buzzy, leafy, creative, family-oriented, student-heavy, waterside, strong high street, evening venues, quiet residential, foodie, historic character.

**LLM**

- **Parse and refine** use Claude Haiku 4.5 with one shared structured-output schema: status, `operations[]`, assumptions, unmet requests. Parse is "operations applied to the default renter or buyer spec", so one schema serves both calls and needs one cache entry.
- **Explain** is a separate Haiku 4.5 call with Citations over one fact per block. It never receives raw user text.
- **Schema limits.** Every field is required, with an `unspecified` enum value in place of optional or nullable fields. That stays under the limits of 24 optional and 16 union-typed parameters.
- **Caching.** The prefix exceeds 4,096 tokens and is kept warm by a real request with `max_tokens` of at least 1. If operations-only parsing fails the golden set, fall back to two schemas and two warm entries.
- **Reproducibility** comes from the query-to-spec cache, because SDK 1.x no longer exposes temperature.
- **Model risk.** Haiku 4.5's retirement floor is 15 October 2026, so the golden set runs on Sonnet 5 with thinking disabled from the first eval. Model ids live in configuration.
- **Verifier.** Every numeral and place, station or line name must appear in a cited fact. Failures become templates.
- **Disclosure.** An AI notice with "may be inaccurate" at the start of every session, and a permission screen on iOS before the first prompt is sent.
- **Prompts.** Raw text is not persisted. Operational logs keep it 30 days at most.

**Evaluation.** Every pull request, with no LLM: ranking, reducer, verifier, perturbation and missing-data tests. On prompt, schema or model changes and weekly, through the Batch API: 150 golden queries with field-level assertions. Every data release: a tag golden set of 40 neighbourhoods and a diff report.

## 6. Data sources for v1

| Dimension | Source | Licence | What it gives | Caveat |
|---|---|---|---|---|
| Cells | ONS 2021 boundaries, centroids, lookups | OGL v3 | Cells, membership, origins | Stacked ONS and OS attribution |
| Names | OS Open Names; Wikidata | OGL v3; CC0 | Seeds, aliases | Coverage unmeasured |
| Naming prior | House of Commons Library MSOA Names v2.3 | Open Parliament Licence | Name hints | Licence text unread: gate |
| Partition | OS Open Roads | OGL v3 | Network distance | |
| Destination search | OS Open Names, Code-Point Open, NaPTAN | OGL v3 | Postcode, station, place lookup | Royal Mail attribution |
| Tube, DLR, tram, TfL bus | TfL Journey Planner timetables | TfL open data licence | Primary timetables | Updated every 7 days, ignores engineering works |
| Bus cross-check | BODS London GTFS | Unproven | Cross-check | Licence and coverage unverified: spike |
| Rail, Overground, Elizabeth line | Network Rail NWR Schedule | Reported OGL-based | Rail timetables | Terms unread: gate. Convert with UK2GTFS `nr2gtfs` |
| Street network | OpenStreetMap London extract | ODbL | Walk, cycle, access legs | Built from OSM alone |
| Basemap | Protomaps extract | ODbL produced work | Map tiles | Attribution on web and iOS |
| Sale prices | HM Land Registry Price Paid; UK HPI | OGL v3, address condition | Quartiles by property type | Postcode is Address Data. No bedroom field |
| Rent anchor | ONS Price Index of Private Rents | OGL v3 | Borough by bedroom, monthly | Understates new lets |
| Rent relativity | ONS "Private rental market in London", nine editions | OGL v3 | Dated district ratios | Treated as discontinued |
| Housing stock | VOA Council Tax stock; Census 2021 | OGL v3 | Tenure, type, build period | Census is five years old |
| Recorded crime | data.police.uk | OGL v3 | Category rates, 24 months | Snapped locations |
| Schools | GIAS, DfE performance tables, Ofsted | OGL v3 | Attainment, adverse flag | Three Ofsted regimes. No catchments |
| Green and water | OS Open Greenspace, OS Open Rivers | OGL v3 | Share, proximity | |
| Air and noise | Defra modelled NO2; Indices of Deprivation 2025 noise | OGL v3 | NO2, noise exposure | 1 km air grid |
| Places | Overture Places 2026-08-19.0 | CDLA-Permissive-2.0, Apache 2.0 or CC0 by record | Venue density, diversity | Quality unmeasured. Keep `sources` |
| Food and drink | FSA Food Hygiene Rating Scheme | OGL v3 | Primary count, chain detection | Never show a rating |
| High streets, culture | GLA boundaries; Cultural Infrastructure Map 2024 | OGL v3 | Anchors, venue counts | GLA accuracy disclaimer |
| Historic | Historic England listings; conservation areas | OGL v3 | Density, coverage | Incomplete, duplicates |

Held out: LAEI 2022, Planning London Datahub, Cultural Infrastructure Map 2025, Ofcom, PropertyData, EPC, Wikipedia prose, the gb-transit rail feed (internal prototyping only), Google, the VOA rating list.

## 7. Repository layout and conventions

```
burro/
  AGENTS.md  CLAUDE.md     CLAUDE.md is one line: @AGENTS.md
  justfile  pyproject.toml  uv.lock  .env.example
  registry/sources.yaml    licence, evidence, date verified, attribution, pinned release
  registry/evidence/       dated licence pages and accepted terms
  docs/adr/  docs/policies/
  contracts/               openapi.json, TypeScript 5.x pin
  packages/core/           pure Python, no IO
  packages/pipeline/       steps/, sources/, routing/
  services/api/            FastAPI, migrations, Dockerfile
  apps/web/  apps/ios/     generated clients committed
  map/style/  map/tiles/  map/worker/
  data/fixtures/camden/
  evals/
```

- Every nested `AGENTS.md` has a one-line `CLAUDE.md` beside it, checked with `/context` inside a package folder.
- Every package exposes the same `just` verbs. `just test` runs in under 30 seconds, and `just pipeline-fixture` in under 60 with the network blocked.
- CI fails on an unregistered source, a missing evidence file, a table mixing share-alike and other columns, or a feature id outside the allowlist.
- The attributions page is generated from the registry.
- Exact pins: anthropic 1.8.0, r5py 1.1.7 and its R5 jar by SHA256, one maplibre-gl 6.x version, the Overture release.
- No Google Maps key in the project. Agent settings deny reading `.env` files.

## 8. Roadmap

| Phase | Goal and build | Human tasks | Exit criteria | Size |
|---|---|---|---|---|
| 0. Spikes and gates | Repo scaffold, registry, CI gate, OSM policy. Inspect BODS by `route_type`; convert TfL timetables; check stop times past 24:00:00. H3 polyfill; 200 LSOA origins at 120 and 60 minute windows; parallel driver. NWR Schedule through `nr2gtfs`. Compile the schema; measure tokens, latency and cache reads on both models. Overture against FHRS in 20 neighbourhoods. Gazetteer v0. Clickable prototype | Register with TfL and Rail Data Marketplace and save terms. Save the Open Parliament Licence. Email ONS, GLA, TfL, PropertyData. Create Anthropic workspaces. Start legal entity, trade mark search, Apple enrolment. Brief a solicitor. Test the prototype with five relocators | Timetable and rail sources chosen with terms on file. Seconds per origin and heap measured. Schema compiles. One decision record per spike | 2 weeks |
| 1. Commute finder | Release bundle, three matrices, 1,000-pair validation, cost model, form-based page, methods and attributions pages. No LLM | Curate inner London. Five movers try it | Median error against TfL Journey Planner under 5 minutes, published by mode mix | 3 weeks |
| 2. Describe your life | Feature store, 12 tags, parse call, ranker, result cards, sliders, fallback parser, share links | Write golden sets. Finish boundary review. Approve the allowlist | Golden sets pass on both models. 20 to 30 beta users | 3 weeks |
| 3. Explain, profile, compare | Cited explanations, verifier, chat refinement, profiles, compare, proxy audit, steering tests, accessibility pass | Legal review, DPIA, privacy notice, ICO fee. Read the EHRC code | No ungrounded numeral in 500 explanations. Counsel sign-off | 3 weeks |
| 4. Accounts and launch | Supabase Auth, shortlists, deletion, entitlements, quotas, Turnstile, spend-limit drill, Sentry | SMTP, domain, higher Anthropic tier, launch | Public web launch | 2 weeks |
| 5. iOS | Device spike first. SwiftUI client, tile Worker, offline shortlist, "Where am I?", permission screen | App Store submission | App approved | 3 to 4 weeks |
| 6. On evidence only | Direct/one-change and evening matrices, asking-rent calibration, reviewed prose, more tags, embeddings, payments, second city | Pricing; legal advice on subscription duties | Triggered by usage | Open |

Public web launch lands about 13 weeks from start, in early January 2027. Gazetteer curation (100 to 150 hours) runs alongside phases 1 to 3 and is the human critical path.

## 9. Running costs

| Item | Monthly | Note |
|---|---|---|
| Fly.io, two small London machines | USD 13 to 15 | Confirm the London price |
| Vercel Pro | USD 20 to 40 | Includes 1 million CDN requests. A launch spike moves it up a tier |
| Supabase Pro | USD 25 | From phase 4 |
| Cloudflare Workers and R2 | USD 5 | From phase 5 |
| Sentry | USD 0 to 26 | Errors only |
| **Fixed total** | **USD 65 to 120** | |
| Claude, online | USD 18 per 1,000 searches on Haiku 4.5, 40 on Sonnet 5, 2 with chips only | Estimates until measured |
| Claude, keep-warm and evals | Under USD 20 | Evals weekly through Batch |
| Routing refresh | Tens of pounds a quarter | VM sized from measured heap |

Annual: Apple Developer USD 99, ICO fee GBP 52, domain. One-off, quotes needed: fixed-fee legal review, trade mark search, about 40 hours of a second curator. The Start-tier cap of USD 500 a month equals about 27,400 searches, and hitting it pauses all API use, so a higher tier is requested before launch.

## 10. Top risks

1. **Timetable inputs are wrong or unlicensed.** TfL's own timetables are primary, BODS is a cross-check, rail terms are a launch gate, and 1,000 pairs are validated.
2. **Routing takes far longer than estimated.** Parallel driver with one JVM per worker, LSOA origins, measured in phase 0. Fall back to a 60-minute window.
3. **Boundaries feel wrong or curation overruns.** v0 from MSOA names unblocks engineering. Inner London first, a paid second reviewer, soft edges, a report link.
4. **Steering or discrimination claim.** Code allowlist, positive-only household inputs, crime off by default, proxy audit, counsel sign-off as a launch gate.
5. **Rent figures mislead newcomers.** "Typical rent paid" label, ranges, a plain sentence that new lets usually cost more, published backtest.
6. **An explanation states something not in the data.** Chips first, per-block verifier, template fallback, perturbation tests.
7. **Haiku 4.5 is retired, or spend runs away.** Both models pass the golden set from day one. Quotas, Turnstile, parse cache, spend limits, deterministic fallback.
8. **Vibe tags fail a local sanity test.** FHRS is the primary food and drink count. Any tag that fails the golden set is dropped.

## 11. Decisions the founder must make

| Decision | Recommendation | Blocks |
|---|---|---|
| Demographic rule | Accept disagreement 2, pending counsel | Allowlist and tags (phase 2) |
| ODbL position on travel times | Publish the methods page and agree to offer the matrix under ODbL if counsel advises | Showing commute times (phase 1) |
| Rail conversion path | NWR Schedule with `nr2gtfs`. Use the RDG feed only if its terms clear | Matrices (phase 1) |
| Evening return and night matrices | Out of v1, confirmed in writing | Routing scope (phase 1) |
| Asking-rent source | Launch without one. Revisit at the end of phase 1 | Rent model (phase 1) |
| Analytics path | Aggregate-only with notice and opt-out | Any analytics SDK, the DPIA |
| Global inference, no UK or EU pinning | Accept and disclose. Google Cloud's EU route is the fallback, without Batch | Privacy notice, DPIA |
| Anonymous search | Yes, three searches a day | Quotas (phase 4) |
| Second curator | Pay someone who knows the half of London the founder knows least | Phase 2 exit |
| Legal entity and fixed-fee legal review | Start this week. Cover the Equality Act position, ODbL for routing outputs, Price Paid address data, privacy documents | ICO fee, Apple organisation enrolment, launch |
| Trade mark and domain | Commission a UK search in classes 9, 36 and 42 and pick the domain now | Public launch, App Store title |

## 12. What we will deliberately not do

- Ingest, scrape or link to listings.
- Let the model rank, score tags, or describe a place from its own knowledge.
- Give affordability or eligibility verdicts such as "will I be approved".
- Run a routing engine, vector database or orchestrator in production.
- Use session replay, a client-side flag SDK, or `pmtiles://` on device.
- Publish a composite safety or liveability score.
- Show ethnicity, religion or age breakdowns, even "for information".
- Display postcode-level price rows or individual food hygiene ratings.
- Use the TfL roundel, TfL maps or New Johnston.
- Build payments before there is retention to price, or start iOS before web has real users.

## 13. Corrections applied from verification

Unverified claims became spikes (phase 0) or launch gates.

- **Open Parliament Licence unread.** Gate: a person saves a dated copy.
- **Overture Places is three licences.** Keep per-record `sources`, add the Overture attribution and Foursquare Apache 2.0 notice, build on `basic_category` and `taxonomy`.
- **OSMF is silent on statistical aggregates.** Treated as a grey area. Any later OSM feature gets its own table and a published method.
- **Keeping the matrix server-side does not avoid ODbL.** Street network built from OSM alone, GTFS kept separate, public methods page, OSM credit beside commute times on web and iOS.
- **OSM benchmarking can trigger share-alike.** Repo rule: comparison sets global thresholds, never per-record decisions.
- **BODS London licence and coverage unproven.** Spike. TfL timetables are primary.
- **NWR Schedule terms unread; gb-transit feed is RDG data.** Gate: accepted terms saved before any rail time is shown.
- **`cif2gtfs` does not read Network Rail CIF.** UK2GTFS `nr2gtfs` in its own container, checked for Overground and Elizabeth line.
- **Postcode is Address Data in Price Paid.** Gate: reasoning in the register and in the legal review.
- **ONS district rent workbook has probably ended.** Nine editions archived. The model rests on the price-ratio prior.
- **Structured outputs have complexity limits.** All-required schema, compiled against the API in phase 0.
- **Parse and refine cannot share a cache across schemas.** One shared schema, warmed by a real request.
- **Retention wording.** Up to 30 days, up to 2 years if flagged, scores up to 7 years. Processor named as Anthropic Ireland, Limited.
- **Nested AGENTS.md files do not load beside a root CLAUDE.md.** One-line `CLAUDE.md` beside each.
- **Person-level analytics needs consent.** Aggregate-only analytics, no PostHog.
- **EHRC estate-agent passage unconfirmed.** Gate: the fairness policy rests on section 29 and the code's website paragraph.
- **Vercel Pro includes 1 million requests, not 10 million.** Budgeted at USD 20 to 40.
- **PMTiles on iOS now caches but is experimental.** Decision kept, reason changed.
- **r5py ships R5 v7.5.1-r5py.** Pin r5py 1.1.7 and the jar checksum.
- **London has about 16,700 res-9 cells, not 15,000.** Sizing redone. Real count from the polyfill.
- **r5py computes origins sequentially.** Spike: parallel driver, chunked result writing, VM sized from measured heap.
- **R5 rejects times past 24:00:00.** Night matrix out of v1.
- **r5py defaults differ from intent.** Settings set explicitly and recorded in the manifest.
- **Ofcom has no small-area files.** Broadband cut from v1.
- **Spend limits cannot be set on the Default Workspace.** Non-default workspaces. Fallback tested on both the 400 and the 429.
- **Guideline 4.2 should not rest on MapKit.** It rests on shortlists, share sheet and offline shortlist.
- **Supabase details untested.** Spike in phase 4: direct IPv6 against the session pooler from Fly, and asymmetric signing keys.
