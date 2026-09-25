# Models: four providers behind one interface

Burro reads a sentence into typed edits by rules, or by a model whose answer is then held to the rules (ADR 0002, ADR 0012). This document is about the model: which providers Burro can ask, how it asks, what people are told, and what is left to do.

| | |
|---|---|
| Status, 24 September 2026 | Built, tested and wired into the service. No adapter has met a live provider |
| Providers | Google Gemini, OpenAI, DeepSeek, Anthropic Claude |
| Which can be turned on today | Gemini, OpenAI and Claude, each once it is named, holds a key and has its terms accepted by name. DeepSeek never, for what people type. See section 2 |
| Code | `services/api/src/burro_api/providers/` |
| Tests | `services/api/tests/providers/`. Run `uv run --no-sync pytest services/api/tests/providers -q` |
| Evidence | `docs/research/models/`: one report a provider, and `definitions.md`, two later looks at the same pages |

A key alone turns nothing on. The service asks `choose` once, as it starts, and `choose` gives it a reader and what people are told of that reader together. Section 2 says what must hold before a model reads what is typed.

Nothing here is legal advice. Prices, model names and terms are a dated snapshot. Whoever wrote this was made by one of the four providers. Every question is put to all four in the same words, and every answer rests on a page that can be checked.

## 1. The interface

```python
class ModelClient(Protocol):
    def complete(
        self,
        *,
        system: str,
        user: str,
        schema: Mapping[str, object],
        model: str,
        max_tokens: int,
        timeout_s: float,
    ) -> ModelReply: ...
```

| Name | Meaning |
|---|---|
| `ModelReply.output` | The answer, as the text of one JSON object. Shown in no `repr` |
| `ModelReply.input_tokens` | Tokens sent and not read from a cache. Tokens written to a cache are among them |
| `ModelReply.output_tokens` | Tokens billed as output. Thinking is among them |
| `ModelReply.cache_read_tokens` | Tokens read from a cache |
| `ModelTimeout`, `ModelCapped`, `ModelRefused`, `ModelError` | The four failures. None has a message, a cause or a context. `ModelRefused` is a provider that would not read what was sent, for safety or for its own terms |

| File | What it holds |
|---|---|
| `interface.py` | The protocol, the reply and the four failures. The reader in `reader.py` imports them, and defines none of its own |
| `base.py` | `over_https`, the one function that sends, and `Adapter`, what the four share |
| `gemini.py`, `openai.py`, `deepseek.py`, `anthropic.py` | One adapter each: what to send, how to read the answer, and the models it was fitted to |
| `terms.py` | What people are told, and the address of each company's own terms. Also what a tool read of each provider's pages, which is research and is shown to nobody |
| `choose.py` | `choose(env)`: the adapter to use or none, and what the meta route should say |
| `measure.py` | The reader as the evaluation set asks for it. The service never uses it |

What every adapter does, the same way:

| Matter | Rule |
|---|---|
| The call | One HTTPS POST to a host that is a constant in code, port 443, certificate and name checked. No SDK, no dependency |
| The key | In one header. Never in an address, a log, a `repr`, a copy, a pickle or an exception |
| Redirects and retries | None. A redirect is an error, and where it points is never read |
| Time | One deadline for the whole call: the name, the connection, the handshake, the sending and every read |
| Size | 256 KiB of answer at most |
| An error's body | Never read. One exception: Anthropic's 400, to tell a spend limit from a bad request |
| The schema | Sent with every reference written out. Six keywords are left, which all four providers list. It is no longer than it was |
| The answer | Must be finished, by the provider's own word for it, and must be a JSON object. `reader._parsed` then holds it to the schema |
| Thinking | Asked to be off, or least. It is billed as output, and it can repeat the person's words |
| Never sent | An id for a person or a search, a tool, a cache mark, stored state, a temperature |
| The model | One of the models the adapter was fitted to, and no other. See below |
| After refusals | After 3 answers in a row of 400, 401, 403 or 404, the provider is asked nothing for 300 seconds. Then one call is let through |
| The certificates | The host's own. `SSLKEYLOGFILE` is never obeyed. `SSL_CERT_FILE` and `SSL_CERT_DIR` are. No proxy is read |

### The models each adapter was fitted to

An adapter sends one fixed setting for thinking. A model that does not take it answers 400 to every call. So an adapter takes only the models whose own documents say they take its request, and `choose` refuses any other name when the service starts, with `unfit_model`. Before this, any name of a provider's family was let through, and every sentence would have been sent and refused.

| Provider | Fitted | Its documents say | Known to refuse |
|---|---|---|---|
| Gemini | `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite` | `minimal` is "Supported (Default)" for "Gemini 3.5 & 3.1 Flash-Lite" | `gemini-3.8-flash`, `gemini-3.7-flash`: `minimal` is "Not supported (error)" |
| OpenAI | `gpt-6-luna`, `gpt-6-sol` | "GPT-6 Astra does not support `none` reasoning effort", and Sol and Luna do. `prompt_cache_options` is for "GPT-5.6 and later" | `gpt-6-astra`: 400 to `none`. `gpt-5.4-nano-2026-03-17` and `gpt-5.5`: older than the cache field |
| DeepSeek | `deepseek-flash`, `deepseek-v4-pro` | `thinking` is "enabled" or "disabled", with no model left out | `deepseek-chat`, `deepseek-reasoner`: retired on 24 July 2026 |
| Claude | `claude-haiku-4-5-20251001`, `claude-sonnet-5` | Neither lists `"disabled"` among what it rejects, and "any value not listed as rejected is accepted" | `claude-opus-5-5`, `claude-fable-5-1`, `claude-fable-5`: thinking is always on, and `"disabled"` answers 400 |

