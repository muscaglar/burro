# Google Gemini, from its own documents

Read on 23 September 2026. A dated snapshot: model names, prices and terms change often. Re-check before relying on a figure.

This is one of four reports, one a provider. The same nine questions were put to each.

It covers the Gemini API for developers, which Google also calls the Gemini Developer API. It covers Vertex AI where that differs. Google Cloud's documents now call Vertex AI "Gemini Enterprise Agent Platform". This report says Vertex AI, because Google's own Gemini API pages still do.

## How this was read

| Point | What it means for you |
|---|---|
| Every page was read through a reader that extracts, not the raw page | A quoted sentence may differ from the source by a word. Check the wording at the address given before it goes into a privacy notice or a contract |
| Raw copies of the pages were not downloaded | Examples marked "copied" are as read through the reader. Line breaks and spacing may differ |
| No web search was made | Only known addresses were read. Anything Google publishes elsewhere was not found |
| Long pages were read in part | The API reference for `generateContent` and several Google Cloud pages were not read to the end. Where a fact came from Google's published API definition instead, the table says so |
| No key, and no call to the provider | Nothing here was tested against the live service |
| Nothing here is legal advice | |

"Read" in a table below means read at Google's own address on the day. "Not read" means it is an inference, or the page did not say.

## In short

| Question | Answer | Read |
|---|---|---|
| Can it do the job | Yes. One POST, a key in a header, JSON back | Read |
| Is the schema enforced | Google says the answer is "a syntactically valid JSON string matching the provided schema". Keywords it does not support are ignored, not refused | Read |
| Which API | There are two. `generateContent` keeps nothing of its own and is called "legacy". Interactions is the one Google recommends, and it stores every call for 55 days unless told not to | Read |
| Smallest model fit for the job | `gemini-3.5-flash-lite`. `gemini-3.1-flash-lite` is cheaper and may retire from 7 May 2027 | Read |
| Cost of 1,000 searches | $1.65 on `gemini-3.5-flash-lite`, not cached, before thinking tokens | Worked out from prices that were read |
| Where the text is processed | No region can be chosen on the Gemini API. "any country in which Google or its agents maintain facilities" | Read |
| How long the text is kept | 55 days, to watch for misuse. It cannot be turned off on the Gemini API | Read |
| Is it used to improve models | Paid: no. Free: yes, and people at Google may read it | Read |
| May Burro use the free tier | No. "You may use only Paid Services when making API Clients available to users in the European Economic Area, Switzerland, or the United Kingdom." | Read |
| Zero retention | Not on the Gemini API. On Vertex AI, by asking Google for an exception | Read |
| Data processing agreement | Yes. It comes with the terms for Paid Services. Nothing is signed | Read |
| A safeguard for a transfer from the UK | The Data Privacy Framework with its UK Extension, and standard contractual clauses where that does not apply | Read |
| Age | 18 or over, and the product must not be "directed towards or ... likely to be accessed by individuals under the age of 18" | Read |

The adapter can be built and tested. Before a real person's sentence is sent, the founder has eight things to settle. They are at the end.

### Where Google's own pages disagree

These were found on the day. Each one is a reason to test against the live service before relying on the page.

