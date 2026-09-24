# Anthropic Claude, from its own documents

Read on 23 September 2026. A dated snapshot: model names, prices and terms change often. Re-check before relying on a figure.

This is one of four reports, one a provider. The same nine questions were put to each.

## How this was read

| Point | What it means for you |
|---|---|
| The developer pages were downloaded as text from `platform.claude.com`, by adding `.md` to each address | Quotes and examples from those pages are copied, not summarised |
| The legal and privacy pages were downloaded as web pages and the tags were stripped | The words are the provider's. Line breaks and list marks are lost. Check the wording at the address given before it goes into a privacy notice or a contract |
| Prices were checked on two pages of the provider's: the developer page and `claude.com/pricing` | They agree |
| No key, and no call to the provider | Nothing here was tested against the live service |
| This report and the three beside it were held to the same questions | Every claim is tied to a page, so it can be checked |
| Nothing here is legal advice | |

"Read" in a table below means read at the provider's own address on the day. "Not read" means it is an inference, or the page did not say.

## In short

| Question | Answer | Read |
|---|---|---|
| Can it do the job | Yes. One POST, a key in a header, JSON back | Read |
| Is the schema enforced | Yes, by constrained decoding, with three written exceptions: a refusal, an answer cut short, and the case of an enum value | Read |
| Does Burro's schema fit | On paper, yes. It uses eight keywords, no optional field and no union. One keyword, `$defs`, is spelt differently on the page | Read, not tested |
| Smallest model fit for the job | `claude-haiku-4-5-20251001` | Read |
| Its retirement | "Not sooner than October 15, 2026". No notice has been given. 60 days' notice is promised | Read |
| Cost of 1,000 searches | $4.50 on the smallest model. The cache does not apply at this length on that model | Worked out from prices that were read |
| Where the text is processed | "select countries in the US, Europe, Asia and Australia". Stored in the US. No UK or EU choice on this API | Read |
| How long the text is kept | Up to 30 days. Up to 2 years if flagged. Safety scores up to 7 years | Read |
| Is it used to train models | No. "Anthropic may not train models on Customer Content from Services" | Read |
| Zero retention | Offered, by arrangement with the sales team, one organisation at a time | Read |
| Data processing agreement | Yes. It is part of the Commercial Terms and is accepted with them | Read |
| A safeguard for a transfer from the UK | The UK Addendum to the EU standard contractual clauses, written into the agreement | Read |
| What the provider says of sensitive data | The agreement lists special categories of personal data as "None" | Read |

The adapter can be built and tested. Three things stand between it and a real person's sentence: the agreement does not plan for special category data, there is no UK or EU region on this API, and the smallest model may be given notice at any time. The last section puts them to the founder.

## 1. The call

| Item | Value | Read |
|---|---|---|
| Base address | `https://api.anthropic.com` | Read |
| Address | `https://api.anthropic.com/v1/messages` | Read |
| Method | `POST` | Read |
| Header that carries the key | `x-api-key: <key>`, or `Authorization: Bearer <key>` | Read |
| May the key go in a header | Yes. Both forms are headers. No key in a query string is documented on any page read | Read |
| Other headers that must be sent | `anthropic-version: 2023-06-01` and `content-type: application/json` | Read |
| A header needed only for some keys | `anthropic-workspace-id`, for a key that is not tied to one workspace | Read |
| Beta header for structured output | None. "beta headers are no longer required" | Read |
| Instructions | The top-level field `system`: a string, or a list of text blocks | Read |
| The person's turn | One entry in `messages` with `"role": "user"` | Read |
| Fields that must be in the body | `model`, `max_tokens`, `messages` | Read |
| State | "stateless multi-turn conversations". Nothing of one call is held for the next | Read |
| Largest request | 32 MB | Read |
| Countries served | The United Kingdom is on the list | Read |

The two forms of the key header, in the provider's words:

| Header | What the page says | Where it is used |
|---|---|---|
| `Authorization: Bearer <key>` | "Send it as `Authorization: Bearer <key>` on direct HTTP requests" | The authentication page |
| `x-api-key: <key>` | "Legacy fallback for `Authorization`, still supported" | Every `curl` example on the four pages checked: 27 uses, against none of the other |

Sources: <https://platform.claude.com/docs/en/api/overview>, <https://platform.claude.com/docs/en/api/messages/create>, <https://platform.claude.com/docs/en/manage-claude/authentication>, <https://platform.claude.com/docs/en/api/versioning>, <https://platform.claude.com/docs/en/api/supported-regions>.

### Fields of the body that matter

| Field | Values | Note | Read |
|---|---|---|---|
| `model` | An id from section 6 | Every id is a pinned snapshot. `claude-haiku-4-5` is an alias of `claude-haiku-4-5-20251001` | Read |
| `max_tokens` | A number, 0 or more | "our models may stop _before_ reaching this maximum" | Read |
| `system` | A string, or a list of `{"type": "text", "text": ...}` | "there is no `"system"` role for input messages in the Messages API" | Read |
| `messages` | A list of turns | One `user` turn is enough | Read |
| `output_config.format` | `{"type": "json_schema", "schema": {...}}` | See section 2 | Read |
| `cache_control` | `{"type": "ephemeral"}`, on a block or at the top level | At the top level it marks the last block, which is the person's turn. Put it on the `system` block only. See section 6 | Read |
| `thinking` | `{"type": "disabled"}`, `{"type": "enabled", "budget_tokens": n}`, `{"type": "adaptive"}` | Off on Haiku 4.5 unless asked for. On by default on Sonnet 5, where it can be turned off. Cannot be turned off on Opus 5.5 or Fable 5.1 | Read |
| `temperature`, `top_p`, `top_k` | Do not send | "Returns a 400 error when set to a non-default value on Claude 4.7 and later models" | Read |
| `inference_geo` | `"global"` or `"us"` | A 400 on Haiku 4.5. See section 7 | Read |
| `metadata.user_id` | Do not send | "Anthropic may use this id to help detect abuse." Burro has nothing to put there that is not about a person | Read |
| `stream` | Leave out | One whole answer is wanted | Read |

**Thinking is billed as output.** "You're still charged for the full thinking tokens." On a model where it is on by default, the adapter must send `"thinking": {"type": "disabled"}`, and a test must hold it to that.