To add a model: read its own page for the setting for thinking and for structured output, add its name to `FITS` in the adapter with the address, and add it to `other` or `refuses` in `tests/providers/cases.py`. The alias `claude-haiku-4-5`, which the service has as its default today, is not on the list. The pinned name is.

Sources, all read on 23 September 2026: <https://ai.google.dev/gemini-api/docs/generate-content/thinking>, <https://developers.openai.com/api/docs/guides/reasoning>, <https://developers.openai.com/api/docs/guides/prompt-caching>, <https://api-docs.deepseek.com/api/create-chat-completion>, <https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting>. The last came back as the page's own text. The others came back through a reader that extracts.

### What each status becomes

| Status | Becomes | Basis |
|---|---|---|
| 408, 504 | timeout | 504 is documented by Google and Anthropic. 408 is named by Google only as a status to try again, and by OpenAI in its guide to Flex. Elsewhere, the meaning HTTP gives them |
| 402, 429 | capped | 429 is documented by all four. 402 by Google, DeepSeek and Anthropic. For OpenAI, the meaning HTTP gives it |
| 400 from Anthropic, where the message begins "You have reached your specified" | capped | Documented. The message is compared and let go of |
| 200 from OpenAI with `status: failed` and code `rate_limit_exceeded` | capped | Documented |
| Anything else that is not 200, every 3xx included | error | |
| 200 that is a refusal: Gemini's `promptFeedback.blockReason`, or its `finishReason` of `SAFETY`, `BLOCKLIST`, `PROHIBITED_CONTENT` or `SPII`. OpenAI's content of type `refusal`, or `incomplete` for `content_filter`. DeepSeek's `finish_reason` of `content_filter`. Claude's `stop_reason` of `refusal` | refused | Documented by each. Why it refused is never read |
| 200 that is cut short, is not JSON, or lacks a count of tokens | error | A number that is not known is never nought |

## 2. Settings

Read once, when the service starts: the command line hands `choose` the environment. A key alone turns nothing on.

| Variable | Meaning | Default |
|---|---|---|
| `BURRO_MODEL_PROVIDER` | `gemini`, `openai`, `deepseek` or `anthropic` | None. There is no default in code |
| `GEMINI_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY` | The key of the provider that is named | None |
| `BURRO_MODEL_TERMS_ACCEPTED` | The same provider's name. It says that whoever runs the service has read its terms and taken them on | None |
| `BURRO_MODEL_ID` | The model | The provider's entry in `terms.py` |
| `BURRO_MODEL_TIMEOUT_S`, `BURRO_MODEL_MAX_TOKENS` | How long an answer is waited for, and the most it may hold | 6 seconds, 2,048 tokens |
| `BURRO_MODEL_CALLS_PER_MINUTE`, `BURRO_MODEL_CALLS_PER_DAY` | The most calls the whole service makes to a model in a minute, and in a day by the clock in UTC. A whole number, from nought to 600 and to 100,000. Nought means the model is never called. Over a cap the rules read, as where a provider says that it is capped: [ADR 0032](../adr/0032-calls-to-a-model-are-capped-for-the-whole-service.md) | 30 calls, 2,000 calls |
| `BURRO_MODEL_SENDS_SETTINGS` | `yes` sends the search settings to the provider with the words. Section 6 says what goes | Not set: the words go alone |

A model reads what is typed only when all six hold. They are looked at in this order, and the first that fails is the reason. `choose` looks at the first five, and the service at the sixth.

| # | What must hold | If not |
|---|---|---|
| 1 | The provider is one of the four | `no_provider`, `unknown_provider` |
| 2 | Its key is present and fit for a header | `no_key`, `unfit_key` |
| 3 | The terms are accepted for that provider | `terms_not_accepted` |
| 4 | The model is one the adapter was fitted to | `unfit_model` |
| 5 | The provider is one that may read what real people type. DeepSeek is not | `not_for_people` |
| 6 | Neither cap on calls to a model is nought | `capped_at_nought` |

Otherwise the rules read, and one line is logged, at the level of a warning. It holds two fixed words and no more: `provider`, the provider that is not used, and `reason`, the first of the six that does not hold.

```json
{"at": "2026-09-24T09:00:00Z", "event": "model_not_used", "level": "warning", "provider": "gemini", "reason": "no_key"}
```

Where what was set names none of the four, the line holds no `provider`. With nothing set, nothing is logged. Nothing that was set is ever logged, because a value in the wrong variable could be a key.

These three, with its key, are what whoever runs the service sets for Gemini. Nothing waits on a person's check of `terms.py`: the founder decided against one (ADR 0023).

```sh
BURRO_MODEL_PROVIDER=gemini  BURRO_MODEL_TERMS_ACCEPTED=gemini  BURRO_MODEL_ID=gemini-3.5-flash-lite
```

## 3. The four, side by side

Costs are for 1,000 searches of 3,000 tokens in and 300 out, not cached, in US dollars. Token counts are estimates until measured. The rows on what a provider does with what it is sent are what a tool read of its pages. Nobody has checked them, and none is shown to people: section 6.

