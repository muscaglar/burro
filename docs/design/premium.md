# The paid tier: the choices, and what to keep open

Status: design, 2026-09-23. Nothing here is built and nothing here is decided. Every price is a placeholder, there to make the sums concrete. It changes no code, no contract and no decision record: section 9 lists what each owner would change. No lawyer and no accountant has read it, and nothing here is legal or tax advice. The founder said at the start: "Premium Sub but initially free. So we plan accordingly." This sets out what that could mean, so that what is built now is not rebuilt when payment arrives.

It rests on [PLAN](../PLAN.md) sections 4, 5 and 11 to 14, on ADRs [0005](../adr/0005-raw-prompts-are-never-stored.md), [0011](../adr/0011-nothing-is-kept-for-a-search.md) and [0014](../adr/0014-evidence-first-and-census-figures-shown.md), on [the contract](contract.md) sections 9 to 11, on [vibes](vibes.md) section 5, on [web](web.md) sections 10 and 12, and on the reports in [`docs/research/`](../research/README.md). Section 8 says what was read on the day, and what was not.

## 0. In short

| Question | Answer |
|---|---|
| What does a search cost to serve | About USD 0.002, where a model reads the sentence and the reasons are templates. Ranking, area pages, comparison and sliders call no model |
| What does that mean for limits | A limit on typed searches is there to stop abuse, and is not worth selling. At 100,000 searches a month the model costs about USD 190 and hosting USD 65 to 120 |
| What can fairly be sold | What is kept for a person over time (alerts), and a finished document (a report, a pack). A one-off payment fits a move of a few weeks. People choose an area once every few years, which favours a pass over a subscription (PLAN section 13) |
| What must be built now | Nothing that takes payment. Four small things: one place for limits, one way to say a limit was met, a counter that holds no search, and an identity that never reaches the reader |
| What is never sold | The source and date of a figure, what Burro cannot see, the census table, the accessible list, the order of the results |
| The largest unknown | Whether anyone will pay. Nothing measures it yet, and nothing can until real data is in |

## 1. What people might pay for

"Harm" asks one thing: would holding it back break the promise that Burro shows its working.

| # | Thing | State today | Cost to serve, each time | Harm if held back | Needs an account | Fair to sell |
|---|---|---|---|---|---|---|
| 1 | More typed searches a day | Route 1. No limit | About USD 0.002 on Gemini (2.1) | None, while the form, the sliders and the rule-based reader stay free | No to count. Yes to carry a paid allowance | Weak. It costs next to nothing |
| 2 | More than 3 places to reach | `max_commutes` is 3 in core | Nothing. Journeys are in the release | Some. Several workplaces on one map is what the plan leads with | No | No. A spec must be valid whoever sends it, or a share breaks |
| 3 | A shortlist kept between visits | Not built. PLAN section 4 has it in v1, with an account | A row in a table | None | Yes | The founder's call (section 7) |
| 4 | Alerts when an area changes | Not built. The plan has a diff report for every release | One email a release, for each area kept | None, if each alert cites the fact that moved | Yes, and an email address | Yes |
| 5 | Comparing more than 4 areas | Route 7 takes 2 to 4 | Nothing | Some. What others charge for comparison was not read | No | No |
| 6 | The full working behind a fit | Built: contributions, weights, facts | Nothing | All of it. It is the promise | No | Never |
| 7 | The area portrait | Designed, vibes 5.1 | Nothing at answer time | Much. It holds what Burro cannot see, and area pages are how a search engine finds Burro | No | Never |
| 8 | More like this | Designed, vibes 7.1 | Nothing. A function of the release | Little | No | Weak |
| 9 | Export of results to a file | Not built | Nothing, if the browser makes the file | None, if the screen shows the same | No | As part of a document |
| 10 | A report for a partner or an employer | Not built | Nothing, if the client lays it out | None, if every figure keeps its source and date | No | Yes |
| 11 | A relocation pack | Not built | As a report, several times over | None | Not for the reader. The buyer may be an employer | Yes. Not measured |
| 12 | Sentences written by a model | `explain()` refuses any writer but the template | USD 18 to 40 for 1,000 searches (PLAN 12) | None | No | Open. ADR 0014 may rule it out (section 8) |

