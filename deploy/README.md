# Putting Burro on the internet

Nothing is deployed. Nothing in this folder has ever been run against a host. It was written so that, on the day the accounts exist, deployment is an hour of following steps.

Every figure about a host below was read from that host's own pages on 2026-09-23. Check each one against the page before you rely on it.

## What runs where

| Part | Host | Region | Files |
|---|---|---|---|
| API, `services/api` | Fly.io, one machine | `lhr`, London | [api/Dockerfile](api/Dockerfile), [api/fly.toml](api/fly.toml) |
| Website, `apps/web` | Vercel | Functions in `lhr1`, London. Static files on every region | [web/README.md](web/README.md), [web/vercel.json](web/vercel.json) |
| Names | Your DNS host | | Two records, below |
| Tiles and releases | Cloudflare R2 | Later | Not needed yet: the release is inside the image |
| Accounts | Supabase | Later, London | Not needed yet: there is no sign-in |
| Error reports | Sentry, EU | Later | Not wired in. See ADR 0005 before it is |

## Before you start

Three things the plan and the code already say, and a deployment must not undo.

1. **Do not set the model key yet.** The API works without one: the rules read the prompt. The plan says no outside person reaches the model until the privacy notice, the ICO registration and the provider's data processing agreement are in place. The service also has no quota and no rate limit yet (`admit` in `services/api/src/burro_api/app.py` is empty), so a key on the open internet is an open bill. And the model-backed reader has never been run against the provider.
2. **The release is synthetic.** Every answer says `synthetic: true`, the website shows a banner, and no page may be indexed. That stays so until a real release is built.
3. **One machine, no more.** A shared search is kept in the machine's memory. A second machine would not find a link the first one made. Every deploy and every restart forgets every link. This holds until shares have a store.

You need: an account at Fly.io and at Vercel, a domain, `flyctl` and `curl` on the machine you deploy from, and a checkout of this repository. Docker is not needed: Fly.io builds the image on its own builder.

## What it costs a month

No price is given here. A price read on one day is soon out of date, and this guide cites no host's price page. Read each host's own price page on the day. Section 12 of the plan says what is allowed for each job.

| Item | Priced by | Notes |
|---|---|---|
| One `shared-cpu-1x` machine, 512 MB, London, always on | Fly.io | The plan allows for two machines |
| An address and a certificate | Fly.io | |
| Data sent out | Fly.io | Small: an answer is a few kilobytes |
| The website, one seat | Vercel | Burro is a product, so plan for a paid plan |
| DNS | The DNS host | |
| Domain | The registrar | Paid by the year |
| Hosted CI | GitHub | The repository is public |
| Object storage, later | Cloudflare | |
| A database and sign-in, later | Supabase | |
| Error reports, later | Sentry | |
| The model, later | The provider, by use | The plan, section 12 |

## The steps, in order

Replace `DOMAIN` with the domain, for example `burro.example`, and `APP` with the Fly.io app name. The website is at `https://DOMAIN` and the API at `https://api.DOMAIN`. If the website is to live at `www.DOMAIN`, use that wherever the website's origin is asked for.

### 1. The domain

1. Register the domain.
2. Choose where its DNS is hosted. If it is Cloudflare, every record below must be **DNS only**, the grey cloud. With the proxy on, Cloudflare ends TLS itself and sees every request body, which holds what a person typed. That is a new place for user text, and needs a decision first.

### 2. The API, on Fly.io

```
fly auth login
fly apps create APP --org personal
```

Open `deploy/api/fly.toml`. Set `app` to `APP`. Set `BURRO_ALLOWED_ORIGINS` to `https://DOMAIN`. Commit the change.

From the repository root:

```
fly deploy . \
  --config deploy/api/fly.toml \
  --dockerfile deploy/api/Dockerfile \
  --ignorefile deploy/api/Dockerfile.dockerignore \
  --ha=false
```

`--ha=false` matters. Without it the first deploy makes two machines.

