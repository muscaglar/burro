# Research behind the plan

Gathered on 2026-09-23, in two passes. Everything here supports [`../PLAN.md`](../PLAN.md). Treat it as a dated snapshot: licences, prices and model line-ups change, so re-check before relying on a specific figure.

## How to read this

| Folder | What is in it |
|---|---|
| `reports/` | One report per domain: recommendations, risks, open questions, claims that were not verified, and a compact list of every source checked |
| `verification/` | Four skeptics tried to refute the claims the plan depends on. Each file lists what was confirmed, what was wrong, and what to check in week one |
| `design/` | Three competing plans (lean, trust, experience), the merged plan, and the critique of it |

## Verification totals

| Area | Confirmed | Partly wrong | Refuted | Not verified |
|---|---|---|---|---|
| Data licences | 9 | 6 | 0 | 3 |
| Claude API | 14 | 2 | 1 | 0 |
| Platform and rules | 13 | 3 | 0 | 1 |
| Routing feasibility | 11 | 6 | 0 | 1 |
| **Total** | **47** | **17** | **1** | **5** |

## Limits of this research

- Web searches were made in part of the first pass. Later checks opened known addresses only.
- Few files were opened, and none is in the repository. Each report says which. The contents of the London bus timetable feed are unmeasured.
- Reddit, the EHRC site and parliament.uk were not read.
- Most pages were read through a reader that summarises. Re-check any quoted wording against the source before it goes into a legal document.
- Of a site whose terms forbid reading by a program, a report says only that a page was read, and on what day. A person opens each such page in a browser before anything rests on it.
- Nothing here is legal advice.

Throughout this folder, "not read" means that a page was not read, for whatever reason. It says nothing about the page, and nothing is implied about its publisher. A report makes no claim about what such a page holds, and a person opens the page before anything rests on it.

## Where the merged plan and the final plan differ

`design/unified.md` is the merged plan as the synthesis agent wrote it. `design/critique.md` found one blocker and fifteen major issues in it. `../PLAN.md` is the final version with those fixes applied, chiefly:

- Legal review was dropped on cost. Open questions are closed by design instead, and no professional has reviewed the result. See ADR 0007.
- Timeline moved from 13 weeks to 18, with founder hours budgeted per phase.
- Costs and quotas planned on the mid-tier model, since the smallest may retire during the build.
- Budget became a soft constraint, because official rent data understates new lets.
- Commute results gained nearest station, lines and on-demand route detail.
- Destination search extended to universities, hospitals and landmarks.
- The attributed Wikipedia excerpt was restored to profiles.
- Two tags renamed for places instead of residents.
- The rule that raw prompts are never logged was made explicit and testable.

## Every page, by folder

Each page is a dated snapshot. [Where to look](../README.md) leads to the guides that are kept up to date.

**`reports/`**: one report for each domain, gathered on 2026-09-23.

| Page | What it is about |
|---|---|
| [accounts-compliance.md](reports/accounts-compliance.md) | Accounts, subscriptions and compliance for a consumer product in the United Kingdom |
| [boundaries.md](reports/boundaries.md) | The gazetteer of neighbourhoods, and the model of geography |
| [housing-cost.md](reports/housing-cost.md) | What homes cost to rent and to buy, by small area |
| [liveability-demographics.md](reports/liveability-demographics.md) | Statistics of liveability and of residents, by small area |
| [llm-architecture.md](reports/llm-architecture.md) | How a model reads a sentence, explains and is evaluated |
| [platform-stack.md](reports/platform-stack.md) | The platform, and how the repository is laid out |
| [poi-vibe.md](reports/poi-vibe.md) | Points of interest and vibe: datasets, licences and methods |
| [transit-routing.md](reports/transit-routing.md) | Travel times and transport data |

**`verification/`**: what four skeptics confirmed, and what they found wrong.

| Page | What it is about |
|---|---|
| [verify-claude-api.md](verification/verify-claude-api.md) | The claims about one provider's API and the cost of a model, held to its pages |
| [verify-data-licences.md](verification/verify-data-licences.md) | The claims about data licences and terms, held to their pages |
| [verify-platform-and-rules.md](verification/verify-platform-and-rules.md) | The claims about platform vendors, the app store's rules and regulation |
| [verify-routing-feasibility.md](verification/verify-routing-feasibility.md) | The claims about whether travel times can be worked out |

