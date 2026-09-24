# Models: four providers behind one interface

Burro reads a sentence into typed edits by rules, or by a model whose answer is then held to the rules (ADR 0002, ADR 0012). This document is about the model: which providers Burro can ask, how it asks, what people are told, and what is left to do.

| | |
|---|---|
| Status, 23 September 2026 | Built and tested as new files. **Not wired into the service.** No adapter has met a live provider |
| Providers | Google Gemini, OpenAI, DeepSeek, Anthropic Claude |
| Which can be turned on today | None. Each is held until a person has checked what people are told of it. See section 6 |
| Code | `services/api/src/burro_api/providers/` |
| Tests | `services/api/tests/providers/`. Run `uv run --no-sync pytest services/api/tests/providers -q` |
| Evidence | `docs/research/models/`: one report a provider, and `definitions.md`, two later looks at the same pages |

**Today `ANTHROPIC_API_KEY` alone turns the model on. Do not set it on a host that serves people until step 5 of section 8 is done.** The service as it stands does not ask `choose`. It reads one variable, and sends what people type to one provider as soon as that variable holds a key. No terms are accepted, no notice is served, and the website shows none. A key of any other provider does nothing today. Everything below describes `choose`, which decides nothing until it is wired in.

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
| `ModelTimeout`, `ModelCapped`, `ModelError` | The three failures. None has a message, a cause or a context |

| File | What it holds |
|---|---|
| `interface.py` | The protocol, the reply and the failures. The same as in `claude.py`, until step 1 of section 8 makes them one |
| `base.py` | `over_https`, the one function that sends, and `Adapter`, what the four share |
| `gemini.py`, `openai.py`, `deepseek.py`, `anthropic.py` | One adapter each: what to send, how to read the answer, and the models it was fitted to |
| `terms.py` | What people are told, by provider: the questions, the forms of words, and the source of every answer |
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
| The answer | Must be finished, by the provider's own word for it, and must be a JSON object. `claude._parsed` then holds it to the schema |
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
| 200 that is a refusal, is cut short, is not JSON, or lacks a count of tokens | error | A number that is not known is never nought |

## 2. Settings

Read once, when the service starts. In `choose`, a key alone turns nothing on.

**Today `ANTHROPIC_API_KEY` alone turns the model on. Do not set it on a host that serves people until step 5 of section 8 is done.** The service does not yet ask `choose`.

| Variable | Meaning | Default |
|---|---|---|
| `BURRO_MODEL_PROVIDER` | `gemini`, `openai`, `deepseek` or `anthropic` | None. There is no default in code |
| `GEMINI_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY` | The key of the provider that is named | None |
| `BURRO_MODEL_TERMS_ACCEPTED` | The same provider's name. It says that whoever runs the service has read its terms and taken them on | None |
| `BURRO_MODEL_ID` | The model | The provider's entry in `terms.py` |
| `BURRO_MODEL_TIMEOUT_S`, `BURRO_MODEL_MAX_TOKENS` | As today | 6 seconds, 2,048 tokens |

A model reads what is typed only when all five hold. They are looked at in this order, and the first that fails is the reason.

| # | What must hold | If not |
|---|---|---|
| 1 | The provider is one of the four | `no_provider`, `unknown_provider` |
| 2 | Its key is present and fit for a header | `no_key`, `unfit_key` |
| 3 | The terms are accepted for that provider | `terms_not_accepted` |
| 4 | A person has checked every sentence of its entry in `terms.py` against its source | `terms_not_checked` |
| 5 | The model is one the adapter was fitted to | `unfit_model` |

Otherwise the rules read, and one line is logged that holds the provider's name and nothing else: `model_not_used_gemini`. With nothing set, nothing is logged. Nothing that was set is ever logged, because a value in the wrong variable could be a key.

The line does not say why. The reason is a fixed word, and this prints it and nothing else:

```sh
uv run python -c "import os; from burro_api.providers.choose import choose; print(choose(os.environ, warn=lambda *_: None).refusal)"
```

