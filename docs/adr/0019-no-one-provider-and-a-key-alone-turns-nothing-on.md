# 0019. No one provider of a model, and a key alone turns nothing on

Status: accepted, 2026-09-24. The founder decided the three things in its title and that Gemini comes first. It amends [0005](0005-raw-prompts-are-never-stored.md), which said what one provider keeps. Amended the same day: the founder accepted what Google keeps, ruled DeepSeek out for what real people type, and settled what a model may apply. Amended again the same day by [0023](0023-what-is-typed-goes-as-typed-and-people-are-told.md): nothing waits on a person's check, DeepSeek never reads what people type, and what a provider's pages say is served to nobody. Three points are left to confirm, and are listed at the end.

## Context

A model may read what a person types into edits. The rules hold its answer to the person's own words before anything is applied ([0002](0002-deterministic-core.md), [0012](0012-a-closed-vocabulary-and-a-guard-on-the-model.md)).

The service could ask one provider, through that provider's own library. It asked as soon as that provider's key was in its environment. Nobody had accepted the provider's terms, and nothing told people that their words went anywhere. The website said in its own words that a provider keeps words "for up to 30 days, or longer if it is flagged". That is what two of the four providers say. One says 55 days, and one gives no period.

What a person types can hold their workplace, their health or their religion. Who receives it, what goes with it, and what becomes of it there are the first things a person is owed, and they differ by provider.

## Decision

**No one provider.** Four adapters stand behind one interface: Gemini, OpenAI, DeepSeek and Claude. Each makes one HTTPS call with the standard library. The service depends on no provider's library. Gemini comes first, which means it is the first to be measured. No provider is a default in code.

**A key alone turns nothing on.** A model reads what is typed only when all of these hold. They are looked at in this order, once, as the service starts.

| # | What must hold | Set by |
|---|---|---|
| 1 | A provider is named | `BURRO_MODEL_PROVIDER` |
| 2 | That provider's key is present | The one variable the provider's entry names |
| 3 | Its terms are accepted, by naming the provider | `BURRO_MODEL_TERMS_ACCEPTED` |
| 4 | The model is one the adapter was fitted to | `BURRO_MODEL_ID`, or the provider's entry |
| 5 | The provider is one that may read what real people type. DeepSeek is not | Code |

Until [0023](0023-what-is-typed-goes-as-typed-and-people-are-told.md) the fourth was that a person had checked every sentence people are told of the provider against its source.

With any of them missing the rules read, and every route works. The service says so in one warning as it starts: `model_not_used`, with the provider and the first thing that does not hold. Both are fixed words. Nothing that was set is ever logged, because a value in the wrong variable could be a key. With nothing set, nothing is said.

**The words go alone unless the service is set otherwise.** `BURRO_MODEL_SENDS_SETTINGS` sends the search settings with the words, and only the one word `yes` turns it on. Where a journey leads is never sent. What is kept of a model's answer does not depend on what was sent.

**What people are told comes from the API.** `providers/terms.py` holds, for each provider, the answer to eight questions, in one form of words: who receives what is typed, whether it is used to train, how long it is kept, whether longer by law or on suspicion of misuse, who may read it, where it is handled and where it is stored. Each answer names the provider's own pages and the day they were read. Since [0023](0023-what-is-typed-goes-as-typed-and-people-are-told.md) those answers are research, and none is served: the notice names the company, states nothing of what it does, and goes with a link to the company's own terms.

Route 11 serves it as `reader`: the whole notice, whether the settings are sent, and the address of the company's own terms. Where no model reads it says that nothing typed is sent to a language model. The reader and the notice are made from one choice, so the service cannot send to one provider and tell people of another, or of none.

**A client writes no provider's name and no terms.** The website shows the notice by the box before anything is typed, as it was served, and sends no sentence until the service has said who reads it. A test reads the website's source for the name of any provider and for any period of keeping.

**The answer of route 1 says `rule` or `model`.** It named one provider. Which provider's model is said by route 11.

What was not taken:

| Way | Why not |
|---|---|
| A default provider in code | Whoever sets a key would send people's words to it without choosing to |
| Turn a provider on by its key | It is what went before. A key in an environment is no decision to send people's words anywhere |
| One notice in the website's own words | It can be true of one provider at most. It was true of two of four |
| A provider's own library | Each is a dependency that can log, retry and keep what it is sent. One HTTPS call can be read in full |
| Who reads, in a route of its own | Route 11 is what a form is built from, and a client already reads it. Its tag now names what is told, so an answer that tells of another reader is never kept |

## Consequences

- Nobody has checked a sentence of `terms.py`, for any of the four. Since [0023](0023-what-is-typed-goes-as-typed-and-people-are-told.md) that holds no provider back, and no sentence of it is shown to anyone.
- A page built ahead of time may be older than the service's setting. So the website asks the service who reads as the page opens, and shows nothing of what it was built on in its place. If the service cannot say, no sentence is sent.
- The methods page is built ahead of time, and says that it says what the service said when it was built. Build the website again when the provider changes.
- A provider can be measured on the evaluation set before it is turned on, because every sentence there is made up. Measuring asks nothing of the terms.
- The iPhone app's models are generated from the contract, and its copy still states one provider's terms. It needs the changes `docs/design/models.md` lists before it is shown to anyone.
- Rows of the call record gain `provider`, from a closed list.

## Decided later the same day

| Question | Decided | What it changes |
|---|---|---|
| Google keeps what is typed for 55 days. The period cannot be shortened on this API, its staff may read what it flags, and it gives no period for what it flags. Is that acceptable | Yes | Nothing in code. Gemini still comes first. The notice by the box says each of these, from `providers/terms.py`, and says that Google gives no period for what it flags |
| May what real people type go to DeepSeek | No | DeepSeek is for made-up sentences only: the evaluation set, and a service that runs on the synthetic release. Point 5 below is closed |
| What a model may apply of what it reads | Nothing by itself. The model proposes, the person confirms, and code checks | Point 3 below is closed. The rule belongs to the record on the reader, [0012](0012-a-closed-vocabulary-and-a-guard-on-the-model.md) |

What keeps DeepSeek from real people's words, as the code stands:

| What | Holds it |
|---|---|
| A provider is used only when it is named, its key is set, its terms are accepted by name and a person has checked its entry | Code and test. Nobody has checked the entry for DeepSeek, and the decision is that nobody will accept its terms for a service that real people use |
| `choose` refuses DeepSeek on a release that is not made up | Not built. `choose` holds all four alike and knows nothing of the release. Until it is built the decision is kept by whoever runs the service, and no test would fail if it were broken |

The privacy notice says that DeepSeek is never used for what real people type, and marks the sentence as one that a setting holds and code does not ([docs/legal/privacy-notice.md](../legal/privacy-notice.md), section 4).

## To confirm

| # | Point | What is built until it is settled |
|---|---|---|
| 1 | Whether a provider is held until a person has checked what people are told of it, or until its terms are accepted alone | Settled by [0023](0023-what-is-typed-goes-as-typed-and-people-are-told.md): until its terms are accepted alone |
| 2 | Whether the search settings go to the model with the words | They do not. One run of the evaluation set each way settles what it costs |
| 3 | What a model may apply in a prompt that is not plain. Two cases of the evaluation set come through the guard against what the case says | **Decided, 2026-09-24:** nothing by itself. See above |
| 4 | Whether the version of the contract moves when a name on the wire changes | It stays 2. Nothing was deployed when the name changed, and every client is generated from the one file. Burro was first deployed on 2026-09-25 |
| 5 | Whether real people's words may go to a provider that publishes no period of keeping and no agreement on processing | Settled: they may not. `choose` refuses DeepSeek, with `not_for_people` |

## What would change it

- A provider that offers a region in the United Kingdom, or keeps nothing. It would come first.
- A reader that runs where the service runs. Nothing would leave, and the notice would say so.
- Accounts. A person could then choose whether a model reads their words, and the choice would be theirs and not the service's.
