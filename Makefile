# What CI runs is what you run. `make help` lists the targets.
# Needs uv, ruff and pyright on your PATH.

.DEFAULT_GOAL := help
.PHONY: help setup ci lint format typecheck test registry-check fixture api openapi eval-reader public-only install-hooks

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | expand -t 18

setup: ## Install everything from the package index this machine is configured for
	uv sync
	@$(MAKE) --no-print-directory public-only

ci: public-only registry-check lint typecheck test ## Everything CI checks, clearest failure first

lint: ## Check style and formatting
	ruff check .
	ruff format --check .

format: ## Fix what can be fixed automatically
	ruff check --fix .
	ruff format .

typecheck: ## Strict type check
	pyright

test: ## Run the tests, offline. Pass options with ARGS="-k name"
	uv run pytest $(ARGS)

registry-check: ## Fail if a data source breaks a licence rule. ARGS=--strict before launch
	uv run burro-registry check $(ARGS)

fixture: ## Rebuild the synthetic release. Generated and committed, never edited by hand
	uv run burro-release build-synthetic --out data/fixtures/synthetic
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
.PHONY: plan fetch by-hand describe seal coverage

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
