# Legal documents: drafts

**Drafts. Not published. Not legal advice.** Written on 23 September 2026 from public guidance and from the code in this repository, and brought up to 24 September 2026. **Nobody qualified has read any of them, and whoever wrote them is not a lawyer.** There is no budget for that ([ADR 0007](../adr/0007-no-solicitor.md)). This file says what they are, what was put right on the second day, where they are most likely to be wrong, and the cheapest ways to have them read.

## What is here

| File | What it is | State |
|---|---|---|
| [privacy-notice.md](privacy-notice.md) | What Burro collects and what it does not, in the order a person would ask | Draft. 16 things stand between it and publishing. They are listed at its top |
| [terms-of-use.md](terms-of-use.md) | What Burro is and is not, and what is asked of a person who uses it. Section 7 holds the term for anyone who lets or sells homes | Draft. 11 things stand between it and publishing |
| [data-protection-checklist.md](data-protection-checklist.md) | The launch checklist. What the founder must do that a document cannot, in the order of what blocks a public launch: 19 tasks in four stages, 31 to 35 hours, GBP 47 to 52 | Draft |
| [residents-crime-and-equality.md](residents-crime-and-equality.md) | What Burro holds about the people who live in an area, what the ICO's pages and the Equality Act say of it, where the risk lies, and each point where a solicitor's reading would change what is safe to ship | Draft. New on 24 September 2026 |
| The accessibility statement | It is part of the website, at `apps/web/src/content/accessibility.ts`. It was read for this work and not changed | It says it has nowhere to send a report yet |

Burro was first deployed on 25 September 2026, with the made-up city. The website has no page for any of the four drafts, so none of them is in front of the public as Burro's own: the accessibility statement is part of the website, and is. None of the drafts may be published as it stands.

| Mark | Meaning |
|---|---|
| `[FOUNDER: ...]` | A blank only the founder can fill |
| `[FOUNDER NAME]`, `[FOUNDER CONTACT]`, `[COMPANY NAME]`, `[COMPANY NUMBER]` | The name and the contact. Never fill them in this repository: it is public |
| `[NOT BUILT: ...]` | A sentence the code does not yet make true |
| `[SETTING: ...]` | A sentence that is true only while a setting holds, at a host, at a provider or in the service. No code or test holds it |
| `[SOLICITOR]` | A sentence where this draft's reading of the law decides what is said. A qualified reading could change what is safe to ship. [residents-crime-and-equality.md](residents-crime-and-equality.md), section 9, lists those about residents, recorded crime and the equality law, in the order of what each could cost. The rest are in the table of risks below |

## What was no longer true on 24 September 2026

The drafts were a day old. In that day the four providers were wired into the service, real data was built for London, and the founder made the decisions below. Every sentence that had stopped being true is here, with what it says now.

### What the founder decided that day

| Decided | Where it shows |
|---|---|
| Google keeping what is typed for 55 days is accepted, with its staff reading what it flags | Notice, section 4. Checklist, tasks 5 and 15. [ADR 0019](../adr/0019-no-one-provider-and-a-key-alone-turns-nothing-on.md) |
| DeepSeek is never used for what real people type | Notice, section 4. Checklist, tasks 4 and 15. ADR 0019 |
| The model proposes, the person confirms, code checks. Nothing a model reads is applied by itself | Notice, sections 3 and 4. Terms, section 5. Marked `[NOT BUILT]` |
| The age of residents and what their households are made of may feed a vibe and a ranking | Notice, sections 5 and 18. Terms, section 2. [ADR 0006](../adr/0006-rank-places-not-residents.md) |
| Ethnic group and religion are shown on an area's page, and ranked on only through what is there | Notice, sections 5 and 18. Terms, sections 2 and 7. [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md) |
| No filter by who lives somewhere. Gender is left out. The religious character of a school is no amenity | [residents-crime-and-equality.md](residents-crime-and-equality.md), section 2 |
| Stop and search is never read. Of the police file, the crime files alone are read | Notice, section 18. [residents-crime-and-equality.md](residents-crime-and-equality.md), section 5 |
| One vibe, Gritty, counts recorded crime. To type "gritty" is to ask for recorded crime by name | Notice, section 18. Terms, section 2. [ADR 0013](../adr/0013-vibes-are-the-centre.md) |
| Vibes are the centre. Median sale prices may be shown | Nothing in these drafts turns on either |