| | Gemini | OpenAI | DeepSeek | Claude |
|---|---|---|---|---|
| Call | `generativelanguage.googleapis.com` `/v1beta/models/{model}:generateContent` | `api.openai.com` `/v1/responses` | `api.deepseek.com` `/chat/completions` | `api.anthropic.com` `/v1/messages` |
| Key header | `x-goog-api-key` | `Authorization: Bearer` | `Authorization: Bearer` | `x-api-key`, with `anthropic-version` |
| Schema goes in | `generationConfig.responseJsonSchema` | `text.format`, `strict` | The instructions, as words | `output_config.format` |
| Schema enforced | Yes. Unknown keywords are ignored | Yes. An unknown keyword is refused | **No.** Valid JSON only | Yes |
| Finished | `finishReason` is `STOP`, prompt not blocked | `status` is `completed`, no refusal | `finish_reason` is `stop` | `stop_reason` is `end_turn` |
| Thinking | `minimal`. Cannot be off | `effort: none` | `disabled` | `disabled` |
| Stores the call | No | No, with `store: false`, which is sent | No | No |
| Model | `gemini-3.5-flash-lite` | `gpt-6-luna` | `deepseek-flash` | `claude-haiku-4-5-20251001` |
| Its name | Stable. No date to retire | Cannot be pinned to a version | Not pinned. Moved to a new model on 10 September | Pinned. May be given 60 days' notice from 15 October 2026 |
| Cost | 1.65. Plan on 1.90 with thinking | 0.45. Plan on 0.60 | 1.26 at peak, 0.63 off it | 4.50. 11.70 on the next model up |
| Kept | 55 days | Up to 30 days | No period is given | Up to 30 days |
| Kept longer if misuse is suspected | Not said | Yes. No period is given | Yes. No period is given | Up to 2 years, and safety scores up to 7 |
| Kept longer by law | Yes | Yes | Yes | Yes |
| Can the period be shortened | No | To none, by approval | Not said | To none, by arrangement. Not for what is flagged |
| Used to train | No, on the paid tier | No, unless opted in | The terms allow it, "to a minimal extent" | No, unless a programme is joined |
| Who may read it | Staff, if flagged | Staff, and contractors who look into misuse | Not said | Not said |
| Where handled | Any country | Not said. Europe by approval | China | United States, Europe, Asia, Australia and others |
| Where stored | Any country | Not said | China | United States |
| A region can be chosen | No | Europe, by approval, at 10% more | No | No, on this API |
| The company | Google LLC, United States | OpenAI OpCo, LLC, United States | Hangzhou DeepSeek Artificial Intelligence Co., Ltd., China | Anthropic Ireland, Limited, Ireland |
| Processing agreement | Yes, with the terms | Yes, with the terms | None published | Yes, with the terms |
| Transfer from the UK | Data Privacy Framework, UK Extension | UK Addendum | None named | UK Addendum |
| On sensitive data | The agreement is silent | "No sensitive data is intended" | "you should not provide" it | Lists "None" |
| Age | Adults only | No minors without a guardian | Guardian's consent under 18 | Nothing asked for end users |
| Where its own pages were found to disagree | In seven places | On whether a product may name the provider | On which model answers to `deepseek-v4-pro` | On whether text is kept by default, and on whether a refusal is billed |
| Checked by a person | No | No | No | No |

What each adapter rests on that nobody has seen a live service do:

| Provider | Unverified |
|---|---|
| All four | Nothing was tested against a live service. Whether the schema is accepted at its size. Whether `User-Agent: burro` and `Accept` are taken |
| Gemini | Which of two fields carries the schema: section 9. `thinkingLevel` is on Google's guide and not in its published definition, which is older. The shape of an error body. That a count left out is nought. Whether `SPII` fires on a workplace |
| OpenAI | The body of an error, which is shown only in a cookbook. 402 and 504, which are on no page. Two answers in `terms.py` rest on pages of `openai.com` that were read once and not a second time |
| DeepSeek | Every fact: all were read through an extraction, and no published definition was found. No error body is documented. 408 and 504 are on no page. How often the shape is wrong. Its privacy policy says it does not cover people who use a product built on its API |
| Claude | 408, which is on no page. That the message of a spend limit still begins as documented. What a retired model answers |

## 4. Which to start with

Start with **Gemini**, as the founder asked. The evidence does not rule it out, and does not put it first. No one has measured how well any of the four reads a sentence, so section 7 decides, not this table.

The same tests are put to each. "Yes" is what a UK service that sends people's words would want.

| Test | Gemini | OpenAI | DeepSeek | Claude |
|---|---|---|---|---|
| The provider enforces the schema | Yes | Yes | **No** | Yes |
| A processing agreement is published | Yes | Yes | **No** | Yes |
| A safeguard for the transfer is named | Yes | Yes | **No** | Yes |
| It says it does not train on what is sent | Yes | Yes | **No** | Yes |
| It gives a period for keeping it | Yes, 55 days | Yes, up to 30 days | **No** | Yes, up to 30 days |
| It gives a period for what it flags | **No** | **No** | **No** | Yes. It is 2 years, and 7 for scores |
| It says who may read it | Yes | Yes | **No** | **No** |
| It says where it is stored | Yes. Any country | **No** | Yes. China | Yes. The United States |
| It can be kept in the UK or Europe | **No** | By approval | **No** | **No** |
| Its agreement plans for sensitive data | Silent | **No** | **No** | **No** |
| The model's name is pinned | A stable name, with no date to retire | **No** | **No** | Yes, and it may be given notice from 15 October 2026 |
| No two of its pages were found to disagree | **No**. Seven places | **No**. One | **No**. One | **No**. Two |
| Cost of 1,000 searches | 1.65 | 0.45 | 0.63 to 1.26 | 4.50 |

What follows from it:

| Provider | Reading |
|---|---|
| DeepSeek | **Not for real people's words as its documents stand.** It fails the three tests a UK controller cannot do without: an agreement, a safeguard for the transfer, and a period. The adapter is for made-up sentences |
| Gemini, OpenAI, Claude | None is ruled out, and none is clear of a "No". Each asks the founder to accept something: section 10 |

Before Gemini is turned on:

1. `choose` decides, which it now does.
2. Its terms are accepted by name, in `BURRO_MODEL_TERMS_ACCEPTED`. Nobody has compared `terms.py` with Google's pages, and nothing waits for that (ADR 0023).
3. Billing is on for the key's project. Google's terms allow no free tier for people in the UK.
4. ADR 0005 is amended: "up to 30 days" is not true of Gemini.
5. The first live call is made with a made-up sentence, and the questions of section 9 are answered.
6. Section 7 is run on Gemini and on one other.

