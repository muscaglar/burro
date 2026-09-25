# The launch checklist

**Draft. Not legal advice.** Written on 23 September 2026 from the public guidance of the Information Commissioner's Office (ICO), GOV.UK and legislation.gov.uk, and brought up to 24 September 2026. Nobody qualified has read it.

This is what the founder must do before launch that a document cannot do for them. It is in the order of what blocks a public launch. The plan says no outside person reaches a language model until the privacy notice, the ICO registration and the provider's agreement are in place ([PLAN.md](../PLAN.md), section 11). This list is how to get there.

| Mark | Meaning |
|---|---|
| Read | Read at the address given, through a reader that extracts of the page. On 23 September 2026 unless the row gives another day. Check the wording at the address before relying on it |
| Read twice | Read twice at the address, asked in different words each time |
| Not read | The page was not read. What is said of it is an inference or a recollection |
| Hours | The founder's own time. Every figure is an estimate made for this draft, unless it says the ICO gave it |

Most ICO pages read carried this notice: "Due to changes made by the Data (Use and Access) Act, this guidance is under review and may be subject to change." The ICO says all of that Act's data protection provisions are in force as of 19 June 2026. Read, at <https://ico.org.uk/about-the-ico/what-we-do/legislation-we-cover/data-use-and-access-act-2025/the-data-use-and-access-act-2025-what-does-it-mean-for-organisations/>.

## In short

There are four stages. Each stage blocks what is named at its head, and nothing in a later stage can be switched on before the stage above it is done.

"Yes" in the third column means that the page named in the task's own section says "must", as it was read. It is this draft's reading of a regulator's guidance. It is not advice, and it is not a reading of the law itself.

### Stage 1: blocks any public launch

The website, on real data about places, with no language model and no figure about residents.

| # | Task | Must it be done | Hours | Cost | Waits on someone else |
|---|---|---|---|---|---|
| 1 | Decide who runs Burro: a person or a company | Yes, in practice. Every other step needs a name | Not estimated | Not read | A company takes time to register |
| 2 | Pay the data protection fee to the ICO | Yes, unless the ICO's checker says exempt | 0.5 | GBP 52 a year, or GBP 47 by direct debit | No |
| 3 | Choose the lawful basis for each use, and write it down | Yes | 3 | 0 | No |
| 4 | Have an agreement with each company that handles data for Burro | Yes | 3 | 0 to the cost of a plan | **Yes. Fly.io must answer** |
| 5 | Cover each transfer out of the UK | Yes | 2 to 6 | 0 | No |
| 6 | Publish the notice and the terms, and link them where a person types | Yes | 1, and the build | 0 | The build |
| 7 | Put the term on letting and selling where a business will see it | This draft's reading. No page says "must" | 0.5, and the build | 0 | The build |
| 8 | Read the equality regulator's guidance for service providers | These drafts do not rest on it, so a person must read it | 1 | 0 | No |
| 9 | Keep a record of processing | Yes, in part | 2 | 0 | No |
| 10 | Be ready to answer a request from a person | Yes | 1.5 | 0 | The build, for deleting one link |
| 11 | Have a way to take a complaint | Yes. "there are no exemptions to this" | 1 | 0 | No |
| 12 | Have a plan for a breach | Treat it as yes. What was read is a duty to report a breach and to keep a record of one, not a duty to hold a plan | 1.5 | 0 | No |
| 13 | Hold the settings at each host | Yes, to keep the privacy notice true. No rule was read that says so | 0.5 | 0 | No |
| 14 | Write down why Burro is not for children | Should | 1 | 0 | No |

### Stage 2: blocks turning a language model on

A sentence in a person's own words is seldom one the rules can apply. So a launch that reads what people type in their own words needs this stage.

| # | Task | Must it be done | Hours | Cost | Waits on someone else |
|---|---|---|---|---|---|
| 15 | Check what people are told of the provider, accept its terms, and hold its settings | Yes. The service turns no model on until a person has | 1.5 | 0. A cap on spending is the founder's to set | No |
| 16 | Decide how a sensitive sentence is handled, and have the step built | Yes | 1, and the build | 0 | The build |
| 17 | Write a data protection impact assessment | Treat it as yes | 8 | 0 | No |

The hours of tasks 4 and 5 include one provider.

### Stage 3: blocks showing or ranking on figures about residents, and counting recorded crime

| # | Task | Must it be done | Hours | Cost | Waits on someone else |
|---|---|---|---|---|---|
| 18 | Hold the figures about residents and about recorded crime to what was decided | This draft's reading | 2, and the build | 0 | The build |

### Stage 4: after launch

| # | Task | Must it be done | Hours | Cost |
|---|---|---|---|---|
| 19 | Look again every three months | Should | 2 each time | 0 |

| | Hours | Cost |
|---|---|---|
| Stage 1, without task 1 | 18.5 to 22.5 | GBP 47 to 52 |
| Stage 2 | 10.5 | 0 |
| Stage 3 | 2 | 0 |
| **Total before a launch with all three**, without task 1 | **31 to 35** | **GBP 47 to 52** |

