# London data: a model as researcher

Status: design, 2026-09-23. Nothing here is built. It changes no code, no registry entry and no decision record: each change it needs is listed in section 13 for its owner. No lawyer has read it. Every count, cost and hour is an estimate unless it says "read", and section 15 says what was read.

It applies [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md): a model may help when a release is built, and what it finds enters only with a source that code has fetched and checked. It rests on [PLAN](../PLAN.md), ADRs 0002, 0004, 0006, 0007, 0010 and 0012, [the contract](contract.md) sections 2, 3, 7 and 11, [the vibes design](vibes.md) and the registry.

## 0. What this assumes of the other parts

Five other designs are being written at the same time, a seventh person will join them, and none of their work was seen. If a row is wrong, the second column says what changes.

| # | Assumed | If not |
|---|---|---|
| 1 | The gazetteer gives each of about 450 areas an `area_id`, a polygon, aliases and, where its name came from Wikidata, the item's QID. The join is `area_id` to QID to article | This design keeps its own reviewed table, `area_sources.csv` (section 4) |
| 2 | Every figure is built by the other parts: journeys, cost, features, vibes, the census table. The researcher writes no number and feeds no score | Nothing changes. It still writes none |
| 3 | A file can be added to a release by a change to contract section 2, and `write_release` can ask a source for `profile_text` | Claims wait for that change |
| 4 | One `ModelClient` interface has adapters for Gemini, OpenAI, DeepSeek and Claude, chosen by a setting, with a fake for tests | The researcher needs two adapters of its own |
| 5 | A release is built where the publishers' hosts can be reached, such as a hosted CI runner, and is kept in object storage, not in git | Section 13 says what the build needs |
| 6 | "Go and look" on the area page names things from sources registered for `display` (vibes 5.3). The researcher adds words to a name that is already there, and chooses no name | The "to see" kind is dropped |

## 1. In short

| Question | Answer |
|---|---|
| What the model does | It reads one fetched page and points at sentences worth showing. It returns sentence numbers, a kind from a closed list, and a copy of the words |
| What the model never does | Write a word that is shown. Answer from memory. Find a page. Run when a person is waiting |
| What is shown in the first version | The source's own sentences, word for word, in a marked box, with the publisher, the page, the revision, the licence and the date read |
| What code checks | That the words are in the page as fetched, whole sentences, about this area, still there 30 days apart, and free of words about residents, safety and praise |
| What a person checks | Every claim, before it is in a release. About 45 hours the first time, about 6 a quarter after |
| Sources open today | One for words: English Wikipedia. Four for names and dates: Wikidata, Planning Data, OS Open Greenspace, NaPTAN. Council and heritage pages are shut until a licence is on file |
| Cost of a full build | USD 3 to 50 on any of the four providers, which is under GBP 40. The price does not decide the provider |
| Where a claim appears | The area page only. Never in a result, a reason, a vibe, a filter, a map, a comparison, likeness or a share |
| Coverage | Measured for each release: the share of areas with an accepted claim of each kind, and every refusal counted by check |
| What gates launch | Nothing here. An area with no claim is a counted gap, and its page is complete without one (ADR 0014 lists what an honest result needs, and a claim is not on the list) |

## 2. What may be claimed, and what never is

A claim is one thing a named source says about one area, in the source's words. Each kind passes the four tests of vibes 2.6: it is still true if everyone moved out tonight.

| Kind | Says | First version | Example shape, from the made-up city |
|---|---|---|---|
| `name_origin` | Where the area's name comes from, or when it was first recorded | Yes, one at most | "The name is first recorded in 1274 as Aldrewic." |
| `history` | A dated event about the place: a building, a railway, a boundary | Yes, two at most | "The station opened in 1907." |
| `known_for` | A named thing in the area: a market, a park, a building, a street, an institution | Yes, two at most. The sentence must name the thing | "Foxholt Market has been held on the high street since 1880." |
| `to_see` | The first sentence of the article about a thing that "Go and look" already names | Yes, three at most. No model: code takes the sentence | "Dulcimer Green is a public park beside the canal." |
| `described_as` | How a named publisher describes the place | No. No cleared source holds such words | |
| Locals' own words | How people who live there describe it | No, in any version as asked. See section 12 | |