## 2. Structured output

| Item | Value | Read |
|---|---|---|
| How to ask | `"output_config": {"format": {"type": "json_schema", "schema": {...}}}` | Read |
| Status | Generally available on the Claude API | Read |
| Older form | `output_format`, with the beta header `structured-outputs-2025-11-13`. Still accepted "for a transition period" | Read |
| Enforced or encouraged | Enforced. "Structured outputs guarantee schema-compliant responses through constrained decoding" | Read |
| How firm the promise is | "While structured outputs guarantee schema compliance in most cases, there are scenarios where the output may not match your schema" | Read |
| Where the answer is | "valid JSON matching your schema, returned in the response's text content block": `content[n].text`, where the block's `type` is `text` | Read |
| A schema it does not accept | "you'll receive a 400 error with details" | Read |
| Models that support it | All four current models, Haiku 4.5 included | Read |
| Cannot be used with | Citations, and a prefilled answer | Read |
| What is kept of the schema | "the JSON schema itself is temporarily cached for up to 24 hours since last use" | Read |

Source: <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>.

### What the schema may hold

| Part of JSON Schema | Accepted | Read |
|---|---|---|
| Types `object`, `array`, `string`, `integer`, `number`, `boolean`, `null` | Yes | Read |
| `enum` | Yes: "strings, numbers, bools, or nulls only" | Read |
| `const` | Yes | Read |
| `anyOf`, `allOf` | Yes, "with limitations". `allOf` with `$ref` is not supported | Read |
| Nullable | Through `anyOf` with `null`, or a list of types such as `["string", "null"]`. Each counts as a union | Read |
| `$ref` | Yes, within the schema. An external `$ref` is not supported | Read |
| Definitions | The page writes "`$ref`, `$def`, and `definitions`". The word `$defs` is nowhere on the page. Burro's schema uses `$defs`, as the standard does. The page also says its Python library takes Pydantic models, which write `$defs`. So it is likely a slip on the page, and it is not confirmed | Read, with a doubt |
| `required` | Yes | Read |
| `additionalProperties` | "must be set to `false` for objects". Any other value is refused | Read |
| `default` | Yes | Read |
| String `format` | `date-time`, `time`, `date`, `duration`, `email`, `hostname`, `uri`, `ipv4`, `ipv6`, `uuid` | Read |
| String `pattern` | Simple patterns. No backreferences, lookahead, lookbehind or word boundaries | Read |
| String `minLength`, `maxLength` | No | Read |
| Number `minimum`, `maximum`, `multipleOf` | No | Read |
| Array `minItems` | Only 0 or 1 | Read |
| Array `maxItems` | No | Read |
| Recursive schemas | No | Read |
| Nesting depth | No number is given. "Deeply nested objects with optional fields compound the complexity" | Read |
| Number of properties, number of enum values | No number is given | Not found |

### Limits on the whole schema

| Limit | Value | Read |
|---|---|---|
| Optional fields, counted across the request | 24. "Each parameter not listed in `required` counts toward this limit" | Read |
| Fields with a union type | 16 | Read |
| Strict tools | 20. Burro sends none | Read |
| Time allowed to compile | 180 seconds | Read |
| Beyond these | A 400 with the message "Schema is too complex for compilation." | Read |

### How Burro's schema fits

`claude.SCHEMA` was printed and counted for this report.

| What the schema uses | Count | Fits |
|---|---|---|
| Keywords | `$defs`, `$ref`, `additionalProperties`, `enum`, `items`, `properties`, `required`, `type` | Seven are listed as supported or used in the page's own examples. `$defs` is the doubt above |
| Objects | 7, each with `additionalProperties: false` | Yes |
| Optional fields | 0 of a limit of 24 | Yes |
| Union types | 0 of a limit of 16 | Yes |
| Enums | 19, holding 103 values, all strings | Yes. No limit is given |
| Arrays | 8, with no `minItems` or `maxItems` | Yes |
| Depth of objects | 2 | Yes |
| Size | 5,798 characters | Yes |

`_plain` in `claude.py` already removes what this provider refuses: `minLength`, `maxLength`, `minimum`, `maximum`, `minItems`, `maxItems`. Nothing more needs to be removed. Lengths and ranges stay checked in code, where they are today.

### What the caller must still do

| Matter | In the provider's words | What Burro does |
|---|---|---|
| The case of an enum value | "Claude may return a value that differs from your schema only in capitalization". "Compare enum values case-insensitively" | `_lower` in `claude.py` already does this |
| The order of fields | "required properties appear first, followed by optional properties" | Nothing. Every field is required |
| The first call with a schema | "there is additional latency while the grammar compiles" | The call may pass Burro's timeout. The rule-based reader answers |
| Later calls | "Compiled grammars are cached for 24 hours from last use" | Nothing |
| Extra tokens | "Claude automatically receives an additional system prompt explaining the expected output format" | Count them in the cost. The number is not given |
| Warming the cache with no output | A request with `max_tokens: 0` "is rejected with an `invalid_request_error`" when `output_config.format` is set | A warm-up, if one is wanted, is a real call with `max_tokens` of 1 or more |

### A refusal, and an answer cut short

| Case | Status | `stop_reason` | The body | Billed | Read |
|---|---|---|---|---|---|
| The model refuses | 200 | `refusal` | "The output may not match your schema because the refusal message takes precedence over schema constraints". `stop_details` names a category | Two pages differ. One says "You'll be billed for the tokens generated". The other says "You are not billed for a refusal that arrives before any output" | Read |
| The answer is cut short | 200 | `max_tokens` | "The output may be incomplete and not match your schema" | Yes | Read |

Both arrive as a success. The adapter must read `stop_reason` before it reads the text.

## 3. What "finished" means

The field is `stop_reason`, at the top level of the answer. "In non-streaming mode this value is always non-null."

| Value | Meaning, in the provider's words | The answer is whole | Read |
|---|---|---|---|
| `end_turn` | "the model reached a natural stopping point" | Yes. The only value that is | Read |
| `max_tokens` | "we exceeded the requested `max_tokens` or the model's maximum" | No | Read |
| `stop_sequence` | "one of your provided custom `stop_sequences` was generated" | No. Burro sends none | Read |
| `tool_use` | "the model invoked one or more tools" | No. Burro sends none | Read |
| `pause_turn` | "we paused a long-running turn" | No | Read |
| `refusal` | "when streaming classifiers intervene to handle potential policy violations" | No | Read |
| `model_context_window_exceeded` | "we exceeded the model's context window" | No | Read |

