# DeepSeek, from its own documents

Read on 23 September 2026. A dated snapshot: model names, prices and terms change often. Re-check before relying on a figure.

This is one of four reports, one a provider. The same nine questions were put to each.

## How this was read

| Point | What it means for you |
|---|---|
| Every page was read through a reader that extracts, not the raw page | A quoted sentence may differ from the source by a word. Check the wording at the address given before it goes into a privacy notice or a contract |
| Raw copies of the pages were not downloaded | Examples marked "copied" are as read through the reader. Line breaks and spacing may differ |
| No web search was made | Only known addresses were read. Anything DeepSeek publishes elsewhere was not found |
| No key, and no call to the provider | Nothing here was tested against the live service |
| Nothing here is legal advice | |

"Read" in a table below means read at the provider's own address on the day. "Not read" means it is an inference, or the page did not say.

## In short

| Question | Answer | Read |
|---|---|---|
| Can it do the job | Yes. One POST, a key in a header, JSON back | Read |
| Is the schema enforced | Only through a tool call on the Beta address. On the stable address the answer is valid JSON and nothing more | Read |
| Smallest model fit for the job | `deepseek-flash` | Read |
| Cost of 1,000 searches | $0.23 to $1.26, by time of day and cache | Worked out from prices that were read |
| Where the text is processed | The People's Republic of China. No region can be chosen | Read |
| How long the text is kept | No period is given | Read |
| Is it used to improve models | The terms allow it. No way to refuse is documented for the API | Read |
| Zero retention | Not offered | Not found |
| Data processing agreement | None published | Not found |
| A safeguard for a transfer from the UK | None named | Read |
| What the provider says of sensitive data | "you should not provide sensitive Personal Data to the Services" | Read |

The adapter can be built and tested. On the documents as they stand, sending a real person's sentence to this provider is a decision for the founder, and the last section says why.

## 1. The call

| Item | Value | Read |
|---|---|---|
| Address | `https://api.deepseek.com/chat/completions` | Read |
| Beta address, for a strict tool call | `https://api.deepseek.com/beta/chat/completions` | Base read; the full path is an inference |
| Method | `POST` | Read |
| Header that carries the key | `Authorization: Bearer <key>` | Read |
| May the key go in a header | Yes. HTTP Bearer is the only scheme documented. No key in a query string is documented | Read |
| Other header | `Content-Type: application/json` | Read |
| Instructions | A message with `"role": "system"`, first in `messages` | Read |
| The person's turn | A message with `"role": "user"` | Read |
| State | "the server does not record the context of the user's requests" | Read |
| Other formats at the same host | `/anthropic` (key in `x-api-key`) and a Responses format. Neither documents a schema | Read |

Sources: <https://api-docs.deepseek.com/>, <https://api-docs.deepseek.com/api/create-chat-completion>, <https://api-docs.deepseek.com/guides/multi_round_chat>, <https://api-docs.deepseek.com/guides/anthropic_api>, <https://api-docs.deepseek.com/guides/responses_api>.

### Fields of the body that matter

| Field | Values | Default | Note | Read |
|---|---|---|---|---|
| `model` | `deepseek-flash`, `deepseek-v4-pro` | none | | Read |
| `messages` | roles `system`, `user`, `assistant`, `tool` | none | At least one | Read |
| `thinking` | `{"type": "enabled"}` or `{"type": "disabled"}` | enabled | Must be sent as disabled. See below | Read |
| `reasoning_effort` | `none`, `low`, `high`, `max` | `high` | `none` also turns thinking off | Read |
| `response_format` | `{"type": "text"}` or `{"type": "json_object"}` | text | No `json_schema` type | Read |
| `max_tokens` | 1 to 393,216 | 8K with thinking off, 64K with it on | | Read |
| `temperature` | 0 to 2 | 1 | Not supported while thinking is on | Read |
| `stream` | true or false | false | Send false | Read |
| `tools`, `tool_choice` | functions; `none`, `auto`, `required`, or a named function | | Needed only for the strict route | Read |
| `user_id` | `[a-zA-Z0-9\-_]`, up to 512 characters | none | Do not send it. See section 7 | Read |

**Thinking is on unless it is turned off.** "Thinking mode is enabled by default, with the default effort being `high`." With it on, the model writes a chain of thought before the answer. That costs time and output tokens, and the text comes back in `reasoning_content`, which would hold the person's words again. Burro must send `"thinking": {"type": "disabled"}` on every call, and a test must hold it to that.

