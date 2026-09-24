# Burro v1 plan: trust, correctness and legal safety

## 1. v1 in one paragraph

Burro v1 ranks about 450 named London neighbourhoods on a map for a renter or buyer who describes the life they want and names one or more commute destinations. Ranking is a pure, versioned function over precomputed open data. Claude works only at the edges: it turns language into a schema-constrained preference spec, and it writes explanations from a per-area fact pack that are verified before display. Every number carries a source, date, native resolution and confidence tier. Every dataset needs a licence-registry entry with evidence before it can be ingested. Nothing ranks on who lives somewhere. Web launches at about week 20 and iOS about six weeks later. Roughly a third of that schedule is curation, review, audit and legal work that agents cannot do.

## 2. What is in v1 and what is cut

**In**
- Natural-language search, ranked map, editable assumption chips, weight sliders, and chat refinement through typed operations.
- Multi-destination commute by public transport, cycling and walking: typical (p50) and "just missed it" (p85) minutes, plus a direct / one change label.
- About 30 features in 8 dimensions and 16 formula-defined vibe tags.
- Rent by bedroom count and sale price by property type, shown as ranges with confidence tiers and an as-of month.
- Human-reviewed area profiles, side-by-side comparison, and share links that pin data release and engine version.
- Accounts (Apple, Google, email code) for shortlists only, with in-app deletion. Search needs no login.
- Public methodology, fairness note, and data sources and licences pages; a report-a-problem link on every profile.
- Entitlements table with everyone on the free plan.

