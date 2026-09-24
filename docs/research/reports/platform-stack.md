# platform-stack: Platform stack and repository design

## Headline
FastAPI on Fly.io (London) + Supabase Pro in London for Postgres (PostGIS, pgvector) and Auth + Next.js 16 on Vercel Pro (lhr1) + MapLibre on web and iOS over a self-hosted Protomaps basemap on Cloudflare R2 behind a Worker. Pipeline is plain Python + DuckDB writing Parquet, run by `just`, no orchestrator. One committed OpenAPI 3.1 file generates the TypeScript and Swift clients. Destination search is an in-house Postgres gazetteer built from OS open data. Estimated fixed run cost about USD 65-100 per month before LLM usage.

## Summary
Everything below was checked against primary sources on 2026-09-23 unless listed in unverified_claims. Later checks used pages opened at known addresses and package registries only.

Key facts that shaped the choices:
- H3 in Postgres is only offered by Neon, Crunchy Bridge and AWS RDS. Supabase, Fly Managed Postgres, Render and Cloud SQL do not list it. This does not matter: compute H3 in the pipeline (DuckDB h3 community extension or h3-py 4.5.0) and store cell ids as BIGINT. That frees the database choice.
- London regions exist on Fly.io (lhr), Supabase (eu-west-2), Neon (aws-eu-west-2), Crunchy Bridge (eu-west-2), Cloud Run (europe-west2, Tier 2 pricing), Vercel (lhr1). Render is Frankfurt only. Railway is Amsterdam only.
- AWS App Runner closed to new customers on 2026-04-30, so the simple AWS path is gone.
- MapLibre Native iOS supports PMTiles since 6.10.0, but PMTiles sources get no offline packs or caching. Feature-state on iOS only landed in 6.30.0 (2026-09-10). MapLibre GL JS 6 is ESM-only and needs WebGL2.
- Nominatim's public API forbids autocomplete; OS Places carries Royal Mail PAF charges. Whether Mapbox or Google geocoding results may be shown on a MapLibre map was not read on their own pages.
- swift-openapi-generator 1.13.1 supports OpenAPI 3.0/3.1 but ignores security schemes and validation keywords. openapi-typescript 7.13.0 declares a peer dependency on TypeScript ^5 while TypeScript latest is 7.0.2.
- Anthropic first-party API offers inference geo 'global' or 'us' and workspace geo 'us' only, so prompts cannot be kept in the UK or EU on that route.

Monthly cost estimate at launch (USD): Fly 2 x shared-cpu-1x 1GB about 13; Supabase Pro 25; Vercel Pro 20; Cloudflare Workers paid 5 plus R2 near 0; Sentry 0-26; PostHog 0; Apple Developer Program 99 per year. Total about 65-100.

Runtime shape: parse (LLM, natural language to structured preferences) and rank (deterministic, no LLM) are separate endpoints, so slider changes never call the model. Map geometry is static tiles; scores are a small id-to-score JSON joined on the client.

## Recommendations
- **Python API framework** [high]: FastAPI 0.141.1 + Pydantic 2.13 + Uvicorn 0.53, Python 3.13 or 3.14
  - why: Emits OpenAPI 3.1 from typed models, which is the contract both clients are generated from. Largest ecosystem and the most familiar to coding agents. MIT. Split POST /v1/search/parse (LLM) from POST /v1/search/rank (pure function) so ranking stays deterministic and cacheable.
  - rejected: Litestar 2.24 (good, MIT, but smaller community and fewer agent priors). Django 6.1 (ORM, admin and templating are dead weight for a JSON API; OpenAPI is an add-on).
- **Python tooling** [high]: uv 0.12 workspace with one lockfile; ruff 0.16 for lint and format; pyright 1.1.414 as the CI type gate; pytest 9.1 with pytest-socket to block network
  - why: One tool each for env, lint, types, tests. ty is still beta (0.0.83, README says no stable API), so it is not a CI gate yet.
  - rejected: ty (revisit at 1.0). mypy 2.3 (slower, needs Pydantic plugin). Poetry or pip-tools (uv replaces both).