| Matter | One page says | Another says |
|---|---|---|
| Whether the Interactions API is finished | "As of June 2026, it is Generally Available" (the guide, read as a page) | "The Interactions API is currently in Beta. Features and schemas are subject to breaking changes." (the markdown copy of the same guide) |
| The address of the Interactions API | `/v1beta/interactions` (the guide, the reference, the key page) | `/v1beta2/interactions` (the migration guide, as read) |
| The field that carries a schema in `generateContent` | `generationConfig.responseFormat.text.schema` (the guide) | `generationConfig.responseMimeType` with `responseSchema` or `responseJsonSchema` (the reference, the API definition, the migration guide) |
| The first REST sample for a schema in `generateContent` | Its braces do not balance as read, in two separate readings | |
| Whether free-tier text improves products | "Used to improve our products: Yes" (the price list) | For a developer in the UK, the paid rules "apply to all Services" (the terms) |
| Where the key goes | "All requests to the Gemini API must include a `x-goog-api-key` header" (the reference) | `?key=$GEMINI_API_KEY` in the address (Google's cookbook, and one sample in the reference as read) |
| Whether any model is processed in the UK on Vertex AI | One reading of the table: Gemini 2.5 Flash, in `europe-west2` | A second reading of the same table: no model |

## 1. The call

### The two APIs

| | `generateContent` | Interactions |
|---|---|---|
| What Google says of it | "While it is now considered legacy, the original `generateContent` API remains fully supported." | "The Interactions API is the best way to build with Gemini models and agents." |
| A date it will be shut | None given on any page read | |
| Does it store the call | No feature stores it. The 55-day record for misuse still applies | Yes, by default. "By default, the API stores all Interaction objects (`store=true`)" |
| How long | | "Paid tier: The system retains interactions for **55 days**." "Free tier: The system retains interactions for **1 day**." |
| How to stop it | Nothing to do | "you can set `store=false` in your request" |
| Where the model's name goes | In the address | In the body |
| How a block or a cut-off is shown | Field by field. See section 3 | `status` only. Where a block is shown was not found |

Sources: <https://ai.google.dev/gemini-api/docs/interactions>, <https://ai.google.dev/gemini-api/docs/migrate-to-interactions>, <https://ai.google.dev/gemini-api/docs/zdr>.

The recommendation is `generateContent`, and the reasons are in "For the builder". Both are set out here so that either can be built.

### `generateContent`

| Item | Value | Read |
|---|---|---|
| Address | `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent` | Read |
| Method | `POST` | Read |
| Header that carries the key | `x-goog-api-key: <key>` | Read |
| May the key go in a header | Yes. "All requests to the Gemini API must include a `x-goog-api-key` header with your API key." | Read |
| Key in the address | Older samples use `?key=`. Burro must never do so | Read |
| Other header | `Content-Type: application/json` | Read |
| Instructions | `system_instruction.parts[].text`. "Developer set system instruction(s). Currently, text only." | Read |
| The person's turn | `contents[].parts[].text` | Read |
| The name of the key in the environment | `GEMINI_API_KEY`. Google's own libraries also read `GOOGLE_API_KEY`, and "If both are set, `GOOGLE_API_KEY` takes precedence." Burro reads only the first | Read |

Sources: <https://ai.google.dev/api>, <https://ai.google.dev/api/generate-content>, <https://ai.google.dev/gemini-api/docs/generate-content/text-generation>, <https://ai.google.dev/gemini-api/docs/api-key>.

### Interactions

| Item | Value | Read |
|---|---|---|
| Address | `https://generativelanguage.googleapis.com/v1beta/interactions` | Read, with the disagreement above |
| Method | `POST` | Read |
| Header | `x-goog-api-key: <key>` | Read |
| Model | `"model": "<id>"` in the body | Read |
| Instructions | `"system_instruction": "<text>"`, a plain string | Read |
| The person's turn | `"input": "<text>"` | Read |
| Storing | `"store": false` must be sent on every call | Read |
| To delete a stored call | `DELETE https://generativelanguage.googleapis.com/v1beta/interactions/{id}` | Read |

Source: <https://ai.google.dev/api/interactions-api>.

### Fields of the body that matter, for `generateContent`

| Field | Send | Note | Read |
|---|---|---|---|
| `system_instruction` | The fixed instructions | The samples spell it this way. The reference names it `systemInstruction` | Read |
| `contents` | One item, one part, the person's turn | | Read |
| `generationConfig.responseMimeType` | `"application/json"` | "`application/json`: JSON response in the response candidates." | Read, in the API definition |
| `generationConfig.responseJsonSchema` | The schema | "If set, `response_schema` must be omitted, but `response_mime_type` is required." | Read, in the API definition |
| `generationConfig.maxOutputTokens` | A fixed number | "The maximum number of tokens to include in a response candidate." Whether thinking tokens count against it was not found | Read |
| `generationConfig.thinkingConfig.thinkingLevel` | `"minimal"` | See below | Read |
| `generationConfig.candidateCount` | Leave out, or 1 | | Read |
| `safetySettings` | Leave out | "If the threshold is not set, the default block threshold is **Off** for Gemini 2.5 and 3 models." | Read |
| `cachedContent` | Never | It stores the text. See section 7 | Read |
| `tools` | Never | Search and Maps grounding store the prompt for 30 days, and "There is no way to disable the storage" | Read |

**Thinking cannot be turned off on the current small models.** "Gemini 3 Flash and Flash-Lite also do not support full thinking-off." The lowest level is `minimal`, which is the default on `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite`. On `gemini-3.8-flash` and `gemini-3.7-flash`, `minimal` is "Not supported (error)" and the default is `medium`. Thinking tokens are paid for as output. Source: <https://ai.google.dev/gemini-api/docs/generate-content/thinking>.

### Vertex AI, where it differs

| Item | Vertex AI | Read |
|---|---|---|
| Host | `https://aiplatform.googleapis.com`, or `https://aiplatform.eu.rep.googleapis.com` for the EU | Read |
| Path | Holds a project and a location. The full path was not read reliably | Not read |
| Credentials | "You can authenticate ... by using Application Default Credentials (ADC) or by using an API key. ADC is the recommended method." And: "We recommend using an API key for testing and using application default credentials for production." | Read |
| What that means for Burro | Away from Google Cloud, Application Default Credentials need a token signed with a private key. The Python standard library cannot sign one. So Vertex AI means a dependency, or hosting on Google Cloud, or a key that Google recommends for testing only | Inference |
| The body and the answer | The same `generateContent` shape | Not read on the day |

Sources: <https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/quickstart>, <https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/api-keys>, <https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations>.

## 2. Structured output

| Point | In the provider's words | Read |
|---|---|---|
| How | Set the type of the answer to `application/json` and give a schema | Read |
| What is promised | "The model will then generate a response that is a syntactically valid JSON string matching the provided schema." | Read |
| What is not promised | "While structured output guarantees syntactically correct JSON, it does not guarantee the values are semantically correct. Always validate the final output in your application code before using it." | Read |
| Keywords it does not know | "Not all features of the JSON Schema specification are supported. The model ignores unsupported properties." | Read |
| A schema that is too big | "The API may reject very large or deeply nested schemas. If you encounter errors, try simplifying your schema by shortening property names, reducing nesting, or limiting the number of constraints." | Read |
| The order of fields | "the model will produce outputs in the same order as the keys in the schema" | Read |
| Which models | The guide's table lists Gemini 3.1 Flash-Lite, 3.5 Flash, 3.1 Pro Preview, 2.5 Pro, 2.5 Flash and 2.5 Flash-Lite. It does not list 3.5 Flash-Lite. That model's own page says "Structured outputs: Supported" | Read |

Sources: <https://ai.google.dev/gemini-api/docs/generate-content/structured-output>, <https://ai.google.dev/gemini-api/docs/structured-output>, <https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite>.

### What it accepts and refuses

| Part of JSON Schema | Taken | Where it was read |
|---|---|---|
| `type`: `string`, `number`, `integer`, `boolean`, `object`, `array`, `null` | Yes | The guide |
| `enum` | Yes, "for strings and numbers" | The guide and the API definition |
| A field that may be null | Yes, as `{"type": ["string", "null"]}` | The guide |
| `properties`, `required` | Yes | The guide |
| `additionalProperties` | Yes. "Can be a boolean or a schema." | The guide |
| `items`, `prefixItems`, `minItems`, `maxItems` | Yes | The guide |
| `minimum`, `maximum` | Yes | The guide |
| `format` | Yes, "such as `date-time`, `date`, `time`" | The guide |
| `title`, `description` | Yes | The guide |
| `$defs`, `$ref`, `$id`, `$anchor` | Yes | The API definition. The guide shows `"$ref": "#"` |
| `anyOf`, `oneOf` | Yes. `oneOf` is "interpreted the same as `anyOf`" | The API definition |
| `minLength`, `maxLength`, `pattern`, `const`, `default`, `allOf`, `not` | Not listed, so ignored | Inference from the list |
| A limit on depth | No number is given | Not found |
| A limit on the number of fields or of enum values | No number is given | Not found |
| `$ref` with other keywords beside it | Refused. "If `$ref` is set on a sub-schema, no other properties, except for than those starting as a `$`, may be set." | The API definition |
| A schema that refers to itself | "Cyclic references are unrolled to a limited degree and, as such, may only be used within non-required properties." | The API definition |

The API definition is Google's published file at <https://github.com/googleapis/googleapis/blob/master/google/ai/generativelanguage/v1beta/generative_service.proto>. It lists the keywords for `responseJsonSchema` one by one. The older field, `responseSchema`, takes "a subset of the OpenAPI schema" and is not the one to use.

### How Burro's schema fits

`SCHEMA` in `claude.py` was printed and its keywords counted.

| Point | Burro's schema | Fits |
|---|---|---|
| Keywords used | `$defs`, `$ref`, `type`, `enum`, `properties`, `required`, `additionalProperties`, `items` | Yes. Every one is on the list |
| Keywords `_plain` strips | `maxLength`, `minLength`, `maximum`, `minimum`, `maxItems`, `minItems`, `title`, `description` | Yes. All but `maxLength` and `minLength` would be taken here. Stripping them does no harm. Code checks the limits |
| Optional or nullable fields | None | Yes |
| Unions | None | Yes |
| `$ref` with a keyword beside it | None in the definitions printed. Not checked in all 25 | Likely |
| Size | 25 definitions, 19 enums, 103 enum values, 50 fields, about 7,700 characters | Not known. No limit is published |
| Depth | Four levels once references are followed | Not known. No limit is published |
| Case of an enum value | The guide does not say the case is kept. `claude.py` lowers it already | Yes |

Whether the schema is accepted as it stands can only be settled by one live call.

### A refusal, and an answer cut short

| Case | What comes back in `generateContent` | Read |
|---|---|---|
| The prompt is blocked | HTTP 200. `promptFeedback.blockReason` is set. "If set, the prompt was blocked and no candidates are returned." | Read |
| The answer is blocked | HTTP 200. `finishReason` is `SAFETY`, `PROHIBITED_CONTENT`, `BLOCKLIST`, `SPII` or `RECITATION`. The text may be missing or part of an answer | Read |
| The answer is cut short | HTTP 200. `finishReason` is `MAX_TOKENS`. The text is JSON that stops part way | Read for the value; the broken JSON is an inference |
| Some harm is always blocked | "These types of harm are always blocked and cannot be adjusted." | Read |

None of these is an HTTP error. The adapter must read the body to find them, and each becomes `ModelError`.

## 3. What "finished" means

### `generateContent`

The answer is whole when `candidates[0].finishReason` is `STOP` and `promptFeedback.blockReason` is absent. Anything else is not an answer.

| `finishReason` | Meaning, in Google's words | Burro |
|---|---|---|
| `STOP` | "Natural stop point of the model or provided stop sequence." | The answer |
| `MAX_TOKENS` | "The maximum number of tokens as specified in the request was reached." | error |
| `SAFETY` | "The response candidate content was flagged for safety reasons." | error |
| `RECITATION` | "The response candidate content was flagged for recitation reasons." | error |
| `LANGUAGE` | "The response candidate content was flagged for using an unsupported language." | error |
| `OTHER` | "Unknown reason." | error |
| `BLOCKLIST` | "Token generation stopped because the content contains forbidden terms." | error |
| `PROHIBITED_CONTENT` | "Token generation stopped for potentially containing prohibited content." | error |
| `SPII` | "Token generation stopped because the content potentially contains Sensitive Personally Identifiable Information (SPII)." | error |
| `MALFORMED_FUNCTION_CALL` | "The function call generated by the model is invalid." | error |
| `UNEXPECTED_TOOL_CALL` | "Model generated a tool call but no tools were enabled in the request." | error |
| `TOO_MANY_TOOL_CALLS` | "Model called too many tools consecutively, thus the system exited execution." | error |
| `IMAGE_SAFETY`, `IMAGE_PROHIBITED_CONTENT`, `IMAGE_OTHER`, `NO_IMAGE`, `IMAGE_RECITATION` | About images | error |
| `FINISH_REASON_UNSPECIFIED` | "Default value. This value is unused." | error |
| Any value not in this list | Google adds values over time | error |

`SPII` matters to Burro. A sentence that names a workplace or a school could trip it. If it does, the rules answer in the model's place.

| `promptFeedback.blockReason` | Meaning |
|---|---|
| `SAFETY` | "Prompt was blocked due to safety reasons." |
| `OTHER` | "Prompt was blocked due to unknown reasons." |
| `BLOCKLIST` | "Prompt was blocked due to the terms which are included from the terminology blocklist." |
| `PROHIBITED_CONTENT` | "Prompt was blocked due to prohibited content." |
| `IMAGE_SAFETY` | About images |

The list of values was read in Google's published API definition, because the reference page was read in part. The part read showed the first nine. Source: <https://ai.google.dev/api/generate-content>.

### Interactions

The answer is whole when `status` is `completed`.

| `status` | Meaning, in Google's words | Burro |
|---|---|---|
| `completed` | "The interaction is completed." | The answer |
| `incomplete` | "The interaction is completed, but contains incomplete results (e.g. hitting max_tokens)." | error |
| `failed` | "The interaction failed." | error |
| `cancelled` | "The interaction was cancelled." | error |
| `in_progress`, `queued`, `requires_action` | Not finished | error |

The text is in `steps[]`, in the step whose `type` is `model_output`, in `content[]` items whose `type` is `text`. The page of errors lists codes for a blocked answer, such as `safety`, `spii` and `prohibited_content`. It does not say which field of the answer holds them. That was not found.

## 4. Usage

| What | `generateContent`, in `usageMetadata` | Interactions, in `usage` | Read |
|---|---|---|---|
| Tokens in | `promptTokenCount`. "When `cachedContent` is set, this is still the total effective prompt size meaning this includes the number of tokens in the cached content." | `total_input_tokens` | Read |
| Tokens read from a cache | `cachedContentTokenCount`. "Number of tokens in the cached part of the prompt" | `total_cached_tokens` | Read |
| Tokens out | `candidatesTokenCount`. "Total number of tokens across all the generated response candidates." | `total_output_tokens` | Read |
| Thinking tokens | `thoughtsTokenCount`. "Number of tokens of thoughts for thinking models." | `total_thought_tokens` | Read |
| Total | `totalTokenCount` | `total_tokens` | Read |

Three things differ from other providers.

| Point | Evidence | Read |
|---|---|---|
| Tokens in include the cached ones | The sentence quoted above | Read |
| Tokens out do not include thinking, and thinking is billed as output | "response pricing is the sum of output tokens and thinking tokens". In Google's sample answer, 7 in, 20 out and 22 thinking make a total of 49 | Read |
| A count of zero may be left out of the answer | Google's sample answers leave out the cached count when nothing was cached | Inference from the samples |

Whether the schema is counted among the tokens in was not found. The rule of thumb is "a token is equivalent to about 4 characters". Source: <https://ai.google.dev/gemini-api/docs/tokens>.

## 5. Errors

Google documents the statuses for the Interactions API. The page for `generateContent` has moved, and the old table of statuses was not found. The HTTP status is the same in both, so the adapter decides on the status alone.

| HTTP | Code in Interactions | Name in `generateContent` | Meaning, in Google's words | Burro |
|---|---|---|---|---|
| 400 | `invalid_request` | `INVALID_ARGUMENT` | "The request payload is malformed or contains invalid parameters." A schema that is refused lands here | error |
| 400 | `failed_precondition` | `FAILED_PRECONDITION` | "a prerequisite is not met (for example, disabled billing)" | error |
| 400 | `parameter_unknown` | | "The request contains an unknown parameter." | error |
| 401 | `authentication` | `UNAUTHENTICATED` | "The API key is missing, invalid, or expired." | error |
| 402 | `payment_required` | | "Your Prepay credit balance is depleted." "Don't retry" | capped |
| 403 | `permission_denied` | `PERMISSION_DENIED` | "Your API key does not have permission for this resource." | error |
| 404 | `not_found`, `model_not_found` | `NOT_FOUND` | "The specified model was not found." A retired model lands here | error |
| 408 | | | Named as one to retry. No more is said | timeout |
| 409 | `already_exists`, `aborted` | | A conflict | error |
| 416 | `out_of_range` | | "Request parameter is outside the valid range." | error |
| 429 | `rate_limit_exceeded` | `RESOURCE_EXHAUSTED` | "You have exceeded the per-minute or per-second request or token limit." | capped |
| 429 | `quota_exceeded` | `RESOURCE_EXHAUSTED` | "You have exceeded your daily quota." | capped |
| 429 | `too_many_requests` | `RESOURCE_EXHAUSTED` | "You have made too many requests in a short period of time." | capped |
| 429 | | `RESOURCE_EXHAUSTED` | The limit on spending in ten minutes. "the API returns a `429 RESOURCE_EXHAUSTED` error" | capped |
| 499 | `cancelled` | | "The client cancelled the request before it completed." | error |
| 500 | `api_error` | `INTERNAL` | "An unexpected error occurred on the server." | error |
| 501 | `unimplemented` | | "The operation or feature is not implemented or supported." | error |
| 503 | `service_unavailable` | `UNAVAILABLE` | "The service is temporarily overloaded or down." | error |
| 504 | `deadline_exceeded` | `DEADLINE_EXCEEDED` | "The request didn't finish within the deadline." | timeout |
| Any 3xx | | | None is documented | error, and never followed |
| Any other status | | | "Any error code not listed above falls back to the `snake_case` version of the HTTP status." | error |
| 200, prompt blocked | | | `promptFeedback.blockReason` is set | error |
| 200, not finished | | | `finishReason` is not `STOP`, or `status` is not `completed` | error |
| 200, not JSON, or too big | | | | error |
| No answer in time | | | The adapter's own clock | timeout |

The names in the third column were read for 429 and 503 on Google's pages. The rest are the standard names of Google's APIs and were not read for this API on the day.

| Point | In the provider's words | Read |
|---|---|---|
| The shape of an error in Interactions | "All errors from the Interactions API return an `error` object containing a `code` and `message`." | Read |
| The shape in `generateContent` | `error.code` is a number, with `error.message`, `error.status` and `error.details` | Read in Google's general guide to its APIs, not for this API |
| The message repeats the request | Google's own sample: "The value 'invalid_tool_type_xyz' is not supported for 'type' at 'tools[0]'." | Read |
| What Google says to retry | "Only retry on transient errors (like 429, 408, or 5xx). Do not retry on client errors (like 400, 402, or 403)." | Read |

Because a message can repeat what was sent, the adapter must never read, log or raise `error.message`. Burro has decided on no retries, which is stricter than Google's advice and fits it.

Sources: <https://ai.google.dev/gemini-api/docs/api-errors>, <https://ai.google.dev/gemini-api/docs/troubleshooting>, <https://ai.google.dev/gemini-api/docs/rate-limits>, <https://google.aip.dev/193>.

### The limits on calls and on spending

| Limit | Value | Read |
|---|---|---|
| What is counted | Requests a minute, tokens in a minute, requests a day. "Rate limits are applied per project, not per API key." | Read |
| The figures for each model | Shown in Google AI Studio for the account. Not on the page | Not found |
| Tier 1 | "Set up and link an active billing account". Cap on the bill: $250 a month | Read |
| Tier 2 | "Paid $100 + 3 days from first successful payment". Cap: $2,000 | Read |
| Tier 3 | "Paid $1,000 + 30 days from first successful payment". Cap: $20,000 to $100,000 and more | Read |
| Spending in ten minutes | Tier 1: $10. Tier 2: $50. Tier 3: $200. Beyond it, 429 | Read |
| When the tier's cap is reached | "service is paused for all projects". The status is not given | Read |
| A cap of your own | "You can set your own project-level spend caps in AI Studio" | Read |
| Prepaid credit at nil | "all API keys in all projects linked to that billing account will stop working simultaneously. Requests then fail with an HTTP 402 Payment Required error until you add credits." | Read |

Source: <https://ai.google.dev/gemini-api/docs/billing>.

## 6. Models

### Offered today, for text

| Model | Kind | Released | Earliest shut-down | Read |
|---|---|---|---|---|
| `gemini-3.8-flash` | Stable | 2 September 2026 | None announced | Read |
| `gemini-3.7-flash` | Stable | 13 August 2026 | None announced | Read |
| `gemini-3.6-flash` | Stable | 21 July 2026 | None announced | Read |
| `gemini-3.5-flash` | Stable | 19 May 2026 | None announced | Read |
| `gemini-3.5-flash-lite` | Stable | 21 July 2026 | None announced | Read |
| `gemini-3.1-flash-lite` | Stable | 7 May 2026 | 7 May 2027. Replacement: `gemini-3.5-flash-lite` | Read |
| `gemini-3.1-pro-preview` | Preview | 19 February 2026 | None announced | Read |
| `gemini-3-flash-preview` | Preview | 17 December 2025 | None announced. Replacement: `gemini-3.6-flash` | Read |
| `gemini-2.5-pro` | Stable | 17 June 2025 | None announced. Closed to new users | Read |
| `gemini-2.5-flash` | Stable | 17 June 2025 | None announced. Closed to new users | Read |
| `gemini-2.5-flash-lite` | Stable | 22 July 2025 | None announced. Closed to new users | Read |

| Point | In the provider's words | Read |
|---|---|---|
| What a date means | "The shutdown dates listed in the table indicate the _earliest possible dates_ on which a model might be retired." | Read |
| The 2.5 models | "To ensure reliable performance for everyone, we are limiting access to the 2.5 models to users who have actively used them in the past." | Read |
| A stable name | "Points to a specific stable model. Stable models usually don't change." | Read |
| A preview | "will be deprecated with at least 2 weeks notice" | Read |
| A name ending `-latest` | "This alias will get hot-swapped with every new release." Burro must not use one | Read |
| How fast models have gone | `gemini-2.0-flash` was released on 5 February 2025 and shut on 1 June 2026, sixteen months later | Read |

Sources: <https://ai.google.dev/gemini-api/docs/models>, <https://ai.google.dev/gemini-api/docs/deprecations>.

### Prices, in US dollars for a million tokens, paid tier, standard service

| Model | In | Out, thinking included | Read from cache | Read |
|---|---|---|---|---|
| `gemini-2.5-flash-lite` | 0.10 | 0.40 | 0.01 | Read |
| `gemini-3.1-flash-lite` | 0.25 | 1.50 | 0.025 | Read |
| `gemini-3.5-flash-lite` | 0.30 | 2.50 | 0.03 | Read |
| `gemini-2.5-flash` | 0.30 | 2.50 | 0.03 | Read |
| `gemini-3.8-flash`, to 31 December 2026 | 0.75 | 3.75 | 0.075 | Read |
| `gemini-3.8-flash`, from 1 January 2027 | 1.50 | 7.50 | 0.15 | Read |
| `gemini-3.5-flash` | 1.50 | 9.00 | 0.15 | Read |
| `gemini-3.1-pro-preview`, prompts to 200,000 tokens | 2.00 | 12.00 | 0.20 | Read |

| Point | Value | Read |
|---|---|---|
| Storing a cache you make yourself | $1.00 for a million tokens an hour | Read |
| A change of price | "effective 30 days after they are posted unless otherwise specified" | Read |
| Other services | Batch and Flex cost about half and are slower. Priority costs about 1.8 times as much | Read |
| Vertex AI's prices | Not read | Not read |

Source: <https://ai.google.dev/gemini-api/docs/pricing>.

### The three small models

| | `gemini-3.5-flash-lite` | `gemini-3.1-flash-lite` | `gemini-2.5-flash-lite` |
|---|---|---|---|
| Tokens in, at most | 1,048,576 | 1,048,576 | 1,048,576 |
| Tokens out, at most | 65,536 | 65,536 | 65,536 |
| Structured output | Supported | Supported | Supported |
| Caching | Supported | Supported | Supported |
| Thinking | Supported, `minimal` by default | Supported, `minimal` by default | Supported, can be set to nil |
| Open to a new account | Yes | Yes | No |
| Earliest shut-down | None announced | 7 May 2027 | None announced |

All read, at each model's own page under <https://ai.google.dev/gemini-api/docs/models/>.

### The cache

| Point | In the provider's words | Read |
|---|---|---|
| On by default | "Implicit caching is enabled by default for all Gemini 2.5 and newer models." | Read |
| What it saves | "We automatically pass on cost savings if your request hits caches." | Read |
| How sure | There is "no cost saving guarantee" | Read |
| The smallest prompt that is cached | 4,096 tokens for Gemini 3.8, 3.7, 3.6 and 3.5 Flash and 3.1 Pro Preview. 2,048 for Gemini 2.5 Flash and Pro. **No Flash-Lite model is in the table** | Read |
| How to help it | "Try putting large and common contents at the beginning of your prompt" | Read |
| What it is | "strictly in RAM (not at-rest), isolated at the project level, and has a 24-hour TTL" | Read |
| Can it be turned off | On Vertex AI, "This feature can be disabled at the project level." On the Gemini API no way was found | Read for Vertex AI |
| A cache you make yourself | Stored until it expires. "If not set, the TTL defaults to 1 hour." The Interactions API does not support it | Read |

Burro's prompt is about 3,000 tokens. That is under the 4,096 the table gives for the Flash models. So the cache may never be used. Only a live call that returns a `cachedContentTokenCount` above nil would show that it is. Source: <https://ai.google.dev/gemini-api/docs/caching>.

### The smallest model fit for the job

`gemini-3.5-flash-lite`. It is the newest of the small models, it is open to a new account, no date is set for its retirement, its own page says it supports structured output, and its context is 300 times what the job needs.

`gemini-3.1-flash-lite` does the same on paper for 45 cents less in every 1,000 searches. Its earliest shut-down is 7 May 2027, which is seven months away.

`gemini-2.5-flash-lite` is the cheapest, and a new account cannot use it.

Whether any of them reads Burro's sentences well is not known until the golden queries are run. No evidence of quality was found, and none is claimed.

### 1,000 searches, at 3,000 tokens in and 300 out

"Cached" assumes 2,700 of the 3,000 tokens are the fixed instructions and are read from the cache, and 300 are not. This is the same split as in the other three reports.

| Model | Not cached | Cached |
|---|---|---|
| `gemini-3.5-flash-lite` | $1.65 | $0.92 |
| `gemini-3.1-flash-lite` | $1.20 | $0.59 |
| `gemini-2.5-flash-lite` | $0.42 | $0.18 |
| `gemini-3.8-flash`, to 31 December 2026 | $3.38 | $1.55 |
| `gemini-3.8-flash`, from 1 January 2027 | $6.75 | $3.11 |

The sums, for `gemini-3.5-flash-lite`: not cached, 3.0 x 0.30 + 0.3 x 2.50 = 1.65. Cached, 2.7 x 0.03 + 0.3 x 0.30 + 0.3 x 2.50 = 0.92.

| What would move the figure | By how much |
|---|---|
| Thinking tokens, which cannot be turned off and are billed as output | For each 100 thinking tokens a call: 25 cents more on `gemini-3.5-flash-lite`, 15 cents on `gemini-3.1-flash-lite` |
| The cache is never used, because the prompt is too short | The "not cached" column |
| The schema is counted among the tokens in | Some 1,900 tokens more a call at 4 characters a token: 57 cents more on `gemini-3.5-flash-lite` |
| A move to `gemini-3.8-flash` | Twice the cost this year, four times from January |

Plan on not cached, with 100 thinking tokens a call: **about $1.90 for 1,000 searches** on `gemini-3.5-flash-lite`. Token counts are estimates until they are measured.

## 7. What happens to a person's text

Four documents apply to the paid Gemini API. They are the Gemini API Additional Terms of Service (effective 23 March 2026), the Google APIs Terms of Service (last modified 9 November 2021), the Data Processing Addendum for Products Where Google is a Data Processor (version 10, 7 May 2026), and the Generative AI Prohibited Use Policy (last modified 17 December 2024).

### The questions

| Question | Answer, in the provider's words | Address | Read |
|---|---|---|---|
| Is it used to train, on the paid tier | "Google doesn't use your prompts (including associated system instructions, cached content, and files such as images, videos, or documents) or responses to improve our products" | <https://ai.google.dev/gemini-api/terms> | Read |
| Is it used to train, on the free tier | "Google uses the content you submit to the Services and any generated responses to provide, improve, and develop Google products and services and machine learning technologies" | same | Read |
| Do people read it, on the free tier | "human reviewers may read, annotate, and process your API input and output." "**Do not submit sensitive, confidential, or personal information to the Unpaid Services.**" | same | Read |
| Does the free tier differ for a developer in the UK | "If you're in the European Economic Area, Switzerland, or the United Kingdom, the terms under "How Google uses Your Data" in "Paid Services" apply to all Services, including Google AI Studio and unpaid quota in the Gemini API, even though they are offered free of charge." | same | Read |
| What makes the API paid | "Your access to Gemini API is a "Paid Service" only when accessing the API through a Cloud Project associated with an active billing account." | same | Read |
| How long is it kept | "Google retains the following data for fifty-five (55) days for the purposes of detecting and preventing violations of the Prohibited Use Policy". The data is "Prompts", "Contextual Information" and "Output" | <https://ai.google.dev/gemini-api/docs/usage-policies> | Read |
| What is the record used for | "it is used solely for the purpose of policy enforcement and preventing policy violations. It is not used to train or fine-tune any AI/ML models besides those used specifically for policy enforcement." | same | Read |
| Do people read the record | "authorized Google employees may assess the flagged content". "Data can be accessed for human review only by authorized Google employees via an internal governance assessment and review management platform." | same | Read |
| Can the record be turned off | "If your workload requires guaranteed zero data retention or enterprise data processing agreements, use Vertex AI." | <https://ai.google.dev/gemini-api/docs/zdr> | Read |
| Where is it processed | "This data may be stored transiently or cached in any country in which Google or its agents maintain facilities." | <https://ai.google.dev/gemini-api/terms> | Read |
| Can a region be chosen | No way was found on any page of the Gemini API | | Not found |
| Is the UK an allowed place to offer the product | Yes. "United Kingdom" is in the list | <https://ai.google.dev/gemini-api/docs/available-regions> | Read |
| Is there a processing agreement | Google "will process your prompts and responses in accordance with the Data Processing Addendum for Products Where Google is a Data Processor" | <https://ai.google.dev/gemini-api/terms> | Read |
| Is the Gemini API named in it | "Gemini API Paid Services" is in the list of services. Last update 27 April 2026 | <https://business.safety.google/services/> | Read |
| How is it accepted | It "is entered into by Google and Partner and supplements the Agreement." It comes with the terms. No step to sign or tick was found | <https://business.safety.google/processorterms/> | Read; the absence of a step is an inference |
| Who is who | "Google is a processor of Partner Personal Data; Partner is a controller or processor, as applicable" | same | Read |
| What else Google collects as a controller | Usage details, "which may include device identifiers, identifiers from cookies or tokens, and IP addresses". Burro's server makes the call, so the address would be the server's and not the person's | <https://ai.google.dev/gemini-api/terms> | Read; the second sentence is an inference |
| Logs a developer can turn on | "As a project owner you have the choice to opt-in to logging of Gemini API calls". Kept for up to 55 days. They may be shared with Google to train models. Leave them off | <https://ai.google.dev/gemini-api/docs/logs-policy> | Read |

### Zero retention

| | Gemini API | Vertex AI |
|---|---|---|
| The record for misuse | Kept for 55 days. No way to turn it off | "If you are in scope for prompt logging for abuse monitoring and want zero data retention, you can request an exception for abuse monitoring." |
| The cache in memory | 24 hours. "**This does not violate zero data retention.**" | 24 hours. "This feature can be disabled at the project level." |
| Interactions API | "you must explicitly set the `store` parameter to `false`" | "To achieve zero data retention, explicitly set store = false in your API requests." |
| A cache you make | "do not utilize the cached_content feature" | Not read |
| Grounding with Google Search | Stores for 30 days. "There is no way to disable the storage of this information" | Do not use it |
| Training | Not on the paid tier | "Google won't use your data to train or fine-tune any AI/ML models without your prior permission or instruction." |

Read. Sources: <https://ai.google.dev/gemini-api/docs/zdr>, <https://docs.cloud.google.com/vertex-ai/generative-ai/docs/vertex-ai-zero-data-retention>. How to ask for the exception, and whether Google grants it to a small company, was not found.

### A region, on Vertex AI

| Point | In the provider's words | Read |
|---|---|---|
| What decides the place | "The geographic location of this processing is determined by your choice of endpoint" | Read |
| The EU | The "European Union multi-region (eu) endpoint strictly covers data residency within EU member states." | Read |
| The UK | "Geographies outside the European Union political boundary, including the United Kingdom and Switzerland, are excluded from this endpoint" | Read |
| The global address | "Don't use the global endpoint if you have ML processing requirements, because you can't control or know which region your ML processing requests are sent to" | Read |
| Which models run in the EU | Gemini 3.8, 3.7, 3.6 and 3.5 Flash, 3.5 and 3.1 Flash-Lite, and the 2.5 models, as the table was read | Read once |
| Which models run in the UK | Two readings of the table disagree. Treat it as none | Not settled |

Source: <https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/data-residency>.

### UK and EU law

| Point | In the provider's words | Address | Read |
|---|---|---|---|
| The UK GDPR is covered | ""GDPR" means, as applicable: (a) the EU GDPR; and/or (b) the UK GDPR." | <https://business.safety.google/processorterms/> | Read |
| Where Google may process | "Google may process Partner Personal Data in any country in which Google or its Subprocessors maintain facilities." | same | Read |
| The safeguard for a transfer | "Google has adopted a Data Transfer Solution for any Restricted European Transfer". A Data Transfer Solution includes "the EU-US Data Privacy Framework, UK Extension to EU-US Data Privacy Framework, Swiss-US Data Privacy Framework" | same | Read |
| If that is not available | Standard contractual clauses apply, between Google and its subprocessors | same | Read |
| Google's certificate | "Google LLC (and its wholly-owned US subsidiaries unless explicitly excluded) has certified that it adheres to the DPF Principles." | <https://policies.google.com/privacy/frameworks> | Read |
| Subprocessors | "Information about Subprocessors is available at business.safety.google/subprocessors/" | <https://business.safety.google/processorterms/> | Read; the list itself was not |
| Help with an impact assessment | Google "will ... assist Partner in ensuring compliance with Partner's ... obligations relating to data protection impact assessments" | same | Read |
| Special category data | The addendum has no clause on it | same | Read |
| Deletion at the end | "Partner instructs Google to delete all remaining Partner Personal Data (including existing copies) from Google's systems at the end of the Term" | same | Read |
| Vertex AI's agreement | The Cloud Data Processing Addendum "is incorporated into the Agreement(s)" | <https://cloud.google.com/terms/data-processing-addendum> | Read in part |

### What a UK company must do first

The first four are Google's conditions. The rest are the regulator's. The Information Commissioner's Office says of its own guide: "Due to changes made by the Data (Use and Access) Act, this guidance is under review and may be subject to change."

| Step | Whose rule | In their words | Read |
|---|---|---|---|
| 1. Turn on billing before any real text is sent | Google | "You may use only Paid Services when making API Clients available to users in the European Economic Area, Switzerland, or the United Kingdom." | Read |
| 2. Keep a dated copy of the terms and the addendum | Good practice | They are the contract that Article 28 asks for | Not read |
| 3. Say in the privacy notice that Google receives the text | Google | "You will provide and adhere to a privacy policy for your API Client that clearly and accurately describes to users of your API Client what user information you collect and how you use and share such information (including for advertising) with Google and third parties." | Read |
| 4. Keep under-18s out | Google | See section 8 | Read |
| 5. Choose a lawful basis and a condition, and write them down | ICO | "you must identify both a lawful basis under Article 6 of the UK GDPR and a separate condition for processing under Article 9." "You must determine your condition for processing special category data before you begin this processing under the UK GDPR, and you should document it." | Read |
| 6. Do an impact assessment | ICO | "You need to complete a data protection impact assessment (DPIA) for any type of processing which is likely to be high risk." | Read |
| 7. Cover the transfer out of the UK | ICO | "Every restricted transfer **must** be covered by one of the following transfer mechanisms: UK adequacy regulations; appropriate safeguards; or an exception." | Read |
| 8. Leave Google's optional logging off, and share no datasets | Google | "Do not include personal, sensitive, or confidential information." | Read |

Sources for the regulator: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/a-guide-to-lawful-basis/special-category-data/>, <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/international-transfers-a-guide/>.

## 8. Terms that bind a product like this

| Matter | In the provider's words | What it means for Burro | Read |
|---|---|---|---|
| Age of the developer | "You must be 18 years of age or older to use the APIs." | | Read |
| Age of the people who use the product | "You also will not use the Services as part of a website, application, or other service ... that is directed towards or is likely to be accessed by individuals under the age of 18." | Burro must be for adults, and say so. Burro asks no age today | Read |
| Who the API is for | "for developers building with Google AI models for professional or business purposes, not for consumer use" | Burro is a business that builds on it. The people who use Burro do not use the API | Read |
| Housing | The policy forbids content or a service that "Makes automated decisions that have a material detrimental impact on individual rights without human supervision in high-risk domains -- for example, in employment, healthcare, finance, legal, housing, insurance, or social welfare." | The model turns a sentence into settings. It decides nothing about a person, and it never ranks. Burro must never be used to choose between tenants or buyers | Read |
| Personal data | The policy forbids a use that "Violates the rights of others, including privacy and intellectual property rights -- for example, using personal data or biometrics without legally-required consent." | The steps in section 7 | Read |
| Telling people a model is used | No clause says a product must. The policy forbids "Misrepresenting the provenance of generated content by claiming it was created solely by a human, in order to deceive." | Do not say a person read the sentence. Saying that a model reads it is good practice | Read |
| Telling people which provider | The privacy policy must say what is shared "with Google and third parties" | Name Google in the notice | Read |
| A badge or a credit to Google | "You agree to display any attribution(s) required by Google as described in the documentation for the API." None was found for plain text | Nothing to show | Read; the absence is an inference |
| Health | "You may not use the Services in clinical practice, to provide medical advice" | Burro gives none | Read |
| Safety settings | "You are responsible for determining the necessary and appropriate safety settings". "Applications with less restrictive safety settings may be subject to Google's review and approval." | Burro sends no setting and takes the default | Read |
| Getting round a block | "You may not attempt to bypass these protective measures" | A blocked call goes to the rules. It is never sent again reworded | Read |
| Competing models | "You may not use the Services to develop models that compete with the Services" | Do not train a model on Gemini's answers | Read |
| What happens on a breach | "Temporary usage limits", "Temporary suspension", "Account closure" | The rules answer when the model cannot | Read |

Sources: <https://ai.google.dev/gemini-api/terms>, <https://policies.google.com/terms/generative-ai/use-policy>, <https://developers.google.com/terms>, <https://ai.google.dev/gemini-api/docs/usage-policies>.

## 9. Examples to test against

Each is as read through the reader. Check it against the page before it becomes a fixture.

### A request with instructions, copied

From <https://ai.google.dev/gemini-api/docs/generate-content/text-generation>.

```
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent" \
      -H "x-goog-api-key: $GEMINI_API_KEY" \
      -H 'Content-Type: application/json' \
      -d '{
        "system_instruction": {
          "parts": [
            {
              "text": "You are a cat. Your name is Neko."
            }
          ]
        },
        "contents": [
          {
            "parts": [
              {
                "text": "Hello there"
              }
            ]
          }
        ]
      }'
```

### A whole answer from `generateContent`, copied

From Google's cookbook, <https://github.com/google-gemini/cookbook/blob/main/quickstarts/rest/Prompting_REST.ipynb>. It was made before thinking models. A current answer also holds `thoughtsTokenCount`, `modelVersion` and `responseId`.

```json
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "```python\n# Example list to be sorted\nmy_list = [5, 3, 1, 2, 4]\n\n# Sort the list in ascending order using the sort() method\nmy_list.sort()\n\n# Print the sorted list\nprint(my_list)\n```\n\nOutput:\n\n```\n[1, 2, 3, 4, 5]\n```"
          }
        ],
        "role": "model"
      },
      "finishReason": "STOP",
      "index": 0,
      "safetyRatings": [
        {
          "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
          "probability": "NEGLIGIBLE"
        },
        {
          "category": "HARM_CATEGORY_HATE_SPEECH",
          "probability": "NEGLIGIBLE"
        },
        {
          "category": "HARM_CATEGORY_HARASSMENT",
          "probability": "NEGLIGIBLE"
        },
        {
          "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
          "probability": "NEGLIGIBLE"
        }
      ]
    }
  ],
  "usageMetadata": {
    "promptTokenCount": 9,
    "candidatesTokenCount": 87,
    "totalTokenCount": 96
  }
}
```

### A whole answer from Interactions, copied

From <https://ai.google.dev/api/interactions-api>.

```json
{
  "created": "2025-11-26T12:25:15Z",
  "id": "v1_ChdPU0F4YWFtNkFwS2kxZThQZ05lbXdROBIXT1NBeGFhbTZBcEtpMWU4UGdOZW13UTg",
  "model": "gemini-3.6-flash",
  "object": "interaction",
  "status": "completed",
  "steps": [
    {
      "type": "model_output",
      "content": [
        {
          "type": "text",
          "text": "Hello! I'm functioning perfectly and ready to assist you.\n\nHow are you doing today?"
        }
      ]
    }
  ],
  "updated": "2025-11-26T12:25:15Z",
  "usage": {
    "input_tokens_by_modality": [
      {
        "modality": "text",
        "tokens": 7
      }
    ],
    "total_cached_tokens": 0,
    "total_input_tokens": 7,
    "total_output_tokens": 20,
    "total_thought_tokens": 22,
    "total_tokens": 49,
    "total_tool_use_tokens": 0
  }
}
```

### A request with a schema to Interactions, copied

From <https://ai.google.dev/gemini-api/docs/structured-output>. Of the samples on the page, this one balanced as read.

```
curl -N -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \
        -H "x-goog-api-key: $GEMINI_API_KEY" \
        -H 'Content-Type: application/json' \
        -d '{
          "model": "gemini-3.8-flash",
          "input": "The new UI is incredibly intuitive. Add a very long summary!",
          "response_format": {
            "type": "text",
            "mime_type": "application/json",
            "schema": {
              "type": "object",
              "properties": {
                "sentiment": { "type": "string", "enum": ["positive", "neutral", "negative"] },
                "summary": { "type": "string" }
              },
              "required": ["sentiment", "summary"]
            }
          },
          "stream": true
        }'
