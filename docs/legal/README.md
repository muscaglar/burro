# Legal documents: drafts

**Drafts. Not published. Not legal advice.** Written on 23 September 2026 from public guidance and from the code in this repository, and brought up to 24 September 2026. Brought to the website again on 26 September 2026, once the founder had walked it a second time: "What was no longer true on 26 September 2026", below, says in what. Brought to it once more on 27 September 2026, once they had walked it a third time: the same part says in what, under "After the third walk". They are behind the code in four things that were built since they were first read against it, and "What the drafts are behind in", below, lists each. **Nobody qualified has read any of them, and whoever wrote them is not a lawyer.** There is no budget for that ([ADR 0007](../adr/0007-no-solicitor.md)). This file says what they are, what was put right on the second day, where they are most likely to be wrong, and the cheapest ways to have them read.

**Brought up to 26 September 2026 for accounts**, which the founder asked for that day: "What accounts changed", below, says what changed in each draft, and what is the founder's to decide.

## What is here

| File | What it is | State |
|---|---|---|
| [privacy-notice.md](privacy-notice.md) | What Burro collects and what it does not, in the order a person would ask | Draft. 22 things stand between it and publishing. They are listed at its top. Six of them are of accounts |
| [terms-of-use.md](terms-of-use.md) | What Burro is and is not, and what is asked of a person who uses it. Section 7 holds the term for anyone who lets or sells homes | Draft. 12 things stand between it and publishing. One of them is of accounts |
| [data-protection-checklist.md](data-protection-checklist.md) | The launch checklist. What the founder must do that a document cannot, in the order of what blocks a public launch: 19 tasks in four stages, 31 to 35 hours, GBP 47 to 52. Then what blocks turning accounts on: twelve steps more, about 15 hours | Draft |
| [residents-crime-and-equality.md](residents-crime-and-equality.md) | What Burro holds about the people who live in an area, what the ICO's pages and the Equality Act say of it, where the risk lies, and each point where a solicitor's reading would change what is safe to ship | Draft. New on 24 September 2026 |
| [access-by-children.md](access-by-children.md) | Whether people under 18 are likely to use Burro, weighed as the ICO sets it out, now that the website is to look like a game. What would change the conclusion, and what is the founder's to do. It is the page that task 14 of the checklist asks for | Draft. New on 26 September 2026. It waits for the founder to read it |
| The accessibility statement | It was part of the website until 26 September 2026, when the founder asked for it to go. The website makes no claim of a standard of accessibility since: [ADR 0042](../adr/0042-the-website-makes-no-claim-of-a-standard-of-accessibility.md) | Gone. It said that it had nowhere to send a report yet, and no page says how to report a problem now |

Burro was first deployed on 25 September 2026, with the made-up city. The website has no page for any of the five drafts, so none of them is in front of the public as Burro's own. What the website itself says of how words are handled is on its page of methods, and is in front of the public. None of the drafts may be published as it stands.

| Mark | Meaning |
|---|---|
| `[FOUNDER: ...]` | A blank only the founder can fill |
| `[FOUNDER NAME]`, `[FOUNDER CONTACT]`, `[COMPANY NAME]`, `[COMPANY NUMBER]` | The name and the contact. Never fill them in this repository: it is public |
| `[NOT BUILT: ...]` | A sentence the code does not yet make true |
| `[SETTING: ...]` | A sentence that is true only while a setting holds, at a host, at a provider or in the service. No code or test holds it |
| `[SOLICITOR]` | A sentence where this draft's reading of the law decides what is said. A qualified reading could change what is safe to ship. [residents-crime-and-equality.md](residents-crime-and-equality.md), section 9, lists those about residents, recorded crime and the equality law, in the order of what each could cost. The rest are in the table of risks below |

## What accounts changed, on 26 September 2026

The founder wrote that day: "We will also need to lay the ground work for a user login, account creation, security etc. Hardening with proper logging etc." and "We'd need to store user preferences/previous searches etc and re-present this etc." Accounts were built as groundwork, and are **off until they are turned on** ([ADR 0043](../adr/0043-burro-has-accounts-and-a-person-signs-in-by-a-link-sent-by-email.md), [0044](../adr/0044-a-person-who-has-signed-in-may-keep-a-search-and-what-is-kept-is-the-spec-and-never-the-words.md), [0045](../adr/0045-the-service-has-a-database-one-file-for-accounts-and-what-they-keep.md)). With them off, every sentence of these drafts that was true of Burro is true still. So each sentence of accounts is marked `[SETTING: accounts are turned on]`, and the mark is taken off when they are.

