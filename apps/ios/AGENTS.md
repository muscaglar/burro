# apps/ios

The Burro app for iPhone: native SwiftUI, iOS 17 and later, Swift 6 with strict concurrency. It is the same product as the website, so it is built to [docs/design/web.md](../../docs/design/web.md) and calls the API of [docs/design/contract.md](../../docs/design/contract.md), sections 4, 5, 8 and 9. It depends on no package.

```
make check      everything: run this before you say you are done
make generate   write the API models, the tokens and the recorded answers from their sources
make test       the package's tests, on macOS. One class: make test ONLY=BurroKitTests.ReduceTests
make build      compile the app for iOS, in Debug and in Release, with code signing off
```

Needs a Mac with Xcode that can run `swift test`. `check` runs `generate-check`, `test` and `build`, in that order, and stops at the first failure. Hosted CI runs its three parts in the job `ios`, each though one before it failed. `test` is `swift test`, and `build` is `xcodebuild`: the [Makefile](Makefile) holds both commands whole.

`test` treats a warning in the package as an error, and the app target does the same for `App/`. What the package holds for iOS alone, inside `#if os(iOS)`, is compiled by `build` only, where a warning in it does not fail.

[README.md](README.md) says how to open the app, point it at an API, what to look at first, what has and has not been checked, and the known issues.

## The rules

The website's three rules hold here, and three more.

1. **Words about a place are the API's.** The app lays them out. It never writes, joins or rewords a sentence about a place, and formats no number that a fact's `slots` hold already formatted. Copy names controls, states and codes only.
2. **The spec on screen is the last spec the API returned.** The app builds edits, never specs.
3. **What a person types stays in the box it was typed in, and in the body of the `POST` that reads it.** That is one call to the rules, and one more to a model where one reads. Not in the search's state, a file, a log, the pasteboard, Spotlight, Siri or Handoff. Beside an offer the screen draws the words the offer rests on, cut from the box by where they stand, while the box holds them: what `SearchScreen.shown` hands the screen is where they stand, and never the words. A place id, a spec, a fact id and a share id are treated the same way.
4. **No sentence is sent until the person has agreed.** `SearchFlow.submitText` sends nothing until `Consent` says `allowed`. The settings need no agreement.
5. **Every screen that shows data says when it is made up, and when its release is a preview.** The shell draws `SyntheticBanner` and `PreviewBanner` above every tab. A screen does not draw its own. A sheet covers the shell, so the one sheet there is draws both.
6. **Nothing Burro noticed is applied until the person chooses.** A suggestion is sent only by `SearchFlow.choose` and `chooseAll`. A choice is known by its id, and what is sent is the edits the API gave with it, unchanged. A journey the API offers with no place is the one exception: a press on a way of it opens the search for a place, and the place the person chooses is put into the journey before it is sent. "Add all" takes of each thing the way the API names in `add_all`, and nothing of a thing it names none for. Which way that is, is the API's to say: the app works nothing out. A budget is taken as the person worded it, which may be a firm limit, and a journey as a guide. What carries Burro's guess is drawn first, in the order its words stand in the sentence, before "Show all" and after it. The screen then says what the press did, in full: how many it added, how many areas a firm budget among them left out, counted from `filtered` of the ranking that followed, and what is left for the person, by the API's names. One press takes it all back: the search as it stood before is ranked again.

Do not weaken a rule to make a change pass. Raise it instead.

## The project, and why it is this shape

| Path | What it is |
|---|---|
| `BurroKit/` | A Swift package that holds everything but the entry point, so that all of it is tested on a Mac with no simulator |
| `App/` | The app target: `BurroApp.swift` shows `BurroRootView` and lets no keyboard but the phone's own be typed on, with `Info.plist` and the privacy manifest. Nothing else goes here |
| `Burro.xcodeproj` | One target, which names the package beside it. It is written by hand and lists no file: the `App` folder is read as it is found |
| `scripts/generate.py` | Writes everything that is generated. `--check` fails if any of it is stale |

A package alone cannot be built as an app, and a project alone cannot be tested without a simulator. One of each, with the project as thin as it can be, is the least that does both. Open `Burro.xcodeproj` in Xcode to run the app.

## Inside `BurroKit/Sources/BurroKit`

