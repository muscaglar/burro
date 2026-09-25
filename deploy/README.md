# Putting Burro on the internet

The website and the API were first deployed on 25 September 2026, by hand, by the steps below, with the made-up city. The steps were written before that day, and have been brought to what was done. What was tried says so where it stands. The rest is untried, and "What has not been checked", at the end, lists it.

Every figure about a host below was read from that host's own pages on 2026-09-23. Check each one against the page before you rely on it. What "Serving a release of London" says of a host was read on 2026-09-25, and that part says where.

## What runs where

| Part | Host | Region | Files |
|---|---|---|---|
| API, `services/api` | Fly.io, one machine | `lhr`, London | [api/Dockerfile](api/Dockerfile), [api/fly.toml](api/fly.toml) |
| Website, `apps/web` | Vercel | Functions in `lhr1`, London. Static files on every region | [web/README.md](web/README.md), [web/vercel.json](web/vercel.json) |
| Names | None yet. Each host gives an address of its own: `https://APP.fly.dev` and `https://PROJECT.vercel.app` | | A domain is a later step: "A domain, once there is one" |
| Releases | Cloudflare R2, a bucket of its own | | A release of London is kept there once a hosted run has built it. It is taken from there before the image is built, and carried inside the image: "Serving a release of London". The machine that runs reaches no bucket |
| Tiles | Cloudflare R2 | Later | Not needed yet |
| Accounts | Supabase | Later, London | Not needed yet: there is no sign-in |
| Error reports | Sentry, EU | Later | Not wired in. See ADR 0005 before it is |

## Before you start

Three things the plan and the code already say, and a deployment must not undo.

1. **Do not set the model key yet.** The API works without one: the rules read the prompt. The plan says no outside person reaches the model until the privacy notice, the ICO registration and the provider's data processing agreement are in place. The service also has no quota and no rate limit yet (`admit` in `services/api/src/burro_api/app.py` is empty), so a key on the open internet is an open bill. And the model-backed reader has never been run against the provider.
2. **The release is synthetic.** Every answer says `synthetic: true`, the website shows a banner, and no page may be indexed. That stays so until you have approved a release of London and deployed it: "Serving a release of London". With nothing given, the image carries the made-up city.
3. **One machine, no more.** A shared search is kept in the machine's memory. A second machine would not find a link the first one made. Every deploy and every restart forgets every link. This holds until shares have a store.

You need: an account at Fly.io and at Vercel, `flyctl` and `curl` on the machine you deploy from, and a checkout of this repository. No domain is needed. Docker is not needed: Fly.io builds the image on its own builder.

## What it costs a month

No price is given here. A price read on one day is soon out of date, and this guide cites no host's price page. Read each host's own price page on the day. Section 12 of the plan says what is allowed for each job.

| Item | Priced by | Notes |
|---|---|---|
| One `shared-cpu-1x` machine, 512 MB, London, always on | Fly.io | The plan allows for two machines |
| An address and a certificate | Fly.io | |
| Data sent out | Fly.io | Small: an answer is a few kilobytes |
| The website, one seat | Vercel | The free plan was used for the first deployment. Vercel's terms keep that plan to work that is not commercial, so a launch needs the paid one. Read the terms on Vercel's own page before you rely on this |
| A domain and its DNS, later | The registrar and the DNS host | Paid by the year. Not needed to deploy |
| Hosted CI | GitHub | The repository is public |
| Object storage, later | Cloudflare | |
| A database and sign-in, later | Supabase | |
| Error reports, later | Sentry | |
| The model, later | The provider, by use | The plan, section 12 |

## The steps, in order

Replace `APP` with the name of the app at Fly.io, and `PROJECT` with the name in the address Vercel gives the project. The API is then at `https://APP.fly.dev` and the website at `https://PROJECT.vercel.app`. Each host serves its address over TLS, and there is no record to make. `deploy/api/fly.toml` holds both as they were deployed.