| Never claimed | Why | Held by |
|---|---|---|
| Who lives there: age, class, wealth, ethnic group, faith, origin, students, families, "community" said of people | Rule 8, ADR 0006 | `POLICY_LEXICON` and the group words of core, the section list, the second look, review |
| Safety, crime, disorder, policing, riots | ADR 0006: no sentence calls a place safe or unsafe | `BANNED_WORDS`, a wider list of crime words, the section list |
| Superlatives and praise: best, most, largest, oldest, famous, popular, sought-after, desirable, trendy, vibrant | Nothing measures them. They are how a seller writes | `VERDICT_WORDS`, a list of superlatives with two exceptions ("first recorded", "first mentioned") |
| Change: up and coming, gentrified, regenerated, declining | It is a claim about who is moving in (vibes 2.3) | Word list |
| Prices, rents, affordability | PLAN section 15: no affordability verdicts. Cost comes from `cost.json` | Word list, and any `£` |
| What is open, busy or on now | A page cannot say a shop is still open | Present-tense words about venues: "is home to", "boasts", "offers" |
| A living person | It is personal data, and says who lives there | Every link in the sentence is looked up in Wikidata. In the first version any human drops the claim |
| Schools' quality, a school's faith, catchments | The tables hold results. A sentence adds a verdict | Section list |
| Any figure | Every number on screen comes from a fact the pipeline built. A year is the one exception, and it is checked (section 4.1) | A digit that is not a year or part of a name drops the claim |

## 3. Sources that may be read

The rule is rule 1 of AGENTS.md. A page is fetched only under a registry entry, and its words are shown or sent to a model only if the entry allows that use. No page is found by a search engine, by a model's search tool, or by following links.

| Source | Registry id | Licence | Registry today | Gives | Words shown | Text to a model |
|---|---|---|---|---|---|---|
| English Wikipedia, the area's own article | `wikimedia-wikipedia-excerpts` | CC BY-SA 4.0 | approved: `display`, `profile_text` | `name_origin`, `history`, `known_for` | Yes: verbatim, boxed, credited, revision recorded | Yes, to a prompt that returns sentence numbers. Never to a prompt that writes text. Decision 2 |
| English Wikipedia, the article of a named thing | the same | the same | the same | `to_see` | The same | No model |
| Wikidata | `wikidata-places-and-landmarks` | CC0 | approved: `gazetteer`, `destination_search` | The article behind an area or a thing. Coordinates. Whether a link is a person. A year to check against | Nothing of it is shown. The two checks need `validation_only` added | Not needed |
| Planning Data: listed buildings, conservation areas | `historic-england-listed-buildings`, `mhclg-planning-data-conservation-areas` | OGL v3 | approved: `scoring` | Names for "Go and look" | Needs `display`, with evidence (vibes 5.3) | Not needed |
| OS Open Greenspace, NaPTAN | `os-open-greenspace`, `dft-naptan` | OGL v3 | approved, with `display` | Park and station names | Yes | Not needed |
| Wikivoyage | `wikimedia-wikivoyage-text` | CC BY-SA 4.0 | held | District pages written for visitors | No | No. It stays held |
| Council pages, conservation area appraisals, neighbourhood plans | `london-boroughs-conservation-area-appraisals` | None stated | held | | A link out only | No |
| Historic England's own list entries | not registered | Not read | | Why a building is listed | No | No |
| GLA pages | not registered | Not read: the site was under maintenance | | | No | No |
| Local press, forums, review sites, estate agents, social media | none, or banned | Closed terms | | | Never | Never |

Three things follow.

