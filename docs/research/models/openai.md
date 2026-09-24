# OpenAI, from its own documents

Read on 23 September 2026. A dated snapshot: model names, prices and terms change often. Re-check before relying on a figure.

This is one of four reports, one a provider. The same nine questions were put to each.

## How this was read

| Point | What it means for you |
|---|---|
| The developer pages were downloaded as text from `developers.openai.com`, most of them by adding `.md` to the address | Quotes and examples from those pages are copied, not summarised |
| The API reference and the pricing page were downloaded as web pages and the tags were stripped | The words and numbers are the provider's. Prices for older models sit in the page's data, behind a button, and were read from there |
| The legal and privacy pages were downloaded from `openai.com` and the tags were stripped | The words are the provider's. Line breaks and list marks are lost. Curly quotation marks are written straight here. Check the wording at the address given before it goes into a privacy notice or a contract |
| Five of the provider's hosts were not read | See "What was not read". Claims that rest on them are marked |
| No key, and no call to the provider | Nothing here was tested against the live service |
| This report and the three beside it were held to the same questions | Every claim is tied to a page, so it can be checked |
| Nothing here is legal advice | |

"Read" in a table below means read at the provider's own address on the day. "Not read" means it is an inference, a recollection, or the page did not say.

## In short

| Question | Answer | Read |
|---|---|---|
| Can it do the job | Yes. One POST, a key in a header, JSON back | Read |
| Which API | Responses, `POST /v1/responses`. "Responses is recommended for all new projects." Chat Completions still works | Read |
| Is the schema enforced | Yes, with `"strict": true`. Two written exceptions: a refusal, and an answer cut short | Read |
| Does Burro's schema fit | On paper, yes. It uses eight keywords, all on the supported list. Every object is closed and every field is required | Read, not tested |
| Smallest model fit for the job | `gpt-6-luna`, with reasoning switched off | Read |
| Its retirement | None listed. Six months' notice is promised for a generally available model | Read |
| Its weakness | It has no dated version. The name `gpt-6-luna` is the only one offered, so what it points to may change | Read |
| Cost of 1,000 searches | $0.45 not cached. $0.21 with the instructions read from a warm cache. $0.52 if every call finds the cache cold | Worked out from prices that were read |
| Where the text is processed | No region is promised by default. The party that receives UK data is OpenAI OpCo, LLC in San Francisco. A region in Europe needs the provider's approval and costs 10% more. The UK region stores and does not process | Read |
| How long the text is kept | Up to 30 days in logs kept to check for misuse, "unless longer retention is required by law". The Responses API also stores each call for at least 30 days unless `"store": false` is sent | Read |
| Is it used to train models | No, unless the customer opts in | Read |
| Does a free tier differ | No page read draws a line between free and paid use of the API | Read, with one gap |
| Zero retention | Offered, "subject to prior approval by OpenAI". Through the sales team | Read |
| Data processing agreement | Yes. It is part of the Services Agreement and is accepted with it. A signed copy can be had through a form | Read |
| A safeguard for a transfer from the UK | The EU standard contractual clauses as amended by the UK Addendum, written into the agreement | Read |
| What the provider says of sensitive data | "No sensitive data is intended to be transferred unless the user includes it unexpectedly in unstructured data" | Read |

The adapter can be built and tested. Four things stand between it and a real person's sentence: one field, `store`, decides whether every call is kept for 30 days; the agreement does not plan for special category data; processing in Europe needs an approval that a small customer may not get; and the smallest model cannot be pinned to a version. The last section puts them to the founder.

## 1. The call

| Matter | What the documents say | Read |
|---|---|---|
| Address | `https://api.openai.com/v1/responses` | Read |
| Method | `POST` | Read |
| Header that carries the key | `Authorization: Bearer OPENAI_API_KEY_OR_ACCESS_TOKEN`. "Provide API credentials with HTTP Bearer authentication." | Read |
| May the key go in the address | No way to do so is documented. Every sample sends it in the header | Read |
| Other headers | `Content-Type: application/json`. `OpenAI-Organization` and `OpenAI-Project` are needed only "if you belong to more than one organization or access projects through a legacy user API key" | Read |
| Size of headers | "keep the total size of an API request's headers under 64 KiB" | Read |
| Version | "The REST API (currently v1)". No version header is asked for | Read |
| Addresses for a region | `us.api.openai.com`, `eu.api.openai.com`, `gb.api.openai.com` and seven more. See section 7 | Read |
| Redirects | None is documented | Read |
| The older API | `POST https://api.openai.com/v1/chat/completions`. "While Chat Completions remains supported, Responses is recommended for all new projects." | Read |

Sources: <https://developers.openai.com/api/reference/overview>, <https://developers.openai.com/api/reference/resources/responses/methods/create>, <https://developers.openai.com/api/docs/guides/migrate-to-responses>.

### Fields of the body that matter

| Field | Send | Why | Read |
|---|---|---|---|
| `model` | The configured id | | Read |
| `input` | A list of two messages: one with the role `developer` that holds the instructions, one with the role `user` that holds the JSON of the spec and the sentence | The instructions may also go in the top-level field `instructions`. That field cannot hold a cache mark: "Top-level `instructions` cannot contain an explicit breakpoint." | Read |
| `text.format` | `{"type": "json_schema", "name": ..., "strict": true, "schema": ...}` | See section 2. `name` "Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64" | Read |
| `store` | `false`, always | "Defaults to true when omitted. If set to true, response data will be stored for at least 30 days" | Read |
| `reasoning` | `{"effort": "none"}` | The default on `gpt-6-luna` is `medium`. Reasoning tokens "are billed as output tokens" and count against `max_output_tokens` | Read |
| `max_output_tokens` | The configured limit | "An upper bound for the number of tokens that can be generated for a response, including visible output tokens and reasoning tokens." The least it may be is 16 | Read |
| `prompt_cache_options` | `{"mode": "explicit"}` | With one mark after the instructions, only the instructions are written to the cache. With no mark, "the request does not use prompt caching". See section 6 | Read |
| `stream`, `background`, `tools`, `previous_response_id`, `conversation` | Never | Each either stores text or changes the shape of the answer | Read |
| `safety_identifier`, `prompt_cache_key`, `user`, `metadata` | Never | Each is a value that stands for a person or a search. Burro keeps none (ADR 0011). The provider says "Safety identifiers are recommended but not required." | Read |
| `temperature`, `top_p` | Leave out | They are refused when reasoning is on: "When reasoning effort is not `none`, remove `temperature`, `top_p`, and `top_logprobs`." Leaving them out means a change of effort cannot break the call | Read |
| `service_tier` | Leave out | The project's default applies. In Europe, `gpt-6-luna` runs "only with Standard processing" | Read |
| `truncation` | Leave out | The default is `disabled`: a prompt that is too long "will fail with a 400 error", which is what Burro wants | Read |

### Response headers

| Header | What it is | What to do with it |
|---|---|---|
| `x-request-id` | "Unique identifier for this API request" | Do not log it. It points to the person's text in the provider's logs for as long as they are kept |
| `x-ratelimit-remaining-requests`, `x-ratelimit-remaining-tokens` and their kin | How much of the limit is left | May be read as numbers. They hold nothing of the person |
| `Retry-After` | "The minimum number of seconds to wait before retrying" | Burro does not retry. It may be ignored |
| `X-Client-Request-Id` (a request header) | An id of the caller's choosing, which "OpenAI logs ... internally" | Never send it |

## 2. Structured output