**The order matters.** The API answers a page only if it was served from an origin the API was told of, and the website has no address until it has been deployed once. So the website goes first, with no API. Then the API, which is told the website's address. Then the website again, which is told the API's.

### 1. The website, with no API yet

Follow [web/README.md](web/README.md), as far as the project settings: import the repository at Vercel, set the root directory to `apps/web`, set the install command and the build command, and deploy. **Set neither environment variable yet.** With no address of the API set, the website is built from the recorded answers, so it needs no API to be up. Vercel gives the project its address, which step 2 needs.

### 2. The API, on Fly.io

```
fly auth login
fly apps create APP --org personal
```

Open `deploy/api/fly.toml`. Set `app` to `APP`. Set `BURRO_ALLOWED_ORIGINS` to the address of step 1, `https://PROJECT.vercel.app`. Commit the change.

From the repository root:

```
fly deploy . \
  --config deploy/api/fly.toml \
  --dockerfile deploy/api/Dockerfile \
  --ignorefile deploy/api/Dockerfile.dockerignore \
  --ha=false \
  --depot=false
```

`--ha=false` matters. Without it the first deploy makes two machines. `--depot=false` builds the image on Fly.io's own builder: without it, the builder Fly.io uses by default built the image and was then refused as it stored it, with a 401.

Fly.io also offers to deploy from the GitHub repository. It fails, because the configuration is not at the top of the repository. Do not make it work: it would deploy on every push with no approval, and a release of London is never in the repository.

```
fly status --app APP
fly scale count 1 --app APP        # only if `fly status` shows more than one machine
```

If the deploy fails its health check, read `fly logs --app APP --no-tail`.

| The log says | It means |
|---|---|
| `a setting in the environment is not in the form it needs` | `BURRO_ALLOWED_ORIGINS` still holds the placeholder, or has a path, a slash at the end, a capital letter or the port `443` in it |
| `the release could not be loaded`, with a file and a rule | The release folder in the image is not what its manifest says. With nothing given to the build, `RELEASE_ID` in the Dockerfile must be the name of a folder under `data/fixtures/synthetic/` |
| `could not listen on` | The port is taken or not allowed. `BURRO_PORT` in the image and `internal_port` in `fly.toml` must both be 8080 |

### 3. The website again, with the API

Give Vercel the two environment variables, as [web/README.md](web/README.md) says: `NEXT_PUBLIC_BURRO_API_URL` is `https://APP.fly.dev`, and `BURRO_SITE_URL` is `https://PROJECT.vercel.app`. Then deploy again. The API must be up: with its address set, a build of the website calls the API, and a failure stops the build.

### 4. Confirm it worked

Each check of the API below was made on 25 September 2026, and passed, but the last: `fly logs` was not read for the marker, and that is still to be tried.

The name `APP.fly.dev` could be looked up a minute or two after the first deploy. A machine that had asked for it before the deploy went on answering for some minutes that there was no such name: wait, and ask again.

The API:

```
curl -sS https://APP.fly.dev/healthz
# {"ok":true}

curl -sS -o /dev/null -D - https://APP.fly.dev/v1/meta
# HTTP 200, x-burro-synthetic: true, x-burro-preview: false, cache-control: no-cache

curl -sS -o /dev/null -D - -H 'Origin: https://PROJECT.vercel.app' https://APP.fly.dev/v1/meta | grep -i '^access-control-allow-origin'
# access-control-allow-origin: https://PROJECT.vercel.app

curl -sS -o /dev/null -D - -H 'Origin: https://elsewhere.example' https://APP.fly.dev/v1/meta | grep -ci '^access-control-allow-origin'
# 0

curl -sS --max-time 5 -o /dev/null -w '%{http_code}\n' http://APP.fly.dev/healthz
# no answer from Burro: the connection is refused, is reset or times out.
# A 200 or a redirect means port 80 is open

curl -sS https://APP.fly.dev/v1/interpret -H 'content-type: application/json' \
  -d '{"text": "leafy, 30 minutes to Cindermoor Works"}'
# "interpreter": "rule" and "synthetic": true
```