```
fly status --app APP
fly scale count 1 --app APP        # only if `fly status` shows more than one machine
fly certs add api.DOMAIN --app APP
```

`fly certs add` prints the DNS record to make. It is a `CNAME` from `api` to `APP.fly.dev`. Make it at the DNS host, then:

```
fly certs check api.DOMAIN --app APP
```

If the certificate has not been issued after a few minutes, run `fly certs show api.DOMAIN --app APP` and add the `_acme-challenge` record it names. Port 80 is closed on purpose, and that record lets the certificate be proved through DNS instead. Whether Fly.io needs it has not been tried.

If the deploy fails its health check, read `fly logs --app APP --no-tail`.

| The log says | It means |
|---|---|
| `a setting in the environment is not in the form it needs` | `BURRO_ALLOWED_ORIGINS` still holds the placeholder, or has a path, a slash at the end, a capital letter or the port `443` in it |
| `the release could not be loaded`, with a file and a rule | The release folder in the image is not what its manifest says. `RELEASE_ID` in the Dockerfile must be the name of a folder under `data/fixtures/synthetic/` |
| `could not listen on` | The port is taken or not allowed. `BURRO_PORT` in the image and `internal_port` in `fly.toml` must both be 8080 |

### 3. The website, on Vercel

The API must be up first. With the API's address set, a build of the website calls the API, and a failure stops the build.

Follow [web/README.md](web/README.md): import the repository, set the root directory to `apps/web`, set the two environment variables, set the region, deploy. Then add `DOMAIN` under the project's domains and make the records Vercel shows.

### 4. Confirm it worked

The API:

```
curl -sS https://api.DOMAIN/healthz
# {"ok":true}

curl -sS -o /dev/null -D - https://api.DOMAIN/v1/meta
# HTTP 200, x-burro-synthetic: true, cache-control: public, max-age=3600

curl -sS -o /dev/null -D - -H 'Origin: https://DOMAIN' https://api.DOMAIN/v1/meta | grep -i '^access-control-allow-origin'
# access-control-allow-origin: https://DOMAIN

curl -sS -o /dev/null -D - -H 'Origin: https://elsewhere.example' https://api.DOMAIN/v1/meta | grep -ci '^access-control-allow-origin'
# 0

curl -sS --max-time 5 -o /dev/null -w '%{http_code}\n' http://api.DOMAIN/healthz
# no answer from Burro: the connection is refused, is reset or times out.
# A 200 or a redirect means port 80 is open

curl -sS https://api.DOMAIN/v1/interpret -H 'content-type: application/json' \
  -d '{"text": "leafy, 30 minutes to Cindermoor Works"}'
# "interpreter": "rule" and "synthetic": true
```

Nothing typed is in the log. Send a marker found nowhere else, then look for it:

```
curl -sS -o /dev/null https://api.DOMAIN/v1/interpret -H 'content-type: application/json' \
  -d '{"text": "I work at Quillfeather Zebrano"}'
fly logs --app APP --no-tail | grep -ci 'quillfeather'
# 0
fly logs --app APP --no-tail | tail -3
# one JSON line a request: the route template, a status, a latency. No path, no text
```

The website:

```
curl -sS -o /dev/null -D - https://DOMAIN/ | grep -i -E '^(content-security-policy|referrer-policy|x-content-type-options|permissions-policy|strict-transport-security|x-powered-by)'
# the four headers of web/README.md. connect-src names https://api.DOMAIN and no other host.
# no x-powered-by

curl -sS https://DOMAIN/robots.txt
# every crawler is asked to stay out, while the release is synthetic
```

Then open `https://DOMAIN` in a browser, search, open an area, compare two, make a share link and open it in a private window. The banner says the data is made up. The browser's network panel shows calls to `api.DOMAIN` and to no other host.

### 5. Later