| Question | Answer | Read |
|---|---|---|
| How to require it | `text.format` with `"type": "json_schema"`, `"strict": true` and the schema | Read |
| Enforced or encouraged | Enforced. "Structured Outputs is a feature that ensures the model will always generate responses that adhere to your supplied JSON Schema, so you don't need to worry about the model omitting a required key, or hallucinating an invalid enum value." | Read |
| What is not promised | The values. "Structured Outputs can still contain mistakes." An answer that fits the schema can still be wrong, so Burro's guard stays | Read |
| A schema it does not support | Refused, not ignored. "If you turn on Structured Outputs by supplying `strict: true` and call the API with an unsupported JSON Schema, you will receive an error." | Read |
| The older JSON mode | `{"type": "json_object"}`. Valid JSON, no schema. "Not recommended for gpt-4o and newer models". Burro does not use it | Read |
| Which models | "gpt-4o-mini, gpt-4o-2024-08-06, and later". The page of `gpt-6-luna` lists `structured_outputs` | Read |
| Order of keys | "outputs will be produced in the same order as the ordering of keys in the schema" | Read |
| Does the schema stay in a region | No. The provider counts a "structured output schema" as system data, which "may be processed and stored outside the selected region". Burro's schema holds no word of a person's, so this costs nothing | Read |

Source: <https://developers.openai.com/api/docs/guides/structured-outputs>.

### What the schema may hold

| Part of JSON Schema | Accepted | Read |
|---|---|---|
| Types | "String, Number, Boolean, Integer, Object, Array, Enum, anyOf" | Read |
| `enum` | Yes | Read |
| Nullable | Yes, as a union with null: `"type": ["string", "null"]` | Read |
| Optional fields | No. "all fields or function parameters must be specified as required" | Read |
| `additionalProperties` | Must be `false` on every object. "we require developers to set `additionalProperties: false`" | Read |
| The root | "must be an object, and not use `anyOf`" | Read |
| `$defs` and `$ref` | Yes. "Definitions are supported". Recursive schemas too | Read |
| For strings | `pattern`, and `format` with nine named formats | Read |
| Length of a string, `minLength` and `maxLength` | Not on the list of what is supported for strings. Named only in the list of what fine-tuned models lack. Treat as not supported | Read, and the page is unclear |
| For numbers | `multipleOf`, `maximum`, `exclusiveMaximum`, `minimum`, `exclusiveMinimum` | Read |
| For arrays | `minItems`, `maxItems` | Read |
| Not supported | "`allOf`, `not`, `dependentRequired`, `dependentSchemas`, `if`, `then`, `else`" | Read |

### Limits on the whole schema

| Limit | Value | Read |
|---|---|---|
| Properties | "up to 5000 object properties total" | Read |
| Nesting | "up to 10 levels of nesting" | Read |
| Names and values | "total string length of all property names, definition names, enum values, and const values cannot exceed 120,000 characters" | Read |
| Enum values | "up to 1000 enum values across all enum properties" | Read |
| One large enum | Over 250 values, their total length "cannot exceed 15,000 characters" | Read |

### How Burro's schema fits

Measured on the day from `burro_api.claude.SCHEMA`. It moves as the vocabulary moves.

| Measure | Burro's schema | The limit | Fits |
|---|---|---|---|
| Keywords used | `$defs`, `$ref`, `additionalProperties`, `enum`, `items`, `properties`, `required`, `type` | All supported | Yes |
| Root | An object, no `anyOf` | Must be so | Yes |
| Objects closed, all fields required | All 7 | Must be so | Yes |
| Properties | 51 | 5,000 | Yes |
| Nesting of objects | 2 | 10 | Yes |
| Enum values | 133 | 1,000 | Yes |
| Characters in names and values | About 2,100 | 120,000 | Yes |

`_plain` strips `maxLength`, `minLength`, `maximum`, `minimum`, `maxItems` and `minItems` before the schema is sent. This provider would take four of the six. Stripping them does no harm, because Burro checks them itself when the answer comes back.

Not tested: whether the live service takes the schema as it stands. The first call says.

### A refusal, and an answer cut short

| Case | What comes back | Read |
|---|---|---|
| The model refuses | HTTP 200, `status` is `completed`, and the content part has `"type": "refusal"` with the words in `refusal`. "Since a refusal does not necessarily follow the schema you have supplied ... the API response will include a new field called `refusal`" | Read |
| The answer is cut short | HTTP 200, `status` is `incomplete`, `incomplete_details.reason` is `max_output_tokens`. The text may be JSON that does not close | Read |
| The answer is cut by a filter | HTTP 200, `status` is `incomplete`, `incomplete_details.reason` is `content_filter` | Read |
| Reasoning used the whole limit | The same as cut short, and "This might occur before any visible output tokens are produced" | Read |

All four are `ModelError`. The words of a refusal are never logged or shown: they can repeat what the person typed.

## 3. What "finished" means

An answer is whole when all four hold:

1. The HTTP status is 200.
2. The top-level `status` is `"completed"`.
3. `output` holds an item whose `type` is `"message"`.
4. That message holds a content part whose `type` is `"output_text"`. Its `text` is the JSON.

| Field | Values it can take | Which is whole | Read |
|---|---|---|---|
| `status` | `completed`, `failed`, `in_progress`, `cancelled`, `queued`, `incomplete` | `completed` | Read |
| `incomplete_details.reason` | `max_output_tokens`, `max_messages`, `content_filter`, `steered`. `null` when whole | `null` | Read |
| `error` | `null`, or an object with `code` and `message` | `null` | Read |
| `output[].type` | `message`, `reasoning` and many kinds of tool call | `message` | Read |
| `output[].status`, on a message | `in_progress`, `completed`, `incomplete` | `completed` | Read |
| `output[].content[].type` | `output_text`, `refusal` | `output_text` | Read |

Three traps:

| Trap | What to do | Read |
|---|---|---|
| `output_text` at the top level of the answer | Do not look for it. It is an "SDK-only convenience property". It is not in the JSON | Read |
| The message is not always first in `output` | Find it by `type`. With reasoning on, a `reasoning` item may stand before it | Read |
| A refusal has `status` `completed` | Check the type of the content part, not only the status | Read |

In Chat Completions the same fact is `choices[0].finish_reason`. It is `stop` when whole. The others are `length`, `tool_calls`, `content_filter` and `function_call`. A refusal is in `choices[0].message.refusal`.

Source: <https://developers.openai.com/api/reference/resources/responses/methods/create>, <https://developers.openai.com/api/reference/resources/chat>.

## 4. Usage

| Field | What the provider says it counts | Read |
|---|---|---|
| `usage.input_tokens` | "The number of input tokens." It includes the cached ones | Read |
| `usage.input_tokens_details.cached_tokens` | "The number of tokens that were retrieved from the cache." | Read |
| `usage.input_tokens_details.cache_write_tokens` | "The number of input tokens that were written to the cache." | Read |
| `usage.output_tokens` | "The number of output tokens." It includes the reasoning tokens | Read |
| `usage.output_tokens_details.reasoning_tokens` | "The number of reasoning tokens." | Read |
| `usage.total_tokens` | "The total number of tokens used." | Read |

That `input_tokens` includes the other two is read from the provider's own sum: `ordinaryInputTokens = inputTokens - cachedTokens - cacheWriteTokens`. Source: <https://developers.openai.com/api/docs/guides/prompt-caching>.

### What goes into `ModelReply`

| `ModelReply` | From | Why |
|---|---|---|
| `input_tokens` | `usage.input_tokens` less `cached_tokens` | The adapter that exists counts tokens that were not read from a cache. So the field means the same in every adapter |
| `cache_read_tokens` | `usage.input_tokens_details.cached_tokens` | |
| `output_tokens` | `usage.output_tokens` | Reasoning tokens are billed as output, so they belong in the count |

