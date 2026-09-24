# Privacy notice

**Draft. Not published. Not legal advice.** Written on 23 September 2026 from the public guidance of the Information Commissioner's Office (ICO) and from the code in this repository, and brought up to 24 September 2026. Nobody qualified has read it. [README.md](README.md) says how it was written, what was put right on the second day, and which sentences carry the most risk.

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

## Before this is published

| # | What is missing | Kind | Section |
|---|---|---|---|
| 1 | The legal name, the address and the contact for requests | Founder | 1 |
| 2 | Whether a language model reads what is typed at launch, and whose. If one does: its terms accepted in a name, and every sentence people are told of it checked by a person against the company's own page | Founder | 4 |
| 3 | A step that asks before a sentence is sent. The website shows the service's notice beside the box before anything is typed, and asks nothing | Not built | 5, 11 |
| 4 | The age limit | Founder | 16 |
| 5 | A way to delete one shared link. Today the only way is to restart the service, which deletes all of them | Not built | 7, 14 |
| 6 | A page for this notice on the website, with the service's notice shown in section 4 as it is served, and a link to the page beside the box where a person types | Not built | all |
| 7 | An agreement on data processing with Fly.io. None was found on a public page | Founder | 9 |
| 8 | Code that refuses DeepSeek on any release that is not made up. Until it exists, the sentence about DeepSeek in section 4 is held by a setting and by nothing else | Not built | 4 |
| 9 | Where email to Burro is received, and how long it is kept | Founder | 10 |
| 10 | The fee paid to the ICO, and the other steps of [data-protection-checklist.md](data-protection-checklist.md) | Founder | |
| 11 | The census table on an area's page, and the measures of age and of households. No page shows a table and no release holds a measure | Not built | 18 |
| 12 | A mailbox, and someone who answers within the times sections 14 and 15 promise | Founder | 14, 15 |
| 13 | Every row of "What is true only while a setting holds", set and checked at the host or the provider | Founder | 2, 4, 8, 9, 12 |
| 14 | That nothing a model reads is applied until the person chooses it. As the code stands a model's reading is applied in the narrow cases that [ADR 0012](../adr/0012-a-closed-vocabulary-and-a-guard-on-the-model.md) lists | Not built | 3, 4 |
| 15 | The equality regulator's guidance for service providers, read by a person. Section 18 rests on the Act as printed and not on the guidance | Founder | 17, 18 |
| 16 | No copy kept of a police file that holds records of stop and search. The police give recorded crime, outcomes and stop and search from one form, and a file saved whole holds all three | Founder | 18 |

## What is true only while a setting holds

The code was read against this notice on 23 September 2026, twice, and again on 24 September 2026. These sentences are not held by the code or by a test. Each is true only while someone keeps a setting as it is. None has been set, because nothing is deployed.

| Sentence | Section | The setting it rests on | Where the setting is written down |
|---|---|---|---|
| No language model reads what you type | 3, 4 | No provider is named in `BURRO_MODEL_PROVIDER`, or its terms are not accepted by name in `BURRO_MODEL_TERMS_ACCEPTED`. A key alone turns nothing on: that part is held by code and by a test | `choose` in `services/api/src/burro_api/providers/choose.py`. [ADR 0019](../adr/0019-no-one-provider-and-a-key-alone-turns-nothing-on.md) |
| Your words go alone | 4, 6 | `BURRO_MODEL_SENDS_SETTINGS` is not the one word `yes`. The notice beside the box says which is so, from the same setting | `choose.py`. [models.md](../design/models.md), section 6 |
| DeepSeek is never used for what real people type | 4 | `BURRO_MODEL_PROVIDER` is never `deepseek` on a service that real people use, and nobody accepts its terms for one. No code refuses it | [ADR 0019](../adr/0019-no-one-provider-and-a-key-alone-turns-nothing-on.md) |
| Burro waits 6 seconds for a model | 4, 12 | `BURRO_MODEL_TIMEOUT_S` is left unset. It may be set to anything up to 60 | `DEFAULT_TIMEOUT_S` and `model_timeout_s` in `settings.py` |
| There is no analytics | 2 | Web Analytics, Speed Insights and the toolbar are off at Vercel. Vercel serves its analytics script from the website's own address, so the website's own rules would not stop it | [deploy/web/README.md](../../deploy/web/README.md) |
| Requests for pages are logged for 1 day | 9, 12 | The Pro plan, with no log drain and no Observability Plus | [deploy/README.md](../../deploy/README.md) |
| Log lines are kept for 7 days, and only by Fly.io | 8, 9, 12 | No log shipper and no add-on that records paths | [deploy/README.md](../../deploy/README.md) |
| The service runs in London | 9, 13 | One machine, one region | `deploy/api/fly.toml` |
| Nobody but the host can read a request on its way | 9 | The domain's records point straight at the hosts, with no proxy in front | [deploy/README.md](../../deploy/README.md), step 1 |
| What a provider keeps, and that it does not train on it | 4 | Settings in the provider's own account. The checklist, task 15, lists them for each provider | [data-protection-checklist.md](data-protection-checklist.md) |