## 2. Structured output

There are two ways. Neither is the same as a schema on the stable address.

| | JSON Output | Strict tool call |
|---|---|---|
| Address | Stable | Beta |
| How | `"response_format": {"type": "json_object"}` | A function in `tools` with `"strict": true`, and `tool_choice` naming it |
| Takes a schema | No. The schema goes in the prompt as words | Yes, as the function's `parameters` |
| What is promised | "guarantees the message the model generates is valid JSON" | "ensure the output always complies with the function's JSON schema" |
| Enforced or encouraged | Valid JSON is enforced. The shape is only encouraged | Enforced |
| Where the answer is | `choices[0].message.content` | `choices[0].message.tool_calls[0].function.arguments`, a JSON string (the path is not read; it follows the format the API copies) |
| Finished value | `stop` | `tool_calls` |
| Known fault | "the API may occasionally return empty content" | Beta. May change |
| Read | Read | Read, but for the path |

Sources: <https://api-docs.deepseek.com/guides/json_mode/>, <https://api-docs.deepseek.com/guides/tool_calls>.

### What JSON Output asks of the caller

1. Set `response_format` to `{"type": "json_object"}`.
2. "Include the word "json" in the system or user prompt, and provide an example of the desired JSON format".
3. "Set the `max_tokens` parameter reasonably to prevent the JSON string from being truncated midway."

Without an instruction to write JSON, "the model may generate an unending stream of whitespace until the generation reaches the token limit". Burro's instructions already say JSON. The schema and one empty answer must be added to the system message by the adapter.

### What the strict route accepts

| Part of JSON Schema | Accepted | Read |
|---|---|---|
| Types `object`, `string`, `number`, `integer`, `boolean`, `array` | Yes | Read |
| `enum` | Yes | Read |
| `anyOf` | Yes | Read |
| `additionalProperties` | Must be `false` on every object | Read |
| `required` | Must list every property of every object | Read |
| Nullable | No word on it. `anyOf` with a `null` type is the likely way | Not read |
| String `pattern`, `format` (email, hostname, ipv4, ipv6, uuid) | Yes | Read |
| String `minLength`, `maxLength` | No | Read |
| Number `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`, `multipleOf`, `const`, `default` | Yes | Read |
| Array `minItems`, `maxItems` | No | Read |
| Reuse | `$ref` with a block named `$def` | Read |
| Nesting depth, number of properties, number of enum values | No limit is given | Not found |
| A schema it does not accept | "an error message will be returned" | Read |

### How Burro's schema fits

`claude.SCHEMA` was printed and counted for this report.

| What the schema uses | Count | Fits the strict route |
|---|---|---|
| Objects, each with `additionalProperties: false` and every property required | 7 | Yes |
| Arrays of records or of enum values | 8 | Yes |
| Enums | 19, with 103 values | Yes |
| Types | string, integer, number, array, object | Yes |
| Length and range limits | None: `_plain` takes them out | Yes |
| `anyOf`, nullable, optional fields | None | Yes |
| `$ref` into a block named `$defs` | 36 references | **Not known.** The documents name the block `$def`. Whether `$defs` is taken is not said |

If the strict route is built, the adapter should write each reference out in full before it sends the schema. Then the question does not arise.

### A refusal, and an answer cut short

| What happened | What comes back | Read |
|---|---|---|
| Cut short by `max_tokens` or the context limit | HTTP 200, `finish_reason` `length`, and content that "may be partially cut off" | Read |
| Blocked by a filter | HTTP 200, `finish_reason` `content_filter` | Read |
| The model declines in words | Not documented. With JSON Output it would be JSON of some other shape, or empty content | Not read |
| Empty content | HTTP 200, `content` empty or `null`. The documents admit it happens | Read |

Burro treats every one of these as an error. The answer is validated in `claude._parsed` whatever the provider promises.

## 3. What "finished" means

The field is `choices[0].finish_reason`.