A missing `usage`, `input_tokens` or `output_tokens` is an error, not a nil. `input_tokens_details` is left out of some of the provider's samples, so a missing `cached_tokens` is read as 0.

Tokens written to the cache are billed at 1.25 times the price of input. `ModelReply` has no field for them. Until it has, a cost worked out from `ModelReply` is a little low on a call that writes the cache.

## 5. Errors

An error answers with a JSON body of this shape: `{"error": {"message": ..., "type": ..., "param": ..., "code": ...}}`. The shape is read from the provider's cookbook, where it is printed as a Python value. The reference page gives no sample of it.

| Status | Type and code | Meaning | Becomes | Read |
|---|---|---|---|---|
| No answer in time | None. The caller's own clock | Timed out | timeout | Read |
| 408 | "408 Request Timeout" | The provider gave up | timeout | Read, in the guide to Flex and the library's README only |
| 400 | `invalid_request_error` | A bad request: a schema it does not take, a parameter it does not know, a prompt too long, a service tier the project may not use | error | Read |
| 401 | "Invalid Authentication", "Incorrect API key provided", "You must be a member of an organization to use the API", "IP not authorized" | The key is wrong, revoked, or used from an address that is not allowed | error | Read |
| 403 | "Country, region, or territory not supported" | The call came from a place the provider does not serve | error | Read |
| 403 | `invalid_request_error`, code `misalignment_policy_violation` | A safety monitor stopped the call. It covers work by agents, not a call like Burro's | error | Read |
| 404 | `NotFoundError` in the library | "Requested resource does not exist", such as a model that is retired or misspelt | error | Read. The status for a retired model is not given |
| 409, 422 | `ConflictError`, `UnprocessableEntityError` in the library | Not expected on this call | error | Read |
| 429 | "Rate limit reached for requests" | Too many calls or tokens in a minute | capped | Read |
| 429 | `rate_limit_error`, code `slow_down` | Traffic rose too fast | capped | Read |
| 429 | code `credit_balance_exhausted` | No prepaid credit is left | capped | Read |
| 429 | code `organization_spend_limit_exceeded` | The organisation's own monthly spend limit | capped | Read |
| 429 | code `project_spend_limit_exceeded` | The project's own monthly spend limit | capped | Read |
| 429 | code `organization_usage_limit_exceeded` | The monthly limit the provider sets | capped | Read |
| 429 | type `insufficient_quota` | "For billing-related errors ... The broader error.type can still be insufficient_quota." | capped | Read |
| 500 | "The server had an error while processing your request" | The provider's fault | error | Read |
| 503 | `service_unavailable_error`, code `server_is_overloaded` | "The requested model is temporarily overloaded." | error | Read |
| 200 | `status` `failed`, with `error.code` | The model could not answer. The codes include `server_error`, `rate_limit_exceeded` and `invalid_prompt` | error. capped if the code is `rate_limit_exceeded` | Read |
| 200 | `status` `incomplete` | Cut short, or cut by a filter | error | Read |
| 200 | A content part of type `refusal` | The model refused | error | Read |
| 200 | Whole, but not JSON, or JSON that does not fit | Should not happen with `strict`. Checked all the same | error | Not read |
| Any 3xx | None documented | The adapter refuses it | error | Not read |
| 402, 502, 504, 529 | Not on any page read | | error | Not read |

Sources: <https://developers.openai.com/api/docs/guides/error-codes>, <https://developers.openai.com/api/docs/guides/rate-limits>, <https://developers.openai.com/api/docs/guides/safety-checks/misalignment-monitoring>, <https://developers.openai.com/api/docs/guides/flex-processing>, <https://github.com/openai/openai-python>.

### Four things the builder must know

| Point | What the documents say | Read |
|---|---|---|
| Every limit on money answers 429, as a rate limit does | So the status alone says capped. The code tells a limit of spend from a limit of rate, if that is ever wanted | Read |
| Overload moved from 429 to 503 | "model overload returns 503 with `service_unavailable_error` and `server_is_overloaded`". "Keep support for earlier response codes while your application can still receive them." So a 429 may still mean overload for a while. It becomes capped, and the rules answer either way | Read |
| A message may repeat the request | Not said. A `400` names the parameter at fault in `error.param`. Treat every message as if it holds the person's words, and keep none of it | Not read |
| A block for one person | With `safety_identifier`, "the associated `safety_identifier` is completely blocked". Without it, "repeated policy violations from your organization can lead to losing access for your entire organization". Burro sends none, so one person's misuse is answered for by the whole of Burro | Read |

### The limits on a new account

| Tier | How it is reached | Monthly limit on use | Read |
|---|---|---|---|
| Free | "User must be in an allowed geography" | $100 | Read |
| Tier 1 | "$5 paid" | $100 | Read |
| Tier 2 | "$50 paid" | $500 | Read |
| Tier 3 | "$100 paid" | $1,000 | Read |

| Limit on `gpt-6-luna` | Tier 1 | Tier 2 | Read |
|---|---|---|---|
| Requests a minute | 500 | 5,000 | Read |
| Tokens a minute | 500,000 | 2,000,000 | Read |

No page of a model lists a limit for the Free tier. Whether `gpt-6-luna` can be called on it is not said.

At about 4,400 tokens a call, 500,000 tokens a minute is about 110 calls a minute. The limit on tokens is met before the limit on requests.

## 6. Models

### Offered today, for text

| Family | Models | What the provider says of them | Read |
|---|---|---|---|
| GPT-6 | `gpt-6-astra`, `gpt-6-sol`, `gpt-6-luna` | The newest. Astra is "our flagship model for complex reasoning and coding". Luna is for "cost-sensitive, high-volume workloads" | Read |
| GPT-5.6 | `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` | The family before. Luna "roughly corresponds to the nano model tier used in earlier GPT-5 families" | Read |
| GPT-5.5 and GPT-5.4 | `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.4-nano`, and the `-pro` kinds | Still listed and priced | Read |
| GPT-5, 5.1, 5.2 | `gpt-5`, `gpt-5-mini`, `gpt-5-nano` and others | Still listed. The first versions of GPT-5 retire on 11 December 2026 | Read |
| GPT-4.1, GPT-4o, o-series | `gpt-4.1-nano`, `gpt-4o-mini`, `o4-mini` and others | Old. Many retire on 23 October 2026 | Read |

The reference lists 88 names for `model`. The full list is at <https://developers.openai.com/api/docs/models/all>.

### The small models, in US dollars for a million tokens

Standard service, prompts under 272,000 tokens.

| Model | In | Cached in | Cache write | Out | Context | Structured output | A dated version | Retires | Read |
|---|---|---|---|---|---|---|---|---|---|
| `gpt-6-luna` | 0.10 | 0.01 | 0.125 | 0.50 | 1,050,000 | Yes | None | None listed | Read |
| `gpt-5.6-luna` | 0.20 | 0.02 | 0.25 | 1.20 | 1,050,000 | Yes | None | None listed | Read |
| `gpt-5.4-nano` | 0.20 | 0.02 | No charge | 1.25 | 400,000 | Yes | `gpt-5.4-nano-2026-03-17` | None listed | Read |
| `gpt-4o-mini` | 0.15 | 0.075 | No charge | 0.60 | 128,000 | Yes | `gpt-4o-mini-2024-07-18` | None listed | Read |
| `gpt-5-nano` | 0.05 | 0.005 | No charge | 0.40 | 400,000 | Yes | `gpt-5-nano-2025-08-07` | Its only version, on 11 December 2026 | Read |
| `gpt-4.1-nano` | 0.10 | 0.025 | No charge | 0.40 | 1,047,576 | Yes | `gpt-4.1-nano-2025-04-14` | 23 October 2026 | Read |
| `gpt-6-sol`, the next size up | 2.00 | 0.20 | 2.50 | 10.00 | 1,050,000 | Yes | None | None listed | Read |

