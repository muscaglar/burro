# verify:claude-api - Anthropic Claude API facts and the LLM cost model

I tried to refute 17 load-bearing claims against the live public docs read today (2026-09-23). Nothing major fell over. 14 are confirmed, 2 are partly wrong, 1 is refuted, and every correction has minor plan impact.

The cost figure stands. With confirmed Haiku 4.5 prices ($1 input, $0.10 cache read, $5 output per MTok) the arithmetic reproduces exactly: $18.25 per 1,000 searches, $22.81 with 25% contingency. The token counts behind it remain unmeasured estimates.

| Scenario | Per 1,000 searches |
|---|---|
| Report base, all Haiku 4.5, caches warm | $18.25 |
| Structured-output overhead lands outside the cache (+1,000 tokens per call) | about $20.75 |
| Caching fails, or caches are cold at launch traffic | about $29.50 to $29.75 |
| Forced move to Sonnet 5 | $40.40 to $47.40 |

The Sonnet 5 and Opus 5.5 rows in the report only reproduce if about 1,500 tokens of the explain prompt are cached, which the report does not state. Without that, all-Sonnet is $47.44 and all-Opus 5.5 is $118.62.

What needs correcting:
- **Schema complexity limits exist.** The report said it did not find them. The docs cap a request at 24 optional parameters and 16 union-typed parameters, so PreferenceSpec must be designed to fit.
- **Interpret and refine cannot share one cached prefix.** Changing `output_config.format` invalidates the prompt cache, and the `max_tokens: 0` pre-warm is rejected when structured outputs are set.
- **Retention wording conflicts between two reports.** The privacy notice should use the 30-day figure from Anthropic's commercial retention policy, not "not retained by default".

Two operational points matter for a public launch:
- The Start tier has a $500 monthly spend cap, about 27,400 searches at the base cost. Hitting it pauses the API until the next month.
- Haiku 4.5's retirement floor is 15 October 2026, 22 days away. No deprecation has been announced and 60 days' notice is promised.

Voyage AI pages were read through a reader that extracts, which is not the page itself. Nothing in the repository was touched.

## Checks
- [confirmed] Current line-up, identifiers and prices per MTok: Claude Fable 5.1 (claude-fable-5-1) $10/$50; Claude Opus 5.5 (claude-opus-5-5) $4/$20; Claude Sonnet 5 (claude-sonnet-5) $2/$10; Claude Haiku 4.5 (claude-haiku-4-5) $1/$5.
- [confirmed] The public docs recommend Claude Opus 5.5 as the default model, and it was released this week.
- [confirmed] Cache reads cost 0.1x input (0.05x on Opus 5.5, 0.025x on Fable 5.1); writes cost 1.25x (5 minutes) or 2x (1 hour). Minimum cacheable prefix is 4,096 tokens on Haiku 4.5, 1,024 on Sonnet 5 and 512 on Opus 5.5, and shorter prefixes silently skip caching.
- [confirmed] Structured outputs and Citations are both GA on the chosen models but cannot be combined in one request (400 error).
- [confirmed] Structured outputs do not support recursive schemas, numeric minimum or maximum, string length limits, array limits beyond minItems 0 or 1, or additionalProperties other than false. The SDK strips these and re-validates client-side. Compiled grammars are cached for 24 hours.
- [refuted] [impact minor] (llm-architecture) No documented limits on structured-output schema complexity (number of optional fields or union types) could be found, so the proposed PreferenceSpec was not checked against any limit.
  - evidence: The structured outputs page has a 'Schema complexity limits' section with explicit limits per request: strict tools 20; optional parameters 24 ('Each parameter not listed in `required` counts toward this limit'); parameters with union types 16 (anyOf or type arrays such as ["string", "null"]). Beyond these, internal grammar-size limits return 400 'Schema is too complex for compilation', and there is a 'compilation timeout of 180 seconds'.
  - correction: Design PreferenceSpec and the refine-operations schema to stay under 24 optional and 16 nullable or union fields in total. Prefer required fields with an explicit 'unspecified' enum value over optional or nullable fields, keep nesting shallow, and keep the arrays of {feature, weight} items the report already proposes. Compile both schemas against the API in week one.
