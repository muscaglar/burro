# transit-routing: Travel times and transport data (London public transport, cycling, walking)

## Headline
Precompute a full cell-to-cell travel-time matrix for London offline (about 15,000 H3 resolution-9 cells, so about 225 million pairs per matrix, 225 MB each as uint8 minutes) with the open-source R5 engine driven from Python via r5py, using open timetables (BODS GTFS for bus/Tube/DLR/tram, National Rail CIF converted to GTFS for Overground, Elizabeth line and rail) plus OpenStreetMap. Serve commute queries as a pure array lookup with no routing engine in the request path. Use the free TfL Unified API Journey Planner only for itinerary detail on the top few results. Keep self-hosted MOTIS as the on-demand fallback and TravelTime as the paid fallback.

## Summary
WHAT I WOULD BUILD
1. Inputs (all free, all commercially usable with attribution): BODS GTFS London region (OGL), National Rail timetable from Rail Data Marketplace (NWR Schedule is explicitly 'Open (OGL3)'), OSM Greater London extract from Geofabrik (123 MB, ODbL), NaPTAN stops (OGL). TfL's own Journey Planner timetables (TransXChange, 24 MB zip, daily) are the authoritative fallback for Tube/DLR/tram/bus.
2. Engine: R5 (MIT, v7.6 published Aug 2026) via r5py (dual GPL-3.0-or-later / MIT, needs JDK 21+). R5 is purpose-built for many-to-many matrices and returns percentiles of travel time across a departure window, which is exactly the 'typical commute' statistic Burro needs. OpenTripPlanner 2's own docs say it has dropped analytics and recommend R5 for this.
3. Grid: H3 res 9 (average cell 0.105 km2, edge about 200 m). Greater London is about 1,572 km2, so about 15,000 cells. Same grid for origins and destinations. Roll up to named neighbourhoods with a population-weighted median.
4. Matrices: weekday AM peak (departures 07:00-09:00) p50 and p85; AM peak limited to one ride (direct) and two rides (one change) to derive interchange counts without an itinerary engine; weekday evening p50; Saturday midday p50; optional Fri/Sat night p50; cycling; walking. About 7 to 9 matrices, roughly 2 GB raw, under 1 GB compressed.
5. Query: geocode destination, snap to its H3 cell, read one 15 KB column per destination per matrix. Multiple destinations are just multiple columns combined deterministically. Latency is sub-millisecond, cost is zero.
6. Refresh: quarterly plus after the May and December rail timetable changes and any major network change. One cloud VM (16-32 vCPU, 64 GB) for an estimated 1-4 hours, under GBP 20 per refresh (my estimate, to be benchmarked).

WHY NOT ON-DEMAND OR A COMMERCIAL API
- TfL Journey Planner API is free and commercially usable (500 calls/min) but building the matrix from it would take about 312 days at the rate limit. Good for detail, useless for bulk.
- Google Routes: transit matrix capped at 100 elements per request, USD 5-10 per 1,000 elements (the London matrix would cost over USD 1 million per window), and caching of travel times is restricted.
- TravelTime: technically the best commercial fit, but the free plan bans commercial use, production is a custom fixed annual fee with a 12-month minimum, caching is only allowed if written into the order, cached data must be refreshed every 60 days and deleted on termination.
- Mapbox: no public transport. HERE: pricing and caching terms were not confirmed.

KEY CAVEATS
- I did not download and inspect the BODS London GTFS, so whether it contains Tube, DLR and tram at good quality is not known. Verify in week one; fall back to converting TfL TransXChange.
- TfL does not publish GTFS (confirmed by TfL FOI response 2022). London Overground and Elizabeth line are not in TfL's timetable data; they come from National Rail data.
- The RDG 'Timetable' products on Rail Data Marketplace are labelled 'Open (restrictions may apply)'; the actual permitted-purpose schedule is only visible after sign-in. NWR Schedule (OGL3) is the licence-safe choice.

## Recommendations
- **Overall architecture for travel times** [high]: Offline batch precompute of full cell-to-cell matrices with R5 via r5py; serve by memory-mapped array lookup. No routing engine in the production request path.
  - why: Deterministic, explainable, sub-millisecond, zero marginal cost, and fits a Python monorepo. A London-wide matrix is small enough (225 MB per matrix) that precomputing everything is simpler than running a routing service. R5 is designed for exactly this workload and returns percentiles over a departure window. Published benchmark: 1,227 x 1,227 with a 120-minute window in under a minute on a laptop (smaller city), so London at 15k origins is hours on one VM, not days.
  - rejected: On-demand one-to-many at query time (needs an always-on routing service, adds ops burden and latency, single departure time unless run repeatedly). Station-to-station matrix plus walking (misses bus-only trips and gives poor first/last mile). Commercial matrix APIs (cost and caching terms).
