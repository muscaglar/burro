---
name: verify
description: How to run Burro and watch a change work. Use before committing anything that changes behaviour.
---

# Verifying a change in Burro

Drive the real command, not the tests. `make ci` tells you the tests pass; it does not tell you the tool behaves.

## Setup

```
make setup
```

Needs `uv`, `ruff`, `pyright` and `make` on your PATH. Use the package index the machine is already configured for. Do not pin or override it.

## Surfaces

| Surface | How to drive it |
|---|---|
| Licence registry | `uv run burro-registry [--path FILE_OR_FOLDER] check [--strict]`, `list`, `attributions` |
| Ingest gate | A short script that imports `burro_pipeline.registry`, calls `load(path)` then `registry.require(id, use)`. Run it with `uv run python script.py` |
| A data release | `uv run burro-release check FOLDER`. `make fixture` rebuilds the synthetic one |
| The API | `make api`, then `curl` against `127.0.0.1:8000`. Where no port can be opened, the test client: see below |
| The API contract | `make openapi`, then `git diff contracts/openapi.json` |
| The website | Build it against a running API and drive it in a real browser: see below |
| Repository hygiene | `make public-only` |
| The gate as a whole | `make ci` |

More surfaces arrive with the pipeline steps. Add them here when they do.

### Driving the website

Work from a copy, so a build never collides with someone else's.

```
BURRO_PORT=8300 BURRO_ALLOWED_ORIGINS=http://localhost:3300 uv run burro-api serve     # terminal 1
cp -R apps/web /tmp/burro-web && cp -R contracts /tmp/contracts && cd /tmp/burro-web    # terminal 2
NEXT_PUBLIC_BURRO_API_URL=http://localhost:8300 BURRO_SITE_URL=http://localhost:3300 npx next build
NEXT_PUBLIC_BURRO_API_URL=http://localhost:8300 BURRO_SITE_URL=http://localhost:3300 npx next start -p 3300
```

The API answers a browser only from the origins in `BURRO_ALLOWED_ORIGINS`, and the website's address of the API is fixed when it is built. Use `next build` and `next start`, not `next dev`, which rewrites `apps/web/AGENTS.md`.

Walk it at 1440 by 900 and at 390 by 844:

1. First visit: the map draws every area, and focus is not moved for you.
2. An example, then Search: what Burro read stands directly under the box, the list and the pins agree, and the address bar has not changed.
3. A sentence with a word the reader does not know: the page says so near the box, and ranks nothing it did not read.
4. Start again, then another search: nothing of the first is left.
5. Remove a chip, move a slider, press a pin, press "Show on the map": each changes one thing and says so.
6. On the phone, the Table tab: the page is no wider than the window.
7. An area's page, a comparison of two, a share made and then opened from its link.
8. Stop the API and search: the page says Burro could not be reached, and does not blame the words.

Then read what the browser recorded: no request to any host but the two you started, no typed word in any address, nothing in local storage, session storage or a cookie, and no error in the console that you did not cause.

### The API's routes

| Route | Send | What to look at |
|---|---|---|
| `POST /v1/interpret` | `{"text": ..., "spec": optional}` | `operations`, `spec`, `rejected`, `assumptions`, `clarify`, `notice`, `degraded` |
| `POST /v1/rank` | `{"spec": ..., "operations": optional, "limit": 1-100}` | `ranked`, `scores`, `filtered`, `unranked`, `spec_hash` |
| `POST /v1/explanations` | `{"spec": ..., "limit": 1-5}` | Every sentence cites a fact that is served |
| `POST /v1/compare` | `{"area_ids": [2 to 4], "spec": ...}` | Rows in the order of the spec's weights |
| `POST /v1/places/search` | `{"q": 2-80 characters}` | Names from the release, never the text sent |
| `POST /v1/shares`, `GET /v1/shares/{share_id}` | `{"spec": ..., "exact_destinations": false}` | `coarsened`, and the same ranking as `/v1/rank` gives the stored spec |
| `GET /v1/areas`, `/v1/areas/geometry`, `/v1/areas/{id_or_slug}`, `/v1/meta` | | `Cache-Control: public`, `ETag` |
| `GET /healthz` | | `{"ok": true}` |

### Driving the API without a port

This builds the app exactly as `burro-api serve` does. Save it in a scratch folder and run it with `uv run python`.

```python
import io
from burro_api import logs
from burro_api.app import create_app, deps_from
from burro_api.settings import Settings
from fastapi.testclient import TestClient

lines = io.StringIO()  # every line the service writes
logs.configure_logging(lines)
client = TestClient(create_app(deps_from(Settings.from_env({}))))
found = client.post("/v1/interpret", json={"text": "leafy, 30 minutes to Cindermoor Works"})
ranked = client.post("/v1/rank", json={"spec": found.json()["data"]["spec"]})
```

To make a model fail, pass `dataclasses.replace(deps, interpreter=...)` an interpreter whose `name` is `InterpreterName.CLAUDE` and whose `interpret` raises.

## Flows worth driving

**Registry**
1. Write a registry in a scratch folder with one source of each status: approved, gated, held, banned. Include an `audit_only` source and a share-alike source.
2. `check` exits 0. `check --strict` exits 1 if any warning is present.
3. Break one thing at a time and confirm the message names the source and the rule, and the exit code is 1: remove evidence, put a share-alike source into `scoring`, blank a `status_reason`, give a banned source a use.
4. Malformed input exits 2 with one readable line and no traceback: unknown field, unknown licence, quoted boolean, wrong `schema_version`, `source = "x"` instead of `[[source]]`, a file that is not UTF-8.
5. Run `uv run burro-registry check` from inside `packages/pipeline`. It must find the repository's registry.
6. Point `--path` at a folder. A source filed under the wrong dimension, and an empty folder, must each exit 2.