```

### An error from Interactions, copied

From <https://ai.google.dev/gemini-api/docs/api-errors>. It comes with HTTP 400.

```json
{
  "error": {
    "code": "invalid_request",
    "message": "The value 'invalid_tool_type_xyz' is not supported for 'type' at 'tools[0]'. Supported values: 'function', 'code_execution', 'mcp_server', 'filesystem', 'google_maps', 'google_search', 'bash', 'computer_use', 'file_search', 'url_context'."
  }
}
```

### An error in the older shape, copied

From Google's general guide to errors, <https://google.aip.dev/193>. It is not from the Gemini API. No sample of an error from `generateContent` was found.

```json
{
  "error": {
    "code": 429,
    "message": "The zone 'us-east1-a' does not have enough resources...",
    "status": "RESOURCE_EXHAUSTED",
    "details": [...]
  }
}
```

### What Burro would send, not copied and not tested

```json
{
  "system_instruction": {"parts": [{"text": "<the instructions>"}]},
  "contents": [{"parts": [{"text": "{\"request\": \"<the sentence>\", \"spec\": {}}"}]}],
  "generationConfig": {
    "responseMimeType": "application/json",
    "responseJsonSchema": {"type": "object"},
    "maxOutputTokens": 2048,
    "thinkingConfig": {"thinkingLevel": "minimal"}
  }
}
```

### Answers that are not whole, made from the reference, not copied

```json
{"promptFeedback": {"blockReason": "SAFETY"}, "usageMetadata": {"promptTokenCount": 3000, "totalTokenCount": 3000}}
```

```json
{"candidates": [{"content": {"parts": [{"text": "{\"status\": \"ok\", \"budget_ops\": ["}], "role": "model"}, "finishReason": "MAX_TOKENS", "index": 0}], "usageMetadata": {"promptTokenCount": 3000, "candidatesTokenCount": 2048, "totalTokenCount": 5048}}
```

## For the builder

| Matter | Do this | Why |
|---|---|---|
| Which API | Build `generateContent` first | Nothing is stored unless a feature is used, so privacy does not rest on one field. A block and a cut-off are documented field by field. Google's pages on Interactions disagree on its address and on whether it is finished |
| What that costs | `generateContent` is called "legacy". No date is set for its end | Keep the adapter to one module, so a move to Interactions changes one file |
| If Interactions is built | Send `"store": false` on every call, and hold it with a test | "By default, the API stores all Interaction objects" |
| Address | A constant: `https://generativelanguage.googleapis.com/v1beta/models/`, then the model, then `:generateContent` | The model's name goes into the address |
| Model id | Check it against a narrow pattern, such as `gemini-` then lower-case letters, digits, dots and hyphens, up to 48. No slash, colon, question mark or per cent sign | A name that holds `?key=` or `/../` would change the address |
| Never a `-latest` name | Refuse it in the pattern or in a test | It changes under you |
| Key | In `x-goog-api-key` only | Google's older samples put it in the address. An address is logged by servers on the way |
| Schema | `responseMimeType` with `responseJsonSchema`. Build the body in one function | The guide shows another shape, `responseFormat`. The first live call says which is taken. If the first is refused with 400, try the second by hand, not in code |
| Thinking | Send `"thinkingLevel": "minimal"` | It is the default on the small models, and an error on `gemini-3.8-flash`. Sending it makes a change of model fail loudly, not cost more quietly |
| Thoughts in the answer | Never ask for them. Skip any part marked as a thought | A thought could repeat the person's words |
| Tools, caches, files, search | Never send them | Each stores text |
| Finished | One candidate, `finishReason` is `STOP`, no `promptFeedback.blockReason`, at least one text part | Anything else is `ModelError` |
| Deadline | One clock for the whole call | |
| Body | Read to a fixed size and refuse beyond it | |
| Errors | Decide on the status alone. 402 and 429 are capped. 408 and 504 are timed out. The rest are errors | The message can repeat the request |
| Redirects | Refuse every 3xx | A redirect could carry the key to another host. None is documented |
| Usage | `cache_read_tokens` from `cachedContentTokenCount`. `input_tokens` from `promptTokenCount` less `cachedContentTokenCount`. `output_tokens` from `candidatesTokenCount` plus `thoughtsTokenCount` | So the three mean the same in every adapter, and the cost comes out right |
| Missing usage | `promptTokenCount` missing is an error. `cachedContentTokenCount` or `thoughtsTokenCount` missing is nil | Google leaves out a count of nil. This is the one provider where absent means nil, and only for these two |
| The first live call | Check that the schema is accepted, that `SPII` does not fire on a workplace, and what `thoughtsTokenCount` comes to | None of the three can be known from the pages |