These three are what whoever runs the service sets for Gemini. As `terms.py` stands they turn nothing on: the answer is `terms_not_checked`, for Gemini as for the other three.

```sh
BURRO_MODEL_PROVIDER=gemini  BURRO_MODEL_TERMS_ACCEPTED=gemini  BURRO_MODEL_ID=gemini-3.5-flash-lite
```

## 3. The four, side by side

Costs are for 1,000 searches of 3,000 tokens in and 300 out, not cached, in US dollars. Token counts are estimates until measured. What people are told of each is in section 6, question by question.

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

1. Step 5 of section 8 is done, so that `choose` decides.
2. A person opens each address in Gemini's entry in `terms.py`, compares each of its eight sentences with the page, puts right what differs, and writes their name and the day in `checked_by` and `checked_on`. Until then `choose` holds it back. The same is asked of the other three.
3. Billing is on for the key's project. Google's terms allow no free tier for people in the UK.
4. ADR 0005 is amended: "up to 30 days" is not true of Gemini.
5. The first live call is made with a made-up sentence, and the questions of section 9 are answered.
6. Section 7 is run on Gemini and on one other.

## 5. Handing over a key

**Today `ANTHROPIC_API_KEY` alone turns the model on. Do not put any key in the environment of a host that serves people until step 5 of section 8 is done.** Until then a key belongs on your own machine, for the measuring of section 7, and nowhere else.

The key is never typed into a chat, a file in the repository, or a command line that is recorded.

| Step | How |
|---|---|
| Make it | In the provider's console, in a project or workspace made for Burro alone, with a monthly cap on spending |
| For a run on your own machine | `read -rs GEMINI_API_KEY && export GEMINI_API_KEY`, then paste. The shell shows nothing and records nothing. Close the shell after |
| For the service, once step 5 is done | Put it in the host's store of secrets, through the host's web page, or through a command that reads the value from standard input. Never as `NAME=value` on a command line |
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

`choose(env).told` holds it: whether a model reads what is typed, the provider, the company, the notice, and for each sentence the question it answers, whether the provider's documents answer it, where it was read and when, and the day a person checked it. The website and the app show what the API serves and write none of it themselves.

### What is sent

The reader sends the words and the search as it stands. The search holds the budget in pounds, whether to rent or buy, each journey's time and mode, every weight and tag, and every area that is ruled in or out, by its id. The one thing taken out is where a journey leads. On real data an area's id names a real neighbourhood. So every notice says, in the same words:

> With it go your search settings: your budget, whether you rent or buy, how long you will travel, what matters to you, and the areas you have ruled in or out.

`SENT_WITH` in `terms.py` names each field of a search and the words that tell of it. A test sends a whole search through the real reader and fails if a field leaves that the notice does not name.

### The questions, and the one form of words for each

Eight questions are put to every provider, in this order. Each has one sentence for an answer and one for the lack of one. A provider's name and its answer are all that change.

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

The notice for Gemini, as `terms.py` makes it:

> When you type a sentence, Burro sends it to Google (Google LLC, United States). With it go your search settings: your budget, whether you rent or buy, how long you will travel, what matters to you, and the areas you have ruled in or out. Google says it does not use them to train its models. It keeps them for 55 days. It may keep them for as long as the law requires. It does not say whether it keeps them for longer if it suspects misuse. They may be read by its staff, if it suspects misuse. They may be handled in any country where Google or its agents have facilities. They are stored in any country where Google or its agents have facilities. Leave out your health, your religion and anything else you would not want kept.

With no model: "What you type is read by rules that are part of Burro. It is not sent to a language model."

### What whoever checks a sentence should know

Each answer in `terms.py` holds the provider's own words, the address, the day, how the page was reached, and a note where there is one. How a page was reached decides nothing: all four are held to a person's own look.