New values may be added: "Add new variants to enum-like output values". Anything that is not `end_turn` is an error, a value not on this list included.

Sources: <https://platform.claude.com/docs/en/api/messages/create>, <https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons>, <https://platform.claude.com/docs/en/api/versioning>.

## 4. Usage

The object is `usage`, at the top level of the answer.

| Field | Counts | Type | Read |
|---|---|---|---|
| `input_tokens` | "Number of input tokens which were not read from or used to create a cache" | number | Read |
| `cache_creation_input_tokens` | "The number of input tokens used to create the cache entry" | number or null | Read |
| `cache_read_input_tokens` | "The number of input tokens read from the cache" | number or null | Read |
| `output_tokens` | "The number of output tokens which were used". It includes thinking | number | Read |
| `output_tokens_details.thinking_tokens` | The part of the output that was thinking | number, in an object that may be null | Read |
| `inference_geo` | "The geographic region where inference was performed for this request" | string or null | Read |
| `service_tier` | `standard`, `priority` or `batch` | string or null | Read |

"Total input tokens in a request is the summation of `input_tokens`, `cache_creation_input_tokens`, and `cache_read_input_tokens`."

Two warnings from the page. The counts "will not match one-to-one with the exact visible content of an API request or response". And "`output_tokens` will be non-zero, even for an empty string response".

| Burro's field | Take it from | Why |
|---|---|---|
| `input_tokens` | `input_tokens` + `cache_creation_input_tokens` | Both were sent and not read from a cache. So the field means the same in every adapter |
| `cache_read_tokens` | `cache_read_input_tokens` | |
| `output_tokens` | `output_tokens` | |

A cache field that is `null` means no cache was used, and is read as 0. A missing `input_tokens` or `output_tokens` is an error, not a zero.

Sources: <https://platform.claude.com/docs/en/api/messages/create>, <https://platform.claude.com/docs/en/build-with-claude/prompt-caching>.

## 5. Errors

An error has an HTTP status of 4xx or 5xx and a body of one shape: `{"type": "error", "error": {"type": ..., "message": ...}, "request_id": ...}`. "The API always returns errors as JSON". One exception is written down: a 413 can come from the network edge "before the request reaches the API servers".

| What happens | Status | `error.type` | Becomes | Read |
|---|---|---|---|---|
| No answer within Burro's own deadline | none | none | timed out | Burro's own |
| The provider gave up | 504 | `timeout_error` | timed out | Read |
| A rate limit: requests or tokens a minute | 429, with a `retry-after` header | `rate_limit_error` | capped | Read |
| A sharp rise in use | 429 | `rate_limit_error` | capped | Read |
| The tier's monthly spend cap | 429, with no `retry-after`. `error.details.error_code` is `enforced_spend_limit_reached` | `rate_limit_error` | capped | Read |
| A spend limit the customer set | **400**. The message begins "You have reached your specified API usage limits", or "You have reached your specified workspace API usage limits" | `invalid_request_error` | capped | Read |
| A fault with billing or payment | 402 | `billing_error` | capped | Read. The mapping is a judgement: whoever reads the log must look at the bill, not at the code |
| A bad request | 400 | `invalid_request_error` | error | Read |
| A schema that is not accepted, or is too complex | 400 | `invalid_request_error` | error | Read |
| A key that is wrong, revoked or expired | 401 | `authentication_error` | error | Read |
| No leave to use the model or the workspace | 403 | `permission_error` | error | Read |
| Not found | 404 | `not_found_error` | error | Read |
| A conflict | 409 | `conflict_error` | error | Read |
| The request is too large | 413 | `request_too_large` | error | Read |
| A fault inside the provider | 500 | `api_error` | error | Read |
| The service is overloaded | 529 | `overloaded_error` | error | Read |
| A safety block | 200, with `stop_reason` of `refusal` | none | error | Read |
| An answer cut short | 200, with `stop_reason` of `max_tokens` or `model_context_window_exceeded` | none | error | Read |
| Any other `stop_reason` but `end_turn` | 200 | none | error | Read |
| A body that is not JSON, holds no text block, or is over the size Burro allows | any | none | error | Burro's own |
| A redirect | 3xx | none | error | Burro's own. None is documented |
| A model that has been retired | "Requests to retired models will fail." The status is not given | not given | error | Read |

Sources: <https://platform.claude.com/docs/en/api/errors>, <https://platform.claude.com/docs/en/api/rate-limits>, <https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback>, <https://platform.claude.com/docs/en/about-claude/model-deprecations>.

### Four things the builder must know

| Matter | What the page says | What to do |
|---|---|---|
| A safety block is a success | "Safety classifiers return this stop reason as a normal HTTP 200 response, not an error." | Read `stop_reason` first |
| A spend limit can be a 400 | See the table | Tell it from a bad request by how the message begins. Compare the start of the message and keep none of it. If that is thought too brittle, treat every 400 as an error: the person is answered either way |
| The message may change | "Change conditions for specific error types" is allowed within a version | Decide on the status and `error.type`. Use the message for the one case above and nothing else |
| The body of an error may repeat the request | Not said. Assumed | Never log it, never put it in an exception |

### The limits on a new account

| Limit | Start tier | Read |
|---|---|---|
| Requests a minute, Haiku 4.5 or Sonnet 5 | 1,000 | Read |
| Input tokens a minute, not counting what is read from a cache | 2,000,000 | Read |
| Output tokens a minute | 400,000 | Read |
| Spend a month | $500. Build: $1,000. Scale: $200,000 | Read |
| When the monthly cap is reached | "API usage pauses until 00:00 UTC on the first day of the next month, unless you request a higher limit sooner" | Read |
| A brand new organisation | "may start in the Evaluation tier, with limits below the standard limits shown on this page". The numbers are not given | Read |
| A limit of your own | Can be set lower than the cap. "You can't set limits on the default Workspace" | Read |

## 6. Models

### Offered today

