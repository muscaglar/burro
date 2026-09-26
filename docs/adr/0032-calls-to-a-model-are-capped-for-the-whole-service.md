# 0032. Calls to a model are capped for the whole service, and nobody is told apart

Status: accepted, 2026-09-25. The founder asked for a limit before a model is turned on. That the cap is for the whole service follows [0023](0023-what-is-typed-goes-as-typed-and-people-are-told.md) and [0011](0011-nothing-is-kept-for-a-search.md). The two numbers are a first guess, and are the founder's to confirm.

## Context

- The API is on the open internet. Route 1 asks a model wherever the rules leave words unread, and every call to a model is paid for.
- The service had no limit of any kind. `admit` in `app.py` was the place kept for one, and was empty. So the model was off in the deployed service for one reason: a key there was an open bill.
- [0023](0023-what-is-typed-goes-as-typed-and-people-are-told.md) decided that Burro builds no accounts and follows nobody, and that a client that abuses the service is blocked afterwards, at the host's edge. [0011](0011-nothing-is-kept-for-a-search.md) and [0005](0005-raw-prompts-are-never-stored.md) decided that the server keeps nothing for a search, and that a log holds counts, latency and status.
- The plan and the contract say that a call that is refused is still answered, by the rules and the form. Never by a login wall, and never by a 5xx.

## Decision

| Matter | What is so |
|---|---|
| What is capped | Calls to a model, and nothing else |
| For whom | The whole service. No person is told apart from another: no address, header, cookie or token is read, hashed or kept. The counter is handed nothing of a call |
| How many | 30 in a minute and 2,000 in a day, unless it is set otherwise |
| The settings | `BURRO_MODEL_CALLS_PER_MINUTE` and `BURRO_MODEL_CALLS_PER_DAY`. Each is a whole number in digits, from nought to 600 and from nought to 100,000. Each has a default that always applies: there is no way to set no cap |
| Nought | The model is never called. The service is then as it is with no model set: the rules read, people are told that the rules read, and as it starts the service says `model_not_used` with the reason `capped_at_nought` |
| A value that is not in that form | Stops the service as it starts, with one line that does not repeat the value |
| A minute and a day | The minute and the day that are running, by the clock in UTC. A day turns at midnight in UTC. A clock that is put back brings no call back |
| When a call is counted | As it is about to be made, before the provider is reached. So a call that fails or times out is counted. A call that is turned away is not |
| Where the cap stands | In the reader, where a model is called: `cap.py`, and `ModelInterpreter.interpret` in `reader.py`. `admit` is left as it was |
| Over a cap | No call is made. The rules read the sentence, as they do where a provider says that it is capped: the answer is a 200 with `degraded` true, and the call is on record as `capped`. Never a 429 |
| What is written | One line, `model_capped`, the first time a cap is reached in its minute or in its day. It holds `reason`, which is `calls_per_minute` or `calls_per_day`. No count, no id, and nothing of any call |
| Where the counts are kept | In the memory of the process, behind a lock. They start again when the process does |

Why the cap is for the whole service, and not for each person:

| Way | Why not |
|---|---|
| A cap for each address | The service reads no address and logs none. To count by one is to keep it, or a hash of it that a guess confirms ([0011](0011-nothing-is-kept-for-a-search.md)). The host's edge holds the address already, and a limit by address belongs there ([0023](0023-what-is-typed-goes-as-typed-and-people-are-told.md)) |
| A cap for each browser, by a cookie or a token | The website sets no cookie and stores nothing. A token that tells one person from another is an account by another name |
| A cap for each account | There are no accounts |
| The provider's cap on spending, alone | It does bound the bill, and it stays as the outer guard. It is set by hand at the provider, and once it is reached every call is refused until a person lifts it. The cap here turns with the minute and the day, is in code, and is held by a test |
| To answer 429 over the cap | One heavy caller would then break the box for everyone. The rules and the form still answer |
| To count in `admit` | `admit` runs before anything is read, on every route. A sentence that the rules apply by themselves makes no call, and only the reader knows which those are. Counted in `admit`, the cap would turn away people whose words cost nothing |

## What it does not do

- **One heavy caller can use up the day's calls for everyone.** After that everyone is read by the rules until the day turns.
- **Nothing limits calls that do not reach a model**: a ranking, a comparison, a share, the form, or a sentence the rules apply by themselves.
- **There is no check for a bot.**
- It does not bound what one call costs. `BURRO_MODEL_MAX_TOKENS` and the 600 characters a person may type do.
- It does not outlive the process. A deploy or a restart starts the minute and the day again, so a day with a restart in it can hold more than a day's calls.
- It does not count what the evaluation set sends. `providers/measure.py` makes a reader with no cap, for made-up sentences that a person chose to send.
- It is not what stands against abuse. That is the host's own protections and blocking after the fact ([0023](0023-what-is-typed-goes-as-typed-and-people-are-told.md)). The provider's own cap on spending is the outer guard.
- **It does not say who may reach the model.** The address of the service is public. An address a host gives an app can be found by anyone: a certificate for it is written to public logs the day it is issued. That nobody was given the address keeps nobody out. With a model on, whatever anyone sends to the reader is sent on to the provider, whether they came by the website, which tells them so before they type, or called the service themselves, which does not. The cap bounds what that costs, and nothing of who is heard.

## Consequences

- One of the conditions for setting a key is met: the service has a limit. The others stand as they were: the privacy notice, the registration with the regulator, the provider's agreement, and a measurement of the provider on the evaluation set ([the deploy guide](../../deploy/README.md#turning-the-model-on)).
- A day at the cap is 2,000 calls. Each sends the instructions, the schema and what was typed, some 28,000 characters in all, and may be answered with as many tokens as `BURRO_MODEL_MAX_TOKENS` allows, which is 2,048 unless it is set. What that costs is the provider's to say, on its own page of prices.
- A call is counted though nothing is sent, where an adapter is leaving its provider alone after three refusals in a row. The cap is then reached sooner than the bill would have it.
- `model_not_used` has one more reason, and `reason` is written in one more line. Neither holds anything that was set.
- Whatever a model's path raises is caught where the model is asked, whatever its kind, and the rules answer. It reaches neither the handler at the edge nor the server's own.

## What would change it

- Accounts. A cap for each account could then stand in `admit`, beside this one.
- A second machine. The counts would have to be shared, or each machine given a part of the cap.
- A host with a firewall in front of the API, which could limit by address. It would see what people type, so it needs a decision of its own first.
- A day's calls used up by one caller, more than once.
- A measurement of what a call costs, which the first real call will give.