- **Routing engine for the batch job** [high]: R5 v7.x through r5py, pinned in a Docker image with JDK 21.
  - why: MIT licensed engine; r5py is dual GPL-3.0-or-later/MIT and gives a pandas/GeoPandas interface. Supports transit, walk and cycle in one tool, departure_time_window, percentiles, max_public_transport_rides and max_bicycle_traffic_stress. OTP2 documentation explicitly points analytics users to R5.
  - rejected: OpenTripPlanner 2 (LGPL, passenger-information focus, no matrix API). GraphHopper (Apache 2.0 but Matrix API is commercial only). OSRM (BSD-2, no transit). Valhalla (MIT, excellent walk/cycle but transit support less proven; keep for later cycling quality). Conveyal note: R5 has no stable public API and no third-party support, which is acceptable for a pinned batch job but not for a live service.
- **Spatial unit for origins and destinations** [high]: H3 resolution 9 for both (about 15,000 cells covering Greater London). Roll up to named neighbourhoods using a population-weighted median and show the within-neighbourhood range.
  - why: Uniform 200 m precision everywhere, trivial snapping of any address, and storage stays tiny. Snapping error is at most about 2-3 minutes of walking, acceptable for ranking areas.
  - rejected: LSOA centroids (about 5,000 in London; uneven size, coarse in outer London and in low-population employment areas such as the City). H3 res 10 (about 105,000 cells, about 11 billion pairs per matrix, not lean). H3 res 8 (about 2,100 cells, 530 m edge, too coarse for walk-to-station effects). Stations as destinations (cannot represent arbitrary workplaces).
- **Timetable inputs** [medium]: Bus, Tube, DLR, tram: BODS GTFS London region (OGL). National Rail including London Overground and Elizabeth line: Rail Data Marketplace timetable (NWR Schedule under OGL3, or RDG Timetable once terms confirmed) converted with the gb-transit cif2gtfs CLI; bootstrap with the gb-transit nightly gtfs-national-rail-only.zip. Snapshot every input into Burro's own storage.
  - why: Official sources, open licences, minimal conversion work. R5 accepts multiple GTFS feeds and links them through the street network, so stop IDs do not need reconciling.
  - rejected: Depending solely on a third-party merged feed (TravelWhiz GB feed, first commit March 2026; Aubin feed used by Transitous): useful for bootstrapping and cross-checking but too young to be the sole source. ATOCCIF2GTFS prebuilt files (last updated April 2024, author recommends commercial alternatives). TNDS (FTP with manual registration, weekly).
- **Fallback if BODS London GTFS lacks Tube/DLR/tram or is poor quality** [medium]: Convert TfL Journey Planner timetables (TransXChange, daily 24 MB zip) to GTFS with transxchange2gtfs (gb-transit) or UK2GTFS.
  - why: It is the authoritative TfL source for Underground, bus, DLR, tram, cable car and river, under the TfL open data licence which permits commercial use.
  - rejected: CommuteStream/tflgtfs converter (old, community reports errors with rail lines).
- **Time windows and statistic** [medium]: Weekday AM peak departures 07:00-09:00 (headline), weekday evening 19:00-21:00, Saturday 11:00-13:00, optional Friday/Saturday night 00:30-02:30. Store p50 as the headline and p85 as the 'just missed it' figure. Trip cutoff 90 minutes. Pick a Tuesday-Thursday in a normal school-term week.
  - why: R5 samples every minute in the window, so percentiles capture waiting-time and frequency effects without pretending to model delays. Median is the standard in accessibility analysis; p85 penalises infrequent services, which matters to commuters.
  - rejected: Single departure time (arbitrary, unstable). Mean travel time (distorted by unreachable minutes). Arrive-by search (not supported by R5; a departure window is the accepted proxy).
- **Number of interchanges and walking legs** [medium]: Compute two extra AM-peak matrices with max_public_transport_rides set to 1 and 2. Derive 'direct', 'one change' or 'two or more' by comparing against the unrestricted time. Compute walk time from every cell to the nearest Tube/rail station and nearest frequent bus stop as separate features.
  - why: Keeps everything deterministic and matrix-based with no itinerary engine. Walk-to-station is more interpretable to users than an access-leg breakdown.
  - rejected: r5py detailed itineraries for all pairs (far too slow for 225 million pairs). Calling a journey planner for every neighbourhood at query time (hundreds of calls per search).