## 5. Handing over a key

Until a provider's terms are accepted, a key belongs on your own machine, for the measuring of section 7, and nowhere else. On a host that serves people it turns nothing on, and it is one more secret to lose.

The key is never typed into a chat, a file in the repository, or a command line that is recorded.

| Step | How |
|---|---|
| Make it | In the provider's console, in a project or workspace made for Burro alone, with a monthly cap on spending |
| For a run on your own machine | `read -rs GEMINI_API_KEY && export GEMINI_API_KEY`, then paste. The shell shows nothing and records nothing. Close the shell after |
| For the service | Put it in the host's store of secrets, through the host's web page, or through a command that reads the value from standard input. Never as `NAME=value` on a command line |
| Never | In `.env` in the repository, in `uv run ... KEY=...`, in a test, in a message to an assistant |
| If it is ever seen | Revoke it in the console and make another. Do not try to clean it up |

What the host must have, or every call is an error and the rules answer:

| Matter | Why |
|---|---|
| A list of certificate authorities | The standard library trusts the host's own. The SDK it replaces carried one. An image with none cannot make a connection |
| A way out on port 443 with no proxy | The adapters read no proxy setting |
| `SSLKEYLOGFILE` unset | It is not obeyed, so it does no harm. It has no place on a host that serves people |
| `SSL_CERT_FILE` and `SSL_CERT_DIR` unset, or set by you | They are obeyed. Whoever can set them chooses whose certificates are trusted |

## 6. What people are told

`choose(env).told` holds it: whether a model reads what is typed, the provider, the company, the notice, the address of the company's own terms, and whether the search settings are sent. The website and the app show what the API serves and write none of it themselves.

### The notice

A few sentences, the same for every provider but for the company's name. They say that what is typed is sent to a language model run by the company, to be read, what goes with it, that nothing private should be typed, and that Burro itself keeps nothing of what is typed. The last points to the company's own terms, and the API serves their address beside the notice, as `terms_url`, for a client to make a link of.

**The notice states nothing about the company as fact.** Not how long it keeps what it is sent, not whether it trains on it, not who may read it or where. Nobody has checked those, and the link serves in their place (ADR 0023).

The notice for Gemini, as `terms.py` makes it where the words go alone:

> What you type is sent to a language model run by Google, to be read. Your words go alone: none of your search settings is sent with them. Do not type anything private. Burro itself keeps nothing of what you type. What Google does with it is in Google's own terms.

And where the settings are sent with them:

> What you type is sent to a language model run by Google, to be read. With it go your search settings: your budget, whether you rent or buy, how long you will travel, what matters to you, and the areas you have ruled in or out. Do not type anything private. Burro itself keeps nothing of what you type. What Google does with it is in Google's own terms.

With no model: "What you type is read by rules that are part of Burro. It is not sent to a language model."

| Company | The link that is served |
|---|---|
| Google | <https://ai.google.dev/gemini-api/terms> |
| OpenAI | <https://openai.com/policies/services-agreement/> |
| DeepSeek | <https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html> |
| Anthropic | <https://www.anthropic.com/legal/commercial-terms> |

What is typed is sent as typed. Nothing is taken out of it or put in its place before it goes: there is no sanitiser and no classifier. A person's own information is theirs to share (ADR 0023).

### What is sent

The words go alone unless the service is set to send the search with them. One setting decides it, `BURRO_MODEL_SENDS_SETTINGS`, and only the one word `yes` turns it on. It is off unless it is set. The reader and the notice are both made from it, and a `Choice` cannot be made that sends the settings and tells people the words go alone.

| `BURRO_MODEL_SENDS_SETTINGS` | What leaves with the words | What every notice says |
|---|---|---|
| Not set, or anything but `yes` | Nothing of the search. The instructions, which hold the names of the features and the vibes, are Burro's own and the same for everyone | The sentence below that begins "Your words go alone" |
| `yes` | The search as it stands: the budget in pounds, whether to rent or buy, each journey's time and mode, every weight and tag, and every area that is ruled in or out, by its id. The one thing taken out is where a journey leads. On real data an area's id names a real neighbourhood | The sentence below that begins "With it go" |

> Your words go alone: none of your search settings is sent with them.

> With it go your search settings: your budget, whether you rent or buy, how long you will travel, what matters to you, and the areas you have ruled in or out.

`SENT_WITH` in `terms.py` names each field of a search and the words that tell of it. A test sends a whole search through the real reader with the setting on, and fails if a field leaves that the notice does not name. Another sends the same search with the setting off, unset and set to a word that is not `yes`, and fails if anything of the search is in what leaves.

What is offered of a model's answer does not depend on what was sent. The guard holds each reading to the person's words and to the search the service holds, and never reads what the model was sent. Nothing a model reads is applied (contract, section 8.2). Section 7 says what was measured, and what a stand-in cannot measure.

### The table of terms: research, checked by nobody and shown to nobody

`terms.py` also holds what a tool read of each provider's pages on 23 September 2026: eight questions, put to every provider in the same order, each with one sentence for an answer and one for the lack of one. No person has compared a sentence with its page, so `checked_by` and `checked_on` are empty in every entry. Nothing of the table is served, put in a notice or waited for. It is kept for whoever next reads the providers' terms.

| Question | If the documents answer | If they do not |
|---|---|---|
| `receiver` | When you type a sentence, Burro sends it to {company} ({answer}). | When you type a sentence, Burro sends it to {company}, which does not say which of its companies receives it. |
| `training` | {company} says it {answer}. | {company} does not say whether it uses them to train its models. |
| `kept` | It keeps them for {answer}. | It does not say how long it keeps them. |
| `by_law` | It may keep them for as long as the law requires. | It does not say whether it keeps them for longer where the law requires it. |
| `if_misuse` | If it suspects misuse, it {answer}. | It does not say whether it keeps them for longer if it suspects misuse. |
| `read_by` | They may be read by {answer}. | It does not say who may read them. |
| `handled` | They may be handled in {answer}. | It does not say where they are handled. |
| `stored` | They are stored in {answer}. | It does not say where they are stored. |

