# What a journey time needs, and what must be signed for it

Status: design, 2026-09-24. Nothing here is built. No dataset was downloaded or opened to write it, and no publisher's service was asked a question. It is a companion to [Travel times for all of London](london-data-travel.md), which holds the engine, the sizes and the method. This document holds the sources: what each publisher's pages said on 2026-09-24, what a person must sign up for, and what Burro may then say of a journey. It applies ADR [0004](../adr/0004-openstreetmap.md), [0007](../adr/0007-no-solicitor.md) and [0014](../adr/0014-evidence-first-and-census-figures-shown.md).

How to read it: **read** was read on a publisher's page on 2026-09-24, through a reader that extracts the text of a page. An extraction is not the page. Each page was asked of twice, in different words, and a thing is kept only where both gave the same. Where a page was asked of once, the row says so. **Registry** is as the licence registry stood that day. **Not known** is what no page that was read says. Nothing is from memory. Check every quotation in a browser before anything rests on it. Nothing here is legal advice.

"Not read" means that a page was not read, and says nothing of the page or of its publisher.

## 0. In short

| Question | Answer |
|---|---|
| Can any timetable of London be had with nothing signed | No. Every publisher of a timetable asks for an account first |
| What can be had with nothing signed | The streets, the stops and the points a journey starts from. That is enough for a time on foot and by bike, for all of London |
| What puts the first time by public transport on the map | An account on Transport for London's portal. It names no charge and no wait (read) |
| What that time counts | The Underground, the DLR, trams, buses, river services and the cable car. No train |
| What a train waits on | A subscription to Network Rail's schedule on the Rail Data Marketplace, and the agreement saved. The entry is gated (registry) |
| What was settled by reading a page | The steps of Transport for London's portal. That the bus service asks for an account and a credit. Nothing that opens a gate |
| What no page settles | Whether the timetable file asks for a key. Whether it holds the London Overground or the Elizabeth line. How long a rail subscription takes |

## 1. What a time by public transport is made of

A journey is a walk to a stop, a wait, one or more rides, and a walk to the door. Each part has one source, and each source is asked for the use `routing`.

| Part | Source, as the registry names it | Status | Licence | Format | How often it changes | Must a person sign up |
|---|---|---|---|---|---|---|
| Underground, DLR, tram, bus, river, cable car | `tfl-journey-planner-timetables` | approved: routing, scoring, display. One thing to settle before launch | Transport for London's own, based on the Open Government Licence 2.0 | TransXChange XML in a zip | A fresh copy each day. "The timetables are updated every 7 days" (read) | **Yes.** A free account on the portal. The licence runs "from the date of registration" (read) |
| London Overground, Elizabeth line, National Rail | `network-rail-nwr-schedule` | **gated** | Network Rail's, based on the Open Government Licence 3.0 (registry) | CIF, a fixed-width text | Daily, overnight (registry) | **Yes.** An account on the Rail Data Marketplace, and a subscription to the product |
| The walk at each end, and a journey by bike or on foot | `osm-geofabrik-greater-london` | approved: routing | ODbL 1.0 | `.osm.pbf`, 123 MB (read) | About daily | No |
| Where a stop or a station is | `dft-naptan` | approved: routing and others | Open Government Licence 3.0 (read) | CSV or XML. All of Great Britain is 96.9 MB as CSV (read) | Daily (registry) | No. London is chosen on a form and saved by a person. The national file is fetched, from the address the registry entry names |
| Where a journey starts | `ons-lsoa-pwc-2021` | approved: cells, routing | Open Government Licence 3.0 | CSV, 4,994 points | Once a census | No |
| Where a journey ends | `uber-h3` | approved: cells | Apache 2.0 | Software | | No |
| The check of a build, and the route shown when a result is opened | `tfl-unified-api-journey-planner` | approved: display, validation_only | Transport for London's own | A service, asked one question at a time | Live | **Yes.** The same account, and its key |
| A second source of bus timetables | `dft-bods-london-gtfs`, `traveline-tnds` | held | Open Government Licence, the version not confirmed | GTFS. TransXChange | Not read | **Yes**, each. Not needed for a first time |