- **Answering an arbitrary destination address at query time** [high]: Geocode, snap to H3 res-9 cell, read that destination's column from each stored matrix (store destination-major for AM peak, origin-major for the evening return). Combine multiple destinations by per-destination caps and a weighted sum.
  - why: One 15 KB contiguous read per destination per matrix. Supports multiple destinations for free and is fully reproducible for shareable links.
  - rejected: On-demand one-to-many run per query (kept only as fallback). Storing matrices in Postgres rows (225 million rows per matrix is wasteful; use memory-mapped arrays or Zarr in object storage).
- **Itinerary detail for explanations** [medium]: For the top 10-20 results only, call TfL Unified API Journey Planner and cache the response; always offer a deep link to a journey planner. Treat it as optional enrichment, never as an input to ranking.
  - why: Free, commercially usable with attribution, 500 requests per minute, zero infrastructure. Ranking stays on the precomputed matrix so results are deterministic.
  - rejected: Self-hosting OTP2 or MOTIS from day one just for itineraries (unnecessary ops for v1).
- **Cycling and walking** [medium]: Same R5 batch run on the OSM network. Walking at 4.8 km/h with a 60-minute cutoff; cycling at about 15 km/h with a traffic-stress limit and a 60-minute cutoff. No time-of-day variants.
  - why: One engine, one pipeline. Walk and cycle matrices are sparse and cheap.
  - rejected: Mapbox Matrix (paid beyond 100k elements, 25 coordinates per request, no transit). OSRM or Valhalla as a second engine in v1 (revisit Valhalla later for elevation-aware cycling).
- **Refresh cadence** [high]: Automated rebuild quarterly, plus after the May and December National Rail timetable changes and after any major TfL network change. Each run produces a diff report flagging cells whose time moved by more than 5 minutes.
  - why: Typical commute times change slowly. Versioned matrices keep shared links reproducible.
  - rejected: Nightly rebuilds (no user benefit, more failure surface). Annual (misses timetable changes).
- **Compute and hardware** [medium]: One on-demand cloud VM with 16-32 vCPU and 64 GB RAM for the batch run, torn down afterwards. Artefacts (about 2 GB raw) in object storage, memory-mapped by the API.
  - why: Estimated 1-4 hours and under GBP 20 per refresh. Serving cost is negligible. Benchmark on day one with 200 origins before committing.
  - rejected: Permanent routing server. Serverless per-origin fan-out (unnecessary complexity at this size).
- **Fallback plan** [medium]: Technical fallback: self-hosted MOTIS (MIT, single binary) using its one-to-all endpoint with arriveBy=true plus a precomputed cell-to-stop walking table, run for several departure times and take the median. Commercial fallback: TravelTime production plan.
  - why: MOTIS gives exact-destination, any-time queries and scales to more cities without N-squared growth. TravelTime removes the data pipeline entirely if budget allows.
  - rejected: Google Routes, Mapbox, HERE as fallbacks (cost, no transit, or unconfirmed terms).
- **Extra transport features for ranking** [medium]: Derive from GTFS: peak and off-peak service frequency per cell, night service availability, number of distinct lines within a 10-minute walk, walk time to nearest station. Add TfL step-free access data and fare zones. Build Burro's own PTAL-style index from current GTFS rather than relying on published PTAL.
  - why: The downloadable PTAL on London Datastore is 2015 data and predates the Elizabeth line. A self-computed index is current, reproducible and extends to other cities.
  - rejected: Using 2015 PTAL as a live ranking input.