### The answers

| Question | Google | OpenAI | DeepSeek | Anthropic |
|---|---|---|---|---|
| `receiver` | Google LLC, United States | OpenAI OpCo, LLC, United States | Hangzhou DeepSeek Artificial Intelligence Co., Ltd., China | Anthropic Ireland, Limited, Ireland |
| `training` | Does not use them to train its models | Does not use them to train its models | May use them to improve its service and the technology under it, to a minimal extent and with what identifies a person taken out. Its documents name no way for a service like Burro to refuse | Does not use them to train its models |
| `kept` | 55 days | Up to 30 days | Does not say | Up to 30 days |
| `by_law` | It may | It may | It may | It may |
| `if_misuse` | Does not say | May keep them for as long as it finds necessary, and gives no period | May keep them for as long as it finds necessary, and gives no period | Keeps them for up to 2 years, and its safety scores for up to 7 years |
| `read_by` | Its staff, if it suspects misuse | Its staff, and by contractors who look into misuse | Does not say | Does not say |
| `handled` | Any country where Google or its agents have facilities | Does not say | China | The United States, Europe, Asia and Australia, and wherever it or its affiliates work |
| `stored` | Any country where Google or its agents have facilities | Does not say | China | The United States |

### What whoever reads the table should know

Each answer in `terms.py` holds the provider's own words, the address, the day, how the page was reached, and a note where there is one.

| Provider | Point |
|---|---|
| All four | "Does not say" is a statement too. It means the pages at the addresses given were read and held no answer. Another page of the provider's may hold one |
| Gemini | Every page came back through a reader that extracts. "It may", for the law, rests on the agreement on data processing and not on the page about the 55 days. The words on where it is stored are of data "stored transiently or cached". The Gemini API's own terms, as read, name no company |
| OpenAI | `openai.com` was read once on the day, and not again. Who receives the words, and who may read them, rest on that reading alone. No page read names the countries where a call is handled |
| DeepSeek | Every page came back through an extraction. The privacy policy says it does not cover people who use a product built on the API, and the terms for the API say nothing of keeping, reading or place. The terms name a switch to refuse training. No page says whether it reaches the API |
| Claude | The page on how long text is kept lists the law and the Usage Policy among its exceptions. Another page says text "is not retained by default", and points to this one. No page read says who may read what was sent |

### When a provider would not read a sentence

What is typed is sent as typed, so a provider may refuse it, for safety or for its own terms. The rules then read the sentence as they would with no model, and route 1 says `model_refused: true` beside `degraded: true`. A client shows one line: that the language model would not read this, and that Burro's rules have.

| What | Where |
|---|---|
| The call | On record with the status `refused`, as the `interpret` line has it in `call_status`. No line is written for a refusal alone, and nothing counts them |
| What was typed | Nowhere. Nor why the provider refused, where in the text, or who sent it |

A client that abuses the service is blocked afterwards by its address, at the host's edge: `deploy/README.md`. Burro holds no account, follows nobody and keeps nothing of a search (ADR 0023).

## 7. Measuring a provider before it is turned on

The set is `evals/reader`: made-up sentences, so nothing private is sent. `measure.py` makes the reader from the provider's name and its key, and asks nothing of the terms. It takes only a model the adapter was fitted to, and it sends what the service would send. It needs no change to any file.

```sh
read -rs GEMINI_API_KEY && export GEMINI_API_KEY
export BURRO_MODEL_PROVIDER=gemini BURRO_MODEL_TIMEOUT_S=30
uv run python evals/reader/score.py --reader model --workers 4 --save evals/reader/baseline/gemini.json
```

Run it three times. A model does not answer the same way twice. One run of 781 cases costs about $1.30 on Gemini. The run is held to Gemini's floor in `floor.json`, which has no limit yet, so it fails only where a case is reversed.

Then run it once more with `BURRO_MODEL_SENDS_SETTINGS=yes`, save it to another file, and compare the two with `--against`. That is the measurement decision 3 of section 10 waits for.

| Measure | Good enough | Why |
|---|---|---|
| Reversed | None, in each of three runs | One reversed case fails a run (`evals/README.md`) |
| Unasked | No more than the rules' ceiling in `floor.json` | The model is held to the rules, so it should invent no more than they do |
| Read correctly | More than the rules read on the same day, in each of three runs | If it reads no more, it buys nothing and costs a person's privacy |
| Failed | Under 2 in 100, at the service's own 6 seconds | Each failure is a wait and then the rules |
| Cost | The tokens the scorer prints, priced from section 3, within half as much again of the estimate | To catch thinking that was not turned off |
| The first call | The schema is accepted. Tokens out are hundreds, not thousands | Neither can be known from a page |

These are proposed. The founder sets the floor, in `floor.json`, after the first run.

### What a stand-in shows, before any provider is called

`evals/reader/stand_in.py` measures the guard with two stand-ins for a model, one that reads each case as it is meant and one that raises whatever a sentence names. It calls no provider. `evals/README.md` has the table. On the 781 cases, on 24 September 2026:

| Question | Answer |
|---|---|
| Is anything a model reads applied? | No. No case is reversed and none holds an edit nobody asked for, for either stand-in |
| Does what is offered depend on what was sent? | No. Not one case ends otherwise, for either stand-in |
| What can a model add that reads every sentence well? | To press every guess reads 401 cases rightly, and 44 more in part. The rules alone apply 408 and offer 232 |
| What do the checks let a careless model do? | 92 cases are a backwards guess, and 47 hold a guess nobody asked for. Nothing of either is applied until it is pressed |
| Is any reading of the rules lost because a model is on? | None |
| What can a stand-in not say? | Whether a real model reads a follow-up less well with the words alone, and how often a real model reads a turn backwards |