| Model | Id | Context | Most output | Thinking | Retirement, "not sooner than" | Structured output | Read |
|---|---|---|---|---|---|---|---|
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | 200K tokens | 64K tokens | Off unless asked for | 15 October 2026 | Yes | Read |
| Claude Sonnet 5 | `claude-sonnet-5` | 1M tokens | 128K tokens | On by default. Can be turned off | 30 June 2027 | Yes | Read |
| Claude Opus 5.5 | `claude-opus-5-5` | 1M tokens | 128K tokens | Always on | 22 September 2027 | Yes | Read |
| Claude Fable 5.1 | `claude-fable-5-1` | 1M tokens | 128K tokens | Always on | 1 September 2027 | Yes | Read |

Older models are still served: Fable 5, Opus 5, Opus 4.8, 4.7, 4.6 and 4.5, Sonnet 4.6 and 4.5. Two more, Mythos 5 and 5.1, are open to approved partners only. None is smaller or cheaper than Haiku 4.5.

Sources: <https://platform.claude.com/docs/en/about-claude/models/overview>, <https://platform.claude.com/docs/en/models/haiku-4-5/overview>, <https://platform.claude.com/docs/en/about-claude/model-deprecations>.

### Prices, in US dollars for a million tokens

| Model | In | Out | Read from cache | Written to cache, 5 minutes | Written to cache, 1 hour | Read |
|---|---|---|---|---|---|---|
| Claude Haiku 4.5 | $1 | $5 | $0.10 | $1.25 | $2 | Read |
| Claude Sonnet 5 | $2 | $10 | $0.20 | $2.50 | $4 | Read |
| Claude Opus 5.5 | $4 | $20 | $0.20 | $5 | $8 | Read |
| Claude Fable 5.1 | $10 | $50 | $0.25 | $12.50 | $20 | Read |

Every figure but the one-hour write was read on two pages, and the two agree. The one-hour write is on the developer page only.

| Other charge | Value | Read |
|---|---|---|
| Inference in the US only | 1.1 times every price. Not offered on Haiku 4.5 | Read |
| Batches | Half price. Not for a person who is waiting | Read |
| A change of price | "effective the earlier of 30 days after the updates are posted" | Read |
| A free tier | None. "New users receive a small amount of free credits to test the API." | Read |

Sources: <https://platform.claude.com/docs/en/about-claude/pricing>, <https://claude.com/pricing>, <https://www.anthropic.com/legal/commercial-terms>.

### The cache

| Point | In the provider's words | Read |
|---|---|---|
| How it is asked for | `cache_control` on a block, or at the top level | Read |
| What is cached | "the entire prompt: `tools`, `system`, and `messages` (in that order), up to and including the block designated with `cache_control`" | Read |
| How long it lasts | "By default, the cache has a 5-minute lifetime. The cache is refreshed for no additional cost each time the cached content is used." One hour at a higher price | Read |
| Smallest prefix that is cached, Haiku 4.5 | 4,096 tokens | Read |
| Smallest prefix that is cached, Sonnet 5 | 1,024 tokens | Read |
| Smallest prefix that is cached, Opus 5.5 and Fable 5.1 | 512 tokens | Read |
| A prefix that is too short | "will be processed without caching, and no error is returned" | Read |
| How to tell | "if both `cache_creation_input_tokens` and `cache_read_input_tokens` are 0, the prompt was not cached" | Read |
| What breaks it | A change to `output_config.format` "will invalidate any prompt cache for that conversation thread" | Read |
| Who shares a cache | Nobody outside the workspace. "Caches are isolated between organizations" | Read |
| What is held | "KV cache representations and cryptographic hashes of cached content are held in memory only and are not stored at rest" | Read |

**On the smallest model the cache will not apply.** Burro's instructions are 8,878 characters, about 2,200 tokens at four characters a token. That is under 4,096. The mark that `claude_sdk.py` puts on the instructions is accepted and does nothing on Haiku 4.5. It would work on Sonnet 5.

### The smallest model fit for the job

`claude-haiku-4-5-20251001`. It is the smallest and the cheapest. It takes a `system` field and a short user turn. It supports structured output. Its context is over 60 times what the job needs. Thinking is off unless asked for, so nothing has to be turned off. Whether it reads Burro's sentences well is not known until the golden queries are run.

Its weak point is its date. It may not be retired before 15 October 2026, which is 22 days away. It is listed as "Active", no notice has been given, and "at least 60 days' notice" is promised. So it runs until late November 2026 at the least, and the day a notice comes the clock starts. The next model up is `claude-sonnet-5`, at twice the price.

### 1,000 searches, at 3,000 tokens in and 300 out

"Cached" assumes 2,700 of the 3,000 tokens are the fixed instructions and are read from the cache, and 300 are not.

| Model | Not cached | Cached | Can the cache apply at this length |
|---|---|---|---|
| `claude-haiku-4-5-20251001` | $4.50 | $2.07 | No. 2,700 is under 4,096 |
| `claude-sonnet-5` | $9.00 | $4.14 | Yes |
| `claude-opus-5-5` | $18.00 | $7.74 | Yes |

The sums, for Haiku 4.5: not cached, 3.0 x 1 + 0.3 x 5 = 4.50. Cached, 2.7 x 0.10 + 0.3 x 1 + 0.3 x 5 = 2.07.

| What would move the figure | By how much |
|---|---|
| Sonnet 5 counts tokens differently. The newer tokenizer "produces approximately 30% more tokens for the same text" | Sonnet 5 becomes $11.70 not cached and $5.38 cached |
| The instructions are made longer than 4,096 tokens so that Haiku 4.5 caches them | $2.21 while the cache is warm. $6.92 if every call is more than five minutes after the last, because each one pays to write the cache |
| Thinking left on, on Sonnet 5 | Output grows. It is billed at the output price |
| The words that structured output adds to the instructions | A little more input. The number is not given |
| The first call with a schema | More time, not more money |

Plan on Haiku 4.5, not cached: **$4.50 for 1,000 searches**. If the model must change, plan on Sonnet 5 with the newer count and no cache: $11.70. Token counts are estimates until they are measured. At $4.50, the Start tier's cap of $500 a month is about 111,000 searches.

## 7. What happens to a person's text

### Who answers for the text