### In the privacy notice

| The draft said | What had changed | Now |
|---|---|---|
| "There is no app yet" | An iPhone app is built. It has not been released | The notice says that it does not cover the app |
| Only one column of the table of four companies is published, and the founder picks it | The service serves what people are told, by provider, and the website shows it beside the box | Section 4 names the four, says what never changes, and points to the notice beside the box for the rest. The table of four is gone from the notice: [models.md](../design/models.md), section 6, holds it, and a test holds that page to the code |
| "A model is on when a provider's key is in the service's environment" | A key alone turns nothing on. Five things must hold | Section 4, and the table of settings |
| "As the service is wired, only Anthropic's column can apply" | The service depends on no provider's library and can ask any of four | Section 4 |
| Adapters "are written and are not wired into the service" | They are wired in | Section 4. Appendix B |
| A provider is held back if its terms "were read through an extraction" | All four are held alike, until a person has checked each sentence | Section 4. Appendix B |
| What the company receives: "Your sentence, and your settings so far" | The words go alone unless the service is set to send the settings | Sections 4 and 6 |
| "A call that is late is not stopped. It is left to finish" | The adapter gives the whole call one deadline, which is the same number of seconds that Burro waits | Sections 4 and 12 |
| "The provider's library times each read and not the whole call" | There is no provider's library | Section 12 |
| What a provider keeps: "55 days at Google, up to 30 days at Anthropic and at OpenAI" | The notice must be true whichever provider is in use | Section 12 points to the notice beside the box |
| The line under the box says a provider keeps words "for up to 30 days" | The line names no company and no period. A test holds the website to that | Off the list of what is missing |
| Burro "turns it into settings" | Words that are not a plain list are applied to nothing. What was noticed is offered, and the person chooses | Section 3 |
| "What a model answers is held to what the rules can check" | The founder decided that nothing a model reads is applied by itself | Section 3, marked `[NOT BUILT]` |
| "Burro has no setting about who lives somewhere" | Age and household make-up may feed a ranking | Sections 5 and 18, marked `[NOT BUILT]`. It is still true of the code |
| "When it finds one it makes no setting from it" | True of a wish for fewer of any group. A wish for more of an age or a kind of household may become a setting | Section 5 |
| A log line holds "which reader read it, which model" | It holds the name of the provider too. The service writes a line when a provider is not used, and when one is left alone | Section 8 |
| "How it went" is "one of seven codes" | Eight | Section 8 |
| Census figures "are never used to rank an area". "Burro holds no data about any resident" | Two of the tables may be ranked on. The second sentence was true and said too little | Section 18 says what is held, for how large an area, and what is never read |
| Appendix B named `claude.py`, `claude_sdk.py`, `test_claude.py`, `test_claude_kept.py`, `_interpreter`, `KEY_VARIABLE` and a test of the line under the box | Each was renamed or is gone | Appendix B names what is there. Every name in it was looked for and found |
| "A test" meant that a test was found and read | | It still does. Every file and every test that Appendix B names is in the repository under that name |

### In the terms of use

| The draft said | What had changed | Now |
|---|---|---|
| "Nothing about who lives in an area is used to rank it" | Age and household make-up may be | Section 2, marked `[NOT BUILT]` |
| "Recorded crime counts in a ranking only if you ask for it" | It also counts in a vibe that holds it, when that vibe is asked for | Section 2 |
| "Until Burro is given real data, everything it shows is invented" | Real data is built for London, as a preview that says it is one | Section 4 names three kinds of data |
| What reads your words: "The privacy notice says which" | The notice beside the box says which | Section 5 |
| Steering "may be against the law", and "the Equality Act 2010 was not read for this draft" | The Act was read, as printed | Section 7 says what it forbids, and holds a term for anyone who lets or sells homes. Appendix A quotes what was read |
| Appendix B: "No real release exists" | One does, as a preview | Appendix B |
| Appendix B named `claude.py` and a test of the synthetic flag | Renamed | Appendix B names what is there |