**Gate**
- The gate refuses the whole registry if any entry breaks an error rule, and if an id is used twice. `check` and `list` still read it and report.
- Approved source, registered use: allowed.
- Approved source, unregistered use: refused, and the message lists what it is registered for.
- `audit_only` source asked for `scoring`: refused.
- Gated or held source asked for an internal use it lists: allowed. Asked for anything else: refused with its reason.
- Banned source: refused for every use.
- Unknown id: refused, and the message says how to register it.

**The whole search, as the website will make it**
1. Interpret five prompts that should disagree: leafy and quiet, nights out, a buyer with children, a tight hard budget with two journeys, historic by the river. Give each a destination from `places.json`.
2. Rank each. The first areas must differ, and the reasons must be the ones the prompt gave. `spec_hash` from route 1 equals `spec_hash` from route 2.
3. Rank one spec ten times: the bodies are byte for byte the same. Shuffle its weights and change every provenance: the hash and the ranking do not move.
4. Change a weight and the budget through `operations`, then say the same in words with the spec attached. Both reach the same `spec_hash`.
5. Fetch an area by id and by slug, compare three areas of which one was filtered, search for a destination as it is typed, make a share of a spec that names a school and open it: the stored commute is the station that stands in for the school.
6. Every response, errors included, has `X-Burro-Synthetic: true` and `meta.synthetic: true`. Only `/healthz` has no `meta`.

**Breaking it**
Each of these must be answered with the error envelope or a rejected edit, never a 5xx and never an echo of what was sent: an empty prompt, a line of spaces, 601 characters, a 20 KB body, a prompt in another language (no edits, `unmet: other`), a budget of 0 and of 1, a cap of 1 minute and of 91 by public transport, 4 and 20 commutes in a spec and as edits, an unknown area in a path, a spec and an edit, an edit to a feature that is not in the allowlist, a spec with every weight at 0 (`empty_spec`, score 0, ordered by id), upper-case enum values in an edit (accepted), `NaN` and a weight of 1.5.

A prompt about who lives somewhere gets `policy_redirect` and the neutral notice, makes no edit for that part, and the rest is applied. "Safe" is rejected with `crime_needs_explicit_request`; "low crime" is applied. "Near a mosque" is `ok` with `community_amenities` unmet.

Copy the fixture to a scratch folder and damage it: remove a file, add one, change a byte, rename the folder. `burro-release check` and `burro-api serve` must each refuse it, exit 2, and name the file and the rule.

**Privacy**
Pick a marker found nowhere else, two made-up words in mixed case. Put it in the prompt, after "I work at", in the search text, in every string of a spec and of an edit, in unknown field names, in malformed JSON, in a path, a query string, the headers and the method. Do it again with an interpreter that raises an error built from the prompt, one that times out, and an explainer that raises. Then search, case folded: every log record in full with the root logger at `DEBUG`, every line the service wrote, standard output and error, every call record, and every response. The only place it may be found is what was sent to the model. No log line may hold `syn-p`, `syn-d`, a place name, a fact id or a share id.

**public-only**
Work in a throwaway copy so the real git index is never touched:
```
copy=$(mktemp -d)
git ls-files -z --cached --others --exclude-standard | while IFS= read -r -d '' f; do
  mkdir -p "$copy/$(dirname "$f")"; cp "$f" "$copy/$f"; done
cd "$copy" && git init -q . && git add -A
```
Then plant a file holding a URL with a token, and separately `git add -f` a lockfile that names a non-public host. Each must fail with exit 2 from `make`, and the output must not print the private hostname. Remove them and confirm it passes again.

Also: stage a file holding a URL with a token, fix it on disk without staging again, and confirm the check still fails and says `(staged)`. Put a private host anywhere in a `pyproject.toml`, and in a `package-lock.json` under `resolved`, and confirm each fails. The marker `public-only: allow` must not excuse a private host: it applies to placeholder credentials only.

If the machine has a private package host configured, write that host with no URL scheme into a Dockerfile `FROM` line and into a markdown file, and confirm both fail without the host appearing in the output. Hold the host in a shell variable; never echo it.

## Gotchas

- In zsh, `${PIPESTATUS[0]}` is empty; capture `$?` straight after the command, or use `$pipestatus[1]`.
- `ruff` and `pyright` are system prerequisites. Use the ones on your PATH, not ones installed into the project.
- Tests block the network. A test that needs it is wrong.
- `uv.lock` is ignored by git on purpose. See `docs/adr/0008-package-sources.md`.
- Binary files are skipped by `public-only`, so it will not see credentials inside one.
- Where no port can be opened, use the test client, and say the service was not run over a socket.
- A release folder holds its files and nothing else. A file browser can leave a hidden file in the fixture folder, and the release is then refused until it is deleted.
- `make openapi` and `make fixture` rewrite committed files. After either, `git diff` must be empty unless you meant to change a route, a record or the generator.
- The rule-based reader adds to the default weights. A prompt with no destination and no budget moves the ranking little; that is an open point in the contract, not a bug in the change you are checking.