| Provider | Point |
|---|---|
| All four | "Does not say" is a statement too. It means the pages at the addresses given were read and held no answer. Another page of the provider's may hold one |
| Gemini | Every page came back through a reader that extracts. "It may", for the law, rests on the agreement on data processing and not on the page about the 55 days. The words on where it is stored are of data "stored transiently or cached". The Gemini API's own terms, as read, name no company |
| OpenAI | `openai.com` was read once on the day, and not again. Who receives the words, and who may read them, rest on that reading alone. No page read names the countries where a call is handled |
| DeepSeek | Every page came back through an extraction. The privacy policy says it does not cover people who use a product built on the API, and the terms for the API say nothing of keeping, reading or place. The terms name a switch to refuse training. No page says whether it reaches the API |
| Claude | The page on how long text is kept lists the law and the Usage Policy among its exceptions. Another page says text "is not retained by default", and points to this one. No page read says who may read what was sent |

## 7. Measuring a provider before it is turned on

The set is `evals/reader`: made-up sentences, so nothing private is sent. `measure.py` makes the reader from the provider's name and its key, and asks nothing of the terms. It takes only a model the adapter was fitted to. It needs no change to any file.

```sh
read -rs GEMINI_API_KEY && export GEMINI_API_KEY
BURRO_MODEL_PROVIDER=gemini BURRO_MODEL_TIMEOUT_S=30 uv run python evals/reader/score.py \
  --reader burro_api.providers.measure:reader --workers 4 --save evals/reader/baseline/gemini.json
```

Run it three times. A model does not answer the same way twice. One run of 655 cases costs about $1.25 on Gemini.

| Measure | Good enough | Why |
|---|---|---|
| Reversed | None, in each of three runs | One reversed case fails a run (`evals/README.md`) |
| Unasked | No more than the rules' ceiling in `floor.json` | The model is held to the rules, so it should invent no more than they do |
| Read correctly | More than the rules read on the same day, in each of three runs | If it reads no more, it buys nothing and costs a person's privacy |
| Failed | Under 2 in 100, at the service's own 6 seconds | Each failure is a wait and then the rules |
| Cost | The tokens the scorer prints, priced from section 3, within half as much again of the estimate | To catch thinking that was not turned off |
| The first call | The schema is accepted. Tokens out are hundreds, not thousands | Neither can be known from a page |

These are proposed. The founder sets the floor, in `floor.json`, after the first run.

## 8. What the wiring step changes, in order

Nothing below has been done. Each is a change to a file that exists.

**Do step 5 before any key reaches the environment of a host that serves people.** Until it is done, `ANTHROPIC_API_KEY` alone turns the model on, with no terms accepted and no notice served. Steps 1 to 4 make step 5 possible. A test in `tests/providers/test_design.py` fails on the day step 5 is done, to say that the warnings in this document can go.