- **One source of words.** At launch the researcher reads Wikipedia and nothing else. The research counted 720 Wikidata items that are areas of London, 703 of them with an English article (`docs/research/reports/boundaries.md`). So most areas are expected to have a page, and some outer areas a stub or none. Neither was measured.
- **Council and heritage pages are shut, and a question to a council does not open them quickly.** A council's page is its copyright unless it says otherwise. The exception for text and data analysis covers "research for a non-commercial purpose" only (Copyright, Designs and Patents Act 1988, section 29A, read). The exception for quotation needs "fair dealing" (section 30(1ZA), read), which is a legal judgement, and ADR 0007 lets nothing in v1 rest on one. What opens a council's pages is a statement of an open licence on its own site, saved in `registry/evidence/`. That is a day of the founder's time across 33 sites (decision 5), and until then an area page may link to an appraisal and quote none of it.
- **Share-alike stays in its own file.** Wikipedia's words go in `claims.json` and nowhere else. The registry already refuses a share-alike source any use in scoring, the gazetteer or destination search, so no claim can reach `rank()`, a vibe or a name.

## 4. The steps

| # | Step | Done by | Takes | Gives | A row is refused when |
|---|---|---|---|---|---|
| 1 | Map | Code, then a person | The gazetteer's QIDs | `area_sources.csv`: `area_id`, `source_id`, `qid`, `page_id`, `title`, `role` (`own`, `alias`, `thing`) | The item's point is over 500 m outside the area's polygon. The item is not a place. Two areas claim one article |
| 2 | Fetch | Code | The table | The page as bytes, twice: the latest revision, and the latest that is 30 days old or more. One evidence row each | The status is not 200. The title redirects elsewhere. The page holds a banner for disputed, unsourced or promotional text, or a template that asks for extra credit (a condition of the registry entry) |
| 3 | Read | Code | The bytes | Plain text by section, split into numbered sentences. Reference marks, tables, boxes and captions are taken out | The text is under 600 characters |
| 4 | Select | Model A | The sentences of the allowed sections, the area's names, the closed list of kinds | Candidates: `kind`, `first`, `last`, `words` | A number is out of range. `words` is not, character for character, the sentences numbered |
| 5 | Check | Code | Candidates | Claims | Any check of 4.1 fails |
| 6 | Second look | Model B, from another provider | The quote alone, with nothing else about the area | One code for each quote: `none`, `residents`, `safety`, `praise`, `person`, `change_or_price`, `not_a_place` | The code is not `none`. Model B can remove and never add |
| 7 | Store | Code | Claims | The review queue, outside git | |
| 8 | Review | A person | The queue | `accepted` or `rejected`, with a reason code | Section 8 |
| 9 | Release | Code | Accepted claims | `claims.json` in the release | `Registry.require(source_id, profile_text)` fails. `verify()` fails the quote (section 11) |

Sections a model is never sent, by heading: Demography, Demographics, Population, Ethnicity, Religion, Crime, Politics, Governance, Education, Schools, Notable people, Notable residents, In popular culture, Sport, Economy, Housing. The model cannot point at what it was not sent. The list is code, and is widened or narrowed from the golden set.

A model's own knowledge is used in one place: judging which sentences on the page are worth a reader's time. It supplies no fact, no name and no address of a page.

Step 2 sends its requests one after another, 50 titles to a request, with a User-Agent that names Burro and a contact address, as the publisher asks (section 15). It reads no page a registry entry does not cover.

### 4.1 The checks in code

| Check | Rule | Catches |
|---|---|---|
| `words_are_in_source` | The quote equals `text[start:end]` of the text whose `sha256` is in the evidence row. No fuzzy match | An invented or altered quotation |
| `whole_sentences` | The span starts and ends at a sentence boundary. One or two sentences. 40 to 320 characters | A cut that drops "not" or a clause |
| `stable` | The same words are in both revisions fetched | Vandalism, an edit war, a fresh edit nobody has checked |
| `about_this_area` | The page is the area's own by QID. The quote, or the sentence before it, holds the area's name or an alias. A quote that names another area of the release is flagged for the reviewer | A sentence about the neighbour |
| `no_group_word`, `no_verdict`, `no_change_or_price` | The lists of section 2, in every form a word takes, read as the verifier reads (accents, look-alike letters). A listed word passes only inside a name that a registered place source holds | A view about a community. Praise. A verdict on safety |
| `no_person` | Each link in the span is resolved to a QID. An item that is a human drops the claim | A living person |
| `no_loose_number` | A digit is allowed only as a year from 1000 to the year of the build, or inside an allowed name | A figure nobody built |
| `year_agrees` | Where Wikidata holds an opening or founding year for the thing named, the year in the quote is the same | A source that is wrong, where a second source exists |
| `not_flagged_in_source` | The sentence carries no "citation needed" or "dubious" mark. Whether it carries a reference is recorded for the reviewer | A statement the source itself doubts |
| `licence_gate` | `Registry.require(source_id, Use.PROFILE_TEXT)` | A source that may not be shown |