The floor below which no model is turned on is in the contract, section 8.2, and ADR 0012. One model has been measured against it once, on 112 sentences, and its answers are kept in `evals/reader/answers/`. That is a fit and not a measurement: the checks were chosen after reading those answers. Before a provider is turned on, measure it on sentences the checks were not fitted to.

## 8. What the wiring step changes, in order

Each is a change to a file that exists. The last column says which are done. Step 5 is the one that matters most: since it was done, a key alone turns nothing on.

The table is what was done then. Two things in it were changed afterwards, by ADR 0023: no provider waits on a person's check, and `reader` serves the notice and the address of the company's own terms, with no `sources`.

| # | File | Change | Done |
|---|---|---|---|
| 1 | `services/api/src/burro_api/claude.py` | Delete its `ModelFailure`, `ModelTimeout`, `ModelCapped`, `ModelError`, `ModelReply` and `ModelClient`. Import them from `providers/interface.py`. Take the expected-failure mark off `tests/providers/test_interface.py`. Until this is done the route counts an adapter's timeout or cap as an error | Yes |
| 2 | `services/api/src/burro_api/logs.py` | Add `provider` and `reason` to `LOGGABLE`, and a way to write a warning. Then `choose._warn` writes `model_not_used` with `provider` and with `reason`, which is the refusal's fixed word, and the four event names go. `reason` is for the founder to confirm: section 10 | Yes |
| 3 | `services/api/src/burro_api/settings.py` | Drop `DEFAULT_MODEL_ID`, `KEY_VARIABLE`, `model_id` and `model_key_present`. The model and the key are `choose`'s. The alias `claude-haiku-4-5` is not a model any adapter takes. A model's name that is not fit no longer stops the service from starting: the rules read, and the line says `unfit_model` | Yes |
| 4 | `services/api/src/burro_api/deps.py` | `Deps` gains `told`, with **no default**. A default would be "not sent to a language model", said of a service that sends. Whoever makes a `Deps` takes `told` from the same `Choice` as the interpreter, and a `Choice` cannot be made with the two at odds | Yes |
| 5 | `services/api/src/burro_api/app.py`, `cli.py`, `tests/test_app.py` | The command line calls `choose(os.environ)`, and `deps_from` builds the interpreter from `choice.client` and `choice.model` and passes `choice.told`. A `Deps` cannot be made that tells people other than who reads. The line `starting` names the provider. The test that a key alone selects the model is turned round. The expected-failure mark is off `tests/providers/test_design.py`, and the three warnings are out of this document | Yes |
| 6 | `services/api/src/burro_api/wire.py`, `routes/meta.py`, `routes/common.py` | `MetaData` gains `reader`: `model_reads`, `provider`, `company`, `notice`, `settings_sent`, `sources`. A source holds `question`, `says`, `answered`, `addresses`, `read_on` and `checked_on`. Who reads is no part of the release, so the `ETag` of route 11 now names the release and what is told: a browser that holds an answer which tells of another reader is answered in full. Then `make openapi`, `make web-types` and `make web-record` | Yes |
| 7 | `services/api/src/burro_api/calls.py`, `routes/interpret.py` | `CallRecord` and the `interpret` line gain `provider`, from the closed list, empty where the rules read. Each time a provider begins to be left alone, one warning is written, `model_resting`, with `provider` and nothing of the call | Yes |
| 8 | `services/api/src/burro_api/claude_sdk.py`, `tests/test_claude_sdk.py` | Delete both. `tests/conftest.py` no longer names the SDK's logger. A test holds the service to no provider's library | Yes |
| 9 | `services/api/pyproject.toml` | Remove `anthropic>=1,<2`. One line in the pull request: a dependency is dropped, none is added. Three packages that it alone needed go with it | Yes |
| 10 | `claude.py`, `tests/test_claude.py`, `tests/test_claude_kept.py` | Rename to `reader.py`, `test_reader.py`, `test_reader_kept.py`. `ClaudeInterpreter` becomes `ModelInterpreter`. What imports them follows: the routes, `tests/support.py`, `providers/measure.py` |Yes |
| 11 | `packages/core` `ids.InterpreterName`, `calls.Caller` | `claude` becomes `model`. This is on the wire, so `contracts/openapi.json`, the website's types and its recorded answers are made again. The version of the contract stays 2: nothing was deployed when this was done, and every client is generated from the one file. The iPhone app's models are not made again here: section 8.1 says what they need | Yes |
| 12 | `evals/reader/model_reader.py`, `score.py`, `floor.json`, `evals/README.md` | `model_reader.py` is deleted: `--reader model` asks for `providers.measure.reader`. `--reader claude` is gone. A model is held to the floor of the provider the environment names, and `floor.json` holds one for each of the four, with no limit yet | Yes |
| 13 | `apps/web` | The search page shows `reader.notice` by the text box, before anything is typed, as it was served. It asks the service as the page opens and shows nothing of what it was built on in its place, and it sends no sentence until the service has said who reads. The methods page shows the notice with the pages each sentence was read on. No provider's name or terms is in the website's own source, and two tests say so. `apps/ios` is not done: section 8.1 | Yes, for the website |
| 14 | `docs/design/contract.md` | Sections 1, 8.2, 9.2, 9.3, 9.5, 10.1, 10.2, 11 and 13: the chooser, what is sent, the meta route and its tag, the new log fields, `provider` on the call record | Yes |
| 15 | `AGENTS.md`, `services/api/AGENTS.md`, `README.md`, `deploy/README.md`, `docs/PLAN.md` | Where they say Claude, a key that selects the model, or an SDK. The rule "only `claude_sdk.py` imports the SDK" becomes "nothing imports a provider's library", with its test | Yes, but for `docs/PLAN.md`, which still speaks of one provider in its account of the architecture |
| 16 | `docs/adr/0005` | Amended: what a provider keeps is in `providers/terms.py`, by provider. It is not "up to 30 days" for all. The words go alone unless the service is set to send the search with them | Yes |
| 17 | `docs/adr/0019` | A new record: no one provider; no SDK; a key alone turns nothing on; every provider held until a person has checked what people are told of it; what is served to people | Yes |
| 18 | `docs/research/models/anthropic.md` | Renamed from a name that differed only by case from the name of an instructions file for coding agents, so that a tool that ignores case does not load a report as instructions | Yes |
| 19 | The privacy notice and the impact assessment, in `docs/legal/` | The notice names the four providers, says what never changes, and points to the notice by the box for the countries and the periods, so that it is true whichever provider reads. It says that all four are held until a person has checked them | Yes, for the notice. The impact assessment is not written: it is task 17 of the launch checklist |