| Folder | Holds | Owner |
|---|---|---|
| `API/` | `Generated/` (the models, the routes and the protocol `BurroAPI`), `LiveBurroAPI`, `Transport`, `Failure`, `APIConfiguration`, `SyntheticNotice`, `PreviewNotice` | Foundation |
| `Search/` | `SearchState` and `reduce`, `SearchStore`, `SearchFlow`, `Edits`, `Shown`. They follow `apps/web/src/lib/search/` event for event: when `state.ts` or `flow.ts` changes, change these and port its test. `Vibes` and `VibeCopy` say a vibe as a band of five, `Offers` what may be done with a suggestion, `ReleaseHolds` and `NotInData` what the release does not hold | Foundation |
| `Design/` | `Tokens`, `TokenColor`, the two button styles, `VibeLine`, `Generated/TokenValues` | Foundation |
| `Kept/` | `PhoneStorage`, `Shortlist`, `Consent`, `FileSavedAreasStorage`: the only things written to the phone | Foundation |
| `Shell/` | `AppModel`, `BurroRootView`, `Navigation`, `SiteAddress`, `SyntheticBanner`, `PreviewBanner`, `ShellCopy` | Foundation |
| `Features/Search/` | `SearchRootView`, `PermissionView`, `SearchCopy`. `SearchScreen.shown` decides what is drawn and in what order, and `SearchHands` what a press does. `OffersBlock` draws what was noticed, each offer in its four parts and in the API's words, what is not in the data and what was not read. `Examples.swift` holds the example sentences, which name a figure and so are in no Copy file | Search |
| `Features/Results/` | `ResultsView`: the map with the list over it, the table of every area, and sharing. `ResultsCompareView`: the comparison. `Model/` works out what is drawn, `Views/` draws it, and every name is inside `Results` | Results |
| `Features/Area/` | `AreaView`: one area, its sources, "Add to shortlist", "Share". `opensLinks()`, which the shell puts on its root, opens the website's own links | Area |
| `Features/Shortlist/` | `ShortlistRootView`, and `SavedAreas`, which is `app.saved` | Shortlist |
| `Features/About/` | `AboutRootView`, `AboutScreenView` for methods, sources and accessibility | About |

An author owns every file in their feature's folder, and `Tests/BurroKitTests/Features/<Name>/`. They add files there freely. They change nothing outside it. If a shared type lacks something, say so and have the foundation changed: three people changing it apart will not agree.

**What a feature may use, and may not change**

| Type | Use it to |
|---|---|
| `AppModel`, from `@Environment(AppModel.self)` | Reach `search`, `saved`, `consent`, `synthetic`, `preview`. Go somewhere with `show(_:)`, `show(_:in:)`, `showRoot(of:)`. Save an area with `toggleShortlist(_:)`, or with `saved.toggle(_:page:)` where its page is in hand: both keep its facts, and nothing of the search |
| `SearchStore`, from `@Environment(SearchStore.self)` inside `Opened { }` | Read `state`. Ask `flow` to do things. Never make a `SearchState` or send an event |
| `SearchFlow` | `submitText`, `applyEdits`, `choose`, `chooseAll`, `takeBack`, `boxChanged`, `answerClarify`, `leaveOut`, `addPlace`, `setTenure`, `rankNow`, `retry`, `stop`, `startAgain`, `openShare`, `createShare`, `compare`, `searchPlaces`, `loadDetail`, `loadGeometry`, `select`, `openSettings`, `wentOffline`, `wentOnline` |
| `SearchState` and `Shown.swift` | `phase`, `conditions`, `failurePlace`, `questions`, `suggestions`, `unread`, `readInPart`, `missing`, `nothingRead`, `unmetShown`, `refusals`, `repairs`: each state of web.md section 3, worked out once. `leads` says what counts for more than what was asked of the place, `reasonsAreIn` says whether the reasons are the ranking's, `failureOfTheCards` why a card lacks something, `servedTheRanking` which release to name under a result |
| `Edits` | Build the one edit a control sends |
| `Screen`, `AreaRef`, `AppTab` | Name where to go. A route holds ids and names of the release, never anything of a search |
| `app.site` | The only place an address is built: `area(_:)` and `share(_:)`, for `ShareLink`. Each is `nil` until the website has an address, from the build setting `BURRO_SITE_URL`: offer no "Share" then |
| `Tokens`, `.burroPrimary`, `.burroSecondary`, `.target()` | Every colour, text style, space and size. No other colour and no fixed font size |
| Generated models | Read what the API sent. Every code has `unlisted(String)` for a value this build does not know: draw nothing for it |

The first screen of each feature keeps its name and its `init`, because the shell makes it: `PermissionView()`, `SearchRootView()`, `ResultsView()`, `ResultsCompareView()`, `AreaView(area:)`, `ShortlistRootView()`, `AboutRootView()`, `AboutScreenView(screen:)`. A test fails to compile if one changes.

## The API