| # | File | Change |
|---|---|---|
| 1 | `services/api/src/burro_api/claude.py` | Delete its `ModelFailure`, `ModelTimeout`, `ModelCapped`, `ModelError`, `ModelReply` and `ModelClient`. Import them from `providers/interface.py`. Take the expected-failure mark off `tests/providers/test_interface.py`. Until this is done the route counts an adapter's timeout or cap as an error |
| 2 | `services/api/src/burro_api/logs.py` | Add `provider` and `reason` to `LOGGABLE`, and a way to write a warning. Then `choose._warn` writes `model_not_used` with `provider` and with `reason`, which is the refusal's fixed word, and the four event names go. `reason` is for the founder to confirm: section 10 |
| 3 | `services/api/src/burro_api/settings.py` | Drop `DEFAULT_MODEL_ID`, `KEY_VARIABLE` and `model_key_present`. The model and the key are `choose`'s. The alias `claude-haiku-4-5` is not a model any adapter takes |
| 4 | `services/api/src/burro_api/deps.py` | `Deps` gains `told`, with **no default**. A default would be "not sent to a language model", said of a service that sends. Whoever makes a `Deps` takes `told` from the same `Choice` as the interpreter, and a `Choice` cannot be made with the two at odds |
| 5 | `services/api/src/burro_api/app.py`, `cli.py`, `tests/test_app.py` | `_interpreter` calls `choose(os.environ)` and builds the interpreter from `choice.client` and `choice.model`. `deps_from` passes `choice.told`. The line `starting` names the provider. The test that a key alone selects the model is turned round. Take the expected-failure mark off `tests/providers/test_design.py`, and the three warnings out of this document |
| 6 | `services/api/src/burro_api/wire.py`, `routes/meta.py` | `MetaData` gains `reader`: `model_reads`, `provider`, `company`, `notice`, `sources`. A source holds `question`, `says`, `answered`, `addresses`, `read_on` and `checked_on`. Then `make openapi` and `make web-types` |
| 7 | `services/api/src/burro_api/calls.py`, `routes/interpret.py` | `CallRecord` and the `interpret` line gain `provider`, from the closed list. When `client.resting` turns true, one line is written with `provider` and nothing of the call |
| 8 | `services/api/src/burro_api/claude_sdk.py`, `tests/test_claude_sdk.py` | Delete both. `tests/conftest.py` no longer names the SDK's logger |
| 9 | `services/api/pyproject.toml` | Remove `anthropic>=1,<2`. One line in the pull request: a dependency is dropped, none is added |
| 10 | `claude.py`, `tests/test_claude.py`, `tests/test_claude_kept.py` | Rename to `reader.py`, `test_reader.py`, `test_reader_kept.py`. `ClaudeInterpreter` becomes `ModelInterpreter`. What imports them follows: the routes, `tests/support.py`, `providers/measure.py` |
| 11 | `packages/core` `ids.InterpreterName`, `calls.Caller` | `claude` becomes `model`. This is on the wire, so the contract, `contracts/openapi.json` and the website's types change with it |
| 12 | `evals/reader/model_reader.py`, `score.py`, `floor.json`, `evals/README.md` | `model_reader.build` becomes `providers.measure.reader`. `--reader claude` becomes `--reader model`. One floor a provider |
| 13 | `apps/web`, and `apps/ios` when it exists | Show `meta.reader.notice` by the text box, before anything is typed. No provider's name or terms in the client's own source. A test says so |
| 14 | `docs/design/contract.md` | Sections 8.2, 9.4, 10.1, 10.2 and 11: the chooser, the meta route, the new log fields, `provider` on the call record |
| 15 | `AGENTS.md`, `services/api/AGENTS.md`, `README.md`, `docs/PLAN.md` | Where they say Claude, a key that selects the model, or an SDK. The rule "only `claude_sdk.py` imports the SDK" becomes "nothing imports a provider's library", with its test |
| 16 | `docs/adr/0005` | Amend: what a provider keeps is in `providers/terms.py`, by provider. It is not "up to 30 days" for all, and it is not only the words that leave |
| 17 | `docs/adr/`, the next free number | A new record: no one provider; no SDK; a key alone turns nothing on; every provider held until a person has checked what people are told of it; what is served to people |
| 18 | `docs/research/models/claude.md` | Rename to `anthropic.md`. Its name differs only by case from the name of an instructions file for coding agents, so a tool that ignores case may load it as instructions |
| 19 | The privacy notice and the impact assessment, in `docs/legal/` | Name the provider, the countries and the periods, from `terms.py`, and what is sent with the words. Where they say a provider is held back because its terms were read through an extraction, say that all four are held until a person has checked them |

