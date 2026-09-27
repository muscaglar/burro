# 0023. What is typed goes to the provider as typed, and people are told so

Status: accepted, 2026-09-24. The founder decided it. It amends [0019](0019-no-one-provider-and-a-key-alone-turns-nothing-on.md), whose fourth condition it takes out, and [0005](0005-raw-prompts-are-never-stored.md). **Amended on 2026-09-26, once the founder had walked the website a second time**: people are told on the page that says how words are handled, which the foot of every page leads to, and no longer by the box where they type. What goes to a provider, and when one is used, are as they were. See "Amended, 2026-09-26", below, which says what that gives up.

**Amended the same day** by [0043](0043-burro-has-accounts-and-a-person-signs-in-by-a-link-sent-by-email.md), at the founder's asking: Burro builds accounts. It still follows nobody, and still keeps no store of what was typed. "Burro builds accounts", below, says what in this record it changes, which is one line.

## Context

[0019](0019-no-one-provider-and-a-key-alone-turns-nothing-on.md) held every provider back until a person had compared each sentence Burro tells people of it with the provider's own pages. Nobody had, so no provider could be turned on. A sanitiser was then proposed, to take what is private out of a sentence before it is sent.

The founder decided against both. The product is to stay simple: people use the model as it is, a person who breaks a provider's terms is warned and may be blocked afterwards, and what a person shares of themselves is theirs to share.

## Decision

| Matter | What is so |
|---|---|
| What goes to a provider | What a person typed, as they typed it. Nothing is taken out of it or put in its place. The search settings go with it only where the service is set to send them |
| When a provider is used | When it is named, its key is present, its terms are accepted by name, and the model is one its adapter was fitted to. DeepSeek never reads what people type, whatever is set |
| What people are told | By the box, before anything is typed: that what is typed is sent to a language model run by the named company, to be read, that nothing private should be typed, and that Burro itself keeps nothing of what is typed. With it goes a link to the company's own terms. *Since the evening of 2026-09-26 it is said on the page that says how words are handled, and not by the box* |
| What people are not told | Anything about the company as fact: not how long it keeps words, not whether it trains on them, not who may read them or where. Nobody has checked those, and the link serves in their place |
| With no provider | People are told that what they type is not sent to a language model |
| When a provider refuses a sentence | The rules read it as they would with no model, and the person is shown one line: that the language model would not read this, and that Burro's rules have. The call is on record as refused. Nothing of what was typed is written down, and nothing worked out from it |
| A client that abuses the service | It is blocked afterwards, by its address, at the host's edge. Burro builds no accounts, follows nobody, and keeps no store of what was typed. **Amended on 2026-09-26**: Burro builds accounts, for a person who asks for one ([0043](0043-burro-has-accounts-and-a-person-signs-in-by-a-link-sent-by-email.md)). It follows nobody and keeps no store of what was typed, as before. Nobody is asked to sign in before they search, and an account is not what blocks a client: that is still done afterwards, at the host's edge |
| A person's own information | It is theirs to share. Burro says not to, and does not stop them |

What was proposed and not built:

| Proposed | Why not |
|---|---|
| A check by a person of every sentence people are told of a provider | The founder decided against it. The notice now states nothing of a provider that a check would be needed for |
| A sanitiser or a classifier in front of the provider | The founder decided against it, as more than the product needs |

## Burro builds accounts

Amended on 2026-09-26. The founder asked for accounts: "We will also need to lay the ground work for a user login, account creation, security etc." [0043](0043-burro-has-accounts-and-a-person-signs-in-by-a-link-sent-by-email.md) is the decision, and accounts are off until they are turned on.

| This record said | What is so |
|---|---|
| "Burro builds no accounts, follows nobody, and keeps no store of what was typed" | Burro builds accounts, for a person who asks for one. It follows nobody, and keeps no store of what was typed: what an account keeps of a search is the spec, and never the words ([0044](0044-a-person-who-has-signed-in-may-keep-a-search-and-what-is-kept-is-the-spec-and-never-the-words.md)) |
| A client that abuses the service is blocked afterwards, at the host's edge | The same, of a search. An account blocks nobody, because a search asks for none, and knows nobody, signed in or not. What one client may ask of the routes of accounts is limited by the service, which counts the address the website gave it, under a keyed hash, in memory, and writes it nowhere |
| Under "What would change it": "Accounts. A person could then be asked, and answered for, by name" | Accounts are built, and nobody is asked by name. No sentence is tied to an account, the reader is handed nothing of who asked, and what people are told of who reads their words is the same whether or not they have signed in. To ask a person who has signed in before their words are sent would be a new decision |

Nothing else of this record is changed by accounts: what goes to a provider, when a provider is used, and what people are told.

## Consequences

- Something private that a person types reaches the provider. The notice is all that stands between, and it is advice.
- The table of what each provider's pages say stays in `providers/terms.py` as research. It is marked as unchecked, and is served to nobody.
- The contract changed. `reader` of route 11 lost `sources` and gained `terms_url`, route 1 gained `model_refused`, and a call may be on record as `refused`. Every client is generated again.
- The host of the API, as its pages were read, offers no block list by address. Until a host with one stands in front of the API, a client of the API cannot be blocked at an edge: `deploy/README.md`.
- Nothing typed is logged, as before ([0005](0005-raw-prompts-are-never-stored.md)). What is logged of a refusal is that the call was refused, in the line every call writes.