### 8.1 What the iPhone app needs

Nothing under `apps/ios` was changed, and the app was not built. Its check fails until this is done on a Mac:

| What | Why |
|---|---|
| `make -C apps/ios generate` | `APIModels.swift` is generated from `contracts/openapi.json`. `InterpreterName` holds `model` where it held `claude`, `MetaData` gains `reader`, and `Reader`, `ReaderSource`, `Provider` and `Question` are new. The recorded answers are copied from the website's, which hold the new name and two new answers, `meta-model-reads` and `meta-model-reads-with-settings` |
| `SearchCopy.swift` | The word for who read a sentence is keyed by the old name: key it by `model`. Its line on how long a provider keeps words says "up to 30 days", which is true of two of the four: take it out, and show what is served |
| `PermissionView` and `Consent` | The app asks before a sentence is sent. What it shows is to be `reader.notice`, as served, and no provider's name or terms of its own. Where `reader.model_reads` is false it says that no language model reads what is typed |
| `Search/` | It follows the website's `state.ts` and `flow.ts` event for event. Both gained who reads: `reader` and `readerFailed` in the state, the events `reader_said` and `reader_unsaid`, `loadReader`, and the rule that `submitText` sends no sentence while `reader` is `null`. Port them, and their tests |
| A test | That no provider's name or terms stands in the app's own source, as `apps/web/test/privacy/source.test.ts` and `apps/web/test/site-copy.test.ts` hold the website |

After a change to any of these, run the verify skill: drive route 1 with a made-up sentence and no key, then with a key and nothing else, then with a key and no accepted terms, and see the rules answer all three times.

## 9. To confirm with the first real call

The documents do not settle these. Each is a question with an answer that can be written down. Make the first call with a made-up sentence, on your own machine, with 30 seconds allowed. It prints what came back and how long it took, and none of the words.

```sh
read -rs GEMINI_API_KEY && export GEMINI_API_KEY
BURRO_MODEL_PROVIDER=gemini BURRO_MODEL_TIMEOUT_S=30 uv run python - <<'EOF'
import time
from burro_api.loading import load_release
from burro_api.providers.measure import reader
from burro_api.settings import SYNTHETIC_FIXTURE
from burro_core import default_spec
from burro_core.ids import Tenure
from burro_core.interpret import InterpretRequest

asked = InterpretRequest(
    "30 minutes to Cindermoor Works", default_spec(Tenure.RENT), load_release(SYNTHETIC_FIXTURE)
)
made = reader()
for call in (1, 2):
    began = time.monotonic()
    try:
        print(call, "answered", made.interpret(asked).usage)
    except Exception as failure:
        print(call, "failed", type(failure).__name__)
    print(call, round(time.monotonic() - began, 1), "seconds")
EOF
```

A failure says only which of the three it was. To see a status, make the same request once with the provider's own example and `curl`, with a made-up sentence.