| Value | Meaning, in the provider's words | Burro |
|---|---|---|
| `stop` | "the model hit a natural stop point or a provided stop sequence" | Whole, if `content` is a string that is not empty |
| `length` | "the maximum number of tokens specified in the request was reached" | Error |
| `content_filter` | "content was omitted due to a flag from our content filters" | Error |
| `tool_calls` | "the model called a tool" | Error on the JSON Output route. Whole on the strict route |
| `insufficient_system_resource` | "the request is interrupted due to insufficient resource of the inference system" | Error |
| `aborted` | "the generation was interrupted" | Error |
| Anything else, or missing | | Error |

All read at <https://api-docs.deepseek.com/api/create-chat-completion>.

## 4. Usage

| Field | Counts | Goes into | Read |
|---|---|---|---|
| `usage.prompt_tokens` | Tokens in. "It equals prompt_cache_hit_tokens + prompt_cache_miss_tokens" | | Read |
| `usage.prompt_cache_miss_tokens` | Tokens in that were not in the cache | `input_tokens` | Read |
| `usage.prompt_cache_hit_tokens` | Tokens in that were read from the cache | `cache_read_tokens` | Read |
| `usage.completion_tokens` | Tokens out | `output_tokens` | Read |
| `usage.total_tokens` | In and out | | Read |
| `usage.completion_tokens_details.reasoning_tokens` | Tokens of the chain of thought | Expect 0 with thinking off | Read |
| `usage.prompt_tokens_details.cached_tokens` | In the example answer. Not described | | Read |

**One thing to settle in the design.** The adapter that exists gives `input_tokens` as the tokens that were not read from the cache, because that is what its provider counts. Here `prompt_tokens` includes the cached ones. To mean the same thing in every adapter, this one should put `prompt_cache_miss_tokens` in `input_tokens`. `docs/design/models.md` should say which meaning holds.

## 5. Errors

The documents give a status, a name, a cause and a fix. They show **no body** for an error. The adapter must decide on the status alone, and must never read, keep or log the body: it may repeat the request.

| Status | Name | Cause, in the provider's words | Becomes | Read |
|---|---|---|---|---|
| 400 | Invalid Format | "Invalid request body format." | error | Read |
| 401 | Authentication Fails | "Authentication fails due to the wrong API key." | error | Read |
| 402 | Insufficient Balance | "You have run out of balance." | capped | Read |
| 422 | Invalid Parameters | "Your request contains invalid parameters." | error | Read |
| 429 | Rate Limit Reached | "You are sending requests too quickly." | capped | Read |
| 500 | Server Error | "Our server encounters an issue." | error | Read |
| 503 | Server Overloaded | "The server is overloaded due to high traffic." | error | Read |
| Any 3xx | | Not documented | error, and not followed | Not read |
| Any other status | | Not documented | error | Not read |
| 200, not JSON, or not the shape above | | | error | |
| 200, `finish_reason` not whole | | See section 3 | error | Read |
| The deadline passes | | No status: see below | timed out | Read |
| A body over the size limit | | | error | |

Source: <https://api-docs.deepseek.com/quick_start/error_codes>.

A safety block has no status of its own. It is a 200 with `finish_reason` `content_filter`.

An overloaded service is 503, and here it becomes "error" and not "capped", because no limit of Burro's was reached. It is a judgement. It changes only what is counted, since nothing is tried again.

### The limit on calls

| Model | Calls at once, per account | Over it | Read |
|---|---|---|---|
| `deepseek-flash` | 2,500 | 429 | Read |
| `deepseek-v4-pro` | 500 | 429 | Read |

No limit by tokens a minute or requests a minute is documented. Source: <https://api-docs.deepseek.com/quick_start/rate_limit>.

### The timeout: two things the builder must know

Under load the server holds the connection open and sends filler until it starts work.

| What the documents say | What it means for the adapter |
|---|---|
| For a request that does not stream, the server will "Continuously return empty lines" | A timeout on each read never fires, because each empty line is a read that worked. The deadline must be on the clock, for the whole call |
| The same | The body may begin with blank lines. They count towards the size limit. Strip them before parsing |
| "If the request has not started inference after 10 minutes, the server will close the connection." | Left alone, a call can hang for ten minutes |

Whether the status line arrives before the filler is not said. If it does, a failure after it cannot change the status, and would show as a body that is not an answer. That becomes "error", which is right.

## 6. Models

### Offered today

