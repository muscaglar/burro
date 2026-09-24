# 0002. Deterministic core, model at the edges

Status: accepted, 2026-09-23

## Context

Burro's promise is that it shows its working. A language model that ranks or describes neighbourhoods from memory cannot keep that promise: its answers vary, cannot be traced, and can be wrong about real places.

## Decision

- `rank(spec, release_id, engine_version)` is a pure function. Same inputs, same output. In code the release is passed as an object and the engine version is a constant, and the result records both.
- The model does two jobs only. It turns language into typed edits to a preference spec, and it writes explanations from a table of stored facts.
- Destinations are resolved by Burro's own place index, never by the model.
- A verifier checks every number and proper noun in an explanation against the cited fact before it is shown. Anything unsupported is replaced by a template.
- Sliders and chips produce the same typed edits as chat, through one reducer, with no model call.

## Consequences

- Ranking is testable without a model and costs nothing to re-run.
- Shared links reproduce exactly.
- If the model is slow, capped or down, the product degrades to a form instead of failing.
- Explanations read a little stiffer than free prose.

## What would change it

Evidence from real usage that people want something the fact table cannot express. Even then the change would be to add facts, not to let the model assert them.