**`design/`**: three competing plans, the merged plan and the critique of it.

| Page | What it is about |
|---|---|
| [critique.md](design/critique.md) | What a critic found in the merged plan |
| [proposal-experience.md](design/proposal-experience.md) | The proposal from the experience of a person who uses it |
| [proposal-lean.md](design/proposal-lean.md) | The proposal from the least that could be built |
| [proposal-trust.md](design/proposal-trust.md) | The proposal from trust, correctness and legal safety |
| [unified.md](design/unified.md) | The three proposals merged into one plan |

**`vibes/`**: what could stand behind each kind of vibe: the sources, their licences and their limits.

| Page | What it is about |
|---|---|
| [community.md](vibes/community.md) | Places to meet and things to join |
| [connectivity.md](vibes/connectivity.md) | Broadband, mobile and other services |
| [culture.md](vibes/culture.md) | Cultural venues, and what highly ranked can honestly mean |
| [fitness.md](vibes/fitness.md) | Gyms, studios, pools, courts and pitches |
| [green.md](vibes/green.md) | Green space and leafiness |
| [grit.md](vibes/grit.md) | Crime, the street, and deprivation |
| [people.md](vibes/people.md) | Who lives there, and cultural background |

**`models/`**: what each provider of a model says of itself, from its own documents.

| Page | What it is about |
|---|---|
| [anthropic.md](models/anthropic.md) | Anthropic Claude, from its own documents |
| [deepseek.md](models/deepseek.md) | DeepSeek, from its own documents |
| [definitions.md](models/definitions.md) | What the providers' published definitions say |
| [gemini.md](models/gemini.md) | Google Gemini, from its own documents |
| [openai.md](models/openai.md) | OpenAI, from its own documents |

**`data/`**: what each publisher's file held once it was fetched, and what each build of London showed.

| Page | What it is about |
|---|---|
| [brands.md](data/brands.md) | Brands: the chains of grocers, gyms and coffee, on the real file |
| [by-hand-files.md](data/by-hand-files.md) | The four files a person saved on 2026-09-24 |
| [cafes-gyms-and-pubs.md](data/cafes-gyms-and-pubs.md) | Cafes, gyms and pubs: what the real file gave |
| [census-2021-tables.md](data/census-2021-tables.md) | Census 2021 tables for the area page: what was read |
| [community-places.md](data/community-places.md) | Places of worship and centres nearby: what is built, and what it waits on |
| [culture-and-community-on-the-real-file.md](data/culture-and-community-on-the-real-file.md) | Culture, places of worship and centres: what the real file gave |
| [culture-venues.md](data/culture-venues.md) | Culture nearby: what is built, and what it waits on |
| [first-vibes-on-london.md](data/first-vibes-on-london.md) | The first vibes on London |
| [food-register.md](data/food-register.md) | The food hygiene register: what the files hold, and what was built on them |
| [heritage.md](data/heritage.md) | Conservation areas and listed buildings |
| [high-streets.md](data/high-streets.md) | High streets, and the second try at Village feel |
| [incidents.md](data/incidents.md) | Recorded criminal damage and anti-social behaviour |
| [journey-estimate-held-against-timetables.md](data/journey-estimate-held-against-timetables.md) | The journey estimate, held against the timetables |
| [land-use.md](data/land-use.md) | Land use, for works and warehouses, gardens and woodland |
| [m1-files.md](data/m1-files.md) | What the files of the first real build hold |
| [m1-first-build.md](data/m1-first-build.md) | The first real build of London |
| [m2-files.md](data/m2-files.md) | What the files of the second build hold |
| [m2-second-build.md](data/m2-second-build.md) | The second real build of London |
| [m3-files.md](data/m3-files.md) | What the files of names and borders hold |
| [m3-first-draft.md](data/m3-first-draft.md) | The first whole draft of London's areas |
| [overture-places.md](data/overture-places.md) | Overture Places in London: what a first look found |
| [postcodes.md](data/postcodes.md) | The postcode lookup, and what it places |
| [prices.md](data/prices.md) | What homes sold for, the council tax bands, and household income |
| [primary-schools.md](data/primary-schools.md) | Primary schools close by |
| [sources-pages-read.md](data/sources-pages-read.md) | Pages read for the source-by-source plan |
| [stations.md](data/stations.md) | The nearest station, and the stations as places |
