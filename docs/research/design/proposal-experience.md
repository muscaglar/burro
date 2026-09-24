## 1. v1 in one paragraph

Burro v1 is a free website, followed by a native iOS app, where someone who has never been to London types one sentence about their life and, about two and a half seconds later, sees roughly 450 named neighbourhoods coloured by fit on a map, with a ranked list in which every card says where the place is in plain words, gives three reasons it matched and admits one trade-off. Ranking is deterministic arithmetic over precomputed open data: door-to-door travel times to several destinations, rent and price estimates, about 20 formula-defined vibe tags and liveability percentiles. Claude only turns language into an editable PreferenceSpec and writes cited sentences that are verified before display. If Claude is slow or down, the same chips become a form and the product still works. Profiles, comparison, share links and shortlists complete the loop: decide, discuss with a partner, visit.

## 2. What is in v1 and what is cut

**In, in the order a user meets it**

- **Landing.** A live London map behind one prompt box, a renter/buyer toggle and three relocator-style example prompts whose results are precomputed. No login. One line of AI disclosure.
- **Results.** Choropleth over every ranked neighbourhood, top ten pinned, with a list view as the accessible equivalent. Each card has the name, an orientation line built from facts ("South-east, Zone 2, 12 min to London Bridge"), three reason chips, one trade-off chip (the largest negative contribution), and source and date on tap.
- **Interpreted chips.** Everything Burro assumed (budget, bedrooms, destinations, modes, tags) is an editable chip. Chips, sliders and chat all emit the same typed operations.
- **Commute as the hero.** Up to four destinations by public transport, cycling or walking, with "direct" or "one change" labels and a map toggle between fit and minutes.
- **Area profiles.** Static, indexable pages at `/london/{slug}`: reviewed prose, cited facts, rent and price ranges with confidence tiers, crime by category, schools by attainment, similar areas, and up to five attributed photos from Wikimedia Commons or Geograph. A stranger needs to see the place.
- **Compare.** Up to three areas side by side, rows ordered by the user's own weights, differences written as templated sentences.
- **Share.** The link stores spec, data snapshot and engine version, shows chips only (never the raw prompt), and lets a partner fork and re-weight.
- **Save.** Hearts work anonymously on the device. Signing in (Apple, Google or email code) syncs them as a shortlist.
- **"Take it to the portals" card.** Area name plus its postcode districts with a copy button. Plain text, no links. This settles disagreement 6: listing links are already out of v1, and the large portals prohibit deep links without written consent.
- **iOS.** The same features plus three native reasons to exist: an offline shortlist with cached profiles for viewing days, "Where am I?" (point-in-polygon on the device, location never sent), and the share sheet.

**Cut or deferred**

Payments; embeddings; LLM-scored tags; evening, weekend and night travel matrices; price per square metre; school catchments; 20 m air quality until the GLA confirms its licence; LLM-written comparison narratives; user-written text on shared pages; passkeys; driving.

## 3. Architecture

**Components**

- **Web:** Next.js on Vercel (London), static profile pages, MapLibre GL JS.
- **iOS:** SwiftUI, MapLibre Native, generated Swift client.
- **API:** FastAPI on Fly.io London, server-sent events with Burro's own event schema.
- **Core:** `packages/core`, pure Python ranking, spec reducer, fact builder and verifier.
- **Pipeline:** Python and DuckDB writing versioned Parquet releases; R5 through r5py in a pinned Docker image on a rented VM.
- **Data:** Supabase Pro London (Postgres, PostGIS, Auth); Cloudflare R2 and a Worker for tiles.
- **LLM:** Claude Haiku 4.5 online; an Opus-class model through the Batch API for offline profile prose. Model IDs live in config.

**How a search flows**

1. The client opens `POST /v1/search` as a stream. The server emits `status` at once.
2. The normalised prompt is looked up in a 24-hour cache. On a miss, Haiku returns a schema-constrained PreferenceSpec with assumptions and unmet requests.
3. Destination strings resolve through Burro's own gazetteer (OS Open Names, Code-Point Open, NaPTAN) to an H3 cell. Ambiguity produces the only clarifying question Burro asks, as tappable options.
4. `rank(spec, snapshot, engine_version)` runs in memory. The server emits `spec` and `results` and stores the snapshot behind the share link.
5. For the top five, a fact pack goes to Haiku with Citations. Every block is verified (each numeral and place name must match a cited fact) before it is sent. Failures fall back to templates.
6. Sliders and chips call `POST /v1/search/rank` directly. Chat asks the LLM for typed operations, then uses the same reducer.