## What Burro must tell a person

True of the paid service, which is the only one Burro may use for people in the UK.

> When you type a sentence, Burro sends your words to Google, whose Gemini service turns them into search settings on computers that may be outside the UK. Google does not use them to improve its products, but it keeps them for 55 days to check for misuse, and its staff may read them if they are flagged.

The free tier differs. There, Google's terms allow it to use what is sent to improve its products and let its reviewers read it. Google's terms do not allow the free tier for a product offered to people in the UK, so Burro never uses it, and the service should refuse to start on a key with no billing behind it if that can be told.

## What was not read

| What | Standing | What was relied on |
|---|---|---|
| Raw copies of the pages | Not downloaded | The reader's extraction |
| A web search | None was made | Known addresses only |
| The whole of the reference for `generateContent` | Read in part, twice | Google's published API definition on GitHub, for the values of `finishReason` and the keywords of `responseJsonSchema` |
| A sample answer from `generateContent` on Google's documentation site | None was in the part that was read | Google's cookbook on GitHub, which is older |
| A sample error from `generateContent` | The old page, `/gemini-api/docs/generate-content/troubleshooting`, was not read | Google's general guide to errors |
| Where Interactions shows a blocked answer | Not said on the pages read | Nothing |
| A limit on the size or depth of a schema | No number is published | Nothing. One live call |
| The smallest prompt that is cached on a Flash-Lite model | Not in the table | Nothing |
| Whether thinking tokens count against `maxOutputTokens` | Not said on the pages read | Nothing |
| Whether the schema is counted among the tokens in | Not said | Nothing |
| The limits on calls for each model | Shown only in the account | Nothing |
| Several Google Cloud pages | The first reading held menus only. A second reading held the body | The second reading |
| The path of a call to Vertex AI, and a sample with a key | The reading was not reliable | Nothing |
| Which models run in the UK on Vertex AI | Two readings disagreed | Treated as none |
| How to ask for the exception to the misuse record on Vertex AI | Not found | Nothing |
| Vertex AI's prices | Not read | Nothing |
| The list of Google's subprocessors | Not read | The address only |
| The transfer terms of the Cloud Data Processing Addendum | Read in part | The addendum for the Gemini API, which was read |
| Whether `SCHEMA` holds a `$ref` with a keyword beside it | Checked once | The definitions printed on the first run |
| The live service | No call was made | Examples from the documents |

