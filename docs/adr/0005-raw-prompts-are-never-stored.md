# 0005. Raw prompts are never stored

Status: accepted, 2026-09-23. Tightened the same day by [0011](0011-nothing-is-kept-for-a-search.md), which this record now agrees with. Amended twice the same day: first what was logged of a spec became its hash under a key, and no longer its plain hash; then nothing worked out from a spec was logged, or kept about a call, at all. **Amended on 2026-09-26** by [0044](0044-a-person-who-has-signed-in-may-keep-a-search-and-what-is-kept-is-the-spec-and-never-the-words.md): a share is no longer the one place a spec is stored. What is typed is still never stored. The last paragraph of the decision says what changed.

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

The only place raw text leaves Burro is the model API call, and only where a provider has been turned on. **Amended on 2026-09-24** by [0019](0019-no-one-provider-and-a-key-alone-turns-nothing-on.md): this record said that the provider keeps inputs for up to 30 days, which is what two of the four providers say. What a provider keeps, for how long and where is held by provider in `services/api/src/burro_api/providers/terms.py`, with the pages each answer was read on, and is served by the API. The words go alone unless the service is set to send the search settings with them. **Amended again the same day** by [0023](0023-what-is-typed-goes-as-typed-and-people-are-told.md): what a provider's pages say is kept as research, which nobody has checked, and is served to nobody. People are told whose language model reads what they type, and are given a link to the company's own terms. What is typed goes as it was typed.

**Amended on 2026-09-26** by [0044](0044-a-person-who-has-signed-in-may-keep-a-search-and-what-is-kept-is-the-spec-and-never-the-words.md), at the founder's asking. This record said that the one place a spec is stored is a share. Where accounts are on there is a second: a search that a person who has signed in keeps, or lets Burro keep as one of their last ten. What is kept of it is the spec, the release it was made on, and a name that code works out from the spec. **What is typed is still never stored**: not with a search that is kept, not under an account, and in no table of the file that holds accounts ([0045](0045-the-service-has-a-database-one-file-for-accounts-and-what-they-keep.md)). A person cannot name a kept search, because a name that is typed is typed text. One thing that a person types is kept, and is no prompt: the address of email they sign in by, which is the account. It is in no log.

## Consequences

- Debugging a bad parse means reproducing it, not reading it from a log.
- Measuring what people ask for needs counts and categories, not text.
- A spec cannot be looked up in the log, by its hash or by anything else, and two calls cannot be told to be about the same search. Counting how often a search is repeated would need a new decision.

## What would change it

Nothing short of explicit, per-user consent, and then only for the separate evaluation table.