- **Database access layer** [medium]: SQLAlchemy 2.0.54 + Alembic 1.20 + psycopg 3.3.6. No GeoAlchemy2.
  - why: Standard, well known to agents. Spatial work happens in the pipeline; the API mostly reads precomputed tables, so a few raw SQL spatial queries are enough. psycopg gives COPY for bulk loads.
  - rejected: asyncpg (Apache-2.0, no COPY convenience through SQLAlchemy sync path). Raw SQL only (loses migrations tooling). Note psycopg is LGPL-3.0-only; fine for server use, flagging for awareness.
- **Database and auth host** [medium]: Supabase Pro, region eu-west-2 London, used as plain Postgres plus Auth. Disable the Data API. API verifies JWTs via the JWKS endpoint.
  - why: USD 25 per month covers Postgres with PostGIS and pgvector, 8 GB disk, and Auth for 100k MAU with native Sign in with Apple through the Swift SDK. User PII stays in London. One vendor instead of two. Dataset is under 2 GB.
  - rejected: Neon (best pure Postgres: has h3, branching, scale to zero, about USD 19 per month at 0.25 CU always on; but Neon Auth has no Swift SDK and no Apple sign-in, so a second auth vendor is needed). Fly Managed Postgres (USD 38 Basic, no h3). Crunchy Bridge (Hobby tier documented as not for production). Cloud SQL and RDS (more ops). Render (no UK region). Clerk and WorkOS (extra vendor, data residency not confirmed).
- **H3 strategy** [high]: Compute H3 in the pipeline and in the API with h3-py; store as BIGINT. Do not depend on the h3-pg extension.
  - why: Only Neon, Crunchy Bridge and RDS ship h3-pg. Avoiding it keeps the database portable.
  - rejected: Choosing the database for h3-pg support.
- **Data pipeline** [high]: Plain Python steps using DuckDB 1.5.5 (spatial + h3 community extension), writing Parquet to versioned release folders with a manifest.json. A small in-repo runner orders steps and skips unchanged ones. Triggered by `just`.
  - why: Batch jobs that run monthly or quarterly do not need a scheduler, daemon or UI. Releases are immutable, so rollback is a config change. The slow routing step is stubbed in fixture mode by a committed sample matrix.
  - rejected: Dagster 1.13 and Prefect 3.8 (extra service, UI and concepts for a handful of steps). dbt-core 1.12 (SQL-only model does not fit routing and tile steps). DVC (adds concepts; revisit if caching becomes painful).
- **Object storage and tile serving** [high]: Cloudflare R2 for PMTiles and pipeline releases; the Protomaps Cloudflare Worker on a custom domain serving z/x/y with edge caching
  - why: R2 egress is free; storage USD 0.015 per GB-month with 10 GB free. Worker z/x/y gives normal HTTP caching for both web and iOS, which matters because iOS PMTiles sources are not cached. Workers paid is USD 5 per month for 10M requests.
  - rejected: S3 and GCS (egress fees). Tigris (zero egress, USD 0.02 per GB, fine but no edge worker). Direct PMTiles range requests from clients (no caching on iOS, R2 latency 500 ms or more on misses).
- **API hosting** [medium]: Fly.io in lhr, two shared-cpu-1x 1 GB machines, Docker image, deployed from GitHub Actions
  - why: Cheapest always-on London compute (USD 6.46 per machine per month), no cold starts, simple CLI. Container stays portable.
  - rejected: Cloud Run europe-west2 (solid, scale to zero, but Tier 2 pricing, cold starts for Python, more IAM setup; keep as fallback). Render (no UK region). Railway (no UK region, egress USD 0.05 per GB). AWS (App Runner closed to new customers; ECS plus RDS is too much ops for v1).
- **Web hosting and rendering** [high]: Next.js 16.3 App Router on Vercel Pro, functions pinned to lhr1. Area pages at /london/[area] are statically generated with generateStaticParams and revalidated on demand when a data release is published. Search and map are client rendered. Share links are server rendered with Open Graph metadata.
  - why: A few hundred area pages prerender trivially and are fully indexable with JSON-LD, canonical URLs and a generated sitemap. City is in the URL from day one. Use classic ISR rather than Cache Components to keep one caching model. Hobby plan is non-commercial, so Pro (USD 20 per seat) is required at launch.
  - rejected: Self-hosting Next.js on Fly (saves USD 20 but ISR cache is per instance and previews are lost). Static export (no ISR). Pre-rendering every comparison pair (quadratic; render on demand instead).
