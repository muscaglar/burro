# Legal documents: drafts

**Drafts. Not published. Not legal advice.** Written on 23 September 2026 from public guidance and from the code in this repository. **Nobody qualified has read any of them.** There is no budget for that ([ADR 0007](../adr/0007-no-solicitor.md)). This file says what they are, where they are most likely to be wrong, and the cheapest ways to have them read.

## What is here

| File | What it is | State |
|---|---|---|
| [privacy-notice.md](privacy-notice.md) | What Burro collects and what it does not, in the order a person would ask | Draft. 14 things stand between it and publishing. They are listed at its top |
| [terms-of-use.md](terms-of-use.md) | What Burro is and is not, and what is asked of a person who uses it | Draft. 8 things stand between it and publishing |
| [data-protection-checklist.md](data-protection-checklist.md) | What the founder must do that a document cannot: 15 tasks, 27 to 31 hours, GBP 47 to 52 | Draft |
| The accessibility statement | It is part of the website, at `apps/web/src/content/accessibility.ts`. It was read for this work and not changed | It says it has nowhere to send a report yet |

Nothing is deployed, so nothing here is in front of the public. None of the four may be published as it stands.

| Mark | Meaning |
|---|---|
| `[FOUNDER: ...]` | A blank only the founder can fill |
| `[FOUNDER NAME]`, `[FOUNDER CONTACT]`, `[COMPANY NAME]`, `[COMPANY NUMBER]` | The name and the contact. Never fill them in this repository: it is public |
| `[NOT BUILT: ...]` | A sentence the code does not yet make true |
| `[SETTING: ...]` | A sentence that is true only while a setting holds, at a host, at a provider or in the service. No code or test holds it |

## Checked against the code

The notice and the terms were read against `services/api/` and `apps/web/` a second time on 23 September 2026, by a second reader. No test was run. What was corrected:

| The draft said | The code, as read | Now |
|---|---|---|
| Only a company that runs a model receives what you type | The company that hosts the service receives every request and decrypts it | The notice says so in its first table, and in sections 3 and 4 |
| Your words are held for 6 seconds at most | The wait is 6 seconds by default and can be set up to 60. A late call is left to finish on its own thread | Sections 4 and 12 say so |
| Nothing worked out from the settings is logged | The counts and codes in a sentence's log line depend on the words and the settings together. ADR 0011 says so and leaves it open | Section 6 says so |
| A model receives your budget, journey times and what matters to you | It also receives any area ruled in or out, by its id | Section 4 lists it |
| A request about who lives somewhere makes no setting | One that the list of words misses is read like any other words. With a model on, one that both miss can become a setting about a place | Section 5 says so |
| A shared link shows everything stored under it | The time it was made is stored and not shown | Section 14 says so |
| There is no analytics | None is in the website's code. The host offers it as a setting, and its script would come from the website's own address | Marked `[SETTING]` |
| The box that finds a place is "the same" as the sentence | It sends what is typed as it is typed, after a quarter of a second | Section 3 says so |
| The code can call Anthropic only | True of the service as wired. Four adapters were written later the same day and are not wired in. Once they are, a key alone switches nothing on | Section 4 has a table for it |
| A call record holds whether the call worked | Its status can also say `policy_redirect` or `off_topic` | Section 8 says so |
| An area's page may show census figures | No page shows any | Marked `[NOT BUILT]` |
| No condition is "needed" for settings, links or an internet address | That is a conclusion about the law | It now reads "none claimed", with the doubt beside it |

## How they were written

| Point | What it means for you |
|---|---|
| Every page was read on 23 September 2026 through a reader that extracts of a page, not the page | A quoted sentence may differ from the source by a word. Check the wording at the address before it is published. Once, the tool's summary said the opposite of the sentence it quoted. The page was asked again and the quote was kept |
| No web search was made | Only known addresses were opened, and addresses found on pages that were read |
| "Read" means read at the publisher's own address that day | "Not read" means that the page was not read. What is said of it is an inference or a recollection |
| The model providers' terms were read for the four reports in [docs/research/models/](../research/models/) | Only each provider's page on how long it keeps text was read again for these drafts |
| The code was read and not run | No test was run. Appendix B of each draft names the file or test behind each claim |
| Most ICO pages say they are "under review" because of the Data (Use and Access) Act | The ICO says all of that Act's data protection provisions are in force as of 19 June 2026 |
| The law itself was read for eight provisions only | Article 11 of the UK GDPR. Sections 57, 61, 62, 65 and 68 of the Consumer Rights Act 2015. Regulation 3 of the fee regulations. Regulation 6 of the e-commerce regulations. For the rest, the regulator's account of the law was read, not the law |