### In the checklist

| The draft said | What had changed | Now |
|---|---|---|
| Tasks were in the order they were thought of | | Four stages, in the order of what blocks a public launch |
| "As the service is wired, a key alone switches a model on" | It does not | Tasks 13 and 15 |
| The table of what the code holds had a column for "the service as wired" and one for "the adapters, which are not wired in" | There is one service | Task 15 |
| "The line under the box put right: it says 30 days" | Done | Task 6 says what is built |
| Nothing on the equality law, on figures about residents or on DeepSeek | | Tasks 7, 8 and 18. DeepSeek is in tasks 4, 5 and 15 |

## Checked against the code

The notice and the terms were read against `services/api/` and `apps/web/` twice on 23 September 2026, and again on 24 September 2026. What the first two readings corrected, and still stands:

| The draft said | The code, as read | Now |
|---|---|---|
| Only a company that runs a model receives what you type | The company that hosts the service receives every request and decrypts it | The notice says so in its first table, and in sections 3 and 4 |
| Nothing worked out from the settings is logged | The counts and codes in a sentence's log line depend on the words and the settings together. ADR 0011 says so and leaves it open | Section 6 says so |
| A request about who lives somewhere makes no setting | One that the list of words misses is read like any other words. With a model on, one that both miss can become a setting about a place | Section 5 says so |
| A shared link shows everything stored under it | The time it was made is stored and not shown | Section 14 says so |
| There is no analytics | None is in the website's code. The host offers it as a setting, and its script would come from the website's own address | Marked `[SETTING]` |
| The box that finds a place is "the same" as the sentence | It sends what is typed as it is typed, after a quarter of a second | Section 3 says so |
| A call record holds whether the call worked | Its status can also say `policy_redirect` or `off_topic` | Section 8 says so |
| No condition is "needed" for settings, links or an internet address | That is a conclusion about the law | It now reads "none claimed", with the doubt beside it |

## How they were written

| Point | What it means for you |
|---|---|
| Every page was read through a reader that extracts of a page, not the page | A quoted sentence may differ from the source by a word. Check the wording at the address before it is published. Once, the tool's summary said the opposite of the sentence it quoted. The page was asked again and the quote was kept |
| On 24 September 2026 every page was read twice, asked in different words each time | What is kept is what both readings gave. Where the two gave a sentence in different words, a third reading was asked whether the page holds it word for word |
| No web search was made | Only known addresses were opened, and addresses found on pages that were read |
| "Read" means read at the publisher's own address that day | "Not read" means that the page was not read. What is said of it is an inference or a recollection |
| The model providers' terms were read for the four reports in [docs/research/models/](../research/models/) | Only each provider's page on how long it keeps text was read again for these drafts, on 23 September 2026. What people are told of a provider is no longer in these drafts. It is in `services/api/src/burro_api/providers/terms.py` |
| The code was read | Appendix B of each draft names the file or test behind each claim. On 24 September 2026 each was looked for by its name, and is there |
| Most ICO pages say they are "under review" because of the Data (Use and Access) Act | The ICO says all of that Act's data protection provisions are in force as of 19 June 2026 |
| The law itself was read for these provisions only | Article 11 of the UK GDPR. Sections 57, 61, 62, 65 and 68 of the Consumer Rights Act 2015. Regulation 3 of the fee regulations. Regulation 6 of the e-commerce regulations. Sections 4, 9, 10, 13, 19, 28, 29, 31, 32, 33, 38, 111 and 112 of the Equality Act 2010, with the Explanatory Notes to six of them. For the rest, the regulator's account of the law was read, not the law |
| The equality regulator's own guidance was not read | Section 7 of the terms and the reading of the equality law rest on the Act as printed. Checklist, task 8 |