| # | Provider | The question | If the answer is no |
|---|---|---|---|
| 1 | All four | Is the schema accepted as it is sent: about 5,600 characters, 7 closed objects, 51 fields, 174 choices? | A 400 on the first call. Look at the schema before anything else |
| 2 | All four | How many seconds does the first call with the schema take, and the second? Is 6 seconds enough for the first call after a deploy, and after a day with no calls? | The first person after each deploy waits 6 seconds and is answered by the rules. Decide whether the service makes one call of its own as it starts |
| 3 | All four | When a call is given up at the deadline, does the provider keep the schema it had begun to compile, so that the next call is quick? | Every call after a quiet day times out until one is allowed to run long |
| 4 | All four | Does the provider's edge take `User-Agent: burro` and `Accept: application/json`? | A 403 or 406 on every call. Change the two lines in `base.py` |
| 5 | All four | Does the handshake succeed with the host's own certificates, on the image the service will run on? | Every call is an error. Put a list of authorities on the image |
| 6 | Gemini | Does `generateContent` take the schema in `generationConfig.responseMimeType` with `generationConfig.responseJsonSchema`, on `gemini-3.5-flash-lite`? Google's published definition names these. Its guide shows `generationConfig.responseFormat.text.mimeType` with `generationConfig.responseFormat.text.schema` | A 400. Send the second form by hand. If it is taken, change `body` in `gemini.py` and its test |
| 7 | Gemini | Does it take `generationConfig.thinkingConfig.thinkingLevel` as `"minimal"`? What is `thoughtsTokenCount`? Google's guide says thinking counts against `maxOutputTokens` | A 400. Leave the field out: `minimal` is the default on both fitted models |
| 8 | Gemini | The guide's list of models that take a schema does not name `gemini-3.5-flash-lite`. The model's own page says "Structured outputs: Supported". Which is right? | Fall back to `gemini-3.1-flash-lite`, which both name |
| 9 | Gemini | With billing off, is the answer 400 with `FAILED_PRECONDITION`? What is the status when the tier's monthly cap is reached? | Nothing to change. After three such answers the adapter rests |
| 10 | Gemini | Does `finishReason` come back as `SPII` for a sentence that names a made-up workplace? | The model cannot read a journey. It would be a reason to choose another |
| 11 | OpenAI | Does `gpt-6-luna` take `reasoning.effort` as `none` together with `text.format` and `strict`? Is `reasoning_tokens` nought? | A 400, or a bill for thinking |
| 12 | OpenAI | Does it take `prompt_cache_options` with `mode` as `explicit` and nothing marked? Is `cached_tokens` nought on the second call? | A 400, or the person's words are written to the cache |
| 13 | OpenAI | What is the status when the project's monthly limit is reached: 429, as documented? Is 402 or 504 ever seen? | Nothing to change. It alters only what is counted |
| 14 | DeepSeek | Does `usage` hold `prompt_tokens`? By which name does it give the tokens read from the cache? | Nothing to change. Either name is read |
| 15 | DeepSeek | The schema is not enforced. Of the 781 made-up sentences, how many answers fail it? | Above 2 in 100, build the strict route or choose another |
| 16 | DeepSeek | Which model does the answer's own `model` field name when `deepseek-v4-pro` is asked for, and at what price? Two pages disagree | Take `deepseek-v4-pro` off the list |
| 17 | DeepSeek | Under load, do the empty lines arrive before the status line or after it? | Nothing to change. Both are read, within the one deadline |
| 18 | Claude | Does `claude-haiku-4-5-20251001` take `thinking` as `disabled` together with `output_config.format`? The table of what each model rejects says it does | A 400. Leave the field out for that model: its thinking is off unless asked for |
| 19 | Claude | What does a retired model answer, status and `error.type`? The documents say only that it "will fail" | Nothing to change. After three such answers the adapter rests. The smallest model may be given notice from 15 October 2026 |
| 20 | Claude | Does the message of a limit the customer set still begin "You have reached your specified"? | It is counted as an error and not as a cap, and after three the adapter rests |

## 10. For the founder to decide

| # | Decision | What is built until you say otherwise |
|---|---|---|
| 1 | **What lets a provider be turned on.** Before, two providers could be turned on and two could not, Gemini among the two that could not. The difference was in how each provider's pages had been read, not in what the pages say. A second reading found the sentences of all four, but for two of OpenAI's, whose pages were not read a second time | Decided on 24 September 2026: no check by a person. A provider is turned on when it is named, holds a key, has its terms accepted by name and is asked for a model its adapter was fitted to: ADR 0023 |
| 2 | Whether the reason a model is not used may be logged beside the provider's name. It is a fixed word such as `no_key`, and never a thing that was set | Decided: the line says which provider is not used and why. Section 2 shows it |
| 3 | Whether the search settings should go to the model with the words. A model may read a follow-up better if it is sent the search: "make the second one shorter". No real model has been measured either way. Section 7 says what a stand-in shows, and what the first measurement of a real model must compare | One setting, `BURRO_MODEL_SENDS_SETTINGS`, off unless it is `yes`. Off, the words go alone. The notice says which, from the same setting |
| 4 | Whether `SSL_CERT_FILE` and `SSL_CERT_DIR` are honoured. They are how a host names its certificates. They also let whoever sets them choose whose certificates are trusted | Honoured. `SSLKEYLOGFILE` is not |
| 5 | How long to leave a provider alone after it refuses, and after how many refusals. And whether a cap should count: while a monthly limit is reached, every sentence is still sent and refused | 300 seconds, after 3 in a row of 400, 401, 403 or 404. A cap of 402 or 429 is not counted, because it may lift within seconds |
| 6 | Whether 55 days at Google is acceptable. It cannot be shortened on the Gemini API, and flagged text may be read by Google's staff. Google gives no period for what it flags | Decided on 24 September 2026: yes. The figure is what a tool read, and is shown to nobody |
| 7 | Whether real people's words may go to DeepSeek at all, and whether the code should refuse it on a release that is not synthetic | Decided on 24 September 2026: they may not. `choose` refuses it on every release, with `not_for_people`. The adapter is for the evaluation set |
| 8 | Special category data. A sentence can hold health or religion. OpenAI's agreement says no sensitive data is intended. Anthropic's lists "None". Google's is silent. DeepSeek asks that none be sent. Ask each provider in writing, ask each person for explicit consent, or both (ADR 0007) | Decided on 24 September 2026: neither. The notice says not to type anything private, and what a person shares of themselves is theirs to share (ADR 0023) |
| 9 | Whether processing outside the UK is acceptable. None of the four offers a UK region that processes | |
| 10 | Adults only. Google's terms forbid a product likely to be used by under-18s. Burro asks no age | |
| 11 | Which model, and what result is good enough: section 7 | The defaults of section 3 |
| 12 | Whether the service makes one call of its own as it starts, with a made-up sentence, so that the first person does not wait for a schema to compile. It is a call that is paid for, and a provider is then called when nobody has typed | It makes none |
| 13 | Whether the privacy notice may name OpenAI or DeepSeek. Both providers' terms restrict use of their names. UK law asks that recipients be named | The notice names every provider |
| 14 | A monthly spend cap on a project of Burro's own at each provider, and who is told when it is near | |
| 15 | The interpreter's name on the wire. `claude` becoming `model` is a change to the contract and to the clients | It says `model`. The version of the contract stays 2, because nothing was deployed when the name changed and every client is generated from the one file. Burro was first deployed on 25 September 2026. The iPhone app's models are not yet made again: section 8.1 |
| 16 | Renaming the report on Anthropic's documents, so that a coding agent does not load it as instructions | Done. It is `docs/research/models/anthropic.md` |