| Point | In the provider's words | Read |
|---|---|---|
| Which company, for a UK customer | "“Anthropic” means Anthropic Ireland, Limited if Customer resides in the European Economic Area (“EEA”), Switzerland or UK" | Read |
| Who is the controller | "Customer is the controller and Anthropic is Customer’s processor" | Read |
| What the processor may do | "Anthropic will only process Customer Personal Data to provide or maintain the Services, and in compliance with Customer’s documented instructions" | Read |
| Who these terms are for | "Services under these Terms are not for consumer use." The customer is a business. It may use the service "to power products and services Customer makes available to its own customers and end users" | Read |
| Whose privacy policy applies to a person using Burro | Burro's. "the Privacy Policy does not apply where Anthropic acts as a data processor" | Read |

Sources: <https://www.anthropic.com/legal/commercial-terms> (effective 17 June 2025), <https://www.anthropic.com/legal/data-processing-addendum> (effective 24 February 2025), <https://privacy.claude.com/en/articles/7996885-how-do-you-use-personal-data-in-model-training>.

### The questions

| Question | In the provider's words | Address | Read |
|---|---|---|---|
| How long is it kept | "For Anthropic API users, we automatically delete inputs and outputs on our backend within 30 days of receipt or generation, except" where a service keeps it longer under your control, where agreed otherwise, to enforce the Usage Policy, or to comply with the law | <https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data> | Read |
| And if it is flagged | "We retain inputs and outputs for up to 2 years and trust and safety classification scores for up to 7 years if your chat is flagged by our automated trust and safety systems as violating our Usage Policy." | The same | Read |
| Can one call be deleted | "For paid API customers, we do not support ad hoc deletion." | <https://privacy.claude.com/en/articles/7996875-can-you-delete-data-that-i-sent-via-api> | Read |
| Is it used to train models, paid | "Anthropic may not train models on Customer Content from Services." | <https://www.anthropic.com/legal/commercial-terms> | Read |
| The same, in the privacy centre | "By default, we will not use your inputs or outputs from our commercial products (e.g. Claude for Work, Anthropic API, Claude Gov, etc.) to train our models." | <https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training> | Read |
| Is it used to train models, free tier | There is no free tier of the API. Free credit is spent under the same terms | <https://platform.claude.com/docs/en/about-claude/pricing>, <https://www.anthropic.com/legal/credit-terms> | Read |
| Where is it processed | "By default, we may route customer traffic to select countries in the US, Europe, Asia and Australia, unless otherwise agreed upon or at your instructions." | <https://privacy.claude.com/en/articles/7996890-where-are-your-servers-located-do-you-host-your-models-on-eu-servers> | Read |
| Where is it stored | "Note that data is stored in the US." | The same | Read |
| Where else | "We may also process data for internal processes (such as safety-related review, product support, or incident response) in countries where we or our affiliates operate." | The same | Read |
| Can a region be chosen | "Inference geo: Only `"us"` and `"global"` are available." "Workspace geo: Only `"us"` is currently available." | <https://platform.claude.com/docs/en/manage-claude/data-residency> | Read |
| On the smallest model | "Requests with `inference_geo` on Claude Opus 4.5, Claude Sonnet 4.5, Claude Haiku 4.5, or earlier models return a 400 error." | The same | Read |
| Can zero retention be had | "Under a ZDR arrangement, Anthropic does not store customer prompts or responses at rest after the API response is returned. To request ZDR for your organization, contact the Anthropic sales team." | <https://platform.claude.com/docs/en/manage-claude/api-and-data-retention> | Read |
| Who can have it | "Some Claude Platform (Claude API) and Claude Code for Enterprise customers, subject to Anthropic’s approval" | <https://privacy.claude.com/en/articles/8956058-i-have-a-zero-data-retention-agreement-with-anthropic-what-products-does-it-apply-to> | Read |
| What it does not stop | "if a chat or session is flagged, Anthropic may retain inputs and outputs for up to 2 years". "Anthropic still retains User Safety classifier results" | The two pages above | Read |
| Is a data processing agreement offered | "Anthropic’s DPA with Standard Contractual Clauses (SCCs) is automatically incorporated into our Commercial Terms of Service" | <https://privacy.claude.com/en/articles/7996862-how-do-i-view-and-sign-your-data-processing-addendum-dpa> | Read |
| How is it accepted | "When you accept Anthropic’s Commercial Terms of Service, you also accept our DPA." | The same | Read |
| Who are the sub-processors | "Anthropic’s list of subprocessors is available at https://www.anthropic.com/subprocessors." | <https://www.anthropic.com/legal/data-processing-addendum> | The sentence was read. The list was not: see "What was not read" |
| A breach | "Anthropic will notify Customer in writing without undue delay, but in any event within 48 hours" | The same | Read |
| At the end of the contract | "Within thirty (30) days of the date of termination or expiration of the Agreement, Anthropic will ... delete all copies of Customer Data", with three exceptions | The same | Read |

### Two pages that do not say the same thing

| Page | What it says |
|---|---|
| The developer page on retention | "Conversation content (your prompts and Claude's outputs) is not retained by default; the exception is Covered Models, which require 30-day retention." |
| The privacy centre, dated 1 July 2026 | "we automatically delete inputs and outputs on our backend within 30 days of receipt or generation" |

The developer page points to the privacy centre for "Anthropic's standard retention policies outside these arrangements". So the privacy centre is the one to rely on. A privacy notice must say up to 30 days, and up to two years if flagged. It must not say the text is not kept.

"Covered Models" are Fable 5, Fable 5.1, Mythos 5 and Mythos 5.1. They keep text for at least 30 days whatever else is agreed. Haiku 4.5 and Sonnet 5 are not among them.

### What the customer can switch on, and should not

| Switch | What it does | In the provider's words | Read |
|---|---|---|---|
| The Development Partner Program | Lets the provider train on what is sent | "If Customer enables Development Partner Mode, Anthropic may use the data that Customer submits to the Services (e.g., Customer Content) in connection with Anthropic’s products and services, including to train models." | Read |
| Feedback, such as a thumbs up or down in the console | Keeps the whole exchange for five years, and allows training on it | "we will store the entire related conversation ... for up to 5 years" | Read |
| The console and its playground | Not covered by zero retention | "Any usage in the Claude Console, including playground" | Read |