## What the founder decided on 23 September 2026, and where it shows

| Decision | Where |
|---|---|
| Every insight is cited | Terms, section 3 |
| Census figures are shown on an area's page | Notice, section 18. Terms, section 2. Changed in part the next day: two of the tables may also be ranked on |
| All of London | Terms, section 1 |
| A model researches when a release is built, and is never asked about a place when answering | Notice, section 4. Terms, section 5. What a model reads when a release is built is public sources, not what people type. These drafts do not cover it. If a source names a living person, that is personal data too |
| No single provider, Gemini first | Notice, section 4 |

## Which sentences carry the most risk if wrong

In the order of what they could cost.

| # | The sentence | Where | Why it may be wrong | What would settle it |
|---|---|---|---|---|
| 1 | The lawful basis for reading a sentence is consent, and explicit consent where it is sensitive | Notice, 5 and 11 | The repository holds two readings. The four provider reports and the ICO's page point to explicit consent. [An earlier report](../research/reports/accounts-compliance.md) held that no condition is needed if Burro never infers or uses such data, and marked that as its own reading. The website informs and asks nothing. The ICO says a basis cannot usually be swapped later. Burro keeps no record of a person, so it cannot show who agreed | A qualified reading. Before that, the ICO's helpline, with the question in writing |
| 2 | Ranking on the age of residents and on what households are made of treats no person less favourably, and the census table leads nobody to steer | Notice, 17 and 18. Terms, 2 and 7 | The Equality Act was read as printed. The regulator's guidance, and every judgment, were not. Age is itself a protected characteristic. Section 111 could reach a service that leads someone else to discriminate, "direct or indirect". No professional has read the decision or the term | Checklist, task 8. Then a qualified reading. [residents-crime-and-equality.md](residents-crime-and-equality.md), section 9 |
| 3 | "DeepSeek is never used for what real people type" | Notice, 4 | A setting holds it and no code does. If it were named on a live service, with its terms accepted and its entry checked, what people type would go to a company that publishes no agreement, no safeguard and no period | Code that refuses it on a release that is not made up |
| 4 | "Burro does not keep it and does not write it to a log" | Notice, 3 | It is true of Burro's code. Fly.io decrypts every request to pass it on. What its own systems record was not said on the pages read, and no agreement with it was found | Fly.io's answer in writing, and its agreement |
| 5 | What the notice beside the box says of a provider | Notice, 4 | Periods and places change. Nobody has checked a sentence of any of the four against its page, so none can be turned on. Once one is, a wrong sentence is a false statement to the public | Checklist, task 15. Read the provider's pages again on the day of publishing |
| 6 | That naming four companies, and pointing to the notice beside the box for the periods and places, is enough | Notice, 4 | The ICO's list asks a notice for recipients, periods and transfers. No page read says whether a notice may point elsewhere for them | Show the served notice on the page of the privacy notice, which the draft asks for. Then a qualified reading |
| 7 | The safeguard for each transfer out of the UK | Notice, 13 | It depends on a list that was not opened, and on risk assessments that are not written. Sensitive data sent under the UK-US arrangement "must be appropriately identified as sensitive". Google may handle what is typed in any country | Checklist, task 5 |
| 8 | "Burro holds nothing that it can tie to you" | Notice, 14 | It rests on Article 11. A sentence can name a workplace and a school. A host holds an internet address and a time. Whether that leaves Burro "not in a position to identify" a person is a legal question | A qualified reading |
| 9 | A share for an area of several thousand people is about nobody who can be identified | Notice, 18 | It is this draft's reading of the ICO's pages on anonymous information, which are written for whoever makes statistics and not for whoever shows them. The floor of 1,000 people is a first guess, and no test holds it | The ICO's helpline, with question 4 below. A test for the floor |
| 10 | No condition is claimed for log lines, or for a setting about a place of worship | Notice, 8 and 11 | A line can hold the code `health_services`, `community_amenities` or `policy_redirect`, with a time. So can a call record, which is kept for up to 30 days. A shared link can hold a wish for a place of worship. No line says whose it is. [ADR 0011](../adr/0011-nothing-is-kept-for-a-search.md) leaves the log to the founder | Take the four fields off the list of what may be logged. That removes `health_services` and `community_amenities`. It does not remove `policy_redirect`, which is in `interpret_status`, in `call_status` and in the call record. Removing that is a second change |
| 11 | What Burro is and is not responsible for | Terms, 9 | The draft limits little, on purpose. As read in the Consumer Rights Act 2015: an unfair term does not bind a consumer (section 62), liability for death or injury from negligence cannot be excluded (section 65), and in a contract for a service nor can the duty of section 49 (section 57). Section 49 itself was not read. Whether a free website makes a contract at all was not settled. The other choice is a cap on what Burro pays. A cap may be unfair, and the regulator's guidance on it was not read | A fixed-fee review, when there is revenue |
| 12 | "Not advice", made-up data, and a preview | Terms, 2 and 4 | Saying so does not cure a statement that misleads. The law on that was not read. The protection is in the product: the banner, the source and the date under every figure | Keep the banner until every figure is real and finished. Say no more in marketing than the terms do |
| 13 | "18 or over", not checked | Notice, 16. Terms, 6 | Google forbids a product "likely to be accessed by" under-18s, and Google comes first. Saying is not checking | Checklist, task 14 |
| 14 | Who is named as running Burro | Notice, 1. Terms, 13 | GOV.UK says a sole trader must put their name on "official paperwork", and does not say whether a website is that. The e-commerce regulations, as read, ask a website for a name and a geographic address. Whether they reach a website that is free was not read. If either applies, a name and an address become public | Checklist, task 1 |
| 15 | Which law and which courts | Terms, 12 | The wording is common. It was not read at a source | A fixed-fee review |
| 16 | No cookie banner is shown | Notice, 2 | That the website sets no cookie and stores nothing is held by tests. That no banner is then needed is an inference. The ICO's page, as read, did not say | Low. Read the ICO's guidance in full |