**Cut**
- Portal links and listings (disagreement 6: already out of v1; the portals' terms forbid deep links without written consent).
- Embeddings and LLM-scored tags.
- Price per square metre, bedroom-level sale prices, school catchment claims, any synthesised Ofsted grade.
- LAEI 20 m air quality, Planning London Datahub and the 2025 Cultural Infrastructure Map, until GLA confirms licences in writing.
- Night-time matrix, destinations outside Greater London, itinerary detail.
- Payments code, photos, user-written text on shared pages.
- Any display of ethnicity, religion, country of birth, language, health or disability data.

## 3. Architecture

**Components**
- `registry/sources.yaml`: licence registry (licence, evidence URL, date verified, attribution string, share-alike flag, pinned release). CI fails on any unregistered source or any table mixing share-alike and other columns. The attribution page is generated from it.
- `packages/pipeline`: plain Python and DuckDB writing Parquet to immutable releases, each with a `manifest.json` of input checksums and code commit.
- `packages/core`: pure Python with no IO. Holds the preference model, `rank(spec, release_id, engine_version)`, the operation reducer and the explanation verifier.
- `services/api`: FastAPI on Fly.io London; Supabase Postgres and Auth in London; one committed OpenAPI file generating the TypeScript and Swift clients.
- Clients: Next.js on Vercel; SwiftUI with MapLibre Native.
- Tiles: Protomaps basemap and a neighbourhood overlay on Cloudflare R2 behind a Worker.

**Search flow**
1. **Parse.** Claude Haiku 4.5 with structured outputs returns a status and a PreferenceSpec that can only name allowlisted feature and tag IDs. Destinations come back as strings and are resolved by Burro's own gazetteer (OS Open Names, Code-Point Open, NaPTAN). Raw prompts are not persisted; operational logs keep them 30 days at most.
2. **Rank.** The spec is canonicalised and hashed. Hard filters run first, then a weighted mean of within-London percentiles, with a stable tie-break. The output includes per-feature contributions and is stored immutably for share links.
3. **Render.** Static tiles plus a small id-to-score JSON, with a list view for accessibility.
4. **Explain.** Deterministic reason chips carry every number and always show. Claude prose is an enhancement using the Citations API over one fact per block. The server drops any block whose numerals or place names are not in the cited facts and falls back to templates.
5. **Refine.** Chat emits typed operations; sliders emit the same operations with no LLM call.

**Precomputed versus per request**

| Precomputed per release | Per request |
|---|---|
| Gazetteer, features, percentiles, tags | Parse call (LLM) |
| Travel-time matrices and rollups | Destination lookup |
| Housing estimates, fact packs | Ranking arithmetic (milliseconds) |
| Reviewed profile text, tiles, similar areas | Explanation call, cached by area and spec signature |

**iOS map (disagreement 8).** MapLibre Native, for style and attribution parity with web. Colour with a match expression rather than the two-week-old feature-state, serve z/x/y from the Worker so tiles cache, and bundle the overlay in the app.

**Pricing (disagreement 7).** Entitlement rows carry `source` and `period_end`, so a time-boxed pass and a recurring subscription are both data changes. The premium-later decision stands and needs no code in v1.

## 4. Geography and data model

**Base grid decision: one canonical cell, one destination index.**

- **Canonical cell: 2021 Output Area (26,369).** All membership, statistics and travel-time origins use it. Census counts roll up as exact sums, so the pipeline contains no areal interpolation step for anyone to challenge. Population-weighted centroids sit where people live.
- **Destination index: H3 resolution 9 (about 15,000 cells).** Workplaces sit where few people live, so destinations need uniform coverage. Each hexagon snaps to its nearest routable street node.
- **LSOA is a join level, not a cell.** LSOA-native data is applied to child OAs, with `native_resolution` recorded and shown to users.
- **Point data** (venues, greenspace) is computed as distance-decay accessibility from OA centroids, not in-polygon counts.

The travel-time matrix is therefore asymmetric: OA origins by H3 destinations, about 395 million pairs or roughly 400 MB per matrix. That is about 1.75 times the compute of the hex-only plan, still hours on one VM. If the benchmark spike shows it is too slow, origins fall back to LSOA centroids. The API loads only the neighbourhood-by-destination rollup (450 by 15,000); the full matrix stays in object storage for audit.

**OpenStreetMap (disagreement 5).** The matrix is derived from OSM and I would not pretend otherwise. It lives in a quarantined artefact, is linked to other data only by key, and is never blended into another feature. The founder commits in advance to offering it under ODbL if counsel says it is a publicly used Derivative Database. The gazetteer partition uses OS Open Roads (OGL) for network distance, so the polygons stay OSM-free. No OSM features enter scoring in v1.

**Main tables and files**

| Name | Contents |
|---|---|
| `gazetteer/london/oa_assignment.csv` | 26,369 rows, OA to neighbourhood, reviewed by pull-request diff |
| `neighbourhood` | Immutable ID, slug, aliases, rankable flag (under about 3,000 residents is not ranked), `superseded_by` |
| `cell`, `cell_neighbourhood` | Generic cell with system, representative point, population; membership weight |
| `metric_catalogue` | Feature ID, sources, native resolution, aggregation, polarity, vintage, rankable, share-alike |
| `cell_metric`, `neighbourhood_metric` | Value, percentile, coverage, sample size, confidence tier |
| `tag_definition`, `neighbourhood_tag` | Versioned formula and scores |
| `tt_matrix_*` (quarantined), `tt_neighbourhood_dest` | Full matrices; rollup of p50, p85 and range |
| `housing_estimate` | Lower quartile, median, upper quartile, tier, as-of |
| `fact` | One row per displayable fact with source and release; the only input to explanations |
| `profiles/<id>.md` | Reviewed text with generation metadata |
| App tables | `users`, `shortlists`, `search_result`, `plans`, `entitlements`, `llm_calls` |

## 5. Ranking and LLM design

**Ranking.** Features are converted to rates, shrunk toward the borough mean for small counts, then to within-London percentiles. Missing features are dropped and weights renormalised, with a coverage badge; nothing is imputed. Commute uses a piecewise decay over precomputed minutes, combined across destinations by worst case or weighted sum.

**Demographics (disagreement 2).** Three tiers, enforced by the code allowlist and not by the prompt.

| Tier | Variables | Use |
|---|---|---|
| A | Tenure, dwelling type and size, density, residential churn, student share | Rankable |
| B | Age bands, household composition | Descriptive on profiles only |
| C | Ethnicity, religion, country of birth, national identity, language, sexual orientation, gender identity, disability, health, sex, partnership status | Never loaded into the product database; used offline for the proxy audit |

This keeps the founder's "demographics as a vibe input" through Tier A. Age stays out of ranking because it is a protected characteristic, and a ranking that uses it is the first thing a solicitor would ask about. "Family-oriented" and "young professional" are built from nurseries, schools, play space, dwelling size and evening venues. Counsel may later promote Tier B to a positive soft preference. The IMD composite rank is never a feature. Requests to avoid a group get one neutral sentence and the rest of the query is served. Positive affinity requests are met through amenities such as places of worship, venues and shops.

**Tag count (disagreement 3).** Sixteen tags, each a published formula over registered features, with no LLM scoring. A tag ships only when it passes the golden set. Unmapped vibe phrases are returned as "unmet requests" and counted, and that count decides which tag to add next.

**Embeddings (disagreement 4).** Deferred. They are opaque, can carry demographic proxies from text, add a vendor, and draw CC BY-SA text into the ranking path. Revisit if more than 10% of real queries contain unmapped vibe phrases.

**Safety (disagreement 9).** Rankable only when the user asks, with a default weight of zero. It uses recorded-crime rates by category over 24 months with residents-plus-workday denominators. There is no composite safety score and the words "safe" and "unsafe" are never used. Profiles show categories with caveats. Counsel may demote this to profiles only.

**Verification**
- Tag golden set: 40 to 60 neighbourhoods with expected tags, run on every release.
- Query golden set: 150 to 250 queries with field-level assertions.
- Commute: about 1,000 origin-destination pairs checked against TfL Journey Planner.
- Housing: leave-one-out backtest, with the error published.
- Explanations: perturbation and missing-data tests in CI.
- Proxy audit: each rankable feature's correlation with Tier C census shares, documented in the DPIA.

## 6. Roadmap

Sizes are elapsed time with agents writing most code. Phases 2 and 3 overlap.

| Phase | Goal and build | Human work | Exit criteria | Size |
|---|---|---|---|---|
| 0. Foundations | Repo skeleton, licence registry and CI gate, release manifest | Form the legal entity; commission UK trade mark search; register on Rail Data Marketplace; put licence questions to GLA, ONS, FSA and PropertyData; engage a solicitor | CI rejects an unregistered source | 1 week |
| 1. Spikes | BODS GTFS mode check and 200-origin R5 benchmark; Overture versus FHRS in 20 neighbourhoods; gazetteer v0 from MSOA names; parse latency and verifier failure rate; MapLibre iOS with 600 polygons | Read results, sign the decision records | Written go or fallback per spike | 2 weeks |
| 2. Data spine | Curated gazetteer, all feature pipelines, full matrices, housing model, tags, both golden sets | Gazetteer curation of 100 to 150 hours plus a second local reviewer; agree golden-set expectations | Golden sets pass; commute validation within tolerance; backtest published; no source without evidence | 6 weeks |
| 3. Core and API | Ranking engine, spec, reducer, fact table, verifier, endpoints, proxy audit | Review audit findings; approve feature allowlist | Property tests green; audit documented | 3 weeks |
| 4. Web product | Search, map, profiles, comparison, share links, accounts, deletion, methodology pages | Copy and design review | End-to-end flows pass; WCAG 2.2 AA check | 4 weeks |
| 5. Review and legal | Offline profile generation, steering test suite, DPIA, privacy notice | Review every profile (15 to 30 hours); solicitor opinion; pay ICO fee; closed beta with 20 to 30 people | Counsel sign-off; zero ungrounded sentences in beta sample | 3 weeks |
| 6. Web launch | Spend circuit breaker, monitoring, corrections process | Launch, triage reports | One week stable | 1 to 2 weeks |
| 7. iOS | SwiftUI client, AI permission screen, privacy labels | Apple Developer enrolment, App Review | Approved | 5 to 6 weeks |

Web launch lands around February 2027 and iOS around late March.

## 7. Top risks

1. **Steering or discrimination claim.** Mitigation: tiered demographics, code allowlist, proxy audit, adversarial prompt tests, counsel review.
2. **A wrong number or sentence about a real place.** Mitigation: numbers come only from the fact table; per-block verifier with template fallback; ranges and tiers; corrections link.
3. **Licence unproven or share-alike leakage.** Several licences are unconfirmed, and the research reports disagree on FHRS. Mitigation: registry with evidence, CI gate, quarantined OSM artefact, Wikipedia used only as an attributed excerpt.
4. **Timetable feed lacks Tube, DLR or tram.** Mitigation: week-two inspection; TfL TransXChange conversion as the fallback; the 1,000-pair validation.
5. **Gazetteer disputed or curation overruns.** Mitigation: ring-fenced hours, inner London first, soft map edges, versioned boundaries, border sensitivity test.
6. **Rent figures mislead.** PIPR measures all tenancies, and the ONS district workbook may have stopped. Mitigation: separate "typical rent paid" and "asking rent now" figures; a model that degrades to the price prior; archive every past edition.
7. **Vibe tags fail a local sanity test** because Overture quality is unmeasured. Mitigation: spike, FHRS as the primary food and drink count, golden set on every release.
8. **Special category data in prompts, and transfer to the US.** Mitigation: structured extraction only, no raw prompt persistence, DPIA, disclosure, iOS permission screen.

## 8. Decisions the founder must make

| Decision | Recommendation |
|---|---|
| Accept the demographic tiering, with age and household composition out of ranking | Yes, pending counsel |
| Commit to publishing the travel-time matrix under ODbL if advised | Yes; low commercial cost, removes the largest licence doubt |
| Fund a fixed-scope legal opinion (Equality Act position, ODbL and derived data, CC BY-SA and summaries, privacy notice and DPIA) | Yes, before beta |
| Crime rankable on request, or profiles only | Rankable on request, default weight zero |
| Who curates the gazetteer and golden sets | Founder plus one paid reviewer with knowledge of the other half of London |
| PropertyData at about £28 a month for asking rents | Yes, only after written confirmation that derived figures may appear on public pages |
| Raw prompt retention for evaluation | No; use synthetic and opt-in examples |
| Primary domain | Decide in phase 0, after the trade mark search |

## 9. What I would deliberately not do

- Let the LLM rank, re-rank, score tags, or state any figure absent from the fact table.
- Put OSM into the gazetteer or scoring features, or blend it with another source.
- Use Google Places or Street View, the VOA rating list, or council appraisal text.
- Publish a composite safety or liveability score, or use the IMD rank as a feature.
- Impute missing data, or show a point estimate where only a range is defensible.
- Store raw prompts, or show user-written text on shared pages.
- Ingest any source on an assumed licence.
- Ship a data release that has not run the golden sets and produced a diff report.
- Build payments, portal links, embeddings or a routing service before launch.