## For the founder to decide

1. **Whether 55 days at Google is acceptable.** On the Gemini API every sentence is kept for 55 days to watch for misuse, Google's staff may read one that is flagged, and it cannot be turned off. ADR 0005 says today that the provider keeps text "for up to 30 days". With Gemini that sentence is wrong, and the ADR and the privacy notice need to change before Gemini is turned on.
2. **The Gemini API or Vertex AI.** Vertex AI offers an exception to the 55-day record and an address that keeps processing in the EU. It asks for credentials that the standard library cannot make, or a key that Google recommends for testing only. It offers no address for the UK. The recommendation is to start on the Gemini API, and to move only if item 1 or item 3 cannot be accepted.
3. **Whether processing outside the UK is acceptable.** No region can be chosen on the Gemini API. Google's addendum names the Data Privacy Framework with its UK Extension as the safeguard. The impact assessment must say so.
4. **Billing, and a cap.** The free tier is not allowed for people in the UK. Billing must be on before the first real sentence. Choose prepaid credit or a monthly bill, and set a monthly cap in AI Studio. At $1.90 for 1,000 searches, $20 a month covers ten thousand.
5. **Adults only.** Google's terms forbid a product "likely to be accessed by" under-18s. Burro asks no age. Decide whether the terms of use say 18 and over, and whether that is enough.
6. **The lawful basis, the condition and the impact assessment.** A sentence can hold health or religion. The regulator asks that the basis and the condition be chosen and written down before the first one is sent. ADR 0007 rules out a solicitor, so this is the founder's to write, from the regulator's templates.
7. **Which model.** `gemini-3.5-flash-lite` at $1.65 for 1,000, with no retirement date, or `gemini-3.1-flash-lite` at $1.20, which may go from 7 May 2027. The recommendation is the first. Run the golden queries on both before it is final. Google retired a stable model sixteen months after its release, so plan for a change of model every year.
8. **`generateContent` or Interactions.** The first is called legacy and stores nothing of its own. The second is the one Google recommends and stores every call unless told not to. The recommendation is the first, and to look again if Google sets a date for its end.