Leave the first off. Never paste a real person's sentence into the console.

### UK and EU law

| Point | In the provider's words | Read |
|---|---|---|
| EU transfers | "the terms of the SCCs Module Two (controller to processor) and/or Module Three (processor to processor) ... are hereby incorporated by reference and will be deemed to have been executed by the parties" | Read |
| UK transfers | "This UK Addendum will apply to any processing of Customer Personal Data that is subject to the UK GDPR or both the UK GDPR and the GDPR." It is "version B.1.0 issued by the UK Information Commissioner" | Read |
| Help with a transfer assessment | "Anthropic will, upon Customer’s request, provide information to Customer which is reasonably necessary for Customer to complete a transfer impact assessment" | Read |
| Help with an impact assessment | "Anthropic will cooperate with and provide reasonable assistance to Customer for: (a) Customer’s performance of any data protection impact assessment" | Read |
| Requests from a person | "Anthropic will forward to Customer promptly any Data Subject Request received by Anthropic" | Read |
| Law and courts, for a UK customer | "the Laws of Ireland", and "the courts of Ireland". Disputes go to "a sole arbitrator in Dublin, Ireland" | Read |
| Special category data | In the description of the processing: "Special categories of personal data (if applicable): None." | Read |
| Personal data in general | "we encourage our users not to use our products and services to process personal data" | Read, on a page about training |
| What the customer promises | "Customer further represents and warrants that it has all rights and permissions required to submit Inputs to the Services." | Read |
| What may not be done with the service | "Misuse, collect, solicit, or gain access without permission to private information such as non-public contact details, health data, biometric or neural data" | Read |
| EU residency | Through Amazon Bedrock, Google Cloud or Microsoft Foundry only, at a 10% premium. On Bedrock and Google Cloud "the cloud provider is the data processor" | Read |

Sources: <https://www.anthropic.com/legal/data-processing-addendum>, <https://www.anthropic.com/legal/commercial-terms>, <https://www.anthropic.com/legal/aup>, <https://claude.com/regional-compliance>, <https://platform.claude.com/docs/en/manage-claude/api-and-data-retention>.

### What a UK company must do first

The provider's documents put all of this on the customer: "Each party will comply with all laws applicable to the provision (for Anthropic) and use (for Customer) of the Services, including any applicable data privacy laws."

The steps below are not from the provider. They are the usual steps under UK law, written from general knowledge. The regulator's pages were not read, so none of this was checked at a source. It is not legal advice.

| Step | Why it applies to Burro | Read |
|---|---|---|
| Accept the Commercial Terms as a business, with the power to bind it | The terms are not for consumer use, and the agreement comes with them | Read, from the provider |
| Write a data protection impact assessment before the first real sentence is sent | A sentence can hold health, religion or sexuality, and it is sent to a model | Not read |
| Find a lawful basis, and a second condition for special category data | The likely one is explicit consent, asked for before the sentence is sent | Not read |
| Settle the gap in the agreement | The agreement describes the processing as holding no special category data. Burro's may. Ask the provider in writing, or keep such data out | Read, from the provider |
| Assess the transfer | The contract is with a company in Ireland. The text is then processed and stored in the United States and other countries | Not read |
| Name the provider, the countries and the periods in the privacy notice | Section 7 has the words | Not read |
| Tell people what to leave out | The cheapest safeguard, and the one the provider's own page points towards | Not read |

## 8. Terms that bind a product like this

| Matter | In the provider's words | What it means for Burro | Read |
|---|---|---|---|
| Age, in the terms Burro would accept | No age is given for a customer's end users | Nothing is asked of Burro by these terms | Not found |
| Age, in the terms for the provider's own apps | "You must be at least 18 years old to use the Services." | These are not Burro's terms. They show where the provider draws the line for itself | Read |
| Who is a minor | "any individual under the age of 18 years old, regardless of jurisdiction" | | Read |
| Products that serve minors | "must comply with the additional guidelines", which name age checks, filtering, monitoring and disclosure | Applies only if Burro is offered to under-18s | Read |
| Telling people a model is used | "All consumer-facing chatbots, including any external-facing or interactive AI agent, must disclose to users that they are interacting with AI rather than a human. This disclosure must be provided at a minimum at the beginning of each chat session." | A box that a model reads is close enough to this to say so, at the start of each visit | Read |
| Telling people the answer may be wrong | "Customer acknowledges, and must notify its Users, that factual assertions in Outputs should not be relied upon without independently checking their accuracy" | The reader's output is edits, not facts. The notice is still owed | Read |
| Housing | High risk: "decisions regarding eligibility for housing, including leases and home loans" | Burro ranks places. It decides nothing about who may rent or buy. On these words it is outside | Read |
| If a use is high risk | "a qualified professional in that field must review the content or decision prior to dissemination or finalization", and AI use must be disclosed | Would apply if Burro ever judged a person's eligibility. It must not | Read |
| Discrimination | Do not "Promote discriminatory practices or behaviors against individuals or groups on the basis of one or more protected attributes" | Agrees with ADR 0006 | Read |
| Scoring people | Do not "assign scores or ratings to individuals based on an assessment of their trustworthiness or social behavior without notification or their consent" | Burro scores places, never people | Read |
| Passing for a person | Do not use results "to convince a natural person that they are communicating with a natural person when they are not" | | Read |
| Telling people which provider is used | Nothing requires it and nothing forbids it | UK law asks that recipients be named. That is not from the provider | Not found |
| The provider naming Burro | "Anthropic may use Customer’s name and logo to publicly identify Customer as a customer of the Services; provided that Customer may opt-out via this request form." | Opt out if that is not wanted | Read |
| Building a rival | Customer may not "access the Services to build a competing product or service, including to train competing AI models or resell the Services" | Do not train a model on the answers | Read |
| Who owns the answer | Customer "owns its Outputs" | | Read |
| A change to the terms | "effective 30 days after the updates are posted" | Re-read the terms on a schedule | Read |
| Being cut off | The provider "may throttle, suspend, or terminate your access" on a breach of the Usage Policy | The rule-based reader must always be able to answer | Read |
| Claims about what was sent | The customer defends the provider against claims "related to Customer’s or its Users’ (a) Inputs" | | Read |