- The address comes from one build setting, `BURRO_API_BASE_URL`, written into `Info.plist` as `BurroAPIBaseURL` and read in `APIConfiguration`. A debug build names the API on `127.0.0.1`. A release build names none until one is given: `xcodebuild BURRO_API_BASE_URL=... build`. `http` is taken for `localhost` and `127.0.0.1` only.
- `BurroAPI` has one method a route and none throws. An answer is `Answered`, with `meta`, `data`, `synthetic` and `preview`, or a `Failure`: the API's own, with its code, message and paths, or one of `timeout`, `aborted`, `offline`, `network`, `notConfigured`, `unreadable`. Show `message` as it came.
- A view never sees `URLSession`. A test passes `StandIn`, which answers from the recorded answers through the real client.
- Two types share a name with the system's: `Dimension` and `Combine`. Inside BurroKit the name means Burro's. Do not `import Combine`.
- A sentence is sent to the rules first, with `ask_model` false, and they answer at once. It is sent again, for a model to read, only where that answer says `model_pending`. What the rules offer never waits on a model: it is drawn at once, and while the model reads the screen says so. Where the provider of a model would not read what was typed, the rules read it, and both screens say so in the website's one line, which names nobody: ask `state.modelRefused`.
- What the release holds is the API's to say. Who reads what is typed is `meta.reader.notice`, shown word for word: the app names no provider. A vibe is a band of five from a fact or a strip, with `meta.recipes` for what it waits on. A place is named by `places` of the answer that brought the spec, and is never shown by a number.
- A vibe that is a rough guide says so wherever it is shown, drawn and behind no press: its label and the sentence that says why, which are `meta.roughGuides` of route 11. Which vibe is one is `Tag.sureness`, and one that does not say is as sure as the rest. `Vibes.rough` reads both, and the app writes neither. It is on the chip of a search and in the first line under the chips, beside the control of the vibe, under the band wherever `VibeLine` draws the vibe (a result, the page of an area, a saved area, a comparison), and under its name where the recipes are set out. Its offer says it in the API's own note, and "Add all" never takes it: the API names no way for it in `add_all`.

## Generated files

`API/Generated/`, `Design/Generated/` and `Tests/BurroKitTests/Recorded/` are written by `make generate` from `contracts/openapi.json`, `apps/web/src/styles/tokens.css` and `apps/web/test/recorded/`. They are committed and never edited by hand. When a source changes, run `make generate`, mend what no longer compiles, and bring each test that names a figure to the recordings as they now are. The generator fails on a schema it has no rule for: give it a rule, never a guess.

## Tests

- Named for the behaviour they protect: `test_typed_text_travels_only_in_a_post_body`.
- Offline. Read an answer with `Answers.ranked("rank-first")` or `Recorded.read(...)`. Run a whole search with `OpenSearch()`, set what is answered with `api.on(.rank, "rank-refined")`, and read what was sent with `api.lastCall(to: .rank).body(as: RankBody.self)`.
- A test of privacy plants a canary, a string found nowhere else, and looks for it everywhere it must not be.
- `PrivacyRulesTests` reads every source file of the app. It fails on a log, a store other than `Kept/`, the pasteboard, Spotlight, Siri, Handoff, analytics, a session of the network outside `API/`, and an import of anything but Foundation, SwiftUI, MapKit and Observation. To copy for the person, name the file in that test and say what it copies.
- A view cannot be drawn here, so put what a screen decides in a plain function or in `Shown.swift`, and test that.
- `Whole/VisitTests` walks one person's whole visit, and answers a request only if the service was sent that very request when the visit was recorded. When what the app sends changes, it fails until `record_the_visit` in `apps/web/test/record.py` is changed to match.
- A test that holds the app's words to the website's fails when the website's words change. Follow the website, in the same change.

## What is kept on the phone

| File | Holds | Never holds |
|---|---|---|
| `shortlist.json` | For each saved area: its id, slug, name, borough, the date, and whether it is made up | A rank, a fit, a place, a spec, anything typed |
| `saved-areas.json` | The order the person put the saved areas in, and for each its release, whether that was a preview, its facts as they were when it was saved, and its vibes with what each waits on and what one that is a rough guide says of itself: only facts of kind `area`, `feature`, `tag`, `cost` and `station`, so that a saved area reads with no connection | A journey, a budget fit, a fact's id, a rank, a fit, a place, a spec, which vibe a search asked for, anything typed |
| `consent.json` | `allowed` or `settingsOnly` | Anything else |

All three are in the app's own folder, left out of backups. To keep a fourth thing, add it to `KeptFile` and to this table. The privacy manifest declares no tracking, no collected data and no API that needs a reason: a change that uses one must declare it.

## Accessibility

Every control is a system control with a label. Text takes a style from `Tokens.Text`, so it grows with the person's setting: never fix a height on text. Anything pressed is 44 points at least: `.target()`. Animate only through `Tokens.Motion.animation`, which gives none when less motion is asked for. Colour is never the only signal: rank is a number, fit is "80 of 100", a vibe is "band 4 of 5", assumed is a word. Nothing is dimmed but a button while it is pressed: a control that is switched off is drawn in colours of its own. What the API said is drawn with `Text(verbatim:)`. Every map has the list that says all it shows.

## What has been checked

Nothing has been seen on a screen, in a simulator or on a phone: say so until it has. [README.md](README.md) says what has and has not been checked. Write no count of tests and no word that a build passes unless you ran it, and say where you ran it.

If something here is wrong or out of date, fix this file in the same change.