| Rule on price | What the documents say | Read |
|---|---|---|
| A region | "Regional processing (data residency) endpoints are charged a 10% uplift for models released on or after March 5, 2026" | Read |
| Batch and Flex | Half price. Both are slow, and neither is for a person who is waiting | Read |
| Fast mode | Twice the price | Read |
| A change of price | "Price changes on the Pricing Page will be effective fourteen days after they are posted." | Read |
| Notice of retirement | "Generally available models: At least 6 months." | Read |

Sources: <https://developers.openai.com/api/docs/pricing>, <https://developers.openai.com/api/docs/models/gpt-6-luna>, <https://developers.openai.com/api/docs/deprecations>, <https://openai.com/policies/services-agreement/>.

### Reasoning

| Point | What the documents say | Read |
|---|---|---|
| The default on `gpt-6-luna` | "`reasoning.effort` supports `none`, `low`, `medium` (default), `high`, `xhigh`, and `max`." | Read |
| What reasoning costs | Reasoning tokens "are billed as output tokens". "the models may generate anywhere from a few hundred to tens of thousands of reasoning tokens" | Read |
| What it does to the limit | `max_output_tokens` counts them. The answer can be cut short "before any visible output tokens are produced" | Read |
| Which models take `none` | "GPT-6 Astra does not support the `none` reasoning effort; GPT-6 Sol and Luna do." | Read |

So Burro sends `"effort": "none"`. Left at the default, 1,000 reasoning tokens a call would take the cost of 1,000 searches on `gpt-6-luna` from $0.45 to $0.95, and the wait would grow.

### The cache

| Point | What the documents say | Read |
|---|---|---|
| On by default | "Prompt caching is enabled by default for supported OpenAI models." | Read |
| What is kept | "The prompt cache stores key-value (KV) tensors, not the tokens themselves." | Read |
| The smallest prompt that is cached | "1,024 tokens for GPT-5.6 and later" | Read |
| How long | "A cached prefix remains eligible for reuse for 30 minutes after its most recent write or reuse, though OpenAI may retain it longer." The page on data says such state "is not retained after the 24-hour expiration" | Read |
| Price of a read | "0.1x the uncached input-token rate" | Read |
| Price of a write, on GPT-5.6 and later | "1.25x the uncached input-token rate". Older models have "No additional cache-write charge" | Read |
| Where the default mark goes | "at the end of the latest eligible message". For Burro that is the end of the person's sentence | Read |
| How to mark only the instructions | `prompt_cache_options.mode` set to `explicit`, and `"prompt_cache_breakpoint": {"mode": "explicit"}` on the text block of the `developer` message | Read |
| How to use no cache | `explicit` with no mark: "the request does not use prompt caching or create cache writes" | Read |
| What else is in the cached part | The schema. `text.format` "Adds output-format instructions and the requested schema" | Read |
| Shared between customers | No. "Caches are not shared across organizations and cannot be reused across regional processing boundaries." | Read |

Left at the default, each call writes the person's sentence into the cache and pays the write price on it. With the explicit mark, the person's words come after the mark and are not written. That is better for privacy and for cost.

Source: <https://developers.openai.com/api/docs/guides/prompt-caching>.

### The smallest model fit for the job

`gpt-6-luna`. It is the cheapest model with no date of retirement, it takes structured output, and reasoning can be switched off. This rests on the documents alone. No call was made, so how well it reads a sentence is not known.

`gpt-5.4-nano-2026-03-17` is the choice if a pinned version matters more than price. It costs about twice as much, and its reasoning is off by default.

`gpt-5-nano` and `gpt-4.1-nano` are cheaper or as cheap, and both retire within three months.

### 1,000 searches, at 3,000 tokens in and 300 out

"Cached" assumes 2,700 of the 3,000 tokens are the fixed instructions and are read from the cache, and 300 are not. This is the same split as in the other three reports. Reasoning is off.

| Model | Not cached | Cached, cache warm | Cached, cache cold on every call |
|---|---|---|---|
| `gpt-6-luna` | $0.45 | $0.21 | $0.52 |
| `gpt-5.6-luna` | $0.96 | $0.47 | $1.10 |
| `gpt-5.4-nano` | $0.98 | $0.49 | $0.98 |
| `gpt-4o-mini` | $0.63 | $0.43 | $0.63 |
| `gpt-6-sol` | $9.00 | $4.14 | $10.35 |

The sums, for `gpt-6-luna`: not cached, 3.0 x 0.10 + 0.3 x 0.50 = 0.45. Warm, 2.7 x 0.01 + 0.3 x 0.10 + 0.3 x 0.50 = 0.207. Cold, 2.7 x 0.125 + 0.3 x 0.10 + 0.3 x 0.50 = 0.5175.

| What would change the figure | By how much |
|---|---|
| The cache is cold when fewer than about one call in five comes within 30 minutes of the last | Above that share of warm calls the cache saves money. Below it, it costs more than no cache |
| Burro's real prompt is longer than 3,000 tokens. The instructions are about 10,600 characters and the schema about 5,900, which is near 4,100 tokens at four characters a token | Not cached, about $0.59. Warm, about $0.22 |
| Reasoning left on | Each 1,000 reasoning tokens a call adds $0.50 |
| A region in Europe | Add 10% |

Plan on not cached: **about $0.60 for 1,000 searches** on `gpt-6-luna` with the prompt as it stands. Token counts are estimates until they are measured.

## 7. What happens to a person's text

### Who answers for the text

| Point | What the documents say | Read |
|---|---|---|
| Which terms apply | The Services Agreement. It "only applies to use of OpenAI's APIs" and the business products | Read |
| Who the customer contracts with | "OpenAI OpCo, LLC, for Customers located outside the EEA or Switzerland". A UK company is outside both, so its contract is with the company in the United States | Read |
| Which law governs | "for Customers in the EEA, Switzerland, or UK, the Laws of Ireland", in "the courts of Dublin" | Read |
| The provider's role | "OpenAI acts as a Data Processor on the Customer's behalf" | Read |
| The privacy policy | Does not cover this. "This Privacy Policy does not apply to content that we process on behalf of customers of our business offerings, such as our API." | Read |

Sources: <https://openai.com/policies/services-agreement/>, <https://openai.com/policies/data-processing-addendum/>, <https://openai.com/policies/row-privacy-policy/>.

### The questions