Sources: <https://www.anthropic.com/legal/aup> (effective 15 September 2025), <https://www.anthropic.com/legal/commercial-terms>, <https://www.anthropic.com/legal/consumer-terms>, <https://support.claude.com/en/articles/9307344-responsible-use-of-anthropic-s-models-guidelines-for-organizations-serving-minors>.

## 9. Examples to test against

### A request, copied

From <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>.

```bash
curl https://api.anthropic.com/v1/messages \
  -H "content-type: application/json" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-opus-5-5",
    "max_tokens": 1024,
    "messages": [
      {
        "role": "user",
        "content": "Extract the key information from this email: John Smith (john@example.com) is interested in our Enterprise plan and wants to schedule a demo for next Tuesday at 2pm."
      }
    ],
    "output_config": {
      "format": {
        "type": "json_schema",
        "schema": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"},
            "plan_interest": {"type": "string"},
            "demo_requested": {"type": "boolean"}
          },
          "required": ["name", "email", "plan_interest", "demo_requested"],
          "additionalProperties": false
        }
      }
    }
  }'
```

What the page shows of the answer is the text of the text block, and no more:

```json
{
  "name": "John Smith",
  "email": "john@example.com",
  "plan_interest": "Enterprise",
  "demo_requested": true
}
```

### A body with instructions and a cache mark, copied

From <https://platform.claude.com/docs/en/build-with-claude/prompt-caching>. The top-level `cache_control` in it is the one Burro must leave out.

```json
{
  "model": "claude-opus-5-5",
  "max_tokens": 1024,
  "cache_control": { "type": "ephemeral" },
  "system": [
    {
      "type": "text",
      "text": "You are a helpful assistant.",
      "cache_control": { "type": "ephemeral" }
    }
  ],
  "messages": [{ "role": "user", "content": "What are the key terms?" }]
}
```

### A whole answer, copied

From <https://platform.claude.com/docs/en/build-with-claude/working-with-messages>.

```json
{
  "id": "msg_018gCsTGsXkYJVqYPxTgDHBU",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Sure, I'd be happy to provide..."
    }
  ],
  "model": "claude-opus-5-5",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 30,
    "output_tokens": 309
  }
}
```

This answer has no cache fields. The adapter must take a missing cache field as none.

### Usage with a cache, copied

From <https://platform.claude.com/docs/en/api/messages/create>. It is the `usage` object of the reference example.

```json
{
  "cache_creation": {
    "ephemeral_1h_input_tokens": 0,
    "ephemeral_5m_input_tokens": 0
  },
  "cache_creation_input_tokens": 2051,
  "cache_read_input_tokens": 2051,
  "inference_geo": "global",
  "input_tokens": 2095,
  "output_tokens": 503,
  "output_tokens_details": {
    "thinking_tokens": 0
  },
  "server_tool_use": {
    "web_fetch_requests": 2,
    "web_search_requests": 0
  },
  "service_tier": "standard"
}
```

The reference example is generated, and the rest of it does not hang together: it shows `stop_details` for a refusal beside a `stop_reason` of `end_turn`. Use its `usage` object and not the whole.

### A refusal, copied

From <https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback>. The status is 200.

```json
{
  "id": "msg_01XFUDYJgAACzvnptvVoYEL",
  "type": "message",
  "role": "assistant",
  "model": "claude-fable-5",
  "content": [],
  "stop_reason": "refusal",
  "stop_details": {
    "type": "refusal",
    "category": "cyber",
    "explanation": "This request was declined because it could enable cyber harm."
  },
  "usage": {
    "input_tokens": 412,
    "output_tokens": 0
  }
}
```

### An error, copied

From <https://platform.claude.com/docs/en/api/errors>. The status is 404.

```json
{
  "type": "error",
  "error": {
    "type": "not_found_error",
    "message": "The requested resource could not be found."
  },
  "request_id": "req_011CSHoEeqs5C35K2UUqR7Fy"
}
```

### The monthly cap, copied

From <https://platform.claude.com/docs/en/api/rate-limits>. The status is 429, with no `retry-after` header.

```json
{
  "type": "error",
  "error": {
    "type": "rate_limit_error",
    "message": "You have reached your API usage limits: your organization has crossed its monthly API usage threshold, set based on your organization's API tier. You will regain access on 2026-09-01 at 00:00 UTC.",
    "details": { "error_code": "enforced_spend_limit_reached" }
  },
  "request_id": "req_018EeWyXxfu5pfWkrYcMdjWG"
}
```

### Overloaded, copied

From <https://platform.claude.com/docs/en/build-with-claude/streaming>. The page shows it as an event in a stream, and says it "would normally correspond to an HTTP 529 in a non-streaming context". The body of a 529 outside a stream is not shown on any page read.

```json
{"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}}
```

### What Burro would send, not copied and not tested

```json
{
  "model": "claude-haiku-4-5-20251001",
  "max_tokens": 2048,
  "system": [
    {
      "type": "text",
      "text": "<claude.SYSTEM>",
      "cache_control": { "type": "ephemeral" }
    }
  ],
  "messages": [
    { "role": "user", "content": "{\"request\": \"<what the person typed>\", \"spec\": {}}" }
  ],
  "output_config": {
    "format": { "type": "json_schema", "schema": "<claude.SCHEMA, as an object>" }
  }
}
```

Headers: `x-api-key`, `anthropic-version: 2023-06-01`, `content-type: application/json`. On Sonnet 5, add `"thinking": {"type": "disabled"}`.

## For the builder