Three things the table cannot say:

1. **Whether the timetable file holds the London Overground or the Elizabeth line.** The open data page names six modes, and neither is one (read). The page of the Unified API lists "Timetables" among its datasets and both lines among its modes (read). On the publisher's forum a person who uses the data wrote in October 2025 of "static timetables for the Elizabeth line". So the publisher may give both under its own terms, by the service and not by the file. Counting the lines in the file settles the first. The registry entry of the service covers the planner's answers alone, so a timetable taken from the service needs the entry widened first, in a change a person reads.
2. **Whether the stops in the timetable file carry their own positions.** Nobody has opened the file. If they do not, every stop is placed from `dft-naptan`.
3. **The walk inside a station.** No source above holds the way from a street door to a platform. `tfl-step-free-station-topology` holds the step-free ways alone, and says so. The engine walks along streets to the point a stop is placed at. Section 8 says what a card tells a person of that.

## 2. What each publisher's pages said on 2026-09-24

### Transport for London

| Asked | What the pages said | Page |
|---|---|---|
| Is an account needed | Yes. "You need to register to gain access to the live feeds." "By registering to use our open data, you confirm that you accept our Open Data terms and conditions" | Open data page. Portal, sign-up page (asked of once) |
| Is a key needed | For the service, the pages differ. The portal says "it is recommended to register for an account", and its page of products gives 50 requests a minute to a request with no key. The page of the Unified API says "you need to register for access tokens and must send those tokens as part of your request". Burro always sends a key (registry): "please append the `app_key` as a query parameter to your requests". For the timetable file, not known | Portal, front page and page of products. Unified API page |
| What it costs | No page names a charge. The terms say they "apply to TfL's free transport data service" | Terms |
| How long to be granted | No page names a wait or an approval. A confirmation email holds a link that turns the account on | Portal, front page |
| What the terms allow | "Copy, publish, distribute and transmit the Information", "Adapt the Information", and "Exploit the Information commercially and non-commercially for example, by combining it with other Information, or by including it in Your own product or application". "TfL grants You a worldwide, royalty-free, perpetual, non-exclusive Licence to use the Information subject to the conditions below" | Terms |
| What credit is asked | "Powered by TfL Open Data". "Contains OS data © Crown copyright and database rights 2016". "Geomni UK Map data © and database rights [2019]" | Terms |
| What is asked besides | To follow the design and branding guidelines. No more than "500 calls per minute per data feed". That "the information You provide on registration is accurate" | Terms |
| What is forbidden | To use the data "in a way that suggests any official status or that TfL endorses You". The roundel, the maps and the typeface: section 8 | Terms. Branding page |
| Storing, and how long a figure may be shown | The terms hold no clause on either. The open data page gives three timings for the feed: a fresh copy every 1440 minutes, 10 minutes at most between capturing and displaying, and 1440 minutes at most on display | Terms. Open data page |
| How the licence ends | Breaking a condition ends it "automatically". It gives no right to use the data after it has ended. "TfL may at any time revise this Licence without notice" | Terms |
| Which law | "The laws of England and Wales". No territory is named | Terms |
| The file on the page | One zip, 24.31 MB. "The example feed below is not updated and is for demonstration purposes only." The page names no address for the file that is kept up to date | Open data page |
| An account that is not used | "User accounts that haven't made a request in the last year will be automatically disabled and deleted" | Portal, page of questions (asked of once) |

Read on the publisher's forum, which is no page of the registry entry: two addresses of the file that is kept up to date, which the list of files gives in its notes; that the publisher's staff issue the file weekly; and that the older Journey Planner API is being retired, with three of its hosts that "may no longer be accessible" from 26 October 2026. The post does not name the timetable file. Two of these posts can be checked at their own addresses: the retirement at `https://techforum.tfl.gov.uk/t/retiring-legacy-journey-planner-api/6353`, and the post of 3 September 2026, which names the second address of the file, at `https://techforum.tfl.gov.uk/t/transxchange-resolving-issues-with-routes-6-and-185/6341`. The posts of 2025 rest on one reading.

Not read that day: the Syndication Developer Guidelines, which state the timings with "must". The registry holds what was read of them on 2026-09-23.