### What to start today, because it waits on someone else

| What | Why it waits |
|---|---|
| Task 1, if a company is chosen | Registering one is not in the founder's hands alone |
| Task 4, the question to Fly.io | No agreement on data processing was found. Only Fly.io can say whether one exists |
| The four questions to the ICO, in [README.md](README.md) | An answer in writing takes days |
| An application to a law clinic | "normally within two weeks of the initial interview", at the one clinic that was read |

### What is built, and what each stage still needs built

| Stage | Built | Not built |
|---|---|---|
| 1 | No cookie, no storage, no analytics, nothing from another origin. Typed text in the body of a request only. A log that holds a fixed list of fields | A page for the notice and a page for the terms. A link to the notice beside the box. A way to delete one shared link. A limit on requests. An address on the accessibility page for a report |
| 2 | A key alone turns nothing on. The notice beside the box is the service's own, is shown before anything is typed, and no sentence is sent before it. No provider's library | A step that asks before a sentence is sent. Code that refuses DeepSeek on a release that is not made up. That nothing a model reads is applied until the person chooses it |
| 3 | Nothing can search, sort or filter by who lives somewhere. A release of a real place is refused if it holds a count of residents, or a Gritty that counts recorded incidents | The census table, with its floor of 1,000 people. The measures of age and of households. The one Gritty. The words of the methods page. The written rule of the proxy audit stood here until 25 September 2026, when the audit was dropped |

---

# Stage 1: blocks any public launch

## 1. Decide who runs Burro

| | |
|---|---|
| Why | The ICO's list of what a privacy notice holds starts with the "name and contact details of your organisation". The fee is paid in a name. Each company's terms are accepted in a name. Who may accept them for a business was not read at a source |
| A sole trader | GOV.UK: "You must include your name and business name (if you have one) on official paperwork". Read, at <https://www.gov.uk/become-sole-trader/choose-your-business-name>. The page does not say whether a website is official paperwork |
| A limited company | GOV.UK says it must show on its website "the company's registered number", "its registered office address", "where the company is registered" and "the fact that it's a limited company". Read, at <https://www.gov.uk/running-a-limited-company/signs-stationery-and-promotional-material> |
| What to weigh | A sole trader's name and address may become public, on the website and on the ICO's register. A company's registered office is public in its place. The ICO's register was not opened, so what it shows was not read. What each costs was not read |
| Hours | Not estimated |

## 2. Pay the data protection fee

| | |
|---|---|
| Who must pay | "organisations (including sole traders) that use personal information need to pay a data protection fee, unless they are exempt." Read, at <https://ico.org.uk/for-organisations/data-protection-fee/> |
| Check first | The ICO's self assessment. The ICO says it takes about 10 minutes. Read, at <https://ico.org.uk/for-organisations/data-protection-fee/data-protection-fee-self-assessment/> |
| What it costs | Tier 1, GBP 52 a year: turnover of GBP 632,000 or less, or 10 staff or fewer. Tier 2, GBP 78. Tier 3, GBP 3,763. Read, at <https://www.legislation.gov.uk/uksi/2018/480/regulation/3>, as amended to 17 February 2025 |
| Direct debit | The charge "is reduced by £5.00 for a data controller that makes payment of the charge by direct debit". So GBP 47. Read, at the same address |
| How long it takes | "It takes about 15 minutes." Read, at <https://ico.org.uk/for-organisations/advice-for-small-organisations/getting-started-with-gdpr/data-protection-fee-what-you-need-to-do/> |
| Where to pay | <https://ico.org.uk/for-organisations/data-protection-fee/>. The ICO's short addresses are `ico.org.uk/fee`, `ico.org.uk/fee-checker` and `ico.org.uk/no-fee`. Read |
| If it is not paid | "If you need to pay and don't pay, you could be fined." The amount was not read |
| Help | 0303 123 1113, option one, Monday to Friday, 9am to 5pm. Read |
| After | Put the registration number in the privacy notice, section 1. Renew each year |
| Hours | 0.5 |

The plan budgets GBP 52. That is tier 1, and it agrees with what was read.

## 3. Choose the lawful basis for each use, and write it down

| | |
|---|---|
| The rule | "You must determine your lawful basis before you start using the personal information and you must document it." Read, at <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/a-guide-to-lawful-basis/>, updated 2 April 2026 |
| It is hard to change later | "You should not swap to a different lawful basis at a later date without good reason. In particular, you can't usually swap from consent to a different basis." Read, same page |
| The draft | [privacy-notice.md](privacy-notice.md), section 11. It is a proposal. The choice is yours |
| Where it rests on legitimate interests | Write a short assessment for each. The ICO calls it "a type of light-touch risk assessment" with three parts: purpose, necessity, balancing. "You should record your LIA". Read, at <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/a-guide-to-lawful-basis/legitimate-interests/> |
| Template | The ICO's sample, at <https://ico.org.uk/media2/kz5jih4c/gdpr-guidance-legitimate-interests-sample-lia-template.docx>. The address was taken from a link on the page. The file was not opened |
| Figures about areas | This draft reads a share for an area of several thousand people as no personal data, so it proposes no basis for holding one. [The reading](residents-crime-and-equality.md), section 9, point 5, says what another reading would change |
| Hours | 3: one to choose, two to write four short assessments |