A document names a workplace. It is laid out on the person's device from the spec the client already holds. If a server ever makes one, it keeps nothing of it. No document holds the census table (section 3).

## 2. Three shapes of offer

### 2.1 What the sums rest on

| Assumption | Value | Standing |
|---|---|---|
| A search | One typed sentence that a model reads on route 1. A search by form or slider costs no model call | Definition |
| Model price | `gemini-3.5-flash-lite`: USD 0.30 in and USD 2.50 out for a million tokens, paid tier. Google allows no free tier for a product offered in the United Kingdom | Price read, <https://ai.google.dev/gemini-api/docs/pricing>, 2026-09-23. The rule on the free tier is from [the Gemini report](../research/models/gemini.md), not re-read |
| Tokens a search | 3,000 in, 300 out, 100 of thinking. USD 1.90 for 1,000 searches | Estimate, from the Gemini report. Not measured |
| The plan's figures | USD 2 for 1,000 with template reasons. USD 40 with a larger model writing the reasons. Fixed costs USD 65 to 120 a month | PLAN section 12 |
| Exchange rate | USD 1.30 to the pound | Assumed. Not checked |
| VAT | 20%, inside the price shown. A seller under GBP 90,000 of taxable turnover need not register | Both figures read on GOV.UK. How they apply to Burro: nobody qualified has said |

### 2.2 What a month costs, whatever the shape

| Searches a month | Fixed, USD | Model on Gemini | Total on Gemini | In pounds, upper | Model on the plan's USD 40 | Total on the plan's | In pounds, upper |
|---|---|---|---|---|---|---|---|
| 1,000 | 65 to 120 | 1.90 | 67 to 122 | 94 | 40 | 105 to 160 | 123 |
| 10,000 | 65 to 120 | 19 | 84 to 139 | 107 | 400 | 465 to 520 | 400 |
| 100,000 | 65 to 120 | 190 | 255 to 310 | 238 | 4,000 | 4,065 to 4,120 | 3,169 |

- The plan gives no fixed cost for 100,000 searches. Hosting would rise. By how much is not known. Google caps a new account's bill at USD 250 a month and pauses the service at the cap (the Gemini report): about 131,000 searches at USD 1.90.
- Building a release with a model is a cost of its own: USD 3 to 50 a full build ([researcher design](london-data-researcher.md), section 9). It does not grow with searches.
- Shapes A and B add email for alerts and reminders. No email provider's price was read. Shape C adds nothing.

### 2.3 The three shapes