### The rail industry

| Asked | What the pages said | Page |
|---|---|---|
| Who runs the marketplace | The Rail Delivery Group "provides and manages the RDM service" | Rail Delivery Group, page on the marketplace |
| Is an account needed | Yes. A person is to "register to be able to subscribe to data products" | The same |
| What it costs | The page names no charge. The registry records the product's charging model as Free, read on 2026-09-23 | The same. Registry |
| Which contracts a person meets | Four: "Platform agreement (data consumer)", "Platform agreement (data publisher)", "Data sharing agreement" and "Open Government Licence (OGL3) - Rail Data Marketplace" | The same |
| Network Rail's own feeds site | An account is needed. Access "is provided on a first come, first served basis and is currently restricted to 1,000 users". The page does not say which feeds the site gives | Network Rail, open data feeds |
| What Network Rail forbids | "You may not use our brand or logo or those of any of our partners including National Rail and the train companies. Also, we do not allow any application or website using our data feeds to be called 'official'" | The same |
| Network Rail's licence for its own feeds | Use is allowed "provided that it's in compliance with the terms of the Open Government Licence". No version, no credit wording, no territory. "Access to other data sets from Network Rail may be subject to different terms and conditions" | Network Rail, Data Feeds Licence |
| National Rail's feeds | "The Rail Data Marketplace (RDM) is the new platform for access to both public and private sector rail data." The journey planner's feeds "are available for use under formal licence". The page names no timetable feed | National Rail, developers page |

Not read that day: every page of the marketplace itself, the product page and its licence among them. So what the registry holds of the product stands as it was read on 2026-09-23: free, for "All registered users", with commercial use allowed, a territory of "UK" in one schedule against a "worldwide" grant, and a credit left blank until the agreement is executed. How long a subscription takes to be granted is on no page that was read on either day.

### The Bus Open Data Service

| Asked | What the pages said | Page |
|---|---|---|
| Is an account needed | Yes. "To register for an account, data consumers using the Find Bus Open Data Service will be required to supply an email address" | Department for Transport, implementation guide |
| What it costs | "It's free to access by all" | The same |
| What may end it | The details given at sign-up "will enable us to restrict data consumers access to API keys and data, should data be used illegally, unfairly or inappropriately" | The same |
| What the terms allow | "We encourage consumers to access this for commercial and non-commercial purposes". "Data consumers are free to find commercial or non-commercial uses of the data" | Department for Transport, guidance on finding and using the data. Implementation guide |
| What credit is asked | "Data consumers must acknowledge the source of information in their product or application through a statement of attribution. Data should be attributed back to BODS." No wording is given | Implementation guide |
| Is London in it | The duty to publish covers "all local bus services across England (outside London)". So what it holds of London is there by another route | Department for Transport, collection page |

Not read that day: every page of the service itself, so the terms shown at sign-up and on the download page are still unread. On Transport for London's forum a person who uses the data wrote in September 2025 of "the GTFS timetable published by BODS" as holding Underground services. That is a report, and no page of the publisher's.

### Streets and stops

| Source | What the page said |
|---|---|
| Geofabrik, Greater London | `greater-london-latest.osm.pbf`, 123 MB, with data to 2026-09-23T20:22:04Z. "License: ODbL 1.0". No account is asked for the file |
| NaPTAN | "The NaPTAN dataset is published under the Open Government Licence." The national file is 96.9 MB as CSV and 552.2 MB as XML. One authority is chosen on a form: "Greater London / London (490)". The pages ask for no account |
| Traveline National Dataset | Access is applied for by a form, and the files are on an FTP site. The page names no licence and no credit, and does not name London (asked of once) |

## 3. What is held back, and what would settle it