- **Web map stack** [high]: MapLibre GL JS 6.11 with a Protomaps basemap extract for London, plus an areas overlay built with tippecanoe. Scores applied client side by area id. No React wrapper.
  - why: BSD-3 code, ODbL data, near-zero cost at any traffic, same style JSON reused on iOS. Geometry is cached static tiles; only a small score map changes per query.
  - rejected: Mapbox (USD 5 per 1,000 loads after 50k, proprietary SDK). MapTiler (free tier non-commercial; Flex USD 30 per month for 25k sessions; keep as fallback). Stadia (USD 20 per month; fallback). OS Open Zoomstack (OGL, GB only, six-monthly, no path to other cities).
- **iOS map SDK** [medium]: MapLibre Native iOS 6.31 via Swift Package Manager, wrapped in a small UIViewRepresentable. Use a match expression for choropleth colour; adopt feature-state after it has matured.
  - why: Same style and tiles as web, BSD-2, Metal renderer, no per-user fees. MapKit cannot consume the shared style or vector tiles, so web and iOS would diverge.
  - rejected: MapKit (free and native, but no styling parity and polygons are per-overlay views). MapLibre SwiftUI DSL (pre-1.0, API not stable). Mapbox Mobile SDK (USD 4 per 1,000 MAU after 25k).
- **Destination entry** [medium]: In-house gazetteer table in Postgres with pg_trgm: OS Open Names, Code-Point Open postcodes, station names, and named OSM places kept in a separate table. Served by GET /v1/places/autocomplete.
  - why: Zero marginal cost, no third-party display restrictions, deterministic and testable offline. Postcode, station and place-name precision is enough for commute destinations.
  - rejected: OS Places API (PAF royalties, per-transaction cost). Google Places (banned in the registry). Mapbox (temporary results cannot be stored). Nominatim public API (autocomplete forbidden, 1 request per second). Pelias (six services, 8 GB RAM minimum). Photon self-hosted (good; add later if business-name search is needed). Stadia or MapTiler hosted geocoding (paid fallback).
- **Client generation** [medium]: Commit contracts/openapi.json exported from FastAPI. Generate TypeScript types with openapi-typescript 7.13 plus openapi-fetch 0.17, and Swift with swift-openapi-generator 1.13.1 CLI. Commit generated code. CI regenerates and fails on any diff.
  - why: Committed output is greppable by agents and makes contract changes visible in review. Set generate_unique_id_function in FastAPI for clean method names. Run the TypeScript generator from its own package pinned to TypeScript 5.x.
  - rejected: Hey API openapi-ts 0.99 (pre-1.0). Swift build plugin (plugin trust friction in Xcode Cloud, output invisible to agents). Hand-written clients.
- **Observability and analytics** [high]: Sentry (EU region, chosen at org creation) for errors and traces on API, web and iOS. PostHog Cloud EU for product analytics and feature flags. structlog JSON logs to stdout. An llm_calls table for prompt version, tokens, latency and validation result.
  - why: Two vendors cover errors, tracing, funnels and flags, both with EU hosting and free tiers that fit launch volume.
  - rejected: Full OpenTelemetry collector stack (too much for v1). Datadog (cost). Self-hosted PostHog (ops).
- **Entitlements** [high]: Server-side entitlements table keyed by user id, one has_entitlement function, returned in GET /v1/me. Everyone is 'free' in v1. Add Stripe on web and RevenueCat on iOS later as writers to that table.
  - why: App Store guideline 3.1.1 requires in-app purchase for unlocking features in the app; 3.1.3(b) allows web-bought subscriptions if also offered as IAP. Keeping the decision server side means adding payments is additive.
  - rejected: Entitlements in JWT claims (stale until refresh). Client-side gating.
- **CI** [high]: GitHub Actions with path-filtered jobs that each call `just ci-<part>`: python, pipeline-fixture, web, contracts drift. iOS builds and TestFlight on Xcode Cloud (25 free hours per month).
  - why: Linux runners cost USD 0.006 per minute; macOS costs USD 0.062 per minute, so keep iOS off GitHub runners. CI runs exactly what developers and agents run locally.
  - rejected: macOS GitHub runners for every PR. Separate CI scripts that differ from local commands.
