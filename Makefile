# What CI runs is what you run. `make help` lists the targets.
# Needs uv, ruff and pyright on your PATH.

.DEFAULT_GOAL := help
.PHONY: help setup ci lint format typecheck test test-split registry-check fixture api openapi eval-reader public-only install-hooks

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | expand -t 18

setup: ## Install everything from the package index this machine is configured for
	uv sync
	@$(MAKE) --no-print-directory public-only

ci: public-only registry-check lint typecheck test-split ## Everything CI checks, clearest failure first

lint: ## Check style and formatting
	ruff check .
	ruff format --check .

format: ## Fix what can be fixed automatically
	ruff check --fix .
	ruff format .

typecheck: ## Strict type check
	pyright

test: ## Run the tests plainly, in one process, offline. Pass options with ARGS="-k name"
	uv run pytest $(ARGS)

# The tests of one file stay in one process and in their order, so that what a file makes
# once is made once. One process for each core, unless JOBS says how many.
JOBS ?= auto

test-split: ## Run every test side by side, split by file, as make ci does. JOBS=4 sets how many processes
	uv run pytest -n $(JOBS) --dist loadfile $(ARGS)

registry-check: ## Fail if a data source breaks a licence rule. ARGS=--strict before launch
	uv run burro-registry check $(ARGS)

fixture: ## Rebuild the synthetic release. Generated and committed, never edited by hand
	uv run burro-release build-synthetic --out data/fixtures/synthetic --census-out data/fixtures/residents \
		--income-out data/fixtures/income
	uv run python -m burro_pipeline coverage data/fixtures/synthetic/syn-2026-09-23-01 \
		--made-up --out packages/pipeline/tests/evidence/fixtures/coverage-syn-2026-09-23-01.md

api: ## Run the API on this machine, on the synthetic release. BURRO_PORT=8000 by default
	uv run burro-api serve

openapi: ## Rewrite contracts/openapi.json from the routes. Generated and committed
	uv run burro-api openapi --out contracts/openapi.json

eval-reader: ## Score the sentence reader against evals/reader/cases. Fails if any case is read backwards. ARGS="--show declined"
	uv run python evals/reader/score.py $(ARGS)

public-only: ## Fail on a private package host, or a URL with credentials, in anything committable
	uv run --no-project python tools/check_public_only.py

install-hooks: ## Opt in to running public-only on what is staged, before every commit
	ln -sf ../../tools/pre-commit .git/hooks/pre-commit
	@echo "pre-commit hook installed"

# The steps of a data build. Each runs the pipeline's own command, and with no ARGS it prints
# the step's help and does nothing more. `uv run python -m burro_pipeline --help` lists every
# step. docs/data-builds.md says what to set up first.
.PHONY: plan fetch by-hand describe seal cells preview coverage

plan: ## Ask the licence registry about every file of a list. No network. ARGS="--list m1 --words"
	uv run python -m burro_pipeline plan $(or $(ARGS),--help)

fetch: ## Fetch the files of a list into the store. Reaches the publishers. ARGS="--list m1"
	uv run python -m burro_pipeline fetch $(or $(ARGS),--help)

by-hand: ## Take a file saved from a browser. ARGS="--list m1 --item NAME --file PATH --url ADDRESS --saved-on DAY"
	uv run python -m burro_pipeline by-hand $(or $(ARGS),--help)

describe: ## Say the shape of a file, on a machine of your own. ARGS="f-0123456789ab" or ARGS="--path FILE"
	uv run python -m burro_pipeline describe $(or $(ARGS),--help)

seal: ## Write the lock of a build: every input by its hash. ARGS as `make seal` alone prints them
	uv run python -m burro_pipeline seal $(or $(ARGS),--help)

cells: ## Make the geography of a build: areas, outlines and land. ARGS="--release-id ID --out FOLDER"
	uv run python -m burro_pipeline cells $(or $(ARGS),--help)

preview: ## Build the preview release of a first build. ARGS="--release-id ID --built-at TIME --out data/releases"
	uv run python -m burro_pipeline preview $(or $(ARGS),--help)

coverage: ## Write the coverage report of a release. ARGS="FOLDER --evidence FILE --out REPORT"
	uv run python -m burro_pipeline coverage $(or $(ARGS),--help)

# The website, in apps/web. Needs Node 20.9 or later and npm. None of it is part of `make ci`:
# hosted CI runs the website's check as a job of its own.
.PHONY: web-setup web-check web web-types web-record

web-setup: ## Install the website's packages, from the package index this machine is configured for
	cd apps/web && npm install

web-check: ## Everything the website is held to: types, lint, tests, the build, and every built page
	cd apps/web && npm run check

web: ## Run the website on localhost:3000 against the API on this machine. Run `make api` first
	cd apps/web && NEXT_PUBLIC_BURRO_API_URL=http://127.0.0.1:$(or $(BURRO_PORT),8000) npm run dev

web-types: ## Rewrite the website's API types after contracts/openapi.json changes
	cd apps/web && npm run gen:api

web-record: ## Record the API's answers again for the website's tests. Generated and committed
	uv run python apps/web/test/record.py

# The review desk, in tools/desk: where a person looks at data and decides. It runs on this
# machine alone and asks no other host for anything. It needs Python and no package, so it
# runs before `make setup`. Only filling the queues from real files needs the licence gate.
# None of the page's tests is part of `make ci`: hosted CI runs them in the job `desk`.
.PHONY: desk desk-check desk-take desk-fill desk-compile desk-publish
REVIEWER ?= r1
# The folder a draft of the areas was written to, which holds what it hands the desk, and
# the desk's folder of real data, which it is taken to.
DRAFT ?=
DESK ?= data/raw/desk
# A folder outside the repository, where a second copy of every decision is kept. Real data
# is not served without one: `git clean -x` removes data/raw, and the copy is what is left.
KEEP ?=

desk: ## Start the review desk on 127.0.0.1:8765, as r1, and print the address. KEEP=FOLDER, REVIEWER=r2, ARGS="--port 8766"
	@PYTHONPATH=tools uv run --no-project python -m desk serve --reviewer $(REVIEWER) $(if $(KEEP),--keep $(KEEP)) $(ARGS)

desk-check: ## Everything the review desk is held to: its own tests, and the page's. Needs Node 20 or later
	uv run pytest tools/desk
	node --test tools/desk/page/test/*.test.mjs

desk-take: ## Take a draft of the areas to the desk, and fill the queues from it. DRAFT=FOLDER, the folder the draft was written to
	@test -d "$(DRAFT)/desk/draft" || { echo 'Say where the draft is: make desk-take DRAFT=FOLDER. It holds desk/draft.' >&2; exit 2; }
	@mkdir -p "$(DESK)"
	@rm -rf "$(DESK)/draft"
	@cp -R "$(DRAFT)/desk/draft" "$(DESK)/draft"
	PYTHONPATH=tools uv run python -m desk fill --from "$(DESK)/draft" --data "$(DESK)"

desk-fill: ## Fill the desk's queues from a draft folder. ARGS="--from data/raw/desk/draft --data data/raw/desk"
	PYTHONPATH=tools uv run python -m desk fill $(or $(ARGS),--help)

desk-compile: ## Make a build's files from the decisions. ARGS="--data data/raw/desk --gazetteer gazetteer/london"
	@PYTHONPATH=tools uv run --no-project python -m desk compile $(ARGS)

desk-publish: ## Make the copy of the decisions that may be committed, and print its notes. ARGS="--to gazetteer/london"
	@PYTHONPATH=tools uv run --no-project python -m desk publish $(ARGS)