## 4. Have an agreement with each company

The rule: "Whenever a controller uses a processor to process personal data on their behalf, a written contract needs to be in place between the parties." Read, at <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/guide-to-accountability-and-governance/contracts/>. The page does not say whether terms accepted online are enough.

| Company | What for | Stage | Where the agreement is | How it is accepted | Read |
|---|---|---|---|---|---|
| Fly.io | Runs the service | 1 | **Not found.** No page was read at `https://fly.io/legal/data-processing-addendum/`. The list at <https://fly.io/legal/> names a privacy policy, terms of service and supplemental terms, and no agreement on data processing. The supplemental terms say nothing of it | Ask Fly.io in writing. Its privacy policy gives `support@fly.io` | Not found |
| Vercel | Serves the website | 1 | <https://vercel.com/legal/dpa>, updated 17 March 2026 | "This Addendum shall become legally binding upon Customer entering into the Agreement". It applies to the Pro and Enterprise plans | Read |
| The company that holds the domain's records | Names | 1 | `[FOUNDER: which company]` | | Not read |
| The mail provider | Requests and complaints | 1 | `[FOUNDER: which company]` | | Not read |
| Google, Gemini API | Reads a sentence. It comes first | 2 | <https://business.safety.google/processorterms/> | It comes with the terms of the paid service. Billing must be on | Read in [gemini.md](../research/models/gemini.md) |
| Anthropic, Claude API | Reads a sentence | 2 | <https://www.anthropic.com/legal/data-processing-addendum> | "When you accept Anthropic's Commercial Terms of Service, you also accept our DPA." | Read in [anthropic.md](../research/models/anthropic.md) |
| OpenAI, API | Reads a sentence | 2 | <https://openai.com/policies/data-processing-addendum/> | With the Services Agreement. A signed copy can be asked for through a form | Read in [openai.md](../research/models/openai.md) |
| DeepSeek, API | Reads made-up sentences only. **Never what real people type**: decided on 24 September 2026 | Never | **None is published** | | Not found. [deepseek.md](../research/models/deepseek.md) |
| Later: a database, map tiles, error reports | | | | | Not read |

| | |
|---|---|
| What to do for each | Open the address. Save a dated copy. Note who accepted it and when. The research says the same of every licence page |
| Fly.io | None was found. That is not the same as none existing: its terms of service were not read in full, and a second look at its list of legal documents on 23 September 2026, through an extraction, named the same three documents and no agreement. Ask Fly.io. Until it answers, the choice is the founder's: keep real people's data off Fly.io, or accept the gap in writing |
| Vercel | The free plan is not covered by the agreement as read. [deploy/README.md](../../deploy/README.md) already plans for Pro |
| Only the provider in use | One provider reads at a time. Only its agreement is needed |
| Hours | 3 |

## 5. Cover each transfer out of the UK

| | |
|---|---|
| What counts | Sending personal data to a separate company outside the UK. The ICO's three questions: does the UK GDPR apply, are we starting the transfer, is the receiver a separate legal entity. Read, at <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/international-transfers-a-guide/>, dated 15 January 2026 |
| What covers one | UK adequacy regulations, or an appropriate safeguard, or an exception. The safeguards named are the international data transfer agreement, the international data transfer addendum, and binding corporate rules. Read, same page |
| With a safeguard, a risk assessment too | You "must also ensure that you have completed a transfer risk assessment (TRA)". Read, same page |
| The United States | From 12 October 2023 a UK business may send data to a United States company "certified to the 'UK Extension to the EU-US Data Privacy Framework'". Read, at <https://www.gov.uk/government/publications/uk-us-data-bridge-supporting-documents/uk-us-data-bridge-factsheet-for-uk-organisations>, published 21 September 2023 |
| What to check | That the company is "an active DPF participant", and that it "has signed up to the UK Extension". The list is at <https://www.dataprivacyframework.gov/s/participant-search>. It was not opened for this draft |
| Sensitive data over that route | It "must be appropriately identified as sensitive to US organisations when transferred". Read. How Burro would do that for a sentence it has not read is not known |
| Any country | Google says what is typed may be handled in "any country in which Google or its agents maintain facilities". The founder accepted on 24 September 2026 what Google keeps. The risk assessment still has to say where it may go |
| China | No safeguard is named by DeepSeek. It is never used for what real people type |