- [partly_wrong] [impact minor] (llm-architecture) One stable cached system prefix of at least 4,096 tokens can serve both interpret and refine, kept alive at low traffic with a keep-warm request on the 1-hour TTL.
  - evidence: Structured outputs page: 'Changing the `output_config.format` parameter will invalidate any prompt cache for that conversation thread', and the feature injects an additional system prompt. Interpret and refine use different schemas, so they cannot be assumed to share a cache entry; the report itself uses this logic to separate interpret from explain. Prompt caching page, pre-warming limitations: a `max_tokens: 0` request 'is rejected with an `invalid_request_error`' when `output_config.format` is set.
  - correction: Plan for two cache entries, or one union schema used by both calls. Each prefix must independently exceed 4,096 tokens. Keep each warm with a real minimal request that carries the same output_config.format and max_tokens of at least 1. Keep-warm costs about $1 a month. Without it, a cold search pays cache writes and costs about $29.75 per 1,000 on the 5-minute TTL.
- [confirmed] Citations are guaranteed to point at supplied content, cited_text is not billed as output, and custom-content documents are cited by caller-defined block index with no further chunking, which allows per-block verification while streaming.
- [confirmed] The Message Batches API gives 50% off, stacks with caching, takes up to 100,000 requests or 256 MB, mostly finishes within an hour, and keeps results 29 days. The report left unverified whether it accepts structured outputs and citations.
- [confirmed] Start-tier limits for Haiku 4.5 are 1,000 requests, 2M uncached input tokens and 400k output tokens per minute, about 200 searches a minute. Spend caps are Start $500, Build $1,000, Scale $200,000. A workspace spend limit (platform-stack: a hard monthly limit on the API key) is the backstop.
- [partly_wrong] [impact minor] (accounts-compliance, llm-architecture) Anthropic may not train on customer content and the customer owns outputs. On retention, accounts-compliance says API inputs and outputs are deleted within 30 days; llm-architecture says conversation content is not retained by default except on Covered Models. Flagged content is kept up to 2 years and classifier scores up to 7 years.
  - evidence: Commercial Terms (effective June 17, 2025): 'Anthropic may not train models on Customer Content from Services'; customer 'owns its Outputs'; D.3 requires notifying users that factual assertions 'should not be relied upon without independently checking their accuracy'. Privacy Center article dated July 1, 2026: 'For Anthropic API users, we automatically delete inputs and outputs on our backend within 30 days of receipt or generation, except...'; 'up to 2 years and trust and safety classification scores for up to 7 years if your chat is flagged'. The docs page does say conversation content 'is not retained by default', but it defers to the Privacy Center article for standard retention. DPA (effective February 24, 2025): Anthropic is processor and a UK Addendum is included.
  - correction: Use the accounts-compliance wording in the privacy notice and DPIA: up to 30 days, up to 2 years if flagged, scores up to 7 years. Do not state that prompts are not retained. For a UK customer the contracting entity is Anthropic Ireland, Limited.
- [confirmed] Anthropic's Usage Policy requires consumer-facing interactive AI products to disclose that users are interacting with AI at the start of each session. The high-risk housing category covers eligibility decisions, not neighbourhood discovery.
- [confirmed] The first-party API offers inference geography 'global' or 'us' only and workspace geography 'us' only, so there is no UK or EU option. Haiku 4.5 does not accept inference_geo at all. US-only inference costs 1.1x.
- [confirmed] Haiku 4.5 is Active with retirement 'not sooner than 15 October 2026', no deprecation is announced, and Anthropic commits to at least 60 days' notice.
- [confirmed] Sonnet 5 can run with thinking disabled, uses a tokenizer producing about 30% more tokens, and rejects non-default sampling parameters. Opus 5.5 cannot disable thinking, rejects forced tool_choice, and defaults to medium effort.
- [confirmed] Voyage AI: voyage-4-large $0.12, voyage-4 $0.06, voyage-4-lite $0.02 per MTok; first 200M tokens free; batch 33% off. Terms last updated 27 May 2026 give Voyage a training licence by default, and opting out may void free tokens. voyage-4-nano is Apache 2.0 and shares the Voyage 4 embedding space.
- [confirmed] Cost is $18.25 per 1,000 searches on Haiku 4.5 (about $23 with 25% contingency); $29.5 with no caching; $31.9 with Sonnet 5 explanations; $40.4 all Sonnet 5; $104 all Opus 5.5; about $27 for an offline regeneration; about $540 a day under the stated abuse scenario.