Nothing typed is in the log. Send a marker found nowhere else, then look for it. **Still to be tried.**

```
curl -sS -o /dev/null https://APP.fly.dev/v1/interpret -H 'content-type: application/json' \
  -d '{"text": "I work at Quillfeather Zebrano"}'
fly logs --app APP --no-tail | grep -ci 'quillfeather'
# 0
fly logs --app APP --no-tail | tail -3
# one JSON line a request: the route template, a status, a latency. No path, no text
```

The website:

```
curl -sS -o /dev/null -D - https://PROJECT.vercel.app/ | grep -i -E '^(content-security-policy|referrer-policy|x-content-type-options|permissions-policy|strict-transport-security|x-powered-by|x-robots-tag)'
# the four headers of web/README.md. connect-src names https://APP.fly.dev and no other host.
# no x-powered-by. x-robots-tag: noindex, nofollow, while the release is made up

curl -sS https://PROJECT.vercel.app/robots.txt
# Allow: /, and no sitemap is named
```

**The robots file lets every crawler in, and that is meant.** While the release is made up, every page asks to be left out of a search engine, in its own markup and in the header `X-Robots-Tag: noindex, nofollow`. A crawler that the robots file kept out would never fetch a page, so it would never read that, and could still list the address from a link it found elsewhere. `apps/web/src/lib/indexing.ts` holds the one rule. Both were read on the deployed website on 25 September 2026: the robots file reads `Allow: /`, and every page carries `noindex, nofollow` in a header and in the page.

Then open `https://PROJECT.vercel.app` in a browser, search, open an area, compare two, make a share link and open it in a private window. The banner says the data is made up. The browser's network panel shows calls to the website's own host and to `APP.fly.dev`, and to no other host.

The website was walked so after the second deploy, on 25 September 2026. A search ranked areas. The page called the website's own host and the API's, and no other. Nothing that was typed was in the address. No cookie was set, and nothing was put in the browser's storage.

### 5. Later

| When | What | Note |
|---|---|---|
| You have a domain | The names | "A domain, once there is one", below. Nothing above waits on it |
| The privacy notice, the ICO registration and the provider's agreement are in place, quotas exist, and the evaluation set passes on it | The model | `fly secrets import --app APP`, then type the three that must agree, one on each line, then end the input: `BURRO_MODEL_PROVIDER=` and the provider, the provider's key in the variable [models.md](../docs/design/models.md) names for it, and `BURRO_MODEL_TERMS_ACCEPTED=` and the provider again. A key alone turns nothing on, and the service says in one line as it starts which of them is missing. It reads them from the keyboard, so the key is not kept in the shell's history. Set a spend limit on the provider's workspace first, and build the website again afterwards: its methods page is built from what the service says |
| You have approved a release of London | The release | "Serving a release of London", below. The image carries it, so the machine needs no bucket, no key and no network to start |
| The map needs tiles | Cloudflare R2 | Choose where the bucket is kept when it is made. Which choices there are was not read |
| Sign-in is built | Supabase | London, on a paid plan |
| Shares need to outlive a deploy | A store for shares | Until then, one machine |

## A domain, once there is one

**Not tried.** No domain was bought, and the steps above work without one. Replace `DOMAIN` with the domain, for example `burro.example`. The website is then at `https://DOMAIN` and the API at `https://api.DOMAIN`. If the website is to live at `www.DOMAIN`, use that wherever the website's origin is asked for.