| Question | What the provider says | Page | Read |
|---|---|---|---|
| How long is it kept, to check for misuse | "By default, abuse monitoring logs are generated for all API feature usage and retained for up to 30 days, unless longer retention is required by law, or is reasonably necessary to protect our services or any third party from harm." | <https://developers.openai.com/api/docs/guides/your-data> | Read |
| What those logs hold | "Abuse monitoring logs may contain certain customer content, such as prompts and responses, as well as metadata derived from that customer content, such as classifier outputs." | The same | Read |
| How long is it kept, as a stored answer | "Except as noted below, the Responses API has a 30 day Application State retention period by default, or when the store parameter is set to true. In those cases, response data will be stored for at least 30 days." | The same | Read |
| How to stop that | "Responses are stored by default. Chat completions are stored by default for new accounts. To disable storage in either API, set `store: false`." | <https://developers.openai.com/api/docs/guides/migrate-to-responses> | Read |
| How long is it kept, in the cache | "Prompt caching may store encrypted key/value tensors in GPU-local storage as application state. This data is stored on the local GPU machines and is not retained after the 24-hour expiration." | <https://developers.openai.com/api/docs/guides/your-data> | Read |
| Is it used to train, on the paid tier | "As of March 1, 2023, data sent to the OpenAI API is not used to train or improve OpenAI models (unless you explicitly opt in to share data with us)." | The same | Read |
| The same, in the contract | "OpenAI will not use Customer Content to develop or improve the Services, unless Customer explicitly agrees to such use." | <https://openai.com/policies/services-agreement/>, section 4.2 | Read |
| Is it used to train, on a free tier | No page read treats free use of the API differently. The sentences above name no tier | The three pages above | Read |
| How a customer opts in | "through explicit opt-in in the API dashboard" | <https://openai.com/business-data/> | Read |
| Whether opting in earns free tokens | Not read. The page that would say is on a host that was not read | | Not read |
| Who at the provider can read it | "Our access to API business data stored on our systems is limited to (1) authorized employees that require access for engineering support, investigating potential platform abuse, and legal compliance and (2) specialized third-party contractors who are bound by confidentiality and security obligations, solely to review for abuse and misuse." | <https://openai.com/enterprise-privacy/> | Read |
| Is it read by machines | "We may run any business data submitted to OpenAI's services through automated content classifiers and safety tools" | The same | Read |
| Is flagged text passed on | "For content that OpenAI's models flag as being in violation of OpenAI's policies, OpenAI may share samples of the flagged Customer Content with relevant Sub-processors to assist OpenAI in its review and enforcement." The companies named for this are in the United States, Canada and the Philippines | <https://openai.com/policies/sub-processor-list/> | Read |
| Where is it processed | No page names a default region. The list of sub-processors names cloud companies in the United States, the United Kingdom and more than twenty other countries | The same | Read |
| When the contract ends | "OpenAI will delete all Customer Content from its systems within thirty days", unless the law requires it to be kept | <https://openai.com/policies/services-agreement/>, section 11.3 | Read |
| Has the provider ever had to keep text for longer | A recollection: in 2025 a court in the United States ordered it to keep text it would have deleted. This was not checked on the day | | Not read |

### A region

| Point | What the documents say | Read |
|---|---|---|
| Who may have one | "Contact our sales team to see if you're eligible for using data residency controls." | Read |
| What else is needed outside the United States | "To use data residency with any region other than the United States, you must be approved for abuse monitoring controls, and execute a Modified Retention amendment." | Read |
| Europe | `eu.api.openai.com`. "Europe (EEA + Switzerland)". Stores and processes. `gpt-6-luna` is listed, "Standard processing only" | Read |
| United Kingdom | `gb.api.openai.com`. Stores. Does not process | Read |
| What a region without processing means | "OpenAI may also process and temporarily store Customer Content outside of the Region to deliver the services." | Read |
| What a region never covers | "system data, which may be processed and stored outside the selected region" | Read |
| How the request gets there | "OpenAI uses Cloudflare Regional Services so that TLS termination and HTTPS decryption occur within the selected processing region." | Read |
| Price | 10% more | Read |

So a UK company that wants the text processed near home must ask for Europe, not the UK. It must first be approved for zero retention or its lighter kind.

Source: <https://developers.openai.com/api/docs/guides/your-data>.

### Zero retention

| Point | What the documents say | Read |
|---|---|---|
| What it does | "Zero Data Retention excludes customer content from abuse monitoring logs". And `store` "will always be treated as false" | Read |
| The lighter kind | "Modified Abuse Monitoring excludes customer content ... from abuse monitoring logs across all API endpoints" | Read |
| How to get it | "Currently, these controls are subject to prior approval by OpenAI and acceptance of additional requirements." "Get in touch with our sales team" | Read |
| Once approved | "you'll see a Data Retention tab within Settings → Organization → Data controls" | Read |
| Is `/v1/responses` covered | Yes. The table marks it as eligible: "Yes, see below for limitations" | Read |
| What it leaves | The customer becomes "responsible for ensuring their users abide by OpenAI's policies" | Read |
| Can it be withdrawn | Yes. "we reserve the right to make models ineligible for Zero Data Retention or Modified Abuse Monitoring for specific customers, as notified in advance" | Read |
| Whether a small customer is granted it | Not said | Not read |

### The agreement on data processing

| Point | What the documents say | Read |
|---|---|---|
| Is one offered | Yes. "This OpenAI Data Processing Addendum ('DPA') supplements, and is incorporated into, the OpenAI Services Agreement" | Read |
| How it is accepted | With the Services Agreement. "By clicking 'I agree,' accepting the Order Form, or using the Services, Customer agrees to this Agreement." | Read |
| A signed copy | "Please complete our DPA form to execute a DPA with OpenAI." The form is on a host that was not read | Read, the form not |
| Breach | "OpenAI will notify Customer without undue delay after becoming aware of any Personal Data Breach." | Read |
| Sub-processors | A general authorisation. Changes are announced, and the customer has 30 days to object | Read |
| Requests from people | "OpenAI will not respond to any such request without Customer's prior written authorization" | Read |
| Audit | Once a year, on written request, at the customer's cost | Read |

Source: <https://openai.com/policies/data-processing-addendum/>, updated 1 December 2025, in force from 1 January 2026.

### UK and EU law

| Point | What the documents say | Read |
|---|---|---|
| In general | "OpenAI's data protection practices support your compliance with GDPR, CCPA, and other privacy laws" | Read |
| The transfer from the UK | "Customer hereby instructs OpenAI OpCo, LLC to process any UK Data in compliance with this DPA and with the SCCs as amended by the UK Addendum, which are deemed entered into (and incorporated into this DPA by this reference)" | Read |
| Who sends and who receives | "Data exporter(s): the Customer under the Agreement; Data importer(s): OpenAI OpCo, LLC, 1455 3rd Street, San Francisco, CA 94158" | Read |
| Which law governs the clauses | "the laws of England and Wales", and "the competent supervisory authority is the Information Commissioner's Office" | Read |
| Special category data | Schedule 1, item 5: "No sensitive data is intended to be transferred unless the user includes it unexpectedly in unstructured data" | Read |
| What the customer promises | "Customer represents, warrants and covenants that it has provided all necessary notices, and has and shall maintain throughout the Term all necessary rights, consents and authorizations" | Read |
| Who sets how long things are kept | The customer "is responsible for certain configurations and design decisions for the Services ... (e.g., retention periods, deletion, etc.)" | Read |
| Health data under United States law | "Customer agrees not to use the Services to create, receive, maintain, transmit, or otherwise process Protected Health Information, unless it has signed the Healthcare Addendum." The term is defined by a United States rule that binds health bodies there. Whether it reaches a sentence typed in London is a question of law | Read, the reach not |

### What a UK company must do first

The first four come from the provider's pages. The rest are a reading of UK law, not checked on the day against the regulator's guidance, and not legal advice.

| Step | From | Read |
|---|---|---|
| Accept the Services Agreement. The agreement on data processing and the UK Addendum come with it | The provider | Read |
| Send `"store": false` on every call | The provider | Read |
| Tell people before their words are sent, and hold whatever consent the law asks for | The provider, DPA 3.1 | Read |
| Do not opt in to sharing data | The provider | Read |
| Decide the lawful basis, and the condition for special category data. Explicit consent is the likely one | UK GDPR, articles 6 and 9 | Not read |
| Write a data protection impact assessment | UK GDPR, article 35 | Not read |
| Write a risk assessment for the transfer to the United States | The regulator's guidance on transfers | Not read |
| Name the provider, or the kind of provider, in the privacy notice | UK GDPR, article 13 | Not read |
| Ask the provider in writing whether the agreement covers a sentence that may hold health or religion | This report | |