## What the founder decided, and where it shows

| Decision of 23 September 2026 | Where |
|---|---|
| Every insight is cited | Terms, section 3 |
| Census figures are shown on an area's page and never ranked on | Notice, section 18. Terms, section 2 |
| All of London | Terms, section 1 |
| A model researches when a release is built, and is never asked about a place when answering | Notice, section 4. Terms, section 5. What a model reads when a release is built is public sources, not what people type. These drafts do not cover it. If a source names a living person, that is personal data too |
| No single provider, Gemini first | Notice, section 4: one column a provider. The service as wired can call Anthropic only. The adapters for the other three are written and not wired in |
| Census figures, again | No page of the website shows them yet. Notice, section 18, is marked `[NOT BUILT]` |

## Which sentences carry the most risk if wrong

In the order of what they could cost.

| # | The sentence | Where | Why it may be wrong | What would settle it |
|---|---|---|---|---|
| 1 | The lawful basis for reading a sentence is consent, and explicit consent where it is sensitive | Notice, 5 and 11 | The repository holds two readings. The four provider reports and the ICO's page point to explicit consent. [An earlier report](../research/reports/accounts-compliance.md) held that no condition is needed if Burro never infers or uses such data, and marked that as its own reading. The website asks nothing today. The ICO says a basis cannot usually be swapped later. Burro keeps no record of a person, so it cannot show who agreed | A qualified reading. Before that, the ICO's helpline, with the question in writing |
| 2 | "Burro does not keep it and does not write it to a log" | Notice, 3 | It is true of Burro's code. Fly.io decrypts every request to pass it on. What its own systems record was not said on the pages read, and no agreement with it was found | Fly.io's answer in writing, and its agreement |
| 3 | How long a provider keeps words | Notice, 4 and 12 | Periods change. The website says 30 days. Google says 55, and Google comes first. A wrong number is a false statement to the public | Read the provider's page on the day of publishing. Hold the website's line to the notice with a test |
| 4 | The safeguard for each transfer out of the UK | Notice, 13 | It depends on a list that was not opened, and on risk assessments that are not written. Sensitive data sent under the UK-US arrangement "must be appropriately identified as sensitive" | Checklist, task 7 |
| 5 | "Burro holds nothing that it can tie to you" | Notice, 14 | It rests on Article 11. A sentence can name a workplace and a school. A host holds an internet address and a time. Whether that leaves Burro "not in a position to identify" a person is a legal question | A qualified reading |
| 6 | No condition is claimed for log lines | Notice, 8 and 11 | A line can hold the code `health_services`, `community_amenities` or `policy_redirect`, with a time. So can a call record, which is kept for up to 30 days: its status can be `policy_redirect`. No line says whose it is. [ADR 0011](../adr/0011-nothing-is-kept-for-a-search.md) leaves it to the founder | Take the four fields off the list of what may be logged. That removes `health_services` and `community_amenities`. It does not remove `policy_redirect`, which is in `interpret_status`, in `call_status` and in the call record. Removing that is a second change |
| 7 | What Burro is and is not responsible for | Terms, 9 | The draft limits little, on purpose. As read in the Consumer Rights Act 2015: an unfair term does not bind a consumer (section 62), liability for death or injury from negligence cannot be excluded (section 65), and in a contract for a service nor can the duty of section 49 (section 57). Section 49 itself was not read. Whether a free website makes a contract at all was not settled. The other choice is a cap on what Burro pays. A cap may be unfair, and the regulator's guidance on it was not read | A fixed-fee review, when there is revenue |
| 8 | "Not advice", and made-up data | Terms, 2 and 4 | Saying so does not cure a statement that misleads. The law on that was not read. The protection is in the product: the banner, the source and the date under every figure | Keep the banner until every figure is real. Say no more in marketing than the terms do |
| 9 | "18 or over", not checked | Notice, 16. Terms, 6 | Google forbids a product "likely to be accessed by" under-18s. Saying is not checking | Checklist, task 12 |
| 10 | Who is named as running Burro | Notice, 1. Terms, 13 | GOV.UK says a sole trader must put their name on "official paperwork", and does not say whether a website is that. The e-commerce regulations, as read, ask a website for a name and a geographic address. Whether they reach a website that is free was not read. If either applies, a name and an address become public | Checklist, task 1 |
| 11 | Which law and which courts | Terms, 12 | The wording is common. It was not read at a source | A fixed-fee review |
| 12 | Census figures beside a tool that ranks areas | Notice, 18 | The Equality Act was not read. [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md) takes the risk knowingly | Advice, or a complaint |
| 13 | No cookie banner is shown | Notice, 2 | That the website sets no cookie and stores nothing is held by tests. That no banner is then needed is an inference. The ICO's page, as read, did not say | Low. Read the ICO's guidance in full |

