# 0011. Nothing is kept for a search

Status: accepted, 2026-09-23. Tightens [0005](0005-raw-prompts-are-never-stored.md). The first point is a judgement call for the founder to confirm. Amended twice the same day: the point that was left open, the spec hash in logs, was decided, and then decided again, more strictly.

## Context

ADR 0005 keeps raw prompts and destination strings out of every log and table. Designing the API showed four ways the same facts could leak without a single string being stored:

- A search kept on the server needs an id, the id sits in a URL, and a URL reaches logs Burro does not control. For as long as the search is kept, the id unlocks where someone works.
- A `place_id` is an id from the release and not the user's words, but it says where someone works or where their child goes to school.
- A hash of a short prompt can be guessed by trying prompts.
- A hash of a spec can be guessed by trying specs. A spec near the defaults with one commute is a small space. Under a key it cannot be guessed, but whoever can read the log and call the service can still have a guess confirmed.

## Decision

- The server holds no search between requests. The client holds the spec and sends it again to rank, to explain, to compare and to share. There is no search id and no route that returns a search.
- A share is the only place a spec is stored, and a person makes one on purpose. Its id is 128 random bits and is never derived from the spec. Destinations are replaced by the station or district that stands in for them, unless the sender asks for the exact places.
- A `place_id`, a `destination_id`, a `fact_id` and a `share_id` are treated as destination strings are: never logged.
- Everything a person types travels in a `POST` body. No route takes typed text in a path or a query string.
- Logging is a list of what may be written, not a scrubber of what may not. A line is an event name and named fields; a field that is not on the list cannot be logged; no message is ever formatted. An exception is logged as its type and its frames.
- What is kept about a call to an interpreter is metadata: counts of edits by group, rejections by reason, unmet categories, token counts, latency and status. No hash of the prompt, no edit, no phrase the interpreter could not map, and nothing worked out from the spec.
- Nothing worked out from a spec is logged, and nothing of one is kept about a call: not its plain hash, and not its hash under a key. No field on the list of what may be logged could hold one, the call record has no field for one, and the service holds no key. The plain hash stays in responses, where the client already holds the spec it is the hash of.
- There is no parse cache in this build. With no model to pay for there is nothing for it to save. When there is one it is keyed by an HMAC under a key made at start-up and never stored, it is held in memory, and its key is looked up and nothing else: never logged, never written down.

## Consequences

- Ranking again costs a request. It takes milliseconds.
- Debugging a bad parse means reproducing it. There is nothing to read back.
- Measuring what people ask for needs categories, not text.
- A shared link ranks a little differently from the search it came from, because a station stands in for the workplace. The response says so.
- Two calls cannot be told to be about the same search, from a log or from a call record. Nothing in the service needs to. Whoever wants to count how often a search is repeated will find nothing to count with, and must ask for a new decision.
- There is no key to look after, to rotate or to lose.

## What was open, and is decided

The spec hash was logged plain, as the plan and ADR 0005 said. A reviewer showed it was practical to reverse: from the hash in one log line, the README's own example gave up its workplace, cap, budget, segment and tag after a million tries, in 21 seconds of plain Python. The same line carried the categories that could not be met, so a request about a place of worship sat beside a hash that led to a child's school.

Decided first, 2026-09-23: log and store an HMAC of the spec under a key made when the service starts and written nowhere. A checker then took the keyed value from one line of somebody's search, posted guesses at the spec to another route, and read the keyed value from each new line. The guess was confirmed after 247 requests, in a little over a second. The key kept the hash from being worked out on another machine. It did nothing against whoever reads the live log and can call the service, and there are no quotas in this build.

Decided again, 2026-09-23: nothing worked out from a spec is logged, or kept about a call, at all. The keyed hash said one thing, that two calls were about the same search, and nothing was found that needs to know it. A limit on calls would have slowed the guessing and not ended it. The field `spec_mac` is gone from the log line and the call record, and the module that held the key is gone with it. The plan still names the spec hash among the columns of `llm_calls`; there is no such column.

## What would change it

Accounts. A saved search then belongs to someone who is signed in, is reached with their session and not by an id in a URL, and is deleted with their account.

## Still to confirm: what route 1's line says of a reading

This record allows counts of edits by group, rejections by reason and unmet categories to be kept about a call, and forbids anything worked out from a spec. On route 1 the two meet. The counts and codes in the log line are worked out from the words and the spec together, so the same words leave a different line when only the spec differs: "a bit cheaper" is rejected as `nothing_to_change` where the spec holds no amount. None holds an id, a name or a number of the spec, none can be matched to a spec without the words, which are in no line, and the call record does not differ. A test holds the line to exactly that. Whether to go on logging them, or to take the four fields out of the list of what may be logged, is the founder's call. Nothing was changed.