| Company | Stage | Route to check | Hours |
|---|---|---|---|
| Fly.io | 1 | The Data Privacy Framework list. Its privacy policy claims the UK Extension | 0.5 |
| Vercel | 1 | The addendum in its agreement, and a risk assessment | 2 |
| Google | 2 | The Data Privacy Framework list, for Google LLC | 0.5 |
| Anthropic | 2 | The UK Addendum in its agreement, and a risk assessment. The contract is with a company in Ireland | 2 |
| OpenAI | 2 | The UK Addendum in its agreement, and a risk assessment | 2 |

Only the companies in use need doing. With Fly.io, Vercel and one provider, plan on 2 to 6 hours.

## 6. Publish, and link where a person types

| | |
|---|---|
| The rule | Privacy information must be given "at the time when personal data are obtained", in an "easily accessible form". Posting it on a website is not enough by itself. Read, at <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/the-right-to-be-informed/when-should-we-provide-privacy-information/> |
| What is needed | A page for the notice. A page for the terms. A link to the notice beside the box. Links to both in the footer. On the page of the notice, the service's own notice of who reads what is typed, shown as it is served |
| What is built | The notice beside the box, which the service serves and the website shows before anything is typed. The methods page shows it too, with the pages each sentence was read on |
| What is not | A page for the privacy notice and a page for the terms. The website has pages for methods, sources, vibes and accessibility |
| Before publishing | Take every mark out of the two drafts: fill each `[FOUNDER]`, check each `[SETTING]` at the host, and publish no sentence marked `[NOT BUILT]` |
| Hours | 1, to read the pages once they are built |

## 7. Put the term on letting and selling where a business will see it

| | |
|---|---|
| What it is | Section 7 of the [terms of use](terms-of-use.md) forbids anyone who lets, sells or manages homes from using Burro to steer people by who they are |
| Why | It is the main risk in [the reading of the equality law](residents-crime-and-equality.md), section 8. The Act says a person must not "knowingly help another" to discriminate, and gives a defence to one who "relies on a statement" that the act is lawful, where that is reasonable. Read twice, at <https://www.legislation.gov.uk/ukpga/2010/15/section/112> |
| What is needed | The terms published, with a link in the footer of every page. A line on the page of an area, beside the census table, that says what the table may not be used for |
| What is not settled | Whether a term that nobody signs is a statement Burro may rely on. `[SOLICITOR]` |
| Never | Sell Burro to agents or landlords as a way to find areas by who lives there. Show a home. Take money from anyone who lets or sells |
| Hours | 0.5, to read the pages once they are built |

## 8. Read the equality regulator's guidance

| | |
|---|---|
| What | The guidance of the Equality and Human Rights Commission for service providers, and its code of practice on services, public functions and associations |
| Why | It is the regulator's own account of what a service-provider must not do. None of it is in these drafts: **it was not read**. The drafts rest on the Act as printed |
| Where | <https://www.equalityhumanrights.com>. Open it in a browser |
| What to look for | What it says of estate agents and letting agents. What it says of steering people towards or away from an area. Whether it says anything of a website, or of information about an area. What it says a service-provider may rely on when someone else uses its service to discriminate |
| Then | Put what it says beside [the reading](residents-crime-and-equality.md), sections 7 to 9, and change what differs |
| Hours | 1 |

## 9. Keep a record of processing

| | |
|---|---|
| Who must | "Most organisations must document their processing activities to some extent." An organisation with fewer than 250 staff need document only processing that is "not occasional", or "likely to result in a risk to the rights and freedoms of individuals", or that involves "special category data or criminal conviction and offence data". Read, at <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/documentation/who-needs-to-document-their-processing-activities/> |
| Does Burro | Yes. Reading sentences is what it does every day, and a sentence may hold special category data |
| Form | "must be in writing; this can be in paper or electronic form" |
| Template | <https://media2.ico.org.uk/for-organisations/documents/2172937/gdpr-documentation-controller-template.xlsx>. The address was read from the page. The file was not opened |
| Hours | 2 |

A start, to copy into the template. Every row is from the privacy notice.

| Activity | Whose data | What data | Why | Lawful basis | Who receives it | Leaves the UK | Kept for |
|---|---|---|---|---|---|---|---|
| Reading a typed sentence | Visitors | Free text, up to 600 characters. May hold special category data | To turn it into settings | Section 11 of the notice | Fly.io. The model's provider, if one reads. The settings go with it only if the service is set to send them, and then without the places to reach | Yes | Not kept by Burro. The provider's period |
| Finding a place by name | Visitors | What is typed in the box for a place, as it is typed, up to 80 characters | To offer places to pick from | Legitimate interests | Fly.io. Never a model | Yes | Not kept |
| Ranking from settings | Visitors | Renting or buying, budget, places to reach and journey times, weights, areas ruled in or out | To answer a search | Legitimate interests | Fly.io | Yes | Not kept |
| A shared link | Visitors who make one | Settings, with places made coarse by default | To open the search again | Legitimate interests | Fly.io | Yes | `[FOUNDER: a period]`. Today, until the service restarts |
| Log lines and call records | Visitors | Counts, codes, times to the second, the name of the provider. No identifier. A code can say a request was about health services, or about who lives somewhere | To run the service | Legitimate interests | Fly.io | Yes | 7 days, and 30 days |
| Serving pages | Visitors | Internet address, browser's name, page asked for. The address of an area's page or of a comparison names the areas | To serve the website | Legitimate interests | Vercel | Yes | 1 day |
| Email | People who write | Address, name, message | To answer | Legitimate interests, legal obligation | `[FOUNDER: the mail provider]` | `[FOUNDER: where the mail provider keeps it]` | `[FOUNDER: a period]` |