| Id | Version behind it | Context | Most it can write | JSON Output | Tool calls | Due to retire | Read |
|---|---|---|---|---|---|---|---|
| `deepseek-flash` | DeepSeek-V4.1-Flash | 1M | 384K | Yes | Yes | No date given | Read |
| `deepseek-v4-pro` | DeepSeek-V4-Pro-0813 | 1M | 384K | Yes | Yes | No date given. Two pages disagree, see below | Read |
| `deepseek-v4-flash` | Served by V4.1-Flash | | | | | The model is retired. The name routes "temporarily" | Read |
| `deepseek-v4-flash-vision-exp` | Served by V4.1-Flash | | | | | The same | Read |
| `deepseek-chat`, `deepseek-reasoner` | | | | | | Retired 24 July 2026, 15:59 UTC | Read |

Sources: <https://api-docs.deepseek.com/quick_start/pricing>, <https://api-docs.deepseek.com/api/list-models>, <https://api-docs.deepseek.com/updates>, <https://api-docs.deepseek.com/news/news260424>, <https://api-docs.deepseek.com/news/news260910>.

Three things follow from the change log.

| Finding | Evidence | Consequence |
|---|---|---|
| A name does not pin a model | `deepseek-flash` was pointed at V4.1-Flash on 10 September 2026. No dated or pinned id is offered | The model behind the id can change with no change in Burro. Run the golden queries on a schedule, not once |
| Notice of retirement has been three months | `deepseek-chat` was given notice on 24 April 2026 and retired on 24 July 2026 | Plan for the id to change about twice a year |
| Two of the provider's pages disagree about `deepseek-v4-pro` | The news page of 10 September says that from 14 September "all `deepseek-v4-pro` requests will route to V4.1-Flash at V4.1-Flash rates". The change log says the provider will "continue providing API services for DeepSeek V4 Pro after September 14, 2026, with the billing method remaining unchanged". The price page lists it with its own price | Do not rely on `deepseek-v4-pro` until one call shows which model answers |

### Prices, in US dollars for a million tokens

| Model | When | In, not cached | In, from cache | Out |
|---|---|---|---|---|
| `deepseek-flash` | Peak | 0.30 | 0.006 | 1.20 |
| `deepseek-flash` | Off-peak | 0.15 | 0.003 | 0.60 |
| `deepseek-v4-pro` | Peak | 1.32 | 0.044 | 3.96 |
| `deepseek-v4-pro` | Off-peak | 0.66 | 0.022 | 1.98 |

All read at <https://api-docs.deepseek.com/quick_start/pricing>, twice, with the same figures.

| Point | In the provider's words | Read |
|---|---|---|
| Peak | "01:00 - 04:00 and 06:00 - 10:00 UTC, Monday through Friday, excluding Chinese public holidays" | Read |
| In London | 06:00 to 10:00 UTC is 07:00 to 11:00 in summer. The rest of the working day and the evening are off-peak | Worked out |
| Prices can move | "Product prices may vary and DeepSeek reserves the right to adjust them." | Read |
| Thinking | One price for output. Whether the chain of thought is billed as output is not said on the pages read | Not read |

### The cache

| Point | In the provider's words | Read |
|---|---|---|
| On by default | "enabled by default for all users, without needing to modify their code" | Read |
| Can it be turned off | No way is documented | Not found |
| What is matched | "The hard disk cache only matches the prefix part of the user's input" | Read |
| How sure | "works on a 'best-effort' basis and does not guarantee a 100% cache hit rate" | Read |
| How long it lasts | "Once the cache is no longer in use, it will be automatically cleared, usually within a few hours to a few days." | Read |
| Smallest prefix that is cached | Not given on the page read | Not found |

Nothing is sent to mark the instructions. Put them first and keep them the same, byte for byte.

### The smallest model fit for the job

`deepseek-flash`. It is the smaller of the two, it takes a system message and a short user turn, it supports JSON Output and tool calls, and its context is over 200 times what the job needs. Whether it reads Burro's sentences well is not known until the golden queries are run.

### 1,000 searches, at 3,000 tokens in and 300 out

"Cached" assumes 2,700 of the 3,000 tokens are the fixed instructions and are read from the cache, and 300 are not.

| Model | When | Not cached | Cached |
|---|---|---|---|
| `deepseek-flash` | Peak | $1.26 | $0.47 |
| `deepseek-flash` | Off-peak | $0.63 | $0.23 |
| `deepseek-v4-pro` | Peak | $5.15 | $1.70 |
| `deepseek-v4-pro` | Off-peak | $2.57 | $0.85 |