| Matter | Do this | Why |
|---|---|---|
| Address | `https://api.anthropic.com/v1/messages`, a constant in code | Decision 1 |
| Key header | `x-api-key`, with the name held in one constant | Every example copied above uses it. The provider calls it legacy and still supported, and names `Authorization: Bearer` first, so the change is one line if it is ever needed |
| Version header | `anthropic-version: 2023-06-01`, always | "you must send an `anthropic-version` request header" |
| The key | One that is tied to one workspace, and not the default workspace | No workspace header is then needed, and a spend limit can be set |
| Instructions | A list of one text block, with `cache_control` on it | The mark does nothing on Haiku 4.5 and works on Sonnet 5 |
| Cache mark at the top level | Never | It would mark the person's turn, and their words would be held in the cache |
| Thinking | Send `{"type": "disabled"}` where the model has it on by default. Send nothing on Haiku 4.5 | It is billed as output, and it takes time |
| `metadata.user_id`, `temperature`, `inference_geo` | Never send them | See section 1 |
| The schema | Send `claude.SCHEMA` as it is. If the first live call refuses `$defs`, write each reference out in full and send no definitions | The one keyword in doubt |
| Finished | `stop_reason` equal to `end_turn`, read before the text | A refusal and a cut-off answer are both a 200 |
| The text | The `text` of the first block in `content` whose `type` is `text` | Other kinds of block can come first |
| Usage | `input_tokens` is the provider's `input_tokens` plus `cache_creation_input_tokens`. `cache_read_tokens` is `cache_read_input_tokens`. A cache field that is null or missing is 0 | So the three mean the same in every adapter. `claude_sdk.py` leaves out the tokens written to the cache |
| Missing usage | A missing or negative `input_tokens` or `output_tokens` is an error, not a zero | Rule 7 |
| Errors | Decide on the status and `error.type`. Read `error.details.error_code` for the cap. Compare the start of `error.message` for the customer's own limit, and keep none of it | A body can repeat the request |
| A 402 | Capped | `claude_sdk.py` does the same. The provider now answers a spend limit with a 400 or a 429, so a 402 is a fault with payment |
| Deadline | One clock for the whole call | Decision 5 |
| Body | Read to a fixed size and refuse beyond it | No largest answer is documented. At 2,048 tokens out, 256 KB is far more than enough |
| Redirects | Refuse every 3xx | Decision 4 |
| Retries | None. Do not act on `retry-after` | Decision 4 |
| Model id | Check it against the pattern already in `calls.py`: lower-case letters, digits, dots and hyphens, up to 64 | Decision 5. Every id on this page fits |
| The `request-id` header | Do not log it | It names one person's call at the provider. Nothing on the list of what may be logged holds it |

## What Burro must tell a person

True of the paid service. There is no free tier of the API, and credit the provider gives away is spent under the same terms. The provider's own free chat app is a different product under different terms, and Burro does not use it.

> When you type a sentence, Burro sends your words to Anthropic, the company that makes the Claude model, and its computers in the United States and other countries turn them into search settings. Anthropic says it does not use them to train its models and deletes them within 30 days, or keeps them for up to two years if its safety systems flag them, so leave out your health, your religion and anything else you would not want kept.

The provider may also keep text for longer where the law requires it. The full privacy notice must say so, and must name the 7 years for which safety scores are kept.

## What was not read

| What | Standing | What was relied on |
|---|---|---|
| The Trust Center, `https://trust.anthropic.com/` | Not read | Nothing. The provider's security reports were not read |
| The list of sub-processors, `https://www.anthropic.com/subprocessors` | Not read. It leads to the Trust Center | The privacy centre's sentence on countries. Which companies handle the text, and where, is not known |
| The UK regulator's guidance, `https://ico.org.uk/` | Not read | General knowledge. The steps in "What a UK company must do first" are not verified |
| The console: limits, billing, privacy controls | Not read. They need an account | The developer pages that describe them |
| Whether `$defs` is accepted | The page writes `$def` | Nothing. The first live call will say |
| The status and body for a retired model | Not given | Nothing. It becomes an error whatever it is |
| The body of a 529 outside a stream | Not shown | The shape every other error has |
| Whether the body of an error can repeat the request | Not said | Nothing. It is treated as if it can |
| How many tokens structured output adds | Not given | Nothing |
| The limits of the Evaluation tier | Not given | Nothing |
| The number of tokens in Burro's instructions | Counting needs a key | Four characters a token |
| How long the first call with a schema takes | Not given | Nothing |
| Decisions of regulators about this provider | Not searched for | Nothing |
| The live service | No call was made | Examples from the documents |

## For the founder to decide

1. **Whether a sentence that may hold health, religion or sexuality may go to this provider as the agreement stands.** The agreement describes the processing as holding no special category data. Three ways forward: ask the provider in writing whether the agreement covers it; ask each person for explicit consent and tell them what to leave out; or both. It costs an email and a line on the screen. Until it is settled, the adapter can be built and used on made-up sentences.
2. **Whether processing in the United States and other countries is acceptable.** This API has no UK or EU region, and the smallest model takes no region at all. The contract is with a company in Ireland and carries the UK Addendum. If a region in Europe is a must, the routes are Google Cloud or Amazon Bedrock. Each is a different contract with a different processor, a different way of signing a request, and a 10% premium. Neither was researched here.
3. **Which model.** Haiku 4.5 is the cheapest at $4.50 for 1,000 searches. Its promised life ends on 15 October 2026, and from then it runs only until 60 days after a notice, which may come on any day. Sonnet 5 is promised until 30 June 2027 and costs $9.00 to $11.70. The recommendation is Haiku 4.5 in configuration, the golden queries run on both, and the budget planned on Sonnet 5.
4. **Whether to ask for zero retention.** It is by arrangement with the sales team, one organisation at a time, and subject to approval. Whether a small customer is granted it is not said. Flagged text is kept for up to two years even then. It costs an email.
5. **Whether to make the instructions longer so that the smallest model caches them.** At 4,096 tokens and a warm cache the cost falls from $4.50 to about $2.21. With fewer than one call every five minutes it rises to about $6.92. At launch, traffic is likely to be thin. The recommendation is to leave them as they are and measure.
6. **The spend limit.** A new account is capped at $500 a month or less, and at the cap the service is refused until the first of the next month. Set a lower limit on a workspace of Burro's own, and decide who is told when it is near.
7. **Where and how to say a model reads the sentence.** The Usage Policy asks for it at the start of each session. The Commercial Terms ask that people are told not to rely on what a model asserts.
8. **Whether Burro is offered to people under 18.** If it is, the provider's guidelines for products serving minors apply. If it is not, say so in Burro's own terms.
9. **Whether the provider may name Burro as a customer.** It may, unless Burro opts out.
10. **Who accepts the terms.** They bind a business, and whoever accepts must have the power to bind it. `BURRO_MODEL_TERMS_ACCEPTED` should name this provider only after that person has read the Commercial Terms, the agreement on data processing and the Usage Policy at the addresses above.