Every refusal is counted by check and by kind. No refused text is logged: a build log on a public repository is public.

## 5. The record of a claim

`claims.json` is a new release file: `{"rows": [...]}`, ordered by `claim_id`. About 3,100 rows and 3.4 MB for London. That is an estimate: 450 areas with up to 5 sentences a model pointed at, and 810 things to see with an article of their own (3 an area, 6 in 10 with an article), at 1.1 KB a row.

| Field | Type | Notes |
|---|---|---|
| `claim_id` | str | `lon-c`, or `syn-c` in the synthetic release, and the first 12 hex digits of the `sha256` of `source_id`, `page_id` and `quote`. The same words keep the same id in every release |
| `area_id`, `kind` | str, enum | `kind` is one of section 2 |
| `quote` | str | The source's words, as shown. Never edited |
| `thing` | str or null | For `known_for` and `to_see`: the name of the thing, which must stand in the quote |
| `source_id` | str | In `manifest.sources` |
| `title`, `url` | str | `url` is the permanent address of the revision, not of the page |
| `page_id`, `revision_id` | int | The publisher's own ids |
| `source_dated` | timestamp | The date of the data: when the revision was made |
| `retrieved_at` | timestamp | When code fetched it |
| `raw_sha256`, `text_sha256` | str | Of the bytes fetched, and of the text the offsets count into |
| `start`, `end`, `section` | int, int, str | Offsets in code points, and the heading the words stood under |
| `derived` | object | `method` (`model_select` or `first_sentence`), `reader_version`, `prompt_version`, `provider`, `model`, `second_provider`, `second_model`, `checks_version` |
| `has_reference` | bool | Whether the source gave a reference for the sentence |
| `review` | object | `status`, `reviewed_on`, `reviewer` (`founder` or `second`, never a name), `reason` |
| `first_release`, `licence`, `attribution`, `shortened` | str, str, str, bool | `attribution` is the registry's wording, filled in. `shortened` is always true |

The evidence is kept outside the release, in a private store: `evidence/<source_id>/<raw_sha256>.gz` and `evidence/index.jsonl`, one row for each fetch with `url`, `status`, `content_type`, `bytes`, both hashes and `retrieved_at`. About 3,000 page reads and 90 MB compressed for one build (estimate: 1,510 pages, two revisions of each, 30 KB each). It is kept for as long as any release that cites it is served. The review queue and every rejected claim are kept there too, and only counts are published, as the ratings of vibes 6.2 are.

A claim becomes a `Fact` of kind `quote` (contract 7.1): `slots` hold the quote, the title and the dates, `sources` holds the one source, `as_of` is the day of `source_dated`. `facts_for` is to return it only when it is called with no spec, which is how route 6 calls it, so no other route can serve one.

Each release carries a coverage report beside it: for each kind, the areas with an accepted claim, and for each check, the candidates it refused. It holds counts and no text.

## 6. How a claim is shown and credited

