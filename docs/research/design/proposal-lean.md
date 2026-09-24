## 1. v1 in one paragraph

Burro v1 is a London-only website (iOS follows as a thin client) where a person types what they want, names up to three places they must reach, and within about three seconds sees roughly 450 named neighbourhoods ranked on a map, each with a contribution breakdown and a short cited explanation. Ranking is a pure function over a precomputed, versioned data bundle: three travel-time matrices, a rent and price estimate, about 20 percentile-ranked features and 12 formula-defined vibe tags. Claude Haiku 4.5 does two jobs online: turn language into a PreferenceSpec, and write explanations from a fact pack that a verifier checks before display. Everything else is arithmetic. There is no database until accounts arrive, no paid data vendor, no embeddings, no routing engine in the request path, and four vendors at first beta (Fly.io, Vercel, Cloudflare R2, Anthropic).

## 2. What is in v1 and what is cut

| Area | In v1 | Cut or deferred |
|---|---|---|
| Search | Prompt to PreferenceSpec, renter/buyer toggle, up to 3 destinations, sliders, chat refinement as typed operations | Multi-question interviews, non-English evals, data-driven "like X abroad" |
| Commute | Weekday AM-peak public transport p50, cycling, walking; labelled "typical timetabled time"; link out to TfL planner | p85, evening, Saturday and night matrices; interchange counts; itinerary detail; destinations outside Greater London |
| Cost | Rent by bedroom (PIPR-anchored model), sale price by property type (Price Paid); ranges, as-of month, confidence tier | PropertyData asking-rent calibration, price per square metre, mortgage maths |
| Features | About 20: recorded crime (3), schools (4), green and water (3), NO2 and noise (2), venues and culture (4), homes (5), station access (2) | The rest of the proposed 34 (digital, flood, GP, cycle infrastructure, change) and every source without a confirmed licence |
| Vibe | 12 formula tags | LLM-scored tags, 40 to 60 tag vocabulary, embeddings, imagery |
| Profiles | One static page per neighbourhood built from the fact table: templated sentences, percentile bars, similar areas, sources and dates | LLM-written prose, photos, Wikipedia excerpts, named venues |
| Compare | 2 to 4 areas side by side, rendered on demand | Prerendered pair pages |
| Share | URL carrying the canonical spec plus data release id | Stored share records, user titles or notes |
| Accounts | Supabase Auth (Apple, Google, email code), shortlists, in-app deletion, entitlements table with everyone on free | Payments, passkeys, alerts |
| Ops | Sentry, a server-side events table | PostHog, orchestrator, pgvector, tile Worker (until iOS) |

Disagreement 6 (portal links): none, and no disabled "outbound provider" abstraction either. Rightmove, Zoopla and OnTheMarket terms forbid deep links without written consent, and the founder has already excluded them.

Disagreement 7 (pricing): write no payment code. Entitlement rows carry `source` and `period_end`, which serves a recurring subscription and a time-boxed pass equally. Choose the shape after launch with usage data; the evidence that area choice is episodic favours passes.

## 3. Architecture

Components:
- `packages/pipeline`: plain Python and DuckDB steps run by `just`, writing an immutable release folder (Parquet, NumPy arrays, SQLite, `manifest.json`) to R2. The R5 routing step runs on a rented VM for a few hours per refresh.
- `packages/core`: pure Python, no IO. PreferenceSpec model, reducer for edit operations, `rank(spec, release_id, engine_version)`, fact-pack builder.
- `services/api`: FastAPI on Fly.io (London). Loads the release into memory at boot (tens of MB). Holds the only Anthropic key.
- `apps/web`: Next.js on Vercel, MapLibre GL JS, Protomaps London extract read from R2.
- `apps/ios`: SwiftUI over the generated OpenAPI client, added last.
- Supabase (London) for Auth and Postgres, added only when accounts ship. Postgres holds users, shortlists, entitlements, events and `llm_calls`, never area data.