1. Register the domain.
2. Choose where its DNS is hosted. If it is Cloudflare, every record below must be **DNS only**, the grey cloud. With the proxy on, Cloudflare ends TLS itself and sees every request body, which holds what a person typed. That is a new place for user text, and needs a decision first.
3. Give the API its name:

   ```
   fly certs add api.DOMAIN --app APP
   ```

   It prints the DNS record to make. It is a `CNAME` from `api` to `APP.fly.dev`. Make it at the DNS host, then run `fly certs check api.DOMAIN --app APP`. If the certificate has not been issued after a few minutes, run `fly certs show api.DOMAIN --app APP` and add the `_acme-challenge` record it names. Port 80 is closed on purpose, and that record lets the certificate be proved through DNS instead. Whether Fly.io needs it has not been tried.
4. Give the website its name: at Vercel, add `DOMAIN` under the project's domains, and make the records Vercel shows.
5. Tell each of the other. Set `BURRO_ALLOWED_ORIGINS` in `deploy/api/fly.toml` to `https://DOMAIN`, commit it, and deploy the API again, as step 2 of "The steps, in order". Set `NEXT_PUBLIC_BURRO_API_URL` to `https://api.DOMAIN` and `BURRO_SITE_URL` to `https://DOMAIN` at Vercel, and deploy the website again. Then make the checks of step 4 again, at the new addresses.

## Serving a release of London

For the founder. Written 2026-09-25. It applies [ADR 0030](../docs/adr/0030-a-release-is-kept-approved-by-its-lock-and-carried-in-the-image.md). **No release of London has been taken or served yet**, and no image has been built with one. One part of it has run on a host. On 25 September 2026 the image was built on Fly.io's builder with the made-up city, and the stage that holds what an image carries to a committed lock ran there, and passed. Every other step was driven on a machine of a developer's own, with a folder standing in for the bucket.

A release of London reaches the service in three moves. A hosted run builds it and keeps it in a bucket. You approve it, by committing its lock. Then you take it from the bucket and deploy, and the image carries it. [The guide to data builds](../docs/data-builds.md), under "London, from the bucket to the service", says the first two. This says the third.

| | |
|---|---|
| What is served | The release you name, and only if its lock is in `data/approved/` on the commit you deploy from |
| What stops anything else | The step `take` takes no release that no lock names, and holds every file to the hash its lock gives. The build of the image holds what it is handed to the lock again, and stops where a file differs, is missing, or is not named |
| What the machine needs to start | The image. No bucket, no key and no network |
| What the service says of itself | On every answer, as before: that it is not made up, and that it is a preview |
| Which key is used | The take key: it may read the bucket of releases, and no more. It is in your password manager, and on no host |
| Who builds the image | Fly.io, on its own builder, when you run `fly deploy`. The build is given no secret |

### Before you start

| You need | Why |
|---|---|
| The lock of the release on `main` | A release with no lock is refused. The guide to data builds says how a lock is committed, under "London, from the bucket to the service" |
| A working copy of `main`, with nothing changed | `fly deploy .` sends the builder what is in the folder, and the lock is read from there |
| `make setup` done in it | The step `take` is a step of the pipeline |
| The take key, and the address and the name of the bucket of releases | The same part of the guide, under "The three keys" |
| The API deployed once with the made-up city | It was, on 25 September 2026: steps 1 to 4 above. The app is then there |
| What an answer of a preview says, decided | The release is a preview and a development build, and its lock says both. ADR 0015 keeps a development build from the public. A preview says that it is one on every page, and no page of one may be indexed. Whether the address is one the public is given is yours to decide before you deploy |

### The steps

1. **Give the step its key, from the keyboard.** Nothing is kept in the shell's history.

   ```
   for name in BURRO_RELEASES_ENDPOINT BURRO_RELEASES_BUCKET BURRO_RELEASES_KEY_ID BURRO_RELEASES_SECRET; do
     printf '%s: ' "$name"; read -rs value; echo; export "$name=$value"
   done; unset value
   ```

   Paste the address Cloudflare shows for S3 clients, the name of the bucket of releases, and the id and the secret of the take key, each when it is asked for.