| Entry | Status | What would settle it | Does reading a page settle it |
|---|---|---|---|
| `tfl-journey-planner-timetables` | approved. One thing before launch | A decision record on showing times worked out from a copy that is rebuilt each quarter, given the three timings the page publishes. Or the publisher's own statement that the timings are not meant for a time worked out from a timetable | No. The page still gives the three timings. The guidelines were not read again |
| The same, its file | No address under `file_urls` | A person who has registered opens the file once in a browser, and says which address it came from and whether a key was asked for | No. No page the entry holds names the address |
| `network-rail-nwr-schedule` | gated | Check 1: the founder registers, subscribes, and saves the agreement as executed, the terms of use and the platform agreement for data consumers. Check 2: what the executed agreement says of territory, and a decision record on a service run in the United Kingdom and read from abroad. Check 3: whether the executed agreement names a credit | No. Each rests on the agreement as executed, which only a subscriber sees |
| The same, for a trial | Lists no internal use | `prototyping_only` added to its uses, in the change that saves the agreement. Until then not even a trial of the converter may open a file: [the travel design](london-data-travel.md), section 2 | It is a change to the registry, and the founder's to approve |
| `dft-bods-london-gtfs` | held | Check 1: an account, and the terms shown at sign-up and on the download page, read and saved. Check 2: the routes and weekday trips of the London file counted by kind. Check 3: where its London content comes from, and whose credit it carries | Part of check 1 is settled: an account is needed, and a credit to the service is asked. The rest is not |
| `traveline-tnds` | held | An account, and the terms sent with it, read and saved | No |
| `rdg-timetable-feed`, `planarnetwork-gb-transit-rail-gtfs` | held | A licence in writing from the Rail Delivery Group that names use in a public product | No. The public licence is for research and analysis alone (registry) |

Nothing was marked approved on 2026-09-24, and no status was changed.

## 4. What can be had with nothing signed

No timetable. Every publisher of one asks for an account, and the one licence that was read in full runs from the day of registration.

The zip on Transport for London's open data page can be opened by anyone. It is not taken. The page says it "is not updated and is for demonstration purposes only", so a time worked out from it would rest on a timetable of no known date, offered for no such use.

| Had with nothing signed | In the list | For |
|---|---|---|
| The streets of Greater London | `m2-living`, as `osm-greater-london` | Every walk, and a time by bike and on foot |
| The stops and stations | `m2-living`, as `naptan-london`, saved by a person, and as `naptan-national`, fetched. Each is listed for scoring, and the entry allows routing | Placing a stop |
| The points a journey starts from | `m2-places`, as `lsoa-centres` | The 4,994 origins |

So **a time on foot and by bike waits on no account.** It waits on the routing build alone: [the travel design](london-data-travel.md), sections 5 and 6.

## 5. The founder's steps, in the order of what each unlocks

A key goes in two places and no other: a password manager, and the secrets of the host that runs the step that reads it. **Never in a chat, never in an email, and never in a file of the repository.** Section 6 names each secret. A key is given to a host on the day a step reads it, and not before.

