# 0005. Raw prompts are never stored

Status: accepted, 2026-09-23. Tightened the same day by [0011](0011-nothing-is-kept-for-a-search.md), which this record now agrees with. Amended twice the same day: first what was logged of a spec became its hash under a key, and no longer its plain hash; then nothing worked out from a spec was logged, or kept about a call, at all.

## Context

People describing where they want to live volunteer their workplace, their child's school, their health, their religion, their sexuality. Some of that is special category data under UK GDPR. Logs and error trackers are the usual place it leaks: they are retained by default, often leave the region the database is pinned to, and have weaker access controls.

## Decision

Raw prompt text and destination strings are never written to any log, error report or database table.

- What is logged: how many edits were produced in each group, token counts, latency, model, status, release ID. Not a hash of the prompt, which can be guessed when the prompt is short, and not the edits, because a commute edit names a place.
- Nothing worked out from a spec is logged, and nothing of one is kept about a call: not its plain hash, and not its hash under a key. The one place a spec is stored is a share, which a person makes on purpose. A spec is a small space. A reviewer took one plain hash from a log line and found the workplace, the cap, the budget and the tag behind it in 21 seconds, by trying a million specs near the defaults. An HMAC under a key made at start-up cannot be reversed that way, but a checker who could read the log and call the service posted guesses and watched for the same value in a new line, and had the workplace after 247 requests. The only thing either hash was for was to tell that two calls were about the same search, and nothing needs to know that. The plain hash goes only in a response, to the client that sent the spec and so already holds it.
- `llm_calls` is metadata only. It has no text or JSON payload column and no column for a hash of a spec, and CI fails a migration that adds one. Rows expire after 30 days, and it is the writing of a row that lets the old ones go, wherever they stand, because nothing reads the table in the ordinary run of the service.
- The error tracker runs with request bodies off, default PII off, and a scrubber. It is hosted in the EU and named as a processor.
- A parse cache is keyed by an HMAC under a key that is never stored, held in memory, and expires after 24 hours. There is none until there is a model to pay for. Its key is never logged and never written down: it is looked up and nothing else.
- Phrases the model could not map are user text in disguise. They are not stored. What could not be met is kept as a category.
- Share links are opaque IDs. The spec is stored server-side, and destinations are coarsened unless the sender chooses otherwise.
- A test proves the parse handler's timeout and validation-failure paths do not log the request body.
- An evaluation set of real prompts is a separate table, filled only with explicit consent.

The only place raw text leaves Burro is the model API call. The provider retains inputs for up to 30 days, longer if flagged. The privacy notice says so.

## Consequences

- Debugging a bad parse means reproducing it, not reading it from a log.
- Measuring what people ask for needs counts and categories, not text.
- A spec cannot be looked up in the log, by its hash or by anything else, and two calls cannot be told to be about the same search. Counting how often a search is repeated would need a new decision.

## What would change it

Nothing short of explicit, per-user consent, and then only for the separate evaluation table.