Figures about areas are not in the record. This draft reads them as about no person. If the founder takes the other view, add a row for them.

## 10. Be ready to answer a request from a person

| | |
|---|---|
| How long | "without undue delay and at the latest within one month of receipt of the request". Two more months "if the request is complex". Read, at <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/right-of-access/what-should-we-consider-when-responding-to-a-request/>, updated 8 December 2025 |
| Cost to the person | "In most cases, you cannot charge a fee" |
| Proof of who they are | "You can ask for enough information to judge if the requester ... is the person whom the information is about." The clock does not start until it arrives |
| How hard to look | "you only have to make reasonable and proportionate searches". Read, on the ICO's page about the Data (Use and Access) Act |

What to do when one arrives:

| Step | What |
|---|---|
| 1 | Write down the date it arrived. The month starts then |
| 2 | Reply within a few days to say it has arrived |
| 3 | Look in the two places Burro holds anything that can be found: the mailbox and the shared links. Log lines and call records hold nothing that says whose they are |
| 4 | If they give a shared link, send what is stored under it, and delete it if they ask. `[NOT BUILT: deleting one link. Nor is there a way to read what is stored under a link but to open it, and opening it does not show the time it was made]` |
| 5 | If they wrote to Burro before, send them their messages and your replies |
| 6 | If nothing is held, say so, and say why: Burro keeps no words, no searches and no record of who visited. Point to section 14 of the notice |
| 7 | If they ask about what a model's provider holds, say which provider was in use, what the notice beside the box said of it, and that Burro cannot tell it which text was theirs |
| 8 | If they ask what Burro holds about them as someone who lives in an area, say that it holds published counts for areas and nothing about any person. Point to section 18 of the notice |
| 9 | Keep a note of the request, the date and the answer |

| | |
|---|---|
| Hours to prepare | 1.5: a mailbox, two standard replies, a place to keep the notes |
| Hours for each request | 0.5 to 1 |

## 11. Have a way to take a complaint

| | |
|---|---|
| The rule | "You must have a process for handling data protection complaints within your organisation - there are no exemptions to this." Read, at <https://ico.org.uk/for-organisations/how-to-deal-with-data-protection-complaints/>, updated 8 May 2026 |
| What it must do | "give people a way of making data protection complaints to you", "acknowledge receipt of complaints within 30 days", "without undue delay, take appropriate steps to respond", and "without undue delay, tell people the outcome" |
| Is an email address enough | Yes, as read. The ICO says you could use "an email address for people to submit complaints to" or a form |
| Tell people | "You must tell people they can complain to you, as well as to us". The privacy notice, section 15, does |
| A complaint about how an area is shown | It is not a data protection complaint, and it matters as much. [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md) names a complaint from residents as a thing that would change the decision to show the census table. Keep it, answer it, and bring it to the next look at the decision |
| Hours | 1 |

## 12. Have a plan for a breach

| | |
|---|---|
| What one is | "A breach of security leading to the accidental or unlawful destruction, loss, alteration, unauthorised disclosure of, or access to, personal data." Read, at <https://ico.org.uk/for-organisations/report-a-breach/personal-data-breach/personal-data-breaches-a-guide/> |
| When to tell the ICO | Within "72 hours of becoming aware of the breach, where feasible", if it "is likely to result in a risk to rights and freedoms" |
| When to tell the people | "If the breach is likely to result in a high risk ... you must also inform those individuals without undue delay." Burro cannot write to its visitors. It has no address for them. A notice on the website is the only way |
| Keep a record | "You must also keep a record of any personal data breaches, regardless of whether you are required to notify." |
| What a company owes you | A processor "must inform you without undue delay as soon as it becomes aware". Anthropic says 48 hours. Read in the report |
| Where to report | <https://ico.org.uk/for-organisations/report-a-breach/> |

What a breach could be, for Burro:

| What happens | What is exposed | First thing to do |
|---|---|---|
| A change makes the service log what people type | Sentences, in Fly.io's log for 7 days | Roll back. The privacy tests exist to stop this |
| Someone reads the memory or the store of shared links | Settings, with exact places where a sender chose them | Restart, which clears every link. Say so on the website |
| Someone gets into the mailbox | Names, addresses, messages | Change the password. Tell those people |
| A provider or a host has a breach | What that company held | Ask what was taken. Decide within 72 hours whether to report |
| A model key leaks | Money, not data | Revoke the key in the provider's console and make another. Do not try to clean it up |