| # | Step | Where | What to choose | Cost | Time to be granted | Unlocks |
|---|---|---|---|---|---|---|
| 1 | Register on Transport for London's portal | `https://api-portal.tfl.gov.uk/`, then sign up | An email address made for Burro, and details that are true: the licence asks that they are accurate. Follow the link in the confirmation email. If it does not come, the portal says to "check your spam or junk folders". Keep the password in the password manager | None named (read) | None named (read) | **The first time by public transport.** The licence starts to run. Milestone M5 |
| 2 | Subscribe to the product, and keep the key | The same portal, signed in: Products, then Profile | "Create a subscription for the 500 requests data plan". Then read the keys under Profile. Save the key in the password manager, and nowhere else. An account that makes no request in a year is disabled and deleted (read), so an account that is never used is lost | None named | None named | The check of a build against the planner. The route shown when a result is opened |
| 3 | Open the timetable file once, in a browser | The portal, signed in. Failing that, the two addresses in the notes of the list `m5-journeys` | Write down the address the file came from in the end, with no key in it: the portal asks for its key as a part of the address, so if `app_key` or anything like it stands after the `?`, leave out the `?` and all that follows. Write down the size of the file, and whether a key was asked for, as yes or no. Do not keep the file: fetch takes it, so that it has a receipt | | 15 minutes | The address in the registry and in the list. The first fetch |
| 4 | Save dated copies of what the licence rests on | The terms, the open data page, the branding page and the guidelines | Each as a PDF, from a browser that is signed out, in `registry/evidence/`, named as the README there says. Nothing that holds a person's name, an email address or a key is saved there | | 30 minutes | A condition of the entry. The answer if the terms are ever revised |
| 5 | Register on the Rail Data Marketplace, and subscribe to the schedule | `https://raildata.org.uk/`, then the product "NWR Schedule" of Network Rail | Register as one who uses data. Subscribe to the one product. Read and save the agreement as executed, the terms of use and the platform agreement for data consumers. The agreement as executed names whoever signed it, and `registry/evidence/` takes nothing that holds personal data. So it stays with whoever signed it, as a written reply does, until the founder has decided what of it the repository holds: a copy with the name and the account taken out, or a dated note. The two other papers are standard ones, each at an address of its own: save them signed out | Free (registry, 2026-09-23) | Not known | Gate checks 1 and 3. A trial of the converter, once the entry lists `prototyping_only` |
| 6 | Decide gate check 2 | A decision record | What the executed agreement says of territory, and whether a service run in the United Kingdom and read from abroad is within it | | 1 hour | **Every time by train.** All of London with no notice about trains. Milestone M7 |
| 7 | Write the decision record on the timings | A decision record | How often everything worked out from the feed is rebuilt, against the three timings the page gives | | 1 hour | The launch. The entry names it under `before_launch` |
| 8 | If a second source of timetables is wanted: an account on the Bus Open Data Service | `https://data.bus-data.dft.gov.uk/` | An email address. Read and save the terms shown at sign-up and on the download page | Free (read) | Not known | Check 1 of the held entry. A count of what the London file holds. No time rests on it |

Steps 1 to 4 are an hour together. Step 5 is two to three hours, by [the plan](london-data.md), section 6, which is an estimate. Nothing above waits on a reply from a data owner (ADR 0007).

Step 1 is the first that puts a journey time by public transport on the map. A time on foot or by bike needs none of the eight.

## 6. The secrets, by name

No workflow reads any of these yet. Each name is proposed here, and is set on a host on the day a step reads it. [The guide to data builds](../data-builds.md), section 4, gains a row that day, and says how a secret is pasted.

| Name | What it holds | Read by | Set in |
|---|---|---|---|
| `BURRO_TFL_APP_KEY` | The key of the subscription on Transport for London's portal | The step of a build that checks 1,000 pairs against the planner. The API, when a result is opened | The environment of the workflow that routes, on GitHub. The secrets of the API's host |
| The same | | The fetch of the timetable file, and only if step 3 finds that the file asks for a key | The environment `data-fetch` |
| `BURRO_RAIL_KEY`, `BURRO_RAIL_SECRET` | What the marketplace gives a subscriber to take a file with. Its shape is not known until step 5 | The fetch of the schedule | The environment `data-fetch` |

Three rules the key of Transport for London needs, because the portal asks for it as a part of the address:

1. No address that holds the key is printed, logged or written to a receipt. Fetch already refuses a list whose address names a parameter that is taken for a key.
2. The key stays on the server. It is never sent to a browser or to the app (registry).
3. The key is changed on any doubt, and the old one is removed at the portal.

## 7. The list of files

The list `m5-journeys` is in `packages/pipeline/src/burro_pipeline/fetch/lists/`. A file is listed once, so what another list holds is left there.

| File | List and item | Page | Address of the file | Size | Edition and period | Not sure of |
|---|---|---|---|---|---|---|
| Transport for London's timetables | `m5-journeys`, `tfl-timetables` | `https://tfl.gov.uk/info-for/open-data-users/our-open-data` | None on the page. Two were read on the publisher's forum, and are in the item's notes | Not known. The example on the page is 24.31 MB | None on the page. The file is replaced under one address. The period is the days its timetables say they run on | The address, the size, the edition, the period, whether a key is asked for, and which lines it holds |
| The streets | `m2-living`, `osm-greater-london` | `https://download.geofabrik.de/europe/united-kingdom/england/greater-london.html` | `https://download.geofabrik.de/europe/united-kingdom/england/greater-london-latest.osm.pbf` | 123 MB | The time its header says its data runs to, which fetch reads in the file | Whether it reaches a few kilometres past London's edge |
| The stops and stations | `m2-living`, `naptan-london` | `https://beta-naptan.dft.gov.uk/` | None: a form, saved by a person | Under 96.9 MB | The day it was saved | Its format as it arrives |
| Where a journey starts | `m2-places`, `lsoa-centres` | The record at data.gov.uk that the registry entry holds | On the portal of the statistics office, as the list gives it | About 4 MB | V4, December 2021 | The address, until a fetch has tried it |
| The rail schedule | In no list: the entry is gated | `https://raildata.org.uk/dataProduct/P-dbd92416-2f09-4f72-ad42-d53bbfec50f3/overview` | Not known | Not known | Daily. The timetable changes in May and December | Everything, until a person has subscribed |