## The cheapest ways to have them read

No public price for a fixed-fee review of a privacy notice was found. No web search was made: only known addresses were opened. Every row was read on 23 September 2026.

| Way | What you get | Cost, as read | Read |
|---|---|---|---|
| Ask the ICO | An answer to a question, by phone, live chat or a form. 0303 123 1113, Monday to Friday, 9am to 5pm. The page does not offer to review a document | Free | Read, at <https://ico.org.uk/for-organisations/advice-for-small-organisations/contact-us/> |
| The ICO's privacy notice generator | A notice made from your answers, to hold against this one. "designed for sole traders and start-ups, as well as small and medium-sized businesses and charities". Updated 10 July 2026 | Free | Read, at <https://ico.org.uk/for-organisations/advice-for-small-organisations/privacy-notices-and-cookies/create-your-own-privacy-notice/> |
| A university law clinic: King's Legal Clinic | Advice from students supervised by lawyers, as "a written letter of advice, normally within two weeks of the initial interview". Six areas. Intellectual property is one. Data protection is not listed | Free | Read, at <https://www.kcl.ac.uk/legal-clinic> |
| A university law clinic: qLegal, Queen Mary | Not checked | | Not read |
| LawWorks clinics | "free initial advice to individuals". Not for a business | Free | Read, at <https://www.lawworks.org.uk/legal-advice-individuals>. Not a route for Burro |
| British Library Business and IP Centre | "Free start-up workshops, events, resources and one-to-ones", and sessions with intellectual property specialists. The page does not name data protection | Free | Read, at <https://www.bl.uk/business-and-ip-centre> |
| The equality regulator | Its guidance and its code, to read. Whether it answers a question from a business was not read | Free | Not read |
| A fixed-fee review: Sprintlaw | "a fixed-fee quote setting out costs, scope and timing", after a call. It lists data and privacy among its services | Not published | Read, at <https://sprintlaw.co.uk/> |
| A fixed-fee review: LawBite | | | Not read |
| Rocket Lawyer UK | | | Not read |
| A template: SEQ Legal | A privacy policy template for UK websites, with a credit line. Updated 1 March 2026 | Free | Read, at <https://seqlegal.com/free-legal-documents/privacy-policy> |
| A template service: Termly | One basic policy | USD 0. Paid plans USD 10 to 20 a website a month | Read, at <https://termly.io/pricing/> |
| A template service: iubenda | | USD 5.99 to 119.99 a site a month | Read, at <https://www.iubenda.com/en/pricing> |
| A solicitor, as first planned | A review of four documents | GBP 5,000 to 10,000 | [PLAN.md](../PLAN.md). Rejected by the founder |