| | |
|---|---|
| Hours | 1.5, to write one page: who decides, where the record is kept, the ICO's address |

## 13. Hold the settings at each host

These keep the privacy notice true. Each is from [deploy/README.md](../../deploy/README.md). None was tested. The notice marks each sentence that rests on one with `[SETTING]`.

| Company | Setting | Why |
|---|---|---|
| Burro's own service | No provider named in `BURRO_MODEL_PROVIDER` until stage 2 is done. `BURRO_MODEL_TIMEOUT_S` left unset, so that the wait is the 6 seconds the notice gives | A key alone turns nothing on. A provider that is named, with its terms accepted and its sentences checked, does |
| Fly.io | One region, London. No log shipper. No metrics add-on that records paths | A path can hold a link's id |
| Vercel | Function region London. Web Analytics off. Speed Insights off. No log drain. No Observability Plus. Toolbar off | The notice says no analytics, and logs for 1 day |
| The domain's records | No proxy in front of the service or the website | A proxy would decrypt what people type |

Hours: 0.5, once the accounts exist.

## 14. Write down why Burro is not for children

| | |
|---|---|
| The rule | The Children's code applies to online services "likely to be accessed by children". A child is "a person under 18". Likely means "more probable than not". Read, at <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/childrens-information/childrens-code-guidance-and-resources/age-appropriate-design-a-code-of-practice-for-online-services/services-covered-by-this-code/> |
| If you think it does not apply | "document and support your reasons for your decision" |
| Google's rule | A product on the Gemini API must not be "directed towards or ... likely to be accessed by individuals under the age of 18". Read twice. Google comes first, so this rule is Burro's too |
| What to write | One page. Burro is for people choosing where to rent or buy. It asks about budgets and journeys to work. Nothing in it is made for children. Say what would change your mind |
| Children's data typed by adults | A parent may name a child's school. That is data about a child. Burro keeps none of it. A provider may. OpenAI asks for zero retention before a child's data is processed. Read in the report |
| Hours | 1 |

---

# Stage 2: blocks turning a language model on

## 15. Check what people are told of the provider, accept its terms, and hold its settings

The service turns a model on only when five things hold, in this order. [ADR 0019](../adr/0019-no-one-provider-and-a-key-alone-turns-nothing-on.md) and [models.md](../design/models.md), section 2, have them in full.

| # | What must hold | Who does it | Hours |
|---|---|---|---|
| 1 | The provider is named, in `BURRO_MODEL_PROVIDER` | Whoever runs the service | |
| 2 | Its key is in the host's store of secrets. Never in a file, a chat or a command line that is recorded | The founder. [models.md](../design/models.md), section 5 | |
| 3 | Its terms are accepted by name, in `BURRO_MODEL_TERMS_ACCEPTED`. That is a statement that the founder has read them and taken them on | The founder | |
| 4 | **A person has opened each address in the provider's entry in `providers/terms.py`, compared each of its eight sentences with the page, put right what differs, and written their name and the day** | The founder, in a browser | 1 |
| 5 | The model is one the adapter was fitted to | Whoever runs the service | |

As the table stands no provider can be turned on: nobody has checked a sentence of any of the four.

What was decided on 24 September 2026:

| Matter | Decided |
|---|---|
| Google keeps what is typed for 55 days, the period cannot be shortened, and its staff may read what it flags | Accepted |
| DeepSeek | Never for what real people type. Do not name it, and do not accept its terms, on a service that real people use. `[NOT BUILT: code that refuses it on a release that is not made up]` |
| What a model may apply | Nothing by itself. The model proposes, the person confirms, code checks |

The settings at the provider. Each is from a report. None was tested.

| Company | Setting | Why |
|---|---|---|
| Google | Billing on before any real sentence. The older API, which stores nothing of its own. Optional logging off. No cache, no files, no search | The free tier may not be used for people in the UK, and lets Google train on text |
| Anthropic | A workspace of Burro's own, with a spend limit. The partner programme off. Never paste a real sentence into the console | Each would keep text longer, or allow training |
| OpenAI | No opt-in to sharing data | The adapter sends `store` as false on every call |
| Any provider | A project of Burro's own, with a monthly cap on spending. No identifier for a person sent with a call | No limit on requests is built, so the cap is what stops a bill. Burro has no identifier to send |

Which of these the code holds:

| Setting | Held by |
|---|---|
| No cache mark is sent, to any provider | `services/api/src/burro_api/providers/`. [models.md](../design/models.md), section 1 |
| OpenAI: `store` false on every call | `providers/openai.py` |
| Google: the API that stores nothing, no cache, no files | `providers/gemini.py`, as its own notes say. Not tried against Google |
| No identifier for a person | `_user` in `services/api/src/burro_api/reader.py` sends the words, and the settings where the service is set to, and nothing else |
| Every other row | In an account or a dashboard. No code can hold it |