## The guidance this follows

| Page | Address | Its own notice, as read |
|---|---|---|
| What privacy information should we provide? | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/the-right-to-be-informed/what-privacy-information-should-we-provide/> | "Due to changes made by the Data (Use and Access) Act, this guidance is under review and may be subject to change." |
| How to write a privacy notice and what goes in it | <https://ico.org.uk/for-organisations/advice-for-small-organisations/privacy-notices-and-cookies/how-to-write-a-privacy-notice-and-what-goes-in-it/> | The same |
| How to deal with data protection complaints | <https://ico.org.uk/for-organisations/how-to-deal-with-data-protection-complaints/> | Updated 8 May 2026 |

The first page lists what a notice must hold. The sections below are in the order a person would ask. [Appendix A](#appendix-a-what-the-ico-asks-for-and-where-it-is) says where each item on the ICO's list is answered. [Appendix B](#appendix-b-what-each-claim-rests-on) says which file or test keeps each claim true.

---

The notice starts here.

---

# How Burro handles what you tell it

Last updated: `[FOUNDER: date of publication]`

## In short

| You may ask | Answer |
|---|---|
| Do I need an account? | No. There are none |
| Does Burro know who I am? | No. It asks for no name, no email address and no sign-in |
| What happens to what I type? | It is read and turned into search settings, or into offers that you choose from. Burro does not keep it and does not write it to a log |
| Does anyone else receive what I type? | The company that hosts Burro's service carries it to Burro, and can read it on the way. Section 9. If a language model reads your words, the company that runs the model receives them as well. The notice beside the box where you type says whether one does, which company, what is sent, how long it is kept and whether it is used to train a model. Section 4 says what never changes |
| Are there cookies, analytics or tracking? | No. Section 2 says what that rests on |
| What does Burro keep? | A shared link, if you make one. A record of each call, with no words in it. An email, if you send one |
| Who else is involved? | The two companies that host Burro. They receive your internet address, as any website's host does. The one that runs the service also receives each request, with what you typed in it. Section 9 |
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
| Ask who you are | There is no account, no sign-in and no form that asks for a name or an email address |
| Set a cookie, or read one | The website sets none. The service that answers searches sets none and reads none |
| Keep anything in your browser | Burro writes nothing to your browser's storage. A search lives in the page's memory and is gone when you close or reload the page. Your browser keeps its own history of the pages you open, as with any website. The address of an area's page, of a comparison and of a shared link you open is in it |
| Count visits | The website holds no analytics. `[SETTING: the company that serves the pages offers analytics, and Burro leaves it switched off]` |
| Load anything from another company | No script, font, image or style comes from anyone but Burro. The website tells your browser to refuse any that does |
| Ask for your location, camera or microphone | The website tells your browser to refuse all three |
| Tell other websites where you came from | When you follow a link to a source, your browser is told not to say which page you were on |
| Write your internet address in its own log | Burro's log has no field for it. The companies that host Burro do receive it. Section 9 |
| Build a profile of you | Nothing ties one search to the next |

## 3. What you type

You can search with the form alone. The form sends settings and no sentence.

If you type a sentence, this is what happens to it.

| Step | What happens |
|---|---|
| 1 | Before you type, the box shows a notice from Burro's service that says who else reads what you type. Nothing you type is sent until the service has said |
| 2 | When you press Search, your browser sends the sentence to Burro's service, inside the body of a request. It is never put in a web address. It does not pass through the company that serves the website's pages. It does pass through the company that hosts the service. Section 9 |
| 3 | Burro reads it. Where your words are a plain list of what you want, it turns them into settings: a budget, a journey, what matters to you. Where they are not, it applies none of them. It shows what it noticed, and you choose |
| 4 | Burro sends the settings and the offers back to your browser, with where in your sentence each one came from, as positions and not as words |
| 5 | Burro drops the sentence. It is not stored and not written to a log |

| Fact | Value |
|---|---|
| Longest sentence | 600 characters |
| Who reads it | Burro's own rules. A language model as well, if the notice beside the box says so |
| What a model may do | Propose. `[NOT BUILT: nothing a model reads is applied until you choose it. As the code stands, a model's reading is applied in the narrow cases that ADR 0012 lists, and is marked as a guess]` |
| What Burro keeps of it | Nothing |
| What Burro's log holds about the call | The time, counts and codes. No words, no place, no settings. Section 8 lists them |
| The box that finds a place by name | What you type there is sent as you type, a quarter of a second after the last key, once there are two characters. It is sent in the body of a request, 80 characters at most. It is used to find places and is not stored or logged. It is never sent to a language model |

## 4. If a language model reads your words

A language model is a computer program that reads text. Burro may use one to read your sentence. The model is run by another company, on that company's computers. That company receives your words.

Burro can use one of four companies, and which one it uses can change. So this section says what is true whichever is in use, and the notice beside the box says the rest.

### Where you are told

| | |
|---|---|
| Where | In the notice beside the box where you type, before you type anything |
| Who writes it | Burro's service. The website has no words of its own for it, and shows what the service sends each time the page is opened |
| What it says | Whether a language model reads your words. Which company runs it. Whether your search settings go with your words. Whether the company uses what it receives to train its models. How long it keeps it, and whether it keeps it longer where the law requires or where it suspects misuse. Who at the company may read it. Where it is handled, and where it is stored |
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
| What is sent | Your words. `[SETTING: your search settings go with them only if the service is set to send them, and the notice beside the box says which is so]` With them go Burro's own instructions to the model, which are the same for everyone |
| What your search settings are, where they are sent | Renting or buying, the budget, how long each journey may be and by what means, what matters to you and how much, and any area you ruled in or out |
| What is never sent | Your internet address: the call comes from Burro's service, not from your browser. The places you need to reach: where settings are sent, each place is replaced by its position in the list, 1, 2 or 3. Anything that says who you are, unless you type it. A place you name in the sentence itself is in the sentence |
| What the model does | It reads your sentence into settings, or into offers that you choose from. It never ranks a place, scores one or describes one |
| What the company's library does | Nothing. Burro uses no company's own software. Each call is one request that Burro's code makes itself |
| If the model is slow or fails | Burro's rules answer in its place. Your words were still sent. Burro waits 6 seconds, and the call is given up at the same limit. `[SETTING: whoever runs the service can set another time, up to 60 seconds]` |
| If a company refuses Burro's calls | After three refusals in a row Burro asks it nothing for five minutes, and the rules read in that time |
| Can Burro delete the company's copy? | No. Burro cannot tell the company which words were yours, because it keeps no record of them |
| Advice | Leave out your health, your religion and anything else you would not want kept. The notice beside the box says the same wherever a model reads |

`[SOLICITOR]` The ICO's list asks a notice for the recipients, the periods and the transfers. This notice gives the four companies by name and leaves the periods and places to the notice beside the box, which is shown at the moment a person types. Whether a page that points there is enough, or whether it must repeat what the box says, is not settled.

`[FOUNDER: what the notice beside the box says of each company today is in providers/terms.py, and models.md, section 6, shows it side by side. A test holds that page to the code. As the table stands no company can be turned on: nobody has checked a sentence of any of the four.]`

`[FOUNDER: what you accepted on 24 September 2026. Google keeps what is typed for 55 days. The period cannot be shortened on this service. Its staff may read what it flags, and it gives no period for what it flags. What is typed may be handled and stored in any country where Google or its agents have facilities. The notice beside the box says each of these when Google is the company in use.]`

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
| If a model reads your words | The company that runs it receives the sentence as you typed it, sensitive parts included, and keeps it as the notice beside the box says. That notice ends with the advice to leave out your health, your religion and anything else you would not want kept |
| Before a sentence is sent | The notice beside the box is shown before you type. `[NOT BUILT: Burro asks you first. The words of the question are in section 11. The website does not ask this yet]` |

A setting can say something about you as well. One that asks for a place of worship, or that names a hospital or a school as a place to reach, is a wish about a place. Burro treats it as that and as nothing more. Section 6 says where a setting goes.

## 6. The settings of your search

| | |
|---|---|
| What they are | Renting or buying, a budget, up to three places to reach and how long each journey may be, what matters to you and how much, and any area you ruled in or out |
| Where they live | In your browser, in the page's memory |
| What Burro's service does with them | Your browser sends them with each request. The service ranks the areas, answers, and keeps nothing |
| Do they go to a language model | `[SETTING: only if the service is set to send them, and the notice beside the box says so]` Where they go, they go without the places you need to reach. Section 4 |
| Are they logged | No setting is logged, and no code made from the settings alone. When you type a sentence, the counts and codes in its log line come from your words and your settings together: a code can say that a request changed nothing, which depends on what was already set. None holds a number, a name or a place. [ADR 0011](../adr/0011-nothing-is-kept-for-a-search.md) leaves it to the founder whether to go on writing them |
| When they are gone | When you close or reload the page |

The places you need to reach can say where you work or where your child goes to school. What matters to you can say something too: a place of worship, or a kind of food shop. That is why Burro keeps no search, and why a place and a setting are never written to a log.

## 7. A shared link

You can make a link to a search. It is the one thing Burro stores, and only when you ask.

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

## 9. The companies that host Burro

Burro runs on other companies' computers. Each receives what any host of a website receives.

| Company | What it does | What reaches it | What it keeps | Where | Agreement on data processing |
|---|---|---|---|---|---|
| Fly.io | Runs the service that answers searches | Every request to the service: your internet address, and the request itself, which holds what you typed and your settings. The id of a shared link, when one is opened | Burro's log lines, for 7 days. **Read**, at <https://fly.io/docs/monitoring/logging-overview/>. What its own systems record of a request was not said on the pages read. **Not read** | The machine is in London. Your connection may be decrypted at the Fly.io computer nearest you, which may be outside the UK, and passed on encrypted. **Not read again: from [deploy/README.md](../../deploy/README.md)** | None found. The list of its legal documents names none. **Not read** |
| Vercel | Serves the pages of the website | Requests for pages: your internet address, your browser's name and the page asked for. The address of an area's page names the area, and the address of a comparison names the areas compared. So Vercel can see which areas an internet address looked at. Never what you type, and never the id of a shared link: your browser sends the first straight to the service, and keeps the second in the part of the address that is sent to no server | Request logs for 1 day on the Pro plan. `[SETTING: the plan, and no add-on that keeps logs longer]` **Read**, at <https://vercel.com/docs/logs/runtime>. It can match a request to an internet address. **Read** | Pages that are rebuilt, in London. Other files from wherever is nearest you. **Not read again: from [deploy/README.md](../../deploy/README.md)** | Part of its terms, for the Pro and Enterprise plans. **Read**, at <https://vercel.com/legal/dpa>, dated 17 March 2026 |
| `[FOUNDER: the company that holds the domain's name records]` | Tells your browser where Burro is | The name your browser looks up | **Not read** | | |

Burro is not deployed. This table is what the plan in [deploy/README.md](../../deploy/README.md) would make true. It changes if a host changes.

Later, and not yet: a company to serve map tiles, a database for accounts and links, and a service that collects error reports. Each will be added here before it is used.

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

## 12. How long each thing is kept

| Thing | Kept by | For how long |
|---|---|---|
| What you type | Burro | Not kept. It is held in the service's memory while it is read, and then dropped. Where a model is slow Burro stops waiting after 6 seconds, and the call is given up at the same limit. `[SETTING: up to 60]` It is never written down |
| What you type | The company that runs the model, if one reads your words | As the notice beside the box says. It differs by company, and one of the four gives no period. Where a company suspects misuse, or the law requires it, it may keep what it received for longer |
| Your settings | Burro | Not kept, unless you make a link |
| A shared link | Burro | Section 7 |
| Log lines | Fly.io | 7 days. `[SETTING]` |
| Records of calls | Burro | 30 days at most. Today, until the service restarts |
| Requests for pages | Vercel | 1 day. `[SETTING]` |
| Email | `[FOUNDER: the mail provider]` | `[FOUNDER: a period]` |

## 13. Where your data goes

Burro is run from the United Kingdom. Some of the companies it uses are outside it. The ICO calls sending personal data to a separate company outside the UK a restricted transfer, and says it needs UK adequacy regulations, a safeguard or an exception. Source: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/international-transfers-a-guide/>, dated 15 January 2026. Read. Whether each row below is enough is this draft's reading, not advice.

| Company | Country | What goes | Safeguard | How it is known |
|---|---|---|---|---|
| Fly.io | United States. The machine is in London | Requests to the service | Its privacy policy says it complies with the "UK Extension to the EU-U.S. Data Privacy Framework" | **Read**, at <https://fly.io/legal/privacy-policy/>, dated 20 July 2026. Whether that covers data it handles for a customer was not said. **Not read** |
| Vercel | United States. Rebuilt pages in London | Requests for pages | Standard contractual clauses with the UK addendum | **Read**, at <https://vercel.com/legal/dpa> |
| The company that runs the model, if one reads your words | As the notice beside the box says. None of the four handles what it receives in the United Kingdom alone | What you type, and your settings if the notice says so | It differs by company. [models.md](../design/models.md), section 3, has each. One of the four names none, and it is the one that is never used for what real people type | Read for the four reports in [docs/research/models/](../research/models/) |

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

**What Burro cannot do.** Burro keeps nothing that says which search was yours. It cannot find your words, because it has none. It cannot pick your line out of a log, because no line says whose it is. It cannot ask the company that runs a model to delete your words, because it cannot say which they were. If you can give Burro something that lets it find your data, such as a shared link, it will act on it. `[FOUNDER: Article 11 of the UK GDPR speaks of a service that does not need to know who a person is. This draft reads it as covering Burro. That is a reading, not advice, and README.md, risk 8, says why it may be wrong. Source: <https://www.legislation.gov.uk/eur/2016/679/article/11>. Read.]`

**How to use a right.** Write to the contact in section 1. Say what you want. You do not need to give a reason or use special words.

| | |
|---|---|
| How long Burro has to answer | One month. The ICO says: "without undue delay and at the latest within one month of receipt of the request" |
| Can it take longer | By up to two more months if the request is complex. Burro will tell you within the first month |
| What it costs | Nothing, in most cases |
| Will Burro ask who you are | Only if it needs to, to be sure it sends data to the right person. For a shared link, the link is enough |

Source: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/right-of-access/what-should-we-consider-when-responding-to-a-request/>, updated 8 December 2025. Read.

## 15. How to complain

| Step | |
|---|---|
| 1. Tell Burro | Write to the contact in section 1. Burro will say it has your complaint within 30 days, look into it, keep you informed, and tell you the outcome without undue delay |
| 2. Tell the regulator | You can complain to the Information Commissioner's Office at any time: <https://ico.org.uk/make-a-complaint/>, or 0303 123 1113 |

## 16. Age

`[FOUNDER: Burro is for people aged 18 or over.]` Burro does not ask your age and does not check it.

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
| What is coming | Accounts, so that a shortlist can be kept. Then Burro will hold an email address, and this notice will say so first |

| Date | What changed |
|---|---|
| `[FOUNDER: date]` | First published |

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
| Recipients or categories of recipients | 4, 9, 10 | The four companies that can run a model are named. Which is in use is said beside the box |
| Details of transfers to third countries | 4, 13 | For a company that runs a model, beside the box |
| Retention periods | 12 | For a company that runs a model, beside the box. `[SOLICITOR]` Section 4 says why |
| Rights available to individuals | 14 | |
| Right to withdraw consent | 11, 14 | |
| Right to lodge a complaint with a supervisory authority | 15 | |
| Details of statutory or contractual obligation to provide data | | Does not apply. Nobody has to give Burro anything |
| Details of automated decision-making, including profiling | 17 | |
| Categories of personal data obtained | | Applies only to data from other sources. Burro gets none |
| Source of the personal data | | The same |

The ICO also says a person must be told they can complain to the organisation as well as to the ICO, "at the point you collect their personal information (eg by displaying this in your privacy notice)". Section 15. Source: <https://ico.org.uk/for-organisations/how-to-deal-with-data-protection-complaints/how-do-we-prepare-to-handle-data-protection-complaints/>. Read.

It says privacy information must be given "at the time when personal data are obtained", and that posting it on a website is not enough by itself. So the box where a person types needs a link to this notice beside it. Source: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/the-right-to-be-informed/when-should-we-provide-privacy-information/>. Read.

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
| What is typed does not pass through the website's host | 3, 9 | `apps/web/src/lib/api/config.ts`: the browser calls the service itself. `apps/web/test/privacy/source.test.ts`, `test_the_website_has_no_handler_action_or_middleware` | Code and test |
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
| The notice beside the box is the service's own, and the website has no words for it | 3, 4 | `reader` in `MetaData`, `services/api/src/burro_api/wire.py`. `test_the_website_has_no_words_of_its_own_for_the_notice`, `test_no_providers_name_or_terms_is_written_in_the_websites_own_source`, `test_site_copy_names_no_provider_and_states_none_of_its_terms` | Code and test |
| No sentence is sent until the service has said who reads | 3, 4 | `test_a_sentence_sent_before_the_service_has_said_who_reads_waits_until_it_has`, `test_the_page_asks_the_service_who_reads_and_takes_nothing_from_what_it_was_built_on` | Code and test |
| Words that are not a plain list are applied to nothing, and what was noticed is offered | 3 | `test_a_prompt_that_is_not_plain_applies_nothing_and_offers_what_was_noticed`. `test_nothing_is_ranked_from_what_was_noticed_until_the_person_chooses` | Code and test |
| Nothing a model reads is applied until the person chooses it | 3, 4 | [ADR 0012](../adr/0012-a-closed-vocabulary-and-a-guard-on-the-model.md) lists what a model's reading may apply today | Not true yet |
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
| There is no step that asks before a sentence is sent | 5, 11 | No such step was found in `apps/web/src` or `services/api/src`. `apps/web/src/components/PromptBox/PromptBox.tsx` shows a line under the box | Not true yet |
| The line under the box names no company and no period | 4 | `WORDS_LINE` in `apps/web/src/content/site.ts`. `test_site_copy_names_no_provider_and_states_none_of_its_terms` | Code and test |
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
| Nobody may use Burro to choose between people | 17 | Sections 13, 29, 33, 111 and 112 of the Equality Act 2010, as printed. The equality regulator's guidance was not read | Read twice. The reading is not |
| That naming four companies and pointing to the notice beside the box is enough | 4 | Nothing. The ICO's list of what a notice holds was read, and does not say | A reading |