**Precomputed per data release:** neighbourhood polygons and tiles, travel-time matrices and roll-ups, metrics, percentiles, tag scores, facts, similar-area lists, reviewed profile prose and photos, results for example prompts.

**Computed per request:** interpretation (one LLM call, cached prefix), destination resolution, ranking arithmetic (under 20 ms), explanation prose for the top five, snapshot write.

**Latency targets**

| Event | p50 | p95 |
|---|---|---|
| Landing map interactive on 4G | 2.0 s | 3.5 s |
| Submit to first acknowledgement | 0.2 s | 0.4 s |
| Submit to interpreted chips | 1.2 s | 2.5 s |
| Submit to ranked map and list | 2.5 s | 4.0 s |
| First explanation sentence | 3.5 s | 6.0 s |
| Slider or chip re-rank | 150 ms | 400 ms |
| Profile or shared link open | 0.5 s | 1.2 s |

Relocators are often on another continent, so tiles, overlay and pages are cached at the edge and rank responses stay under 10 KB.

**When the LLM is slow or unavailable**

| Level | Trigger | What the user gets |
|---|---|---|
| 1 | Explanation slow or fails verification | Reason chips and template sentences. Nothing looks broken |
| 2 | Interpretation exceeds 4 s, errors, or the daily spend breaker trips | A rule-based parser (money, bedrooms, "minutes to X", gazetteer names, a phrase-to-tag lexicon) pre-fills the chips as a form. A banner says smart reading is paused |
| 3 | API down | Static profiles, shared snapshots and the iOS offline shortlist still work |

The level 2 form is the ordinary chip UI in a different state, not a second product.

**iOS map (disagreement 8).** MapLibre Native, because one style and one tile set keeps two clients thin. Avoid its two immature parts: colour areas with a `match` expression instead of feature-state, and serve z/x/y tiles from the Worker instead of reading PMTiles directly. Bundle the simplified neighbourhood overlay in the app. A one-day device spike confirms this; MapKit polygons are the fallback.

**Entitlements (disagreement 7).** `plans`, `plan_features`, `entitlements(user_id, key, source, status, period_end)` and one `require_entitlement()` check. With `period_end`, a time-boxed pass and a renewing subscription are the same row shape.

## 4. Geography and data model

**Base grid (disagreement 1): two cell systems, each used for what it is good at.**

- **Output Areas (26,369) are the canonical cell** for membership, statistics and travel-time origins. Neighbourhoods are sets of OAs, census counts roll up exactly, and population-weighted centroids sit where people live.
- **H3 resolution 9 (about 15,000) is the travel-time destination grid** and the kernel grid for place densities. Any workplace snaps to a hexagon whether or not anyone lives there.
- **LSOA is a join level only.** LSOA-native data is applied to child OAs through the ONS lookup, with `native_resolution` recorded so explanations can say a figure comes from a wider area.

The full OA-to-H3 matrix (about 395 MB each at one byte per pair) stays in object storage. The API memory-maps a roll-up of neighbourhood by destination hexagon: population-weighted median plus the 10th and 90th percentile across OAs, about 20 MB per matrix. Boundaries can therefore be redrawn without re-routing. If the benchmark shows OA origins need more than eight hours, fall back to LSOA centroids. v1 computes six matrices: public transport morning peak p50 and p85, one-ride and two-ride limits, cycling, walking.

**OpenStreetMap (disagreement 5).** Use OSM where nothing replaces it: the basemap and the routing network. Treat travel-time matrices as ODbL-derived, keep them as separate files joined only by key at query time, and be ready to publish the neighbourhood roll-up under ODbL. OSM stays out of the gazetteer, place features and scoring tables, enforced by a CI lineage check.

**Main tables and files**