The sums, for `deepseek-flash` at peak: not cached, 3.0 x 0.30 + 0.3 x 1.20 = 1.26. Cached, 2.7 x 0.006 + 0.3 x 0.30 + 0.3 x 1.20 = 0.47.

| What would move the figure | By how much |
|---|---|
| The schema rides in the prompt on the JSON Output route. It is about 5,800 characters, some 1,700 tokens at the provider's rule of 0.3 tokens a character | Cached: a cent more. Not cached at peak: about $0.51 more |
| Thinking left on | Output grows from hundreds of tokens to thousands. Several times the cost, and seconds more to wait |
| The cache misses | Up to the "not cached" column |

Plan on the peak price, not cached: **$1.26 for 1,000 searches**. Token counts are estimates until they are measured.

## 7. What happens to a person's text

Three documents apply. None was written for a developer's end users, and two say so.

| Document | Date | Address |
|---|---|---|
| Open Platform Terms of Service | Effective 29 April 2026 | <https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html> |
| Terms of Use | 27 March 2026 | <https://cdn.deepseek.com/policies/en-US/deepseek-terms-of-use.html> |
| Privacy Policy | 10 February 2026 | <https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html> |

The Open Platform terms call themselves a "Specific Agreement to the DeepSeek Terms of Use". So the Terms of Use bind an API customer too. The Terms of Use count "application programming interfaces (APIs)" among the services.

### Who answers for the text

| Point | Sentence | Where | Read |
|---|---|---|---|
| Burro is the controller | "As the controller of personal information processing activities in that scenario, you should disclose the relevant privacy policy to your end users." | Open Platform terms, 5.5 | Read |
| The privacy policy does not cover Burro's users | "the processing rules for Personal Data collected from end users when accessing downstream systems or applications developed by developers using our open platform services are not covered by this privacy policy" | Privacy Policy | Read |
| Burro must have consent or another basis, for the hand-over too | "You shall obtain the consent of end users or have other legal basis for the collection, processing of personal information, and delegation of personal information processing to us." | Open Platform terms, 3.3 | Read |
| Burro answers people's requests | "you shall promptly respond in accordance with legal requirements. If cooperation with DeepSeek is required, you can contact us" | Open Platform terms, 3.3 | Read |

### The questions

| Question | Answer | Sentence | Where | Read |
|---|---|---|---|---|
| How long is it kept | No period is given for text sent through the API | "We retain Personal Data for as long as necessary to provide our Services and for the other purposes set out in this Privacy Policy." | Privacy Policy | Read |
| | For DeepSeek's own account holders, as long as the account lasts | "we keep this Personal Data for as long as you have an account. This Personal Data includes your account Personal Data, input and payment Personal Data." | Privacy Policy | Read |
| | The cache holds the start of a request on disk | "automatically cleared, usually within a few hours to a few days" | <https://api-docs.deepseek.com/guides/kv_cache> | Read |
| Is it used to train models, paid | The terms allow use to improve the service. They do not say the API is left out | "we may, to a minimal extent, use Inputs and Outputs to provide, maintain, operate, develop or improve the Services or the underlying technologies supporting the Services" | Terms of Use, 4.3 | Read |
| | | "a small portion [of question-answer pairs are] potentially based on user input" | <https://cdn.deepseek.com/policies/en-US/model-algorithm-disclosure.html> | Read |
| How to refuse | By a switch in the app. No switch, field or form is documented for the API | "you can opt out by turning off 'Improve the model for everyone'" | Terms of Use, 4.3 | Read |
| Is it used to train models, free | No free tier of the API is documented. Credit the provider gives away is spent first, and no other terms are given for it | "with a preference for using the granted balance first" | <https://api-docs.deepseek.com/quick_start/pricing> | Read |
| Where is it processed | China | "we directly collect, process and store your Personal Data in People's Republic of China" | Privacy Policy | Read |
| Can a region be chosen | No way is documented | | | Not found |
| Zero retention | Not offered in any document read | | | Not found |
| Data processing agreement | None is published. The terms have no word for processor, sub-processor, audit, deletion or breach notice | | Open Platform terms | Read: the words are absent |
| Who else may receive it | Service providers, the corporate group, and authorities | "We may access, preserve, and share the Personal Data with law enforcement agencies, public authorities, copyright holders, or other third parties if we have good faith belief that it is necessary to: comply with applicable law, legal process or government requests" | Privacy Policy | Read |
| Sensitive data | The provider asks that none be sent | "The Services are not designed or intended to process sensitive Personal Data (e.g., personal data revealing racial or ethnic origin, religious beliefs, health, sexuality, citizenship, immigration status, genetic or biometric data, personal data of children, precise geolocation or criminal membership)." "We do not ask for, and you should not provide sensitive Personal Data to the Services" | Privacy Policy | Read |
| Whose law | China's, in a court where the provider has its office | "governed by the laws of the People's Republic of China in the mainland" | Open Platform terms, 10 | Read |

