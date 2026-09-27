# Privacy notice

**Draft. Not published. Not legal advice.** Written on 23 September 2026 from the public guidance of the Information Commissioner's Office (ICO) and from the code in this repository, and brought up to 24 September 2026. **Brought to the website again on 26 September 2026**, in two things alone: the website no longer says beside the box what becomes of what a person types, and it applies what it read of a sentence without asking. "What changed on 26 September 2026", below, says what the draft said of each and what it says now. No conclusion of this draft was changed for either: each is the founder's to draw. **It is behind the code in four things that are built since it was read against it**, of the providers, of the census and of recorded crime, and no mark of it was changed for them: [README.md](README.md#what-the-drafts-are-behind-in-as-the-code-was-read-on-27-september-2026) lists each. Nobody qualified has read it. [README.md](README.md) says how it was written, what was put right on the second day, and which sentences carry the most risk.

**Brought up to 26 September 2026 for accounts.** The founder asked for them that day. They are built, and they are off until they are turned on, which waits on this notice among other things ([ADR 0043](../adr/0043-burro-has-accounts-and-a-person-signs-in-by-a-link-sent-by-email.md)). Section 20 is new and says what an account keeps. Every sentence elsewhere that accounts make untrue says so where it stands. [README.md](README.md), under "What accounts changed", lists each.

It covers the website. An iPhone app is built and has not been released. This notice does not cover it.

## How to read this draft

| Mark | Meaning |
|---|---|
| `[FOUNDER: ...]` | A blank only the founder can fill |
| `[FOUNDER NAME]`, `[FOUNDER CONTACT]`, `[COMPANY NAME]`, `[COMPANY NUMBER]` | The name and the contact. Fill them when the page is published, never in this repository: it is public |
| `[NOT BUILT: ...]` | The sentence is not true of the code yet. It must not be published until it is |
| `[SETTING: ...]` | The sentence is true only while a setting holds, at a host, at a provider or in the service. The code does not hold it. The table below lists them |
| `[SOLICITOR]` | This draft's reading of the law decides what the sentence says. A qualified reading could change it |
| Read | Read at the publisher's own address, for this draft, on 23 September 2026 unless the sentence gives another day |
| Read twice | Read twice at the publisher's address, asked in different words each time. What is kept is what both readings gave |
| Not read | An inference, or the page did not say, or the page was not read |

Every page was read through a reader that extracts of the page, not the page itself. A quoted sentence may differ from the source by a word. Check the wording at the address given before this is published.

## What changed on 26 September 2026

The founder walked the website a second time, and wrote: "remove how your words are handeld from the home page search. this is overkill, also remove 'what you type is sent to burro….. language model' copy". And: "When running a search, don't ask the user to add anything, assume they want it to be added and just present the results." The website was rebuilt to both ([ADR 0023](../adr/0023-what-is-typed-goes-as-typed-and-people-are-told.md) and [ADR 0012](../adr/0012-a-closed-vocabulary-and-a-guard-on-the-model.md), each as amended that day).

| The draft said | What changed | Now |
|---|---|---|
| The notice of who reads what is typed stands beside the box, before anything is typed | Nothing stands beside the box: not the website's own line, not the service's notice, and not the link to how words are handled. The same notice is on the page of methods, under "How your words are handled", and the foot of every page leads there, by the word "Privacy" | Every sentence that said "the notice beside the box" says where the notice is. Sections 3, 4, 5, 6, 12 and 13, and Appendices A, B and C |
| The website shows what the service sends each time the page is opened | The page of methods is built ahead of time, and built again each hour at most. It shows what the service said when it was built | Section 4, marked `[SETTING]`: the website is built again when the provider changes |
| A person is told before they type, whether they looked for it or not | A person is told when they look for it | Section 4, with a mark for the founder. The rule that the checklist holds under task 6 asks that a person is told at the time their data is obtained. Whether a page the foot leads to meets it is not settled: [README.md](README.md) has it among the sentences that carry the most risk |
| Words that are not a plain list are applied to nothing, and a person chooses | The website applies what was read of them, and asks nothing. Each thing it applied is shown under the box, and can be taken off. Recorded crime, and what counts who lives somewhere, are applied only where a person chooses them. Since that night so are two things more, where the words do not say how they are meant: a rule that would look in one area alone or leave one out, and a thing that can count either way. Since 27 September 2026 recorded crime is applied where a person's own words name it, and a wish that may be somebody else's is left for the person | Section 3, step 3 |
| Nothing a model reads is applied until the person chooses it, which was marked as not yet built | It is decided the other way: what a model reads is checked by Burro's code, and then applied | Sections 3 and 4. Row 14 of what stands between this draft and publishing is the founder's now, and no longer the build's |
| No sentence is sent until the service has said who reads | As it was. Nothing beside the box says that the page is waiting, or why | Section 3, step 1 |

## Before this is published

| # | What is missing | Kind | Section |
|---|---|---|---|
| 1 | The legal name, the address and the contact for requests | Founder | 1 |
| 2 | Whether a language model reads what is typed at launch, and whose. If one does: its terms accepted in a name, and every sentence people are told of it checked by a person against the company's own page | Founder | 4 |
| 3 | A step that asks before a sentence is sent. The website asks nothing. Until 26 September 2026 it showed the service's notice beside the box before anything was typed. It shows nothing there since, and the notice is on the page of methods | Not built | 5, 11 |
| 4 | The age limit | Founder | 16 |
| 5 | A way to delete one shared link. Today the only way is to restart the service, which deletes all of them | Not built | 7, 14 |
| 6 | A page for this notice on the website, with the service's notice shown in section 4 as it is served, and a link to the page beside the box where a person types. Since 26 September 2026 nothing beside the box leads anywhere: the founder asked for the link to go. The foot of every page leads to how words are handled, by a link named "Privacy", which a person will take for the way to this notice | Not built | all |
| 7 | An agreement on data processing with Fly.io. None was found on a public page | Founder | 9 |
| 8 | Code that refuses DeepSeek on any release that is not made up. Until it exists, the sentence about DeepSeek in section 4 is held by a setting and by nothing else | Not built | 4 |
| 9 | Where email to Burro is received, and how long it is kept | Founder | 10 |
| 10 | The fee paid to the ICO, and the other steps of [data-protection-checklist.md](data-protection-checklist.md) | Founder | |
| 11 | The census table on an area's page, and the measures of age and of households. No page shows a table and no release holds a measure | Not built | 18 |
| 12 | A mailbox, and someone who answers within the times sections 14 and 15 promise | Founder | 14, 15 |
| 13 | Every row of "What is true only while a setting holds", set and checked at the host or the provider | Founder | 2, 4, 8, 9, 12 |
| 14 | Whether this notice may say that what a model reads is applied without asking. Until 26 September 2026 this row asked that nothing a model reads is applied until the person chooses it. The founder decided the other way that day, and [ADR 0012](../adr/0012-a-closed-vocabulary-and-a-guard-on-the-model.md), as amended, says what that risks | Founder | 3, 4 |
| 15 | The equality regulator's guidance for service providers, read by a person. Section 18 rests on the Act as printed and not on the guidance | Founder | 17, 18 |
| 16 | No copy kept of a police file that holds records of stop and search. The police give recorded crime, outcomes and stop and search from one form, and a file saved whole holds all three | Founder | 18 |
| 17 | Who sends the email that a link to sign in arrives in: the company by name, its agreement on data processing, where it keeps an email and for how long, and that it does not rewrite a link to count who pressed it | Founder | 9, 13, 20 |
| 18 | How long each thing of an account is kept. Section 20 lists each, with what is built and what there is to choose | Founder | 12, 20 |
| 19 | Whether a person's last searches are kept from the moment they sign in, or only once they turn that on. It is built both ways | Founder | 20 |
| 20 | The lawful basis for an account and for what it keeps, and whether the cookie that keeps a person signed in may be set without asking | Founder | 11, 20 |
| 21 | What is done for a person who can no longer read the email address of their account, and asks for the account to be deleted | Founder | 14, 20 |
| 22 | How long the company that hosts the service keeps its daily copies of the disk that holds accounts. An account that is deleted is in those copies until they are let go | Founder | 12, 20 |

## What is true only while a setting holds

The code was read against this notice on 23 September 2026, twice, and again on 24 September 2026. These sentences are not held by the code or by a test. Each is true only while someone keeps a setting as it is. Burro was first deployed on 25 September 2026, with the made-up city. This notice does not say which of the settings were set then.

| Sentence | Section | The setting it rests on | Where the setting is written down |
|---|---|---|---|
| No language model reads what you type | 3, 4 | No provider is named in `BURRO_MODEL_PROVIDER`, or its terms are not accepted by name in `BURRO_MODEL_TERMS_ACCEPTED`. A key alone turns nothing on: that part is held by code and by a test | `choose` in `services/api/src/burro_api/providers/choose.py`. [ADR 0019](../adr/0019-no-one-provider-and-a-key-alone-turns-nothing-on.md) |
| Your words go alone | 4, 6 | `BURRO_MODEL_SENDS_SETTINGS` is not the one word `yes`. The notice on the page of methods says which is so, from the same setting | `choose.py`. [models.md](../design/models.md), section 6 |
| DeepSeek is never used for what real people type | 4 | `BURRO_MODEL_PROVIDER` is never `deepseek` on a service that real people use, and nobody accepts its terms for one. No code refuses it | [ADR 0019](../adr/0019-no-one-provider-and-a-key-alone-turns-nothing-on.md) |
| Burro waits 6 seconds for a model | 4, 12 | `BURRO_MODEL_TIMEOUT_S` is left unset. It may be set to anything up to 60 | `DEFAULT_TIMEOUT_S` and `model_timeout_s` in `settings.py` |
| There is no analytics | 2 | Web Analytics, Speed Insights and the toolbar are off at Vercel. Vercel serves its analytics script from the website's own address, so the website's own rules would not stop it | [deploy/web/README.md](../../deploy/web/README.md) |
| Requests for pages are logged for 1 day | 9, 12 | The Pro plan, with no log drain and no Observability Plus | [deploy/README.md](../../deploy/README.md) |
| Log lines are kept for 7 days, and only by Fly.io | 8, 9, 12 | No log shipper and no add-on that records paths | [deploy/README.md](../../deploy/README.md) |
| The service runs in London | 9, 13 | One machine, one region | `deploy/api/fly.toml` |
| There are no accounts: Burro asks for no email address and sets no cookie | 2 | Accounts are off, at the service and at the website. One setting at each turns them on | [The design of accounts](../design/accounts.md), section 2 |
| A link to sign in is sent as Burro wrote it, and the company that sends the email does not record who pressed it | 20 | The sender's own settings for following links and for counting who opened an email, which are both off | [deploy/README.md](../../deploy/README.md#turning-accounts-on) |
| The file that holds accounts is encrypted where it is kept | 20 | The disk was made without the option that leaves it unencrypted | [deploy/README.md](../../deploy/README.md#turning-accounts-on) |
| A daily copy of the disk that holds accounts is kept for 5 days | 12, 20 | How long the host is set to keep such a copy, which may be from 1 day to 60 | [deploy/README.md](../../deploy/README.md#turning-accounts-on) |
| Nobody but the host can read a request on its way | 9 | The domain's records point straight at the hosts, with no proxy in front | [deploy/README.md](../../deploy/README.md), "A domain, once there is one" |
| What a provider keeps, and that it does not train on it | 4 | Settings in the provider's own account. The checklist, task 15, lists them for each provider | [data-protection-checklist.md](data-protection-checklist.md) |
| The notice says who reads your words now | 4 | The website is built again when a provider is turned on, turned off or changed. The page that shows the notice is built ahead of time, and shows what the service said when it was built | [ADR 0023](../adr/0023-what-is-typed-goes-as-typed-and-people-are-told.md), as amended on 26 September 2026 |

## The guidance this follows

| Page | Address | Its own notice, as read |
|---|---|---|
| What privacy information should we provide? | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/the-right-to-be-informed/what-privacy-information-should-we-provide/> | "Due to changes made by the Data (Use and Access) Act, this guidance is under review and may be subject to change." |
| How to write a privacy notice and what goes in it | <https://ico.org.uk/for-organisations/advice-for-small-organisations/privacy-notices-and-cookies/how-to-write-a-privacy-notice-and-what-goes-in-it/> | The same |
| How to deal with data protection complaints | <https://ico.org.uk/for-organisations/how-to-deal-with-data-protection-complaints/> | Updated 8 May 2026 |

For accounts, six pages more. Each was read on 26 September 2026, at the address given, through a reader that extracts of a page and not the page itself, so check the wording at the address before this is published. [Appendix C](#appendix-c-what-this-notice-says-of-the-law) says which sentence rests on which.

| Page | Address | Its own notice, as read |
|---|---|---|
| Contract, as a lawful basis | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/a-guide-to-lawful-basis/contract/> | "Due to changes made by the Data (Use and Access) Act, this guidance is under review and may be subject to change." |
| Guidance on the use of storage and access technologies, "What are the exceptions?" and "What are the PECR rules?" | <https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-the-use-of-storage-and-access-technologies/what-are-the-exceptions/> | The guidance says that it was finalised after two consultations, and was last updated on 29 April 2026 |
| Right to erasure | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/> | Under review, in the same words as the first |
| Right to data portability | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-data-portability/> | The same |
| Storage limitation | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/storage-limitation/> | The same |
| Data protection by design and by default | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/guide-to-accountability-and-governance/data-protection-by-design-and-by-default/> | Updated on 5 February 2026, for the Data (Use and Access) Act |

The first page lists what a notice must hold. The sections below are in the order a person would ask. [Appendix A](#appendix-a-what-the-ico-asks-for-and-where-it-is) says where each item on the ICO's list is answered. [Appendix B](#appendix-b-what-each-claim-rests-on) says which file or test keeps each claim true.

---

The notice starts here.

---

# How Burro handles what you tell it

Last updated: `[FOUNDER: date of publication]`

## In short

| You may ask | Answer |
|---|---|
| Do I need an account? | No. You can search, compare areas and share a search without one. `[SETTING: accounts are turned on]` You can make an account if you want Burro to keep a search for you. Section 20 |
| Does Burro know who I am? | Not unless you make an account. It asks for no name. If you make an account it holds your email address, and what you choose to keep |
| What happens to what I type? | It is read and turned into search settings, which the page shows you under the box so that you can take off any that is wrong. Burro does not keep it and does not write it to a log |
| Does anyone else receive what I type? | The company that hosts Burro's service carries it to Burro, and can read it on the way. Section 9. If a language model reads your words, the company that runs the model receives them as well. The page that says how your words are handled, which the foot of every page leads to, holds a notice that says whether one does, which company, what is sent, how long it is kept and whether it is used to train a model. Section 4 says what never changes |
| Are there cookies, analytics or tracking? | There is no analytics and no tracking. There is no cookie unless you ask for a link to sign in. Burro then sets two, which are there to sign you in and to keep you signed in, and for nothing else. Sections 2 and 20 |
| What does Burro keep? | A shared link, if you make one. A record of each call, with no words in it. An email, if you send one. If you make an account: your email address, and the searches that you keep. Section 20 |
| Who else is involved? | The two companies that host Burro. They receive your internet address, as any website's host does. The one that runs the service also receives each request, with what you typed in it. Section 9. If you make an account, a company that sends email receives your email address. Section 20 |
| What does Burro know about the people who live in an area? | Published counts for areas of several thousand people. Nothing about any one person. Section 18 |
| How do I ask a question or complain? | Section 15 |

## 1. Who runs Burro

| | |
|---|---|
| Who is responsible for your data | `[FOUNDER NAME]`, or `[COMPANY NAME]`, company number `[COMPANY NUMBER]`. `[FOUNDER: for a sole trader, the person's own name and the business name. For a company, the company's name, its registered number and where it is registered]` |
| Address | `[FOUNDER: a geographic address]` |
| Contact for privacy questions, requests and complaints | `[FOUNDER CONTACT]`. `[FOUNDER: an email address or a form]` |
| Registered with the ICO | `[FOUNDER: registration number, once the fee is paid]` |
| Data protection officer | None. Burro has not appointed one |

Burro decides why and how your data is used. Data protection law calls that a controller. `[FOUNDER: the word is the ICO's. No page that defines it was read for this draft. Appendix C]`

## 2. What Burro does not collect

| Burro does not | How |
|---|---|
| Ask who you are | Nothing asks for a name. Nothing asks for an email address unless you choose to make an account, and nothing that you can do without one asks you to make one. Section 20 |
| Set a cookie, or read one | The website sets none, and the service that answers searches sets none and reads none, unless you ask for a link to sign in. Section 20 says which two cookies are then set, what each is for and how long it lasts |
| Keep anything in your browser | Burro writes nothing to your browser's storage. A search lives in the page's memory and is gone when you close or reload the page, unless you have signed in and kept it. Your browser keeps its own history of the pages you open, as with any website. The address of an area's page, of a comparison and of a shared link you open is in it |
| Count visits | The website holds no analytics. `[SETTING: the company that serves the pages offers analytics, and Burro leaves it switched off]` |
| Load anything from another company | No script, font, image or style comes from anyone but Burro. The website tells your browser to refuse any that does |
| Ask for your location, camera or microphone | The website tells your browser to refuse all three |
| Tell other websites where you came from | When you follow a link to a source, your browser is told not to say which page you were on |
| Write your internet address in its own log | Burro's log has no field for it. The companies that host Burro do receive it. Section 9 |
| Build a profile of you | Nothing ties one search to the next, unless you have signed in and Burro keeps your last searches for you. It keeps ten, shows them to you and to nobody else, and draws no conclusion about you from them. Section 20 |

## 3. What you type

You can search with the form alone. The form sends settings and no sentence.

If you type a sentence, this is what happens to it.

| Step | What happens |
|---|---|
| 1 | As the page opens it asks Burro's service who else reads what you type. Nothing you type is sent until the service has said. The notice of who reads is on the page that says how your words are handled, which the foot of every page leads to. `[FOUNDER: until 26 September 2026 the box showed that notice before you typed. Nothing beside the box says it now]` |
| 2 | When you press Search, your browser sends the sentence to Burro's service, inside the body of a request. It is never put in a web address. It does not pass through the company that serves the website's pages. It does pass through the company that hosts the service. Section 9 |
| 3 | Burro reads it, and turns what it read into settings: a budget, a journey, what matters to you. It asks nothing. Where your words may set a firm limit or a guide, Burro takes the guide, which leaves no area out, and marks the setting "assumed". It sets nothing about recorded crime unless your own words ask for it by name, as "gritty" or "low crime" do, or you choose it yourself. It sets nothing about who lives somewhere unless you choose it yourself, and nothing that your words do not say is your own wish, as where you write what somebody else would like. `[FOUNDER: until 27 September 2026 nothing was set about recorded crime unless a person chose it, whatever they had typed. ADR 0012, as amended that day]` Where your words do not say how you mean them, it does not guess whether to look in one area alone or to leave it out, or which way a thing should count, such as more pubs or fewer: it leaves each for you, and names what it left in a line under the box |
| 4 | Burro sends the settings back to your browser, with where in your sentence each one came from, as positions and not as words. The page shows each setting under the box, and you can take any of them off |
| 5 | Burro drops the sentence. It is not stored and not written to a log |

| Fact | Value |
|---|---|
| Longest sentence | 600 characters |
| Who reads it | Burro's own rules. A language model as well, if the notice on the page that says how your words are handled says so |
| What a model may do | Read your words into settings. Burro's own code checks what it read, and what passes is applied and shown to you, marked "assumed" where you did not say it in so many words. `[FOUNDER: until 26 September 2026 this row said that a model may propose, and that nothing it reads is applied until you choose it, which was marked as not built. You decided that day that Burro asks nothing. ADR 0012, as amended, says what that risks: a reading that is wrong now moves the ranking, where it moved an offer]` |
| What Burro keeps of it | Nothing |
| What Burro's log holds about the call | The time, counts and codes. No words, no place, no settings. Section 8 lists them |
| The box that finds a place by name | What you type there is sent as you type, a quarter of a second after the last key, once there are two characters. It is sent in the body of a request, 80 characters at most. It is used to find places and is not stored or logged. It is never sent to a language model |

## 4. If a language model reads your words

A language model is a computer program that reads text. Burro may use one to read your sentence. The model is run by another company, on that company's computers. That company receives your words.

Burro can use one of four companies, and which one it uses can change. So this section says what is true whichever is in use, and the notice on the page that says how your words are handled says the rest.

### Where you are told

| | |
|---|---|
| Where | In the notice on the page that says how your words are handled. The foot of every page leads to it. `[FOUNDER: until 26 September 2026 the same notice stood beside the box where you type, before you typed anything, and you asked for it to go from there. A person is now told when they look for it. The regulator's guidance, as read for the checklist, asks that a person is told at the time their data is obtained: task 6, and the list of risks in README.md]` |
| Who writes it | Burro's service. The website has no words of its own for it, and shows what the service said when the page was built. `[SETTING: the website is built again whenever the company in use changes. Until it is, the page shows the notice of the company before, or of none]` |
| What it says | Whether a language model reads your words. Which company runs it. Whether your space requirements go with your words, which is the name the website gives the settings of your search. Whether the company uses what it receives to train its models. How long it keeps it, and whether it keeps it longer where the law requires or where it suspects misuse. Who at the company may read it. Where it is handled, and where it is stored |
| Where a company's own pages do not answer one of these | The notice says that they do not |
| If no model reads your words | The notice says: "What you type is read by rules that are part of Burro. It is not sent to a language model." |
| If the service cannot say who reads | Nothing you type is sent |
| On this page | `[NOT BUILT: the same notice is shown here, as the service serves it, with the pages each sentence was read on]` |

### What never changes

| | |
|---|---|
| The companies Burro can use | Google, OpenAI, Anthropic and DeepSeek. One at a time, and none unless all of this holds: whoever runs Burro has named the company, holds its key, has accepted its terms by name, and a person has checked every sentence of the notice against the company's own pages. A key alone turns nothing on |
| DeepSeek | It is never used for what real people type. It is for made-up test sentences only. `[SETTING: whoever runs the service never names it on a service that real people use]` `[NOT BUILT: the service refuses it on any data that is not made up]` |
| With no company in use | Burro's own rules read your words, in Burro's service. Nothing you type leaves Burro for a company that runs a model. The company that hosts the service still carries the request. Section 9 |
| What is sent | Your words. `[SETTING: your space requirements go with them only if the service is set to send them, and the notice on the page that says how your words are handled says which is so]` With them go Burro's own instructions to the model, which are the same for everyone |
| What your space requirements are, where they are sent | The settings of your search, which section 6 is about: renting, buying or visiting, the budget, how long each journey may be and by what means, what matters to you and how much, and any area you ruled in or out |
| What is never sent | Your internet address: the call comes from Burro's service, not from your browser. The places you need to reach: where settings are sent, each place is replaced by its position in the list, 1, 2 or 3. Anything that says who you are, unless you type it. A place you name in the sentence itself is in the sentence |
| What the model does | It reads your sentence into settings, which Burro's own code checks before any is applied. It never ranks a place, scores one or describes one |
| What the company's library does | Nothing. Burro uses no company's own software. Each call is one request that Burro's code makes itself |
| If the model is slow or fails | Burro's rules answer in its place. Your words were still sent. Burro waits 6 seconds, and the call is given up at the same limit. `[SETTING: whoever runs the service can set another time, up to 60 seconds]` |
| If a company refuses Burro's calls | After three refusals in a row Burro asks it nothing for five minutes, and the rules read in that time |
| Can Burro delete the company's copy? | No. Burro cannot tell the company which words were yours, because it keeps no record of them |
| Advice | Leave out your health, your religion and anything else you would not want kept. The notice says the same wherever a model reads. `[FOUNDER: the advice stood beside the box until 26 September 2026. It is now on the page that the foot leads to, so a person who types may not have read it]` |

`[SOLICITOR]` The ICO's list asks a notice for the recipients, the periods and the transfers. This notice gives the four companies by name and leaves the periods and places to the notice the service serves. Until 26 September 2026 that notice was shown at the moment a person types, beside the box. It is now shown on the page of methods. Whether a page that points there is enough, or whether it must repeat what that notice says, is not settled, and it is less settled than it was.

`[FOUNDER: what the notice says of each company today is in providers/terms.py, and models.md, section 6, shows it side by side. A test holds that page to the code. As the table stands no company can be turned on: nobody has checked a sentence of any of the four.]`

`[FOUNDER: what you accepted on 24 September 2026. Google keeps what is typed for 55 days. The period cannot be shortened on this service. Its staff may read what it flags, and it gives no period for what it flags. What is typed may be handled and stored in any country where Google or its agents have facilities. The notice says each of these when Google is the company in use.]`

`[FOUNDER: two of the four companies' terms restrict the use of their names. The ICO asks that recipients be named. This notice names all four. models.md, section 10, point 13.]`

## 5. Sensitive things in a sentence

People who describe where they want to live often say something about their health, their religion, their family, their sexuality or where they come from. The ICO says the law gives some of this extra protection, and calls it special category data.

| The law's list, in the ICO's words |
|---|
| "personal data revealing racial or ethnic origin" |
| "personal data revealing political opinions" |
| "personal data revealing religious or philosophical beliefs" |
| "personal data revealing trade union membership" |
| "genetic data" |
| "biometric data (where used for identification purposes)" |
| "data concerning health" |
| "data concerning a person's sex life" |
| "data concerning a person's sexual orientation" |

Source: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/a-guide-to-lawful-basis/special-category-data/>. Read.

How Burro treats a sentence that holds some:

| | |
|---|---|
| Burro does not ask for it | Nothing on the website asks about your health, religion, ethnic group, sexuality or politics |
| You do not need to say it | Ask for the thing, not the reason. "Near a park" works. "Quiet" works. You can also use the form, which takes no sentence |
| If you say it anyway | The sentence is read like any other, and dropped like any other. Burro keeps none of it |
| Burro makes no setting about you | No setting says who you are. Burro's code draws no conclusion about you from what you ask for, holds nothing to draw one from, and treats nobody differently for what they typed |
| If you ask for fewer of any group of people | Burro makes no setting from it, tells you so in one sentence, and answers the rest of your request. This is so for every group: by ethnic group, religion, age, family, or anything else about who lives somewhere |
| If you ask for a community | Burro ranks on what is there and never on who is there. `[NOT BUILT: a wish for a community is met through places of worship, cultural centres and food shops. As the data stands Burro holds none of these, and says that it cannot answer]` |
| If you ask for more people of an age, or more households of a kind | `[NOT BUILT: it can become a setting about the area, from the census of 2021. Section 18. As the code stands Burro makes no setting from it]` |
| The list can miss a request | Burro finds a request about who lives somewhere from a list of words. A request the list misses is read like any other words, and no sentence tells you. Where a model reads your words, a request that the list and the model both miss can become a setting about what is in a place. The contract, sections 8.2 and 13, names this as a gap that code narrows and cannot close |
| If a model reads your words | The company that runs it receives the sentence as you typed it, sensitive parts included, and keeps it as the notice on the page that says how your words are handled says. That notice ends with the advice to leave out your health, your religion and anything else you would not want kept |
| Before a sentence is sent | Nothing is shown beside the box, since 26 September 2026. `[NOT BUILT: Burro asks you first. The words of the question are in section 11. The website does not ask this yet]` |

A setting can say something about you as well. One that asks for a place of worship, or that names a hospital or a school as a place to reach, is a wish about a place. Burro treats it as that and as nothing more. Section 6 says where a setting goes.

## 6. The settings of your search

| | |
|---|---|
| What they are | Renting or buying, a budget, up to three places to reach and how long each journey may be, what matters to you and how much, and any area you ruled in or out |
| Where they live | In your browser, in the page's memory |
| What Burro's service does with them | Your browser sends them with each request. The service ranks the areas, answers, and keeps nothing |
| Do they go to a language model | `[SETTING: only if the service is set to send them, and the notice on the page that says how your words are handled says so]` Where they go, they go without the places you need to reach. Section 4 |
| Are they logged | No setting is logged, and no code made from the settings alone. When you type a sentence, the counts and codes in its log line come from your words and your settings together: a code can say that a request changed nothing, which depends on what was already set. None holds a number, a name or a place. [ADR 0011](../adr/0011-nothing-is-kept-for-a-search.md) leaves it to the founder whether to go on writing them |
| When they are gone | When you close or reload the page, unless you have signed in and keep the search |

The places you need to reach can say where you work or where your child goes to school. What matters to you can say something too: a place of worship, or a kind of food shop. That is why Burro keeps no search unless you ask it to, and why a place and a setting are never written to a log.

## 7. A shared link

You can make a link to a search. Burro stores it only when you ask. If you have no account it is the one thing of a search that Burro stores.

| | |
|---|---|
| What the link holds | An id made at random. It says nothing about the search |
| What Burro stores under the id | The settings of the search, whether a place in them was replaced, the data release it was made on, and the time it was made, to the second. The settings hold what matters to you, so a link can say that a search asked for a place of worship |
| What Burro does not store | What you typed, or anything about who made the link |
| The places you named | Each is replaced by the station or district that stands in for it, unless you tick "Share the exact places" |
| Who can open it | Anyone who has the link |
| How long it is kept | `[FOUNDER: a period, once links are kept in a database]`. Today links are held in memory. Every link is lost when the service restarts, which happens at each update. Burro keeps 50,000 at most and lets the oldest go |
| How to have one deleted | `[NOT BUILT: send the link to the contact in section 1 and Burro will delete it. Today one link cannot be deleted without deleting all of them]` |

## 8. What Burro writes down

| Record | What it holds | What it never holds | Kept for |
|---|---|---|---|
| A log line for each request | The time, to the second. A request id made by Burro, the kind of request, whether it worked, how long it took, which data release answered, and whether that data is made up or a preview. For a sentence: whether the rules or a model read it, which company's model and which model, how many tokens were used, how many settings were made of each kind, how many were refused and why, and codes from a fixed list. A code can say that the request asked for something Burro cannot answer, such as "health services" or "community amenities", or that it asked about who lives somewhere | Your words, your settings, a place, a link's id, the web address asked for, your internet address, your browser's name. Nothing in a line says whose request it was | 7 days, by the company that hosts the service. `[SETTING: no log is sent on to anyone else]` Section 9 |
| A line when the service starts, and a line when a company is left alone | Which company's model is not used, and which of a fixed list of reasons is why. That a company is being asked nothing for a while | Anything that was set, and anything of a request | With the log lines |
| A record of each call to a reader, and of each call to the part that writes the reasons for a result | An id made at random for the call. The time to the second, whether the rules or a model was asked, which company's and which model, which data release, how it went, how long it took, how many tokens were used. "How it went" is one of eight codes. One of them says that the request asked about who lives somewhere | The same | 30 days at most. Today it is held in memory, 10,000 at most, and lost at each restart |
| A report of an error | The kind of error, the kinds of error that led to it, and where in the code it happened | The error's message, which could repeat what you typed | With the log lines |
| `[SETTING: accounts are turned on]` A log line for each thing that happens when somebody signs in | The time, to the second. What happened, which is one of nine fixed words: that a link was asked for, was sent, could not be sent, was used or was turned away, that somebody signed in or was signed out, that too much was asked for, or that an account was deleted. How it ended, which is one of six fixed words | Your email address, the link, your internet address, and anything that says which account or which browser it was. Nothing in a line says whose sign-in it was | With the log lines |
| `[SETTING: accounts are turned on]` What has happened to your account | The same two words and the time, kept with your account so that you can read them there | The same | With your account. Section 20 |

## 9. The companies that host Burro

Burro runs on other companies' computers. Each receives what any host of a website receives.

| Company | What it does | What reaches it | What it keeps | Where | Agreement on data processing |
|---|---|---|---|---|---|
| Fly.io | Runs the service that answers searches | Every request to the service: your internet address, and the request itself, which holds what you typed and your settings. The id of a shared link, when one is opened | Burro's log lines, for 7 days. **Read**, at <https://fly.io/docs/monitoring/logging-overview/>. What its own systems record of a request was not said on the pages read. **Not read** | The machine is in London. Your connection may be decrypted at the Fly.io computer nearest you, which may be outside the UK, and passed on encrypted. **Not read again: from [deploy/README.md](../../deploy/README.md)** | None found. The list of its legal documents names none. **Not read** |
| Vercel | Serves the pages of the website | Requests for pages: your internet address, your browser's name and the page asked for. The address of an area's page names the area, and the address of a comparison names the areas compared. So Vercel can see which areas an internet address looked at. Since the website was given its look, the address of a drawing names what the drawing is of, and a small drawing stands beside each thing a search holds: so Vercel can see which kinds of thing a search held, a vibe by its name among them, and never a place, a sum or a number of minutes. Never what you type into a search, and never the id of a shared link: your browser sends the first straight to the service, and keeps the second in the part of the address that is sent to no server. `[SETTING: accounts are turned on]` What you send for an account does pass through this company on its way to the service: your email address when you ask for a link, the code of the link when you confirm it, the two cookies, and the settings of a search that you keep. Burro's code there passes them on and writes none of them down. Section 20 | Request logs for 1 hour on the Hobby plan, which is the free plan and the one in use. **Not read again: from [deploy/web/README.md](../../deploy/web/README.md)**. For 1 day on the Pro plan. `[SETTING: the plan, and no add-on that keeps logs longer]` **Read**, at <https://vercel.com/docs/logs/runtime>. It can match a request to an internet address. **Read** | Pages that are rebuilt, in London. Other files from wherever is nearest you. **Not read again: from [deploy/README.md](../../deploy/README.md)** | Part of its terms, for the Pro and Enterprise plans. **Read**, at <https://vercel.com/legal/dpa>, dated 17 March 2026 |
| `[FOUNDER: the company that holds the domain's name records]` | Tells your browser where Burro is | The name your browser looks up | **Not read** | | |
| `[FOUNDER: the company that sends email]` `[SETTING: accounts are turned on]` | Sends the email that a link to sign in arrives in | Your email address, and the email, which holds the link | `[FOUNDER: what it keeps of an email, and for how long]` **Not read: no company is chosen** | `[FOUNDER]` | `[FOUNDER]` |

Burro was first deployed on 25 September 2026, to Fly.io and to Vercel, with the made-up city. This table was written before that, from the plan in [deploy/README.md](../../deploy/README.md), and is what that plan makes true. It changes if a host changes, or the plan at a host.

Later, and not yet: a company to serve map tiles, a store for links that outlives an update, and a service that collects error reports. Each will be added here before it is used.

Accounts add one company, which is the one that sends email. They are kept in a file on the computer that runs the service, at Fly.io, and in no database of another company's. Section 20.

## 10. When you write to Burro

| | |
|---|---|
| What Burro receives | Your email address, your name if you give it, and what you write |
| What it is used for | To answer you, and to keep a record of requests and complaints |
| Where it is received | `[FOUNDER: the mail provider]` |
| How long it is kept | `[FOUNDER: a period. Two years from the last message is a common choice. It was not read at a source]` |

## 11. Why Burro is allowed to do this

The ICO says the law asks for a reason, called a lawful basis, for each use of personal data, and that where the data is special category data it asks for a second reason, called a condition. Its words: "you must identify both a lawful basis under Article 6 of the UK GDPR and a separate condition for processing under Article 9." Source: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/a-guide-to-lawful-basis/special-category-data/>. Read.

The ICO says: "You must determine your lawful basis before you start using the personal information and you must document it." Source: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/a-guide-to-lawful-basis/>, updated 2 April 2026. Read.

Every cell of this table is this draft's proposal. None is a statement of what the law requires, and nobody qualified has read it.

| What | Lawful basis proposed | Condition for special category data proposed |
|---|---|---|
| Reading the sentence you type, by Burro's rules or by a model | Consent. `[NOT BUILT: the website does not ask]` | Explicit consent. `[NOT BUILT]` |
| Finding a place by the name you type | Legitimate interests: to offer you places to pick from | None claimed, with the same doubt as the row below |
| Ranking areas from your settings | Legitimate interests: to answer the search you made | None claimed. No setting asks anything about you. A place you need to reach can still say something about you, where it is a hospital or a place of worship, and so can a wish for a place of worship. The ICO says that a guess becomes special category data where "your processing intends to make an inference linked to one of the special categories of data; or you intend to treat someone differently on the basis of inferred information". Read twice. Burro does neither. `[SOLICITOR]` |
| Storing a shared link | Legitimate interests: to do what you asked when you pressed "Make the link" | None claimed, for the same reason and with the same doubt |
| Log lines and call records | Legitimate interests: to keep the service running and to see what it costs | None claimed. No line says whose request it was. A code can say that a request was about health services or about who lives somewhere. README.md, risk 10 |
| Your internet address, at the hosts | Legitimate interests: a website cannot be served without it | None claimed |
| Answering your email, request or complaint | Legitimate interests, and legal obligation where the law requires an answer | Explicit consent, if you tell Burro something sensitive in it |
| `[SETTING: accounts are turned on]` Making your account, signing you in and keeping you signed in: your email address, the record of the links you asked for, and the record of where you are signed in | Contract: you asked Burro to keep an account for you, and it cannot do so without these. The ICO says this basis applies where "you need to process their personal data to do what they ask", and that a contract "does not have to be a formal signed document, or even written down". Read on 26 September 2026. Whether using a free website makes such an agreement is not settled here. README.md, risk 20 | None claimed |
| Keeping a search that you pressed to keep | Contract, for the same reason | None claimed. A search that is kept can hold a wish for a place of worship, or a hospital as a place to reach, beside an email address. This draft treats it as a wish about a place, as it treats any setting. The doubt is greater here, because the person can be named. `[SOLICITOR]` README.md, risk 18 |
| Keeping your last ten searches | `[FOUNDER: if they are kept from the moment a person signs in, legitimate interests: to show a person what they searched for. If they are kept only once a person turns that on, contract. README.md, risk 20]` | None claimed, with the same doubt as the row above |
| Counting how often a link is asked for, for an email address and from an internet address | Legitimate interests: to keep anybody from making Burro send a great deal of email, to one person or to many | None claimed |
| Keeping what has happened to your account | Legitimate interests: to let you see whether somebody else has signed in to your account | None claimed |

`[FOUNDER: this table is the most important choice in this notice, and nobody qualified has made it. README.md, risk 1, sets out the other choice: legitimate interests for the sentence, with no step that asks.]`

The question the website would ask, before the first sentence of a visit is sent:

> `[NOT BUILT]` What you type may say something about your health, your religion, your family or where you come from. Burro reads it to turn it into search settings, and does not keep it. `[If a model reads what is typed: the notice the service serves, whole, in place of this sentence.]` Do you agree? You can say no and use the form.

| What the ICO asks of consent | How the step would meet it |
|---|---|
| "a clear statement (whether oral or written), rather than by any other type of affirmative action" | A button that says "I agree", not a box ticked in advance |
| It must "specify the nature of the special category data" | The question names health, religion, family and origin |
| It "should be separate from any other consents" | It asks one thing |
| As easy to withdraw as to give | Stop typing, or use the form. Nothing is kept by Burro to take back. The company's copy cannot be recalled: section 4 |
| A record that shows consent was given | Burro keeps no record of a person, so it can show only that a sentence cannot be sent without the button. Whether that is enough is not settled. README.md, risk 1 |

Sources: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/special-category-data/what-are-the-conditions-for-processing/> and <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/consent/what-is-valid-consent/>. Read.

Where Burro relies on legitimate interests, you can object. Section 14.

**The two cookies of an account** fall under a second set of rules, which are about keeping anything in a person's browser. The ICO states the rule as "a person must not store information, or gain access to information stored, in the terminal equipment of a subscriber or user", and gives exceptions to it. One is for what is "essential to provide the service the subscriber or user requests", and among what the ICO lists as likely to meet it is "Identifying a user once they have logged in to an online service for the duration of their visit to the site". Read on 26 September 2026, at <https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-the-use-of-storage-and-access-technologies/what-are-the-exceptions/>, in guidance that the ICO says it finalised on 29 April 2026. `[SOLICITOR]` This draft reads both cookies as within that exception, and so asks no permission for them. The cookie that keeps a person signed in lasts for 30 days, which is longer than a visit. README.md, risk 19, says why that reading may be wrong and what the other choice is.

## 12. How long each thing is kept

| Thing | Kept by | For how long |
|---|---|---|
| What you type | Burro | Not kept. It is held in the service's memory while it is read, and then dropped. Where a model is slow Burro stops waiting after 6 seconds, and the call is given up at the same limit. `[SETTING: up to 60]` It is never written down |
| What you type | The company that runs the model, if one reads your words | As the notice on the page that says how your words are handled says. It differs by company, and one of the four gives no period. Where a company suspects misuse, or the law requires it, it may keep what it received for longer |
| Your settings | Burro | Not kept, unless you make a link |
| A shared link | Burro | Section 7 |
| Log lines | Fly.io | 7 days. `[SETTING]` |
| Records of calls | Burro | 30 days at most. Today, until the service restarts |
| Requests for pages | Vercel | 1 day. `[SETTING]` |
| Email | `[FOUNDER: the mail provider]` | `[FOUNDER: a period]` |
| `[SETTING: accounts are turned on]` Everything of an account | Burro, and the two companies below | Section 20 has a row for each thing, with how long it is kept |
| A daily copy of the disk that holds accounts | Fly.io | 5 days. `[SETTING]` `[FOUNDER: from 1 day to 60. Section 20]` |
| The email that held a link to sign in | `[FOUNDER: the company that sends email]` | `[FOUNDER: as that company keeps it]` |

## 13. Where your data goes

Burro is run from the United Kingdom. Some of the companies it uses are outside it. The ICO calls sending personal data to a separate company outside the UK a restricted transfer, and says it needs UK adequacy regulations, a safeguard or an exception. Source: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/international-transfers-a-guide/>, dated 15 January 2026. Read. Whether each row below is enough is this draft's reading, not advice.

| Company | Country | What goes | Safeguard | How it is known |
|---|---|---|---|---|
| Fly.io | United States. The machine is in London | Requests to the service | Its privacy policy says it complies with the "UK Extension to the EU-U.S. Data Privacy Framework" | **Read**, at <https://fly.io/legal/privacy-policy/>, dated 20 July 2026. Whether that covers data it handles for a customer was not said. **Not read** |
| `[FOUNDER: the company that sends email]` `[SETTING: accounts are turned on]` | `[FOUNDER]` | Your email address, and the email that holds your link | `[FOUNDER]` | **Not read: no company is chosen** |
| Vercel | United States. Rebuilt pages in London | Requests for pages | Standard contractual clauses with the UK addendum | **Read**, at <https://vercel.com/legal/dpa> |
| The company that runs the model, if one reads your words | As the notice on the page that says how your words are handled says. None of the four handles what it receives in the United Kingdom alone | What you type, and your settings if the notice says so | It differs by company. [models.md](../design/models.md), section 3, has each. One of the four names none, and it is the one that is never used for what real people type | Read for the four reports in [docs/research/models/](../research/models/) |

`[FOUNDER: before launch, look each United States company up on the Data Privacy Framework list and check that it has signed up to the UK Extension. The checklist says how.]`

## 14. Your rights

The ICO lists these rights over your personal data. In most cases they are free to use.

| Right | What it means | What Burro can do |
|---|---|---|
| To be informed | To be told how your data is used | This notice |
| Of access | To get a copy of what is held about you | Burro holds nothing that it can tie to you, unless you have written to it. It will tell you so. A shared link shows the settings stored under it to whoever opens it, with the data release it was made on. The time it was made is stored and is not shown |
| To rectification | To have a mistake put right | The same. A shared link cannot be changed. Make a new one |
| To erasure | To have data deleted | A shared link: section 7. Email: ask. What you typed: there is nothing to delete at Burro |
| To restrict processing | To have data kept and not used | There is little to restrict. Ask, and Burro will say what it can do |
| To data portability | To get your data in a form another service can read | The settings under a shared link, as text |
| To object | To say no to a use that rests on legitimate interests | Ask. Burro will stop unless it has a strong reason not to, and will say which |
| Over automated decisions | Not to be subject to a decision made by a computer alone that has a legal or similar effect on you | Burro makes none. Section 17 |
| To withdraw consent | To take back a yes | Stop typing sentences and use the form. It does not undo what was already sent |

The list of rights is the ICO's, at <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/>. Read.

**If you have an account.** `[SETTING: accounts are turned on]` What the table says Burro can do is what it can do for a person who has no account. For an account it can do more, and you can do each of these yourself, signed in, on the page of your account. Section 20 says how.

| Right | With an account |
|---|---|
| Of access | The page of your account shows what Burro holds in it, and gives you a copy of all of it |
| To rectification | You can take a search away and keep another. The email address of an account cannot be changed: you make a new account and delete the old one |
| To erasure | You can delete your account, and everything in it goes at once. Section 20 says what is left for a few days in a copy of the disk |
| To data portability | The copy is one file in JSON, which is a format that other programs read |
| To object, and to restrict | You can turn off the keeping of your last searches, which deletes them. For anything else, ask |

Burro sends nothing of an account to any address but the account's own, and does not delete an account because an email asks it to. It asks the person to sign in, because only the person who can read the account's email address can.

**What Burro cannot do.** Unless you kept a search in an account, Burro keeps nothing that says which search was yours. It cannot find your words, because it has none. It cannot pick your line out of a log, because no line says whose it is. It cannot ask the company that runs a model to delete your words, because it cannot say which they were. If you can give Burro something that lets it find your data, such as a shared link, it will act on it. `[FOUNDER: Article 11 of the UK GDPR speaks of a service that does not need to know who a person is. This draft reads it as covering Burro. That is a reading, not advice, and README.md, risk 8, says why it may be wrong. Source: <https://www.legislation.gov.uk/eur/2016/679/article/11>. Read.]`

**How to use a right.** Write to the contact in section 1. Say what you want. You do not need to give a reason or use special words.

| | |
|---|---|
| How long Burro has to answer | One month. The ICO says: "without undue delay and at the latest within one month of receipt of the request" |
| Can it take longer | By up to two more months if the request is complex. Burro will tell you within the first month |
| What it costs | Nothing, in most cases |
| Will Burro ask who you are | Only if it needs to, to be sure it sends data to the right person. For a shared link, the link is enough. For an account, signing in is how Burro knows, and it asks for nothing else |

Source: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/right-of-access/what-should-we-consider-when-responding-to-a-request/>, updated 8 December 2025. Read.

## 15. How to complain

| Step | |
|---|---|
| 1. Tell Burro | Write to the contact in section 1. Burro will say it has your complaint within 30 days, look into it, keep you informed, and tell you the outcome without undue delay |
| 2. Tell the regulator | You can complain to the Information Commissioner's Office at any time: <https://ico.org.uk/make-a-complaint/>, or 0303 123 1113 |

## 16. Age

`[FOUNDER: Burro is for people aged 18 or over.]` Burro does not ask your age and does not check it.

`[SETTING: accounts are turned on]` There is one place where Burro asks. When you make an account it asks you to confirm that you are 18 or over, and it makes no account until you have. It keeps the time at which you confirmed it, with your account. It asks for no date of birth, and it checks nothing. README.md, risk 13.

## 17. Decisions made by a computer

Burro ranks areas by arithmetic. It makes no decision about you. It does not decide whether you may rent, buy, borrow or be offered anything. It makes no guess about who you are, and gives the same ranking to everyone who asks for the same things. It must never be used by anyone to choose between people: the [terms of use](terms-of-use.md), section 7, forbid it.

## 18. What Burro holds about the people who live in an area

Burro holds nothing about any person who lives anywhere. It holds published counts for whole areas.

| | |
|---|---|
| What it holds | Figures from Census 2021, taken on 21 March 2021 and published by the Office for National Statistics: the age of an area's residents, what its households were made of, and their country of birth, ethnic group and religion |
| For how large an area | Areas of several thousand people. `[NOT BUILT: no figure is shown for an area of under 1,000 people or 400 households]` |
| In what form | `[NOT BUILT: shares of a whole, never a count of people. Under one in a hundred reads "under 1%"]` |
| What is ranked on | `[NOT BUILT: the age of residents and what households were made of may count in a ranking, where you ask for more of what a figure counts. You cannot ask for fewer of anyone]` |
| What is shown and never ranked on | `[NOT BUILT: country of birth, ethnic group and religion are shown on an area's page, as the statistics office's own table, in its own words and order. Burro writes no sentence about them. Nothing can search, sort, filter or colour a map by them]` |
| What is never held | Anything about one person, one household, one home or one address. The police's records of stop and search, which say whom the police stopped and not who lives in a place. `[FOUNDER: true only once no copy of a police file that holds them is kept. Each record of a stop is about one person. A file saved with all three boxes of the police's form ticked holds them, and to keep it is to hold it, opened or not. Save the file with the crime box alone and keep no other copy. The checklist, task 18]` |
| What is never read | The police's records of stop and search. Of a police file, the files of recorded crime alone are read |
| What is not used to rank | Income, employment, health and qualifications |
| Recorded crime | Counts of what the police recorded, for an area. `[NOT BUILT: one vibe, Gritty, counts recorded criminal damage and recorded anti-social behaviour. It counts them when you ask for that vibe by name. Elsewhere recorded crime counts only when you ask for it or switch it on]` Burro never calls a place safe or unsafe |
| Is any of it about you | No. Burro does not put a figure about an area beside anything about a person, and draws no conclusion about anyone from where they live or where they search |

`[SOLICITOR]` This draft reads the ICO's pages to say that a share for an area of several thousand people is about nobody who can be identified, and so is not personal data. [The reading](residents-crime-and-equality.md), sections 4 and 9, gives the pages and says what another reading would change.

`[FOUNDER: you decided on 24 September 2026 that age and household make-up may feed a vibe and a ranking, that ethnic group and religion are shown and never ranked on, and that stop and search is never read (ADR 0006 and ADR 0014, as amended that day). On that day no page of the website showed a census table, and no release held a measure of residents or a count of recorded crime for a real place. Each sentence above that is marked is to be held by a test before it is published.]`

## 19. Changes to this notice

| | |
|---|---|
| When it changes | Before Burro starts to collect anything new, or uses a new company |
| How you will know | The date at the top changes, and this section says what changed |
| What is coming | Accounts are built, and nobody can make one yet. Section 20 says what an account keeps, and it is published before the first account can be made. A shortlist of areas may follow, and this notice will say so first |

| Date | What changed |
|---|---|
| `[FOUNDER: date]` | First published |

## 20. If you make an account

`[SETTING: accounts are turned on. While they are off nobody can make an account, Burro holds no email address and sets no cookie, and nothing in this section happens.]`

You do not need an account to use Burro. You can search, compare areas and share a search without one, and Burro then keeps nothing about you, as the rest of this notice says. An account is there for one thing, which is to keep a search so that you can come back to it later, on this device or on another.

`[SOLICITOR]` Four things in this section rest on this draft's reading of the rules, and nobody qualified has made any of them. Each is marked where it stands, and the list of risks sets out the doubt. That a search which is kept in an account needs no special condition: README.md, risk 18. That the cookie which keeps you signed in needs no permission: README.md, risk 19. That the lawful basis for an account is contract: README.md, risk 20. And what is owed to a person whose deleted account is still in a copy of the disk, or who cannot sign in to delete it: README.md, risk 21.

### What an account is, and how you sign in

| | |
|---|---|
| What Burro asks for | Your email address, and nothing else. Burro does not ask for your name, and there is no password to choose or to remember |
| How you sign in | You type your email address, and Burro sends you an email with a link in it. When you open the link, the page shows the address it is about to sign you in with and asks you to confirm. This means that you are never signed in without seeing who as |
| How long the link works | For 15 minutes, and only once. If you ask for another link and use it, the earlier one stops working |
| If you open the link in another browser | The page tells you that the link was asked for in a different browser, shows you the address again, and asks you to confirm a second time. Burro does this because a link that somebody else sent you would sign you in to their account, where they could read whatever you kept |
| The first time you sign in | Burro asks you to confirm that you are 18 or over, and then makes your account. Section 16 |
| If you ask for a link and do not use it | No account is made. Burro keeps the email address you typed with the record of that link, so that it can count how many links an address has been sent, and deletes both once a day has passed, as "When Burro deletes what is too old" says below. `[FOUNDER: a day is what is built. It is a first guess, and yours to set]` The company that sends the email keeps its own record of it, as "Who else receives it" says below |
| If you get an email that you did not ask for | Somebody typed your address. You can ignore the email, because nothing happens unless the link is used, and the link stops working after 15 minutes. Typing your address lets nobody into your account |
| If you can no longer read that email address | You cannot sign in, because the email is the only way in. `[FOUNDER: what Burro does for a person who writes to say so. An email cannot show whose an account is, so an account that is deleted because an email asked could be somebody else's. It is the fourth of the readings at the start of this section]` |

### The two cookies

A cookie is a short piece of text that a website asks your browser to keep, and to send back with later requests. Burro sets none until you ask for a link to sign in. It then sets two, and it uses neither to follow you or to count visits.

| Cookie | What it is for | How long it lasts |
|---|---|---|
| `__Host-burro_link` | It remembers which browser asked for the link, so that Burro can tell you when a link is opened somewhere else | 15 minutes, which is as long as the link works |
| `__Host-burro_session` | It keeps you signed in, so that you are not sent a new email each time you open a page | 30 days from when you last used Burro, and never more than 90 days from when you signed in. It stops working at once when you sign out |

Each holds a random value that says nothing about you. No script on a page can read either, and your browser sends them to Burro's website and to nobody else. Section 11 says why Burro asks no permission for them, and that this is a reading of the rules and not advice. It is the second of the readings at the start of this section.

### What Burro keeps in your account

| What | What it holds | Why | How long |
|---|---|---|---|
| Your email address | The address, written in small letters | To send you the link, and to know which account is yours | Until you delete your account. `[FOUNDER: whether an account that nobody has signed in to for a time is deleted, and after how long. Without such a limit an account is kept for as long as Burro runs. With one, a person who comes back after a long while finds that their searches are gone. It also matters for another reason: companies that give out email addresses give some of them out again, and whoever is given an address that has an account can sign in to it]` |
| That you confirmed you are 18 or over | The time at which you did | So that Burro can show that it asked | With your account |
| A search that you keep | The settings of the search, which set of data it was made on, and a short description that Burro writes from the settings. You can keep up to 100 | Because you pressed to keep it | Until you take it away, or delete your account. `[FOUNDER: or a period, after which a search that was kept is let go]` |
| Your last ten searches | The same, for each | `[FOUNDER: choose one, and delete the other. Either: "Burro keeps these only once you turn this on in your account, and deletes them if you turn it off again." That is how Burro is built to run unless it is set otherwise. Or: "Burro keeps these from the moment you sign in, so that you can find a search again without having pressed to keep it. You can turn this off in your account, and Burro then deletes them."]` | Until an eleventh takes the place of the oldest, or you turn this off, or you delete your account |
| Your preferences | Whether Burro keeps your last searches | To do as you chose | With your account |
| Where you are signed in | For each browser: when you signed in, the day you last used it, when it will end, and which kind of browser it is, such as Firefox or Safari. Not your internet address | So that you can see where you are signed in, and sign out of a browser that you no longer use | For 30 days after the sign-in has ended or you have signed out of it, and then until Burro next deletes what is too old. `[FOUNDER: 30 days is what is built. It is a first guess, and yours to set]` |
| The links you asked for | For each: when you asked, when it ends, and whether it was used. Not the link itself. Burro keeps a scrambled form of it, which cannot be turned back into the link | So that a link works only once, and so that no address is sent more than three links in a quarter of an hour or ten in a day | For a day after you asked for it, and then until Burro next deletes what is too old. `[FOUNDER: a day is what is built. It is a first guess, and yours to set]` |
| What has happened to your account | A list of three kinds of event, each with the time: that a link was used to sign in, that somebody signed in, and that a sign-in was ended. A link that was asked for, or that was turned away, is not in the list | So that you can see whether somebody else has signed in to your account | For 90 days, and then until Burro next deletes what is too old. Burro keeps the newest 200 at the most. `[FOUNDER: both are what is built. Each is a first guess, and yours to set]` |

**When Burro deletes what is too old.** Burro does not delete by the clock. It deletes what is too old each time somebody asks for a link or signs in, each day that somebody who is signed in comes back to Burro, and each time the service starts. This means that each period in the table is the shortest time for which a thing is kept. On a day when nobody does any of these, what is too old is kept until somebody does. `[FOUNDER: that is what is built. To hold each period to the day takes a step that runs by the clock, which is not built, and is yours to choose. While accounts are turned off the file is not opened, so nothing is deleted by its age until they are turned on again]`

### What Burro does not keep, even in an account

| | |
|---|---|
| What you typed | A search that is kept holds what Burro understood, which is the settings. It never holds the words you typed to make them. Section 3 |
| A name or a note of your own | You cannot give a kept search a name. Burro writes its description from the settings, because a name that you typed would be your words, kept |
| The ranking | Burro works the ranking out again each time you open a kept search, on the data it holds that day. So what you see may differ from what you saw when you kept it, and the page says so where the data has changed |
| Your internet address | Burro counts how often a link is asked for from one internet address, so that nobody can make it send a great deal of email. The count is held in the memory of the service, in a scrambled form, and is written nowhere. It is gone a quarter of an hour after you last asked, and whenever the service restarts |

### What a kept search can say about you

A search holds the places you need to reach and what matters to you. This means that it can say where you work, where your child goes to school, or that you want to live near a place of worship or a hospital. Without an account those settings belong to nobody, because nothing says whose they are. In an account they are kept beside your email address. Please keep a search only if you are content for Burro to hold that.

`[SOLICITOR]` This draft treats a kept search as a wish about a place and not as a fact about a person's health or religion, as section 11 does for any setting. It is the first of the readings at the start of this section, and the doubt is greater for a search that is kept in an account than for one that belongs to nobody.

### Who else receives it

| Company | What it receives | What it keeps |
|---|---|---|
| `[FOUNDER: the company that sends email]` | Your email address, and the email, which holds the link | `[FOUNDER: what it keeps of an email, and for how long]` `[SETTING: it sends the link as Burro wrote it, and does not put an address of its own in its place to count who pressed it]` |
| Vercel, which serves the website | What you send for your account passes through it on its way to the service: your email address when you ask for a link, the code of the link when you confirm it, the two cookies, and the settings of a search that you keep | Its log of a request holds the address of what was asked for, your internet address and the time. It holds nothing that you sent, because none of it is ever part of an address. Section 9 says how long that log is kept |
| Fly.io, which runs the service | The same. It also holds the file that your account is kept in | The file is kept in London, on a disk that the company encrypts. `[SETTING]` The company makes a copy of the disk each day and keeps each copy for 5 days. `[SETTING]` `[FOUNDER: from 1 day to 60. A longer time means that an account you have deleted is held for longer in a copy. A shorter time leaves fewer days in which a fault can be noticed and the file put back]` |

Nobody else receives anything of an account. Burro sends you no email but the one that holds your link: no news, and nothing that sells. `[FOUNDER: if Burro is ever to write to the address of an account about the account itself, as it would if accounts were withdrawn or an account that nobody uses were about to be deleted, say so here first. Nothing that sends such an email is built]`

### How to see what Burro holds, take a copy, or delete it

You do each of these yourself, on the page of your account, while you are signed in. You do not need to write to Burro, and Burro will not do them because an email asks it to, since an email cannot show who sent it.

| To | What happens |
|---|---|
| See what is kept | The page of your account shows your email address, the searches you have kept, your last searches, and where you are signed in. What has happened to your account, and the links you asked for, are in the copy |
| Take a copy | You are given everything Burro holds in your account as one file, in JSON, which is a format that other programs read. It holds what the page shows, and with it what has happened to your account and the links you asked for |
| Take one search away | It is deleted at once |
| Sign out | The browser you are using is signed out, and the sign-in stops working at Burro as well. You can also sign out of one other browser, or of all of them at once |
| Delete your account | If you signed in more than ten minutes ago Burro asks you to sign in again first, so that nobody can delete your account from a browser that you left signed in. Your email address, every search, your preferences, every sign-in, the record of what happened and the record of each link that was asked for your address are then deleted together |

**What deleting cannot do at once.** The company that runs the service keeps its daily copies of the disk for 5 days. `[SETTING]` So an account that you delete is still held in those copies until the last copy that holds it is let go. Burro uses a copy for one thing, which is to put the file back after a failure. `[FOUNDER: if a copy is ever put back, every account that was deleted after that copy was made is back in the file, and nothing in the file says which they were. Decide what is done then, and say it here. It is the fourth of the readings at the start of this section.]` The company that sends email keeps its own record of the emails it sent you. `[FOUNDER: for how long]`

The ICO says of copies like these: "The key issue is to put the backup data 'beyond use', even if it cannot be immediately overwritten", and "You must be absolutely clear with individuals as to what will happen to their data when their erasure request is fulfilled, including in respect of backup systems." Read on 26 September 2026, at <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/>.

### If you share a computer

While a browser is signed in, anybody who uses that browser can open your account and see the searches you have kept, which may say where you work and where you hope to live. If other people use the computer, sign out when you have finished. If you think you left a browser signed in somewhere, sign in on another device and sign out of all of them from there.

---

The notice ends here.

---

## Appendix A: what the ICO asks for, and where it is

The list is from "What privacy information should we provide?", read on 23 September 2026. Every item applies to data collected from the person unless the last column says otherwise.

| The ICO's item | Section | Note |
|---|---|---|
| Name and contact details of your organisation | 1 | Blank |
| Name and contact details of your representative | | Does not apply. A representative is for an organisation outside the UK. Not read at a source |
| Contact details of your data protection officer | 1 | None appointed. Whether one is required was not read |
| Purposes of the processing | 3 to 10 | |
| Lawful basis for the processing | 11 | |
| Legitimate interests for the processing | 11 | |
| Recipients or categories of recipients | 4, 9, 10 | The four companies that can run a model are named. Which is in use is said in the notice the service serves, on the page of methods |
| Details of transfers to third countries | 4, 13 | For a company that runs a model, in that notice |
| Retention periods | 12 | For a company that runs a model, in that notice. `[SOLICITOR]` Section 4 says why |
| Rights available to individuals | 14 | |
| Right to withdraw consent | 11, 14 | |
| Right to lodge a complaint with a supervisory authority | 15 | |
| Details of statutory or contractual obligation to provide data | | Does not apply. Nobody has to give Burro anything |
| Details of automated decision-making, including profiling | 17 | |
| Categories of personal data obtained | | Applies only to data from other sources. Burro gets none |
| Source of the personal data | | The same |

The ICO also says a person must be told they can complain to the organisation as well as to the ICO, "at the point you collect their personal information (eg by displaying this in your privacy notice)". Section 15. Source: <https://ico.org.uk/for-organisations/how-to-deal-with-data-protection-complaints/how-do-we-prepare-to-handle-data-protection-complaints/>. Read.

It says privacy information must be given "at the time when personal data are obtained", and that posting it on a website is not enough by itself. So the box where a person types needs a link to this notice beside it. It has none since 26 September 2026, when the founder asked for what stood beside the box to go: the foot of every page leads to how words are handled, and nothing beside the box does. Source: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/the-right-to-be-informed/when-should-we-provide-privacy-information/>. Read.

**For an account**, section 20 answers the same list again, with sections 9, 11, 12 and 13: who receives what, why, for how long, and where it goes. One item of the list changes. An email address is needed to make an account, because the account is kept by it. Nobody has to make an account, and nothing that can be done without one asks for one. And the page where a person asks for a link to sign in needs a link to this notice beside it, as the box where a person types does.

## Appendix B: what each claim rests on

Read in the repository on 23 September 2026, twice, and again on 24 September 2026, against `services/api/` and `apps/web/` as they then stood. Check each row again before publishing. Every file and every test named below is in the repository under that name, as of 24 September 2026. "A test" below means the test was found and read, not that it proves the sentence beside it.

The last column says how the claim is held.

| Mark | Meaning |
|---|---|
| Code and test | The code makes it true and a named test would fail if it stopped |
| Code | The code makes it true. No test that holds it was found |
| Setting | It is true only while a setting holds |
| Not true yet | The code does not make it true |

| Claim | Section | Where it is kept true | Held by |
|---|---|---|---|
| What is typed is never logged or stored | 3 | `services/api/src/burro_api/logs.py`, `LOGGABLE`: a line can hold only a field on the list, and no message is formatted. `services/api/tests/test_privacy.py`, `test_a_prompt_is_read_and_appears_nowhere_afterwards`, which plants a marker and looks for it in every log line, record and response. [contract.md](../design/contract.md), section 10 | Code and test |
| A failure does not log what was typed | 3, 8 | `log_failure` in `logs.py` writes a type and frames, never a message. `test_interpret_timeout_does_not_log_the_prompt`, `test_unhandled_error_logs_the_type_and_not_the_message`, `test_a_library_that_logs_what_it_was_given_is_cut_down_to_where_it_came_from` | Code and test |
| Typed text travels only in the body of a request | 3 | `services/api/tests/test_contract.py`, `test_no_route_takes_typed_text_in_a_path_or_query`. `apps/web/test/privacy/search.test.tsx`, `test_typed_text_travels_only_in_a_post_body` and `test_the_prompt_form_cannot_be_sent_as_a_get` | Code and test |
| What is typed into a search does not pass through the website's host | 3, 9 | `apps/web/src/lib/api/config.ts`: the browser calls the service itself. `apps/web/test/privacy/source.test.ts`, `test_the_website_has_one_handler_which_passes_accounts_on_and_no_action_or_middleware`: the one handler passes the routes of accounts on, and nothing while accounts are off. What is sent for an account does pass through it: section 20 | Code and test |
| The box that finds a place sends as you type, after 250 milliseconds, from 2 characters, 80 at most | 3 | `WAIT_MS` in `apps/web/src/components/PlaceCombobox/PlaceCombobox.tsx`. `PLACE_QUERY` in `apps/web/src/lib/search/flow.ts`. `PlaceSearchBody` in `services/api/src/burro_api/wire.py`. `test_place_search_text_never_reaches_a_log` | Code and test |
| Settings come back with positions and not words | 3 | `as_sent` in `services/api/src/burro_api/routes/interpret.py`. `test_the_words_an_edit_rests_on_are_returned_as_offsets_and_written_nowhere` | Code and test |
| Nothing is kept for a search | 6 | [ADR 0011](../adr/0011-nothing-is-kept-for-a-search.md). `services/api/src/burro_api/app.py`: one release in memory and no database | Code |
| No setting, and no hash of the settings, is logged | 6, 8 | `test_nothing_worked_out_from_a_spec_is_logged_or_kept`, `test_no_hash_of_a_spec_can_be_logged` | Code and test |
| The counts and codes in a sentence's log line depend on the words and the settings together | 6, 8 | `_record` in `routes/interpret.py`. `test_what_a_line_says_of_a_reading_is_counts_and_codes_and_nothing_of_the_spec`. ADR 0011, "Still to confirm" | Code and test. Whether to go on logging them is the founder's |
| Burro's log holds no internet address and no header | 2, 8 | `LOGGABLE` has no field for one. `test_what_a_browser_says_of_itself_is_neither_logged_nor_sent_back`. Contract, section 10.1 | Code and test |
| The log names the kind of request, never the web address asked for | 8 | `template_of` in `services/api/src/burro_api/boundary.py`. `access_log=False` in `cli.py`. `test_request_log_names_the_route_template_not_the_path` | Code and test |
| A log line and a call record hold the time to the second | 8 | `_at` in `logs.py`. `at` in `CallRecord`, `services/api/src/burro_api/calls.py` | Code |
| A call record can say that a request asked about who lives somewhere | 8, 11 | `POLICY_REDIRECT` in `CallStatus`, `services/api/src/burro_api/calls.py`. `interpret_status` and `call_status` in `LOGGABLE` | Code |
| "How it went" is one of eight codes | 8 | `CallStatus` in `calls.py` | Code |
| A line and a call record name the company whose model was asked, from a closed list | 8 | `provider` in `LOGGABLE` and in `CallRecord`. `PROVIDER_PATTERN` in `calls.py` | Code |
| The line that says a company is not used holds two fixed words and nothing that was set | 8 | `_warn` in `services/api/src/burro_api/providers/choose.py`. `test_why_is_a_fixed_word_and_never_a_thing_that_was_set`, `test_a_key_set_where_another_setting_belongs_is_in_no_line` | Code and test |
| The service sets no cookie | 2 | `services/api/tests/test_routes.py`, `test_no_answer_allows_every_origin_or_asks_for_a_cookie`. The browser sends none: `credentials: "omit"` in `apps/web/src/lib/api/send.ts` | Code and test |
| A shared link holds settings and not words, and nothing about who made it | 7 | `services/api/src/burro_api/stores.py`, `StoredShare`. `services/api/src/burro_api/routes/shares.py`. `apps/web/test/privacy/share.test.tsx`, `test_a_share_is_made_of_the_spec_the_api_returned_and_never_of_the_words` | Code and test |
| The id of a link is random and not made from the settings | 7 | `test_share_id_is_not_derived_from_the_spec` | Code and test |
| Places in a link are replaced unless the sender asks | 7 | `coarsen` in `routes/shares.py`. `test_share_coarsens_destinations_unless_asked_not_to`. `test_the_exact_places_are_shared_only_when_the_box_is_ticked` | Code and test |
| Links are held in memory, 50,000 at most | 7 | `stores.py`, `KEEP_AT_MOST` | Code |
| Opening a link does not show the time it was made | 14 | `ShareData` in `wire.py` has no field for it. `StoredShare` has `created_at` | Code |
| There is no way to delete one link | 7, 14 | The service has two routes for links, to make one and to open one. `ShareStore` in `stores.py` has `put` and `get` only. Contract, section 9.2 | Not true yet |
| Call records last 30 days at most, 10,000 at most | 8, 12 | `services/api/src/burro_api/calls.py`, `KEEP_DAYS` and `KEEP_AT_MOST` | Code |
| A model is sent the words alone, unless the service is set to send the settings | 4, 6 | `_user` in `services/api/src/burro_api/reader.py`. `test_the_model_is_sent_the_words_alone_unless_the_settings_are_asked_for`. `test_the_settings_are_sent_only_where_the_service_is_set_to_send_them` | Code and test. Which is set is a setting |
| Where the settings are sent, each place to reach is replaced by its position | 4 | `_user` in `reader.py`. `test_where_the_settings_are_sent_the_spec_goes_without_its_places`, `test_the_model_is_never_sent_anything_about_a_place` | Code and test |
| Where the settings are sent, any area ruled in or out goes by its id | 4 | `_user` takes out `place_id` from each journey and nothing else. `areas` in `PreferenceSpec`, `packages/core/src/burro_core/spec.py` | Code |
| A key alone turns nothing on | 4 | `_decided` in `choose.py`. `test_a_key_alone_turns_nothing_on`, in `services/api/tests/providers/test_choose.py` and in `services/api/tests/test_app.py` | Code and test |
| A company is used only when it is named, holds a key, has its terms accepted by name and has been checked by a person | 4 | `_decided` in `choose.py`. `test_a_provider_reads_only_when_it_is_named_has_a_key_and_its_terms_are_accepted`, `test_a_provider_with_one_sentence_that_nobody_has_checked_is_not_turned_on` | Code and test |
| As the table stands no company can be turned on | 4 | `checked_by` and `checked_on` in `services/api/src/burro_api/providers/terms.py` are empty for all four. `test_as_the_table_stands_no_provider_reads_because_no_person_has_checked_its_terms` | Code and test |
| What people are told and who reads cannot differ | 4 | `Choice` in `choose.py`. `test_a_choice_cannot_tell_people_of_one_provider_while_another_reads`, `test_a_choice_cannot_hold_a_model_and_tell_people_that_none_reads` | Code and test |
| DeepSeek is never used for what real people type | 4 | [ADR 0019](../adr/0019-no-one-provider-and-a-key-alone-turns-nothing-on.md). `choose.py` holds all four alike and knows nothing of the release | Not true yet. A setting holds it |
| Burro uses no company's own software | 4 | `test_the_service_depends_on_no_providers_library`, `test_nothing_in_the_service_imports_a_providers_library` | Code and test |
| After three refusals a company is asked nothing for five minutes | 4 | `PATIENCE` and `REST_S` in `services/api/src/burro_api/providers/base.py` | Code |
| The notice is the service's own, and the website has no words for it. It stood beside the box until 26 September 2026, and stands on the page of methods | 3, 4 | `reader` in `MetaData`, `services/api/src/burro_api/wire.py`. `test_the_website_has_no_words_of_its_own_for_the_notice`, `test_no_providers_name_or_terms_is_written_in_the_websites_own_source`, `test_site_copy_names_no_provider_and_states_none_of_its_terms` | Code and test |
| No sentence is sent until the service has said who reads | 3, 4 | `test_a_sentence_sent_before_the_service_has_said_who_reads_waits_until_it_has`, `test_the_page_asks_the_service_who_reads_and_takes_nothing_from_what_it_was_built_on` | Code and test |
| The service applies nothing of words that are not a plain list, and returns what it read of them as offers | 3 | `test_a_prompt_that_is_not_plain_applies_nothing_and_offers_what_was_noticed`, which is of the service. Since 26 September 2026 the website takes the offers without asking: [ADR 0012](../adr/0012-a-closed-vocabulary-and-a-guard-on-the-model.md), as amended | Code and test, of the service |
| What a model reads is checked by Burro's code before it is applied, and is applied without asking | 3, 4 | [ADR 0012](../adr/0012-a-closed-vocabulary-and-a-guard-on-the-model.md), as amended on 26 September 2026. The checks are the service's, and the contract, section 8.2, lists them. Until that day this row said that nothing a model reads is applied until the person chooses it | Code, of the checks. The founder's, of what the notice may say |
| If a model is slow or fails, the rules answer | 4 | `answer` in `routes/interpret.py`. `test_interpret_timeout_does_not_log_the_prompt` | Code and test |
| Burro waits 6 seconds for a model | 4, 12 | `DEFAULT_TIMEOUT_S` in `services/api/src/burro_api/settings.py`. `BURRO_MODEL_TIMEOUT_S` may set up to 60 | Setting |
| A late call is not waited for, and is given up at the same limit | 4, 12 | `within` in `routes/interpret.py` stops waiting. `over_https` in `providers/base.py` gives the whole call one deadline, which is the same number of seconds. `test_an_interpreter_that_is_too_slow_is_not_waited_for` | Code and test |
| The longest sentence is 600 characters | 3 | `MAX_TEXT` in `packages/core/src/burro_core/interpret.py` | Code |
| No cookie and no browser storage | 2 | `apps/web/eslint.config.mjs`. `test_nothing_is_ever_written_to_browser_storage`. `test_nothing_in_the_source_touches_storage_the_console_or_the_address` | Code and test |
| Nothing from another origin | 2 | `contentSecurityPolicy` in `apps/web/src/lib/headers.ts`. `test_nothing_is_loaded_from_another_origin`. The map has no basemap and asks no host for anything: `apps/web/src/lib/map/style.ts` | Code and test |
| No analytics | 2 | Nothing in the website's source sends any. The host's own analytics is a setting at the host, and its script would come from the website's own origin: [deploy/web/README.md](../../deploy/web/README.md) | Setting |
| Location, camera and microphone are refused. No referrer is sent | 2 | `securityHeaders` in `apps/web/src/lib/headers.ts` | Code |
| The id of a link is never sent to the website's host | 9 | `apps/web/src/lib/paths.ts`: the id goes after the `#`. `test_a_share_id_is_only_ever_in_the_fragment` | Code and test |
| The website's host sees which area pages and comparisons are opened | 9 | `paths.area` and `paths.compare` in `apps/web/src/lib/paths.ts` | Code |
| The website's host sees which drawings a page asks for, and so which kinds of thing a search holds | 9 | A drawing is asked for by its name: `pictureOf` in `apps/web/src/components/kit/drawings.ts`. [ADR 0033](../adr/0033-the-website-looks-like-the-map-of-a-gentle-game.md), under its consequences | Code |
| There is no step that asks before a sentence is sent | 5, 11 | No such step was found in `apps/web/src` or `services/api/src`. `apps/web/src/components/PromptBox/PromptBox.tsx` showed a line under the box until 26 September 2026, and shows none | Not true yet |
| The website's own words name no company and no period | 4 | `test_site_copy_names_no_provider_and_states_none_of_its_terms`. The line that stood under the box until 26 September 2026 was one of them | Code and test |
| A request about who lives somewhere that is found makes no setting | 5 | [ADR 0006](../adr/0006-rank-places-not-residents.md). Contract, section 8.4. `packages/core/tests/test_interpret.py`, `test_a_request_about_who_lives_somewhere_makes_no_edit_at_all`. `services/api/tests/test_reader.py`, `test_a_request_about_who_lives_somewhere_is_redirected_whoever_notices` | Code and test |
| Burro has no setting about who lives somewhere | 5, 18 | `packages/core/tests/test_catalogue.py`, `test_no_feature_or_tag_describes_residents`. It is true of the code today. It stops being the rule once a measure of age or of households is built, and the test changes in that change | Code and test |
| A request about who lives somewhere can be missed | 5 | Contract, sections 8.2, 8.4 and 13. `services/api/tests/test_reader_kept.py` | Not true yet, and named as such |
| A wish for a community is met through what is there | 5 | [ADR 0006](../adr/0006-rank-places-not-residents.md). Today the request is counted under the code `community_amenities`, as a thing Burro cannot answer | Not true yet |
| The age of residents and what households are made of may count in a ranking | 18 | [ADR 0006](../adr/0006-rank-places-not-residents.md), as amended on 24 September 2026. No release holds a measure of either | Not true yet |
| Census figures of country of birth, ethnic group and religion are shown on an area's page and never ranked on | 18 | [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md). No file of `apps/web/src`, `services/api/src` or `packages/core/src` draws or serves a census table | Not true yet |
| Stop and search records are never read | 18 | The condition on `police-uk-street-level-crime` in `registry/sources/safety.toml`. No step reads the police file | A rule of the registry. No test |
| Stop and search records are never held | 18 | Nothing in the repository. It is true only where no copy of a police file that holds them is kept | Not true yet. It is the founder's to do |
| No release of a real place holds a count of residents or a vibe that counts recorded crime | 18 | `test_the_release_holds_no_count_of_residents`. The rule `gritty_b_is_synthetic` in `packages/core/src/burro_core/release.py` | Code and test. Both change when what was decided is built |
| No limit on requests | | `admit` in `app.py` is empty | Not true yet. The terms ask, and nothing enforces |

### For accounts

Read on 26 September 2026 in the code of accounts. Each test is named as it stood that day, under `services/api/tests/accounts/` and `apps/web/`: [the design of accounts](../design/accounts.md), section 12, says where each is. Check each row again before accounts are turned on.

| Claim | Section | What holds it | How |
|---|---|---|---|
| With accounts off Burro asks for no email address, sets no cookie and opens no file | 2, 20 | `BURRO_ACCOUNTS` at the service and `NEXT_PUBLIC_BURRO_ACCOUNTS` at the website. `test_with_accounts_off_no_route_of_accounts_exists`, `test_with_accounts_off_no_file_is_opened_and_nothing_of_them_is_made`, `test_nothing_is_passed_on_and_the_answer_is_that_there_is_nothing_at_the_address` | Code and test, while the two settings hold |
| A search knows nobody, with accounts on as with them off | 6, 20 | `test_a_search_knows_nobody_with_accounts_on_as_with_them_off` | Code and test |
| What is kept of a search is the settings, and no word that was typed | 6, 20 | `test_what_is_kept_holds_no_word_that_anybody_typed`, `test_a_search_is_checked_by_the_schema_the_ranking_uses_before_it_is_kept`, `test_what_is_kept_is_what_burro_understood_and_no_word_that_was_typed` | Code and test |
| The name of a search that is kept is worked out by Burro | 20 | `accounts/names.py`. `test_a_search_is_kept_as_what_burro_understood_and_named_from_it` | Code and test |
| The last searches are kept only once a person turns it on | 20 | `KEEP_RECENT` in `accounts/settings.py`, and `BURRO_ACCOUNTS_KEEP_RECENT`. `test_the_last_searches_are_kept_only_once_a_person_turns_it_on`, `test_nothing_of_a_search_is_sent_where_the_person_does_not_let_burro_keep_them`, `test_turning_it_off_takes_away_what_was_kept` | Code and test, while the setting holds. Which way it is set is the founder's to decide |
| A link works once, for 15 minutes | 20 | `test_a_link_works_once`, `test_a_link_ends_after_a_quarter_of_an_hour` | Code and test |
| The page a link opens says whose link it is, and signs nobody in until the button is pressed | 20 | `test_the_page_says_whose_link_it_is_and_signs_nobody_in_until_the_button_is_pressed`, `test_nothing_but_a_press_sends_the_token_to_sign_in`, `test_a_link_opened_in_another_browser_is_not_taken_without_being_asked` | Code and test |
| Burro keeps the hash of a link and of a sign-in, and never either | 20 | `test_what_is_kept_of_a_link_is_the_hash_of_its_token_and_never_the_token`, `test_signing_in_gives_the_session_and_takes_back_what_bound_the_link` | Code and test |
| The two cookies cannot be read by a script, and are sent to Burro alone | 2, 20 | `test_asking_binds_the_link_to_the_browser_that_asked`, `test_signing_in_gives_the_session_and_takes_back_what_bound_the_link`, `test_no_browser_is_let_send_a_cookie_or_the_header_of_a_page_across_origins` | Code and test. That they are used for nothing else is the code's, and no test can hold what a thing is not used for |
| What the website itself says of what a browser keeps is true with accounts on as with them off | 2, 20 | `KEPT_WITH_ACCOUNTS` in `apps/web/src/content/account.ts`. `test_where_nobody_can_sign_in_the_page_says_nothing_of_a_cookie_or_of_signing_in`, `test_where_a_person_can_sign_in_the_page_says_what_the_browser_and_burro_then_keep` | Code and test. Which of the two lines is said is chosen as the website is built, by the setting that turns accounts on |
| Asking for a link is answered the same whether or not the address has an account | 20 | `test_a_known_address_and_an_unknown_one_are_answered_the_same`, `test_a_known_address_and_an_unknown_one_are_answered_in_like_time` | Code and test |
| The email is plain text, and the company that sends it is asked not to record who opened it or pressed its link | 10, 20 | `test_the_letter_is_plain_text_and_the_same_for_everybody`, `test_a_letter_is_not_followed_and_is_not_opened_for_the_sender` | Code and test for one of the two companies that are fitted. For the other it is a setting at the company, and no test |
| Your internet address is counted under a key, in memory, and is written nowhere | 8, 20 | `test_what_is_held_of_a_client_is_a_hash_under_a_key_and_never_the_address`, `test_no_line_holds_an_address_a_token_a_session_an_account_a_client_or_a_spec` | Code and test |
| What is kept of a browser is which of five kinds it is | 20 | `test_what_is_kept_of_a_browser_is_its_family_and_nothing_else`, `test_what_a_browser_says_it_is_is_written_nowhere` | Code and test |
| No record of a call holds anything of an account | 8, 20 | `test_no_line_holds_an_address_a_token_a_session_an_account_a_client_or_a_spec`, `test_the_log_gained_two_fields_and_each_is_a_word_of_a_closed_list` | Code and test |
| Nobody is shown anything of an account but the person who is signed in to it | 20 | `test_no_route_ever_returns_a_row_of_another_account`, `test_whose_rows_are_read_is_never_decided_by_what_a_request_says` | Code and test |
| The copy holds everything Burro holds of an account | 14, 20 | `test_every_row_the_file_holds_of_an_account_is_in_what_the_person_is_given` | Code and test |
| Deleting an account takes everything of it, at once, and what is deleted is written over in the file | 12, 14, 20 | `test_an_account_is_deleted_with_everything_of_it_in_the_file_and_beside_it`, `test_what_is_deleted_is_gone_from_the_file_and_not_only_from_the_tables` | Code and test. A daily copy of the disk holds it until the copy is let go: a setting of the host |
| Deleting asks for a sign-in in the last ten minutes | 20 | `test_deleting_asks_for_a_sign_in_in_the_last_ten_minutes` | Code and test |
| A sign-in ends after 30 days unused, and after 90 whatever is done | 12, 20 | `test_a_session_lasts_thirty_days`, `test_a_session_never_lasts_past_ninety_days_from_when_it_was_made` | Code and test. The periods are the founder's to decide |
| A link is let go of after a day, a sign-in that ended after 30 days, and what happened to an account after 90, each the next time anybody asks for a link, signs in or comes back signed in, or the service starts | 12, 20 | `test_a_link_is_let_go_of_after_a_day_whoever_asked_for_it`, `test_sessions_that_ended_long_ago_are_let_go_of_as_a_person_signs_in`, `test_what_happened_to_an_account_is_cut_to_so_many_and_let_go_of_by_its_age`, `test_an_address_that_never_signed_in_goes_as_somebody_who_is_signed_in_comes_back`, `test_a_session_that_ended_long_ago_is_let_go_of_as_somebody_else_comes_back`, `test_what_happened_long_ago_is_let_go_of_as_somebody_else_comes_back`, `test_what_is_too_old_of_every_kind_is_let_go_of_as_the_service_starts` | Code and test. Nothing runs by the clock, so each period is the least and not the most. The periods are the founder's to decide |
| An account is made only once a person has said that they are 18 or over | 16, 20 | `test_the_first_sign_in_makes_the_account_once_the_person_says_they_are_an_adult`, `test_no_account_is_made_until_the_person_has_said_so` | Code and test. Nothing checks that it is so |
| The file is encrypted where it is kept, and a daily copy of it is kept for 5 days | 12, 20 | Settings of the host. [deploy/README.md](../../deploy/README.md#turning-accounts-on) has what the host's pages said | Not checked. No volume has been made |
| An account that is not used is deleted after a time | 12, 20 | Nothing | Not built. The period is the founder's to decide |

## Appendix C: what this notice says of the law

Nothing in this notice is advice. Each sentence that says what the law is rests on one of these, or is marked as a reading.

| Sentence | Section | What it rests on | Read |
|---|---|---|---|
| Burro is a controller | 1 | The ICO's word. No page that defines it was read for this draft | Not read |
| Some data is special category data | 5 | The ICO's list, quoted in section 5 | Read |
| A lawful basis is needed, and a condition for special category data | 11 | The ICO's two pages, quoted in section 11 | Read |
| Which lawful basis and which condition fit each use | 11 | This draft's proposal. README.md, risk 1 | A reading |
| That no condition is needed for settings, links or an internet address | 11 | This draft's reading. It now says "none claimed" | A reading |
| Sending data to a company outside the UK needs a safeguard | 13 | The ICO's guide to international transfers | Read |
| That each company's safeguard is enough | 4, 13 | This draft's reading. The Data Privacy Framework list was not opened, and no risk assessment is written | A reading |
| The list of rights | 14 | The ICO's list | Read |
| One month to answer, two more if complex, no fee in most cases | 14 | The ICO's page on answering a request | Read |
| Burro need not find a person it cannot identify | 14 | Article 11 of the UK GDPR. Whether it covers Burro is a reading. README.md, risk 8 | Read. The reading is not |
| A complaint is acknowledged within 30 days | 15 | The ICO's page on complaints, updated 8 May 2026 | Read |
| No data protection officer is needed | 1 | Nothing. The ICO's page on it was not read. The notice says only that none is appointed | Not read |
| No representative is needed | Appendix A | Nothing | Not read |
| No cookie banner is needed | 2 | Nothing. The notice does not say so. README.md, risk 16 | Not read |
| 18 or over | 16 | Google's terms, and the ICO's children's code. The checklist, task 14 | Read. The choice is the founder's |
| A share for an area of several thousand people is not personal data | 18 | The ICO's pages on personal data and on anonymous information. [The reading](residents-crime-and-equality.md), section 4 | Read twice. The reading is not |
| A setting about a place of worship is not special category data | 5, 11 | The ICO's page "What is special category data?", on inferences | Read twice. The reading is not |
| The lawful basis for an account is contract | 11, 20 | The ICO's page on contract as a lawful basis, quoted in section 11. Whether using a free website makes such an agreement is a reading. README.md, risk 20 | Read on 26 September 2026. The reading is not |
| The two cookies of an account need no permission | 11, 20 | The ICO's guidance on storage and access technologies, under "What are the exceptions?", quoted in section 11. README.md, risk 19 | Read on 26 September 2026. The reading is not |
| A search that is kept in an account needs no special condition | 11, 20 | The ICO's page "What is special category data?", on inferences, as for any setting. README.md, risk 18 | Read twice, for the draft of 24 September 2026. The reading is not |
| A copy of an account is given in a form that other programs read | 14, 20 | The ICO's page on the right to data portability, which speaks of "a structured, commonly used and machine readable format", and says the right applies where the lawful basis is "consent or for the performance of a contract" | Read on 26 September 2026 |
| An account that was deleted, and is still in a daily copy of the disk, is put beyond use | 20 | The ICO's page on the right to erasure, quoted in section 20. That a copy which is kept for 5 days, and used only after a failure, is "beyond use" is a reading. README.md, risk 21 | Read on 26 September 2026. The reading is not |
| Nothing is kept for longer than it is needed | 12, 20 | The ICO's page on storage limitation: "You must not keep personal data for longer than you need it", and "The UK GDPR does not set specific time limits for different types of data." The periods are the founder's to set | Read on 26 September 2026 |
| What is so before a person chooses anything must guard their privacy | 20 | The ICO's page on data protection by design and by default: "Ensure any default settings offer strong privacy protections." It bears on whether a person's last searches are kept from the moment they sign in | Read on 26 September 2026 |
| Nobody may use Burro to choose between people | 17 | Sections 13, 29, 33, 111 and 112 of the Equality Act 2010, as printed. The equality regulator's guidance was not read | Read twice. The reading is not |
| That naming four companies and pointing to the notice the service serves is enough | 4 | Nothing. The ICO's list of what a notice holds was read, and does not say. The notice is no longer shown where a person types | A reading |