## 8. Terms that bind a product like this

| Matter | What the documents say | What it means for Burro | Read |
|---|---|---|---|
| Age | The customer will not "allow minors to use OpenAI Services without consent from their parent or guardian" | Burro is for adults choosing a home. Say so in Burro's own terms | Read |
| Children's data | "You should not use OpenAI services to process any personal data of children under 13 or the applicable age of digital consent without first implementing zero data retention in our API." | A parent may type a child's school. That is data about a child, sent by an adult. Whether the sentence reaches it is not said | Read |
| A duty to say a model is used | None was found in the Usage Policies in force, dated 29 October 2025, or in the Services Agreement | The duty to tell people comes from the agreement on data processing, which asks for "all necessary notices", and from UK law | Read |
| A duty to mark what a model wrote | The Sharing and Publication Policy asks that shared content "Indicate that the content is AI-generated". It covers posts, streams and published writing | Burro shows typed edits, not writing. When a model later writes explanations, read this again | Read |
| Housing | The Usage Policies forbid "automation of high-stakes decisions in sensitive areas without human review", and list "housing" beneath it | Burro decides nothing about a person. The model turns a sentence into edits the person can see and change, and places are ranked by code. This reading is the report's, not the provider's | Read, the reading not |
| Profiling | The same policies forbid "evaluation or classification of individuals based on their social behavior, personal traits, or biometric data (including social scoring, profiling, or inferring sensitive attributes)" | Burro asks the model to flag a request about who lives somewhere, so that it can refuse it. It sorts requests, not people, and keeps nothing. Worth a line in the record of decisions | Read, the reading not |
| Advice that needs a licence | No "tailored advice that requires a license, such as legal or medical advice, without appropriate involvement by a licensed professional" | Burro gives none | Read |
| Naming the provider | The Services Agreement, section 10: "Except with express prior written permission in each instance, neither Party will: (i) include the other Party's name or logo on their websites, media, or marketing materials; or (ii) make any public statement about its relationship with the other Party or this Agreement." | On its face this covers a privacy notice that names OpenAI. See the next row | Read |
| Naming the provider, the other page | The design guidelines: "If you are an active OpenAI developer, you may truthfully identify the OpenAI technology you use." They allow "is building on OpenAI" and forbid "partnered with", "worked with" and "collaborated with" | The two pages pull apart. A plain sentence of fact in a privacy notice is the safest form. No logo, no model name in the product's name | Read |
| Not looking like the provider's product | "please make a clear indication to users that your product is independently developed and not affiliated, endorsed, or sponsored by OpenAI" where a product "closely resembles an OpenAI product" | Burro does not resemble one | Read |
| Where it may be offered | "Customer and End Users may not access or offer access to the Services outside of the Supported Countries and Territories." The United Kingdom is on the list | Burro is for London | Read |
| What the customer owns | "Customer: (a) retains all ownership rights in Input; and (b) owns all Output." | | Read |
| Competing models | The customer will not "use Output to develop artificial intelligence models that compete with OpenAI's products and services" | Burro trains none | Read |
| Who answers for misuse | "Customer is responsible for all activities that occur under its Account, including the activities of End Users ... who access the Services through a Customer Application." | One person's misuse is Burro's to answer for | Read |
| Changes to the terms | "at least thirty days notice" where a change "materially impacts Customer's rights or obligations". Other changes take effect when posted. Going on using the service is acceptance | Someone must read the notices | Read |
| Disputes | "final and binding arbitration", with no class actions | | Read |
| Liability | Capped at what the customer paid in the twelve months before | At these prices, a few pounds | Read |

Sources: <https://openai.com/policies/services-agreement/>, <https://openai.com/policies/usage-policies/>, <https://openai.com/policies/sharing-publication-policy/>, <https://openai.com/brand/>, <https://developers.openai.com/api/docs/guides/safety-checks/under-18-api-guidance>, <https://developers.openai.com/api/docs/supported-countries>.

## 9. Examples to test against

### A request with a schema, copied

From <https://developers.openai.com/api/docs/guides/structured-outputs>.

```bash
curl https://api.openai.com/v1/responses \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-6-astra",
    "input": [
      {
        "role": "system",
        "content": "You are an expert at structured data extraction. You will be given unstructured text from a research paper and should convert it into the given structure."
      },
      {
        "role": "user",
        "content": "..."
      }
    ],
    "text": {
      "format": {
        "type": "json_schema",
        "name": "research_paper_extraction",
        "schema": {
          "type": "object",
          "properties": {
            "title": { "type": "string" },
            "authors": {
              "type": "array",
              "items": { "type": "string" }
            },
            "abstract": { "type": "string" },
            "keywords": {
              "type": "array",
              "items": { "type": "string" }
            }
          },
          "required": ["title", "authors", "abstract", "keywords"],
          "additionalProperties": false
        },
        "strict": true
      }
    }
  }'
```

### A whole answer, copied

From <https://developers.openai.com/api/reference/resources/responses/methods/create>. It answers a request for plain text. With a schema, `text` holds the JSON as a string, and `text.format.type` is `json_schema`.

```json
{
  "id": "resp_67ccd2bed1ec8190b14f964abc0542670bb6a6b452d3795b",
  "object": "response",
  "created_at": 1741476542,
  "status": "completed",
  "completed_at": 1741476543,
  "error": null,
  "incomplete_details": null,
  "instructions": null,
  "max_output_tokens": null,
  "model": "gpt-6-astra",
  "output": [
    {
      "type": "message",
      "id": "msg_67ccd2bf17f0819081ff3bb2cf6508e60bb6a6b452d3795b",
      "status": "completed",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "In a peaceful grove beneath a silver moon, a unicorn named Lumina discovered a hidden pool that reflected the stars. As she dipped her horn into the water, the pool began to shimmer, revealing a pathway to a magical realm of endless night skies. Filled with wonder, Lumina whispered a wish for all who dream to find their own hidden magic, and as she glanced back, her hoofprints sparkled like stardust.",
          "annotations": []
        }
      ]
    }
  ],
  "parallel_tool_calls": true,
  "previous_response_id": null,
  "reasoning": {
    "effort": null,
    "summary": null
  },
  "store": true,
  "temperature": 1.0,
  "text": {
    "format": {
      "type": "text"
    }
  },
  "tool_choice": "auto",
  "tools": [],
  "top_p": 1.0,
  "truncation": "disabled",
  "usage": {
    "input_tokens": 36,
    "input_tokens_details": {
      "cached_tokens": 0,
      "cache_write_tokens": 0
    },
    "output_tokens": 87,
    "output_tokens_details": {
      "reasoning_tokens": 0
    },
    "total_tokens": 123
  },
  "user": null,
  "metadata": {}
}
```

### The content of a whole answer to the request above, copied

From the structured outputs guide. This is what `text` holds, once parsed.

```json
{
  "title": "Application of Quantum Algorithms in Interstellar Navigation: A New Frontier",
  "authors": ["Dr. Stella Voyager", "Dr. Nova Star", "Dr. Lyra Hunter"],
  "abstract": "This paper investigates the utilization of quantum algorithms to improve interstellar navigation systems. By leveraging quantum superposition and entanglement, our proposed navigation system can calculate optimal travel paths through space-time anomalies more efficiently than classical methods. Experimental simulations suggest a significant reduction in travel time and fuel consumption for interstellar missions.",
  "keywords": [
    "Quantum algorithms",
    "interstellar navigation",
    "space-time anomalies",
    "quantum superposition",
    "quantum entanglement",
    "space travel"
  ]
}
```