### UK and EU law

| What the provider says | Sentence | Read |
|---|---|---|
| Extra terms apply in the "European Region" | "If you are using the Services in the EEA, Switzerland or the UK (the "European Region"), the following additional terms apply" | Read |
| It has a representative | "have therefore appointed Prighter Group with its local partners as our privacy representative". Contact: `rep_deepseek@prighter.com` | Read |
| It names no safeguard for the transfer | "Where required, we will use appropriate safeguards for transferring Personal Data outside of certain countries" | Read |
| It gives people rights, its own users that is | Access, rectification, erasure, restriction, portability, objection, and "the right to opt-out of using your Personal Data for training our models" | Read |
| It offers no transfer agreement | No mention of standard contractual clauses, the UK transfer agreement or the UK addendum | Read: the words are absent |

### What a UK company must do first

This is the regulator's guidance, not the provider's. Read at the Information Commissioner's Office.

| Step | In the ICO's words | Can it be done with this provider today | Address |
|---|---|---|---|
| A lawful basis, and a condition for special category data | "you must identify both a lawful basis under Article 6 and a condition for processing special category data under Article 9" | Burro's part. Explicit consent is the likely condition | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/special-category-data/what-are-the-rules-on-special-category-data/> |
| Know what counts | Data "revealing" racial or ethnic origin, political opinions, religious or philosophical beliefs, trade union membership; genetic and biometric data; data "concerning health", sex life or sexual orientation | A sentence about where to live can hold several | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/special-category-data/what-is-special-category-data/> |
| An impact assessment | Needed for special category data "on a large scale" or "to determine access to a product, service, opportunity or benefit" | Burro's part | As the first |
| A written contract with the processor | "Whenever a controller uses a processor to process personal data on their behalf, a written contract needs to be in place between the parties." It must bind the processor to act "only" on instructions, to keep confidence, to seek leave for a sub-processor and to "submit to audits and inspections" | **No.** No such contract is published | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/guide-to-accountability-and-governance/contracts/> |
| A safeguard for the transfer | "the International data transfer agreement (IDTA); the International data transfer addendum (the Addendum); or UK binding corporate rules" | **No.** None is offered. One would have to be asked for | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/international-transfers-a-guide/> |
| A transfer risk assessment | "to make sure that the standard of protection for people's information is not materially lower after we transfer it" | Burro's part. It must weigh the sentence on government requests above | As above |
| If none of that can be done | "We must not make a restricted transfer" unless an exception applies | | As above |

Not read at a source: that the UK has no adequacy regulations for China. The ICO guide that was read lists no countries. Check it before relying on it.

## 8. Terms that bind a product like this

| Matter | What the terms say | Where | Read |
|---|---|---|---|
| Age | "The Services are primarily intended for adults. If you are under 18 years old or the minimum age required in your country, please read these Terms with your legal guardian and use the Services only with the consent of your legal guardian." | Terms of Use, 2.1 | Read |
| Children | "Our Services are not aimed at children, and we do not knowingly process Personal Data from children." | Privacy Policy | Read |
| Telling people a model is used | "You shall clearly disclose to your end users that the Output content is generated by AI, and may contain errors or omissions and are for reference only." | Open Platform terms, 8.1 | Read |
| Housing | "if you use the Outputs for any purpose that could have a legal or material impact on natural persons, such as making credit, educational, employment, housing, insurance, legal, medical, or other important decisions about them, such Outputs shall undergo human reviews" | Terms of Use, 5.4 | Read |
| Discrimination | Forbids content that is "discriminatory such as discriminating another based on race, gender, sexuality, religion, nationality, disability or age" | Terms of Use | Read |
| Telling people which provider is used | No duty was found. The terms forbid use of the provider's "trademarks, service marks, trade names" | Open Platform terms | Read |
| Burro answers for its users | "you should procure that both of you and your end users comply with the requirements of the DeepSeek Terms of Use" | Open Platform terms, 3.1 | Read |
| Security | Burro must keep "user management, data security, monitoring, warning, and emergency disposal" | Open Platform terms, 3.4 | Read |
| Sanctions | "Services may not be used in or for the benefit of, or exported, re-exported, or transferred (a) to or within any country subject to comprehensive sanctions" | Open Platform terms, 9 | Read |
| Liability | Capped at the fees "actually consumed for the service in the past twelve months". Burro indemnifies the provider | Open Platform terms, 7 | Read |