A template service writes a notice. It does not read yours. Burro's notice is unusual in what it does not collect, and a template will not know that.

What to do, in order:

| Step | Cost | Hours |
|---|---|---|
| 1. Put four questions to the ICO, in writing, and keep the answers | Free | 1 |
| 2. Read the equality regulator's guidance, and put it beside the reading of the Act | Free | 1 |
| 3. Run the ICO's generator and hold its notice against this one. Note what it asks that this one does not answer | Free | 1 |
| 4. Apply to a clinic, with the notice, the terms and the list of risks above | Free. A wait | 2 |
| 5. When there is revenue, buy a fixed-fee review. Ask first for the points marked `[SOLICITOR]`, in the order of [residents-crime-and-equality.md](residents-crime-and-equality.md), section 9, and then for the privacy notice | A quote | |

The four questions:

| # | Question |
|---|---|
| 1 | People may type something sensitive into a free-text box. We keep none of it. We send it to a processor that keeps it for up to 55 days. Must we ask for explicit consent before the first sentence, or is a clear notice beside the box enough? |
| 2 | We keep no record of who visits. If consent is needed, how do we show it was given? |
| 3 | We hold nothing that says whose a search was. May we rely on Article 11 when a person asks for their data? |
| 4 | We show published census shares for areas of 5,000 to 15,000 people, ethnic group and religion among them, and we rank areas on the age of residents and on what households are made of. We hold nothing about any person. Is any of that processing of personal data? |

## What disagrees with these drafts

Each is outside `docs/legal/`, so none was changed for these drafts.