## 8. What Burro may say of a journey

A card says three things of a journey: the time, what it was worked out from and when, and what it cannot see. Every date and every name in them comes from the record of the build, `inputs` and `method` in `travel.json`: [the travel design](london-data-travel.md), section 10. A client writes no date of its own.

### The time

These are the contract's own templates ([contract](contract.md), section 7.3), and are not changed here.

| When | Sentence |
|---|---|
| Both times are known | By public transport to {place}: about {typical} minutes on a typical weekday morning, {missed} if you just miss a service. |
| The release counts no train | The same, then: Trains are not counted. |
| By bike, or on foot | {mode} to {place}: about {minutes} minutes. |
| Beyond the longest journey that is worked out | {mode} to {place}: more than {cutoff} minutes. |
| No time, in a release that counts no train | There is no public transport time from {name} to {place} in this release. A train may be the way to travel, and train times are not in Burro's data yet. It was left out of the score. |
| No time, for any other reason | There is no journey time from {name} to {place} in this release, so that journey was left out of the score. |

### What it was worked out from, and when

One sentence, set under the time. Each part is there only if the build read that source.

| Release | Sentence |
|---|---|
| Without trains | Timetabled time, worked out by Burro for departures between {from} and {to} on {day}. From Transport for London's timetables of {timetables_date}, over streets © OpenStreetMap contributors, {streets_date}. Powered by TfL Open Data. |
| With trains | Timetabled time, worked out by Burro for departures between {from} and {to} on {day}. From Transport for London's timetables of {timetables_date} and Network Rail's schedule of {schedule_date}, over streets © OpenStreetMap contributors, {streets_date}. Powered by TfL Open Data. Contains public sector information licensed under the Open Government Licence v3.0. |
| By bike, or on foot | Worked out by Burro over streets © OpenStreetMap contributors, {streets_date}, at {speed} kilometres an hour. |

"OpenStreetMap" is a link to its copyright page (ADR 0004). The other two statements Transport for London asks for, on Ordnance Survey's and Geomni's data, are on the sources page with the first, word for word. The credit for the rail schedule is the default of its licence until the executed agreement is read: gate check 3.

### What it cannot see

One sentence, set last, and the same on every card.

> This is a time from the timetable. It knows nothing of a delay, a closure or engineering works, of how full a train or a bus is, or of the walk inside a station. It is for a weekday morning, and says nothing of an evening or a weekend.

| It cannot see | Why | Where that is said |
|---|---|---|
| A delay or a closure | A timetable is a plan. The publisher says its timetables "do not take account of planned engineering works" | The sentence above. The methods page |
| A crowded train | No source that is read counts people | The sentence above |
| The walk inside a station | A stop is a point. The way from the street to a platform is in no source that is read | The sentence above. The methods page gives the rule for placing a stop |
| Which line a time rests on | The table holds minutes, and no route | Nothing names a line beside a time |
| A hill, on a bike | The streets are taken as flat | The methods page |
| A fare | No fare is read | Nothing is said of cost beside a time |

### What a card never shows

The rules are the publishers' own (read), and the registry holds each as a condition.