Until that day the drafts could say that Burro does not know who anybody is. Of a person who makes an account they cannot.

### What changed in each draft

| Draft | What it said | What it says now |
|---|---|---|
| Notice, in short, and sections 2 and 6 | There are no accounts. Burro asks for no email address, sets no cookie, ties no search to the next, and keeps no search | Each is so unless a person makes an account. Each sentence says so where it stands, and sends the reader to section 20 |
| Notice, 8 | Two kinds of log line and a record of each call | A line for what happens when somebody signs in, which holds two fixed words and nothing of a person. And what has happened to an account, kept with the account |
| Notice, 9 and 13 | Two hosts. Nothing that a person types passes through the company that serves the website | A company that sends email, which is not chosen. What is sent for an account passes through the company that serves the website: an email address, the code of a link, two cookies, and the settings of a search that is kept. What is typed into a search still does not |
| Notice, 11 | No basis proposed for an account | Contract, for an account and for a search that a person pressed to keep. Legitimate interests, for the limits and for what has happened to an account. For the last searches it depends on the founder's choice. A reading of the rules on cookies |
| Notice, 12 | No period of an account | A row for each copy that another company holds. The periods of an account are in section 20, and most are blanks for the founder |
| Notice, 14 | "Burro holds nothing that it can tie to you" | It is so of a person with no account. A person with one sees what is held, takes a copy and deletes it, themselves, signed in |
| Notice, 16 | Burro does not ask your age | It asks once, where an account is made, and keeps the time of the answer. It checks nothing |
| Notice, 19 | Accounts are coming | They are built, and nobody can make one until the notice is published |
| Notice, 20 | | New: what an account is, the two cookies, what is kept and what is not, who else receives it, how a person sees it, takes a copy and deletes it, what deleting cannot do at once, and what to do on a shared computer |
| Terms, 1 and 6 | "What you need: no account". Burro does not ask your age | No account is needed. Where one is made, a person confirms that they are 18 or over |
| Terms, 14 | | New: what is asked of a person who makes an account, and how an account ends |
| Checklist | "What changes when accounts arrive", as an expectation | "Before accounts are turned on": twelve steps, lettered, each with what it costs. Then what accounts changed, row by row, as they were built |
| [Children](access-by-children.md) | No account, no check of age and no statement of age on any page | Section 8 is new: a person says that they are 18 or over when an account is made, what the ICO says of a statement that nothing checks, and what it adds to the weighing. No conclusion of the page was changed |

### What is the founder's to decide, and what each choice costs

None of these is decided in the drafts. Each is a blank, marked `[FOUNDER]`, where the notice would say it.

