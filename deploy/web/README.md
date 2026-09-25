# The website on Vercel

First deployed on 25 September 2026, on Vercel's free plan, with the made-up city. Written from Vercel's own pages as they read on 2026-09-23, and brought to what was done. The order of steps, the costs and the rollback are in [../README.md](../README.md).

**The free plan is for now.** Vercel's terms keep it to work that is not commercial, so a launch needs the paid plan. Read the terms on Vercel's own page before you rely on this.

## Project settings

Import the repository in Vercel, then set these under Settings, Build and Deployment.

| Setting | Value | Why |
|---|---|---|
| Root Directory | `apps/web` | The app sits two folders down. A build can read nothing above this folder, and `npm run build` needs nothing above it |
| Framework Preset | Next.js | |
| Install Command | `npm install --no-audit --no-fund` | No lockfile is committed yet, and `npm ci` needs one. See ADR 0008 |
| Build Command | `npm run build` | The script switches Next's telemetry off. Not `npm run check`: that reads `contracts/openapi.json`, which is above the root directory, and it is CI's job |
| Output Directory | Leave as it is | |
| Function Region | `lhr1`, London | A page is rebuilt, hourly at most, by a function that calls the API. It should run beside the API. The default is in the United States |
| Node.js Version | See "Node" below | |

[vercel.json](vercel.json) holds the same install command, build command, framework and region. **Vercel does not read it where it is.** It reads `vercel.json` only from the root directory, `apps/web`. Moved to `apps/web/vercel.json`, the four settings would be reviewed like any other change. It has not been moved, so set them in the dashboard: on the first deployment the root directory, the install command and the build command were set there by hand.

## The two environment variables

Neither is a secret. Set both for Production only.

| Name | Value | Read by |
|---|---|---|
| `NEXT_PUBLIC_BURRO_API_URL` | `https://APP.fly.dev`, the address Fly.io gives the app | The browser's client, a build, and the content security policy |
| `BURRO_SITE_URL` | `https://PROJECT.vercel.app`, the address Vercel gives the project | `src/lib/indexing.ts`, for what a search engine is told, and nothing else |

```
vercel link
vercel env add NEXT_PUBLIC_BURRO_API_URL production
vercel env add BURRO_SITE_URL production
vercel env ls
```

- **Set neither for the first deployment.** The website is then built from the recorded answers, and Vercel gives the project its address. Set both once the API is deployed, and deploy again: [../README.md](../README.md) gives the order.
- Once there is a domain, the first is `https://api.DOMAIN` and the second `https://DOMAIN`.
- Both are read when the website is built. The API's address is written into the pages and into the policy. A change does nothing until the next deployment.
- `BURRO_SITE_URL` must be the same origin as `BURRO_ALLOWED_ORIGINS` in [../api/fly.toml](../api/fly.toml). If the website is later served from `www.DOMAIN`, both say `https://www.DOMAIN`.
- Each is an address with no name and password, no query and no fragment. `BURRO_SITE_URL` has no path either. One that is not in that form is treated as not set, and nothing says so.
- Leave both unset for Preview. A preview is then built from the recorded answers in `test/recorded/`, and its search answers `not_configured`. A preview's address is not on the API's list of origins, and the list takes no pattern, so a preview could not read the API's answers in any case.
- While the release is synthetic no page may be indexed, whatever `BURRO_SITE_URL` says. Every page says so in its markup and in the header `X-Robots-Tag`, and the robots file lets a crawler in to read it: [../README.md](../README.md), step 4, says why.

## The API must be up before a build that names it

With no address of the API set, a build reads the recorded answers and calls nothing: the first deployment was built so. With `NEXT_PUBLIC_BURRO_API_URL` set, a build calls routes 4, 5, 6 and 11 of the API. A read that timed out, or met a service too busy to answer, is asked for four times at most, each waited for longer than the last. A failure then stops the build, and the deployment before it stays live. Deploy the API before you set its address. After a new release reaches the API, the pages catch up within the hour, or at once with a new deployment.

## The headers the website already sets

`next.config.ts` sets them on every path, from `src/lib/headers.ts`. They are not repeated in `vercel.json`: two sources would come to disagree, and the policy depends on the API's address.

| Header | Value |
|---|---|
| `Content-Security-Policy` | `default-src 'self'`; `script-src 'self' 'unsafe-inline'`; `style-src 'self' 'unsafe-inline'`; `img-src 'self' data: blob:`; `font-src 'self'`; `connect-src 'self'` and the API's origin; `worker-src 'self' blob:`; `object-src 'none'`; `base-uri 'self'`; `form-action 'self'`; `frame-ancestors 'none'` |
| `Referrer-Policy` | `no-referrer` |
| `X-Content-Type-Options` | `nosniff` |
| `Permissions-Policy` | `camera=(), geolocation=(), microphone=()` |

`X-Powered-By` is switched off. The website does not set `Strict-Transport-Security`. Vercel is expected to add it; the check in [../README.md](../README.md) shows whether it does.

## Privacy settings

The website has no route handler, no server action and no middleware, so nothing a person types passes through Vercel. These settings keep it that way.

| Setting | Set to | Why |
|---|---|---|
| Web Analytics | Off | The website has no analytics. Vercel serves its script from the website's own origin, so the content security policy would not stop it |
| Speed Insights | Off | The same |
| Log drains | None | A drain sends every request's path to a third party |
| Observability Plus | Not bought | It keeps runtime logs for 30 days in place of 1 |
| Vercel Toolbar | Off for production | It adds a script to the page |
| Build Logs and Source Protection | On, as it comes | |
| Git Fork Protection | On, as it comes | A pull request from a fork is not built until you allow it |
| Deployment Protection | On for previews, as it comes | A preview is not for the public |

What Vercel's own log holds for a request: the path, the query string, the status and the browser's name. For this website that is an area's slug, or the slugs of a comparison. It is kept for 1 hour on Hobby, which is the free plan and the one in use, and 1 day on Pro.

`vercel link` writes a `.vercel` folder that names the account and the project. It is not in `.gitignore` yet. Do not commit it.

## Node

Three versions of Node are in play, and nothing holds them to one.

| Where | Version on 2026-09-23 | Set by |
|---|---|---|
| Vercel | The newest 24 | `engines.node` in `package.json` is `>=20.9`. Vercel reads `engines` over the project's own setting, and gives a range like this the newest major it has |
| Hosted CI | 22 | The runner's image |

To hold Vercel to one major, `engines.node` must name it, as `22.x`. That is a change to `apps/web/package.json`.

## No lockfile

`package-lock.json` is not committed (ADR 0008). On Vercel and in CI that means:

- Every build resolves the packages again. `package.json` holds each direct dependency to its minor version, and what those depend on is held to nothing.
- Two builds of one commit can differ, and a build can fail on a day nothing was committed.
- No package is checked against a recorded hash.
- A rollback on Vercel is safe all the same: it serves the old build and installs nothing.

When the lockfile is committed, the install command becomes `npm ci`, here and in the `web` job of `.github/workflows/ci.yml`.