After step 5, run the verify skill: drive route 1 with a made-up sentence and no key, then with a key and nothing else, then with a key and no accepted terms, and see the rules answer all three times.

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
| 15 | DeepSeek | The schema is not enforced. Of 655 made-up sentences, how many answers fail it? | Above 2 in 100, build the strict route or choose another |
| 16 | DeepSeek | Which model does the answer's own `model` field name when `deepseek-v4-pro` is asked for, and at what price? Two pages disagree | Take `deepseek-v4-pro` off the list |
| 17 | DeepSeek | Under load, do the empty lines arrive before the status line or after it? | Nothing to change. Both are read, within the one deadline |
| 18 | Claude | Does `claude-haiku-4-5-20251001` take `thinking` as `disabled` together with `output_config.format`? The table of what each model rejects says it does | A 400. Leave the field out for that model: its thinking is off unless asked for |
| 19 | Claude | What does a retired model answer, status and `error.type`? The documents say only that it "will fail" | Nothing to change. After three such answers the adapter rests. The smallest model may be given notice from 15 October 2026 |
| 20 | Claude | Does the message of a limit the customer set still begin "You have reached your specified"? | It is counted as an error and not as a cap, and after three the adapter rests |

## 10. For the founder to decide

| # | Decision | What is built until you say otherwise |
|---|---|---|
| 1 | **What lets a provider be turned on.** Before, two providers could be turned on and two could not, Gemini among the two that could not. The difference was in how each provider's pages had been read, not in what the pages say. A second reading found the sentences of all four, but for two of OpenAI's, whose pages were not read a second time | All four are held alike, until a person has compared each of a provider's eight sentences with its page and written their name and the day. For one provider that is under an hour |
| 2 | Whether the reason a model is not used may be logged beside the provider's name. It is a fixed word such as `no_key`, and never a thing that was set. It was decided that the line holds the provider's name and nothing else | The line holds the name alone. The reason is returned, and section 2 shows how to print it |
| 3 | Whether the search settings should go to the model at all, or only the part it needs. It needs the position and mode of each journey to read "make the second one shorter". It may not need the budget's amount or the ids of the areas. The change is to `_user` in `claude.py`, and what is left out comes out of `SENT_WITH` and of the notice in the same change | All of them go, but for where a journey leads. The notice says so |
| 4 | Whether `SSL_CERT_FILE` and `SSL_CERT_DIR` are honoured. They are how a host names its certificates. They also let whoever sets them choose whose certificates are trusted | Honoured. `SSLKEYLOGFILE` is not |
| 5 | How long to leave a provider alone after it refuses, and after how many refusals. And whether a cap should count: while a monthly limit is reached, every sentence is still sent and refused | 300 seconds, after 3 in a row of 400, 401, 403 or 404. A cap of 402 or 429 is not counted, because it may lift within seconds |
| 6 | Whether 55 days at Google is acceptable. It cannot be shortened on the Gemini API, and flagged text may be read by Google's staff. Google gives no period for what it flags | |
| 7 | Whether real people's words may go to DeepSeek at all, and whether the code should refuse it on a release that is not synthetic | The adapter is built. Nothing in code refuses it |
| 8 | Special category data. A sentence can hold health or religion. OpenAI's agreement says no sensitive data is intended. Anthropic's lists "None". Google's is silent. DeepSeek asks that none be sent. Ask each provider in writing, ask each person for explicit consent, or both (ADR 0007) | The notice advises people to leave it out |
| 9 | Whether processing outside the UK is acceptable. None of the four offers a UK region that processes | |
| 10 | Adults only. Google's terms forbid a product likely to be used by under-18s. Burro asks no age | |
| 11 | Which model, and what result is good enough: section 7 | The defaults of section 3 |
| 12 | Whether the service makes one call of its own as it starts, with a made-up sentence, so that the first person does not wait for a schema to compile. It is a call that is paid for, and a provider is then called when nobody has typed | It makes none |
| 13 | Whether the privacy notice may name OpenAI or DeepSeek. Both providers' terms restrict use of their names. UK law asks that recipients be named | The notice names every provider |
| 14 | A monthly spend cap on a project of Burro's own at each provider, and who is told when it is near | |
| 15 | The interpreter's name on the wire. `claude` becoming `model` is a change to the contract and to the clients | |
| 16 | Renaming `docs/research/models/claude.md` to `anthropic.md`, so that a coding agent does not load it as instructions | |