| | A. Move pass | B. Subscription | C. Pay for the document |
|---|---|---|---|
| What it is | One payment. Everything paid is open for 30 days, then closes. It never renews | A payment every month until the person stops it | One payment for one finished thing. Everything on the screen is free |
| Placeholder price | GBP 12 | GBP 6 a month | GBP 5 a report. GBP 19 a pack |
| Price anchor | Crystal Roof: GBP 7.99 a week, 12.99 a month, 29.99 for 3 months (read on its own site, <https://crystalroof.co.uk/>, 2026-09-23) | None read | None found |
| Free | Search by sentence, form and slider. Map, cards, reasons, sources. Area pages. Comparison. Share links | The same | The same, and a shortlist for the visit |
| Paid | Alerts. Documents. A higher daily allowance of typed sentences. The shortlist too, if the founder chooses | The same, for as long as it is paid | The report or the pack. Nothing else |
| Needs an account | Yes | Yes | No. A single-use token. An employer buys tokens in a batch |
| Needs built | Accounts and a session. The entitlement table with an end date. Hosted checkout. A webhook that writes the entitlement. `GET /v1/me`. Refunds | All of A. Renewal, failed payments, reminders, cancelling in the same place as joining. The subscription duties of 5.3 | The report in core, as facts. The layout in the client. Hosted checkout. Tokens and their redemption. Refunds |
| On iOS | A non-renewing subscription. Burro keeps the end date | An auto-renewable subscription | A consumable purchase |
| Fits a move of a few weeks | Yes | Poorly. Most people would cancel after a month | Yes |
| Main risk | People finish inside the free allowance | Revenue that does not return, and the most to build and to get wrong | A document must be worth more than a screenshot |
| What it holds about a person | An account, an email address, an end date | The same, and a payment that repeats | Nothing. The payment provider holds the buyer |

### 2.4 What is left of one sale

Fees as read on 2026-09-23 (section 5.1). A merchant of record is the seller in law, and charges VAT from the first sale. Figures are in pounds, for a UK buyer paying with a standard UK card.

| Route | Fee as read | Left of GBP 12 | Left of GBP 6 a month | Left of GBP 5 |
|---|---|---|---|---|
| Stripe, Burro as the seller, not VAT registered | 1.5% + 20p. Billing adds 0.7% to a subscription | 11.62 | 5.67 | 4.72 |
| The same, a card from outside Europe, converted | 3.15% + 20p, and 2% | 11.18 | 5.45 | 4.54 |
| Stripe Managed Payments | 3.5% on top of the above | 9.20 | 4.46 | 3.72 |
| Paddle | 5% + USD 0.50 | 9.02 | 4.32 | 3.53 |
| Lemon Squeezy | 5% + USD 0.50, 1.5% more outside the US, 0.5% more on a subscription, 1% on the payout | 8.75 | 4.15 | 3.42 |
| Apple, at GBP 11.99, 5.99 and 4.99 | 15% in the Small Business Program | 8.49 | 4.24 | 3.53 |

Not read: whether each provider takes its fee on the price with VAT or without, and whether Apple takes its share before or after VAT. The table assumes the fee is on the price paid, and Apple's share is on the price less VAT. Paddle asks a seller of anything under USD 10 to write for a price, so two of its three figures are a guess.

### 2.5 Where each breaks even

Sales needed in a month to cover the upper total of 2.2. The first figure is through Stripe with Burro as the seller. The second is through Apple.

| Searches a month | A. Pass, on Gemini | A, on the plan's | B. Subscribers, on Gemini | B, on the plan's | C. Reports, on Gemini | C, on the plan's |
|---|---|---|---|---|---|---|
| 1,000 | 9 or 12 | 11 or 15 | 17 or 23 | 22 or 30 | 20 or 27 | 27 or 35 |
| 10,000 | 10 or 13 | 35 or 48 | 19 or 26 | 71 or 95 | 23 or 31 | 85 or 114 |
| 100,000 | 21 or 29 | 273 or 374 | 43 or 57 | 560 or 747 | 51 or 68 | 671 or 897 |

- On Gemini with template reasons, the fixed costs are nearly the whole bill. Ten passes a month cover 10,000 searches: one sale in every 1,000. On the plan's USD 40 the model is the bill, and the same searches need 35.
- Who writes the reasons moves break-even more than the choice of shape does. It is an open question for the founder.
- Break-even covers hosting and the model. It pays nobody. How many searches one person makes is not known, so the share of people who must pay cannot be stated.

## 3. What never sits behind payment

| Never sold | Why | Rests on |
|---|---|---|
| The source and date of a figure | A figure without them may not be shown at all. A cheaper tier cannot show less evidence, only fewer things | AGENTS.md rule 6. ADR 0014 |
| What Burro cannot see, and what is missing | A gap that is hidden reads as a fact | AGENTS.md rule 7. Vibes promise 3 |
| The working: weights, contributions, the recipe of a vibe, the methods page | It is what Burro is chosen for | PLAN section 2 |
| The order of the results | The same question gives the same answer to everyone. No plan is an input to `rank()`, and no release holds more for a payer | AGENTS.md rule 5. ADR 0002 |
| The census table | It is the statistics office's own table, open to all. Sold, it would be who lives somewhere as a product. It is on an area's page and nowhere else, so it is in no report, no pack, no export and no alert, paid or free | ADR 0014. AGENTS.md rule 8 |
| The list and table beside the map, the keyboard, the screen reader | An adjustment for a disabled person is not an extra | Web section 9. [accounts-compliance](../research/reports/accounts-compliance.md) |
| The form and the sliders | A refused call to route 1 is answered by the rules and the form. Never a login wall | PLAN section 5. Contract 11 |
| Area pages, read with no account | Apple asks that an app works without a login. Search engines must be able to read them | Guideline 5.1.1(v), read |
| The attributions, the synthetic flag, the notice that a model read the words, the crime caveats | The licences require the credit. The rest are warnings | PLAN section 9. AGENTS.md rule 13 |
| A person's own data, deleting it, and reporting a wrong figure | The law gives the first two. A paid "export" is a laid-out document, never a person's own records | UK GDPR, not re-read |

## 4. What must be true of the code now

### 4.1 Where a limit is checked

| Rule | Detail | State today |
|---|---|---|
| One place | `admit` in `services/api/src/burro_api/app.py`. No route tests a plan itself | The function is there, and empty |
| A table, not code | `plan` by `action` gives a number or no limit. Today one row, `free`. A paid tier is a new row | Not built |
| Actions are a closed list | `read_by_model`, `keep_shortlist`, `alert`, `make_document`. A new paid thing is a new action | Not built |
| What may be gated | Route 1's use of a model, and routes that do not exist yet: shortlists, alerts, documents | |
| What may never be gated | Routes 2 to 11 as they stand: rank, reasons by template, areas, geometry, a profile, comparison, place search, shares, meta | No limit today |
| Core never sees a caller | `rank`, `explain`, `facts_for` and `similar` take a spec and a release, and no plan | True today. No test says so |
| One spec and one release for everyone | `LIMITS` in core is one set, so a share made by a payer opens for anyone. No release holds more for a payer | True today |

### 4.2 How a person is told

| Case | The answer | Why |
|---|---|---|
| Before any limit is met | Route 11 serves `plans`: for each plan, what is limited and the number. It is the same for every caller, so it is cached as now | The page can say how many typed searches a day are free, and that the form has no limit, before anyone meets it |
| The allowance of typed searches is spent | Route 1 answers 200 from the rule-based reader, `degraded` true, with `limit`: a code, the scope (`pool` or `account`), and when it resets | Contract 9.4: never a 5xx because a model was not used. PLAN section 5: never a login wall |
| A paid route with no entitlement, or an account's route with no session | 403 `not_entitled`, where `fields` names the action. 401 `sign_in_needed`, only on a route that belongs to an account | Reserved now. The contract says no route returns 401, 403 or 429 in this build |
| Abuse | 429, at the edge and not in a route | |
| The words on the screen | Fixed text for each code, served by the API, as every message is. They say what was limited, what still works and when it resets | The website shows API text word for word |
| On iOS | The same fields. The words name no website and no other way to pay | Guideline 3.1.1(a), read |

### 4.3 How a search is counted without storing it

What is counted is a call, never a search. The count goes up before the words are read, so it is the same whatever was typed and whatever the spec holds.

| Counter | Key | Holds | Kept |
|---|---|---|---|
| The pool | The day | Calls that a model read | One number a day. It is the ceiling on spend, and it needs no identity. **Build this one first** |
| An account's allowance | Account id, day, action | A number | Until the day ends. Deleted with the account |
| A visitor with no account | None in the service | Nothing | The website holds no cookie and no storage (web 10), and an address is never logged (contract 10.1). A limit by address belongs at the edge, where the address already is. How to do that was not read |

| Rule | Why |
|---|---|
| A counter has no column for text, a spec, a place, an area or a hash | As `llm_calls` has none (ADR 0005) |
| A counter holds no time finer than the day, and no call id or request id | A call record holds the second a call was made. A counter that held it too could be joined to it, and would say what an account could not get met |
| A call record and a log line hold no account id and no plan | With few payers, a plan is nearly a name. `CallRecord` and `LOGGABLE` have no such field today |
| A call that the rules answered is not counted against a person. Nothing counts how often one search is repeated | The first is known from the call's status, not from the spec. The second is forbidden by ADR 0011, and nothing here needs it |

### 4.4 How an account attaches without the typed words being tied to it

| Rule | Detail |
|---|---|
| `identify` gives a `Caller` | Anonymous, or an account id and its plan. It is handed to `admit` and to the routes that belong to an account. To nothing else |
| The reader never learns who asked | Route 1 is told one thing by `admit`: whether a model may be used. The interpreter, core, the call record and the log are handed no caller |
| The model provider never learns who asked | No user id is sent with a call. The Claude report already says never to send `metadata.user_id`. The same holds for every adapter |
| The payment provider never learns what was searched | Checkout is the provider's hosted page, so Burro never holds a card. It carries an action and an opaque reference. A product is named "Burro report", never for an area: a receipt that named an area would say where someone means to live |
| What Burro keeps of a payment | `account_id`, `action`, `source`, `status`, `period_end` and the provider's reference |
| A shortlist holds areas, not a search | `account_id` and `area_id`, as contract 11 says |
| A saved search is a new decision | It would hold a spec, and so a workplace, for an account. ADR 0011 allows it once there are accounts. It needs its own record first |
| A document's token is not tied to a spec | Paying buys a token. Redeeming it allows one document. What the document was of is not kept |
| A session changes the website's rules | Web 10 rule 1 allows no cookie and no storage. An account needs one or the other, or a sign-in on every visit. Contract 9.1 sends no credentials header. Both change in the same change that adds accounts |

### 4.5 Tests to write now

| Test | Proves |
|---|---|
| `test_the_order_of_results_does_not_depend_on_who_asks` | Every route of 4.1's "never" row answers the same for every caller and plan, and no function of `burro_core` takes one |
| `test_a_refused_model_call_is_answered_by_the_rules_and_says_so` | The pool at its cap gives 200, `degraded` and `limit`, and the form still works |
| `test_a_counter_holds_a_number_and_nothing_of_the_search` | The canary of the privacy tests is in no counter, and two specs leave the same count |
| `test_a_counter_cannot_be_joined_to_a_call_record` | No field of one matches a field of the other but the day |
| `test_a_call_record_cannot_say_who_called` | `CallRecord` and `LOGGABLE` hold no account and no plan |
| `test_no_document_holds_the_census_table` | When documents exist |

## 5. Payments in practice, for a sole founder in the United Kingdom

Every page was read through a reader that extracts, on 2026-09-23. A quoted figure may differ from the page by a word. Check each at its address before relying on it.

### 5.1 The providers

| Provider | Who is the seller | Handles VAT for you | Fees as read | Read at |
|---|---|---|---|---|
| Stripe Payments | Burro | No. Stripe Tax works it out for 0.5% a transaction, or from GBP 70 a month. Registering and filing stay with Burro | 1.5% + 20p standard UK cards. 2.8% + 20p premium UK cards. 2.5% + 20p EEA. 3.15% + 20p international, and 2% if converted. Billing 0.7%. GBP 20 a dispute. No monthly fee | <https://stripe.com/gb/pricing> |
| Stripe Managed Payments | Stripe, shown as "Sold through Onelink, LLC" | Yes, in over 80 countries, sales at home included | 3.5% on top of the payment fee. Sellers in GB are supported, after an eligibility review. Digital products only. Checkout and Payment Links only | <https://docs.stripe.com/payments/managed-payments/eligibility>, <https://docs.stripe.com/payments/managed-payments/tax-compliance> |
| Paddle | Paddle | Yes | 5% + USD 0.50. No monthly fee. Under USD 10 a sale: "contact us for custom pricing" | <https://www.paddle.com/pricing> |
| Lemon Squeezy | Lemon Squeezy | Yes | 5% + USD 0.50. 1.5% more outside the US. 0.5% more on a subscription. 1.5% more by PayPal. 1% on a payout to a bank outside the US | <https://www.lemonsqueezy.com/pricing>, <https://docs.lemonsqueezy.com/help/getting-started/fees> |
| Polar | Polar | Yes | Free plan: 5% + USD 0.50. 1.5% more for a card from outside the US. Payout fees passed on | <https://polar.sh/resources/pricing> |
| RevenueCat | Nobody: it is not a payment provider. It keeps web and app purchases in step | No | Free to USD 2,500 of tracked revenue a month, then 1%. Whether web sales count was not stated | <https://www.revenuecat.com/pricing> |
| Apple In-App Purchase | Apple | Yes | 15% in the Small Business Program, for a developer with up to USD 1 million of proceeds in the year before. Enrolment is needed. Above that, "the standard commission rate" | <https://developer.apple.com/app-store/small-business-program/> |

### 5.2 Tax

| A sale to a person in | If Burro is the seller | With a merchant of record, or Apple |
|---|---|---|
| The United Kingdom | No VAT until taxable turnover passes GBP 90,000. Then 20% | The provider charges VAT from the first sale. The same price leaves about a sixth less |
| A member state of the EU | VAT is due where the buyer lives. The guidance names no threshold: register for the non-Union scheme in one state, or in each state | The provider's |
| Anywhere else | Not UK VAT. It "may be liable to VAT in the country where the consumer is based" | The provider's, in the countries it covers |

Read at <https://www.gov.uk/how-vat-works/vat-thresholds>, <https://www.gov.uk/vat-rates> and <https://www.gov.uk/guidance/the-vat-rules-if-you-supply-digital-services-to-private-consumers>. The last was updated on 28 March 2022 and may be out of date. It says that for a sale through a platform, "the digital platform is responsible for accounting for VAT". People moving to London buy from abroad: that is the case for a merchant of record, at the cost of section 2.4.

### 5.3 What Apple takes and requires, and consumer law

| Rule | As read | What it means |
|---|---|---|
| Guideline 3.1.1 | "If you want to unlock features or functionality within your app ... you must use in-app purchase" | Anything paid that works in the app is sold in the app, by Apple |
| 3.1.1(a) | Outside named storefronts and the United States, apps "may not include buttons, external links, or other calls to action that direct customers to purchasing mechanisms other than in-app purchase". The United Kingdom is not named | The app cannot point to the website's checkout. The competition authority's proposal to change this was not re-read |
| 3.1.3(b) | What was bought elsewhere may be used in the app, "provided those items are also available as in-app purchases within the app" | A pass bought on the web opens the app only if the app sells it too |
| 3.1.2, and the purchase types | An auto-renewable subscription "must last at least seven days". A non-renewing subscription "does not renew automatically" | The first is shape B. The second is shape A, and Burro keeps the end date in the entitlement row |
| 5.1.1(v) | "If your app doesn't include significant account-based features, let people use it without a login" | Search stays open with no account |
| What Apple takes | 15%, by enrolment | Whether before or after VAT was not read |
| Cancelling within 14 days, regulation 37 | The right is lost only if "the consumer has given express consent" to supply at once and "has acknowledged that the right to cancel ... will be lost" | A tick at checkout, or a refund on request for 14 days. The refund is simpler, and at these prices cheap |
| Subscription duties, DMCC Act 2024 | Not re-read. The accounts-compliance report gives January 2027 and marks the date unverified | Shape B carries reminders, a cooling-off at renewal and an easy exit. A and C do not renew. Whether they fall outside, nobody qualified has said |

Read at <https://developer.apple.com/app-store/review/guidelines/>, <https://developer.apple.com/help/app-store-connect/reference/in-app-purchase-types/> and <https://www.legislation.gov.uk/uksi/2013/3134/regulation/37>.

## 6. The order

| # | When | Build | Why then |
|---|---|---|---|
| 1 | Before the API is public with a model key | The pool of 4.3 in `admit`. The `limit` notice of 4.2. The tests of 4.5 | Spend has no ceiling without it |
| 2 | With it | The names, reserved in the contract: `Caller`, the actions, the three codes, `plans` on route 11. No behaviour | A name is cheap now and a rename is not |
| 3 | With accounts, phase 4 | The entitlement table, every account on `free`. `GET /v1/me`. The account's counter | The accounts-compliance report asks for it from the first day of accounts |
| 4 | At launch | Nothing paid. Count what the table below names | |
| 5 | After launch | A plain line where a paid thing would be: "Not built yet. Tell us you would use it." One press, no text | It measures demand and promises nothing |
| 6 | On the signal | One paid thing, on the web, through a hosted checkout | |
| 7 | After people have paid on the web | The same thing in the app, by In-App Purchase | PLAN section 15: no iOS work ahead of real use |

| Measure before charging | How it is counted, with no search kept | What it answers |
|---|---|---|
| Typed searches a day, and how many the rules answered | Call records, as now | The model's bill, and whether the pool bites |
| Shares and comparisons for each 1,000 searches | The request log, by route template | Whether people bring in a partner. The case for a document |
| Accounts made, and shortlists of two areas or more | Tables | Whether anything is worth keeping |
| Accounts seen again four weeks later | The week an account was last seen | Whether use is a few weeks, as assumed. It decides pass against subscription |
| Presses on "tell us you would use it", for each thing | A counter | Which thing, if any |
| What people say they would pay, and employers or agencies who write in | Asked in person: the plan has testers in phases 0b and 2. An address on the site | A price, and whether shape C has a second buyer |

**The signal that it is time to charge** is all four of these, for two months running. The numbers are first guesses. (1) The release is real London, and nothing on screen is synthetic. (2) Typed searches a month are steady or rising. (3) Presses on one paid thing are at least three times the break-even count of 2.5 for that month: a press is not a sale. (4) At least five people, asked in person, named a price at or above the placeholder. Charging has a cost of its own: PLAN section 9 says a capped review of the privacy documents is the first thing to buy once Burro charges.

## 7. The founder's five decisions

| # | Decision | Recommendation | Why |
|---|---|---|---|
| 1 | Which shape comes first | C, pay for the document, on the web. Then A, the pass, once accounts exist. B only if accounts are seen again months later | C needs no account and holds nothing about a person. It is the least to build. The founder's own word was "Sub": [the design proposals](../research/design/proposal-experience.md) and PLAN section 13 both favour a pass over a subscription |
| 2 | What is free for good | Adopt section 3 as a decision record before anything is priced | It is easier to promise before there is revenue to lose |
| 3 | Is the shortlist free | Yes. Sell alerts and documents | PLAN section 4 already has it in v1. A shortlist is the reason to make an account, and an account is what a pass attaches to |
| 4 | Who is the seller, and where Burro sells | A merchant of record, from the first sale, worldwide but for the EU until the privacy documents are reviewed (PLAN 14, decision 7). Read Stripe Managed Payments' and Paddle's terms before choosing | People moving to London pay from abroad. There is no accountant. It costs about GBP 2.40 of a GBP 12 sale, of which GBP 2 is VAT |
| 5 | Does the app sell the same thing, at the same price | Yes to both, and only after the web has sold it. Enrol in the Small Business Program | Apple requires the sale in the app if the thing works in the app. One price is simpler to explain than two |

Already open for the founder, and needed before any of this: what a visitor may do before a limit applies, whether the website may keep anything in the browser, and whether templates are enough for launch.

## 8. What was read, and what was not

| Matter | Standing |
|---|---|
| Gemini's prices | Read on 2026-09-23. They match the Gemini report |
| Stripe, Paddle, Lemon Squeezy, Polar, RevenueCat, Apple, Crystal Roof, GOV.UK, legislation.gov.uk | Read on 2026-09-23 at the addresses given, through a reader that extracts |
| Whether a fee is taken on the price with VAT or without. Each provider's terms, and whether Burro would pass Stripe's or Paddle's review | Not read |
| The DMCC Act's subscription regime, and the competition authority's proposal on links out of an app | Not re-read. Both stand as the accounts-compliance report left them |
| The price of sending email. How to limit by address at the edge. The exchange rate | Not read. The rate is assumed |
| Whether ADR 0014 rules out a sentence written by a model from the fact table | Not settled. The record says a model "is never asked about a place at the moment of answering". PLAN sections 5 and 8 still hold model-written reasons open. Section 2 gives both columns for that reason |
| What people will pay | Not known. A price read on a page is what another asks, not what it takes |
| Tokens a search, and everything else here | Estimated. No live call was made, no figure was tested against a live service, and no test was run |

## 9. What this asks of other files

Nothing below was changed. Each is for its owner. Nothing is asked of `registry/`, `Makefile`, `README.md` or `pyproject.toml`.

| File | Change |
|---|---|
| `docs/adr/` | A record for section 3, "what is never sold". A record for 4.3, what may be counted and where. A record for a saved search, before one is built |
| `AGENTS.md` | One rule under "Ranking and the LLM": payment never changes a ranking, a figure, a source, or what Burro says it cannot see |
| `docs/PLAN.md` | PLAN 12: the Gemini figure beside the Claude ones. PLAN 14, decision 10: point here, and list the five decisions of section 7. PLAN 5 and 8: say whether ADR 0014 leaves model-written reasons open |
| `docs/design/contract.md` | 9.2: reserve `not_entitled`, `sign_in_needed` and `limit` on route 1. 11: the row on payments names routes 1 and 3, and should name what may never be gated. Route 11: `plans` |
| `docs/design/web.md` | 12: a row for limits and payment. 10: what changes when a session arrives |
| `services/api/AGENTS.md` | `admit` hands a route one answer and no caller. `CallRecord` and `LOGGABLE` never gain an account or a plan |