### A refusal, copied

From the structured outputs guide. As printed it is not valid JSON: it has a comma after `"reasoning_tokens": 0` and another before the last brace, and the page marks two lines with `// highlight`. A test must take them out. They are left in here so the copy is true.

```text
{
  "id": "resp_1234567890",
  "object": "response",
  "created_at": 1721596428,
  "status": "completed",
  "completed_at": 1721596429,
  "error": null,
  "incomplete_details": null,
  "input": [],
  "instructions": null,
  "max_output_tokens": null,
  "model": "gpt-4o-2024-08-06",
  "output": [{
    "id": "msg_1234567890",
    "type": "message",
    "role": "assistant",
    "content": [
      // highlight-start
      {
        "type": "refusal",
        "refusal": "I'm sorry, I cannot assist with that request."
      }
      // highlight-end
    ]
  }],
  "usage": {
    "input_tokens": 81,
    "output_tokens": 11,
    "total_tokens": 92,
    "output_tokens_details": {
      "reasoning_tokens": 0,
    }
  },
}
```

### Usage with reasoning, copied

From <https://developers.openai.com/api/docs/guides/reasoning>. It shows `cached_tokens` with no `cache_write_tokens` beside it, so the adapter must not count on both.

```json
{
  "usage": {
    "input_tokens": 75,
    "input_tokens_details": {
      "cached_tokens": 0
    },
    "output_tokens": 1186,
    "output_tokens_details": {
      "reasoning_tokens": 1024
    },
    "total_tokens": 1261
  }
}
```

### An error, copied

From <https://developers.openai.com/cookbook/examples/how_to_handle_rate_limits>. It is printed there by the provider's Python library, so the body is written as a Python value.

```text
Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}}
```

The same body as JSON, made from the line above and not copied:

```json
{
  "error": {
    "message": "You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.",
    "type": "insufficient_quota",
    "param": null,
    "code": "insufficient_quota"
  }
}
```

### Answers that are not whole, made from the reference, not copied

The reference names the fields and their values. It gives no sample of these. Each is the whole answer above with the named fields changed.

| Case | Status | Fields to change |
|---|---|---|
| Cut short | 200 | `"status": "incomplete"`, `"incomplete_details": {"reason": "max_output_tokens"}` |
| Cut by a filter | 200 | `"status": "incomplete"`, `"incomplete_details": {"reason": "content_filter"}` |
| Failed | 200 | `"status": "failed"`, `"error": {"code": "server_error", "message": "..."}`, `"output": []` |
| Overloaded | 503 | The error body, with `"type": "service_unavailable_error"` and `"code": "server_is_overloaded"` |
| Too fast | 429 | The error body, with `"type": "rate_limit_error"` and `"code": "slow_down"` |
| Spend limit | 429 | The error body, with `"code": "project_spend_limit_exceeded"` |

### What Burro would send, not copied and not tested

Made from the fields in section 1. Every field is documented. The whole has not met the service.

```json
{
  "model": "gpt-6-luna",
  "store": false,
  "reasoning": { "effort": "none" },
  "max_output_tokens": 2048,
  "prompt_cache_options": { "mode": "explicit" },
  "input": [
    {
      "role": "developer",
      "content": [
        {
          "type": "input_text",
          "text": "<the instructions>",
          "prompt_cache_breakpoint": { "mode": "explicit" }
        }
      ]
    },
    {
      "role": "user",
      "content": [
        { "type": "input_text", "text": "<the JSON of the spec and the sentence>" }
      ]
    }
  ],
  "text": {
    "format": {
      "type": "json_schema",
      "name": "burro_edits",
      "strict": true,
      "schema": { "type": "object" }
    }
  }
}
```

`schema` is cut short here. The real one is `burro_api.claude.SCHEMA`.

## For the builder

| Matter | Do this | Why |
|---|---|---|
| Which API | Responses, `POST /v1/responses` | The provider recommends it for new work. Chat Completions has the same default of storing for new accounts, so it is no safer |
| Address | A constant: `https://api.openai.com/v1/responses`. The host for a region is a second constant, chosen by a setting, never built from one | The model's name is not in the address. Nothing a person types is |
| Model id | Check it against the pattern the service has, `MODEL_PATTERN`. `gpt-6-luna` and `gpt-5.4-nano-2026-03-17` both fit | It goes into the body |
| Key | In `Authorization: Bearer` only. Never send `OpenAI-Organization` or `OpenAI-Project` unless a key needs them | |
| `store` | `false` on every call, held by a test that reads the body that was sent | It is the one field between Burro and 30 days of stored sentences. Leaving it out means `true` |
| Reasoning | `"effort": "none"` on every call, held by a test | The default is `medium`. It costs money and time, and can use the whole limit |
| Cache | `"mode": "explicit"`, with one mark on the instructions. Or no mark at all, which is no cache | The default writes the person's sentence into the cache |
| Instructions | In a `developer` message, not in `instructions` | The top-level field cannot hold a cache mark |
| Never send | `safety_identifier`, `prompt_cache_key`, `user`, `metadata`, `X-Client-Request-Id`, `previous_response_id`, `conversation`, `tools`, `stream`, `background` | Each stands for a person, stores text, or changes the shape of the answer |
| Finished | Status 200, `status` is `completed`, a `message` item found by its type, a content part of type `output_text` | Anything else is `ModelError` |
| A refusal | Check the type of the content part. Never log or return the words | `status` is `completed` on a refusal. The words can repeat the person's |
| Deadline | One clock for the whole call | |
| Body | Read to a fixed size and refuse beyond it | |
| Errors | Decide on the status alone. 429 is capped. 408 is timed out. The rest are errors. Inside a 200, `failed` with the code `rate_limit_exceeded` is capped | The message can name a parameter, and may repeat the request |
| Redirects | Refuse every 3xx | A redirect could carry the key to another host. None is documented |
| Response headers | Do not log `x-request-id` | It leads to the person's text in the provider's logs |
| Usage | `cache_read_tokens` from `cached_tokens`. `input_tokens` from `usage.input_tokens` less `cached_tokens`. `output_tokens` from `usage.output_tokens` | So the three mean the same in every adapter |
| Missing usage | `usage`, `input_tokens` or `output_tokens` missing is an error. `input_tokens_details` missing is nil | One of the provider's samples leaves it out |
| The sample of a refusal | Take out the two stray commas and the two comment lines before using it in a test | As printed it is not valid JSON |
| The first live call | Check that the schema is accepted, that `cached_tokens` is above nil on the second call, that `reasoning_tokens` is nil, and how long the first call with a new schema takes | None of the four can be known from the pages |

## What Burro must tell a person

True of the paid service, with `store` off and no data shared by choice.

> When you type a sentence, Burro sends your words to OpenAI, a company in the United States, whose computers turn them into search settings and may be outside the UK. OpenAI says it does not use them to train its models and keeps them for up to 30 days to check for misuse, or longer if the law requires it, so leave out your health, your religion and anything else you would not want kept.

No free tier was found to differ. The provider's pages apply the same rules to every use of the API, and name no tier. The provider's own free chat app is a different product under different terms, and Burro does not use it.

The full privacy notice must also say that the provider's staff and its contractors may read text that is flagged.

## What was not read

