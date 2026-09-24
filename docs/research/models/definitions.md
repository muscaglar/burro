# What the providers' published definitions say

Read on 23 September 2026, by whoever built the adapters. A dated snapshot.

The four reports beside this one were read from each provider's pages. Two of them were read through a reader that extracts. This note is a second look at the facts an adapter is built on: the names of the fields it sends and reads. Three providers publish a definition of their API as a file. Each was downloaded as it is served and searched for the names the adapter uses. No call was made to any provider.

| Provider | File | Its own date |
|---|---|---|
| Google | <https://raw.githubusercontent.com/googleapis/googleapis/master/google/ai/generativelanguage/v1beta/generative_service.proto> and `content.proto` beside it | "Copyright 2025". Older than the guide |
| OpenAI | <https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml> | None. It names `gpt-5.6`, so it is recent |
| Anthropic | <https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/types/> : `message_create_params.py`, `output_config_param.py`, `json_output_format_param.py`, `thinking_config_disabled_param.py`, `stop_reason.py`, `usage.py` | The provider's own library, made from its definition |
| DeepSeek | None was found | |

## What was found

| Provider | What the adapter does | In the definition |
|---|---|---|
| Gemini | Sends the schema in `generationConfig.responseJsonSchema`, with `responseMimeType` | Yes. "Use `responseJsonSchema`". "If set, `response_schema` must be omitted, but `response_mime_type` is required." |
| Gemini | Sends a schema of `type`, `enum`, `items`, `properties`, `additionalProperties`, `required` | Yes. All six are on the list of what is supported |
| Gemini | Sends `system_instruction`, `contents`, `maxOutputTokens` | Yes |
| Gemini | Sends `thinkingConfig.thinkingLevel` | **No.** `ThinkingConfig` holds `include_thoughts` and `thinking_budget` and no level. The file is older than the guide that names the level, so this neither confirms it nor rules it out |
| Gemini | Reads `finishReason`, and takes `STOP` alone as finished | Yes. The 18 values are as the report lists them |
| Gemini | Reads `promptFeedback.blockReason` | Yes. `SAFETY`, `OTHER`, `BLOCKLIST`, `PROHIBITED_CONTENT`, `IMAGE_SAFETY` |
| Gemini | Skips a part marked `thought` | Yes. `bool thought` is a field of a part |
| Gemini | Reads `promptTokenCount`, `cachedContentTokenCount`, `candidatesTokenCount`, `thoughtsTokenCount` | Yes |
| OpenAI | Sends `store: false` | Yes. The default is true, and then the call "will be stored for at least 30 days" |
| OpenAI | Sends `reasoning.effort` as `none` | Yes. `none` is a value. "Not all reasoning models support every value." |
| OpenAI | Sends `prompt_cache_options.mode` as `explicit`, and marks nothing | Yes. "If there are no explicit breakpoints, the request does not use prompt caching." It is "Supported for `gpt-5.6` and later models" |
| OpenAI | Sends the instructions with the role `system`, as a string | Yes. The roles are `user`, `assistant`, `system`, `developer`, and the content is a string or a list |
| OpenAI | Sends `text.format` with `type`, `name`, `strict`, `schema` | Yes |
| OpenAI | Reads `status`, and takes `completed` alone as finished | Yes. The six values are as the report lists them |
| OpenAI | Reads a content part of type `output_text`, and refuses one of type `refusal` | Yes. They are the two kinds |
| OpenAI | Counts a `failed` answer with the code `rate_limit_exceeded` as a cap | Yes. It is one of the codes |
| OpenAI | Reads `input_tokens`, `input_tokens_details.cached_tokens`, `output_tokens` | Yes |
| Anthropic | Sends `output_config.format` with `type: json_schema` and `schema` | Yes |
| Anthropic | Sends `thinking` as `{"type": "disabled"}` | Yes, as a value. Whether each model takes it is not said |
| Anthropic | Sends `system` as a string | Yes. A string, or a list of blocks |
| Anthropic | Reads `stop_reason`, and takes `end_turn` alone as finished | Yes. The seven values are as the report lists them |
| Anthropic | Reads `input_tokens`, `output_tokens`, and the two counts for the cache, which may be null | Yes |

## What this does not show

| Matter | Why |
|---|---|
| That any provider accepts the request as a whole | A definition names fields. Only a live call says whether they are taken together |
| Anything of DeepSeek | No definition was found. Its adapter rests on the report alone, which was read through an extraction |
| What people are told | Terms are not in a definition. `providers/terms.py` rests on the four reports, and on the later look below |
| The body of an error | None of the three files was searched for it. The adapters decide on the status |

## What was not read

| What | Standing | What was relied on |
|---|---|---|
| Google's terms and its usage policy, as the pages are served | Not read | The report, which read them through an extraction. Its sentences stay marked so |
| DeepSeek's terms and its privacy policy, as the pages are served | Not read | The same |
| The live service of any provider | No call was made | The documents |

## A later look at the pages, the same day

Made after a review of the adapters, by whoever put right what it found. The pages were asked for through a reader that summarises. For one host it gave back the page's own text. For the others it gave back an extraction, which can change a word. So nothing below counts as a person's check of a sentence. `providers/terms.py` holds every provider back until a person has made one.

### Which models take the request as it is sent