## Risks
- [high] BODS London GTFS may not contain Tube, DLR and tram, or may contain them with quality problems (duplicates, wrong route types). -> Inspect the file in week one: count routes by mode against known totals. If inadequate, convert TfL Journey Planner TransXChange instead. Build a validation harness comparing about 1,000 sampled origin-destination pairs against TfL Journey Planner.
- [medium] Rail timetable licence ambiguity: the RDG Timetable product is 'Open (restrictions may apply)' and its permitted purposes are not publicly visible. -> Use NWR Schedule (explicitly OGL3) or register on Rail Data Marketplace and read Schedule 1 before launch. Keep a record of accepted terms.
- [medium] Compute time and memory for London are estimates, not measurements. -> Benchmark 200 origins on day one. If too slow, shorten the window to 60 minutes, drop unpopulated origin cells, or use a larger VM; cost remains small.
- [medium] Timetabled times are optimistic versus real journeys (delays, crowding, engineering works). -> Label as 'typical timetabled time', show p85 alongside p50, round to the nearest few minutes, and validate against TfL Journey Planner.
- [low] R5 has no stable public API and no third-party support; r5py upgrades could break the pipeline. -> Pin R5, r5py and JDK in a Docker image; batch-only use means a failure delays a refresh, not the product.
- [medium] Dependence on small third-party feeds or tools (gb-transit, TravelWhiz) that may disappear. -> Snapshot all inputs in Burro storage, vendor the converter version, and keep UK2GTFS as a second converter.
- [low] ODbL share-alike could apply if the travel-time matrix is treated as a derivative database and distributed publicly. -> Keep matrices server-side, attribute OpenStreetMap, and take legal advice before publishing any bulk download.
- [low] Destination snapping to a 200 m cell adds up to about 2-3 minutes of error. -> Present times as approximate; optionally refine central London destinations to res 10 later.
- [low] TfL API throttling or outage affects itinerary detail. -> Cache responses, treat detail as optional, degrade to a deep link.
- [medium] Commercial fallback (TravelTime) requires deleting cached data on termination and refreshing every 60 days. -> Only adopt with caching rights written into the order; keep the open-data pipeline as the primary path.


## Open questions
- Does the BODS London-region GTFS include Underground, DLR and tram at usable quality? This must be checked by downloading the file, which has not been done.
- What are the Schedule 1 permitted purposes, attribution and retention terms for the RDG 'Timetable - Full Refresh' products on Rail Data Marketplace?
- Which time windows matter most to the founder: is a night-time matrix needed for v1, and should the evening return leg be modelled separately?
- Should destinations outside Greater London be supported in v1 (for example Gatwick, Reading, Watford, Cambridge)? If so, add a short list of extra destination points rather than extending the grid.
- Should unpopulated cells (parks, water, industrial land) be dropped as origins to cut compute, while staying valid as destinations?
- What cycling assumptions should be the default (speed and tolerance for busy roads), and should there be a 'cautious cyclist' variant?
- Is itinerary detail (lines and changes) required in v1, or is a travel time plus 'direct / one change' label and a deep link enough?
- Is there a current, downloadable, openly licensed PTAL from TfL WebCAT, or should Burro rely solely on its own computed index?