| What | Standing | What was relied on |
|---|---|---|
| The help centre, `help.openai.com` | Not read | The developer pages. How a customer opts in to sharing data, and whether free tokens are given for it, were not read |
| The trust portal, `trust.openai.com` | Not read | Nothing. The provider's audit reports and certificates were not read |
| The dashboard and the form for a signed agreement, `platform.openai.com` | Not read. They need an account | The pages that describe them |
| The security measures the agreement points to, on `cdn.openai.com` | Not read | Nothing |
| The status page, `status.openai.com` | Not read | Nothing |
| The old address of the documents, `platform.openai.com/docs` | It sends the reader to `developers.openai.com`, which was read | |
| The UK regulator's guidance, `https://ico.org.uk/` | Not read | General knowledge. The steps in "What a UK company must do first" that are marked are not verified |
| A sample of an error body in the reference | None is given | The provider's cookbook, where one is printed as a Python value |
| The status and body for a retired model | Not given | Nothing. It becomes an error whatever it is |
| Whether the body of an error can repeat the request | Not said | Nothing. It is treated as if it can |
| Which region a call goes to by default | Not said | The agreement, which names the company in San Francisco as the receiver |
| Whether the Free tier can call `gpt-6-luna` | Not said | Nothing |
| Whether a small customer is granted zero retention, or a region | Not said | Nothing |
| The number of tokens in Burro's instructions | Counting needs a tokenizer or a key | Four characters a token |
| The order of 2025 to keep text for a court | Not searched for | A recollection. It is marked as such |
| Decisions of regulators about this provider | Not searched for | Nothing |
| The live service | No call was made | Examples from the documents |

## For the founder to decide

1. **Whether a sentence that may hold health, religion or sexuality may go to this provider as the agreement stands.** The agreement says no sensitive data is intended, "unless the user includes it unexpectedly in unstructured data". That is close to Burro's case and not the same: Burro knows people will do it. Three ways forward: ask the provider in writing; ask each person for explicit consent and tell them what to leave out; or both. It costs an email and a line on the screen.
2. **Whether processing in the United States is acceptable.** The contract for a UK company is with the company in the United States, under the UK Addendum. A region in Europe needs the provider's approval for zero retention first, a signed amendment, and 10% more. The UK region stores and does not process, so it does not help.
3. **Whether to ask for zero retention.** It ends the 30 days of logs. It is by approval, through the sales team. Whether a customer of Burro's size is granted it is not said. It costs an email. Without it, the 30 days stand and the notice must say so.
4. **Which model.** `gpt-6-luna` is the cheapest, at about $0.60 for 1,000 searches with the prompt as it stands. It cannot be pinned to a version, so its reading of a sentence may change without notice. `gpt-5.4-nano-2026-03-17` is pinned and costs about twice as much. The recommendation is `gpt-6-luna` in configuration, the golden queries run on both, and the golden queries run again each week so that a change is seen.
5. **Whether to use the cache.** With the explicit mark it keeps the person's words out of the cache and halves the cost when calls come often. When fewer than one call in five follows another within 30 minutes, it costs more than no cache. At launch, traffic is likely to be thin. The recommendation is no cache at first, and measure.
6. **Whether to send a safety identifier.** The provider asks for one so that it can block one person and not the whole customer. Burro has no accounts and keeps nothing that stands for a person. The recommendation is to send none, and to accept that one person's misuse is answered for by Burro.
7. **Whether the privacy notice may name OpenAI.** The Services Agreement forbids using the provider's name on a website without written permission. The provider's design guidelines allow a developer to "truthfully identify the OpenAI technology you use". UK law asks that people are told who receives their data, or what kind of company does. The recommendation is one plain sentence of fact, no logo, and an email to the provider to confirm.
8. **The spend limit.** Set a monthly limit on a project of Burro's own, in the dashboard. At the limit the provider answers 429, Burro's rules take over, and no bill grows. Decide the figure and who is told when it is near.
9. **Whether Burro is offered to people under 18.** If it is not, say so in Burro's own terms. A parent who types a child's school sends data about a child either way. The provider asks for zero retention before a child's data is processed.
10. **Who accepts the terms.** They bind a business, and whoever accepts must have the power to bind it. `BURRO_MODEL_TERMS_ACCEPTED` should name this provider only after that person has read the Services Agreement, the agreement on data processing and the Usage Policies at the addresses below, and has decided points 1 to 3.

## Pages read

All on 23 September 2026.

| Page | Address | Its own date |
|---|---|---|
| API overview and authentication | <https://developers.openai.com/api/reference/overview> | |
| Create a model response | <https://developers.openai.com/api/reference/resources/responses/methods/create> | |
| Chat Completions | <https://developers.openai.com/api/reference/resources/chat> | |
| Structured outputs | <https://developers.openai.com/api/docs/guides/structured-outputs> | |
| Error codes | <https://developers.openai.com/api/docs/guides/error-codes> | |
| Rate limits | <https://developers.openai.com/api/docs/guides/rate-limits> | |
| Pricing | <https://developers.openai.com/api/docs/pricing> | |
| Models | <https://developers.openai.com/api/docs/models/all> and the page of each model named | |
| Deprecations | <https://developers.openai.com/api/docs/deprecations> | Latest entry 11 September 2026 |
| Prompt caching | <https://developers.openai.com/api/docs/guides/prompt-caching> | |
| Reasoning | <https://developers.openai.com/api/docs/guides/reasoning> | |
| Using GPT-6 | <https://developers.openai.com/api/docs/guides/latest-model> | |
| Data controls | <https://developers.openai.com/api/docs/guides/your-data> | |
| Migrate to the Responses API | <https://developers.openai.com/api/docs/guides/migrate-to-responses> | |
| Text generation | <https://developers.openai.com/api/docs/guides/text> | |
| Flex processing | <https://developers.openai.com/api/docs/guides/flex-processing> | |
| Safety best practices | <https://developers.openai.com/api/docs/guides/safety-best-practices> | |
| Safety classifiers | <https://developers.openai.com/api/docs/guides/safety-checks> | |
| Misalignment monitoring | <https://developers.openai.com/api/docs/guides/safety-checks/misalignment-monitoring> | |
| Under-18 guidance | <https://developers.openai.com/api/docs/guides/safety-checks/under-18-api-guidance> | |
| Supported countries | <https://developers.openai.com/api/docs/supported-countries> | |
| Cookbook: how to handle rate limits | <https://developers.openai.com/cookbook/examples/how_to_handle_rate_limits> | |
| The Python library's README | <https://github.com/openai/openai-python> | |
| Services Agreement | <https://openai.com/policies/services-agreement/> | Updated 1 December 2025, in force 1 January 2026 |
| Data Processing Addendum | <https://openai.com/policies/data-processing-addendum/> | Updated 1 December 2025, in force 1 January 2026 |
| Usage policies | <https://openai.com/policies/usage-policies/> | In force 29 October 2025 |
| Service terms | <https://openai.com/policies/service-terms/> | Updated 21 September 2026 |
| Service credit terms | <https://openai.com/policies/service-credit-terms/> | |
| Sub-processor list | <https://openai.com/policies/sub-processor-list/> | Updated 9 July 2026 |
| Sharing and publication policy | <https://openai.com/policies/sharing-publication-policy/> | Updated 14 November 2022 |
| Enterprise privacy | <https://openai.com/enterprise-privacy/> | Updated 8 January 2026 |
| Business data | <https://openai.com/business-data/> | |
| Privacy policy | <https://openai.com/policies/row-privacy-policy/> | Updated 6 February 2026 |
| Terms of use, as served in Europe | <https://openai.com/policies/terms-of-use/> | For people, not for the API |
| Design guidelines | <https://openai.com/brand/> | |