2. **Take the release.** From the top of the repository:

   ```
   rm -rf data/releases/served
   uv run python -m burro_pipeline take --release lon-2026-10-02-01 --out data/releases/served
   ```

   | It prints | It means |
   |---|---|
   | `step=take kind=object_store` | It was given a bucket, and not a folder |
   | `step=take status=ok release=lon-2026-10-02-01 files=21 bytes=... sha256=...` | Every file the lock names is in `data/releases/served`, and is the file the lock names. `sha256` is the hash of what the lock says, which the run that built the release showed |
   | `step=take status=missing release=...` | No lock names that release on this commit. It is not approved, or the working copy is not at `main` |
   | `step=take status=differs release=... differing=1` | A file in the bucket is not the file the lock names. Nothing was left in the folder. Do not deploy: build again under a new id, and approve that |
   | `step=take status=refused` | No release was named, and one is approved. Name it |
   | `error: ...` and nothing else | The bucket did not answer or refused the key, or the folder could not be written. The words say which |

3. **Put the key away.**

   ```
   unset BURRO_RELEASES_ENDPOINT BURRO_RELEASES_BUCKET BURRO_RELEASES_KEY_ID BURRO_RELEASES_SECRET
   ```

4. **Deploy, and name the release.** It is the command of step 2 of "The steps, in order", with two things more:

   ```
   fly deploy . \
     --config deploy/api/fly.toml \
     --dockerfile deploy/api/Dockerfile \
     --ignorefile deploy/api/Dockerfile.dockerignore \
     --build-arg RELEASE_ID=lon-2026-10-02-01 \
     --build-arg RELEASE_FROM=data/releases/served \
     --ha=false \
     --depot=false
   ```

   The log of the build holds one line of the check: `step=take status=ok release=lon-2026-10-02-01 files=21 ...`. If the build stops there, the line says why, as the table of step 2 does. `unlisted=` with a number says that the folder holds something beside the release: remove the folder and take the release again.

5. **Confirm what is served.**

   ```
   curl -sS -o /dev/null -D - https://APP.fly.dev/v1/meta | grep -i '^x-burro-'
   # x-burro-synthetic: false
   # x-burro-preview: true

   curl -sS https://APP.fly.dev/v1/meta | grep -o '"release_id":"[^"]*"'
   # "release_id":"lon-2026-10-02-01"
   ```

   Then do the checks of step 4 of "The steps, in order" again. Two of them read otherwise on London. The second shows `x-burro-synthetic: false` and `x-burro-preview: true`. The last names a made-up place, and is no test of London: send a wish of your own in its place, and look for `"synthetic": false` and `"preview": true` in the answer.

6. **Remove what was taken.** `rm -rf data/releases/served`. The release is in the bucket and in the image.

7. **Build the website again**, with a new deployment at Vercel. Its pages were built on the made-up city, and a page built on made-up data shows a notice and no figure while the service answers with real data. The banner then says that the release is a preview, and no page may be indexed while it is one.

### Going back to the release before

| To | Do this | What it needs |
|---|---|---|
| Go back at once | `fly releases --app APP --image`, then `fly deploy . --config deploy/api/fly.toml --image IMAGE --ha=false --depot=false`, as "Rolling back" says | Nothing but the host. The release is inside the image, so the data goes back with the code |
| Go back to any release you approved | Steps 1 to 7 again, with its id | Its lock is still in `data/approved/`, and its files are still in the bucket |
| Go back to the made-up city | Step 2 of "The steps, in order", as it is written. With no release named, the image carries the made-up city | Nothing |
| Stop a release from being served again | `git rm data/approved/lon-2026-10-02-01.json`, commit it, and bring it into `main`. Then deploy another release | No image can be built with it from then on. An image that carries it already is not changed: deploy another over it |

### What was read

Read on 2026-09-25, on the host's own pages, through a reader that summarises. Check the wording in a browser before relying on it.