## Unverified
- That BODS London GTFS contains Tube, DLR and tram services (indirect evidence only; file not inspected).
- Exact wording of Google Maps Platform caching restrictions: the official terms page was not read in full.
- HERE pricing, London coverage and caching terms.
- Mapbox Product Terms on caching results.
- All compute-time, VM size and cost estimates for the London batch run (extrapolated from a published small-city benchmark).
- Cell counts: about 15,000 H3 res-9 cells is derived from Greater London area of about 1,572 km2 divided by the H3 average cell area; LSOA count of about 5,000 is from memory.
- Release years for MOTIS v2.11.3 and OpenTripPlanner 2.10.0 (dates were shown without an unambiguous year or came from a summarised changelog).
- Maturity of Valhalla's public transport support.
- Commercial-use status of the gb-transit prebuilt feeds and the Aubin feed.
- Whether the National Rail Data Portal has been retired: not read.
- Availability of fare zone data and night-service flags through the TfL Unified API, and any open source for planned new lines.
- Whether newer PTAL values in TfL WebCAT can be downloaded and under what licence.
- That cif2gtfs works directly on the Network Rail (NWR) CIF as well as the RDG CIF without extra station reference data.
## Findings (compact)
- TfL Transport Data Service licence | use_v1 | commercial=yes_with_conditions | verified=True | lic=Based on Open Government Licence v2.0 with TfL amendments. Grants a worldwide, royalty-free, perpetual, non-exclusive licence. | cost=Free
- TfL Journey Planner timetables | use_later | commercial=yes_with_conditions | verified=True | lic=TfL Transport Data Service terms | cost=Free, registration required
- TfL Unified API (Journey Planner, StopPoint, Line) | use_v1 | commercial=yes_with_conditions | verified=True | lic=TfL Transport Data Service terms | cost=Free
- TfL official GTFS | reference_only | commercial=not_applicable | verified=True | lic= | cost=
- Bus Open Data Service (BODS) timetables GTFS | use_v1 | commercial=yes | verified=True | lic=Open Government Licence (per DfT Find Transport Data catalogue and Transitland feed record) | cost=Free
- Rail Data Marketplace: NWR Schedule | use_v1 | commercial=yes_with_conditions | verified=True | lic=Open (OGL3): RDM licence based on Open Government Licence 3.0 | cost=Free, RDM account required
- Rail Data Marketplace: RDG Timetable (Full Refresh Daily/Weekly/Monthly) | use_later | commercial=unknown | verified=True | lic=Labelled 'Open (restrictions may apply)' under the RDM data sharing agreement; permitted purposes are set per product in Schedule 1, visible | cost=Free
- Rail Data Marketplace: Darwin Timetable Files | reference_only | commercial=yes_with_conditions | verified=True | lic=Open (OGL3) | cost=Free
- gb-transit (planarnetwork) nightly GB rail GTFS and converters | use_v1 | commercial=unknown | verified=True | lic=Tools: GNU GPLv3. Data stated as 'Rail Settlement Plan Data Licence and Open Government Licence v3.0'. | cost=Free
- TravelWhiz GB Bus, Train and Metro GTFS | reference_only | commercial=yes_with_conditions | verified=True | lic=Curated content CC BY 4.0; upstream sources (TNDS, BODS, TfL, National Rail Darwin, NaPTAN, OSM) keep their own terms. | cost=Free
- Aubin Great Britain GTFS (used by Transitous) | reference_only | commercial=unknown | verified=False | lic=Points to National Rail Data Portal terms and BODS requirements; no standalone licence found. | cost=
- Traveline National Dataset (TNDS) | reference_only | commercial=yes | verified=True | lic=Open Government Licence | cost=Free; FTP credentials issued after manual registration
- NaPTAN | use_v1 | commercial=yes | verified=True | lic=Open Government Licence | cost=Free
- OpenStreetMap via Geofabrik Greater London extract | use_v1 | commercial=yes_with_conditions | verified=True | lic=ODbL 1.0 | cost=Free
- R5 (Conveyal) | use_v1 | commercial=yes | verified=True | lic=MIT | cost=Free
- r5py | use_v1 | commercial=yes | verified=True | lic=Dual GPL-3.0-or-later or MIT | cost=Free
- OpenTripPlanner 2 | reject | commercial=yes | verified=True | lic=LGPL 3.0 | cost=Free
- MOTIS | use_later | commercial=yes | verified=True | lic=MIT | cost=Free
- Valhalla | use_later | commercial=yes | verified=True | lic=MIT | cost=Free
- OSRM | reject | commercial=yes | verified=True | lic=BSD-2-Clause | cost=Free
- GraphHopper (open source) | reject | commercial=yes | verified=True | lic=Apache 2.0 | cost=Free
- UK2GTFS | use_later | commercial=yes | verified=True | lic=GPL-3.0 | cost=Free
- TravelTime API | use_later | commercial=yes_with_conditions | verified=True | lic=Free Basic plan: 'Development and testing only - not for commercial use'. Production: custom fixed annual subscription, minimum 12 months. T | cost=Not published; quote required. Likely above the stated budget.
- Google Maps Platform Routes API | reject | commercial=yes_with_conditions | verified=True | lic=Google Maps Platform terms; caching of content restricted except place IDs. | cost=Compute Route Matrix: Essentials USD 5 per 1,000 elements (10,000 free per month
- Mapbox Matrix and Isochrone APIs | reject | commercial=yes_with_conditions | verified=True | lic=Mapbox Terms of Service and Product Terms | cost=100,000 free elements per month, then USD 2.00 per 1,000 (falling to USD 1.20).
- HERE Public Transit and Matrix Routing | reject | commercial=unknown | verified=False | lic= | cost=
- PTAL (Public Transport Accessibility Levels) on London Datastore | reference_only | commercial=yes | verified=True | lic=Open Government Licence v2 | cost=Free
- TfL step-free access and station topology data | use_v1 | commercial=yes_with_conditions | verified=True | lic=TfL Transport Data Service terms | cost=Free
- TfL NUMBAT and station entry/exit counts | use_later | commercial=yes_with_conditions | verified=True | lic=TfL Transport Data Service terms | cost=Free
- Fare zones, Night Tube and planned changes | use_v1 | commercial=yes_with_conditions | verified=False | lic=TfL Transport Data Service terms | cost=