How each bears on Burro:

| Term | Bearing |
|---|---|
| Housing, and human review | Burro decides nothing about a person. The model's answer becomes edits to the person's own search, shown to them, and theirs to change. That is the review. It is a reading of the clause, not a ruling |
| Telling people a model is used | Burro must say so where the sentence is typed, whichever provider is in use |
| Naming the provider | UK law asks a privacy notice to name who receives the data. Naming DeepSeek in a notice describes a fact and uses no logo. Whether the trade mark clause reaches that far is for the founder |
| Age | Burro has no accounts and asks no age. If it says nothing, it cannot show it kept this term |

## 9. Examples to test against

### A request, copied

From <https://api-docs.deepseek.com/>. It has thinking on, as the provider's example does. Burro would send it off.

```
curl https://api.deepseek.com/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" \
  -d '{"model": "deepseek-flash", "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hello!"}], "thinking": {"type": "enabled"}, "reasoning_effort": "high", "stream": false}'
```

### A whole answer, copied

From <https://api-docs.deepseek.com/api/create-chat-completion>.

```json
{
  "id": "930c60df-bf64-41c9-a88e-3ec75f81e00e",
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "message": {
        "content": "Hello! How can I help you today?",
        "role": "assistant"
      },
      "logprobs": null
    }
  ],
  "created": 1705651092,
  "model": "deepseek-flash",
  "object": "chat.completion",
  "system_fingerprint": "fp_7a09fdf9c2",
  "usage": {
    "completion_tokens": 10,
    "prompt_tokens": 16,
    "total_tokens": 26,
    "prompt_tokens_details": {
      "cached_tokens": 0
    },
    "prompt_cache_hit_tokens": 0,
    "prompt_cache_miss_tokens": 16
  }
}
```

### JSON Output, copied

From <https://api-docs.deepseek.com/guides/json_mode/>. The provider shows it through a vendor's library, which Burro does not use. What matters is the prompt and the content that comes back.

| Part | Text |
|---|---|
| System | `The user will provide some exam text. Please parse the "question" and "answer" and output them in JSON format. EXAMPLE INPUT: Which is the highest mountain in the world? Mount Everest. EXAMPLE JSON OUTPUT: {"question": "Which is the highest mountain in the world?", "answer": "Mount Everest"}` |
| User | `Which is the longest river in the world? The Nile River.` |
| Field sent | `"response_format": {"type": "json_object"}` |
| Content returned | `{"question": "Which is the longest river in the world?", "answer": "The Nile River"}` |

### An error

The documents show no body for an error. What they give is the status and its name:

```
429 - Rate Limit Reached
Cause: You are sending requests too quickly.
```

Test with the status and a body of the test's own, and prove the body is never read: put a canary in it and look for it in every log line and every exception.

### What Burro would send, not copied and not tested

```json
{
  "model": "deepseek-flash",
  "messages": [
    {"role": "system", "content": "<the instructions, then the schema, then one empty answer>"},
    {"role": "user", "content": "<the JSON Burro makes of the spec and the sentence>"}
  ],
  "thinking": {"type": "disabled"},
  "response_format": {"type": "json_object"},
  "max_tokens": 1024,
  "temperature": 0,
  "stream": false
}
```

## For the builder