- **Secrets** [high]: .env locally (gitignored) with a committed .env.example; fly secrets, Vercel env vars and GitHub environment secrets in production; gitleaks plus GitHub push protection; agent settings deny reading .env files; separate Anthropic keys per environment with spend limits
  - why: No extra vendor. LLM key exists only on the API server. iOS and web ship public keys only.
  - rejected: Doppler, Infisical or Vault in v1 (add when there is a team). Secrets in the repo, even encrypted.
- **Agent instructions** [high]: AGENTS.md at the root as the single source, under 150 lines, plus a one-line CLAUDE.md containing @AGENTS.md. Short nested AGENTS.md per package.
  - why: One file serves every coding tool that reads AGENTS.md, and the import line serves a tool that reads CLAUDE.md. Which tool reads which file was not read on the tools' own pages.
  - rejected: Duplicated CLAUDE.md and AGENTS.md content. One large root file.
- **Repository layout** [high]: burro/
  AGENTS.md            canonical instructions, commands, invariants
  CLAUDE.md            one line: @AGENTS.md
  README.md
  justfile             setup, dev, test, lint, typecheck, contracts, pipeline-fixture, ci
  pyproject.toml       uv workspace root, ruff and pyright config
  uv.lock
  compose.yaml         local Postgres with PostGIS and pgvector
  .env.example
  .github/workflows/   ci.yml, deploy-api.yml, publish-data.yml
  .claude/             settings.json (permissions, deny .env), skills/
  docs/
    architecture.md
    adr/               0001-... short decision records
    data-sources.md    source, licence, attribution, cadence
    playbooks/         add-a-data-source.md, release-data.md
  contracts/
    openapi.json       exported from the API, committed
    preferences.schema.json
    package.json       pins the TypeScript generator
  services/api/        FastAPI app
    src/burro_api/     routers/ domain/ llm/ db/ auth/ entitlements/
    migrations/  tests/  Dockerfile  fly.toml  AGENTS.md
  packages/core/       pure Python: preference model, scoring, explanation facts; no IO
  packages/pipeline/   steps/ sources/ runner.py cli.py tests/
  apps/web/            Next.js; src/lib/api/schema.d.ts is generated
  apps/ios/            SwiftUI app; Packages/BurroAPI is generated
  map/style/           shared MapLibre style JSON
  map/tiles/           scripts to build basemap extract and overlays
  map/worker/          Cloudflare tile worker
  data/fixtures/camden/  tiny clipped inputs plus LICENCES.md
  evals/               LLM evals, run nightly, not a merge gate
  - why: Top-level folders map to deployables. packages/core holds the deterministic ranking so both API and pipeline import it and it can be tested without a database. Conventions: every package exposes the same just verbs; `just test` under 30 seconds; `just pipeline-fixture` under 60 seconds on one borough with network blocked; LLM calls go through an interface with a fake in tests; generated code is committed and never edited by hand.
  - rejected: Separate repos per client (contract drift). Nx or Turborepo (not needed for one web app). Git LFS for fixtures (keep fixtures under 10 MB instead).