## New facts
- Structured outputs have documented per-request limits: 24 optional parameters, 16 union-typed parameters (including nullable type arrays), 20 strict tools, and a 180-second grammar compilation timeout. Exceeding the internal grammar size returns 400 'Schema is too complex for compilation'.
- Structured outputs emit required properties first and optional ones after, regardless of schema order, and may return enum values with different capitalisation.
- The `max_tokens: 0` cache pre-warm is rejected with structured outputs, with streaming, and inside batches. Keep-warm for interpret and refine must be a real request with max_tokens of at least 1.
- Spend and rate limits cannot be set on the Default Workspace. A user-set spend limit returns HTTP 400 `invalid_request_error`. The tier cap returns 429 with error_code `enforced_spend_limit_reached` and no retry-after header, so SDK retries will not help.
- The Start-tier $500 monthly cap equals about 27,400 searches at $18.25 per 1,000, about 21,900 at $22.81, or about 16,900 if caching fails. Reaching it pauses all API use until the first of the next month unless a higher limit is granted.
- Nightly evals at the report's $3.40 per run come to about $100 a month, a fifth of the Start-tier cap. Structured outputs and citations both work in the Batch API, so evals can run there at 50% off.
- Commercial Terms H.1: Anthropic may change published rates with effect 30 days after posting. For customers in the UK, EEA or Switzerland the contracting entity is Anthropic Ireland, Limited.
- If EU processing becomes a hard requirement, Google Cloud offers an 'eu' multi-region endpoint and Amazon Bedrock offers EU inference profiles, both at a 10% premium. London (eu-west-2) is listed for global and EU routing only, so there is no UK-only pinning.
- On those cloud routes the Message Batches API is unavailable and the cloud provider, not Anthropic, is the data processor. The Bedrock Messages-API endpoint lists structured outputs as not supported; Google Cloud supports both structured outputs and citations.
- The anthropic Python SDK is at 1.8.0 (released 22 September 2026, Python 3.10 or later, MIT), with eight minor releases since 1.1.0 on 26 August 2026. Pin the version.
- SDK 1.x removed temperature, top_p and top_k from typed method signatures. On Haiku 4.5 they can only be passed through `extra_body`, and Sonnet 5 and later reject non-default values. Reproducibility must come from caching the query-to-spec result, not from temperature 0.
- Token counting is free, has its own rate limit, returns an estimate, and does not apply caching logic. Counts must be taken with the model ID that will be used, because the newer tokenizer produces about 30% more tokens.
- On Opus 5.5, accounts created on or after 31 August 2026 get a 400 if thinking blocks are replayed after earlier turns were edited. Burro's Anthropic account will be new, so keep offline Opus calls single-turn.
- Voyage free-token credits do not apply to Voyage Batch API usage, and voyage-4-nano's default output dimension is 2,048.

## Week one
- Create the Anthropic organisation and read the actual tier, rate limits and spend cap in the Console. A new organisation may start on the Evaluation tier with unpublished lower limits. Request a higher tier well before public launch.
- Create non-default workspaces per environment, issue keys from them, and set monthly spend limits and alerts. Confirm the app degrades to deterministic mode on both the 400 (user-set limit) and the 429 without retry-after (tier cap).
- Measure real token counts for interpret, refine and explain on Haiku 4.5 using the token counting endpoint and live `usage` fields, including structured-output and citations overhead. Re-run the cost sheet with measured numbers.
- Run a cache smoke test: assert `cache_read_input_tokens` is above zero on the second interpret call and the second refine call, confirm each prefix exceeds 4,096 tokens, and test whether the two calls share a cache entry.
- Compile the PreferenceSpec and refine-operations schemas against the live API. Confirm they stay under 24 optional and 16 union-typed parameters, and measure first-request grammar compilation latency.
- Measure p50 and p95 latency for the interpret call on Haiku 4.5 and on Sonnet 5 with thinking disabled before fixing the interaction design.
- Run the golden set on Sonnet 5 with thinking disabled alongside Haiku 4.5, and watch the deprecations page, because Haiku 4.5's retirement floor is 15 October 2026.
- Decide whether global inference with no UK or EU pinning is acceptable. If not, test the Google Cloud 'eu' multi-region route before building on first-party-only features such as the Batches API.
- Write the privacy notice and DPIA with the 30-day, 2-year and 7-year retention figures, naming Anthropic Ireland, Limited as processor with transfer under the DPA's UK Addendum.
- Put the AI disclosure at the start of every chat session on web and iOS, with the notice that outputs may be inaccurate, and have it checked against the Usage Policy wording.
- Pin the anthropic SDK version and keep model IDs in configuration. Make sure coding agents load current SDK documentation, since SDK 1.x is weeks old.
- Add a one-line CLAUDE.md beside every nested AGENTS.md, then confirm in a Claude Code session that package-level instructions actually load.
- Have a person read the full Voyage AI terms before any embeddings work starts. Embeddings are deferred, so this is low priority.