| Matter | Do this | Why |
|---|---|---|
| Route | Build JSON Output first, on the stable address | Every part of it is documented. The strict route is Beta and one point of it is not known |
| Schema | Put it in the system message, after the instructions, with one empty answer | JSON Output takes no schema |
| Thinking | Send `"thinking": {"type": "disabled"}` always | It is on by default, and it repeats the person's words in a second field |
| `user_id` | Never send it | The provider says "Do not include user privacy information in the user_id", and Burro has nothing to put there that is not about a person |
| Deadline | One clock for the whole call | Empty lines defeat a timeout on each read |
| Body | Read to a fixed size and refuse beyond it. Count the empty lines | |
| Errors | Decide on the status alone | No body is documented, and a body can repeat the request |
| Redirects | Refuse every 3xx | A redirect could carry the key to another host. None is documented |
| Model id | Check it against a narrow pattern, such as lower-case letters, digits, dots and hyphens, up to 64 | It goes into the body as it is |
| Usage | `input_tokens` from `prompt_cache_miss_tokens`, `cache_read_tokens` from `prompt_cache_hit_tokens`, `output_tokens` from `completion_tokens` | So the three mean the same in every adapter |
| Missing usage | A missing or negative count is an error, not a zero | A number that is not known is never zero |

## What Burro must tell a person

True of the paid service. No free tier of the API is documented, and no other terms are given for credit the provider gives away, so nothing differs.

> When you type a sentence, Burro sends your words to DeepSeek, a company in China, and its computers in China turn them into search settings. DeepSeek does not say how long it keeps them and may use them to improve its models after removing what it says could identify you, so leave out your health, your religion and anything else you would not want kept.

## What was not read

| What | Standing | What was relied on |
|---|---|---|
| Raw copies of the pages | Not downloaded | The reader's extraction |
| A web search | None was made | Known addresses only |
| `https://platform.deepseek.com/` | Not read | Nothing. Whether the account page has a switch to refuse training is not known |
| `https://chat.deepseek.com/` | Not read | Nothing |
| The FAQ at `https://static.deepseek.com/faq/` | Not read | Nothing |
| A data processing agreement | None at the addresses read | The absence of the words in the three documents |
| A body for an error | Not shown on any page read | The table of statuses |
| Whether `$defs` is taken by the strict route | Not said | Nothing. Write references out in full |
| Whether the chain of thought is billed as output | Not said on the pages read | Nothing. Thinking is sent as off |
| Whether the cache is kept apart between accounts | Not said on the page read | Nothing |
| Decisions of regulators about this provider | Not searched for | Nothing. Check the ICO and the EU regulators before relying on this provider |
| The live service | No call was made | Examples from the documents |

## For the founder to decide

1. **Whether real people's sentences may go to this provider at all.** Its own policy says sensitive data should not be sent. It processes in China, names no safeguard for the transfer, publishes no processing contract, gives no period for keeping text, and allows use to improve its models with no documented way to refuse through the API. A sentence typed into Burro can hold a workplace, a child's school, health or religion. On these documents the steps the ICO sets out cannot all be taken. The adapter can still be built, and used on made-up sentences and in tests.
2. **Whether to ask DeepSeek for what is missing.** A processing contract, a UK transfer agreement, a period of retention and a written promise not to train on API text. The address is `api-service@deepseek.com`. It costs an email. Until there is an answer in writing, item 1 stands.
3. **Whether `BURRO_MODEL_TERMS_ACCEPTED=deepseek` should be possible in a service that real people use.** One way to hold the line in code: the table of terms marks this provider as fit for synthetic text only, and the service refuses to start with it on a release that is not synthetic. That is a change to a decision already made, so it is yours.
4. **Whether to run the open model somewhere else instead.** The provider says it releases its weights under the MIT licence. Run by a host in the UK or the EU, the text would not go to China. That is a different provider with its own terms, a fifth adapter, and a paid service. It was not researched here.
5. **JSON Output or the strict tool call.** The first is documented and stable, and does not enforce the shape. The second enforces it and is Beta. The recommendation is the first, with the second held back until the golden queries show how often the shape is wrong.
6. **Whether to plan on the peak price.** $1.26 for 1,000 searches at peak and not cached, against $0.23 off-peak and cached. At either figure the cost of the model is small beside the other questions here.
7. **What to say about age.** The terms ask for a guardian's consent under 18. Burro asks no age today.
8. **Whether naming DeepSeek in the privacy notice needs the provider's leave.** The terms forbid use of its trade names. UK law asks that recipients be named.