## Risks
- [medium] User prompts sent to the Anthropic API are processed outside the UK and EU; they may contain workplace locations -> Send no account identifiers or email to the model. Disclose in the privacy policy and sign the DPA. If strict residency is required, evaluate Claude through a cloud provider's European region before launch.
- [medium] MapLibre iOS feature-state is two weeks old and iOS PMTiles sources are not cached -> Use a match expression keyed by area id for colours. Serve z/x/y from the Worker. Bundle the small areas overlay in the app. Run a one-day spike on a mid-range iPhone with 600 polygons.
- [medium] Generated clients break on schema shapes: Optional fields become anyOf with null, producing awkward Swift types; openapi-typescript needs TypeScript 5 -> Keep response models flat with explicit required fields. CI compiles both generated clients. Pin the generator's TypeScript in contracts/package.json. Add oasdiff for breaking-change detection.
- [high] LLM cost abuse through anonymous search -> Per-IP and per-user rate limits, Cloudflare Turnstile on anonymous parse calls, cache parse results by normalised prompt hash, hard monthly spend limit on the API key, quotas tied to entitlements.
- [low] Coupling to Supabase Auth -> API only trusts a JWT verified through JWKS and maps subject to its own users table. Data API disabled. Swapping provider touches one module.
- [medium] Fly.io outage or pricing change -> Plain Dockerfile, no Fly-specific code. Cloud Run in europe-west2 documented as the fallback in an ADR.
- [medium] ODbL share-alike if OSM data is merged into the gazetteer -> Keep OSM-derived rows in a separate table. OSMF guideline says individual geocoding results are not share-alike, but aggregated city-scale extracts can be. Get a short legal review before launch.
- [medium] Attribution drift across many open data sources -> docs/data-sources.md is the single register. Pipeline manifest carries licence and attribution per source. The /attribution page and map control are generated from it. CI fails if a source lacks licence metadata.
- [low] Vercel bill spikes from crawlers hitting on-demand pages -> Set spend management limit. Restrict on-demand comparison pages with canonical ordering and robots rules.
- [medium] Secrets exposed by coding agents -> Agent settings deny reading .env files. Fixture data and fake keys for local work. gitleaks in CI and GitHub push protection.
- [low] Heavy routing step does not fit CI runners -> Run on demand on a larger machine. Outputs are versioned releases. Fixture mode uses a committed sample matrix.
- [low] Self-hosted basemap needs upkeep (style, fonts, rebuilds) -> Rebuild extract on each data release. MapTiler Flex at USD 30 per month is a drop-in fallback since the style spec is shared.


## Open questions
- Is UK-only data residency a hard requirement, or is EU and US processing with safeguards acceptable? This decides the LLM route and analytics vendors.
- Will the repository be public or private? It affects free CI minutes and whether fixture data licences must be published.
- Can people search without an account at launch? Apple's guideline 5.1.1(v) favours it, but it raises LLM abuse exposure.
- Must destination search find company names and street addresses, or are postcode, station and place name enough for v1?
- Minimum iOS version: 17 or 18?
- Are offline maps needed on iOS?
- Which email provider will send auth emails? Supabase's built-in sender is not usable in production.
- Which sign-in methods at launch: Apple, Google, email code?
- Is the Apple Developer Program enrolment individual or organisation? Organisation needs a D-U-N-S number.
- Expected launch traffic, to size machines and set LLM spend limits.
- Who is the second person with production access, if any? Sentry's free plan allows one user.