| When | What | Note |
|---|---|---|
| The privacy notice, the ICO registration and the provider's agreement are in place, quotas exist, and the evaluation set passes on it | The model | `fly secrets import --app APP`, then type the three that must agree, one on each line, then end the input: `BURRO_MODEL_PROVIDER=` and the provider, the provider's key in the variable [models.md](../docs/design/models.md) names for it, and `BURRO_MODEL_TERMS_ACCEPTED=` and the provider again. A key alone turns nothing on, and the service says in one line as it starts which of them is missing. It reads them from the keyboard, so the key is not kept in the shell's history. Set a spend limit on the provider's workspace first, and build the website again afterwards: its methods page is built from what the service says |
| A real release exists | The release | Build it into the image by changing `RELEASE_ID` and the folder it is copied from, or fetch it from R2 when the machine starts. The second needs code that does not exist yet |
| The map needs tiles | Cloudflare R2 | Choose where the bucket is kept when it is made. Which choices there are was not read |
| Sign-in is built | Supabase | London, on a paid plan |
| Shares need to outlive a deploy | A store for shares | Until then, one machine |

## Privacy settings, host by host

ADR 0005 and ADR 0011 say what may never be written down: what a person typed, a destination, a place id, a fact id, a share id, and anything worked out from a spec. The code keeps that in its own log. These are the settings that keep it at each host.

| Host | What reaches it | What it writes down | Where | Kept for | Set this |
|---|---|---|---|---|---|
| Fly.io | Every call to the API. The body of a `POST` holds what a person typed. A path can hold a share id | The service's own lines, and only those: one JSON line a request, built from a fixed list of fields. No body, no path, no header. The server's access log is off in code. What Fly.io's own proxy records about a request was not read | The machine is in London. TLS may end at the Fly.io server nearest the visitor, which may be outside the UK. That was not read on Fly.io's pages | 7 days, read at <https://fly.io/docs/monitoring/logging-overview/> | No log shipper. No second region. No metrics or tracing add-on that records paths |
| Vercel | Requests for pages. The path of an area's page holds its slug, and the address of a comparison holds `a=slug`. Never what a person typed: the browser calls the API itself. A share id stays in the fragment, which a browser sends to no server | The path, the query string, the status and the browser's name | Functions in London. Static files may be served from any region. That was not read on Vercel's pages | 1 day on the Pro plan, read at <https://vercel.com/docs/logs/runtime> | Function region `lhr1`. Web Analytics off. Speed Insights off. No log drain. No Observability Plus. Toolbar off in production |
| DNS host | The names that are looked up | | | | Records are DNS only. No proxy in front of the API or the website |
| GitHub | The source and the CI logs, both public | No user data: tests are offline and use canaries | | | No secret in CI. None is needed |
| Model provider, later | The prompt, once a provider is turned on. The search settings too, if the service is set to send them | It differs by provider. `services/api/src/burro_api/providers/terms.py` holds what a tool read of each provider's pages, which nobody has checked and the service serves to nobody. The service serves a link to the provider's own terms | It differs by provider, and none offers a UK region | It differs by provider | Nothing until the conditions in step 5 are met. The privacy notice must say what the service serves |
| Sentry, later | Errors | Must be set to: request bodies off, default PII off, a scrubber | To be chosen. Which regions there are was not read | | Attach it at `logs.log_failure` and nowhere else |

Two things follow for the privacy notice. Fly.io and Vercel are processors and must be named. And "hosted in London" is true of where the API runs. It may not be true of where a visitor's connection is first decrypted.

## Blocking a client that abuses the service