| Rule | Detail |
|---|---|
| Where | The area page, in one block, after the portrait and the figures. Nowhere else. A test: nothing that ranks, explains, compares, finds likeness or makes a share opens `claims.json` |
| Heading | "From Wikipedia", fixed text in core. Under it, the kinds as plain labels: Name, History, Places and buildings, To see. No label says "known for": that would be Burro's own claim |
| The words | Each quote in quotation marks, in a `blockquote`, unchanged. No sentence of Burro's is mixed in |
| The credit, once for each article | The registry's wording: the article's title, a link to the revision quoted, "released under the Creative Commons Attribution-Share-Alike License 4.0" with a link to the licence, and "The excerpt has been shortened." Then "Read by Burro on {retrieved}" |
| The caution, fixed text | "These are Wikipedia's words, not Burro's. Anyone can edit Wikipedia. Burro checked that these words were on the page on the date shown. It did not check that they are true." |
| A gap | "Burro holds no cited description of {name} in this release." Never a filler sentence |
| Wrong? | A link to report a claim. The promise of vibes promise 7 applies: a review within 28 days. A claim is withdrawn by a new release that leaves the row out, which takes minutes because nothing else is rebuilt |
| Synthetic | The synthetic release holds made-up claims from a made-up encyclopaedia, flagged `synthetic`, so the block can be built before any page is fetched |

## 7. How stale claims are found

| When | What runs | Model calls | Outcome |
|---|---|---|---|
| Every build | Each page is fetched again. If `revision_id` is unchanged, the claim is carried forward | None | The same claim, the same id |
| Every build, page changed | `words_are_in_source` and `stable` run on the new text | None | Words still there: carried forward with the new revision. Words gone: the claim leaves the next release and the page is read again |
| Every build | A page that is gone, has moved or has gained a banner | None | Its claims leave the next release, and the area shows a gap |
| Weekly, between builds | A scheduled job asks for the latest `revision_id` of every page, 50 titles to a request, about 31 requests | None | A list of changed pages. It costs nothing on a public repository (read) |
| On a report | The founder opens the claim and its evidence | None | Kept, or withdrawn by a new release |
| Every year | Any claim whose `retrieved_at` is over 12 months old is reviewed again | None | The registry's own staleness rule, applied to a claim |

An old release stays true of what it says: the link is to the revision, which the publisher keeps, and the bytes are in the evidence store.

## 8. What a person reviews, and how long it takes

The reviewer sees the quote, the sentence before and after it, the kind, the flags of 4.1 and a link to the revision. They answer four questions: is it about this place, does it describe people, does it pass judgement, would a resident find it fair. One "no" rejects.

| Task | Count | Each | Hours |
|---|---|---|---|
| Golden set: mark every sentence of 30 articles as fit or unfit, before any model is run | 30 | 12 min | 6 |
| Confirm the map: every area's article, and the 1 in 5 things whose match is unsure | 860 rows | 20 s | 5 |
| Read each claim with its context | 3,100 | 25 s | 21 |
| Open the source for one claim in ten | 310 | 3 min | 15 |
| Read each finished area block once, whole | 450 | 1 min | 8 |
| **First release** | | | **about 55, of which 45 is review** |
| Second reviewer reads a sample of 1 in 10, to measure agreement | 310 | 40 s | 3.5, paid by the hour |
| Each later build: new and changed claims, estimated at 15% | 460 | 50 s | 6 |

The times are guesses from reading speed, to be replaced by the first 100 claims timed. An area is released as soon as its own claims are reviewed, so review does not hold a launch.

## 9. What a build costs

**Tokens, estimated.** 700 articles about areas. Model A: 6,000 tokens of article and 2,500 of instructions in, 1,200 out. Model B: 4,000 in, 300 out. A full build on one provider is 8.75 million tokens in and 1.05 million out. The sentences for things to see go to model B only, 20 to a call, and add under 3%. Article length was not measured: the first step of the first build counts it and makes no model call. The planning figure adds 30% for thinking tokens and retries.