Search flow:
1. `POST /v1/search/parse`: one Haiku 4.5 call with structured output returns status, PreferenceSpec, assumptions and unmet requests. Destinations come back as strings and are resolved by the SQLite gazetteer, never by the model.
2. `POST /v1/search/rank`: hard filters, then a weighted sum of percentile utilities plus commute decay read from matrix columns. Returns ordered areas with per-feature contributions in milliseconds.
3. The client joins `area_id -> score` onto static vector tiles and shows reason chips built from the contributions.
4. `GET /v1/search/{hash}/explain` streams (SSE) explanations for the top five. The server verifies each block before re-emitting and falls back to templates.
5. Sliders and chat both emit typed operations into the same reducer. Sliders never call the model.

| Precomputed per release | Computed per request |
|---|---|
| Travel-time matrices, features, percentiles, tags, cost estimates, similar areas, tiles, profile pages, place gazetteer | One parse call, ranking arithmetic, one optional explanation call |

Disagreement 8 (iOS map): MapLibre Native, because one style and one tile set across clients is worth more than MapKit's zero dependencies. Avoid the two immature parts: colour polygons with a `match` expression rather than feature-state, bundle the 450-polygon overlay in the app, and add the Cloudflare Worker serving cacheable z/x/y only when iOS starts. Open the iOS phase with a one-day device spike; MapKit is the fallback.

Fixed run cost is about USD 65 to 100 a month. LLM cost is about USD 18 per 1,000 searches, with a floor near USD 2 when explanations degrade to chips.

## 4. Geography and data model

Disagreement 1 (base grid): use each unit for the one job it is good at.
- Membership and census sums: 2021 Output Areas (26,369). A neighbourhood is a set of OAs in a reviewed CSV; polygons are dissolved in the build. This costs nothing at runtime and gives edges that follow real streets, which is where trust is won or lost.
- Routing origins and feature computation: LSOA population-weighted centroids (4,994). They sit where people live, and most sources (IoD 2025, crime, council tax stock) are LSOA-native. OAs inherit their LSOA value.
- Routing destinations: H3 resolution 9 cells (about 15,000). Workplaces are anywhere, and a uniform 200 m snap suits them. A hexagon centred in a park is harmless as a destination.

That is about 75 million pairs per matrix (75 MB as uint8) instead of 225 million. The API serves only the roll-up, neighbourhood by destination cell (450 x 15,000, about 7 MB per matrix), as a population-weighted median with a within-area range. The fine matrix stays in R2 so boundaries can change without re-routing. The ranking engine sees only a generic `cell` abstraction, so a city without census units can use H3 throughout.

Disagreement 5 (OpenStreetMap): basemap only, plus the routing graph. The gazetteer seeds from OS Open Names, Wikidata and House of Commons Library MSOA names; the feature store uses Overture, FHRS and OGL sources. The travel-time matrix is accepted as plausibly an ODbL derivative database. It lives in its own files, is linked to other data only by key, is never blended into a feature column, and Burro publishes the build recipe and offers the matrix under ODbL on request. Anyone with R5 can rebuild it, so little is given away. Swapping the street network for a non-OSM one is not worth the engineering.

Release bundle (`releases/<date>/`):
- `gazetteer/oa_to_neighbourhood.csv` (source of truth, reviewed by pull request), `neighbourhoods.parquet` (immutable id, slug, borough shares, rankable flag), `aliases.parquet`
- `cells.parquet` (cell id, system, representative point, population, parent codes)
- `features_lsoa.parquet`, `features_neighbourhood.parquet` (raw value, percentile, native resolution, vintage, source id)
- `tags_neighbourhood.parquet`, `cost_neighbourhood.parquet`, `similar.parquet`
- `tt_transit_am.npy`, `tt_cycle.npy`, `tt_walk.npy` plus `h3_index.parquet`
- `places.sqlite` (FTS5 over OS Open Names, Code-Point Open postcodes, NaPTAN stations)
- `sources.yaml` (licence, attribution, share-alike flag, date verified; CI blocks unregistered sources) and `manifest.json`