| Page | What it says |
|---|---|
| Fly.io, `fly deploy` | `--build-arg`: "Set of build time variables in the form of NAME=VALUE pairs. Can be specified multiple times." `--remote-only`: "Perform builds on a remote builder instance instead of using the local docker daemon. This is the default." `--image`: "The Docker image to deploy". `--ignorefile`: "Path to a Docker ignore file." `--build-secret` is offered, and is not used here |
| Fly.io, continuous deployment with GitHub Actions | A hosted run deploys with the host's own program, set up by an action of the host's, and a token kept as `FLY_API_TOKEN`. No workflow of this repository may install either, so none deploys |
| Fly.io, access tokens | A deploy token is "limited to managing a single app and its resources". None is made here: you deploy signed in as yourself |
| Fly.io, builders | The page does not say what is sent to the builder, or what an ignore file does to it |

### What has not been checked

- **The image has never been built with a release of London.** What its stage that holds a release to its lock does was walked with no builder: each thing it copies was copied to a folder, and what it runs was run there. It accepted the release its lock names and the made-up city, and refused a release with one byte changed, a release no lock names, and a folder that held a second release.
- That the host's builder is handed `data/releases/served`. Git ignores the folder. The ignore file of the build lets it in, and whether the host sends what git ignores was not read.
- That the builder gives a build argument to every stage that asks for it. The Dockerfile states both arguments before its first stage, and each stage that reads one asks for it by name.
- **That the machine has the memory London needs.** Loaded with no socket, on a Mac, the service took 374 MB with London once it was loaded and 381 MB at its peak over sixteen requests, and 71 MB with the made-up city. The machine in `fly.toml` has 512 MB. If the health check fails after a deploy of London, read `fly logs` for a line that says the machine ran out of memory, and raise `memory` in `fly.toml`.
- How long a deploy takes with London. The image is about 90 MB larger than with the made-up city, of which 53 MB is the evidence.
- That `read -rs` reads without showing what is typed in the shell you use. It does in `zsh` and in `bash`.

## Privacy settings, host by host

ADR 0005 and ADR 0011 say what may never be written down: what a person typed, a destination, a place id, a fact id, a share id, and anything worked out from a spec. The code keeps that in its own log. These are the settings that keep it at each host.

| Host | What reaches it | What it writes down | Where | Kept for | Set this |
|---|---|---|---|---|---|
| Fly.io | Every call to the API. The body of a `POST` holds what a person typed. A path can hold a share id | The service's own lines, and only those: one JSON line a request, built from a fixed list of fields. No body, no path, no header. The server's access log is off in code. What Fly.io's own proxy records about a request was not read | The machine is in London. TLS may end at the Fly.io server nearest the visitor, which may be outside the UK. That was not read on Fly.io's pages | 7 days, read at <https://fly.io/docs/monitoring/logging-overview/> | No log shipper. No second region. No metrics or tracing add-on that records paths |
| Vercel | Requests for pages. The path of an area's page holds its slug, and the address of a comparison holds `a=slug`. Never what a person typed: the browser calls the API itself. A share id stays in the fragment, which a browser sends to no server | The path, the query string, the status and the browser's name | Functions in London. Static files may be served from any region. That was not read on Vercel's pages | 1 hour on the free plan, which is the plan in use, and 1 day on the Pro plan, read at <https://vercel.com/docs/logs/runtime> | Function region `lhr1`. Web Analytics off. Speed Insights off. No log drain. No Observability Plus. Toolbar off in production |
| DNS host, once there is a domain | The names that are looked up | | | | Records are DNS only. No proxy in front of the API or the website |
| GitHub | The source and the CI logs, both public | No user data: tests are offline and use canaries | | | No secret in `ci.yml`, which runs on a pull request from anyone. The workflows that fetch and build data hold the keys of the store in environments that you approve: [the guide to data builds](../docs/data-builds.md) |
| Cloudflare R2 | Publishers' files, and the releases built from them. Never what a person typed, and nothing of a search | Whatever it records of a request for a file. It was not read | Chosen when a bucket is made | | Public access off on both buckets. No domain on either |
| Model provider, later | The prompt, once a provider is turned on. The search settings too, if the service is set to send them | It differs by provider. `services/api/src/burro_api/providers/terms.py` holds what a tool read of each provider's pages, which nobody has checked and the service serves to nobody. The service serves a link to the provider's own terms | It differs by provider, and none offers a UK region | It differs by provider | Nothing until the conditions in step 5 are met. The privacy notice must say what the service serves |
| Sentry, later | Errors | Must be set to: request bodies off, default PII off, a scrubber | To be chosen. Which regions there are was not read | | Attach it at `logs.log_failure` and nowhere else |

