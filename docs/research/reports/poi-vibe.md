# poi-vibe: Points of interest and "vibe": datasets, licences and methods for a defensible, licence-clean neighbourhood vibe representation (London v1)

## Headline
Launch with a scoring database that contains no share-alike data at all. Build vibe as a transparent, deterministic tag taxonomy over percentile-ranked features computed from Overture Places (CDLA-Permissive-2.0) cross-checked against FSA food hygiene data (OGL), plus OS OpenData, Historic England, GLA high street / town centre / cultural infrastructure data, Census 2021 and VOA council tax stock tables (all OGL v3). Keep OpenStreetMap to the basemap and internal benchmarking, keep Wikipedia to attributed excerpts and internal retrieval, and ban Google Places and Street View outright.

## Summary
WHAT I FOUND

1. There is enough permissively licensed data to build vibe for London without any share-alike source. OGL v3 covers FSA food hygiene ratings, all 18 OS OpenData products, ONS Census 2021, Historic England listings, GLA high street and town centre boundaries, VOA council tax stock tables and the non-address fields of EPC data. Overture Places is CDLA-Permissive-2.0, which explicitly imposes no obligations on "Results" of computational analysis. That is the cleanest possible footing for a product whose core asset is derived scores.

2. OpenStreetMap is usable commercially but is the one source that can force Burro to publish its own derived tables. Under ODbL 1.0, a rendered map is a Produced Work (attribution only). Loading and filtering OSM is a trivial transformation. But counts and densities computed from OSM using external inputs (Burro's neighbourhood polygons, census denominators) are most safely treated as a Derivative Database: if publicly used, that table must be offered under ODbL (sections 4.4 and 4.6). OSMF has no guideline on statistical aggregates; its own FAQ is silent, so this is a genuine grey area. Storing OSM-derived columns next to Census or FSA columns is fine (Collective Database) provided each property is all-OSM or all-non-OSM and datasets are only linked by key. What triggers share-alike on other data is mixing within a feature type, for example de-duplicating OSM cafes against another cafe list.

3. Google is unusable for this purpose. The Google Maps Platform Terms (last modified 26 August 2026) prohibit storing business names and addresses, prohibit creating content from Google Maps Content, and give as explicit examples using Places lat/lng for point-in-polygon analysis and building an index of tree locations from Street View. Places content may not be shown on a non-Google map. Only place_id may be cached indefinitely; Places lat/lng for 30 days.

4. Two datasets in the brief are traps. VOA rating list downloads state "An open government licence does not apply" and are under a restricted licence. Council conservation area appraisals are council copyright with restricted OS mapping inside, and the UK text and data mining exception remains non-commercial only after the government dropped its proposed commercial exception in March 2026.

5. Wikipedia and Wikivoyage are CC BY-SA 4.0. Facts are free to reuse; Wikimedia's terms say contributors waive database rights so facts may be reused without attribution. An LLM summary that tracks the prose is plausibly Adapted Material and would have to be shared under CC BY-SA 4.0 with attribution. Only that text block is affected, not the page or app around it.

WHAT I RECOMMEND FOR V1

- POI spine: Overture Places monthly release, filtered on confidence and operating_status, with FSA FHRS as the authoritative cross-check for food and drink.
- Built form and character: VOA CTSOP4.1 (build period by LSOA) and CTSOP3.1 (property type), Census 2021 accommodation type, Historic England listed building density, conservation area coverage, OS Open Greenspace and OS Open Rivers.
- High street and culture: GLA High Street Boundaries (600+ high streets), Town Centre Boundaries, GLA Cultural Infrastructure Map (pubs, music venues, studios, galleries, LGBTQ+ venues and more).
- Vibe model: about 16 named tags, each a published formula over percentile-ranked features. Claude maps language to tag weights and filters; ranking is pure arithmetic. Embeddings (voyage-4) are a recall aid and a visible secondary signal, never the ranker.
- Text: Wikidata for facts; Wikipedia as an attributed excerpt box and an internal retrieval corpus; Burro's own summaries generated only from the structured fact table.
- Governance: a source registry in the repo with licence, attribution string, share-alike flag and date verified; column-level lineage; an auto-generated attribution page; a CI check that blocks any unregistered source.

WHAT WAS NOT CONFIRMED

I did not measure Overture Places quality in London. That is the largest unknown in this recommendation and should be the first engineering spike, benchmarked internally against OSM and FHRS.

## Recommendations
- **Primary points-of-interest source for vibe features** [medium]: Overture Maps Places (monthly GeoParquet from public S3/Azure, no account) as the single POI spine, filtered to operating_status = open and a confidence threshold (start at 0.7, tune in the spike). Use FSA FHRS as the authoritative cross-check and primary count for food and drink.
  - why: CDLA-Permissive-2.0 section 3.1 imposes no restriction or obligation on Results of computational analysis, so Burro's aggregates and scores stay proprietary. Overture already conflates Meta, Microsoft, Foursquare and AllThePlaces, has a brand field for chain detection and stable GERS IDs. FHRS is a statutory register updated daily, so it corrects the staleness that social-media-derived POIs suffer from. Both sources are national or global, which makes later cities and 'like X' comparisons cheap.
  - rejected: OSM as spine: best London coverage but ODbL share-alike risk on derived tables. Foursquare OS Places direct: same Apache 2.0 data is already inside Overture, and since October 2025 new releases require a portal account and token. Google Places: terms prohibit storing and deriving. OS Points of Interest (PointX): premium, priced per record, out of budget. Confidence is medium only because London quality of Overture was not measured.
- **How to use OpenStreetMap** [high]: V1: basemap tiles only (Produced Work, attribution) and internal benchmarking (no public use, so no obligations). Do not put OSM-derived features in the scoring database at launch. If the spike shows gaps only OSM fills, add them in a quarantined osm_features table that Burro publishes under ODbL, and never blend OSM with other sources inside one feature type.
  - why: ODbL 4.4 and 4.6 require a publicly used Derivative Database to be offered under ODbL. OSMF guidance covers maps, geocoding, layers and trivial transformations but says nothing on statistical aggregates, so a conservative reading treats per-area counts as derivative. The Collective Database guideline protects other columns only when each property is all-OSM or all-non-OSM. Avoiding OSM in scores removes the question entirely; publishing a quarantined table later turns the obligation into goodwill.
  - rejected: Blending OSM and Overture into one 'best POI' layer: the Horizontal Layers and Collective Database guidelines say this triggers share-alike on the merged layer. Relying on 'scores are a Produced Work': arguable for an on-screen number, weak for an API returning a table.
- **Representation of vibe** [high]: A fixed taxonomy of about 16 tags, each defined as a documented weighted formula over percentile-ranked features computed on a fine grid and rolled up. Proposed tags: village feel, buzzy, leafy, creative, family-oriented, student-heavy, riverside or waterside, strong high street, evening and nightlife, quiet residential, foodie, cafe culture, historic character, modern or new-build, sporty and outdoorsy, young professional. Claude outputs tag weights and hard filters as structured data; ranking is deterministic arithmetic.
  - why: Meets the founder's requirement for deterministic, explainable ranking. Percentile ranks give honest explanations such as 'top 8 percent in London for cafes per resident'. Every tag traces to named open datasets, so each claim is defensible. Example inputs: village feel = independent share + pre-1919 dwelling share + conservation area coverage + greenspace within 400 m + compact high street; creative = GLA studios, workspaces, galleries and music venues per km2; family-oriented = households with dependent children + play space access + low evening venue density; riverside = share of area within 300 m of Thames or canal.
  - rejected: Pure embedding similarity as the ranker: not explainable and not stable. Unsupervised clusters as the user-facing vocabulary: hard to name and defend. LLM-assigned vibe labels from its own knowledge: violates 'must not invent facts'.
- **Feature engineering from the mix of places** [medium]: Compute per grid cell with a walkable kernel, then roll up: densities per km2 and per 1,000 residents by category; Shannon diversity over Overture basic_category; cuisine diversity over restaurant taxonomy; independent share; evening venue density; listed buildings per km2; greenspace and water proximity. Chain detection = Overture brand field, plus national name-frequency over FHRS (a normalised name appearing in many local authorities is a chain), plus Geolytix for grocery.
  - why: All inputs are permissive and national. FHRS name frequency gives a chain detector that needs no paid data. Kernel smoothing on a grid avoids boundary artefacts from fuzzy neighbourhood edges.
  - rejected: Opening-hours-based 'late night' metric: no open source has reliable hours (Overture has none, OSM is sparse, Google is prohibited). Use evening venue counts and label the feature honestly as 'evening venues', not 'open late'. CDRC chain and vacancy indicators: safeguarded, not open.
- **Building age and housing typology** [high]: VOA Council Tax stock of properties tables CTSOP4.1 (build period) and CTSOP3.1 (property type) at LSOA, plus Census 2021 accommodation type at output area, plus Historic England listed building points and conservation area polygons.
  - why: CTSOP covers every dwelling on the council tax list, is OGL v3 and is published annually (2025 tables published 22 May 2026). That gives 'Victorian terraces' versus 'post-2000 flats' without any address-level licensing issue.
  - rejected: EPC: useful later for finer grain but only covers homes sold or let, and address fields are Royal Mail and OS copyright. Colouring London: ODbL and crowdsourced with patchy coverage; footprints are excluded from downloads. OS NGD Buildings: has age attributes but is premium.
- **Open text and LLM-written area descriptions** [medium]: Wikidata (CC0) for facts. Wikipedia as (a) an internal retrieval corpus and (b) a clearly attributed, linked excerpt box marked CC BY-SA 4.0. Burro's own summaries are generated by Claude from the structured fact table only, with Wikipedia prose excluded from the generation prompt, and each sentence stored with the fact IDs it relies on.
  - why: Keeps Burro's copy proprietary and verifiable. CC BY-SA conditions attach on sharing adapted material, so internal embedding triggers nothing, and an attributed excerpt is simple compliance. If Wikipedia prose is ever used as generation input, tag that output CC BY-SA 4.0 and attribute it.
  - rejected: Summarising Wikipedia into unattributed house copy: likely Adapted Material, share-alike applies. Council conservation area appraisals: council copyright, restricted OS maps inside, and no commercial text-mining exception in UK law. Review sites: excluded by the brief and by their terms.
- **Embeddings for semantic retrieval** [medium]: voyage-4 (1024 dimensions, 32k context) over one 'area card' per neighbourhood built from structured facts plus the Wikipedia extract. Store in Postgres with pgvector or brute-force cosine, since there are only a few hundred areas. Use as a recall aid for long-tail queries and as one visible, user-adjustable 'text match' weight.
  - why: Anthropic has no embedding model and its docs point to Voyage. Cost is negligible: first 200M tokens free, then 0.06 USD per million. voyage-4-nano is open-weight under Apache 2.0 if Burro wants to self-host and remove the vendor dependency.
  - rejected: Dedicated vector database: unnecessary at this scale. Embeddings as the primary ranker: breaks explainability.
- **'This is like X' comparisons for people relocating** [medium]: Phase 1 (launch): Claude translates the reference place into visible, editable tag weights, labelled as an interpretation rather than a fact. Phase 2: data-driven analogues across England and Wales using the same national features (Census 2021, FHRS, Overture, OS OpenData, CTSOP). Phase 3: international reference neighbourhoods using Overture global data plus Wikipedia and Wikivoyage text embeddings.
  - why: Phase 1 costs nothing extra and stays honest because the user sees and can edit the translation. Phases 2 and 3 reuse the v1 pipeline because the chosen sources are national or global.
  - rejected: Shipping international data-driven analogues in v1: no comparable census or built-form data across countries, so features would be POI-only and weak.
- **Imagery and street character** [high]: No imagery-derived features in v1. Street character comes from built-form and network data. If profile pages need photos, use Geograph (CC BY-SA 2.0) or Wikimedia Commons with automated per-image attribution.
  - why: Google Street View terms prohibit deriving data and showing Street View beside a non-Google map. Mapillary images are CC BY-SA 4.0 but its terms limit commercial use to listed purposes and require logo attribution for derived data. Neither is worth the complexity at launch.
  - rejected: Street View greenery or frontage scoring: prohibited. Mapillary-based scoring: revisit after launch.
- **Demographic inputs to vibe** [high]: Use age bands, household composition, student share, tenure and dwelling size only. Exclude ethnicity, religion, country of birth and similar protected characteristics from ranking, filters and generated text.
  - why: A recommender that steers people toward or away from areas by protected characteristics is a legal and reputational risk for a housing-adjacent product. The remaining variables are sufficient for family-oriented, student-heavy and young professional tags.
  - rejected: Using ready-made geodemographic cluster names (OAC or LOAC) in the UI: several cluster labels encode ethnicity or class and would surface in explanations.
- **Licence governance in the repository** [high]: A machine-readable source registry (one entry per dataset: licence, URL, attribution string, share-alike flag, commercial-use flag, date verified, release pinned), column-level lineage from feature to source, an attribution page generated from the registry, and a CI check that fails on any unregistered source or any table mixing share-alike and non-share-alike columns.
  - why: Licences drift: Foursquare changed access in October 2025, Overture removes the categories column in September 2026, the old EPC site closed on 30 May 2026. A registry makes the clean position provable to investors and keeps coding agents from quietly adding a prohibited source.
  - rejected: A prose LICENCES.md maintained by hand: goes stale and cannot be enforced.

## Risks
- [high] Overture Places quality in London is unmeasured. Records derived from social media pages can be stale, duplicated or miscategorised, which would make vibe tags wrong in ways locals notice immediately. -> First engineering spike: load one Overture release for Greater London, compare counts by category against FHRS and an internal OSM benchmark for 20 well-known neighbourhoods, and set the confidence threshold from that. Use FHRS as the primary count for food and drink.
- [high] Vibe tags fail a local sanity test (for example Crouch End not scoring as village feel), undermining trust in a product whose whole promise is judgement. -> Build a golden set of 40 to 60 neighbourhoods with expected tags agreed by people who know London. Run it as a regression test on every data refresh and formula change.
- [high] Discriminatory steering: demographic features or generated text lead users toward or away from areas by ethnicity, religion or similar characteristics. -> Exclude protected-characteristic variables from features, filters and prompts. Add a prompt rule and an output check so Claude declines such requests and explains why. Get a short legal view before launch.
- [high] ODbL share-alike reaches Burro's proprietary tables because OSM-derived values were blended with other sources or used to correct them. -> No OSM in the scoring database at launch. If added, one quarantined table, published under ODbL, enforced by the CI lineage check.
- [medium] A developer or coding agent uses Google Places or Street View to 'verify' or enrich data, breaching Google's terms. -> State the ban in the repo conventions file and enforce via the source registry check. Do not hold a Google Maps Platform key in the project.
- [medium] CC BY-SA text leaks into Burro's proprietary descriptions because Wikipedia prose was included in a generation prompt. -> Keep Wikipedia text in a separate store with licence metadata. The summary-writing prompt receives fact rows only. Log prompt inputs for audit.
- [medium] Claude states an ungrounded 'fact' about an area in an explanation. -> Generate from a fact table with IDs, require each sentence to cite fact IDs, validate numerically before display, and pre-generate and cache summaries so they can be reviewed.
- [medium] Licence or access drift: Foursquare moved to gated access in October 2025, Overture removes the categories column in September 2026, the old EPC service closed in May 2026. -> Pin dataset releases, record date verified in the registry, add schema tests on ingest, and re-verify licences quarterly.
- [medium] GLA Cultural Infrastructure Map 2025 edition has no stated licence, and some layers originate from third parties whose rights OGL cannot grant. -> Email the GLA for written confirmation. Until then use the earlier OGL-licensed edition and show aggregates only, not venue lists.
- [medium] No open source gives reliable opening hours, so a 'late-night' tag would overclaim. -> Name the feature 'evening venues' and define it as pubs, bars, clubs and music venues per km2. Do not claim opening times.
- [low] Conservation area data is incomplete, so some genuinely historic areas score low on historic character. -> Combine with listed building density and pre-1919 dwelling share so no single source decides the tag. Treat absent coverage as unknown.
- [low] FHRS terms warn that showing an invalid rating can be an offence. -> Use FHRS for counts only. Do not show individual ratings or rating imagery in v1.
- [low] Census 2021 is five years old at launch and fast-changing areas will be misdescribed. -> Show data dates in explanations. Weight fresher sources (Overture, FHRS, CTSOP) more heavily for fast-moving tags.


## Open questions
- Will Burro show individual places by name on profile pages, or only aggregates? Names raise the quality bar and add attribution duties for Overture and Foursquare records.
- If OSM-derived features are added later, is the founder comfortable publishing that derived table openly under ODbL?
- Which census variables is the founder comfortable using for vibe? I recommend age, household type, students, tenure and dwelling size only.
- Is there budget for a one-off legal opinion covering two grey areas: ODbL and statistical aggregates, and CC BY-SA and LLM summaries?
- Are photos wanted on area profile pages in v1? If so, Geograph or Wikimedia Commons with automated attribution is the clean route.
- Who validates the vibe golden set? It needs people with real local knowledge across north, south, east and west London.
- Which origin cities matter most for relocators? This sets the priority for data-driven 'like X' comparisons.
- What is the source of the neighbourhood polygons? If they are derived from OSM place boundaries, the ODbL analysis applies to them too.

## Unverified
- Overture Places coverage and accuracy in London. Not measured. A local DuckDB check was not run.
- Whether per-area counts computed from OSM are legally a Derivative Database or a Produced Work. OSMF publishes no guideline on aggregates; my position is a conservative reading, not settled law.
- Whether an LLM summary of a Wikipedia article is 'Adapted Material' under CC BY-SA 4.0. This is a legal judgement; I recommend treating it as adapted.
- GLA Cultural Infrastructure Map 2025 edition licence. The page shows none and data.gov.uk says 'not set'. Earlier editions are confirmed OGL v3.
- Which third parties supplied layers in the GLA Cultural Infrastructure Map and whether their rights are cleared.
- Full terms of the VOA rating list restricted licence. I confirmed only that OGL does not apply.
- Companies House licence: the download page states none. The data.gov.uk listing was not read.
- Historic England's own Open Data Hub terms page was not read; OGL v3 was confirmed from data.gov.uk instead.
- OS premium pricing and licence terms for a public consumer app: not read.
- OS Open Greenspace function types and its update cycle: the specification was not read.
- FHRS business type list and the number of London establishments. The API was not queried.
- Copyright position of conservation area appraisals across all 33 London authorities. Not audited; some councils may publish under OGL.
- The March 2026 UK government report on copyright and AI: not read.
- Geolytix Retail Points has no formal licence document; reliance is on the publisher's public statement.
- Legal robustness of the AllThePlaces CC0 waiver over data scraped from retailer store locators.
- Specific Census 2021 table identifiers and output-area availability for each variable.
- Open datasets for London tree canopy and street trees were not checked.
- That a national name-frequency method over FHRS reliably separates chains from independents. Plausible but untested.
## Findings (compact)
- OpenStreetMap (via Geofabrik Greater London extract) | use_later | commercial=yes_with_conditions | verified=True | lic=ODbL 1.0 (database), attribution plus share-alike on derivative databases | cost=Free
- Overture Maps Places | use_v1 | commercial=yes_with_conditions | verified=True | lic=CDLA-Permissive-2.0 for most sources; Apache 2.0 with NOTICE for Foursquare-sourced records; CC0 for AllThePlaces | cost=Free
- Overture Maps buildings, transportation, base and divisions themes | use_later | commercial=yes_with_conditions | verified=True | lic=ODbL (these themes contain OpenStreetMap data) | cost=Free
- Foursquare Open Source Places | use_later | commercial=yes_with_conditions | verified=True | lic=Apache License 2.0 with NOTICE.txt | cost=Free
- Food Standards Agency Food Hygiene Rating Scheme (FHRS) | use_v1 | commercial=yes_with_conditions | verified=True | lic=Open Government Licence; site terms and conditions apply to ratings imagery | cost=Free, no registration or API key
- Ordnance Survey OpenData (Open Greenspace, OpenMap Local, Open Roads, Open Rivers, Open Names, Open UPRN, Open Zoomstack, Boundary-Line, Code-Point Open and others) | use_v1 | commercial=yes_with_conditions | verified=True | lic=Open Government Licence v3 | cost=Free
- Ordnance Survey premium: Points of Interest (PointX) and OS NGD Buildings | reject | commercial=yes_with_conditions | verified=True | lic=Proprietary premium licence; Points of Interest is owned by PointX (Landmark) and distributed by OS | cost=Not confirmed. OS Data Hub premium plan includes up to 1,000 GBP per month of fr
- Google Places API | reject | commercial=no | verified=True | lic=Google Maps Platform Terms of Service (last modified 26 August 2026) and Service Specific Terms (last modified 10 June 2026) | cost=Pay per request
- Google Street View | reject | commercial=no | verified=True | lic=Google Maps Platform Terms of Service | cost=Pay per request
- Google Places Insights (BigQuery) | reject | commercial=unknown | verified=True | lic=Google Maps Platform terms; product-specific storage terms not found on the overview page | cost=Not published on the overview page
- Geolytix Retail Points | use_v1 | commercial=yes | verified=True | lic=No formal licence text. Publisher states it is 'fully open data which you can do with it as you please' and 'unrestricted use, no licensing  | cost=Free
- VOA non-domestic rating list downloads (business rates) | reject | commercial=unknown | verified=True | lic=Restricted licence with terms and conditions. The page states 'An open government licence does not apply.' | cost=Free
- VOA Council Tax: stock of properties (CTSOP3.1 and CTSOP4.1) | use_v1 | commercial=yes_with_conditions | verified=True | lic=Open Government Licence v3.0 | cost=Free
- Companies House Free Company Data Product | reject | commercial=yes_with_conditions | verified=True | lic=Download page states no licence; the data.gov.uk listing describes it as Open Government Licence v3.0 | cost=Free
- Historic England National Heritage List (listed building points) | use_v1 | commercial=yes_with_conditions | verified=True | lic=Open Government Licence v3.0 | cost=Free
- Conservation areas (planning.data.gov.uk and Historic England) | use_v1 | commercial=yes_with_conditions | verified=True | lic=Open Government Licence v3.0 | cost=Free
- GLA High Street Boundaries and Town Centre Boundaries | use_v1 | commercial=yes_with_conditions | verified=True | lic=Open Government Licence v3 | cost=Free
- GLA High Streets Data Service partnership data (spend, footfall, vacancy) | reject | commercial=no | verified=True | lic=Restricted to partnership members (GLA, boroughs, BIDs) | cost=
- GLA Cultural Infrastructure Map | use_v1 | commercial=yes_with_conditions | verified=True | lic=Earlier editions are Open Government Licence v3. The 2025 edition page shows no licence field and data.gov.uk lists its licence as 'not set' | cost=Free
- ONS Census 2021 | use_v1 | commercial=yes_with_conditions | verified=True | lic=Open Government Licence v3.0 | cost=Free
- Output Area Classification 2021 and London Output Area Classification 2021 | use_later | commercial=yes_with_conditions | verified=True | lic=Open Government Licence v3 | cost=Free
- Geographic Data Service Retail Centre Boundaries and Open Indicators (2022) | use_later | commercial=yes_with_conditions | verified=True | lic=Open Government Licence v3.0 for the open files; vacancy and chain versus independent composition are safeguarded (restricted) | cost=Free
- Energy Performance of Buildings data (Get energy performance of buildings data service) | use_later | commercial=yes_with_conditions | verified=True | lic=Open Government Licence v3.0 for all fields except address and postcode, which are Royal Mail and Ordnance Survey copyright with a closed li | cost=Free
- Colouring London / Colouring Britain | reject | commercial=yes_with_conditions | verified=True | lic=ODbL | cost=Free
- Wikipedia (English) | use_v1 | commercial=yes_with_conditions | verified=True | lic=CC BY-SA 4.0 and GFDL (terms last updated 7 June 2023) | cost=Free
- Wikivoyage | use_later | commercial=yes_with_conditions | verified=True | lic=CC BY-SA 4.0 | cost=Free
- Wikidata | use_v1 | commercial=yes | verified=True | lic=CC0 | cost=Free
- Geograph Britain and Ireland | use_later | commercial=yes_with_conditions | verified=True | lic=CC BY-SA 2.0 for images and descriptions | cost=Free
- Mapillary | reject | commercial=yes_with_conditions | verified=True | lic=Images CC BY-SA 4.0; service use under Mapillary Terms of Use (last updated 15 February 2024) | cost=Free
- London borough conservation area appraisals | reference_only | commercial=unknown | verified=False | lic=Copyright of each council; no default open licence. Embedded maps carry restrictive Ordnance Survey notices. | cost=
- AllThePlaces | reference_only | commercial=yes | verified=True | lic=CC0 waiver on the output data; MIT for the scraper code | cost=Free
- OSM name-suggestion-index | use_later | commercial=yes_with_conditions | verified=True | lic=BSD 3-Clause | cost=Free
- Voyage AI embeddings (voyage-4 family) | use_v1 | commercial=yes | verified=True | lic=Commercial API terms | cost=voyage-4-large 0.12 USD, voyage-4 0.06 USD, voyage-4-lite 0.02 USD per million t