## Unverified
- Render's prices: not read.
- The prices of Cloud SQL and RDS: not read.
- Cloud Run per-second rates and free tier figures: not read. Only the Tier 2 status of London was confirmed on Google's docs.
- GitHub Actions included minutes and the macOS multiplier: not read. Per-minute prices were confirmed on GitHub docs.
- The price of the OS Places API: not read.
- Whether Mapbox requires geocoding results to be shown only on a Mapbox map: not read. Mapbox's own help page confirms only the no-storage rule.
- DuckDB spatial reading and writing GeoParquet was not confirmed on the docs pages read today.
- Licence of the DuckDB h3 community extension was not stated on its page.
- Size of a Greater London Protomaps extract is not known; only the 120 GB planet figure is confirmed.
- MapKit polygon rendering performance at choropleth scale is not benchmarked.
- Photon Great Britain extract size and memory needs were not confirmed.
- Network latency between Fly lhr and AWS eu-west-2 is assumed low, not measured.
- Clerk and WorkOS data storage locations were not confirmed.
- Neon cold-start latency after scale to zero was not confirmed.
- Whether @vis.gl/react-maplibre works with MapLibre GL JS 6 was not checked; the recommendation avoids the wrapper.
- Monthly cost total of USD 65-100 is my own sum of listed prices.
## Findings (compact)
- FastAPI 0.141.1 | use_v1 | commercial=yes | verified=True | lic=MIT | cost=Free
- Litestar 2.24.0 | reject | commercial=yes | verified=True | lic=MIT | cost=Free
- Django 6.1.1 | reject | commercial=yes | verified=True | lic=BSD-3-Clause | cost=Free
- uv 0.12.18 | use_v1 | commercial=yes | verified=True | lic=MIT OR Apache-2.0 | cost=Free
- ruff 0.16.8 | use_v1 | commercial=yes | verified=True | lic=MIT | cost=Free
- pyright 1.1.414 | use_v1 | commercial=yes | verified=True | lic=MIT | cost=Free
- ty 0.0.83 | use_later | commercial=yes | verified=True | lic=MIT | cost=Free
- just 1.58 | use_v1 | commercial=yes | verified=True | lic=CC0-1.0 | cost=Free
- SQLAlchemy 2.0.54, Alembic 1.20.0, psycopg 3.3.6 | use_v1 | commercial=yes_with_conditions | verified=True | lic=MIT, MIT, LGPL-3.0-only | cost=Free
- Supabase (Postgres + Auth) | use_v1 | commercial=yes | verified=True | lic=Commercial SaaS terms | cost=Pro USD 25 per month: 8 GB database, 100k MAU, 250 GB egress. Free tier pauses a
- Neon | use_later | commercial=yes | verified=True | lic=Commercial SaaS terms | cost=Launch USD 0.106 per CU-hour, storage USD 0.35 per GB-month, no minimum. Free: 0
- Crunchy Bridge | reject | commercial=yes | verified=True | lic=Commercial SaaS terms | cost=Hobby-0 USD 9, Hobby-1 USD 18; storage USD 0.10 per GB
- Fly Managed Postgres | reject | commercial=yes | verified=True | lic=Commercial SaaS terms | cost=Basic USD 38, Starter USD 72 per month; storage USD 0.28 per GB
- Google Cloud SQL for PostgreSQL | reject | commercial=yes | verified=False | lic=Google Cloud terms | cost=Not read
- AWS (RDS, ECS, App Runner) | reject | commercial=yes | verified=False | lic=AWS terms | cost=Not read
- Fly.io Machines | use_v1 | commercial=yes | verified=True | lic=Commercial SaaS terms | cost=shared-cpu-1x: 512 MB USD 3.62, 1 GB USD 6.46, 2 GB USD 12.14 per month; egress 
- Google Cloud Run | use_later | commercial=yes | verified=True | lic=Google Cloud terms | cost=Not read; London is Tier 2
- Render | reject | commercial=yes | verified=False | lic=Commercial SaaS terms | cost=Not read
- Railway | reject | commercial=yes | verified=True | lic=Commercial SaaS terms | cost=Hobby USD 5, Pro USD 20 per month; about USD 10 per GB RAM and USD 20 per vCPU; 
- Vercel | use_v1 | commercial=yes_with_conditions | verified=True | lic=Commercial SaaS terms; Hobby is non-commercial | cost=Pro USD 20 per seat per month, 1 TB transfer and 10M edge requests included
- Cloudflare R2 and Workers | use_v1 | commercial=yes | verified=True | lic=Cloudflare terms | cost=R2 USD 0.015 per GB-month, 10 GB free, Class B USD 0.36 per million. Workers pai
- DuckDB 1.5.5 with spatial and h3 extensions | use_v1 | commercial=yes | verified=True | lic=MIT (DuckDB). h3 community extension licence not stated on its page. | cost=Free
- Dagster 1.13, Prefect 3.8, dbt-core 1.12 | reject | commercial=yes | verified=True | lic=Apache-2.0 | cost=Free self-hosted
- tippecanoe (felt fork) | use_v1 | commercial=yes | verified=True | lic=BSD-2-Clause | cost=Free
- MapLibre GL JS 6.11.0 | use_v1 | commercial=yes | verified=True | lic=BSD-3-Clause | cost=Free
- Protomaps basemap and PMTiles | use_v1 | commercial=yes_with_conditions | verified=True | lic=Code BSD-3-Clause, styles CC0, data ODbL as a Produced Work | cost=Free; planet file about 120 GB, extract London with pmtiles extract
- MapTiler Cloud | use_later | commercial=yes_with_conditions | verified=True | lic=Commercial; Free plan is non-commercial | cost=Flex USD 30 per month: 25k sessions, 500k requests; then USD 2.50 per 1k session
- Mapbox | reject | commercial=yes_with_conditions | verified=True | lic=Proprietary terms | cost=Web 50k loads free then USD 5 per 1k; mobile 25k MAU free then USD 4 per 1k; tem
- Stadia Maps | use_later | commercial=yes_with_conditions | verified=True | lic=Commercial; Free plan is non-commercial | cost=Starter USD 20 per month for 1M credits; autocomplete v2 is 1 credit
- OS Open Zoomstack | reference_only | commercial=yes | verified=True | lic=OS OpenData under Open Government Licence | cost=Free
- MapLibre Native iOS 6.31.0 | use_v1 | commercial=yes | verified=True | lic=BSD-2-Clause | cost=Free
- Apple MapKit | reject | commercial=yes | verified=False | lic=Apple Developer Program terms | cost=Included with USD 99 per year membership
- OS Open Names | use_v1 | commercial=yes | verified=True | lic=OS OpenData under Open Government Licence | cost=Free
- Code-Point Open and ONS Postcode Directory | use_v1 | commercial=yes_with_conditions | verified=True | lic=Open Government Licence v3.0 | cost=Free
- OS Names API | reference_only | commercial=yes | verified=True | lic=OS OpenData plan | cost=Free; 600 transactions per minute per live project
- OS Places API | reject | commercial=yes_with_conditions | verified=False | lic=Premium or Public Sector plan; includes Royal Mail IP | cost=Not read
- postcodes.io | reference_only | commercial=unknown | verified=True | lic=Code MIT; data from OS and ONS | cost=Free public API; rate limit not stated
- Photon 1.3.0 | use_later | commercial=yes_with_conditions | verified=True | lic=Apache-2.0 code; OSM data under ODbL | cost=Free plus hosting; planet index about 95 GB, country extracts published weekly
- Nominatim public API | reject | commercial=yes_with_conditions | verified=True | lic=OSMF usage policy | cost=Free, max 1 request per second
- Pelias | reject | commercial=yes | verified=True | lic=MIT | cost=Free plus hosting; 6 services, 8 GB RAM minimum
- Google Places API | reject | commercial=yes_with_conditions | verified=True | lic=Google Maps Platform terms | cost=Autocomplete 10k free per month then USD 2.83 per 1k
- openapi-typescript 7.13.0 and openapi-fetch 0.17.0 | use_v1 | commercial=yes | verified=True | lic=MIT | cost=Free
- swift-openapi-generator 1.13.1 | use_v1 | commercial=yes | verified=True | lic=Apache-2.0 | cost=Free
- Next.js 16.3.6 | use_v1 | commercial=yes | verified=True | lic=MIT | cost=Free
- Sentry | use_v1 | commercial=yes | verified=True | lic=Commercial SaaS terms | cost=Developer free (1 user, 5k errors); Team USD 26 per month
- PostHog Cloud EU | use_v1 | commercial=yes | verified=True | lic=Commercial SaaS terms | cost=Free monthly: 1M events, 5k recordings, 1M flag requests, 100k exceptions
- Clerk | reject | commercial=yes | verified=True | lic=Commercial SaaS terms | cost=Free to 50k monthly retained users; Pro USD 25 per month
- WorkOS AuthKit | reject | commercial=yes | verified=True | lic=Commercial SaaS terms | cost=Free to 1M MAU; custom domain USD 99 per month
- RevenueCat | use_later | commercial=yes | verified=True | lic=Commercial SaaS terms | cost=Free to USD 2,500 monthly tracked revenue, then 1%
- GitHub Actions and Xcode Cloud | use_v1 | commercial=yes | verified=True | lic=GitHub and Apple terms | cost=Linux USD 0.006 per minute, macOS USD 0.062 per minute. Xcode Cloud 25 hours per
- AGENTS.md and CLAUDE.md | use_v1 | commercial=not_applicable | verified=True | lic=Open format stewarded by the Agentic AI Foundation under the Linux Foundation | cost=Free
- Anthropic API data residency | reference_only | commercial=yes | verified=True | lic=Anthropic commercial terms | cost=US-only inference is 1.1x standard price
- App Store Review Guidelines 4.8, 5.1.1(v), 3.1.1, 3.1.3(b) | reference_only | commercial=not_applicable | verified=True | lic=Apple guidelines | cost=
- EU adequacy decision for the UK | reference_only | commercial=not_applicable | verified=True | lic=Renewed 2025-12-19, expires 2031-12-27 | cost=