| Provider | Model | In, USD a million | Out | Full build | Planning figure | Price read |
|---|---|---|---|---|---|---|
| Gemini | `gemini-3.5-flash-lite` | 0.30 | 2.50 | 5.25 | 6.80 | Today, and `docs/research/models/gemini.md` |
| Gemini | `gemini-3.8-flash`, to 31 December 2026 | 0.75 | 3.75 | 10.50 | 13.70 | The same. It doubles on 1 January 2027 |
| Gemini | `gemini-3.1-pro-preview` | 2.00 | 12.00 | 30.10 | 39.10 | The same |
| OpenAI | `gpt-5.6-luna` | 0.20 | 1.20 | 3.00 | 3.90 | Today, through a tool. No report in the repository |
| OpenAI | `gpt-6-sol` | 2.00 | 10.00 | 28.00 | 36.40 | The same |
| DeepSeek | `deepseek-flash`, peak | 0.30 | 1.20 | 3.90 | 5.10 | `docs/research/models/deepseek.md` |
| Claude | Haiku 4.5 | 1.00 | 5.00 | 14.00 | 18.20 | `docs/research/models/claude.md` |
| Claude | Sonnet 5 | 2.00 | 10.00 | 28.00 | 47.30, with its 30% more tokens | The same |

| Point | Value |
|---|---|
| In pounds | Every figure is under GBP 40, at an assumed USD 1.30 to the pound. The rate was not checked |
| Batch | About half price on Gemini, OpenAI and Claude, and the answer comes within a day. A build can wait a day |
| A later build | Only a page that lost its words is read again. Estimated at 15% of pages: under USD 7 on any row |
| Compute | 3,000 page reads, one after another: about 50 minutes. 1,440 model calls, 8 at a time: about 45 minutes. Checks: under a minute. No native library |
| Privacy | Nothing a person typed is sent. The input is a public page and fixed instructions. So a provider's retention terms, which rule DeepSeek out for prompts, do not rule it out here |
| Which provider | Gemini for model A, as the founder asked. Another provider for model B, so that one model's blind spot is not checked by itself. Both are settled by the golden set, not by price |

## 10. How it fails, and what catches each

| Failure | First catch | Second catch | What is left |
|---|---|---|---|
| A quotation that is invented or altered | `words_are_in_source`: an exact match against the stored text | The model returns sentence numbers, and code lifts the words | A fault in the reader of step 3, which the planted sentences test |
| A real sentence cut so that it says something else | `whole_sentences` | Review shows the sentence either side | A bad split after "St." or "c.", seen in review |
| A real sentence about another place | `about_this_area` | Review | A sentence that names neither place |
| A page that changed after it was read | The revision is recorded, and the link is to it | The build of section 7 | The quote may no longer be on the live page. The credit says which revision |
| A page that was vandalised when read | `stable`: the words must be in two revisions 30 days apart | Banners, review | Vandalism that stood for a month |
| A source that is itself wrong | `year_agrees`, `not_flagged_in_source` | The caution of section 6. The report link | **Most of it.** Code can check that a source said a thing, not that the thing is true. Burro shows it as the source's words and says so |
| Text that carries a view about a community | The section list: the model never sees it | The word lists, model B, review against four questions | A view said in plain words no list holds. Review is the only catch, which is why every claim is reviewed |
| Text written to sell an area | `no_verdict`, the promotional banner | Review | |
| A living person named | `no_person`, by link | Review, for a name that is not a link | |
| Instructions hidden in a page | A model's answer can only be numbers and a kind from a closed list. Nothing it writes is run or shown | Checks and review | It can sway which true sentence is picked |
| The wrong article for an area | Step 1: coordinates inside the polygon | The person who confirms the map | |
| A model that changes under the same name | `derived` records provider, model and prompt. Unchanged pages are never read again | The golden set runs on every change of model or prompt | |
| Imported text with its own licence | The template check of step 2 | | A template nobody listed |
| A rejected claim about a real area made public | The queue and the evidence are outside git. Logs hold counts | | |

**The gate before the first real build.** On the golden set of 30 articles, after code and model B: no sentence the founder marked unfit for residents, safety or a living person is kept, and at least 7 in 10 kept sentences were marked fit. If one unfit sentence is kept, the lists are widened and the set is run again. Offline, 40 planted sentences in made-up pages must each be refused by the check named for it.

## 11. How the verifier must grow

**Stage A, the first version: quotations.** No sentence a model wrote is shown, so `explain()` still refuses any explainer but the template one.