| Name | Purpose |
|---|---|
| `gazetteer/london/oa_to_neighbourhood.csv` | Source of truth, reviewed by diff |
| `cell`, `neighbourhood`, `neighbourhood_cell`, `neighbourhood_alias`, `slug_history` | Geography with immutable opaque IDs |
| `place` | Destination autocomplete |
| `metric`, `cell_metric`, `neighbourhood_metric` | Catalogue, values, percentiles, confidence tier, vintage |
| `tag`, `neighbourhood_tag` | Formula definitions and scores |
| `fact`, `profile`, `photo` | Citable facts, reviewed prose, attributed images |
| `source_registry`, `data_release` | Licence, attribution, pinned release |
| `tt/{release}/*.zarr`, `tt/{release}/nbh_*.npy` | Full matrices and serving roll-ups |
| `search`, `spec_version`, `shortlist`, `shortlist_item` | User state |
| `users`, `plans`, `plan_features`, `entitlements`, `llm_calls` | Accounts and operations |

## 5. Ranking and LLM design

**Ranking.** Hard filters first (budget and commute caps when marked strict), then a weighted mean of within-London percentile utilities, with missing features dropped and weights renormalised. With several destinations the slowest commute drives the score by default, because a couple needs both to work. Budget fit uses the "asking rent if you move in now" estimate (the ONS-anchored model with PropertyData calibration), because a newcomer signs a new tenancy. Per-feature contributions are returned and generate the chips.

**Demographics (disagreement 2).** One rule: Burro ranks places, never the protected characteristics of residents. Age bands are excluded along with ethnicity, religion and every other protected characteristic. Household and housing structure that is not protected (tenure mix, dwelling type, share of households with dependent children, student share, density) may feed tags, but only as positive soft inputs capped at 30% of any tag's weight, never as a filter or an exclusion. "Young professional" is not a tag; the phrase maps to buzzy, evening venues, cafe culture and a fast commute. Excluded census tables load only into an offline audit schema for a proxy-correlation check.

**Tag count (disagreement 3).** About 20 tags, all formulas over data, none scored by an LLM. Every tag needs a golden set, a Londoner's sanity check and an explanation, and LLM scoring from open text favours well-documented central areas. Breadth of language is handled by a phrase lexicon in the cached prompt. `unmet_requests` logs show which tag to add next.

**Embeddings (disagreement 4).** Deferred. "Areas like Peckham" uses nearest neighbours on the standardised feature vector, which can be explained. Revisit if more than 10% of real queries contain vibe phrases that match no tag.

**Safety (disagreement 9).** Rankable, but opt-in. "Lower recorded crime" enters the score only when the user asks for it or switches it on; its default weight is zero. It is built from category rates with residents-plus-workday denominators and shrinkage. Profiles show categories against the London distribution with caveats. There is no composite badge, and the words "safe" and "unsafe" never appear.

**LLM boundaries.** Three online call types (interpret, refine, explain). None can rank. The explain call never receives raw user text. Raw prompts are kept only in 30-day logs. CI runs ranking and verifier tests with no LLM, and a 200-query golden set gates every prompt or model change.

## 6. Roadmap

About 15 weeks elapsed. Boundary curation is the critical path.