## Amended, 2026-09-26

The founder walked the website a second time, and wrote: "remove how your words are handeld from the home page search. this is overkill, also remove 'what you type is sent to burro….. language model' copy".

Under the box stood two lines, before anything was typed. The first was the website's own: that what is typed is sent to Burro to be read, and that Burro does not keep it. The second was the service's notice, as it was served: whose language model reads what is typed, that nothing private should be typed, or that what is typed is sent to no language model. Once a search was open the two gave way to a link beside the label of the box, "How your words are handled".

| Matter | What was decided | What stands now |
|---|---|---|
| What goes to a provider | What a person typed, as they typed it | The same |
| When a provider is used | When it is named, its key is present, its terms are accepted by name, and the model is one its adapter was fitted to. DeepSeek never reads what people type | The same |
| What people are told | The service's notice, with the link to the company's own terms | The same notice, as the service serves it. The website still writes no name of a provider and no terms of its own |
| Where they are told | By the box, before anything is typed | On the page of methods, under "How your words are handled", with what Burro itself does with what is typed. The foot of every page leads there, by the word a person looks for at the foot of a page: "Privacy". Whoever hears the page hears where it leads after the word: "Privacy: How your words are handled". The page says of the service's notice that it is what the service said when the page was built. Nothing by the box says it, before a search or after one |
| When they are told | Before they type, whether they looked for it or not | When they look for it |
| What the box waits on | The page asked the service who reads as it opened, and sent no sentence until the service had said. The line said so meanwhile, and said that nothing is sent where the service could not say | The page asks as it did, and sends no sentence until the service has said. Nothing by the box says that it is waiting, or why |

**What it gives up.** This record rests on one sentence of its consequences: "Something private that a person types reaches the provider. The notice is all that stands between, and it is advice." The advice is now a page away, behind a link at the foot of the page. A person who types their health or their workplace into the box has been told nothing, where they typed it, of who reads it. With a model turned on, as one was on the host on 2026-09-26, their words go to the company that runs it, and nothing where they typed has told them so.

**What holds it.**

| What | Holds it |
|---|---|
| Burro keeps nothing of what is typed, and writes none of it to a log | [0005](0005-raw-prompts-are-never-stored.md), [0011](0011-nothing-is-kept-for-a-search.md), and the tests of both. Nothing of it was changed |
| What is typed travels in the body of a request, and never in an address | The same |
| A key alone turns no model on | [0019](0019-no-one-provider-and-a-key-alone-turns-nothing-on.md). With no provider turned on, what is typed is read by Burro's own rules and leaves for no company that runs a model |
| What people are told is the service's own, and is of the provider that reads | The notice and the reader are made from one choice, as before. The website shows the notice as it was served |
| A person can find it from any page | The foot of every page leads to it: `test_the_foot_leads_to_how_a_persons_words_are_handled_by_a_name_a_person_looks_for_at_the_foot_of_a_page`. That it is named by the heading of the part it leads to is built too, and one line chooses: `WORDS_IN_THE_FOOT` in `apps/web/src/components/SiteHeader/look.ts` |

**What does not hold it.**

- **The page of methods is built ahead of time**, and built again each hour at most. The line under the box asked the service as the page opened, so that it was never older than the service's setting. What a person is now told is what the service said when the page was built. Once a provider is turned on, or another takes its place, the page says what was so before until it is built again: deploy the website in the same hour as the service.
- **No law was read for this amendment.** The launch checklist holds what the regulator asks of when a person is told: privacy information is to be given "at the time when personal data are obtained", and posting it on a website is not enough by itself ([the checklist](../legal/data-protection-checklist.md), task 6). What was built to meet that was the notice by the box. It is the founder's to weigh, with [the draft of the privacy notice](../legal/privacy-notice.md), which was brought to the change and marks each sentence that rested on the box.
- **What a provider's terms ask that people be told, and where, was not read.**

What was weighed, and put aside:

| Way | Why not |
|---|---|
| One short line under the box, which leads to the page | The founder asked for the words under the box to go, and named both |
| The notice shown by the box only where a model reads | It is the line the founder quoted |
| The notice shown once, the first time a person types | The website keeps nothing in a browser, so it cannot know a first time from a second |

## What would change it

- A provider that tells Burro its terms are being broken through it, and that a warning afterwards is not enough.
- Accounts. A person could then be asked, and answered for, by name. They were built on 2026-09-26. Nothing of who reads what is typed was changed with them: a person who has signed in is asked nothing more, and what they type goes as anybody's does. "Burro builds accounts", above, says so.
- A regulator's finding that advice beside the box is not enough for what people type. Since 2026-09-26: a regulator's finding, or a provider's, that a page the foot leads to is not enough.
- A model that is on while nothing by the box says so. One was turned on where Burro is hosted, on 2026-09-26. Whether it stays on is the founder's to say, and [the page on children](../legal/access-by-children.md), section 6, asks the same of it for another reason.