| Change | Where | Done when |
|---|---|---|
| Fact kind `quote` and template `quote`, which prints the slot and nothing else | contract 7.1 to 7.3 | Every quote of the synthetic release renders |
| The pipeline runs `verify()` on every quote before it writes a release | `write_release` | A quote holding "safe" or "vibrant" is refused at build, not at answer time |
| Rule `claims_are_sourced` in `parse_release`: every row has a source in the manifest, both dates, both hashes and `review.status` of `accepted` | contract 2.8 | A row in `BROKEN` shows it refusing |
| `write_release` asks `claims.json` for `Use.PROFILE_TEXT` | contract 2.1, registry README | A release citing a held source is refused |
| `POLICY_LEXICON` and the group words are run over a quote, which `verify()` does not do today | core | The sentence "popular with young families" fails |

**Stage B, before any sentence a model wrote is shown.** Contract section 11 already names four steps: run the policy lexicon, widen the banned words, allow only the words of the cited fact plus a short list of connectives, and turn the two tests marked as expected to fail into tests that pass. The third already holds a sentence to the words of its quote, because the quote is a slot of the fact. A sentence that rests on a quote needs four more.

| # | Rule | Catches |
|---|---|---|
| 5 | A word that turns or compares (not, never, no longer, more, less, before, after) is allowed only if the quote holds it, as many times | A meaning turned round |
| 6 | Each year or number has, within three words, a word that stands within three words of it in the quote | "Closed in 1907" where the quote says "opened in 1907" |
| 7 | Names are matched in any case against every name in the release and every capitalised run of the quote | "near the tate modern" |
| 8 | The sentence is stored and served with its quote, and the screen shows the quote one press away. A sentence resting on share-alike words is itself released under CC BY-SA 4.0 and says so | A reader who cannot check. A licence breach |

These rules cannot prove that a sentence means what its quote means. No code can. So stage B also needs a measured test: an adversary writes 500 sentences that pass every rule and are false of their quote, as ADR 0012 did for the reader, and the share that gets through is published. Every model sentence is reviewed by a person until that share is known and accepted by the founder.

## 12. Not in the first version

| Not attempted | Why |
|---|---|
| Any sentence written by a model | The verifier cannot check what a sentence means. A summary of Wikipedia is also plausibly adapted material, which the registry entry forbids today |
| "History in two sentences" as a summary | The same. The first version shows up to two of the source's own sentences |
| How locals describe a place | It is a statement about residents. The places where locals write, forums, reviews and social media, forbid reuse or are banned. No version should claim to speak for residents |
| Finding pages with a search engine or a model's search tool | The pages found have no licence on file, and the choice of pages cannot be repeated |
| Asking a model what it knows, even as a lead | It would propose what an area is reputed for, which is the stereotype the lists exist to stop. Left to a later version, with its own test |
| Council, heritage body and GLA pages | No licence on file. Decision 5 |
| Claims about streets, single buildings' state, or venues that may have closed | A page cannot say what is there today |
| Photographs | Every image source is held |
| Claims in search, ranking, vibes, cards, comparison or a share | ADR 0014: evidence may stand behind a conclusion. A quotation is not a measure, and none is used as one |
| Embeddings or text search over claims at answer time | Production runs no vector database |
| Translation, or sources not in English | Nothing could check them |
| Publishing without review | Review is the only catch for a view said in plain words |

## 13. What each part needs, and what can start now

| Need | From | Blocks |
|---|---|---|
| A QID for each area and alias, and polygons | The gazetteer | Step 1 |
| `claims.json` in contract section 2, fact kind `quote`, a field on route 6, `make openapi` | Core and the API | Stage A |
| The registry's use table gains `claims.json` to `profile_text`. The Wikipedia entry's third condition is reworded (decision 2). `validation_only` on the Wikidata entry. `display` on the two Planning Data entries, with evidence | The registry's owner | A real release |
| The block on the area page | The website | Showing a claim |
| A place to build that can reach the publisher and two providers, with Python and no native library | The founder. A hosted runner, started by hand from the default branch, is enough. Keys are held as secrets | Steps 2 to 6 |
| Two provider keys with billing, and a cap of USD 50 a month each | The founder | Steps 4 and 6 |
| A private store for evidence and the queue | The founder | Step 7 |
| The golden set | The founder, 6 hours | The gate of section 10 |
| A decision record for the researcher, and the changes to PLAN sections 4 and 7 that follow from decision 2 | Their owner, in the same change as the code | Stage A |