| Never | Whose rule |
|---|---|
| The roundel, or any logo | Transport for London: "The TfL roundel is a trademark of TfL". "Use or adapt our branding" |
| A map of the publisher's | "Use our maps without a licence" |
| The New Johnston typeface | "Use New Johnston font without a license" |
| The colour of a line as the publisher draws it | Burro's own choice, under "Use or adapt our branding". The page does not name line colours |
| A trade mark in the name of the product or of a page | "This includes use as part of app names" |
| "Official", "in partnership", or any word of the kind | Transport for London: "any terms that imply a commercial partnership with TfL". Network Rail: no product "called 'official'" |
| The brand or logo of Network Rail, of National Rail or of a train company | Network Rail |

| May be written | For what |
|---|---|
| "London Underground", "Tube", "London Buses", "DLR", "London Overground", "London River Services", "London Cable Car" | "Only (1) in travel tools to label services, for service messaging, journey planning and wayfinding; and (2) in app store descriptions and marketing to describe services" |
| "Elizabeth line", "tram" | The publisher's list names neither. Burro writes each as the plain name of a service, in the same two uses and no other. That is Burro's reading, and not the publisher's word |

## 9. What this asks of others

| Where | Change | Why |
|---|---|---|
| Registry, `tfl-journey-planner-timetables` | The address of its file under `file_urls`, after step 3 | Fetch refuses an address the entry does not name |
| The list `m5-journeys` | The same address under `url`, in the same change. Then the edition and the period, once a person has read them in the file | So that the first fetch can be made, and the second can write a receipt |
| Registry, `network-rail-nwr-schedule` | `prototyping_only`, in the change that saves the executed agreement | [The travel design](london-data-travel.md), section 13 |
| Registry, `tfl-unified-api-journey-planner` | A wider use, if timetables of the London Overground and the Elizabeth line are ever taken from the service | The entry covers the planner's answers alone |
| Contract, section 7.3 | The sentence of section 8 that says what a time was worked out from, and the one that says what it cannot see | Neither is a template yet. Each holds names and dates, so each must pass the verifier |
| Fetch | A way to send a key that is not a part of an address, if step 3 finds that the file asks for one | An address in a list holds no key |
| [The guide to data builds](../data-builds.md), section 4 | A row for each secret of section 6, on the day a workflow reads it | The guide names a secret only where a step reads it |

## 10. What was read, and what was not

Read on 2026-09-24, through a reader that extracts. Twice, in different words, but where the row says once.

| Publisher | Page |
|---|---|
| Transport for London | The front page for open data users. Our open data. The terms of the Transport Data Service. Design and branding. The Unified API. The open data policy, once |
| Transport for London, the portal | The front page. The sign-up page, the page of products and the page of questions, each once |
| Transport for London, the forum | The front page, the first three pages of the category for open data, and seventeen of its topics, most of them once |
| Network Rail | Open data feeds. The Data Feeds Licence |
| Rail Delivery Group | The page on the Rail Data Marketplace. The page on rail data, once |
| National Rail | The developers page |
| Department for Transport | The collection page of the Bus Open Data Service. The guidance on finding and using the data. The implementation guide. NaPTAN: the download page, the national download, the download by authority and the terms, each once |
| Geofabrik | Greater London, once |
| Traveline | The National Dataset, once |

Not read on 2026-09-24:

| Page | So |
|---|---|
| Every page of the Rail Data Marketplace | The registry's record of 2026-09-23 stands. Steps 5 and 6 rest on it |
| Every page of the Bus Open Data Service itself | The entry stays held |
| Network Rail's own feeds site, and the National Rail Data Portal | Nothing is said of either but what Network Rail's own page says |
| Transport for London's Syndication Developer Guidelines, and the developer pack of National Rail Enquiries | The registry's record of the first stands. Nothing is said of the second |
| The pages of the portal that only a person who has signed in sees | Steps 2 and 3 say what to look for |

Not known, and nothing here should be read as if it were:

| Thing | What settles it |
|---|---|
| Whether the timetable file asks for a key | Step 3 |
| Which address the timetable file is at | Step 3 |
| Which lines the timetable file holds | Counting them in the file |
| The size of the timetable file | The first fetch |
| How long a rail subscription takes | Step 5 |
| What the marketplace gives a subscriber to take a file with | Step 5 |
| Whether the key of the portal may be sent in a header | The portal's pages for a person who has signed in |