| # | What | The choices | What each costs |
|---|---|---|---|
| A | How long an account is kept when nobody signs in to it | For as long as Burro runs. Or deleted after a time: 12 months and 24 months are common choices, and neither was read at a source | With no limit, Burro holds the address and the searches of people who left years ago, and a later owner of a mailbox can sign in to the account that was there. With a limit, a person who comes back finds their searches gone, and a step must be built that deletes, with a warning by email first or without one. The ICO, as read: "You must not keep personal data for longer than you need it", and "The UK GDPR does not set specific time limits for different types of data" |
| B | How long a search that was kept is kept | Until the person takes it away. Or let go after a time | A search that is let go is one the person pressed to keep. A search that is never let go names a workplace that may be years out of date |
| C | How long the records of links and of sign-ins that have ended are kept, and of what has happened to an account | As built: a link for a day, a sign-in that has ended for 30 days, and what has happened to an account for 90 days and 200 at the most. Each is a first guess, and one number in the code. **Each is the least, and not the most**: nothing runs by the clock, so what is too old is deleted the next time anybody asks for a link, signs in or comes back signed in, and as the service starts. Or a step that runs by the clock, which holds each to the day, and is not built | As built, what is too old is still held on a day when nobody uses an account, and for as long as accounts are turned off, and the notice says so. A step that runs by the clock is one more thing to build and to watch. They are what a person reads to see whether somebody else has tried their account. The shorter they are kept, the less there is to read, and the less there is to lose. The record of a link holds the address it was asked for, whether or not an account came of it |
| D | How long the host keeps its daily copies of the disk | From 1 day to 60. It is 5 unless it is set | It is how long a deleted account is still held somewhere, and it is what the notice must say. The shorter it is, the fewer days there are in which a fault can be noticed and the file put back |
| E | Whether a person's last searches are kept from the moment they sign in | Only once a person turns it on, which is how the code is left. Or from the start, with a way to turn it off. One setting chooses, `BURRO_ACCOUNTS_KEEP_RECENT` | From the start, every search of a person who is signed in is written down with the places they must reach, though they pressed nothing to keep it, and the basis for it is weaker: risk 20. Turned on by the person, fewer will ever see their last searches, which the founder asked for |
| F | Who sends the email | Two companies are fitted, Postmark and Resend. Any other needs code | It is given every address that asks for a link. It needs an agreement and a check of where it keeps an email. [The guide to deployment](../../deploy/README.md#turning-accounts-on) lists what to ask of one |
| G | Whether the cookie that keeps a person signed in is set without asking | Set for 30 days, as built. Or a box to tick, "keep me signed in", without which the cookie ends when the browser is closed | As built, it rests on a reading: risk 19. With a box, a person who does not tick it is sent an email each time they come back. It is not built |
| H | What is done for a person who cannot read the email address of their account | Nothing: the account is kept as A says. Or the founder deletes it, after whatever proof they settle on | An email cannot show whose an account is. To delete for an email is to let one person delete another's account. To refuse is to keep what a person has asked to have deleted: risk 21 |

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

## What was no longer true on 26 September 2026

The founder walked the website twice that day. After the first walk [the page on children](access-by-children.md) was brought up to a rabbit who always moves. After the second the website was rebuilt in six things that these drafts speak of. Every sentence that had stopped being true is here, with what it says now. **No conclusion of any draft was changed**: each is the founder's to draw.

### What the founder asked for, and where it shows

| The founder wrote | What was built | Where it shows |
|---|---|---|
| "remove how your words are handeld from the home page search. this is overkill, also remove 'what you type is sent to burro….. language model' copy" | Nothing beside the box says what becomes of what is typed, or who reads it. The service's notice is on the page of methods, under "How your words are handled", and the foot of every page leads there | Notice, "What changed on 26 September 2026", and sections 3 to 6, 12 and 13. Terms, section 5. Checklist, tasks 6 and 16. Risks 1, 5 and 6. [ADR 0023](../adr/0023-what-is-typed-goes-as-typed-and-people-are-told.md), as amended |
| "When running a search, don't ask the user to add anything, assume they want it to be added and just present the results." | The website applies what was read of a sentence, whoever read it, and shows each thing under the box, where it can be taken off. Recorded crime, and what counts who lives somewhere, are applied only where a person chooses them | Notice, sections 3 and 4. Terms, section 5. Checklist, task 15. Risk 17. [ADR 0012](../adr/0012-a-closed-vocabulary-and-a-guard-on-the-model.md), as amended |
| "Add a visiting option under renting or buying" | A search may be a visit, which holds no budget and no home | Terms, section 1. Children, sections 2 and 6. [ADR 0041](../adr/0041-a-search-may-be-a-visit.md) |
| "remove the pause button for the rabbit, for accessibility we will rely on users having motion turned off in the browser" | The rabbit has no button. He is still where a person's system asks for less movement, and nowhere else | Children, section 3 |
| "create a few seconds load time to allow the bunny jumping into a hole animation to appear and take center stage" | A first search waits with the rabbit, however soon the answer is in: two seconds, as it was built that evening, and three seconds and three quarters since 27 September 2026 | Children, section 3 |
| "get rid of the accessibility tab. Overkill" | The statement of accessibility is gone, and the website claims no standard | The table of what is here, above. Checklist, the table of what is built. [ADR 0042](../adr/0042-the-website-makes-no-claim-of-a-standard-of-accessibility.md) |

### In the drafts

| The draft said | What had changed | Now |
|---|---|---|
| Notice: the notice of who reads stands beside the box, and is shown before anything is typed | It stands on the page of methods | Every such sentence says where the notice is, and four carry a mark for the founder |
| Notice: the website shows what the service sends each time the page is opened | The page of methods is built ahead of time | Marked `[SETTING]`: the website is built again when the provider changes |
| Notice and terms: words that are not a plain list are applied to nothing, and the person chooses | The website applies what was read of them | Notice, section 3. Terms, section 5 |
| Notice and terms: nothing a model reads is applied until the person chooses it, marked `[NOT BUILT]` | It was decided the other way | The mark is gone, and a mark for the founder says what stood there |
| Terms: Burro helps you decide where in London to live | A search may be a visit | Section 1, with a mark for the founder |
| Checklist: what is built for task 6 is the notice beside the box | Nothing is built where a person types | Task 6 says so, in bold. Task 16 says that nothing stands in the place of the step that asks |
| Children: a button stops the rabbit, and he hops for 5 seconds at the most | Nothing stops him but the system, and a first search waits so that he is seen: two seconds that evening, and three seconds and three quarters since 27 September 2026 | Section 3, with what it adds to the weighing |

### After the third walk, on 27 September 2026

The founder walked the website a third time, late on 26 September 2026. What they asked for is of the look and of how much a result says. It changed what two drafts say, and **no conclusion of either**: each is the founder's to draw.

| The founder wrote | What was built | Where it shows |
|---|---|---|
| "slow the hole hopping animation down a bit and make it last a tad longer, make soil flick up as it burros" | The rabbit hops more slowly, and a first search waits with him for three rounds of his hop where it waited for two: three seconds and three quarters. Soil flicks up from his hole. Where a person's system asks for less movement he is still, and nothing is waited for | Children, section 3. [ADR 0033](../adr/0033-the-website-looks-like-the-map-of-a-gentle-game.md) and [ADR 0035](../adr/0035-the-search-page-is-one-box-and-the-look-gives-way-to-the-answer.md), as amended |
| "where a gauge may exist, ensure they have a opposing icons for each side of the gauge" | Every gauge has a small picture at each end, wherever one is drawn. None pictures a person, and none says that an end is good or bad | Children, section 3. ADR 0033, as amended |
| "Create visuals for brands near by, air and noise and recorded crime" | Each has a drawing. Recorded crime is drawn as a count that was written down, and never as a warning | Children, section 3. [The reading of the equality law](residents-crime-and-equality.md), section 6 |
| "the source's key should just exist under the show the working section we dont need it at the summary high level card version" | A result draws the key of no source as it is first shown. The key of every figure it shows stands under its working, and opens to the source and the date as it did | The reading of the equality law, section 6. [ADR 0046](../adr/0046-a-result-shows-what-was-asked-for-as-a-name-and-a-gauge-and-the-source-of-every-figure-stands-under-its-working.md), which says what the licence registry asks of a credit and leaves it to the founder |

| The draft said | What had changed | Now |
|---|---|---|
| Children: a first search waits two seconds so that he is seen, and small drawings stand on a meadow | The wait is longer, soil flicks up, and every gauge has a picture at each end | Section 3, with what each adds to the weighing, and sections 4 and 6 where they say what the lean was written before |
| The reading of the equality law: of recorded crime Burro says the count, its category, its period and its source | On a result the period and the source are two presses from the figure, behind a key that stands under the working, where they were one | Section 6 says where each stands |
| Notice and terms: recorded crime is applied only where a person chooses it | It is applied where a person's own words ask for it by name, as "gritty" does, and a wish that may be somebody else's is left for the person. The founder asked for neither: each was decided for them as the website was driven ([ADR 0012](../adr/0012-a-closed-vocabulary-and-a-guard-on-the-model.md), as amended on 27 September 2026) | Notice, section 3, step 3. Terms, section 5. Each with a mark for the founder |

## What the drafts are behind in, as the code was read on 27 September 2026

The drafts were read against the code on 23 and 24 September 2026. Since then they were brought to what the founder asked for of the website, and to accounts, and to nothing else. **Four things that were decided by 24 September 2026 are built since, and the drafts still mark each as not built, or say what was so before it.** No draft was changed for them. Each takes a mark off a sentence that people would be told, so each is the founder's to read first, and the rows that are numbered would move under the sentences that cite them.

| What is so | What holds it | Where a draft is behind |
|---|---|---|
| No provider waits for a person to check what Burro tells people of it. A provider reads where it is named, holds a key, has its terms accepted by name, and its model is one that its adapter was fitted to. One was turned on where Burro is hosted, by hand, on 26 September 2026 | [ADR 0023](../adr/0023-what-is-typed-goes-as-typed-and-people-are-told.md), which took the condition out. `services/api/src/burro_api/providers/choose.py`, and `test_a_provider_is_turned_on_though_no_person_has_checked_what_its_pages_say`. [The guide to deployment](../../deploy/README.md#turning-the-model-on) | The notice: row 2 of what stands between it and publishing, section 4 under "What never changes" with the mark for the founder after it, and two rows of Appendix B, which name two tests that no file holds. The checklist: task 15, where it says that no provider can be turned on. This file: risk 5 |
| The service turns DeepSeek on for nobody, whatever is set and whatever the release | `NOT_FOR_PEOPLE` in the same file, and `test_the_one_provider_that_may_not_read_what_people_type_is_never_turned_on` | The notice: row 8 of what stands between it and publishing, the row of DeepSeek among what is true only while a setting holds, section 4, and Appendix B. The checklist: task 15, and the second row of what is built. This file: the row of `choose.py` under "What disagrees with these drafts" |
| An area's page shows the census table, where the release serves one. Core holds four measures of the age of residents and of what their households were made of, and two vibes that count them. A person may choose one, for more of what it counts, and Burro applies none for them | [ADR 0006](../adr/0006-rank-places-not-residents.md) and [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md), each as amended on 24 September 2026. `test_nothing_describes_residents_but_the_four_measures_and_the_two_vibes_that_hold_one`, which took the place of the test the drafts name | The notice: row 11 of what stands between it and publishing, sections 5 and 18, and Appendix B. The terms: section 2 and Appendix B. The reading of the equality law: sections 2, 3, 4 and 8. The checklist: task 18 |
| Gritty is one vibe, and it counts recorded crime. A release of a real place may carry it, and the rule `gritty_b_is_synthetic` is in the code no longer. A step of a build reads the police's files of recorded crime. A word such as "affluent" is read as a wish about the place, in more ways than one, of which the website takes one | [ADR 0013](../adr/0013-vibes-are-the-centre.md) and [ADR 0012](../adr/0012-a-closed-vocabulary-and-a-guard-on-the-model.md), each as amended | The notice: section 18 and the last rows of Appendix B. The terms: section 2. The reading of the equality law: sections 2, 5 and 6. The checklist: task 18 |

What was not read again for this list: whether a census table is left out for an area of under 1,000 people or 400 households, how a share of under one in a hundred is worded, and whether any release counts a place of worship. Each stands in a draft beside a mark, as it did.

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
| 1 | The lawful basis for reading a sentence is consent, and explicit consent where it is sensitive | Notice, 5 and 11 | The repository holds two readings. The four provider reports and the ICO's page point to explicit consent. [An earlier report](../research/reports/accounts-compliance.md) held that no condition is needed if Burro never infers or uses such data, and marked that as its own reading. The website informs and asks nothing. Since 26 September 2026 it informs on a page that the foot of every page leads to, and says nothing where a person types. The ICO says a basis cannot usually be swapped later. Burro keeps no record of a person, so it cannot show who agreed | A qualified reading. Before that, the ICO's helpline, with the question in writing |
| 2 | Ranking on the age of residents and on what households are made of treats no person less favourably, and the census table leads nobody to steer | Notice, 17 and 18. Terms, 2 and 7 | The Equality Act was read as printed. The regulator's guidance, and every judgment, were not. Age is itself a protected characteristic. Section 111 could reach a service that leads someone else to discriminate, "direct or indirect". No professional has read the decision or the term | Checklist, task 8. Then a qualified reading. [residents-crime-and-equality.md](residents-crime-and-equality.md), section 9 |
| 3 | "DeepSeek is never used for what real people type" | Notice, 4 | A setting holds it and no code does. If it were named on a live service, with its terms accepted and its entry checked, what people type would go to a company that publishes no agreement, no safeguard and no period | Code that refuses it on a release that is not made up |
| 4 | "Burro does not keep it and does not write it to a log" | Notice, 3 | It is true of Burro's code. Fly.io decrypts every request to pass it on. What its own systems record was not said on the pages read, and no agreement with it was found | Fly.io's answer in writing, and its agreement |
| 5 | What the notice of the service says of a provider | Notice, 4 | Periods and places change. Nobody has checked a sentence of any of the four against its page, so none can be turned on. Once one is, a wrong sentence is a false statement to the public. Since 26 September 2026 the notice is shown on a page that is built ahead of time, so it may also say what was so of the provider before | Checklist, task 15. Read the provider's pages again on the day of publishing, and build the website again whenever the provider changes |
| 6 | That naming four companies, and pointing to the notice of the service for the periods and places, is enough | Notice, 4 | The ICO's list asks a notice for recipients, periods and transfers. No page read says whether a notice may point elsewhere for them. Since 26 September 2026 the notice it points to is no longer shown where a person types: the ICO's page on when to tell a person, as read for the checklist, says that privacy information is to be given "at the time when personal data are obtained", and that posting it on a website is not enough by itself | Show the served notice on the page of the privacy notice, which the draft asks for, and say where a person types that it is there. Then a qualified reading |
| 7 | The safeguard for each transfer out of the UK | Notice, 13 | It depends on a list that was not opened, and on risk assessments that are not written. Sensitive data sent under the UK-US arrangement "must be appropriately identified as sensitive". Google may handle what is typed in any country | Checklist, task 5 |
| 8 | "Burro holds nothing that it can tie to you" | Notice, 14 | It rests on Article 11. A sentence can name a workplace and a school. A host holds an internet address and a time. Whether that leaves Burro "not in a position to identify" a person is a legal question | A qualified reading |
| 9 | A share for an area of several thousand people is about nobody who can be identified | Notice, 18 | It is this draft's reading of the ICO's pages on anonymous information, which are written for whoever makes statistics and not for whoever shows them. The floor of 1,000 people is a first guess, and no test holds it | The ICO's helpline, with question 4 below. A test for the floor |
| 10 | No condition is claimed for log lines, or for a setting about a place of worship | Notice, 8 and 11 | A line can hold the code `health_services`, `community_amenities` or `policy_redirect`, with a time. So can a call record, which is kept for up to 30 days. A shared link can hold a wish for a place of worship. No line says whose it is. [ADR 0011](../adr/0011-nothing-is-kept-for-a-search.md) leaves the log to the founder | Take the four fields off the list of what may be logged. That removes `health_services` and `community_amenities`. It does not remove `policy_redirect`, which is in `interpret_status`, in `call_status` and in the call record. Removing that is a second change |
| 11 | What Burro is and is not responsible for | Terms, 9 | The draft limits little, on purpose. As read in the Consumer Rights Act 2015: an unfair term does not bind a consumer (section 62), liability for death or injury from negligence cannot be excluded (section 65), and in a contract for a service nor can the duty of section 49 (section 57). Section 49 itself was not read. Whether a free website makes a contract at all was not settled. The other choice is a cap on what Burro pays. A cap may be unfair, and the regulator's guidance on it was not read | A fixed-fee review, when there is revenue |
| 12 | "Not advice", made-up data, and a preview | Terms, 2 and 4 | Saying so does not cure a statement that misleads. The law on that was not read. The protection is in the product: the banner, the source and the date under every figure | Keep the banner until every figure is real and finished. Say no more in marketing than the terms do |
| 13 | "18 or over", not checked | Notice, 16 and 20. Terms, 6 and 14 | Google forbids a product "likely to be accessed by" under-18s, and Google comes first. Saying is not checking. Since 26 September 2026 a person confirms it where an account is made, and nowhere else: a search asks for no account, so it stands before nothing that reaches a model. The ICO says of a statement that nothing checks: "It may be suitable for low risk processing or when used in conjunction with other techniques" | Checklist, task 14. [access-by-children.md](access-by-children.md), section 8 |
| 14 | Who is named as running Burro | Notice, 1. Terms, 13 | GOV.UK says a sole trader must put their name on "official paperwork", and does not say whether a website is that. The e-commerce regulations, as read, ask a website for a name and a geographic address. Whether they reach a website that is free was not read. If either applies, a name and an address become public | Checklist, task 1 |
| 15 | Which law and which courts | Terms, 12 | The wording is common. It was not read at a source | A fixed-fee review |
| 16 | No cookie banner is shown | Notice, 2 | That the website sets no cookie and stores nothing is held by tests. That no banner is then needed is an inference. The ICO's page, as read, did not say | Low. Read the ICO's guidance in full |
| 17 | What Burro read in your words is applied without asking, and you can take it off | Notice, 3 and 4. Terms, 5 | It stands after the sixteen before it because it was added after them, on 26 September 2026, and not because it costs less. So do the four of accounts that follow it, which were added the same day. A reading that is wrong now moves the ranking, where it moved an offer that a person could leave. A person may not see that it did. Where a language model reads, what it read is applied once Burro's code has checked it, and the checks were fitted to one model on made-up sentences. Whether a setting that a person did not choose is processing they would expect was not read anywhere | A person reads [ADR 0012](../adr/0012-a-closed-vocabulary-and-a-guard-on-the-model.md), as amended, and says whether a model stays on. Then a qualified reading of the two sentences |
| 18 | A search that is kept in an account needs no special condition | Notice, 11 and 20 | A kept search can hold a wish for a place of worship, or a hospital or a school as a place to reach. With no account it is nobody's. In an account it stands beside an email address, for as long as it is kept. The ICO says that a guess is special category data where a service means to make one, and Burro makes none. But the drafts read that for settings that belong to nobody, and whether a fact that a person chose to keep about themselves is "revealing" of their religion or their health was not read anywhere | A qualified reading. Before that, the ICO's helpline, with the sixth question below. If the answer is that it is: explicit consent, asked where a search is kept |
| 19 | The cookie that keeps a person signed in needs no permission | Notice, 2, 11 and 20 | The ICO lists, as likely to meet the exception for what is strictly necessary, "Identifying a user once they have logged in to an online service for the duration of their visit to the site". The cookie lasts 30 days, across visits. The pages read do not say whether staying signed in between visits is within the exception. The fines under these rules are now those of data protection law | The ICO's helpline, with the fifth question below. The other choice is built by nobody yet: a box to tick, "keep me signed in", without which the cookie ends when the browser is closed |
| 20 | The lawful basis for an account is contract, and for the last searches whatever the founder's choice makes it | Notice, 11 and 20 | The ICO says contract applies where "you need to process their personal data to do what they ask". Whether a person who uses a free website has an agreement with it "which meets the requirements of contract law" was not settled, and risk 11 has the same doubt for the terms. If the last searches are kept from the moment a person signs in, the person did not ask for each to be kept, so the basis is legitimate interests, with an assessment, and the ICO's words on what is so by default weigh against it: "Ensure any default settings offer strong privacy protections" | The founder's choice of E, above. Then a qualified reading, or the ICO's helpline |
| 21 | What is owed to a person whose deleted account is still in a copy of the disk, or who cannot sign in to delete it | Notice, 12, 14 and 20 | The ICO says erasure reaches "backup systems as well as live systems", that the key issue is to put a copy "beyond use", and that a person must be told plainly. That a daily copy kept for 5 days and used only after a failure is beyond use is this draft's reading. If a copy is put back, accounts that were deleted come back, and nothing records which they were. And a person who has lost their mailbox cannot delete their account, while the founder cannot know that an email is theirs | Decide D and H, above, and say both in the notice. Write down, outside the repository, each time a copy of the disk is put back, with the day the copy was made |

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
| 1 | People may type something sensitive into a free-text box. We keep none of it. We send it to a processor that keeps it for up to 55 days. Must we ask for explicit consent before the first sentence, or is a clear notice enough? And if a notice is enough, must it stand beside the box where a person types, or may it stand on a page that every page of the website leads to? |
| 2 | We keep no record of who visits. If consent is needed, how do we show it was given? |
| 3 | We hold nothing that says whose a search was. May we rely on Article 11 when a person asks for their data? |
| 4 | We show published census shares for areas of 5,000 to 15,000 people, ethnic group and religion among them, and we rank areas on the age of residents and on what households are made of. We hold nothing about any person. Is any of that processing of personal data? |

Two questions more, for accounts:

| # | Question |
|---|---|
| 5 | A person signs in by a link sent to their email address. We then keep them signed in with a cookie for 30 days, so that they are not sent an email at every visit. We set no other cookie but one that lasts 15 minutes while they sign in. Is the first within the exception for what is strictly necessary, or must we ask before we set it? |
| 6 | A person who has signed in may keep a search. It holds the places they need to reach and what matters to them, which may be a place of worship or a hospital, beside their email address. We draw no conclusion from it and treat nobody differently for it. Is it special category data? |

## What disagrees with these drafts

Each is outside `docs/legal/`, so none was changed for these drafts.

| Where | What it says | What is so |
|---|---|---|
| `apps/web/src/content/methods.ts` | "Nothing that describes who lives somewhere is used", and of the features, "None describes who lives there" | Changed on 2026-09-24, when core came to hold four measures of age and of households. It says the words of [residents-crime-and-equality.md](residents-crime-and-equality.md), section 11, but for the year of the census, which is in the name of each measure. The part on what Burro holds about residents is not written |
| `apps/web/src/content/vibes.ts`, `apps/web/src/content/area.ts` | A vibe "is named for the place, never for who lives there". "Nothing about who lives in a place is compared" | The first was changed the same day: a vibe that counts who lived in an area says so. The second stands, and is still so. Since 26 September 2026, when the words of the website were written again, it reads "Burro compares nothing about who lives in a place." |
| `packages/core/AGENTS.md` | The Gritty that holds recorded incidents "is refused in any release that is not synthetic. Do not loosen that rule: changing it is changing ADR 0006" | ADR 0006 was changed on 24 September 2026. The rule is still in the code |
| `services/api/src/burro_api/providers/choose.py` | It holds all four providers alike | The founder decided that DeepSeek never reads what real people type. No code refuses it |
| `apps/ios`, `SearchCopy.swift` and its tests | A provider "may keep it for up to 30 days" | It is true of two of the four, and Google comes first. [ADR 0019](../adr/0019-no-one-provider-and-a-key-alone-turns-nothing-on.md) says what the app needs |
| [deploy/README.md](../../deploy/README.md) | Vercel's log holds "the path, the query string, the status and the browser's name" | Vercel's page also says it can match a request by internet address. Read on 23 September 2026 |
| [deploy/README.md](../../deploy/README.md) | Fly.io is a processor and must be named | No agreement with Fly.io was found. Its list of legal documents was read a second time on 23 September 2026, through an extraction, and named a privacy policy, supplemental terms and terms of service. The terms of service were not read in full for one |
| `services/api`, `calls.py` and `logs.py` | A status of `policy_redirect` is kept in the call record and written to the log | ADR 0011 leaves four fields of the log line to the founder. The status is not one of the four |
| `services/api` | No route deletes one shared link | A person may ask for one to be deleted |
| `services/api`, `admit` in `app.py` | Every call is let in | The terms ask people not to send requests in bulk, and nothing enforces it. With a model on, what stops a bill is the service's own cap on calls to a model, which is for everyone together and tells nobody apart ([ADR 0032](../adr/0032-calls-to-a-model-are-capped-for-the-whole-service.md)), and a cap on spending at the provider |
| `apps/web` | No step asks before a sentence is sent. No page holds a privacy notice or terms. Since 26 September 2026 nothing beside the box says who reads what is typed, and no page says how to report a problem: the statement of accessibility went. **The foot of every page has a link named "Privacy" since that day. It leads to how words are handled, on the page of methods, and to no privacy notice: none is published** | Each is needed before launch, or is decided not to be by the founder, in writing. A link named "Privacy" is read as the way to a privacy notice: once the notice has a page, the link leads to it |
| [accounts-compliance.md](../research/reports/accounts-compliance.md) | Legitimate interests for a typed sentence, and no step that asks | Risk 1 |
| [accounts-compliance.md](../research/reports/accounts-compliance.md) | Sign-in bought from another company, with Apple, Google and a code by email, and "Saved searches store the structured summary" | Accounts were built otherwise on 26 September 2026: a link by email and no other company but the one that sends it ([ADR 0043](../adr/0043-burro-has-accounts-and-a-person-signs-in-by-a-link-sent-by-email.md)). What the report says of what is kept is what was built: the spec, and never the words |
| [deploy/web/README.md](../../deploy/web/README.md), and `apps/web/AGENTS.md` | Each said, until accounts were built, that the website has no route handler, "so nothing a person types passes through Vercel" | It is so of what is typed into a search, and of everything while accounts are off, and each was brought to say so. With accounts on, the website passes the routes of accounts on to the service, and an email address that a person typed passes through it |

## How to keep them true

| Rule | Why |
|---|---|
| Never publish a sentence marked `[NOT BUILT]` or `[FOUNDER]` | It is not true yet |
| Before publishing, check every `[SETTING]` at the host or the provider, and take the mark off only then | The code cannot hold it. A setting changed in a dashboard makes the notice false, and no test fails |
| Before publishing, read every `[SOLICITOR]` and decide whether to ship on this draft's reading | Nobody qualified has |
| When a file named in Appendix B changes, read the sentence beside it | A change to the code can make the notice false |
| Write no provider's period, place or terms in these drafts. Point to the notice the service serves | The service serves it, from one table that a person checks. A second copy here can only drift |
| When the website changes where or whether it tells a person a thing, change the drafts in the same change, and say what they said before | On 26 September 2026 the notice went from beside the box, and the privacy notice had pointed there in 22 places |
| When a host changes, change the notice in the same change | The notice names them |
| When a measure of residents, or a vibe that counts recorded crime, is built, take the mark off the sentence in the same change, and name the test that holds it | The decision is made and the code is not |
| Hold the numbers with a test: 10,000, 50,000, 600 characters, 6 seconds, 1,000 people | The website's copy is held to the decision records that way already |
| Before accounts are turned on, take every mark out of section 20 of the notice and of section 14 of the terms | Accounts are built and are off. The notice was written again for them on 26 September 2026, and most of section 20 is blanks that only the founder can fill. The checklist, under "Before accounts are turned on", has the steps |
| When a table or a column is added to the file that holds accounts, read section 20 of the notice beside it | The notice lists what is kept, thing by thing. A column that is added is a thing that is kept |

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
| The terms of any company that sends email | No company is chosen |
| The regulations on cookies, and the ICO's chapter on how to tell people of one | The ICO's account of the rule and of its exceptions was read. The notice has the address |
| Whether a free website and a person who uses it have a contract | Not read. Risks 11 and 20 |
| What the company that runs the service says of its daily copies of a disk, beyond how often they are made and how long they are kept | Not read. [deploy/README.md](../../deploy/README.md#turning-accounts-on) has what was |