Burro builds nothing to block anyone: no accounts, nothing that follows a person, and no store of what was typed (ADR 0023). A client that abuses the service is blocked afterwards, by its address, at the host's edge. The sign of abuse is a run of `interpret` lines with `call_status` `refused` in `fly logs`, or a notice from the provider. Neither says who it was: Burro's log holds no address, so who it was is in the host's own record of requests. At Vercel, the project's Firewall blocks an address or a range of them for a host (IP Blocking), and limits how often one address may ask within a window of 10 seconds to 10 minutes (a rate limit rule, counted by IP). Both were read on <https://vercel.com/docs/vercel-firewall/vercel-waf/ip-blocking> and <https://vercel.com/docs/vercel-firewall/vercel-waf/rate-limiting> on 2026-09-24. **That stands in front of the website and not in front of the API**, which the browser calls itself, at Fly.io. Fly.io's pages on `fly.toml` and on networking, read on the same day through a reader that summarises, name no block list and no limit by address: `concurrency` in `fly.toml` limits what one machine takes from everyone, not what one client sends. So as this guide stands, a client of the API can be blocked at an edge only once a host with a firewall stands in front of the API. That host would see the body of every request, which holds what a person typed. It is a new place for user text, and needs a decision first, as step 1 says of a proxy. Until then what limits the API is the spending cap on the provider's project and `hard_limit` in `fly.toml`.

## Rolling back

**The API.** Every deploy keeps its image.

```
fly releases --app APP --image
fly deploy . --config deploy/api/fly.toml --image IMAGE --ha=false
```

`IMAGE` is the reference of the release to return to, as the first command prints it. The settings come from `fly.toml` as it is in your checkout, so check out the commit that release was made from if the settings changed too. The release is inside the image, so the data goes back with the code. A rollback is a deploy: every share link is forgotten.

**The website.** In Vercel's dashboard, on the project's page, press Instant Rollback and choose the deployment. After a rollback, new pushes to the main branch no longer go live by themselves. To undo that, promote a deployment: `vercel promote DEPLOYMENT`. A rolled-back build holds the environment variables it was built with.

**Both.** Roll the website back first if the API's contract changed, so that no page calls a route that is gone.

## Pins, and what changes when the lockfiles are committed

| Thing | Pinned how, today | Why not more | The change to make |
|---|---|---|---|
| Base image | By exact tag, `python:3.13.15-slim-trixie` | No digest has been read. The tag was seen on Docker Hub on 2026-09-23 | Run `docker buildx imagetools inspect python:3.13.15-slim-trixie`, and write the digest it prints after the tag in `PYTHON_IMAGE`, as `python:3.13.15-slim-trixie@sha256:...`. An old tag gets no more security updates, so move the pin when Python does |
| Python packages in the image | By the ranges in each `pyproject.toml` | No lockfile is committed yet (ADR 0008) | Once `uv.lock` is committed: let `uv.lock` and the root `pyproject.toml` into `Dockerfile.dockerignore`, and in the build stage install what `uv export --locked --no-dev --no-emit-workspace --package burro-api` lists, with `pip install --require-hashes`, before the two local folders with `--no-deps` |
| Python packages in CI | The same | The same | `uv sync --locked`, as ADR 0008 says |
| Website packages, in CI and on Vercel | By the `~` ranges in `apps/web/package.json` | No `package-lock.json` is committed | `npm ci` in the `web` job and as Vercel's install command |
| Node in CI | Not pinned: the runner's own, 22 on 2026-09-23 | No action that installs Node is pinned by commit in `ci.yml` | Add `actions/setup-node` by commit, with one Node version |
| Actions in CI | By commit | | |

Until then two builds of the same commit can differ, and a build can break on a day nothing was committed, because a dependency published a release.

## What has not been checked

- The image has never been built. The `image` job in `.github/workflows/ci.yml` is the first place it will be built.
- The steps of the Dockerfile were done by hand: `pip install` of the two folders into a fresh environment, the release copied to another path, and the installed service driven in memory. It answered `/healthz` and `/v1/meta`, and refused the placeholder origin before it listened. It was not run over a socket.
- `fly.toml` and `vercel.json` parse. Neither has been read by its host.
- The new CI jobs have never run.
- The two retention figures were read on the hosts' pages on 2026-09-23, through a reader that summarises. No price was kept.