| Phase | Goal and what gets built | Human must | Exit criteria | Size |
|---|---|---|---|---|
| 0. Spikes (parallel) | S1: inspect BODS GTFS for Tube, DLR and tram; run R5 on 200 OA origins; compare 1,000 pairs with TfL Journey Planner. S2: Overture Places against FSA data in 20 neighbourhoods. S3: interpretation latency and token counts from the UK and overseas. S4: 450 polygons on a mid-range iPhone. S5: a thirty-second prototype on fake data | Open vendor accounts; read Rail Data Marketplace terms; recruit five recent relocators; commission a trade mark search; brief a solicitor | Tube data present or TransXChange fallback chosen; median error against TfL under 5 minutes; chips p50 under 1.2 s; four of five testers can say why the top area was suggested | 2 weeks |
| 1. Walking skeleton | Monorepo, CI, OpenAPI contract, source registry with CI gate, rough gazetteer from MSOA names, eight features, prompt to map on staging | Review conventions | `just ci` green; end-to-end search for all London | 2 weeks |
| 2. Data depth | Six matrices, rent and price model with backtest, liveability metrics, place features, 20 tags, facts, similar areas, a curation review page | 3 to 4 person-weeks of boundary curation, inner London first; tag golden set for 50 areas; licence emails to GLA and ONS | Golden sets pass; backtest error published; every source registered | 5 weeks |
| 3. Web product | Full search UX, verifier, degraded modes, profiles, compare, share, accounts, shortlists, accessibility, attribution page | Review 450 profiles and photos (about 30 hours); privacy notice and terms | Latency targets met; verifier failures under 2%; WCAG 2.2 AA audit passed | 3 weeks, overlapping phase 2 |
| 4. iOS | SwiftUI app, offline shortlist, "Where am I?", AI permission screen, account deletion | Apple Developer enrolment, store assets, demo account | TestFlight build passes the pre-submission checklist | 3 weeks, overlapping phase 3 |
| 5. Beta and launch | Private beta with 30 relocators, abuse and load tests, spend-breaker drill, proxy audit, DPIA | Legal sign-off, ICO fee, App Store submission | Public web launch; iOS on approval | 3 weeks |

## 7. Top risks

1. **It reads like a spreadsheet, or no better than a chat assistant.** Spike S5 with real relocators; orientation line, trade-off chip and photos; launch on one hero, "two workplaces, one map".
2. **Boundary curation is underestimated and locals dispute the lines.** Ring-fence the human time; pay a second reviewer; soft edges; a "report this boundary" link; versioned gazetteer.
3. **Travel times are wrong (BODS lacks the Tube; timetables are optimistic).** Spike S1; TransXChange fallback; validation harness; label as "typical timetabled time" and show p85.
4. **Newcomers trust a rent figure that understates asking rents, or ONS stops the district workbook.** Two labelled figures; PropertyData calibration; the model degrades to the price prior; ranges and confidence tiers.
5. **Steering and Equality Act exposure.** Feature allowlist enforced in code; positive-only household inputs; opt-in crime; offline proxy audit; legal review.
6. **An explanation states an invented fact, or interpretation misses the latency budget.** Citations, per-block verifier and templates; perturbation tests; 4-second timeout ladder; measured in spike S3.
7. **Automated abuse runs up LLM cost.** Turnstile, per-device quotas, sign-in after a few searches, daily spend breaker that drops to form mode.
8. **Licence contamination or drift (ODbL, CC BY-SA, withdrawn datasets).** Source registry with CI block; quarantined OSM-derived files; prose written from facts only; snapshots of every input.

## 8. Decisions the founder must make

1. **Narrow "demographics" to household and housing structure, positive-only.** Recommend yes. It keeps the brief's intent and gives a solicitor a line to defend.
2. **Crime as an opt-in ranking dimension.** Recommend yes. Newcomers ask for it.
3. **Publish the neighbourhood travel-time roll-up under ODbL.** Recommend yes. It removes the share-alike question cheaply.
4. **Premium shape.** Recommend a time-boxed "move pass" (week, month, quarter) over a perpetual subscription. Nothing to build now; decide before payments work starts.
5. **Second curator.** Recommend paying someone with local knowledge for about 40 hours.
6. **PropertyData at GBP 28 a month.** Recommend yes, as calibration only.
7. **One fixed-fee legal review** of the Equality Act position, ODbL aggregates, CC BY-SA and privacy documents. Recommend yes, booked in phase 0.
8. **Geographic scope.** Recommend Greater London for areas, plus about 20 destination points outside it (airports, Reading, Watford, Cambridge).

## 9. What I would deliberately not do

- Let the LLM choose, rank or re-rank areas, or describe a place from its own knowledge.
- Build a chatbot persona. Chat is one way to edit the chips, not the product.
- Interview the user before showing results. Show results with visible assumptions.
- Add a second ranking implementation on the client. One engine, tested once.
- Show a single safety score, liveability index or match percentage without its breakdown.
- Ingest or link to listings, scrape anything, or use Google Places or Street View.
- Put embeddings, a workflow orchestrator or a routing server in v1.
- Hand-draw polygons. Boundaries change only through the reviewed OA assignment file.