Postgres, from the accounts phase: `users`, `shortlists`, `shortlist_items`, `entitlements`, `events`, `llm_calls`.

## 5. Ranking and LLM design

Ranking: `rank()` canonicalises the spec (sorted keys, weights rounded to 0.05), applies hard filters (budget fit, per-destination time caps, exclusions), then scores each area as a weighted mean of within-London percentiles plus a piecewise commute decay averaged across destinations. Missing features are dropped and weights renormalised, never imputed. Ties break on area id. The contribution table is the single source for chips, explanations and tests.

LLM: Haiku 4.5 for parse and refine, with structured outputs, a cached prefix above 4,096 tokens and model ids in config. Explanations use the Citations API over one fact per block; every numeral and place name must appear in a cited fact or the block is replaced by a template. Raw user text never reaches the explanation call and is not persisted. Reason chips ship first because they are the fallback anyway. No offline Opus profile generation in v1.

Disagreement 2 (demographics): keep the founder's input, narrowly. Tenure, dwelling type and build period describe homes and are ordinary features. Share of households with dependent children and student share may feed only the positive tags "family-oriented" and "student-heavy"; they can never be a filter, a negative weight or an exclusion. Age bands are out of ranking, since age is a protected characteristic and schools, nurseries and venue mix carry the same signal. Ethnicity, religion, country of birth, language, sexual orientation, disability and health are never loaded into the ranking store; they are used only offline to audit features for proxy effects. Affinity requests are served through amenities. A code-level allowlist of feature ids enforces this.

Disagreement 3 (tag count): 12, formula-only: village feel, buzzy, leafy, creative, family-oriented, student-heavy, waterside, strong high street, evening venues, quiet residential, foodie, historic character. "Young professional" is dropped because it needs age bands. LLM-scored tags add review work, share-alike exposure and coverage bias before anyone has asked for them.

Disagreement 4 (embeddings): deferred. With 450 areas and a vocabulary that fits in the cached prompt, the parse call already maps language to tags. Log `unmet_requests`; revisit if more than 10 percent of real queries contain vibe phrases that map to no tag.

Disagreement 9 (safety): rankable, but off by default and never called "safety". The dimension is "recorded crime": category rates with residents-plus-workday denominators, shrinkage and a 24-month window. Its weight is zero unless the user asks or moves the slider. Profiles show category rates with caveats and no composite score. The words safe, unsafe and dangerous are banned from generated text.

## 6. Roadmap

| Phase | Goal and build | Human work | Exit criteria | Size |
|---|---|---|---|---|
| 0. Spikes | Four parallel spikes: (a) inspect BODS GTFS for Tube, DLR and tram, run R5 on 200 origins; (b) Overture versus FHRS counts for 20 known neighbourhoods; (c) v0 gazetteer by merging MSOAs on base name, measure OS Open Names coverage; (d) Haiku parse latency and token counts on 30 prompts | Register for BODS and Rail Data Marketplace, create Anthropic key with spend limit, start trade mark search and Apple enrolment | Timetable source chosen; routing hours measured; Overture threshold set or tags trimmed; parse p50 under 2 s | 1 week |
| 1. Commute finder | Repo scaffold, release bundle, three matrices, cost model, form-based web page: two workplaces plus budget gives ranked neighbourhoods with times. No LLM | Curate inner London boundaries; put it in front of 5 people who are moving | 90 percent of 200 sampled pairs within 5 minutes of TfL Journey Planner; 5 people complete a search | 2 weeks |
| 2. Describe your life | Feature store, 12 tags, PreferenceSpec, parse call, ranker with contributions, chips, sliders, URL share links, policy redirect | Write golden set (100 queries, 40 neighbourhoods with expected tags); finish boundary review | Golden set passes in CI; 20 to 30 closed-beta users | 2 to 3 weeks |
| 3. Explain, profile, compare | Cited explanations with verifier, chat refinement, static profile pages, compare view, attribution and methodology pages, proxy audit | Legal review (Equality Act, ODbL, privacy), DPIA, ICO fee | No ungrounded numeral in a 500-explanation sample; legal sign-off | 2 to 3 weeks |
| 4. Accounts and launch | Supabase Auth, shortlists, deletion, entitlements, quotas, Turnstile, spend circuit breaker, Sentry | Vendor accounts, SMTP, domain, privacy notice, launch | Public web launch | 1 to 2 weeks |
| 5. iOS | Map spike, SwiftUI client, tile Worker, AI permission screen, TestFlight | App Store submission and review replies | App approved | 3 to 4 weeks |
| 6. On evidence only | Asking-rent calibration, extra matrices, embeddings, passes and payments, second city | Pricing and partnerships | Triggered by usage data | Open |