## The cheapest ways to have them read

No public price for a fixed-fee review of a privacy notice was found. No web search was made: only known addresses were opened.

| Way | What you get | Cost, as read | Read |
|---|---|---|---|
| Ask the ICO | An answer to a question, by phone, live chat or a form. 0303 123 1113, Monday to Friday, 9am to 5pm. The page does not offer to review a document | Free | Read, at <https://ico.org.uk/for-organisations/advice-for-small-organisations/contact-us/> |
| The ICO's privacy notice generator | A notice made from your answers, to hold against this one. "designed for sole traders and start-ups, as well as small and medium-sized businesses and charities". Updated 10 July 2026 | Free | Read, at <https://ico.org.uk/for-organisations/advice-for-small-organisations/privacy-notices-and-cookies/create-your-own-privacy-notice/> |
| A university law clinic: King's Legal Clinic | Advice from students supervised by lawyers, as "a written letter of advice, normally within two weeks of the initial interview". Six areas. Intellectual property is one. Data protection is not listed | Free | Read, at <https://www.kcl.ac.uk/legal-clinic> |
| A university law clinic: qLegal, Queen Mary | Not checked | | Not read |
| LawWorks clinics | "free initial advice to individuals". Not for a business | Free | Read, at <https://www.lawworks.org.uk/legal-advice-individuals>. Not a route for Burro |
| British Library Business and IP Centre | "Free start-up workshops, events, resources and one-to-ones", and sessions with intellectual property specialists. The page does not name data protection | Free | Read, at <https://www.bl.uk/business-and-ip-centre> |
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
| 1. Put three questions to the ICO, in writing, and keep the answers | Free | 1 |
| 2. Run the ICO's generator and hold its notice against this one. Note what it asks that this one does not answer | Free | 1 |
| 3. Apply to a clinic, with the notice and the list of risks above | Free. A wait | 2 |
| 4. When there is revenue, buy a fixed-fee review of the privacy notice first | A quote | |

The three questions:

| # | Question |
|---|---|
| 1 | People may type something sensitive into a free-text box. We keep none of it. We send it to a processor that keeps it for up to 55 days. Must we ask for explicit consent before the first sentence, or is a clear notice enough? |
| 2 | We keep no record of who visits. If consent is needed, how do we show it was given? |
| 3 | We hold nothing that says whose a search was. May we rely on Article 11 when a person asks for their data? |

## What disagrees with these drafts

Each is outside `docs/legal/`, so none was changed.