Hours: 1.5. One to check the sentences, half to set the account.

## 16. Decide how a sensitive sentence is handled

| | |
|---|---|
| The rule | "In order to lawfully process special category data, you must identify both a lawful basis under Article 6 of the UK GDPR and a separate condition for processing under Article 9." Read twice, at <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/a-guide-to-lawful-basis/special-category-data/> |
| Why it applies | People type their health, their religion and their family into a box that asks how they want to live. [ADR 0005](../adr/0005-raw-prompts-are-never-stored.md) says so |
| The condition this draft proposes | Explicit consent. Which condition fits is a legal question, and nobody qualified has answered it. The ICO says explicit consent "must be confirmed in a clear statement (whether oral or written), rather than by any other type of affirmative action", must "specify the nature of the special category data", and "should be separate from any other consents". Read, at <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/special-category-data/what-are-the-conditions-for-processing/> |
| What that needs | A step on the website, before the first sentence of a visit is sent. It is not built. The privacy notice, section 11, has words for it |
| What is built in its place | The notice beside the box, shown before anything is typed. Where a model reads, it ends with the advice to leave out health, religion and anything else a person would not want kept. It informs. It does not ask |
| The other view | An earlier report in this repository held that no condition is needed if Burro never infers or uses such data. It marked that as its own reading, not confirmed. [README.md](README.md), risk 1 |
| A policy document | The page read names no need for one where the condition is explicit consent |
| Hours | 1 to decide. The step is built by whoever builds the website |

## 17. Write a data protection impact assessment

Is one required? The law and the ICO each give a list. Read, at <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/when-do-we-need-to-do-a-dpia/>.

| Trigger | Does Burro meet it | Reading |
|---|---|---|
| "systematic and extensive evaluation of personal aspects ... on which decisions are based that produce legal effects" | No. Burro evaluates places, and decides nothing about a person | Not read: this draft's reading |
| "processing on a large scale of special categories of data" | Not at launch. Burro does not ask for such data, and keeps none. Scale counts "the number of individuals concerned; the volume of data; the variety of data; the duration of the processing; and the geographical extent" | The same |
| "systematic monitoring of a publicly accessible area on a large scale" | No | The same |
| The ICO's list: "Innovative technology", in combination with another criterion | Arguably yes. A language model reads free text that may hold sensitive data | The same |
| The ICO's list: profiling on a large scale, tracking, data matching, invisible processing, children, biometrics, genetics, denial of a service, risk of physical harm | No | The same |

| | |
|---|---|
| Verdict | Not plainly required, and arguably required. The ICO says "it is good practice to do so". The plan already commits to one. **Treat it as required, and write it before a model is switched on** |
| The steps | "identify the need for a DPIA", "describe the processing", "consider consultation", "assess necessity and proportionality", "identify and assess risks", "identify measures to mitigate the risks", "sign off and record outcomes". Read, at <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/how-do-we-do-a-dpia/> |
| Template | <https://www.ico.org.uk/media2/migrated/2553993/dpia-template.docx>. The address was read from the page. The file was not opened |
| If a high risk is left | "if there is still a high risk, you need to consult the ICO before you can go ahead with the processing." Read |
| What to put in it | The decision records already hold most of it: [0005](../adr/0005-raw-prompts-are-never-stored.md), [0006](../adr/0006-rank-places-not-residents.md), [0011](../adr/0011-nothing-is-kept-for-a-search.md), [0012](../adr/0012-a-closed-vocabulary-and-a-guard-on-the-model.md), [0014](../adr/0014-evidence-first-and-census-figures-shown.md), [0019](../adr/0019-no-one-provider-and-a-key-alone-turns-nothing-on.md), and section 10 of the [contract](../design/contract.md). Add the provider's row from `providers/terms.py`, the transfer, what was accepted of Google on 24 September 2026, and that the proxy audit was dropped on 25 September 2026 |
| Each provider offers help | Google and Anthropic both say they will assist with an impact assessment. Read in the reports |
| Hours | 8 |
| When to redo it | A new provider, a new host, accounts, a database, anything that stores text |

---

# Stage 3: blocks showing or ranking on figures about residents, and counting recorded crime

## 18. Hold the figures about residents and about recorded crime to what was decided

[ADR 0006](../adr/0006-rank-places-not-residents.md) and [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md) record what was decided on 24 September 2026. [The reading](residents-crime-and-equality.md) says what the law asks, as read. Before any such figure is in front of the public:

| # | What | Who | Why |
|---|---|---|---|
| 1 | Task 8 is done, and what the guidance says has been put beside the reading | The founder | The reading rests on the Act alone |
| 2 | Each census entry in the registry is checked by eye: a person opens each page under `evidence_urls`, saves a dated copy, and confirms the licence and the source line | The founder | The registry says so of its census entries |
| 3 | No table is shown for an area of under 1,000 people or 400 households, and a test holds it | The build | A share for a few dozen people can point at a household |
| 4 | Shares only, as whole per cents. No count is printed, stored or served | The build | The registry's condition |
| 5 | A measure of age or of households can be asked for more of, and never for fewer. It is no end of a scale and no filter, and a test holds it | The build | It is the line between describing an area and keeping people out of one |
| 6 | The tests that say no feature describes residents, and that no release holds a count of them, are changed in the same change as the code, to say what is now allowed and nothing more | The build | They are the fence today. A fence that is taken down and not put back holds nothing |
| 7 | Dropped on 25 September 2026. It asked that the written rule of the proxy audit exists: for each measure, the aim it serves, the correlation that triggers a review, and what can be done | The founder, who decided that no proxy audit is run | [ADR 0006](../adr/0006-rank-places-not-residents.md), as amended that day. Rows 5 and 6 stand as they were |
| 8 | Which file feeds the two counts of recorded crime in Gritty is decided, and whether a rate that a publisher divided by residents, or smoothed by the kind of people who live in an area, may feed it | The founder | [The reading](residents-crime-and-equality.md), section 6 |
| 9 | The police file is saved with the crime box ticked and the other two boxes not. A copy that was saved with all three ticked is saved again and deleted. No step opens an outcomes file or a stop and search file, and a test holds that | The founder, at the form. Then the build | Decided on 24 September 2026: the crime files alone are read. A copy that holds the other two is still held |
| 10 | The methods page says what Burro holds about residents, that it holds nothing about any person, and why stop and search is never read | The build | [The reading](residents-crime-and-equality.md), section 11, has words for it |
| 11 | The page of Gritty says that it counts recorded crime, which parts of it do, and that recorded is not the same as committed | The build | The website's words for a vibe that counts recorded crime are built. No real release holds one |

Hours: 2, for rows 2, 8 and 9, and for row 7 before it was dropped.

---

# Stage 4: after launch

## 19. Look again every three months

| What | Why |
|---|---|
| Each provider's terms and retention page, and the day in `checked_on` | Anthropic's and OpenAI's terms can change 30 days after a notice. Read in the reports. A sentence of the notice beside the box can go out of date, and the service holds a provider back where its entry was read after it was checked |
| Each ICO page named here | Most say they are under review |
| The Data Privacy Framework list | A company can leave it |
| Appendix B of the notice, against the code | A change to the code can make a sentence false |
| What is published about areas, by anyone | The ICO says to "monitor changes in what data is publicly available as it may mean it becomes easier to re-identify data". Read twice |
| What people say of the census table and of Gritty | [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md) names a complaint, and evidence that people use the table to avoid areas, as things that would change the decision |
| The ICO fee | It renews each year |

## What changes when accounts arrive

Accounts are in the plan and not built. Today Burro can say it does not know who anyone is. With accounts it cannot.

Every "must" in this table is this draft's expectation of what will be asked. None was read at a source for this draft. Read the ICO's pages again when accounts are designed.

| Today | With accounts |
|---|---|
| Burro holds no identifier | It holds an email address, or an id from Apple or Google |
| It can answer most requests with "we hold nothing we can tie to you" | It must find and send what it holds about an account |
| Nothing to delete | Deleting an account must delete everything under it |
| No cookie and nothing in the browser | A signed-in session needs one or the other. The notice must say so. Whether it needs consent depends on what it is for |
| Two hosts and perhaps a provider | A database and a sign-in service as well, and a company that sends email. An agreement and a transfer check for each |
| A shortlist is not kept | A shortlist says where a named person hopes to live |
| A search is not kept | A saved search would tie a workplace to a named person. [ADR 0011](../adr/0011-nothing-is-kept-for-a-search.md) asks for a new decision first |
| A setting about a place of worship is a wish about a place | Kept under an account, it is a fact about a named person. The reading that it is no special category data would have to be made again |
| A log line cannot say whose it is | It must still not. No account id in a log line or a call record |
| Consent cannot be recorded against a person | It can, and then it must be |
| Age is stated and not checked | Sign-up can ask a person to confirm it |
| A breach exposes settings and codes | A breach exposes people |
| The impact assessment covers a box and a model | It must be written again |
| No marketing | Any email that is not about the account needs consent first |
| The fee | The same tier |

Hours, when the time comes: about 15, most of it the impact assessment and the agreements.

## What was not read

| What | Standing |
|---|---|
| A web search | None was made. Only known addresses, and addresses found on pages that were read, were opened |
| The equality regulator's guidance and code | Not read. Task 8 |
| The ICO's page on data protection officers | Not read |
| The ICO's page for making a complaint | Only its menus were read |
| An agreement on data processing with Fly.io | None was read. None is on its list of legal documents |
| The Data Privacy Framework list | Not opened |
| The ICO's tool for a transfer risk assessment | Not looked for |
| Every template file | The addresses were read. The files were not opened |
| The providers' agreements | Read for the reports, not again for this draft. The retention pages were read again on 23 September 2026 |
| The amount of a fine for not paying the fee | Not on the pages read |