| Can start now, with no page fetched and no key | |
|---|---|
| The reader of step 3, the checks of 4.1 and the claim record, against made-up pages | Pure Python, offline |
| The 40 planted sentences and the word lists | Tests |
| Made-up claims in the synthetic release, and the block on the area page | `make fixture` |
| The prompt, the schema and a fake model that answers wrongly | As `claude.py` was built |
| The review page, on made-up claims | A static page |

## 14. Decisions for the founder

| # | Decision | Recommended |
|---|---|---|
| 1 | Is the first version quotations only, with no sentence written by a model? | Yes |
| 2 | The Wikipedia entry says never to pass its prose "to any prompt that writes Burro's own text". PLAN section 7 and contract section 11 say the excerpt is never sent to a model. May it be sent to a prompt that returns sentence numbers and writes nothing? | Yes. All three are reworded in the same change as the code. If no: code takes the first two sentences of the article, no model is used, and every check and the review stay as they are |
| 3 | May a claim name a person who has died? | Not in the first version. Later, only a linked person with a date of death in Wikidata |
| 4 | May a quotation mention war damage, such as bombing? | Yes, where it is about buildings. Riots and crime: no |
| 5 | Spend a day opening the copyright pages of 33 councils, Historic England and the GLA in a browser, and saving each? | Yes, after launch. A site that states an open licence gets a registry entry. No letters: a reply takes weeks and a statement on the site is better evidence |
| 6 | Does the second curator review a sample? | Yes, 1 in 10, about 3 paid hours |
| 7 | Which two providers? | Gemini for model A. Settle model B on the golden set |
| 8 | Does Wikivoyage stay held? | Yes. It is written for visitors, by district |
| 9 | If a resident objects to a true, sourced quotation about their area? | Withdraw it in the next release, within 28 days, and record the reason code |

## 15. What was read, and what was not checked

Read on 2026-09-23, each through a reader that summarises, so every quoted word must be checked in a browser before it is relied on.

| Page | What it says |
|---|---|
| CC BY-SA 4.0, legal code | Adapted Material is material "derived from or based upon the Licensed Material and in which the Licensed Material is translated, altered, arranged, transformed, or otherwise modified". Section 2(a)(1) grants the right to "reproduce and Share the Licensed Material, in whole or in part" |
| Wikipedia: Reusing Wikipedia content | Credit by "a hyperlink (where possible) or URL to the page". "If you make modifications or additions, you must indicate in a reasonable fashion that the original work has been modified." |
| MediaWiki, API:Revisions | `rvprop` takes `ids`, `timestamp`, `sha1`, `content`. At most 50 revisions to a request when content is asked for |
| MediaWiki, API:Etiquette. Wikimedia User-Agent policy, updated 27 March 2026 | Requests "in series rather than in parallel". A script without contact details in its User-Agent "may be blocked without notice" |
| MediaWiki, TextExtracts | In plain text "citations may not be stripped" and "new lines may be dropped". So step 3 reads the page itself and does not use this |
| Copyright, Designs and Patents Act 1988, sections 29A and 30 | The words quoted in section 3 |
| GitHub, billing for Actions | Usage is "free" for "public repositories that use standard GitHub-hosted runners" |
| Gemini and OpenAI price pages | The prices of section 9. The OpenAI model names are as read through the reader |
| Historic England terms. OpenAI's marketing price page. The GLA copyright page | Not read |

Not checked, and to be treated as unknown: the length of a London article; how many of 450 areas have an article of their own; the form of the publisher's endpoint for a rendered page at a given revision; which banner and credit templates exist; how long a hosted job may run; every hour in section 8; the exchange rate; whether any council states an open licence; whether `verify()` as built passes a quote that holds "century". No dataset was downloaded and no page about a place was read.
