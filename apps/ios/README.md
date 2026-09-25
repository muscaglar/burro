# Burro for iPhone

The same product as the website, as a native app: a sentence, then ranked areas on a map, then refining by typing again or with controls. Every sentence about a place and every figure comes from the API. The app adds a shortlist kept on the phone, the phone's own share sheet, and a screen before the first search that asks whether your words may be read.

It is SwiftUI, for iOS 17 and later, in Swift 6. It depends on no package. [AGENTS.md](AGENTS.md) has the rules for changing it.

**It has never been run.** Nothing in it has been seen on a screen, in a simulator or on a phone. [What has and has not been checked](#what-has-and-has-not-been-checked) says where that leaves it, and [Known issues](#known-issues) lists what a review of the source found. If you run it, say what you see that differs from this page.

## Open it

You need a Mac with Xcode and a simulator for iOS 17 or later. The project was made with Xcode 26.5, and its format needs Xcode 16 at least.

1. Open `apps/ios/Burro.xcodeproj` in Xcode.
2. Choose the scheme **Burro** and an iPhone simulator.
3. Press Run.

To run on a phone, choose your own team under Signing & Capabilities in Xcode, and do not commit that change. The project names no team.

## Point it at an API

The app reads two build settings. Both are written into `Info.plist` when the app is built.

| Setting | Debug | Release | What it sets |
|---|---|---|---|
| `BURRO_API_BASE_URL` | `http://127.0.0.1:8000` | None | Where the API is. `http` is taken for `localhost` and `127.0.0.1` alone. Any other address must be `https`, so that nothing typed crosses a network in the clear. With none set, the app says it is not connected to Burro's data |
| `BURRO_SITE_URL` | None | None | The website's own address, as an `https` origin with no path. It is what a share link begins with. With none set, no "Share" is offered anywhere |

**On a simulator**, a Debug build reaches the API on your Mac with nothing to set. From the top of the repository, in a terminal:

```
make setup
make api
```

Leave it running and press Run in Xcode. A simulator shares the Mac's network, so `127.0.0.1` is the Mac.

**On a phone**, `127.0.0.1` is the phone itself. Give the app an `https` address the phone can reach:

```
xcodebuild -project apps/ios/Burro.xcodeproj -scheme Burro BURRO_API_BASE_URL=https://api.example.org build
```

or set `BURRO_API_BASE_URL` in the target's build settings in Xcode, and do not commit it.

**To see sharing**, set `BURRO_SITE_URL` to any `https` origin, such as `https://burro.example.org`. The link is handed to the share sheet and is not fetched by the app. Opening a link from outside the app needs an associated domain, which is not set up: see what is not built.

## Check it without a simulator

Needs a Mac with Xcode that can run `swift test`. From `apps/ios`:

```
make check      generated files in step, the tests, and the app compiled for iOS with signing off
make generate   after contracts/openapi.json, the website's tokens or the recorded answers change
make test ONLY=BurroKitTests.VisitTests
```

`make test` is `swift test`, with a warning treated as an error. `make build` is `xcodebuild` for any iPhone, in Debug and in Release, with code signing off. Hosted CI runs the three parts of `make check` on a Mac, in its job `ios`. It runs each part though one before it failed, and says what a failed part printed where it can be read without signing in.

## What has and has not been checked

- **Written against the contract and the recorded answers.** The models and the routes are generated from `contracts/openapi.json`. The tests answer from the website's recorded answers, copied from `apps/web/test/recorded`. `make generate-check` fails if a generated file is out of step, and needs python3 alone.
- **It reads version 2 of the contract.** The models in `API/Generated` are generated from it, and the code that reads them was brought to it: vibes as bands of five, what Burro noticed and did not apply, what the release does not hold, whether the release is a preview, who reads what is typed, and when the provider of a model would not read it. Each test that names a figure was brought to the answers as they were recorded on 2026-09-24, and on 2026-09-25 for what one press takes and for a vibe that is a rough guide. What those tests expect was worked out from the recordings, and the job `ios` is what confirms it. Since 2026-09-25 a test reads from the recording what the service made or said of the build that answered: the id of a share, the release, and how many areas an answer holds.
- **An offer is drawn whole.** Since 2026-09-24 the API serves an offer in four parts, with Burro's guess marked and with the way one press may add, and serves the census of an area on a route of its own. The models read all of it. A sentence is sent to the rules first, and then to a model where one has more to read, as the website sends it. What the rules offer is drawn at once, and while the model reads the screen says so. The app draws the four parts in the website's words and order: what the offer would do, under "You wrote" the person's own words cut from the box, what follows, and the choices, with Burro's guess marked. It takes a choice by its id and sends that choice's own edits. Of what one press may add it follows the API, and works nothing out. A journey to a place Burro does not know asks which place, under the offer, and is sent with the place that is chosen and the way that was pressed. What carries Burro's guess is drawn first, in the order its words stand in the sentence. Since 2026-09-25 one press takes what a person plainly said of the home they look for, with a budget as they worded it, and a journey that was plainly said as a guide, because the API names it so. After "Add all" the screen says what was done, in full: how many things were added, how many areas a firm budget among them left out, and what is left for the person. "Take it all back" puts the search and the offers back as they were. Since 2026-09-25 what is left after that press is folded to one line, "Show the 7 left to choose", as on the website, so that the way to the list and the map is in sight. One press opens them all, and they fold again when one of them is added or skipped: the line above then says what was chosen since, "Then 1 more added." or "Then 1 skipped.", and no longer names it as left. The website gives the focus to the line that opens them. The app leaves where VoiceOver stands to the phone, and says the line when it changes. The app asks for no census.
- **A credit is drawn beside a fact.** A publisher may ask that its own statement of credit stands wherever a figure made from its data is shown, and its terms may ask that something is said with the credit. The API says which source asks, and brings both with the fact. Since 2026-09-25 the app draws them in the line that ends every sentence and every figure: after the name of the source and before the date, each line of the statement as a sentence, and what is said with it after it, as the website writes them. A statement that two sources of one publisher bring is said once under a figure. The line is drawn on a result, in how its fit is worked out, in a comparison, on the screen of an area and on a saved area, where the statement is kept with the fact so that it is said with no connection. Where a source brings none, nothing is drawn for one. The made-up release holds no such source, so no recorded answer holds a credit: the tests of what is drawn make their facts from recorded ones. The screen of sources is as it was.
- **The tests and the build are yours to run.** They must be run on a Mac with Xcode, with `make check`, and by the hosted check. This page gives no count of tests and does not say that a build passes. Go by the last run of the job `ios`.
- **Nothing has been seen.** Not on a screen, not in a simulator and not on a phone. The two sections below say what to look at first, and what is unknown until somebody does.

## What to look at first

Nobody has done this yet. The right-hand column is what the tests expect the app to show, with the API serving the synthetic release on ranking engine 1.12.0, as it was on 2026-09-24.

| Do this | You should see |
|---|---|
| Open the app for the first time | "Before your first search", under three headings: what is sent, who reads it, what is kept. Who reads it is said in the API's own words: with no model key, that rules that are part of Burro read what you type, and that it is not sent to a language model. Two buttons: "Allow and continue", which is switched off until the API has said who reads, and "Use the settings instead". No banner, because no data is shown |
| Press "Allow and continue" | Three tabs: Search, Shortlist, About. A yellow banner above them that says the data is made up. It cannot be closed. On Search: "Describe the life you want", examples, renting or buying, "A place you need to reach", and the settings |
| Type `Renting a 1 bed for about £1,700 a month, leafy and quiet, 35 minutes to Cindermoor Works` and press Search | "Reading", then the results screen: a map of 24 areas in five shades of green with pins numbered 1 to 10, and a panel over it with 20 results. The first is **Farrowmere**, "Fit 71 of 100", with a strip of vibes, each a band of five with "asked for" on the two that were, then up to three reasons, a trade-off, and the source and date written under every line. Above the list: "21 areas ranked. First: Farrowmere. What you asked for counts most." |
| Drag the panel, or press its handle | It stands at three heights. "Map", "List" and "Table" above it change what is shown. The table holds every area, with its status in words |
| Go back to Search | Chips under "What Burro understood": renting, the budget, Cindermoor Works, and what was asked for. Each part nobody chose is marked "assumed". Under them: "Read without AI." |
| Type `a bit more green space, and ignore the high street`, press Search | The results again, in a new order. On Search, a chip for the distance to the nearest town centre that says "does not count" and has no "Remove" |
| On Search, open the chip for Cindermoor Works and switch on "The journey is a firm limit" | You stay on Search. "Show results" leads to 14 results. In the table, seven areas say a journey is longer than a firm limit, and the map draws them with lines across |
| Type `and 30 minutes to Pellam`, press Search | You stay on Search. "Which place did you mean?", with Pellam Cross, Pellam Exchange and Pellam Infirmary. Pick one and it becomes a chip |
| Type `not too many students, and near a park`, press Search | You stay on Search. One sentence in a plain block: "Burro ranks places by what is there. Of who lives in a place it counts only their age and their households, at the census of 2021, and you cannot ask for fewer of anyone. The rest of your search has been applied." Nothing says what was left out |
| Start again, type `Pubs are so noisy`, press Search | You stay on Search, and nothing is ranked. "Choose what to add", with two offers, each in four parts. The first says "Pubs and bars: more, or fewer?", then "You wrote" with the sentence you typed between quote marks, then "What Burro counts: pubs and bars for each 1,000 homes within 800 m, in a straight line.", then "More pubs and bars", "Fewer pubs and bars" and "Skip". The second says "Less transport noise: count it?", with "Add" and "Skip". No button adds both. On iOS 18 and later, "Show the words" selects in the box the word each rests on. "Fewer pubs and bars" ranks, and leaves the other still to choose |
| On a result, press "Open the page" | The area: where it is, with a small picture drawn from the API's outlines, stations, what homes cost, "Character" with each vibe as a band of five under the list the API put it in, everything measured there, and "In your search" with its rank and fit |
| Press "Add to shortlist", then open the Shortlist tab | The area, with the day it was saved, under "Kept on this phone. Burro does not hold it." |
| Stop `make api`, close the app and open it again, then open the Shortlist tab and the saved area | The banner is still there. The area opens with its figures as they were when it was saved, under a line that begins "This is the data as it was when you saved this area". The Search tab says "Burro could not be opened", with "Try again" |
| Start `make api` again. Search, then on two results press "Add to compare", then "Compare 2 areas" | A screen of its own: each thing that counts, and under it each area by name. Back leads to the results |
| With `BURRO_SITE_URL` set: on the results, "Share this search", then "Make the link", then "Share" | What the link will hold, said before anything is made. Then the phone's own share sheet, with a link that ends `/s#` and 22 letters and digits |
| In About, "Read it again and choose", then "Use the settings instead" | On Search, a line in place of the box, and the settings open. Every control works. No sentence can be sent |
| Set the text size to the largest in the simulator's accessibility settings, and turn VoiceOver on | Nothing is cut off, and every control has a name. This is the part most likely to be wrong |

## What has never been seen running

Everything on a screen. In particular:

- **Layout.** Every screen at every size of text, in light and dark, in portrait and landscape. Whether anything is cut off, overlaps or is too small to press.
- **The map.** Whether MapKit draws the polygons, the lines, the dots and the pins as asked. Whether the camera frames the city in the part of the map the panel leaves free. Whether a press on the map finds the area under it. Whether it is fast enough with 450 areas: the synthetic city has 24.
- **The panel over the map.** Its three heights and its drag.
- **VoiceOver.** The order of each screen, that a sentence and its source are read as one, that announcements are spoken, that the map can be used at all.
- **The keyboard.** Whether Return in the box sends the search. Whether the keyboard covers the field being typed in. Whether refusing other makers' keyboards works as the code asks.
- **The cover.** Whether the plain cover is drawn in time for the picture the phone keeps of the app for its switcher.
- **The network.** The app has never called a real API. Every test answers from a recording through the real client, with a stand-in where the network would be. That a redirect is refused, that nothing is cached, and how App Transport Security treats the address, are untried.
- **Files on a phone.** That the three files are locked while the phone is, and left out of backups. The test checks the backup flag on a Mac.
- **The share sheet**, and opening a link from outside the app.

## Known issues

A review of the source found these eleven. The third is settled in part, and no other is fixed. The most serious is first. The first three must be settled before anything is submitted to the App Store.

1. **Coming back to the app sends what is in the box, with no press.** *Settle before the App Store.*
   After a sentence fails to leave because the phone is offline, each return to the app sends the text then in the box to be read. The person may have changed it, and has not pressed Search. The screen promises "Nothing is sent until you press Search", and the website sends no words on coming online.
   Fix: on return, call `flow.wentOnline()` only, and leave the sentence to "Try again". Change the visit test to expect one reading until the button is pressed.
2. **The privacy manifest says nothing is collected.** *Settle before the App Store.*
   `App/PrivacyInfo.xcprivacy` declares no collected data, and `PrivacyRulesTests` holds it to that. A share stores the search on the server until it is deleted, and a model's provider may keep what is typed for as long as the API's notice says. Apple counts both as collected, so a label of "Data Not Collected" would be untrue, which is a ground for rejection or removal.
   Fix: decide the label, make the manifest and the test match it, and record the decision in an ADR.
3. **There is no privacy policy to open, and nothing says the map is Apple's.** *Settle before the App Store.*
   The permission screen and About now say who reads what is typed in the API's own words, which name the company where a model reads. What is left: About says there is no code from anyone else, and does not say that the results map is Apple's. No privacy policy can be reached in the app. After "Use the settings instead" the screen says nothing typed is sent, while a place typed is still sent to Burro. A person who agreed while rules read is not asked again if a model reads later: the line under the box says who reads now. App Review guidelines 5.1.1(i) and 5.1.2(i) ask for a policy in the app, and for a third party to be named before data is shared with it.
   Fix: add a line about the map. Link the privacy notice once the website has an address, and hold submission until it exists. Reword the line shown after declining. Decide whether a change of reader asks again.
4. **The map is rebuilt whole on every change of state.**
   `Results.mapped` runs inside the view's body, about ten times for one sentence, and makes a new shape for every area each time. Each line and dot of a pattern is an overlay of its own: the review counted 109 to 297 overlays for the 24 made-up areas. With the 450 areas expected for London that is thousands, made again at every press. It is the likeliest thing to make the app unusable on a phone.
   Fix: work the map out only when the ranking, the chosen area or the boundaries change. Make the polygons once for a release. Draw a pattern as one overlay. Then measure on a phone with 450 areas.
5. **A saved area waits on the network before the copy on the phone is shown.**
   Opening a saved area waits for the release, then asks for the area, and only then falls back to the copy it held all along: up to 20 seconds on a weak connection. The shortlist is the part meant to work with no connection, and a weak connection is what a phone has on the Underground.
   Fix: when a kept copy exists, show it at once with its "as saved" line, then ask the API and replace it if an answer comes.
6. **A share link can be shown as the link of a search it was not made of.**
   The link is tied to the hash of the search as it stands when the answer comes back, not when the request was sent. If the search changes in between, the link holds the old search and is shown as the link of the new one.
   Fix: read the hash before the request is sent, and use that. Add a test that changes the search while the link is being made.
7. **The results card and the area page use different rules for "Trade-off".**
   The card shows the API's trade-off sentence only when the ranking says the area does badly on it. The area page shows whatever sentence came. One area could then say two things on two screens. No recorded answer shows it today.
   Fix: use one function for both screens, and test an answer whose trade-off is something the area does well.
8. **With VoiceOver the map's marks come before the results, and a change may be announced twice.**
   The map is first in the stack, so up to 40 marks and the legend are met before the headline and the first card. The search screen stays alive under the results and announces the same change. This is read from the code and needs a phone to confirm.
   Fix: give the panel a higher sort priority than the map, or open on the list when VoiceOver is on. Announce from the screen on top alone.
9. **Two controls fix the size of a symbol that grows, and landscape is allowed.**
   The minus and plus buttons and the map's three controls draw a symbol in a text style inside a frame fixed at 44 by 44 points, so at the largest text size the symbol is larger than its box. Landscape is switched on and nothing was designed for it. The legend says every ranked area is marked with its fit, while only the first 40 are.
   Fix: give those frames a least width and height, as `.target()` does. Ship portrait only until landscape has been seen. Change the legend's line, or mark every area.
10. **The build that ships allows local networking in the clear.**
    A Release build carries `NSAllowsLocalNetworking` in its `Info.plist`, and the client takes `http://localhost` in any build. A shipped app has no use for either. The review also found that the check compiled Debug alone: `make build` now compiles Release as well.
    Fix: put the key behind a build setting that Debug alone sets, and refuse `http` in a Release build.
11. **How Burro works is compiled into the app, while the engine it describes is served.**
    Methods states how a fit is worked out, with two thresholds held as constants in the build. An installed app cannot follow a change: when the engine moves, a phone shows the new engine version beside the old account of it, until the app is updated.
    Fix: ask the backend to serve the methods text and the thresholds, versioned with the engine. Until then, show Methods only when the served engine version is one the build knows.

## What is not built

| Not built | Why, and what it needs |
|---|---|
| Opening a link from outside the app | The app handles a link it is given, and no link can reach it: it declares no associated domain. That needs the website's address, a team, and a file the website serves |
| A way to know the phone is online again | The app learns it is offline from a call that fails. It tries again when you press "Try again" and when you come back to the app. A monitor needs the Network framework, which the app does not use |
| "Add to compare" on an area's page | Areas are chosen to compare on the results |
| The settings a link holds, listed under the link | The share panel says what a link holds in words, as the website does, and does not list the stored settings as chips |
| Showing which words an applied edit rests on | The API says so (`rests_on`). The app shows the words a suggestion rests on and the words that were not read, and not those of an edit that was applied |
| "Show the words" on iOS 17 | Selecting a stretch of the box needs iOS 18. On iOS 17 the buttons are not offered, and the line that says words were not read still is. The words an offer rests on are drawn under "You wrote" on both |
| The shelf of vibes, "In short", and "More like this" | The website offers each vibe as a word to press above the results, a summary of a result, and areas like the one on a page. In the app a vibe is added in the settings, and the other two are not drawn |
| Settings grouped by family, and what changed since the ranking before | The settings are grouped by dimension, as they were. The status says how many areas changed place, and not how many fewer were ranked, nor that a change of tenure took the budget off |
| The label of an area beside its name, and that a name is a draft | Since 2026-09-24 an area says what is known of the name it bears: the label its publisher gives it, who wrote the name, and whether a person has checked it (`named`). The models read it, and no screen draws it, so a drafted name reads as any other. It needs the label beside the name on a result, in the table and on the screen of an area, the words for a draft, and how an area is named on Methods, as the website has them |
| The brands nearby | Since 2026-09-24 the API serves the chains of grocers, gyms and coffee within reach, as measures of a group of their own. The app names the group in the website's words, "Brands nearby", on the screen of an area, in the settings and on Methods. It lists the measures of the group in the API's order, and gives the group no line of its own. The website puts the mix of brands first, then what is counted of each tier, then the chains, and says above them what the group holds |
| The household income of an area | Since 2026-09-25 the API serves what the households of an area are estimated to have as income, by a route of its own, and the website shows it on an area's page in a part that is closed at first. It is shown and never ranked on. The models read the route, and no screen of the app asks for it or draws it |
| What a press leaves unsaid | The website marks as assumed each part that a press adds and its edit does not say: the way of travelling of a journey, and whether a budget is a firm limit. The app marks what the API says was assumed of a plain sentence, and since 2026-09-25 the kind of house that Burro took at a press, and nothing else after a press |
| A rent that is of a wider place than the area | Since 2026-09-25 the API serves, for a release of London, the rents of the postcode district or the borough an area lies in, and says the place. The app draws the place, the months and the count wherever it draws such a rent: on the screen of an area, on a result and under its sources. It says what the publisher advises once over the rents of an area, and on Methods, and ends the line that counts what a firm budget left out with the API's line on what the rents are of. The note of an offer is drawn as any note is. Where no area passes every limit the website says the same line under the counts, and the app does not. The screen of an area has no link to Methods beside its rents |
| Who published a source, beside a figure | The website names who published each source beside a figure, says each source once and the date once after them all, and on a result shows them at a press of "Source". The app writes the line out under every figure with nothing to press, names each source without its publisher, and says the date after each source. The credit of a source stands where the website puts it: after the name of its source and before the date |
| Finding an area by its name | The search by name answers with the areas that match (`areas`) beside the places. The models read both, and the field draws the places alone. It needs the areas listed under the field, each leading to the screen of its area |
| A map with no basemap | MapKit draws Apple's map under the areas, so Apple's servers learn which part of the city is on screen. The small picture on an area's page draws no basemap. This is a decision to take before real data |
| An icon, a launch screen, other languages | Not started |
| App Attest, which the plan names for this phase | Not started |
