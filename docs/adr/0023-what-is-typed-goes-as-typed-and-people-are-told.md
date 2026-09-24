# 0023. What is typed goes to the provider as typed, and people are told so

Status: accepted, 2026-09-24. The founder decided it. It amends [0019](0019-no-one-provider-and-a-key-alone-turns-nothing-on.md), whose fourth condition it takes out, and [0005](0005-raw-prompts-are-never-stored.md).

## Context

[0019](0019-no-one-provider-and-a-key-alone-turns-nothing-on.md) held every provider back until a person had compared each sentence Burro tells people of it with the provider's own pages. Nobody had, so no provider could be turned on. A sanitiser was then proposed, to take what is private out of a sentence before it is sent.

The founder decided against both. The product is to stay simple: people use the model as it is, a person who breaks a provider's terms is warned and may be blocked afterwards, and what a person shares of themselves is theirs to share.

## Decision

| Matter | What is so |
|---|---|
| What goes to a provider | What a person typed, as they typed it. Nothing is taken out of it or put in its place. The search settings go with it only where the service is set to send them |
| When a provider is used | When it is named, its key is present, its terms are accepted by name, and the model is one its adapter was fitted to. DeepSeek never reads what people type, whatever is set |
| What people are told | By the box, before anything is typed: that what is typed is sent to a language model run by the named company, to be read, that nothing private should be typed, and that Burro itself keeps nothing of what is typed. With it goes a link to the company's own terms |
| What people are not told | Anything about the company as fact: not how long it keeps words, not whether it trains on them, not who may read them or where. Nobody has checked those, and the link serves in their place |
| With no provider | People are told that what they type is not sent to a language model |
| When a provider refuses a sentence | The rules read it as they would with no model, and the person is shown one line: that the language model would not read this, and that Burro's rules have. The call is on record as refused. Nothing of what was typed is written down, and nothing worked out from it |
| A client that abuses the service | It is blocked afterwards, by its address, at the host's edge. Burro builds no accounts, follows nobody, and keeps no store of what was typed |
| A person's own information | It is theirs to share. Burro says not to, and does not stop them |

What was proposed and not built:

| Proposed | Why not |
|---|---|
| A check by a person of every sentence people are told of a provider | The founder decided against it. The notice now states nothing of a provider that a check would be needed for |
| A sanitiser or a classifier in front of the provider | The founder decided against it, as more than the product needs |

## Consequences

- Something private that a person types reaches the provider. The notice is all that stands between, and it is advice.
- The table of what each provider's pages say stays in `providers/terms.py` as research. It is marked as unchecked, and is served to nobody.
- The contract changed. `reader` of route 11 lost `sources` and gained `terms_url`, route 1 gained `model_refused`, and a call may be on record as `refused`. Every client is generated again.
- The host of the API, as its pages were read, offers no block list by address. Until a host with one stands in front of the API, a client of the API cannot be blocked at an edge: `deploy/README.md`.
- Nothing typed is logged, as before ([0005](0005-raw-prompts-are-never-stored.md)). What is logged of a refusal is that the call was refused, in the line every call writes.

## What would change it

- A provider that tells Burro its terms are being broken through it, and that a warning afterwards is not enough.
- Accounts. A person could then be asked, and answered for, by name.
- A regulator's finding that advice beside the box is not enough for what people type.