| Provider | Page | What it says | How it was read |
|---|---|---|---|
| Gemini | <https://ai.google.dev/gemini-api/docs/generate-content/thinking> | `minimal` is "Supported (Default)" for "Gemini 3.5 & 3.1 Flash-Lite", "Supported" for "Gemini 3.6 & 3.5 Flash", and "Not supported (error)" for "Gemini 3.8 & 3.7 Flash". The field is `generationConfig.thinkingConfig.thinkingLevel`. "The `max_output_tokens` generation parameter sets the maximum number of tokens a response can generate, including thought tokens." | Extraction |
| Gemini | <https://ai.google.dev/gemini-api/docs/generate-content/structured-output> | The REST example carries the schema in `generationConfig.responseFormat.text.schema`, with `mimeType` beside it. The table of models names Gemini 3.1 Flash-Lite and does not name 3.5 Flash-Lite | Extraction |
| Gemini | <https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite> | "Structured Outputs: Supported". "Thinking: Supported" | Extraction |
| Gemini | <https://ai.google.dev/api/generate-content> | Read in part, as far as the fields of `GenerationConfig` | Extraction |
| OpenAI | <https://developers.openai.com/api/docs/guides/reasoning> | "GPT-6 Astra does not support `none` reasoning effort. Setting `reasoning.effort` (Responses) or `reasoning_effort` (Chat Completions) to `none` returns HTTP 400." "GPT-6 Sol and Luna also default to `medium` reasoning effort." | Extraction |
| OpenAI | <https://developers.openai.com/api/docs/guides/prompt-caching> | `prompt_cache_options` is for "GPT-5.6 and later". "When no explicit breakpoints are placed, the request does not use prompt caching or create cache writes." What an older model answers to the field is not said | Extraction |
| DeepSeek | <https://api-docs.deepseek.com/api/create-chat-completion> | `model` is `deepseek-flash` or `deepseek-v4-pro`. `thinking` is "enabled" (the default) or "disabled". The list of the fields of `usage` names `completion_tokens`, `prompt_tokens`, `prompt_tokens_details`, `total_tokens` and `completion_tokens_details`. The example also holds `prompt_cache_hit_tokens` and `prompt_cache_miss_tokens` | Extraction |
| Anthropic | <https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting> | A table of what each model rejects with a 400. `"disabled"` is listed for Claude Fable 5.1, Mythos 5.1, Fable 5, Mythos 5, Mythos Preview and Opus 5.5. It is not listed for Claude Sonnet 5 or Claude Haiku 4.5. "any value not listed as rejected is accepted" | The page's own text |

### What people are told

| Provider | Page | What was found | How it was read |
|---|---|---|---|
| Gemini | <https://ai.google.dev/gemini-api/terms>, effective 23 March 2026 | The sentences on training and on "any country" are there, word for word. The page names no company | Extraction |
| Gemini | <https://ai.google.dev/gemini-api/docs/usage-policies>, updated 9 June 2026 | The 55 days, and review "only by authorized Google employees". It does not say whether what is flagged is kept for longer | Extraction |
| Gemini | <https://developers.google.com/terms>, last modified 9 November 2021 | "Google" means Google LLC, in the United States, "unless set forth otherwise in additional terms applicable for a given API" | Extraction |
| Gemini | <https://business.safety.google/processorterms/>, version 10, 7 May 2026 | Deletion "unless applicable laws require storage". Processing "in any country in which Google or its Subprocessors maintain facilities" | Extraction |
| OpenAI | <https://developers.openai.com/api/docs/guides/your-data> | The sentences on training and on 30 days are there, word for word. The page does not say who may read the data, or where it is handled by default | Extraction |
| OpenAI | <https://openai.com/enterprise-privacy/>, <https://openai.com/policies/data-processing-addendum/>, <https://openai.com/policies/services-agreement/> | Not read | Not read |
| DeepSeek | <https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html>, 10 February 2026 | The sentence on China is there. So is a sentence that the policy does not cover people who use a product built on the open platform. Data is kept "when necessary to comply with contractual and legal obligations", and "as necessary to process the violation" | Extraction |
| DeepSeek | <https://cdn.deepseek.com/policies/en-US/deepseek-terms-of-use.html>, 27 March 2026 | The sentence on use "to a minimal extent" is there, with the words on encryption and de-identification before it. A switch to refuse is named. Whether it reaches the API is not said | Extraction |
| DeepSeek | <https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html>, effective 29 April 2026 | Nothing on how long text is kept, on training, on place or on who may read it | Extraction |
| Anthropic | <https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data>, updated 1 July 2026 | The 30 days, the 2 years and the 7 years are there. The exceptions to the 30 days are listed, the law and the Usage Policy among them. It does not say who may read the data | Extraction |
| Anthropic | <https://privacy.claude.com/en/articles/7996890-where-are-your-servers-located-do-you-host-your-models-on-eu-servers>, updated 15 June 2026 | The three sentences on where traffic goes, where data is stored, and where internal processes run | Extraction |
| Anthropic | <https://www.anthropic.com/legal/commercial-terms>, effective 17 June 2025 | The sentence on training, and the company by where the customer resides | Extraction |
| Anthropic | <https://www.anthropic.com/legal/data-processing-addendum>, <https://privacy.claude.com/en/collections/10663361-commercial-customers> | Persons authorised to process are under a duty of confidentiality. No article of the thirty listed is about who may read what was sent | Extraction |

### What was not read

| What | Standing | What was relied on |
|---|---|---|
| A web search | None was made | Known addresses only. A page of a provider's that answers a question may exist and not have been found |
| Three pages of `openai.com` | Not read | The report, which read them as served. Its words were not seen a second time |
| The reference for `generateContent` | Read in part | Google's guide, and its published definition as read before |
| The live service of any provider | No call was made | The documents |