| Where | What it says | What is so |
|---|---|---|
| `apps/web/src/content/methods.ts` | "Nothing that describes who lives somewhere is used", and of the features, "None describes who lives there" | Changed on 2026-09-24, when core came to hold four measures of age and of households. It says the words of [residents-crime-and-equality.md](residents-crime-and-equality.md), section 11, but for the year of the census, which is in the name of each measure. The part on what Burro holds about residents is not written |
| `apps/web/src/content/vibes.ts`, `apps/web/src/content/area.ts` | A vibe "is named for the place, never for who lives there". "Nothing about who lives in a place is compared" | The first was changed the same day: a vibe that counts who lived in an area says so. The second stands, and is still so |
| `packages/core/AGENTS.md` | The Gritty that holds recorded incidents "is refused in any release that is not synthetic. Do not loosen that rule: changing it is changing ADR 0006" | ADR 0006 was changed on 24 September 2026. The rule is still in the code |
| `services/api/src/burro_api/providers/choose.py` | It holds all four providers alike | The founder decided that DeepSeek never reads what real people type. No code refuses it |
| `apps/ios`, `SearchCopy.swift` and its tests | A provider "may keep it for up to 30 days" | It is true of two of the four, and Google comes first. [ADR 0019](../adr/0019-no-one-provider-and-a-key-alone-turns-nothing-on.md) says what the app needs |
| [deploy/README.md](../../deploy/README.md) | Vercel's log holds "the path, the query string, the status and the browser's name" | Vercel's page also says it can match a request by internet address. Read on 23 September 2026 |
| [deploy/README.md](../../deploy/README.md) | Fly.io is a processor and must be named | No agreement with Fly.io was found. Its list of legal documents was read a second time on 23 September 2026, through an extraction, and named a privacy policy, supplemental terms and terms of service. The terms of service were not read in full for one |
| `services/api`, `calls.py` and `logs.py` | A status of `policy_redirect` is kept in the call record and written to the log | ADR 0011 leaves four fields of the log line to the founder. The status is not one of the four |
| `services/api` | No route deletes one shared link | A person may ask for one to be deleted |
| `services/api`, `admit` in `app.py` | Every call is let in | The terms ask people not to send requests in bulk, and nothing enforces it. With a model on, what stops a bill is the service's own cap on calls to a model, which is for everyone together and tells nobody apart ([ADR 0032](../adr/0032-calls-to-a-model-are-capped-for-the-whole-service.md)), and a cap on spending at the provider |
| `apps/web` | No step asks before a sentence is sent. No page holds a privacy notice or terms. The accessibility page has no address for a report | Each is needed before launch |
| [accounts-compliance.md](../research/reports/accounts-compliance.md) | Legitimate interests for a typed sentence, and no step that asks | Risk 1 |

## How to keep them true

| Rule | Why |
|---|---|
| Never publish a sentence marked `[NOT BUILT]` or `[FOUNDER]` | It is not true yet |
| Before publishing, check every `[SETTING]` at the host or the provider, and take the mark off only then | The code cannot hold it. A setting changed in a dashboard makes the notice false, and no test fails |
| Before publishing, read every `[SOLICITOR]` and decide whether to ship on this draft's reading | Nobody qualified has |
| When a file named in Appendix B changes, read the sentence beside it | A change to the code can make the notice false |
| Write no provider's period, place or terms in these drafts. Point to the notice beside the box | The service serves it, from one table that a person checks. A second copy here can only drift |
| When a host changes, change the notice in the same change | The notice names them |
| When a measure of residents, or a vibe that counts recorded crime, is built, take the mark off the sentence in the same change, and name the test that holds it | The decision is made and the code is not |
| Hold the numbers with a test: 10,000, 50,000, 600 characters, 6 seconds, 1,000 people | The website's copy is held to the decision records that way already |
| When accounts arrive, write the notice again | Most of what it says of rights will no longer be true. The checklist says what changes |

## What was not read

| What | Standing |
|---|---|
| A web search | None was made. Only known addresses were opened, and addresses found on pages that were read |
| The guidance of the Equality and Human Rights Commission for service providers, and its code of practice | Not read. The Act was read in its place. Checklist, task 8 |
| Any judgment of a court on the Equality Act | Not read |
| Schedules 3 and 5 of the Equality Act, and its Part 7 | Not read |
| The statistics office's own account of how it protects census tables | Not read for these drafts. The registry holds a note of it |
| qLegal | Not read |
| LawBite | Not read |
| Rocket Lawyer UK, the ICO's page on data protection officers | Not read |
| An agreement on data processing with Fly.io | None was read. None is on its list of legal documents, at <https://fly.io/legal/> |
| The ICO's page for making a complaint | Only its menus were read. Its postal address is not in the notice for that reason |
| The Competition and Markets Authority's guidance on unfair terms | The page that holds it was read. The 134 pages were not |
| Section 49 of the Consumer Rights Act, the Digital Markets, Competition and Consumers Act 2024 | Not read |
| Whether the e-commerce regulations reach a website that is free | Not read |
| Article 13 of the UK GDPR | Not read. The ICO's list of what it asks for was |
| The Data Privacy Framework list | Not opened |
| Any template file | The addresses were read. The files were not opened |
| What Fly.io's own systems record of a request | Not said on the pages read |