Two things follow for the privacy notice. Fly.io and Vercel are processors and must be named. And "hosted in London" is true of where the API runs. It may not be true of where a visitor's connection is first decrypted.

## Blocking a client that abuses the service

Burro builds nothing to block anyone: no accounts, nothing that follows a person, and no store of what was typed (ADR 0023). A client that abuses the service is blocked afterwards, by its address, at the host's edge. The sign of abuse is a run of `interpret` lines with `call_status` `refused` in `fly logs`, or a notice from the provider. Neither says who it was: Burro's log holds no address, so who it was is in the host's own record of requests. At Vercel, the project's Firewall blocks an address or a range of them for a host (IP Blocking), and limits how often one address may ask within a window of 10 seconds to 10 minutes (a rate limit rule, counted by IP). Both were read on <https://vercel.com/docs/vercel-firewall/vercel-waf/ip-blocking> and <https://vercel.com/docs/vercel-firewall/vercel-waf/rate-limiting> on 2026-09-24. **That stands in front of the website and not in front of the API**, which the browser calls itself, at Fly.io. Fly.io's pages on `fly.toml` and on networking, read on the same day through a reader that summarises, name no block list and no limit by address: `concurrency` in `fly.toml` limits what one machine takes from everyone, not what one client sends. So as this guide stands, a client of the API can be blocked at an edge only once a host with a firewall stands in front of the API. That host would see the body of every request, which holds what a person typed. It is a new place for user text, and needs a decision first, as "A domain, once there is one" says of a proxy. Until then what limits the API is the spending cap on the provider's project and `hard_limit` in `fly.toml`.

## Rolling back

**Not tried, at either host.**

**The API.** Every deploy keeps its image.

```
fly releases --app APP --image
fly deploy . --config deploy/api/fly.toml --image IMAGE --ha=false --depot=false
```

`IMAGE` is the reference of the release to return to, as the first command prints it. The settings come from `fly.toml` as it is in your checkout, so check out the commit that release was made from if the settings changed too. The release is inside the image, so the data goes back with the code. A rollback is a deploy: every share link is forgotten. "Going back to the release before" says how a release of London that you approved is served again once its image is gone.

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

## What was checked on 25 September 2026

- Every job of hosted CI passed. The job `image` builds the image with nothing given, so it carries the made-up city whatever is approved, and starts it as its own user.
- `fly.toml` was read by Fly.io, which built the image on its own builder and deployed it. The service answers its health check.
- The checks of step 4, as that step says: all of the API's but the search of the log, the robots file and what asks a crawler to leave a page out, and the walk in a browser.
- The root directory, the install command and the build command were set by hand at Vercel, and the website was built twice: once from the recorded answers, and once from the API.

## What has not been checked

- That nothing typed is in `fly logs`: step 4.
- The website's other headers, as its host serves them. Whether Vercel adds `Strict-Transport-Security` was not noted.
- A rollback, at either host, and `fly scale count`.
- A domain, a certificate and a DNS record: "A domain, once there is one".
- A release of London: "Serving a release of London" lists what of it is untried.
- A model. No key is set.
- That the website's functions run in London. `vercel.json` is not read where it is, and whether the region was set by hand was not noted: [web/README.md](web/README.md).
- The two retention figures were read on the hosts' pages on 2026-09-23, through a reader that summarises. No price was kept.