Each phase stands alone: phase 1 is already a multi-destination commute finder. Public web launch lands around 9 to 11 weeks from start. Unverified claims to clear in phase 0 are listed per domain in the research reports.

## 7. Top risks

| Risk | Mitigation |
|---|---|
| BODS GTFS lacks Tube, DLR or tram, or routing takes far longer than estimated | Phase 0 spike; convert TfL TransXChange instead; shorten the window or drop unpopulated origins |
| Boundaries feel wrong and curation (3 to 4 person-weeks) is underestimated | v0 from MSOA names unblocks engineering; review inner London first; soft edges, "approximate" wording, report-a-boundary link |
| Overture Places is poor in London | FHRS is the primary count for food and drink, GLA data for culture; drop any tag that fails the golden set |
| Steering or discrimination claims | Feature allowlist in code, positive-only household tags, recorded crime off by default, proxy audit, legal review before launch |
| An explanation states something not in the data | Chips first; per-block verifier; template fallback; perturbation tests in CI |
| Anonymous traffic runs up LLM spend | Quotas per device and account, Turnstile, parse cache, daily circuit breaker to deterministic mode, workspace spend limit |
| Rent figures mislead: PIPR measures all tenancies, and ONS may stop the postcode-district workbook | Label "typical rent paid", show ranges and tiers; model degrades to the price-ratio prior; add paid calibration only if beta users are misled |
| Haiku 4.5 is retired during the build (not sooner than 15 October 2026) | Model ids in config; golden set is the migration gate; Sonnet 5 tested as drop-in |

## 8. Decisions the founder must make

1. Scope of demographic inputs. Recommendation: accept the positive-only rule in section 5 and have a solicitor confirm it.
2. ODbL on the travel-time matrix. Recommendation: agree now to publish the recipe and offer the matrix if counsel says share-alike applies.
3. Who curates the gazetteer and golden set. Recommendation: the founder plus one paid reviewer with local knowledge of the half of London the founder knows least.
4. Raw prompt retention. Recommendation: do not persist; 30-day operational logs only; evaluation corpus is opt-in.
5. Anonymous search. Recommendation: yes, three searches a day without an account; Apple's guideline 5.1.1(v) favours it.
6. Geographic edge. Recommendation: Greater London only for both homes and destinations at launch.
7. Domain and trade mark clearance for Burro. Recommendation: commission a UK IPO search in classes 9, 36 and 42 this week and pick a modifier domain if the .com is unavailable.
8. Legal entity and a one-off fixed-fee legal review. Recommendation: budget for it before phase 4; it gates launch, not the beta.

## 9. What you would deliberately not do

- Ingest, scrape or link to listings.
- Let the model rank, re-rank or describe areas from its own knowledge.
- Run a routing engine, vector database, orchestrator or general chat surface in production.
- Put area data in Postgres, or add Postgres before accounts need it.
- Buy data (TravelTime, PropertyData, OS premium, Google) before users show the open data is insufficient.
- Compute nine matrices when three answer the hero question.
- Publish a composite safety or liveability score.
- Show ethnicity or religion breakdowns, even "for information".
- Generate profile prose with an LLM before a human has time to review it.
- Build payments, passes or paywalls before there is retention to price.
- Start iOS before the web product has real users.
- Add a second city before London's golden set passes on every release.