| Where | What it says | What was read |
|---|---|---|
| `apps/web/src/content/site.ts`, `WORDS_LINE`, and the test that holds it | A provider "may keep it for up to 30 days, or longer if it is flagged" | Google keeps text for 55 days. Anthropic keeps flagged text for up to 2 years |
| [ADR 0005](../adr/0005-raw-prompts-are-never-stored.md) | "The provider retains inputs for up to 30 days, longer if flagged." | The same. [gemini.md](../research/models/gemini.md) says so too |
| [PLAN.md](../PLAN.md), section 9 | "The only place raw text leaves Burro is the Claude API call." | The founder has decided no single provider |
| [PLAN.md](../PLAN.md), section 10 | Plans a folder `docs/policies/` | These are in `docs/legal/` |
| [deploy/README.md](../../deploy/README.md) | Vercel's log holds "the path, the query string, the status and the browser's name" | Vercel's page also says it can match a request by internet address |
| [deploy/README.md](../../deploy/README.md) | Fly.io is a processor and must be named | No agreement with Fly.io was found. Its list of legal documents was read a second time on 23 September 2026, through an extraction, and named a privacy policy, supplemental terms and terms of service. The terms of service were not read in full for one |
| [deploy/README.md](../../deploy/README.md) | The model provider keeps inputs "for up to 30 days", and the key to set is `ANTHROPIC_API_KEY` | Google keeps text for 55 days. The founder has decided no single provider |
| `services/api`, as wired | It can call Anthropic only, and a key alone switches the model on | The founder has decided Google comes first. `services/api/src/burro_api/providers/` holds four adapters that are not wired in. [models.md](../design/models.md), section 8, lists what wiring them changes |
| `services/api`, `within` in `routes/interpret.py` | A call to a model that is late is left to finish | The notice can promise no fixed time that a sentence is held in memory. The adapters in `providers/` set one deadline for the whole call. They are not wired in |
| `services/api`, `calls.py` and `logs.py` | A status of `policy_redirect` is kept in the call record and written to the log | ADR 0011 leaves four fields of the log line to the founder. The status is not one of the four |
| `services/api` | No route deletes one shared link | A person may ask for one to be deleted |
| `apps/web` | No step asks before a sentence is sent. No page holds a privacy notice or terms. The accessibility page has no address for a report | Each is needed before launch |
| `docs/research/models/claude.md` | Its name differs only by case from the name of an instructions file for coding agents, so a tool that ignores case may load it as instructions. It is a report | A name such as `anthropic.md` would stop that |
| [accounts-compliance.md](../research/reports/accounts-compliance.md) | Legitimate interests for a typed sentence, and no step that asks | Risk 1 |

## How to keep them true

| Rule | Why |
|---|---|
| Never publish a sentence marked `[NOT BUILT]` or `[FOUNDER]` | It is not true yet |
| Before publishing, check every `[SETTING]` at the host or the provider, and take the mark off only then | The code cannot hold it. A setting changed in a dashboard makes the notice false, and no test fails |
| When a file named in Appendix B changes, read the sentence beside it | A change to the code can make the notice false |
| When a provider, a host or a period changes, change the notice in the same change | The notice names them |
| Hold the numbers with a test: 30 days, 10,000, 50,000, 600 characters, 6 seconds | The website's copy is held to the decision records that way already |
| Read each provider's page again on the day of publishing | They change |
| When accounts arrive, write the notice again | Most of what it says of rights will no longer be true. The checklist says what changes |

## What was not read

| What | Standing |
|---|---|
| A web search | None was made. Only known addresses were opened, and addresses found on pages that were read |
| qLegal | Not read |
| LawBite | Not read |
| Rocket Lawyer UK, the ICO's page on data protection officers | Not read |
| An agreement on data processing with Fly.io | None was read. None is on its list of legal documents, at <https://fly.io/legal/> |
| The ICO's page for making a complaint | Only its menus were read. Its postal address is not in the notice for that reason |
| The Competition and Markets Authority's guidance on unfair terms | The page that holds it was read. The 134 pages were not |
| Section 49 of the Consumer Rights Act, the Digital Markets, Competition and Consumers Act 2024, the Equality Act 2010 | Not read |
| Whether the e-commerce regulations reach a website that is free | Not read |
| Article 13 of the UK GDPR | Not read. The ICO's list of what it asks for was |
| The Data Privacy Framework list | Not opened |
| Any template file | The addresses were read. The files were not opened |
| What Fly.io's own systems record of a request | Not said on the pages read |
